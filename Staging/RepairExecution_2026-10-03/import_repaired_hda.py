"""Import/save the retained shared HDA while the owned Engine is paused."""
import unreal
import json
import os
import hashlib
from pathlib import Path

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/RepairExecution_2026-10-03'
SOURCE = Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank')
lease = (PROJECT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_REPAIR_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
profile = json.loads((PROJECT / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json').read_text())
dirty_maps = [p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert set(dirty_maps).issubset({profile['map']}), 'An unrelated map is dirty'
if dirty_maps:
    assert json.loads(Path(profile['workflow_receipt']).read_text())['phase']=='failed_cook_verification'
dirty = [p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
from geocity_editor_action import acknowledged_cook_leftovers
foreign=[p for p in dirty if not p.startswith(profile['cook_folder']+'/')]
assert set(foreign).issubset(acknowledged_cook_leftovers(PROJECT, foreign))
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert world == profile['map']
task = unreal.AssetImportTask()
task.filename = str(SOURCE / 'GeoCity_city_v015_PermanentBank.hdalc')
task.destination_path = '/Game/Project/Shared/ModelBank/HDA'
task.destination_name = 'GeoCity_city_v015_PermanentBank'
task.automated = True
task.replace_existing = True
task.save = False
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
asset = unreal.load_asset(profile['hda'])
assert isinstance(asset, unreal.HoudiniAsset)
assert unreal.EditorAssetLibrary.save_asset(profile['hda'], only_if_is_dirty=True)
receipt = {'hda': profile['hda'], 'external_sha256': hashlib.sha256(Path(task.filename).read_bytes()).hexdigest(), 'named_save': True, 'engine_paused': True, 'city_cook': 'next_official_regenerate'}
(HERE / 'NATIVE_HDA_IMPORT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt))
