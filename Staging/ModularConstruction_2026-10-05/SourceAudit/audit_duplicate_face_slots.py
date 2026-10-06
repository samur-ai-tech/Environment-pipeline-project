import bpy, pathlib, json, hashlib, collections
BASE=pathlib.Path(r'C:\Users\USER\Documents\Pipeline Environment\ModelBank\Modular_2026-10-04\WholeBuildingConversions')
OUT=pathlib.Path(__file__).parent
REQUESTS=[('H0018','SM_H0018_Tier04_EastFacade'),('H0021','SM_H0021_Roof_Core')]
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def mesh_receipt(ob):
    mesh=ob.data;mesh.calc_loop_triangles()
    counts=collections.Counter(t.material_index for t in mesh.loop_triangles)
    return {'object':ob.name,'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),
        'slots':[{'slot_index':i,'material_name':slot.material.name if slot.material else None,
                  'triangle_count':counts.get(i,0)} for i,slot in enumerate(ob.material_slots)],
        'uv_channels':[u.name for u in mesh.uv_layers],
        'bounds_m':{'min':[min(v.co[i] for v in mesh.vertices) for i in range(3)],
                    'max':[max(v.co[i] for v in mesh.vertices) for i in range(3)]}}
results=[]
for fid,name in REQUESTS:
    assembly=read(BASE/fid/'ASSEMBLY.json');part=next(p for p in assembly['modules'] if p['name']==name)
    blend=assembly['blend'];before_blend=sha(blend);before_fbx=sha(part['fbx'])
    bpy.ops.wm.open_mainfile(filepath=blend,load_ui=False)
    source=mesh_receipt(bpy.data.objects[name])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=part['fbx'],use_custom_normals=True)
    objs=[o for o in bpy.data.objects if o.type=='MESH']
    if len(objs)!=1:raise RuntimeError(f'{name} imported {len(objs)} meshes')
    readback=mesh_receipt(objs[0])
    # FBX Blender import bakes centimetre/unit conversion into a uniform object transform.
    transformed=[objs[0].matrix_world@v.co for v in objs[0].data.vertices]
    readback['world_bounds_m']={'min':[min(v[i] for v in transformed) for i in range(3)],'max':[max(v[i] for v in transformed) for i in range(3)]}
    readback['matrix_world']=[list(row) for row in objs[0].matrix_world]
    source_by_name={s['material_name']:s['triangle_count'] for s in source['slots']}
    rb_by_name={s['material_name']:s['triangle_count'] for s in readback['slots']}
    changes=[{'material_name':mat,'source_slot_index':next(s['slot_index'] for s in source['slots'] if s['material_name']==mat),
              'fbx_readback_slot_index':next((s['slot_index'] for s in readback['slots'] if s['material_name']==mat),None),
              'source_triangles':source_by_name[mat],'fbx_readback_triangles':rb_by_name.get(mat,0),
              'removed_triangles':source_by_name[mat]-rb_by_name.get(mat,0)} for mat in source_by_name]
    result={'family_id':fid,'part_name':name,'fbx':part['fbx'],
        'recorded_fbx_sha256':part['sha256'],'actual_fbx_sha256_before':before_fbx,
        'actual_fbx_sha256_after':sha(part['fbx']),'fbx_hash_matches_recorded':before_fbx==part['sha256'],
        'source_blend':blend,'source_blend_sha256_before':before_blend,'source_blend_sha256_after':sha(blend),
        'source_unchanged':before_blend==sha(blend) and before_fbx==sha(part['fbx']),
        'source':source,'fresh_blender_fbx_readback':readback,'per_material_triangle_differences':changes,
        'material_names_exact_match':set(source_by_name)==set(rb_by_name)}
    results.append(result)
    print(json.dumps({k:result[k] for k in ('part_name','per_material_triangle_differences','source_unchanged','material_names_exact_match')},indent=2))
(OUT/'DUPLICATE_FACE_SLOT_READBACK.json').write_text(json.dumps({'schema':'environmentpipeline.exact_duplicate_face_slot_readback.v1',
    'scope':'Fresh read-only Blender FBX reimport of exactly two source parts; no saves, changes or native qualification.',
    'parts':results},indent=2),encoding='utf-8')
