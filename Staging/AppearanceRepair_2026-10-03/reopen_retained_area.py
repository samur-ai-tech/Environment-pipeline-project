"""Owner-run saved-map reopen and readback; official Engine stays paused."""
import datetime
import json
import os
import runpy
import subprocess
from pathlib import Path

import unreal
import geocity_bank_workflow
from geocity_editor_action import acknowledged_cook_leftovers

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/AppearanceRepair_2026-10-03'
REVISION = 'r018_retained_appearance'
PROFILE_PATHS = {str((PROJECT / 'Staging/ModelBank' / directory / 'AREA_PROFILE.json').resolve()).lower()
    for directory in ('PermanentIntegration_2026-10-02', 'GazaShujaiyaIntegration_2026-10-02')}


def reopen_area(profile_path):
    lease = (PROJECT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
    assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
    processes = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
        'Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],
        capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
    assert processes.returncode == 0
    assert [int(pid) for pid in processes.stdout.split()] == [os.getpid()]
    assert all(not workflow.watch_tick and not workflow.save_tick for workflow in geocity_bank_workflow.ACTIVE)
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    assert api.is_asset_cooking_paused()
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    dirty = [package.get_path_name() for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    assert set(dirty).issubset(acknowledged_cook_leftovers(PROJECT, dirty))
    profile_path = Path(profile_path).resolve()
    assert str(profile_path).lower() in PROFILE_PATHS, 'Reopen is scoped to the two assigned retained profiles'
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    saved = json.loads(Path(profile['workflow_receipt']).read_text(encoding='utf-8'))
    assert saved['phase'] == 'baked_saved_verified' and saved['generator_revision'] == REVISION
    previous_world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
    assert unreal.EditorLoadingAndSavingUtils.load_map(profile['map'])
    assert api.is_asset_cooking_paused()
    namespace = runpy.run_path(str(HERE / 'inspect_retained_area.py'), init_globals={'READBACK_PREFIX': 'REOPEN_INSPECT_'})
    actual = namespace['READBACK_RESULT']
    area = json.loads(Path(profile['source']).read_text(encoding='utf-8'))['area_id']
    assert actual['world'] == profile['map'] and actual['native_count'] == saved['instance_count']
    assert actual['landscape_count'] == 1 and not actual['dirty_maps']
    assert actual['native_material_slots_verified'] and actual['anchor_material_partition_verified']
    assert actual['all_native_anchor_locations_match_recipe_within_1mm']
    assert actual['all_saved_baked_actors_present'] and actual['cooked_mesh_components'] == 0
    assert actual['hda_actor_count'] == 1 and actual['auto_cooking_enabled'] is False
    assert all(not workflow.watch_tick and not workflow.save_tick for workflow in geocity_bank_workflow.ACTIVE)
    assert api.is_asset_cooking_paused()
    actual['persistence'] = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'method': 'Saved map opened through load_map in the same owned editor; Engine paused, no recook or new bake',
        'previous_world': previous_world, 'reopened_world': actual['world'],
        'all_saved_baked_actors_present': True, 'cooked_mesh_components': 0, 'hda_actor_count': 1,
        'auto_cooking_enabled': False, 'exact_native_material_partitions_verified': True,
        'all_native_anchors_and_material_partitions_within_1mm': True,
        'fresh_editor_process_restart_performed': False,
        'inspection_receipt': namespace['READBACK_TARGET_PATH']}
    target = namespace['_new_receipt_path']('REOPEN_' + area + '.json')
    target.write_text(json.dumps(actual, indent=2), encoding='utf-8')
    print(json.dumps({'reopened': area, 'native_count': actual['native_count'],
        'material_group_count': len(actual['native_mesh_material_counts']),
        'baked_actors': len(saved['baked_actor_paths']), 'dirty_maps': actual['dirty_maps'],
        'no_recook': True, 'receipt': str(target)}))
    return str(target)
