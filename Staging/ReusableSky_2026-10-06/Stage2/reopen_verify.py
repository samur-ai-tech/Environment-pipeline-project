import os,json,collections,math
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert hasattr(unreal,'SunPositionFunctionLibrary')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();assert len(actors)==122
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky');cdo=unreal.get_default_object(bp.generated_class())
a=next(x for x in actors if x.get_name()=='BP_EnvironmentSky_C_0')
assert a.get_editor_property('RigEnabled') and not cdo.get_editor_property('RigEnabled')
assert a.get_editor_property('ClockDisplay')=='12:00' and a.get_editor_property('Status')=='Active - Time and Location'
assert a.get_editor_property('ConflictActors')=='' and not a.get_editor_property('OverrideExposure')
assert a.get_editor_property('WeatherPreset')=='Partly Cloudy'
assert abs(a.get_editor_property('CloudAmount')-.55)<1e-5
assert abs(a.get_editor_property('Haze')-.15)<1e-5
assert a.get_editor_property('CloudSpeed')==1.0 and a.get_editor_property('CloudDirection')==45.0
assert not a.get_editor_property('HighQuality')
mid=a.get_editor_property('CloudMID');assert mid,'MID failed to reconstruct on fresh load'
cloud=a.get_component_by_class(unreal.VolumetricCloudComponent)
assert cloud.is_visible() and cloud.get_editor_property('material')==mid
assert abs(mid.get_scalar_parameter_value('Cloud_GlobalCoverage')-(-1+2.5*.55*.55))<1e-5
assert abs(mid.get_scalar_parameter_value('Cloud_GlobalDensity')-(.006+.012*.55))<1e-5
sky=a.get_component_by_class(unreal.SkyAtmosphereComponent)
assert abs(sky.get_editor_property('mie_scattering_scale')-(.002+.022*.15))<1e-6
sun=a.get_component_by_class(unreal.DirectionalLightComponent)
assert abs(sun.intensity-10*(1-.88*.55**3))<1e-5
assert cloud.get_editor_property('view_sample_count_scale')==1.0
assert cloud.get_editor_property('reflection_view_sample_count_scale_value')==.5
classes=dict(collections.Counter(c.get_class().get_name() for c in a.get_components_by_class(unreal.ActorComponent)))
assert classes==json.loads((root/'CONTROL_VERIFICATION.json').read_text())['component_classes']
for row in json.loads((root.parent/'LIGHTING_RESTORATION.json').read_text()):
 c=unreal.find_object(None,row['component']);assert c and not c.is_visible()
orig=unreal.find_object(None,json.loads((root/'CLOUD_RESTORATION.json').read_text())['component']);assert orig and not orig.is_visible()
assert not a.get_component_by_class(unreal.PostProcessComponent).get_editor_property('enabled')
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert dc==[] and dm==[],(dc,dm)
RESULT={'pid':os.getpid(),'fresh_process_reopen_passed':True,'map':world.get_outermost().get_path_name(),'actor_count':len(actors),'clock':'12:00','weather_preset':'Partly Cloudy','cloud_amount':a.get_editor_property('CloudAmount'),'haze':a.get_editor_property('Haze'),'dynamic_material_reconstructed':mid.get_path_name(),'coverage':mid.get_scalar_parameter_value('Cloud_GlobalCoverage'),'density':mid.get_scalar_parameter_value('Cloud_GlobalDensity'),'wind':str(mid.get_vector_parameter_value('Layout_WindControls')),'cloud_visible':cloud.is_visible(),'sun_intensity':sun.intensity,'mie_scale':sky.get_editor_property('mie_scattering_scale'),'owned_component_classes':classes,'exposure_override_off':True,'original_lighting_and_clouds_retained_disabled':True,'dirty_content':dc,'dirty_maps':dm,'cooking_paused':True}
(root/'REOPEN_VERIFIED.json').write_text(json.dumps(RESULT,indent=2))
