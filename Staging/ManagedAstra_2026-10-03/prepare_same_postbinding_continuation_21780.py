"""PREPARATION ONLY: reviewed correction adapter/activation contract still required.

Import is inert. No helper reload, export, network creation, road/corner replay,
rebuild, grounding pass or generic clipping call occurs in this wrapper.
"""
import copy
import datetime
import hashlib
import inspect
import json
import marshal
import os
import sys
import time
import traceback
from pathlib import Path
import fresh_delivery_21780 as d
import continue_explicit_callbacks_21780 as callbacks

PREPARATION_ONLY = True  # Change only after concrete adapter and source review.
ACTIVE = []
BASELINE = d.HERE / 'SAME_POSTBINDING_BASELINE_20261003T213208608026Z.json'
ACTIVATION = d.HERE / 'MANAGER_SAME_POSTBINDING_CORRECTION_ACTIVATION.json'
WORKER = '01a102e1-25e6-7f13-b593-4988290a283b'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def authorize():
    assert not PREPARATION_ONLY, 'Prepared only; concrete adapter and manager review outstanding'
    a = d.read(ACTIVATION)
    assignments = d.read(d.HERE / 'ASSIGNMENTS.json')
    assert a['authorized'] is True and a['pid'] == os.getpid() == 21780
    assert a['wrapper_sha256'] == digest(__file__)
    assert a['baseline_sha256'] == digest(BASELINE)
    assert assignments['one_editor_pid'] == 21780 and assignments['editor_writer_thread_id'] == WORKER
    assert assignments['tasks']['task2_delivery']['editor_calls_authorized'] is True
    for filename, expected in a['reviewed_source_sha256'].items():
        assert digest(d.ROOT / 'Content/Python' / filename) == expected, filename
    assert digest(callbacks.__file__) == a['typed_callback_helper_sha256']
    assert digest(d.__file__) == a['observer_helper_sha256']
    assert hashlib.sha256(marshal.dumps(d.call.__code__)).hexdigest() == a['observer_call_code_sha256']
    assert hashlib.sha256(marshal.dumps(callbacks.install.__code__)).hexdigest() == a['typed_install_code_sha256']
    assert digest(a['independent_review_path']) == a['independent_review_sha256']
    # Root-reviewed installation must retain existing p/r objects and ACTIVE lists.
    # Do not import/reload an adapter or source helper implicitly here.
    module = sys.modules[a['installed_adapter_module']]
    assert digest(module.__file__) == a['installed_adapter_file_sha256']
    correction = getattr(module, a['correction_function'])
    verify_links = getattr(module, a['report_lineage_verifier'])
    for fn, arity, key in [(correction, 1, 'correction_code_sha256'), (verify_links, 3, 'lineage_code_sha256')]:
        assert inspect.isfunction(fn) and fn.__code__.co_argcount == arity
        assert not fn.__code__.co_flags & 0x0c
        assert hashlib.sha256(marshal.dumps(fn.__code__)).hexdigest() == a[key]
    return a, correction, verify_links


