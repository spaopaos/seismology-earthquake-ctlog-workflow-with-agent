import shutil
from pathlib import Path

dst = Path('/tmp/skhash_smoke')
if dst.exists():
    shutil.rmtree(dst)
dst.mkdir()
shutil.copytree('/mnt/d/yunan/ctlog_work/knowledge/repos/SKHASH/examples/smile/IN', dst / 'IN')
(dst / 'OUT').mkdir()

src = Path('/mnt/d/yunan/ctlog_work/knowledge/repos/SKHASH/examples/smile/control_file.txt').read_text()
blocks = []
for block in src.split('\n\n'):
    stripped = block.strip()
    if stripped.startswith('$outfolder_plots'):
        continue  # no matplotlib in this env; plots are optional
    blocks.append(block.replace('smile/', ''))
(dst / 'control_file.txt').write_text('\n\n'.join(blocks))
print('prepared', dst)
