"""In-editor, read-only: HLOD layer and spatial-loading flags per actor group (incl. PCG partition actors)."""
import os
from collections import Counter
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
c = Counter()
for a in eas.get_all_level_actors():
    lab = a.get_actor_label(); cls = a.get_class().get_name()
    g = 'building' if lab.startswith('Bldg_') else 'bank' if lab.startswith('bank_instances') else 'pazfarm' if lab.startswith('PazFarm_') else cls
    try:
        l = a.get_editor_property('hlod_layer'); ln = l.get_name() if l else None
    except Exception:
        ln = 'n/a'
    try:
        sp = bool(a.get_editor_property('is_spatially_loaded'))
    except Exception:
        sp = 'n/a'
    c[(g, ln, sp)] += 1
RESULT = {'ok': True, 'groups': {'%s | layer=%s | spatial=%s' % k: v for k, v in sorted(c.items(), key=lambda x: -x[1])}}
