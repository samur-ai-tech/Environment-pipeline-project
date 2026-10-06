"""Inert preparation: only reviewed helper definitions may be installed later.

No source hashes or adapter names are assumed before Task1 freezes its API.
The separate manager manifest authorizes installation, never geometry work.
"""
import copy
import datetime
import hashlib
import inspect
import json
import marshal
import os
import sys
import traceback
import types
from pathlib import Path
import fresh_delivery_21780 as d
import continue_explicit_callbacks_21780 as callbacks

PREPARATION_ONLY = True
ALLOWED = ('geocity_roadbld_grounding', 'geocity_roadbld_seams', 'geocity_roadbld_clip')
PRESERVED = ('geocity_bank_workflow', 'geocity_roadbld_workflow', 'geocity_roadbld_junctions')
MANIFEST = d.HERE / 'MANAGER_REVIEWED_HELPER_INSTALL_ACTIVATION.json'
BASELINE = d.HERE / 'SAME_POSTBINDING_BASELINE_20261003T213208608026Z.json'
STATE = {'handle': None, 'installed': False, 'before': None}


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_identity(fn):
    target = getattr(fn, '__func__', fn)
    code = target.__code__
    return dict(module=target.__module__, qualname=target.__qualname__, filename=code.co_filename,
        positional_args=code.co_argcount, keyword_only_args=code.co_kwonlyargcount,
        flags=code.co_flags, code_sha256=hashlib.sha256(marshal.dumps(code)).hexdigest())


def authorize(kind):
    assert not PREPARATION_ONLY, 'Prepared only; source freeze and installation review pending'
    assert os.getpid() == 21780 and kind in ('install', 'inspect')
    a = d.read(MANIFEST)
    assert a[kind + '_authorized'] is True and a['pid'] == 21780
    assert a['installer_sha256'] == file_sha(__file__)
    assert a['baseline_sha256'] == file_sha(BASELINE)
    assignments = d.read(d.HERE / 'ASSIGNMENTS.json')
    assert assignments['one_editor_pid'] == 21780
    assert assignments['editor_writer_thread_id'] == '01a102e1-25e6-7f13-b593-4988290a283b'
    assert assignments['tasks']['task2_delivery']['read_only_editor_calls_authorized'] is True
    assert set(a['helper_source_sha256']) == set(ALLOWED)
    assert sorted(a['install_order']) == sorted(ALLOWED)
    assert file_sha(a['independent_review_path']) == a['independent_review_sha256']
    assert file_sha(callbacks.__file__) == a['typed_callback_file_sha256']
    assert file_sha(d.__file__) == a['observer_file_sha256']
    for module_name in PRESERVED:
        module = sys.modules[module_name]
        assert file_sha(module.__file__) == a['preserved_module_file_sha256'][module_name]
    for module_name, expected in a['helper_source_sha256'].items():
        assert file_sha(d.ROOT / 'Content/Python' / (module_name + '.py')) == expected
    guard_map = a['reviewed_guard_map']
    assert set(d.FROZEN).issubset(guard_map), 'Do not drop existing guard entries'
    assert {name + '.py' for name in ALLOWED}.issubset(guard_map)
    for name, expected in guard_map.items():
        assert Path(name).name == name and name.endswith('.py')
        assert file_sha(d.ROOT / 'Content/Python' / name) == expected
    for module_name in ALLOWED:
        assert guard_map[module_name + '.py'] == a['helper_source_sha256'][module_name]
    return a


def snapshot(s):
    import unreal as u
    bank, native, junctions = [sys.modules[name] for name in PRESERVED]
    clip = sys.modules['geocity_roadbld_clip']
    assert len(bank.ACTIVE) == len(native.ACTIVE) == 1
    p, r = bank.ACTIVE[0], native.ACTIVE[0]
    assert p.native_road_run is r and r.revision == '20261003T203730573110'
    assert r.transaction_token == '500220db-e53b-4010-b6ee-04b4eb2df128'
    assert p.state['phase'] == 'failed_native_road_transaction' and r.state['phase'] == 'failed_validating'
    assert not r._tick_running and p.native_road_phase == 'authoring'
    assert all(getattr(x, k, None) is None for x in [p, r] for k in ['watch_tick', 'save_tick', 'tick_handle'])
    d.call(s, 'parent.guard', p.guard)
    d.call(s, 'native.guard', r.guard)
    d.call(s, 'sole_editor_guard', p.guard_processes)
    api = d.idle(s)
    assert d.call(s, 'Engine_valid', api.is_session_valid)
    assert not p.wrapper.is_auto_cooking_enabled() and not p.wrapper.is_auto_bake_enabled()
    bindings = []
    for geo in r.native_geos():
        for component in geo.get_components_by_class(u.StaticMeshComponent):
            bindings.append(dict(component=component.get_path_name(), mesh=native._path(component.static_mesh),
                materials=clip._materials(component), transform=clip._transform(component.get_world_transform()),
                collision=clip._collision(component, component.static_mesh)))
    assert len(bindings) == 87
    baseline = d.read(BASELINE)
    expected_bindings = [{k: row[k] for k in ['component', 'mesh', 'materials', 'transform', 'collision']} for row in baseline['full_bound_ledger']]
    assert sorted(bindings, key=lambda x: x['component']) == sorted(expected_bindings, key=lambda x: x['component'])
    assert junctions._owned_state(r) == baseline['owned_participants']
    return dict(module_ids={name: id(sys.modules[name]) for name in PRESERVED},
        active_ids=[id(bank.ACTIVE), id(native.ACTIVE), id(p), id(r)],
        class_ids=[id(type(p)), id(type(r))], sampler_id=id(r.landscape_sampler),
        callback_module_id=id(callbacks), observer_module_id=id(d),
        parent_codes={name: code_identity(getattr(p, name)) for name in ['guard', 'after_cook', 'after_processing', 'after_native_roads', 'after_bake', 'finish_save', 'watch', 'finish_operation']},
        native_codes={name: code_identity(getattr(r, name)) for name in ['guard', 'validate', 'commit', 'tick', 'finish', 'fail']},
        observer_call=code_identity(d.call), observer_guards=code_identity(d.guards),
        typed_install=code_identity(callbacks.install), typed_observe=code_identity(callbacks.observe),
        callback_frozen=copy.deepcopy(callbacks.FROZEN), on_complete=code_identity(r.on_complete),
        parent_state=copy.deepcopy(p.state), native_state=copy.deepcopy(r.state),
        participants=junctions._owned_state(r), dirty={k: sorted(v) for k, v in d.dirty(s).items()},
        bindings=sorted(bindings, key=lambda x: x['component']),
        grounding_report=copy.deepcopy(r.grounding_report), clipping_report=copy.deepcopy(r.clipping_report),
        immutable_clip_receipt_sha256=file_sha(r.clipping_report['receipt']))


