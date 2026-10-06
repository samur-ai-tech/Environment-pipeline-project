"""Candidate append for the retained GeoCity PythonModule; no native side effects.

The source family lane preserves complete source assemblies and their materials.
It is separate from Courtyard bays/palettes, but uses the retained assembly record,
native point translator, final-terrain check, replacement and persistence ledger.
Importing this file alone installs no hook; appending it after the retained module
installs only an assembly_layout wrapper. Production embedding belongs to owner.
"""
import hashlib
import json
import math
import re
from pathlib import Path

SOURCE_FAMILY_PROTOCOL = 'environmentpipeline.retained_source_family_registry.v1'
SOURCE_NATIVE_PROTOCOL = 'environmentpipeline.modular_native_family_readback.v1'
SOURCE_ROUTE_PROTOCOL = 'environmentpipeline.modular_route_authorization.v1'
SOURCE_CAPABILITY_GATES = ('source_reconstruction', 'native_import', 'houdini_repeat',
    'official_engine_output', 'material_appearance', 'named_save', 'fresh_reopen', 'regeneration')
SOURCE_BAND_GATES = ('connection_geometry', 'texture_phase', 'openings_corners_roof')
SOURCE_QUALIFICATION_VALIDATION_GATES = ('houdini_repeat', 'official_engine_output',
    'named_save', 'fresh_reopen', 'regeneration', 'native_material_visual_fidelity',
    'native_reflection_normals_material_culling')
_SOURCE_PART_PATH = re.compile(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+')
_SOURCE_FAMILY_USE_CONTEXT = {}
_SOURCE_FAMILY_EVIDENCE_CACHE = None


class SourceFamilyQualificationError(ValueError):
    """An explicitly assigned qualification cannot silently fall back."""


def _sf_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode('utf-8')).hexdigest()


def _sf_load_ref(ref):
    if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
        raise ValueError('source_family_evidence_ref_missing')
    digest = ref.get('sha256', '')
    if not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('source_family_evidence_digest_invalid')
    key = (ref['path'], digest)
    if _SOURCE_FAMILY_EVIDENCE_CACHE is not None and key in _SOURCE_FAMILY_EVIDENCE_CACHE:
        return _SOURCE_FAMILY_EVIDENCE_CACHE[key]
    data = Path(ref['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('source_family_evidence_changed:' + ref['path'])
    value = json.loads(data.decode('utf-8-sig'))
    if _SOURCE_FAMILY_EVIDENCE_CACHE is not None:
        _SOURCE_FAMILY_EVIDENCE_CACHE[key] = value
    return value


def _sf_vec(value, size=3):
    if not isinstance(value, (tuple, list)) or len(value) != size:
        raise ValueError('source_family_vector_shape_invalid')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value):
        raise ValueError('source_family_nonfinite_or_non_numeric_transform')
    return [float(v) for v in value]


def _sf_mul(matrix, point):
    return [sum(matrix[i][j] * point[j] for j in range(3)) for i in range(3)]


def _sf_basis(value):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError('source_family_native_basis_missing')
    matrix = [_sf_vec(row) for row in value]
    # Only a measured signed axis permutation is supported by this candidate.
    # No unit multiplication, shear or geometric adaptation is hidden here.
    for row in matrix:
        if sum(abs(v) == 1.0 for v in row) != 1 or any(v not in (-1.0, 0.0, 1.0) for v in row):
            raise ValueError('source_family_native_basis_not_signed_permutation')
    if any(sum(abs(matrix[i][j]) for i in range(3)) != 1 for j in range(3)):
        raise ValueError('source_family_native_basis_nonorthogonal')
    if matrix[2] != [0.0, 0.0, 1.0]:
        raise ValueError('source_family_source_up_not_native_positive_Z')
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    return matrix, determinant


def _sf_transformed_bounds(low, high, matrix):
    low, high = _sf_vec(low), _sf_vec(high)
    # Original architecture can contain single-surface roofs/walls. Do not add
    # thickness or reject a legitimate planar source part to make an AABB solid.
    if any(high[i] < low[i] for i in range(3)) or sum(high[i] > low[i] for i in range(3)) < 2:
        raise ValueError('source_family_bounds_degenerate')
    corners = [_sf_mul(matrix, [x, y, z]) for x in (low[0], high[0])
        for y in (low[1], high[1]) for z in (low[2], high[2])]
    return ([min(p[i] for p in corners) for i in range(3)],
            [max(p[i] for p in corners) for i in range(3)])


def _sf_cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _sf_on(p, a, b):
    return abs(_sf_cross(a, b, p)) <= 1e-7 * max(1.0, math.dist(a, b)) and all(
        min(a[i], b[i])-1e-7 <= p[i] <= max(a[i], b[i])+1e-7 for i in range(2))


def _sf_inside(p, ring):
    if any(_sf_on(p, a, ring[(i+1) % len(ring)]) for i, a in enumerate(ring)):
        return True
    inside = False
    for i, a in enumerate(ring):
        b = ring[(i+1) % len(ring)]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1]-a[1])*(b[0]-a[0])/(b[1]-a[1]):
            inside = not inside
    return inside


