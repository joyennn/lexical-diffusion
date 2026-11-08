"""Prepare an isolated inference folder; this command never generates model responses."""
from pathlib import Path
import argparse,json,shutil,sys
REPO=Path(__file__).resolve().parents[1]
load=lambda p:json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--condition',choices=['baseline','source_access','memory4000','continuation'],required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=int,default=2026110300)
 p.add_argument('--baseline-dir',type=Path);a=p.parse_args();dest=a.output.resolve()
 if dest==REPO or dest in REPO.parents or (dest.exists() and any(dest.iterdir())):raise ValueError('Choose a new, empty output folder.')
 if a.seed%10:raise ValueError('Use a seed ending in zero to preserve source identity.')
 runner={'baseline':'baseline.py','source_access':'source_access.py','memory4000':'memory4000.py','continuation':'baseline.py'}[a.condition]
 states={}
 if a.condition=='continuation':
  if not a.baseline_dir:raise ValueError('Continuation requires --baseline-dir.')
  for model in ['llama','qwen','gemma','mistral']:
   src=a.baseline_dir/'runs/main'/model;state=load(src/'checkpoint.json')
   assert state['completed'] and state['target_cycles']==100 and state['next_cycle']==101
   assert state['seed']==a.seed,'Seed must match baseline.';states[model]=(src,state)
 (dest/'materials').mkdir(parents=True)
 for src,name in [(REPO/'materials/models.json','models.json'),(REPO/'materials/expressions.json','materials/terms.json'),(REPO/'materials/personas.json','materials/personas.json'),(REPO/'code/runners'/runner,'run.py')]:shutil.copy2(src,dest/name)
 if a.condition=='source_access':shutil.copy2(REPO/'code/runners/feed_policy.py',dest/'feed_policy.py')
 (dest/'protocol.json').write_text(json.dumps({'main_seed':a.seed,'pilot_seed':a.seed+90,'recommendation_probability':.5},indent=2))
 for model,(src,state) in states.items():
  target=dest/'runs/main'/model;target.mkdir(parents=True);origin=dest/'origin'/model;origin.mkdir(parents=True)
  for name in ['checkpoint.json','calls.jsonl']:shutil.copy2(src/name,origin/name)
  shutil.copy2(src/'calls.jsonl',target/'calls.jsonl');state.update(target_cycles=200,completed=False);(target/'checkpoint.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
 cycles=200 if a.condition=='continuation' else 100
 print('Prepared',dest,'— no inference performed.')
 print('Set MODEL_STORE to the downloaded model directory. Then run each model:')
 for model in ['llama','qwen','gemma','mistral']:print(f'{sys.executable} {dest / "run.py"} --model {model} --stage main --cycles {cycles} --hours 96')
if __name__=='__main__':main()
