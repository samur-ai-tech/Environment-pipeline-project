"""Original Aleppo pines with closed needle geometry and explicit volume LOD3.

All output is confined to this revision. No native editor APIs or source assets.
"""
import sys, math, random, json, collections, struct, zlib
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Vector
import paz_common as p
p.SOURCE['author']='Paz Farm Aleppo pine modelling delivery, 2026-10-10'

CONFIG = [
    dict(variant='A', height=8.0, width=6.0, depth=5.75, lean=(.78,-.26), seed=431, crown_start=.60),
    dict(variant='B', height=11.0, width=8.0, depth=7.2, lean=(-.84,.55), seed=839, crown_start=.55),
    dict(variant='C', height=15.0, width=10.0, depth=9.15, lean=(1.08,.66), seed=1277, crown_start=.57),
]
HULL_LINEAR_MULTIPLIER = .63

class Batch:
    def __init__(self): self.v=[]; self.f=[]; self.uv=[]; self.parts=0
    def add(self, verts, faces, uvs=None):
        start=len(self.v); self.v.extend(tuple(v) for v in verts)
        for i, face in enumerate(faces):
            self.f.append(tuple(start+k for k in face))
            self.uv.append(uvs[i] if uvs else [(verts[k][0], verts[k][2]) for k in face])
        self.parts+=1
    def tube(self, pts, radii, sides=8):
        pts=list(map(Vector,pts)); verts=[]
        for i,pt in enumerate(pts):
            tangent=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
            side=tangent.cross(Vector((0,0,1)))
            if side.length<.01: side=tangent.cross(Vector((1,0,0)))
            side.normalize(); other=tangent.cross(side).normalized()
            for j in range(sides):
                angle=math.tau*j/sides
                verts.append(pt+radii[i]*(side*math.cos(angle)+other*math.sin(angle)))
        faces=[]; uvs=[]
        for i in range(len(pts)-1):
            for j in range(sides):
                faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
                uvs.append([(j/sides,pts[i].z*.5),((j+1)/sides,pts[i].z*.5),((j+1)/sides,pts[i+1].z*.5),(j/sides,pts[i+1].z*.5)])
        faces.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))])
        for q in range(2): uvs.append([(.5+.5*math.cos(math.tau*j/sides),.5+.5*math.sin(math.tau*j/sides)) for j in (reversed(range(sides)) if q==0 else range(sides))])
        self.add(verts,faces,uvs)
    def hull(self, center, radii, phase, seg=12, rings=6, inflate=1.0):
        c=Vector(center); rx,ry,rz=[r*inflate for r in radii]
        def position(theta,phi):
            st=math.sin(theta); ct=math.cos(theta)
            ripple=1+.10*math.sin(3*phi+phase)*st+.052*math.sin(5*phi+theta*2+phase)
            # Broad irregular upper pads, pinched lower silhouette, not spheres.
            bulge=1+.10*ct
            return c+Vector((rx*st*math.cos(phi)*ripple*bulge,ry*st*math.sin(phi)*ripple*bulge,rz*ct*(1+.055*math.sin(3*phi+phase)*st)))
        verts=[c+Vector((0,0,rz))]
        for i in range(1,rings):
            for j in range(seg): verts.append(position(math.pi*i/rings,math.tau*j/seg))
        bottom=len(verts); verts.append(c-Vector((0,0,rz)))
        faces=[]; uvs=[]
        for j in range(seg):
            faces.append((0,1+j,1+(j+1)%seg)); uvs.append([((j+.5)/seg,1),(j/seg,1-1/rings),((j+1)/seg,1-1/rings)])
        for i in range(rings-2):
            for j in range(seg):
                a=1+i*seg+j; b=1+i*seg+(j+1)%seg; c2=b+seg; d=a+seg
                faces.append((a,d,c2,b)); uvs.append([(j/seg,1-(i+1)/rings),(j/seg,1-(i+2)/rings),((j+1)/seg,1-(i+2)/rings),((j+1)/seg,1-(i+1)/rings)])
        for j in range(seg):
            faces.append((bottom,1+(rings-2)*seg+(j+1)%seg,1+(rings-2)*seg+j));uvs.append([((j+.5)/seg,0),((j+1)/seg,1/rings),(j/seg,1/rings)])
        self.add(verts,faces,uvs)
    def needle(self, base, direction, length, radius):
        base=Vector(base); direction=Vector(direction).normalized()
        side=direction.cross(Vector((0,0,1)))
        if side.length<.01: side=direction.cross(Vector((1,0,0)))
        side.normalize(); other=direction.cross(side).normalized()
        # Closed diamond-cross-section pyramidal needle, six true triangles.
        verts=[base+radius*side,base+radius*other,base-radius*side,base-radius*other,base+direction*length]
        faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2),(0,2,1)]
        uv=[[(.1,0),(.9,0),(.5,1)]]*4+[[(0,0),(0,1),(1,1)],[(0,0),(1,1),(1,0)]]
        self.add(verts,faces,uv)
    def obj(self,name,mat,smooth=True):
        return p.mesh(name,self.v,self.f,mat,self.uv,smooth)

