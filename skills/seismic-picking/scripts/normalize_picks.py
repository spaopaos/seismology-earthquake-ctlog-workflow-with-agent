"""Turn actual EQNet output into the fixed downstream CSV, with archive interval flags."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from contract_io import load_contract
from archive_interface import archive_records

COLUMNS = ['station_id', 'phase_index', 'phase_time', 'phase_score', 'phase_type', 'dt_s',
           'phase_polarity', 'phase_amplitude', 'polarity_score', 'instrument_family',
           'usable_3c', 'outside_usable', 'amplitude_units', 'day']

def normalize(directory, archive, destination):
    doc, contract = load_contract(archive, 'preprocess')
    root = (contract.parent / doc['archive_root']).resolve()
    records, skipped = archive_records(root)
    lookup = {}
    for r in records:
        key = (r['trace_group'], r['date'])
        if key in lookup:
            raise ValueError('Ambiguous waveform identity mapping')
        lookup[key] = r
    files = sorted(Path(directory).rglob('*.csv'))
    if len(files) != len(records):
        raise ValueError(f'Expected one output (including zero-pick files) per group-day: {len(files)} != {len(records)}')
    tables = []
    for path in files:
        if path.stat().st_size == 0:
            continue
        try:
            frame = pd.read_csv(path, dtype={'station_id': str})
        except pd.errors.EmptyDataError:
            continue
        if frame.empty:
            continue
        required = {'station_id','phase_time','phase_score','phase_type','phase_amplitude','phase_polarity'}
        if required - set(frame):
            raise ValueError('Model output missing fields: ' + str(required - set(frame)))
        tables.append(frame)
    result = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame(columns=COLUMNS)
    if len(result):
        times = pd.to_datetime(result.phase_time, utc=True, errors='raise')
        if times.isna().any():
            raise ValueError('Missing pick timestamp')
        result['day'] = times.dt.strftime('%Y-%m-%d')
        result['phase_type'] = result.phase_type.str.upper()
        if not result.phase_type.isin(['P','S']).all():
            raise ValueError('Invalid phase type')
        for column in ['phase_score','phase_polarity','phase_amplitude']:
            result[column] = pd.to_numeric(result[column], errors='raise')
        if not np.isfinite(result.phase_score).all() or not result.phase_score.between(0,1).all():
            raise ValueError('Invalid picking probability')
        if not np.isfinite(result.phase_polarity).all() or not result.phase_polarity.between(-1,1).all():
            raise ValueError('Invalid polarity score')
        if not np.isfinite(result.phase_amplitude).all() or (result.phase_amplitude < 0).any():
            raise ValueError('Invalid velocity amplitude')
        indices = ((times - times.dt.normalize()).dt.total_seconds() * 100).round().astype('int64')
        flags, ids = [], []
        for sid, day, index in zip(result.station_id, result.day, indices):
            r = lookup.get((sid, day))
            if r is None:
                raise ValueError('Pick has no eligible archive group/day: ' + str((sid, day)))
            flags.append(any(a <= index < b for a,b in r['usable']))
            ids.append(r['group'])
        result['station_id'] = ids
        result['phase_index'] = indices
        result['phase_time'] = times.dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        result['instrument_family'] = result.station_id.str.split('.').str[-1]
        result['polarity_score'] = result.phase_polarity
        result['dt_s'] = 0.01
        result['usable_3c'] = flags
        result['outside_usable'] = ~result.usable_3c
        result['amplitude_units'] = 'm/s'
        if result.duplicated(['station_id','phase_time','phase_type']).any():
            raise ValueError('Duplicate normalized picks; do not silently concatenate repeated inference')
        result = result[COLUMNS].sort_values(['phase_time','station_id','phase_type']).reset_index(drop=True)
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Normalized picks already exist')
    result.to_csv(destination, index=False)
    receipt = {'group_days_processed': len(records), 'group_days_skipped': skipped,
               'raw_csv_files': len(files), 'n_picks': len(result),
               'outside_usable': int(result.outside_usable.sum()) if len(result) else 0,
               'amplitude_scale': 'linear', 'amplitude_units': 'm/s'}
    destination.with_suffix('.normalization.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return result, receipt
