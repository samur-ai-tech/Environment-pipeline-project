"""Load the retained GeoCity action from its sealed project sources.

No cook, session, actor, map or Content changes occur at import/startup.
Already loaded stale modules are rejected; running objects are never reloaded.
"""
import datetime
import hashlib
import importlib
import importlib.abc
import importlib.util
import inspect
import json
import os
import re
import subprocess
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


# ---------------------------------------------------------------------------
# Parallel editors (brief 1, 2026-10-06). Pure file/process reads; no unreal
# import, so the sealed launcher can run the same code outside the editor.
# ---------------------------------------------------------------------------
PARALLEL_EDITOR_SCHEMA = 'environmentpipeline.parallel_editor.v1'
PARALLEL_CHECK_SCHEMA = 'environmentpipeline.parallel_editor_check.v1'
PARALLEL_RECORDS = 'Staging/ParallelEditors'
LEASE_FILE = 'Staging/ModelBank/EDITOR_OWNER.txt'
LEASE_PID_KEYS = ('assigned_editor_PID', 'editor_PID', 'previous_editor_PID')
SURFACE_ROOT = '/Game/Project/Shared/SurfacePainting/Appearance_20261003/'
SHARED_GRASS_WRITES = (SURFACE_ROOT + 'LG_GeoCity_PermittedGroundGrass',
                       SURFACE_ROOT + 'M_SurfaceBank_Natural')
SHARED_READS = ('/Game/Project/Shared/ModelBank/',
                SURFACE_ROOT + 'MI_SurfaceBank_Natural',
                SURFACE_ROOT + 'M_SurfaceBank_Natural',
                SURFACE_ROOT + 'LG_GeoCity_PermittedGroundGrass')
SHARED_ROAD_READS = ('/Game/Project/Shared/RoadBLD/',)
PROTECTED_FILES = ('Content/Python/', 'Config/DefaultEngine.ini', 'Config/DefaultRoadBLD.ini',
                   'Staging/SystemCompletion_2026-10-04/')
START_TOLERANCE_SECONDS = 2.0
_OWN_START_UTC = None


def lease_fields(line):
    return dict(re.findall(r'(?:^|\s)([A-Za-z_]+)=([^\s]+)', line or ''))


def parse_utc(value):
    """Aware UTC datetime from an ISO-8601 token (Z, offset or none); None if unparseable."""
    match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})?$', (value or '').strip())
    if not match:
        return None
    base, fraction, zone = match.groups()
    text = base + ('.' + fraction[:6].ljust(6, '0') if fraction else '') + ('+00:00' if zone in (None, 'Z') else zone)
    try:
        return datetime.datetime.fromisoformat(text).astimezone(datetime.timezone.utc)
    except ValueError:
        return None


def _lease_timestamp(line):
    return parse_utc((line or '').strip().split(' ', 1)[0])


def editor_lease_line(text, pid, start_utc=None):
    """Last lease line naming exactly this PID, written at or after its process start.

    A line names the PID when assigned_editor_PID, editor_PID or previous_editor_PID
    equals the PID token exactly (suffixed tokens such as 29900_still_running never
    match). Lines older than the process start minus one second belong to an earlier
    process with the same PID and end the search; lines whose timestamp cannot be
    parsed are kept so the caller fails closed. Returns None when no line qualifies.
    """
    pid = str(int(pid))
    floor = None
    if start_utc:
        parsed = parse_utc(start_utc)
        floor = parsed - datetime.timedelta(seconds=1) if parsed else None
    for line in reversed(text.splitlines()):
        fields = lease_fields(line)
        if not any(fields.get(key) == pid for key in LEASE_PID_KEYS):
            continue
        stamp = _lease_timestamp(line)
        if floor is not None and stamp is not None and stamp < floor:
            return None
        return line
    return None


def _powershell(command, timeout=30):
    read = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                          capture_output=True, text=True, timeout=timeout,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if read.returncode != 0:
        raise RuntimeError('Process inspection failed: ' + (read.stderr or read.stdout).strip()[:300])
    return read.stdout


def live_editors():
    """[(pid, start_utc or None)] of UnrealEditor and UnrealEditor-Cmd processes; one PowerShell call."""
    text = _powershell("$rows=@(Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue);"
                       "foreach($p in $rows){try{$s=$p.StartTime.ToUniversalTime().ToString('o')}catch{$s='?'};"
                       "Write-Output ($p.Id.ToString()+' '+$s)};exit 0")
    result = []
    for line in text.splitlines():
        parts = line.split()
        if parts:
            result.append((int(parts[0]), parts[1] if len(parts) > 1 and parts[1] != '?' else None))
    return sorted(result)


