"""Original orchard tree meshes; deterministic retained source for seven Paz Farm variants."""
import sys, math, random, json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
import paz_common as p

CONFIG={
 'Avocado':{'heights':[5.8,6.4,5.4],'widths':[5.5,5.9,5.15],'depths':[5.25,5.45,5.4],'leaf_count':10800,'leaf_length':.255,'leaf_width':.115,'fruit_count':18,'trunk_radius':.125,'leaf_color':(.070,.185,.035)},
 'Lemon':{'heights':[3.45,3.8],'widths':[3.25,3.5],'depths':[3.1,3.25],'leaf_count':9600,'leaf_length':.172,'leaf_width':.079,'fruit_count':46,'trunk_radius':.105,'leaf_color':(.084,.22,.043)},
 'Orange':{'heights':[3.65,3.3],'widths':[3.65,3.2],'depths':[3.35,3.05],'leaf_count':9500,'leaf_length':.178,'leaf_width':.086,'fruit_count':56,'trunk_radius':.11,'leaf_color':(.071,.18,.032)}
}

class Batch:
 def __init__(self):self.v=[];self.f=[];self.uv=[]
 def face(self,coords,uv):
  start=len(self.v);self.v.extend([tuple(a) for a in coords]);self.f.append(tuple(range(start,start+len(coords))));self.uv.append(uv)
 def tube(self,a,b,r1,r2,n=8):
  a,b=Vector(a),Vector(b);d=(b-a).normalized();side=d.cross(Vector((0,0,1)))
  if side.length<.01:side=d.cross(Vector((1,0,0)))
  side.normalize();other=d.cross(side).normalized()
  for j in range(n):
   t=j*math.tau/n;t2=(j+1)*math.tau/n
   u=side*math.cos(t)+other*math.sin(t);v=side*math.cos(t2)+other*math.sin(t2)
   self.face([a+u*r1,a+v*r1,b+v*r2,b+u*r2],[(j/n,0),((j+1)/n,0),((j+1)/n,(b-a).length*3),(j/n,(b-a).length*3)])
  self.face([a+(side*math.cos(-j*math.tau/n)+other*math.sin(-j*math.tau/n))*r1 for j in range(n)],[(.5+.5*math.cos(-j*math.tau/n),.5+.5*math.sin(-j*math.tau/n)) for j in range(n)])
  self.face([b+(side*math.cos(j*math.tau/n)+other*math.sin(j*math.tau/n))*r2 for j in range(n)],[(.5+.5*math.cos(j*math.tau/n),.5+.5*math.sin(j*math.tau/n)) for j in range(n)])
 def leaf(self,base,direction,width,length,roll):
  base=Vector(base);along=Vector(direction).normalized();side=along.cross(Vector((0,0,1)))
  if side.length<.02:side=along.cross(Vector((1,0,0)))
  side.normalize();up=along.cross(side).normalized();side=side*math.cos(roll)+up*math.sin(roll);up=along.cross(side).normalized()
  # Two curved card strips, matching lancet-shaped alpha texture and central vein.
  points=[]
  for t in (0,.5,1):
   center=base+along*length*t+up*(math.sin(t*math.pi)*length*.12)
   points.extend([center-side*width/2,center+side*width/2])
  self.face([points[0],points[1],points[3],points[2]],[(0,0),(1,0),(1,.5),(0,.5)])
  self.face([points[2],points[3],points[5],points[4]],[(0,.5),(1,.5),(1,1),(0,1)])
 def obj(self,name,mat):return p.mesh(name,self.v,self.f,mat,self.uv,True)

