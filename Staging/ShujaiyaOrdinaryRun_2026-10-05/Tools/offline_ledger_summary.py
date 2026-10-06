"""Offline, read-only ledger summary for the ShujaiyaOrdinaryRun startup-inspection design.

Reads project files only. Writes only Tools/receipts/OFFLINE_LEDGER_SUMMARY.json.
Never imports unreal, never touches the editor, leases, maps or ledgers.
"""
import configparser
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

assert 'unreal' not in sys.modules, 'offline tool must not run inside Unreal'
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert ROOT.name == 'Environmentpipeline', ROOT
OUT = HERE / 'receipts' / 'OFFLINE_LEDGER_SUMMARY.json'

SHUJ = ROOT / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02'
CANDIDATE_LEDGER = ROOT / 'Staging/ManagedAstra_2026-10-03/ExteriorIntervalStop_20261003T213017494226Z/ROADBLD_WORKFLOW_STATE.json'
MANIFEST = ROOT / 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
DISK_RECON = ROOT / 'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/DISK_RECONCILIATION.json'
ASSIGNMENTS = ROOT / 'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json'
LEASE = ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt'
ROADBLD_INI = ROOT / 'Config/DefaultRoadBLD.ini'
FLAGS = ('bEnableIntersectionLandscapePatch', 'bEnableIntersectionLandscapeVisibilityHole',
         'bEnableRoadLandscapePaint', 'bUseRoadLandscapeHeightPatch', 'bAutoCreatePaintLayerInfo')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def shape(obj, limit=140):
    out = {}
    for key, value in obj.items():
        if isinstance(value, (list, dict)):
            out[key] = type(value).__name__ + '[' + str(len(value)) + ']'
        elif isinstance(value, str):
            out[key] = value if len(value) <= limit else value[:limit] + '...'
        else:
            out[key] = value
    return out


def package_file(name, extension='.uasset'):
    assert name.startswith('/Game/')
    return ROOT / 'Content' / (name.split('.')[0][6:] + extension)


def landscape_like(paths):
    return sorted(p for p in paths if 'landscape' in p.rsplit('.', 1)[-1].lower())


def road_ledger(path):
    data = read(path)
    rfg = data.get('retained_failed_generations', [])
    return {
        'path': str(path), 'sha256': sha(path), 'shape': shape(data),
        'phase': data.get('phase'), 'pid': data.get('pid'), 'revision': data.get('revision'),
        'saved': data.get('saved'), 'named_map': data.get('named_map'), 'area_id': data.get('area_id'),
        'source_sha256': data.get('source_sha256'), 'centreline_sha256': data.get('centreline_sha256'),
        'staged_actor_paths_count': len(data.get('staged_actor_paths', []) or []),
        'owned_actor_paths_count': len(data.get('owned_actor_paths', []) or []),
        'road_actor_paths_count': len(data.get('road_actor_paths', []) or []),
        'geometry_actor_paths_count': len(data.get('geometry_actor_paths', []) or []),
        'clipping_bindings_count': len((data.get('clipping_report') or {}).get('bindings', []) or []),
        'retained_failed_generations': [{'revision': r.get('revision'), 'actor_paths': len(r.get('actor_paths', [])),
                                         'unvalidated_mesh_paths': len(r.get('unvalidated_mesh_paths', []))} for r in rfg],
        'error': (str(data.get('error'))[:300] if data.get('error') else None),
        'utc': data.get('utc'),
        '_data': data,
    }


