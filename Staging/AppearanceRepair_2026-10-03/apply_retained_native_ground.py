"""Continue the original Rimal native actors with physical terrain fitting."""
import datetime, importlib, json, time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_clip as clip
import geocity_roadbld_grounding as grounding
import geocity_roadbld_landscape as landscape

p = bank.ACTIVE[-1]
r = native.ACTIVE[-1]
p.guard(); p.guard_processes(); r.guard()
assert r.area == 'GazaRimal' and not p.watch_tick and not p.save_tick and not r.tick_handle
# RebuildStatus expires completed jobs and returns a blank default Running
# struct. Authoritative live network state and exact road ledger still prove
# this same completed network is stable; never rebuild merely for that expiry.
networks = list(native._tool('RoadBLDDiscoveryToolset', 'DescribeNetwork', r.network, len(r.roads) + len(r.derived_junction_roads) + 1))
assert len(networks) == 1
info = networks[0]
assert not native._get(info, 'Stale') and not native._get(info, 'RebuildInProgress')
assert native._get(info, 'RoadCount') == len(r.roads) + len(r.derived_junction_roads)
assert {str(native._get(native._get(row, 'Actor'), 'RefPath')) for row in native._get(info, 'Roads')} == {native._path(a) for a in r.roads + r.derived_junction_roads}
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
here = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03')
(here / ('BEFORE_NATIVE_GROUND_' + stamp + '.json')).write_text(json.dumps({'official':p.state,'native':r.state},indent=2),encoding='utf-8')
for module in (native, clip, grounding, landscape):
    importlib.reload(module)
native.ACTIVE.append(r); r.__class__ = native.RoadBLDRun
r.on_complete = p.after_native_roads
p.suspend_transaction_autosave()
try:
    patch_type = getattr(unreal, 'LandscapePatchComponent', None)
    if patch_type:
        for actor in r.owned_actors():
            for patch in actor.get_components_by_class(patch_type):
                patch.set_is_enabled(False)
    r.state.update(phase='clipping',native_rebuild_completed=True)
    r.state.pop('error',None); r.write()
    r.clip_final_geometry()
    r.state['phase']='validating';r.write()
    r.validate();r.finish()
except Exception as exc:
    r.fail(exc)
    (here / ('NATIVE_GROUND_FAILURE_' + stamp + '.json')).write_text(json.dumps({'error':repr(exc),'native_phase':r.state['phase']},indent=2),encoding='utf-8')
    raise
p.native_road_phase='authoring'; p.native_road_run=r; p.started_epoch=time.time()
p.state.pop('error',None)
p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
p.watch_tick=unreal.register_slate_post_tick_callback(p.watch)
p.after_native_roads(r,True)
print(json.dumps({'area':r.area,'physical_native_ground':r.state['native_grounding_validation']['passed'],
    'native_components':len(r.state['native_component_bindings']),
    'same_source_empty_placeholders':len(r.state['native_grounding_validation']['automatic_empty_geometry']),
    'official_phase':p.state['phase'],'map_saved':False}))
