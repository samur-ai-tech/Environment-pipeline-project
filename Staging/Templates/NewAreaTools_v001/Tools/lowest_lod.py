"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef tool. Aviv: far trees in the always-loaded HLOD use their LOWEST LOD. A card or
dead-tree billboard as lowest LOD would show everywhere far away, and a single 8.9k-triangle level for 13.8k pines is too heavy.
So the area-owned vegetation copies (<clone>/Vegetation/Meshes, Nanite on; only their non-Nanite render path changes) get
automatic LOD chains reduced from LOD0 (real geometry, no cards). Before-state -> receipts/LOWEST_LOD_BEFORE.json.
Not saved here. ARGS: expected_pid, script_file (client), plan {mesh_name: [[percent_triangles, screen_size], ...]}."""
import importlib.util, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
VM = A.TRIAL_ROOT + '/Vegetation/Meshes/'
assert os.getpid() == ARGS['expected_pid']
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
before, after = {}, {}
for name, steps in ARGS['plan'].items():
    m = u.load_asset(VM + name); assert m, name
    before[name] = {'lods': [m.get_num_triangles(i) for i in range(sms.get_lod_count(m))], 'screen': [round(x, 3) for x in sms.get_lod_screen_sizes(m)]}
    opts = u.EditorScriptingMeshReductionOptions(auto_compute_lod_screen_size=False,
                                                reduction_settings=[u.EditorScriptingMeshReductionSettings(percent_triangles=p, screen_size=s) for p, s in steps])
    n = sms.set_lods(m, opts)
    after[name] = {'set_lods': n, 'lods': [m.get_num_triangles(i) for i in range(sms.get_lod_count(m))],
                   'sections_last': m.get_num_sections(sms.get_lod_count(m) - 1), 'screen': [round(x, 3) for x in sms.get_lod_screen_sizes(m)]}
rec = TASK / 'receipts' / 'LOWEST_LOD_BEFORE.json'
if not rec.exists():
    rec.write_text(json.dumps(before, indent=1), encoding='utf-8')
RESULT = {'ok': True, 'before': before, 'after': after}
