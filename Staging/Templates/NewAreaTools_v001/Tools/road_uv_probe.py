"""In-editor, read-only. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). LOD0 build settings of this area's baked road mesh
(full-precision UVs?) and the UV0 range of a sample of its vertex instances. ARGS: expected_pid, script_file (client)."""
import os
import importlib.util
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
MESH = A.ROAD_MESH
m = u.load_asset(MESH)
sub = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
bs = sub.get_lod_build_settings(m, 0)
keys = ('use_full_precision_u_vs', 'use_high_precision_tangent_basis', 'recompute_normals', 'recompute_tangents', 'remove_degenerates',
        'generate_lightmap_u_vs')
settings = {k: bs.get_editor_property(k) for k in keys}
d = m.get_static_mesh_description(0)
n = d.get_vertex_instance_count()
us, vs = [], []
step = max(1, n // 4000)
for i in range(0, n, step):
    uv = d.get_vertex_instance_uv(u.VertexInstanceID(i), 0)
    us.append(uv.x); vs.append(uv.y)
RESULT = {'ok': True, 'mesh': MESH, 'build_settings_lod0': settings, 'vertex_instances': n, 'sampled': len(us),
          'uv0_u_range': [min(us), max(us)], 'uv0_v_range': [min(vs), max(vs)],
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
