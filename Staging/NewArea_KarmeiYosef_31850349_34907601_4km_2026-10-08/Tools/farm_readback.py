"""In-editor, read-only: Paz Farm actors after reopen. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors() if a.get_actor_label().startswith('PazFarm_')}
d = acts.get('PazFarm_Detail')
inst = {}
if d:
    for c in d.get_components_by_class(u.InstancedStaticMeshComponent):
        inst[c.get_editor_property('static_mesh').get_name()] = c.get_instance_count()
land = [a for a in eas.get_all_level_actors() if isinstance(a, u.Landscape)][0]
RESULT = {'ok': True, 'actors': sorted(acts), 'detail_instances': inst, 'total': sum(inst.values()),
          'landscape_material': land.get_editor_property('landscape_material').get_path_name(),
          'dirty': [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()] + [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