def replay_reconcile(prior, plan_source_sha, previous_owned, area, named_map):
    """Offline mirror of geocity_roadbld_workflow.RoadBLDRun.reconcile_failed_generations (:684-716)
    minus the live actor/tag checks. Reports what the live code would require."""
    report = {'candidates': [], 'expected_paths_count': 0, 'errors': []}
    if not prior:
        return report
    candidates = list(prior.get('retained_failed_generations', []))
    if str(prior.get('phase', '')).startswith('failed_') and prior.get('staged_actor_paths'):
        if not (prior.get('saved') is False and prior.get('named_map') == named_map and prior.get('area_id') == area):
            report['errors'].append('prior ledger saved/map/area assertion would fail')
        candidates.append({'revision': prior['revision'], 'actor_paths': list(prior['staged_actor_paths']),
                           'source_sha256': prior['source_sha256'], 'centreline_sha256': prior['centreline_sha256'],
                           'unvalidated_mesh_paths': [row['clipped_mesh'] for row in prior.get('clipping_report', {}).get('bindings', [])]})
    expected = set()
    for item in candidates:
        row = {'revision': item['revision'], 'actor_paths': len(item['actor_paths']),
               'source_sha256_matches_plan': item['source_sha256'] == plan_source_sha,
               'unvalidated_mesh_paths': len(item.get('unvalidated_mesh_paths', []))}
        paths = set(item['actor_paths'])
        if len(paths) != len(item['actor_paths']) or expected.intersection(paths):
            report['errors'].append('Ambiguous saved failed generation ' + str(item['revision']))
        if not row['source_sha256_matches_plan']:
            report['errors'].append('Saved failed geography differs for ' + str(item['revision']))
        expected.update(paths)
        row['required_tags'] = ['GeoCity_RoadBLD', 'GeoCityArea_' + area, 'GeoCityRevision_' + str(item['revision'])]
        report['candidates'].append(row)
    overlap = expected.intersection(previous_owned)
    if overlap:
        report['errors'].append('Failed/successful actor ledgers overlap: ' + str(len(overlap)))
    report['expected_paths_count'] = len(expected)
    report['expected_paths'] = sorted(expected)
    report['overlap_with_previous_owned'] = len(overlap)
    report['already_owned_expected_total'] = len(expected | set(previous_owned))
    return report


