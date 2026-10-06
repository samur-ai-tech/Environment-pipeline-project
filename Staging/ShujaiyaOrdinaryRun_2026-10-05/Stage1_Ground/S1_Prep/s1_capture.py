"""Stage 1 locked-exposure capture for GazaShujaiya / GazaRimal (phased, in-editor only).

Run each phase through a reviewed, pinned copy of GP/copilot_call.py (run_unreal_skill with ARGS -> RESULT,
GP/copilot_call.py:20-31). Importing this file without ARGS is idle; `import unreal` is lazy so the pure
helpers can be exercised offline.

Why phased: AutomationLibrary.take_high_res_screenshot is asynchronous (the PNG is written on later ticks,
GP/native_capture_epic_resident.py:206-207), and sleeping inside a call freezes the game thread (no frames,
streaming or Lumen accumulation). So the orchestrator calls, all against one CAPTURE_<label>.json:
  begin    guard, record priors (camera/FOV/viewmode/cvars/environment/disk/dirty), apply the transient
           exposure lock (+ optional streaming cvar), create the receipt with open('x').
  prepare  (index) move camera, set the view mode, read back, force residency, record frame + log offset.
           -> orchestrator waits outside the editor (settle).
  request  (index) settle gate (frames + seconds), camera/viewmode/exposure re-check, finish_loading,
           InvestigateTexture residency gate, shader-log gate, render-proof gate (streamer ViewN position must
           equal the eye for every streamed bound texture that has a view record; engine ticks are not redraws),
           then take_high_res_screenshot. Refusals leave the shot PREPARED and are retryable, except that
           STREAMER_VIEW_NOT_AT_CAMERA has no programmatic remedy (root/Aviv must act; do not loop).
           Refuses while any other screenshot of this capture is REQUESTED/REQUESTING or has a live task.
  complete (index) PNG present + complete (IEND) + task done; camera/view mode/exposure/dimensions re-checked
           -> CAPTURED, or CAPTURED_UNQUALIFIED with reasons (incl. RENDER_PROOF_UNAVAILABLE); PENDING otherwise.
  end      restore of every applied cvar (whitelisted names, numeric priors, registry copy preferred), of the
           force_game_view state on the begin viewport key, and of the viewport camera/FOV/view mode; preservation
           checks; log slice. Refuses while any screenshot task of this capture is live (whatever the shot state)
           unless cancel=true; those shots become INVALIDATED_RESTORED_BEFORE_CAPTURE. There is no native cancel
           (MEASURED: UAutomationEditorTask exposes only IsTaskDone/IsValidTask, AutomationBlueprintFunctionLibrary.h:46-51),
           so a late PNG can still land at the shot path: end renames (never deletes/overwrites) every PNG at a
           non-CAPTURED shot path to <stem>.INVALIDATED.png; call end again >= screenshot_delay s later to sweep
           late writes. end tolerates a changed s1_capture.py (recorded as a warning) so the restore is never
           blocked; it still requires the begin PID (cvars are per-process). A run that ended
           ENDED_PRESERVATION_CHECK_FAILED can call end again to retry the cvar/game-view restore.
  status   read-only summary (reports unvalidated PNGs present and live tasks).

Operator rules: run end in the begin PID before any editor exit. Root must not edit or re-pin
S1_Prep/s1_capture.py while a CAPTURE_<label>.json is BEGUN or ACTIVE. Manual fallback if end cannot run in the
begin PID: issue '<name> <prior>' for each receipt applied_cvars row in reverse order (receipt restore_fallback
lists them) and editor_set_game_view(<priors.game_view>, <priors.active_viewport_key>); the cvars are session-only,
so an editor restart also clears them. REGISTRY ('s1_capture_runtime') must never be renamed between script
versions: end reads the applied-cvar rows that begin stored there.

Never: Content/actor/map edits, compile, Cook, Bake, prepare(), saves, ini edits, post-process volume or
show-flag changes. Transient only: console variables (restored in 'end'), viewport camera/FOV/view mode
(restored in 'end'), per-texture SetForceMipLevelsToBeResident (time-limited, no persistent property;
REV/STREAMING_DIAGNOSTIC_REVIEW.json temporary_residency_test). Writes only under S1_Prep:
CAPTURE_<label>.json, CAPTURE_<label>_LOG.txt and images/<label>_<NN>_<shot>.png.
"""
import datetime
import hashlib
import json
import math
import os
import re
import struct
import subprocess
import sys
import time
import types
import uuid
from pathlib import Path

SCHEMA = 'environmentpipeline.s1_capture.v1'
REL_STAGE = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep'
REL_GP = 'Staging/GroundPainting_2026-10-04'
SCRIPT_NAME = 's1_capture.py'
WIDTH, HEIGHT = 1600, 1000                      # GP native_capture_epic_resident.py:192,206
SHOT_NAMES = ('close', 'middle', 'wide')        # GP CAMERAS_<Area>.json keys (:106)
AREA_MAPS = {                                   # GP ASSIGNMENT.json original_maps
    'GazaShujaiya': '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration',
    'GazaRimal': '/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration'}
AREA_CHILD = {a: '/Game/Project/Areas/%s/BankIntegration_v015/Materials/MI_GeoCityGround' % a for a in AREA_MAPS}
SURFACE = '/Game/Project/Shared/SurfacePainting/Appearance_20261003'
MASTER, BASE, GRASS = SURFACE + '/M_SurfaceBank_Natural', SURFACE + '/MI_SurfaceBank_Natural', SURFACE + '/LG_GeoCity_PermittedGroundGrass'
# Live bound set (4 painted layers + macro). GeoCity_S1_* texture parameters are added when present.
BASE_RESIDENCY_PARAMETERS = tuple(l + '_' + c for l in ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')
                                  for c in ('Albedo', 'Normal')) + ('Ground_MacroMask',)
S1_TEXTURE_PREFIX = 'GeoCity_S1_'
S1_SWITCH_CANDIDATES = ('GeoCity_S1_Enable', 'GeoCity_S1_GazaGround')   # D2 / D1 spec names
# 'r.EyeAdaptation.MethodOverride' help (UnrealEditor-Renderer.dll): -2 custom, -1 none, 1 histogram, 2 basic, 3 Manual.
# 'r.ExposureOffset' help (UnrealEditor-Engine.dll): exposure on top of post process settings and eye adaptation.
METHOD_OVERRIDE, EXPOSURE_OFFSET, FULLY_LOAD = 'r.EyeAdaptation.MethodOverride', 'r.ExposureOffset', 'r.Streaming.FullyLoadUsedTextures'
MANUAL_METHOD = 3
RESTORABLE_CVARS = (METHOD_OVERRIDE, EXPOSURE_OFFSET, FULLY_LOAD)      # the only cvars begin may set / end may restore
_CVAR_VALUE = re.compile(r'^-?\d+(\.\d+)?([eE][-+]?\d+)?$')           # numeric priors only (no console injection)
VIEW_TOLERANCE_CM = 1.0
CAPTURED_STATES = ('CAPTURED', 'CAPTURED_UNQUALIFIED')
INVALIDATED = 'INVALIDATED_RESTORED_BEFORE_CAPTURE'
NATIVE_CANCEL = ('NOT_AVAILABLE (MEASURED: UAutomationEditorTask exposes only IsTaskDone/IsValidTask, '
                 'UE_5.8 AutomationBlueprintFunctionLibrary.h:46-51); late PNGs are quarantined by end, never deleted')
RENDER_PROOF_REMEDY = ('NO_PROGRAMMATIC_REMEDY: the streamer has not seen a view at this eye, so the viewport has not '
                       'drawn it (GetFrameCount counts engine ticks, not redraws). The realtime setter is excluded '
                       '(GP Revision_2026-10-05/STREAMING_DIAGNOSTIC_REVIEW.json excluded_next_actions). Do not loop '
                       'request; root/Aviv must make the editor viewport redraw, then retry once.')
RESTORE_PRIORITY_NOTE = ('INFERRED: restore goes through execute_console_command, so each restored cvar is now held at '
                         'SetByConsole priority for the rest of the session; string values equal the priors, the set-by '
                         'priority may not.')
CVARS = {
    'exposure': (METHOD_OVERRIDE, EXPOSURE_OFFSET, 'r.EyeAdaptationQuality', 'r.EyeAdaptation.PreExposureOverride',
                 'r.EyeAdaptation.LensAttenuation', 'r.EyeAdaptation.CachedLightingPreExposure',
                 'r.DefaultFeature.AutoExposure', 'r.DefaultFeature.AutoExposure.Method',
                 'r.DefaultFeature.AutoExposure.Bias', 'r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange',
                 'r.DefaultFeature.LocalExposure.HighlightContrastScale',
                 'r.DefaultFeature.LocalExposure.ShadowContrastScale', 'r.LUT.TonemappingMethod'),
    # Global ShowFlag.<Name> overrides ("ShowFlag.%s" in UnrealEditor-Engine.dll); recorded, never set.
    'showflag_overrides': ('ShowFlag.PostProcessing', 'ShowFlag.EyeAdaptation', 'ShowFlag.Tonemapper',
                           'ShowFlag.LocalExposure', 'ShowFlag.Lighting', 'ShowFlag.Game'),
    'streaming': ('r.TextureStreaming', 'r.Streaming.PoolSize', 'r.Streaming.MipBias', 'r.Streaming.UsePerTextureBias',
                  'r.Streaming.Boost', 'r.Streaming.MaxEffectiveScreenSize', 'r.Streaming.HiddenPrimitiveScale',
                  FULLY_LOAD, 'r.Streaming.UseAllMips', 'r.ScreenPercentage', 'sg.TextureQuality'),  # GP native_streaming_diagnostic.py:41
    'lighting': ('r.DynamicGlobalIlluminationMethod', 'r.ReflectionMethod', 'sg.GlobalIlluminationQuality',
                 'sg.ReflectionQuality', 'sg.ShadowQuality', 'sg.PostProcessQuality', 'r.Substrate')}
TEXTURE_PROPS = ('lod_bias', 'lod_group', 'max_texture_size', 'never_stream', 'global_force_mip_levels_to_be_resident',
                 'num_cinematic_mip_levels', 'virtual_texture_streaming', 'srgb', 'compression_settings')  # GP native_streaming_diagnostic.py:40 (+2)
