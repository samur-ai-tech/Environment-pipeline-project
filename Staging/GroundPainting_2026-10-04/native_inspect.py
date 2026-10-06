"""Read-only native ground inspection; no preparation, cook or authoring."""
import datetime, hashlib, json, os, sys
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/GroundPainting_2026-10-04'
LIB=unreal.MaterialEditingLibrary
def path(o):return o.get_path_name() if o else None
def vec(v):return [v.r,v.g,v.b,v.a]
def safe(o,k):
    try:return o.get_editor_property(k)
    except Exception:return None
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
maps=assignment['original_maps']
areas=[k for k,v in maps.items() if v==world.get_outermost().get_path_name()]
assert len(areas)==1
area=areas[0]
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
assert f'assigned_editor_PID={os.getpid()} ' in lease and 'OWNER=CODEX_GROUND_PAINTING' in lease
fields=dict(t.split('=',1) for t in lease.split() if '=' in t)
assert fields['map']==maps[area] and fields['operator_thread_id']==assignment['execution_thread_id']
import geocity_runtime_guard
sources=geocity_runtime_guard.verify()
api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
hd=[a for a in actors if a.get_class().get_name()=='HoudiniAssetActor']
assert len(hd)==1
wrappers=[unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,a) for a in hd]
state={'pid':os.getpid(),'area':area,'world':world.get_outermost().get_path_name(),'sources':sources,'cooking_paused':api.is_asset_cooking_paused(),'session_valid':api.is_session_valid(),
       'hdas':[{'path':path(a),'auto_cook':w.is_auto_cooking_enabled(),'auto_bake':w.is_auto_bake_enabled()} for a,w in zip(hd,wrappers)],
       'autosave':unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
       'dirty_maps':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
       'dirty_content':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],
       'callbacks':{n:sum(getattr(r,k,None) is not None for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction')) for n in ('geocity_bank_workflow','geocity_roadbld_workflow')}}
assert state['cooking_paused'] and not state['autosave'] and not any(state['callbacks'].values())
assert all(not a['auto_cook'] and not a['auto_bake'] for a in state['hdas'])
if ARGS.get('require_clean',True):assert not state['dirty_maps'] and not state['dirty_content']
master=unreal.load_asset('/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural')
def material(mi):
    if not mi:return None
    chain=[];m=mi
    while m:
        chain.append(path(m));m=safe(m,'parent')
    scalars={str(k):LIB.get_material_instance_scalar_parameter_value(mi,k) for k in LIB.get_scalar_parameter_names(master)}
    vectors={str(k):vec(LIB.get_material_instance_vector_parameter_value(mi,k)) for k in LIB.get_vector_parameter_names(master)}
    textures={str(k):path(LIB.get_material_instance_texture_parameter_value(mi,k)) for k in LIB.get_texture_parameter_names(master)}
    return {'path':path(mi),'parents':chain,'scalars':scalars,'vectors':vectors,'textures':textures,
            'scalar_overrides':str(safe(mi,'scalar_parameter_values')),'vector_overrides':str(safe(mi,'vector_parameter_values')),'texture_overrides':str(safe(mi,'texture_parameter_values'))}
landscapes=[]
for a in actors:
    if isinstance(a,unreal.LandscapeProxy):
        comps=a.get_components_by_class(unreal.LandscapeComponent)
        origin,extent=a.get_actor_bounds(False)
        landscapes.append({'path':path(a),'label':a.get_actor_label(),'class':a.get_class().get_name(),'hidden':a.is_hidden_ed(),
            'location':[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z],
            'bounds_origin':[origin.x,origin.y,origin.z],'bounds_extent':[extent.x,extent.y,extent.z],
            'material':material(safe(a,'landscape_material')),'components':len(comps),
            'layers':str(safe(a,'editor_layer_settings')),'component_materials':[path(safe(c,'override_material')) for c in comps]})
state['landscapes']=landscapes
target=f'/Game/Project/Areas/{area}/BankIntegration_v015/Materials/MI_GeoCityGround'
state['intended_area_material']=material(unreal.load_asset(target)) if unreal.EditorAssetLibrary.does_asset_exist(target) else None
state['base_material']=material(unreal.load_asset('/Game/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural'))
state['normal_settings']={k:{'path':path(t),'srgb':safe(t,'srgb'),'compression':str(safe(t,'compression_settings'))} for k in ('Sand_01_Normal','Sand_02_Normal') for t in [unreal.load_asset(state['base_material']['textures'][k])]}
def transform(a):
 t=a.get_actor_transform();return {'translation':[t.translation.x,t.translation.y,t.translation.z],'rotation':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],'scale':[t.scale3d.x,t.scale3d.y,t.scale3d.z]}
state['actor_transforms']={path(a):transform(a) for a in actors}
state['actor_identity_digest']=hashlib.sha256(json.dumps(state['actor_transforms'],sort_keys=True).encode()).hexdigest()
state['native_mesh_components']=[{'actor':path(a),'component':path(c),'mesh':path(c.get_editor_property('static_mesh')),'materials':[path(c.get_material(i)) for i in range(c.get_num_materials())],'instances':c.get_instance_count() if isinstance(c,unreal.InstancedStaticMeshComponent) else 1} for a in actors if not isinstance(a,unreal.LandscapeProxy) for c in a.get_components_by_class(unreal.StaticMeshComponent)]
state['actor_count']=len(actors)
state['camera']=str(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_level_viewport_camera_info())
state['graph_expression_count']=len(LIB.get_material_expressions(master))
name=ARGS.get('label','inspection')
out=HERE/f'{area}_{name}_PID{os.getpid()}.json';out.write_text(json.dumps(state,indent=2),encoding='utf-8')
RESULT={'pid':os.getpid(),'area':area,'receipt':str(out),'landscapes':[{'path':s['path'],'hidden':s['hidden'],'material':s['material']['path'] if s['material'] else None,'bounds_origin':s['bounds_origin'],'bounds_extent':s['bounds_extent']} for s in landscapes], 'dirty_maps':state['dirty_maps'],'dirty_content':state['dirty_content'],'actor_count':state['actor_count'],'camera':state['camera']}
