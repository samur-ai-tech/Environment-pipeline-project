"""In-editor, read-only diagnostics for the first rebuilt shell. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
m = u.load_asset('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/Buildings/Shells/SM_Shell_1040458071')
out = {'doc_build': (u.StaticMesh.build_from_static_mesh_descriptions.__doc__ or '')[:900],
       'lods': sms.get_lod_count(m), 'tris': m.get_num_triangles(0),
       'slots': [(str(s.get_editor_property('material_slot_name')), s.get_editor_property('material_interface').get_name() if s.get_editor_property('material_interface') else None) for s in m.get_editor_property('static_materials')]}
try:
    out['build_settings'] = str(sms.get_lod_build_settings(m, 0))[:400]
except Exception as e:
    out['bs_err'] = repr(e)[:200]
try:
    d = m.get_static_mesh_description(0); out['desc_counts'] = [d.get_vertex_count(), d.get_polygon_count()]
except Exception as e:
    out['desc_err'] = repr(e)[:200]
RESULT = {'ok': True, **out}
