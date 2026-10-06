from pathlib import Path
from datetime import datetime,timezone
import unreal,json,os,sys,shutil,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
assert os.getpid()==31508
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle'))
folder=ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02'
assert json.loads((folder/'WORKFLOW_STATE.json').read_text())['phase']=='failed_native_road_transaction'
dirty=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
maps=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert maps==['/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration']
assert all(p.startswith(('/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Cook/','/Game/Project/Areas/GazaShujaiya/RoadBLD/Presets/','/Game/Project/Areas/GazaShujaiya/RoadBLD/Sidewalks/')) for p in dirty)
out=HERE/'Attempt2';out.mkdir(exist_ok=True)
for name in ('WORKFLOW_STATE.json','ROADBLD_WORKFLOW_STATE.json','HDA_CATALOG_RECEIPT.json','AREA_PROFILE.json'):
    assert not (out/name).exists();shutil.copy2(folder/name,out/name)
for p in (ROOT/'Content/Python/geocity_roadbld_props.py',ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'):
    shutil.copy2(p,out/p.name)
(out/'EDITOR_EXIT.json').write_text(json.dumps({'pid':os.getpid(),'discard_failed_run_only':True,'dirty_content':dirty,'dirty_maps':maps,'callbacks':0,'paused':True,'saved_map_sha256':hashlib.sha256((ROOT/'Content'/(maps[0][6:]+'.umap')).read_bytes()).hexdigest()},indent=2))
lease=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
with lease.open('a') as f:f.write('\n'+datetime.now(timezone.utc).isoformat()+' OWNER=CODEX_MANAGED_SYSTEMS_TASK4 operator_thread_id=01a10c77-46ba-7001-a657-5014f6205d3a assigned_editor_PID=31508 activation=ORDERLY_FAILED_RUN_EXIT scope=discard_only_recorded_failed_run_buffers\n')
unreal.SystemLibrary.quit_editor()
