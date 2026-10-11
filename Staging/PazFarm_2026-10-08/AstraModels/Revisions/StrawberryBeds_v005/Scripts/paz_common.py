"""Paz Farm original Blender modelling utilities. All output confined to AstraModels."""
import bpy, math, json, random, hashlib, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = {'source':'Original procedural artwork created specifically for Paz Farm; no external images or satellite pixels used.', 'licence':'CC0-1.0', 'author':'Paz Farm modelling delivery, 2026-10-08'}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    s.unit_settings.system='METRIC'; s.unit_settings.scale_length=1.0
    s.render.engine='CYCLES'; s.cycles.samples=24; s.cycles.use_denoising=True
    s.render.threads_mode='FIXED'; s.render.threads=4
    s.render.resolution_x=1200; s.render.resolution_y=1000; s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG'
    s.render.film_transparent=False
    s.world=bpy.data.worlds.new('PazFarm_Preview_World'); s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.20,.25,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    s.view_settings.view_transform='AgX'
    bpy.context.preferences.filepaths.save_version=0
    bpy.context.preferences.filepaths.temporary_directory=str(ROOT/'Temp')

def image_file(name, pixels, noncolor=False):
    path=ROOT/'Textures'/name
    h,w=pixels.shape[:2]
    im=bpy.data.images.new(name,width=w,height=h,alpha=True)
    im.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
    im.pixels.foreach_set(np.asarray(pixels,dtype=np.float32).ravel())
    im.filepath_raw=str(path); im.file_format='PNG'; im.save()
    return im

def pbr(name,color=(.5,.5,.5),roughness=.65,metallic=0.,kind='noise',res=1024,alpha=1.,seed=13):
    """kind: noise, steel, bark, leaf, net, mulch, film. Unique family-prefixed names."""
    full=name if name.startswith('M_PazFarm_') else 'M_PazFarm_'+name
    if full in bpy.data.materials: return bpy.data.materials[full]
    tag=full[len('M_PazFarm_'):]
    rng=np.random.default_rng(seed)
    y,x=np.mgrid[0:res,0:res]/float(res-1)
    noise=rng.random((res,res))
    height=(noise-.5)*.07
    a=np.full((res,res),alpha,dtype=float)
    tint=np.ones((res,res))
    if kind=='bark':
        height=.22*np.sin(x*math.pi*38+np.sin(y*19)*.9)+.12*np.sin(x*math.pi*89+y*5)+(noise-.5)*.15
        tint=.80+height*.8
    elif kind=='leaf':
        v=y; width=np.power(np.maximum(0,np.sin(math.pi*v)),.78)*.44
        a=(np.abs(x-.5)<width).astype(float)*alpha
        vein=np.exp(-((x-.5)/.011)**2)
        secondary=np.power(np.maximum(0,np.cos((v-np.abs(x-.5)*.85)*math.pi*28)),26)
        tint=.75+.2*np.sin(math.pi*v)+.12*noise+.15*vein+.08*secondary
        height=.08*vein+.03*secondary+.02*noise
    elif kind=='net':
        # Eight apertures per UV tile, tile UVs to physical mesh density.
        grid=(np.mod(x*8,1)<.14)|(np.mod(y*8,1)<.14)
        a=grid.astype(float)*alpha; height=grid.astype(float)*.06
        tint=.85+noise*.15
    elif kind=='mulch':
        height=.07*np.sin(x*80+np.sin(y*40)*2)+.03*noise
        tint=.8+.2*np.sin(x*60+y*7)**2
    elif kind=='steel':
        height=.01*noise; tint=.94+.06*noise
    elif kind=='film':
        height=.013*np.sin(x*70+y*3)+.008*noise; tint=.94+.06*noise
    else: tint=.88+.20*noise
    bc=np.ones((res,res,4),dtype=float)
    for i,c in enumerate(color[:3]): bc[:,:,i]=np.clip(c*tint,0,1)
    bc[:,:,3]=a
    gy,gx=np.gradient(height)
    n=np.stack((-gx*15,-gy*15,np.ones_like(gx)),axis=-1); n/=np.linalg.norm(n,axis=-1,keepdims=True)
    nm=np.ones_like(bc); nm[:,:,:3]=n*.5+.5
    orm=np.ones_like(bc); orm[:,:,0]=np.clip(.96+height*.1,.75,1); orm[:,:,1]=roughness; orm[:,:,2]=metallic
    base=image_file('T_PazFarm_'+tag+'_BaseColor.png',bc)
    normal=image_file('T_PazFarm_'+tag+'_Normal.png',nm,True)
    packed=image_file('T_PazFarm_'+tag+'_ORM.png',orm,True)
    mat=bpy.data.materials.new(full); mat.use_nodes=True; nt=mat.node_tree; bs=nt.nodes.get('Principled BSDF')
    tb=nt.nodes.new('ShaderNodeTexImage'); tb.image=base; tb.label='Base Colour + opacity'; nt.links.new(tb.outputs['Color'],bs.inputs['Base Color'])
    tn=nt.nodes.new('ShaderNodeTexImage'); tn.image=normal; nn=nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'],nn.inputs['Color']); nt.links.new(nn.outputs['Normal'],bs.inputs['Normal'])
    to=nt.nodes.new('ShaderNodeTexImage'); to.image=packed; sep=nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(to.outputs['Color'],sep.inputs['Color']); nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']); nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    if kind in ('net','leaf','film') or alpha<1:
        nt.links.new(tb.outputs['Alpha'],bs.inputs['Alpha']); mat.surface_render_method='DITHERED'; mat.use_backface_culling=False
    if kind=='leaf':
        bs.inputs['Subsurface Weight'].default_value=.06
    if kind=='film':
        bs.inputs['Transmission Weight'].default_value=.25; bs.inputs['IOR'].default_value=1.46
    mat['texture_files']=json.dumps([str(Path('Textures')/p.name) for p in (Path(base.filepath_raw),Path(normal.filepath_raw),Path(packed.filepath_raw))])
    mat['licence']='CC0-1.0'; mat['source']=SOURCE['source']; mat['blend_mode_intent']='MASKED_TWO_SIDED' if kind in ('leaf','net') else ('TRANSLUCENT_TWO_SIDED' if kind=='film' else 'OPAQUE')
    mat['orm_channels']='R=AmbientOcclusion G=Roughness B=Metallic'; mat['normal_convention']='OpenGL +Y; flip green if using Unreal DirectX convention'
    return mat

