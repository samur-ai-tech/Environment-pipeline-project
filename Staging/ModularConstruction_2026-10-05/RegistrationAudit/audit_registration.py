"""Read-only reconciliation for the retained twenty-family source delivery.

Only writes receipts beside this script. Does not import Unreal/Houdini modules,
open native editors, alter the catalog, or create runtime identities.
"""
import collections
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INTEGRATION = ROOT / 'Staging/BankIntegration_2026-10-04'
CAT_PATH = ROOT / 'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
SOURCE_ROOT = Path('C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/WholeBuildingConversions')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')

def package_file(obj):
    return ROOT / 'Content' / (obj.split('.')[0][6:] + '.uasset') if obj.startswith('/Game/') else None

def check(path, expected=None):
    path = Path(path)
    result = {'path': str(path), 'exists': path.is_file()}
    if result['exists']:
        result['sha256'] = sha(path)
        result['bytes'] = path.stat().st_size
    if expected:
        result['expected_sha256'] = expected
        result['matches'] = result.get('sha256') == expected.lower()
    return result

registration_path = INTEGRATION / 'MODULAR_SOURCE_FAMILIES.json'
registration = read(registration_path)
catalog = read(CAT_PATH)
records = {row['asset_id']: row for row in catalog['rows']}
assert len(records) == len(catalog['rows']), 'duplicate_canonical_asset_identity'
manifest = read(SOURCE_ROOT / 'MANIFEST.json')
assert registration['family_count'] == manifest['family_count'] == 20
assert registration['source_module_count'] == manifest['module_count'] == 585
assert registration['extension_part_count'] == manifest['additional_extension_parts'] == 24

recipes = {}
queues = {}
for directory in [INTEGRATION, INTEGRATION / 'CategoryBatches/WholeBuildings']:
    for filename, target in [('EXTERNAL_MATERIAL_RECIPES.json', recipes), ('EXTERNAL_IMPORT_QUEUE.json', queues)]:
        path = directory / filename
        if path.exists():
            for item in read(path):
                target[item['asset_id']] = {'record': item, 'path': str(path), 'sha256': sha(path)}

content_by_name = collections.defaultdict(list)
for path in (ROOT / 'Content').rglob('*.uasset'):
    content_by_name[path.stem].append(path)

