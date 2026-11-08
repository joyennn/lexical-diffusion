"""Start or inspect the frozen controller without duplicating a live process."""
import os,subprocess,sys
from setup import R,load,put,now
def main():
 if (R/'STOP').exists():raise RuntimeError('STOP exists. Resume only after explicit user authorization and clearing operational STOP markers.')
 if (R/'controller.json').exists():
  old=load(R/'controller.json')
  try:
   os.kill(old['pid'],0);print('Recorded controller PID exists. Inspect it; no duplicate started.');return
  except ProcessLookupError:pass
 assert (R/'freeze.json').exists()
 with (R/'pipeline.log').open('a') as log:
  process=subprocess.Popen([sys.executable,str(R/'controller.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONUNBUFFERED='1'))
 put(R/'controller.json',dict(pid=process.pid,started=now(),python=sys.executable))
 keeper=subprocess.Popen(['/usr/bin/caffeinate','-i','-s','-w',str(process.pid)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 put(R/'sleep_prevention.json',dict(pid=keeper.pid,controller_pid=process.pid,time=now(),scope='Prevent idle/system sleep while controller runs; does not change permanent power settings.'))
 print('Replication controller started:',process.pid,'sleep-prevention PID:',keeper.pid)
if __name__=='__main__':main()
