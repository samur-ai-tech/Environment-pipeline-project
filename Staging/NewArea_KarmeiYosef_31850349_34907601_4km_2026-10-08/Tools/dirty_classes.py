"""In-editor, read-only: dirty packages grouped by the class/label of the actor they hold (World Partition external actors)."""
import os
from collections import Counter
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
dirty = {x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()} | {x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
c = Counter(); seen = set()
for a in eas.get_all_level_actors():
    p = a.get_package().get_path_name() if hasattr(a, 'get_package') else a.get_outermost().get_path_name()
    if p in dirty:
        lab = a.get_actor_label()
        c[a.get_class().get_name() + (':Bldg' if lab.startswith('Bldg_') else '')] += 1; seen.add(p)
other = sorted(dirty - seen)
RESULT = {'ok': True, 'dirty_total': len(dirty), 'by_class': dict(c), 'other': other[:15], 'n_other': len(other)}
