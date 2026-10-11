"""Original Mediterranean field grass for the offline FieldCrops_v004 delivery.

Creates small closed backing tufts in LOD0 and independently expands their
lowest-LOD counterparts to replace missing blade coverage. No masked cards,
wind, collision or external assets.
Only this revision's grass outputs are written. Common helper remains unchanged.
"""
import bpy, bmesh, math, json, random, sys, os, argparse, hashlib, struct, zlib, binascii
from pathlib import Path
from mathutils import Vector
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
import paz_common as pc
os.environ['TEMP']=os.environ['TMP']=str(ROOT/'Temp')
ap=argparse.ArgumentParser()
ap.add_argument('--heroes',choices=['first','all','none'],default='all')
ap.add_argument('--render-only',action='store_true',help='Read existing source; update only fitted preview PNGs.')
ap.add_argument('--only',default='',help='Optional comma-separated object names for fitted previews.')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

CONFIG=[
 {'suffix':'Clump_A','size':[.36,.32,.28],'fans':18,'blades':114,'heads':2,'oat':False,'green':.05,'weeds':1,'seed':411},
 {'suffix':'Clump_B','size':[.52,.45,.51],'fans':17,'blades':130,'heads':3,'oat':False,'green':.07,'weeds':1,'seed':412},
 {'suffix':'Clump_C','size':[.67,.55,.68],'fans':17,'blades':145,'heads':3,'oat':True,'green':.06,'weeds':1,'seed':413},
 {'suffix':'Clump_D','size':[.85,.73,.78],'fans':17,'blades':160,'heads':3,'oat':False,'green':.10,'weeds':2,'seed':414},
 {'suffix':'Clump_E','size':[.39,.34,.25],'fans':18,'blades':115,'heads':2,'oat':False,'green':.90,'weeds':3,'seed':415},
 {'suffix':'Clump_F','size':[.64,.56,.55],'fans':17,'blades':145,'heads':3,'oat':True,'green':.80,'weeds':3,'seed':416},
 {'suffix':'Patch_2m_A','size':[2.,2.,.60],'patch':True,'green':.08,'seed':421},
 {'suffix':'Patch_2m_B','size':[2.,2.,.63],'patch':True,'green':.42,'seed':422},
]
PALETTE=[
 {'name':'Grass_Dry','srgb':[145,122,78],'roughness':.94,'description':'subdued dry golden straw'},
 {'name':'Grass_Straw','srgb':[177,151,99],'roughness':.96,'description':'restrained pale straw and seed husks'},
 {'name':'Grass_Green','srgb':[77,96,47],'roughness':.89,'description':'living olive-green annual grass and weeds'},
 {'name':'Grass_Stem','srgb':[112,89,53],'roughness':.98,'description':'dry stems and darker seed details'},
]
PALETTE += [dict(p,name=p['name']+'_Low',texture_parent=p['name'],linear_albedo_multiplier=.70,
                 description=p['description']+'; calibrated lowest proxy') for p in PALETTE[:]]
LOW_PROXY={'clump':{'width':1.6,'depth':1.3,'height':1.0},
           'patch':{'width':3.0,'depth':2.2,'height':1.9}}
for cfg in CONFIG:
    if cfg['suffix'] in ('Clump_B','Clump_C','Clump_D'):
        cfg['low_proxy']={'width':2.0,'depth':1.6,'height':1.0}

def png(path,a,srgb=False):
    a=np.asarray(a,np.uint8);h,w=a.shape[:2]
    def chunk(t,d):return struct.pack('!I',len(d))+t+d+struct.pack('!I',binascii.crc32(t+d)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,6,0,0,0))
    if srgb:data+=chunk(b'sRGB',b'\0')
    data+=chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r.tobytes() for r in a),6))+chunk(b'IEND',b'')
    path.write_bytes(data)

