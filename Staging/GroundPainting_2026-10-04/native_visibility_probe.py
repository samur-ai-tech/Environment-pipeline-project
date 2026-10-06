"""Transient-only overlap inspection. Restore before any save/exit."""
import json,os,datetime
from pathlib import Path
import unreal,geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/GroundPainting_2026-10-04';REV=HERE/'Revision_2026-10-05'
a=json.loads((HERE/'ASSIGNMENT.json').read_text())
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();named=world.get_outermost().get_path_name()
area=next(k for k,v in a['original_maps'].items() if v==named)
fields=dict(t.split('=',1) for t in [s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1].split() if '=' in t)
assert fields['OWNER']=='CODEX_GROUND_PAINTING' and fields['activation']=='GROUND_AUTHORING' and fields['assigned_editor_PID']==str(os.getpid()) and fields['map']==named and fields['operator_thread_id']==a['execution_thread_id']
geocity_runtime_guard.verify();assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
landscapes=[x for x in actors if isinstance(x,unreal.LandscapeProxy)]
target=next(x for x in landscapes if x.get_path_name()==named+'.'+named.split('/')[-1]+':PersistentLevel.'+area+'_landscape')
assert len(landscapes)==2
def state():
 rows=[]
 for x in landscapes:
  t=x.get_actor_transform()
  rows.append({'path':x.get_path_name(),'temporary_hidden':x.is_temporarily_hidden_in_editor(),'hidden_ed':x.is_hidden_ed(),'material':x.get_editor_property('landscape_material').get_path_name(),'transform':{'position':[t.translation.x,t.translation.y,t.translation.z],'rotation':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],'scale':[t.scale3d.x,t.scale3d.y,t.scale3d.z]}})
 return sorted(rows,key=lambda x:x['path'])
def dirty():
 return {'maps':[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'content':sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
out=REV/f'TEMP_VISIBILITY_PID{os.getpid()}.json'
if ARGS['action']=='hide':
 assert not out.exists() and not dirty()['maps']
 before=state();assert all(not r['temporary_hidden'] for r in before)
 record={'pid':os.getpid(),'area':area,'world':named,'target':target.get_path_name(),'before':before,'dirty_before':dirty(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'attempt_started','permanent_visibility_change':False,'save_called':False}
 out.write_text(json.dumps(record,indent=2))
 target.set_is_temporarily_hidden_in_editor(True)
 assert target.is_temporarily_hidden_in_editor() and dirty()==record['dirty_before']
 record['after_hide']=state();record['status']='temporarily_hidden_waiting_capture'
 out.write_text(json.dumps(record,indent=2))
elif ARGS['action']=='restore':
 record=json.loads(out.read_text());assert record['pid']==os.getpid() and record['world']==named and record['target']==target.get_path_name()
 prior=next(r['temporary_hidden'] for r in record['before'] if r['path']==target.get_path_name())
 target.set_is_temporarily_hidden_in_editor(prior)
 assert state()==record['before'] and dirty()==record['dirty_before']
 record['after_restore']=state();record['status']='restored_exactly';record['restore_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 out.write_text(json.dumps(record,indent=2))
else:raise AssertionError('Unknown action')
RESULT={'receipt':str(out),'status':record['status'],'target':target.get_path_name(),'dirty':dirty()}
