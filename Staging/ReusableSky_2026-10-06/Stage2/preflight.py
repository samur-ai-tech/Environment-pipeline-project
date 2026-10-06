import os,json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert dc==[] and dm==[]
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
props={n:a.get_editor_property(n) for n in ['TimeOfDay','ClockDisplay','ManualSun','ManualDirection','ManualElevation','NorthOffset','Latitude','Longitude','Year','Month','Day','TimeZone','UseDaylightSavingTime','RigEnabled','SunIntensity','SkyIntensity','OverrideExposure']}
assert props['ClockDisplay']=='12:00'
mat=unreal.load_asset('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud')
inst=unreal.load_asset('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst')
mel=unreal.MaterialEditingLibrary
RESULT={'pid':os.getpid(),'dirty_content':dc,'dirty_maps':dm,'public_controls':props,'variables':list(BP.list_variables(bp)),'material_scalars':[str(n) for n in mel.get_scalar_parameter_names(mat)],'material_vectors':[str(n) for n in mel.get_vector_parameter_names(mat)],'instance_scalars':{str(n):mel.get_material_instance_scalar_parameter_value(inst,n) for n in mel.get_scalar_parameter_names(mat)},'instance_vectors':{str(n):str(mel.get_material_instance_vector_parameter_value(inst,n)) for n in mel.get_vector_parameter_names(mat)},'material_methods':[x for x in dir(unreal.MaterialEditingLibrary) if any(y in x for y in ['expression','connection','input'])]}
(root/'PREFLIGHT.json').write_text(json.dumps(RESULT,indent=2))
