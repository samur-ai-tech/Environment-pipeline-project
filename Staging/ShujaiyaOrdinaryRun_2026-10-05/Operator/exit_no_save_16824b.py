import os,json,sys,unreal
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(r'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
assert os.getpid()==16824,'unexpected PID'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
wp=world.get_outermost().get_path_name()
assert wp=='/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration',wp
api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
paused=bool(api.is_asset_cooking_paused())
active=[k for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle') if getattr(r,k,None) is not None]
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
# the map is dirty only from the reverted (unsaved) MW preview; it is discarded on exit
land=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a,unreal.Landscape)][0]
assert land.get_editor_property('landscape_material').get_path_name()=='/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround.MI_GeoCityGround','preview not reverted'
assert not active,'lifecycle ticks still active: '+str(active)
rec={'pid':os.getpid(),'utc':datetime.now(timezone.utc).isoformat(),'world':wp,'cooking_paused':paused,'active_ticks':active,
     'dirty_content_discarded_unsaved':dc,'dirty_maps':dm,'shutdown_saves':0,'forced_termination':False,
     'reason':'MW auto-material preview (unsaved) reverted; Aviv chose Path B (MW material via small reviewed code change); editor closed without saving; disk unchanged'}
out=ROOT/'Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator'/f'EXIT_PID{os.getpid()}.json'
out.write_text(json.dumps(rec,indent=2),encoding='utf-8')
with (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').open('a',encoding='utf-8') as f:
    f.write('\n'+datetime.now(timezone.utc).isoformat()+' OWNER=NONE released_by=claude_manager_cc37d4d2 previous_editor_PID=16824 reason=discard_unsaved_MW_preview_before_PathB shutdown_saves=0 dirty_discarded='+str(len(dc))+'\n')
print(json.dumps({'ok':True,'recorded':str(out),'paused':paused,'dirty_discarded':len(dc)}))
unreal.SystemLibrary.quit_editor()
