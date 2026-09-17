"""Strict, independent parsers for HypoDD CC/CT bundles and joint schedules."""
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from runtime_support import digest


def utc(value):
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('UTC offset required: ' + str(value))
    return result.astimezone(timezone.utc)


def finite(values):
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError('Nonfinite native input')


def events(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        f = line.split()
        if len(f) != 10:
            raise ValueError('Expected ten event.dat fields')
        eid = int(f[-1])
        if not 0 < eid <= 999999999 or eid in result:
            raise ValueError('Duplicate/invalid event ID')
        finite(f[2:9])
        clock = f[1].zfill(8)
        if len(clock) != 8:
            raise ValueError('Expected HHMMSScc native origin time')
        t = datetime.strptime(f[0] + clock[:4], '%Y%m%d%H%M').replace(tzinfo=timezone.utc)
        t += timedelta(seconds=int(clock[4:6]), milliseconds=int(clock[6:])*10)
        lat, lon, dep = map(float, f[2:5])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and dep >= 0):
            raise ValueError('Invalid coordinates or unsupported negative native depth')
        result[eid] = {'origin_time': t.isoformat(), 'latitude': lat, 'longitude': lon, 'depth_km': dep}
    return result


def stations(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if not f:
            continue
        if len(f) != 3 or len(f[0]) > 7 or f[0] in result:
            raise ValueError('Invalid/duplicate station record')
        lat, lon = map(float, f[1:]); finite([lat, lon])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError('Invalid station coordinate')
        result[f[0]] = (lat, lon)
    return result


def differentials(path, kind):
    if kind not in ('cc', 'ct'):
        raise ValueError('Unknown differential type')
    pairs, current, seen = [], None, set()
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        f = line.split()
        if not f:
            continue
        if f[0] == '#':
            if len(f) != (4 if kind == 'cc' else 3):
                raise ValueError('Invalid differential header at line ' + str(number))
            a, b = int(f[1]), int(f[2]); key = tuple(sorted((a, b)))
            if a == b or min(a, b) <= 0 or key in seen:
                raise ValueError('Duplicate/self/invalid differential pair')
            seen.add(key)
            otc = float(f[3]) if kind == 'cc' else 0.0
            finite([otc])
            if otc != 0:
                raise ValueError('Only common-origin OTC=0 bundles are supported')
            current = {'a': a, 'b': b, 'observations': []}
            pairs.append(current)
        else:
            if current is None or len(f) != (4 if kind == 'cc' else 5):
                raise ValueError('Invalid differential observation at line ' + str(number))
            numbers = list(map(float, f[1:-1])); finite(numbers)
            if f[-1] not in ('P', 'S') or not 0 < numbers[-1] <= 1:
                raise ValueError('Invalid phase/weight')
            if kind == 'ct' and not all(0 < v < 600 for v in numbers[:-1]):
                raise ValueError('Invalid CT travel time')
            obs = {'station': f[0], 'phase': f[-1], 'times': numbers[:-1], 'weight': numbers[-1]}
            if any((o['station'], o['phase']) == (obs['station'], obs['phase']) for o in current['observations']):
                raise ValueError('Duplicate event-pair/station/phase observation')
            current['observations'].append(obs)
    if any(not p['observations'] for p in pairs):
        raise ValueError('Empty differential pair block')
    return pairs


def check_bundle(directory, require_both=True):
    directory = Path(directory)
    event_table = events(directory / 'event.dat')
    station_table = stations(directory / 'station.dat')
    counts, per_event = {}, {str(e): {'cc': 0, 'ct': 0} for e in event_table}
    for kind in ('cc', 'ct'):
        pairs = differentials(directory / ('dt.' + kind), kind)
        counts[kind] = sum(len(p['observations']) for p in pairs)
        counts[kind + '_pairs'] = len(pairs)
        for pair in pairs:
            if not {pair['a'], pair['b']}.issubset(event_table):
                raise ValueError('Unknown event in dt.' + kind)
            for obs in pair['observations']:
                if obs['station'] not in station_table:
                    raise ValueError('Unknown station in dt.' + kind)
            for eid in (pair['a'], pair['b']):
                per_event[str(eid)][kind] += len(pair['observations'])
    if require_both and (not counts['cc'] or not counts['ct']):
        raise ValueError('Joint solving requires nonempty CC AND CT observations')
    return {'counts': counts, 'per_event': per_event, 'events': len(event_table), 'stations': len(station_table)}


def verify_joint_receipt(directory):
    directory = Path(directory)
    receipt = json.loads((directory / 'joint_verification.json').read_text())
    required = {'dt.cc', 'dt.ct', 'event.dat', 'station.dat', 'joint_config.json'}
    if receipt.get('status') != 'PASS' or not required.issubset(receipt.get('input_sha256', {})):
        raise ValueError('Missing independent joint input verification')
    for name, expected in receipt['input_sha256'].items():
        if digest(directory / name) != expected:
            raise ValueError('Joint input changed after verification: ' + name)
    if receipt.get('validator_sha256') != digest(__file__):
        raise ValueError('Joint validator changed; create a new run')
    verifier = Path(__file__).resolve().parent.parent/'skills/seismic-post-detection-relocation/scripts/verify_inputs.py'
    if receipt.get('source_verifier_sha256') != digest(verifier):
        raise ValueError('Independent source verifier changed; create a new run')
    for record in receipt.get('source_files', []):
        if digest(record['path']) != record['sha256']:
            raise ValueError('Source observations changed after joint verification')
    measured = check_bundle(directory)
    if measured != receipt.get('measured'):
        raise ValueError('Joint observation evidence differs from native inputs')
    return receipt


def joint_schedule(path):
    doc = json.loads(Path(path).read_text())
    if doc.get('idat') != 3 or doc.get('ipha') != 3 or doc.get('ct_source') not in (
            'independent_phasenet', 'first_round_reuse'):
        raise ValueError('Joint mode requires IDAT=3, IPHA=3 and a known CT source')
    if doc['ct_source'] == 'independent_phasenet':
        if not .3 <= float(doc.get('min_pick_probability', 0)) <= 1:
            raise ValueError('Independent picking probability must be in [0.3,1]')
        if set(doc.get('match_window_s', {})) != {'P', 'S'} or any(
                not 0 < float(v) <= 10 for v in doc['match_window_s'].values()):
            raise ValueError('Explicit finite P/S matching windows in (0,10] seconds required')
    for key in ('obscc', 'obsct'):
        if type(doc.get(key)) is not int or doc[key] < 0:
            raise ValueError('Invalid joint clustering threshold')
    if doc['obscc'] + doc['obsct'] <= 0:
        raise ValueError('Positive effective joint link threshold required')
    rows = doc.get('iterations', [])
    if not rows:
        raise ValueError('Explicit joint iteration schedule required')
    columns = ('wtccp', 'wtccs', 'wrcc', 'wdcc', 'wtctp', 'wtcts', 'wrct', 'wdct')
    for row in rows:
        if type(row.get('niter')) is not int or row['niter'] <= 0:
            raise ValueError('Invalid joint iteration count')
        finite([row[k] for k in columns])
        for k in ('wtccp', 'wtccs', 'wtctp', 'wtcts'):
            if not 0 < row[k] <= 1:
                raise ValueError('Both CC and CT weights must remain positive in each iteration set')
        for k in ('wrcc', 'wdcc', 'wrct', 'wdct'):
            if row[k] != -9 and row[k] <= 0:
                raise ValueError('Cutoffs must be positive or -9')
    return doc
