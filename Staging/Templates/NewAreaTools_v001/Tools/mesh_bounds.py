"""In-editor, read-only: local bounding boxes (cm) of ARGS.meshes. ARGS: expected_pid, meshes."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
out = {}
for p in ARGS['meshes']:
    m = u.load_asset(p); b = m.get_bounding_box()
    out[p] = [[b.min.x, b.min.y, b.min.z], [b.max.x, b.max.y, b.max.z]]
RESULT = {'ok': True, 'bounds': out}
