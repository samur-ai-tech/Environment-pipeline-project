from pathlib import Path
from datetime import datetime,timezone
import unreal,json,os,sys,hashlib,subprocess
import geocity_runtime_guard,geocity_editor_action
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
auth=read(HERE/'CONNECTION_AUTHORIZATION.json')
assert auth['status']=='PREPARED' and auth['ordinary_generation_authorized']
assert os.getpid()==25464
assert len(geocity_runtime_guard.verify())==12
api=unreal.HoudiniPublicAPIBlueprintLib.get_api();assert api.is_asset_cooking_paused()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert world==auth['map']
old=read(Path(auth['profile_path']));proposed=read(Path(auth['proposed_profile_ref']['path']))
assert sha(Path(auth['profile_path']))==auth['profile_before_sha256']
assert sha(Path(auth['proposed_profile_ref']['path']))==auth['proposed_profile_ref']['sha256']
assert sha(Path(auth['external_hda_ref']['path']))==auth['external_hda_ref']['sha256']
assert sha(Path(auth['registry_ref']['path']))==auth['registry_ref']['sha256']
dirty={p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
material_package=old['landscape_material'].split('.')[0]
assert dirty=={material_package} and not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
mat=unreal.load_asset(old['landscape_material'])
for name,entry in proposed['surface_normal_overrides'].items():
    tex=unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mat,name)
    assert tex.get_path_name()==entry['copy'] and not tex.srgb and tex.compression_settings==unreal.TextureCompressionSettings.TC_NORMALMAP
    assert sha(ROOT/'Content'/(tex.get_path_name().split('.')[0][6:]+'.uasset'))==entry['current_native_package_sha256']
lease=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
fields=geocity_editor_action.lease_fields(lease.read_text().splitlines()[-1])
assert fields['operator_thread_id']==auth['operator_thread_id'] and fields['assigned_editor_PID']==str(os.getpid())
utc=datetime.now(timezone.utc).isoformat()
with lease.open('a',encoding='utf-8') as f:f.write('\n'+utc+' OWNER=CODEX_MANAGED_SYSTEMS_TASK4 manager_thread_id='+auth['operator_thread_id']+' operator_thread_id='+auth['operator_thread_id']+' assigned_editor_PID='+str(os.getpid())+' map='+world+' activation=MODULAR_HDA_PROFILE_BINDING native_authorized_now=true ordinary_generation_authorized=false\n')
asset=unreal.load_asset(auth['native_hda']);assert isinstance(asset,unreal.HoudiniAsset)
assert sha(ROOT/'Content'/(auth['native_hda'][6:]+'.uasset'))==auth['native_hda_before_sha256']
hd=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_class().get_name()=='HoudiniAssetActor'];assert len(hd)==1
w=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0]);assert not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled()
task=unreal.AssetImportTask()
for k,v in {'filename':auth['external_hda_ref']['path'],'destination_path':auth['native_hda'].rsplit('/',1)[0],
            'destination_name':auth['native_hda'].rsplit('/',1)[1],'automated':True,'replace_existing':True,
            'replace_existing_settings':True,'save':False,'factory':unreal.HoudiniAssetFactory()}.items():task.set_editor_property(k,v)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
objects=list(task.get_objects());assert len(objects)==1 and isinstance(objects[0],unreal.HoudiniAsset)
asset=objects[0];assert asset.get_path_name().split('.')[0]==auth['native_hda']
source=asset.get_editor_property('asset_import_data').get_first_filename()
assert Path(source).resolve()==Path(auth['external_hda_ref']['path']).resolve(),source
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
assert {p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}.issubset({auth['native_hda'],material_package})
assert unreal.EditorAssetLibrary.save_asset(auth['native_hda'],only_if_is_dirty=True)
assert unreal.EditorAssetLibrary.save_asset(material_package,only_if_is_dirty=True)
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
write(Path(auth['profile_path']),proposed)
auth.update(status='CONNECTED_READY_FOR_GENERATION',pid=os.getpid(),profile_after_sha256=sha(Path(auth['profile_path'])),
            imported_hda_source=source,native_hda_after_sha256=sha(ROOT/'Content'/(auth['native_hda'][6:]+'.uasset')),
            profile_registry_connected=True,actual_generation_completed=False)
write(HERE/'CONNECTION_AUTHORIZATION.json',auth)
write(HERE/'NATIVE_CONNECTION.json',{'pid':os.getpid(),'hda_asset':asset.get_path_name(),'source':source,
      'source_sha256':auth['external_hda_ref']['sha256'],'native_hda_saved':True,'profile_sha256':auth['profile_after_sha256'],
      'enabled_families':auth['family_ids'],'excluded_incomplete':auth['excluded_incomplete'],
      'normal_texture_references_reconciled':True,'texture_assets_changed':False,'dirty_content':[],'dirty_maps':[],
      'ordinary_generation_completed':False,'existing_hda_actor':hd[0].get_path_name()})
print(json.dumps({'connected_families':18,'native_parts':489,'hda_source':source,'clean':True}))
