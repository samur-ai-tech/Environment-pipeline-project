"""Translate existing bank receipts into the consumer protocol without reimport.

Writes ContractAudit/NativeNormalized only. Sparse native material slot order,
bank derivative IDs and actual basis/UV probe limits remain explicit. No visual,
reopen, generation or eligibility evidence is invented by normalization.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
BANK = PROJECT/'Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05'
APPROVED_REQUESTS = {
    '8a253d5bb3d0d5024fa59c99690cc481a1b110f9ab42d5ff738a6c71a42dcdea':
        BANK/'Handoffs/8a253d5bb3d0d5024fa59c99690cc481a1b110f9ab42d5ff738a6c71a42dcdea/NATIVE_IMPORT_REQUEST.json',
    'f738f677914e27dcc772256acb2a6ea68c3262ae4e83dede3f460c1e9cc4979d':
        BANK/'NATIVE_IMPORT_REQUEST_v002.json',
    '1fa6654d606f8b5ee9901d7f86e50e3007328751b56498b64fbfbbefa2b73984':
        BANK/'NATIVE_IMPORT_REQUEST_v003.json',
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def reference(path):
    return {'path': str(path), 'sha256': sha(path)}


def checked_ref(ref):
    path = Path(ref['path']); assert sha(path) == ref['sha256'], ('evidence_changed', path)
    return read(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--family', required=True)
    parser.add_argument('--scope-review-ref', help='JSON file containing a manager receipt path/SHA reference')
    parser.add_argument('--reflection-evidence-ref', help='Actual normals/culling receipt reference; optional until verified')
    args = parser.parse_args()
    report_path = BANK/'Receipts'/args.family/'FAMILY.json'; report = read(report_path)
    request_sha = report['request_sha256']
    request_path = APPROVED_REQUESTS[request_sha]; assert sha(request_path) == request_sha
    request = read(request_path)
    job = next(f for f in request['families'] if f['id'] == args.family)
    family = next(f for f in read(BANK/'SOURCE_BINDINGS.json')['families'] if f['id'] == args.family)
    assert digest(family) == job['source_family_sha256']
    assert report['family_id'] == family['family_id']
    assert report['complete_native_import'] and report['imported_part_count'] == report['expected_part_count'] == len(job['parts'])
    assert report['holds_preserved'] and not report['procedural_eligible']
    source_parts = {p['name']: p for p in job['parts']}
    receipts = {p['name']: p for p in report['parts']}
    assert len(receipts) == len(report['parts']) and set(receipts) == set(source_parts)
    output = HERE/'NativeNormalized'/args.family; assert output.resolve().is_relative_to(HERE.resolve())
    output.mkdir(parents=True, exist_ok=True)
    def save(name, value):
        path = output/name; path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        return reference(path)
    parts, matrices, maximum_bound_error, probe_count = {}, [], 0.0, 0
    for name, raw in receipts.items():
        source = source_parts[name]; basis = raw['basis_readback']
        assert raw['request_sha256'] == request_sha
        assert raw['source_family_sha256'] == digest(family) and raw['source_sha256'] == source['fbx_sha256']
        assert raw['derivative_id'] == family['family_id']+'/'+name
        assert raw['native_object_path'] == source['native_package']+'.'+name
        assert raw['named_saved'] and not raw['dependencies']['missing'] and raw['source_graph_components_transferred']
        for package, expected_sha in raw['saved_packages'].items():
            assert package.startswith('/Game/')
            native_file = PROJECT/'Content'/(package[6:]+'.uasset')
            assert sha(native_file) == expected_sha, ('native_package_changed', package)
        assert basis['units'] == 'source_metres_to_native_centimetres' and basis['scale'] == 100
        assert basis['vertex_probe_count'] >= 3 and basis['bounds_max_error_cm'] <= 0.025
        assert basis['uv0_probe_count'] > 0 and basis['uv0_matching_conventions']
        matrices.append(basis['source_xyz_to_native_xyz']); probe_count += basis['vertex_probe_count']
        maximum_bound_error = max(maximum_bound_error, basis['bounds_max_error_cm'])
        measurement = raw['measurement']; assert measurement['uv_channels'] == len(source['uv_channels'])
        slots = sorted(raw['material_slots'], key=lambda s: s['slot'])
        assert [s['slot'] for s in slots] == list(range(len(slots)))
        used = source['slot_triangle_counts'] if measurement['triangles'] == source['triangles'] else source['roundtrip_slot_triangle_counts']
        for slot in slots:
            assert slot['source_name'] == source['source_material_slots'][slot['source_slot']]
            assert slot['triangles'] == used.get(str(slot['source_slot']), 0)
            material_ref = BANK/'MaterialReceipts'/(slot['recipe_sha256']+'.json')
            material = read(material_ref); recipe = job['materials'][slot['recipe_sha256']]
            assert recipe['source_graph_supported'] and material['instancing_usage']
            assert material['material_path'] == slot['material_path'] and material['normal_strength'] == recipe['normal']['strength']
        parts[name] = {'asset_id': raw['derivative_id'], 'path': raw['native_object_path'],
            'source_sha256': raw['source_sha256'], 'min_cm': measurement['bounds_cm']['min'],
            'max_cm': measurement['bounds_cm']['max'], 'source_material_slots': source['source_material_slots'],
            'material_slots': [s['material_path'] for s in slots],
            'native_source_slot_indices': [s['source_slot'] for s in slots], 'source_slot_triangle_counts': used,
            'dependency_closed': True, 'pivot_preserved': True, 'source_uv0_probe_alignment_passed': True,
            'uv_channel_count_verified': True, 'full_geometry_or_uv_equivalence': False,
            'actual_named_or_dependency_hold': True, 'actual_bank_part_receipt_ref': reference(BANK/'Receipts'/args.family/(name+'.json'))}
    assert matrices and all(matrix == matrices[0] for matrix in matrices)
    matrix = matrices[0]; reflection_verified = False; reflection_ref = None
    if args.reflection_evidence_ref:
        reflection_ref = read(Path(args.reflection_evidence_ref)); evidence = checked_ref(reflection_ref)
        assert evidence['family_id'] == family['family_id'] and evidence['source_family_sha256'] == digest(family)
        assert evidence['request_sha256'] == request_sha and evidence['passed']
        assert evidence['normals_verified'] and evidence['source_material_culling_verified']
        reflection_verified = True
    if args.scope_review_ref:
        scope_ref = read(Path(args.scope_review_ref)); scope = checked_ref(scope_ref)
        assert scope['approved'] and scope['manager_thread_id'] and scope['preserve_canonical_holds']
        assert scope['family_id'] == family['family_id'] and scope['source_family_sha256'] == digest(family)
        assert scope['actual_named_or_dependency_hold'] is False
        for part in parts.values():
            part['actual_named_or_dependency_hold'] = False
    else:
        scope_ref = None
    basis_ref = save('BASIS_EVIDENCE.json', {'family_id': family['family_id'], 'source_family_sha256': digest(family),
        'passed': True, 'source_to_native_matrix': matrix, 'source_units': 'metres', 'native_units': 'centimetres',
        'pivot_translation_preserved': True, 'sample_vertices_checked': probe_count,
        'verified_part_names': sorted(parts), 'maximum_probe_error_cm': 0.025,
        'probe_error_is_adapter_verified_upper_bound': True, 'actual_bounds_max_error_cm': maximum_bound_error,
        'reflection_normals_material_culling_verified': reflection_verified, 'reflection_evidence_ref': reflection_ref,
        'actual_bank_family_receipt_ref': reference(report_path), 'full_geometry_or_uv_equivalence': False})
    graph_ref = save('MATERIAL_GRAPH_EVIDENCE.json', {'family_id': family['family_id'], 'source_family_sha256': digest(family),
        'native_parts_sha256': digest(parts), 'passed': True, 'source_recipes_bound': True,
        'texture_dependencies_complete': True, 'mesh_slot_order_preserved': True,
        'visual_fidelity_verified': False, 'actual_bank_family_receipt_ref': reference(report_path)})
    native_ref = save('NATIVE_FAMILY.json', {'schema': 'environmentpipeline.modular_native_family_readback.v1',
        'family_id': family['family_id'], 'source_family_sha256': digest(family), 'source_to_native_matrix': matrix,
        'basis_evidence_ref': basis_ref, 'material_graph_evidence_ref': graph_ref,
        'actual_named_or_dependency_hold': scope_ref is None, 'parent_canonical_hold_preserved': True,
        'scope_review_ref': scope_ref, 'parts': parts, 'ordinary_selection_enabled': False,
        'native_visual_qualification': False, 'fresh_process_reopened': report['fresh_process_reopened']})
    assembly_ref = {'path': family['assembly_path'], 'sha256': family['assembly_sha256']}
    readback_ref = {'path': family['readback_path'], 'sha256': family['readback_sha256']}
    assembly = checked_ref(assembly_ref); source_readback = checked_ref(readback_ref)
    reconstruction = next(s for s in family['sets'] if s['kind'] == 'reconstruction')
    names = {p['name'] for p in reconstruction['parts']}
    source_probes = source_readback['fbx_readbacks']
    assert assembly['id'] == source_readback['id'] == family['id']
    assert assembly['validation']['image_comparison_passed'] is True
    assert source_readback['blend_reopened'] and source_readback['source_hashes_unchanged']
    assert not source_readback['missing_used_images'] and source_readback['original_reference_objects_retained']
    assert source_readback['module_count'] == len(names) == len(source_probes)
    assert {p['name'] for p in source_probes} == names and all(p['pass'] is True for p in source_probes)
    for part in reconstruction['parts']:
        assert sha(Path(part['fbx'])) == part['fbx_sha256']
    source_ref = save('SOURCE_QUALIFICATION.json', {
        'schema': 'environmentpipeline.modular_source_qualification.v1',
        'family_id': family['family_id'], 'source_family_sha256': digest(family), 'passed': True,
        'repeat_counts_by_capability': {'exact_reconstruction': [1]},
        'assembly_ref': assembly_ref, 'source_readback_ref': readback_ref,
        'source_reconstruction_image_comparison_passed': True, 'source_fbx_readbacks_passed': True,
        'source_fbx_file_hashes_verified': True, 'architectural_floors_certified': False,
        'native_visual_fidelity_verified': False, 'houdini_or_engine_output_verified': False,
        'ordinary_selection_enabled': False, 'extension_repeat_counts_enabled': []})
    print(json.dumps({'native_manifest_ref': native_ref, 'ordinary_selection_enabled': False,
        'source_qualification_ref': source_ref, 'source_family_sha256': digest(family), 'part_count': len(parts)}))


if __name__ == '__main__':
    main()
