"""Prepare review-only evidence; never edit production, native packages or approvals."""
import copy
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANK = HERE.parent
PROJECT = BANK.parents[2]
AUDIT = PROJECT / 'Staging/ModularConstruction_2026-10-05/ContractAudit'
BINDINGS = AUDIT.parent / 'Bindings'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def ref(p):
    return {'path': str(p), 'sha256': sha(p)}

def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return ref(p)

def main():
    request_path = BANK / 'NATIVE_IMPORT_REQUEST_v003.json'
    request_sha = sha(request_path)
    assert request_sha.startswith('1fa6654d')
    source_path = AUDIT / 'normalize_bank_readback.py'
    original = source_path.read_text(encoding='utf-8-sig')
    marker = "        BANK/'NATIVE_IMPORT_REQUEST_v002.json',\n"
    assert original.count(marker) == 1
    proposed = original.replace(marker, marker + "    '" + request_sha + "':\n        BANK/'NATIVE_IMPORT_REQUEST_v003.json',\n")
    (HERE / 'normalize_bank_readback.proposed.py').write_text(proposed, encoding='utf-8')
    (HERE / 'normalize_bank_readback.patch').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), proposed.splitlines(True),
        fromfile=str(source_path), tofile=str(source_path))), encoding='utf-8')
    # Execute the candidate in this review directory; keep every canonical file untouched.
    staged = proposed.replace('PROJECT = HERE.parents[2]', 'PROJECT = Path(' + repr(str(PROJECT)) + ')')
    runner = HERE / 'normalize_review_only.py'
    runner.write_text(staged, encoding='utf-8')
    registry = read(AUDIT / 'DISABLED_SOURCE_FAMILY_REGISTRY.json')
    normalized, incomplete = [], []
    for family_path in sorted((BANK / 'Receipts').glob('*/FAMILY.json')):
        family = read(family_path)
        short_id = family_path.parent.name
        if not family['complete_native_import']:
            incomplete.append({'id': short_id, 'saved': family['imported_part_count'], 'expected': family['expected_part_count']})
            continue
        result = subprocess.run([sys.executable, str(runner), '--family', short_id], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(short_id + '\n' + result.stdout + result.stderr)
        value = json.loads(result.stdout)
        value['id'] = short_id
        normalized.append(value)
        entry = next(e for e in registry['families'] if e['family_id'] == family['family_id'])
        entry.update(native_manifest_ref=value['native_manifest_ref'],
                     source_qualification_ref=value['source_qualification_ref'],
                     enabled=False, execution_mode='connection', route_authorization_ref=None)
        print(json.dumps({'normalized': short_id, 'parts': value['part_count']}), flush=True)
    assert len(normalized) == 18 and {x['id'] for x in incomplete} == {'H0017', 'H0019'}
    registry.update(enabled=False, ordinary_selection_enabled=False,
                    ordinary_selection_configured=False, actual_generation_completed=False,
                    review_status='AWAITING_MANAGER_REVIEW_NOT_ACTIVATED',
                    staged_native_bindings=normalized)
    registry_ref = save(HERE / 'DRAFT_SOURCE_FAMILY_REGISTRY.json', registry)
    plan = read(BINDINGS / 'NATIVE_BINDING_PLAN.json')
    profiles = []
    preserved = [ref(source_path), ref(request_path), ref(BANK / 'SOURCE_BINDINGS.json')]
    for item in plan['profiles']:
        original_ref = item['profile']['original']
        path = Path(original_ref['path'])
        assert sha(path) == original_ref['sha256']
        value = read(path)
        assert 'source_family_registry_ref' not in value['building_assembly_contract']
        candidate = copy.deepcopy(value)
        candidate['building_assembly_contract']['source_family_registry_ref'] = registry_ref
        target = HERE / 'ProposedProfiles' / path.parent.name / 'AREA_PROFILE.json'
        profiles.append({'original': ref(path), 'proposed': save(target, candidate),
                         'changed_semantic_fields': ['building_assembly_contract.source_family_registry_ref'],
                         'apply_status': 'DO_NOT_APPLY_DISABLED_REVIEW_REGISTRY'})
        preserved.append(ref(path))
    for key in ('new_external_source', 'build_receipt'):
        p = Path(plan[key]['path'])
        assert sha(p) == plan[key]['sha256']
        preserved.append(ref(p))
    native_hda = Path(plan['native_hda_before']['original']['path'])
    assert sha(native_hda) == plan['native_hda_before']['original']['sha256']
    preserved.append(ref(native_hda))
    request = read(request_path)
    queue = read(BANK / 'REPAIR_QUEUE_v004.json')
    failures = []
    for failure in queue['failures']:
        family = next(f for f in request['families'] if f['id'] == failure['family'])
        part = next(p for p in family['parts'] if p['name'] == failure['name'])
        native = PROJECT / 'Content' / (part['native_package'][6:] + '.uasset')
        failures.append({'id': part['derivative_id'], 'native_package': part['native_package'],
                         'source_triangles': part['triangles'],
                         'expected_native_triangles_from_failure': part['triangles'] - 1,
                         'source_slot_triangle_counts': part['slot_triangle_counts'],
                         'roundtrip_slot_triangle_counts': part.get('roundtrip_slot_triangle_counts'),
                         'source_material_slots': part['source_material_slots'],
                         'native_file_exists_now': native.exists(),
                         'native_file_sha256_now': sha(native) if native.exists() else None,
                         'repair_executed': False, 'live_per_slot_face_check': 'PENDING_NEW_EDITOR_LEASE'})
    save(HERE / 'SIX_MESH_REPAIR_PLAN.json', {
        'request_ref': ref(request_path), 'allowed_packages': [f['native_package'] for f in failures],
        'allowance': 'Only these six named meshes; source minus exactly one triangle; every source material slot must map uniquely. Per-slot native counts may equal source except one occupied slot may lose exactly one triangle; no gained faces, no removed slot, no other difference. Record exact native slot counts before material assignment. Keep bounds and UV checks unchanged.',
        'execution': 'Reimport at the existing native package path, bind existing modular materials, named-save only, record measured allowance in separate pinned receipt without modifying immutable v003 request or source manifests.',
        'failures': failures})
    save(HERE / 'REVIEW_MANIFEST.json', {
        'status': 'PREPARED_REVIEW_ONLY_MANAGER_REVIEW_AND_NATIVE_LEASE_PENDING',
        'manager_thread_id': '01a10789-2e6a-7321-ad85-0a2964f8a937',
        'operator_thread_id': '01a10c93-8b7e-7d70-8f75-ca340ae6db99',
        'v003_request_ref': ref(request_path), 'normalizer_original_ref': ref(source_path),
        'normalizer_proposed_ref': ref(HERE / 'normalize_bank_readback.proposed.py'),
        'normalizer_patch_ref': ref(HERE / 'normalize_bank_readback.patch'),
        'draft_registry_ref': registry_ref, 'normalized_complete_families': normalized,
        'normalized_part_count': sum(v['part_count'] for v in normalized),
        'incomplete_families': incomplete, 'profiles': profiles,
        'preserved_inputs': preserved, 'native_writes_performed': False,
        'manager_review_completed': False, 'production_reachable_families': 0,
        'hda_promoted': False, 'generation_performed': False,
        'canonical_holds_unchanged': True,
        'placement_requirement': 'Use the complete-family consumer basis transform of each assembly_translation_m, equivalent to native_assembly_translation_cm. Common-origin placement overlaps these parts.'})

if __name__ == '__main__':
    main()
