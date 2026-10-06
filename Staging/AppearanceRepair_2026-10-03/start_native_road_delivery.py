"""Root-only ordinary native RoadBLD transaction in the current retained area."""
import datetime
import importlib
import json
import os
import shutil
from pathlib import Path

import unreal
import geocity_bank_workflow
import geocity_roadbld_workflow
import geocity_editor_action
importlib.reload(geocity_editor_action)
acknowledged_cook_leftovers = geocity_editor_action.acknowledged_cook_leftovers

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/AppearanceRepair_2026-10-03'
lease = (PROJECT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
assert all(not r.watch_tick and not r.save_tick for r in geocity_bank_workflow.ACTIVE)
assert all(not r.tick_handle for r in geocity_roadbld_workflow.ACTIVE)
api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
assert api.is_session_valid() and api.is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
dirty = [p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
assert set(dirty).issubset(acknowledged_cook_leftovers(PROJECT, dirty))
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
paths = [PROJECT / 'Staging/ModelBank' / d / 'AREA_PROFILE.json' for d in
         ('PermanentIntegration_2026-10-02', 'GazaShujaiyaIntegration_2026-10-02')]
profiles = [(p, json.loads(p.read_text(encoding='utf-8'))) for p in paths]
matches = [(p, data) for p, data in profiles if data['map'] == world]
assert len(matches) == 1
profile_path, profile = matches[0]
assert unreal.get_editor_subsystem(unreal.WorldBLDAuthSubsystem).has_license_for_tool('RoadBLD')
importlib.reload(geocity_bank_workflow)
importlib.reload(geocity_roadbld_workflow)
for helper in ('geocity_roadbld_clip', 'geocity_roadbld_grounding',
               'geocity_roadbld_seams', 'geocity_roadbld_topology',
               'geocity_roadbld_junctions', 'geocity_roadbld_landscape'):
    importlib.reload(importlib.import_module(helper))
preflight = geocity_roadbld_workflow.preflight(str(profile_path), reviewed_dirty_packages=dirty)
area = preflight['area_id']
backup = HERE / 'BeforeNative' / area
backup.mkdir(parents=True, exist_ok=True)
for source in [profile_path, Path(profile['workflow_receipt']), Path(profile['catalog_receipt']),
               PROJECT / ('Content/' + profile['map'].removeprefix('/Game/') + '.umap')]:
    target = backup / source.name
    if not target.exists():
        shutil.copy2(source, target)
profile['roadbld_workflow']['enabled'] = True
profile['roadbld_workflow']['status'] = 'native_authorized_generation_in_progress'
profile['roadbld_workflow']['sign_in_verified_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
profile_path.write_text(json.dumps(profile, indent=2) + '\n', encoding='utf-8')
operation = geocity_bank_workflow.run(str(profile_path), action='regenerate', reviewed_dirty_packages=dirty)
print(json.dumps({'area': area, 'phase': operation.state['phase'], 'roadbld_license': True,
                  'source_roads': preflight['source_road_count'], 'source_pieces': preflight['source_piece_count'],
                  'native_road_delivery': 'pending_native_generation_validation_HDA_suppression_and_named_save'}))
