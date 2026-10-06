"""Resume only native authoring after a captured adapter error; reuse full actual HDA cook."""
import datetime
import importlib
import json
import os
from pathlib import Path
import unreal
import geocity_bank_workflow as workflow
import geocity_roadbld_workflow as native

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/AppearanceRepair_2026-10-03'
assert workflow.ACTIVE
operation = workflow.ACTIVE[-1]
operation.guard()
operation.guard_processes()
assert not operation.watch_tick and not operation.save_tick
assert operation.native_road_phase == 'authoring'
assert operation.state['phase'].startswith('failed_')
assert operation.state.get('generator_revision') == 'r018_retained_appearance'
assert operation.state.get('instance_count') in (16009, 18016)
assert operation.state.get('native_material_family_count') == 40
assert operation.api.is_asset_cooking_paused()
assert all(not r.tick_handle for r in native.ACTIVE)
receipt = json.loads(operation.receipt.read_text(encoding='utf-8'))
assert receipt['generator_revision'] == 'r018_retained_appearance'
assert receipt['surface_geometry']['road_provider']['provider'] == 'houdini'
assert operation.receipt.stat().st_mtime >= operation.state['cook_started_epoch']
assert receipt.get('roadbld_centerlines') and not receipt.get('partial_output')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
failure = {'official_workflow': operation.state, 'native_workflow': native.status()}
(HERE / ('NATIVE_FAILURE_' + stamp + '.json')).write_text(json.dumps(failure, indent=2), encoding='utf-8')
if native.ACTIVE:
    failed = native.ACTIVE[-1]
    failed.guard()
    assert failed.state['phase'].startswith('failed_') and not failed.tick_handle
    if failed.network:
        failed.network.abort_and_wait_for_pending_rebuild()
    staged = failed.owned_actors()
    recorded = set(failed.state.get('staged_actor_paths', []))
    assert {_a.get_path_name() for _a in staged} == recorded, 'Review exact failed native kit paths before removal'
    for actor in staged:
        tags = {str(t) for t in actor.get_editor_property('tags')}
        assert {'GeoCity_RoadBLD', 'GeoCityArea_' + failed.area, 'GeoCityRevision_' + failed.revision}.issubset(tags)
        assert actor.get_path_name().startswith(failed.p['map'] + '.')
    for actor in reversed(staged):
        assert failed.actor_subsystem.destroy_actor(actor)
    assert not recorded.intersection(a.get_path_name() for a in failed.actor_subsystem.get_all_level_actors())
importlib.reload(native)
operation.native_road_phase = 'export'
operation.state['phase'] = 'cooked_verified'
operation.state.pop('error', None)
operation.write()
operation.wrapper.on_post_cook_delegate.add_callable(operation.after_cook)
operation.wrapper.on_post_processing_delegate.add_callable(operation.after_processing)
operation.watch_tick = unreal.register_slate_post_tick_callback(operation.watch)
try:
    operation.begin_native_roads(receipt)
except Exception as exc:
    operation.fail('failed_native_road_transaction', exc)
    raise
print(json.dumps({'phase': operation.state['phase'], 'native_phase': operation.native_road_run.state['phase'],
                  'reused_completed_HDA_cook': True, 'failed_attempt_receipt_preserved': True}))