def mesh(name,verts,faces,mat=None,uvs=None,smooth=False):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    ob=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(ob)
    if mat: data.materials.append(mat)
    layer=data.uv_layers.new(name='UV0')
    for poly in data.polygons:
        poly.use_smooth=smooth
        for j,li in enumerate(poly.loop_indices):
            vi=data.loops[li].vertex_index
            layer.data[li].uv=uvs[poly.index][j] if uvs else (data.vertices[vi].co.x,data.vertices[vi].co.z+data.vertices[vi].co.y)
    return ob

def box(name,center,size,mat=None,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center); o=bpy.context.object; o.name=name; o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    if o.data.uv_layers:o.data.uv_layers[0].name='UV0'
    if bevel:
        m=o.modifiers.new('Small manufactured edge bevel','BEVEL');m.width=bevel;m.segments=1
        bpy.ops.object.modifier_apply(modifier=m.name)
    return o

def cylinder(name,a,b,radius,mat=None,vertices=10,radius2=None):
    a,b=Vector(a),Vector(b); vec=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=radius,radius2=radius if radius2 is None else radius2,depth=vec.length,end_fill_type='NGON',location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=vec.to_track_quat('Z','Y').to_euler()
    if mat:o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    if o.data.uv_layers:o.data.uv_layers[0].name='UV0'
    return o

def sphere(name,center,scale,mat=None,segments=12,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=center)
    o=bpy.context.object;o.name=name;o.scale=scale
    if mat:o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    if o.data.uv_layers:o.data.uv_layers[0].name='UV0'
    return o

def combine(name,objects,pivot=(0,0,0)):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.hide_set(False);o.hide_viewport=False;o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;o.data.name=name+'_Mesh'
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.context.scene.cursor.location=pivot;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return o

def bounds(ob):
    pts=[ob.matrix_world@Vector(p) for p in ob.bound_box]
    return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]

