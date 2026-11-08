"""Read-only verification of published code, instrument, scores and table inputs."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,hashlib,json,statistics,ast,re
R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text())
def main():
 for line in (R/'SHA256SUMS').read_text().splitlines():
  expected,rel=line.split('  ',1);assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==expected,rel
 bank=load(R/'study3_questions/item_bank_180.json');old=load(R/'study3_questions/item_bank_original_135.json');items={q['id']:q for q in bank}
 assert len(items)==180 and len(old)==135 and len({q['term_id'] for q in bank})==60
 assert all(items[q['id']]==q for q in old)
 for q in bank:assert len(q['distractors'])==3 and len(set([q['correct'],*q['distractors']]))==4
 assert Counter(q['kind'] for q in bank)=={'meaning':60,'application':120}
 views=load(R/'study3_questions/actual_item_presentations_1482.json');assert len(views)==1482
 scores=list(csv.DictReader((R/'replication_check/analysis/semantic_responses.csv').open()));assert len(scores)==1482
 pairs=defaultdict(dict);ids=set();cases=set()
 for v in views:
  item=items[v['item_id']];assert v['correct'] in range(4)
  assert v['options'][v['correct']]==item['correct']==v['correct_option_text']
  assert sorted(v['options'])==sorted([item['correct'],*item['distractors']])
  ident=(v['run'],v['model'],v['case_id'],v['item_id'],v['state']);assert ident not in ids;ids.add(ident)
  pairs[ident[:-1]][v['state']]=v;cases.add((v['run'],v['model'],v['case_id']))
 for p in pairs.values():
  assert set(p)=={'initial','use'}
  for key in ['options','correct','sampling_seed']:assert p['initial'][key]==p['use'][key]
 for r in scores:
  assert (dict(rep01='Run1',rep02='Run2')[r['replication']],r['model'],r['case_id'],r['item_id'],r['state']) in ids
  assert r['correct'] in ['0','1']
 assert len(cases)==247 and Counter(v['run'] for v in views)=={'Run1':810,'Run2':672}
 allrows=list(csv.DictReader((R/'replication_check/analysis/run_metrics.csv').open()))
 rows=[r for r in allrows if r['group']=='nonseed' and int(r['end_cycle'])-int(r['start_cycle'])==99];assert len(rows)==32
 for cell in load(R/'results/study2_three_metrics_mean_sd.json'):
  for condition in ['baseline','exposure50','time200','memory4000']:
   selected=[r for r in rows if r['model']==cell['model'] and r['condition']==condition];assert len(selected)==2
   assert all((r['start_cycle'],r['end_cycle'])==(('101','200') if condition=='time200' else ('1','100')) for r in selected)
   vals=[float(r[cell['metric']]) for r in selected]
   assert cell[condition]==f'{statistics.mean(vals):.2f} ({statistics.stdev(vals):.2f})'
 for p in R.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
 for p in R.rglob('*.md'):
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if not target.startswith(('http:','https:','#')):assert (p.parent/target.split('#')[0]).exists(),(p,target)
 print('PASS: file hashes; 180 items and 135 retained originals; 247 cases and 1482 paired presentations; score alignment; all 48 mean/SD cells; Python syntax; documentation links. No inference or posterior sampling.')
if __name__=='__main__':main()
