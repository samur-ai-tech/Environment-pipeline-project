"""Geographic ground/Grass connection inside the retained ordinary lifecycle.

Uses the existing material, painted Ground/RoadBed/BuildingPad/Steep targets
and already enabled grass rows. Trees/shrubs retain their HDA placement rules.
There is no separate scatter actor, geography import or bank release.
"""
import hashlib
import json
import math
import unreal

OWNER = 'GeoCity_LandscapeGrass'
LIB = unreal.MaterialEditingLibrary
ROOT = '/Game/Project/Shared/SurfacePainting/Appearance_20261003/'
BASE = ROOT + 'MI_SurfaceBank_Natural.MI_SurfaceBank_Natural'
MASTER = ROOT + 'M_SurfaceBank_Natural.M_SurfaceBank_Natural'
GRASS_TYPE = ROOT + 'LG_GeoCity_PermittedGroundGrass'
TARGETS = {'Ground': 'Sand_01', 'Steep': 'Sand_02',
           'RoadBed': 'Dirt_Path', 'BuildingPad': 'Sand_Path'}
CHOICES = {'paint_ground_choice': 17, 'paint_steep_choice': 18,
           'paint_roadbed_choice': 16, 'paint_buildingpad_choice': 20}
PERMITTED_MESHES = (
    '/Game/Palms_Pack_01/Add_Props/Grass/Meshes/SM_Grass_02_3.SM_Grass_02_3',
    '/Game/Palms_Pack_01/Add_Props/Grass/Meshes/SM_Grass_05_2.SM_Grass_05_2')
WEIGHT_TOLERANCE = 4.0 / 255.0


def _path(obj):
    return obj.get_path_name() if obj else None


def _nodes(material):
    # Installed public API reads the asset without opening a material editor.
    return list(LIB.get_material_expressions(material))


def _config(profile):
    config = profile['landscape_grass']
    if config['base_material_instance'] != BASE or config['ground_layer'] != TARGETS['Ground']:
        raise RuntimeError('Grass requires the retained Natural/Ground material contract.')
    if tuple(config['mesh_paths']) != PERMITTED_MESHES:
        raise RuntimeError('This assignment permits exactly the two retained grass meshes.')
    if set(profile.get('painted_layer_names', [])) != set(TARGETS.values()):
        raise RuntimeError('Four distinct geographic paint targets are required.')
    if any(profile.get('surface_choices', {}).get(k) != v for k, v in CHOICES.items()):
        raise RuntimeError('Geographic role-to-layer routing differs from the Grass contract.')
    for key, low, high in (('coverage', 0.0, 1.0), ('density_per_10m2', 0.0, 1000.0)):
        value = float(config[key])
        if not math.isfinite(value) or not low < value <= high:
            raise RuntimeError('Invalid native Grass ' + key)
    probes = config.get('paint_probe_locations', [])
    if not {'RoadBed', 'BuildingPad'}.issubset({p.get('expected_role') for p in probes}):
        raise RuntimeError('Manager-reviewed known road and pad paint probes are required.')
    if len({p['id'] for p in probes}) != len(probes):
        raise RuntimeError('Geographic paint probe identifiers must be unique.')
    for probe in probes:
        if not isinstance(probe.get('id'), str) or not probe['id'].strip():
            raise RuntimeError('Geographic paint probes need nonempty string identifiers.')
        xyz = probe.get('world_location_cm', [])
        if len(xyz) != 3 or not all(math.isfinite(float(v)) for v in xyz):
            raise RuntimeError('Geographic paint probes need three finite world coordinates.')
        minimum = float(probe.get('minimum_weight', .8))
        if probe.get('expected_role') not in TARGETS or not math.isfinite(minimum) or not .8 <= minimum <= 1:
            raise RuntimeError('Invalid geographic paint probe role/threshold.')
    return config


def _read_varieties(grass):
    result = []
    for variety in grass.get_editor_property('grass_varieties'):
        entry = {'mesh': _path(variety.get_editor_property('grass_mesh')),
                 'materials': [_path(m) for m in variety.get_editor_property('override_materials')]}
        for key in ('grass_density', 'grass_density_quality', 'start_cull_distance',
                    'end_cull_distance', 'start_cull_distance_quality', 'end_cull_distance_quality'):
            value = variety.get_editor_property(key)
            entry[key] = float(value.get_editor_property('default'))
            # An inherited platform/quality override must not silently defeat defaults.
            override = 'per_quality' if key.endswith('_quality') else 'per_platform'
            entry[key + '_overrides'] = {str(k): float(v) for k, v in
                                        dict(value.get_editor_property(override)).items()}
        for key in ('use_grid', 'placement_jitter', 'random_rotation', 'align_to_surface',
                    'weight_attenuates_max_scale', 'min_lod'):
            entry[key] = variety.get_editor_property(key)
        entry['scaling'] = str(variety.get_editor_property('scaling'))
        for key in ('scale_x', 'scale_y', 'scale_z', 'allowed_density_range'):
            value = variety.get_editor_property(key)
            entry[key] = [float(value.get_editor_property('min')), float(value.get_editor_property('max'))]
        result.append(entry)
    return result


def _expected_varieties(profile, config):
    result = []
    for path in config['mesh_paths']:
        entry = {'mesh': path, 'materials': profile.get('instance_materials', {}).get(path, []),
                 'use_grid': True, 'placement_jitter': 1.0, 'random_rotation': True,
                 'align_to_surface': True, 'weight_attenuates_max_scale': False,
                 'min_lod': -1, 'scaling': str(unreal.GrassScaling.UNIFORM),
                 'allowed_density_range': [0.0, 1.0], 'scale_x': [1.0, 1.0],
                 'scale_y': [1.0, 1.0], 'scale_z': [1.0, 1.0]}
        for key, value in (('grass_density', float(config['density_per_10m2']) / len(config['mesh_paths'])),
                           ('start_cull_distance', 10000), ('end_cull_distance', 20000)):
            for suffix in ('', '_quality'):
                entry[key + suffix] = value
                entry[key + suffix + '_overrides'] = {}
        result.append(entry)
    return result


def _verify_textures(profile, material):
    bindings = {}
    for parameter, entry in profile.get('surface_normal_overrides', {}).items():
        texture = LIB.get_material_instance_texture_parameter_value(material, parameter)
        if _path(texture) != entry['copy']:
            raise RuntimeError('Corrected ground normal dependency differs: ' + parameter)
        if texture.get_editor_property('srgb') or texture.get_editor_property('compression_settings') != unreal.TextureCompressionSettings.TC_NORMALMAP:
            raise RuntimeError('Corrected ground normal is no longer linear/normal-compressed: ' + parameter)
        bindings[parameter] = _path(texture)
    if set(bindings) != {'Sand_01_Normal', 'Sand_02_Normal'}:
        raise RuntimeError('Both retained corrected normal dependencies are required.')
    return bindings


def evaluate_paint_samples(samples, coverage):
    """Pure readiness check. Zero/failure is pending, never proof of empty paint.

    Four weight-blended targets sum to one, with quantization tolerance. The
    existing Ground weight already contains road/pad and slope exclusions;
    multiplying exclusions a second time would change the geographic contract.
    """
    roles = {role: {'nonzero_samples': 0, 'max_weight': 0.0, 'best_sample': None}
             for role in TARGETS}
    failures, pending, normalized = [], [], 0
    known_ids, known_passed = set(), {'RoadBed': [], 'BuildingPad': []}
    for sample in samples:
        values = {role: float(sample['weights'][layer]) for role, layer in TARGETS.items()}
        name = sample['id']
        expected = sample.get('expected_role')
        if expected:
            xyz = sample.get('world_location_cm', [])
            minimum = float(sample.get('minimum_weight', .8))
            if (not isinstance(name, str) or not name.strip() or name in known_ids
                    or expected not in TARGETS or len(xyz) != 3
                    or not all(math.isfinite(float(v)) for v in xyz)
                    or not math.isfinite(minimum) or not .8 <= minimum <= 1):
                failures.append({'id': name, 'reason': 'invalid_or_duplicate_known_probe'})
                continue
            known_ids.add(name)
        if any(not math.isfinite(v) or v < -WEIGHT_TOLERANCE or v > 1.0 + WEIGHT_TOLERANCE for v in values.values()):
            failures.append({'id': name, 'reason': 'invalid_weight'})
            continue
        total = sum(values.values())
        if total <= WEIGHT_TOLERANCE:
            pending.append(name)
            continue
        if abs(total - 1.0) > WEIGHT_TOLERANCE:
            failures.append({'id': name, 'reason': 'four_target_weights_not_normalized', 'sum': total})
            continue
        normalized += 1
        for role, value in values.items():
            if value > WEIGHT_TOLERANCE:
                roles[role]['nonzero_samples'] += 1
            if value > roles[role]['max_weight']:
                roles[role]['max_weight'] = value
                roles[role]['best_sample'] = sample
        if expected:
            if values[expected] < minimum:
                failures.append({'id': name, 'reason': 'known_location_role_mismatch',
                                 'expected_role': expected, 'actual_weight': values[expected], 'minimum': minimum})
            elif expected in known_passed:
                known_passed[expected].append(name)
        # Applies to partial slopes/boundaries as well as full exclusions.
        exclusion = sum(values[role] for role in ('Steep', 'RoadBed', 'BuildingPad'))
        density_weight = values['Ground'] * coverage
        if density_weight > max(0.0, 1.0 - exclusion) * coverage + WEIGHT_TOLERANCE:
            failures.append({'id': name, 'reason': 'grass_exclusion_contract'})
    ground_observed = roles['Ground']['nonzero_samples'] > 0
    missing_roles = [role for role, v in roles.items() if not v['nonzero_samples']]
    known_exclusions_passed = all(known_passed.values())
    return {'paint_ready': bool(ground_observed and normalized and not pending and not failures and not missing_roles and known_exclusions_passed),
            'ground_paint_weight_observed': ground_observed,
            'normalized_sample_count': normalized, 'pending_sample_ids': pending,
            'paint_contract_failures': failures, 'role_weight_readback': roles,
            'weight_tolerance': WEIGHT_TOLERANCE,
            'unobserved_roles': missing_roles,
            'known_exclusion_probe_ids_passed': known_passed,
            'known_exclusion_probes_passed': known_exclusions_passed,
            'missing_known_exclusion_roles': [role for role, ids in known_passed.items() if not ids],
            'all_four_targets_observed': all(v['nonzero_samples'] for v in roles.values()),
            'grass_exclusions': 'Ground = (1-Steep) * (1-Pad) * (1-RoadBed_before_pad_mask)',
            'geographic_land_cover_semantics_verified': False}


