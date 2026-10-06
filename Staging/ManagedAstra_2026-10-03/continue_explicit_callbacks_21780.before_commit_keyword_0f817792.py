"""PREPARED ONLY. Same live v6 transaction, explicit native callback arities."""
import copy,datetime,hashlib,json,os,time,traceback
import fresh_delivery_21780 as d
HERE=d.HERE
LIVE=HERE/'DELEGATE_STOP_20261003T205851425661Z.json'
LIVE_SHA='abb098e40d3ee76948c028d7a881ded46cab891f297e0c6e4dc5a7269b90dfcc'
ARCHIVE=HERE/'EXPIRED_ZERO_ATTEMPT_INTENT_20261003T205502525516Z.json'
ARCHIVE_SHA='cb5fffaa0b9c2246f7ae842fafa67ee2f785168729392b5c9315ecf1854d3f2b'
REVIEW=HERE/'TASK3_LICENSE_REVIEW.json'
REVIEW_SHA='eb4180ca54d178de9453b79e300160aaf16db910d53dd412a567806daa4f5bd0'
FROZEN={'geocity_roadbld_junctions.py':'dfb65168e6cdc6f5e75a98d63b2f862f0c1e5eca13bf8d93741be5accaf62802','geocity_roadbld_workflow.py':'a75d78d4eff44068109ab56fae46f34a074f4c0b141409ca2f764dfb26bc645a','geocity_roadbld_grounding.py':'62a8a28a03803fb845bafa2ce820b742a83cb35134b25cf192fcd532bbf6233d','geocity_roadbld_clip.py':'872f4814060a214cdf4238a8ae8c7b9a0a819364bc4f5ea486e573d396980211'}
ACTIVE=[]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def authorize(s):
    d.journal(s,'BEFORE',operation='activation_guard')
    assert s['activation']=='ROOT_ACTIVATED_EXPLICIT_CALLBACK_ARITY_CONTINUATION'
    assert os.getpid()==21780
    a=d.read(HERE/'ASSIGNMENTS.json');assert a['one_editor_pid']==21780 and a['editor_writer_thread_id']=='01a102e1-25e6-7f13-b593-4988290a283b'
    assert a['tasks']['task2_delivery']['editor_calls_authorized'] is True
    for path,want in [(LIVE,LIVE_SHA),(ARCHIVE,ARCHIVE_SHA),(REVIEW,REVIEW_SHA)]:assert digest(path)==want
    for name,want in FROZEN.items():assert digest(d.ROOT/'Content/Python'/name)==want
    d.journal(s,'AFTER',operation='activation_guard')
def observe(s,original,label,arity):
    # Actual co_argcount, not functools.wraps or inspect-only signatures.
    if arity==0:
        def explicit():return d.call(s,label,original)
    elif arity==1:
        def explicit(in_wrapper_or_delta):return d.call(s,label,lambda:original(in_wrapper_or_delta))
    elif arity==2:
        def explicit(in_wrapper,cook_success):return d.call(s,label,lambda:original(in_wrapper,cook_success))
    else:raise AssertionError('Unsupported callback arity')
    assert explicit.__code__.co_argcount==arity and not explicit.__code__.co_flags & 0x0c
    return explicit
def install(s,p,r,native):
    hooks=[]
    for obj,entries,prefix in [(p,{'guard':0,'after_cook':2,'after_processing':1,'after_native_roads':2,'after_bake':2,'finish_save':1,'watch':1},'parent'),(r,{'guard':0,'request_rebuild':0,'clip_final_geometry':0,'validate':0,'staged_contract':0,'commit':1,'tick':1},'native')]:
        for name,arity in entries.items():
            original=getattr(obj,name);wrapped=observe(s,original,prefix+'.'+name,arity)
            setattr(obj,name,wrapped);hooks.append((obj,name,original,wrapped))
    original_tool=native._tool
    def tool_observed(*args,**kwargs):return d.call(s,'SDK.'+'.'.join(map(str,args[:2])),lambda:original_tool(*args,**kwargs))
    native._tool=tool_observed;hooks.append((native,'_tool',original_tool,tool_observed))
    original_finish=p.finish_operation
    def finish():
        result=d.call(s,'parent.finish_operation',original_finish)
        for obj,name,original,wrapped in reversed(hooks):
            assert getattr(obj,name) is wrapped;setattr(obj,name,original)
        p.finish_operation=original_finish
        s['report'].update(observation_hooks_restored=True,terminal_parent_phase=p.state['phase'],terminal_native_phase=r.state['phase'])
        d.write(s['receipt'],s['report']);return result
    p.finish_operation=finish;r.on_complete=p.after_native_roads
    s['report']['native_callback_actual_argcounts']={name:getattr(p,name).__code__.co_argcount for name in ['after_cook','after_processing','after_bake','watch','finish_save']}
    s['report']['native_tick_actual_argcount']=r.tick.__code__.co_argcount
