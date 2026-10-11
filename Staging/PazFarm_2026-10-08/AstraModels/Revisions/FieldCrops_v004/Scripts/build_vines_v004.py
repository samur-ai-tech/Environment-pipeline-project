"""Original VSP grapevine modules; metre geometry, +Y tiling, no editor work.

All output belongs to the FieldCrops_v004 revision. Earlier artwork is read-only.
"""
import bpy, math, random, json, sys, struct, zlib, hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Scripts'))
import paz_common as C

PARAMS={
    'tile_length_m':3.0,'tile_axis':'+Y','pivot_metres':[0,0,0],
    'vine_centres_y_m':[.75,2.25],'trunk_height_m':.90,
    'post_width_m':.07,'post_center_y_m':.035,'post_height_m':1.90,
    'canopy_base_m':.92,'canopy_top_m':1.78,'canopy_hull_thickness_m':.53,
    'detailed_inner_hull_width_m':.48,'detailed_inner_hull_top_m':1.70,
    'canopy_stations_m':[0,.15,.75,1.5,2.25,2.85,3],
    'wire_heights_m':[.90,1.28,1.62],'leaf_counts':{'A':420,'B':432,'C':444},
    'leaf_rgb_srgb':[49,79,28],'canopy_rgb_srgb':[47,76,27],
    'row_pitch_preview_m':2.75,'seed':10112026,
    'material_order':['Vine_Bark_v004','Vine_Post_v004','Vine_Wire_v004','Vine_Leaf_v004','Vine_LeafLight_v004','Vine_Canopy_v004','Vine_Grape_v004'],
}

class Batch:
    def __init__(self):self.v=[];self.f=[];self.uv=[];self.mi=[];self.parts=[]
    def add(self,verts,faces,uvs,material,part):
        start=len(self.v);self.v.extend(tuple(p) for p in verts)
        for face,uv in zip(faces,uvs):
            self.f.append(tuple(start+i for i in face));self.uv.append(uv);self.mi.append(material);self.parts.append(part)
    def finish(self,name,materials):
        mesh=bpy.data.meshes.new(name+'_Mesh');mesh.from_pydata(self.v,[],self.f);mesh.update()
        ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
        for mat in materials:mesh.materials.append(mat)
        uv=mesh.uv_layers.new(name='UV0');tag=mesh.attributes.new('Vine_component','INT','FACE')
        for p,coords,mi,part in zip(mesh.polygons,self.uv,self.mi,self.parts):
            p.material_index=mi;p.use_smooth=part not in (2,8,10);tag.data[p.index].value=part
            if part==1 and len(p.vertices)>4:p.use_smooth=False
            for li,co in zip(p.loop_indices,coords):uv.data[li].uv=co
        return ob

def tube(batch,points,radii,sides,mat,part):
    """Closed curved tube, circular cap UVs and a seam-aware side unwrap."""
    verts=[];n=len(points);points=[Vector(p) for p in points]
    for j,p in enumerate(points):
        axis=(points[min(n-1,j+1)]-points[max(0,j-1)]).normalized()
        helper=Vector((0,0,1)) if abs(axis.z)<.92 else Vector((0,1,0))
        u=axis.cross(helper).normalized();v=axis.cross(u).normalized()
        for i in range(sides):
            a=math.tau*i/sides;verts.append(p+radii[j]*(u*math.cos(a)+v*math.sin(a)))
    faces=[];uv=[]
    for j in range(n-1):
        for i in range(sides):
            ni=(i+1)%sides;faces.append((j*sides+i,j*sides+ni,(j+1)*sides+ni,(j+1)*sides+i))
            uv.append([(i/sides,j/(n-1)),((i+1)/sides,j/(n-1)),((i+1)/sides,(j+1)/(n-1)),(i/sides,(j+1)/(n-1))])
    faces.extend([tuple(reversed(range(sides))),tuple((n-1)*sides+i for i in range(sides))])
    for face in faces[-2:]:uv.append([(.5+.5*math.cos(math.tau*(i%sides)/sides),.5+.5*math.sin(math.tau*(i%sides)/sides)) for i in face])
    batch.add(verts,faces,uv,mat,part)