def _permitted(profile, config):
    # Re-read actual canonical enabled rows; never write the table or its flags.
    table = unreal.load_asset(profile['table'])
    rows = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    area = profile['map'].split('/')[4]
    permitted = set()
    for row in rows:
        enabled = str(row.get('RunEligible', '')).lower() in ('1', 'true', '1.0')
        areas = str(row.get('AllowedAreas', '')).split('|')
        if enabled and area in areas and row.get('Role') == 'understory':
            permitted.add(str(row['ObjectPath']))
    paths = config['mesh_paths']
    if not paths or not set(paths).issubset(permitted):
        raise RuntimeError('Landscape Grass requires existing enabled understory rows for this area: ' + str(sorted(set(paths) - permitted)))
    return paths


def prepare(run):
    """Idempotently bind grass before official generation; save exact shared assets."""
    run.guard()
    config = run.p.get('landscape_grass')
    if not config or not config.get('enabled'):
        return {'enabled': False, 'provider': 'retained_HDA_native_instances'}
    config = _config(run.p)
    paths = _permitted(run.p, config)
    instance = unreal.load_asset(config['base_material_instance'])
    if not isinstance(instance, unreal.MaterialInstanceConstant):
        raise RuntimeError('Retained Natural material instance is unavailable.')
    material = instance.get_editor_property('parent')
    if _path(material) != MASTER or not isinstance(material, unreal.Material):
        raise RuntimeError('Landscape Grass requires the retained owned Natural master material.')
    type_path = GRASS_TYPE
    grass = unreal.load_asset(type_path)
    changed = False
    if grass is None:
        grass = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            type_path.rsplit('/', 1)[1], type_path.rsplit('/', 1)[0],
            unreal.LandscapeGrassType, unreal.LandscapeGrassTypeFactory())
        if grass is None:
            raise RuntimeError('Native Landscape Grass Type creation failed.')
        unreal.EditorAssetLibrary.set_metadata_tag(grass, 'GeoCityOwner', OWNER)
        changed = True
    elif not isinstance(grass, unreal.LandscapeGrassType) or str(unreal.EditorAssetLibrary.get_metadata_tag(grass, 'GeoCityOwner')) != OWNER:
        raise RuntimeError('Existing Grass Type is not project-owned.')
    spec = _expected_varieties(run.p, config)
    spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode('utf-8')).hexdigest()
    if _read_varieties(grass) != spec:
        varieties = []
        for path in paths:
            mesh = unreal.load_asset(path)
            if not isinstance(mesh, unreal.StaticMesh):
                raise RuntimeError('Permitted grass mesh is unavailable: ' + path)
            variety = unreal.GrassVariety()
            variety.set_editor_property('grass_mesh', mesh)
            variety.set_editor_property('grass_density', unreal.PerPlatformFloat(default=float(config['density_per_10m2']) / len(paths)))
            variety.set_editor_property('grass_density_quality', unreal.PerQualityLevelFloat(default=float(config['density_per_10m2']) / len(paths)))
            variety.set_editor_property('start_cull_distance', unreal.PerPlatformInt(default=10000))
            variety.set_editor_property('end_cull_distance', unreal.PerPlatformInt(default=20000))
            variety.set_editor_property('start_cull_distance_quality', unreal.PerQualityLevelInt(default=10000))
            variety.set_editor_property('end_cull_distance_quality', unreal.PerQualityLevelInt(default=20000))
            variety.set_editor_property('use_grid', True)
            variety.set_editor_property('placement_jitter', 1.0)
            variety.set_editor_property('random_rotation', True)
            variety.set_editor_property('align_to_surface', True)
            variety.set_editor_property('scaling', unreal.GrassScaling.UNIFORM)
            variety.set_editor_property('weight_attenuates_max_scale', False)
            variety.set_editor_property('allowed_density_range', unreal.FloatInterval(min=0.0, max=1.0))
            variety.set_editor_property('min_lod', -1)
            variety.set_editor_property('scale_x', unreal.FloatInterval(min=1.0, max=1.0))
            variety.set_editor_property('scale_y', unreal.FloatInterval(min=1.0, max=1.0))
            variety.set_editor_property('scale_z', unreal.FloatInterval(min=1.0, max=1.0))
            overrides = run.p.get('instance_materials', {}).get(path, [])
            if overrides:
                materials = [unreal.load_asset(p) for p in overrides]
                if any(not isinstance(m, unreal.MaterialInterface) for m in materials):
                    raise RuntimeError('A retained grass material override is unavailable: ' + path)
                variety.set_editor_property('override_materials', materials)
            varieties.append(variety)
        grass.set_editor_property('grass_varieties', varieties)
        unreal.EditorAssetLibrary.set_metadata_tag(grass, 'GeoCityGrassSpec', spec_hash)
        changed = True
    if _read_varieties(grass) != spec:
        raise RuntimeError('Native Grass variety readback differs from the retained settings.')
    nodes = _nodes(material)
    owned = [n for n in nodes if str(n.get_editor_property('desc')).startswith(OWNER)]
    output = [n for n in owned if isinstance(n, unreal.MaterialExpressionLandscapeGrassOutput)]
    if not output:
        if owned:
            raise RuntimeError('Partial owned Grass graph requires reconciliation before creating nodes.')
        if any(isinstance(n, unreal.MaterialExpressionLandscapeGrassOutput) for n in nodes):
            raise RuntimeError('An unrelated native Grass output needs explicit reconciliation.')
        created = []

        def node(cls, label, y):
            obj = LIB.create_material_expression(material, cls, -2500, y)
            if obj is None:
                raise RuntimeError('Cannot create native Grass material expression: ' + label)
            obj.set_editor_property('desc', OWNER + ':' + label)
            created.append(obj)
            return obj

        try:
            sample = node(unreal.MaterialExpressionLandscapeLayerSample, 'Ground', 17000)
            sample.set_editor_property('parameter_name', unreal.Name(config['ground_layer']))
            # The current HDA Ground target is explicitly masked by RoadBed and
            # BuildingPad. Steep uses its own target. Reuse those actual weights.
            density = node(unreal.MaterialExpressionScalarParameter, 'Density', 17200)
            density.set_editor_property('parameter_name', unreal.Name('GeoCity_GrassCoverage'))
            # Other areas inherit zero. Only this area's retained child MI
            # enables the authorized distribution, avoiding cross-area scope.
            density.set_editor_property('default_value', 0.0)
            multiply = node(unreal.MaterialExpressionMultiply, 'GroundDensity', 17100)
            if not LIB.connect_material_expressions(sample, '', multiply, 'A') or not LIB.connect_material_expressions(density, '', multiply, 'B'):
                raise RuntimeError('Cannot connect geographic Ground and coverage to native Grass.')
            out = node(unreal.MaterialExpressionLandscapeGrassOutput, 'Output', 17400)
            inp = unreal.GrassInput()
            inp.set_editor_property('name', unreal.Name('GeoCityGroundGrass'))
            inp.set_editor_property('grass_type', grass)
            out.set_editor_property('grass_types', [inp])
            if not LIB.connect_material_expressions(multiply, '', out, 'GeoCityGroundGrass'):
                raise RuntimeError('Cannot connect native Grass output.')
            output = [out]
            changed = True
        except Exception:
            for obj in reversed(created):
                LIB.delete_material_expression(material, obj)
            raise
    if len(output) != 1 or sum(isinstance(n, unreal.MaterialExpressionLandscapeGrassOutput) for n in _nodes(material)) != 1:
        raise RuntimeError('Ambiguous owned Landscape Grass output.')
    if sum(str(n.get_editor_property('desc')).startswith(OWNER) for n in _nodes(material)) != 4:
        raise RuntimeError('Native Grass graph must contain exactly four owned nodes.')
    inputs = list(output[0].get_editor_property('grass_types'))
    if len(inputs) != 1 or inputs[0].get_editor_property('grass_type') != grass or str(inputs[0].get_editor_property('name')) != 'GeoCityGroundGrass':
        raise RuntimeError('Landscape Grass Type binding differs from the ordinary profile.')
    samples = [n for n in _nodes(material) if str(n.get_editor_property('desc')) == OWNER + ':Ground']
    if len(samples) != 1 or str(samples[0].get_editor_property('parameter_name')) != config['ground_layer']:
        raise RuntimeError('Landscape Grass geographic layer binding differs.')
    # The graph-input inspection helpers require an active material editor.
    # Reassert only the three owned edges with the supported connection API.
    # Existing node counts/labels/types are validated first; no duplicate graph.
    owned_by_label = {}
    for label, cls in (('Ground', unreal.MaterialExpressionLandscapeLayerSample),
                       ('Density', unreal.MaterialExpressionScalarParameter),
                       ('GroundDensity', unreal.MaterialExpressionMultiply),
                       ('Output', unreal.MaterialExpressionLandscapeGrassOutput)):
        matches = [n for n in _nodes(material) if str(n.get_editor_property('desc')) == OWNER + ':' + label]
        if len(matches) != 1 or not isinstance(matches[0], cls):
            raise RuntimeError('Native Grass graph has missing/ambiguous owned node: ' + label)
        owned_by_label[label] = matches[0]
    density = owned_by_label['Density']
    if str(density.get_editor_property('parameter_name')) != 'GeoCity_GrassCoverage' or float(density.get_editor_property('default_value')) != 0.0:
        raise RuntimeError('Native Grass coverage parameter/default differs; unconfigured areas must inherit zero.')
    for source, dest, pin in (('Ground', 'GroundDensity', 'A'), ('Density', 'GroundDensity', 'B'),
                              ('GroundDensity', 'Output', 'GeoCityGroundGrass')):
        if not LIB.connect_material_expressions(owned_by_label[source], '', owned_by_label[dest], pin):
            raise RuntimeError('Cannot bind retained native Grass graph edge: ' + source + ' -> ' + dest)
    changed = True
    if changed:
        LIB.recompile_material(material)
        if not unreal.EditorLoadingAndSavingUtils.save_packages([grass.get_outermost(), material.get_outermost()], True):
            raise RuntimeError('Named Grass Type/master material save failed.')
    child_path = run.p['root'] + '/Materials/MI_GeoCityGround'
    child = unreal.load_asset(child_path)
    if child is None:
        child = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'MI_GeoCityGround', child_path.rsplit('/', 1)[0],
            unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if child is None:
            raise RuntimeError('Cannot create the retained area ground material.')
        unreal.EditorAssetLibrary.set_metadata_tag(child, 'GeoCityOwner', OWNER)
    elif not isinstance(child, unreal.MaterialInstanceConstant) or str(unreal.EditorAssetLibrary.get_metadata_tag(child, 'GeoCityOwner')) != OWNER:
        raise RuntimeError('Retained area ground material has another owner.')
    LIB.set_material_instance_parent(child, instance)
    LIB.update_material_instance(child)
    if child.get_editor_property('parent') != instance:
        raise RuntimeError('Area ground material parent readback differs.')
    texture_bindings = _verify_textures(run.p, child)
    parameter = 'GeoCity_GrassCoverage'
    if parameter not in [str(name) for name in LIB.get_scalar_parameter_names(child)]:
        raise RuntimeError('Native Grass coverage parameter is unavailable on the area material.')
    requested = float(config['coverage'])
    # Installed 5.8 returned False while applying this value. Require actual
    # parameter presence and readback, rather than treating that flag as output.
    setter_result = LIB.set_material_instance_scalar_parameter_value(child, parameter, requested)
    LIB.update_material_instance(child)
    applied = LIB.get_material_instance_scalar_parameter_value(child, parameter)
    if not math.isfinite(applied) or abs(applied - requested) >= .0001:
        raise RuntimeError('Native Grass coverage parameter readback differs: requested=%s actual=%s setter=%s' % (requested, applied, setter_result))
    if not unreal.EditorLoadingAndSavingUtils.save_packages([child.get_outermost()], True):
        raise RuntimeError('Named area ground material save failed.')
    run.p['landscape_material'] = _path(child)
    return {'enabled': True, 'provider': 'native_LandscapeGrassOutput', 'grass_type': _path(grass),
            'material': _path(material), 'area_material': _path(child), 'mesh_paths': paths, 'ground_layer': config['ground_layer'],
            'coverage': config['coverage'], 'density_per_10m2': config['density_per_10m2'],
            'coverage_setter_result': setter_result, 'coverage_readback': applied,
            'varieties_readback': _read_varieties(grass), 'grass_spec_sha256': spec_hash,
            'enable_density_scaling': bool(grass.get_editor_property('enable_density_scaling')),
            'graph_owned_edges_reasserted': 3, 'graph_node_count': len(owned_by_label),
            'corrected_normal_bindings': texture_bindings,
            'named_area_packages': [_path(child.get_outermost())],
            'named_shared_packages': [_path(grass.get_outermost()), _path(material.get_outermost())],
            'bank_eligibility_changed': False, 'distribution': 'generated_on_geographic_open_Ground; not surveyed vegetation'}


