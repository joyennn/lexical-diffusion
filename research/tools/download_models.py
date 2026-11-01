"""Explicit download of the four pinned conversions; requires huggingface-hub and model access."""
from pathlib import Path
import argparse,json
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
    from huggingface_hub import snapshot_download
    models=json.loads((Path(__file__).resolve().parents[1]/'source/fresh_study1/models.json').read_text())
    for name,m in models.items():
        print('Downloading pinned model',name,m['revision'],flush=True)
        snapshot_download(repo_id=m['repo'],revision=m['revision'],local_dir=a.destination/m['folder'])
if __name__=='__main__':main()
