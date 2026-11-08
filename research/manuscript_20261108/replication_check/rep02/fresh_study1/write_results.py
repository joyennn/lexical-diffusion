"""Plot only new completed data, write a clean manuscript, and package outputs."""
from pathlib import Path
import json,csv,subprocess,hashlib,zipfile,os
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def esc(s):
 for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:s=s.replace(a,b)
 return s
def main():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 d=read(ROOT/'analysis/summary.json');assert d['complete']
 folder=ROOT/'manuscript';figs=folder/'figures';figs.mkdir(exist_ok=True)
 curves=list(csv.DictReader((ROOT/'analysis/adoption_curves.csv').open()));models=['llama','qwen','gemma','mistral']
 for endpoint,label,name in [('mean','Mean exposure-linked nonseed reach','figure1'),('any','Fraction of 60 terms with a linked first user','figure2')]:
  fig,ax=plt.subplots(figsize=(7,3.6))
  for m in models:
   rows=[x for x in curves if x['model']==m];values=[]
   for c in range(101):
    z=[int(x['linked_users']) for x in rows if int(x['cycle'])==c]
    values.append(sum(z)/(60*9) if endpoint=='mean' else sum(v>0 for v in z)/60)
   ax.plot(range(101),values,label=m.upper())
  ax.set(xlabel='Recorded simulation cycle',ylabel=label,ylim=(0,1));ax.grid(alpha=.2);ax.legend(frameon=False);fig.tight_layout()
  for ext in ['pdf','png']:fig.savefig(figs/(name+'.'+ext),dpi=220,bbox_inches='tight')
  plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(8,3.6))
 for ax,key,title in zip(axs,['lexical_occurrences','occurrences_per_100_messages'],['Generated lexical occurrences','Occurrences per 100 messages']):
  for ch,offset in [('post',-.18),('comment',.18)]:
   vals=[next(x[key] for x in d['channel_metrics'] if x['model']==m and x['channel']==ch) for m in models]
   ax.bar([i+offset for i in range(4)],[v if v is not None else 0 for v in vals],width=.36,label=ch.title())
  ax.set_xticks(range(4),[m.upper() for m in models],rotation=20);ax.set_title(title);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
 axs[0].legend(frameon=False);fig.tight_layout()
 for ext in ['pdf','png']:fig.savefig(figs/('figure3.'+ext),dpi=220,bbox_inches='tight')
 plt.close(fig)
 def fig(n,caption):return '\\begin{figure*}[t]\\centering\\includegraphics[width=\\textwidth]{figures/figure'+str(n)+'.pdf}\\caption{'+caption+'}\\end{figure*}\n'
 front=(folder/'frontmatter.tex').read_text()
 tex=front+r'''
\begin{abstract}
Lexical frequency alone does not identify how widely or quickly an expression is taken up by other agents. We conduct a fresh exploratory social-network simulation using four pinned four-bit open-weight model configurations: Llama 3 8B Instruct, Qwen3-8B, Gemma 2 9B IT and Mistral 7B Instruct v0.3. Each configuration runs for 100 cycles with ten fixed personas and sixty author-supplied neologisms. One source agent supplies initial material; other agents do not receive a bulk initial read. We record actual input exposure, generated posts and comments, memory updates and first-use events. Diffusion size is operationalized as unique nonseed first users following recorded external exposure; pre-exposure uses are reported separately. Time-to-first-use and half-population thresholds retain non-use as censored observations. Total and normalized lexical output are distinguished from distributed uptake. All observations are newly generated; no previous experimental outcomes are pooled. One trajectory per configuration supports descriptive within-system comparisons, not model-population inference, semantic-acquisition claims or validation of human diffusion.
\end{abstract}
\begin{keywords}LLM agents, lexical diffusion, exposure, first-use timing, open-weight models, reproducibility\end{keywords}
\titlepgskip=-21pt
\maketitle
\section{Introduction}
Generative agents enable the study of interacting artificial systems through explicit inputs, memories and updating rules \cite{park2023,ashery2025}. Innovation Diffusion Theory motivates attention to innovations, channels, time and social participation \cite{rogers2003}. However, repeated output, the number of distinct users and elapsed cycles to first use are different quantities. A common word can also appear without recorded local exposure because the model already encountered it during training. We therefore distinguish observable exposure-linked lexical uptake from pre-exposure use and semantic understanding.
This report presents newly executed Study 1 only. The questions concern final distributed reach, finite-horizon uptake timing, and differences between total and opportunity-normalized lexical output in the four tested configurations. Previously generated observations are not used as evidence. A subsequent controlled study would need to examine the contributions of exposure and memory separately.
\section{Background and measurement rationale}
Cascade structure and size depend on exposure and network rules \cite{watts2002,centola2007,goel2016}. Generative-agent memory and persona descriptions are modelling components rather than guarantees of human fidelity \cite{park2023,grimm2020odd}. Work on emergent conventions already establishes collective behaviour in LLM populations \cite{ashery2025}. Our contribution is a documented finite-horizon measurement design across four open-weight configurations, not a new general diffusion law.
Human sharing and knowledge-related outcomes also require distinct measurements: sharing without clicking does not prove an individual has no understanding, and sharing can increase subjective knowledge without reading \cite{sundar2025sharing,ward2023sharing}. These findings motivate separate operational outcomes; they do not validate our agents as human proxies. Literal word matching cannot establish correct semantic use.
\section{Fresh experimental design}
The sixty neologisms and ten persona descriptions come from the author-supplied materials and are held fixed across models. No claim is made that the words are absent from pretraining or that the personas represent a human population. One missing original example, shadow banning, is omitted while its word, definition and available origin text remain. No replacement example is invented.
Exactly one source agent has a persistent private glossary and authors sixty exogenous initial source posts at cycle zero. The other agents initially have empty mutable memories and are never made to read the complete seed set. The public posts constitute potential exposure; a term enters another agent's observed input only when that agent encounters the post or an included comment. The source is excluded from reach denominators.
Each of 100 cycles gives agents 0--9 one sequential turn. A constrained, label-counterbalanced binary model decision selects reading or writing. A read samples one unread other-authored post using a fixed random stream; up to three latest comments on that post are included. A second binary decision selects reading alone or commenting. Later agents can encounter earlier same-cycle outputs. These are specified sequential scheduling effects, not synchronous interactions. Comments can enter future readers' inputs in this new experiment.
Posts are capped at 100 characters and 40 generated tokens, comments at 50 characters and 20 tokens. The untruncated output is retained. Mutable memory exceeding 1000 characters is summarized before the next turn, with a 500-character transmitted summary ceiling and 100 generated-token ceiling. The source glossary remains outside that mutable cap. Errors and empty generations stop execution; they are never converted to memory-as-message outputs.
All four instruction models use pinned community MLX conversions and temperature 0.9/top-p 0.9 on the same local Apple GPU, one model at a time. The same task content is supplied as one user message through each native chat template; Qwen thinking is disabled. The numeric action format is imposed rather than treated as a fidelity finding. Full identifiers, hashes, library versions, prompts, seeds, responses and stopping metadata accompany the data. Four-bit settings do not imply identical quantization errors or isolate model architecture from training differences.
\section{Outcomes and analysis}
For each term and nonseed agent, we locate the first literal generated use and first recorded other-author input containing that form. A qualifying first user has external exposure at or before its first-use turn. Same-turn exposure precedes comment generation and may have zero cycle lag. A first use preceding any such exposure is recorded separately; it is not later relabelled as a first transmitted adoption. The measurement is operational and does not establish that exposure caused use.
Size is the number of qualifying distinct agents out of nine. Speed includes the first qualifying-use cycle, reaching five of nine nonseed users, and exposure-to-use lag. An unreached threshold has a null event time, event indicator zero and follow-up 100; non-adopting terms are retained. Cumulative curves display all sixty selected terms, not just successful cases. Initial source posts are excluded from generated output, and message and character denominators accompany occurrence counts.
There is one fresh trajectory per model. Agents, words, cycles and pilot runs are not independent model repetitions. We report descriptive distributions and curves without between-model significance tests or confidence intervals inferred from within-run pseudoreplication. Any future repetition or controlled extension must be reported as additional work.
\section{Fresh results}
'''
 tex+='\\begin{table*}[t]\\centering\\small\\caption{Fresh 100-cycle trajectory summaries. Reach concerns qualifying nonseed first users; model-level independent trajectories equal one.}\\begin{tabular}{lrrrrr}\\hline Model&Cycles&Messages&Mean reach (\\%)&Terms with linked use&Terms reaching5/9\\\\\\hline\n'
 for x in d['models']:tex+=f"{x['model'].upper()} & {x['cycles']} & {x['generated_messages']} & {100*x['mean_linked_reach']:.1f} & {x['words_ever_linked_used']}/60 & {x['words_reaching_50percent']}/60 \\\\\n"
 tex+='\\hline\\end{tabular}\\end{table*}\n'
 for x in d['models']:
  tex+=esc(x['model'].upper())+' has '+str(x['preexposure_agent_term_first_uses'])+' nonseed agent--term first uses preceding recorded external exposure. Those cases are not counted as qualifying first users.\n\n'
 tex+=fig(1,'Mean qualifying nonseed reach over the sixty selected words. Lines are descriptive trajectories, not averages over independent runs.')
 tex+=fig(2,'Fraction of the full sixty-word set with at least one qualifying nonseed first use by each recorded cycle. Unreached words remain in the denominator.')
 tex+=fig(3,'Total and message-normalized lexical occurrences in generated posts and comments, excluding exogenous initial material. Channel differences do not establish causal influence.')
 tex+=r'''
\section{Discussion and limits}
The outcomes separate distributed first use from repeated lexical output. Model-specific observations concern the exact pinned configurations and this particular initial state, seed role, source reservoir and sequential read/write protocol. Familiar words can be used before local exposure, while post-exposure use still does not prove new semantic acquisition. The source receives an explicit information advantage; its exclusion from reach avoids counting the initial reservoir as uptake.
Conditional output counts depend on the model's action choices, character ceilings and exposure opportunities. Memory summaries and native templates are additional implementation conditions. A single trajectory cannot establish typical behaviour or model rankings. The 100-cycle horizon permits administrative censoring, not a claim of saturation or ergodicity. Human adoption, psychological mechanisms and policy effects require external validation.
\section{Conclusion}
This fresh Study 1 supplies full source-to-exposure-to-first-use records for four open-weight configurations over 100 cycles. The dataset supports auditable descriptive size and timing measurements while retaining pre-exposure use and non-use. Controlled causal and semantic claims remain outside this exploratory evidence.
\section*{Reproducibility}
The accompanying repository package contains the protocol, input provenance, pinned model manifest, complete raw request logs, per-cycle states, exposure records, analysis scripts and derived CSV files. Model weights are downloaded separately and are not included. A separate three-cycle technical pilot is excluded from all main results. No previous simulation observations are used as new evidence.
\EOD
\bibliographystyle{IEEEtran}
\bibliography{references}
\end{document}
'''
 (folder/'main.tex').write_text(tex)
 subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-silent','main.tex'],cwd=folder,check=True)
 out=ROOT.parent/'output';out.mkdir(exist_ok=True)
 import shutil
 shutil.copy2(folder/'main.pdf',out/'fresh_study1_manuscript.pdf')
 for name,include in [('fresh_study1_code_and_data.zip','all'),('fresh_study1_data.zip','data')]:
  with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED) as z:
   for f in ROOT.rglob('*'):
    if not f.is_file() or any(x in f.parts for x in ['models','.cache','__pycache__']):continue
    if f.suffix in ['.aux','.log','.fls','.fdb_latexmk','.blg']:continue
    if include=='data' and f.relative_to(ROOT).parts[0] not in ['runs','analysis','materials']:continue
    z.write(f,Path('fresh_study1')/f.relative_to(ROOT))
 (ROOT/'report_ready.json').write_text(json.dumps(dict(time=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),data_complete=True,manuscript_compiled=True,visual_QA_pending=True)))
 print('Fresh manuscript and packages built; PDF visual review still required.',flush=True)
if __name__=='__main__':main()
