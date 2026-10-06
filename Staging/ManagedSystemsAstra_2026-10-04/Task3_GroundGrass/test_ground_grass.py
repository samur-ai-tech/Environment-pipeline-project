"""Offline regression checks: AST functions + inert API fixtures, no Unreal import."""
import ast
import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'Content/Python/geocity_landscape_workflow.py'
tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
# Deliberately omit every import from the production module. No editor bridge,
# native module, HDA graph, package writer, or engine process can be reached.
nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Assign))]
api = SimpleNamespace(MaterialEditingLibrary=SimpleNamespace(),
                      GrassScaling=SimpleNamespace(UNIFORM='Uniform'))
ns = {'unreal': api, 'math': math, 'json': json}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), ns)


def sample(name, values, role=None):
    item = {'id': name, 'world_location_cm': [0, 0, 0],
            'weights': dict(zip(ns['TARGETS'].values(), values))}
    if role:
        item.update(expected_role=role, minimum_weight=.8)
    return item


def four_roles():
    return [sample('ground', [1, 0, 0, 0], 'Ground'),
            sample('steep', [0, 1, 0, 0], 'Steep'),
            sample('road', [0, 0, 1, 0], 'RoadBed'),
            sample('pad', [0, 0, 0, 1], 'BuildingPad')]


