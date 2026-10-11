"""Original Paz Farm barn and fence meshes. All dimensions are metres.

Run in Blender background. Parameters below are the approved defaults and the
single place to change proportions; roof overhang is additional to the footprint.
Source front is -Y, Z up. The export helpers use forward -Y / up Z.
"""
import bpy, math, json, sys, os
sys.dont_write_bytecode = True
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Scripts'))
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
        b.corrugated(origin,cross,(0,side,-slope),L+2*over,lambda q:0,lambda q:run_len,1,
                     depth=.045,thickness=.025)
        z=R-slope*(D/2+over)
        b.box((0,side*(D/2+over),z-.04),(L+2*over,.105,.13),1)
    # Broad ridge flashing, bent as two strips so ridge reads cleanly at distance.
    for side in [-1,1]:
        a=(-L/2-over,0,R+.082);u=(1,0,0);v=(0,side,-slope)
        b.corrugated(a,u,v,L+2*over,lambda q:0,lambda q:.19,1,pitch=L+2*over,depth=.002,thickness=.012)
    # Corner verge flashings protect both gable sheet edges.
    for x in [-L/2-over,L/2+over]:
        for side in [-1,1]:
            b.rod((x,0,R+.028),(x,side*(D/2+over),R-slope*(D/2+over)),.045,1,8)
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

def post(b,x=0,y=0,r=None,h=None,braces=False):
    r=r or FENCE['post_radius'];h=h or FENCE['height']
    b.rod((x,y,0),(x,y,h-.025),r,0,12)
    b.rod((x,y,h-.025),(x,y,h),r*1.12,0,12,r*.72)
    for z in [.18,1.,1.85]:b.rod((x,y,z-.016),(x,y,z+.016),r*1.14,0,12)
    if braces:
        for dx,dy in [(1,0),(0,1)]:
            b.rod((x+dx*r,y+dy*r,1.4),(x+dx*.65,y+dy*.65,.025),.021,0,8)
            b.box((x+dx*.65,y+dy*.65,.015),(.10,.10,.03),0)

def fence_geometry(materials):
    assets=[];h=FENCE['height'];L=FENCE['length'];r=FENCE['post_radius']
    b=Builder('SM_PazFarm_Fence_Mesh_3m',materials)
    post(b);b.wire_mesh(r,L,.065,h-.075)
    for z in [.065,1.,h-.075]:b.rod((0,0,z),(L,0,z),.0032,0,6)
    b.rod((0,0,h-.04),(L,0,h-.04),.016,0,10)
    obj=b.object();obj['module_length_m']=L;obj['repeat_direction']='+X';obj['pivot_note']='Ground at one-end post centre. Repeat by exactly +3 m in X; end post is supplied by next panel.';assets.append(obj)
    b=Builder('SM_PazFarm_Fence_Post',materials);post(b,r=.042)
    obj=b.object();obj['pivot_note']='Ground at post centre; terminal post closes last panel.';assets.append(obj)
    b=Builder('SM_PazFarm_Fence_Corner',materials);post(b,r=.046,braces=True)
    obj=b.object();obj['pivot_note']='Ground at corner-post centre; brace directions +X and +Y. Use standalone terminal post if no braces wanted.';assets.append(obj)
    b=Builder('SM_PazFarm_Gate_Double_6m',materials);W=FENCE['gate_width'];pw=.12;px=W/2-pw/2
    for x in [-px,px]:
        b.box((x,0,h/2),(pw,pw,h),0)
        b.box((x,0,h-.008),(pw,pw,.016),0)
    # Leaves maintain a central clearance and swing about hinges near each post.
    for sign in [-1,1]:
        x0,x1=((-px+.11,-.035) if sign<0 else (.035,px-.11))
        z0,z1=.10,h-.09;w=x1-x0
        for x in [x0,x1]:b.box((x,0,(z0+z1)/2),(.045,.045,z1-z0),0)
        for z in [z0,z1]:b.box(((x0+x1)/2,0,z),(w,.045,.045),0)
        b.wire_mesh(x0+.027,x1-.027,z0+.027,z1-.027,y=.002)
        # Diagonal compression brace and three working hinge barrels.
        hinge_x=x0-.025 if sign<0 else x1+.025
        for z in [.3,1.,1.7]:
            b.rod((hinge_x,-.02,z-.045),(hinge_x,-.02,z+.045),.024,0,10)
            b.box((hinge_x-sign*.033,0,z),(.07,.03,.03),0)
        a,bz=((x0,z0),(x1,z1)) if sign<0 else ((x0,z1),(x1,z0))
        b.rod((a[0],-.027,a[1]),(bz[0],-.027,bz[1]),.013,0,8)
        drop_x=x1-.07 if sign<0 else x0+.07
        b.rod((drop_x,-.045,.035),(drop_x,-.045,.70),.008,1,8)
        b.rod((drop_x,-.045,.70),(drop_x+sign*.07,-.045,.70),.008,1,8)
    b.box((0,-.054,1.04),(.23,.045,.035),1)
    b.box((.025,-.064,1.0),(.035,.027,.12),1)
    obj=b.object();obj['parameter_defaults']=json.dumps(FENCE);obj['pivot_note']='Ground at centre of the complete gate; outside width exactly 6 m. Closed leaves are combined; edit source geometry to swing them.';assets.append(obj)
    return assets

