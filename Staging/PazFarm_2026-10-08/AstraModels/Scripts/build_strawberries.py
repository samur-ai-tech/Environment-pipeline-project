"""Paz Farm editable strawberry/tunnel family. Original procedural geometry.

Blender axes: front -Y, up Z, metre units. Tile along +Y from 0 to 4.
Parameters below are deliberately explicit for operator revision.
"""
import bpy, math, random, json, sys
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Scripts'))

PARAMS = {
    'seed': 5082026,
    'bed_length_m': 4.0, 'bed_width_m': .8, 'bed_height_m': .25,
    'plants_per_row': 12, 'rows': 2, 'row_offset_m': .19,
    'leaf_canopy_height_above_bed_m': .20,
    'tunnel_width_m': 1.2, 'tunnel_height_m': 1.0, 'tunnel_length_m': 4.0,
    'tunnel_hoop_pitch_m': 1.0, 'include_terminal_hoop': False,
    'notes': 'End hoop excluded from repeating tunnel. Duplicate start hoop at Y=4 only at the terminal end of an assembled run.',
}

class MeshBatch:
    def __init__(self): self.v=[]; self.f=[]; self.uv=[]; self.mi=[]
    def add(self, verts, faces, uvs=None, material=0):
        start=len(self.v); self.v.extend(tuple(p) for p in verts)
        for f in faces:
            self.f.append(tuple(start+i for i in f)); self.mi.append(material)
            self.uv.append([uvs[i] if uvs else (verts[i][0],verts[i][1]) for i in f])
    def finish(self, name, materials, smooth=False):
        mesh=bpy.data.meshes.new(name+'_Mesh'); mesh.from_pydata(self.v,[],self.f); mesh.update()
        obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj)
        for mat in materials: mesh.materials.append(mat)
        layer=mesh.uv_layers.new(name='UV0')
        for p,uv,mi in zip(mesh.polygons,self.uv,self.mi):
            p.material_index=mi; p.use_smooth=smooth
            for li,co in zip(p.loop_indices,uv): layer.data[li].uv=co
        obj['source_parameters_json']=json.dumps(PARAMS,sort_keys=True)
        obj['original_geometry']='Original authored procedural geometry for Paz Farm, 2026-10-08'
        return obj

def cylinder(batch,a,b,r,segments=6,material=0,cap=True):
    a,b=Vector(a),Vector(b); axis=(b-a).normalized()
    helper=Vector((0,0,1)) if abs(axis.z)<.92 else Vector((0,1,0))
    u=axis.cross(helper).normalized(); v=axis.cross(u).normalized()
    verts=[]; uv=[]
    for n,p in enumerate((a,b)):
        for i in range(segments):
            ang=2*math.pi*i/segments
            verts.append(p+r*(u*math.cos(ang)+v*math.sin(ang))); uv.append((i/segments,n))
    faces=[]
    for i in range(segments):
        j=(i+1)%segments; faces.append((i,j,segments+j,segments+i))
    if cap: faces.extend([tuple(reversed(range(segments))),tuple(range(segments,2*segments))])
    batch.add(verts,faces,uv,material)

def leaf(batch,base,direction,length,width,material=0,roll=0):
    """Geometric toothed silhouette and gently cupped midrib; UV is botanical leaf space."""
    base=Vector(base); d=Vector(direction).normalized()
    side=d.cross(Vector((0,0,1))).normalized()
    normal=side.cross(d).normalized()
    if roll: side,normal=side*math.cos(roll)+normal*math.sin(roll),normal*math.cos(roll)-side*math.sin(roll)
    # Twelve triangular serrations on each leaf margin, real geometry rather than alpha-only cards.
    verts=[base]; uv=[(.5,0)]
    rings=11
    for j in range(1,rings):
        t=j/rings; profile=(math.sin(math.pi*t)**.7)*(0.80+0.20*t)
        tooth=1.0 if j%2 else .83
        center=base+d*(length*t)+normal*(length*.095*math.sin(math.pi*t))
        w=width*.5*profile*tooth
        verts.extend([center-side*w-normal*w*.12,center,center+side*w-normal*w*.12])
        uv.extend([(.5-.5*profile*tooth,t),(.5,t),(.5+.5*profile*tooth,t)])
    tip=base+d*length+normal*(-length*.065); tip_i=len(verts); verts.append(tip);uv.append((.5,1))
    faces=[(0,1,2),(0,2,3)]
    for j in range(rings-2):
        n=1+3*j; m=n+3
        faces.extend([(n,m,m+1,n+1),(n+1,m+1,m+2,n+2)])
    last=1+3*(rings-2); faces.extend([(last,tip_i,last+1),(last+1,tip_i,last+2)])
    batch.add(verts,[tuple(reversed(f)) for f in faces],uv,material)

