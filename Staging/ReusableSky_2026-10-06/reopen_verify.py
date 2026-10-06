import os,json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert hasattr(unreal,'SunPositionFunctionLibrary')
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
rigs=[a for a in actors if a.get_class()==bp.generated_class()]
assert len(rigs)==1 and len(actors)==122
a=rigs[0];cdo=unreal.get_default_object(bp.generated_class())
assert a.get_editor_property('RigEnabled') and not cdo.get_editor_property('RigEnabled')
assert a.get_editor_property('TimeOfDay')==12.0 and a.get_editor_property('ClockDisplay')=='12:00'
assert a.get_editor_property('Status')=='Active - Time and Location'
assert a.get_editor_property('ConflictActors')==''
sun=a.get_component_by_class(unreal.DirectionalLightComponent)
expected=json.loads((root/'CONTROL_VERIFICATION.json').read_text())['final']['sun_forward'];f=sun.get_forward_vector()
assert max(abs(v-e) for v,e in zip([f.x,f.y,f.z],expected))<1e-6
owned={c.get_name():c.is_visible() for c in a.get_components_by_class(unreal.SceneComponent)}
assert all(owned[k] for k in ['DirectionalLight','SkyLight','SkyAtmosphere','NorthArrow'])
for row in json.loads((root/'LIGHTING_RESTORATION.json').read_text()):
 c=unreal.find_object(None,row['component']);assert c and not c.is_visible()
pp=a.get_component_by_class(unreal.PostProcessComponent);assert not pp.get_editor_property('enabled')
dirty_content=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
dirty_maps=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert dirty_content==[] and dirty_maps==[],(dirty_content,dirty_maps)
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
RESULT={'pid':os.getpid(),'map':world.get_outermost().get_path_name(),'asset':bp.get_path_name(),'actor':a.get_path_name(),'actor_count':len(actors),'clock':a.get_editor_property('ClockDisplay'),'status':a.get_editor_property('Status'),'sun_forward':[f.x,f.y,f.z],'owned_component_visibility':owned,'disabled_original_components_retained':True,'default_rig_inactive':True,'exposure_override_off':True,'dirty_content':dirty_content,'dirty_maps':dirty_maps,'plugin_loaded_without_launch_enable_flag':True,'fresh_process_reopen_passed':True}
(root/'REOPEN_VERIFIED.json').write_text(json.dumps(RESULT,indent=2))
