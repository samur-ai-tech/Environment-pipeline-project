"""In-editor, read-only (2026-10-12): collision facts of the baked road/sidewalk meshes. Per mesh: sections and whether each
has collision enabled, body setup flags, and a component-only complex trace at sample points (ARGS.points, UE cm) plus the
mesh vertex height nearest each point (from LOD0 mesh description). ARGS: expected_pid, points."""
import os, math
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
out = {}
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if not (isinstance(a, u.StaticMeshActor) and ('road_surfaces' in lab or 'sidewalks' in lab)):
        continue
    c = a.static_mesh_component; m = c.get_editor_property('static_mesh')
    n = sms.get_number_materials(m) if hasattr(sms, 'get_number_materials') else None
    secs = []
    for s in range(64):
        try:
            secs.append(bool(sms.is_section_collision_enabled(m, 0, s)))
        except Exception:
            break
    bs = m.get_editor_property('body_setup')
    rec = {'sections_collision': secs, 'num_sections': len(secs),
           'body_setup': {k: str(bs.get_editor_property(k)) for k in ('collision_trace_flag', 'double_sided_geometry')} if bs else None,
           'never_needs_cooked_collision': None,
           'traces': []}
    d = m.get_static_mesh_description(0)
    nv = d.get_vertex_count()
    pts = [d.get_vertex_position(u.VertexID(i)) for i in range(0, nv, max(1, nv // 200000))]
    for x, y in ARGS['points']:
        hit = c.line_trace_component(u.Vector(x, y, 80000.0), u.Vector(x, y, -30000.0), True, False, False)
        ok = hit[0] if isinstance(hit, tuple) else hit
        near = min(pts, key=lambda p: (p.x - x) ** 2 + (p.y - y) ** 2)
        rec['traces'].append({'xy': [x, y], 'component_trace_hit': bool(ok), 'hit_z': round(hit[1].z, 1) if isinstance(hit, tuple) and ok else None,
                              'nearest_vertex': [round(near.x), round(near.y), round(near.z, 1)], 'nearest_dist_cm': round(math.hypot(near.x - x, near.y - y))})
    rec['vertices'] = nv
    out[lab] = rec
RESULT = {'ok': True, **out}
