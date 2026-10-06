"""Bounded second Natural graph edit; sole root writer executes after review.

ARGS: absolute baseline_receipt(current820), graph_receipt(successful revision),
backup_manifest. Preserves all820 expressions/properties; only16 old edge changes.
No assets, explicit compile/save, Grass/scene edits, Cook/Bake or automatic recovery.
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



OLDMARK = MARK
MARK = 'GeoCity_GroundRefinement_20261005:'
FLAT = ('Sand_01', 'Dirt_Path', 'Sand_Path')


def refine(args):
    assignment = json.loads((HERE / 'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    sources, actors = guard(assignment, named_map)
    input_files, documents = {}, {}
    for key in ('baseline_receipt', 'graph_receipt', 'backup_manifest'):
        file = Path(args[key]).resolve(strict=True)
        assert file.is_relative_to(HERE) and file.suffix == '.json', (key, str(file))
        input_files[key] = file
        documents[key] = json.loads(file.read_text(encoding='utf-8-sig'))
    baseline, reference, manifest = (documents[k] for k in ('baseline_receipt', 'graph_receipt', 'backup_manifest'))
    assert baseline['pid'] == reference['pid'] == manifest['pid'] == manifest['editor_pid'] == os.getpid()
    assert baseline['world'] == reference['world'] == manifest['world'] == named_map
    assert baseline['graph_expression_count'] == 820
    assert reference['status'] == 'graph_verified_no_explicit_save_compile_pending'
    assert reference['old_node_preservation_verified'] and reference['existing_package_files_unchanged']
    assert len(reference['nodes_after']) == 820 and reference['added_node_count'] == 116
    assert manifest['ready'] is True and manifest['ready_for_graph_revision'] is True
    assert manifest['execution_thread_id'] == THREAD and manifest['ordinary_generation_authorized'] is False
    assert set(manifest['new_asset_paths']) == set(MASK_COPIES.values())
    normalized = {str(Path(k).resolve(strict=True)): row for k, row in manifest['file_bindings'].items()}
    assert len(normalized) == 13
    for source, row in normalized.items():
        backup = Path(row['backup']).resolve(strict=True)
        assert Path(source).is_relative_to(ROOT) and backup.is_relative_to(REV / 'Before')
        assert sha(source) == sha(backup) == row['sha256'], source
    for family in ('preserved_files', 'sealed_files'):
        for relative, expected in manifest[family].items():
            file = (ROOT / relative).resolve(strict=True)
            assert file.is_relative_to(ROOT) and sha(file) == expected, relative
    child = assignment['material_contract']['area_instances'][area]
    expected_dirty = {MASTER, child.split('.')[0], *MASK_COPIES.values()}
    dirty_maps_before = [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    dirty_content_before = [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    assert dirty_maps_before == baseline['dirty_maps'] == []
    assert set(dirty_content_before) == set(baseline['dirty_content']) == expected_dirty
    once = REV / 'GRAPH_REFINEMENT_ONCE.json'
    out = REV / ('GRAPH_REFINEMENT_PID' + str(os.getpid()) + '.json')
    assert not once.exists() and not out.exists(), 'Root review required before any further attempt.'
    material = unreal.load_asset(MASTER)
    assert isinstance(material, unreal.Material)
    assert material.get_editor_property('tangent_space_normal') is True
    assert not material.get_editor_property('enable_tessellation')
    roots = {name: LIB.get_material_property_input_node(material, prop) for name, prop in PROPERTIES.items()}
    assert {k: path(v) for k, v in roots.items()} == reference['roots_after']
    nodes = list(LIB.get_material_expressions(material))
    assert len(nodes) == 820 and not any(str(safe(e, 'desc')).startswith(MARK) for e in nodes)
    owned = {path(e): e for e in nodes}
    old = {p: describe(material, e) for p, e in owned.items()}
    assert old == reference['nodes_after'], 'Current820 graph differs from retained revision receipt'
    layer_names = reference['layer_names']
    for key in ('color', 'normal', 'roughness', 'ao'):
        assert isinstance(roots[key], unreal.MaterialExpressionLandscapeLayerBlend)
        entries = roots[key].get_editor_property('layers')
        assert [str(e.get_editor_property('layer_name')) for e in entries] == layer_names
        assert all(e.get_editor_property('blend_type') == unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND for e in entries)
    assert len(layer_names) == len(set(layer_names)) == 69
    before_scene = scene_state(actors)
    assert before_scene['transforms'] == baseline['actor_transforms']
    landscapes = [a for a in actors if isinstance(a, unreal.LandscapeProxy)]
    assert sorted(path(a) for a in landscapes) == sorted(row['path'] for row in baseline['landscapes'])
    for actor in landscapes:
        scale = actor.get_actor_scale3d()
        assert abs(scale.x - 100) < 1e-6 and abs(scale.y - 100) < 1e-6
        assert path(actor.get_editor_property('landscape_material')) == child

    def tagged(label):
        return one((e for e in nodes if safe(e, 'desc') == OLDMARK + label), label)

    def upstream(expression, pin):
        return one((e for name, e in inputs(material, expression) if name == pin and e), pin)

    active = reachable(material, [roots[k] for k in ('color', 'normal', 'roughness', 'ao')])
    macro_object = parameter(active, 'Ground_MacroMask', unreal.MaterialExpressionTextureObjectParameter)
    macro_tile = parameter(active, 'Ground_MacroTileCm', unreal.MaterialExpressionVectorParameter)
    original_sand = one((r for r in reference['modified_pins']
                         if r['root'] == path(roots['color']) and r['pin'] == 'Layer Sand_01'), 'priorSandPin')
    original_branch = reachable(material, [owned[original_sand['before']['source']]])
    soil_strength = parameter(original_branch, 'Ground_SoilBlendStrength', unreal.MaterialExpressionScalarParameter)
    pattern_scale = tagged('GeoCity_PatternScale')
    distance_alpha = tagged('SharedDistanceAlpha')
    world_position = tagged('WorldPosition')
    flat_sources, consumers = {}, {}
    allowed = set()
    sampler_types = {'color': unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                     'normal': unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                     'mask': unreal.MaterialSamplerType.SAMPLERTYPE_MASKS}
    for layer in FLAT:
        flat_sources[layer] = {}
        for channel, sampler in sampler_types.items():
            function = tagged(layer + channel + 'DistanceCell')
            texture = upstream(function, 'Texture')
            assert isinstance(texture, unreal.MaterialExpressionTextureObjectParameter)
            assert texture.get_editor_property('sampler_type') == sampler
            assert upstream(function, 'NearUVs') == tagged(layer + 'NearUV')
            assert upstream(function, 'FarUVs') == tagged(layer + 'FarUV')
            assert upstream(function, 'DistanceBlend') == distance_alpha
            flat_sources[layer][channel] = texture
        normal_texture = flat_sources[layer]['normal'].get_editor_property('texture')
        assert normal_texture.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_NORMALMAP
        assert normal_texture.get_editor_property('srgb') is False
        if layer == 'Sand_01':
            assert path(normal_texture) == SURFACE + '/Textures/T_Sand_01_Normal_GeoCity.T_Sand_01_Normal_GeoCity'
        packed = flat_sources[layer]['mask'].get_editor_property('texture')
        assert path(packed).split('.')[0] == MASK_COPIES[layer]
        assert packed.get_editor_property('srgb') is False
        assert packed.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_MASKS
        consumers[layer] = [(tagged(layer + 'TintedColor'), 'A', 'color'),
                            (tagged(layer + 'NormalIntensity'), 'NormalMap', 'normal'),
                            (tagged(layer + 'PackedRoughnessR'), 'None', 'mask'),
                            (tagged(layer + 'PackedAOG'), 'None', 'mask')]
        for target, pin, channel in consumers[layer]:
            assert upstream(target, pin) == tagged(layer + channel + 'DistanceCell')
            allowed.add((path(target), pin))
    ground, soil = {}, {}
    for key in ('color', 'normal', 'roughness', 'ao'):
        ground[key] = upstream(roots[key], 'Layer Sand_01')
        soil[key] = upstream(roots[key], 'Layer Dirt_Path')
        allowed.add((path(roots[key]), 'Layer Sand_01'))
    assert len(allowed) == 16
    grass = unreal.load_asset(GRASS)
    grass_nodes = [e for e in nodes if isinstance(e, unreal.MaterialExpressionLandscapeGrassOutput)]
    assert len(grass_nodes) == 1

    def grass_state():
        return {'graph': {p: describe(material, e) for p, e in reachable(material, grass_nodes).items()},
                'settings': grass_settings(grass), 'effective_coverage': {
                    path(a): float(LIB.get_material_instance_scalar_parameter_value(
                        a.get_editor_property('landscape_material'), 'GeoCity_GrassCoverage')) for a in landscapes}}

    grass_before = grass_state()
    assert grass_before == reference['grass_after']
    receipt = {'schema': 'environmentpipeline.ground_graph_refinement.v1', 'pid': os.getpid(),
               'world': named_map, 'area': area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'input_files': {k: {'file': str(v), 'sha256': sha(v)} for k, v in input_files.items()},
               'sources': sources, 'master': path(material), 'old_node_count': 820, 'old_nodes': old,
               'roots_before': {k: path(v) for k, v in roots.items()}, 'layer_names': layer_names,
               'permitted_old_edge_changes': [{'target': p, 'pin': pin} for p, pin in sorted(allowed)],
               'grass_before': grass_before, 'grass_digest_before': digest(grass_before),
               'scene_digest_before': digest(before_scene), 'added_nodes': [], 'modified_pins': [],
               'added_assets': [], 'added_parameters': {}, 'explicit_save_called': False, 'explicit_save_paths': [],
               'compile_pending': True, 'status': 'attempt_started', 'dirty_maps_before': dirty_maps_before,
               'dirty_content_before': dirty_content_before, 'existing_package_file_count': 13,
               'existing_package_files_before': {p: row['sha256'] for p, row in normalized.items()},
               'new_mask_package_files_before': mask_disk_states(),
               'reused_canonical_soil_parameter': path(soil_strength),
               'uv_rotations': False, 'fixed_uv_translations': [[0, 0], [.371, .619]],
               'macro_tile_bounds_cm': [2000, 3500],
               'soil_alpha': 'clamp(Ground_SoilBlendStrength*(.25+.75*smoothstep(.2,.8,macroR)),0,.35)',
               'tangent_normal_basis': 'explicit normal sampler; translations preserve UV basis; Normalize',
               'geometry_weight_changes_requested': False}
    with once.open('x', encoding='utf-8') as stream:
        json.dump({'pid': os.getpid(), 'world': named_map, 'status': 'attempt_started', 'receipt': str(out)}, stream, indent=2)

    def node(cls, label, **properties):
        index = len(receipt['added_nodes'])
        expression = LIB.create_material_expression(material, cls, -4000 + (index % 10) * 240, 28000 + (index // 10) * 230)
        assert expression is not None, label
        receipt['added_nodes'].append(path(expression))
        expression.set_editor_property('desc', MARK + label)
        for key, value in properties.items():
            expression.set_editor_property(key, value)
        return expression

    def link(source, output, target, input_name):
        names = list(LIB.get_material_expression_input_names(target))
        if input_name not in names and input_name == 'Input' and 'None' in names:
            input_name = 'None'
        assert input_name in names, (path(target), input_name, names)
        outputs = list(LIB.get_material_expression_output_names(source))
        assert output in outputs or (output == '' and outputs), (path(source), output, outputs)
        assert LIB.connect_material_expressions(source, output, target, input_name), (path(target), input_name)

    def binary(cls, label, a, b):
        result = node(cls, label)
        link(a, '', result, 'A'); link(b, '', result, 'B')
        return result

    def lerp(label, a, a_output, b, b_output, alpha):
        result = node(unreal.MaterialExpressionLinearInterpolate, label)
        link(a, a_output, result, 'A'); link(b, b_output, result, 'B'); link(alpha, '', result, 'Alpha')
        return result

    def clamp(label, source, low, high):
        result = node(unreal.MaterialExpressionClamp, label, min_default=low, max_default=high)
        link(source, '', result, 'Input')
        return result

    def normalise(label, source):
        result = node(unreal.MaterialExpressionNormalize, label)
        link(source, '', result, 'VectorInput')
        return result

    def sample(label, texture_object, uv, sampler):
        # Texture stays unset; require the supported input pin instead of touching
        # hidden native flags. A missing Tex pin produces a preserved partial receipt.
        result = node(unreal.MaterialExpressionTextureSample, label, sampler_type=sampler,
                      sampler_source=unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        link(uv, '', result, 'UVs')
        link(texture_object, '', result, 'Tex')
        return result

    def replace(source, target, pin):
        assert (path(target), pin) in allowed
        assert not any(r['target'] == path(target) and r['pin'] == pin for r in receipt['modified_pins'])
        link(source, '', target, pin)
        receipt['modified_pins'].append({'target': path(target), 'pin': pin,
                                        'before': old[path(target)]['edges'][pin], 'after_source': path(source)})

    try:
        xy = node(unreal.MaterialExpressionComponentMask, 'WorldXY', r=True, g=True, b=False, a=False)
        link(world_position, '', xy, 'Input')
        macro_r = node(unreal.MaterialExpressionComponentMask, 'MacroTileR', r=True, g=False, b=False, a=False)
        link(macro_tile, '', macro_r, 'Input')
        macro_size = clamp('MacroTile20to35m', macro_r, 2000., 3500.)
        macro_uv = binary(unreal.MaterialExpressionDivide, 'MacroWorldUV', xy, macro_size)
        macro_sample = sample('MacroMask', macro_object, macro_uv, macro_object.get_editor_property('sampler_type'))
        macro_red = node(unreal.MaterialExpressionComponentMask, 'MacroR', r=True, g=False, b=False, a=False)
        link(macro_sample, 'RGB', macro_red, 'Input')
        mask = node(unreal.MaterialExpressionSmoothStep, 'SharedSmoothMask', const_min=.2, const_max=.8)
        link(macro_red, '', mask, 'Value')
        offset = node(unreal.MaterialExpressionConstant2Vector, 'FixedTranslation', r=.371, g=.619)
        sampled = {}
        for layer in FLAT:
            near = binary(unreal.MaterialExpressionMultiply, layer + 'NearPatternUV', tagged(layer + 'NearUV'), pattern_scale)
            far = binary(unreal.MaterialExpressionMultiply, layer + 'FarPatternUV', tagged(layer + 'FarUV'), pattern_scale)
            near_shift = binary(unreal.MaterialExpressionAdd, layer + 'NearShiftedUV', near, offset)
            far_shift = binary(unreal.MaterialExpressionAdd, layer + 'FarShiftedUV', far, offset)
            sampled[layer] = {}
            for channel, sampler in sampler_types.items():
                texture = flat_sources[layer][channel]
                near_a = sample(layer + channel + 'NearA', texture, near, sampler)
                near_b = sample(layer + channel + 'NearB', texture, near_shift, sampler)
                far_a = sample(layer + channel + 'FarA', texture, far, sampler)
                far_b = sample(layer + channel + 'FarB', texture, far_shift, sampler)
                near_result = lerp(layer + channel + 'NearBlend', near_a, 'RGB', near_b, 'RGB', mask)
                far_result = lerp(layer + channel + 'FarBlend', far_a, 'RGB', far_b, 'RGB', mask)
                result = lerp(layer + channel + 'DistanceBlend', near_result, '', far_result, '', distance_alpha)
                if channel == 'normal':
                    result = normalise(layer + 'DecodedUnitNormal', result)
                sampled[layer][channel] = result
            for target, pin, channel in consumers[layer]:
                replace(sampled[layer][channel], target, pin)
        span = node(unreal.MaterialExpressionMultiply, 'SoilMaskSpan', const_b=.75)
        link(mask, '', span, 'A')
        base = node(unreal.MaterialExpressionAdd, 'SoilMaskBase', const_b=.25)
        link(span, '', base, 'A')
        soil_alpha = clamp('SoilAlpha0to35', binary(unreal.MaterialExpressionMultiply, 'SoilStrength', base, soil_strength), 0., .35)
        mixed = {}
        for key in ('color', 'normal', 'roughness', 'ao'):
            result = lerp('GroundSoil' + key, ground[key], '', soil[key], '', soil_alpha)
            if key == 'normal':
                result = normalise('GroundSoilUnitNormal', result)
            mixed[key] = result
            replace(result, roots[key], 'Layer Sand_01')
        after_nodes = list(LIB.get_material_expressions(material))
        after = {path(e): describe(material, e) for e in after_nodes}
        assert set(old) <= set(after) and len(after) == 820 + len(receipt['added_nodes'])
        changed = set()
        for p, row in old.items():
            assert {k: v for k, v in row.items() if k != 'edges'} == {k: v for k, v in after[p].items() if k != 'edges'}, p
            assert set(row['edges']) == set(after[p]['edges']), p
            for pin, edge in row['edges'].items():
                if edge != after[p]['edges'][pin]:
                    changed.add((p, pin))
                    assert (p, pin) in allowed, (p, pin)
        assert changed == allowed and len(receipt['modified_pins']) == 16
        roots_after = {k: LIB.get_material_property_input_node(material, prop) for k, prop in PROPERTIES.items()}
        assert {k: path(v) for k, v in roots_after.items()} == receipt['roots_before']
        grass_after = grass_state()
        assert grass_after == grass_before
        sources_after, actors_after = guard(assignment, named_map)
        assert sources_after == sources and scene_state(actors_after) == before_scene
        dirty_maps = [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
        dirty_content = [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
        assert dirty_maps == [] and set(dirty_content) == expected_dirty, (dirty_maps, dirty_content)
        assert all(sha(p) == row['sha256'] for p, row in normalized.items())
        for family in ('preserved_files', 'sealed_files'):
            assert all(sha(ROOT / p) == expected for p, expected in manifest[family].items()), family
        assert mask_disk_states() == receipt['new_mask_package_files_before']
        sampled_texture_refs = {layer: {channel: path(texture) for channel, texture in row.items()}
                                for layer, row in flat_sources.items()}
        new_sampler_rows = {path(e): {'sampler_type': plain(e.get_editor_property('sampler_type')),
                                      'sampler_source': plain(e.get_editor_property('sampler_source'))}
                            for e in after_nodes if path(e) in receipt['added_nodes']
                            and isinstance(e, unreal.MaterialExpressionTextureSample)}
        receipt.update(status='refinement_verified_no_explicit_save_compile_pending',
                       old_node_preservation_verified=True, added_node_count=len(receipt['added_nodes']),
                       nodes_after=after, roots_after={k: path(v) for k, v in roots_after.items()},
                       actual_modified_old_edges=[{'target': p, 'pin': pin} for p, pin in sorted(changed)],
                       grass_after=grass_after, grass_digest_after=digest(grass_after),
                       scene_digest_after=digest(scene_state(actors_after)), dirty_maps=dirty_maps, dirty_content=dirty_content,
                       existing_package_files_after={p: disk_state(p) for p in normalized},
                       existing_package_files_unchanged=True, new_mask_package_files_after=mask_disk_states(),
                       sampler_nodes=new_sampler_rows, reused_texture_objects=sampled_texture_refs,
                       shared_mask=path(mask), shared_soil_alpha=path(soil_alpha), shared_distance_alpha=path(distance_alpha),
                       sampled_outputs={layer: {channel: path(e) for channel, e in row.items()} for layer, row in sampled.items()},
                       ground_soil_outputs={k: path(v) for k, v in mixed.items()})
    except Exception as error:
        receipt.update(status='failed_no_explicit_save_requires_root_review', error=repr(error),
                       dirty_maps=[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
                       dirty_content=[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],
                       existing_package_files_after={p: disk_state(p) for p in normalized},
                       new_mask_package_files_after=mask_disk_states())
        receipt['existing_package_files_unchanged'] = all(
            row.get('sha256') == normalized[p]['sha256'] for p, row in receipt['existing_package_files_after'].items())
        try:
            current = list(LIB.get_material_expressions(material))
            receipt['nodes_at_failure'] = {path(e): describe(material, e) for e in current}
            receipt['added_nodes_at_failure'] = sorted(set(receipt['nodes_at_failure']) - set(old))
            receipt['roots_at_failure'] = {k: path(LIB.get_material_property_input_node(material, prop))
                                           for k, prop in PROPERTIES.items()}
        except Exception as snapshot_error:
            receipt['failure_snapshot_error'] = repr(snapshot_error)
        out.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        once.write_text(json.dumps({'pid': os.getpid(), 'world': named_map, 'status': receipt['status'], 'receipt': str(out)}, indent=2), encoding='utf-8')
        raise
    out.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    once.write_text(json.dumps({'pid': os.getpid(), 'world': named_map, 'status': receipt['status'], 'receipt': str(out)}, indent=2), encoding='utf-8')
    return {'receipt': str(out), 'status': receipt['status'], 'added_node_count': receipt['added_node_count'],
            'modified_old_edges': receipt['actual_modified_old_edges'], 'explicit_save_called': False,
            'existing_package_files_unchanged': True, 'compile_pending': True, 'dirty_content': receipt['dirty_content']}


if 'ARGS' in globals():
    RESULT = refine(ARGS)

