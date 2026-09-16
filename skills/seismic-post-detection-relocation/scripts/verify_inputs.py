"""Independently compare native input times with their original source measurements."""
import csv
import json
from pathlib import Path
import bootstrap
import hypodd_inputs
from hypodd_inputs import utc, events, stations, differentials, check_bundle, joint_schedule
from runtime_support import digest


def write(path, doc):
    Path(path).write_text(json.dumps(doc, indent=2, allow_nan=False) + '\n')


def verify_phases(directory):
    directory = Path(directory)
    meta = json.loads((directory/'conversion_meta.json').read_text())
    if meta.get('converter_sha256') != digest(Path(__file__).with_name('prepare_inputs.py')):
        raise ValueError('Inputs were not produced by the current maintained converter')
    source = json.loads((directory / 'source_files.json').read_text())
    for name, sha in source['files'].items():
        if digest(name) != sha:
            raise ValueError('Source observation changed: ' + name)
    with Path(source['picking_path']).open(newline='') as stream:
        picks = list(csv.DictReader(stream))
    aliases = json.loads((directory / 'station_aliases.json').read_text())['aliases']
    native = events(directory / 'events.native')
    truth = json.loads((directory / 'events.json').read_text())
    if set(native) != set(map(int, truth)):
        raise ValueError('Native and source event sets differ')
    for eid, e in native.items():
        r = truth[str(eid)]
        if utc(e['origin_time']) != utc(r['solver_origin_time']):
            raise ValueError('Native source origin mismatch')
        for field, tolerance in (('latitude', 0.00000051), ('longitude', 0.00000051), ('depth_km', 0.00051)):
            if abs(e[field]-float(r[field])) > tolerance:
                raise ValueError('Native source coordinate mismatch')
    coords = stations(directory / 'station.dat')
    if set(coords) != set(aliases):
        raise ValueError('Station aliases differ from native stations')
    for alias, coord in coords.items():
        original = aliases[alias]['coordinates']
        if max(abs(coord[i]-original[key]) for i, key in enumerate(('latitude', 'longitude'))) > 0.000000051:
            raise ValueError('Native station coordinates differ from metadata')
    observed = json.loads((directory / 'observations.json').read_text())
    expected, used_picks = {}, set()
    config = joint_schedule(directory / 'joint_config.json')
    for obs in observed:
        key = (int(obs['event_id']), obs['station'], obs['phase'])
        row_number = obs['pick_row']
        if type(row_number) is not int or not 0 <= row_number < len(picks) or row_number in used_picks or key in expected:
            raise ValueError('Duplicate/invalid independent pick reference')
        used_picks.add(row_number)
        raw = picks[row_number]
        if (raw['station_id'] != obs['group'] or obs['group'] not in aliases[obs['station']]['groups']
                or raw['phase_type'] != obs['phase'] or utc(raw['phase_time']) != utc(obs['phase_time'])
                or str(raw.get('usable_3c', '')).lower() != 'true'):
            raise ValueError('CT observation is not the identified independent PhaseNet pick')
        score = float(raw['phase_score'])
        weight = 1.0 if score >= .5 else .5 if score >= .4 else .2 if score >= .3 else 0.
        if score < config['min_pick_probability'] or obs['weight'] != weight or weight <= 0:
            raise ValueError('CT weight differs from independent pick probability')
        if abs((utc(raw['phase_time'])-utc(obs['hint_time'])).total_seconds()) > config['match_window_s'][obs['phase']] + 1e-6:
            raise ValueError('CT pick falls outside declared matching window')
        tt = (utc(raw['phase_time'])-utc(native[key[0]]['origin_time'])).total_seconds()
        if not 0 < tt < 600:
            raise ValueError('Invalid independent travel time')
        expected[key] = (tt, weight)
    parsed, header_ids, current = {}, set(), None
    for line in (directory / 'phase.dat').read_text().splitlines():
        f = line.split()
        if not f:
            continue
        if f[0] == '#':
            if len(f) != 15:
                raise ValueError('Invalid ph2dt header')
            current = int(f[-1])
            if current in header_ids or current not in native:
                raise ValueError('Invalid ph2dt event identity')
            header_ids.add(current)
            from datetime import datetime, timedelta, timezone
            t = datetime(*map(int, f[1:6]), tzinfo=timezone.utc) + timedelta(seconds=float(f[6]))
            if t != utc(native[current]['origin_time']):
                raise ValueError('ph2dt origin differs from joint event origin')
            for field, value, tol in zip(('latitude', 'longitude', 'depth_km'), f[7:10], (5.1e-7, 5.1e-7, .00051)):
                if abs(float(value)-native[current][field]) > tol:
                    raise ValueError('ph2dt header coordinate mismatch')
        else:
            if len(f) != 4 or current is None:
                raise ValueError('Invalid ph2dt phase row')
            key = (current, f[0], f[3])
            if key in parsed or key not in expected:
                raise ValueError('Duplicate or unsupported ph2dt observation')
            tt, weight = map(float, f[1:3])
            if abs(tt-expected[key][0]) > 5.1e-7 or abs(weight-expected[key][1]) > 5.1e-4:
                raise ValueError('ph2dt travel time differs from original independent pick')
            parsed[key] = (tt, weight)
    if set(parsed) != set(expected) or header_ids != set(native):
        raise ValueError('Independent observations omitted/added in ph2dt inputs')
    if meta.get('n_events') != len(native) or meta.get('n_phase_lines') != len(parsed):
        raise ValueError('Conversion counts differ from verified native observations')
    receipt = {'status': 'PASS', 'n_events': len(native), 'n_phase_lines': len(parsed),
               'phase_dat_sha256': digest(directory/'phase.dat'), 'errors': [], 'warnings': [],
               'verifier_sha256': digest(__file__)}
    write(directory/'ph2dt_input_verification.json', receipt)
    return expected


