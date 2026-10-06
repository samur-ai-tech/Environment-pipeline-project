"""Import the retained shared HDA in the single owned, paused editor."""
import unreal,json,os,hashlib,subprocess
from pathlib import Path
PROJECT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=PROJECT/'Staging/AppearanceRepair_2026-10-03'
SOURCE=Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank')
lease=(PROJECT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
processes=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
assert [int(p) for p in processes.stdout.split()]==[os.getpid()]
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
profiles=[json.loads(p.read_text()) for p in (PROJECT/'Staging/ModelBank').rglob('AREA_PROFILE.json')]
profiles=[p for p in profiles if p['map']==world]
assert len(profiles)==1
profile=profiles[0]
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
dirty=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
from geocity_editor_action import acknowledged_cook_leftovers
assert set(dirty).issubset(acknowledged_cook_leftovers(PROJECT,dirty))
task=unreal.AssetImportTask()
task.filename=str(SOURCE/'GeoCity_city_v015_PermanentBank.hdalc')
task.destination_path='/Game/Project/Shared/ModelBank/HDA'
task.destination_name='GeoCity_city_v015_PermanentBank'
task.automated=True;task.replace_existing=True;task.save=False
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
asset=unreal.load_asset(profile['hda'])
assert isinstance(asset,unreal.HoudiniAsset)
assert unreal.EditorAssetLibrary.save_asset(profile['hda'],only_if_is_dirty=True)
receipt={'hda':profile['hda'],'external_sha256':hashlib.sha256(Path(task.filename).read_bytes()).hexdigest(),'named_save':True,'engine_paused':True,'city_cook':'next_official_regenerate'}
(HERE/'NATIVE_HDA_IMPORT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