def is_native_grass(actor, component, profile):
    return (bool(profile.get('landscape_grass', {}).get('enabled'))
            and isinstance(actor, unreal.LandscapeProxy)
            and isinstance(component, unreal.HierarchicalInstancedStaticMeshComponent)
            and _path(component.get_editor_property('static_mesh')) in PERMITTED_MESHES)


def verify_landscape(run, landscape, receipt):
    """Read generated or baked target; caller retries paint_ready after Bake.

    Native graph/type bindings, paint readiness, current grass cache, and Lit
    appearance are deliberately separate. This never moves a camera or cooks.
    """
    run.guard()
    config = _config(run.p)
    if _path(landscape.get_editor_property('landscape_material')) != run.p['landscape_material']:
        raise RuntimeError('Geographic Landscape material binding is missing.')
    material = unreal.load_asset(run.p['landscape_material'])
    if _path(material.get_editor_property('parent')) != BASE:
        raise RuntimeError('Geographic area material lost the retained Natural parent.')
    applied = LIB.get_material_instance_scalar_parameter_value(material, 'GeoCity_GrassCoverage')
    if not math.isfinite(applied) or abs(applied - float(config['coverage'])) >= .0001:
        raise RuntimeError('Native Grass coverage binding is missing.')
    textures = _verify_textures(run.p, material)
    grass_type = unreal.load_asset(GRASS_TYPE)
    if grass_type is None or _read_varieties(grass_type) != _expected_varieties(run.p, config):
        raise RuntimeError('Native Grass Type settings changed after preparation.')
    layers = sorted(str(name) for name in landscape.get_target_layer_names())
    expected = list(TARGETS.values())
    if set(layers) != set(expected):
        raise RuntimeError('Four geographic paint target bindings differ: ' + str(layers))
    samples = []
    components = list(landscape.get_components_by_class(unreal.LandscapeComponent))
    bounds = [(c, unreal.SystemLibrary.get_component_bounds(c)) for c in components]

    def sample_at(component, location, identity, probe=None):
        sample = {'id': identity, 'component': _path(component),
                  'world_location_cm': [location.x, location.y, location.z],
                  'weights': {name: float(component.editor_get_paint_layer_weight_by_name_at_location(location, name))
                              for name in expected}}
        if probe:
            sample.update({k: probe[k] for k in ('expected_role', 'minimum_weight') if k in probe})
        samples.append(sample)

    for component, (origin, extent, radius) in bounds:
        for x in (-.8, -.4, 0.0, .4, .8):
            for y in (-.8, -.4, 0.0, .4, .8):
                location = unreal.Vector(origin.x + x * extent.x, origin.y + y * extent.y, origin.z)
                sample_at(component, location, '%s:%s:%s' % (_path(component), x, y))
    # Manager-owned known locations are world coordinates from retained source
    # receipts, not inferred from whichever paint value happens to be nonzero.
    probes = config.get('paint_probe_locations', [])
    for probe in probes:
        if probe.get('expected_role') not in TARGETS:
            raise RuntimeError('Unknown geographic probe role: ' + str(probe))
        xyz = probe['world_location_cm']
        if len(xyz) != 3 or not all(math.isfinite(float(v)) for v in xyz):
            raise RuntimeError('Invalid geographic paint probe location.')
        location = unreal.Vector(*xyz)
        containing = [c for c, (origin, extent, radius) in bounds
                      if abs(location.x-origin.x) <= extent.x and abs(location.y-origin.y) <= extent.y]
        if not containing:
            raise RuntimeError('Known paint probe is outside the generated Landscape: ' + probe['id'])
        sample_at(containing[0], location, probe['id'], probe)
    paint = evaluate_paint_samples(samples, float(config['coverage']))
    grass = []
    for component in landscape.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        mesh = _path(component.get_editor_property('static_mesh'))
        if mesh not in config['mesh_paths']:
            raise RuntimeError('Unexpected automatic grass mesh on the geographic Landscape: ' + str(mesh))
        grass.append({'component': _path(component), 'mesh': mesh, 'instances': component.get_instance_count()})
    weights = {layer: {'nonzero_samples': paint['role_weight_readback'][role]['nonzero_samples'],
                       'max_weight': paint['role_weight_readback'][role]['max_weight']}
               for role, layer in TARGETS.items()}
    count = sum(v['instances'] for v in grass)
    return dict(paint, material=run.p['landscape_material'], layer_names=layers,
                required_layer_names=expected, native_grass_components=grass,
                paint_weight_sample_count=len(samples), paint_weight_readback=weights,
                known_location_samples=[s for s in samples if 'expected_role' in s],
                paint_samples_are_partial_coverage=True, native_grass_instance_count=count,
                grass_count_is_current_loaded_cache=True, grass_cache_output_observed=count > 0,
                grass_cache_is_viewer_and_quality_dependent=True,
                nearby_grass_cache_verified=False, visible_lit_grass_verified=False,
                corrected_normal_bindings=textures,
                geographic_palette_receipt=receipt.get('surface_palette_choices', receipt.get('surface_palette', {})))


