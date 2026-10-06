import json,os,collections
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3/Resume'
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
actors=unreal.GameplayStatics.get_all_actors_of_class(w,bp.generated_class());assert len(actors)==1
a=actors[0];tag=json.loads((r/'RUNTIME_REQUEST.json').read_text())['tag']
RESULT={'pid':os.getpid(),'world':w.get_path_name(),'hour':a.get_editor_property('TimeOfDay'),'clock':a.get_editor_property('ClockDisplay'),'tick_enabled':a.is_actor_tick_enabled(),'moon_intensity':a.get_editor_property('MoonLight').intensity,'component_count':len(a.get_components_by_class(unreal.ActorComponent)),'cooking_paused':unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()}
if tag=='running':
 assert abs(RESULT['hour']-23.99)>0.01
 a.call_method('SetTimeProgression',(True,True,1.));RESULT['paused_hour']=a.get_editor_property('TimeOfDay');assert not a.is_actor_tick_enabled()
else:
 prev=json.loads((r/'RUNTIME_running.json').read_text());assert RESULT['hour']==prev['paused_hour'] and not RESULT['tick_enabled'];RESULT['pause_verified']=True
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
(r/('RUNTIME_'+tag+'.json')).write_text(json.dumps(RESULT,indent=2))
