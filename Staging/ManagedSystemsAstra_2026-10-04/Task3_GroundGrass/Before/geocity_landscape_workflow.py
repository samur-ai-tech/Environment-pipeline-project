"""Geographic ground/Grass connection inside the retained ordinary lifecycle.

Uses the existing material, painted Ground/RoadBed/BuildingPad/Steep targets
and already enabled grass rows. Trees/shrubs retain their HDA placement rules.
There is no separate scatter actor, geography import or bank release.
"""
import hashlib
import json
from pathlib import Path
import unreal

OWNER = 'GeoCity_LandscapeGrass'
LIB = unreal.MaterialEditingLibrary


def _path(obj):
    return obj.get_path_name() if obj else None


def _nodes(material):
    return [obj for obj in unreal.ObjectIterator(unreal.MaterialExpression)
            if obj.get_outer() == material]


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
    paths = _permitted(run.p, config)
    instance = unreal.load_asset(config['base_material_instance'])
    material = instance.get_editor_property('parent')
    root = '/Game/Project/Shared/SurfacePainting/Appearance_20261003/'
    if not _path(material).startswith(root) or not isinstance(material, unreal.Material):
        raise RuntimeError('Landscape Grass requires the retained owned Natural master material.')
    type_path = root + 'LG_GeoCity_PermittedGroundGrass'
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
    elif str(unreal.EditorAssetLibrary.get_metadata_tag(grass, 'GeoCityOwner')) != OWNER:
        raise RuntimeError('Existing Grass Type is not project-owned.')
    spec = {'meshes': paths, 'density': config['density_per_10m2'],
            'materials': {p: run.p.get('instance_materials', {}).get(p, []) for p in paths}}
    spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode('utf-8')).hexdigest()
    if str(unreal.EditorAssetLibrary.get_metadata_tag(grass, 'GeoCityGrassSpec')) != spec_hash:
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
            variety.set_editor_property('scale_x', unreal.FloatInterval(min=1.0, max=1.0))
            variety.set_editor_property('scale_y', unreal.FloatInterval(min=1.0, max=1.0))
            variety.set_editor_property('scale_z', unreal.FloatInterval(min=1.0, max=1.0))
            overrides = run.p.get('instance_materials', {}).get(path, [])
            if overrides:
                variety.set_editor_property('override_materials', [unreal.load_asset(p) for p in overrides])
            varieties.append(variety)
        grass.set_editor_property('grass_varieties', varieties)
        unreal.EditorAssetLibrary.set_metadata_tag(grass, 'GeoCityGrassSpec', spec_hash)
        changed = True
    nodes = _nodes(material)
    owned = [n for n in nodes if str(n.get_editor_property('desc')).startswith(OWNER)]
    output = [n for n in owned if isinstance(n, unreal.MaterialExpressionLandscapeGrassOutput)]
    if not output:
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
            assert LIB.connect_material_expressions(sample, '', multiply, 'A')
            assert LIB.connect_material_expressions(density, '', multiply, 'B')
            out = node(unreal.MaterialExpressionLandscapeGrassOutput, 'Output', 17400)
            inp = unreal.GrassInput()
            inp.set_editor_property('name', unreal.Name('GeoCityGroundGrass'))
            inp.set_editor_property('grass_type', grass)
            out.set_editor_property('grass_types', [inp])
            assert LIB.connect_material_expressions(multiply, '', out, 'GeoCityGroundGrass')
            output = [out]
            changed = True
        except Exception:
            for obj in reversed(created):
                LIB.delete_material_expression(material, obj)
            raise
    if len(output) != 1:
        raise RuntimeError('Ambiguous owned Landscape Grass output.')
    inputs = list(output[0].get_editor_property('grass_types'))
    if len(inputs) != 1 or inputs[0].get_editor_property('grass_type') != grass:
        raise RuntimeError('Landscape Grass Type binding differs from the ordinary profile.')
    samples = [n for n in _nodes(material) if str(n.get_editor_property('desc')) == OWNER + ':Ground']
    if len(samples) != 1 or str(samples[0].get_editor_property('parameter_name')) != config['ground_layer']:
        raise RuntimeError('Landscape Grass geographic layer binding differs.')
    if changed:
        LIB.recompile_material(material)
        assert unreal.EditorLoadingAndSavingUtils.save_packages([grass.get_outermost(), material.get_outermost()], True)
    child_path = run.p['root'] + '/Materials/MI_GeoCityGround'
    child = unreal.load_asset(child_path)
    if child is None:
        child = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'MI_GeoCityGround', child_path.rsplit('/', 1)[0],
            unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if child is None:
            raise RuntimeError('Cannot create the retained area ground material.')
        unreal.EditorAssetLibrary.set_metadata_tag(child, 'GeoCityOwner', OWNER)
    elif str(unreal.EditorAssetLibrary.get_metadata_tag(child, 'GeoCityOwner')) != OWNER:
        raise RuntimeError('Retained area ground material has another owner.')
    LIB.set_material_instance_parent(child, instance)
    LIB.update_material_instance(child)
    parameter = 'GeoCity_GrassCoverage'
    if parameter not in [str(name) for name in LIB.get_scalar_parameter_names(child)]:
        raise RuntimeError('Native Grass coverage parameter is unavailable on the area material.')
    requested = float(config['coverage'])
    # Installed 5.8 returned False while applying this value. Require actual
    # parameter presence and readback, rather than treating that flag as output.
    setter_result = LIB.set_material_instance_scalar_parameter_value(child, parameter, requested)
    LIB.update_material_instance(child)
    applied = LIB.get_material_instance_scalar_parameter_value(child, parameter)
    if abs(applied - requested) >= .0001:
        raise RuntimeError('Native Grass coverage parameter readback differs: requested=%s actual=%s setter=%s' % (requested, applied, setter_result))
    assert unreal.EditorLoadingAndSavingUtils.save_packages([child.get_outermost()], True)
    run.p['landscape_material'] = _path(child)
    return {'enabled': True, 'provider': 'native_LandscapeGrassOutput', 'grass_type': _path(grass),
            'material': _path(material), 'area_material': _path(child), 'mesh_paths': paths, 'ground_layer': config['ground_layer'],
            'coverage': config['coverage'], 'density_per_10m2': config['density_per_10m2'],
            'coverage_setter_result': setter_result, 'coverage_readback': applied,
            'named_shared_packages': [_path(grass.get_outermost()), _path(material.get_outermost())],
            'bank_eligibility_changed': False, 'distribution': 'generated_on_geographic_open_Ground; not surveyed vegetation'}


