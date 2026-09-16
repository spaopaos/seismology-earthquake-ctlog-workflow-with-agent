#!/usr/bin/env python3
"""Export a read-only execution snapshot from an existing LLM Wiki; never modify the live project."""
import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
import yaml

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def contained(root,value):
    p=(root/value).resolve()
    p.relative_to(root.resolve())
    if not p.is_file(): raise ValueError('Missing Wiki file: '+value)
    return p

def export(source,destination):
    source=Path(source).resolve(); destination=Path(destination).resolve()
    if destination.exists(): raise ValueError('Use a new snapshot destination')
    corpus=json.loads((source/'.llm-wiki/corpus-manifest.json').read_text())
    for item in corpus['sources']:
        if sha(contained(source,item['source_path']))!=item['sha256']: raise ValueError('Original PDF hash mismatch: '+item['id'])
        if sha(contained(source,item['text_path']))!=item['text_sha256']: raise ValueError('Source text hash mismatch: '+item['id'])
    original={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
    source_ids={i['filename']:i['id'] for i in corpus['sources']}
    pages={}; all_md={}
    for path in sorted((source/'wiki').rglob('*.md')):
        if path.stem in all_md: raise ValueError('Ambiguous Wiki slug: '+path.stem)
        all_md[path.stem]=path.relative_to(source)
        text=path.read_text()
        if text.startswith('---\n'):
            front=yaml.safe_load(text.split('---',2)[1])
            required={'type','title','sources','related'}
            if not isinstance(front,dict) or required-set(front): raise ValueError('Invalid page metadata: '+str(path))
            pages[path.stem]={'id':path.stem,'title':front['title'],'type':front['type'],
                'path':str(path.relative_to(source)), 'source_ids':[source_ids[n] for n in front['sources']],
                'related':front['related'],'original_sha256':sha(path),
                'evidence_scope':'background_and_source_synthesis; not version-matched execution instructions'}
    destination.mkdir(parents=True)
    for item in corpus['sources']:
        for field in ['source_path','text_path']:
            target=destination/item[field]; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source/item[field],target)
    for slug,relative in all_md.items():
        path=source/relative; text=path.read_text()
        def link(match):
            target,label=(match.group(1).split('|',1)+[None])[:2] if '|' in match.group(1) else (match.group(1),None)
            target,sep,anchor=target.partition('#')
            if target not in all_md: raise ValueError('Broken Wiki link: '+target)
            ref=os.path.relpath(all_md[target],relative.parent).replace(os.sep,'/')
            return '['+(label or target)+']('+ref+('#'+anchor if sep else '')+')'
        text=re.sub(r'\[\[([^\]]+)\]\]',link,text)
        target=destination/relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(text)
        if slug in pages: pages[slug]['sha256']=sha(target)
    for name in ['schema.md','purpose.md']:
        shutil.copyfile(source/name,destination/name)
    write(destination/'corpus-manifest.json',corpus)
    write(destination/'pages.json',pages)
    snapshot={'format_version':'1.0','page_count':len(pages),'source_count':len(corpus['sources']),
        'source_pdf_pages':sum(i['pdf_pages'] for i in corpus['sources']),
        'export_transform':'Wiki links converted to ordinary relative Markdown links; original PDFs/texts unchanged',
        'live_source_identity':hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),
        'original_files':original}
    write(destination/'export.json',snapshot)
    after={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
    if original!=after: raise ValueError('Live Wiki changed during export')
    print(json.dumps({k:snapshot[k] for k in ['page_count','source_count','source_pdf_pages','live_source_identity']}))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--source',required=True); ap.add_argument('--out',required=True)
    args=ap.parse_args(); export(args.source,args.out)
