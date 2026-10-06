import json,inspect
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3';base='/Game/Project/Shared/Atmosphere/ReusableSky/'
bp=unreal.load_asset(base+'BP_EnvironmentSky');mat=unreal.load_asset(base+'M_EnvironmentCelestial');mel=unreal.MaterialEditingLibrary
nodes=mel.get_material_expressions(mat)
custom=next(x for x in nodes if isinstance(x,unreal.MaterialExpressionCustom));moon_dir=next(x for x in nodes if isinstance(x,unreal.MaterialExpressionSkyAtmosphereLightDirection));neg=next(x for x in nodes if isinstance(x,unreal.MaterialExpressionMultiply))
params={str(x.get_editor_property('parameter_name')):x for x in nodes if isinstance(x,unreal.MaterialExpressionScalarParameter)}
def expr(cls):return mel.create_material_expression(mat,cls)
def wire(a,out,b,inp):assert mel.connect_material_expressions(a,out,b,inp),(a,b,inp)
inputs=[]
for n in ['ViewDirection','MoonDirection']+list(params):
 ci=unreal.CustomInput();ci.set_editor_property('input_name',n);inputs.append(ci)
custom.set_editor_property('inputs',inputs)
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
