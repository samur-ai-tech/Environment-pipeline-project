"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Area-owned material-instance copy with MI parameter values
(no material-graph edit, no recompile; the vendor MI is only read). Creates ARGS.dest from ARGS.source once (refuses a
dest outside this area's Materials folder), then sets ARGS.scalars {name: value} and ARGS.vectors {name: [r, g, b, a]}.
No save here (save_prefix.py). ARGS: expected_pid, script_file (client), source, dest, scalars (optional), vectors (optional)."""
import os
import importlib.util
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
AREA_MATS = A.AREA_MATERIALS + '/'
src, dst = ARGS['source'], ARGS['dest']
assert dst.startswith(AREA_MATS), dst
L = u.MaterialEditingLibrary
created = False
if not u.EditorAssetLibrary.does_asset_exist(dst):
    assert u.EditorAssetLibrary.duplicate_asset(src, dst), 'duplicate failed'
    created = True
mi = u.load_asset(dst)
names_s = [str(n) for n in L.get_scalar_parameter_names(mi)]
names_v = [str(n) for n in L.get_vector_parameter_names(mi)]
for n, v in (ARGS.get('scalars') or {}).items():
    assert n in names_s, (n, names_s)
    L.set_material_instance_scalar_parameter_value(mi, n, float(v))
for n, v in (ARGS.get('vectors') or {}).items():
    assert n in names_v, (n, names_v)
    L.set_material_instance_vector_parameter_value(mi, n, u.LinearColor(*[float(x) for x in v]))
L.update_material_instance(mi)
RESULT = {'ok': True, 'dest': dst, 'created': created, 'parent': mi.get_editor_property('parent').get_path_name(),
          'scalars': {n: round(L.get_material_instance_scalar_parameter_value(mi, n), 4) for n in (ARGS.get('scalars') or {})},
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
