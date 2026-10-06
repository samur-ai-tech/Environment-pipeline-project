import json
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3/Resume'
assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
assert abs(a.get_editor_property('TimeOfDay')-23.99)<1e-8
a.call_method('SetTimeProgression',(False,False,20.));a.call_method('SetSkyTime',(12.,));a.call_method('PresetPartlyCloudy');a.set_editor_property('CloudSpeed',1.)
RESULT={'runtime_did_not_change_editor_time':True,'editor_tick_disabled':not a.is_actor_tick_enabled(),'hour':a.get_editor_property('TimeOfDay')}
(r/'RUNTIME_ENDED.json').write_text(json.dumps(RESULT,indent=2))
