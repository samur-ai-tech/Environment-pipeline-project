"""Repair only the retained Natural ground shader in the owner's editor.

Run by the sole editor owner. No map save, geographic mask changes, Houdini
evaluation, native road edits, or original texture writes are performed.
"""
import datetime
import hashlib
import json
import os
import runpy
import shutil
from pathlib import Path

import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/AppearanceRepair_2026-10-03'
ROOT = '/Game/Project/Shared/SurfacePainting/Appearance_20261003'
MPATH = ROOT + '/M_SurfaceBank_Natural'
IPATH = ROOT + '/MI_SurfaceBank_Natural'
NORMALS = {
    'Sand_01_Normal': '/Game/MOUT_Arabian/Textures/Landscape/Sand_01/T_Sand_01_Normal',
    'Sand_02_Normal': '/Game/MOUT_Arabian/Textures/Landscape/Sand_02/T_Sand_02_Normal',
}
LIB = unreal.MaterialEditingLibrary


def _path(obj):
    return obj.get_path_name() if obj else None


def _file(package):
    assert package.startswith('/Game/')
    return PROJECT / 'Content' / (package[6:].split('.')[0] + '.uasset')


def _sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _guard():
    lease = (PROJECT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(
        encoding='utf-8-sig').splitlines()[-1]
    assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease
    assert f'assigned_editor_PID={os.getpid()}' in lease
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    assert api and api.is_asset_cooking_paused()
    assert all(not r.watch_tick and not r.save_tick for r in bank.ACTIVE)
    assert all(not r.tick_handle for r in native.ACTIVE)
    # Rimal's native road transaction intentionally leaves its map dirty.
    return [_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]


def _inputs(material, expression):
    return [p for p in LIB.get_inputs_for_material_expression(material, expression) if p]


def _reachable(material):
    roots = {key: LIB.get_material_property_input_node(material, prop)
             for key, prop in (
                 ('BaseColor', unreal.MaterialProperty.MP_BASE_COLOR),
                 ('Normal', unreal.MaterialProperty.MP_NORMAL),
                 ('Roughness', unreal.MaterialProperty.MP_ROUGHNESS))}
    assert all(roots.values()), 'Material output root is missing'
    seen, pending = {}, list(roots.values())
    while pending:
        expression = pending.pop()
        key = _path(expression)
        if key not in seen:
            seen[key] = expression
            pending.extend(_inputs(material, expression))
    return roots, seen


def _one(candidates, label):
    candidates = list(candidates)
    assert len(candidates) == 1, (label, [_path(e) for e in candidates])
    return candidates[0]


def _parameter(reachable, name, cls):
    return _one((e for e in reachable.values() if isinstance(e, cls)
                 and str(e.get_editor_property('parameter_name')) == name), name)


def _function(material, reachable, texture_object, label):
    return _one((e for e in reachable.values()
                 if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall)
                 and texture_object in _inputs(material, e)), label)


def _layer_names(blend):
    assert isinstance(blend, unreal.MaterialExpressionLandscapeLayerBlend)
    return [str(layer.get_editor_property('layer_name'))
            for layer in blend.get_editor_property('layers')]


def _graph(material, roots, reachable):
    return {
        'roots': {name: _path(e) for name, e in roots.items()},
        'reachable': [{'path': _path(e), 'class': e.get_class().get_name(),
                       'input_names': list(LIB.get_material_expression_input_names(e)),
                       'inputs': [_path(p) for p in _inputs(material, e)]}
                      for e in sorted(reachable.values(), key=_path)],
    }


def _values(instance):
    return {
        'scalars': {str(n): float(LIB.get_material_instance_scalar_parameter_value(instance, n))
                    for n in LIB.get_scalar_parameter_names(instance)},
        'vectors': {str(n): [v.r, v.g, v.b, v.a]
                    for n in LIB.get_vector_parameter_names(instance)
                    for v in [LIB.get_material_instance_vector_parameter_value(instance, n)]},
        'textures': {str(n): _path(LIB.get_material_instance_texture_parameter_value(instance, n))
                     for n in LIB.get_texture_parameter_names(instance)},
    }


