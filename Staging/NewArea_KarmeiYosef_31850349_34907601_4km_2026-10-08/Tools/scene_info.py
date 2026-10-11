"""In-editor, read-only (Karmei Yosef operator): landscape bounds and bounds of baked actors by name group, for cameras.
ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
def b(a):
    o, e = a.get_actor_bounds(False)
    return {'origin': [o.x, o.y, o.z], 'extent': [e.x, e.y, e.z]}
land = [b(a) for a in actors if isinstance(a, u.Landscape)]
groups = {}
for a in actors:
    label = a.get_actor_label()
    for key in ('buildings', 'road_surfaces', 'sidewalks', 'street_details', 'Instancer', 'instanc'):
        if key.lower() in label.lower():
            groups.setdefault(key, []).append({'label': label, **b(a)})
            break
labels = sorted({a.get_actor_label() for a in actors})[:80]
RESULT = {'ok': True, 'landscape': land, 'groups': {k: v[:6] for k, v in groups.items()}, 'group_counts': {k: len(v) for k, v in groups.items()}, 'labels_sample': labels}
