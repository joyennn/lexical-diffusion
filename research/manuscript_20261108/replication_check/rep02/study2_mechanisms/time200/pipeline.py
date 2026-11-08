"""Continue immutable baseline trajectories, without any exposure/memory manipulation."""
import fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
from run_study1 import ROOT,read,put,stamp

def status(s,**k):put(ROOT/'status.json',dict(status=s,time=stamp(),**k));print(json.dumps(dict(status=s,time=stamp(),**k)),flush=True)
def freeze():
 names=['protocol.json','models.json','run_study1.py','analyze.py','pipeline.py','test_continuation.py','materials/terms.json','materials/personas.json','lineage.json']
 files={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
 if (ROOT/'freeze.json').exists():
  expected=read(ROOT/'freeze.json')['files']
  for p in sorted((ROOT/'amendments').glob('*.json')):
   for n,c in read(p).get('file_changes',{}).items():assert expected[n]==c['before'];expected[n]=c['after']
  assert expected==files
 else:put(ROOT/'freeze.json',dict(time=stamp(),registration='Internal prospective continuation freeze, not public preregistration.',files=files))
 lineage=read(ROOT/'lineage.json');assert files['run_study1.py']==lineage['runner_sha256']
 for m,meta in lineage['models'].items():
  assert hashlib.sha256(Path(meta['source_checkpoint']).read_bytes()).hexdigest()==meta['source_checkpoint_sha256']
  assert hashlib.sha256((ROOT/'origin'/m/'checkpoint_100.json').read_bytes()).hexdigest()==meta['source_checkpoint_sha256']
def main():
 lock=(ROOT/'execution.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);freeze();p=read(ROOT/'protocol.json')
 subprocess.run([sys.executable,'-m','unittest','discover','-p','test_*.py'],cwd=ROOT,check=True)
 if not (ROOT/'execution_budget.json').exists():put(ROOT/'execution_budget.json',dict(start=stamp(),deadline=time.time()+p['budget_hours']*3600))
 deadline=read(ROOT/'execution_budget.json')['deadline']
 for m in p['models']:
  folder=ROOT/'runs/main'/m
  if (folder/'completed.json').exists():assert read(folder/'completed.json')['cycles']==200;continue
  if (ROOT/'STOP').exists():raise RuntimeError('Operator STOP file')
  state=read(folder/'checkpoint.json');assert state['target_cycles']==200 and state['next_cycle']>=101;assert time.time()<deadline
  status('continuation_running',model=m,original_completed_cycles=100,target_total_cycles=200)
  subprocess.run([sys.executable,str(ROOT/'run_study1.py'),'--model',m,'--stage','main','--cycles','200','--hours',str((deadline-time.time())/3600)],cwd=ROOT,check=True)
 status('auditing_temporal_windows');subprocess.run([sys.executable,str(ROOT/'analyze.py')],cwd=ROOT,check=True)
 status('calculation_and_analysis_complete_final_comparison_review_pending',manuscript_required=False)
if __name__=='__main__':
 try:main()
 except BlockingIOError:print('Another continuation controller already holds lock.',flush=True);raise
 except Exception as e:status('stopped_incomplete',error=str(e));raise
