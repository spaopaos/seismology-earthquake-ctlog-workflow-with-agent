"""Strict standardized archive boundary, independent of dataset-specific preprocessing."""
import csv
import json
from pathlib import Path

SR = 100
DAY_NPTS = 8640000

def intervals(value, n=DAY_NPTS):
    if not isinstance(value, list):
        raise ValueError('Intervals must be an array of [start,end) sample indices')
    last = 0
    for pair in value:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError('Invalid interval')
        a, b = pair
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= n or a < last:
            raise ValueError('Unsorted, overlapping or out-of-bounds interval')
        last = b
    return value

def within(inner, outer):
    return all(any(x <= a and b <= y for x, y in outer) for a, b in inner)

def archive_records(root):
    root = Path(root).resolve()
    with (root / 'daily_manifest.csv').open(newline='') as f:
        reader = csv.DictReader(f)
        required = {'group', 'date', 'status', 'metadata', 'file_Z', 'file_N', 'file_E'}
        if required - set(reader.fieldnames or []):
            raise ValueError('Archive manifest missing fields: ' + str(required - set(reader.fieldnames or [])))
        rows = list(reader)
    seen = set()
    records, skipped = [], []
    for row in rows:
        key = (row['group'], row['date'])
        if key in seen:
            raise ValueError('Duplicate archive group/day: ' + str(key))
        seen.add(key)
        if row['status'] not in ('READY', 'PARTIAL_DAY'):
            skipped.append({'group': key[0], 'date': key[1], 'reason': row['status']})
            continue
        if not row['metadata']:
            raise ValueError('Missing metadata: ' + str(key))
        metadata = json.loads((root / row['metadata']).read_text())
        if metadata.get('group') != key[0] or metadata.get('utc_day') != key[1]:
            raise ValueError('Metadata and manifest group/day differ: ' + str(key))
        usable = intervals(metadata.get('usable_3c_intervals'))
        if not usable:
            skipped.append({'group': key[0], 'date': key[1], 'reason': 'NO_USABLE_3C'})
            continue
        records.append({**row, 'meta': metadata, 'usable': usable,
                        'trace_group': row.get('trace_group') or metadata.get('trace_group') or row['group']})
    return records, skipped
