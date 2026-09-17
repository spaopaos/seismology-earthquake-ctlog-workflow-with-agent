"""MESS-native CC plus the verbatim first-round dt.ct -> joint HypoDD inputs (IDAT=3, lite)."""
import csv
import json
from collections import defaultdict
from pathlib import Path

import bootstrap
from hypodd_inputs import utc, events as native_events, stations as parse_stations, differentials, finite
from runtime_support import digest
from station_identity import native_mapping, save_mapping

LABELS = ('cc_0p4', 'cc_0p6', 'cc_0p8')


def read_csv(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def template_events(path):
    """Reference-event coordinates from the MESS template export; hint lines are ignored."""
    result = {}
    for f in csv.reader(Path(path).read_text().splitlines()):
        if not f or '_' not in f[0]:
            continue
        eid = int(f[0].split('_')[0])
        if eid in result:
            raise ValueError('Duplicate template event')
        result[eid] = {'event_id': eid, 'origin_time': utc(f[1]).isoformat(),
                       'latitude': float(f[2]), 'longitude': float(f[3]), 'depth_km': float(f[4])}
    return result


def native_origin(value):
    t = utc(value)
    return t.replace(microsecond=(t.microsecond // 10000)*10000)


def corrected_cc(dt, source_first, source_second, target_first, target_second):
    """D=(arrival1-origin1)-(arrival2-origin2), preserving event order."""
    return (float(dt) + (utc(source_first)-utc(target_first)).total_seconds()
            - (utc(source_second)-utc(target_second)).total_seconds())


def load_ct_reuse(source):
    """First-round ph2dt dt.ct/event.dat/station.dat, hash-tied to the saved solver context."""
    source = {k: Path(v).resolve() for k, v in source.items()}
    for key in ('dt_ct_path', 'event_dat_path', 'station_dat_path', 'selection_path', 'tier_dir'):
        if key not in source:
            raise ValueError('Incomplete first-round CT reuse source: missing ' + key)
    selection = json.loads(source['selection_path'].read_text())
    recorded = selection.get('context', {}).get('input_sha256', {})
    for local, key in (('dt_ct_path', 'dt.ct'), ('event_dat_path', 'event.dat'), ('station_dat_path', 'station.dat')):
        if key not in recorded:
            raise ValueError('First-round solver context does not record ' + key)
        if digest(source[local]) != recorded[key]:
            raise ValueError('First-round ' + key + ' differs from its verified solver evidence')
    raw_events = {eid: line for eid, line in
                  ((int(line.split()[-1]), line) for line in source['event_dat_path'].read_text().splitlines() if line.strip())}
    parsed_events = native_events(source['event_dat_path'])
    if set(raw_events) != set(parsed_events):
        raise ValueError('First-round event table is not one-line-one-event')
    pairs = differentials(source['dt_ct_path'], 'ct')
    referenced = set()
    for pair in pairs:
        referenced.update((pair['a'], pair['b']))
    if not referenced.issubset(set(raw_events)):
        raise ValueError('Reused dt.ct references events missing from the first-round table')
    reused_stations = parse_stations(source['station_dat_path'])
    return {'paths': source, 'dt_ct_text': source['dt_ct_path'].read_text(), 'pairs': pairs,
            'referenced': referenced, 'raw_events': raw_events, 'events': parsed_events,
            'stations': reused_stations, 'n_observations': sum(len(p['observations']) for p in pairs)}


def build_master(catalog_root, documents, stations_path, ct_reuse):
    """Three-tier MESS event tables, CC sources, and the verified first-round CT bundle."""
    catalog_root = Path(catalog_root)
    doc = documents['cc_0p4']
    base = catalog_root / 'cc_0p4'
    artifact = lambda key: (base / doc['artifacts'][key]['path']).resolve()
    template_path = artifact('source_templates')
    source_catalog_path = artifact('source_catalog')
    source_origins = {int(r['event_id']): utc(r['origin_time']).isoformat() for r in read_csv(source_catalog_path)}
    templates = template_events(template_path)
    view_path = template_path.parent / 'continuous_manifest.json'
    snapshot_path = artifact('source_template_source_snapshot')
    snapshot = json.loads(snapshot_path.read_text())
    if digest(view_path) != snapshot['view_sha256']:
        raise ValueError('Selected instrument mapping differs from MESS snapshot')
    groups = json.loads(view_path.read_text())['selected_groups']
    alias_by_group, aliases = native_mapping(stations_path, groups.values())
    physical_alias = {physical: alias_by_group[group] for physical, group in groups.items()}
    bare = defaultdict(set)
    for physical, alias in physical_alias.items():
        bare[physical.split('.', 1)[1]].add(alias)
    if any(len(values) != 1 for values in bare.values()):
        raise ValueError('Ambiguous bare MESS CC station across networks; cannot recover its identity')
    bare_alias = {key: next(iter(value)) for key, value in bare.items()}
    rows_by_label, ids_by_label, all_events, sources = {}, {}, {}, {}
    for label in LABELS:
        current = documents[label]
        paths = {key: (catalog_root / label / current['outputs'][key]).resolve()
                 for key in ('detections_path', 'event_path', 'dt_cc_path', 'reference_events_path')}
        rows = read_csv(paths['detections_path'])
        rows_by_label[label] = rows
        ids = {int(row['event_id']) for row in rows}
        if len(ids) != len(rows):
            raise ValueError('Duplicate detection ID')
        refs = set(json.loads(paths['reference_events_path'].read_text())['event_ids'])
        native = native_events(paths['event_path'])
        if set(native) != ids | refs:
            raise ValueError('MESS native/reference IDs disagree')
        manifest_path = (catalog_root / label / current['artifacts']['source_scan_manifest']['path']).resolve()
        manifest = json.loads(manifest_path.read_text())
        offset = float(manifest['hypodd_depth_offset_km']); finite([offset])
        for row in rows:
            eid = int(row['event_id'])
            record = {**row, 'event_id': eid, 'role': 'detection',
                      'latitude': float(row['latitude']), 'longitude': float(row['longitude']),
                      'depth_km': float(row['depth_km']), 'origin_time': utc(row['origin_time']).isoformat()}
            if eid in all_events and all_events[eid].get('role') == 'detection' and all_events[eid] != record:
                raise ValueError('Common detection fields differ across CC catalogs')
            all_events[eid] = record
        for eid in refs:
            if eid not in all_events:
                if eid not in templates:
                    raise ValueError('Missing reference template')
                all_events[eid] = dict(templates[eid])
                all_events[eid]['role'] = 'template_reference'
        for eid in ids | refs:
            expected = all_events[eid] if eid in ids else templates[eid]
            if abs(native[eid]['depth_km'] - float(expected['depth_km']) - offset) > 0.00051:
                raise ValueError('MESS depth offset disagrees with its source coordinates')
            if abs((utc(native[eid]['origin_time'])-utc(expected['origin_time'])).total_seconds()) > 0.01001:
                raise ValueError('MESS native origin differs from its source event')
        ids_by_label[label] = ids | refs
        sources[label] = paths
    for event in all_events.values():
        if float(event['depth_km']) < 0:
            raise ValueError('Negative sea-level initial depth unsupported by current native solver')
        event['solver_origin_time'] = native_origin(event['origin_time']).isoformat()
    reused = load_ct_reuse(ct_reuse)
    # Catalog events that only enter via the reused dt.ct keep their first-round native rows verbatim.
    shared = set(all_events) & set(reused['events'])
    for eid in shared:
        first = reused['events'][eid]
        mine = all_events[eid]
        if (abs(first['latitude']-float(mine['latitude'])) > 0.01001 or abs(first['longitude']-float(mine['longitude'])) > 0.01001
                or abs(first['depth_km']-float(mine['depth_km'])) > 0.1001):
            raise ValueError('Event present in both MESS and first-round tables with different coordinates: ' + str(eid))
    for eid in reused['referenced'] - set(all_events):
        row = dict(reused['events'][eid])
        row['role'] = 'first_round_catalog'
        row['solver_origin_time'] = row['origin_time']
        all_events[eid] = row
    for alias, coord in reused['stations'].items():
        if alias in aliases:
            known = aliases[alias]['coordinates']
            if max(abs(coord[0]-known['latitude']), abs(coord[1]-known['longitude'])) > 0.000000051:
                raise ValueError('First-round station alias collides with a different coordinate: ' + alias)
    source_files = {str(Path(p).resolve()): digest(p) for p in
                    [stations_path, template_path, view_path, snapshot_path, source_catalog_path]}
    for paths in sources.values():
        source_files.update({str(p): digest(p) for p in paths.values()})
    source_files.update({str(ct_reuse[k]): digest(ct_reuse[k]) for k in ('dt_ct_path', 'event_dat_path', 'station_dat_path', 'selection_path')})
    return {'events': all_events, 'templates': templates, 'ids_by_label': ids_by_label,
            'rows_by_label': rows_by_label, 'sources': sources, 'aliases': aliases,
            'bare_alias': bare_alias, 'source_files': source_files, 'reused': reused,
            'template_path': str(Path(template_path).resolve()),
            'source_origins': source_origins, 'source_catalog_path': str(Path(source_catalog_path).resolve())}


def event_line(eid, event):
    t = utc(event['solver_origin_time'])
    return (f"{t:%Y%m%d} {t:%H%M%S}{t.microsecond//10000:02d} "
            f"{event['latitude']:.6f} {event['longitude']:.6f} {event['depth_km']:.3f} "
            f"0.0 0.0 0.0 0.0 {eid}\n")


def prepare_tier(master, label, directory, settings):
    """Joint lite inputs: MESS dt.cc (adapted) + first-round dt.ct (verbatim), union event.dat."""
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Joint lite input directory must be fresh')
    directory.mkdir(parents=True, exist_ok=True)
    ids = master['ids_by_label'][label] | master['reused']['referenced']
    event_table = {eid: dict(master['events'][eid]) for eid in sorted(ids)}
    selected_ids = {int(r['event_id']) for r in master['rows_by_label'][label]}
    for eid in event_table:
        if eid in selected_ids:
            event_table[eid]['role'] = 'detection'
        elif event_table[eid].get('role') not in ('first_round_catalog',):
            event_table[eid]['role'] = 'template_reference'
    write_json(directory / 'events.json', {str(e): r for e, r in event_table.items()})
    write_json(directory / 'source_files.json', {'files': master['source_files'],
               'template_path': master['template_path'],
               'source_cc_path': str(master['sources'][label]['dt_cc_path']),
               'source_catalog_path': master['source_catalog_path'],
               'reused_dt_ct_path': str(master['reused']['paths']['dt_ct_path'])})
    save_mapping(directory / 'station_aliases.json', master['aliases'])
    reused_station_lines = []
    for alias, coord in master['reused']['stations'].items():
        if alias not in master['aliases']:
            reused_station_lines.append(f"{alias} {coord[0]:.7f} {coord[1]:.7f}\n")
    (directory / 'station.dat').write_text(''.join(
        f"{alias} {record['coordinates']['latitude']:.7f} {record['coordinates']['longitude']:.7f}\n"
        for alias, record in sorted(master['aliases'].items())) + ''.join(sorted(reused_station_lines)))
    lines = []
    for eid, row in event_table.items():
        if row.get('role') == 'first_round_catalog':
            lines.append(master['reused']['raw_events'][eid])
            if not lines[-1].endswith('\n'):
                lines[-1] += '\n'
        else:
            lines.append(event_line(eid, row))
    (directory / 'event.dat').write_text(''.join(lines))
    cc, audit = [], []
    for pair in differentials(master['sources'][label]['dt_cc_path'], 'cc'):
        a, b = pair['a'], pair['b']
        if not {a, b}.issubset(master['ids_by_label'][label]) or b not in master['templates']:
            raise ValueError('CC pair lacks its original template reference')
        cc.append(f'# {a} {b} 0.0\n')
        for obs in pair['observations']:
            if obs['station'] not in master['bare_alias']:
                raise ValueError('Unknown bare MESS CC station')
            target = master['bare_alias'][obs['station']]
            value = corrected_cc(obs['times'][0], master['source_origins'][a],
                                 master['templates'][b]['origin_time'], event_table[a]['solver_origin_time'],
                                 event_table[b]['solver_origin_time'])
            cc.append(f"{target} {value:.7f} {obs['weight']:.4f} {obs['phase']}\n")
            audit.append({'a': a, 'b': b, 'station': target, 'source_station': obs['station'],
                          'phase': obs['phase'], 'source_dt': obs['times'][0], 'dt': value,
                          'source_origin_a': master['source_origins'][a],
                          'source_origin_b': master['templates'][b]['origin_time'], 'weight': obs['weight']})
    (directory / 'dt.cc').write_text(''.join(cc))
    write_json(directory / 'cc_adaptation.json', audit)
    (directory / 'dt.ct').write_text(master['reused']['dt_ct_text'])
    write_json(directory / 'ct_reuse.json', {'tier': master['reused']['paths']['tier_dir'].name,
                'n_pairs': len(master['reused']['pairs']),
                'n_observations': master['reused']['n_observations'],
                'referenced_events': sorted(master['reused']['referenced']),
                'note': 'First-round ph2dt dt.ct reused verbatim; byte-identical to its solver-verified source.'})
    write_json(directory / 'joint_config.json', {'idat': 3, 'ipha': 3, 'ct_source': 'first_round_reuse',
                'obscc': settings['obscc'], 'obsct': settings['obsct'], 'iterations': settings['iterations']})
    write_json(directory / 'conversion_meta.json', {'n_events': len(ids), 'n_cc_observations': len(audit),
                'n_ct_observations': master['reused']['n_observations'],
                'converter_sha256': digest(__file__), 'method': 'joint_lite_cc_ct', 'idat': 3,
                'ct_source': 'first_round_reuse',
                'depth_reference': 'sea_level', 'solver_depth_offset_km': 0,
                'magnitude_and_error_placeholders': 'native input zeros are unset, not measured magnitudes/errors'})
    return {'events': len(ids), 'cc_observations': len(audit), 'ct_observations': master['reused']['n_observations']}
