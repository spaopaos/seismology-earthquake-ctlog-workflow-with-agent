#!/usr/bin/env python3
"""Record the reviewed knowledge/bindings file list in a NEW release workspace, then check links and routes."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'contracts'))
from knowledge_access import Knowledge

def main():
    base=ROOT/'knowledge'
    routes=json.loads((base/'stage-routes.json').read_text())
    paths=[p for d in ['library','bindings','runtime-sources'] for p in (base/d).rglob('*') if p.is_file()]
    paths += [base/'README.md',base/'stage-routes.json',ROOT/'contracts/knowledge_access.py',ROOT/'seisflow.py',ROOT/'toolchain.json']
    for stage in routes['stages'].values(): paths += [ROOT/item['path'] for item in stage['runtime_evidence']]
    files=sorted(str(p.relative_to(ROOT)) for p in set(paths))
    tools=json.loads((ROOT/'toolchain.json').read_text())
    manifest={'format_version':'1.0',
              'knowledge_id':'seismology-wiki-'+tools['release']+'-'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S'),
              'package_release':tools['release'],
              'scientific_fact_review':'NOT_TESTED','files':files}
    (base/'knowledge-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(Knowledge().verify(),indent=2))

if __name__=='__main__': main()
