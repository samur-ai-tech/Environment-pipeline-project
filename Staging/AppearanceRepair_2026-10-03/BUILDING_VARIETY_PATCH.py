"""Append after the retained r017 normal assembly implementation.

Only a validated building_style_variants field in the existing scoped assembly
contract enables this patch. Native whole-building selection is untouched.
Native bounds, closure/door/height/footprint and final terrain gates are reused.
"""

_STYLE_VARIETY_MESH_PATHS = {
    'closed4': '/Game/ModularCourtyard/Meshes/SM_wall_windows_close_4x4_01.SM_wall_windows_close_4x4_01',
    'single4': '/Game/ModularCourtyard/Meshes/SM_wall_windows_one_4x4_open.SM_wall_windows_one_4x4_open',
    'narrow2': '/Game/ModularCourtyard/Meshes/SM_wall_windowsT2_4x2_01.SM_wall_windowsT2_4x2_01',
}
_STYLE_WALL_SOURCE = '/Game/ModularCourtyard/Mats/MI_Wall_PlasterBrick.MI_Wall_PlasterBrick'
_STYLE_VARIETY_PREVIOUS_CONTRACT = _assembly_contract
_STYLE_VARIETY_PREVIOUS_LAYOUT = assembly_layout
_STYLE_VARIETY_PREVIOUS_COOK = cook_normal_building_assembly_points


def _style_game_path(value):
    return isinstance(value, str) and re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+', value)


def _style_surface_indices(module):
    original = module.get('original_material_slots', [])
    return [i for i, path in enumerate(original) if path == _STYLE_WALL_SOURCE]


def _style_validate(contract, area_id):
    styles = contract.get('building_style_variants')
    if not styles or not styles.get('enabled'):
        return None
    if styles.get('schema') != 'environmentpipeline.native_building_styles.v1':
        raise ValueError('building_style_schema_mismatch')
    scopes = set(styles.get('scope_area_ids', []))
    if area_id not in scopes or not scopes <= {'GazaRimal', 'GazaShujaiya'}:
        raise ValueError('building_style_area_outside_scoped_authorization')
    modules = styles.get('modules', {})
    families = [f for f in styles.get('families', []) if f.get('enabled', True)]
    palettes = [p for p in styles.get('palettes', []) if p.get('enabled', True)]
    for entries, label in ((families, 'family'), (palettes, 'palette')):
        ids = [entry.get('id') for entry in entries]
        if len(ids) != len(set(ids)) or any(not isinstance(i, str) or not re.fullmatch(r'[a-z0-9_]+', i) for i in ids):
            raise ValueError('building_style_invalid_' + label + '_identity')
        for entry in entries:
            weight = float(entry.get('weight', 1.0))
            if not math.isfinite(weight) or weight <= 0:
                raise ValueError('building_style_invalid_' + label + '_weight')
    if len(families) < 2 or len(palettes) < 2:
        raise ValueError('building_style_requires_real_mesh_families_and_native_palettes')
    window_paths = set()
    used_keys = set()
    for family in families:
        overrides = family.get('module_overrides', {})
        if not set(overrides) <= {'window4', 'plain4', 'plain2', 'plain1'}:
            raise ValueError('building_style_door_or_unknown_module_override')
        if any(key not in modules for key in overrides.values()):
            raise ValueError('building_style_module_registry_missing')
        used_keys.update(overrides.values())
        window_key = overrides.get('window4')
        window_paths.add(modules[window_key]['path'] if window_key else contract['modules']['window4']['path'])
    if len(window_paths) < 2:
        raise ValueError('building_style_mesh_variety_cannot_be_only_recoloring')
    for key in used_keys:
        module = modules[key]
        if module.get('path') != _STYLE_VARIETY_MESH_PATHS.get(key):
            raise ValueError('building_style_mesh_outside_exact_native_whitelist:' + key)
        if (module.get('actual_named_or_dependency_hold') is not False
                or module.get('dependency_status') != 'closed'
                or module.get('route_hold_preserved') is not True
                or not module.get('native_measurement_source')
                or module.get('axis_contract') != 'X_inward_minusY_along_Z_up'):
            raise ValueError('building_style_native_dependency_measurement_or_axis_unconfirmed:' + key)
        low, high = module.get('min_cm', []), module.get('max_cm', [])
        if len(low) != 3 or len(high) != 3 or not all(math.isfinite(float(v)) for v in low + high):
            raise ValueError('building_style_native_bounds_invalid:' + key)
        if any(float(high[i]) <= float(low[i]) for i in range(3)):
            raise ValueError('building_style_native_bounds_degenerate:' + key)
        if (float(high[0]) - float(low[0])) / 100.0 > float(contract['closure_thickness_m']) + 1e-6:
            raise ValueError('building_style_native_depth_exceeds_retained_closure_envelope:' + key)
        slots = module.get('material_slots', [])
        originals = module.get('original_material_slots', [])
        if not slots or len(slots) != len(originals) or not all(_style_game_path(p) for p in slots + originals):
            raise ValueError('building_style_native_slots_missing:' + key)
        if not _style_surface_indices(module):
            raise ValueError('building_style_native_wall_surface_slot_unconfirmed:' + key)
    for palette in palettes:
        if (palette.get('source_material_path') != _STYLE_WALL_SOURCE
                or palette.get('dependency_status') != 'closed'
                or palette.get('actual_named_or_dependency_hold') is not False
                or not palette.get('native_parameter_evidence')
                or not _style_game_path(palette.get('surface_material_path'))
                or not palette['surface_material_path'].startswith('/Game/Project/Shared/ModelBank/Materials/')):
            raise ValueError('building_style_native_palette_unconfirmed:' + palette['id'])
    return styles


