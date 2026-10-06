"""Bounded read-only native geometry/material evidence for existing Iran candidates.

Raw triangle occupancy and UVs support category-owner functional measurement;
no functional front/aperture/material suitability is inferred from a name/AABB.
"""
from pathlib import Path
from . import intake as I
from . import authority as A
from . import integrity as V

REQUIREMENTS=I.ROOT/'Staging/IranBuildingAdaptation_2026-10-04/ConsumerIntegration/PER_BUILDING_REQUIREMENTS.json'
SELECTED={
 'NU_bec0553f5648e25ec0e6':'warehouse_loading_opening',
 'NU_a083b80710f2f1964814':'warehouse_loading_opening',
 'NU_2a042d4f85289d403ec7':'station_entrance',
 'NU_0de70e66afd34c0b6301':'station_entrance',
 'NU_0578953dbe96b3a1eebb':'station_entrance',
 'NU_39235413a24a9b050a5b':'station_entrance_leaf',
 'NU_d62b1ba0a2e59d93a97c':'station_entrance_leaf',
 'NU_8c80be71172f994d4600':'station_entrance_leaf',
 'NU_c247d726647fbd09e57e':'station_entrance_leaf',
 'NU_1518ec1a321c3a7b6c76':'station_glazing',
 'NU_dde2c58b9c163d6170b4':'station_glazing',
 'NU_d0a1054a5956fbda1c70':'industrial_facade_material',
 'NU_eb7ab02a131aaa339199':'industrial_facade_material',
 'NU_3634d948d49c75552804':'neutral_facade_material',
}


def build():
    m,mp=A.manifest();requirements=I.read(REQUIREMENTS);q=I.read(I.HERE/'READY_JOBS.json');byid={j['job_id']:j for j in q['jobs']}
    jobs=[]
    for jid,role in SELECTED.items():
        j=byid[jid];assert j['source_id']=='Current' and j['operation']=='reference_existing'
        assert I.sha(j['source_file'])==j['source_sha256']
        jobs.append({'job_id':jid,'asset_id':j['asset_id'],'object_path':j['native_object_path'],'package_sha256':j['source_sha256'],
            'candidate_role':role,'role_is_search_hypothesis':True,'source_style':j['source_style'],'rights_state':j['rights_state'],
            'capture':'native_triangle_positions_uvs_groups_and_material_graph' if 'material' not in role else 'material_graph_shader_parameters_texture_dependencies',
            'qualification_required':['functional front/up/contact frame','clear aperture in that frame','frame leaf glazing triangle occupancy and motion clearance',
                'native unit scale depth <=56cm and feature-specific height','physical UV/tiling and material shader review','industrial or neutral use/style visual review','rights and selection scope'],
            'approved_for_selection':False})
    report={'schema':'environmentpipeline.targeted_native_measurement_jobs.v1','authority':m['authority'],
        'command_manifest_path':str(mp),'command_manifest_sha256':I.sha(mp),'requirements_path':str(REQUIREMENTS),
        'requirements_sha256':I.sha(REQUIREMENTS),'queue_sha256':I.sha(I.HERE/'READY_JOBS.json'),
        'job_ids':list(SELECTED),'jobs':jobs,'feature_limits':[{'source_osm_id':f['source_osm_id'],'canonical_use':f['canonical_use'],
            'geometry_limits':f['geometry_limits'],'required_roles':f['required_supplier_roles']} for f in requirements['features'] if f['source_status']=='retained'],
        'preserved_rejections':requirements['known_candidate_limits'],'unqualified_existing_measurements_reused':I.read(I.HERE/'ADOPTED_NATIVE_EVIDENCE.json')['job_ids'],
        'full_existing_queue_inspected_count':len(q['jobs']),'no_new_inventory_or_source_request':True,
        'ordinary_generation_authorized':False,'native_execution_performed':False,
        'followup':'Bank executes inspect with this measurement_request_path and exact activation SHA, then supplies reviewed functional frame/triangle labels; raw samples alone do not qualify use.'}
    p=I.HERE/'TargetedJobs'/V.digest(report)/'REQUEST.json';A.immutable_json(p,report)
    I.write('TARGETED_MEASUREMENT_JOBS.json',{'path':str(p),'sha256':I.sha(p),'job_ids':list(SELECTED)})
    return report


def validate_request(path,job_ids,activation):
    p=Path(path).resolve();assert p.is_relative_to(I.HERE/'TargetedJobs');r=I.read(p)
    assert V.digest(r)==p.parent.name and activation['measurement_request_sha256']==I.sha(p)
    assert r['authority']==A.authority() and set(r['job_ids'])==set(job_ids)
    assert I.sha(REQUIREMENTS)==r['requirements_sha256'] and I.sha(I.HERE/'READY_JOBS.json')==r['queue_sha256']
    return r