def _sf_proper_cross(a, b, c, d):
    ac, ad, ca, cb = _sf_cross(a, b, c), _sf_cross(a, b, d), _sf_cross(c, d, a), _sf_cross(c, d, b)
    return ac * ad < -1e-14 and ca * cb < -1e-14


def _sf_contained(polygon, ring):
    probes = list(polygon) + [[(a[0]+polygon[(i+1) % len(polygon)][0])/2,
        (a[1]+polygon[(i+1) % len(polygon)][1])/2] for i, a in enumerate(polygon)]
    return all(_sf_inside(p, ring) for p in probes) and not any(
        _sf_proper_cross(a, polygon[(i+1) % len(polygon)], b, ring[(j+1) % len(ring)])
        for i, a in enumerate(polygon) for j, b in enumerate(ring))


def _sf_feature(feature):
    if feature.get('closed') is not True or feature.get('holes'):
        raise ValueError('source_family_requires_single_closed_hole_free_pad')
    ring = [_sf_vec(p, 2) for p in feature.get('ring_xz_m', [])]
    if len(ring) > 3 and math.dist(ring[0], ring[-1]) < 1e-7:
        ring.pop()
    if not 3 <= len(ring) <= 128 or any(math.dist(a, ring[(i+1) % len(ring)]) < 1e-7 for i, a in enumerate(ring)):
        raise ValueError('source_family_pad_vertices_invalid')
    area = sum(a[0]*ring[(i+1) % len(ring)][1]-a[1]*ring[(i+1) % len(ring)][0] for i, a in enumerate(ring))/2
    if abs(area) < 1.0:
        raise ValueError('source_family_pad_area_invalid')
    for i, a in enumerate(ring):
        for j in range(i+1, len(ring)):
            if j in ((i+1) % len(ring), i) or i == (j+1) % len(ring):
                continue
            b, c, d = ring[(i+1) % len(ring)], ring[j], ring[(j+1) % len(ring)]
            if _sf_proper_cross(a, b, c, d) or any((_sf_on(a, c, d), _sf_on(b, c, d), _sf_on(c, a, b), _sf_on(d, a, b))):
                raise ValueError('source_family_self_intersecting_pad')
    base, height = _sf_vec([feature.get('base_m'), feature.get('height_m')], 2)
    if height <= 0:
        raise ValueError('source_family_requested_height_invalid')
    area_id, osm_id = str(feature.get('area_id', '')), str(feature.get('osm_id', ''))
    if not area_id or not osm_id:
        raise ValueError('source_family_source_identity_missing')
    return ring, base, height, area_id, osm_id


def _sf_pad_edge_yaw(feature):
    ring = _sf_feature(feature)[0]
    edges = [(math.dist(a, ring[(i+1) % len(ring)]), tuple(a), tuple(ring[(i+1) % len(ring)]))
        for i, a in enumerate(ring)]
    _, a, b = sorted(edges, key=lambda item: (-item[0], item[1], item[2]))[0]
    return math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))


def _sf_capability(entry, mode, count, family_digest, native_digest):
    capability = entry.get('capabilities', {}).get(mode, {})
    if capability.get('enabled') is not True:
        raise ValueError('source_family_capability_disabled:' + mode)
    counts = capability.get('allowed_repeat_counts', [1] if mode == 'exact_reconstruction' else [])
    if count not in counts:
        raise ValueError('source_family_repeat_count_not_individually_qualified')
    gates = SOURCE_CAPABILITY_GATES + (SOURCE_BAND_GATES if mode == 'one_axis_extension' else ())
    for gate in gates:
        evidence = capability.get('evidence', {}).get(gate, {})
        if (evidence.get('passed') is not True or evidence.get('source_family_sha256') != family_digest
                or evidence.get('native_manifest_sha256') != native_digest or count not in evidence.get('repeat_counts', [])):
            raise ValueError('source_family_capability_evidence_missing_or_stale:' + gate)
        receipt = _sf_load_ref(evidence.get('receipt_ref'))
        if (receipt.get('contract_test_only') or receipt.get('passed') is not True or receipt.get('family_id') != entry['family_id']
                or receipt.get('gate') != gate or receipt.get('source_family_sha256') != family_digest
                or receipt.get('native_manifest_sha256') != native_digest or count not in receipt.get('repeat_counts', [])):
            raise ValueError('source_family_capability_receipt_mismatch:' + gate)
    return capability


