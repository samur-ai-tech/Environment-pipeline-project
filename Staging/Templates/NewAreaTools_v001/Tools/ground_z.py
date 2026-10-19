"""In-editor, read-only (Karmei Yosef operator, 2026-10-11): landscape height (cm) at ARGS.points [[x, y], ...] in UE cm,
landscape-only hits (None elsewhere). Used to place capture cameras. ARGS: expected_pid, points."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
out = []
for x, y in ARGS['points']:
    hits = u.SystemLibrary.line_trace_multi(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0), u.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                            False, [], u.DrawDebugTrace.NONE, True)
    z = None
    for h in (hits[1] if isinstance(hits, tuple) else hits) or []:
        t = h.to_tuple()
        if t[0] and isinstance(t[9], (u.Landscape, u.LandscapeProxy)):
            z = round(t[4].z, 1); break
    out.append(z)
RESULT = {'ok': True, 'z': out}
