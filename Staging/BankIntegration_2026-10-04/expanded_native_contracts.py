"""Complete the measured non-held cohort without treating metadata as acceptance.

This module only writes bank configuration inputs. It never imports Unreal, clears
holds, changes style provenance, or marks an asset ready for runtime selection.
"""
import copy
import math


HOST_CASES = {
    'current_ModularCourtyard__Meshes__SM_Cap_dumpster': (
        'component_of_dumpster', 'Parent dumpster identity, hinge/local frame and open/closed state; this is a lid, not a complete street bin.'),
    'current_ModularCourtyard__Meshes__SM_Lamp': (
        'wall_or_overhead_light', 'Native visual review must establish its bracket/support; a wall or overhead fixture needs host identity and attachment frame.'),
    'current_ProceduralBuildingGenerator__Meshes__PGB_Meshes__Lamp_Var2': (
        'wall_or_overhead_light', 'Native visual review must establish its bracket/support; a wall or overhead fixture needs host identity and attachment frame.'),
    'current_ProceduralBuildingGenerator__Meshes__Slum__SM_Slums_Light_01a': (
        'hanging_light', 'Hanging fixture extends below its origin. Requires overhead host, suspension point and mount height.'),
    'current_ProceduralBuildingGenerator__Meshes__Slum__SM_Slums_Light_01b': (
        'hanging_light', 'Hanging fixture extends below its origin. Requires overhead host, suspension point and mount height.'),
    'current_UtopianCity__Meshes__SM_Lamp01': (
        'wall_or_overhead_light', 'Mesh minimum is 127.54 cm above its origin. Preserve authored offset; establish host/support before any placement.'),
}


def _contact(role, name):
    text = name.lower()
    if role == 'whole_building':
        return 'building_foundation', 'Preserve complete measured footprint at native scale; choose geographic footprint fit, not stretching.'
    if role in ('tree', 'shrub', 'understory'):
        return 'root_or_stem_base', 'Use the root/stem support plane; leaf-card or buried-root minimum is not automatically the ground plane.'
    if 'stone_' in text:
        return 'authored_rock_embedment', 'Preserve intended embedment; the lowest buried rock vertex is not an accepted support plane.'
    if any(token in text for token in ('bicycle', 'wreck', 'destryoedcar', 'foodcart', '_cart')):
        return 'wheel_and_support_contact', 'Read wheel/support contact and native facing; preserve functional support and complete dimensions.'
    if any(token in text for token in ('bench', 'grill', 'rack', 'parasol', 'barrier', 'road_block')):
        return 'feet_or_support_base', 'Read actual feet/support vertices and outward facing; retain native geometry and full clearance.'
    if role == 'street_pole' or 'flagpole' in text:
        return 'pole_base', 'Read shaft/base support and the direction of any overhead arm; retain full measured clearance.'
    return 'ground_support', 'Verify the measured lower support surface; source vertex bounds alone do not mark contact or material appearance accepted.'


