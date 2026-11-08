"""Temporary synthetic tests; no fake observations enter real experiment folders."""
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
import copy,hashlib,io,json,shutil,tempfile,time,unittest
import run_study1 as run
from analyze import window_metrics
class FakeBackend:
 interrupt=False
 def __init__(self,name,out,deadline):
  self.out=out;out.mkdir(parents=True,exist_ok=True);self.log=out/'calls.jsonl';self.cache={}
  if self.log.exists():
   for line in self.log.read_text().splitlines():r=json.loads(line);self.cache[r['key']]=r
 def ask(self,key,content,max_tokens,choice=False):
  request=dict(content=content,max_tokens=max_tokens,choice=choice);h=run.digest(request)
  if key in self.cache:
   assert self.cache[key]['request_hash']==h;return self.cache[key]
  if self.interrupt and '/c5/a3/action' in key:FakeBackend.interrupt=False;raise RuntimeError('Synthetic interruption')
  output='0' if choice else 'A short neutral update.'
  row=dict(key=key,request_hash=h,request=request,output=output,finish_reason='stop',status='completed')
  with self.log.open('a') as f:f.write(json.dumps(row)+'\n')
  self.cache[key]=row;return row
 def close(self):pass
class ContinuationTests(unittest.TestCase):
 def test_runner_byte_identical_to_baseline(self):
  meta=json.loads((run.ROOT/'lineage.json').read_text());self.assertEqual(hashlib.sha256((run.ROOT/'run_study1.py').read_bytes()).hexdigest(),meta['runner_sha256'])
 def test_prepared_origin_only_changes_endpoint_flags(self):
  lineage=json.loads((run.ROOT/'lineage.json').read_text())
  for m in lineage['models']:
   original=run.read(run.ROOT/'origin'/m/'checkpoint_100.json');state=run.read(run.ROOT/'runs/main'/m/'checkpoint.json')
   if state['next_cycle']==101 and state['next_agent']==0:
    self.assertEqual(dict(state,target_cycles=100,completed=True),original)
   else:self.assertEqual(state['events'][:1000],original['events'])
 def test_continuation_and_interruption_equal_uninterrupted_run(self):
  with tempfile.TemporaryDirectory() as tmp:
   roots={n:Path(tmp)/n for n in ['base','extended','reference']}
   for r in roots.values():
    r.mkdir();shutil.copytree(run.ROOT/'materials',r/'materials');shutil.copy2(run.ROOT/'protocol.json',r/'protocol.json')
   def execute(r,cycles):
    with patch.object(run,'ROOT',r),patch.object(run,'Backend',FakeBackend),redirect_stdout(io.StringIO()):run.experiment('SYNTHETIC_TEST_ONLY','main',cycles,time.time()+90)
   FakeBackend.interrupt=False;execute(roots['base'],3)
   rel=Path('runs/main/SYNTHETIC_TEST_ONLY');shutil.copytree(roots['base']/rel,roots['extended']/rel)
   original_bytes=(roots['base']/rel/'checkpoint.json').read_bytes();prefix=(roots['base']/rel/'calls.jsonl').read_bytes()
   state=run.read(roots['extended']/rel/'checkpoint.json');state.update(target_cycles=6,completed=False);run.put(roots['extended']/rel/'checkpoint.json',state);(roots['extended']/rel/'completed.json').unlink()
   FakeBackend.interrupt=True
   with self.assertRaisesRegex(RuntimeError,'Synthetic interruption'):execute(roots['extended'],6)
   execute(roots['extended'],6);execute(roots['reference'],6)
   self.assertEqual(run.read(roots['extended']/rel/'checkpoint.json'),run.read(roots['reference']/rel/'checkpoint.json'))
   self.assertEqual((roots['base']/rel/'checkpoint.json').read_bytes(),original_bytes)
   self.assertTrue((roots['extended']/rel/'calls.jsonl').read_bytes().startswith(prefix))
   rows=[json.loads(x) for x in (roots['extended']/rel/'calls.jsonl').read_text().splitlines()];self.assertEqual(len(rows),len({x['key'] for x in rows}))
 def test_more_cumulative_use_can_have_lower_rate(self):
  ms=[dict(agent=1,cycle=1,text='alpha',counts={0:1}),dict(agent=1,cycle=101,text='alpha',counts={0:1}),dict(agent=1,cycle=102,text='neutral',counts={0:0})]
  for m in ms:m['counts']={w:m['counts'].get(w,0) for w in range(60)}
  uses={(1,0):(1,1)};ex={(1,0):(1,1)}
  a=window_metrics(ms,uses,ex,[1],1,100);b=window_metrics(ms,uses,ex,[1],101,200)
  self.assertEqual(a['occurrences_per100messages'],100);self.assertEqual(b['occurrences_per100messages'],50);self.assertEqual(b['repeat_occurrences'],1);self.assertEqual(b['new_first_user_word_pairs'],0)
if __name__=='__main__':unittest.main()
