"""Reviewed, once-only Natural ground graph revision; caller alone owns Unreal.

ARGS: baseline_receipt and backup_manifest, both absolute task-local JSON paths.
Requires the exact actual-PID GROUND_AUTHORING lease and root's ready manifest.
Leaves five named Content packages dirty for separate compilation/review/save.
Duplication may create disk packages; each new file's existence/hash is reported.
No explicit Save, prepare, Cook, Bake, actor edits or automatic recovery.
"""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

import unreal

LIB = unreal.MaterialEditingLibrary
ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE = ROOT / 'Staging/GroundPainting_2026-10-04'
REV = HERE / 'Revision_2026-10-05'
SURFACE = '/Game/Project/Shared/SurfacePainting/Appearance_20261003'
MASTER = SURFACE + '/M_SurfaceBank_Natural'
BASE = SURFACE + '/MI_SurfaceBank_Natural'
GRASS = SURFACE + '/LG_GeoCity_PermittedGroundGrass'
THREAD = '01a10883-481f-7723-bdaa-fed004f15ef1'
MARK = 'GeoCity_GroundRevision_20261005:'
LAYERS = ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')
SOURCES = {'Sand_01': 'Sand_01', 'Sand_02': 'Sand_02',
           'Dirt_Path': 'Dirt_Path_01', 'Sand_Path': 'Sand_Path_01'}
MASK_SOURCES = {layer: '/Game/MOUT_Arabian/Textures/Landscape/' + stem + '/T_' + stem + '_Mask'
                for layer, stem in SOURCES.items()}
MASK_COPIES = {layer: SURFACE + '/Textures/T_' + stem + '_Mask_GeoCity'
               for layer, stem in SOURCES.items()}
FUNCTIONS = {
    'cell': '/Game/Iceland_Environment/Materials/MaterialFunctions/MF_DistanceCellBlend',
    'intensity': '/Game/Iceland_Environment/Materials/MaterialFunctions/MF_NormalIntensity',
    'color': '/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture',
    'normal': '/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal',
}
PROPERTIES = {'color': unreal.MaterialProperty.MP_BASE_COLOR,
              'normal': unreal.MaterialProperty.MP_NORMAL,
              'roughness': unreal.MaterialProperty.MP_ROUGHNESS,
              'ao': unreal.MaterialProperty.MP_AMBIENT_OCCLUSION,
              'specular': unreal.MaterialProperty.MP_SPECULAR,
              'metallic': unreal.MaterialProperty.MP_METALLIC,
              'emissive': unreal.MaterialProperty.MP_EMISSIVE_COLOR,
              'wpo': unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET,
              'opacity': unreal.MaterialProperty.MP_OPACITY,
              'opacity_mask': unreal.MaterialProperty.MP_OPACITY_MASK}


def path(obj):
    return obj.get_path_name() if obj else None


def package_file(package, suffix='.uasset'):
    assert package.startswith('/Game/')
    return ROOT / 'Content' / (package[6:].split('.')[0] + suffix)


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def disk_state(file):
    file = Path(file)
    row = {'file': str(file), 'exists': file.exists()}
    if row['exists']:
        try:
            row['sha256'] = sha(file)
        except Exception as error:
            row['read_error'] = repr(error)
    return row


def mask_disk_states():
    return {target: disk_state(package_file(target)) for target in MASK_COPIES.values()}