def process_start_utc(pid):
    """Kernel creation time of one process in UTC ('o' format); raises when unreadable."""
    text = _powershell("(Get-Process -Id %d -ErrorAction Stop).StartTime.ToUniversalTime().ToString('o')" % int(pid)).strip()
    if parse_utc(text) is None:
        raise RuntimeError('Cannot read the start time of process %d' % int(pid))
    return text


def own_process_start_utc():
    global _OWN_START_UTC
    if _OWN_START_UTC is None:
        _OWN_START_UTC = process_start_utc(os.getpid())
    return _OWN_START_UTC


def own_lease_line(project):
    """This process's own last lease line (None when no line names this PID since it started)."""
    text = (Path(project) / LEASE_FILE).read_text(encoding='utf-8-sig')
    return editor_lease_line(text, os.getpid(), own_process_start_utc())


def _package(value):
    """Package part of an object path, lower-cased, without a trailing slash."""
    text = str(value).split('.', 1)[0].strip().lower()
    return text.rstrip('/') if text != '/' else text


def _overlaps(a, b):
    a, b = _package(a), _package(b)
    return a == b or b.startswith(a + '/') or a.startswith(b + '/')


def _covered(value, prefixes):
    value = _package(value)
    return any(value == _package(p) or value.startswith(_package(p) + '/') for p in prefixes)


def _file_key(value, project):
    """Project-relative posix path when inside the project, else absolute posix path."""
    text = str(value).replace('\\', '/').strip()
    try:
        path = Path(text)
        if path.is_absolute() and project is not None:
            resolved = path.resolve()
            root = Path(project).resolve()
            if resolved.is_relative_to(root):
                text = resolved.relative_to(root).as_posix()
            else:
                text = resolved.as_posix()
    except (OSError, ValueError):
        pass
    return text.rstrip('/')


def _file_overlaps(a, b, project):
    a, b = _file_key(a, project).lower(), _file_key(b, project).lower()
    return a == b or b.startswith(a + '/') or a.startswith(b + '/')


def generation_scope(profile, project):
    """Declared write and read sets of one ordinary generation from its AREA_PROFILE.

    write: the whole area folder /Game/Project/Areas/<area>/ (root, map, Cook, Bake,
    LayerInfos, area ground MI, RoadBLD) plus the shared grass type and Natural master
    when landscape_grass.enabled. read: every /Game package named in the profile, the
    ModelBank folder (table rows reach meshes the profile never names), the shared
    surface-painting constants and, with roads enabled, the shared RoadBLD folder.
    file_write: the profile, the workflow and catalog receipt folders, the lease file.
    file_read: every absolute file path named in the profile. Bank imports are NOT
    part of a generation's write set; a bank editor declares them in its own record.
    """
    path = None
    if isinstance(profile, (str, Path)):
        path = Path(profile).resolve(strict=True)
        p = json.loads(path.read_text(encoding='utf-8-sig'))
    else:
        p = profile
    root, map_path = p['root'], p['map']
    if not root.startswith('/Game/Project/Areas/') or not map_path.startswith(root + '/'):
        raise RuntimeError('Profile root/map are outside the managed area layout')
    area = '/'.join(root.split('/')[:5])
    write = {area + '/'}
    grass = p.get('landscape_grass') or {}
    if grass.get('enabled'):
        write.update(SHARED_GRASS_WRITES)
    roads = bool((p.get('roadbld_workflow') or {}).get('enabled'))
    read, files = set(SHARED_READS), set()
    if roads:
        read.update(SHARED_ROAD_READS)

    def walk(value):
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            if value.startswith('/Game/'):
                read.add(value.split('.', 1)[0])
            elif re.match(r'^[A-Za-z]:[\\/]', value):
                files.add(value)
    walk(p)
    read = {r for r in read if not _covered(r, write)}
    file_write = {LEASE_FILE}
    if path is not None:
        file_write.add(_file_key(path, project))
    for key in ('workflow_receipt', 'catalog_receipt'):
        if p.get(key):
            file_write.add(_file_key(Path(p[key]).parent, project) + '/')
    file_write = {f for f in file_write if not any(_file_overlaps(f, w, project) and f != w and len(f) > len(w) for w in file_write)}
    file_read = {_file_key(f, project) for f in files}
    file_read = {f for f in file_read if not any(_file_overlaps(f, w, project) for w in file_write)}
    return {'area_id': area.rsplit('/', 1)[-1], 'map': map_path, 'grass_enabled': bool(grass.get('enabled')),
            'roads_enabled': roads, 'write': sorted(write), 'read': sorted(read),
            'file_write': sorted(file_write), 'file_read': sorted(file_read)}


