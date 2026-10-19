"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the fork of the manager's exit_failed_area_run.py: orderly exit after a
FAILED run. Saves nothing. Records the run state and error, releases
ASSIGNMENT_RUN.json and the ParallelEditors record, then quits the editor without saving (dirty map and cook packages are
discarded). The GEOCITY_MENU lease line stays held; Aviv, or the agent he assigns, appends the OWNER=NONE release line
afterwards (there is no manager session, GOVERNANCE_RECORD.md RC-03).
ARGS: label, expected_pid."""
import datetime, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
import importlib.util
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
pid = os.getpid(); assert pid == ARGS['expected_pid']
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
import geocity_bank_workflow as bank
st = bank.ACTIVE[-1].state if bank.ACTIVE else {}
assert str(st.get('phase', '')).startswith('failed'), 'Not a failed run: %s' % st.get('phase')
dirty = ([x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
         [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()])
receipt = {'utc': now, 'pid': pid, 'label': ARGS['label'], 'phase': st.get('phase'), 'error': str(st.get('error'))[:500],
           'dirty_discarded_unsaved': dirty, 'saves': 0}
(TASK / 'receipts').mkdir(exist_ok=True)
(TASK / 'receipts' / ('EXIT_FAILED_%s_PID%d.json' % (ARGS['label'], pid))).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
for f in (TASK / 'ASSIGNMENT_RUN.json', TASK / ('ASSIGNMENT_RUN_PID%d.json' % pid), ROOT / ('Staging/ParallelEditors/EDITOR_%d.json' % pid)):
    if f.exists():
        d = json.loads(f.read_text(encoding='utf-8-sig')); d['editor_live'] = False; d['released_utc'] = now
        d['status'] = 'RELEASED_FAILED_' + ARGS['label']; f.write_text(json.dumps(d, indent=2), encoding='utf-8')
RESULT = {'ok': True, 'receipt': receipt}
# discard everything: reload the map from disk without saving, then quit without a save prompt
for pkg in list(u.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(u.EditorLoadingAndSavingUtils.get_dirty_content_packages()):
    try: pkg.set_dirty_flag(False)
    except Exception: pass
u.SystemLibrary.quit_editor()