ENV_CLASSES = ('DirectionalLight', 'SkyLight', 'SkyAtmosphere', 'ExponentialHeightFog', 'VolumetricCloud', 'PostProcessVolume')
PP_FIELDS = ('auto_exposure_method', 'auto_exposure_bias', 'auto_exposure_apply_physical_camera_exposure',
             'auto_exposure_min_brightness', 'auto_exposure_max_brightness', 'camera_iso', 'camera_shutter_speed',
             'depth_of_field_fstop', 'local_exposure_highlight_contrast_scale', 'local_exposure_shadow_contrast_scale')
REGISTRY = 's1_capture_runtime'   # never rename: end of a newer script version reads rows stored here by begin
QUALIFICATION = {
    'exposure_manual_cvar': ('Exposure locked by the process-global transient cvar r.EyeAdaptation.MethodOverride=3 '
                             '(Manual) plus r.ExposureOffset; restored in end. The viewport-only routes (editor viewport '
                             'post-process settings, fixed EV100 ExposureSettings) have no Python setter.'),
    'exposure_auto_recorded': 'EXPOSURE_NOT_LOCKED: auto exposure; images are not luminance-comparable across scenes.',
    'force_bound_textures': ('TEMPORARY_RESIDENCY_DIAGNOSTIC_ONLY (REV/STREAMING_DIAGNOSTIC_REVIEW.json '
                             'temporary_residency_test). Acceptance needs root decision on owned NeverStream copies '
                             'or Aviv viewport review.'),
    'fully_load_cvar': 'TRANSIENT r.Streaming.FullyLoadUsedTextures=1 (root approval required); diagnostic for acceptance.',
    'none': 'DEFAULT_STREAMING: residency only recorded; programmatic-capture blur is a known risk (REV RESULT.txt).'}
BEGIN_KEYS = {'mode', 'expected_pid', 'owner', 'operator_thread_id', 'area', 'label', 'camera_file_sha256', 'shots',
              'viewmode', 'exposure', 'residency', 'min_settle_frames', 'min_settle_seconds', 'screenshot_delay',
              'min_gi_quality', 'allowed_dirty_content', 'require_sole_editor', 'restore_ui', 'log_problem_gate'}
PHASE_KEYS = {'mode', 'expected_pid', 'label', 'index', 'cancel'}


# ----------------------------------------------------------------------------- pure helpers (offline-safe)
def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def safe_token(text, limit=96):
    return isinstance(text, str) and 0 < len(text) <= limit and all(c.isascii() and (c.isalnum() or c == '_') for c in text)


def parse_lease(line):
    """GP native_streaming_diagnostic.py:12 field parsing of the last EDITOR_OWNER.txt line."""
    return dict(t.split('=', 1) for t in line.split() if '=' in t)


def rotation_for(eye, target):
    """GP native_capture_epic_resident.py:158-159 (pitch, yaw, roll=0)."""
    dx, dy, dz = (float(t) - float(e) for e, t in zip(eye, target))
    return [math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx)), 0.0]


def matches(values, expected, tolerance, angular=False):
    """GP native_capture_epic_resident.py:64-68."""
    if len(values) != len(expected):
        return False
    deltas = [((float(a) - float(b) + 180.0) % 360.0 - 180.0) if angular else float(a) - float(b)
              for a, b in zip(values, expected)]
    return all(math.isfinite(v) and abs(v) <= tolerance for v in deltas)


_INV_TEXTURE = re.compile(r'LogContentStreaming:\s+Texture:\s+\S+\s+(\S+)')
_INV_FIELDS = {
    'force_seconds_left': (re.compile(r'Force all mips:\s+([-\d.]+) seconds left'), lambda m: float(m.group(1))),
    'current': (re.compile(r'Current size \[2D Mips\]:\s*(\d+)x(\d+) \[(\d+)\]'), lambda m: [int(m.group(i)) for i in (1, 2, 3)]),
    'wanted': (re.compile(r'Wanted size \[2D Mips\]:\s*(\d+)x(\d+) \[(\d+)\]'), lambda m: [int(m.group(i)) for i in (1, 2, 3)]),
    'allowed': (re.compile(r'Allowed mips:\s*(\d+)-(\d+) \[(\d+)\]'), lambda m: [int(m.group(i)) for i in (1, 2, 3)]),
    'view0': (re.compile(r'View0: Position=\(X=([-\d.]+) Y=([-\d.]+) Z=([-\d.]+)\)'), lambda m: [float(m.group(i)) for i in (1, 2, 3)]),
    'format': (re.compile(r'Format:\s+(\S+)'), lambda m: m.group(1))}
# Every streamer view (MEASURED format 'View0: Position=(X= Y= Z=)', REV STREAMING_NATIVE_LOG_TEMP_PID14776.txt:23;
# INFERRED that further views print as View1.., so all are collected).
_INV_VIEW = re.compile(r'\bView(\d+): Position=\(X=([-\d.]+) Y=([-\d.]+) Z=([-\d.]+)\)')


def parse_investigate(text):
    """InvestigateTexture blocks (format: REV/STREAMING_NATIVE_LOG_TEMP_PID14776.txt:11-25). Last block per path wins."""
    records, current = {}, None
    for line in text.splitlines():
        if 'Cmd: ' in line:
            current = None
            continue
        hit = _INV_TEXTURE.search(line)
        if hit:
            current = {'path': hit.group(1), 'views': []}
            records[current['path']] = current
            continue
        if current is not None and 'LogContentStreaming:' in line:
            for key, (rx, conv) in _INV_FIELDS.items():
                m = rx.search(line)
                if m and key not in current:
                    current[key] = conv(m)
            v = _INV_VIEW.search(line)
            if v:
                current['views'].append([float(v.group(i)) for i in (2, 3, 4)])
    return records


def is_streamed(props):
    return str(props.get('never_stream')) != 'True' and str(props.get('virtual_texture_streaming')) != 'True'


def render_proof(records, props_by_path, eye, tolerance=VIEW_TOLERANCE_CM):
    """INFERRED proxy that the viewport drew from `eye`: viewport draws register their view origin with the texture
    streamer (InvestigateTexture ViewN). Only streamed (not NeverStream, not VT) bound textures carry views."""
    rows, mismatched, with_views = {}, [], 0
    for path in sorted(props_by_path):
        if not is_streamed(props_by_path[path] or {}):
            continue
        views = list((records.get(path) or {}).get('views') or [])
        hit = any(matches(v, eye, tolerance) for v in views) if views else None
        rows[path] = {'views': views, 'eye_in_views': hit}
        if views:
            with_views += 1
            if not hit:
                mismatched.append(path)
    status = ('STREAMER_VIEW_NOT_AT_CAMERA' if mismatched else
              'STREAMER_VIEW_AT_CAMERA' if with_views else 'RENDER_PROOF_UNAVAILABLE')
    return {'label': 'INFERRED', 'status': status, 'eye': list(eye), 'tolerance_cm': tolerance,
            'streamed_textures': rows, 'mismatched': mismatched, 'with_view_records': with_views}


def residency_verdict(record, props, forced):
    """Per-texture gate. NeverStream textures are fully resident by policy; VT textures are not covered."""
    if str(props.get('never_stream')) == 'True':
        return 'NEVER_STREAM_RESIDENT'
    if str(props.get('virtual_texture_streaming')) == 'True':
        return 'VIRTUAL_TEXTURE_NOT_COVERED'
    if not record or 'current' not in record or 'wanted' not in record:
        return 'NOT_IN_LOG'
    full = 'allowed' in record and record['current'][2] == record['allowed'][1]
    if record['current'] == record['wanted'] and full:
        if forced and not (record.get('force_seconds_left', 0.0) > 0.0):
            return 'FULL_BUT_FORCE_EXPIRED'
        return 'CONFIRMED_FULL'
    if record['current'] == record['wanted']:
        return 'CURRENT_EQUALS_WANTED_BELOW_MAX'
    return 'STREAMING_IN_PROGRESS'


_PROBLEM = re.compile(r'Log(ShaderCompilers|Material\w*|Shaders?)\s*:\s*(Error|Warning)\b|Failed to compile|shader compile error', re.I)


def log_scan(text):
    lines = text.splitlines()
    problems = [l[:400] for l in lines if _PROBLEM.search(l)]
    activity = [l[:300] for l in lines if 'LogShaderCompilers:' in l and not _PROBLEM.search(l)]
    clipping = [l[:400] for l in lines if 'r.EyeAdaptation.CachedLightingPreExposure' in l]
    return {'lines': len(lines), 'shader_or_material_problems': problems[:50], 'problem_count': len(problems),
            'shader_compiler_display_lines': activity[:50], 'shader_compiler_display_count': len(activity),
            'lumen_cached_lighting_exposure_clipping_warnings': clipping[:10]}


def parse_viewport_ini(text, key):
    """Saved LevelEditorViewportSettings PerInstanceSettings line for the active key (preference, not runtime)."""
    for line in text.splitlines():
        if line.startswith('PerInstanceSettings=(ConfigName="%s"' % key):
            out = {'line_sha256': sha_bytes(line.encode('utf-8'))}
            m = re.search(r'PerspViewModeIndex=(\w+)', line)
            out['persp_view_mode'] = m.group(1) if m else None
            m = re.search(r'ExposureSettings=\(([^)]*)\)', line)
            out['exposure_settings'] = m.group(1) if m else None
            for name in ('EditorShowFlagsString', 'GameShowFlagsString'):
                m = re.search(name + r'="([^"]*)"', line)
                flags = dict(f.split('=', 1) for f in m.group(1).split(',') if '=' in f) if m else {}
                out[name] = {k: flags.get(k) for k in ('PostProcessing', 'EyeAdaptation', 'Tonemapper', 'LocalExposure', 'Lighting', 'Game')}
            return out
    return {'line_sha256': None, 'status': 'KEY_NOT_IN_SAVED_CONFIG'}


def png_info(path):
    data = Path(path).read_bytes()
    ok = data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR'
    width, height = struct.unpack('>II', data[16:24]) if ok and len(data) >= 24 else (None, None)
    return {'bytes': len(data), 'sha256': sha_bytes(data), 'signature_ok': ok, 'width': width, 'height': height,
            'iend_present': b'IEND' in data[-16:]}


