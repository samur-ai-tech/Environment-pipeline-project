"""Read-only verifier for the frozen applied Sand sampler; root pins this file.

ARGS: mode='verify' or 'snapshot_expected_mi'; reference_receipt, baseline_receipt,
backup_manifest and each *_sha256; master_package_sha256; label; require_clean
(default True). Intentional MI changes require expected_mi_receipt and its SHA,
plus separately SHA-bound expected_mi_review approval. Snapshot grants no approval.
Later other-area verification can bind prior_mi_receipt + prior_mi_review and
their SHAs to an approved prior-area named-save snapshot; no other child waiver.
No compile/save, Content/actor writes, forced residency, Cook/Bake or cleanup.
"""
import datetime
import json
import os
import types
from pathlib import Path

FROZEN_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'


def load_helper():
    import hashlib
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    helper = (root / 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py').resolve(strict=True)
    helper_bytes = helper.read_bytes()
    assert hashlib.sha256(helper_bytes).hexdigest() == FROZEN_SHA
    module = types.ModuleType('ground_stochastic_frozen_readonly')
    module.__file__ = str(helper)
    # A new module namespace has no ARGS, so the frozen authoring entry point is idle.
    exec(compile(helper_bytes, str(helper), 'exec'), module.__dict__)
    assert 'ARGS' not in module.__dict__ and module.SCRIPT.resolve() == helper
    assert module.sha(helper) == FROZEN_SHA
    return module


def constrained_mi_changes(before, after, child_key, global_association):
    """Allow only current-child ground scalar/vector values, retaining other identity."""
    assert set(before) == set(after)
    targets = ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')
    scalar_allow = {t + s for t in targets for s in ('_Roughness', '_NormalStrength', '_FarScale')} | {
        'Ground_MacroContrast', 'Ground_SoilBlendStrength', 'GeoCity_DistanceStartCm',
        'GeoCity_DistanceRangeCm', 'GeoCity_RoughnessDetail', 'GeoCity_AOStrength',
        'GeoCity_MacroAmount', 'GeoCity_CellScale', 'GeoCity_PatternScale'}
    vector_allow = {t + s for t in targets for s in ('_Tint', '_TileCm')} | {
        'Ground_MacroTileCm', 'Ground_MacroTile2Cm', 'Ground_MacroOffsetCm'}
    changed = []
    for key in before:
        old, new = before[key], after[key]
        if old == new:
            continue
        assert key == child_key, 'Only current-area child parameters may differ'
        assert set(old) == set(new)
        for field in set(old) - {'scalars', 'vectors', 'scalar_overrides', 'vector_overrides'}:
            assert old[field] == new[field], (key, field)
        for kind, allowed in (('scalar', scalar_allow), ('vector', vector_allow)):
            field = kind + 's'
            assert set(old[field]) == set(new[field])
            assert all(old[field][name] == new[field][name] for name in old[field] if name not in allowed)
            field = kind + '_overrides'
            assert [v for v in old[field] if v['name'] not in allowed] == [
                v for v in new[field] if v['name'] not in allowed]
            assert all(v['index'] == -1 and v['association'] == global_association
                       for v in new[field] if v['name'] in allowed)
        changed.append(key)
    return sorted(changed)


def diagnostics(h, material):
    result = {'statistics': {}, 'compile_accessors': {}, 'compile_success_proven': False}
    api = getattr(h.LIB, 'get_statistics', None)
    if not callable(api):
        result['statistics']['status'] = 'API_NOT_EXPOSED'
    else:
        try:
            statistics = api(material)
            result['statistics']['status'] = 'READ_ONLY_NATIVE_RESULT'
            for field in ('num_vertex_shader_instructions', 'num_pixel_shader_instructions',
                          'num_samplers', 'num_vertex_texture_samples', 'num_pixel_texture_samples',
                          'num_virtual_texture_samples', 'num_uv_scalars', 'num_interpolator_scalars'):
                try:
                    result['statistics'][field] = int(statistics.get_editor_property(field))
                except Exception as error:
                    result['statistics'][field] = {'status': 'FIELD_NOT_EXPOSED', 'error': str(error)}
        except Exception as error:
            result['statistics'] = {'status': 'READ_FAILED', 'error': str(error)}
    # Native IsCompiling/IsComplete are not UFUNCTIONs in the installed header.
    # Probe only their corresponding Python methods if actually exposed.
    for name in ('is_compiling', 'is_complete'):
        accessor = getattr(material, name, None)
        if not callable(accessor):
            result['compile_accessors'][name] = {'status': 'API_NOT_EXPOSED'}
        else:
            try:
                result['compile_accessors'][name] = {'status': 'READ_ONLY_NATIVE_RESULT', 'value': bool(accessor())}
            except Exception as error:
                result['compile_accessors'][name] = {'status': 'READ_FAILED', 'error': str(error)}
    result['limitations'] = ['Statistics are a native result for this loaded material, not a GPU timing measurement.',
        'IsComplete may be true before resources are cached; no accessor here proves absence of shader errors.',
        'Root independently checks compile logs and actual Lit readiness.']
    return result


def approved_mi(h, args, prefix, files, assignment, reference_sha, manifest_sha, verifier_sha):
    receipt_key, review_key = prefix + '_receipt', prefix + '_review'
    files[receipt_key], candidate = h.load_document(args[receipt_key])
    files[review_key], review = h.load_document(args[review_key])
    assert h.sha(files[receipt_key]) == args[receipt_key + '_sha256']
    assert h.sha(files[review_key]) == args[review_key + '_sha256']
    assert candidate['schema'] == 'environmentpipeline.stochastic_expected_mi.v1'
    assert candidate['status'] == 'CANDIDATE_REQUIRES_ROOT_REVIEW' and candidate['native_mutation'] is False
    assert candidate['world'] == assignment['original_maps'][candidate['area']]
    assert candidate['frozen_helper_sha256'] == FROZEN_SHA and candidate['verifier_sha256'] == verifier_sha
    assert candidate['reference_sha256'] == reference_sha and candidate['backup_manifest_sha256'] == manifest_sha
    assert review['status'] == 'APPROVED_EXACT_EXPECTED_MI'
    assert review['world'] == candidate['world'] and review['area'] == candidate['area']
    assert review['expected_mi_receipt_sha256'] == h.sha(files[receipt_key])
    assert Path(review['expected_mi_receipt']).resolve(strict=True) == files[receipt_key]
    assert review['frozen_helper_sha256'] == FROZEN_SHA and review['verifier_sha256'] == verifier_sha
    assert review['reference_receipt_sha256'] == reference_sha and review['backup_manifest_sha256'] == manifest_sha
    assert review['changed_instance_paths'] == candidate['changed_instance_paths']
    assert review.get('prior_mi_receipt_sha256') == candidate.get('prior_mi_receipt_sha256')
    return candidate


def verify(args):
    h = load_helper()
    script = (h.HERE / 'native_stochastic_verify_readonly.py').resolve(strict=True)
    mode = args.get('mode', 'verify')
    assert mode in ('verify', 'snapshot_expected_mi')
    assignment = json.loads((h.HERE / 'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
    world = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = h.one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    sources, actors = h.guard(assignment, named_map, require_authoring=False)
    files, documents = {}, {}
    for key in ('reference_receipt', 'baseline_receipt', 'backup_manifest'):
        files[key], documents[key] = h.load_document(args[key])
        assert h.sha(files[key]) == args[key + '_sha256'], key
    reference, baseline, manifest = (documents[k] for k in ('reference_receipt', 'baseline_receipt', 'backup_manifest'))
    assert reference['status'] == 'stochastic_verified_no_explicit_save_compile_pending'
    assert reference['old_node_preservation_verified'] and reference['graph_count'] == 1015
    assert reference['helper_sha256'] == manifest['helper_sha256'] == h.sha(h.SCRIPT) == FROZEN_SHA
    h.same_binding(manifest, 'helper', h.SCRIPT.resolve(strict=True))
    for key, binding in reference['input_files'].items():
        file, _ = h.load_document(binding['file'])
        assert h.sha(file) == binding['sha256'], key
    assert reference['input_files']['backup_manifest']['sha256'] == h.sha(files['backup_manifest'])
    assert baseline['pid'] == os.getpid() and baseline['world'] == named_map
    assert baseline['graph_expression_count'] == 1015 and baseline['sources'] == sources
    assert baseline['cooking_paused'] and not baseline['autosave'] and not any(baseline['callbacks'].values())
    assert len(baseline['hdas']) == 1 and all(not x['auto_cook'] and not x['auto_bake'] for x in baseline['hdas'])
    assert reference['world'] in assignment['original_maps'].values()
    assert manifest['ready'] is True and manifest['new_asset_paths'] == []
    assert manifest['execution_thread_id'] == h.THREAD and manifest['ordinary_generation_authorized'] is False
    material = h.unreal.load_asset(h.MASTER)
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][area])
    child_package = child.get_outermost().get_path_name()
    child_key = h.one((p for p in reference['instances'] if h.unreal.load_asset(p) == child), 'current child key')
    instances = {p: h.material_state(material, h.unreal.load_asset(p)) for p in reference['instances']}
    global_association = h.plain(h.unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    owned_mi_files = {str(h.package_file(p).resolve()) for p in assignment['material_contract']['area_instances'].values()}
    mi_package_hashes = {p: h.sha(p) for p in sorted(owned_mi_files)}
    anchor, prior_hashes, prior_sha = reference['instances'], {}, None
    if args.get('prior_mi_receipt'):
        prior = approved_mi(h, args, 'prior_mi', files, assignment, h.sha(files['reference_receipt']),
                            h.sha(files['backup_manifest']), h.sha(script))
        assert prior['area'] != area and prior.get('prior_mi_receipt_sha256') is None, 'Only one separately approved prior-area transition'
        prior_child = assignment['material_contract']['area_instances'][prior['area']]
        assert constrained_mi_changes(reference['instances'], prior['instances'], prior_child,
                                      global_association) == prior['changed_instance_paths']
        assert set(prior['owned_mi_package_sha256']) == owned_mi_files
        prior_file = str(h.package_file(prior_child).resolve())
        prior_hashes = {prior_file: prior['owned_mi_package_sha256'][prior_file]}
        anchor, prior_sha = prior['instances'], h.sha(files['prior_mi_receipt'])
    changed_mis = constrained_mi_changes(anchor, instances, child_key, global_association)
    expected_mi = None
    if args.get('expected_mi_receipt'):
        assert mode == 'verify'
        expected_mi = approved_mi(h, args, 'expected_mi', files, assignment, h.sha(files['reference_receipt']),
                                  h.sha(files['backup_manifest']), h.sha(script))
        assert expected_mi['world'] == named_map and expected_mi['area'] == area
        assert expected_mi.get('prior_mi_receipt_sha256') == prior_sha
        assert expected_mi['instances'] == instances and expected_mi['changed_instance_paths'] == changed_mis
        assert expected_mi['owned_mi_package_sha256'] == mi_package_hashes
    elif mode == 'verify':
        assert instances == anchor, 'Intentional MI changes need a separate exact reviewed snapshot'
    assert len(manifest['file_bindings']) == 17
    disk_hashes = {}
    for filename, row in manifest['file_bindings'].items():
        source, backup = Path(filename).resolve(strict=True), Path(row['backup']).resolve(strict=True)
        assert source.is_relative_to(h.ROOT) and backup.is_relative_to(h.REV / 'SamplerBefore')
        assert h.sha(backup) == row['sha256'], filename
        actual = h.sha(source)
        if source == h.package_file(h.MASTER).resolve():
            expected = args['master_package_sha256']
        elif source == h.package_file(child_package).resolve() and (expected_mi is not None or mode == 'snapshot_expected_mi'):
            expected = mi_package_hashes[str(source)]
        elif str(source) in prior_hashes:
            expected = prior_hashes[str(source)]
        else:
            expected = row['sha256']
        assert actual == expected, filename
        disk_hashes[str(source)] = actual
    for family, count in (('preserved_files', 65), ('sealed_files', 17)):
        assert len(manifest[family]) == count
        for relative, expected in manifest[family].items():
            source = (h.ROOT / relative).resolve(strict=True)
            assert source.is_relative_to(h.ROOT) and h.sha(source) == expected, relative
    dirty = lambda: {'maps': [h.path(p) for p in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
                     'content': [h.path(p) for p in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
    dirty_before = dirty()
    assert dirty_before['maps'] == baseline['dirty_maps'] == []
    assert set(dirty_before['content']) == set(baseline['dirty_content'])
    allowed_dirty = {h.MASTER, child_package}
    assert not dirty_before['content'] if args.get('require_clean', True) else set(dirty_before['content']) <= allowed_dirty
    nodes = list(h.LIB.get_material_expressions(material))
    current = {h.path(e): h.describe(material, e) for e in nodes}
    assert len(current) == 1015 and current == reference['nodes_after'], 'Complete observed graph identity mismatch'
    roots = {k: h.path(h.LIB.get_material_property_input_node(material, prop)) for k, prop in h.PROPERTIES.items()}
    assert roots == reference['roots']
    settings = {k: h.plain(material.get_editor_property(k)) for k in reference['material_settings']}
    assert settings == reference['material_settings']
    scene = h.scene_state(actors)
    assert scene['transforms'] == baseline['actor_transforms']
    assert scene['native_mesh_components'] == sorted(baseline['native_mesh_components'], key=lambda x: x['component'])
    clean_landscape = lambda rows: [{k: v for k, v in row.items() if k != 'layers'} for row in rows]
    expected_landscapes = sorted([{'path': row['path'], 'material': row['material']['path'], 'hidden': row['hidden']}
                                 for row in baseline['landscapes']], key=lambda x: x['path'])
    assert clean_landscape(scene['landscapes']) == expected_landscapes
    same_area = reference['world'] == named_map
    if same_area:
        assert scene['transforms'] == reference['scene']['transforms']
        assert scene['native_mesh_components'] == reference['scene']['native_mesh_components']
        assert clean_landscape(scene['landscapes']) == clean_landscape(reference['scene']['landscapes'])
    landscapes = [a for a in actors if isinstance(a, h.unreal.LandscapeProxy)]
    assert all(a.get_editor_property('landscape_material') == child for a in landscapes)
    assert all(a.get_actor_scale3d().x == a.get_actor_scale3d().y == 100 for a in landscapes)
    grass_nodes = [e for e in nodes if isinstance(e, h.unreal.MaterialExpressionLandscapeGrassOutput)]
    assert len(grass_nodes) == 1
    grass_now = {'graph': {p: h.describe(material, e) for p, e in h.reachable(material, grass_nodes).items()},
        'settings': h.grass_settings(h.unreal.load_asset(h.GRASS)), 'effective_coverage': {
            h.path(a): float(h.LIB.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage'))
            for a in landscapes}}
    assert grass_now['graph'] == reference['grass_after']['graph']
    assert grass_now['settings'] == reference['grass_after']['settings']
    assert set(grass_now['effective_coverage'].values()) == set(reference['grass_after']['effective_coverage'].values())
    mask_settings = {}
    for layer, package in h.MASK_COPIES.items():
        texture = h.LIB.get_material_instance_texture_parameter_value(child, layer + '_PackedMask')
        assert h.path(texture).split('.')[0] == package and texture.get_editor_property('srgb') is False
        assert texture.get_editor_property('compression_settings') == h.unreal.TextureCompressionSettings.TC_MASKS
        mask_settings[layer] = {'path': h.path(texture), 'srgb': False, 'compression': 'TC_MASKS'}
    added = set(reference['added_nodes'])
    custom_nodes = {p: row for p, row in current.items() if p in added and row['class'] == 'MaterialExpressionCustom'}
    samplers = {p: row for p, row in current.items() if p in added and row['class'] == 'MaterialExpressionTextureSample'}
    assert len(custom_nodes) == 8 and len(samplers) == 24
    assert all(row['properties']['code'] == h.HASH_CODE and row['custom_inputs'] == ['Cell']
               and row['custom_outputs'] == [] and row['includes'] == [] for row in custom_nodes.values())
    assert all(row['properties']['mip_value_mode'] == h.plain(h.unreal.TextureMipValueMode.TMVM_DERIVATIVE)
               and row['edges']['DDX(UVs)']['source'] and row['edges']['DDY(UVs)']['source'] for row in samplers.values())
    native_diagnostics = diagnostics(h, material)
    sources_after, actors_after = h.guard(assignment, named_map, require_authoring=False)
    assert sources_after == sources and h.scene_state(actors_after) == scene and dirty() == dirty_before
    assert {p: h.material_state(material, h.unreal.load_asset(p)) for p in reference['instances']} == instances
    assert all(h.sha(p) == expected for p, expected in disk_hashes.items())
    assert all(h.sha(h.ROOT / p) == expected for family in ('preserved_files', 'sealed_files')
               for p, expected in manifest[family].items())
    label = args.get('label', 'verification')
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label)
    prefix = 'EXPECTED_MI_STOCHASTIC_' if mode == 'snapshot_expected_mi' else 'VERIFY_STOCHASTIC_READONLY_'
    out = h.REV / (prefix + area + '_' + label + '_PID' + str(os.getpid()) + '.json')
    assert not out.exists(), 'Never overwrite earlier evidence'
    result = {'schema': 'environmentpipeline.stochastic_expected_mi.v1' if mode == 'snapshot_expected_mi'
              else 'environmentpipeline.stochastic_readonly_identity.v1',
        'status': 'CANDIDATE_REQUIRES_ROOT_REVIEW' if mode == 'snapshot_expected_mi' else 'IDENTITY_VERIFIED_READ_ONLY',
        'pid': os.getpid(), 'world': named_map, 'area': area,
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'frozen_helper_sha256': FROZEN_SHA, 'verifier_sha256': h.sha(script),
        'reference_sha256': h.sha(files['reference_receipt']), 'backup_manifest_sha256': h.sha(files['backup_manifest']),
        'prior_mi_receipt_sha256': prior_sha,
        'input_files': {k: {'file': str(p), 'sha256': h.sha(p)} for k, p in files.items()},
        'instances': instances, 'changed_instance_paths': changed_mis, 'owned_mi_package_sha256': mi_package_hashes,
        'graph_count': 1015, 'nodes': current, 'graph_sha256': h.digest(current), 'roots': roots,
        'material_settings': settings, 'custom_nodes': custom_nodes, 'sampler_nodes': samplers,
        'complete_code_input_output_mip_identity_equal': True, 'grass': grass_now, 'scene': scene,
        'mask_settings': mask_settings, 'dirty': dirty_before, 'allowed_dirty_packages': sorted(allowed_dirty),
        'package_sha256': disk_hashes, 'native_diagnostics': native_diagnostics,
        'fresh_process': os.getpid() != reference['pid'], 'same_area_as_authoring': same_area,
        'native_mutation': False, 'explicit_save_called': False, 'explicit_compile_called': False,
        'streaming_residency_proven': False, 'gpu_cost_measured': False,
        'limitations': ['ExpressionGUID is not captured by the Python override structs.',
            'Deprecated editor_layer_settings is unknown; original map hashes and graph layer identities are checked.',
            'This verifier does not sample the full Landscape heightfield/weights or prove visual/default-streaming quality.']}
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return {'receipt': str(out), 'sha256': h.sha(out), 'status': result['status'],
            'graph_count': 1015, 'native_mutation': False, 'native_diagnostics': native_diagnostics}


if 'ARGS' in globals():
    RESULT = verify(ARGS)
