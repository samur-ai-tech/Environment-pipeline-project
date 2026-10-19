"""In-editor, read-only (Karmei Yosef operator, 2026-10-11): what does a capture pixel show? Casts a multi line trace from
ARGS.eye along the view ray through pixel ARGS.px (image ARGS.size, horizontal FOV ARGS.fov, camera aimed at ARGS.target)
and lists every hit (actor label/class, component, mesh, material of the hit section, distance). Also lists landscape
hits only. No changes. ARGS: expected_pid, eye, target, px [x, y], size [w, h], fov (default 90), length_cm."""
import math, os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
E, T = ARGS['eye'], ARGS['target']
dx, dy, dz = (T[i] - E[i] for i in range(3)); yaw = math.atan2(dy, dx); pitch = math.atan2(dz, math.hypot(dx, dy))
F = (math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))
R = (-math.sin(yaw), math.cos(yaw), 0.0)
U = (-math.sin(pitch) * math.cos(yaw), -math.sin(pitch) * math.sin(yaw), math.cos(pitch))
w, h = ARGS['size']; f = (w / 2) / math.tan(math.radians(ARGS.get('fov', 90.0)) / 2)
px, py = ARGS['px']; a, b = px - w / 2, -(py - h / 2)
d = [f * F[i] + a * R[i] + b * U[i] for i in range(3)]; n = math.sqrt(sum(x * x for x in d)); d = [x / n for x in d]
L = ARGS.get('length_cm', 600000.0)
end = u.Vector(E[0] + d[0] * L, E[1] + d[1] * L, E[2] + d[2] * L)
hits = u.SystemLibrary.line_trace_multi(world, u.Vector(*E), end, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], u.DrawDebugTrace.NONE, True)
out = []
for hh in (hits[1] if isinstance(hits, tuple) else hits) or []:
    t = hh.to_tuple()
    act, comp = t[9], t[10]
    mesh = None
    try:
        mesh = comp.get_editor_property('static_mesh').get_path_name().split('.')[0]
    except Exception:
        pass
    out.append({'actor': act.get_actor_label() if act else None, 'class': act.get_class().get_name() if act else None,
                'component': comp.get_name() if comp else None, 'mesh': mesh, 'dist_m': round(t[3] / 100.0, 1) if isinstance(t[3], float) else None,
                'loc': [round(t[4].x), round(t[4].y), round(t[4].z)]})
RESULT = {'ok': True, 'dir': [round(x, 4) for x in d], 'hits': out[:12]}
