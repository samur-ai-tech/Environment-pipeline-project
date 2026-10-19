"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Orderly quit with ZERO saves.
Refuses (no quit) if any map is dirty or any content package outside this area's Cook folder is dirty. Dirty packages
inside <root>/Cook/ are allowed only with ARGS.allow_cook_leftovers (unreferenced cook stages after a verified run); they
must equal the run's acknowledged unreferenced_cook_packages; they are recorded and discarded with the process (never saved). Releases ../ASSIGNMENT_RUN.json, ../ASSIGNMENT_RUN_PID<pid>.json and the ParallelEditors
record, then quits. ARGS: label, expected_pid, allow_cook_leftovers (bool, default false).
"""
import datetime, json, os
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
import importlib.util
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
COOK = A.COOK_PREFIX
pid = os.getpid()
assert pid == ARGS['expected_pid'], (pid, ARGS['expected_pid'])
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
maps = [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
content = [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
leftovers = [x for x in content if x.startswith(COOK)]
other = [x for x in content if not x.startswith(COOK)]
bank = None                                         # template fix: no NameError below when the import fails
try:
    import geocity_bank_workflow as bank
    phase = bank.ACTIVE[-1].state.get('phase') if bank.ACTIVE else None
except Exception as exc:
    phase = 'unknown: ' + repr(exc)
refusal = None
if maps or other:
    refusal = 'dirty map/content outside the Cook folder'
elif leftovers and not ARGS.get('allow_cook_leftovers'):
    refusal = 'cook leftovers present and allow_cook_leftovers not set'
elif leftovers and bank is None:
    refusal = 'cook leftovers present but geocity_bank_workflow could not be imported to check them'
elif leftovers and sorted(leftovers) != sorted(bank.ACTIVE[-1].state.get('unreferenced_cook_packages') or [] if bank.ACTIVE else []):
    refusal = 'dirty cook packages differ from the run-acknowledged unreferenced cook packages'
elif phase and not (str(phase).startswith(('baked_saved', 'failed')) or phase is None):
    refusal = 'a GeoCity run is in phase ' + str(phase)
receipt = {'utc': now, 'pid': pid, 'label': ARGS['label'], 'dirty_maps': maps, 'dirty_content_other': other,
           'cook_leftovers_discarded': leftovers if refusal is None else [], 'last_run_phase': phase,
           'saves': 0, 'refused': refusal}
(TASK / 'receipts').mkdir(exist_ok=True)
(TASK / 'receipts' / ('QUIT_CLEAN_%s_PID%d.json' % (ARGS['label'], pid))).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
RESULT = {'ok': refusal is None, 'receipt': receipt}
if refusal is None:
    for f in (TASK / 'ASSIGNMENT_RUN.json', TASK / ('ASSIGNMENT_RUN_PID%d.json' % pid), ROOT / ('Staging/ParallelEditors/EDITOR_%d.json' % pid)):
        if f.exists():
            d = json.loads(f.read_text(encoding='utf-8-sig'))
            d['editor_live'] = False
            d['released_utc'] = now
            d['status'] = 'RELEASED_CLEAN_' + ARGS['label']
            f.write_text(json.dumps(d, indent=2), encoding='utf-8')
    # Same as the bank owner's quit_clean.py: the unsaved cook leftovers are discarded with the process.
    u.SystemLibrary.quit_editor()