def png_rgba(path, rgba):
    data=np.asarray(np.clip(rgba,0,255),dtype=np.uint8)
    height,width=data.shape[:2]
    def chunk(tag,payload):return struct.pack('>I',len(payload))+tag+payload+struct.pack('>I',zlib.crc32(tag+payload)&0xffffffff)
    raw=b''.join(b'\x00'+row.tobytes() for row in data)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))

def needle_grain(mat):
    """Original fully opaque needle-grain PBR, never used for silhouettes."""
    rng=np.random.default_rng(6381); size=1024
    height=np.zeros((size,size),np.float32)
    color=np.ones((size,size,4),np.float32)*255
    noise=rng.uniform(-2,2,(size,size))
    for ch,value in enumerate((29,39,20)):color[:,:,ch]=value+noise
    for n in range(6500):
        cx,cy=rng.uniform(0,size,2);length=rng.uniform(18,73);ang=rng.uniform(0,math.tau);width=rng.uniform(.6,1.7)
        bx=int(length*.5+3);x0=max(0,int(cx)-bx);x1=min(size,int(cx)+bx+1);y0=max(0,int(cy)-bx);y1=min(size,int(cy)+bx+1)
        y,x=np.mgrid[y0:y1,x0:x1];dx=x-cx;dy=y-cy
        along=dx*math.cos(ang)+dy*math.sin(ang);across=-dx*math.sin(ang)+dy*math.cos(ang)
        tapered=np.clip(1-np.abs(along)/(length*.5),0,1)
        coverage=np.clip(1-np.abs(across)/(width*np.sqrt(tapered)+.001),0,1)*tapered**.3
        shade=rng.uniform(.70,1.18);tone=np.array([41,54,27])*shade
        color[y0:y1,x0:x1,:3]=color[y0:y1,x0:x1,:3]*(1-coverage[:,:,None])+tone*coverage[:,:,None]
        height[y0:y1,x0:x1]=np.maximum(height[y0:y1,x0:x1],coverage)
    # Match diffuse crown luminance across LODs. Geometry-rich needle tufts
    # self-shadow more than the far hull, so the hull needs a calibrated albedo.
    srgb=np.clip(color[:,:,:3]/255,0,1)
    linear=np.where(srgb<=.04045,srgb/12.92,((srgb+.055)/1.055)**2.4)*HULL_LINEAR_MULTIPLIER
    color[:,:,:3]=np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)*255
    base=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and '_BaseColor' in n.image.name)
    png_rgba(Path(base.filepath),color)
    gy,gx=np.gradient(height);norm=np.stack((-gx*.5,-gy*.5,np.ones_like(gx)),axis=-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
    nm=np.ones((size,size,4),np.float32)*255;nm[:,:,:3]=(norm*.5+.5)*255
    normal=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and '_Normal' in n.image.name)
    png_rgba(Path(normal.filepath),nm)

