"""Post-run secondary audit; does not change frozen analysis or simulation."""
from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import json,csv,re,unicodedata,hashlib,random,statistics
R=Path(__file__).resolve().parent; B=R.parents[1]/'fresh_study1'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def norm(x):return unicodedata.normalize('NFKC',x).casefold().replace('’',"'").replace('‘',"'")
def save(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 terms=load(R/'materials/terms.json'); pats={t['id']:re.compile(r'(?<!\w)'+r'\s+'.join(re.escape(x) for x in norm(t['word']).split())+r'(?!\w)') for t in terms}
 ids=lambda text:{i for i,p in pats.items() if p.search(norm(text))}
 for n,h in load(R/'freeze.json')['files'].items():assert sha(R/n)==h,n
 prov=load(R/'provenance.json');assert sha(B/'run_study1.py')==prov['baseline_runner_sha256']
 assert (R/'run_study1.py').read_text()==(B/'run_study1.py').read_text().replace('if len(before)>1000:','if len(before)>4000:')
 for n,h in prov['baseline_inputs_sha256'].items():assert sha(B/n)==sha(R/n)==h
 primary={(x['study'],x['model'],x['group']):x for x in csv.DictReader((R/'analysis/summary.csv').open())}
 bins={(x['study'],x['model'],x['group'],int(x['start_cycle'])):x for x in csv.DictReader((R/'analysis/twenty_cycle_bins.csv').open())}
 rows=[];intervals=[];wordrows=[];checks=[];memrows=[]
 for study,root,limit in [('baseline',B,1000),('memory4000',R,4000)]:
  for m in ['llama','qwen','gemma','mistral']:
   d=root/'runs/main'/m;s=load(d/'checkpoint.json');assert s['completed'] and s['target_cycles']==100 and s['next_cycle']==101
   calls=[json.loads(x) for x in (d/'calls.jsonl').read_text().splitlines()];cl={x['key']:x for x in calls};assert len(cl)==len(calls) and all(x['status']=='completed' for x in calls)
   for x in calls:assert x['request_hash']==hashlib.sha256(json.dumps(x['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
   public=sorted([dict(x,channel='post') for x in s['posts'] if not x['initial_material']]+[dict(x,channel='comment') for x in s['comments']],key=lambda x:(x['cycle'],x['agent']))
   uses={}; messages=[];received={};firstex={}
   for x in public:
    raw=cl[x['task_key']]['output'];assert raw==x['raw_text'] and x['text']==raw[:(100 if x['channel']=='post' else 50)]
    counts={i:len(p.findall(norm(x['text']))) for i,p in pats.items()};assert [i for i,n in counts.items() if n]==x['term_ids'];messages.append(dict(x,counts=counts))
    for i,n in counts.items():
     if n:uses.setdefault((x['agent'],i),(x['cycle'],x['agent']))
   for x in s['exposures']:
    assert x['source_agent']!=x['agent'];key=x['cycle'],x['agent'];ii=ids(x['text']);assert sorted(ii)==x['term_ids']
    assert x['text'] in cl[f"main/s{s['seed']}/c{key[0]}/a{key[1]}/reaction"]['request']['content']
    received.setdefault(key,dict(words=set(),initial=False));received[key]['words']|=ii;received[key]['initial']|=x['source_kind']=='post' and x['initial_material']
    for i in ii:firstex.setdefault((x['agent'],i),key)
   memory={a:'' for a in range(10)};seen={a:[] for a in range(10)};summaryevents=[]
   ownposts={x['task_key']:x['id'] for x in s['posts'] if not x['initial_material']}
   assert [(e['cycle'],e['agent']) for e in s['events']]==[(c,a) for c in range(1,101) for a in range(10)]
   for e in s['events']:
    a=e['agent'];c=e['cycle'];before=memory[a];assert before==e['memory_before'];assert bool(e['summary_task'])==(len(before)>limit)
    after=before
    if e['summary_task']:
     call=cl[e['summary_task']];assert call['request']['max_tokens']==100 and call['generation_tokens']<=100 and 'at most 500 characters' in call['request']['content'] and before in call['request']['content'];after=call['output'][:500]
     summaryevents.append(dict(agent=a,before=len(before),stored=len(after),forms=len(ids(before)),retained=len(ids(before)&ids(after))))
    assert 'feed_branch' not in e
    if e['action'] in ['read','comment','read_no_available_post']:
     eligible=[p for p in s['posts'] if (p['initial_material'] or (p['cycle'],p['agent'])<(c,a)) and p['agent']!=a and p['id'] not in seen[a]]
     expected=random.Random(int(hashlib.sha256((str(s['seed'])+f'/c{c}/a{a}/feed').encode()).hexdigest()[:8],16)).choice(eligible)['id'] if eligible else None
     assert e['parent_id']==expected
     if expected is not None:seen[a].append(expected)
    if e['incoming']:after+='\nReceived: '+'\n'.join(x['kind']+': '+x['text'] for x in e['incoming'])
    if e['generated']:
     after+='\nWrote: '+e['generated']['text']
     if e['action']=='write':seen[a].append(ownposts[e['generated']['task_key']])
    assert after==e['memory_after'];memory[a]=after
   assert all(memory[a]==s['agents'][a]['memory'] for a in range(10))
   for group,agents in [('all',list(range(10))),('source',[s['source_agent']]),('nonseed',[a for a in range(10) if a!=s['source_agent']])]:
    ms=[x for x in messages if x['agent'] in agents];wc=Counter({i:sum(x['counts'][i] for x in ms) for i in pats});total=sum(wc.values());chars=sum(len(x['text']) for x in ms);pairs=[k for k in uses if k[0] in agents];qual=[k for k in pairs if k in firstex and firstex[k]<=uses[k]];read=[v for (c,a),v in received.items() if a in agents];dose=Counter((a,i) for (c,a),v in received.items() if a in agents for i in v['words'])
    row=dict(study=study,model=m,group=group,messages=len(ms),characters=chars,occurrences=total,occurrences_per100messages=100*total/len(ms),occurrences_per1000characters=1000*total/chars,term_bearing_message_percent=100*sum(any(x['counts'].values()) for x in ms)/len(ms),distinct_used_words=sum(n>0 for n in wc.values()),unique_user_word_pairs=len(pairs),exposure_linked_first_users=len(qual),repeat_occurrences=total-len(pairs),read_turns=len(read),initial_entry_read_turns=sum(x['initial'] for x in read),initial_entry_share=sum(x['initial'] for x in read)/len(read),zero_exposure_pairs=len(agents)*60-len(dose),mean_external_exposure_turns=sum(dose.values())/(len(agents)*60),top_word=terms[wc.most_common(1)[0][0]]['word'],top_word_share=wc.most_common(1)[0][1]/total)
    ref=primary[study,m,group]
    for k,v in row.items():
     if k in ref and k not in ['study','model','group']:assert abs(float(ref[k])-v)<1e-10,(study,m,group,k)
    rows.append(row)
    for start in range(1,101,20):
     chunk=[x for x in ms if start<=x['cycle']<start+20];n=sum(sum(x['counts'].values()) for x in chunk);rr=dict(study=study,model=m,group=group,start_cycle=start,messages=len(chunk),occurrences=n,occurrences_per100messages=100*n/len(chunk));assert int(bins[study,m,group,start]['occurrences'])==n;intervals.append(rr)
    wordrows.extend(dict(study=study,model=m,group=group,word=terms[i]['word'],occurrences=wc[i],users=sum((a,i) in uses for a in agents)) for i in pats)
    ss=[x for x in summaryevents if x['agent'] in agents];ee=[x for x in s['events'] if x['agent'] in agents];forms=sum(x['forms'] for x in ss)
    memrows.append(dict(study=study,model=m,group=group,summary_calls=len(ss),median_memory_before=statistics.median(len(x['memory_before']) for x in ee),max_memory_before=max(len(x['memory_before']) for x in ee),literal_forms_before_summary=forms,literal_forms_retained=sum(x['retained'] for x in ss),literal_retention=sum(x['retained'] for x in ss)/forms if forms else None))
   checks.append(dict(study=study,model=m,cycles=100,calls=len(calls),last_response=calls[-1]['time'],memory_and_feed_replayed=True,calls_sha256=sha(d/'calls.jsonl'),checkpoint_sha256=sha(d/'checkpoint.json')))
 out=R/'analysis/final_review';out.mkdir(exist_ok=True)
 for n,v in [('verified_metrics.csv',rows),('verified_intervals.csv',intervals),('verified_words.csv',wordrows),('verified_memory.csv',memrows)]:save(out/n,v)
 report=dict(time=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),frozen_files_unchanged=True,only_engine_change_1000_to4000=True,same_inputs_and_models=True,raw_public_messages_exposures_and_memory_verified=True,primary_metrics_match=True,pilots_excluded=True,checks=checks,review_code_sha256=sha(Path(__file__)))
 (out/'independent_audit.json').write_text(json.dumps(report,indent=2))
 print(json.dumps([x for x in rows if x['group']=='nonseed'],indent=2));print('MEMORY',json.dumps([x for x in memrows if x['group']=='nonseed'],indent=2))
if __name__=='__main__':main()
