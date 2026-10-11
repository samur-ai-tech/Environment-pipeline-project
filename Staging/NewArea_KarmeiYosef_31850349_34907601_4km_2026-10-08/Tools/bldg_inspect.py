"""In-editor, read-only: components of one Bldg_ actor (and one bank prop ISM for comparison). ARGS: expected_pid, label."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
def info(c):
    d = {'class': c.get_class().get_name(), 'name': c.get_name(), 'visible': c.is_visible(), 'hidden_in_game': c.get_editor_property('hidden_in_game'),
         'mobility': str(c.get_editor_property('mobility')), 'world_loc': str(c.get_world_location())[:90]}
    if isinstance(c, u.StaticMeshComponent):
        m = c.get_editor_property('static_mesh'); d['mesh'] = m.get_name() if m else None
        d['mats'] = [x.get_name() if x else None for x in c.get_materials()]
        try:
            o, e = c.get_local_bounds(); d['local_bounds'] = [str(o)[:80], str(e)[:80]]
        except Exception as exc:
            d['local_bounds'] = repr(exc)[:80]
        if isinstance(c, u.InstancedStaticMeshComponent):
            d['n'] = c.get_instance_count()
            if d['n']:
                t = c.get_instance_transform(0, True); d['inst0_world'] = str(t.translation)[:90]
                t2 = c.get_instance_transform(0, False); d['inst0_local'] = str(t2.translation)[:90]
    p = c.get_attach_parent(); d['parent'] = p.get_name() if p else None
    return d
a = [x for x in eas.get_all_level_actors() if x.get_actor_label() == ARGS['label']][0]
out = {'actor_loc': str(a.get_actor_location()), 'root': a.root_component.get_name() if a.root_component else None,
       'comps': [info(c) for c in a.get_components_by_class(u.SceneComponent)]}
b = [x for x in eas.get_all_level_actors() if x.get_actor_label().startswith('bank_instances')][0]
cc = b.get_components_by_class(u.InstancedStaticMeshComponent)
out['bank_ref'] = info(cc[0]) if cc else None
RESULT = {'ok': True, **out}
