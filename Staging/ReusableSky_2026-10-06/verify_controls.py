import json,math
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
checks=[]
def setprops(**kw):
 for k,v in kw.items():a.set_editor_property(k,v)
def state():
 sun=a.get_component_by_class(unreal.DirectionalLightComponent);f=sun.get_forward_vector()
 return {'time':a.get_editor_property('TimeOfDay'),'clock':a.get_editor_property('ClockDisplay'),'manual':a.get_editor_property('ManualSun'),'direction':a.get_editor_property('ManualDirection'),'elevation':a.get_editor_property('ManualElevation'),'sun_forward':[f.x,f.y,f.z],'azimuth':a.get_editor_property('Azimuth'),'corrected_elevation':a.get_editor_property('CorrectedElevation'),'status':a.get_editor_property('Status')}
setprops(TimeOfDay=12.5,ManualDirection=123.0,ManualElevation=27.0,ManualSun=True)
m=state();assert m['clock']=='12:30' and m['azimuth']==123 and m['corrected_elevation']==207;checks.append({'manual':m})
setprops(TimeOfDay=7.25);m2=state();assert m2['sun_forward']==m['sun_forward'];checks.append({'time_edit_in_manual_does_not_rotate':True})
setprops(ManualSun=False);t=state();assert t['time']==7.25 and t['direction']==123 and t['elevation']==27 and t['sun_forward']!=m['sun_forward']
setprops(ManualSun=True);assert state()['sun_forward']==m['sun_forward'];checks.append({'round_trip_keeps_both_modes':True})
setprops(NorthOffset=90.0);north=state();assert north['sun_forward']!=m['sun_forward'];checks.append({'north_offset_rotates_sun':True})
setprops(NorthOffset=0.0,ManualSun=False,TimeOfDay=24.0);mid=state();assert mid['clock']=='00:00' and mid['time']==0;checks.append({'midnight_wrap':mid})
setprops(Year=2024,Month=2,Day=29,TimeOfDay=12.0);leap=state();assert math.isfinite(leap['corrected_elevation']);checks.append({'leap_date':leap})
setprops(Year=2026,Month=6,Day=21,TimeOfDay=12.0,UseDaylightSavingTime=False);base=state()
setprops(UseDaylightSavingTime=True);dst=state();assert dst['sun_forward']!=base['sun_forward'];checks.append({'explicit_DST_changes_solar_position':True})
setprops(UseDaylightSavingTime=False,TimeOfDay=6.0);first=state();setprops(TimeOfDay=18.0);setprops(TimeOfDay=6.0);assert state()['sun_forward']==first['sun_forward'];checks.append({'repeat_time_deterministic':True})
setprops(OverrideExposure=True)
pp=a.get_component_by_class(unreal.PostProcessComponent);assert pp.get_editor_property('enabled') and pp.get_editor_property('blend_weight')==1.0
setprops(OverrideExposure=False);pp=a.get_component_by_class(unreal.PostProcessComponent);assert not pp.get_editor_property('enabled') and pp.get_editor_property('blend_weight')==0.0
checks.append({'exposure_opt_in':True})
setprops(TimeOfDay=12.0,ManualDirection=180.0,ManualElevation=35.0)
RESULT={'checks':checks,'final':state(),'all_passed':True,'explicit_UpdateSky_calls':0,'Play_pressed':False}
(root/'CONTROL_VERIFICATION.json').write_text(json.dumps(RESULT,indent=2))
