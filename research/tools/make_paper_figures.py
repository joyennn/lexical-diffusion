from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':12,'axes.titlesize':13,'axes.labelsize':12,'xtick.labelsize':10.5,'ytick.labelsize':10.5,'legend.fontsize':11})
import argparse
_parser=argparse.ArgumentParser(description='Recreate paper figures from a restored audited workspace.')
_parser.add_argument('--workspace',type=Path,required=True);_parser.add_argument('--output',type=Path,required=True)
_args=_parser.parse_args();R=_args.output.resolve();R.mkdir(parents=True,exist_ok=True);W=_args.workspace.resolve()
def rows(p):return list(csv.DictReader(p.open()))
def main():
 colors={'baseline':'#283F5B','exposure':'#007A73','memory4000':'#C66B28'};fig,axs=plt.subplots(2,2,figsize=(9,6.5))
 for ax,m in zip(axs.flat,['llama','qwen','gemma','mistral']):
  rr=rows(W/'study2_mechanisms/time200/analysis/final_review/verified_window_metrics.csv');rr=[x for x in rr if x['model']==m and x['group']=='nonseed' and int(x['end_cycle'])-int(x['start_cycle'])==19];rr.sort(key=lambda x:int(x['start_cycle']));ax.plot([int(x['start_cycle'])+9.5 for x in rr],[float(x['occurrences_per100messages']) for x in rr],'-o',color=colors['baseline'],label='Baseline and continuation',markersize=4)
  rr=rows(W/'study2_mechanisms/exposure50/analysis/final_review/verified_twenty_cycle_bins.csv')
  rr=[x for x in rr if x['model']==m and x['group']=='nonseed' and x.get('study')=='exposure50'];rr.sort(key=lambda x:int(x['start_cycle']));ax.plot([int(x['start_cycle'])+9.5 for x in rr],[100*int(x['occurrences'])/int(x['messages']) for x in rr],'-s',color=colors['exposure'],label='Source recommendation',markersize=4)
  rr=[x for x in rows(W/'study2_mechanisms/memory4000/analysis/final_review/verified_intervals.csv') if x['model']==m and x['group']=='nonseed' and x['study']=='memory4000'];rr.sort(key=lambda x:int(x['start_cycle']));ax.plot([int(x['start_cycle'])+9.5 for x in rr],[float(x['occurrences_per100messages']) for x in rr],'-^',color=colors['memory4000'],label='Memory trigger 4000',markersize=4)
  ax.axvline(100,color='gray',ls=':',lw=1);ax.set_title(m.capitalize());ax.set_xlabel('Simulation cycle');ax.set_ylabel('Occurrences per 100 messages');ax.set_ylim(bottom=0);ax.set_xlim(0,201);ax.grid(alpha=.18)
 handles,labels=axs.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False);fig.tight_layout(rect=(0,.06,1,1));fig.savefig(R/'figure1_circulation.png',dpi=1200);fig.savefig(R/'figure1_circulation.svg');fig.savefig(R/'figure1_circulation.pdf');plt.close(fig)
 p=W/'study3_semantics/analysis/accuracy_summary.csv'
 if not p.exists():return
 rr=rows(p);fig,axs=plt.subplots(1,2,figsize=(8,3.8),sharey=True)
 for ax,k in zip(axs,['meaning','application']):
  for off,state,label,color in [(-.17,'initial','Initial',colors['baseline']),(.17,'use','Pre-generation',colors['exposure'])]:
   vals=[100*float(next(x for x in rr if x['model']==m and x['kind']==k and x['state']==state)['macro_word_accuracy']) for m in ['llama','qwen','gemma','mistral']];bars=ax.bar([i+off for i in range(4)],vals,width=.32,label=label,color=color)
   # Exact values are reported in Table4; omit crowded duplicate bar labels.
  ax.axhline(25,color='gray',ls='--',lw=1);ax.set_xticks(range(4),['Llama','Qwen','Gemma','Mistral']);ax.set_title('Definition identification' if k=='meaning' else 'Novel scenario selection');ax.set_ylim(0,110);ax.set_ylabel('Word macro accuracy (%)');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
 fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False);fig.tight_layout(rect=(0,.08,1,1));fig.savefig(R/'figure2_semantics.png',dpi=190);plt.close(fig)
if __name__=='__main__':main()
