"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Area-owned instance area_constants.py ROAD_MI
(<root>/Materials/MI_RoadAsphalt_<AREA_SHORT>_v001) of the area master ROAD_MASTER (created once with MaterialInstanceConstantFactoryNew, as import_astra.py did), then MI
parameter values only (no graph edit): ARGS.scalars {name: value}, ARGS.vectors {name: [r, g, b]}. No save here.
ARGS: expected_pid, script_file (client), scalars (optional), vectors (optional)."""
import os
import importlib.util
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
L = u.MaterialEditingLibrary
MATS = A.AREA_MATERIALS
MASTER, MI = A.ROAD_MASTER, A.ROAD_MI
created = False
if u.EditorAssetLibrary.does_asset_exist(MI):
    mi = u.load_asset(MI)
else:
    mi = u.AssetToolsHelpers.get_asset_tools().create_asset(MI.rsplit('/', 1)[1], MATS, u.MaterialInstanceConstant,
                                                            u.MaterialInstanceConstantFactoryNew())
    L.set_material_instance_parent(mi, u.load_asset(MASTER))
    created = True
assert mi.get_editor_property('parent').get_path_name().split('.')[0] == MASTER
names_s = [str(n) for n in L.get_scalar_parameter_names(mi)]
names_v = [str(n) for n in L.get_vector_parameter_names(mi)]
for n, v in (ARGS.get('scalars') or {}).items():
    assert n in names_s, (n, names_s)
    L.set_material_instance_scalar_parameter_value(mi, n, float(v))
for n, v in (ARGS.get('vectors') or {}).items():
    assert n in names_v, (n, names_v)
    L.set_material_instance_vector_parameter_value(mi, n, u.LinearColor(float(v[0]), float(v[1]), float(v[2]), 1.0))
L.update_material_instance(mi)
RESULT = {'ok': True, 'mi': MI, 'created': created,
          'scalars': {n: round(L.get_material_instance_scalar_parameter_value(mi, n), 4) for n in names_s},
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
