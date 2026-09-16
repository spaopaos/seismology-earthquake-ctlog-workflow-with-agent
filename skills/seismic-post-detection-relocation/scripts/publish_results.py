"""Publish exactly three post-MESS outcomes, retaining native counts and event lineage."""
import csv
import json
from pathlib import Path
import bootstrap
from pipeline_contracts import now, relative, write_v2
from runtime_support import digest
from hypodd_inputs import utc
from damping_metrics import load_catalog, displacement_metrics
from qc_and_contract import FIELDS
from prepare_inputs import LABELS, write_json


def write_csv(path, rows, fields):
    with Path(path).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)


def publish(out, master, states, detection_contracts, picking, location, vp, run_id):
    out = Path(out)
    catalogs, native_paths, counts, metrics = {}, {}, {}, {}
    union = set()
    for label in LABELS:
        directory = out/label; directory.mkdir(exist_ok=True)
        ids = master['ids_by_label'][label]
        selected = {int(r['event_id']): r for r in master['rows_by_label'][label]}
        native, rows, refs = {}, [], []
        state = states[label]
        if state['status'] == 'READY':
            path = directory/'output/hypoDD.reloc'
            native_paths[label] = relative(path, out)
            for line in path.read_text().splitlines():
                f = line.split()
                if not f:
                    continue
                if len(f) != len(FIELDS):
                    raise ValueError('Unexpected native relocated row')
                row = dict(zip(FIELDS, f)); eid = int(row['id'])
                if eid not in ids or eid in native:
                    raise ValueError('Duplicate/unknown relocated event ID')
                from datetime import datetime, timedelta, timezone
                origin = datetime(*[int(row[k]) for k in ('yr', 'mo', 'dy', 'hr', 'mi')], tzinfo=timezone.utc)
                origin += timedelta(seconds=float(row['sc']))
                initial = master['events'][eid]
                record = {**selected.get(eid, {}), 'event_id': eid, 'origin_time': origin.isoformat(),
                          'latitude': float(row['lat']), 'longitude': float(row['lon']), 'depth_km': float(row['dep']),
                          'initial_latitude': initial['latitude'], 'initial_longitude': initial['longitude'],
                          'initial_depth_km': initial['depth_km'], 'location_method': 'hypodd_cc_ct',
                          'depth_reference': 'sea_level', 'ct_source': 'independent_phasenet',
                          'role': 'detection' if eid in selected else 'template_reference',
                          **{k: int(row[k]) for k in ('nccp', 'nccs', 'nctp', 'ncts', 'cid')},
                          'rcc_s': float(row['rcc']), 'rct_s': float(row['rct'])}
                native[eid] = record
                (rows if eid in selected else refs).append(record)
            metrics[label] = displacement_metrics(load_catalog(directory/'output/hypoDD.loc'), load_catalog(path))
            if not rows:
                state = {**state, 'status': 'EMPTY', 'reason': 'NO_DETECTION_RETAINED_BY_SOLVER'}
                states[label] = state
        else:
            metrics[label] = None
        fields = list(dict.fromkeys(['event_id', 'origin_time', 'latitude', 'longitude', 'depth_km',
                   'role', 'location_method', 'ct_source', 'depth_reference', 'status', 'known_match_method',
                   'best_detection_cc', 'initial_latitude', 'initial_longitude', 'initial_depth_km',
                   'nccp', 'nccs', 'nctp', 'ncts', 'cid', 'rcc_s', 'rct_s'] + [k for r in rows for k in r]))
        if state['status'] != 'UNAVAILABLE':
            write_csv(directory/'catalog.csv', rows, fields)
            write_csv(directory/'reference_events.csv', refs, fields)
            catalogs[label] = relative(directory/'catalog.csv', out)
            counts[label] = len(rows)
            union.update(r['event_id'] for r in rows)
        else:
            counts[label] = None
        lineage = []
        evidence = directory/'input/joint_verification.json'
        observations = json.loads(evidence.read_text())['measured'] if evidence.is_file() else None
        for eid in sorted(ids):
            retained = eid in native if state['status'] != 'UNAVAILABLE' else None
            lineage.append({'event_id': eid, 'role': 'detection' if eid in selected else 'template_reference',
                            'relocated': retained, 'reason': 'RETAINED' if retained else
                            ('NOT_RETAINED_BY_SOLVER' if state['status'] == 'READY' else state['reason']),
                            'cc_observations': observations['per_event'][str(eid)]['cc'] if observations else None,
                            'ct_observations': observations['per_event'][str(eid)]['ct'] if observations else None})
        write_csv(directory/'event_lineage.csv', lineage,
                  ['event_id', 'role', 'relocated', 'reason', 'cc_observations', 'ct_observations'])
        write_json(directory/'qc_summary.json', {'outcome': state, 'input_detection_events': len(selected),
                   'retained_detection_events': counts[label], 'retained_reference_events': len(refs) if counts[label] is not None else None,
                   'input_observations': observations, 'spatial_metrics': metrics[label],
                   'scientific_status': 'NOT_TESTED', 'rms_scope': 'per-event native final rcc/rct; not before-after comparable aggregate'})
    write_json(out/'qc_summary.json', {'tiers': states, 'counts': counts, 'spatial_metrics': metrics,
               'ct_source': 'independent_phasenet', 'formal_catalog_count': len(catalogs),
               'new_event_uncertainty': 'not measured by template inheritance or the upstream ERH comparison scale'})
    artifacts = {}
    def register(name, path):
        path = Path(path).resolve()
        ref = relative(path, out)
        artifacts[name] = {'path': ref, 'kind': 'file', 'required': True, 'sha256': digest(path)}
        return ref
    upstream = []
    for label, path in detection_contracts.items():
        upstream.append({'stage': 'detection', 'contract_path': register('upstream_'+label, path),
                         'input_verification': 'PASS', 'verification_basis': 'verified_shared_contract_graph'})
    for stage, path in (('picking', picking), ('location', location)):
        upstream.append({'stage': stage, 'contract_path': register('upstream_'+stage, path),
                         'input_verification': 'PASS', 'verification_basis': 'verified_shared_contract_graph'})
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.name not in ('contract.v2.json', 'catalogs.json'):
            register('product_'+str(path.relative_to(out)), path)
    register('vp_model', vp)
    index = {'stage': 'post_detection_relocation', 'catalogs': {label: {
             **states[label], 'catalog_path': catalogs.get(label), 'events': counts[label]} for label in LABELS}}
    write_json(out/'catalogs.json', index)
    register('catalog_index', out/'catalogs.json')
    doc = {'contract_version': '2.0', 'stage': 'post_detection_relocation', 'run_id': run_id+'-post-mess',
           'created_at': now(), 'software': {'name': 'ph2dt + HypoDD CC+CT', 'version': 'pinned'},
           'status': 'READY' if all(s['status'] == 'READY' for s in states.values()) else 'PARTIAL',
           'upstream': upstream, 'qc_path': relative(out/'qc_summary.json', out), 'artifacts': artifacts,
           'times': {'catalog_dt': True, 'cross_correlation': True, 'ct_source': 'independent_phasenet'},
           'solver': {'idat': 3, 'ipha': 3, 'damping_rule': 'spatial-evidence-1.7',
                      'parameters_path': relative(out/'effective_parameters.json', out)},
           'tiers': states, 'outputs': {'catalogs': catalogs, 'reloc_paths': native_paths,
                      'event_mapping_paths': {label: label+'/event_lineage.csv' for label in LABELS}},
           'stats': {'tier_counts': counts, 'unique_relocated_detection_events': len(union)},
           'warnings': ['Only independent PhaseNet+ arrival values enter CT; MESS hints guide selection, so errors need not be statistically independent.',
                        'Upstream ERH is a comparison scale, not measured uncertainty for newly detected events.',
                        'Reference events are separately labeled; no cross-CC-tier merge or absolute magnitude calibration.',
                        'Damping stability and solver completion do not independently establish physical location accuracy.']}
    written = write_v2(doc, out/'contract.v2.json')
    if written['validation']['artifact_status'] != 'PASS':
        raise ValueError('Joint output contract failed artifact validation')
    print(json.dumps({'tier_counts': counts, 'status': written['status']}))