def material(spec,idx):
    n=1024; yy,xx=np.mgrid[0:n,0:n]/(n-1)
    rng=np.random.default_rng(100+idx%4)
    texture_noise=rng.random((n,n))-.5
    variation=.985+.025*np.sin(xx*math.pi*27)+.018*texture_noise+.012*np.sin(yy*math.pi*4)
    color=np.empty((n,n,4),np.uint8)
    color[:,:,:3]=np.rint(np.clip(np.array(spec['srgb'])*variation[...,None],0,255)).astype(np.uint8)
    if spec.get('linear_albedo_multiplier'):
        c=color[:,:,:3].astype(np.float64)/255
        linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)*spec['linear_albedo_multiplier']
        c=np.where(linear<=.0031308,linear*12.92,1.055*linear**(1/2.4)-.055)
        color[:,:,:3]=np.rint(np.clip(c*255,0,255)).astype(np.uint8)
    color[:,:,3]=255
    # Subtle original longitudinal blade grain; no photographed pixels.
    nx=.025*np.cos(xx*math.pi*27); ny=.006*np.cos(yy*math.pi*4)
    normal=np.ones((n,n,4),np.uint8)*255
    v=np.stack((nx,ny,np.ones_like(nx)),axis=-1);v/=np.linalg.norm(v,axis=-1,keepdims=True)
    normal[:,:,:3]=np.rint((v*.5+.5)*255).astype(np.uint8)
    orm=np.ones((n,n,4),np.uint8)*255
    orm[:,:,0]=255;orm[:,:,1]=round(spec['roughness']*255);orm[:,:,2]=0
    files=[];images=[]
    for suffix,array,is_srgb in [('BaseColor',color,True),('Normal',normal,False),('ORM',orm,False)]:
        texture_name=spec.get('texture_parent',spec['name']) if suffix!='BaseColor' else spec['name']
        path=ROOT/'Textures'/('T_PazFarm_'+texture_name+'_'+suffix+'.png')
        if suffix=='BaseColor' or not spec.get('texture_parent'):png(path,array,is_srgb)
        files.append(path.relative_to(ROOT).as_posix())
        im=bpy.data.images.load(str(path),check_existing=False)
        im.colorspace_settings.name='sRGB' if is_srgb else 'Non-Color';images.append(im)
    m=bpy.data.materials.new('M_PazFarm_'+spec['name']);m.use_nodes=True;m.use_backface_culling=False
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    base=nt.nodes.new('ShaderNodeTexImage');base.image=images[0];nt.links.new(base.outputs['Color'],bs.inputs['Base Color'])
    texn=nt.nodes.new('ShaderNodeTexImage');texn.image=images[1]
    nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.35
    nt.links.new(texn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    texo=nt.nodes.new('ShaderNodeTexImage');texo.image=images[2]
    sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(texo.outputs['Color'],sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    bs.inputs['Alpha'].default_value=1;bs.inputs['Specular IOR Level'].default_value=.10
    bs.inputs['Subsurface Weight'].default_value=0
    m['texture_files']=json.dumps(files);m['blend_mode_intent']='OPAQUE_TWO_SIDED';m['licence']='CC0-1.0'
    m['source']='Original procedural grass materials, no external images or satellite pixels'
    m['orm_channels']='R=AO G=Roughness B=Metallic';m['normal_convention']='OpenGL +Y'
    m['srgb_palette_bytes']=json.dumps(spec['srgb'])
    m['linear_albedo_multiplier']=spec.get('linear_albedo_multiplier',1.)
    return m

class Geo:
    def __init__(self):self.v=[];self.f=[];self.mi=[]
    def append(self,verts,faces,mat):
        start=len(self.v);self.v.extend([tuple(map(float,p)) for p in verts])
        self.f.extend([[start+i for i in face] for face in faces]);self.mi.extend([mat]*len(faces))
    def copy(self):
        g=Geo();g.v=list(self.v);g.f=[list(f) for f in self.f];g.mi=list(self.mi);return g
    def tetra(self,base,width,depth,tip,az,mat):
        b=Vector(base);side=Vector((math.cos(az),math.sin(az),0));back=Vector((-math.sin(az),math.cos(az),0))
        verts=[b-side*width/2,b+side*width/2,b+back*depth,Vector(tip)]
        self.append(verts,[(0,2,1),(0,1,3),(1,2,3),(2,0,3)],mat)
    def rod(self,a,b,r,mat):
        a,b=Vector(a),Vector(b);t=(b-a).normalized()
        s=t.cross(Vector((0,1,0))).normalized()
        if s.length<.01:s=t.cross(Vector((1,0,0))).normalized()
        q=t.cross(s).normalized()
        v=[]
        for p,rad in ((a,r),(b,r*.72)):
            v.extend([p+s*(math.cos(k*math.tau/3)*rad)+q*(math.sin(k*math.tau/3)*rad) for k in range(3)])
        self.append(v,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],mat)
    def blade(self,root,tip,width,mat,curved=False):
        a,b=Vector(root),Vector(tip);d=b-a
        if Vector((d.x,d.y,0)).length<.001:d.x+=.02
        side=Vector((-d.y,d.x,0)).normalized();t=d.normalized();thick=t.cross(side).normalized()
        if thick.z<0:thick=-thick
        mid=a+Vector((d.x*.55,d.y*.55,d.z*1.06))
        sections=[(a,width*.35),(mid,width)]
        if curved:
            sections=[(a,width*.32),(a+Vector((d.x*.4,d.y*.4,d.z*.65)),width),(a+Vector((d.x*.78,d.y*.78,d.z*1.10)),width*.45)]
        verts=[]
        for p,w in sections:
            verts.extend([p-side*w/2,p+side*w/2,p+thick*max(.0004,width*.07)])
        tip_index=len(verts);verts.append(b);faces=[(0,2,1)]
        for ring in range(len(sections)-1):
            start=ring*3;next_start=start+3
            for k in range(3):faces.append((start+k,start+(k+1)%3,next_start+(k+1)%3,next_start+k))
        start=(len(sections)-1)*3
        for k in range(3):faces.append((start+k,start+(k+1)%3,tip_index))
        self.append(verts,faces,mat)
    def leaf(self,root,tip,width,mat):
        a,b=Vector(root),Vector(tip);d=b-a;s=Vector((-d.y,d.x,0)).normalized()
        middle=(a+b)/2;top=middle+Vector((0,0,.002));bottom=middle-Vector((0,0,.0015))
        self.append([a,middle+s*width/2,b,middle-s*width/2,top,bottom],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],mat)
    def kernel(self,center,radius,height,mat):
        p=Vector(center)
        self.append([p+Vector((-radius,0,0)),p+Vector((0,-radius,0)),p+Vector((radius,0,0)),p+Vector((0,radius,0)),p+Vector((0,0,height/2)),p-Vector((0,0,height/2))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],mat)
    def transform(self,sx,sy,sz):self.v=[(x*sx,y*sy,z*sz) for x,y,z in self.v]

