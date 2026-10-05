import json
from pathlib import Path

f = next(Path('/home/spaopaos/insar_test_eryuan').glob('job_*/p*/hyp3_jobs.json'))
d = json.loads(f.read_text())
print('file:', f)
print('top:', type(d).__name__, list(d.keys()) if isinstance(d, dict) else len(d))


def walk(o, depth=0, path=''):
    if depth > 4:
        return
    if isinstance(o, dict):
        for k, v in o.items():
            if k.lower() in ('status', 'statuscode', 'state', 'job_id', 'id'):
                print(' ' * depth, f'{path}/{k} =', repr(v)[:80])
            walk(v, depth + 1, f'{path}/{k}')
    elif isinstance(o, list):
        for i, v in enumerate(o[:2]):
            walk(v, depth + 1, f'{path}[{i}]')


walk(d)
