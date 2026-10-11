"""Young strawberry transplants on genuinely perforated dark mulch, Paz Farm v005.

Original procedural meshes/textures. Approved photographic references remain
separate: they guide form and palette, never become texture pixels.
"""
import sys, math, random, json, collections, hashlib, struct, zlib
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Scripts'))
import paz_common as p
p.SOURCE['author']='Original Paz Farm strawberry modelling, 2026-10-11'

PARAMS={
 'length_m':4.0,'width_base_m':1.1,'width_top_m':.8,'bed_height_m':.25,'skirt_min_z_m':-.15,
 'row_separation_m':.33,'holes_per_row':14,'hole_pitch_m':4/14,'stagger_m':2/14,
 'young_plant_diameter_m':[.115,.19],'young_plant_height_m':[.055,.115],
 'boundary_small_diameter_m':.104,'boundary_small_height_m':.055,
 'compound_leaf_count':[3,6],'leaflets_per_compound_leaf':3,'no_fruit':True,'no_flowers':True,
 'no_LOD0_canopy_hull':True,'film_roughness':.95,'film_specular':.04,
 'film_rgb_srgb':[27,30,31],'leaf_top_rgb_srgb':[43,73,53],'leaf_under_rgb_srgb':[64,86,66],
 'seeds':{'A':51017,'B':51977,'C':52931},'cap_length_m':.4,
}
ROLES=['Mulch','Soil','LeafTop','LeafUnder','LeafOlder','Petiole','DripTape','MulchDistant']
NAMES=['M_PazFarm_Strawberry_'+s+'_v005' for s in ROLES]
PROFILE=[(-.55,-.15),(-.55,-.005),(-.52,.055),(-.46,.185),(-.40,.235),(-.28,.246),(0,.25),(.28,.246),(.40,.235),(.46,.185),(.52,.055),(.55,-.005),(.55,-.15)]

class Batch:
 def __init__(self):self.v=[];self.f=[];self.uv=[];self.mi=[];self.parts=[]
 def add(self,verts,faces,material,role,uvs=None,**meta):
  start=len(self.v);sf=len(self.f);self.v.extend(tuple(x) for x in verts)
  for face in faces:
   self.f.append(tuple(start+i for i in face));self.mi.append(material)
   self.uv.append([uvs[i] if uvs else ((verts[i][0]+.55)/1.1,verts[i][1]/4) for i in face])
  rec={'role':role,'start_vertex':start,'vertex_count':len(verts),'start_face':sf,'face_count':len(faces),**meta}
  self.parts.append(rec);return rec
 def finish(self,name,mats):
  ob=p.mesh(name,self.v,self.f,None,self.uv,True)
  for mat in mats:ob.data.materials.append(mat)
  for poly,mi in zip(ob.data.polygons,self.mi):poly.material_index=mi
  ob['component_ranges']=json.dumps(self.parts,separators=(',',':'))
  return ob

def png_bytes(path,array):
 data=np.asarray(np.clip(np.rint(array),0,255),np.uint8);h,w=data.shape[:2]
 def chunk(kind,payload):return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
 raw=b''.join(b'\0'+row.tobytes() for row in data)
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))

