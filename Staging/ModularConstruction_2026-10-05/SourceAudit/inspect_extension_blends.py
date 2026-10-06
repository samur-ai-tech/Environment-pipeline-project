import bpy, json, pathlib
from mathutils import Vector
BASE = pathlib.Path(r'C:\Users\USER\Documents\Pipeline Environment\ModelBank\Modular_2026-10-04\WholeBuildingConversions')
OUT = pathlib.Path(__file__).parent
summary = []
for ep in sorted(BASE.glob('*/ExtensionBand/EXTENSION.json')):
    e = json.loads(ep.read_text(encoding='utf-8-sig'))
    bpy.ops.wm.open_mainfile(filepath=e['blend'], load_ui=False)
    objects = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        coords = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
        objects.append({'name':ob.name, 'data':ob.data.name,
                        'hide_render':ob.hide_render, 'hide_viewport':ob.hide_viewport,
                        'world_min':[min(v[i] for v in coords) for i in range(3)],
                        'world_max':[max(v[i] for v in coords) for i in range(3)],
                        'matrix_world':[list(row) for row in ob.matrix_world],
                        'vertices':len(ob.data.vertices), 'polygons':len(ob.data.polygons),
                        'uv_layers':[uv.name for uv in ob.data.uv_layers],
                        'material_slots':[s.material.name if s.material else None for s in ob.material_slots]})
    summary.append({'id':e['id'],'objects':objects,'extension':e})
(OUT/'EXTENSION_BLEND_OBJECTS.json').write_text(json.dumps(summary, indent=2),encoding='utf-8')
print(json.dumps([{'id':f['id'], 'objects':[o['name'] for o in f['objects']]} for f in summary],indent=2))
