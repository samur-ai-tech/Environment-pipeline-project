# Category-owned derivative of C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\BankIntegration_2026-10-04\import_prepared.py; source SHA256 35607f45bf049918ae303c98d9890d859525ec17c6ec7356ed9a4f9b86285777
"""Import selected prepared sources into permanent explicit bank paths, keeping holds."""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import unreal
import bank_contracts as C
import native_bank_ops as N

E=unreal.EditorAssetLibrary
M=unreal.MaterialEditingLibrary
SHARED='/Game/Project/Shared/ModelBank/Prepared/Dependencies'

def short(value):return hashlib.sha256(value.encode()).hexdigest()[:16]
def norm(value):return re.sub('[^A-Za-z0-9]','',value).lower()

def import_file(filename,dest,options=None,factory=None):
    assert not E.does_asset_exist(dest),'refuse_to_overwrite_existing_asset: '+dest
    task=unreal.AssetImportTask()
    for k,v in {'filename':str(filename),'destination_path':dest.rsplit('/',1)[0],
                'destination_name':dest.rsplit('/',1)[1],'automated':True,
                'replace_existing':False,'save':False}.items():task.set_editor_property(k,v)
    if options:task.set_editor_property('options',options)
    if factory:task.set_editor_property('factory',factory)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    results=list(task.get_objects())
    assert results,('import_returned_no_objects',filename)
    return results

def texture(ref,kind,created,used):
    file=Path(ref['path']);assert file.is_file(),str(file)
    source_sha=C.sha(file);dest=SHARED+'/Textures/T_'+source_sha[:20]+'_'+kind
    if E.does_asset_exist(dest):
        obj=unreal.load_asset(dest)
        assert E.get_metadata_tag(obj,'BankSourceSHA256')==source_sha,dest
        if dest in N.dirty()['content']:created[dest]=obj
    else:
        result=import_file(file,dest)
        assert len(result)==1 and isinstance(result[0],unreal.Texture2D)
        obj=result[0]
        obj.set_editor_property('srgb',kind=='color')
        if kind=='normal':
            obj.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
            obj.set_editor_property('flip_green_channel',True)
        elif kind=='data':obj.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
        E.set_metadata_tag(obj,'BankSourceSHA256',source_sha)
        E.set_metadata_tag(obj,'BankOriginalFile',str(file))
        created[dest]=obj
    used.append({'source':str(file),'source_sha256':source_sha,'native_path':obj.get_path_name(),'kind':kind})
    return obj

def scalar(material,value,prop):
    n=M.create_material_expression(material,unreal.MaterialExpressionConstant)
    n.set_editor_property('r',float(value));assert M.connect_material_property(n,'',prop)

def vector(material,value,prop):
    n=M.create_material_expression(material,unreal.MaterialExpressionConstant3Vector)
    n.set_editor_property('constant',unreal.LinearColor(*list(value)[:3],1.0))
    assert M.connect_material_property(n,'',prop)

def sample(material,obj,ref,kind):
    node=M.create_material_expression(material,unreal.MaterialExpressionTextureSample)
    node.set_editor_property('texture',obj)
    node.set_editor_property('sampler_type',{'normal':unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,'data':unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,'color':unreal.MaterialSamplerType.SAMPLERTYPE_COLOR}[kind])
    scale=ref.get('uv_scale') or [1,1];offset=ref.get('uv_offset') or [0,0]
    uv=M.create_material_expression(material,unreal.MaterialExpressionTextureCoordinate)
    uv.set_editor_property('u_tiling',float(scale[0]));uv.set_editor_property('v_tiling',float(scale[1]))
    if offset!=[0,0]:
        off=M.create_material_expression(material,unreal.MaterialExpressionConstant2Vector)
        off.set_editor_property('r',float(offset[0]));off.set_editor_property('g',float(offset[1]))
        add=M.create_material_expression(material,unreal.MaterialExpressionAdd)
        assert M.connect_material_expressions(uv,'',add,'A') and M.connect_material_expressions(off,'',add,'B')
        uv=add
    assert 'UVs' in M.get_material_expression_input_names(node)
    assert M.connect_material_expressions(uv,'',node,'UVs')
    return node

