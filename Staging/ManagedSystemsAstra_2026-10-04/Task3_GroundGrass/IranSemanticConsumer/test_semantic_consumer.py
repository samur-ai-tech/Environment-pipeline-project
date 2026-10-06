"""Staging-only consumer checks. Synthetic probes are never a native profile."""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
BASELINE = PROJECT / 'Content/Python/geocity_landscape_workflow.py'
STAGED = HERE / 'geocity_landscape_workflow.py'
OWNER_PACKAGE = PROJECT / 'Staging/PipelineSemanticRepair_2026-10-04/Completion/CONSUMER_PACKAGE.json'
package = json.loads(OWNER_PACKAGE.read_text())
policy = json.loads(Path(package['contract']).read_text())
ns = {'unreal': SimpleNamespace(MaterialEditingLibrary=SimpleNamespace(), GrassScaling=SimpleNamespace(UNIFORM='Uniform')),
      'math': math, 'hashlib': hashlib, 'json': json}
tree = ast.parse(STAGED.read_text())
nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Assign))]
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(STAGED), 'exec'), ns)


def seal(profile):
    envelope = profile['landscape_semantics']
    envelope['contract_sha256'] = ns['_semantic_digest'](envelope['contract'])
    return profile


def fixture():
    """Purposefully synthetic counts/locations, not claimed source measurements."""
    targets = copy.deepcopy(policy['class_material_targets'])
    layers = {n: {'kind': 'weight', 'state': 'absent', 'nonzero_sample_count': 0} for n in targets.values()}
    for name in ('BaseGrass1', 'PB_Custom_Ground', 'Dirt_Path', 'Sand_Path', 'Sand_02'):
        layers[name] = {'kind': 'weight', 'state': 'painted', 'nonzero_sample_count': 1}
    for name in ('GC_GrassEligible', 'GC_WaterCandidate'):
        layers[name] = {'kind': 'mask', 'state': 'painted', 'nonzero_sample_count': 1}
    for name, value in zip(ns['SEMANTIC_RGB'], policy['water']['linear_rgb']):
        layers[name] = {'kind': 'constant', 'state': 'painted', 'nonzero_sample_count': 5, 'value': value}
    contract = {'schema':'environmentpipeline.semantic_landscape_contract.v1',
                'area_id':policy['area_id'], 'source_package_sha256':package['package_sha256'],
                'class_grid_sha256':'ee4024abf7e233cde32c69c63722d123578faca3be4cd51c6e919c0f7046c3da',
                'policy_sha256':package['contract_sha256'],
                'coordinate_frame':'houdini_x_east_y_up_z_south_to_unreal_cm_x_z_y',
                'coverage_scope':'emitted_landscape_including_border',
                'vegetation_provider':'native_landscape_grass','grass_layer':'GC_GrassEligible',
                'grass_allowed_classes':[10,20,30], 'water_mode':'classification_surface',
                'class_targets':targets,'class_counts':{str(c):0 for c in ns['SEMANTIC_CLASSES']},
                'role_layers':{'RoadBed':'Dirt_Path','BuildingPad':'Sand_Path','Steep':'Sand_02'},
                'layers':layers,'probes':[]}
    contract['class_counts'].update({'30':2, '80':1})
    present = {n for n,v in layers.items() if v['state'] != 'absent'}
    for i, (name, tag, code, mask, water) in enumerate([
        ('BaseGrass1', 'class:30', 30, 1, 0), ('PB_Custom_Ground', 'class:80', 80, 0, 1),
        ('Dirt_Path', 'role:RoadBed', None, 0, 0), ('Sand_Path', 'role:BuildingPad', None, 0, 0),
        ('Sand_02', 'role:Steep', None, 0, 0)]):
        values = {n:layers[n]['value'] if layers[n]['kind']=='constant' else 0 for n in present}
        values[name]=1;values['GC_GrassEligible']=mask;values['GC_WaterCandidate']=water
        tags = [tag, 'grass:positive' if mask else 'grass:excluded']
        contract['probes'].append({'id':'synthetic-'+str(i), 'world_location_cm':[i*100,0,0],
                                  'tags':tags,'source_class_id':code,
                                  'expected_weights':{n:[v,v] for n,v in values.items()}})
    profile = {'root':'/Game/Project/Areas/'+policy['area_id']+'/BankIntegration_v015',
               'map':'/Game/Project/Areas/'+policy['area_id']+'/BankIntegration_v015/L_Iran',
               'source':package['package'],
               'landscape_grass':dict(copy.deepcopy(policy['grass']), enabled=True, base_material_instance=ns['BASE'], ground_layer=ns['SEMANTIC_MASK']),
               'painted_layer_names':sorted(present),
               'landscape_semantics':{'schema':'environmentpipeline.semantic_landscape_profile.v1','contract':contract}}
    return seal(profile)


