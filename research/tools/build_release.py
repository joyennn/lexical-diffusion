"""Maintainer packaging tool. Reads original workspace; never runs models or edits observations."""
from pathlib import Path
import gzip,hashlib,io,json,tarfile,shutil,re,os

DEST=Path(__file__).resolve().parents[1]
WORK=DEST.parent
STUDIES=['fresh_study1','study2_mechanisms/exposure50','study2_mechanisms/time200','study2_mechanisms/memory4000','study3_semantics']
MODELS=['llama','qwen','gemma','mistral']
MANIFEST=[];ADAPT=[];ARCHIVES=[]
def sha(data):return hashlib.sha256(data).hexdigest()
def portable(data):return data.replace(str(WORK).encode(),b'${WORKSPACE}')
def copy_file(src,rel):
    data=src.read_bytes();clean=portable(data)
    if rel.endswith('study2_mechanisms/time200/lineage.json'):
        d=json.loads(clean);d['baseline_root']='../../fresh_study1'
        for m,v in d['models'].items():v['source_checkpoint']=f'../../fresh_study1/runs/main/{m}/checkpoint.json'
        clean=json.dumps(d,ensure_ascii=False,indent=2).encode()
    if rel.endswith('study2_mechanisms/memory4000/provenance.json'):
        d=json.loads(clean);d['baseline_root']='../../fresh_study1';clean=json.dumps(d,ensure_ascii=False,indent=2).encode()
    out=DEST/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(clean)
    if data!=clean:ADAPT.append(dict(path=rel,kind='metadata_path_portability',original_sha256=sha(data),release_sha256=sha(clean),scientific_content_changed=False))
    MANIFEST.append(dict(path=rel,bytes=len(clean),sha256=sha(clean),original_sha256=sha(data)))

def archive(files,name,category):
    files=sorted(files);out=DEST/'data'/f'{name}.tar.gz';out.parent.mkdir(exist_ok=True)
    members=[]
    with out.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=6,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as tar:
        for p in files:
            data=p.read_bytes();rel=p.relative_to(WORK).as_posix()
            # Prompt texts, checkpoints and responses must remain byte-identical.
            assert b'/Users/' not in data, f'Unreviewed host path in raw data: {rel}'
            info=tarfile.TarInfo(rel);info.size=len(data);info.mtime=0;info.mode=0o644
            tar.addfile(info,io.BytesIO(data));members.append(dict(path=rel,bytes=len(data),sha256=sha(data)))
    assert out.stat().st_size<95*1024**2, f'Archive exceeds release file limit: {out.name}'
    ARCHIVES.append(dict(path=out.relative_to(DEST).as_posix(),bytes=out.stat().st_size,sha256=sha(out.read_bytes()),category=category,members=members))
    print(name,len(files),round(out.stat().st_size/1024**2,2),'MiB',flush=True)

def main():
    for study in STUDIES:
        source=WORK/study
        names={'protocol.json','models.json','freeze.json','pilot_gate.json','provenance.json','lineage.json','preflight_context.json','requirements.txt','environment-lock.txt'}
        for p in sorted(source.iterdir()):
            if p.is_file() and (p.suffix=='.py' or p.name in names):copy_file(p,'source/'+study+'/'+p.name)
        for sub in ['materials','analysis','amendments']:
            if not (source/sub).exists():continue
            for p in sorted((source/sub).rglob('*')):
                if not p.is_file() or any(v in p.parts for v in ['__pycache__','runs']):continue
                if p.suffix not in ['.json','.csv','.tsv','.py','.before']:continue
                if p.name in ['controller.json','progress.json','status.json']:continue
                copy_file(p,'source/'+p.relative_to(WORK).as_posix())
        for stage in ['pilot','main']:
            for model in MODELS:
                f=source/'runs'/stage/model
                if f.exists():archive([p for p in f.rglob('*') if p.is_file() and p.suffix in ['.json','.jsonl','.csv']],study.replace('/','_')+'_'+stage+'_'+model,'retained_main' if stage=='main' else 'technical_pilot_excluded')
        if (source/'origin').exists():
            archive([p for p in (source/'origin').rglob('*') if p.is_file()],study.replace('/','_')+'_origin','baseline_history_not_new_inference')
        excluded=source/'amendments/001_definition_option_cues/runs'
        if excluded.exists():archive([p for p in excluded.rglob('*') if p.is_file() and p.suffix=='.jsonl'],'study3_excluded_pre_amendment','excluded_do_not_pool')
    # Required by the exposure independent audit; planning outcomes are not new observations.
    p=WORK/'study2_mechanisms/exposure_planning/baseline_exposure_summary.json'
    copy_file(p,'source/'+p.relative_to(WORK).as_posix())
    for study in STUDIES:
        root=DEST/'source'/study;f=root/'freeze.json';original=json.loads(f.read_text());adjusted=json.loads(f.read_text());changed=False
        for name,h in original['files'].items():
            rel='source/'+study+'/'+name
            modification=next((x for x in ADAPT if x['path']==rel),None)
            if modification:
                assert h==modification['original_sha256'];adjusted['files'][name]=modification['release_sha256'];changed=True
        if changed:
            history=root/'provenance_release/historical_freeze.json';history.parent.mkdir(exist_ok=True);history.write_bytes(f.read_bytes())
            adjusted['release_note']='Only host-path metadata hashes updated for portable release; historical freeze preserved in provenance_release. This is not a new prospective experiment freeze.'
            f.write_text(json.dumps(adjusted,ensure_ascii=False,indent=2))
    (DEST/'data/archives.json').write_text(json.dumps(ARCHIVES,indent=2))
    (DEST/'RELEASE_ADAPTATIONS.json').write_text(json.dumps(dict(changes=ADAPT,scientific_rules_and_raw_data_unchanged=True),indent=2))
    # Recompute final file hashes after explicit freeze adaptations.
    final=[]
    for p in sorted((DEST/'source').rglob('*')):
        if p.is_file():final.append(dict(path=p.relative_to(DEST).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes())))
    (DEST/'data/source_files.json').write_text(json.dumps(final,indent=2))
    print('PACKAGED',len(final),'source/material/result files;',len(ARCHIVES),'raw archives;',round(sum(x['bytes'] for x in ARCHIVES)/1024**2,2),'MiB',flush=True)
if __name__=='__main__':main()
