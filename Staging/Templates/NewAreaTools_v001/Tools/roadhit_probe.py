"""In-editor, read-only (2026-10-12): why world traces miss the baked road mesh. For the road/sidewalk actors: actor-level
collision, component responses to Visibility/Camera/WorldStatic/Vehicle-relevant channels, physics state; then world traces at
ARGS.points with several settings. ARGS: expected_pid, points."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
out = {}
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if isinstance(a, u.StaticMeshActor) and ('road_surfaces' in lab or 'sidewalks' in lab):
        c = a.static_mesh_component
        resp = {}
        for ch in ('ECC_VISIBILITY', 'ECC_CAMERA', 'ECC_WORLD_STATIC', 'ECC_WORLD_DYNAMIC', 'ECC_PAWN', 'ECC_PHYSICS_BODY', 'ECC_VEHICLE'):
            try:
                resp[ch] = str(c.get_collision_response_to_channel(getattr(u.CollisionChannel, ch)))
            except Exception as exc:
                resp[ch] = 'n/a ' + type(exc).__name__
        out[lab] = {'actor_enable_collision': a.get_actor_enable_collision(), 'hidden_in_game': a.get_editor_property('hidden'),
                    'collision_enabled': str(c.get_collision_enabled()), 'object_type': str(c.get_collision_object_type()), 'responses': resp,
                    'generate_overlaps': c.get_editor_property('generate_overlap_events')}


def first(x, y, complex_, kind):
    s, e = u.Vector(x, y, 80000.0), u.Vector(x, y, -30000.0)
    if kind == 'single_vis':
        r = u.SystemLibrary.line_trace_single(world, s, e, u.TraceTypeQuery.TRACE_TYPE_QUERY1, complex_, [], u.DrawDebugTrace.NONE, True)
    else:
        r = u.SystemLibrary.line_trace_single_for_objects(world, s, e, [u.ObjectTypeQuery.OBJECT_TYPE_QUERY1], complex_, [], u.DrawDebugTrace.NONE, True)
    h = r[1] if isinstance(r, tuple) else r
    t = h.to_tuple()
    return [t[9].get_actor_label() if t[0] and t[9] else None, round(t[4].z, 1) if t[0] else None]


out['traces'] = []
for x, y in ARGS['points'][:6]:
    out['traces'].append({'xy': [x, y], 'vis_complex': first(x, y, True, 'single_vis'), 'vis_simple': first(x, y, False, 'single_vis'),
                          'worldstatic_complex': first(x, y, True, 'obj'), 'worldstatic_simple': first(x, y, False, 'obj')})
RESULT = {'ok': True, **out}
