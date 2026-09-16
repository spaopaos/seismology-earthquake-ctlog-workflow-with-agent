#!/usr/bin/env python3
"""Build a source archive, runtime-assets archive and complete offline tar from this release."""
import argparse
import hashlib
import json
import tarfile
import sys
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RELEASE=json.loads((ROOT/'toolchain.json').read_text())['release']
NAME='seismology-agent-'+RELEASE

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()

def asset(path):
    p=path.relative_to(ROOT)
    return p.parts[0]=='bin' or p.parts[:2]==('assets','weights')

def files():
    excluded={'__pycache__','.git','.pytest_cache','runtime','runtime_archives','.cache','test_raw','runs'}
    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in excluded)
        for name in sorted(names):
            if name.endswith('.pyc') or name=='runtime.local.json': continue
            path=Path(directory)/name
            if path.is_file(): yield path

def metadata(member):
    member.uid=member.gid=0
    member.uname=member.gname=''
    member.mtime=0
    return member

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True)
    ap.add_argument('--runtime-archives',required=True)
    args=ap.parse_args()
    sys.path.insert(0,str(ROOT/'contracts'))
    from knowledge_access import Knowledge
    Knowledge().verify()
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    runtime=Path(args.runtime_archives).resolve()
    runtime_manifest=json.loads((runtime/'runtime-manifest.json').read_text())
    for item in runtime_manifest['environments'].values():
        if sha(runtime/item['archive'])!=item['sha256']: raise ValueError('Runtime checksum mismatch')
    manifest={'release':RELEASE,'platform':'linux-x86_64','files':{}}
    for p in files():
        if p.name=='release_manifest.json': continue
        manifest['files'][str(p.relative_to(ROOT))]={'sha256':sha(p),'category':'runtime_asset' if asset(p) else 'source'}
    (ROOT/'release_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    paths=list(files())
    outputs={}
    for category,suffix in [('source','source.tar.gz'),('runtime_asset','assets-linux-x86_64.tar.gz')]:
        target=out/(NAME+'-'+suffix)
        if target.exists(): raise ValueError('Release archive already exists: '+str(target))
        with tarfile.open(target,'w:gz',compresslevel=6) as archive:
            for path in paths:
                if (asset(path)) != (category=='runtime_asset'): continue
                archive.add(path,arcname=NAME+'/'+str(path.relative_to(ROOT)),recursive=False,filter=metadata)
        outputs[target.name]={'sha256':sha(target),'bytes':target.stat().st_size}
        print('Built '+target.name,flush=True)
    upgrade=out/(NAME+'-upgrade.tar.gz')
    if upgrade.exists(): raise ValueError('Upgrade archive already exists')
    with tarfile.open(upgrade,'w:gz',compresslevel=6) as archive:
        for path in paths:
            archive.add(path,arcname=NAME+'/'+str(path.relative_to(ROOT)),recursive=False,filter=metadata)
    outputs[upgrade.name]={'sha256':sha(upgrade),'bytes':upgrade.stat().st_size}
    print('Built '+upgrade.name,flush=True)
    target=out/(NAME+'-linux-x86_64-offline.tar')
    if target.exists(): raise ValueError('Offline archive already exists')
    with tarfile.open(target,'w') as archive:
        for path in paths:
            archive.add(path,arcname=NAME+'/'+str(path.relative_to(ROOT)),recursive=False,filter=metadata)
        for path in [runtime/'runtime-manifest.json']+[runtime/r['archive'] for r in runtime_manifest['environments'].values()]:
            archive.add(path,arcname=NAME+'/runtime_archives/'+path.name,recursive=False,filter=metadata)
    outputs[target.name]={'sha256':sha(target),'bytes':target.stat().st_size}
    (out/'SHA256SUMS').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in outputs.items()))
    (out/'distribution.json').write_text(json.dumps(outputs,indent=2)+'\n')
    print(json.dumps(outputs,indent=2))

if __name__=='__main__': main()