def berry(batch,center,size=.019,material=0,seed_count=10):
    """Downward-pointing strawberry with broad shoulder and UV seed ellipses."""
    center=Vector(center); vertices=[]; uv=[]; sides=10; rings=6
    vertices.append(center+Vector((0,0,-size*1.15)));uv.append((.5,0))
    for j in range(1,rings):
        t=j/rings; rad=size*(math.sin(math.pi*t)**.58)*(0.56+.56*t)
        for i in range(sides):
            a=math.tau*i/sides;vertices.append(center+Vector((rad*math.cos(a),rad*math.sin(a),size*(2*t-1.15))));uv.append((i/sides,t))
    top=len(vertices);vertices.append(center+Vector((0,0,size*.85)));uv.append((.5,1))
    faces=[]
    for i in range(sides): faces.append((0,1+(i+1)%sides,1+i))
    for j in range(rings-2):
        a=1+j*sides;b=a+sides
        for i in range(sides):ni=(i+1)%sides;faces.append((a+i,a+ni,b+ni,b+i))
    a=1+(rings-2)*sides
    for i in range(sides):faces.append((a+i,a+(i+1)%sides,top))
    batch.add(vertices,faces,uv,material)
    for coords in batch.uv[-len(faces):]:
        if max(p[0] for p in coords)-min(p[0] for p in coords)>.5:
            for idx,p in enumerate(coords):
                if p[0]<.5:coords[idx]=(p[0]+1,p[1])

def calyx_blade(batch,base,direction,length,width,material=0):
    base=Vector(base);d=Vector(direction).normalized();side=d.cross(Vector((0,0,1))).normalized()
    verts=[base,base+d*length*.46-side*width*.5,base+d*length*.48+Vector((0,0,.0015)),base+d*length,base+d*length*.46+side*width*.5]
    batch.add(verts,[(2,1,0),(2,3,1),(4,3,2),(4,2,0)],[(.5,0),(0,.46),(.5,.48),(.5,1),(1,.46)],material)

def flower(batch,center,radius=.010,material=0):
    center=Vector(center)
    for k in range(5):
        ang=math.tau*k/5
        d=Vector((math.cos(ang),math.sin(ang),.15));side=Vector((-d.y,d.x,0))
        verts=[center+d*radius*.15,center+d*radius*.58+side*radius*.38,center+d*radius+side*radius*.26,
               center+d*radius*1.08,center+d*radius-side*radius*.26,center+d*radius*.58-side*radius*.38]
        batch.add(verts,[(5,4,3,2,1,0)],[(.5,.05),(0,.5),(.12,.85),(.5,1),(.88,.85),(1,.5)],material)
    # Yellow centre is a second material assigned by the caller after white petal slot.
    verts=[center+Vector((math.cos(math.tau*k/8)*radius*.28,math.sin(math.tau*k/8)*radius*.28,.001)) for k in range(8)]
    batch.add(verts,[tuple(range(8))],[(.5+.5*math.cos(math.tau*k/8),.5+.5*math.sin(math.tau*k/8)) for k in range(8)],material+1)