def _sf_authorization(entry, family, native, mode, count, area_id, osm_id, qualification=False, connection=False):
    author = _sf_load_ref(entry.get('route_authorization_ref'))
    if (author.get('contract_test_only') or author.get('schema') != SOURCE_ROUTE_PROTOCOL or author.get('approved') is not True
            or author.get('family_id') != family['family_id'] or author.get('parent_asset_id') != family['parent_asset_id']
            or not author.get('manager_thread_id') or author.get('preserve_canonical_holds') is not True
            or author.get('actual_named_or_dependency_hold') is not False
            or author.get('use_scope') != 'retained_complete_family_dependency'
            or area_id not in author.get('allowed_area_ids', []) or mode not in author.get('capabilities', [])
            or count not in author.get('allowed_repeat_counts', [1])
            or author.get('source_family_sha256') != _sf_digest(family)
            or author.get('native_manifest_sha256') != (entry.get('native_manifest_ref') or {}).get('sha256')):
        raise ValueError('source_family_route_or_inherited_hold_authorization_missing')
    ids = author.get('allowed_source_osm_ids', {})
    if author.get('placement_scope') == 'exact_ids':
        if osm_id not in ids.get(area_id, []):
            raise ValueError('source_family_source_id_outside_authorization')
    elif author.get('placement_scope') != 'approved_areas':
        raise ValueError('source_family_placement_scope_unrecognized')
    if native.get('actual_named_or_dependency_hold') is not False or native.get('parent_canonical_hold_preserved') is not True:
        raise ValueError('source_family_native_dependency_hold_or_preservation_invalid')
    expected_execution = 'connection' if connection else ('qualification' if qualification else 'ordinary_selection')
    if author.get('execution_mode') != expected_execution:
        raise ValueError('source_family_execution_mode_not_authorized')
    if author.get('ordinary_selection_authorized') is not (not qualification):
        raise ValueError('source_family_ordinary_selection_authorization_flag_invalid')
    if connection:
        if (qualification or mode != 'exact_reconstruction' or count != 1
                or author.get('connection_without_additional_tests_authorized') is not True
                or author.get('unperformed_validation_remains_pending') is not True):
            raise ValueError('source_family_direct_connection_scope_invalid')
    if qualification:
        if author.get('placement_scope') != 'exact_ids':
            raise ValueError('source_family_qualification_requires_exact_source_ids')
        if not set(SOURCE_QUALIFICATION_VALIDATION_GATES) <= set(author.get('allowed_validation_gates', [])):
            raise ValueError('source_family_qualification_lifecycle_scope_incomplete')
    if qualification or connection:
        source_receipt = _sf_load_ref(entry.get('source_qualification_ref'))
        if (source_receipt.get('contract_test_only') or source_receipt.get('passed') is not True
                or source_receipt.get('family_id') != family['family_id']
                or source_receipt.get('source_family_sha256') != _sf_digest(family)
                or count not in source_receipt.get('repeat_counts_by_capability', {}).get(mode, [])):
            raise ValueError('source_family_qualification_source_capability_not_proven')
        graph_receipt = _sf_load_ref(native.get('material_graph_evidence_ref'))
        if (graph_receipt.get('contract_test_only') or graph_receipt.get('passed') is not True
                or graph_receipt.get('family_id') != family['family_id']
                or graph_receipt.get('source_family_sha256') != _sf_digest(family)
                or graph_receipt.get('native_parts_sha256') != _sf_digest(native.get('parts', {}))
                or any(graph_receipt.get(key) is not True for key in ('source_recipes_bound',
                    'texture_dependencies_complete', 'mesh_slot_order_preserved'))):
            raise ValueError('source_family_qualification_native_material_graph_unverified')
    return author


