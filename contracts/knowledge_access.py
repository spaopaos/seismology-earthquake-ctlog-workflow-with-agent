"""Portable, source-linked Wiki access and honest per-run knowledge provenance (stdlib only)."""
import argparse
import copy
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def write(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.pending')
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n'); tmp.replace(path)

class Knowledge:
    def __init__(self,root=ROOT):
        self.root=Path(root).resolve()
        self.base=self.root/'knowledge'
        self.library=self.base/'library'
        self.manifest_path=self.base/'knowledge-manifest.json'
        self.manifest=json.loads(self.manifest_path.read_text())
        self.routes=json.loads((self.base/'stage-routes.json').read_text())
        self.pages=json.loads((self.library/'pages.json').read_text())
        self.corpus=json.loads((self.library/'corpus-manifest.json').read_text())
        self.sources={i['id']:{**i,'path_base':'knowledge/library'} for i in self.corpus['sources']}
        self.sources.update(self.routes.get('runtime_sources',{}))
    def path(self,value):
        if Path(value).is_absolute(): raise ValueError('Knowledge paths must be package-relative')
        p=(self.root/value).resolve(); p.relative_to(self.root)
        return p
    def lock(self):
        return {'format_version':'1.0','knowledge_id':self.manifest['knowledge_id'],
                'manifest_sha256':sha(self.manifest_path),'execution_identity':self.manifest['execution_identity'],
                'provenance_scope':'Available versioned evidence; does not assert that an agent read or understood it.'}
    def verify(self):
        for name,expected in self.manifest['files'].items():
            p=self.path(name)
            if not p.is_file() or sha(p)!=expected: raise ValueError('Knowledge file changed/missing: '+name)
        tools=json.loads((self.root/'toolchain.json').read_text())
        identity=digest({k:tools[k] for k in ['sources','binaries','weights']})
        if identity!=self.manifest['execution_identity']: raise ValueError('Knowledge binding targets a different toolchain')
        for page in self.pages.values():
            path=self.path('knowledge/library/'+page['path'])
            if sha(path)!=page['sha256']: raise ValueError('Page index digest differs: '+page['id'])
            if any(s not in self.sources for s in page['source_ids']): raise ValueError('Unknown cited source')
            if any(r not in self.pages for r in page['related']): raise ValueError('Broken related-page ID')
        for path in (self.library/'wiki').rglob('*.md'):
            text=path.read_text()
            if '[[' in text: raise ValueError('Unresolved Wiki link: '+str(path))
            for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',text):
                parsed=urlsplit(target)
                if parsed.scheme or not parsed.path: continue
                dest=(path.parent/unquote(parsed.path)).resolve(); dest.relative_to(self.root)
                if not dest.is_file(): raise ValueError('Broken exported link: '+target)
                if parsed.fragment.startswith('page='):
                    page=int(parsed.fragment[5:])
                    source=next((s for s in self.sources.values() if self.path(s['path_base']+'/'+s['source_path'])==dest),None)
                    if source is None or not 1<=page<=source['pdf_pages']: raise ValueError('Invalid PDF page locator')
        for stage,route in self.routes['stages'].items():
            if any(p not in self.pages for p in route['wiki_pages']): raise ValueError('Broken stage route: '+stage)
            for evidence in route['runtime_evidence']:
                if not self.path(evidence['path']).is_file(): raise ValueError('Missing runtime evidence: '+evidence['path'])
        return {'status':'PASS','knowledge_id':self.manifest['knowledge_id'],'wiki_pages':len(self.pages),
                'wiki_sources':len(self.corpus['sources']),'runtime_sources':len(self.sources)-len(self.corpus['sources']),
                'scope':'Content identity, links, source/page locators and documented toolchain binding; scientific fact accuracy not established.'}
    def stage(self,name):
        route=copy.deepcopy(self.routes['stages'][name])
        route['wiki_pages']=[{'id':i,'path':'knowledge/library/'+self.pages[i]['path'],
                              'title':self.pages[i]['title'],'role':'background'} for i in route['wiki_pages']]
        return {'stage':name,**route,'knowledge':self.lock()}
    def search(self,query,stage=None,limit=5):
        if not query.strip() or not 1<=limit<=50: raise ValueError('Provide query and limit between 1 and 50')
        aliases=self.routes.get('query_aliases',{})
        expanded=query.lower()+' '+' '.join(v for k,v in aliases.items() if k in query)
        terms=set(re.findall(r'[a-z0-9_]+',expanded))
        ids=set(self.routes['stages'][stage]['wiki_pages']) if stage else set(self.pages)
        hits=[]
        for i in ids:
            page=self.pages[i]; path=self.path('knowledge/library/'+page['path']); text=path.read_text()
            lower=text.lower(); title=page['title'].lower()
            score=sum(5*title.count(t)+min(lower.count(t),10) for t in terms)
            if score:
                positions=[lower.find(t) for t in terms if t in lower]
                pos=min(positions) if positions else 0
                # Favor visible prose instead of frontmatter in search snippets.
                body=text.split('---',2)[-1] if text.startswith('---\n') else text
                hits.append({'id':i,'title':page['title'],'path':'knowledge/library/'+page['path'],
                             'score':score,'excerpt':body.strip()[:650],'source_ids':page['source_ids'],
                             'evidence_scope':page['evidence_scope']})
        result={'query':query,'stage':stage,'results':sorted(hits,key=lambda h:(-h['score'],h['id']))[:limit]}
        if stage: result['execution_binding']=self.stage(stage)
        return result
    def read(self,page):
        p=self.pages[page]
        return {'id':page,'title':p['title'],'path':'knowledge/library/'+p['path'],'sha256':p['sha256'],
                'sources':[self.sources[s] for s in p['source_ids']],
                'evidence_scope':p['evidence_scope'],'content':self.path('knowledge/library/'+p['path']).read_text()}
    def source_page(self,source_id,page):
        s=self.sources[source_id]
        if not 1<=page<=s['pdf_pages']: raise ValueError('PDF page is outside the source')
        result={'source_id':source_id,'pdf_path':s['path_base']+'/'+s['source_path'],
                'pdf_page':page,'pdf_sha256':s['sha256'],'citation_convention':'physical PDF page, starting at 1'}
        if s.get('text_path'):
            text=self.path(s['path_base']+'/'+s['text_path']).read_text()
            match=re.search(r'(?ms)^## PDF page '+str(page)+r'\s*\n(.*?)(?=^## PDF page \d+\s*$|\Z)',text)
            if not match: raise ValueError('Page-numbered extraction is missing this page')
            result['text']=match.group(1).strip()
            result['note']='Figures/tables/formulas may require checking the original PDF.'
        return result
    def bind_run(self,run,existing_steps=False):
        run=Path(run).resolve(); path=run/'knowledge.lock.json'; expected=self.lock()
        state=run/'run_state.json'
        if state.is_file(): existing_steps=existing_steps or bool(json.loads(state.read_text()).get('steps'))
        if path.exists():
            if json.loads(path.read_text())!=expected: raise ValueError('Run uses a different knowledge snapshot; use its original release or a new run')
        else:
            if existing_steps: raise ValueError('Existing pre-Wiki run has no knowledge provenance; start a new run instead of retroactively assigning citations')
            run.mkdir(parents=True,exist_ok=True); write(path,expected)
        return expected
    def stage_context(self,run,stage,settings,existing_steps=False):
        self.verify(); lock=self.bind_run(run,existing_steps)
        payload={'status':'AVAILABLE_CONTEXT','stage':stage,'knowledge':lock,'binding':self.stage(stage),
                 'configured_stage_settings':settings,'reading_status':'NOT_ATTESTED'}
        write(Path(run)/'knowledge'/('context-'+stage+'.json'),payload)
        return lock
    def log_access(self,run,stage,kind,item):
        self.bind_run(run)
        import fcntl
        path=Path(run)/'knowledge-access.jsonl'
        with path.open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX)
            row={'timestamp':datetime.now(timezone.utc).isoformat(),'stage':stage,'operation':kind,
                 'knowledge':self.lock(),**item}
            stream.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')