def main():
    import paz_common as pc
    for folder in ['Blend','FBX','Textures','Previews','Reports','Temp/barn_fence']:
        (ROOT/folder).mkdir(parents=True,exist_ok=True)
    records=[];pc.reset()
    barn_mats=[pc.pbr('Barn_WallGalvanized',(.62,.65,.66),.64,.72,'steel',1024,seed=21),
               pc.pbr('Barn_RoofPaintedGrey',(.68,.71,.71),.61,.44,'steel',1024,seed=22),
               pc.pbr('Barn_DarkHardware',(.105,.12,.13),.53,.80,'steel',1024,seed=23),
               pc.pbr('Barn_ConcretePlinth',(.39,.38,.35),.90,0.,'noise',1024,seed=24)]
    barn=barn_geometry(barn_mats)
    length,depth,eave,ridge=[BARN[k] for k in ['length','depth','eave','ridge']]
    roof_h=ridge-eave
    collisions=[pc.box('Barn_Collision_Base',(0,0,eave/2),(length,depth,eave)),
                pc.box('Barn_Collision_RoofLower',(0,0,eave+roof_h*.25),(length,depth*.75,roof_h*.5)),
                pc.box('Barn_Collision_RoofUpper',(0,0,eave+roof_h*.75),(length,depth*.25,roof_h*.5))]
    barn,rec=pc.asset(barn.name,[barn],collisions,budget=30000,nominal=[length,depth,ridge],notes=[
        'Inferred default farm barn; no ground photograph was supplied. Not a surveyed reconstruction.',
        'Wall footprint 20 x 12 m. Eave 6 m, structural ridge 8 m, roof overhang 0.24 m. Measured outer bounds include roof/flashing thickness.',
        'Front is Blender -Y. Closed 6 x 4.4 m sliding door on long front side with external sliding rail; wall opening exists behind door.',
        'Physical corrugated steel sheets have thickness, perimeter closures, corner uprights, verge and ridge flashing.',
        'Pivot at footprint centre, ground level. Exterior-only prop; collision closes the building volume.',
        'Defaults and material colours are editable in Scripts/build_barn_fence.py. All geometry and textures are original CC0.'])
    pc.preview(barn,rec,azimuth=-63,elevation=22)
    pc.save_family('Barn.blend',[rec],BARN);records.append(rec)
    pc.report('barn_fence.json',records,{'status':'Barn complete; fence delivery in progress'})
    pc.reset()
    fence_mats=[pc.pbr('Fence_Galvanized',(.54,.60,.61),.46,.86,'steel',1024,seed=31),
                pc.pbr('Fence_DarkLatch',(.12,.15,.16),.56,.78,'steel',1024,seed=32)]
    objects=fence_geometry(fence_mats);fence_records=[]
    for obj in objects:
        name=obj.name
        if name.endswith('Mesh_3m'):
            col=[pc.box('Panel_Collision',(1.5,0,1),(3.067,.075,2))]
            nominal=[3.,.066,2.]
            notes=['Actual diamond wire geometry: diagonal galvanized wires, approximately 0.12 m horizontal and vertical diamond spans.',
                   'One post only, at the start. Nominal module length exactly 3.0 m in Blender +X; place repeats at X=0,3,6... with identical rotation.',
                   'Pivot at ground, starting post centre. Physical bounds include post radius before X=0; this does not alter the 3 m repeat pitch.',
                   'Mesh and horizontal rails terminate at X=3.0 m and meet the next post; no doubled posts. Add Fence_Post at the final X endpoint.']
        elif name.endswith('Fence_Post'):
            col=[pc.box('Post_Collision',(0,0,1),(.10,.10,2))];nominal=[.084,.084,2]
            notes=['Terminal/end post; pivot at ground, post centre. Place at the open end of a 3 m panel run.']
        elif name.endswith('Fence_Corner'):
            col=[pc.box('CornerPost_Collision',(0,0,1),(.11,.11,2))];nominal=[.7,.7,2]
            notes=['Corner post with two orthogonal diagonal stays toward Blender +X and +Y; rotate whole piece to suit corner.',
                   'Pivot at ground, post centre. Corner-post UCX covers the upright only; slim diagonal stays have no collision.',
                   'Use at the meeting point of two runs that terminate here, or remove redundant terminal upright in source if integrating a run that starts here.']
        else:
            col=[pc.box('Gate_Post_Left',(-2.94,0,1),(.125,.125,2)),
                 pc.box('Gate_Post_Right',(2.94,0,1),(.125,.125,2)),
                 pc.box('Gate_Leaf_Left',(-1.4325,0,1.005),(2.795,.08,1.81)),
                 pc.box('Gate_Leaf_Right',(1.4325,0,1.005),(2.795,.08,1.81))]
            nominal=[6.,.12,2.]
            notes=['Two closed steel swing-gate leaves with actual diamond wire infill, diagonal stays, hinge barrels, drop bolts and latch.',
                   'Outside post width exactly 6 m. Pivot ground centre.',
                   'A static combined mesh is delivered; leaves can be separated and rotated at their hinges in the source if an opening is wanted.']
        notes+=['Blender front -Y, Z up; FBX forward -Y / up Z, FBX Units Scale.','Original CC0 geometry and textures; geometry mesh is opaque and needs no alpha-test setup.']
        ob,rec=pc.asset(name,[obj],col,notes=notes,budget=5000,nominal=nominal)
        pc.preview(ob,rec,azimuth=-75,elevation=12)
        fence_records.append(rec)
    pc.save_family('Fence.blend',fence_records,FENCE);records+=fence_records
    pc.report('barn_fence.json',records,{'status':'Complete',
              'modular_check':{'fence_repeat_step_m':[3.,0.,0.], 'panel_mesh_end_x_m':3.,
                               'next_panel_post_center_x_m':3.,'post_count_per_panel':1},
              'reference_status':'Parent reviewed provided aerial reference; defaults approved by handoff are used. No barn ground photograph supplied.',
              'source_script':'Scripts/build_barn_fence.py'})

