"""In-editor, read-only: location of one PCG instance per requested mesh name (nearest to ARGS.near if given),
and write ../cameras_lodcheck.json looking at it from 30/150/400/800 m. ARGS: expected_pid, mesh_names, near."""
import json, math, os
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
TASK = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
vol = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)][0]
nx, ny = ARGS.get('near', [0, 0])
found, cams = {}, {}
for c in vol.get_components_by_class(u.InstancedStaticMeshComponent):
    m = c.get_editor_property('static_mesh')
    if not m or m.get_name() not in ARGS['mesh_names'] or m.get_name() in found:
        continue
    best = None
    for i in range(0, c.get_instance_count(), max(1, c.get_instance_count() // 400)):
        t = c.get_instance_transform(i, True).translation
        d = (t.x - nx) ** 2 + (t.y - ny) ** 2
        if best is None or d < best[0]:
            best = (d, t)
    t = best[1]
    found[m.get_name()] = [t.x, t.y, t.z]
    for dist in (3000, 15000, 40000, 80000):
        cams['%s_%dm' % (m.get_name(), dist // 100)] = {'eye': [t.x - dist * 0.7, t.y - dist * 0.7, t.z + dist * 0.25 + 300], 'target': [t.x, t.y, t.z + 400]}
(TASK / 'cameras_lodcheck.json').write_text(json.dumps(cams, indent=1), encoding='utf-8')
RESULT = {'ok': True, 'found': found, 'cams': len(cams)}
