"""Stage 1 (S1) ground: in-editor READ-ONLY verifier for a fresh editor process.

Root reviews, pins and executes. Import without ARGS is idle (no unreal import).
Invocation: a Stage-1 copy of GP/copilot_call.py (run_unreal_skill inline: ARGS global in,
RESULT out). That wrapper only runs a script in its own directory that its SCRIPT_PINS.json
pins (GP/copilot_call.py:20-23); this verifier also requires that sibling SCRIPT_PINS.json to
pin verifier_file to ARGS.verifier_sha256, and proves the executed code equals verifier_file
by code signature (pattern Content/Python/geocity_runtime_guard.py:26-32).
Exit status: the receipt is written first; a status other than *_VERIFIED_READ_ONLY then
RAISES, so the inline runner returns ok False and copilot_call exits 1 (runner.py:104-107
returns ok True for any script that does not raise). Root still reads the receipt status,
never the exit code alone, and confirms externally that exactly one UnrealEditor.exe runs
before and after the run (no process control here). No top-level main(): SkillRunner.run_script
would call main(args) a second time after runpy (runner.py:207-210).

Never called here: recompile, update_material_instance, any set_*, save, reload,
Cook/Bake, actor/Landscape edits, CVar/residency changes, the MCP get_material_info
tool, LW prepare()/verify_landscape() (both guard and prepare saves, LW:213,353,382).
Only write: S1_Prep/receipts/VERIFY_<label>_<pid>.json (exclusive create, never overwritten).

ARGS
  label              ascii [A-Za-z0-9_]
  phase              'baseline' (pre-S1: switch/params/MFs absent, graph digest = r030)
                     | 'post_s1' (S1 saved; run in a fresh process after the saves)
  lease_owner        exact OWNER token of the last Staging/ModelBank/EDITOR_OWNER.txt line
  operator_thread_id REQUIRED; must equal the lease line's operator_thread_id
  allowed_activations  optional; may only NARROW READONLY_ACTIVATIONS ({STARTUP_INSPECTION_ONLY}).
                     Writer activations (GROUND_AUTHORING, MANAGER_ACTIVATED, ...) never qualify.
  expectations + expectations_sha256
                     S1_EDIT_EXPECTATIONS.json written by `s1_material_edit_offline.py expectations
                     <apply args> <out>` from the edit script's own PARAMS/FUNCTIONS/EXISTING_CHILD plus
                     the apply child_values (generated_by.target_sha256 = edit script sha). The hand-made
                     S1_MINIMAL_SAFE_SPEC.json has no generated_by and is refused. Both Gaza children
                     must be listed (both are always tracked). Baseline and post_s1 use the SAME file.
  reference_graph + reference_graph_sha256   pre-S1 1015-node describe() dump
                     (default: REV r031 fresh reopen, sha c6b74f0f..., GP/finalize_epic_ground_result.py:15)
  baseline_receipt + baseline_receipt_sha256  post_s1 REQUIRED: a passed phase=baseline receipt of the
                     same verifier sha, expectations sha, reference sha and area/map
  save_receipt + save_receipt_sha256  post_s1 REQUIRED: S1_SAVE_<label>_PID<pid>.json of
                     s1_material_edit.py (schema ...s1_material_edit.save.v1, SAVED_NAMED_ONLY). The authoring
                     PID, the expected package sha256 (disk_after) and the in-scope children derive from it;
                     its SHA-bound apply receipt supplies plans and graph_after_sha256.
  profiles / profile_sha256   optional {area: AREA_PROFILE.json} overrides; every override needs a SHA pin
  expected_grass_coverage     optional {area: float}; pending decision (0.0 vs 0.15)
  expected_landscape_count, expected_hda_count   optional ints
  accepted_failures  {check_id: exact str(error) text} known pre-existing failures, e.g.
                     {"profile_normal_pins:GazaRimal": "Corrected ground normal dependency differs: Sand_01_Normal"}.
                     NEVER_WAIVE ids are refused at startup; a waiver that matches no failure with exactly
                     its text FAILS the run (waivers_matched); post_s1 waivers must have been accepted with
                     the same text in the baseline receipt.
  require_clean      baseline only (default True); post_s1 forces require_clean/fresh/baseline True
  statistics_children (False)
  verifier_file + verifier_sha256   REQUIRED: the pinned copy actually executed
Refused: accepted_failure_ids, authoring_pids, expected_package_sha256 (derived now), statistics=False,
  require_fresh/require_baseline/require_clean=False in post_s1.
Verdict: *_VERIFIED_READ_ONLY only if every REQUIRED[phase] id has a PASS row (or an exact-text waived
row), no row is FAIL/NOT_RUN and no early gate aborted the run; otherwise FAILED_READ_ONLY_CHECKS.
Receipt check ids: dirty_before, expectations_wellformed, base_mi_unchanged, disk_matches_spec_baseline,
  baseline_receipt_binding, save_receipt_binding, named_save_boundary, expected_package_sha256,
  fresh_process, parent_chain, graph_snapshot, graph_matches_apply_receipt, old_graph_identity,
  reachability_iran_path, roots_and_switch, added_nodes_prefix_canvas, parameters_and_defaults,
  layer_samples, height_blend_llbs, material_functions, samplers_and_function_calls,
  no_pixel_normal_in_normal_or_height, grass_contract, instance_state_snapshot,
  effective_values_off_base_on_children, instances_unchanged_outside_s1, profile_normal_pins:<area>,
  profile_normal_pins:Iran_base, texture_bindings_and_samplers, registry_dependencies,
  landscapes_in_world, iran_statistics_equal, compile_log_errors, dirty_after_unchanged,
  disk_unchanged_during_run, inputs_unchanged_during_run, runtime_sources_unchanged,
  required_checks_present, waivers_matched.
"""
import datetime
import hashlib
import json
import os
import re
import struct
import sys
import traceback
import types
from collections import Counter
from pathlib import Path

# The module code object actually executing (inline exec, runpy or idle import); compared with
# compile(verifier_file) so the receipt binds the bytes that ran, not just a file with that hash.
_EXECUTED_CODE = sys._getframe(0).f_code
SCHEMA = 'environmentpipeline.stage1_s1_readonly_verify.v1'
GP = 'Staging/GroundPainting_2026-10-04'
PREP = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep'
# Frozen ground-chat helpers, exec'd idle exactly as GP/native_stochastic_verify_readonly.py:20-33.
STOCHASTIC_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
POLICY_SHA = 'bdba22a3bcf801663788166649e3fd593704507f133995a1085ed0b37c2404b4'
REFERENCE = GP + '/Revision_2026-10-05/EPIC_RESIDENT_RIMAL_verify_r031_epic_fresh_reopen_PID35000.json'
REFERENCE_SHA = 'c6b74f0f9fe5dd64d9027ac9fca253c99d878925c167e077394912158f302d4b'
PROFILES = {'GazaShujaiya': 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json',
            'GazaRimal': 'Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json',
            'Iran': 'Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json'}
VENDOR = ('/Game/MWLandscapeAutoMaterial/', '/Game/HighPoly_Tree_Model/',
          '/Game/Pegasus/', '/Game/PegasusWorkshop2024/')
LAYER_CLASSES = ('MaterialExpressionLandscapeLayerSample', 'MaterialExpressionLandscapeLayerWeight',
                 'MaterialExpressionLandscapeLayerSwitch', 'MaterialExpressionLandscapeLayerBlend',
                 'MaterialExpressionLandscapeVisibilityMask')
SWITCH_CLASS = 'MaterialExpressionStaticSwitchParameter'
KIND_CLASS = {'static_switch': SWITCH_CLASS, 'scalar': 'MaterialExpressionScalarParameter',
              'vector': 'MaterialExpressionVectorParameter',
              'texture_color': 'MaterialExpressionTextureObjectParameter',
              'texture_normal': 'MaterialExpressionTextureObjectParameter',
              'texture_masks': 'MaterialExpressionTextureObjectParameter'}
KIND_SAMPLER = {'texture_color': 'SAMPLERTYPE_COLOR', 'texture_normal': 'SAMPLERTYPE_NORMAL',
                'texture_masks': 'SAMPLERTYPE_MASKS'}
KIND_STATE = {'scalar': 'scalars', 'vector': 'vectors', 'static_switch': 'static_switches',
              'texture_color': 'textures', 'texture_normal': 'textures', 'texture_masks': 'textures'}
DEFAULT_SOURCES = ('SSM_WRAP_WORLD_GROUP_SETTINGS',)  # decision Shared:Wrap; Clamp only if expectations allow it
FORBIDDEN_NORMAL = ('MaterialExpressionPixelNormalWS',)
GRASS_COVERAGE = 'GeoCity_GrassCoverage'
GAZA = ('GazaShujaiya', 'GazaRimal')
PASS_STATUS = {'baseline': 'BASELINE_VERIFIED_READ_ONLY', 'post_s1': 'S1_VERIFIED_READ_ONLY'}
FAILED_STATUS = 'FAILED_READ_ONLY_CHECKS'
EXPECTATIONS_SCHEMA = 'environmentpipeline.stage1_s1_minimal_safe_spec.v1'
SAVE_SCHEMA = 'environmentpipeline.s1_material_edit.save.v1'
APPLY_SCHEMA = 'environmentpipeline.s1_material_edit.apply.v1'
# Read-only lease activations; ARGS may narrow, never widen (no writer lease such as GROUND_AUTHORING
# or MANAGER_ACTIVATED: another chat could mutate this PID between calls).
READONLY_ACTIVATIONS = frozenset({'STARTUP_INSPECTION_ONLY'})
RETIRED_ARGS = ('accepted_failure_ids', 'authoring_pids', 'expected_package_sha256')
# Never waivable: ARGS.accepted_failures naming one is refused at startup; Checks.run ignores such waivers.
NEVER_WAIVE = frozenset({
    'base_mi_unchanged', 'dirty_before', 'dirty_after_unchanged', 'expectations_wellformed', 'parent_chain',
    'graph_snapshot', 'old_graph_identity', 'reachability_iran_path', 'roots_and_switch',
    'effective_values_off_base_on_children', 'instances_unchanged_outside_s1', 'fresh_process',
    'expected_package_sha256', 'grass_contract', 'iran_statistics_equal', 'instance_state_snapshot',
    'baseline_receipt_binding', 'save_receipt_binding', 'named_save_boundary', 'graph_matches_apply_receipt',
    'disk_unchanged_during_run', 'inputs_unchanged_during_run', 'runtime_sources_unchanged',
    'required_checks_present', 'waivers_matched'})
# Every id here needs a PASS row (or an exact-text waived row) for the phase to pass.
REQUIRED_COMMON = (
    'dirty_before', 'expectations_wellformed', 'base_mi_unchanged', 'parent_chain', 'graph_snapshot',
    'old_graph_identity', 'reachability_iran_path', 'roots_and_switch', 'parameters_and_defaults',
    'material_functions', 'samplers_and_function_calls', 'grass_contract', 'instance_state_snapshot',
    'effective_values_off_base_on_children', 'profile_normal_pins:GazaShujaiya', 'profile_normal_pins:GazaRimal',
    'profile_normal_pins:Iran_base', 'texture_bindings_and_samplers', 'registry_dependencies',
    'landscapes_in_world', 'iran_statistics_equal', 'compile_log_errors', 'dirty_after_unchanged',
    'disk_unchanged_during_run', 'inputs_unchanged_during_run', 'runtime_sources_unchanged')
REQUIRED = {'baseline': REQUIRED_COMMON + ('disk_matches_spec_baseline',),
            'post_s1': REQUIRED_COMMON + (
                'baseline_receipt_binding', 'save_receipt_binding', 'named_save_boundary', 'expected_package_sha256',
                'fresh_process', 'graph_matches_apply_receipt', 'added_nodes_prefix_canvas', 'layer_samples',
                'height_blend_llbs', 'no_pixel_normal_in_normal_or_height', 'instances_unchanged_outside_s1')}