def post(batch):
    x=.035;y0=0;y1=.07;h=1.9
    v=[(-x,y0,0),(x,y0,0),(x,y1,0),(-x,y1,0),(-x,y0,h),(x,y0,h),(x,y1,h),(-x,y1,h)]
    f=[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    batch.add(v,f,[[(0,0),(1,0),(1,1),(0,1)] for _ in f],1,2)

def wire_support(batch,z):
    x=.2925;y0=.02;y1=.05;lo=z-.006;hi=z+.006
    v=[(-x,y0,lo),(x,y0,lo),(x,y1,lo),(-x,y1,lo),(-x,y0,hi),(x,y0,hi),(x,y1,hi),(-x,y1,hi)]
    f=[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    batch.add(v,f,[[(0,0),(1,0),(1,1),(0,1)] for _ in f],2,8)

def canopy(batch,variant,lowest):
    # Clockwise X/Z perimeter makes +Y-directed prism side surfaces face outward.
    profile=[(-.19,.92),(-.265,1.02),(-.265,1.51),(-.19,1.73),(0,1.78),(.19,1.73),(.265,1.51),(.265,1.02),(.19,.92)]
    if not lowest:profile=[(x*.48/.53,.92+(z-.92)*.78/.86) for x,z in profile]
    stations=PARAMS['canopy_stations_m'];n=len(profile);verts=[];var='ABC'.index(variant)
    for j,y in enumerate(stations):
        interior=j not in (0,1,len(stations)-2,len(stations)-1)
        shift=.012*math.sin(j*2.2+var*1.5) if interior else 0
        lift=.012*math.cos(j*1.8+var) if interior else 0
        for x,z in profile:
            weight=(z-.92)/.84;verts.append((x+shift*weight,y,z+lift*weight))
    lengths=[math.hypot(profile[(i+1)%n][0]-profile[i][0],profile[(i+1)%n][1]-profile[i][1]) for i in range(n)]
    arc=[0]
    for v in lengths:arc.append(arc[-1]+v)
    arc=[a/arc[-1] for a in arc]
    faces=[];uv=[]
    for j in range(len(stations)-1):
        for i in range(n):
            ni=(i+1)%n;faces.append((j*n+i,j*n+ni,(j+1)*n+ni,(j+1)*n+i))
            uv.append([(arc[i],stations[j]/3),(arc[i+1],stations[j]/3),(arc[i+1],stations[j+1]/3),(arc[i],stations[j+1]/3)])
    faces.extend([tuple(reversed(range(n))),tuple((len(stations)-1)*n+i for i in range(n))])
    for face in faces[-2:]:uv.append([((verts[i][0]+.35)/.7,(verts[i][2]-.85)/1.0) for i in face])
    batch.add(verts,faces,uv,5,1)

def grape_leaf(batch,center,normal,length,width,phase,mat):
    """Five-lobed closed leaf prism, real outline and thickness; no opacity card."""
    normal=Vector(normal).normalized();u=normal.cross(Vector((0,0,1))).normalized()
    v=normal.cross(u).normalized();u,v=u*math.cos(phase)+v*math.sin(phase),v*math.cos(phase)-u*math.sin(phase)
    c=Vector(center);n=20;outline=[]
    for i in range(n):
        a=math.tau*i/n;r=.88+.12*math.cos(5*a)
        outline.append((math.cos(a)*r,math.sin(a)*r))
    verts=[c+normal*.0015]
    for x,y in outline:verts.append(c+u*x*width*.5+v*y*length*.5+normal*(.0006+.0005*abs(y)))
    back=len(verts);verts.append(c-normal*.0012)
    for x,y in outline:verts.append(c+u*x*width*.5+v*y*length*.5-normal*.0012)
    faces=[];uv=[]
    for i in range(n):
        ni=(i+1)%n
        faces.extend([(0,1+i,1+ni),(back,back+1+ni,back+1+i),(1+i,back+1+i,back+1+ni,1+ni)])
        a=(.5+outline[i][0]*.5,.5+outline[i][1]*.5);b=(.5+outline[ni][0]*.5,.5+outline[ni][1]*.5)
        uv.extend([[ (.5,.5),a,b],[(.5,.5),b,a],[(i/n,0),(i/n,1),((i+1)/n,1),((i+1)/n,0)]])
    batch.add(verts,faces,uv,mat,10)

def fruit(batch,center,radius):
    # Small closed octahedral subdivision (48 triangles) for restrained fruit clusters.
    c=Vector(center);sides=8;rings=3;verts=[c+Vector((0,0,-radius))]
    for j in range(1,rings+1):
        a=-math.pi/2+j*math.pi/(rings+1);z=math.sin(a)*radius;r=math.cos(a)*radius
        for i in range(sides):
            t=math.tau*i/sides;verts.append(c+Vector((math.cos(t)*r,math.sin(t)*r,z)))
    top=len(verts);verts.append(c+Vector((0,0,radius)))
    faces=[]
    for i in range(sides):faces.append((0,1+(i+1)%sides,1+i))
    for j in range(rings-1):
        for i in range(sides):
            ni=(i+1)%sides;a=1+j*sides;b=a+sides;faces.append((a+i,a+ni,b+ni,b+i))
    for i in range(sides):faces.append((1+(rings-1)*sides+i,1+(rings-1)*sides+(i+1)%sides,top))
    uv=[]
    for f in faces:
        coords=[]
        for i in f:
            p=(verts[i]-c)/radius;coords.append((.5+math.atan2(p.y,p.x)/math.tau,.5+math.asin(max(-1,min(1,p.z)))/math.pi))
        if max(u for u,v in coords)-min(u for u,v in coords)>.5:coords=[(u+1 if u<.5 else u,v) for u,v in coords]
        uv.append(coords)
    batch.add(verts,faces,uv,6,11)

def build(variant,mats,lowest):
    rng=random.Random(PARAMS['seed']+'ABC'.index(variant)*191);batch=Batch()
    canopy(batch,variant,lowest);post(batch)
    for z in (1.28,1.62):wire_support(batch,z)
    for index,y in enumerate(PARAMS['vine_centres_y_m']):
        lean=(.018+.008*'ABC'.index(variant))*(-1 if index==0 else 1)
        pts=[(0,y,0),(lean,y+.013,.30),(-lean*.3,y-.015,.64),(lean*.5,y,.90)]
        tube(batch,pts,[.035,.030,.025,.021],6 if lowest else 10,0,3+index)
        # One cordon per vine, visibly tied along the bottom wire.
        cpts=[(lean*.5,y-.66,.905),(lean*.5,y,.89),(lean*.5,y+.66,.905)] if not lowest else [(lean*.5,y-.66,.905),(lean*.5,y+.66,.905)]
        tube(batch,cpts,[.015]*len(cpts),4 if lowest else 8,0,5)
        if not lowest:
            for j in range(8):
                sy=y-.59+j*1.18/7;dz=rng.uniform(1.70,1.84)
                tube(batch,[(lean*.5,sy,.905),(.06*(-1 if j%2 else 1),sy+rng.uniform(-.045,.045),1.25),(.12*(-1 if j%2 else 1),sy+rng.uniform(-.055,.055),dz)],[.005,.0037,.0024],5,0,6)
            # Two restrained purple clusters per vine, below the leaf wall.
            for bunch in range(2):
                sign=-1 if (bunch+index)%2 else 1;cy=y+(-.22 if bunch==0 else .26);cx=sign*.254
                for berry in range(12):
                    layer=berry//4;angle=math.tau*(berry%4)/4+layer*.65
                    fruit(batch,(cx+math.cos(angle)*(.033-layer*.006),cy+math.sin(angle)*(.033-layer*.006),1.065-layer*.031),rng.uniform(.013,.016))
    for x,z in zip((0,-.285,.285),PARAMS['wire_heights_m']):
        tube(batch,[(x,0,z),(x,3,z)],[.0016,.0016],3 if lowest else 8,2,7)
    if not lowest:
        count=PARAMS['leaf_counts'][variant]
        top_count=120+'ABC'.index(variant)*6;side_count=count-top_count
        for i in range(side_count):
            side=-1 if i%2 else 1
            y=.13+(i//2)/max(1,side_count//2-1)*2.74+rng.uniform(-.023,.023)
            y=min(2.88,max(.12,y));z=.997+rng.random()*.735
            x=side*(.292+rng.uniform(-.008,.008))
            normal=(side,rng.uniform(-.25,.25),rng.uniform(-.20,.35))
            grape_leaf(batch,(x,y,z),normal,rng.uniform(.145,.195),rng.uniform(.142,.190),rng.uniform(-math.pi,math.pi),4 if i%7==0 else 3)
        for i in range(top_count):
            y=.13+i/max(1,top_count-1)*2.74+rng.uniform(-.022,.022)
            y=min(2.88,max(.12,y));x=rng.uniform(-.19,.19);z=rng.uniform(1.745,1.775)
            grape_leaf(batch,(x,y,z),(rng.uniform(-.35,.35),rng.uniform(-.25,.25),1),rng.uniform(.15,.19),rng.uniform(.15,.19),rng.uniform(-math.pi,math.pi),4 if i%9==0 else 3)
    ob=batch.finish('SM_PazFarm_VineRow_3m_'+variant+('_LOD3' if lowest else ''),mats)
    # Enforce flat root ends so leaning trunk cross-sections do not go below ground.
    for vert in ob.data.vertices:
        if vert.co.z<0:vert.co.z=0
    ob['parameters']=json.dumps(PARAMS);ob['variant']=variant;ob['lod']=3 if lowest else 0
    ob['post_count']=1;ob['vine_trunk_count']=2;ob['vine_centres_y_m']=json.dumps(PARAMS['vine_centres_y_m'])
    ob['tiling']='Translate by (0,3,0). Exact shared cap plane; no volume crosses Y=0 or Y=3. Start post occupies Y=0..0.07.'
    ob['material_slots']='0=bark 1=post 2=wire 3=leaf 4=leaf light 5=canopy 6=grape; same order in both LODs.'
    return ob

def png(path,pixels,srgb=False):
    a=np.asarray(np.clip(pixels,0,255),np.uint8);h,w=a.shape[:2]
    def chunk(tag,data):return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,6,0,0,0))
    if srgb:data+=chunk(b'sRGB',b'\0')
    path.write_bytes(data+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+row.tobytes() for row in a),6))+chunk(b'IEND',b''))

