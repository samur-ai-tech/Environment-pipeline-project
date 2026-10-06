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
factory=unreal.MaterialFactoryNew();mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_EnvironmentCelestial',base.rstrip('/'),unreal.Material,factory)
assert mat
mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);mat.set_editor_property('two_sided',True);mat.set_editor_property('is_sky',True)
mel=unreal.MaterialEditingLibrary
def expr(cls):return mel.create_material_expression(mat,cls)
def wire(a,out,b,inp):assert mel.connect_material_expressions(a,out,b,inp),(a,b,inp)
view=expr(unreal.MaterialExpressionCameraVectorWS);neg=expr(unreal.MaterialExpressionMultiply);neg.set_editor_property('const_b',-1.0);wire(view,'',neg,'A')
moon_dir=expr(unreal.MaterialExpressionSkyAtmosphereLightDirection);moon_dir.set_editor_property('light_index',1)
params={}
for name,value in [('MoonLuminance',0.0),('MoonPhase',.5),('MoonDiameter',1.2),('StarLuminance',0.0),('NorthRadians',0.0)]:
 p=expr(unreal.MaterialExpressionScalarParameter);p.set_editor_property('parameter_name',name);p.set_editor_property('default_value',value);params[name]=p
custom=expr(unreal.MaterialExpressionCustom);custom.set_editor_property('code',(root/'Celestial.hlsl').read_text(encoding='utf-8-sig'));custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
custom.set_editor_property('inputs',[unreal.CustomInput(input_name=n) for n in ['ViewDirection','MoonDirection']+list(params)])
wire(neg,'',custom,'ViewDirection');wire(moon_dir,'',custom,'MoonDirection')
for n,p in params.items():wire(p,'',custom,n)
sky=expr(unreal.MaterialExpressionSkyAtmosphereViewLuminance);sun=expr(unreal.MaterialExpressionSkyAtmosphereLightDiskLuminance);sun.set_editor_property('light_index',0)
add=expr(unreal.MaterialExpressionAdd);wire(sky,'',add,'A');wire(sun,'',add,'B')
add2=expr(unreal.MaterialExpressionAdd);wire(add,'',add2,'A');wire(custom,'',add2,'B');assert mel.connect_material_property(add2,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.layout_material_expressions(mat);mel.recompile_material(mat)
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);c=unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
 if c.get_name().startswith('MoonLight'):
  c.set_editor_property('atmosphere_sun_light',True);c.set_editor_property('atmosphere_sun_light_index',1);c.set_editor_property('atmosphere_sun_disk_color_scale',unreal.LinearColor(0,0,0,1));c.set_editor_property('intensity',0.0);c.set_editor_property('light_source_angle',1.2);c.set_editor_property('cast_cloud_shadows',True);c.set_editor_property('visible',False);c.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
 if c.get_name().startswith('CelestialDome'):
  mesh=unreal.load_asset('/Engine/EngineSky/SM_SkySphere');assert mesh
  c.set_editor_property('static_mesh',mesh);c.set_material(0,mat);c.set_editor_property('relative_scale3d',unreal.Vector(100000,100000,100000));c.set_editor_property('cast_shadow',False);c.set_editor_property('visible',False);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property('affect_distance_field_lighting',False)
BP.compile_blueprint(bp,True)
RESULT={'created':['MoonLight','CelestialDome',base+'M_EnvironmentCelestial'],'saved':False,'add_param_doc':inspect.signature(BP.add_function_param).__str__(),'event_doc':inspect.signature(BP.add_event).__str__(),'functions':BP.list_functions(bp)}
(root/'FOUNDATION.json').write_text(json.dumps(RESULT,indent=2,default=str))