def choose_mat(rng,green,highlight=.19):
    f=rng.random()
    return 2 if f<green else (1 if f<green+highlight*(1-green) else 0)

def add_seed(g,root,top,oat,rng):
    """A small solid barley awn spike or loose, drooping oat panicle."""
    root,top=Vector(root),Vector(top);height=top.z-root.z
    root.z=max(root.z,.003)
    stem_top=top-Vector((0,0,height*.11));g.rod(root,stem_top,max(.0008,height*.0026),3)
    if oat:
        for k in range(4):
            t=.55+k*.105;branch=root+(stem_top-root)*t
            az=rng.uniform(0,math.tau);reach=height*rng.uniform(.10,.17)
            knee=branch+Vector((math.cos(az)*reach*.7,math.sin(az)*reach*.7,height*.09))
            end=knee+Vector((math.cos(az)*reach*.3,math.sin(az)*reach*.3,-height*.075))
            g.rod(branch,knee,.00065,3);g.rod(knee,end,.0006,3)
            g.kernel(end,height*.012,height*.062,1)
    else:
        for k in range(5):
            p=stem_top+Vector((0,0,height*.011*k))
            az=k*2.4+rng.random()*.3
            p+=Vector((math.cos(az)*height*.012,math.sin(az)*height*.012,0))
            g.kernel(p,height*.011,height*.031,1)
            awntip=Vector((p.x+math.cos(az)*height*.045,p.y+math.sin(az)*height*.045,min(top.z,p.z+height*.063)))
            g.tetra(p,height*.004,height*.002,awntip,az,1)

