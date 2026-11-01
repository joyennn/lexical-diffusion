"""Secondary independent reconstruction from public post/comment tables and exposure records.
No simulation, no primary-rule changes, no original baseline edits.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import json,csv,hashlib,re,unicodedata
ROOT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t):return unicodedata.normalize('NFKC',t).casefold().replace('’',"'").replace('‘',"'")
def savecsv(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 terms=read(ROOT/'materials/terms.json');pats={t['id']:re.compile(r'(?<!\w)'+r'\s+'.join(re.escape(w) for w in norm(t['word']).split())+r'(?!\w)') for t in terms}
 lineage=read(ROOT/'lineage.json');assert sha(ROOT/'run_study1.py')==lineage['runner_sha256']
 auto={(r['model'],r['group'],int(r['start_cycle']),int(r['end_cycle'])):r for r in csv.DictReader((ROOT/'analysis/window_metrics.csv').open())}
 rows=[];wordrows=[];checks=[];newuses=[]
 intervals=[(1,100),(101,200),(1,200)]+[(i,i+19) for i in range(1,201,20)]
 for model,meta in lineage['models'].items():
  folder=ROOT/'runs/main'/model;origin=ROOT/'origin'/model;s=read(folder/'checkpoint.json');old=read(origin/'checkpoint_100.json')
  assert s['completed'] and s['target_cycles']==200 and s['next_cycle']==201
  assert sha(Path(meta['source_checkpoint']))==meta['source_checkpoint_sha256']==sha(origin/'checkpoint_100.json')
  assert sha(origin/'calls_1_100.jsonl')==meta['source_calls_sha256']
  raw=(folder/'calls.jsonl').read_bytes();prefix=(origin/'calls_1_100.jsonl').read_bytes();assert raw[:len(prefix)]==prefix
  for name in ['posts','comments','exposures','events']:assert s[name][:len(old[name])]==old[name]
  firstnew={e['agent']:e for e in s['events'] if e['cycle']==101}
  assert len(firstnew)==10 and all(firstnew[a]['memory_before']==old['agents'][a]['memory'] for a in range(10))
  assert all('feed_branch' not in e for e in s['events'])
  calls=[json.loads(x) for x in raw.splitlines()];lookup={x['key']:x for x in calls};assert len(lookup)==len(calls) and all(x['status']=='completed' for x in calls)
  extra=calls[meta['source_completed_calls']:];assert all(101<=int(re.search('/c(\\d+)/',x['key'])[1])<=200 for x in extra)
  for x in extra:assert x['request_hash']==hashlib.sha256(json.dumps(x['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
  public=sorted([dict(x,channel='post') for x in s['posts'] if not x['initial_material']]+[dict(x,channel='comment') for x in s['comments']],key=lambda x:(x['cycle'],x['agent']))
  uses={};exposures={};messages=[];received={}
  for x in public:
   response=lookup[x['task_key']]['output'];assert x['raw_text']==response and x['text']==response[:(100 if x['channel']=='post' else 50)]
   counts={w:len(p.findall(norm(x['text']))) for w,p in pats.items()};assert x['term_ids']==[w for w,n in counts.items() if n]
   messages.append(dict(x,counts=counts))
   for w,n in counts.items():
    if n:uses.setdefault((x['agent'],w),(x['cycle'],x['agent']))
  for e in s['exposures']:
   assert e['source_agent']!=e['agent'];when=e['cycle'],e['agent'];key=f"main/s{s['seed']}/c{e['cycle']}/a{e['agent']}/reaction"
   assert e['text'] in lookup[key]['request']['content']
   ids=[w for w,p in pats.items() if p.search(norm(e['text']))];assert ids==e['term_ids']
   received.setdefault(when,dict(words=set(),initial=False));received[when]['words'].update(ids);received[when]['initial']|=e['source_kind']=='post' and e['initial_material']
   for w in ids:exposures.setdefault((e['agent'],w),when)
  for (a,w),use in uses.items():
   if a and use[0]>100:newuses.append(dict(model=model,agent=a,word=terms[w]['word'],first_use_cycle=use[0],first_exposure_cycle=exposures[a,w][0] if (a,w) in exposures else None,qualifying=(a,w) in exposures and exposures[a,w]<=use))
  for group,agents in [('all',list(range(10))),('source',[0]),('nonseed',list(range(1,10)))]:
   for start,end in intervals:
    ms=[x for x in messages if x['agent'] in agents and start<=x['cycle']<=end];chars=sum(len(x['text']) for x in ms);wc={w:sum(x['counts'][w] for x in ms) for w in range(60)};total=sum(wc.values())
    first=[k for k,u in uses.items() if k[0] in agents and start<=u[0]<=end];qualified=[k for k in first if k in exposures and exposures[k]<=uses[k]]
    observed=[v for (c,a),v in received.items() if a in agents and start<=c<=end];dose=Counter((a,w) for (c,a),v in received.items() if a in agents and start<=c<=end for w in v['words']);top=max(wc,key=wc.get) if total else None
    row=dict(model=model,group=group,start_cycle=start,end_cycle=end,messages=len(ms),occurrences=total,occurrences_per100messages=total/len(ms)*100 if ms else None,occurrences_per1000characters=total/chars*1000 if chars else None,term_bearing_message_percent=100*sum(any(x['counts'].values()) for x in ms)/len(ms) if ms else None,distinct_used_words=sum(n>0 for n in wc.values()),distinct_user_word_pairs_in_window=len({(x['agent'],w) for x in ms for w,n in x['counts'].items() if n}),new_first_user_word_pairs=len(first),new_exposure_linked_first_users=len(qualified),repeat_occurrences=total-len(first),new_exposure_pairs=sum(a in agents and start<=t[0]<=end for (a,w),t in exposures.items()),top_word_id=top,top_word_share=wc[top]/total if total else None,top_word=terms[top]['word'] if total else None,read_turns=len(observed),initial_source_read_share=sum(v['initial'] for v in observed)/len(observed) if observed else None,zero_exposure_pairs_in_window=len(agents)*60-len(dose),exposure_turn_word_pairs=sum(dose.values()))
    ref=auto[model,group,start,end]
    for k,v in row.items():
     if k in ref and k not in ['model','group']:
      assert (v is None and ref[k]=='') or(v is not None and abs(float(ref[k])-v)<1e-10),(model,group,start,k)
    rows.append(row)
    if (start,end) in [(1,100),(101,200),(1,200)]:
     wordrows.extend(dict(model=model,group=group,start_cycle=start,end_cycle=end,term_id=w,word=terms[w]['word'],occurrences=wc[w],users=sum(any(x['agent']==a and x['counts'][w]>0 for x in ms) for a in agents)) for w in range(60))
  checks.append(dict(model=model,baseline_checkpoint_unchanged=True,original100_state_prefix_and_log_prefix_preserved=True,first_new_memory_matches_cycle100=True,new_calls=len(extra),latest_new_response=extra[-1]['time'],checkpoint_sha256=sha(folder/'checkpoint.json'),calls_sha256=sha(folder/'calls.jsonl')))
 out=ROOT/'analysis/final_review';out.mkdir(exist_ok=True)
 savecsv(out/'verified_window_metrics.csv',rows);savecsv(out/'word_frequency_by_phase.csv',wordrows);savecsv(out/'new_user_word_events_after100.csv',newuses)
 report=dict(time=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),all_four_continuations_verified=True,independent_public_message_and_exposure_reconstruction_matches_primary=True,original_baseline_preserved=True,one_extended_trajectory_per_model=True,not_independent100cycle_repetitions=True,no_manuscript_written=True,code_sha256=sha(Path(__file__)),checks=checks)
 (out/'independent_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps([x for x in rows if x['group']=='nonseed' and (x['start_cycle'],x['end_cycle']) in [(1,100),(101,200),(1,200)]],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
