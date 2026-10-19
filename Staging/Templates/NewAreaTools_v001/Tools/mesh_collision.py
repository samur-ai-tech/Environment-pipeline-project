"""In-editor, read-only. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Simple-collision shape counts and trace flag of
ARGS.meshes (+ the first two shell meshes in <PCG clone folder>/Buildings_v2/Shells). ARGS: expected_pid, script_file (client), meshes."""
import os
import importlib.util
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
eal = u.EditorAssetLibrary
meshes = list(ARGS['meshes'])
shells = [p for p in eal.list_assets(A.TRIAL_ROOT + '/Buildings_v2/Shells', False)][:2]
meshes += [s.split('.')[0] for s in shells]
out = {}
for p in meshes:
    m = u.load_asset(p); bs = m.get_editor_property('body_setup')
    agg = bs.get_editor_property('agg_geom') if bs else None
    n = sum(len(agg.get_editor_property(k)) for k in ('box_elems', 'sphere_elems', 'sphyl_elems', 'convex_elems')) if agg else 0
    out[p.rsplit('/', 1)[1]] = {'simple_shapes': n, 'trace_flag': str(bs.get_editor_property('collision_trace_flag')).split('.')[-1].split(':')[0] if bs else None}
RESULT = {'ok': True, **out}
