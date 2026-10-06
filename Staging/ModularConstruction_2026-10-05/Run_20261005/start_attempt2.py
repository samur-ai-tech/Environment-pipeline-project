from pathlib import Path
from datetime import datetime,timezone
import unreal,json,os,sys,hashlib
import geocity_runtime_guard,geocity_editor_action
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.getpid()==31508
assert len(geocity_runtime_guard.verify())==12
api=unreal.HoudiniPublicAPIBlueprintLib.get_api();assert api.is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert world=='/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
hd=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_class().get_name()=='HoudiniAssetActor'];assert len(hd)==1
w=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0]);assert not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled()
lease=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
fields=geocity_editor_action.lease_fields(lease.read_text().splitlines()[-1]);assert fields['assigned_editor_PID']==str(os.getpid()) and fields['operator_thread_id']=='01a10c77-46ba-7001-a657-5014f6205d3a'
build=json.loads((HERE/'USE_FIX_BUILD.json').read_text());assert sha(Path(build['source_after']))==build['source_after_sha256']
path='/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank'
before=sha(ROOT/'Content'/(path[6:]+'.uasset'))
task=unreal.AssetImportTask()
for k,v in {'filename':build['source_after'],'destination_path':path.rsplit('/',1)[0],'destination_name':path.rsplit('/',1)[1],'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':False,'factory':unreal.HoudiniAssetFactory()}.items():task.set_editor_property(k,v)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
objects=list(task.get_objects());assert len(objects)==1 and objects[0].get_path_name().split('.')[0]==path
assert Path(objects[0].get_editor_property('asset_import_data').get_first_filename()).resolve()==Path(build['source_after']).resolve()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
assert {p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}.issubset({path})
assert unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=True)
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
with lease.open('a') as f:f.write('\n'+datetime.now(timezone.utc).isoformat()+' OWNER=CODEX_MANAGED_SYSTEMS_TASK4 manager_thread_id=01a10c77-46ba-7001-a657-5014f6205d3a operator_thread_id=01a10c77-46ba-7001-a657-5014f6205d3a assigned_editor_PID='+str(os.getpid())+' map='+world+' activation=MANAGER_ACTIVATED scope=new18families_retained_Houdini_generation ordinary_generation_authorized=true\n')
(HERE/'ATTEMPT2_START.json').write_text(json.dumps({'pid':os.getpid(),'native_hda':path,'before_sha256':before,'after_sha256':sha(ROOT/'Content'/(path[6:]+'.uasset')),'source':build,'runtime_guard_modules':12,'map':world,'clean_before_run':True,'utc':datetime.now(timezone.utc).isoformat()},indent=2))
geocity_editor_action.generate_current_area()
print('Ordinary generation invoked using corrected retained HDA and RoadBLD settings adapter.')
