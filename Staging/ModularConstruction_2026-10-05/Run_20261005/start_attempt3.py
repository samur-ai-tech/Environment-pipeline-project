from pathlib import Path
from datetime import datetime,timezone
import unreal,json,os,hashlib
import geocity_runtime_guard,geocity_editor_action,geocity_roadbld_clip
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
assert os.getpid()==10460
assert len(geocity_runtime_guard.verify())==12
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
profile=json.loads((ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json').read_text())
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert world==profile['map'] and profile['road_provider']=='RoadBLD' and profile['roadbld_workflow']['enabled'] is False
contract=profile['road_provider_contract'];assert contract['saved'] and contract['phase']=='native_generated_saved_verified'
for row in contract['native_component_bindings']:
    comp=unreal.find_object(None,row['component']);assert comp,row['component']
    assert comp.static_mesh.get_path_name()==row['mesh']
    assert geocity_roadbld_clip._materials(comp)==row['material_slots']
    assert geocity_roadbld_clip._transform(comp.get_world_transform())==row['component_world_transform']
for path in contract['owned_actor_paths']:assert unreal.find_object(None,path),path
hd=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_class().get_name()=='HoudiniAssetActor'];assert len(hd)==1
w=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0]);assert not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled()
build=json.loads((HERE/'USE_FIX_BUILD.json').read_text())
asset=unreal.load_asset('/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank')
assert Path(asset.get_editor_property('asset_import_data').get_first_filename()).resolve()==Path(build['source_after']).resolve()
lease=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
fields=geocity_editor_action.lease_fields(lease.read_text().splitlines()[-1]);assert fields['assigned_editor_PID']==str(os.getpid()) and fields['operator_thread_id']=='01a10c77-46ba-7001-a657-5014f6205d3a'
with lease.open('a') as f:f.write('\n'+datetime.now(timezone.utc).isoformat()+' OWNER=CODEX_MANAGED_SYSTEMS_TASK4 manager_thread_id=01a10c77-46ba-7001-a657-5014f6205d3a operator_thread_id=01a10c77-46ba-7001-a657-5014f6205d3a assigned_editor_PID='+str(os.getpid())+' map='+world+' activation=MANAGER_ACTIVATED scope=new18families_retained_Houdini_generation_reuse_saved_roads ordinary_generation_authorized=true\n')
(HERE/'ATTEMPT3_START.json').write_text(json.dumps({'pid':os.getpid(),'map':world,'source':build['source_after'],'runtime_guard_modules':12,'clean_before_run':True,'saved_native_road_components_verified':len(contract['native_component_bindings']),'saved_native_road_actors_verified':len(contract['owned_actor_paths']),'utc':datetime.now(timezone.utc).isoformat()},indent=2))
geocity_editor_action.generate_current_area()
print('Ordinary Houdini generation started with new kits and retained saved native roads.')