def _sf_native_parts(family, native, mode, audit_only=False, pending_reflection_authorized=False):
    if native.get('schema') != SOURCE_NATIVE_PROTOCOL or native.get('family_id') != family['family_id']:
        raise ValueError('source_family_native_manifest_identity_invalid')
    if native.get('source_family_sha256') != _sf_digest(family):
        raise ValueError('source_family_native_manifest_source_binding_stale')
    matrix, determinant = _sf_basis(native.get('source_to_native_matrix'))
    basis_receipt = _sf_load_ref(native.get('basis_evidence_ref'))
    if not audit_only and (native.get('contract_test_only') or basis_receipt.get('contract_test_only')):
        raise ValueError('source_family_synthetic_native_fixture_not_runtime_evidence')
    if (basis_receipt.get('family_id') != family['family_id'] or basis_receipt.get('passed') is not True
            or basis_receipt.get('source_family_sha256') != _sf_digest(family)
            or basis_receipt.get('source_to_native_matrix') != matrix
            or basis_receipt.get('native_units') != 'centimetres'
            or basis_receipt.get('source_units') != 'metres'
            or basis_receipt.get('pivot_translation_preserved') is not True
            or basis_receipt.get('sample_vertices_checked', 0) < 3):
        raise ValueError('source_family_native_basis_probe_evidence_invalid')
    if (determinant < 0 and basis_receipt.get('reflection_normals_material_culling_verified') is not True
            and not pending_reflection_authorized):
        raise ValueError('source_family_reflection_appearance_unverified')
    probe_error = _sf_vec([basis_receipt.get('maximum_probe_error_cm')], 1)[0]
    if probe_error < 0 or probe_error > 0.15:
        raise ValueError('source_family_native_probe_error_exceeds_1p5mm')
    kind = 'reconstruction' if mode == 'exact_reconstruction' else 'extension'
    matches = [s for s in family.get('sets', []) if s.get('kind') == kind]
    if len(matches) != 1 or not matches[0].get('parts'):
        raise ValueError('source_family_complete_source_set_missing:' + kind)
    sources = matches[0]['parts']
    names = [p['name'] for p in sources]
    if len(names) != len(set(names)):
        raise ValueError('source_family_duplicate_source_part_identity')
    if not set(names) <= set(basis_receipt.get('verified_part_names', [])):
        raise ValueError('source_family_native_basis_not_verified_for_every_part')
    if mode == 'exact_reconstruction':
        assembly = _sf_load_ref({'path': family.get('assembly_path'), 'sha256': family.get('assembly_sha256')})
        authored = {part['name']: part for part in assembly.get('modules', [])}
        if assembly.get('id') != family['id'] or set(names) != set(authored):
            raise ValueError('source_family_partial_reconstruction_or_source_identity_mismatch')
        for source in sources:
            original = authored[source['name']]
            if (source['fbx_sha256'] != original['sha256']
                    or source['assembly_translation_m'] != original['original_assembly_translation_m']
                    or source['local_bounds_m'] != original['local_bounds_m']):
                raise ValueError('source_family_source_bounds_pivot_or_fbx_changed')
    native_parts = native.get('parts', {})
    selected = []
    for source in sources:
        name = source['name']; part = native_parts.get(name, {})
        expected_path = source['native_package'] + '.' + name
        if (part.get('path') != expected_path or not _SOURCE_PART_PATH.fullmatch(expected_path)
                or part.get('asset_id') != family['family_id'] + '/' + name
                or part.get('source_sha256') != source['fbx_sha256']
                or part.get('actual_named_or_dependency_hold') is not False
                or part.get('dependency_closed') is not True or part.get('pivot_preserved') is not True
                or part.get('source_uv0_probe_alignment_passed') is not True
                or part.get('uv_channel_count_verified') is not True
                or part.get('source_material_slots') != source['source_material_slots']):
            raise ValueError('source_family_native_part_binding_incomplete:' + name)
        slots = part.get('material_slots', [])
        indices = part.get('native_source_slot_indices', [])
        if (not isinstance(slots, list) or not isinstance(indices, list) or not slots
                or len(slots) != len(indices) or len(indices) != len(set(indices))
                or any(isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < len(source['source_material_slots']) for i in indices)
                or any(not isinstance(p, str) or not _SOURCE_PART_PATH.fullmatch(p) for p in slots)):
            raise ValueError('source_family_native_material_slots_incomplete:' + name)
        used_source = {int(index) for index, count in part.get('source_slot_triangle_counts', source.get('slot_triangle_counts', {})).items() if count > 0}
        if not used_source <= set(indices):
            raise ValueError('source_family_used_source_material_slot_missing:' + name)
        low = [v/100 for v in _sf_vec(part.get('min_cm'))]
        high = [v/100 for v in _sf_vec(part.get('max_cm'))]
        expected_low, expected_high = _sf_transformed_bounds(source['local_bounds_m']['min'], source['local_bounds_m']['max'], matrix)
        if max(abs(a-b) for a, b in zip(low+high, expected_low+expected_high)) > 0.0015:
            raise ValueError('source_family_native_scale_axes_or_bounds_mismatch:' + name)
        translation = _sf_mul(matrix, _sf_vec(source['assembly_translation_m']))
        selected.append((source, part, low, high, translation))
    return matrix, selected


