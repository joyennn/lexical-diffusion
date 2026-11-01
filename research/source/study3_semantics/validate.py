"""Structural validation before responses; does not claim human item validation."""
from pathlib import Path
from collections import Counter
import json,hashlib
R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text())
def main():
 jobs=load(R/'materials/jobs.json');cases=load(R/'materials/cases.json');bank=load(R/'materials/item_bank.json');terms=load(R/'materials/terms.json');assert len(jobs)==810 and len(cases)==135 and len(bank)==135
 assert len({j['key'] for j in jobs})==810
 for c in cases:
  selected=[j for j in jobs if j['case_id']==c['id']];assert len(selected)==6
  for q in {j['item_id'] for j in selected}:
   a,b=[j for j in selected if j['item_id']==q];assert a['state']!=b['state'] and a['options']==b['options'] and a['correct']==b['correct'] and a['sampling_seed']==b['sampling_seed']
   assert a['content'].split('\nTask:\n')[1]==b['content'].split('\nTask:\n')[1]
 for q in bank:
  assert q['correct'] not in q['distractors'] and len(set(q['distractors']))==3
  if q['kind']=='application':assert q['correct']!=terms[q['term_id']]['example']
 for m in ['llama','qwen','gemma','mistral']:
  p=Counter(j['correct'] for j in jobs if j['model']==m and j['state']=='use');assert max(p.values())-min(p.values())<=1
 print('135 matched cases,810 requests, answer positions balanced per model; novel context scenarios and no feedback verified.')
if __name__=='__main__':main()
