"""Offline AST-only bank lease and parent Landscape authority regressions."""
import ast
import copy
import hashlib
import json
import os
import re
import sys
import types
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
checks=[]
def check(name,fn):
    fn();checks.append({'check':name,'passed':True})
def reject(fn):
    try:fn()
    except (AssertionError,RuntimeError):return
    raise AssertionError('Expected rejection')
def selected(path,names,ns):
    tree=ast.parse(path.read_bytes(),str(path))
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names],type_ignores=[]),str(path),'exec'),ns)
    return tree

action=types.ModuleType('geocity_editor_action')
action.__dict__.update(json=json,os=os,re=re)
selected(ROOT/'Content/Python/geocity_editor_action.py',{'lease_fields','managed_operation_lease'},action.__dict__)
sys.modules['geocity_editor_action']=action
assignment={'manager_thread_id':'manager','tasks':[{'id':'task4','thread_id':'task4'}],'native_area_maps':['/Game/Project/Areas/Test/Map']}
named_map=assignment['native_area_maps'][0]
bank_path='Staging/BankIntegration_2026-10-04/ASSIGNMENT.json'
activation_path='Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json'
scope=['/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4','/Game/Project/Shared/ModelBank/Prepared','/Game/Project/Shared/ModelBank/Materials/BankIntegration_20261004','Named original dependencies/maps']
bank={'schema':'environmentpipeline.bank_integration.v1','thread':'bank','system_owner':'manager','native_save_scope':scope}
activation={'schema':'environmentpipeline.manager_bank_activation.v1','manager_thread_id':'manager','bank_thread_id':'bank','scope_receipt':bank_path,'native_authorized_now':True,'ordinary_generation_authorized':True,'assigned_editor_PID':os.getpid(),'map':named_map,'native_save_scope':scope}
docs={'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json':assignment,bank_path:bank,activation_path:activation}
line=f'OWNER=CODEX_BANK_INTEGRATION manager_thread_id=manager operator_thread_id=bank assigned_editor_PID={os.getpid()} activation=MANAGER_ACTIVATED map={named_map}'
class DocPath:
    def __init__(self,key=''):self.key=key
    def __truediv__(self,key):return DocPath(key)
    def read_text(self,**kwargs):
        return line if self.key.endswith('EDITOR_OWNER.txt') else json.dumps(docs[self.key])
project=DocPath()
def valid_lease():assert action.managed_operation_lease(project,line,named_map)
check('bank generation requires and accepts exact activated identities and scope',valid_lease)
for key,value in [('ordinary_generation_authorized',False),('ordinary_generation_authorized','true'),('native_authorized_now',False),('assigned_editor_PID',os.getpid()+1),('map',named_map+'Wrong'),('manager_thread_id','other'),('bank_thread_id','other'),('scope_receipt','wrong'),('native_save_scope',scope+['/Game/Other'])]:
    def test(key=key,value=value):
        old=activation[key];activation[key]=value
        try:assert not action.managed_operation_lease(project,line,named_map)
        finally:activation[key]=old
    check('bank rejects activation '+key+'='+str(value),test)
for before,after in [('CODEX_BANK_INTEGRATION','CODEX_MANAGED_SYSTEMS_STARTUP'),('MANAGER_ACTIVATED','AWAITING_MANAGER_ACTUAL_PID'),('operator_thread_id=bank','operator_thread_id=other'),('manager_thread_id=manager','manager_thread_id=other'),(f'PID={os.getpid()}',f'PID={os.getpid()+1}'),('map='+named_map,'map=/Game/Other')]:
    check('bank rejects altered lease '+after,lambda before=before,after=after:None if not action.managed_operation_lease(project,line.replace(before,after),named_map) else (_ for _ in ()).throw(AssertionError()))
task4=line.replace('CODEX_BANK_INTEGRATION','CODEX_MANAGED_SYSTEMS_TASK4').replace('operator_thread_id=bank','operator_thread_id=task4')
check('task4 activated path remains valid',lambda:None if action.managed_operation_lease(project,task4,named_map) else (_ for _ in ()).throw(AssertionError()))