def inspect_near_view(run, landscape, view_location_cm, radius_cm=5000.0):
    """Task4 readback at a recorded near Lit view, after ordinary paint readiness.

    Inspect existing instance positions, without changing quality or forcing a
    cache. A nearby cached instance still needs actual Lit pixel review.
    """
    run.guard()
    if len(view_location_cm) != 3 or not all(math.isfinite(float(v)) for v in view_location_cm):
        raise RuntimeError('A finite recorded view location is required.')
    if not 0.0 < float(radius_cm) <= 10000.0:
        raise RuntimeError('Near-view radius must be within the retained start cull distance.')
    result = verify_landscape(run, landscape, {})
    near, seen = [], set()
    for component in landscape.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        for index in range(component.get_instance_count()):
            transform = component.get_instance_transform(index, world_space=True)
            if transform is None:
                raise RuntimeError('Grass instance transform readback failed.')
            location = transform.translation
            xyz = [location.x, location.y, location.z]
            distance = math.sqrt(sum((a-b)**2 for a, b in zip(xyz, view_location_cm)))
            if distance <= radius_cm:
                mesh = _path(component.get_editor_property('static_mesh'))
                near.append({'mesh': mesh, 'component': _path(component), 'instance': index,
                             'world_location_cm': xyz, 'view_distance_cm': distance})
                seen.add(mesh)
                break  # One concrete nearby instance per loaded component suffices.
    result.update(view_location_cm=list(view_location_cm), near_radius_cm=radius_cm,
                  nearby_grass_instances=near, nearby_grass_meshes=sorted(seen),
                  nearby_grass_cache_verified=bool(near), visible_lit_grass_verified=False)
    return result


# Staged append to geocity_landscape_workflow.py. Not imported by Unreal.
# Default/Gaza entry points delegate to the exact reviewed implementation.
_GEOMETRIC_PREPARE = prepare
_GEOMETRIC_VERIFY = verify_landscape
_GEOMETRIC_NEAR_VIEW = inspect_near_view
SEMANTIC_OWNER = 'GeoCity_SemanticLandscapeGrass_v1'
SEMANTIC_CLASSES = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100)
SEMANTIC_MASK = 'GC_GrassEligible'
SEMANTIC_WATER = 'GC_WaterCandidate'
SEMANTIC_RGB = ('PB_Custom_Ground_R', 'PB_Custom_Ground_G', 'PB_Custom_Ground_B')


def _semantic_digest(contract):
    return hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('utf-8')).hexdigest()


def _semantic_preparation_contract(profile):
    """v2 pre-Cook support contract; counts/probes come only from actual output."""
    envelope = profile['landscape_semantics']
    if envelope.get('schema') == 'environmentpipeline.semantic_landscape_profile.v1':
        return _semantic_contract(profile)
    if envelope.get('schema') != 'environmentpipeline.semantic_landscape_profile.v2':
        raise RuntimeError('Unknown semantic profile schema.')
    from pathlib import Path
    path = Path(profile['source'])
    package = json.loads(path.read_bytes())
    policy = json.loads((path.parent/package['semantic_consumer_contract']['path']).read_bytes())
    area = profile['map'].split('/')[4]
    if area != 'Iran_38196167_46086167_4km' or policy['area_id'] != area:
        raise RuntimeError('Semantic profile is outside the bounded Iran assignment.')
    config = profile['landscape_grass']
    if policy['grass']['provider'] != 'native_landscape_grass':
        raise RuntimeError('This reviewed Iran consumer supports only the pinned native_landscape_grass policy; another provider needs its own reviewed binding contract.')
    if set(policy['class_material_targets']) != {str(c) for c in SEMANTIC_CLASSES} or any(not isinstance(n,str) or not n for n in policy['class_material_targets'].values()):
        raise RuntimeError('All source classes require explicit existing material targets.')
    if (bool(config.get('enabled')) != (policy['grass']['provider'] == 'native_landscape_grass')
            or config['base_material_instance'] != BASE or config['ground_layer'] != SEMANTIC_MASK
            or tuple(config['mesh_paths']) != PERMITTED_MESHES):
        raise RuntimeError('Semantic provider/material/Grass configuration differs.')
    for key, high in (('coverage',1), ('density_per_10m2',1000)):
        value = float(config[key])
        if not math.isfinite(value) or not 0 < value <= high: raise RuntimeError('Invalid semantic '+key)
    roles = {'RoadBed':'Dirt_Path', 'BuildingPad':'Sand_Path', 'Steep':'Sand_02'}
    if any(profile.get('surface_choices',{}).get(k) != v for k,v in CHOICES.items()):
        raise RuntimeError('Semantic geometric target choices differ from the retained route.')
    layers = {n:{'kind':'weight','state':'potential'} for n in set(policy['class_material_targets'].values()).union(roles.values())}
    layers.update({n:{'kind':'mask','state':'potential'} for n in (SEMANTIC_MASK,SEMANTIC_WATER)})
    layers.update({n:{'kind':'constant','state':'potential','value':v} for n,v in zip(SEMANTIC_RGB,policy['water']['linear_rgb'])})
    contract = {'schema':'environmentpipeline.semantic_landscape_contract.v1','area_id':area,
                'source_package_sha256':envelope['source_package_sha256'],
                'class_grid_sha256':envelope['class_grid_sha256'],'policy_sha256':envelope['consumer_contract_sha256'],
                'coordinate_frame':'houdini_x_east_y_up_z_south_to_unreal_cm_x_z_y',
                'coverage_scope':'emitted_landscape_including_border','vegetation_provider':policy['grass']['provider'],
                'grass_layer':SEMANTIC_MASK,'grass_allowed_classes':[10,20,30], 'water_mode':'classification_surface',
                'class_targets':policy['class_material_targets'],'role_layers':roles,'layers':layers}
    _semantic_source_identity(profile, contract)
    return contract


def _semantic_verified_output_contract(profile, receipt):
    """No invented pre-Cook counts. Consume the source owner's actual HDA detail."""
    if profile['landscape_semantics'].get('schema') == 'environmentpipeline.semantic_landscape_profile.v1':
        return _semantic_contract(profile)
    preparation = _semantic_preparation_contract(profile)
    raw = receipt.get('semantic_surface_contract')
    if not isinstance(raw, dict):
        raise RuntimeError('Actual source-derived semantic_surface_contract output is missing.')
    contract = json.loads(json.dumps(raw, allow_nan=False))
    if receipt.get('semantic_surface_contract_sha256') != _semantic_digest(contract):
        raise RuntimeError('HDA semantic contract canonical hash differs.')
    for key in ('schema','area_id','source_package_sha256','class_grid_sha256','policy_sha256','coordinate_frame',
                'coverage_scope','vegetation_provider','grass_layer','grass_allowed_classes','water_mode','class_targets','role_layers'):
        if contract.get(key) != preparation[key]: raise RuntimeError('HDA semantic identity/route differs: '+key)
    # Producer probes use HDA X=east,Y=up,Z=south. Conversion is fixed and the
    # actual actor identity transform is separately checked before any query.
    for probe in contract['probes']:
        p = probe.get('hda_location_m', [])
        if len(p) != 3 or not all(math.isfinite(float(v)) for v in p):
            raise RuntimeError('Source-derived HDA probe position is required.')
        converted = [100*p[0],100*p[2],100*p[1]]
        if 'world_location_cm' in probe:
            world = probe['world_location_cm']
            if len(world) != 3 or not all(math.isfinite(float(v)) for v in world) or any(abs(a-b)>.0001 for a,b in zip(world,converted)):
                raise RuntimeError('Source HDA/world probe transform disagrees.')
        probe['world_location_cm'] = converted
        probe['expected_weights'] = {n:([v,v] if isinstance(v,(int,float)) else v) for n,v in probe['expected_weights'].items()}
    # Reuse strict count/zero/absent/probe validation without modifying profiles.
    derived = dict(profile, painted_layer_names=[n for n,v in contract['layers'].items() if v['state']!='absent'])
    derived['landscape_semantics'] = {'schema':'environmentpipeline.semantic_landscape_profile.v1',
                                    'contract':contract,'contract_sha256':_semantic_digest(contract)}
    _semantic_contract(derived)
    return contract


