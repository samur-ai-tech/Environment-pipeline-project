"""In-editor, read-only: list dirty map/content packages. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
RESULT = {'ok': True, 'maps': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
          'content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
