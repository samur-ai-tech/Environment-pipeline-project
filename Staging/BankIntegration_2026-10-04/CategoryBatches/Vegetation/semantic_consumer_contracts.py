"""Export descriptive vegetation contracts for the existing semantic source owner.

Uses saved receipts and already inspected historical images. Writes only this
category directory; never imports Unreal, edits policy, or changes eligibility.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BANK = HERE.parents[1]
PREP = ROOT/'Staging/BankPreparation_2026-10-04'
SHARED = ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
IRAN = ROOT/'Staging/Iran_4km_2026-10-04'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def yes(value):
    return str(value).lower() in {'1', 'true'}


def ref(path):
    path = Path(path)
    return {'path': str(path.resolve()), 'sha256': sha(path)}


def package(obj):
    return ROOT/'Content'/(obj.split('.')[0][6:]+'.uasset')


OBSERVATIONS = {
    'current_Palms_Pack_01__Add_Props__Thicket__Meshes__SM_Thicket_03_G': {
        'growth_form': 'sparse_single_trunk_tree', 'appearance_descriptor': 'sapling_like',
        'observation': 'Thin single main trunk, slender branches, sparse leaves, narrow open crown. Broad dense canopy is not established.',
        'kind': 'historical_native_Lit_preview', 'image': 'Thicket_03.jpg', 'native_appearance_currently_verified': False},
    'current_Palms_Pack_01__Add_Props__Grass__Meshes__SM_Grass_02_3': {
        'growth_form': 'low_grass_tuft',
        'observation': 'Ground clump with a small number of long, relatively broad green blades; open spacing between blades.',
        'kind': 'historical_native_Lit_preview', 'image': 'Grass_02_3.jpg', 'native_appearance_currently_verified': False},
    'current_Palms_Pack_01__Add_Props__Grass__Meshes__SM_Grass_05_2': {
        'growth_form': 'low_grass_tuft',
        'observation': 'Sparse upright tuft with narrow green blades and visible gaps; no dense continuous lawn is established.',
        'kind': 'historical_native_Lit_preview', 'image': 'Grass_05_2.jpg', 'native_appearance_currently_verified': False},
    'current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0636_Acacia': {
        'growth_form': 'unknown', 'appearance_descriptor': 'single_trunk_visible_canopy_obscured',
        'observation': 'One visible woody trunk; large opaque white/black cards obscure canopy form. Cannot claim a valid broad-canopy appearance.',
        'kind': 'historical_native_Lit_preview_with_material_defect', 'image': 'H0636_Acacia_recheck.jpg',
        'native_appearance_currently_verified': False},
    'external.T1090': {
        'growth_form': 'unknown', 'source_geometry_descriptor': 'single_trunk_leafy_tapered_crown_geometry',
        'observation': 'Neutral source render shows a single trunk and substantial elongated/tapered leaf-cluster geometry. It does not verify native alpha/materials or botanical species.',
        'kind': 'prepared_geometry_render_not_native_material_appearance', 'native_appearance_currently_verified': False},
    'external.T1183': {
        'growth_form': 'unknown', 'source_geometry_descriptor': 'single_trunk_wide_card_canopy_geometry',
        'observation': 'Neutral source render shows a trunk and wide angular card-based canopy envelope. Correct native masked foliage and resulting growth-form appearance are unverified.',
        'kind': 'prepared_geometry_render_not_native_material_appearance', 'native_appearance_currently_verified': False},
}


def build():
    ready = read(HERE/'READY_JOBS.json')
    catalog = read(SHARED)
    records = {r['asset_id']: r for r in catalog['rows']}
    prepared = {r['asset_id']: r for r in read(PREP/'PREPARED_BANK.json')['rows']}
    iran_rows = {r['AssetId']: r for r in read(IRAN/'AREA_CATALOG_ROWS.json')}
    inputs = [HERE/'HANDOFF.json', HERE/'READY_JOBS.json', HERE/'EXECUTION_MANIFEST.json', SHARED,
        PREP/'NATIVE_MEASUREMENTS.json', PREP/'PREPARED_BANK.json',
        ROOT/'Staging/ModularBank_2026-10-04/VEGETATION_COORDINATION_REVIEW.json',
        ROOT/'Staging/PipelineSemanticRepair_2026-10-04/SEMANTIC_POLICY.json',
        IRAN/'AREA_CATALOG_ROWS.json', IRAN/'NATIVE_AREA_CATALOG.json', IRAN/'AREA_CATALOG_DIGEST_CHECK.json',
        ROOT/'Content/Python/geocity_landscape_workflow.py']
    evidence = {str(p.resolve()): sha(p) for p in inputs}
    trees, grasses = [], []
    selected_grass = {
        'current_Palms_Pack_01__Add_Props__Grass__Meshes__SM_Grass_02_3',
        'current_Palms_Pack_01__Add_Props__Grass__Meshes__SM_Grass_05_2'}
    for job in ready['rows']:
        aid = job['asset_id']
        if job['preservation']['palm_hold']:
            continue
        is_tree = job['role_proposed'] == 'tree' or aid == 'current_ProceduralBuildingGenerator__Meshes__Foliage__SM_Aspen_Tree_01'
        is_grass = 'grass' in prepared[aid]['name'].lower()
        if not is_tree and not is_grass:
            continue
        p, record = prepared[aid], records[aid]
        rt = record['runtime']
        area = iran_rows.get(aid)
        config = job['contact_and_placement_configuration']
        observation = dict(OBSERVATIONS.get(aid, {'growth_form': 'unknown',
            'kind': 'no_individual_native_growth_form_review',
            'observation': 'Name, vendor family and measured dimensions do not establish individual growth form.',
            'native_appearance_currently_verified': False}))
        if 'image' in observation:
            image = ROOT/'Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02'/observation.pop('image')
            observation['image_evidence'] = ref(image)
        if aid in {'external.T1090', 'external.T1183'}:
            observation['image_evidence'] = ref(p['prepared_source']['preview'])
            observation['prepared_blend'] = ref(p['prepared_source']['blend'])
        object_path = rt['ObjectPath']
        native_hash = sha(package(object_path)) if object_path else None
        if object_path:
            assert native_hash == rt['AssetRevision'].lower(), ('current_catalog_package_revision_mismatch', aid)
        known_form = observation['growth_form'] != 'unknown'
        iran_eligible = bool(area and yes(area['RunEligible']) and not yes(area['ExplicitHold']) and not area['HoldReasons'])
        item = {'asset_id': aid, 'catalog_row_name': record['catalog_row_name'], 'object_path': object_path or job['target_object_path'],
            'native_object_exists_and_hash_matches_catalog': bool(object_path), 'native_package_sha256': native_hash,
            'source': job['source'], 'observation': observation,
            'botanical_species': 'unknown', 'biological_age': 'unknown', 'regional_suitability': 'unverified',
            'source_label_only': p['name'], 'source_style_preserved': record['environment_style_set'],
            'source_label_not_botanical_identification': True,
            'native_fit': {'bounds_cm': config['bounds_cm'] if config else None,
                'dimensions_cm': [b-a for a,b in zip(config['bounds_cm']['min'],config['bounds_cm']['max'])] if config else None,
                'anchor_z_cm': rt['AnchorZCm'] if object_path else None,
                'forward_axis': rt['ForwardAxis'], 'native_scale': [1, 1, 1],
                'min_spacing_cm': rt['MinSpacingCm'],
                'bounds_valid_current_row': yes(rt['BoundsValid']),
                'anchor_valid_current_row': yes(rt['AnchorValid']),
                'orientation_valid_current_row': yes(rt['OrientationValid']),
                'measurement_evidence': job['existing_evidence']['native_measurement'] or job['existing_evidence']['import_receipt'],
                'fit_status': 'existing enabled scope contract retained' if yes(rt['RunEligible']) else 'candidate bounds or held import; native functional support not approved',
                'fresh_native_fit_query_performed': False},
            'material_slot_paths': job['material_slot_paths'], 'material_package_hashes': job['material_package_hashes'],
            'shared_runtime_row': {k:rt[k] for k in ['Role','RequestRole','PlacementRule','RunEligible','ExplicitHold','HoldReasons','FamilyId','StyleSet','AllowedAreas','AllowedZones','SelectionWeight']},
            'saved_iran_area_row': area,
            'saved_iran_scope_eligible': iran_eligible,
            'iran_scope_receipts_are_saved_evidence_not_fresh_live_readback': True,
            'semantic_context': {'candidate_classes': [10] if is_tree else [10, 20, 30],
                'meaning': 'procedural generic visual representation in a classified source context; class is not species or an individual plant survey',
                'default_requires_verified_species_or_region': False,
                'botanical_fidelity_request_requires_additional_species_region_evidence': True,
                'new_candidate_policy_consumption_ready': False,
                'existing_iran_generic_tree_contract_supported': is_tree and known_form and iran_eligible,
                'existing_iran_grass_mesh_contract_supported': is_grass and known_form and iran_eligible,
                'native_semantic_grass_provider_connected_by_category': False},
            'blockers_preserved': job['blockers'], 'catalog_eligibility_rights_or_hold_changes': False}
        if is_grass:
            item['current_gaza_landscape_grass_provider_mesh'] = aid in selected_grass
            item['native_grass_anchor_distinction'] = 'HDA AnchorZCm is a catalog placement contract. Current native GrassVariety settings do not apply that field; pivot/slope support needs provider-native verification.'
            grasses.append(item)
        else:
            trees.append(item)
    result = {'schema': 'environmentpipeline.vegetation_semantic_consumer_contract.v1',
        'status': 'DESCRIPTIVE_SOURCE_CONTRACT_READY_NO_POLICY_OR_NATIVE_ACTIVATION',
        'semantic_owner_thread': '01a1067b-a64c-7cb1-b244-111b118e4940',
        'manager_thread': ready['system_manager_thread'], 'latest_category_handoff': ref(HERE/'HANDOFF.json'),
        'latest_category_jobs': ref(HERE/'READY_JOBS.json'), 'latest_category_execution_manifest': ref(HERE/'EXECUTION_MANIFEST.json'),
        'trees': trees, 'grass_meshes': grasses,
        'available_reviewed_generic_tree_form': ['sparse_single_trunk_tree'],
        'verified_native_broad_canopy_or_needleleaf_alternative_eligible_in_iran': [],
        'native_grass_consumer_contract': {
            'mesh_asset_ids': sorted(selected_grass), 'class_allowlist': [10,20,30],
            'class_exclusions': 'All other classes, invalid/unknown, crop, water and bare; road/pad priority and slope/support constraints remain.',
            'required_provider_count': 1,
            'HDA_understory_suppression_required_in_native_grass_owned_context': True,
            'HDA_understory_suppression_applied_or_verified_by_category': False,
            'tree_and_shrub_HDA_roles_not_replaced_by_grass': True,
            'coverage_and_density_are_procedural_not_measured_plant_counts': True,
            'existing_gaza_configuration_only': {'total_density_per_10m2': 12.0, 'per_mesh_density_per_10m2': 6.0,
                'coverage': 0.15, 'uniform_scale': [1,1,1], 'align_to_surface': True,
                'existing_type': '/Game/Project/Shared/SurfacePainting/Appearance_20261003/LG_GeoCity_PermittedGroundGrass'},
            'iran_semantic_provider_native_activation_and_readback': 'pending separate system/semantic owner delivery',
            'existing_generic_Ground_mask_is_not_a_verified_classified_grass_mask': True},
        'preserved_exclusions': {'palms': [j['asset_id'] for j in ready['rows'] if j['preservation']['palm_hold']],
            'Plant07': 'Not a selected native Grass mesh; sparse leaf diagnosis remains required.',
            'hosted_vegetation': 'Vines and hedge remain outside ground scattering.',
            'species_and_regions': 'Unknown or unverified unless independent actual evidence establishes them.'},
        'evidence_hashes': evidence, 'new_editor_operations': 0, 'new_native_visual_reviews': 0,
        'image_review': 'Existing exact historical native/source images visually inspected; no new render or native operation.',
        'source_tree_cover_does_not_require_mature_broad_canopy': True}
    for path, expected in evidence.items():
        assert sha(path) == expected, 'source_changed_during_semantic_contract_snapshot'
    output = HERE/'SEMANTIC_CONSUMER_HANDOFF.json'
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    (HERE/'SEMANTIC_EXECUTION_MANIFEST.json').write_text(json.dumps({
        'adapter': ref(__file__), 'output': ref(output), 'inputs': evidence,
        'writes': [str(output), str(HERE/'SEMANTIC_EXECUTION_MANIFEST.json')],
        'unreal_or_shared_source_operations': False},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'semantic_contract': str(output), 'tree_records':len(trees),'grass_records':len(grasses),
        'reviewed_current_tree':result['available_reviewed_generic_tree_form'], 'new_native_candidates_released':0,
        'source_hash':sha(output)}))
    return result


if __name__ == '__main__':
    build()
