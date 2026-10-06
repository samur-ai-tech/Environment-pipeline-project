from pathlib import Path
from datetime import datetime,timezone
import unreal,json,os,sys,hashlib,shutil,traceback
import geocity_bank_workflow as base,geocity_runtime_guard
HERE=Path(__file__).resolve().parent
r=base.ACTIVE[-1]
assert os.getpid()==10460 and r.state['phase']=='failed_cook_verification'
assert r.state['error']=="PermissionError(13, 'Access is denied')"
assert len(geocity_runtime_guard.verify())==12
assert r.watch_tick is None and r.save_tick is None and r._finishing is False
assert r.state.get('bake_success') is None
assert r.state['instance_count']==r.state['actual_instance_count']==11508
assert r.state['geographic_building_coverage']['complete_native_construction']
# Paint readback can lag the output callback; the retained readiness gate below
# remains responsible for observing it before Bake.
assert r.native_road_run is None and r.p['roadbld_workflow']['enabled'] is False
assert hashlib.sha256(r.profile_path.read_bytes()).hexdigest()==r.profile_sha256
assert base._generation_lease(r.project,r.p['map'])==r.lease_line
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()==r.p['map']
assert r.api.is_asset_cooking_paused() and not r.wrapper.is_auto_cooking_enabled() and not r.wrapper.is_auto_bake_enabled()
assert r.wrapper.get_num_outputs()==3 and len(r.wrapper.get_houdini_asset_actor().get_components_by_class(unreal.MeshComponent))==498
out=HERE/'Attempt3';out.mkdir(exist_ok=True)
assert not (out/'WORKFLOW_BEFORE_SAVE_RECOVERY.json').exists()
shutil.copy2(r.state_path,out/'WORKFLOW_BEFORE_SAVE_RECOVERY.json')
shutil.copy2(r.receipt,out/'COMPLETED_HDA_RECEIPT.json')
recovery={'pid':os.getpid(),'utc':datetime.now(timezone.utc).isoformat(),'prior_error':r.state['error'],'reused_completed_native_cook':True,'recook_requested':False,'checks':'Retained after_processing will re-read complete native outputs/materials/terrain before invoking ordinary Bake and named save','unrelated_packages_saved':False}
(out/'SAVE_RECOVERY.json').write_text(json.dumps(recovery,indent=2))
# No runtime reload or alternate bake: re-enter the retained completion callback
# against the same fully cooked outputs after the transient file-access error.
r.state.update(phase='cooking',save_recovery=recovery)
r.state.pop('error',None)
r._finishing=False
r.watch_tick=unreal.register_slate_post_tick_callback(r.watch)
r.after_processing(r.wrapper)
print(json.dumps({'phase':r.state['phase'],'error':r.state.get('error'),'native_instances':r.state.get('instance_count')}))
