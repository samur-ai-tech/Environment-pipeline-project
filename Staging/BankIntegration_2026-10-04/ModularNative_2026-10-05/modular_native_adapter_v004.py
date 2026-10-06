"""Bounded 20-family native import. No catalog, map, generator or eligibility writes."""
import collections, hashlib, itertools, json, math, os, subprocess, sys
from pathlib import Path
import unreal
import bank_contracts as C
import native_bank_ops as N
import import_prepared as P
import bank_batch_loader as L

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
E=unreal.EditorAssetLibrary
M=unreal.MaterialEditingLibrary
NATIVE_ROOT='/Game/Project/Shared/ModelBank/Prepared/Modular'
MANAGER='01a10789-2e6a-7321-ad85-0a2964f8a937'
OPERATOR='01a1067c-5012-7550-b449-015b53c9d726'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def protected_files(path):
    value=read(path);assert value['schema']=='environmentpipeline.modular_native_preservation.v1'
    return {p:s.lower() for p,s in value['files'].items()}
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def preflight(request_path,request_sha,activation_path):
    assert sha(request_path)==request_sha,'request_changed'
    request=read(request_path)
    for path,expected in request['python_sources'].items():assert sha(path)==expected,('python_source_changed',path)
    modules=[C,N,P,L,sys.modules[__name__]]
    for module in modules:
        path=str(Path(module.__file__).resolve())
        assert path in request['python_sources'],('unsealed_module',path)
        L.verify_module(module,path)
    activation=read(activation_path)
    assert activation['status']=='MODULAR_NATIVE_CONTENT_ACTIVATED'
    assert activation['request_sha256']==request_sha and activation['native_authorized_now'] is True
    assert activation['ordinary_generation_authorized'] is False
    assert activation['manager_thread_id']==MANAGER and activation['operator_thread_id']==OPERATOR
    assert activation['assigned_editor_PID']==os.getpid()
    assert sha(activation['resumption_path'])==activation['resumption_sha256']
    process_ids=json.loads(subprocess.check_output(['powershell','-NoProfile','-NonInteractive','-Command','ConvertTo-Json -Compress -InputObject @((Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Id)'],creationflags=subprocess.CREATE_NO_WINDOW,text=True))
    assert process_ids==[os.getpid()],('multiple_or_wrong_editor',process_ids)
    assert sha(activation['preservation_path'])==activation['preservation_sha256']
    for path,expected in protected_files(activation['preservation_path']).items():assert sha(path)==expected,('protected_file_changed',path)
    import geocity_editor_action,geocity_runtime_guard
    lease=[l for l in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if l.strip()][-1]
    fields=geocity_editor_action.lease_fields(lease)
    assert fields.get('OWNER')=='CODEX_BANK_INTEGRATION'
    assert fields.get('operator_thread_id')==OPERATOR and fields.get('manager_thread_id')==MANAGER
    assert fields.get('assigned_editor_PID')==str(os.getpid())
    assert fields.get('activation')=='MODULAR_NATIVE_CONTENT_ACTIVATED'
    assert fields.get('native_authorized_now')=='true'
    assert fields.get('ordinary_generation_authorized')=='false'
    geocity_runtime_guard.verify()
    assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
    assert world==activation['world'],'world_changed'
    assert N.dirty()=={'content':[],'maps':[]},('requires_clean_boundary',N.dirty())
    return request,{'pid':os.getpid(),'world':world,'activation_sha256':sha(activation_path)}

def constant(mat,value):
    if isinstance(value,(list,tuple)):
        n=M.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector)
        n.set_editor_property('constant',unreal.LinearColor(*value[:3],1))
    else:
        n=M.create_material_expression(mat,unreal.MaterialExpressionConstant);n.set_editor_property('r',float(value))
    return n

def arithmetic(mat,cls,a,b=None):
    node=M.create_material_expression(mat,cls)
    assert M.connect_material_expressions(a[0],a[1],node,'A' if b else 'VectorInput')
    if b:assert M.connect_material_expressions(b[0],b[1],node,'B')
    return node