def read_parallel_records(project):
    """Every Staging/ParallelEditors/EDITOR_<pid>.json with its sha256; unreadable files are listed, not raised."""
    folder = Path(project) / PARALLEL_RECORDS
    entries = []
    for path in sorted(folder.glob('EDITOR_*.json')) if folder.is_dir() else []:
        entry = {'path': PARALLEL_RECORDS + '/' + path.name, 'sha256': _sha(path), 'record': None, 'error': None}
        try:
            record = json.loads(path.read_text(encoding='utf-8-sig'))
            if record.get('schema') != PARALLEL_EDITOR_SCHEMA:
                raise ValueError('unsupported record schema')
            if path.name != 'EDITOR_%d.json' % int(record['pid']):
                raise ValueError('file name does not match the record pid')
            if not isinstance(record.get('write_scope'), list) or not record.get('process_start_utc'):
                raise ValueError('record lacks write_scope or process_start_utc')
            entry['record'] = record
        except Exception as exc:
            entry['error'] = repr(exc)
        entries.append(entry)
    return entries


def _record_matches(entry, start_utc):
    record = entry['record']
    if start_utc is None:
        return False, 'live process start time could not be read'
    recorded, live = parse_utc(record.get('process_start_utc')), parse_utc(start_utc)
    if recorded is None or live is None:
        return False, 'process start time is not ISO-8601'
    if abs((recorded - live).total_seconds()) > START_TOLERANCE_SECONDS:
        return False, 'record start %s differs from live start %s (PID reuse)' % (record.get('process_start_utc'), start_utc)
    if record.get('released_utc'):
        return False, 'record is released (released_utc=%s) but the process is still live' % record['released_utc']
    return True, 'valid'


def parallel_editor_report(project, profile, own_pid, live=None, records=None):
    """Read-only scope check of this generation against every other live editor.

    PASS when no other editor is live. Otherwise every other live editor needs a valid
    record (pid, file name, process start within 2 s, not released); this editor needs
    its own record whose write_scope covers the run's write set (own_pid=None is the
    launcher's pre-start check and has no own record yet). REFUSE when another record's
    write_scope or original_map overlaps the run's write set or read set, or its
    file_write_scope overlaps the run's files or the protected sealed files. Records for
    dead PIDs are stale and ignored. Nothing is written.
    """
    project = Path(project).resolve(strict=True)
    scope = generation_scope(profile, project)
    live = live_editors() if live is None else sorted((int(pid), start) for pid, start in live)
    entries = read_parallel_records(project) if records is None else records
    own_pid = None if own_pid is None else int(own_pid)
    starts = dict(live)
    report = {'schema': PARALLEL_CHECK_SCHEMA, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'project': str(project), 'profile': str(profile) if isinstance(profile, (str, Path)) else None,
              'own_pid': own_pid, 'live_editors': [{'pid': pid, 'start_utc': start} for pid, start in live],
              'scope': scope, 'verdict': 'PASS', 'reasons': [], 'other_editors': [], 'own_record': None,
              'stale_records': [], 'invalid_records': []}
    valid = {}
    for entry in entries:
        record = entry['record']
        if record is None:
            report['invalid_records'].append({'path': entry['path'], 'sha256': entry['sha256'], 'why': entry['error']})
            continue
        pid = int(record['pid'])
        if pid not in starts:
            report['stale_records'].append({'path': entry['path'], 'sha256': entry['sha256'], 'pid': pid,
                                            'why': 'no live process with this PID'})
            continue
        ok, why = _record_matches(entry, starts[pid])
        if ok:
            valid[pid] = entry
        else:
            report['invalid_records'].append({'path': entry['path'], 'sha256': entry['sha256'], 'pid': pid, 'why': why})

    def refuse(text):
        report['verdict'] = 'REFUSE'
        report['reasons'].append(text)
    others = [(pid, start) for pid, start in live if pid != own_pid]
    if not others:
        report['summary'] = 'no other Unreal editor process is live'
        return report
    if own_pid is not None:
        own = valid.get(own_pid)
        if own is None:
            refuse('this editor (PID %d) has no valid record %s/EDITOR_%d.json while other editors are live'
                   % (own_pid, PARALLEL_RECORDS, own_pid))
        else:
            report['own_record'] = {'path': own['path'], 'sha256': own['sha256']}
            for wanted in scope['write']:
                if not _covered(wanted, own['record']['write_scope']):
                    refuse('own record %s write_scope does not cover this run\'s write prefix %s' % (own['path'], wanted))
    for pid, start in others:
        entry = valid.get(pid)
        if entry is None:
            why = next((row['why'] for row in report['invalid_records'] if row.get('pid') == pid), 'no record file')
            refuse('live editor PID %d (started %s) has no valid record %s/EDITOR_%d.json: %s'
                   % (pid, start, PARALLEL_RECORDS, pid, why))
            continue
        record = entry['record']
        report['other_editors'].append({'pid': pid, 'start_utc': start, 'record': entry['path'],
                                        'record_sha256': entry['sha256'], 'task': record.get('task'),
                                        'operator_thread_id': record.get('operator_thread_id'),
                                        'original_map': record.get('original_map'),
                                        'write_scope': list(record.get('write_scope', [])),
                                        'file_write_scope': list(record.get('file_write_scope', []))})
        theirs = list(record.get('write_scope', [])) + ([record['original_map']] if record.get('original_map') else [])
        for prefix in theirs:
            for ours in scope['write']:
                if _overlaps(prefix, ours):
                    refuse('PID %d record %s writes %s, which overlaps this run\'s write prefix %s' % (pid, entry['path'], prefix, ours))
            for ours in scope['read']:
                if _overlaps(prefix, ours):
                    refuse('PID %d record %s writes %s, which overlaps this run\'s read dependency %s' % (pid, entry['path'], prefix, ours))
        for prefix in record.get('read_scope', []):
            for ours in scope['write']:
                if _overlaps(prefix, ours):
                    refuse('PID %d record %s reads %s, which this run would write under %s' % (pid, entry['path'], prefix, ours))
        for prefix in record.get('file_write_scope', []):
            for ours in scope['file_write'] + scope['file_read']:
                if _file_overlaps(prefix, ours, project):
                    refuse('PID %d record %s writes file scope %s, which overlaps this run\'s file %s' % (pid, entry['path'], prefix, ours))
            for protected in PROTECTED_FILES:
                if _file_overlaps(prefix, protected, project):
                    refuse('PID %d record %s declares writes to protected sealed files %s' % (pid, entry['path'], protected))
    report['summary'] = ('%d other live editor(s): %s' % (len(others), ', '.join(str(pid) for pid, _ in others))
                         + ('; refused: ' + report['reasons'][0] if report['reasons'] else '; all recorded with disjoint scope'))
    return report