class Fail(Exception):
    pass


def need(condition, message):
    if not condition:
        raise Fail(message)
    return True


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def iso(seconds):
    return datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc).isoformat()


def enum_name(value):
    match = re.search(r'\.([A-Za-z0-9_]+)\s*(?::|>|$)', str(value))
    return match.group(1) if match else str(value)


def norm(path):
    return None if path is None else str(path).split('.')[0]


def vendor(path):
    return path is not None and any(str(path).startswith(v) for v in VENDOR)


def kind_of(value):
    if isinstance(value, bool):
        return 'static_switch'
    if isinstance(value, str):
        return 'texture_color'
    if isinstance(value, (list, tuple)):
        return 'vector'
    return 'scalar'


def same(kind, actual, expected):
    if kind == 'scalar':
        return actual is not None and f32(actual) == f32(expected)
    if kind == 'vector':
        return (isinstance(actual, (list, tuple)) and len(actual) == len(expected)
                and all(f32(a) == f32(b) for a, b in zip(actual, expected)))
    if kind == 'static_switch':
        return isinstance(actual, bool) and actual is bool(expected)
    return norm(actual) == norm(expected)


def resolve(root, value):
    file = Path(value)
    if not file.is_absolute():
        file = root / file
    file = file.resolve(strict=True)
    need(file.is_relative_to(root), 'Input outside the project: ' + str(file))
    return file


def bound_json(root, args, key, default_path=None, default_sha=None, required=True):
    value = args.get(key) or default_path
    if not value:
        need(not required, 'ARGS.' + key + ' is required')
        return None, None
    file = resolve(root, value)
    expected = args.get(key + '_sha256') or (default_sha if value == default_path else None)
    need(expected, 'ARGS.' + key + '_sha256 is required (SHA-bound input)')
    digest = sha(file)
    need(digest == expected, key + ' sha256 differs: ' + digest)
    return {'file': str(file), 'sha256': digest}, json.loads(file.read_text(encoding='utf-8-sig'))


def exec_pinned(file, expected, name):
    data = file.read_bytes()
    need(hashlib.sha256(data).hexdigest() == expected, 'Pinned helper bytes changed: ' + str(file))
    module = types.ModuleType(name)
    module.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), module.__dict__)
    need('ARGS' not in module.__dict__, 'Helper entry point must stay idle: ' + str(file))
    need(sha(file) == expected, 'Helper changed during load: ' + str(file))
    return module


def code_signature(code):
    """Pattern Content/Python/geocity_runtime_guard.py:26-32 (co_exceptiontable exists on 3.11+ only)."""
    constants = tuple(code_signature(v) if isinstance(v, types.CodeType) else v for v in code.co_consts)
    return (code.co_code, constants, code.co_names, code.co_varnames, code.co_freevars, code.co_cellvars,
            code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount, code.co_flags,
            getattr(code, 'co_exceptiontable', None))


def file_sha(file):
    try:
        return sha(file)
    except Exception as error:
        return 'UNREADABLE: %s: %s' % (type(error).__name__, error)


def parse_waivers(args):
    """Exact-text waivers {check_id: str(error)}; never-waive ids are refused before anything runs."""
    need('accepted_failure_ids' not in args,
         'ARGS.accepted_failure_ids is retired; use accepted_failures {check_id: exact error message}')
    waivers = args.get('accepted_failures') or {}
    need(isinstance(waivers, dict) and all(isinstance(k, str) and k and isinstance(v, str) and v
                                           for k, v in waivers.items()),
         'ARGS.accepted_failures must map check id -> exact non-empty error message')
    banned = sorted(set(waivers) & NEVER_WAIVE)
    need(not banned, 'Never-waive checks cannot be accepted: ' + ', '.join(banned))
    return dict(waivers)


def disk_snapshot(root, tracked):
    """sha256/size/mtime per tracked package file; read errors are recorded, never raised."""
    disk = {}
    for package, suffix in tracked:
        file = root / 'Content' / (package[len('/Game/'):] + suffix)
        row = {'file': str(file)}
        try:
            row['exists'] = file.exists()
            if row['exists']:
                stat = file.stat()
                row.update(sha256=sha(file), bytes=stat.st_size, mtime_utc=iso(stat.st_mtime), mtime=stat.st_mtime)
        except Exception as error:
            row['error'] = '%s: %s' % (type(error).__name__, error)
        disk[package] = row
    return disk


def plan_mismatches(exp, plans, coverage):
    """Expectation per-area values vs the apply receipt plans (s1_material_edit.plan_children), both ways."""
    problems = []
    per_area = (exp.get('existing_param_child_overrides') or {}).get('per_area') or {}
    for a, plan in sorted(plans.items()):
        given = {}
        for field in ('textures', 'vectors', 'scalars'):
            for name, value in (plan.get(field) or {}).items():
                given[name] = value.get('path') if field == 'textures' else value
        if GRASS_COVERAGE in given:
            want = (coverage or {}).get(a)
            if want is None or f32(want) != f32(given[GRASS_COVERAGE]):
                problems.append([a, GRASS_COVERAGE, given[GRASS_COVERAGE], want])
            given.pop(GRASS_COVERAGE)
        for entry in exp['new_parameters']:
            if entry['kind'] == 'static_switch':
                continue  # the edit sets the switch True for every planned child; c_effective reads it back
            want = given.pop(entry['name'], entry['master_default'])
            if a not in entry or not same(entry['kind'], entry[a], want):
                problems.append([a, entry['name'], entry.get(a), want])
        for name, value in (per_area.get(a) or {}).items():
            got = given.pop(name, None)
            if got is None or not same(kind_of(value), got, value):
                problems.append([a, name, got, value])
        if given:
            problems.append([a, 'plan_values_absent_from_expectations', sorted(given)])
    return problems


def bind_baseline(info, run):
    """Review (a)-(d): a passed baseline of this verifier sha, expectations, reference and area/map, with
    exact-text waivers only (none never-waive), taken before the S1 save; post_s1 waivers were accepted there."""
    baseline, files = run.baseline, run.files
    bfiles = baseline.get('input_files') or {}
    accepted = baseline.get('accepted_known_failures')
    info.update(file=files['baseline_receipt']['file'], pid=baseline.get('pid'), area=baseline.get('area'),
                status=baseline.get('status'), accepted=accepted)
    need(baseline.get('schema') == SCHEMA and baseline.get('phase') == 'baseline'
         and baseline.get('status') == PASS_STATUS['baseline'] and baseline.get('failed_checks') == [],
         'Baseline receipt is not a passed baseline')
    need((bfiles.get('expectations') or {}).get('sha256') == files['expectations']['sha256'],
         '(a) Baseline used other expectations')
    need(baseline.get('area') == run.area and baseline.get('world') == run.named_map, '(b) Baseline area/map differs')
    need(isinstance(accepted, list) and all(isinstance(x, dict) and set(x) == {'id', 'message'} for x in accepted),
         '(c) Baseline predates exact-text waivers: re-run the baseline with this verifier')
    need(not [x['id'] for x in accepted if x['id'] in NEVER_WAIVE], '(c) Baseline accepted a never-waive check')
    pairs = {(x['id'], x['message']) for x in accepted}
    info['post_waivers_not_in_baseline'] = sorted(k for k, v in run.waivers.items() if (k, v) not in pairs)
    need(not info['post_waivers_not_in_baseline'], '(c) post_s1 waiver was not accepted with the same text at baseline')
    need((bfiles.get('verifier') or {}).get('sha256') == files['verifier']['sha256'],
         '(d) Baseline ran another verifier sha')
    need((bfiles.get('reference_graph') or {}).get('sha256') == files['reference_graph']['sha256'],
         '(d) Baseline used another reference graph')
    need(isinstance(baseline.get('disk'), dict) and isinstance(baseline.get('instances'), dict)
         and isinstance(baseline.get('registry_dependencies'), dict)
         and isinstance((baseline.get('graph') or {}).get('static_switch_names'), list),
         'Baseline lacks disk/instance/dependency/switch evidence')
    need(datetime.datetime.fromisoformat(baseline['utc']) < datetime.datetime.fromisoformat(run.save['utc']),
         'Baseline was not taken before the S1 save')


def bind_save(info, run):
    """The s1_material_edit SAVED_NAMED_ONLY receipt, its SHA-bound apply receipt, the edit script that generated
    the expectations, and the per-area plan (apply plans == expectation per-area values, both ways)."""
    save, exp, files = run.save, run.exp, run.files
    info.update(file=files['save_receipt']['file'], pid=save.get('pid'), status=save.get('status'),
                script_sha256=save.get('script_sha256'), scope=run.scope)
    need(save.get('schema') == SAVE_SCHEMA and save.get('mode') == 'save' and save.get('status') == 'SAVED_NAMED_ONLY',
         'Save receipt is not an s1_material_edit SAVED_NAMED_ONLY receipt')
    need(run.authoring and run.pid not in run.authoring, 'Save receipt PID missing or equal to this PID')
    need(save.get('saves') and all(s.get('result') is True for s in save['saves']), 'A named save group did not succeed')
    need(save.get('dirty_after') == {'maps': [], 'content': []}, 'Save receipt dirty_after is not clean')
    need((exp.get('generated_by') or {}).get('target_sha256') == save.get('script_sha256'),
         'Expectations were not generated from the edit script that saved (generated_by.target_sha256)')
    ref = save.get('apply_receipt') or {}
    need(ref.get('file') and ref.get('sha256'), 'Save receipt lacks its apply receipt binding')
    apply_file = resolve(run.root, ref['file'])
    need(sha(apply_file) == ref['sha256'], 'Apply receipt bytes differ from the save receipt binding')
    files['apply_receipt'] = {'file': str(apply_file), 'sha256': ref['sha256']}
    applied = json.loads(apply_file.read_text(encoding='utf-8-sig'))
    need(applied.get('schema') == APPLY_SCHEMA and applied.get('status') == 'APPLIED_VERIFIED_NO_SAVE'
         and applied.get('pid') == save.get('pid') and applied.get('script_sha256') == save.get('script_sha256'),
         'Apply receipt is not the APPLIED_VERIFIED_NO_SAVE run of the saving PID/script')
    plans = applied.get('plans') or {}
    info.update(plans=sorted(plans), expectation_areas=run.exp_areas)
    need(run.scope and sorted(plans) == run.scope == run.exp_areas,
         'In-scope areas differ between saved children, apply plans and expectations')
    info['plan_mismatches'] = plan_mismatches(exp, plans, run.coverage)
    need(not info['plan_mismatches'], 'Expectation per-area values differ from the apply receipt plans')
    run.apply['receipt'] = applied


def bind_named_saves(info, run):
    """Named-save boundary: saved set == S1 functions + master + in-scope children; base MI, Grass type,
    both maps and any out-of-scope child are byte-identical to the baseline receipt's disk."""
    save, baseline, disk = run.save, run.baseline, run.disk
    keys = sorted(norm(k) for k in (save.get('disk_after') or {}))
    want = sorted(set(run.mfs) | {run.master_pkg} | {run.child_pkgs[a] for a in run.scope})
    info.update(saved=keys, expected=want)
    need(run.scope and keys == want, 'Saved packages differ from the S1 functions + master + in-scope children')
    prior = baseline.get('disk') or {}
    never = ([run.base_pkg, run.grass_pkg] + sorted(run.maps.values())
             + [run.child_pkgs[a] for a in GAZA if a not in run.scope])
    state = lambda row: (bool((row or {}).get('exists')), (row or {}).get('sha256'))
    info['never_saved'] = {k: {'baseline': state(prior.get(k)), 'now': state(disk.get(k))} for k in never}
    need(all(state(prior.get(k))[1] for k in never), 'Baseline receipt lacks a never-saved package sha256')
    info['changed'] = sorted(k for k in never if state(prior.get(k)) != state(disk.get(k)))
    need(not info['changed'], 'Never-saved package (base MI/Grass type/map/out-of-scope child) changed since baseline')


