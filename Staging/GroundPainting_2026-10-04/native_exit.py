"""Orderly clean original-map exit; no shutdown save/discard of dirty content."""
import datetime,json,os,sys
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04'
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
assert f'assigned_editor_PID={os.getpid()}' in lease and 'OWNER=CODEX_GROUND_PAINTING' in lease
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
result={'pid':os.getpid(),'world':world.get_outermost().get_path_name(),'clean':True,'paused':True,'shutdown_saves':0,'forced_termination':False,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(HERE/f'EXIT_PID{os.getpid()}.json').write_text(json.dumps(result,indent=2),encoding='utf-8');RESULT=result
unreal.SystemLibrary.quit_editor()