def add_weeds(g,rng,diam,height,count):
    for w in range(count):
        az=rng.uniform(0,math.tau);r=diam*rng.uniform(.13,.28)
        root=Vector((r*math.cos(az),r*math.sin(az),height*.10))
        for k in range(4):
            a=az+k*math.tau/4+rng.uniform(-.25,.25)
            length=diam*rng.uniform(.10,.18)
            tip=root+Vector((math.cos(a)*length,math.sin(a)*length,height*rng.uniform(.06,.16)))
            g.leaf(root,tip,length*.37,2)

def clump(cfg):
    rng=random.Random(cfg['seed']);diam=cfg['size'][0];height=cfg['size'][2]
    low=Geo();cores=[]
    # Closed, pointed backing fans, not round balls or a footprint slab.
    for i in range(cfg['fans']):
        az=i*math.tau/cfg['fans']+rng.uniform(-.2,.2)
        base=Vector((math.cos(az)*diam*.11,math.sin(az)*diam*.11,0))
        tip=Vector((math.cos(az)*diam*rng.uniform(.36,.45),math.sin(az)*diam*rng.uniform(.34,.43),height*rng.uniform(.38,.61)))
        mat=choose_mat(rng,cfg['green'])
        low.tetra(base,diam*rng.uniform(.045,.075),diam*.025,tip,az+math.pi/2,mat)
        cores.append((base,tip))
    seeds=[]
    for i in range(cfg['heads']):
        az=i*2.4+rng.uniform(0,1)
        root=Vector((diam*.12*math.cos(az),diam*.12*math.sin(az),0))
        top=Vector((diam*.25*math.cos(az+.3),diam*.25*math.sin(az+.3),height*(1 if i==0 else rng.uniform(.82,.96))))
        low.tetra(root,.007+diam*.005,.006,top,az,0 if cfg['green']<.5 else 2)
        seeds.append((root,top))
    high=low.copy()
    for i in range(cfg['blades']):
        az=i*2.399963+rng.uniform(-.12,.12)
        rr=diam*rng.uniform(.015,.18)
        root=Vector((math.cos(az)*rr,math.sin(az)*rr,0))
        reach=diam*rng.uniform(.28,.46)
        tip=Vector((math.cos(az)*reach,math.sin(az)*reach,height*rng.uniform(.25,.77)))
        high.blade(root,tip,diam*rng.uniform(.007,.016),choose_mat(rng,cfg['green']),curved=True)
    for root,top in seeds:add_seed(high,root,top,cfg['oat'],rng)
    add_weeds(high,rng,diam,height,cfg['weeds'])
    return low,high

def patch(cfg):
    rng=random.Random(cfg['seed']);low=Geo();centers=[]
    for row in range(5):
        for col in range(4):
            center=Vector(((col-1.5)*.47+rng.uniform(-.035,.035),(row-2)*.36+rng.uniform(-.035,.035),0))
            centers.append(center)
            az=(row*1.7+col*2.1)+rng.uniform(-.2,.2)
            tip=center+Vector((math.cos(az)*rng.uniform(.09,.14),math.sin(az)*rng.uniform(.09,.14),rng.uniform(.13,.21)))
            # One slim upper spear retains the full-height seed-stem envelope.
            if row==2 and col==1:
                tip=center+Vector((.045,.025,cfg['size'][2]));width,depth=.018,.009
            else:width,depth=rng.uniform(.12,.17),rng.uniform(.04,.065)
            low.tetra(center,width,depth,tip,az+math.pi/2,choose_mat(rng,cfg['green']))
    high=low.copy()
    for n,center in enumerate(centers):
        for i in range(28):
            az=i*2.399963+n*.62+rng.uniform(-.16,.16)
            root=center+Vector((math.cos(az)*rng.uniform(.005,.1),math.sin(az)*rng.uniform(.005,.1),0))
            reach=rng.uniform(.17,.29)
            tip=center+Vector((math.cos(az)*reach,math.sin(az)*reach,rng.uniform(.18,.48)))
            high.blade(root,tip,rng.uniform(.012,.023),choose_mat(rng,cfg['green']))
        for j in range(1):
            root=center+Vector((rng.uniform(-.08,.08),rng.uniform(-.08,.08),0))
            top=center+Vector((rng.uniform(-.12,.12),rng.uniform(-.12,.12),cfg['size'][2]*rng.uniform(.81,.98)))
            add_seed(high,root,top,bool((n+j)%3==0),rng)
        if n%5==0:
            for k in range(4):
                az=k*math.pi/2+n
                root=center+Vector((0,0,.07));tip=root+Vector((math.cos(az)*.17,math.sin(az)*.17,.045))
                high.leaf(root,tip,.055,2)
    return low,high