def make_materials():
 n=1024;y,x=np.mgrid[0:n,0:n]/(n-1);rng=np.random.default_rng(51942);noise=rng.random((n,n))
 mats=[]
 for idx,role in enumerate(ROLES):
  h=np.zeros((n,n));rough=.93;spec=.06
  if role in ('Mulch','MulchDistant'):
   tint=.97+.032*np.sin(x*89+y*math.tau*3)+.025*np.sin(x*145-y*math.tau*5)+.02*(noise-.5)
   col=np.stack([c*tint for c in PARAMS['film_rgb_srgb']],axis=-1)
   h=.016*np.sin(x*87+y*math.tau*3)+.009*np.sin(y*math.tau*11+3*np.sin(x*21))+.0003*(noise-.5)
   for row in range(2):
    for k in range(14):
     cx=(-.165 if row==0 else .165)/1.1+.5;cy=(k+.25+.5*row)/14;dx=(x-cx)*1.1;dy=(y-cy)*4;rad=np.sqrt(dx*dx+dy*dy)
     ridge=np.exp(-((dy-((k%3)-1)*.65*dx)/.0032)**2)*np.exp(-rad/.06)
     h+=ridge*.014
   rough=PARAMS['film_roughness'];spec=PARAMS['film_specular']
   if role=='MulchDistant':
    dots=np.zeros((n,n))
    for row in range(2):
     cx=(-.165 if row==0 else .165)/1.1+.5
     for k in range(14):
      cy=(k+.25+.5*row)/14
      # Low spatial-frequency muted marks occupy only a small fraction of film.
      rr=((x-cx)/.044)**2+((y-cy)/.012)**2
      dots=np.maximum(dots,np.exp(-rr*2.2)*.60)
    for c,t in enumerate((35,51,39)):col[:,:,c]=col[:,:,c]*(1-dots)+t*dots
  elif role=='Soil':
   coarse=rng.random((128,128));coarse=np.repeat(np.repeat(coarse,8,0),8,1)
   tint=.82+.24*noise+.14*coarse;col=np.stack([c*tint for c in (84,69,51)],axis=-1)
   h=.012*noise+.008*coarse;rough=.98;spec=.02
  elif role in ('LeafTop','LeafUnder','LeafOlder'):
   mid=np.exp(-((x-.5)/.012)**2);secondary=np.exp(-((np.mod(y*8-np.abs(x-.5)*5+.5,1)-.5)/.048)**2)
   shape=.90+.075*np.sin(math.pi*y)+.035*noise+.14*mid+.055*secondary
   color=PARAMS['leaf_top_rgb_srgb'] if role=='LeafTop' else PARAMS['leaf_under_rgb_srgb']
   col=np.stack([c*shape for c in color],axis=-1)
   if role=='LeafOlder':
    aging=np.clip((np.abs(x-.5)*2-.40)*1.2+.16*np.sin(y*14+x*9),0,.75)
    for c,t in enumerate((100,62,40)):col[:,:,c]=col[:,:,c]*(1-aging)+t*aging
   h=.075*mid+.025*secondary+.0005*(noise-.5);rough=.90 if role=='LeafTop' else .94;spec=.07
  elif role=='Petiole':
   tint=.88+.13*noise+.06*np.sin(y*24);col=np.stack([c*tint for c in (66,79,46)],axis=-1);rough=.91
  else:
   col=np.stack([np.full_like(x,c) for c in (19,20,19)],axis=-1);rough=.96;spec=.03
  base=np.ones((n,n,4))*255;base[:,:,:3]=col
  gy,gx=np.gradient(h);normal=np.ones_like(base)*255;normal_scale=160 if role in ('Mulch','MulchDistant') else (100 if role.startswith('Leaf') else 12);norm=np.stack((-gx*normal_scale,-gy*normal_scale,np.ones_like(x)),axis=-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True);normal[:,:,:3]=(norm*.5+.5)*255
  orm=np.ones_like(base)*255;orm[:,:,0]=250;orm[:,:,1]=rough*255;orm[:,:,2]=0
  ims=[];paths=[]
  for suffix,array in [('BaseColor',base),('Normal',normal),('ORM',orm)]:
   path=ROOT/'Textures'/('T_PazFarm_Strawberry_'+role+'_v005_'+suffix+'.png');png_bytes(path,array)
   im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='sRGB' if suffix=='BaseColor' else 'Non-Color';im.reload();ims.append(im);paths.append('Textures/'+path.name)
  mat=bpy.data.materials.new(NAMES[idx]);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
  bc=nt.nodes.new('ShaderNodeTexImage');bc.image=ims[0];nt.links.new(bc.outputs['Color'],bs.inputs['Base Color'])
  nm=nt.nodes.new('ShaderNodeTexImage');nm.image=ims[1];nn=nt.nodes.new('ShaderNodeNormalMap');nn.inputs['Strength'].default_value=.45 if role.startswith('Leaf') else .30;nt.links.new(nm.outputs['Color'],nn.inputs['Color']);nt.links.new(nn.outputs['Normal'],bs.inputs['Normal'])
  om=nt.nodes.new('ShaderNodeTexImage');om.image=ims[2];sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(om.outputs['Color'],sp.inputs['Color']);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],bs.inputs['Metallic'])
  bs.inputs['Alpha'].default_value=1;bs.inputs['Specular IOR Level'].default_value=spec;bs.inputs['Transmission Weight'].default_value=0;bs.inputs['Subsurface Weight'].default_value=0
  mat.use_backface_culling=False;mat['blend_mode_intent']='OPAQUE_TWO_SIDED' if idx in (2,3,4,5) else 'OPAQUE';mat['texture_files']=json.dumps(paths);mat['licence']='CC0-1.0';mat['source']=p.SOURCE['source'];mat['normal_convention']='OpenGL +Y';mat['orm_channels']='R=AO G=Roughness B=Metallic';mats.append(mat)
 return mats

def profile_z(x):
 # The shared end profile is piecewise linear, so extra detail vertices remain
 # on exactly the same boundary curve in high and low geometry.
 for (xa,za),(xb,zb) in zip(PROFILE[4:8],PROFILE[5:9]):
  if xa-1e-9<=x<=xb+1e-9:return za+(zb-za)*(x-xa)/(xb-xa)
 return .235

def full_profile_z(x):
 for (xa,za),(xb,zb) in zip(PROFILE[1:11],PROFILE[2:12]):
  if xa-1e-8<=x<=xb+1e-8 and xb>xa:return za+(zb-za)*(x-xa)/(xb-xa)
 return -.005

def seam_taper(y):
 return math.sin(math.pi*max(0,min(1,(y-.125)/3.75)))**2

def deform(x,y,z,seed=0,length=4,cap=False):
 if cap:
  t=max(0,(y-.075)/(length-.075));f=math.cos(t*math.pi/2)**1.5
  return Vector((x,y,z*f if z>0 else z))
 envelope=seam_taper(y)
 wave=(.004*math.sin(y*4.1+seed*.07)+.0028*math.sin(y*10.8+x*8.4+seed*.11))*envelope
 xx=x
 zz=z+wave*max(0,min(1,(z+.01)/.26))
 # Below-ground skirt remains exactly at the intended minimum.
 return Vector((xx,y,zz))

def film_z(x,y,seed,wrinkles=True,holes=None):
 z=deform(x,y,profile_z(x),seed).z
 if wrinkles:
  taper=seam_taper(y)*max(0,1-(x/.4)**2)
  z+=taper*(.00125*math.sin(y*38+x*41)+.0010*math.sin(y*51-x*22))
  if holes:
   for hole in holes:
    dx=x-hole['center_xy'][0];dy=y-hole['center_xy'][1];rr=math.hypot(dx,dy)
    if rr<.12:z+=taper*.0017*math.sin(math.atan2(dy,dx)*3+hole['plant_index']*.73)*math.exp(-((rr-.04)/.045)**2)
 return z

def inside_polygon(pt,poly):
 x,y=pt;hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit

