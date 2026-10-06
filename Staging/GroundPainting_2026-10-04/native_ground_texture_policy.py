"""Owned twelve-texture residency policy; root reviews, pins, and executes.

All modes require expected_pid, label, baseline_receipt, graph_receipt,
backup_manifest, plan_receipt and each *_sha256. Inspect grants no approval.
Apply additionally binds inspect_receipt + review_receipt and their SHAs.
Verify additionally binds inspect_receipt + apply_receipt and their SHAs;
expected_target_mi_package_sha256 is the exact current-child disk expectation
(pre-save original hash, or independently approved named-save hash after reopen).
Other-area verification requires its own pre-binding inspect receipt and a
SHA-bound root binding_review that names that inspection, plan, and creation.
Creation-only apply: twelve new paths, two copied properties, current child only.
No explicit save/master compile, source/vendor/actor edits, force timer or CVars.
Import without ARGS is idle. Partial failures retain objects and evidence.
"""
import datetime
import hashlib
import json
import os
import subprocess
import types
from pathlib import Path

FROZEN_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
ASSIGNMENT_SHA = 'c3c49a9baabdfe357a5852d383501d0ac0396bfc7a795b58762ac52b61d3fec7'
PARAMETERS = tuple(s + '_' + k for s in ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')
                   for k in ('Albedo', 'Normal', 'PackedMask'))
FIELDS = ('srgb', 'compression_settings', 'compression_no_alpha', 'compression_force_alpha',
          'compression_none', 'compression_quality', 'lossy_compression_amount',
          'flip_green_channel', 'normalize_normals', 'use_legacy_gamma', 'source_color_settings',
          'lod_group', 'lod_bias', 'mip_gen_settings', 'num_cinematic_mip_levels', 'mip_load_options',
          'filter', 'address_x', 'address_y', 'preserve_border', 'use_new_mip_filter',
          'power_of_two_mode', 'downscale', 'downscale_options', 'alpha_coverage_thresholds',
          'do_scale_mips_for_alpha_coverage', 'never_stream', 'max_texture_size',
          'global_force_mip_levels_to_be_resident', 'virtual_texture_streaming')
REQUIRED_FIELDS = ('srgb', 'compression_settings', 'flip_green_channel', 'lod_group', 'lod_bias',
                   'mip_gen_settings', 'filter', 'address_x', 'address_y', 'never_stream',
                   'max_texture_size', 'global_force_mip_levels_to_be_resident', 'virtual_texture_streaming')
CVARS = ('r.TextureStreaming', 'r.Streaming.PoolSize', 'r.Streaming.MipBias',
         'r.Streaming.UsePerTextureBias', 'r.Streaming.Boost', 'r.Streaming.MaxEffectiveScreenSize',
         'r.Streaming.HiddenPrimitiveScale', 'r.Streaming.FullyLoadUsedTextures',
         'r.Streaming.UseAllMips', 'r.ScreenPercentage', 'sg.TextureQuality')


def load_helper():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py').resolve(strict=True)
    data = file.read_bytes()
    assert hashlib.sha256(data).hexdigest() == FROZEN_SHA
    h = types.ModuleType('ground_texture_policy_frozen_definitions')
    h.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), h.__dict__)
    assert 'ARGS' not in h.__dict__ and h.sha(file) == FROZEN_SHA
    return h


def sole_editor():
    command = 'ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process -Filter "Name = \'UnrealEditor.exe\'" | ForEach-Object { [int]$_.ProcessId })'
    run = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                         check=True, capture_output=True, text=True, timeout=30,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert json.loads(run.stdout) == [os.getpid()], 'Exactly the current editor process is required'


