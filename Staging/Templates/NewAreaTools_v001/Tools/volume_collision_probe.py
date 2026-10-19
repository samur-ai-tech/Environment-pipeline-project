"""In-editor, read-only: collision of every Volume/Brush actor (PCG volume etc.): object type, enabled, responses. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
out = {}
for a in eas.get_all_level_actors():
    if isinstance(a, u.Brush) or 'Volume' in a.get_class().get_name():
        for c in a.get_components_by_class(u.PrimitiveComponent):
            resp = {}
            for ch in ('ECC_VISIBILITY', 'ECC_CAMERA', 'ECC_WORLD_STATIC', 'ECC_WORLD_DYNAMIC', 'ECC_PAWN', 'ECC_PHYSICS_BODY', 'ECC_VEHICLE'):
                resp[ch[4:]] = str(c.get_collision_response_to_channel(getattr(u.CollisionChannel, ch))).split('.')[-1].split(':')[0]
            b = a.get_actor_bounds(False)
            out[a.get_actor_label() + '/' + c.get_name()] = {'class': a.get_class().get_name(), 'enabled': str(c.get_collision_enabled()).split('.')[-1].split(':')[0],
                'object_type': str(c.get_collision_object_type()).split('.')[-1].split(':')[0], 'profile': str(c.get_collision_profile_name()),
                'responses': resp, 'bounds_z_cm': [round(b[0].z - b[1].z), round(b[0].z + b[1].z)]}
RESULT = {'ok': True, **out}
