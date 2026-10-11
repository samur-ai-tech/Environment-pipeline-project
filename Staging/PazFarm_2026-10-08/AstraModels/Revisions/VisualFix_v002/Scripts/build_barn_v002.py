"""Offline Paz Farm barn v002: source-default footprint, roof-only revision.
Original wall, trim, door, hardware and UCX remain; no native editor actions.
All output goes to this revision. Generator copied from original barn source.
"""
import bpy, math, json, sys, os, hashlib, shutil, struct, zlib
from pathlib import Path
from mathutils import Vector
import numpy as np
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT.parents[1]
sys.path.insert(0, str(ROOT/'Scripts'))
import paz_common as pc
ROOF_TARGET_SRGB = [70,62,68]
ROOF_ROUGHNESS = .94
ROOF_METALLIC = 0.
ROOF_SPECULAR_IOR_LEVEL = .20
ROOF_RELIEF_M = .006

BARN = dict(length=20., depth=12., eave=6., ridge=8., roof_overhang=.24,
            corrugation_pitch=.22, corrugation_depth=.035, sheet_thickness=.012,
            door_width=6., door_height=4.4, plinth_height=.16)

FENCE = dict(length=3., height=2., post_radius=.033, wire_radius=.0019,
             diamond_pitch=.12, gate_width=6.)