def object_from(g,name,mats):
    ob=pc.mesh(name,g.v,g.f,None,smooth=False)
    for m in mats:ob.data.materials.append(m)
    for p,mi in zip(ob.data.polygons,g.mi):p.material_index=mi
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob.data.update()
    return ob

def expand_low_proxy(g,cfg):
    """Independent solid proxy replacing removed blades, never a facing card."""
    profile=cfg.get('low_proxy',LOW_PROXY['patch' if cfg.get('patch') else 'clump'])
    for n in range(len(g.v)//4):
        if not cfg.get('patch') and n>=cfg['fans']:continue
        k=n*4;v=[Vector(p) for p in g.v[k:k+4]];base=(v[0]+v[1])/2
        if cfg.get('patch') and n==9:
            side=(v[1]-v[0]).normalized();back=(v[2]-base).normalized()
            v[0]=base-side*.18;v[1]=base+side*.18;v[2]=base+back*.22
            g.v[k:k+4]=[tuple(p) for p in v]
            continue
        v[0]=base+(v[0]-base)*profile['width'];v[1]=base+(v[1]-base)*profile['width']
        v[2]=base+(v[2]-base)*profile['depth']
        v[3].z=base.z+(v[3].z-base.z)*profile['height']
        g.v[k:k+4]=[tuple(p) for p in v]
    g.mi=[i+4 for i in g.mi]

def mesh_qa(ob):
    ob.data.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(ob.data)
    info={'triangles':len(ob.data.loop_triangles),'vertices':len(ob.data.vertices),
          'zero_area_triangles':sum(t.area<1e-12 for t in ob.data.loop_triangles),
          'finite_vertices':all(math.isfinite(c) for v in ob.data.vertices for c in v.co),
          'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
          'UV0_present':bool(ob.data.uv_layers) and ob.data.uv_layers.active.name=='UV0',
          'min_z_m':min(v.co.z for v in ob.data.vertices),'pivot_m':list(ob.location),
          'material_slots':[m.name for m in ob.data.materials]}
    bm.free();return info

def hero(ob,rec):
    scene=bpy.context.scene;old={o:o.hide_render for o in scene.objects}
    for o in scene.objects:o.hide_render=(o!=ob)
    tmp=[];bounds=pc.bounds(ob);target=Vector([(bounds[0][k]+bounds[1][k])/2 for k in range(3)])
    extent=max(bounds[1][k]-bounds[0][k] for k in range(3));extent=max(extent,.4)
    floor=pc.plain_mat('Grass_Preview_Floor',(.055,.067,.075))
    tmp.append(pc.box('Grass_Preview_Floor',(0,0,-.023),(extent*200,extent*200,.04),floor))
    az,el=math.radians(-55),math.radians(26)
    bpy.ops.object.camera_add(location=target+Vector((math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)))*extent*4)
    cam=bpy.context.object;tmp.append(cam);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';scene.camera=cam;bpy.context.view_layer.update()
    camera_inverse=cam.matrix_world.inverted();pts=[camera_inverse@(ob.matrix_world@Vector(p)) for p in ob.bound_box]
    ww=max(p.x for p in pts)-min(p.x for p in pts);hh=max(p.y for p in pts)-min(p.y for p in pts)
    cam.data.ortho_scale=max(hh,ww/1.2)*1.33
    bpy.ops.object.light_add(type='AREA',location=target+Vector((-extent,-extent,extent*2)))
    light=bpy.context.object;tmp.append(light);light.data.energy=120*extent*extent;light.data.size=extent*1.5
    light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;tmp.append(sun);sun.data.energy=1.4;sun.data.angle=.2;sun.rotation_euler=(.5,-.3,-.5)
    scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.filepath=str(ROOT/rec['preview']);bpy.ops.render.render(write_still=True)
    for o in tmp:bpy.data.objects.remove(o,do_unlink=True)
    for o,val in old.items():o.hide_render=val
    scene.camera=None

