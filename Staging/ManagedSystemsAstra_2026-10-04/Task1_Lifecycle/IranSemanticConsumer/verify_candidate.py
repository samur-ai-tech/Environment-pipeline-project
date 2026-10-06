"""Offline actual-owner contract interoperability; no Unreal/Houdini imports."""
import ast, copy, hashlib, json, math, os, re, runpy, time, types
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
T3=ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task3_GroundGrass/IranSemanticConsumer'
PRODUCER=ROOT/'Staging/PipelineSemanticRepair_2026-10-04/Completion'
checks=[]
def check(name,fn):fn();checks.append({'check':name,'passed':True})
def reject(fn):
    try:fn()
    except (AssertionError,RuntimeError,ValueError,KeyError):return
    raise AssertionError('Expected fail-closed rejection')
def nodes(path,ns,predicate):
    tree=ast.parse(path.read_bytes(),str(path))
    exec(compile(ast.Module(body=[n for n in tree.body if predicate(n)],type_ignores=[]),str(path),'exec'),ns)
    return tree
ns={'Path':Path,'hashlib':hashlib,'json':json,'os':os,'re':re,'time':time,'Counter':Counter}
tree=nodes(OUT/'geocity_bank_workflow.py',ns,lambda n:isinstance(n,(ast.FunctionDef,ast.ClassDef)))
Run=ns['GeoCityRun']
task3=runpy.run_path(str(T3/'test_semantic_consumer.py'),run_name='offline_lifecycle_interop')
native_ns=task3['ns']
profile,_=task3['dynamic_fixture']()
profile['catalog_sha256']='b'*64
profile['landscape_material']=profile['root']+'/Materials/MI_GeoCityGround.MI_GeoCityGround'
preparation=native_ns['_semantic_preparation_contract'](profile)
readback={'landscape_material':profile['landscape_material'],'grass_type':'OFFLINE_GRASS_HANDLE_NOT_NATIVE',
          'varieties':'OFFLINE_READBACK_FIXTURE_NOT_NATIVE','coverage':.15,
          'material_layer_names':sorted(preparation['layers'])}
original_read=native_ns['_semantic_binding_readback'];original_path=native_ns['_path']
native_ns['_semantic_binding_readback']=lambda *args:readback
native_ns['_path']=lambda value:value
try:token=native_ns['_semantic_runtime_binding'](profile,preparation,profile['landscape_material'],'OFFLINE_GRASS_HANDLE_NOT_NATIVE')
finally:native_ns['_semantic_binding_readback']=original_read;native_ns['_path']=original_path
prepared={'semantic_runtime_binding':token,'native_binding_receipt':readback}
producer={'json':json,'hashlib':hashlib,'re':re,'GRID_SAMPLES':4033}
nodes(PRODUCER/'semantic_consumer_extension.py',producer,lambda n:isinstance(n,ast.FunctionDef) and n.name in {'sc_validate_runtime_binding','sc_attach_surface_receipt','sc_canonical_digest'})
owner_package=json.loads((PRODUCER/'CONSUMER_PACKAGE.json').read_text())
policy=json.loads(Path(owner_package['contract']).read_bytes())
info={'area_id':policy['area_id'],'sha256':owner_package['package_sha256'],
      'semantic_consumer_contract':policy,'semantic_consumer_contract_sha256':owner_package['contract_sha256']}
raw=json.loads((T3/'PRODUCER_SAMPLE_CONTRACT_TEST_ONLY.json').read_text())
receipt=producer['sc_attach_surface_receipt']({'nonbuilding_instances':[]},info,raw,token,raw['auxiliary_layers'],0)
receipt['semantic_consumer']={'source_contract':policy,'contract_sha256':owner_package['contract_sha256'],
                            'runtime_binding':token,'native_postcook_verified':False}
def newrun():
    run=Run.__new__(Run);run.p=copy.deepcopy(profile);run.state={'landscape_grass_connection':copy.deepcopy(prepared)}
    run.state['semantic_native_binding']=ns['_semantic_prepared_binding'](run.p,run.state['landscape_grass_connection'])
    run.write=lambda:None
    return run
def interop():
    assert producer['sc_validate_runtime_binding'](info,token,profile['landscape_material'],preparation['layers'])==token
    run=newrun();run.verify_consumer_receipt(receipt)
    assert run.state['semantic_producer_receipt']['semantic_surface_contract']==raw
    assert run.state['semantic_producer_receipt_verified'] is True
    adapted=native_ns['_semantic_verified_output_contract'](profile,receipt)
    native_ns['_semantic_output_contract'](receipt,adapted)
    assert producer['sc_canonical_digest'](token)==ns['_consumer_digest'](token)==native_ns['_semantic_digest'](token)