def tree(species,index,params,mats):
 rng=random.Random(1301+index*73+sum(map(ord,species)))
 h=params['heights'][index];w=params['widths'][index];depth=params['depths'][index]
 center_z=h*.64; rz=h*.345;rr=w*.39;tr=params['trunk_radius']
 bark=Batch();leaf_batches=[Batch(),Batch(),Batch()]
 trunk=[Vector((0,0,0)),Vector((.025,-.018,h*.095)),Vector((-.045,.02,h*.20)),Vector((.015,.03,h*.31))]
 for i in range(3):bark.tube(trunk[i],trunk[i+1],tr*(1-i*.13),tr*(.87-i*.13),12)
 for j in range(5):
  a=j*math.tau/5+.25;start=Vector((math.cos(a)*tr*1.30,math.sin(a)*tr*1.30,.018));bark.tube(start,trunk[1],tr*.34,tr*.45,8)
 scaff=[]
 for j in range(9):
  angle=j*math.tau/9+rng.uniform(-.17,.17)
  start=trunk[2] if j%2 else trunk[3]
  end=Vector((math.cos(angle)*w*.22,math.sin(angle)*depth*.22,h*(.42+.06*(j%3))))
  mid=start.lerp(end,.53)+Vector((0,0,-h*.04))
  bark.tube(start,mid,tr*.65,tr*.36,10);bark.tube(mid,end,tr*.36,tr*.19,9);scaff.append(end)
 clusters=[]
 for ring,(zz,count) in enumerate([(-.65,12),(-.34,16),(0.,18),(.34,16),(.65,12),(.87,6)]):
  for j in range(count):
   a=(j+.3*(ring%2))*math.tau/count+rng.uniform(-.09,.09)
   radius=math.sqrt(1-zz*zz)*rr*rng.uniform(.88,1.06)
   c=Vector((math.cos(a)*radius,math.sin(a)*radius*depth/w,center_z+zz*rz))
   parent=min(scaff,key=lambda s:(s-c).length)
   elbow=parent.lerp(c,.58)+Vector((0,0,-.045*h));bark.tube(parent,elbow,tr*.14,tr*.07,7);bark.tube(elbow,c,tr*.07,.0025,6)
   clusters.append(c)
 # Smaller interior clusters stop the shell looking hollow while retaining individual leaf silhouettes.
 for j in range(8):clusters.append(Vector((rng.uniform(-.18,.18)*w,rng.uniform(-.18,.18)*depth,center_z+rng.uniform(-.15,.2)*h)))
 per=params['leaf_count']//len(clusters)
 for k,c in enumerate(clusters):
  cl=w*rng.uniform(.092,.127)
  for j in range(6):
   a=rng.random()*math.tau;tip=c+Vector((math.cos(a)*cl*.75,math.sin(a)*cl*.75,rng.uniform(-.18,.20)*cl))
   bark.tube(c,tip,.0035,.0014,5)
  for j in range(per):
   theta=rng.uniform(0,math.tau);z=rng.uniform(-1,1);r=rng.random()**.35
   offs=Vector((math.sqrt(1-z*z)*math.cos(theta)*cl*r,math.sqrt(1-z*z)*math.sin(theta)*cl*r,z*cl*.8*r))
   pos=c+offs
   da=rng.random()*math.tau;direction=Vector((math.cos(da),math.sin(da),rng.uniform(-.6,.65)))
   length=params['leaf_length']*rng.uniform(.73,1.15);width=params['leaf_width']*rng.uniform(.8,1.12)
   leaf_batches[rng.choices([0,1,2],[.56,.31,.13])[0]].leaf(pos,direction,width,length,rng.uniform(-.65,.65))
 parts=[bark.obj(species+'_Bark',mats['bark'])]+[b.obj(species+'_Leaves_'+str(i),mats['leaves'][i]) for i,b in enumerate(leaf_batches)]
 for j in range(params['fruit_count']):
  c=clusters[j*7%len(clusters)];angle=math.atan2(c.y,c.x)
  loc=c+Vector((math.cos(angle)*w*.075,math.sin(angle)*w*.075,-w*.048))
  if species=='Avocado':scale=(.040,.040,.067)
  elif species=='Lemon':scale=(.043,.039,.063)
  elif index==1:scale=(.032,.032,.029)
  else:scale=(.042,.042,.041)
  fruit=p.sphere(species+'_Fruit',loc,scale,mats['fruit'],10,6)
  if species in ('Lemon','Avocado'):
   for v in fruit.data.vertices:
    fac=1-.17*abs(v.co.z) if species=='Lemon' else .79-.20*v.co.z
    v.co.x*=fac;v.co.y*=fac
  parts.append(fruit)
  parts.append(p.cylinder('FruitStem',loc+Vector((0,0,scale[2]*.9)),loc+Vector((0,0,scale[2]+.025)),.0022,mats['bark'],5))
 name='SM_PazFarm_'+species+'_'+'ABC'[index]
 ob=p.combine(name,parts)
 # Set measured horticultural envelope explicitly, retaining trunk-ground origin.
 bpy.context.view_layer.update();bb=p.bounds(ob)
 fx=w/(bb[1][0]-bb[0][0]);fy=depth/(bb[1][1]-bb[0][1]);fz=h/(bb[1][2]-bb[0][2])
 for v in ob.data.vertices:v.co.x*=fx;v.co.y*=fy;v.co.z=(v.co.z-bb[0][2])*fz
 ob.data.update();bpy.context.view_layer.update()
 note=['Original orchard tree with branching trunk, individually curved alpha-masked two-sided leaves, and scattered fruit.','No wind, no collision. UV0 includes intentional reusable leaf-card UV overlap.','Crown and height defaults are authored approximations; orchard species locations are not inferred from the aerial screenshot.','Blender ground origin at trunk base. For Unreal use foliage MASKED + Two Sided; base colour alpha is opacity mask.']
 if species=='Orange' and index==1:note.append('Variant B is clementine, with smaller fruit than orange variant A.')
 obj,rec=p.asset(name,[ob],budget=60000,notes=note,nominal=[w,depth,h]);obj['species']=species;obj['variant']='ABC'[index];obj['parameters']=json.dumps(params)
 p.preview(obj,rec,azimuth=-62,elevation=14)
 return obj,rec

def main():
 allrec=[]
 for species,params in CONFIG.items():
  if '--resume-citrus' in sys.argv and species=='Avocado':
   prior=json.loads((p.ROOT/'Reports'/'trees_progress.json').read_text())['assets']
   for r in prior:r['blend']='Blend/Avocado.blend'
   allrec+=prior
   continue
  p.reset()
  mats={'bark':p.pbr(species+'Bark',(.26,.185,.105),.87,kind='bark',res=1024),'leaves':[]}
  for i,f in enumerate([1.,1.18,.77]):mats['leaves'].append(p.pbr(species+'Leaf'+str(i),tuple(c*f for c in params['leaf_color']),.39 if species=='Avocado' else .46,kind='leaf',res=1024,seed=22+i))
  color={'Avocado':(.062,.10,.019),'Lemon':(.92,.70,.029),'Orange':(.95,.29,.009)}[species]
  mats['fruit']=p.pbr(species+'Fruit',color,.42,kind='noise',res=1024)
  records=[];obs=[]
  for i in range(len(params['heights'])):
   ob,rec=tree(species,i,params,mats);records.append(rec);obs.append(ob)
   p.report('trees_progress.json',allrec+records)
  for i,ob in enumerate(obs):ob.hide_set(i!=0);ob.hide_render=(i!=0)
  p.save_family(species+'.blend',records,params);allrec+=records
 p.report('trees.json',allrec,{'source':'Original deterministic geometry and textures; see Scripts/build_trees.py.','defaults':CONFIG})

if __name__=='__main__':main()
