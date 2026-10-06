"""Targeted geometry readback for three actual native import count differences."""
import bpy,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
jobs={j['asset_id']:j for j in json.loads((HERE/'EXTERNAL_IMPORT_QUEUE.json').read_text())}
out={}
for aid in ['external.H0045','external.H0056','external.T1028']:
    job=jobs[aid]
    bpy.ops.wm.open_mainfile(filepath=job['prepared_blend'],load_ui=False,use_scripts=False)
    rows=[]
    source=json.loads(Path(job['original_source_receipt']).read_text())
    for entry in source['objects']:
        if not entry['geometry_role'].startswith('render'):continue
        obj=bpy.data.objects.get(entry['name']);assert obj
        mesh=obj.data;mesh.calc_loop_triangles()
        vertices=[list((obj.matrix_world@v.co)*(100*bpy.context.scene.unit_settings.scale_length)) for v in mesh.vertices]
        triangles=[list(t.vertices) for t in mesh.loop_triangles]
        rows.append({'name':entry['name'],'vertices_cm':vertices,'triangles':triangles})
    out[aid]=rows
(HERE/'SOURCE_TRIANGLE_GEOMETRY.json').write_text(json.dumps(out))
print('Targeted source triangle readback saved; sources unchanged')
