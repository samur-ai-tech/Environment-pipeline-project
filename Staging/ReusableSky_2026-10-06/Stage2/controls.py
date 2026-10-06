import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
req=json.loads((root/'REQUEST.json').read_text(encoding='utf-8-sig'))
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
if req.get('preset'):a.call_method(req['preset'])
for k,v in req.get('values',{}).items():a.set_editor_property(k,v)
cloud=a.get_component_by_class(unreal.VolumetricCloudComponent);sun=a.get_component_by_class(unreal.DirectionalLightComponent);sky=a.get_component_by_class(unreal.SkyAtmosphereComponent);mid=a.get_editor_property('CloudMID')
RESULT={'name':req['name'],'clock':a.get_editor_property('ClockDisplay'),'status':a.get_editor_property('Status'),'inputs':{k:a.get_editor_property(k) for k in ['TimeOfDay','ManualSun','ManualDirection','ManualElevation','NorthOffset','Year','Month','Day','Latitude','Longitude','TimeZone','UseDaylightSavingTime','OverrideExposure','SunIntensity','SkyIntensity','CloudAmount','CloudSpeed','CloudDirection','Haze','HighQuality','WeatherPreset']},'cloud_visible':cloud.is_visible(),'coverage':mid.get_scalar_parameter_value('Cloud_GlobalCoverage'),'density':mid.get_scalar_parameter_value('Cloud_GlobalDensity'),'wind':str(mid.get_vector_parameter_value('Layout_WindControls')),'sun_intensity':sun.intensity,'sun_source_angle':sun.get_editor_property('light_source_angle'),'mie_scale':sky.get_editor_property('mie_scattering_scale'),'samples':{p:cloud.get_editor_property(p) for p in ['view_sample_count_scale','reflection_view_sample_count_scale_value','shadow_view_sample_count_scale','shadow_reflection_view_sample_count_scale_value']},'components':sorted(c.get_class().get_name()+':'+c.get_name() for c in a.get_components_by_class(unreal.ActorComponent)),'mid':mid.get_path_name()}
(root/('CHECK_'+req['name']+'.json')).write_text(json.dumps(RESULT,indent=2))
