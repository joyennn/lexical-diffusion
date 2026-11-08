"""Technical checks in temporary folders, never synthetic observations in run folders."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,shutil,unittest
import controller as c
from setup import W,NEW,SEED,MODELS,PATHS,load,put,sha

class ReplicationTests(unittest.TestCase):
 def test_inference_runners_and_inputs_unchanged(self):
  for condition in PATHS:
   for name in ['models.json','materials/terms.json']:
    self.assertEqual(sha(NEW/PATHS[condition]/name),sha(W/PATHS[condition]/name))
  for condition,name in [('baseline','run_study1.py'),('time200','run_study1.py'),('memory4000','run_study1.py'),('exposure50','run_exposure.py'),('semantics','run.py')]:
   self.assertEqual(sha(NEW/PATHS[condition]/name),sha(W/PATHS[condition]/name))
  self.assertEqual(sha(NEW/PATHS['baseline']/'run_study1.py'),sha(NEW/PATHS['time200']/'run_study1.py'))
  base=(NEW/PATHS['baseline']/'run_study1.py').read_text();mem=(NEW/PATHS['memory4000']/'run_study1.py').read_text()
  self.assertEqual(mem,base.replace('if len(before)>1000:','if len(before)>4000:'))
 def test_seed_changes_all_streams_but_not_source(self):
  self.assertNotEqual(SEED,2026103000);self.assertEqual(SEED%10,0)
  for m in MODELS:
   old=hashlib.sha256(f'{m}/main/s2026103000/c1/a0/action'.encode()).hexdigest()
   new=hashlib.sha256(f'{m}/main/s{SEED}/c1/a0/action'.encode()).hexdigest()
   self.assertNotEqual(old,new)
 def test_question_bank_complete_old_items_unchanged(self):
  bank=load(NEW/PATHS['semantics']/'materials/item_bank.json');old=load(W/PATHS['semantics']/'materials/item_bank.json')
  self.assertEqual(len(bank),180);self.assertEqual({q['term_id'] for q in bank},set(range(60)))
  for q in old:self.assertEqual(q,next(x for x in bank if x['id']==q['id']))
 def test_dynamic_case_generation_matches_independent_retained_case_count(self):
  with TemporaryDirectory() as temp:
   root=Path(temp);sem=root/PATHS['semantics'];(sem/'materials').mkdir(parents=True)
   for name in ['protocol.json','models.json','run.py','materials/item_bank.json','materials/terms.json']:shutil.copy2(NEW/PATHS['semantics']/name,sem/name)
   (root/'study2_mechanisms').mkdir();(root/PATHS['exposure50']).symlink_to(W/PATHS['exposure50'],target_is_directory=True)
   (root/PATHS['baseline']).symlink_to(W/PATHS['baseline'],target_is_directory=True)
   with patch.object(c,'NEW',root),patch.object(c,'SEED',2026103000):c.prepare_semantics()
   cases=load(sem/'materials/cases.json');jobs=load(sem/'materials/jobs.json')
   self.assertEqual(len(cases),135);self.assertEqual(len(jobs),810)
   for case in cases:
    ss=[j for j in jobs if j['case_id']==case['id']];self.assertEqual(len(ss),6)
    for q in {j['item_id'] for j in ss}:
     a,b=[j for j in ss if j['item_id']==q];self.assertEqual(a['options'],b['options']);self.assertEqual(a['sampling_seed'],b['sampling_seed']);self.assertNotEqual(a['state'],b['state'])
if __name__=='__main__':unittest.main()
