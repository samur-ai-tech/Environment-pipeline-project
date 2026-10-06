"""Sand-only cell translation sampler; root executes only after independent review.

Inspect ARGS: mode="inspect", baseline_receipt, graph_receipt, backup_manifest.
Apply additionally requires preflight_receipt and compiler_review; manifest binds
this exact script, both fresh receipts, preflight and independent review SHA256.
Verify ARGS: reference_receipt+sha256, fresh baseline_receipt+sha256,
backup_manifest+sha256, master_package_sha256, require_clean(default True), label.
Fresh 915-node clean original world; retain every old node/property except four
explicit Sand consumer edges. No assets/parameters, compile/save, actor edits,
Cook/Bake, residency changes, cleanup, rollback execution or automatic replay.
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


def guard(assignment, named_map, require_authoring=True):
    lease = [s for s in (ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(
        encoding='utf-8-sig').splitlines() if s.strip()][-1]
    fields = dict(token.split('=', 1) for token in lease.split() if '=' in token)
    assert fields.get('OWNER') == 'CODEX_GROUND_PAINTING'
    assert fields.get('activation') in (('GROUND_AUTHORING',) if require_authoring else
                                       ('GROUND_AUTHORING', 'STARTUP_INSPECTION_ONLY'))
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


REVISION_MARK = MARK
REFINEMENT_MARK = 'GeoCity_GroundRefinement_20261005:'
MARK = 'GeoCity_GroundStochastic_20261005:'
SCRIPT = HERE / 'native_graph_stochastic.py'
HASH_CODE = '''uint2 k = uint2(int2(Cell));
uint n = (k.x * 0x8da6b343u) ^ (k.y * 0xd8163841u);
uint2 h = uint2(n ^ 0x68bc21ebu, n ^ 0x02e5be93u);
h ^= h >> 16; h *= 0x7feb352du;
h ^= h >> 15; h *= 0x846ca68bu;
h ^= h >> 16;
return float2(h & 0x00ffffffu) * (1.0 / 16777216.0);'''
OLD_DESCRIBE = describe
OLD_SCENE = scene_state
OLD_PLAIN = plain


def plain(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if value is not None and all(hasattr(value, c) for c in ('a', 'b', 'c', 'd')):
        return [int(getattr(value, c)) for c in ('a', 'b', 'c', 'd')]
    result = OLD_PLAIN(value)
    assert not isinstance(result, str) or '0x' not in result, 'Transient address in snapshot'
    return result


def describe(material, expression):
    row = OLD_DESCRIBE(material, expression)
    row['input_names'] = list(LIB.get_material_expression_input_names(expression))
    row['output_names'] = list(LIB.get_material_expression_output_names(expression))
    for key in ('const_exponent', 'const_min', 'const_max', 'sampler_source', 'mip_value_mode',
                'automatic_view_mip_bias', 'const_mip_value', 'const_coordinate', 'gather_mode',
                'transform_source_type', 'transform_type', 'expression_guid', 'material_expression_guid',
                'material_expression_editor_x', 'material_expression_editor_y', 'group', 'sort_priority',
                'code', 'output_type', 'description'):
        value = safe(expression, key)
        if value is not None:
            row['properties'][key] = plain(value)
    if isinstance(expression, unreal.MaterialExpressionCustom):
        row['custom_inputs'] = [str(x.get_editor_property('input_name'))
                                for x in expression.get_editor_property('inputs')]
        row['custom_outputs'] = [{'name': str(x.get_editor_property('output_name')),
                                  'type': plain(x.get_editor_property('output_type'))}
                                 for x in expression.get_editor_property('additional_outputs')]
        row['includes'] = list(expression.get_editor_property('include_file_paths'))
        row['custom_defines'] = [{'name': str(x.get_editor_property('define_name')),
                                  'value': str(x.get_editor_property('define_value'))}
                                 for x in expression.get_editor_property('additional_defines')]
        row['custom_clip_instruction'] = plain(expression.get_editor_property('contains_clip_instruction'))
        row['custom_show_code'] = bool(expression.get_editor_property('show_code'))
    return row


def material_state(material, instance):
    result = {'path': path(instance), 'parent': path(instance.get_editor_property('parent')),
              'scalars': {str(k): float(LIB.get_material_instance_scalar_parameter_value(instance, k))
                          for k in LIB.get_scalar_parameter_names(material)},
              'vectors': {str(k): plain(LIB.get_material_instance_vector_parameter_value(instance, k))
                          for k in LIB.get_vector_parameter_names(material)},
              'textures': {str(k): path(LIB.get_material_instance_texture_parameter_value(instance, k))
                           for k in LIB.get_texture_parameter_names(material)},
              'override_guid_capture': 'GUID_NOT_CAPTURED_PYTHON_UNEXPOSED'}
    for kind in ('scalar', 'vector', 'texture'):
        result[kind + '_overrides'] = []
        for value in instance.get_editor_property(kind + '_parameter_values'):
            info = value.get_editor_property('parameter_info')
            result[kind + '_overrides'].append({'name': str(info.get_editor_property('name')),
                'association': plain(info.get_editor_property('association')),
                'index': int(info.get_editor_property('index')),
                'value': plain(value.get_editor_property('parameter_value'))})
    return result


def scene_state(actors):
    result = OLD_SCENE(actors)
    result['native_mesh_components'] = sorted([
        {'actor': path(a), 'component': path(c), 'mesh': path(c.get_editor_property('static_mesh')),
         'materials': [path(c.get_material(i)) for i in range(c.get_num_materials())],
         'instances': c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1}
        for a in actors if not isinstance(a, unreal.LandscapeProxy)
        for c in a.get_components_by_class(unreal.StaticMeshComponent)], key=lambda x: x['component'])
    return result


def load_document(file):
    file = Path(file).resolve(strict=True)
    assert file.is_relative_to(HERE) and file.suffix == '.json', str(file)
    return file, json.loads(file.read_text(encoding='utf-8-sig'))


def same_binding(manifest, key, file):
    assert Path(manifest[key]).resolve(strict=True) == file
    assert manifest[key + '_sha256'] == sha(file), key


def check_reference(current, reference):
    assert set(current) == set(reference)
    for p, row in reference.items():
        live = current[p]
        assert live['class'] == row['class'] and live['input_names'] == row['input_names'], p
        assert live['output_names'] == row['output_names'], p
        assert [live['edges'][n]['source'] for n in live['input_names']] == row['inputs'], p
        for edge in live['edges'].values():
            if edge['source']:
                assert edge['output'] == row['input_outputs'][edge['source']], p
        assert all(live['properties'].get(k) == v for k, v in row['properties'].items()), p
        if 'layers' in row:
            assert [{'name': e['layer_name'], 'type': e['blend_type']} for e in live['layers']] == row['layers'], p
        if 'grass_types' in row:
            assert live['grass_types'] == row['grass_types'], p


def stochastic(args):
    mode = args.get('mode', 'inspect')
    assert mode in ('inspect', 'apply')
    assignment = json.loads((HERE / 'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    sources, actors = guard(assignment, named_map, require_authoring=(mode == 'apply'))
    files, docs = {}, {}
    for key in ('baseline_receipt', 'graph_receipt', 'backup_manifest'):
        files[key], docs[key] = load_document(args[key])
    baseline, reference, manifest = (docs[k] for k in ('baseline_receipt', 'graph_receipt', 'backup_manifest'))
    assert baseline['pid'] == reference['pid'] == manifest['pid'] == manifest['editor_pid'] == os.getpid()
    assert baseline['world'] == reference['world'] == manifest['world'] == named_map
    assert baseline['sources'] == sources and baseline['graph_expression_count'] == reference['graph_count'] == 915
    assert reference['graph_preserved'] is True
    assert reference['signature_sha256'] == digest(reference['signature']) == '4d46be198ff77fbd684ff44e31eedc51a5b38038a84349992b53880a296db87f'
    assert baseline['cooking_paused'] and not baseline['autosave'] and not any(baseline['callbacks'].values())
    assert len(baseline['hdas']) == 1 and all(not h['auto_cook'] and not h['auto_bake'] for h in baseline['hdas'])
    assert manifest['ready'] is True and manifest['ordinary_generation_authorized'] is False
    assert manifest['execution_thread_id'] == THREAD and manifest['new_asset_paths'] == []
    assert set(manifest['derived_texture_paths']) == set(MASK_COPIES.values())
    same_binding(manifest, 'baseline_receipt', files['baseline_receipt'])
    same_binding(manifest, 'graph_receipt', files['graph_receipt'])
    same_binding(manifest, 'helper', SCRIPT.resolve(strict=True))
    normalized = {str(Path(k).resolve(strict=True)): row for k, row in manifest['file_bindings'].items()}
    required = {package_file(MASTER), package_file(BASE), package_file(GRASS),
                *(package_file(p) for p in MASK_COPIES.values()),
                *(package_file(p.split('.')[0]) for p in assignment['material_contract']['area_instances'].values()),
                *(package_file(p, '.umap') for p in assignment['original_maps'].values())}
    assert len(normalized) == 17 and {str(p.resolve(strict=True)) for p in required} <= set(normalized)

    def verify_files():
        for source, row in normalized.items():
            backup = Path(row['backup']).resolve(strict=True)
            assert Path(source).is_relative_to(ROOT) and backup.is_relative_to(REV / 'SamplerBefore')
            assert sha(source) == sha(backup) == row['sha256'], source
        for family, count in (('preserved_files', 65), ('sealed_files', 17)):
            assert len(manifest[family]) == count
            for relative, expected in manifest[family].items():
                source = (ROOT / relative).resolve(strict=True)
                assert source.is_relative_to(ROOT) and sha(source) == expected, relative

    verify_files()
    dirty = lambda: {'maps': [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
                     'content': [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
    assert dirty() == {'maps': [], 'content': []}
    assert baseline['dirty_maps'] == baseline['dirty_content'] == []
    material = unreal.load_asset(MASTER)
    base = unreal.load_asset(BASE)
    child = unreal.load_asset(assignment['material_contract']['area_instances'][area])
    assert isinstance(material, unreal.Material) and isinstance(child, unreal.MaterialInstanceConstant)
    assert child.get_editor_property('parent') == base and base.get_editor_property('parent') == material
    settings = {k: plain(material.get_editor_property(k)) for k in
                ('tangent_space_normal', 'enable_tessellation', 'blend_mode', 'shading_model',
                 'material_domain', 'two_sided', 'use_material_attributes')}
    assert settings['tangent_space_normal'] is True and settings['enable_tessellation'] is False
    roots = {k: LIB.get_material_property_input_node(material, prop) for k, prop in PROPERTIES.items()}
    assert {k: path(roots[k]) for k in reference['signature']['roots']} == reference['signature']['roots']
    nodes = list(LIB.get_material_expressions(material))
    assert len(nodes) == 915 and not any(str(safe(e, 'desc')).startswith(MARK) for e in nodes)
    owned = {path(e): e for e in nodes}
    old = {p: describe(material, e) for p, e in owned.items()}
    check_reference(old, reference['signature']['graph'])
    layers = None
    for key in ('color', 'normal', 'roughness', 'ao'):
        assert isinstance(roots[key], unreal.MaterialExpressionLandscapeLayerBlend)
        entries = roots[key].get_editor_property('layers')
        names = [str(e.get_editor_property('layer_name')) for e in entries]
        layers = names if layers is None else layers
        assert names == layers and len(names) == len(set(names)) == 69
        assert all(e.get_editor_property('blend_type') == unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND for e in entries)
    before_scene = scene_state(actors)
    assert before_scene['transforms'] == baseline['actor_transforms']
    assert before_scene['native_mesh_components'] == sorted(baseline['native_mesh_components'], key=lambda x: x['component'])
    landscapes = [a for a in actors if isinstance(a, unreal.LandscapeProxy)]
    assert sorted(path(a) for a in landscapes) == sorted(l['path'] for l in baseline['landscapes'])
    for actor in landscapes:
        scale = actor.get_actor_scale3d()
        assert scale.x == scale.y == 100 and actor.get_editor_property('landscape_material') == child
    instances = {p: unreal.load_asset(p) for p in [BASE, *assignment['material_contract']['area_instances'].values()]}
    instance_before = {p: material_state(material, mi) for p, mi in instances.items()}
    assert abs(instance_before[path_key(instances, child)]['scalars']['GeoCity_CellScale'] - .1) < 1e-6

    def tagged(mark, label):
        return one((e for e in nodes if safe(e, 'desc') == mark + label), label)

    def upstream(expression, pin):
        return one((e for name, e in inputs(material, expression) if name == pin and e), pin)

    distance = tagged(REVISION_MARK, 'SharedDistanceAlpha')
    scale_control = parameter(owned, 'GeoCity_CellScale', unreal.MaterialExpressionScalarParameter)
    uv = {s: tagged(REFINEMENT_MARK, 'Sand_01' + s + 'PatternUV') for s in ('Near', 'Far')}
    sampler_types = {'color': unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                     'normal': unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                     'mask': unreal.MaterialSamplerType.SAMPLERTYPE_MASKS}
    textures = {}
    for channel, sampler in sampler_types.items():
        textures[channel] = upstream(tagged(REFINEMENT_MARK, 'Sand_01' + channel + 'NearA'), 'Tex')
        assert isinstance(textures[channel], unreal.MaterialExpressionTextureObjectParameter)
        assert textures[channel].get_editor_property('sampler_type') == sampler
        for phase in ('NearA', 'NearB', 'FarA', 'FarB'):
            assert upstream(tagged(REFINEMENT_MARK, 'Sand_01' + channel + phase), 'Tex') == textures[channel]
    normal_texture = textures['normal'].get_editor_property('texture')
    assert path(normal_texture) == SURFACE + '/Textures/T_Sand_01_Normal_GeoCity.T_Sand_01_Normal_GeoCity'
    assert normal_texture.get_editor_property('srgb') is False
    assert normal_texture.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_NORMALMAP
    mask_texture = textures['mask'].get_editor_property('texture')
    assert path(mask_texture).split('.')[0] == MASK_COPIES['Sand_01']
    assert mask_texture.get_editor_property('srgb') is False
    assert mask_texture.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_MASKS
    consumers = [(tagged(REVISION_MARK, 'Sand_01TintedColor'), 'A', 'color',
                  tagged(REFINEMENT_MARK, 'Sand_01colorDistanceBlend')),
                 (tagged(REVISION_MARK, 'Sand_01NormalIntensity'), 'NormalMap', 'normal',
                  tagged(REFINEMENT_MARK, 'Sand_01DecodedUnitNormal')),
                 (tagged(REVISION_MARK, 'Sand_01PackedRoughnessR'), 'None', 'mask',
                  tagged(REFINEMENT_MARK, 'Sand_01maskDistanceBlend')),
                 (tagged(REVISION_MARK, 'Sand_01PackedAOG'), 'None', 'mask',
                  tagged(REFINEMENT_MARK, 'Sand_01maskDistanceBlend'))]
    assert all(upstream(target, pin) == source for target, pin, channel, source in consumers)
    allowed = {(path(target), pin) for target, pin, channel, source in consumers}
    assert len(allowed) == 4
    grass = unreal.load_asset(GRASS)
    grass_nodes = [e for e in nodes if isinstance(e, unreal.MaterialExpressionLandscapeGrassOutput)]
    assert len(grass_nodes) == 1

    def grass_state():
        return {'graph': {p: describe(material, e) for p, e in reachable(material, grass_nodes).items()},
                'settings': grass_settings(grass), 'effective_coverage': {
                    path(a): float(LIB.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage'))
                    for a in landscapes}}

    before_grass = grass_state()
    snapshot = {'schema': 'environmentpipeline.ground_stochastic_preflight.v1', 'pid': os.getpid(),
                'world': named_map, 'area': area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'status': 'inspect_only_clean_915', 'helper_sha256': sha(SCRIPT), 'sources': sources,
                'input_files': {k: {'file': str(files[k]), 'sha256': sha(files[k])}
                                for k in ('baseline_receipt', 'graph_receipt')},
                'old_node_count': 915, 'old_nodes': old, 'roots': {k: path(v) for k, v in roots.items()},
                'material_settings': settings, 'layers': layers, 'scene': before_scene,
                'instances': instance_before, 'grass': before_grass, 'dirty': dirty(),
                'allowed_old_edges': [{'target': p, 'pin': pin} for p, pin in sorted(allowed)],
                'cell_hash_code_sha256': hashlib.sha256(HASH_CODE.encode()).hexdigest(),
                'no_native_mutation': True}
    if mode == 'inspect':
        verify_files()
        sources_after, actors_after = guard(assignment, named_map, require_authoring=(mode == 'apply'))
        assert sources_after == sources and scene_state(actors_after) == before_scene and dirty() == snapshot['dirty']
        out = REV / ('STOCHASTIC_PREFLIGHT_PID' + str(os.getpid()) + '.json')
        assert not out.exists(), 'Fresh snapshot requires root review, never overwrite.'
        out.write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
        return {'status': snapshot['status'], 'receipt': str(out), 'sha256': sha(out),
                'allowed_old_edges': snapshot['allowed_old_edges'], 'native_mutation': False}
    assert manifest['ready_for_graph_revision'] is True
    files['preflight_receipt'], preflight = load_document(args['preflight_receipt'])
    files['compiler_review'], review = load_document(args['compiler_review'])
    same_binding(manifest, 'preflight_receipt', files['preflight_receipt'])
    same_binding(manifest, 'compiler_review', files['compiler_review'])
    assert preflight['pid'] == review['pid'] == os.getpid() and preflight['world'] == review['world'] == named_map
    assert review['status'] == 'APPROVED_FOR_BOUNDED_NATIVE_COMPILATION' and review['execution_thread_id'] == THREAD
    assert review['helper_sha256'] == sha(SCRIPT) and review['preflight_receipt_sha256'] == sha(files['preflight_receipt'])
    assert review['cell_hash_code_sha256'] == snapshot['cell_hash_code_sha256']
    assert review['allowed_old_edges'] == snapshot['allowed_old_edges']
    assert preflight['status'] == 'inspect_only_clean_915' and preflight['helper_sha256'] == sha(SCRIPT)
    assert all(preflight[k] == snapshot[k] for k in ('sources', 'input_files', 'old_nodes', 'roots',
        'material_settings', 'layers', 'scene', 'instances', 'grass', 'dirty', 'allowed_old_edges', 'cell_hash_code_sha256'))
    once = REV / 'GRAPH_STOCHASTIC_ONCE.json'
    out = REV / ('GRAPH_STOCHASTIC_PID' + str(os.getpid()) + '.json')
    assert not once.exists() and not out.exists(), 'No replay/cleanup; partial state requires root review.'
    receipt = {**snapshot, 'schema': 'environmentpipeline.ground_stochastic.v1', 'status': 'attempt_started',
               'input_files': {k: {'file': str(v), 'sha256': sha(v)} for k, v in files.items()},
               'added_nodes': [], 'modified_pins': [], 'added_assets': [], 'added_parameters': {},
               'explicit_save_called': False, 'explicit_compile_called': False, 'compile_pending': True,
               'rollback_executed': False, 'no_native_mutation': False,
               'existing_package_files_before': {p: disk_state(p) for p in normalized},
               'rollback_snapshot': {'old_nodes': old, 'roots': snapshot['roots'], 'instances': instance_before,
                                     'scene': before_scene, 'grass': before_grass,
                                     'package_backups': normalized},
               'planned_expression_count': 100, 'planned_texture_sample_count': 24,
               'cell_rule': 'Q = untranslatedUV * max(GeoCity_CellScale, .01)',
               'weights': 'bilinear weights of quintic(frac(Q)), shared across C/N/M',
               'uv_rotation': False, 'packed_height_used': False,
               'mip_derivatives': 'DDX/DDY(untranslated Near/FarPatternUV)',
               'shader_cost_measured': False, 'streaming_residency_proven': False}
    with once.open('x', encoding='utf-8') as stream:
        json.dump({'pid': os.getpid(), 'world': named_map, 'status': receipt['status'], 'receipt': str(out)}, stream, indent=2)
    out.write_text(json.dumps(receipt, indent=2), encoding='utf-8')

    def node(cls, label, **properties):
        index = len(receipt['added_nodes'])
        result = LIB.create_material_expression(material, cls, -4000 + (index % 10) * 240, 32000 + (index // 10) * 230)
        assert result is not None, label
        receipt['added_nodes'].append(path(result))
        result.set_editor_property('desc', MARK + label)
        for key, value in properties.items():
            result.set_editor_property(key, value)
        return result

    def link(source, output, target, name):
        names = list(LIB.get_material_expression_input_names(target))
        assert name in names, (path(target), name, names)
        outputs = list(LIB.get_material_expression_output_names(source))
        assert output in outputs or (output == '' and outputs), (path(source), output, outputs)
        assert LIB.connect_material_expressions(source, output, target, name)

    def single(source, target):
        names = list(LIB.get_material_expression_input_names(target))
        assert len(names) == 1, (path(target), names)
        link(source, '', target, names[0])

    def binary(cls, label, a, b=None, **properties):
        result = node(cls, label, **properties)
        link(a, '', result, 'A')
        if b is not None:
            link(b, '', result, 'B')
        return result

    def lerp(label, a, ao, b, bo, alpha):
        result = node(unreal.MaterialExpressionLinearInterpolate, label)
        link(a, ao, result, 'A'); link(b, bo, result, 'B'); link(alpha, '', result, 'Alpha')
        return result

    try:
        cell_scale = binary(unreal.MaterialExpressionMax, 'CellScaleMin001', scale_control, const_b=.01)
        neighbors = [None] + [node(unreal.MaterialExpressionConstant2Vector, 'CellNeighbor' + str(i), r=x, g=y)
                               for i, (x, y) in enumerate(((1., 0.), (0., 1.), (1., 1.)), 1)]
        per_scale, details = {}, {}
        for scale_name, base_uv in uv.items():
            q = binary(unreal.MaterialExpressionMultiply, scale_name + 'CellQ', base_uv, cell_scale)
            cell = node(unreal.MaterialExpressionFloor, scale_name + 'CellID'); single(q, cell)
            fraction = node(unreal.MaterialExpressionFrac, scale_name + 'CellFraction'); single(q, fraction)
            f2 = binary(unreal.MaterialExpressionMultiply, scale_name + 'Fraction2', fraction, fraction)
            f3 = binary(unreal.MaterialExpressionMultiply, scale_name + 'Fraction3', f2, fraction)
            six = binary(unreal.MaterialExpressionMultiply, scale_name + 'Fraction6', fraction, const_b=6.)
            minus = binary(unreal.MaterialExpressionAdd, scale_name + 'Minus15', six, const_b=-15.)
            polynomial = binary(unreal.MaterialExpressionMultiply, scale_name + 'Polynomial', fraction, minus)
            plus = binary(unreal.MaterialExpressionAdd, scale_name + 'Plus10', polynomial, const_b=10.)
            smooth = binary(unreal.MaterialExpressionMultiply, scale_name + 'Quintic', f3, plus)
            sx = node(unreal.MaterialExpressionComponentMask, scale_name + 'SmoothX', r=True, g=False, b=False, a=False)
            sy = node(unreal.MaterialExpressionComponentMask, scale_name + 'SmoothY', r=False, g=True, b=False, a=False)
            single(smooth, sx); single(smooth, sy)
            dx = node(unreal.MaterialExpressionDDX, scale_name + 'UntranslatedDDX'); single(base_uv, dx)
            dy = node(unreal.MaterialExpressionDDY, scale_name + 'UntranslatedDDY'); single(base_uv, dy)
            phase_uvs, hashes = [], []
            for i, neighbor in enumerate(neighbors):
                identity = cell if neighbor is None else binary(unreal.MaterialExpressionAdd,
                    scale_name + 'CellIdentity' + str(i), cell, neighbor)
                custom_input = unreal.CustomInput()
                custom_input.set_editor_property('input_name', 'Cell')
                hashed = node(unreal.MaterialExpressionCustom, scale_name + 'Hash' + str(i),
                    code=HASH_CODE, output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT2,
                    inputs=[custom_input], additional_outputs=[], include_file_paths=[])
                assert list(LIB.get_material_expression_input_names(hashed)) == ['Cell']
                assert hashed.get_editor_property('output_type') == unreal.CustomMaterialOutputType.CMOT_FLOAT2
                link(identity, '', hashed, 'Cell')
                hashes.append(path(hashed))
                phase_uvs.append(binary(unreal.MaterialExpressionAdd, scale_name + 'TranslatedUV' + str(i), base_uv, hashed))
            per_scale[scale_name] = {}
            for channel, sampler in sampler_types.items():
                samples = []
                for i, phase_uv in enumerate(phase_uvs):
                    sample = node(unreal.MaterialExpressionTextureSample, scale_name + channel + 'Phase' + str(i),
                        sampler_type=sampler, sampler_source=unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS,
                        mip_value_mode=unreal.TextureMipValueMode.TMVM_DERIVATIVE)
                    # Actual reflected pin names are required; absent pins fail before old rewiring.
                    link(phase_uv, '', sample, 'UVs'); link(textures[channel], '', sample, 'Tex')
                    link(dx, '', sample, 'DDX(UVs)'); link(dy, '', sample, 'DDY(UVs)')
                    samples.append(sample)
                bottom = lerp(scale_name + channel + 'Bottom', samples[0], 'RGB', samples[1], 'RGB', sx)
                top = lerp(scale_name + channel + 'Top', samples[2], 'RGB', samples[3], 'RGB', sx)
                per_scale[scale_name][channel] = lerp(scale_name + channel + 'CellBlend', bottom, '', top, '', sy)
            details[scale_name] = {'untranslated_uv': path(base_uv), 'cell_q': path(q), 'cell_floor': path(cell),
                'smooth_x': path(sx), 'smooth_y': path(sy), 'hashes': hashes,
                'translated_uvs': [path(p) for p in phase_uvs], 'ddx': path(dx), 'ddy': path(dy)}
        final = {}
        for channel in sampler_types:
            final[channel] = lerp(channel + 'DistanceBlend', per_scale['Near'][channel], '',
                                  per_scale['Far'][channel], '', distance)
            if channel == 'normal':
                normalized_normal = node(unreal.MaterialExpressionNormalize, 'DecodedUnitNormal')
                single(final[channel], normalized_normal)
                final[channel] = normalized_normal
        assert len(receipt['added_nodes']) == 100
        for target, pin, channel, previous in consumers:
            assert (path(target), pin) in allowed and upstream(target, pin) == previous
            link(final[channel], '', target, pin)
            receipt['modified_pins'].append({'target': path(target), 'pin': pin,
                'before': old[path(target)]['edges'][pin], 'after_source': path(final[channel])})
        after_nodes = list(LIB.get_material_expressions(material))
        after = {path(e): describe(material, e) for e in after_nodes}
        assert set(old) <= set(after) and len(after) == 1015
        changed = set()
        for p, row in old.items():
            assert {k: v for k, v in row.items() if k != 'edges'} == {k: v for k, v in after[p].items() if k != 'edges'}, p
            assert set(row['edges']) == set(after[p]['edges']), p
            for pin, edge in row['edges'].items():
                if edge != after[p]['edges'][pin]:
                    changed.add((p, pin))
        assert changed == allowed and len(receipt['modified_pins']) == 4
        assert {k: path(LIB.get_material_property_input_node(material, prop)) for k, prop in PROPERTIES.items()} == snapshot['roots']
        assert {k: plain(material.get_editor_property(k)) for k in settings} == settings
        assert grass_state() == before_grass
        assert {p: material_state(material, mi) for p, mi in instances.items()} == instance_before
        sources_after, actors_after = guard(assignment, named_map)
        assert sources_after == sources and scene_state(actors_after) == before_scene
        assert dirty() == {'maps': [], 'content': [MASTER]}, dirty()
        verify_files()
        samplers = {path(e): describe(material, e) for e in after_nodes
                    if path(e) in receipt['added_nodes'] and isinstance(e, unreal.MaterialExpressionTextureSample)}
        assert len(samplers) == 24
        receipt.update(status='stochastic_verified_no_explicit_save_compile_pending',
            old_node_preservation_verified=True, added_node_count=100, graph_count=1015,
            nodes_after=after, actual_modified_old_edges=[{'target': p, 'pin': pin} for p, pin in sorted(changed)],
            grass_after=grass_state(), grass_digest_before=digest(before_grass), grass_digest_after=digest(grass_state()),
            scene_digest_before=digest(before_scene), scene_digest_after=digest(scene_state(actors_after)),
            dirty_after=dirty(), existing_package_files_after={p: disk_state(p) for p in normalized},
            existing_package_files_unchanged=True, numeric_hash_code=HASH_CODE,
            scale_details=details, sampler_nodes=samplers, reused_texture_objects={k: path(v) for k, v in textures.items()},
            shared_distance_alpha=path(distance), sampled_outputs={k: path(v) for k, v in final.items()})
    except Exception as error:
        receipt.update(status='failed_no_explicit_save_requires_root_review', error=repr(error), dirty_after=dirty(),
                       existing_package_files_after={p: disk_state(p) for p in normalized})
        receipt['existing_package_files_unchanged'] = all(
            row.get('sha256') == normalized[p]['sha256'] for p, row in receipt['existing_package_files_after'].items())
        try:
            current = list(LIB.get_material_expressions(material))
            receipt['nodes_at_failure'] = {path(e): describe(material, e) for e in current}
            receipt['added_nodes_at_failure'] = sorted(set(receipt['nodes_at_failure']) - set(old))
            receipt['roots_at_failure'] = {k: path(LIB.get_material_property_input_node(material, prop))
                                           for k, prop in PROPERTIES.items()}
            receipt['grass_at_failure'] = grass_state()
            receipt['scene_at_failure'] = scene_state(list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()))
            receipt['instances_at_failure'] = {p: material_state(material, mi) for p, mi in instances.items()}
        except Exception as snapshot_error:
            receipt['failure_snapshot_error'] = repr(snapshot_error)
        out.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        once.write_text(json.dumps({'pid': os.getpid(), 'world': named_map, 'status': receipt['status'], 'receipt': str(out)}, indent=2), encoding='utf-8')
        raise
    out.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    once.write_text(json.dumps({'pid': os.getpid(), 'world': named_map, 'status': receipt['status'], 'receipt': str(out)}, indent=2), encoding='utf-8')
    return {'receipt': str(out), 'status': receipt['status'], 'graph_count': 1015, 'added_node_count': 100,
            'modified_old_edges': receipt['actual_modified_old_edges'], 'explicit_save_called': False,
            'explicit_compile_called': False, 'shader_cost_measured': False, 'compile_pending': True}


def path_key(instances, target):
    return one((p for p, instance in instances.items() if instance == target), 'current instance key')


def verify_stochastic(args):
    """Read-only identity capture, valid after compile and across fresh processes."""
    assignment = json.loads((HERE / 'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    sources, actors = guard(assignment, named_map, require_authoring=False)
    files, documents = {}, {}
    for key in ('reference_receipt', 'baseline_receipt', 'backup_manifest'):
        files[key], documents[key] = load_document(args[key])
        assert sha(files[key]) == args[key + '_sha256'], key
    reference, baseline, manifest = (documents[k] for k in ('reference_receipt', 'baseline_receipt', 'backup_manifest'))
    assert reference['status'] == 'stochastic_verified_no_explicit_save_compile_pending'
    assert reference['old_node_preservation_verified'] and reference['graph_count'] == 1015
    assert reference['helper_sha256'] == manifest['helper_sha256'] == sha(SCRIPT)
    assert baseline['pid'] == os.getpid() and baseline['world'] == named_map
    assert reference['world'] in assignment['original_maps'].values()
    same_area = reference['world'] == named_map
    assert baseline['graph_expression_count'] == 1015 and baseline['sources'] == sources
    assert manifest['execution_thread_id'] == THREAD and manifest['ordinary_generation_authorized'] is False
    assert manifest['ready'] is True and manifest['new_asset_paths'] == []
    same_binding(manifest, 'helper', SCRIPT.resolve(strict=True))
    # The original 915 package is still backed up. Only master may differ on disk;
    # caller binds its exact current hash from the named-save/persistence record.
    assert len(manifest['file_bindings']) == 17
    for filename, row in manifest['file_bindings'].items():
        source = Path(filename).resolve(strict=True)
        backup = Path(row['backup']).resolve(strict=True)
        assert source.is_relative_to(ROOT) and backup.is_relative_to(REV / 'SamplerBefore')
        assert sha(backup) == row['sha256'], filename
        expected = args['master_package_sha256'] if source == package_file(MASTER) else row['sha256']
        assert sha(source) == expected, filename
    for family, count in (('preserved_files', 65), ('sealed_files', 17)):
        assert len(manifest[family]) == count
        for relative, expected in manifest[family].items():
            source = (ROOT / relative).resolve(strict=True)
            assert source.is_relative_to(ROOT) and sha(source) == expected, relative
    dirty = lambda: {'maps': [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
                     'content': [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
    dirty_before = dirty()
    assert dirty_before['maps'] == baseline['dirty_maps'] == []
    assert set(dirty_before['content']) == set(baseline['dirty_content'])
    assert not dirty_before['content'] if args.get('require_clean', True) else set(dirty_before['content']) <= {MASTER}
    material = unreal.load_asset(MASTER)
    nodes = list(LIB.get_material_expressions(material))
    current = {path(e): describe(material, e) for e in nodes}
    assert len(current) == 1015 and current == reference['nodes_after'], 'Complete graph identity mismatch'
    roots = {k: path(LIB.get_material_property_input_node(material, prop)) for k, prop in PROPERTIES.items()}
    assert roots == reference['roots']
    settings = {k: plain(material.get_editor_property(k)) for k in reference['material_settings']}
    assert settings == reference['material_settings']
    scene = scene_state(actors)
    assert scene['transforms'] == baseline['actor_transforms']
    assert scene['native_mesh_components'] == sorted(baseline['native_mesh_components'], key=lambda x: x['component'])
    # Do not compare address-bearing editor layer reprs across editor processes.
    clean_landscape = lambda rows: [{k: v for k, v in row.items() if k != 'layers'} for row in rows]
    if same_area:
        assert scene['transforms'] == reference['scene']['transforms']
        assert scene['native_mesh_components'] == reference['scene']['native_mesh_components']
        assert clean_landscape(scene['landscapes']) == clean_landscape(reference['scene']['landscapes'])
    child = unreal.load_asset(assignment['material_contract']['area_instances'][area])
    landscapes = [a for a in actors if isinstance(a, unreal.LandscapeProxy)]
    assert all(a.get_editor_property('landscape_material') == child for a in landscapes)
    assert sorted(path(a) for a in landscapes) == sorted(l['path'] for l in baseline['landscapes'])
    assert all(a.get_actor_scale3d().x == a.get_actor_scale3d().y == 100 for a in landscapes)
    grass = unreal.load_asset(GRASS)
    grass_nodes = [e for e in nodes if isinstance(e, unreal.MaterialExpressionLandscapeGrassOutput)]
    assert len(grass_nodes) == 1
    grass_now = {'graph': {p: describe(material, e) for p, e in reachable(material, grass_nodes).items()},
                 'settings': grass_settings(grass), 'effective_coverage': {
                    path(a): float(LIB.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage'))
                    for a in landscapes}}
    assert grass_now['graph'] == reference['grass_after']['graph']
    assert grass_now['settings'] == reference['grass_after']['settings']
    assert set(grass_now['effective_coverage'].values()) == set(reference['grass_after']['effective_coverage'].values())
    instances = {p: unreal.load_asset(p) for p in reference['instances']}
    instance_now = {p: material_state(material, mi) for p, mi in instances.items()}
    assert instance_now == reference['instances']
    mask_settings = {}
    for layer, package in MASK_COPIES.items():
        texture = LIB.get_material_instance_texture_parameter_value(child, layer + '_PackedMask')
        assert path(texture).split('.')[0] == package and texture.get_editor_property('srgb') is False
        assert texture.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_MASKS
        mask_settings[layer] = {'path': path(texture), 'srgb': False, 'compression': 'TC_MASKS'}
    added = set(reference['added_nodes'])
    custom_nodes = {p: row for p, row in current.items() if p in added and row['class'] == 'MaterialExpressionCustom'}
    samplers = {p: row for p, row in current.items() if p in added and row['class'] == 'MaterialExpressionTextureSample'}
    assert len(custom_nodes) == 8 and len(samplers) == 24
    assert all(row['properties']['code'] == HASH_CODE and row['custom_inputs'] == ['Cell']
               and row['custom_outputs'] == [] and row['includes'] == [] for row in custom_nodes.values())
    assert all(row['properties']['mip_value_mode'] == plain(unreal.TextureMipValueMode.TMVM_DERIVATIVE)
               and row['edges']['DDX(UVs)']['source'] and row['edges']['DDY(UVs)']['source']
               for row in samplers.values())
    sources_after, actors_after = guard(assignment, named_map, require_authoring=False)
    assert sources_after == sources and scene_state(actors_after) == scene and dirty() == dirty_before
    label = args.get('label', 'verification')
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label), label
    out = REV / ('VERIFY_STOCHASTIC_' + area + '_' + label + '_PID' + str(os.getpid()) + '.json')
    assert not out.exists(), 'Read-only receipt must not overwrite earlier evidence.'
    result = {'schema': 'environmentpipeline.ground_stochastic_identity.v1', 'pid': os.getpid(),
        'world': named_map, 'area': area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reference': {'file': str(files['reference_receipt']), 'sha256': sha(files['reference_receipt'])},
        'helper_sha256': sha(SCRIPT), 'graph_count': 1015, 'nodes': current, 'graph_sha256': digest(current),
        'roots': roots, 'material_settings': settings, 'custom_nodes': custom_nodes, 'sampler_nodes': samplers,
        'complete_code_input_output_mip_identity_equal': True, 'grass': grass_now, 'scene': scene,
        'instances': instance_now, 'mask_settings': mask_settings, 'dirty': dirty_before,
        'fresh_process': os.getpid() != reference['pid'], 'same_area_as_authoring': same_area,
        'scene_comparison': 'authoring reference and fresh baseline' if same_area else 'fresh baseline; original map file hash preserved',
        'master_package_sha256': sha(package_file(MASTER)), 'native_mutation': False,
        'explicit_save_called': False, 'explicit_compile_called': False,
        'shader_cost_measured': False, 'streaming_residency_proven': False}
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return {'receipt': str(out), 'sha256': sha(out), 'graph_count': 1015,
            'complete_code_input_output_mip_identity_equal': True, 'fresh_process': result['fresh_process'],
            'native_mutation': False, 'streaming_residency_proven': False}


if 'ARGS' in globals():
    RESULT = verify_stochastic(ARGS) if ARGS.get('mode') == 'verify' else stochastic(ARGS)


