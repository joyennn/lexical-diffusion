"""Independently audit fresh logs and expand the descriptive Study1 report.

No inference, simulation change or primary-outcome redefinition is performed.
Run after pipeline.py; inspect manuscript/main.pdf before packaging for delivery.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import csv,hashlib,json,re,statistics,subprocess,shutil,unicodedata,zipfile
ROOT=Path(__file__).resolve().parent
MODELS=['llama','qwen','gemma','mistral']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(s):return unicodedata.normalize('NFKC',s).casefold().translate({0x2019:39,0x2018:39})
def audit():
 terms=read(ROOT/'materials/terms.json');results=read(ROOT/'analysis/summary.json')
 patterns={w['id']:re.compile(r'(?<!\w)'+r'\s+'.join(re.escape(x) for x in normalize(w['word']).split())+r'(?!\w)') for w in terms}
 expected=read(ROOT/'freeze.json')['files']
 for f in sorted((ROOT/'amendments').glob('*.json')):
  for name,c in read(f).get('file_changes',{}).items():
   assert expected[name]==c['before'];expected[name]=c['after']
 assert all(sha(ROOT/k)==v for k,v in expected.items())
 diagnostics=[];digests={}
 for model in MODELS:
  folder=ROOT/'runs/main'/model;s=read(folder/'checkpoint.json');source=s['source_agent']
  assert s['completed'] and s['target_cycles']==100
  assert len(s['events'])==1000 and {(e['cycle'],e['agent']) for e in s['events']}=={(c,a) for c in range(1,101) for a in range(10)}
  calls=[json.loads(x) for x in (folder/'calls.jsonl').read_text().splitlines()]
  assert all(x['status']=='completed' and x['key'].startswith('main/') for x in calls)
  lookup={x['key']:x for x in calls};assert len(lookup)==len(calls)
  assert len(list((folder/'snapshots').glob('cycle_*.json')))==100
  generated=[e for e in s['events'] if e['generated']]
  assert len(generated)==len(s['comments'])+sum(not x['initial_material'] for x in s['posts'])
  first_use={};first_exposure={}
  for e in s['events']:
   position=e['cycle'],e['turn'];agent=e['agent']
   g=e['generated']
   if g:
    raw=lookup[g['task_key']]['output'];cap=100 if e['action']=='write' else 50
    assert raw==g['raw_text'] and raw[:cap]==g['text']
    ids=[wi for wi,pat in patterns.items() if pat.search(normalize(g['text']))]
    assert ids==g['term_ids']
    if agent!=source:
     for wi in ids:first_use.setdefault((agent,wi),position)
   for incoming in e['incoming']:
    if incoming['agent']==agent or agent==source:continue
    for wi,pat in patterns.items():
     if pat.search(normalize(incoming['text'])):first_exposure.setdefault((agent,wi),position)
  rows=[x for x in results['terms'] if x['model']==model];observed=[];half=[]
  for row in rows:
   wi=row['term_id'];linked=sorted(u for (a,w),u in first_use.items() if w==wi and (a,w) in first_exposure and first_exposure[a,w]<=u)
   allusers=[u for (a,w),u in first_use.items() if w==wi]
   assert row['exposure_linked_first_users']==len(linked) and row['all_first_users']==len(allusers)
   assert row['exposed_agents']==sum(w==wi for a,w in first_exposure)
   assert row['time_first_linked_use']==(linked[0][0] if linked else None)
   assert row['time_50percent']==(linked[4][0] if len(linked)>=5 else None)
   assert row['time_first_linked_use_observed']==bool(linked) and row['time_50percent_observed']==(len(linked)>=5)
   assert row['time_first_linked_use_followup']==100 and row['time_50percent_followup']==100
   if linked:observed.append(linked[0][0])
   if len(linked)>=5:half.append(dict(word=row['word'],cycle=linked[4][0]))
  diagnostics.append(dict(model=model,unique_main_calls=len(calls),completed_turns=1000,unexposed_terms=sum(x['exposed_agents']==0 for x in rows),exposed_agent_term_pairs=len(first_exposure),linked_agent_term_first_users=sum(x['exposure_linked_first_users'] for x in rows),first_use_observed_terms=len(observed),first_use_censored_terms=60-len(observed),first_use_conditional_median=statistics.median(observed),full_set_first_use_median_reached=len(observed)>=30,half_population_events=half,half_population_censored_terms=60-len(half),write_turns=sum(e['action']=='write' for e in s['events']),read_turns=sum(e['action'] in ['read','comment'] for e in s['events']),source_generated_messages=sum(e['agent']==source for e in generated)))
  digests[model]={'checkpoint_sha256':sha(folder/'checkpoint.json'),'calls_sha256':sha(folder/'calls.jsonl')}
 report=dict(verified_at=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),all_four_new_100cycle_runs_complete=True,primary_metrics_independently_reconstructed=True,frozen_source_amendment_chain_verified=True,no_prior_results_used=True,pilots_excluded=True,diagnostics=diagnostics,input_hashes=digests)
 out=ROOT/'qa';out.mkdir(exist_ok=True);(out/'completion_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 with (ROOT/'analysis/exposure_and_timing_diagnostics.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(diagnostics[0]));writer.writeheader();writer.writerows(diagnostics)
 return report
def main():
 # This expanded narrative describes the delivered dataset only; new runs use write_results.py.
 expected_calls={'llama': '4d85bcf2e4c4250130a2ea08eb960be49015943b20e8d90410d9da8dccc2b9f0', 'qwen': '402c453817b1631502b7051f553c47dfca2f7e5404e8091b750fd5e645a19fc7', 'gemma': 'ad21eed1e1efab62d6380942a8557fed1fa82c4c13ee1213c296393aa79e5e86', 'mistral': '65907a19f892346f1984638beacae8abc21aaa30ebd66b229c20550ceb7b3924'}
 if any(sha(ROOT/'runs/main'/m/'calls.jsonl')!=h for m,h in expected_calls.items()):
  raise RuntimeError('Dataset-specific narrative: new trajectories must use write_results.py and receive a new scientific review.')
 report=audit()
 import write_results
 write_results.main()  # regenerates the numerical base from current fresh data
 d=read(ROOT/'analysis/summary.json');diag=report['diagnostics'];paper=ROOT/'manuscript/main.tex';s=paper.read_text()
 s=s.replace('Terms reaching5/9','Terms reaching 5/9')
 s=s.replace('One trajectory per configuration supports descriptive within-system comparisons, not model-population inference, semantic-acquisition claims or validation of human diffusion.','Only 7--16 of the sixty words have an exposure-linked first user by cycle100, and two model--word cases reach five of nine nonseed users. Most timing endpoints are censored. These descriptive trajectories do not establish model-population effects, semantic acquisition or human diffusion.')
 start=s.index('\\section{Background and measurement rationale}')
 end=s.index('\\section{Fresh experimental design}',start)
 s=s[:start]+r'''\section{Background and measurement rationale}
\subsection{Diffusion, opportunity and operational adoption}
IDT directs attention to what is communicated, through which channels, over what time and across which social participants \cite{rogers2003}. In computational systems, the measured adoption event must nevertheless be specified. Repeating an expression is not the same as gaining a new user, and a new user is not necessarily a new learner. Cascade structure and size depend on exposure and updating rules \cite{watts2002,centola2007,goel2016}. A frequent poster can inflate total occurrences without expanding the set of participating agents.
The shared feed creates opportunities that are partly endogenous to model action choices. Writing adds public material, while reading accesses a limited part of the growing pool. Consequently, a model can generate many messages while exposing few nonseed agents to the selected word set. Scheduled turns, realized reads, actual term-bearing inputs and first uses must therefore remain distinguishable. Our reach denominator is the nine nonseed agents, and we separately report realized exposure coverage.
\subsection{Memory and configured artificial agents}
Generative agents combine language-model outputs with explicit observations, memories and action rules \cite{park2023}. Persona descriptions and memory fields are modelling components rather than evidence of human fidelity. Structured documentation helps expose these implementation assumptions \cite{grimm2020odd}. Here the source's persistent glossary, other agents' bounded mutable memory, sequential execution and visible-comment window are explicit parts of the studied system.
Work on emergent conventions already establishes that communicating LLM populations can develop collective patterns \cite{ashery2025}. Merely observing repeated words or differences among model names would add limited explanation. The present study instead supplies an auditable mapping from published input exposure to first literal use, preserves non-use and pre-exposure use, and distinguishes distributed reach from output volume. It is an exploratory measurement study of configured systems, not a new architecture or universal diffusion theory.
\subsection{Circulation and meaning-related outcomes}
Human sharing and knowledge-related outcomes also require separate measurements: sharing without clicking does not prove that an individual has no understanding, and sharing can increase subjective knowledge without reading \cite{sundar2025sharing,ward2023sharing}. These findings motivate a conceptual distinction among circulation, access and knowledge. They do not validate LLM agents as human proxies or show that the same psychological mechanisms operate in both populations.
Natural neologisms present a further difficulty: dictionary recentness does not guarantee absence from model training, and the same form can have multiple senses. Literal matching therefore identifies form use rather than semantically verified adoption. We retain first uses that precede any observed local exposure as a separate diagnostic. Even a first use following exposure remains an operational event; inference, prior familiarity and the shared task context remain alternative explanations.
''' + s[end:]
 modeltext=r'''\subsection{Model selection and recorded configurations}
The study uses four instruction-tuned open-weight configurations from distinct development families: Meta-Llama-3-8B-Instruct, Qwen3-8B, Gemma-2-9B-IT and Mistral-7B-Instruct-v0.3 \cite{llama3card,qwen3card,gemma2card,mistral7bcard}. Their approximate seven-to-nine-billion parameter range and available four-bit MLX conversions make sequential local execution feasible. Selection targets reproducible local comparison across four families, not state-of-the-art ranking or a random sample of all LLMs.
Both source model names and community conversion revisions are fixed in models.json. The runs use an Apple M1 Pro with fourteen GPU cores and16GB unified memory. Each model is loaded separately; hardware speed is not the diffusion-speed outcome. Native templates, training, tokenizers and quantization errors differ. Shared sampling settings and character ceilings do not isolate a pure architecture effect or establish equal effective capacity. Numerical action labels are counterbalanced by task, and a recorded pre-main technical amendment accommodates Mistral's empty-prefix tokenizer token without changing the allowed0/1output decisions.
'''
 s=s.replace('\\section{Outcomes and analysis}',modeltext+'\\section{Outcomes and analysis}',1)
 resultstart=s.index('LLAMA has ');resultend=s.index('\\begin{figure*}',resultstart)
 paragraph='\\subsection{Distributed reach and finite-horizon timing}\n'
 paragraph+='Across the four trajectories, qualifying first-use counts are 16,9,10 and24 agent--term pairs for Llama,Qwen,Gemma and Mistral, respectively, out of540 possible nonseed agent--term pairs per configuration. Mean final reach is therefore 3.0,1.7,1.9 and4.4\\%. Only9,9,7 and16 of the sixty words have any qualifying first user. These figures describe this initial state and trajectory; they are not model rankings with replicated uncertainty.\n\n'
 paragraph+='Most speed outcomes are administratively censored at cycle100. The median time to first qualifying use over the full sixty-word set is not reached in any model. Table~\\ref{tab:timing} gives the number censored and, only as a conditional description, the median among words with an observed event. Conditional medians must not be interpreted as whole-set diffusion speeds or used to discard unsuccessful words. Only Galentine\'s Day in Llama reaches five of nine nonseed first users (cycle85), and alpha in Mistral reaches that threshold (cycle60). The other238 of240 model--word half-population endpoints are censored.\n\n'
 paragraph+='\\begin{table*}[t]\\centering\\small\\caption{Finite-horizon timing and exposure diagnostics for all sixty words. Conditional median refers only to words with an observed first-use event; the full-set median is unreached in all four configurations.}\\label{tab:timing}\\begin{tabular}{lrrrrr}\\hline Model&First-use events&First-use censored&Conditional median cycle&Never-exposed words&Exposed agent--term pairs\\\\\\hline\n'
 for x in diag:
  paragraph+=f"{x['model'].upper()} & {x['first_use_observed_terms']} & {x['first_use_censored_terms']} & {x['first_use_conditional_median']:.1f} & {x['unexposed_terms']} & {x['exposed_agent_term_pairs']}/540 \\\\\n"
 paragraph+='\\hline\\end{tabular}\\end{table*}\n'
 paragraph+='\\subsection{Exposure opportunities and normalized output}\n'
 paragraph+='Read turns number296,115,242 and335 across Llama,Qwen,Gemma and Mistral; the corresponding write turns are704,885,758 and665. Only75,19,68 and113 nonseed agent--term pairs receive recorded external exposure. In Qwen,44of60words are never externally encountered by any nonseed agent. Limited observed reach must therefore be interpreted alongside limited opportunity, rather than as evidence of inability to use an encountered word. This association is descriptive because actions and exposures are endogenous.\n\n'
 paragraph+='Generated-message totals include the source agent, whereas reach excludes it. Source-generated messages number79,88,100 and87, respectively. Initial exogenous posts are excluded from all generated-output totals. Nonseed first uses preceding recorded exposure number3,0,0 and4 and remain separate from qualifying uptake.\n\n'
 paragraph+='Posts have greater total lexical occurrence counts in all four trajectories. After message normalization, Qwen comments have27.4occurrences per100messages versus17.1for posts; the other three configurations favour posts. Different numbers of read/write opportunities and different post/comment length limits prevent a causal channel interpretation.\n\n'
 paragraph+='The fixed character ceilings materially affect transmitted output. For example,549of704Llama posts and139of144Llama comments exceed their respective ceilings and are truncated; the corresponding Gemma counts are70of758and43of102. Complete rates and raw outputs are retained in channel_metrics.csv and calls.jsonl. The primary analysis uses the actually transmitted prefix. An untruncated-generation recount would be a separate diagnostic, not the exposure history that actually occurred.\n\n'
 s=s[:resultstart]+paragraph+s[resultend:]
 s=s.replace('The outcomes separate distributed first use from repeated lexical output.','The observed reach is low and most timing outcomes remain unresolved within100cycles. Unequal realized reads, declining access to source material in a growing public pool, and character truncation are implementation conditions consistent with the observations, not experimentally isolated causes. A controlled follow-up should equalize exposure opportunities and separately intervene on memory while retaining the same model configurations.\n\nThe outcomes separate distributed first use from repeated lexical output.')
 replacements={
  'cycle100':'cycle 100','cycle85':'cycle 85','cycle60':'cycle 60','within100cycles':'within 100 cycles',
  '16,9,10 and24':'16, 9, 10 and 24','out of540':'out of 540','3.0,1.7,1.9 and4.4':'3.0, 1.7, 1.9 and 4.4',
  'Only9,9,7 and16':'Only 9, 9, 7 and 16','other238 of240':'other 238 of 240',
  'number296,115,242 and335':'number 296, 115, 242 and 335','are704,885,758 and665':'are 704, 885, 758 and 665',
  'Only75,19,68 and113':'Only 75, 19, 68 and 113','Qwen,44of60words':'Qwen, 44 of 60 words',
  'number79,88,100 and87':'number 79, 88, 100 and 87','number3,0,0 and4':'number 3, 0, 0 and 4',
  'have27.4occurrences per100messages versus17.1for':'have 27.4 occurrences per 100 messages versus 17.1 for',
  'example,549of704Llama':'example, 549 of 704 Llama','and139of144Llama':'and 139 of 144 Llama',
  'are70of758and43of102':'are 70 of 758 and 43 of 102','and16GB':'and 16 GB','allowed0/1output':'allowed 0/1 output',
  'channel_metrics.csv':r'\texttt{channel\_metrics.csv}',
 }
 for old,new in replacements.items():s=s.replace(old,new)
 s=s.replace('Model&First-use events&First-use censored&Conditional median cycle&Never-exposed words&Exposed agent--term pairs',r'Model&\shortstack{First-use\\events}&\shortstack{First-use\\censored}&\shortstack{Conditional median\\cycle}&\shortstack{Never-exposed\\words}&\shortstack{Exposed agent--term\\pairs}')
 s=s.replace('Mean qualifying nonseed reach over the sixty selected words. Lines are descriptive trajectories, not averages over independent runs.','Mean qualifying nonseed reach over the sixty selected words. Left: full percentage range. Right: detail over 0--5.5\\%. Lines are single descriptive trajectories, not averages over independent runs.')
 paper.write_text(s)
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 curves=list(csv.DictReader((ROOT/'analysis/adoption_curves.csv').open()))
 fig,axes=plt.subplots(1,2,figsize=(9,3.7))
 for ax,title,upper in zip(axes,['Full scale','Detail (0--5.5%)'],[100,5.5]):
  for model in MODELS:
   rows=[x for x in curves if x['model']==model]
   values=[100*sum(int(x['linked_users']) for x in rows if int(x['cycle'])==c)/(60*9) for c in range(101)]
   ax.plot(range(101),values,label=model.upper())
  ax.set(xlabel='Recorded cycle',ylabel='Mean nonseed reach (%)',ylim=(0,upper),title=title);ax.grid(alpha=.2)
 axes[0].legend(frameon=False);fig.tight_layout()
 for ext in ['pdf','png']:fig.savefig(ROOT/'manuscript/figures'/('figure1.'+ext),dpi=220,bbox_inches='tight')
 plt.close(fig)
 bib=ROOT/'manuscript/references.bib';b=bib.read_text()
 if 'gemma2card' not in b:
  b+='\n@misc{gemma2card,author={{Google}},title={{Gemma 2 9B IT Model Card}},year={2024},howpublished={\\url{https://huggingface.co/google/gemma-2-9b-it}}}\n@misc{mistral7bcard,author={{Mistral AI}},title={{Mistral-7B-Instruct-v0.3 Model Card}},year={2024},howpublished={\\url{https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3}}}\n'
  bib.write_text(b)
 subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-silent','main.tex'],cwd=ROOT/'manuscript',check=True)
 shutil.copy2(ROOT/'manuscript/main.pdf',ROOT.parent/'output/fresh_study1_manuscript.pdf')
 print('Expanded fresh-only numerical report compiled. Inspect PDF before final packaging.')
if __name__=='__main__':main()
