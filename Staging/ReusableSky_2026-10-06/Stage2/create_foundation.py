import json,shutil
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools as AT
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
base='/Game/Project/Shared/Atmosphere/ReusableSky/'
shutil.copy2(Path(unreal.Paths.project_content_dir())/'Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky.uasset',root/'Before/BP_EnvironmentSky_Stage1.uasset')
bp=unreal.load_asset(base+'BP_EnvironmentSky')
mi=unreal.EditorAssetLibrary.duplicate_asset('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst',base+'MI_EnvironmentCloudDefaults')
assert mi
assert AT.add_component(bp,unreal.VolumetricCloudComponent.static_class(),'WeatherClouds')
for name,typ,category in [('CloudAmount','float','06 Weather'),('Haze','float','06 Weather'),('CloudSpeed','float','07 Cloud Motion'),('CloudDirection','float','07 Cloud Motion'),('HighQuality','bool','08 Quality'),('WeatherPreset','string','06 Weather')]:
 BP.add_variable(bp,name,typ);BP.set_variable_category(bp,name,category);BP.set_variable_instance_editable(bp,name,True)
BP.add_object_variable(bp,'CloudMID',unreal.MaterialInstanceDynamic.static_class())
BP.compile_blueprint(bp)
cdo=unreal.get_default_object(bp.generated_class())
for k,v in {'CloudAmount':.45,'Haze':.15,'CloudSpeed':1.0,'CloudDirection':45.0,'HighQuality':False,'WeatherPreset':'Partly Cloudy'}.items():cdo.set_editor_property(k,v)
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);c=unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
 if isinstance(c,unreal.VolumetricCloudComponent):
  c.set_editor_property('material',mi);c.set_editor_property('layer_bottom_altitude',2.0);c.set_editor_property('layer_height',4.0);c.set_editor_property('visible',False)
g=BP.get_graph(bp,'UpdateSky')
queries=['CreateDynamicMaterialInstance','SetScalarParameterValue','SetVectorParameterValue','SetMieScatteringScale','SetAerialPerspective','SetLightSourceAngle','SetViewSampleCountScale','SetReflectionViewSampleCountScale','SetShadowViewSampleCountScale','SetShadowReflectionViewSampleCountScale','SetMaterial','Cos','Sin']
RESULT={'node_types':{q:list(BP.find_node_types(g,q)) for q in queries},'object_var_methods':[x for x in dir(BP) if 'object' in x]}
(root/'WEATHER_NODE_TYPES.json').write_text(json.dumps(RESULT,indent=2))
