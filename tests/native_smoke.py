"""Run the bundled HYPOINVERSE binary against its official known-output fixture."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'contracts'))
from runtime_support import native_environment, digest

def main():
    record=json.loads((ROOT/'toolchain.json').read_text())['binaries']['hyp1.40']
    binary=ROOT/record['path']
    if digest(binary)!=record['sha256']: raise ValueError('Native binary identity mismatch')
    source=ROOT/'knowledge/repos/hyp2000-1.40/testone'
    with tempfile.TemporaryDirectory(prefix='seisflow-native-') as tmp:
        work=Path(tmp)
        for path in source.iterdir():
            if path.is_file(): shutil.copyfile(path,work/path.name)
        (work/'out').mkdir()
        command=(work/'testone.hyp').read_text()
        for suffix in ['prt','sum','arc']: command=command.replace('testone.'+suffix,'out/testone.'+suffix)
        (work/'check.hyp').write_text(command)
        run=subprocess.run([str(binary)],cwd=work,input='@check.hyp\n'+'\n'*40+'loc\nstop\n',
                           env=native_environment(),text=True,capture_output=True,timeout=120)
        if run.returncode: raise ValueError(run.stdout[-2000:]+run.stderr)
        results={suffix:(work/'out'/('testone.'+suffix)).read_bytes()==(source/('testone.'+suffix)).read_bytes() for suffix in ['sum','arc']}
        if not all(results.values()): raise ValueError('Official native outputs differ: '+str(results))
        print(json.dumps({'status':'PASS','test':'HYPOINVERSE official testone','byte_identical':results}))

if __name__=='__main__': main()
