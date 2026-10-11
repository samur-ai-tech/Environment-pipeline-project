"""Original olive family, opaque leaf volumes and authored matching lowest LODs."""
import sys, math, random, json, collections, struct, zlib, hashlib
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Vector
import paz_common as p
p.SOURCE['author']='Paz Farm original olive modelling, 2026-10-11'

CONFIG=[
 dict(variant='A',height=4.5,width=4.7,depth=4.35,trunk_radius=.27,lean=(.25,-.15),seed=9401),
 dict(variant='B',height=5.5,width=5.35,depth=4.90,trunk_radius=.33,lean=(-.32,.21),seed=9507),
 dict(variant='C',height=6.5,width=5.95,depth=5.55,trunk_radius=.39,lean=(.38,.17),seed=9683),
 dict(variant='Young',height=2.0,width=1.7,depth=1.6,trunk_radius=.065,lean=(.05,-.035),seed=9787),
]
LEAVES_PER_CLUMP=400
HULL_LINEAR_MULTIPLIER=.68
INNER_HULL_FACTOR=.46
LOW_HULL_FACTOR=1.035

class Batch:
 def __init__(self):self.v=[];self.f=[];self.uv=[];self.mi=[];self.parts=0
 def add(self,verts,faces,uvs=None,mi=None):
  start=len(self.v);self.v.extend(tuple(v) for v in verts)
  for i,face in enumerate(faces):
   self.f.append(tuple(start+k for k in face));self.uv.append(uvs[i] if uvs else [(verts[k][0],verts[k][2]) for k in face]);self.mi.append(mi[i] if mi else 0)
  self.parts+=1
 def tube(self,pts,radii,sides=8,gnarl=0,phase=0,flat_base=False):
  pts=list(map(Vector,pts));verts=[];previous_side=None
  for i,pt in enumerate(pts):
   tangent=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
   reference=previous_side if previous_side is not None else Vector((1,0,0));side=reference-tangent*reference.dot(tangent)
   if side.length<.01:side=Vector((0,1,0))-tangent*tangent.y
   side.normalize();previous_side=side.copy();other=tangent.cross(side).normalized()
   for j in range(sides):
    a=math.tau*j/sides+phase+i*.29;rr=radii[i]*(1+gnarl*math.sin(a*3+phase+i*.77)+gnarl*.35*math.cos(a*5-i*.61))
    pos=pt+rr*(side*math.cos(a)+other*math.sin(a))
    if flat_base and i==0:pos.z=0
    verts.append(pos)
  faces=[];uv=[]
  for i in range(len(pts)-1):
   for j in range(sides):
    faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j));uv.append([(j/sides,pts[i].z),((j+1)/sides,pts[i].z),((j+1)/sides,pts[i+1].z),(j/sides,pts[i+1].z)])
  faces.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))])
  for q in range(2):uv.append([(.5+.5*math.cos(math.tau*j/sides),.5+.5*math.sin(math.tau*j/sides)) for j in (reversed(range(sides)) if q==0 else range(sides))])
  self.add(verts,faces,uv)
 def hull(self,center,radii,phase,seg=12,rings=6,factor=1):
  c=Vector(center);rx,ry,rz=[r*factor for r in radii];verts=[c+Vector((0,0,rz))]
  for i in range(1,rings):
   t=math.pi*i/rings;st=math.sin(t);ct=math.cos(t)
   for j in range(seg):
    a=math.tau*j/seg;ripple=1+.15*math.sin(3*a+phase)*st+.055*math.sin(5*a+2*t+phase)
    verts.append(c+Vector((rx*st*math.cos(a)*ripple,ry*st*math.sin(a)*ripple,rz*ct*(1+.07*math.sin(3*a+phase)*st))))
  bottom=len(verts);verts.append(c-Vector((0,0,rz)));faces=[];uv=[]
  for j in range(seg):faces.append((0,1+j,1+(j+1)%seg));uv.append([((j+.5)/seg,1),(j/seg,1-1/rings),((j+1)/seg,1-1/rings)])
  for i in range(rings-2):
   for j in range(seg):
    a=1+i*seg+j;b=1+i*seg+(j+1)%seg;faces.append((a,a+seg,b+seg,b));uv.append([(j/seg,1-(i+1)/rings),(j/seg,1-(i+2)/rings),((j+1)/seg,1-(i+2)/rings),((j+1)/seg,1-(i+1)/rings)])
  for j in range(seg):faces.append((bottom,1+(rings-2)*seg+(j+1)%seg,1+(rings-2)*seg+j));uv.append([((j+.5)/seg,0),((j+1)/seg,1/rings),(j/seg,1/rings)])
  self.add(verts,faces,uv)
 def leaf(self,center,along,length,width,roll):
  c=Vector(center);along=Vector(along).normalized();side=Vector((0,0,1)).cross(along)
  if side.length<.01:side=Vector((1,0,0)).cross(along)
  side.normalize();up=along.cross(side).normalized();side=side*math.cos(roll)+up*math.sin(roll);up=along.cross(side).normalized()
  # Closed, gently bowed narrow lanceolate leaf. Pale underside is genuine
  # separate material geometry, not two-sided transmission or alpha shading.
  outline=[(0,0),(.25,-.40),(.65,-.50),(1,0),(.65,.50),(.25,.40)]
  verts=[c+along*((t-.5)*length)+side*(s*width)+up*(math.sin(t*math.pi)*length*.052) for t,s in outline]
  verts.extend([c+up*length*.082,c+up*length*.015]);faces=[];uv=[];mi=[]
  for i in range(6):
   j=(i+1)%6;faces.append((6,i,j));uv.append([(.5,.5),(outline[i][1]+.5,outline[i][0]),(outline[j][1]+.5,outline[j][0])]);mi.append(0)
  for i in range(6):
   j=(i+1)%6;faces.append((7,j,i));uv.append([(.5,.5),(outline[j][1]+.5,outline[j][0]),(outline[i][1]+.5,outline[i][0])]);mi.append(1)
  self.add(verts,faces,uv,mi)
 def obj(self,name,mats,smooth=True):
  if not isinstance(mats,list):mats=[mats]
  ob=p.mesh(name,self.v,self.f,mats[0],self.uv,smooth)
  for m in mats[1:]:ob.data.materials.append(m)
  for poly,mi in zip(ob.data.polygons,self.mi):poly.material_index=mi
  return ob