def plain(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if hasattr(value, 'get_path_name'):
        return path(value)
    if all(hasattr(value, c) for c in ('r', 'g', 'b', 'a')):
        return [float(getattr(value, c)) for c in ('r', 'g', 'b', 'a')]
    if all(hasattr(value, c) for c in ('x', 'y')):
        return [float(getattr(value, c)) for c in ('x', 'y', 'z', 'w') if hasattr(value, c)]
    return str(value)


def safe(obj, key):
    try:
        return obj.get_editor_property(key)
    except Exception:
        return None


def inputs(material, expression):
    names = list(LIB.get_material_expression_input_names(expression))
    nodes = list(LIB.get_inputs_for_material_expression(material, expression))
    assert len(names) == len(nodes), (path(expression), names, len(nodes))
    return list(zip(names, nodes))


def describe(material, expression):
    row = {'class': expression.get_class().get_name(), 'edges': {}, 'properties': {}}
    for name, source in inputs(material, expression):
        row['edges'][name] = {'source': path(source), 'output': str(
            LIB.get_input_node_output_name_for_material_expression(expression, source)) if source else None}
    for key in ('parameter_name', 'default_value', 'constant', 'r', 'g', 'b', 'a', 'value',
                'const_a', 'const_b', 'const_alpha', 'sampler_type', 'desc', 'texture',
                'material_function', 'min_default', 'max_default', 'mapping_scale',
                'mapping_type', 'custom_uv_type', 'mapping_rotation', 'mapping_pan_u', 'mapping_pan_v'):
        value = safe(expression, key)
        if value is not None:
            row['properties'][key] = plain(value)
    if isinstance(expression, unreal.MaterialExpressionLandscapeLayerBlend):
        row['layers'] = [{k: plain(entry.get_editor_property(k)) for k in
                          ('layer_name', 'blend_type', 'preview_weight', 'const_layer_input', 'const_height_input')}
                         for entry in expression.get_editor_property('layers')]
    if isinstance(expression, unreal.MaterialExpressionLandscapeGrassOutput):
        row['grass_types'] = [{'name': str(entry.get_editor_property('name')),
                               'grass_type': path(entry.get_editor_property('grass_type'))}
                              for entry in expression.get_editor_property('grass_types')]
    return row


def reachable(material, starts):
    seen, pending = {}, list(starts)
    while pending:
        expression = pending.pop()
        if expression and path(expression) not in seen:
            seen[path(expression)] = expression
            pending.extend(source for _, source in inputs(material, expression) if source)
    return seen


def one(candidates, label):
    candidates = list(candidates)
    assert len(candidates) == 1, (label, [plain(e) for e in candidates])
    return candidates[0]


def parameter(owned, name, cls):
    return one((e for e in owned.values() if isinstance(e, cls)
                and str(e.get_editor_property('parameter_name')) == name), name)


def grass_settings(grass):
    rows = []
    for variety in grass.get_editor_property('grass_varieties'):
        row = {'mesh': path(variety.get_editor_property('grass_mesh')),
               'materials': [path(m) for m in variety.get_editor_property('override_materials')]}
        for key in ('grass_density', 'grass_density_quality', 'start_cull_distance',
                    'end_cull_distance', 'start_cull_distance_quality', 'end_cull_distance_quality'):
            value = variety.get_editor_property(key)
            row[key] = float(value.get_editor_property('default'))
            override = 'per_quality' if key.endswith('_quality') else 'per_platform'
            row[key + '_overrides'] = {str(k): float(v) for k, v in
                                       dict(value.get_editor_property(override)).items()}
        for key in ('use_grid', 'placement_jitter', 'random_rotation', 'align_to_surface',
                    'weight_attenuates_max_scale', 'min_lod', 'scaling'):
            row[key] = plain(variety.get_editor_property(key))
        for key in ('scale_x', 'scale_y', 'scale_z', 'allowed_density_range'):
            value = variety.get_editor_property(key)
            row[key] = [float(value.get_editor_property('min')), float(value.get_editor_property('max'))]
        rows.append(row)
    return rows


def scene_state(actors):
    transforms, landscapes = {}, []
    for actor in actors:
        t = actor.get_actor_transform()
        transforms[path(actor)] = {'translation': plain(t.translation), 'rotation': plain(t.rotation),
                                   'scale': plain(t.scale3d)}
        if isinstance(actor, unreal.LandscapeProxy):
            landscapes.append({'path': path(actor), 'material': path(actor.get_editor_property('landscape_material')),
                               'hidden': actor.is_hidden_ed(), 'layers': str(safe(actor, 'editor_layer_settings'))})
    return {'transforms': transforms, 'landscapes': sorted(landscapes, key=lambda x: x['path'])}


def guard(assignment, named_map):
    lease = [s for s in (ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(
        encoding='utf-8-sig').splitlines() if s.strip()][-1]
    fields = dict(token.split('=', 1) for token in lease.split() if '=' in token)
    assert fields.get('OWNER') == 'CODEX_GROUND_PAINTING'
    assert fields.get('activation') == 'GROUND_AUTHORING'
    assert fields.get('assigned_editor_PID') == str(os.getpid()) and fields.get('map') == named_map
    assert fields.get('operator_thread_id') == assignment['execution_thread_id'] == THREAD
    import geocity_runtime_guard
    sources = geocity_runtime_guard.verify()
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    assert api and api.is_asset_cooking_paused()
    assert not unreal.get_default_object(unreal.load_class(
        None, '/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
    assert not any(getattr(run, key, None) is not None for name in
                   ('geocity_bank_workflow', 'geocity_roadbld_workflow') for run in
                   getattr(sys.modules.get(name), 'ACTIVE', []) for key in
                   ('watch_tick', 'save_tick', 'tick_handle', '_pending_correction'))
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    hdas = [a for a in actors if isinstance(a, unreal.HoudiniAssetActor)]
    assert len(hdas) == 1
    for actor in hdas:
        wrapper = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None, actor)
        assert not wrapper.is_auto_cooking_enabled() and not wrapper.is_auto_bake_enabled()
    return sources, actors


def revise(args):
    assignment = json.loads((HERE / 'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    sources, actors = guard(assignment, named_map)
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    input_files = {}
    for key in ('baseline_receipt', 'backup_manifest'):
        file = Path(args[key]).resolve(strict=True)
        assert file.is_relative_to(HERE) and file.suffix == '.json', (key, str(file))
        input_files[key] = file
    baseline = json.loads(input_files['baseline_receipt'].read_text(encoding='utf-8-sig'))
    assert baseline['pid'] == os.getpid() and baseline['world'] == named_map
    assert not baseline['dirty_maps'] and not baseline['dirty_content']
    assert baseline['graph_expression_count'] == 704
    manifest = json.loads(input_files['backup_manifest'].read_text(encoding='utf-8-sig'))
    assert manifest['ready'] is True and manifest['ready_for_graph_revision'] is True
    assert manifest['pid'] == manifest['editor_pid'] == os.getpid()
    assert manifest['world'] == named_map and manifest['execution_thread_id'] == THREAD
    assert manifest['ordinary_generation_authorized'] is False
    assert set(manifest['new_asset_paths']) == set(MASK_COPIES.values())
    bindings = manifest['file_bindings']
    required = [MASTER, BASE, GRASS, SURFACE + '/Textures/T_Sand_01_Normal_GeoCity',
                SURFACE + '/Textures/T_Sand_02_Normal_GeoCity', assignment['material_contract']['area_instances'][area],
                *MASK_SOURCES.values()]
    required_files = {str(package_file(p).resolve()) for p in required}
    required_files.add(str(package_file(named_map, '.umap').resolve()))
    normalized = {str(Path(k).resolve(strict=True)): v for k, v in bindings.items()}
    assert required_files <= set(normalized), sorted(required_files - set(normalized))
    for source, row in normalized.items():
        backup = Path(row['backup']).resolve(strict=True)
        assert Path(source).is_relative_to(ROOT) and backup.is_relative_to(REV / 'Before')
        assert sha(source) == sha(backup) == row['sha256'], source
    for family in ('preserved_files', 'sealed_files'):
        for relative, expected in manifest[family].items():
            file = (ROOT / relative).resolve(strict=True)
            assert file.is_relative_to(ROOT) and sha(file) == expected, relative
    for target in MASK_COPIES.values():
        assert not unreal.EditorAssetLibrary.does_asset_exist(target)
        assert not package_file(target).exists(), target
    once = REV / 'GRAPH_REVISION_ONCE.json'
    assert not once.exists(), 'Attempt already recorded; root must inspect/preserve before another action.'
    material = unreal.load_asset(MASTER)
    assert isinstance(material, unreal.Material)
    assert material.get_editor_property('tangent_space_normal') is True
    assert not material.get_editor_property('enable_tessellation')
    roots = {name: LIB.get_material_property_input_node(material, prop) for name, prop in PROPERTIES.items()}
    assert roots['ao'] is None and roots['specular'] is None
    assert all(isinstance(roots[k], unreal.MaterialExpressionLandscapeLayerBlend)
               for k in ('color', 'normal', 'roughness'))
    layer_names = [str(e.get_editor_property('layer_name')) for e in roots['color'].get_editor_property('layers')]
    assert len(layer_names) == len(set(layer_names)) == 69 and set(LAYERS) <= set(layer_names)
    for key in ('color', 'normal', 'roughness'):
        entries = roots[key].get_editor_property('layers')
        assert [str(e.get_editor_property('layer_name')) for e in entries] == layer_names
        assert all(e.get_editor_property('blend_type') == unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND for e in entries)
    nodes = list(LIB.get_material_expressions(material))
    assert len(nodes) == 704 and not any(str(safe(e, 'desc')).startswith(MARK) for e in nodes)
    old = {path(e): describe(material, e) for e in nodes}
    active = reachable(material, [roots[k] for k in ('color', 'normal', 'roughness')])
    old_parameters = {str(safe(e, 'parameter_name')) for e in nodes if safe(e, 'parameter_name') is not None}
    selected = {layer: {suffix: parameter(active, layer + '_' + suffix, cls)
                       for suffix, cls in [('Albedo', unreal.MaterialExpressionTextureObjectParameter),
                                           ('Normal', unreal.MaterialExpressionTextureObjectParameter),
                                           ('TileCm', unreal.MaterialExpressionVectorParameter),
                                           ('Tint', unreal.MaterialExpressionVectorParameter),
                                           ('Roughness', unreal.MaterialExpressionScalarParameter)]} for layer in LAYERS}
    for layer, params in selected.items():
        assert params['Albedo'].get_editor_property('sampler_type') == unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
        assert params['Normal'].get_editor_property('sampler_type') == unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        normal = params['Normal'].get_editor_property('texture')
        assert normal.get_editor_property('srgb') is False
        assert normal.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_NORMALMAP
        if layer in ('Sand_01', 'Sand_02'):
            assert path(normal) == SURFACE + '/Textures/T_' + layer + '_Normal_GeoCity.T_' + layer + '_Normal_GeoCity'
    landscapes = [a for a in actors if isinstance(a, unreal.LandscapeProxy)]
    assert landscapes and sorted(path(a) for a in landscapes) == sorted(row['path'] for row in baseline['landscapes'])
    expected_child = assignment['material_contract']['area_instances'][area]
    for actor in landscapes:
        scale = actor.get_actor_scale3d()
        assert abs(scale.x - 100) < 1e-6 and abs(scale.y - 100) < 1e-6
        assert path(actor.get_editor_property('landscape_material')) == expected_child
    before_scene = scene_state(actors)
    assert before_scene['transforms'] == baseline['actor_transforms']
    grass = unreal.load_asset(GRASS)
    grass_nodes = [e for e in nodes if isinstance(e, unreal.MaterialExpressionLandscapeGrassOutput)]
    assert len(grass_nodes) == 1
    grass_graph = {p: describe(material, e) for p, e in reachable(material, grass_nodes).items()}
    grass_before = {'graph': grass_graph, 'settings': grass_settings(grass),
                    'effective_coverage': {path(a): float(LIB.get_material_instance_scalar_parameter_value(
                        a.get_editor_property('landscape_material'), 'GeoCity_GrassCoverage')) for a in landscapes}}
    native_functions = {k: unreal.load_asset(v) for k, v in FUNCTIONS.items()}
    assert all(isinstance(f, unreal.MaterialFunction) for f in native_functions.values())
    macro_object = parameter(active, 'Ground_MacroMask', unreal.MaterialExpressionTextureObjectParameter)
    macro_tile = parameter(active, 'Ground_MacroTileCm', unreal.MaterialExpressionVectorParameter)
    macro_call = one((e for e in active.values() if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall)
                      and macro_object in [s for _, s in inputs(material, e)]
                      and macro_tile in [s for _, s in inputs(material, e)]), 'original macro sample')
    receipt = {'schema': 'environmentpipeline.ground_graph_revision.v1', 'pid': os.getpid(), 'world': named_map,
               'area': area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'input_files': {k: {'file': str(v), 'sha256': sha(v)} for k, v in input_files.items()},
               'sources': sources, 'master': path(material), 'old_node_count': len(old), 'old_nodes': old,
               'roots_before': {k: path(v) for k, v in roots.items()}, 'layer_names': layer_names,
               'grass_before': grass_before, 'grass_digest_before': digest(grass_before),
               'scene_digest_before': digest(before_scene), 'added_assets': [], 'added_nodes': [],
               'added_parameters': {}, 'modified_pins': [], 'status': 'attempt_started',
               'compile_pending': True, 'explicit_save_called': False, 'explicit_save_paths': [],
               'existing_package_file_count': len(normalized),
               'existing_package_files_before': {source: row['sha256'] for source, row in normalized.items()},
               'new_mask_package_files_before': mask_disk_states()}
    out = REV / ('GRAPH_REVISION_PID' + str(os.getpid()) + '.json')
    assert not out.exists()
    with once.open('x', encoding='utf-8') as stream:
        json.dump({'pid': os.getpid(), 'world': named_map, 'status': 'attempt_started', 'receipt': str(out)}, stream, indent=2)

    def node(cls, label, **properties):
        index = len(receipt['added_nodes'])
        expression = LIB.create_material_expression(material, cls, -4000 + (index % 10) * 240, 22000 + (index // 10) * 230)
        assert expression is not None, label
        expression.set_editor_property('desc', MARK + label)
        for key, value in properties.items():
            expression.set_editor_property(key, value)
        receipt['added_nodes'].append(path(expression))
        return expression

    def scalar(name, value):
        assert name not in old_parameters and name not in receipt['added_parameters']
        expression = node(unreal.MaterialExpressionScalarParameter, name, parameter_name=name, default_value=value)
        receipt['added_parameters'][name] = value
        return expression

    def link(source, output, target, input_name):
        names = list(LIB.get_material_expression_input_names(target))
        if input_name not in names and input_name == 'Input' and 'None' in names:
            input_name = 'None'
        assert input_name in names, (path(target), input_name, names)
        outputs = list(LIB.get_material_expression_output_names(source))
        # Installed API explicitly defines an empty name as the first output,
        # including vector parameters whose other outputs are R/G/B/A.
        assert output in outputs or (output == '' and outputs), (path(source), output, outputs)
        assert LIB.connect_material_expressions(source, output, target, input_name), (path(target), input_name)

    def call(key, label, connections):
        expression = node(unreal.MaterialExpressionMaterialFunctionCall, label, material_function=native_functions[key])
        for pin, (source, output) in connections.items():
            link(source, output, expression, pin)
        return expression

    def binary(cls, label, a, b):
        expression = node(cls, label)
        link(a, '', expression, 'A'); link(b, '', expression, 'B')
        return expression

    def lerp(label, a, a_output, b, b_output, alpha):
        expression = node(unreal.MaterialExpressionLinearInterpolate, label)
        link(a, a_output, expression, 'A'); link(b, b_output, expression, 'B'); link(alpha, '', expression, 'Alpha')
        return expression

    def clamp(label, source, low, high):
        expression = node(unreal.MaterialExpressionClamp, label, min_default=low, max_default=high)
        link(source, '', expression, 'Input')
        return expression

    try:
        true = node(unreal.MaterialExpressionStaticBool, 'True', value=True)
        false = node(unreal.MaterialExpressionStaticBool, 'False', value=False)
        world_position = node(unreal.MaterialExpressionWorldPosition, 'WorldPosition')
        camera = node(unreal.MaterialExpressionCameraPositionWS, 'Camera')
        distance = binary(unreal.MaterialExpressionDistance, 'CameraDistance', camera, world_position)
        start = scalar('GeoCity_DistanceStartCm', 1200.)
        fade_range = scalar('GeoCity_DistanceRangeCm', 4800.)
        safe_range = clamp('PositiveDistanceRange', fade_range, 1., 1000000.)
        delta = binary(unreal.MaterialExpressionSubtract, 'DistanceMinusStart', distance, start)
        ratio = binary(unreal.MaterialExpressionDivide, 'DistanceRatio', delta, safe_range)
        alpha = node(unreal.MaterialExpressionSaturate, 'SharedDistanceAlpha')
        link(ratio, '', alpha, 'Input')
        rough_detail = clamp('RoughDetailBound', scalar('GeoCity_RoughnessDetail', .75), 0., 1.)
        ao_strength = clamp('AOStrengthBound', scalar('GeoCity_AOStrength', .3), 0., 1.)
        macro_amount = clamp('MacroAmountBound', scalar('GeoCity_MacroAmount', .08), 0., .08)
        cell_scale = scalar('GeoCity_CellScale', .1)
        pattern_scale = scalar('GeoCity_PatternScale', 1.)
        grid_cm = node(unreal.MaterialExpressionConstant, 'LandscapeGridCm100', r=100.)
        coordinates = node(unreal.MaterialExpressionLandscapeLayerCoords, 'LandscapeXY',
                           mapping_scale=1., mapping_type=unreal.TerrainCoordMappingType.TCMT_XY,
                           custom_uv_type=unreal.LandscapeCustomizedCoordType.LCCT_NONE,
                           mapping_rotation=0., mapping_pan_u=0., mapping_pan_v=0.)
        one_value = node(unreal.MaterialExpressionConstant, 'One', r=1.)
        outputs = {}
        for layer in LAYERS:
            source = unreal.load_asset(MASK_SOURCES[layer])
            assert isinstance(source, unreal.Texture2D)
            copied = unreal.EditorAssetLibrary.duplicate_asset(MASK_SOURCES[layer], MASK_COPIES[layer])
            assert isinstance(copied, unreal.Texture2D) and path(copied).split('.')[0] == MASK_COPIES[layer]
            copied_row = {'source': path(source), 'path': path(copied),
                          'disk_immediately_after_duplicate': disk_state(package_file(MASK_COPIES[layer]))}
            receipt['added_assets'].append(copied_row)
            copied.set_editor_property('srgb', False)
            copied.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
            assert copied.get_editor_property('srgb') is False
            assert copied.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_MASKS
            copied_row.update(srgb=False, compression='TC_MASKS')
            texture_name = layer + '_PackedMask'
            assert texture_name not in old_parameters
            mask = node(unreal.MaterialExpressionTextureObjectParameter, texture_name, parameter_name=texture_name,
                        texture=copied, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            receipt['added_parameters'][texture_name] = path(copied)
            params = selected[layer]
            far_scale = clamp(layer + 'FarScaleBound', scalar(layer + '_FarScale', 5.), 1., 32.)
            strength = clamp(layer + 'NormalStrengthBound', scalar(layer + '_NormalStrength', 1.6), 0., 4.)
            texture_sets = {'color': params['Albedo'], 'normal': params['Normal'], 'mask': mask}
            sampled = {}
            if layer != 'Sand_02':
                tile_r = node(unreal.MaterialExpressionComponentMask, layer + 'TileR', r=True, g=False, b=False, a=False)
                link(params['TileCm'], '', tile_r, 'Input')
                tile_safe = clamp(layer + 'TilePositive', tile_r, 1., 1000000.)
                tiling = binary(unreal.MaterialExpressionDivide, layer + 'CentimetersToUV', grid_cm, tile_safe)
                near_uv = binary(unreal.MaterialExpressionMultiply, layer + 'NearUV', coordinates, tiling)
                far_uv = binary(unreal.MaterialExpressionDivide, layer + 'FarUV', near_uv, far_scale)
                for channel, texture in texture_sets.items():
                    fn = call('cell', layer + channel + 'DistanceCell', {
                        'Texture': (texture, ''), 'NearUVs': (near_uv, ''), 'FarUVs': (far_uv, ''),
                        'CellScale': (cell_scale, ''), 'PatternScale': (pattern_scale, ''),
                        'IsNormalMap': (true if channel == 'normal' else false, ''),
                        'DistanceBlend?': (true, ''), 'DistanceBlend': (alpha, '')})
                    sampled[channel] = (fn, 'Output')
            else:
                far_size = binary(unreal.MaterialExpressionMultiply, layer + 'FarTextureSize', params['TileCm'], far_scale)
                for channel, texture in texture_sets.items():
                    key = 'normal' if channel == 'normal' else 'color'
                    pair = []
                    for which, size in [('Near', params['TileCm']), ('Far', far_size)]:
                        fn = call(key, layer + channel + which, {'TextureObject': (texture, ''),
                                  'TextureSize': (size, ''), 'WorldPosition': (world_position, '')})
                        pair.append(fn)
                    result = lerp(layer + channel + 'Distance', pair[0], 'XYZ Texture', pair[1], 'XYZ Texture', alpha)
                    sampled[channel] = (result, '')
            color = node(unreal.MaterialExpressionMultiply, layer + 'TintedColor')
            link(*sampled['color'], color, 'A'); link(params['Tint'], '', color, 'B')
            if layer == 'Sand_01':
                macro_r = node(unreal.MaterialExpressionComponentMask, 'MacroRed', r=True, g=False, b=False, a=False)
                link(macro_call, 'XYZ Texture', macro_r, 'Input')
                macro_r = clamp('MacroRedBound', macro_r, 0., 1.)
                doubled = node(unreal.MaterialExpressionMultiply, 'MacroDouble', const_b=2.)
                link(macro_r, '', doubled, 'A')
                centered = binary(unreal.MaterialExpressionSubtract, 'MacroCentered', doubled, one_value)
                variation = binary(unreal.MaterialExpressionMultiply, 'MacroVariation', centered, macro_amount)
                multiplier = binary(unreal.MaterialExpressionAdd, 'MacroMultiplier', one_value, variation)
                color = binary(unreal.MaterialExpressionMultiply, 'SandRestrainedMacroColor', color, multiplier)
            intensity = call('intensity', layer + 'NormalIntensity', {'NormalMap': sampled['normal'], 'Normal Strength': (strength, '')})
            normal = node(unreal.MaterialExpressionNormalize, layer + 'UnitNormal')
            link(intensity, 'Result', normal, 'VectorInput')
            packed_r = node(unreal.MaterialExpressionComponentMask, layer + 'PackedRoughnessR', r=True, g=False, b=False, a=False)
            packed_g = node(unreal.MaterialExpressionComponentMask, layer + 'PackedAOG', r=False, g=True, b=False, a=False)
            link(*sampled['mask'], packed_r, 'Input'); link(*sampled['mask'], packed_g, 'Input')
            roughness = clamp(layer + 'BoundedRoughness', lerp(layer + 'RoughnessDetail', params['Roughness'], '', packed_r, '', rough_detail), .55, .98)
            ao = lerp(layer + 'SubtleAO', one_value, '', packed_g, '', ao_strength)
            outputs[layer] = {'color': color, 'normal': normal, 'roughness': roughness, 'ao': ao}
        ao_entries = []
        for entry in roots['color'].get_editor_property('layers'):
            new_entry = unreal.LayerBlendInput()
            for key in ('layer_name', 'blend_type', 'preview_weight'):
                new_entry.set_editor_property(key, entry.get_editor_property(key))
            ao_entries.append(new_entry)
        ao_root = node(unreal.MaterialExpressionLandscapeLayerBlend, 'AO69Layers', layers=ao_entries)
        for layer in layer_names:
            link(outputs[layer]['ao'] if layer in outputs else one_value, '', ao_root, 'Layer ' + layer)
        for key in ('color', 'normal', 'roughness'):
            for layer in LAYERS:
                pin = 'Layer ' + layer
                link(outputs[layer][key], '', roots[key], pin)
                receipt['modified_pins'].append({'root': path(roots[key]), 'pin': pin,
                                                'before': old[path(roots[key])]['edges'][pin], 'after': path(outputs[layer][key])})
        assert LIB.connect_material_property(ao_root, '', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
        # Re-read before any separate root-owned compilation or named saves.
        after_nodes = list(LIB.get_material_expressions(material))
        after = {path(e): describe(material, e) for e in after_nodes}
        assert set(old) <= set(after) and len(after) == 704 + len(receipt['added_nodes'])
        permitted = {(path(roots[key]), 'Layer ' + layer) for key in ('color', 'normal', 'roughness') for layer in LAYERS}
        changed = set()
        for node_path, old_row in old.items():
            new_row = after[node_path]
            assert {k: v for k, v in old_row.items() if k != 'edges'} == {k: v for k, v in new_row.items() if k != 'edges'}, node_path
            assert set(old_row['edges']) == set(new_row['edges']), node_path
            for pin, edge in old_row['edges'].items():
                if edge != new_row['edges'][pin]:
                    changed.add((node_path, pin))
                    assert (node_path, pin) in permitted, (node_path, pin)
        assert changed == permitted, (sorted(changed), sorted(permitted))
        roots_after = {name: LIB.get_material_property_input_node(material, prop) for name, prop in PROPERTIES.items()}
        assert path(roots_after['ao']) == path(ao_root)
        assert all(path(roots_after[k]) == path(v) for k, v in roots.items() if k != 'ao')
        grass_after = {'graph': {p: describe(material, e) for p, e in reachable(material, grass_nodes).items()},
                       'settings': grass_settings(grass), 'effective_coverage': {
                           path(a): float(LIB.get_material_instance_scalar_parameter_value(
                               a.get_editor_property('landscape_material'), 'GeoCity_GrassCoverage')) for a in landscapes}}
        assert grass_after == grass_before, 'Grass graph/settings/effective coverage changed'
        sources_after, actors_after = guard(assignment, named_map)
        assert sources_after == sources and scene_state(actors_after) == before_scene
        dirty_maps = [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
        dirty_content = [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
        expected_dirty = {MASTER, *MASK_COPIES.values()}
        assert not dirty_maps and set(dirty_content) == expected_dirty, (dirty_maps, dirty_content)
        for source, row in normalized.items():
            assert sha(source) == row['sha256'], 'Unexpected package save: ' + source
        for family in ('preserved_files', 'sealed_files'):
            assert all(sha(ROOT / relative) == expected for relative, expected in manifest[family].items()), family
        receipt.update(status='graph_verified_no_explicit_save_compile_pending', old_node_preservation_verified=True,
                       permitted_old_edge_changes=12, new_ao_root=path(ao_root),
                       roots_after={k: path(v) for k, v in roots_after.items()}, added_node_count=len(receipt['added_nodes']),
                       nodes_after=after, grass_after=grass_after, grass_digest_after=digest(grass_after),
                       scene_digest_after=digest(scene_state(actors_after)), dirty_maps=dirty_maps, dirty_content=dirty_content,
                       channels={'R': 'Roughness', 'G': 'AO', 'B': 'height_unused'},
                       macro_multiplier_bounds=[.92, 1.08], grid_cm_constant=100.,
                       existing_package_files_after={source: disk_state(source) for source in normalized},
                       existing_package_files_unchanged=True,
                       new_mask_package_files_after=mask_disk_states())
    except Exception as error:
        receipt.update(status='failed_no_explicit_save_requires_root_review', error=repr(error),
                       dirty_maps=[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
                       dirty_content=[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],
                       existing_package_files_after={source: disk_state(source) for source in normalized},
                       new_mask_package_files_after=mask_disk_states())
        receipt['existing_package_files_unchanged'] = all(
            row.get('sha256') == normalized[source]['sha256']
            for source, row in receipt['existing_package_files_after'].items())
        try:
            current_nodes = list(LIB.get_material_expressions(material))
            receipt['nodes_at_failure'] = {path(e): describe(material, e) for e in current_nodes}
            receipt['added_nodes_at_failure'] = sorted(set(receipt['nodes_at_failure']) - set(old))
            receipt['roots_at_failure'] = {name: path(LIB.get_material_property_input_node(material, prop))
                                           for name, prop in PROPERTIES.items()}
        except Exception as snapshot_error:
            receipt['failure_snapshot_error'] = repr(snapshot_error)
        out.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        once.write_text(json.dumps({'pid': os.getpid(), 'world': named_map, 'status': receipt['status'], 'receipt': str(out)}, indent=2), encoding='utf-8')
        raise
    out.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    once.write_text(json.dumps({'pid': os.getpid(), 'world': named_map, 'status': receipt['status'], 'receipt': str(out)}, indent=2), encoding='utf-8')
    return {'receipt': str(out), 'status': receipt['status'], 'added_node_count': receipt['added_node_count'],
            'added_assets': receipt['added_assets'], 'added_parameters': receipt['added_parameters'],
            'dirty_content': receipt['dirty_content'], 'compile_pending': True,
            'explicit_save_called': False, 'explicit_save_paths': [],
            'existing_package_file_count': receipt['existing_package_file_count'],
            'existing_package_files_unchanged': receipt['existing_package_files_unchanged'],
            'new_mask_package_files_after': receipt['new_mask_package_files_after']}


if 'ARGS' in globals():
    RESULT = revise(ARGS)
