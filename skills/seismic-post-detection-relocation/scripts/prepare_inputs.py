"""MESS CC plus independent PhaseNet arrivals -> reversible joint native inputs."""
import bisect
import csv
import json
from collections import defaultdict
from pathlib import Path

import bootstrap
from hypodd_inputs import utc, events as native_events, differentials, finite
from runtime_support import digest
from station_identity import native_mapping, save_mapping
from make_ph2dt_inputs import prob_to_weight

LABELS = ('cc_0p4', 'cc_0p6', 'cc_0p8')


def read_csv(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def phase_hints(path, template=False):
    result, current = {}, None
    for f in csv.reader(Path(path).read_text().splitlines()):
        if not f:
            continue
        if (template and '_' in f[0]) or (not template and f[0][:4].isdigit()):
            eid = int(f[0].split('_')[0]) if template else int(f[5])
            if eid in result:
                raise ValueError('Duplicate phase/template event')
            current = {'hints': []}
            if template:
                current.update(event_id=eid, origin_time=utc(f[1]).isoformat(),
                               latitude=float(f[2]), longitude=float(f[3]), depth_km=float(f[4]))
            result[eid] = current
        else:
            if current is None or len(f) < 3:
                raise ValueError('Phase hint without event')
            for i, phase in ((1, 'P'), (2, 'S')):
                if f[i] and f[i] != '-1':
                    current['hints'].append({'physical': f[0], 'phase': phase, 'time': utc(f[i]).isoformat()})
    return result


def native_origin(value):
    t = utc(value)
    return t.replace(microsecond=(t.microsecond // 10000)*10000)


def corrected_cc(dt, source_first, source_second, target_first, target_second):
    """D=(arrival1-origin1)-(arrival2-origin2), preserving event order."""
    return (float(dt) + (utc(source_first)-utc(target_first)).total_seconds()
            - (utc(source_second)-utc(target_second)).total_seconds())


def match_independent(picks, targets, groups, settings):
    """Unique independent arrivals only; never substitute MESS times for missing picks."""
    index = defaultdict(list)
    min_prob = float(settings['min_pick_probability'])
    for row_number, row in enumerate(picks):
        score = float(row['phase_score'])
        if not (0 <= score <= 1):
            raise ValueError('Invalid independent picking probability')
        if (row['station_id'] not in set(groups.values()) or row['phase_type'] not in ('P', 'S')
                or str(row.get('usable_3c', '')).lower() != 'true' or score < min_prob):
            continue
        index[(row['station_id'], row['phase_type'])].append((utc(row['phase_time']).timestamp(), row_number))
    for key in index:
        index[key].sort()
    candidates, excluded = [], []
    for eid, hints in sorted(targets.items()):
        seen = set()
        for hint in hints:
            group = groups.get(hint['physical'])
            key = (group, hint['phase'])
            if group is None or key in seen:
                raise ValueError('Unresolved/duplicate event station phase hint')
            seen.add(key)
            expected = utc(hint['time']).timestamp()
            window = float(settings['match_window_s'][hint['phase']])
            if not 0 < window <= 10:
                raise ValueError('Explicit matching window must be in (0,10] s')
            values = index[key]
            found = values[bisect.bisect_left(values, (expected-window, -1)):
                           bisect.bisect_right(values, (expected+window, len(picks)))]
            audit = {'event_id': eid, 'group': group, 'phase': hint['phase'], 'hint_time': hint['time']}
            if len(found) != 1:
                excluded.append({**audit, 'reason': 'NO_INDEPENDENT_PICK' if not found else 'AMBIGUOUS_INDEPENDENT_PICKS',
                                 'candidate_rows': [i for _, i in found]})
                continue
            measured, row_number = found[0]
            row = picks[row_number]
            weight = prob_to_weight(float(row['phase_score']))
            if weight <= 0:
                excluded.append({**audit, 'reason': 'ZERO_PICK_WEIGHT'})
                continue
            candidates.append({**audit, 'pick_row': row_number, 'phase_time': row['phase_time'],
                               'phase_score': float(row['phase_score']), 'weight': weight,
                               'match_delta_s': measured-expected})
    claims = defaultdict(list)
    for obs in candidates:
        claims[obs['pick_row']].append(obs['event_id'])
    accepted = []
    for obs in candidates:
        if len(claims[obs['pick_row']]) > 1:
            excluded.append({**obs, 'reason': 'PICK_CLAIMED_BY_MULTIPLE_EVENTS', 'claiming_events': claims[obs['pick_row']]})
        else:
            accepted.append(obs)
    return accepted, excluded


def build_master(catalog_root, documents, picking_path, stations_path, settings):
    catalog_root = Path(catalog_root)
    doc = documents['cc_0p4']
    base = catalog_root / 'cc_0p4'
    artifact = lambda key: (base / doc['artifacts'][key]['path']).resolve()
    template_path = artifact('source_templates')
    source_catalog_path = artifact('source_catalog')
    source_origins = {int(r['event_id']): utc(r['origin_time']).isoformat() for r in read_csv(source_catalog_path)}
    templates = phase_hints(template_path, True)
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
                 for key in ('detections_path', 'phase_path', 'event_path', 'dt_cc_path', 'reference_events_path')}
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
                all_events[eid] = {k: v for k, v in templates[eid].items() if k != 'hints'}
                all_events[eid]['role'] = 'template_reference'
        for eid in ids | refs:
            expected = all_events[eid] if eid in ids else templates[eid]
            if abs(native[eid]['depth_km'] - float(expected['depth_km']) - offset) > 0.00051:
                raise ValueError('MESS depth offset disagrees with its source coordinates')
            if abs((utc(native[eid]['origin_time'])-utc(expected['origin_time'])).total_seconds()) > 0.01001:
                raise ValueError('MESS native origin differs from its source event')
        ids_by_label[label] = ids | refs
        sources[label] = paths
    targets = {}
    low_hints = phase_hints(sources['cc_0p4']['phase_path'])
    for eid, event in all_events.items():
        if float(event['depth_km']) < 0:
            raise ValueError('Negative sea-level initial depth unsupported by current native solver')
        event['solver_origin_time'] = native_origin(event['origin_time']).isoformat()
        hints = low_hints[eid]['hints'] if eid in low_hints else templates[eid]['hints']
        targets[eid] = hints
    picks = read_csv(picking_path)
    accepted, excluded = match_independent(picks, targets, groups, settings)
    good = []
    for obs in accepted:
        tt = (utc(obs['phase_time']) - utc(all_events[obs['event_id']]['solver_origin_time'])).total_seconds()
        if not 0 < tt < 600:
            excluded.append({**obs, 'reason': 'INVALID_TRAVEL_TIME'})
            continue
        good.append({**obs, 'station': alias_by_group[obs['group']], 'travel_time_s': tt})
    source_files = {str(Path(p).resolve()): digest(p) for p in
                    [picking_path, stations_path, template_path, view_path, snapshot_path, source_catalog_path]}
    for paths in sources.values():
        source_files.update({str(p): digest(p) for p in paths.values()})
    return {'events': all_events, 'templates': templates, 'observations': good, 'excluded': excluded,
            'ids_by_label': ids_by_label, 'sources': sources, 'rows_by_label': rows_by_label,
            'aliases': aliases, 'bare_alias': bare_alias, 'source_files': source_files,
            'picking_path': str(Path(picking_path).resolve()), 'template_path': str(template_path),
            'source_origins': source_origins, 'source_catalog_path': str(source_catalog_path)}


def event_line(eid, event):
    t = utc(event['solver_origin_time'])
    return (f"{t:%Y%m%d} {t:%H%M%S}{t.microsecond//10000:02d} "
            f"{event['latitude']:.6f} {event['longitude']:.6f} {event['depth_km']:.3f} "
            f"0.0 0.0 0.0 0.0 {eid}\n")


def prepare_tier(master, label, directory, joint_config):
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Joint input directory must be fresh')
    directory.mkdir(parents=True, exist_ok=True)
    ids = master['ids_by_label'][label]
    event_table = {eid: master['events'][eid] for eid in sorted(ids)}
    observed = [o for o in master['observations'] if o['event_id'] in ids]
    excluded = [o for o in master['excluded'] if o['event_id'] in ids]
    selected_ids = {int(r['event_id']) for r in master['rows_by_label'][label]}
    for eid in event_table:
        event_table[eid] = {**event_table[eid], 'role': 'detection' if eid in selected_ids else 'template_reference'}
    write_json(directory / 'events.json', {str(e): r for e, r in event_table.items()})
    write_json(directory / 'observations.json', observed)
    write_json(directory / 'matching_exclusions.json', excluded)
    write_json(directory / 'joint_config.json', joint_config)
    write_json(directory / 'source_files.json', {'files': master['source_files'], 'picking_path': master['picking_path'],
               'template_path': master['template_path'], 'source_cc_path': str(master['sources'][label]['dt_cc_path']),
               'source_catalog_path': master['source_catalog_path']})
    save_mapping(directory / 'station_aliases.json', master['aliases'])
    (directory / 'station.dat').write_text(''.join(
        f"{alias} {record['coordinates']['latitude']:.7f} {record['coordinates']['longitude']:.7f}\n"
        for alias, record in sorted(master['aliases'].items())))
    (directory / 'events.native').write_text(''.join(event_line(eid, row) for eid, row in event_table.items()))
    lines = []
    for eid, event in event_table.items():
        t = utc(event['solver_origin_time'])
        lines.append(f"# {t.year} {t.month} {t.day} {t.hour} {t.minute} {t.second+t.microsecond/1e6:.2f} "
                     f"{event['latitude']:.6f} {event['longitude']:.6f} {event['depth_km']:.3f} 0.0 0.0 0.0 0.0 {eid}\n")
        for obs in observed:
            if obs['event_id'] == eid:
                lines.append(f"{obs['station']} {obs['travel_time_s']:.6f} {obs['weight']:.3f} {obs['phase']}\n")
    (directory / 'phase.dat').write_text(''.join(lines))
    cc, audit = [], []
    for pair in differentials(master['sources'][label]['dt_cc_path'], 'cc'):
        a, b = pair['a'], pair['b']
        if not {a, b}.issubset(ids) or b not in master['templates']:
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
    write_json(directory / 'conversion_meta.json', {'n_events': len(ids), 'n_phase_lines': len(observed),
                'converter_sha256': digest(__file__), 'ct_source': 'independent_phasenet',
                'depth_reference': 'sea_level', 'solver_depth_offset_km': 0,
                'magnitude_and_error_placeholders': 'native input zeros are unset, not measured magnitudes/errors'})
    return {'events': len(ids), 'independent_arrivals': len(observed), 'cc_observations': len(audit)}
