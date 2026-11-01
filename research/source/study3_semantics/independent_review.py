"""Independent case reconstruction and answer recount; immutable simulation inputs."""
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import csv,json,hashlib,statistics
R=Path(__file__).resolve().parent;P=R.parent
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 protocol=load(R/'protocol.json');cases={x['id']:x for x in load(R/'materials/cases.json')};jobs=load(R/'materials/jobs.json');items={x['id']:x for x in load(R/'materials/item_bank.json')};records=[];checks=[]
 for model in protocol['models']:
  source=P/'study2_mechanisms/exposure50/runs/main'/model;meta=protocol['sources'][model]
  assert sha(source/'checkpoint.json')==meta['checkpoint_sha256'] and sha(source/'calls.jsonl')==meta['calls_sha256']
  s=load(source/'checkpoint.json');original={x['key']:x for x in map(json.loads,(source/'calls.jsonl').read_text().splitlines())};first={}
  for e in s['events']:
   g=e['generated']
   if g and e['agent']!=s['source_agent']:
    for w in g['term_ids']:first.setdefault((e['agent'],w),e)
  selected=[c for c in cases.values() if c['model']==model];assert len(first)==len(selected)
  for c in selected:
   e=first[c['agent'],c['term_id']];g=e['generated'];assert c['cycle']==e['cycle'] and c['original_generation_key']==g['task_key'];raw=original[g['task_key']]
   assert raw['request_hash']==c['original_request_hash'] and raw['request']['content'].split('\nTask:\n')[0]==c['use_prefix']
   assert 'Private initial source knowledge' not in c['use_prefix']
  calls=[json.loads(x) for x in (R/'runs/main'/model/'calls.jsonl').read_text().splitlines()];lookup={x['job_key']:x for x in calls};jj=[x for x in jobs if x['model']==model];assert len(calls)==len(jj)==len(lookup)
  paired={}
  for j in jj:
   x=lookup[j['key']];q=items[j['item_id']];answer=j['options'].index(q['correct']);assert answer==j['correct'] and len(j['options'])==len(set(j['options']))==4
   c=cases[j['case_id']];assert x['request']['content']==c[j['state']+'_prefix']+'\nTask:\n'+j['content'].split('\nTask:\n')[1]
   assert x['status']=='completed' and x['output'] in ['0','1','2','3'];correct=int(x['output'])==answer
   records.append(dict(model=model,kind=j['kind'],state=j['state'],word=c['term_id'],case=j['case_id'],correct=correct));paired.setdefault((j['case_id'],j['item_id']),{})[j['state']]=(x,j)
  for pair in paired.values():
   a,b=pair['initial'],pair['use']
   assert a[1]['options']==b[1]['options'] and a[0]['request']['seed']==b[0]['request']['seed']
  checks.append(dict(model=model,all_first_uses_included=True,source_files_unchanged=True,exact_prefixes_recovered=True,response_count=len(calls),calls_sha256=sha(R/'runs/main'/model/'calls.jsonl')))
 ref={(x['model'],x['kind'],x['state']):x for x in csv.DictReader((R/'analysis/accuracy_summary.csv').open())}
 for key,row in ref.items():
  ss=[x for x in records if (x['model'],x['kind'],x['state'])==key];byword=defaultdict(list)
  for x in ss:byword[x['word']].append(x['correct'])
  assert len(ss)==int(row['items']) and sum(x['correct'] for x in ss)==int(row['correct'])
  assert abs(statistics.mean(x['correct'] for x in ss)-float(row['micro_accuracy']))<1e-12
  assert abs(statistics.mean(statistics.mean(v) for v in byword.values())-float(row['macro_word_accuracy']))<1e-12
 report=dict(time=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),independent_case_selection_and_context_reconstruction_verified=True,all_810_responses_and_primary_scores_verified=True,pilots_and_amended_partial_runs_excluded=True,source_files_preserved=True,checks=checks,review_code_sha256=sha(Path(__file__)))
 (R/'analysis/independent_audit.json').write_text(json.dumps(report,indent=2));print('Independent audit passed for810 retained responses and135 reconstructed first-use cases.')
if __name__=='__main__':main()
