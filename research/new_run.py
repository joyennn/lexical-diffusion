"""Plan or explicitly run fresh inference in an isolated destination. Never overwrite retained runs."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
R=Path(__file__).resolve().parent
S={'baseline':'fresh_study1','exposure50':'study2_mechanisms/exposure50','memory4000':'study2_mechanisms/memory4000','time200':'study2_mechanisms/time200','semantics':'study3_semantics'}
MODELS=['llama','qwen','gemma','mistral']
def load(p):return json.loads(p.read_text())
def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--condition',choices=S,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--model-store',type=Path);p.add_argument('--seed',type=int);p.add_argument('--baseline-dir',type=Path);p.add_argument('--hours',type=float,default=96);p.add_argument('--execute',action='store_true');a=p.parse_args()
    dest=a.destination.resolve();assert a.hours>0
    assert dest!=R and R not in dest.parents,'Fresh inference must be outside the release tree.'
    if dest.exists() and any(dest.iterdir()):raise ValueError('Destination must be absent or empty. Use the copied low-level runner to resume an interrupted new run.')
    src=R/'source'/S[a.condition];plan=load(src/'protocol.json')
    seed=a.seed if a.seed is not None else plan.get('main_seed',2026103000)
    if a.condition=='semantics' and a.seed is not None:raise ValueError('Semantic jobs contain paired task-specific seeds; a global seed override is unsupported.')
    if a.condition=='time200':
        if not a.baseline_dir:raise ValueError('time200 requires --baseline-dir containing completed 100-cycle checkpoints/calls.')
        baseline=a.baseline_dir.resolve();seeds=set()
        for m in MODELS:
            s=load(baseline/'runs/main'/m/'checkpoint.json');assert s['completed'] and s['target_cycles']==100;seeds.add(s['seed'])
        assert len(seeds)==1;seed=seeds.pop()
        if a.seed is not None:assert seed==a.seed,'Continuation must preserve baseline seed.'
    description=dict(condition=a.condition,destination=str(dest),seed=seed,models=MODELS,cycles=200 if a.condition=='time200' else 100 if a.condition!='semantics' else None,budget_hours_total=a.hours,inference_requested=a.execute,retained_observations_reused_as_new=False)
    print(json.dumps(description,indent=2),flush=True)
    if not a.execute:return
    if not a.model_store:raise ValueError('--execute requires --model-store pointing to downloaded pinned models.')
    store=a.model_store.resolve();models=load(src/'models.json')
    for m in models.values():assert (store/m['folder']/'config.json').exists(),m['folder']
    dest.mkdir(parents=True,exist_ok=True);target=dest/S[a.condition];target.mkdir(parents=True)
    for f in src.glob('*.py'):shutil.copy2(f,target/f.name)
    for name in ['models.json','protocol.json']:shutil.copy2(src/name,target/name)
    shutil.copytree(src/'materials',target/'materials')
    if a.condition!='semantics':
        plan['main_seed']=seed;put(target/'protocol.json',plan)
    else:
        # Frozen jobs are replayed with fresh answers; no old response cache is copied.
        shutil.copy2(src/'freeze.json',target/'freeze.json')
        (dest/'local_gpu_check').mkdir();(dest/'local_gpu_check/models').symlink_to(store,target_is_directory=True)
    if a.condition=='time200':
        shutil.copy2(baseline/'protocol.json',target/'protocol.json')
        continued_plan=load(target/'protocol.json');continued_plan['cycles']=200;put(target/'protocol.json',continued_plan)
        lineage=dict(baseline_root=str(baseline),runner_sha256=hashlib.sha256((target/'run_study1.py').read_bytes()).hexdigest(),models={})
        for m in MODELS:
            original=baseline/'runs/main'/m;origin=target/'origin'/m;origin.mkdir(parents=True)
            shutil.copy2(original/'checkpoint.json',origin/'checkpoint_100.json');shutil.copy2(original/'calls.jsonl',origin/'calls_1_100.jsonl')
            run=target/'runs/main'/m;run.mkdir(parents=True);shutil.copy2(original/'calls.jsonl',run/'calls.jsonl')
            state=load(original/'checkpoint.json');state.update(target_cycles=200,completed=False);put(run/'checkpoint.json',state)
            callbytes=(original/'calls.jsonl').read_bytes()
            lineage['models'][m]=dict(source_checkpoint=str(original/'checkpoint.json'),source_checkpoint_sha256=hashlib.sha256((original/'checkpoint.json').read_bytes()).hexdigest(),source_calls_sha256=hashlib.sha256(callbytes).hexdigest(),source_calls_bytes=len(callbytes),source_completed_calls=len(callbytes.splitlines()),original_event_count=1000,continuation_start_cycle=101)
        put(target/'lineage.json',lineage)
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob('*.py')}
    put(dest/'NEW_RUN_PROVENANCE.json',dict(**description,source_script_sha256=hashes,source_release='research/source',no_stored_responses_copied=a.condition!='time200',continuation_history_is_not_new_inference=a.condition=='time200'))
    env=dict(os.environ,MODEL_STORE=str(store));deadline=time.time()+a.hours*3600
    if a.condition=='semantics':
        subprocess.run([sys.executable,'run.py'],cwd=target,env=env,check=True,timeout=a.hours*3600);return
    runner='run_exposure.py' if a.condition=='exposure50' else 'run_study1.py'
    stages=[('main',200)] if a.condition=='time200' else [('pilot',plan['pilot_cycles']),('main',100)]
    for stage,cycles in stages:
        for m in MODELS:
            remaining=(deadline-time.time())/3600
            if remaining<=0:raise TimeoutError('New inference budget elapsed; completed checkpoints preserved.')
            subprocess.run([sys.executable,runner,'--model',m,'--stage',stage,'--cycles',str(cycles),'--hours',str(remaining)],cwd=target,env=env,check=True)
    print('Fresh inference complete. Analyze these new observations separately; they are not the retained release data.')
if __name__=='__main__':main()