def source_family_plan(feature, family, native, entry, mode='exact_reconstruction', repeat_count=1,
                       yaw_degrees=0.0, audit_only=False, contains=None, qualification=False, connection=False):
    """Pure complete-family plan; audit_only never authorizes runtime selection.

    Native meshes already contain the measured source-to-native basis. Apply that
    basis once to assembly translations, convert native cm bounds once to metres,
    then map native XYZ metres to Houdini XZY. Point orient rotates the complete
    family rigidly around up; it never applies a second FBX conversion or scale.
    """
    if mode not in ('exact_reconstruction', 'one_axis_extension'):
        raise ValueError('source_family_unsupported_capability')
    if isinstance(repeat_count, bool) or not isinstance(repeat_count, int) or repeat_count < 1:
        raise ValueError('source_family_repeat_count_invalid')
    if mode == 'exact_reconstruction' and repeat_count != 1:
        raise ValueError('source_family_exact_reconstruction_cannot_repeat')
    if feature.get('requested_floor_count') is not None or feature.get('requested_scale') is not None:
        raise ValueError('source_family_floors_or_geometric_scaling_not_supported')
    ring, base, requested_height, area_id, osm_id = _sf_feature(feature)
    yaw = _sf_vec([yaw_degrees], 1)[0]
    family_digest = _sf_digest(family)
    native_digest = (entry.get('native_manifest_ref') or {}).get('sha256', '')
    authorization = None
    if not audit_only:
        if not qualification and not connection:
            _sf_capability(entry, mode, repeat_count, family_digest, native_digest)
        authorization = _sf_authorization(entry, family, native, mode, repeat_count, area_id, osm_id,
            qualification=qualification, connection=connection)
    pending_reflection_authorized = bool(authorization and (
        (qualification and 'native_reflection_normals_material_culling' in authorization.get('allowed_validation_gates', []))
        or (connection and authorization.get('unperformed_validation_remains_pending') is True)))
    matrix, selected = _sf_native_parts(family, native, mode, audit_only=audit_only,
        pending_reflection_authorized=pending_reflection_authorized)
    pending_gates = []
    if (qualification or connection) and not audit_only:
        pending_gates = ['houdini_repeat', 'official_engine_output', 'named_save', 'fresh_reopen',
            'regeneration', 'native_material_visual_fidelity']
        if (_sf_basis(matrix)[1] < 0 and _sf_load_ref(native['basis_evidence_ref']).get(
                'reflection_normals_material_culling_verified') is not True):
            pending_gates.append('native_reflection_normals_material_culling')
    uses = entry.get('allowed_building_uses', [])
    actual_use = feature.get('building_use', 'unknown') or 'unknown'
    if (uses and actual_use not in uses) or (actual_use != 'unknown' and not uses):
        raise ValueError('source_family_building_use_unqualified')
    expanded = []
    if mode == 'one_axis_extension':
        band = _sf_load_ref(entry.get('extension_rule_ref'))
        axis, pitch = band.get('corridor', {}).get('axis'), band.get('corridor', {}).get('pitch_m')
        if axis not in (0, 1) or isinstance(axis, bool) or band.get('id') != family['id']:
            raise ValueError('source_family_extension_axis_or_identity_invalid')
        pitch = _sf_vec([pitch], 1)[0]
        if pitch <= 0 or band.get('corridor', {}).get('pass') is not True or band['corridor'].get('profile_hausdorff_m', float('inf')) > 0.0015:
            raise ValueError('source_family_extension_connection_unqualified')
        roles = {source.get('source_role_label'): item for item in selected for source in [item[0]]}
        if set(roles) != {'Start', 'Repeat', 'End'} or len(selected) != 3:
            raise ValueError('source_family_extension_requires_complete_start_repeat_end')
        authored = {part['name']: part for part in band.get('source_derived_parts', [])}
        if {item[0]['name'] for item in selected} != set(authored):
            raise ValueError('source_family_extension_source_set_mismatch')
        for source, _, _, _, _ in selected:
            original = authored[source['name']]
            if (source['fbx_sha256'] != original['sha256']
                    or source['assembly_translation_m'] != original['assembly_translation_m']
                    or source['local_bounds_m'] != original['local_bounds_m']):
                raise ValueError('source_family_extension_source_binding_changed')
        step = _sf_mul(matrix, [pitch if i == axis else 0.0 for i in range(3)])
        for role in ('Start', 'Repeat', 'End'):
            indexes = range(repeat_count) if role == 'Repeat' else [0 if role == 'Start' else repeat_count-1]
            for index in indexes:
                source, part, low, high, translation = roles[role]
                expanded.append((source, part, low, high, [translation[i]+index*step[i] for i in range(3)], role, index))
    else:
        expanded = [(*item, 'Exact', 0) for item in selected]
    low = [min(item[2][i]+item[4][i] for item in expanded) for i in range(3)]
    high = [max(item[3][i]+item[4][i] for item in expanded) for i in range(3)]
    height = high[2]-low[2]
    if any(high[i] <= low[i] for i in range(3)):
        raise ValueError('source_family_complete_envelope_not_volumetric')
    policy = entry.get('height_policy', 'match_source_height')
    if policy == 'match_source_height' or feature.get('height_rule') != 'seeded_rule_not_measured':
        if abs(height-requested_height) > float(entry.get('height_tolerance_m', 0.04)):
            raise ValueError('source_family_native_height_does_not_match_measured_source')
    elif policy != 'preserve_native_for_unmeasured_source':
        raise ValueError('source_family_height_policy_unrecognized')
    anchor = [(low[0]+high[0])/2, (low[1]+high[1])/2, low[2]]
    # Geographic centroid is a fitting candidate; containment remains mandatory
    # for concave pads and every native part rectangle. No footprint is reshaped.
    center = [sum(p[i] for p in ring)/len(ring) for i in range(2)]
    angle = math.radians(yaw); cosine, sine = math.cos(angle), math.sin(angle)
    def world(native_point):
        x, z, y = [native_point[i]-anchor[i] for i in (0, 1, 2)]
        return [center[0]+cosine*x-sine*z, base+y, center[1]+sine*x+cosine*z]
    def rectangle(lo, hi):
        return [[p[0], p[2]] for p in (world([lo[0], lo[1], low[2]]), world([hi[0], lo[1], low[2]]),
            world([hi[0], hi[1], low[2]]), world([lo[0], hi[1], low[2]]))]
    envelope = rectangle(low, high)
    predicate = contains or _sf_contained
    if not predicate(envelope, ring):
        raise ValueError('source_family_complete_envelope_leaves_geographic_pad')
    pad_area = abs(sum(a[0]*ring[(i+1) % len(ring)][1]-a[1]*ring[(i+1) % len(ring)][0] for i, a in enumerate(ring))/2)
    envelope_area = (high[0]-low[0])*(high[1]-low[1])
    minimum_coverage = _sf_vec([entry.get('minimum_pad_coverage_ratio', 0.45)], 1)[0]
    if not 0.45 <= minimum_coverage <= 1.0:
        raise ValueError('source_family_minimum_pad_coverage_weaker_than_retained_contract')
    coverage_ratio = envelope_area/pad_area
    if coverage_ratio+1e-9 < minimum_coverage:
        raise ValueError('source_family_envelope_covers_too_little_of_geographic_pad')
    placements = []
    orient = [0.0, -math.sin(angle/2), 0.0, math.cos(angle/2)]
    for slot, (source, part, part_low, part_high, translation, role, repeat_index) in enumerate(expanded):
        lo = [part_low[i]+translation[i] for i in range(3)]
        hi = [part_high[i]+translation[i] for i in range(3)]
        footprint = rectangle(lo, hi)
        if not predicate(footprint, ring):
            raise ValueError('source_family_native_part_leaves_geographic_pad:' + source['name'])
        identifier = '%s:%s:source_family:%s:%s:%s:%s' % (area_id, osm_id, family['family_id'], mode, source['name'], repeat_index)
        slots = list(part['material_slots'])
        placements.append({'placement_id': identifier, 'path': part['path'], 'asset_id': part['asset_id'],
            'module_key': source['name'], 'role': 'building_module', 'rule': 'complete_source_family_assembly',
            'P': world(translation), 'orient': orient, 'scale': [1.0, 1.0, 1.0], 'native_scale': [1.0, 1.0, 1.0],
            # The old cook uses floor==0 solely to collect terrain support probes.
            # Every part contributes horizontal support probes; this is no story.
            'floor': 0, 'architectural_floor_index': None, 'source_region_label': source.get('source_role_label'),
            'edge_index': -1, 'slot': slot, 'footprint_xz_m': footprint, 'ground_contact_y_m': base,
            'source_area_id': area_id, 'source_osm_id': osm_id, 'selection_source': 'explicit_scoped_complete_source_family_contract',
            'catalog_release': False, 'height_rule': feature.get('height_rule', 'unknown'), 'material_slots': slots,
            'style_family_id': family['family_id'], 'style_palette_id': 'source_preserved',
            'material_signature': _sf_digest(slots)[:16], 'source_part_sha256': source['fbx_sha256'],
            'source_assembly_translation_m': source['assembly_translation_m'], 'band_role': role, 'repeat_index': repeat_index})
    if len({p['placement_id'] for p in placements}) != len(placements):
        raise ValueError('source_family_duplicate_placement_identity')
    return {'schema': 'environmentpipeline.native_building_assembly_record.v1', 'status': 'complete',
        'source_feature': {'area_id': area_id, 'osm_id': osm_id}, 'footprint_xz_m': ring,
        'native_family_envelope_xz_m': envelope, 'base_m': base, 'height_m': height,
        'footprint_area_m2': pad_area, 'generated_closed_solid_count': 0,
        'building_use': actual_use, 'building_use_evidence': feature.get('building_use_evidence', {'source': 'not_present_on_retained_pad', 'verified': False}),
        'requested_source_height_m': requested_height, 'height_rule': feature.get('height_rule', 'unknown'),
        'stories': None, 'story_height_m': None, 'architectural_floors_certified': False,
        'source_geometric_tiers_are_floors': False, 'wall_placements': placements, 'generated_parts': [],
        'module_count': len(placements), 'style_family_id': family['family_id'], 'style_palette_id': 'source_preserved',
        'style_selection': {'policy': 'stable_complete_source_family', 'rejected_families': []},
        'closure_policy': 'all_matched_source_parts_or_complete_start_repeat_end_no_generated_substitution',
        'source_family': {'family_id': family['family_id'], 'parent_asset_id': family['parent_asset_id'],
            'parent_catalog_row': family['parent_catalog_row'], 'source_family_sha256': family_digest,
            'native_manifest_sha256': native_digest, 'mode': mode, 'repeat_count': repeat_count,
            'rigid_yaw_degrees': yaw, 'source_to_native_matrix': matrix, 'material_substitution': False,
            'source_facing_verified': entry.get('source_facing_verified') is True,
            'source_geometry_scaled': False, 'appearance_accepted': False, 'runtime_selection_authorized': not audit_only,
            'ordinary_selection_enabled': not audit_only and not qualification,
            'connection_without_additional_tests': connection and not audit_only,
            'qualification_pending': (qualification or connection) and not audit_only,
            'pending_validation_gates': pending_gates,
            'parent_canonical_holds_unchanged': True},
        'coverage_check': {'complete_family': True, 'native_envelope_inside_pad': True,
            'geographic_pad_area_m2': pad_area, 'native_family_envelope_area_m2': envelope_area,
            'native_pad_coverage_ratio': coverage_ratio, 'minimum_pad_coverage_ratio': minimum_coverage,
            'matching_source_connections_only': True, 'terrain_contact': 'retained_cook_must_verify_final_heightfield'}}


