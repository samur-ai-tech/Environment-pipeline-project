import json
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
s=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
p=r/'Resume/EDITOR_PREFERENCES_BEFORE.json'
if not p.exists():p.write_text(json.dumps({'bThrottleCPUWhenNotForeground':s.get_editor_property('bThrottleCPUWhenNotForeground')}))
s.set_editor_property('bThrottleCPUWhenNotForeground',False)
cam=json.loads((r/'CAMERA.json').read_text(encoding='utf-8-sig'));l=cam['location'];rot=cam['rotation']
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(l['x'],l['y'],l['z']),unreal.Rotator(pitch=rot['pitch'],yaw=rot['yaw'],roll=rot['roll']))
RESULT={'camera_set':True,'background_throttle':False}
