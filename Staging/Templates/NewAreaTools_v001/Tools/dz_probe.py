"""In-editor, read-only (Karmei Yosef operator, 2026-10-11): landscape height minus instance height for a sample of the
instances of the actors in ARGS.labels (landscape-only hits). Shows whether imported actors still sit on the regenerated
landscape. No changes. ARGS: expected_pid, labels, every (sample step, default 10)."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)


def land_z(x, y):
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0), u.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                            False, [], u.DrawDebugTrace.NONE, True)
    h = hit[1] if isinstance(hit, tuple) else hit
    t = h.to_tuple() if h is not None else None
    if not t or not t[0] or not isinstance(t[9], (u.Landscape, u.LandscapeProxy)):
        return None
    return t[4].z


out = {}
for lab in ARGS['labels']:
    a = [x for x in eas.get_all_level_actors() if x.get_actor_label() == lab][0]
    d = []
    for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
        for i in range(0, c.get_instance_count(), int(ARGS.get('every', 10))):
            t = c.get_instance_transform(i, True).translation
            z = land_z(t.x, t.y)
            if z is not None:
                d.append(round(z - t.z, 1))
    d.sort()
    out[lab] = {'n': len(d), 'min': d[0] if d else None, 'median': d[len(d) // 2] if d else None, 'max': d[-1] if d else None}
RESULT = {'ok': True, 'land_minus_instance_cm': out}