def samples(profile):
    return [{'id':p['id'], 'world_location_cm':p['world_location_cm'][:],
             'weights':{n:v[0] for n,v in p['expected_weights'].items()}}
            for p in profile['landscape_semantics']['contract']['probes']]


def dynamic_fixture():
    p=fixture()
    c=p['landscape_semantics']['contract']
    p['surface_choices']=dict(ns['CHOICES'])
    p['landscape_semantics']={'schema':'environmentpipeline.semantic_landscape_profile.v2',
                             'source_package_sha256':c['source_package_sha256'],
                             'consumer_contract_sha256':c['policy_sha256'], 'class_grid_sha256':c['class_grid_sha256']}
    raw=copy.deepcopy(c)
    for probe in raw['probes']:
        xyz=probe.pop('world_location_cm')
        probe['hda_location_m']=[xyz[0]/100,xyz[2]/100,xyz[1]/100]
        probe['expected_weights']={n:v[0] for n,v in probe['expected_weights'].items()}
    receipt={'semantic_surface_contract':raw,'semantic_surface_contract_sha256':ns['_semantic_digest'](raw)}
    return p,receipt


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.p = fixture()
        self.c = self.p['landscape_semantics']['contract']

    def validate(self): return ns['_semantic_contract'](seal(self.p))

    def test_valid_dynamic_contract(self): self.assertIs(self.validate(), self.c)

    def test_active_source_exactly_preserved(self):
        self.assertEqual(hashlib.sha256(BASELINE.read_bytes()).hexdigest(),'d1a5d5fdbcf8e5d3ced8dc9ccf9a2d975fb2c845546ffd84649c37137b4c998d')
        self.assertTrue(STAGED.read_text().startswith(BASELINE.read_text()))

    def test_gaza_cannot_opt_into_semantic_exception(self):
        self.p['map']='/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya'
        with self.assertRaises(RuntimeError): self.validate()

    def test_stale_contract_digest(self):
        self.c['class_counts']['30']=3
        with self.assertRaises(RuntimeError): ns['_semantic_contract'](self.p)

    def test_provider_mismatch_rejected(self):
        self.c['vegetation_provider']='hda_understory'
        with self.assertRaises(RuntimeError): self.validate()

    def test_both_provider_is_not_supported(self):
        self.c['vegetation_provider']='both'
        with self.assertRaises(RuntimeError): self.validate()

    def test_unknown_class_without_explicit_count_rejected(self):
        del self.c['class_counts']['20']
        with self.assertRaises(RuntimeError): self.validate()

    def test_zero_role_is_explicit_and_does_not_need_positive_probe(self):
        self.c['layers']['Sand_02'].update(state='zero', nonzero_sample_count=0)
        self.c['probes'].pop()
        for p in self.c['probes']: p['expected_weights']['Sand_02']=[0,0]
        self.validate()
        self.assertTrue(ns['evaluate_semantic_samples'](samples(self.p),self.c)['paint_ready'])

    def test_absent_role_is_explicit_and_not_sampled(self):
        self.c['layers']['Sand_02'].update(state='absent', nonzero_sample_count=0)
        self.c['probes'].pop(); self.p['painted_layer_names'].remove('Sand_02')
        for p in self.c['probes']: del p['expected_weights']['Sand_02']
        self.validate()
        self.assertTrue(ns['evaluate_semantic_samples'](samples(self.p),self.c)['paint_ready'])

    def test_declared_zero_with_positive_count_fails(self):
        self.c['layers']['Sand_02']['state']='zero'
        with self.assertRaises(RuntimeError): self.validate()

    def test_positive_role_cannot_omit_known_probe(self):
        self.c['probes'].pop()
        with self.assertRaises(RuntimeError): self.validate()

    def test_nonfinite_probe_rejected(self):
        self.c['probes'][0]['world_location_cm'][0]=float('inf')
        with self.assertRaises((RuntimeError,ValueError)): self.validate()

    def test_vacuous_probe_interval_rejected(self):
        self.c['probes'][0]['expected_weights']['BaseGrass1']=[0,1]
        with self.assertRaises(RuntimeError): self.validate()

    def test_missing_water_rgb_rejected(self):
        del self.c['layers']['PB_Custom_Ground_R']
        with self.assertRaises(RuntimeError): self.validate()

    def test_water_not_physical_provider(self):
        self.c['water_mode']='lake_plane'
        with self.assertRaises(RuntimeError): self.validate()

    def test_excluded_class_must_expect_zero_grass(self):
        self.c['probes'][1]['expected_weights']['GC_GrassEligible']=[.1,.1]
        with self.assertRaises(RuntimeError): self.validate()