ns={'Path':Path,'hashlib':hashlib,'os':os,'json':json}
tree=selected(ROOT/'Content/Python/geocity_bank_workflow.py',{'GeoCityRun','_path','_generation_lease'},ns)
Run=ns['GeoCityRun']
run=Run.__new__(Run)
run.project=project;run.lease_line=line;run.state={'phase':'preflight'};run.p={'map':named_map}
run.profile_path=OUT/'verify_source.py';run.profile_sha256=hashlib.sha256(run.profile_path.read_bytes()).hexdigest()
world=types.SimpleNamespace(get_outermost=lambda:types.SimpleNamespace(get_path_name=lambda:named_map))
class Landscape:
    def __init__(self,name):self.path=named_map+'.Map:PersistentLevel.'+name
    def get_path_name(self):return self.path
    def get_outermost(self):return types.SimpleNamespace(get_path_name=lambda:named_map)
old=Landscape('Prior');current=Landscape('GeoCity_city_v015_PermanentBank_3_999_0_area_landscape_0');unknown=Landscape('Unexpected')
owner=Landscape('HDA')
actors=[old,current,owner]
engine_type=object();actor_type=object()
ns['unreal']=types.SimpleNamespace(UnrealEditorSubsystem=engine_type,EditorActorSubsystem=actor_type,Landscape=Landscape,
    get_editor_subsystem=lambda typ:types.SimpleNamespace(get_editor_world=lambda:world) if typ is engine_type else types.SimpleNamespace(get_all_level_actors=lambda:actors))
# HDA owner is not a native Landscape in real Unreal.
owner=types.SimpleNamespace(get_path_name=lambda:named_map+'.Map:PersistentLevel.HDA',get_outermost=lambda:world.get_outermost())
actors[:]=[old,current,owner]
check('parent guard accepts exact bank generation activation',run.guard)
def blocked_parent():
    activation['ordinary_generation_authorized']=False
    try:reject(run.guard)
    finally:activation['ordinary_generation_authorized']=True
check('direct parent call rejects import-only bank activation',blocked_parent)
def blocked_startup():
    global line
    before=line;line=line.replace('CODEX_BANK_INTEGRATION','CODEX_MANAGED_SYSTEMS_STARTUP');run.lease_line=line
    try:reject(run.guard)
    finally:line=before;run.lease_line=line
check('direct parent call rejects paused startup identity',blocked_startup)

selected(ROOT/'Content/Python/geocity_bank_workflow.py',{'run'},ns)
runtime=types.ModuleType('geocity_runtime_guard');runtime.verify=lambda:None
sys.modules['geocity_runtime_guard']=runtime
public_profile=OUT/'PublicRunProfile.json'
public_profile.write_text(json.dumps({'map':named_map}))
ns['unreal'].Paths=types.SimpleNamespace(project_dir=lambda:'PROJECT_FIXTURE',convert_relative_path_to_full=lambda value:value)
def public_rejected():
    activation['ordinary_generation_authorized']=False
    events=[];ns['ACTIVE']=[];ns['GeoCityRun']=lambda *args:events.append('constructor/history') or run
    ns['Path']=lambda value:project if value=='PROJECT_FIXTURE' else Path(value)
    run.fail=lambda *args:events.append('cleanup')
    run.start=lambda *args:events.append('start')
    try:
        reject(lambda:ns['run'](public_profile))
        assert not events and not ns['ACTIVE']
    finally:activation['ordinary_generation_authorized']=True;ns['GeoCityRun']=Run;ns['Path']=Path
check('public run rejects content-only bank before construction/history, Engine cleanup or registration',public_rejected)
def public_startup_rejected():
    global line
    before=line;line=line.replace('CODEX_BANK_INTEGRATION','CODEX_MANAGED_SYSTEMS_STARTUP')
    try:public_rejected()
    finally:line=before
check('public run rejects startup before construction/history, Engine cleanup or registration',public_startup_rejected)
def public_allowed():
    events=[];ns['ACTIVE']=[];ns['GeoCityRun']=lambda *args:run
    ns['Path']=lambda value:project if value=='PROJECT_FIXTURE' else Path(value)
    run.start=lambda *args:events.append('start')
    try:
        ns['run'](public_profile)
        assert events==['start'] and ns['ACTIVE']==[run]
    finally:ns['GeoCityRun']=Run;ns['Path']=Path
check('public run proceeds only after valid bank generation guard',public_allowed)

