import json,os
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
a=next(x for x in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if x.get_name()=='BP_EnvironmentSky_C_0')
cloud=a.get_component_by_class(unreal.VolumetricCloudComponent)
RESULT={'pid':os.getpid(),'dirty_content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'dirty_maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'cloud_mid':str(a.get_editor_property('CloudMID')),'cloud_component_material':str(cloud.get_editor_property('material')),'exposure_override':a.get_editor_property('OverrideExposure'),'clock':a.get_editor_property('ClockDisplay'),'preset':a.get_editor_property('WeatherPreset'),'status':a.get_editor_property('Status'),'cooking_paused':unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()}
(r/'RECOVERY_PREFLIGHT_FINDING.json').write_text(json.dumps(RESULT,indent=2))
