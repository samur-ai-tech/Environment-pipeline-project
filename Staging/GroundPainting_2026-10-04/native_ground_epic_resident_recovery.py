"""Recover one proven Epic2K copy; create three, strict ordinary readiness, bind.

Common ARGS: mode(inspect/apply/bind/verify),expected_pid,label,
held_copy_package_sha256 and SHA-bound baseline_receipt,reference_receipt,
epic_native_receipt,source_manifest,mutation_backup,plan_receipt,failure_receipt.
Failure SHA and frozen origin helper are explicitly pinned; no failed proof promotion.
After creation, inspect/bind/verify additionally bind prepared_receipt+SHA.
Apply/bind bind inspect_receipt+review_receipt and SHAs. Verify binds the strict
inspect_receipt+bind_receipt and exact expected_target_mi_package_sha256 plus
expected_copy_package_sha256{four absolute files:SHA or None when unsaved}.
No graph/source/actor edits, compile/save, loading/force/CVar call or cleanup.
Apply reuses1 strict-ready copy and creates only3, setting2 policy fields.
Pending resource sizes0 or powers of two through2048 are not a readiness proof.
Bind requires a new reviewed strict2048 readback, changes only8 current-child
D/N bindings and updates that MI. Partial failures retain objects and receipts.
"""
import copy
import datetime
import hashlib
import json
import os
import types
from pathlib import Path

ORIGIN_SHA = 'fa1721fdbd5cd8d36599bfd587adbf092dc2f2a2f018fd1522c5b662c4d953d7'
FAILURE_SHA = 'c1c36213025db1c11e67694f82a3f7b7c0be3747e9e3d97b2340b16037e177c1'
SH_SHA = '19d99d44b31ca2027a3d814c76dd5ab1ff6d17dd44578cd2a55ad880a9d3a5c0'
REFERENCE_SHA = '89a02abd7c180bdf6b37b0c2e4eaf43636c195f21d0b36afae1f853f22198024'
REFERENCE_HELPER_SHA = '4cdbed23867bb1db0cecb3da312fa05852cb79f0c55abd042746d8e723d57c1a'
STEMS = ('Ground_Gravel_D', 'Ground_Gravel_N', 'Rock_Sandstone_D', 'Rock_Sandstone_N')
COPY_ROOT = '/Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/EpicResident2K/'
COPIES = {'/Game/StarterContent/Textures/T_' + stem + '.T_' + stem:
          COPY_ROOT + 'T_' + stem + '_GeoCityResident2K.T_' + stem + '_GeoCityResident2K' for stem in STEMS}


def load_definitions():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_ground_epic_integration.py').resolve(strict=True)
    data = file.read_bytes()
    assert hashlib.sha256(data).hexdigest() == SH_SHA
    s = types.ModuleType('epic_resident_frozen_definitions')
    s.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), s.__dict__)
    assert 'ARGS' not in s.__dict__ and hashlib.sha256(file.read_bytes()).hexdigest() == SH_SHA
    h, p, policy_file = s.load_definitions()
    return h, p, s, file, policy_file


def compare_copy(original, copied, ready=True):
    assert copied['class'] == original['class'] == 'Texture2D'
    for name, expected in original['properties'].items():
        actual = copied['properties'][name]
        if name in ('never_stream', 'max_texture_size'):
            assert actual == {'status': 'READ', 'value': True if name == 'never_stream' else 2048}
        elif expected['status'] == 'READ':
            assert actual == expected, (copied['path'], name)
        else:
            assert actual['status'] == expected['status'], (copied['path'], name)
    for name in ('size_x', 'size_y'):
        actual = copied['metadata'][name]
        assert actual['status'] == 'READ' and actual['value'] in ((2048,) if ready else (0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048)), actual
    for name in ('pixel_format', 'num_mips', 'imported_size'):
        if original['metadata'][name]['status'] == 'READ':
            assert copied['metadata'][name] == original['metadata'][name], name


