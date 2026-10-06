"""Derivative-only H0926 RepeatLoop proof. Never export FBX or save source files."""
import bpy, pathlib, json, hashlib, math, collections
import numpy as np
from mathutils import Vector

BASE=pathlib.Path(r'C:\Users\USER\Documents\Pipeline Environment\ModelBank\Modular_2026-10-04\WholeBuildingConversions')
OUT=pathlib.Path(__file__).parent/'H0926'
OUT.mkdir(parents=True,exist_ok=True)
FID='H0926';WIDTH=.05
EXT=json.loads((BASE/FID/'ExtensionBand'/'EXTENSION.json').read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
SOURCE_BLEND=EXT['blend'];BEFORE=sha(SOURCE_BLEND)
bpy.ops.wm.open_mainfile(filepath=SOURCE_BLEND,load_ui=False)
scene=bpy.context.scene
axis=EXT['corridor']['axis'];pitch=EXT['corridor']['pitch_m']
source=bpy.data.objects[f'SM_{FID}_Extension_Repeat']
mesh=source.data;mesh.calc_loop_triangles();mesh.calc_tangents(uvmap=mesh.uv_layers[0].name)
source_uv_names=[u.name for u in mesh.uv_layers]
source_normals=[np.array(n.vector,dtype=float) for n in mesh.corner_normals]
source_tangents=[np.array(l.tangent,dtype=float) for l in mesh.loops]
source_signs=[l.bitangent_sign for l in mesh.loops]
cross=[i for i in range(3) if i!=axis]
low_segments=[];triangles=[]
for tri in mesh.loop_triangles:
    verts=[]
    for vi,li in zip(tri.vertices,tri.loops):
        verts.append({'co':np.array(mesh.vertices[vi].co,dtype=float),
                      'uvs':[np.array(u.data[li].uv,dtype=float) for u in mesh.uv_layers],
                      'normal':source_normals[li].copy(),'tangent':source_tangents[li].copy(),
                      'sign':source_signs[li]})
    normal=np.array(tri.normal,dtype=float);mat=tri.material_index
    triangles.append((verts,normal,mat))
    for j in range(3):
        a=verts[j];b=verts[(j+1)%3]
        if abs(a['co'][axis])>2e-5 or abs(b['co'][axis])>2e-5:continue
        if np.linalg.norm(a['co']-b['co'])<1e-7:continue
        p0,p1,p2=[v['co'] for v in verts]
        pinv=np.linalg.pinv(np.column_stack([p1-p0,p2-p0]))
        low_segments.append({'a':a,'b':b,'tri':verts,'normal':normal,'material':mat,'pinv':pinv})

def interpolate(a,b,t):
    return {'co':a['co']+(b['co']-a['co'])*t,
            'uvs':[u+(v-u)*t for u,v in zip(a['uvs'],b['uvs'])],
            'normal':a['normal']+(b['normal']-a['normal'])*t,
            'tangent':a['tangent']+(b['tangent']-a['tangent'])*t,'sign':a['sign']}
def clip(poly,plane,above):
    output=[]
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)]
        ina=a['co'][axis]>=plane-1e-10 if above else a['co'][axis]<=plane+1e-10
        inb=b['co'][axis]>=plane-1e-10 if above else b['co'][axis]<=plane+1e-10
        if ina:output.append(a)
        if ina!=inb:
            t=(plane-a['co'][axis])/(b['co'][axis]-a['co'][axis])
            output.append(interpolate(a,b,float(t)))
    return output
def target_for(point,normal,material):
    options=[]
    for s in low_segments:
        if s['material']!=material or np.dot(s['normal'],normal)<.95:continue
        a=s['a']['co'][cross];b=s['b']['co'][cross];d=b-a
        t=float(np.clip(np.dot(point[cross]-a,d)/np.dot(d,d),0,1))
        closest=a+t*d;distance=float(np.linalg.norm(point[cross]-closest))
        options.append((distance,s,t,closest))
    if not options:raise RuntimeError('No homologous material/normal lower-edge chart')
    return min(options,key=lambda x:x[0])

