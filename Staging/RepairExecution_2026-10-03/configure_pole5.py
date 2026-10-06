"""Prepare/apply one named pole row; native DataTable import stays with the manager."""
import argparse
import copy
import csv
import hashlib
import io
import json
import math
from pathlib import Path

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/RepairExecution_2026-10-03'
BANK = PROJECT / 'Staging/ModelBank/PermanentIntegration_2026-10-02'
SOURCE = BANK / 'catalog_v4_source.json'
CSV = BANK / 'catalog_v4_full.csv'
RECEIPT = HERE / 'POLE5_NORMAL_CONFIGURATION.json'
PROFILES = [BANK / 'AREA_PROFILE.json', PROJECT / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json']
ROW_NAME = 'MB_D7354F34502E4C88BEA903711C9F0A51'
OBJECT = '/Game/AssetsvilleTown/Meshes/StreetProps/SM_utility_pole_5.SM_utility_pole_5'
ASSET = 'current_AssetsvilleTown__Meshes__StreetProps__SM_utility_pole_5'
AREAS = ['GazaRimal', 'GazaShujaiya']
BEFORE_DIGEST = '890a497927a479b5011e9639f165c2640342a6b4bb1d013b099e97bcbd6d57eb'
RELEASE = 'GazaRimal_NormalUse_2026-10-02_v001'
DECISION = 'Aviv_RetainedRepair_2026-10-03_Pole5'
INTS = {'SchemaVersion', 'RunEligible', 'BoundsValid', 'AnchorValid', 'OrientationValid', 'TechnicalPreviewEligible', 'ExplicitHold'}
MINIMUM = [-12.5546875, -10.872679710388184, 0.000030517578125]
MAXIMUM = [12.5546875, 10.872679710388184, 800.0000305175781]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def typed_rows(rows):
    """Same numeric types/order as _nonbuilding_v3_rows; do not re-round floats."""
    result = []
    for raw in rows:
        row = {}
        for key, value in raw.items():
            if key in INTS:
                if key == 'SchemaVersion':
                    row[key] = int(value)
                else:
                    assert str(value).lower() in ('0', '1', 'false', 'true'), (key, value)
                    row[key] = int(str(value).lower() in ('1', 'true'))
            elif key.endswith('Cm') or key in ('SelectionWeight', 'PreviewWeight'):
                row[key] = float(value)
                assert math.isfinite(row[key]), key
            else:
                row[key] = value
        result.append(row)
    return sorted(result, key=lambda row: row['Name'])


def digest(rows):
    return sha(json.dumps(typed_rows(rows), sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def prepare():
    source = json.loads(SOURCE.read_text(encoding='utf-8-sig'))
    with CSV.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        fields, rows = list(reader.fieldnames), list(reader)
    assert len(rows) == len(source['rows']) == 1223
    assert source['native_schema_version'] == 3
    assert source['native_row_struct'] == '/Game/Project/Shared/ModelBank/S_BankReleaseRow_v3'
    assert digest(rows) == BEFORE_DIGEST, 'Current catalog differs; re-review before applying this named update'
    by_name = {row['Name']: row for row in rows}
    assert len(by_name) == len(rows)
    assert all(record['runtime'] == by_name[record['catalog_row_name']] for record in source['rows'])
    before_source = copy.deepcopy(source)
    before_rows = copy.deepcopy(rows)
    record = next(row for row in source['rows'] if row['catalog_row_name'] == ROW_NAME)
    runtime = by_name[ROW_NAME]
    assert record['object_path'] == runtime['ObjectPath'] == OBJECT
    assert record['asset_id'] == runtime['AssetId'] == ASSET
    assert not record['explicit_hold'] and not record['hold_reasons']
    assert runtime['ExplicitHold'] == 'false' and not runtime['HoldReasons']
    assert not record['canonical_run_eligible'] and not record['canonical_qualified']
    assert not record['general_generation_released']
    assert record['environment_style_set'] == runtime['StyleSet'] == 'stylized_town'
    assert record['recorded_category'] == 'StreetProps'
    for axis, low, high in zip('XYZ', MINIMUM, MAXIMUM):
        assert float(runtime['BoundsMin'+axis+'Cm']) == low
        assert float(runtime['BoundsMax'+axis+'Cm']) == high
    slots_receipt = json.loads((HERE / 'INSTANCE_MATERIALS.json').read_text())
    slots = slots_receipt['mesh_slots'][OBJECT]
    assert len(slots) == 1 and slots[0].startswith('/Game/Project/Shared/ModelBank/Materials/Instancing/Repair_20261003/')
    update = {'Role': 'street_pole', 'RequestRole': 'street_pole', 'PlacementRule': 'roadside_pole',
              'RunEligible': 'true', 'BoundsValid': 'true', 'AnchorValid': 'true',
              'AnchorZCm': str(MINIMUM[2]), 'OrientationValid': 'true', 'ForwardAxis': '+X',
              'StyleSet': 'mediterranean_urban', 'SelectionWeight': '1.0',
              'PlacementScope': 'area_zone', 'AllowedAreas': '|'.join(AREAS),
              'AllowedZones': 'roadside', 'AllowedPlacementIds': '',
              'ReleaseId': RELEASE, 'DecisionId': DECISION}
    runtime.update(update)
    record['runtime'] = copy.deepcopy(runtime)
    record['request_role'] = 'street_pole'
    record['placement_rule'] = 'roadside_pole'
    record['allowed_area_policy'] = 'GazaRimal_and_GazaShujaiya_project_scoped_normal_use'
    record['normal_use'] = {
        'eligible': True, 'areas': AREAS, 'release_id': RELEASE, 'decision_id': DECISION,
        'decision_receipt': str(RECEIPT), 'source_style_set_preserved': record['environment_style_set'],
        'context_style_set': 'mediterranean_urban',
        'context_style_evidence': 'Aviv current repair scope permits this non-held native pole; final visual suitability pending',
        'native_scale': [1, 1, 1], 'ground_anchor_policy': 'bounds_bottom_and_horizontal_center',
        'forward_axis_basis': 'native_longest_horizontal_extent; no facade contract inferred',
        'bounds_cm': {'min': MINIMUM, 'max': MAXIMUM}, 'instance_material_slots': slots}
    source['instance_materials'][OBJECT] = slots
    after_digest = digest(rows)
    source['revision'] = '2026-10-03.normal.repair_pole5.v001'
    source['normal_use_catalog_digest'] = source['catalog_sha256'] = after_digest
    source['normal_use_areas'] = AREAS
    source['repair_configuration_receipt'] = str(RECEIPT)
    assert sum(row['RunEligible'] == 'true' for row in rows) == 18
    assert [row['Name'] for row, before in zip(rows, before_rows) if row != before] == [ROW_NAME]
    for record_after, record_before in zip(source['rows'], before_source['rows']):
        if record_after['catalog_row_name'] != ROW_NAME:
            assert record_after == record_before, record_after['catalog_row_name']
        else:
            for key in ('environment_style_set', 'style_evidence', 'recorded_category',
                        'recorded_functional_role_inferred', 'recorded_rights_state',
                        'recorded_dependency_state', 'recorded_visual_state', 'review_hold',
                        'canonical_run_eligible', 'canonical_qualified', 'general_generation_released',
                        'explicit_hold', 'hold_reasons', 'asset_revision_sha256'):
                assert record_after[key] == record_before[key], key
    report = {'schema': 'environmentpipeline.project_pole_normal_configuration.v1',
              'status': 'prepared_not_applied', 'date_local': '2026-10-03',
              'authorization': 'Aviv explicitly requested retained implementation until the environment works; manager assigned this non-held supported native pole for the two existing areas',
              'scope': 'Project use in GazaRimal and GazaShujaiya only; no canonical qualification, global release, rights approval or final visual acceptance',
              'row_name': ROW_NAME, 'asset_id': ASSET, 'object_path': OBJECT,
              'source_style_set': record['environment_style_set'], 'runtime_context_style_set': runtime['StyleSet'],
              'source_category': record['recorded_category'], 'rights_state_preserved': record['recorded_rights_state'],
              'release_id': RELEASE, 'decision_id': DECISION, 'areas': AREAS,
              'before_typed_catalog_sha256': BEFORE_DIGEST, 'after_typed_catalog_sha256': after_digest,
              'digest_policy': 'Sorted native v3 row names; Boolean/schema ints, exact finite Python float conversion, strings; canonical sorted-key compact JSON. No Float32 re-rounding.',
              'row_count': len(rows), 'enabled_rows_before': 17, 'enabled_rows_after': 18,
              'runtime_field_changes': {key: {'before': before_rows[[r['Name'] for r in rows].index(ROW_NAME)][key], 'after': value} for key, value in update.items() if before_rows[[r['Name'] for r in rows].index(ROW_NAME)][key] != value},
              'bounds_min_cm': MINIMUM, 'bounds_max_cm': MAXIMUM, 'native_scale': [1, 1, 1],
              'instance_material_slots': slots, 'other_row_changes': 0,
              'preserved_holds': ['H0013', 'H0907', 'H0051', 'H0958', 'H0094', 'declined palms', 'all other existing holds'],
              'measured_placement_count': None, 'native_table_import': 'not_performed',
              'previous_decision_receipts': [], 'input_file_sha256': {str(SOURCE): sha(SOURCE.read_bytes()), str(CSV): sha(CSV.read_bytes())},
              'stale_source_digest_metadata_before': {key: before_source.get(key) for key in ('normal_use_catalog_digest', 'catalog_sha256')},
              'apply_targets': [str(SOURCE), str(CSV)] + [str(p) for p in PROFILES],
              'manager_next_action': 'Review/apply this script, import the exact CSV into the existing native v3 table, compare native typed digest, save the named table, and run ordinary area generation'}
    profiles = []
    for path in PROFILES:
        profile = json.loads(path.read_text(encoding='utf-8-sig'))
        assert profile['catalog_sha256'] == profile['release']['catalog_sha256'] == BEFORE_DIGEST
        assert profile['release']['id'] == RELEASE
        assert profile['table'] == source['native_data_table_package']
        report['previous_decision_receipts'].append(profile['release']['decision_receipt'])
        profile['catalog_sha256'] = profile['release']['catalog_sha256'] = after_digest
        profile['release']['decision_receipt'] = str(RECEIPT)
        profile['normal_asset_policy']['repair_receipt'] = str(RECEIPT)
        profile['normal_asset_policy']['unavailable_roles'].pop('street_pole', None)
        profile['normal_asset_policy']['native_pole'] = 'configured_supported_non_held_candidate; actual placement and visual suitability require ordinary generation'
        profile['instance_materials'][OBJECT] = slots
        profiles.append((path, profile))
    return source, rows, fields, profiles, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Write the named catalog and profiles; never operate the native editor/table')
    args = parser.parse_args()
    source, rows, fields, profiles, report = prepare()
    if args.apply:
        report['status'] = 'catalog_profiles_configured_native_import_not_performed'
    receipt_text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    RECEIPT.write_text(receipt_text, encoding='utf-8')
    if args.apply:
        receipt_sha = sha(RECEIPT.read_bytes())
        SOURCE.write_text(json.dumps(source, indent=2) + '\n', encoding='utf-8')
        with CSV.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        for path, profile in profiles:
            profile['release']['decision_sha256'] = receipt_sha
            path.write_text(json.dumps(profile, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'row': ROW_NAME,
                      'after_typed_catalog_sha256': report['after_typed_catalog_sha256'],
                      'receipt': str(RECEIPT), 'native_table_import': 'not_performed'}))


if __name__ == '__main__':
    main()
