"""In-editor, read-only: LOD-editing functions available on StaticMeshEditorSubsystem / StaticMesh in this build."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
s = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
names = [n for n in dir(s) if 'lod' in n.lower()]
docs = {n: (getattr(s, n).__doc__ or '').splitlines()[0][:160] for n in names}
RESULT = {'ok': True, 'subsystem': docs}
