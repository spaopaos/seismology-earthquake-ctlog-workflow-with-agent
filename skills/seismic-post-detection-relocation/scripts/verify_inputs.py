"""Independently verify joint-lite inputs: adapted CC against MESS, reused CT against round one."""
import csv
import json
from pathlib import Path
import bootstrap
import hypodd_inputs
from hypodd_inputs import utc, events, stations, differentials, check_bundle
from runtime_support import digest


def write(path, doc):
    Path(path).write_text(json.dumps(doc, indent=2, allow_nan=False) + '\n')


def verify_joint_lite_inputs(directory):
    """Re-derive event.dat, station.dat, dt.cc; confirm dt.ct is byte-identical to its source."""
    directory = Path(directory)
    meta = json.loads((directory/'conversion_meta.json').read_text())
    if meta.get('converter_sha256') != digest(Path(__file__).with_name('prepare_inputs.py')):
        raise ValueError('Inputs were not produced by the current maintained converter')
    if meta.get('method') != 'joint_lite_cc_ct' or meta.get('idat') != 3 or meta.get('ct_source') != 'first_round_reuse':
        raise ValueError('Inputs are not joint-lite (IDAT=3, first-round CT reuse)')
    source = json.loads((directory / 'source_files.json').read_text())
    for name, sha in source['files'].items():
        if digest(name) != sha:
            raise ValueError('Source observation changed: ' + name)
    if (directory / 'dt.ct').read_text() != Path(source['reused_dt_ct_path']).read_text():
        raise ValueError('Reused dt.ct is not byte-identical to its first-round source')
    aliases = json.loads((directory / 'station_aliases.json').read_text())['aliases']
    native = events(directory / 'event.dat')
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
    if not set(aliases).issubset(coords):
        raise ValueError('Native stations lack a MESS instrument-group alias')
    for alias, coord in coords.items():
        if alias in aliases:
            original = aliases[alias]['coordinates']
            if max(abs(coord[i]-original[key]) for i, key in enumerate(('latitude', 'longitude'))) > 0.000000051:
                raise ValueError('Native station coordinates differ from metadata')
    # CC adaptation: order/origin-time correction/weight must be re-derivable from MESS.
    source_cc = differentials(source['source_cc_path'], 'cc')
    with Path(source['source_catalog_path']).open(newline='') as stream:
        source_origins = {int(row['event_id']): utc(row['origin_time']) for row in csv.DictReader(stream)}
    template_origins = {}
    for f in csv.reader(Path(source['template_path']).read_text().splitlines()):
        if f and '_' in f[0]:
            template_origins[int(f[0].split('_')[0])] = utc(f[1])
    raw = {(p['a'], p['b'], o['station'], o['phase']): o for p in source_cc for o in p['observations']}
    table = events(directory / 'event.dat')
    adapted = differentials(directory / 'dt.cc', 'cc')
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
    # Reused CT: every pair/observation must reference prepared events and stations.
    reused = differentials(directory / 'dt.ct', 'ct')
    ct_count = 0
    for pair in reused:
        if not {pair['a'], pair['b']}.issubset(native):
            raise ValueError('Reused CT pair references an event outside the union table')
        for obs in pair['observations']:
            if obs['station'] not in coords:
                raise ValueError('Reused CT observation references an unprepared station')
        ct_count += len(pair['observations'])
    if meta.get('n_events') != len(native) or meta.get('n_cc_observations') != count or meta.get('n_ct_observations') != ct_count:
        raise ValueError('Conversion counts differ from verified native observations')
    names = ('dt.cc', 'dt.ct', 'event.dat', 'station.dat', 'joint_config.json', 'events.json',
             'station_aliases.json', 'source_files.json', 'cc_adaptation.json', 'ct_reuse.json',
             'conversion_meta.json')
    receipt = {'status': 'PASS', 'method': 'joint_lite_cc_ct', 'ct_source': 'first_round_reuse',
               'measured': check_bundle(directory),
               'input_sha256': {name: digest(directory/name) for name in names},
               'source_files': [{'path': p, 'sha256': h} for p, h in source['files'].items()],
               'validator_sha256': digest(hypodd_inputs.__file__),
               'source_verifier_sha256': digest(__file__)}
    write(directory/'joint_verification.json', receipt)
    return receipt