positions=[];faces=[];face_materials=[];attributes=[];cache={}
proof={'family_id':FID,'source_blend':SOURCE_BLEND,'source_blend_sha256_before':BEFORE,'prototype_revision':2,
       'derivative_id':f'source_derived_modular.{FID}.RepeatLoop.v001','additional_part_count':1,
       'baseline_source_part_count_stays':609,'collar_width_m':WIDTH,'uv_channels':source_uv_names+['SeamTargetUV','SeamWeight'],
       'normal_blend_space':'Common shader normal-vector space: two Normal Map nodes use original UV0 and SeamTargetUV respectively, then vectors are linearly blended and normalized. Tangent-space RGB is not blended blindly.',
       'outside_collar_max_position_change_m':0.,'outside_collar_max_original_uv_change':0.,
       'boundary_vertices':0,'max_boundary_correction_m':0.,'target_chart_pairing_failures':0,
       'fbx_exported':False,'native_qualified':False}
boundary=[]
for verts,normal,material in triangles:
    pieces=[(clip(verts,pitch-WIDTH,False),False),(clip(verts,pitch-WIDTH,True),True)]
    for poly,is_collar in pieces:
        if len(poly)<3:continue
        for fan in range(1,len(poly)-1):
            triangle=[poly[0],poly[fan],poly[fan+1]]
            if np.linalg.norm(np.cross(triangle[1]['co']-triangle[0]['co'],triangle[2]['co']-triangle[0]['co']))<1e-11:continue
            inds=[];loops=[]
            for a in triangle:
                p=a['co'].copy();original=p.copy();uvs=[u.copy() for u in a['uvs']]
                weight=float(np.clip((p[axis]-(pitch-WIDTH))/WIDTH,0,1))
                customnormal=a['normal'].copy();targetuv=uvs[0].copy();expected_tangent=None;expected_sign=None
                if is_collar:
                    distance,s,t,closest=target_for(p,normal,material)
                    correction=closest-p[cross]
                    p[cross]+=correction*weight
                    homologous=p.copy();homologous[axis]-=pitch
                    coeff=s['pinv']@(homologous-s['tri'][0]['co'])
                    targetuv=s['tri'][0]['uvs'][0]+coeff[0]*(s['tri'][1]['uvs'][0]-s['tri'][0]['uvs'][0])+coeff[1]*(s['tri'][2]['uvs'][0]-s['tri'][0]['uvs'][0])
                    targetnormal=s['a']['normal']+(s['b']['normal']-s['a']['normal'])*t
                    customnormal=(1-weight)*customnormal+weight*targetnormal
                    if weight>1-1e-5:
                        expected=s['a']['uvs'][0]+t*(s['b']['uvs'][0]-s['a']['uvs'][0])
                        expected_tangent=s['a']['tangent']+t*(s['b']['tangent']-s['a']['tangent'])
                        expected_tangent/=max(np.linalg.norm(expected_tangent),1e-12)
                        expected_sign=s['a']['sign']
                        proof['boundary_vertices']+=1
                        proof['max_boundary_correction_m']=max(proof['max_boundary_correction_m'],float(np.linalg.norm(p-original)))
                        boundary.append({'loop_position_m':p.tolist(),'left_homologue_position_m':(s['a']['co']+t*(s['b']['co']-s['a']['co'])).tolist(),
                            'target_uv':targetuv.tolist(),'expected_left_uv0':expected.tolist(),
                            'target_uv_error':float(np.linalg.norm(targetuv-expected)),
                            'expected_left_normal':(targetnormal/np.linalg.norm(targetnormal)).tolist()})
                else:
                    proof['outside_collar_max_position_change_m']=max(proof['outside_collar_max_position_change_m'],float(np.linalg.norm(p-original)))
                    proof['outside_collar_max_original_uv_change']=max(proof['outside_collar_max_original_uv_change'],max(float(np.linalg.norm(u-v)) for u,v in zip(uvs,a['uvs'])))
                customnormal/=max(np.linalg.norm(customnormal),1e-12)
                key=tuple(p.tolist())
                if key not in cache:cache[key]=len(positions);positions.append(p.tolist())
                inds.append(cache[key]);loops.append({'uvs':uvs+[targetuv,np.array([weight,0.])],'normal':customnormal.tolist(),'weight':weight,'original':original.tolist(),
                    'expected_left_tangent':expected_tangent,'expected_left_sign':expected_sign})
            faces.append(inds);face_materials.append(material);attributes.extend(loops)

