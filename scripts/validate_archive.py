#!/usr/bin/env python3
"""Validate agent-produced daily archives and publish the preprocessing handoff."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import obspy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'contracts'))
from archive_interface import archive_records, intervals, within, DAY_NPTS
from pipeline_contracts import sha256, load_contract, publish_payload

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', required=True)
    ap.add_argument('--run-id', required=True)
    args = ap.parse_args()
    root = Path(args.archive).resolve()
    if (root / 'contract.v2.json').exists():
        doc, _ = load_contract(root, 'preprocess')
        report = json.loads((root / 'archive_validation.json').read_text())
        for name, expected in report['file_sha256'].items():
            if sha256(root / name) != expected:
                raise ValueError('Archive changed since independent validation: ' + name)
        print(json.dumps({'status': report['status'], 'reused': True}))
        return
    provenance = json.loads((root / 'archive_provenance.json').read_text())
    hashes = {}
    for field in ['processing_script', 'effective_config', 'source_manifest', 'qc_summary']:
        name = provenance[field]
        if not isinstance(name, str) or not name or not (root / name).is_file():
            raise ValueError('Missing preprocessing evidence: ' + field)
        hashes[name] = sha256(root / name)
    for name in ['daily_manifest.csv', 'archive_provenance.json']:
        hashes[name] = sha256(root / name)
    records, skipped = archive_records(root)
    if not records:
        raise ValueError('No usable group-days; preprocessing has no consumable output')
    summaries = []
    for r in records:
        m = r['meta']
        if m.get('units') != 'm/s' or m.get('physical_quantity') != 'ground_velocity':
            raise ValueError('Archive must explicitly declare physical velocity in m/s')
        if m.get('orientation_verified') is not True or not m.get('orientation_source'):
            raise ValueError('Verified orientation and its source are required: ' + r['group'])
        if m.get('response_verified') is not True or not m.get('response_source'):
            raise ValueError('Verified response/physical-unit provenance is required: ' + r['group'])
        low, high = map(float, m['analysis_band_hz'])
        original_sr = float(m['group_min_raw_sampling_rate_hz'])
        if not 0 < low < high <= min(40, 0.8 * original_sr / 2):
            raise ValueError('Effective passband violates original sampling support')
        start = obspy.UTCDateTime(r['date'])
        amplitudes = {}
        for c in 'ZNE':
            path = root / r['file_' + c]
            if path.suffix.lower() not in ('.mseed', '.ms', '.sac'):
                raise ValueError('Unsupported standardized archive file: ' + str(path))
            st = obspy.read(str(path), apply_calib=False)
            if len(st) != 1:
                raise ValueError('Exactly one complete trace is required per component file')
            tr = st[0]
            if tr.id != r['trace_group'] + c:
                raise ValueError('Trace identity differs from declared group mapping: ' + tr.id)
            if abs(tr.stats.sampling_rate - 100) > 1e-8 or tr.stats.npts != DAY_NPTS or abs(tr.stats.starttime - start) > 1e-7:
                raise ValueError('Waveform is not on the complete 100 Hz UTC daily grid')
            if tr.stats.calib != 1.0 or not np.isfinite(tr.data).all():
                raise ValueError('Nonfinite samples or non-unit calib')
            comp = m['components'][c]
            data = intervals(comp['data_intervals'])
            usable = intervals(comp['usable_intervals'])
            if not within(usable, data) or not within(r['usable'], usable):
                raise ValueError('Usable interval extends beyond observation support')
            last = 0
            for a, b in data + [[DAY_NPTS, DAY_NPTS]]:
                if np.any(tr.data[last:a] != 0):
                    raise ValueError('Unobserved archive samples must be zero-filled')
                last = b
            amplitudes[c] = float(np.max(np.abs(tr.data)))
            hashes[r['file_' + c]] = sha256(path)
        hashes[r['metadata']] = sha256(root / r['metadata'])
        summaries.append({'group': r['group'], 'date': r['date'], 'peak_abs_mps': amplitudes,
                          'usable_fraction': sum(b-a for a,b in r['usable']) / DAY_NPTS})
    report = {'status': 'PARTIAL' if skipped else 'PASS', 'groups_checked': len(records),
              'skipped': skipped, 'file_sha256': hashes, 'summaries': summaries,
              'scientific_status': 'NOT_TESTED',
              'scope': 'Independent waveform/metadata consistency. Response and orientation correctness require source/QC review.'}
    report_path = root / 'archive_validation.json'
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    dc = {'format': 'MiniSEED' if all(Path(r['file_Z']).suffix.lower() != '.sac' for r in records) else 'SAC',
          'physical_quantity': 'ground_velocity', 'units': 'm/s', 'response_removed': True,
          'sampling_rate_hz': 100.0, 'archive_component_labels': ['Z','N','E'], 'target_band_hz': [1.0,40.0],
          'actual_band_source': 'per_group_day_metadata'}
    payload = {'contract_version': '2.0', 'stage': 'preprocess', 'run_id': args.run_id,
               'created_at': datetime.now(timezone.utc).isoformat(), 'upstream': [],
               'software': {'name': 'dataset-specific preprocessing + independent release validator', 'version': '0.1.0'},
               'status': 'PARTIAL' if skipped else 'READY', 'archive_root': '.',
               'manifest_path': 'daily_manifest.csv', 'archive_validation_status': report['status'],
               'data_contract': dc, 'reader_requirements': {'consume_valid_intervals': True, 'reapply_response_removal': False},
               'model_input_verification': {'status': 'NOT_TESTED'},
               'qc_path': provenance['qc_summary'], 'config_path': provenance['effective_config'],
               'script_path': provenance['processing_script'],
               'stats': {'group_days': len(records)+len(skipped), 'ready': sum(r['status']=='READY' for r in records),
                         'partial': sum(r['status']=='PARTIAL_DAY' for r in records), 'unavailable': len(skipped)},
               'artifacts': {name: {'path': name, 'kind': 'file', 'required': True, 'sha256': h} for name,h in hashes.items()}}
    payload['artifacts']['independent_validation'] = {'path': report_path.name, 'kind': 'file', 'required': True, 'sha256': sha256(report_path)}
    payload['artifacts']['archive_root'] = {'path': '.', 'kind': 'directory', 'required': True}
    doc = publish_payload(payload, root / 'contract.v2.json', 'preprocess')
    load_contract(root, 'preprocess')
    print(json.dumps({'status': report['status'], 'checked': len(records), 'contract': str(root / 'contract.v2.json')}))

if __name__ == '__main__':
    main()