class ReadinessTests(unittest.TestCase):
    def setUp(self): self.p=fixture(); self.c=self.p['landscape_semantics']['contract'];self.s=samples(self.p)
    def evaluate(self): return ns['evaluate_semantic_samples'](self.s,self.c)

    def test_surface_normalization_excludes_nonweight_masks_and_rgb(self):
        self.assertGreater(sum(self.s[0]['weights'].values()),2)
        self.assertTrue(self.evaluate()['paint_ready'])

    def test_grid_only_cannot_pass(self):
        for p in self.s:p['id']='grid:'+p['id']
        self.assertFalse(self.evaluate()['paint_ready'])

    def test_missing_small_water_component_probe_cannot_pass(self):
        self.s.pop(1)
        self.assertFalse(self.evaluate()['paint_ready'])

    def test_zero_readback_remains_pending(self):
        self.s[0]['weights']={n:0 for n in self.s[0]['weights']}
        r=self.evaluate();self.assertFalse(r['paint_ready']);self.assertTrue(r['pending_sample_ids'])

    def test_wrong_axis_or_probe_position_fails(self):
        self.s[1]['world_location_cm'][1]=100
        self.assertFalse(self.evaluate()['paint_ready'])

    def test_truncated_actual_probe_location_fails(self):
        self.s[1]['world_location_cm']=[]
        self.assertFalse(self.evaluate()['paint_ready'])

    def test_nonfinite_actual_probe_location_fails(self):
        self.s[1]['world_location_cm'][0]=float('nan')
        self.assertFalse(self.evaluate()['paint_ready'])

    def test_unreviewed_disabled_alternate_provider_fails(self):
        self.p['landscape_grass']['enabled']=False
        self.c['vegetation_provider']='hda_understory'
        with self.assertRaises(RuntimeError):ns['_semantic_contract'](seal(self.p))

    def test_raw_water_mask_cannot_grow_terrestrial_grass(self):
        self.s[1]['weights']['GC_GrassEligible']=1
        r=self.evaluate();self.assertFalse(r['paint_ready'])
        self.assertIn('semantic_grass_exclusion',[v['reason'] for v in r['paint_contract_failures']])

    def test_rgb_constant_drift_fails(self):
        self.s[1]['weights']['PB_Custom_Ground_R']=.9
        self.assertFalse(self.evaluate()['paint_ready'])

    def test_unexpected_positive_zero_role_fails(self):
        self.c['layers']['Sand_02'].update(state='zero',nonzero_sample_count=0)
        self.assertFalse(self.evaluate()['paint_ready'])

    def test_classification_does_not_claim_hydrology_or_pixels(self):
        r=self.evaluate()
        self.assertFalse(r['surveyed_hydrology_verified']);self.assertFalse(r['visible_lit_grass_verified'])