def _semantic_actor_frame(run):
    actor = run.wrapper.get_houdini_asset_actor()
    location, rotation, scale = actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d()
    values = [location.x,location.y,location.z,rotation.pitch,rotation.yaw,rotation.roll,scale.x,scale.y,scale.z]
    if not all(math.isfinite(float(v)) for v in values) or any(abs(v)>.0001 for v in values[:6]) or any(abs(v-1)>.000001 for v in values[6:]):
        raise RuntimeError('Source-local semantic probes require the reviewed identity HDA actor transform.')
    return {'location_cm':values[:3],'rotation_degrees':values[3:6],'scale':values[6:]}


def _semantic_contract(profile):
    envelope = profile['landscape_semantics']
    contract = envelope['contract']
    if (envelope.get('schema') != 'environmentpipeline.semantic_landscape_profile.v1'
            or contract.get('schema') != 'environmentpipeline.semantic_landscape_contract.v1'
            or envelope.get('contract_sha256') != _semantic_digest(contract)):
        raise RuntimeError('Semantic Landscape contract schema/hash differs.')
    area = profile['map'].split('/')[4]
    if area != 'Iran_38196167_46086167_4km' or contract.get('area_id') != area:
        raise RuntimeError('This bounded semantic consumer is scoped to the reviewed Iran area.')
    for key in ('source_package_sha256', 'class_grid_sha256', 'policy_sha256'):
        value = contract.get(key, '')
        if len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise RuntimeError('Missing semantic source hash: ' + key)
    if (contract.get('coordinate_frame') != 'houdini_x_east_y_up_z_south_to_unreal_cm_x_z_y'
            or contract.get('coverage_scope') != 'emitted_landscape_including_border'
            or contract.get('water_mode') != 'classification_surface'
            or contract.get('grass_layer') != SEMANTIC_MASK
            or contract.get('grass_allowed_classes') != [10, 20, 30]):
        raise RuntimeError('Unsupported semantic frame/scope/water/Grass contract.')
    provider = contract.get('vegetation_provider')
    if provider != 'native_landscape_grass':
        raise RuntimeError('This reviewed semantic consumer requires the pinned native_landscape_grass provider.')
    config = profile.get('landscape_grass', {})
    if bool(config.get('enabled')) != (provider == 'native_landscape_grass'):
        raise RuntimeError('Semantic Grass enablement/provider disagree.')
    if config.get('base_material_instance') != BASE or config.get('ground_layer') != SEMANTIC_MASK:
        raise RuntimeError('Semantic Grass must retain Natural dependencies and read GC_GrassEligible.')
    if tuple(config.get('mesh_paths', [])) != PERMITTED_MESHES:
        raise RuntimeError('Semantic consumer does not expand permitted Grass candidates.')
    for key, maximum in (('coverage', 1.0), ('density_per_10m2', 1000.0)):
        value = float(config[key])
        if not math.isfinite(value) or not 0 < value <= maximum:
            raise RuntimeError('Invalid semantic Grass density/coverage.')
    layers, counts, targets = contract['layers'], contract['class_counts'], contract['class_targets']
    if set(counts) != {str(c) for c in SEMANTIC_CLASSES} or set(targets) != set(counts):
        raise RuntimeError('All semantic classes need explicit counts and target mappings.')
    if any(type(v) is not int or v < 0 for v in counts.values()) or not sum(counts.values()):
        raise RuntimeError('Invalid emitted-grid class counts.')
    if targets['80'] != 'PB_Custom_Ground':
        raise RuntimeError('Class80 requires the retained classification-colour branch.')
    if set(contract['role_layers']) != {'RoadBed', 'BuildingPad', 'Steep'}:
        raise RuntimeError('All geometric exclusion roles must be declared, including zero roles.')
    if len(set(contract['role_layers'].values())) != 3:
        raise RuntimeError('Geographic exclusion roles require distinct targets.')
    if not set(targets.values()).union(contract['role_layers'].values()).issubset(layers):
        raise RuntimeError('Each mapped role/class must declare its layer state.')
    present, painted = set(), set()
    for name, item in layers.items():
        kind, state, count = item['kind'], item['state'], item['nonzero_sample_count']
        if kind not in ('weight', 'mask', 'constant') or state not in ('painted', 'zero', 'absent'):
            raise RuntimeError('Invalid semantic layer kind/state: ' + name)
        if type(count) is not int or count < 0 or (state == 'painted') != (count > 0):
            raise RuntimeError('Semantic layer state/count disagree: ' + name)
        if kind == 'mask' and name not in (SEMANTIC_MASK, SEMANTIC_WATER):
            raise RuntimeError('Only explicit Grass eligibility and water-class diagnostic masks are supported.')
        if kind == 'constant':
            value = float(item['value'])
            if name not in SEMANTIC_RGB or not math.isfinite(value) or not 0 <= value <= 1:
                raise RuntimeError('Invalid nonweight classification colour channel.')
            if state != 'absent' and (state == 'painted') != (value > 0):
                raise RuntimeError('Constant channel value/state disagree.')
        if state != 'absent': present.add(name)
        if state == 'painted': painted.add(name)
    if layers.get(SEMANTIC_MASK, {}).get('kind') != 'mask' or SEMANTIC_MASK not in present:
        raise RuntimeError('Emit GC_GrassEligible as a nonweight layer, including explicit zero.')
    if layers.get(SEMANTIC_WATER, {}).get('kind') != 'mask' or SEMANTIC_WATER not in present:
        raise RuntimeError('Emit GC_WaterCandidate as a nonweight diagnostic, including explicit zero.')
    if any(layers[n]['kind'] != 'weight' for n in set(targets.values()).union(contract['role_layers'].values())):
        raise RuntimeError('Surface targets must be weight blended; auxiliary channels must not enter the sum.')
    if 'PB_Custom_Ground' in present and not set(SEMANTIC_RGB).issubset(present):
        raise RuntimeError('Classification surface needs all three RGB channels.')
    if not any(layers[n]['kind'] == 'weight' for n in painted):
        raise RuntimeError('No nonzero semantic surface was declared.')
    if set(profile.get('painted_layer_names', [])) != present:
        raise RuntimeError('Profile target names differ from the exact emitted semantic contract.')
    probes = contract['probes']
    if not probes or len({p['id'] for p in probes}) != len(probes):
        raise RuntimeError('Distinct source-derived semantic probes are required.')
    tags, positive_layers = set(), set()
    for probe in probes:
        xyz = probe['world_location_cm']
        if not isinstance(probe['id'], str) or not probe['id'].strip() or len(xyz) != 3 or not all(math.isfinite(float(v)) for v in xyz):
            raise RuntimeError('Invalid source semantic probe identity/location.')
        weights = probe['expected_weights']
        if set(weights) != present or not probe['tags']:
            raise RuntimeError('Tagged source probes must specify every emitted semantic weight.')
        for name, bounds in weights.items():
            if len(bounds) != 2 or not all(math.isfinite(float(v)) for v in bounds) or not 0 <= bounds[0] <= bounds[1] <= 1 or bounds[1]-bounds[0] > .02:
                raise RuntimeError('Invalid expected semantic weight interval.')
            if bounds[0] > WEIGHT_TOLERANCE: positive_layers.add(name)
        for tag in probe['tags']:
            if tag.startswith('class:'):
                code = int(tag.split(':')[1])
                if code not in SEMANTIC_CLASSES or probe.get('source_class_id') != code:
                    raise RuntimeError('Class probe tag and source class disagree.')
                if code not in (10, 20, 30) and weights.get(SEMANTIC_MASK) != [0, 0]:
                    raise RuntimeError('Excluded source classes need a known zero Grass probe.')
                if weights[SEMANTIC_WATER] != ([1, 1] if code == 80 else [0, 0]):
                    raise RuntimeError('Known class-cell interior probes must verify the raw water classification mask.')
            elif tag.startswith('role:'):
                role = tag.split(':')[1]
                if role not in contract['role_layers'] or contract['role_layers'][role] not in weights:
                    raise RuntimeError('Role probe must test its geographic target.')
                if SEMANTIC_MASK not in weights:
                    raise RuntimeError('Role probe must also test Grass exclusion/reduction.')
                if weights[contract['role_layers'][role]][0] <= WEIGHT_TOLERANCE:
                    raise RuntimeError('Known nonzero role probe needs a positive expected weight.')
            elif tag not in ('grass:positive', 'grass:excluded'):
                raise RuntimeError('Unsupported semantic probe tag.')
            elif tag == 'grass:positive' and weights[SEMANTIC_MASK][0] <= WEIGHT_TOLERANCE:
                raise RuntimeError('Positive Grass probe needs a positive expected mask.')
            elif tag == 'grass:excluded' and weights[SEMANTIC_MASK] != [0, 0]:
                raise RuntimeError('Excluded Grass probe needs an explicit zero expectation.')
            tags.add(tag)
    required = {'class:' + code for code, count in counts.items() if count}
    required.update('role:' + role for role, layer in contract['role_layers'].items() if layers[layer]['state'] == 'painted')
    if layers[SEMANTIC_MASK]['state'] == 'painted': required.add('grass:positive')
    if not required.issubset(tags) or not painted.issubset(positive_layers):
        raise RuntimeError('Every nonzero class/role/layer needs an explicit source probe; zero roles remain explicit.')
    return contract


