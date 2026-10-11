"""In-editor, read-only: per component kind, worst distance of building parts from their planned world positions."""
import os, json, math
from collections import defaultdict
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
P = json.loads((ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/receipts/WPTRIAL_BLD_PLAN.json').read_text())
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
worst = defaultdict(float); n = defaultdict(int); ex = {}
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if not lab.startswith('Bldg_'):
        continue
    want = defaultdict(list)
    for p in P['plan'].get(lab[5:], {}).get('parts', []):
        want[p['mesh'].split('.')[0]].append(p['xf'][:3])
    for c in a.get_components_by_class(u.StaticMeshComponent):
        m = c.get_editor_property('static_mesh'); mpth = m.get_path_name().split('.')[0] if m else None
        if mpth not in want:
            continue
        k = ('ISM ' if isinstance(c, u.InstancedStaticMeshComponent) else 'SMC ') + c.get_name().split('_')[0] + ('_win' if 'windows' in c.get_name() else '')
        got = [c.get_instance_transform(i, True).translation for i in range(c.get_instance_count())] if isinstance(c, u.InstancedStaticMeshComponent) else [c.get_world_location()]
        for g in got:
            d = min(math.dist((g.x, g.y, g.z), w) for w in want[mpth]); n[k] += 1
            if d > worst[k]:
                worst[k] = d; ex[k] = [lab, c.get_name(), [round(g.x), round(g.y), round(g.z)], [round(v) for v in min(want[mpth], key=lambda w: math.dist((g.x, g.y, g.z), w))],
                                      str(c.get_editor_property('relative_location'))[:80], c.get_attach_parent().get_name() if c.get_attach_parent() else None]
RESULT = {'ok': True, 'worst_cm': {k: round(v, 2) for k, v in worst.items()}, 'n': dict(n), 'examples': ex}
