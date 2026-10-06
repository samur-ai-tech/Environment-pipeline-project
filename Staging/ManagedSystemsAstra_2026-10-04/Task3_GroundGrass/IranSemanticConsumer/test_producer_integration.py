"""Actual producer AST -> staged consumer, on registered source data, no native API."""
import ast, copy, hashlib, json, math, re
from pathlib import Path
from unittest.mock import patch
import numpy as np
from test_semantic_consumer import ns, dynamic_fixture, HERE, PROJECT, package, policy

source=PROJECT/'Staging/PipelineSemanticRepair_2026-10-04/Completion/geocity_city_module_semantic_consumer_candidate.py'
producer={'np':np,'Path':Path,'json':json,'hashlib':hashlib,'math':math,'re':re}
tree=ast.parse(source.read_text())
nodes=[]
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and (node.name.startswith('sc_') or node.name=='_semantic_provenance'):nodes.append(node)
    if isinstance(node,ast.Assign) and all(isinstance(t,ast.Name) and (t.id.startswith('SC_') or t.id in ('_SEMANTIC_SOURCE_REVISION','_SEMANTIC_POLICY_SHA256','GRID_SAMPLES','GRID_SPACING_M')) for t in node.targets):nodes.append(node)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),producer)
grid=producer['sc_load_semantic_grid'](package['package'])
info={'area_id':policy['area_id'],'sha256':package['package_sha256'],'semantic_grid':grid,
      'semantic_consumer_contract':policy,'semantic_consumer_contract_sha256':package['contract_sha256']}
p,_=dynamic_fixture()
p['catalog_sha256']='b'*64
p['landscape_material']=p['root']+'/Materials/MI_GeoCityGround.MI_GeoCityGround'
prep=ns['_semantic_preparation_contract'](p)
synthetic_readback={'varieties':'OFFLINE_FIXTURE_NOT_NATIVE','coverage':.15,
                   'material_layer_names':sorted(prep['layers'])}
with patch.dict(ns,{'_semantic_binding_readback':lambda *a:synthetic_readback,'_path':lambda a:a}):
    token=ns['_semantic_runtime_binding'](p,prep,p['landscape_material'],'OFFLINE_GRASS_FIXTURE')
producer['sc_validate_runtime_binding'](info,token,p['landscape_material'],list(prep['layers']))
assert token['native_binding_receipt_sha256']==ns['_semantic_digest'](synthetic_readback)
assert token['grass_bindings_verified'] is True
assert token['visible_lit_grass_verified'] is False

axis=np.arange(producer['GRID_SAMPLES'],dtype=np.float64)*producer['GRID_SPACING_M']-(producer['GRID_SAMPLES']-1)*producer['GRID_SPACING_M']/2
classes=producer['sc_sample_hda_classes'](grid,axis[None,:],axis[:,None])
checks=[]
for scenario in ('zero_geometric_roles','positive_geometric_roles','zero_grass_mask'):
    zeros=np.zeros_like(classes,dtype=np.float32)
    masks={r:zeros.copy() for r in ('RoadBed','BuildingPad','Steep')}
    if scenario=='positive_geometric_roles':
        masks['RoadBed'][:,100:102]=1
        masks['BuildingPad'][100:102,:]=1
        masks['Steep'][:,150:152]=1
    if scenario=='zero_grass_mask':masks['BuildingPad'][:]=1
    choices={r:{'layer':n} for r,n in prep['role_layers'].items()}
    choices.update({'LC_'+c:{'layer':n} for c,n in policy['class_material_targets'].items()})
    values={}
    for role,weights in producer['sc_iter_surface_weights'](classes,masks['RoadBed'],masks['BuildingPad'],masks['Steep']):
        if np.any(weights):
            name=choices[role]['layer']
            values[name]=values.get(name,zeros)+weights
    aux={'GC_GrassEligible':producer['sc_grass_eligible_weights'](classes,masks['RoadBed'],masks['BuildingPad'],masks['Steep']),
         'GC_WaterCandidate':(classes==80).astype(np.float32)}
    if 'PB_Custom_Ground' in values:
        aux.update({n:np.full(classes.shape,v,dtype=np.float32) for n,v in zip(ns['SEMANTIC_RGB'],policy['water']['linear_rgb'])})
    raw=producer['sc_surface_contract'](info,axis,classes,masks,zeros,choices,values,aux)
    receipt=producer['sc_attach_surface_receipt']({'nonbuilding_instances':[]},info,raw,token,sorted(aux),0)
    assert receipt['semantic_runtime_binding_sha256']==ns['_semantic_digest'](token)
    contract=ns['_semantic_verified_output_contract'](p,receipt)
    ns['_semantic_source_identity'](p,contract)
    ns['_semantic_output_contract'](receipt,contract)
    samples=[{'id':q['id'],'world_location_cm':q['world_location_cm'],
              'weights':{n:v[0] for n,v in q['expected_weights'].items()}} for q in contract['probes']]
    result=ns['evaluate_semantic_samples'](samples,contract)
    assert result['paint_ready'],result
    assert raw['classified_water_cells_preserved']==9
    assert sum(q['source_class_id']==80 for q in raw['probes'])>=9
    checks.append({'scenario':scenario,'status':'PASS','source_probe_count':len(samples),
                   'explicit_zero_layers':result['explicit_zero_layers'],'explicit_absent_layers':result['explicit_absent_layers']})
    if scenario=='positive_geometric_roles':
        (HERE/'PRODUCER_SAMPLE_CONTRACT_TEST_ONLY.json').write_text(json.dumps(raw,indent=2))

result={'status':'PASS','producer_candidate_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'consumer_candidate_sha256':hashlib.sha256((HERE/'geocity_landscape_workflow.py').read_bytes()).hexdigest(),
        'token_shape_actual_consumer_to_actual_producer':'PASS','checks':checks,
        'class_grid':list(classes.shape),'source_data':'Real registered 404x404 source sampled on actual retained 4033x4033 1m lattice; nine original class80 cells',
        'geometry_and_native_readback':'Synthetic test masks and readback values, NOT native measurement or generated terrain',
        'no_unreal_or_houdini_import':True,'native_actions':False,'active_source_changed':False}
(HERE/'PRODUCER_INTEGRATION_RESULT.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
