from editor_toolset.toolsets.blueprint import BlueprintTools as BP
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
arrow=a.get_editor_property('NorthArrow')
RESULT={'pointer':arrow.get_path_name(),'actual':[(c.get_path_name(),c.is_visible(),str(c.get_editor_property('hidden_in_game')),str(c.get_editor_property('is_editor_only'))) for c in a.get_components_by_class(unreal.ArrowComponent)],'graph_tail':BP.read_graph_dsl(BP.get_graph(unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky'),'UpdateSky'))[-2000:]}
