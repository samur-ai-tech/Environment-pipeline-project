"""Path B (GazaShujaiya) READ-ONLY fresh-process verification. In-editor only, after the named save.

Same channel/conventions as pathb_assign_and_save.py (inline exec, ARGS in, RESULT out, receipt then raise on
failure, idle without ARGS). Never: any set_*, update/recompile, save, Cook/Bake, prepare()/verify_landscape(),
camera/CVar changes, the MCP get_material_info tool. Writes only PathB_MW/receipts/PATHB_VERIFY_<label>_PID<pid>.json.

ARGS: mode='verify', label, expected_pid, lease_owner, manager_thread_id, operator_thread_id, script_file,
  script_sha256, profile_sha256, save_receipt, save_receipt_sha256,
  expected_map_sha256 (optional; REQUIRED when the save scope was 'mi_only' and an ordinary regeneration then
  re-saved the map; otherwise the map hash comes from the save receipt).
Lease activation must be STARTUP_INSPECTION_ONLY or GROUND_PATHB_VERIFY (read-only), on a PID different from
the authoring PID (fresh process). Verdict VERIFIED_READ_ONLY only if every check row is PASS.
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import types
from pathlib import Path

_EXECUTED_CODE = sys._getframe(0).f_code

SCHEMA = 'environmentpipeline.pathb_mw_verify.v1'
SAVE_SCHEMA = 'environmentpipeline.pathb_mw_assign.v1'
MAP = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
AREA_ROOT = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015'
MI_PKG = AREA_ROOT + '/Materials/MI_GeoCityGround_MW'
MI_PATH = MI_PKG + '.MI_GeoCityGround_MW'
OLD_MI_PATH = AREA_ROOT + '/Materials/MI_GeoCityGround.MI_GeoCityGround'
PROFILE_REL = 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
OUT_REL = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/PathB_MW/receipts'
VENDOR_REL = 'Content/MWLandscapeAutoMaterial'
MI_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW.uasset'
MAP_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
OWNER_TAG, OWNER_VALUE = 'GeoCityOwner', 'GeoCity_GroundPathB_MW'
READONLY = ('STARTUP_INSPECTION_ONLY', 'GROUND_PATHB_VERIFY')
TINT_PARAMS = ('MW_SnowColorCorrection', 'MW_GrassColorCorrection', 'MW_DirtColorCorrection',
               'MW_StonesColorCorrection', 'MW_RockColorCorrection')
KEYS = {'mode', 'label', 'expected_pid', 'lease_owner', 'manager_thread_id', 'operator_thread_id', 'script_file',
        'script_sha256', 'profile_sha256', 'save_receipt', 'save_receipt_sha256', 'expected_map_sha256'}


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


def run(args):
    if not isinstance(args, dict) or args.get('mode') != 'verify':
        return {'ok': False, 'idle': True, 'reason': "No ARGS.mode='verify'; nothing was done."}
    need(not set(args) - KEYS, 'Unknown ARGS keys: %s' % sorted(set(args) - KEYS))
    need(token(args.get('label')) and isinstance(args.get('expected_pid'), int), 'label/expected_pid')
    script = Path(args['script_file'])
    source = script.read_bytes()
    need(script.parent.name == 'PathB_MW' and sha_bytes(source) == args['script_sha256'], 'Unreviewed script bytes')
    need(code_signature(_EXECUTED_CODE) == code_signature(compile(source, str(script), 'exec')), 'Executed code differs')
    import unreal as u
    lib = u.MaterialEditingLibrary
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    out = root / OUT_REL / ('PATHB_VERIFY_%s_PID%s.json' % (args['label'], os.getpid()))
    need(not out.exists(), 'Receipt label already used in this PID')
    rows, receipt = [], {'schema': SCHEMA, 'label': args['label'], 'pid': os.getpid(), 'utc_start': utc(),
                         'executed_script': str(script), 'args': args, 'engine': u.SystemLibrary.get_engine_version()}

    def check(cid, fn):
        try:
            detail = fn()
            rows.append({'id': cid, 'result': 'PASS', 'detail': detail})
        except Exception as exc:
            rows.append({'id': cid, 'result': 'FAIL', 'error': repr(exc)})

    def dirty():
        return (sorted(_p(p) for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
                sorted(_p(p) for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()))

    raw = Path(args['save_receipt']).read_bytes()
    need(sha_bytes(raw) == args['save_receipt_sha256'], 'Save receipt sha256 differs')
    saved = json.loads(raw.decode('utf-8'))
    need(saved.get('schema') == SAVE_SCHEMA and saved.get('status') == 'SAVED_NAMED_ONLY', 'Not a SAVED_NAMED_ONLY receipt')
    d0 = dirty()

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
        p = json.loads(data.decode('utf-8'))
        need(sha_bytes(data) == args['profile_sha256'], 'profile sha256')
        need(p['landscape_material'] == MI_PATH and p['landscape_grass']['enabled'] is False, 'profile not Path B')
        return {'sha256': sha_bytes(data), 'landscape_material': p['landscape_material']}

    def disk_files():
        mi_sha, map_sha = sha_file(root / MI_FILE), sha_file(root / MAP_FILE)
        need(mi_sha == saved['disk_after']['mi'], 'MI package differs from the saved receipt')
        expected_map = args.get('expected_map_sha256') or (saved['disk_after']['map'] if saved['scope'] == 'mi_and_map' else None)
        need(expected_map is not None and map_sha == expected_map, 'map package sha256 differs from the expected value')
        # Hard: Shujaiya's own old child. Advisory: shared Natural master/base/GrassType and Rimal's child,
        # which a legitimate Rimal/Iran ordinary run re-saves through prepare() (LW:353, :382).
        protected = {rel: sha_file(root / rel) for rel in saved['disk_after']['protected']}
        hard = [rel for rel in protected if rel.startswith('Content/Project/Areas/GazaShujaiya/')]
        need(all(protected[rel] == saved['disk_after']['protected'][rel] for rel in hard), 'Shujaiya old MI_GeoCityGround changed')
        need(vendor_snapshot(root) == saved_vendor(), 'MW vendor files changed')
        return {'mi': mi_sha, 'map': map_sha, 'shared_changed_since_save_advisory':
                sorted(rel for rel in protected if rel not in hard and protected[rel] != saved['disk_after']['protected'][rel])}

    def saved_vendor():
        apply = json.loads(Path(saved['apply_receipt']).read_bytes().decode('utf-8'))
        return apply['vendor_snapshot']

    def material():
        mi = u.load_asset(MI_PATH)
        need(isinstance(mi, u.MaterialInstanceConstant), 'MI class')
        need(str(u.EditorAssetLibrary.get_metadata_tag(mi, OWNER_TAG)) == OWNER_VALUE, 'owner tag')
        chain = chain_of(u, mi.get_editor_property('parent'))
        need(chain == saved['mi']['parent_chain'], 'parent chain %s' % chain)
        names = {str(n) for n in lib.get_static_switch_parameter_names(mi)}
        switches = {n: (bool(lib.get_material_instance_static_switch_parameter_value(mi, n)) if n in names else 'MISSING')
                    for n in saved['mi']['switches']}
        need(switches == saved['mi']['switches'], 'static switches %s' % switches)
        for name in TINT_PARAMS:
            c = lib.get_material_instance_vector_parameter_value(mi, name)
            need(all(abs(a - b) < 1e-4 for a, b in zip((c.r, c.g, c.b), saved['mi']['tints'][name])), 'tint ' + name)
        return {'parent_chain': chain, 'switches': switches}

    def landscape():
        actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
        lands = [a for a in actors if isinstance(a, u.Landscape)]
        proxies = [a for a in actors if isinstance(a, u.LandscapeProxy) and not isinstance(a, u.Landscape)]
        need(len(lands) == 1 and not proxies, 'landscape count %d / proxies %d' % (len(lands), len(proxies)))
        land = lands[0]
        need(land.get_outermost().get_path_name() == MAP, 'landscape not in map package')
        bound = _p(land.get_editor_property('landscape_material'))
        need(bound == MI_PATH, 'Landscape material is %s' % bound)
        chains = [chain_of(u, c.get_material(0)) for c in land.get_components_by_class(u.LandscapeComponent)]
        need(chains and all(MI_PATH in c for c in chains) and not any(OLD_MI_PATH in c for c in chains), 'component bindings')
        hism = list(land.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent))
        return {'landscape': _p(land), 'material': bound, 'components': len(chains),
                'landscape_hism_components_advisory': len(hism),
                'landscape_hism_instances_advisory': sum(c.get_instance_count() for c in hism)}

    for cid, fn in (('lease_fresh_pid', lease), ('editor_state', editor_state), ('profile_path_b', profile),
                    ('disk_named_save', disk_files), ('mi_readback', material), ('landscape_binding', landscape)):
        check(cid, fn)
    check('dirty_clean_before_after', lambda: (need(d0 == ([], []) and dirty() == ([], []), 'dirty %s / %s' % (d0, dirty())), d0)[1])
    status = 'VERIFIED_READ_ONLY' if rows and all(r['result'] == 'PASS' for r in rows) else 'FAILED_READ_ONLY_CHECKS'
    receipt.update(rows=rows, status=status, utc_end=utc())
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2, default=str)
    need(status == 'VERIFIED_READ_ONLY', 'Path B verification failed; see ' + str(out))
    return {'ok': True, 'status': status, 'receipt': str(out), 'receipt_sha256': sha_file(out)}


RESULT = run(globals().get('ARGS'))
