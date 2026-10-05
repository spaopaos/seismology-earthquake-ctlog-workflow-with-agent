import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'm6', '/mnt/d/yunan/ctlog_work/skills/seismic-insar/scripts/6_make_maps.py')
m6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m6)

import rasterio

root = Path('/home/spaopaos/insar_test_eryuan')
jobs = json.loads((root / 'insar_jobs.json').read_text())['jobs']
ev = {e['event_id']: e for j in jobs for e in j['events']}
sel = json.loads((root / 'selected_pairs.json').read_text())['selection']
for s in sel:
    e = ev[s['event_id']]
    pdir = m6.find_product_dir(root / s['job_id'] / s['stack'], s['granules'])
    with rasterio.open(m6.layer(pdir, 'unw_phase')) as src:
        b = src.bounds
    inside = b.left <= e['longitude'] <= b.right and b.bottom <= e['latitude'] <= b.top
    print(f"{s['job_id']} {s['stack']:12s} frame lon {b.left:.2f}..{b.right:.2f} "
          f"lat {b.bottom:.2f}..{b.top:.2f} | {s['event_id']} "
          f"({e['longitude']:.3f}, {e['latitude']:.3f}) inside={inside}")