def materials():
    bark=p.pbr('AleppoPine_Bark',(.245,.208,.177),.94,kind='bark',res=1024,seed=461)
    needle=p.pbr('AleppoPine_Needles',(.175,.215,.116),.96,kind='noise',res=1024,seed=317)
    hull=p.pbr('AleppoPine_CrownHull',(.133,.171,.089),.96,kind='noise',res=1024,seed=503)
    needle_grain(hull)
    for mat in (bark,needle,hull):
        bs=mat.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Specular IOR Level'].default_value=.08
        bs.inputs['Alpha'].default_value=1
        bs.inputs['Subsurface Weight'].default_value=0
        mat.use_backface_culling=False
        mat['blend_mode_intent']='OPAQUE_TWO_SIDED' if mat!=bark else 'OPAQUE'
        mat['opacity_contract']='Uniform alpha one. Silhouettes defined entirely by closed geometry.'
        # Reload PNG files so Blender previews use the same sRGB decode as consumers.
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE': node.image.reload()
    return bark,needle,hull

def layout(cfg):
    rng=random.Random(cfg['seed']); H=cfg['height']; W=cfg['width']; D=cfg['depth']; lx,ly=cfg['lean']
    trunk=[]
    for t in (0,.08,.22,.40,.58,.73,.88):
        trunk.append(Vector((lx*(t/.88)**1.25+.08*math.sin(t*10),ly*(t/.88)**1.15+.06*math.sin(t*13),H*t)))
    branches=[]; clumps=[]
    rotation=rng.uniform(-.3,.3)
    for j in range(7):
        a=j*math.tau/7+rotation+rng.uniform(-.18,.18)
        z=H*(cfg['crown_start']+.035*(j%3)+rng.uniform(-.022,.028))
        radial=W*rng.uniform(.22,.32)
        tip=Vector((lx*.85+math.cos(a)*radial,ly*.85+math.sin(a)*radial*D/W,z+H*.085))
        start=trunk[3 if j%3==0 else 4]
        elbow=start.lerp(tip,.47)+Vector((0,0,-H*.065))
        branches.append((start,elbow,tip))
        for k in range(3):
            angle=a+(-.40,.07,.44)[k]+rng.uniform(-.06,.06)
            extension=W*(.045,.12,.07)[k]
            center=tip+Vector((math.cos(angle)*extension,math.sin(angle)*extension*D/W,H*((-.015,.025,.093)[k]+rng.uniform(-.012,.015))))
            radii=(W*rng.uniform(.105,.133),D*rng.uniform(.10,.137),H*rng.uniform(.047,.072))
            clumps.append(dict(center=center,radii=radii,phase=rng.random()*math.tau,parent=tip))
    for k in range(2):
        c=trunk[-1]+Vector(((-1 if k==0 else 1)*W*.066,W*.024*(1 if k==0 else -1),H*(-.005 if k==0 else .025)))
        clumps.append(dict(center=c,radii=(W*.132,D*.134,H*.068),phase=rng.random()*math.tau,parent=trunk[-2]))
    return trunk,branches,clumps

