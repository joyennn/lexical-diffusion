"""Study2-1 source-recommendation policy, adapted from fresh Study1.

Run: python run_exposure.py --model llama --stage main --cycles 100
Model files are supplied via MODEL_STORE; weights are never packaged with data.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,csv,copy,hashlib,json,os,random,time
ROOT=Path(__file__).resolve().parent
def stamp():return datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2));tmp.replace(p)
def read(p):return json.loads(p.read_text())
def terms_in(text,terms):
 import re,unicodedata
 text=unicodedata.normalize('NFKC',text).casefold().replace('’',"'").replace('‘',"'")
 return [x['id'] for x in terms if re.search(r'(?<!\w)'+r'\s+'.join(re.escape(y) for y in unicodedata.normalize('NFKC',x['word']).casefold().replace('’',"'").split())+r'(?!\w)',text)]
class Backend:
 def __init__(self,model,out,deadline):
  import mlx.core as mx
  from mlx_lm import load
  self.mx=mx;self.info=read(ROOT/'models.json')[model];self.model_name=model;self.out=out;self.deadline=deadline;self.cache={}
  out.mkdir(parents=True,exist_ok=True);self.log=out/'calls.jsonl'
  if self.log.exists():
   for line in self.log.read_text().splitlines():
    row=json.loads(line)
    if row['status']=='completed':
     assert row['key'] not in self.cache,'Duplicate task key';self.cache[row['key']]=row
  mx.set_default_device(mx.gpu);mx.set_memory_limit(7*1024**3);mx.set_cache_limit(256*1024**2)
  store=Path(os.environ.get('MODEL_STORE',ROOT/'models'));start=time.monotonic()
  self.net,self.tok=load(str(store/self.info['folder']));mx.eval(self.net.parameters());mx.synchronize()
  self.choice_ids=[]
  for digit in ['0','1']:
   ids=self.tok.encode(digit,add_special_tokens=False)
   exact=[i for i in ids if self.tok.decode([i]).strip()==digit]
   assert len(set(exact))==1,'Binary action labels unsupported'
   self.choice_ids.append(exact[0])
  put(out/'backend.json',dict(model=self.info,load_seconds=time.monotonic()-start,device=mx.device_info(),time=stamp()))
 def ask(self,key,content,max_tokens,choice=False):
  from mlx_lm import stream_generate
  from mlx_lm.sample_utils import make_sampler
  mx=self.mx;request=dict(content=content,max_tokens=max_tokens,choice=choice,temperature=.9,top_p=.9,model=self.info,role='user',thinking=False)
  rh=digest(request)
  if key in self.cache:
   row=self.cache[key];assert row['request_hash']==rh,'Cached request changed: '+key;return row
  if (ROOT/'STOP').exists():raise RuntimeError('Operator STOP file')
  if time.time()>self.deadline:raise RuntimeError('Recorded resource deadline reached')
  prompt=self.tok.apply_chat_template([{'role':'user','content':content}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
  n=len(self.tok.encode(prompt,add_special_tokens=False))
  if n>7680:raise RuntimeError('Prompt exceeds common 7680-token safety ceiling')
  seed=int(hashlib.sha256((self.model_name+'/'+key).encode()).hexdigest()[:8],16);mx.random.seed(seed)
  def restrict(tokens,logits):
   ids=mx.array(self.choice_ids);mask=mx.any(mx.arange(logits.shape[-1])[:,None]==ids[None,:],axis=1)
   return mx.where(mask,logits,-float('inf'))
  start=time.monotonic();parts=[];last=None
  try:
   for last in stream_generate(self.net,self.tok,prompt=prompt,max_tokens=max_tokens,sampler=make_sampler(temp=.9,top_p=.9),logits_processors=[restrict] if choice else None):parts.append(last.text)
   if last is None:raise RuntimeError('No generation record returned')
   text=''.join(parts)
   if not text.strip():raise RuntimeError('Empty generation; never replaced by memory')
   if choice and text.strip() not in ['0','1']:raise RuntimeError('Invalid constrained action')
   row=dict(key=key,request_hash=rh,request=request,seed=seed,status='completed',output=text,time=stamp(),seconds=time.monotonic()-start,prompt_tokens=n,generation_tokens=last.generation_tokens,finish_reason=last.finish_reason,peak_bytes=mx.get_peak_memory())
  except Exception as exc:
   with self.log.open('a') as f:f.write(json.dumps(dict(key=key,request_hash=rh,request=request,seed=seed,status='failed',error=str(exc),time=stamp()),ensure_ascii=False)+'\n')
   raise
  with self.log.open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
  self.cache[key]=row;return row
 def close(self):
  import gc
  del self.net;gc.collect();self.mx.clear_cache()
def export(out,state):
 for name,data in [('posts',state['posts']),('comments',state['comments']),('events',state['events']),('exposures',state['exposures'])]:
  if not data:continue
  fields=list(dict.fromkeys(k for row in data for k in row))
  with (out/(name+'.csv')).open('w',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()} for row in data)
def experiment(model,stage,cycles,deadline):
 terms=read(ROOT/'materials/terms.json');personas=read(ROOT/'materials/personas.json');plan=read(ROOT/'protocol.json')
 seed=plan['main_seed'] if stage=='main' else plan['pilot_seed'];source_agent=seed%10
 out=ROOT/'runs'/stage/model;out.mkdir(parents=True,exist_ok=True)
 statepath=out/'checkpoint.json';b=Backend(model,out,deadline)
 try:
  if statepath.exists():state=read(statepath);assert state['seed']==seed and state['target_cycles']==cycles
  else:
   posts=[]
   for term in terms:
    text=term['word']+'\n'+(term['example']+'\n' if isinstance(term['example'],str) and term['example'].strip() else '')+term['meaning']+('\n'+term['origin_usage'] if isinstance(term.get('origin_usage'),str) else '')
    posts.append(dict(id=len(posts),agent=source_agent,cycle=0,text=text,initial_material=True,term_id=term['id']))
   state=dict(seed=seed,target_cycles=cycles,source_agent=source_agent,next_cycle=1,next_agent=0,posts=posts,comments=[],events=[],exposures=[],agents=[dict(id=i,persona=personas[i],memory='',read_ids=[],stats=dict(write=0,read=0,comment=0)) for i in range(10)],completed=False)
   put(statepath,state)
  source='\n'.join(x['word']+': '+x['meaning'] for x in terms)
  def context(agent,task):
   private='\nPrivate initial source knowledge (available only to you):\n'+source if agent['id']==source_agent else ''
   return 'You are one social-network user. Follow the task and remain consistent with your persona.\nPersona:\n'+agent['persona']+private+'\nYour current memory:\n'+agent['memory']+'\nYour activity counts: '+json.dumps(agent['stats'])+'\nTask:\n'+task
  for cycle in range(state['next_cycle'],cycles+1):
   for ai in range(state['next_agent'] if cycle==state['next_cycle'] else 0,10):
    agent=state['agents'][ai];key=f'{stage}/s{seed}/c{cycle}/a{ai}'
    before=agent['memory'];summary_key=None
    if len(before)>1000:
     summary_key=key+'/summary';row=b.ask(summary_key,context(agent,'Summarize the important information in your current memory in at most 500 characters. Return only the summary.'),100);agent['memory']=row['output'][:500]
    action_order=['read','write'];reaction_order=None
    if int(hashlib.sha256((str(seed)+key+'/action_labels').encode()).hexdigest()[:8],16)%2:action_order.reverse()
    task='Choose one action considering your persona, memory and activity counts. Return 0 for '+action_order[0]+' or 1 for '+action_order[1]+'. Return only the digit.'
    decision=b.ask(key+'/action',context(agent,task),1,choice=True)['output'].strip()
    action=action_order[int(decision)];incoming=[];parent=None;generated=None
    eligible=[x for x in state['posts'] if x['id'] not in agent['read_ids'] and x['agent']!=ai]
    feed_branch=None;feed_draw=None
    if action=='read':
     from feed_policy import select_pool
     eligible,feed_branch,feed_draw=select_pool(state['posts'],agent['read_ids'],ai,source_agent,seed,cycle,plan['recommendation_probability'])
    if action=='read' and eligible:
     rng=random.Random(int(hashlib.sha256((str(seed)+f'/c{cycle}/a{ai}/feed').encode()).hexdigest()[:8],16));parent=rng.choice(eligible)
     incoming=[dict(kind='post',id=parent['id'],agent=parent['agent'],text=parent['text'],initial_material=parent['initial_material'])]
     incoming += [dict(kind='comment',id=x['id'],agent=x['agent'],text=x['text'],initial_material=False) for x in state['comments'] if x['post_id']==parent['id']][-3:]
     visible='\n'.join(x['kind']+': '+x['text'] for x in incoming)
     reaction_order=['read','comment']
     if int(hashlib.sha256((str(seed)+key+'/reaction_labels').encode()).hexdigest()[:8],16)%2:reaction_order.reverse()
     task='Incoming post and up to three latest comments:\n'+visible+'\nReturn 0 for '+reaction_order[0]+' or 1 for '+reaction_order[1]+'. Here read means reading without commenting. Return only the digit.'
     reaction=b.ask(key+'/reaction',context(agent,task),1,choice=True)['output'].strip()
     for component in incoming:
      if component['agent']!=ai:
       state['exposures'].append(dict(cycle=cycle,turn=ai,agent=ai,source_agent=component['agent'],source_kind=component['kind'],source_id=component['id'],initial_material=component['initial_material'],term_ids=terms_in(component['text'],terms),text=component['text']))
     agent['memory']+='\nReceived: '+visible;agent['read_ids'].append(parent['id']);agent['stats']['read']+=1
     if reaction_order[int(reaction)]=='comment':action='comment'
    elif action=='read':action='read_no_available_post'
    if action in ['write','comment']:
     cap,tokens=(100,40) if action=='write' else (50,20)
     task=('Write one new public post' if action=='write' else 'Write one comment responding to the incoming post and comments in your memory')+f' in at most {cap} characters. Use information available to you; no particular word is required. Return only the text.'
     row=b.ask(key+'/generation',context(agent,task),tokens);used=row['output'][:cap]
     generated=dict(cycle=cycle,agent=ai,text=used,raw_text=row['output'],term_ids=terms_in(used,terms),length_compliant=len(row['output'])<=cap,finish_reason=row['finish_reason'],task_key=key+'/generation')
     if action=='write':state['posts'].append(dict(id=len(state['posts']),initial_material=False,**generated));agent['stats']['write']+=1;agent['read_ids'].append(state['posts'][-1]['id'])
     else:state['comments'].append(dict(id=len(state['comments']),post_id=parent['id'],**generated));agent['stats']['comment']+=1
     agent['memory']+='\nWrote: '+used
    state['events'].append(dict(cycle=cycle,turn=ai,agent=ai,action=action,action_label_order=action_order,reaction_label_order=reaction_order,parent_id=parent['id'] if parent else None,feed_branch=feed_branch,feed_draw=feed_draw,memory_before=before,memory_after=agent['memory'],summary_task=summary_key,generated=generated,incoming=incoming))
    state['next_cycle']=cycle;state['next_agent']=ai+1
    if ai==9:state['next_cycle']=cycle+1;state['next_agent']=0
    put(statepath,state)
    if ai==9:
     put(out/'snapshots'/f'cycle_{cycle:03}.json',state);export(out,state)
     put(ROOT/'progress.json',dict(stage=stage,model=model,completed_cycles=cycle,target_cycles=cycles,last_saved=stamp(),calls=len(b.cache)))
     print(json.dumps(dict(model=model,stage=stage,cycle=cycle,calls=len(b.cache),time=stamp())),flush=True)
  state['completed']=True;put(statepath,state);export(out,state)
  put(out/'completed.json',dict(completed=True,cycles=cycles,seed=seed,model=model,stage=stage,time=stamp()))
 finally:b.close()
def main():
 a=argparse.ArgumentParser();a.add_argument('--model',required=True);a.add_argument('--stage',choices=['pilot','main'],required=True);a.add_argument('--cycles',type=int,required=True);a.add_argument('--hours',type=float,default=96);args=a.parse_args()
 experiment(args.model,args.stage,args.cycles,time.time()+3600*args.hours)
if __name__=='__main__':main()