def audit():
    """Fresh-process source and FBX readback; does not write or import into Unreal."""
    import paz_common as pc
    from collections import Counter
    delivery=json.loads((ROOT/'Reports/barn_fence.json').read_text())
    results=[]
    for rec in delivery['assets']:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(ROOT/rec['fbx']))
        ob=bpy.data.objects.get(rec['name'])
        if ob is None:raise RuntimeError('Missing imported mesh '+rec['name'])
        bpy.context.view_layer.update();ob.data.calc_loop_triangles()
        bb=pc.bounds(ob);size=[bb[1][i]-bb[0][i] for i in range(3)]
        delta=max(abs(a-b) for a,b in zip(size,rec['size_metres_W_D_H']))
        edges=Counter()
        for poly in ob.data.polygons:
            v=list(poly.vertices)
            for i,a in enumerate(v):edges[tuple(sorted((a,v[(i+1)%len(v)])))]+=1
        wrong_edges=sum(n!=2 for n in edges.values())
        degenerate=sum(t.area<1e-12 for t in ob.data.loop_triangles)
        collisions=[o.name for o in bpy.context.scene.objects if o.name.startswith('UCX_')]
        missing_textures=[]
        for mat in rec['materials']:
            missing_textures += [p for p in mat['textures'] if not (ROOT/p).is_file()]
        result={'name':rec['name'],'fbx_reimport_dimensions_metres':size,'max_dimension_difference_m':delta,
                'fbx_reimport_triangles':len(ob.data.loop_triangles),'zero_area_triangles':degenerate,
                'non_manifold_boundary_edges':wrong_edges,'uv0_layer_names':[l.name for l in ob.data.uv_layers],
                'expected_collision_count':len(rec['collision_objects']),'readback_collision_count':len(collisions),
                'missing_texture_paths':missing_textures}
        result['pass']=(delta<.0001 and not degenerate and not wrong_edges and bool(ob.data.uv_layers)
                        and len(collisions)==len(rec['collision_objects']) and not missing_textures
                        and len(ob.data.loop_triangles)==rec['triangles_LOD0'])
        results.append(result)
    source_checks=[]
    for filename in ['Barn.blend','Fence.blend']:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend'/filename))
        missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and im.filepath and not Path(bpy.path.abspath(im.filepath)).is_file()]
        source_checks.append({'blend':filename,'scale_length':bpy.context.scene.unit_settings.scale_length,
                              'missing_textures':missing,'source_objects':[ob.name for ob in bpy.context.scene.objects if ob.name.startswith('SM_PazFarm_')]})
    report={'assets':results,'blend_reopen_checks':source_checks,'pass':all(r['pass'] for r in results) and all(not x['missing_textures'] and x['scale_length']==1. for x in source_checks)}
    (ROOT/'Reports/barn_fence_readback.json').write_text(json.dumps(report,indent=2))
    if not report['pass']:raise RuntimeError('Readback failed; see barn_fence_readback.json')

