import base64,json,os
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04'
assert 'assigned_editor_PID='+str(os.getpid()) in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines()[-1]
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
RESULT={'viewport_keys':[str(k) for k in level.get_viewport_config_keys()],'active_key':str(level.get_active_viewport_config_key()),'cameras':{str(k):str(level.get_level_viewport_camera_info(k)) for k in level.get_viewport_config_keys()}}
