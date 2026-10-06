"""Record a clean native checkpoint only under the manager's actual bank lease."""
import datetime
import json
import os
from pathlib import Path
import unreal
import geocity_editor_action as action
import geocity_runtime_guard as guard

ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/BankIntegration_2026-10-04'
lease=[s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
fields=action.lease_fields(lease)
assert fields.get('OWNER')=='CODEX_BANK_INTEGRATION'
assert fields.get('assigned_editor_PID')==str(os.getpid())
assert fields.get('operator_thread_id')=='01a1067c-5012-7550-b449-015b53c9d726'
assert fields.get('manager_thread_id')=='01a106bc-2fde-7f23-9aa7-8ba413dc6245'
sources=guard.verify()
startup=json.loads((HERE/'STARTUP_INSPECTION.json').read_text())
assert startup['passed'] and startup['state_unchanged'] and startup['before']['pid']==os.getpid()
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert world==startup['before']['world']==fields['map']
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
actors=sorted(a.get_path_name() for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
assert actors==startup['after']['actors']
result={'pid':os.getpid(),'world':world,'lease':lease,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'allowed_dirty_maps':[],'allowed_dirty_content':['/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4'], 'startup_receipt':str(HERE/'STARTUP_INSPECTION.json'),
    'sources':sources,'ordinary_generation_authorized':False,'initial_state_clean':True,'actor_paths':actors}
(HERE/'EDITOR_ACQUIRED.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'bank_checkpoint_created':True,'pid':os.getpid(),'world':world,'clean':True}))
