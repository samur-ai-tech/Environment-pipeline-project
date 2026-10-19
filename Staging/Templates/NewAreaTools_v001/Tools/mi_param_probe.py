"""In-editor, read-only. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Scalar / vector / texture parameter names and
values of ARGS.materials (material instances). Static switches are NOT read (reading them marks an MI dirty).
ARGS: expected_pid, materials (list of paths)."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
L = u.MaterialEditingLibrary
out = {}
for path in ARGS['materials']:
    mi = u.load_asset(path)
    r = {'parent': mi.get_editor_property('parent').get_path_name() if isinstance(mi, u.MaterialInstance) else None}
    r['scalars'] = {str(n): round(L.get_material_instance_scalar_parameter_value(mi, n), 4) for n in L.get_scalar_parameter_names(mi)}
    r['vectors'] = {str(n): str(L.get_material_instance_vector_parameter_value(mi, n)).split(' address')[0][:80] for n in L.get_vector_parameter_names(mi)}
    r['textures'] = {str(n): (L.get_material_instance_texture_parameter_value(mi, n).get_path_name() if L.get_material_instance_texture_parameter_value(mi, n) else None)
                     for n in L.get_texture_parameter_names(mi)}
    out[path] = r
RESULT = {'ok': True, 'materials': out,
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
