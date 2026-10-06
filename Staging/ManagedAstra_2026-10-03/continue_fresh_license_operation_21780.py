"""PREPARED ONLY: explicit new operation after reviewed license-log fix.

Import does not touch Unreal. schedule requires root activation and exact new
source/review hashes. The expired intent is preserved, never extended/retried.
"""
import copy,datetime,hashlib,importlib,importlib.util,inspect,json,os,sys,time,traceback
from pathlib import Path
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
REVISION='20261003T203730573110'
ARCHIVE=HERE/'EXPIRED_OPERATION_20261003T203730573110_CONNECTOR_CONTROLS.json'
ARCHIVE_SHA='5ef0a305f6825f5c726b760c20e406484052f539b4049075ea20fbd078578e0e'
LIVE=HERE/'FRESH_READONLY_STOP_20261003T204227744766Z.json'
LIVE_SHA='dcc00c4b19f7706fbf1f0e327ce64ff122d9211348d66f98f28b3355c2dbc74f'
UNCHANGED={'geocity_roadbld_grounding.py':'62a8a28a03803fb845bafa2ce820b742a83cb35134b25cf192fcd532bbf6233d','geocity_roadbld_clip.py':'872f4814060a214cdf4238a8ae8c7b9a0a819364bc4f5ea486e573d396980211'}
OLD_WORKFLOW='1909fb60f22be17a18012a5b2a8f990d6fdc7c5c73b8ae164f8fbef5e74ad453'
ACTIVE=[]
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    with Path(path).open('w',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def journal(s,event,**values):
    with s['journal'].open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),event=event,**values))+'\n');f.flush();os.fsync(f.fileno())
def call(s,label,fn):
    journal(s,'BEFORE',operation=label)
    try:value=fn()
    except Exception:
        journal(s,'EXCEPTION',operation=label,error=traceback.format_exc());raise
    journal(s,'AFTER',operation=label);return value
