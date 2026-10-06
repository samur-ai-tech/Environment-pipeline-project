"""Bind completed bank imports to the retained consumer without native edits.

Every enabled entry is derived from actual saved bank receipts and the current
manager's exact family scope. Source templates and partial imports cannot enable
an entry. This operation does not run generation or claim visual qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
MANAGER = PROJECT / 'Staging/ManagedSystemsAstra_2026-10-04'
BANK = PROJECT / 'Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return ref(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--family', action='append', required=True)
    parser.add_argument('--execution-mode', choices=['connection', 'qualification'], default='connection')
    args = parser.parse_args()
    assert len(set(args.family)) == len(args.family)
    registry = read(HERE / 'DISABLED_SOURCE_FAMILY_REGISTRY.json')
    scopes = MANAGER / 'ModularFamilyScopes'
    placements = read(HERE.parent / 'Validation/QUALIFICATION_PLACEMENT_PLAN.json')
    by_id = {p['id']: p for p in placements['placements']}
    template = read(HERE / 'QUALIFICATION_AUTHORIZATION_TEMPLATE.json')
    connected = []
    for short_id in args.family:
        placement = by_id[short_id]
        entry = next(e for e in registry['families'] if e['family_id'] == placement['family_id'])
        scope_path = scopes / (short_id + '.json')
        scope = read(scope_path)
        assert scope['approved'] is True and scope['preserve_canonical_holds'] is True
        assert scope['actual_named_or_dependency_hold'] is False
        assert scope['family_id'] == entry['family_id']
        assert scope['source_family_sha256'] == entry['source_family_sha256']
        actual = read(BANK / 'Receipts' / short_id / 'FAMILY.json')
        assert actual['complete_native_import'] is True
        output = HERE / 'NativeNormalized' / short_id
        scope_wrapper = output / 'SCOPE_REF.json'
        save(scope_wrapper, ref(scope_path))
        process = subprocess.run([sys.executable, str(HERE / 'normalize_bank_readback.py'),
            '--family', short_id, '--scope-review-ref', str(scope_wrapper)],
            capture_output=True, text=True)
        if process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        normalized = json.loads(process.stdout)
        area_id, source_id = placement['area_id'], str(placement['osm_id'])
        authorization = dict(template)
        authorization.pop('template_only', None)
        authorization.update(approved=True, family_id=entry['family_id'],
            parent_asset_id=entry['parent_asset_id'], manager_thread_id=scope['manager_thread_id'],
            source_family_sha256=entry['source_family_sha256'],
            native_manifest_sha256=normalized['native_manifest_ref']['sha256'],
            actual_named_or_dependency_hold=False, allowed_area_ids=[area_id],
            allowed_source_osm_ids={area_id: [source_id]}, capabilities=['exact_reconstruction'],
            allowed_repeat_counts=[1], manager_scope_ref=ref(scope_path),
            placement_plan_ref=ref(HERE.parent / 'Validation/QUALIFICATION_PLACEMENT_PLAN.json'),
            additional_test_cycles_requested=False)
        if args.execution_mode == 'connection':
            assert scope['ordinary_selection_authorized'] is True
            assert scope['connection_without_additional_tests_authorized'] is True
            assert scope['unperformed_validation_remains_pending'] is True
            assert scope['allowed_area_ids'] and all(a in ('GazaRimal', 'GazaShujaiya') for a in scope['allowed_area_ids'])
            authorization.update(execution_mode='connection', ordinary_selection_authorized=True,
                connection_without_additional_tests_authorized=True,
                unperformed_validation_remains_pending=True, placement_scope='approved_areas',
                allowed_area_ids=scope['allowed_area_ids'], allowed_source_osm_ids={})
        route_ref = save(output / 'ROUTE_AUTHORIZATION.json', authorization)
        entry.update(enabled=True, execution_mode=args.execution_mode,
            native_manifest_ref=normalized['native_manifest_ref'],
            source_qualification_ref=normalized['source_qualification_ref'],
            route_authorization_ref=route_ref,
            qualification_variations=[{'mode': 'exact_reconstruction', 'repeat_count': 1}],
            qualification_target_source_ids={area_id: [source_id]})
        if args.execution_mode == 'connection':
            entry['capabilities']['exact_reconstruction'].update(enabled=True,
                enabled_basis='Direct user requested ordinary connection using source reconstruction and actual native saved bindings; further lifecycle and visual evidence remains pending.')
            entry['qualification_variations'] = []
            entry['qualification_target_source_ids'] = {}
        connected.append({'id': short_id, 'family_id': entry['family_id'],
            'native_part_count': normalized['part_count'], 'area_id': area_id, 'source_osm_id': source_id,
            'native_manifest_ref': normalized['native_manifest_ref']})
    registry.update(enabled=True, staged_native_bindings=connected,
        ordinary_selection_enabled=False,
        ordinary_selection_configured=args.execution_mode == 'connection', actual_generation_completed=False,
        additional_tests_run=False)
    serialized = json.dumps(registry, indent=2, allow_nan=False) + '\n'
    digest = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    registry_path = HERE / 'Registries' / (digest + '.json')
    registry_ref = save(registry_path, registry)
    save(HERE / 'STAGED_NATIVE_REGISTRY_REF.json', registry_ref)
    print(json.dumps({'registry_ref': registry_ref, 'native_bound_families': connected,
        'ordinary_selection_enabled': False,
        'ordinary_selection_configured': args.execution_mode == 'connection',
        'actual_generation_completed': False}))


if __name__ == '__main__':
    main()
