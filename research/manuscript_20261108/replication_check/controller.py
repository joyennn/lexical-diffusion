"""Resume-safe orchestration of exactly one additional seed. Never runs manuscript builders."""
from pathlib import Path
from collections import Counter
import fcntl,hashlib,json,os,random,shutil,subprocess,sys,time,traceback
from setup import R,W,NEW,SEED,MODELS,PATHS,load,put,sha,now

def status(state,**kwargs):
 row=dict(status=state,time=now(),**kwargs);put(R/'status.json',row);print(json.dumps(row,ensure_ascii=False),flush=True)
def verify_originals():
 for rel,h in load(R/'original_manifest.json').items():assert sha(W/rel)==h,'Original input/output changed: '+rel
def verify_freeze():
 for rel,h in load(R/'freeze.json')['files'].items():assert sha(R/rel)==h,'Frozen replication file changed: '+rel
def check_stop():
 if (R/'STOP').exists():raise RuntimeError('User/operator STOP: explicit resume required.')
 if shutil.disk_usage(R).free<8*1024**3:raise RuntimeError('Less than8GiB disk space remains; checkpoints preserved.')
def command(args,cwd):
 check_stop();verify_freeze()
 env=dict(os.environ,MODEL_STORE=str(W/'local_gpu_check/models'),PYTHONUNBUFFERED='1')
 process=subprocess.Popen([sys.executable,*map(str,args)],cwd=cwd,env=env)
 put(R/'active_child.json',dict(pid=process.pid,cwd=str(cwd),arguments=list(map(str,args)),started=now()))
 while True:
  try:
   code=process.wait(timeout=10);break
  except subprocess.TimeoutExpired:
   if (R/'STOP').exists() or shutil.disk_usage(R).free<8*1024**3:
    # The unmodified runner checks its local STOP before each uncached call.
    (Path(cwd)/'STOP').touch()
 if code:raise subprocess.CalledProcessError(code,[sys.executable,*map(str,args)])
def run_network(condition,cycles):
 folder=NEW/PATHS[condition];runner='run_exposure.py' if condition=='exposure50' else 'run_study1.py'
 for m in MODELS:
  check_stop();done=folder/'runs/main'/m/'completed.json'
  if done.exists():
   dd=load(done);assert dd['cycles']==cycles and dd['seed']==SEED;continue
  status('network_running',condition=condition,model=m,target_cycles=cycles,replication='rep02',new_seed=SEED)
  command([runner,'--model',m,'--stage','main','--cycles',cycles,'--hours',96],folder)
def prepare_continuation():
 dest=NEW/PATHS['time200'];base=NEW/PATHS['baseline'];marker=dest/'lineage.json'
 if marker.exists():return
 models={}
 for m in MODELS:
  source=base/'runs/main'/m;s=load(source/'checkpoint.json');assert s['completed'] and s['target_cycles']==100 and s['seed']==SEED
  origin=dest/'origin'/m;origin.mkdir(parents=True,exist_ok=True)
  shutil.copy2(source/'checkpoint.json',origin/'checkpoint_100.json');shutil.copy2(source/'calls.jsonl',origin/'calls_1_100.jsonl')
  run=dest/'runs/main'/m;run.mkdir(parents=True,exist_ok=True)
  assert not (run/'completed.json').exists()
  shutil.copy2(source/'calls.jsonl',run/'calls.jsonl');s.update(target_cycles=200,completed=False);put(run/'checkpoint.json',s)
  models[m]=dict(source_checkpoint=str(source/'checkpoint.json'),source_checkpoint_sha256=sha(source/'checkpoint.json'),source_calls_sha256=sha(source/'calls.jsonl'),source_calls_bytes=(source/'calls.jsonl').stat().st_size,source_completed_calls=len((source/'calls.jsonl').read_text().splitlines()),continuation_start_cycle=101)
 put(marker,dict(time=now(),baseline_root=str(base),runner_sha256=sha(dest/'run_study1.py'),models=models))
 assert sha(dest/'run_study1.py')==sha(base/'run_study1.py')

