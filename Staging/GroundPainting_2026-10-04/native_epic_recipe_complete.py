"""Complete exactly20 remaining controls; actual full readback is authoritative."""
import json,types,hashlib,os,datetime
from pathlib import Path
import unreal
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();here=root/'Staging/GroundPainting_2026-10-04';rev=here/'Revision_2026-10-05'
f=here/'native_ground_epic_integration.py';assert hashlib.sha256(f.read_bytes()).hexdigest()=='19d99d44b31ca2027a3d814c76dd5ab1ff6d17dd44578cd2a55ad880a9d3a5c0'
e=types.ModuleType('epic_recipe_complete_definitions');e.__file__=str(f);exec(compile(f.read_bytes(),str(f),'exec'),e.__dict__);h,p,_=e.load_definitions();p.sole_editor();assert os.getpid()==ARGS['expected_pid']==32464
partial_file=rev/'EPIC_PARTIAL_READ_ONLY_PID32464.json';assert h.sha(partial_file)=='85fd33b23842031f3f8ef4e80ce0f012cc56c1272ceecdc8857e1577564ca44f';partial=json.loads(partial_file.read_text())
failed_file=rev/'EPIC_GROUND_apply_GazaShujaiya_r027_direct_sources_PID32464.json';assert h.sha(failed_file)==partial['failure_receipt_sha256'];failed=json.loads(failed_file.read_text())
plan=failed['plan'];assert failed['status']=='FAILED_PARTIAL_STATE_PRESERVED'
review_file=Path(ARGS['review_receipt']).resolve(strict=True);assert review_file.parent==rev and h.sha(review_file)==ARGS['review_receipt_sha256'];review=json.loads(review_file.read_text());assert review['status']=='APPROVED_EPIC_RECIPE_COMPLETION' and review['helper_sha256']==h.sha(here/'native_epic_recipe_complete.py') and review['partial_receipt_sha256']==h.sha(partial_file)
assignment=json.loads((here/'ASSIGNMENT.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name();assert world==partial['world']
master=unreal.load_asset(h.MASTER);child=unreal.load_asset(assignment['material_contract']['area_instances']['GazaShujaiya']);child_path=h.path(child)
def snap():
 sources,actors=h.guard(assignment,world,True)
 return {'sources':sources,'scene':h.scene_state(actors),'nodes':{h.path(x):h.describe(master,x) for x in h.LIB.get_material_expressions(master)},'instances':{k:h.material_state(master,unreal.load_asset(k)) for k in failed['before']['instances']},'disk':{k:h.sha(k) for k in failed['before']['disk']},'cvars':{k:unreal.SystemLibrary.get_console_variable_string_value(k) for k in p.CVARS},'dirty':{'maps':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),'content':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}}
before=snap();assert before==partial['state'];assert before['nodes']==e.expected_graph(h,failed['before']['nodes'],h.path(master))
e.compare_instances(h,failed['before']['instances'],before['instances'],child_path,{'textures':{'Sand_01_Albedo':plan['textures']['Sand_01_Albedo']},'scalars':{},'vectors':{}})
once=rev/'EPIC_RECIPE_COMPLETE_ONCE_PID32464.json';assert not once.exists();once.write_text(json.dumps({'helper_sha256':h.sha(here/'native_epic_recipe_complete.py'),'partial_sha256':h.sha(partial_file)}))
out=rev/'EPIC_RECIPE_COMPLETED_PID32464.json';assert not out.exists()
result={'status':'STARTED','pid':os.getpid(),'world':world,'area':'GazaShujaiya','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before':before,'original_before':failed['before'],'plan':plan,'helper_sha256':h.sha(here/'native_epic_recipe_complete.py'),'partial_receipt_sha256':h.sha(partial_file),'review_receipt_sha256':h.sha(review_file),'setter_returns':[],'graph_mutation':False,'explicit_save_or_compile':False}
out.write_text(json.dumps(result,indent=2))
try:
 for k,v in plan['textures'].items():
  if k=='Sand_01_Albedo':continue
  value=unreal.load_asset(v);assert isinstance(value,unreal.Texture2D)
  returned=h.LIB.set_material_instance_texture_parameter_value(child,k,value)
  result['setter_returns'].append({'parameter':k,'returned':h.plain(returned)})
  assert h.path(h.LIB.get_material_instance_texture_parameter_value(child,k))==v,k
 for k,v in plan['scalars'].items():
  returned=h.LIB.set_material_instance_scalar_parameter_value(child,k,v);result['setter_returns'].append({'parameter':k,'returned':h.plain(returned)})
  assert h.LIB.get_material_instance_scalar_parameter_value(child,k)==e.float32(v),k
 for k,v in plan['vectors'].items():
  returned=h.LIB.set_material_instance_vector_parameter_value(child,k,unreal.LinearColor(*v));result['setter_returns'].append({'parameter':k,'returned':h.plain(returned)})
  assert h.plain(h.LIB.get_material_instance_vector_parameter_value(child,k))==[e.float32(x) for x in v],k
 assert len(result['setter_returns'])==20
 h.LIB.update_material_instance(child)
 after=snap();result['after']=after
 assert all(after[k]==before[k] for k in before if k not in ('instances','dirty'))
 e.compare_instances(h,failed['before']['instances'],after['instances'],child_path,plan)
 assert after['dirty']==before['dirty']
 result['status']='EPIC_RECIPE_COMPLETED_FULL_READBACK_NO_SAVE';result['full_21_control_readback_passed']=True
except Exception as error:
 result['status']='FAILED_PARTIAL_STATE_PRESERVED';result['error']=repr(error);result['failure_state']=snap();raise
finally:out.write_text(json.dumps(result,indent=2))
RESULT={'receipt':str(out),'sha256':h.sha(out),'status':result['status'],'dirty':result['after']['dirty'],'setter_returns':result['setter_returns']}
