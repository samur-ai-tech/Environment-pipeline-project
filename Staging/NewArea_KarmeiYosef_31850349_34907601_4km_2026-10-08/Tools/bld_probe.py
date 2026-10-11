"""In-editor, read-only (Karmei Yosef operator, WP/per-building trial 2026-10-10, map L_..._WPTrial).
1) actors: building-related mesh holders (HoudiniAssetActor-less copy: 68 plain ISM actors + merged buildings mesh actor).
2) mapping check: for sample receipt modules / whole buildings / doors, nearest ISM instance of the same mesh and distance.
3) merged buildings mesh: triangles, sections, material slots, bounds; StaticMeshDescription API availability.
ARGS: expected_pid."""
import json, math, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TR = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/WPTrial'
MAP = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_KarmeiYosef_31850349_34907601_4km_WPTrial'
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAP
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
B = json.loads((TR / 'BUILDINGS_COMPACT.json').read_text(encoding='utf-8'))
ism = {}
merged = None
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if lab.endswith('_buildings') and isinstance(a, u.StaticMeshActor):
        merged = a
    if isinstance(a, u.StaticMeshActor) or a.get_class().get_name() != 'Actor':
        continue
    for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if m:
            ism.setdefault(m.get_path_name().split('.')[0], []).append((a, c))
out = {'ism_meshes': len(ism), 'ism_actors': len({a.get_name() for v in ism.values() for a, c in v})}
samples = B['modules'][:3] + [m for m in B['modules'] if 'Steeldoor' in m['mesh']][:3] + B['whole'][:3] + B['modules'][17000:17003]
checks = []
for s in samples:
    best = None
    for a, c in ism.get(s['mesh'], []):
        for i in range(c.get_instance_count()):
            t = c.get_instance_transform(i, True).translation
            d = math.dist((t.x, t.y, t.z), s['ue'])
            if best is None or d < best[0]:
                best = (d, [round(t.x, 1), round(t.y, 1), round(t.z, 1)], a.get_actor_label())
    checks.append({'mesh': s['mesh'].rsplit('/', 1)[1], 'receipt_ue': s['ue'], 'nearest': best[1] if best else None,
                   'dist_cm': round(best[0], 2) if best else None, 'actor': best[2] if best else None})
out['mapping_checks'] = checks
if merged:
    m = merged.static_mesh_component.get_editor_property('static_mesh')
    sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    b = m.get_bounding_box()
    out['merged'] = {'actor': merged.get_actor_label(), 'mesh': m.get_path_name(), 'tris': m.get_num_triangles(0), 'sections': m.get_num_sections(0),
                     'slots': [str(s.get_editor_property('material_slot_name')) for s in m.get_editor_property('static_materials')],
                     'nanite': bool(m.get_editor_property('nanite_settings').enabled), 'lods': sms.get_lod_count(m),
                     'bounds': [[round(b.min.x), round(b.min.y), round(b.min.z)], [round(b.max.x), round(b.max.y), round(b.max.z)]],
                     'actor_xform': str(merged.get_actor_transform())}
    api = {}
    try:
        d = m.get_static_mesh_description(0)
        api['desc_class'] = d.get_class().get_name()
        api['vertices'] = d.get_vertex_count(); api['triangles'] = d.get_triangle_count(); api['polygon_groups'] = d.get_polygon_group_count()
        names = [n for n in dir(d) if not n.startswith('_')]
        api['methods'] = [n for n in names if any(k in n for k in ('vertex', 'triangle', 'polygon', 'uv', 'normal', 'create', 'material'))][:120]
    except Exception as exc:
        api['error'] = repr(exc)[:300]
    out['mesh_description_api'] = api
RESULT = {'ok': True, **out}