def run(s):
    import unreal as u
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_junctions as junctions
    import geocity_roadbld_clip as clip
    activation, correction, verify_links = authorize()
    baseline = d.read(BASELINE)
    assert len(bank.ACTIVE) == len(native.ACTIVE) == 1
    p, r = bank.ACTIVE[0], native.ACTIVE[0]
    s.update(parent=p, native=r)
    assert p.native_road_run is r and type(r) is native.RoadBLDRun
    assert r.revision == baseline['revision'] == '20261003T203730573110'
    assert r.transaction_token == baseline['token']
    assert p.state['phase'] == baseline['parent_phase'] == 'failed_native_road_transaction'
    assert r.state['phase'] == baseline['native_phase'] == 'failed_validating'
    assert p.native_road_phase == 'authoring' and p.lease_line == r.lease_line
    assert not p.release_menu_lease and p.was_paused is True
    assert len(r.roads) == 40 and len(r.derived_junction_roads) == 4
    assert r.junction_repair['completed_corner_count'] == 4 and r.rebuild_pass == 3
    assert not r._tick_running
    assert all(getattr(x, k, None) is None for x in [p, r] for k in ['watch_tick', 'save_tick', 'tick_handle'])
    d.call(s, 'parent.guard', p.guard)
    d.call(s, 'native.guard', r.guard)
    d.call(s, 'sole_editor_guard', p.guard_processes)
    api = d.idle(s)
    assert d.call(s, 'Engine_valid', api.is_session_valid)
    assert not d.call(s, 'autoCook', p.wrapper.is_auto_cooking_enabled)
    assert not d.call(s, 'autoBake', p.wrapper.is_auto_bake_enabled)
    assert d.call(s, 'participant_checkpoint', lambda: junctions._owned_state(r)) == baseline['owned_participants']
    assert {k: sorted(v) for k, v in d.dirty(s).items()} == {k: sorted(v) for k, v in baseline['dirty'].items()}
    previous = {'grounding': copy.deepcopy(r.grounding_report), 'clipping': copy.deepcopy(r.clipping_report)}
    for kind in ['grounding', 'clipping']:
        assert value_sha(previous[kind]) == baseline[kind + '_report_sha256']
    old_receipt = Path(r.clipping_report['receipt'])
    assert digest(old_receipt) == baseline['immutable_clip_receipt_sha256']
    bindings = []
    for geo in d.call(s, 'native_geos', r.native_geos):
        for component in geo.get_components_by_class(u.StaticMeshComponent):
            bindings.append(dict(geo=geo.get_path_name(), source_refs=sorted(native._path(x) for x in native._get(geo, 'SourceRoads')),
                component=component.get_path_name(), mesh=native._path(component.static_mesh),
                transform=clip._transform(component.get_world_transform()), materials=clip._materials(component),
                collision=clip._collision(component, component.static_mesh)))
    assert len(bindings) == 87
    assert sorted(bindings, key=lambda x: x['component']) == sorted(baseline['full_bound_ledger'], key=lambda x: x['component'])
    assert '_GUARD_JOURNAL' in d.call.__code__.co_names
    s['report'].update(pre_parent_state=copy.deepcopy(p.state), pre_native_state=copy.deepcopy(r.state),
        preserved_reports=previous, bindings_before=bindings, baseline=str(BASELINE), old_clip_receipt_sha256=digest(old_receipt))
    d.write(s['receipt'], s['report'])
    # Only after all identity/authorization checks may the reviewed adapter edit.
    s['transition_started'] = True
    callbacks.install(s, p, r, native)
    d.call(s, 'register_post_cook_2args', lambda: p.wrapper.on_post_cook_delegate.add_callable(p.after_cook))
    d.call(s, 'register_post_processing_1arg', lambda: p.wrapper.on_post_processing_delegate.add_callable(p.after_processing))
    d.call(s, 'suspend_transaction_autosave', p.suspend_transaction_autosave)
    p.started_epoch = time.time()
    p.state.update(phase='native_road_authoring', same_postbinding_evidence=str(s['receipt']))
    r.state.update(phase='postbinding_correction', same_postbinding_evidence=str(s['receipt']))
    for state in [p.state, r.state]:
        state.pop('error', None)
        state.pop('api_error', None)
    d.call(s, 'persist_parent_start', p.write)
    d.call(s, 'persist_native_start', r.write)
    r._tick_running = True
    try:
        result = d.call(s, 'reviewed_generic_same_candidate_correction', lambda: correction(r))
        s['report']['correction_result'] = result
        assert digest(old_receipt) == baseline['immutable_clip_receipt_sha256'], 'Previous immutable ledger changed'
        assert d.call(s, 'verify_new_linked_immutable_reports', lambda: verify_links(r, previous, result)) is True
        assert value_sha(r.grounding_report) != baseline['grounding_report_sha256']
        assert value_sha(r.clipping_report) != baseline['clipping_report_sha256']
        assert Path(r.clipping_report['receipt']) != old_receipt
        assert not r.clipping_report['map_save_performed']
        assert junctions._owned_state(r) == baseline['owned_participants'], 'Source/network/road controls changed'
        s['report']['new_reports'] = dict(grounding=copy.deepcopy(r.grounding_report), clipping=copy.deepcopy(r.clipping_report))
        d.write(s['receipt'], s['report'])
        r.state['phase'] = 'validating'
        d.call(s, 'persist_validation_phase', r.write)
        d.call(s, 'ordinary_final_native_validation', r.validate)
        d.call(s, 'ordinary_native_finish', r.finish)
        p.started_epoch = time.time()
        p.watch_tick = d.call(s, 'register_parent_watch_1arg', lambda: u.register_slate_post_tick_callback(p.watch))
        # This exact callback is the first permitted path to suppression Cook.
        d.call(s, 'parent_native_completion_2args', lambda: r.on_complete(r, True))
        assert not p.state['phase'].startswith('failed'), p.state
        s['report']['status'] = 'native_validated_parent_lifecycle_resumed'
    finally:
        r._tick_running = False


def schedule():
    authorize()
    assert not ACTIVE, 'One reviewed schedule only'
    import unreal as u
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s = dict(handle=None, receipt=d.HERE / ('SAME_POSTBINDING_' + stamp + '.json'),
        journal=d.HERE / ('SAME_POSTBINDING_' + stamp + '.jsonl'), report=dict(status='scheduled', pid=os.getpid()))
    def tick(delta_time):
        d.call(s, 'unregister_one_shot', lambda: u.unregister_slate_post_tick_callback(s['handle']))
        s['handle'] = None
        try:
            run(s)
        except Exception as exc:
            s['report'].update(status='stopped', error=traceback.format_exc())
            if s.get('transition_started') and not s['report'].get('observation_hooks_restored'):
                try:
                    d.call(s, 'ordinary_native_failure_cleanup', lambda: s['native'].fail(exc))
                except Exception:
                    s['report']['cleanup_error'] = traceback.format_exc()
        d.write(s['receipt'], s['report'])
    ACTIVE.append(s)
    d.write(s['receipt'], s['report'])
    s['handle'] = d.call(s, 'register_one_shot_GameThread', lambda: u.register_slate_post_tick_callback(tick))
    return str(s['receipt'])
