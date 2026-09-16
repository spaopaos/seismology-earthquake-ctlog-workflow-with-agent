#!/usr/bin/env python3
"""Freeze reviewed knowledge/bindings in a NEW release workspace, then validate the snapshot."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'contracts'))
from knowledge_access import Knowledge, sha, digest

def main():
    base=ROOT/'knowledge'
    routes=json.loads((base/'stage-routes.json').read_text())
    paths=[p for d in ['library','bindings','runtime-sources'] for p in (base/d).rglob('*') if p.is_file()]
    paths += [base/'README.md',base/'stage-routes.json',ROOT/'contracts/knowledge_access.py',ROOT/'seisflow.py',ROOT/'toolchain.json']
    for stage in routes['stages'].values(): paths += [ROOT/item['path'] for item in stage['runtime_evidence']]
    files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))}
    tools=json.loads((ROOT/'toolchain.json').read_text())
    manifest={'format_version':'1.0','knowledge_id':'seismology-wiki-'+digest(files)[:16],
              'package_release':tools['release'],'execution_identity':digest({k:tools[k] for k in ['sources','binaries','weights']}),
              'scientific_fact_review':'NOT_TESTED','files':files}
    (base/'knowledge-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(Knowledge().verify(),indent=2))

if __name__=='__main__': main()
