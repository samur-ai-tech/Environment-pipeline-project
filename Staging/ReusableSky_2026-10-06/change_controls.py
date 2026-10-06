import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
req=json.loads((root/'CONTROL_REQUEST.json').read_text())
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
for k,v in req['values'].items():a.set_editor_property(k,v)
sun=a.get_component_by_class(unreal.DirectionalLightComponent)
rot=sun.get_world_rotation();fwd=sun.get_forward_vector()
pp=a.get_component_by_class(unreal.PostProcessComponent)
RESULT={'name':req['name'],'inputs':{k:a.get_editor_property(k) for k in ['TimeOfDay','ManualSun','ManualDirection','ManualElevation','NorthOffset','Latitude','Longitude','TimeZone','Year','Month','Day','UseDaylightSavingTime','RigEnabled','OverrideExposure']},'clock':a.get_editor_property('ClockDisplay'),'status':a.get_editor_property('Status'),'sun_rotation':[rot.pitch,rot.yaw,rot.roll],'sun_forward':[fwd.x,fwd.y,fwd.z],'solar_elevation':a.get_editor_property('CorrectedElevation')-180,'azimuth':a.get_editor_property('Azimuth'),'sun_intensity':sun.intensity,'sun_visible':sun.is_visible(),'exposure_enabled':pp.get_editor_property('enabled'),'exposure_blend':pp.get_editor_property('blend_weight'),'update_invoked_explicitly':False}
(root/('CHECK_'+req['name']+'.json')).write_text(json.dumps(RESULT,indent=2))
