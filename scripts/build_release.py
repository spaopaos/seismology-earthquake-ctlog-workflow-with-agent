#!/usr/bin/env python3
"""Build a source archive, runtime-assets archive and complete offline tar from this release."""
import argparse

import json
import tarfile
import sys
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RELEASE=json.loads((ROOT/'toolchain.json').read_text())['release']
NAME='seismology-agent-'+RELEASE

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
        if not (runtime/item['archive']).is_file(): raise ValueError('Runtime archive missing: '+item['archive'])
    paths=[p for p in files() if p.name!='release_manifest.json']
    outputs={}
    for category,suffix in [('source','source.tar.gz'),('runtime_asset','assets-linux-x86_64.tar.gz')]:
        target=out/(NAME+'-'+suffix)
        if target.exists(): raise ValueError('Release archive already exists: '+str(target))
        with tarfile.open(target,'w:gz',compresslevel=6) as archive:
            for path in paths:
                if (asset(path)) != (category=='runtime_asset'): continue
                archive.add(path,arcname=NAME+'/'+str(path.relative_to(ROOT)),recursive=False,filter=metadata)
        outputs[target.name]={'bytes':target.stat().st_size}
        print('Built '+target.name,flush=True)
    upgrade=out/(NAME+'-upgrade.tar.gz')
    if upgrade.exists(): raise ValueError('Upgrade archive already exists')
    with tarfile.open(upgrade,'w:gz',compresslevel=6) as archive:
        for path in paths:
            archive.add(path,arcname=NAME+'/'+str(path.relative_to(ROOT)),recursive=False,filter=metadata)
    outputs[upgrade.name]={'bytes':upgrade.stat().st_size}
    print('Built '+upgrade.name,flush=True)
    target=out/(NAME+'-linux-x86_64-offline.tar')
    if target.exists(): raise ValueError('Offline archive already exists')
    with tarfile.open(target,'w') as archive:
        for path in paths:
            archive.add(path,arcname=NAME+'/'+str(path.relative_to(ROOT)),recursive=False,filter=metadata)
        for path in [runtime/'runtime-manifest.json']+[runtime/r['archive'] for r in runtime_manifest['environments'].values()]:
            archive.add(path,arcname=NAME+'/runtime_archives/'+path.name,recursive=False,filter=metadata)
    outputs[target.name]={'bytes':target.stat().st_size}
    (out/'distribution.json').write_text(json.dumps(outputs,indent=2)+'\n')
    print(json.dumps(outputs,indent=2))

if __name__=='__main__': main()
