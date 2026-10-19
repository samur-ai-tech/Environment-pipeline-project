"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Set scalar parameters on an EXISTING area-owned material instance
(this area's Materials folder only; no graph edit, no recompile, no save). Records old -> new values.
ARGS: expected_pid, script_file (client), mi, scalars {name: value}."""
import os
import importlib.util
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
AREA_MATS = A.AREA_MATERIALS + '/'
assert ARGS['mi'].startswith(AREA_MATS), ARGS['mi']
L = u.MaterialEditingLibrary
mi = u.load_asset(ARGS['mi'])
assert isinstance(mi, u.MaterialInstanceConstant), ARGS['mi']
names = [str(n) for n in L.get_scalar_parameter_names(mi)]
changes = {}
for n, v in ARGS['scalars'].items():
    assert n in names, (n, names)
    old = L.get_material_instance_scalar_parameter_value(mi, n)
    L.set_material_instance_scalar_parameter_value(mi, n, float(v))
    changes[n] = [round(old, 4), round(L.get_material_instance_scalar_parameter_value(mi, n), 4)]
L.update_material_instance(mi)
RESULT = {'ok': True, 'mi': ARGS['mi'], 'changes': changes,
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
