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
