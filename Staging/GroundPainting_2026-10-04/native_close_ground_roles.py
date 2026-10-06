"""Read-only exact close-view Landscape paint weights; no material/cook operations."""
import datetime, hashlib, json, os, sys
from pathlib import Path
import unreal, geocity_runtime_guard

ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/GroundPainting_2026-10-04'
REV=HERE/'Revision_2026-10-05'
A=json.loads((HERE/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
W=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
MAP=W.get_outermost().get_path_name()
AREA=next(k for k,v in A['original_maps'].items() if v==MAP)
assert AREA=='GazaShujaiya' and os.getpid()==ARGS['pid']
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
F=dict(x.split('=',1) for x in lease.split() if '=' in x)
assert F['OWNER']=='CODEX_GROUND_PAINTING' and F['assigned_editor_PID']==str(os.getpid())
assert F['map']==MAP and F['operator_thread_id']==A['execution_thread_id']
sources=geocity_runtime_guard.verify()
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction'))
assert not unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for actor in actors:
    if isinstance(actor,unreal.HoudiniAssetActor):
        wrapper=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,actor)
        assert not wrapper.is_auto_cooking_enabled() and not wrapper.is_auto_bake_enabled()
def dirty():
    return {'maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], 'content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
before=dirty()
allowed={A['material_contract']['master'].split('.')[0],A['material_contract']['area_instances'][AREA].split('.')[0]}
assert before['maps']==[] and set(before['content'])<=allowed
out=REV/f'CLOSE_GROUND_ROLES_PID{os.getpid()}.json'
assert not out.exists()
center=(-1268.1745794274116,2408.9167042506506,4835.460048837922)
layers=('Sand_01','Sand_02','Dirt_Path','Sand_Path')
rows=[]
for actor in actors:
    if not isinstance(actor,unreal.Landscape): continue
    for dx,dy in ((0,0),(-100,0),(100,0),(0,-100),(0,100)):
        loc=unreal.Vector(center[0]+dx,center[1]+dy,center[2])
        candidates=[]
        for component in actor.get_components_by_class(unreal.LandscapeComponent):
            origin,extent,radius=unreal.SystemLibrary.get_component_bounds(component)
            if abs(loc.x-origin.x)<=extent.x and abs(loc.y-origin.y)<=extent.y:
                candidates.append(component)
        assert len(candidates)==1, (actor.get_path_name(),dx,dy,len(candidates))
        component=candidates[0]
        weights={n:float(component.editor_get_paint_layer_weight_by_name_at_location(loc,n)) for n in layers}
        assert abs(sum(weights.values())-1)<.02, weights
        rows.append({'landscape':actor.get_path_name(),'component':component.get_path_name(),'location_cm':[loc.x,loc.y,loc.z],'weights':weights})
assert len(rows)==10 and dirty()==before and geocity_runtime_guard.verify()==sources
result={'pid':os.getpid(),'world':MAP,'area':AREA,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'samples':rows,'dirty_before':before,'dirty_after':dirty(),'native_mutation':False,'scope':'saved paint lookup at close target and one-metre neighbors'}
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={'receipt':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'samples':rows,'native_mutation':False}
