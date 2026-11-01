"""Detached local memory4000 controller; no other experiment is launched."""
import fcntl,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent
lock=(ROOT/'execution.lock').open('a')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('Controller already running; duplicate not started.')
if (ROOT/'STOP').exists():raise SystemExit('STOP exists; explicit resume authorization needed.')
fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
env=dict(os.environ);env.setdefault('MODEL_STORE',str(ROOT.parents[1]/'local_gpu_check/models'))
with (ROOT/'pipeline.log').open('ab',buffering=0) as log:
 command=['/usr/bin/caffeinate','-i','-s',sys.executable,'-u',str(ROOT/'pipeline.py')]
 child=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
record=dict(time=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),pid=child.pid,command=command,model_store=env['MODEL_STORE'])
(ROOT/'controller.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
