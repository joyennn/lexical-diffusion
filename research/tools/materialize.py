"""Verify and unpack a release into a NEW disposable workspace. No inference."""
from pathlib import Path
import argparse,hashlib,json,shutil,tarfile
RELEASE=Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def materialize(destination):
    destination=Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):raise ValueError('Destination must be absent or empty; supplied observations are never overwritten.')
    assert destination!=RELEASE and RELEASE not in destination.parents,'Use a workspace outside the release tree.'
    destination.mkdir(parents=True,exist_ok=True)
    for row in json.loads((RELEASE/'data/source_files.json').read_text()):
        p=RELEASE/row['path'];assert sha(p)==row['sha256'],row['path']
        q=destination/p.relative_to(RELEASE/'source');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    for archive in json.loads((RELEASE/'data/archives.json').read_text()):
        p=RELEASE/archive['path'];assert sha(p)==archive['sha256'],archive['path']
        expected={x['path']:x for x in archive['members']}
        with tarfile.open(p,'r:gz') as tar:
            for member in tar:
                assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
                assert member.name in expected
                q=destination/member.name;q.parent.mkdir(parents=True,exist_ok=True)
                assert not q.exists(),member.name
                with tar.extractfile(member) as src,q.open('wb') as dst:shutil.copyfileobj(src,dst)
                assert q.stat().st_size==expected[member.name]['bytes'] and sha(q)==expected[member.name]['sha256'],member.name
        print('Verified and restored',archive['path'],flush=True)
    (destination/'RELEASE_WORKSPACE.json').write_text(json.dumps({'source_release':str(RELEASE),'raw_data_hashes_verified':True,'inference_performed':False},indent=2))
    return destination
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--destination',required=True);a=p.parse_args();materialize(a.destination)
