"""Run fresh pilots, four new main trajectories, analysis and manuscript."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys,time
from run_study1 import ROOT,read,put,stamp
def status(value,**kwargs):
 put(ROOT/'status.json',dict(status=value,time=stamp(),**kwargs));print(value,kwargs,flush=True)
def main():
 lock=(ROOT/'execution.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 plan=read(ROOT/'protocol.json');source_names=['protocol.json','models.json','run_study1.py','analyze.py','write_results.py','materials/terms.json','materials/personas.json']
 hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_names}
 if (ROOT/'freeze.json').exists():
  expected=read(ROOT/'freeze.json')['files']
  for amendment in sorted((ROOT/'amendments').glob('*.json')):
   for name,change in read(amendment).get('file_changes',{}).items():
    assert expected[name]==change['before'],'Amendment chain mismatch';expected[name]=change['after']
  assert expected==hashes,'Frozen source changed; record an amendment before restart.'
 else:put(ROOT/'freeze.json',dict(time=stamp(),registration='Internal pre-pilot freeze, not public preregistration.',files=hashes,old_results_reused=False))
 budget=ROOT/'execution_budget.json'
 if not budget.exists():put(budget,dict(deadline=time.time()+plan['budget_hours']*3600,start_time=stamp()))
 deadline=read(budget)['deadline'];store=Path(os.environ.get('MODEL_STORE',ROOT/'models'))
 def launch(model,stage,cycles):
  done=ROOT/'runs'/stage/model/'completed.json'
  if done.exists():assert read(done)['cycles']==cycles;return
  folder=store/read(ROOT/'models.json')[model]['folder']
  while not (folder/'config.json').exists() or not list(folder.glob('*.safetensors')):
   if time.time()>deadline or (ROOT/'STOP').exists():raise RuntimeError('Waiting interrupted or resource deadline reached')
   status('waiting_for_model_download',model=model,stage=stage);time.sleep(30)
  # Download completion marker is necessary for newly obtained conversions.
  if model in ['gemma','mistral']:
   while not (ROOT/'models_ready.json').exists():
    if time.time()>deadline or (ROOT/'STOP').exists():raise RuntimeError('Download not ready within resource window')
    status('waiting_for_model_download',model=model,stage=stage);time.sleep(30)
  status(stage+'_running',model=model,target_cycles=cycles)
  remaining=(deadline-time.time())/3600;assert remaining>0
  subprocess.run([sys.executable,str(ROOT/'run_study1.py'),'--model',model,'--stage',stage,'--cycles',str(cycles),'--hours',str(remaining)],check=True,cwd=ROOT)
 for model in plan['models']:launch(model,'pilot',plan['pilot_cycles'])
 put(ROOT/'pilot_gate.json',dict(passed=True,time=stamp(),reason='All four separate3-cycle technical pilots completed without inference/template/empty-output failures. No uptake/effect-direction gate.'))
 for model in plan['models']:launch(model,'main',100)
 assert all(read(ROOT/'runs/main'/m/'completed.json')['cycles']==100 for m in plan['models'])
 status('analyzing_fresh_data')
 subprocess.run([sys.executable,str(ROOT/'analyze.py')],check=True,cwd=ROOT)
 status('building_clean_manuscript_and_packages')
 subprocess.run([sys.executable,str(ROOT/'write_results.py')],check=True,cwd=ROOT)
 status('data_and_report_built_visual_review_pending',main_cycles_per_model=100,independent_trajectories_per_model=1)
if __name__=='__main__':
 try:main()
 except Exception as exc:
  status('stopped_incomplete',error_type=type(exc).__name__,reason=str(exc));raise