def expand(initial, prepared_rows, records, areas, rules):
    """Keep the initial detailed work and cover every additional measured candidate."""
    result = {r['asset_id']: copy.deepcopy(r) for r in initial}
    for aid, p in prepared_rows.items():
        m = p.get('native_measurement')
        if not m or m.get('status') != 'measured' or p['runtime_enabled']:
            continue
        if p['runtime_hold_preserved'] or p['hold_reasons_preserved'] or p['named_holds_preserved'] or p['palm_hold_not_released']:
            continue
        record = records[aid]
        rt = record['runtime']
        role = p['request_role']
        # These exact measured variants belong to the existing pole consumer.
        if aid in {'current_AssetsvilleTown__Meshes__StreetProps__SM_utility_pole_' + str(i) for i in range(1, 5)}:
            role = 'street_pole'
        assert role in rules, (aid, role)
        bounds = m.get('vertex_bounds_cm', m['bounds_cm'])
        contact, note = _contact(role, p['name'])
        zones = 'open_ground'
        if role in ('street_prop', 'street_pole'):
            zones = 'roadside'
        if role == 'whole_building':
            zones = 'building_yes|building_residential|building_house|building_apartments|building_commercial'
        base_spacing = {'small_prop': 350, 'street_prop': 600, 'street_pole': 1500,
                        'understory': 180, 'shrub': 350, 'tree': 800, 'whole_building': 0}[role]
        # Bounding diagonal plus clearance is conservative and does not resize geometry.
        diagonal = math.hypot(bounds['max'][0] - bounds['min'][0], bounds['max'][1] - bounds['min'][1])
        job = result.get(aid, {
            'asset_id': aid, 'row_name': p['catalog_row_name'], 'object_path': rt['ObjectPath'],
            'package_sha256': p['current_package_sha256'], 'role': role, 'placement_rule': rules[role],
            'contact_kind': contact, 'anchor_z_cm': bounds['min'][2],
            'anchor_basis': 'Measured minimum retained as a candidate only; individual functional support review may override it.',
            'bounds_cm': bounds, 'forward_axis': '+X',
            'forward_basis': 'Unconstrained yaw is acceptable only for reviewed nondirectional ground clutter/vegetation; directional furniture and buildings require native review.',
            'native_scale': [1, 1, 1], 'allowed_areas': list(areas), 'allowed_zones': zones,
            'style_context': rt['StyleSet'], 'source_style_preserved': record['environment_style_set'],
            'family_id': rt['FamilyId'], 'min_spacing_cm': max(base_spacing, int(math.ceil(diagonal + 100))),
            'material_slots': m['material_slots'], 'existing_instance_materials': [],
            'review_note': note, 'historical_native_images': p['native_preview_sources'],
            'rights_state_preserved': record['recorded_rights_state'],
            'state': 'configuration_saved_native_contact_material_review_pending',
            'activation_requires': 'NATIVE_VALIDATION.json explicit per-asset ready=true with matching source SHA, contact/facing review, verified instance materials and no unresolved native dependency',
        })
        constraints = []
        automatic_ground_allowed = True
        if aid in HOST_CASES:
            mechanism, reason = HOST_CASES[aid]
            constraints.append({'kind': 'host_consumer_required', 'mechanism': mechanism, 'reason': reason})
            automatic_ground_allowed = False
        name = p['name'].lower()
        if 'traffic_lights_' in name:
            constraints.append({'kind': 'traffic_control_context', 'mechanism': 'junction_or_crossing_approach',
                                'reason': 'Require source junction/crossing, road approach and signal facing. Generic roadside_prop requests do not establish these.'})
            automatic_ground_allowed = False
        if any(v in name for v in ('road_block', 'road_cone', 'barrier')):
            constraints.append({'kind': 'boundary_or_worksite_context', 'mechanism': 'source_boundary_or_worksite',
                                'reason': 'Distinguish freestanding support from a linear fence/boundary and require the actual placement context; do not randomly obstruct streets.'})
            automatic_ground_allowed = False
        if 'parking_meter' in name or 'public_phone' in name or 'mailbox' in name or 'hydrant' in name:
            constraints.append({'kind': 'functional_street_context', 'mechanism': 'supported_local_street_service',
                                'reason': 'Native support can be configured, but street-service context and functional facing must be individually established.'})
        if m['dependencies']['unresolved_registry_packages']:
            constraints.append({'kind': 'missing_native_dependencies', 'paths': m['dependencies']['unresolved_registry_packages']})
            automatic_ground_allowed = False
        job['automatic_ground_activation_allowed'] = automatic_ground_allowed
        job['suitability_constraints'] = constraints
        job['style_policy'] = {
            'source_style_preserved': record['environment_style_set'],
            'configured_runtime_style': job['style_context'],
            'gaza_profile_style': 'mediterranean_urban',
            'matches_current_gaza_style': job['style_context'] == 'mediterranean_urban',
            'reason': 'The installed selector requires an exact StyleSet match. Style provenance is not silently rewritten to make a row selectable.',
        }
        result[aid] = job
    return list(result.values())