def _texture_settings(texture):
    return {'path': _path(texture), 'srgb': bool(texture.get_editor_property('srgb')),
            'compression': str(texture.get_editor_property('compression_settings'))}


def repair_ground_shader():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dirty_maps = _guard()
    assert not (HERE / 'GROUND_SHADER_REPAIR_CURRENT.json').exists(), 'Already repaired; inspect receipt before rerun'
    material, instance = unreal.load_asset(MPATH), unreal.load_asset(IPATH)
    assert isinstance(material, unreal.Material)
    assert isinstance(instance, unreal.MaterialInstanceConstant)
    assert _path(instance.get_editor_property('parent')) == _path(material)
    roots, reachable = _reachable(material)
    layers_before = {name: _layer_names(root) for name, root in roots.items()}
    assert all(len(names) == 69 and len(set(names)) == 69 for names in layers_before.values())
    assert layers_before['BaseColor'] == layers_before['Normal'] == layers_before['Roughness']
    new_names = {'Ground_MacroTile2Cm', 'Ground_MacroOffsetCm', 'Ground_MacroContrast'}
    assert not any(str(e.get_editor_property('parameter_name')) in new_names
                   for e in reachable.values()
                   if isinstance(e, (unreal.MaterialExpressionVectorParameter,
                                     unreal.MaterialExpressionScalarParameter)))
    graph_before, values_before = _graph(material, roots, reachable), _values(instance)
    texture_nodes = {name: _parameter(reachable, name, unreal.MaterialExpressionTextureObjectParameter)
                     for name in (*NORMALS, 'Sand_01_Albedo', 'Ground_MacroSoilAlbedo',
                                  'Ground_MacroSoilNormal', 'Ground_MacroMask')}
    sand_color = _function(material, reachable, texture_nodes['Sand_01_Albedo'], 'sand colour function')
    soil_color = _function(material, reachable, texture_nodes['Ground_MacroSoilAlbedo'], 'soil colour function')
    soil_normal = _function(material, reachable, texture_nodes['Ground_MacroSoilNormal'], 'soil normal function')
    sand_normal = _function(material, reachable, texture_nodes['Sand_01_Normal'], 'sand normal function')
    mask_fn = _function(material, reachable, texture_nodes['Ground_MacroMask'], 'first macro function')
    color_lerp = _one((e for e in reachable.values()
                       if isinstance(e, unreal.MaterialExpressionLinearInterpolate)
                       and sand_color in _inputs(material, e)
                       and soil_color in _inputs(material, e)), 'sand-soil colour Lerp')
    normal_lerp = _one((e for e in reachable.values()
                        if isinstance(e, unreal.MaterialExpressionLinearInterpolate)
                        and sand_normal in _inputs(material, e)
                        and soil_normal in _inputs(material, e)), 'sand-soil normal Lerp')
    sand_tint = _parameter(reachable, 'Sand_01_Tint', unreal.MaterialExpressionVectorParameter)
    soil_tint = _parameter(reachable, 'Dirt_Path_Tint', unreal.MaterialExpressionVectorParameter)
    soil_size = _parameter(reachable, 'Dirt_Path_TileCm', unreal.MaterialExpressionVectorParameter)
    strength = _parameter(reachable, 'Ground_SoilBlendStrength', unreal.MaterialExpressionScalarParameter)
    alpha = _one((e for e in _inputs(material, color_lerp)
                  if isinstance(e, unreal.MaterialExpressionMultiply)
                  and strength in _inputs(material, e)), 'shared sand-soil Alpha')
    assert alpha in _inputs(material, normal_lerp), 'Colour and normal alpha differ'
    mask_channel = _one((e for e in _inputs(material, alpha)
                         if isinstance(e, unreal.MaterialExpressionComponentMask)
                         and mask_fn in _inputs(material, e)), 'first macro red channel')
    final_tint = _one((e for e in _inputs(material, roots['BaseColor'])
                      if isinstance(e, unreal.MaterialExpressionMultiply)
                      and color_lerp in _inputs(material, e)
                      and sand_tint in _inputs(material, e)), 'Sand_01 post-blend tint')
    assert 'Layer Sand_01' in LIB.get_material_expression_input_names(roots['BaseColor'])
    sources = {name: unreal.load_asset(path) for name, path in NORMALS.items()}
    for name, source in sources.items():
        assert isinstance(source, unreal.Texture2D)
        assert _path(texture_nodes[name].get_editor_property('texture')) == _path(source)
        assert values_before['textures'][name] == _path(source)
        assert source.get_editor_property('srgb')
        assert source.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_DEFAULT
    targets = {name: ROOT + '/Textures/T_' + name.removesuffix('_Normal') + '_Normal_GeoCity'
               for name in NORMALS}
    # A preceding attempt stopped after its first setter returned False despite
    # correct value readback. Reuse only that exact unsaved owned normal copy.
    existing = [p for p in targets.values() if unreal.EditorAssetLibrary.does_asset_exist(p)]
    if existing:
        failed = list(HERE.glob('GROUND_SHADER_REPAIR_FAILED_*.json'))
        assert len(failed) == 1 and existing == [targets['Sand_01_Normal']]
        assert json.loads(failed[0].read_text())['error'] == 'AssertionError()'
        assert not _file(existing[0]).exists(), 'Recovery copy was unexpectedly saved'
    backup = HERE / 'BeforeGroundShader' / stamp
    backup.mkdir(parents=True, exist_ok=False)
    before_hashes = {path: _sha(_file(path)) for path in NORMALS.values()}
    backups = {}
    for package in (MPATH, IPATH):
        src = _file(package)
        assert src.is_file()
        for suffix in ('.uasset', '.uexp', '.ubulk'):
            sidecar = src.with_suffix(suffix)
            if sidecar.exists():
                dest = backup / 'Content' / sidecar.relative_to(PROJECT / 'Content')
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sidecar, dest)
                assert _sha(sidecar) == _sha(dest)
                backups[str(sidecar)] = {'backup': str(dest), 'sha256': _sha(dest)}
    receipt = {'schema': 'environmentpipeline.retained_ground_shader_repair.v1', 'utc': stamp,
               'master': _path(material), 'instance': _path(instance), 'backup': str(backup),
               'backups': backups, 'source_hashes_before': before_hashes,
               'graph_before': graph_before, 'instance_values_before': values_before,
               'layer_names_before': layers_before, 'dirty_maps_before': dirty_maps,
               'normal_settings_before': {name: _texture_settings(t) for name, t in sources.items()},
               'graph_links_written': [], 'saved_paths': [], 'status': 'started',
               'geographic_masks_changed': False, 'normal_worldspace_defaults_changed': False,
               'native_rgb_mask_semantics_unverified_roughness_unchanged': True}
    try:
        helpers = runpy.run_path(str(PROJECT / 'Staging/PaintBank_2026-10-02/author_all_layers_surface_material.py'))
        node = helpers['node']

        def link(source, output, destination, input_name):
            names = list(LIB.get_material_expression_input_names(destination))
            actual = input_name if input_name in names else (
                'None' if input_name == 'Input' and names == ['None'] else None)
            assert actual is not None, (_path(destination), input_name, names)
            helpers['link'](source, output, destination, actual)
            assert source in _inputs(material, destination), ('Link readback failed', actual)
            receipt['graph_links_written'].append({'from': _path(source), 'output': output,
                                                   'to': _path(destination), 'input': actual})

        copies = {}
        for name, source in sources.items():
            _guard()
            copy = (unreal.load_asset(targets[name]) if unreal.EditorAssetLibrary.does_asset_exist(targets[name])
                    else unreal.EditorAssetLibrary.duplicate_asset(_path(source), targets[name]))
            assert isinstance(copy, unreal.Texture2D)
            copy.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
            copy.set_editor_property('srgb', False)
            assert copy.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_NORMALMAP
            assert not copy.get_editor_property('srgb')
            texture_nodes[name].set_editor_property('texture', copy)
            texture_nodes[name].set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            assert texture_nodes[name].get_editor_property('sampler_type') == unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
            LIB.set_material_instance_texture_parameter_value(instance, name, copy)
            assert _path(LIB.get_material_instance_texture_parameter_value(instance, name)) == _path(copy)
            copies[name] = copy
        sand_colored = node(material, unreal.MaterialExpressionMultiply, -640, 14900)
        soil_colored = node(material, unreal.MaterialExpressionMultiply, -640, 15120)
        link(sand_color, 'XYZ Texture', sand_colored, 'A')
        link(sand_tint, '', sand_colored, 'B')
        link(soil_color, 'XYZ Texture', soil_colored, 'A')
        link(soil_tint, '', soil_colored, 'B')
        link(sand_colored, '', color_lerp, 'A')
        link(soil_colored, '', color_lerp, 'B')
        link(color_lerp, '', roots['BaseColor'], 'Layer Sand_01')
        link(soil_size, '', soil_color, 'TextureSize')
        link(soil_size, '', soil_normal, 'TextureSize')
        # Two samples of the SAME existing native grayscale mask. Absolute world
        # coordinates preserve deterministic variation across normal regeneration.
        tile2 = node(material, unreal.MaterialExpressionVectorParameter, -2300, 15800,
                     parameter_name='Ground_MacroTile2Cm', default_value=unreal.LinearColor(5700, 5700, 5700, 1))
        offset = node(material, unreal.MaterialExpressionVectorParameter, -2300, 16000,
                      parameter_name='Ground_MacroOffsetCm', default_value=unreal.LinearColor(1700, 2900, 0, 0))
        world = node(material, unreal.MaterialExpressionWorldPosition, -2550, 16140)
        shifted = node(material, unreal.MaterialExpressionAdd, -2000, 16140)
        link(world, 'XYZ', shifted, 'A'); link(offset, '', shifted, 'B')
        second = node(material, unreal.MaterialExpressionMaterialFunctionCall, -1650, 15800,
                      material_function=mask_fn.get_editor_property('material_function'))
        link(texture_nodes['Ground_MacroMask'], '', second, 'TextureObject')
        link(tile2, '', second, 'TextureSize')
        link(shifted, '', second, 'WorldPosition')
        second_r = node(material, unreal.MaterialExpressionComponentMask, -1250, 15800,
                        r=True, g=False, b=False, a=False)
        link(second, 'XYZ Texture', second_r, 'None')
        mask_mix = node(material, unreal.MaterialExpressionLinearInterpolate, -1000, 15800, const_alpha=.45)
        link(mask_channel, '', mask_mix, 'A'); link(second_r, '', mask_mix, 'B')
        inverse = node(material, unreal.MaterialExpressionOneMinus, -780, 15800)
        link(mask_mix, '', inverse, 'Input')
        contrast = node(material, unreal.MaterialExpressionScalarParameter, -1000, 16000,
                        parameter_name='Ground_MacroContrast', default_value=3.)
        amplified = node(material, unreal.MaterialExpressionMultiply, -530, 15800)
        link(inverse, '', amplified, 'A'); link(contrast, '', amplified, 'B')
        saturated = node(material, unreal.MaterialExpressionSaturate, -300, 15800)
        link(amplified, '', saturated, 'Input')
        link(saturated, '', alpha, 'A'); link(strength, '', alpha, 'B')
        LIB.set_material_instance_scalar_parameter_value(instance, 'Ground_SoilBlendStrength', .60)
        assert abs(float(LIB.get_material_instance_scalar_parameter_value(
            instance, 'Ground_SoilBlendStrength')) - .60) < 1e-6
        for name, rgb in {'Ground_MacroTile2Cm': (5700, 5700, 5700, 1),
                          'Ground_MacroOffsetCm': (1700, 2900, 0, 0)}.items():
            LIB.set_material_instance_vector_parameter_value(instance, name, unreal.LinearColor(*rgb))
            actual = LIB.get_material_instance_vector_parameter_value(instance, name)
            assert max(abs(a - b) for a, b in zip(
                (actual.r, actual.g, actual.b, actual.a), rgb)) < 1e-6
        LIB.set_material_instance_scalar_parameter_value(instance, 'Ground_MacroContrast', 3.)
        assert abs(float(LIB.get_material_instance_scalar_parameter_value(
            instance, 'Ground_MacroContrast')) - 3.) < 1e-6
        LIB.recompile_material(material)
        LIB.update_material_instance(instance)
        roots_after, reachable_after = _reachable(material)
        assert {n: _path(e) for n, e in roots.items()} == {n: _path(e) for n, e in roots_after.items()}
        assert {n: _layer_names(e) for n, e in roots_after.items()} == layers_before
        assert _path(final_tint) not in reachable_after, 'Old post-blend tint still reachable'
        assert sand_colored in _inputs(material, color_lerp) and soil_colored in _inputs(material, color_lerp)
        assert color_lerp in _inputs(material, roots_after['BaseColor'])
        assert alpha in _inputs(material, normal_lerp) and saturated in _inputs(material, alpha)
        assert soil_size in _inputs(material, soil_color) and soil_size in _inputs(material, soil_normal)
        after_values = _values(instance)
        allowed = {'scalars': {'Ground_SoilBlendStrength', 'Ground_MacroContrast'},
                   'vectors': {'Ground_MacroTile2Cm', 'Ground_MacroOffsetCm'},
                   'textures': set(NORMALS)}
        for family, params in values_before.items():
            for name, value in params.items():
                if name not in allowed[family]:
                    assert after_values[family].get(name) == value, ('Unrelated value changed', family, name)
        assert abs(after_values['scalars']['Ground_SoilBlendStrength'] - .60) < 1e-6
        receipt.update(graph_after=_graph(material, roots_after, reachable_after),
                       instance_values_after=after_values, layer_names_after=layers_before,
                       normal_settings_after={name: _texture_settings(t) for name, t in copies.items()},
                       normal_sampler_readback={name: str(texture_nodes[name].get_editor_property('sampler_type')) for name in NORMALS},
                       macro_formula='0.60 * saturate(3 * (1 - (0.55 * mask36m.R + 0.45 * mask57m_offset.R)))',
                       macro_parameters={name: after_values[family][name]
                                         for family, names in allowed.items() if family != 'textures' for name in names},
                       native_mask_probe={'size': [4096, 4096], 'rgb_equal': True, 'byte_range': [60, 255], 'mean': 206.95,
                                          'basis': 'Owner exported and measured exact native T_dirt3_M before authoring'},
                       soil_tile_parameter='Dirt_Path_TileCm', normal_copies={n: _path(t) for n, t in copies.items()})
        for path in (*targets.values(), MPATH, IPATH):
            _guard()
            assert unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=True), path
            receipt['saved_paths'].append(path)
        receipt['source_hashes_after'] = {p: _sha(_file(p)) for p in NORMALS.values()}
        assert receipt['source_hashes_after'] == before_hashes, 'Original texture bytes changed'
        assert {n: _texture_settings(t) for n, t in sources.items()} == receipt['normal_settings_before']
        receipt['dirty_maps_after'] = [_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
        assert receipt['dirty_maps_after'] == dirty_maps, 'Unexpected map package mutation'
        receipt.update(status='named_assets_saved_graph_verified', visual_acceptance='pending_actual_ground_close_and_area_view')
        (HERE / ('GROUND_SHADER_REPAIR_' + stamp + '.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        (HERE / 'GROUND_SHADER_REPAIR_CURRENT.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': receipt['status'], 'normal_copies': receipt['normal_copies'],
                          'layer_names_preserved': 69, 'soil_blend_max': .60, 'backup': str(backup),
                          'original_texture_hashes_unchanged': True, 'receipt': str(HERE / 'GROUND_SHADER_REPAIR_CURRENT.json')}))
        return receipt
    except Exception as exc:
        receipt.update(status='failed_requires_owner_review', error=repr(exc),
                       source_hashes_after={p: _sha(_file(p)) for p in NORMALS.values()})
        (HERE / ('GROUND_SHADER_REPAIR_FAILED_' + stamp + '.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        raise


if __name__ in ('__main__', '<run_path>'):
    repair_ground_shader()