def png(path,rgba):
 data=np.asarray(np.clip(rgba,0,255),np.uint8);h,w=data.shape[:2]
 def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
 raw=b''.join(b'\0'+row.tobytes() for row in data)
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))

def calibrate_hull(mat):
 rng=np.random.default_rng(2348);n=1024;y,x=np.mgrid[0:n,0:n]/float(n-1)
 noise=rng.uniform(-.025,.025,(n,n));patch=.94+.06*np.sin(x*47+y*13)*np.cos(y*33)+noise
 color=np.ones((n,n,4),np.float32)*255
 for ch,base in enumerate((.285,.320,.262)):color[:,:,ch]=base*patch*255
 srgb=np.clip(color[:,:,:3]/255,0,1);linear=np.where(srgb<=.04045,srgb/12.92,((srgb+.055)/1.055)**2.4)*HULL_LINEAR_MULTIPLIER
 color[:,:,:3]=np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)*255
 im=next(nd.image for nd in mat.node_tree.nodes if nd.type=='TEX_IMAGE' and '_BaseColor' in nd.image.name);png(Path(im.filepath),color)

def materials():
 bark=p.pbr('Olive_Bark',(.285,.265,.231),.96,kind='bark',res=1024,seed=61)
 top=p.pbr('Olive_LeafTop',(.29,.335,.273),.90,kind='noise',res=1024,seed=172)
 under=p.pbr('Olive_LeafUnderside',(.405,.425,.363),.94,kind='noise',res=1024,seed=282)
 hull=p.pbr('Olive_CrownHull',(.285,.32,.262),.96,kind='noise',res=1024,seed=516);calibrate_hull(hull)
 mats=[bark,top,under,hull]
 for i,mat in enumerate(mats):
  bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.07;bs.inputs['Alpha'].default_value=1;bs.inputs['Subsurface Weight'].default_value=0
  mat.use_backface_culling=False;mat['blend_mode_intent']='OPAQUE' if i==0 else 'OPAQUE_TWO_SIDED';mat['opacity_contract']='Alpha1; actual closed leaf geometry or closed opaque crown volume, no masks.'
  for nd in mat.node_tree.nodes:
   if nd.type=='TEX_IMAGE':nd.image.reload()
 return mats

