import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
import unreal

ROOT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
OUT = ROOT / 'Staging/AssetBankOperator_2026-10-06/Exit_20261006/EXIT_PID29900.json'
assert os.getpid() == 29900, 'Wrong editor PID; no exit performed'
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world_path = world.get_outermost().get_path_name()
assert world_path == '/Game/Project/Areas/Iran_38196167_46086167_4km/BankIntegration_v015/L_Iran_38196167_46086167_4km', world_path
owner_file = ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt'
owner_before = [line for line in owner_file.read_text(encoding='utf-8-sig').splitlines() if line.strip()][-1]
assert 'OWNER=NONE' in owner_before, owner_before
paused = bool(unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused())
active = [k for n in ('geocity_bank_workflow', 'geocity_roadbld_workflow') for r in getattr(sys.modules.get(n), 'ACTIVE', []) for k in ('watch_tick', 'save_tick', 'tick_handle') if getattr(r, k, None) is not None]
dirty_content = sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
dirty_maps = sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
cook_prefix = '/Game/Project/Areas/Iran_38196167_46086167_4km/BankIntegration_v015/Cook/GeoCity_city_v015_4km/78F86F39/GeoCity_city_v015_4km_3_'
expected_dirty = sorted(cook_prefix + str(n) + '_0_main_geo' for n in (374, 375, 376))
assert not dirty_maps, 'Dirty maps: ' + str(dirty_maps)
assert dirty_content == expected_dirty, 'Unexpected dirty content: ' + str(dirty_content)
assert not active, 'Active lifecycle callbacks: ' + str(active)
assert paused, 'Houdini cooking is not paused'
assert not OUT.exists(), 'Exit receipt already exists; inspect before retrying'
now = datetime.now(timezone.utc).isoformat()
release = now + ' OWNER=NONE released_by=ASSET_BANK_OPERATOR editor_PID=29900 released_phase=closed_no_generation authority=AVIV_MANAGER_CC37D4D2 shutdown_saves=0 dirty_maps=0 transient_cook_packages_discarded=3 receipt=Staging/AssetBankOperator_2026-10-06/Exit_20261006/EXIT_PID29900.json'
record = {
    'status': 'ORDERLY_EXIT_REQUESTED_AWAITING_OS_CONFIRMATION',
    'utc': now, 'editor_pid': os.getpid(), 'world': world_path,
    'authority': 'Aviv decision relayed by manager Claude cc37d4d2: close PID 29900 without saving; generation and placement verification deferred to next manager-scheduled ordinary run.',
    'dirty_maps_before_quit': dirty_maps,
    'dirty_content_discarded_unsaved': dirty_content,
    'cooking_paused': paused, 'active_lifecycle_callbacks': active,
    'shutdown_saves': 0, 'saved_packages': [], 'generation_performed': False,
    'placement_verification': 'DEFERRED_TO_NEXT_MANAGER_SCHEDULED_ORDINARY_RUN',
    'forced_termination': False, 'quit_method': 'unreal.SystemLibrary.quit_editor()',
    'owner_line_before': owner_before, 'release_line': release,
    'native_asset_map_profile_changes': False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(record, indent=2), encoding='utf-8')
with owner_file.open('a', encoding='utf-8') as f:
    f.write('\n' + release + '\n')
print(json.dumps({'exit_receipt': str(OUT), 'dirty_maps': 0, 'transient_cook_packages_discarded': len(dirty_content), 'shutdown_saves': 0}))
unreal.SystemLibrary.quit_editor()
