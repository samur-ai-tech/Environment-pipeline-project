"""Original, parameterized Paz Farm shade-house and greenhouse kits.

Run with bundled Blender in background. Optional -- --parameters <JSON> replaces
the listed defaults; all output remains inside AstraModels. No external textures.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, math, json
from mathutils import Vector
import paz_common as C

P = dict(net_width=8.0, net_depth=4.0, net_height=4.0, net_post=.08,
         net_rail=.04, net_door_width=1.6, net_door_height=2.5,
         greenhouse_span=9.0, greenhouse_height=4.5,
         greenhouse_length=4.0, greenhouse_arch_segments=40,
         greenhouse_door_width=1.8, greenhouse_door_height=2.2,
         render_previews=True, render_assembled=True)
if '--' in sys.argv:
    args=sys.argv[sys.argv.index('--')+1:]
    if '--parameters' in args:
        supplied=json.loads(Path(args[args.index('--parameters')+1]).read_text())
        if set(supplied)-set(P): raise ValueError('Unknown parameters: '+str(set(supplied)-set(P)))
        P.update(supplied)
for folder in ('Blend','FBX','Textures','Previews','Reports','Temp'):
    (C.ROOT/folder).mkdir(parents=True,exist_ok=True)

ALL=[]

def panel(name,corners,mat,uvscale=1):
    # Order corners counterclockwise as seen from the visible side.
    p0,p1,p2,p3=[Vector(p) for p in corners]
    w=(p1-p0).length; h=(p3-p0).length
    return C.mesh(name,corners,[(0,1,2,3)],mat,
                  [[(0,0),(w*uvscale,0),(w*uvscale,h*uvscale),(0,h*uvscale)]])

def box_limits(name,lo,hi,mat=None,bevel=0):
    return C.box(name,tuple((lo[i]+hi[i])/2 for i in range(3)),
                 tuple(hi[i]-lo[i] for i in range(3)),mat,bevel)

def wire(name,a,b,r,mat):
    return C.cylinder(name,a,b,r,mat,vertices=8)

def collision_beam(name,a,b,thickness):
    a,b=Vector(a),Vector(b); v=b-a
    ob=C.box(name,(a+b)/2,(thickness,thickness,v.length))
    ob.rotation_euler=v.to_track_quat('Z','Y').to_euler()
    return ob

def store(name,objects,collisions,notes,nominal,records,pivot=(0,0,0)):
    ob,rec=C.asset(name,objects,collisions,pivot,notes,budget=5000,nominal=nominal)
    records.append(rec); ALL.append(rec)
    if P['render_previews']: C.preview(ob,rec)
    return ob,rec

def finalize_family(filename,records,params):
    # Each component retains local origin for editing/export; prevent the source
    # from opening with every overlapping kit component visible simultaneously.
    first=records[0]['name']
    for ob in bpy.context.scene.objects:
        ob.hide_set(ob.name != first)
        ob.hide_render=(ob.name != first)
    C.save_family(filename,records,params)
    # Images created with bpy.data.images.new can remain GENERATED after save;
    # their source type does not exempt their PNG paths from portability.
    for im in bpy.data.images:
        if im.name.startswith('T_PazFarm_') and im.filepath:
            im.filepath=bpy.path.relpath(im.filepath)
    bpy.ops.wm.save_as_mainfile(filepath=str(C.ROOT/'Blend'/filename))

def net_house():
    C.reset(); records=[]; assets={}
    w,d,h,t,r=[P[k] for k in ('net_width','net_depth','net_height','net_post','net_rail')]
    steel=C.pbr('NetGalvanizedSteel',(.48,.52,.54),.36,.87,'steel',res=1024)
    hem=C.pbr('NetBinding',(.30,.31,.28),.77,0,'noise',res=1024)
    netmats={
      'White':C.pbr('NetWhite',(.89,.91,.85),.68,0,'net',res=1024),
      'Black':C.pbr('NetBlack',(.031,.042,.034),.72,0,'net',res=1024)
    }
    # 16 repeats per metre x 8 openings per repeat = 128 mesh openings/metre.
    # The texture's RGBA alpha is essential: a solid material is not equivalent.
    net_uv=16.0
    for variant,net in netmats.items():
        parts=[]; coll=[]
        parts.append(box_limits('LowerLeftOwnedPost',(0,0,0),(t,t,h-r),steel,.002))
        coll.append(box_limits('PostCollision',(0,0,0),(t,t,h-r)))
        parts.append(box_limits('LeadingOwnedRail',(r,0,h-r),(w,r,h),steel,.001))
        parts.append(box_limits('LeftOwnedRail',(0,0,h-r),(r,d,h),steel,.001))
        coll += [box_limits('LeadingRailCollision',(r,0,h-r),(w,r,h)),
                 box_limits('LeftRailCollision',(0,0,h-r),(r,d,h))]
        parts.append(panel('FlatShadeNet',[(0,0,h-.007),(w,0,h-.007),(w,d,h-.007),(0,d,h-.007)],net,net_uv))
        # Interior tension wires support the shade fabric, never crossing edges.
        for xx in (w*.25,w*.5,w*.75):
            parts.append(wire('RoofTensionWire',(xx,r,h-.015),(xx,d,h-.015),.0025,steel))
        name='SM_PazFarm_NetHouse_Bay_8x4'+('' if variant=='White' else '_'+variant)
        assets['bay_'+variant]=store(name,parts,coll,[
          'Default flat white shade house; Black is the alternative material variant.',
          'Pivot is the south-west/lower-left ground corner (0,0,0); source front is -Y.',
          'Tile at (i*8,j*4,0) in Blender metres. Exact rendered envelope is 8 x 4 x 4 m.',
          'Half-open 2D lattice: each bay owns ONLY its lower-left post, leading Y=0 rail and left X=0 rail. Adjacent bays do not duplicate posts or rails.',
          'Close external right/rear boundaries with supplied Post_4m and ClosureBeam pieces; see Reports/structures_assembly.md.',
          'Net UV0 repeats at 16/m: approximately 7.8 mm openings; use BaseColor alpha as masked opacity with two-sided material.',
          'All dimensions are adjustable in Scripts/build_structures.py or --parameters JSON.'
        ],[w,d,h],records)
        side=[panel('VerticalShadeNet',[(0,0,0),(d,0,0),(d,0,h),(0,0,h)],net,net_uv)]
        # Binding cord is visually distinct from the main structural rails.
        for z in (.012,h-.012): side.append(wire('NetHem',(0,0,z),(d,0,z),.006,hem))
        for x in (.006,d-.006): side.append(wire('VerticalHem',(x,0,.012),(x,0,h-.012),.005,hem))
        name='SM_PazFarm_NetHouse_Side_4'+('' if variant=='White' else '_'+variant)
        assets['side_'+variant]=store(name,side,[],[
          'Four-metre net curtain; source plane is XZ at Y=0; pivot is left ground edge.',
          'Curtain has binding hems only. Loadbearing boundary rails/posts come from Bay and closure pieces, so walls do not duplicate corner posts.',
          'Place X-facing walls at x=4*k; rotate 90 degrees about Z for Y-facing walls. Panels tile exactly at a 4 m pitch.',
          'No collision for flexible net; two-sided masked opacity from net BaseColor alpha.'
        ],[d,0,h],records)
        dw=P['net_door_width']; dh=P['net_door_height']; xl=(d-dw)/2; xr=(d+dw)/2
        parts=[panel('DoorLeftCurtain',[(0,0,0),(xl,0,0),(xl,0,h),(0,0,h)],net,net_uv),
               panel('DoorRightCurtain',[(xr,0,0),(d,0,0),(d,0,h),(xr,0,h)],net,net_uv),
               panel('DoorHeaderCurtain',[(xl,0,dh),(xr,0,dh),(xr,0,h),(xl,0,h)],net,net_uv)]
        coll=[]
        jamb=.045
        for xx in (xl-jamb/2,xr+jamb/2):
            parts.append(C.box('DoorJamb',(xx,0,dh/2),(jamb,.055,dh),steel,.002))
            coll.append(C.box('JambCollision',(xx,0,dh/2),(jamb,.055,dh)))
        parts.append(C.box('DoorLintel',(d/2,0,dh+jamb/2),(dw+2*jamb,.055,jamb),steel,.002))
        coll.append(C.box('LintelCollision',(d/2,0,dh+jamb/2),(dw+2*jamb,.055,jamb)))
        # A light framed single leaf folded 85 degrees inward. The default
        # opening remains walkable, without a collision slab spanning it.
        leafw=dw-.04; leafh=dh-.04; hinge=Vector((xl+.02,.045,0)); angle=math.radians(85)
        axis=Vector((math.cos(angle),math.sin(angle),0)); a=hinge+Vector((0,0,.025)); b=a+axis*leafw
        c=b+Vector((0,0,leafh)); e=a+Vector((0,0,leafh))
        parts.append(panel('OpenNetDoor',[a,b,c,e],net,net_uv))
        for aa,bb in ((a,b),(b,c),(c,e),(e,a)):
            parts.append(wire('OpenDoorLeafFrame',aa,bb,.012,steel))
        for xx in (.006,d-.006):parts.append(wire('WallHem',(xx,0,.01),(xx,0,h-.01),.005,hem))
        for zz in (.012,h-.012):parts.append(wire('WallHem',(0,0,zz),(d,0,zz),.006,hem))
        name='SM_PazFarm_NetHouse_Door'+('' if variant=='White' else '_'+variant)
        assets['door_'+variant]=store(name,parts,coll,[
          'Four-metre wall with a 1.6 m wide x 2.5 m high doorway; leaf is folded inward by 85 degrees in the default.',
          'Pivot left ground edge; XZ wall at Y=0; positive Y is inward.',
          'UCX is limited to jambs/lintel, with no box blocking the doorway. Open leaf is visual-only.',
          'NetHouse has no sill crossing the walking opening. Door width/height and folded-leaf construction are parameterized.'
        ],[d,round(leafw*math.sin(angle),4),h],records)
    name='SM_PazFarm_NetHouse_Post_4m'
    assets['post']=store(name,[box_limits('BoundaryPost',(0,0,0),(t,t,h-r),steel,.002)],
      [box_limits('PostCollision',(0,0,0),(t,t,h-r))],[
       'Supplementary outer-boundary post. Pivot at lower-left footprint corner; visible post reaches underside of 4 m roof rail.',
       'For Nx by Ny bays, place right edge at x=Nx*8-0.08, y=j*4; rear edge at x=i*8,y=Ny*4-0.08; add one far corner at x=Nx*8-0.08,y=Ny*4-0.08.',
       'Right-edge j=0..Ny-1; rear-edge i=0..Nx-1. This recipe creates (Nx+1)*(Ny+1) posts, with no duplicate positions.'
      ],[t,t,h-r],records)
    for length,tag in ((d,'4m'),(w,'8m')):
        # Ground pivot makes closure pieces align by the same corner coordinates.
        name='SM_PazFarm_NetHouse_ClosureBeam_'+tag
        assets['beam_'+tag]=store(name,[box_limits('BoundaryTopRail',(0,0,h-r),(length,r,h),steel,.001)],
          [box_limits('BoundaryTopRailCollision',(0,0,h-r),(length,r,h))],[
           'Supplementary missing outer-boundary top rail, modelled along +X at elevation 3.96..4.00 m, pivot ground at one end.',
           'Rear edge: use 8m beam at (i*8,Ny*4-0.04,0). Right edge: 4m beam rotated +90deg, at (Nx*8,j*4,0).',
           'Beam end-to-end seams are flush. At outer corners perpendicular rail ends meet with a small intended structural corner joint; no doubled coplanar rail surfaces.'
          ],[length,r,r],records)
    if P['render_assembled']:
        for var in ('White','Black'):
            copies=[]; nx=ny=2
            def dup(key,loc,rot=0):
                source=assets[key][0]; ob=source.copy(); ob.data=source.data.copy();bpy.context.collection.objects.link(ob)
                ob.hide_set(False);ob.hide_render=False;ob.location=loc;ob.rotation_euler.z=rot;copies.append(ob)
            for i in range(nx):
                for j in range(ny):dup('bay_'+var,(i*w,j*d,0))
            for j in range(ny):dup('post',(nx*w-t,j*d,0))
            for i in range(nx):dup('post',(i*w,ny*d-t,0))
            dup('post',(nx*w-t,ny*d-t,0))
            for i in range(nx):dup('beam_8m',(i*w,ny*d-r,0))
            for j in range(ny):dup('beam_4m',(nx*w,j*d,0),math.pi/2)
            for k in range(nx*2):
                dup(('door_' if k==1 else 'side_')+var,(k*d,0,0))
                dup('side_'+var,(k*d,ny*d,0))
            for j in range(ny):
                dup('side_'+var,(0,j*d,0),math.pi/2)
                dup('side_'+var,(nx*w,j*d,0),math.pi/2)
            assembled=C.combine('PREVIEW_ONLY_NetHouse_2x2_'+var,copies)
            rec={'preview':'Previews/NetHouse_Assembled_2x2_'+var+'.png'}
            C.preview(assembled,rec,elevation=24)
            bpy.data.objects.remove(assembled,do_unlink=True)
    finalize_family('NetHouse.blend',records,P)
    return records

def arch_points(y=0):
    seg=int(P['greenhouse_arch_segments']); span=P['greenhouse_span']; height=P['greenhouse_height']
    # Inset steel radius leaves the outside film envelope at exact 9 x 4.5 m.
    return [( -(span/2-.035)*math.cos(i*math.pi/seg),y,
              .035+(height-.07)*math.sin(i*math.pi/seg)) for i in range(seg+1)]

def continuous_tube(name,points,radius,mat,sides=8):
    vs=[];fs=[];uvs=[];count=len(points)
    arc=[0.0]
    for a,b in zip(points,points[1:]):arc.append(arc[-1]+(Vector(b)-Vector(a)).length)
    for i,p in enumerate(points):
        tangent=Vector(points[min(i+1,count-1)])-Vector(points[max(i-1,0)])
        tangent.normalize(); u=Vector((0,1,0)); v=tangent.cross(u).normalized()
        for j in range(sides):
            a=j*2*math.pi/sides;vs.append(tuple(Vector(p)+radius*(u*math.cos(a)+v*math.sin(a))))
    for i in range(count-1):
        for j in range(sides):
            jj=(j+1)%sides;fs.append((i*sides+j,i*sides+jj,(i+1)*sides+jj,(i+1)*sides+j))
            uvs.append([(j/sides,arc[i]),((j+1)/sides,arc[i]),((j+1)/sides,arc[i+1]),(j/sides,arc[i+1])])
    capuv=[(.5+.5*math.cos(j*2*math.pi/sides),.5+.5*math.sin(j*2*math.pi/sides)) for j in range(sides)]
    fs.append(tuple(reversed(range(sides))));uvs.append(list(reversed(capuv)))
    fs.append(tuple((count-1)*sides+j for j in range(sides)));uvs.append(capuv)
    return C.mesh(name,vs,fs,mat,uvs,smooth=True)

def greenhouse():
    C.reset();records=[]; assets={}
    steel=C.pbr('GreenhouseGalvanizedSteel',(.52,.56,.58),.31,.88,'steel',res=1024)
    film=C.pbr('GreenhouseFilm',(.82,.91,.88),.28,0,'film',res=1024,alpha=.20)
    hem=C.pbr('GreenhouseFilmSeam',(.61,.69,.66),.50,0,'film',res=1024,alpha=.62)
    span=P['greenhouse_span']; length=P['greenhouse_length']; height=P['greenhouse_height'];seg=int(P['greenhouse_arch_segments'])
    # Leading arch is inset by half its radius so full section bounds lie in
    # [0,length]; shared seams never repeat an arch at the same position.
    points=arch_points(.035)
    parts=[continuous_tube('LeadingOwnedSteelArch',points,.035,steel)]
    coll=[]
    for endpoint in (points[0],points[-1]):
        x,y,z=endpoint
        parts.append(C.box('SteelArchGroundFoot',(x,y,.0175),(.07,.07,.035),steel,.001))
        coll.append(C.box('SteelArchGroundFootCollision',(x,y,.0175),(.07,.07,.035)))
    for i in range(0,len(points)-1,2):
        coll.append(collision_beam('ArchCollision',points[i],points[min(i+2,len(points)-1)],.065))
    for a in (0,math.pi/4,math.pi/2,math.pi*3/4,math.pi):
        x=-(span/2-.08)*math.cos(a); z=.055+(height-.12)*math.sin(a)
        parts.append(wire('LongitudinalSteelPurlin',(x,0,z),(x,length,z),.0175,steel))
    # Elliptical formula remains valid if height differs from span/2.
    vs=[]; fs=[];uvs=[]
    for i in range(seg+1):
        a=math.pi*i/seg; x=-span/2*math.cos(a);z=height*math.sin(a)
        vs.extend([(x,0,z),(x,length,z)])
    for i in range(seg):
        fs.append((i*2,i*2+2,i*2+3,i*2+1));uvs.append([(i/seg*span,0),((i+1)/seg*span,0),((i+1)/seg*span,length),(i/seg*span,length)])
    parts.append(C.mesh('ArchedPolyethyleneFilm',vs,fs,film,uvs,smooth=True))
    name='SM_PazFarm_Greenhouse_Tunnel_9x4'
    assets['tunnel']=store(name,parts,coll,[
      '9 m outer film span x 4 m axial pitch x 4.5 m outer film height; source front is -Y.',
      'Ground pivot at centre of leading short end (0,0,0); local X spans -4.5..4.5, local Y spans 0..4.',
      'One steel arch on the leading edge only; tile at (0,j*4,0). Purlins and film end flush at exactly Y=0 and Y=4.',
      'Add End wall at Y=0 and Y=N*4; add one EndArch closure only at Y=N*4-0.07. No duplicate interior arches.',
      'Semi-transparent film: two sided translucent PBR; BaseColor alpha 0.20, roughness 0.28, IOR 1.46. FBX materials need native Unreal recreation.',
      'UCX boxes follow steel arch only. Film and walking volume have no collision. No opaque box across tunnel.'
    ],[span,length,height],records)
    dw=P['greenhouse_door_width']; dh=P['greenhouse_door_height'];hw=dw/2
    # Vertical strips fill a domed end while exactly excluding the doorway.
    xs=sorted(set([round(-span/2*math.cos(i*math.pi/seg),9) for i in range(seg+1)]+[-hw,hw]))
    parts=[];coll=[]
    for i,(a,b) in enumerate(zip(xs,xs[1:])):
        za=height*math.sqrt(max(0,1-(a/(span/2))**2)); zb=height*math.sqrt(max(0,1-(b/(span/2))**2))
        bottom=dh if a>=-hw-1e-8 and b<=hw+1e-8 else 0
        verts=[(a,0,bottom),(b,0,bottom),(b,0,zb),(a,0,za)]
        # At the two pointed spring-line tips use a triangle, avoiding a repeated
        # zero-height vertex and zero-area triangle in the exported mesh.
        if za-bottom<1e-8:
            parts.append(C.mesh('EndFilmTip',verts[:3],[(0,1,2)],film,[[((x+span/2)/span,z/height) for x,y,z in verts[:3]]]))
        elif zb-bottom<1e-8:
            vv=[verts[0],verts[1],verts[3]];parts.append(C.mesh('EndFilmTip',vv,[(0,1,2)],film,[[((x+span/2)/span,z/height) for x,y,z in vv]]))
        else:parts.append(C.mesh('EndFilmPanel',verts,[(0,1,2,3)],film,[[((x+span/2)/span,z/height) for x,y,z in verts]]))
    jamb=.055
    for x in (-hw-jamb/2,hw+jamb/2):
        parts.append(C.box('EndDoorJamb',(x,0,dh/2),(jamb,.07,dh),steel,.002))
        coll.append(C.box('EndDoorJambCollision',(x,0,dh/2),(jamb,.07,dh)))
    parts.append(C.box('EndDoorLintel',(0,0,dh+jamb/2),(dw+jamb*2,.07,jamb),steel,.002))
    coll.append(C.box('EndDoorLintelCollision',(0,0,dh+jamb/2),(dw+jamb*2,.07,jamb)))
    # Roll-up translucent door tied above the doorway; opening stays obvious.
    parts.append(wire('RolledFilmDoor',(-hw,-.08,dh+.095),(hw,-.08,dh+.095),.07,hem))
    for x in (-hw*.65,hw*.65):
        parts.append(C.box('DoorRollStrap',(x,-.08,dh+.095),(.045,.155,.155),steel,.005))
    name='SM_PazFarm_Greenhouse_End'
    assets['end']=store(name,parts,coll,[
      'Domed 9 m wide x 4.5 m tall film end wall with centred 1.8 m x 2.2 m door opening; rolled-up door film above opening.',
      'Pivot at ground centre; end wall in local XZ plane at Y=0. Can be rotated 180 degrees on far end for outside-facing rolled door.',
      'End wall deliberately excludes a perimeter arch, so it can attach to the existing leading arch without duplicate steel.',
      'Add exactly one Greenhouse_EndArch at trailing cap; see structures_assembly.md.',
      'Collision only on doorway steel jambs and lintel; no sill or invisible solid blocking the opening.'
    ],[span,.23,height],records)
    points=arch_points(.035)
    parts=[continuous_tube('TrailingClosureSteelArch',points,.035,steel)]
    coll=[collision_beam('ClosureArchCollision',points[i],points[min(i+2,len(points)-1)],.065) for i in range(0,len(points)-1,2)]
    for endpoint in (points[0],points[-1]):
        x,y,z=endpoint
        parts.append(C.box('ClosureArchGroundFoot',(x,y,.0175),(.07,.07,.035),steel,.001))
        coll.append(C.box('ClosureArchGroundFootCollision',(x,y,.0175),(.07,.07,.035)))
    name='SM_PazFarm_Greenhouse_EndArch'
    assets['arch']=store(name,parts,coll,[
      'Supplementary single terminal arch; same ground-centre origin and profile as the tunnel leading arch.',
      'For N sections, place at (0,N*4-0.07,0); its steel bounds finish at Y=N*4 without extending the module envelope.',
      'Not needed at the first end because first Tunnel already owns its leading arch.'
    ],[span,.07,height],records)
    if P['render_assembled']:
        copies=[]
        def dup(key,loc,rot=0):
            o=assets[key][0].copy();o.data=assets[key][0].data.copy();bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler.z=rot;o.hide_set(False);o.hide_render=False;copies.append(o)
        for j in range(3):dup('tunnel',(0,j*length,0))
        dup('end',(0,0,0));dup('end',(0,3*length,0),math.pi);dup('arch',(0,3*length-.07,0))
        ob=C.combine('PREVIEW_ONLY_Greenhouse_3Sections',copies)
        C.preview(ob,{'preview':'Previews/Greenhouse_Assembled_3Sections.png'},azimuth=-62,elevation=22)
        bpy.data.objects.remove(ob,do_unlink=True)
    finalize_family('Greenhouse.blend',records,P)
    return records

if __name__=='__main__':
    netrecords=net_house(); ghrecords=greenhouse()
    C.report('structures.json',ALL,{'parameters':P,'reference_assessment':'Screenshot gives plan context only. Handoff explicitly authorizes these defaults; no extra reference required. These are configurable original generic agricultural structures, not a claimed measured Paz Farm reconstruction.',
      'orientation':'Source front -Y, up Z. FBX exporter axis_forward=-Y axis_up=Z, apply_scale_options=FBX_SCALE_UNITS; Blender metres.',
      'assembly_guide':'Reports/structures_assembly.md',
      'assembled_previews':['Previews/NetHouse_Assembled_2x2_White.png','Previews/NetHouse_Assembled_2x2_Black.png','Previews/Greenhouse_Assembled_3Sections.png']})
    print('PAZ_STRUCTURES_COMPLETE',len(ALL),'assets',sum(r['triangles_LOD0'] for r in ALL),'triangles')