class PaintTests(unittest.TestCase):
    def evaluate(self, points):
        return ns['evaluate_paint_samples'](points, .15)

    def test_all_targets_and_full_exclusions(self):
        r = self.evaluate(four_roles())
        self.assertTrue(r['paint_ready'])
        self.assertTrue(r['all_four_targets_observed'])
        self.assertFalse(r['geographic_land_cover_semantics_verified'])

    def test_postprocessing_zero_is_pending(self):
        r = self.evaluate([sample('pending', [0, 0, 0, 0])])
        self.assertFalse(r['paint_ready'])
        self.assertEqual(r['pending_sample_ids'], ['pending'])
        self.assertFalse(r['paint_contract_failures'])

    def test_partial_ready_components_do_not_hide_pending(self):
        r = self.evaluate(four_roles() + [sample('pending', [0, 0, 0, 0])])
        self.assertTrue(r['ground_paint_weight_observed'])
        self.assertFalse(r['paint_ready'])

    def test_later_readback_recovers_without_relaxing_gate(self):
        self.assertFalse(self.evaluate([sample('first', [0, 0, 0, 0])])['paint_ready'])
        self.assertTrue(self.evaluate(four_roles())['paint_ready'])

    def test_ground_only_is_insufficient(self):
        r = self.evaluate([sample('ground', [1, 0, 0, 0])])
        self.assertTrue(r['ground_paint_weight_observed'])
        self.assertFalse(r['paint_ready'])
        self.assertEqual(r['unobserved_roles'], ['Steep', 'RoadBed', 'BuildingPad'])

    def test_grid_only_all_four_targets_cannot_pass(self):
        points = four_roles()
        for p in points: p.pop('expected_role')
        r = self.evaluate(points)
        self.assertTrue(r['all_four_targets_observed'])
        self.assertFalse(r['paint_ready'])
        self.assertFalse(r['known_exclusion_probes_passed'])
        self.assertEqual(r['missing_known_exclusion_roles'], ['RoadBed', 'BuildingPad'])

    def test_missing_one_known_exclusion_cannot_pass(self):
        points = four_roles()
        points[-1].pop('expected_role')
        self.assertFalse(self.evaluate(points)['paint_ready'])

    def test_duplicate_known_probe_cannot_pass(self):
        points = four_roles()
        points[-1]['id'] = points[-2]['id']
        r = self.evaluate(points)
        self.assertFalse(r['paint_ready'])
        self.assertEqual(r['paint_contract_failures'][0]['reason'], 'invalid_or_duplicate_known_probe')

    def test_nonfinite_known_coordinate_cannot_pass(self):
        points = four_roles()
        points[-1]['world_location_cm'][0] = float('nan')
        self.assertFalse(self.evaluate(points)['paint_ready'])

    def test_painted_road_misrouted_as_ground_fails(self):
        r = self.evaluate(four_roles() + [sample('known-road', [1, 0, 0, 0], 'RoadBed')])
        self.assertFalse(r['paint_ready'])
        self.assertEqual(r['paint_contract_failures'][0]['reason'], 'known_location_role_mismatch')

    def test_painted_pad_and_steep_misrouting_fail(self):
        for role in ('BuildingPad', 'Steep'):
            with self.subTest(role=role):
                self.assertFalse(self.evaluate(four_roles() + [sample('wrong', [1, 0, 0, 0], role)])['paint_ready'])

    def test_overlapping_full_ground_and_road_not_normalized(self):
        r = self.evaluate(four_roles() + [sample('overlap', [1, 0, 1, 0])])
        self.assertFalse(r['paint_ready'])
        self.assertEqual(r['paint_contract_failures'][0]['reason'], 'four_target_weights_not_normalized')

    def test_partial_boundaries_keep_existing_normalized_contract(self):
        r = self.evaluate(four_roles() + [sample('boundary', [.28, .12, .1, .5])])
        self.assertTrue(r['paint_ready'])

    def test_byte_quantization_is_allowed(self):
        r = self.evaluate(four_roles() + [sample('quantized', [64/255]*4)])
        self.assertTrue(r['paint_ready'])

    def test_nan_infinity_and_out_of_range_fail(self):
        for value in (float('nan'), float('inf'), -.1, 1.1):
            with self.subTest(value=value):
                self.assertFalse(self.evaluate(four_roles()+[sample('bad', [value, 0, 0, 0])])['paint_ready'])


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'landscape_grass': {'base_material_instance': ns['BASE'],
                        'ground_layer': 'Sand_01', 'mesh_paths': list(ns['PERMITTED_MESHES']),
                        'coverage': .15, 'density_per_10m2': 12.0,
                        'paint_probe_locations': [{'id':'road', 'expected_role':'RoadBed', 'world_location_cm':[0,0,0]},
                                                  {'id':'pad', 'expected_role':'BuildingPad', 'world_location_cm':[1,1,1]}]},
                        'painted_layer_names': list(ns['TARGETS'].values()),
                        'surface_choices': dict(ns['CHOICES'])}

    def test_retained_contract(self):
        self.assertEqual(ns['_config'](self.profile)['coverage'], .15)

    def test_role_alias_or_wrong_choice_rejected(self):
        self.profile['surface_choices']['paint_roadbed_choice'] = 17
        with self.assertRaises(RuntimeError): ns['_config'](self.profile)

    def test_new_grass_mesh_rejected_even_before_bank_lookup(self):
        self.profile['landscape_grass']['mesh_paths'].append('/Game/Other.Other')
        with self.assertRaises(RuntimeError): ns['_config'](self.profile)

    def test_invalid_coverage_rejected(self):
        for value in (float('nan'), float('inf'), 0, -1, 1.1):
            self.profile['landscape_grass']['coverage'] = value
            with self.assertRaises(RuntimeError): ns['_config'](self.profile)

    def test_missing_known_probes_fail_before_native_preparation(self):
        self.profile['landscape_grass']['paint_probe_locations'] = []
        with self.assertRaises(RuntimeError): ns['_config'](self.profile)

    def test_nonfinite_profile_probe_coordinate_rejected(self):
        self.profile['landscape_grass']['paint_probe_locations'][0]['world_location_cm'][0] = float('inf')
        with self.assertRaises(RuntimeError): ns['_config'](self.profile)

    def test_duplicate_profile_probe_ids_rejected(self):
        self.profile['landscape_grass']['paint_probe_locations'][1]['id'] = 'road'
        with self.assertRaises(RuntimeError): ns['_config'](self.profile)

    def test_invalid_probe_expected_weight_rejected(self):
        for value in (float('nan'), .1, 1.1):
            self.profile['landscape_grass']['paint_probe_locations'][0]['minimum_weight'] = value
            with self.assertRaises(RuntimeError): ns['_config'](self.profile)

    def test_density_is_total_across_two_meshes(self):
        varieties = ns['_expected_varieties'](self.profile, self.profile['landscape_grass'])
        self.assertEqual(sum(v['grass_density'] for v in varieties), 12.0)
        self.assertTrue(all(v['grass_density_quality'] == 6 for v in varieties))
        self.assertTrue(all(v['end_cull_distance'] == 20000 for v in varieties))
        self.assertTrue(all(v['allowed_density_range'] == [0, 1] for v in varieties))


class Prop:
    def __init__(self, **values): self.values = values
    def get_editor_property(self, key): return self.values[key]
    def get_path_name(self): return self.values['path']


