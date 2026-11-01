"""Verify baseline feed and4000character trigger; compare all60 use and memory diagnostics."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,random,re,statistics
from run_study1 import ROOT,read,put,stamp,terms_in
from metrics import derive,patterns,BASE

def audit(folder,model,stage,cycles):
 s=read(folder/'checkpoint.json');assert s['completed'] and s['target_cycles']==cycles
 assert [(e['cycle'],e['agent']) for e in s['events']]==[(c,a) for c in range(1,cycles+1) for a in range(10)]
 rows=[json.loads(l) for l in (folder/'calls.jsonl').read_text().splitlines()];calls=[x for x in rows if x['status']=='completed'];lookup={x['key']:x for x in calls};assert len(calls)==len(lookup)
 assert all(x['key'].startswith(stage+'/') and x['prompt_tokens']<=7680 for x in calls)
 terms=read(ROOT/'materials/terms.json');seed=s['seed'];mem={a:'' for a in range(10)};seen={a:[] for a in range(10)};ex=[];summaries=[]
 postkeys={x['task_key']:x['id'] for x in s['posts'] if not x['initial_material']}
 for e in s['events']:
  c,a=e['cycle'],e['agent'];before=e['memory_before'];assert before==mem[a]
  assert bool(e['summary_task'])==(len(before)>4000)
  after=before
  if e['summary_task']:
   call=lookup[e['summary_task']];assert call['request']['max_tokens']==100
   after=call['output'][:500]
   assert 'at most 500 characters' in call['request']['content'] and before in call['request']['content']
   ids=set(terms_in(before,terms));kept=set(terms_in(after,terms))
   summaries.append(dict(model=model,stage=stage,cycle=c,agent=a,memory_chars_before=len(before),summary_chars=len(after),word_forms_before=len(ids),word_forms_retained=len(ids&kept),word_form_retention_fraction=len(ids&kept)/len(ids) if ids else None))
  assert 'feed_branch' not in e
  if e['action'] in ['read','comment','read_no_available_post']:
   available=[x for x in s['posts'] if x['initial_material'] or x['cycle']<c or (x['cycle']==c and x['agent']<a)]
   eligible=[x for x in available if x['agent']!=a and x['id'] not in seen[a]]
   if eligible:
    parent=random.Random(int(hashlib.sha256((str(seed)+f'/c{c}/a{a}/feed').encode()).hexdigest()[:8],16)).choice(eligible);assert e['parent_id']==parent['id'];seen[a].append(parent['id'])
   else:assert e['parent_id'] is None
  if e['incoming']:
   visible='\n'.join(x['kind']+': '+x['text'] for x in e['incoming']);after+='\nReceived: '+visible
   assert visible in lookup[f'{stage}/s{seed}/c{c}/a{a}/reaction']['request']['content']
   for x in e['incoming']:
    if x['agent']!=a:ex.append(dict(cycle=c,turn=a,agent=a,source_agent=x['agent'],source_kind=x['kind'],source_id=x['id'],initial_material=x['initial_material'],term_ids=terms_in(x['text'],terms),text=x['text']))
  if e['generated']:
   g=e['generated'];call=lookup[g['task_key']];assert g['raw_text']==call['output'] and g['text']==call['output'][:(100 if e['action']=='write' else 50)]
   assert g['term_ids']==terms_in(g['text'],terms);after+='\nWrote: '+g['text']
   if e['action']=='write':seen[a].append(postkeys[g['task_key']])
  assert after==e['memory_after'];mem[a]=after
 assert ex==s['exposures'] and all(mem[a]==s['agents'][a]['memory'] for a in range(10))
 for x in calls:assert x['request_hash']==hashlib.sha256(json.dumps(x['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 return dict(model=model,stage=stage,cycles=cycles,completed_calls=len(calls),failed_calls=len(rows)-len(calls),summary_calls=len(summaries),seconds=sum(x['seconds'] for x in calls),max_prompt_tokens=max(x['prompt_tokens'] for x in calls),baseline_feed_and4000_trigger_and500cap_verified=True,calls_sha256=hashlib.sha256((folder/'calls.jsonl').read_bytes()).hexdigest(),checkpoint_sha256=hashlib.sha256((folder/'checkpoint.json').read_bytes()).hexdigest()),summaries

def writecsv(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def memory_diagnostics(state,folder,study,model):
 calls={x['key']:x for x in (json.loads(l) for l in (folder/'calls.jsonl').read_text().splitlines()) if x['status']=='completed'};terms=read(ROOT/'materials/terms.json');records=[]
 for group,who in [('all',range(10)),('source',[0]),('nonseed',range(1,10))]:
  events=[e for e in state['events'] if e['agent'] in who];ss=[e for e in events if e['summary_task']]
  after=[calls[e['summary_task']]['output'][:500] for e in ss];eligible=[];retained=0;total=0
  for e,text in zip(ss,after):
   old=set(terms_in(e['memory_before'],terms));new=set(terms_in(text,terms));total+=len(old);retained+=len(old&new)
  records.append(dict(study=study,model=model,group=group,summary_calls=len(ss),median_memory_chars_before_turn=statistics.median(len(e['memory_before']) for e in events),max_memory_chars_before_turn=max(len(e['memory_before']) for e in events),median_chars_before_summary=statistics.median(len(e['memory_before']) for e in ss) if ss else None,median_stored_summary_chars=statistics.median(map(len,after)) if ss else None,summary_word_forms_before=total,summary_word_forms_retained=retained,pooled_literal_form_retention=retained/total if total else None,interpretation='Surface-form retention across summary, not semantic-memory validation.'))
 return records

def main():
 plan=read(ROOT/'protocol.json');out=ROOT/'analysis';out.mkdir(exist_ok=True);allrows=[[],[],[],[]];checks=[];memory=[];summary_events=[]
 for m in plan['models']:
  check,se=audit(ROOT/'runs/main'/m,m,'main',100);checks.append(check);summary_events+=se
  for study,root in [('baseline',BASE),('memory4000',ROOT)]:
   f=root/'runs/main'/m;state=read(f/'checkpoint.json')
   for dest,items in zip(allrows,derive(state,study,m)):dest.extend(items)
   memory+=memory_diagnostics(state,f,study,m)
 for name,rs in zip(['summary.csv','twenty_cycle_bins.csv','word_metrics.csv','exposure_pairs.csv'],allrows):writecsv(out/name,rs)
 writecsv(out/'memory_diagnostics.csv',memory)
 if summary_events:writecsv(out/'summary_events.csv',summary_events)
 put(out/'completion_audit.json',dict(time=stamp(),all_four_fresh100cycle_runs_verified=True,pilots_excluded=True,checks=checks))
 print('Fresh memory4000 runs audited; all60 baseline comparison and memory diagnostics computed. No manuscript.')
if __name__=='__main__':main()