def main():
    result = {'schema': 'environmentpipeline.shujaiya_ordinary_run.offline_ledger_summary.v1',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'root': str(ROOT),
              'native_calls': 0, 'writes': [str(OUT)]}
    # --- seal ---
    manifest = read(MANIFEST)
    seal = {'manifest_sha256': sha(MANIFEST), 'modules': {}, 'support_files': {}, 'startup': {}}
    for name, entry in manifest['modules'].items():
        path = ROOT / 'Content/Python' / entry['file']
        actual = sha(path)
        seal['modules'][name] = {'expected': entry['sha256'], 'actual': actual, 'match': actual == entry['sha256']}
    for relative, expected in manifest['support_files'].items():
        actual = sha(ROOT / relative)
        seal['support_files'][relative] = {'expected': expected, 'actual': actual, 'match': actual == expected}
    startup = ROOT / 'Content/Python' / manifest['startup']['file']
    seal['startup'] = {'expected': manifest['startup']['sha256'], 'actual': sha(startup), 'match': sha(startup) == manifest['startup']['sha256']}
    seal['module_count'] = len(manifest['modules'])
    seal['all_match'] = all(v['match'] for v in seal['modules'].values()) and all(v['match'] for v in seal['support_files'].values()) and seal['startup']['match']
    result['seal'] = seal
    # --- profiles ---
    profiles = sorted((ROOT / 'Staging/ModelBank').glob('*/AREA_PROFILE.json'))
    result['persistent_profiles'] = [str(p) for p in profiles]
    shuj_profile_path = SHUJ / 'AREA_PROFILE.json'
    p = read(shuj_profile_path)
    grass = p.get('landscape_grass', {})
    result['shujaiya_profile'] = {
        'path': str(shuj_profile_path), 'sha256': sha(shuj_profile_path), 'map': p['map'], 'table': p['table'],
        'row_count': p['row_count'], 'catalog_sha256': p['catalog_sha256'], 'source': p['source'],
        'source_sha256': sha(p['source']), 'root': p['root'], 'cook_folder': p['cook_folder'], 'bake_folder': p.get('bake_folder'),
        'hda': p['hda'], 'mode': p['mode'], 'workflow_receipt': p['workflow_receipt'], 'catalog_receipt': p['catalog_receipt'],
        'build_state_alias': p.get('build_state_alias'), 'landscape_material': p.get('landscape_material'),
        'procedural_material': p.get('procedural_material'), 'road_provider': p.get('road_provider'),
        'road_provider_contract_phase': (p.get('road_provider_contract') or {}).get('phase'),
        'road_provider_contract_revision': (p.get('road_provider_contract') or {}).get('revision'),
        'road_provider_contract_owned_count': len((p.get('road_provider_contract') or {}).get('owned_actor_paths', [])),
        'roadbld_workflow': {'enabled': p.get('roadbld_workflow', {}).get('enabled'), 'status': p.get('roadbld_workflow', {}).get('status'),
                             'settings_keys': sorted((p.get('roadbld_workflow', {}).get('settings') or {}).keys())},
        'landscape_grass': {'enabled': grass.get('enabled'), 'coverage': grass.get('coverage'), 'density_per_10m2': grass.get('density_per_10m2'),
                            'mesh_paths': grass.get('mesh_paths'), 'base_material_instance': grass.get('base_material_instance'),
                            'ground_layer': grass.get('ground_layer'), 'paint_probe_count': len(grass.get('paint_probe_locations', []))},
        'surface_normal_overrides': p.get('surface_normal_overrides'), 'painted_layer_names': p.get('painted_layer_names'),
        'surface_choices': p.get('surface_choices'), 'operation_timeout_seconds': p.get('operation_timeout_seconds'),
        'release': {k: p.get('release', {}).get(k) for k in ('id', 'style_set', 'catalog_sha256', 'decision_receipt', 'decision_sha256')},
        'environment_style_set': p.get('environment_style_set'), 'instance_materials_count': len(p.get('instance_materials', {})),
        'building_assembly_contract_enabled': (p.get('building_assembly_contract') or {}).get('enabled'),
        'top_level_keys': sorted(p.keys()),
    }
    # --- maps / shared ground assets ---
    files = {
        'shujaiya_umap': package_file(p['map'], '.umap'),
        'rimal_umap': ROOT / 'Content/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.umap',
        'master_material': ROOT / 'Content/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.uasset',
        'natural_mi': ROOT / 'Content/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural.uasset',
        'grass_type': ROOT / 'Content/Project/Shared/SurfacePainting/Appearance_20261003/LG_GeoCity_PermittedGroundGrass.uasset',
        'shujaiya_mi': ROOT / 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround.uasset',
        'rimal_mi': ROOT / 'Content/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround.uasset',
        'table': package_file(p['table']),
        'hda': package_file(p['hda']),
        'default_roadbld_ini': ROADBLD_INI,
    }
    result['files'] = {k: ({'path': str(v), 'exists': v.is_file(), 'sha256': sha(v) if v.is_file() else None,
                            'bytes': v.stat().st_size if v.is_file() else None,
                            'mtime_utc': datetime.datetime.fromtimestamp(v.stat().st_mtime, datetime.timezone.utc).isoformat() if v.is_file() else None})
                       for k, v in files.items()}
    # --- RoadBLD ini flags ---
    config = configparser.RawConfigParser(strict=False)
    config.read_string(ROADBLD_INI.read_text(encoding='utf-8-sig'))
    result['roadbld_ini_flags'] = {n: config.getboolean('/Script/RoadBLDRuntime.RoadBLDRuntimeSettings', n) for n in FLAGS}
    # --- ledgers ---
    canonical = road_ledger(SHUJ / 'ROADBLD_WORKFLOW_STATE.json')
    candidate = road_ledger(CANDIDATE_LEDGER)
    delivery_path = SHUJ / 'ROADBLD_DELIVERY.json'
    d = read(delivery_path)
    delivery = {'path': str(delivery_path), 'sha256': sha(delivery_path), 'shape': shape(d), 'phase': d.get('phase'), 'saved': d.get('saved'),
                'revision': d.get('revision'), 'named_map': d.get('named_map'), 'area_id': d.get('area_id'),
                'source_sha256': d.get('source_sha256'), 'owned_actor_paths_count': len(d.get('owned_actor_paths', [])),
                'road_actor_paths_count': len(d.get('road_actor_paths', [])), 'geometry_actor_paths_count': len(d.get('geometry_actor_paths', [])),
                'network_actor_path': d.get('network_actor_path'), 'derived_junction_road_count': d.get('derived_junction_road_count'),
                'actual_native_road_actor_count': d.get('actual_native_road_actor_count'),
                'retired_failed_generations': [{'revision': r.get('revision'), 'actor_paths': len(r.get('actor_paths', []))} for r in d.get('retired_failed_generations', [])],
                'retired_successful_generations': [{'revision': r.get('revision'), 'owned_actor_paths': len(r.get('owned_actor_paths', []))} for r in d.get('retired_successful_generations', [])],
                'unreferenced_native_staged_packages_count': len(d.get('unreferenced_native_staged_packages', [])),
                'named_generated_dependency_paths_count': len(d.get('named_generated_dependency_paths', [])),
                'native_component_bindings_count': len(d.get('native_component_bindings', [])),
                'hda_vehicle_surfaces_suppressed': d.get('hda_vehicle_surfaces_suppressed'), 'utc': d.get('utc'),
                'owned_actor_name_prefixes': sorted({re.sub(r'_\d+$', '', x.rsplit('.', 1)[-1]) for x in d.get('owned_actor_paths', [])})}
    last_path = SHUJ / 'LAST_SUCCESSFUL_WORKFLOW_STATE.json'
    ls = read(last_path)
    last = {'path': str(last_path), 'sha256': sha(last_path), 'shape': shape(ls), 'phase': ls.get('phase'), 'pid': ls.get('pid'),
            'profile': ls.get('profile'), 'catalog_sha256': ls.get('catalog_sha256'), 'row_count': ls.get('row_count'),
            'baked_actor_paths_count': len(ls.get('baked_actor_paths', [])), 'baked_landscape_like': landscape_like(ls.get('baked_actor_paths', [])),
            'baked_actor_names': sorted(x.rsplit('.', 1)[-1] for x in ls.get('baked_actor_paths', [])),
            'previous_baked_actor_paths_count': len(ls.get('previous_baked_actor_paths', [])),
            'named_generated_dependency_paths_count': len(ls.get('named_generated_dependency_paths', [])),
            'unreferenced_cook_packages_count': len(ls.get('unreferenced_cook_packages', [])),
            'instance_count': ls.get('instance_count'), 'baked_mesh_counts': ls.get('baked_mesh_counts'), 'roles': ls.get('roles'),
            'native_material_family_count': ls.get('native_material_family_count'), 'utc': ls.get('utc'), 'lease_at_start': ls.get('lease_at_start')}
    ws_path = SHUJ / 'WORKFLOW_STATE.json'
    ws = read(ws_path)
    workflow = {'path': str(ws_path), 'sha256': sha(ws_path), 'phase': ws.get('phase'), 'pid': ws.get('pid'), 'utc': ws.get('utc'),
                'error': (str(ws.get('error'))[:400] if ws.get('error') else None), 'profile': ws.get('profile'),
                'previous_baked_actor_paths_count': len(ws.get('previous_baked_actor_paths', [])),
                'previous_landscape_accounting': ws.get('previous_landscape_accounting'),
                'current_road_landscape_authority_present': 'current_road_landscape_authority' in ws, 'shape': shape(ws)}
    build_alias = Path(p['build_state_alias']) if p.get('build_state_alias') else None
    if build_alias and build_alias.is_file():
        workflow['build_state_alias_sha256'] = sha(build_alias)
        workflow['build_state_alias_equals_workflow_state'] = sha(build_alias) == workflow['sha256']
    # --- actor set arithmetic ---
    owned = set(d.get('owned_actor_paths', []))
    cand_staged = set(candidate['_data'].get('staged_actor_paths', []) or [])
    canon_staged = set(canonical['_data'].get('staged_actor_paths', []) or [])
    sets = {'delivery_owned': len(owned), 'candidate_ledger_staged': len(cand_staged), 'canonical_ledger_staged': len(canon_staged),
            'owned_intersect_candidate_staged': len(owned & cand_staged), 'owned_union_candidate_staged': len(owned | cand_staged),
            'candidate_staged_equals_canonical_staged': cand_staged == canon_staged,
            'candidate_staged_minus_canonical': len(cand_staged - canon_staged), 'canonical_minus_candidate': len(canon_staged - cand_staged),
            'candidate_staged_name_prefixes': sorted({re.sub(r'_\d+$', '', x.rsplit('.', 1)[-1]) for x in cand_staged}),
            'baked_intersect_owned': len(set(ls.get('baked_actor_paths', [])) & owned),
            'baked_intersect_candidate_staged': len(set(ls.get('baked_actor_paths', [])) & cand_staged)}
    result['actor_sets'] = sets
    result['replay_reconcile_with_candidate_ledger'] = replay_reconcile(candidate['_data'], result['shujaiya_profile']['source_sha256'], owned, d.get('area_id'), p['map'])
    result['replay_reconcile_with_canonical_ledger'] = replay_reconcile(canonical['_data'], result['shujaiya_profile']['source_sha256'], owned, d.get('area_id'), p['map'])
    for ledger in (canonical, candidate):
        ledger.pop('_data')
    result['roadbld_workflow_state_canonical'] = canonical
    result['roadbld_workflow_state_candidate'] = candidate
    result['roadbld_delivery'] = delivery
    result['last_successful_workflow_state'] = last
    result['workflow_state'] = workflow
    # --- HDA catalog receipt header (bounded read of a 186MB file) ---
    receipt_path = Path(p['catalog_receipt'])
    head = receipt_path.open('rb').read(16384).decode('utf-8', 'replace') if receipt_path.is_file() else ''
    result['hda_catalog_receipt'] = {'path': str(receipt_path), 'exists': receipt_path.is_file(),
                                     'bytes': receipt_path.stat().st_size if receipt_path.is_file() else None,
                                     'catalog_sha256_in_header': (re.search(r'"catalog_sha256"\s*:\s*"([0-9a-f]{64})"', head) or [None, None])[1],
                                     'native_v3_catalog_sha256_in_header': (re.search(r'"native_v3_catalog_sha256"\s*:\s*"([0-9a-f]{64})"', head) or [None, None])[1],
                                     'generator_revision_in_header': (re.search(r'"generator_revision"\s*:\s*"([^"]+)"', head) or [None, None])[1]}
    # --- 87 candidates ---
    recon = read(DISK_RECON)
    cands = [r for a in recon['areas'] for r in a['preserved_candidate_disk_checks']]
    checks = []
    for r in cands:
        path = ROOT / r['file']
        actual = sha(path) if path.is_file() else None
        checks.append({'file': r['file'], 'expected': r['sha256'], 'actual': actual, 'match': actual == r['sha256'], 'approved': r.get('approved')})
    result['candidates_87'] = {'source': str(DISK_RECON), 'count': len(cands), 'unique_files': len({r['file'] for r in cands}),
                               'all_present': all(c['actual'] for c in checks), 'all_match': all(c['match'] for c in checks),
                               'mismatches': [c for c in checks if not c['match']], 'approved_any': any(c['approved'] for c in checks),
                               'by_area': {a.get('area_id', a.get('map')): len(a['preserved_candidate_disk_checks']) for a in recon['areas']},
                               'recon_shape': shape(recon)}
    # --- authority / lease ---
    a = read(ASSIGNMENTS)
    result['assignments'] = {'path': str(ASSIGNMENTS), 'sha256': sha(ASSIGNMENTS), 'manager_thread_id': a.get('manager_thread_id'),
                             'task4_thread_id': next((t.get('thread_id') for t in a.get('tasks', []) if t.get('id') == 'task4'), None),
                             'native_area_maps': a.get('native_area_maps'), 'shape': shape(a)}
    lines = [x for x in LEASE.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
    result['lease'] = {'last_line': lines[-1], 'line_count': len(lines)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=str) + '\n', encoding='utf-8')
    brief = {k: result[k] for k in ('actor_sets',)}
    brief['seal_all_match'] = seal['all_match']
    brief['shujaiya_umap_sha256'] = result['files']['shujaiya_umap']['sha256']
    brief['profile_sha256'] = result['shujaiya_profile']['sha256']
    brief['canonical_phase'] = canonical['phase']
    brief['candidate_phase'] = candidate['phase']
    brief['delivery_revision'] = delivery['revision']
    brief['candidates_87_all_match'] = result['candidates_87']['all_match']
    brief['out'] = str(OUT)
    print(json.dumps(brief, indent=2))


if __name__ == '__main__':
    main()
