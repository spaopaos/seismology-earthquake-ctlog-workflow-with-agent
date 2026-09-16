"""Knowledge routing, citations, integrity and actual driver checkpoints."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'contracts'))
from knowledge_access import Knowledge, sha

class WikiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='wiki-package-copy-')
        cls.package=Path(cls.temp.name)/'package'
        shutil.copytree(ROOT,cls.package,ignore=shutil.ignore_patterns('__pycache__','*.pyc',
                        'runtime', 'runtime_archives', 'test_raw', '.git', '.cache', 'runs'))
        cls.k=Knowledge(cls.package)
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def setUp(self):
        self.work=tempfile.TemporaryDirectory(prefix='wiki-run-'); self.run=Path(self.work.name)
    def tearDown(self): self.work.cleanup()
    def test_copied_snapshot_and_links(self):
        self.assertEqual(self.k.verify()['wiki_pages'],32)
        self.assertEqual(self.k.verify()['wiki_sources'],8)
        self.assertFalse((self.package/'knowledge/library/.llm-wiki').exists())
    def test_chinese_query_and_stage_filter(self):
        hits=self.k.search('阻尼 条件数','relocation')['results']
        self.assertTrue(any(p['id']=='waldhauser-2001-hypodd' for p in hits))
        self.assertEqual(self.k.search('AutoBA','association')['results'],[])
        self.assertTrue(any(p['id']=='autoba' for p in self.k.search('AutoBA')['results']))
    def test_manual_page_and_bounds(self):
        page=self.k.source_page('waldhauser-2001-hypodd',9)
        self.assertIn('condition',page['text'].lower())
        self.assertEqual(page['pdf_page'],9)
        self.assertIn('text',self.k.source_page('klein-2014-hypoinverse140',1))
        with self.assertRaises(ValueError): self.k.source_page('klein-2014-hypoinverse140',149)
    def test_old_manual_is_not_execution_authority(self):
        route=self.k.stage('location')
        self.assertIn('historical',route['scope_note'])
        self.assertTrue(any(e['role']=='version_matched_manual' and 'hyp1.40.pdf' in e['path'] for e in route['runtime_evidence']))
    def test_page_tamper_is_rejected(self):
        path=self.package/'knowledge/library/wiki/entities/gamma.md'; old=path.read_bytes()
        try:
            path.write_bytes(old+b'\nUnverified replacement claim\n')
            with self.assertRaisesRegex(ValueError,'changed/missing'): self.k.verify()
        finally: path.write_bytes(old)
    def test_available_context_is_not_claimed_reading(self):
        self.k.stage_context(self.run,'association',{'dbscan_eps_choice':None})
        context=json.loads((self.run/'knowledge/context-association.json').read_text())
        self.assertEqual(context['status'],'AVAILABLE_CONTEXT')
        self.assertEqual(context['reading_status'],'NOT_ATTESTED')
        self.assertFalse((self.run/'knowledge-access.jsonl').exists())
    def test_changed_lock_and_legacy_run_are_rejected(self):
        self.k.bind_run(self.run)
        path=self.run/'knowledge.lock.json'; lock=json.loads(path.read_text()); lock['knowledge_id']='other'
        path.write_text(json.dumps(lock))
        with self.assertRaisesRegex(ValueError,'different knowledge'): self.k.bind_run(self.run)
        path.unlink(); (self.run/'run_state.json').write_text(json.dumps({'steps':{'old_step':{'status':'PASS'}}}))
        with self.assertRaisesRegex(ValueError,'pre-Wiki'): self.k.log_access(self.run,'association','read',{'item_id':'gamma'})
    def test_cli_citation_records_actual_configuration(self):
        config={'association':{'dbscan_eps_choice':'default'}}
        (self.run/'pipeline.json').write_text(json.dumps(config))
        command=[sys.executable,'-B',str(self.package/'seisflow.py'),'knowledge','cite','--id','gamma',
                 '--stage','association','--run-dir',str(self.run),'--parameter','association.dbscan_eps_choice',
                 '--rationale','Synthetic test decision; not a scientific recommendation.']
        result=subprocess.run(command,cwd=self.package,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        record=json.loads((self.run/'knowledge-access.jsonl').read_text())
        self.assertEqual(record['configured_value'],'default')
        self.assertEqual(record['configuration_sha256'],sha(self.run/'pipeline.json'))
        self.assertEqual(record['page_sha256'],self.k.pages['gamma']['sha256'])
    def test_driver_provides_context_before_scientific_step(self):
        spec=importlib.util.spec_from_file_location('wiki_seisflow',ROOT/'seisflow.py')
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        config=json.loads((ROOT/'configs/pipeline.example.json').read_text())
        (self.run/'pipeline.json').write_text(json.dumps(config))
        runner=mod.Runner(self.run/'pipeline.json')
        def checkpoint(*args,**kwargs):
            self.assertTrue((self.run/'knowledge.lock.json').is_file())
            self.assertTrue((self.run/'knowledge/context-preprocess.json').is_file())
            raise ValueError('Test stop before scientific execution')
        with patch.object(runner,'step',side_effect=checkpoint):
            with self.assertRaisesRegex(ValueError,'Test stop'): runner.run_stage('preprocess')
        self.assertIn('knowledge',json.loads((self.run/'run_state.json').read_text()))
    def test_post_mess_is_last_and_routes_to_joint_runner(self):
        spec=importlib.util.spec_from_file_location('joint_seisflow',ROOT/'seisflow.py')
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.assertEqual(mod.STAGES[-2:], ['detection', 'post_detection_relocation'])
        config=json.loads((ROOT/'configs/pipeline.example.json').read_text())
        (self.run/'pipeline.json').write_text(json.dumps(config))
        runner=mod.Runner(self.run/'pipeline.json')
        called=[]
        def checkpoint(stage,name,script,args,expected=()):
            called.append((stage,name,str(script)))
            if name=='run_stage':
                self.assertTrue((self.run/'knowledge/context-post_detection_relocation.json').is_file())
                self.assertTrue(str(script).endswith('seismic-post-detection-relocation/scripts/run_stage.py'))
                raise ValueError('Joint execution boundary')
        with patch.object(runner,'step',side_effect=checkpoint):
            with self.assertRaisesRegex(ValueError,'Joint execution boundary'):
                runner.run_stage('post_detection_relocation')
        self.assertEqual([item[1] for item in called], ['prepare_region', 'run_stage'])

if __name__=='__main__': unittest.main()
