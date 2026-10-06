"""Manager-activated continuation of the one existing Shujaiya transaction."""
import datetime
import hashlib
import importlib
import json
import os
import time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_junctions as junctions

HERE = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedAstra_2026-10-03')
ROOT = HERE.parent.parent
assignment = json.loads((HERE / 'ASSIGNMENTS.json').read_text(encoding='utf-8-sig'))
worker = '01a102e1-25e6-7f13-b593-4988290a283b'
assert assignment['editor_writer_thread_id'] == worker
assert assignment['tasks']['task2_delivery']['editor_calls_authorized']
assert assignment['tasks']['task2_delivery']['status'] == 'active_editor_writer'
freeze = json.loads((HERE / 'TASK1_SOURCE_RESULT.json').read_text(encoding='utf-8-sig'))
assert freeze['status'] == 'READY_FOR_EDITOR'
for row in freeze['frozen_files'].values():
    assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256']
p = bank.ACTIVE[-1]
r = native.ACTIVE[-1]
p.guard()
r.guard()
assert os.getpid() == 32752 and ('worker_thread_id=' + worker) in p.lease_line
assert p.lease_line == r.lease_line
assert p.p['map'] == '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
assert all(x.tick_handle is None for x in native.ACTIVE)
assert not r._tick_running
assert p.api.is_session_valid() and p.api.is_asset_cooking_paused()
assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
assert r.revision == '20261003T172549017159' and r.rebuild_pass == 1
assert len(r.roads) == 40 and len(r.derived_junction_roads) == 1
assert r.derived_junction_roads[0].get_path_name().endswith(':PersistentLevel.DynamicRoad_86')
failed = json.loads((ROOT / 'Staging/AppearanceRepair_2026-10-03/TASK2_FAILED_RECOVERY_20261003T181945515173Z.json').read_text(encoding='utf-8'))
assert r.state['phase'] == 'failed_conditioning' and p.state['phase'] == 'failed_native_road_transaction'
assert r.state['error'] == failed['error']
assert r.state['junction_recovery_error'] == failed['recovery_error']
assert r.state['junction_repair_report'] == failed['native_state']['junction_repair_report']
assert 'checkpoint_version' not in r.state['junction_repair_report']
assert not r.state['junction_repair_report'].get('operation')
assert r.state['junction_repair_report']['phase'] == 'failed_native_corner_repair'

stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
evidence = ROOT / 'Staging/AppearanceRepair_2026-10-03' / ('TASK2_PRE_RESUME_' + stamp + '.json')
assert not evidence.exists()
snapshot = dict(utc=stamp, pid=os.getpid(), lease=p.lease_line, parent_state=p.state,
    native_state=r.state, transaction_token=r.transaction_token,
    previous_native_delivery=r.previous,
    roads=[x.get_path_name() for x in r.roads],
    derived=[x.get_path_name() for x in r.derived_junction_roads],
    network=r.network.get_path_name(),
    dirty_maps=[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
    dirty_content=[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],
    autosave_current=False, original_autosave=True, source_freeze=freeze['frozen_files'])
evidence.write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')

native = importlib.reload(native)
junctions = importlib.reload(junctions)
r.__class__ = native.RoadBLDRun
assert native.ACTIVE == []
native.ACTIVE.append(r)
r.junction_repair = None
r.state['phase'] = 'conditioning'
r.on_complete = p.after_native_roads
p.native_road_phase = 'authoring'
p.started_epoch = time.time()
p.state['phase'] = 'native_road_authoring'
p.state['task2_resume_evidence'] = str(evidence)
p.state.pop('error', None)
p.state.pop('api_error', None)
p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
p.watch_tick = unreal.register_slate_post_tick_callback(p.watch)

def continue_native(delta):
    r.tick(delta)
    if r.state['phase'].startswith('failed'):
        # Parent failure cleanup restores user autosave. Immediately suspend it
        # again in this same callback while the dirty failed candidate remains.
        p.suspend_transaction_autosave()
        p.write()

r.write()
p.write()
r.tick_handle = unreal.register_slate_post_tick_callback(continue_native)
print(json.dumps(dict(scheduled=True, revision=r.revision, pre_resume_evidence=str(evidence),
    existing_network=r.network.get_path_name(), existing_original_roads=len(r.roads),
    existing_derived_roads=len(r.derived_junction_roads))))
