"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69) (playbook 10c). After road_uv_fix.py set use_full_precision_u_vs on the baked
road mesh, the rendered UVs still looked quantised, so the render data was not rebuilt. This step rebuilds this area's
road_surfaces mesh (area_constants.py ROAD_MESH) from its own mesh description (full build, which honours the LOD0 build settings), keeps its material
slots and restores its collision trace flag, then reports triangles, UV range sample and dirty packages. The backup made
by road_uv_fix.py (../Before/) is the undo. No save here. ARGS: expected_pid, script_file (client)."""
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
assert sub.get_lod_build_settings(m, 0).get_editor_property('use_full_precision_u_vs') is True
mats = [(s.get_editor_property('material_slot_name'), s.get_editor_property('material_interface')) for s in m.get_editor_property('static_materials')]
bs = m.get_editor_property('body_setup')
trace = bs.get_editor_property('collision_trace_flag') if bs else None
tri_before = m.get_num_triangles(0)
d = m.get_static_mesh_description(0)
m.build_from_static_mesh_descriptions([d], False, False)          # full build (not fast): honours the LOD build settings
mats_after = [(s.get_editor_property('material_slot_name'), s.get_editor_property('material_interface')) for s in m.get_editor_property('static_materials')]
if mats_after != mats:
    m.set_editor_property('static_materials', [u.StaticMaterial(material_interface=i, material_slot_name=n) for n, i in mats])
bs2 = m.get_editor_property('body_setup')
if trace is not None and bs2:
    bs2.set_editor_property('collision_trace_flag', trace)
RESULT = {'ok': m.get_num_triangles(0) == tri_before, 'triangles_before': tri_before, 'triangles_after': m.get_num_triangles(0),
          'full_precision_uvs': sub.get_lod_build_settings(m, 0).get_editor_property('use_full_precision_u_vs'),
          'materials_kept': [str(n) for n, _ in mats], 'materials_reset': mats_after != mats,
          'collision_trace_flag': str(trace), 'collision_trace_flag_after': str(bs2.get_editor_property('collision_trace_flag')) if bs2 else None,
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