if args.render_only:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend'/'FieldGrass.blend'))
    existing=json.loads((ROOT/'Reports'/'grass_v004.json').read_text())['assets']
    priority={'SM_PazFarm_GrassPatch_2m_A':0,'SM_PazFarm_GrassPatch_2m_A_LOD3':1,'SM_PazFarm_GrassClump_E':2,'SM_PazFarm_GrassClump_E_LOD3':3}
    for rec in sorted(existing,key=lambda r:priority.get(r['name'],4)):
        if args.heroes=='none':continue
        if args.only and rec['name'] not in args.only.split(','):continue
        if args.heroes=='first' and not rec['name'].startswith('SM_PazFarm_GrassClump_A'):continue
        hero(bpy.data.objects[rec['name']],rec)
        print('GRASS_HERO',rec['preview'],flush=True)
    print('GRASS_HERO_ONLY_COMPLETE',flush=True)
    sys.exit(0)

pc.reset();MATS=[material(p,i) for i,p in enumerate(PALETTE)]
records=[];pairs=[];objects=[];qa=[]
for cfg in CONFIG:
    low,high=patch(cfg) if cfg.get('patch') else clump(cfg)
    expand_low_proxy(low,cfg)
    # Common scale normalizes the authored envelope without changing the pair's
    # relation or adding an oversized coarse footprint.
    arr=np.array(high.v);size=arr.max(0)-arr.min(0)
    scale=[cfg['size'][i]/size[i] for i in range(3)]
    high.transform(*scale);low.transform(*scale)
    # Re-centre BOTH geometries on the LOD0 footprint; ground contact stays z=0.
    arr=np.array(high.v);cx=(arr[:,0].min()+arr[:,0].max())/2;cy=(arr[:,1].min()+arr[:,1].max())/2
    for g in (high,low):g.v=[(x-cx,y-cy,z) for x,y,z in g.v]
    high_min=np.min(high.v,axis=0);high_max=np.max(high.v,axis=0)
    low.v=[tuple(np.minimum(high_max,np.maximum(high_min,p))) for p in low.v]
    base='SM_PazFarm_Grass'+cfg['suffix']
    produced={}
    for lod,g,budget in [('LOD0',high,8000 if cfg.get('patch') else 3000),('LOD3',low,80)]:
        name=base+('_LOD3' if lod=='LOD3' else '')
        ob=object_from(g,name,MATS)
        note=['Original late-September Mediterranean field grass: solid bent blades, small closed backing tufts and seed heads.',
              'Pivot at ground centre; metres; FBX -Y forward / Z up. No wind or collision.',
              'No alpha cards. BaseColor alpha=1; opaque two-sided materials. Normal OpenGL +Y.',
              'LOD3 uses independent expanded closed tuft proxies to replace the fine blade coverage; LOD0 keeps smaller inner backing tufts.',
              'Fitted hero preview is not a fixed-distance preview; root supplies separate distance frames.']
        if lod=='LOD3':note+=['Lowest LOD uses closed pointed tuft volumes, never billboard cards; full patch/clump budget is 20–80 triangles.']
        ob,rec=pc.asset(name,[ob],pivot=(0,0,0),notes=note,budget=budget,nominal=cfg['size'])
        rec['lod_level']=lod;rec['source_family']='field_grass';rec['grass_type']='patch' if cfg.get('patch') else 'clump'
        rec['appearance']='golden/green mixture' if cfg.get('patch') and cfg['green']>.2 else ('greener annual grasses and weeds' if cfg['green']>.5 else 'mostly dry golden annual grasses')
        rec['lowest_lod_pair']=base+'_LOD3';rec['material_slot_order']=[m.name for m in MATS]
        rec['triangles']=rec['triangles_LOD0'];rec['blend']='Blend/FieldGrass.blend'
        q=mesh_qa(ob);q['name']=name;q['budget']=budget
        assert q['finite_vertices'] and q['zero_area_triangles']==0 and q['boundary_edges']==0 and q['nonmanifold_edges']==0,q
        assert q['UV0_present'] and abs(q['min_z_m'])<1e-7 and q['pivot_m']==[0.,0.,0.],q
        assert (20<=q['triangles']<=80) if lod=='LOD3' else ((3000 if cfg.get('patch') else 300)<=q['triangles']<=budget),q
        records.append(rec);objects.append(ob);qa.append(q);produced[lod]=(ob,rec)
    pairs.append({'base':base,'high':base,'low':base+'_LOD3','high_triangles':produced['LOD0'][1]['triangles'],'low_triangles':produced['LOD3'][1]['triangles'],'same_material_slots':True,'backing_geometry':'small high inner tufts; separate expanded low proxies replace outer blade coverage','low_proxy_scale':cfg.get('low_proxy',LOW_PROXY['patch' if cfg.get('patch') else 'clump']),'low_linear_albedo_multiplier':.70,'parameters':cfg})
    print('GRASS_BUILT',json.dumps(pairs[-1]),flush=True)

