"""Offline parser and ownership regression checks; no Unreal import."""
import ast
import hashlib
import json
import os
import re
import time
import types
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
SOURCE=ROOT/'Content/Python/geocity_bank_workflow.py'
tree=ast.parse(SOURCE.read_bytes(),str(SOURCE))
names={'_path','_landscape_export_identity','GeoCityRun'}
ns={'Path':Path,'json':json,'hashlib':hashlib,'os':os,'re':re,'time':time}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names],type_ignores=[]),str(SOURCE),'exec'),ns)
raw_parse=ns['_landscape_export_identity']
cls='/Script/HoudiniEngineRuntime.HoudiniLandscapeTargetLayerOutput'
name='HoudiniLandscapeTargetLayerOutput_0'
map_path='/Game/Project/Areas/GazaShujaiya/Map'
object_path=map_path+'.Map:PersistentLevel.HoudiniAssetActor_0.HoudiniOutput_0.'+name
def parse(text,name,cls):return raw_parse(text,name,cls,object_path,map_path)
actor='/Game/Project/Areas/GazaShujaiya/Map.Map:PersistentLevel.ExactActor'
def document(path=actor):
    return '\n'.join([f'Begin Object Class={cls} Name="{name}" ExportPath="{cls}\'{object_path}\'"',f' Landscape="/Script/Landscape.Landscape\'{path}\'"',
                       f' LandscapeProxy="/Script/Landscape.Landscape\'{path}\'"','End Object'])
checks=[]
def check(label,fn):fn();checks.append(label)
def reject(fn):
    try:fn()
    except (RuntimeError,AssertionError):return
    raise AssertionError('Expected rejection')
check('absolute exact reference',lambda:None if parse(document(),name,cls)==actor else (_ for _ in ()).throw(AssertionError()))
check('native same-package reference resolves only exact map context',lambda:None if parse(document('Map:PersistentLevel.ExactActor'),name,cls)==actor else (_ for _ in ()).throw(AssertionError()))
for label,text in [
 ('wrong root name',document().replace('Name="'+name+'"','Name="Other"')),
 ('wrong root class',document().replace('Class='+cls,'Class=/Script/CoreUObject.Object')),
 ('duplicate root identity field',document().replace('Name="'+name+'"','Name="'+name+'" Name="'+name+'"')),
 ('duplicate actor field',document().replace('End Object',f' Landscape=Landscape\'{actor}\'\nEnd Object')),
 ('relative reference',document('ExactActor')),
 ('wrong relative map',document('OtherMap:PersistentLevel.ExactActor')),
 ('wrong exported owner identity',document().replace(object_path,object_path+'_other')),
 ('missing binding',document().replace(' Landscape="',' Unrelated="')),
 ('multiple roots',document()+'\n'+document()),
 ('unterminated root',document().replace('End Object','')),
 ('foreign proxy',document().replace('LandscapeProxy="/Script/Landscape.Landscape\''+actor,'LandscapeProxy="/Script/Landscape.Landscape\''+actor+'_other')),
 ('nested-only spoof',f'Begin Object Class={cls} Name="{name}"\nBegin Object Class={cls} Name="Nested"\nLandscape=Landscape\'{actor}\'\nEnd Object\nEnd Object'),
 ('nested reference with valid root reference',document().replace('End Object',f'Begin Object Name="Nested"\nLandscape=Landscape\'{actor}\'\nEnd Object\nEnd Object')),
 ('unbalanced reference quote',document().replace("Landscape'", "Landscape'\"",1)),
 ]:
    check('reject '+label,lambda text=text:reject(lambda:parse(text,name,cls)))

