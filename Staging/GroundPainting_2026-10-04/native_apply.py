"""Scoped area-instance appearance and Landscape binding; no graph/Grass authoring."""
import datetime,json,math,os,sys
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04';LIB=unreal.MaterialEditingLibrary
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();named_map=world.get_outermost().get_path_name()
area=next(k for k,v in assignment['original_maps'].items() if v==named_map)
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1];fields=dict(t.split('=',1) for t in lease.split() if '=' in t)
assert fields['OWNER']=='CODEX_GROUND_PAINTING' and fields['activation']=='GROUND_AUTHORING' and fields['assigned_editor_PID']==str(os.getpid()) and fields['map']==named_map
assert fields['operator_thread_id']==assignment['execution_thread_id']
import geocity_runtime_guard
geocity_runtime_guard.verify()
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction'))
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();landscapes=[a for a in actors if isinstance(a,unreal.Landscape)]
assert not unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
for a in actors:
 if isinstance(a,unreal.HoudiniAssetActor):
  w=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,a);assert not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled()
baseline=json.loads((HERE/f'{area}_baseline_PID{os.getpid()}.json').read_text())
assert sorted(a.get_path_name() for a in landscapes)==sorted(s['path'] for s in baseline['landscapes'])
base=unreal.load_asset(assignment['material_contract']['base_instance']);target=assignment['material_contract']['area_instances'][area];child=unreal.load_asset(target)
assert isinstance(base,unreal.MaterialInstanceConstant) and base.get_path_name()==assignment['material_contract']['base_instance']
allowed={base.get_path_name(),target}
assert all(a.get_editor_property('landscape_material').get_path_name() in allowed for a in landscapes)
effective_grass=[LIB.get_material_instance_scalar_parameter_value(a.get_editor_property('landscape_material'),'GeoCity_GrassCoverage') for a in landscapes]
assert len(set(effective_grass))==1
created=False
if child is None:
 package=target.split('.')[0];child=unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_GeoCityGround',package.rsplit('/',1)[0],unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew());assert child is not None
 LIB.set_material_instance_parent(child,base);unreal.EditorAssetLibrary.set_metadata_tag(child,'GeoCityOwner','GeoCity_LandscapeGrass');created=True
assert isinstance(child,unreal.MaterialInstanceConstant) and child.get_path_name()==target
assert child.get_editor_property('parent')==base
assert str(unreal.EditorAssetLibrary.get_metadata_tag(child,'GeoCityOwner'))=='GeoCity_LandscapeGrass'
before={'child_existed':not created,'effective_grass':effective_grass,'latent_child_grass':LIB.get_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage')}
scalars=ARGS['scalars'];vectors=ARGS['vectors']
assert set(scalars).issubset({'Ground_MacroContrast','Ground_SoilBlendStrength','Sand_01_Roughness','Sand_02_Roughness','Dirt_Path_Roughness','Sand_Path_Roughness'})
assert set(vectors).issubset({'Sand_01_TileCm','Sand_02_TileCm','Dirt_Path_TileCm','Sand_Path_TileCm','Sand_01_Tint','Sand_02_Tint','Dirt_Path_Tint','Sand_Path_Tint','Ground_MacroTileCm','Ground_MacroTile2Cm','Ground_MacroOffsetCm'})
before['scalars']={k:LIB.get_material_instance_scalar_parameter_value(child,k) for k in scalars}
before['vectors']={k:[getattr(LIB.get_material_instance_vector_parameter_value(child,k),c) for c in ('r','g','b','a')] for k in vectors}
for k,v in scalars.items():
 assert math.isfinite(v);LIB.set_material_instance_scalar_parameter_value(child,k,v)
 assert abs(LIB.get_material_instance_scalar_parameter_value(child,k)-v)<1e-4
for k,v in vectors.items():
 assert len(v)==4 and all(math.isfinite(c) for c in v)
 LIB.set_material_instance_vector_parameter_value(child,k,unreal.LinearColor(*v))
 assert all(abs(getattr(LIB.get_material_instance_vector_parameter_value(child,k),c)-v[i])<1e-4 for i,c in enumerate(('r','g','b','a')))
# Preserve actual effective baseline. The unused child had a latent .15 setting;
# binding that setting would activate vegetation outside this ground-only task.
LIB.set_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage',effective_grass[0]);LIB.update_material_instance(child)
applied=LIB.get_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage');assert math.isfinite(applied) and abs(applied-effective_grass[0])<1e-5
for a in landscapes:a.set_editor_property('landscape_material',child)
assert all(a.get_editor_property('landscape_material')==child for a in landscapes)
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'area':area,'recipe':ARGS,'before':before,'created_child':created,
 'landscape_paths':[a.get_path_name() for a in landscapes],'child':child.get_path_name(),'parent':base.get_path_name(),'effective_grass_after':LIB.get_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage'),
 'dirty_maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'dirty_content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
assert set(result['dirty_content'])=={child.get_outermost().get_path_name()}
assert set(result['dirty_maps'])=={named_map}
out=HERE/f'APPLY_{area}_{ARGS["revision"]}_PID{os.getpid()}.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8');RESULT=result
