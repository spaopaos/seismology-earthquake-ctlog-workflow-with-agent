"""Three independent post-MESS joint CC+CT relocations, with evidence-selected DAMP."""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from statistics import median
import bootstrap
from bootstrap import ROOT
from pipeline_contracts import load_contract, inspect_artifacts, lookup
from runtime_support import digest, runtime_path
from hypodd_inputs import joint_schedule, verify_joint_receipt
from tier_outcomes import pairing_result, outcome
from run_hypodd import trial_context, validate_final_selection
from prepare_inputs import LABELS, read_csv, write_json, build_master, prepare_tier
from verify_inputs import verify_phases, verify_joint

STAGE = 'post_detection_relocation'


def verified_graph(paths):
    """Verify each immutable upstream product once per invocation, including shared ancestors."""
    verified, visiting = {}, set()
    def visit(path, stage):
        path = Path(path).resolve()
        if path in visiting:
            raise ValueError('Upstream contract cycle')
        if path in verified:
            if verified[path]['stage'] != stage:
                raise ValueError('Conflicting upstream identity')
            return
        doc, actual = load_contract(path, stage, check_artifacts=False)
        visiting.add(path)
        issues = inspect_artifacts(doc, actual.parent)
        if issues:
            raise ValueError('Upstream artifact failure: ' + json.dumps(issues[:3]))
        for parent in doc['upstream']:
            visit(actual.parent / parent['contract_path'], parent['stage'])
        visiting.remove(path)
        verified[path] = doc
    for path in paths:
        visit(path, 'detection')
    return verified


def unique_source(graph, stage):
    matches = [(p, d) for p, d in graph.items() if d['stage'] == stage]
    if len(matches) != 1:
        raise ValueError('Expected one common upstream ' + stage + ' contract')
    return matches[0]


def execute(script, args, log):
    log = Path(log); log.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'}
    with log.open('w') as stream:
        process = subprocess.run([str(runtime_path('science_python')), '-B', str(script), *map(str, args)],
                                 stdout=stream, stderr=subprocess.STDOUT, env=env)
    if process.returncode:
        raise ValueError('Native step failed; inspect ' + str(log))


def copy_identical(source, target):
    source, target = Path(source), Path(target)
    if target.exists():
        if digest(source) != digest(target):
            raise ValueError('Existing input differs; use a new run: ' + str(target))
    else:
        shutil.copyfile(source, target)