run.p['source']=str(OUT/'verify_source.py')
source_sha=hashlib.sha256(Path(run.p['source']).read_bytes()).hexdigest()
run.started_epoch=123.5;run.native_road_phase='authoring';run.state['phase']='native_road_authoring'
run.previous_baked_paths=[old.path]
run.state['previous_landscape_accounting']={'source':run.p['source'],'source_sha256':source_sha,'unaccounted_actor_paths':[], 'hda_actor_path':owner.get_path_name(),'live_actor_paths':[old.path]}
run.native_road_export={'area_id':'Test','source_sha256':source_sha,'centreline_sha256':'a'*64}
run.wrapper=types.SimpleNamespace(get_houdini_asset_actor=lambda:owner)
calls=[]
run.official_landscapes=lambda w:calls.append(w) or {current.path:current}
run.write=lambda:None
def authority():
    result=run.current_road_landscape_authority()
    assert result['actor'] is current and calls==[run.wrapper]
    assert result['evidence']['current_actor_path']==current.path
    assert result['evidence']['accounted_previous_landscape_paths']==[old.path]
    assert not hasattr(run,'cooked_landscape')
check('fresh official output works without paint-wait field and with landscape_0 suffix',authority)
def unexpected():
    actors.append(unknown)
    try:reject(run.current_road_landscape_authority)
    finally:actors.remove(unknown)
check('unknown loaded Landscape rejects road authoring',unexpected)
for bound in ({},{old.path:old,current.path:current}):
    def test(bound=bound):
        saved=run.official_landscapes;run.official_landscapes=lambda w:bound
        try:reject(run.current_road_landscape_authority)
        finally:run.official_landscapes=saved
    check('missing or multiple current official Landscapes reject',test)
def changed_source():
    run.native_road_export['source_sha256']='wrong'
    try:reject(run.current_road_landscape_authority)
    finally:run.native_road_export['source_sha256']=source_sha
check('source digest must match prior accounting and completed export',changed_source)
def unaccounted_prior():
    run.previous_baked_paths=[]
    try:reject(run.current_road_landscape_authority)
    finally:run.previous_baked_paths=[old.path]
check('prior paths must be owned by retained lifecycle ledger',unaccounted_prior)

builds=[]
provider=types.ModuleType('geocity_roadbld_workflow')
provider.build=lambda *args,**kwargs:builds.append(kwargs) or object()
sys.modules['geocity_roadbld_workflow']=provider
ns['unreal'].EditorLoadingAndSavingUtils=types.SimpleNamespace(get_dirty_map_packages=lambda:[],get_dirty_content_packages=lambda:[])
run.api=types.SimpleNamespace(is_asset_cooking_paused=lambda:True)
def begin():
    run.native_road_phase='export';run.state['phase']='cooked_verified';calls.clear()
    run.begin_native_roads({'roadbld_centerlines':run.native_road_export})
    assert len(calls)==1 and len(builds)==1
    assert builds[0]['landscape_authority'].__self__ is run
    assert builds[0]['landscape_authority']()['actor'] is current
check('begin roads resolves freshly before build and passes bound callback',begin)
def begin_unknown():
    run.native_road_phase='export';run.state['phase']='cooked_verified';actors.append(unknown)
    try:reject(lambda:run.begin_native_roads({'roadbld_centerlines':run.native_road_export}))
    finally:actors.remove(unknown)
    assert len(builds)==1
check('unknown Landscape prevents provider build',begin_unknown)

# Execute task2 pure selector with this real parent method and fake Unreal objects.
road_ns={'Path':Path,'hashlib':hashlib,'os':os,'json':json,'unreal':ns['unreal']}
selected(ROOT/'Content/Python/geocity_roadbld_landscape.py',{'_current_landscape'},road_ns)
ns['unreal'].load_object=lambda _,path:next((a for a in actors if a.get_path_name()==path),None)
native=types.SimpleNamespace(landscape_authority=run.current_road_landscape_authority,_landscape_authority_parent=run,
    lease_line=line,plan={'named_map':named_map,**run.native_road_export},p=run.p,_current_landscape_evidence=None,_current_landscape_actor=None,state={})
run.native_road_run=native
def integrated():
    assert road_ns['_current_landscape'](native,world,actors) is current
    assert road_ns['_current_landscape'](native,world,actors) is current
    assert native.state['current_landscape_authority']==run.state['current_road_landscape_authority']
check('task2 consumer accepts real parent callback evidence and revalidation',integrated)
for path in ('Content/Python/geocity_editor_action.py','Content/Python/geocity_bank_workflow.py'):
    compile((ROOT/path).read_bytes(),str(ROOT/path),'exec')
checks.append({'check':'changed Python sources compile under Unreal bundled Python','passed':True})
(OUT/'SOURCE_CHECKS.json').write_text(json.dumps({'checks':checks,'passed':len(checks),'unreal_imported':False,'native_execution':False,'resealed':False},indent=2)+'\n')
print(json.dumps({'passed':len(checks),'receipt':str(OUT/'SOURCE_CHECKS.json')}))