class ReadbackTests(unittest.TestCase):
    def make_grass(self):
        profile = {'landscape_grass': {'mesh_paths': list(ns['PERMITTED_MESHES']), 'density_per_10m2':12}}
        expected = ns['_expected_varieties'](profile, profile['landscape_grass'])
        varieties = []
        for entry in expected:
            p = {'grass_mesh': Prop(path=entry['mesh']), 'override_materials': []}
            for key, value in entry.items():
                if key in ('mesh', 'materials') or key.endswith('_overrides'): continue
                if key in ('scale_x', 'scale_y', 'scale_z', 'allowed_density_range'):
                    p[key] = Prop(min=value[0], max=value[1])
                elif key + '_overrides' in entry:
                    p[key] = Prop(default=value, **{'per_quality' if key.endswith('_quality') else 'per_platform': {}})
                else: p[key] = value
            varieties.append(Prop(**p))
        return Prop(grass_varieties=varieties), expected

    def test_actual_settings_equal_spec(self):
        grass, expected = self.make_grass()
        self.assertEqual(ns['_read_varieties'](grass), expected)

    def test_metadata_cannot_hide_stale_density_or_platform_override(self):
        grass, expected = self.make_grass()
        grass.values['grass_varieties'][0].values['grass_density'].values['per_platform'] = {'Windows': 0}
        self.assertNotEqual(ns['_read_varieties'](grass), expected)

    def test_metadata_cannot_hide_stale_mesh(self):
        grass, expected = self.make_grass()
        grass.values['grass_varieties'][0].values['grass_mesh'] = Prop(path='/Game/Wrong.Wrong')
        self.assertNotEqual(ns['_read_varieties'](grass), expected)

    def test_nodes_use_public_asset_api(self):
        ns['LIB'].get_material_expressions = lambda material: ['existing-owned-nodes']
        self.assertEqual(ns['_nodes'](object()), ['existing-owned-nodes'])


class CacheEvidenceTests(unittest.TestCase):
    def inspect(self, xyz):
        class Component(Prop):
            def get_instance_count(self): return 1
            def get_instance_transform(self, index, world_space=False):
                if not world_space: raise AssertionError('Need actual world position')
                return SimpleNamespace(translation=SimpleNamespace(x=xyz[0], y=xyz[1], z=xyz[2]))
        component = Component(path='Landscape:Grass0', static_mesh=Prop(path=ns['PERMITTED_MESHES'][0]))
        landscape = SimpleNamespace(get_components_by_class=lambda cls: [component])
        run = SimpleNamespace(guard=lambda: None)
        fake_api = SimpleNamespace(HierarchicalInstancedStaticMeshComponent=object)
        snapshot = {'paint_ready': True, 'native_grass_instance_count': 1, 'visible_lit_grass_verified': False}
        with patch.dict(ns, {'unreal': fake_api, 'verify_landscape': lambda *args: dict(snapshot)}):
            return ns['inspect_near_view'](run, landscape, [0, 0, 0])

    def test_distant_cache_is_not_nearby_or_visible(self):
        r = self.inspect([6000, 0, 0])
        self.assertFalse(r['nearby_grass_cache_verified'])
        self.assertFalse(r['visible_lit_grass_verified'])

    def test_nearby_cache_still_does_not_claim_lit_pixels(self):
        r = self.inspect([100, 0, 0])
        self.assertTrue(r['nearby_grass_cache_verified'])
        self.assertFalse(r['visible_lit_grass_verified'])
        self.assertEqual(r['nearby_grass_instances'][0]['view_distance_cm'], 100)

    def test_unknown_landscape_hism_is_not_exempt_from_native_counts(self):
        class Landscape: pass
        class HISM(Prop): pass
        fake_api = SimpleNamespace(LandscapeProxy=Landscape, HierarchicalInstancedStaticMeshComponent=HISM)
        profile = {'landscape_grass': {'enabled': True}}
        with patch.dict(ns, {'unreal': fake_api}):
            self.assertFalse(ns['is_native_grass'](Landscape(), HISM(static_mesh=Prop(path='/Game/Other.Other')), profile))
            self.assertTrue(ns['is_native_grass'](Landscape(), HISM(static_mesh=Prop(path=ns['PERMITTED_MESHES'][0])), profile))


if __name__ == '__main__':
    unittest.main(verbosity=2)
