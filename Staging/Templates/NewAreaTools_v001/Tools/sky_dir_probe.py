"""In-editor, read-only (2026-10-12): world rotation / forward vector of the sky's DirectionalLight and NorthArrow, with the
sky's Azimuth / CorrectedElevation / NorthOffset readbacks. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
sky = [a for a in eas.get_all_level_actors() if a.get_class().get_name().startswith('BP_EnvironmentSky')][0]
out = {k: sky.get_editor_property(k) for k in ('Azimuth', 'CorrectedElevation', 'NorthOffset', 'TimeOfDay', 'SunElevation')}
for c in sky.get_components_by_class(u.SceneComponent):
    if c.get_name() in ('DirectionalLight', 'NorthArrow', 'MoonLight'):
        r = c.get_world_rotation(); f = c.get_forward_vector()
        out[c.get_name()] = {'pitch': r.pitch, 'yaw': r.yaw, 'roll': r.roll, 'forward': [round(f.x, 4), round(f.y, 4), round(f.z, 4)]}
RESULT = {'ok': True, **out}
