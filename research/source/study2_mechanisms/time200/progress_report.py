"""Report newly generated101-200 data separately from copied baseline history."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,re,subprocess
ROOT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text()) if p.exists() else None
out=dict(checked_at=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),status=read(ROOT/'status.json'),progress=read(ROOT/'progress.json'),models={})
for m in read(ROOT/'protocol.json')['models']:
 f=ROOT/'runs/main'/m;s=read(f/'checkpoint.json');new=[];failed=0
 for line in (f/'calls.jsonl').read_text().splitlines():
  try:r=json.loads(line)
  except json.JSONDecodeError:continue
  if int(re.search(r'/c(\d+)/',r['key'])[1])>100:
   if r['status']=='completed':new.append(r)
   else:failed+=1
 out['models'][m]=dict(total_completed_cycles=s['next_cycle']-1,additional_completed_cycles=max(0,s['next_cycle']-101),additional_target_cycles=100,total_target_cycles=200,completed=s['completed'],actual_new_calls=len(new),failed_new_calls=failed,last_actual_new_call=new[-1]['time'] if new else None,last_checkpoint=datetime.fromtimestamp((f/'checkpoint.json').stat().st_mtime,ZoneInfo('Asia/Seoul')).isoformat())
ps=subprocess.check_output(['ps','-axo','pid,etime,pcpu,command'],text=True);out['processes']=[x.strip() for x in ps.splitlines() if str(ROOT) in x and any(k in x for k in ['/pipeline.py','/run_study1.py'])]
out['log_tail']=(ROOT/'pipeline.log').read_text(errors='replace').splitlines()[-5:] if (ROOT/'pipeline.log').exists() else []
print(json.dumps(out,ensure_ascii=False,indent=2))