def filesystem_guard(s):
    journal(s,'BEFORE',operation='filesystem_activation_and_freeze_guard')
    assert os.getpid()==21780
    a=read(HERE/'ASSIGNMENTS.json');assert a['one_editor_pid']==21780 and a['editor_writer_thread_id']=='01a102e1-25e6-7f13-b593-4988290a283b'
    assert a['tasks']['task2_delivery']['editor_calls_authorized'] is True
    lease=(ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
    assert 'assigned_editor_PID=21780' in lease and 'worker_thread_id=01a102e1-25e6-7f13-b593-4988290a283b' in lease
    assert s['activation']=='ROOT_ACTIVATED_FRESH_LICENSE_NEW_OPERATION'
    assert file_sha(s['review_path'])==s['review_sha256']
    assert file_sha(ARCHIVE)==ARCHIVE_SHA and file_sha(LIVE)==LIVE_SHA
    for name,digest in {**UNCHANGED,**s['changed_sources']}.items():assert file_sha(ROOT/'Content/Python'/name)==digest,name
    journal(s,'AFTER',operation='filesystem_activation_and_freeze_guard')
    return lease
def dirty(s,u):
    result={}
    for kind,fn in [('maps',u.EditorLoadingAndSavingUtils.get_dirty_map_packages),('content',u.EditorLoadingAndSavingUtils.get_dirty_content_packages)]:
        result[kind]=sorted(call(s,'dirty_'+kind,lambda fn=fn:[v.get_path_name() for v in fn()]))
    return result
def install_observation(s,p,r,bank,native):
    """Journal existing calls without changing their arguments or results."""
    hooks=[]
    def hook(obj,name,label):
        original=getattr(obj,name)
        def observed(*args,**kwargs):return call(s,label,lambda:original(*args,**kwargs))
        setattr(obj,name,observed);hooks.append((obj,name,original,observed))
    for name in ['guard','after_cook','after_processing','after_native_roads','after_bake','finish_save','watch']:
        hook(p,name,'parent.'+name)
    for name in ['guard','request_rebuild','clip_final_geometry','validate','staged_contract','commit','tick']:
        hook(r,name,'native.'+name)
    original_tool=native._tool
    def observed_tool(*args,**kwargs):
        label='native.SDK.'+'.'.join(map(str,args[:2]))
        return call(s,label,lambda:original_tool(*args,**kwargs))
    native._tool=observed_tool;hooks.append((native,'_tool',original_tool,observed_tool))
    # Clean up only after the parent's existing termination routine removes
    # delegates/callbacks using the same observed function identities.
    finish=p.finish_operation
    def finish_observed(*args,**kwargs):
        result=call(s,'parent.finish_operation',lambda:finish(*args,**kwargs))
        for obj,name,original,observed in reversed(hooks):
            assert getattr(obj,name) is observed
            setattr(obj,name,original)
        p.finish_operation=finish
        s['report']['observation_hooks_restored']=True
        s['report']['terminal_parent_phase']=p.state['phase'];s['report']['terminal_native_phase']=r.state['phase']
        write(s['receipt'],s['report'])
        return result
    p.finish_operation=finish_observed
    r.on_complete=p.after_native_roads
    s['hooks']=hooks
def continue_once(s):
    import unreal as u
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_junctions as junctions
    lease=filesystem_guard(s);assert len(bank.ACTIVE)==len(native.ACTIVE)==1
    p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
    s['live_parent']=p;s['live_native']=r
    assert p.native_road_run is r and p.lease_line==r.lease_line==lease
    call(s,'parent.guard',p.guard);call(s,'native.guard',r.guard);call(s,'sole_editor_process_guard',p.guard_processes)
    assert r.revision==REVISION and p.state['phase']=='failed_native_road_transaction' and r.state['phase']=='failed_rebuilding'
    assert r.state['error']=="AssertionError('Native edit failed without fresh call-local pending-license evidence')"
    assert r.rebuild_pass==1 and r.job_id=='19d5d010-47eb-c755-b729-9c81554ef290'
    assert len(r.roads)==40 and len(r.derived_junction_roads)==1 and r.cursor==40
    assert r.junction_repair is None and r.clipping_report is None and not r._tick_running
    assert r.on_complete==p.after_native_roads and p.native_road_phase=='authoring'
    assert all(getattr(x,k,None) is None for x in bank.ACTIVE+native.ACTIVE for k in ['watch_tick','save_tick','tick_handle'])
    api=call(s,'official_API',u.HoudiniPublicAPIBlueprintLib.get_api)
    assert call(s,'Engine_valid',api.is_session_valid) and call(s,'Engine_paused',api.is_asset_cooking_paused)
    assert not call(s,'autosave_current',lambda:p.autosave_settings.get_editor_property('bAutoSaveEnable'))
    assert not call(s,'HDA_autoCook',p.wrapper.is_auto_cooking_enabled) and not call(s,'HDA_autoBake',p.wrapper.is_auto_bake_enabled)
    archive=read(ARCHIVE);old=archive['operation'];live=read(LIVE)
    report=r.state['junction_repair_report'];assert report['phase']=='failed_native_corner_repair'
    assert report['transaction_identity']==archive['transaction_identity']
    assert r.transaction_token==archive['transaction_identity']['token']
    assert report['task_index']==0 and report['step_index']==1 and report['completed_corner_count']==0
    assert report['operation']==old and time.monotonic()>old['deadline_monotonic']
    assert old['step']=='connector_controls' and old['attempts']==1
    assert old['calls'][0]['start_byte']==old['calls'][0]['end_byte']==476884 and old['calls'][0]['suffix']==''
    actual=call(s,'fresh_complete_participant_checkpoint',lambda:junctions._owned_state(r))
    assert sha(actual)==sha(old['before'])==sha(report['checkpoint_state'])==live['actual_owned_state_sha256']
    assert dirty(s,u)=={k:sorted(v) for k,v in live['dirty'].items()}
    assert call(s,'global_defaults',junctions._defaults)==report['global_defaults_before']
    connector=report['connector_actor_path'];assert connector.endswith(':PersistentLevel.DynamicRoad_86')
    assert call(s,'current_connector_path',r.derived_junction_roads[0].get_path_name)==connector
    assert call(s,'current_network_path',r.network.get_path_name)==archive['transaction_identity']['network']
    assert sha(report['planned_tasks'])==report['planned_tasks_sha256'] and sha(report['sourcecontrols_trimproof'])==report['sourcecontrols_trimproof_sha256']
    s['report'].update(pre_parent_state=copy.deepcopy(p.state),pre_native_state=copy.deepcopy(r.state),current_checkpoint=actual,expired_operation_archive=str(ARCHIVE),expired_operation_archive_sha256=ARCHIVE_SHA,expired_deadline=old['deadline_monotonic'],revision=r.revision,token=r.transaction_token,dirty=live['dirty'])
    write(s['receipt'],s['report'])
    # Only the reviewed changed modules may reload. Keep exact run identities.
    live_native_runs=native.ACTIVE;old_class=r.__class__
    if s['changed_sources']['geocity_roadbld_workflow.py']!=OLD_WORKFLOW:
        # Evaluate the reviewed definitions in an isolated module namespace.
        # Do not reload in place: that would clear the live ACTIVE registry.
        workflow_path=ROOT/'Content/Python/geocity_roadbld_workflow.py'
        spec=importlib.util.spec_from_file_location('geocity_roadbld_workflow',workflow_path)
        candidate=importlib.util.module_from_spec(spec)
        attrs_before={key:id(value) for key,value in vars(r).items()}
        state_before_refresh=sha(r.state)
        call(s,'load_reviewed_workflow_definitions_in_isolated_namespace',lambda:spec.loader.exec_module(candidate))
        old_signatures={name:str(inspect.signature(value)) for name,value in old_class.__dict__.items() if inspect.isfunction(value)}
        new_signatures={name:str(inspect.signature(value)) for name,value in candidate.RoadBLDRun.__dict__.items() if inspect.isfunction(value)}
        assert all(new_signatures.get(name)==signature for name,signature in old_signatures.items()),'Live workflow method signatures are incompatible'
        assert native.ACTIVE is live_native_runs and len(live_native_runs)==1 and live_native_runs[0] is r
        assert {key:id(value) for key,value in vars(r).items()}==attrs_before and sha(r.state)==state_before_refresh
        candidate.ACTIVE=live_native_runs
        s['report']['workflow_refresh_compatibility']={'existing_method_signatures':old_signatures,'all_existing_signatures_identical':True,'live_ACTIVE_list_preserved':True,'all_run_attribute_identities_preserved':True,'state_sha256':state_before_refresh}
        write(s['receipt'],s['report'])
        sys.modules['geocity_roadbld_workflow']=candidate;native=candidate
        r.__class__=native.RoadBLDRun
        assert native.ACTIVE is live_native_runs and {key:id(value) for key,value in vars(r).items()}==attrs_before
    junctions=call(s,'reload_reviewed_junction_module',lambda:importlib.reload(junctions))
    assert bank.ACTIVE[-1] is p and native.ACTIVE[-1] is r and p.native_road_run is r
    actual_after_reload=call(s,'checkpoint_after_helper_refresh',lambda:junctions._owned_state(r))
    assert sha(actual_after_reload)==sha(actual)
    expected=call(s,'derive_same_exact_new_operation_expectation',lambda:junctions._expected_edit(actual,report['planned_tasks'][0],'connector_controls',connector,report['sourcecontrols_trimproof']))
    assert expected==old['expected_after']
    # New intent is separately identified. Old object/deadline remains archived.
    intent=dict(step=old['step'],task_index=old['task_index'],before=actual,expected_after=expected,attempts=0,calls=[])
    now=time.monotonic();intent.update(started_monotonic=now,deadline_monotonic=now+60.0)
    s['report'].update(new_operation_intent=copy.deepcopy(intent),new_intent_is_same_failed_step=True,grounding_clip_not_reloaded=True,workflow_class_refreshed=r.__class__ is not old_class)
    write(s['receipt'],s['report'])
    assert report['operation']==old and old['deadline_monotonic']==167732.562
    s['authoring_transition_started']=True
    report['operation']=intent
    report['phase']='conditioning_native_corners';report.pop('error',None)
    r.state['phase']='conditioning';r.state.pop('error',None)
    r.state['license_new_operation_evidence']=str(s['receipt']);call(s,'persist_new_native_operation_intent',r.write)
    install_observation(s,p,r,bank,native)
    call(s,'parent_suspend_autosave',p.suspend_transaction_autosave)
    p.started_epoch=time.time();p.state['phase']='native_road_authoring';p.state.pop('error',None);p.state.pop('api_error',None)
    p.state['license_new_operation_evidence']=str(s['receipt'])
    call(s,'restore_parent_post_cook_delegate',lambda:p.wrapper.on_post_cook_delegate.add_callable(p.after_cook))
    call(s,'restore_parent_post_processing_delegate',lambda:p.wrapper.on_post_processing_delegate.add_callable(p.after_processing))
    p.watch_tick=call(s,'register_parent_watch',lambda:u.register_slate_post_tick_callback(p.watch))
    r.tick_handle=call(s,'register_existing_native_queue',lambda:u.register_slate_post_tick_callback(r.tick))
    call(s,'persist_parent_continuation',p.write)
    s['report'].update(status='ordinary_queue_resumed_new_operation',no_new_export_Cook_network_or_source_roads=True)

def schedule(expected_junction_sha256,expected_workflow_sha256,review_path,review_sha256,manager_activation):
    assert not ACTIVE,'Single explicit continuation only; no repeated schedules'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'handle':None,'receipt':HERE/('FRESH_LICENSE_CONTINUATION_'+stamp+'.json'),'journal':HERE/('FRESH_LICENSE_CONTINUATION_'+stamp+'.jsonl'),
       'activation':manager_activation,'review_path':str(review_path),'review_sha256':review_sha256,
       'changed_sources':{'geocity_roadbld_junctions.py':expected_junction_sha256,'geocity_roadbld_workflow.py':expected_workflow_sha256},
       'report':{'status':'scheduled','pid':os.getpid(),'review_path':str(review_path),'review_sha256':review_sha256}}
    filesystem_guard(s)
    import unreal as u
    def tick(dt):
        call(s,'remove_one_shot_continuation_callback',lambda:u.unregister_slate_post_tick_callback(s['handle']));s['handle']=None
        try:continue_once(s)
        except Exception as exc:
            s['report'].update(status='stopped',error=traceback.format_exc())
            if s.get('authoring_transition_started'):
                try:call(s,'ordinary_native_failure_cleanup',lambda:s['live_native'].fail(exc))
                except Exception:s['report']['cleanup_error']=traceback.format_exc()
        write(s['receipt'],s['report']);journal(s,'CONTINUATION_STEP_END',status=s['report']['status'])
    write(s['receipt'],s['report']);ACTIVE.append(s)
    s['handle']=call(s,'register_one_shot_GameThread_continuation',lambda:u.register_slate_post_tick_callback(tick))
    return str(s['receipt'])
