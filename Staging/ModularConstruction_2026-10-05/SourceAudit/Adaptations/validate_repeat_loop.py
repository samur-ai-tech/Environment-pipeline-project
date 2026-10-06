"""Fresh saved-derivative validation and conditional staged FBX export; no native work."""
import bpy, pathlib, json, hashlib, math
import numpy as np
from mathutils import Vector
BASE=pathlib.Path(r'C:\Users\USER\Documents\Pipeline Environment\ModelBank\Modular_2026-10-04\WholeBuildingConversions')
OUT=pathlib.Path(__file__).parent/'H0926';FID='H0926';WIDTH=.05
EXT=json.loads((BASE/FID/'ExtensionBand'/'EXTENSION.json').read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def mesh_pin(mesh):
    h=hashlib.sha256()
    for v in mesh.vertices:h.update(np.asarray(v.co,dtype='<f4').tobytes())
    for p in mesh.polygons:h.update(np.asarray([p.material_index,*p.vertices],dtype='<i4').tobytes())
    for uv in mesh.uv_layers:
        h.update(uv.name.encode())
        for loop in uv.data:h.update(np.asarray(loop.uv,dtype='<f4').tobytes())
    return h.hexdigest()
def section(ob,plane,uv_name):
    mesh=ob.data;mesh.calc_loop_triangles();mesh.calc_tangents(uvmap=uv_name)
    uv=mesh.uv_layers[uv_name];coords=[ob.matrix_world@v.co for v in mesh.vertices]
    out=[]
    for poly in mesh.polygons:
        loops=list(poly.loop_indices);on=[abs(coords[mesh.loops[li].vertex_index][0]-plane)<2e-5 for li in loops]
        if all(on):continue
        for j,li in enumerate(loops):
            lj=loops[(j+1)%len(loops)]
            if not(on[j] and on[(j+1)%len(loops)]):continue
            a=coords[mesh.loops[li].vertex_index];b=coords[mesh.loops[lj].vertex_index]
            if (a-b).length<1e-7:continue
            out.append({'a':np.array(a)[1:],'b':np.array(b)[1:],
                'uv_a':np.array(uv.data[li].uv),'uv_b':np.array(uv.data[lj].uv),
                'normal_a':np.array(mesh.corner_normals[li].vector),'normal_b':np.array(mesh.corner_normals[lj].vector),
                'tangent_a':np.array(mesh.loops[li].tangent),'tangent_b':np.array(mesh.loops[lj].tangent),
                'sign':mesh.loops[li].bitangent_sign,'normal':np.array(poly.normal)})
    return out
def normalized(v):return v/max(np.linalg.norm(v),1e-12)
def compare(a,b):
    distances=[];phases=[];normalangles=[];tangentangles=[];sign_mismatches=0;unmatched=0
    byorientation={}
    for source,target in [(a,b),(b,a)]:
        for s in source:
            size=np.linalg.norm(s['b']-s['a']);steps=max(3,min(128,math.ceil(size/.05)))
            for f in np.linspace(.0,1.,steps+1):
                p=s['a']+(s['b']-s['a'])*f;choices=[]
                for t in target:
                    d=t['b']-t['a'];g=float(np.clip(np.dot(p-t['a'],d)/np.dot(d,d),0,1))
                    dist=float(np.linalg.norm(p-(t['a']+g*d)))
                    if np.dot(s['normal'],t['normal'])>=.95:choices.append((dist,t,g))
                if not choices:unmatched+=1;continue
                dist,t,g=min(choices,key=lambda z:z[0]);distances.append(dist)
                ua=s['uv_a']+(s['uv_b']-s['uv_a'])*f;ub=t['uv_a']+(t['uv_b']-t['uv_a'])*g
                phases.append(float(np.linalg.norm((ua-ub)-np.round(ua-ub))))
                na=normalized(s['normal_a']+(s['normal_b']-s['normal_a'])*f);nb=normalized(t['normal_a']+(t['normal_b']-t['normal_a'])*g)
                ta=normalized(s['tangent_a']+(s['tangent_b']-s['tangent_a'])*f);tb=normalized(t['tangent_a']+(t['tangent_b']-t['tangent_a'])*g)
                normalangles.append(math.degrees(math.acos(float(np.clip(np.dot(na,nb),-1,1)))))
                tangentangles.append(math.degrees(math.acos(float(np.clip(np.dot(ta,tb),-1,1)))))
                if s['sign']!=t['sign']:sign_mismatches+=1
                category='horizontal' if abs(s['normal'][2])>.9 else ('vertical' if abs(s['normal'][2])<.25 else 'oblique')
                byorientation.setdefault(category,[]).append(dist)
    return {'samples':len(distances),'profile_distance_max_m':max(distances) if distances else None,
        'effective_wrapped_uv_phase_max':max(phases) if phases else None,
        'custom_normal_angle_max_degrees':max(normalangles) if normalangles else None,
        'effective_uv_tangent_angle_max_degrees':max(tangentangles) if tangentangles else None,
        'effective_uv_tangent_sign_mismatches':sign_mismatches,'unmatched':unmatched,
        'surface_orientations':{k:{'samples':len(v),'profile_distance_max_m':max(v)} for k,v in byorientation.items()}}

source_file_before=sha(EXT['blend'])
bpy.ops.wm.open_mainfile(filepath=EXT['blend'],load_ui=False)
source_mesh=bpy.data.objects[f'SM_{FID}_Extension_Repeat'].data
source_pin=mesh_pin(source_mesh);source_mesh.calc_loop_triangles()
source_triangles=[]
for t in source_mesh.loop_triangles:
    points=np.array([source_mesh.vertices[i].co for i in t.vertices]);uvs=[np.array([layer.data[li].uv for li in t.loops]) for layer in source_mesh.uv_layers]
    pinv=np.linalg.pinv(np.column_stack([points[1]-points[0],points[2]-points[0]]))
    normals=np.array([source_mesh.corner_normals[li].vector for li in t.loops])
    source_triangles.append((points,uvs,pinv,t.material_index,np.array(t.normal),normals))

validations=[];derivative_paths=[]
for n in (2,3):
    blend=OUT/f'{FID}_RepeatLoop_N{n}_DERIVATIVE.blend';derivative_paths.append(str(blend))
    bpy.ops.wm.open_mainfile(filepath=str(blend),load_ui=False)
    loop=bpy.data.objects[f'SM_{FID}_Extension_RepeatLoop_v001']
    original=bpy.data.objects[f'SM_{FID}_Extension_Repeat_Second']
    copies=[loop]+([bpy.data.objects[f'SM_{FID}_Extension_RepeatLoop_v001_Second']] if n==3 else [])
    outside={'loops_checked':0,'max_geometry_residual_m':0.,'max_original_uv_residual':0.,'unmatched':0,'unmatched_details':[]}
    loop.data.calc_loop_triangles()
    for poly in loop.data.polygons:
        for li in poly.loop_indices:
            point=np.array(loop.data.vertices[loop.data.loops[li].vertex_index].co)
            if point[0]>=EXT['corridor']['pitch_m']-WIDTH-1e-6:continue
            choices=[]
            for points,uvs,pinv,mat,norm,normals in source_triangles:
                if mat!=poly.material_index or np.dot(norm,np.array(poly.normal))<.95:continue
                c=pinv@(point-points[0]);weights=np.array([1-c.sum(),*c])
                if min(weights)<-1e-5:continue
                projected=weights@points;dist=float(np.linalg.norm(projected-point))
                if dist>1e-6:continue
                err=max(float(np.linalg.norm(weights@uv-np.array(layer.data[li].uv))) for uv,layer in zip(uvs,list(loop.data.uv_layers)[:2]))
                choices.append((err,dist))
            outside['loops_checked']+=1
            if not choices:
                outside['unmatched']+=1
                fallback=[]
                for points,uvs,pinv,mat,norm,normals in source_triangles:
                    if mat!=poly.material_index:continue
                    c=pinv@(point-points[0]);weights=np.array([1-c.sum(),*c])
                    if min(weights)<-1e-5:continue
                    projected=weights@points;dist=float(np.linalg.norm(projected-point))
                    err=max(float(np.linalg.norm(weights@uv-np.array(layer.data[li].uv))) for uv,layer in zip(uvs,list(loop.data.uv_layers)[:2]))
                    fallback.append({'geometry_residual_m':dist,'original_uv_residual':err,
                        'polygon_normal_dot':float(np.dot(norm,np.array(poly.normal))),
                        'custom_normal_residual':float(np.linalg.norm(normalized(weights@normals)-np.array(loop.data.corner_normals[li].vector)))})
                outside['unmatched_details'].append({'polygon_index':poly.index,'loop_index':li,'point_local_m':point.tolist(),'polygon_area_m2':poly.area,
                    'best_source_match':min(fallback,key=lambda r:(r['geometry_residual_m'],r['original_uv_residual'])) if fallback else None})
                continue
            err,dist=min(choices);outside['max_original_uv_residual']=max(outside['max_original_uv_residual'],err)
            outside['max_geometry_residual_m']=max(outside['max_geometry_residual_m'],dist)
    seams=[]
    for i,l in enumerate(copies):
        mate=copies[i+1] if i+1<len(copies) else original
        plane=l.location[0]+EXT['corridor']['pitch_m']
        seam=compare(section(l,plane,'SeamTargetUV'),section(mate,plane,'SourceRenderUV'))
        mask=l.data.uv_layers['SeamWeight'];upper=[mask.data[li].uv.x for p in l.data.polygons for li in p.loop_indices if abs(l.data.vertices[l.data.loops[li].vertex_index].co.x-EXT['corridor']['pitch_m'])<2e-5]
        seam.update({'left_object':l.name,'right_object':mate.name,'plane_world_m':plane,'left_seam_weight_min':min(upper),'left_seam_weight_max':max(upper)})
        seams.append(seam)
    material=loop.material_slots[0].material;nodes=material.node_tree.nodes
    proof={'repeat_count':n,'derivative_blend':str(blend),'derivative_blend_sha256':sha(blend),
        'source_original_repeat_mesh_pin_matches':mesh_pin(original.data)==source_pin,
        'outside_collar_source_surface_readback':outside,'new_join_readbacks':seams,
        'loop_uv_channels':[u.name for u in loop.data.uv_layers],
        'normal_strength_original':nodes['Normal Map'].inputs['Strength'].default_value,
        'normal_map_uv0_name':nodes['Normal Map'].uv_map,
        'source_diffuse_path':bpy.path.abspath(nodes['Image Texture'].image.filepath),
        'source_normal_path':bpy.path.abspath(nodes['Image Texture.001'].image.filepath),
        'native_qualified':False}
    proof['source_level_exact_count_pass']=proof['source_original_repeat_mesh_pin_matches'] and outside['unmatched']==0 and outside['max_original_uv_residual']<1e-5 and all(s['samples'] and s['profile_distance_max_m']<1e-5 and s['effective_wrapped_uv_phase_max']<1e-5 and s['effective_uv_tangent_sign_mismatches']==0 and s['effective_uv_tangent_angle_max_degrees']<.1 and s['left_seam_weight_min']>.9999 for s in seams)
    validations.append(proof)
    if n==3 and '--diagnose-only' not in __import__('sys').argv:
        scene=bpy.context.scene;camera=scene.camera
        origin=Vector(next(p['assembly_translation_m'] for p in EXT['source_derived_parts'] if p['role']=='Repeat'))
        for label,z,y,view in [('Wall',2.,.15,(3,-5,2)),('Roof',4.015,4.7,(2,-2,5))]:
            target=origin+Vector((2*EXT['corridor']['pitch_m'],y,z));camera.location=target+Vector(view)
            camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=2.5
            scene.render.filepath=str(OUT/f'Derivative_N3_Second_{label}_Seam.png');bpy.ops.render.render(write_still=True)

receipt={'schema':'environmentpipeline.repeat_loop_fresh_saved_readback.v1','family_id':FID,
    'source_blend_sha256_before':source_file_before,'source_blend_sha256_after':sha(EXT['blend']),
    'source_blend_unchanged':source_file_before==sha(EXT['blend']),
    'source_original_repeat_mesh_pin':source_pin,'validations':validations,
    'source_level_N2_N3_pass':all(v['source_level_exact_count_pass'] for v in validations),
    'native_qualified':False,'exported_fbx':None}
(OUT/'REPEAT_LOOP_FRESH_SAVED_READBACK.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))

# Export only if all exact-count saved derivative checks passed; source 609 parts stay unchanged.
if not receipt['source_level_N2_N3_pass']:raise RuntimeError('Fresh derivative source-level gate failed; FBX not exported')
bpy.ops.wm.open_mainfile(filepath=str(OUT/f'{FID}_RepeatLoop_N2_DERIVATIVE.blend'),load_ui=False)
loop=bpy.data.objects[f'SM_{FID}_Extension_RepeatLoop_v001'];expected_vertices=[list(v.co) for v in loop.data.vertices]
expected_pin=mesh_pin(loop.data);expected_triangles=len(loop.data.polygons);expected_uvs=[u.name for u in loop.data.uv_layers]
expected_materials=[s.material.name for s in loop.material_slots]
assembly_translation=list(loop.location);loop.location=(0,0,0)
bpy.ops.object.select_all(action='DESELECT');loop.select_set(True);bpy.context.view_layer.objects.active=loop
fbx=OUT/f'SM_{FID}_Extension_RepeatLoop_v001.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_NONE',use_space_transform=True,axis_forward='Y',axis_up='Z',
    use_mesh_modifiers=False,mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False,bake_anim=False,
    embed_textures=False,path_mode='ABSOLUTE')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(fbx),use_custom_normals=True)
