"""Synthetic control-flow checks only; temporary data are never evidence."""
import json,tempfile,time,unittest,shutil
from pathlib import Path
from unittest.mock import patch
import run_study1 as run
class FakeBackend:
 stop_once=True
 def __init__(self,name,out,deadline):self.cache={}
 def ask(self,key,content,max_tokens,choice=False):
  if '/c2/a3/action' in key and FakeBackend.stop_once:
   FakeBackend.stop_once=False;raise RuntimeError('Synthetic interruption')
  out='0' if choice else 'A short neutral response.'
  r=dict(output=out,finish_reason='stop');self.cache[key]=r;return r
 def close(self):pass
class ExecutionTests(unittest.TestCase):
 def test_checkpoint_resume_without_duplicate_events(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);shutil.copytree(run.ROOT/'materials',root/'materials');shutil.copy2(run.ROOT/'protocol.json',root/'protocol.json')
   FakeBackend.stop_once=True
   with patch.object(run,'ROOT',root),patch.object(run,'Backend',FakeBackend):
    with self.assertRaisesRegex(RuntimeError,'Synthetic interruption'):run.experiment('SYNTHETIC_TEST_ONLY','pilot',3,time.time()+30)
    run.experiment('SYNTHETIC_TEST_ONLY','pilot',3,time.time()+30)
   s=json.loads((root/'runs/pilot/SYNTHETIC_TEST_ONLY/checkpoint.json').read_text())
   self.assertTrue(s['completed']);self.assertEqual(len(s['events']),30)
   self.assertEqual(len({(x['cycle'],x['agent']) for x in s['events']}),30)
   self.assertEqual(s['next_cycle'],4)
   self.assertTrue(all(x['cycle']>=1 for x in s['exposures']))
 def test_phrase_matching_and_apostrophes(self):
  terms=[dict(id=0,word='chef’s kiss'),dict(id=1,word='alpha')]
  self.assertEqual(run.terms_in("Chef's   kiss! ALPHA.",terms),[0,1])
  self.assertEqual(run.terms_in('alphabet',terms),[])
if __name__=='__main__':unittest.main()