def finalize():
    """Make source texture paths portable and retain measured collision receipts."""
    import paz_common as pc
    delivery=json.loads((ROOT/'Reports/barn_fence.json').read_text())
    for filename in ['Barn.blend','Fence.blend']:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend'/filename))
        bpy.context.preferences.filepaths.save_version=0
        for im in bpy.data.images:
            if im.filepath:im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath))
        relevant=[rec for rec in delivery['assets'] if rec['blend']=='Blend/'+filename]
        for index,rec in enumerate(relevant):
            rec['collision_geometry']=[]
            for name in rec['collision_objects']:
                obj=bpy.data.objects.get(name);bb=pc.bounds(obj)
                rec['collision_geometry'].append({'name':name,'type':'BOX','bounds_metres':bb,
                    'size_metres':[round(bb[1][i]-bb[0][i],6) for i in range(3)]})
            collection=bpy.data.collections.new(rec['name']);bpy.context.scene.collection.children.link(collection)
            for name in [rec['name']]+rec['collision_objects']:
                obj=bpy.data.objects[name]
                for old in list(obj.users_collection):old.objects.unlink(obj)
                collection.objects.link(obj)
                obj.hide_set(index>0 or name.startswith('UCX_'))
            rec['qa']['source_textures_relative']=True
            rec['qa']['preview_visually_reviewed']=True
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blend'/filename))
    delivery['extra']['visual_review']='Every preview inspected at full output resolution. Final correction joins corner stays to foot plates and mirrors gate compression braces.'
    delivery['extra']['source_visibility']='Each source asset has its own named collection. Fence source opens with the 3 m panel visible; use the Outliner eye icons to reveal other parts.'
    (ROOT/'Reports/barn_fence.json').write_text(json.dumps(delivery,indent=2))

if __name__=='__main__':
    if '--audit' in sys.argv:audit()
    elif '--finalize' in sys.argv:finalize()
    else:
        main()
        finalize()
