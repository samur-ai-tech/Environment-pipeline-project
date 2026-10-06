"""Prepared v3 fresh-session owner. No action at import; no launcher included.

Root must review this package and issue an actual-PID lease and activation.
Historical PID21780 objects/candidates are never reconstructed or rebound.
"""
import copy
import hashlib
import importlib
import inspect
import json
import marshal
import os
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MANIFEST = HERE / 'TASK2_V3_FRESH_PACKAGE_20261004.json'
ACTIVATION = HERE / 'MANAGER_V3_FRESH_OWNER_ACTIVATION.json'
STATE = {'installed': False, 'handle': None, 'runtime': None}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def authorize(stage):
    m, a = read(MANIFEST), read(ACTIVATION)
    assert a['package_sha256'] == sha(MANIFEST) and a['installer_sha256'] == sha(__file__)
    assert a['allowed_stages'][stage] is True and a['actual_pid'] == os.getpid()
    assert a['baseline_reconciled_by_root'] is True, 'Changed saved-map baseline requires root reconciliation'
    assert sha(m['observed_map']['path']) == a['approved_map_sha256']
    lease = (ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
    assert lease == a['actual_pid_lease_line'] and 'OWNER=NONE' not in lease
    assert 'assigned_editor_PID=' + str(os.getpid()) in lease
    assert 'worker_thread_id=01a102e1-25e6-7f13-b593-4988290a283b' in lease
    for name, expected in m['six_source_sha256'].items():
        assert sha(ROOT / 'Content/Python' / name) == expected, name
    for path, expected in m['source_review_receipt_sha256'].items():
        assert sha(ROOT / path) == expected
    return m, a


def runtime_code(fn):
    fn = getattr(fn, '__func__', fn)
    return hashlib.sha256(marshal.dumps(fn.__code__)).hexdigest()


def installed_code_matches_source(module, reviewed_path, reviewed_sha256):
    """Bind the loaded identity and code to the manifest, never to its own file."""
    reviewed_path = Path(reviewed_path).resolve(strict=True)
    assert Path(module.__file__).resolve(strict=True) == reviewed_path, 'Alternate loaded module: ' + module.__name__
    assert module.__spec__ and Path(module.__spec__.origin).resolve(strict=True) == reviewed_path, 'Alternate module origin'
    assert sha(reviewed_path) == reviewed_sha256, 'Reviewed module hash differs: ' + module.__name__
    reviewed_source = reviewed_path.read_bytes()
    expected = {}
    def walk(code):
        expected[code.co_qualname] = code
        for value in code.co_consts:
            if isinstance(value, types.CodeType):
                walk(value)
    # Use loaded co_filename so slash spelling does not create false differences.
    functions = [v for v in vars(module).values() if inspect.isfunction(v) and v.__module__ == module.__name__]
    for cls in list(vars(module).values()):
        if inspect.isclass(cls) and cls.__module__ == module.__name__:
            functions.extend(v for v in vars(cls).values() if inspect.isfunction(v))
    result = {}
    for fn in functions:
        assert Path(fn.__code__.co_filename).resolve(strict=True) == reviewed_path, 'Alternate function origin: ' + fn.__qualname__
        expected.clear()
        walk(compile(reviewed_source, fn.__code__.co_filename, 'exec', dont_inherit=True))
        want = hashlib.sha256(marshal.dumps(expected[fn.__qualname__])).hexdigest()
        assert runtime_code(fn) == want, fn.__qualname__
        result[fn.__qualname__] = want
    return result


def idle(a):
    import unreal as u
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_path_name() == a['original_map']
    api = u.HoudiniPublicAPIBlueprintLib.get_api()
    assert api.is_asset_cooking_paused()
    settings = u.load_object(None, '/Script/UnrealEd.Default__EditorLoadingSavingSettings')
    assert not settings.get_editor_property('bAutoSaveEnable')
    for name in ['geocity_bank_workflow', 'geocity_roadbld_workflow']:
        for run in getattr(sys.modules.get(name), 'ACTIVE', []):
            assert all(getattr(run, key, None) is None for key in ['watch_tick', 'save_tick', 'tick_handle'])
    return u, api


def install_fresh():
    m, a = authorize('install_fresh')
    idle(a)
    assert not STATE['installed']
    for name in ['geocity_bank_workflow', 'geocity_roadbld_workflow']:
        assert not getattr(sys.modules.get(name), 'ACTIVE', []), 'Fresh-session installation only'
    codes = {}
    # Normal imports only. Already loaded modules must match; never reload or rebind stale classes.
    for filename, reviewed_sha256 in m['six_source_sha256'].items():
        reviewed_path = (ROOT / 'Content/Python' / filename).resolve(strict=True)
        module_name = filename[:-3]
        spec = importlib.util.find_spec(module_name)
        assert spec and spec.origin and Path(spec.origin).resolve(strict=True) == reviewed_path, 'Alternate import resolution: ' + module_name
        assert sha(reviewed_path) == reviewed_sha256, 'Reviewed source changed before import: ' + module_name
        module = importlib.import_module(module_name)
        codes[filename] = installed_code_matches_source(module, reviewed_path, reviewed_sha256)
    STATE.update(installed=True, runtime=dict(python=sys.version, cache_tag=sys.implementation.cache_tag,
        marshal_version=marshal.version, code_sha256=codes))
    return STATE['runtime']


def regenerate_saved_original():
    m, a = authorize('regenerate_saved_original')
    assert STATE['installed']
    u, api = idle(a)
    assert api.is_session_valid(), 'Root must authorize and establish official session while paused first'
    assert u.get_editor_subsystem(u.WorldBLDAuthSubsystem).has_license_for_tool('RoadBLD')
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    # A separate fresh readback must reconcile actual saved actors/bindings/dependencies,
    # single HDA/auto flags, material child and the changed map hash before this point.
    assert sha(a['fresh_baseline_receipt']) == a['fresh_baseline_receipt_sha256']
    baseline = read(a['fresh_baseline_receipt'])
    assert baseline['pid'] == os.getpid() and baseline['map'] == a['original_map']
    assert baseline['saved_ownership_bindings_dependencies_verified'] is True
    assert baseline['HDA_autoCook'] is False and baseline['HDA_autoBake'] is False
    bank = sys.modules['geocity_bank_workflow']
    native = sys.modules['geocity_roadbld_workflow']
    assert not bank.ACTIVE and not native.ACTIVE
    return bank.run(str(ROOT / m['profile']), 'regenerate', reviewed_dirty_packages=[], release_menu_lease=False)


def correct_new_failed_candidate():
    """Optional separately activated continuation of a NEW session's measured failure."""
    m, a = authorize('correct_new_failed_candidate')
    assert STATE['installed']
    u, api = idle(a)
    bank, native, g = [sys.modules[n] for n in ['geocity_bank_workflow', 'geocity_roadbld_workflow', 'geocity_roadbld_grounding']]
    assert len(bank.ACTIVE) == len(native.ACTIVE) == 1
    p, r = bank.ACTIVE[0], native.ACTIVE[0]
    assert p.native_road_run is r and r.revision == a['new_failed_revision'] and r.transaction_token == a['new_failed_token']
    assert r.revision != '20261003T203730573110', 'Historical run cannot be resumed'
    assert r.state['phase'] == 'failed_validating' and not r._tick_running and r.tick_handle is None
    assert r.state['native_rebuild_completed'] and not r.state.get('saved')
    assert p.native_road_phase == 'authoring' and p.was_paused is True
    assert getattr(r, '_pending_correction', None) is None
    p.guard_processes(); p.guard(); r.guard()
    assert api.is_session_valid()
    previous = {key: copy.deepcopy(getattr(r, key)) for key in ['grounding_report', 'clipping_report']}
    # Every operation after correction, including delegate setup, is inside this rollback boundary.
    try:
        result = g.correction(r)  # Owns tick guard; preserve failed_validating on entry.
        validation = g.verify_links(r, previous, result)
        assert isinstance(validation, dict) and validation['source_coverage_accounted']
        r.validate(); r.finish()  # Pending snapshots stay alive.
        for fn, arity in [(p.after_cook, 2), (p.after_processing, 1), (p.after_bake, 2), (p.watch, 1), (p.finish_save, 1), (p.after_native_roads, 2)]:
            assert len(inspect.signature(fn).parameters) == arity
        p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
        p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
        p.suspend_transaction_autosave()
        p.started_epoch = time.time()
        p.state['phase'] = 'native_road_authoring'; p.state.pop('error', None); p.state.pop('api_error', None)
        p.write()
        p.watch_tick = u.register_slate_post_tick_callback(p.watch)
        r.on_complete = p.after_native_roads
        # Source performs staged contract/second validation/ownership checks, then
        # commit_correction immediately before is_asset_cooking_paused/resume.
        p.after_native_roads(r, True)
        assert getattr(r, '_correction_outcome', None) == 'committed'
        assert not p.state['phase'].startswith('failed'), p.state
        return result
    except Exception as exc:
        # If rollback fails this raises and retains handles; do not invoke parent.fail.
        # Remove only owner delegates/ticks via finish_operation; Engine stays paused.
        try:
            g.rollback_correction(r, exc)
        except Exception:
            p.finish_operation()
            raise
        p.fail('failed_native_road_transaction', exc)
        raise


def schedule(stage, receipt_path):
    """Future sole GameThread callback. Each stage needs separate root activation."""
    authorize(stage)
    assert STATE['handle'] is None
    assert stage in ['install_fresh', 'regenerate_saved_original', 'correct_new_failed_candidate']
    destination = Path(receipt_path).resolve()
    assert destination.parent == HERE and not destination.exists()
    import unreal as u
    def tick(delta_time):
        u.unregister_slate_post_tick_callback(STATE['handle']); STATE['handle'] = None
        with destination.open('x', encoding='utf-8') as f:
            json.dump(dict(status='STARTED', pid=os.getpid(), stage=stage), f); f.flush(); os.fsync(f.fileno())
        try:
            result = globals()[stage]()
            output = result if stage != 'regenerate_saved_original' else {'parent_phase': result.state['phase'], 'ordinary_async_lifecycle_started': True}
            report = dict(status='STAGE_RETURNED', pid=os.getpid(), stage=stage, result=output)
        except Exception:
            import traceback
            report = dict(status='STOPPED', pid=os.getpid(), stage=stage, error=traceback.format_exc())
        with destination.open('w', encoding='utf-8') as f:
            json.dump(report, f, indent=2); f.flush(); os.fsync(f.fileno())
    STATE['handle'] = u.register_slate_post_tick_callback(tick)