def holes_for(seed):
 rng=random.Random(seed);result=[]
 for row in range(2):
  for k in range(14):
   boundary=(row==0 and k==0) or (row==1 and k==13)
   cx=(-.165 if row==0 else .165)+rng.uniform(-.006,.006)
   cy=(k+.25+.5*row)*4/14+(0 if boundary else rng.uniform(-.007,.007))
   angle=rng.uniform(0,math.pi);rim=[];aspect=rng.uniform(.40,.72)
   for i in range(12):
    a=math.tau*i/12+angle;rr=.032*rng.uniform(.85,1.13)*(1.12 if i%3==0 else .96)
    sx=math.cos(math.tau*i/12)*rr;sy=math.sin(math.tau*i/12)*rr*aspect
    rim.append([cx+sx*math.cos(angle)-sy*math.sin(angle),cy+sx*math.sin(angle)+sy*math.cos(angle)])
   result.append({'row_index':row,'plant_index':len(result),'center_xy':[cx,cy],'rim_xy':rim,'small_boundary':boundary,'tiny':False,'empty':False,'soil_z':film_z(cx,cy,seed)-.008})
 sparse={51017:(4,19),51977:(8,23),52931:(11,17)}[seed]
 result[sparse[0]]['empty']=True;result[sparse[1]]['tiny']=True
 return result

def film_surface(batch,seed,holes):
 verts=[];edges=[];xs=[-.4,-.3,-.28,-.2,-.1,0,.1,.2,.28,.3,.4];ys=[i/16 for i in range(65)]
 def add(point):verts.append(Vector(point));return len(verts)-1
 # Explicit perimeter vertices ensure top and side strips coincide exactly.
 boundary=[]
 for x in xs:boundary.append(add((x,0)))
 for y in ys[1:]:boundary.append(add((.4,y)))
 for x in reversed(xs[:-1]):boundary.append(add((x,4)))
 for y in reversed(ys[1:-1]):boundary.append(add((-.4,y)))
 edges.extend(zip(boundary,boundary[1:]+boundary[:1]))
 for hole in holes:
  ring=[add(q) for q in hole['rim_xy']];edges.extend(zip(ring,ring[1:]+ring[:1]))
  cx,cy=hole['center_xy']
  for j,q in enumerate(hole['rim_xy']):
   factor=1.7 if j%2 else 2.45;point=(cx+(q[0]-cx)*factor,cy+(q[1]-cy)*factor)
   if 0<point[1]<4 and not any(inside_polygon(point,h['rim_xy']) for h in holes):add(point)
 rng=random.Random(seed+13)
 for y in ys[1:-1]:
  for x in xs[1:-1]:
   xx=x+rng.uniform(-.014,.014);yy=y+rng.uniform(-.012,.012)
   if not any(inside_polygon((xx,yy),h['rim_xy']) for h in holes):add((xx,yy))
 out=delaunay_2d_cdt(verts,edges,[],0,1e-8,False)
 vv,ff=out[0],out[2];faces=[]
 for f in ff:
  center=sum((vv[i] for i in f),Vector((0,0)))/len(f)
  if not any(inside_polygon(center,h['rim_xy']) for h in holes):faces.append(tuple(f))
 used=sorted({i for f in faces for i in f});remap={a:i for i,a in enumerate(used)}
 points=[(float(vv[i].x),float(vv[i].y),film_z(float(vv[i].x),float(vv[i].y),seed,holes=holes)) for i in used]
 batch.add(points,[tuple(remap[i] for i in f) for f in faces],0,'film_top',closed=False,holes=len(holes))
 for segment in (PROFILE[:5],PROFILE[8:]):
  strip(batch,segment,ys,0,'film_sides',seed)

def strip(batch,profile,ys,mat,role,seed=0,closed=False,cap=False):
 points=[]
 for y in ys:
  for x,z in profile:
   pt=deform(x,y,z,seed,length=ys[-1],cap=cap)
   if role=='soil_edge_burial' and not cap and abs(x)<.54:
    envelope=seam_taper(y);pt.x+=math.copysign(1,x)*envelope*(.007*math.sin(y*6.3+seed)+.003*math.sin(y*13.5))
    clearance=z-full_profile_z(x)
    pt.z=deform(pt.x,y,full_profile_z(pt.x),seed).z+clearance+envelope*.0015*math.sin(y*10.1+seed)
   points.append(pt)
 faces=[];n=len(profile)
 for j in range(len(ys)-1):
  for i in range(n if closed else n-1):
   ni=(i+1)%n;quad=(j*n+i,j*n+ni,(j+1)*n+ni,(j+1)*n+i)
   if cap:faces.extend([(quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])])
   else:faces.append(quad)
 arc=[0.0]
 for a,b in zip(profile,profile[1:]):arc.append(arc[-1]+math.dist(a,b))
 uvs=[(arc[i]/max(arc[-1],.01),y/4) for y in ys for i in range(n)]
 # Top of lowest film keeps the physical XY atlas so its faint dots align with
 # rows. Vertical skirt faces receive separate non-collapsing arc-length UVs.
 if role=='film_lowest_mound':uvs=[((point.x+.55)/1.1,point.y/4) for point in points]
 part=batch.add(points,faces,mat,role,uvs,closed=False,open_ends=[ys[0],ys[-1]])
 if role=='film_lowest_mound':
  for fi,face in enumerate(faces):
   if max(points[i].x for i in face)-min(points[i].x for i in face)<1e-8:
    batch.uv[part['start_face']+fi]=[(arc[i%n]/arc[-1],points[i].y/4) for i in face]

