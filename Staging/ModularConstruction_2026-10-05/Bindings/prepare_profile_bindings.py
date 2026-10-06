"""Prepare the exact existing profile changes after all 20 imports complete.

Only owned staging copies are written. Native HDA import, wrapper binding and
the two production profile/map saves belong to the manager's native phase.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def checked(ref_value):
    path = Path(ref_value['path'])
    assert ref(path)['sha256'] == ref_value['sha256'], ('input_changed', path)
    return read(path)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
    return ref(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registry-ref', required=True)
    args = parser.parse_args()
    registry_ref = read(Path(args.registry_ref))
    registry = checked(registry_ref)
    assert registry['enabled'] is True
    families = registry['families']
    assert len(families) == len({f['family_id'] for f in families}) == 20
    assert all(f['enabled'] and f['execution_mode'] == 'connection' for f in families)
    assert sum(f['native_part_count'] for f in registry['staged_native_bindings']) == 609
    for family in families:
        native = checked(family['native_manifest_ref'])
        assert native['family_id'] == family['family_id']
        assert native['actual_named_or_dependency_hold'] is False
        assert native['parent_canonical_hold_preserved'] is True
        assert family['capabilities']['exact_reconstruction']['allowed_repeat_counts'] == [1]
        assert not family['capabilities'].get('one_axis_extension', {}).get('enabled', False)
    plan = read(HERE / 'NATIVE_BINDING_PLAN.json')
    prepared = []
    for item in plan['profiles']:
        original = item['profile']['original']
        profile = checked(original)
        assert profile == checked(item['profile']['backup'])
        assert profile['hda'] == plan['native_hda_identity'] == item['hda']
        assert 'source_family_registry_ref' not in profile['building_assembly_contract']
        proposed = json.loads(json.dumps(profile))
        proposed['building_assembly_contract']['source_family_registry_ref'] = registry_ref
        folder = Path(original['path']).parent.name
        proposed_ref = save(HERE / 'ProposedProfiles' / folder / 'AREA_PROFILE.json', proposed)
        parameter_ref = save(HERE / 'ProposedProfiles' / folder / 'building_assembly_contract.json',
            proposed['building_assembly_contract'])
        prepared.append({'target_profile': original, 'proposed_profile': proposed_ref,
            'map': profile['map'], 'native_hda_identity': profile['hda'], 'bank_table': profile['table'],
            'parameter_name': 'building_assembly_contract_json', 'parameter_value_ref': parameter_ref,
            'changed_semantic_fields': ['building_assembly_contract.source_family_registry_ref']})
    result = {'schema': 'environmentpipeline.modular_prepared_native_profile_bindings.v1',
        'status': 'PREPARED_FOR_OWNER_APPLICATION', 'registry_ref': registry_ref,
        'native_family_count': 20, 'native_saved_part_count': 609,
        'native_hda_source_ref': plan['new_external_source'], 'profiles': prepared,
        'production_profiles_changed': False, 'native_maps_changed': False,
        'actual_generation_performed': False, 'additional_tests_run': False}
    result_ref = save(HERE / 'PREPARED_NATIVE_BINDINGS.json', result)
    print(json.dumps(result_ref))


if __name__ == '__main__':
    main()
