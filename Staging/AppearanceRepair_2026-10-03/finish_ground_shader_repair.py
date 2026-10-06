"""Resume the recorded OneMinus input-alias failure; never rerun authoring."""
import datetime
import hashlib
import json
import runpy
from pathlib import Path

import unreal

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/AppearanceRepair_2026-10-03'
LIB = unreal.MaterialEditingLibrary


def finish_ground_shader_repair():
    # A non-entry run name loads helpers without executing repair_ground_shader.
    helper_path = HERE / 'repair_ground_shader.py'
    h = runpy.run_path(str(helper_path), run_name='_ground_shader_recovery_library')
    path, inputs, one = h['_path'], h['_inputs'], h['_one']
    dirty_maps = h['_guard']()
    assert not (HERE / 'GROUND_SHADER_REPAIR_CURRENT.json').exists()
    failures = sorted(HERE.glob('GROUND_SHADER_REPAIR_FAILED_*.json'))
    assert len(failures) == 2, 'Recovery is limited to the two recorded failures'
    first, failed = [json.loads(p.read_text(encoding='utf-8')) for p in failures]
    assert "Missing input Input on MaterialExpressionOneMinus: ['None']" in failed['error']
    assert first['saved_paths'] == failed['saved_paths'] == []
    assert first['source_hashes_before'] == failed['source_hashes_before'] == failed['source_hashes_after']
    assert first['master'] == failed['master'] and first['instance'] == failed['instance']
    for original, row in first['backups'].items():
        assert h['_sha'](Path(row['backup'])) == row['sha256']
        assert h['_sha'](Path(original)) == row['sha256'], 'Retained disk package changed after original backup'
    assert {p: h['_sha'](h['_file'](p)) for p in h['NORMALS'].values()} == first['source_hashes_before']
    material, instance = unreal.load_asset(h['MPATH']), unreal.load_asset(h['IPATH'])
    assert path(material) == failed['master'] and path(instance) == failed['instance']
    assert path(instance.get_editor_property('parent')) == path(material)
    roots, reachable = h['_reachable'](material)
    assert {n: path(e) for n, e in roots.items()} == failed['graph_before']['roots']
    assert {n: h['_layer_names'](e) for n, e in roots.items()} == first['layer_names_before']
    all_nodes = {path(e): e for e in LIB.get_material_expressions(material)}
    links = list(failed['graph_links_written'])
    assert len(links) == 17, ('Unexpected completed-link frontier', len(links))
    for row in links:
        assert row['from'] in all_nodes and row['to'] in all_nodes
        assert row['from'] in {path(e) for e in inputs(material, all_nodes[row['to']])}, row

    def edge(input_name, predicate):
        matches = [r for r in links if r['input'] == input_name and predicate(r)]
        assert len(matches) == 1, (input_name, matches)
        return matches[0]

    color_edge = edge('Layer Sand_01', lambda r: r['to'] == path(roots['BaseColor']))
    color_lerp = all_nodes[color_edge['from']]
    assert isinstance(color_lerp, unreal.MaterialExpressionLinearInterpolate)
    sand_colored = all_nodes[edge('A', lambda r: r['to'] == path(color_lerp))['from']]
    soil_colored = all_nodes[edge('B', lambda r: r['to'] == path(color_lerp))['from']]
    mask_mix_path = links[-1]['to']
    assert links[-2]['to'] == mask_mix_path and links[-2]['input'] == 'A' and links[-1]['input'] == 'B'
    mask_mix = all_nodes[mask_mix_path]
    assert isinstance(mask_mix, unreal.MaterialExpressionLinearInterpolate)
    assert abs(float(mask_mix.get_editor_property('const_alpha')) - .45) < 1e-6
    mask_channel = all_nodes[links[-2]['from']]
    assert isinstance(mask_channel, unreal.MaterialExpressionComponentMask)
    strength = h['_parameter'](reachable, 'Ground_SoilBlendStrength', unreal.MaterialExpressionScalarParameter)
    alpha = one((e for e in inputs(material, color_lerp)
                 if isinstance(e, unreal.MaterialExpressionMultiply)
                 and strength in inputs(material, e)), 'existing shared alpha')
    assert mask_channel in inputs(material, alpha)
    normal_lerp = one((e for e in reachable.values()
                       if isinstance(e, unreal.MaterialExpressionLinearInterpolate)
                       and e != color_lerp and alpha in inputs(material, e)), 'existing normal Lerp')
    soil_size = h['_parameter'](reachable, 'Dirt_Path_TileCm', unreal.MaterialExpressionVectorParameter)
    soil_functions = [all_nodes[r['to']] for r in links
                      if r['input'] == 'TextureSize' and r['from'] == path(soil_size)]
    assert len(soil_functions) == 2
    tile2 = one((e for e in all_nodes.values() if isinstance(e, unreal.MaterialExpressionVectorParameter)
                 and str(e.get_editor_property('parameter_name')) == 'Ground_MacroTile2Cm'), 'existing second tile')
    offset = one((e for e in all_nodes.values() if isinstance(e, unreal.MaterialExpressionVectorParameter)
                  and str(e.get_editor_property('parameter_name')) == 'Ground_MacroOffsetCm'), 'existing second offset')
    original_nodes = {r['path'] for r in failed['graph_before']['reachable']}
    inverse = one((e for e in all_nodes.values() if isinstance(e, unreal.MaterialExpressionOneMinus)
                   and path(e) not in original_nodes
                   and tuple(LIB.get_material_expression_node_position(e)) == (-780, 15800)), 'existing orphan OneMinus')
    assert not inputs(material, inverse), 'Orphan OneMinus unexpectedly connected'
    assert list(LIB.get_material_expression_input_names(inverse)) == ['None']
    sources = {n: unreal.load_asset(p) for n, p in h['NORMALS'].items()}
    targets = {n: h['ROOT'] + '/Textures/T_' + n.removesuffix('_Normal') + '_Normal_GeoCity'
               for n in h['NORMALS']}
    copies = {n: unreal.load_asset(p) for n, p in targets.items()}
    normal_nodes = {n: h['_parameter'](reachable, n, unreal.MaterialExpressionTextureObjectParameter)
                    for n in h['NORMALS']}
    for name, copy in copies.items():
        assert isinstance(copy, unreal.Texture2D) and path(copy) == targets[name] + '.' + targets[name].rsplit('/', 1)[1]
        assert not copy.get_editor_property('srgb')
        assert copy.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_NORMALMAP
        assert path(normal_nodes[name].get_editor_property('texture')) == path(copy)
        assert normal_nodes[name].get_editor_property('sampler_type') == unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        assert path(LIB.get_material_instance_texture_parameter_value(instance, name)) == path(copy)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    receipt = dict(first)
    receipt.update(utc=stamp, original_attempt_utc=first['utc'], status='resuming_recorded_frontier',
                   graph_links_written=links, saved_paths=[], recovery_failure_receipts=[str(p) for p in failures],
                   recovery_library_sha256=hashlib.sha256(helper_path.read_bytes()).hexdigest(),
                   recovery_frontier_graph=h['_graph'](material, roots, reachable),
                   dirty_maps_before_recovery=dirty_maps,
                   recovery_reason='Setter bool can be false after applied getter readback; OneMinus exposes None rather than Input')
    receipt.pop('error', None)
    helpers = runpy.run_path(str(PROJECT / 'Staging/PaintBank_2026-10-02/author_all_layers_surface_material.py'))
    node = helpers['node']

    def link(source, output, destination, preferred):
        names = list(LIB.get_material_expression_input_names(destination))
        actual = preferred if preferred in names else ('None' if preferred == 'Input' and names == ['None'] else None)
        assert actual is not None, (path(destination), preferred, names)
        result = LIB.connect_material_expressions(source, output, destination, actual)
        assert source in inputs(material, destination), ('Actual link readback failed', path(destination), actual)
        receipt['graph_links_written'].append({'from': path(source), 'output': output,
                                               'to': path(destination), 'input': actual,
                                               'connection_return': bool(result)})

    try:
        h['_guard']()
        link(mask_mix, '', inverse, 'Input')
        contrast = node(material, unreal.MaterialExpressionScalarParameter, -1000, 16000,
                        parameter_name='Ground_MacroContrast', default_value=3.)
        amplified = node(material, unreal.MaterialExpressionMultiply, -530, 15800)
        link(inverse, '', amplified, 'A'); link(contrast, '', amplified, 'B')
        saturated = node(material, unreal.MaterialExpressionSaturate, -300, 15800)
        link(amplified, '', saturated, 'Input')
        link(saturated, '', alpha, 'A'); link(strength, '', alpha, 'B')
        for name, value in {'Ground_SoilBlendStrength': .60, 'Ground_MacroContrast': 3.}.items():
            LIB.set_material_instance_scalar_parameter_value(instance, name, value)
            assert abs(float(LIB.get_material_instance_scalar_parameter_value(instance, name)) - value) < 1e-6
        for name, rgba in {'Ground_MacroTile2Cm': (5700, 5700, 5700, 1),
                           'Ground_MacroOffsetCm': (1700, 2900, 0, 0)}.items():
            LIB.set_material_instance_vector_parameter_value(instance, name, unreal.LinearColor(*rgba))
            actual = LIB.get_material_instance_vector_parameter_value(instance, name)
            assert max(abs(a - b) for a, b in zip((actual.r, actual.g, actual.b, actual.a), rgba)) < 1e-6
        LIB.recompile_material(material)
        LIB.update_material_instance(instance)
        after_roots, after_reachable = h['_reachable'](material)
        assert {n: path(e) for n, e in after_roots.items()} == first['graph_before']['roots']
        assert {n: h['_layer_names'](e) for n, e in after_roots.items()} == first['layer_names_before']
        assert sand_colored in inputs(material, color_lerp) and soil_colored in inputs(material, color_lerp)
        assert saturated in inputs(material, alpha) and alpha in inputs(material, normal_lerp)
        assert inverse in inputs(material, amplified) and mask_mix in inputs(material, inverse)
        assert all(soil_size in inputs(material, e) for e in soil_functions)
        before_nodes = {r['path']: r for r in first['graph_before']['reachable']}
        original_post_tint = one((all_nodes[p] for p, row in before_nodes.items()
                                 if row['class'] == 'MaterialExpressionMultiply'
                                 and path(color_lerp) in row['inputs']
                                 and p in before_nodes[first['graph_before']['roots']['BaseColor']]['inputs']), 'original post-blend tint')
        assert path(original_post_tint) not in after_reachable
        values_after = h['_values'](instance)
        allowed = {'scalars': {'Ground_SoilBlendStrength', 'Ground_MacroContrast'},
                   'vectors': {'Ground_MacroTile2Cm', 'Ground_MacroOffsetCm'}, 'textures': set(h['NORMALS'])}
        for family, params in first['instance_values_before'].items():
            for name, value in params.items():
                if name not in allowed[family]:
                    assert values_after[family].get(name) == value, ('Unrelated value changed', family, name)
        for name, copy in copies.items():
            assert values_after['textures'][name] == path(copy)
        receipt.update(graph_after=h['_graph'](material, after_roots, after_reachable),
                       instance_values_after=values_after, layer_names_after=first['layer_names_before'],
                       normal_settings_after={n: h['_texture_settings'](t) for n, t in copies.items()},
                       normal_sampler_readback={n: str(normal_nodes[n].get_editor_property('sampler_type')) for n in h['NORMALS']},
                       normal_copies={n: path(t) for n, t in copies.items()},
                       macro_formula='0.60 * saturate(3 * (1 - (0.55 * mask36m.R + 0.45 * mask57m_offset.R)))',
                       macro_parameters={n: values_after[f][n] for f, names in allowed.items() if f != 'textures' for n in names},
                       soil_tile_parameter='Dirt_Path_TileCm',
                       native_mask_probe={'size': [4096, 4096], 'rgb_equal': True, 'byte_range': [60, 255], 'mean': 206.95,
                                          'basis': 'Owner exported and measured exact native T_dirt3_M before authoring'})
        for package in (*targets.values(), h['MPATH'], h['IPATH']):
            h['_guard']()
            assert unreal.EditorAssetLibrary.save_asset(package, only_if_is_dirty=True), package
            receipt['saved_paths'].append(package)
        receipt['source_hashes_after'] = {p: h['_sha'](h['_file'](p)) for p in h['NORMALS'].values()}
        assert receipt['source_hashes_after'] == first['source_hashes_before']
        assert {n: h['_texture_settings'](t) for n, t in sources.items()} == first['normal_settings_before']
        receipt['dirty_maps_after'] = [path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
        assert set(receipt['dirty_maps_after']) == set(dirty_maps), 'Unexpected map package mutation'
        receipt.update(status='named_assets_saved_graph_verified', visual_acceptance='pending_actual_ground_close_and_area_view')
        (HERE / ('GROUND_SHADER_REPAIR_' + stamp + '.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        (HERE / 'GROUND_SHADER_REPAIR_CURRENT.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': receipt['status'], 'resumed_failure': str(failures[-1]),
                          'saved_paths': receipt['saved_paths'], 'original_texture_hashes_unchanged': True,
                          'layer_names_preserved': 69, 'receipt': str(HERE / 'GROUND_SHADER_REPAIR_CURRENT.json')}))
        return receipt
    except Exception as exc:
        receipt.update(status='failed_ground_shader_recovery_requires_owner_review', error=repr(exc),
                       source_hashes_after={p: h['_sha'](h['_file'](p)) for p in h['NORMALS'].values()})
        (HERE / ('GROUND_SHADER_RECOVERY_FAILED_' + stamp + '.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        raise


if __name__ in ('__main__', '<run_path>'):
    finish_ground_shader_repair()