def _semantic_source_identity(profile, contract):
    """Verify the semantic owner's v2 artifact bytes; never regenerate source."""
    from pathlib import Path
    package_path = Path(profile['source']).resolve()
    raw = package_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != contract['source_package_sha256']:
        raise RuntimeError('Active semantic source package does not match the reviewed consumer.')
    package = json.loads(raw)
    def read_reference(root, entry):
        path = (root / entry['path']).resolve()
        if not path.is_relative_to(root.resolve()): raise RuntimeError('Semantic source reference leaves its package.')
        data = path.read_bytes()
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise RuntimeError('Semantic source dependency bytes differ: ' + str(path))
        return path, data
    policy_path, policy_bytes = read_reference(package_path.parent, package['semantic_consumer_contract'])
    if hashlib.sha256(policy_bytes).hexdigest() != contract['policy_sha256']:
        raise RuntimeError('Reviewed semantic consumer policy hash differs.')
    policy = json.loads(policy_bytes)
    geography_path, geography_bytes = read_reference(package_path.parent, package['semantic_geography'])
    geography = json.loads(geography_bytes)
    grid_path, grid_bytes = read_reference(geography_path.parent, geography['class_grid'])
    if hashlib.sha256(grid_bytes).hexdigest() != contract['class_grid_sha256']:
        raise RuntimeError('Registered class grid differs from the native probe contract.')
    if (policy.get('schema') != 'environmentpipeline.semantic_consumer.v2'
            or policy['area_id'] != contract['area_id']
            or policy['semantic_manifest_sha256'] != package['semantic_geography']['sha256']
            or policy['class_material_targets'] != contract['class_targets']
            or policy['grass']['provider'] != contract['vegetation_provider']
            or policy['grass']['mask_layer'] != SEMANTIC_MASK
            or policy['grass']['class_ids'] != [10, 20, 30]):
        raise RuntimeError('Semantic owner policy and native consumer disagree.')
    if policy['geographic_role_sha256'] != {item['role']: item['sha256'] for item in package['files']}:
        raise RuntimeError('Semantic policy geographic source identities differ.')
    required_understory = 'suppress' if contract['vegetation_provider'] == 'native_landscape_grass' else 'retain'
    if policy['grass']['hda_understory_policy'] != required_understory:
        raise RuntimeError('Semantic provider and HDA understory policy disagree.')
    for key in ('coverage', 'density_per_10m2', 'mesh_paths'):
        if policy['grass'][key] != profile['landscape_grass'][key]:
            raise RuntimeError('Semantic owner Grass settings differ: ' + key)
    water = policy['water']
    if (water['mode'] != 'classification_surface' or water['classification_layer'] != SEMANTIC_WATER
            or water['paint_layer'] != 'PB_Custom_Ground' or water['physical_geometry_emitted'] is not False
            or water['water_level_m'] is not None or water['shoreline_is_surveyed'] is not False):
        raise RuntimeError('Unsupported physical-water claim or binding in classification contract.')
    for name, value in zip(SEMANTIC_RGB, water['linear_rgb']):
        # Producer stores the constant in float32 heightfield voxels.
        if name in contract['layers'] and contract['layers'][name]['state'] != 'absent' and abs(contract['layers'][name]['value']-value) > 1e-7:
            raise RuntimeError('Water classification RGB differs from semantic policy.')
    return {'source_package_sha256': contract['source_package_sha256'], 'policy_sha256': contract['policy_sha256'],
            'class_grid_sha256': contract['class_grid_sha256'], 'source_identity_verified': True}


def evaluate_semantic_samples(samples, contract):
    """Validate registered probes and normalize surface weights without auxiliaries."""
    layers = contract['layers']
    present = {n for n, v in layers.items() if v['state'] != 'absent'}
    weighted = {n for n in present if layers[n]['kind'] == 'weight'}
    probes = {p['id']: p for p in contract['probes']}
    failures, pending, passed, seen = [], [], [], set()
    observed = {n: {'max_weight': 0.0, 'nonzero_samples': 0, 'best_sample': None} for n in present}
    normalized = 0
    for sample in samples:
        name, values = sample['id'], sample['weights']
        if set(values) != present or any(not math.isfinite(float(v)) or not -WEIGHT_TOLERANCE <= float(v) <= 1 + WEIGHT_TOLERANCE for v in values.values()):
            failures.append({'id': name, 'reason': 'invalid_semantic_weights'})
            continue
        total = sum(values[n] for n in weighted)
        if total <= WEIGHT_TOLERANCE:
            pending.append(name)
            continue
        if abs(total - 1) > WEIGHT_TOLERANCE:
            failures.append({'id': name, 'reason': 'semantic_surface_not_normalized', 'sum': total})
            continue
        normalized += 1
        valid = True
        for layer in present:
            value, item = values[layer], layers[layer]
            if ((item['state'] == 'zero' and abs(value) > WEIGHT_TOLERANCE)
                    or (item['kind'] == 'constant' and abs(value-item['value']) > WEIGHT_TOLERANCE)):
                failures.append({'id': name, 'reason': 'zero_or_constant_layer_differs', 'layer': layer})
                valid = False
            observed[layer]['nonzero_samples'] += int(value > WEIGHT_TOLERANCE)
            if value > observed[layer]['max_weight']:
                observed[layer].update(max_weight=value, best_sample=sample)
        # Paint and native Grass share classes; the independent mask cannot
        # exceed eligible class surface weights or geographic exclusion capacity.
        eligible_layers = {contract['class_targets'][str(c)] for c in (10, 20, 30)}
        capacity = sum(values.get(n, 0) for n in eligible_layers)
        exclusion = sum(values.get(n, 0) for n in contract['role_layers'].values())
        if values[SEMANTIC_MASK] > min(capacity, max(0, 1-exclusion), max(0, 1-values[SEMANTIC_WATER])) + WEIGHT_TOLERANCE:
            failures.append({'id': name, 'reason': 'semantic_grass_exclusion'})
            valid = False
        if name in probes:
            probe = probes[name]
            xyz = sample.get('world_location_cm', [])
            if name in seen or len(xyz) != 3 or not all(math.isfinite(float(v)) for v in xyz) or any(abs(a-b) > .0001 for a, b in zip(xyz, probe['world_location_cm'])):
                failures.append({'id': name, 'reason': 'known_probe_identity_or_location_differs'})
                valid = False
            seen.add(name)
            for layer, (low, high) in probe['expected_weights'].items():
                if not low-WEIGHT_TOLERANCE <= values[layer] <= high+WEIGHT_TOLERANCE:
                    failures.append({'id': name, 'reason': 'known_semantic_weight_differs', 'layer': layer, 'actual': values[layer]})
                    valid = False
            if valid: passed.append(name)
    missing = sorted(set(probes)-set(passed))
    unobserved = [n for n in present if layers[n]['state'] == 'painted' and not observed[n]['nonzero_samples']]
    return {'paint_ready': bool(normalized and not missing and not failures and not pending and not unobserved),
            'paint_contract_failures': failures, 'pending_sample_ids': pending,
            'known_semantic_probe_ids_passed': passed, 'missing_known_semantic_probes': missing,
            'unobserved_semantic_layers': unobserved, 'paint_weight_readback': observed,
            'normalized_sample_count': normalized, 'weight_tolerance': WEIGHT_TOLERANCE,
            'explicit_zero_layers': sorted(n for n, v in layers.items() if v['state'] == 'zero'),
            'explicit_absent_layers': sorted(n for n, v in layers.items() if v['state'] == 'absent'),
            'grass_mask_expected_zero': layers[SEMANTIC_MASK]['state'] == 'zero',
            'ground_paint_weight_observed': bool(normalized),
            'classification_surface_only': True, 'surveyed_hydrology_verified': False,
            'geographic_precision_verified': False, 'visible_lit_grass_verified': False}


def _semantic_output_contract(receipt, contract):
    # v2 local probes are converted only after validating the producer's raw hash.
    expected_hash = _semantic_digest(receipt.get('semantic_surface_contract', contract))
    if (receipt.get('semantic_surface_contract_sha256') != expected_hash
            or receipt.get('semantic_surface_complete') is not True
            or receipt.get('semantic_grass_provider') != contract['vegetation_provider']):
        raise RuntimeError('Complete HDA semantic output does not match the pinned consumer contract.')
    nonweight = {n for n, item in contract['layers'].items() if item['state'] != 'absent' and item['kind'] != 'weight'}
    if set(receipt.get('semantic_nonweight_layers', [])) != nonweight:
        raise RuntimeError('Semantic auxiliary layers must be explicitly nonweight blended.')
    if not isinstance(receipt.get('nonbuilding_instances'), list):
        raise RuntimeError('Complete native instance readback is required for provider exclusivity.')
    if contract['vegetation_provider'] == 'native_landscape_grass':
        if receipt.get('semantic_hda_understory_suppressed') is not True or any(i.get('role') == 'understory' for i in receipt.get('nonbuilding_instances', [])):
            raise RuntimeError('Native Grass and HDA understory outputs are not exclusive.')


