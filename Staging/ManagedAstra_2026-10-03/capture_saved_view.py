"""Delivery-owned, explicit single-view capture; import performs no editor action.

After activation and successful saved/reopen checks:
    capture('ground_close', verification_receipt_path)
The caller reviews each actual image before selecting the next pose.
"""
import base64
import datetime
import hashlib
import json
import math
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ACTIVE_CAPTURES = []

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def field(value, name):
    key = lambda s: s.replace('_', '').lower()
    if isinstance(value, dict):
        matches = [v for k,v in value.items() if key(k)==key(name)]
        assert len(matches)==1, 'Missing/ambiguous capture field '+name
        return matches[0]
    import geocity_roadbld_workflow as native
    return native._get(value, name)

def capture(shot_name, verification_path):
    import unreal
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    assignment = read(HERE/'ASSIGNMENTS.json')
    assert assignment['tasks']['task2_delivery']['editor_calls_authorized']
    assert assignment['editor_writer_thread_id']=='01a102e1-25e6-7f13-b593-4988290a283b'
    assert not any(item['handle'] is not None for item in ACTIVE_CAPTURES)
    lease_path=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
    lease=lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
    assert 'worker_thread_id=01a102e1-25e6-7f13-b593-4988290a283b' in lease
    assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and ('assigned_editor_PID='+str(os.getpid())) in lease
    plan=read(HERE/'TASK2_CAPTURE_PLAN.json')
    shot=next(row for row in plan['shots'] if row['name']==shot_name)
    verification=read(verification_path)
    assert verification['phase']=='passed' and verification['area']==plan['area']
    assert verification['saved_native_receipt']['status']=='passed'
    assert verification['reopened_native_receipt']['status']=='passed'
    assert verification['reopened_native_receipt']['reopened_binding_readback_verified']
    delivery=read(ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/ROADBLD_DELIVERY.json')
    assert delivery['saved'] and delivery['revision']==plan['road_proof_revision']
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_path_name()==plan['named_map']
    landscape=[a for a in actors if isinstance(a,unreal.Landscape)]
    assert len(landscape)==1
    network=unreal.load_object(None,delivery['network_actor_path'])
    assert network and not network.is_road_network_stale()
    ignored=[a for a in actors if a!=landscape[0]]
    api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
    dirty_before={x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
    dependencies=set(delivery['named_generated_dependency_paths'])
    def guard():
        assert lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]==lease
        assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()==world
        assert api.is_asset_cooking_paused()
        assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
        assert all(x.tick_handle is None for x in native.ACTIVE)
        assert plan['named_map'] not in {x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()}
        dirty={x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
        assert not dependencies.intersection(dirty) and dirty==dirty_before
    guard()
    def height(xy):
        hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(*xy,100000),unreal.Vector(*xy,-100000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignored,unreal.DrawDebugTrace.NONE,False)
        assert hit is not None
        values=hit.to_dict()
        assert values['blocking_hit'] and not values['initial_overlap'] and values['hit_actor']==landscape[0]
        return float(values['impact_point'].z)
    target=shot['target_xy_cm']+[height(shot['target_xy_cm'])+shot['target_above_saved_landscape_cm']]
    if shot_name=='area_overview':
        eye=shot['eye_xy_cm']+[target[2]+shot['eye_above_saved_landscape_cm']]
    else:
        eye=shot['eye_xy_cm']+[height(shot['eye_xy_cm'])+shot['eye_above_saved_landscape_cm']]
    delta=[target[i]-eye[i] for i in range(3)]
    yaw=math.degrees(math.atan2(delta[1],delta[0]))
    pitch=math.degrees(math.atan2(delta[2],math.hypot(delta[0],delta[1])))
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    image_path=ROOT/'Staging/AppearanceRepair_2026-10-03'/('SHUJ_SAVED_LIT_'+shot_name+'_'+stamp+'.png')
    status_path=image_path.with_suffix('.json')
    assert not image_path.exists() and not status_path.exists()
    state={'handle':None,'pending':None,'began':time.monotonic(),'camera_time':None,'busy':False}
    report=dict(phase='scheduled',shot=shot,verification_path=str(verification_path),revision=delivery['revision'],
        intended_camera_cm=eye,intended_rotation={'pitch':pitch,'yaw':yaw,'roll':0},target_cm=target,
        landscape_path=landscape[0].get_path_name(),view_mode_requested='Lit',image=str(image_path),
        no_rebuild=True,no_cook=True,no_package_save=True,pixel_review='PENDING')
    def write():
        status_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    def stop():
        if state['handle'] is not None:
            unreal.unregister_slate_post_tick_callback(state['handle'])
            state['handle']=None
    def tick(dt):
        if state['busy']:
            return
        state['busy']=True
        try:
            guard()
            assert time.monotonic()-state['began']<90, 'Capture timed out'
            if state['camera_time'] is None:
                unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(*eye),unreal.Rotator(pitch,yaw,0))
                unreal.SystemLibrary.execute_console_command(world,'viewmode lit')
                state['camera_time']=time.monotonic()
                report['phase']='settling_camera';write();return
            if time.monotonic()-state['camera_time']<3:
                return
            if state['pending'] is None:
                state['pending']=native._tool('RoadBLDFeedbackToolset','CaptureViewport',None,'None',network,
                    unreal.RoadBLDCaptureView.CURRENT,1280,720,1.15,False,1000,False)
                report['phase']='capturing_native_viewport';write();return
            result=state['pending']
            if not result.is_complete:
                return
            assert not result.error,str(result.error)
            value=json.loads(result.get_value_as_json_string())
            image_value=field(value,'Image')
            assert field(image_value,'MimeType')=='image/png'
            pixels=base64.b64decode(field(image_value,'Data'),validate=True)
            assert pixels.startswith(b'\x89PNG\r\n\x1a\n')
            camera=field(value,'CameraLocation')
            actual=[float(field(camera,axis)) for axis in ('X','Y','Z')]
            assert math.dist(actual,eye)<1, 'Native capture used a different camera'
            warnings=field(value,'Warnings')
            assert not warnings,'Native capture warnings: '+str(warnings)
            image_path.write_bytes(pixels)
            report.update(phase='captured_pending_pixel_review',camera_location_cm=actual,
                camera_rotation=field(value,'CameraRotation'),warnings=warnings,image_bytes=len(pixels),
                image_sha256=hashlib.sha256(pixels).hexdigest())
            stop();write()
        except Exception as exc:
            report.update(phase='failed',error=repr(exc));stop();write()
        finally:
            state['busy']=False
    write()
    ACTIVE_CAPTURES.append(state)
    state['handle']=unreal.register_slate_post_tick_callback(tick)
    return {'scheduled':True,'status':str(status_path),'image':str(image_path)}