check('actual Task3 token builder -> lifecycle binding -> producer transport -> Task3 receipt verifier',interop)
for field in ('schema','source_package_sha256','consumer_contract_sha256','catalog_sha256','native_binding_receipt_sha256','landscape_material','provider','mask_layer'):
    def test(field=field):
        bad=copy.deepcopy(prepared);bad['semantic_runtime_binding'][field]='mismatch'
        reject(lambda:ns['_semantic_prepared_binding'](profile,bad))
    check('reject mismatched preparation '+field,test)
for field in ('material_graph_prepared','canonical_area_eligibility_verified','grass_bindings_verified'):
    def test(field=field):
        bad=copy.deepcopy(prepared);bad['semantic_runtime_binding'][field]=False
        reject(lambda:ns['_semantic_prepared_binding'](profile,bad))
    check('reject unverified preparation '+field,test)
for field in ('semantic_surface_contract_sha256','semantic_surface_complete','semantic_grass_provider','semantic_runtime_binding_sha256','semantic_nonweight_layers','semantic_hda_understory_suppressed','semantic_native_postcook_verified'):
    def test(field=field):
        bad=copy.deepcopy(receipt);bad[field]=[] if field.endswith('layers') else 'invalid'
        run=newrun();reject(lambda:run.verify_consumer_receipt(bad))
        assert run.state['semantic_producer_receipt'][field]==bad[field]
    check('reject and preserve malformed producer '+field,test)
def duplicate_understory():
    bad=copy.deepcopy(receipt);bad['nonbuilding_instances']=[{'role':'understory'}]
    reject(lambda:newrun().verify_consumer_receipt(bad))
check('native Grass rejects duplicated HDA understory',duplicate_understory)
def source_change():
    p=copy.deepcopy(profile);p['landscape_semantics']['source_package_sha256']='0'*64
    reject(lambda:ns['_semantic_prepared_binding'](p,prepared))
check('exact source package identity required before cook',source_change)
def grid_change():
    p=copy.deepcopy(profile);p['landscape_semantics']['class_grid_sha256']='0'*64
    reject(lambda:ns['_semantic_prepared_binding'](p,prepared))
check('exact classified grid identity required before cook',grid_change)

class Wrapper:
    def __init__(self,values):self.values=dict(values);self.events=[];self.inputs={};self.auto=False
    def get_parameter_tuples(self):return {k:types.SimpleNamespace(string_values=[v]) for k,v in self.values.items()}
    def get_string_parameter_value(self,k):return self.values.get(k)
    def set_string_parameter_value(self,k,v):self.events.append(('string',k,v));self.values[k]=v;return True
    def set_auto_cooking_enabled(self,v):self.auto=v
    def is_auto_cooking_enabled(self):return self.auto
    def set_input_parameter(self,k,v):self.inputs[k]=v;return True
    def get_input_parameter(self,k):return self.inputs[k]
    def set_bool_parameter_value(self,k,v):self.values[k]=v;return True
    def get_bool_parameter_value(self,k):return self.values[k]
    def set_int_parameter_value(self,k,v):self.values[k]=v;return True
    def get_int_parameter_value(self,k):return self.values[k]
    def set_temporary_cook_folder(self,v):return True
    def set_bake_folder(self,v):return True
    def set_replace_previous_bake(self,v):return True
    def get_replace_previous_bake(self):return True
    def set_remove_output_after_bake(self,v):return True
    def get_remove_output_after_bake(self):return True
    def set_auto_bake_enabled(self,v):return True
    def is_auto_bake_enabled(self):return False
    def recook(self):self.events.append(('recook',));return True
def binding_parameter():
    run=newrun();w=Wrapper({'semantic_runtime_binding_json':''})
    strings=run.consumer_parameter_strings(w)
    assert strings=={'semantic_runtime_binding_json':ns['_consumer_json'](token)}
    assert producer['sc_validate_runtime_binding'](info,strings['semantic_runtime_binding_json'],profile['landscape_material'])==token
check('exact scalar-string canonical semantic token reaches official parameter plan',binding_parameter)
check('missing promoted semantic parameter refuses bind',lambda:reject(lambda:newrun().consumer_parameter_strings(Wrapper({}))))
def legacy():
    run=Run.__new__(Run);run.p={};run.state={}
    assert run.consumer_parameter_strings(Wrapper({}))=={}
    w=Wrapper({'semantic_runtime_binding_json':'stale','building_rules_json':'{"schema":"environmentpipeline.building_rules.v1","defaults":{"unchanged":true},"content_input":{"stale":true}}'})
    result=run.consumer_parameter_strings(w)
    assert result['semantic_runtime_binding_json']==''
    rules=json.loads(result['building_rules_json']);assert rules['defaults']=={'unchanged':True} and 'content_input' not in rules
    run.verify_consumer_receipt({})