def runtime_readback(a):
    values = {}
    # All named entry points are measured here under the actual editor Python.
    # No marshal/code identity is imported from the external preparation runtime.
    for label, entry in a['runtime_entrypoints'].items():
        module_name, attribute = entry['module'], entry['attribute']
        assert module_name in ALLOWED
        fn = getattr(sys.modules[module_name], attribute)
        assert inspect.isfunction(fn)
        values[label] = code_identity(fn)
    return dict(python_version=sys.version, python_executable=sys.executable,
        cache_tag=sys.implementation.cache_tag, marshal_version=marshal.version,
        helper_source_sha256=a['helper_source_sha256'], runtime_entrypoints=values,
        observer_call=code_identity(d.call), typed_install=code_identity(callbacks.install),
        guard_map=copy.deepcopy(d.FROZEN))


def perform(s, kind):
    a = authorize(kind)
    before = snapshot(s)
    if kind == 'inspect':
        assert STATE['installed'] and before == STATE['before']
        assert d.FROZEN == a['reviewed_guard_map']
        s['report'].update(status='READ_ONLY_POSTINSTALL_INSPECTION_COMPLETE', runtime=runtime_readback(a))
        return
    assert not STATE['installed']
    assert d.FROZEN == a['expected_preinstall_guard_map']
    compiled = {}
    for name in ALLOWED:
        path = d.ROOT / 'Content/Python' / (name + '.py')
        source = path.read_bytes()
        assert hashlib.sha256(source).hexdigest() == a['helper_source_sha256'][name]
        compiled[name] = compile(source, str(path), 'exec')
    old_modules = {name: sys.modules.get(name) for name in ALLOWED}
    old_dicts = {name: dict(module.__dict__) for name, module in old_modules.items() if module is not None}
    old_guard_map = copy.deepcopy(d.FROZEN)
    s['report'].update(before=before, guard_map_before=old_guard_map, status='REVIEWED_DEFINITION_INSTALL_STARTING')
    d.write(s['receipt'], s['report'])
    try:
        for name in a['install_order']:
            module = old_modules[name]
            if module is None:
                module = types.ModuleType(name)
                module.__file__ = str(d.ROOT / 'Content/Python' / (name + '.py'))
                module.__package__ = ''
                sys.modules[name] = module
            d.journal(s, 'BEFORE', operation='install_reviewed_definitions', module=name)
            # Explicit reviewed source bytes avoid timestamp/pyc ambiguity.
            # Retain existing helper module identity; clear removed definitions.
            metadata = {k: v for k, v in module.__dict__.items() if k in ['__name__', '__file__', '__package__', '__loader__', '__spec__', '__cached__', '__builtins__']}
            module.__dict__.clear()
            module.__dict__.update(metadata)
            exec(compiled[name], module.__dict__)
            d.journal(s, 'AFTER', operation='install_reviewed_definitions', module=name)
        # Intentional data update only. d.guards/d.call and callbacks stay intact.
        d.FROZEN = dict(a['reviewed_guard_map'])
        assert snapshot(s) == before, 'Installation changed preserved live inputs'
        authorize('install')  # Recheck frozen files after installation.
        s['report'].update(status='DEFINITIONS_INSTALLED_NO_AUTHORING', runtime=runtime_readback(a),
            preserved_inputs_unchanged=True, next='Separate read-only inspection, root review, then separate authored activation')
        STATE.update(installed=True, before=before)
    except Exception:
        # Definition rollback only; installation is forbidden from editing UObjects.
        for name, old in old_modules.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                old.__dict__.clear()
                old.__dict__.update(old_dicts[name])
                sys.modules[name] = old
        d.FROZEN = old_guard_map
        s['report']['definition_rollback_preserved_inputs'] = snapshot(s) == before
        raise


def schedule(kind):
    authorize(kind)
    assert STATE['handle'] is None
    import unreal as u
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s = dict(receipt=d.HERE / ('REVIEWED_HELPER_' + kind.upper() + '_' + stamp + '.json'),
        journal=d.HERE / ('REVIEWED_HELPER_' + kind.upper() + '_' + stamp + '.jsonl'),
        report=dict(status='scheduled', kind=kind, pid=os.getpid()))
    def tick(delta_time):
        u.unregister_slate_post_tick_callback(STATE['handle'])
        STATE['handle'] = None
        try:
            perform(s, kind)
        except Exception:
            s['report'].update(status='STOPPED', error=traceback.format_exc())
        d.write(s['receipt'], s['report'])
    d.write(s['receipt'], s['report'])
    STATE['handle'] = u.register_slate_post_tick_callback(tick)
    return str(s['receipt'])