def material_for(job,recipe,created,used):
    name=recipe['source_material'];refs={r['channel']:r for r in job['textures'] if r['material']==name}
    config={'recipe':recipe,'textures':refs,'native_normal_green_flipped':True,'native_mask_clip':0.333}
    key=short(json.dumps(config,sort_keys=True));dest=SHARED+'/Materials/M_'+key
    recipe_sha=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    if E.does_asset_exist(dest):
        mat=unreal.load_asset(dest)
        assert E.get_metadata_tag(mat,'BankRecipeSHA256')==recipe_sha,'preexisting_material_recipe_mismatch'
        if E.get_metadata_tag(mat,'BankRecipeComplete')=='true':
            if dest in N.dirty()['content']:created[dest]=mat
            for ref in refs.values():
                kind='normal' if ref['channel']=='Normal' else 'data' if ref['channel'].startswith('ORM') else 'color'
                texture(ref,kind,created,used)
            return mat
        assert not C.package_file(dest).exists(),'incomplete_material_already_saved_requires_review'
        M.delete_all_material_expressions(mat)
    else:
        mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(dest.rsplit('/',1)[1],dest.rsplit('/',1)[0],unreal.Material,unreal.MaterialFactoryNew())
    assert mat
    E.set_metadata_tag(mat,'BankRecipeSHA256',recipe_sha)
    E.set_metadata_tag(mat,'BankRecipeComplete','false')
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    mat.set_editor_property('automatically_set_usage_in_editor',False)
    mat.set_editor_property('two_sided',not recipe['backface_culling'])
    p=recipe['principled_inputs'];masked=bool(p['Alpha']['links'])
    if masked:
        assert p['Alpha']['links'][0]['output']=='Alpha','unsupported_alpha_graph'
        mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED)
        mat.set_editor_property('opacity_mask_clip_value',0.333)
    if 'BaseColor' in refs:
        node=sample(mat,texture(refs['BaseColor'],'color',created,used),refs['BaseColor'],'color')
        assert M.connect_material_property(node,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
        if masked:assert M.connect_material_property(node,'A',unreal.MaterialProperty.MP_OPACITY_MASK)
    else:
        assert not p['Base Color']['links'],'unresolved_base_color_link'
        vector(mat,p['Base Color']['default'],unreal.MaterialProperty.MP_BASE_COLOR)
    if 'Normal' in refs:
        node=sample(mat,texture(refs['Normal'],'normal',created,used),refs['Normal'],'normal')
        assert M.connect_material_property(node,'RGB',unreal.MaterialProperty.MP_NORMAL)
    orm='ORM_R_AO_G_Roughness_B_Metallic'
    if orm in refs:
        node=sample(mat,texture(refs[orm],'data',created,used),refs[orm],'data')
        for channel,prop in [('R',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),('G',unreal.MaterialProperty.MP_ROUGHNESS),('B',unreal.MaterialProperty.MP_METALLIC)]:
            assert M.connect_material_property(node,channel,prop)
    else:
        for name,prop in [('Roughness',unreal.MaterialProperty.MP_ROUGHNESS),('Metallic',unreal.MaterialProperty.MP_METALLIC)]:
            assert not p[name]['links'],'unsupported_parameter_graph: '+name
            scalar(mat,p[name]['default'],prop)
    emission=float(p['Emission Strength']['default'])
    if emission>0:
        if 'Emission' in refs:
            node=sample(mat,texture(refs['Emission'],'color',created,used),refs['Emission'],'color')
            mul=M.create_material_expression(mat,unreal.MaterialExpressionMultiply);mul.set_editor_property('const_b',emission)
            assert M.connect_material_expressions(node,'RGB',mul,'A') and M.connect_material_property(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        else:vector(mat,[v*emission for v in p['Emission Color']['default'][:3]],unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    E.set_metadata_tag(mat,'BankRecipeComplete','true')
    M.layout_material_expressions(mat);M.recompile_material(mat)
    created[dest]=mat
    return mat

def import_one(asset_id):
    assert asset_id in {"external.H0017", "external.H0018", "external.H0019", "external.H0020", "external.H0021"}, "whole_authored_family_scope"
    before=N.preflight()
    jobs={j['asset_id']:j for j in C.read(C.HERE/'EXTERNAL_IMPORT_QUEUE.json')};job=jobs[asset_id]
    rec=next(r for r in C.read(C.HERE/'EXTERNAL_MATERIAL_RECIPES.json') if r['asset_id']==asset_id)
    source=C.read(job['original_source_receipt'])
    assert C.sha(job['prepared_blend'])==rec['prepared_blend_sha256']
    fbx=job['source_fbx']
    if asset_id=='external.H0633':fbx=C.read(C.PREP/'MATERIAL_REPAIR.json')['prepared_fbx']
    else:assert C.sha(fbx)==job['sha256']
    override_file=C.HERE/'IMPORT_SOURCE_OVERRIDES.json'
    override=C.read(override_file).get(asset_id) if override_file.exists() else None
    if override:
        assert C.sha(override['fbx'])==override['sha256'] and C.sha(job['prepared_blend'])==override['prepared_blend_sha256']
        fbx=override['fbx']
    report_path=C.HERE/('IMPORTED_'+asset_id.replace('.','_')+'.json')
    dest=job['destination_package_proposed']
    if report_path.exists():
        prior=C.read(report_path)
        if prior.get('saved'):
            assert C.sha(C.package_file(prior['native_path']))==prior['native_sha256'],'saved_import_changed'
            return prior
    resume_mesh=None
    if E.does_asset_exist(dest):
        pending=C.HERE/('IMPORT_PENDING_'+asset_id.replace('.','_')+'.json')
        progress=C.read(pending) if pending.exists() else C.read(C.HERE/'NATIVE_IMPORT_PROGRESS.json')
        assert progress['asset_id']==asset_id and progress['pid']==os.getpid() and progress['destination']==dest
        assert not progress['completed'] and not C.package_file(dest).exists(),'preexisting_saved_destination_without_this_task_receipt'
        resume_mesh=unreal.load_asset(dest)
        assert isinstance(resume_mesh,unreal.StaticMesh)
        assert Path(resume_mesh.get_editor_property('asset_import_data').get_first_filename()).resolve()==Path(fbx).resolve(),'partial_import_source_mismatch'
    C.write(C.HERE/'NATIVE_IMPORT_PROGRESS.json',{'asset_id':asset_id,'pid':os.getpid(),
        'started_utc':datetime.now(timezone.utc).isoformat(),'phase':'creating_materials_and_importing',
        'destination':dest,'completed':False})
    created={};used=[]
    slots=[material_for(job,m,created,used) for m in rec['materials']]
    # Preserve every prepared dependency, including unsupported source-only channels.
    for ref in job['textures']:
        if ref['channel'].startswith('SourceOnly:') or ref['channel']=='Emission':
            texture(ref,'color' if ref['channel']=='Emission' else 'data',created,used)
    opts=unreal.FbxImportUI()
    for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,
                'import_as_skeletal':False,'import_mesh':True,'import_materials':False,'import_textures':False,'import_animations':False}.items():opts.set_editor_property(k,v)
    data=opts.get_editor_property('static_mesh_import_data')
    for k,v in {'combine_meshes':bool(job.get('category_combine_meshes', False)),'auto_generate_collision':False,'import_mesh_lo_ds':True,'remove_degenerates':False,
                'generate_lightmap_u_vs':False,'convert_scene':True,'convert_scene_unit':True,
                'force_front_x_axis':False,'transform_vertex_to_absolute':True,'bake_pivot_in_vertex':False,
                'import_uniform_scale':1.0,'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS}.items():data.set_editor_property(k,v)
    objects=[resume_mesh] if resume_mesh else import_file(fbx,dest,opts,unreal.FbxFactory())
    meshes=[o for o in objects if isinstance(o,unreal.StaticMesh)]
    assert len(meshes)==1,('unexpected_multiple_meshes',asset_id,[o.get_path_name() for o in objects])
    mesh=meshes[0];assert mesh.get_path_name().split('.')[0]==dest,'native_import_destination_differs'
    measurement=N.measure(mesh)
    actual=measurement['dimensions_cm'];expected=[100*v for v in job['source_dimensions_m']]
    z_error=abs(actual[2]-expected[2]);xy_error=max(abs(a-b) for a,b in zip(sorted(actual[:2]),sorted(expected[:2])))
    assert z_error<=max(0.05,expected[2]*0.0002) and xy_error<=max(0.05,max(expected[:2])*0.0002),('native_units_or_axes_mismatch',actual,expected)
    geometry_equivalence=None
    if measurement['triangles']!=source['triangles']:
        proof_path=C.HERE/'IMPORT_GEOMETRY_EQUIVALENCE.json'
        geometry_equivalence=C.read(proof_path).get(asset_id) if proof_path.exists() else None
        assert geometry_equivalence and geometry_equivalence['passed'],('triangle_count_differs',measurement['triangles'],source['triangles'])
        proof=geometry_equivalence['objects']
        assert len(proof)==1 and proof[0]['native_path']==mesh.get_path_name()
        assert proof[0]['native_triangles']==measurement['triangles'] and proof[0]['source_triangles']==source['triangles']
        assert source['triangles']-measurement['triangles']==proof[0]['source_zero_area_triangles']-proof[0]['native_zero_area_triangles']
    expected_names=[m['source_material'] for m in rec['materials']]
    slot_usage=C.read(C.HERE/'SOURCE_IMPORT_SLOT_USAGE.json')[asset_id]
    assert slot_usage['sha256']==rec['prepared_blend_sha256']
    mapped_indices=[];native_slots=[]
    desc=mesh.get_static_mesh_description(0)
    native_group_counts={}
    for tri_id in range(desc.get_triangle_count()):
        tri=unreal.TriangleID(tri_id)
        assert desc.is_triangle_valid(tri),'unexpected_sparse_triangle_ids'
        group=desc.get_triangle_polygon_group(tri).get_editor_property('id_value')
        native_group_counts[group]=native_group_counts.get(group,0)+1
    for i,native in enumerate(mesh.static_materials):
        actual_name=str(native.get_editor_property('imported_material_slot_name')) or str(native.material_slot_name)
        matches=[index for index,recipe in enumerate(rec['materials']) if norm(actual_name) in {norm(recipe['source_material']),norm(recipe['prepared_material_name']),norm(recipe['source_material']+'.001'),norm(recipe['prepared_material_name'].rsplit(':',1)[-1])}]
        assert len(matches)==1,('ambiguous_native_material_slot',i,actual_name,matches)
        index=matches[0]
        # The exact source proof binds every used material to triangulated faces.
        alias_proof=C.read(C.HERE/'WHOLE_SOURCE_MATERIAL_PROOFS.json')[asset_id]
        assert alias_proof['prepared_blend_sha256']==rec['prepared_blend_sha256']
        assert alias_proof['source_fbx_sha256']==C.sha(fbx)
        expected_triangles=alias_proof['material_triangles'][rec['materials'][index]['prepared_material_name']]
        sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        assert sub.get_lod_material_slot(mesh,0,i)==i,'non_identity_section_slot_requires_explicit_adapter'
        actual_triangles=native_group_counts.get(i,0)
        assert actual_triangles==expected_triangles,('source_native_material_section_differs',asset_id,i,actual_triangles,expected_triangles)
        material=slots[index];mapped_indices.append(index);native_slots.append(material)
        mesh.set_material(i,material)
    assert set(slot_usage['used_slots']).issubset(mapped_indices),'native_material_slots_lost_used_source_faces'
    E.set_metadata_tag(mesh,'BankAssetId',asset_id)
    E.set_metadata_tag(mesh,'BankOriginalSource',job['source_fbx'])
    E.set_metadata_tag(mesh,'BankPreparedSource',job['prepared_blend'])
    E.set_metadata_tag(mesh,'BankExplicitHoldPreserved',str(job['original_explicit_hold']))
    E.set_metadata_tag(mesh,'BankRightsState',source['rights_state'])
    created[dest]=mesh
    for path in sorted(created):assert E.save_asset(path,only_if_is_dirty=True),path
    measurement=N.measure(mesh)
    closure=N.dependency_closure(dest);assert not closure['missing'],closure
    report={'asset_id':asset_id,'native_path':mesh.get_path_name(),'native_sha256':C.sha(C.package_file(mesh.get_path_name())),
        'import_fbx':str(fbx),'import_fbx_sha256':C.sha(fbx),'original_fbx':job['source_fbx'],'original_fbx_sha256':job['sha256'],
        'prepared_blend':job['prepared_blend'],'prepared_blend_sha256':rec['prepared_blend_sha256'],
        'measurement':measurement,'source_dimensions_m':job['source_dimensions_m'],'axis_readback':'native_Z_equals_source_Z_horizontal_axes_permitted_swap',
        'dimension_error_cm':{'z':z_error,'horizontal_max':xy_error},'dependencies':closure,'textures':used,
        'material_slot_sources':[expected_names[i] for i in mapped_indices],'native_material_slots':[m.get_path_name() for m in native_slots],
        'source_slot_usage':slot_usage,'native_to_source_slot_indices':mapped_indices,
        'saved_paths':sorted(created),'saved':True,'catalog_connected':False,'enabled':False,
        'hold_preserved':job['original_explicit_hold'],'hold_reasons_preserved':job['hold_reasons_preserved'],
        'visual_acceptance':False,'source_only_shader_behavior':'SourceOnly textures preserved as dependencies; source custom shader behavior is not claimed reproduced.',
        'geometry_remodeled':False,'source_export_override':override,'geometry_equivalence':geometry_equivalence,'scene_saved':False}
    C.write(report_path,report)
    assert dirty_safe(before),N.dirty()
    C.write(C.HERE/'NATIVE_IMPORT_PROGRESS.json',{'asset_id':asset_id,'pid':os.getpid(),
        'completed_utc':datetime.now(timezone.utc).isoformat(),'phase':'named_saved',
        'destination':dest,'completed':True,'receipt':str(report_path)})
    print(json.dumps({'asset_id':asset_id,'imported_and_saved':mesh.get_path_name(),'saved_packages':len(created),'enabled':False}))
    return report

def dirty_safe(before):
    after=N.dirty()
    return after['maps']==before['dirty']['maps'] and set(after['content']).issubset(set(before['dirty']['content']))
