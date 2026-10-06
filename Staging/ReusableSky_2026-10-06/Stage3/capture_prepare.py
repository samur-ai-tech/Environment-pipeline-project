import json
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
o=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
(r/'EDITOR_CAPTURE_PREFERENCES_BEFORE.json').write_text(json.dumps({n:o.get_editor_property(n) for n in ['bThrottleCPUWhenNotForeground']},indent=2))
o.set_editor_property('bThrottleCPUWhenNotForeground',False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_viewport_realtime(True)
RESULT={'temporary_background_throttle_disabled':True,'viewport_realtime':True,'configuration_files_saved':False}
