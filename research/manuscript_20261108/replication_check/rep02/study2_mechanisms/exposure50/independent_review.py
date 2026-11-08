"""Independent raw-record reconstruction for final all60 baseline/policy review.
Does not import the primary metric or feed-selection implementation. No inference.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import csv,hashlib,json,random,re,unicodedata
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parents[1]/'fresh_study1';MODELS=['llama','qwen','gemma','mistral']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return unicodedata.normalize('NFKC',s).casefold().replace('’',"'").replace('‘',"'")
def csvwrite(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def frozen(root):
 expected=dict(read(root/'freeze.json')['files'])
 for p in sorted((root/'amendments').glob('*.json')):
  for name,c in read(p).get('file_changes',{}).items():assert expected[name]==c['before'];expected[name]=c['after']
 assert all(sha(root/n)==v for n,v in expected.items())

def rebuild(study,model,terms,patterns):
 root=BASE if study=='baseline' else ROOT;folder=root/'runs/main'/model;state=read(folder/'checkpoint.json');source=state['source_agent'];seed=state['seed']
 assert state['completed'] and state['target_cycles']==100 and source==0 and seed==2026103000
 assert [(e['cycle'],e['agent']) for e in state['events']]==[(c,a) for c in range(1,101) for a in range(10)]
 calls=[json.loads(l) for l in (folder/'calls.jsonl').read_text().splitlines()];assert all(x['status']=='completed' and x['key'].startswith('main/') for x in calls)
 lookup={x['key']:x for x in calls};assert len(lookup)==len(calls)
 for x in calls:assert x['request_hash']==hashlib.sha256(json.dumps(x['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest() and x['prompt_tokens']<=7680
 uses={};exposures={};source_ex={};reads=Counter();initial=Counter();recommend=Counter();dose=Counter();outputs=[];reconstructed_ex=[];seen={a:[] for a in range(10)}
 post_for_key={x['task_key']:x for x in state['posts'] if not x['initial_material']}
 for e in state['events']:
  c,a=e['cycle'],e['agent'];pos=c,a
  if e['action'] in ['read','comment','read_no_available_post']:
   current=[p for p in state['posts'] if p['initial_material'] or p['cycle']<c or (p['cycle']==c and p['agent']<a)]
   ordinary=[p for p in current if p['id'] not in seen[a] and p['agent']!=a]
   if study=='exposure50' and a!=source:
    coin=random.Random(int(hashlib.sha256((str(seed)+f'/c{c}/a{a}/recommendation_branch').encode()).hexdigest()[:8],16)).random()
    selected=coin<.5;assert e['feed_draw']==coin and e['feed_branch']==('recommended_source' if selected else 'ordinary_unread')
    pool=[p for p in current if p['initial_material'] and p['agent']!=a] if selected else ordinary
    if selected:assert len(pool)==60
   else:pool=ordinary
   if pool:
    parent=random.Random(int(hashlib.sha256((str(seed)+f'/c{c}/a{a}/feed').encode()).hexdigest()[:8],16)).choice(pool)
    assert e['parent_id']==parent['id'];seen[a].append(parent['id'])
   else:assert not e['incoming'] and e['parent_id'] is None
  if e['incoming']:
   reads[a]+=1;initial[a]+=any(x['kind']=='post' and x['initial_material'] for x in e['incoming']);recommend[a]+=e.get('feed_branch')=='recommended_source'
   key=f'main/s{seed}/c{c}/a{a}/reaction'
   for x in e['incoming']:assert x['text'] in lookup[key]['request']['content']
   encountered=set()
   for x in e['incoming']:
    if x['agent']==a:continue
    ids=[w for w,p in patterns.items() if p.search(norm(x['text']))]
    reconstructed_ex.append(dict(cycle=c,turn=a,agent=a,source_agent=x['agent'],source_kind=x['kind'],source_id=x['id'],initial_material=x['initial_material'],term_ids=ids,text=x['text']))
    encountered.update(ids)
    for w in ids:
     exposures.setdefault((a,w),pos)
     if x['agent']==source:source_ex.setdefault((a,w),pos)
   for w in encountered:dose[a,w]+=1
  if e['generated']:
   g=e['generated'];raw=lookup[g['task_key']]['output'];cap=100 if e['action']=='write' else 50
   assert g['raw_text']==raw and g['text']==raw[:cap]
   counts={w:len(p.findall(norm(g['text']))) for w,p in patterns.items()};assert g['term_ids']==[w for w,n in counts.items() if n]
   outputs.append(dict(agent=a,cycle=c,counts=counts,text=g['text'],truncated=len(raw)>cap,channel='post' if e['action']=='write' else 'comment'))
   for w,n in counts.items():
    if n:uses.setdefault((a,w),pos)
   if e['action']=='write':seen[a].append(post_for_key[g['task_key']]['id'])
 assert reconstructed_ex==state['exposures']
 rows=[];details=[];curves=[];bins=[]
 for group,agents in [('all',list(range(10))),('source',[0]),('nonseed',list(range(1,10)))]:
  messages=[x for x in outputs if x['agent'] in agents];pairs=[k for k in uses if k[0] in agents];linked=[k for k in pairs if k in exposures and exposures[k]<=uses[k]]
  wc={w:sum(x['counts'][w] for x in messages) for w in range(60)};total=sum(wc.values());chars=sum(len(x['text']) for x in messages);reading=sum(reads[a] for a in agents);top=max(wc,key=wc.get);authorcounts=Counter({a:sum(sum(x['counts'].values()) for x in messages if x['agent']==a) for a in agents})
  row=dict(study=study,model=model,group=group,messages=len(messages),occurrences=total,occurrences_per100messages=total/len(messages)*100 if messages else None,occurrences_per1000characters=total/chars*1000 if chars else None,term_bearing_message_percent=100*sum(any(x['counts'].values()) for x in messages)/len(messages) if messages else None,distinct_used_words=sum(n>0 for n in wc.values()),unique_user_word_pairs=len(pairs),exposure_linked_first_users=len(linked),repeat_occurrences=total-len(pairs),read_turns=reading,recommended_read_turns=sum(recommend[a] for a in agents),initial_entry_read_turns=sum(initial[a] for a in agents),initial_entry_share=sum(initial[a] for a in agents)/reading if reading else None,zero_exposure_pairs=sum(dose[a,w]==0 for a in agents for w in range(60)),mean_external_exposure_turns=sum(dose[a,w] for a in agents for w in range(60))/(len(agents)*60),truncated_messages=sum(x['truncated'] for x in messages),top_word=terms[top]['word'],top_word_occurrences=wc[top],top_word_share=wc[top]/total if total else None,top_author_share=max(authorcounts.values())/total if total else None,strict_peer_only_first_uses=sum(k not in source_ex or source_ex[k]>uses[k] for k in linked))
  rows.append(row)
  for w in range(60):details.append(dict(study=study,model=model,group=group,term_id=w,word=terms[w]['word'],occurrences=wc[w],users=sum((a,w) in uses for a in agents),qualified_first_users=sum((a,w) in linked for a in agents)))
  for c in range(101):curves.append(dict(study=study,model=model,group=group,cycle=c,cumulative_occurrences=sum(sum(x['counts'].values()) for x in messages if x['cycle']<=c),cumulative_first_users=sum(uses[k][0]<=c for k in linked)))
  for start in range(1,101,20):
   ms=[x for x in messages if start<=x['cycle']<=start+19];newpairs=[k for k in linked if start<=uses[k][0]<=start+19]
   bins.append(dict(study=study,model=model,group=group,start_cycle=start,end_cycle=start+19,messages=len(ms),occurrences=sum(sum(x['counts'].values()) for x in ms),new_exposure_pairs=sum(a in agents and start<=t[0]<=start+19 for (a,w),t in exposures.items()),new_qualifying_first_users=len(newpairs)))
 return dict(rows=rows,details=details,curves=curves,bins=bins,audit=dict(study=study,model=model,completed_calls=len(calls),last_call=calls[-1]['time'],calls_sha256=sha(folder/'calls.jsonl'),checkpoint_sha256=sha(folder/'checkpoint.json'),raw_inputs_outputs_exposures_and_feed_verified=True))

def main():
 assert read(ROOT/'analysis/completion_audit.json')['all_four_new_runs_verified']
 frozen(ROOT);frozen(BASE)
 for name in ['models.json','materials/terms.json','materials/personas.json']:assert sha(ROOT/name)==sha(BASE/name)
 oldhash=read(ROOT.parent/'exposure_planning/baseline_exposure_summary.json')['source_checkpoint_hashes']
 for m in MODELS:assert sha(BASE/'runs/main'/m/'checkpoint.json')==oldhash[m]
 terms=read(ROOT/'materials/terms.json');patterns={t['id']:re.compile(r'(?<!\w)'+r'\s+'.join(re.escape(w) for w in norm(t['word']).split())+r'(?!\w)') for t in terms}
 results=[rebuild(study,m,terms,patterns) for study in ['baseline','exposure50'] for m in MODELS]
 automatic={(r['study'],r['model'],r['group']):r for r in csv.DictReader((ROOT/'analysis/summary.csv').open())}
 automatic_words={(r['study'],r['model'],r['group'],int(r['term_id'])):r for r in csv.DictReader((ROOT/'analysis/word_metrics.csv').open())}
 automatic_bins={(r['study'],r['model'],r['group'],int(r['start_cycle'])):r for r in csv.DictReader((ROOT/'analysis/twenty_cycle_bins.csv').open())}
 for result in results:
  for row in result['rows']:
   ref=automatic[row['study'],row['model'],row['group']]
   for k,v in row.items():
    if k in ref and k not in ['study','model','group']:
     assert (v is None and ref[k]=='') or (v is not None and abs(float(ref[k])-v)<1e-10),(row['study'],row['model'],k)
  for row in result['details']:
   ref=automatic_words[row['study'],row['model'],row['group'],row['term_id']]
   assert int(ref['occurrences'])==row['occurrences'] and int(ref['users'])==row['users']
  for row in result['bins']:
   ref=automatic_bins[row['study'],row['model'],row['group'],row['start_cycle']]
   for key in ['messages','occurrences','new_exposure_pairs','new_qualifying_first_users']:assert int(ref[key])==row[key]
 out=ROOT/'analysis/final_review';out.mkdir(exist_ok=True)
 for filename,key in [('verified_summary.csv','rows'),('verified_words.csv','details'),('verified_curves.csv','curves'),('verified_twenty_cycle_bins.csv','bins')]:csvwrite(out/filename,[row for r in results for row in r[key]])
 report=dict(time=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),all_eight_datasets_independently_reconstructed=True,primary_summary_word_counts_and_interval_metrics_match=True,baseline_source_hashes_unchanged=True,same60terms_personas_models_and_main_seed_verified=True,recommendation_coin_and_parent_selection_independently_replayed=True,technical_pilots_excluded=True,no_manuscript_written=True,code_sha256=sha(Path(__file__)),audits=[r['audit'] for r in results])
 (out/'independent_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps([row for r in results for row in r['rows'] if row['group']=='nonseed'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