def verify_joint(directory, pairing_receipt=None):
    directory = Path(directory)
    expected = verify_phases(directory)
    if (directory/'event.dat').read_bytes() != (directory/'events.native').read_bytes():
        raise ValueError('Joint event union was replaced by the CT-selected subset')
    measured = check_bundle(directory)
    for pair in differentials(directory/'dt.ct', 'ct'):
        for obs in pair['observations']:
            for eid, tt in zip((pair['a'], pair['b']), obs['times']):
                key = (eid, obs['station'], obs['phase'])
                if key not in expected or abs(tt-expected[key][0]) > .00051:
                    raise ValueError('CT differential not backed by independent arrivals')
            weights = [expected[(eid, obs['station'], obs['phase'])][1] for eid in (pair['a'], pair['b'])]
            if abs(obs['weight']-sum(weights)/2) > .000051:
                raise ValueError('ph2dt pair weight differs from original pick weights')
    sources = json.loads((directory/'source_files.json').read_text())
    source_cc = differentials(sources['source_cc_path'], 'cc')
    with Path(sources['source_catalog_path']).open(newline='') as stream:
        source_origins = {int(row['event_id']): utc(row['origin_time']) for row in csv.DictReader(stream)}
    template_origins = {}
    for f in csv.reader(Path(sources['template_path']).read_text().splitlines()):
        if f and '_' in f[0]:
            template_origins[int(f[0].split('_')[0])] = utc(f[1])
    raw = {(p['a'], p['b'], o['station'], o['phase']): o for p in source_cc for o in p['observations']}
    table = events(directory/'event.dat')
    aliases = json.loads((directory/'station_aliases.json').read_text())['aliases']
    adapted = differentials(directory/'dt.cc', 'cc')
    count = 0
    for pair in adapted:
        a, b = pair['a'], pair['b']
        for obs in pair['observations']:
            site = aliases[obs['station']]['site_id'].split('.')[1]
            key = (a, b, site, obs['phase'])
            original = raw.get(key)
            if original is None:
                raise ValueError('CC observation has no MESS source')
            # Independently express the adjustment as elapsed origin differences.
            old_separation = (source_origins[a]-template_origins[b]).total_seconds()
            new_separation = (utc(table[a]['origin_time'])-utc(table[b]['origin_time'])).total_seconds()
            dt = original['times'][0]+old_separation-new_separation
            if abs(obs['times'][0]-dt) > 2e-7 or obs['weight'] != original['weight']:
                raise ValueError('CC order/origin correction/weight mismatch')
            count += 1
    if count != len(raw):
        raise ValueError('CC adaptation omitted original observations')
    names = ('dt.cc', 'dt.ct', 'event.dat', 'station.dat', 'joint_config.json', 'phase.dat',
             'observations.json', 'events.json', 'station_aliases.json', 'source_files.json',
             'cc_adaptation.json', 'conversion_meta.json')
    source_files = [{'path': p, 'sha256': h} for p, h in sources['files'].items()]
    if pairing_receipt:
        source_files.append({'path': str(Path(pairing_receipt).resolve()), 'sha256': digest(pairing_receipt)})
    receipt = {'status': 'PASS', 'measured': measured, 'ct_source': 'independent_phasenet',
               'input_sha256': {name: digest(directory/name) for name in names},
               'source_files': source_files, 'validator_sha256': digest(hypodd_inputs.__file__),
               'source_verifier_sha256': digest(__file__)}
    write(directory/'joint_verification.json', receipt)
    return receipt
