import os,json,unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
dc=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
dm=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
RESULT={'ok':True,'pid':os.getpid(),'world':world.get_outermost().get_path_name(),'dirty_content':dc,'dirty_maps':dm}
print(json.dumps(RESULT))