derived=bpy.data.meshes.new(f'SM_{FID}_Extension_RepeatLoop_v001_Mesh')
derived.from_pydata(positions,[],faces);derived.update()
for name in source_uv_names+['SeamTargetUV','SeamWeight']:derived.uv_layers.new(name=name)
for li,a in enumerate(attributes):
    for channel,uv in enumerate(a['uvs']):derived.uv_layers[channel].data[li].uv=uv.tolist()
derived.uv_layers.active_index=0
for layer in derived.uv_layers:layer.active_render=False
derived.uv_layers[0].active_render=True
derived.normals_split_custom_set([a['normal'] for a in attributes])
for poly,material in zip(derived.polygons,face_materials):poly.material_index=material

def blend_material(original):
    material=original.copy();material.name=f'M_{FID}_ExtensionLoop_Seam_v001';material['derivative_only']=True
    material['source_material']=original.name;material['collar_width_m']=WIDTH
    nodes=material.node_tree.nodes;links=material.node_tree.links
    base=nodes['Image Texture'];normal_image=nodes['Image Texture.001'];normal0=nodes['Normal Map'];bsdf=nodes['Principled BSDF']
    normal0.uv_map=source_uv_names[0]
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='SeamTargetUV';uv.name='Derivative seam target UV'
    mask=nodes.new('ShaderNodeUVMap');mask.uv_map='SeamWeight';mask.name='Derivative seam weight'
    separate=nodes.new('ShaderNodeSeparateXYZ');links.new(mask.outputs['UV'],separate.inputs['Vector'])
    inv=nodes.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;links.new(separate.outputs['X'],inv.inputs[1])
    def duplicate_image(src,label):
        node=nodes.new('ShaderNodeTexImage');node.image=src.image;node.interpolation=src.interpolation
        node.extension=src.extension;node.projection=src.projection;node.name=label
        links.new(uv.outputs['UV'],node.inputs['Vector']);return node
    base1=duplicate_image(base,'Derivative seam target BaseColor')
    normal1image=duplicate_image(normal_image,'Derivative seam target normal image')
    colormix=nodes.new('ShaderNodeMixRGB');colormix.blend_type='MIX';colormix.name='Derivative narrow seam BaseColor blend'
    links.new(separate.outputs['X'],colormix.inputs[0]);links.new(base.outputs['Color'],colormix.inputs[1]);links.new(base1.outputs['Color'],colormix.inputs[2]);links.new(colormix.outputs['Color'],bsdf.inputs['Base Color'])
    normal1=nodes.new('ShaderNodeNormalMap');normal1.space=normal0.space;normal1.uv_map='SeamTargetUV'
    normal1.inputs['Strength'].default_value=normal0.inputs['Strength'].default_value
    links.new(normal1image.outputs['Color'],normal1.inputs['Color'])
    def scale(normal_socket,factor_socket):
        node=nodes.new('ShaderNodeVectorMath');node.operation='SCALE';links.new(normal_socket,node.inputs[0]);links.new(factor_socket,node.inputs['Scale']);return node.outputs['Vector']
    va=scale(normal0.outputs['Normal'],inv.outputs[0]);vb=scale(normal1.outputs['Normal'],separate.outputs['X'])
    add=nodes.new('ShaderNodeVectorMath');add.operation='ADD';links.new(va,add.inputs[0]);links.new(vb,add.inputs[1])
    normalize=nodes.new('ShaderNodeVectorMath');normalize.operation='NORMALIZE';links.new(add.outputs['Vector'],normalize.inputs[0]);links.new(normalize.outputs['Vector'],bsdf.inputs['Normal'])
    return material
for slot in source.material_slots:derived.materials.append(blend_material(slot.material))
loop=bpy.data.objects.new(f'SM_{FID}_Extension_RepeatLoop_v001',derived)
loop.matrix_world=source.matrix_world.copy();scene.collection.objects.link(loop);loop.hide_render=True

