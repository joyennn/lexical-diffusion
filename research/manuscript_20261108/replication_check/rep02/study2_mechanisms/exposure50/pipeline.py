"""Frozen four-model exposure50 experiment; no automatic other mechanisms."""
import fcntl,hashlib,subprocess,sys,time,json
from run_exposure import ROOT,read,put,stamp
from analyze import audit

def status(s,**kwargs):put(ROOT/'status.json',dict(status=s,time=stamp(),**kwargs));print(json.dumps(dict(status=s,time=stamp(),**kwargs)),flush=True)
def freeze():
 names=['protocol.json','models.json','run_exposure.py','feed_policy.py','analyze.py','pipeline.py','test_execution.py','test_policy.py','materials/terms.json','materials/personas.json','provenance.json']
 hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
 if (ROOT/'freeze.json').exists():
  expected=read(ROOT/'freeze.json')['files']
  for f in sorted((ROOT/'amendments').glob('*.json')):
   for name,c in read(f).get('file_changes',{}).items():assert expected[name]==c['before'];expected[name]=c['after']
  assert expected==hashes,'Source changed: record prospective amendment'
 else:put(ROOT/'freeze.json',dict(time=stamp(),registration='Internal prospective freeze before inference; not public preregistration.',files=hashes))
def main():
 lock=(ROOT/'execution.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);freeze();p=read(ROOT/'protocol.json')
 subprocess.run([sys.executable,'-m','unittest','discover','-p','test_*.py'],cwd=ROOT,check=True)
 if not (ROOT/'execution_budget.json').exists():put(ROOT/'execution_budget.json',dict(start=stamp(),deadline=time.time()+p['budget_hours']*3600))
 deadline=read(ROOT/'execution_budget.json')['deadline']
 def launch(model,stage,cycles):
  if (ROOT/'runs'/stage/model/'completed.json').exists():assert read(ROOT/'runs'/stage/model/'completed.json')['cycles']==cycles;return
  if (ROOT/'STOP').exists():raise RuntimeError('Operator STOP file')
  assert time.time()<deadline;status(stage+'_running',model=model,target_cycles=cycles)
  subprocess.run([sys.executable,str(ROOT/'run_exposure.py'),'--model',model,'--stage',stage,'--cycles',str(cycles),'--hours',str((deadline-time.time())/3600)],cwd=ROOT,check=True)
 for m in p['models']:launch(m,'pilot',p['pilot_cycles'])
 checks=[audit(ROOT/'runs/pilot'/m,m,'pilot',p['pilot_cycles']) for m in p['models']]
 put(ROOT/'pilot_gate.json',dict(time=stamp(),passed=True,criterion='Technical execution only; no diffusion-direction gate.',checks=checks))
 for m in p['models']:launch(m,'main',100)
 status('auditing_and_analyzing');subprocess.run([sys.executable,str(ROOT/'analyze.py')],cwd=ROOT,check=True)
 status('calculation_and_analysis_complete_final_comparison_review_pending',manuscript_required=False)
if __name__=='__main__':
 try:main()
 except BlockingIOError:print('Another controller holds lock; no duplicate started.',flush=True);raise
 except Exception as e:status('stopped_incomplete',error=str(e));raise