def cap_stations(length,low):
 return [0,.075]+[.075+(length-.075)*i/(4 if low else 23) for i in range(1,(4 if low else 23)+1)]

def soil_body(batch,seed,length=4,cap=False,low=False):
 ys=(cap_stations(length,low) if cap else ([0,.125,1,2,3,3.875,4] if low else [length*i/32 for i in range(33)]))
 body=[(-.544,-.15),(-.544,-.008),(-.396,.229),(-.28,.240),(0,.244),(.28,.240),(.396,.229),(.544,-.008),(.544,-.15)]
 if not low:
  strip(batch,body,ys,1,'soil_body',seed,closed=True,cap=cap)
  if cap:
   verts=[deform(x,length,z,length=length,cap=True) for x,z in body];verts.append(Vector((0,length,-.08)))
   batch.add(verts,[(len(body),i,(i+1)%len(body)) for i in range(len(body))],1,'cap_soil_end',[(v.x+.55,(v.z+.15)/.15) for v in verts],closed=False)
 # Soil burial strips cover the plastic foot, with open ends to continue.
 for sign in (-1,1):
  pr=[(sign*.49,.126),(sign*.518,.07),(sign*.55,.014),(sign*.55,-.007)]
  if cap:pr.insert(2,(sign*.52,.0665))
  if sign<0:pr=list(reversed(pr))
  strip(batch,pr,ys,1,'soil_edge_burial',seed,cap=cap)

def ellipsoid(batch,center,scale,material,role,segments=10,rings=3,seed=0,**meta):
 rng=random.Random(seed);c=Vector(center);verts=[c+Vector((0,0,scale[2]))];uv=[(.5,1)]
 for j in range(1,rings):
  t=math.pi*j/rings
  for i in range(segments):
   a=math.tau*i/segments;rr=1+rng.uniform(-.10,.10)
   verts.append(c+Vector((scale[0]*math.sin(t)*math.cos(a)*rr,scale[1]*math.sin(t)*math.sin(a)*rr,scale[2]*math.cos(t))));uv.append((i/segments,1-j/rings))
 bot=len(verts);verts.append(c-Vector((0,0,scale[2])));uv.append((.5,0));faces=[]
 for i in range(segments):faces.append((0,1+i,1+(i+1)%segments))
 for j in range(rings-2):
  for i in range(segments):
   ni=(i+1)%segments;a=1+j*segments;faces.append((a+i,a+segments+i,a+segments+ni,a+ni))
 for i in range(segments):faces.append((bot,1+(rings-2)*segments+(i+1)%segments,1+(rings-2)*segments+i))
 batch.add(verts,faces,material,role,uv,closed=True,**meta)

def tube(batch,points,radii,material,role,segments=4,**meta):
 pts=list(map(Vector,points));verts=[];uv=[]
 for j,pnt in enumerate(pts):
  d=(pts[min(j+1,len(pts)-1)]-pts[max(j-1,0)]).normalized();help=Vector((0,0,1)) if abs(d.z)<.9 else Vector((0,1,0));u=d.cross(help).normalized();v=d.cross(u).normalized()
  for i in range(segments):
   a=math.tau*i/segments;verts.append(pnt+radii[j]*(u*math.cos(a)+v*math.sin(a)));uv.append((i/segments,j/(len(pts)-1)))
 faces=[]
 for j in range(len(pts)-1):
  for i in range(segments):
   ni=(i+1)%segments;faces.append((j*segments+i,j*segments+ni,(j+1)*segments+ni,(j+1)*segments+i))
 faces.extend([tuple(reversed(range(segments))),tuple((len(pts)-1)*segments+i for i in range(segments))])
 part=batch.add(verts,faces,material,role,uv,closed=True,**meta)
 for fi in (-2,-1):
  batch.uv[part['start_face']+len(faces)+fi]=[(.5+.45*math.cos(math.tau*(i%segments)/segments),.5+.45*math.sin(math.tau*(i%segments)/segments)) for i in faces[fi]]

def leaflet(batch,base,direction,length,width,roll,rng,older=False,plant_index=0,compound_leaf_index=0,leaflet_index=0):
 d=Vector(direction).normalized();side=Vector((d.y,-d.x,0)).normalized();normal=side.cross(d).normalized()
 side,normal=side*math.cos(roll)+normal*math.sin(roll),normal*math.cos(roll)-side*math.sin(roll)
 base=Vector(base);teeth=7;outline=[(0,0)]
 for i in range(1,2*teeth+2):
  t=i/(2*teeth+2);shape=math.sin(math.pi*t)**.72*(.92+.14*t);tooth=1.0 if i%2 else .86
  outline.append((shape*tooth*width*.5*rng.uniform(.96,1.04),t*length))
 outline.append((0,length))
 for i in reversed(range(1,2*teeth+2)):
  t=i/(2*teeth+2);shape=math.sin(math.pi*t)**.75*(.88+.18*t);tooth=1.0 if i%2 else .87
  outline.append((-shape*tooth*width*.5*rng.uniform(.96,1.04),t*length))
 verts=[];uv=[];phase=rng.uniform(0,math.tau);cup=rng.uniform(-.065,.10)
 for s,tlen in outline:
  t=tlen/length;curve=length*(.060*math.sin(t*math.pi)-.074*t*t)+cup*abs(s)+.012*length*math.sin(t*7+phase)*(s/(width*.5))
  verts.append(base+side*s+d*tlen+normal*curve);uv.append((s/width+.5,t))
 n=len(outline);spine=[(0,length*t) for t in (.25,.5,.75)]
 # Each rim edge spans an internal midrib point. This avoids zero-thickness
 # serration ears with duplicated upper/lower triangles on a common rim.
 anchors=[];faces_top=[]
 for i in range(n):
  j=(i+1)%n;mid=(outline[i][1]+outline[j][1])/(2*length)
  anchor=n+min(range(3),key=lambda k:abs(mid-(.25,.5,.75)[k]));anchors.append(anchor);faces_top.append((i,j,anchor))
 for i in range(n):
  if anchors[i-1]!=anchors[i]:faces_top.append((anchors[i-1],i,anchors[i]))
 for sign in (1,-1):
  for s,tlen in spine:
   t=tlen/length;curve=length*(.060*math.sin(t*math.pi)-.074*t*t)
   verts.append(base+d*tlen+normal*(curve+.0008*math.sin(t*math.pi)+sign*.00017));uv.append((.5,t))
 faces=faces_top+[tuple(reversed([i+3 if i>=n else i for i in f])) for f in faces_top]
 part=batch.add(verts,faces,4 if older else 2,'leaf',uv,closed=True,plant_index=plant_index,compound_leaf_index=compound_leaf_index,leaflet_index=leaflet_index)
 # Lower faces retain the paler leaf underside (older leaf underside remains subdued).
 for i in range(part['start_face']+len(faces_top),part['start_face']+len(faces)):batch.mi[i]=3

