"""In-editor, read-only: 'obj dump' the runtime hash set object (and its subobjects) into the log. ARGS: expected_pid, path."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world, 'obj dump ' + ARGS['path'] + ' recurse')
RESULT = {'ok': True}