def is_native_grass(actor, component, profile):
    return (bool(profile.get('landscape_grass', {}).get('enabled'))
            and isinstance(actor, unreal.LandscapeProxy)
            and isinstance(component, unreal.HierarchicalInstancedStaticMeshComponent))


def verify_landscape(run, landscape, receipt):
    run.guard()
    if _path(landscape.get_editor_property('landscape_material')) != run.p['landscape_material']:
        raise RuntimeError('Geographic Landscape material binding is missing.')
    material = unreal.load_asset(run.p['landscape_material'])
    assert abs(LIB.get_material_instance_scalar_parameter_value(material, 'GeoCity_GrassCoverage') - float(run.p['landscape_grass']['coverage'])) < .0001, 'Native Grass coverage binding is missing'
    palette = receipt.get('surface_palette_choices', receipt.get('surface_palette', {}))
    # Installed 5.8 exposes these public editor methods, not the internal
    # EditorLayerSettings / WeightmapLayerAllocations fields.
    layers = [str(name) for name in landscape.get_target_layer_names()]
    expected = run.p.get('painted_layer_names', [])
    if expected and not set(expected).issubset(layers):
        raise RuntimeError('Relevant geographic paint layers are missing: ' + str(sorted(set(expected) - set(layers))))
    weights = {name: {'nonzero_samples': 0, 'max_weight': 0.0} for name in layers}
    sampled = 0
    for component in landscape.get_components_by_class(unreal.LandscapeComponent):
        origin, extent, radius = unreal.SystemLibrary.get_component_bounds(component)
        for x in (-.5, 0.0, .5):
            for y in (-.5, 0.0, .5):
                location = unreal.Vector(origin.x + x * extent.x, origin.y + y * extent.y, origin.z)
                sampled += 1
                for name in layers:
                    value = component.editor_get_paint_layer_weight_by_name_at_location(location, name)
                    weights[name]['max_weight'] = max(weights[name]['max_weight'], value)
                    weights[name]['nonzero_samples'] += int(value > 0.0)
    paint_observed = bool(sampled and weights[run.p['landscape_grass']['ground_layer']]['nonzero_samples'])
    grass = []
    for component in landscape.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        mesh = _path(component.get_editor_property('static_mesh'))
        if mesh not in run.p.get('landscape_grass', {}).get('mesh_paths', []):
            raise RuntimeError('Unexpected automatic grass mesh on the geographic Landscape: ' + str(mesh))
        grass.append({'component': _path(component), 'mesh': mesh, 'instances': component.get_instance_count()})
    return {'material': run.p['landscape_material'], 'layer_names': sorted(layers),
            'required_layer_names': expected, 'native_grass_components': grass,
            'paint_weight_sample_count': sampled, 'paint_weight_readback': weights,
            'ground_paint_weight_observed': paint_observed,
            'paint_samples_are_partial_coverage': True,
            'native_grass_instance_count': sum(v['instances'] for v in grass),
            'grass_count_is_current_loaded_cache': True,
            'grass_cache_output_observed': sum(v['instances'] for v in grass) > 0,
            'grass_cache_is_viewer_and_quality_dependent': True,
            'geographic_palette_receipt': palette}
