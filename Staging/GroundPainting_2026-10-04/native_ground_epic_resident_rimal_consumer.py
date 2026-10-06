"""Rimal-only saved Epic-resident palette binding; root alone reviews, pins and executes.

inspect/apply/verify require expected_pid,label,held_copy_package_sha256 and
SHA-bound baseline_receipt,shared_reference,epic_native_receipt,source_manifest,
mutation_backup,plan_receipt,original_reference,resident_creation,resident_ready,
resident_binding,resident_save,resident_failure,resident_previous_failure,
resident_copy_state,resident_gamma_failure,consumer_plan_receipt. Shared-reference baseline is SHA-bound and must be fresh
(reference.pid != saved.pid); no same-process saved proof substitutes for reopen. Apply also binds inspect_receipt/review_receipt.
Verify binds apply_receipt and exact expected_target_mi_package_sha256.
resident_save_helper_sha256 pins the actual reviewed named-save execution.
shared_reference_helper_sha256 must be the frozen resident helper SHA.
Shared reference is the saved/fresh-read verified1015-node Shujaiya resident
result, bound to original Epic21-control proof and four-copy creation/readiness/
binding/named-save provenance. No normalization of an older proof status.
Only27 RI overrides change:11textures,8scalars,8vectors (bothMacroSoil
consumers use the same four saved nativeEpic copies). No graph/source/texture
property/actor edits, copying, compile/save, force/loading/CVar call or cleanup.
Import without ARGS is idle; failures retain partial state and write evidence.
"""
import copy
import datetime
import hashlib
import json
import os
import types
from pathlib import Path

RESIDENT_SHA = '691d33b3b7ead57a132f2b8354c9f2e0d5eaaed80cc1168ccc9feffcd4ba4fb0'
RECIPE = {'GeoCity_CellScale': 1, 'Ground_SoilBlendStrength': .1,
          'Sand_01_FarScale': 2, 'Dirt_Path_NormalStrength': .2}


def load_definitions():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_ground_epic_resident_consumer_recovery.py').resolve(strict=True)
    data = file.read_bytes()
    assert hashlib.sha256(data).hexdigest() == RESIDENT_SHA
    r = types.ModuleType('epic_resident_frozen_shared_definitions')
    r.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), r.__dict__)
    assert 'ARGS' not in r.__dict__ and hashlib.sha256(file.read_bytes()).hexdigest() == RESIDENT_SHA
    h, p, s, sh_file, policy_file = r.load_definitions()
    return h, p, s, r, file, sh_file, policy_file


