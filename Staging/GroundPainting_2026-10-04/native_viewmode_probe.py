"""Read actual active editor view mode and camera; no scene or UI mutation."""
import datetime,json,os
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text());named_map=world.get_outermost().get_path_name()
assert named_map in assignment['original_maps'].values()
lease=[s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
assert f'assigned_editor_PID={os.getpid()}' in lease and 'OWNER=CODEX_GROUND_PAINTING' in lease and f'map={named_map}' in lease
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);key=level.get_active_viewport_config_key()
mode=unreal.AutomationLibrary.get_editor_active_viewport_view_mode()
result={'pid':os.getpid(),'world':named_map,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':str(mode),'active_key':str(key),'camera':str(level.get_level_viewport_camera_info(key)),'available_modes':[x for x in dir(unreal.ViewModeIndex) if 'LIT' in x or 'UNKNOWN' in x]}
(HERE/'Revision_2026-10-05'/f'VIEWMODE_BEFORE_PID{os.getpid()}.json').write_text(json.dumps(result,indent=2),encoding='utf-8');RESULT=result
