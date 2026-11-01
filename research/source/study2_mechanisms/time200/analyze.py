"""Audit unchanged continuation and compare rates over fixed temporal windows."""
from pathlib import Path
from collections import Counter
import csv,json,hashlib,random,re,unicodedata
from run_study1 import ROOT,read,put,stamp

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return unicodedata.normalize('NFKC',s).casefold().replace('’',"'").replace('‘',"'")
def windows():return [(1,100),(101,200),(1,200)]+[(c,c+19) for c in range(1,201,20)]
def window_metrics(messages,uses,exposures,agents,start,end):
 ms=[x for x in messages if x['agent'] in agents and start<=x['cycle']<=end]
 total=sum(sum(x['counts'].values()) for x in ms);characters=sum(len(x['text']) for x in ms)
 firsts=[k for k,t in uses.items() if k[0] in agents and start<=t[0]<=end]
 qualified=[k for k in firsts if k in exposures and exposures[k]<=uses[k]]
 counts=Counter({w:sum(x['counts'][w] for x in ms) for w in range(60)})
 return dict(start_cycle=start,end_cycle=end,messages=len(ms),occurrences=total,occurrences_per100messages=100*total/len(ms) if ms else None,occurrences_per1000characters=1000*total/characters if characters else None,term_bearing_message_percent=100*sum(any(x['counts'].values()) for x in ms)/len(ms) if ms else None,distinct_used_words=sum(n>0 for n in counts.values()),distinct_user_word_pairs_in_window=len({(x['agent'],w) for x in ms for w,n in x['counts'].items() if n}),new_first_user_word_pairs=len(firsts),new_exposure_linked_first_users=len(qualified),repeat_occurrences=total-len(firsts),new_exposure_pairs=sum(a in agents and start<=t[0]<=end for (a,w),t in exposures.items()),top_word_id=counts.most_common(1)[0][0] if total else None,top_word_share=counts.most_common(1)[0][1]/total if total else None)