def bind_expected_disk(info, run):
    """Current disk sha256 == the save receipt's disk_after for every saved package; S1 functions exist."""
    disk = run.disk
    expected = {norm(k): (v or {}).get('sha256') for k, v in (run.save.get('disk_after') or {}).items()}
    info['expected'] = expected
    need(expected and all(expected.values()), 'Save receipt disk_after lacks sha256 values')
    info['mismatch'] = {k: (disk.get(k) or {}).get('sha256') for k, v in expected.items()
                        if (disk.get(k) or {}).get('sha256') != v}
    need(not info['mismatch'], 'Package sha256 differs from the named-save receipt disk_after')
    need(all((disk.get(x) or {}).get('exists') for x in run.mfs), 'An S1 function package is missing on disk')


def bfs(rows, starts):
    seen, pending = set(), [s for s in starts if s]
    while pending:
        node = pending.pop()
        if node in seen or node not in rows:
            continue
        seen.add(node)
        pending.extend(e['source'] for e in rows[node]['edges'].values() if e.get('source'))
    return seen


def pin(row, wanted, override=None):
    names = row.get('input_names', [])
    if override:
        need(override in names, 'Spec switch pin %r absent; pins=%r' % (override, names))
        return override
    hits = [n for n in names if n.lower() == wanted]
    need(len(hits) == 1, 'Switch pin %r not unique/absent; pins=%r' % (wanted, names))
    return hits[0]


class Checks:
    """Check rows + verdict gates. Pure Python (no unreal), so the verdict logic is testable offline."""

    def __init__(self, waivers):
        self.rows, self.waivers = [], dict(waivers or {})

    def run(self, cid, fn):
        info = {}
        try:
            fn(info)
            self.rows.append({'id': cid, 'status': 'PASS', 'detail': info})
            return True
        except Exception as error:
            message = str(error)
            # A waiver applies only to its exact error text and never to a NEVER_WAIVE id.
            waived = cid not in NEVER_WAIVE and self.waivers.get(cid) == message
            self.rows.append({'id': cid, 'status': 'ACCEPTED_KNOWN_FAILURE' if waived else 'FAIL',
                              'error': '%s: %s' % (type(error).__name__, message), 'message': message,
                              'waiver': self.waivers.get(cid), 'detail': info,
                              'trace': traceback.format_exc(limit=8)[-4000:]})
            return False

    def skip(self, cid, reason):
        """Not applicable to this phase; never satisfies a REQUIRED id."""
        self.rows.append({'id': cid, 'status': 'NOT_APPLICABLE', 'reason': reason})

    def not_run(self, cid, reason):
        """Applicable but could not execute (a prerequisite failed); counts as a failure."""
        self.rows.append({'id': cid, 'status': 'NOT_RUN', 'reason': reason})

    def failed(self):
        return [r['id'] for r in self.rows if r['status'] in ('FAIL', 'NOT_RUN')]

    def accepted_failures(self):
        return [{'id': r['id'], 'message': r['message']} for r in self.rows if r['status'] == 'ACCEPTED_KNOWN_FAILURE']

    def close(self, required):
        """Final gates: every required id PASSED (or exact-text waived) and every waiver matched a failure."""
        def c_required(info):
            seen = {}
            for r in self.rows:
                seen.setdefault(r['id'], set()).add(r['status'])
            info['absent'] = sorted(c for c in required if c not in seen)
            info['not_applicable'] = sorted(c for c in required if seen.get(c) == {'NOT_APPLICABLE'})
            info['not_passed'] = sorted(c for c in required if c in seen and seen[c] != {'NOT_APPLICABLE'}
                                        and not seen[c] <= {'PASS', 'ACCEPTED_KNOWN_FAILURE'})
            need(not (info['absent'] or info['not_applicable'] or info['not_passed']),
                 'Required checks absent/not applicable/not passed: ' + ', '.join(
                     info['absent'] + info['not_applicable'] + info['not_passed']))

        def c_waivers(info):
            matched = {r['id'] for r in self.rows if r['status'] == 'ACCEPTED_KNOWN_FAILURE'}
            info['waivers'] = dict(self.waivers)
            info['unmatched'] = sorted(set(self.waivers) - matched)
            need(not info['unmatched'], 'Waiver matched no failure with exactly its text: ' + ', '.join(info['unmatched']))
        self.run('required_checks_present', c_required)
        self.run('waivers_matched', c_waivers)


def guard(unreal, h, root, args, named_map, authoring, require_fresh):
    """Fatal preconditions; pattern GP/native_graph_stochastic.py:192-217 without its fixed owner/HDA count.
    authoring: PIDs that saved S1 (post_s1: from the SHA-bound save receipt)."""
    lines = [s for s in (root / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(
        encoding='utf-8-sig').splitlines() if s.strip()]
    lease = lines[-1]
    fields = dict(t.split('=', 1) for t in lease.split() if '=' in t)
    owner = str(args.get('lease_owner') or '')
    need(owner and owner != 'NONE' and fields.get('OWNER') == owner, 'Lease OWNER differs from ARGS.lease_owner')
    need(fields.get('assigned_editor_PID') == str(os.getpid()), 'Lease is not for this editor PID')
    need(fields.get('map') == named_map, 'Lease map differs from the open world')
    allowed = set(args.get('allowed_activations') or READONLY_ACTIVATIONS)
    need(allowed <= READONLY_ACTIVATIONS, 'ARGS.allowed_activations may only narrow the read-only set: '
         + ', '.join(sorted(allowed - READONLY_ACTIVATIONS)))
    need(fields.get('activation') in allowed, 'Lease activation not allowed: ' + str(fields.get('activation')))
    thread = str(args.get('operator_thread_id') or '')
    need(thread and thread != 'NONE', 'ARGS.operator_thread_id is required')
    need(fields.get('operator_thread_id') == thread, 'Lease operator thread differs')
    authoring = sorted(int(x) for x in authoring)
    if require_fresh:
        need(authoring, 'post_s1 freshness requires the save receipt PID')
        need(os.getpid() not in authoring, 'Verifier must run in a fresh process, not an authoring PID')
    import geocity_runtime_guard
    sources = geocity_runtime_guard.verify()  # sealed-source preflight, geocity_runtime_guard.py:118-131
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    need(api and api.is_asset_cooking_paused(), 'Houdini Engine cooking must be paused')
    settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorLoadingSavingSettings'))
    need(not settings.get_editor_property('bAutoSaveEnable'), 'Editor autosave must be off')
    ticks = [name + '.' + key for name in ('geocity_bank_workflow', 'geocity_roadbld_workflow')
             for run in getattr(sys.modules.get(name), 'ACTIVE', [])
             for key in ('watch_tick', 'save_tick', 'tick_handle', '_pending_correction')
             if getattr(run, key, None) is not None]
    need(not ticks, 'Workflow ticks are active: ' + str(ticks))
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    hdas = []
    for actor in actors:
        if isinstance(actor, unreal.HoudiniAssetActor):
            wrapper = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None, actor)
            row = {'actor': h.path(actor), 'auto_cook': bool(wrapper.is_auto_cooking_enabled()),
                   'auto_bake': bool(wrapper.is_auto_bake_enabled())}
            need(not row['auto_cook'] and not row['auto_bake'], 'HDA auto cook/bake enabled: ' + row['actor'])
            hdas.append(row)
    if args.get('expected_hda_count') is not None:
        need(len(hdas) == int(args['expected_hda_count']), 'HDA actor count differs: %d' % len(hdas))
    return {'lease_line': lease, 'lease_fields': fields, 'runtime_sources': sources, 'cooking_paused': True,
            'autosave': False, 'workflow_ticks': [], 'hda_actors': hdas, 'authoring_pids': authoring}, actors


def fdescribe(h, function, expression):
    """Material-function node row (pattern GP/native_function_probe.py:16-23)."""
    names = list(h.LIB.get_material_expression_input_names(expression))
    sources = list(h.LIB.get_inputs_for_material_function_expression(function, expression))
    row = {'class': expression.get_class().get_name(), 'input_names': names, 'properties': {}}
    row['edges'] = ({n: h.path(s) for n, s in zip(names, sources)} if len(names) == len(sources)
                    else {'_count_mismatch': [names, [h.path(s) for s in sources]]})
    for key in ('parameter_name', 'input_name', 'output_name', 'input_type', 'sampler_type', 'sampler_source',
                'texture', 'material_function', 'desc', 'mip_value_mode', 'const_a', 'const_b', 'r', 'g', 'b',
                'a', 'value', 'default_value', 'constant', 'sort_priority'):
        value = h.safe(expression, key)
        if value is not None:
            row['properties'][key] = h.plain(value)
    return row


def statistics(h, material):
    """Native preview statistics (pattern GP/native_stochastic_verify_readonly.py:68-100)."""
    try:
        stats = h.LIB.get_statistics(material)
    except Exception as error:
        return {'status': 'READ_FAILED', 'error': str(error)}
    row = {'status': 'READ_ONLY_NATIVE_RESULT'}
    for field in ('num_vertex_shader_instructions', 'num_pixel_shader_instructions', 'num_samplers',
                  'num_vertex_texture_samples', 'num_pixel_texture_samples', 'num_virtual_texture_samples',
                  'num_uv_scalars', 'num_interpolator_scalars'):
        try:
            row[field] = int(stats.get_editor_property(field))
        except Exception as error:
            row[field] = {'status': 'FIELD_NOT_EXPOSED', 'error': str(error)}
    return row


def derived_sampler(props):
    """INFERRED mirror of MaterialExpressionUtils::GetSamplerTypeForTexture (MaterialExpressionUtils.h:25)."""
    def value(name):
        entry = props.get(name, {})
        return entry.get('value') if entry.get('status') == 'READ' else None
    raw, srgb, vt = value('compression_settings'), value('srgb'), value('virtual_texture_streaming')
    if raw is None or srgb is None or vt is None:
        return None
    compression = enum_name(raw)
    base = {'TC_NORMALMAP': 'NORMAL', 'TC_MASKS': 'MASKS', 'TC_ALPHA': 'ALPHA',
            'TC_DISTANCE_FIELD_FONT': 'DISTANCE_FIELD_FONT'}.get(compression)
    if base is None and compression == 'TC_GRAYSCALE':
        base = 'GRAYSCALE' if srgb else 'LINEAR_GRAYSCALE'
    if base is None:
        base = 'COLOR' if srgb else 'LINEAR_COLOR'
    return 'SAMPLERTYPE_' + ('VIRTUAL_' if vt and base != 'DISTANCE_FIELD_FONT' else '') + base


