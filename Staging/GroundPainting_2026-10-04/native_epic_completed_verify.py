"""Root-reviewed Epic StarterContent adaptation; import without ARGS is idle.

inspect/apply/verify require expected_pid,label and SHA-bound baseline_receipt,
graph_receipt,epic_native_receipt,source_manifest,mutation_backup,plan_receipt;
held_copy_package_sha256 binds the already saved, unused recovery copy.
apply also requires inspect_receipt+review_receipt, with each *_sha256.
verify requires apply_receipt+sha and expected_owned_package_sha256 (exact
master/current-child disk hashes; unchanged pre-save or reviewed post-save).
Only eight R/AO root edges, three macro properties and enumerated current-child
overrides change. All1015 nodes/69 layers remain. No copying, texture edits,
explicit compilation/save, scene edits, force/loading/CVar call or cleanup.
Epic D/N+macro are adapted to retained sampling, not original-master clones.
"""
import copy
import datetime
import hashlib
import json
import os
import struct
import types
from pathlib import Path

FROZEN_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
POLICY_SHA = 'bdba22a3bcf801663788166649e3fd593704507f133995a1085ed0b37c2404b4'
ASSIGNMENT_SHA = 'c3c49a9baabdfe357a5852d383501d0ac0396bfc7a795b58762ac52b61d3fec7'
EPIC_SHA = '9b7785af647a3eaf5674cf45c8f1b56aa9d80da1f02d0848da46ebad391598b6'
LAYERS = ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')
MACRO = '/Game/StarterContent/Textures/T_MacroVariation.T_MacroVariation'
HOLD = '/Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/Resident4K/T_Sand_01_Albedo_GeoCityResident4K'
ROUGH = {'Sand_01': 105, 'Sand_02': 106, 'Dirt_Path': 103, 'Sand_Path': 108}
SAMPLERS = ('MaterialExpressionTextureObjectParameter_154', 'MaterialExpressionTextureSample_0')
PALETTE = {layer + '_' + kind: '/Game/StarterContent/Textures/T_' +
           ('Rock_Sandstone' if layer == 'Sand_02' else 'Ground_Gravel') + '_' +
           ('D' if kind == 'Albedo' else 'N') for layer in LAYERS for kind in ('Albedo', 'Normal')}
PALETTE = {key: path + '.' + path.rsplit('/', 1)[1] for key, path in PALETTE.items()}
PALETTE['Ground_MacroMask'] = MACRO


def load_definitions():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_ground_texture_policy.py').resolve(strict=True)
    data = file.read_bytes()
    assert hashlib.sha256(data).hexdigest() == POLICY_SHA
    p = types.ModuleType('epic_ground_property_definitions')
    p.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), p.__dict__)
    assert 'ARGS' not in p.__dict__ and hashlib.sha256(file.read_bytes()).hexdigest() == POLICY_SHA
    h = p.load_helper()
    assert h.sha(h.SCRIPT) == FROZEN_SHA
    return h, p, file


