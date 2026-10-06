import unreal,pathlib,json,hashlib,shutil,os,datetime
P=pathlib.Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline');D=P/'Staging/DisableModularCourtyard_2026-10-06'
read=lambda p:json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
b=read(D/'BUILD.json');v=read(D/'VALIDATION.json');a=read(D/'ASSIGNMENT.json');assert v['passed'] and v['hda']==b['hda'];assert sha(b['hda']['path'])==b['hda']['sha256']
assert 'OWNER=NONE' in (P/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().strip().splitlines()[-1]
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
for p in a['profiles']:assert sha(p['path'])==p['sha256']
n=b['source'];assert sha(n['native_file'])==n['native_sha256'];obj=unreal.load_asset(n['asset']);assert pathlib.Path(obj.get_editor_property('asset_import_data').get_first_filename()).resolve()==pathlib.Path(n['source']).resolve()
backup=D/'Before';backup.mkdir(exist_ok=True);target=backup/pathlib.Path(n['native_file']).name
if target.exists():assert sha(target)==n['native_sha256']
else:shutil.copy2(n['native_file'],target)
for p in a['profiles']:shutil.copy2(p['path'],backup/(pathlib.Path(p['path']).parent.name+'_AREA_PROFILE.json'))
a.update(native_writer_pid=os.getpid(),control_endpoint='Local PythonScriptCommandlet exact saved script',writable_packages=[n['asset']],status='PROMOTING');(D/'ASSIGNMENT.json').write_text(json.dumps(a,indent=2))
task=unreal.AssetImportTask()
for k,value in dict(filename=b['hda']['path'],destination_path=n['asset'].rsplit('/',1)[0],destination_name=n['asset'].rsplit('/',1)[1],automated=True,replace_existing=True,replace_existing_settings=True,save=False,factory=unreal.HoudiniAssetFactory()).items():task.set_editor_property(k,value)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);objects=list(task.get_objects());assert len(objects)==1;obj=objects[0];assert pathlib.Path(obj.get_editor_property('asset_import_data').get_first_filename()).resolve()==pathlib.Path(b['hda']['path']).resolve()
assert 'OWNER=NONE' in (P/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().strip().splitlines()[-1]
assert unreal.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False)
rows=[]
for item in a['profiles']:
 p=pathlib.Path(item['path']);assert sha(p)==item['sha256'];x=read(p);old=read(p);c=x['building_assembly_contract'];c['retired_building_module_prefixes']=['/Game/ModularCourtyard/'];c['retired_building_family_reason']='User rejected ModularCourtyard; no automatic reuse via fallback.'
 temp=p.with_suffix('.courtyard_retired.tmp');temp.write_text(json.dumps(x,indent=2)+'\n');temp.replace(p)
 check=read(p);check['building_assembly_contract'].pop('retired_building_module_prefixes');check['building_assembly_contract'].pop('retired_building_family_reason');assert check==old
 rows.append(dict(path=str(p),sha256=sha(p),before_sha256=item['sha256']))
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
result=dict(passed=True,pid=os.getpid(),hda=b['hda'],asset=obj.get_path_name(),native_file=n['native_file'],native_sha256=sha(n['native_file']),profiles=rows,city_regenerated=False,maps_saved=[],source_assets_deleted=[],note='An editor that already loaded the previous HDA must load the saved updated asset before the next generation. Other editor instances untouched.')
(D/'PROMOTION.json').write_text(json.dumps(result,indent=2));print('PROMOTION_PASS',2)
