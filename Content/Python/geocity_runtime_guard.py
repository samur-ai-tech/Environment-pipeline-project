"""Load the retained GeoCity action from its sealed project sources.

No cook, session, actor, map or Content changes occur at import/startup.
Already loaded stale modules are rejected; running objects are never reloaded.
"""
import hashlib
import importlib
import importlib.abc
import importlib.util
import inspect
import json
import os
import sys
import types
from pathlib import Path

_ROOT = None
_MANIFEST = None
_FINDER = None


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _code_signature(code):
    constants = tuple(_code_signature(v) if isinstance(v, types.CodeType) else v
                      for v in code.co_consts)
    return (code.co_code, constants, code.co_names, code.co_varnames,
            code.co_freevars, code.co_cellvars, code.co_argcount,
            code.co_posonlyargcount, code.co_kwonlyargcount, code.co_flags,
            code.co_exceptiontable)


def _functions(module):
    for value in vars(module).values():
        if inspect.isfunction(value) and value.__module__ == module.__name__:
            yield value
        elif inspect.isclass(value) and value.__module__ == module.__name__:
            for member in vars(value).values():
                if isinstance(member, (staticmethod, classmethod)):
                    member = member.__func__
                if isinstance(member, property):
                    for fn in (member.fget, member.fset, member.fdel):
                        if fn is not None:
                            yield fn
                elif inspect.isfunction(member):
                    yield member


def _source(name):
    entry = _MANIFEST['modules'][name]
    path = (_ROOT / 'Content/Python' / entry['file']).resolve(strict=True)
    if path.parent != (_ROOT / 'Content/Python').resolve() or path.stem != name:
        raise RuntimeError('Unscoped GeoCity source: ' + name)
    if _sha(path) != entry['sha256']:
        raise RuntimeError('GeoCity source changed after sealing: ' + name)
    return path


def _verify_module(module):
    name = module.__name__
    path = _source(name)
    if (not getattr(module, '__file__', None)
            or Path(module.__file__).resolve(strict=True) != path
            or not module.__spec__ or not module.__spec__.origin
            or Path(module.__spec__.origin).resolve(strict=True) != path):
        raise RuntimeError('Alternate loaded GeoCity module: ' + name)
    if getattr(module, '__geocity_loaded_sha256__', None) != _MANIFEST['modules'][name]['sha256']:
        raise RuntimeError('GeoCity module was not loaded from the sealed source; restart the editor: ' + name)
    expected = {}

    def walk(code):
        expected[code.co_qualname] = code
        for value in code.co_consts:
            if isinstance(value, types.CodeType):
                walk(value)

    walk(compile(path.read_bytes(), str(path), 'exec', dont_inherit=True))
    count = 0
    for fn in _functions(module):
        # Standard decorators such as contextmanager keep the declared function
        # in __wrapped__; verify that source function rather than stdlib code.
        fn = inspect.unwrap(fn)
        if Path(fn.__code__.co_filename).resolve(strict=True) != path:
            raise RuntimeError('Alternate GeoCity function origin: ' + fn.__qualname__)
        wanted = expected.get(fn.__qualname__)
        if wanted is None or _code_signature(fn.__code__) != _code_signature(wanted):
            raise RuntimeError('Stale loaded GeoCity code; restart the editor: ' + fn.__qualname__)
        count += 1
    return {'file': str(path), 'sha256': _sha(path), 'verified_functions': count}


class _SourceLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        path = _source(module.__name__)
        module.__file__ = str(path)
        # Compile the sealed source directly: timestamp-based bytecode caches
        # cannot substitute an earlier revision with the same size/timestamp.
        source = path.read_bytes()
        module.__geocity_loaded_sha256__ = hashlib.sha256(source).hexdigest()
        if module.__geocity_loaded_sha256__ != _MANIFEST['modules'][module.__name__]['sha256']:
            raise RuntimeError('GeoCity source changed immediately before import: ' + module.__name__)
        exec(compile(source, str(path), 'exec', dont_inherit=True), module.__dict__)
        _verify_module(module)


