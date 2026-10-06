import unreal,pathlib,json,hashlib,os
D=pathlib.Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/DisableModularCourtyard_2026-10-06')
r=json.loads((D/'PROMOTION.json').read_text());assert r['passed'];obj=unreal.load_asset(r['asset']);actual=obj.get_editor_property('asset_import_data').get_first_filename();assert pathlib.Path(actual).resolve()==pathlib.Path(r['hda']['path']).resolve();assert hashlib.sha256(pathlib.Path(r['native_file']).read_bytes()).hexdigest()==r['native_sha256']
for p in r['profiles']:
 assert hashlib.sha256(pathlib.Path(p['path']).read_bytes()).hexdigest()==p['sha256'];x=json.loads(pathlib.Path(p['path']).read_text());assert x['building_assembly_contract']['retired_building_module_prefixes']==['/Game/ModularCourtyard/']
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
(D/'SAVED_REOPEN.json').write_text(json.dumps(dict(passed=True,pid=os.getpid(),native_asset=r['asset'],native_source=actual,hda=r['hda'],profile_count=2),indent=2));print('SAVED_REOPEN_PASS')
