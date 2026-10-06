"""Retained native facade dependencies and natural Landscape appearance."""
import hashlib, json, os, runpy
from pathlib import Path
import unreal

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/AppearanceRepair_2026-10-03'
lease = (PROJECT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
baseline = json.loads((PROJECT/'Staging/RepairExecution_2026-10-03/INSTANCE_MATERIALS.json').read_text())
measurements = json.loads((HERE/'NATIVE_VARIETY_MEASUREMENTS.json').read_text())
ROOT = '/Game/Project/Shared/ModelBank/Materials/Appearance_20261003'
copies = {p:unreal.load_asset(v) for p,v in baseline['copies'].items()}
created = {}

def compatible_copy(source):
    p = source.get_path_name()
    if p in copies:
        assert copies[p]
        return copies[p]
    is_master = isinstance(source,unreal.Material)
    assert is_master or isinstance(source,unreal.MaterialInstanceConstant), p
    target = ROOT + '/' + ('M_' if is_master else 'MI_') + hashlib.sha256(p.encode()).hexdigest()[:12]
    copy = unreal.load_asset(target) if unreal.EditorAssetLibrary.does_asset_exist(target) else unreal.EditorAssetLibrary.duplicate_asset(p,target)
    assert copy
    copies[p] = copy
    if is_master:
        copy.set_editor_property('used_with_instanced_static_meshes',True)
        copy.set_editor_property('automatically_set_usage_in_editor',False)
        unreal.MaterialEditingLibrary.recompile_material(copy)
    else:
        copy.set_editor_property('parent',compatible_copy(source.get_editor_property('parent')))
        unreal.MaterialEditingLibrary.update_material_instance(copy)
    created[target] = copy
    return copy

slots = dict(baseline['mesh_slots'])
for item in measurements['meshes']:
    mesh = unreal.load_asset(item['mesh'])
    assert isinstance(mesh,unreal.StaticMesh)
    original = [s.material_interface for s in mesh.get_editor_property('static_materials')]
    assert [m.get_path_name() for m in original]==item['materials']
    slots[item['mesh']] = [compatible_copy(m).get_path_name() for m in original]
for path in sorted(created):
    assert unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=True), path
(HERE/'INSTANCE_MATERIALS.json').write_text(json.dumps({'mesh_slots':slots,'copies':{p:o.get_path_name() for p,o in copies.items()},'saved_paths':sorted(created)},indent=2)+'\n')

# Preserve every bank layer name and custom RGB route, replacing only appearance.
h = runpy.run_path(str(PROJECT/'Staging/PaintBank_2026-10-02/author_all_layers_surface_material.py'))
catalog,names,layers = h['load_inputs']()
node,link,texture = h['node'],h['link'],h['texture']
SROOT = '/Game/Project/Shared/SurfacePainting/Appearance_20261003'
MPATH,IPATH = SROOT+'/M_SurfaceBank_Natural',SROOT+'/MI_SurfaceBank_Natural'
assert not (HERE/'SURFACE_MATERIAL.json').exists(), 'Already authored; inspect named receipt before rerun'
tools = unreal.AssetToolsHelpers.get_asset_tools()
material = unreal.load_asset(MPATH) if unreal.EditorAssetLibrary.does_asset_exist(MPATH) else tools.create_asset('M_SurfaceBank_Natural',SROOT,unreal.Material,unreal.MaterialFactoryNew())
assert material
assert material.get_path_name()==MPATH+'.M_SurfaceBank_Natural'
unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_OPAQUE)
material.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
wc = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture')
wn = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal')
cb,nb,rb = [h['blend'](material,layers,y) for y in (0,650,1300)]

def aligned(tex,parameter,size,x,y,function):
    obj = node(material,unreal.MaterialExpressionTextureObjectParameter,x,y,parameter_name=parameter,texture=texture(tex))
    fn = node(material,unreal.MaterialExpressionMaterialFunctionCall,x+450,y,material_function=function)
    link(obj,'',fn,'TextureObject'); link(size,'',fn,'TextureSize')
    return fn