def build_one(cfg,mats,lod):
    high=(lod==0); rng=random.Random(cfg['seed']+23); H=cfg['height']; W=cfg['width']
    bark=Batch(); hull=Batch(); needles=Batch(); trunk,branches,clumps=layout(cfg)
    tr=.018*H+.046
    bark.tube(trunk,[tr,tr*.92,tr*.79,tr*.60,tr*.44,tr*.25,tr*.07],12 if high else 6)
    # Large branches and every crown support persist in the lowest LOD.
    for j,(start,elbow,tip) in enumerate(branches):
        if high:
            curve=[start,start.lerp(elbow,.55)+Vector((0,0,-H*.016)),elbow,elbow.lerp(tip,.58)+Vector((0,0,H*.02)),tip]
            bark.tube(curve,[tr*.50,tr*.38,tr*.27,tr*.16,tr*.08],9)
        else: bark.tube([start,elbow,tip],[tr*.50,tr*.27,tr*.08],5)
    for cl in clumps:
        c=cl['center']; radii=cl['radii']; parent=cl['parent']
        bark.tube([parent,c],[tr*.095,tr*.023],6 if high else 4)
        hull.hull(c,radii,cl['phase'],12 if high else 8,6 if high else 4,.70 if high else 1.065)
        if high:
            rx,ry,rz=radii
            # Tufts concentrate on upper/side faces, leaving the overlapping inner
            # clump mesh as a reliable opaque backing at all distances.
            for q in range(350):
                z=rng.uniform(-.78,1); a=rng.random()*math.tau; s=math.sqrt(1-z*z)
                normal=Vector((s*math.cos(a),s*math.sin(a),z))
                ripple=1+.10*math.sin(3*a+cl['phase'])*s+.052*math.sin(5*a+math.acos(z)*2+cl['phase'])
                anchor=c+Vector((rx*normal.x*ripple*(1+.10*z),ry*normal.y*ripple*(1+.10*z),rz*z))*.81
                outward=Vector((normal.x,normal.y,normal.z*.55+.38)).normalized()
                length=rng.uniform(.22,.37)*(H/11)**.2
                stemstart=anchor-outward*.045
                if q%10==0: bark.tube([stemstart,anchor],[.007,.003],5)
                for n in range(2):
                    direction=(outward+Vector((rng.uniform(-.90,.90),rng.uniform(-.90,.90),rng.uniform(-.5,.65)))).normalized()
                    base=stemstart.lerp(anchor,rng.uniform(.45,1))
                    needles.needle(base,direction,length*rng.uniform(.70,1.15),rng.uniform(.018,.028)*(W/6.0))
    name='SM_PazFarm_AleppoPine_'+cfg['variant']+('' if high else '_LOD3')
    objects=[bark.obj(name+'_Bark',mats[0]),hull.obj(name+'_CrownHull',mats[2])]
    if high: objects.append(needles.obj(name+'_Needles',mats[1],False))
    ob=p.combine(name,objects)
    bpy.context.view_layer.update(); bb=p.bounds(ob)
    factors=(cfg['width']/(bb[1][0]-bb[0][0]),cfg['depth']/(bb[1][1]-bb[0][1]),H/(bb[1][2]-bb[0][2]))
    for v in ob.data.vertices:
        v.co.x*=factors[0];v.co.y*=factors[1];v.co.z=(v.co.z-bb[0][2])*factors[2]
    ob.data.update(); bpy.context.view_layer.update()
    notes=[
        'Original procedural Pinus halepensis: leaning trunk, asymmetric umbrella crown, 23 irregular overlapping opaque clump volumes.',
        'All foliage opaque with alpha 1; no masked cards, billboard, wind or collision. Shared dark grey-olive needle and hull palette.',
        'LOD0 uses 16,100 closed diamond-section tapered needle-cluster prisms in 8,050 distributed pairs; opaque inner hulls are recessed beneath them.' if high else 'Lowest LOD is hand-authored from the same 23 closed crown clumps, leaning trunk and support branches; no needles/cards or billboard. Slight clump-envelope inflation compensates for removed needles.',
        'Trunk base ground origin at (0,0,0), applied transforms, metres. Each matching LOD has the same nominal W/D/H.',
        'Designed for non-Nanite instancing HLOD at far distances. Native integration and 1 km appearance require operator verification.'
    ]
    ob,rec=p.asset(name,[ob],budget=120000 if high else 2000,nominal=[cfg['width'],cfg['depth'],H],notes=notes)
    rec['lod_index']=lod;rec['triangle_budget_min']=40000 if high else 800
    rec['family']='AleppoPine';rec['variant']=cfg['variant'];rec['paired_asset']='SM_PazFarm_AleppoPine_'+cfg['variant']+('_LOD3' if high else '')
    rec['construction']={'closed_crown_clumps':len(clumps),'closed_needle_prisms':needles.parts,'crown_shape':'irregular umbrella clumps','alpha':1.0,'no_billboard':True}
    ob['species']='Pinus halepensis';ob['lod_index']=lod;ob['variant']=cfg['variant'];ob['parameters']=json.dumps(cfg);ob['lod_pair']=rec['paired_asset']
    # Verify edge incidence for every disconnected closed component; vertices
    # are shared inside each primitive, not welded across separate components.
    edge_count=collections.Counter()
    for face in ob.data.polygons:
        ids=list(face.vertices)
        for i,v in enumerate(ids): edge_count[tuple(sorted((v,ids[(i+1)%len(ids)])))]+=1
    rec['qa']['nonmanifold_edges']=sum(n!=2 for n in edge_count.values())
    rec['qa']['closed_components']=rec['qa']['nonmanifold_edges']==0
    rec['qa']['finite_geometry']=all(math.isfinite(c) for v in ob.data.vertices for c in v.co)
    rec['qa']['finite_uv0']=all(math.isfinite(c) for uv in ob.data.uv_layers[0].data for c in uv.uv)
    if not all([rec['qa']['closed_components'],rec['qa']['finite_geometry'],rec['qa']['finite_uv0']]):raise RuntimeError('Invalid closed tree mesh: '+name)
    if rec['triangles_LOD0']<rec['triangle_budget_min']: raise RuntimeError('Tree below required geometry budget: '+name)
    p.preview(ob,rec,azimuth=-64,elevation=14)
    return ob,rec

