"""Bounded four-surface appearance overrides; never write Grass or bindings."""
import datetime,hashlib,json,math,os,sys
from pathlib import Path
import unreal,geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04';REV=HERE/'Revision_2026-10-05';LIB=unreal.MaterialEditingLibrary
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();named_map=world.get_outermost().get_path_name();area=next(k for k,v in assignment['original_maps'].items() if v==named_map)
fields=dict(t.split('=',1) for t in [s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1].split() if '=' in t)
assert fields['OWNER']=='CODEX_GROUND_PAINTING' and fields['activation']=='GROUND_AUTHORING' and fields['assigned_editor_PID']==str(os.getpid()) and fields['map']==named_map and fields['operator_thread_id']==assignment['execution_thread_id']
geocity_runtime_guard.verify();assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction'))
assert not unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for a in actors:
 if isinstance(a,unreal.HoudiniAssetActor):
  w=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,a);assert not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled()
baseline_path=Path(ARGS['baseline_receipt']).resolve();assert HERE in baseline_path.parents
baseline=json.loads(baseline_path.read_text());assert baseline['pid']==os.getpid() and baseline['world']==named_map and not baseline['dirty_maps'] and not baseline['dirty_content']
def path(o):return o.get_path_name() if o else None
def transforms():
 return {path(a):{'translation':[a.get_actor_transform().translation.x,a.get_actor_transform().translation.y,a.get_actor_transform().translation.z],'rotation':[a.get_actor_transform().rotation.x,a.get_actor_transform().rotation.y,a.get_actor_transform().rotation.z,a.get_actor_transform().rotation.w],'scale':[a.get_actor_transform().scale3d.x,a.get_actor_transform().scale3d.y,a.get_actor_transform().scale3d.z]} for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
assert transforms()==baseline['actor_transforms']
child=unreal.load_asset(assignment['material_contract']['area_instances'][area]);base=unreal.load_asset(assignment['material_contract']['base_instance']);master=unreal.load_asset(assignment['material_contract']['master'])
assert isinstance(child,unreal.MaterialInstanceConstant) and child.get_editor_property('parent')==base
assert base.get_editor_property('parent')==master
landscapes=[a for a in actors if isinstance(a,unreal.LandscapeProxy)]
assert sorted(path(a) for a in landscapes)==sorted(s['path'] for s in baseline['landscapes'])
assert all(a.get_editor_property('landscape_material')==child and a.get_actor_scale3d().x==100 and a.get_actor_scale3d().y==100 for a in landscapes)
targets=('Sand_01','Sand_02','Dirt_Path','Sand_Path');shared='/Game/Project/Shared/SurfacePainting/Appearance_20261003'
allowed_content={master.get_outermost().get_path_name(),child.get_outermost().get_path_name()}|{shared+'/Textures/T_'+n+'_Mask_GeoCity' for n in ('Sand_01','Sand_02','Dirt_Path_01','Sand_Path_01')}
assert {path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}.issubset(allowed_content)
assert {path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()}.issubset({named_map})
scalar_allow={t+s for t in targets for s in ('_Roughness','_NormalStrength','_FarScale')}|{'Ground_MacroContrast','Ground_SoilBlendStrength','GeoCity_DistanceStartCm','GeoCity_DistanceRangeCm','GeoCity_RoughnessDetail','GeoCity_AOStrength','GeoCity_MacroAmount','GeoCity_CellScale','GeoCity_PatternScale'}
out=REV/f'APPLY_{area}_{ARGS["revision"]}_PID{os.getpid()}.json';assert not out.exists(), 'Preserve prior application; use a new reviewed revision'
vector_allow={t+s for t in targets for s in ('_Tint','_TileCm')}|{'Ground_MacroTileCm','Ground_MacroTile2Cm','Ground_MacroOffsetCm'}
scalars=ARGS['scalars'];vectors=ARGS['vectors'];assert set(scalars)<=scalar_allow and set(vectors)<=vector_allow
assert set(scalars)<={str(k) for k in LIB.get_scalar_parameter_names(master)} and set(vectors)<={str(k) for k in LIB.get_vector_parameter_names(master)}
for k,v in scalars.items():
 assert math.isfinite(v)
 if k.endswith('_NormalStrength'):assert 0<=v<=3
 if k.endswith('_FarScale'):assert 1<=v<=16
 if k.endswith('_Roughness') or k in ('Ground_SoilBlendStrength','GeoCity_RoughnessDetail','GeoCity_AOStrength','GeoCity_MacroAmount'):assert 0<=v<=1
 if k in ('GeoCity_DistanceStartCm','GeoCity_DistanceRangeCm'):assert 100<=v<=100000
 if k in ('GeoCity_CellScale','GeoCity_PatternScale'):assert .01<=v<=10
for k,v in vectors.items():
 assert len(v)==4 and all(math.isfinite(x) for x in v)
 if k.endswith('_TileCm'):assert all(50<=v[i]<=200000 for i in range(3))
before={'scalars':{k:LIB.get_material_instance_scalar_parameter_value(child,k) for k in scalars},'vectors':{k:[getattr(LIB.get_material_instance_vector_parameter_value(child,k),c) for c in ('r','g','b','a')] for k in vectors},'grass':LIB.get_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage')}
for k,v in scalars.items():
 LIB.set_material_instance_scalar_parameter_value(child,k,v);assert abs(LIB.get_material_instance_scalar_parameter_value(child,k)-v)<1e-4
for k,v in vectors.items():
 LIB.set_material_instance_vector_parameter_value(child,k,unreal.LinearColor(*v));assert all(abs(getattr(LIB.get_material_instance_vector_parameter_value(child,k),c)-v[i])<1e-4 for i,c in enumerate(('r','g','b','a')))
LIB.update_material_instance(child)
assert LIB.get_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage')==before['grass']
assert transforms()==baseline['actor_transforms'] and all(a.get_editor_property('landscape_material')==child for a in landscapes)
result={'pid':os.getpid(),'area':area,'world':named_map,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'recipe':ARGS,'before':before,'effective_grass_after':LIB.get_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage'),'actor_transforms_preserved':True,'dirty_maps':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'dirty_content':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
assert set(result['dirty_content'])<=allowed_content and set(result['dirty_maps'])<={named_map}
out.write_text(json.dumps(result,indent=2),encoding='utf-8');RESULT=result
