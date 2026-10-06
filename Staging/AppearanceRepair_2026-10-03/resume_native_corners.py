"""Resume the exact staged native source actors after the captured diagnostics."""
import ast, datetime, importlib, json, time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_junctions as corners

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03')
parent=bank.ACTIVE[-1];run=native.ACTIVE[-1]
parent.guard();parent.guard_processes();run.guard()
assert not parent.watch_tick and not parent.save_tick and not run.tick_handle
assert parent.state['phase']=='failed_native_road_transaction'
assert run.state['phase'] in ('failed_rebuilding','failed_corner_recovery')
assert len(run.roads)==run.cursor==run.plan['source_piece_count']
assert parent.api.is_asset_cooking_paused() and not run.network.is_road_network_stale()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
(HERE/('NATIVE_CORNER_BEFORE_'+stamp+'.json')).write_text(json.dumps({'official':parent.state,'native':run.state},indent=2),encoding='utf-8')
if run.state.get('junction_repair_report'):
 assert run.state['junction_repair_report']['phase']=='failed_native_corner_repair'
 assert not run.state['junction_repair_report']['derived_junction_roads']
 for actor in run.derived_junction_roads:
  assert actor.get_path_name() in run.state['staged_actor_paths'] or actor.get_path_name() in run.state['junction_repair_report']['actual_derived_actor_paths']
  assert actor.get_path_name() not in run.initial_actor_paths
  assert not native._get(native._tool('RoadBLDDiscoveryToolset','DescribeRoad',actor),'ControlPoints')
  assert not native._get(native._get(native._tool('RoadBLDDiscoveryToolset','DescribeRoad',actor),'Network'),'RefPath')
  assert run.actor_subsystem.destroy_actor(actor), 'Exact failed empty SDK actor removal failed'
 run.state.pop('junction_repair_report')
for module in (bank,native,corners):
 ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
 importlib.reload(module)
parent.__class__=bank.GeoCityRun;bank.ACTIVE.append(parent)
run.__class__=native.RoadBLDRun;native.ACTIVE.append(run)
run.derived_junction_roads=[];run.junction_repair=None;run.clipping_report=None
for road in run.roads:
 controls=native._get(road,'ControlSpline');limits=native._get(controls,'TurnRadiusLimit')
 native._set(controls,'TurnRadiusLimit',unreal.Vector2D(100.0,limits.y))
parent.p=json.loads(parent.profile_path.read_text(encoding='utf-8'))
run.on_complete=parent.after_native_roads
try:
 run.junction_repair=corners.repair_native_corners(run)
 (HERE/('ACTUAL_NATIVE_CORNERS_'+run.area+'.json')).write_text(json.dumps(run.junction_repair,indent=2),encoding='utf-8')
 run.rebuild_pass=0
 run.request_rebuild()
 parent.native_road_run=run;parent.native_road_phase='authoring'
 parent.state.update(phase='native_road_authoring',recovery='Preserved original native source actors; supported corner connectors and precise source trim ledger')
 parent.state.pop('error',None);parent.started_epoch=time.time();parent.write()
 parent.wrapper.on_post_cook_delegate.add_callable(parent.after_cook)
 parent.wrapper.on_post_processing_delegate.add_callable(parent.after_processing)
 parent.watch_tick=unreal.register_slate_post_tick_callback(parent.watch)
 run.state.pop('error',None);run.write()
 run.tick_handle=unreal.register_slate_post_tick_callback(run.tick)
 print(json.dumps({'phase':parent.state['phase'],'native_phase':run.state['phase'],
                   'original_roads_preserved':len(run.roads),'derived_junctions':len(run.derived_junction_roads),
                   'source_recreation':False,'rebuild_job':run.job_id}))
except Exception as exc:
 run.state.update(phase='failed_corner_recovery',saved=False,error=repr(exc));run.write()
 raise
