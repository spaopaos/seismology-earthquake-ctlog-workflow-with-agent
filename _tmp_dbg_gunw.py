import sys
sys.path.insert(0, '/mnt/d/yunan/ctlog_work/skills/seismic-insar/scripts')
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location(
    'm', '/mnt/d/yunan/ctlog_work/skills/seismic-insar/scripts/6_make_maps.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

import json
sel = json.loads(Path('/home/spaopaos/insar_test_eryuan/selected_pairs.json').read_text())['selection']
s = sel[0]
print('job:', s['job_id'], s['stack'], 'granules:', s['granules'])
root = Path('/home/spaopaos/insar_test_eryuan')
sd = root / s['job_id'] / s['stack']
print('stack dir exists:', sd.is_dir())
print('zips:', [str(p.relative_to(sd)) for p in sd.rglob('*.zip')])
print('ncs:', [str(p.relative_to(sd)) for p in sd.rglob('*.nc')])
print('find_gunw ->', m.find_gunw(sd, s['granules']))
