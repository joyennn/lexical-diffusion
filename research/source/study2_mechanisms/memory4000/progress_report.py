"""Read-only live state. Actual calls/checkpoints, not PID alone, indicate progress."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,subprocess
ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'protocol.json').read_text())
def read(f):return json.loads(f.read_text()) if f.exists() else None
out=dict(checked_at=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),status=read(ROOT/'status.json'),progress=read(ROOT/'progress.json'),models={})
for model in p['models']:
 out['models'][model]={}
 for stage in ['pilot','main']:
  folder=ROOT/'runs'/stage/model;s=read(folder/'checkpoint.json');calls=[]
  if (folder/'calls.jsonl').exists():
   for line in (folder/'calls.jsonl').read_text().splitlines():
    try:calls.append(json.loads(line))
    except json.JSONDecodeError:pass # concurrent final append may still be in flight
  done=[x for x in calls if x['status']=='completed']
  out['models'][model][stage]=dict(completed_cycles=s['next_cycle']-1 if s else 0,target_cycles=p['pilot_cycles'] if stage=='pilot' else 100,completed=s['completed'] if s else False,actual_completed_calls=len(done),failed_calls=len(calls)-len(done),last_actual_call=done[-1]['time'] if done else None,last_checkpoint=datetime.fromtimestamp((folder/'checkpoint.json').stat().st_mtime,ZoneInfo('Asia/Seoul')).isoformat() if s else None)
ps=subprocess.check_output(['ps','-axo','pid,etime,pcpu,command'],text=True);out['processes']=[l.strip() for l in ps.splitlines() if str(ROOT) in l and any(s in l for s in ['/pipeline.py','/run_study1.py'])]
out['log_tail']=(ROOT/'pipeline.log').read_text(errors='replace').splitlines()[-6:] if (ROOT/'pipeline.log').exists() else []
print(json.dumps(out,ensure_ascii=False,indent=2))
