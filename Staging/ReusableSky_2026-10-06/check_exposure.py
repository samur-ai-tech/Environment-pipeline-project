from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
g=BP.get_graph(bp,'UpdateSky')
RESULT={'nodes':[{'path':n.get_path_name(),'pins':[(p.name,p.pin_id,p.type_id) for p in BP._get_node_info(n).input_pins]} for n in BP.find_nodes(g,node_class=unreal.K2Node_MakeStruct.static_class())],'set_settings':list(BP.find_node_types(g,'SetSettings'))}
