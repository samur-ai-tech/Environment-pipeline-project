"""In-editor, read-only: what line_trace_single returns here, at the Paz Farm pin. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
ignore = [a for a in eas.get_all_level_actors() if not isinstance(a, (u.Landscape, u.LandscapeProxy))]
r = u.SystemLibrary.line_trace_single(world, u.Vector(-12690, -10640, 60000.0), u.Vector(-12690, -10640, -20000.0),
                                      u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, u.DrawDebugTrace.NONE, True)
info = {'type': type(r).__name__}
h = r[1] if isinstance(r, tuple) else r
info['ok_flag'] = r[0] if isinstance(r, tuple) else None
try:
    t = h.to_tuple(); info['tuple_len'] = len(t); info['t0_4'] = [str(x)[:80] for x in t[:6]]
except Exception as exc:
    info['to_tuple_err'] = repr(exc)[:120]
RESULT = {'ok': True, **info}
