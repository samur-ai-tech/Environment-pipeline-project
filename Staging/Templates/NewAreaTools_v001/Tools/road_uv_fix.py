"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69) (playbook 10c). The generator writes road UVs in
world metres (UV0 -2000..+2000) and the baked road mesh stored them at half precision, which quantises every texture into
0.5-1 m blocks ('grey paving'). This step backs up this area's road_surfaces bake package (area_constants.py ROAD_MESH) to ../Before/, enables
use_full_precision_u_vs on its LOD0 build settings (which rebuilds the mesh) and reports the dirty packages. Only this
area's own bake mesh changes; a regeneration re-bakes it with the old setting. No save here (save_prefix.py on the Bake
folder). ARGS: expected_pid, script_file (client)."""
import datetime, hashlib, importlib.util, json, os, shutil
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
MESH = A.ROAD_MESH
f = ROOT / ('Content' + MESH[5:] + '.uasset')
sha = hashlib.sha256(f.read_bytes()).hexdigest()
backup = TASK / 'Before' / ('%s_%s.uasset' % (f.stem, sha[:8]))
if not backup.exists():
    shutil.copy2(f, backup)
assert hashlib.sha256(backup.read_bytes()).hexdigest() == sha
m = u.load_asset(MESH)
sub = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
bs = sub.get_lod_build_settings(m, 0)
before = bs.get_editor_property('use_full_precision_u_vs')
bs.set_editor_property('use_full_precision_u_vs', True)
sub.set_lod_build_settings(m, 0, bs)                       # triggers the rebuild
after = sub.get_lod_build_settings(m, 0).get_editor_property('use_full_precision_u_vs')
res = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'mesh': MESH, 'sha256_before': sha, 'backup': str(backup),
       'full_precision_uvs_before': before, 'full_precision_uvs_after': after, 'triangles': m.get_num_triangles(0),
       'dirty_maps': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
       'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
(TASK / 'receipts' / 'ROAD_UV_FIX.json').write_text(json.dumps(res, indent=2), encoding='utf-8')
RESULT = {'ok': after is True, **res}
