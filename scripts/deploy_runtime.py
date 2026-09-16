#!/usr/bin/env python3
"""Deploy supplied environment snapshots into an explicitly chosen NEW directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archives',required=True,help='Directory containing runtime-manifest.json and three tar.gz files')
    ap.add_argument('--destination',required=True,help='New environment directory; no existing environments are modified')
    ap.add_argument('--mapping',required=True,help='New runtime.local.json location')
    args=ap.parse_args()
    source=Path(args.archives).resolve()
    destination=Path(args.destination).resolve()
    mapping=Path(args.mapping).resolve()
    if destination.exists() or mapping.exists():
        raise ValueError('Choose a new destination and mapping; deployment never overwrites existing environments')
    manifest=json.loads((source/'runtime-manifest.json').read_text())
    for record in manifest['environments'].values():
        if sha(source/record['archive'])!=record['sha256']: raise ValueError('Runtime archive checksum mismatch: '+record['archive'])
    destination.mkdir(parents=True)
    result={}
    for key,record in manifest['environments'].items():
        target=destination/record['name']
        target.mkdir()
        print('Extracting '+record['name'],flush=True)
        with tarfile.open(source/record['archive']) as archive:
            for member in archive.getmembers():
                p=Path(member.name)
                if p.is_absolute() or '..' in p.parts: raise ValueError('Unsafe archive path')
                if member.ischr() or member.isblk() or member.isfifo(): raise ValueError('Unexpected special file')
            archive.extractall(target)
        python=target/'bin/python'
        env=dict(os.environ,PYTHONNOUSERSITE='1')
        env.pop('PYTHONPATH',None)
        subprocess.run([str(python),str(target/'bin/conda-unpack')],check=True,env=env)
        result[key]=os.path.relpath(python,mapping.parent)
    mapping.parent.mkdir(parents=True,exist_ok=True)
    mapping.write_text(json.dumps(result,indent=2)+'\n')
    print('Created '+str(mapping)+'; run seisflow.py --runtime <mapping> doctor before analysis')

if __name__=='__main__':
    main()
