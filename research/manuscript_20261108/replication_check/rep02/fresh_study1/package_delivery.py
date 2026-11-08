"""Package the reviewed fresh Study 1 without weights, transient files or old results."""
from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'output'
def include(p,kind):
 r=p.relative_to(ROOT);parts=r.parts
 if any(x in parts for x in ['__pycache__','.venv','models','.cache']):return False
 if p.suffix in ['.safetensors','.pyc','.aux','.log','.fls','.fdb_latexmk','.blg','.bbl','.synctex','.lock']:return False
 if parts[0]=='qa' and p.suffix!='.json':return False
 if parts[0]=='manuscript' and (p.name.endswith('.synctex.gz') or p.name=='main.out'):return False
 if len(parts)==1 and p.name not in ['README.md','requirements.txt','environment-lock.txt','.gitignore','protocol.json','models.json','freeze.json','status.json','progress.json','deliverables.json','report_ready.json','읽어주세요.txt'] and p.suffix!='.py':return False
 if kind=='code':return parts[0] not in ['runs','analysis','qa'] and p.name not in ['status.json','progress.json','report_ready.json','deliverables.json']
 if kind=='data':return parts[0] in ['runs','analysis','materials','amendments','qa'] or p.name in ['protocol.json','models.json','freeze.json']
 return True

def main():
 OUT.mkdir(exist_ok=True)
 for kind,name in [('code','fresh_study1_code.zip'),('data','fresh_study1_data.zip'),('combined','fresh_study1_code_and_data.zip')]:
  dest=OUT/name
  with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(ROOT.rglob('*')):
    if p.is_file() and include(p,kind):z.write(p,'fresh_study1/'+str(p.relative_to(ROOT)))
  with zipfile.ZipFile(dest) as z:
   assert z.testzip() is None
   if kind!='data':assert z.read('fresh_study1/manuscript/main.pdf')==(ROOT/'manuscript/main.pdf').read_bytes()
   if kind!='code':
    for m in ['llama','qwen','gemma','mistral']:assert f'fresh_study1/runs/main/{m}/calls.jsonl' in z.namelist()
  print(name,round(dest.stat().st_size/1024/1024,2),'MiB; archive integrity PASS')
 manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.glob('fresh_study1_*') if p.suffix in ['.pdf','.zip']}
 (OUT/'fresh_study1_manifest.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
