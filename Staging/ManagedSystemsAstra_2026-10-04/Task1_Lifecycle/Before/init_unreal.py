"""Register the ordinary action from the sealed, exact project sources."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import unreal

project = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
guard_path = project / 'Content/Python/geocity_runtime_guard.py'
manifest = json.loads((project / 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json').read_text(encoding='utf-8'))
expected = manifest['modules']['geocity_runtime_guard']['sha256']
guard_source = guard_path.read_bytes()
if hashlib.sha256(guard_source).hexdigest() != expected:
    raise RuntimeError('GeoCity startup source differs from its sealed manifest.')
guard = sys.modules.get('geocity_runtime_guard')
if guard is None:
    spec = importlib.util.spec_from_file_location('geocity_runtime_guard', guard_path)
    guard = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = guard
    guard.__geocity_loaded_sha256__ = expected
    exec(compile(guard_source, str(guard_path), 'exec', dont_inherit=True), guard.__dict__)
elif (not getattr(guard, '__file__', None) or Path(guard.__file__).resolve() != guard_path.resolve()
      or not guard.__spec__ or Path(guard.__spec__.origin).resolve() != guard_path.resolve()
      or getattr(guard, '__geocity_loaded_sha256__', None) != expected):
    raise RuntimeError('An alternate or stale GeoCity startup is already loaded; restart the editor.')
guard.bootstrap(project)