def material_graph(material):
    import unreal
    L=unreal.MaterialEditingLibrary;leaf=material;parents=[]
    while isinstance(material,unreal.MaterialInstanceConstant):
        assert material.get_path_name() not in parents,'material_parent_cycle'
        parents.append(material.get_path_name());material=material.get_editor_property('parent');assert material
    assert isinstance(material,unreal.Material)
    parameters={}
    for name in L.get_scalar_parameter_names(leaf):
        parameters[str(name)]=float(L.get_material_instance_scalar_parameter_value(leaf,name) if isinstance(leaf,unreal.MaterialInstanceConstant)
            else L.get_material_default_scalar_parameter_value(leaf,name))
    roots={};todo=[]
    for prop in ('MP_BASE_COLOR','MP_NORMAL','MP_OPACITY','MP_OPACITY_MASK','MP_ROUGHNESS','MP_METALLIC'):
        n=L.get_material_property_input_node(material,getattr(unreal.MaterialProperty,prop));roots[prop]=n.get_path_name() if n else None
        if n:todo.append(n)
    nodes={}
    # Function calls remain explicit graph boundaries requiring owner review.
    fields={'MaterialExpressionTextureCoordinate':['coordinate_index','u_tiling','v_tiling'],
        'MaterialExpressionScalarParameter':['parameter_name','default_value'],
        'MaterialExpressionConstant':['r'],'MaterialExpressionMultiply':['const_a','const_b'],
        'MaterialExpressionTextureSample':['texture','const_coordinate'],
        'MaterialExpressionTextureSampleParameter2D':['texture','parameter_name'],
        'MaterialExpressionMaterialFunctionCall':['material_function']}
    while todo:
        node=todo.pop();key=node.get_path_name()
        if key in nodes:continue
        assert len(nodes)<4096,'material_graph_limit_requires_review'
        cls=node.get_class().get_name();inputs=list(L.get_inputs_for_material_expression(material,node));values={}
        for field in fields.get(cls,[]):
            try:
                v=node.get_editor_property(field)
                values[field]=v.get_path_name() if hasattr(v,'get_path_name') else v if isinstance(v,(str,int,float,bool,type(None))) else str(v)
            except Exception as exc:values[field]={'unavailable':str(exc)}
        nodes[key]={'class':cls,'inputs':[x.get_path_name() if x else None for x in inputs],'values':values}
        todo.extend(x for x in inputs if x is not None)
    return {'path':leaf.get_path_name(),'base_material':material.get_path_name(),'parent_chain':parents,
        'base_blend_mode':str(material.get_editor_property('blend_mode')),'base_two_sided':bool(material.get_editor_property('two_sided')),
        'instance_base_property_overrides':str(leaf.get_editor_property('base_property_overrides')) if isinstance(leaf,unreal.MaterialInstanceConstant) else None,
        'scalar_parameters':parameters,'root_nodes':roots,'nodes':nodes,'physical_tiling_verified':False,
        'opaque_facade_use_qualified':False,'unknowns':['function internals and shader paths require category review','physical UV scale requires surface and graph review','appearance/use/rights not qualified']}


def capture(asset):
    import unreal
    if isinstance(asset,(unreal.Material,unreal.MaterialInstanceConstant)):
        return {'material_graph':material_graph(asset)}
    assert isinstance(asset,unreal.StaticMesh)
    desc=asset.get_static_mesh_description(0);assert desc
    uv_count=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_num_uv_channels(asset,0)
    triangles=[]
    for idx in range(desc.get_triangle_count()):
        tid=unreal.TriangleID(idx);assert desc.is_triangle_valid(tid),'sparse_triangles_require_supported_iteration'
        corners=[]
        for k in range(3):
            vi=desc.get_triangle_vertex_instance(tid,k);vid=desc.get_vertex_instance_vertex(vi);p=desc.get_vertex_position(vid)
            uvs=[]
            for channel in range(uv_count):
                uv=desc.get_vertex_instance_uv(vi,channel);uvs.append([uv.x,uv.y])
            corners.append({'position_cm':[p.x,p.y,p.z],'uv_channels':uvs})
        group=desc.get_triangle_polygon_group(tid)
        triangles.append({'triangle_id':idx,'polygon_group_id':int(group.get_editor_property('id_value')),'corners':corners})
    return {'lod':0,'triangles':triangles,'material_slots':[{'slot':i,'imported_name':str(s.get_editor_property('imported_material_slot_name')),
        'material_graph':material_graph(s.material_interface) if s.material_interface else None} for i,s in enumerate(asset.static_materials)],
        'authored_origin_cm':[0,0,0],'native_up_axis':'Z','native_scale':[1,1,1],
        'functional_front_axis':None,'functional_contact_anchor':None,'clear_aperture_cm':None,
        'occupancy_labels':None,'movement_clearance_cm':None,
        'review_required':'Category owner must bind front/contact and frame/leaf/glazing labels to triangle IDs, measure clear aperture and verify motion clearance. Polygon group index is not silently assumed to equal material slot index.'}
