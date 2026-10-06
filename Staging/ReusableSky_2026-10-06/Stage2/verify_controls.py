import json,collections,os
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
keys=['TimeOfDay','ManualSun','ManualDirection','ManualElevation','NorthOffset','Year','Month','Day','Latitude','Longitude','TimeZone','UseDaylightSavingTime','OverrideExposure','SunIntensity','SkyIntensity']
original={k:json.loads((root/'PREFLIGHT.json').read_text())['public_controls'][k] for k in keys}
mi=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/MI_EnvironmentCloudDefaults')
mel=unreal.MaterialEditingLibrary
material_before={str(n):mel.get_material_instance_scalar_parameter_value(mi,n) for n in mel.get_scalar_parameter_names(mi)}
changes={'TimeOfDay':7.25,'ManualSun':True,'ManualDirection':123.0,'ManualElevation':27.0,'NorthOffset':37.0,'Year':2027,'Month':3,'Day':7,'TimeZone':3.0,'UseDaylightSavingTime':True}
for k,v in changes.items():a.set_editor_property(k,v)
expected={k:a.get_editor_property(k) for k in keys}
results=[]
for p in ['PresetClear','PresetPartlyCloudy','PresetOvercast','PresetHazy']:
 a.call_method(p)
 got={k:a.get_editor_property(k) for k in keys}
 assert got==expected,(p,got,expected)
 results.append({'preset':p,'preserved_time_location_manual_exposure':True,'amount':a.get_editor_property('CloudAmount'),'haze':a.get_editor_property('Haze')})
sun=a.get_component_by_class(unreal.DirectionalLightComponent)
def forward():
 f=a.get_component_by_class(unreal.DirectionalLightComponent).get_forward_vector();return [f.x,f.y,f.z]
manual_forward=forward();a.set_editor_property('ManualSun',False)
times=[]
for hour in [6.0,12.0,18.0]:
 a.set_editor_property('TimeOfDay',hour)
 assert a.get_editor_property('ManualDirection')==123.0 and a.get_editor_property('ManualElevation')==27.0
 times.append({'time':hour,'display':a.get_editor_property('ClockDisplay'),'sun_forward':forward()})
assert len({tuple(x['sun_forward']) for x in times})==3
a.set_editor_property('ManualSun',True)
assert forward()==manual_forward
assert a.get_editor_property('TimeOfDay')==18.0
counts=lambda:dict(collections.Counter(c.get_class().get_name() for c in a.get_components_by_class(unreal.ActorComponent)))
before=counts();mid=a.get_editor_property('CloudMID').get_path_name()
for i in range(50):a.call_method('UpdateSky')
assert counts()==before and a.get_editor_property('CloudMID').get_path_name()==mid
old_mid=mid;a.set_editor_property('CloudDirection',90.0);new_mid=a.get_editor_property('CloudMID').get_path_name();assert new_mid!=old_mid
assert counts()==before
material_after={str(n):mel.get_material_instance_scalar_parameter_value(mi,n) for n in mel.get_scalar_parameter_names(mi)}
assert material_before==material_after
for k,v in original.items():a.set_editor_property(k,v)
a.call_method('PresetPartlyCloudy')
for k,v in {'TimeOfDay':12.0,'ManualSun':False,'CloudSpeed':1.0,'CloudDirection':45.0,'HighQuality':False}.items():a.set_editor_property(k,v)
RESULT={'pid':os.getpid(),'presets':results,'time_positions':times,'manual_forward_restored':manual_forward,'repeated_updates':50,'component_classes':before,'component_count':sum(before.values()),'regular_update_reuses_mid':True,'construction_creates_fresh_mid':True,'material_defaults_unchanged':True,'cross_scene_second_instance_tested':False,'final_inputs':{k:a.get_editor_property(k) for k in keys}}
(root/'CONTROL_VERIFICATION.json').write_text(json.dumps(RESULT,indent=2))
