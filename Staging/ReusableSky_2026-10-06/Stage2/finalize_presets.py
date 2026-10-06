import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
g=BP.get_graph(bp,'PresetPartlyCloudy')
BP.write_graph_dsl(g,'(fn PresetPartlyCloudy () (Variables|06Weather|SetCloudAmount 0.55) (Variables|06Weather|SetHaze 0.15) (Variables|06Weather|SetWeatherPreset "Partly Cloudy") (CallFunction|UpdateSky))')
unreal.BlueprintGraphEditor.get_graph_editor(g).set_is_call_in_editor_function(True)
cdo=unreal.get_default_object(bp.generated_class());cdo.set_editor_property('CloudAmount',.55)
BP.compile_blueprint(bp,True)
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
a.call_method('PresetPartlyCloudy');a.set_editor_property('CloudSpeed',0.0)
RESULT={'preset_partly_amount':a.get_editor_property('CloudAmount'),'editor_cvars':{x:unreal.SystemLibrary.get_console_variable_float_value(x) for x in ['r.ScreenPercentage','sg.ShadowQuality','sg.EffectsQuality','sg.PostProcessQuality','sg.GlobalIlluminationQuality','sg.ReflectionQuality','r.VolumetricRenderTarget.Mode','r.VSyncEditor','t.MaxFPS','r.GPUCsvStatsEnabled']},'editor_realtime_api':[x for x in dir(unreal.LevelEditorSubsystem) if 'realtime' in x]}
(root/'PERFORMANCE_CONTEXT.json').write_text(json.dumps(RESULT,indent=2))
