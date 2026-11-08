"""Build paired Study 3 jobs from locally generated source-access trajectories.
Adapted from the additional-run controller; no stored outcomes are included.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,hashlib,json,random,shutil
MODELS=['llama','qwen','gemma','mistral']
load=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
def now():return datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
def prepare_semantics():
 folder=R;marker=folder/'freeze.json'
 if marker.exists():
  for rel,h in load(marker)['files'].items():assert sha(folder/rel)==h
  return
 bank=load(folder/'materials/item_bank.json');items={q['id']:q for q in bank};terms=load(folder/'materials/terms.json');people=load(R/'materials/personas.json');cases=[];sources={}
 for m in MODELS:
  src=EXPOSURE/'runs/main'/m;s=load(src/'checkpoint.json');assert s['completed'] and s['seed']==SEED
  calls={x['key']:x for x in map(json.loads,(src/'calls.jsonl').read_text().splitlines()) if x['status']=='completed'};seen=set()
  sources[m]=dict(checkpoint_sha256=sha(src/'checkpoint.json'),calls_sha256=sha(src/'calls.jsonl'))
  for e in s['events']:
   g=e['generated']
   if not g or e['agent']==s['source_agent']:continue
   for w in g['term_ids']:
    key=e['agent'],w
    if key in seen:continue
    seen.add(key);raw=calls[g['task_key']];prefix=raw['request']['content'].split('\nTask:\n')[0]
    assert prefix.startswith('You are one social-network user.') and 'Private initial source knowledge' not in prefix
    initial='You are one social-network user. Follow the task and remain consistent with your persona.\nPersona:\n'+people[e['agent']]+'\nYour current memory:\n\nYour activity counts: '+json.dumps(dict(write=0,read=0,comment=0))
    prior=any(x['agent']==e['agent'] and w in x['term_ids'] and (x['cycle'],x['turn'])<=(e['cycle'],e['turn']) for x in s['exposures'])
    # Match the inherited current-incoming flag; definitive exposure is audited independently.
    import re
    incoming=any(re.search(r'(?<!\w)'+re.escape(terms[w]['word'].casefold())+r'(?!\w)',x['text'].casefold()) for x in e['incoming'])
    cases.append(dict(id=f'{RUN_LABEL}_{m}_a{e["agent"]}_w{w}',model=m,agent=e['agent'],term_id=w,word=terms[w]['word'],cycle=e['cycle'],action=e['action'],original_generation_key=g['task_key'],original_request_hash=raw['request_hash'],use_prefix=prefix,initial_prefix=initial,prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),earlier_or_same_turn_exposure=prior,current_incoming_contains_term=incoming,exact_source_definition_in_prefix=terms[w]['meaning'] in prefix))
 jobs=[]
 for m in MODELS:
  cc=[c for c in cases if c['model']==m];labels=[n%4 for n in range(3*len(cc))];random.Random(SEED+MODELS.index(m)).shuffle(labels)
  for n,c in enumerate(cc):
   w=c['term_id']
   for k,qid in enumerate([f'w{w}_meaning',f'w{w}_context1',f'w{w}_context2']):
    q=items[qid];key=labels[3*n+k];ds=q['distractors'][:];random.Random(c['id']+qid).shuffle(ds);opts=ds[:];opts.insert(key,q['correct'])
    task='Answer the following four-option semantic question. Return only the digit 0, 1, 2, or 3.\n'+q['question']+'\n'+'\n'.join(f'{i}: {v}' for i,v in enumerate(opts))+'\nReturn only the selected digit.'
    sampling_seed=int(hashlib.sha256((c['id']+'/'+qid).encode()).hexdigest()[:8],16)
    for state in ['initial','use']:jobs.append(dict(key=c['id']+'/'+qid+'/'+state,case_id=c['id'],model=m,term_id=w,agent=c['agent'],kind=q['kind'],item_id=qid,state=state,correct=key,options=opts,content=c[state+'_prefix']+'\nTask:\n'+task,sampling_seed=sampling_seed))
 assert len(jobs)==len(cases)*6 and len({j['key'] for j in jobs})==len(jobs)
 for m in MODELS:
  counts=Counter(j['correct'] for j in jobs if j['model']==m and j['state']=='use')
  if counts:assert max(counts.get(k,0) for k in range(4))-min(counts.get(k,0) for k in range(4))<=1
 put(folder/'materials/cases.json',cases);put(folder/'materials/jobs.json',jobs)
 plan=load(folder/'protocol.json');plan.update(source='All first non-source agent-expression uses in rep02 exposure50, never rep01 contexts.',cases=len(cases),case_counts=dict(Counter(c['model'] for c in cases)),tested_word_union=len({c['term_id'] for c in cases}),untested_words=60-len({c['term_id'] for c in cases}),main_responses=len(jobs),sources=sources,item_bank='All180 questions frozen before rep02 simulation inference; original135 unchanged;45 additional source-based items. Case/job freeze occurs before any new semantic answers.',semantic_seed_policy='Case IDs prefixed rep02; both context states share options/order/sampling seed. No feedback.',release_note='Prepared locally from the fixed published item bank; generated contexts and responses are not committed.')
 put(folder/'protocol.json',plan)
 names=['models.json','protocol.json','run.py','materials/item_bank.json','materials/terms.json','materials/cases.json','materials/jobs.json']
 put(marker,dict(time=now(),registration='Prospective case/job freeze before semantic inference, not public preregistration.',files={n:sha(folder/n) for n in names}))

def main():
 global R,EXPOSURE,SEED,RUN_LABEL
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exposure-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--run-label',default='rep02');a=p.parse_args()
 EXPOSURE=a.exposure_dir.resolve();R=a.output.resolve();RUN_LABEL=a.run_label
 if R.exists() and any(R.iterdir()):raise ValueError('Output must be absent or empty.')
 seeds={load(EXPOSURE/'runs/main'/m/'checkpoint.json')['seed'] for m in MODELS};assert len(seeds)==1;SEED=seeds.pop()
 repo=Path(__file__).resolve().parents[2];(R/'materials').mkdir(parents=True)
 for source,dest in [(repo/'materials/models.json',R/'models.json'),(repo/'materials/personas.json',R/'materials/personas.json'),(repo/'materials/expressions.json',R/'materials/terms.json'),(repo/'evaluation/questions.json',R/'materials/item_bank.json'),(Path(__file__).with_name('run.py'),R/'run.py')]:shutil.copy2(source,dest)
 put(R/'protocol.json',{'version':'portable-study3','paired_contexts':True});prepare_semantics()
 print('Prepared local Study 3 jobs. Run:', 'python3',str(R/'run.py'))
if __name__=='__main__':main()
