"""Verified all60 frequency trajectories; no manuscript."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;out=ROOT/'analysis/final_review';data=list(csv.DictReader((out/'verified_twenty_cycle_bins.csv').open()))
fig,axes=plt.subplots(2,2,figsize=(9,6),sharex=True,sharey=True)
for ax,m in zip(axes.flat,['llama','qwen','gemma','mistral']):
 for study,label,color in [('baseline','Baseline','#2468aa'),('exposure50','50% recommendation policy','#dc7633')]:
  rs=sorted([r for r in data if r['study']==study and r['model']==m and r['group']=='nonseed'],key=lambda r:int(r['start_cycle']))
  ax.plot([10,30,50,70,90],[100*int(r['occurrences'])/int(r['messages']) for r in rs],label=label,color=color,marker='o')
 ax.set(title=m.upper(),ylim=(0,35),ylabel='Occurrences / 100 messages');ax.set_xticks([10,30,50,70,90],['1–20','21–40','41–60','61–80','81–100']);ax.tick_params(labelbottom=True);ax.grid(alpha=.2)
axes.flat[0].legend(frameon=False,fontsize=8);fig.suptitle('All 60 words, nine non-source agents, repeated uses included\nOne exploratory trajectory per model and policy; 20-cycle intervals.',fontsize=11);fig.tight_layout();fig.savefig(out/'frequency_by_interval.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(out/'frequency_by_interval.png')
