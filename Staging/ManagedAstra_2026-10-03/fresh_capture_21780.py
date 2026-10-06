"""Actual saved/reopened Lit captures with explicit Rotator keyword fields."""
import base64,json,math,time,traceback
from types import SimpleNamespace
import fresh_delivery_21780 as d
ACTIVE=[]

def field(value,name):
    values=[v for k,v in value.items() if k.replace('_','').lower()==name.replace('_','').lower()]
    assert len(values)==1;return values[0]

def setup(s,area,verification):
    import unreal as u
    import geocity_roadbld_workflow as native
    from geocity_roadbld_landscape import LandscapeSampler
    d.idle(s);proof=d.read(verification);assert proof['status']=='passed' and proof['stage']=='reopened' and proof['area']==area
    p=d.read(d.PROFILES[area]);c=p['road_provider_contract'];assert c['revision']==proof['revision']
    world=d.call(s,'capture_world',lambda:u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world())
    assert world.get_outermost().get_path_name()==p['map']
    network=d.call(s,'saved_network',lambda:u.load_object(None,c['network_actor_path']));assert network
    before=d.dirty(s);assert not before['maps']
    def guard():
        d.guards();assert u.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
        assert u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()==world
        return world
    sampler=d.call(s,'saved_Landscape_sampler',lambda:LandscapeSampler(SimpleNamespace(guard=guard,plan={'named_map':p['map'],'area_id':area}),saved=True))
    if area=='GazaShujaiya':
        plan=d.read(d.HERE/'TASK2_CAPTURE_PLAN.json')
        shots=[next(x for x in plan['shots'] if x['name']==name) for name in ['curb_street_close','junction_close','ground_close']]
    else:
        # Derive pedestrian poses from a central actual original-source segment.
        choices=[]
        for row in c['source_piece_ledger']:
            pts=row['points_m'];i=len(pts)//2
            if i==0:continue
            a=[pts[i-1][0]*100,pts[i-1][2]*100];b=[pts[i][0]*100,pts[i][2]*100]
            length=math.dist(a,b)
            if length>1:choices.append((math.hypot(*b),row,a,b,length))
        _,row,a,b,length=min(choices,key=lambda x:x[0]);t=[(b[k]-a[k])/length for k in range(2)];n=[-t[1],t[0]];half=row['width_m']*50
        offset=lambda along,lateral:[b[k]+t[k]*along+n[k]*lateral for k in range(2)]
        shots=[{'name':'curb_street_close','eye_xy_cm':offset(-650,half-80),'target_xy_cm':offset(100,half-20),'eye_above_saved_landscape_cm':170,'target_above_saved_landscape_cm':8},
            {'name':'ground_close','eye_xy_cm':offset(-400,half+350),'target_xy_cm':offset(0,half+350),'eye_above_saved_landscape_cm':170,'target_above_saved_landscape_cm':0}]
        trims=c['junction_repair'].get('sourcecontrols_trimproof',[])
        candidates=[]
        for trim in (trims.values() if isinstance(trims,dict) else trims):
            if 'source_endpoint_world_cm' in trim:candidates.append(trim['source_endpoint_world_cm'])
            for item in trim.get('end_trims',trim.get('trims',[])):
                if 'source_endpoint_world_cm' in item:candidates.append(item['source_endpoint_world_cm'])
        if candidates:
            target=min(candidates,key=lambda x:math.hypot(x[0],x[1]))
            shots.append({'name':'junction_close','eye_xy_cm':[target[0]-800,target[1]-600],'target_xy_cm':target[:2],'eye_above_saved_landscape_cm':250,'target_above_saved_landscape_cm':8})
        s['report']['camera_source_piece']=row['piece_id']
    original=d.call(s,'original_camera',u.EditorLevelLibrary.get_level_viewport_camera_info)
    state={'handle':None,'pending':None,'index':0,'camera_time':None,'began':time.monotonic(),'busy':False}
    s['report'].update(status='capturing',area=area,revision=c['revision'],verification=str(verification),shots=[],saved_reopened=True,user_visual_acceptance=False)
    d.write(s['receipt'],s['report'])
    def finish():
        d.call(s,'remove_capture_callback',lambda:u.unregister_slate_post_tick_callback(state['handle']));state['handle']=None
        d.call(s,'restore_camera',lambda:u.EditorLevelLibrary.set_level_viewport_camera_info(*original))
        s['report']['dirty_after']=d.dirty(s);assert s['report']['dirty_after']==before
    def tick(dt):
        if state['busy']:return
        state['busy']=True
        try:
            guard();assert time.monotonic()-state['began']<180
            shot=shots[state['index']]
            if state['camera_time'] is None:
                eye=shot['eye_xy_cm']+[d.call(s,'eye_Landscape_height',lambda:sampler(*shot['eye_xy_cm']))+shot['eye_above_saved_landscape_cm']]
                target=shot['target_xy_cm']+[d.call(s,'target_Landscape_height',lambda:sampler(*shot['target_xy_cm']))+shot['target_above_saved_landscape_cm']]
                delta=[target[i]-eye[i] for i in range(3)];pitch=math.degrees(math.atan2(delta[2],math.hypot(*delta[:2])));yaw=math.degrees(math.atan2(delta[1],delta[0]))
                state['shot']={'name':shot['name'],'intended_camera_cm':eye,'intended_rotation':{'pitch':pitch,'yaw':yaw,'roll':0},'target_cm':target}
                d.call(s,'set_explicit_camera_rotation',lambda:u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(*eye),u.Rotator(pitch=pitch,yaw=yaw,roll=0)))
                d.call(s,'request_Lit',lambda:u.SystemLibrary.execute_console_command(world,'viewmode lit'));state['camera_time']=time.monotonic();return
            if time.monotonic()-state['camera_time']<4:return
            if state['pending'] is None:
                state['pending']=d.call(s,'capture_actual_native_viewport',lambda:native._tool('RoadBLDFeedbackToolset','CaptureViewport',None,'None',network,u.RoadBLDCaptureView.CURRENT,1280,720,1.15,False,1000,False));return
            result=state['pending']
            if not result.is_complete:return
            assert not result.error,str(result.error)
            value=json.loads(d.call(s,'capture_result_JSON',result.get_value_as_json_string));im=field(value,'Image');assert field(im,'MimeType')=='image/png'
            data=base64.b64decode(field(im,'Data'),validate=True);assert data.startswith(b'\x89PNG\r\n\x1a\n')
            actual=[float(field(field(value,'CameraLocation'),k)) for k in ['X','Y','Z']];assert math.dist(actual,state['shot']['intended_camera_cm'])<1
            rotation=field(value,'CameraRotation');assert all(abs((float(field(rotation,k))-v+180)%360-180)<.001 for k,v in state['shot']['intended_rotation'].items())
            assert not field(value,'Warnings')
            target=d.ROOT/'Staging/AppearanceRepair_2026-10-03'/(s['receipt'].stem+'_'+shot['name']+'.png');target.write_bytes(data)
            state['shot'].update(image=str(target),image_sha256=d.hashlib.sha256(data).hexdigest(),actual_camera_cm=actual,actual_rotation=rotation,pixel_review='PENDING')
            s['report']['shots'].append(state['shot']);state.update(index=state['index']+1,pending=None,camera_time=None)
            if state['index']==len(shots):finish();s['report']['status']='captured_pending_pixel_review'
            d.write(s['receipt'],s['report'])
        except Exception:
            s['report'].update(status='stopped',error=traceback.format_exc());finish();d.write(s['receipt'],s['report'])
        finally:state['busy']=False
    ACTIVE.append(state);state['handle']=d.call(s,'register_capture_callback',lambda:u.register_slate_post_tick_callback(tick))

def schedule(area,verification):
    assert not any(s['handle'] is not None for s in ACTIVE)
    name='capture_'+area
    setattr(d,name,lambda s:setup(s,area,verification))
    return d.schedule(name)