# Source stores all models at their ground-centred origins; open showing A only.
for ob in objects:
    visible=ob.name=='SM_PazFarm_GrassClump_A'
    ob.hide_render=not visible;ob.hide_set(not visible)
pc.save_family('FieldGrass.blend',records,{'variants':CONFIG,'palette_srgb':PALETTE,'lowest_lod_strategy':'80 triangles, independent closed pointed proxy tufts replacing high blade coverage; high retains smaller inner backing','low_proxy':LOW_PROXY,'source_visibility':'A high is visible; other variants and all lows are hidden at their original ground-centred origins'})

def reports():
    extra={'parameters':CONFIG,'palette_srgb':PALETTE,'pairings':pairs,
           'source_licence':'CC0-1.0 original procedural modelling and textures; no image copying',
           'fbx_axes':{'forward':'-Y','up':'Z','units':'metres, FBX Units Scale'},
           'material_slots':[m.name for m in MATS],'material_count':len(MATS),'texture_count':16,
           'image_encoding':'BaseColor explicit sRGB PNG bytes; Normal/ORM are linear data; all alpha bytes255',
           'source':'Blend/FieldGrass.blend','heroes_requested':args.heroes}
    pc.report('grass_v004.json',records,extra)
    (ROOT/'Reports'/'grass_v004_qa.json').write_text(json.dumps({'status':'PASS_SOURCE_GEOMETRY','assets':qa,'pairings':pairs,'opaque_foliage':True,'two_sided':True,'texture_alpha_min_max':[255,255],'uv0':True,'normal_convention':'OpenGL +Y','no_wind':True,'no_collision':True,'native_checks_performed':False,'fresh_FBX_roundtrip':'root independent validation, not claimed by this source report'},indent=2)+'\n')
reports()
if args.heroes!='none':
    for ob,rec in zip(objects,records):
        if args.heroes=='first' and not ob.name.startswith('SM_PazFarm_GrassClump_A'):continue
        hero(ob,rec);print('GRASS_HERO',rec['preview'],flush=True)
print('GRASS_COMPLETE',json.dumps({'assets':len(records),'pairings':len(pairs),'high_triangles':[p['high_triangles'] for p in pairs],'low_triangles':[p['low_triangles'] for p in pairs]}),flush=True)
