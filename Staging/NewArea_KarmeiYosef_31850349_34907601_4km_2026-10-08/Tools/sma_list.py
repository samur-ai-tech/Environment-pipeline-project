"""In-editor, read-only: every StaticMeshActor's label, mesh and folder. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
RESULT = {'ok': True, 'actors': [[a.get_actor_label(), a.get_name(), str(a.get_folder_path()),
          (a.static_mesh_component.get_editor_property('static_mesh').get_path_name().split('.')[0] if a.static_mesh_component.get_editor_property('static_mesh') else None)]
          for a in eas.get_all_level_actors() if isinstance(a, u.StaticMeshActor)]}
