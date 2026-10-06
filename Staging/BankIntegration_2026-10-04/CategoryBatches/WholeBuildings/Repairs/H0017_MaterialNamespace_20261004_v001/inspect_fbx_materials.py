"""Read exact original FBX material/model/geometry links and prepared face usage.

Blender background only: no render, export, save, geometry editing or native call.
This separate repair does not import or change any frozen category helper.
"""
import collections
import hashlib
import json
from pathlib import Path
import bpy
from io_scene_fbx import parse_fbx

HERE=Path(__file__).resolve().parent
CATEGORY=HERE.parents[1]
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(name,value):
    path=HERE/name
    if path.exists():assert read(path)==value,('immutable_repair_receipt_collision',str(path))
    else:path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def child(element,name):return next((v for v in element.elems if v.id==name),None)
def text(value):return value.decode('utf-8') if isinstance(value,bytes) else str(value)
def object_name(raw):
    # Binary FBX class suffix is format metadata, retained separately below.
    return text(raw).split('\x00\x01')[0]

queue=read(CATEGORY/'EXTERNAL_IMPORT_QUEUE.json')
recipes={v['asset_id']:v for v in read(CATEGORY/'EXTERNAL_MATERIAL_RECIPES.json')}
result=[];failures=[]
for job in queue:
    aid=job['asset_id'];fbx=Path(job['source_fbx']);blend=Path(job['prepared_blend'])
    fbx_sha=sha(fbx);blend_sha=sha(blend)
    assert fbx_sha==job['sha256'] and blend_sha==recipes[aid]['prepared_blend_sha256']
    try:
        tree,version=parse_fbx.parse(str(fbx))
        objs=child(tree,b'Objects');connections=child(tree,b'Connections')
        assert objs is not None and connections is not None
        elements={int(v.props[0]):v for v in objs.elems if v.id in {b'Material',b'Model',b'Geometry'}}
        materials={uid:{'fbx_material_id':uid,'raw_name':text(v.props[1]),'material_name':object_name(v.props[1])}
                   for uid,v in elements.items() if v.id==b'Material'}
        models={uid:{'fbx_model_id':uid,'raw_name':text(v.props[1]),'model_name':object_name(v.props[1])}
                for uid,v in elements.items() if v.id==b'Model'}
        links=[]
        for conn in connections.elems:
            if conn.id==b'C' and len(conn.props)>=3 and conn.props[0]==b'OO':
                links.append((int(conn.props[1]),int(conn.props[2])))
        geometry_links=collections.defaultdict(list);material_links=collections.defaultdict(list)
        for source,target in links:
            if source in elements and elements[source].id==b'Geometry' and target in models:geometry_links[target].append(source)
            if source in materials and target in models:material_links[target].append(source)
        raw_objects=[];raw_usage=collections.Counter()
        for model_id,model in models.items():
            for geometry_id in geometry_links[model_id]:
                geometry=elements[geometry_id]
                polygons=child(geometry,b'PolygonVertexIndex')
                if polygons is None:continue
                layers=[v for v in geometry.elems if v.id==b'LayerElementMaterial']
                assert len(layers)==1,('ambiguous_material_layer',aid,model['model_name'],len(layers))
                layer=layers[0];mode=text(child(layer,b'MappingInformationType').props[0]);reference=text(child(layer,b'ReferenceInformationType').props[0])
                indices=list(child(layer,b'Materials').props[0]);assigned=material_links[model_id]
                assert mode in ['ByPolygon','AllSame'] and reference in ['IndexToDirect','Direct'],(aid,model['model_name'],mode,reference)
                sizes=[];size=0
                for index in polygons.props[0]:
                    size+=1
                    if index<0:sizes.append(size);size=0
                assert size==0 and all(n>=3 for n in sizes)
                assert (mode=='AllSame' and len(indices)==1) or (mode=='ByPolygon' and len(indices)==len(sizes))
                counts=collections.Counter();faces=collections.Counter()
                for face,size in enumerate(sizes):
                    slot=indices[0] if mode=='AllSame' else indices[face]
                    assert 0<=slot<len(assigned),(aid,model['model_name'],'material_index_not_connected',slot)
                    mid=assigned[slot];counts[mid]+=size-2;faces[mid]+=1
                for mid,count in counts.items():raw_usage[mid]+=count
                raw_objects.append({**model,'fbx_geometry_id':geometry_id,'geometry_name':object_name(geometry.props[1]),
                    'mapping':mode,'reference':reference,'connected_material_ids_in_source_order':assigned,
                    'materials':[{'source_object_slot':i,**materials[mid],'source_polygon_count':faces[mid],
                                  'triangles_from_original_polygon_sizes':counts[mid]} for i,mid in enumerate(assigned)],
                    'source_polygon_count':len(sizes),'triangles_from_original_polygon_sizes':sum(counts.values())})
        bpy.ops.wm.open_mainfile(filepath=str(blend),load_ui=False,use_scripts=False)
        primary={v['name']:v for v in job['category_object_members'] if v['primary_render']}
        assert {v['model_name'] for v in raw_objects}==set(primary),(aid,'fbx_prepared_component_membership_differs')
        source_to_recipe={v['source_material']:v['slot'] for v in recipes[aid]['materials']}
        raw_names={v['material_name']:v['fbx_material_id'] for v in materials.values()}
        assert len(raw_names)==len(materials),'duplicate_exact_fbx_material_name'
        expected_by_recipe=collections.Counter();prepared_objects=[]
        for name,original in primary.items():
            obj=bpy.data.objects.get(name);assert obj and obj.type=='MESH'
            assert len(obj.material_slots)==len(original['material_slots'])
            obj.data.calc_loop_triangles()
            usage=collections.Counter(t.material_index for t in obj.data.loop_triangles)
            fbx_object=next(v for v in raw_objects if v['model_name']==name)
            prepared=[]
            for slot,source_name in enumerate(original['material_slots']):
                assert source_name in raw_names and source_name in source_to_recipe,(aid,name,source_name,'missing_exact_source_material_identity')
                mid=raw_names[source_name];linked=next((m for m in fbx_object['materials'] if m['fbx_material_id']==mid),None)
                assert linked is not None,(aid,name,source_name,'material_not_connected_to_original_fbx_model')
                triangles=usage[slot]
                assert linked['triangles_from_original_polygon_sizes']==triangles,(aid,name,source_name,'fbx_prepared_material_triangle_usage_differs',linked['triangles_from_original_polygon_sizes'],triangles)
                recipe_slot=source_to_recipe[source_name];expected_by_recipe[recipe_slot]+=triangles
                prepared.append({'prepared_object_slot':slot,'source_material':source_name,'fbx_material_id':mid,
                    'recipe_slot':recipe_slot,'source_triangles':triangles,'source_polygons':sum(p.material_index==slot for p in obj.data.polygons)})
            prepared_objects.append({'object':name,'fbx_model_id':fbx_object['fbx_model_id'],'fbx_geometry_id':fbx_object['fbx_geometry_id'],'materials':prepared})
        aliases=[];alias_targets=collections.defaultdict(set)
        for material in recipes[aid]['materials']:
            name=material['source_material'];mid=raw_names[name]
            # This produces explicit per-ID candidate aliases. Runtime code must
            # consume this collision-checked table, never strip arbitrary names.
            leaf=name.rsplit(':',1)[-1]
            accepted=[name] if leaf==name else [name,leaf]
            for alias in accepted:alias_targets[alias].add(material['slot'])
            aliases.append({'recipe_slot':material['slot'],'source_material':name,'fbx_material_id':mid,
                'raw_fbx_material_name':materials[mid]['raw_name'],'explicit_imported_name_aliases':accepted,
                'source_triangles':expected_by_recipe[material['slot']],
                'source_object_memberships':[{'object':v['object'],'fbx_model_id':v['fbx_model_id'],'fbx_geometry_id':v['fbx_geometry_id'],
                    'source_triangles':m['source_triangles']} for v in prepared_objects for m in v['materials'] if m['recipe_slot']==material['slot']]})
        collisions={alias:sorted(targets) for alias,targets in alias_targets.items() if len(targets)>1}
        assert not collisions,('explicit_alias_collision',aid,collisions)
        source=read(job['original_source_receipt'])
        total=sum(expected_by_recipe.values());assert total==source['triangles']
        result.append({'asset_id':aid,'original_fbx':str(fbx),'original_fbx_sha256':fbx_sha,'fbx_version':version,
            'prepared_blend':str(blend),'prepared_blend_sha256':blend_sha,'original_source_receipt_sha256':sha(job['original_source_receipt']),
            'destination':job['destination_package_proposed'],'source_component_names':sorted(primary),
            'raw_fbx_objects':raw_objects,'prepared_component_material_usage':prepared_objects,
            'material_aliases':aliases,'alias_collisions':collisions,'triangles_total':total,
            'fbx_prepared_per_material_triangle_usage_agrees':True,'geometry_uv_transform_or_material_graph_edited':False})
        print('EXACT_FBX_MATERIAL_PROOF',aid,total,len(aliases),flush=True)
    except Exception as error:
        failures.append({'asset_id':aid,'error':str(error)})
        print('EXACT_FBX_MATERIAL_BLOCKED',aid,str(error),flush=True)
    finally:
        assert sha(fbx)==fbx_sha and sha(blend)==blend_sha,('source_modified',aid)
write('SOURCE_MATERIAL_ALIAS_PROOF.json',{'schema':'environmentpipeline.explicit_fbx_material_alias.v1',
    'status':'PASS' if not failures else 'BLOCKED','jobs':result,'failures':failures,
    'runtime_policy':'Use only explicit unique aliases from this exact FBX/material-ID/object/triangle table. No generic namespace stripping, slot-index guessing or source recipe/material hash changes.',
    'native_execution':False,'frozen_category_helpers_changed':False})
