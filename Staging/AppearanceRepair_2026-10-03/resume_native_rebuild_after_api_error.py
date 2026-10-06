"""Root recovery of existing authored native roads after captured async API mismatch."""
import datetime
import importlib
import json
import time
from pathlib import Path
import unreal
import geocity_bank_workflow as workflow
import geocity_roadbld_workflow as native

HERE = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03')
parent = workflow.ACTIVE[-1]
run = native.ACTIVE[-1]
parent.guard(); parent.guard_processes(); run.guard()
assert not parent.watch_tick and not parent.save_tick and not run.tick_handle
assert parent.state['phase'] == 'failed_native_road_transaction'
assert run.state['phase'] == 'failed_authoring'
assert run.cursor == run.plan['source_piece_count'] == len(run.roads)
assert parent.api.is_asset_cooking_paused()
assert run.network and run.native_geos() and not run.network.is_road_network_stale()
result = unreal.find_object(None, '/Engine/Transient.RoadBLDRebuildAsyncResult_0')
assert result and result.is_complete and not result.error
value = json.loads(result.get_value_as_json_string())
assert value.get('jobId') and value['networks'][0]['refPath'] == run.network.get_path_name()
status = native._tool('RoadBLDBuildToolset', 'RebuildStatus', value['jobId'])
assert 'SUCCEEDED' in str(native._get(status, 'State')).upper(), 'Current native rebuild must finish before recovery'
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
(HERE / ('NATIVE_ASYNC_API_FAILURE_' + stamp + '.json')).write_text(json.dumps(
    {'official': parent.state, 'native': run.state, 'native_dispatch': value}, indent=2), encoding='utf-8')
importlib.reload(native)
run.__class__ = native.RoadBLDRun
native.ACTIVE.append(run)
run.job_id = value['jobId']; run.rebuild_pass = 1; run.rebuild_started = time.monotonic()
run.state.update(phase='rebuilding', rebuild_job_id=run.job_id, rebuild_pass=1,
                 recovery='existing native40roads/83geometry retained after captured async result getter correction')
run.state.pop('error', None); run.write()
parent.native_road_phase = 'authoring'
parent.native_road_run = run
parent.state['phase'] = 'native_road_authoring'
parent.state.pop('error', None); parent.write()
parent.started_epoch = time.time()
parent.wrapper.on_post_cook_delegate.add_callable(parent.after_cook)
parent.wrapper.on_post_processing_delegate.add_callable(parent.after_processing)
parent.watch_tick = unreal.register_slate_post_tick_callback(parent.watch)
run.tick_handle = unreal.register_slate_post_tick_callback(run.tick)
print(json.dumps({'phase': parent.state['phase'], 'native_phase': run.state['phase'],
                  'actual_native_road_count': len(run.roads), 'actual_geometry_count': len(run.native_geos()),
                  'source_recreation': False}))