def layout(cfg):
 rng=random.Random(cfg['seed']);H=cfg['height'];W=cfg['width'];D=cfg['depth'];lx,ly=cfg['lean'];young=cfg['variant']=='Young'
 base=[Vector((0,0,0)),Vector((-.018*W,.017*W,H*.07)),Vector((.012*W,-.020*W,H*.15)),Vector((lx*.65,ly*.65,H*.24))]
 stems=[]
 for q in range(2):
  sign=-1 if q==0 else 1;start=base[2];pts=[]
  for i,t in enumerate((0,.2,.4,.6,.8,1)):
   a=t*math.pi*1.05+q*math.pi
   pts.append(start+Vector((lx*t+math.cos(a)*W*.065*t,ly*t+sign*W*.032*t+math.sin(a)*W*.045*t,H*(.46+.045*q)*t)))
  stems.append(pts)
 branches=[];clumps=[]
 for j in range(6):
  a=j*math.tau/6+rng.uniform(-.22,.22);r=W*rng.uniform(.20,.29);z=H*rng.uniform(.51,.65)
  start=stems[j%2][3 if j%3 else 2];tip=Vector((lx+math.cos(a)*r,ly+math.sin(a)*r*D/W,z));elbow=start.lerp(tip,.52)+Vector((0,0,-H*.045));branches.append([start,elbow,tip])
  for k in range(3):
   angle=a+(-.26,.18,.06)[k]+rng.uniform(-.08,.08);radial=(.065,.14,-.065)[k]*W
   center=tip+Vector((math.cos(angle)*radial,math.sin(angle)*radial*D/W,H*((-.035,.075,.195)[k]+rng.uniform(-.022,.023))))
   radii=(W*rng.uniform(.105,.137),D*rng.uniform(.10,.14),H*rng.uniform(.091,.13))
   clumps.append(dict(center=center,radii=radii,phase=rng.uniform(0,math.tau),parent=tip))
 return base,stems,branches,clumps

def fix_material_slots(ob,mats):
 old=list(ob.data.materials);indices=[mats.index(old[poly.material_index]) for poly in ob.data.polygons]
 ob.data.materials.clear()
 for mat in mats:ob.data.materials.append(mat)
 for poly,idx in zip(ob.data.polygons,indices):poly.material_index=idx

