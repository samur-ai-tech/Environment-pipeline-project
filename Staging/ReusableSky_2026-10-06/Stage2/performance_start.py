import json,datetime
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
req=json.loads((root/'REQUEST.json').read_text(encoding='utf-8-sig'))
csvdir=Path(unreal.Paths.project_saved_dir())/'Profiling/CSV'
before=[str(p.resolve()) for p in csvdir.glob('*.csv')]
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(w,'csvprofile frames=180')
RESULT={'name':req['name'],'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before_csv_files':before,'frames_requested':180}
(root/('PERF_START_'+req['name']+'.json')).write_text(json.dumps(RESULT,indent=2))
