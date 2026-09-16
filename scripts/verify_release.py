#!/usr/bin/env python3
"""Verify release file contents; runtime archives have a separate manifest."""
import argparse
import hashlib
import json
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-only',action='store_true')
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((root/'release_manifest.json').read_text())
    failures=[]; checked=0
    for name,record in manifest['files'].items():
        if args.source_only and record['category']=='runtime_asset': continue
        path=root/name
        if not path.is_file() or digest(path)!=record['sha256']: failures.append(name)
        checked+=1
    print(json.dumps({'status':'FAIL' if failures else 'PASS','checked_files':checked,'failures':failures},indent=2))
    return 1 if failures else 0

if __name__=='__main__': raise SystemExit(main())