def _assembly_contract(parent, area_id):
    contract = _STYLE_VARIETY_PREVIOUS_CONTRACT(parent, area_id)
    if contract is not None:
        _style_validate(contract, area_id)
    return contract


def _style_order(entries, seed, area_id, osm_id, tag):
    """Stable weighted ordering; changes to material paths do not reshuffle lots."""
    def score(entry):
        identity = '%s|%s|%s|%s|%s' % (seed, area_id, osm_id, tag, entry['id'])
        digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()
        fraction = (int(digest[:15], 16) + 0.5) / float(16 ** 15)
        return (-math.log(fraction) / float(entry.get('weight', 1.0)), entry['id'])
    return sorted(entries, key=score)


def _style_family_contract(contract, styles, family, palette):
    chosen = dict(contract)
    chosen['modules'] = {key: dict(module) for key, module in contract['modules'].items()}
    for key, variant_key in family.get('module_overrides', {}).items():
        chosen['modules'][key] = dict(styles['modules'][variant_key])
    for key, module in chosen['modules'].items():
        if key == 'door':
            continue
        indices = _style_surface_indices(module)
        if not indices:
            raise ValueError('building_style_wall_surface_slot_missing:' + key)
        slots = list(module['material_slots'])
        for index in indices:
            slots[index] = palette['surface_material_path']
        module['material_slots'] = slots
    chosen['closure_material_path'] = palette['surface_material_path']
    return chosen


def assembly_layout(feature, contract):
    styles = _style_validate(contract, feature['area_id'])
    if styles is None:
        return _STYLE_VARIETY_PREVIOUS_LAYOUT(feature, contract)
    seed, area_id, osm_id = int(styles.get('selection_seed', 1337)), feature['area_id'], str(feature['osm_id'])
    families = _style_order([f for f in styles['families'] if f.get('enabled', True)], seed, area_id, osm_id, 'family')
    palettes = _style_order([p for p in styles['palettes'] if p.get('enabled', True)], seed, area_id, osm_id, 'palette')
    palette, rejected = palettes[0], []
    for family in families:
        try:
            selected_contract = _style_family_contract(contract, styles, family, palette)
            record = _STYLE_VARIETY_PREVIOUS_LAYOUT(feature, selected_contract)
            for item in record['wall_placements']:
                if not _assembly_polygon_contained(item['footprint_xz_m'], record['footprint_xz_m']):
                    raise ValueError('building_style_native_envelope_leaves_geographic_footprint')
        except ValueError as error:
            rejected.append({'family_id': family['id'], 'reason': str(error)})
            continue
        record['style_family_id'] = family['id']
        record['style_palette_id'] = palette['id']
        record['style_selection'] = {'policy': 'source_building_stable_weighted_family_and_palette',
            'seed': seed, 'requested_family_order': [f['id'] for f in families], 'rejected_families': rejected,
            'native_mesh_variety': True, 'door_slab_source_height_and_footprint_rules_preserved': True}
        for item in record['wall_placements']:
            item['style_family_id'] = family['id']
            item['style_palette_id'] = palette['id']
            item['material_signature'] = hashlib.sha256(json.dumps(item['material_slots'], separators=(',', ':')).encode()).hexdigest()[:16]
        return record
    # A style miss never destroys previously valid native building coverage.
    record = _STYLE_VARIETY_PREVIOUS_LAYOUT(feature, contract)
    record['style_family_id'] = 'retained_safe_baseline'
    record['style_palette_id'] = 'retained_native_materials'
    record['style_selection'] = {'policy': 'explicit_style_fit_failed_retained_baseline', 'seed': seed,
        'requested_family_order': [f['id'] for f in families], 'rejected_families': rejected}
    for item in record['wall_placements']:
        item['style_family_id'] = record['style_family_id']
        item['style_palette_id'] = record['style_palette_id']
        item['material_signature'] = hashlib.sha256(json.dumps(item['material_slots'], separators=(',', ':')).encode()).hexdigest()[:16]
    return record


