"""Hybrid ground (GazaShujaiya) READ-ONLY fresh-process verification. In-editor only, after the named save.
Fork of PathB_MW/pathb_verify_fresh.py (same channel/conventions: inline exec, ARGS in, RESULT out, receipt then
raise on failure, idle without ARGS).

Never: any set_*, update/recompile, save, Cook/Bake, prepare()/verify_landscape(), camera/CVar changes, the MCP
get_material_info tool. Writes only Hybrid_Auto/receipts/HYBRID_VERIFY_<label>_PID<pid>.json.

ARGS: mode='verify', label, expected_pid, lease_owner, manager_thread_id, operator_thread_id, script_file,
  script_sha256, profile_sha256 (P'), save_receipt, save_receipt_sha256, build_receipt, build_receipt_sha256,
  post_regeneration (bool), expected_map_sha256 (REQUIRED with post_regeneration=true: the map the ordinary
  regeneration saved; optional otherwise, default = the save receipt's map hash).
Lease activation STARTUP_INSPECTION_ONLY or GROUND_HYBRID_VERIFY, on a PID different from the authoring PID.
Rows: lease_fresh_pid, editor_state, profile_hybrid, disk_named_save, master_graph (digest == build, MMA_0 root,
4 layer samples reachable from MMA_0, RemoveFoliage reachable), mi_readback (full value table == save receipt),
landscape_binding (1 Landscape, material == profile == Auto MI, all components bound), paint_probes (profile
landscape_grass.paint_probe_locations: BuildingPad -> Sand_Path, RoadBed -> Dirt_Path, weight >= minimum_weight),
dirty_clean_before_after; with post_regeneration additionally regeneration_ledger (LAST_SUCCESSFUL phase
baked_saved_verified, parameters.landscape_material == Auto MI, the four '_landscape_<Layer>' LayerInfo packages
among named_generated_dependency_paths) and target_layers (Landscape target layer names include the four).
In post_regeneration mode the MI file hash is advisory (the ordinary lifecycle may re-save area packages under
profile.root, BW:938-986); the full MI value readback is the gate. Verdict VERIFIED_READ_ONLY only if every row PASS.
"""
import datetime
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import types
from pathlib import Path

_EXECUTED_CODE = sys._getframe(0).f_code

SCHEMA = 'environmentpipeline.ground_hybrid_verify.v1'
SAVE_SCHEMA = 'environmentpipeline.ground_hybrid_assign.v1'
BUILD_SCHEMA = 'environmentpipeline.ground_hybrid_master.v1'
MAP = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
AREA_ROOT = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015'
MI_PKG = AREA_ROOT + '/Materials/MI_GeoCityGround_Auto'
MI_PATH = MI_PKG + '.MI_GeoCityGround_Auto'
PATHB_MI_PKG = AREA_ROOT + '/Materials/MI_GeoCityGround_MW'
PATHB_MI_PATH = PATHB_MI_PKG + '.MI_GeoCityGround_MW'
OLD_MI_PATH = AREA_ROOT + '/Materials/MI_GeoCityGround.MI_GeoCityGround'
COPY_OBJ = '/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto.M_GeoCityAuto'
OWNER_TAG, OWNER_VALUE = 'GeoCityOwner', 'GeoCity_GroundHybrid_20261006'
PROFILE_REL = 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
LEDGER_REL = 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/LAST_SUCCESSFUL_WORKFLOW_STATE.json'
STAGE_REL = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/Hybrid_Auto'
OUT_REL = STAGE_REL + '/receipts'
HELPER_REL = 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py'
HELPER_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
VENDOR_REL = 'Content/MWLandscapeAutoMaterial'
COPY_FILE = 'Content/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto.uasset'
MI_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_Auto.uasset'
PATHB_MI_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW.uasset'
MAP_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
READONLY = ('STARTUP_INSPECTION_ONLY', 'GROUND_HYBRID_VERIFY')
LAYERS = ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')
ROLE_LAYER = {'Ground': 'Sand_01', 'Steep': 'Sand_02', 'RoadBed': 'Dirt_Path', 'BuildingPad': 'Sand_Path'}   # LW:18-19
MW_LAYER = 'RemoveFoliage'
MMA = 'MaterialExpressionMakeMaterialAttributes_0'
EXPECTED_COMPONENTS = 64
TOL = 1e-4
SHA = re.compile(r'^[0-9a-f]{64}$')
KEYS = {'mode', 'label', 'expected_pid', 'lease_owner', 'manager_thread_id', 'operator_thread_id', 'script_file',
        'script_sha256', 'profile_sha256', 'save_receipt', 'save_receipt_sha256', 'build_receipt', 'build_receipt_sha256',
        'post_regeneration'}
