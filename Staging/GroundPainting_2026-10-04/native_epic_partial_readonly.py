"""Read the exact preserved Epic partial state and reflected setter docs."""
import json,types,hashlib,os
from pathlib import Path
import unreal
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();here=root/'Staging/GroundPainting_2026-10-04';rev=here/'Revision_2026-10-05'
f=here/'native_ground_epic_integration.py';assert hashlib.sha256(f.read_bytes()).hexdigest()=='19d99d44b31ca2027a3d814c76dd5ab1ff6d17dd44578cd2a55ad880a9d3a5c0'
e=types.ModuleType('epic_partial_definitions');e.__file__=str(f);exec(compile(f.read_bytes(),str(f),'exec'),e.__dict__);h,p,_=e.load_definitions();p.sole_editor();assert os.getpid()==ARGS['expected_pid']==32464
failed_file=rev/'EPIC_GROUND_apply_GazaShujaiya_r027_direct_sources_PID32464.json';failed=json.loads(failed_file.read_text());assert failed['status']=='FAILED_PARTIAL_STATE_PRESERVED'
assignment=json.loads((here/'ASSIGNMENT.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name();assert world==failed['world']
master=unreal.load_asset(h.MASTER)
def snap():
 sources,actors=h.guard(assignment,world,True)
 return {'sources':sources,'scene':h.scene_state(actors),'nodes':{h.path(x):h.describe(master,x) for x in h.LIB.get_material_expressions(master)},'instances':{k:h.material_state(master,unreal.load_asset(k)) for k in failed['before']['instances']},'disk':{k:h.sha(k) for k in failed['before']['disk']},'cvars':{k:unreal.SystemLibrary.get_console_variable_string_value(k) for k in p.CVARS},'dirty':{'maps':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),'content':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}}
s=snap();assert s['dirty']==failed['failure_dirty'];assert s['nodes']==e.expected_graph(h,failed['before']['nodes'],h.path(master))
assert all(s[k]==failed['before'][k] for k in ('sources','scene','disk','cvars'))
assert snap()==s
docs={k:getattr(h.LIB,k).__doc__ for k in ('set_material_instance_texture_parameter_value','set_material_instance_scalar_parameter_value','set_material_instance_vector_parameter_value')}
out=rev/'EPIC_PARTIAL_READ_ONLY_PID32464.json';assert not out.exists()
out.write_text(json.dumps({'status':'PRESERVED_APPROVED_GRAPH_PATCH_READ_ONLY','pid':os.getpid(),'world':world,'failure_receipt_sha256':h.sha(failed_file),'state':s,'setter_api_docs':docs,'native_mutation':False},indent=2))
RESULT={'receipt':str(out),'sha256':h.sha(out),'docs':docs,'changed_mi_values':{k:{q:{n:t for n,t in v[q].items() if t!=failed['before']['instances'][k][q].get(n)} for q in ('textures','scalars','vectors')} for k,v in s['instances'].items()},'dirty':s['dirty']}