def compare_instances(h, old, new, child_key, bindings):
    assert set(old) == set(new)
    association = h.plain(h.unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    for key, prior in old.items():
        live = new[key]
        if key != child_key:
            assert live == prior, 'Other instance changed'
            continue
        assert set(live) == set(prior)
        assert all(live[k] == prior[k] for k in prior if k not in ('textures', 'texture_overrides'))
        assert live['textures'] == dict(prior['textures'], **bindings)
        assert [r for r in live['texture_overrides'] if r['name'] not in bindings] == [
            r for r in prior['texture_overrides'] if r['name'] not in bindings]
        selected = [r for r in live['texture_overrides'] if r['name'] in bindings]
        assert len(selected) == 8 and {r['name'] for r in selected} == set(bindings)
        assert all(r['association'] == association and r['index'] == -1 and
                   r['value'] == bindings[r['name']] for r in selected)


def persistent_state(state):
    result = copy.deepcopy(state)
    for row in result['epic_textures'].values():
        row.pop('metadata')
    result['held_texture'].pop('metadata')
    return result


def run(args):
    h, p, s, sh_file, policy_file = load_definitions()
    script = (h.HERE / 'native_ground_epic_resident_recovery.py').resolve(strict=True)
    origin_file = (h.HERE / 'native_ground_epic_resident.py').resolve(strict=True)
    assert h.sha(origin_file) == ORIGIN_SHA
    script_sha = h.sha(script)
    mode = args.get('mode', 'inspect')
    assert mode in ('inspect', 'apply', 'bind', 'verify') and os.getpid() == args['expected_pid']
    p.sole_editor()
    files, docs = {}, {}
    for key in ('baseline_receipt', 'reference_receipt', 'epic_native_receipt',
                'source_manifest', 'mutation_backup', 'plan_receipt', 'failure_receipt'):
        files[key], docs[key] = h.load_document(args[key])
        assert h.sha(files[key]) == args[key + '_sha256'], key
    baseline, reference, epic, source, backup, plan = [docs[k] for k in (
        'baseline_receipt', 'reference_receipt', 'epic_native_receipt', 'source_manifest', 'mutation_backup', 'plan_receipt')]
    assert h.sha(files['reference_receipt']) == REFERENCE_SHA
    assert reference['status'] == 'IDENTITY_VERIFIED_READ_ONLY_EPIC_GROUND' and reference['helper_sha256'] == REFERENCE_HELPER_SHA
    assert reference['graph_count'] == 1015 and reference['complete_code_input_output_mip_identity_equal']
    failure_origin = docs['failure_receipt']
    assert h.sha(files['failure_receipt']) == FAILURE_SHA
    assert failure_origin['schema'] == 'environmentpipeline.epic_resident.v1'
    assert failure_origin['status'] == 'FAILED_PARTIAL_STATE_PRESERVED' and failure_origin['mode'] == 'apply'
    assert failure_origin['helper_sha256'] == ORIGIN_SHA and failure_origin['plan_sha256'] == h.sha(files['plan_receipt'])
    assert failure_origin['bound_parameters'] == [] and failure_origin['update_material_instance_called'] is False
    assert failure_origin['explicit_save_called'] is False and failure_origin['explicit_master_compile_called'] is False
    assert failure_origin['global_loading_helper_called'] is False and len(failure_origin['created_assets']) == 1
    reused_row = failure_origin['created_assets'][0]
    reused_source = next(iter(COPIES))
    reused_destination = COPIES[reused_source]
    assert reused_row['source'] == reused_source and reused_row['destination'] == reused_row['path'] == reused_destination
    assert not reused_row['disk_immediately_after_duplicate']['exists']
    assert failure_origin['failure_dirty'] == {'maps': [], 'content': [reused_destination.split('.')[0]]}

    assert reference['after']['dirty'] == {'maps': [], 'content': []} and reference['native_mutation'] is False
    assert h.sha(files['epic_native_receipt']) == s.EPIC_SHA and epic['status'] == 'EPIC_ORIGINAL_GRAPHS_READ_ONLY'
    assert reference['source_manifest_sha256'] == h.sha(files['source_manifest'])
    assert reference['frozen_helper_sha256'] == source['helper_sha256'] == s.FROZEN_SHA
    assert len(source['file_bindings']) == len(source['sealed_files']) == 17 and len(source['preserved_files']) == 65
    assert source['ordinary_generation_authorized'] is False
    assignment_file = h.HERE / 'ASSIGNMENT.json'
    assert h.sha(assignment_file) == s.ASSIGNMENT_SHA
    assignment = json.loads(assignment_file.read_text(encoding='utf-8-sig'))
    world = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = h.one((key for key, value in assignment['original_maps'].items() if value == named_map), 'original area')
    assert area == reference['area'] == plan['area'] == 'GazaShujaiya' and named_map == reference['world'] == plan['world']
    assert baseline['pid'] == os.getpid() and baseline['world'] == named_map and baseline['area'] == area
    assert failure_origin['world'] == named_map and failure_origin['area'] == area
    assert baseline['graph_expression_count'] == 1015 and baseline['cooking_paused'] and not baseline['autosave']
    assert len(baseline['hdas']) == 1 and not any(baseline['callbacks'].values())
    assert all(not row['auto_cook'] and not row['auto_bake'] for row in baseline['hdas'])
    bindings = {key: COPIES[value] for key, value in s.PALETTE.items() if key != 'Ground_MacroMask'}
    assert plan['schema'] == 'environmentpipeline.epic_resident_plan.v1'
    assert plan['bindings'] == bindings and len(bindings) == 8
    assert len(plan['items']) == 4 and all(set(row) == {'source', 'destination'} for row in plan['items'])
    assert {row['source']: row['destination'] for row in plan['items']} == COPIES
    assert plan['policy'] == {'never_stream': True, 'max_texture_size': 2048, 'global_force_mip_levels_to_be_resident': False}
    assert plan['reference_sha256'] == REFERENCE_SHA and plan['epic_native_receipt_sha256'] == s.EPIC_SHA
    assert backup['ready'] is True and backup['ready_for_epic_resident'] is True
    assert backup['world'] == named_map and backup['execution_thread_id'] == assignment['execution_thread_id']
    assert backup['plan_sha256'] == h.sha(files['plan_receipt'])
    if mode != 'verify':
        assert plan['pid'] == backup['pid'] == os.getpid()
    master = h.unreal.load_asset(h.MASTER)
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][area])
    assert isinstance(master, h.unreal.Material) and isinstance(child, h.unreal.MaterialInstanceConstant)
    child_key = h.one((key for key, row in reference['instances'].items() if row['path'] == h.path(child)), 'current instance key')
    child_file = str(h.package_file(h.path(child)).resolve(strict=True))
    copy_files = {str(h.package_file(value).resolve()) for value in COPIES.values()}
    copy_packages = {value.split('.')[0] for value in COPIES.values()}
    allowed_dirty = copy_packages | {child.get_outermost().get_path_name()}
    required_backups = {child_file} | {str(h.package_file(asset).resolve(strict=True)) for asset in COPIES}
    assert set(backup['file_bindings']) == required_backups and len(required_backups) == 5
    for row in backup['file_bindings'].values():
        assert h.sha(Path(row['backup']).resolve(strict=True)) == row['sha256']
    protected = {str(Path(file).resolve(strict=True)) for file in reference['package_sha256']}
    assert set(source['file_bindings']) <= protected
    protected.update(str(h.package_file(asset).resolve(strict=True)) for asset in epic['original_file_sha256'])
    hold_file = h.package_file(s.HOLD).resolve(strict=True)
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
    prepared = None
    if args.get('prepared_receipt'):
        files['prepared_receipt'], prepared = h.load_document(args['prepared_receipt'])
        assert h.sha(files['prepared_receipt']) == args['prepared_receipt_sha256']
        assert prepared['status'] == 'EPIC_RESIDENT_RECOVERY_COPIES_CREATED_PENDING_READINESS' and prepared['mode'] == 'apply'
        assert prepared['helper_sha256'] == script_sha and prepared['plan_sha256'] == h.sha(files['plan_receipt'])
        assert prepared['world'] == named_map and prepared['area'] == area and len(prepared['created_assets']) == 3 and len(prepared['reused_assets']) == 1
        assert prepared['reused_assets'][0] == reused_row and prepared['failure_receipt_sha256'] == FAILURE_SHA
        assert {row['source']: row['destination'] for row in prepared['all_copy_provenance']} == COPIES
        assert len(prepared['all_copy_provenance']) == 4
        assert prepared['bound_parameters'] == [] and prepared['update_material_instance_called'] is False
    assert prepared is not None if mode in ('bind', 'verify') else True
    assert prepared is None if mode == 'apply' else True

    def copy_states():
        return {destination: {'asset_exists': h.unreal.EditorAssetLibrary.does_asset_exist(destination),
                'disk': h.disk_state(h.package_file(destination))} for destination in COPIES.values()}

    def snapshot():
        modules, actors = h.guard(assignment, named_map, require_authoring=(mode in ('apply', 'bind')))
        assert len(modules) == 12
        grass_nodes = [e for e in h.LIB.get_material_expressions(master) if isinstance(e, h.unreal.MaterialExpressionLandscapeGrassOutput)]
        assert len(grass_nodes) == 1
        return {'sources': modules, 'nodes': {h.path(e): h.describe(master, e) for e in h.LIB.get_material_expressions(master)},
            'roots': {key: h.path(h.LIB.get_material_property_input_node(master, prop)) for key, prop in h.PROPERTIES.items()},
            'material_settings': {key: h.plain(master.get_editor_property(key)) for key in reference['material_settings']},
            'instances': {key: h.material_state(master, h.unreal.load_asset(key)) for key in reference['instances']},
            'grass': {'graph': {key: h.describe(master, e) for key, e in h.reachable(master, grass_nodes).items()},
                'settings': h.grass_settings(h.unreal.load_asset(h.GRASS)),
                'effective_coverage': {h.path(a): float(h.LIB.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage'))
                    for a in actors if isinstance(a, h.unreal.LandscapeProxy)}},
            'scene': h.scene_state(actors), 'disk': {file: h.sha(file) for file in sorted(protected)},
            'dirty': {'maps': sorted(h.path(x) for x in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                      'content': sorted(h.path(x) for x in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())},
            'cvars': {name: h.unreal.SystemLibrary.get_console_variable_string_value(name) for name in p.CVARS},
            'epic_textures': {key: p.texture_details(h, h.unreal.load_asset(key)) for key in epic['textures']},
            'held_texture': p.texture_details(h, h.unreal.load_asset(s.HOLD)), 'copies': copy_states()}

    before = snapshot()
    assert before['sources'] == baseline['sources'] and before['dirty'] == {'maps': sorted(baseline['dirty_maps']), 'content': sorted(baseline['dirty_content'])}
    assert before['dirty']['maps'] == []
    assert before['scene']['transforms'] == baseline['actor_transforms']
    assert before['scene']['native_mesh_components'] == sorted(baseline['native_mesh_components'], key=lambda row: row['component'])
    landscapes = sorted([{'path': row['path'], 'material': row['material']['path'], 'hidden': row['hidden']}
                         for row in baseline['landscapes']], key=lambda row: row['path'])
    assert [{key: value for key, value in row.items() if key != 'layers'} for row in before['scene']['landscapes']] == landscapes
    assert len(before['scene']['transforms']) == baseline['actor_count']
    assert before['nodes'] == reference['nodes'] and len(before['nodes']) == 1015
    assert before['roots'] == reference['roots'] and before['material_settings'] == reference['material_settings']
    assert before['grass'] == reference['grass'] and before['scene'] == reference['scene'] and before['cvars'] == reference['cvars']
    for asset, prior in epic['textures'].items():
        assert before['epic_textures'][asset]['properties'] == prior['properties'], asset
    for asset in COPIES:
        row = before['epic_textures'][asset]
        assert p.value(row, 'never_stream') is False and p.value(row, 'max_texture_size') == 0
        assert p.value(row, 'global_force_mip_levels_to_be_resident') is False
        assert epic['textures'][asset]['metadata']['size_x'] == epic['textures'][asset]['metadata']['size_y'] == {'status': 'READ', 'value': 2048}
    if mode != 'verify':
        assert before['instances'] == reference['instances']
        for file, expected in reference['package_sha256'].items():
            assert before['disk'][str(Path(file).resolve(strict=True))] == expected
        if prepared is None:
            assert before['dirty'] == failure_origin['failure_dirty']
            assert before['copies'] == failure_origin['failure_all_copy_states']
            reused_details = p.texture_details(h, h.unreal.load_asset(reused_destination))
            compare_copy(before['epic_textures'][reused_source], reused_details)
            assert all(not row['disk']['exists'] and row['asset_exists'] is (key == reused_destination) for key, row in before['copies'].items())
        else:
            assert set(before['dirty']['content']) == copy_packages
            assert all(row['asset_exists'] and not row['disk']['exists'] for row in before['copies'].values())
    prior_persistent, live_persistent = persistent_state(failure_origin['before']), persistent_state(before)
    excluded = ('dirty', 'copies', 'disk', 'instances') if mode == 'verify' else ('dirty', 'copies', 'disk')
    assert all(live_persistent[key] == value for key, value in prior_persistent.items() if key not in excluded)
    if mode != 'verify':
        assert {file: before['disk'][file] for file in failure_origin['before']['disk']} == failure_origin['before']['disk']
    ready_details = {}
    if prepared is not None:
        ready_details = {destination: p.texture_details(h, h.unreal.load_asset(destination)) for destination in COPIES.values()}
        for source_asset, destination in COPIES.items():
            compare_copy(before['epic_textures'][source_asset], ready_details[destination])
    if mode in ('apply', 'bind', 'verify'):
        keys = ('inspect_receipt', 'review_receipt') if mode != 'verify' else ('inspect_receipt', 'bind_receipt')
        for key in keys:
            files[key], docs[key] = h.load_document(args[key])
            assert h.sha(files[key]) == args[key + '_sha256']
        inspection = docs['inspect_receipt']
        assert inspection['status'] == 'EPIC_RESIDENT_RECOVERY_CANDIDATE_REQUIRES_ROOT_REVIEW' and inspection['mode'] == 'inspect'
        assert inspection['helper_sha256'] == script_sha and inspection['plan_sha256'] == h.sha(files['plan_receipt'])
        if mode in ('apply', 'bind'):
            review = docs['review_receipt']
            assert review['status'] == ('APPROVED_EPIC_RESIDENT_RECOVERY_CREATE' if mode == 'apply' else 'APPROVED_EPIC_RESIDENT_RECOVERY_BIND')
            assert review['pid'] == os.getpid() and review['world'] == named_map and review['area'] == area
            assert persistent_state(before) == persistent_state(inspection['before'])
            for key, expected in {'helper_sha256': script_sha, 'inspect_receipt_sha256': h.sha(files['inspect_receipt']),
                'baseline_receipt_sha256': h.sha(files['baseline_receipt']), 'plan_sha256': h.sha(files['plan_receipt']),
                'reference_receipt_sha256': REFERENCE_SHA, 'epic_native_receipt_sha256': s.EPIC_SHA,
                'source_manifest_sha256': h.sha(files['source_manifest']), 'mutation_backup_sha256': h.sha(files['mutation_backup']),
                'held_copy_package_sha256': args['held_copy_package_sha256'],
                'failure_receipt_sha256': FAILURE_SHA, 'origin_helper_sha256': ORIGIN_SHA}.items():
                assert review[key] == expected, key
            if mode == 'bind':
                assert review['prepared_receipt_sha256'] == h.sha(files['prepared_receipt'])
                assert inspection['input_files']['prepared_receipt']['sha256'] == h.sha(files['prepared_receipt'])
                assert inspection['all_four_resources_strict_ready'] and ready_details == inspection['copy_textures']
            else:
                assert inspection['inspect_stage'] == 'RECOVERY_CREATE_ONLY'
        else:
            application = docs['bind_receipt']
            assert application['status'] == 'EPIC_RESIDENT_RECOVERY_BOUND_NO_EXPLICIT_SAVE' and application['mode'] == 'bind'
            assert application['helper_sha256'] == script_sha and application['plan_sha256'] == h.sha(files['plan_receipt'])
            assert application['input_files']['prepared_receipt']['sha256'] == h.sha(files['prepared_receipt'])
            assert application['input_files']['inspect_receipt']['sha256'] == h.sha(files['inspect_receipt'])
            assert application['world'] == named_map and application['area'] == area and application['all_four_resources_strict_ready']
            compare_instances(h, reference['instances'], before['instances'], child_key, bindings)
            assert before['instances'] == application['after']['instances']
            for file, expected in reference['package_sha256'].items():
                target = str(Path(file).resolve(strict=True))
                assert before['disk'][target] == (args['expected_target_mi_package_sha256'] if target == child_file else expected)
            expected_copies = args['expected_copy_package_sha256']
            assert set(expected_copies) == copy_files
            for state in before['copies'].values():
                assert state['asset_exists']
                expected = expected_copies[state['disk']['file']]
                assert state['disk']['exists'] is (expected is not None)
                if expected is not None:
                    assert state['disk']['sha256'] == expected
            assert set(before['dirty']['content']) <= allowed_dirty
    label = args['label']
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label)
    out = h.REV / ('EPIC_RESIDENT_RECOVERY_' + mode + '_' + label + '_PID' + str(os.getpid()) + '.json')
    assert not out.exists()
    result = {'schema': 'environmentpipeline.epic_resident_recovery.v1', 'status': 'STARTED', 'mode': mode,
        'pid': os.getpid(), 'world': named_map, 'area': area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'helper_sha256': script_sha, 'shared_helper_sha256': SH_SHA, 'frozen_helper_sha256': s.FROZEN_SHA,
        'origin_helper_sha256': ORIGIN_SHA, 'failure_receipt_sha256': FAILURE_SHA,
        'reused_assets': [reused_row], 'all_copy_provenance': prepared['all_copy_provenance'] if prepared else [reused_row],
        'creation_mode': 'RECOVERY_REUSE_ONE_CREATE_THREE',
        'plan': plan, 'plan_sha256': h.sha(files['plan_receipt']), 'reference_receipt_sha256': REFERENCE_SHA,
        'epic_native_receipt_sha256': s.EPIC_SHA, 'source_manifest_sha256': h.sha(files['source_manifest']),
        'mutation_backup_sha256': h.sha(files['mutation_backup']), 'before': before,
        'input_files': {key: {'file': str(file), 'sha256': h.sha(file)} for key, file in files.items()},
        'created_assets': [], 'bound_parameters': [], 'setter_returns': [], 'modified_pins': [], 'modified_properties': [],
        'inspect_stage': 'BIND_READY' if prepared else 'RECOVERY_CREATE_ONLY', 'all_four_resources_strict_ready': bool(prepared),
        'allowed_dirty_packages': sorted(allowed_dirty), 'explicit_save_called': False, 'explicit_master_compile_called': False,
        'update_material_instance_called': False, 'global_loading_helper_called': False, 'rollback_executed': False,
        'native_mutation': mode in ('apply', 'bind'), 'limitations': ['Original Epic assets are immutable; four copied sources retain all readable persistent fields except never_stream/max_texture_size.',
            'Creation resources0/powers2<=2048 are pending; only a separately reviewed strict2048 inspector permits binding.',
            'Complete1015 graph/69 layers/Grass are unchanged; no residency force, global config, source color or mip-generation policy change.',
            'Unknown metadata/GUID fields remain unknown; no cooked/GPU/shader/visual quality acceptance is inferred.']}
    attempt = None
    if mode in ('apply', 'bind'):
        attempt = h.REV / ('EPIC_RESIDENT_RECOVERY_' + mode + '_ONCE_' + h.sha(files['plan_receipt']) + '.json')
        with attempt.open('x', encoding='utf-8') as file:
            file.write(json.dumps({'status': 'ATTEMPT_RESERVED', 'pid': os.getpid(), 'helper_sha256': script_sha, 'receipt': str(out)}, indent=2))
    with out.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2))
    failure = None
    try:
        if mode == 'apply':
            tools = h.unreal.AssetToolsHelpers.get_asset_tools()
            copied_objects = {}
            copied_objects[reused_destination] = h.unreal.load_asset(reused_destination)
            compare_copy(before['epic_textures'][reused_source], p.texture_details(h, copied_objects[reused_destination]))
            for source_asset, destination in COPIES.items():
                if destination == reused_destination:
                    continue
                package = destination.split('.')[0]
                assert not h.unreal.EditorAssetLibrary.does_asset_exist(destination) and not h.package_file(package).exists()
                directory, name = package.rsplit('/', 1)
                copied = tools.duplicate_asset(name, directory, h.unreal.load_asset(source_asset))
                result['created_assets'].append({'source': source_asset, 'destination': destination, 'path': h.path(copied),
                    'disk_immediately_after_duplicate': h.disk_state(h.package_file(package))})
                result['all_copy_provenance'].append(result['created_assets'][-1])
                assert copied and h.path(copied) == destination and not h.package_file(package).exists(), 'Unexpected implicit save: stop before binding'
                copied.set_editor_property('never_stream', True)
                copied.set_editor_property('max_texture_size', 2048)
                compare_copy(before['epic_textures'][source_asset], p.texture_details(h, copied), ready=False)
                copied_objects[destination] = copied
            result['copy_textures'] = {destination: p.texture_details(h, texture) for destination, texture in copied_objects.items()}
            for source_asset, destination in COPIES.items():
                compare_copy(before['epic_textures'][source_asset], result['copy_textures'][destination], ready=False)
        elif mode == 'bind':
            for key, destination in bindings.items():
                source_asset = s.PALETTE[key]
                texture = h.unreal.load_asset(destination)
                compare_copy(before['epic_textures'][source_asset], p.texture_details(h, texture))
                result['bound_parameters'].append(key)
                returned = h.LIB.set_material_instance_texture_parameter_value(child, key, texture)
                result['setter_returns'].append({'parameter': key, 'returned': h.plain(returned)})
            result['update_material_instance_called'] = True
            h.LIB.update_material_instance(child)
            result['copy_textures'] = ready_details
        elif prepared is not None:
            result['copy_textures'] = ready_details
        after = snapshot()
        result['after'] = after
        for key in ('sources', 'nodes', 'roots', 'material_settings', 'grass', 'scene', 'disk', 'cvars'):
            assert after[key] == before[key], key
        for asset in before['epic_textures']:
            assert after['epic_textures'][asset]['properties'] == before['epic_textures'][asset]['properties']
        assert after['held_texture']['properties'] == before['held_texture']['properties']
        if mode == 'apply':
            assert after['instances'] == before['instances'] and set(after['dirty']['content']) == copy_packages
            assert after['dirty']['maps'] == [] and all(row['asset_exists'] and not row['disk']['exists'] for row in after['copies'].values())
        elif mode == 'bind':
            compare_instances(h, before['instances'], after['instances'], child_key, bindings)
            assert after['dirty']['maps'] == [] and set(after['dirty']['content']) <= allowed_dirty
            assert all(row['asset_exists'] and not row['disk']['exists'] for row in after['copies'].values())
        else:
            assert after['instances'] == before['instances'] and after['dirty'] == before['dirty'] and after['copies'] == before['copies']
        p.sole_editor()
        assert h.sha(script) == script_sha and h.sha(origin_file) == ORIGIN_SHA and h.sha(sh_file) == SH_SHA and h.sha(policy_file) == s.POLICY_SHA
        assert h.sha(h.SCRIPT) == s.FROZEN_SHA and h.sha(assignment_file) == s.ASSIGNMENT_SHA
        assert all(h.sha(file) == result['input_files'][key]['sha256'] for key, file in files.items())
        result.update(graph_count=1015, nodes=after['nodes'], roots=after['roots'], material_settings=after['material_settings'],
            instances=after['instances'], grass=after['grass'], scene=after['scene'], cvars=after['cvars'], dirty=after['dirty'],
            package_sha256=after['disk'], complete_code_input_output_mip_identity_equal=True,
            preserved_1015_nodes=True, preserved_69_layer_names=True,
            preserved_grass=True, preserved_scene=True, preserved_cvars=True, preserved_original_files=True,
            preserved_epic_texture_properties=True, held_copy_unchanged=True)
        result['status'] = {'inspect': 'EPIC_RESIDENT_RECOVERY_CANDIDATE_REQUIRES_ROOT_REVIEW', 'apply': 'EPIC_RESIDENT_RECOVERY_COPIES_CREATED_PENDING_READINESS',
            'bind': 'EPIC_RESIDENT_RECOVERY_BOUND_NO_EXPLICIT_SAVE', 'verify': 'IDENTITY_VERIFIED_READ_ONLY_EPIC_RESIDENT'}[mode]
    except Exception as error:
        failure = error
        result['status'] = 'FAILED_PARTIAL_STATE_PRESERVED' if mode in ('apply', 'bind') else 'FAILED_READ_ONLY_CHECK'
        result['error'] = repr(error)
        try:
            result['failure_dirty'] = {'maps': sorted(h.path(x) for x in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                'content': sorted(h.path(x) for x in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
            result['failure_all_copy_states'] = copy_states()
            result['failure_original_disk_hashes'] = {file: h.disk_state(file) for file in sorted(protected)}
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
            'world': named_map, 'area': area, 'graph_count': 1015, 'native_mutation': mode in ('apply', 'bind')}


if 'ARGS' in globals():
    RESULT = run(ARGS)
