import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cls=unreal.EditorAssetLibrary.load_blueprint_class('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
assert not [a for a in sub.get_all_level_actors() if a.get_class()==cls]
a=sub.spawn_actor_from_class(cls,unreal.Vector(0,0,1000))
a.set_actor_label('EnvironmentSky');a.set_folder_path('ReusableSky')
RESULT={'actor':a.get_path_name(),'status':a.get_editor_property('Status'),'conflicts':a.get_editor_property('ConflictActors'),'clock':a.get_editor_property('ClockDisplay'),'visible':{c.get_name():c.is_visible() for c in a.get_components_by_class(unreal.SceneComponent)},'camera_api':str(unreal.UnrealEditorSubsystem.set_level_viewport_camera_info.__doc__)}
(root/'PLACED_INACTIVE.json').write_text(json.dumps(RESULT,indent=2))
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(-8268,-6591,11552),unreal.Rotator(-15,52,0))