class Builder:
    def __init__(self, name, materials):
        self.name, self.materials = name, materials
        self.verts, self.faces, self.mats, self.uvs, self.smooth = [], [], [], [], []
    def face(self, indices, mat=0, uvs=None, smooth=False):
        self.faces.append(tuple(indices)); self.mats.append(mat)
        self.uvs.append(uvs or [(0,0),(1,0),(1,1),(0,1)][:len(indices)])
        self.smooth.append(smooth)
    def box(self, center, size, mat=0):
        x,y,z = center; a,b,c = [d/2 for d in size]; start=len(self.verts)
        self.verts += [(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                       (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
        for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.face([start+i for i in f],mat)
    def rod(self, p0, p1, radius, mat=0, sides=8, radius1=None):
        p0,p1=Vector(p0),Vector(p1); direction=p1-p0
        if direction.length < 1e-7: return
        axis=direction.normalized(); helper=Vector((0,0,1))
        if abs(axis.dot(helper))>.95: helper=Vector((1,0,0))
        u=axis.cross(helper).normalized(); v=axis.cross(u).normalized()
        start=len(self.verts); radius1=radius if radius1 is None else radius1
        for p,r in [(p0,radius),(p1,radius1)]:
            for i in range(sides):
                a=2*math.pi*i/sides
                self.verts.append(tuple(p+r*(math.cos(a)*u+math.sin(a)*v)))
        for i in range(sides):
            n=(i+1)%sides
            self.face([start+i,start+n,start+sides+n,start+sides+i],mat,
                      [(i/sides,0),((i+1)/sides,0),((i+1)/sides,direction.length),(i/sides,direction.length)],True)
        # Fan caps with valid non-degenerate triangles.
        for i in range(1,sides-1):
            self.face([start,start+i+1,start+i],mat,[(.5,.5),(1,0),(0,0)])
            self.face([start+sides,start+sides+i,start+sides+i+1],mat,[(.5,.5),(0,0),(1,0)])
    def corrugated(self, origin, cross, run, length, run_start, run_end, mat=0,
                   pitch=None, depth=None, thickness=None):
        """Closed trapezoid-corrugated sheet, with independently varying end heights."""
        pitch=pitch or BARN['corrugation_pitch']; depth=depth or BARN['corrugation_depth']
        thickness=thickness or BARN['sheet_thickness']
        o,c,r=Vector(origin),Vector(cross).normalized(),Vector(run).normalized()
        n=c.cross(r).normalized(); periods=max(1,round(length/pitch)); pitch=length/periods
        points=[]
        for j in range(periods):
            for frac,relief in [(0,0),(.32,0),(.5,depth),(.68,0)]:
                points.append((pitch*(j+frac),relief))
        points.append((length,0)); start=len(self.verts); count=len(points)
        for skin in [0,-thickness]:
            for q,d in points:
                for t in [run_start(q),run_end(q)]: self.verts.append(tuple(o+q*c+t*r+(d+skin)*n))
        for side in [0,1]:
            k=start+side*2*count
            for j in range(count-1):
                q0,q1=points[j][0],points[j+1][0]
                f=[k+2*j,k+2*j+2,k+2*j+3,k+2*j+1]
                uv=[(q0,run_start(q0)),(q1,run_start(q1)),(q1,run_end(q1)),(q0,run_end(q0))]
                if side: f.reverse(); uv.reverse()
                self.face(f,mat,uv)
        for j in range(count-1):
            a=start+2*j; b=start+2*(j+1); back=2*count
            self.face([a,a+back,b+back,b],mat)
            self.face([a+1,b+1,b+back+1,a+back+1],mat)
        for j in [0,count-1]:
            a=start+2*j; b=a+2*count
            f=[a,a+1,b+1,b]
            if j==count-1:f.reverse()
            self.face(f,mat)
    def wire_mesh(self,x0,x1,z0,z1,y=0.,mat=0,pitch=None):
        """Two directions of real galvanized wire, clipped to the panel frame."""
        pitch=pitch or FENCE['diamond_pitch']
        # Each orientation is shifted by one wire radius to imply the over-under crossing.
        for sign in [-1,1]:
            lo=min(z0-sign*x0,z0-sign*x1); hi=max(z1-sign*x0,z1-sign*x1)
            for k in range(math.floor(lo/pitch)-1,math.ceil(hi/pitch)+2):
                intercept=k*pitch; pts=[]
                for x in [x0,x1]:
                    z=sign*x+intercept
                    if z0-1e-8<=z<=z1+1e-8:pts.append((x,z))
                for z in [z0,z1]:
                    x=(z-intercept)/sign
                    if x0-1e-8<=x<=x1+1e-8 and all(abs(x-a)>1e-7 or abs(z-b)>1e-7 for a,b in pts):pts.append((x,z))
                if len(pts)==2:
                    self.rod((pts[0][0],y+sign*FENCE['wire_radius'],pts[0][1]),
                             (pts[1][0],y+sign*FENCE['wire_radius'],pts[1][1]),FENCE['wire_radius'],mat,6)
    def object(self):
        mesh=bpy.data.meshes.new(self.name+'_Geometry');mesh.from_pydata(self.verts,[],self.faces);mesh.update()
        obj=bpy.data.objects.new(self.name,mesh);bpy.context.collection.objects.link(obj)
        for material in self.materials:mesh.materials.append(material)
        uv=mesh.uv_layers.new(name='UV0')
        for poly,mi,coords,sm in zip(mesh.polygons,self.mats,self.uvs,self.smooth):
            poly.material_index=mi;poly.use_smooth=sm
            for li,co in zip(poly.loop_indices,coords):uv.data[li].uv=co
        obj['source_units']='metres';obj['front']='-Y';obj['original_geometry']=True
        return obj

def barn_geometry(materials):
    b=Builder('SM_PazFarm_Barn',materials);p=BARN
    L,D,H,R=p['length'],p['depth'],p['eave'],p['ridge'];dw,dh=p['door_width'],p['door_height']
    pl=p['plinth_height']; door_y=-D/2-.065
    # Concrete low plinth, split at the full-height front door threshold.
    b.box((0,D/2-.075,pl/2),(L,.15,pl),3)
    for x in [-L/2+.075,L/2-.075]:b.box((x,0,pl/2),(.15,D,pl),3)
    for x in [-(L+dw)/4,(L+dw)/4]:b.box((x,-D/2+.075,pl/2),((L-dw)/2,.15,pl),3)
    # Long wall sheets. Front leaves a true framed opening behind the sliding door.
    b.corrugated((-L/2,D/2,H),(1,0,0),(0,0,-1),L,lambda q:0,lambda q:H-pl,0)
    for x0,width in [(-L/2,(L-dw)/2),(dw/2,(L-dw)/2)]:
        b.corrugated((x0,-D/2,pl),(1,0,0),(0,0,1),width,lambda q:0,lambda q:H-pl,0)
    b.corrugated((-dw/2,-D/2,dh),(1,0,0),(0,0,1),dw,lambda q:0,lambda q:H-dh,0)
    # End walls follow the actual gable roof profile.
    for x,sgn in [(-L/2,-1),(L/2,1)]:
        b.corrugated((x,-sgn*D/2,pl),(0,sgn,0),(0,0,1),D,lambda q:0,
                     lambda q:H-pl+(R-H)*(1-abs(q-D/2)/(D/2)),0)
    # Structural corners / wall uprights, exposed outside the thin sheet.
    for x in [-L/2,L/2]:
        for y in [-D/2,D/2]: b.box((x,y,H/2),(.115,.115,H),1)
    for x in [-L/4,0,L/4]:b.box((x,D/2+.024,H/2),(.065,.075,H),1)
    for x in [-L/4,L/4]:b.box((x,-D/2-.024,H/2),(.065,.075,H),1)
    for y in [-D/2,D/2]:b.box((0,y,H-.08),(L,.13,.17),1)
    # Roof is two closed physical sheets with real corrugation and a capped ridge.
    over=p['roof_overhang']; slope=(R-H)/(D/2)
    run_len=math.sqrt((D/2+over)**2+((D/2+over)*slope)**2)
    for side in [-1,1]:
        # Reverse cross for south slope so exterior normals face upwards.
        cross=(side,0,0);origin=(-side*(L/2+over),0,R+.018)
        b.corrugated(origin,cross,(0,side,-slope),L+2*over,lambda q:0,lambda q:run_len,4,
                     depth=.006,thickness=.025)
        z=R-slope*(D/2+over)
        b.box((0,side*(D/2+over),z-.04),(L+2*over,.105,.13),4)
    # Broad ridge flashing, bent as two strips so ridge reads cleanly at distance.
    for side in [-1,1]:
        a=(-L/2-over,0,R+.082);u=(1,0,0);v=(0,side,-slope)
        b.corrugated(a,u,v,L+2*over,lambda q:0,lambda q:.19,4,pitch=L+2*over,depth=.002,thickness=.012)
    # Corner verge flashings protect both gable sheet edges.
    for x in [-L/2-over,L/2+over]:
        for side in [-1,1]:
            b.rod((x,0,R+.028),(x,side*(D/2+over),R-slope*(D/2+over)),.045,4,8)
    # Closed single sliding door, dark reveal and track. A photo can replace this default easily.
    b.box((0,door_y+.025,dh/2),(dw+.075,.035,dh+.04),2)
    b.corrugated((-dw/2,door_y-.018,.04),(1,0,0),(0,0,1),dw,lambda q:0,lambda q:dh-.06,1,
                 pitch=.16,depth=.028,thickness=.02)
    for x in [-dw/2,dw/2]:b.box((x,door_y-.055,dh/2),(.07,.07,dh),2)
    for z in [.08,dh-.02]:b.box((0,door_y-.06,z),(dw,.075,.075),2)
    b.box((dw*.36,door_y-.13,1.55),(.045,.06,.38),2)
    b.box((dw*.36,door_y-.11,1.72),(.09,.08,.04),2)
    b.box((dw*.36,door_y-.11,1.38),(.09,.08,.04),2)
    # Rail extends by one door width toward the right to show actual sliding travel.
    track_len=min(L-.45,dw*2+.3);track_center=(track_len-dw)/2
    b.box((track_center,door_y-.09,dh+.17),(track_len,.13,.11),2)
    for x in [-dw*.38,dw*.38]:
        b.box((x,door_y-.08,dh+.06),(.08,.09,.22),2)
        b.rod((x,door_y-.17,dh+.19),(x,door_y-.06,dh+.19),.065,2,12)
    obj=b.object();obj['parameter_defaults']=json.dumps(BARN);return obj


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def linear_from_srgb(c):
    a=np.asarray(c,dtype=float)
    return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)


def explicit_srgb_png(name,srgb):
    """Write known encoded sRGB bytes, then let the sRGB image node decode them.

    Generated byte-buffer images did not transform linear input values at save
    in Blender 5.2 here. Explicit encoding avoids silently saving dark [16,12,15].
    """
    a=np.rint(np.clip(srgb,0,1)*255).astype(np.uint8)
    h,w,_=a.shape
    def chunk(tag,payload):
        return struct.pack('>I',len(payload))+tag+payload+struct.pack('>I',zlib.crc32(tag+payload)&0xffffffff)
    raw=b''.join(b'\x00'+a[j].tobytes() for j in range(h))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'sRGB',b'\x00')+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
    path=ROOT/'Textures'/name;path.write_bytes(png)
    im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='sRGB'
    return im


def roof_material():
    """PNG median encodes sRGB 70,62,68; sRGB loading performs shader conversion."""
    n=1024;y,x=np.mgrid[0:n,0:n]/float(n-1)
    # Restrained, low-frequency procedural paint variation; no source photograph pixels.
    tint=1.+.007*np.sin(x*2*math.pi*7)*np.sin(y*2*math.pi*11)
    srgb=np.clip(np.asarray(ROOF_TARGET_SRGB)[None,None,:]/255.*tint[:,:,None],0,1)
    bc=np.ones((n,n,4));bc[:,:,:3]=linear_from_srgb(srgb)
    nm=np.ones_like(bc);nm[:,:,:3]=(.5,.5,1.)
    orm=np.ones_like(bc);orm[:,:,1]=ROOF_ROUGHNESS;orm[:,:,2]=ROOF_METALLIC
    tag='Barn_RoofCharcoal_v002'
    base=explicit_srgb_png('T_PazFarm_'+tag+'_BaseColor.png',srgb)
    normal=pc.image_file('T_PazFarm_'+tag+'_Normal.png',nm,True)
    packed=pc.image_file('T_PazFarm_'+tag+'_ORM.png',orm,True)
    mat=bpy.data.materials.new('M_PazFarm_'+tag);mat.use_nodes=True
    nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
    tb=nt.nodes.new('ShaderNodeTexImage');tb.image=base;nt.links.new(tb.outputs['Color'],bs.inputs['Base Color'])
    tn=nt.nodes.new('ShaderNodeTexImage');tn.image=normal
    nn=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tn.outputs['Color'],nn.inputs['Color']);nt.links.new(nn.outputs['Normal'],bs.inputs['Normal'])
    to=nt.nodes.new('ShaderNodeTexImage');to.image=packed
    sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(to.outputs['Color'],sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    bs.inputs['Specular IOR Level'].default_value=ROOF_SPECULAR_IOR_LEVEL
    mat['texture_files']=json.dumps(['Textures/'+Path(i.filepath_raw).name for i in (base,normal,packed)])
    mat['blend_mode_intent']='OPAQUE';mat['source']=pc.SOURCE['source'];mat['licence']='CC0-1.0'
    mat['orm_channels']='R=AmbientOcclusion G=Roughness B=Metallic'
    mat['normal_convention']='OpenGL +Y; flip green if using Unreal DirectX convention'
    mat['target_screenshot_srgb']=json.dumps(ROOF_TARGET_SRGB)
    return mat


def geometry_snapshot(ob):
    return {'vertices':[list(v.co) for v in ob.data.vertices],
            'faces':[list(p.vertices) for p in ob.data.polygons],
            'material_indices':[p.material_index for p in ob.data.polygons],
            'transform':[list(row) for row in ob.matrix_world]}


def main():
    for folder in ['Blend','FBX','Textures','Previews','Reports','Temp/barn']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
    source_paths=[ORIGINAL/'Blend/Barn.blend',ORIGINAL/'FBX/SM_PazFarm_Barn.fbx']
    originals={str(p.relative_to(ORIGINAL)):digest(p) for p in source_paths}
    bpy.ops.wm.open_mainfile(filepath=str(ORIGINAL/'Blend/Barn.blend'))
    bpy.context.preferences.filepaths.save_version=0
    bpy.context.preferences.filepaths.temporary_directory=str(ROOT/'Temp/barn')
    scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=4
    old=bpy.data.objects['SM_PazFarm_Barn'];old_state=geometry_snapshot(old)
    materials=list(old.data.materials)
    copied=[]
    for mat in materials:
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                im=node.image;src=Path(bpy.path.abspath(im.filepath));dst=ROOT/'Textures'/src.name
                if not dst.exists():shutil.copyfile(src,dst)
                assert digest(src)==digest(dst)
                im.filepath=str(dst)
                copied.append({'texture':str(dst.relative_to(ROOT)),'sha256':digest(dst)})
    collision_names=['UCX_SM_PazFarm_Barn_'+str(i).zfill(2) for i in range(3)]
    collisions=[bpy.data.objects[n] for n in collision_names]
    collision_before={ob.name:geometry_snapshot(ob) for ob in collisions}
    old_material_names=[m.name for m in materials]
    bpy.data.objects.remove(old,do_unlink=True)
    materials.append(roof_material())
    barn=barn_geometry(materials)
    new_state=geometry_snapshot(barn)
    assert old_state['faces']==new_state['faces'],'Unexpected topology change'
    roof_vertices={i for p in barn.data.polygons if p.material_index==4 for i in p.vertices}
    unchanged=[i for i in range(len(barn.data.vertices)) if i not in roof_vertices]
    changed_outside_roof=[i for i in unchanged if old_state['vertices'][i]!=new_state['vertices'][i]]
    assert not changed_outside_roof,changed_outside_roof[:20]
    material_errors=[i for i,(a,b) in enumerate(zip(old_state['material_indices'],new_state['material_indices'])) if a!=b and not(a==1 and b==4)]
    assert not material_errors
    barn,rec=pc.asset('SM_PazFarm_Barn',[barn],collisions,budget=30000,nominal=[20.,12.,8.],notes=[
        'Offline v002 roof-only revision. No native import or rendering has been performed.',
        'Source wall footprint remains 20 x 12 m, eave 6 m, ridge 8 m. Do not bake the existing 25.8 x 20.5 m map instance scale into this mesh.',
        'Original four material slots retained in exact order. New slot 4 M_PazFarm_Barn_RoofCharcoal_v002 is assigned only to roof sheets, ridge, eave and verge flashings.',
        'Roof corrugation relief reduced from 0.045 m to 0.006 m. Corrugation pitch, wall corrugation, doors and trim are unchanged.',
        'Roof BaseColor PNG median target is sRGB 70,62,68; roughness 0.94, metallic 0, Blender Specular IOR Level 0.20, flat normal map. Appearance matching still depends on native exposure.',
        'Exact original pivot, orientation and all three UCX boxes retained. Ground-centred origin; source front -Y, Z up.',
        'All geometry/textures original CC0 artwork. No satellite pixels used for textures.'])
    collision_after={ob.name:geometry_snapshot(ob) for ob in collisions}
    assert collision_before==collision_after,'Collision changed'
    rec['collision_geometry']=[{'name':ob.name,'type':'BOX','bounds_metres':pc.bounds(ob),'size_metres':[round(pc.bounds(ob)[1][i]-pc.bounds(ob)[0][i],6) for i in range(3)]} for ob in collisions]
    rec['qa'].update({'unchanged_nonroof_vertices':len(unchanged),'changed_nonroof_vertices':0,'original_UCX_exact':True,'original_material_slots_preserved':old_material_names,'new_roof_slot_index':4})
    pc.preview(barn,rec,azimuth=-63,elevation=22)
    overhead=dict(rec,preview='Previews/SM_PazFarm_Barn_Roof_v002.png')
    pc.preview(barn,overhead,azimuth=-63,elevation=63)
    pc.save_family('Barn.blend',[rec],dict(BARN,roof_corrugation_depth_v002=ROOF_RELIEF_M,roof_target_srgb=ROOF_TARGET_SRGB))
    originals_after={str(p.relative_to(ORIGINAL)):digest(p) for p in source_paths}
    assert originals==originals_after
    rec['qa']['original_blend_fbx_hashes_unchanged']=True
    pc.report('barn_v002.json',[rec],{'status':'Offline candidate ready for import and native verification',
        'original_hashes_unchanged':originals,'retained_texture_hashes':copied,
        'roof_material_parameters':{'target_srgb':ROOF_TARGET_SRGB,'roughness':ROOF_ROUGHNESS,'metallic':ROOF_METALLIC,'specular_ior_level':ROOF_SPECULAR_IOR_LEVEL,'normal':'flat'},
        'slot_mapping':{'0':'M_PazFarm_Barn_WallGalvanized','1':'M_PazFarm_Barn_RoofPaintedGrey (non-roof trim, uprights and sliding door; unchanged)','2':'M_PazFarm_Barn_DarkHardware','3':'M_PazFarm_Barn_ConcretePlinth','4':'M_PazFarm_Barn_RoofCharcoal_v002 (roof only; NEW)'},
        'changes':{'roof_relief_before_m':.045,'roof_relief_after_m':ROOF_RELIEF_M,'nonroof_geometry_changed':False,'UCX_changed':False},
        'native_verification':False,'source_script':'Scripts/build_barn_v002.py'})


def audit():
    from collections import Counter
    data=json.loads((ROOT/'Reports/barn_v002.json').read_text());rec=data['assets'][0]
    pc.reset();bpy.ops.import_scene.fbx(filepath=str(ROOT/rec['fbx']))
    ob=bpy.data.objects['SM_PazFarm_Barn'];bpy.context.view_layer.update();ob.data.calc_loop_triangles()
    bb=pc.bounds(ob);size=[bb[1][i]-bb[0][i] for i in range(3)]
    edges=Counter()
    for p in ob.data.polygons:
        ids=list(p.vertices)
        for i,a in enumerate(ids):edges[tuple(sorted((a,ids[(i+1)%len(ids)])))]+=1
    uv=ob.data.uv_layers.active;zero_uv=0
    for tri in ob.data.loop_triangles:
        a,b,c=[uv.data[i].uv for i in tri.loops]
        area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
        if area<1e-12:zero_uv+=1
    qa={'fbx_reimport_dimensions_metres':size,'fbx_reimport_triangles':len(ob.data.loop_triangles),
        'triangle_budget':30000,'zero_area_triangles':sum(t.area<1e-12 for t in ob.data.loop_triangles),
        'zero_area_uv_triangles':zero_uv,'non_manifold_boundary_edges':sum(v!=2 for v in edges.values()),
        'uv0_layer_names':[l.name for l in ob.data.uv_layers],
        'material_slots':[m.name for m in ob.data.materials],
        'collision_objects':[o.name for o in bpy.context.scene.objects if o.name.startswith('UCX_')],
        'max_dimension_error_m':max(abs(a-b) for a,b in zip(size,rec['size_metres_W_D_H']))}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend/Barn.blend'))
    imgs=[i for i in bpy.data.images if i.source=='FILE' and i.filepath]
    qa['source_reopen']={'scale_length':bpy.context.scene.unit_settings.scale_length,
        'texture_paths_relative':all(i.filepath.startswith('//') for i in imgs),
        'missing_textures':[i.filepath for i in imgs if not Path(bpy.path.abspath(i.filepath)).is_file()],
        'textures_all_1k':all(tuple(i.size)==(1024,1024) for i in imgs),
        'pivot':list(bpy.data.objects['SM_PazFarm_Barn'].location)}
    qa['pass']=all([qa['fbx_reimport_triangles']<=30000,qa['zero_area_triangles']==0,qa['zero_area_uv_triangles']==0,
        qa['non_manifold_boundary_edges']==0,qa['max_dimension_error_m']<.0001,len(qa['collision_objects'])==3,
        qa['source_reopen']['scale_length']==1.,qa['source_reopen']['texture_paths_relative'],
        not qa['source_reopen']['missing_textures'],qa['source_reopen']['textures_all_1k'],qa['source_reopen']['pivot']==[0,0,0]])
    qa['sha256']={rel:digest(ROOT/rel) for rel in ['Blend/Barn.blend','FBX/SM_PazFarm_Barn.fbx']}
    (ROOT/'Reports/barn_v002_readback.json').write_text(json.dumps(qa,indent=2))
    assert qa['pass'],qa


if __name__=='__main__':
    if '--audit' in sys.argv:audit()
    else:main()
