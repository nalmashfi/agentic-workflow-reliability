#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def close(a, b, tol=5e-10):
    return abs(float(a) - float(b)) <= tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--actual', required=True, type=Path)
    ap.add_argument('--expected', required=True, type=Path)
    args = ap.parse_args()
    actual = json.loads(args.actual.read_text())
    expected = json.loads(args.expected.read_text())
    checks = []

    def chk(name, av, ev, tol=5e-10):
        ok = close(av, ev, tol)
        checks.append((name, ok, av, ev))

    def chk_exact(name, av, ev):
        checks.append((name, av == ev, av, ev))

    chk_exact('manifest_sha256', actual['dataset']['manifest_sha256'], expected['dataset']['manifest_sha256'])
    chk('trajectories', actual['dataset']['trajectories'], expected['dataset']['trajectories'], 0)
    chk('task_clusters', actual['dataset']['task_clusters'], expected['dataset']['task_clusters'], 0)
    chk('repositories', actual['dataset']['repositories'], expected['dataset']['repositories'], 0)
    chk('solve_rate', actual['terminal']['solve_rate'], expected['terminal']['solve_rate'])
    chk('incorrect_rate', actual['annotation']['rate'], expected['annotation']['rate'])

    for k in ['entry', 'persistence', 'return', 'recurrence_after_return', 'multi_episode_rate', 'solve_given_observed_return']:
        chk(k, actual['transitions'][k], expected['transitions'][k])

    for model in ['aggregate', 'homogeneous', 'position']:
        for metric in ['MAE', 'RMSE', 'Brier', 'Log loss', 'ECE', 'Mean prediction', 'Observed']:
            chk(f'{model}.{metric}', actual['heldout'][model][metric], expected['heldout'][model][metric], 2e-9)

    chk_exact('fold_trajectory_counts', actual['heldout_folds']['trajectory_counts'], expected['heldout_folds']['trajectory_counts'])
    chk_exact('fold_repository_counts', actual['heldout_folds']['repository_counts'], expected['heldout_folds']['repository_counts'])

    for key in ['position_minus_aggregate', 'position_minus_homogeneous']:
        chk(f'{key}.estimate', actual['heldout_brier_deltas'][key]['estimate'], expected['heldout_brier_deltas'][key]['estimate'], 2e-9)
        for j in [0, 1]:
            chk(f'{key}.ci95[{j}]', actual['heldout_brier_deltas'][key]['ci95'][j], expected['heldout_brier_deltas'][key]['ci95'][j], 2e-9)

    chk('mc_max_abs_error', actual['monte_carlo']['max_position_abs_error'], expected['monte_carlo']['max_position_abs_error'], 2e-9)
    chk('mc_max_se', actual['monte_carlo']['max_position_mc_se'], expected['monte_carlo']['max_position_mc_se'], 2e-9)

    failed = [x for x in checks if not x[1]]
    for name, ok, av, ev in checks:
        print(('PASS' if ok else 'FAIL'), name, av, 'expected', ev)
    if failed:
        raise SystemExit(1)
    print(f'PASS: {len(checks)} numerical and provenance checks matched the frozen results.')


if __name__ == '__main__':
    main()