def ev_inference(ppv_rows, cvars, exposure_offset):
    """INFERRED manual-exposure EV from recorded inputs; only when no enabled volume overrides an exposure input."""
    overriding = [r['name'] for r in ppv_rows if str(r.get('enabled')) == 'True' and any(
        str(r.get('settings', {}).get('override_' + f)) == 'True' for f in PP_FIELDS)]
    if overriding:
        return {'label': 'INFERRED', 'status': 'NOT_COMPUTED_PP_VOLUME_OVERRIDES_EXPOSURE_INPUTS', 'volumes': overriding}
    try:
        bias = float(cvars.get('r.DefaultFeature.AutoExposure.Bias') or 0.0)
    except ValueError:
        bias = 0.0
    ev_cam = math.log2(4.0 ** 2 * 60.0 * 100.0 / 100.0)
    comp = bias + float(exposure_offset)
    return {'label': 'INFERRED', 'status': 'COMPUTED_FROM_ASSUMED_POST_PROCESS_DEFAULTS',
            'assumed_defaults': {'apply_physical_camera_exposure': True, 'camera_iso': 100.0,
                                 'camera_shutter_speed': 60.0, 'depth_of_field_fstop': 4.0},
            'ev100_physical_camera': ev_cam, 'exposure_compensation_ev': comp,
            'ev100_effective_estimate': ev_cam - comp,
            'formula': 'EV100=log2(N^2*shutter*100/ISO); effective=EV100-(r.DefaultFeature.AutoExposure.Bias+r.ExposureOffset)',
            'caveat': 'Engine manual-exposure math is not installed as source; confirm with paired captures.'}


def package_file(root, package, ext='.uasset'):
    check(package.startswith('/Game/'), 'Only /Game packages map to project files')
    return Path(root) / 'Content' / (package[len('/Game/'):].split('.')[0] + ext)


def disk_state(path):
    p = Path(path)
    if not p.exists():
        return {'exists': False}
    st = p.stat()
    return {'exists': True, 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns, 'sha256': sha_file(p)}