def asset(name,objects,collisions=None,pivot=(0,0,0),notes=None,budget=5000,nominal=None):
    ob=combine(name,objects,pivot); coll=collisions or []
    for i,c in enumerate(coll):
        c.name='UCX_'+name+'_'+str(i).zfill(2);c.hide_render=True;c.display_type='WIRE'
    bpy.context.view_layer.update();ob.data.calc_loop_triangles()
    deg=sum(1 for t in ob.data.loop_triangles if t.area<1e-12)
    if deg:raise RuntimeError(name+' has zero-area triangles: '+str(deg))
    tris=len(ob.data.loop_triangles)
    if tris>budget:raise RuntimeError(name+' over budget: '+str(tris)+' > '+str(budget))
    bb=bounds(ob);sz=[round(bb[1][i]-bb[0][i],5) for i in range(3)]
    mats=[]
    for m in ob.data.materials:
        if not m:continue
        mats.append({'name':m.name,'textures':json.loads(m.get('texture_files','[]')),'mode':m.get('blend_mode_intent','OPAQUE'),'source_licence':SOURCE})
    rec={'name':name,'size_metres_W_D_H':sz,'bounds_metres':bb,'triangles_LOD0':tris,'triangle_budget':budget,'materials':mats,'pivot':{'position_metres':list(pivot),'description':'Ground origin; see notes for module placement'},'notes':notes or [],'collision_objects':[c.name for c in coll],'fbx':'FBX/'+name+'.fbx','preview':'Previews/'+name+'.png','nominal_size_metres':nominal,'qa':{'zero_area_triangles':deg,'uv0_present':bool(ob.data.uv_layers),'negative_scale':any(s<0 for s in ob.scale)}}
    ob['manifest']=json.dumps(rec);ob['source_front']='Blender -Y; FBX axis_forward=-Y axis_up=Z';ob['real_units']='metres; scale_length=1.0'
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
    for c in coll:c.hide_set(False);c.select_set(True)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.fbx(filepath=str(ROOT/rec['fbx']),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    for c in coll:c.hide_set(True)
    return ob,rec

def plain_mat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8;return m

def preview(ob,rec,azimuth=-55,elevation=21):
    s=bpy.context.scene; old={o:o.hide_render for o in s.objects}
    for o in s.objects:o.hide_render=(o!=ob)
    tmp=[]; dark=plain_mat('Preview_Human_Charcoal',(.055,.074,.085));floor=plain_mat('Preview_Ground',(.20,.235,.25))
    bb=bounds(ob);w,d,h=[bb[1][i]-bb[0][i] for i in range(3)]
    hx=bb[1][0]+max(.55,w*.10);hy=bb[0][1]+d*.3
    # Human height is exactly 1.800 m including head. Preview-only; never exported.
    tmp.append(sphere('SCALE_1_8m_Head',(hx,hy,1.665),(.10,.09,.135),dark))
    tmp.append(cylinder('SCALE_Torso',(hx,hy,1.00),(hx,hy,1.49),.16,dark,8,.21))
    for sign in (-1,1):
        tmp.append(cylinder('SCALE_Leg',(hx+sign*.10,hy,.08),(hx+sign*.09,hy,1.02),.072,dark,8))
        tmp.append(box('SCALE_Foot',(hx+sign*.10,hy-.04,.045),(.14,.27,.09),dark))
        tmp.append(cylinder('SCALE_Arm',(hx+sign*.19,hy,1.43),(hx+sign*.27,hy,.94),.055,dark,8))
    size=max(w,d,h,3)
    tmp.append(box('Preview_Floor',((bb[0][0]+hx)/2,(bb[0][1]+bb[1][1])/2,-.045),(size*200,size*200,.08),floor))
    target=Vector(((bb[0][0]+hx+.15)/2,(bb[0][1]+bb[1][1])/2,max(h,1.8)*.46))
    aa=math.radians(azimuth);el=math.radians(elevation)
    bpy.ops.object.camera_add(location=target+Vector((math.cos(aa)*math.cos(el),math.sin(aa)*math.cos(el),math.sin(el)))*size*2.5)
    cam=bpy.context.object;tmp.append(cam);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=max(w*1.3,d*1.25,h*1.4,3)*1.10;s.camera=cam
    bpy.ops.object.light_add(type='AREA',location=target+Vector((-size*.6,-size*.8,size*1.5)));light=bpy.context.object;tmp.append(light);light.data.energy=150*size*size;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN',location=(0,0,20));sun=bpy.context.object;tmp.append(sun);sun.rotation_euler=(.5,-.3,-.5);sun.data.energy=1.6;sun.data.angle=.2
    s.render.filepath=str(ROOT/rec['preview']);bpy.ops.render.render(write_still=True)
    for o in tmp:bpy.data.objects.remove(o,do_unlink=True)
    for o,val in old.items():o.hide_render=val
    s.camera=None

def save_family(filename,records,parameters=None):
    scene=bpy.context.scene;scene['PazFarm_parameters']=json.dumps(parameters or {},indent=2);scene['PazFarm_assets']=json.dumps([r['name'] for r in records]);scene['PazFarm_source_licence']='CC0-1.0 original modelling and original procedural textures'
    # Relative texture paths survive moving the whole AstraModels folder.
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blend'/filename))
    for im in bpy.data.images:
        if im.filepath:im.filepath=bpy.path.relpath(im.filepath)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blend'/filename))
    for rec in records:rec['blend']='Blend/'+filename

def report(filename,records,extra=None):
    (ROOT/'Reports'/filename).write_text(json.dumps({'assets':records,'extra':extra or {}},indent=2),encoding='utf-8')
