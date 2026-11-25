#!/usr/bin/env python3
"""From the reproduced tables and model estimates, the script generates the analysis figures."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch


def clean(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--outputs', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    r = json.loads((args.outputs / 'results_v23.json').read_text())
    cfg = r['config']
    agents = pd.read_csv(args.outputs / 'tables' / 'agent_summary.csv')
    qtab = pd.read_csv(args.outputs / 'tables' / 'incorrect_position.csv')
    pp = pd.read_csv(args.outputs / 'tables' / 'position_parameters.csv')
    lengths = pd.read_csv(args.outputs / 'tables' / 'final_incorrect_by_stage_count.csv')
    trans = pd.read_csv(args.outputs / 'tables' / 'observed_transitions.csv')
    mc = pd.read_csv(args.outputs / 'tables' / 'analytical_monte_carlo.csv')

    # Figure 1: conceptual five-state model and observable boundary.
    fig, ax = plt.subplots(figsize=(11.2, 5.7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.axis('off')
    states = {'C':(1.0,5.1),'L':(3.2,5.1),'D':(5.4,5.1),'R':(7.6,5.1),'F':(5.4,2.9)}
    names = {'C':'Confirmed\ncorrect','L':'Latent\nfailure','D':'Detected\nfailure','R':'Candidate\nrepair','F':'Terminal\nfailure'}
    for s,(x,y) in states.items():
        ax.add_patch(Circle((x,y),0.48,fill=False,linewidth=1.8))
        ax.text(x,y+0.05,s,ha='center',va='center',fontsize=14,fontweight='bold')
        ax.text(x,y-0.85,names[s],ha='center',va='top',fontsize=9)
    def arrow(a,b,label,rad=0):
        x1,y1=states[a]; x2,y2=states[b]
        ax.add_patch(FancyArrowPatch((x1+(.5 if x2>x1 else -.5),y1),
                                     (x2-(.5 if x2>x1 else -.5),y2),
                                     arrowstyle='-|>',mutation_scale=14,linewidth=1.5,
                                     connectionstyle=f'arc3,rad={rad}'))
        ax.text((x1+x2)/2,(y1+y2)/2+(0.35 if rad>=0 else -0.35),label,ha='center',fontsize=10)
    arrow('C','L',r'$\alpha_i$'); arrow('L','D',r'$\delta_i$'); arrow('D','R',r'$\rho_i$')
    arrow('D','F',r'$1-\rho_i$'); arrow('R','C',r'$1-\eta_i$',-.28); arrow('R','L',r'$\eta_i$',.28)
    for s,label in [('C',r'$1-\alpha_i$'),('L',r'$1-\delta_i$')]:
        x,y=states[s]
        ax.add_patch(FancyArrowPatch((x-.25,y+.48),(x+.25,y+.48),arrowstyle='-|>',mutation_scale=12,
                                     linewidth=1.3,connectionstyle='arc3,rad=-1.5'))
        ax.text(x,y+1.05,label,ha='center',fontsize=10)
    ax.add_patch(FancyBboxPatch((8.8,3.6),2.7,2.3,boxstyle='round,pad=.15',fill=False,linewidth=1.5,linestyle='--'))
    ax.text(10.15,5.55,'Acceptance boundary',ha='center',fontsize=10,fontweight='bold')
    ax.text(10.15,4.85,r'$C \rightarrow$ accepted',ha='center',fontsize=10)
    ax.text(10.15,4.25,r'$L,D,R,F \rightarrow F$',ha='center',fontsize=10)
    ax.text(10.15,3.75,'Residual uncertainty is not accepted',ha='center',fontsize=8)
    ax.add_patch(FancyBboxPatch((.7,.45),10.8,1.35,boxstyle='round,pad=.15',fill=False,linewidth=1.5))
    ax.text(1.05,1.5,'Public-trace observation layer',ha='left',fontsize=10,fontweight='bold')
    ax.text(3.7,1.12,r'$N$: no incorrect-stage annotation',ha='center',fontsize=9)
    ax.text(7.7,1.12,r'$I$: incorrect-stage annotation',ha='center',fontsize=9)
    ax.add_patch(FancyArrowPatch((5.0,1.1),(6.4,1.1),arrowstyle='<|-|>',mutation_scale=14,linewidth=1.5))
    ax.text(5.7,.72,r'$N\leftrightarrow I$ is observable; $L,D,R$ are not uniformly identifiable',ha='center',fontsize=8.5)
    fig.tight_layout(); fig.savefig(args.out/'Figure1_reliability_framework_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 2: stage-count distribution.
    x = lengths['Stage count'].to_numpy(); n = lengths['N'].to_numpy()
    fig, ax = plt.subplots(figsize=(8.6,4.9)); ax.vlines(x,0,n,linewidth=1.2); ax.scatter(x,n,s=55)
    for xi,ni in zip(x,n):
        if ni >= 50: ax.text(xi,ni+7,str(int(ni)),ha='center',fontsize=8)
    ax.set_xlabel('Segmented stages per trajectory'); ax.set_ylabel('Trajectories'); ax.set_xticks(x)
    ax.grid(axis='y',alpha=.18); clean(ax); fig.tight_layout(); fig.savefig(args.out/'Figure2_stage_count_distribution_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 3: solve-rate forest plot.
    y = np.arange(len(agents)); rate = agents['Solve rate'].to_numpy(); lo = agents['Solve CI low'].to_numpy(); hi = agents['Solve CI high'].to_numpy()
    fig, ax = plt.subplots(figsize=(8.6,4.8)); ax.errorbar(rate,y,xerr=np.vstack([rate-lo,hi-rate]),fmt='o',capsize=5,markersize=7,linewidth=1.6)
    for i,(v,nn) in enumerate(zip(rate,agents['N'])): ax.text(v+.018,i,f'{v:.3f}  (n={int(nn)})',va='center',fontsize=9)
    ax.set_yticks(y,agents['Agent']); ax.set_xlim(.60,.89); ax.set_xlabel('Solve probability with task-level 95% bootstrap interval')
    ax.grid(axis='x',alpha=.18); clean(ax); fig.tight_layout(); fig.savefig(args.out/'Figure3_agent_solve_rates_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 4: conditional solved outcome.
    rates = [r['annotation']['solve_given_I'], r['annotation']['solve_given_no_I']]
    fig, ax = plt.subplots(figsize=(8.6,4.8)); ax.plot([0,1],rates,marker='o',linewidth=1.8)
    ax.text(0,rates[0]+.016,f"{rates[0]:.3f}",ha='center',fontsize=9); ax.text(1,rates[1]+.016,f"{rates[1]:.3f}",ha='center',fontsize=9)
    ax.set_xticks([0,1],['Any incorrect stage','No incorrect stage']); ax.set_ylim(.66,.80); ax.set_ylabel('Conditional solve probability')
    ax.grid(axis='y',alpha=.18); clean(ax); fig.tight_layout(); fig.savefig(args.out/'Figure4_incorrect_stage_outcomes_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 5: incorrect-stage position concentration.
    xx=np.arange(len(qtab)); total=qtab['All incorrect stages'].to_numpy()
    fig,ax=plt.subplots(figsize=(8.6,4.9)); ax.plot(xx,total,marker='o',linewidth=1.8); ax.scatter(xx,total,s=np.maximum(45,total*2.2))
    for i,row in qtab.iterrows(): ax.text(i,row['All incorrect stages']+9,f"{int(row['All incorrect stages'])}\nS {int(row['Solved trajectories'])} / U {int(row['Unsolved trajectories'])}",ha='center',fontsize=8)
    ax.set_xticks(xx,qtab['Normalized position']); ax.set_xlabel('Normalized workflow position'); ax.set_ylabel('Incorrect-stage occurrences')
    ax.grid(axis='y',alpha=.18); clean(ax); fig.tight_layout(); fig.savefig(args.out/'Figure5_incorrect_stage_position_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 6: observable N/I transition map.
    vals={row['Transition']:row['Probability'] for _,row in trans.iterrows()}
    fig,ax=plt.subplots(figsize=(8.8,4.6)); ax.set_xlim(0,10); ax.set_ylim(0,5); ax.axis('off')
    for lab,x0 in [('N',2.2),('I',6.2)]:
        ax.add_patch(Circle((x0,2.5),.62,fill=False,linewidth=2)); ax.text(x0,2.55,lab,ha='center',va='center',fontsize=16,fontweight='bold')
    ax.text(2.2,1.45,'No incorrect-stage\nannotation',ha='center',fontsize=9); ax.text(6.2,1.45,'Incorrect-stage\nannotation',ha='center',fontsize=9)
    ax.add_patch(FancyArrowPatch((2.85,2.75),(5.55,2.75),arrowstyle='-|>',mutation_scale=17,linewidth=2)); ax.text(4.2,3.08,f"{vals['N->I']:.4f}  entry",ha='center',fontsize=10)
    ax.add_patch(FancyArrowPatch((5.55,2.2),(2.85,2.2),arrowstyle='-|>',mutation_scale=17,linewidth=2)); ax.text(4.2,1.82,f"{vals['I->N']:.4f}  return",ha='center',fontsize=10)
    ax.add_patch(FancyArrowPatch((5.9,3.1),(6.5,3.1),arrowstyle='-|>',mutation_scale=14,linewidth=1.7,connectionstyle='arc3,rad=-1.4')); ax.text(6.2,3.9,f"{vals['I->I']:.4f}  persistence",ha='center',fontsize=10)
    ax.add_patch(FancyArrowPatch((1.9,3.1),(2.5,3.1),arrowstyle='-|>',mutation_scale=14,linewidth=1.7,connectionstyle='arc3,rad=-1.4')); ax.text(2.2,3.9,f"{vals['N->N']:.4f}  remains N",ha='center',fontsize=10)
    ax.text(8.25,2.55,'Observed layer only',ha='center',fontsize=10,fontweight='bold'); ax.text(8.25,1.95,'N is not proven correctness.\nI is not assumed latent.',ha='center',fontsize=8.5)
    fig.tight_layout(); fig.savefig(args.out/'Figure6_observed_transition_map_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 7: return and recurrence structure.
    ret=r['transitions']['return']; rec=r['transitions']['recurrence_after_return']; multi=r['transitions']['multi_episode_rate']; solret=r['transitions']['solve_given_observed_return']
    fig,ax=plt.subplots(figsize=(8.8,4.7)); ax.set_xlim(0,10); ax.set_ylim(0,5); ax.axis('off')
    for lab,pos in [('I',(2.0,2.7)),('N',(5.0,2.7)),('I',(8.0,2.7))]:
        ax.add_patch(Circle(pos,.55,fill=False,linewidth=2)); ax.text(*pos,lab,ha='center',va='center',fontsize=15,fontweight='bold')
    ax.add_patch(FancyArrowPatch((2.6,2.7),(4.4,2.7),arrowstyle='-|>',mutation_scale=16,linewidth=2)); ax.add_patch(FancyArrowPatch((5.6,2.7),(7.4,2.7),arrowstyle='-|>',mutation_scale=16,linewidth=2))
    ax.text(3.5,3.1,f'Return {ret:.4f}',ha='center',fontsize=10); ax.text(6.5,3.1,f'Recurrence {rec:.4f}',ha='center',fontsize=10)
    ax.text(5.0,1.35,f'{100*multi:.2f}% of trajectories contained multiple incorrect-state episodes',ha='center',fontsize=9)
    ax.text(5.0,.75,f'Solve probability among trajectories with an observed I→N return: {solret:.4f}',ha='center',fontsize=9)
    fig.tight_layout(); fig.savefig(args.out/'Figure7_return_recurrence_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 8: agent transition probability matrix.
    M=agents[['N->I','I->I','I->N']].to_numpy(float); fig,ax=plt.subplots(figsize=(8.6,4.9))
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            p=M[i,j]; ax.scatter(j,i,s=2200*p+90); ax.text(j,i,f'{p:.3f}',ha='center',va='center',fontsize=9)
    ax.set_xticks(range(3),['Entry to I','Persistence in I','Return to N']); ax.set_yticks(range(len(agents)),agents['Agent']); ax.set_xlim(-.55,2.55); ax.set_ylim(len(agents)-.4,-.6)
    ax.set_xlabel('Observable transition role'); ax.set_ylabel('Agent framework'); ax.grid(False); ax.tick_params(length=0)
    for spine in ax.spines.values(): spine.set_visible(False)
    fig.tight_layout(); fig.savefig(args.out/'Figure8_agent_transition_profiles_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 9: final I rate by workflow length.
    fig,ax=plt.subplots(figsize=(8.6,4.9)); ax.plot(lengths['Stage count'],lengths['Rate'],linewidth=1.2,alpha=.7); ax.scatter(lengths['Stage count'],lengths['Rate'],s=30+2*lengths['N'])
    ax.set_xlabel('Segmented stages per trajectory'); ax.set_ylabel('Final incorrect-stage rate'); ax.set_ylim(-.03,1.05); ax.grid(axis='y',alpha=.18); clean(ax)
    fig.tight_layout(); fig.savefig(args.out/'Figure9_final_incorrect_by_stage_count_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 10: position-aware transition map.
    M=np.vstack([pp['N->I'].to_numpy(float),pp['I->I'].to_numpy(float)]); fig,ax=plt.subplots(figsize=(8.6,3.9)); im=ax.imshow(M,aspect='auto')
    for i in range(2):
        for j in range(len(pp)): ax.text(j,i,f'{M[i,j]:.3f}',ha='center',va='center',fontsize=10)
    ax.set_xticks(range(len(pp)),pp['Normalized position']); ax.set_yticks([0,1],['N→I entry','I→I persistence']); ax.set_xlabel('Normalized destination-stage position'); ax.tick_params(length=0)
    for spine in ax.spines.values(): spine.set_visible(False)
    cbar=fig.colorbar(im,ax=ax,fraction=.035,pad=.025); cbar.set_label('Estimated probability')
    fig.tight_layout(); fig.savefig(args.out/'Figure10_position_aware_parameters_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 11: analytical vs Monte Carlo parity.
    xa=mc['Position-aware analytical'].to_numpy(); ym=mc['Position-aware MC'].to_numpy(); sizes=45+2*mc['Observed trajectories'].to_numpy()
    fig,ax=plt.subplots(figsize=(6.4,5.8)); ax.scatter(xa,ym,s=sizes); mn=min(xa.min(),ym.min())-.006; mx=max(xa.max(),ym.max())+.006; ax.plot([mn,mx],[mn,mx],linestyle='--',linewidth=1.2)
    ax.set_xlim(mn,mx); ax.set_ylim(mn,mx); ax.set_xlabel('Analytical final observed I-state probability'); ax.set_ylabel('Monte Carlo final observed I-state probability')
    ax.text(.03,.97,'Marker area proportional to observed trajectories',transform=ax.transAxes,va='top',fontsize=8); ax.grid(alpha=.15); clean(ax)
    fig.tight_layout(); fig.savefig(args.out/'Figure11_analytical_monte_carlo_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    # Figure 12: local sensitivity over empirical intervals.
    stage_hist=dict(zip(lengths['Stage count'].astype(int),lengths['N'].astype(int))); xs=np.array(sorted(stage_hist)); weights=np.array([stage_hist[k] for k in xs],float); weights/=weights.sum()
    init=sum(1 for _ in [1]) * 0.0
    # For trajectories with one stage, the analytical table gives the initial probability of an incorrect annotation.
    init=float(mc.loc[mc['Stage count']==1,'Position-aware analytical'].iloc[0])
    entry=r['transitions']['entry']; persistence=r['transitions']['persistence']; eci=r['transitions']['entry_ci95']; pci=r['transitions']['persistence_ci95']
    def pf(n,a,q):
        p=init
        for _ in range(2,int(n)+1): p=(1-p)*a+p*q
        return p
    def weighted(a,q): return float(np.dot(weights,[pf(n,a,q) for n in xs]))
    aeff=[weighted(eci[0],persistence),weighted(entry,persistence),weighted(eci[1],persistence)]
    qeff=[weighted(entry,pci[0]),weighted(entry,persistence),weighted(entry,pci[1])]
    fig,ax=plt.subplots(figsize=(8.6,4.2)); ax.hlines(1,aeff[0],aeff[2],linewidth=5); ax.scatter(aeff,[1,1,1],s=[65,95,65]); ax.hlines(0,qeff[0],qeff[2],linewidth=5); ax.scatter(qeff,[0,0,0],s=[65,95,65])
    for yy,arr in zip([1,0],[aeff,qeff]):
        for x in arr: ax.text(x,yy+.15,f'{x:.3f}',ha='center',fontsize=8)
    ax.set_yticks([1,0],['N→I entry\n95% interval','I→I persistence\n95% interval']); ax.set_xlabel('Weighted final observed I-state probability'); ax.set_ylim(-.45,1.45); ax.grid(axis='x',alpha=.15)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['left'].set_visible(False); ax.tick_params(axis='y',length=0)
    fig.tight_layout(); fig.savefig(args.out/'Figure12_sensitivity_v23.png',dpi=320,bbox_inches='tight'); plt.close(fig)

    print(f'Generated 12 analysis figures in {args.out}')


if __name__ == '__main__':
    main()
