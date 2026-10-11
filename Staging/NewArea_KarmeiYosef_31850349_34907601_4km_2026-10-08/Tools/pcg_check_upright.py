"""In-editor, read-only: max |pitch|/|roll| over sampled PCG instances and WPO flags of the PCG ISM components. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
vol = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)][0]
comp = vol.get_component_by_class(u.PCGComponent)
mp = mr = 0.0; n_total = 0; wpo = set(); comps = 0
for c in vol.get_components_by_class(u.InstancedStaticMeshComponent):
    comps += 1
    n = c.get_instance_count(); n_total += n
    try:
        wpo.add(bool(c.get_editor_property('evaluate_world_position_offset')))
    except Exception as exc:
        wpo.add('n/a')
    for i in range(0, n, max(1, n // 50)):
        r = c.get_instance_transform(i, True).rotation.rotator()
        mp = max(mp, abs(r.pitch)); mr = max(mr, abs(r.roll))
RESULT = {'ok': True, 'generated': comp.get_editor_property('generated'), 'in_progress': comp.get_editor_property('generation_in_progress'),
          'components': comps, 'instances': n_total, 'max_abs_pitch_deg': round(mp, 3), 'max_abs_roll_deg': round(mr, 3), 'wpo_values': sorted(map(str, wpo))}
