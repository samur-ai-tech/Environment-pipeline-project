"""Read retained prepared building section counts; no source save or export."""
import collections
import hashlib
import json
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
CAT=HERE/'CategoryBatches/WholeBuildings'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
recipes={r['asset_id']:r for r in read(CAT/'EXTERNAL_MATERIAL_RECIPES.json')}
result={}
for job in read(CAT/'EXTERNAL_IMPORT_QUEUE.json'):
    aid=job['asset_id'];recipe=recipes[aid]
    assert sha(job['prepared_blend'])==recipe['prepared_blend_sha256'] and sha(job['source_fbx'])==job['sha256']
    bpy.ops.wm.open_mainfile(filepath=job['prepared_blend'])
    counts=collections.Counter()
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH' or obj.hide_render:continue
        obj.data.calc_loop_triangles()
        for tri in obj.data.loop_triangles:
            mat=obj.material_slots[tri.material_index].material;assert mat
            counts[mat.name]+=1
    aliases={}
    for material in recipe['materials']:
        name=material['prepared_material_name'];alias=name.rsplit(':',1)[-1]
        assert alias not in aliases,('material_suffix_collision',aid,alias)
        aliases[alias]=name
    assert set(counts)<=set(aliases.values())
    result[aid]={'prepared_blend_sha256':recipe['prepared_blend_sha256'],'source_fbx_sha256':job['sha256'],
                 'material_triangles':dict(counts),'unique_namespace_aliases':aliases,'total_triangles':sum(counts.values()),
                 'source_geometry_changed':False,'native_validation_pending':aid!='external.H0017'}
    assert sha(job['prepared_blend'])==recipe['prepared_blend_sha256'] and sha(job['source_fbx'])==job['sha256']
out=HERE/'WHOLE_SOURCE_MATERIAL_PROOFS.json';assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'families':len(result),'triangles':{k:v['total_triangles'] for k,v in result.items()},'sha256':sha(out)}))