class SourceAndOutputTests(unittest.TestCase):
    def setUp(self):self.p=fixture();self.c=self.p['landscape_semantics']['contract']

    def receipt(self):
        return {'semantic_surface_contract_sha256':ns['_semantic_digest'](self.c),'semantic_surface_complete':True,
                'semantic_grass_provider':'native_landscape_grass','semantic_hda_understory_suppressed':True,
                'nonbuilding_instances':[{'role':'tree'},{'role':'shrub'}],
                'semantic_nonweight_layers':[n for n,v in self.c['layers'].items() if v['kind']!='weight' and v['state']!='absent']}

    def test_current_owner_v2_package_grid_policy_hashes_read_only(self):
        # Checks real artifact identities only. Fixture locations remain synthetic.
        r=ns['_semantic_source_identity'](self.p,self.c)
        self.assertTrue(r['source_identity_verified'])

    def test_wrong_policy_hash_rejected(self):
        self.c['policy_sha256']='0'*64
        with self.assertRaises(RuntimeError):ns['_semantic_source_identity'](self.p,self.c)

    def test_complete_matching_output(self):ns['_semantic_output_contract'](self.receipt(),self.c)

    def test_duplicate_understory_provider_fails(self):
        r=self.receipt();r['nonbuilding_instances'].append({'role':'understory'})
        with self.assertRaises(RuntimeError):ns['_semantic_output_contract'](r,self.c)

    def test_missing_actual_instance_ledger_fails(self):
        r=self.receipt();del r['nonbuilding_instances']
        with self.assertRaises(RuntimeError):ns['_semantic_output_contract'](r,self.c)

    def test_incomplete_hda_cannot_save(self):
        r=self.receipt();r['semantic_surface_complete']=False
        with self.assertRaises(RuntimeError):ns['_semantic_output_contract'](r,self.c)

    def test_auxiliary_mask_must_not_be_weight_blended(self):
        r=self.receipt();r['semantic_nonweight_layers'].remove('GC_GrassEligible')
        with self.assertRaises(RuntimeError):ns['_semantic_output_contract'](r,self.c)

    def test_legacy_entrypoints_delegate_without_semantic_side_effects(self):
        run=SimpleNamespace(p={})
        with patch.dict(ns, {'_GEOMETRIC_PREPARE':lambda r:'oldprepare', '_GEOMETRIC_VERIFY':lambda *args:'oldverify',
                             '_GEOMETRIC_NEAR_VIEW':lambda *args:'oldnear'}):
            self.assertEqual(ns['prepare'](run),'oldprepare')
            self.assertEqual(ns['verify_landscape'](run,None,{}),'oldverify')
            self.assertEqual(ns['inspect_near_view'](run,None,[0,0,0]),'oldnear')

    def test_semantic_near_view_needs_complete_output_receipt(self):
        with self.assertRaises(RuntimeError):ns['inspect_near_view'](SimpleNamespace(p=self.p),None,[0,0,0])

    def test_dynamic_preparation_does_not_invent_output_counts(self):
        p,r=dynamic_fixture(); c=ns['_semantic_preparation_contract'](p)
        self.assertNotIn('class_counts',c)
        self.assertTrue(all(v['state']=='potential' for v in c['layers'].values()))

    def test_dynamic_local_probes_convert_under_exact_source_identity(self):
        p,r=dynamic_fixture();c=ns['_semantic_verified_output_contract'](p,r)
        self.assertEqual(c['probes'][1]['world_location_cm'],[100,0,0])
        self.assertTrue(ns['evaluate_semantic_samples'](samples(fixture()),c)['paint_ready'])

    def test_missing_dynamic_contract_is_not_ready(self):
        p,r=dynamic_fixture()
        with self.assertRaises(RuntimeError):ns['_semantic_verified_output_contract'](p,{})

    def test_dynamic_contract_stale_class_grid_rejected(self):
        p,r=dynamic_fixture();r['semantic_surface_contract']['class_grid_sha256']='0'*64
        r['semantic_surface_contract_sha256']=ns['_semantic_digest'](r['semantic_surface_contract'])
        with self.assertRaises(RuntimeError):ns['_semantic_verified_output_contract'](p,r)

    def test_dynamic_supplied_world_coordinate_mismatch_rejected(self):
        p,r=dynamic_fixture();r['semantic_surface_contract']['probes'][1]['world_location_cm']=[999,0,0]
        r['semantic_surface_contract_sha256']=ns['_semantic_digest'](r['semantic_surface_contract'])
        with self.assertRaises(RuntimeError):ns['_semantic_verified_output_contract'](p,r)

    def test_nonidentity_actor_transform_rejected(self):
        actor=SimpleNamespace(get_actor_location=lambda:SimpleNamespace(x=1,y=0,z=0),
                              get_actor_rotation=lambda:SimpleNamespace(pitch=0,yaw=0,roll=0),
                              get_actor_scale3d=lambda:SimpleNamespace(x=1,y=1,z=1))
        run=SimpleNamespace(wrapper=SimpleNamespace(get_houdini_asset_actor=lambda:actor))
        with self.assertRaises(RuntimeError):ns['_semantic_actor_frame'](run)


if __name__=='__main__':unittest.main(verbosity=2)
