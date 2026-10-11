"""In-editor (diagnosis only, Karmei Yosef operator): show only / hide PCG ISM components by mesh-name substring, or show all.
Visibility is restored with mode 'all' before any save. ARGS: expected_pid, mode ('hide'|'only'|'all'), names [substrings]."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
vol = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)][0]
mode, names = ARGS['mode'], ARGS.get('names', [])
hidden = []
for c in vol.get_components_by_class(u.InstancedStaticMeshComponent):
    m = c.get_editor_property('static_mesh'); n = m.get_name() if m else ''
    hit = any(s in n for s in names)
    vis = True if mode == 'all' else (not hit if mode == 'hide' else hit)
    c.set_visibility(vis, False)
    if not vis:
        hidden.append(n)
RESULT = {'ok': True, 'hidden': sorted(set(hidden))}
