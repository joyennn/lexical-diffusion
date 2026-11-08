from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;out=ROOT/'analysis/final_review';data=list(csv.DictReader((out/'verified_window_metrics.csv').open()))
fig,axes=plt.subplots(2,2,figsize=(9,6),sharex=True,sharey=True)
for ax,model in zip(axes.flat,['llama','qwen','gemma','mistral']):
 rs=sorted([r for r in data if r['model']==model and r['group']=='nonseed' and int(r['end_cycle'])-int(r['start_cycle'])==19],key=lambda r:int(r['start_cycle']))
 ax.plot([int(r['start_cycle'])+9 for r in rs],[float(r['occurrences_per100messages']) for r in rs],marker='o',color='#2468aa');ax.axvspan(100,200,color='gray',alpha=.10);ax.axvline(100,color='gray',ls='--',lw=1)
 ax.set(title=model.upper(),ylim=(0,30),xlim=(0,200),ylabel='Occurrences / 100 messages',xlabel='Recorded cycle');ax.grid(alpha=.2)
fig.suptitle('Same baseline trajectories continued to 200 cycles (no reset at 100)\nAll 60 terms, nine non-source agents; repeated uses included; points summarize 20-cycle intervals.',fontsize=10.5);fig.tight_layout();fig.savefig(out/'frequency_through200.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(out/'frequency_through200.png')
