"""Contract checks only. Synthetic native data is never native validation evidence."""
import copy
import hashlib
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
NS = runpy.run_path(str(HERE/'RETAINED_SOURCE_FAMILY_APPEND.py'))
SOURCE = HERE.parents[2]/'Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05/SOURCE_BINDINGS.json'
BINDINGS = json.loads(SOURCE.read_text(encoding='utf-8'))
FIXTURES = HERE/'Checks'/'SyntheticFixtures'
FIXTURES.mkdir(parents=True, exist_ok=True)
IDENTITY = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def save_fixture(name, value):
    path = FIXTURES/name
    assert path.resolve().is_relative_to(HERE.resolve())
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def fixture(family_index=6, matrix=None):
    family = copy.deepcopy(BINDINGS['families'][family_index])
    matrix = matrix or IDENTITY
    names = [part['name'] for aset in family['sets'] for part in aset['parts']]
    basis = {'contract_test_only': True, 'family_id': family['family_id'], 'passed': True,
        'source_family_sha256': NS['_sf_digest'](family), 'source_to_native_matrix': matrix,
        'source_units': 'metres', 'native_units': 'centimetres', 'pivot_translation_preserved': True,
        'sample_vertices_checked': 32, 'verified_part_names': names, 'maximum_probe_error_cm': 0.0,
        'reflection_normals_material_culling_verified': True}
    native = {'schema': NS['SOURCE_NATIVE_PROTOCOL'], 'family_id': family['family_id'],
        'source_family_sha256': NS['_sf_digest'](family), 'source_to_native_matrix': matrix,
        'basis_evidence_ref': save_fixture(family['id']+'_basis.json', basis), 'contract_test_only': True,
        'actual_named_or_dependency_hold': False, 'parent_canonical_hold_preserved': True, 'parts': {}}
    for aset in family['sets']:
        for source in aset['parts']:
            low, high = NS['_sf_transformed_bounds'](source['local_bounds_m']['min'], source['local_bounds_m']['max'], matrix)
            name = source['name']
            native['parts'][name] = {'asset_id': family['family_id']+'/'+name,
                'path': source['native_package']+'.'+name, 'source_sha256': source['fbx_sha256'],
                'min_cm': [v*100 for v in low], 'max_cm': [v*100 for v in high],
                'source_material_slots': source['source_material_slots'],
                'material_slots': ['/Game/ContractCheck/M_%s.M_%s' % (i, i) for i in range(len(source['source_material_slots']))],
                'native_source_slot_indices': list(range(len(source['source_material_slots']))),
                'actual_named_or_dependency_hold': False, 'dependency_closed': True,
                'pivot_preserved': True, 'source_uv0_probe_alignment_passed': True, 'uv_channel_count_verified': True}
    entry = {'family_id': family['family_id'], 'native_manifest_ref': {'sha256': NS['_sf_digest'](native)},
        'height_policy': 'preserve_native_for_unmeasured_source',
        'capabilities': {'exact_reconstruction': {'enabled': False, 'allowed_repeat_counts': [1]}}}
    extension = Path(family['assembly_path']).parent/'ExtensionBand/EXTENSION.json'
    if extension.is_file():
        entry['extension_rule_ref'] = {'path': str(extension), 'sha256': hashlib.sha256(extension.read_bytes()).hexdigest()}
    feature = {'area_id': 'GazaRimal', 'osm_id': 'CONTRACT_CHECK_ONLY', 'closed': True, 'holes': False,
        'base_m': 7.25, 'height_m': 10.0, 'height_rule': 'seeded_rule_not_measured'}
    reconstruction = next(s['parts'] for s in family['sets'] if s['kind'] == 'reconstruction')
    lows, highs = [], []
    for source in reconstruction:
        lo, hi = NS['_sf_transformed_bounds'](source['local_bounds_m']['min'], source['local_bounds_m']['max'], matrix)
        translation = NS['_sf_mul'](matrix, source['assembly_translation_m'])
        lows.append([lo[i]+translation[i] for i in range(3)]); highs.append([hi[i]+translation[i] for i in range(3)])
    dimensions = [max(v[i] for v in highs)-min(v[i] for v in lows) for i in range(3)]
    x, z = dimensions[0]*0.6, dimensions[1]*0.6
    feature['ring_xz_m'] = [[-x,-z],[x,-z],[x,z],[-x,z]]
    return feature, family, native, entry, basis