def make(cfg,mats,lod):
 high=lod==0;rng=random.Random(cfg['seed']+113);H=cfg['height'];W=cfg['width'];tr=cfg['trunk_radius'];young=cfg['variant']=='Young'
 bark=Batch();hull=Batch();leaf=Batch();base,stems,branches,clumps=layout(cfg)
 bark.tube(base,[tr*1.30,tr*1.07,tr*.88,tr*.58],12 if high else 7,.20 if not young else .09,flat_base=True)
 for q,pts in enumerate(stems):bark.tube(pts,[tr*.63,tr*.58,tr*.48,tr*.35,tr*.24,tr*.10],10 if high else 6,.23 if not young else .09,phase=q*1.24)
 for start,elbow,tip in branches:
  if high:bark.tube([start,start.lerp(elbow,.55)+Vector((W*.012,0,-H*.025)),elbow,tip],[tr*.34,tr*.27,tr*.21,tr*.08],8,.12)
  else:bark.tube([start,elbow,tip],[tr*.34,tr*.21,tr*.08],5,.10)
 for cl in clumps:
  c=cl['center'];rx,ry,rz=cl['radii'];phase=cl['phase'];bark.tube([cl['parent'],c],[tr*.10,tr*.028],6 if high else 4,.04)
  hull.hull(c,cl['radii'],phase,12 if high else 8,6 if high else 4,INNER_HULL_FACTOR if high else LOW_HULL_FACTOR)
  if high:
   for q in range(LEAVES_PER_CLUMP):
    z=rng.uniform(-1,1);a=rng.uniform(0,math.tau);s=math.sqrt(1-z*z);ripple=1+.15*math.sin(3*a+phase)*s+.055*math.sin(5*a+2*math.acos(z)+phase)
    center=c+Vector((rx*s*math.cos(a)*ripple,ry*s*math.sin(a)*ripple,rz*z))*.72
    theta=a+rng.uniform(-1.15,1.15);direction=Vector((math.cos(theta),math.sin(theta),rng.uniform(-.6,.65)))
    length=rng.uniform(.18,.275)*(W/4.7)**.50;width=length*rng.uniform(.27,.33)*max(1,(W/4.7)**.50)
    leaf.leaf(center,direction,length,width,rng.uniform(-1.65,1.65))
    if q%25==0:bark.tube([c.lerp(center,.60),center],[.004*(W/4.7)**.5,.0017],5)
 name='SM_PazFarm_Olive_'+cfg['variant']+('' if high else '_LOD3');parts=[bark.obj(name+'_Bark',mats[0]),hull.obj(name+'_Hull',mats[3])]
 if high:parts.append(leaf.obj(name+'_Leaves',[mats[1],mats[2]],False))
 ob=p.combine(name,parts);fix_material_slots(ob,mats);bpy.context.view_layer.update();bb=p.bounds(ob)
 factors=(cfg['width']/(bb[1][0]-bb[0][0]),cfg['depth']/(bb[1][1]-bb[0][1]),H/(bb[1][2]-bb[0][2]))
 for v in ob.data.vertices:v.co.x*=factors[0];v.co.y*=factors[1];v.co.z=(v.co.z-bb[0][2])*factors[2]
 ob.data.update();bpy.context.view_layer.update()
 notes=['Original grey-green olive with curved narrow lanceolate leaves, pale undersides, twisted split trunk and irregular open crown.',
 '18 recessed opaque closed crown clumps and 7,200 closed leaf volumes.' if high else 'Authored lowest LOD from the corresponding 18 closed crown clumps, split trunk and support branches; no billboard/cards. Crown negative spaces retained.',
 'Material slot names/order identical in high and low mesh, including unused leaf slots in LOD3. All foliage alpha1, opaque two-sided; no wind or collision.',
 'Trunk-base ground origin; metres; -Y FBX forward, Z up. Native integration and distant appearance remain for the operator.']
 ob,rec=p.asset(name,[ob],budget=100000 if high else 1500,nominal=[cfg['width'],cfg['depth'],H],notes=notes)
 rec.update(lod_index=lod,family='Olive',variant=cfg['variant'],triangle_budget_min=40000 if high else 800,paired_asset='SM_PazFarm_Olive_'+cfg['variant']+('_LOD3' if high else ''),material_slot_order=[m.name for m in mats])
 counts=collections.Counter()
 for poly in ob.data.polygons:
  ids=list(poly.vertices)
  for i,v in enumerate(ids):counts[tuple(sorted((v,ids[(i+1)%len(ids)])))]+=1
 rec['qa'].update(nonmanifold_edges=sum(n!=2 for n in counts.values()),closed_components=all(n==2 for n in counts.values()),finite_geometry=all(math.isfinite(x) for v in ob.data.vertices for x in v.co),finite_uv0=all(math.isfinite(x) for uv in ob.data.uv_layers[0].data for x in uv.uv))
 rec['construction']={'closed_crown_clumps':18,'closed_leaf_volumes':18*LEAVES_PER_CLUMP if high else 0,'leaf_shape':'narrow bowed lanceolate, grey-green upper and pale underside faces','billboard':False,'alpha':1.0,'inner_hull_factor':INNER_HULL_FACTOR,'low_hull_factor':LOW_HULL_FACTOR}
 if rec['triangles_LOD0']<rec['triangle_budget_min'] or not rec['qa']['closed_components'] or not rec['qa']['finite_geometry'] or not rec['qa']['finite_uv0']:raise RuntimeError('Olive QA failed: '+name)
 ob['species']='Olea europaea';ob['lod_index']=lod;ob['variant']=cfg['variant'];ob['lod_pair']=rec['paired_asset'];ob['parameters']=json.dumps(cfg)
 p.preview(ob,rec,azimuth=-62,elevation=15)
 return ob,rec

