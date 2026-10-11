"""In-editor (Karmei Yosef operator): force-generate the trial volume. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
vol = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)][0]
vol.get_component_by_class(u.PCGComponent).generate_local(True)
RESULT = {'ok': True}
