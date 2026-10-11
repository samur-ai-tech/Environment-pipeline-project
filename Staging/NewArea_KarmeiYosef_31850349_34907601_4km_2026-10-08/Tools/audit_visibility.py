"""In-editor, read-only (Karmei Yosef operator), 2026-10-09. Why can plants/trees vanish at distance? Per mesh component on
the loaded map: owner, instance count, instance cull distances, max draw distances, mesh Nanite + shape preservation,
mesh LOD count and screen sizes. Also World Partition presence and building storage. Writes receipts/VISIBILITY_AUDIT.json.
ARGS: expected_pid."""
import json, os
from collections import defaultdict
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
meshes = {}


def mesh_info(m):
    p = m.get_path_name().split('.')[0]
    if p not in meshes:
        s = m.get_editor_property('nanite_settings')
        info = {'nanite': bool(s.enabled), 'shape': str(getattr(s, 'shape_preservation', '?')).split('.')[-1].split(':')[0],
                'lods': sms.get_lod_count(m), 'tris_lod0': None}
        try:
            info['tris_lod0'] = m.get_num_triangles(0)
        except Exception:
            pass
        try:
            info['min_lod'] = str(m.get_editor_property('min_lod'))
        except Exception:
            pass
        meshes[p] = info
    return p


rows = []
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(u.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if not m:
            continue
        r = {'owner': a.get_actor_label(), 'owner_class': a.get_class().get_name(), 'comp_class': c.get_class().get_name(),
             'mesh': mesh_info(m), 'instances': c.get_instance_count() if isinstance(c, u.InstancedStaticMeshComponent) else 1,
             'ld_max_draw': c.get_editor_property('ld_max_draw_distance'), 'min_draw': c.get_editor_property('min_draw_distance')}
        if isinstance(c, u.InstancedStaticMeshComponent):
            r['cull'] = [c.get_editor_property('instance_start_cull_distance'), c.get_editor_property('instance_end_cull_distance')]
        rows.append(r)
# summarise
by_owner = defaultdict(lambda: {'components': 0, 'instances': 0, 'culled_components': 0, 'drawdist_components': 0, 'meshes': set()})
for r in rows:
    k = r['owner_class'] + ':' + (r['owner'] if r['owner_class'] != 'Actor' else r['owner'].split('_')[0])
    s = by_owner[k]
    s['components'] += 1; s['instances'] += r['instances']; s['meshes'].add(r['mesh'])
    if r.get('cull') and r['cull'][1] > 0:
        s['culled_components'] += 1
    if r['ld_max_draw'] > 0 or r['min_draw'] > 0:
        s['drawdist_components'] += 1
summary = {k: {**v, 'meshes': len(v['meshes'])} for k, v in by_owner.items()}
culled = [r for r in rows if (r.get('cull') and r['cull'][1] > 0) or r['ld_max_draw'] > 0 or r['min_draw'] > 0]
non_nanite_used = sorted({r['mesh'] for r in rows if not meshes[r['mesh']]['nanite']})
nanite_no_preserve = sorted({r['mesh'] for r in rows if meshes[r['mesh']]['nanite'] and meshes[r['mesh']]['shape'] in ('NONE', '?')})
ext = ROOT / 'Content/__ExternalActors__'
out = {'world': world.get_path_name(), 'components': len(rows), 'instances': sum(r['instances'] for r in rows),
       'external_actors_folder_exists': ext.exists(), 'summary_by_owner': summary,
       'components_with_cull_or_drawdistance': culled[:200], 'count_with_cull_or_drawdistance': len(culled),
       'non_nanite_meshes_used': {p: meshes[p] for p in non_nanite_used},
       'nanite_meshes_without_preserve_area': len(nanite_no_preserve), 'nanite_no_preserve_sample': nanite_no_preserve[:60],
       'mesh_count': len(meshes)}
(TASK / 'receipts' / 'VISIBILITY_AUDIT.json').write_text(json.dumps(out, indent=1, default=str), encoding='utf-8')
RESULT = {'ok': True, 'components': out['components'], 'instances': out['instances'], 'summary': summary,
          'count_with_cull_or_drawdistance': len(culled), 'non_nanite_count': len(non_nanite_used),
          'nanite_no_preserve': len(nanite_no_preserve), 'mesh_count': len(meshes)}