def source_family_select(feature, registry, contains=None):
    """Stable weighted qualified ordering; failed fits never weaken fallback."""
    qualification_targets = []
    for entry in registry.get('families', []):
        if entry.get('execution_mode') != 'qualification':
            continue
        scopes = entry.get('qualification_target_source_ids', {})
        if not isinstance(scopes, dict) or not scopes or any(not isinstance(ids, list) or not ids for ids in scopes.values()):
            raise SourceFamilyQualificationError('source_family_qualification_exact_target_configuration_missing')
        if str(feature.get('osm_id')) in scopes.get(str(feature.get('area_id')), []):
            qualification_targets.append(entry)
    if len(qualification_targets) > 1:
        raise SourceFamilyQualificationError('source_family_multiple_qualification_families_assigned_to_one_pad')
    if registry.get('schema') != SOURCE_FAMILY_PROTOCOL or registry.get('enabled') is not True:
        if qualification_targets:
            raise SourceFamilyQualificationError('source_family_requested_qualification_registry_disabled')
        return None, [{'reason': 'source_family_registry_disabled_or_schema_invalid'}]
    entries = registry.get('families', [])
    ids = [entry.get('family_id') for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError('source_family_duplicate_registry_identity')
    seed = int(registry.get('selection_seed', 1337))
    def score(entry):
        weight = _sf_vec([entry.get('weight', 1.0)], 1)[0]
        if weight <= 0:
            raise ValueError('source_family_selection_weight_invalid')
        identity = '%s|%s|%s|%s' % (seed, feature['area_id'], feature['osm_id'], entry['family_id'])
        fraction = (int(hashlib.sha256(identity.encode()).hexdigest()[:15], 16)+0.5)/float(16**15)
        return -math.log(fraction)/weight, entry['family_id']
    rejected = []
    candidates = qualification_targets if qualification_targets else [e for e in entries
        if e.get('enabled') is True and e.get('execution_mode', 'ordinary_selection') != 'qualification']
    if qualification_targets and qualification_targets[0].get('enabled') is not True:
        raise SourceFamilyQualificationError('source_family_requested_qualification_entry_disabled')
    for entry in sorted(candidates, key=score):
        try:
            bindings = _sf_load_ref(entry.get('source_bindings_ref'))
            families = [f for f in bindings.get('families', []) if f['family_id'] == entry['family_id']]
            if len(families) != 1:
                raise ValueError('source_family_source_identity_missing_or_duplicate')
            family = families[0]; native = _sf_load_ref(entry.get('native_manifest_ref'))
            execution = entry.get('execution_mode', 'ordinary_selection')
            if execution not in ('ordinary_selection', 'qualification', 'connection'):
                raise ValueError('source_family_unknown_execution_mode')
            qualification = execution == 'qualification'
            connection = execution == 'connection'
            if qualification:
                requested = entry.get('qualification_variations', [])
                variations = [(item['mode'], item['repeat_count']) for item in requested]
            else:
                variations = [(mode, count) for mode, capability in sorted(entry.get('capabilities', {}).items())
                    if capability.get('enabled') is True for count in capability.get('allowed_repeat_counts', [1])]
            def variation_order(value):
                return _sf_digest([seed, feature['area_id'], feature['osm_id'], entry['family_id'], *value])
            for mode, count in sorted(variations, key=variation_order):
                for offset in entry.get('allowed_rigid_yaw_offsets_degrees', [0, 90, 180, 270]):
                    yaw = _sf_pad_edge_yaw(feature) + _sf_vec([offset], 1)[0]
                    try:
                        record = source_family_plan(feature, family, native, entry, mode, count, yaw,
                            contains=contains, qualification=qualification, connection=connection)
                    except (ValueError, OSError, KeyError, TypeError) as error:
                        rejected.append({'family_id': entry['family_id'], 'mode': mode, 'repeat_count': count,
                            'yaw_degrees': yaw, 'reason': str(error)})
                        continue
                    record['style_selection']['rejected_families'] = rejected
                    return record, rejected
            if not variations:
                rejected.append({'family_id': entry['family_id'], 'reason': 'source_family_no_enabled_capabilities'})
        except (ValueError, OSError, KeyError, TypeError) as error:
            rejected.append({'family_id': entry['family_id'], 'reason': str(error)})
    if qualification_targets:
        raise SourceFamilyQualificationError('source_family_requested_qualification_failed:' + json.dumps(rejected, sort_keys=True))
    return None, rejected


# Appending AFTER r018 style wrappers leaves every earlier output path unchanged.
# Its old cook resolves assembly_layout globally when it runs, so no SOP rewiring,
# alternative output bridge, native scene mutation or protected API is necessary.
if 'assembly_layout' in globals():
    _SOURCE_FAMILY_PREVIOUS_LAYOUT = assembly_layout

    def assembly_layout(feature, contract):
        registry_ref = contract.get('source_family_registry_ref')
        if not registry_ref:
            return _SOURCE_FAMILY_PREVIOUS_LAYOUT(feature, contract)
        try:
            registry = _sf_load_ref(registry_ref)
            feature = dict(feature)
            feature.update(_SOURCE_FAMILY_USE_CONTEXT.get((str(feature['area_id']), str(feature['osm_id'])), {}))
            record, rejected = source_family_select(feature, registry,
                contains=globals().get('_assembly_polygon_contained', _sf_contained))
        except SourceFamilyQualificationError:
            raise
        except (ValueError, OSError, KeyError, TypeError) as error:
            record, rejected = None, [{'reason': str(error)}]
        if record is not None:
            return record
        record = _SOURCE_FAMILY_PREVIOUS_LAYOUT(feature, contract)
        record['source_family_selection'] = {'status': 'retained_fallback', 'rejected_families': rejected,
            'holds_preserved': True, 'unqualified_partial_output_emitted': False}
        return record


if 'cook_normal_building_assembly_points' in globals():
    _SOURCE_FAMILY_PREVIOUS_COOK = cook_normal_building_assembly_points

    def cook_normal_building_assembly_points(node):
        """Read only existing identity-bound pad use attributes; never infer use."""
        global _SOURCE_FAMILY_USE_CONTEXT, _SOURCE_FAMILY_EVIDENCE_CACHE
        previous = _SOURCE_FAMILY_USE_CONTEXT
        previous_cache = _SOURCE_FAMILY_EVIDENCE_CACHE
        context = {}
        inputs = node.inputs()
        if len(inputs) > 1 and inputs[1] is not None:
            pads = inputs[1].geometry()
            for primitive in pads.prims():
                if not pads.findPrimAttrib('source_area_id') or not pads.findPrimAttrib('source_osm_id'):
                    continue
                identity = (str(primitive.attribValue('source_area_id')), str(primitive.attribValue('source_osm_id')))
                for name in ('building_use', 'source_building_use', 'building_class', 'source_building_class'):
                    if pads.findPrimAttrib(name):
                        value = primitive.attribValue(name)
                        if isinstance(value, str) and value.strip():
                            context[identity] = {'building_use': value.strip(), 'building_use_evidence': {
                                'source': 'identity_bound_original_pad_attribute', 'attribute': name,
                                'source_area_id': identity[0], 'source_osm_id': identity[1], 'verified': True}}
                            break
        _SOURCE_FAMILY_USE_CONTEXT = context
        _SOURCE_FAMILY_EVIDENCE_CACHE = {}
        try:
            return _SOURCE_FAMILY_PREVIOUS_COOK(node)
        finally:
            _SOURCE_FAMILY_USE_CONTEXT = previous
            _SOURCE_FAMILY_EVIDENCE_CACHE = previous_cache