def solve_tier(directory, master, label, settings, vp, ratio, erh):
    directory = Path(directory)
    inputs = directory/'input'
    if not master['rows_by_label'][label]:
        return {'status': 'EMPTY', 'reason': 'NO_DETECTIONS_IN_CC_TIER', 'damp': None}
    if not inputs.exists():
        prepare_tier(master, label, inputs, settings)
    if not (inputs/'conversion_meta.json').is_file():
        raise ValueError('Incomplete preparation; preserve it and use a fresh run')
    verify_phases(inputs)
    meta = json.loads((inputs/'conversion_meta.json').read_text())
    if meta['n_phase_lines'] == 0:
        return {'status': 'UNAVAILABLE', 'reason': 'NO_INDEPENDENT_PHASES_FOR_CT', 'damp': None}
    if not (inputs/'dt.cc').read_text().strip():
        return {'status': 'UNAVAILABLE', 'reason': 'NO_CC_OBSERVATIONS', 'damp': None}
    pairdir = directory/'ct_pairing'
    (pairdir/'input').mkdir(parents=True, exist_ok=True)
    for name in ('phase.dat', 'station.dat', 'conversion_meta.json', 'ph2dt_input_verification.json'):
        copy_identical(inputs/name, pairdir/'input'/name)
    receipt = pairing_result(pairdir)
    if receipt is None:
        args = ['--workdir', pairdir]
        for key, value in settings['pairing'].items():
            args += ['--'+key, value]
        execute(ROOT/'skills/seismic-relocation/scripts/run_ph2dt.py', args, directory/'logs/ph2dt.log')
        receipt = pairing_result(pairdir)
    if receipt['status'] != 'PASS':
        return {'status': 'UNAVAILABLE', 'reason': 'NO_VALID_CT_PAIRS_' + receipt['status'], 'damp': None}
    # Keep original ph2dt outputs immutable; joint event union also contains CC-only nodes.
    copy_identical(pairdir/'input/dt.ct', inputs/'dt.ct')
    copy_identical(inputs/'events.native', inputs/'event.dat')
    if (inputs/'joint_verification.json').exists():
        verify_joint_receipt(inputs)
    else:
        verify_joint(inputs, pairdir/'qc/pairing_result.json')
    base = ['--workdir', directory, '--vp-model', vp, '--ratio', ratio, '--initial-erh-km', erh,
            '--joint-config', inputs/'joint_config.json', '--obsct', max(1, settings['obsct']),
            '--dist', settings['pairing']['maxdist'], '--wdct-last', settings['iterations'][-1]['wdct']]
    selection_path = directory/'qc/damping_selection.json'
    solver = ROOT/'skills/seismic-relocation/scripts/run_hypodd.py'
    if not selection_path.exists():
        execute(solver, base+['--damping-trials', ','.join(map(str, settings['damping_trials']))],
                directory/'logs/damping.log')
    selection = json.loads(selection_path.read_text())
    if selection.get('selected_damp') is None:
        return outcome(directory)
    if not (directory/'qc/final_run.json').exists():
        execute(solver, base+['--damp', selection['selected_damp']], directory/'logs/final.log')
    # Re-evaluate the saved selection even on resume/publication.
    args = argparse.Namespace(vp_model=vp, ratio=ratio, initial_erh_km=erh,
                              joint_config=inputs/'joint_config.json', obsct=max(1, settings['obsct']),
                              dist=settings['pairing']['maxdist'], wdct_last=settings['iterations'][-1]['wdct'])
    validate_final_selection(directory/'qc', trial_context(directory, args), selection['selected_damp'])
    state = outcome(directory)
    if state['status'] == 'READY':
        final = json.loads((directory/'qc/final_run.json').read_text())
        counts = final.get('used_event_observation_counts', {})
        if final.get('data_mode') != 'cc_ct' or not all(counts.get(k, 0) > 0 for k in ('cc', 'ct')):
            raise ValueError('Final native result does not demonstrate use of CC AND CT')
    return state


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--vp-model', required=True)
    ap.add_argument('--stations', required=True)
    args = ap.parse_args()
    cfgpath, out = Path(args.config).resolve(), Path(args.out).resolve()
    config = json.loads(cfgpath.read_text())
    settings = config.get(STAGE)
    if not settings:
        raise ValueError('Add explicit post_detection_relocation settings to a NEW run configuration')
    if settings.get('ct_source') != 'independent_phasenet' or settings.get('idat') != 3:
        raise ValueError('Post-MESS requires independent PhaseNet CT and joint IDAT=3')
    catalog_root = (cfgpath.parent/settings['detection_catalogs']).resolve()
    paths = {label: catalog_root/label/'contract.v2.json' for label in LABELS}
    print('Validating MESS and shared upstream contract graph', flush=True)
    graph = verified_graph(paths.values())
    docs = {label: graph[p.resolve()] for label, p in paths.items()}
    for label, threshold in zip(LABELS, (.4, .6, .8)):
        if docs[label]['selection']['cc_min'] != threshold:
            raise ValueError('Incorrect CC tier threshold')
    picking, pickdoc = unique_source(graph, 'picking')
    location, locdoc = unique_source(graph, 'location')
    relocation, relocdoc = unique_source(graph, 'relocation')
    upstream_model = (relocation.parent/relocdoc['solver']['velocity_model']['p_path']).resolve()
    if digest(args.vp_model) != digest(upstream_model):
        raise ValueError('Post-MESS must use the same validated regional P model')
    ratio = float(relocdoc['solver']['velocity_model']['vp_vs_ratio'])
    values = [float(row['erh']) for row in read_csv(location.parent/locdoc['outputs']['catalog_path'])
              if row.get('erh') and math.isfinite(float(row['erh'])) and float(row['erh']) > 0]
    erh = settings.get('initial_erh_km')
    if erh is None:
        if not values:
            raise ValueError('No positive upstream ERH comparison scale; set an explicit justified scale')
        erh = median(values)
    erh = float(erh)
    if not math.isfinite(erh) or erh <= 0 or not math.isfinite(ratio) or ratio <= 1:
        raise ValueError('Invalid ERH scale or Vp/Vs')
    source_files = list(Path(__file__).parent.glob('*.py'))
    source_files += list((ROOT/'skills/seismic-relocation/scripts').glob('*.py'))
    source_files += list((ROOT/'contracts').glob('*.py'))
    identity = {'settings': settings, 'config_sha256': digest(cfgpath), 'vp_sha256': digest(args.vp_model),
                'stations_sha256': digest(args.stations), 'ratio': ratio, 'initial_erh_km': erh,
                'contracts': {str(p): digest(p) for p in graph},
                'code': {str(p.relative_to(ROOT)): digest(p) for p in source_files}}
    out.mkdir(parents=True, exist_ok=True)
    identity_path = out/'execution_identity.json'
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError('Joint workflow/input/configuration identity changed; create a new run')
    if not identity_path.exists():
        write_json(identity_path, identity)
    write_json(out/'effective_parameters.json', {'settings': settings, 'vp_vs_ratio': ratio,
               'ratio_basis': 'same validated upstream regional Wadati ratio; not estimated from MESS CC-derived arrivals',
               'initial_erh_km': erh, 'erh_source': str(location),
               'erh_scope': 'upstream comparison scale, not measured uncertainty of new detections',
               'joint_effective_link_threshold': settings['obscc']+settings['obsct'],
               'depth_reference': 'sea_level', 'solver_depth_offset_km': 0})
    master = build_master(catalog_root, docs, picking.parent/pickdoc['outputs']['picks_path'], args.stations, settings)
    # A current diagnostic uses only independent matched P/S arrivals, never MESS CC times.
    ps = {}
    for obs in master['observations']:
        ps.setdefault((obs['event_id'], obs['station']), {})[obs['phase']] = obs['travel_time_s']
    pairs = [row for row in ps.values() if set(row) == {'P', 'S'} and row['S'] > row['P'] > 0]
    diagnostic = {'n_independent_ps_pairs': len(pairs), 'configured_vp_vs': ratio,
                  'source': 'independent matched PhaseNet arrivals relative to common solver origins',
                  'scope': 'diagnostic of ratio applicability; inferred template origins introduce uncertainty'}
    if len(pairs) >= 3:
        import numpy as np
        x = np.array([r['P'] for r in pairs]); y = np.array([r['S']-r['P'] for r in pairs])
        fit = np.linalg.lstsq(np.column_stack((x, np.ones_like(x))), y, rcond=None)[0]
        diagnostic.update(median_ts_tp=float(np.median(1+y/x)),
                          wadati_slope_plus_one=float(fit[0]+1), intercept_s=float(fit[1]),
                          residual_std_s=float(np.std(y-(fit[0]*x+fit[1]))))
    else:
        diagnostic['check_status'] = 'INSUFFICIENT_MATCHED_PAIRS'
    write_json(out/'matched_ct_ratio_check.json', diagnostic)
    states = {}
    for label in LABELS:
        print('Joint relocation: ' + label, flush=True)
        try:
            states[label] = solve_tier(out/label, master, label, settings, args.vp_model, ratio, erh)
        except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
            states[label] = {'status': 'UNAVAILABLE', 'reason': str(exc), 'damp': None}
        write_json(out/'tier_states.json', states)
        print(label + ': ' + states[label]['status'] + '; ' + states[label]['reason'], flush=True)
    from publish_results import publish
    publish(out, master, states, paths, picking, location, args.vp_model, config['run_id'])


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