def property_plain(h, value):
    """Capture reflected struct values without transient Python wrapper addresses."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if hasattr(value, 'get_path_name'):
        return h.path(value)
    if isinstance(value, (list, tuple)):
        return [property_plain(h, row) for row in value]
    if isinstance(value, dict) or callable(getattr(value, 'items', None)):
        return {str(key): property_plain(h, row) for key, row in value.items()}
    if callable(getattr(value, 'to_dict', None)):
        return property_plain(h, value.to_dict())
    return h.plain(value)


def read_property(h, obj, name):
    try:
        return {'status': 'READ', 'value': property_plain(h, obj.get_editor_property(name))}
    except Exception as error:
        return {'status': 'API_FAILURE', 'error': str(error)}


def texture_details(h, texture):
    assert isinstance(texture, h.unreal.Texture2D)
    row = {'path': h.path(texture), 'class': texture.get_class().get_name(),
           'properties': {name: read_property(h, texture, name) for name in FIELDS}, 'metadata': {}}
    # Blueprint_GetSizeX/Y are UFUNCTIONs in installed Texture2D.h360-367.
    # GetImportedSize/GetPixelFormat/GetNumMips are not UFUNCTIONs there.
    for key, method in (('size_x', 'blueprint_get_size_x'), ('size_y', 'blueprint_get_size_y'),
                        ('pixel_format', 'get_pixel_format'), ('num_mips', 'get_num_mips'),
                        ('imported_size', 'get_imported_size')):
        accessor = getattr(texture, method, None)
        if not callable(accessor):
            row['metadata'][key] = {'status': 'API_NOT_EXPOSED', 'method': method}
        else:
            try:
                row['metadata'][key] = {'status': 'READ', 'value': h.plain(accessor())}
            except Exception as error:
                row['metadata'][key] = {'status': 'API_FAILURE', 'method': method, 'error': str(error)}
    return row


def value(row, name):
    entry = row['properties'][name]
    assert entry['status'] == 'READ', (row['path'], name, entry)
    return entry['value']


def assert_source(h, parameter, row):
    for name in REQUIRED_FIELDS:
        value(row, name)
    assert all(row['metadata'][k] == {'status': 'READ', 'value': 4096} for k in ('size_x', 'size_y'))
    assert value(row, 'never_stream') is False and value(row, 'max_texture_size') in (0, 4096)
    assert value(row, 'global_force_mip_levels_to_be_resident') is False
    assert value(row, 'virtual_texture_streaming') is False and value(row, 'lod_bias') == 0
    assert value(row, 'mip_gen_settings') != h.plain(h.unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    kind = parameter.rsplit('_', 1)[1]
    compression = {'Albedo': h.unreal.TextureCompressionSettings.TC_DEFAULT,
                   'Normal': h.unreal.TextureCompressionSettings.TC_NORMALMAP,
                   'PackedMask': h.unreal.TextureCompressionSettings.TC_MASKS}[kind]
    assert value(row, 'srgb') is (kind == 'Albedo')
    assert value(row, 'compression_settings') == h.plain(compression)


def compare_copy(source, copied):
    assert copied['class'] == source['class']
    for name, expected in source['properties'].items():
        actual = copied['properties'][name]
        if name in ('never_stream', 'max_texture_size'):
            assert actual == {'status': 'READ', 'value': True if name == 'never_stream' else 4096}
        elif expected['status'] == 'READ':
            assert actual == expected, (copied['path'], name)
        else:
            assert actual['status'] == expected['status'], (copied['path'], name)
    assert all(copied['metadata'][k] == {'status': 'READ', 'value': 4096} for k in ('size_x', 'size_y'))
    for key in ('pixel_format', 'num_mips', 'imported_size'):
        if source['metadata'][key]['status'] == 'READ':
            assert copied['metadata'][key] == source['metadata'][key], (copied['path'], key)


def instances_after_policy(h, old, new, child_path, items):
    assert set(old) == set(new)
    expected = {x['parameter']: x['destination'] for x in items}
    association = h.plain(h.unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    for path, prior in old.items():
        live = new[path]
        if path != child_path:
            assert live == prior, 'Other material instance changed'
            continue
        assert set(live) == set(prior)
        assert all(live[k] == prior[k] for k in prior if k not in ('textures', 'texture_overrides'))
        assert live['textures'] == dict(prior['textures'], **expected)
        assert [r for r in live['texture_overrides'] if r['name'] not in expected] == [
            r for r in prior['texture_overrides'] if r['name'] not in expected]
        selected = [r for r in live['texture_overrides'] if r['name'] in expected]
        assert len(selected) == 12 and {r['name'] for r in selected} == set(expected)
        assert all(r['association'] == association and r['index'] == -1
                   and r['value'] == expected[r['name']] for r in selected)


def run(args):
    h = load_helper()
    script = (h.HERE / 'native_ground_texture_policy.py').resolve(strict=True)
    script_sha = h.sha(script)
    mode = args.get('mode', 'inspect')
    assert mode in ('inspect', 'apply', 'verify') and os.getpid() == args['expected_pid']
    sole_editor()
    files, docs = {}, {}
    for key in ('baseline_receipt', 'graph_receipt', 'backup_manifest', 'plan_receipt'):
        files[key], docs[key] = h.load_document(args[key])
        assert h.sha(files[key]) == args[key + '_sha256'], key
    baseline, graph, manifest, plan = (docs[k] for k in ('baseline_receipt', 'graph_receipt', 'backup_manifest', 'plan_receipt'))
    assignment_file = h.HERE / 'ASSIGNMENT.json'
    assert h.sha(assignment_file) == ASSIGNMENT_SHA
    assignment = json.loads(assignment_file.read_text(encoding='utf-8-sig'))
    world = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = h.one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    assert area in ('GazaShujaiya', 'GazaRimal')
    assert baseline['pid'] == os.getpid() and baseline['world'] == named_map and baseline['area'] == area
    assert baseline['graph_expression_count'] == graph['graph_count'] == 1015
    assert graph['status'] in ('IDENTITY_VERIFIED_READ_ONLY', 'IDENTITY_VERIFIED_READ_ONLY_TEXTURE_POLICY')
    assert graph['complete_code_input_output_mip_identity_equal']
    assert graph['frozen_helper_sha256'] == manifest['helper_sha256'] == FROZEN_SHA
    assert graph['backup_manifest_sha256'] == h.sha(files['backup_manifest'])
    assert len(manifest['file_bindings']) == len(manifest['sealed_files']) == 17
    assert len(manifest['preserved_files']) == 65 and manifest['ordinary_generation_authorized'] is False
    assert baseline['cooking_paused'] and not baseline['autosave'] and not any(baseline['callbacks'].values())
    assert len(baseline['hdas']) == 1 and all(not a['auto_cook'] and not a['auto_bake'] for a in baseline['hdas'])
    assert plan['schema'] == 'environmentpipeline.ground_texture_policy_plan.v1'
    assert plan['policy'] == {'never_stream': True, 'max_texture_size': 4096,
                              'global_force_mip_levels_to_be_resident': False}
    assert Path(plan['graph_receipt']).resolve(strict=True) == files['graph_receipt']
    assert plan['graph_receipt_sha256'] == h.sha(files['graph_receipt'])
    items = plan['items']
    assert len(items) == 12 and {r['parameter'] for r in items} == set(PARAMETERS)
    assert len({r['source'] for r in items}) == len({r['destination'] for r in items}) == 12
    destination_root = h.SURFACE + '/Textures/Resident4K/'
    for row in items:
        assert set(row) == {'parameter', 'source', 'destination'}
        name = 'T_' + row['parameter'] + '_GeoCityResident4K'
        assert row['destination'] == destination_root + name + '.' + name
        assert row['source'].startswith('/Game/') and row['source'] != row['destination']
    if mode != 'verify':
        assert plan['pid'] == os.getpid() and plan['world'] == named_map and plan['area'] == area
        if mode == 'apply':
            assert graph['pid'] == os.getpid() and graph['world'] == named_map and graph['area'] == area
    master = h.unreal.load_asset(h.MASTER)
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][area])
    assert isinstance(master, h.unreal.Material) and isinstance(child, h.unreal.MaterialInstanceConstant)
    child_path, child_package = h.path(child), child.get_outermost().get_path_name()
    copy_packages = {r['destination'].split('.')[0] for r in items}
    allowed_dirty = copy_packages | {child_package}
    source_files = {str(h.package_file(r['source']).resolve(strict=True)) for r in items}
    original_files = {str(Path(p).resolve(strict=True)) for p in manifest['file_bindings']} | source_files
    for family in ('preserved_files', 'sealed_files'):
        for relative, expected in manifest[family].items():
            file = (h.ROOT / relative).resolve(strict=True)
            assert file.is_relative_to(h.ROOT) and h.sha(file) == expected
            original_files.add(str(file))
    for row in manifest['file_bindings'].values():
        assert h.sha(Path(row['backup']).resolve(strict=True)) == row['sha256']

    def dirty():
        return {'maps': sorted(h.path(p) for p in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                'content': sorted(h.path(p) for p in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}

    def copies():
        return {r['parameter']: {'asset_exists': h.unreal.EditorAssetLibrary.does_asset_exist(r['destination']),
                 'disk': h.disk_state(h.package_file(r['destination']))} for r in items}

    def snapshot():
        sources, actors = h.guard(assignment, named_map, require_authoring=(mode == 'apply'))
        assert len(sources) == 12
        nodes = {h.path(e): h.describe(master, e) for e in h.LIB.get_material_expressions(master)}
        assert nodes == graph['nodes'] and len(nodes) == 1015
        roots = {k: h.path(h.LIB.get_material_property_input_node(master, prop)) for k, prop in h.PROPERTIES.items()}
        settings = {k: h.plain(master.get_editor_property(k)) for k in graph['material_settings']}
        assert roots == graph['roots'] and settings == graph['material_settings']
        grass_nodes = [e for e in h.LIB.get_material_expressions(master)
                       if isinstance(e, h.unreal.MaterialExpressionLandscapeGrassOutput)]
        assert len(grass_nodes) == 1
        grass = {'graph': {p: h.describe(master, e) for p, e in h.reachable(master, grass_nodes).items()},
                 'settings': h.grass_settings(h.unreal.load_asset(h.GRASS)),
                 'effective_coverage': {h.path(a): float(h.LIB.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage'))
                    for a in actors if isinstance(a, h.unreal.LandscapeProxy)}}
        assert grass['graph'] == graph['grass']['graph'] and grass['settings'] == graph['grass']['settings']
        assert set(grass['effective_coverage'].values()) == set(graph['grass']['effective_coverage'].values())
        return {'sources': sources, 'scene': h.scene_state(actors), 'nodes': nodes, 'roots': roots,
                'material_settings': settings, 'grass': grass,
                'instances': {p: h.material_state(master, h.unreal.load_asset(p)) for p in graph['instances']},
                'cvars': {name: h.unreal.SystemLibrary.get_console_variable_string_value(name) for name in CVARS},
                'dirty': dirty(), 'disk': {p: h.sha(p) for p in sorted(original_files)}, 'copies': copies(),
                'source_textures': {r['parameter']: texture_details(h, h.unreal.load_asset(r['source'])) for r in items}}

    before = snapshot()
    assert before['sources'] == baseline['sources'] and before['dirty'] == {
        'maps': sorted(baseline['dirty_maps']), 'content': sorted(baseline['dirty_content'])}
    assert before['dirty']['maps'] == []
    assert before['scene']['transforms'] == baseline['actor_transforms']
    assert before['scene']['native_mesh_components'] == sorted(baseline['native_mesh_components'], key=lambda r: r['component'])
    expected_landscapes = sorted([{'path': r['path'], 'material': r['material']['path'], 'hidden': r['hidden']}
                                 for r in baseline['landscapes']], key=lambda r: r['path'])
    assert [{k: v for k, v in r.items() if k != 'layers'} for r in before['scene']['landscapes']] == expected_landscapes
    assert len(before['scene']['transforms']) == baseline['actor_count']
    for row in items:
        assert_source(h, row['parameter'], before['source_textures'][row['parameter']])
    if mode != 'verify':
        assert before['dirty']['content'] == [] and before['instances'] == graph['instances']
        assert all(before['disk'][str(Path(p).resolve(strict=True))] == expected for p, expected in graph['package_sha256'].items())
        assert all(before['instances'][child_path]['textures'][r['parameter']] == r['source'] for r in items)
    else:
        assert set(before['dirty']['content']) <= allowed_dirty

    inspection = application = None
    if mode in ('apply', 'verify'):
        keys = ('inspect_receipt', 'review_receipt') if mode == 'apply' else ('inspect_receipt', 'apply_receipt')
        for key in keys:
            files[key], docs[key] = h.load_document(args[key])
            assert h.sha(files[key]) == args[key + '_sha256'], key
        inspection = docs['inspect_receipt']
        assert inspection['status'] == 'CANDIDATE_REQUIRES_ROOT_REVIEW' and inspection['mode'] == 'inspect'
        assert inspection['helper_sha256'] == script_sha and inspection['plan_sha256'] == h.sha(files['plan_receipt'])
        assert inspection['graph_receipt_sha256'] == h.sha(files['graph_receipt'])
        assert inspection['backup_manifest_sha256'] == h.sha(files['backup_manifest'])
        if mode == 'apply':
            review = docs['review_receipt']
            assert review['status'] == 'APPROVED_GROUND_TEXTURE_POLICY_APPLY'
            assert review['pid'] == inspection['pid'] == os.getpid()
            assert review['world'] == inspection['world'] == named_map and review['area'] == inspection['area'] == area
            for field, expected in (('helper_sha256', script_sha), ('inspect_receipt_sha256', h.sha(files['inspect_receipt'])),
                                    ('plan_sha256', h.sha(files['plan_receipt'])), ('graph_receipt_sha256', h.sha(files['graph_receipt'])),
                                    ('baseline_receipt_sha256', h.sha(files['baseline_receipt'])), ('backup_manifest_sha256', h.sha(files['backup_manifest']))):
                assert review[field] == expected, field
            assert before == inspection['before'], 'Reviewed inspection state has changed'
        else:
            application = docs['apply_receipt']
            assert application['status'] == 'TEXTURE_POLICY_APPLIED_NO_EXPLICIT_SAVE' and application['mode'] == 'apply'
            assert application['helper_sha256'] == script_sha and application['plan']['items'] == items
            assert inspection['world'] == named_map and inspection['area'] == area, 'Current-area pre-binding inspection required'
            if application['world'] == named_map:
                assert application['plan_sha256'] == h.sha(files['plan_receipt'])
                assert application['input_files']['inspect_receipt']['sha256'] == h.sha(files['inspect_receipt'])
            else:
                files['binding_review'], binding = h.load_document(args['binding_review'])
                assert h.sha(files['binding_review']) == args['binding_review_sha256']
                assert binding['status'] == 'APPROVED_GROUND_TEXTURE_POLICY_BIND'
                assert binding['world'] == named_map and binding['area'] == area
                assert binding['helper_sha256'] == script_sha and binding['child'] == child_path
                assert binding['inspect_receipt_sha256'] == h.sha(files['inspect_receipt'])
                assert binding['creation_apply_receipt_sha256'] == h.sha(files['apply_receipt'])
                assert binding['plan_sha256'] == h.sha(files['plan_receipt'])
                assert binding['texture_mapping'] == {r['parameter']: r['destination'] for r in items}
            instances_after_policy(h, inspection['before']['instances'], before['instances'], child_path, items)
            for p, expected in inspection['before']['disk'].items():
                if Path(p) == h.package_file(child_package).resolve():
                    expected = args['expected_target_mi_package_sha256']
                assert before['disk'][p] == expected, p
            assert before['source_textures'] == inspection['before']['source_textures']
            assert before['cvars'] == inspection['before']['cvars'] and before['scene'] == inspection['before']['scene']

    label = args['label']
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label)
    out = h.REV / ('GROUND_TEXTURE_POLICY_' + mode + '_' + area + '_' + label + '_PID' + str(os.getpid()) + '.json')
    assert not out.exists()
    result = {'schema': 'environmentpipeline.ground_texture_policy.v1', 'mode': mode, 'status': 'STARTED',
              'pid': os.getpid(), 'world': named_map, 'area': area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'helper_sha256': script_sha, 'frozen_helper_sha256': FROZEN_SHA, 'assignment_sha256': ASSIGNMENT_SHA,
              'plan': plan, 'plan_sha256': h.sha(files['plan_receipt']),
              'graph_receipt_sha256': h.sha(files['graph_receipt']), 'backup_manifest_sha256': h.sha(files['backup_manifest']),
              'input_files': {k: {'file': str(p), 'sha256': h.sha(p)} for k, p in files.items()},
              'before': before, 'created_assets': [], 'bound_parameters': [], 'allowed_dirty_packages': sorted(allowed_dirty),
              'explicit_save_called': False, 'explicit_master_compile_called': False, 'update_material_instance_called': False,
              'native_mutation': mode == 'apply', 'rollback_executed': False,
              'limitations': ['ExpressionGUID is not Python-exposed; ordered parameter identity/value is captured.',
                  'Unexposed texture metadata is unknown; no shader readiness, GPU budget or visual quality is inferred.',
                  'Copy-property PostEditChange and update_material_instance may build resources/shaders; no explicit master compilation.',
                  'Legacy editor_layer_settings is unknown; scene identity and original package hashes are checked.',
                  'No native call here proves full geographic weight/height equality or cooked-platform residency.']}
    attempt = None
    if mode == 'apply':
        assert all(not r['asset_exists'] and not r['disk']['exists'] for r in before['copies'].values())
        attempt = h.REV / ('GROUND_TEXTURE_POLICY_ONCE_' + h.sha(files['plan_receipt']) + '.json')
        with attempt.open('x', encoding='utf-8') as file:
            file.write(json.dumps({'status': 'ATTEMPT_RESERVED', 'pid': os.getpid(), 'helper_sha256': script_sha,
                                   'plan_sha256': h.sha(files['plan_receipt']), 'receipt': str(out)}, indent=2))
    with out.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2))
    failure = None
    try:
        if mode == 'apply':
            tools = h.unreal.AssetToolsHelpers.get_asset_tools()
            copied_objects = {}
            for row in items:
                destination = row['destination'].split('.')[0]
                assert not h.unreal.EditorAssetLibrary.does_asset_exist(destination)
                assert not h.package_file(destination).exists()
                directory, name = destination.rsplit('/', 1)
                copied = tools.duplicate_asset(name, directory, h.unreal.load_asset(row['source']))
                result['created_assets'].append({'parameter': row['parameter'], 'path': h.path(copied),
                                                'disk_immediately_after_duplicate': h.disk_state(h.package_file(destination))})
                assert copied and h.path(copied) == row['destination']
                assert not h.package_file(destination).exists(), 'Implicit target save: stop before binding'
                copied.set_editor_property('never_stream', True)
                copied.set_editor_property('max_texture_size', 4096)
                compare_copy(before['source_textures'][row['parameter']], texture_details(h, copied))
                copied_objects[row['parameter']] = copied
            for row in items:
                assert h.LIB.set_material_instance_texture_parameter_value(child, row['parameter'], copied_objects[row['parameter']])
                result['bound_parameters'].append(row['parameter'])
            result['update_material_instance_called'] = True
            h.LIB.update_material_instance(child)
        if mode in ('apply', 'verify'):
            copy_details = {r['parameter']: texture_details(h, h.unreal.load_asset(r['destination'])) for r in items}
            for row in items:
                compare_copy(before['source_textures'][row['parameter']], copy_details[row['parameter']])
            result['copy_textures'] = copy_details
        after = snapshot()
        result['after'] = after
        for key in ('sources', 'scene', 'nodes', 'roots', 'material_settings', 'grass', 'cvars', 'disk', 'source_textures'):
            assert after[key] == before[key], key
        if mode == 'apply':
            instances_after_policy(h, before['instances'], after['instances'], child_path, items)
            assert after['dirty']['maps'] == [] and set(after['dirty']['content']) <= allowed_dirty
            assert all(not r['disk']['exists'] and r['asset_exists'] for r in after['copies'].values())
        else:
            assert after['instances'] == before['instances'] and after['dirty'] == before['dirty']
            assert after['copies'] == before['copies']
        sole_editor()
        assert h.sha(script) == script_sha and h.sha(h.SCRIPT) == FROZEN_SHA and h.sha(assignment_file) == ASSIGNMENT_SHA
        assert all(h.sha(p) == result['input_files'][k]['sha256'] for k, p in files.items())
        result.update(graph_count=1015, graph_sha256=h.digest(after['nodes']),
                      nodes=after['nodes'], roots=after['roots'], material_settings=after['material_settings'],
                      instances=after['instances'], grass=after['grass'], scene=after['scene'], cvars=after['cvars'],
                      package_sha256=after['disk'],
                      complete_code_input_output_mip_identity_equal=True, preserved_grass=True, preserved_scene=True,
                      preserved_cvars=True, preserved_original_package_files=True, preserved_source_texture_properties=True,
                      exact_twelve_copy_properties_and_mapping_verified=mode in ('apply', 'verify'))
        result['status'] = {'inspect': 'CANDIDATE_REQUIRES_ROOT_REVIEW', 'apply': 'TEXTURE_POLICY_APPLIED_NO_EXPLICIT_SAVE',
                            'verify': 'IDENTITY_VERIFIED_READ_ONLY_TEXTURE_POLICY'}[mode]
    except Exception as error:
        failure = error
        result['status'] = 'FAILED_PARTIAL_STATE_PRESERVED' if mode == 'apply' else 'FAILED_READ_ONLY_CHECK'
        result['error'] = repr(error)
        try:
            result['failure_dirty'] = dirty()
            result['failure_all_twelve_copy_states'] = copies()
            result['failure_original_disk_hashes'] = {p: h.sha(p) for p in sorted(original_files)}
        except Exception as capture_error:
            result['failure_capture_error'] = repr(capture_error)
    finally:
        out.write_text(json.dumps(result, indent=2), encoding='utf-8')
        if attempt:
            attempt.write_text(json.dumps({'status': result['status'], 'pid': os.getpid(), 'helper_sha256': script_sha,
                                          'receipt': str(out), 'receipt_sha256': h.sha(out)}, indent=2), encoding='utf-8')
    if failure:
        raise failure
    return {'receipt': str(out), 'sha256': h.sha(out), 'status': result['status'], 'pid': os.getpid(),
            'world': named_map, 'area': area, 'graph_count': 1015, 'native_mutation': mode == 'apply'}


if 'ARGS' in globals():
    RESULT = run(ARGS)