class _SourceFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in _MANIFEST['modules'] and fullname != __name__:
            source = _source(fullname)
            return importlib.util.spec_from_file_location(fullname, source, loader=_SourceLoader())
        return None


def verify():
    """Preflight the same loaded revision immediately before an ordinary action."""
    if _ROOT is None or _MANIFEST is None:
        raise RuntimeError('GeoCity startup source binding is absent; restart with the project startup.')
    manifest_path = _ROOT / 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
    current = json.loads(manifest_path.read_text(encoding='utf-8'))
    if current != _MANIFEST:
        raise RuntimeError('GeoCity manifest changed in this session; restart the editor.')
    _verify_support_files()
    result = {}
    for name in _MANIFEST['modules']:
        _source(name)
        if name not in sys.modules:
            raise RuntimeError('A required GeoCity module was not loaded: ' + name)
        result[name] = _verify_module(sys.modules[name])
    return result


def _verify_support_files():
    startup=(_ROOT/'Content/Python'/ _MANIFEST['startup']['file']).resolve(strict=True)
    if startup!=(_ROOT/'Content/Python/init_unreal.py').resolve() or _sha(startup)!=_MANIFEST['startup']['sha256']:
        raise RuntimeError('GeoCity startup entrypoint changed after sealing')
    required={'Config/DefaultEngine.ini','Config/DefaultRoadBLD.ini',
              'Staging/SystemCompletion_2026-10-04/launch_editor.ps1',
              'Staging/SystemCompletion_2026-10-04/seal_runtime.py'}
    if set(_MANIFEST.get('support_files',{}))!=required:
        raise RuntimeError('GeoCity combined seal lacks its exact startup/configuration contract')
    for relative,expected in _MANIFEST['support_files'].items():
        path=(_ROOT/relative).resolve(strict=True)
        if not path.is_relative_to(_ROOT) or _sha(path)!=expected:
            raise RuntimeError('GeoCity startup/configuration changed after sealing: '+relative)


def bootstrap(project):
    global _ROOT, _MANIFEST, _FINDER
    project = Path(project).resolve(strict=True)
    if _ROOT is not None and _ROOT != project:
        raise RuntimeError('GeoCity is already bound to another project.')
    _ROOT = project
    manifest = json.loads((_ROOT / 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json').read_text(encoding='utf-8'))
    if _MANIFEST is not None and _MANIFEST!=manifest:
        raise RuntimeError('GeoCity cannot rebind a running session to another seal; restart the editor')
    _MANIFEST=manifest
    if _MANIFEST['schema'] != 'environmentpipeline.geocity_runtime_sources.v2':
        raise RuntimeError('Unsupported GeoCity runtime manifest.')
    _verify_support_files()
    startup = _ROOT / 'Content/Python' / _MANIFEST['startup']['file']
    if startup.name != 'init_unreal.py' or _sha(startup) != _MANIFEST['startup']['sha256']:
        raise RuntimeError('The ordinary GeoCity startup differs from its sealed entrypoint.')
    for name in _MANIFEST['modules']:
        _source(name)
        if name in sys.modules:
            _verify_module(sys.modules[name])
    if _FINDER is None:
        _FINDER = _SourceFinder()
        sys.meta_path.insert(0, _FINDER)
    for name in _MANIFEST['modules']:
        importlib.import_module(name)
    sources = verify()
    sys.modules['geocity_editor_action'].register_menu()
    receipt = _ROOT / 'Staging/SystemCompletion_2026-10-04/RUNTIME_STARTUP.json'
    receipt.parent.mkdir(parents=True, exist_ok=True)
    payload=json.dumps({'pid':os.getpid(),'sources':sources,'support_files':_MANIFEST['support_files'],
                        'manifest_sha256':_sha(_ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'),
                        'menu_registered':True,'generation_started':False},indent=2)
    receipt.write_text(payload,encoding='utf-8')
    receipt.with_name('RUNTIME_STARTUP_PID'+str(os.getpid())+'.json').write_text(payload,encoding='utf-8')
    return sources