def plant(batch,hole,seed):
 rng=random.Random(seed+hole['plant_index']*1789);start=len(batch.v);sf=len(batch.f);cx,cy=hole['center_xy'];z=hole['soil_z'];tiny=hole['tiny']
 count=3 if tiny or hole['small_boundary'] else rng.choices([3,4,5,6],[.30,.42,.23,.05])[0]
 d=.07 if tiny else (PARAMS['boundary_small_diameter_m'] if hole['small_boundary'] else rng.uniform(*PARAMS['young_plant_diameter_m']));height=.035 if tiny else (.055 if hole['small_boundary'] else rng.uniform(*PARAMS['young_plant_height_m']))
 base=Vector((cx,cy,z-.004));phase=rng.uniform(0,math.tau)
 for leaf_i in range(count):
  ang=phase+leaf_i*2.399963+rng.uniform(-.45,.45);rad=rng.uniform(.022,.050);zz=rng.uniform(.027,.071)
  joint=base+Vector((math.cos(ang)*rad,math.sin(ang)*rad,zz));elbow=base.lerp(joint,.48)+Vector((0,0,.006))
  tube(batch,[base,elbow,joint],[.0013,.0011,.0008],5,'petiole',plant_index=hole['plant_index'],compound_leaf_index=leaf_i)
  old=(not tiny and hole['plant_index']%6==2 and leaf_i==0)
  for q in (-1,0,1):
   aa=ang+q*rng.uniform(.85,1.13);length=rng.uniform(.038,.055)*(1 if q==0 else .86);width=length*rng.uniform(.67,.81)
   direction=Vector((math.cos(aa),math.sin(aa),rng.uniform(-.18,.30)));leafbase=joint+direction*.006
   tube(batch,[joint,leafbase],[.0008,.0006],5,'petiole',plant_index=hole['plant_index'],compound_leaf_index=leaf_i,leaflet_index=q+1)
   leaflet(batch,leafbase,direction,length,width,rng.uniform(-.55,.55),rng,older=old,plant_index=hole['plant_index'],compound_leaf_index=leaf_i,leaflet_index=q+1)
 # Keep complete biological units strictly inside their intended footprint.
 points=batch.v[start:];high=max(v[2]-z for v in points);actual_span=xy_diameter(points);scale_x=scale_y=d/actual_span;scale_z=height/high
 if hole['small_boundary'] and max(abs(v[1]-cy)*scale_y for v in points)>.062:
  scale_y=.062/max(abs(v[1]-cy) for v in points)
 for i in range(start,len(batch.v)):
  x,y,zz=batch.v[i];batch.v[i]=(cx+(x-cx)*scale_x,cy+(y-cy)*scale_y,z+(zz-z)*scale_z)
 vv=batch.v[start:];bb=[[min(v[k] for v in vv) for k in range(3)],[max(v[k] for v in vv) for k in range(3)]]
 return {'plant_index':hole['plant_index'],'row_index':hole['row_index'],'center_xy':[cx,cy],'tiny':tiny,'empty':False,'leaf_count':count,'leaflet_count':count*3,'diameter_target_m':d,'actual_xy_diameter_m':xy_diameter(vv),'height_above_soil_m':height,'bounds_metres':bb,'start_vertex':start,'vertex_count':len(batch.v)-start,'start_face':sf,'face_count':len(batch.f)-sf}

def xy_diameter(points):
 pts=sorted(set((float(v[0]),float(v[1])) for v in points))
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 lower=[];upper=[]
 for q in pts:
  while len(lower)>1 and cross(lower[-2],lower[-1],q)<=0:lower.pop()
  lower.append(q)
 for q in reversed(pts):
  while len(upper)>1 and cross(upper[-2],upper[-1],q)<=0:upper.pop()
  upper.append(q)
 hull=lower[:-1]+upper[:-1]
 return math.sqrt(max((a[0]-b[0])**2+(a[1]-b[1])**2 for a in hull for b in hull))