def compare_instances(h, s, old, new, child_path, plan):
    assert set(old) == set(new)
    association = h.plain(h.unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    for path, prior in old.items():
        live = new[path]
        if path != child_path:
            assert live == prior, 'Other instance changed: ' + path
            continue
        assert set(live) == set(prior)
        assert all(live[k] == prior[k] for k in ('path', 'parent', 'override_guid_capture'))
        for kind, overrides in (('textures', 'texture_overrides'), ('scalars', 'scalar_overrides'),
                                ('vectors', 'vector_overrides')):
            updates = plan[kind]
            if kind == 'scalars':
                updates = {k: s.float32(v) for k, v in updates.items()}
            elif kind == 'vectors':
                updates = {k: [s.float32(x) for x in v] for k, v in updates.items()}
            assert live[kind] == dict(prior[kind], **updates), (path, kind)
            assert [r for r in live[overrides] if r['name'] not in updates] == [
                r for r in prior[overrides] if r['name'] not in updates], (path, overrides)
            selected = [r for r in live[overrides] if r['name'] in updates]
            assert len(selected) == len(updates) and {r['name'] for r in selected} == set(updates)
            assert all(r['association'] == association and r['index'] == -1 and
                       r['value'] == updates[r['name']] for r in selected), (path, overrides)


def validate_reference(h, p, s, r, docs, files, args, sh_key):
    reference, original, epic = [docs[key] for key in ('shared_reference', 'original_reference', 'epic_native_receipt')]
    creation, ready, binding, saved = [docs[key] for key in ('resident_creation', 'resident_ready', 'resident_binding', 'resident_save')]
    assert h.sha(files['original_reference']) == r.REFERENCE_SHA
    assert original['status'] == 'IDENTITY_VERIFIED_READ_ONLY_EPIC_GROUND' and original['helper_sha256'] == r.REFERENCE_HELPER_SHA
    assert original['mode'] == 'verify' and original['area'] == 'GazaShujaiya'
    assert original['after']['dirty'] == {'maps': [], 'content': []} and original['native_mutation'] is False
    assert original['nodes'] == reference['nodes'] and original['roots'] == reference['roots']
    assert original['material_settings'] == reference['material_settings'] and original['grass'] == reference['grass']
    assert original['scene'] == reference['scene'] and original['cvars'] == reference['cvars']
    s.compare_instances(h, epic['instances'], original['instances'], sh_key, original['plan'])
    bindings = {key: r.COPIES[value] for key, value in s.PALETTE.items() if key != 'Ground_MacroMask'}
    consumer = docs['consumer_plan_receipt']
    assert consumer['schema'] == 'environmentpipeline.epic_native_consumer_closure.v1'
    assert consumer['original_plan_sha256'] == reference['plan_sha256']
    assert consumer['bindings'] == dict(bindings,
        Ground_MacroSoilAlbedo=r.COPIES['/Game/StarterContent/Textures/T_Rock_Sandstone_D.T_Rock_Sandstone_D'],
        Ground_MacroSoilNormal=r.COPIES['/Game/StarterContent/Textures/T_Rock_Sandstone_N.T_Rock_Sandstone_N'])
    assert reference['consumer_plan_sha256'] == h.sha(files['consumer_plan_receipt']) and reference['consumer_plan'] == consumer
    assert reference['consumer_binding_count'] == 10 and reference['extra_ground_soil_texture_bindings_closed']
    assert reference['copy_properties_match_except_policy_and_inactive_normal_gamma'] and reference['copy_property_comparison_scope'] == 'ALL_FOUR'
    original_bindings = bindings
    bindings = consumer['bindings']

    r.compare_instances(h, original['instances'], reference['instances'], sh_key, bindings)
    assert reference['reference_receipt_sha256'] == r.REFERENCE_SHA and reference['all_four_resources_strict_ready']
    assert reference['native_mutation'] is False and set(reference['package_sha256']) == set(original['package_sha256'])
    assert reference['preserved_epic_texture_properties'] and reference['preserved_original_files'] and reference['held_copy_unchanged']
    assert reference['plan']['bindings'] == original_bindings
    assert {row['source']: row['destination'] for row in reference['plan']['items']} == r.COPIES
    for key, status, mode in (('resident_creation', 'EPIC_RESIDENT_CONSUMER_COPIES_CREATED_PENDING_READINESS', 'apply'),
            ('resident_ready', 'EPIC_RESIDENT_CONSUMER_CANDIDATE_REQUIRES_ROOT_REVIEW', 'inspect'),
            ('resident_binding', 'EPIC_RESIDENT_CONSUMER_BOUND_NO_EXPLICIT_SAVE', 'bind')):
        receipt = docs[key]
        assert receipt['status'] == status and receipt['mode'] == mode and receipt['helper_sha256'] == RESIDENT_SHA
        assert receipt['consumer_plan_sha256'] == h.sha(files['consumer_plan_receipt']) and receipt['consumer_plan'] == consumer
        assert receipt['plan_sha256'] == reference['plan_sha256'] and receipt['plan'] == reference['plan']
        assert receipt['world'] == reference['world'] and receipt['area'] == 'GazaShujaiya'
        assert receipt['pid'] == creation['pid'] and receipt['explicit_save_called'] is False
    failure = docs['resident_failure']
    assert h.sha(files['resident_failure']) == r.FAILURE_SHA
    assert failure['status'] == 'FAILED_PARTIAL_STATE_PRESERVED' and failure['helper_sha256'] == r.ORIGIN_SHA
    assert failure['bound_parameters'] == [] and failure['explicit_save_called'] is False
    assert len(failure['created_assets']) == 1 and failure['update_material_instance_called'] is False
    assert failure['plan_sha256'] == reference['plan_sha256']
    assert creation['failure_receipt_sha256'] == reference['failure_receipt_sha256'] == r.FAILURE_SHA
    assert creation['origin_helper_sha256'] == reference['origin_helper_sha256'] == r.ORIGIN_SHA
    assert creation['input_files']['failure_receipt']['sha256'] == r.FAILURE_SHA
    previous, copy_state = docs['resident_previous_failure'], docs['resident_copy_state']
    assert h.sha(files['resident_previous_failure']) == r.PREVIOUS_FAILURE_SHA
    assert h.sha(files['resident_copy_state']) == r.COPY_STATE_SHA
    assert previous['status'] == 'FAILED_PARTIAL_STATE_PRESERVED' and previous['helper_sha256'] == r.PREVIOUS_HELPER_SHA
    assert previous['origin_helper_sha256'] == r.ORIGIN_SHA and previous['failure_receipt_sha256'] == r.FAILURE_SHA
    assert previous['bound_parameters'] == [] and previous['explicit_save_called'] is False
    assert previous['reused_assets'] == failure['created_assets'] and len(previous['created_assets']) == 1
    assert previous['all_copy_provenance'] == failure['created_assets'] + previous['created_assets']
    assert creation['previous_recovery_failure_sha256'] == reference['previous_recovery_failure_sha256'] == r.PREVIOUS_FAILURE_SHA
    assert creation['previous_helper_sha256'] == reference['previous_helper_sha256'] == r.PREVIOUS_HELPER_SHA
    assert creation['copy_state_receipt_sha256'] == reference['copy_state_receipt_sha256'] == r.COPY_STATE_SHA
    assert creation['input_files']['previous_recovery_failure']['sha256'] == r.PREVIOUS_FAILURE_SHA
    assert creation['input_files']['copy_state_receipt']['sha256'] == r.COPY_STATE_SHA
    assert copy_state['status'] == 'EPIC_COPY_PROPERTIES_READ_ONLY' and copy_state['native_mutation'] is False
    assert copy_state['originals_preserved'] and copy_state['graph_instances_scene_preserved']
    assert len(creation['created_assets']) == 2 and creation['reused_assets'] == previous['all_copy_provenance']
    assert creation['all_copy_provenance'] == previous['all_copy_provenance'] + creation['created_assets']
    gamma = docs['resident_gamma_failure']
    assert h.sha(files['resident_gamma_failure']) == r.GAMMA_FAILURE_SHA
    assert gamma['status'] == 'FAILED_PARTIAL_STATE_PRESERVED' and gamma['helper_sha256'] == r.GAMMA_HELPER_SHA
    assert gamma['created_assets'] == gamma['bound_parameters'] == [] and gamma['update_material_instance_called'] is False
    assert gamma['failure_receipt_sha256'] == r.FAILURE_SHA and gamma['previous_recovery_failure_sha256'] == r.PREVIOUS_FAILURE_SHA
    assert gamma['reused_assets'] == previous['all_copy_provenance']
    assert creation['gamma_failure_receipt_sha256'] == reference['gamma_failure_receipt_sha256'] == r.GAMMA_FAILURE_SHA
    assert creation['gamma_helper_sha256'] == reference['gamma_helper_sha256'] == r.GAMMA_HELPER_SHA
    assert creation['input_files']['gamma_failure_receipt']['sha256'] == r.GAMMA_FAILURE_SHA
    assert creation['restored_copy_properties'] == []
    assert len(gamma['restored_copy_properties']) == 1
    assert gamma['restored_copy_properties'][0]['before'] == gamma['restored_copy_properties'][0]['after'] == {'status': 'READ', 'value': False}
    assert len(creation['all_copy_provenance']) == 4 and creation['bound_parameters'] == []
    assert {row['source']: row['destination'] for row in creation['all_copy_provenance']} == r.COPIES
    assert creation['after']['instances'] == original['instances'] and creation['update_material_instance_called'] is False
    assert all(not row['disk_immediately_after_duplicate']['exists'] for row in creation['all_copy_provenance'])
    assert ready['inspect_stage'] == 'BIND_READY' and ready['all_four_resources_strict_ready'] and ready['native_mutation'] is False
    assert ready['input_files']['prepared_receipt']['sha256'] == h.sha(files['resident_creation'])
    assert ready['before']['instances'] == original['instances'] and binding['after']['instances'] == reference['instances']
    assert set(binding['bound_parameters']) == set(bindings) and len(binding['bound_parameters']) == 10
    for key, receipt_key in (('resident_creation', 'prepared_receipt'), ('resident_ready', 'inspect_receipt')):
        assert binding['input_files'][receipt_key]['sha256'] == h.sha(files[key])
        assert reference['input_files'][receipt_key]['sha256'] == h.sha(files[key])
    assert reference['input_files']['bind_receipt']['sha256'] == h.sha(files['resident_binding'])
    assert saved['schema'] == 'environmentpipeline.epic_resident_named_save.v1'
    assert saved['status'] == 'NAMED_EPIC_RESIDENT_SAVE_VERIFIED_CLEAN' and saved['helper_sha256'] == args['resident_save_helper_sha256']
    assert saved['consumer_plan_sha256'] == h.sha(files['consumer_plan_receipt'])
    assert saved['resident_helper_sha256'] == RESIDENT_SHA and saved['plan_sha256'] == reference['plan_sha256']
    assert saved['origin_helper_sha256'] == r.ORIGIN_SHA and saved['failure_receipt_sha256'] == r.FAILURE_SHA
    assert saved['creation_provenance'] == creation['all_copy_provenance']
    assert saved['pid'] == creation['pid'] and saved['world'] == reference['world'] and saved['area'] == 'GazaShujaiya'
    assert saved['dirty_after'] == {'maps': [], 'content': []}
    assert reference['pid'] != saved['pid'], 'A fresh Shujaiya process is required before RI'
    baseline_row = reference['input_files']['baseline_receipt']
    fresh_file, fresh = h.load_document(baseline_row['file'])
    assert h.sha(fresh_file) == baseline_row['sha256']
    files['shared_fresh_baseline'] = fresh_file
    assert fresh['pid'] == reference['pid'] and fresh['world'] == reference['world'] and fresh['area'] == 'GazaShujaiya'
    assert fresh['graph_expression_count'] == 1015 and fresh['dirty_maps'] == fresh['dirty_content'] == []
    assert fresh['sources'] == reference['before']['sources']
    assert fresh['actor_transforms'] == reference['scene']['transforms']
    assert sorted(fresh['native_mesh_components'], key=lambda row: row['component']) == reference['scene']['native_mesh_components']

    verify_file, verify = h.load_document(saved['input_files']['resident_verify_receipt']['file'])
    assert h.sha(verify_file) == saved['input_files']['resident_verify_receipt']['sha256']
    files['resident_pre_save_verify'] = verify_file
    assert verify['status'] == 'IDENTITY_VERIFIED_READ_ONLY_EPIC_RESIDENT' and verify['helper_sha256'] == RESIDENT_SHA
    assert verify['instances'] == reference['instances'] and verify['nodes'] == reference['nodes']
    assert saved['protected_package_sha256_before'] == saved['protected_package_sha256_after']
    sh_package = original['instances'][sh_key]['path'].split('.')[0]
    expected_named = {destination.split('.')[0] for destination in r.COPIES.values()} | {sh_package}
    assert set(saved['named_packages']) == set(saved['named_package_sha256']) == expected_named and len(expected_named) == 5
    assert saved['current_child_package_sha256'] == saved['named_package_sha256'][sh_package]
    assert reference['package_sha256'][str(h.package_file(sh_package).resolve(strict=True))] == saved['current_child_package_sha256']
    for file, expected in original['package_sha256'].items():
        target = str(Path(file).resolve(strict=True))
        assert reference['package_sha256'][target] == (saved['current_child_package_sha256'] if target == str(h.package_file(sh_package).resolve(strict=True)) else expected)
    assert set(reference['after']['copies']) == set(reference['copy_textures']) == set(r.COPIES.values())
    for source_asset, destination in r.COPIES.items():
        copied = reference['copy_textures'][destination]
        r.compare_copy(epic['textures'][source_asset], copied)
        r.compare_copy(epic['textures'][source_asset], ready['copy_textures'][destination])
        state = reference['after']['copies'][destination]
        package = destination.split('.')[0]
        assert state['asset_exists'] and state['disk']['exists'] and state['disk']['sha256'] == saved['named_package_sha256'][package]
        assert saved['copied_texture_disk_after'][package] == state['disk']
        assert h.sha(h.package_file(destination)) == state['disk']['sha256']


def run(args):
    h, p, s, r, resident_file, sh_file, policy_file = load_definitions()
    script = (h.HERE / 'native_ground_epic_resident_rimal_consumer.py').resolve(strict=True)
    script_sha = h.sha(script)
    mode = args.get('mode', 'inspect')
    assert mode in ('inspect', 'apply', 'verify') and args['expected_pid'] == os.getpid()
    p.sole_editor()
    files, docs = {}, {}
    for key in ('baseline_receipt', 'shared_reference', 'epic_native_receipt',
                'source_manifest', 'mutation_backup', 'plan_receipt', 'original_reference',
                'resident_creation', 'resident_ready', 'resident_binding', 'resident_save', 'resident_failure',
                'resident_previous_failure', 'resident_copy_state', 'resident_gamma_failure', 'consumer_plan_receipt'):
        files[key], docs[key] = h.load_document(args[key])
        assert h.sha(files[key]) == args[key + '_sha256'], key
    baseline, reference, epic, source, backup, plan = [docs[k] for k in (
        'baseline_receipt', 'shared_reference', 'epic_native_receipt', 'source_manifest', 'mutation_backup', 'plan_receipt')]
    assert reference['status'] == 'IDENTITY_VERIFIED_READ_ONLY_EPIC_RESIDENT' and reference['mode'] == 'verify'
    assert reference['area'] == 'GazaShujaiya' and reference['helper_sha256'] == args['shared_reference_helper_sha256'] == RESIDENT_SHA
    assert reference['graph_count'] == 1015 and reference['complete_code_input_output_mip_identity_equal']
    assert reference['preserved_1015_nodes'] and reference['preserved_69_layer_names'] and reference['preserved_grass']
    assert reference['preserved_scene'] and reference['after']['dirty'] == {'maps': [], 'content': []}
    assert reference['frozen_helper_sha256'] == source['helper_sha256'] == s.FROZEN_SHA
    assert reference['source_manifest_sha256'] == h.sha(files['source_manifest'])
    assert h.sha(files['epic_native_receipt']) == s.EPIC_SHA and epic['status'] == 'EPIC_ORIGINAL_GRAPHS_READ_ONLY'
    assert epic['native_mutation'] is False
    assert len(source['file_bindings']) == len(source['sealed_files']) == 17 and len(source['preserved_files']) == 65
    assert source['ordinary_generation_authorized'] is False
    assignment_file = h.HERE / 'ASSIGNMENT.json'
    assert h.sha(assignment_file) == s.ASSIGNMENT_SHA
    assignment = json.loads(assignment_file.read_text(encoding='utf-8-sig'))
    world = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = h.one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    assert area == plan['area'] == 'GazaRimal' and plan['world'] == named_map
    assert baseline['pid'] == os.getpid() and baseline['world'] == named_map and baseline['area'] == area
    assert baseline['graph_expression_count'] == 1015 and baseline['cooking_paused'] and not baseline['autosave']
    assert not any(baseline['callbacks'].values()) and len(baseline['hdas']) == 1
    assert all(not row['auto_cook'] and not row['auto_bake'] for row in baseline['hdas'])
    palette = dict(docs['consumer_plan_receipt']['bindings'], Ground_MacroMask=s.MACRO)
    assert len(palette) == 11
    assert plan['schema'] == 'environmentpipeline.epic_resident_consumer_rimal_plan.v1' and plan['textures'] == palette
    assert plan['scalars'] == dict({layer + '_Roughness': .8 for layer in s.LAYERS}, **RECIPE)
    assert plan['vectors'] == docs['original_reference']['plan']['vectors']
    assert set(plan['vectors']) == {layer + '_' + kind for layer in s.LAYERS for kind in ('Tint', 'TileCm')}
    for layer in s.LAYERS:
        assert plan['vectors'][layer + '_Tint'] == [1, 1, 1, 1]
        tile = plan['vectors'][layer + '_TileCm']
        assert len(tile) == 4 and tile[0] == tile[1] == tile[2] and 50 <= tile[0] <= 400 and tile[3] == 1
    assert plan['shared_reference_sha256'] == h.sha(files['shared_reference'])
    assert plan['epic_native_receipt_sha256'] == s.EPIC_SHA
    assert backup['ready'] is True and backup['ready_for_epic_resident_rimal_binding'] is True
    assert backup['world'] == named_map and backup['execution_thread_id'] == assignment['execution_thread_id']
    assert backup['plan_sha256'] == h.sha(files['plan_receipt'])
    if mode != 'verify':
        assert plan['pid'] == backup['pid'] == os.getpid()
    master = h.unreal.load_asset(h.MASTER)
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][area])
    assert isinstance(master, h.unreal.Material) and isinstance(child, h.unreal.MaterialInstanceConstant)
    child_path = h.path(child)
    assert reference['nodes'] == s.expected_graph(h, epic['natural_nodes'], h.path(master))
    sh_child = assignment['material_contract']['area_instances']['GazaShujaiya']
    sh_key = h.one((key for key, row in epic['instances'].items() if row['path'] == sh_child), 'Sh instance key')
    validate_reference(h, p, s, r, docs, files, args, sh_key)
    assert plan['original_reference_sha256'] == r.REFERENCE_SHA
    assert plan['resident_save_sha256'] == h.sha(files['resident_save'])
    assert plan['consumer_plan_sha256'] == h.sha(files['consumer_plan_receipt'])
    child_key = h.one((key for key, row in reference['instances'].items() if row['path'] == child_path), 'RI instance key')
    child_file = str(h.package_file(child_path).resolve(strict=True))
    assert set(backup['file_bindings']) == {child_file}
    for row in backup['file_bindings'].values():
        assert h.sha(Path(row['backup']).resolve(strict=True)) == row['sha256']
    protected = {str(Path(file).resolve(strict=True)) for file in reference['package_sha256']}
    assert set(source['file_bindings']) <= protected and child_file in protected
    protected.update(str(h.package_file(asset).resolve(strict=True)) for asset in epic['original_file_sha256'])
    protected.update(str(h.package_file(asset).resolve(strict=True)) for asset in r.COPIES.values())
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
    allowed_dirty = {child.get_outermost().get_path_name()}

    def snapshot():
        modules, actors = h.guard(assignment, named_map, require_authoring=(mode == 'apply'))
        assert len(modules) == 12
        grass_nodes = [e for e in h.LIB.get_material_expressions(master)
                       if isinstance(e, h.unreal.MaterialExpressionLandscapeGrassOutput)]
        assert len(grass_nodes) == 1
        return {'sources': modules, 'nodes': {h.path(e): h.describe(master, e) for e in h.LIB.get_material_expressions(master)},
                'roots': {k: h.path(h.LIB.get_material_property_input_node(master, prop)) for k, prop in h.PROPERTIES.items()},
                'material_settings': {k: h.plain(master.get_editor_property(k)) for k in reference['material_settings']},
                'instances': {k: h.material_state(master, h.unreal.load_asset(k)) for k in reference['instances']},
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
                'held_texture': p.texture_details(h, h.unreal.load_asset(s.HOLD)),
                'copy_textures': {key: p.texture_details(h, h.unreal.load_asset(key)) for key in r.COPIES.values()},
                'copies': {key: {'asset_exists': h.unreal.EditorAssetLibrary.does_asset_exist(key),
                    'disk': h.disk_state(h.package_file(key))} for key in r.COPIES.values()}}

    before = snapshot()
    assert before['sources'] == baseline['sources'] and before['dirty'] == {
        'maps': sorted(baseline['dirty_maps']), 'content': sorted(baseline['dirty_content'])}
    assert before['dirty']['maps'] == []
    assert before['scene']['transforms'] == baseline['actor_transforms']
    assert before['scene']['native_mesh_components'] == sorted(baseline['native_mesh_components'], key=lambda row: row['component'])
    landscapes = sorted([{'path': row['path'], 'material': row['material']['path'], 'hidden': row['hidden']}
                         for row in baseline['landscapes']], key=lambda row: row['path'])
    assert [{k: v for k, v in row.items() if k != 'layers'} for row in before['scene']['landscapes']] == landscapes
    assert len(before['scene']['transforms']) == baseline['actor_count']
    assert before['nodes'] == reference['nodes'] and len(before['nodes']) == 1015
    assert before['roots'] == reference['roots'] and before['material_settings'] == reference['material_settings']
    assert before['grass']['graph'] == reference['grass']['graph'] and before['grass']['settings'] == reference['grass']['settings']
    assert set(before['grass']['effective_coverage'].values()) == set(reference['grass']['effective_coverage'].values())
    assert before['cvars'] == reference['cvars']
    for asset, prior in epic['textures'].items():
        assert before['epic_textures'][asset]['properties'] == prior['properties'], asset
    for source_asset, destination in r.COPIES.items():
        r.compare_copy(before['epic_textures'][source_asset], before['copy_textures'][destination])
        assert before['copy_textures'][destination]['properties'] == reference['copy_textures'][destination]['properties']
        assert before['copies'][destination] == reference['after']['copies'][destination]
        assert destination.split('.')[0] not in before['dirty']['content']
    if mode == 'verify':
        files['apply_receipt'], application = h.load_document(args['apply_receipt'])
        assert h.sha(files['apply_receipt']) == args['apply_receipt_sha256']
        assert application['status'] == 'EPIC_RESIDENT_RIMAL_BOUND_NO_EXPLICIT_SAVE' and application['mode'] == 'apply'
        assert application['helper_sha256'] == script_sha and application['plan_sha256'] == h.sha(files['plan_receipt'])
        assert application['shared_reference_sha256'] == h.sha(files['shared_reference'])
        assert application['world'] == named_map and application['area'] == area
        assert before['instances'] == application['after']['instances']
        assert before['scene'] == application['before']['scene'] and before['grass'] == application['before']['grass']
        assert before['held_texture']['properties'] == application['before']['held_texture']['properties']
        assert set(before['dirty']['content']) <= allowed_dirty
    else:
        assert before['dirty'] == {'maps': [], 'content': []}
        assert before['instances'] == reference['instances']
        assert before['disk'][child_file] == backup['file_bindings'][child_file]['sha256']
    for file, expected in reference['package_sha256'].items():
        target = str(Path(file).resolve(strict=True))
        if mode == 'verify' and target == child_file:
            expected = args['expected_target_mi_package_sha256']
        assert before['disk'][target] == expected, target
    if mode == 'apply':
        for key in ('inspect_receipt', 'review_receipt'):
            files[key], docs[key] = h.load_document(args[key])
            assert h.sha(files[key]) == args[key + '_sha256']
        inspection, review = docs['inspect_receipt'], docs['review_receipt']
        assert inspection['status'] == 'EPIC_RESIDENT_RIMAL_CANDIDATE_REQUIRES_ROOT_REVIEW'
        assert inspection['helper_sha256'] == script_sha and inspection['plan_sha256'] == h.sha(files['plan_receipt'])
        assert r.persistent_state(inspection['before']) == r.persistent_state(before)
        assert review['status'] == 'APPROVED_EPIC_RESIDENT_RIMAL_BINDING'
        assert review['pid'] == os.getpid() and review['world'] == named_map and review['area'] == area
        for key, expected in {'helper_sha256': script_sha, 'inspect_receipt_sha256': h.sha(files['inspect_receipt']),
            'baseline_receipt_sha256': h.sha(files['baseline_receipt']), 'plan_sha256': h.sha(files['plan_receipt']),
            'shared_reference_sha256': h.sha(files['shared_reference']), 'epic_native_receipt_sha256': s.EPIC_SHA,
            'shared_reference_helper_sha256': args['shared_reference_helper_sha256'],
            'source_manifest_sha256': h.sha(files['source_manifest']), 'mutation_backup_sha256': h.sha(files['mutation_backup']),
            'held_copy_package_sha256': args['held_copy_package_sha256'],
            'resident_helper_sha256': RESIDENT_SHA,
            'resident_save_helper_sha256': args['resident_save_helper_sha256'],
            **{key + '_sha256': h.sha(files[key]) for key in ('original_reference', 'resident_creation',
                'resident_ready', 'resident_binding', 'resident_save', 'resident_failure',
                'resident_previous_failure', 'resident_copy_state', 'resident_gamma_failure', 'consumer_plan_receipt')}}.items():
            assert review[key] == expected, key
    label = args['label']
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label)
    out = h.REV / ('EPIC_RESIDENT_RIMAL_' + mode + '_' + label + '_PID' + str(os.getpid()) + '.json')
    assert not out.exists()
    result = {'schema': 'environmentpipeline.epic_resident_rimal.v1', 'status': 'STARTED', 'mode': mode,
        'pid': os.getpid(), 'world': named_map, 'area': area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'helper_sha256': script_sha, 'shared_helper_sha256': r.SH_SHA, 'resident_helper_sha256': RESIDENT_SHA, 'frozen_helper_sha256': s.FROZEN_SHA,
        'plan': plan, 'plan_sha256': h.sha(files['plan_receipt']), 'shared_reference_sha256': h.sha(files['shared_reference']),
        'shared_reference_helper_sha256': args['shared_reference_helper_sha256'],
        'resident_save_helper_sha256': args['resident_save_helper_sha256'],
        'original_reference_sha256': r.REFERENCE_SHA, 'previous_recovery_failure_sha256': r.PREVIOUS_FAILURE_SHA,
        'copy_state_receipt_sha256': r.COPY_STATE_SHA, 'gamma_failure_receipt_sha256': r.GAMMA_FAILURE_SHA,
        'consumer_plan_sha256': h.sha(files['consumer_plan_receipt']), 'resident_save_sha256': h.sha(files['resident_save']),
        'source_manifest_sha256': h.sha(files['source_manifest']), 'epic_native_receipt_sha256': s.EPIC_SHA,
        'mutation_backup_sha256': h.sha(files['mutation_backup']), 'before': before,
        'input_files': {k: {'file': str(file), 'sha256': h.sha(file)} for k, file in files.items()},
        'set_parameters': [], 'setter_returns': [], 'created_assets': [], 'modified_pins': [], 'modified_properties': [],
        'allowed_dirty_packages': sorted(allowed_dirty), 'explicit_save_called': False, 'explicit_master_compile_called': False,
        'update_material_instance_called': False, 'native_mutation': mode == 'apply', 'rollback_executed': False,
        'limitations': ['Adapted Epic palette, constant dry roughness maximum .8 and AO1; original masters are not cloned.',
            'Fresh Sh proof is SHA-bound to a native baseline and process different from named save; RI27 controls only; otherMIs/graph/originals exact; inactive copied normal gamma exception is explicit.',
            'Texture resource metadata may settle; ordered parameter identity/value is captured, unexposed ExpressionGUID is unknown.',
            'Legacy editor_layer_settings is unknown; no full geographic paint/height capture or visual/streaming/cooked acceptance is inferred.']}
    attempt = None
    if mode == 'apply':
        attempt = h.REV / ('EPIC_RESIDENT_RIMAL_ONCE_' + h.sha(files['plan_receipt']) + '.json')
        with attempt.open('x', encoding='utf-8') as file:
            file.write(json.dumps({'status': 'ATTEMPT_RESERVED', 'pid': os.getpid(), 'helper_sha256': script_sha,
                                   'plan_sha256': h.sha(files['plan_receipt']), 'receipt': str(out)}, indent=2))
    with out.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2))
    failure = None
    try:
        if mode == 'apply':
            for key, asset in plan['textures'].items():
                result['set_parameters'].append(key)
                returned = h.LIB.set_material_instance_texture_parameter_value(child, key, h.unreal.load_asset(asset))
                result['setter_returns'].append({'parameter': key, 'kind': 'texture', 'returned': h.plain(returned)})
            for key, value in plan['scalars'].items():
                result['set_parameters'].append(key)
                returned = h.LIB.set_material_instance_scalar_parameter_value(child, key, value)
                result['setter_returns'].append({'parameter': key, 'kind': 'scalar', 'returned': h.plain(returned)})
            for key, values in plan['vectors'].items():
                result['set_parameters'].append(key)
                returned = h.LIB.set_material_instance_vector_parameter_value(child, key, h.unreal.LinearColor(*values))
                result['setter_returns'].append({'parameter': key, 'kind': 'vector', 'returned': h.plain(returned)})
            result['update_material_instance_called'] = True
            h.LIB.update_material_instance(child)
        after = snapshot()
        result['after'] = after
        for key in ('sources', 'nodes', 'roots', 'material_settings', 'grass', 'scene', 'disk', 'cvars', 'copies'):
            assert after[key] == before[key], key
        for asset in before['epic_textures']:
            assert after['epic_textures'][asset]['properties'] == before['epic_textures'][asset]['properties']
        assert after['held_texture']['properties'] == before['held_texture']['properties']
        for source_asset, destination in r.COPIES.items():
            r.compare_copy(after['epic_textures'][source_asset], after['copy_textures'][destination])
            assert after['copy_textures'][destination]['properties'] == before['copy_textures'][destination]['properties']
        if mode == 'apply':
            compare_instances(h, s, before['instances'], after['instances'], child_key, plan)
            assert after['dirty']['maps'] == [] and set(after['dirty']['content']) <= allowed_dirty
        else:
            assert after['instances'] == before['instances'] and after['dirty'] == before['dirty']
        p.sole_editor()
        assert h.sha(script) == script_sha and h.sha(resident_file) == RESIDENT_SHA and h.sha(sh_file) == r.SH_SHA
        assert h.sha(policy_file) == s.POLICY_SHA and h.sha(h.SCRIPT) == s.FROZEN_SHA
        assert h.sha(assignment_file) == s.ASSIGNMENT_SHA
        assert all(h.sha(file) == result['input_files'][key]['sha256'] for key, file in files.items())
        result.update(graph_count=1015, nodes=after['nodes'], roots=after['roots'], material_settings=after['material_settings'],
            instances=after['instances'], grass=after['grass'], scene=after['scene'], cvars=after['cvars'], dirty=after['dirty'],
            package_sha256=after['disk'], graph_sha256=h.digest(after['nodes']), complete_code_input_output_mip_identity_equal=True,
            preserved_1015_nodes=True, preserved_69_layer_names=True, preserved_grass=True, preserved_scene=True,
            preserved_cvars=True, preserved_original_files=True, preserved_epic_texture_properties=True, held_copy_unchanged=True, copy_textures=after['copy_textures'], copies=after['copies'],
            all_four_resources_strict_ready=True, preserved_resident_copy_files=True,
            copy_properties_match_except_policy_and_inactive_normal_gamma=True, consumer_binding_count=10, rimal_texture_binding_count=11)
        result['inactive_gamma_differences'] = reference['inactive_gamma_differences']
        result['status'] = {'inspect': 'EPIC_RESIDENT_RIMAL_CANDIDATE_REQUIRES_ROOT_REVIEW',
            'apply': 'EPIC_RESIDENT_RIMAL_BOUND_NO_EXPLICIT_SAVE', 'verify': 'IDENTITY_VERIFIED_READ_ONLY_EPIC_RESIDENT_RIMAL'}[mode]
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
