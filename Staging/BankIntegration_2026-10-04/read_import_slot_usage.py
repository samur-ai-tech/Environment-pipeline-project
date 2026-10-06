"""Read used material slots for lossless source-to-native import mapping."""
import bpy
import collections
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
jobs=json.loads((HERE/'EXTERNAL_IMPORT_QUEUE.json').read_text())
out={}
for job in jobs:
    path=Path(job['prepared_blend']); before=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    assert len(meshes)==1
    obj=meshes[0];counts=collections.Counter(p.material_index for p in obj.data.polygons)
    out[job['asset_id']]={'source':str(path),'sha256':before,'used_slots':sorted(counts),
        'slots':[{'index':i,'material':s.material.name if s.material else None,'polygons':counts[i]} for i,s in enumerate(obj.material_slots)]}
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    (HERE/'SOURCE_IMPORT_SLOT_USAGE.json').write_text(json.dumps(out,indent=2)+'\n')
print('Material slot use read for',len(out),'sources; no source changes')
