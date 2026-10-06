"""Explicit manager-authorized diagnostic camera captures; import is inert."""
import base64,datetime,hashlib,json,math,os,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ACTIVE=[]
def field(v,name):
    key=lambda s:s.replace('_','').lower()
    if isinstance(v,dict):
        found=[x for k,x in v.items() if key(k)==key(name)];assert len(found)==1,(name,list(v));return found[0]
    import geocity_roadbld_workflow as n
    return n._get(v,name)
def schedule():
    import unreal
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_clip as clip
    import geocity_roadbld_junctions as junctions
    p=bank.ACTIVE[-1];r=native.ACTIVE[-1];p.guard();r.guard();p.guard_processes()
    assert os.getpid()==32752 and 'worker_thread_id=01a102e1-25e6-7f13-b593-4988290a283b' in p.lease_line
    assert r.state['phase']=='failed_validating' and r.revision=='20261003T172549017159'
    assert not any(s['handle'] for s in ACTIVE)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_path_name()==r.plan['named_map']
    assert r.landscape_sampler.path==r.grounding_report['landscape_actor_path']
    dirty=lambda:dict(maps=sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),content=sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
    dirty_before=dirty()
    def bindings():
        return [{'component':c.get_path_name(),'mesh':native._path(c.static_mesh),'transform':clip._transform(c.get_world_transform()),'materials':clip._materials(c)} for a in r.native_geos() for c in a.get_components_by_class(unreal.StaticMeshComponent)]
    before=bindings();owned=junctions._owned_state(r);checkpoint=junctions._sha(r.junction_repair)
    original=unreal.EditorLevelLibrary.get_level_viewport_camera_info();assert original and len(original)==2
    loc,rot=original
    camera_before={'location_cm':[float(loc.x),float(loc.y),float(loc.z)],'rotation':[float(rot.pitch),float(rot.yaw),float(rot.roll)]}
    def guard():
        p.guard();r.guard()
        assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()==world
        assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
        assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
        assert p.api.is_asset_cooking_paused() and p.api.is_session_valid()
        assert not p.autosave_settings.get_editor_property('bAutoSaveEnable')
        assert r.state['phase']=='failed_validating' and not r.network.is_road_network_stale()
        assert dirty()==dirty_before
    guard()
    plan=json.loads((HERE/'TASK2_CAPTURE_PLAN.json').read_text())
    shots=[dict(next(s for s in plan['shots'] if s['name']==name)) for name in ['curb_street_close','pad_margin_close']]
    shots.append({'name':'source1096660488_pad_conflict','eye_xy_cm':[-15700,-16550],'target_xy_cm':[-13650,-14650],
        'eye_above_saved_landscape_cm':2400,'target_above_saved_landscape_cm':30,'purpose':'Two protected-pad/source-road conflicts; diagnosis only.','coordinate_basis':{'road':'DynamicRoad_41','source_osm_id':'1096660488','pad_ids':['298979086','301838006']}})
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_UNSAVED_CURRENT_CANDIDATE_LIT_'+stamp+'.json')
    status_path=HERE/'TASK2_UNSAVED_CANDIDATE_CAPTURE_STATUS.json'
    report={'phase':'scheduled','label':'UNSAVED_CURRENT_CANDIDATE','pid':os.getpid(),'world':world.get_path_name(),'revision':r.revision,
        'landscape_path':r.landscape_sampler.path,'height_basis':'Existing exact current-export Landscape-only sampler',
        'camera_before':camera_before,'dirty_before':dirty_before,'bound_components_before':before,'owned_participants_before':owned,
        'junction_checkpoint_sha256':checkpoint,'workflow_callbacks':0,'Engine_paused':True,'Engine_session_valid':True,
        'map_saved':False,'saved_reopen_acceptance':False,'no_cook_rebuild_graph_evaluation_geometry_material_edit_or_helper_reload':True,'shots':[]}
    state={'handle':None,'index':0,'pending':None,'camera_time':None,'began':time.monotonic(),'busy':False}
    def write():
        receipt.write_text(json.dumps(report,indent=2)+'\n')
        status_path.write_text(json.dumps({'phase':report['phase'],'receipt':str(receipt),'shots_complete':len(report['shots']),'error':report.get('error')},indent=2)+'\n')
    def stop():
        if state['handle'] is not None:unreal.unregister_slate_post_tick_callback(state['handle']);state['handle']=None
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc,rot)
        now=unreal.EditorLevelLibrary.get_level_viewport_camera_info()
        report['camera_restored']=math.dist([now[0].x,now[0].y,now[0].z],camera_before['location_cm'])<.001 and max(abs(a-b) for a,b in zip([now[1].pitch,now[1].yaw,now[1].roll],camera_before['rotation']))<.001
        report['bound_components_unchanged']=bindings()==before
        report['participants_unchanged']=junctions._owned_state(r)==owned
        report['junction_checkpoint_unchanged']=junctions._sha(r.junction_repair)==checkpoint
        report['dirty_packages_unchanged']=dirty()==dirty_before
        report['capture_callback_removed']=state['handle'] is None
    def tick(dt):
        if state['busy']:return
        state['busy']=True
        try:
            guard();assert time.monotonic()-state['began']<150
            shot=shots[state['index']]
            if state['camera_time'] is None:
                eye=shot['eye_xy_cm']+[r.landscape_sampler(*shot['eye_xy_cm'])+shot['eye_above_saved_landscape_cm']]
                target=shot['target_xy_cm']+[r.landscape_sampler(*shot['target_xy_cm'])+shot['target_above_saved_landscape_cm']]
                delta=[target[i]-eye[i] for i in range(3)]
                pitch=math.degrees(math.atan2(delta[2],math.hypot(*delta[:2])));yaw=math.degrees(math.atan2(delta[1],delta[0]))
                state['shot']={'name':shot['name'],'purpose':shot['purpose'],'coordinate_basis':shot.get('coordinate_basis'),
                    'label':'UNSAVED_CURRENT_CANDIDATE','intended_camera_cm':eye,'target_cm':target,'requested_viewmode':'Lit',
                    'intended_rotation':{'pitch':pitch,'yaw':yaw,'roll':0}}
                unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(*eye),unreal.Rotator(pitch=pitch,yaw=yaw,roll=0))
                unreal.SystemLibrary.execute_console_command(world,'viewmode lit')
                state['camera_time']=time.monotonic();report['phase']='settling_'+shot['name'];write();return
            if time.monotonic()-state['camera_time']<4:return
            if state['pending'] is None:
                state['pending']=native._tool('RoadBLDFeedbackToolset','CaptureViewport',None,'None',r.network,unreal.RoadBLDCaptureView.CURRENT,1280,720,1.15,False,1000,False)
                report['phase']='capturing_'+shot['name'];write();return
            result=state['pending']
            if not result.is_complete:return
            assert not result.error,str(result.error)
            value=json.loads(result.get_value_as_json_string());im=field(value,'Image');assert field(im,'MimeType')=='image/png'
            pixels=base64.b64decode(field(im,'Data'),validate=True);assert pixels.startswith(b'\x89PNG\r\n\x1a\n')
            actual=[float(field(field(value,'CameraLocation'),k)) for k in ['X','Y','Z']]
            assert math.dist(actual,state['shot']['intended_camera_cm'])<1
            actual_rotation=field(value,'CameraRotation')
            assert all(abs((float(field(actual_rotation,k))-v+180)%360-180)<.001 for k,v in state['shot']['intended_rotation'].items()),'Captured rotation differs from intended'
            assert not field(value,'Warnings'),str(field(value,'Warnings'))
            path=receipt.parent/('SHUJ_UNSAVED_CURRENT_CANDIDATE_LIT_'+shot['name']+'_'+stamp+'.png');path.write_bytes(pixels)
            state['shot'].update(image=str(path),image_sha256=hashlib.sha256(pixels).hexdigest(),actual_camera_cm=actual,camera_rotation=field(value,'CameraRotation'),warnings=field(value,'Warnings'),pixel_review='PENDING')
            report['shots'].append(state['shot']);state['index']+=1;state['pending']=None;state['camera_time']=None
            if state['index']==len(shots):
                stop();guard();assert all(report[k] for k in ['camera_restored','bound_components_unchanged','participants_unchanged','junction_checkpoint_unchanged','dirty_packages_unchanged'])
                report['phase']='THREE_CAPTURES_COMPLETE_PENDING_PIXEL_REVIEW';write();return
            write()
        except Exception:
            report['phase']='FAILED';report['error']=traceback.format_exc();stop();write()
        finally:state['busy']=False
    write();ACTIVE.append(state);state['handle']=unreal.register_slate_post_tick_callback(tick)
    return {'scheduled':True,'receipt':str(receipt)}