check('legacy definition unchanged; promoted definition clears stale tokens only, retaining defaults',legacy)
class Table:
    def get_path_name(self):return '/Game/FixtureTable'
class Input:
    def set_input_objects(self,v):self.objects=v
    def get_input_objects(self):return self.objects
ns['unreal']=types.SimpleNamespace(DataTable=Table,HoudiniPublicAPIGeoInput=Input,new_object=lambda cls:cls(),
    load_asset=lambda path:Table(),DirectoryPath=lambda:types.SimpleNamespace(),
    DataTableFunctionLibrary=types.SimpleNamespace(get_data_table_row_names=lambda t:['fixture']))
def configured_run():
    run=newrun();run.p.update(mode='disabled',release={},table='/Game/FixtureTable',row_count=1,
        environment_style_set='fixture',procedural_material='/Game/FixtureMaterial',surface_choices={},
        cook_folder=profile['root']+'/Cook',bake_folder=profile['root']+'/Bake')
    run.guard=lambda:None;run.guard_processes=lambda:None;run.configure_engine_outputs=lambda w:None
    run.native_road_phase=None;run.native_road_contract=None
    run.receipt=OUT/'NONEXISTENT_OFFLINE_CATALOG_RECEIPT.json';assert not run.receipt.exists()
    return run
def full_configure():
    run=configured_run();w=Wrapper({'semantic_runtime_binding_json':''});run.configure_and_bind(w)
    assert w.events[-1]==('recook',)
    assert run.state['consumer_parameter_readback']['semantic_runtime_binding_json']==ns['_consumer_json'](token)
    assert run.state['parameters']['package_file']==profile['source']
    assert w.events.index(('string','semantic_runtime_binding_json',ns['_consumer_json'](token)))<len(w.events)-1
check('full configure_and_bind official setter/readback precedes sole recook and records token',full_configure)
def wrong_readback():
    run=configured_run();w=Wrapper({'semantic_runtime_binding_json':''})
    old=w.get_string_parameter_value
    w.get_string_parameter_value=lambda k:'corrupt' if k=='semantic_runtime_binding_json' else old(k)
    reject(lambda:run.configure_and_bind(w));assert ('recook',) not in w.events
check('semantic parameter readback mismatch prevents recook',wrong_readback)