def analyze_one(model):
 folder=ROOT/'runs/main'/model;origin=ROOT/'origin'/model;meta=read(ROOT/'lineage.json')['models'][model];base=read(origin/'checkpoint_100.json');s=read(folder/'checkpoint.json');terms=read(ROOT/'materials/terms.json')
 assert sha(Path(meta['source_checkpoint']))==meta['source_checkpoint_sha256'] and sha(origin/'checkpoint_100.json')==meta['source_checkpoint_sha256']
 assert sha(origin/'calls_1_100.jsonl')==meta['source_calls_sha256']
 callbytes=(folder/'calls.jsonl').read_bytes();prefix=(origin/'calls_1_100.jsonl').read_bytes();assert callbytes[:len(prefix)]==prefix
 assert s['completed'] and s['target_cycles']==200 and s['next_cycle']==201 and s['next_agent']==0
 for name in ['events','posts','comments','exposures']:assert s[name][:len(base[name])]==base[name]
 assert [(e['cycle'],e['agent']) for e in s['events']]==[(c,a) for c in range(1,201) for a in range(10)]
 calls=[json.loads(l) for l in callbytes.splitlines()];lookup={r['key']:r for r in calls};assert len(lookup)==len(calls) and all(r['status']=='completed' for r in calls)
 newcalls=calls[meta['source_completed_calls']:]
 assert all(101<=int(re.search(r'/c(\d+)/',r['key'])[1])<=200 for r in newcalls)
 assert len(list((folder/'snapshots').glob('cycle_*.json')))==100
 pats={t['id']:re.compile(r'(?<!\w)'+r'\s+'.join(re.escape(w) for w in norm(t['word']).split())+r'(?!\w)') for t in terms};seed=s['seed'];seen={a:[] for a in range(10)};messages=[];uses={};ex={};reconstructed=[]
 postkeys={x['task_key']:x['id'] for x in s['posts'] if not x['initial_material']}
 for e in s['events']:
  c,a=e['cycle'],e['agent'];pos=c,a
  assert 'feed_branch' not in e,'Recommendation policy must not be present'
  if e['action'] in ['read','comment','read_no_available_post']:
   current=[p for p in s['posts'] if p['initial_material'] or p['cycle']<c or (p['cycle']==c and p['agent']<a)]
   pool=[p for p in current if p['agent']!=a and p['id'] not in seen[a]]
   if pool:
    parent=random.Random(int(hashlib.sha256((str(seed)+f'/c{c}/a{a}/feed').encode()).hexdigest()[:8],16)).choice(pool)
    assert parent['id']==e['parent_id'];seen[a].append(parent['id'])
   else:assert e['parent_id'] is None
  for x in e['incoming']:
   assert x['text'] in lookup[f'main/s{seed}/c{c}/a{a}/reaction']['request']['content']
   if x['agent']==a:continue
   ids=[w for w,p in pats.items() if p.search(norm(x['text']))]
   for w in ids:ex.setdefault((a,w),pos)
   reconstructed.append(dict(cycle=c,turn=a,agent=a,source_agent=x['agent'],source_kind=x['kind'],source_id=x['id'],initial_material=x['initial_material'],term_ids=ids,text=x['text']))
  if e['generated']:
   g=e['generated'];raw=lookup[g['task_key']]['output'];cap=100 if e['action']=='write' else 50
   assert g['raw_text']==raw and g['text']==raw[:cap]
   counts={w:len(p.findall(norm(g['text']))) for w,p in pats.items()};assert g['term_ids']==[w for w,n in counts.items() if n]
   messages.append(dict(cycle=c,agent=a,text=g['text'],counts=counts))
   for w,n in counts.items():
    if n:uses.setdefault((a,w),pos)
   if e['action']=='write':seen[a].append(postkeys[g['task_key']])
 assert reconstructed==s['exposures']
 for r in newcalls:
  assert r['request_hash']==hashlib.sha256(json.dumps(r['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
  assert r['prompt_tokens']<=7680
 rows=[]
 for group,agents in [('all',list(range(10))),('source',[s['source_agent']]),('nonseed',[a for a in range(10) if a!=s['source_agent']])]:
  rows.extend(dict(model=model,group=group,**window_metrics(messages,uses,ex,agents,start,end)) for start,end in windows())
 curves=[]
 for c in range(201):
  linked=[k for k,u in uses.items() if k[0]!=s['source_agent'] and u[0]<=c and k in ex and ex[k]<=u]
  curves.append(dict(model=model,cycle=c,nonseed_linked_first_users=len(linked),nonseed_cumulative_occurrences=sum(sum(m['counts'].values()) for m in messages if m['agent']!=s['source_agent'] and m['cycle']<=c)))
 return rows,curves,dict(model=model,cycles=200,added_cycles=100,original100_state_and_call_prefix_preserved=True,baseline_rules_replayed=True,total_calls=len(calls),new_calls=len(newcalls),last_new_call=newcalls[-1]['time'],checkpoint_sha256=sha(folder/'checkpoint.json'),calls_sha256=sha(folder/'calls.jsonl'))
def writecsv(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 rows=[];curves=[];checks=[]
 for m in read(ROOT/'protocol.json')['models']:
  a,b,c=analyze_one(m);rows+=a;curves+=b;checks.append(c)
 out=ROOT/'analysis';out.mkdir(exist_ok=True);writecsv(out/'window_metrics.csv',rows);writecsv(out/'cumulative_curves.csv',curves)
 put(out/'completion_audit.json',dict(time=stamp(),all_four200cycle_trajectories_verified=True,checks=checks,independent_repetitions_added=0,meaning_of_comparison='Same trajectories:1-100 versus101-200; use normalized interval rates, not cumulative count increase alone.'))
 print('Continuation history, baseline rules and temporal metrics verified; no manuscript produced.')
if __name__=='__main__':main()
