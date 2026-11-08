"""Create an isolated fresh run; never overwrite or reuse supplied outcomes."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,json,shutil
ROOT=Path(__file__).resolve().parent
def create(destination,seed):
 destination=Path(destination).resolve();old=json.loads((ROOT/'protocol.json').read_text())
 if destination.exists():raise ValueError('Destination must not exist; existing data are never overwritten.')
 if seed==old['main_seed']:raise ValueError('Use a new seed for a new replication.')
 destination.mkdir(parents=True)
 for f in ROOT.iterdir():
  if f.is_file() and (f.suffix=='.py' or f.name in ['README.md','requirements.txt','environment-lock.txt','.gitignore','models.json']):shutil.copy2(f,destination/f.name)
 shutil.copytree(ROOT/'materials',destination/'materials')
 shutil.copytree(ROOT/'manuscript',destination/'manuscript',ignore=shutil.ignore_patterns('figures','main.tex','*.pdf','*.aux','*.log','*.fls','*.fdb_latexmk','*.bbl','*.blg'))
 old.update(main_seed=seed,pilot_seed=seed+990,created_at=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),replication_of='fresh-1.0; new seed and no copied observations')
 (destination/'protocol.json').write_text(json.dumps(old,ensure_ascii=False,indent=2))
 assert not (destination/'runs').exists() and not (destination/'analysis').exists()
 print('Created isolated fresh-run folder:',destination)
 return destination
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--destination',required=True);p.add_argument('--seed',required=True,type=int);a=p.parse_args();create(a.destination,a.seed)
