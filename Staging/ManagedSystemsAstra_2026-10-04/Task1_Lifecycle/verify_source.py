"""Offline regressions: AST-selected source only; never import Unreal/providers."""
import ast
import copy
import datetime
import hashlib
import json
import os
import re
import time
import types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
results=[]
def check(name,fn):
    fn()
    results.append({'check':name,'passed':True})
def rejected(fn):
    try:fn()
    except (AssertionError,RuntimeError):return
    raise AssertionError('Expected fail-closed rejection')
def load_nodes(path,predicate,namespace):
    tree=ast.parse(path.read_bytes(),str(path))
    selected=[node for node in tree.body if predicate(node)]
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
    return tree

bank_path=ROOT/'Content/Python/geocity_bank_workflow.py'
ns={'json':json,'Path':Path,'time':time,'datetime':datetime,'os':os,'hashlib':hashlib,'re':re}
tree=load_nodes(bank_path,lambda n:isinstance(n,(ast.FunctionDef,ast.ClassDef)) or
                isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RUNTIME_PROFILE_FIELDS' for t in n.targets),ns)
merge=ns['_runtime_profile_merge']
profile={'root':'/Game/Project/Areas/GazaShujaiya/BankIntegration_v015','landscape_grass':{'enabled':True},
         'landscape_material':'original','road_provider':'houdini','roadbld_workflow':{'status':'pending','settings':{'held':True}},
         'bank_fields':{'held':['H0013','H0907']}}
def profile_allowed():
    proposed=copy.deepcopy(profile)
    proposed['road_provider']='RoadBLD'
    proposed['road_provider_contract']={'saved':True,'token':'fixture'}
    proposed['roadbld_workflow']['status']='native_generated_saved_verified'
    proposed['landscape_material']=profile['root']+'/Materials/MI_GeoCityGround.MI_GeoCityGround'
    merged,diff=merge(profile,copy.deepcopy(profile),proposed)
    assert len(diff)==4 and merged['bank_fields']==profile['bank_fields']
    assert merged['roadbld_workflow']['settings']==profile['roadbld_workflow']['settings']
check('runtime allowlist preserves bank and provider settings',profile_allowed)
for label,change in [('bank',lambda p:p['bank_fields'].update(held=[])),
                     ('road settings',lambda p:p['roadbld_workflow']['settings'].update(held=False)),
                     ('material outside area',lambda p:p.update(landscape_material='/Game/Other.Asset'))]:
    proposed=copy.deepcopy(profile);change(proposed)
    check('reject unowned '+label,lambda proposed=proposed:rejected(lambda:merge(profile,profile,proposed)))
current=copy.deepcopy(profile);current['bank_fields']['new']=1
check('reject concurrent profile edit',lambda:rejected(lambda:merge(profile,current,profile)))

action_ns={'json':json,'os':os,'re':re}
load_nodes(ROOT/'Content/Python/geocity_editor_action.py',lambda n:isinstance(n,ast.FunctionDef) and n.name in
           ('lease_fields','managed_operation_lease','persistent_profiles'),action_ns)
assignment={'manager_thread_id':'manager','tasks':[{'id':'task4','thread_id':'operator'}],'native_area_maps':['map']}
class FakePath:
    def __truediv__(self,value):return self
    def read_text(self,**kwargs):return json.dumps(assignment)
line=f'OWNER=CODEX_MANAGED_SYSTEMS_TASK4 manager_thread_id=manager operator_thread_id=operator assigned_editor_PID={os.getpid()} activation=MANAGER_ACTIVATED map=map'
check('actual-PID managed menu lease accepted',lambda: None if action_ns['managed_operation_lease'](FakePath(),line,'map') else (_ for _ in ()).throw(AssertionError()))
for replacement in (line.replace('MANAGER_ACTIVATED','AWAITING_MANAGER_ACTUAL_PID'),line.replace('operator_thread_id=operator','operator_thread_id=other'),line.replace(f'PID={os.getpid()}',f'PID={os.getpid()}9')):
    check('reject stale/unactivated managed lease',lambda replacement=replacement: None if not action_ns['managed_operation_lease'](FakePath(),replacement,'map') else (_ for _ in ()).throw(AssertionError()))

run_class=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GeoCityRun')
processing=next(n for n in run_class.body if isinstance(n,ast.FunctionDef) and n.name=='after_processing')
assembly_gate=next(n for n in processing.body[1].body if isinstance(n,ast.If) and 'building_assembly_contract' in ast.unparse(n.test))
gate=compile(ast.Module(body=[assembly_gate],type_ignores=[]),str(bank_path),'exec')
p=json.loads((ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json').read_text())
receipt=json.loads(Path(p['catalog_receipt']).read_text())
def buildings(data):
    owner=types.SimpleNamespace(p=p,state={},write=lambda:None)
    exec(gate,{'self':owner,'receipt':data})
    return owner.state
check('retained Shujaiya native building ledger passes',lambda:buildings(receipt))
bad=copy.deepcopy(receipt)
bad['building_assembly']['unsupported_count']=1
bad['building_assembly']['unsupported']=[{'source':'fixture','reason':'unsupported'}]
bad['building_assembly']['assembled_building_count']-=1
check('unsupported building refuses complete-area Bake',lambda:rejected(lambda:buildings(bad)))
bad=copy.deepcopy(receipt);bad['building_assembly']['native_module_point_count']-=1
check('module count mismatch refuses complete-area Bake',lambda:rejected(lambda:buildings(bad)))

Run=ns['GeoCityRun']
def paint_readiness():
    run=Run.__new__(Run)
    run.guard=lambda:None;run.write=lambda:None
    run.state={};run.save_tick='pending';run.paint_wait_started=time.time();run.paint_last_probe=0
    run.cooked_landscape=object();run.completed_receipt={};run.started_epoch=100
    advanced=[];removed=[];failures=[]
    run.advance_cooked=lambda r:advanced.append(r);run.fail=lambda *a:failures.append(a)
    ns['unreal']=types.SimpleNamespace(unregister_slate_post_tick_callback=removed.append)
    ns['geocity_landscape_workflow']=types.SimpleNamespace(verify_landscape=lambda *a:{'paint_ready':False,'ground_paint_weight_observed':True})
    run.finish_cook_readiness(0)
    assert not advanced and not removed and not failures
    ns['geocity_landscape_workflow'].verify_landscape=lambda *a:{'paint_ready':True}
    run.paint_last_probe=0;run.finish_cook_readiness(0)
    assert len(advanced)==1 and removed==['pending'] and run.save_tick is None and run.started_epoch==100
check('paint waits for full readiness without resetting capacity',paint_readiness)

def cleanup_failure():
    run=Run.__new__(Run)
    run._finishing=False;run.state={'phase':'failed_test','transaction_autosave':{}}
    run.native_road_run=None;run.save_tick='save';run.watch_tick='watch';run.was_paused=False
    run.started_epoch=time.time();run.autosave_before=True;run.release_menu_lease=False
    flags=[];detached=[];paused=[]
    run.autosave_settings=types.SimpleNamespace(set_editor_property=lambda *a,**k:flags.append(a[1]))
    run.api=types.SimpleNamespace(pause_asset_cooking=lambda:paused.append(True),is_asset_cooking_paused=lambda:True)
    run.write=lambda:None
    def broken(*a):raise RuntimeError('delegate fixture failure')
    run.wrapper=types.SimpleNamespace(set_auto_cooking_enabled=lambda x:None,set_auto_bake_enabled=lambda x:None,
        is_auto_cooking_enabled=lambda:False,is_auto_bake_enabled=lambda:False,
        on_post_instantiation_delegate=types.SimpleNamespace(remove_callable=broken),
        **{key:types.SimpleNamespace(remove_callable=lambda x:None) for key in ('on_post_cook_delegate','on_post_processing_delegate','on_post_bake_delegate')})
    ns['unreal']=types.SimpleNamespace(unregister_slate_post_tick_callback=detached.append,
        PropertyAccessChangeNotifyMode=types.SimpleNamespace(NEVER=0),
        EditorLoadingAndSavingUtils=types.SimpleNamespace(get_dirty_map_packages=lambda:[],get_dirty_content_packages=lambda:[]))
    run.finish_operation()
    assert detached==['save','watch'] and flags==[False] and paused and run.state['recovery_required']
    assert run.state['cleanup_errors'] and not run.state['lease_released']
check('cleanup error still detaches callbacks and holds unsafe release',cleanup_failure)

def landscape_identity():
    diagnostic=json.loads((ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/LANDSCAPE_EXPORT_DIAGNOSTIC.json').read_text())
    actual=set()
    for row in diagnostic['exports']:
        raw=Path(row['filename']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        args=(row['object'].rsplit('.',1)[-1],row['class'],row['object'],diagnostic['world'].split('.',1)[0])
        actual.add(ns['_landscape_export_identity'](raw.decode('utf-8-sig'),*args))
        rejected(lambda:ns['_landscape_export_identity']('',*args))
    assert actual==set(diagnostic['resolved_official_landscape_paths'])
check('all measured official Landscape exports resolve exact actor and reject missing binding',landscape_identity)

def suppression():
    run=Run.__new__(Run);run.action='regenerate';run.native_road_phase='suppression';run.state={};run.write=lambda:None
    baked=[];run.bake_and_save=lambda:baked.append(True)
    run.native_road_contract={k:'fixture' for k in ('area_id','source_sha256','centreline_sha256','drivable_source_ids','source_road_count','generated_road_count','generated_piece_ids')}
    run.native_road_contract['transaction']={'token':'expected'}
    provider={**run.native_road_contract,'provider':'RoadBLD','vehicle_surfaces_suppressed':True,
              'contract':{'transaction':{'token':'wrong'}}}
    rejected(lambda:run.advance_cooked({'surface_geometry':{'road_provider':provider}}))
    assert not baked
    provider['contract']['transaction']['token']='expected'
    run.advance_cooked({'surface_geometry':{'road_provider':provider}})
    assert baked==[True] and run.state['native_suppression_verified_before_bake']
check('suppression token must match before official Bake',suppression)

seal_ns={'ROOT':ROOT,'PYTHON':ROOT/'Content/Python','hashlib':hashlib}
load_nodes(ROOT/'Staging/SystemCompletion_2026-10-04/seal_runtime.py',lambda n:isinstance(n,ast.FunctionDef) and n.name=='snapshot',seal_ns)
snapshot=seal_ns['snapshot']()
check('sealer snapshot covers dedicated RoadBLD config without publishing seal',lambda:None if
      snapshot['schema']=='environmentpipeline.geocity_runtime_sources.v2' and len(snapshot['support_files'])==4
      and 'Config/DefaultRoadBLD.ini' in snapshot['support_files'] else (_ for _ in ()).throw(AssertionError()))

for path in [ROOT/'Content/Python/init_unreal.py',* (ROOT/'Content/Python').glob('geocity_*.py'),ROOT/'Staging/SystemCompletion_2026-10-04/seal_runtime.py']:
    compile(path.read_bytes(),str(path),'exec')
results.append({'check':'compile retained Python sources with installed Unreal Python runtime','passed':True})
output={'schema':'environmentpipeline.task1_offline_checks.v1','checks':results,'passed':len(results),
        'unreal_imported':False,'native_execution':False,'combined_manifest_sealed':False}
(OUT/'SOURCE_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output,indent=2))