def main():
    p.reset(); mats=materials(); records=[]; objects=[]
    for cfg in CONFIG:
        for lod in (0,3):
            ob,rec=build_one(cfg,mats,lod);objects.append(ob);records.append(rec)
            p.report('pines_progress.json',records)
    for ob in objects:ob.hide_set(ob!=objects[0]);ob.hide_render=ob!=objects[0]
    p.save_family('AleppoPine.blend',records,{'variants':CONFIG,'tufts_per_clump':350,'needles_per_tuft':2,'lod3_hull_inflation':1.065,'lod0_inner_hull_factor':.70,'hull_linear_multiplier':HULL_LINEAR_MULTIPLIER,'needle_width_variant_factor':'width_metres / 6','foliage_srgb_target_RGB':[43,53,29]})
    p.report('pines_v003.json',records,{
        'construction':'Original deterministic procedural 3D pine geometry and PBR textures; no external content or satellite pixels.',
        'parameters':CONFIG,'lod_pairing':{r['name']:r['paired_asset'] for r in records if r['lod_index']==0},
        'lod0':'23 recessed closed irregular crown hulls plus 8,050 distributed pairs of closed tapered needle-cluster prisms; leaning trunk and branched limbs.',
        'lod3':'Same 23 hull centers and trunk/branch architecture. Low-ring closed volumes, no needles, no billboard. Envelope inflation 1.065 before final nominal envelope fit.',
        'native_verified':False,'source_licence':'CC0-1.0 original procedural artwork',
        'texture_color_handling':'Saved PNG files reloaded before rendering, so BaseColor receives sRGB decoding consistently. All BaseColor alpha=1.',
        'materials':'Three shared opaque materials; needles and hull intended two-sided, roughness .96, specular .08, no transmission/subsurface/wind.'})
    (p.ROOT/'Reports'/'pines_v003_notes.md').write_text('''# Aleppo pines v003\n\nThree original Pinus halepensis variants at 8/11/15 m, with 6/8/10 m crowns. All six FBXs preserve the trunk-base origin.\n\nLOD0 has solid needle prisms over closed clump hulls. LOD3 retains the corresponding trunk, branches and the same 23 clump centers; the hulls expand by 6.5% before envelope fitting to stand in for removed outer needles. All crown geometry is opaque; there are no cards or billboards.\n\nThe three PBR materials are shared. Needle and hull roughness is 0.96, specular 0.08; no wind, collision or alpha fading. Normals are OpenGL +Y. BaseColor PNG files were reloaded as sRGB for the previews. Geometry validation checks finite positions/UV0, no zero-area triangles, and exactly two incident polygons per edge of every closed primitive.\n\nThis is offline source artwork. Root supplies fresh-FBX round trips and fixed-camera distance evidence; Unreal/HLOD verification remains with the receiving operator.\n''',encoding='utf-8')

if __name__=='__main__':main()
