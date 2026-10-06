import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools as AT
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
seen=set();removed=[]
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);o=unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
 if not o or o.get_path_name() in seen:continue
 seen.add(o.get_path_name())
 if isinstance(o,unreal.VolumetricCloudComponent):
  removed.append(o.get_path_name());assert AT.remove_component(o)
 elif isinstance(o,(unreal.DirectionalLightComponent,unreal.SkyLightComponent,unreal.SkyAtmosphereComponent)):
  o.set_editor_property('visible',False)
  if isinstance(o,unreal.DirectionalLightComponent):o.set_editor_property('intensity',10.0)
 elif isinstance(o,unreal.ArrowComponent):o.set_editor_property('is_editor_only',True)
 elif isinstance(o,unreal.PostProcessComponent):
  settings=o.get_editor_property('settings');settings.set_editor_property('override_auto_exposure_min_brightness',True);settings.set_editor_property('override_auto_exposure_max_brightness',True);settings.set_editor_property('auto_exposure_min_brightness',3.0);settings.set_editor_property('auto_exposure_max_brightness',3.0);o.set_editor_property('settings',settings)
g=BP.get_graph(bp,'UpdateSky')
for n in BP.find_nodes(g,node_class=unreal.K2Node_MakeStruct.static_class()):
 if 'PostProcess' in n.get_node_title():BP.delete_node(n)
unreal.BlueprintGraphEditor.get_graph_editor(g).set_is_call_in_editor_function(True)
BP.compile_blueprint(bp,True)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
RESULT={'cloud_component_removed':removed,'opened_asset_editor':True}
