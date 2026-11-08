"""Download the four pinned model conversions only when explicitly invoked."""
from pathlib import Path
import argparse,json
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 from huggingface_hub import snapshot_download
 models=json.loads((Path(__file__).resolve().parents[2]/'materials/models.json').read_text())
 for m in models.values():snapshot_download(repo_id=m['repo'],revision=m['revision'],local_dir=a.output/m['folder'])
if __name__=='__main__':main()
