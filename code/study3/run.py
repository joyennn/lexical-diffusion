"""Resume-safe forced four-choice probes of frozen saved contexts. No simulation writes."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,os,time,sys,fcntl
R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text())
def now():return datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2));t.replace(p)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def run_model(model,jobs,stage):
 import mlx.core as mx
 from mlx_lm import load as loadmodel,stream_generate
 from mlx_lm.sample_utils import make_sampler
 info=load(R/'models.json')[model];out=R/'runs'/stage/model;out.mkdir(parents=True,exist_ok=True);log=out/'calls.jsonl';cache={}
 if log.exists():
  for line in log.read_text().splitlines():
   row=json.loads(line)
   if row['status']=='completed':assert row['key'] not in cache;cache[row['key']]=row
 mx.set_default_device(mx.gpu);mx.set_memory_limit(7*1024**3);mx.set_cache_limit(256*1024**2)
 net,tok=loadmodel(str(Path(os.environ.get('MODEL_STORE', R.parent/'models'))/info['folder']));mx.eval(net.parameters());mx.synchronize();digits=[]
 for n in range(4):
  exact=[i for i in tok.encode(str(n),add_special_tokens=False) if tok.decode([i]).strip()==str(n)];assert len(set(exact))==1;digits.append(exact[0])
 def restrict(tokens,logits):
  return mx.where(mx.any(mx.arange(logits.shape[-1])[:,None]==mx.array(digits)[None,:],axis=1),logits,-float('inf'))
 for i,j in enumerate(jobs):
  if (R/'STOP').exists():raise RuntimeError('Operator STOP')
  request=dict(content=j['content'],model=info,max_tokens=1,temperature=.9,top_p=.9,allowed_digits=[0,1,2,3],thinking=False,seed=j['sampling_seed']);rh=digest(request);key=stage+'/'+j['key']
  if key in cache:assert cache[key]['request_hash']==rh;continue
  prompt=tok.apply_chat_template([{'role':'user','content':j['content']}],tokenize=False,add_generation_prompt=True,enable_thinking=False);n=len(tok.encode(prompt,add_special_tokens=False));assert n<=7680
  mx.random.seed(j['sampling_seed']);start=time.monotonic();parts=[];last=None
  try:
   for last in stream_generate(net,tok,prompt=prompt,max_tokens=1,sampler=make_sampler(temp=.9,top_p=.9),logits_processors=[restrict]):parts.append(last.text)
   output=''.join(parts).strip();assert output in ['0','1','2','3'],repr(output)
   row=dict(key=key,job_key=j['key'],request_hash=rh,request=request,output=output,status='completed',time=now(),seconds=time.monotonic()-start,prompt_tokens=n,generation_tokens=last.generation_tokens,correct=int(output)==j['correct'])
  except Exception as exc:
   with log.open('a') as f:f.write(json.dumps(dict(key=key,status='failed',error=str(exc),time=now()))+'\n');f.flush();os.fsync(f.fileno())
   raise
  with log.open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
  cache[key]=row;put(R/'progress.json',dict(stage=stage,model=model,completed_responses=len(cache),target_responses=len(jobs),last_response=now()))
  if (i+1)%12==0 or i==len(jobs)-1:print(json.dumps(dict(stage=stage,model=model,completed=len(cache),target=len(jobs),time=now())),flush=True)
 del net
 import gc
 gc.collect();mx.clear_cache()
def main():
 lock=(R/'execution.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for n,h in load(R/'freeze.json')['files'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
 jobs=load(R/'materials/jobs.json');pilotcases={m:next(x['case_id'] for x in jobs if x['model']==m) for m in load(R/'models.json')}
 for stage in ['pilot','main']:
  for m in ['llama','qwen','gemma','mistral']:
   subset=[x for x in jobs if x['model']==m and (stage=='main' or x['case_id']==pilotcases[m])]
   put(R/'status.json',dict(status=stage+'_running',model=m,time=now()));run_model(m,subset,stage)
  if stage=='pilot':put(R/'pilot_gate.json',dict(time=now(),passed=True,responses=24,criterion='format, context length and execution only; no accuracy criterion'))
 put(R/'status.json',dict(status='calculation_complete_analysis_pending',time=now()))
if __name__=='__main__':
 try:main()
 except Exception as exc:put(R/'status.json',dict(status='error',error=str(exc),time=now()));raise