def main():
 p.reset();mats=materials();records=[];objects=[]
 selected=CONFIG[:1] if '--first-hero' in sys.argv else CONFIG
 for cfg in selected:
  for lod in (0,3):
   ob,rec=make(cfg,mats,lod);objects.append(ob);records.append(rec);p.report('olives_progress.json',records)
 for ob in objects:ob.hide_set(ob!=objects[0]);ob.hide_render=ob!=objects[0]
 params={'variants':CONFIG,'leaves_per_clump':LEAVES_PER_CLUMP,'inner_hull_factor':INNER_HULL_FACTOR,'low_hull_factor':LOW_HULL_FACTOR,'hull_linear_multiplier':HULL_LINEAR_MULTIPLIER,'material_slot_order':[m.name for m in mats]}
 p.save_family('Olive.blend',records,params)
 p.report('olives_v004.json',records,{'parameters':params,'lod_pairing':{r['name']:r['paired_asset'] for r in records if r['lod_index']==0},'source_licence':'CC0-1.0 original procedural geometry and textures. No external image content.','native_verified':False,'construction':'18 irregular rounded closed clumps per variant; hollow gaps between clumps and split trunk survive in LOD3. 7200 closed narrow lanceolate leaf volumes at LOD0.','materials':'Bark, grey-green LeafTop, pale LeafUnderside, and calibrated CrownHull; fixed same slot order on both LODs. Foliage opaque/two-sided, alpha1. All images 1K with BaseColor sRGB; Normal OpenGL +Y and ORM Non-Color.','lowest_lod':'Closed reduced-ring hulls at original clump centers plus gnarled/split trunk and supporting limbs, never a billboard. Hull diffuse calibrated in linear space; independent fixed-camera tests supplied by root.'})

def source_qa():
 source=p.ROOT/'Blend'/'Olive.blend';bpy.ops.wm.open_mainfile(filepath=str(source))
 records=json.loads((p.ROOT/'Reports'/'olives_v004.json').read_text())['assets'];checks=[];failures=[]
 for rec in records:
  ob=bpy.data.objects.get(rec['name']);ob.data.calc_loop_triangles();bb=p.bounds(ob);edge_counts=collections.Counter()
  for poly in ob.data.polygons:
   ids=list(poly.vertices)
   for i,v in enumerate(ids):edge_counts[tuple(sorted((v,ids[(i+1)%len(ids)])))]+=1
  result={'name':rec['name'],'triangles':len(ob.data.loop_triangles),'zero_area_triangles':sum(t.area<1e-12 for t in ob.data.loop_triangles),'closed_components':all(n==2 for n in edge_counts.values()),'uv0':bool(ob.data.uv_layers) and ob.data.uv_layers[0].name=='UV0','finite_geometry':all(math.isfinite(x) for v in ob.data.vertices for x in v.co),'finite_uv':all(math.isfinite(x) for uv in ob.data.uv_layers[0].data for x in uv.uv),'material_slots':[m.name for m in ob.data.materials],'location':list(ob.location),'rotation':list(ob.rotation_euler),'scale':list(ob.scale),'dimensions':[bb[1][i]-bb[0][i] for i in range(3)],'ground_min_z':bb[0][2]}
  result['passed']=all((result['triangles']==rec['triangles_LOD0'],result['zero_area_triangles']==0,result['closed_components'],result['uv0'],result['finite_geometry'],result['finite_uv'],result['material_slots']==rec['material_slot_order'],max(abs(x) for x in result['location'])<1e-7,max(abs(x) for x in result['rotation'])<1e-7,max(abs(x-1) for x in result['scale'])<1e-7,abs(result['ground_min_z'])<1e-7,max(abs(result['dimensions'][i]-rec['nominal_size_metres'][i]) for i in range(3))<1e-4))
  checks.append(result)
  if not result['passed']:failures.append(rec['name'])
 textures=[]
 for im in bpy.data.images:
  if im.source!='FILE':continue
  path=Path(bpy.path.abspath(im.filepath));buf=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(buf);rgba=buf.reshape((-1,4));texture={'file':path.name,'exists':path.is_file(),'size':list(im.size),'colorspace':im.colorspace_settings.name,'alpha_min':float(rgba[:,3].min()),'alpha_max':float(rgba[:,3].max()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  expected='sRGB' if '_BaseColor' in path.name else 'Non-Color';texture['passed']=texture['exists'] and texture['size']==[1024,1024] and texture['alpha_min']==1.0 and texture['alpha_max']==1.0 and texture['colorspace']==expected;textures.append(texture)
  if not texture['passed']:failures.append(path.name)
 result={'passed':not failures and len(checks)==8 and len(textures)==12,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'assets':checks,'textures':textures,'failures':failures,'scope':'Fresh Blender source-file readback only; parent supplies independent fresh FBX imports.'}
 (p.ROOT/'Reports'/'olives_source_readback.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps({'passed':result['passed'],'assets':len(checks),'textures':len(textures),'failures':failures}))
 if not result['passed']:raise RuntimeError('Olive source readback failed')

if __name__=='__main__':
 if '--source-qa' in sys.argv:source_qa()
 else:main()
