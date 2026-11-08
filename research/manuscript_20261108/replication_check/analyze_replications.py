"""Independent raw recount and n=2 descriptive comparisons, without inferential p-values."""
from collections import Counter,defaultdict
from pathlib import Path
import csv,hashlib,json,math,re,statistics,unicodedata
from setup import R,W,NEW,SEED,MODELS,PATHS,load,put,sha,now

OUT=R/'analysis'
def writecsv(name,rows):
 if not rows:return
 OUT.mkdir(exist_ok=True)
 with (OUT/name).open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for row in rows for k in row)));writer.writeheader();writer.writerows(rows)
def norm(s):return unicodedata.normalize('NFKC',s).casefold().replace('’',"'").replace('‘',"'")
def patterns(terms):return {t['id']:re.compile(r'(?<!\w)'+r'\s+'.join(re.escape(x) for x in norm(t['word']).split())+r'(?!\w)') for t in terms}
def groupmeans(rows,key,value):
 groups=defaultdict(list)
 for r in rows:groups[r[key]].append(r[value])
 return statistics.mean(statistics.mean(v) for v in groups.values()) if groups else None

def audit_network(root,condition,model,rep):
 folder=root/PATHS[condition];run=folder/'runs/main'/model;s=load(run/'checkpoint.json');target=200 if condition=='time200' else 100
 assert s['completed'] and s['target_cycles']==target and s['next_cycle']==target+1
 assert s['source_agent']==0 and s['seed']==(2026103000 if rep=='rep01' else SEED)
 assert [(e['cycle'],e['agent']) for e in s['events']]==[(c,a) for c in range(1,target+1) for a in range(10)]
 terms=load(folder/'materials/terms.json');pats=patterns(terms);raw=[json.loads(line) for line in (run/'calls.jsonl').open()];completed=[x for x in raw if x['status']=='completed'];calls={x['key']:x for x in completed}
 assert len(calls)==len(completed) and all(x['request_hash']==hashlib.sha256(json.dumps(x['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest() for x in completed)
 memories={a:'' for a in range(10)};exposures=[];uses={};ex={};messages=[];summary_count=Counter();read_count=Counter();intro_reads=Counter()
 glossary='\n'.join(t['word']+': '+t['meaning'] for t in terms)
 for e in s['events']:
  c,a=e['cycle'],e['agent'];before=e['memory_before'];assert memories[a]==before
  threshold=4000 if condition=='memory4000' else 1000;assert bool(e['summary_task'])==(len(before)>threshold)
  after=before
  if e['summary_task']:
   call=calls[e['summary_task']];assert call['request']['max_tokens']==100 and before in call['request']['content'];after=call['output'][:500];summary_count[a]+=1
  if e['incoming']:
   read_count[a]+=1;intro_reads[a]+=any(x['kind']=='post' and x['initial_material'] for x in e['incoming'])
   visible='\n'.join(x['kind']+': '+x['text'] for x in e['incoming']);after+='\nReceived: '+visible
   for x in e['incoming']:
    if x['agent']==a:continue
    ids=[w for w,p in pats.items() if p.search(norm(x['text']))]
    for w in ids:ex.setdefault((a,w),(c,a))
    exposures.append(dict(cycle=c,turn=a,agent=a,source_agent=x['agent'],source_kind=x['kind'],source_id=x['id'],initial_material=x['initial_material'],term_ids=ids,text=x['text']))
  g=e['generated']
  if g:
   call=calls[g['task_key']];cap=100 if e['action']=='write' else 50;assert g['raw_text']==call['output'] and g['text']==call['output'][:cap]
   assert after in call['request']['content']
   assert ('Private initial source knowledge' in call['request']['content'])==(a==0)
   if a==0:assert glossary in call['request']['content']
   counts={w:len(p.findall(norm(g['text']))) for w,p in pats.items()};assert g['term_ids']==[w for w,n in counts.items() if n]
   for w,n in counts.items():
    if n:uses.setdefault((a,w),(c,a))
   messages.append(dict(cycle=c,agent=a,text=g['text'],counts=counts));after+='\nWrote: '+g['text']
  assert after==e['memory_after'];memories[a]=after
 assert exposures==s['exposures'] and all(memories[a]==s['agents'][a]['memory'] for a in range(10))
 if condition=='time200':
  origin=folder/'origin'/model;base=load(origin/'checkpoint_100.json');prefix=(origin/'calls_1_100.jsonl').read_bytes()
  assert (run/'calls.jsonl').read_bytes().startswith(prefix)
  for n in ['events','posts','comments','exposures']:assert s[n][:len(base[n])]==base[n]
 windows=[(1,100)] if target==100 else [(101,200)]+[(c,c+19) for c in range(101,201,20)]
 if target==100:windows +=[(c,c+19) for c in range(1,101,20)]
 metrics=[]
 for start,end in windows:
  for group,agents in [('nonseed',set(range(1,10))),('source',{0})]:
   selected=[x for x in messages if x['agent'] in agents and start<=x['cycle']<=end];n=len(selected);chars=sum(len(x['text']) for x in selected);freq=Counter({w:sum(x['counts'][w] for x in selected) for w in pats});occ=sum(freq.values());pairs={(x['agent'],w) for x in selected for w,k in x['counts'].items() if k}
   firsts=[k for k,pos in uses.items() if k[0] in agents and start<=pos[0]<=end];linked=[k for k in firsts if k in ex and ex[k]<=uses[k]]
   events=[e for e in s['events'] if e['agent'] in agents and start<=e['cycle']<=end];reads=[e for e in events if e['incoming']];nr=len(reads);ni=sum(any(x['kind']=='post' and x['initial_material'] for x in e['incoming']) for e in reads)
   metrics.append(dict(replication=rep,seed=s['seed'],model=model,condition=condition,group=group,start_cycle=start,end_cycle=end,messages=n,characters=chars,occurrences=occ,occurrences_per100messages=100*occ/n if n else None,occurrences_per1000characters=1000*occ/chars if chars else None,term_bearing_message_percent=100*sum(any(x['counts'].values()) for x in selected)/n if n else None,distinct_used_words=sum(k>0 for k in freq.values()),expression_coverage_percent=100*sum(k>0 for k in freq.values())/60,user_word_pairs_in_window=len(pairs),user_word_coverage_percent=100*len(pairs)/(60*len(agents)),new_exposure_linked_first_users=len(linked),new_linked_pair_coverage_percent=100*len(linked)/(60*len(agents)),read_turns=nr,initial_entry_read_turns=ni,initial_entry_share=ni/nr if nr else None,top_word=terms[freq.most_common(1)[0][0]]['word'] if occ else None,top_word_share=freq.most_common(1)[0][1]/occ if occ else None,summary_calls=sum(bool(e['summary_task']) for e in events),median_memory_before_turn=statistics.median(len(e['memory_before']) for e in events)))
 return metrics,dict(replication=rep,model=model,condition=condition,all_turns_and_raw_text_recounted=True,memory_and_exposure_transitions_verified=True,calls_sha256=sha(run/'calls.jsonl'),checkpoint_sha256=sha(run/'checkpoint.json'))

def audit_semantics(root,rep):
 folder=root/PATHS['semantics'];cases={c['id']:c for c in load(folder/'materials/cases.json')};jobs=load(folder/'materials/jobs.json');bank={q['id']:q for q in load(folder/'materials/item_bank.json')};terms=load(folder/'materials/terms.json');pats=patterns(terms);records=[];checks=[]
 if rep=='rep02':
  for rel,h in load(folder/'freeze.json')['files'].items():assert sha(folder/rel)==h
 for m in MODELS:
  source=root/PATHS['exposure50']/'runs/main'/m;s=load(source/'checkpoint.json');calls={r['key']:r for r in map(json.loads,(source/'calls.jsonl').open()) if r['status']=='completed'};first={}
  for e in s['events']:
   if e['generated'] and e['agent']!=s['source_agent']:
    for w,p in pats.items():
     if p.search(norm(e['generated']['text'])):first.setdefault((e['agent'],w),e)
  cc=[c for c in cases.values() if c['model']==m];assert len(cc)==len(first)
  for c in cc:
   event=first[c['agent'],c['term_id']];raw=calls[event['generated']['task_key']];assert raw['request_hash']==c['original_request_hash'] and raw['request']['content'].split('\nTask:\n')[0]==c['use_prefix']
  jj=[j for j in jobs if j['model']==m];path=folder/'runs/main'/m/'calls.jsonl';raw=[json.loads(x) for x in path.open()] if path.exists() else [];done=[x for x in raw if x['status']=='completed'];lookup={x['job_key']:x for x in done};assert len(jj)==len(done)==len(lookup)==6*len(cc)
  pairs={}
  for j in jj:
   r=lookup[j['key']];c=cases[j['case_id']];q=bank[j['item_id']];assert r['request']['content']==j['content']==c[j['state']+'_prefix']+'\nTask:\n'+j['content'].split('\nTask:\n')[1]
   assert r['request']['seed']==j['sampling_seed'] and j['options'][j['correct']]==q['correct'];correct=int(r['output'])==j['correct'];assert correct==r['correct']
   assert r['request_hash']==hashlib.sha256(json.dumps(r['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
   records.append(dict(replication=rep,model=m,case_id=c['id'],agent=c['agent'],term_id=c['term_id'],word=c['word'],kind=j['kind'],state=j['state'],item_id=j['item_id'],correct=int(correct),exact_source_definition_in_prefix=c['exact_source_definition_in_prefix'],prior_exposure=c['earlier_or_same_turn_exposure']))
   pairs.setdefault((j['case_id'],j['item_id']),{})[j['state']]=j
  for pair in pairs.values():
   a,b=pair['initial'],pair['use'];assert a['options']==b['options'] and a['sampling_seed']==b['sampling_seed']
  checks.append(dict(replication=rep,model=m,first_cases=len(cc),responses=len(done),all_first_uses_recovered=True,exact_prefix_and_paired_answers_verified=True))
 summary=[];transitions=[];strata=[]
 for m in MODELS:
  for kind in ['meaning','application']:
   rr=[x for x in records if x['model']==m and x['kind']==kind]
   for state in ['initial','use']:
    ss=[x for x in rr if x['state']==state]
    summary.append(dict(replication=rep,model=m,kind=kind,state=state,cases=len({x['case_id'] for x in ss}),words=len({x['term_id'] for x in ss}),items=len(ss),correct=sum(x['correct'] for x in ss),micro_accuracy=statistics.mean(x['correct'] for x in ss) if ss else None,macro_word_accuracy=groupmeans(ss,'term_id','correct')))
    for flag in [False,True]:
     sub=[x for x in ss if x['exact_source_definition_in_prefix']==flag];strata.append(dict(replication=rep,model=m,kind=kind,state=state,definition_present=flag,items=len(sub),accuracy=statistics.mean(x['correct'] for x in sub) if sub else None))
   pair={}
   for x in rr:pair.setdefault((x['case_id'],x['item_id']),{})[x['state']]=x['correct']
   counts=Counter((v['initial'],v['use']) for v in pair.values());transitions.append(dict(replication=rep,model=m,kind=kind,wrong_wrong=counts[0,0],wrong_right=counts[0,1],right_wrong=counts[1,0],right_right=counts[1,1]))
 return records,summary,transitions,strata,checks

def main():
 OUT.mkdir(exist_ok=True);metrics=[];checks=[]
 for rep,root in [('rep01',W),('rep02',NEW)]:
  for condition in ['baseline','exposure50','memory4000','time200']:
   for m in MODELS:
    mm,check=audit_network(root,condition,m,rep);metrics+=mm;checks.append(check)
 writecsv('run_metrics.csv',metrics)
 mainrows=[r for r in metrics if r['group']=='nonseed' and r['end_cycle']-r['start_cycle']==99];contrasts=[];stats=[]
 keys=['occurrences_per100messages','occurrences_per1000characters','term_bearing_message_percent','expression_coverage_percent','user_word_coverage_percent']
 for m in MODELS:
  for condition in ['exposure50','memory4000','time200']:
   for key in keys:
    paired=[]
    for rep in ['rep01','rep02']:
     base=next(r for r in mainrows if r['model']==m and r['condition']=='baseline' and r['replication']==rep);other=next(r for r in mainrows if r['model']==m and r['condition']==condition and r['replication']==rep);a,b=base[key],other[key];diff=b-a if a is not None and b is not None else None
     row=dict(replication=rep,model=m,condition=condition,metric=key,baseline=a,condition_value=b,absolute_difference=diff,relative_change_percent=100*(b/a-1) if a and b is not None else None);contrasts.append(row);paired.append(row)
    ds=[x['absolute_difference'] for x in paired if x['absolute_difference'] is not None]
    stats.append(dict(model=m,condition=condition,metric=key,independent_seed_pairs=len(ds),rep01_difference=paired[0]['absolute_difference'],rep02_difference=paired[1]['absolute_difference'],mean_difference=statistics.mean(ds) if ds else None,sample_sd=statistics.stdev(ds) if len(ds)>1 else None,min_difference=min(ds) if ds else None,max_difference=max(ds) if ds else None,same_nonzero_direction=len(ds)==2 and ds[0]*ds[1]>0,pvalue=None,confidence_interval=None,interpretation='Two-run descriptive agreement, not stable uncertainty or confirmatory evidence.'))
 writecsv('within_seed_contrasts.csv',contrasts);writecsv('two_run_descriptive_summary.csv',stats)
 records=[];summary=[];transitions=[];strata=[];semchecks=[]
 for rep,root in [('rep01',W),('rep02',NEW)]:
  rr,ss,tt,st,cc=audit_semantics(root,rep);records+=rr;summary+=ss;transitions+=tt;strata+=st;semchecks+=cc
 writecsv('semantic_responses.csv',records);writecsv('semantic_accuracy_by_run.csv',summary);writecsv('semantic_paired_transitions.csv',transitions);writecsv('semantic_definition_strata.csv',strata)
 common=[];semtwo=[]
 for m in MODELS:
  for kind in ['meaning','application']:
   sets=[{x['term_id'] for x in records if x['model']==m and x['kind']==kind and x['replication']==rep} for rep in ['rep01','rep02']];shared=set.intersection(*sets)
   for rep in ['rep01','rep02']:
    for state in ['initial','use']:
     sub=[x for x in records if x['model']==m and x['kind']==kind and x['replication']==rep and x['state']==state and x['term_id'] in shared]
     common.append(dict(model=m,kind=kind,replication=rep,state=state,common_words=len(shared),macro_word_accuracy=groupmeans(sub,'term_id','correct'),items=len(sub)))
   changes=[]
   for rep in ['rep01','rep02']:
    a,b=[next(x['macro_word_accuracy'] for x in summary if x['model']==m and x['kind']==kind and x['replication']==rep and x['state']==state) for state in ['initial','use']];changes.append(b-a if a is not None and b is not None else None)
   ds=[d for d in changes if d is not None];semtwo.append(dict(model=m,kind=kind,rep01_macro_change=changes[0],rep02_macro_change=changes[1],equal_run_mean_macro_change=statistics.mean(ds) if ds else None,same_nonzero_direction=len(ds)==2 and ds[0]*ds[1]>0,word_sets_differ=True,pvalue=None,confidence_interval=None))
 writecsv('semantic_common_word_sensitivity.csv',common);writecsv('semantic_two_run_summary.csv',semtwo)
 # Old outcomes and frozen new inputs remain immutable throughout the workflow.
 for rel,h in load(R/'original_manifest.json').items():assert sha(W/rel)==h
 for rel,h in load(R/'freeze.json')['files'].items():assert sha(R/rel)==h
 put(OUT/'independent_audit.json',dict(time=now(),all_original_files_unchanged=True,independent_raw_text_memory_and_exposure_recount=True,semantic_case_prefix_and_answer_recount=True,network_checks=checks,semantic_checks=semchecks,independent_runs_per_model_condition=2,no_inferential_pvalues_or_bootstrap_intervals=True))
 lines=['추가 반복과 검산 완료. 모델·조건별 독립 실행은 총2회이며, 시간 연장의 전·후반은 동일 궤적입니다.','두 실행을 각각 표시하고 차이의 평균·범위·방향 일치를 비교합니다. n=2로 안정적인 신뢰구간이나 일반화 가능한 유의성을 주장하지 않습니다.','']
 names={'exposure50':'접근성 증가','time200':'시간 연장','memory4000':'메모리 조정'}
 for condition in ['exposure50','time200','memory4000']:
  lines.append(names[condition])
  for m in MODELS:
   ss=[x for x in contrasts if x['condition']==condition and x['model']==m and x['metric']=='occurrences_per100messages']
   lines.append(m+': '+ '; '.join(f"{x['replication']} {x['baseline']:.2f}→{x['condition_value']:.2f} ({x['relative_change_percent']:+.1f}%)" if x['relative_change_percent'] is not None else f"{x['replication']} 변화율 산출 불가" for x in ss))
  lines.append('')
 lines.append('Study3은 각 실행에서 실제 사용된 표현에 조건화된 평가입니다. 단어집합과 사례 수 차이 및 동일 단어 민감도 결과를 함께 확인해야 합니다. 최초45표현 문항은 유지하고, 나머지15표현 문항은 새 실행 전 고정했습니다. 인간 검증을 받은 도구나 실제 발화 의미 적합성 평가로 해석하지 않습니다.')
 (OUT/'결과요약.txt').write_text('\n'.join(lines))
 print('\n'.join(lines),flush=True)
if __name__=='__main__':main()
