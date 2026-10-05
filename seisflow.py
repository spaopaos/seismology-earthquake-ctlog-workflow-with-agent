#!/usr/bin/env python3
"""Portable command entry for a researcher or any agent with local command access."""
import argparse
import csv

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'contracts'))
from runtime_support import runtime_path, verify_vendor, digest, native_environment, binary
from pipeline_contracts import load_contract
from knowledge_access import Knowledge, add_cli as add_knowledge_cli, cli as knowledge_cli

STAGES = ['preprocess','picking','association','location','relocation','detection','post_detection_relocation','focal_mechanism']
ENVKEY = {'preprocess':'science_python', 'picking':'science_python','association':'science_python',
          'location':'science_python','relocation':'science_python','detection':'mess_python',
          'post_detection_relocation':'science_python','focal_mechanism':'science_python'}

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.pending')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    tmp.replace(path)

def write_reverse_csv(path, rows):
    """SKHASH polarity-reversal table; start/end times must be timezone-aware
    (e.g. 2025-03-01T00:00:00+00:00) — see the focal-mechanism skill pitfalls."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ['network','station','location','channel','start_time','end_time']
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in keys})

def configure(args):
    values = {k: str(Path(getattr(args,k)).expanduser().resolve()) for k in ['science_python','validator_python','mess_python']}
    if any(not Path(p).is_file() for p in values.values()):
        raise ValueError('All explicitly selected interpreters must exist')
    path = Path(args.out).resolve() if args.out else ROOT / 'runtime.local.json'
    if path.exists() and json.loads(path.read_text()) != values:
        raise ValueError('Runtime mapping exists; use --out for a new mapping')
    write_json(path, values)
    print(path)

def doctor(args):
    checks = []
    def check(name, fn):
        try:
            detail = fn()
            checks.append({'name':name,'status':'PASS','detail':detail})
        except Exception as exc:
            checks.append({'name':name,'status':'FAIL','detail':str(exc)})
    check('platform', lambda: platform.platform() if platform.system() == 'Linux' and platform.machine() == 'x86_64'
          else (_ for _ in ()).throw(ValueError('Release native binaries require Linux x86-64')))
    packages = {'science_python':['numpy','pandas','scipy','obspy','torch','torchvision','sklearn','numba','pyproj','matplotlib'],
                'validator_python':['jsonschema'], 'mess_python':['numpy','pandas','scipy','obspy','torch','numba','matplotlib']}
    for key, names in packages.items():
        def inspect(key=key, names=names):
            python = runtime_path(key)
            if not python or not python.is_file():
                raise ValueError('Configure ' + key + ' or deploy the supplied runtime archives')
            code = 'import importlib,json,sys; names=' + repr(names) + '; print(json.dumps({n:getattr(importlib.import_module(n),"__version__","installed") for n in names}))'
            run = subprocess.run([str(python),'-I','-B','-c',code], capture_output=True, text=True, timeout=120,
                                 env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
            if run.returncode:
                raise ValueError(run.stderr[-2000:])
            return json.loads(run.stdout.splitlines()[-1])
        check(key, inspect)
    check('knowledge_snapshot', lambda: Knowledge().verify())
    tools = json.loads((ROOT / 'toolchain.json').read_text())
    for name, record in tools['sources'].items():
        check('source_' + name, lambda name=name, record=record: verify_vendor(ROOT / record['path'], record['commit']))
    for name, record in tools['binaries'].items():
        def native(name=name, record=record):
            binary = runtime_path(name, str(ROOT / record['path']))
            if digest(binary) != record['sha256']:
                raise ValueError('Binary identity mismatch')
            run = subprocess.run(['ldd',str(binary)],capture_output=True,text=True,env=native_environment())
            if run.returncode or 'not found' in run.stdout:
                raise ValueError(run.stdout + run.stderr)
            return {'sha256':record['sha256'],'dynamic_libraries':run.stdout.splitlines()}
        check('binary_' + name, native)
    weight = tools['weights']['phasenet_plus']
    check('local_weights', lambda: weight['sha256'] if digest(ROOT / weight['path']) == weight['sha256']
          else (_ for _ in ()).throw(ValueError('Checkpoint checksum mismatch')))
    check('schema', lambda: __import__('pipeline_contracts').schema_errors({'stage':'preprocess'}) and 'Draft 2020-12 validation callable')
    report = {'status':'FAIL' if any(c['status']=='FAIL' for c in checks) else 'PASS',
              'checked_at':datetime.now(timezone.utc).isoformat(), 'checks':checks,
              'gpu_validation':'NOT_TESTED', 'scientific_validation':'NOT_TESTED'}
    if args.out: write_json(args.out, report)
    print(json.dumps(report,indent=2))
    return 1 if report['status']=='FAIL' else 0

def init(args):
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    config = work / 'pipeline.json'
    if config.exists():
        raise ValueError('Existing project configuration; choose a new directory')
    example = json.loads((ROOT / 'configs/pipeline.example.json').read_text())
    example['run_id'] = work.name
    write_json(config, example)
    for name in ['raw','input','archive','processing','logs']:
        (work / name).mkdir(exist_ok=True)
    print('Created ' + str(config))
    print('Read AGENTS.md and docs/ARCHIVE_INTERFACE.md. Prepare the current input archive using the preprocessing skill.')

class Runner:
    def __init__(self, config):
        self.path = Path(config).resolve()
        self.base = self.path.parent
        self.config = json.loads(self.path.read_text())
        if self.config.get('config_version') != '1.0':
            raise ValueError('Unsupported pipeline configuration')
        if self.config['resources']['cpu_workers'] < 1:
            raise ValueError('Positive CPU budget required')
        self.archive = (self.base / self.config['archive']).resolve()
        self.inputs = self.base / 'inputs'
        self.stations = self.inputs / 'stations.txt'
        self.vp = self.inputs / 'velocity_p.cre'
        self.vs = self.inputs / 'velocity_s.cre'
        preparation = self.inputs / 'region_preparation.json'
        if preparation.is_file():
            recorded = json.loads(preparation.read_text())['input_sha256']
            current = {'stations':self.base/self.config['stations'], 'velocity_model':self.base/self.config['velocity_model'],
                       'manifest':self.archive/'daily_manifest.csv'}
            if any(digest(path) != recorded[key] for key,path in current.items()):
                raise ValueError('Regional inputs changed after preparation; create a new run')
        self.state_path = self.base / 'run_state.json'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {'run_id':self.config['run_id'],'stages':{},'steps':{}}
        self.logs = self.base / 'logs'
        self.logs.mkdir(exist_ok=True)
    def step(self, stage, name, script, args, expected=()):
        key = stage + '.' + name
        python = runtime_path(ENVKEY[stage])
        if not python or not python.is_file(): raise ValueError('Missing configured interpreter: ' + ENVKEY[stage])
        command = [str(python),'-B',str(script),*map(str,args)]
        signature = json.dumps(command).replace(str(ROOT),'$PACKAGE').replace(str(self.base),'$RUN')
        relevant = {"region":self.config.get("region"), "stations":self.config.get("stations"), "velocity_model":self.config.get("velocity_model")}
        if name != 'prepare_region':
            relevant = {"stage":self.config.get(stage), "resources":self.config.get("resources")}
            if stage == 'association' and name in ('build_gamma_inputs', 'prepare_dbscan_eps'):
                relevant['stage'] = {"dbscan_vp_km_s":self.config['association']['dbscan_vp_km_s']}

        previous = self.state['steps'].get(key)
        if previous and previous['status'] == 'PASS':
            if previous['identity'] != identity or any(not (self.base / p).is_file() or digest(self.base / p) != h for p,h in previous['outputs'].items()):
                raise ValueError('Completed step/input configuration changed; create a new run: ' + key)
            return
        print('Running ' + key, flush=True)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        env.pop('PYTHONPATH',None)
        env['SEISFLOW_RUNTIME'] = str(Path(os.environ.get('SEISFLOW_RUNTIME', ROOT / 'runtime.local.json')).resolve())
        env['MPLCONFIGDIR'] = str(self.base / '.cache/matplotlib')
        record = {'status':'RUNNING','identity':identity,'command':command,'outputs':{}}
        self.state['steps'][key] = record
        write_json(self.state_path,self.state)
        with (self.logs / (key + '.log')).open('w') as stream:
            result = subprocess.run(command,cwd=self.base,env=env,stdout=stream,stderr=subprocess.STDOUT)
        record['status'] = 'PASS' if result.returncode==0 else 'FAIL'
        record['exit_code'] = result.returncode
        for p in map(Path,expected):
            if not p.is_file(): record['status'] = 'FAIL'
            else: record['outputs'][os.path.relpath(p,self.base)] = digest(p)
        write_json(self.state_path,self.state)
        if record['status'] != 'PASS':
            raise ValueError('Step failed: ' + key + '; inspect ' + str(self.logs / (key + '.log')))
    def script(self, stage, name):
        return ROOT / 'skills' / ('seismic-' + stage.replace('_', '-')) / 'scripts' / name
    def native(self, stage, name, args, expected=()):
        self.step(stage,name[:-3],self.script(stage,name),args,expected)
    def run_stage(self, stage):
        knowledge = Knowledge()
        lock = knowledge.stage_context(self.base, stage, self.config.get(stage, {}), bool(self.state['steps']))
        self.state['knowledge'] = lock
        write_json(self.state_path, self.state)
        print('Knowledge context: ' + str(self.base / 'knowledge' / ('context-' + stage + '.json')), flush=True)
        cfg = self.config
        out = self.base / stage
        ncpu = cfg['resources']['cpu_workers']
        archive = self.archive
        common = ['--run-id',cfg['run_id'] + '-' + stage]
        if stage == 'preprocess':
            self.step(stage,'validate',ROOT/'scripts/validate_archive.py',['--archive',archive,*common],[archive/'contract.v2.json'])
        elif stage == 'picking':
            load_contract(archive,'preprocess')
            out.mkdir(exist_ok=True)
            verify = out/'reader_verification/verify_report.json'
            data = out/'data_list.txt'
            raw = out/'raw'
            self.native(stage,'verify_input_roundtrip.py',['--eqnet-repo',ROOT/'knowledge/repos/EQNet','--out',verify.parent],[verify])
            self.native(stage,'build_data_list.py',['--archive',archive,'--out',data],[data])
            device = cfg['resources']['picking_device']
            args = ['--eqnet-repo',ROOT/'knowledge/repos/EQNet','--weights',ROOT/'assets/weights/phasenet_plus_v1.pth',
                    '--data-list',data,'--result-path',raw,'--verify-report',verify,'--device',device,
                    '--min-prob',cfg['picking']['min_prob'],'--subdir-level',0,'--workers',0]
            if device=='cuda': args += ['--gpu-idx',cfg['resources']['gpu_index']]
            self.native(stage,'eqnet_pick.py',args,[raw/'execution_receipt.json'])
            self.native(stage,'qc_picks.py',['--picks',raw,'--archive',archive,'--out',out/'qc'],[out/'qc/qc_summary.json'])
            self.native(stage,'gen_picking_contract.py',['--picks-dir',raw,'--archive',archive,'--out',out/'contract.v2.json',*common,
                '--eqnet-commit',json.loads((ROOT/'toolchain.json').read_text())['sources']['EQNet']['commit'],
                '--weights-sha256',digest(ROOT/'assets/weights/phasenet_plus_v1.pth'),'--device',device,'--min-prob',cfg['picking']['min_prob'],
                '--verification-report',verify,'--qc-path',out/'qc'],[out/'contract.v2.json',out/'picks.csv'])
        else:
            self.step(stage,'prepare_region',ROOT/'scripts/prepare_region.py',['--config',self.path],
                      [self.stations,self.vp,self.vs,self.inputs/'region_preparation.json'])
            if stage=='association':
                picks = self.base/'picking'
                pc,_ = load_contract(picks,'picking')
                table = self.base/'association_inputs'
                preparation = ['--picks',picks/pc['outputs']['picks_path'],'--archive',archive,'--stations',self.stations,'--out',table]
                if cfg['association'].get('utc_day'): preparation += ['--day',cfg['association']['utc_day']]
                self.native(stage,'build_gamma_inputs.py',preparation,[table/'gamma_picks.csv',table/'gamma_stations.csv',table/'input_manifest.json'])
                eps = table/'dbscan_eps_options.json'
                # Scaling velocity is explicit; this is separate from layered travel times.
                self.native(stage,'prepare_dbscan_eps.py',['--stations',table/'gamma_stations.csv','--vp',cfg['association']['dbscan_vp_km_s'],'--out',eps],[eps])
                choice = cfg['association']['dbscan_eps_choice']
                if choice not in ['default','estimated','custom']:
                    print(json.loads(eps.read_text())['user_prompt'])
                    raise ValueError('A user decision is required: set association.dbscan_eps_choice in pipeline.json; no association was launched')
                args = ['--picks',table/'gamma_picks.csv','--stations',table/'gamma_stations.csv','--vp-model',self.vp,'--vs-model',self.vs,
                        '--out',out,'--ncpu',ncpu,'--picking-contract',picks,'--dbscan-eps-options',eps,
                        '--dbscan-eps-choice',choice,'--dbscan-eps-selected-via','pipeline_config',
                        '--depth-max-km',cfg['region']['depth_range_km'][1],'--margin-km',cfg['region']['station_margin_km']]
                if choice=='custom': args += ['--dbscan-eps',cfg['association']['dbscan_eps_s']]
                for field in ['min_picks','min_p','min_s','min_stations','max_sigma11','max_sigma22','oversample']:
                    args += ['--'+field.replace('_','-'),cfg['association'][field]]
                self.native(stage,'run_gamma.py',args,[out/'gamma_events.csv',out/'gamma_assignments.csv'])
                self.native(stage,'qc_and_contract.py',['--dir',out,'--out',out/'contract.v2.json',*common,'--picks-contract',picks,
                    '--vp-model',self.vp,'--vs-model',self.vs,'--ncpu-used',ncpu],[out/'contract.v2.json'])
            elif stage=='location':
                assoc = self.base/'association'
                doc,_ = load_contract(assoc,'association')
                if doc['stats']['n_events']==0:
                    return self.mark_empty(stage,'NO_ASSOCIATED_EVENTS')
                self.native(stage,'make_hypoinverse_inputs.py',['--assoc-dir',assoc,'--stations',self.stations,'--vp-model',self.vp,
                    '--vs-model',self.vs,'--pos',cfg['location']['pos'],'--out',out],[out/'input/phase.dat',out/'input/station_aliases.json'])
                self.native(stage,'verify_phase_dat.py',['--workdir',out,'--assoc-dir',assoc],[out/'input/phase_dat_verification.json'])
                self.native(stage,'run_hypoinverse.py',['--workdir',out],[out/'output/run.sum',out/'output/run.arc'])
                self.native(stage,'qc_and_contract.py',['--workdir',out,'--assoc-dir',assoc,'--stations',self.stations,*common],[out/'contract.v2.json'])
            elif stage=='relocation':
                location = self.base/'location'
                if self.state['stages'].get('location',{}).get('status')=='EMPTY':
                    return self.mark_empty(stage,'NO_LOCATED_EVENTS')
                doc,_ = load_contract(location,'location')
                if doc['stats']['located']==0: return self.mark_empty(stage,'NO_LOCATED_EVENTS')
                ratio = cfg['relocation']['vp_vs_ratio']
                if ratio is None or ratio <= 1:
                    raise ValueError('Configure a scientifically justified relocation.vp_vs_ratio; HypoDD accepts a constant ratio')
                erh = json.loads((location/'qc/location_qc.json').read_text())['erh_median_km']
                out.mkdir(exist_ok=True)
                for tier, params in cfg['relocation']['tiers'].items():
                    directory = out/tier
                    self.step(stage,'convert_'+tier,self.script(stage,'make_ph2dt_inputs.py'),['--location-dir',location,
                        '--assoc-dir',self.base/'association','--stations',self.stations,'--out',directory],[directory/'input/phase.dat'])
                    self.step(stage,'verify_'+tier,self.script(stage,'verify_ph2dt_inputs.py'),['--workdir',directory,'--location-dir',location],[directory/'input/ph2dt_input_verification.json'])
                    pairargs=['--workdir',directory]
                    for key in ['minlnk','minobs','maxdist','maxsep','maxngh']: pairargs += ['--'+key,params[key]]
                    self.step(stage,'pair_'+tier,self.script(stage,'run_ph2dt.py'),pairargs,[directory/'qc/pairing_result.json'])
                    if json.loads((directory/'qc/pairing_result.json').read_text())['status']=='EMPTY': continue
                    base = ['--workdir',directory,'--vp-model',self.vp,'--ratio',ratio,'--initial-erh-km',erh,
                            '--obsct',params['obsct'],'--wdct-last',params['wdct_last'],'--dist',params['maxdist']]
                    self.step(stage,'damping_'+tier,self.script(stage,'run_hypodd.py'),base+['--damping-trials',','.join(map(str,cfg['relocation']['damping_trials']))],
                              [directory/'qc/damping_selection.json'])
                    selection=json.loads((directory/'qc/damping_selection.json').read_text())
                    if selection['status']=='EMPTY': continue
                    if selection['selected_damp'] is None:
                        print('DAMP evidence is inconclusive for '+tier+'; inspect saved trials and the relocation skill.')
                        continue
                    self.step(stage,'solve_'+tier,self.script(stage,'run_hypodd.py'),base+['--damp',selection['selected_damp']],[directory/'qc/final_run.json'])
                self.native(stage,'qc_and_contract.py',['--workdir',out,'--location-dir',location,'--vp-model',self.vp,'--ratio',ratio,*common],[out/'contract.v2.json'])
            elif stage == 'post_detection_relocation':
                if self.state['stages'].get('detection', {}).get('status') == 'EMPTY':
                    return self.mark_empty(stage, 'NO_MESS_DETECTIONS')
                if not cfg.get(stage):
                    raise ValueError('Post-MESS joint settings are required; use a NEW run with the current example configuration')
                reloc = self.base/'relocation'
                rdoc,_ = load_contract(reloc,'relocation')
                tier = cfg[stage]['ct_reuse']['relocation_tier']
                if rdoc['tiers'].get('statuses',{}).get(tier,{}).get('status') != 'READY':
                    return self.mark_empty(stage, 'CT_REUSE_TIER_UNAVAILABLE')
                strict_cat = reloc/rdoc['outputs']['catalogs'][tier]
                det = self.base/'detection'
                joint = out/'joint'
                self.native(stage,'4_build_joint_inputs.py',
                    ['--strict-catalog',strict_cat,'--mess-catalog',det/'output/mess/catalog.csv',
                     '--mess-event-dat',det/'output/mess/event.dat','--mess-dt-cc',det/'output/mess/dt.cc',
                     '--strict-dt-ct',reloc/tier/'input/dt.ct',
                     '--station-aliases',self.base/'location/input/station_aliases.json',
                     '--new-cc-min',cfg[stage].get('new_cc_min',0.4),'--outdir',joint],
                    [joint/'input/event.dat',joint/'input/dt.ct',joint/'input/dt.cc'])
                self.native(stage,'5_run_hypodd_joint.py',
                    ['--indir',joint/'input','--outdir',joint/'output','--hypodd-bin',binary('hypoDD'),
                     '--vp-model',self.vp,'--vs-model',self.vs,'--ratio',cfg['relocation']['vp_vs_ratio'],
                     '--damp',cfg[stage].get('damp',400)],
                    [joint/'output/hypoDD.reloc'])
                self.native(stage,'6_parse_joint.py',
                    ['--reloc',joint/'output/hypoDD.reloc','--strict-catalog',strict_cat,
                     '--mess-catalog',det/'output/mess/catalog.csv','--out',out/'joint_relocated_catalog.csv'],
                    [out/'joint_relocated_catalog.csv'])
            elif stage=='detection':
                if self.state['stages'].get('relocation',{}).get('status')=='EMPTY': return self.mark_empty(stage,'NO_TEMPLATES')
                doc,_=load_contract(self.base/'relocation','relocation')
                states=doc['tiers'].get('statuses',{})
                if states.get('medium',{}).get('status')=='EMPTY': return self.mark_empty(stage,'NO_MEDIUM_TEMPLATES')
                if states.get('medium',{}).get('status')!='READY':
                    self.state['stages'][stage]={'status':'UNAVAILABLE','reason':'MEDIUM_TEMPLATE_CATALOG_UNAVAILABLE'}
                    write_json(self.state_path,self.state)
                    raise ValueError('Medium relocation tier is unavailable; detection cannot start. Inspect DAMP evidence and failures.')
                with (self.base/'relocation'/doc['outputs']['catalogs']['medium']).open() as f:
                    if not list(csv.DictReader(f)): return self.mark_empty(stage,'NO_MEDIUM_TEMPLATES')
                if not cfg['detection']['time_range']:
                    raise ValueError('Set detection.time_range to YYYYMMDD-YYYYMMDD (end exclusive)')
                catalog = self.base/'relocation'/doc['outputs']['catalogs']['medium']
                self.native(stage,'1_prepare_inputs.py',
                    ['--catalog',catalog,'--assignments',self.base/'association/gamma_assignments.csv',
                     '--stations',self.base/'association_inputs/gamma_stations.csv','--archive',archive,
                     '--data-root',out/'mess_data','--out-dir',out],
                    [out/'mess.temp',out/'mess.sta'])
                cfg_file = out/('config_%s.py' % cfg['run_id'])
                if not cfg_file.is_file():
                    cfg_file.write_text(self.script(stage,'config_mess.py').read_text())
                scan = ['--data-root',out/'mess_data','--config-dir',out,'--palm-root',ROOT/'knowledge/repos/PALM',
                        '--time-range',cfg['detection']['time_range'],
                        '--segment-days',cfg['detection'].get('segment_days',7)]
                if cfg['resources']['mess_device']=='gpu': scan += ['--gpu-index',cfg['resources']['gpu_index']]
                self.native(stage,'2_run_mess_scan.py',scan,
                    [out/'output/mess/catalog.csv',out/'output/mess/dt.cc'])
                self.native(stage,'3_export_tiers.py',
                    ['--catalog',out/'output/mess/catalog.csv','--event-dat',out/'output/mess/event.dat',
                     '--outdir',out/'output/mess'],
                    [out/'output/mess/catalog_cc08.csv'])
            elif stage=='focal_mechanism':
                if self.state['stages'].get('relocation',{}).get('status')=='EMPTY':
                    return self.mark_empty(stage,'NO_RELOCATED_EVENTS')
                if not cfg.get(stage):
                    raise ValueError('Focal-mechanism settings are required; use a NEW run with the current example configuration')
                rdoc,_=load_contract(self.base/'relocation','relocation')
                tier=cfg[stage].get('relocation_tier','strict')
                if rdoc['tiers'].get('statuses',{}).get(tier,{}).get('status')!='READY':
                    return self.mark_empty(stage,'RELOCATION_TIER_'+tier.upper()+'_UNAVAILABLE')
                catalog=self.base/'relocation'/rdoc['outputs']['catalogs'][tier]
                assoc=self.base/'association/gamma_assignments.csv'
                self.native(stage,'1_build_inputs.py',
                    ['--assignments',assoc,'--catalog',catalog,
                     '--stations',self.base/'association_inputs/gamma_stations.csv',
                     '--vmodel',self.vp,'--out',out/'IN'],
                    [out/'IN/pol_dl.csv',out/'IN/catalog.csv',out/'IN/stations.csv',out/'IN/vmodel_layers.txt'])
                self.native(stage,'2_cut_event_waveforms.py',
                    ['--archive',archive,'--assignments',assoc,'--catalog',catalog,
                     '--out',out/'event_wf','--workers',ncpu],
                    [out/'event_wf/event_station_manifest.csv'])
                self.native(stage,'3_measure_sp_amplitudes.py',
                    ['--wf-root',out/'event_wf','--out',out/'IN/amp.csv'],[out/'IN/amp.csv'])
                fargs=['--in-dir',out/'IN','--out-dir',out/'OUT',
                       '--threshold',cfg[stage].get('polarity_threshold',0.3),
                       '--delmax',cfg[stage].get('delmax_km',120),
                       '--num-cpus',cfg[stage].get('num_cpus',min(ncpu,8))]
                reversals=cfg[stage].get('reversal_stations') or []
                if reversals:
                    rev=out/'IN'/'reverse.csv'
                    if not rev.is_file(): write_reverse_csv(rev,reversals)
                    fargs += ['--reverse-file',rev]
                self.native(stage,'5_run_skhash.py',fargs,[out/'OUT/out.csv'])
                self.native(stage,'6_parse_mechanisms.py',
                    ['--out-dir',out/'OUT','--catalog-out',out/'mechanisms_catalog.csv',
                     '--qc-out',out/'qc_summary.json'],[out/'mechanisms_catalog.csv'])
        if stage in ('detection','post_detection_relocation','focal_mechanism'):
            primary = {'detection': [out/'output/mess/catalog.csv',out/'output/mess/catalog_cc08.csv'],
                       'post_detection_relocation': [out/'joint_relocated_catalog.csv'],
                       'focal_mechanism': [out/'mechanisms_catalog.csv']}[stage]
            if any(not p.is_file() or p.stat().st_size == 0 for p in primary):
                return self.mark_empty(stage,'NO_PRIMARY_OUTPUT')
            self.state['stages'][stage]={'status':'COMPLETE','contract_status':'LAUNCHER_OUTPUTS_VERIFIED','scientific_status':'NOT_TESTED'}
        else:
            doc,_=load_contract(archive if stage=='preprocess' else out,stage)
            self.state['stages'][stage]={'status':'COMPLETE','contract_status':doc.get('status'),'scientific_status':'NOT_TESTED'}
        write_json(self.state_path,self.state)
    def mark_empty(self,stage,reason):
        self.state['stages'][stage]={'status':'EMPTY','reason':reason,'scientific_status':'NOT_TESTED'}
        write_json(self.state_path,self.state)
        print(stage+': '+reason)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime',help='Explicit runtime.local.json, relative to current directory')
    commands=ap.add_subparsers(dest='command',required=True)
    p=commands.add_parser('configure')
    for name in ['science-python','validator-python','mess-python']: p.add_argument('--'+name,required=True)
    p.add_argument('--out')
    p=commands.add_parser('doctor'); p.add_argument('--out')
    p=commands.add_parser('init'); p.add_argument('--workdir',required=True)
    p=commands.add_parser('run'); p.add_argument('--config',required=True); p.add_argument('--stage',choices=STAGES+['all'],required=True)
    p=commands.add_parser('status'); p.add_argument('--config',required=True)
    p=commands.add_parser('knowledge'); add_knowledge_cli(p)
    args=ap.parse_args()
    if args.runtime: os.environ['SEISFLOW_RUNTIME']=str(Path(args.runtime).resolve())
    if args.command=='knowledge': return knowledge_cli(args)
    if args.command=='configure': configure(args)
    elif args.command=='doctor': return doctor(args)
    elif args.command=='init': init(args)
    elif args.command=='status': print(json.dumps(Runner(args.config).state,indent=2))
    elif args.command=='run':
        runner=Runner(args.config)
        import fcntl
        with (runner.base/'.run.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            for stage in STAGES if args.stage=='all' else [args.stage]: runner.run_stage(stage)
    return 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except (ValueError,OSError,KeyError,subprocess.SubprocessError) as exc:
        print('STOP: '+str(exc),file=sys.stderr)
        sys.exit(2)