def _semantic_owned_asset(path, cls, factory=None, duplicate=None):
    asset = unreal.load_asset(path)
    if asset is None:
        if duplicate:
            asset = unreal.EditorAssetLibrary.duplicate_asset(duplicate, path)
        else:
            asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(path.rsplit('/', 1)[1], path.rsplit('/', 1)[0], cls, factory)
        if not isinstance(asset, cls):
            raise RuntimeError('Cannot create permanent semantic dependency: ' + path)
        unreal.EditorAssetLibrary.set_metadata_tag(asset, 'GeoCityOwner', SEMANTIC_OWNER)
    elif not isinstance(asset, cls) or str(unreal.EditorAssetLibrary.get_metadata_tag(asset, 'GeoCityOwner')) != SEMANTIC_OWNER:
        raise RuntimeError('Existing semantic dependency has another owner: ' + path)
    return asset


def _semantic_graph(material, grass):
    nodes = _nodes(material)
    owned = [n for n in nodes if str(n.get_editor_property('desc')).startswith(OWNER)]
    labels = ('Ground', 'Density', 'GroundDensity', 'Output')
    classes = (unreal.MaterialExpressionLandscapeLayerSample, unreal.MaterialExpressionScalarParameter,
               unreal.MaterialExpressionMultiply, unreal.MaterialExpressionLandscapeGrassOutput)
    if len(owned) != 4 or sum(isinstance(n, unreal.MaterialExpressionLandscapeGrassOutput) for n in nodes) != 1:
        raise RuntimeError('Copied semantic master must retain the exact four-node Grass graph.')
    result = {}
    for label, cls in zip(labels, classes):
        matches = [n for n in owned if str(n.get_editor_property('desc')) == OWNER+':'+label and isinstance(n, cls)]
        if len(matches) != 1: raise RuntimeError('Copied semantic Grass node differs: ' + label)
        result[label] = matches[0]
    result['Ground'].set_editor_property('parameter_name', unreal.Name(SEMANTIC_MASK))
    water_nodes = [n for n in nodes if str(n.get_editor_property('desc')) == SEMANTIC_OWNER+':WaterCandidate']
    if not water_nodes:
        water_sample = LIB.create_material_expression(material, unreal.MaterialExpressionLandscapeLayerSample, -2500, 17700)
        if water_sample is None: raise RuntimeError('Cannot declare the raw water diagnostic material target.')
        water_sample.set_editor_property('desc', SEMANTIC_OWNER+':WaterCandidate')
        water_sample.set_editor_property('parameter_name', unreal.Name(SEMANTIC_WATER))
    elif len(water_nodes) != 1 or not isinstance(water_nodes[0], unreal.MaterialExpressionLandscapeLayerSample) or str(water_nodes[0].get_editor_property('parameter_name')) != SEMANTIC_WATER:
        raise RuntimeError('Raw water diagnostic material target differs.')
    if str(result['Density'].get_editor_property('parameter_name')) != 'GeoCity_GrassCoverage' or float(result['Density'].get_editor_property('default_value')) != 0:
        raise RuntimeError('Copied semantic coverage parameter must inherit zero.')
    inputs = list(result['Output'].get_editor_property('grass_types'))
    if len(inputs) != 1 or str(inputs[0].get_editor_property('name')) != 'GeoCityGroundGrass':
        raise RuntimeError('Copied semantic Grass output differs.')
    inputs[0].set_editor_property('grass_type', grass)
    result['Output'].set_editor_property('grass_types', inputs)
    for a, b, pin in (('Ground', 'GroundDensity', 'A'), ('Density', 'GroundDensity', 'B'), ('GroundDensity', 'Output', 'GeoCityGroundGrass')):
        if not LIB.connect_material_expressions(result[a], '', result[b], pin):
            raise RuntimeError('Cannot bind semantic Grass edge: ' + a)


def _semantic_material_readback(profile, material, instance, contract):
    if instance.get_editor_property('parent') != material:
        raise RuntimeError('Semantic area material parent differs.')
    if 'GeoCity_GrassCoverage' not in [str(n) for n in LIB.get_scalar_parameter_names(instance)]:
        raise RuntimeError('Semantic Grass coverage parameter is missing from the compiled instance interface.')
    nodes = _nodes(material)
    blends = [n for n in nodes if isinstance(n, unreal.MaterialExpressionLandscapeLayerBlend)]
    weighted = {n for n, item in contract['layers'].items() if item['kind'] == 'weight' and item['state'] != 'absent'}
    if len(blends) != 3 or any(not weighted.issubset({str(v.get_editor_property('layer_name')) for v in n.get_editor_property('layers')}) for n in blends):
        raise RuntimeError('Retained colour/normal/roughness palette does not support all semantic targets.')
    for blend in blends:
        for entry in blend.get_editor_property('layers'):
            name = str(entry.get_editor_property('layer_name'))
            if name in weighted and entry.get_editor_property('blend_type') != unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND:
                raise RuntimeError('Semantic surface is not a weight-blend target: ' + name)
            if name in (SEMANTIC_MASK, SEMANTIC_WATER) or name in SEMANTIC_RGB:
                raise RuntimeError('Auxiliary masks/colour must not enter the surface weight blend.')
    sampled = {str(n.get_editor_property('parameter_name')) for n in nodes if isinstance(n, unreal.MaterialExpressionLandscapeLayerSample)}
    # GC_WaterCandidate is a raw diagnostic mask, not a surface/Grass input.
    # It must be imported and sampled on the Landscape, but must not repaint roads.
    nonweight = {n for n, v in contract['layers'].items() if v['kind'] != 'weight' and v['state'] != 'absent'}
    if not nonweight.issubset(sampled):
        raise RuntimeError('Semantic auxiliary mask/colour channel is not sampled by the material.')
    owned = [n for n in nodes if str(n.get_editor_property('desc')).startswith(OWNER)]
    ground = [n for n in owned if str(n.get_editor_property('desc')) == OWNER+':Ground']
    outputs = [n for n in nodes if isinstance(n, unreal.MaterialExpressionLandscapeGrassOutput)]
    if len(owned) != 4 or len(ground) != 1 or str(ground[0].get_editor_property('parameter_name')) != SEMANTIC_MASK or len(outputs) != 1:
        raise RuntimeError('Semantic Grass mask/output graph readback differs.')
    inputs = list(outputs[0].get_editor_property('grass_types'))
    expected_grass = profile['root']+'/Materials/LG_GeoCitySemanticGrass.LG_GeoCitySemanticGrass'
    if len(inputs) != 1 or _path(inputs[0].get_editor_property('grass_type')) != expected_grass:
        raise RuntimeError('Semantic Grass output lost the permanent area Grass Type.')
    _verify_textures(profile, instance)
    return {'weighted_targets_supported': sorted(weighted), 'auxiliary_targets_sampled': sorted(nonweight),
            'native_shader_pixels_verified': False, 'water_mode': 'classification_surface'}


def _semantic_binding_readback(profile, contract, material, grass):
    names = set(contract['class_targets'].values()).union(contract['role_layers'].values(), SEMANTIC_RGB, (SEMANTIC_MASK, SEMANTIC_WATER))
    return {'landscape_material':_path(material), 'grass_type':_path(grass),
                'varieties':_read_varieties(grass), 'material_layer_names':sorted(names),
                'corrected_normals':_verify_textures(profile, material),
                'coverage':LIB.get_material_instance_scalar_parameter_value(material,'GeoCity_GrassCoverage')}


def _semantic_runtime_binding(profile, contract, material, grass):
    """Measured preparation transfer. HDA must echo/validate it; not a licence."""
    config = profile['landscape_grass']
    readback = _semantic_binding_readback(profile,contract,material,grass)
    return {'schema': 'environmentpipeline.semantic_runtime_binding.v1',
            'area_id': contract['area_id'], 'source_package_sha256': contract['source_package_sha256'],
            'consumer_contract_sha256': contract['policy_sha256'],
            'landscape_material': _path(material), 'provider': contract['vegetation_provider'],
            'material_layer_names':readback['material_layer_names'],
            'native_binding_receipt_sha256':_semantic_digest(readback), 'catalog_sha256':profile['catalog_sha256'],
            'nonweight_layer_names': sorted(set(SEMANTIC_RGB).union((SEMANTIC_MASK,SEMANTIC_WATER))),
            'mask_layer': SEMANTIC_MASK, 'grass_type': _path(grass), 'grass_mesh_paths': list(config['mesh_paths']),
            'materials_by_mesh': {p: list(profile.get('instance_materials', {}).get(p, [])) for p in config['mesh_paths']},
            'coverage': float(config['coverage']) if config['enabled'] else 0.0,
            'density_per_10m2': float(config['density_per_10m2']),
            'material_graph_prepared': True, 'canonical_area_eligibility_verified': bool(config['enabled']),
            'grass_bindings_verified': True,
            'output_weight_readback_verified': False, 'visible_lit_grass_verified': False}


