import zipfile
from pathlib import Path

sd = Path('/home/spaopaos/insar_test_eryuan/job_001/p99_f1265')
for z in sd.rglob('*.zip'):
    print('zip:', z.name)
    names = zipfile.ZipFile(z).namelist()
    print('\n'.join(names[:15]))
    print('total entries:', len(names))
    ext = z.parent / 'extracted' / z.stem
    print('extracted dir exists:', ext.exists(),
          '| nc inside:', [str(p.relative_to(ext)) for p in ext.rglob('*.nc')]
          if ext.exists() else None)
