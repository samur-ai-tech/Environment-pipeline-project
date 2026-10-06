import json,os
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3/Resume'
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
a.call_method('SetSkyTime',(23.99,));a.call_method('SetTimeProgression',(True,False,1.))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
RESULT={'pid':os.getpid(),'requested_simulate':True,'start_hour':23.99,'day_minutes':1.}
(r/'RUNTIME_STARTED.json').write_text(json.dumps(RESULT))