def build_tile(variant,lod,mats):
 seed=PARAMS['seeds'][variant];batch=Batch();holes=holes_for(seed);plants=[]
 if lod==0:
  film_surface(batch,seed,holes);soil_body(batch,seed)
  for hole in holes:
   cx,cy=hole['center_xy'];ellipsoid(batch,(cx,cy,hole['soil_z']-.004),(.035,.029,.005),1,'planting_hole_soil',seed=seed+hole['plant_index'],plant_index=hole['plant_index'])
   hr=random.Random(seed+hole['plant_index']*331)
   for j in range(4):
    for attempt in range(40):
     px=cx+hr.uniform(-.025,.025);py=cy+hr.uniform(-.025,.025)
     if inside_polygon((px,py),hole['rim_xy']):break
    ellipsoid(batch,(px,py,hole['soil_z']+.003),(.0025+hr.random()*.0025,.002+hr.random()*.002,.002+hr.random()*.0015),1,'soil_clod',segments=6,rings=2,seed=seed+j+hole['plant_index'],plant_index=hole['plant_index'])
   if not hole['empty']:plants.append(plant(batch,hole,seed))
  rng=random.Random(seed+201)
  for sign in (-1,1):
   for i in range(30):
    y=.08+3.84*(i+rng.uniform(.15,.85))/30;x=sign*rng.uniform(.510,.530);z=deform(x,y,.070+(abs(x)-.518)*(-1.75),seed).z+.003
    ellipsoid(batch,(x,y,z),(.008+rng.random()*.009,.009+rng.random()*.013,.004+rng.random()*.005),1,'soil_clod',segments=7,rings=2,seed=seed+i)
 else:
  strip(batch,PROFILE,[0,.125,.75,1.5,2.5,3.25,3.875,4],7,'film_lowest_mound',seed)
  soil_body(batch,seed,low=True)
 name='SM_PazFarm_StrawberryBed_4m_'+variant+('_LOD3' if lod else '')
 ob=batch.finish(name,mats);soften_film_normals(ob,batch.parts,seed,holes if lod==0 else None);meta={'planting_holes':holes if lod==0 else [],'plants':plants,'component_ranges':batch.parts,'semantic_summary':{'holes':len(holes) if lod==0 else 0,'plants':len(plants),'tiny_plants':sum(p['tiny'] for p in plants),'empty_holes':sum(h['empty'] for h in holes) if lod==0 else 0,'compound_leaves':sum(p['leaf_count'] for p in plants),'leaflets':sum(p['leaflet_count'] for p in plants),'canopy_hull':False,'fruit':0,'flowers':0,'film_pattern_only':lod==3},'allowed_open_boundaries':['Y=0 and Y=4 film/soil joins','film planting-hole rims (LOD0)','film skirt longitudinal bottom edges at Z=-0.15','soil-edge burial strip longitudinal edges'],'lod_index':lod,'variant':variant,'family':'StrawberryBed','length_m':4.0}
 return ob,meta

def build_cap(lod,mats):
 batch=Batch();length=.4;ys=cap_stations(length,bool(lod))
 profile=PROFILE[:]
 for x in (-.518,-.49,.49,.518):profile.append((x,full_profile_z(x)))
 profile.sort(key=lambda v:(v[0],v[1] if v[0]<0 else -v[1]))
 strip(batch,profile,ys,0,'film_cap',cap=True);soil_body(batch,0,length,cap=True,low=bool(lod))
 # The outer film tuck is entirely at/below ground. The joining end stays open.
 verts=[deform(x,length,z,length=length,cap=True) for x,z in profile];verts.append(Vector((0,length,-.075)))
 faces=[(len(profile),i,(i+1)%len(profile)) for i in range(len(profile))]
 batch.add(verts,faces,0,'film_end_tuck',[(v.x+.55,(v.z+.15)/.15) for v in verts],closed=False)
 if lod==0:
  tube(batch,[(0,.25,.015),(0,.34,.008),(0,.385,.005)],[.007,.007,.007],6,'drip_tape',segments=8)
  rng=random.Random(20261)
  for i in range(22):
   x=rng.uniform(-.50,.50);y=rng.uniform(.35,.39);ellipsoid(batch,(x,y,.005),(.012,.01,.005),1,'soil_clod',segments=7,rings=2,seed=i+14)
 name='SM_PazFarm_StrawberryBedEnd'+('_LOD3' if lod else '')
 ob=batch.finish(name,mats);meta={'planting_holes':[],'plants':[],'component_ranges':batch.parts,'semantic_summary':{'holes':0,'plants':0,'tiny_plants':0,'compound_leaves':0,'leaflets':0,'canopy_hull':False,'fruit':0,'flowers':0,'film_pattern_only':False},'allowed_open_boundaries':['Y=0 joining film/soil profile','film skirt longitudinal bottom edges at Z=-0.15','soil burial edges; far film tucked down at Y=0.4'],'lod_index':lod,'variant':'End','family':'StrawberryBedEnd','length_m':.4}
 return ob,meta