def require_parallel_editors(project, profile, own_pid):
    """Raise RuntimeError naming PID, record and overlapping prefix unless the check passes."""
    report = parallel_editor_report(project, profile, own_pid)
    if report['verdict'] != 'PASS':
        raise RuntimeError('GeoCity refuses to generate beside another Unreal editor: ' + '; '.join(report['reasons']))
    return report


def write_parallel_record(project, pid, task, operator_thread_id, authority, original_map, write_scope,
                          file_write_scope=(), control_endpoints=None, assignment_ref=None,
                          generation_authorized=False, written_by=None, process_start=None,
                          read_scope=(), file_read_scope=()):
    """Create Staging/ParallelEditors/EDITOR_<pid>.json for a live editor; a stale file for a reused PID is moved aside."""
    project = Path(project).resolve(strict=True)
    pid = int(pid)
    folder = project / PARALLEL_RECORDS
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ('EDITOR_%d.json' % pid)
    start = process_start or process_start_utc(pid)
    if path.is_file():
        previous = json.loads(path.read_text(encoding='utf-8-sig'))
        before, now = parse_utc(previous.get('process_start_utc')), parse_utc(start)
        if before is not None and now is not None and abs((before - now).total_seconds()) <= START_TOLERANCE_SECONDS and not previous.get('released_utc'):
            raise RuntimeError('A live record already exists for PID %d: %s' % (pid, path))
        stale = folder / 'Stale'
        stale.mkdir(exist_ok=True)
        path.replace(stale / ('EDITOR_%d_%s.json' % (pid, datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))))
    record = {'schema': PARALLEL_EDITOR_SCHEMA, 'pid': pid, 'process_start_utc': start, 'task': task,
              'operator_thread_id': operator_thread_id, 'authority': authority, 'assignment_ref': assignment_ref,
              'original_map': original_map, 'write_scope': list(write_scope), 'read_scope': list(read_scope),
              'file_write_scope': list(file_write_scope), 'file_read_scope': list(file_read_scope),
              'control_endpoints': control_endpoints or {}, 'generation_authorized': bool(generation_authorized),
              'no_save_all': True, 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'written_by': written_by or 'geocity_runtime_guard.write_parallel_record', 'editor_live': True,
              'released_utc': None}
    with path.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
    return str(path)


def release_parallel_record(project, pid):
    """Mark EDITOR_<pid>.json released at exit; the file is kept as history."""
    path = Path(project).resolve(strict=True) / PARALLEL_RECORDS / ('EDITOR_%d.json' % int(pid))
    record = json.loads(path.read_text(encoding='utf-8-sig'))
    record['editor_live'] = False
    record['released_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    path.write_text(json.dumps(record, indent=2), encoding='utf-8')
    return str(path)