def integration(foreign=False,duplicate_object=False,ambiguous=False):
    map_path='/Game/Project/Areas/GazaShujaiya/Map'
    class Obj:
        def __init__(self,path,outer=None):self.path=path;self.outer=outer
        def get_path_name(self):return self.path
        def get_outer(self):return self.outer
        def get_name(self):return self.path.rsplit('.',1)[-1]
    class Landscape(Obj):
        def get_outermost(self):return Obj(map_path)
    owner=Obj(map_path+'.Map:PersistentLevel.HoudiniAssetActor_0')
    landscape=Landscape(actor)
    unknown=Landscape(actor+'_unknown')
    obj=Obj(owner.path+'.HoudiniOutput_0.'+name,owner)
    obj.get_class=lambda:types.SimpleNamespace(get_name=lambda:'HoudiniLandscapeTargetLayerOutput',get_path_name=lambda:cls)
    def denied(*args):raise AssertionError('Protected property access must never occur')
    obj.get_editor_property=denied
    obj2=Obj(owner.path+'.HoudiniOutput_0.HoudiniLandscapeTargetLayerOutput_1',owner)
    obj2.get_class=obj.get_class;obj2.get_editor_property=denied
    objects=[obj,obj if duplicate_object else obj2]
    actors=[owner,landscape,unknown]
    class Task:errors=[]
    exports=[]
    def export(task):
        assert task.object in objects and not task.prompt and not task.selected and task.automated
        path=actor+'_foreign' if foreign else actor+'_unknown' if ambiguous and task.object is obj2 else actor
        payload=document(path).replace('Name="'+name+'"','Name="'+task.object.get_name()+'"').replace(object_path,task.object.get_path_name())
        Path(task.filename).write_text(payload,encoding='utf-8')
        exports.append(task.filename)
        return True
    ns['unreal']=types.SimpleNamespace(Landscape=Landscape,EditorActorSubsystem=object,
        get_editor_subsystem=lambda _:types.SimpleNamespace(get_all_level_actors=lambda:actors),
        EditorLoadingAndSavingUtils=types.SimpleNamespace(get_dirty_map_packages=lambda:[],get_dirty_content_packages=lambda:[]),
        AssetExportTask=Task,ObjectExporterT3D=lambda:object(),Exporter=types.SimpleNamespace(run_asset_export_task=export),
        HoudiniOutputType=types.SimpleNamespace(LANDSCAPE='landscape'))
    wrapper=types.SimpleNamespace(get_string_parameter_value=lambda _:'source.json',get_houdini_asset_actor=lambda:owner,
        get_num_outputs=lambda:1,get_output_type_at=lambda _:'landscape',get_output_identifiers_at=lambda _:[1,2],
        get_output_object_at=lambda index,identifier:objects[identifier-1],is_auto_cooking_enabled=lambda:False,is_auto_bake_enabled=lambda:False)
    run=ns['GeoCityRun'].__new__(ns['GeoCityRun'])
    run.project=ROOT;run.p={'map':map_path,'source':'source.json'};run.state={};run.state_path=OUT/'OFFLINE_STATE.json'
    run.api=types.SimpleNamespace(is_asset_cooking_paused=lambda:True,is_session_valid=lambda:False)
    result=run.official_landscapes(wrapper)
    assert set(result)=={actor} and actor+'_unknown' not in result
    assert len(exports)==2 and len(run.state['official_landscape_identity_reads'][0]['records'])==2
check('exact native-object export resolver deduplicates layers; no protected access or unknown actor selection',integration)
check('unloaded foreign reference fails without selecting another actor',lambda:reject(lambda:integration(foreign=True)))
check('duplicate official layer object identity rejected',lambda:reject(lambda:integration(duplicate_object=True)))
check('multiple native Landscape references rejected as ambiguous',lambda:reject(lambda:integration(ambiguous=True)))
native_first=ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/LANDSCAPE_EXPORT_FIRST.json'
if native_first.is_file():
    proof=json.loads(native_first.read_text())
    raw=Path(proof['filename']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==proof['sha256']
    expected=proof['before']['world']+':PersistentLevel.GeoCity_city_v015_PermanentBank_3_373_0_GazaShujaiya_landscape'
    value=raw_parse(raw.decode('utf-8-sig'),proof['object'].rsplit('.',1)[-1],proof['object_class'],proof['object'],proof['before']['world'].split('.',1)[0])
    assert value==expected
    checks.append('measured task4 first native export parses exact second saved Landscape identity')
native_all=ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/LANDSCAPE_EXPORT_DIAGNOSTIC.json'
if native_all.is_file():
    proof=json.loads(native_all.read_text())
    assert proof['status']=='READONLY_EXPORT_CONFIRMED_NATIVE_INACTIVE' and proof['state_clean_unchanged'] and not proof['errors']
    resolved=set()
    assert len(proof['exports'])==5
    for row in proof['exports']:
        raw=Path(row['filename']).read_bytes()
        assert row['export_return'] and not row['export_errors'] and hashlib.sha256(raw).hexdigest()==row['sha256']
        value=raw_parse(raw.decode('utf-8-sig'),row['object'].rsplit('.',1)[-1],row['class'],row['object'],proof['world'].split('.',1)[0])
        assert value==row['references']['Landscape']['resolved_loaded_actor_path']==row['references']['LandscapeProxy']['resolved_loaded_actor_path']
        resolved.add(value)
    assert resolved==set(proof['resolved_official_landscape_paths']) and not proof['ownership_accounting']['unaccounted']
    checks.append('all five hashed real native exports match exact task4 Landscape/Proxy ownership accounting')
compile(SOURCE.read_bytes(),str(SOURCE),'exec')
checks.append('source compiles under installed Unreal Python311')
receipt={'schema':'environmentpipeline.task1_landscape_ownership_checks.v1','passed':len(checks),'checks':checks,
         'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'native_exporter_executed':False,
         'unreal_imported':False,'native_serialization_format_verified':native_first.is_file(),
         'native_diagnostic_receipt':str(native_all) if native_all.is_file() else None,
         'fixtures':'Synthetic adversarial T3D, AST-selected resolver with fake native objects, and task4 hashed real exports. Revised lifecycle method itself remains unexecuted in Unreal.'}
(OUT/'SOURCE_CHECKS.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
