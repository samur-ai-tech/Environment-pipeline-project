import bpy, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
job=next(j for j in json.loads((HERE/'EXTERNAL_IMPORT_QUEUE.json').read_text()) if j['asset_id']=='external.H0045')
out={}
for kind,path in [('prepared',job['prepared_blend']),('fbx',job['source_fbx'])]:
    if kind=='prepared':bpy.ops.wm.open_mainfile(filepath=path,load_ui=False,use_scripts=False)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=path)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    records=[]
    for obj in meshes:
        obj.data.calc_loop_triangles()
        areas=[t.area for t in obj.data.loop_triangles]
        records.append({'object':obj.name,'triangles':len(areas),'area_zero':sum(a==0 for a in areas),'area_below_1e_12':sum(a<1e-12 for a in areas)})
    out[kind]=records
(HERE/'H0045_TRIANGLE_DIAGNOSIS.json').write_text(json.dumps(out,indent=2))
print(out)