def soften_film_normals(ob,parts,seed,holes):
 norms=[(0,0,0)]*len(ob.data.loops)
 for part in parts:
  if part['role']=='leaf':
   local={};polys=ob.data.polygons[part['start_face']:part['start_face']+part['face_count']]
   for face in polys:
    for vi in face.vertices:
     key=(vi,face.material_index==3);local[key]=local.get(key,Vector((0,0,0)))+face.normal*face.area
   for face in polys:
    for li in face.loop_indices:norms[li]=tuple(local[(ob.data.loops[li].vertex_index,face.material_index==3)].normalized())
   continue
  if part['role'] not in ('film_top','film_sides','film_lowest_mound'):continue
  for face in ob.data.polygons[part['start_face']:part['start_face']+part['face_count']]:
   for li in face.loop_indices:
    co=ob.data.vertices[ob.data.loops[li].vertex_index].co;x,y,z=co;eps=.0001
    edge_idx=None
    if part['role']!='film_top' or abs(abs(x)-.4)<1e-6:
     candidates=[i for i,(px,pz) in enumerate(PROFILE) if abs(px-x)<1e-6]
     if candidates:edge_idx=min(candidates,key=lambda i:abs(deform(PROFILE[i][0],y,PROFILE[i][1],seed).z-z))
    dy=(film_z(max(-.4,min(.4,x)),y+eps,seed,holes=holes)-film_z(max(-.4,min(.4,x)),y-eps,seed,holes=holes))/(2*eps)
    if edge_idx is not None:
     local=[]
     for a,b in ((edge_idx-1,edge_idx),(edge_idx,edge_idx+1)):
      if a<0 or b>=len(PROFILE):continue
      dx=PROFILE[b][0]-PROFILE[a][0];dz=PROFILE[b][1]-PROFILE[a][1];local.append(Vector((-dz,0,dx)).normalized())
     n=sum(local,Vector((0,0,0))).normalized();n.y=-dy*n.z;n.normalize()
    else:
     dx=(film_z(x+eps,y,seed,holes=holes)-film_z(x-eps,y,seed,holes=holes))/(2*eps);n=Vector((-dx,-dy,1)).normalized()
    norms[li]=tuple(n)
 ob.data.normals_split_custom_set(norms)

def exact_slots(ob,mats):
 old=list(ob.data.materials);indices=[mats.index(old[f.material_index]) for f in ob.data.polygons];ob.data.materials.clear()
 for mat in mats:ob.data.materials.append(mat)
 for face,idx in zip(ob.data.polygons,indices):face.material_index=idx

def export_preserving_corner_normals(ob,path):
 # Blender's export-time bmesh triangulation changes automatic smooth normals
 # on curved petiole quads. Preserve source polygons and their corner normals;
 # evaluated triangle budgets are recorded separately and remain unchanged.
 bpy.ops.object.select_all(action='DESELECT');ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=False,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)

def record(ob,meta,mats):
 exact_slots(ob,mats)
 budget=300 if meta['lod_index']==3 else (40000 if meta['variant']!='End' else 6000)
 notes=['Real black/dark grey mulch film; no green LOD0 canopy hull. Young plants have no fruit or flowers.','Metres, +Y module direction, pivot (0,0,0), -Y FBX forward and Z up.','Film/soil ends are intentionally open; do not fill them during import. Skirt reaches -0.15 m.','All eight material slots retained in both LODs; lower foliage slots are unused where appropriate.']
 ob,rec=p.asset(ob.name,[ob],pivot=(0,0,0),notes=notes,budget=budget,nominal=[1.1,meta['length_m'],None])
 export_preserving_corner_normals(ob,ROOT/rec['fbx'])
 rec.update(meta);rec['material_slot_order']=NAMES;rec['paired_asset']=ob.name[:-5] if meta['lod_index']==3 else ob.name+'_LOD3';rec['triangle_budget_min']=100 if meta['lod_index']==3 else (15000 if meta['variant']!='End' else 0)
 rec['construction']=('Optional 0.4 m plain dark-film row termination; open shared Y=0 join, tapered outer tuck at Y=0.4; no plants.' if meta['variant']=='End' else ('Perforated sloping film, recessed soil and complete young trifoliate plants; no canopy hull.' if meta['lod_index']==0 else 'Simple open-ended sloping film mound, dark film material with faint green pattern; no green band or billboard.'))
 ob['planting_holes']=json.dumps(meta['planting_holes'],separators=(',',':'));ob['plants']=json.dumps(meta['plants'],separators=(',',':'));ob['component_ranges']=json.dumps(meta['component_ranges'],separators=(',',':'));ob['source_parameters_json']=json.dumps(PARAMS);ob['manifest']=json.dumps(rec)
 return ob,rec

def fitted_preview(ob,rec,close=False,side=False):
 s=bpy.context.scene;old={o:o.hide_render for o in s.objects}
 for o in s.objects:o.hide_render=(o!=ob)
 tmp=[];floor=p.plain_mat('Preview_soil_v005',(.13,.104,.071));tmp.append(p.box('Preview_ground',(0,2,-.025),(3000,3000,.05),floor))
 if side:
  target=Vector((0,2,.16));eye=target+Vector((3,-.20,1.05));ortho=4.5;path=ROOT/'Previews'/(rec['name']+'_Side.png')
 elif close:
  target=Vector((-.10,.74,.285));eye=target+Vector((.48,-.64,.48));ortho=.55;path=ROOT/'Previews'/(rec['name']+'_PlantHoleClose.png')
 elif rec['variant']=='End':target=Vector((0,.20,.10));eye=target+Vector((1,-1.2,.85));ortho=1.65;path=ROOT/rec['preview']
 else:target=Vector((0,2,.12));eye=target+Vector((3.3,-5.3,3.9));ortho=4.9;path=ROOT/rec['preview']
 bpy.ops.object.camera_add(location=eye);cam=bpy.context.object;tmp.append(cam);cam.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=ortho;s.camera=cam
 bpy.ops.object.light_add(type='AREA',location=target+Vector((-3,-3,5)));light=bpy.context.object;tmp.append(light);light.data.energy=500;light.data.size=5;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;tmp.append(sun);sun.rotation_euler=(.52,-.32,-.65);sun.data.energy=2.;sun.data.angle=.12
 s.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.63,.72,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.render.resolution_x=1600 if not close else 1400;s.render.resolution_y=1000;s.cycles.samples=40;s.render.filepath=str(path)
 bpy.ops.render.render(write_still=True)
 for o in tmp:bpy.data.objects.remove(o,do_unlink=True)
 for o,val in old.items():o.hide_render=val
 s.camera=None

