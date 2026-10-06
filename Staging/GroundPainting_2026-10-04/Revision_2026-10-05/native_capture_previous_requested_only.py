"""Matched Lit native viewport evidence, without scene-content edits."""
import datetime,json,math,os
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text());area=next(k for k,v in assignment['original_maps'].items() if v==world.get_outermost().get_path_name())
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
assert f'assigned_editor_PID={os.getpid()}' in lease and 'OWNER=CODEX_GROUND_PAINTING' in lease
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
landscapes=[a for a in actors if isinstance(a,unreal.Landscape)]
target=[a for a in landscapes if a.get_name().startswith('GeoCity_')]
landscape=target[0] if len(target)==1 else landscapes[0]
ignored=[a for a in actors if a!=landscape]
def height(x,y):
 hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,100000),unreal.Vector(x,y,-100000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignored,unreal.DrawDebugTrace.NONE,False)
 f=hit.to_dict();assert f['blocking_hit'] and not f['initial_overlap'] and f['hit_actor']==landscape
 assert isinstance(f['hit_component'],unreal.LandscapeHeightfieldCollisionComponent) and f['hit_component'].get_owner()==landscape
 return float(f['impact_point'].z)
camera_path=HERE/f'CAMERAS_{area}.json'
if camera_path.exists():cameras=json.loads(camera_path.read_text())
else:
 x,y=-1268.1745794274116,2408.9167042506506;z=height(x,y)
 cameras={'close':{'eye':[-1518.2358806223988,2096.7158944428124,height(-1518.2358806223988,2096.7158944428124)+170], 'target':[x,y,z],'fov':65},
          'middle':{'eye':[x-7000,y-9000,z+8000],'target':[x,y,z],'fov':65},
          'wide':{'eye':[-31348.5971,-31348.5971,height(0,0)+45597.9594],'target':[0,0,height(0,0)],'fov':65}}
 camera_path.write_text(json.dumps(cameras,indent=2),encoding='utf-8')
shot=ARGS['shot'];stage=ARGS['stage'];v=cameras[shot]
eye=unreal.Vector(*v['eye']);target=unreal.Vector(*v['target']);dx,dy,dz=target.x-eye.x,target.y-eye.y,target.z-eye.z
rotation=unreal.Rotator(pitch=math.degrees(math.atan2(dz,math.hypot(dx,dy))),yaw=math.degrees(math.atan2(dy,dx)),roll=0)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);key=level.get_active_viewport_config_key()
unreal.SystemLibrary.execute_console_command(world,'viewmode lit')
level.set_level_viewport_camera_info(eye,rotation,key);level.set_level_viewport_fov(v['fov'],key);level.editor_invalidate_viewports()
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(eye,rotation)
level.editor_invalidate_viewports()
out=HERE/'Images'/f'{area}_{stage}_{shot}.png';out.parent.mkdir(exist_ok=True)
assert not out.exists(),'Preserve prior capture'
task=unreal.AutomationLibrary.take_high_res_screenshot(1600,1000,str(out),delay=2.0,force_game_view=True)
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'area':area,'stage':stage,'shot':shot,'camera':v,'rotation':[rotation.pitch,rotation.yaw,rotation.roll],'viewmode':'Lit','path':str(out),'requested':True,'valid_task':bool(task and task.is_valid_task())}
(HERE/f'CAPTURE_{area}_{stage}_{shot}.json').write_text(json.dumps(result,indent=2),encoding='utf-8');RESULT=result