OPTIONAL = {'expected_map_sha256'}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes()) if Path(path).is_file() else None


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def token(text, limit=96):
    return isinstance(text, str) and 0 < len(text) <= limit and all(c.isascii() and (c.isalnum() or c in '_-') for c in text)


def lease_fields(line):
    return dict(re.findall(r'(?:^|\s)([A-Za-z_]+)=([^\s]+)', line))


def code_signature(code):
    constants = tuple(code_signature(v) if isinstance(v, types.CodeType) else v for v in code.co_consts)
    return (code.co_code, constants, code.co_names, code.co_varnames, code.co_freevars, code.co_cellvars,
            code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def close(a, b, tol=TOL):
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if number(a) and number(b):
        return abs(float(a) - float(b)) <= tol
    return a == b


def values_equal(a, b):
    return set(a) == set(b) and all(set(a[k]) == set(b[k]) and all(close(a[k][n], b[k][n]) for n in a[k]) for k in a)


def short(path):
    return path.rsplit(':', 1)[1] if isinstance(path, str) and ':' in path else path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def strip_guids(rows):
    return {k: dict(v, properties={p: x for p, x in v['properties'].items() if p not in ('expression_guid', 'material_expression_guid')})
            for k, v in rows.items()}


def reach(rows, starts):
    seen, stack = set(), [s for s in starts if s]
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in rows:
            continue
        seen.add(cur)
        stack.extend(e['source'] for e in rows[cur]['edges'].values() if e.get('source'))
    return seen


def layer_info_ok(paths, layer):
    return any(isinstance(p, str) and p.endswith('_landscape_' + layer) for p in paths)


def validate(args):
    need(isinstance(args, dict) and args.get('mode') == 'verify', "mode must be 'verify'")
    need(not (KEYS - set(args)), 'Missing ARGS keys: %s' % sorted(KEYS - set(args)))
    need(not (set(args) - KEYS - OPTIONAL), 'Unknown ARGS keys: %s' % sorted(set(args) - KEYS - OPTIONAL))
    need(token(args.get('label')), 'label: ascii [A-Za-z0-9_-]')
    need(isinstance(args.get('expected_pid'), int) and not isinstance(args.get('expected_pid'), bool), 'expected_pid int')
    for key in ('lease_owner', 'manager_thread_id', 'operator_thread_id'):
        need(token(args.get(key), 64) and args[key] != 'NONE', key + ' required')
    for key in ('script_sha256', 'profile_sha256', 'save_receipt_sha256', 'build_receipt_sha256'):
        need(isinstance(args.get(key), str) and SHA.match(args[key]), key + ' must be a sha256')
    for key in ('save_receipt', 'build_receipt'):
        need(isinstance(args.get(key), str) and args[key].endswith('.json'), key + ' path')
    need(isinstance(args.get('post_regeneration'), bool), 'post_regeneration bool')
    if args['post_regeneration'] or 'expected_map_sha256' in args:
        need(isinstance(args.get('expected_map_sha256'), str) and SHA.match(args['expected_map_sha256']),
             'expected_map_sha256 (required with post_regeneration) must be a sha256')
    return 'verify'


def vendor_snapshot(root):
    rows = {}
    for path in sorted((root / VENDOR_REL).rglob('*')):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            stat = path.stat()
            small = rel.startswith((VENDOR_REL + '/Materials/', VENDOR_REL + '/Procedurals/')) and path.suffix == '.uasset'
            rows[rel] = [stat.st_size, stat.st_mtime_ns, sha_file(path) if small else None]
    return rows


def _p(obj):
    return obj.get_path_name() if obj else None


def chain_of(u, material):
    out = []
    while material is not None and len(out) < 8:
        out.append(_p(material))
        material = material.get_editor_property('parent') if isinstance(material, u.MaterialInstance) else None
    return out


def mi_values(u, lib, mi):
    out = {'scalars': {}, 'vectors': {}, 'textures': {}, 'switches': {}}
    for n in lib.get_scalar_parameter_names(mi):
        out['scalars'][str(n)] = round(float(lib.get_material_instance_scalar_parameter_value(mi, n)), 6)
    for n in lib.get_vector_parameter_names(mi):
        c = lib.get_material_instance_vector_parameter_value(mi, n)
        out['vectors'][str(n)] = [round(float(c.r), 6), round(float(c.g), 6), round(float(c.b), 6), round(float(c.a), 6)]
    for n in lib.get_texture_parameter_names(mi):
        out['textures'][str(n)] = _p(lib.get_material_instance_texture_parameter_value(mi, n))
    for n in lib.get_static_switch_parameter_names(mi):
        out['switches'][str(n)] = bool(lib.get_material_instance_static_switch_parameter_value(mi, n))
    return out


def load_helper(root):
    data = (root / HELPER_REL).read_bytes()
    need(sha_bytes(data) == HELPER_SHA, 'Frozen graph helper changed')
    module = types.ModuleType('hybrid_frozen_graph_helper')
    exec(compile(data, str(root / HELPER_REL), 'exec'), module.__dict__)
    need('ARGS' not in module.__dict__ and 'RESULT' not in module.__dict__, 'Helper executed a mode')
    return module


def bound_json(root, file, expected_sha, under):
    path = Path(file).resolve()
    need(path.is_file() and path.is_relative_to((root / under).resolve()), 'Bound file outside %s: %s' % (under, path))
    raw = path.read_bytes()
    need(sha_bytes(raw) == expected_sha, 'Bound file sha256 differs: ' + str(path))
    return path, json.loads(raw.decode('utf-8'))


def verify_identity(args):
    script = Path(args['script_file'])
    need(script.is_absolute() and script.is_file() and script.parent.name == 'Hybrid_Auto'
         and script.name == 'hybrid_verify_fresh.py', 'script_file must be the Hybrid_Auto/hybrid_verify_fresh.py copy')
    source = script.read_bytes()
    need(sha_bytes(source) == args['script_sha256'], 'Unreviewed script bytes')
    need(code_signature(_EXECUTED_CODE) == code_signature(compile(source, str(script), 'exec')), 'Executed code differs')
    return str(script)


def run(args):
    if not isinstance(args, dict) or args.get('mode') != 'verify':
        return {'ok': False, 'idle': True, 'reason': "No ARGS.mode='verify'; nothing was done."}
    validate(args)
    script = verify_identity(args)
    import unreal as u
    lib = u.MaterialEditingLibrary
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    out = root / OUT_REL / ('HYBRID_VERIFY_%s_PID%s.json' % (args['label'], os.getpid()))
    need(not out.exists(), 'Receipt label already used in this PID')
    post = args['post_regeneration']
    rows, receipt = [], {'schema': SCHEMA, 'label': args['label'], 'pid': os.getpid(), 'utc_start': utc(),
                         'executed_script': script, 'args': args, 'post_regeneration': post,
                         'engine': u.SystemLibrary.get_engine_version()}
    h = load_helper(root)
    _, saved = bound_json(root, args['save_receipt'], args['save_receipt_sha256'], OUT_REL)
    need(saved.get('schema') == SAVE_SCHEMA and saved.get('status') == 'SAVED_NAMED_ONLY', 'Not a SAVED_NAMED_ONLY receipt')
    _, built = bound_json(root, args['build_receipt'], args['build_receipt_sha256'], OUT_REL)
    need(built.get('schema') == BUILD_SCHEMA and built.get('status') == 'BUILT_VERIFIED_NO_SAVE', 'Not a BUILT_VERIFIED_NO_SAVE receipt')
    need(saved['build_receipt_sha256'] == args['build_receipt_sha256'] and built['pid'] == saved['pid'],
         'Save and build receipts are not one authoring PID')

    def check(cid, fn):
        try:
            rows.append({'id': cid, 'result': 'PASS', 'detail': fn()})
        except Exception as exc:
            rows.append({'id': cid, 'result': 'FAIL', 'error': repr(exc)})

    def dirty():
        return (sorted(_p(p) for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
                sorted(_p(p) for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()))

    d0 = dirty()
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    lands = [a for a in actors if isinstance(a, u.Landscape)]
    proxies = [a for a in actors if isinstance(a, u.LandscapeProxy) and not isinstance(a, u.Landscape)]
    profile_doc = json.loads((root / PROFILE_REL).read_bytes().decode('utf-8'))

    def lease():
        line = [x for x in (root / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
        f = lease_fields(line)
        need(args['expected_pid'] == os.getpid() == int(f.get('assigned_editor_PID', -1)), 'PID/lease PID')
        need(f.get('OWNER') == args['lease_owner'] and f.get('activation') in READONLY and f.get('map') == MAP, 'lease fields')
        need(f.get('manager_thread_id') == args['manager_thread_id'] and f.get('operator_thread_id') == args['operator_thread_id'], 'threads')
        need(os.getpid() != saved['pid'], 'Not a fresh process (same PID as the save)')
        return line

    def editor_state():
        world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
        need(world.get_outermost().get_path_name() == MAP, 'world')
        api = u.HoudiniPublicAPIBlueprintLib.get_api()
        need(api.is_asset_cooking_paused(), 'Houdini Engine cooking not paused')
        listing = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq UnrealEditor.exe', '/FO', 'CSV', '/NH'], capture_output=True,
                                 text=True, timeout=30, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout
        pids = sorted(int(r.split('","')[1]) for r in listing.splitlines() if r.startswith('"UnrealEditor.exe"'))
        need(pids == [os.getpid()], 'sole editor: %s' % pids)
        return {'world': MAP, 'cooking_paused': True, 'editor_pids': pids}

    def profile():
        data = (root / PROFILE_REL).read_bytes()
        need(sha_bytes(data) == args['profile_sha256'], 'profile sha256')
        ext = profile_doc.get('external_landscape_material') or {}
        need(profile_doc['landscape_material'] == MI_PATH and profile_doc['landscape_grass']['enabled'] is False
             and ext.get('parent_chain') == [COPY_OBJ], 'profile not Hybrid')
        need(sorted(profile_doc.get('painted_layer_names') or []) == sorted(LAYERS), 'painted_layer_names')
        return {'sha256': sha_bytes(data), 'landscape_material': profile_doc['landscape_material']}

    def disk_files():
        after = saved['disk_after']
        copy_sha, mi_sha, map_sha = sha_file(root / COPY_FILE), sha_file(root / MI_FILE), sha_file(root / MAP_FILE)
        need(copy_sha == after['copy'], 'M_GeoCityAuto package differs from the save receipt')
        if not post:
            need(mi_sha == after['mi'], 'MI package differs from the save receipt')
        need(mi_sha is not None, 'MI package missing')
        expected_map = args.get('expected_map_sha256') or after['map']
        need(map_sha == expected_map, 'map package sha256 differs from the expected value')
        need(sha_file(root / PATHB_MI_FILE) is None, 'MI_GeoCityGround_MW exists on disk')
        protected = {rel: sha_file(root / rel) for rel in after['protected']}
        # Hard: Shujaiya's own old child and the Urban textures. Advisory: shared Natural assets and Rimal's child,
        # which a legitimate Rimal/Iran ordinary run re-saves through prepare() (LW:353, :382).
        hard = [rel for rel in protected if rel.startswith(('Content/Project/Areas/GazaShujaiya/', 'Content/ModularCourtyard/'))]
        need(all(protected[rel] == after['protected'][rel] for rel in hard), 'Shujaiya old MI or an Urban texture changed')
        need(vendor_snapshot(root) == saved['vendor_snapshot'], 'MW vendor files changed')
        return {'copy': copy_sha, 'mi': mi_sha, 'mi_equals_save_receipt': mi_sha == after['mi'], 'map': map_sha,
                'shared_changed_since_save_advisory':
                    sorted(rel for rel in protected if rel not in hard and protected[rel] != after['protected'][rel])}

    def master_graph():
        master = u.load_asset(COPY_OBJ)
        need(isinstance(master, u.Material), 'M_GeoCityAuto class')
        need(str(u.EditorAssetLibrary.get_metadata_tag(master, OWNER_TAG)) == OWNER_VALUE, 'M_GeoCityAuto owner tag')
        obj = h.path(master)
        graph = {short(h.path(e)): h.describe(master, e) for e in lib.get_material_expressions(master)}
        graph = json.loads(json.dumps(graph, sort_keys=True).replace(obj + ':', '').replace(obj, '<SELF>'))
        live = digest(strip_guids(graph))
        need(live == built['graph']['digest_noguid'] and len(graph) == built['graph']['rows'], 'graph digest differs from the build')
        root_mma = short(h.path(lib.get_material_property_input_node(master, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)))
        need(root_mma == MMA, 'material attributes root is %s' % root_mma)
        samples = {k: r['properties'].get('parameter_name') for k, r in graph.items()
                   if r['class'] == 'MaterialExpressionLandscapeLayerSample'}
        need(sorted(samples.values()) == sorted(LAYERS + (MW_LAYER,)), 'layer samples %s' % samples)
        from_mma = reach(graph, [MMA])
        outputs = [k for k, r in graph.items() if r['class'] in ('MaterialExpressionLandscapeGrassOutput',
                                                                 'MaterialExpressionLandscapePhysicalMaterialOutput')]
        from_all = reach(graph, [MMA] + outputs)
        need(all(k in from_mma for k, n in samples.items() if n in LAYERS), 'a hybrid layer sample is not reachable from MMA_0')
        need(all(k in from_all for k in samples), 'a layer sample is unreachable')
        return {'digest_noguid': live, 'digest_full_equals_build_advisory': digest(graph) == built['graph']['digest'],
                'rows': len(graph), 'layer_samples': samples}

    def material():
        mi = u.load_asset(MI_PATH)
        need(isinstance(mi, u.MaterialInstanceConstant), 'MI class')
        need(str(u.EditorAssetLibrary.get_metadata_tag(mi, OWNER_TAG)) == OWNER_VALUE, 'owner tag')
        chain = chain_of(u, mi.get_editor_property('parent'))
        need(chain == [COPY_OBJ] == saved['mi']['parent_chain'], 'parent chain %s' % chain)
        values = mi_values(u, lib, mi)
        need(values_equal(values, saved['mi']['values']), 'MI parameter values differ from the save receipt')
        need(not u.EditorAssetLibrary.does_asset_exist(PATHB_MI_PKG), 'MI_GeoCityGround_MW exists')
        return {'parent_chain': chain, 'parameter_count': sum(len(v) for v in values.values()),
                'urban': {k: v for kind in values.values() for k, v in kind.items() if k.startswith('Urban_')}}

    def landscape():
        need(len(lands) == 1 and not proxies, 'landscape count %d / proxies %d' % (len(lands), len(proxies)))
        land = lands[0]
        need(land.get_outermost().get_path_name() == MAP, 'landscape not in map package')
        bound = _p(land.get_editor_property('landscape_material'))
        need(bound == MI_PATH == profile_doc['landscape_material'], 'Landscape material is %s' % bound)
        chains = [chain_of(u, c.get_material(0)) for c in land.get_components_by_class(u.LandscapeComponent)]
        need(chains and all(MI_PATH in c for c in chains) and not any(OLD_MI_PATH in c or PATHB_MI_PATH in c for c in chains),
             'component bindings')
        if not post:
            need(len(chains) == EXPECTED_COMPONENTS, 'component count %d != 64' % len(chains))
        hism = list(land.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent))
        try:
            layer_names = sorted(str(n) for n in land.get_target_layer_names())
        except Exception as error:          # advisory only; the post_regeneration row gates it
            layer_names = repr(error)
        return {'landscape': _p(land), 'material': bound, 'components': len(chains),
                'target_layer_names_advisory': layer_names,
                'landscape_hism_components_advisory': len(hism),
                'landscape_hism_instances_advisory': sum(c.get_instance_count() for c in hism)}

    def paint_probes():
        probes = (profile_doc.get('landscape_grass') or {}).get('paint_probe_locations') or []
        if not probes:
            return {'skipped': 'profile has no landscape_grass.paint_probe_locations'}
        need(len(lands) == 1, 'one Landscape')
        comps = list(lands[0].get_components_by_class(u.LandscapeComponent))
        bounds = [(c, u.SystemLibrary.get_component_bounds(c)) for c in comps]
        results, failures = [], []
        for probe in probes:
            role, xyz = probe.get('expected_role'), probe.get('world_location_cm') or []
            need(role in ROLE_LAYER and len(xyz) == 3 and all(math.isfinite(float(v)) for v in xyz), 'invalid probe %s' % probe)
            minimum = float(probe.get('minimum_weight', 0.8))
            location = u.Vector(*[float(v) for v in xyz])
            containing = [c for c, (origin, extent, radius) in bounds        # LW:451-455 pattern
                          if abs(location.x - origin.x) <= extent.x and abs(location.y - origin.y) <= extent.y]
            need(containing, 'probe outside the Landscape: ' + str(probe.get('id')))
            weights = {l: float(containing[0].editor_get_paint_layer_weight_by_name_at_location(location, l)) for l in LAYERS}
            row = {'id': probe.get('id'), 'role': role, 'layer': ROLE_LAYER[role], 'minimum': minimum, 'weights': weights,
                   'component': _p(containing[0])}
            results.append(row)
            if weights[ROLE_LAYER[role]] < minimum:
                failures.append(row)
        need(not failures, 'paint probes below minimum: %s' % failures)
        need({r['role'] for r in results} >= {'RoadBed', 'BuildingPad'}, 'probes must cover RoadBed and BuildingPad')
        return {'probes': results}

    def ledger():
        state = json.loads((root / LEDGER_REL).read_bytes().decode('utf-8'))
        paths = state.get('named_generated_dependency_paths') or []
        need(state.get('phase') == 'baked_saved_verified', 'ledger phase %s' % state.get('phase'))
        need((state.get('parameters') or {}).get('landscape_material') == MI_PATH, 'ledger parameters.landscape_material')
        missing = [l for l in LAYERS if not layer_info_ok(paths, l)]
        need(not missing, 'LayerInfo packages missing for %s' % missing)
        return {'phase': state['phase'], 'utc': state.get('utc'), 'pid': state.get('pid'),
                'layer_infos': sorted(p for p in paths if '_landscape_' in str(p))}

    def target_layers():
        need(len(lands) == 1, 'one Landscape')
        names = sorted(str(n) for n in lands[0].get_target_layer_names())
        need(set(LAYERS) <= set(names), 'target layer names %s lack the four' % names)
        return {'target_layer_names': names}

    checks = [('lease_fresh_pid', lease), ('editor_state', editor_state), ('profile_hybrid', profile),
              ('disk_named_save', disk_files), ('master_graph', master_graph), ('mi_readback', material),
              ('landscape_binding', landscape), ('paint_probes', paint_probes)]
    if post:
        checks += [('regeneration_ledger', ledger), ('target_layers', target_layers)]
    for cid, fn in checks:
        check(cid, fn)
    check('dirty_clean_before_after', lambda: (need(d0 == ([], []) and dirty() == ([], []), 'dirty %s / %s' % (d0, dirty())), d0)[1])
    status = 'VERIFIED_READ_ONLY' if rows and all(r['result'] == 'PASS' for r in rows) else 'FAILED_READ_ONLY_CHECKS'
    receipt.update(rows=rows, status=status, utc_end=utc())
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2, default=str)
    need(status == 'VERIFIED_READ_ONLY', 'Hybrid verification failed; see ' + str(out))
    return {'ok': True, 'status': status, 'receipt': str(out), 'receipt_sha256': sha_file(out)}


RESULT = run(globals().get('ARGS'))