def write_json(path, data):
    tmp = path.with_name('.' + path.name + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')
    os.replace(tmp, path)


def is_cvar_value(value):
    return isinstance(value, str) and bool(_CVAR_VALUE.match(value))


def restorable_rows(rows):
    """Split rows into (restorable, refused): whitelisted cvar names with numeric priors only."""
    good, bad = [], []
    for row in rows or []:
        ok = isinstance(row, dict) and row.get('name') in RESTORABLE_CVARS and is_cvar_value(row.get('prior'))
        (good if ok else bad).append(row if ok else {'row': str(row)[:200], 'status': 'REFUSED_NOT_WHITELISTED_OR_NON_NUMERIC'})
    return good, bad


def restore_fallback(receipt):
    """Manual fallback when end cannot run in the begin PID (cvars are session-only; a restart also clears them)."""
    good, _ = restorable_rows(receipt.get('applied_cvars'))
    priors = receipt.get('priors') or {}
    return {'rule': 'Run mode=end in the begin PID before any editor exit. Do not edit or re-pin S1_Prep/s1_capture.py '
                    'while this receipt is BEGUN/ACTIVE (end tolerates it, other phases refuse).',
            'console_commands_reverse_order': ['%s %s' % (r['name'], r['prior']) for r in reversed(good)],
            'game_view': 'LevelEditorSubsystem.editor_set_game_view(%s, "%s")' % (priors.get('game_view'),
                                                                                priors.get('active_viewport_key'))}


def image_path_for(stage, label, index, shot):
    """Image paths are always derived (never read from the receipt): <S1_Prep>/images/<label>_<NN>_<shot>.png."""
    check(safe_token(label) and shot in SHOT_NAMES and isinstance(index, int) and 0 <= index < 100, 'Unsafe image identity')
    return Path(stage) / 'images' / ('%s_%02d_%s.png' % (label, index, shot))


def quarantine_png(src):
    """Rename (never delete, never overwrite) a PNG that is not a validated capture."""
    src = Path(src)
    if not src.exists():
        return {'path': str(src), 'status': 'ABSENT'}
    row = {'from': str(src), 'utc': utc()}
    try:
        row['png'] = png_info(src)
    except Exception as error:
        row['png'] = 'READ_FAILED:' + repr(error)
    dst = src.with_name(src.stem + '.INVALIDATED.png')
    if dst.exists():
        dst = src.with_name('%s.INVALIDATED_%s.png' % (src.stem, uuid.uuid4().hex[:8]))
    try:
        os.rename(src, dst)          # Windows os.rename never replaces an existing target
        row.update(to=str(dst), status='QUARANTINED')
    except OSError as error:         # e.g. still being written; a later end call retries
        row.update(status='RENAME_FAILED', error=repr(error))
    return row


def validate_begin(args):
    unknown = set(args) - BEGIN_KEYS
    check(not unknown, 'Unknown ARGS keys: %s' % sorted(unknown))
    check(args.get('area') in AREA_MAPS, 'area must be GazaShujaiya or GazaRimal')
    label = args.get('label')
    check(safe_token(label) and label.startswith(args['area'] + '_'), 'label must be <Area>_<ascii alnum/_>')
    check(isinstance(args.get('expected_pid'), int), 'expected_pid (int) required')
    check(safe_token(args.get('owner'), 64) and args['owner'] != 'NONE', 'owner lease token required')
    check(isinstance(args.get('camera_file_sha256'), str) and len(args['camera_file_sha256']) == 64, 'camera_file_sha256 required')
    shots = args.get('shots', list(SHOT_NAMES))
    check(isinstance(shots, list) and 1 <= len(shots) <= 12 and all(s in SHOT_NAMES for s in shots), 'shots: 1-12 of close/middle/wide (repeats allowed)')
    check(args.get('viewmode', 'LIT') in ('LIT', 'UNLIT'), 'viewmode LIT or UNLIT')
    exposure = dict({'mode': 'manual_cvar', 'exposure_offset': 0.0}, **(args.get('exposure') or {}))
    check(set(exposure) <= {'mode', 'exposure_offset'} and exposure['mode'] in ('manual_cvar', 'auto_recorded'), 'exposure.mode manual_cvar|auto_recorded')
    check(isinstance(exposure['exposure_offset'], (int, float)) and -10.0 <= exposure['exposure_offset'] <= 10.0, 'exposure_offset in [-10, 10]')
    residency = dict({'mode': 'force_bound_textures', 'seconds': 60.0, 'extra_parameters': [], 'require_confirmed': True},
                     **(args.get('residency') or {}))
    check(set(residency) <= {'mode', 'seconds', 'extra_parameters', 'require_confirmed'} and
          residency['mode'] in ('force_bound_textures', 'fully_load_cvar', 'none'), 'residency.mode force_bound_textures|fully_load_cvar|none')
    check(isinstance(residency['seconds'], (int, float)) and 5.0 <= residency['seconds'] <= 120.0, 'residency.seconds in [5, 120]')
    check(isinstance(residency['extra_parameters'], list) and all(safe_token(n) for n in residency['extra_parameters']), 'extra_parameters: parameter names')
    settings = {'min_settle_frames': int(args.get('min_settle_frames', 120)),
                'min_settle_seconds': float(args.get('min_settle_seconds', 8.0)),
                'screenshot_delay': float(args.get('screenshot_delay', 2.0)),
                'min_gi_quality': args.get('min_gi_quality', 2),
                'require_sole_editor': bool(args.get('require_sole_editor', True)),
                'restore_ui': bool(args.get('restore_ui', True)),
                'log_problem_gate': bool(args.get('log_problem_gate', True))}
    check(0 <= settings['min_settle_frames'] <= 100000 and 0.0 <= settings['min_settle_seconds'] <= 600.0, 'settle bounds')
    check(0.0 <= settings['screenshot_delay'] <= 10.0, 'screenshot_delay in [0, 10]')
    check(settings['min_gi_quality'] is None or settings['min_gi_quality'] in (0, 1, 2, 3, 4), 'min_gi_quality 0-4 or null')
    allowed = args.get('allowed_dirty_content', [])
    check(isinstance(allowed, list) and all(isinstance(p, str) and p.startswith('/Game/') for p in allowed), 'allowed_dirty_content: /Game package paths')
    return shots, args.get('viewmode', 'LIT'), exposure, residency, settings, sorted(allowed)


# ----------------------------------------------------------------------------- editor helpers (lazy unreal)
def _u():
    import unreal
    return unreal


def project_root(u):
    return Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()   # GP :37


def registry():
    mod = sys.modules.get(REGISTRY)
    if mod is None:
        mod = types.ModuleType(REGISTRY)
        mod.ACTIVE, mod.TASKS = {}, {}
        sys.modules[REGISTRY] = mod
    return mod


def task_done(task):
    """True/False from UAutomationEditorTask.IsTaskDone; None when there is no task or the query fails."""
    if task is None:
        return None
    try:
        return bool(task.is_task_done())
    except Exception:
        return None


def live_tasks(label=None):
    """(label, index, done) for every registry screenshot task not known to be done, whatever its shot state."""
    return sorted((lab, idx, task_done(t)) for (lab, idx), t in list(registry().TASKS.items())
                  if (label is None or lab == label) and task_done(t) is not True)


def path_of(obj):
    return obj.get_path_name() if obj is not None else None


def dirty(u):
    """GP native_capture_epic_resident.py:126-128."""
    return {'maps': sorted(p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
            'content': sorted(p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}


def sole_editor():
    """GP native_capture_epic_resident.py:48-53 (spawns a read-only PowerShell process query)."""
    command = 'ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process -Filter "Name = \'UnrealEditor.exe\'" | ForEach-Object { [int]$_.ProcessId })'
    run = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command], check=True,
                         capture_output=True, text=True, timeout=30, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    pids = json.loads(run.stdout)
    pids = pids if isinstance(pids, list) else [pids]
    check(pids == [os.getpid()], 'Exactly the current editor process is required: %s' % pids)
    return pids


def cvar_snapshot(u, names):
    out = {}
    for name in names:
        try:
            out[name] = str(u.SystemLibrary.get_console_variable_string_value(name))   # GP native_streaming_diagnostic.py:41
        except Exception as error:
            out[name] = 'READ_FAILED:' + repr(error)
    return out


def all_cvars(u):
    return {group: cvar_snapshot(u, names) for group, names in CVARS.items()}


def set_cvar(u, world, name, value):
    u.SystemLibrary.execute_console_command(world, '%s %s' % (name, value))          # GP native_streaming_diagnostic.py:56
    return str(u.SystemLibrary.get_console_variable_string_value(name))


def prop(obj, *names):
    for name in names:
        try:
            return str(obj.get_editor_property(name))
        except Exception:
            continue
    return None


def texture_props(texture):
    return {k: prop(texture, k) for k in TEXTURE_PROPS}


def view_mode_name(u, mode):
    """Enum -> 'VMI_*' name using dir(unreal.ViewModeIndex) (REV/VIEWMODE_BEFORE_PID30632.json available_modes)."""
    for name in dir(u.ViewModeIndex):
        if name.startswith('VMI_') and getattr(u.ViewModeIndex, name) == mode:
            return name
    return str(mode)


def guard(u, area, owner, thread, require_sole):
    """Self-contained guard. Patterns: lease GP native_streaming_diagnostic.py:9-13; cooking paused :15-16;
    HDA auto cook/bake :20-22; autosave :23; workflow ticks :24; sole editor GP native_capture_epic_resident.py:48-53."""
    pid = os.getpid()
    root = project_root(u)
    lines = [x for x in (root / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
    lease = lines[-1]
    fields = parse_lease(lease)
    check(fields.get('OWNER') == owner, 'Last lease OWNER differs from ARGS owner')
    check(fields.get('assigned_editor_PID') == str(pid), 'Last lease is not assigned to this editor PID')
    check(fields.get('map') == AREA_MAPS[area], 'Last lease map differs from the area map')
    if thread:
        check(fields.get('operator_thread_id') == thread, 'Lease operator_thread_id differs')
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    world = editor.get_editor_world()
    check(world.get_outermost().get_path_name() == AREA_MAPS[area], 'Editor world is not the area map')
    check(not level.is_in_play_in_editor(), 'PIE is active')
    key = level.get_active_viewport_config_key()
    check(str(key) not in ('', 'None'), 'An active viewport key is required')
    check(level.get_pilot_level_actor(key) is None, 'Viewport is piloting an actor; camera setters would move it')
    api = u.HoudiniPublicAPIBlueprintLib.get_api()
    check(api.is_asset_cooking_paused(), 'Houdini Engine cooking must be paused')
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    hdas = [a for a in actors if a.get_class().get_name() == 'HoudiniAssetActor']
    wrappers = [u.HoudiniPublicAPIAssetWrapper.create_wrapper(None, a) for a in hdas]
    check(all(not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled() for w in wrappers), 'HDA auto cook/bake must be off')
    check(not u.get_default_object(u.load_class(None, '/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
          'Editor autosave must be off')
    check(not any(sum(getattr(r, k, None) is not None for r in getattr(sys.modules.get(n), 'ACTIVE', [])
                      for k in ('watch_tick', 'save_tick', 'tick_handle', '_pending_correction'))
                  for n in ('geocity_bank_workflow', 'geocity_roadbld_workflow')), 'Managed workflow ticks are active')
    pids = sole_editor() if require_sole else 'NOT_CHECKED_BY_ARGS'
    return {'pid': pid, 'lease': lease, 'world': AREA_MAPS[area], 'key': str(key), 'hda_actors': len(hdas),
            'cooking_paused': True, 'autosave': False, 'editor_pids': pids}, world, level, editor, key, actors


def camera_state(u, level, editor, key):
    eye, rot = level.get_level_viewport_camera_info(key)                                 # GP :170-172
    p_eye, p_rot = editor.get_level_viewport_camera_info()
    vec = lambda v: [float(v.x), float(v.y), float(v.z)]
    rot3 = lambda r: [float(r.pitch), float(r.yaw), float(r.roll)]
    return {'keyed': {'eye': vec(eye), 'rotation': rot3(rot), 'fov': float(level.get_level_viewport_fov(key))},
            'primary': {'eye': vec(p_eye), 'rotation': rot3(p_rot)},
            'view_mode': view_mode_name(u, u.AutomationLibrary.get_editor_active_viewport_view_mode())}


def set_camera(u, level, editor, key, eye, rotation, fov):
    """GP native_capture_epic_resident.py:160-164."""
    e, r = u.Vector(*eye), u.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2] if len(rotation) > 2 else 0.0)
    level.set_level_viewport_camera_info(e, r, key)
    level.set_level_viewport_fov(float(fov), key)
    level.editor_invalidate_viewports()
    editor.set_level_viewport_camera_info(e, r)


def restore_game_view(level, receipt):
    """take_high_res_screenshot(force_game_view=True) (AutomationBlueprintFunctionLibrary.h:143) may leave game view on.
    Restore the begin value on the begin viewport key (LevelEditorSubsystem.h:72,75), independent of restore_ui."""
    priors = receipt.get('priors') or {}
    prior, key = priors.get('game_view'), priors.get('active_viewport_key')
    out = {'prior': prior, 'viewport_key': key}
    if prior not in ('True', 'False') or not key:
        out.update(status='PRIOR_UNKNOWN', restored=None)
        return out
    want = prior == 'True'
    try:
        out['before'] = bool(level.editor_get_game_view(key))
        if out['before'] != want:
            level.editor_set_game_view(want, key)
            level.editor_invalidate_viewports()
            out['action'] = 'SET'
        else:
            out['action'] = 'UNCHANGED'
        out['after'] = bool(level.editor_get_game_view(key))
        out['restored'] = out['after'] == want
        out['status'] = 'OK' if out['restored'] else 'READBACK_DIFFERS'
    except Exception as error:
        out.update(status='FAILED', error=repr(error), restored=False)
    return out


def camera_verdict(state, preset, viewmode):
    rot = rotation_for(preset['eye'], preset['target'])
    out = {'eye_match': matches(state['keyed']['eye'], preset['eye'], 0.01),
           'rotation_match': matches(state['keyed']['rotation'], rot, 0.01, angular=True),
           'fov_match': abs(state['keyed']['fov'] - float(preset['fov'])) <= 0.001,
           'primary_eye_match': matches(state['primary']['eye'], preset['eye'], 0.01),
           'primary_rotation_match': matches(state['primary']['rotation'], rot, 0.01, angular=True),
           'view_mode_match': state['view_mode'] == 'VMI_' + viewmode}
    out['all_match'] = all(out.values())
    return out


def environment(u, actors):
    rows = []
    for a in actors:
        cls = a.get_class().get_name()
        is_ls = isinstance(a, u.LandscapeProxy)
        if cls not in ENV_CLASSES and not isinstance(a, u.PostProcessVolume) and not is_ls:
            continue
        row = {'name': a.get_name(), 'class': cls}
        try:
            row['label'] = a.get_actor_label()
            r = a.get_actor_rotation()
            row['rotation'] = [float(r.pitch), float(r.yaw), float(r.roll)]
        except Exception:
            pass
        if isinstance(a, u.PostProcessVolume):
            row.update({k: prop(a, k) for k in ('enabled', 'unbound', 'priority', 'blend_weight', 'blend_radius')})
            try:
                s = a.get_editor_property('settings')
                row['settings'] = {}
                for f in PP_FIELDS:
                    row['settings'][f] = prop(s, f)
                    row['settings']['override_' + f] = prop(s, 'override_' + f)
            except Exception as error:
                row['settings'] = {'status': 'READ_FAILED', 'error': repr(error)}
        elif is_ls:
            try:
                row['landscape_material'] = path_of(a.get_editor_property('landscape_material'))
            except Exception as error:
                row['landscape_material'] = 'READ_FAILED:' + repr(error)
        else:
            for comp_cls, keys in ((getattr(u, 'DirectionalLightComponent', None), ('intensity', 'light_color', 'atmosphere_sun_light')),
                                   (getattr(u, 'SkyLightComponent', None), ('intensity', 'real_time_capture', 'source_type')),
                                   (getattr(u, 'ExponentialHeightFogComponent', None), ('fog_density', 'fog_height_falloff', 'volumetric_fog'))):
                if comp_cls is None:
                    continue
                try:
                    comp = a.get_component_by_class(comp_cls)
                except Exception:
                    comp = None
                if comp is not None:
                    row['component'] = {k: prop(comp, k) for k in keys}
        rows.append(row)
    return rows


def resolve_residency(u, child, extra):
    names = list(BASE_RESIDENCY_PARAMETERS)
    try:
        listed = [str(n) for n in u.MaterialEditingLibrary.get_texture_parameter_names(child)]   # MaterialEditingLibrary.h:510
        names += sorted(n for n in listed if n.startswith(S1_TEXTURE_PREFIX))
        listing = 'LISTED'
    except Exception as error:
        listing = 'LIST_FAILED:' + repr(error)
    names += list(extra)
    names = list(dict.fromkeys(names))
    rows, textures = {}, {}
    for name in names:
        t = u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(child, name)   # GP native_streaming_diagnostic.py:68
        rows[name] = path_of(t)
        if isinstance(t, u.Texture2D) and hasattr(t, 'set_force_mip_levels_to_be_resident'):
            textures[t.get_path_name()] = t
    unresolved = [n for n in BASE_RESIDENCY_PARAMETERS if not isinstance(rows.get(n), str)]
    check(not unresolved, 'Live bound parameters did not resolve to textures: %s' % unresolved)
    return {'parameter_listing': listing, 'parameters': rows}, textures


def force(textures, seconds):
    for t in textures.values():
        t.set_force_mip_levels_to_be_resident(float(seconds), 0)                        # GP native_streaming_diagnostic.py:73


def material_readback(u, child):
    out = {'parent': path_of(child.get_editor_property('parent'))}
    try:
        out['GeoCity_GrassCoverage'] = float(u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(child, 'GeoCity_GrassCoverage'))
    except Exception as error:
        out['GeoCity_GrassCoverage'] = 'READ_FAILED:' + repr(error)
    for name in S1_SWITCH_CANDIDATES:   # no project precedent for this getter; read-only, failure recorded
        try:
            out[name] = bool(u.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(child, name))
        except Exception as error:
            out[name] = 'READ_FAILED:' + repr(error)
    return out


def flush_log(u, world):
    u.SystemLibrary.execute_console_command(world, 'FLUSHLOG')   # FLUSHLOG string present in UnrealEditor-Engine.dll


def locate_log(u, world):
    marker = 'S1_CAPTURE_LOG_MARKER_' + uuid.uuid4().hex
    u.log(marker)
    flush_log(u, world)
    log_dir = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_log_dir()))
    files = sorted((p for p in log_dir.glob('*.log') if '-backup-' not in p.name), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[:6]:
        size = p.stat().st_size
        start = max(0, size - 16 * 1024 * 1024)
        with p.open('rb') as f:
            f.seek(start)
            data = f.read()
        idx = data.rfind(marker.encode('ascii'))
        if idx >= 0:
            return {'file': str(p), 'offset': start + idx, 'marker': marker, 'status': 'LOCATED'}
    return {'file': None, 'offset': None, 'marker': marker, 'status': 'MARKER_NOT_FOUND'}


def read_log(u, world, log, offset):
    if not log.get('file') or offset is None:
        return '', None
    flush_log(u, world)
    p = Path(log['file'])
    with p.open('rb') as f:
        f.seek(offset)
        data = f.read(64 * 1024 * 1024)
    return data.decode('utf-8', errors='replace'), offset + len(data)


def log_end(u, world, log):
    """Byte offset of the log end after FLUSHLOG, so later reads start exactly after already-written lines."""
    if not log.get('file'):
        return None
    flush_log(u, world)
    return Path(log['file']).stat().st_size


def frame_count(u):
    fn = getattr(u.SystemLibrary, 'get_frame_count', None)                               # KismetSystemLibrary.h:286-287
    return int(fn()) if callable(fn) else None


# ----------------------------------------------------------------------------- receipt plumbing
def stage_dir(u):
    return project_root(u) / REL_STAGE


def receipt_path(u, label):
    check(safe_token(label), 'Unsafe label')
    return stage_dir(u) / ('CAPTURE_' + label + '.json')


def load_receipt(u, args, allow_script_change=False):
    """Returns (path, receipt, script_check). prepare/request/complete refuse a changed script; end and status only
    record it, so the restore of process-global cvars is never blocked. The begin PID is always required."""
    unknown = set(args) - PHASE_KEYS
    check(not unknown, 'Unknown ARGS keys: %s' % sorted(unknown))
    path = receipt_path(u, args.get('label'))
    receipt = json.loads(path.read_text(encoding='utf-8'))
    check(receipt['schema'] == SCHEMA and receipt['label'] == args['label'], 'Receipt identity differs')
    check(os.getpid() == args.get('expected_pid') == receipt['pid'], 'Phase must run in the begin PID')
    current = sha_file(stage_dir(u) / SCRIPT_NAME)
    unchanged = current == (receipt.get('script') or {}).get('sha256')
    check(unchanged or allow_script_change, 'Capture script changed since begin')
    script_check = {'unchanged': unchanged, 'current_sha256': current}
    if not unchanged:
        script_check['warning'] = 'S1_Prep/s1_capture.py changed since begin; this phase runs the current file'
    return path, receipt, script_check


def shot_of(receipt, args):
    index = args.get('index')
    check(isinstance(index, int) and 0 <= index < len(receipt['shots']), 'index out of range')
    return receipt['shots'][index]


def phase_log(receipt, phase, frame, outcome, **extra):
    row = {'phase': phase, 'utc': utc(), 'frame': frame, 'outcome': outcome}
    row.update(extra)
    receipt.setdefault('phases', []).append(row)
    receipt['updated_utc'] = row['utc']


def light_guard(u, receipt):
    g, world, level, editor, key, actors = guard(u, receipt['area'], receipt['owner'], receipt.get('operator_thread_id'), False)
    check(str(key) == receipt['priors']['active_viewport_key'], 'Active viewport key changed since begin')
    d = dirty(u)
    return g, world, level, editor, key, d


# ----------------------------------------------------------------------------- phases
def begin(u, args):
    shots, viewmode, exposure, residency, settings, allowed = validate_begin(args)
    check(os.getpid() == args['expected_pid'], 'Wrong current process')
    reg = registry()
    check(not reg.ACTIVE, 'Another capture is active or its restore is incomplete (run mode=end for it): %s'
          % {k: (v or {}).get('state', 'ACTIVE') for k, v in reg.ACTIVE.items()})
    busy = [t for t in live_tasks() if t[2] is False]
    check(not busy, 'A screenshot task of an earlier capture is still running (global screenshot config): %s' % busy)
    g, world, level, editor, key, actors = guard(u, args['area'], args['owner'], args.get('operator_thread_id'), settings['require_sole_editor'])
    game_view_prior = prop_call(level, 'editor_get_game_view', key)                    # LevelEditorSubsystem.h:75
    check(game_view_prior in ('True', 'False'), 'Game view prior unreadable (%s); force_game_view could not be restored' % game_view_prior)
    root, out_dir = project_root(u), stage_dir(u)
    script = out_dir / SCRIPT_NAME
    cameras_file = (root / REL_GP / ('CAMERAS_' + args['area'] + '.json')).resolve(strict=True)
    check(sha_file(cameras_file) == args['camera_file_sha256'], 'Approved existing camera file changed')       # GP :102-104
    cameras = json.loads(cameras_file.read_text(encoding='utf-8-sig'))
    check(set(cameras) == set(SHOT_NAMES) and all(set(c) == {'eye', 'target', 'fov'} for c in cameras.values()), 'Malformed camera file')
    d0 = dirty(u)
    check(d0['maps'] == [] and set(d0['content']) <= set(allowed), 'Map dirty or unexpected dirty content: %s' % d0)  # GP :148-149
    cv = all_cvars(u)
    if settings['min_gi_quality'] is not None:
        check(cv['lighting'].get('r.DynamicGlobalIlluminationMethod') == '1', 'Lumen GI is not active (r.DynamicGlobalIlluminationMethod != 1)')
        check(cv['lighting'].get('sg.GlobalIlluminationQuality', '').isdigit() and
              int(cv['lighting']['sg.GlobalIlluminationQuality']) >= settings['min_gi_quality'], 'sg.GlobalIlluminationQuality below the required level')
    child = u.load_asset(AREA_CHILD[args['area']])
    check(child is not None, 'Area child MI missing')
    res_rows, textures = resolve_residency(u, child, residency['extra_parameters'])
    tex_props = {p: texture_props(t) for p, t in textures.items()}
    ini_file = root / 'Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini'
    ini = parse_viewport_ini(ini_file.read_text(encoding='utf-8-sig', errors='replace'), str(key)) if ini_file.exists() else {'status': 'NO_FILE'}
    disk_files = [package_file(root, p) for p in (MASTER, BASE, GRASS, *AREA_CHILD.values())] + [package_file(root, m, '.umap') for m in AREA_MAPS.values()]
    images = out_dir / 'images'
    images.mkdir(exist_ok=True)
    shot_rows = []
    for i, name in enumerate(shots):
        image = image_path_for(out_dir, args['label'], i, name)
        check(not image.exists() and not list(images.glob(image.stem + '.INVALIDATED*.png')), 'Preserve existing image: %s' % image)
        worst = len(str(image.with_name(image.stem + '.INVALIDATED_00000000.png')))   # MAX_PATH would make quarantine fail
        check(worst < 250, 'Image/quarantine path is %d chars (Windows MAX_PATH); shorten the label' % worst)
        shot_rows.append({'index': i, 'shot': name, 'image': str(image), 'state': 'PENDING'})
    path = receipt_path(u, args['label'])
    check(not (out_dir / ('CAPTURE_' + args['label'] + '_LOG.txt')).exists(), 'Preserve existing log slice')
    ppv = environment(u, actors)
    throttle = None
    try:
        throttle = prop(u.get_default_object(u.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings')),
                        'throttle_cpu_when_not_foreground', 'bThrottleCPUWhenNotForeground')
    except Exception as error:
        throttle = 'READ_FAILED:' + repr(error)
    try:
        size = editor.get_level_viewport_size()
        viewport_size = [int(size.x), int(size.y)] if size is not None else None
    except Exception as error:
        viewport_size = 'READ_FAILED:' + repr(error)
    receipt = {
        'schema': SCHEMA, 'label': args['label'], 'area': args['area'], 'status': 'BEGINNING', 'created_utc': utc(),
        'pid': os.getpid(), 'owner': args['owner'], 'operator_thread_id': args.get('operator_thread_id'),
        'script': {'path': str(script), 'sha256': sha_file(script)}, 'world': AREA_MAPS[args['area']],
        'child': AREA_CHILD[args['area']], 'cameras': {'file': str(cameras_file), 'sha256': args['camera_file_sha256'], 'presets': cameras},
        'settings': dict(settings, viewmode=viewmode, width=WIDTH, height=HEIGHT, force_game_view=True),
        'exposure': {'mode': exposure['mode'], 'exposure_offset': float(exposure['exposure_offset']),
                     'qualification': QUALIFICATION['exposure_' + exposure['mode']],
                     'viewport_only_route': {'status': 'NOT_AVAILABLE_IN_PYTHON', 'evidence': [
                         'LevelEditorSubsystem.h / UnrealEditorSubsystem.h / AutomationBlueprintFunctionLibrary.h expose no exposure or post-process setter',
                         'Fixed EV100 (ToggleInGameExposure/FixedEV100) exists only as a UnrealEd UI command; its saved preference is in the ini line below']},
                     'saved_viewport_preference': ini},
        'residency': dict(residency, qualification=QUALIFICATION[residency['mode']], bound=res_rows,
                          textures=sorted(textures), texture_props_begin=tex_props),
        'priors': {'active_viewport_key': str(key), 'camera': camera_state(u, level, editor, key),
                   'game_view': game_view_prior, 'cvars': cv},
        'environment': {'actors': ppv, 'throttle_cpu_when_not_foreground': throttle, 'viewport_size': viewport_size},
        'material_begin': material_readback(u, child), 'guard_begin': g, 'dirty_begin': d0, 'allowed_dirty_content': allowed,
        'disk_begin': {str(f): disk_state(f) for f in disk_files}, 'applied_cvars': [], 'shots': shot_rows,
        'native_cancel': NATIVE_CANCEL, 'log': locate_log(u, world)}
    receipt['log']['begin_offset'] = receipt['log']['offset']
    receipt['restore_fallback'] = restore_fallback(receipt)
    with path.open('x', encoding='utf-8') as f:            # never overwrite a receipt (GP :202)
        f.write(json.dumps(receipt, indent=2, default=str))
    # Authoritative in-process copy of what begin set; end prefers it over the on-disk receipt.
    entry = reg.ACTIVE[args['label']] = {'tick_handle': None, 'receipt': str(path), 'state': 'ACTIVE', 'applied_cvars': []}

    def apply(name, value, prior):
        check(name in RESTORABLE_CVARS and is_cvar_value(prior),
              'Prior of %s was not read as a number (%r); refusing to apply it' % (name, prior))
        row = {'name': name, 'prior': prior, 'value': str(value)}
        entry['applied_cvars'].append(dict(row))
        receipt['applied_cvars'].append(row)
        receipt['restore_fallback'] = restore_fallback(receipt)
        write_json(path, receipt)
        row['readback'] = set_cvar(u, world, name, value)

    try:
        if exposure['mode'] == 'manual_cvar':
            for name, value in ((METHOD_OVERRIDE, MANUAL_METHOD), (EXPOSURE_OFFSET, float(exposure['exposure_offset']))):
                apply(name, value, cv['exposure'][name])
            check(int(u.SystemLibrary.get_console_variable_int_value(METHOD_OVERRIDE)) == MANUAL_METHOD, 'Manual exposure override did not read back')
            check(abs(float(u.SystemLibrary.get_console_variable_float_value(EXPOSURE_OFFSET)) - float(exposure['exposure_offset'])) < 1e-4, 'Exposure offset did not read back')
        if residency['mode'] == 'fully_load_cvar':
            apply(FULLY_LOAD, 1, cv['streaming'][FULLY_LOAD])
            check(int(u.SystemLibrary.get_console_variable_int_value(FULLY_LOAD)) == 1, 'FullyLoadUsedTextures did not read back')
        receipt['exposure']['locked_readback'] = cvar_snapshot(u, CVARS['exposure'])
        receipt['exposure']['ev'] = (ev_inference([r for r in ppv if 'settings' in r], cv['exposure'],
                                                  exposure['exposure_offset']) if exposure['mode'] == 'manual_cvar' else {'status': 'NOT_LOCKED'})
        check(dirty(u) == d0, 'Begin changed dirty packages')
        receipt['status'] = 'BEGUN'
        phase_log(receipt, 'begin', frame_count(u), 'OK')
    except Exception as error:
        receipt['status'] = 'FAILED_BEGIN'
        receipt['begin_error'] = repr(error)
        receipt['begin_restore'] = restore_cvars(u, world, entry['applied_cvars'])
        if all(r.get('restored') is True for r in receipt['begin_restore']):
            reg.ACTIVE.pop(args['label'], None)
        else:
            entry['state'] = 'RESTORE_INCOMPLETE'      # blocks later begins until mode=end restores
        phase_log(receipt, 'begin', frame_count(u), 'FAILED', error=repr(error))
        write_json(path, receipt)
        raise
    write_json(path, receipt)
    return {'receipt': str(path), 'status': receipt['status'], 'shots': [(s['index'], s['shot']) for s in shot_rows],
            'textures': len(textures), 'exposure': receipt['exposure']['locked_readback'], 'log': receipt['log']['status']}


def prop_call(obj, name, *args):
    fn = getattr(obj, name, None)
    if not callable(fn):
        return 'API_NOT_EXPOSED'
    try:
        return str(fn(*args))
    except Exception as error:
        return 'READ_FAILED:' + repr(error)


def exposure_still_locked(u, receipt):
    if receipt['exposure']['mode'] != 'manual_cvar':
        return True
    return (int(u.SystemLibrary.get_console_variable_int_value(METHOD_OVERRIDE)) == MANUAL_METHOD and
            abs(float(u.SystemLibrary.get_console_variable_float_value(EXPOSURE_OFFSET)) - receipt['exposure']['exposure_offset']) < 1e-4)


def prepare(u, args):
    path, receipt, _ = load_receipt(u, args)
    check(receipt['status'] in ('BEGUN', 'ACTIVE'), 'Capture is not active: ' + receipt['status'])
    shot = shot_of(receipt, args)
    check(shot['state'] in ('PENDING', 'PREPARED', 'REFUSED'), 'Shot cannot be (re)prepared from ' + shot['state'])
    check(not any(s['state'] in ('REQUESTED', 'REQUESTING') for s in receipt['shots']), 'A requested screenshot is still pending completion')
    check(not live_tasks(receipt['label']), 'A screenshot task of this capture is still live: %s' % live_tasks(receipt['label']))
    g, world, level, editor, key, d = light_guard(u, receipt)
    check(d == receipt['dirty_begin'], 'Dirty packages changed since begin')
    check(exposure_still_locked(u, receipt), 'Exposure lock changed since begin')
    preset = receipt['cameras']['presets'][shot['shot']]
    rotation = rotation_for(preset['eye'], preset['target'])
    set_camera(u, level, editor, key, preset['eye'], rotation, preset['fov'])
    u.AutomationLibrary.set_editor_active_viewport_view_mode(getattr(u.ViewModeIndex, 'VMI_' + receipt['settings']['viewmode']))   # GP :166
    level.editor_invalidate_viewports()
    state = camera_state(u, level, editor, key)
    verdict = camera_verdict(state, preset, receipt['settings']['viewmode'])
    check(verdict['all_match'], 'Camera/FOV/view-mode readback differs from preset: %s' % verdict)                # GP :181-183
    child = u.load_asset(receipt['child'])
    _, textures = resolve_residency(u, child, receipt['residency']['extra_parameters'])
    check(sorted(textures) == receipt['residency']['textures'], 'Bound texture set changed since begin')
    if receipt['residency']['mode'] == 'force_bound_textures':
        force(textures, receipt['residency']['seconds'])
    clearance = None
    try:
        e = preset['eye']
        hit = u.SystemLibrary.line_trace_single(world, u.Vector(e[0], e[1], e[2] + 100000), u.Vector(e[0], e[1], e[2] - 100000),
                                                u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], u.DrawDebugTrace.NONE, False).to_dict()   # GP native_capture.py:17
        if hit.get('blocking_hit'):
            clearance = {'first_hit_actor': path_of(hit.get('hit_actor')), 'impact_z': float(hit['impact_point'].z),
                         'eye_minus_impact_cm': float(e[2]) - float(hit['impact_point'].z)}
    except Exception as error:
        clearance = 'READ_FAILED:' + repr(error)
    check(dirty(u) == receipt['dirty_begin'], 'Prepare changed dirty packages')
    shot.update({'state': 'PREPARED', 'prepared_utc': utc(), 'prepare_epoch': time.time(), 'prepare_frame': frame_count(u),
                 'prepare_log_offset': log_end(u, world, receipt['log']), 'camera_after_prepare': state, 'camera_verdict': verdict,
                 'rotation': rotation, 'eye_clearance': clearance, 'refusals': shot.get('refusals', [])})
    receipt['status'] = 'ACTIVE'
    phase_log(receipt, 'prepare', shot['prepare_frame'], 'OK', index=shot['index'])
    write_json(path, receipt)
    return {'receipt': str(path), 'index': shot['index'], 'shot': shot['shot'], 'state': 'PREPARED',
            'wait_at_least': {'frames': receipt['settings']['min_settle_frames'], 'seconds': receipt['settings']['min_settle_seconds']}}


def refuse(u, path, receipt, shot, reason, **detail):
    row = dict({'utc': utc(), 'reason': reason}, **detail)
    shot.setdefault('refusals', []).append(row)
    phase_log(receipt, 'request', frame_count(u), 'REFUSED', index=shot['index'], reason=reason)
    write_json(path, receipt)
    return {'receipt': str(path), 'index': shot['index'], 'state': shot['state'], 'refused': reason, 'detail': detail}


def request(u, args):
    path, receipt, _ = load_receipt(u, args)
    check(receipt['status'] == 'ACTIVE', 'Capture is not active: ' + receipt['status'])
    shot = shot_of(receipt, args)
    check(shot['state'] == 'PREPARED', 'Shot must be PREPARED, is ' + shot['state'])
    check(not any(s is not shot and s['state'] in ('REQUESTED', 'REQUESTING') for s in receipt['shots']),
          'Another screenshot of this capture is still REQUESTED/REQUESTING')        # one high-res request at a time
    check(not live_tasks(receipt['label']), 'A screenshot task of this capture is still live: %s' % live_tasks(receipt['label']))
    image = image_path_for(stage_dir(u), receipt['label'], shot['index'], shot['shot'])
    check(str(image) == shot['image'], 'Receipt image path differs from the derived path')
    g, world, level, editor, key, d = light_guard(u, receipt)
    check(d == receipt['dirty_begin'], 'Dirty packages changed since begin')
    preset = receipt['cameras']['presets'][shot['shot']]
    state = camera_state(u, level, editor, key)
    verdict = camera_verdict(state, preset, receipt['settings']['viewmode'])
    if not verdict['all_match']:
        return refuse(u, path, receipt, shot, 'CAMERA_OR_VIEWMODE_CHANGED', verdict=verdict)
    if not exposure_still_locked(u, receipt):
        return refuse(u, path, receipt, shot, 'EXPOSURE_LOCK_CHANGED')
    frames = frame_count(u)
    elapsed = time.time() - shot['prepare_epoch']
    frame_delta = None if frames is None or shot['prepare_frame'] is None else frames - shot['prepare_frame']
    if elapsed < receipt['settings']['min_settle_seconds'] or (frame_delta is not None and frame_delta < receipt['settings']['min_settle_frames']):
        return refuse(u, path, receipt, shot, 'NOT_SETTLED', seconds=elapsed, frames=frame_delta)
    child = u.load_asset(receipt['child'])
    _, textures = resolve_residency(u, child, receipt['residency']['extra_parameters'])
    check(sorted(textures) == receipt['residency']['textures'], 'Bound texture set changed since begin')
    forced = receipt['residency']['mode'] == 'force_bound_textures'
    if forced:
        force(textures, receipt['residency']['seconds'])
    started = time.monotonic()
    u.AutomationLibrary.finish_loading_before_screenshot()                               # AutomationBlueprintFunctionLibrary.h:79-80
    finish_seconds = time.monotonic() - started
    inv_offset = log_end(u, world, receipt['log'])
    for name in sorted({t.get_name() for t in textures.values()}):
        u.SystemLibrary.execute_console_command(world, 'InvestigateTexture ' + name)     # GP native_streaming_diagnostic.py:55-56
    inv_text, _ = read_log(u, world, receipt['log'], inv_offset)
    records = parse_investigate(inv_text)
    props = receipt['residency']['texture_props_begin']
    residency = {p: {'verdict': residency_verdict(records.get(p), props.get(p, {}), forced), 'record': records.get(p)} for p in sorted(textures)}
    eye = preset['eye']
    for row in residency.values():
        v0 = (row['record'] or {}).get('view0')
        row['streamer_view0_matches_camera'] = None if v0 is None else matches(v0, eye, VIEW_TOLERANCE_CM)
    proof = render_proof(records, {p: props.get(p, {}) for p in textures}, eye)       # runs for every residency mode
    settle_text, _ = read_log(u, world, receipt['log'], shot['prepare_log_offset'])
    scan = log_scan(settle_text)
    gate = {'seconds': elapsed, 'frames': frame_delta, 'finish_loading_seconds': finish_seconds,
            'frames_caveat': 'MEASURED: KismetSystemLibrary GetFrameCount (h:287) counts engine ticks, not viewport redraws; see render_proof',
            'finish_loading_effect': 'INFERRED (cpp not installed): flush loading/compilation/streaming',
            'pending_shader_compile_getter': 'NOT_EXPOSED (no UFUNCTION; GP native_stochastic_verify_readonly.py:86-95)',
            'log_scan': scan, 'residency': residency, 'render_proof': proof, 'log_status': receipt['log']['status']}
    shot['gate'] = gate
    if scan['problem_count'] and receipt['settings']['log_problem_gate']:
        return refuse(u, path, receipt, shot, 'SHADER_OR_MATERIAL_LOG_PROBLEMS', count=scan['problem_count'])
    if proof['status'] == 'STREAMER_VIEW_NOT_AT_CAMERA':
        return refuse(u, path, receipt, shot, 'STREAMER_VIEW_NOT_AT_CAMERA', mismatched=proof['mismatched'],
                      views={p: proof['streamed_textures'][p]['views'] for p in proof['mismatched']}, eye=eye,
                      remedy=RENDER_PROOF_REMEDY)
    bad = {p: r['verdict'] for p, r in residency.items() if r['verdict'] not in ('CONFIRMED_FULL', 'NEVER_STREAM_RESIDENT')}
    if receipt['residency']['mode'] != 'none' and receipt['residency']['require_confirmed'] and bad:
        return refuse(u, path, receipt, shot, 'RESIDENCY_NOT_CONFIRMED', textures=bad)
    check(not image.exists() and not list(image.parent.glob(image.stem + '.INVALIDATED*.png')), 'Preserve existing image')
    shot.update({'state': 'REQUESTING', 'request_utc': utc(), 'request_frame': frames, 'camera_at_request': state,
                 'render_proof': proof['status']})
    write_json(path, receipt)
    task = u.AutomationLibrary.take_high_res_screenshot(WIDTH, HEIGHT, str(image), delay=receipt['settings']['screenshot_delay'],
                                                        force_game_view=True)                  # GP native_capture_epic_resident.py:206-207
    if task is not None:
        registry().TASKS[(receipt['label'], shot['index'])] = task                      # stored first; kept until end sees it done
    valid = bool(task and task.is_valid_task())
    if not valid:
        registry().TASKS.pop((receipt['label'], shot['index']), None)                  # IsValidTask false: no screenshot was set up
    shot['valid_task'] = valid
    shot['state'] = 'REQUESTED' if valid else 'FAILED'
    shot['post_request'] = {'dirty_unchanged': dirty(u) == receipt['dirty_begin'],
                            'key_unchanged': str(level.get_active_viewport_config_key()) == receipt['priors']['active_viewport_key'],
                            'view_mode': view_mode_name(u, u.AutomationLibrary.get_editor_active_viewport_view_mode())}   # GP :211-214
    phase_log(receipt, 'request', frames, 'REQUESTED' if valid else 'INVALID_TASK', index=shot['index'])
    write_json(path, receipt)
    check(valid, 'Native screenshot task is invalid')
    check(shot['post_request']['dirty_unchanged'], 'Screenshot request changed dirty packages')
    return {'receipt': str(path), 'index': shot['index'], 'state': 'REQUESTED', 'image': str(image),
            'next': 'poll for the PNG, then mode=complete with the same index'}


def complete(u, args):
    path, receipt, _ = load_receipt(u, args)
    check(receipt['status'] == 'ACTIVE', 'Capture is not active: ' + receipt['status'])
    shot = shot_of(receipt, args)
    check(shot['state'] == 'REQUESTED', 'Shot must be REQUESTED, is ' + shot['state'])
    done = task_done(registry().TASKS.get((receipt['label'], shot['index'])))          # AutomationBlueprintFunctionLibrary.h:46-47
    image = image_path_for(stage_dir(u), receipt['label'], shot['index'], shot['shot'])
    check(str(image) == shot['image'], 'Receipt image path differs from the derived path')
    if done is False or not image.exists():
        return {'receipt': str(path), 'index': shot['index'], 'state': 'PENDING', 'task_done': done, 'image_exists': image.exists()}
    info = png_info(image)
    if not (info['signature_ok'] and info['iend_present']):
        return {'receipt': str(path), 'index': shot['index'], 'state': 'PENDING', 'png': info}
    _, world, level, editor, key, d = light_guard(u, receipt)
    after = camera_state(u, level, editor, key)
    verdict = camera_verdict(after, receipt['cameras']['presets'][shot['shot']], receipt['settings']['viewmode'])
    evidence = {'dimensions_match': [info['width'], info['height']] == [WIDTH, HEIGHT],
                'camera_and_view_mode_match_after_capture': verdict['all_match'],
                'exposure_locked_after_capture': exposure_still_locked(u, receipt),
                'dirty_unchanged_after_capture': d == receipt['dirty_begin']}
    reasons = sorted(k for k, v in evidence.items() if not v)
    proof = shot.get('render_proof') or 'RENDER_PROOF_NOT_RECORDED'
    if proof != 'STREAMER_VIEW_AT_CAMERA':          # e.g. RENDER_PROOF_UNAVAILABLE: no streamed bound texture had a view record
        reasons.append(proof)
    state = 'CAPTURED' if not reasons else 'CAPTURED_UNQUALIFIED'
    shot.update(dict(evidence, state=state, unqualified_reasons=reasons, captured_utc=utc(), task_done=done, png=info,
                     camera_after_capture=after, camera_verdict_after_capture=verdict))
    registry().TASKS.pop((receipt['label'], shot['index']), None)
    phase_log(receipt, 'complete', frame_count(u), state, index=shot['index'], reasons=reasons)
    write_json(path, receipt)
    check(evidence['dirty_unchanged_after_capture'], 'Dirty packages changed during capture')
    return {'receipt': str(path), 'index': shot['index'], 'state': state, 'unqualified_reasons': reasons, 'png': info}


def restore_cvars(u, world, rows):
    """Restore whitelisted cvars (RESTORABLE_CVARS) with numeric priors, newest first; anything else is refused and
    reported, never sent to the console. 'restored' is True only when the string readback equals the prior."""
    good, refused = restorable_rows(rows)
    out = list(refused)
    for row in reversed(good):
        try:
            readback = set_cvar(u, world, row['name'], row['prior'])
            out.append({'name': row['name'], 'restored_to': row['prior'], 'readback': readback, 'restored': readback == row['prior']})
        except Exception as error:
            out.append({'name': row['name'], 'error': repr(error), 'restored': False})
    return out


def sweep_images(u, receipt):
    """Quarantine (rename) every PNG at a non-CAPTURED shot path; drop registry tasks that are now done."""
    stage, label = stage_dir(u), receipt['label']
    actions = []
    for s in receipt['shots']:
        if s['state'] in CAPTURED_STATES:
            continue
        src = image_path_for(stage, label, s['index'], s['shot'])
        if src.exists():
            row = dict(quarantine_png(src), shot_index=s['index'], shot_state=s['state'])
            s.setdefault('quarantine', []).append(row)
            actions.append(row)
    for (lab, idx), task in list(registry().TASKS.items()):
        if lab == label and task_done(task) is True:
            registry().TASKS.pop((lab, idx), None)
    return {'utc': utc(), 'quarantined': actions, 'tasks_still_live': live_tasks(label)}


def end(u, args):
    path, receipt, script_check = load_receipt(u, args, allow_script_change=True)
    label, prior_status = receipt['label'], receipt['status']
    delay = (receipt.get('settings') or {}).get('screenshot_delay', 2.0)
    later = ('call mode=end again after >= %s s to quarantine late PNGs and re-check game view '
             '(a late force_game_view shot can turn it back on)' % delay)
    if prior_status in ('COMPLETED', 'ENDED_INCOMPLETE'):
        sweep = sweep_images(u, receipt)
        sweep['game_view'] = restore_game_view(u.get_editor_subsystem(u.LevelEditorSubsystem), receipt)
        gv_failed = sweep['game_view'].get('restored') is False
        if sweep['quarantined'] or sweep['game_view'].get('action') == 'SET' or gv_failed:
            receipt.setdefault('post_end_sweeps', []).append(sweep)
            phase_log(receipt, 'end_sweep', frame_count(u), 'SWEPT', count=len(sweep['quarantined']),
                      game_view=sweep['game_view'].get('status'))
            write_json(path, receipt)
        nxt = [later] if sweep['tasks_still_live'] else []
        if gv_failed:
            nxt.append('GAME_VIEW_NOT_RESTORED: use restore_fallback.game_view manually')
        return {'receipt': str(path), 'status': prior_status, 'note': 'already ended', 'script_check': script_check,
                'image_sweep': sweep, 'next': nxt or None}
    retry = prior_status == 'ENDED_PRESERVATION_CHECK_FAILED'
    tasks = registry().TASKS
    pending = sorted({idx for _, idx, _ in live_tasks(label)} |
                     {s['index'] for s in receipt['shots'] if s['state'] in ('REQUESTED', 'REQUESTING')
                      and task_done(tasks.get((label, s['index']))) is not True})
    unvalidated = [s['index'] for s in receipt['shots'] if s['state'] == 'REQUESTED' and s['index'] not in pending]
    if not retry and (pending or unvalidated) and args.get('cancel') is not True:
        return {'receipt': str(path), 'status': prior_status, 'refused': 'SCREENSHOT_PENDING_OR_NOT_COMPLETED',
                'pending_indices': pending, 'requested_not_completed': unvalidated, 'script_check': script_check,
                'next': 'complete those shots first, or end with cancel=true (their PNGs are then quarantined)'}
    invalidated_images = []
    for s in receipt['shots']:
        if s['index'] in pending and s['state'] != INVALIDATED:
            s['state_before_invalidation'] = s['state']
            s['state'] = INVALIDATED
            img = image_path_for(stage_dir(u), label, s['index'], s['shot'])
            seen = {'index': s['index'], 'path': str(img), 'utc': utc(), 'exists': img.exists()}
            if seen['exists']:
                try:
                    seen['sha256'] = sha_file(img)
                except Exception as error:
                    seen['sha256'] = 'READ_FAILED:' + repr(error)
            s['image_at_end'] = seen          # recorded before restore/sweep, present or absent
            invalidated_images.append(seen)
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    world = editor.get_editor_world()
    if retry:
        receipt.setdefault('end_history', []).append(receipt.get('end'))
    entry = registry().ACTIVE.get(label)
    if isinstance(entry, dict) and isinstance(entry.get('applied_cvars'), list):
        rows, source = entry['applied_cvars'], 'REGISTRY'
    else:
        rows, source = receipt.get('applied_cvars') or [], 'RECEIPT_WHITELISTED'
    receipt_rows = [(r.get('name'), r.get('prior')) for r in receipt.get('applied_cvars') or [] if isinstance(r, dict)]
    out = {'utc': utc(), 'retry_of': prior_status if retry else None, 'cancel': args.get('cancel') is True,
           'script_check': script_check, 'invalidated_pending': pending, 'invalidated_images_at_end': invalidated_images,
           'native_cancel': NATIVE_CANCEL,
           'cvar_restore_source': source,
           'receipt_rows_match_registry': ([(r.get('name'), r.get('prior')) for r in rows] == receipt_rows) if source == 'REGISTRY' else None,
           'cvar_restore': restore_cvars(u, world, rows), 'restore_priority_note': RESTORE_PRIORITY_NOTE}
    out['cvars_restored'] = all(r.get('restored') is True for r in out['cvar_restore'])
    out['requested_not_completed'] = [s['index'] for s in receipt['shots'] if s['state'] == 'REQUESTED']
    ui = {'game_view': restore_game_view(level, receipt)}
    if retry:
        ui['camera'] = 'SKIPPED_ON_RETRY'
    else:
        try:
            key = level.get_active_viewport_config_key()
            if receipt['settings']['restore_ui'] and str(key) == receipt['priors']['active_viewport_key'] and level.get_pilot_level_actor(key) is None:
                prior = receipt['priors']['camera']
                set_camera(u, level, editor, key, prior['keyed']['eye'], prior['keyed']['rotation'], prior['keyed']['fov'])
                editor.set_level_viewport_camera_info(u.Vector(*prior['primary']['eye']), u.Rotator(pitch=prior['primary']['rotation'][0],
                                                      yaw=prior['primary']['rotation'][1], roll=prior['primary']['rotation'][2]))
                u.AutomationLibrary.set_editor_active_viewport_view_mode(getattr(u.ViewModeIndex, prior['view_mode']))
                level.editor_invalidate_viewports()
                ui['camera'] = camera_state(u, level, editor, key)
            else:
                ui['camera'] = 'SKIPPED (restore_ui false, key changed or piloting)'
        except Exception as error:
            ui['camera'] = 'FAILED:' + repr(error)
    out['ui_restored'] = ui
    game_view_ok = ui['game_view'].get('restored') is True or ui['game_view'].get('status') == 'PRIOR_UNKNOWN'
    root = project_root(u)
    now_cvars = all_cvars(u)
    out['cvars_equal_priors'] = now_cvars == receipt['priors']['cvars']
    out['cvar_differences'] = {g: {k: [receipt['priors']['cvars'][g].get(k), v] for k, v in vals.items() if receipt['priors']['cvars'][g].get(k) != v}
                               for g, vals in now_cvars.items()}
    checks = (('texture_props_unchanged', lambda: {p: texture_props(u.load_asset(p)) for p in receipt['residency']['textures']}
               == receipt['residency']['texture_props_begin']),
              ('dirty', lambda: dirty(u)),
              ('disk_unchanged', lambda: {f: disk_state(f) for f in receipt['disk_begin']} == receipt['disk_begin']),
              ('material_end', lambda: material_readback(u, u.load_asset(receipt['child']))))
    for name, fn in checks:
        try:
            out[name] = fn()
        except Exception as error:
            out[name] = 'FAILED:' + repr(error)
    out['dirty_unchanged'] = out['dirty'] == receipt['dirty_begin']
    ini_file = root / 'Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini'
    if ini_file.exists():
        out['saved_viewport_preference_end'] = parse_viewport_ini(ini_file.read_text(encoding='utf-8-sig', errors='replace'),
                                                                  receipt['priors']['active_viewport_key'])
    log_file = stage_dir(u) / ('CAPTURE_' + label + '_LOG.txt')
    if log_file.exists():
        out['log_slice'] = {'status': 'ALREADY_WRITTEN', 'file': str(log_file), 'sha256': sha_file(log_file)}
    else:
        try:
            text, end_offset = read_log(u, world, receipt['log'], receipt['log'].get('begin_offset'))
        except Exception as error:
            text, end_offset = '', 'FAILED:' + repr(error)
        if text:
            with log_file.open('x', encoding='utf-8') as f:
                f.write(text)
            out['log_slice'] = {'file': str(log_file), 'sha256': sha_file(log_file), 'end_offset': end_offset, 'scan': log_scan(text)}
        else:
            out['log_slice'] = {'status': 'NOT_WRITTEN', 'log': receipt['log']['status'], 'end_offset': end_offset}
    out['image_sweep'] = sweep_images(u, receipt)
    all_captured = all(s['state'] == 'CAPTURED' for s in receipt['shots'])
    preserved = (all(out.get(k) is True for k in ('cvars_equal_priors', 'texture_props_unchanged', 'dirty_unchanged', 'disk_unchanged'))
                 and out['cvars_restored'] and game_view_ok)
    receipt['status'] = ('COMPLETED' if all_captured and preserved and not pending and not out['requested_not_completed'] else
                         'ENDED_PRESERVATION_CHECK_FAILED' if not preserved else 'ENDED_INCOMPLETE')
    if out['cvars_restored'] and game_view_ok:
        registry().ACTIVE.pop(label, None)
        out['registry'] = 'RELEASED'
    else:   # keep (or recreate) the entry: later begins refuse and a repeated end retries from the same rows
        good, _ = restorable_rows(rows)
        registry().ACTIVE[label] = dict(entry if isinstance(entry, dict) else
                                        {'tick_handle': None, 'receipt': str(path), 'applied_cvars': [dict(r) for r in good]},
                                        state='RESTORE_INCOMPLETE')
        out['registry'] = 'RESTORE_INCOMPLETE (later begins refuse; call mode=end again)'
    out['next'] = later if out['image_sweep']['tasks_still_live'] else None
    receipt['end'] = out
    phase_log(receipt, 'end', frame_count(u), receipt['status'], retry=retry)
    write_json(path, receipt)
    return {'receipt': str(path), 'status': receipt['status'], 'cvars_restored': out['cvars_restored'],
            'cvars_equal_priors': out['cvars_equal_priors'], 'game_view': ui['game_view'].get('status'),
            'dirty_unchanged': out['dirty_unchanged'], 'disk_unchanged': out['disk_unchanged'], 'script_check': script_check,
            'quarantined': [q.get('to') or q.get('status') for q in out['image_sweep']['quarantined']], 'next': out['next'],
            'images': [s['image'] for s in receipt['shots'] if s['state'] == 'CAPTURED']}


def status(u, args):
    """Read-only: no editor or file changes."""
    path, receipt, script_check = load_receipt(u, args, allow_script_change=True)
    stage, label = stage_dir(u), receipt['label']
    unvalidated = [{'index': s['index'], 'state': s['state'], 'path': str(image_path_for(stage, label, s['index'], s['shot']))}
                   for s in receipt['shots'] if s['state'] not in CAPTURED_STATES
                   and image_path_for(stage, label, s['index'], s['shot']).exists()]
    return {'receipt': str(path), 'status': receipt['status'], 'active': sorted(registry().ACTIVE),
            'registry_state': (registry().ACTIVE.get(label) or {}).get('state'), 'live_tasks': live_tasks(label),
            'script_check': script_check, 'unvalidated_png_present': unvalidated,
            'next': ('complete REQUESTED shots; PNGs at other non-captured shot paths are not captures and mode=end '
                     'quarantines them') if unvalidated else None,
            'shots': [{k: s.get(k) for k in ('index', 'shot', 'state', 'image', 'render_proof')} for s in receipt['shots']]}


def run(args):
    u = _u()
    mode = args.get('mode')
    phases = {'begin': begin, 'prepare': prepare, 'request': request, 'complete': complete, 'end': end, 'status': status}
    check(mode in phases, 'mode must be one of %s' % sorted(phases))
    if mode != 'begin':
        load_receipt(u, args, allow_script_change=mode in ('end', 'status'))
        if mode in ('prepare', 'request', 'complete'):
            try:
                return phases[mode](u, args)
            except Exception as error:
                path, receipt, _ = load_receipt(u, args, allow_script_change=True)   # record the error, never mask it
                if isinstance(args.get('index'), int) and 0 <= args['index'] < len(receipt['shots']):
                    shot = receipt['shots'][args['index']]
                    shot.setdefault('errors', []).append({'utc': utc(), 'phase': mode, 'error': repr(error)})
                    if shot['state'] in ('REQUESTING',):
                        shot['state'] = 'FAILED'    # a live registry task still makes end require cancel + quarantine
                phase_log(receipt, mode, None, 'FAILED', index=args.get('index'), error=repr(error))
                write_json(path, receipt)
                raise
    return phases[mode](u, args)


if 'ARGS' in globals():
    RESULT = run(ARGS)
