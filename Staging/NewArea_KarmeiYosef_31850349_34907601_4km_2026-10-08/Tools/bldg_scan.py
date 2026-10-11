"""In-editor, read-only: Bldg_ actors' components without an attach parent (other than the actor root). ARGS: expected_pid."""
import os
from collections import Counter
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
det = Counter(); tot = Counter(); ex = []
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('Bldg_'):
        continue
    root = a.root_component
    for c in a.get_components_by_class(u.SceneComponent):
        if c == root:
            continue
        key = c.get_class().get_name() + ':' + c.get_name().split('_')[0] + ('_win' if 'windows' in c.get_name() else '')
        tot[key] += 1
        if c.get_attach_parent() is None:
            det[key] += 1
            if len(ex) < 5:
                ex.append([a.get_actor_label(), c.get_name(), str(c.get_editor_property('mobility'))])
RESULT = {'ok': True, 'detached': dict(det), 'total': dict(tot), 'examples': ex}
