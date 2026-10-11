"""In-editor (Karmei Yosef operator, fork of the manager's exit_failed_area_run.py): orderly exit after a FAILED run. Saves nothing. Records the run state and error, releases
ASSIGNMENT_RUN.json and the ParallelEditors record, then quits the editor without saving (dirty map and cook packages are
discarded). The GEOCITY_MENU lease line stays held; the manager appends the OWNER=NONE release line afterwards.
ARGS: label, expected_pid."""
import datetime, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve(); TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
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