def material_for(recipe,created,used):
    key=digest(recipe);dest=NATIVE_ROOT+'/Dependencies/Materials/M_'+key[:20]
    if E.does_asset_exist(dest):
        receipt_file=HERE/'MaterialReceipts'/(key+'.json')
        if not receipt_file.is_file():
            mat=unreal.load_asset(dest)
            assert dest in RESUME_OWNED,('unreceipted_unowned_material',dest)
            assert E.get_metadata_tag(mat,'ModularRecipeSHA256')==key
            assert E.get_metadata_tag(mat,'ModularRecipeComplete')=='true'
            created[dest]=mat
            for tex in M.get_used_textures(mat):
                path=tex.get_path_name().split('.')[0]
                if path in N.dirty()['content']:
                    assert path in RESUME_OWNED,('unowned_dirty_texture',path)
                    created[path]=tex
            return mat
        material_receipt=read(receipt_file)
        assert material_receipt['recipe_sha256']==key
        for path,expected in material_receipt['saved_packages'].items():assert sha(C.package_file(path))==expected,('material_dependency_changed',path)
        mat=unreal.load_asset(dest)
        assert E.get_metadata_tag(mat,'ModularRecipeSHA256')==key
        assert E.get_metadata_tag(mat,'ModularRecipeComplete')=='true'
        assert C.package_file(dest).is_file() and dest not in N.dirty()['content']
        return mat
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(dest.rsplit('/',1)[1],dest.rsplit('/',1)[0],unreal.Material,unreal.MaterialFactoryNew())
    assert mat
    created[dest]=mat
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    mat.set_editor_property('automatically_set_usage_in_editor',False)
    mat.set_editor_property('two_sided',recipe['two_sided'])
    mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_OPAQUE)
    samples={}
    def sample(key):
        if key not in samples:
            ref=recipe['textures'][key];assert sha(ref['path'])==ref['sha256']
            if ref['kind']=='normal':
                texture_dest=NATIVE_ROOT+'/Dependencies/Textures/T_'+ref['sha256'][:20]+'_NormalRGB'
                if E.does_asset_exist(texture_dest):
                    obj=unreal.load_asset(texture_dest)
                    assert E.get_metadata_tag(obj,'ModularSourceSHA256')==ref['sha256']
                else:
                    objects=P.import_file(ref['path'],texture_dest)
                    assert len(objects)==1 and isinstance(objects[0],unreal.Texture2D)
                    obj=objects[0]
                    obj.set_editor_property('srgb',False)
                    obj.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP)
                    obj.set_editor_property('flip_green_channel',False)
                    E.set_metadata_tag(obj,'ModularSourceSHA256',ref['sha256'])
                    created[texture_dest]=obj
                assert not obj.get_editor_property('srgb') and not obj.get_editor_property('flip_green_channel')
                assert obj.get_editor_property('compression_settings')==unreal.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP
                used.append({'source':ref['path'],'source_sha256':ref['sha256'],'native_path':obj.get_path_name(),'kind':'linear_RGB_normal_no_reconstructed_blue'})
            else:
                obj=P.texture(ref,ref['kind'],created,used)
                assert obj.get_editor_property('srgb')==(ref['kind']=='color')
                assert obj.get_editor_property('compression_settings') in ({'color':(unreal.TextureCompressionSettings.TC_DEFAULT,unreal.TextureCompressionSettings.TC_EDITOR_ICON),'data':(unreal.TextureCompressionSettings.TC_MASKS,)}[ref['kind']])
                assert not obj.get_editor_property('flip_green_channel')
            assert obj.get_editor_property('address_x')==unreal.TextureAddress.TA_WRAP and obj.get_editor_property('address_y')==unreal.TextureAddress.TA_WRAP
            assert obj.get_editor_property('filter') in (unreal.TextureFilter.TF_DEFAULT,unreal.TextureFilter.TF_BILINEAR,unreal.TextureFilter.TF_TRILINEAR)
            node=M.create_material_expression(mat,unreal.MaterialExpressionTextureSample)
            node.set_editor_property('texture',obj)
            node.set_editor_property('sampler_type',{'normal':unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,'color':unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,'data':unreal.MaterialSamplerType.SAMPLERTYPE_MASKS}[ref['kind']])
            uv=M.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate)
            uv.set_editor_property('coordinate_index',0)
            uv.set_editor_property('u_tiling',ref['uv_scale'][0]);uv.set_editor_property('v_tiling',ref['uv_scale'][1])
            assert ref['uv_offset']==[0,0], 'unsupported_nonzero_uv_offset'
            assert M.connect_material_expressions(uv,'',node,'UVs')
            samples[key]=node
        return samples[key]
    def expression(channel):
        if 'constant' in channel:return constant(mat,channel['constant']),''
        return sample(channel['texture']),channel['output']
    for name,prop in [('Base Color',unreal.MaterialProperty.MP_BASE_COLOR),('Roughness',unreal.MaterialProperty.MP_ROUGHNESS),('Metallic',unreal.MaterialProperty.MP_METALLIC)]:
        n,port=expression(recipe['channels'][name]);assert M.connect_material_property(n,port,prop)
    P.scalar(mat,recipe['specular'],unreal.MaterialProperty.MP_SPECULAR)
    strength=recipe['normal']['strength']
    if 'texture' in recipe['normal']:
        n=sample(recipe['normal']['texture']);clamped=min(1.0,max(0.0,strength))
        # Keep the source blue channel; decode RGB and convert OpenGL green exactly once.
        decoded=arithmetic(mat,unreal.MaterialExpressionMultiply,(n,'RGB'),(constant(mat,[2,-2,2]),''))
        decoded=arithmetic(mat,unreal.MaterialExpressionAdd,(decoded,''),(constant(mat,[-1,1,-1]),''))
        scale=constant(mat,[strength,strength,clamped]);bias=constant(mat,[0,0,1-clamped])
        mul=arithmetic(mat,unreal.MaterialExpressionMultiply,(decoded,''),(scale,''))
        add=arithmetic(mat,unreal.MaterialExpressionAdd,(mul,''),(bias,''))
        normalized=M.create_material_expression(mat,unreal.MaterialExpressionNormalize)
        assert M.connect_material_expressions(add,'',normalized,'VectorInput')
        assert M.connect_material_property(normalized,'',unreal.MaterialProperty.MP_NORMAL)
    else:P.vector(mat,[0,0,1],unreal.MaterialProperty.MP_NORMAL)
    n,port=expression(recipe['channels']['Emission Color'])
    mul=arithmetic(mat,unreal.MaterialExpressionMultiply,(n,port),(constant(mat,recipe['emission_strength']),''))
    assert M.connect_material_property(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    E.set_metadata_tag(mat,'ModularRecipeSHA256',key)
    E.set_metadata_tag(mat,'ModularSourceGraphSHA256',recipe['source_graph_sha256'])
    E.set_metadata_tag(mat,'ModularNormalStrength',repr(strength))
    E.set_metadata_tag(mat,'ModularRecipeComplete','true')
    M.layout_material_expressions(mat);M.recompile_material(mat)
    return mat

def transform(p,basis):return [100*sum(row[k]*p[k] for k in range(3)) for row in basis]

def read_basis_and_uv(mesh,part,measurement,expected_basis=None):
    desc=mesh.get_static_mesh_description(0)
    vertices=[]
    for i in range(desc.get_vertex_count()):
        v=unreal.VertexID();v.set_editor_property('id_value',i)
        p=desc.get_vertex_position(v);vertices.append([p.x,p.y,p.z])
    tolerance=0.025
    cells=collections.defaultdict(list)
    def cell(p):return tuple(math.floor(x/tolerance) for x in p)
    for p in vertices:cells[cell(p)].append(p)
    neighbors=list(itertools.product((-1,0,1),repeat=3))
    def exists(p):
        key=cell(p)
        return any(max(abs(a-b) for a,b in zip(p,q))<=tolerance for d in neighbors for q in cells.get(tuple(a+b for a,b in zip(key,d)),[]))
    source_corners=list(itertools.product(*zip(part['local_bounds_m']['min'],part['local_bounds_m']['max'])))
    matches=[]
    for swap in (False,True):
        for sx,sy in itertools.product((-1,1),repeat=2):
            basis=[[0,sx,0],[sy,0,0],[0,0,1]] if swap else [[sx,0,0],[0,sy,0],[0,0,1]]
            corners=[transform(p,basis) for p in source_corners]
            bounds={'min':[min(p[k] for p in corners) for k in range(3)],'max':[max(p[k] for p in corners) for k in range(3)]}
            error=max(abs(bounds[key][k]-measurement['bounds_cm'][key][k]) for key in ('min','max') for k in range(3))
            if error<=tolerance and all(exists(transform(p,basis)) for p in part['sample_local_vertices_m']):matches.append((basis,error))
    independently_unique=len(matches)==1
    if expected_basis is not None:matches=[m for m in matches if m[0]==expected_basis]
    assert len(matches)==1,('source_to_native_basis_ambiguous_or_changed',part['name'],matches)
    basis,error=matches[0]
    # Match source position/UV pairs against actual native vertex instances, allowing UE's V convention.
    native_uv=collections.defaultdict(list)
    for i in range(desc.get_vertex_instance_count()):
        vi=unreal.VertexInstanceID();vi.set_editor_property('id_value',i)
        vid=desc.get_vertex_instance_vertex(vi);p=desc.get_vertex_position(vid)
        uv=desc.get_vertex_instance_uv(vi,0)
        native_uv[cell([p.x,p.y,p.z])].append(([p.x,p.y,p.z],[uv.x,uv.y]))
    uv_modes=[]
    for flip_v in (False,True):
        passed=True
        for probe in part['source_uv0_probes']:
            p=transform(probe['position_m'],basis);key=cell(p)
            uv=[probe['uv0'][0],1-probe['uv0'][1] if flip_v else probe['uv0'][1]]
            if not any(max(abs(a-b) for a,b in zip(p,q))<=tolerance and max(abs(a-b) for a,b in zip(uv,r))<=0.0002 for d in neighbors for q,r in native_uv.get(tuple(a+b for a,b in zip(key,d)),[])):
                passed=False;break
        if passed:uv_modes.append('v_one_minus_source' if flip_v else 'source_uv_unchanged')
    assert uv_modes,('native_uv0_probe_mismatch',part['name'])
    return {'source_xyz_to_native_xyz':basis,'units':'source_metres_to_native_centimetres','scale':100,
            'bounds_max_error_cm':error,'vertex_probe_count':len(part['sample_local_vertices_m']),
            'independently_unique_basis':independently_unique,'family_basis_used_to_disambiguate':not independently_unique,
            'uv0_probe_count':len(part['source_uv0_probes']),'uv0_matching_conventions':uv_modes,
            'native_assembly_translation_cm':transform(part['assembly_translation_m'],basis),
            'full_geometry_or_uv_equivalence':False}

def import_part(family,part,request_sha,state,expected_basis=None):
    receipt_path=HERE/'Receipts'/family['id']/(part['name']+'.json')
    dest=part['native_package']
    if receipt_path.is_file():
        receipt=read(receipt_path)
        assert receipt['source_sha256']==part['fbx_sha256'] and receipt['request_sha256']==request_sha
        for path,expected in receipt['saved_packages'].items():assert sha(C.package_file(path))==expected,('saved_package_changed',path)
        assert E.does_asset_exist(dest)
        if expected_basis is not None:assert receipt['basis_readback']['source_xyz_to_native_xyz']==expected_basis
        return receipt
    assert (not E.does_asset_exist(dest) and not C.package_file(dest).exists()) or dest in RESUME_REIMPORT,('unreceipted_existing_destination',dest)
    assert sha(part['fbx'])==part['fbx_sha256']
    progress={'part':part['name'],'family':family['id'],'pid':os.getpid(),'completed':False,'destination':dest,'request_sha256':request_sha}
    write(HERE/'NATIVE_PROGRESS.json',progress)
    created={};used=[]
    materials={k:material_for(family['materials'][k],created,used) for k in set(part['material_keys'])}
    opts=unreal.FbxImportUI()
    for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_mesh':True,'import_materials':False,'import_textures':False,'import_animations':False}.items():opts.set_editor_property(k,v)
    data=opts.get_editor_property('static_mesh_import_data')
    for k,v in {'combine_meshes':False,'auto_generate_collision':False,'import_mesh_lo_ds':False,'remove_degenerates':False,'generate_lightmap_u_vs':False,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,'transform_vertex_to_absolute':True,'bake_pivot_in_vertex':False,'import_uniform_scale':1.0,'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS}.items():data.set_editor_property(k,v)
    import_source=part.get('import_fbx',part['fbx'])
    assert sha(import_source)==part.get('import_fbx_sha256',part['fbx_sha256'])
    objects=resume_import_file(import_source,dest,opts,unreal.FbxFactory())
    assert len(objects)==1 and isinstance(objects[0],unreal.StaticMesh)
    mesh=objects[0];assert mesh.get_path_name().split('.')[0]==dest
    created[dest]=mesh
    measurement=N.measure(mesh)
    assert measurement['uv_channels']==len(part['uv_channels'])
    allowed={part['triangles']}
    if part.get('roundtrip_slot_triangle_counts') is not None:allowed.add(sum(part['roundtrip_slot_triangle_counts'].values()))
    assert measurement['triangles'] in allowed,('triangle_count_changed',part['name'],measurement['triangles'],allowed)
    basis=read_basis_and_uv(mesh,part,measurement,expected_basis)
    desc=mesh.get_static_mesh_description(0);groups=collections.Counter()
    for i in range(desc.get_triangle_count()):
        t=unreal.TriangleID();t.set_editor_property('id_value',i)
        groups[desc.get_triangle_polygon_group(t).id_value]+=1
    native_slots=[];mapped=[];used_source={int(i):n for i,n in part['slot_triangle_counts'].items()}
    if measurement['triangles']!=part['triangles']:
        used_source={int(i):n for i,n in part['roundtrip_slot_triangle_counts'].items()}
    sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for section in range(mesh.get_num_sections(0)):
        assert sub.get_lod_material_slot(mesh,0,section)==section,'nonidentity_section_material_mapping'
    for i,slot in enumerate(mesh.static_materials):
        name=str(slot.get_editor_property('imported_material_slot_name')) or str(slot.material_slot_name)
        candidates=[j for j,s in enumerate(part['source_material_slots']) if P.norm(name) in {P.norm(s),P.norm(s.split(':')[-1])}]
        assert len(candidates)==1,('ambiguous_material_slot',name,candidates)
        index=candidates[0];mapped.append(index)
        actual=groups.get(i,0);expected=used_source.get(index,0)
        assert actual==expected,('material_face_count_changed',part['name'],index,actual,expected)
        mat=materials[part['material_keys'][index]];mesh.set_material(i,mat)
        native_slots.append({'slot':i,'source_slot':index,'source_name':part['source_material_slots'][index],
                             'native_imported_name':name,'material_path':mat.get_path_name(),'triangles':actual,
                             'recipe_sha256':part['material_keys'][index]})
    assert len(set(mapped))==len(mapped) and set(used_source).issubset(mapped)
    for key,value in {'ModularDerivativeId':part['derivative_id'],'ModularParentAssetId':family['parent_asset_id'],
                      'ModularSourceSHA256':part['fbx_sha256'],'ModularSourceFamilySHA256':family['source_family_sha256'],
                      'BankExplicitHoldPreserved':str(family['explicit_hold']),'BankRightsState':family['rights_state']}.items():E.set_metadata_tag(mesh,key,value)
    dirty=N.dirty();assert set(dirty['maps'])==set(RESUME_BASELINE['maps']) and set(dirty['content']).issubset(set(created)|set(RESUME_BASELINE['content'])),('unexpected_dirty_packages',dirty)
    for path in sorted(set(created)-{dest}):assert E.save_asset(path,only_if_is_dirty=True)
    assert E.save_asset(dest,only_if_is_dirty=True)
    assert set(N.dirty()['maps'])==set(RESUME_BASELINE['maps']) and set(N.dirty()['content']).issubset(RESUME_BASELINE['content'])
    closure=N.dependency_closure(dest);assert not closure['missing'],closure
    saved={path:sha(C.package_file(path)) for path in created}
    for path in closure['packages']:
        if path.startswith('/Game/'):saved[path]=sha(C.package_file(path))
    for slot in native_slots:
        path=slot['material_path'].split('.')[0];saved[path]=sha(C.package_file(path))
    for key,mat in materials.items():
        material_path=mat.get_path_name().split('.')[0]
        material_packages=N.dependency_closure(material_path);assert not material_packages['missing']
        pins={path:sha(C.package_file(path)) for path in material_packages['packages'] if path.startswith('/Game/')}
        texture_properties=[]
        for texture in M.get_used_textures(mat):
            path=texture.get_path_name().split('.')[0];pins[path]=sha(C.package_file(path))
            texture_properties.append({'path':texture.get_path_name(),'srgb':texture.get_editor_property('srgb'),
                'compression':str(texture.get_editor_property('compression_settings')),'flip_green':texture.get_editor_property('flip_green_channel'),
                'filter':str(texture.get_editor_property('filter')),'address_x':str(texture.get_editor_property('address_x')),'address_y':str(texture.get_editor_property('address_y'))})
        saved.update(pins)
        material_receipt_path=HERE/'MaterialReceipts'/(key+'.json')
        material_receipt={'recipe_sha256':key,'material_path':mat.get_path_name(),'saved_packages':pins,
            'texture_properties':sorted(texture_properties,key=lambda t:t['path']),'two_sided':mat.get_editor_property('two_sided'),
            'instancing_usage':M.has_material_usage(mat,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES),
            'normal_strength':family['materials'][key]['normal']['strength'],'visual_fidelity_verified':False}
        assert material_receipt['instancing_usage']
        if material_receipt_path.is_file():assert read(material_receipt_path)==material_receipt,'material_readback_changed'
        else:write(material_receipt_path,material_receipt)
    receipt={'schema':'environmentpipeline.modular_native_part_readback.v1','request_sha256':request_sha,
             'derivative_id':part['derivative_id'],'family_id':family['family_id'],'parent_asset_id':family['parent_asset_id'],
             'source_family_sha256':family['source_family_sha256'],'name':part['name'],'kind':part['kind'],
             'source':part['fbx'],'source_sha256':part['fbx_sha256'],'native_object_path':mesh.get_path_name(),
             'import_source':import_source,'import_source_sha256':sha(import_source),
             'import_adaptation_receipt':part.get('import_adaptation_receipt'),
             'native_render_uv_channel':0,'source_render_uv_alignment':'SourceRenderUV matched against native UV0; original tolerance unchanged',
             'native_package':dest,'native_package_sha256':saved[dest],'measurement':N.measure(mesh),
             'basis_readback':basis,'material_slots':native_slots,'textures':used,'dependencies':closure,
             'saved_packages':saved,'named_saved':True,'native_reloaded':False,'fresh_process_reopened':False,
             'source_graph_components_transferred':True,'visual_fidelity_verified':False,'procedural_eligible':False,
             'collision_prepared':False,'additional_lods_prepared':False,'native_state':state}
    write(receipt_path,receipt)
    progress.update(completed=True,receipt=str(receipt_path));write(HERE/'NATIVE_PROGRESS.json',progress)
    return receipt

def run(request_path,request_sha,activation_path,family_id,max_parts=8):
    request,state=preflight(request_path,request_sha,activation_path)
    family=next(f for f in request['families'] if f['id']==family_id)
    assert family_id in read(activation_path)['family_ids']
    for path,expected in request['files'].items():assert sha(path)==expected,('input_changed',path)
    receipts=[];completed=0;expected_basis=None
    for part in family['parts']:
        receipt=HERE/'Receipts'/family_id/(part['name']+'.json')
        if not receipt.is_file() and completed>=max_parts:continue
        if not receipt.is_file():completed+=1
        receipt_value=import_part(family,part,request_sha,state,expected_basis)
        if expected_basis is None:expected_basis=receipt_value['basis_readback']['source_xyz_to_native_xyz']
        receipts.append(receipt_value)
    report={'schema':'environmentpipeline.modular_native_family_readback.v1','family_id':family['family_id'],
            'parent_asset_id':family['parent_asset_id'],'source_family_sha256':family['source_family_sha256'],
            'request_sha256':request_sha,'parts':receipts,'expected_part_count':len(family['parts']),
            'imported_part_count':len(receipts),'complete_native_import':len(receipts)==len(family['parts']),
            'native_reloaded':False,'fresh_process_reopened':False,'procedural_eligible':False,
            'visual_fidelity_verified':False,'holds_preserved':True,'state':state}
    bases={json.dumps(r['basis_readback']['source_xyz_to_native_xyz']) for r in receipts}
    assert len(bases)<=1,'inconsistent_family_basis'
    write(HERE/'Receipts'/family_id/'FAMILY.json',report)
    print(json.dumps({'family':family_id,'completed_this_call':completed,'imported':len(receipts),'expected':len(family['parts'])}))
    return report


# Resume-only boundary. Original import geometry/material/UV checks above are retained.
RESUME_BASELINE={'content':[], 'maps':[]}
RESUME_OWNED=set()
RESUME_REIMPORT=set()
RESUME_REQUEST=None
RESUME_BASES={}

def resume_import_file(filename,dest,options,factory):
    if dest not in RESUME_REIMPORT:
        return P.import_file(filename,dest,options,factory)
    assert not C.package_file(dest).exists() and dest in RESUME_OWNED
    task=unreal.AssetImportTask()
    for k,v in {'filename':str(filename),'destination_path':dest.rsplit('/',1)[0],
                'destination_name':dest.rsplit('/',1)[1],'automated':True,
                'replace_existing':True,'replace_existing_settings':True,'save':False,
                'options':options,'factory':factory}.items():task.set_editor_property(k,v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    result=list(task.get_objects());assert result,('import_returned_no_objects',filename)
    return result

def resume_boundary():
    activation=read(HERE/'RESUME_ACTIVATION_v004.json')
    assert activation['native_authorized_now'] and activation['assigned_editor_PID']==os.getpid()
    lease=[l for l in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if l.strip()][-1]
    import geocity_editor_action
    fields=geocity_editor_action.lease_fields(lease)
    assert fields.get('OWNER')=='CODEX_BANK_INTEGRATION'
    assert fields.get('operator_thread_id')==activation['operator_thread_id']
    assert fields.get('assigned_editor_PID')==str(os.getpid())
    assert fields.get('activation')=='MODULAR_NATIVE_RESUME_V004'
    assert fields.get('native_authorized_now')=='true'
    ids=json.loads(subprocess.check_output(['powershell','-NoProfile','-NonInteractive','-Command','ConvertTo-Json -Compress -InputObject @((Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Id)'],creationflags=subprocess.CREATE_NO_WINDOW,text=True))
    assert ids==[os.getpid()]
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
    assert world==activation['world']
    assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
    return activation,{'pid':os.getpid(),'world':world,'activation_sha256':sha(HERE/'RESUME_ACTIVATION_v004.json')}

def resume_initialize():
    global RESUME_REQUEST,RESUME_BASELINE
    activation,state=resume_boundary()
    RESUME_REQUEST=read(HERE/'NATIVE_IMPORT_REQUEST_v003.json')
    assert sha(HERE/'NATIVE_IMPORT_REQUEST_v003.json')==activation['request_sha256']
    for path,expected in RESUME_REQUEST['python_sources'].items():assert sha(path)==expected
    for module in (C,N,P,L,sys.modules[__name__]):L.verify_module(module,module.__file__)
    for path,expected in protected_files(activation['preservation_path']).items():assert sha(path)==expected,('protected_file_changed',path)
    before=N.dirty();RESUME_BASELINE=before
    previous=read(HERE/'USER_DEADLINE_STOP_2026-10-05.json')
    RESUME_OWNED.update(set(before['content']) & set(previous['dirty']['content']))
    # Only the exact failed, never-saved mesh may be reimported in place.
    RESUME_REIMPORT.add(NATIVE_ROOT+'/H0017/Modules/SM_H0017_Ground_SWCorner')
    reused=[];pins={}
    for family in RESUME_REQUEST['families']:
        for part in family['parts']:
            rp=HERE/'Receipts'/family['id']/(part['name']+'.json')
            if rp.is_file():
                r=read(rp);assert r['named_saved'] and r['source_sha256']==part['fbx_sha256']
                assert E.does_asset_exist(part['native_package'])
                pins.update(r['saved_packages']);reused.append(part['derivative_id'])
                RESUME_BASES[family['id']]=r['basis_readback']['source_xyz_to_native_xyz']
    assert len(reused)==34
    for path,expected in pins.items():assert sha(C.package_file(path))==expected
    write(HERE/'RESUME_BASELINE_v004.json',{'state':state,'dirty':before,'owned_partial_packages':sorted(RESUME_OWNED),'reused':reused,'preserved_saved_packages':pins})
    write(HERE/'RESUME_RESULT_v004.json',{'status':'RUNNING','reused_existing':reused,'imported_saved':[],'failed':[]})
    return {'reused':len(reused),'remaining':575,'preserved_dirty':before}

def resume_batch(max_parts=15):
    global RESUME_BASELINE
    activation,state=resume_boundary()
    assert RESUME_REQUEST is not None
    result=read(HERE/'RESUME_RESULT_v004.json')
    done=set(result['reused_existing'])|{r['id'] for r in result['imported_saved']}|{r['id'] for r in result['failed']}
    count=0
    for family in RESUME_REQUEST['families']:
        for part in family['parts']:
            if part['derivative_id'] in done:continue
            if count>=max_parts:break
            RESUME_BASELINE=N.dirty();count+=1
            try:
                r=import_part(family,part,activation['request_sha256'],state,RESUME_BASES.get(family['id']))
                RESUME_BASES[family['id']]=r['basis_readback']['source_xyz_to_native_xyz']
                result['imported_saved'].append({'id':part['derivative_id'],'family':family['id'],'name':part['name'],'native_package':part['native_package']})
            except Exception as exc:
                import traceback
                failure={'id':part['derivative_id'],'family':family['id'],'name':part['name'],'native_package':part['native_package'],
                         'error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'dirty_after':N.dirty()}
                result['failed'].append(failure)
                write(HERE/'RepairQueue'/family['id']/(part['name']+'.json'),failure)
            after=N.dirty()
            RESUME_OWNED.update(set(after['content'])-set(RESUME_BASELINE['content']))
            result['last_part']=part['name'];result['dirty_remaining']=after
            write(HERE/'RESUME_RESULT_v004.json',result)
        if count>=max_parts:break
    total=len(result['reused_existing'])+len(result['imported_saved'])+len(result['failed'])
    if total==609:
        baseline=read(HERE/'RESUME_BASELINE_v004.json')
        for path,expected in baseline['preserved_saved_packages'].items():assert sha(C.package_file(path))==expected
        result['status']='COMPLETE_WITH_REPAIR_QUEUE' if result['failed'] else 'COMPLETE'
        write(HERE/'RESUME_RESULT_v004.json',result)
    return {'status':result['status'],'imported_saved':len(result['imported_saved']),'reused_existing':len(result['reused_existing']),
            'failed':len(result['failed']),'remaining':609-total,'last_part':result.get('last_part'),'recent_errors':[f['error'] for f in result['failed'][-3:]]}
