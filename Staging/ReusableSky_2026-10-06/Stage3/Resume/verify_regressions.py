import json,collections,math,os
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
keys=['TimeOfDay','ManualSun','ManualDirection','ManualElevation','NorthOffset','Year','Month','Day','Latitude','Longitude','TimeZone','UseDaylightSavingTime','OverrideExposure','SunIntensity','SkyIntensity','MoonEnabled','MoonBrightness','MoonDiskBrightness','MoonPhase','StarsEnabled','StarBrightness','AnimateTime','TimePaused','DayLengthMinutes','NightSkyFill']
original={k:a.get_editor_property(k) for k in keys}
counts=lambda:dict(collections.Counter(c.get_class().get_name() for c in a.get_components_by_class(unreal.ActorComponent)))
def vec(c):
 v=c.get_forward_vector();return [v.x,v.y,v.z]
sun=a.get_editor_property('DirectionalLight');moon=a.get_editor_property('MoonLight')
for k,v in {'TimeOfDay':7.25,'ManualSun':True,'ManualDirection':123.,'ManualElevation':27.,'NorthOffset':37.,'MoonPhase':.25,'StarsEnabled':False}.items():a.set_editor_property(k,v)
expected={k:a.get_editor_property(k) for k in keys};presets=[]
for fn in ['PresetClear','PresetPartlyCloudy','PresetOvercast','PresetHazy']:
 a.call_method(fn);assert {k:a.get_editor_property(k) for k in keys}==expected
 presets.append(fn)
manual=vec(a.get_editor_property('DirectionalLight'));a.set_editor_property('ManualSun',False)
for t in [6.,12.,18.]:
 a.set_editor_property('TimeOfDay',t);assert a.get_editor_property('ManualDirection')==123. and a.get_editor_property('ManualElevation')==27.
a.set_editor_property('ManualSun',True);assert vec(a.get_editor_property('DirectionalLight'))==manual and a.get_editor_property('TimeOfDay')==18.
for k,v in original.items():a.set_editor_property(k,v)
a.set_editor_property('ManualSun',False);a.call_method('PresetClear')
samples=[]
for t in [0.,4.,4.5,5.,5.5,6.,12.,17.5,18.,18.5,19.,20.,23.99,0.01]:
 a.call_method('SetSkyTime',(t,));s=a.get_editor_property('DirectionalLight');m=a.get_editor_property('MoonLight');sv=vec(s);mv=vec(m)
 assert abs(sum(x*y for x,y in zip(sv,mv))+1)<1e-5
 samples.append({'hour':t,'clock':a.get_editor_property('ClockDisplay'),'sun_elevation':a.get_editor_property('SunElevation'),'sun_lux':s.intensity,'moon_lux':m.intensity,'night_blend':a.get_editor_property('NightBlend'),'star_luminance':a.get_editor_property('CelestialMID').get_scalar_parameter_value('StarLuminance'),'sun_forward':sv,'moon_forward':mv})
a.call_method('SetSkyTime',(12.,));a.call_method('SetStarAppearance',(True,.4));assert a.get_editor_property('TimeOfDay')==12. and a.get_editor_property('CelestialMID').get_scalar_parameter_value('StarLuminance')==0
a.call_method('SetSkyTime',(0.,));phase=[]
for p in [0.,.25,.5,.75,1.]:
 a.call_method('SetMoonAppearance',(True,.05,2.,p));phase.append({'phase':p,'moon_lux':a.get_editor_property('MoonLight').intensity})
a.call_method('SetMoonAppearance',(False,.05,2.,.5));assert not a.get_editor_property('MoonLight').is_visible() and a.get_editor_property('MoonLight').intensity==0 and a.get_editor_property('CelestialMID').get_scalar_parameter_value('MoonLuminance')==0
a.call_method('SetSkyTime',(23.99,));a.call_method('SetTimeProgression',(True,False,20.));assert a.is_actor_tick_enabled()
a.call_method('AdvanceSkyTime',(1.,));assert abs(a.get_editor_property('TimeOfDay')-.01)<1e-5
a.call_method('SetTimeProgression',(True,True,20.));assert not a.is_actor_tick_enabled();before=a.get_editor_property('TimeOfDay');a.call_method('AdvanceSkyTime',(20.,));assert a.get_editor_property('TimeOfDay')==before
a.call_method('SetTimeProgression',(False,False,20.));assert not a.is_actor_tick_enabled()
c=counts();mids=[a.get_editor_property(n).get_path_name() for n in ['CloudMID','CelestialMID']]
for i in range(50):a.call_method('UpdateSky')
assert counts()==c and [a.get_editor_property(n).get_path_name() for n in ['CloudMID','CelestialMID']]==mids
for k,v in original.items():a.set_editor_property(k,v)
a.call_method('PresetPartlyCloudy');a.set_editor_property('CloudSpeed',1.);a.set_editor_property('TimeOfDay',12.)
RESULT={'pid':os.getpid(),'weather_preserves_independent_choices':presets,'manual_and_time_buffers_preserved':True,'samples':samples,'moon_phase_lighting':phase,'moon_disable':True,'stars_enable_keeps_day':True,'progression_callable_wrap_and_pause':True,'actual_runtime_tick_tested':False,'repeated_updates':50,'component_counts':c,'transient_mids_reused_on_regular_update':True,'exposure_unchanged':not a.get_editor_property('OverrideExposure')}
(r/'Resume/REGRESSION_VERIFICATION.json').write_text(json.dumps(RESULT,indent=2))
