import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
def write(g,code):
 def create(g,t,pos):
  cls=unreal.MaterialLibrary.static_class() if t=='Rendering|Material|CreateDynamicMaterialInstance' else unreal.MaterialInstanceDynamic.static_class() if t in ['Rendering|Material|SetScalarParameterValue','Rendering|Material|SetVectorParameterValue'] else None
  return BP.create_node(g,t,pos,cls)
 blueprint_dsl.Transpiler(g,create,BP.connect_pins,BP._get_node_info,BP.set_pin_value,lambda g:BP.find_nodes(g),delete_node_fn=BP.delete_node,find_node_types_fn=lambda f:BP.find_node_types(g,f)).transpile(code)
 BP.compile_blueprint(bp,True)
code=(root/'ApplyWeather.dsl').read_text().replace('(+ 0.5 (* 7.0','(+ 0.002 (* 0.022').replace(') 1 0.5)',') 1.0 0.5)').replace(') 2 1)',') 2.0 1.0)')
# Keep the engine's original partly-cloudy coverage near -0.2; use a nonlinear amount response.
code=code.replace('(+ -1.0 (* 2.5 (Variables|06Weather|GetCloudAmount)))','(+ -1.0 (* 2.5 (* (Variables|06Weather|GetCloudAmount) (Variables|06Weather|GetCloudAmount))))')
(root/'ApplyWeather.dsl').write_text(code)
write(BP.get_graph(bp,'ApplyWeather'),code)
ucs=BP.get_graph(bp,'UserConstructionScript')
write(ucs,'(fn ConstructionScript () (Variables|Default|SetCloudMID (Rendering|Material|CreateDynamicMaterialInstance :Parent "/Game/Project/Shared/Atmosphere/ReusableSky/MI_EnvironmentCloudDefaults.MI_EnvironmentCloudDefaults" :OptionalName "EnvironmentCloudMID" :CreationFlags "Transient")) (CallFunction|UpdateSky))')
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0');a.call_method('PresetPartlyCloudy')
RESULT={'compiled':True,'mie_scale':a.get_component_by_class(unreal.SkyAtmosphereComponent).get_editor_property('mie_scattering_scale'),'per_construction_unique_material':True}