building=ROOT/'Staging/IranBuildingAdaptation_2026-10-04/ConsumerIntegration'
input_doc=json.loads((building/'INPUT_CONTRACT.json').read_bytes())
building_ns={}
nodes(ROOT/'Staging/IranBuildingAdaptation_2026-10-04/building_extension.py',building_ns,
      lambda n:isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BUILDING_POLICY' for t in n.targets))
rules=copy.deepcopy(building_ns['BUILDING_POLICY'])
rules['content_input']={'path':str(building/'INPUT_CONTRACT.json'),'sha256':hashlib.sha256((building/'INPUT_CONTRACT.json').read_bytes()).hexdigest()}
building_profile=copy.deepcopy(profile);building_profile['building_rules_json']=rules
check('actual current building input is rejected against different promoted semantic source hash',lambda:reject(lambda:ns['_building_rules_binding'](building_profile)))
# The building owner separately publishes this exact additive-source binding.
combined_path=building/'INPUT_CONTRACT_COMBINED.json'
building_profile['building_rules_json']['content_input']={'path':str(combined_path),'sha256':hashlib.sha256(combined_path.read_bytes()).hexdigest()}
def building_shape():
    bound=ns['_building_rules_binding'](building_profile)
    forward=json.loads(bound['json'])
    evidence=runpy.run_path(str(building/'evidence_contract.py'),run_name='offline_building_contract')
    result=evidence['_bc_load_content_input'](forward['content_input'],policy['area_id'],owner_package['package_sha256'])
    assert result['input_sha256']==bound['content_input_sha256']
    assert not result['validation_errors'],result['validation_errors']
    assert not result['accepted'],'Current unqualified evidence must remain unqualified'
    run=newrun();run.p=building_profile
    w=Wrapper({'semantic_runtime_binding_json':'','building_rules_json':json.dumps(building_ns['BUILDING_POLICY'])})
    plan=run.consumer_parameter_strings(w)
    assert json.loads(plan['building_rules_json'])==forward
    producer_receipt=copy.deepcopy(receipt)
    producer_receipt.update(building_content_input_sha256=bound['content_input_sha256'],building_dependencies_complete=False)
    reject(lambda:run.verify_consumer_receipt(producer_receipt))
    assert run.state['building_consumer_receipt']['building_dependencies_complete'] is False
check('building wire digest matches actual evidence parser, does not qualify candidates or bypass completeness',building_shape)
def naked_filename():
    bad=copy.deepcopy(building_profile);bad['building_rules_json']['content_input']=str(building/'INPUT_CONTRACT.json')
    reject(lambda:ns['_building_rules_binding'](bad))
check('mutable building evidence filename cannot be an ordinary activation',naked_filename)
def combined_configure():
    run=configured_run();run.p['building_rules_json']=building_profile['building_rules_json']
    w=Wrapper({'semantic_runtime_binding_json':'','building_rules_json':json.dumps(building_ns['BUILDING_POLICY'])})
    run.configure_and_bind(w)
    bound=run.state['building_rules_binding']
    assert run.state['consumer_parameter_readback']['building_rules_json']==bound['json']
    assert ('string','building_rules_json',bound['json']) in w.events and w.events[-1]==('recook',)
check('complete configure sets and reads back both exact tokens before sole full cook',combined_configure)
def missing_building():
    run=configured_run();run.p['building_rules_json']=building_profile['building_rules_json'];w=Wrapper({'semantic_runtime_binding_json':''})
    reject(lambda:run.configure_and_bind(w));assert not w.events
check('missing required building parameter fails before setters or cook',missing_building)
def building_readback():
    run=configured_run();run.p['building_rules_json']=building_profile['building_rules_json']
    w=Wrapper({'semantic_runtime_binding_json':'','building_rules_json':json.dumps(building_ns['BUILDING_POLICY'])})
    old=w.get_string_parameter_value;w.get_string_parameter_value=lambda k:'corrupt' if k=='building_rules_json' else old(k)
    reject(lambda:run.configure_and_bind(w));assert ('recook',) not in w.events
check('building readback mismatch prevents cook',building_readback)
def stale_evidence():
    bad=copy.deepcopy(building_profile);bad['building_rules_json']['content_input']['sha256']='0'*64
    reject(lambda:ns['_building_rules_binding'](bad))
check('changed top-level building contract bytes prevent cook',stale_evidence)
def disabled_semantic():
    bad=copy.deepcopy(profile);bad['landscape_grass']['enabled']=False
    reject(lambda:ns['_semantic_prepared_binding'](bad,prepared))
check('disabled native Grass cannot silently bypass semantic provider contract',disabled_semantic)

baseline=ast.parse((OUT/'Before/geocity_bank_workflow.py').read_bytes())
original_class=next(n for n in baseline.body if isinstance(n,ast.ClassDef) and n.name=='GeoCityRun')
newclass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GeoCityRun')
def unchanged():
    protected=('guard','guard_processes','finish_operation','watch','validate_outputs','official_landscapes','account_previous_landscapes',
               'configure_engine_outputs','finish_cook_readiness','begin_native_roads','current_road_landscape_authority',
               'after_native_roads','bake_and_save','after_bake','save_generated_dependencies')
    for name in protected:
        before=next(n for n in original_class.body if isinstance(n,ast.FunctionDef) and n.name==name)
        after=next(n for n in newclass.body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert ast.dump(before)==ast.dump(after),name
    text=(OUT/'geocity_bank_workflow.py').read_text();before=(OUT/'Before/geocity_bank_workflow.py').read_text()
    assert text.count('<120')==before.count('<120')==3
    assert (ROOT/'Content/Python/geocity_bank_workflow.py').read_bytes()==(OUT/'Before/geocity_bank_workflow.py').read_bytes()
    assert (ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json').read_bytes()==(OUT/'Before/geocity_runtime_manifest.json').read_bytes()
check('native lifecycle guards, 120s waits, named save functions and runtime/seal remain unchanged',unchanged)
dependencies=[T3/'geocity_landscape_workflow.py',T3/'semantic_consumer_extension.py',T3/'INTERFACE_FROZEN_DECISION.json',
              T3/'PRODUCER_SAMPLE_CONTRACT_TEST_ONLY.json',PRODUCER/'semantic_consumer_extension.py',building/'evidence_contract.py',building/'INPUT_CONTRACT.json',combined_path,building/'SOURCE_BINDING.json']
result={'status':'OFFLINE_CROSS_OWNER_SHAPE_PASS_NATIVE_NOT_RUN','checks':checks,'passed':len(checks),
        'candidate_sha256':hashlib.sha256((OUT/'geocity_bank_workflow.py').read_bytes()).hexdigest(),
        'dependencies':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies},
        'fixtures':'Actual source bytes and actual producer sample with synthetic geometric masks; native readback is explicitly fake. No generated terrain/material/native readiness claimed.',
        'unreal_imported':False,'houdini_imported':False,'runtime_mutated':False,'native_actions':False,
        'building_source_binding':{'original_input_source_sha256':input_doc['source_sha256'],'semantic_source_sha256':owner_package['package_sha256'],
          'resolution':'Original input rejected; new owner INPUT_CONTRACT_COMBINED plus SOURCE_BINDING pass exact evidence parser. No candidates qualified by this lifecycle patch.'}}
(OUT/'SOURCE_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':len(checks),'status':result['status']}))
