"""In-editor, read-only: class and height of a few assets. ARGS: expected_pid, paths."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
r = {}
for p in ARGS['paths']:
    a = u.load_asset(p)
    if a is None:
        r[p] = None; continue
    h = None
    if isinstance(a, u.StaticMesh):
        b = a.get_bounding_box(); h = round((b.max.z - b.min.z) / 100, 2)
    r[p.split('/')[-1]] = [a.get_class().get_name(), h]
RESULT = {'ok': True, 'r': r}
