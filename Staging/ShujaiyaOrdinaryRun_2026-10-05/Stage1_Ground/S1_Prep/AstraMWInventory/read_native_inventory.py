import unreal, os, json, pathlib, hashlib, datetime, collections, re
assert os.getpid()==10460
OUT=pathlib.Path(r"C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/AstraMWInventory")
OUT.mkdir(parents=True,exist_ok=True)
ROOT=pathlib.Path(unreal.Paths.project_dir()).resolve()
L=unreal.MaterialEditingLibrary
def ser(v):
    if v is None or isinstance(v,(bool,int,float,str)): return v
    if isinstance(v,unreal.Object): return v.get_path_name()
    if hasattr(v,'to_dict'):
        fields=v.to_dict()
        return {str(k):ser(x) for k,x in fields.items()} if fields else v.export_text()
    try:
        if not isinstance(v,unreal.Name): return [ser(x) for x in v]
    except: pass
    return str(v)
def props(o, names):
    d={}
    for k in sorted(set(names) | set(re.findall(r'- ``([^`]+)`` [(]', o.__doc__ or ''))):
        try: d[k]=ser(o.get_editor_property(k))
        except: pass
    return d
def snapshot():
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),'dirty_content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'dirty_maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
def hash_files():
    files=list((ROOT/'Content/MWLandscapeAutoMaterial').rglob('*'))
    files+=list((ROOT/'Content/Project/Shared/SurfacePainting/Appearance_20261003').glob('*'))
    files+=[ROOT/'Staging/ModelBank/EDITOR_OWNER.txt',ROOT/'Content/Python/geocity_landscape_workflow.py']
    for area in ['GazaShujaiya','GazaRimal']:
        files+=list((ROOT/f'Content/Project/Areas/{area}/BankIntegration_v015/Materials').glob('MI_GeoCityGround*'))
    return {str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
before=snapshot(); hashes=hash_files()
registry=unreal.AssetRegistryHelpers.get_asset_registry()
entries=registry.get_assets_by_path('/Game/MWLandscapeAutoMaterial',recursive=True)
catalog=[{'path':str(a.package_name)+'.'+str(a.asset_name),'class':str(a.asset_class_path.asset_name)} for a in entries]
targets=[x for x in catalog if x['class'] in ['Material','MaterialInstanceConstant','MaterialFunction','Texture2D','TextureRenderTarget2D']]
for path in ['/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural','/Game/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural','/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround','/Game/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround']:
    targets.append({'path':path,'class':'retained'})
nodeprops='desc parameter_name group default_value texture sampler_type sampler_source material_function input_name input_type output_name preview_value use_preview_value_as_default sort_priority parameter_expression_id layers parameter_name preview_weight grass_types const_a const_b const_c const_coordinate constant const_exponent min_default max_default r g b a value names inputs outputs code output_type mapping_scale mapping_type mapping_rotation mapping_pan_u mapping_pan_v world_position_shader_offset normalize uses_vertex_position x y z height_ratio reference_plane channel_names function_inputs function_outputs'.split()
records=[];errors=[]
for item in targets:
    try:
        a=unreal.load_asset(item['path'])
        rec={'path':a.get_path_name(),'class':a.get_class().get_name()}
        if isinstance(a,(unreal.Material,unreal.MaterialFunction)):
            nodes=L.get_material_expressions(a) if isinstance(a,unreal.Material) else L.get_material_function_expressions(a)
            rec['nodes']=[]
            for n in nodes:
                row={'name':n.get_name(),'class':n.get_class().get_name(),'properties':props(n,nodeprops)}
                try:
                    row['input_names']=ser(L.get_material_expression_input_names(n))
                    ins=L.get_inputs_for_material_expression(a,n) if isinstance(a,unreal.Material) else L.get_inputs_for_material_function_expression(a,n)
                    row['input_nodes']=[x.get_name() if x else None for x in ins]
                    row['output_names']=ser(L.get_material_expression_output_names(n))
                except Exception as e: row['connection_error']=str(e)
                rec['nodes'].append(row)
            rec.update(props(a,['description','material_domain','blend_mode','use_material_attributes','two_sided']))
        if isinstance(a,(unreal.Material,unreal.MaterialInstanceConstant)):
            rec['parameters']=[]
            for kind in ['scalar','vector','texture','static_switch']:
                for name in getattr(L,'get_'+kind+'_parameter_names')(a):
                    try:
                        fn='get_material_instance_'+kind+'_parameter_value' if isinstance(a,unreal.MaterialInstanceConstant) else 'get_material_default_'+kind+'_parameter_value'
                        value=ser(getattr(L,fn)(a,name))
                        rec['parameters'].append({'name':str(name),'type':kind,'effective_value':value})
                    except Exception as e: errors.append({'path':rec['path'],'parameter':str(name),'error':str(e)})
            rec['statistics']=ser(L.get_statistics(a))
            rec.update(props(a,['parent','scalar_parameter_values','vector_parameter_values','texture_parameter_values','static_parameters','static_parameters_editor_only']))
            if isinstance(a,unreal.Material):
                rec['material_outputs']={}
                for k in ['MP_BASE_COLOR','MP_NORMAL','MP_ROUGHNESS','MP_AMBIENT_OCCLUSION','MP_MATERIAL_ATTRIBUTES']:
                    try:
                        n=L.get_material_property_input_node(a,getattr(unreal.MaterialProperty,k))
                        rec['material_outputs'][k]=n.get_name() if n else None
                    except: pass
        if isinstance(a,unreal.Texture):
            rec.update(props(a,['compression_settings','srgb','lod_group','max_texture_size','lod_bias','virtual_texture_streaming','compression_no_alpha','address_x','address_y','mip_gen_settings','filter']))
            for dim in ['x','y']:
                try: rec['size_'+dim]=getattr(a,'blueprint_get_size_'+dim)()
                except: pass
            try: rec['registry_dimensions']=registry.get_asset_by_object_path(a.get_path_name()).get_tag_value('Dimensions')
            except: pass
        records.append(rec)
    except Exception as e: errors.append({'path':item['path'],'error':str(e)})
data={'before':before,'after':snapshot(),'catalog':catalog,'assets':records,'errors':errors,'hashes_before':hashes,'hashes_after':hash_files(),'method':'Read-only native property and graph APIs; no setters, saves, map loads, cooks or bakes.'}
(OUT/'native_inventory_complete.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps({'records':len(records),'classes':dict(collections.Counter(x['class'] for x in records)),'errors':errors,'before':before,'after':data['after'],'hashes_equal':data['hashes_before']==data['hashes_after']}))


