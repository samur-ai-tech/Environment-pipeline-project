import unreal,json,os,time,hashlib
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
base='/Game/Project/Shared/Atmosphere/ReusableSky/'
assert not unreal.EditorAssetLibrary.does_asset_exist(base+'M_EnvironmentCelestial'), 'Refuse overwrite existing retained material'
(root/'Resume/MATERIAL_STARTED.json').write_text(json.dumps({'pid':os.getpid(),'stage':'create','world_loaded':False}))
factory=unreal.MaterialFactoryNew();mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_EnvironmentCelestial',base.rstrip('/'),unreal.Material,factory)
assert mat
mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);mat.set_editor_property('two_sided',True);mat.set_editor_property('is_sky',True)
mel=unreal.MaterialEditingLibrary
def expr(cls):return mel.create_material_expression(mat,cls)
def wire(a,out,b,inp):assert mel.connect_material_expressions(a,out,b,inp),(a,b,inp)
view=expr(unreal.MaterialExpressionCameraVectorWS);neg=expr(unreal.MaterialExpressionMultiply);neg.set_editor_property('const_b',-1.0);wire(view,'',neg,'A')
moon_dir=expr(unreal.MaterialExpressionVectorParameter);moon_dir.set_editor_property('parameter_name','MoonDirection');moon_dir.set_editor_property('default_value',unreal.LinearColor(0,0,1,1))
params={}
for name,value in [('MoonLuminance',0.0),('MoonPhase',.5),('MoonDiameter',1.2),('StarLuminance',0.0),('NorthRadians',0.0)]:
 p=expr(unreal.MaterialExpressionScalarParameter);p.set_editor_property('parameter_name',name);p.set_editor_property('default_value',value);params[name]=p
custom=expr(unreal.MaterialExpressionCustom);custom.set_editor_property('code',(root/'Celestial.hlsl').read_text(encoding='utf-8-sig'));custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
inputs=[]
for n in ['ViewDirection','MoonDirection']+list(params):
 ci=unreal.CustomInput();ci.set_editor_property('input_name',n);inputs.append(ci)
custom.set_editor_property('inputs',inputs)
wire(neg,'',custom,'ViewDirection');wire(moon_dir,'',custom,'MoonDirection')
for n,p in params.items():wire(p,'',custom,n)
sky=expr(unreal.MaterialExpressionSkyAtmosphereViewLuminance);sun=expr(unreal.MaterialExpressionSkyAtmosphereLightDiskLuminance);sun.set_editor_property('light_index',0)
add=expr(unreal.MaterialExpressionAdd);wire(sky,'',add,'A');wire(sun,'',add,'B')
add2=expr(unreal.MaterialExpressionAdd);wire(add,'',add2,'A');wire(custom,'',add2,'B');assert mel.connect_material_property(add2,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.layout_material_expressions(mat)

(root/'Resume/MATERIAL_STARTED.json').write_text(json.dumps({'pid':os.getpid(),'stage':'compile','world_loaded':False}))
errors=unreal.MaterialEditingLibrary.recompile_material(mat)
assert not errors, str(errors)
stats=unreal.MaterialEditingLibrary.get_statistics(mat)
assert stats.num_pixel_shader_instructions>0, 'Material shader statistics are zero; refuse save: '+str(stats)
assert unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False)
RESULT={'pid':os.getpid(),'asset':mat.get_path_name(),'compile_errors':list(errors),'stats':str(unreal.MaterialEditingLibrary.get_statistics(mat)),'named_save':True,'map_save':False}
(root/'Resume/MATERIAL_SAVED.json').write_text(json.dumps(RESULT,indent=2))
print('SKY_MATERIAL_SAVED',json.dumps(RESULT))
