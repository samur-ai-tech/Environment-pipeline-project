import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
seen=set()
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);o=unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
 if not o or o.get_path_name() in seen:continue
 seen.add(o.get_path_name())
 if isinstance(o,unreal.ArrowComponent):
  o.set_editor_property('visible',True);o.set_editor_property('hidden_in_game',False);o.set_editor_property('arrow_size',5.0)
BP.compile_blueprint(bp,True)
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
arrow=a.get_component_by_class(unreal.ArrowComponent);arrow.set_editor_property('visible',True);arrow.set_editor_property('hidden_in_game',False)
a.set_editor_property('NorthOffset',90.0)
arrow=a.get_component_by_class(unreal.ArrowComponent);p90=arrow.get_world_rotation().yaw
a.set_editor_property('NorthOffset',0.0)
arrow=a.get_component_by_class(unreal.ArrowComponent)
assert arrow.is_visible() and abs(p90-90)<.01 and abs(arrow.get_world_rotation().yaw)<.01
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();assert unreal.EditorLoadingAndSavingUtils.save_map(w,w.get_outermost().get_path_name())
RESULT={'arrow_visible':arrow.is_visible(),'yaw0':arrow.get_world_rotation().yaw,'yaw90':p90,'saved_asset_and_Rimal':True}
(root/'NORTH_ARROW_VERIFIED.json').write_text(json.dumps(RESULT,indent=2))
