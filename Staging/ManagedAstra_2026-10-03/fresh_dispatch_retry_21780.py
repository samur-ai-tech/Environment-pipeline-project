"""One supported retry of fresh native dispatch explicitly rejected as pending license.
No source reload, new network, new cook, duplicated road or old-PID restoration.
"""
import time
import fresh_delivery_21780 as d

def retry(s):
    import unreal as u
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    api=d.idle(s)
    assert len(bank.ACTIVE)==len(native.ACTIVE)==1
    p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
    d.call(s,'parent_guard',p.guard);d.call(s,'native_guard',r.guard);d.call(s,'sole_process_guard',p.guard_processes)
    assert p.native_road_run is r and p.native_road_phase=='authoring' and r.on_complete==p.after_native_roads
    assert p.state['phase']=='failed_native_road_transaction' and r.state['phase']=='failed_authoring'
    assert r.state['error']=="AssertionError('Native rebuild dispatch failed: RoadBLDToolset: The RoadBLD license check is still running. Retry in a few seconds.')"
    assert r.revision=='20261003T203730573110' and r.rebuild_pass==0 and r.job_id is None
    assert r.cursor==len(r.roads)==r.plan['source_piece_count']==40
    assert not r.derived_junction_roads and r.junction_repair is None and r.clipping_report is None
    assert not r._tick_running and p.lease_line==r.lease_line
    assert d.call(s,'official_session_valid',api.is_session_valid)
    auth=d.call(s,'auth_subsystem',lambda:u.get_editor_subsystem(u.WorldBLDAuthSubsystem))
    assert d.call(s,'current_RoadBLD_license',lambda:auth.has_license_for_tool('RoadBLD'))
    roads=[d.path(s,a,'source_road') for a in r.roads]
    assert len(set(roads))==40
    for road,row in zip(r.roads,r.plan['roads']):d.call(s,'verify_source_controls:'+row['piece_id'],lambda road=road,row=row:r.check_road(road,row))
    geos=d.call(s,'existing_owned_geometry',r.native_geos);assert not geos,'Unexpected geometry means dispatch may have started'
    s['report'].update(parent_state=dict(p.state),native_state=dict(r.state),revision=r.revision,transaction_token=r.transaction_token,network=d.path(s,r.network,'network'),roads=roads,dirty=d.dirty(s),rebuild_pass_before=0,job_id_before=None,source_frozen=d.FROZEN)
    d.write(s['receipt'],s['report'])
    # Retry only the same official dispatch after the pending SDK check yielded.
    d.call(s,'retry_existing_native_request_rebuild_once',r.request_rebuild)
    assert r.rebuild_pass==1 and r.job_id and r.state['phase']=='rebuilding'
    r.state.pop('error',None);r.state['fresh_dispatch_retry_evidence']=str(s['receipt']);r.write()
    d.call(s,'suspend_transaction_autosave',p.suspend_transaction_autosave)
    p.started_epoch=time.time();p.state['phase']='native_road_authoring';p.state.pop('error',None);p.state.pop('api_error',None)
    p.state['fresh_dispatch_retry_evidence']=str(s['receipt'])
    d.call(s,'restore_post_cook_delegate',lambda:p.wrapper.on_post_cook_delegate.add_callable(p.after_cook))
    d.call(s,'restore_post_processing_delegate',lambda:p.wrapper.on_post_processing_delegate.add_callable(p.after_processing))
    p.watch_tick=d.call(s,'restore_parent_watch',lambda:u.register_slate_post_tick_callback(p.watch))
    r.tick_handle=d.call(s,'resume_existing_native_queue',lambda:u.register_slate_post_tick_callback(r.tick))
    p.write();s['report'].update(retry_dispatched=True,job_id=r.job_id,rebuild_pass_after=r.rebuild_pass,new_network_or_roads_created=False,new_export_Cook=False)

def schedule():
    d.fresh_dispatch_retry=retry
    return d.schedule('fresh_dispatch_retry')
