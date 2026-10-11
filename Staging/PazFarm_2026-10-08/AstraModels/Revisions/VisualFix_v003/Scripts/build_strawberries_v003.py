"""Paz Farm strawberry visual revision v003. Original procedural geometry.

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
    'plants_per_row': 12, 'rows': 2, 'row_offset_m': .145,
    'compound_leaves_per_plant': 5, 'leaflet_length_range_m': [.140, .157],
    'leaflet_width_ratio': .82, 'leaflet_profile_rings': 6,
    'canopy_width_m': .68, 'canopy_peak_height_m': .408,
    'canopy_material_rgb_srgb': [29, 58, 20],
    'leaf_material_rgb_srgb': [35, 66, 23],
    'mulch_material_rgb_srgb': [8, 9, 8],
    'mulch_roughness': .92, 'mulch_specular': .06,
    'canopy_roughness': .9, 'leaf_roughness': .87,
    'notes': 'v003: closed opaque canopy under 24 larger rosettes; identical hull in LOD0 and separate non-billboard LOD3. Exact 0.8 x 4 m tile.',
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
        obj['original_geometry']='Original authored procedural geometry for Paz Farm, 2026-10-10'
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
    # Lower tessellation funds six full compound leaves per plant while keeping true silhouettes.
    verts=[base]; uv=[(.5,0)]
    rings=PARAMS['leaflet_profile_rings']
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


def closed_ridge(batch, profile, stations, material, wave=0):
    """Closed connected prism. Cyclic profile goes up the left side then down the right.

    First and last profiles are identical. End caps are real closed polygons; no
    mask, billboard, shell gap or overlapping coplanar sheet supplies the crown.
    """
    verts=[]; uv=[]; n=len(profile)
    for y,w in stations:
        for i,(x,z) in enumerate(profile):
            top_weight=math.sin(math.pi*i/(n-3)) if i<=n-3 else 0
            verts.append((x,y,z+wave*w*max(0,top_weight)))
            uv.append(((x+.4)/.8,y/4))
    faces=[]
    for j in range(len(stations)-1):
        for i in range(n):
            ni=(i+1)%n
            # Across x then along y makes the crown face outward/upward.
            faces.append((j*n+i,j*n+ni,(j+1)*n+ni,(j+1)*n+i))
    faces.extend([tuple(reversed(range(n))),tuple((len(stations)-1)*n+i for i in range(n))])
    first_face=len(batch.f)
    batch.add(verts,faces,uv,material)
    # Per-face UVs unwrap the complete perimeter, including vertical sides;
    # the two end caps use planar X/Z UVs rather than a collapsed Y coordinate.
    lengths=[math.hypot(profile[(i+1)%n][0]-profile[i][0],profile[(i+1)%n][1]-profile[i][1]) for i in range(n)]
    arc=[0]
    for length in lengths:arc.append(arc[-1]+length)
    arc=[u/arc[-1] for u in arc]
    for j in range(len(stations)-1):
        for i in range(n):
            batch.uv[first_face+j*n+i]=[(arc[i],stations[j][0]/4),(arc[i+1],stations[j][0]/4),(arc[i+1],stations[j+1][0]/4),(arc[i],stations[j+1][0]/4)]
    for offset in (-2,-1):
        face=faces[offset]
        batch.uv[first_face+len(faces)+offset]=[((verts[v][0]+.4)/.8,verts[v][2]/.45) for v in face]
    return {'first_face':first_face,'face_count':len(faces),'caps':[first_face+len(faces)-2,first_face+len(faces)-1]}


def build_body(batch):
    # Eleven-vertex mulch cross-section with a closed underside on the ground.
    mulch=[(-.4,.025),(-.365,.11),(-.30,.205),(-.20,.245),(0,.25),(.20,.245),(.30,.205),(.365,.11),(.4,.025),(.4,0),(-.4,0)]
    r1=closed_ridge(batch,mulch,[(0,0),(1,0),(2,0),(3,0),(4,0)],0)
    # Low-poly clumped mound: full opaque width .68m, sitting inside the bed.
    # Equal-height first/last adjacent stations avoid a visible shading seam.
    canopy=[(-.34,.225),(-.285,.295),(-.17,.357),(0,.388),(.17,.357),(.285,.295),(.34,.225),(.34,.215),(-.34,.215)]
    stations=[(0,0),(.25,0),(.75,1),(1.25,.25),(1.75,.9),(2.25,.20),(2.75,1),(3.25,0),(3.75,0),(4,0)]
    r2=closed_ridge(batch,canopy,stations,8,.02)
    return {'mulch':r1,'canopy':r2}


def build_strawberry(materials,lowest=False):
    rng=random.Random(PARAMS['seed']);batch=MeshBatch();parts=build_body(batch)
    if not lowest:
        for row in range(2):
            for p in range(PARAMS['plants_per_row']):
                x=(-1 if row==0 else 1)*PARAMS['row_offset_m']+rng.uniform(-.005,.005)
                y=.215+p*3.57/(PARAMS['plants_per_row']-1)+rng.uniform(-.004,.004)
                base=Vector((x,y,.285));phase=rng.random()*math.tau
                for branch in range(PARAMS['compound_leaves_per_plant']):
                    angle=phase+branch*math.tau/PARAMS['compound_leaves_per_plant']+rng.uniform(-.1,.1)
                    direction=Vector((math.cos(angle),math.sin(angle),0))
                    stalk=base+direction*rng.uniform(.023,.035)+Vector((0,0,rng.uniform(.089,.105)))
                    cylinder(batch,base,stalk,.0019,5,4,False)
                    for leaflet,delta in enumerate((-.72,0,.72)):
                        a=angle+delta
                        d=Vector((math.cos(a),math.sin(a),rng.uniform(.01,.09)))
                        length=rng.uniform(*PARAMS['leaflet_length_range_m'])*(1 if leaflet==1 else .94)
                        leaf(batch,stalk,d,length,length*PARAMS['leaflet_width_ratio'],3 if (p+branch)%7==0 else 2,rng.uniform(-.12,.12))
                if (p+row)%2==0:
                    # Twelve isolated berries placed on the outer shoulder below foliage.
                    c=Vector((x+(-1 if row==0 else 1)*.16,y+rng.uniform(-.04,.04),rng.uniform(.284,.315)))
                    size=rng.uniform(.015,.020);stem=c+Vector((0,0,size*.95))
                    cylinder(batch,base+Vector((0,0,.075)),stem,.001,4,4,False);berry(batch,c,size,5)
                    for k in range(5):
                        a=math.tau*k/5;calyx_blade(batch,stem,(math.cos(a),math.sin(a),-.28),size*.83,size*.34,2)
                if p%4==1:
                    fc=Vector((x,y,.408));cylinder(batch,base,fc,.001,4,4,False);flower(batch,fc,.011,6)
    name='SM_PazFarm_StrawberryBed_4m'+('_LOD3' if lowest else '')
    obj=batch.finish(name,materials,True)
    for part in parts.values():
        for face in part['caps']:obj.data.polygons[face].use_smooth=False
    # Explicit face attributes preserve the closed body identities for QA.
    att=obj.data.attributes.new('PazFarm_body_part','INT','FACE')
    for tag,part in enumerate(parts.values(),1):
        for i in range(part['first_face'],part['first_face']+part['face_count']):att.data[i].value=tag
    obj['body_parts']=json.dumps(parts)
    obj['pivot']='Ground centre of Y=0 short end at (0,0,0)';obj['tile_axis']='+Y';obj['tile_length_m']=4.0
    obj['foliage_import']='Opaque, two-sided geometric leaves and opaque closed crown hull. All alpha is 1; no masked cards.'
    obj['collision']='None';obj['LOD_role']='Lowest independent geometry mesh for non-Nanite Instancing HLOD' if lowest else 'Detailed geometry with retained closed crown hull'
    return obj


def write_png_rgba(path,values):
    """Explicit 8-bit PNG values, with an sRGB tag for BaseColor only."""
    import struct,zlib,numpy as np
    arr=np.asarray(np.clip(values,0,255),dtype=np.uint8);h,w=arr.shape[:2]
    def chunk(tag,payload):return struct.pack('!I',len(payload))+tag+payload+struct.pack('!I',zlib.crc32(tag+payload)&0xffffffff)
    raw=b''.join(b'\0'+row.tobytes() for row in arr)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,6,0,0,0))
    if 'BaseColor' in str(path):data+=chunk(b'sRGB',b'\0')
    path.write_bytes(data+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))


def pbr_opaque(C,tag,rgb,roughness,specular=.10,kind='noise'):
    import numpy as np
    mat=C.pbr(tag,tuple(c/255 for c in rgb),roughness,0,kind='noise',res=1024)
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Alpha'].default_value=1;bs.inputs['Specular IOR Level'].default_value=specular
    bs.inputs['Subsurface Weight'].default_value=0
    mat.use_backface_culling=False;mat['blend_mode_intent']='OPAQUE_TWO_SIDED'
    mat['opaque_alpha']=1.0;mat['specular_target']=specular
    mat['basecolor_srgb_nominal_rgb']=list(rgb);mat['roughness_target']=roughness
    y,x=np.mgrid[0:1024,0:1024]/1023.
    rng=np.random.default_rng(608+(len(tag)*17));noise=rng.random((1024,1024))
    tint=.965+.05*noise
    height=np.zeros_like(x)
    if kind=='leaf':
        vein=np.exp(-((x-.5)/.009)**2)
        secondary=np.maximum(0,np.cos((y-np.abs(x-.5)*.85)*math.pi*26))**20
        tint=.92+.09*np.sin(math.pi*y)+.04*noise+.028*vein+.015*secondary
        height=.002*vein+.0005*secondary
    elif kind=='canopy':
        # Broad green tonal variation only; no transparent holes or baked sunlight.
        tint=.965+.02*np.sin(x*19+y*11)+.02*np.sin(y*33-x*9)+.02*noise
    elif kind=='mulch':
        tint=.965+.03*np.sin(x*60+y*7)**2
        height=.0007*np.sin(x*70+np.sin(y*30)*2)
    rgba=np.ones((1024,1024,4),dtype=float)*255
    rgba[:,:,:3]=np.clip(np.array(rgb)[None,None,:]*tint[:,:,None],0,255)
    base=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_BaseColor.png'))
    write_png_rgba(Path(base.filepath_raw),rgba);base.reload();base.colorspace_settings.name='sRGB'
    gy,gx=np.gradient(height);norm=np.stack((-gx*15,-gy*15,np.ones_like(gx)),axis=-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
    rgba[:,:,:3]=(norm*.5+.5)*255
    normal=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_Normal.png'))
    write_png_rgba(Path(normal.filepath_raw),rgba);normal.reload();normal.colorspace_settings.name='Non-Color'
    rgba[:,:,0]=255;rgba[:,:,1]=round(roughness*255);rgba[:,:,2]=0
    orm=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.endswith('_ORM.png'))
    write_png_rgba(Path(orm.filepath_raw),rgba);orm.reload();orm.colorspace_settings.name='Non-Color'
    return mat


def comparison_preview(C,objects):
    scene=bpy.context.scene;copies=[];labels=[]
    for ob,x,text in zip(objects,[-.65,.65],['LOD0 - 24 ROSETTES','LOD3 - CLOSED RIDGE']):
        cp=ob.copy();cp.data=ob.data.copy();bpy.context.collection.objects.link(cp);cp.location.x=x;copies.append(cp)
        font=bpy.data.curves.new('Strawberry_LOD_label','FONT');font.body=text;font.size=.078
        label=bpy.data.objects.new('Strawberry_LOD_label',font);bpy.context.collection.objects.link(label)
        label.location=(x-.37,-.20,.005);label.data.materials.append(C.plain_mat('Strawberry_Preview_label',(.025,.035,.045)))
        bpy.ops.object.select_all(action='DESELECT');label.select_set(True);bpy.context.view_layer.objects.active=label;bpy.ops.object.convert(target='MESH');labels.append(bpy.context.object)
    pair=C.combine('StrawberryPreviewPair',copies+labels)
    C.preview(pair,{'preview':'Previews/SM_PazFarm_StrawberryBed_4m_LOD_Comparison.png'},azimuth=-67,elevation=60)
    bpy.data.objects.remove(pair,do_unlink=True)
    scene.camera=None


def main():
    import paz_common as C
    C.reset()
    mats=[
        pbr_opaque(C,'StrawberryMulch_v003',[8,9,8],.92,.06,'mulch'),
        pbr_opaque(C,'StrawberrySoil_v003',[44,28,16],.96,.06),
        pbr_opaque(C,'StrawberryLeaf_v003',[35,66,23],.87,.10,'leaf'),
        pbr_opaque(C,'StrawberryLeafNew_v003',[42,75,28],.87,.10,'leaf'),
        pbr_opaque(C,'StrawberryPetiole_v003',[37,63,23],.9,.08),
        pbr_opaque(C,'StrawberryFruit_v003',[147,18,12],.70,.14),
        pbr_opaque(C,'StrawberryFlower_v003',[220,218,183],.87,.06),
        pbr_opaque(C,'StrawberryPollen_v003',[207,151,21],.9,.06),
        pbr_opaque(C,'StrawberryCanopy_v003',[29,58,20],.90,.08,'canopy'),
    ]
    objects=[];records=[]
    for lowest in (False,True):
        raw=build_strawberry(mats,lowest)
        ob,rec=C.asset(raw.name,[raw],budget=400 if lowest else 20000,nominal=[.8,4,.42],notes=[
            'Exact .8 x 4 m boundary, ground origin at centre of Y=0 short end, tiling along +Y in 4m increments.',
            'Separate lowest LOD for always-loaded Instancing HLOD, Nanite disallowed; this is opaque closed ridge geometry, not a billboard.' if lowest else '24 rosettes / 360 larger geometric leaflets over a continuous closed opaque dark-green canopy hull; modest berries and flowers retained.',
            'Same closed canopy and mulch body in both LODs; all foliage alpha 1, opaque two-sided materials, no wind or collision.',
            'Dark mulch: nominal sRGB 8/9/8, roughness .92, specular .06, barely raised normal detail. No sunlight baked into BaseColor.',
            '1K BaseColor sRGB; Normal OpenGL +Y and ORM are linear non-color. Normals must be converted to Unreal convention by receiver.',
        ])
        rec['lod_index']=3 if lowest else 0;rec['lod']=3 if lowest else 0;rec['lowest_lod']=bool(lowest)
        rec['paired_asset']='SM_PazFarm_StrawberryBed_4m' if lowest else 'SM_PazFarm_StrawberryBed_4m_LOD3'
        objects.append(ob);records.append(rec)
        C.preview(ob,rec,azimuth=-54,elevation=39)
    C.save_family('Strawberry.blend',records,PARAMS)
    comparison_preview(C,objects)
    C.report('strawberries_v003.json',records,{
        'parameters':PARAMS,
        'LODpairing':{'SM_PazFarm_StrawberryBed_4m':'SM_PazFarm_StrawberryBed_4m_LOD3'},
        'construction':'Each asset contains the same two closed connected prisms: black mulch and continuous green canopy. LOD0 adds 24 rosettes, 360 larger leaflets, 12 berries and 6 flowers. LOD3 is only those two prisms.',
        'materials':'All nine slots opaque, two-sided, alpha 1. Slots 0=mulch, 8=canopy shared across both meshes; LOD3 uses these two slots only.',
        'preview_comparison':'Previews/SM_PazFarm_StrawberryBed_4m_LOD_Comparison.png',
        'scope':'Offline only; no Unreal operation. Distance suite supplied by root; native HLOD assignment and material reconstruction remain operator work.'})
    print('STRAWBERRY_V003_COMPLETE',json.dumps([(r['name'],r['triangles_LOD0'],r['size_metres_W_D_H']) for r in records]))


def verify_delivery():
    import numpy as np
    import paz_common as C
    from collections import Counter
    checks={'assets':[],'textures':[]}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend'/'Strawberry.blend'))
    source={}
    def inspect(obj):
        obj.data.calc_loop_triangles();v=np.array([v.co[:] for v in obj.data.vertices])
        texcoords=obj.data.uv_layers.active.data
        uv_degenerate=0
        for tri in obj.data.loop_triangles:
            a,b,c=[texcoords[i].uv for i in tri.loops]
            uv_degenerate+=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))<1e-12
        out={'name':obj.name,'triangles':len(obj.data.loop_triangles),'dimensions_metres':(v.max(axis=0)-v.min(axis=0)).tolist(),
            'bounds_metres':[v.min(axis=0).tolist(),v.max(axis=0).tolist()],'origin_metres':list(obj.location),
            'zero_area_triangles':sum(t.area<1e-12 for t in obj.data.loop_triangles),'finite':bool(np.isfinite(v).all()),
            'uv_finite':bool(np.isfinite(np.array([t.uv[:] for t in obj.data.uv_layers.active.data])).all()),'zero_uv_area_triangles':uv_degenerate,'closed_body':{}}
        for slot,label in ((0,'mulch'),(8,'canopy')):
            polys=[p for p in obj.data.polygons if p.material_index==slot]
            edges=Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in polys for i in range(len(p.vertices)))
            ids={i for p in polys for i in p.vertices};verts=[obj.data.vertices[i].co for i in ids]
            front=sorted(set((round(float(p.x),6),round(float(p.z),6)) for p in verts if abs(p.y)<1e-6))
            back=sorted(set((round(float(p.x),6),round(float(p.z),6)) for p in verts if abs(p.y-4)<1e-6))
            signed_volume=sum(obj.data.vertices[t.vertices[0]].co.dot(obj.data.vertices[t.vertices[1]].co.cross(obj.data.vertices[t.vertices[2]].co))/6 for t in obj.data.loop_triangles if t.material_index==slot)
            out['closed_body'][label]={'edge_incidence_two':all(n==2 for n in edges.values()),'non_manifold_edge_count':sum(n!=2 for n in edges.values()),
                'signed_volume_m3':signed_volume,'equal_end_profiles':front==back,'end_profile_xz':front}
        return out
    for name in ('SM_PazFarm_StrawberryBed_4m','SM_PazFarm_StrawberryBed_4m_LOD3'):
        source[name]=inspect(bpy.data.objects[name])
    for im in bpy.data.images:
        if im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));pix=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(pix);pix=pix.reshape((-1,4))
            checks['textures'].append({'path':str(p),'exists':p.is_file(),'size':list(im.size),'alpha_min':float(pix[:,3].min()),'alpha_max':float(pix[:,3].max()),'relative':im.filepath.startswith('//')})
    for name,src in source.items():
        C.reset();bpy.ops.import_scene.fbx(filepath=str(ROOT/'FBX'/(name+'.fbx')),use_anim=False)
        fbx=inspect(bpy.data.objects[name]);budget=400 if name.endswith('LOD3') else 20000
        assertions=[]
        for r in (src,fbx):
            assertions.extend([r['triangles']<=budget,r['zero_area_triangles']==0,r['zero_uv_area_triangles']==0,r['finite'],r['uv_finite'],max(abs(x) for x in r['origin_metres'])<1e-6,
                abs(r['dimensions_metres'][0]-.8)<1e-6,abs(r['dimensions_metres'][1]-4)<1e-6])
            for part in r['closed_body'].values():assertions.extend([part['edge_incidence_two'],part['signed_volume_m3']>0,part['equal_end_profiles']])
        assertions.extend([src['triangles']==fbx['triangles'],max(abs(a-b) for a,b in zip(src['dimensions_metres'],fbx['dimensions_metres']))<1e-5])
        checks['assets'].append({'source':src,'fresh_fbx_import':fbx,'pass':all(assertions)})
    checks['pass']=all(a['pass'] for a in checks['assets']) and all(t['exists'] and t['size']==[1024,1024] and t['alpha_min']==1 and t['relative'] for t in checks['textures'])
    checks['limitations']='Offline geometry and texture verification. Rendered distances are supplied separately; no Unreal import, HLOD placement or native screenshots verified.'
    (ROOT/'Reports'/'strawberries_v003_qa.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('STRAWBERRY_V003_QA',checks['pass'])
    if not checks['pass']:raise RuntimeError('Strawberry v003 QA failed')


if __name__=='__main__':
    if '--verify-only' in sys.argv:verify_delivery()
    else:main()

