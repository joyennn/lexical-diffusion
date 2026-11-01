"""Verify every distributed file using SHA256SUMS; no extraction or inference."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
def main():
    lines=(R/'SHA256SUMS').read_text().splitlines()
    for line in lines:
        expected,rel=line.split('  ',1);p=R/rel;h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        assert h.hexdigest()==expected,rel
    print('Verified',len(lines),'release files; no model calls.')
if __name__=='__main__':main()
