import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
obj=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
obj.set_editor_property('bThrottleCPUWhenNotForeground',False)
sub=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
sub.editor_set_viewport_realtime(True)
RESULT={'viewport_realtime':True,'temporary_background_throttle_disabled':True}