def build_strawberry(materials):
    """Slots: mulch, soil, leaf, leaf_light, petiole, berry, flower, pollen."""
    rng=random.Random(PARAMS['seed']);batch=MeshBatch()
    # A rounded, trapezoid-like earthen mound. End boundaries sit exactly on Y=0/4.
    xs=[-.4,-.365,-.30,-.20,0,.20,.30,.365,.4]
    zs=[.025,.11,.205,.245,.25,.245,.205,.11,.025]
    verts=[];uv=[];cross=len(xs);segments=28
    for j in range(segments+1):
        y=4*j/segments
        for i,(x,z) in enumerate(zip(xs,zs)):
            ripple=0 if i in (0,cross-1) or j in (0,segments) else .0025*math.sin(j*1.9+i*.8)
            verts.append((x,y,z+ripple));uv.append((i/(cross-1),y/4))
    faces=[]
    for j in range(segments):
        for i in range(cross-1):a=j*cross+i;faces.append((a,a+1,a+cross+1,a+cross))
    batch.add(verts,faces,uv,0)
    # End soil profile visible only at a run termination; coplanar adjacent ends share no protrusion.
    for y,flip in ((0,True),(4,False)):
        v=[(x,y,z-.004) for x,z in zip(xs,zs)]+[(.4,y,0),(-.4,y,0)]
        f=tuple(range(len(v)));batch.add(v,[tuple(reversed(f)) if flip else f],[(x+.4,z) for x,_,z in v],1)
    # Flat closed underside, no hidden root or collision geometry.
    batch.add([(-.4,0,0),(.4,0,0),(.4,4,0),(-.4,4,0)],[(3,2,1,0)],[(0,0),(1,0),(1,1),(0,1)],1)
    for x in (-.4,.4):
        v=[(x,0,0),(x,4,0),(x,4,.025),(x,0,.025)]
        batch.add(v,[(0,1,2,3) if x>.0 else (3,2,1,0)],[(0,0),(4,0),(4,.025),(0,.025)],1)
    for row in range(PARAMS['rows']):
        for p in range(PARAMS['plants_per_row']):
            x=(-1+2*row/(PARAMS['rows']-1) if PARAMS['rows']>1 else 0)*PARAMS['row_offset_m']+rng.uniform(-.013,.013)
            y=.205+p*(3.59/(PARAMS['plants_per_row']-1)) if PARAMS['plants_per_row']>1 else 2.0
            y+=rng.uniform(-.009,.009)
            base=Vector((x,y,.245));phase=rng.random()*math.tau
            # Small exposed-soil planting opening, tucked below the leaf crown.
            hole=[(x+math.cos(k*math.tau/12)*(.023 if k%2 else .026),y+math.sin(k*math.tau/12)*(.023 if k%2 else .026),.247) for k in range(12)]
            batch.add(hole,[tuple(range(12))],[(.5+.5*math.cos(k*math.tau/12),.5+.5*math.sin(k*math.tau/12)) for k in range(12)],1)
            # Four compound leaves radiate from a compact crown; each carries three leaflets.
            for branch in range(4):
                angle=phase+branch*math.tau/4+rng.uniform(-.15,.15)
                direction=Vector((math.cos(angle),math.sin(angle),0))
                stalk=base+direction*rng.uniform(.036,.066)+Vector((0,0,rng.uniform(.12,.168)))
                cylinder(batch,base,stalk,.0018,5,4,False)
                for leaflet,delta in enumerate((-.73,0,.73)):
                    angle2=angle+delta
                    d=Vector((math.cos(angle2),math.sin(angle2),rng.uniform(.04,.22)))
                    b=stalk+Vector((math.cos(angle2)*.012,math.sin(angle2)*.012,.006))
                    cylinder(batch,stalk,b,.0011,4,4,False)
                    l=rng.uniform(.082,.109)*(1 if leaflet==1 else .89)
                    leaf(batch,b,d,l,l*.66,2 if (p+branch)%3 else 3,rng.uniform(-.25,.25))
            # A few visibly red fruits hang below foliage. Alternate rows/stations for variation.
            if (p+row)%2==0:
                for fruit in range(2 if p%3==0 else 1):
                    sign=-1 if row==0 else 1
                    c=base+Vector((sign*rng.uniform(.085,.125),rng.uniform(-.065,.065),rng.uniform(.029,.049)))
                    size=rng.uniform(.014,.020)
                    stem=c+Vector((0,0,size*.95));cylinder(batch,base+Vector((0,0,.06)),stem,.001,4,4,False)
                    berry(batch,c,size,5)
                    for k in range(5):
                        a=math.tau*k/5;calyx_blade(batch,stem,(math.cos(a),math.sin(a),-.28),size*.83,size*.34,2)
            if p%4==1:
                fc=base+Vector((rng.uniform(-.055,.055),rng.uniform(-.045,.045),.145))
                cylinder(batch,base,fc,.001,4,4,False);flower(batch,fc,.011,6)
    obj=batch.finish('SM_PazFarm_StrawberryBed_4m',materials,True)
    for v in obj.data.vertices:
        v.co.x*=PARAMS['bed_width_m']/.8;v.co.y*=PARAMS['bed_length_m']/4
        v.co.z=(v.co.z*PARAMS['bed_height_m']/.25 if v.co.z<=.25 else PARAMS['bed_height_m']+(v.co.z-.25)*PARAMS['leaf_canopy_height_above_bed_m']/.20)
    obj['pivot']='Ground centre of short end at (0,0,0)';obj['tile_axis']='+Y';obj['tile_length_m']=4.0
    obj['collision']='None: plants and soft bed';obj['foliage_import']='Masked, two-sided. Opacity is intentionally solid because leaf outlines are geometric.'
    return obj

