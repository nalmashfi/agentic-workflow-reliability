#!/usr/bin/env python3
"""From the Tracebench records, the analysis reconstructs stage sequences and computes the empirical results.
For each recorded trajectory, the analysis uses the stage boundaries, annotations,
task identifier, and terminal outcome supplied by Tracebench. These observations
leave hidden agent reasoning and the underlying reliability state unobserved.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, random
from pathlib import Path
import numpy as np
import pandas as pd


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_list(value):
    if isinstance(value, list):
        return value
    if not value:
        return []
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return []


def task_id(row: dict) -> str:
    return str(row.get("task_name") or row.get("trial_name") or row.get("task_slug") or row.get("traj_id"))


def repository_id(row: dict) -> str:
    text = task_id(row)
    if "__" in text:
        return text.split("__", 1)[0]
    if "/" in text:
        return text.split("/", 1)[0]
    return text.split("-", 1)[0]


def annotation_sequence(row: dict) -> list[int]:
    n = max(1, int(row.get("stage_count") or 1))
    incorrect = set()
    for item in parse_list(row.get("incorrect_stages")):
        try:
            incorrect.add(int(item.get("stage_id")))
        except (TypeError, ValueError):
            pass
    return [1 if j in incorrect else 0 for j in range(1, n + 1)]  # N=0, I=1


def load_rows(path: Path, prefix: str) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("source_relpath") or "").startswith(prefix):
                rows.append(row)
    return rows


def mean(values):
    return sum(values) / len(values) if values else float("nan")


def percentile_ci(values: list[float], low=0.025, high=0.975):
    x = sorted(values)
    return [x[int(low * len(x))], x[int(high * len(x)) - 1]]


def transition_counts(rows: list[dict]):
    nn = ni = ii = inn = 0
    first_positions, last_positions, episodes = [], [], []
    final_i = 0
    return_trajectories = return_solved = multi_episode = 0
    recurrence = return_followup = 0
    for row in rows:
        seq = annotation_sequence(row)
        if seq[-1] == 1:
            final_i += 1
        ids = [j + 1 for j, z in enumerate(seq) if z == 1]
        if ids:
            first_positions.append(min(ids) / len(seq))
            last_positions.append(max(ids) / len(seq))
        ep = 1 if seq and seq[0] == 1 else 0
        observed_return = False
        for k, (a, b) in enumerate(zip(seq[:-1], seq[1:])):
            if (a, b) == (0, 0): nn += 1
            elif (a, b) == (0, 1): ni += 1; ep += 1
            elif (a, b) == (1, 1): ii += 1
            elif (a, b) == (1, 0):
                inn += 1; observed_return = True
                if k + 2 < len(seq):
                    return_followup += 1
                    if seq[k + 2] == 1:
                        recurrence += 1
        episodes.append(ep)
        if ep > 1:
            multi_episode += 1
        if observed_return:
            return_trajectories += 1
            if bool(row.get("solved")):
                return_solved += 1
    return {
        "NN": nn, "NI": ni, "II": ii, "IN": inn,
        "entry": ni / (nn + ni),
        "persistence": ii / (ii + inn),
        "return": inn / (ii + inn),
        "recurrence_after_return": recurrence / return_followup,
        "return_followup_opportunities": return_followup,
        "recurrence_count": recurrence,
        "final_incorrect_rate": final_i / len(rows),
        "mean_failure_episodes": mean(episodes),
        "multi_episode_rate": multi_episode / len(rows),
        "return_trajectory_count": return_trajectories,
        "return_trajectory_solved": return_solved,
        "solve_given_observed_return": return_solved / return_trajectories,
        "first_incorrect_mean": mean(first_positions),
        "last_incorrect_mean": mean(last_positions),
    }


def cluster_bootstrap(rows: list[dict], B: int, seed: int):
    clusters = collections.defaultdict(list)
    for row in rows:
        clusters[task_id(row)].append(row)
    keys = list(clusters)
    rng = random.Random(seed)
    stats = collections.defaultdict(list)
    for _ in range(B):
        sampled_keys = [keys[rng.randrange(len(keys))] for _ in range(len(keys))]
        sample = [row for key in sampled_keys for row in clusters[key]]
        tr = transition_counts(sample)
        solved = sum(bool(r.get("solved")) for r in sample) / len(sample)
        any_i = sum(bool(parse_list(r.get("incorrect_stages"))) for r in sample) / len(sample)
        stats["solve_rate"].append(solved)
        stats["incorrect_rate"].append(any_i)
        stats["entry"].append(tr["entry"])
        stats["persistence"].append(tr["persistence"])
        stats["return"].append(tr["return"])
        stats["recurrence"].append(tr["recurrence_after_return"])
        stats["final_incorrect"].append(tr["final_incorrect_rate"])
        stats["multi_episode"].append(tr["multi_episode_rate"])
        stats["solve_given_return"].append(tr["solve_given_observed_return"])
        stats["first_incorrect_mean"].append(tr["first_incorrect_mean"])
    return len(keys), {k: percentile_ci(v) for k, v in stats.items()}


def agent_summary(rows: list[dict], B: int, seed: int):
    records = []
    for agent in sorted(set(r.get("agent") for r in rows)):
        sub = [r for r in rows if r.get("agent") == agent]
        clusters = collections.defaultdict(list)
        for r in sub:
            clusters[task_id(r)].append(r)
        keys = list(clusters)
        rng = random.Random(seed)
        solve_samples, incorrect_samples = [], []
        for _ in range(B):
            selected = [keys[rng.randrange(len(keys))] for _ in range(len(keys))]
            z = [r for key in selected for r in clusters[key]]
            solve_samples.append(sum(bool(r.get("solved")) for r in z) / len(z))
            incorrect_samples.append(sum(bool(parse_list(r.get("incorrect_stages"))) for r in z) / len(z))
        tr = transition_counts(sub)
        solved = sum(bool(r.get("solved")) for r in sub)
        has_i = sum(bool(parse_list(r.get("incorrect_stages"))) for r in sub)
        records.append({
            "Agent": agent, "N": len(sub), "Solved": solved,
            "Solve rate": solved / len(sub), "Solve CI low": percentile_ci(solve_samples)[0],
            "Solve CI high": percentile_ci(solve_samples)[1],
            "Has incorrect": has_i, "Incorrect rate": has_i / len(sub),
            "N->I": tr["entry"], "I->I": tr["persistence"], "I->N": tr["return"]
        })
    return pd.DataFrame(records)


def position_summary(rows: list[dict], bins=5):
    labels = [f"{int(100*i/bins)}-{int(100*(i+1)/bins)}%" for i in range(bins)]
    allc = collections.Counter(); solved = collections.Counter(); unsolved = collections.Counter()
    trans = [collections.Counter() for _ in range(bins)]
    stage_hist = collections.Counter()
    final_by_length = collections.defaultdict(lambda: [0, 0])
    for row in rows:
        seq = annotation_sequence(row); n = len(seq); stage_hist[n] += 1
        final_by_length[n][0] += 1; final_by_length[n][1] += seq[-1]
        incorrect_ids = []
        for item in parse_list(row.get("incorrect_stages")):
            try: incorrect_ids.append(int(item.get("stage_id")))
            except (TypeError, ValueError): pass
        for sid in incorrect_ids:
            p = sid / n; b = min(bins - 1, max(0, int((p - 1e-12) * bins)))
            lab = labels[b]; allc[lab] += 1
            (solved if bool(row.get("solved")) else unsolved)[lab] += 1
        for j, (a, bstate) in enumerate(zip(seq[:-1], seq[1:]), start=2):
            pos = j / n; b = min(bins - 1, max(0, int((pos - 1e-12) * bins)))
            trans[b][(a, bstate)] += 1
    qrows, params = [], []
    overall = transition_counts(rows)
    for i, lab in enumerate(labels):
        qrows.append({"Normalized position": lab, "All incorrect stages": allc[lab],
                      "Solved trajectories": solved[lab], "Unsolved trajectories": unsolved[lab]})
        c = trans[i]
        c0 = c[(0,0)] + c[(0,1)]; c1 = c[(1,0)] + c[(1,1)]
        params.append({"Normalized position": lab,
                       "N->I": c[(0,1)] / c0 if c0 else overall["entry"],
                       "I->I": c[(1,1)] / c1 if c1 else overall["persistence"],
                       "NN": c[(0,0)], "NI": c[(0,1)], "IN": c[(1,0)], "II": c[(1,1)]})
    length_rows = [{"Stage count": n, "N": v[0], "Final incorrect": v[1], "Rate": v[1]/v[0]}
                   for n, v in sorted(final_by_length.items())]
    return pd.DataFrame(qrows), pd.DataFrame(params), dict(sorted(stage_hist.items())), pd.DataFrame(length_rows)


def fit_transition_model(rows: list[dict], bins=5):
    seqs = [annotation_sequence(r) for r in rows]
    initial_i = sum(s[0] for s in seqs) / len(seqs)
    nn = ni = ii = inn = 0
    bcounts = [collections.Counter() for _ in range(bins)]
    for seq in seqs:
        n = len(seq)
        for j, (a, b) in enumerate(zip(seq[:-1], seq[1:]), start=2):
            if (a,b)==(0,0): nn += 1
            elif (a,b)==(0,1): ni += 1
            elif (a,b)==(1,1): ii += 1
            else: inn += 1
            q = min(bins - 1, max(0, int(((j/n)-1e-12)*bins)))
            bcounts[q][(a,b)] += 1
    entry = (ni + 0.5) / (nn + ni + 1)
    persistence = (ii + 0.5) / (ii + inn + 1)
    params = []
    for c in bcounts:
        c0 = c[(0,0)] + c[(0,1)]; c1 = c[(1,0)] + c[(1,1)]
        a = (c[(0,1)] + 0.5)/(c0+1) if c0 else entry
        q = (c[(1,1)] + 0.5)/(c1+1) if c1 else persistence
        params.append((a,q))
    baseline = sum(s[-1] for s in seqs) / len(seqs)
    return {"initial": initial_i, "entry": entry, "persistence": persistence,
            "position": params, "baseline": baseline}


def predict_final(n: int, fitted: dict, kind: str, bins=5):
    if kind == "aggregate":
        return fitted["baseline"]
    p = fitted["initial"]
    for j in range(2, n+1):
        if kind == "homogeneous":
            a, q = fitted["entry"], fitted["persistence"]
        else:
            b = min(bins - 1, max(0, int(((j/n)-1e-12)*bins)))
            a, q = fitted["position"][b]
        p = (1-p)*a + p*q
    return p


def prediction_metrics(records: list[dict], key: str, cal_bins=10):
    y = [x["y"] for x in records]; p = [x[key] for x in records]; n = len(y); eps = 1e-12
    mae = sum(abs(a-b) for a,b in zip(p,y))/n
    mse = sum((a-b)**2 for a,b in zip(p,y))/n
    logloss = -sum(yy*math.log(max(eps,min(1-eps,pp))) + (1-yy)*math.log(max(eps,min(1-eps,1-pp))) for pp,yy in zip(p,y))/n
    buckets=[[] for _ in range(cal_bins)]
    for pp, yy in zip(p,y): buckets[min(cal_bins-1,int(pp*cal_bins))].append((pp,yy))
    ece=sum(len(b)/n*abs(mean([x for x,_ in b])-mean([z for _,z in b])) for b in buckets if b)
    return {"N":n,"MAE":mae,"RMSE":math.sqrt(mse),"Brier":mse,"Log loss":logloss,
            "ECE":ece,"Mean prediction":mean(p),"Observed":mean(y)}


def heldout_validation(rows: list[dict], folds: int, bins: int, cal_bins: int, B: int, seed: int):
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[repository_id(row)].append(row)
    # At each step, the procedure assigns the largest remaining repository to the smallest fold.
    # For repositories of equal size, SHA-256 determines their order.
    ordered = sorted(grouped.items(), key=lambda kv: (-len(kv[1]), hashlib.sha256(kv[0].encode()).hexdigest()))
    fold_groups = [[] for _ in range(folds)]
    fold_sizes = [0 for _ in range(folds)]
    for rp, group_rows in ordered:
        f = min(range(folds), key=lambda j: (fold_sizes[j], j))
        fold_groups[f].append(rp)
        fold_sizes[f] += len(group_rows)
    foldmap = {rp: f for f, names in enumerate(fold_groups) for rp in names}
    fold_repository_counts = [len(names) for names in fold_groups]
    records=[]
    for f in range(folds):
        train=[r for r in rows if foldmap[repository_id(r)] != f]
        test=[r for r in rows if foldmap[repository_id(r)] == f]
        model=fit_transition_model(train,bins)
        for r in test:
            y=annotation_sequence(r)[-1]; n=len(annotation_sequence(r))
            records.append({"fold":f,"repo":repository_id(r),"y":y,
                            "aggregate":predict_final(n,model,"aggregate",bins),
                            "homogeneous":predict_final(n,model,"homogeneous",bins),
                            "position":predict_final(n,model,"position",bins)})
    metrics={k:prediction_metrics(records,k,cal_bins) for k in ["aggregate","homogeneous","position"]}
    rr=collections.defaultdict(list)
    for x in records: rr[x["repo"]].append(x)
    repo_list=list(rr); rng=random.Random(seed); deltas={"position_minus_aggregate":[],"position_minus_homogeneous":[]}
    def brier(sample,key):
        z=[x for rp in sample for x in rr[rp]]
        return sum((x[key]-x["y"])**2 for x in z)/len(z)
    for _ in range(B):
        sm=[repo_list[rng.randrange(len(repo_list))] for _ in range(len(repo_list))]
        deltas["position_minus_aggregate"].append(brier(sm,"position")-brier(sm,"aggregate"))
        deltas["position_minus_homogeneous"].append(brier(sm,"position")-brier(sm,"homogeneous"))
    delta_out={k:{"estimate":metrics["position"]["Brier"]-metrics[k.split("_minus_")[1]]["Brier"],"ci95":percentile_ci(v)} for k,v in deltas.items()}
    fold_info={"trajectory_counts":fold_sizes,"repository_counts":fold_repository_counts}
    return metrics, delta_out, foldmap, fold_info


def monte_carlo(rows: list[dict], position_params: pd.DataFrame, runs: int, seed: int):
    seqs=[annotation_sequence(r) for r in rows]
    initial=sum(s[0] for s in seqs)/len(seqs)
    tr=transition_counts(rows); entry=tr["entry"]; persistence=tr["persistence"]
    pa=position_params["N->I"].to_numpy(float); pq=position_params["I->I"].to_numpy(float); bins=len(pa)
    stage_hist=collections.Counter(len(s) for s in seqs); rng=np.random.default_rng(seed)
    def ah(n):
        p=initial
        for _ in range(2,n+1): p=(1-p)*entry+p*persistence
        return p
    def ap(n):
        p=initial
        for j in range(2,n+1):
            b=min(bins-1,max(0,int(((j/n)-1e-12)*bins)))
            p=(1-p)*pa[b]+p*pq[b]
        return p
    out=[]
    for n in sorted(stage_hist):
        h=ah(n); p=ap(n)
        state=rng.random(runs)<initial
        for _ in range(2,n+1):
            u=rng.random(runs); state=np.where(state,u<persistence,u<entry)
        hmc=float(state.mean()); hse=math.sqrt(hmc*(1-hmc)/runs)
        state=rng.random(runs)<initial
        for j in range(2,n+1):
            b=min(bins-1,max(0,int(((j/n)-1e-12)*bins)))
            u=rng.random(runs); state=np.where(state,u<pq[b],u<pa[b])
        pmc=float(state.mean()); pse=math.sqrt(pmc*(1-pmc)/runs)
        out.append({"Stage count":n,"Observed trajectories":stage_hist[n],
                    "Homogeneous analytical":h,"Homogeneous MC":hmc,"Homogeneous abs. error":abs(h-hmc),"Homogeneous MC SE":hse,
                    "Position-aware analytical":p,"Position-aware MC":pmc,"Position-aware abs. error":abs(p-pmc),"Position-aware MC SE":pse})
    return pd.DataFrame(out)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True,type=Path)
    ap.add_argument("--config",type=Path,default=Path(__file__).resolve().parents[1]/"config"/"analysis_config.json")
    ap.add_argument("--out",type=Path,default=Path("outputs"))
    ap.add_argument("--skip-hash-check",action="store_true")
    args=ap.parse_args()
    cfg=json.loads(args.config.read_text())
    digest=sha256_file(args.manifest)
    if not args.skip_hash_check and digest != cfg["expected_manifest_sha256"]:
        raise SystemExit(f"Manifest SHA-256 mismatch: {digest}")
    rows=load_rows(args.manifest,cfg["swe_source_prefix"])
    if len(rows)!=646:
        raise SystemExit(f"Expected 646 SWE-bench trajectories, found {len(rows)}")
    out=args.out; out.mkdir(parents=True,exist_ok=True); (out/"tables").mkdir(exist_ok=True)
    tr=transition_counts(rows)
    clusters, cis=cluster_bootstrap(rows,cfg["bootstrap_replicates"],cfg["bootstrap_seed"])
    agents=agent_summary(rows,cfg["bootstrap_replicates"],cfg["bootstrap_seed"])
    qtab, posparams, stage_hist, lengthtab=position_summary(rows,cfg["position_bins"])
    held, deltas, foldmap, fold_info=heldout_validation(rows,cfg["repository_folds"],cfg["position_bins"],cfg["calibration_bins"],cfg["bootstrap_replicates"],cfg["bootstrap_seed"])
    mc=monte_carlo(rows,posparams,cfg["monte_carlo_runs_per_stage_count"],cfg["monte_carlo_seed"])
    solved=sum(bool(r.get("solved")) for r in rows); any_i=sum(bool(parse_list(r.get("incorrect_stages"))) for r in rows)
    incorrect_rows=[r for r in rows if bool(parse_list(r.get("incorrect_stages")))]; no_i=[r for r in rows if not bool(parse_list(r.get("incorrect_stages")))]
    result={
      "dataset":{"source":cfg["dataset"],"manifest_sha256":digest,"trajectories":len(rows),"task_clusters":clusters,"repositories":len(set(repository_id(r) for r in rows))},
      "terminal":{"solved":solved,"unsolved":len(rows)-solved,"solve_rate":solved/len(rows),"solve_ci95":cis["solve_rate"]},
      "annotation":{"trajectories_with_I":any_i,"rate":any_i/len(rows),"rate_ci95":cis["incorrect_rate"],
        "solve_given_I":sum(bool(r.get("solved")) for r in incorrect_rows)/len(incorrect_rows),
        "solve_given_no_I":sum(bool(r.get("solved")) for r in no_i)/len(no_i),
        "first_I_mean":tr["first_incorrect_mean"],"first_I_ci95":cis["first_incorrect_mean"],"last_I_mean":tr["last_incorrect_mean"]},
      "transitions":{"NN":tr["NN"],"NI":tr["NI"],"II":tr["II"],"IN":tr["IN"],"entry":tr["entry"],"entry_ci95":cis["entry"],
        "persistence":tr["persistence"],"persistence_ci95":cis["persistence"],"return":tr["return"],"return_ci95":cis["return"],
        "recurrence_after_return":tr["recurrence_after_return"],"recurrence_ci95":cis["recurrence"],"multi_episode_rate":tr["multi_episode_rate"],
        "multi_episode_ci95":cis["multi_episode"],"solve_given_observed_return":tr["solve_given_observed_return"],"solve_given_return_ci95":cis["solve_given_return"]},
      "heldout":held,"heldout_brier_deltas":deltas,"heldout_folds":fold_info,
      "monte_carlo":{"runs_per_stage_count":cfg["monte_carlo_runs_per_stage_count"],"max_position_mc_se":float(mc["Position-aware MC SE"].max()),"max_position_abs_error":float(mc["Position-aware abs. error"].max())},
      "config":cfg
    }
    agents.to_csv(out/"tables"/"agent_summary.csv",index=False)
    qtab.to_csv(out/"tables"/"incorrect_position.csv",index=False)
    posparams.to_csv(out/"tables"/"position_parameters.csv",index=False)
    lengthtab.to_csv(out/"tables"/"final_incorrect_by_stage_count.csv",index=False)
    pd.DataFrame([{"Transition":"N->N","Count":tr["NN"],"Probability":tr["NN"]/(tr["NN"]+tr["NI"])},
                  {"Transition":"N->I","Count":tr["NI"],"Probability":tr["entry"]},
                  {"Transition":"I->I","Count":tr["II"],"Probability":tr["persistence"]},
                  {"Transition":"I->N","Count":tr["IN"],"Probability":tr["return"]}]).to_csv(out/"tables"/"observed_transitions.csv",index=False)
    pd.DataFrame([{"Model":k,**v} for k,v in held.items()]).to_csv(out/"tables"/"heldout_validation.csv",index=False)
    mc.to_csv(out/"tables"/"analytical_monte_carlo.csv",index=False)
    (out/"results_v23.json").write_text(json.dumps(result,indent=2))
    (out/"repository_folds.json").write_text(json.dumps(foldmap,indent=2,sort_keys=True))
    print(json.dumps({"status":"ok","manifest_sha256":digest,"swe_trajectories":len(rows),"output":str(out)},indent=2))

if __name__ == "__main__":
    main()
