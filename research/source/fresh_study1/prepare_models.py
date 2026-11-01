"""Pin public model conversions and download missing files; no inference."""
from pathlib import Path
import json,sys,time
from huggingface_hub import HfApi,snapshot_download
ROOT=Path(__file__).resolve().parent
def main():
 models={
 'llama':{'repo':'mlx-community/Meta-Llama-3-8B-Instruct-4bit','revision':'c38b3b1f03cce0ce0ccd235e5c97b0d3d255e651','folder':'Meta-Llama-3-8B-Instruct-4bit'},
 'qwen':{'repo':'mlx-community/Qwen3-8B-4bit','revision':'545dc4251c05440727734bcd94334791f6ab0192','folder':'Qwen3-8B-4bit'},
 'gemma':{'repo':'mlx-community/gemma-2-9b-it-4bit','revision':'ff12eb39da2cd9b3b0f4b4f9ffb274603f05bb29','folder':'gemma-2-9b-it-4bit'},
 'mistral':{'repo':'mlx-community/Mistral-7B-Instruct-v0.3-4bit','revision':'a4b8f870474b0eb527f466a03fbc187830d271f5','folder':'Mistral-7B-Instruct-v0.3-4bit'}}
 (ROOT/'models.json').write_text(json.dumps(models,indent=2))
 store=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'models'
 store.mkdir(exist_ok=True)
 for name,info in models.items():
  target=store/info['folder'];print('Preparing',name,info['revision'],flush=True)
  if name in ['llama','qwen'] and (target/'config.json').exists():continue
  snapshot_download(info['repo'],revision=info['revision'],local_dir=target,max_workers=4,ignore_patterns=['*.md','*.gitattributes'])
  (ROOT/'download_progress.json').write_text(json.dumps({'last_completed':name,'time':time.time()}))
 (ROOT/'models_ready.json').write_text(json.dumps({'ready':True,'model_store':str(store.resolve()),'time':time.time()}))
if __name__=='__main__':main()