def cook_normal_building_assembly_points(node):
    _STYLE_VARIETY_PREVIOUS_COOK(node)
    geo = node.geometry()
    if geo.findGlobalAttrib('building_assembly_records_json') is None:
        return
    records = json.loads(geo.attribValue('building_assembly_records_json'))
    if not records or not any('style_family_id' in record for record in records):
        return
    by_id = {item['placement_id']: item for record in records for item in record['wall_placements']}
    for point in geo.points():
        placement_id = point.attribValue('placement_id')
        item = by_id.get(placement_id)
        values = {'assembly_style_id': item['style_family_id'] if item else '',
            'assembly_palette_id': item['style_palette_id'] if item else '',
            'assembly_material_signature': item['material_signature'] if item else 'retained_native_default'}
        for key, value in values.items():
            point.setAttribValue(_attr(geo, hou.attribType.Point, key, ''), value)
    # Official installed translator reads this attribute-name declaration, then
    # point strings to split instance groups before applying native overrides.
    _set_detail(geo, 'unreal_split_attr', 'assembly_material_signature')
    receipt = json.loads(geo.attribValue('bank_catalog_readback_json'))
    family_counts, palette_counts, rejected_reasons, component_counts = {}, {}, {}, {}
    for record in records:
        family = record['style_family_id']; palette = record['style_palette_id']
        family_counts[family] = family_counts.get(family, 0) + 1
        palette_counts[palette] = palette_counts.get(palette, 0) + 1
        for rejection in record.get('style_selection', {}).get('rejected_families', []):
            reason = rejection['reason']; rejected_reasons[reason] = rejected_reasons.get(reason, 0) + 1
        for item in record['wall_placements']:
            key = (item['path'], tuple(item['material_slots']))
            component_counts[key] = component_counts.get(key, 0) + 1
    summary = {'schema': 'environmentpipeline.native_building_style_summary.v1',
        'family_building_counts': family_counts, 'palette_building_counts': palette_counts,
        'candidate_family_rejection_reasons': rejected_reasons,
        'expected_assembly_mesh_material_counts': [{'mesh': key[0], 'material_slots': list(key[1]), 'instances': count}
            for key, count in sorted(component_counts.items())],
        'official_instance_split_attribute': 'assembly_material_signature',
        'native_part_placement_ids_preserved': True, 'appearance_accepted': False}
    receipt['building_style_variants'] = summary
    receipt['building_assembly']['style_family_counts'] = family_counts
    receipt['building_assembly']['style_palette_counts'] = palette_counts
    _set_detail(geo, 'building_style_summary_json', json.dumps(summary, sort_keys=True))
    _set_detail(geo, 'building_assembly_summary_json', json.dumps(receipt['building_assembly'], sort_keys=True))
    _set_detail(geo, 'bank_catalog_readback_json', json.dumps(receipt, sort_keys=True, allow_nan=False))
    report = node.parent().evalParm('bank_receipt_file').strip()
    if report:
        Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')