ob=next(o for o in bpy.data.objects if o.type=='MESH');ob.data.calc_loop_triangles()
actual_vertices=[list(ob.matrix_world@v.co) for v in ob.data.vertices]
geommax=max(min(np.linalg.norm(np.array(a)-np.array(b)) for b in actual_vertices) for a in expected_vertices)
uvnames=[u.name for u in ob.data.uv_layers];materialnames=[s.material.name for s in ob.material_slots]
export={'derivative_id':f'source_derived_modular.{FID}.RepeatLoop.v001','additional_derived_part_count':1,
    'baseline_source_parts':609,'fbx':str(fbx),'fbx_sha256':sha(fbx),
    'derivative_source_mesh_pin':expected_pin,'source_blend_unchanged':sha(EXT['blend'])==source_file_before,
    'source_repeat_assembly_translation_m':assembly_translation,
    'triangles_expected':expected_triangles,'triangles_fbx_readback':len(ob.data.loop_triangles),
    'uv_names_expected':expected_uvs,'uv_names_fbx_readback':uvnames,
    'materials_expected':expected_materials,'materials_fbx_readback':materialnames,
    'vertex_hausdorff_one_direction_readback_m':geommax,
    'fresh_blender_fbx_readback_pass':expected_triangles==len(ob.data.loop_triangles) and expected_uvs==uvnames and expected_materials==materialnames and geommax<2e-6,
    'placement_rule':'For N=2 or3 only: Start at original assembly translation; Loop at Repeat translation + k*pitch for k=0..N-2; original Repeat at Repeat translation +(N-1)*pitch; End at original End translation +(N-1)*pitch. All offsets along X only. N=1 uses unchanged original Start/Repeat/End.',
    'native_material_bridge':'UV0/1 original channels unchanged. UV2=SeamTargetUV, UV3.x=SeamWeight. BaseColor=lerp(source diffuse UV0, source diffuse UV2, weight). Two normal samples preserve source full RGB, source strength0.2700000107 and source tangent/OpenGL convention; convert each through its own UV tangent basis into a common space, blend and normalize, then convert to native output basis. Do not blindly mix tangent-space RGB. Preserve roughness/metallic/alpha source defaults.',
    'capability_scope':'Source-level candidate for exact N=2/N=3 whole-building X-band extension only. No native import, catalog release, procedural selection, Houdini Engine generation, or architectural floor repetition enabled.',
    'hold_state':'Preserve all original rights/asset holds; additional staged derived identity only.'}
(OUT/'REPEAT_LOOP_EXPORT.json').write_text(json.dumps(export,indent=2),encoding='utf-8')
print(json.dumps(export,indent=2))
