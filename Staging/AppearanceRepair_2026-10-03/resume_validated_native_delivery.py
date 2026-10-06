"""Resume after captured nested Slate timeout; reuse the fully validated native candidate."""
import ast, importlib, json, time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_junctions as corners

p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();p.guard_processes();r.guard()
assert not p.watch_tick and not p.save_tick and not r.tick_handle
assert p.state['phase']=='failed_native_road_transaction'
assert r.state['phase'].endswith('native_generated_verified') and not r.network.is_road_network_stale()
assert not r.state['junction_issues'] and not r.state['geometry_issues']
assert r.state['geometry_validation_passed'] and len(r.state['native_component_bindings'])==len(r.native_geos())
assert r.clipping_report['status']=='native_conflicts_clipped_pending_independent_fit_saves_and_reopen'
assert r.capture_component_bindings(r.owned_actors())==r.state['native_component_bindings'], 'Current bindings differ from the final native candidate'
for module in (bank,native,corners):
 ast.parse(Path(module.__file__).read_text(encoding='utf-8'));importlib.reload(module)
p.__class__=bank.GeoCityRun;bank.ACTIVE.append(p)
r.__class__=native.RoadBLDRun;native.ACTIVE.append(r)
p.native_road_run=r;p.native_road_phase='authoring';r.on_complete=p.after_native_roads
p.state.update(phase='native_road_authoring',recovery='Final native candidate validated; nested Slate callback blocked by reusable tick guard')
p.state.pop('error',None);r.state.pop('error',None);p.started_epoch=time.time()
p.suspend_transaction_autosave()
r.validate()
p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
p.watch_tick=unreal.register_slate_post_tick_callback(p.watch)
r.write();p.write()
p.after_native_roads(r,True)
print(json.dumps({'parent_phase':p.state['phase'],'native_phase':r.state['phase'],
                  'native_junction_issues':0,'native_geometry_issues':0,'source_roads':len(r.roads),
                  'derived':len(r.derived_junction_roads),'official_provider_cook':'pending','extra_native_rebuild':False}))
