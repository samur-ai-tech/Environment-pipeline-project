"""Package the ordinary project startup; compile source only, no Unreal import."""
import hashlib
import json
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / 'Content/Python'


def snapshot():
    modules = {}
    for path in sorted(PYTHON.glob('geocity_*.py')):
        source = path.read_bytes()
        compile(source, str(path), 'exec', dont_inherit=True)
        modules[path.stem] = {'file': path.name, 'sha256': hashlib.sha256(source).hexdigest()}
    entry = PYTHON / 'init_unreal.py'
    compile(entry.read_bytes(), str(entry), 'exec', dont_inherit=True)
    support = {}
    for relative in ('Config/DefaultEngine.ini', 'Config/DefaultRoadBLD.ini',
                     'Staging/SystemCompletion_2026-10-04/launch_editor.ps1',
                     'Staging/SystemCompletion_2026-10-04/seal_runtime.py'):
        support[relative] = hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    return {'schema': 'environmentpipeline.geocity_runtime_sources.v2',
                'startup': {'file': entry.name, 'sha256': hashlib.sha256(entry.read_bytes()).hexdigest()},
                'modules': modules, 'support_files':support,
                'loading': 'exact project source; no stale-module reload; no startup generation'}


def seal(check=False):
    # Manager invokes only after all source workers stop changing their files.
    # Profile runtime delivery fields are intentionally not source-sealed.
    manifest=snapshot()
    path=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
    if snapshot()!=manifest:
        raise RuntimeError('Sources changed during sealing; wait for all writers to stop')
    if check:
        if json.loads(path.read_text(encoding='utf-8'))!=manifest:
            raise RuntimeError('Combined source/configuration differs from its final seal')
    else:
        pending=path.with_suffix('.json.pending')
        pending.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        os.replace(pending,path)
    print(json.dumps({'sealed_modules':len(manifest['modules']),'support_files':list(manifest['support_files']),
                      'check_only':check,'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'runtime_executed':False}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    seal(parser.parse_args().check)
