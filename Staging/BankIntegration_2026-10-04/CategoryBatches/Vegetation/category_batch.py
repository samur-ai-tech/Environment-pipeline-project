"""Complete retained vegetation intake. Import/build never operates Unreal.

CLI writes only this directory. helper_payloads() returns existing integrator
schemas, not a second catalog. Native entry points are for the bank integrator
inside its actual-PID lease; this category chat must never call them.
"""
import argparse
import collections
import copy
import hashlib
import importlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANK = HERE.parents[1]
ROOT = BANK.parents[1]
PREP = ROOT / 'Staging/BankPreparation_2026-10-04'
CATALOG = ROOT / 'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
AREAS = ['GazaRimal', 'GazaShujaiya']
TRANSFER = ROOT/'Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/STATE.json'
LOD_HEADER = Path('C:/Program Files/Epic Games/UE_5.8/Engine/Source/Editor/StaticMeshEditor/Public/StaticMeshEditorSubsystem.h')
RULES = {'tree': 'terrain_tree', 'shrub': 'terrain_shrub', 'understory': 'terrain_understory'}
PROFILES = [CATALOG.parent / 'AREA_PROFILE.json',
            ROOT / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    target = Path(path).resolve()
    assert target.is_relative_to(HERE), 'category_writes_only_its_owned_directory'
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def yes(value):
    return str(value).lower() in {'true', '1'}


def package_file(obj):
    assert obj.startswith('/Game/')
    return ROOT / 'Content' / (obj.split('.')[0][6:] + '.uasset')


def source_ref(path, expected=None):
    p = Path(path)
    actual = sha(p) if p.is_file() else None
    assert not expected or actual == expected.lower(), ('source_identity_changed', str(p), expected, actual)
    return {'path': str(p), 'sha256': actual, 'exists': p.is_file()}


def proposed_role(p):
    if p['palm_hold_not_released']:
        return p['request_role'] or 'tree'
    if p['request_role'] in RULES:
        return p['request_role']
    # Exact existing archive identities; these are proposed contracts, not approvals.
    aid = p['asset_id']
    if aid in {'external.T1090', 'external.T1183'} or aid.startswith('external.ST_') or aid == 'external.MOUT_FAMILY_DesertTree':
        return 'tree'
    if aid in {'external.T1172', 'external.T1173', 'external.T1174', 'external.T1175'}:
        return 'understory'
    return 'shrub'


def spacing(role, bounds):
    diagonal = math.hypot(*[b-a for a, b in zip(bounds['min'][:2], bounds['max'][:2])])
    return max({'tree': 800, 'shrub': 350, 'understory': 180}[role], math.ceil(diagonal + 100))


def row_delta(rt, config, allow_eligibility=False):
    """Exact fields consumed by the existing row struct; no invented schema fields."""
    update = {'Role': config['role'], 'RequestRole': config['role'],
              'PlacementRule': config['placement_rule'], 'FamilyId': config['family_id'],
              'StyleSet': config['style_context'], 'ForwardAxis': config['forward_axis'],
              'AnchorZCm': str(config['anchor_z_cm']), 'MinSpacingCm': str(config['min_spacing_cm']),
              'PlacementScope': 'area_zone', 'AllowedAreas': '|'.join(AREAS),
              'AllowedZones': config['allowed_zones'], 'AllowedPlacementIds': ''}
    if config.get('bounds_cm'):
        for axis, lo, hi in zip('XYZ', config['bounds_cm']['min'], config['bounds_cm']['max']):
            update['BoundsMin'+axis+'Cm'] = str(lo)
            update['BoundsMax'+axis+'Cm'] = str(hi)
    if allow_eligibility:
        update.update(RunEligible='true', BoundsValid='true', AnchorValid='true', OrientationValid='true')
    else:
        update.update(RunEligible=rt['RunEligible'], BoundsValid=rt['BoundsValid'],
                      AnchorValid=rt['AnchorValid'], OrientationValid=rt['OrientationValid'],
                      SelectionWeight=rt['SelectionWeight'])
    return {k: {'before': rt[k], 'after': v} for k, v in update.items() if rt[k] != v}


def build():
    transfer = read(TRANSFER)
    assert transfer['status'] == 'TRANSFERRED_TO_SUCCESSOR'
    manager = transfer['successor_manager_thread_id']
    source_sha = sha(CATALOG)
    catalog = read(CATALOG)
    records = {r['asset_id']: r for r in catalog['rows']}
    prepared = [r for r in read(PREP / 'PREPARED_BANK.json')['rows'] if r['category'] == 'Vegetation']
    assert len(prepared) == 80 and len({r['asset_id'] for r in prepared}) == 80
    configurations = {r['asset_id']: r for r in read(BANK / 'NATIVE_CONFIGURATIONS.json')['rows']}
    validation = read(BANK / 'NATIVE_VALIDATION.json')
    native_contact = read(BANK / 'NATIVE_CONTACT_READBACK.json')
    materials = read(BANK / 'NATIVE_INSTANCE_MATERIALS.json')['mesh_slots']
    import_queue = {r['asset_id']: r for r in read(BANK / 'EXTERNAL_IMPORT_QUEUE.json')}
    manifest = {r['asset_id']: r for r in read(PREP / 'EXTERNAL_IMPORT_MANIFEST.json')}
    recipes = {r['asset_id']: r for r in read(BANK / 'EXTERNAL_MATERIAL_RECIPES.json')}
    coverage = {r['asset_id']: r for r in read(BANK / 'FULL_BANK_COVERAGE.json')['rows']}
    derivatives = read(HERE / 'DERIVATIVE_RESULT.json')
    rows, native_rows, extra_imports, held_contracts = [], [], [], []
    for p in prepared:
        aid = p['asset_id']
        record = records[aid]
        rt = record['runtime']
        original = source_ref(p['source_path'])
        held = yes(rt['ExplicitHold']) or bool(record['hold_reasons']) or bool(p['named_holds_preserved']) or p['palm_hold_not_released']
        hosted = aid == 'external.T1144' or aid.startswith('current_Stylized_Egypt__Meshes__plants__SM_vine_')
        m = p.get('native_measurement')
        imp_path = BANK / ('IMPORTED_'+aid.replace('.', '_')+'.json')
        imp = read(imp_path) if imp_path.exists() else None
        external = p.get('prepared_source')
        role = proposed_role(p)
        if imp and imp.get('saved'):
            assert sha(package_file(imp['native_path'])) == imp['native_sha256']
            bounds = imp['measurement']['bounds_cm']
            slots = imp['native_material_slots']
        elif m:
            bounds = m['vertex_bounds_cm']
            assert original['sha256'] == p['current_package_sha256'].lower()
            slots = materials.get(rt['ObjectPath']) or catalog.get('instance_materials', {}).get(rt['ObjectPath']) or p['instancing_material_slots_recorded'] or [s['path'] for s in m['material_slots']]
        elif external:
            bounds = {k: [100*v for v in external['bounds_m'][k]] for k in ['min', 'max']}
            slots = []
        else:
            bounds, slots = None, []
        config = copy.deepcopy(configurations.get(aid))
        if config is None and bounds and not p['palm_hold_not_released']:
            config = {'asset_id': aid, 'row_name': p['catalog_row_name'], 'object_path': rt['ObjectPath'],
                      'package_sha256': original['sha256'] if m else (imp['native_sha256'] if imp else None),
                      'role': role, 'placement_rule': RULES[role], 'contact_kind': 'root_or_stem_base',
                      'anchor_z_cm': float(rt['AnchorZCm']) if yes(rt['RunEligible']) else bounds['min'][2],
                      'anchor_basis': 'Retain existing activated anchor' if yes(rt['RunEligible']) else 'Measured candidate only; root/stem support must be explicitly reviewed.',
                      'bounds_cm': bounds, 'forward_axis': rt['ForwardAxis'] or '+X',
                      'forward_basis': 'Rotationally unconstrained ground vegetation; preserve native axes.',
                      'native_scale': [1, 1, 1], 'allowed_areas': AREAS, 'allowed_zones': 'open_ground',
                      'style_context': rt['StyleSet'], 'source_style_preserved': record['environment_style_set'],
                      'family_id': rt['FamilyId'], 'min_spacing_cm': float(rt['MinSpacingCm']) if yes(rt['RunEligible']) else spacing(role, bounds),
                      'material_slots': m['material_slots'] if m else imp['measurement']['material_slots'] if imp else external['material_slots_by_object'],
                      'existing_instance_materials': slots, 'rights_state_preserved': record['recorded_rights_state'],
                      'state': 'existing_active' if yes(rt['RunEligible']) else 'held_configuration_only',
                      'activation_requires': 'Exact current source/material hashes and actual contact/facing/material validation; all existing holds remain binding.'}
        blockers = []
        if held:
            blockers.append({'kind': 'preserved_hold', 'explicit_hold': rt['ExplicitHold'],
                             'reasons': record['hold_reasons'], 'named_holds': p['named_holds_preserved'],
                             'palm_hold_not_released': p['palm_hold_not_released'],
                             'release_by_this_batch': False})
        if hosted:
            blockers.append({'kind': 'host_or_linear_consumer_required',
                             'required_contract': ['source_boundary_or_host_identity', 'local_support_frame_and_normal',
                                'terrain_or_mount_height', 'measured_forward_axis', 'segment_end_corner_policy',
                                'building_road_clearance', 'owned_replacement_identity'],
                             'ground_scatter_allowed': False})
        if p['style_source_recorded'] != 'mediterranean_urban':
            blockers.append({'kind': 'current_profile_style_mismatch', 'source_style': p['style_source_recorded'],
                             'profile_style': 'mediterranean_urban', 'style_rewrite_allowed': False})
        missing = (m or {}).get('dependencies', {}).get('unresolved_registry_packages', [])
        if missing:
            blockers.append({'kind': 'missing_native_dependencies', 'paths': missing,
                             'repair': 'Retained material derivative needs the exact missing original vendor texture; no alternate species/material substitution.'})
        sparse = 'SM_Plant_07_' in aid
        if sparse:
            blockers.append({'kind': 'sparse_leaf_visibility_unresolved',
                             'basis': 'Latest category assignment reports almost invisible leaves in actual native preview.',
                             'batch_action': 'collect_material_diagnostics then apply_reviewed_foliage_repairs with exact parameter/texture evidence',
                             'material_ready': False, 'automatic_validation_patch': None})
        if 'SM_H0636_Acacia' in aid:
            blockers.append({'kind': 'opaque_foliage_cards', 'batch_action': 'Evidence-bound opacity graph correction on a retained material derivative; hold remains.'})
        live_v = validation.get(aid, {})
        if m and not held and not yes(rt['RunEligible']):
            assert aid in configurations, ('unexpected_nonheld_asset_missing_integrator_config', aid)
            native_rows.append(config)
            blockers.append({'kind': 'native_contact_and_material_validation_pending',
                             'existing_validation': live_v,
                             'required_patch': {'source_sha256': config['package_sha256'], 'anchor_z_cm': 'EXPLICIT_REVIEWED_SUPPORT_VALUE',
                                 'forward_axis': config['forward_axis'], 'contact_reviewed': 'ACTUAL_REVIEW',
                                 'facing_reviewed': 'ACTUAL_REVIEW', 'material_reviewed': 'ACTUAL_REVIEW', 'ready': 'ALL_PRECONDITIONS_TRUE'},
                             'reuse_native_measurements': True, 'repeat_inventory_required': False})
        if p['palm_hold_not_released']:
            action = 'preserve_palm_hold'
        elif hosted:
            action = 'hosted_contract_separate'
        elif yes(rt['RunEligible']):
            action = 'reuse_existing_active_contract'
        elif m and not held:
            action = 'complete_native_configuration_and_validation'
        elif m:
            action = 'repair_or_classify_held_native_without_release'
        elif imp:
            action = 'reuse_saved_import_connect_held_contract_without_reimport'
        elif external:
            action = 'import_prepared_held_source'
        elif aid.startswith('external.ST_'):
            action = 'import_native_speedtree_held_source'
            blockers.append({'kind': 'native_speedtree_import_readback_pending',
                'required_evidence': ['Installed factory successful import', 'Exact final named-saved mesh/material package hashes',
                    'Full native bounds and root support', 'Native LOD/UV/dependency readback', 'Actual foliage material review'],
                'blender_or_fbx_conversion_required': False, 'existing_hold_release': False})
        else:
            action = 'native_family_intake_requires_source_registry_closure'
            blockers.append({'kind': 'native_family_dependency_contract_missing',
                             'source_package': p['source_path'],
                             'required_evidence': 'Exact source registry dependency closure, target conflict hashes and individual representative measurement; a family label is not one measured mesh.'})
        if external:
            original_blend = source_ref(external['blend'])
            source_receipt = source_ref(external['receipt'])
        else:
            original_blend = source_receipt = None
        import_job = copy.deepcopy(import_queue.get(aid))
        if aid in derivatives:
            derivative = derivatives[aid]
            import_job = copy.deepcopy(manifest[aid])
            import_job.update(prepared_blend=derivative['prepared_blend'], original_explicit_hold=rt['ExplicitHold'],
                hold_reasons_preserved=record['hold_reasons'], native_activation=False,
                activation_policy='Preserve every existing hold; import is not selection approval.',
                source_bounds_m=external['bounds_m'], source_dimensions_m=external['dimensions_m'],
                original_source_receipt=external['receipt'], category='Vegetation',
                required_consumer_context='linear_boundary_alignment' if hosted else 'vegetation_ground_fit',
                primary_render_object_count=1, material_mapping_by_source_object=[{
                    'name': 'VegetationJoinedLOD0' if aid == 'external.T0976' else 'HedgeSmall_Untitled',
                    'geometry_role': 'render_lod0', 'material_slots': derivative['material_slots'], 'uv_layers': []}])
            extra_imports.append(import_job)
        if config and (held or hosted):
            config['automatic_ground_activation_allowed'] = False
            held_contracts.append({'asset_id': aid, 'configuration': config,
                                   'runtime_deltas_without_release': row_delta(rt, config), 'blockers': blockers})
        material_refs = []
        for slot in slots:
            path = slot['path'] if isinstance(slot, dict) else slot
            if path:
                material_refs.append({'object_path': path, **source_ref(package_file(path))})
        texture_hashes = [{**{k: ref.get(k) for k in ['material', 'channel', 'uv_scale', 'uv_offset']},
                           **source_ref(ref['path'])} for ref in (external or {}).get('texture_references', [])]
        target = rt['ObjectPath'] or (import_job['destination_package_proposed'] + '.' + import_job['destination_package_proposed'].rsplit('/', 1)[1] if import_job else None)
        if aid.startswith('external.ST_'):
            name = 'SM_'+aid.removeprefix('external.ST_')
            target = '/Game/Project/Shared/ModelBank/Prepared/External/'+aid.replace('.', '_')+'/'+name+'.'+name
        if aid.startswith('external.MOUT_FAMILY_'):
            package = p['source_path'].replace('\\', '/').split('/Content/', 1)[1].removesuffix('.uasset')
            target = '/Game/'+package+'.'+package.rsplit('/', 1)[1]
        rows.append({'asset_id': aid, 'row_name': p['catalog_row_name'], 'category': 'Vegetation',
            'action': action, 'existing_object_path': rt['ObjectPath'], 'target_object_path': target,
            'source': original, 'prepared_source': original_blend, 'source_receipt': source_receipt,
            'native_package_sha256': (imp['native_sha256'] if imp else original['sha256'] if m else None),
            'role_proposed': role, 'contact_and_placement_configuration': config,
            'material_slot_paths': slots, 'material_package_hashes': material_refs,
            'source_texture_hashes': texture_hashes,
            'import_job': import_job, 'source_override': derivatives.get(aid),
            'existing_material_recipe': {'path': str(BANK / 'EXTERNAL_MATERIAL_RECIPES.json'), 'asset_id': aid} if aid in recipes else None,
            'existing_evidence': {'native_measurement': {'path': str(PREP / 'NATIVE_MEASUREMENTS.json'), 'asset_id': aid} if m else None,
                'native_contact': native_contact.get(aid), 'validation': live_v,
                'coverage_receipt': {'path': str(BANK / 'FULL_BANK_COVERAGE.json'), 'record': coverage[aid]},
                'historical_native_images': p['native_preview_sources'],
                'import_receipt': str(imp_path) if imp else None},
            'runtime_deltas_after_explicit_validation': row_delta(rt, config, allow_eligibility=not held and not hosted and not yes(rt['RunEligible']) and rt['StyleSet'] == 'mediterranean_urban') if config else {},
            'selection_weight_resolution': 'Existing apply_bank_configuration.build computes exact 1/N over actual eligible members; do not insert a formula string into the CSV.',
            'preservation': {'ExplicitHold': rt['ExplicitHold'], 'HoldReasons': rt['HoldReasons'],
                'source_style': record['environment_style_set'], 'rights': record['recorded_rights_state'],
                'canonical_qualified': record['canonical_qualified'], 'palm_hold': p['palm_hold_not_released']},
            'automatic_gaza_use_currently_ready': yes(rt['RunEligible']) and not held and not hosted and rt['StyleSet'] == 'mediterranean_urban',
            'new_native_validation_ready_by_this_category': False, 'blockers': blockers,
            'ordinary_output_by_this_category': False, 'saved_area_reopen_by_this_category': False})
    assert sha(CATALOG) == source_sha, 'catalog_changed_during_snapshot_rebuild_category_bundle'
    family_members = collections.defaultdict(list)
    for row in rows:
        c = row['contact_and_placement_configuration']
        if c and not row['preservation']['palm_hold'] and row['action'] != 'hosted_contract_separate':
            family_members[(c['role'], c['style_context'], c['family_id'])].append(row['asset_id'])
    budgets = [{'role': k[0], 'style': k[1], 'family_id': k[2], 'areas': AREAS,
        'zones': 'open_ground', 'total_budget': 1.0, 'candidate_ids': ids,
        'formula': '1 / actual eligible family members in the same role/style/areas/zones',
        'held_members_add_zero_probability': True} for k, ids in sorted(family_members.items())]
    payload = {'schema': 'environmentpipeline.vegetation_category_jobs.v1',
        'bank_integrator_thread': '01a1067c-5012-7550-b449-015b53c9d726',
        'system_manager_thread': manager,
        'management_transfer': {'path': str(TRANSFER), 'sha256': sha(TRANSFER)},
        'native_authoring_currently_authorized': transfer['native_authoring_authorized'],
        'status': 'EXECUTABLE_CATEGORY_BATCH_READY_NATIVE_INTEGRATOR_REQUIRED',
        'canonical_source_sha256_at_build': source_sha, 'identity_count': len(rows),
        'scope': 'All 80 existing vegetation identities. Hosted vegetation, palms, style and rights holds remain separate.',
        'family_budgets': budgets, 'rows': rows,
        'counts': dict(collections.Counter(r['action'] for r in rows)),
        'helper_schema_payloads': {'native_configurations': str(HERE/'NATIVE_CONFIGURATIONS.payload.json'),
            'extra_import_queue': str(HERE/'EXTERNAL_IMPORT_QUEUE.payload.json'),
            'material_recipes': str(HERE/'ADDITIONAL_MATERIAL_RECIPES.json'),
            'slot_usage': str(HERE/'ADDITIONAL_SLOT_USAGE.json'),
            'source_overrides': str(HERE/'IMPORT_SOURCE_OVERRIDES.payload.json'),
            'held_runtime_contracts': str(HERE/'HELD_CONTRACTS.payload.json')},
        'generation_entrypoint': 'Tools > GeoCity: Generate / Regenerate Current Area',
        'automatic_route': 'Current canonical DataTable selection -> retained Houdini roles -> official Houdini Engine unreal_instance -> native baked instances.',
        'profile_patch_policy': 'System manager merges catalog digest/decision/material fields after sole integrator named table save; never hardcode a category-only catalog.',
        'landscape_grass_policy': 'Retain current profile GrassType two meshes/density. Additional understory uses existing terrain_understory requests; no second Grass spawn path or implicit GrassType expansion.'}
    write(HERE/'READY_JOBS.json', payload)
    write(HERE/'NATIVE_CONFIGURATIONS.payload.json', {'rows': native_rows})
    write(HERE/'EXTERNAL_IMPORT_QUEUE.payload.json', extra_imports)
    write(HERE/'HELD_CONTRACTS.payload.json', {'rows': held_contracts})
    overrides = {a: {'fbx': d['exports'][0]['fbx'], 'sha256': d['exports'][0]['sha256'],
        'prepared_blend': d['prepared_blend'], 'prepared_blend_sha256': d['prepared_blend_sha256'],
        'source_files_changed': False, 'geometry_remodeled': False, 'native_equivalence_pending': True}
        for a, d in derivatives.items()}
    write(HERE/'IMPORT_SOURCE_OVERRIDES.payload.json', overrides)
    inputs = [CATALOG, PREP/'PREPARED_BANK.json', PREP/'NATIVE_MEASUREMENTS.json',
        PREP/'EXTERNAL_IMPORT_MANIFEST.json', PREP/'FAMILY_WEIGHT_BUDGETS.json', PREP/'EXACT_GEOMETRY_FAMILIES.json',
        BANK/'NATIVE_CONFIGURATIONS.json', BANK/'NATIVE_VALIDATION.json', BANK/'NATIVE_INSTANCE_MATERIALS.json',
        BANK/'SOURCE_CONTACT_READBACK.json', BANK/'FULL_BANK_COVERAGE.json', *PROFILES]
    write(HERE/'INPUT_SNAPSHOT.json', {str(p): sha(p) for p in inputs})
    write(HERE/'HANDOFF.json', {'status': payload['status'], 'identity_count': 80, 'counts': payload['counts'],
        'system_manager_thread': manager,
        'native_operator_thread': transfer['native_operator_thread_id'],
        'native_authoring_currently_authorized': transfer['native_authoring_authorized'],
        'current_native_blocker': transfer['native_blocker'],
        'existing_automatic_gaza_assets': sum(r['automatic_gaza_use_currently_ready'] for r in rows),
        'native_configuration_rows': len(native_rows), 'new_import_jobs': len(extra_imports),
        'completed_source_work': ['Exact two-part DesertBush LOD0 derivative plus original LOD1/LOD2 exports',
            'Additional native material recipes and source slot usage', 'Complete native/held/source category row and family contracts'],
        'native_operations_by_category': 0, 'native_activations_by_category': 0,
        'generation_or_reopen_by_category': False,
        'integrator_sequence': ['Call helper_payloads and merge by canonical asset_id after checking exact sources; only integrator writes shared queues.',
            'Import external.T0976 using existing import_prepared.import_one with supplied derivative override; append_original_lods afterwards.',
            'Keep external.T1144 out of ground jobs; supplied recipe supports later held host/linear intake only.',
            'Reuse 13 saved external imports and all existing native measurements/material derivatives.',
            'Complete 22 native configuration contact/facing/material validations in batches; Plant07 requires recorded leaf-visibility diagnosis or evidence-bound correction.',
            'Five of the 22 native configurations retain stylized_egypt; do not validate them into Gaza selection or rewrite style. Six SpeedTree native jobs remain held and return compatible binding receipts to the integrator.',
            'Apply existing apply_bank_configuration transaction, named DataTable save/readback; preserve every hold/style/right.',
            'Manager merges exact profile digest/decision/material fields and coordinates ordinary Shujaiya/Rimal generation, named saves, fresh reopen and replacement.'],
        'files': payload['helper_schema_payloads'], 'ready_jobs': str(HERE/'READY_JOBS.json'),
        'remaining_exceptional_work': ['Preserved palms/rights/style/native explicit holds',
            'Missing original Hazel bark textures', 'Held Acacia opaque foliage cards',
            'Five vines and hedge need supported host/linear context',
            'Three MOUT native families need exact source registry closure, not a fabricated per-mesh contract'],
        'permanent_connection_claim': 'Category preparation complete; full saved automatic integration awaits actual integrator and manager receipts.'})
    execution_files = [HERE/'category_batch.py', HERE/'prepare_derivatives.py',
        BANK/'bank_contracts.py', BANK/'native_bank_ops.py', BANK/'import_prepared.py',
        BANK/'apply_bank_configuration.py']
    data_files = [HERE/name for name in ['READY_JOBS.json', 'NATIVE_CONFIGURATIONS.payload.json',
        'EXTERNAL_IMPORT_QUEUE.payload.json', 'HELD_CONTRACTS.payload.json', 'IMPORT_SOURCE_OVERRIDES.payload.json',
        'ADDITIONAL_MATERIAL_RECIPES.json', 'ADDITIONAL_SLOT_USAGE.json', 'DERIVATIVE_RESULT.json', 'HANDOFF.json', 'USAGE.txt']]
    write(HERE/'EXECUTION_MANIFEST.json', {'schema': 'environmentpipeline.category_execution_source_binding.v1',
        'manager_thread': manager, 'status': 'SOURCE_BOUND_NATIVE_NOT_RUN',
        'files': {str(p.resolve()): sha(p) for p in execution_files},
        'payloads': {str(p.resolve()): sha(p) for p in data_files},
        'installed_api_evidence': {str(LOD_HEADER): {'sha256': sha(LOD_HEADER),
            'declaration': 'StaticMeshEditorSubsystem.h:120 ImportLOD(BaseStaticMesh, LODIndex, SourceFilename)',
            'native_invocation_by_category': False}},
        'native_authoring_requires': 'Fresh actual-PID bank lease activation=MANAGER_ACTIVATED; INSPECTION_ONLY is rejected.'})
    print(json.dumps({'ready_jobs': len(rows), 'native_configuration_rows': len(native_rows),
                      'new_import_jobs': len(extra_imports), 'counts': payload['counts']}))
    return payload


def helper_payloads():
    """Return directly consumable existing helper schemas; caller owns all merges."""
    jobs = read(HERE/'READY_JOBS.json')
    for row in jobs['rows']:
        source_ref(row['source']['path'], row['source']['sha256'])
        for material in row['material_package_hashes']:
            source_ref(material['path'], material['sha256'])
        for texture in row['source_texture_hashes']:
            source_ref(texture['path'], texture['sha256'])
    for recipe in read(HERE/'ADDITIONAL_MATERIAL_RECIPES.json'):
        source_ref(recipe['prepared_blend'], recipe['prepared_blend_sha256'])
        for mat in recipe['materials']:
            for texture in mat['linked_images']:
                source_ref(texture['path'], texture['sha256'])
    for override in read(HERE/'IMPORT_SOURCE_OVERRIDES.payload.json').values():
        source_ref(override['fbx'], override['sha256'])
        source_ref(override['prepared_blend'], override['prepared_blend_sha256'])
    return {'native_configurations': read(HERE/'NATIVE_CONFIGURATIONS.payload.json')['rows'],
            'import_queue': read(HERE/'EXTERNAL_IMPORT_QUEUE.payload.json'),
            'material_recipes': read(HERE/'ADDITIONAL_MATERIAL_RECIPES.json'),
            'source_slot_usage': read(HERE/'ADDITIONAL_SLOT_USAGE.json'),
            'source_overrides': read(HERE/'IMPORT_SOURCE_OVERRIDES.payload.json'),
            'held_contracts': read(HERE/'HELD_CONTRACTS.payload.json')['rows'],
            'completed_native_import_receipts': [read(p) for p in sorted(HERE.glob('IMPORTED_external_ST_*.json'))]}


def integrator_modules(authoring=False):
    """Only native caller entry points import Unreal or bank native helpers."""
    manifest = read(HERE/'EXECUTION_MANIFEST.json')
    for path, expected in manifest['files'].items():
        source_ref(path, expected)
    for path, expected in manifest['payloads'].items():
        source_ref(path, expected)
    if str(BANK) not in sys.path:
        sys.path.insert(0, str(BANK))
    N = importlib.import_module('native_bank_ops')
    assert Path(N.__file__).resolve() == (BANK/'native_bank_ops.py').resolve()
    source_ref(N.__file__, manifest['files'][str((BANK/'native_bank_ops.py').resolve())])
    C = importlib.import_module('bank_contracts')
    assert Path(C.__file__).resolve() == (BANK/'bank_contracts.py').resolve()
    source_ref(C.__file__, manifest['files'][str((BANK/'bank_contracts.py').resolve())])
    U = importlib.import_module('unreal')
    N.preflight()
    A = importlib.import_module('geocity_editor_action')
    lines = (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines()
    fields = A.lease_fields([s for s in lines if s.strip()][-1])
    assert fields['manager_thread_id'] == read(TRANSFER)['successor_manager_thread_id']
    if authoring:
        assert fields.get('activation') == 'MANAGER_ACTIVATED', 'category_native_authoring_rejects_inspection_only_lease'
        assert fields.get('native_authorized_now', 'true') != 'false', 'native_authoring_is_not_currently_authorized'
        assert not any(p.startswith('/Game/Palms_Pack_01/') for p in N.dirty()['content']), 'dirty_vendor_vegetation_requires_manager_recovery_before_authoring'
    return N, U


def collect_material_diagnostics(ids=None):
    """Read exact leaf/material/texture/parameter state; no scene placement or edits."""
    N, U = integrator_modules()
    before = N.dirty()
    jobs = read(HERE/'READY_JOBS.json')['rows']
    result = {}
    M = U.MaterialEditingLibrary
    for job in jobs:
        if ids and job['asset_id'] not in ids:
            continue
        config = job['contact_and_placement_configuration']
        if not config or not job['existing_object_path']:
            continue
        source_ref(package_file(job['existing_object_path']), job['native_package_sha256'])
        paths = job['material_slot_paths'] or [s['path'] for s in config['material_slots']]
        slots = []
        for path in paths:
            mat = U.load_asset(path)
            assert mat
            chain = []
            while isinstance(mat, U.MaterialInstanceConstant):
                params = {}
                for kind in ['scalar', 'texture']:
                    names = getattr(M, 'get_'+kind+'_parameter_names')(mat)
                    getter = getattr(M, 'get_material_instance_'+kind+'_parameter_value')
                    params[kind] = {str(name): getter(mat, name).get_path_name() if kind == 'texture' and getter(mat, name)
                                    else getter(mat, name) if kind == 'scalar' else None for name in names}
                chain.append({'path': mat.get_path_name(), 'sha256': sha(package_file(mat.get_path_name())), 'parameters': params})
                mat = mat.get_editor_property('parent')
                assert mat
            assert isinstance(mat, U.Material)
            used = [t.get_path_name() for t in M.get_used_textures(mat)]
            graph = {}
            for name in ['MP_BASE_COLOR', 'MP_OPACITY_MASK', 'MP_WORLD_POSITION_OFFSET']:
                node = M.get_material_property_input_node(mat, getattr(U.MaterialProperty, name))
                graph[name] = {'node': node.get_name(), 'class': node.get_class().get_name()} if node else None
            chain.append({'path': mat.get_path_name(), 'sha256': sha(package_file(mat.get_path_name())),
                'blend_mode': str(mat.get_editor_property('blend_mode')), 'two_sided': mat.get_editor_property('two_sided'),
                'opacity_mask_clip_value': mat.get_editor_property('opacity_mask_clip_value'),
                'instancing_usage': M.has_material_usage(mat, U.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES),
                'used_textures': [{'object_path': t, 'sha256': sha(package_file(t)) if t.startswith('/Game/') else None} for t in used],
                'material_inputs': graph})
            slots.append({'selected_slot_path': path, 'chain': chain})
        result[job['asset_id']] = {'source_sha256': job['native_package_sha256'], 'slots': slots,
            'contact_receipt_reused': job['existing_evidence']['native_contact'],
            'leaf_visibility': 'Requires actual existing/native Lit evidence; graph readback is not appearance approval.',
            'ready': False, 'originals_changed': False}
    assert N.dirty() == before
    write(HERE/'NATIVE_MATERIAL_DIAGNOSTICS.json', result)
    return result


def apply_reviewed_foliage_repairs(edits_path):
    """Apply exact evidence-bound edits on NEW derivatives; never guess alpha settings.

Input rows: asset_id, source_slot_path, source_sha256, evidence_receipt,
scalar_parameters, texture_parameters [{name,path,sha256}], base_properties
(two_sided, opacity_mask_clip_value, blend_mode='BLEND_MASKED'), and optional
opacity_mask_link {path,sha256,uv_channel,channel,sampler_type}. Every setting
must be backed by the sealed diagnosis. Missing evidence rejects the job.
Returns material-slot deltas for the integrator; never edits catalog or validation.
"""
    N, U = integrator_modules(authoring=True)
    jobs = {j['asset_id']: j for j in read(HERE/'READY_JOBS.json')['rows']}
    M, E = U.MaterialEditingLibrary, U.EditorAssetLibrary
    before = N.dirty()
    receipt_path = HERE/'NATIVE_FOLIAGE_REPAIR_RECEIPTS.json'
    result = read(receipt_path) if receipt_path.exists() else []
    for edit in read(edits_path)['rows']:
        job = jobs[edit['asset_id']]
        assert not job['preservation']['palm_hold']
        evidence = Path(edit['evidence_receipt'])
        assert evidence.is_file() and edit.get('evidence_sha256') == sha(evidence), 'repair_requires_sealed_actual_diagnosis'
        source_ref(package_file(edit['source_slot_path']), edit['source_sha256'])
        known = job['material_slot_paths'] or [s['path'] for s in job['contact_and_placement_configuration']['material_slots']]
        assert edit['source_slot_path'] in known
        assert set(edit.get('base_properties', {})).issubset({'two_sided', 'opacity_mask_clip_value', 'blend_mode'})
        if 'blend_mode' in edit.get('base_properties', {}):
            assert edit['base_properties']['blend_mode'] == 'BLEND_MASKED'
        opacity = edit.get('opacity_mask_link')
        if opacity:
            source_ref(package_file(opacity['path']), opacity['sha256'])
            assert opacity['channel'] in {'A', 'R', 'G', 'B'}
            assert isinstance(opacity['uv_channel'], int) and 0 <= opacity['uv_channel'] <= 7
            assert opacity['sampler_type'] in {'SAMPLERTYPE_COLOR', 'SAMPLERTYPE_MASKS', 'SAMPLERTYPE_LINEAR_COLOR'}
        key = hashlib.sha256(json.dumps(edit, sort_keys=True).encode()).hexdigest()[:16]
        reused = next((r for r in result if r.get('edit_key') == key and r['asset_id'] == edit['asset_id']), None)
        if reused:
            for path, expected in reused['saved_paths'].items():
                source_ref(package_file(path), expected)
            continue
        saved = {}
        def duplicate_chain(source, depth=0):
            name = 'MI_' if isinstance(source, U.MaterialInstanceConstant) else 'M_'
            dest = N.MAT_ROOT+'/VegetationFix/'+name+key+'_'+str(depth)
            assert not E.does_asset_exist(dest), 'existing_repair_requires_receipt_reuse_not_overwrite'
            obj = E.duplicate_asset(source.get_path_name(), dest)
            assert obj
            saved[dest] = obj
            if isinstance(obj, U.MaterialInstanceConstant):
                obj.set_editor_property('parent', duplicate_chain(source.get_editor_property('parent'), depth+1))
            else:
                for prop, value in edit.get('base_properties', {}).items():
                    obj.set_editor_property(prop, getattr(U.BlendMode, value) if prop == 'blend_mode' else value)
                if opacity:
                    uv = M.create_material_expression(obj, U.MaterialExpressionTextureCoordinate)
                    uv.set_editor_property('coordinate_index', opacity['uv_channel'])
                    node = M.create_material_expression(obj, U.MaterialExpressionTextureSample)
                    node.set_editor_property('texture', U.load_asset(opacity['path']))
                    node.set_editor_property('sampler_type', getattr(U.MaterialSamplerType, opacity['sampler_type']))
                    assert M.connect_material_expressions(uv, '', node, 'UVs')
                    assert M.connect_material_property(node, opacity['channel'], U.MaterialProperty.MP_OPACITY_MASK)
                    assert M.get_material_property_input_node(obj, U.MaterialProperty.MP_OPACITY_MASK) == node
                if edit.get('base_properties', {}).get('blend_mode') == 'BLEND_MASKED':
                    assert M.get_material_property_input_node(obj, U.MaterialProperty.MP_OPACITY_MASK), 'masked_repair_requires_explicit_opacity_source'
                obj.set_editor_property('used_with_instanced_static_meshes', True)
                obj.set_editor_property('automatically_set_usage_in_editor', False)
                M.recompile_material(obj)
            return obj
        repaired = duplicate_chain(U.load_asset(edit['source_slot_path']))
        if edit.get('scalar_parameters') or edit.get('texture_parameters'):
            assert isinstance(repaired, U.MaterialInstanceConstant)
            for name, value in edit.get('scalar_parameters', {}).items():
                assert name in {str(n) for n in M.get_scalar_parameter_names(repaired)}
                M.set_material_instance_scalar_parameter_value(repaired, name, float(value))
                assert abs(M.get_material_instance_scalar_parameter_value(repaired, name)-float(value)) < 0.00001
            for value in edit.get('texture_parameters', []):
                source_ref(package_file(value['path']), value['sha256'])
                assert value['name'] in {str(n) for n in M.get_texture_parameter_names(repaired)}
                texture = U.load_asset(value['path'])
                M.set_material_instance_texture_parameter_value(repaired, value['name'], texture)
                assert M.get_material_instance_texture_parameter_value(repaired, value['name']) == texture
            M.update_material_instance(repaired)
        for path in sorted(saved):
            assert E.save_asset(path, only_if_is_dirty=True)
        result.append({'asset_id': edit['asset_id'], 'old_slot_path': edit['source_slot_path'],
            'edit_key': key,
            'new_slot_path': repaired.get_path_name(), 'saved_paths': {p: sha(package_file(p)) for p in saved},
            'sealed_diagnosis': str(evidence), 'ready': False, 'explicit_holds_preserved': True,
            'material_review_still_required': True})
        source_ref(package_file(edit['source_slot_path']), edit['source_sha256'])
        write(receipt_path, result)
    assert N.dirty() == before
    write(receipt_path, result)
    return result


def append_original_lods(asset_id='external.T0976'):
    """Import source LOD1/2 directly into the retained mesh; no temporary assets.

Installed UE 5.8 StaticMeshEditorSubsystem.h:120 exposes ImportLOD for an
existing destination and an explicit FBX filename. Native execution is pending.
"""
    assert asset_id == 'external.T0976'
    N, U = integrator_modules(authoring=True)
    C = importlib.import_module('bank_contracts')
    dest = next(j for j in read(HERE/'EXTERNAL_IMPORT_QUEUE.payload.json') if j['asset_id'] == asset_id)['destination_package_proposed']
    receipt_path = BANK/('IMPORTED_'+asset_id.replace('.', '_')+'.json')
    receipt = C.read(receipt_path)
    assert receipt['saved'] and C.sha(C.package_file(receipt['native_path'])) == receipt['native_sha256']
    assert receipt['native_path'].split('.')[0] == dest
    derivative = read(HERE/'DERIVATIVE_RESULT.json')[asset_id]
    assert receipt['import_fbx_sha256'] == derivative['exports'][0]['sha256'], 'retained_LOD0_is_not_the_category_derivative'
    mesh = U.load_asset(receipt['native_path'])
    S, E = U.get_editor_subsystem(U.StaticMeshEditorSubsystem), U.EditorAssetLibrary
    if receipt.get('category_lod_completion'):
        assert S.get_lod_count(mesh) == 3
        return receipt['category_lod_completion']
    before = N.dirty()
    assert S.get_lod_count(mesh) == 1, 'unexpected_existing_lods'
    prior_slots = [s.material_interface.get_path_name() if s.material_interface else None for s in mesh.static_materials]
    for lod in derivative['exports'][1:]:
        source_ref(lod['fbx'], lod['sha256'])
        assert S.import_lod(mesh, lod['lod'], lod['fbx']) == lod['lod']
        assert mesh.get_static_mesh_description(lod['lod']).get_triangle_count() == lod['triangles']
        assert [s.material_interface.get_path_name() if s.material_interface else None for s in mesh.static_materials] == prior_slots, 'direct_lod_import_changed_material_slots'
    assert S.get_lod_count(mesh) == 3
    assert E.save_asset(receipt['native_path'], only_if_is_dirty=True)
    receipt['native_sha256'] = C.sha(C.package_file(receipt['native_path']))
    receipt['measurement'] = N.measure(mesh)
    receipt['category_lod_completion'] = {'source_exports': derivative['exports'], 'saved_lod_count': 3,
        'source_geometry_preserved': True, 'held': True, 'native_api': 'StaticMeshEditorSubsystem.import_lod',
        'temporary_native_assets_created_or_deleted': False,
        'source_derivative_receipt': str(HERE/'DERIVATIVE_RESULT.json')}
    C.write(receipt_path, receipt)
    assert N.dirty() == before
    write(HERE/'NATIVE_LOD_COMPLETION.json', receipt['category_lod_completion'])
    return receipt['category_lod_completion']


def import_speedtree(asset_id):
    """Use installed native .st importer; all originals/holds retained, no activation."""
    N, U = integrator_modules(authoring=True)
    job = next(j for j in read(HERE/'READY_JOBS.json')['rows'] if j['asset_id'] == asset_id)
    assert asset_id.startswith('external.ST_') and job['preservation']['ExplicitHold'] == 'true'
    source_ref(job['source']['path'], job['source']['sha256'])
    E = U.EditorAssetLibrary
    name = asset_id.removeprefix('external.ST_')
    folder = '/Game/Project/Shared/ModelBank/Prepared/External/'+asset_id.replace('.', '_')
    path = folder+'/SM_'+name
    report_path = HERE/('IMPORTED_'+asset_id.replace('.', '_')+'.json')
    if report_path.exists():
        report = read(report_path)
        assert report['source_sha256'] == job['source']['sha256']
        for p, expected in report['saved_paths'].items():
            source_ref(package_file(p), expected)
        return report
    assert not E.does_asset_exist(path), 'native_intake_destination_conflict'
    before = N.dirty()
    task = U.AssetImportTask()
    for key, value in {'filename': job['source']['path'], 'destination_path': folder,
        'destination_name': 'SM_'+name, 'automated': True, 'replace_existing': False, 'save': False}.items():
        task.set_editor_property(key, value)
    factory = getattr(U, 'SpeedTreeImportFactory', None)
    assert factory, 'installed_native_SpeedTree_factory_not_exposed_no_format_or_license_bypass'
    task.set_editor_property('factory', factory())
    U.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    objects = list(task.get_objects())
    meshes = [o for o in objects if isinstance(o, U.StaticMesh)]
    assert len(meshes) == 1 and meshes[0].get_path_name().split('.')[0] == path
    mesh = meshes[0]
    closure = N.dependency_closure(path)
    assert not closure['missing']
    created = {}
    for index, slot in enumerate(mesh.static_materials):
        assert slot.material_interface
        mesh.set_material(index, N.compatible_copy(slot.material_interface, created, {}))
    for p in sorted(created):
        assert E.save_asset(p, only_if_is_dirty=True)
    # Only newly imported packages under this exact asset folder are saved.
    packages = set(N.dependency_closure(path)['packages'])
    packages.update(o.get_path_name().split('.')[0] for o in objects)
    owned = {p for p in packages if p.startswith(folder+'/')}
    assert path in owned
    for p in sorted(owned):
        assert E.save_asset(p, only_if_is_dirty=True)
    assert N.dirty() == before
    report = {'asset_id': asset_id, 'source_sha256': job['source']['sha256'],
        'native_path': mesh.get_path_name(), 'native_sha256': sha(package_file(mesh.get_path_name())),
        'measurement': N.measure(mesh),
        'native_material_slots': [s.material_interface.get_path_name() for s in mesh.static_materials],
        'saved_paths': {p: sha(package_file(p)) for p in owned | set(created)},
        'saved': True, 'catalog_connected': False, 'ready': False, 'eligible': False,
        'enabled': False, 'hold_preserved': job['preservation']['ExplicitHold'],
        'hold_reasons_preserved': next(b['reasons'] for b in job['blockers'] if b['kind'] == 'preserved_hold'),
        'rights_and_style_preserved': job['preservation'], 'material_visual_review_pending': True,
        'source_files_unchanged': True, 'ordinary_output': False}
    source_ref(job['source']['path'], job['source']['sha256'])
    write(report_path, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--validate', action='store_true', help='Validate retained helper payloads without native operations.')
    args = parser.parse_args()
    if args.validate:
        payloads = helper_payloads()
        print(json.dumps({'payloads_valid': True, 'native_configs': len(payloads['native_configurations']),
                          'imports': len(payloads['import_queue']), 'native_operations': 0}))
    else:
        build()
