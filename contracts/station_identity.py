"""Resolve full station identities and generate reversible five-character native aliases."""
import json
import math
from pathlib import Path

def parts(group):
    p = str(group).split('.')
    if len(p) != 4 or not p[0] or not p[1] or len(p[3]) != 2:
        raise ValueError('Expected NET.STA.LOC.FAMILY: ' + str(group))
    return p

def read_stations(path):
    import pandas as pd
    path = Path(path)
    if path.suffix.lower() == '.csv':
        frame = pd.read_csv(path, dtype={'id': str}, keep_default_na=False)
    else:
        frame = pd.read_csv(path, sep=r'\s+', header=None,
                            names=['id', 'longitude', 'latitude', 'elevation_m'], dtype={'id': str})
    if set(['id', 'longitude', 'latitude', 'elevation_m']) - set(frame):
        raise ValueError('Station table requires id,longitude,latitude,elevation_m')
    if frame.id.duplicated().any() or frame.id.isna().any():
        raise ValueError('Station metadata IDs must be nonempty and unique')
    for c in ['longitude', 'latitude', 'elevation_m']:
        frame[c] = pd.to_numeric(frame[c], errors='raise')
        if not frame[c].map(math.isfinite).all():
            raise ValueError('Nonfinite station coordinate: ' + c)
    if (frame.longitude.abs() > 180).any() or (frame.latitude.abs() > 90).any():
        raise ValueError('Invalid longitude/latitude')
    return frame.set_index('id')

def resolve_groups(path, groups):
    import pandas as pd
    table = read_stations(path)
    groups = sorted(set(map(str, groups)))
    short_sites = {}
    for group in groups:
        p = parts(group)
        short_sites.setdefault(p[1], set()).add('.'.join(p[:3]))
    records = []
    for group in groups:
        p = parts(group)
        keys = [group, '.'.join(p[:3]), '.'.join(p[:2])]
        matches = [k for k in keys if k in table.index]
        if not matches and p[1] in table.index:
            if len(short_sites[p[1]]) != 1:
                raise ValueError('Ambiguous bare station ID; provide NET.STA.LOC or group: ' + p[1])
            matches = [p[1]]
        if not matches:
            raise ValueError('Missing station coordinates: ' + group)
        rows = table.loc[matches, ['longitude', 'latitude', 'elevation_m']]
        if len(rows.drop_duplicates()) != 1:
            raise ValueError('Conflicting station coordinates: ' + group)
        records.append({'id': group, **rows.iloc[0].to_dict()})
    return pd.DataFrame(records, columns=['id', 'longitude', 'latitude', 'elevation_m'])

def native_mapping(stations, groups):
    resolved = resolve_groups(stations, groups)
    sites = {}
    for row in resolved.to_dict('records'):
        key = '.'.join(parts(row['id'])[:3])
        coordinates = {k: row[k] for k in ['longitude', 'latitude', 'elevation_m']}
        if key in sites and sites[key]['coordinates'] != coordinates:
            raise ValueError('Instrument families at one site have conflicting coordinates: ' + key)
        sites.setdefault(key, {'coordinates': coordinates, 'groups': []})['groups'].append(row['id'])
    if len(sites) > 9999:
        raise ValueError('Native station alias capacity exceeded')
    by_group = {}
    aliases = {}
    for i, site in enumerate(sorted(sites), 1):
        alias = f'S{i:04d}'
        aliases[alias] = {'site_id': site, **sites[site]}
        for group in sites[site]['groups']:
            by_group[group] = alias
    return by_group, aliases

def save_mapping(path, aliases):
    Path(path).write_text(json.dumps({'scheme': 'five_char_alias_for_NET.STA.LOC',
                                    'aliases': aliases}, indent=2) + '\n')