def prepare_semantics():
 folder=NEW/PATHS['semantics'];marker=folder/'freeze.json'
 if marker.exists():
  for rel,h in load(marker)['files'].items():assert sha(folder/rel)==h
  return
 bank=load(folder/'materials/item_bank.json');items={q['id']:q for q in bank};terms=load(folder/'materials/terms.json');people=load(NEW/PATHS['baseline']/'materials/personas.json');cases=[];sources={}
 for m in MODELS:
  src=NEW/PATHS['exposure50']/'runs/main'/m;s=load(src/'checkpoint.json');assert s['completed'] and s['seed']==SEED
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
    cases.append(dict(id=f'rep02_{m}_a{e["agent"]}_w{w}',model=m,agent=e['agent'],term_id=w,word=terms[w]['word'],cycle=e['cycle'],action=e['action'],original_generation_key=g['task_key'],original_request_hash=raw['request_hash'],use_prefix=prefix,initial_prefix=initial,prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),earlier_or_same_turn_exposure=prior,current_incoming_contains_term=incoming,exact_source_definition_in_prefix=terms[w]['meaning'] in prefix))
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
 plan=load(folder/'protocol.json');plan.update(source='All first non-source agent-expression uses in rep02 exposure50, never rep01 contexts.',cases=len(cases),case_counts=dict(Counter(c['model'] for c in cases)),tested_word_union=len({c['term_id'] for c in cases}),untested_words=60-len({c['term_id'] for c in cases}),main_responses=len(jobs),sources=sources,item_bank='All180 questions frozen before rep02 simulation inference; original135 unchanged;45 additional source-based items. Case/job freeze occurs before any new semantic answers.',semantic_seed_policy='Case IDs prefixed rep02; both context states share options/order/sampling seed. No feedback.',github='No automatic publication authorized by this replication request.')
 put(folder/'protocol.json',plan)
 names=['models.json','protocol.json','run.py','materials/item_bank.json','materials/terms.json','materials/cases.json','materials/jobs.json']
 put(marker,dict(time=now(),registration='Prospective case/job freeze before semantic inference, not public preregistration.',files={n:sha(folder/n) for n in names}))
def run_semantics():
 folder=NEW/PATHS['semantics'];prepare_semantics()
 # The inherited model inference function is byte-identical. Dynamic case counts
 # and the possibility of no first-use cases are handled by this outer wrapper.
 code="""import run,json
jobs=run.load(run.R/'materials/jobs.json')
for stage in ['pilot','main']:
 for m in ['llama','qwen','gemma','mistral']:
  ss=[j for j in jobs if j['model']==m]
  if stage=='pilot' and ss:ss=[j for j in ss if j['case_id']==ss[0]['case_id']]
  run.put(run.R/'status.json',dict(status=stage+'_running',model=m,time=run.now(),target_responses=len(ss)))
  if ss:run.run_model(m,ss,stage)
 if stage=='pilot':run.put(run.R/'pilot_gate.json',dict(time=run.now(),passed=True,criterion='Format/context/execution only; pilot responses excluded. No accuracy gate.'))
run.put(run.R/'status.json',dict(status='calculation_complete_analysis_pending',time=run.now()))
"""
 status('semantic_probes_running',cases=load(folder/'protocol.json')['cases'],target_responses=load(folder/'protocol.json')['main_responses'])
 command(['-c',code],folder)

def main():
 lock=(R/'execution.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 check_stop();verify_freeze();verify_originals()
 put(R/'controller.json',dict(pid=os.getpid(),started=now(),python=sys.executable,replication_root=str(NEW),seed=SEED))
 for condition in ['baseline','exposure50','memory4000']:run_network(condition,100)
 status('preparing_baseline_continuation');prepare_continuation()
 command(['-m','unittest','discover','-p','test_*.py'],NEW/PATHS['time200'])
 run_network('time200',200)
 status('auditing_network_conditions')
 for condition in ['baseline','exposure50','memory4000','time200']:command(['analyze.py'],NEW/PATHS[condition])
 run_semantics();status('independent_audit_and_two_run_analysis');command([R/'analyze_replications.py'],R)
 verify_originals();status('computation_and_automated_audit_complete_final_review_pending',independent_runs_per_model_condition=2,no_confirmatory_pvalues=True)
if __name__=='__main__':
 try:main()
 except BlockingIOError:print('Another replication controller holds the lock; no duplicate launched.',flush=True);raise
 except Exception as exc:status('stopped_incomplete',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc());raise
