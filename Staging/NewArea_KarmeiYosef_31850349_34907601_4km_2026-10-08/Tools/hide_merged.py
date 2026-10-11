"""In-editor (diagnosis, trial only): temporarily hide/show the merged buildings shell actor in the editor view. ARGS: expected_pid, hide."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
m = [a for a in eas.get_all_level_actors() if a.get_actor_label().endswith('_buildings') and isinstance(a, u.StaticMeshActor)]
for a in m:
    a.set_is_temporarily_hidden_in_editor(bool(ARGS['hide']))
RESULT = {'ok': True, 'actors': [a.get_actor_label() for a in m], 'hidden': bool(ARGS['hide'])}