def float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def expected_graph(h, original, prefix):
    result = copy.deepcopy(original)
    node = lambda name: prefix + ':' + name
    for layer in LAYERS:
        result[node('MaterialExpressionLandscapeLayerBlend_8')]['edges']['Layer ' + layer] = {
            'source': node('MaterialExpressionScalarParameter_' + str(ROUGH[layer])), 'output': ''}
        result[node('MaterialExpressionLandscapeLayerBlend_0')]['edges']['Layer ' + layer] = {
            'source': node('MaterialExpressionConstant_1'), 'output': ''}
    for name in SAMPLERS:
        result[node(name)]['properties']['sampler_type'] = h.plain(h.unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    result[node(SAMPLERS[0])]['properties']['texture'] = MACRO
    return result


def persistent_state(state):
    """Resource-size readbacks may settle; no persistent field is omitted."""
    result = copy.deepcopy(state)
    for row in result['epic_textures'].values():
        row.pop('metadata')
    result['held_texture'].pop('metadata')
    return result


def compare_instances(h, old, new, child_path, plan):
    """Only inherited macro resolution changes on the two untouched instances."""
    assert set(old) == set(new)
    association = h.plain(h.unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    for path, prior in old.items():
        live = new[path]
        assert set(live) == set(prior)
        assert not any(r['name'] == 'Ground_MacroMask' for r in prior['texture_overrides'])
        expected_textures = dict(prior['textures'], Ground_MacroMask=MACRO)
        if path != child_path:
            assert live['textures'] == expected_textures
            assert all(live[k] == prior[k] for k in prior if k != 'textures'), path
            continue
        assert live['path'] == prior['path'] and live['parent'] == prior['parent']
        assert live['override_guid_capture'] == prior['override_guid_capture']
        for kind, resolved, overrides in (('textures', 'textures', 'texture_overrides'),
                                          ('scalars', 'scalars', 'scalar_overrides'),
                                          ('vectors', 'vectors', 'vector_overrides')):
            updates = plan[kind]
            if kind == 'scalars':
                updates = {k: float32(v) for k, v in updates.items()}
            elif kind == 'vectors':
                updates = {k: [float32(v) for v in row] for k, row in updates.items()}
            expected = dict(expected_textures if kind == 'textures' else prior[resolved], **updates)
            assert live[resolved] == expected, (path, kind)
            assert [r for r in live[overrides] if r['name'] not in updates] == [
                r for r in prior[overrides] if r['name'] not in updates], (path, overrides)
            selected = [r for r in live[overrides] if r['name'] in updates]
            assert len(selected) == len(updates) and {r['name'] for r in selected} == set(updates)
            assert all(r['association'] == association and r['index'] == -1 and
                       r['value'] == updates[r['name']] for r in selected), (path, overrides)


def run(args):
    h, p, policy_file = load_definitions()
    script = (h.HERE / 'native_epic_completed_verify.py').resolve(strict=True)
    script_sha = h.sha(script)
    mode = args.get('mode', 'inspect')
    assert mode == 'verify' and args['expected_pid'] == os.getpid()
    p.sole_editor()
    files, docs = {}, {}
    for key in ('baseline_receipt', 'graph_receipt', 'epic_native_receipt',
                'source_manifest', 'mutation_backup', 'plan_receipt'):
        files[key], docs[key] = h.load_document(args[key])
        assert h.sha(files[key]) == args[key + '_sha256'], key
    baseline, graph, epic, source, backup, plan = [docs[k] for k in (
        'baseline_receipt', 'graph_receipt', 'epic_native_receipt', 'source_manifest', 'mutation_backup', 'plan_receipt')]
    assert h.sha(files['epic_native_receipt']) == EPIC_SHA and epic['status'] == 'EPIC_ORIGINAL_GRAPHS_READ_ONLY'
    assert epic['native_mutation'] is False and len(epic['natural_nodes']) == 1015
    assert graph['status'] == 'IDENTITY_VERIFIED_READ_ONLY' and graph['graph_count'] == 1015
    assert graph['complete_code_input_output_mip_identity_equal'] and graph['frozen_helper_sha256'] == FROZEN_SHA
    assert graph['nodes'] == epic['natural_nodes'] and graph['instances'] == epic['instances']
    assert graph['backup_manifest_sha256'] == h.sha(files['source_manifest'])
    assert source['helper_sha256'] == FROZEN_SHA and len(source['file_bindings']) == len(source['sealed_files']) == 17
    assert len(source['preserved_files']) == 65 and source['ordinary_generation_authorized'] is False
    assignment_file = h.HERE / 'ASSIGNMENT.json'
    assert h.sha(assignment_file) == ASSIGNMENT_SHA
    assignment = json.loads(assignment_file.read_text(encoding='utf-8-sig'))
    world = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = h.one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    assert area == plan['area'] == 'GazaShujaiya' and named_map == plan['world']
    assert baseline['pid'] == os.getpid() and baseline['world'] == named_map and baseline['area'] == area
    assert baseline['graph_expression_count'] == 1015 and baseline['cooking_paused'] and not baseline['autosave']
    assert not any(baseline['callbacks'].values()) and len(baseline['hdas']) == 1
    assert all(not a['auto_cook'] and not a['auto_bake'] for a in baseline['hdas'])
    assert plan['schema'] == 'environmentpipeline.epic_ground_plan.v1' and plan['textures'] == PALETTE
    assert plan['scalars'] == {layer + '_Roughness': .8 for layer in LAYERS}
    assert set(plan['vectors']) == {layer + '_' + kind for layer in LAYERS for kind in ('Tint', 'TileCm')}
    for layer in LAYERS:
        assert plan['vectors'][layer + '_Tint'] == [1, 1, 1, 1]
        tile = plan['vectors'][layer + '_TileCm']
        assert len(tile) == 4 and tile[0] == tile[1] == tile[2] and 50 <= tile[0] <= 400 and tile[3] == 1
    assert plan['graph_receipt_sha256'] == h.sha(files['graph_receipt']) and plan['epic_native_receipt_sha256'] == EPIC_SHA
    assert backup['ready'] is True and backup['ready_for_epic_graph'] is True
    assert backup['world'] == named_map and backup['execution_thread_id'] == assignment['execution_thread_id']
    assert backup['plan_sha256'] == h.sha(files['plan_receipt']) and backup['epic_native_receipt_sha256'] == EPIC_SHA
    if mode != 'verify':
        assert plan['pid'] == backup['pid'] == graph['pid'] == os.getpid()
    master = h.unreal.load_asset(h.MASTER)
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][area])
    assert isinstance(master, h.unreal.Material) and isinstance(child, h.unreal.MaterialInstanceConstant)
    prefix, child_path = h.path(master), h.path(child)
    owned = {str(h.package_file(h.MASTER).resolve()), str(h.package_file(child_path).resolve())}
    required_backups = owned | {str(h.package_file(v).resolve()) for v in PALETTE.values()}
    assert set(backup['file_bindings']) == required_backups and len(required_backups) == 7
    for name, row in backup['file_bindings'].items():
        assert h.sha(Path(row['backup']).resolve(strict=True)) == row['sha256'], name
    protected = {str(Path(file).resolve(strict=True)) for file in source['file_bindings']}
    protected.update(str(h.package_file(asset).resolve(strict=True)) for asset in epic['original_file_sha256'])
    hold_file = h.package_file(HOLD).resolve(strict=True)
    assert h.sha(hold_file) == args['held_copy_package_sha256']
    protected.add(str(hold_file))
    for family in ('sealed_files', 'preserved_files'):
        for relative, expected in source[family].items():
            file = (h.ROOT / relative).resolve(strict=True)
            assert file.is_relative_to(h.ROOT) and h.sha(file) == expected
            protected.add(str(file))
    for row in source['file_bindings'].values():
        assert h.sha(Path(row['backup']).resolve(strict=True)) == row['sha256']
    for asset, expected in epic['original_file_sha256'].items():
        assert h.sha(h.package_file(asset)) == expected
    expected_nodes = expected_graph(h, graph['nodes'], prefix)
    allowed_dirty = {master.get_outermost().get_path_name(), child.get_outermost().get_path_name()}

    def snapshot():
        modules, actors = h.guard(assignment, named_map, require_authoring=(mode == 'apply'))
        assert len(modules) == 12
        nodes = {h.path(e): h.describe(master, e) for e in h.LIB.get_material_expressions(master)}
        grass_nodes = [e for e in h.LIB.get_material_expressions(master)
                       if isinstance(e, h.unreal.MaterialExpressionLandscapeGrassOutput)]
        assert len(grass_nodes) == 1
        return {'sources': modules, 'nodes': nodes,
                'roots': {k: h.path(h.LIB.get_material_property_input_node(master, prop)) for k, prop in h.PROPERTIES.items()},
                'material_settings': {k: h.plain(master.get_editor_property(k)) for k in graph['material_settings']},
                'instances': {k: h.material_state(master, h.unreal.load_asset(k)) for k in graph['instances']},
                'grass': {'graph': {q: h.describe(master, e) for q, e in h.reachable(master, grass_nodes).items()},
                    'settings': h.grass_settings(h.unreal.load_asset(h.GRASS)),
                    'effective_coverage': {h.path(a): float(h.LIB.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage'))
                        for a in actors if isinstance(a, h.unreal.LandscapeProxy)}},
                'scene': h.scene_state(actors),
                'dirty': {'maps': sorted(h.path(x) for x in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                          'content': sorted(h.path(x) for x in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())},
                'disk': {file: h.sha(file) for file in sorted(protected)},
                'cvars': {name: h.unreal.SystemLibrary.get_console_variable_string_value(name) for name in p.CVARS},
                'epic_textures': {k: p.texture_details(h, h.unreal.load_asset(k)) for k in epic['textures']},
                'held_texture': p.texture_details(h, h.unreal.load_asset(HOLD))}

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
    assert before['roots'] == graph['roots'] and before['material_settings'] == graph['material_settings']
    assert before['grass'] == graph['grass']
    for asset, prior in epic['textures'].items():
        assert before['epic_textures'][asset]['properties'] == prior['properties'], asset
    for name, asset in PALETTE.items():
        row = before['epic_textures'][asset]
        normal = name.endswith('_Normal')
        assert p.value(row, 'srgb') is (not normal)
        assert p.value(row, 'compression_settings') == h.plain(h.unreal.TextureCompressionSettings.TC_NORMALMAP if normal
                                                            else h.unreal.TextureCompressionSettings.TC_DEFAULT)
    assert before['held_texture']['properties']['never_stream'] == {'status': 'READ', 'value': True}
    assert before['held_texture']['properties']['max_texture_size'] == {'status': 'READ', 'value': 4096}
    if mode == 'verify':
        files['apply_receipt'], application = h.load_document(args['apply_receipt'])
        assert h.sha(files['apply_receipt']) == args['apply_receipt_sha256']
        assert application['status'] == 'EPIC_RECIPE_COMPLETED_FULL_READBACK_NO_SAVE'
        assert application['helper_sha256'] == '7908aff3fea9f76579c02036986fcbb280f0d613378f6e00c2c23951cd18bfc8'
        assert application['plan'] == plan and application['full_21_control_readback_passed'] is True
        assert application['world'] == named_map and application['area'] == area
        failure_file = h.REV / 'EPIC_GROUND_apply_GazaShujaiya_r027_direct_sources_PID32464.json'
        partial_file = h.REV / 'EPIC_PARTIAL_READ_ONLY_PID32464.json'
        assert h.sha(partial_file) == application['partial_receipt_sha256'] == '85fd33b23842031f3f8ef4e80ce0f012cc56c1272ceecdc8857e1577564ca44f'
        partial = json.loads(partial_file.read_text())
        assert h.sha(failure_file) == partial['failure_receipt_sha256']
        failed = json.loads(failure_file.read_text())
        assert failed['helper_sha256'] == '19d99d44b31ca2027a3d814c76dd5ab1ff6d17dd44578cd2a55ad880a9d3a5c0'
        assert failed['status'] == 'FAILED_PARTIAL_STATE_PRESERVED' and failed['plan_sha256'] == h.sha(files['plan_receipt'])
        assert application['original_before'] == failed['before']
        assert before['nodes'] == application['after']['nodes'] == expected_nodes
        assert before['instances'] == application['after']['instances']
        compare_instances(h, application['original_before']['instances'], before['instances'], child_path, plan)
        assert before['scene'] == application['original_before']['scene'] and before['cvars'] == application['original_before']['cvars']
        assert before['held_texture']['properties'] == application['original_before']['held_texture']['properties']
        assert before['grass'] == application['original_before']['grass'] and before['roots'] == application['original_before']['roots']
        assert before['material_settings'] == application['original_before']['material_settings']
        result_origin = {'failed_apply_sha256': h.sha(failure_file), 'partial_readonly_sha256':h.sha(partial_file),
                         'completion_sha256':h.sha(files['apply_receipt']), 'completion_helper_sha256':application['helper_sha256']}
        expected_hashes = args['expected_owned_package_sha256']
        assert set(expected_hashes) == owned
        for file, expected in application['original_before']['disk'].items():
            assert before['disk'][file] == expected_hashes[file] if file in owned else before['disk'][file] == expected, file
        assert set(before['dirty']['content']) <= allowed_dirty
    else:
        assert before['nodes'] == graph['nodes'] and before['instances'] == graph['instances']
        assert before['dirty'] == {'maps': [], 'content': []}
        for file, expected in graph['package_sha256'].items():
            assert before['disk'][str(Path(file).resolve(strict=True))] == expected, file
        for file, row in backup['file_bindings'].items():
            assert before['disk'][file] == row['sha256'], file
    if mode == 'apply':
        for key in ('inspect_receipt', 'review_receipt'):
            files[key], docs[key] = h.load_document(args[key])
            assert h.sha(files[key]) == args[key + '_sha256']
        inspection, review = docs['inspect_receipt'], docs['review_receipt']
        assert inspection['status'] == 'EPIC_GROUND_CANDIDATE_REQUIRES_ROOT_REVIEW'
        assert persistent_state(inspection['before']) == persistent_state(before), 'Reviewed persistent state changed'
        assert inspection['helper_sha256'] == script_sha and inspection['plan_sha256'] == h.sha(files['plan_receipt'])
        assert review['status'] == 'APPROVED_EPIC_GROUND_INTEGRATION'
        assert review['pid'] == os.getpid() and review['world'] == named_map and review['area'] == area
        for key, expected in {'helper_sha256': script_sha, 'inspect_receipt_sha256': h.sha(files['inspect_receipt']),
            'baseline_receipt_sha256': h.sha(files['baseline_receipt']), 'plan_sha256': h.sha(files['plan_receipt']),
            'graph_receipt_sha256': h.sha(files['graph_receipt']), 'epic_native_receipt_sha256': EPIC_SHA,
            'source_manifest_sha256': h.sha(files['source_manifest']), 'mutation_backup_sha256': h.sha(files['mutation_backup']),
            'held_copy_package_sha256': args['held_copy_package_sha256']}.items():
            assert review[key] == expected, key
    label = args['label']
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label)
    out = h.REV / ('EPIC_GROUND_' + mode + '_' + area + '_' + label + '_PID' + str(os.getpid()) + '.json')
    assert not out.exists()
    result = {'schema': 'environmentpipeline.epic_ground_integration.v1', 'status': 'STARTED', 'mode': mode,
        'pid': os.getpid(), 'world': named_map, 'area': area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'helper_sha256': script_sha, 'frozen_helper_sha256': FROZEN_SHA, 'property_helper_sha256': POLICY_SHA,
        'plan': plan, 'plan_sha256': h.sha(files['plan_receipt']), 'graph_receipt_sha256': h.sha(files['graph_receipt']),
        'epic_native_receipt_sha256': EPIC_SHA, 'source_manifest_sha256': h.sha(files['source_manifest']),
        'mutation_backup_sha256': h.sha(files['mutation_backup']), 'before': before,
        'input_files': {k: {'file': str(v), 'sha256': h.sha(v)} for k, v in files.items()},
        'operation_origin':result_origin, 'modified_pins': [], 'modified_properties': [], 'set_parameters': [], 'created_assets': [],
        'allowed_dirty_packages': sorted(allowed_dirty), 'explicit_save_called': False,
        'explicit_master_compile_called': False, 'update_material_instance_called': False,
        'native_mutation': mode == 'apply', 'rollback_executed': False,
        'limitations': ['Adapted Epic source palette with constant dry maximum roughness .8 and AO1; original material graphs are not cloned.',
            'The shared macro default changes inherited resolution on base/Rimal; their local arrays and all other values remain exact.',
            'Resource-size metadata may change during ordinary readiness; persistent texture properties and all source package hashes remain exact.',
            'ExpressionGUID and legacy editor_layer_settings are Python-unexposed; no complete serialized GUID or paint capture is claimed.',
            'No shader/GPU/ordinary streaming/visual acceptance, cooked residency or geographic sample equality is inferred.']}
    attempt = None
    if mode == 'apply':
        attempt = h.REV / ('EPIC_GROUND_ONCE_' + h.sha(files['plan_receipt']) + '.json')
        with attempt.open('x', encoding='utf-8') as file:
            file.write(json.dumps({'status': 'ATTEMPT_RESERVED', 'pid': os.getpid(), 'helper_sha256': script_sha,
                                   'plan_sha256': h.sha(files['plan_receipt']), 'receipt': str(out)}, indent=2))
    with out.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2))
    failure = None
    try:
        if mode == 'apply':
            objects = {h.path(e): e for e in h.LIB.get_material_expressions(master)}
            node = lambda name: prefix + ':' + name
            for name, field, target in ((SAMPLERS[0], 'texture', h.unreal.load_asset(MACRO)),
                                        (SAMPLERS[0], 'sampler_type', h.unreal.MaterialSamplerType.SAMPLERTYPE_COLOR),
                                        (SAMPLERS[1], 'sampler_type', h.unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)):
                objects[node(name)].set_editor_property(field, target)
                result['modified_properties'].append({'node': node(name), 'property': field,
                    'before': graph['nodes'][node(name)]['properties'][field], 'after': h.plain(target)})
            for layer in LAYERS:
                for root_name, source_name in (('MaterialExpressionLandscapeLayerBlend_8', 'MaterialExpressionScalarParameter_' + str(ROUGH[layer])),
                                               ('MaterialExpressionLandscapeLayerBlend_0', 'MaterialExpressionConstant_1')):
                    pin = 'Layer ' + layer
                    assert pin in graph['nodes'][node(root_name)]['input_names']
                    assert h.LIB.connect_material_expressions(objects[node(source_name)], '', objects[node(root_name)], pin)
                    result['modified_pins'].append({'node': node(root_name), 'pin': pin,
                        'before': graph['nodes'][node(root_name)]['edges'][pin], 'after': expected_nodes[node(root_name)]['edges'][pin]})
            for key, asset in plan['textures'].items():
                assert h.LIB.set_material_instance_texture_parameter_value(child, key, h.unreal.load_asset(asset))
                result['set_parameters'].append(key)
            for key, value in plan['scalars'].items():
                assert h.LIB.set_material_instance_scalar_parameter_value(child, key, value)
                result['set_parameters'].append(key)
            for key, values in plan['vectors'].items():
                assert h.LIB.set_material_instance_vector_parameter_value(child, key, h.unreal.LinearColor(*values))
                result['set_parameters'].append(key)
            result['update_material_instance_called'] = True
            h.LIB.update_material_instance(child)
        after = snapshot()
        result['after'] = after
        assert after['nodes'] == (expected_nodes if mode != 'inspect' else graph['nodes']) and len(after['nodes']) == 1015
        for key in ('sources', 'scene', 'roots', 'material_settings', 'grass', 'cvars', 'disk'):
            assert after[key] == before[key], key
        for asset in before['epic_textures']:
            assert after['epic_textures'][asset]['properties'] == before['epic_textures'][asset]['properties'], asset
        assert after['held_texture']['properties'] == before['held_texture']['properties']
        if mode == 'apply':
            compare_instances(h, before['instances'], after['instances'], child_path, plan)
            assert after['dirty']['maps'] == [] and set(after['dirty']['content']) <= allowed_dirty
        else:
            assert after['instances'] == before['instances'] and after['dirty'] == before['dirty']
        p.sole_editor()
        assert h.sha(script) == script_sha and h.sha(policy_file) == POLICY_SHA and h.sha(h.SCRIPT) == FROZEN_SHA
        assert h.sha(assignment_file) == ASSIGNMENT_SHA
        assert all(h.sha(file) == result['input_files'][key]['sha256'] for key, file in files.items())
        result.update(graph_count=1015, nodes=after['nodes'], roots=after['roots'], material_settings=after['material_settings'],
            instances=after['instances'], grass=after['grass'], scene=after['scene'], cvars=after['cvars'], package_sha256=after['disk'],
            graph_sha256=h.digest(after['nodes']), complete_code_input_output_mip_identity_equal=True,
            preserved_1015_nodes=True, preserved_69_layer_names=True, preserved_grass=True, preserved_scene=True,
            preserved_cvars=True, preserved_original_files=True, preserved_epic_texture_properties=True, held_copy_unchanged=True)
        result['status'] = {'inspect': 'EPIC_GROUND_CANDIDATE_REQUIRES_ROOT_REVIEW',
            'apply': 'EPIC_GROUND_APPLIED_NO_EXPLICIT_SAVE', 'verify': 'IDENTITY_VERIFIED_READ_ONLY_EPIC_GROUND'}[mode]
    except Exception as error:
        failure = error
        result['status'] = 'FAILED_PARTIAL_STATE_PRESERVED' if mode == 'apply' else 'FAILED_READ_ONLY_CHECK'
        result['error'] = repr(error)
        try:
            result['failure_dirty'] = {'maps': sorted(h.path(x) for x in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                                       'content': sorted(h.path(x) for x in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
            result['failure_disk'] = {file: h.disk_state(file) for file in sorted(protected)}
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
