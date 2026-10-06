"""Continue original Rimal actors using measured native multiway junction topology."""
import ast, datetime, importlib, json, time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_junctions as corners
import geocity_roadbld_topology as topology

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03')
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();p.guard_processes();r.guard()
assert r.area=='GazaRimal' and r.state['phase']=='failed_rebuilding'
assert p.state['phase']=='failed_native_road_transaction' and r.rebuild_pass==1
assert not p.watch_tick and not p.save_tick and not r.tick_handle
assert not r.junction_repair and not r.derived_junction_roads and not r.state.get('junction_repair_report')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
(HERE/('RIMAL_TOPOLOGY_BEFORE_'+stamp+'.json')).write_text(json.dumps({'official':p.state,'native':r.state},indent=2),encoding='utf-8')
for module in (bank,native,corners,topology):
 ast.parse(Path(module.__file__).read_text(encoding='utf-8'));importlib.reload(module)
p.__class__=bank.GeoCityRun;bank.ACTIVE.append(p)
r.__class__=native.RoadBLDRun;native.ACTIVE.append(r)
r.on_complete=p.after_native_roads;r.junction_repair=corners.repair_native_corners(r)
assert len(r.junction_repair['automatic_native_junctions'])==3 and not r.derived_junction_roads
for geo in r.native_geos():native._set(geo,'bDisableIntersectionLandscapeAlignment',True)
p.native_road_phase='authoring';p.native_road_run=r;p.started_epoch=time.time()
p.state.update(phase='native_road_authoring',recovery='Exact original source endpoints retained; geographic T/fourway native junctions independently checked')
p.state.pop('error',None);r.state.pop('error',None)
p.suspend_transaction_autosave()
p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
p.watch_tick=unreal.register_slate_post_tick_callback(p.watch)
r.request_rebuild();r.tick_handle=unreal.register_slate_post_tick_callback(r.tick)
p.write();r.write()
print(json.dumps({'area':r.area,'source_roads':len(r.roads),'derived_roads':len(r.derived_junction_roads),
                  'native_multiway_issues_pending_physical_geometry_check':len(r.junction_repair['automatic_native_junctions']),
                  'rebuild_pass':r.rebuild_pass,'phase':p.state['phase']}))
