import os,json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert not dc and not dm
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();assert len(actors)==122
a=next(a for a in actors if a.get_name()=='BP_EnvironmentSky_C_0')
controls={str(n):str(a.get_editor_property(n)) for n in BP.list_variables(bp)}
assert a.get_editor_property('ClockDisplay')=='12:00' and a.get_editor_property('ConflictActors')==''
assert a.get_editor_property('WeatherPreset')=='Partly Cloudy' and abs(a.get_editor_property('CloudAmount')-.55)<1e-5
assert a.get_editor_property('CloudMID') and not a.get_editor_property('OverrideExposure')
RESULT={'pid':os.getpid(),'world':world.get_outermost().get_path_name(),'dirty_content':dc,'dirty_maps':dm,'cooking_paused':True,'actor_count':len(actors),'stage1_stage2_public_controls':controls,'bp_api_file':BP.add_variable.__module__,'bp_function_api':[n for n in dir(BP) if any(k in n for k in ['function','parameter','event','variable'])]}
(root/'PREFLIGHT_NATIVE.json').write_text(json.dumps(RESULT,indent=2))
