"""Independent Blender reopen + fresh FBX round-trip for all v003 LODs.

This script only writes the validation receipt inside the current revision.
"""
import bpy, json, math, sys, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ASSETS = []
for fragment in ['pines_v003.json', 'strawberries_v003.json']:
    ASSETS.extend(json.loads((ROOT/'Reports'/fragment).read_text(encoding='utf-8'))['assets'])
OUT = {'method':'Fresh Blender process reopens retained sources, then resets the scene and imports each separate FBX at metre unit scale 1.0. No Unreal operations.',
       'blender':bpy.app.version_string,'assets':[],'sources':[],'lod_pairs':[],'failures':[]}
def fail(message): OUT['failures'].append(message)
def inspect(obj):
    obj.data.calc_loop_triangles()
    pts = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
    bb = [[min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]]
    counts = {}
    for poly in obj.data.polygons:
        for edge in poly.edge_keys:
            edge = tuple(sorted(edge)); counts[edge] = counts.get(edge,0)+1
    uv = obj.data.uv_layers.get('UV0')
    return {'triangles':len(obj.data.loop_triangles),
            'zero_area_triangles':sum(t.area<1e-12 for t in obj.data.loop_triangles),
            'bounds_metres':bb,'size_metres':[bb[1][i]-bb[0][i] for i in range(3)],
            'pivot_metres':list(obj.matrix_world.translation),
            'finite_geometry':all(math.isfinite(c) for v in obj.data.vertices for c in v.co),
            'finite_normals':all(math.isfinite(c) for p in obj.data.polygons for c in p.normal),
            'uv0_present':uv is not None,
            'finite_uv0':uv is not None and all(math.isfinite(c) for d in uv.data for c in d.uv),
            'boundary_edges':sum(n==1 for n in counts.values()),
            'nonmanifold_edges':sum(n>2 for n in counts.values()),
            'materials':[m.name if m else None for m in obj.data.materials],
            'identity_scale':all(abs(x-1)<1e-6 for x in obj.scale)}