checks = []
families = []
part_jobs = []
material_jobs = []
for family in registration['families']:
    family_id = family['family_id']
    aid = family['parent_asset_id']
    sid = aid.split('.')[-1]
    source_files = family['source_files']
    record = records[aid]
    assert record['catalog_row_name'] == family['parent_catalog_row'], (sid, 'parent_identity_changed')
    assembly = read(source_files['assembly'])
    readback = read(source_files['readback'])
    assembly_check = check(source_files['assembly'], source_files['assembly_sha256'])
    readback_check = check(source_files['readback'], source_files['readback_sha256'])
    checks.extend([assembly_check, readback_check])
    originals = {kind: check(source_files['original_' + kind], source_files['original_sha256'][kind]) for kind in ('blend', 'fbx')}
    checks.extend(originals.values())
    assert assembly['module_count'] == readback['module_count'] == len(family['modules'])
    source_modules = {module['name']: module for module in assembly['modules']}
    source_readbacks = {part['name']: part for part in readback['fbx_readbacks']}
    assert set(source_modules) == set(source_readbacks) == {part['name'] for part in family['modules']}

    parent_obj = record['runtime']['ObjectPath']
    parent_file = package_file(parent_obj)
    parent_package = check(parent_file, record.get('asset_revision_sha256')) if parent_file else None
    receipts = []
    for directory in [INTEGRATION, INTEGRATION / 'CategoryBatches/WholeBuildings']:
        path = directory / ('IMPORTED_' + aid.replace('.', '_') + '.json')
        if path.exists():
            receipt = read(path)
            receipts.append({'path': str(path), 'sha256': sha(path), 'record': receipt,
                             'package': check(package_file(receipt['native_path']), receipt['native_sha256'])})
    saved_receipt = next((item for item in receipts if item['record'].get('saved') and item['package'].get('matches')), None)
    source_materials = list(dict.fromkeys(name for module in assembly['modules'] for name in module['source_material_slots']))
    mat_candidates = {}
    if saved_receipt:
        receipt = saved_receipt['record']
        for name, native in zip(receipt['material_slot_sources'], receipt['native_material_slots']):
            mat_candidates[name] = {'native_path': native, 'basis': saved_receipt['path']}
    if sid == 'H0017':
        recovery_request = read(INTEGRATION / 'H0017_RECOVERY_REQUEST.json')
        recovery_result = read(INTEGRATION / 'H0017_RECOVERY_RESULT.json')
        if recovery_result['passed'] and parent_package and parent_package.get('sha256') == recovery_result['native_mesh_sha256']:
            mat_candidates = {binding['source_material']: {'native_path': binding['native_material'],
                              'basis': str(INTEGRATION / 'H0017_RECOVERY_REQUEST.json'),
                              'exact_namespace_alias': binding['native_imported_name'],
                              'recipe_sha256': binding['recipe_sha256']} for binding in recovery_request['material_bindings']}
    materials = []
    recipe = recipes.get(aid)
    recipe_names = {item['source_material'] for item in recipe['record']['materials']} if recipe else set()
    for name in source_materials:
        candidate = mat_candidates.get(name)
        native = candidate['native_path'] if candidate else None
        package = check(package_file(native)) if native else None
        item = {'family_id': family_id, 'parent_asset_id': aid, 'source_material': name,
                'native_material_candidate': native, 'native_package': package,
                'candidate_basis': candidate, 'recipe_available': name in recipe_names,
                'recipe_registry': recipe['path'] if recipe else None,
                'reusable_after_native_recipe_uv_and_instancing_readback': bool(candidate and package and package['exists']),
                'native_appearance_qualified_for_new_parts': False,
                'action': 'readback_existing_material_then_bind' if candidate and package and package['exists'] else 'build_missing_derivative_material_from_retained_recipe'}
        materials.append(item)
        material_jobs.append(item)
    bounds = {'min': [min(part['local_bounds_m']['min'][axis] + part['original_assembly_translation_m'][axis] for part in family['modules']) for axis in range(3)],
              'max': [max(part['local_bounds_m']['max'][axis] + part['original_assembly_translation_m'][axis] for part in family['modules']) for axis in range(3)]}

    extension_path = source_files.get('extension')
    extension = read(extension_path) if extension_path else None
    extension_readback = read(Path(extension_path).with_name('READBACK.json')) if extension_path else None
    if extension_path:
        checks.append(check(extension_path))
        checks.append(check(Path(extension_path).with_name('READBACK.json')))
        assert extension == family['source_capabilities']['extension'], (sid, 'stale_registered_extension')
    jobs = []
    for kind, parts in [('exact_reconstruction', assembly['modules']), ('one_axis_extension', extension['source_derived_parts'] if extension else [])]:
        for part in parts:
            name = part['name']
            source_check = check(part['fbx'], part['sha256'])
            checks.append(source_check)
            existing = content_by_name.get(name, [])
            assert len(existing) <= 1, (name, 'duplicated_native_package_names')
            part_key = family_id + '.part.' + name
            assert part_key not in records, (name, 'part_already_registered')
            proposed_package = '/Game/Project/Shared/ModelBank/Prepared/Modular/' + sid + '/v001/' + name
            dimensions = [part['local_bounds_m']['max'][axis] - part['local_bounds_m']['min'][axis] for axis in range(3)]
            readback_row = source_readbacks.get(name) if kind == 'exact_reconstruction' else next(item for item in extension_readback['fbx_readbacks'] if item['name'] == name)
            job = {'part_key_proposed': part_key, 'family_id': family_id, 'parent_asset_id': aid,
                   'parent_catalog_row': family['parent_catalog_row'], 'name': name, 'assembly_kind': kind,
                   'source_fbx': part['fbx'], 'source_sha256': part['sha256'], 'source_hash_check': source_check,
                   'source_local_bounds_m': part['local_bounds_m'], 'source_dimensions_m': dimensions,
                   'assembly_translation_m': part.get('original_assembly_translation_m', part.get('assembly_translation_m')),
                   'source_role_label': part['role'], 'architectural_role_verified': False,
                   'source_material_slots': part.get('source_material_slots', source_materials),
                   'source_uv_channels': part.get('uv_channels', assembly['modules'][0]['uv_channels']),
                   'source_triangles': part['triangles'], 'blender_roundtrip': readback_row,
                   'existing_native_packages_with_exact_name': [str(path) for path in existing],
                   'destination_package_proposed': proposed_package, 'destination_is_established_canonical': False,
                   'import_action': 'reconcile_existing_exact_identity_before_import' if existing else 'import_missing_part_without_replace_existing',
                   'rights_state_preserved': record['recorded_rights_state'],
                   'explicit_hold_preserved': record['runtime']['ExplicitHold'], 'hold_reasons_preserved': record['hold_reasons'],
                   'technical_qualified': False, 'procedural_selection_enabled': False}
            jobs.append(job)
            part_jobs.append(job)

    families.append({'family_id': family_id, 'source_id': sid, 'source_name': family['source_name'],
                     'parent_asset_id': aid, 'parent_catalog_row': family['parent_catalog_row'],
                     'parent_object_path_current': parent_obj, 'parent_package': parent_package,
                     'parent_import_receipts': receipts, 'parent_catalog_binding': record.get('native_bank_integration'),
                     'source_original_hash_checks': originals, 'assembly_file': assembly_check, 'readback_file': readback_check,
                     'module_count': len(assembly['modules']), 'extension_count': len(extension['source_derived_parts']) if extension else 0,
                     'source_exact_reconstruction_passed': assembly['validation']['image_comparison_passed'] and all(item['pass'] for item in readback['fbx_readbacks']),
                     'source_original_bounds_m': bounds, 'source_dimensions_m': [bounds['max'][axis]-bounds['min'][axis] for axis in range(3)],
                     'extension_corridor': extension['corridor'] if extension else None,
                     'extension_blender_readback': extension_readback,
                     'materials': materials, 'module_bound_count': sum(bool(item['native_object_path']) for item in family['modules']),
                     'native_part_packages_by_exact_name_count': sum(bool(item['existing_native_packages_with_exact_name']) for item in jobs),
                     'source_capabilities': family['source_capabilities'], 'current_generator_mapping': family['current_generator_mapping'],
                     'integration_status': family['integration_status'], 'rights_state_preserved': record['recorded_rights_state'],
                     'explicit_hold_preserved': record['runtime']['ExplicitHold'], 'hold_reasons_preserved': record['hold_reasons'],
                     'parent_runtime_eligible': record['runtime']['RunEligible']})
    print(json.dumps({'source_id': sid, 'parts': len(jobs), 'parent_saved': bool(parent_package and parent_package['exists']), 'source_materials': len(materials)}), flush=True)

