"""Read-only progress: completed cycles and actual calls, never inference."""
from pathlib import Path
import json,os,time
from setup import R,W,NEW,MODELS,PATHS,load,now
def main():
 rows=[]
 for condition in ['baseline','exposure50','memory4000','time200']:
  for model in MODELS:
   folder=NEW/PATHS[condition]/'runs/main'/model;checkpoint=folder/'checkpoint.json';calls=folder/'calls.jsonl';s=load(checkpoint) if checkpoint.exists() else None
   cycle=(min(s['target_cycles'],s['next_cycle']-1) if s else 0);last=None;n=0
   if calls.exists():
    with calls.open() as f:
     for line in f:
      if not line.strip():continue
      x=json.loads(line)
      if x['status']=='completed' and (condition!='time200' or int(x['key'].split('/c')[1].split('/')[0])>=101):last=dict(key=x['key'],time=x['time']);n+=1
   rows.append(dict(condition=condition,model=model,total_completed_cycles=cycle,total_target_cycles=200 if condition=='time200' else 100,new_completed_cycles=max(0,cycle-100) if condition=='time200' else cycle,new_target_cycles=100,completed=bool(s and s['completed']),current_agent=s['next_agent'] if s else None,new_saved_calls=n,last_actual_new_call=last,calls_mtime=calls.stat().st_mtime if calls.exists() else None))
 sem=NEW/PATHS['semantics'];jobs=load(sem/'materials/jobs.json') if (sem/'materials/jobs.json').exists() else []
 semantic=[]
 for model in MODELS:
  f=sem/'runs/main'/model/'calls.jsonl';records=[json.loads(x) for x in f.open()] if f.exists() else [];done=[x for x in records if x['status']=='completed']
  semantic.append(dict(model=model,completed_responses=len(done),target_responses=sum(j['model']==model for j in jobs) if jobs else None,last_actual_response=done[-1]['time'] if done else None))
 controller=load(R/'controller.json') if (R/'controller.json').exists() else None;alive=False
 if controller:
  try:os.kill(controller['pid'],0);alive=True
  except ProcessLookupError:pass
 print(json.dumps(dict(time=now(),status=load(R/'status.json') if (R/'status.json').exists() else None,controller=controller,controller_pid_exists=alive,note='PID existence alone is not proof of inference progress. Compare actual calls/checkpoints across observations.',network=rows,semantics=semantic),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