def material(tag,rgb,roughness,kind='noise',spec=.08):
    mat=C.pbr(tag,tuple(v/255 for v in rgb),roughness,0,kind='noise',res=1024)
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=1
    bs.inputs['Specular IOR Level'].default_value=spec;bs.inputs['Subsurface Weight'].default_value=0
    mat.use_backface_culling=False;mat['blend_mode_intent']='OPAQUE_TWO_SIDED'
    mat['nominal_rgb_srgb']=rgb;mat['roughness_target']=roughness;mat['specular_target']=spec
    y,x=np.mgrid[0:1024,0:1024]/1023.;rng=np.random.default_rng(len(tag)*79)
    noise=rng.random((1024,1024));height=np.zeros_like(x);tint=.965+.07*noise
    if kind=='bark':
        height=.016*np.sin(x*60+np.sin(y*22)*1.3)+.009*np.sin(x*150+y*8)
        tint=.84+.10*noise+.13*np.sin(x*60+np.sin(y*22)*1.3)**2
    elif kind=='leaf':
        mid=np.exp(-((x-.5)/.012)**2);vein=np.maximum(0,np.cos((y-np.abs(x-.5)*.7)*math.pi*18))**24
        tint=.945+.055*noise+.015*mid+.01*vein;height=.0015*mid+.0003*vein
    elif kind=='canopy':
        tint=.965+.024*np.sin(x*29+y*17)+.016*np.sin(y*39-x*11)+.02*noise
    rgba=np.ones((1024,1024,4),float)*255;rgba[:,:,:3]=np.array(rgb)[None,None,:]*tint[:,:,None]
    base=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_BaseColor.png'))
    png(Path(base.filepath_raw),rgba,True);base.reload();base.colorspace_settings.name='sRGB'
    gy,gx=np.gradient(height);normal=np.stack((-gx*15,-gy*15,np.ones_like(x)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    rgba[:,:,:3]=(normal*.5+.5)*255
    nm=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_Normal.png'))
    png(Path(nm.filepath_raw),rgba);nm.reload();nm.colorspace_settings.name='Non-Color'
    rgba[:,:,0]=255;rgba[:,:,1]=round(roughness*255);rgba[:,:,2]=0
    orm=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_ORM.png'))
    png(Path(orm.filepath_raw),rgba);orm.reload();orm.colorspace_settings.name='Non-Color'
    return mat

def main():
    C.reset()
    mats=[material('Vine_Bark_v004',[87,63,40],.94,'bark'),material('Vine_Post_v004',[113,100,79],.94,'bark'),
          material('Vine_Wire_v004',[76,77,72],.88),material('Vine_Leaf_v004',[49,79,28],.93,'leaf'),
          material('Vine_LeafLight_v004',[57,87,32],.93,'leaf'),material('Vine_Canopy_v004',[47,76,27],.94,'canopy'),
          material('Vine_Grape_v004',[38,28,48],.76,spec=.10)]
    records=[];objects=[]
    for variant in 'ABC':
        for lowest in (False,True):
            raw=build(variant,mats,lowest)
            ob,rec=C.asset(raw.name,[raw],budget=300 if lowest else 40000,nominal=[.65,3,1.9],notes=[
                'VSP grapevine tile; exactly 3m along +Y; ground start-end origin. Two vines at Y=.75/2.25m and one wooden post occupying Y=0..0.07m.',
                'Closed recessed inner canopy from .92 to 1.70m; detailed five-lobed green leaf clusters cover sides/top to approx 1.8m. Three wires; no mask, wind or collision.',
                'Separate final LOD has a slightly expanded closed canopy to stand in for the detailed leaf envelope, plus post, two trunks, cordons and wires. Explicitly assign it as the receiving mesh lowest LOD; importing it as an unrelated mesh is insufficient.',
                'All seven material slots retained in both LODs: bark0, post1, wire2, leaf3, leaf_light4, canopy5, grape6.',
                'Translate tiles by exact 3m pitch. Identical canopy end profiles across A/B/C; internal end caps coincide on a plane only, with no positive-volume inter-tile overlap.',
            ])
            rec['lod']=3 if lowest else 0;rec['lod_index']=rec['lod'];rec['lowest_lod']=lowest
            rec['paired_asset']='SM_PazFarm_VineRow_3m_'+variant+('' if lowest else '_LOD3')
            rec['post_count']=1;rec['vine_trunk_count']=2
            rec['seam_contract']={'y_min':0,'y_max':3,'pitch_m':3,'canopy_shared_end_profile':True,'one_start_post':True,'post_center_y_m':.035,'vine_centres_y_m':[.75,2.25]}
            records.append(rec);objects.append(ob)
            C.preview(ob,rec,azimuth=-54,elevation=21)
            print('VINE_HERO_READY',ob.name,rec['triangles_LOD0'],flush=True)
    C.save_family('VineRows.blend',records,PARAMS)
    C.report('vines_v004.json',records,{'parameters':PARAMS,
        'LODpairing':{f'SM_PazFarm_VineRow_3m_{v}':f'SM_PazFarm_VineRow_3m_{v}_LOD3' for v in 'ABC'},
        'construction':'Seven shared opaque material slots. Each detailed module has a recessed opaque connected canopy, one start post with two wire supports, two trunks/cordons, sixteen shoots, three wires, four restrained grape bunches and 420/432/444 closed five-lobed leaf prisms. Each lowest LOD retains an expanded proxy canopy band, post/supports, two trunks/cordons and three wires.',
        'source':'Original procedural modelling and texture artwork; no photographic pixels copied.',
        'scope':'Offline only. Native import/LOD assignment and actual HLOD rendering remain with the operator.'})
    print('VINE_DELIVERY_COMPLETE',json.dumps([(r['name'],r['triangles_LOD0'],r['size_metres_W_D_H']) for r in records]),flush=True)

def structural_preview():
    """Unobstructed fitted side view; source file is only read, never resaved."""
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend/VineRows.blend'))
    scene=bpy.context.scene;ob=bpy.data.objects['SM_PazFarm_VineRow_3m_A']
    for o in scene.objects:o.hide_render=o!=ob
    floor=C.plain_mat('Vine_Structural_Preview_Floor',(.20,.235,.25))
    C.box('Vine_Structural_Preview_Ground',(0,1.5,-.045),(20,20,.08),floor)
    target=Vector((0,1.5,.94));bpy.ops.object.camera_add(location=(7,1.5,1.8));cam=bpy.context.object
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.8;scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(3,-1,6));lamp=bpy.context.object;lamp.data.energy=1100;lamp.data.size=4
    lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN');lamp=bpy.context.object;lamp.rotation_euler=(.5,-.3,-.5);lamp.data.energy=1.5;lamp.data.angle=.2
    scene.render.filepath=str(ROOT/'Previews/VineRows_Structure_A.png');bpy.ops.render.render(write_still=True)

def verify():
    from collections import Counter
    checks={'assets':[],'joins':[],'textures':[]}
    qa_inputs=[ROOT/'Blend/VineRows.blend']+sorted((ROOT/'FBX').glob('SM_PazFarm_VineRow_3m_*.fbx'))+sorted((ROOT/'Textures').glob('T_PazFarm_Vine_*.png'))
    def input_hashes():return {p.relative_to(ROOT).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in qa_inputs}
    checks['input_hashes']=input_hashes()
    checks['input_hashes_capture']='Captured before this fresh source reopen and FBX QA run; independently rechecked afterward. Not retrofilled into the earlier QA run.'
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend/VineRows.blend'))
    def examine(ob):
        ob.data.calc_loop_triangles();xyz=np.array([v.co[:] for v in ob.data.vertices]);edges=Counter(tuple(sorted(e)) for p in ob.data.polygons for e in p.edge_keys)
        uv=ob.data.uv_layers.get('UV0');faces=[p for p in ob.data.polygons if p.material_index==5]
        ids={i for p in faces for i in p.vertices};points=[ob.data.vertices[i].co for i in ids]
        profiles={str(y):sorted(set((round(float(p.x),6),round(float(p.z),6)) for p in points if abs(p.y-y)<1e-6)) for y in (0,3)}
        def component_boxes(material):
            parent={}
            def find(v):
                parent.setdefault(v,v)
                while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
                return v
            for p in ob.data.polygons:
                if p.material_index==material:
                    for v in p.vertices:parent[find(v)]=find(p.vertices[0])
            groups={}
            for v in list(parent):groups.setdefault(find(v),[]).append(ob.data.vertices[v].co)
            return [[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]] for vs in groups.values()]
        bark_components=component_boxes(0);post_components=component_boxes(1)
        root_trunks=[b for b in bark_components if abs(b[0][2])<1e-6 and b[1][2]>.8]
        canopy_components=component_boxes(5)
        return {'name':ob.name,'triangles':len(ob.data.loop_triangles),'dimensions_metres':(xyz.max(axis=0)-xyz.min(axis=0)).tolist(),
                'bounds_metres':[xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist()],'pivot_metres':list(ob.location),
                'finite_geometry':bool(np.isfinite(xyz).all()),'uv0':uv.name if uv else None,'finite_uv':bool(uv and np.isfinite(np.array([d.uv[:] for d in uv.data])).all()),
                'zero_area_triangles':sum(t.area<1e-12 for t in ob.data.loop_triangles),'boundary_edges':sum(n==1 for n in edges.values()),'nonmanifold_edges':sum(n!=2 for n in edges.values()),
                'material_order':[m.name for m in ob.data.materials],'canopy_end_profiles':profiles,
                'post_count':len(post_components),'vine_trunk_count':len(root_trunks),'canopy_connected_components':len(canopy_components),
                'post_component_bounds':post_components,'grounded_trunk_component_bounds':root_trunks}
    src={ob.name:examine(ob) for ob in bpy.data.objects if ob.type=='MESH' and ob.name.startswith('SM_PazFarm_VineRow_3m_')}
    for im in bpy.data.images:
        if im.source=='FILE':
            path=Path(bpy.path.abspath(im.filepath));pix=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(pix)
            checks['textures'].append({'path':str(path),'exists':path.is_file(),'size':list(im.size),'alpha_min':float(pix[3::4].min()),'relative_path':im.filepath.startswith('//')})
    for lod in ('','_LOD3'):
        for a in 'ABC':
            for b in 'ABC':
                left=src['SM_PazFarm_VineRow_3m_'+a+lod];right=src['SM_PazFarm_VineRow_3m_'+b+lod]
                checks['joins'].append({'left':a+lod,'right':b+lod,'pitch_m':3,'profile_equal':left['canopy_end_profiles']['3']==right['canopy_end_profiles']['0'],
                    'gap_m':right['bounds_metres'][0][1]+3-left['bounds_metres'][1][1],
                    'positive_volume_overlap_possible':left['bounds_metres'][1][1]>3.000001 or right['bounds_metres'][0][1]<-.000001,
                    'cap_coincidence':'The closed end caps coincide only on the join plane; they have no positive-volume overlap.'})
    instances=[];posts=[];trunks=[]
    for row in range(5):
        for tile in range(10):
            var='ABC'[(row+tile)%3];x=(row-2)*2.75;y=tile*3
            instances.append({'variant':var,'translation_m':[x,y,0]});posts.append((x,y+.035));trunks.extend([(x,y+.75),(x,y+2.25)])
    checks['mixed_block']={'layout':'5 rows x 10 mixed A/B/C tiles; +Y pitch3m, row pitch2.75m','instances':instances,'post_count':len(posts),'unique_post_locations':len(set(posts)),
        'vine_trunk_count':len(trunks),'unique_vine_locations':len(set(trunks)),'row_end_m':30,'post_pitch_m':3,'vine_pitch_m':1.5,
        'post_count_from_source_geometry':sum(src['SM_PazFarm_VineRow_3m_'+i['variant']]['post_count'] for i in instances),
        'trunk_count_from_source_geometry':sum(src['SM_PazFarm_VineRow_3m_'+i['variant']]['vine_trunk_count'] for i in instances),
        'pass':len(posts)==len(set(posts))==50 and len(trunks)==len(set(trunks))==100 and all(s['post_count']==1 and s['vine_trunk_count']==2 for s in src.values())}
    for name,s in src.items():
        C.reset();bpy.ops.import_scene.fbx(filepath=str(ROOT/'FBX'/(name+'.fbx')),use_anim=False);f=examine(bpy.data.objects[name]);low=name.endswith('_LOD3')
        passed=True
        for v in (s,f):
            passed &= v['finite_geometry'] and v['finite_uv'] and v['uv0']=='UV0' and v['zero_area_triangles']==0 and v['nonmanifold_edges']==0 and v['post_count']==1 and v['vine_trunk_count']==2 and v['canopy_connected_components']==1
            passed &= max(abs(x) for x in v['pivot_metres'])<1e-6 and abs(v['bounds_metres'][0][1])<1e-6 and abs(v['bounds_metres'][1][1]-3)<1e-6 and abs(v['bounds_metres'][0][2])<1e-6
            passed &= (100<=v['triangles']<=300) if low else (15000<=v['triangles']<=40000)
        passed &= s['triangles']==f['triangles'] and s['material_order']==f['material_order'] and max(abs(a-b) for a,b in zip(s['dimensions_metres'],f['dimensions_metres']))<1e-5
        checks['assets'].append({'source':s,'fresh_fbx':f,'pass':bool(passed)})
    checks['input_hashes_unchanged']=checks['input_hashes']==input_hashes()
    checks['pass']=all(a['pass'] for a in checks['assets']) and all(j['profile_equal'] and abs(j['gap_m'])<1e-6 and not j['positive_volume_overlap_possible'] for j in checks['joins']) and checks['mixed_block']['pass'] and all(t['exists'] and t['size']==[1024,1024] and t['alpha_min']==1 and t['relative_path'] for t in checks['textures']) and checks['input_hashes_unchanged']
    checks['limits']='Offline geometry and source/FBX verification. Root supplies fixed-camera distance evidence; no native editor or HLOD acceptance is inferred.'
    (ROOT/'Reports/vines_v004_qa.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('VINES_V004_QA',checks['pass'],flush=True)
    if not checks['pass']:raise RuntimeError('Vine QA failed')

if __name__=='__main__':
    if '--verify-only' in sys.argv:verify()
    elif '--structure-only' in sys.argv:structural_preview()
    else:main()