def add_cli(parser):
    parser.add_argument('operation',choices=['verify','stage','search','read','source','cite'])
    parser.add_argument('--stage',choices=['preprocess','picking','association','location','relocation','detection','post_detection_relocation'])
    parser.add_argument('--query'); parser.add_argument('--id'); parser.add_argument('--page',type=int)
    parser.add_argument('--limit',type=int,default=5); parser.add_argument('--run-dir')
    parser.add_argument('--parameter'); parser.add_argument('--rationale')

def cli(args):
    k=Knowledge(); report=k.verify()
    if args.operation=='verify': result=report
    elif args.operation=='stage':
        if not args.stage: raise ValueError('--stage required')
        result=k.stage(args.stage)
    elif args.operation=='search': result=k.search(args.query or '',args.stage,args.limit)
    elif args.operation=='read': result=k.read(args.id)
    elif args.operation=='source': result=k.source_page(args.id,args.page or 0)
    else:
        if not all([args.run_dir,args.stage,args.id,args.parameter,args.rationale]): raise ValueError('cite requires --run-dir --stage --id --parameter --rationale')
        if args.id not in k.routes['stages'][args.stage]['wiki_pages']: raise ValueError('Cited Wiki page is not in this stage route')
        config_path=Path(args.run_dir)/'pipeline.json'; config=json.loads(config_path.read_text()); value=config
        if args.parameter.split('.')[0]!=args.stage: raise ValueError('Parameter must belong to the selected stage')
        for part in args.parameter.split('.'): value=value[part]
        result={'page_id':args.id,'page_sha256':k.pages[args.id]['sha256'],'source_ids':k.pages[args.id]['source_ids'],
                'parameter':args.parameter,'configured_value':value,'configuration_sha256':sha(config_path),
                'rationale':args.rationale,'assertion_scope':'Agent-supplied explanation of configured value; actual scientific execution recorded separately.'}
    if args.run_dir and args.operation in ['read','source','cite']:
        if not args.stage: raise ValueError('--stage required for run access records')
        item={'item_id':args.id,'status':'RETURNED_TO_CALLER'} if args.operation!='cite' else result
        if args.operation=='source': item['pdf_page']=args.page
        k.log_access(args.run_dir,args.stage,args.operation,item)
    print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
    return 0
