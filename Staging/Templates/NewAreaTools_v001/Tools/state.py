"""In-editor, read-only: loaded world and dirty packages. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
w = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
RESULT = {'ok': True, 'world': w.get_path_name() if w else None,
          'dirty_maps': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())[:30]}