source_objects={}
for source in sorted({a['blend'] for a in ASSETS}):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/source), load_ui=False, use_scripts=False)
    entry={'file':source,'sha256':hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),'unit_scale':bpy.context.scene.unit_settings.scale_length,'meshes':[],'images':[],'materials':[]}
    if abs(entry['unit_scale']-1)>1e-8: fail(source+': non-metre source')
    for a in [x for x in ASSETS if x['blend']==source]:
        o=bpy.data.objects.get(a['name'])
        if o is None: fail(a['name']+': source object missing'); continue
        v=inspect(o);v['name']=a['name'];source_objects[a['name']]=v;entry['meshes'].append(v)
        if not all(v[k] for k in ['finite_geometry','finite_normals','uv0_present','finite_uv0','identity_scale']) or v['zero_area_triangles']:
            fail(a['name']+': source geometry/UV/scale invalid')
        if a['name'].endswith('_LOD3') and (v['boundary_edges'] or v['nonmanifold_edges']):
            fail(a['name']+': lowest LOD must be closed solid geometry')
    relevant_materials={m for a in ASSETS if a['blend']==source for m in bpy.data.objects[a['name']].data.materials}
    for mat in sorted(relevant_materials,key=lambda m:m.name):
        bs=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
        alpha=bs.inputs.get('Alpha') if bs else None
        r={'name':mat.name,'mode_intent':mat.get('blend_mode_intent','unspecified'),
           'backface_culling':mat.use_backface_culling,
           'alpha_default':float(alpha.default_value) if alpha else None,
           'alpha_linked':bool(alpha and alpha.is_linked)}
        entry['materials'].append(r)
        if alpha and not alpha.is_linked and alpha.default_value<.999:fail(mat.name+': shader is not solid alpha')
        if any(k in mat.name.lower() for k in ['leaf','needle']) and mat.use_backface_culling: fail(mat.name+': foliage is not two-sided')
    for im in bpy.data.images:
        if not im.filepath:continue
        p=Path(bpy.path.abspath(im.filepath))
        r={'name':im.name,'path':im.filepath,'exists':p.is_file(),'relative':im.filepath.startswith('//'),'size':list(im.size),'colour_space':im.colorspace_settings.name,
           'delivery_path':p.resolve().relative_to(ROOT.resolve()).as_posix() if p.resolve().is_relative_to(ROOT.resolve()) else None,
           'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None}
        if r['delivery_path'] is None:fail(source+': texture outside revision '+im.name)
        if not r['exists'] or not r['relative'] or r['size']!=[1024,1024]:fail(source+': image contract '+im.name)
        if 'BaseColor' in im.name:
            pixels=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(pixels)
            r['alpha_range']=[float(pixels[3::4].min()),float(pixels[3::4].max())]
            if r['alpha_range'][0]<.999:fail(source+': non-solid texture alpha '+im.name)
        entry['images'].append(r)
    OUT['sources'].append(entry)

for a in ASSETS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
    p=ROOT/a['fbx'];bpy.ops.import_scene.fbx(filepath=str(p),use_anim=False)
    obj=bpy.data.objects.get(a['name'])
    if obj is None: fail(a['name']+': FBX render object missing');continue
    bpy.context.view_layer.update();r=inspect(obj);r['name']=a['name'];r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();r['bytes']=p.stat().st_size
    r['size_error_m']=max(abs(x-y) for x,y in zip(r['size_metres'],a['size_metres_W_D_H']))
    r['pivot_error_m']=max(abs(x-y) for x,y in zip(r['pivot_metres'],a['pivot']['position_metres']))
    actual_source=source_objects[a['name']]
    r['source_bounds_error_m']=max(abs(r['bounds_metres'][i][j]-actual_source['bounds_metres'][i][j]) for i in range(2) for j in range(3))
    r['source_pivot_error_m']=max(abs(x-y) for x,y in zip(r['pivot_metres'],actual_source['pivot_metres']))
    r['source_triangle_count_match']=r['triangles']==actual_source['triangles']
    r['visual_meshes']=sum(o.type=='MESH' and not o.name.startswith('UCX_') for o in bpy.data.objects)
    r['collision_names']=[o.name for o in bpy.data.objects if o.name.startswith('UCX_')]
    r['budget']=a['triangle_budget'];r['lod']=3 if a['name'].endswith('_LOD3') else 0
    if r['size_error_m']>.0001 or r['pivot_error_m']>.0001:fail(a['name']+': round-trip dimensions/pivot')
    if r['source_bounds_error_m']>.0001 or r['source_pivot_error_m']>.0001 or not r['source_triangle_count_match']:fail(a['name']+': FBX differs from actual reopened source geometry')
    if r['triangles']!=a['triangles_LOD0'] or r['triangles']>r['budget']:fail(a['name']+': triangle count/budget')
    if r['zero_area_triangles'] or not all(r[k] for k in ['finite_geometry','finite_normals','uv0_present','finite_uv0']):fail(a['name']+': invalid FBX geometry/UV')
    if r['visual_meshes']!=1 or len(r['collision_names'])!=len(a.get('collision_objects',[])):fail(a['name']+': FBX object/collision count')
    if r['materials']!=source_objects[a['name']]['materials']:fail(a['name']+': FBX material order differs')
    if r['lod']==3:
        lo,hi=(800,2000) if 'AleppoPine' in a['name'] else (100,400)
        if not lo<=r['triangles']<=hi:fail(a['name']+': lowest LOD target budget')
        if r['boundary_edges'] or r['nonmanifold_edges']:fail(a['name']+': FBX lowest LOD is not closed solid geometry')
    elif 'AleppoPine' in a['name'] and not 40000<=r['triangles']<=120000:fail(a['name']+': LOD0 pine target budget')
    if 'Strawberry' in a['name']:
        if max(abs(r['bounds_metres'][0][0]+.4),abs(r['bounds_metres'][1][0]-.4),abs(r['bounds_metres'][0][1]),abs(r['bounds_metres'][1][1]-4),abs(r['bounds_metres'][0][2]))>.0001:fail(a['name']+': strawberry tile envelope/start-end ground pivot')
    for m in a['materials']:
        for tex in m['textures']:
            if not (ROOT/tex).is_file():fail(a['name']+': missing texture '+tex)
    if not (ROOT/a['preview']).is_file():fail(a['name']+': missing hero preview')
    OUT['assets'].append(r)

for high in [a for a in OUT['assets'] if a['lod']==0]:
    low=next(a for a in OUT['assets'] if a['name']==high['name']+'_LOD3')
    ratio=[low['size_metres'][i]/high['size_metres'][i] for i in range(3)]
    OUT['lod_pairs'].append({'high':high['name'],'low':low['name'],'size_ratio_low_to_high':ratio,'triangle_ratio':low['triangles']/high['triangles'],'same_pivot':max(abs(x-y) for x,y in zip(high['pivot_metres'],low['pivot_metres']))<1e-7})
    if any(v<.80 or v>1.1 for v in ratio):fail(high['name']+': excessive lowest LOD envelope change')
if len(OUT['assets'])!=8 or len(OUT['sources'])!=2:fail('Expected four model families with two LODs each and two source files')
OUT['passed']=not OUT['failures']
(ROOT/'Reports/VALIDATION.json').write_text(json.dumps(OUT,indent=2),encoding='utf-8')
print('V003_VALIDATION',OUT['passed'],'ASSETS',len(OUT['assets']),'FAILURES',OUT['failures'])
if not OUT['passed']:raise RuntimeError('v003 independent validation failed')
