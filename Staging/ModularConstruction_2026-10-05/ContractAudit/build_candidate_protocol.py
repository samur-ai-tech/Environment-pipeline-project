"""Build disabled protocol files in this directory only; no editor/HDA/catalog IO."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE = PROJECT / 'Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05/SOURCE_BINDINGS.json'
BASE = Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def write(name, value):
    path = HERE / name
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return ref(path)


def main():
    source = json.loads(SOURCE.read_text(encoding='utf-8'))
    source_ref = ref(SOURCE)
    entries, templates = [], []
    count = 0
    for family in source['families']:
        family_digest = digest(family)
        extension_path = Path(family['assembly_path']).parent / 'ExtensionBand/EXTENSION.json'
        entry = {'family_id': family['family_id'], 'parent_asset_id': family['parent_asset_id'],
            'parent_catalog_row': family['parent_catalog_row'], 'enabled': False, 'weight': 1.0,
            'source_bindings_ref': source_ref, 'source_family_sha256': family_digest,
            'native_manifest_ref': None, 'route_authorization_ref': None, 'source_qualification_ref': None,
            'execution_mode': 'ordinary_selection', 'qualification_variations': [], 'qualification_target_source_ids': {},
            'allowed_rigid_yaw_offsets_degrees': [0, 90, 180, 270], 'allowed_building_uses': [],
            'source_facing_verified': False, 'minimum_pad_coverage_ratio': 0.45,
            'height_policy': 'preserve_native_for_unmeasured_source', 'height_tolerance_m': 0.04,
            'capabilities': {'exact_reconstruction': {'enabled': False, 'allowed_repeat_counts': [1], 'evidence': {}}},
            'geometric_tiers_are_architectural_floors': False, 'canonical_parent_hold_preserved': family['explicit_hold'],
            'canonical_parent_hold_reasons_preserved': family['hold_reasons'], 'rights_state_preserved': family['rights_state']}
        if extension_path.is_file():
            entry['extension_rule_ref'] = ref(extension_path)
            entry['capabilities']['one_axis_extension'] = {'enabled': False, 'allowed_repeat_counts': [], 'evidence': {},
                'source_geometric_example_repeat_count': 2,
                'limitation': 'Eight new-repeat UV0 seams fail; original bands cannot be qualified for N>=2 from geometry alone.'}
        entries.append(entry)
        parts = {}
        for assembly_set in family['sets']:
            for source_part in assembly_set['parts']:
                name = source_part['name']; count += 1
                parts[name] = {'asset_id': family['family_id']+'/'+name,
                    'path': source_part['native_package']+'.'+name, 'source_sha256': source_part['fbx_sha256'],
                    'min_cm': None, 'max_cm': None, 'material_slots': None,
                    'source_material_slots': source_part['source_material_slots'],
                    'native_source_slot_indices': None,
                    'dependency_closed': False, 'pivot_preserved': False, 'source_uv0_probe_alignment_passed': False,
                    'uv_channel_count_verified': False,
                    'actual_named_or_dependency_hold': True}
        templates.append({'schema': 'environmentpipeline.modular_native_family_readback.v1',
            'family_id': family['family_id'], 'source_family_sha256': family_digest,
            'source_to_native_matrix': None, 'basis_evidence_ref': None, 'material_graph_evidence_ref': None,
            'actual_named_or_dependency_hold': True, 'parent_canonical_hold_preserved': True, 'parts': parts})
    assert len(entries) == 20 and count == 609
    registry = {'schema': 'environmentpipeline.retained_source_family_registry.v1', 'enabled': False,
        'selection_seed': 1337, 'families': entries, 'native_qualification_completed': False,
        'production_hda_or_profiles_changed': False}
    registry_ref = write('DISABLED_SOURCE_FAMILY_REGISTRY.json', registry)
    templates_ref = write('NATIVE_READBACK_TEMPLATE.json', {'schema': 'environmentpipeline.modular_native_template.v1',
        'template_only': True, 'never_treat_template_as_readback': True, 'families': templates})
    gate = {'passed': False, 'family_id': '<exact source family_id>', 'gate': '<one required gate>',
        'source_family_sha256': '<canonical JSON digest of SOURCE_BINDINGS family>',
        'native_manifest_sha256': '<actual saved native manifest byte SHA256>', 'repeat_counts': [],
        'actual_native_editor_or_houdini_evidence': [], 'limitations': []}
    write('CAPABILITY_RECEIPT_TEMPLATE.json', gate)
    write('QUALIFICATION_AUTHORIZATION_TEMPLATE.json', {
        'schema': 'environmentpipeline.modular_route_authorization.v1', 'approved': False,
        'execution_mode': 'qualification', 'family_id': '<one exact family>', 'parent_asset_id': '<unchanged parent>',
        'manager_thread_id': '<current manager>', 'source_family_sha256': '<actual binding family digest>',
        'native_manifest_sha256': '<actual native manifest byte digest>',
        'use_scope': 'retained_complete_family_dependency', 'preserve_canonical_holds': True,
        'actual_named_or_dependency_hold': True, 'allowed_area_ids': [], 'placement_scope': 'exact_ids',
        'allowed_source_osm_ids': {}, 'capabilities': [], 'allowed_repeat_counts': [],
        'allowed_validation_gates': ['houdini_repeat', 'official_engine_output', 'named_save', 'fresh_reopen', 'regeneration',
            'native_material_visual_fidelity', 'native_reflection_normals_material_culling'],
        'ordinary_selection_authorized': False, 'template_only': True})
    write('DATUM_PROTOCOL.json', {'schema': 'environmentpipeline.source_family_datum_protocol.v1',
        'source_units': 'metres', 'native_asset_units': 'centimetres', 'houdini_point_units': 'metres',
        'source_to_native_matrix': 'Measured signed horizontal axis permutation, source+Z to native+Z; never guessed from FBX export labels.',
        'numeric_units': 'Native readback min_cm/max_cm divide by100 once. Source assembly translations are already metres, apply measured basis with no additional100 conversion.',
        'native_to_houdini': '[nativeX_m,nativeZ_m,nativeY_m]',
        'family_origin': 'Native assembled bbox horizontal center and minimumZ mapped rigidly to pad horizontal center and corrected base.',
        'part_origin': 'Preserved FBX local source pivot; one common measured family basis. No perpart recentering.',
        'rotation': 'Native yaw about+Z maps to Houdini quaternion [0,-sin(yaw/2),0,cos(yaw/2)]. All part origins and envelope corners rotate together.',
        'scale': '[1,1,1] always; no source floor count, story scaling, bay substitution or generated corner/roof solids.',
        'reflection': 'Ordinary selection requires measured native vertex/bounds basis and actual normals/materialculling verification for reflections. Exact-ID manager-authorized qualification may produce first retained-route output with reflection appearance explicitly pending; never record an unmeasured reflection gate as passed.',
        'architectural_roles': 'Source region labels are preserved; tiers and native floor=0 support-probe bookkeeping do not certify architectural floors.',
        'support': 'Every source part horizontal envelope contributes retained final-heightfield terrain probes; retained cook rejects>4cm contact error.',
        'height': 'Preserve native height for seeded_rule_not_measured with difference reported; measured source heights must match4cm. No fabricated class/floor/use facts.',
        'pad_coverage': 'Complete-family native bbox area/pad area must be>=0.45 as retained whole-building fit; containment required first.',
        'yaw_selection': 'Deterministic longest geographic pad edge angle plus approved rigid rotation offsets; source facing unverified until actual evidence.',
        'basis_evidence_required_fields': ['family_id', 'source_family_sha256', 'passed', 'source_to_native_matrix',
            'source_units', 'native_units', 'pivot_translation_preserved', 'sample_vertices_checked',
            'verified_part_names', 'maximum_probe_error_cm', 'reflection_normals_material_culling_verified']})
    write('BEFORE_HASHES.json', {'schema': 'environmentpipeline.modular_candidate_before_hashes.v1',
        'retained_module': ref(BASE/'geocity_city_module.py'), 'retained_hda': ref(BASE/'GeoCity_city_v015_PermanentBank.hdalc'),
        'source_bindings': source_ref, 'candidate_append': ref(HERE/'RETAINED_SOURCE_FAMILY_APPEND.py'),
        'disabled_registry': registry_ref, 'native_template': templates_ref,
        'active_type': 'trackb::geocity_city::15.0', 'production_changes': False})
    print(json.dumps({'family_count': len(entries), 'part_count': count, 'registry_enabled': False,
        'candidate_path': str(HERE/'RETAINED_SOURCE_FAMILY_APPEND.py')}))


if __name__ == '__main__':
    main()