def _prepare_semantic(run):
    run.guard()
    contract, config = _semantic_preparation_contract(run.p), run.p['landscape_grass']
    source_identity = _semantic_source_identity(run.p, contract)
    if config['enabled']: _permitted(run.p, config)
    root = run.p['root'] + '/Materials/'
    # Permanent, explicitly saved area dependencies. Originals/shared Gaza graph
    # remain intact; source duplication preserves the retained texture branches.
    master = _semantic_owned_asset(root+'M_GeoCitySemanticGround', unreal.Material, duplicate=MASTER)
    child = _semantic_owned_asset(root+'MI_GeoCityGround', unreal.MaterialInstanceConstant, duplicate=BASE)
    grass = _semantic_owned_asset(root+'LG_GeoCitySemanticGrass', unreal.LandscapeGrassType, unreal.LandscapeGrassTypeFactory())
    expected = _expected_varieties(run.p, config)
    if _read_varieties(grass) != expected:
        varieties = []
        for entry in expected:
            mesh = unreal.load_asset(entry['mesh'])
            overrides = [unreal.load_asset(p) for p in entry['materials']]
            if not isinstance(mesh, unreal.StaticMesh) or any(not isinstance(m, unreal.MaterialInterface) for m in overrides):
                raise RuntimeError('Semantic Grass mesh/material dependency is unavailable.')
            variety = unreal.GrassVariety()
            variety.set_editor_property('grass_mesh', mesh)
            variety.set_editor_property('override_materials', overrides)
            for key in ('grass_density', 'start_cull_distance', 'end_cull_distance'):
                for suffix in ('', '_quality'):
                    cls = (unreal.PerQualityLevelFloat if suffix else unreal.PerPlatformFloat) if key == 'grass_density' else (unreal.PerQualityLevelInt if suffix else unreal.PerPlatformInt)
                    variety.set_editor_property(key+suffix, cls(default=entry[key+suffix]))
            for key in ('use_grid', 'placement_jitter', 'random_rotation', 'align_to_surface', 'weight_attenuates_max_scale', 'min_lod'):
                variety.set_editor_property(key, entry[key])
            variety.set_editor_property('scaling', unreal.GrassScaling.UNIFORM)
            for key in ('scale_x', 'scale_y', 'scale_z', 'allowed_density_range'):
                lo, hi = entry[key]
                variety.set_editor_property(key, unreal.FloatInterval(min=lo, max=hi))
            varieties.append(variety)
        grass.set_editor_property('grass_varieties', varieties)
    if _read_varieties(grass) != expected: raise RuntimeError('Semantic Grass settings failed native readback.')
    _semantic_graph(master, grass)
    LIB.recompile_material(master)
    LIB.set_material_instance_parent(child, master)
    requested = float(config['coverage']) if config['enabled'] else 0.0
    setter = LIB.set_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage', requested)
    LIB.update_material_instance(child)
    actual = LIB.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage')
    if not math.isfinite(actual) or abs(actual-requested) >= .0001:
        raise RuntimeError('Semantic Grass coverage did not bind.')
    readback = _semantic_material_readback(run.p, master, child, contract)
    packages = [a.get_outermost() for a in (grass, master, child)]
    if not unreal.EditorLoadingAndSavingUtils.save_packages(packages, True):
        raise RuntimeError('Named semantic dependency save failed.')
    run.p['landscape_material'] = _path(child)
    return {'enabled': config['enabled'], 'provider': contract['vegetation_provider'],
            'semantic_contract_sha256': _semantic_digest(contract), 'ground_layer': SEMANTIC_MASK,
            'coverage_readback': actual, 'coverage_setter_result': setter,
            'named_area_packages': [_path(p) for p in packages], 'shader_readback': readback,
            'source_identity': source_identity,
            'semantic_runtime_binding': _semantic_runtime_binding(run.p, contract, child, grass),
            'native_binding_receipt': _semantic_binding_readback(run.p, contract, child, grass),
            'bank_eligibility_changed': False, 'visible_lit_grass_verified': False}


def _verify_semantic_landscape(run, landscape, receipt):
    run.guard()
    contract = _semantic_verified_output_contract(run.p, receipt)
    frame = _semantic_actor_frame(run)
    _semantic_source_identity(run.p, contract)
    _semantic_output_contract(receipt, contract)
    if _path(landscape.get_editor_property('landscape_material')) != run.p['landscape_material']:
        raise RuntimeError('Semantic Landscape material binding differs.')
    child = unreal.load_asset(run.p['landscape_material'])
    master = unreal.load_asset(run.p['root']+'/Materials/M_GeoCitySemanticGround')
    grass_type = unreal.load_asset(run.p['root']+'/Materials/LG_GeoCitySemanticGrass')
    if not master or not grass_type or _read_varieties(grass_type) != _expected_varieties(run.p, run.p['landscape_grass']):
        raise RuntimeError('Semantic native dependencies differ from preparation.')
    material_readback = _semantic_material_readback(run.p, master, child, contract)
    actual = LIB.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage')
    requested = float(run.p['landscape_grass']['coverage']) if run.p['landscape_grass']['enabled'] else 0.0
    if not math.isfinite(actual) or abs(actual-requested) >= .0001:
        raise RuntimeError('Semantic native Grass coverage differs.')
    if run.p['landscape_grass']['enabled']: _permitted(run.p, run.p['landscape_grass'])
    binding = _semantic_runtime_binding(run.p, contract, child, grass_type)
    if receipt.get('semantic_runtime_binding_sha256') != _semantic_digest(binding):
        raise RuntimeError('HDA did not acknowledge the exact measured native semantic receiver.')
    expected = {n for n, v in contract['layers'].items() if v['state'] != 'absent'}
    layers = {str(n) for n in landscape.get_target_layer_names()}
    if layers != expected: raise RuntimeError('Native semantic target set differs, including zero/absent states.')
    components = [(c, unreal.SystemLibrary.get_component_bounds(c)) for c in landscape.get_components_by_class(unreal.LandscapeComponent)]
    samples = []
    def sample(component, xyz, name):
        vector = unreal.Vector(*xyz)
        samples.append({'id': name, 'world_location_cm': list(xyz),
                        'weights': {n: float(component.editor_get_paint_layer_weight_by_name_at_location(vector, n)) for n in expected}})
    for index, (component, (origin, extent, radius)) in enumerate(components):
        for x in (-.5, 0, .5):
            for y in (-.5, 0, .5):
                sample(component, [origin.x+x*extent.x, origin.y+y*extent.y, origin.z], 'grid:%d:%s:%s' % (index,x,y))
    for probe in contract['probes']:
        xyz = probe['world_location_cm']
        hits = [c for c, (origin, extent, radius) in components if abs(xyz[0]-origin.x) <= extent.x and abs(xyz[1]-origin.y) <= extent.y]
        if not hits: raise RuntimeError('Known semantic probe is outside Landscape: ' + probe['id'])
        sample(hits[0], xyz, probe['id'])
    result = evaluate_semantic_samples(samples, contract)
    grass = []
    for component in landscape.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        mesh = _path(component.get_editor_property('static_mesh'))
        if mesh not in PERMITTED_MESHES: raise RuntimeError('Unexpected semantic native Grass mesh.')
        grass.append({'component': _path(component), 'mesh': mesh, 'instances': component.get_instance_count()})
    count = sum(c['instances'] for c in grass)
    if count and (not run.p['landscape_grass']['enabled'] or result['grass_mask_expected_zero']):
        result['paint_ready'] = False
        result['paint_contract_failures'].append({'reason': 'unexpected_cache_for_disabled_or_zero_mask'})
    result.update(material=run.p['landscape_material'], semantic_contract_sha256=_semantic_digest(contract),
                  layer_names=sorted(layers), native_grass_components=grass, native_grass_instance_count=count,
                  grass_cache_output_observed=count>0, grass_count_is_current_loaded_cache=True,
                  nearby_grass_cache_verified=False, shader_readback=material_readback,
                  verified_HDA_actor_frame=frame,
                  known_location_samples=[s for s in samples if not s['id'].startswith('grid:')])
    return result


def prepare(run):
    return _prepare_semantic(run) if run.p.get('landscape_semantics') is not None else _GEOMETRIC_PREPARE(run)


def verify_landscape(run, landscape, receipt):
    return _verify_semantic_landscape(run, landscape, receipt) if run.p.get('landscape_semantics') is not None else _GEOMETRIC_VERIFY(run, landscape, receipt)


def inspect_near_view(run, landscape, view_location_cm, radius_cm=5000.0, receipt=None):
    if run.p.get('landscape_semantics') is None:
        return _GEOMETRIC_NEAR_VIEW(run, landscape, view_location_cm, radius_cm)
    if receipt is None:
        raise RuntimeError('Semantic near-view readback requires the current complete HDA receipt.')
    result = _verify_semantic_landscape(run, landscape, receipt)
    if len(view_location_cm) != 3 or not all(math.isfinite(float(v)) for v in view_location_cm) or not 0 < radius_cm <= 10000:
        raise RuntimeError('Invalid recorded semantic near-view location/radius.')
    near = []
    for component in landscape.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        for index in range(component.get_instance_count()):
            transform = component.get_instance_transform(index, world_space=True)
            if transform is None: raise RuntimeError('Semantic Grass instance transform is unavailable.')
            p = transform.translation
            xyz = [p.x, p.y, p.z]
            distance = math.sqrt(sum((a-b)**2 for a,b in zip(xyz, view_location_cm)))
            if distance <= radius_cm:
                near.append({'component': _path(component), 'instance': index, 'world_location_cm': xyz,
                             'mesh': _path(component.get_editor_property('static_mesh')), 'view_distance_cm': distance})
                break
    result.update(view_location_cm=list(view_location_cm), near_radius_cm=radius_cm,
                  nearby_grass_instances=near, nearby_grass_cache_verified=bool(near), visible_lit_grass_verified=False)
    return result