# Tangents are recalculated for both UV charts after derivative topology/custom-normal changes.
derived.calc_tangents(uvmap=source_uv_names[0]);t0=[np.array(l.tangent) for l in derived.loops];s0=[l.bitangent_sign for l in derived.loops]
derived.calc_tangents(uvmap='SeamTargetUV');t1=[np.array(l.tangent) for l in derived.loops];s1=[l.bitangent_sign for l in derived.loops]
angles=[];parity=0;invalid=0;left_angles=[];left_sign_mismatch=0
for li,a in enumerate(attributes):
    if a['weight']>1-1e-5:
        dot=float(np.clip(np.dot(t0[li],t1[li]),-1,1));angles.append(math.degrees(math.acos(dot)))
        if s0[li]!=s1[li]:parity+=1
        expected=a.get('expected_left_tangent')
        if expected is not None:
            left_angles.append(math.degrees(math.acos(float(np.clip(np.dot(t1[li],expected),-1,1)))))
            if s1[li]!=a['expected_left_sign']:left_sign_mismatch+=1
    if np.linalg.norm(t0[li])<.5 or np.linalg.norm(t1[li])<.5:invalid+=1
proof['loop_triangles']=len(derived.polygons);proof['source_repeat_triangles']=len(mesh.loop_triangles)
proof['boundary_target_uv_max_error']=max(b['target_uv_error'] for b in boundary)
proof['boundary_uv0_vs_target_tangent_max_angle_degrees']=max(angles) if angles else None
proof['boundary_uv0_vs_target_tangent_sign_mismatches']=parity
proof['invalid_tangent_loops']=invalid
proof['boundary_target_vs_original_left_tangent_max_angle_degrees']=max(left_angles) if left_angles else None
proof['boundary_target_vs_original_left_tangent_sign_mismatches']=left_sign_mismatch
proof['boundary_records']=boundary
proof['qualification']='PROTOTYPE_REQUIRES_BOUNDARY_RENDER_REVIEW_AND_NATIVE_BINDING'
(OUT/'REPEAT_LOOP_PROTOTYPE_PROOF.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')

camera=bpy.data.objects.new('DerivativeAuditCamera',bpy.data.cameras.new('DerivativeAuditCamera'))
scene.collection.objects.link(camera);camera.data.type='ORTHO';scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.seed=0
scene.render.resolution_x=760;scene.render.resolution_y=760;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
bpy.context.preferences.filepaths.save_version=0
def render(name,target,view,scale):
    target=Vector(target);camera.location=target+Vector(view)
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
def full(name):
    coords=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' and not o.hide_render for v in o.bound_box]
    lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)])
    scale=max((hi-lo).x,(hi-lo).y,(hi-lo).z)*1.35
    render(name,(lo+hi)*.5,(24,-32,24),scale)
translation=Vector(next(p['assembly_translation_m'] for p in EXT['source_derived_parts'] if p['role']=='Repeat'))
wall_target=list(translation+Vector((pitch,.15,2.0)))
roof_target=list(translation+Vector((pitch,4.7,4.015)))
render('Original_N2_Wall_Seam',wall_target,(3,-5,2),2.5)
render('Original_N2_Roof_Seam',roof_target,(2,-2,5),2.5)
source.hide_render=True;loop.hide_render=False
full('Derivative_N2_Full')
render('Derivative_N2_Wall_Seam',wall_target,(3,-5,2),2.5)
render('Derivative_N2_Roof_Seam',roof_target,(2,-2,5),2.5)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{FID}_RepeatLoop_N2_DERIVATIVE.blend'))
loop2=loop.copy();loop2.data=derived;loop2.name=f'SM_{FID}_Extension_RepeatLoop_v001_Second';scene.collection.objects.link(loop2);loop2.location[axis]+=pitch
bpy.data.objects[f'SM_{FID}_Extension_Repeat_Second'].location[axis]+=pitch
bpy.data.objects[f'SM_{FID}_Extension_End'].location[axis]+=pitch
full('Derivative_N3_Full')
render('Derivative_N3_First_Wall_Seam',wall_target,(3,-5,2),2.5)
render('Derivative_N3_First_Roof_Seam',roof_target,(2,-2,5),2.5)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{FID}_RepeatLoop_N3_DERIVATIVE.blend'))
proof['source_blend_sha256_after']=sha(SOURCE_BLEND);proof['source_blend_unchanged']=BEFORE==proof['source_blend_sha256_after']
proof['saved_derivative_blends']=[str(OUT/f'{FID}_RepeatLoop_N2_DERIVATIVE.blend'),str(OUT/f'{FID}_RepeatLoop_N3_DERIVATIVE.blend')]
proof['render_files']=[str(p) for p in OUT.glob('*.png')]
(OUT/'REPEAT_LOOP_PROTOTYPE_PROOF.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items() if k!='boundary_records'},indent=2))
