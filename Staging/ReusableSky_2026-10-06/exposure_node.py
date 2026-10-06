from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
g=BP.get_graph(bp,'UpdateSky')
n=BP.create_node(g,'Utilities|Struct|MakePostProcessSettings',unreal.IntPoint(0,0))
opts=n.get_editor_property('ShowPinForProperties')
for o in opts:
 if str(o.get_editor_property('PropertyName')) in ['AutoExposureMinBrightness','AutoExposureMaxBrightness']:
  for k in ['bShowPin','bIsOverrideEnabled','bIsSetValuePinVisible']:
   o.set_editor_property(k,True)
n.set_editor_property('ShowPinForProperties',opts)
RESULT={'node':n.get_path_name(),'node_methods':dir(n),'library_methods':dir(unreal.BlueprintEditorLibrary),'pins':[(p.name,p.type_id) for p in BP._get_node_info(n).input_pins]}