assert len(part_jobs) == 609
assert len({job['part_key_proposed'] for job in part_jobs}) == 609
assert len({job['destination_package_proposed'] for job in part_jobs}) == 609
sha_groups = collections.defaultdict(list)
for job in part_jobs:
    sha_groups[job['source_sha256']].append(job['part_key_proposed'])
failed_checks = [item for item in checks if not item['exists'] or item.get('matches') is False]
summary = {'families': len(families), 'modules': sum(item['module_count'] for item in families),
           'extensions': sum(item['extension_count'] for item in families), 'part_jobs': len(part_jobs),
           'registered_native_part_bindings': sum(item['module_bound_count'] for item in families),
           'native_part_packages_by_exact_name': sum(item['native_part_packages_by_exact_name_count'] for item in families),
           'saved_parent_whole_packages': sum(bool(item['parent_package'] and item['parent_package']['exists']) for item in families),
           'saved_parent_whole_receipts_matching_current_package': sum(any(r['record'].get('saved') and r['package'].get('matches') for r in item['parent_import_receipts']) for item in families),
           'source_material_bindings': len(material_jobs),
           'existing_material_candidates_with_package': sum(item['reusable_after_native_recipe_uv_and_instancing_readback'] for item in material_jobs),
           'materials_needing_native_creation_or_reconciliation': sum(not item['reusable_after_native_recipe_uv_and_instancing_readback'] for item in material_jobs),
           'hash_checks': len(checks), 'failed_hash_or_exists_checks': len(failed_checks),
           'duplicate_fbx_sha_groups': {key: value for key,value in sha_groups.items() if len(value)>1},
           'all_parents_held': all(str(item['explicit_hold_preserved']).lower() == 'true' for item in families),
           'all_rights_unconfirmed': all(item['rights_state_preserved'] == 'unconfirmed' for item in families),
           'canonical_identity_count': len(records), 'canonical_catalog_path': str(CAT_PATH), 'canonical_catalog_sha256': sha(CAT_PATH)}
result = {'schema': 'environmentpipeline.modular_registration_reconciliation.v1',
          'recorded_utc': datetime.now(timezone.utc).isoformat(), 'read_only': True,
          'registration': check(registration_path), 'delivery': check(SOURCE_ROOT/'DELIVERY.md'),
          'manifest': check(SOURCE_ROOT/'MANIFEST.json'), 'summary': summary, 'failed_checks': failed_checks,
          'families': families, 'capability_activation_performed': False, 'catalog_writes': False,
          'native_edits': False, 'source_edits': False, 'holds_released': False}
write('REGISTRATION_RECONCILIATION.json', result)
write('MISSING_PART_IMPORT_PLAN.json', {'schema': 'environmentpipeline.modular_missing_import_plan.v1',
      'state': 'offline_plan_native_execution_and_identity_commit_pending', 'native_execution': False,
      'canonical_catalog_sha256_at_plan': summary['canonical_catalog_sha256'],
      'part_count': len(part_jobs), 'parts': part_jobs,
      'identity_policy': 'Preserve twenty source-derived family IDs and existing parent canonical rows. Part keys and destination paths here are proposals, not committed catalog identities. Confirm with current bank owner before any additive registration. Never reuse the whole-building parent asset_id for a module import receipt.'})
write('MATERIAL_REUSE_PLAN.json', {'schema': 'environmentpipeline.modular_material_reuse_plan.v1',
      'state': 'offline_recipe_and_package_reconciliation_native_readback_pending', 'materials': material_jobs,
      'uv_policy': 'SourceRenderUV is the first UV channel in source-derived parts and copies each original render UV per object. Native readback must establish imported UV0 and material texture-coordinate compatibility. Retain source graphs and per-material slot provenance; appearance qualification remains pending.'})
write('SOURCE_HASH_CHECKS.json', {'checks': checks, 'failed': failed_checks})
print(json.dumps(summary, indent=2), flush=True)