def resume(s):
    import unreal as u
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_junctions as junctions
    authorize(s);assert len(bank.ACTIVE)==len(native.ACTIVE)==1
    p=bank.ACTIVE[0];r=native.ACTIVE[0];s['parent']=p;s['native']=r
    assert p.native_road_run is r and type(r) is native.RoadBLDRun
    d.call(s,'parent_guard',p.guard);d.call(s,'native_guard',r.guard);d.call(s,'sole_editor_guard',p.guard_processes)
    live=d.read(LIVE);archive=d.read(ARCHIVE);report=r.state['junction_repair_report'];old=archive['operation']
    assert r.revision==live['revision']=='20261003T203730573110' and r.transaction_token==archive['token']==live['token']
    assert p.state['phase']=='failed_native_road_transaction' and r.state['phase']=='failed_conditioning'
    assert p.lease_line==r.lease_line and r.rebuild_pass==1 and r.job_id==live['native_state']['rebuild_job_id']
    assert len(r.roads)==40 and len(r.derived_junction_roads)==1 and r.cursor==40 and r.junction_repair is None and r.clipping_report is None
    assert not r._tick_running and all(getattr(x,k,None) is None for x in [p,r] for k in ['watch_tick','save_tick','tick_handle'])
    assert report['operation']==old and old['attempts']==0 and old['calls']==[] and time.monotonic()>old['deadline_monotonic']
    assert report['task_index']==0 and report['step_index']==1 and report['completed_corner_count']==0
    assert report['phase']=='conditioning_native_corners' and old['step']=='connector_controls'
    actual=d.call(s,'fresh_participant_checkpoint',lambda:junctions._owned_state(r))
    assert junctions._sha(actual)==junctions._sha(old['before'])==junctions._sha(report['checkpoint_state'])==junctions._sha(live['actual_participants'])
    current_dirty=d.dirty(s);assert {k:sorted(v) for k,v in current_dirty.items()}=={k:sorted(v) for k,v in live['dirty'].items()}
    api=d.idle(s);assert d.call(s,'Engine_valid',api.is_session_valid)
    assert not d.call(s,'HDA_autoCook',p.wrapper.is_auto_cooking_enabled) and not d.call(s,'HDA_autoBake',p.wrapper.is_auto_bake_enabled)
    expected=d.call(s,'pure_exact_expected_after',lambda:junctions._expected_edit(actual,report['planned_tasks'][0],old['step'],report['connector_actor_path'],report['sourcecontrols_trimproof']))
    assert expected==old['expected_after'] and d.call(s,'global_defaults',junctions._defaults)==report['global_defaults_before']
    s['report'].update(pre_parent_state=copy.deepcopy(p.state),pre_native_state=copy.deepcopy(r.state),current_participants=actual,dirty=current_dirty,
        expired_operation_archive=str(ARCHIVE),expired_operation_sha256=ARCHIVE_SHA,expired_deadline=old['deadline_monotonic'],no_helpers_reloaded=True,live_class_is_current_reviewed_v6=True)
    d.write(s['receipt'],s['report'])
    # Register exactly shaped delegates before creating the new timed intent.
    s['transition_started']=True;install(s,p,r,native)
    d.call(s,'register_post_cook_2args',lambda:p.wrapper.on_post_cook_delegate.add_callable(p.after_cook))
    d.call(s,'register_post_processing_1arg',lambda:p.wrapper.on_post_processing_delegate.add_callable(p.after_processing))
    d.call(s,'suspend_transaction_autosave',p.suspend_transaction_autosave)
    now=time.monotonic();intent=dict(step=old['step'],task_index=old['task_index'],before=actual,expected_after=expected,started_monotonic=now,deadline_monotonic=now+60,attempts=0,calls=[])
    s['report']['new_operation_intent']=copy.deepcopy(intent);d.write(s['receipt'],s['report'])
    assert report['operation']==old and old['deadline_monotonic']==168707.234
    report['operation']=intent;r.state['phase']='conditioning';r.state.pop('error',None);r.state['explicit_callback_continuation_evidence']=str(s['receipt'])
    p.started_epoch=time.time();p.state['phase']='native_road_authoring';p.state.pop('error',None);p.state.pop('api_error',None);p.state['explicit_callback_continuation_evidence']=str(s['receipt'])
    d.call(s,'persist_new_native_intent',r.write);d.call(s,'persist_parent_continuation',p.write)
    p.watch_tick=d.call(s,'register_parent_watch_1arg',lambda:u.register_slate_post_tick_callback(p.watch))
    r.tick_handle=d.call(s,'register_native_tick_1arg',lambda:u.register_slate_post_tick_callback(r.tick))
    s['report']['status']='ordinary_queue_resumed'
def schedule(manager_activation):
    assert not ACTIVE,'One reviewed schedule only'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'handle':None,'activation':manager_activation,'journal':HERE/('EXPLICIT_CALLBACK_CONTINUATION_'+stamp+'.jsonl'),'receipt':HERE/('EXPLICIT_CALLBACK_CONTINUATION_'+stamp+'.json'),'report':{'status':'scheduled','pid':os.getpid()}}
    authorize(s)
    import unreal as u
    def tick(dt):
        d.call(s,'unregister_continuation',lambda:u.unregister_slate_post_tick_callback(s['handle']));s['handle']=None
        try:resume(s)
        except Exception as exc:
            s['report'].update(status='stopped',error=traceback.format_exc())
            if s.get('transition_started'):
                try:d.call(s,'ordinary_failure_cleanup',lambda:s['native'].fail(exc))
                except Exception:s['report']['cleanup_error']=traceback.format_exc()
        d.write(s['receipt'],s['report'])
    d.write(s['receipt'],s['report']);ACTIVE.append(s)
    s['handle']=d.call(s,'register_one_shot_continuation',lambda:u.register_slate_post_tick_callback(tick));return str(s['receipt'])