def build_tunnel(materials):
    """Slots: translucent film, zinc steel. Geometry occupies exact 1.2 x 4 x 1m envelope."""
    batch=MeshBatch();arch_segments=40;long_segments=16
    # Outer film at the exact dimension. Arch posts/hoops are inset by their radius.
    vertices=[];uv=[]
    for j in range(long_segments+1):
        y=4*j/long_segments
        for k in range(arch_segments+1):
            t=math.pi*k/arch_segments
            x=-.6*math.cos(t);z=math.sin(t)
            # Fine tension ripples: zero at module boundaries/hoops and maximum crown.
            ripple=.0025*math.sin(math.pi*y)**2*math.sin(t)*math.sin(k*.92+j*.5)*(1-math.sin(t))
            vertices.append((x,y,max(0,z+ripple)));uv.append((k/arch_segments,y/4))
    faces=[]
    for j in range(long_segments):
        for k in range(arch_segments):
            a=j*(arch_segments+1)+k;faces.append((a,a+arch_segments+1,a+arch_segments+2,a+1))
    batch.add(vertices,[tuple(reversed(f)) for f in faces],uv,0)
    # Hoop tube centred just inside envelope; no end cap and no owned Y=4 hoop on repeating tile.
    pitch=PARAMS['tunnel_hoop_pitch_m']/PARAMS['tunnel_length_m']*4
    y_positions=[.007]+[i*pitch for i in range(1,math.ceil(4/pitch)) if i*pitch<3.99]+([3.993] if PARAMS['include_terminal_hoop'] else [])
    tube_r=.006
    for y in y_positions:
        verts=[];uv=[];rings=32;sides=5
        for k in range(rings+1):
            t=math.pi*k/rings
            c=Vector((-.59*math.cos(t),y,.988*math.sin(t)+.006))
            tangent=Vector((.59*math.sin(t),0,.988*math.cos(t))).normalized()
            side=Vector((0,1,0));normal=tangent.cross(side).normalized()
            for s in range(sides):
                a=math.tau*s/sides;verts.append(c+tube_r*(math.cos(a)*normal+math.sin(a)*side));uv.append((s/sides,k/rings))
        f=[]
        for k in range(rings):
            for s in range(sides):a=k*sides+s;b=k*sides+(s+1)%sides;f.append((a,b,b+sides,a+sides))
        batch.add(verts,f,uv,1)
    obj=batch.finish('SM_PazFarm_LowTunnel_4m',materials,True)
    for v in obj.data.vertices:
        v.co.x*=PARAMS['tunnel_width_m']/1.2;v.co.y*=PARAMS['tunnel_length_m']/4;v.co.z*=PARAMS['tunnel_height_m']
    obj['pivot']='Ground centre of short end at (0,0,0)';obj['tile_axis']='+Y';obj['tile_length_m']=4.0
    obj['film_material']='Translucent two-sided material. UE importer must recreate alpha/transmission from manifest.'
    obj['hoop_ownership']='Owns hoops at Y=0.007,1,2,3. Terminal hoop optional parameter. Start hoop inset radius to stay within tile.'
    obj['collision']='None: low flexible crop tunnel'
    return obj

