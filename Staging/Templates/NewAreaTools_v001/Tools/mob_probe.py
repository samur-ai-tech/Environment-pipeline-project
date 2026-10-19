"""In-editor, read-only: mobility and parent of every scene component of the named actors. ARGS: expected_pid, labels."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
out = {}
for lab in ARGS['labels']:
    a = [x for x in eas.get_all_level_actors() if x.get_actor_label() == lab][0]
    out[lab] = [[c.get_name(), c.get_class().get_name(), str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0],
                 c.get_attach_parent().get_name() if c.get_attach_parent() else None] for c in a.get_components_by_class(u.SceneComponent)]
RESULT = {'ok': True, **out}
