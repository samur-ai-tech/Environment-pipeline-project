"""Package the ordinary project startup; compile source only, no Unreal import."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / 'Content/Python'


def seal():
    modules = {}
    for path in sorted(PYTHON.glob('geocity_*.py')):
        source = path.read_bytes()
        compile(source, str(path), 'exec', dont_inherit=True)
        modules[path.stem] = {'file': path.name, 'sha256': hashlib.sha256(source).hexdigest()}
    entry = PYTHON / 'init_unreal.py'
    compile(entry.read_bytes(), str(entry), 'exec', dont_inherit=True)
    manifest = {'schema': 'environmentpipeline.geocity_runtime_sources.v1',
                'startup': {'file': entry.name, 'sha256': hashlib.sha256(entry.read_bytes()).hexdigest()},
                'modules': modules, 'loading': 'exact project source; no stale-module reload; no startup generation'}
    (ROOT / 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sealed_modules': len(modules), 'startup': str(entry), 'runtime_executed': False}))


if __name__ == '__main__':
    seal()
