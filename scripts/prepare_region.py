#!/usr/bin/env python3
"""Normalize explicit station/model inputs; no inferred units, datum or station identity."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'contracts'))
from station_identity import resolve_groups
from archive_interface import archive_records
from pipeline_contracts import sha256

def load_model(path):
    path = Path(path)
    if path.suffix.lower() == '.csv':
        table = pd.read_csv(path)
        required = {'depth_top_km','vp_km_s','vs_km_s'}
        if required - set(table):
            raise ValueError('Model CSV requires depth_top_km,vp_km_s,vs_km_s')
        return table[list(required)].astype(float)
    raise ValueError('Portable regional input is explicit model CSV; convert other formats using documented units and datum')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    path = Path(args.config).resolve()
    config = json.loads(path.read_text())
    base = path.parent
    archive = (base / config['archive']).resolve()
    station_path = (base / config['stations']).resolve()
    model_path = (base / config['velocity_model']).resolve()
    region = config['region']
    if region['horizontal_datum'] != 'WGS84' or region['depth_reference'] != 'sea_level' or region['elevation_units'] != 'm':
        raise ValueError('Release supports WGS84 and depths positive below sea level, station elevations in m above sea level')
    records, skipped = archive_records(archive)
    stations = resolve_groups(station_path, [r['group'] for r in records])
    model = load_model(model_path)
    arr = model[['depth_top_km','vp_km_s','vs_km_s']].to_numpy()
    if len(arr) < 1 or not np.isfinite(arr).all() or arr[0,0] != 0:
        raise ValueError('Finite model with first layer top at 0 km required')
    if not (np.diff(arr[:,0]) > 0).all() or not (np.diff(arr[:,1:3], axis=0) > 0).all():
        raise ValueError('This HYPOINVERSE CRH path requires strictly increasing depths and velocities')
    if not (arr[:,1] > arr[:,2]).all() or not (arr[:,2] > 0).all():
        raise ValueError('Require Vp > Vs > 0 in km/s')
    depth = region['depth_range_km']
    if len(depth) != 2 or depth[0] != 0 or depth[1] <= 0:
        raise ValueError('Current source-depth search requires [0, positive_maximum] km')
    output = base / 'inputs'
    output.mkdir(exist_ok=True)
    stations.to_csv(output / 'stations.txt', sep=' ', index=False, header=False)
    for phase in ['p','s']:
        column = 'v' + phase + '_km_s'
        lines = ['REGIONAL ' + phase.upper()] + [f'{v:.8g} {z:.8g}' for z,v in zip(model.depth_top_km, model[column])]
        (output / ('velocity_' + phase + '.cre')).write_text('\n'.join(lines) + '\n')
    receipt = {'input_sha256': {'stations': sha256(station_path), 'velocity_model': sha256(model_path),
                               'manifest': sha256(archive / 'daily_manifest.csv')},
               'groups': len(stations), 'layers': len(model), 'region': region,
               'model_vp_vs_by_layer': (model.vp_km_s / model.vs_km_s).tolist()}
    (output / 'region_preparation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))

if __name__ == '__main__':
    main()