soil = next(o for o in catalog['texture_options'] if o['option_id']=='mout.Dirt_Path')
for index,option in enumerate(catalog['texture_options']):
    layer = names['texture_layers'][option['option_id']]
    y=index*850
    tile=float(option.get('default_tile_metres',2))*100
    tile={'Sand_01':220.,'Sand_02':350.,'Dirt_Path':260.,'Sand_Path':300.}.get(layer,tile)
    size=node(material,unreal.MaterialExpressionVectorParameter,-2300,y,parameter_name=layer+'_TileCm',default_value=unreal.LinearColor(tile,tile,tile,1))
    color=aligned(option['native_textures']['albedo'],layer+'_Albedo',size,-2300,y+100,wc)
    normal=aligned(option['native_textures']['normal'],layer+'_Normal',size,-2300,y+280,wn)
    color_output='XYZ Texture'
    if layer=='Sand_01':
        macro_size=node(material,unreal.MaterialExpressionVectorParameter,-2300,y+480,parameter_name='Ground_MacroTileCm',default_value=unreal.LinearColor(3600,3600,3600,1))
        mask=aligned('/Game/ModularCourtyard/Textures/T_dirt3_M.T_dirt3_M','Ground_MacroMask',macro_size,-2300,y+600,wc)
        channel=node(material,unreal.MaterialExpressionComponentMask,-1380,y+620,r=True,g=False,b=False,a=False)
        link(mask,'XYZ Texture',channel,'None')
        strength=node(material,unreal.MaterialExpressionScalarParameter,-1380,y+720,parameter_name='Ground_SoilBlendStrength',default_value=.25)
        alpha=node(material,unreal.MaterialExpressionMultiply,-1150,y+620)
        link(channel,'',alpha,'A'); link(strength,'',alpha,'B')
        soil_color=aligned(soil['native_textures']['albedo'],'Ground_MacroSoilAlbedo',size,-2300,y+780,wc)
        soil_normal=aligned(soil['native_textures']['normal'],'Ground_MacroSoilNormal',size,-2300,y+960,wn)
        color_lerp=node(material,unreal.MaterialExpressionLinearInterpolate,-800,y+140)
        link(color,'XYZ Texture',color_lerp,'A');link(soil_color,'XYZ Texture',color_lerp,'B');link(alpha,'',color_lerp,'Alpha')
        normal_lerp=node(material,unreal.MaterialExpressionLinearInterpolate,-800,y+320)
        link(normal,'XYZ Texture',normal_lerp,'A');link(soil_normal,'XYZ Texture',normal_lerp,'B');link(alpha,'',normal_lerp,'Alpha')
        normal_unit=node(material,unreal.MaterialExpressionNormalize,-530,y+320)
        link(normal_lerp,'',normal_unit,'VectorInput')
        color,color_output=color_lerp,''
        normal,normal_output=normal_unit,''
    else:
        normal_output='XYZ Texture'
    tint_rgb=h['rgb_linear'](option.get('default_tint_hex','#FFFFFF'))
    tint=node(material,unreal.MaterialExpressionVectorParameter,-500,y+100,parameter_name=layer+'_Tint',default_value=unreal.LinearColor(*tint_rgb,1))
    colored=node(material,unreal.MaterialExpressionMultiply,-270,y+100)
    link(color,color_output,colored,'A');link(tint,'',colored,'B')
    rough=node(material,unreal.MaterialExpressionScalarParameter,-500,y+520,parameter_name=layer+'_Roughness',default_value=float(option.get('default_roughness',.85)))
    link(colored,'',cb,'Layer '+layer);link(normal,normal_output,nb,'Layer '+layer);link(rough,'',rb,'Layer '+layer)
offset=len(catalog['texture_options'])
for index,preset in enumerate(catalog['solid_color_presets']):
    h['make_solid_branch'](material,preset,names['solid_layers'][preset['preset_id']],offset+index,cb,nb,rb)
offset+=len(catalog['solid_color_presets'])
for index,role in enumerate(h['ROLES']):
    h['make_custom_branch'](material,role,names['custom_layers'][role],offset+index,cb,nb,rb)
for expr,prop in ((cb,unreal.MaterialProperty.MP_BASE_COLOR),(nb,unreal.MaterialProperty.MP_NORMAL),(rb,unreal.MaterialProperty.MP_ROUGHNESS)):
    assert unreal.MaterialEditingLibrary.connect_material_property(expr,'',prop)
unreal.MaterialEditingLibrary.recompile_material(material)
instance=unreal.load_asset(IPATH) if unreal.EditorAssetLibrary.does_asset_exist(IPATH) else tools.create_asset('MI_SurfaceBank_Natural',SROOT,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
assert instance
unreal.MaterialEditingLibrary.set_material_instance_parent(instance,material)
for layer,rgb in {'Sand_01':(1.,.97,.90),'Sand_02':(.76,.78,.77),'Dirt_Path':(.78,.72,.63),'Sand_Path':(.88,.82,.71)}.items():
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance,layer+'_Tint',unreal.LinearColor(*rgb,1))
    v=unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(instance,layer+'_Tint')
    assert max(abs(a-b) for a,b in zip((v.r,v.g,v.b),rgb))<1e-6
unreal.MaterialEditingLibrary.update_material_instance(instance)
for path in (MPATH,IPATH):
    assert unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=True)
result={'schema':'environmentpipeline.retained_natural_surface.v1','master':material.get_path_name(),'instance':instance.get_path_name(),'weight_layer_count':len(layers),'texture_layer_count':len(catalog['texture_options']),'preserved_layer_names':layers,'ground_macro_mask':'/Game/ModularCourtyard/Textures/T_dirt3_M','macro_tile_cm':3600,'soil_blend_strength':.25,'native_soil_textures':soil['native_textures'],'saved_paths':[MPATH,IPATH],'landuse_claim':'Visual material variation only; geographic source masks unchanged'}
(HERE/'SURFACE_MATERIAL.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'saved_instancing_materials':len(created),'native_mesh_families':len(slots),'landscape':result['instance'],'preserved_bank_layer_count':len(layers)}))
