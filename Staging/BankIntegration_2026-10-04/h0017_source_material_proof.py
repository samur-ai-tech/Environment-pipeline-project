"""Read existing Blender geometry/material usage; never save or export sources."""
import collections
import hashlib
import json
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
CAT = HERE/'CategoryBatches/WholeBuildings'
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
job = next(r for r in read(CAT/'EXTERNAL_IMPORT_QUEUE.json') if r['asset_id']=='external.H0017')
recipe = next(r for r in read(CAT/'EXTERNAL_MATERIAL_RECIPES.json') if r['asset_id']=='external.H0017')
native = read(CAT/'PARTIAL_H0017_NATIVE_READBACK.json')
sections = read(CAT/'PARTIAL_H0017_SECTIONS.json')
assert sha(job['prepared_blend']) == recipe['prepared_blend_sha256']
assert sha(job['source_fbx']) == job['sha256']
bpy.ops.wm.open_mainfile(filepath=job['prepared_blend'])
counts = collections.Counter()
objects = []
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH' or obj.hide_render:
        continue
    obj.data.calc_loop_triangles()
    usage = collections.Counter()
    for tri in obj.data.loop_triangles:
        mat = obj.material_slots[tri.material_index].material
        assert mat
        usage[mat.name] += 1
    counts.update(usage)
    objects.append({'object':obj.name,'triangles':dict(usage)})
aliases = collections.defaultdict(list)
for material in recipe['materials']:
    aliases[material['prepared_material_name'].rsplit(':',1)[-1]].append(material)
assert all(len(v)==1 for v in aliases.values()),'namespace_suffix_collision'
bindings = []
for slot in native['slots']:
    found = aliases.get(slot['imported_name'])
    assert found and len(found)==1,('no_exact_unique_alias',slot)
    material = found[0]
    expected = counts[material['prepared_material_name']]
    actual = sections['polygon_group_triangles'][str(slot['slot'])]
    assert expected == actual,('source_native_section_triangles_differ',material['source_material'],expected,actual)
    bindings.append({'native_slot':slot['slot'],'native_imported_name':slot['imported_name'],'recipe_slot':material['slot'],
                     'source_material':material['source_material'],'prepared_material':material['prepared_material_name'],
                     'source_triangles':expected,'native_triangles':actual})
assert sum(counts.values()) == sections['triangle_count']
assert sha(job['prepared_blend']) == recipe['prepared_blend_sha256'] and sha(job['source_fbx']) == job['sha256']
result={'schema':'environmentpipeline.h0017_exact_material_alias_proof.v1','passed':True,'source_blend':job['prepared_blend'],
        'source_blend_sha256':recipe['prepared_blend_sha256'],'source_fbx':job['source_fbx'],'source_fbx_sha256':job['sha256'],
        'rule':'Unique exact source namespace suffix equals actual Unreal imported material name; complete per-material triangulated source usage equals native polygon-group usage.',
        'alias_collisions':[],'bindings':bindings,'source_objects':objects,'total_triangles':sum(counts.values()),
        'source_files_saved_or_geometry_changed':False,'native_operations':False}
out=HERE/'H0017_SOURCE_MATERIAL_PROOF.json'
assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'sections':len(bindings),'triangles':sum(counts.values()),'sha256':sha(out)}))
