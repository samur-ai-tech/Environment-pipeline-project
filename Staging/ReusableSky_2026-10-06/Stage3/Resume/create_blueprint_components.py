import json,inspect
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools as AT
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3';base='/Game/Project/Shared/Atmosphere/ReusableSky/'
bp=unreal.load_asset(base+'BP_EnvironmentSky')
assert AT.add_component(bp,unreal.DirectionalLightComponent.static_class(),'MoonLight')
assert AT.add_component(bp,unreal.StaticMeshComponent.static_class(),'CelestialDome')
variables=[('MoonEnabled','bool','09 Moon',True),('MoonBrightness','float','09 Moon',.05),('MoonPhase','float','09 Moon',.5),('MoonDiskBrightness','float','09 Moon',2.0),('MoonAngularDiameter','float','09 Moon',1.2),('StarsEnabled','bool','10 Stars',True),('StarBrightness','float','10 Stars',.4),('AnimateTime','bool','11 Time Progression',False),('TimePaused','bool','11 Time Progression',False),('DayLengthMinutes','float','11 Time Progression',20.0),('NightSkyFill','float','12 Night Advanced',.08),('SunElevation','float','13 Readback',0.0),('NightBlend','float','13 Readback',0.0)]
for n,t,c,v in variables:
 BP.add_variable(bp,n,t);BP.set_variable_category(bp,n,c);BP.set_variable_instance_editable(bp,n,True)
BP.add_object_variable(bp,'CelestialMID',unreal.MaterialInstanceDynamic.static_class())
BP.compile_blueprint(bp,True)
cdo=unreal.get_default_object(bp.generated_class())
for n,t,c,v in variables:cdo.set_editor_property(n,v)
mat=unreal.load_asset(base+'M_EnvironmentCelestial');assert mat
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);c=unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
 if c.get_name().startswith('MoonLight'):
  c.set_editor_property('atmosphere_sun_light',True);c.set_editor_property('atmosphere_sun_light_index',1);c.set_editor_property('atmosphere_sun_disk_color_scale',unreal.LinearColor(0,0,0,1));c.set_editor_property('intensity',0.0);c.set_editor_property('light_source_angle',1.2);c.set_editor_property('cast_cloud_shadows',True);c.set_editor_property('visible',False);c.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
 if c.get_name().startswith('CelestialDome'):
  mesh=unreal.load_asset('/Engine/EngineSky/SM_SkySphere');assert mesh
  c.set_editor_property('static_mesh',mesh);c.set_material(0,mat);c.set_editor_property('relative_scale3d',unreal.Vector(2500,2500,2500));c.set_editor_property('cast_shadow',False);c.set_editor_property('visible',False);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property('affect_distance_field_lighting',False);c.set_editor_property('visible_in_ray_tracing',False)
BP.compile_blueprint(bp,True)
RESULT={'components_created':True,'compiled':True,'material_modified':False}
