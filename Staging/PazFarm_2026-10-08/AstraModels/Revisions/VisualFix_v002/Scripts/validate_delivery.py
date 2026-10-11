"""Fresh-process read-only Blender/FBX inspection. Writes only this delivery's QA report."""
import bpy, json, math, sys, hashlib
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]

def bbox(o):
 pts=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]

def inspect(o):
 o.data.calc_loop_triangles();b=bbox(o)
 return {'triangles':len(o.data.loop_triangles),'zero_area_triangles':sum(t.area<1e-12 for t in o.data.loop_triangles),'uv_layers':[u.name for u in o.data.uv_layers],'bounds_metres':b,'size_metres':[b[1][i]-b[0][i] for i in range(3)],'origin_metres':list(o.location),'finite_vertices':all(math.isfinite(v) for p in o.data.vertices for v in p.co),'finite_normals':all(math.isfinite(v) for p in o.data.polygons for v in p.normal),'material_slots':[m.name if m else None for m in o.data.materials]}

assets=[]
for f in ['trees_v002.json','barn_v002.json','strawberries_v002.json']:
 assets+=json.loads((ROOT/'Reports'/f).read_text(encoding='utf-8'))['assets']
out={'method':'Independent fresh Blender process reopens each retained .blend, imports each FBX separately at unit scale 1.0, and reads PNG metadata. No Unreal actions.','blender':bpy.app.version_string,'assets':[],'families':[],'failures':[]}
for filename in sorted(set(a['blend'] for a in assets)):
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/filename),load_ui=False,use_scripts=False)
 family={'file':filename,'unit_scale':bpy.context.scene.unit_settings.scale_length,'meshes':[],'texture_files':[]}
 if abs(family['unit_scale']-1)>1e-8:out['failures'].append(filename+': unit scale')
 for a in [a for a in assets if a['blend']==filename]:
  o=bpy.data.objects.get(a['name'])
  if o is None:out['failures'].append(a['name']+': source object missing');continue
  v=inspect(o);v['name']=a['name'];family['meshes'].append(v)
  if v['zero_area_triangles'] or not v['finite_vertices'] or not v['finite_normals'] or not v['uv_layers']:out['failures'].append(a['name']+': invalid source geometry')
 for im in bpy.data.images:
  if not im.filepath:continue
  path=Path(bpy.path.abspath(im.filepath));entry={'name':im.name,'filepath':im.filepath,'relative':im.filepath.startswith('//'),'exists':path.exists(),'size':list(im.size),'source':im.source}
  family['texture_files'].append(entry)
  if not entry['exists']:out['failures'].append(filename+': missing '+im.name)
  if not entry['relative']:out['failures'].append(filename+': texture path is not relative '+im.name)
  if list(im.size)!=[1024,1024]:out['failures'].append(filename+': texture is not required 1K '+im.name)
  if 'Leaf' in im.name and im.name.endswith('_BaseColor.png'):
   import numpy as np
   pixels=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(pixels)
   amin=float(pixels[3::4].min());amax=float(pixels[3::4].max())
   entry['alpha_range']=[amin,amax]
   if amin<.999:out['failures'].append(filename+': geometric foliage alpha is not full coverage '+im.name)
 out['families'].append(family)

for a in assets:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
 path=ROOT/a['fbx'];bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False)
 o=bpy.data.objects.get(a['name'])
 if o is None:out['failures'].append(a['name']+': FBX named render mesh missing');continue
 bpy.context.view_layer.update();r=inspect(o);r['name']=a['name'];r['fbx_bytes']=path.stat().st_size;r['fbx_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 r['roundtrip_size_error_metres']=max(abs(x-y) for x,y in zip(r['size_metres'],a['size_metres_W_D_H']))
 r['roundtrip_origin_error_metres']=max(abs(x-y) for x,y in zip(r['origin_metres'],a['pivot']['position_metres']))
 r['collision_names']=[ob.name for ob in bpy.data.objects if ob.name.startswith('UCX_')]
 r['collision_count_expected']=len(a['collision_objects'])
 r['render_mesh_count']=sum(ob.type=='MESH' and not ob.name.startswith('UCX_') for ob in bpy.data.objects)
 r['collision_geometry']=[{'name':c.name,'vertices':len(c.data.vertices),'polygons':len(c.data.polygons)} for c in bpy.data.objects if c.name.startswith('UCX_')]
 if r['roundtrip_size_error_metres']>.0001:out['failures'].append(a['name']+': FBX scale differs')
 if r['roundtrip_origin_error_metres']>.0001:out['failures'].append(a['name']+': FBX pivot differs')
 if r['triangles']!=a['triangles_LOD0']:out['failures'].append(a['name']+': FBX triangle count differs')
 if r['triangles']>a['triangle_budget']:out['failures'].append(a['name']+': triangle budget')
 if r['zero_area_triangles'] or not r['uv_layers']:out['failures'].append(a['name']+': FBX degenerate geometry or missing UV')
 if len(r['collision_names'])!=r['collision_count_expected']:out['failures'].append(a['name']+': FBX collision count')
 if r['render_mesh_count']!=1:out['failures'].append(a['name']+': unexpected FBX render mesh count')
 preview=ROOT/a['preview']
 if not preview.exists():out['failures'].append(a['name']+': preview missing')
 r['preview_exists']=preview.exists()
 for m in a['materials']:
  for tex in m['textures']:
   if not (ROOT/tex).exists():out['failures'].append(a['name']+': texture missing '+tex)
 out['assets'].append(r)
out['passed']=len(out['failures'])==0
(ROOT/'Reports'/'VALIDATION.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('PAZ_VALIDATION',out['passed'],len(out['assets']),'assets; failures',out['failures'])
if out['failures']:raise RuntimeError('Delivery validation failed')