def run_s1_verify(args):
    """Entry point. Not named main(): SkillRunner.run_script calls main(args) again after runpy
    (runner.py:207-210), and that second run would refuse to overwrite this run's receipt."""
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    pid = os.getpid()
    phase = args.get('phase')
    need(phase in PASS_STATUS, "ARGS.phase must be 'baseline' or 'post_s1'")
    post = phase == 'post_s1'
    label = str(args.get('label') or '')
    need(label and all(c.isascii() and (c.isalnum() or c == '_') for c in label), 'Label must be ascii [A-Za-z0-9_]')
    out = root / PREP / 'receipts' / ('VERIFY_%s_%d.json' % (label, pid))
    need(not out.exists(), 'Never overwrite earlier evidence: ' + str(out))
    waivers = parse_waivers(args)
    retired = sorted(k for k in RETIRED_ARGS if k in args)
    need(not retired, 'Retired ARGS (now derived from the SHA-bound receipts): ' + ', '.join(retired))
    need(args.get('statistics', True) is True, 'iran_statistics_equal is required; ARGS.statistics cannot disable it')
    relaxed = sorted(k for k in ('require_fresh', 'require_baseline', 'require_clean') if args.get(k, True) is not True)
    need(not (post and relaxed), 'post_s1 cannot relax protections: ' + ', '.join(relaxed))
    require_fresh = post
    require_clean = True if post else bool(args.get('require_clean', True))
    # Bind the receipt to the code actually executed: SHA pin, code-signature proof against the
    # running module code (pattern Content/Python/geocity_runtime_guard.py:26-32), sibling SCRIPT_PINS.json.
    need(args.get('verifier_file') and args.get('verifier_sha256'), 'ARGS.verifier_file + verifier_sha256 required')
    verifier = resolve(root, args['verifier_file'])
    source = verifier.read_bytes()
    need(hashlib.sha256(source).hexdigest() == args['verifier_sha256'], 'verifier_file sha256 differs from ARGS.verifier_sha256')
    need(code_signature(_EXECUTED_CODE) == code_signature(compile(source, str(verifier), 'exec')),
         'Executed code differs from verifier_file (code signature)')
    pins_file = verifier.parent / 'SCRIPT_PINS.json'
    need(pins_file.is_file(), 'SCRIPT_PINS.json beside verifier_file is required (root pin for the Stage-1 copilot_call)')
    need(json.loads(pins_file.read_text(encoding='utf-8-sig')).get(verifier.name) == args['verifier_sha256'],
         'SCRIPT_PINS.json does not pin verifier_file to ARGS.verifier_sha256')

    h = exec_pinned((root / GP / 'native_graph_stochastic.py').resolve(strict=True), STOCHASTIC_SHA,
                    's1_verify_frozen_graph_helper')
    p = exec_pinned((root / GP / 'native_ground_texture_policy.py').resolve(strict=True), POLICY_SHA,
                    's1_verify_frozen_texture_policy')
    LIB = h.LIB
    lw = sys.modules.get('geocity_landscape_workflow')
    need(lw is not None, 'Sealed geocity_landscape_workflow is not loaded; use the sealed startup')

    files = {'verifier': {'file': str(verifier), 'sha256': args['verifier_sha256']},
             'script_pins': {'file': str(pins_file), 'sha256': sha(pins_file)},
             'graph_helper': {'file': str(root / GP / 'native_graph_stochastic.py'), 'sha256': STOCHASTIC_SHA},
             'texture_policy_helper': {'file': str(root / GP / 'native_ground_texture_policy.py'), 'sha256': POLICY_SHA}}
    files['expectations'], exp = bound_json(root, args, 'expectations')
    for key in ('children', 'new_parameters', 'static_switch_nodes', 'node_desc_prefix', 'baseline_expectations',
                'new_function_packages'):
        need(key in exp, 'Expectations lack required key: ' + key)
    need(isinstance(exp['children'], dict) and set(exp['children']) == set(GAZA),
         'Expectations must list both Gaza children (both are always tracked)')
    files['reference_graph'], reference = bound_json(root, args, 'reference_graph', REFERENCE, REFERENCE_SHA)
    baseline = save = None
    if post:
        files['baseline_receipt'], baseline = bound_json(root, args, 'baseline_receipt')
        files['save_receipt'], save = bound_json(root, args, 'save_receipt')
        need(isinstance(baseline, dict) and isinstance(save, dict), 'Baseline/save receipts must be JSON objects')
    overrides, pinned = dict(args.get('profiles') or {}), dict(args.get('profile_sha256') or {})
    need(set(overrides) <= set(pinned), 'Every ARGS.profiles override needs ARGS.profile_sha256: '
         + ', '.join(sorted(set(overrides) - set(pinned))))
    profiles = {}
    for name, rel in dict(PROFILES, **overrides).items():
        file = resolve(root, rel)
        files['profile:' + name] = {'file': str(file), 'sha256': sha(file)}
        need(name not in pinned or pinned[name] == files['profile:' + name]['sha256'], 'Profile sha256 differs: ' + name)
        profiles[name] = json.loads(file.read_text(encoding='utf-8-sig'))

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    areas = [a for a in GAZA if profiles.get(a, {}).get('map') == named_map]
    need(len(areas) == 1, 'Open world is not exactly one S1 area map: ' + named_map)
    area = areas[0]
    # Areas with per-area values in the expectations, and the in-scope children: post_s1 = the children the
    # named-save receipt saved (save_receipt_binding re-checks them against the apply plans); baseline = both.
    exp_areas = sorted(a for a in GAZA if exp['new_parameters']
                       and all(isinstance(e, dict) and a in e for e in exp['new_parameters']))
    scope, authoring = sorted(GAZA), []
    if post:
        saved_keys = {norm(k) for k in (save.get('disk_after') or {})}
        scope = sorted(a for a in GAZA if norm(exp['children'][a]) in saved_keys)
        authoring = [save['pid']] if isinstance(save.get('pid'), int) else []
    environment, actors = guard(unreal, h, root, args, named_map, authoring, require_fresh)

    checks = Checks(waivers)
    mfs = [norm(x) for x in exp['new_function_packages']]
    child_pkgs = {a: norm(exp['children'][a]) for a in GAZA}
    maps = {a: norm(profiles[a]['map']) for a in GAZA}
    # Never dirty in any phase; re-hashed at the end (another editor/chat must not save them mid-run).
    protected = sorted({norm(lw.MASTER), norm(lw.BASE), norm(lw.GRASS_TYPE)} | set(child_pkgs.values())
                       | set(mfs) | set(maps.values()))
    tracked = [(x, '.umap' if x in maps.values() else '.uasset') for x in protected]
    disk = disk_snapshot(root, tracked)
    dirty = lambda: {'maps': sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                     'content': sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
    dirty_before = dirty()
    R = {'environment': environment, 'dirty_before': dirty_before, 'disk': disk, 'scope': scope,
         'expectation_areas': exp_areas, 'authoring_pids': authoring}
    run = types.SimpleNamespace(h=h, out=out, R=R, checks=checks, files=files, exp=exp, phase=phase, area=area,
                                named_map=named_map, pid=pid, dirty=dirty, dirty_before=dirty_before, root=root,
                                tracked=tracked, disk=disk, protected=protected, waivers=waivers,
                                baseline=baseline, save=save, scope=scope, exp_areas=exp_areas, authoring=authoring,
                                apply={}, mfs=mfs, child_pkgs=child_pkgs, maps=maps, master_pkg=norm(lw.MASTER),
                                base_pkg=norm(lw.BASE), grass_pkg=norm(lw.GRASS_TYPE),
                                coverage=args.get('expected_grass_coverage'))
    base_exp = exp['baseline_expectations']

    def c_dirty_before(info):
        info.update(dirty_before)
        info['protected_dirty'] = sorted(x for x in dirty_before['maps'] + dirty_before['content'] if norm(x) in protected)
        need(not info['protected_dirty'], 'Master/base/child/S1 function/Grass type/map package dirty before verification')
        need(not dirty_before['maps'], 'Dirty map packages before verification')
        need(not any(vendor(x) for x in dirty_before['content']), 'Vendor package dirty before verification')
        if require_clean:
            need(not dirty_before['content'], 'Dirty content packages before verification')
    checks.run('dirty_before', c_dirty_before)

    # ---------- expectations sanity ----------
    spec_params = {}

    def c_expectations(info):
        need(exp.get('schema') == EXPECTATIONS_SCHEMA, 'Expectations schema differs')
        generated = exp.get('generated_by') or {}
        info['generated_by'] = generated
        need(re.fullmatch(r'[0-9a-f]{64}', str(generated.get('target_sha256') or '')),
             'Expectations lack generated_by.target_sha256: generate them with s1_material_edit_offline.py '
             '(never the hand-made minimal spec)')
        names = [x['name'] for x in exp['new_parameters']]
        need(len(names) == len(set(names)), 'Duplicate spec parameter names')
        need(exp.get('new_parameter_names') in (None, len(names)), 'new_parameter_names differs from the list')
        need(exp_areas, 'Expectations carry no per-area values')
        for entry in exp['new_parameters']:
            need(entry['kind'] in KIND_CLASS, 'Unknown parameter kind: ' + entry['kind'])
            need(all(a in entry for a in exp_areas), 'Spec lacks per-area value: ' + entry['name'])
            spec_params[entry['name']] = entry
        sw = exp['static_switch_nodes']
        need(spec_params.get(sw['name'], {}).get('kind') == 'static_switch', 'Switch is not a spec static_switch')
        need(spec_params[sw['name']]['master_default'] is False, 'Switch master default must be False')
        need(len(sw['roots']) == len(sw['False_pin_sources']), 'Switch roots/False sources differ in length')
        need(norm(exp.get('master', lw.MASTER)) == norm(lw.MASTER), 'Spec master differs from LW:16')
        need(norm(exp.get('base_mi_untouched', lw.BASE)) == norm(lw.BASE), 'Spec base MI differs from LW:15')
        need(mfs and len(mfs) == len(set(mfs)), 'Expectations list no (or duplicate) S1 function packages')
        need(all(m.rsplit('/', 1)[1] in (exp.get('functions') or {}) for m in mfs), 'functions spec lacks an S1 function')
        need(exp.get('new_landscape_layer_samples') and (exp.get('new_llbs') or {}).get('count') is not None,
             'Layer-sample/LLB expectations required (no vacuous post_s1 checks)')
        need((exp.get('sampler_estimate') or {}).get('new_samples') is not None and exp.get('added_node_count') is not None,
             'sampler_estimate.new_samples and added_node_count required')
        for key in ('node_count', 'graph_sha256_r030', 'reachable_any_root_plus_grass', 'root_layer_pins_connected',
                    'master_and_children_preview_stats_PID10460'):
            need(base_exp.get(key) is not None, 'baseline_expectations lacks ' + key)
        need(all(k in base_exp.get('disk_sha256', {})
                 for k in ('master', 'base_mi', 'shujaiya_child', 'rimal_child')), 'baseline disk_sha256 incomplete')
        info.update(parameters=len(names), switch=sw['name'], functions=mfs, expectation_areas=exp_areas)
    if not checks.run('expectations_wellformed', c_expectations):
        return finish(run, aborted='expectations_wellformed')
    switch_name = exp['static_switch_nodes']['name']

    # ---------- disk (tracked packages hashed once at start, re-hashed in finish) ----------
    def c_base_disk(info):
        # Iran backstop: never waivable. The base MI is never saved by S1 or prepare() (LW:353,382).
        info.update(actual=disk[norm(lw.BASE)].get('sha256'), expected=base_exp['disk_sha256']['base_mi'])
        need(info['actual'] == info['expected'], 'Base MI (Iran) package changed from the S1 baseline')
    checks.run('base_mi_unchanged', c_base_disk)

    def c_spec_disk(info):
        # Expected to drift after any ordinary run: prepare() re-saves master/child (LW:350-353,382).
        spec_disk = {norm(lw.MASTER): base_exp['disk_sha256']['master'],
                     child_pkgs['GazaShujaiya']: base_exp['disk_sha256']['shujaiya_child'],
                     child_pkgs['GazaRimal']: base_exp['disk_sha256']['rimal_child']}
        info['mismatch'] = {k: disk[k].get('sha256') for k, v in spec_disk.items() if disk[k].get('sha256') != v}
        need(not info['mismatch'], 'Disk differs from spec baseline: re-baseline (graph digest decides) before S1')
        need(not any(disk[x].get('exists') for x in mfs), 'S1 function packages already exist on disk')
    if phase == 'baseline':
        checks.run('disk_matches_spec_baseline', c_spec_disk)
    else:
        checks.skip('disk_matches_spec_baseline', 'post_s1: bound by the named-save receipt instead')

    # ---------- post_s1 bindings (module-level, offline-tested): baseline receipt (a-d), save receipt, boundary ----------
    for cid, fn in (('baseline_receipt_binding', bind_baseline), ('save_receipt_binding', bind_save),
                    ('named_save_boundary', bind_named_saves), ('expected_package_sha256', bind_expected_disk)):
        if post:
            checks.run(cid, lambda info, fn=fn: fn(info, run))
        else:
            checks.skip(cid, 'baseline phase: no S1 saves yet')

    startup = root / 'Staging/SystemCompletion_2026-10-04' / ('RUNTIME_STARTUP_PID%d.json' % pid)
    fresh = {'pid': pid, 'startup_receipt': str(startup)}
    try:
        fresh['startup_receipt_exists'] = startup.exists()
        saved = [disk[x]['mtime'] for x in [norm(lw.MASTER)] + [child_pkgs[a] for a in scope] + mfs
                 if disk.get(x, {}).get('mtime') is not None]
        if fresh['startup_receipt_exists']:
            fresh['startup_mtime_utc'] = iso(startup.stat().st_mtime)
            fresh['startup_receipt_pid'] = json.loads(startup.read_text(encoding='utf-8')).get('pid')
            fresh['process_started_after_package_saves'] = bool(saved) and startup.stat().st_mtime > max(saved)
        fresh['latest_s1_package_mtime_utc'] = iso(max(saved)) if saved else None
    except Exception as error:
        fresh['error'] = '%s: %s' % (type(error).__name__, error)
    R['freshness'] = fresh

    def c_fresh(info):
        info.update(fresh)
        need(authoring and pid not in authoring, 'post_s1 must run in a PID other than the saving PID')
        need(fresh.get('startup_receipt_exists') and fresh.get('startup_receipt_pid') == pid,
             'No sealed-startup receipt for this PID')
        need(fresh.get('process_started_after_package_saves'), 'Process did not start after the S1 package saves')
    if require_fresh:
        checks.run('fresh_process', c_fresh)
    else:
        checks.skip('fresh_process', 'baseline phase')

    # ---------- assets + parent chain (LW:219-224, 364-369, 416) ----------
    A = {}

    def c_parents(info):
        A.update(master=unreal.load_asset(lw.MASTER), base=unreal.load_asset(lw.BASE),
                 children={a: unreal.load_asset(pth) for a, pth in exp['children'].items()},
                 grass=unreal.load_asset(lw.GRASS_TYPE))
        master, base, children = A['master'], A['base'], A['children']
        need(isinstance(master, unreal.Material) and h.path(master) == lw.MASTER, 'Master unavailable at LW:16 path')
        need(isinstance(base, unreal.MaterialInstanceConstant), 'Base MI unavailable')
        need(base.get_editor_property('parent') == master, 'Base MI parent is not the retained master (LW:222-224)')
        info['base'] = h.path(base)
        for a, child in children.items():
            need(isinstance(child, unreal.MaterialInstanceConstant), 'Child unavailable: ' + a)
            need(h.path(child.get_editor_property('parent')) == lw.BASE, 'Child parent differs (LW:368,416): ' + a)
            owner = str(unreal.EditorAssetLibrary.get_metadata_tag(child, 'GeoCityOwner'))
            need(owner == lw.OWNER, 'Child GeoCityOwner differs (LW:364): ' + a)
            need(h.path(child) == profiles[a]['landscape_material'], 'Profile landscape_material differs: ' + a)
            info[a] = h.path(child)
        need(profiles['Iran'].get('landscape_material') == lw.BASE, 'Iran profile no longer binds the base MI')
    if not checks.run('parent_chain', c_parents):
        return finish(run, aborted='parent_chain')
    master, base, children, grass = A['master'], A['base'], A['children'], A['grass']

    # ---------- graph snapshot (frozen describe(); digest comparable with r030/r031) ----------
    G = {}

    def c_snapshot(info):
        exprs = list(LIB.get_material_expressions(master))
        G['rows'] = {h.path(e): h.describe(master, e) for e in exprs}
        G['objects'] = {h.path(e): e for e in exprs}
        G['roots'] = {k: h.path(LIB.get_material_property_input_node(master, prop)) for k, prop in h.PROPERTIES.items()}
        G['settings'] = {k: h.plain(master.get_editor_property(k)) for k in reference['material_settings']}
        G['switch_names'] = sorted(str(n) for n in LIB.get_static_switch_parameter_names(master))
        G['param_names'] = sorted({str(n) for fn in (LIB.get_scalar_parameter_names, LIB.get_vector_parameter_names,
                                                     LIB.get_texture_parameter_names) for n in fn(master)}
                                  | set(G['switch_names']))
        info.update(node_count=len(G['rows']), roots=G['roots'], static_switch_names=G['switch_names'])
    if not checks.run('graph_snapshot', c_snapshot):
        return finish(run, aborted='graph_snapshot')
    rows, roots = G['rows'], G['roots']
    ref_nodes, ref_roots = reference['nodes'], reference['roots']
    added = sorted(set(rows) - set(ref_nodes))
    R['graph'] = {'node_count': len(rows), 'added_count': len(added), 'roots': roots,
                  'material_settings': G['settings'], 'static_switch_names': G['switch_names'],
                  'added_nodes': {q: rows[q] for q in added}, 'graph_sha256_all': h.digest(rows)}
    prop_key = {enum_name(h.plain(v)): k for k, v in h.PROPERTIES.items()}
    grass_ref = [q for q, r in ref_nodes.items() if r['class'] == 'MaterialExpressionLandscapeGrassOutput']

    def c_apply_graph(info):
        applied = run.apply.get('receipt')
        need(applied, 'Apply receipt unavailable (save_receipt_binding failed)')
        info.update(live=R['graph']['graph_sha256_all'], applied=applied.get('graph_after_sha256'),
                    live_count=len(rows), applied_count=applied.get('graph_count_after'))
        need(info['live'] == info['applied'], 'Live master graph differs from the apply receipt graph_after_sha256')
        need(roots == applied.get('roots_after'), 'Live roots differ from the apply receipt roots_after')
    if post:
        checks.run('graph_matches_apply_receipt', c_apply_graph)
    else:
        checks.skip('graph_matches_apply_receipt', 'baseline phase')

    def c_old_graph(info):
        need(len(ref_nodes) == base_exp['node_count'], 'Reference node count differs from spec')
        ref_digest = h.digest(ref_nodes)
        info['reference_digest'] = ref_digest
        need(ref_digest == reference.get('graph_sha256') == base_exp['graph_sha256_r030'], 'Reference digest mismatch')
        missing = sorted(set(ref_nodes) - set(rows))
        changed = sorted(q for q in ref_nodes if q in rows and rows[q] != ref_nodes[q])
        info.update(missing=missing[:50], changed=changed[:50], missing_count=len(missing), changed_count=len(changed))
        info['old_rows_digest'] = h.digest({q: rows[q] for q in ref_nodes if q in rows})
        info['connected_edges'] = sum(1 for r in rows.values() for e in r['edges'].values() if e['source'])
        info['root_layer_pins_connected'] = sum(1 for k in ('color', 'normal', 'roughness')
                                                for n, e in rows.get(ref_roots[k], {'edges': {}})['edges'].items()
                                                if n.startswith('Layer ') and e['source'])
        info['added_count'] = len(added)
        need(info['connected_edges'] > 0, 'Vacuous edge dump (input helpers returned nothing)')
        need(not missing and not changed, 'Pre-S1 node rows missing/changed')
        need(info['old_rows_digest'] == base_exp['graph_sha256_r030'], 'Old-row digest differs from r030')
        need(info['root_layer_pins_connected'] == base_exp['root_layer_pins_connected'], 'Root Layer pin count differs')
        need(G['settings'] == reference['material_settings'], 'Material settings differ')
        if phase == 'baseline':
            need(not added, 'Baseline already contains added nodes')
    if not checks.run('old_graph_identity', c_old_graph):
        R['graph']['all_rows_for_rebaseline'] = rows

    def c_reach(info):
        starts = [q for q in ref_roots.values() if q] + grass_ref
        ref_set, cur_set = bfs(ref_nodes, starts), bfs(rows, starts)
        info.update(reference=len(ref_set), current=len(cur_set))
        need(len(ref_set) == base_exp['reachable_any_root_plus_grass'], 'Reference reachable count differs from spec')
        need(cur_set == ref_set, 'Reachable set from old roots + Grass changed')
        if post:
            sw = exp['static_switch_nodes']
            fsrc = []
            for mp in sw['roots']:
                row = rows.get(roots.get(prop_key.get(mp)), {})
                if row.get('class') == SWITCH_CLASS:
                    fsrc.append(row['edges'][pin(row, 'false', (exp.get('switch_pins') or {}).get('false'))]['source'])
            other = [roots[k] for k in roots if k not in {prop_key[m] for m in sw['roots']}]
            false_set = bfs(rows, fsrc + other + grass_ref)
            info['false_path'] = len(false_set)
            need(false_set == ref_set, 'False-path (Iran) reachable set differs from baseline')
    checks.run('reachability_iran_path', c_reach)

    def c_roots(info):
        info['roots'] = roots
        if not post:
            need(roots == ref_roots, 'Roots differ from reference')
            need(switch_name not in G['switch_names'], 'S1 switch already present at baseline')
            return
        sw, pins = exp['static_switch_nodes'], exp.get('switch_pins') or {}
        handled = set()
        for mp, short in zip(sw['roots'], sw['False_pin_sources']):
            key = prop_key[mp]
            handled.add(key)
            need(ref_roots[key].endswith(':MaterialExpression' + short), 'Spec False source is not the old root: ' + mp)
            row = rows.get(roots[key], {})
            need(row.get('class') == SWITCH_CLASS, 'Root is not a StaticSwitchParameter: ' + key)
            need(row['properties'].get('parameter_name') == switch_name, 'Root switch name differs: ' + key)
            need(row['properties'].get('default_value') is False, 'Root switch default is not False: ' + key)
            fpin, tpin = pin(row, 'false', pins.get('false')), pin(row, 'true', pins.get('true'))
            info[key] = {'node': roots[key], 'input_names': row['input_names'], 'false': row['edges'][fpin],
                         'true': row['edges'][tpin]}
            need(row['edges'][fpin]['source'] == ref_roots[key], 'False pin is not the old root: ' + key)
            need(row['edges'][tpin]['source'] in added, 'True pin is not an added S1 node: ' + key)
        for key in roots:
            if key not in handled:
                need(roots[key] == ref_roots[key], 'Unexpected root change: ' + key)
        nodes = [q for q, r in rows.items() if r['class'] == SWITCH_CLASS
                 and r['properties'].get('parameter_name') == switch_name]
        info['switch_nodes'] = nodes
        need(len(nodes) == sw['count'] and set(nodes) <= set(added), 'Switch node count differs')
        need(switch_name in G['switch_names'], 'Switch not reported by get_static_switch_parameter_names')
        need(LIB.get_material_default_static_switch_parameter_value(master, switch_name) is False,
             'Master static switch default is not False')
        if baseline is not None:
            need(set(G['switch_names']) == set(baseline['graph']['static_switch_names']) | {switch_name},
                 'Static switch name set differs from baseline + S1 switch')
    checks.run('roots_and_switch', c_roots)

    def c_added(info):
        prefix, canvas = exp['node_desc_prefix'], exp.get('canvas')
        info['by_class'] = dict(Counter(rows[q]['class'] for q in added))
        bad_prefix, grass_like, bad_canvas = [], [], []
        for q in added:
            props = rows[q]['properties']
            desc = str(props.get('desc') or '')
            if not desc.startswith(prefix):
                bad_prefix.append(q)
            if desc.startswith(lw.OWNER):
                grass_like.append(q)
            if canvas:
                x, y = props.get('material_expression_editor_x'), props.get('material_expression_editor_y')
                if x is None or y is None or not canvas['x'][0] <= x <= canvas['x'][1] or y < canvas['y_min']:
                    bad_canvas.append([q, x, y])
        info.update(bad_prefix=bad_prefix[:30], grass_prefix=grass_like, bad_canvas=bad_canvas[:30])
        need(not grass_like, 'Added node desc starts with the Grass owner prefix (LW:278,323)')
        need(not bad_prefix, 'Added node without S1 desc prefix')
        need(not bad_canvas, 'Added node outside the S1 canvas')
        if exp.get('added_node_count') is not None:
            need(len(added) == int(exp['added_node_count']), 'Added node count differs: %d' % len(added))
    if post:
        checks.run('added_nodes_prefix_canvas', c_added)
    else:
        checks.skip('added_nodes_prefix_canvas', 'baseline')

    def material_default(kind, name):
        if kind == 'scalar':
            return float(LIB.get_material_default_scalar_parameter_value(master, name))
        if kind == 'vector':
            return h.plain(LIB.get_material_default_vector_parameter_value(master, name))
        if kind == 'static_switch':
            return bool(LIB.get_material_default_static_switch_parameter_value(master, name))
        return h.path(LIB.get_material_default_texture_parameter_value(master, name))

    def c_params(info):
        info['mw_parameters'] = [n for n in G['param_names'] if n.startswith('MW_')]
        need(not info['mw_parameters'], 'MW_ parameters present in the shared master')
        if not post:
            info['present'] = sorted(set(spec_params) & set(G['param_names']))
            need(not info['present'], 'S1 parameter names already exist at baseline')
            return
        nodes = {}
        for q in added:
            r = rows[q]
            if 'parameter_name' in r['properties'] and r['class'] not in LAYER_CLASSES:
                nodes.setdefault(r['properties']['parameter_name'], []).append(q)
        old = {r['properties']['parameter_name'] for r in ref_nodes.values()
               if 'parameter_name' in r['properties'] and r['class'] not in LAYER_CLASSES}
        info.update(added_names=sorted(nodes), missing=sorted(set(spec_params) - set(nodes)),
                    unexpected=sorted(set(nodes) - set(spec_params)), collisions=sorted(set(nodes) & old))
        need(set(nodes) == set(spec_params), 'Added parameter set differs from spec')
        need(not info['collisions'], 'S1 parameter collides with an existing name')
        problems = []
        for name, entry in spec_params.items():
            kind = entry['kind']
            for q in nodes[name]:
                props = rows[q]['properties']
                if rows[q]['class'] != KIND_CLASS[kind]:
                    problems.append([name, q, 'class', rows[q]['class']])
                default = props.get('texture') if kind.startswith('texture') else props.get('default_value')
                if not same(kind, default, entry['master_default']):
                    problems.append([name, q, 'node_default', default])
                if kind in KIND_SAMPLER and enum_name(props.get('sampler_type')) != KIND_SAMPLER[kind]:
                    problems.append([name, q, 'sampler_type', props.get('sampler_type')])
                if kind.startswith('texture') and vendor(default):
                    problems.append([name, q, 'vendor_default', default])
            effective = material_default(kind, name)
            if not same(kind, effective, entry['master_default']):
                problems.append([name, 'material_default', effective])
            if kind != 'static_switch' and len(nodes[name]) != 1:
                problems.append([name, 'node_count', len(nodes[name])])
        info['problems'] = problems
        need(not problems, 'S1 parameter node/default/sampler problems')
    checks.run('parameters_and_defaults', c_params)

    def c_layer_samples(info):
        found = sorted(rows[q]['properties'].get('parameter_name') for q in added
                       if rows[q]['class'] == 'MaterialExpressionLandscapeLayerSample')
        info['added_layer_samples'] = found
        need(found == sorted(exp.get('new_landscape_layer_samples', [])), 'Added LandscapeLayerSample set differs')
        need(set(found) <= set(lw.TARGETS.values()), 'Layer sample outside the 4 painted targets (LW:18-19)')
    if post:
        checks.run('layer_samples', c_layer_samples)
    else:
        checks.skip('layer_samples', 'baseline phase')

    def c_llbs(info):
        spec = exp.get('new_llbs') or {'count': 0}
        llbs = sorted(q for q in added if rows[q]['class'] == 'MaterialExpressionLandscapeLayerBlend')
        info['nodes'] = llbs
        need(len(llbs) == int(spec.get('count', 0)), 'Added LandscapeLayerBlend count differs')
        patterns, heights = spec.get('pins', ['Layer <name>', 'Height <name>']), []
        for q in llbs:
            r = rows[q]
            info[q] = {'layers': r['layers'], 'input_names': r['input_names']}
            need([x['layer_name'] for x in r['layers']] == spec['layers'], 'LLB layer names/order differ')
            need(all(enum_name(x['blend_type']) == spec['blend_type'] for x in r['layers']), 'LLB blend type differs')
            for x in r['layers']:
                weight = (spec.get('preview_weight') or {}).get(x['layer_name'])
                need(weight is None or f32(weight) == f32(x['preview_weight']), 'LLB preview weight differs')
            pins = sorted(pat.replace('<name>', n) for n in spec['layers'] for pat in patterns)
            need(sorted(r['input_names']) == pins, 'LLB pin names differ from spec patterns')
            need(all(r['edges'][n]['source'] for n in r['input_names']), 'LLB has an unconnected pin')
            heights.append(tuple((n, r['edges'][n]['source'], r['edges'][n]['output'])
                                 for n in sorted(r['input_names']) if n.startswith('Height')))
        if spec.get('height_sources_identical_on_all_three') and heights:
            need(len(set(heights)) == 1, 'Height sources differ between the new LLBs')
    if post:
        checks.run('height_blend_llbs', c_llbs)
    else:
        checks.skip('height_blend_llbs', 'baseline phase')

    # ---------- material functions ----------
    MF = {}

    def c_functions(info):
        for package in mfs:
            name = package.rsplit('/', 1)[1]
            if not post:
                need(unreal.find_object(None, package + '.' + name) is None, 'S1 function already loaded: ' + name)
                continue
            asset = unreal.load_asset(package)
            need(isinstance(asset, unreal.MaterialFunction), 'S1 function unavailable: ' + package)
            frows = {h.path(e): fdescribe(h, asset, e) for e in LIB.get_material_function_expressions(asset)}
            spec = (exp.get('functions') or {}).get(name, {})
            samples = [q for q, r in frows.items() if 'TextureSample' in r['class']]
            row = {'node_count': len(frows),
                   'parameters': [q for q, r in frows.items() if 'Parameter' in r['class']],
                   'texture_samples': len(samples),
                   'sampler_sources': sorted({enum_name(frows[q]['properties'].get('sampler_source')) for q in samples}),
                   'sampler_types': sorted({enum_name(frows[q]['properties'].get('sampler_type')) for q in samples}),
                   'inputs': sorted(str(r['properties'].get('input_name')) for r in frows.values()
                                    if r['class'] == 'MaterialExpressionFunctionInput'),
                   'outputs': sorted(str(r['properties'].get('output_name')) for r in frows.values()
                                     if r['class'] == 'MaterialExpressionFunctionOutput'),
                   'calls': sorted({norm(r['properties'].get('material_function')) for r in frows.values()
                                    if r['class'] == 'MaterialExpressionMaterialFunctionCall'}),
                   'pixel_normal_nodes': [q for q, r in frows.items() if r['class'] in FORBIDDEN_NORMAL],
                   'vendor_refs': sorted({str(v) for r in frows.values() for k, v in r['properties'].items()
                                          if k in ('texture', 'material_function') and vendor(v)}),
                   'edge_count_mismatch': [q for q, r in frows.items() if '_count_mismatch' in r['edges']],
                   'rows': frows}
            MF[package] = row
            info[name] = {k: v for k, v in row.items() if k != 'rows'}
            need(not row['parameters'], 'Parameter expressions inside S1 function: ' + name)
            need(not row['vendor_refs'], 'Vendor reference inside S1 function: ' + name)
            need(not row['calls'], 'MaterialFunctionCall inside S1 function (edit check_function :879): ' + name)
            need(not row['edge_count_mismatch'], 'Function input readback mismatch: ' + name)
            if 'texture_samples' in spec:
                need(row['texture_samples'] == spec['texture_samples'], 'Function sample count differs: ' + name)
            if samples:
                allowed = set(exp.get('allowed_sampler_sources') or DEFAULT_SOURCES)
                need(set(row['sampler_sources']) <= allowed, 'Function sample not Shared:Wrap/Clamp: ' + name)
                if spec.get('sampler_source'):
                    need(row['sampler_sources'] == [enum_name(spec['sampler_source'])], 'Function sampler source differs')
                if spec.get('sampler_type'):
                    need(row['sampler_types'] == [enum_name(spec['sampler_type'])], 'Function sampler type differs')
            for key in ('inputs', 'outputs'):
                if key in spec:
                    need(row[key] == sorted(x.split(':')[0] for x in spec[key]), 'Function %s differ: %s' % (key, name))
    if mfs:
        checks.run('material_functions', c_functions)
    else:
        checks.skip('material_functions', 'inline design: expectations list no S1 function packages')
    R['functions'] = {k: v for k, v in MF.items()}

    def c_samplers(info):
        census = Counter('%s|%s|%s' % (r['class'], enum_name(r['properties'].get('sampler_source')),
                                       enum_name(r['properties'].get('sampler_type')))
                         for r in rows.values() if 'TextureSample' in r['class'])
        info['census_all'] = dict(census)
        info['vendor_refs'] = sorted({q for q, r in rows.items() for k, v in r['properties'].items()
                                      if k in ('texture', 'material_function') and vendor(v)})
        need(not info['vendor_refs'], 'Vendor texture/function referenced by the shared master')
        if not post:
            return
        allowed = set(exp.get('allowed_sampler_sources') or DEFAULT_SOURCES)
        samples = [q for q in added if 'TextureSample' in rows[q]['class']]
        bad_source = [q for q in samples if enum_name(rows[q]['properties'].get('sampler_source')) not in allowed]
        mismatch = []
        for q in samples:
            tex = rows[q]['edges'].get('Tex', {}).get('source')
            if tex in rows and 'sampler_type' in rows[tex]['properties']:
                if enum_name(rows[tex]['properties']['sampler_type']) != enum_name(rows[q]['properties'].get('sampler_type')):
                    mismatch.append(q)
        calls = {q: norm(rows[q]['properties'].get('material_function')) for q in added
                 if rows[q]['class'] == 'MaterialExpressionMaterialFunctionCall'}
        bad_calls = sorted(q for q, f in calls.items() if f not in mfs)
        effective = len(samples) + sum(MF.get(f, {}).get('texture_samples', 0) for f in calls.values())
        info.update(direct_samples=len(samples), function_calls=calls, effective_new_samples=effective,
                    bad_source=bad_source, type_mismatch=mismatch, bad_calls=bad_calls)
        need(not bad_source, 'Added sample not Shared:Wrap/Clamp (new sampler state)')
        need(not mismatch, 'Added sample sampler_type differs from its texture object parameter')
        need(not bad_calls, 'Added function call outside the S1 function list (vendor/WorldAligned/other)')
        expected = (exp.get('sampler_estimate') or {}).get('new_samples')
        if expected is not None:
            need(effective == int(expected), 'Effective new sample count %d differs from spec' % effective)
    checks.run('samplers_and_function_calls', c_samplers)

    def c_pixel_normal(info):
        sw, pins = exp['static_switch_nodes'], exp.get('switch_pins') or {}
        starts = []
        row = rows.get(roots.get('normal'), {})
        if row.get('class') == SWITCH_CLASS:
            starts.append(row['edges'][pin(row, 'true', pins.get('true'))]['source'])
        for q in added:
            if rows[q]['class'] == 'MaterialExpressionLandscapeLayerBlend':
                starts += [e['source'] for n, e in rows[q]['edges'].items() if n.startswith('Height')]
        seen = bfs(rows, starts)
        funcs = sorted({norm(rows[q]['properties'].get('material_function')) for q in seen
                        if rows[q]['class'] == 'MaterialExpressionMaterialFunctionCall'})
        info.update(upstream_nodes=len(seen), direct=[q for q in seen if rows[q]['class'] in FORBIDDEN_NORMAL],
                    s1_functions_with_pixel_normal=[f for f in funcs if MF.get(f, {}).get('pixel_normal_nodes')],
                    unexamined_function_calls=[f for f in funcs if f not in MF])
        need(not info['direct'], 'PixelNormalWS upstream of Normal True input or a Height pin')
        need(not info['s1_functions_with_pixel_normal'], 'S1 function upstream of Normal/Height uses PixelNormalWS')
    if post:
        checks.run('no_pixel_normal_in_normal_or_height', c_pixel_normal)
    else:
        checks.skip('no_pixel_normal_in_normal_or_height', 'baseline phase')

    # ---------- Grass contract (LW:321-344) + types (LW:236-240, 275, 423-424) ----------
    def c_grass(info):
        objects = G['objects']
        outputs = [e for e in objects.values() if isinstance(e, unreal.MaterialExpressionLandscapeGrassOutput)]
        owned = [e for e in objects.values() if str(e.get_editor_property('desc')).startswith(lw.OWNER)]
        info.update(grass_outputs=len(outputs), owned_nodes=len(owned))
        need(len(outputs) == 1, 'Exactly one LandscapeGrassOutput required (LW:321)')
        need(len(owned) == 4, 'Exactly four owned Grass nodes required (LW:323)')
        by = {}
        for label_, cls in (('Ground', unreal.MaterialExpressionLandscapeLayerSample),
                            ('Density', unreal.MaterialExpressionScalarParameter),
                            ('GroundDensity', unreal.MaterialExpressionMultiply),
                            ('Output', unreal.MaterialExpressionLandscapeGrassOutput)):
            hits = [e for e in owned if str(e.get_editor_property('desc')) == lw.OWNER + ':' + label_]
            need(len(hits) == 1 and isinstance(hits[0], cls), 'Owned Grass node missing/ambiguous: ' + label_)
            by[label_] = hits[0]
        need(str(by['Ground'].get_editor_property('parameter_name')) == lw.TARGETS['Ground'], 'Grass layer differs (LW:329)')
        need(str(by['Density'].get_editor_property('parameter_name')) == GRASS_COVERAGE, 'Coverage parameter differs')
        need(float(by['Density'].get_editor_property('default_value')) == 0.0, 'Coverage default not 0.0 (LW:344)')
        need(isinstance(grass, unreal.LandscapeGrassType), 'Grass type unavailable')
        need(str(unreal.EditorAssetLibrary.get_metadata_tag(grass, 'GeoCityOwner')) == lw.OWNER, 'Grass type owner differs')
        inputs = list(by['Output'].get_editor_property('grass_types'))
        need(len(inputs) == 1 and inputs[0].get_editor_property('grass_type') == grass
             and str(inputs[0].get_editor_property('name')) == 'GeoCityGroundGrass', 'GrassInput binding differs (LW:325-327)')
        edges = {label_: dict((n, h.path(s)) for n, s in h.inputs(master, by[label_])) for label_ in ('GroundDensity', 'Output')}
        info['edges'] = edges
        need(edges['GroundDensity'].get('A') == h.path(by['Ground']) and edges['GroundDensity'].get('B') == h.path(by['Density']),
             'GroundDensity inputs differ (LW:346-347)')
        need(edges['Output'].get('GeoCityGroundGrass') == h.path(by['GroundDensity']), 'Grass output input differs (LW:347)')
        graph_rows = {q: rows[q] for q in reference['grass']['graph'] if q in rows}
        need(graph_rows == reference['grass']['graph'], 'Grass subgraph rows differ from reference')
        settings = h.grass_settings(grass)
        need(settings == reference['grass']['settings'], 'Grass type settings differ from reference')
        config = lw._config(profiles[area])
        need(lw._read_varieties(grass) == lw._expected_varieties(profiles[area], config),
             'Grass varieties differ from the profile contract (LW:423-424)')
        info['settings'] = settings
    checks.run('grass_contract', c_grass)

    # ---------- instance states: OFF in base (Iran), ON in Gaza children ----------
    S = {}

    def c_states(info):
        instances = [base] + [children[a] for a in exp['children']]
        for inst in instances:
            state = h.material_state(master, inst)
            state['static_switches'] = {n: bool(LIB.get_material_instance_static_switch_parameter_value(inst, n))
                                        for n in G['switch_names']}
            for key in ('static_parameters_runtime', 'static_parameters'):
                try:
                    inst.get_editor_property(key)
                    state[key + '_readable'] = True
                except Exception as error:
                    state[key + '_readable'] = 'NOT_EXPOSED: ' + str(error)[:160]
            S[h.path(inst)] = state
        info['instances'] = sorted(S)
    states_ok = checks.run('instance_state_snapshot', c_states)
    R['instances'] = S
    base_key = h.path(base) if base else None
    child_key = {a: h.path(c) for a, c in children.items()}

    def overrides_for(a):
        block = exp.get('existing_param_child_overrides') or {}
        result = dict(block.get('both_children') or {})
        result.update((block.get('per_area') or {}).get(a) or {})
        return result

    def c_effective(info):
        state = S[base_key]
        problems = []
        for name, entry in spec_params.items():
            field = KIND_STATE[entry['kind']]
            if not post:
                continue
            if not same(entry['kind'], state[field].get(name), entry['master_default']):
                problems.append(['base', name, state[field].get(name), entry['master_default']])
        base_overrides = sorted({r['name'] for k in ('scalar', 'vector', 'texture') for r in state[k + '_overrides']}
                                & set(spec_params))
        info['base_s1_overrides'] = base_overrides
        if post:
            need(state['static_switches'].get(switch_name) is False, 'Base MI (Iran) switch is not False')
        for a, key in child_key.items():
            cstate = S[key]
            if post and a not in scope:
                # Out-of-scope Gaza child (not saved by S1): switch False, S1 values inherited from the master.
                need(cstate['static_switches'].get(switch_name) is False, 'Out-of-scope Gaza child switch is not False: ' + a)
                for name, entry in spec_params.items():
                    field = KIND_STATE[entry['kind']]
                    if not same(entry['kind'], cstate[field].get(name), entry['master_default']):
                        problems.append([a, 'out_of_scope', name, cstate[field].get(name), entry['master_default']])
            elif post:
                need(cstate['static_switches'].get(switch_name) is True, 'Gaza child switch is not True: ' + a)
                for name, entry in spec_params.items():
                    field = KIND_STATE[entry['kind']]
                    if not same(entry['kind'], cstate[field].get(name), entry[a]):
                        problems.append([a, name, cstate[field].get(name), entry[a]])
                for name, value in overrides_for(a).items():
                    kind = kind_of(value)
                    if not same(kind, cstate[KIND_STATE[kind]].get(name), value):
                        problems.append([a, name, cstate[KIND_STATE[kind]].get(name), value])
            coverage = (args.get('expected_grass_coverage') or {}).get(a)
            actual = cstate['scalars'].get(GRASS_COVERAGE)
            info['coverage_' + a] = actual
            if coverage is not None and (actual is None or abs(actual - float(coverage)) >= 1e-4):
                problems.append([a, GRASS_COVERAGE, actual, coverage])
        info['base_coverage'] = state['scalars'].get(GRASS_COVERAGE)
        if state['scalars'].get(GRASS_COVERAGE) != 0.0:
            problems.append(['base', GRASS_COVERAGE, state['scalars'].get(GRASS_COVERAGE), 0.0])
        info['problems'] = problems
        need(not base_overrides, 'Base MI (Iran) overrides an S1 parameter')
        need(not problems, 'Effective parameter values differ (base neutral / Gaza ON)')
    if states_ok:
        checks.run('effective_values_off_base_on_children', c_effective)
    else:
        checks.not_run('effective_values_off_base_on_children', 'instance_state_snapshot failed')

    def c_unchanged(info):
        association = h.plain(unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
        problems = []
        for key, prior in baseline['instances'].items():
            live = S.get(key)
            if live is None:
                problems.append([key, 'missing'])
                continue
            area_ = next((a for a, k in child_key.items() if k == key), None)
            in_scope = area_ in scope  # base MI and an out-of-scope child: nothing may change
            allowed = set(spec_params) if in_scope else set()
            if in_scope:
                allowed |= set(overrides_for(area_))
                if area_ in (args.get('expected_grass_coverage') or {}):
                    allowed.add(GRASS_COVERAGE)
            if live['parent'] != prior['parent']:
                problems.append([key, 'parent'])
            for field in ('scalars', 'vectors', 'textures'):
                for name, value in prior[field].items():
                    if name not in allowed and live[field].get(name) != value:
                        problems.append([key, name, value, live[field].get(name)])
            for kind in ('scalar', 'vector', 'texture'):
                field = kind + '_overrides'
                if [r for r in live[field] if r['name'] not in allowed] != [r for r in prior[field] if r['name'] not in allowed]:
                    problems.append([key, field, 'unlisted override changed'])
                bad = [r['name'] for r in live[field] if r['name'] in allowed
                       and (r['association'] != association or r['index'] != -1)]
                if bad:
                    problems.append([key, field, 'non-global override', bad])
            for name, value in prior.get('static_switches', {}).items():
                if live['static_switches'].get(name) != value:
                    problems.append([key, 'static_switch', name])
        info['problems'] = problems[:80]
        need(not problems, 'Instance values outside the S1 change set differ from baseline')
    if not post:
        checks.skip('instances_unchanged_outside_s1', 'baseline phase')
    elif states_ok:
        checks.run('instances_unchanged_outside_s1', c_unchanged)
    else:
        checks.not_run('instances_unchanged_outside_s1', 'instance_state_snapshot failed')

    # ---------- profile normal pins: the verdict prepare()/verify_landscape() would reach (LW:110-121) ----------
    for a in GAZA:
        def c_pins(info, a=a):
            info['profile'] = files['profile:' + a]['file']
            info['bindings'] = lw._verify_textures(profiles[a], children[a])
        checks.run('profile_normal_pins:' + a, c_pins)

    def c_iran_pins(info):
        info['bindings'] = lw._verify_textures(profiles['Iran'], base)
    checks.run('profile_normal_pins:Iran_base', c_iran_pins)

    # ---------- texture bindings resolve + sampler compatibility ----------
    T = {}

    def c_textures(info):
        live = bfs(rows, [q for q in roots.values() if q] + grass_ref)
        sampler = {}
        for q in live:
            r = rows[q]
            if 'parameter_name' in r['properties'] and 'sampler_type' in r['properties']:
                sampler.setdefault(r['properties']['parameter_name'], set()).add(enum_name(r['properties']['sampler_type']))
        unresolved, missing_files, vendor_base = [], [], []
        paths = sorted({v for st in S.values() for v in st['textures'].values() if v})
        for key, st in S.items():
            unresolved += [[key, n] for n, v in st['textures'].items() if not v]
        vendor_base = sorted(v for v in S[base_key]['textures'].values() if vendor(v))
        defaults = {n: h.path(LIB.get_material_default_texture_parameter_value(master, n))
                    for n in LIB.get_texture_parameter_names(master)}
        vendor_defaults = sorted(n for n, v in defaults.items() if vendor(v))
        for v in paths:
            if v.startswith('/Game/'):
                file = root / 'Content' / (norm(v)[len('/Game/'):] + '.uasset')
                if not file.exists():
                    missing_files.append(v)
        gate = set(spec_params)
        for a in exp['children']:
            gate |= set(overrides_for(a))
        detail_paths = sorted({S[k]['textures'].get(n) for k in S for n in gate if S[k]['textures'].get(n)}
                              | {v for a in exp['children'] for n, v in S[child_key[a]]['textures'].items()
                                 if v and v != S[base_key]['textures'].get(n)})
        for v in detail_paths:
            obj = unreal.load_asset(v)
            try:
                T[v] = p.texture_details(h, obj)
            except Exception as error:
                T[v] = {'path': v, 'class': obj.get_class().get_name() if obj else None, 'error': str(error)}
        mismatches, ambiguous, informational = [], [], []
        for key, st in S.items():
            for n, v in st['textures'].items():
                if not v or v not in T or n not in sampler:
                    continue
                if len(sampler[n]) != 1:
                    ambiguous.append([n, sorted(sampler[n])])
                    continue
                derived = derived_sampler(T[v].get('properties', {}))
                want = next(iter(sampler[n]))
                if derived is not None and derived != want:
                    (mismatches if n in gate else informational).append([key, n, v, want, derived])
        info.update(texture_count=len(paths), unresolved=unresolved, missing_files=missing_files,
                    vendor_in_base=vendor_base, vendor_master_defaults=vendor_defaults,
                    sampler_mismatch_gated=mismatches, sampler_mismatch_existing_info=informational,
                    ambiguous_sampler_types=ambiguous, derivation='INFERRED GetSamplerTypeForTexture mirror')
        need(not unresolved, 'Unresolved texture parameter binding')
        need(not missing_files, 'Bound texture package file missing')
        need(not vendor_base and not vendor_defaults, 'Base MI (Iran) or master default binds a vendor texture')
        need(not mismatches, 'Texture compression/sRGB/VT inconsistent with the consuming sampler type')
    if states_ok:
        checks.run('texture_bindings_and_samplers', c_textures)
    else:
        checks.not_run('texture_bindings_and_samplers', 'instance_state_snapshot failed')
    R['texture_details'] = T

    # ---------- registry dependencies ----------
    deps = {}

    def c_deps(info):
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,
                                                        include_hard_package_references=True)
        for package in [norm(lw.MASTER), norm(lw.BASE)] + [norm(c) for c in exp['children'].values()] + (mfs if post else []):
            deps[package] = sorted(str(x) for x in (registry.get_dependencies(package, options) or []))
        info['vendor'] = {k: [d for d in v if vendor(d + '/')] for k, v in deps.items()}
        for package in [norm(lw.MASTER), norm(lw.BASE)] + (mfs if post else []):
            need(not info['vendor'][package], 'Shared package depends on a vendor pack: ' + package)
        if post and baseline is not None:
            prior = set(baseline['registry_dependencies'][norm(lw.MASTER)])
            added_deps = sorted(d for d in set(deps[norm(lw.MASTER)]) - prior if d.startswith(('/Game/', '/Engine/')))
            allowed = set(mfs) | {norm(x) for x in exp.get('allowed_new_master_dependencies', [])}
            info['master_added_dependencies'] = added_deps
            need(set(added_deps) <= allowed, 'Master gained unexpected /Game or /Engine dependencies')
            base_prior = set(baseline['registry_dependencies'][norm(lw.BASE)])
            need(set(deps[norm(lw.BASE)]) == base_prior, 'Base MI dependencies changed')
    checks.run('registry_dependencies', c_deps)
    R['registry_dependencies'] = deps

    # ---------- current-world Landscapes (+ INFERRED G1 proxy evidence) ----------
    def c_landscapes(info):
        proxies = [a for a in actors if isinstance(a, unreal.LandscapeProxy)]
        need(proxies, 'No Landscape in the open world')
        rows_ = []
        for actor in proxies:
            row = {'actor': h.path(actor), 'material': h.path(actor.get_editor_property('landscape_material'))}
            getter = getattr(actor, 'get_target_layer_names', None)
            row['layers'] = sorted(str(n) for n in getter()) if callable(getter) else 'API_NOT_EXPOSED'
            comps = list(actor.get_components_by_class(unreal.LandscapeComponent))
            row['components'] = len(comps)
            row['component_material0'] = dict(Counter(h.path(c.get_material(0)) for c in comps))
            evidence = {}
            if comps:
                try:
                    mics = list(comps[0].get_editor_property('material_instances'))
                    evidence['first_component_mics'] = []
                    for mic in mics:
                        chain, cur = [], mic
                        for _ in range(6):
                            if cur is None or not isinstance(cur, unreal.MaterialInstance):
                                break
                            chain.append(h.path(cur))
                            cur = cur.get_editor_property('parent')
                        entry = {'mic': h.path(mic), 'chain': chain}
                        if post and isinstance(mic, unreal.MaterialInstanceConstant):
                            entry['switch'] = bool(LIB.get_material_instance_static_switch_parameter_value(mic, switch_name))
                        evidence['first_component_mics'].append(entry)
                except Exception as error:
                    evidence['material_instances'] = 'NOT_EXPOSED: ' + str(error)[:160]
            row['g1_proxy_evidence_INFERRED'] = evidence
            rows_.append(row)
        info['landscapes'] = rows_
        for row in rows_:
            need(row['material'] == child_key[area], 'Landscape does not use this area child: ' + row['actor'])
            if row['layers'] != 'API_NOT_EXPOSED':
                need(set(row['layers']) == set(lw.TARGETS.values()), 'Target layers differ (LW:425-428)')
        if args.get('expected_landscape_count') is not None:
            need(len(rows_) == int(args['expected_landscape_count']), 'Landscape count differs: %d' % len(rows_))
    checks.run('landscapes_in_world', c_landscapes)

    # ---------- statistics (G4 evidence; transient preview compile, no package write) ----------
    stats = {}

    def c_stats(info):
        want = base_exp.get('master_and_children_preview_stats_PID10460')
        need(want, 'baseline_expectations lacks master_and_children_preview_stats_PID10460 (no vacuous pass)')
        targets = [master, base] + ([children[a] for a in exp['children']] if args.get('statistics_children') else [])
        for target in targets:
            stats[h.path(target)] = statistics(h, target)
        info.update(stats)
        for target in (master, base):
            row = stats[h.path(target)]
            got = {'vs': row.get('num_vertex_shader_instructions'), 'ps': row.get('num_pixel_shader_instructions'),
                   'samplers': row.get('num_samplers'), 'ps_samples': row.get('num_pixel_texture_samples')}
            need(got == want, 'Preview statistics differ from baseline for ' + h.path(target) + ': ' + str(got))
    checks.run('iran_statistics_equal', c_stats)
    R['statistics'] = stats

    # ---------- compile log slice ----------
    def c_log(info):
        log = root / 'Saved/Logs/Environmentpipeline.log'
        info['log'] = str(log)
        need(log.exists(), 'Editor log missing')
        lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
        names = ['M_SurfaceBank_Natural', 'MI_SurfaceBank_Natural', 'MI_GeoCityGround'] + [m.rsplit('/', 1)[1] for m in mfs]
        pattern = re.compile(r'error|failed to compile|default material will be used|exceeds', re.I)
        hits = [i for i, line in enumerate(lines) if any(n in line for n in names) and pattern.search(line)]
        info.update(first_line=lines[0][:200] if lines else None, line_count=len(lines),
                    hits=[lines[j][:400] for i in hits[:20] for j in range(i, min(i + 6, len(lines)))])
        need(not hits, 'Compile/fallback errors naming S1 materials in this session log')
    checks.run('compile_log_errors', c_log)

    try:
        R['cvars'] = {n: unreal.SystemLibrary.get_console_variable_string_value(n) for n in p.CVARS}
    except Exception as error:
        R['cvars'] = {'error': '%s: %s' % (type(error).__name__, error)}
    return finish(run)


def finish(run, aborted=None):
    """Closing gates, verdict and receipt; aborted names the early gate that stopped the run (always FAILED)."""
    R, checks, exp = run.R, run.checks, run.exp
    dirty_after = run.dirty()
    R['dirty_after'] = dirty_after

    def c_dirty_after(info):
        info.update(dirty_after)
        info['protected_dirty'] = sorted(x for x in dirty_after['maps'] + dirty_after['content'] if norm(x) in run.protected)
        need(dirty_after == run.dirty_before, 'Dirty package set changed during verification')
        need(not info['protected_dirty'], 'Master/base/child/S1 function/Grass type/map package dirty after verification')
        need(not any(vendor(x) for x in dirty_after['maps'] + dirty_after['content']), 'Vendor package dirty')
    checks.run('dirty_after_unchanged', c_dirty_after)

    def c_disk_end(info):
        end = disk_snapshot(run.root, run.tracked)
        R['disk_end'] = end
        state = lambda row: (row.get('exists'), row.get('sha256'))
        info['unreadable'] = sorted(k for k in run.disk if run.disk[k].get('error') or end.get(k, {}).get('error'))
        info['changed'] = sorted(k for k in run.disk if state(run.disk[k]) != state(end.get(k, {})))
        need(not info['unreadable'], 'Tracked package file unreadable')
        need(not info['changed'], 'Tracked package changed on disk during the run (another writer?)')
    checks.run('disk_unchanged_during_run', c_disk_end)

    def c_inputs_end(info):
        info['changed'] = sorted(k for k, v in run.files.items() if file_sha(v['file']) != v['sha256'])
        need(not info['changed'], 'Bound input file changed during the run')
    checks.run('inputs_unchanged_during_run', c_inputs_end)

    def c_runtime_end(info):
        import geocity_runtime_guard
        need(geocity_runtime_guard.verify() == R['environment']['runtime_sources'],
             'Sealed runtime sources changed during the run (geocity_runtime_guard.verify)')
    checks.run('runtime_sources_unchanged', c_runtime_end)

    checks.close(REQUIRED[run.phase])
    failed = checks.failed()
    status = FAILED_STATUS if failed or aborted else PASS_STATUS[run.phase]
    result = {'schema': SCHEMA, 'status': status, 'phase': run.phase, 'pid': run.pid, 'world': run.named_map,
              'area': run.area, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'aborted_at': aborted, 'input_files': run.files,
              'switch_name': (exp.get('static_switch_nodes') or {}).get('name'),
              'required_checks': list(REQUIRED[run.phase]), 'waivers': run.waivers,
              'failed_checks': failed, 'accepted_known_failures': checks.accepted_failures(),
              'checks': checks.rows, 'native_mutation': False, 'explicit_save_called': False,
              'explicit_compile_called': False, 'update_material_instance_called': False,
              'get_statistics_called': bool(R.get('statistics')),
              'get_statistics_note': 'transient preview shader compile for statistics; no package write',
              'labels': {
                  'MEASURED': 'every check row, disk hash and readback in this receipt',
                  'INFERRED': 'the r031 reference was dumped at master sha bea25944; the current master was re-saved '
                              'by PID10460 prepare(); old_graph_identity is the first live proof that the live graph '
                              'still equals it'},
              'limitations': [
                  'Per-component Landscape MIC permutations are evidence only (UPROPERTY without BP exposure); '
                  'visible S1 effect needs a locked-exposure Lit capture (G1).',
                  'IsMaterialInstanceParameterOverridden (MaterialEditingLibrary.h:473-474) is not called yet '
                  '(record-only candidate); base disk sha256 is the backstop.',
                  'Sampler compatibility uses an INFERRED mirror of GetSamplerTypeForTexture.',
                  'get_statistics is a preview-pruned native result, not a Landscape sampler budget.',
                  'Function calls upstream of Normal/Height other than S1 functions are not opened (listed).',
                  'No process control: root confirms exactly one UnrealEditor.exe before and after the run.',
                  'MW vault originality (compare_vault.py 109/109) is an offline check, not done here.']}
    result.update(R)
    run.out.parent.mkdir(parents=True, exist_ok=True)
    with run.out.open('x', encoding='utf-8') as stream:  # exclusive create: never overwrite evidence
        stream.write(json.dumps(result, indent=1, default=str))
    return {'ok': status == PASS_STATUS[run.phase], 'status': status, 'receipt': str(run.out),
            'sha256': sha(run.out), 'phase': run.phase, 'area': run.area, 'pid': run.pid, 'aborted_at': aborted,
            'failed_checks': failed, 'accepted_known_failures': checks.accepted_failures(), 'native_mutation': False}


class VerificationNotPassed(RuntimeError):
    """Raised after the receipt is written, so the inline runner reports ok False (copilot_call exit 1)."""


if 'ARGS' in globals():
    RESULT = run_s1_verify(ARGS)
    print(json.dumps(RESULT, default=str))
    if RESULT.get('ok') is not True or RESULT.get('status') != PASS_STATUS.get(RESULT.get('phase')):
        raise VerificationNotPassed('S1 verify %s (receipt %s sha256 %s); failed checks: %s' % (
            RESULT.get('status'), RESULT.get('receipt'), RESULT.get('sha256'), ', '.join(RESULT.get('failed_checks') or [])))