def plan(bundle, **kwargs):
    return NS['source_family_plan'](*bundle[:4], audit_only=True, **kwargs)


class CandidateChecks(unittest.TestCase):
    def test_all_twenty_complete_exact_families_at_unit_scale(self):
        total = 0
        for index in range(20):
            bundle = fixture(index)
            record = plan(bundle)
            expected = len(next(s for s in bundle[1]['sets'] if s['kind'] == 'reconstruction')['parts'])
            self.assertEqual(record['module_count'], expected)
            self.assertEqual(record['generated_parts'], [])
            self.assertIsNone(record['stories'])
            self.assertFalse(record['architectural_floors_certified'])
            self.assertFalse(record['source_family']['runtime_selection_authorized'])
            self.assertFalse(record['source_family']['ordinary_selection_enabled'])
            for part in record['wall_placements']:
                self.assertEqual(part['native_scale'], [1,1,1])
                self.assertEqual(part['style_palette_id'], 'source_preserved')
                self.assertIsNone(part['architectural_floor_index'])
            total += expected
        self.assertEqual(total, 585)

    def test_native_centimetres_converted_once_and_whole_family_rotated(self):
        bundle = fixture()
        bundle[0]['ring_xz_m'] = [[-8,-8],[8,-8],[8,8],[-8,8]]
        zero, ninety = plan(bundle), plan(bundle, yaw_degrees=90)
        self.assertAlmostEqual(zero['height_m'], ninety['height_m'], places=10)
        for a, b in zip(zero['wall_placements'], ninety['wall_placements']):
            self.assertAlmostEqual(a['P'][0], b['P'][2], places=10)
            self.assertAlmostEqual(a['P'][2], -b['P'][0], places=10)
            self.assertAlmostEqual(a['P'][1], b['P'][1], places=10)
        self.assertGreater(zero['height_m'], 4)
        self.assertLess(zero['height_m'], 5)

    def test_verified_signed_basis_supported(self):
        for matrix in ([[0,-1,0],[1,0,0],[0,0,1]], [[-1,0,0],[0,1,0],[0,0,1]]):
            bundle = fixture(matrix=matrix)
            result = plan(bundle)
            self.assertEqual(result['source_family']['source_to_native_matrix'], matrix)
            self.assertEqual(result['module_count'], 17)

    def test_reflection_without_culling_normals_evidence_rejected(self):
        bundle = fixture(matrix=[[-1,0,0],[0,1,0],[0,0,1]])
        bundle[4]['reflection_normals_material_culling_verified'] = False
        bundle[2]['basis_evidence_ref'] = save_fixture('reflection_unverified.json', bundle[4])
        with self.assertRaisesRegex(ValueError, 'reflection_appearance_unverified'):
            plan(bundle)

    def test_wrong_native_units_rejected(self):
        bundle = fixture()
        part = next(iter(bundle[2]['parts'].values()))
        part['max_cm'] = [v*100 for v in part['max_cm']]
        with self.assertRaisesRegex(ValueError, 'scale_axes_or_bounds_mismatch'):
            plan(bundle)

    def test_missing_native_part_rejected(self):
        bundle = fixture()
        bundle[2]['parts'].pop(next(iter(bundle[2]['parts'])))
        with self.assertRaisesRegex(ValueError, 'binding_incomplete'):
            plan(bundle)

    def test_missing_material_slot_rejected(self):
        bundle = fixture()
        next(iter(bundle[2]['parts'].values()))['material_slots'] = []
        with self.assertRaisesRegex(ValueError, 'material_slots_incomplete'):
            plan(bundle)

    def test_partial_source_set_rejected_even_with_resealed_native_fixture(self):
        bundle = fixture()
        bundle[1]['sets'][0]['parts'].pop()
        bundle[2]['source_family_sha256'] = NS['_sf_digest'](bundle[1])
        bundle[4]['source_family_sha256'] = NS['_sf_digest'](bundle[1])
        bundle[2]['basis_evidence_ref'] = save_fixture('partial_source_basis.json', bundle[4])
        with self.assertRaisesRegex(ValueError, 'partial_reconstruction'):
            plan(bundle)

    def test_unknown_or_nonvertical_native_basis_rejected(self):
        bundle = fixture()
        bundle[2]['source_to_native_matrix'] = [[0,0,1],[0,1,0],[1,0,0]]
        with self.assertRaisesRegex(ValueError, 'source_up_not_native_positive_Z'):
            plan(bundle)

    def test_nonfinite_transform_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            plan(fixture(), yaw_degrees=float('nan'))
        bundle = fixture()
        bundle[0]['base_m'] = float('inf')
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            plan(bundle)

    def test_outside_pad_and_concave_gap_rejected(self):
        bundle = fixture()
        bundle[0]['ring_xz_m'] = [[-1,-1],[1,-1],[1,1],[-1,1]]
        with self.assertRaisesRegex(ValueError, 'envelope_leaves_geographic_pad'):
            plan(bundle)
        polygon = [[-2,-2],[2,-2],[2,2],[-2,2]]
        ring = [[-3,-3],[3,-3],[3,3],[1,3],[1,0],[-1,0],[-1,3],[-3,3]]
        self.assertFalse(NS['_sf_contained'](polygon, ring))

    def test_measured_height_mismatch_rejected(self):
        bundle = fixture()
        bundle[0]['height_rule'] = 'osm_height'
        with self.assertRaisesRegex(ValueError, 'does_not_match_measured_source'):
            plan(bundle)

    def test_floor_scaling_and_unknown_shape_requests_rejected(self):
        for field, value in (('requested_floor_count', 3), ('requested_scale', [1,1,2])):
            bundle = fixture(); bundle[0][field] = value
            with self.assertRaisesRegex(ValueError, 'floors_or_geometric_scaling_not_supported'):
                plan(bundle)
        with self.assertRaisesRegex(ValueError, 'unsupported_capability'):
            plan(fixture(), mode='arbitrary_footprint')

    def test_eight_source_band_formulas_without_claiming_native_or_uv_qualification(self):
        checked = 0
        for index, family in enumerate(BINDINGS['families']):
            if not (Path(family['assembly_path']).parent/'ExtensionBand/EXTENSION.json').is_file():
                continue
            bundle = fixture(index)
            band = json.loads(Path(bundle[3]['extension_rule_ref']['path']).read_text())
            def band_plan(count):
                modified = copy.deepcopy(bundle)
                parts = band['source_derived_parts']; axis = band['corridor']['axis']; pitch = band['corridor']['pitch_m']
                lo = [min(p['local_bounds_m']['min'][i]+p['assembly_translation_m'][i] for p in parts) for i in range(3)]
                hi = [max(p['local_bounds_m']['max'][i]+p['assembly_translation_m'][i]
                    +(count-1)*pitch if i == axis and p['role'] == 'End' else
                    p['local_bounds_m']['max'][i]+p['assembly_translation_m'][i] for p in parts) for i in range(3)]
                x, z = (hi[0]-lo[0])*0.6, (hi[1]-lo[1])*0.6
                modified[0]['ring_xz_m'] = [[-x,-z],[x,-z],[x,z],[-x,z]]
                return plan(modified, mode='one_axis_extension', repeat_count=count)
            one, two = band_plan(1), band_plan(2)
            self.assertEqual(one['module_count'], 3)
            self.assertEqual(two['module_count'], 4)
            axis = band['corridor']['axis']; world_index = 0 if axis == 0 else 2
            one_end = next(p for p in one['wall_placements'] if p['band_role'] == 'End')
            two_end = next(p for p in two['wall_placements'] if p['band_role'] == 'End')
            # Centering the enlarged whole family moves Start -pitch/2 and End +pitch/2.
            self.assertAlmostEqual(two_end['P'][world_index]-one_end['P'][world_index], band['corridor']['pitch_m']/2, places=6)
            repeats = [p for p in two['wall_placements'] if p['band_role'] == 'Repeat']
            self.assertAlmostEqual(repeats[1]['P'][world_index]-repeats[0]['P'][world_index], band['corridor']['pitch_m'], places=6)
            self.assertFalse(two['source_family']['runtime_selection_authorized'])
            checked += 1
        self.assertEqual(checked, 8)

    def test_twelve_exact_only_families_reject_band_requests(self):
        checked = 0
        for index, family in enumerate(BINDINGS['families']):
            if any(s['kind'] == 'extension' for s in family['sets']):
                continue
            with self.assertRaisesRegex(ValueError, 'complete_source_set_missing'):
                plan(fixture(index), mode='one_axis_extension', repeat_count=2)
            checked += 1
        self.assertEqual(checked, 12)

    def test_unqualified_runtime_and_missing_qualification_authorization_rejected(self):
        bundle = fixture()
        with self.assertRaisesRegex(ValueError, 'capability_disabled'):
            NS['source_family_plan'](*bundle[:4])
        with self.assertRaisesRegex(ValueError, 'evidence_ref_missing'):
            NS['source_family_plan'](*bundle[:4], qualification=True)
        with self.assertRaisesRegex(ValueError, 'synthetic_native_fixture'):
            NS['_sf_native_parts'](bundle[1], bundle[2], 'exact_reconstruction')

    def test_source_evidence_tamper_rejected(self):
        bundle = fixture()
        bundle[2]['basis_evidence_ref']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'evidence_changed'):
            plan(bundle)

    def test_disabled_registry_retains_existing_hook_result(self):
        old = lambda feature, contract: {'status': 'complete', 'wall_placements': [], 'generated_parts': [], 'sentinel': 'retained'}
        wrapped = runpy.run_path(str(HERE/'RETAINED_SOURCE_FAMILY_APPEND.py'), init_globals={'assembly_layout': old})
        path = HERE/'DISABLED_SOURCE_FAMILY_REGISTRY.json'
        registry_ref = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        result = wrapped['assembly_layout'](fixture()[0], {'source_family_registry_ref': registry_ref})
        self.assertEqual(result['sentinel'], 'retained')
        self.assertEqual(result['source_family_selection']['status'], 'retained_fallback')

    def test_minimum_coverage_not_relaxed_and_tiny_family_replacement_rejected(self):
        bundle = fixture()
        bundle[0]['ring_xz_m'] = [[-100,-100],[100,-100],[100,100],[-100,100]]
        with self.assertRaisesRegex(ValueError, 'covers_too_little'):
            plan(bundle)
        bundle = fixture(); bundle[3]['minimum_pad_coverage_ratio'] = 0.4
        with self.assertRaisesRegex(ValueError, 'weaker_than_retained'):
            plan(bundle)

    def test_pad_edge_orientation_is_not_limited_to_world_quadrants(self):
        feature = fixture()[0]
        feature['ring_xz_m'] = [[0,0],[10,10],[7,13],[-3,3]]
        self.assertAlmostEqual(NS['_sf_pad_edge_yaw'](feature), 45)

    def test_unknown_use_reported_and_known_station_not_fabricated(self):
        bundle = fixture()
        self.assertEqual(plan(bundle)['building_use'], 'unknown')
        bundle[0]['building_use'] = 'station'
        with self.assertRaisesRegex(ValueError, 'building_use_unqualified'):
            plan(bundle)

    def test_assigned_qualification_cannot_silently_emit_baseline(self):
        old = lambda feature, contract: {'sentinel': 'retained'}
        wrapped = runpy.run_path(str(HERE/'RETAINED_SOURCE_FAMILY_APPEND.py'), init_globals={'assembly_layout': old})
        registry = {'schema': NS['SOURCE_FAMILY_PROTOCOL'], 'enabled': True, 'families': [{
            'family_id': 'source_derived_modular.H0911.v001', 'enabled': True, 'execution_mode': 'qualification',
            'qualification_target_source_ids': {'GazaRimal': ['CONTRACT_CHECK_ONLY']},
            'qualification_variations': [{'mode': 'exact_reconstruction', 'repeat_count': 1}], 'weight': 1.0}]}
        registry_ref = save_fixture('requested_qualification_invalid.json', registry)
        with self.assertRaisesRegex(wrapped['SourceFamilyQualificationError'], 'requested_qualification_failed'):
            wrapped['assembly_layout'](fixture()[0], {'source_family_registry_ref': registry_ref})
        feature = fixture()[0]; feature['osm_id'] = 'UNASSIGNED_PAD'
        self.assertEqual(wrapped['assembly_layout'](feature, {'source_family_registry_ref': registry_ref})['sentinel'], 'retained')

    def test_ordinary_false_authorization_flag_rejected(self):
        bundle = fixture(); feature, family, native, entry = bundle[:4]
        author = {'schema': NS['SOURCE_ROUTE_PROTOCOL'], 'approved': True, 'family_id': family['family_id'],
            'parent_asset_id': family['parent_asset_id'], 'manager_thread_id': 'IN_MEMORY_TEST_ONLY',
            'preserve_canonical_holds': True, 'actual_named_or_dependency_hold': False,
            'use_scope': 'retained_complete_family_dependency', 'allowed_area_ids': [feature['area_id']],
            'capabilities': ['exact_reconstruction'], 'allowed_repeat_counts': [1], 'placement_scope': 'exact_ids',
            'allowed_source_osm_ids': {feature['area_id']: [feature['osm_id']]},
            'source_family_sha256': NS['_sf_digest'](family), 'native_manifest_sha256': entry['native_manifest_ref']['sha256'],
            'execution_mode': 'ordinary_selection', 'ordinary_selection_authorized': False}
        function = NS['_sf_authorization']; namespace = function.__globals__; original = namespace['_sf_load_ref']
        namespace['_sf_load_ref'] = lambda ref: author
        try:
            with self.assertRaisesRegex(ValueError, 'ordinary_selection_authorization_flag_invalid'):
                function(entry, family, native, 'exact_reconstruction', 1, feature['area_id'], feature['osm_id'])
        finally:
            namespace['_sf_load_ref'] = original


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CandidateChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {'schema': 'environmentpipeline.modular_candidate_contract_checks.v1',
        'checks_run': result.testsRun, 'passed': result.wasSuccessful(),
        'failures': [{'test': str(test), 'detail': detail} for test, detail in result.failures+result.errors],
        'source_families_exercised': 20, 'source_exact_parts_exercised': 585,
        'source_band_formulas_exercised': 8, 'all_native_geometry_in_checks_is_synthetic': True,
        'actual_houdini_cook': False, 'actual_official_engine_output': False, 'native_visual_qualification': False,
        'production_source_or_profiles_changed': False,
        'candidate_append_sha256': hashlib.sha256((HERE/'RETAINED_SOURCE_FAMILY_APPEND.py').read_bytes()).hexdigest()}
    (HERE/'CANDIDATE_CHECKS.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