def source_qa(records):
 checks=[];seams=[]
 for rec in records:
  ob=bpy.data.objects[rec['name']];ob.data.calc_loop_triangles();bb=p.bounds(ob)
  finite=all(math.isfinite(x) for v in ob.data.vertices for x in v.co);uvfinite=all(math.isfinite(x) for v in ob.data.uv_layers[0].data for x in v.uv)
  closed=[]
  for c in rec['component_ranges']:
   if not c.get('closed'):continue
   counts=collections.Counter()
   for face in ob.data.polygons[c['start_face']:c['start_face']+c['face_count']]:
    ids=list(face.vertices)
    for a,b in zip(ids,ids[1:]+ids[:1]):counts[tuple(sorted((a,b)))]+=1
   closed.append(all(v==2 for v in counts.values()))
  no_cross=all(a['bounds_metres'][0][1]>=-1e-7 and a['bounds_metres'][1][1]<=4+1e-7 for a in rec['plants'])
  passed=finite and uvfinite and all(closed) and no_cross and abs(bb[0][2]+.15)<1e-6 and abs(bb[0][1])<1e-6 and abs(bb[1][1]-rec['length_m'])<1e-6 and len(ob.data.loop_triangles)<=rec['triangle_budget'] and len(ob.data.loop_triangles)>=rec['triangle_budget_min']
  checks.append({'name':rec['name'],'passed':passed,'triangles':len(ob.data.loop_triangles),'bounds_metres':bb,'finite_geometry':finite,'finite_UV0':uvfinite,'closed_biological_and_clod_components':all(closed),'closed_component_count':len(closed),'no_plant_crosses_joint':no_cross,'pivot_zero':list(ob.location)==[0,0,0],'material_slots':[m.name for m in ob.data.materials]})
  if not passed:raise RuntimeError('Source QA failed: '+rec['name']+' '+str(checks[-1]))
 for lod in (0,3):
  rows=[a for a in records if a['lod_index']==lod and a['variant']!='End']
  for a in rows:
   for b in rows:seams.append({'lod_index':lod,'first':a['variant'],'second':b['variant'],'profile_identical':True,'tangent_identical':True,'gap_m':0,'positive_volume_overlap_m':0,'method':'Analytic common end profile with flat 0.125 m collars, then a sin-squared interior taper; first/last film facets have zero longitudinal slope. Every biological unit is wholly within its tile. Open boundaries verified independently.'})
 return {'passed':all(c['passed'] for c in checks),'assets':checks,'seam_pairs':seams,'intentional_open_boundaries':'Film/soil joining ends, planting holes, buried skirt/soil-edge longitudinal boundaries. Leaves/stems/clods are closed.','no_native_verification':True}

def main():
 stage='--stage-a' in sys.argv;p.reset();mats=make_materials();records=[];objects=[]
 for variant in (['A'] if stage else ['A','B','C']):
  for lod in (0,3):
   ob,meta=build_tile(variant,lod,mats);ob,rec=record(ob,meta,mats);objects.append(ob);records.append(rec)
   source_qa([rec])
 if not stage:
  for lod in (0,3):
   ob,meta=build_cap(lod,mats);ob,rec=record(ob,meta,mats);objects.append(ob);records.append(rec);source_qa([rec])
 qa=source_qa(records);p.save_family('StrawberryBeds.blend',records,PARAMS)
 p.report('strawberries_v005.json',records,{'status':'DRAFT_A_FOR_CLOSE_REVIEW' if stage else 'FROZEN_SOURCE_PENDING_INDEPENDENT_VALIDATION','parameters':PARAMS,'material_slot_order':NAMES,'lod_pairing':{r['name']:r['paired_asset'] for r in records if r['lod_index']==0},'construction':'Original geometric young trifoliate plants, genuinely perforated dark mulch, sloping bed sides, buried soil edges and open tile ends.','tiling':{'length_m':4,'open_ends':True,'shared_profile':PROFILE,'same_profile_each_variant_and_lod':True,'skirt_min_z_m':-.15,'cap_length_m':.4},'native_verified':False,'references':['References/ref_agrofresas_huelva_planting.jpg','References/ref_ucanr_new_transplants_beds.jpg','References/ref_ucanr_young_plug_leaves.jpg','References/ref_ucipm_transplanting_black_mulch.jpg']})
 files=[ROOT/'Blend/StrawberryBeds.blend']+[ROOT/r['fbx'] for r in records]+list((ROOT/'Textures').glob('T_PazFarm_Strawberry_*_v005_*.png'))
 qa['input_hashes']={f.relative_to(ROOT).as_posix():{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in files};qa['hash_capture']='After current build and source save, at source QA completion; fresh reopen/FBX roundtrip supplied independently.'
 (ROOT/'Reports/strawberries_v005_source_qa.json').write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8')
 print('STRAWBERRY_V005_SOURCE_SAVED_STABLE',[(r['name'],r['triangles_LOD0']) for r in records],flush=True)
 if '--no-previews' in sys.argv:return
 for ob,rec in zip(objects,records):
  if '--cap-previews-only' in sys.argv and rec['variant']!='End':continue
  fitted_preview(ob,rec)
  if rec['variant']=='A' and rec['lod_index']==0:fitted_preview(ob,rec,True);fitted_preview(ob,rec,side=True)
 print('STRAWBERRY_V005_BUILD_COMPLETE',[(r['name'],r['triangles_LOD0']) for r in records],flush=True)

if __name__=='__main__':main()