def solid_leaf_material(C,name,color):
    import numpy as np
    mat=C.pbr(name,color,.58,0,kind='leaf',res=1024)
    base=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_BaseColor.png'))
    pix=np.empty(len(base.pixels),dtype=np.float32);base.pixels.foreach_get(pix);pix=pix.reshape((1024,1024,4));pix[:,:,3]=1
    base.pixels.foreach_set(pix.ravel());base.save()
    mask=np.ones((1024,1024,4),dtype=np.float32)
    im=C.image_file('T_PazFarm_'+name+'_Opacity.png',mask,True)
    paths=json.loads(mat['texture_files']);paths.append('Textures/'+Path(im.filepath_raw).name);mat['texture_files']=json.dumps(paths)
    mat['geometry_leaf_outline']='Serrated true-mesh leaflets. Solid white opacity preserves authored silhouette.'
    return mat

def seeded_berry_material(C):
    import numpy as np
    mat=C.pbr('StrawberryFruit',(.52,.015,.008),.33,0,kind='noise',res=1024)
    y,x=np.mgrid[0:1024,0:1024]/1023.
    row=np.floor(y*7);u=np.mod(x*10+np.mod(row,2)*.5,1)-.5;v=np.mod(y*7,1)-.5
    seed=np.exp(-((u/.11)**2+(v/.20)**2)*2)
    dent=np.exp(-((u/.17)**2+(v/.26)**2)*2)
    rgba=np.ones((1024,1024,4),dtype=np.float32)
    rgba[:,:,0]=.38+.13*np.sin(math.pi*y)+seed*.25-dent*.05
    rgba[:,:,1]=.009+seed*.18;rgba[:,:,2]=.006+seed*.035
    base=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_BaseColor.png'))
    base.pixels.foreach_set(rgba.ravel());base.save()
    height=.015*seed-.008*dent;gy,gx=np.gradient(height)
    normal=np.stack((-gx*45,-gy*45,np.ones_like(gx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    rgba[:,:,:3]=normal*.5+.5
    nm=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_Normal.png'))
    nm.pixels.foreach_set(rgba.ravel());nm.save()
    return mat

def crop_closeup(C,ob,rec):
    """Supplementary close-up, no export or added deliverable mesh."""
    scene=bpy.context.scene;tmp=[]
    target=Vector((-.025,.86,.335))
    bpy.ops.object.camera_add(location=target+Vector((.85,-1.3,1.05)))
    cam=bpy.context.object;tmp.append(cam);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.87;scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=target+Vector((-.5,-.7,1.8)))
    lamp=bpy.context.object;tmp.append(lamp);lamp.data.energy=180;lamp.data.size=1.8;lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN');lamp=bpy.context.object;tmp.append(lamp);lamp.rotation_euler=(.5,-.3,-.5);lamp.data.energy=1.4;lamp.data.angle=.2
    path='Previews/SM_PazFarm_StrawberryBed_4m_Detail.png';scene.render.filepath=str(ROOT/path);bpy.ops.render.render(write_still=True)
    for o in tmp:bpy.data.objects.remove(o,do_unlink=True)
    scene.camera=None;rec['detail_preview']=path

def save_relative(C,filename,records):
    C.save_family(filename,records,PARAMS)
    for im in bpy.data.images:
        if im.filepath:im.filepath=bpy.path.relpath(im.filepath)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blend'/filename))

def main():
    import paz_common as C
    all_records=[]
    C.reset()
    mats=[
        C.pbr('StrawberryMulch',(.008,.010,.011),.31,0,kind='mulch',res=1024),
        C.pbr('StrawberrySoil',(.13,.062,.023),.94,0,kind='noise',res=1024),
        solid_leaf_material(C,'StrawberryLeaf',(.038,.145,.022)),
        solid_leaf_material(C,'StrawberryLeafNew',(.075,.205,.030)),
        C.pbr('StrawberryPetiole',(.075,.17,.023),.68,0,kind='noise',res=1024),
        seeded_berry_material(C),
        C.pbr('StrawberryFlower',(.90,.88,.72),.7,0,kind='noise',res=1024),
        C.pbr('StrawberryPollen',(.9,.56,.035),.75,0,kind='noise',res=1024),
    ]
    raw=build_strawberry(mats)
    ob,rec=C.asset(raw.name,[raw],budget=20000,nominal=[.8,4,.45],notes=[
        'Open-bed default, 0.8m wide x 4m long, 0.25m raised mulch mound; canopy approx 0.20m above bed.',
        'Two rows of 12 plants. Each plant has four trifoliate serrated compound leaves; red seeded fruits and six small five-petal flowers.',
        'Pivot is the ground centre of the Y=0 short end. Tile translations (0,4*n,0). Geometry stays within the 0.8m x 4m footprint.',
        'Black plastic mulch, original geometric foliage outlines with solid masked opacity. Two-sided foliage; no plant collision.',
        'Editable deterministic parameters in build_strawberries.py and scene PazFarm_parameters; all textures original CC0 procedural artwork.',
    ])
    C.preview(ob,rec,azimuth=-54,elevation=39)
    crop_closeup(C,ob,rec)
    save_relative(C,'Strawberry.blend',[rec])
    all_records.append(rec)
    C.reset()
    mats=[C.pbr('LowTunnelFilm',(.75,.80,.79),.28,0,kind='film',alpha=.26,res=1024),
          C.pbr('LowTunnelSteel',(.43,.49,.52),.31,.92,kind='steel',res=1024)]
    # Standalone grayscale opacity map for straightforward Unreal material reconstruction.
    import numpy as np
    opacity=np.ones((1024,1024,4),dtype=np.float32);opacity[:,:,:3]=.26
    im=C.image_file('T_PazFarm_LowTunnelFilm_Opacity.png',opacity,True)
    paths=json.loads(mats[0]['texture_files']);paths.append('Textures/'+Path(im.filepath_raw).name);mats[0]['texture_files']=json.dumps(paths)
    raw=build_tunnel(mats)
    ob,rec=C.asset(raw.name,[raw],budget=5000,nominal=[1.2,4,1],notes=[
        'Optional open-ended low plastic crop tunnel: 1.2m span x 4m length x 1m outer-film crown.',
        'Pivot ground centre of Y=0 short end. Tile translations (0,4*n,0); film seams flush, no end caps.',
        'Each module owns start hoop at Y=0.007 (inset to keep frame inside boundary), and hoops Y=1,2,3. Next module supplies next start hoop.',
        'For the last module of a row enable include_terminal_hoop to add its last hoop at Y=3.993. Retained source parameter makes this easy to change.',
        'Film must be reconstructed in Unreal as translucent two-sided: BaseColor alpha 0.26, roughness .28, IOR 1.46, Blender transmission .25. FBX does not reproduce this automatically.',
        'No collision for soft low crop tunnel; not a walk-in structure. Editable source parameters included.',
    ])
    C.preview(ob,rec,azimuth=-54,elevation=29)
    save_relative(C,'LowTunnel.blend',[rec])
    all_records.append(rec)
    C.report('strawberries.json',all_records,{'parameters':PARAMS,'implementation':'All source geometry and procedural textures authored for this delivery; no reference/satellite pixels used.','scope':'Strawberry bed and optional low tunnel only.'})
    (ROOT/'Reports'/'strawberries_parameters.json').write_text(json.dumps(PARAMS,indent=2),encoding='utf-8')
    print('STRAWBERRY_DELIVERY_COMPLETE',json.dumps([(r['name'],r['triangles_LOD0'],r['size_metres_W_D_H']) for r in all_records]))

if __name__=='__main__': main()
