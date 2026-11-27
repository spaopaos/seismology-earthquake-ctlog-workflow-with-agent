"""Portable release identity and explicit runtime configuration (stdlib only)."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def verify_vendor(repo, expected_commit):
    repo = Path(repo).resolve()
    manifest = json.loads((repo / 'SOURCE_MANIFEST.json').read_text())
    if manifest['commit'] != expected_commit:
        raise ValueError('Unexpected source version: ' + str(repo))
    for name in manifest['files']:
        if not (repo / name).is_file():
            raise ValueError('Vendor source missing: ' + str(repo / name))
    extras = [str(p.relative_to(repo)) for p in repo.rglob('*.py')
              if str(p.relative_to(repo)) not in manifest['files']]
    if extras:
        raise ValueError('Unexpected vendor Python source: ' + str(extras))
    return manifest['commit']

def runtime():
    path = Path(os.environ.get('SEISFLOW_RUNTIME', ROOT / 'runtime.local.json')).resolve()
    if not path.is_file():
        return {}, path.parent
    doc = json.loads(path.read_text())
    return doc, path.parent

def runtime_path(key, default=None):
    doc, base = runtime()
    value = doc.get(key, default)
    if not value:
        return None
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()

def binary(name):
    # Release binary identity is checked independently by every native runner.
    return str(runtime_path(name, str(ROOT / 'bin' / name)))

def native_environment():
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(ROOT / 'bin/lib') + (os.pathsep + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    return env
