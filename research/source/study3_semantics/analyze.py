"""Post-freeze reporting only. All metrics descriptive, no pseudoreplicated tests."""
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import json,csv,hashlib,statistics
R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text())
def save(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 jobs=load(R/'materials/jobs.json');cases={x['id']:x for x in load(R/'materials/cases.json')};bank={x['id']:x for x in load(R/'materials/item_bank.json')};checks=[];records=[]
 for n,h in load(R/'freeze.json')['files'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
 for model in ['llama','qwen','gemma','mistral']:
  p=R/'runs/main'/model/'calls.jsonl';calls=[json.loads(x) for x in p.read_text().splitlines()];cc={x['job_key']:x for x in calls if x['status']=='completed'};expected=[x for x in jobs if x['model']==model];assert len(cc)==len(calls)==len(expected)
  for j in expected:
   x=cc[j['key']];assert x['output'] in ['0','1','2','3'] and x['generation_tokens']==1
   assert x['request_hash']==hashlib.sha256(json.dumps(x['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
   assert x['request']['content']==j['content'] and x['request']['seed']==j['sampling_seed'];assert x['correct']==(int(x['output'])==j['correct'])
   c=cases[j['case_id']];q=bank[j['item_id']];assert j['options'][j['correct']]==q['correct']
   records.append(dict(model=model,case_id=j['case_id'],agent=j['agent'],term_id=j['term_id'],word=c['word'],kind=j['kind'],item_id=j['item_id'],state=j['state'],response=int(x['output']),answer=j['correct'],correct=int(x['correct']),cycle=c['cycle'],prior_exposure=c['earlier_or_same_turn_exposure'],current_incoming_contains_term=c['current_incoming_contains_term'],exact_source_definition_in_prefix=c['exact_source_definition_in_prefix']))
  checks.append(dict(model=model,responses=len(calls),latest_response=calls[-1]['time'],seconds=sum(x['seconds'] for x in calls),calls_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 summary=[];transitions=[];byword=[];sensitivity=[];strata=[]
 for model in ['llama','qwen','gemma','mistral']:
  for kind in ['meaning','application']:
   rr=[x for x in records if x['model']==model and x['kind']==kind];pair={}
   for x in rr:pair.setdefault((x['case_id'],x['item_id']),{})[x['state']]=x
   for state in ['initial','use']:
    sub=[x for x in rr if x['state']==state];terms=defaultdict(list)
    for x in sub:terms[x['term_id']].append(x['correct'])
    macro=statistics.mean(statistics.mean(v) for v in terms.values())
    summary.append(dict(model=model,kind=kind,state=state,cases=len({x['case_id'] for x in sub}),words=len(terms),items=len(sub),correct=sum(x['correct'] for x in sub),micro_accuracy=statistics.mean(x['correct'] for x in sub),macro_word_accuracy=macro))
    byword.extend(dict(model=model,kind=kind,state=state,term_id=w,word=next(x['word'] for x in sub if x['term_id']==w),items=len(v),accuracy=statistics.mean(v)) for w,v in terms.items())
   tr=Counter((p['initial']['correct'],p['use']['correct']) for p in pair.values());transitions.append(dict(model=model,kind=kind,item_pairs=len(pair),wrong_wrong=tr[0,0],wrong_right=tr[0,1],right_wrong=tr[1,0],right_right=tr[1,1],micro_change=(tr[0,1]-tr[1,0])/len(pair)))
   def delta(sub):
    states=[]
    for state in ['initial','use']:
     terms=defaultdict(list)
     for x in sub:
      if x['state']==state:terms[x['term_id']].append(x['correct'])
     states.append(statistics.mean(statistics.mean(v) for v in terms.values()))
    return states[1]-states[0]
   for unit in ['term_id','agent']:
    dd=[delta([x for x in rr if x[unit]!=u]) for u in {x[unit] for x in rr}];sensitivity.append(dict(model=model,kind=kind,omitted_unit=unit,min_macro_change=min(dd),max_macro_change=max(dd),note='Leave-one-group-out sensitivity, not confidence interval.'))
   for label in ['prior_exposure','current_incoming_contains_term','exact_source_definition_in_prefix']:
    for flag in [False,True]:
     sub=[x for x in rr if x[label]==flag]
     if not sub:continue
     for state in ['initial','use']:
      ss=[x for x in sub if x['state']==state];strata.append(dict(model=model,kind=kind,stratum=label,flag=flag,state=state,items=len(ss),accuracy=statistics.mean(x['correct'] for x in ss)))
 out=R/'analysis';out.mkdir(exist_ok=True)
 for n,v in [('responses.csv',records),('accuracy_summary.csv',summary),('paired_transitions.csv',transitions),('word_accuracy.csv',byword),('sensitivity.csv',sensitivity),('stratified_accuracy.csv',strata)]:save(out/n,v)
 report=dict(time=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),main_responses=810,pilot_responses_excluded=24,frozen_files_unchanged=True,all_raw_requests_and_answers_verified=True,checks=checks,no_independent_simulation_replications=True,no_human_item_validation=True)
 (out/'completion_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
