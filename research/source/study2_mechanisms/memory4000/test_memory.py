from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
import hashlib,io,json,shutil,tempfile,time,unittest
import run_study1 as run
class FakeBackend:
 calls=[]
 def __init__(self,name,out,deadline):self.cache={}
 def ask(self,key,content,max_tokens,choice=False):
  self.calls.append(dict(key=key,content=content,max_tokens=max_tokens,choice=choice));text='0' if choice else ('S'*600 if '/summary' in key else 'A neutral update.')
  row=dict(output=text,finish_reason='stop');self.cache[key]=row;return row
 def close(self):pass
class MemoryTests(unittest.TestCase):
 def test_only_threshold_changes_inference_runner(self):
  provenance=run.read(run.ROOT/'provenance.json');baseline=(Path(provenance['baseline_root'])/'run_study1.py').read_text();ours=(run.ROOT/'run_study1.py').read_text()
  self.assertEqual(ours,baseline.replace('if len(before)>1000:','if len(before)>4000:'))
 def test_trigger_and_summary_cap(self):
  for size,expected in [(1001,False),(4000,False),(4001,True)]:
   with self.subTest(size=size),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);shutil.copytree(run.ROOT/'materials',root/'materials');shutil.copy2(run.ROOT/'protocol.json',root/'protocol.json')
    plan=run.read(root/'protocol.json');people=run.read(root/'materials/personas.json')
    state=dict(seed=plan['main_seed'],target_cycles=1,source_agent=0,next_cycle=1,next_agent=9,posts=[],comments=[],events=[],exposures=[],agents=[dict(id=i,persona=people[i],memory='Z'*size if i==9 else '',read_ids=[],stats=dict(write=0,read=0,comment=0)) for i in range(10)],completed=False)
    out=root/'runs/main/SYNTHETIC_TEST_ONLY';run.put(out/'checkpoint.json',state);FakeBackend.calls=[]
    with patch.object(run,'ROOT',root),patch.object(run,'Backend',FakeBackend),redirect_stdout(io.StringIO()):run.experiment('SYNTHETIC_TEST_ONLY','main',1,time.time()+30)
    final=run.read(out/'checkpoint.json');e=final['events'][0];summaries=[x for x in FakeBackend.calls if '/summary' in x['key']]
    self.assertEqual(bool(summaries),expected)
    if expected:
     self.assertEqual(summaries[0]['max_tokens'],100);self.assertIn('at most 500 characters',summaries[0]['content']);self.assertTrue(e['memory_after'].startswith('S'*500));self.assertNotIn('S'*501,e['memory_after'])
    else:self.assertTrue(e['memory_after'].startswith('Z'*size))
if __name__=='__main__':unittest.main()
