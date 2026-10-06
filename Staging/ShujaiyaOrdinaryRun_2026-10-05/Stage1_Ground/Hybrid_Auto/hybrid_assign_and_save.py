"""Hybrid ground (GazaShujaiya): area MI MI_GeoCityGround_Auto, Landscape assignment and NAMED save. In-editor only.
Fork of PathB_MW/pathb_assign_and_save.py (same channel, guard, receipt and identity conventions).

Run through the manager's UnrealCopilot client (Operator/copilot_client.py -> run_unreal_skill inline exec:
ARGS global in, RESULT global out; runner.py:221-236). No file/name dunders and no top-level main().
A failed run writes its receipt first and then RAISES, so the client exits 1. Import without ARGS is idle.

Modes (the build PID, one lease; plan PLAN_HYBRID.md):
  inspect  READ-ONLY: bound BUILT_VERIFIED_NO_SAVE receipt of this PID; M_GeoCityAuto in memory with the build's
           graph digest; DesertExample's 99 MW parameters read live; Landscape (64 components, scale); MI absent;
           MI_GeoCityGround_MW absent; dirty == ([M_GeoCityAuto], []).
  apply    create/update /Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_Auto
           (parent M_GeoCityAuto): DesertExample's 13 scalar + 11 texture overrides replicated, 12 static switches
           (5 MW Procedurals OFF, 5 Advanced ON, Water OFF, Snow ON), 5 ColorCorrection tints (ARGS, P1), Urban
           parameters (ARGS, bounded; Urban_GridCm = measured Landscape scale X; the 4 Urban textures explicit =
           the build's set). Parity gate: all 99 MW parameters read back vs live DesertExample; the differing set
           must equal exactly the 6 forced switches + the tints that differ (11 with P1). Assigns the single
           Landscape; all 64 components bound. NO save. <= 5 applies per PID; re-apply re-tunes.
           purpose 'mask_proof' (high-contrast Urban_Tint) can never be saved; purpose 'look' can.
  save     scope 'master_mi_map' only: after Aviv's approval receipt (sha-bound, this PID, latest apply).
           save_packages([M_GeoCityAuto]) -> save_packages([MI_GeoCityGround_Auto]) -> save_map(Shujaiya); dirty
           ([], []) after; MW vendor, protected files and pins unchanged; anchored log scan since the build clean.
Never: Save All, save_assets([]), Cook/Bake/recook, prepare()/verify_landscape(), vendor (MW) or Natural asset
edits, the MCP get_material_info tool, profile/ledger/lease writes. Writes only Hybrid_Auto/receipts/.

ARGS (all modes): mode, label, expected_pid (int), lease_owner, manager_thread_id, operator_thread_id,
  script_file (absolute path of THIS file), script_sha256, profile_sha256 (P'), expected_map_sha256,
  vendor_sha256 {desert, master}, build_receipt, build_receipt_sha256.
apply: purpose ('mask_proof'|'look'), tints {5 TINT_PARAMS: [r, g, b] in [0.25, 3.0]},
  urban {Urban_Amount, Urban_PadAmount, Urban_RoadAmount, Urban_TileCm, Urban_FarScale, Urban_FarDistanceCm,
         Urban_RoughnessScale, Urban_NormalStrength, Urban_Specular, Urban_Tint [r, g, b]} (bounds in URBAN_BOUNDS).
save: scope 'master_mi_map', apply_receipt, apply_receipt_sha256, approval_receipt, approval_receipt_sha256.
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

SCHEMA = 'environmentpipeline.ground_hybrid_assign.v1'
BUILD_SCHEMA = 'environmentpipeline.ground_hybrid_master.v1'
APPROVAL_SCHEMA = 'environmentpipeline.hybrid_visual_approval.v1'
MAP = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
AREA_ROOT = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015'
MI_NAME = 'MI_GeoCityGround_Auto'
MI_PKG = AREA_ROOT + '/Materials/' + MI_NAME
MI_PATH = MI_PKG + '.' + MI_NAME
PATHB_MI_PKG = AREA_ROOT + '/Materials/MI_GeoCityGround_MW'
PATHB_MI_PATH = PATHB_MI_PKG + '.MI_GeoCityGround_MW'
OLD_MI_PATH = AREA_ROOT + '/Materials/MI_GeoCityGround.MI_GeoCityGround'
COPY_PKG = '/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto'
COPY_OBJ = COPY_PKG + '.M_GeoCityAuto'
DESERT = '/Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.MTL_MWAM_Landscape_DesertExample'
VENDOR_OBJ = '/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER'
OWNER_TAG, OWNER_VALUE = 'GeoCityOwner', 'GeoCity_GroundHybrid_20261006'
LEASE_OWNER, SCOPE = 'GEOCITY_GROUND_HYBRID', 'GeoCity_GroundHybrid_20261006_auto_material'
AUTHORING, READONLY = 'GROUND_HYBRID_AUTHORING', ('STARTUP_INSPECTION_ONLY',)
PROFILE_REL = 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
STAGE_REL = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/Hybrid_Auto'
OUT_REL = STAGE_REL + '/receipts'
HELPER_REL = 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py'
HELPER_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
VENDOR_REL = 'Content/MWLandscapeAutoMaterial'
VENDOR_FILES = {'desert': 'Content/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.uasset',
                'master': 'Content/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.uasset'}
COPY_FILE = 'Content/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto.uasset'
MI_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_Auto.uasset'
PATHB_MI_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW.uasset'
MAP_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
_TEX = 'Content/ModularCourtyard/Textures/'
PROTECTED_FILES = ('Content/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.uasset',
                   'Content/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural.uasset',
                   'Content/Project/Shared/SurfacePainting/Appearance_20261003/LG_GeoCity_PermittedGroundGrass.uasset',
                   'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround.uasset',
                   'Content/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround.uasset',
                   _TEX + 'Asphalt/Asphalt_cracked/T_asphalt_cracked_AO.uasset',
                   _TEX + 'Asphalt/Asphalt_cracked/T_asphalt_cracked_basecolor.uasset',
                   _TEX + 'Asphalt/Asphalt_cracked/T_asphalt_cracked_normal.uasset',
                   _TEX + 'Asphalt/Asphalt_cracked/T_asphalt_cracked_roughness.uasset',
                   _TEX + 'Concrete_plate/T_Concrete_plate_BaseColor.uasset',
                   _TEX + 'Concrete_plate/T_Concrete_plate_Normal.uasset',
                   _TEX + 'Concrete_plate/T_Concrete_plate_ORM.uasset')
PROCEDURALS = ('MW_[x]_UseRockProcedurals', 'MW_[x]_UseStonesProcedurals', 'MW_[x]_UseGrassProcedurals',
               'MW_[x]_UseDirtProcedurals', 'MW_[x]_UseSnowProcedurals')       # only feed LandscapeGrassOutput_0
ADVANCED = ('MW_[x]_UseSnowAdvanced', 'MW_[x]_UseStonesAdvanced', 'MW_[x]_UseRockAdvanced',
            'MW_[x]_UseDirtAdvanced', 'MW_[x]_UseGrassAdvanced')                # gate ColorCorrection (MF_MWAM_DefaultLayer)
SET_SWITCHES = dict([(n, False) for n in PROCEDURALS] + [(n, True) for n in ADVANCED] +
                    [('MW_UseWater', False), ('MW_UseSnow', True)])
TINT_PARAMS = ('MW_SnowColorCorrection', 'MW_GrassColorCorrection', 'MW_DirtColorCorrection',
               'MW_StonesColorCorrection', 'MW_RockColorCorrection')
# DesertExample's measured overrides (MW_INVENTORY.json / native_inventory_complete.json, 2026-10-05; pathb :70-82).
DESERT_SCALARS = {'MW_SnowWorldPosition': 0.0, 'MW_DirtNormalIntensity': 1.0, 'MW_DirtSlopePower': 512.0,
                  'MW_GrassNormalIntensity': 0.75, 'MW_GrassSlopePower': 4.0, 'MW_GrassSpecular': 1.0,
                  'MW_StonesSlopePower': 0.699999988079071, 'MW_VariationWorldUVSize': 128.0,
                  'MW_RoughnessMultiplier': 1.2999999523162842, 'MW_RoughnessPower': 1.2000000476837158,
                  'MW_LandscapeWorldUVSize': 512.0, 'MW_LandscapeWorldUVSizeFar': 6144.0, 'RefractionDepthBias': 0.0}
_G = '/Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_'
DESERT_TEXTURES = {'MW_TextureSnowBaseColor': _G + 'SandA_col.TEX_MWAM_SandA_col', 'MW_TextureSnowNormal': _G + 'SandA_nrm.TEX_MWAM_SandA_nrm',
                   'MW_TextureDirtBaseColor': _G + 'SandA_col.TEX_MWAM_SandA_col', 'MW_TextureDirtNormal': _G + 'SandA_nrm.TEX_MWAM_SandA_nrm',
                   'MW_TextureGrassBaseColor': _G + 'SandA_col.TEX_MWAM_SandA_col', 'MW_TextureGrassNormal': _G + 'SandA_nrm.TEX_MWAM_SandA_nrm',
                   'MW_TextureStonesBaseColor': _G + 'SandC_col.TEX_MWAM_SandC_col', 'MW_TextureStonesNormal': _G + 'SandC_nrm.TEX_MWAM_SandC_nrm',
                   'MW_TextureRockBaseColor': _G + 'Stones_col.TEX_MWAM_Stones_col', 'MW_TextureRockNormal': _G + 'Stones_nrm.TEX_MWAM_Stones_nrm',
                   'MW_TextureLandscapeVariationMask': '/Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk'}
# M (native_inventory_complete.json): DesertExample has Dirt/Stones/Rock Procedurals ON and Snow/Stones/Rock Advanced
# OFF; Water OFF, Snow ON, Grass/Snow Procedurals OFF and Dirt/Grass Advanced ON already match SET_SWITCHES.
FORCED_SWITCH_DIFFS = ('MW_[x]_UseDirtProcedurals', 'MW_[x]_UseStonesProcedurals', 'MW_[x]_UseRockProcedurals',
                       'MW_[x]_UseSnowAdvanced', 'MW_[x]_UseStonesAdvanced', 'MW_[x]_UseRockAdvanced')
MW_PARAM_COUNT = 99                                            # M: 56 scalar + 24 switch + 12 texture + 7 vector
URBAN_NAMES = {'scalars': ('Urban_Amount', 'Urban_PadAmount', 'Urban_RoadAmount', 'Urban_TileCm', 'Urban_FarScale',
                           'Urban_FarDistanceCm', 'Urban_GridCm', 'Urban_RoughnessScale', 'Urban_NormalStrength',
                           'Urban_Specular'),
               'vectors': ('Urban_Tint',), 'textures': ('Urban_BaseColor', 'Urban_Normal', 'Urban_Roughness', 'Urban_AO'),
               'switches': ()}
URBAN_BOUNDS = {'Urban_Amount': (0.0, 1.0), 'Urban_PadAmount': (0.0, 1.0), 'Urban_RoadAmount': (0.0, 1.0),
                'Urban_TileCm': (50.0, 5000.0), 'Urban_FarScale': (1.0, 32.0), 'Urban_FarDistanceCm': (500.0, 100000.0),
                'Urban_RoughnessScale': (0.25, 2.0), 'Urban_NormalStrength': (0.0, 2.0), 'Urban_Specular': (0.0, 1.0)}
TINT_BOUNDS = (0.25, 3.0)
EXPECTED_COMPONENTS = 64                                        # M: PathB apply receipt PID34928
MAX_APPLY, TOL = 5, 1e-4
LOG_FAILURE_MARKERS = ('Failed to compile Material', 'Default Material will be used', ': Error:')
LOG_NAMES = ('M_GeoCityAuto', 'MI_GeoCityGround_Auto', 'Auto_20261006')
SHA = re.compile(r'^[0-9a-f]{64}$')
COMMON = {'mode', 'label', 'expected_pid', 'lease_owner', 'manager_thread_id', 'operator_thread_id', 'script_file',
          'script_sha256', 'profile_sha256', 'expected_map_sha256', 'vendor_sha256', 'build_receipt', 'build_receipt_sha256'}
KEYS = {'inspect': COMMON, 'apply': COMMON | {'purpose', 'tints', 'urban'},
        'save': COMMON | {'scope', 'apply_receipt', 'apply_receipt_sha256', 'approval_receipt', 'approval_receipt_sha256'}}


# ------------------------------------------------------------------ pure helpers (offline-safe)
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
    return dict(re.findall(r'(?:^|\s)([A-Za-z_]+)=([^\s]+)', line))      # geocity_editor_action.py:17-18


def code_signature(code):
    constants = tuple(code_signature(v) if isinstance(v, types.CodeType) else v for v in code.co_consts)
    return (code.co_code, constants, code.co_names, code.co_varnames, code.co_freevars, code.co_cellvars,
            code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def rgb_ok(value, low, high):
    return isinstance(value, list) and len(value) == 3 and all(number(v) and low <= v <= high for v in value)


def close(a, b, tol=TOL):
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if number(a) and number(b):
        return abs(float(a) - float(b)) <= tol
    return a == b


def values_equal(a, b):
    """Full MI value tables {kind: {name: value}} equal within TOL."""
    return set(a) == set(b) and all(set(a[k]) == set(b[k]) and all(close(a[k][n], b[k][n]) for n in a[k]) for k in a)


def parity(desert, mi, tints):
    """99 MW parameters: MI vs live DesertExample. Returns (rows, differing names, expected differing names)."""
    rows, diff = {}, []
    for kind in ('scalars', 'vectors', 'textures', 'switches'):
        for name in sorted(desert[kind]):
            same = close(desert[kind][name], mi[kind].get(name, '<MISSING>'))
            rows[kind + ':' + name] = {'desert': desert[kind][name], 'mi': mi[kind].get(name, '<MISSING>'), 'equal': same}
            if not same:
                diff.append(name)
    expected = set(FORCED_SWITCH_DIFFS) | {n for n in TINT_PARAMS if not close(desert['vectors'][n][:3], tints[n])}
    return rows, sorted(diff), sorted(expected)


def validate(args):
    mode = args.get('mode')
    need(mode in KEYS, 'mode must be inspect|apply|save')
    need(not (KEYS[mode] - set(args)), 'Missing ARGS keys: %s' % sorted(KEYS[mode] - set(args)))
    need(not (set(args) - KEYS[mode]), 'Unknown ARGS keys: %s' % sorted(set(args) - KEYS[mode]))
    need(token(args.get('label')), 'label: ascii [A-Za-z0-9_-]')
    need(isinstance(args.get('expected_pid'), int) and not isinstance(args.get('expected_pid'), bool), 'expected_pid int')
    for key in ('lease_owner', 'manager_thread_id', 'operator_thread_id'):
        need(token(args.get(key), 64) and args[key] != 'NONE', key + ' required')
    for key in ('script_sha256', 'profile_sha256', 'expected_map_sha256', 'build_receipt_sha256'):
        need(isinstance(args.get(key), str) and SHA.match(args[key]), key + ' must be a sha256')
    need(isinstance(args.get('build_receipt'), str) and args['build_receipt'].endswith('.json'), 'build_receipt path')
    v = args.get('vendor_sha256')
    need(isinstance(v, dict) and set(v) == set(VENDOR_FILES) and all(isinstance(x, str) and SHA.match(x) for x in v.values()),
         'vendor_sha256 {desert, master}')
    if mode in ('apply', 'save'):
        need(args.get('lease_owner') == LEASE_OWNER, mode + ' requires lease_owner ' + LEASE_OWNER)
    if mode == 'apply':
        need(args.get('purpose') in ('mask_proof', 'look'), "purpose must be 'mask_proof' or 'look'")
        tints = args.get('tints')
        need(isinstance(tints, dict) and set(tints) == set(TINT_PARAMS), 'tints must give exactly ' + str(TINT_PARAMS))
        for name, rgb in tints.items():
            need(rgb_ok(rgb, *TINT_BOUNDS), 'tint out of %s: %s' % (TINT_BOUNDS, name))
        urban = args.get('urban')
        need(isinstance(urban, dict) and set(urban) == set(URBAN_BOUNDS) | {'Urban_Tint'},
             'urban must give exactly %s + Urban_Tint (Urban_GridCm is measured, never an arg)' % sorted(URBAN_BOUNDS))
        for name, (low, high) in URBAN_BOUNDS.items():
            need(number(urban[name]) and low <= urban[name] <= high, '%s out of [%s, %s]' % (name, low, high))
        need(rgb_ok(urban['Urban_Tint'], *TINT_BOUNDS), 'Urban_Tint out of %s' % (TINT_BOUNDS,))
    if mode == 'save':
        need(args.get('scope') == 'master_mi_map', "scope must be 'master_mi_map'")
        for key in ('apply_receipt_sha256', 'approval_receipt_sha256'):
            need(isinstance(args.get(key), str) and SHA.match(args[key]), key + ' must be a sha256')
        for key in ('apply_receipt', 'approval_receipt'):
            need(isinstance(args.get(key), str) and args[key].endswith('.json'), key + ' path')
    return mode


def verify_identity(args):
    script = Path(args['script_file'])
    need(script.is_absolute() and script.is_file() and script.parent.name == 'Hybrid_Auto'
         and script.name == 'hybrid_assign_and_save.py', 'script_file must be the Hybrid_Auto/hybrid_assign_and_save.py copy')
    source = script.read_bytes()
    need(sha_bytes(source) == args['script_sha256'], 'Unreviewed script bytes (sha256 differs)')
    need(code_signature(_EXECUTED_CODE) == code_signature(compile(source, str(script), 'exec')),
         'Executed code differs from script_file')
    return str(script)


def vendor_snapshot(root):
    rows = {}
    for path in sorted((root / VENDOR_REL).rglob('*')):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            stat = path.stat()
            small = rel.startswith((VENDOR_REL + '/Materials/', VENDOR_REL + '/Procedurals/')) and path.suffix == '.uasset'
            rows[rel] = [stat.st_size, stat.st_mtime_ns, sha_file(path) if small else None]
    return rows


def sole_editor():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq UnrealEditor.exe', '/FO', 'CSV', '/NH'], capture_output=True,
                         text=True, timeout=30, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout
    return sorted(int(row.split('","')[1]) for row in out.splitlines() if row.startswith('"UnrealEditor.exe"'))


def disk(root):
    return {'map': sha_file(root / MAP_FILE), 'copy': sha_file(root / COPY_FILE), 'mi': sha_file(root / MI_FILE),
            'pathb_mi': sha_file(root / PATHB_MI_FILE),
            'protected': {rel: sha_file(root / rel) for rel in PROTECTED_FILES},
            'vendor_pins': {k: sha_file(root / rel) for k, rel in VENDOR_FILES.items()}}


def short(path):
    return path.rsplit(':', 1)[1] if isinstance(path, str) and ':' in path else path


def strip_guids(rows):
    return {k: dict(v, properties={p: x for p, x in v['properties'].items() if p not in ('expression_guid', 'material_expression_guid')})
            for k, v in rows.items()}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


# ------------------------------------------------------------------ editor helpers (lazy unreal)
def _p(obj):
    return obj.get_path_name() if obj else None


def dirty(u):
    return (sorted(_p(p) for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
            sorted(_p(p) for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()))


def chain_of(u, material):
    out = []
    while material is not None and len(out) < 8:
        out.append(_p(material))
        material = material.get_editor_property('parent') if isinstance(material, u.MaterialInstance) else None
    return out


def guard(u, root, args, mode):
    pid = os.getpid()
    need(args['expected_pid'] == pid, 'expected_pid %s is not this editor PID %s' % (args['expected_pid'], pid))
    lines = [x for x in (root / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
    lease = lines[-1]
    f = lease_fields(lease)
    need(f.get('OWNER') == args['lease_owner'], 'Last lease OWNER differs from ARGS lease_owner')
    need(f.get('assigned_editor_PID') == str(pid), 'Last lease is not assigned to this PID')
    need(f.get('map') == MAP, 'Last lease map is not GazaShujaiya')
    need(f.get('manager_thread_id') == args['manager_thread_id'] and f.get('operator_thread_id') == args['operator_thread_id'],
         'Lease manager/operator thread ids differ')
    authoring = f.get('activation') == AUTHORING and f.get('scope') == SCOPE and f.get('OWNER') == LEASE_OWNER
    need(authoring or (mode == 'inspect' and f.get('activation') in READONLY),
         'Lease %s/%s does not permit %s' % (f.get('activation'), f.get('scope'), mode))
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    need(world.get_outermost().get_path_name() == MAP, 'Editor world is not the GazaShujaiya map')
    need(not u.get_editor_subsystem(u.LevelEditorSubsystem).is_in_play_in_editor(), 'PIE is active')
    api = u.HoudiniPublicAPIBlueprintLib.get_api()
    need(api.is_asset_cooking_paused(), 'Houdini Engine cooking must be paused')
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    hdas = [a for a in actors if a.get_class().get_name() == 'HoudiniAssetActor']
    need(len(hdas) == 1, 'Expected exactly one HDA actor, found %d' % len(hdas))
    w = u.HoudiniPublicAPIAssetWrapper.create_wrapper(None, hdas[0])
    need(not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled(), 'HDA auto cook/bake must be off')
    need(not u.get_default_object(u.load_class(None, '/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
         'Editor autosave must be off')
    need(not any(getattr(r, k, None) is not None for n in ('geocity_bank_workflow', 'geocity_roadbld_workflow')
                 for r in getattr(sys.modules.get(n), 'ACTIVE', []) for k in ('watch_tick', 'save_tick', 'tick_handle')),
         'A managed GeoCity workflow tick is active')
    pids = sole_editor()
    need(pids == [pid], 'Exactly this one UnrealEditor.exe must run: %s' % pids)
    lands = [a for a in actors if isinstance(a, u.Landscape)]
    proxies = [a for a in actors if isinstance(a, u.LandscapeProxy) and not isinstance(a, u.Landscape)]
    need(len(lands) == 1 and not proxies, 'Need exactly one Landscape and no streaming proxies: %d/%d' % (len(lands), len(proxies)))
    need(lands[0].get_outermost().get_path_name() == MAP, 'Landscape actor is not stored in the map package (external actor?)')
    return {'pid': pid, 'lease': lease, 'lease_kind': 'authoring' if authoring else 'readonly', 'world': MAP,
            'hda_actors': 1, 'cooking_paused': True, 'autosave': False, 'editor_pids': pids, 'landscape': _p(lands[0])}, world, lands[0]


def landscape_state(u, land):
    comps = list(land.get_components_by_class(u.LandscapeComponent))
    chains = [chain_of(u, c.get_material(0)) for c in comps]
    grass = list(land.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent))
    scale = land.get_actor_scale3d()
    return {'landscape_material': _p(land.get_editor_property('landscape_material')),
            'components': len(comps), 'components_bound_to_auto_mi': sum(MI_PATH in c for c in chains),
            'components_bound_to_old_mi': sum(OLD_MI_PATH in c for c in chains),
            'components_bound_to_pathb_mi': sum(PATHB_MI_PATH in c for c in chains),
            'sample_component_chain': chains[0] if chains else [],
            'scale': [float(scale.x), float(scale.y), float(scale.z)],
            'landscape_hism_components': len(grass), 'landscape_hism_instances': sum(c.get_instance_count() for c in grass),
            'hism_note': 'grass/scatter cache is viewer-dependent; MW procedural switches OFF are the real no-grass control'}


def mi_values(u, lib, mi):
    """Every parameter of the instance (effective values) by kind."""
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


def mi_state(u, lib, mi):
    if mi is None:
        return None
    return {'path': _p(mi), 'class': mi.get_class().get_name(), 'parent_chain': chain_of(u, mi.get_editor_property('parent')),
            'owner_tag': str(u.EditorAssetLibrary.get_metadata_tag(mi, OWNER_TAG)), 'values': mi_values(u, lib, mi)}


def load_helper(root):
    data = (root / HELPER_REL).read_bytes()
    need(sha_bytes(data) == HELPER_SHA, 'Frozen graph helper changed')
    module = types.ModuleType('hybrid_frozen_graph_helper')
    exec(compile(data, str(root / HELPER_REL), 'exec'), module.__dict__)
    need('ARGS' not in module.__dict__ and 'RESULT' not in module.__dict__, 'Helper executed a mode')
    return module


def master_digest(u, lib, h, master):
    """Same normalisation as hybrid_build_master.graph(): rows keyed by expression name, GUIDs excluded."""
    obj = h.path(master)
    rows = {short(h.path(e)): h.describe(master, e) for e in lib.get_material_expressions(master)}
    rows = json.loads(json.dumps(rows, sort_keys=True).replace(obj + ':', '').replace(obj, '<SELF>'))
    return digest(strip_guids(rows)), len(rows)


def read_profile(root, args):
    raw = (root / PROFILE_REL).read_bytes()
    profile = json.loads(raw.decode('utf-8'))
    ext = profile.get('external_landscape_material') or {}
    row = {'sha256': sha_bytes(raw), 'landscape_material': profile.get('landscape_material'),
           'landscape_grass_enabled': profile.get('landscape_grass', {}).get('enabled'), 'parent_chain': ext.get('parent_chain')}
    need(row['sha256'] == args['profile_sha256'], 'Profile sha256 differs from the reviewed patched profile (P\')')
    need(row['landscape_material'] == MI_PATH and row['landscape_grass_enabled'] is False and row['parent_chain'] == [COPY_OBJ],
         'Profile is not patched for the Hybrid')
    return row


def bound_json(root, file, expected_sha, under):
    path = Path(file).resolve()
    need(path.is_file() and path.is_relative_to((root / under).resolve()), 'Bound file outside %s: %s' % (under, path))
    raw = path.read_bytes()
    need(sha_bytes(raw) == expected_sha, 'Bound file sha256 differs: ' + str(path))
    return path, json.loads(raw.decode('utf-8'))


def build_receipt(root, args):
    _, built = bound_json(root, args['build_receipt'], args['build_receipt_sha256'], OUT_REL)
    need(built.get('schema') == BUILD_SCHEMA and built.get('mode') == 'build' and built.get('status') == 'BUILT_VERIFIED_NO_SAVE'
         and built.get('pid') == os.getpid(), 'Build receipt is not a verified build of this PID')
    return built


def check_master(u, lib, h, built):
    master = u.load_asset(COPY_OBJ)
    need(isinstance(master, u.Material), 'M_GeoCityAuto is not loaded as a Material')
    need(str(u.EditorAssetLibrary.get_metadata_tag(master, OWNER_TAG)) == OWNER_VALUE, 'M_GeoCityAuto owner tag')
    live, count = master_digest(u, lib, h, master)
    need(live == built['graph']['digest_noguid'] and count == built['graph']['rows'], 'M_GeoCityAuto graph differs from the build')
    return master, {'digest_noguid': live, 'rows': count}


def log_file(u):
    folder = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_log_dir()))
    return folder / (Path(u.Paths.get_project_file_path()).stem + '.log')


def log_scan(u, offset):
    file = log_file(u)
    data = file.read_bytes()
    need(len(data) >= offset, 'Editor log shrank/rotated since the recorded offset')
    lines = data[offset:].decode('utf-8', 'replace').splitlines()
    benign = re.compile(r'\berrors?\s*[=:]\s*0\b', re.I)
    word = re.compile(r'\b(error|errors|failed|failure)\b', re.I)
    named = [s for s in lines if any(n in s for n in LOG_NAMES) and not benign.search(s)
             and (word.search(s) or any(m in s for m in LOG_FAILURE_MARKERS))]
    unattributed = [s for s in lines if s not in named and (
        any(m in s for m in LOG_FAILURE_MARKERS[:2]) or
        (('LogMaterial' in s or 'LogShaderCompilers' in s) and LOG_FAILURE_MARKERS[2] in s))]
    return {'file': str(file), 'offset': offset, 'end': len(data), 'named_hits': named[:200],
            'unattributed_material_errors': unattributed[:200], 'clean': not named and not unattributed}


def receipt_path(root, mode, label, pid):
    return root / OUT_REL / ('HYBRID_ASSIGN_%s_%s_PID%s.json' % (mode.upper(), label, pid))


def write_receipt(root, receipt):
    path = receipt_path(root, receipt['mode'], receipt['label'], receipt['pid'])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2, default=str)
    return str(path)


# ------------------------------------------------------------------ modes
def do_inspect(u, lib, h, root, args, receipt):
    g, world, land = guard(u, root, args, 'inspect')
    d0 = dirty(u)
    built = build_receipt(root, args)
    master, live = check_master(u, lib, h, built)
    desert = u.load_asset(DESERT)
    need(desert is not None and chain_of(u, desert) == [DESERT, VENDOR_OBJ], 'DesertExample chain differs')
    dvals = mi_values(u, lib, desert)
    disk0 = disk(root)
    receipt.update(guard=g, dirty_before=d0, profile=read_profile(root, args), disk=disk0, master=live,
                   landscape=landscape_state(u, land), desert_values=dvals,
                   desert_param_count=sum(len(v) for v in dvals.values()),
                   mi_exists=bool(u.EditorAssetLibrary.does_asset_exist(MI_PKG)),
                   pathb_mi_exists=bool(u.EditorAssetLibrary.does_asset_exist(PATHB_MI_PKG)))
    need(d0 == ([COPY_PKG], []), 'Dirty state is not exactly the unsaved M_GeoCityAuto: %s' % (d0,))
    need(disk0['map'] == args['expected_map_sha256'] and disk0['vendor_pins'] == args['vendor_sha256'], 'Map/vendor pins differ')
    need(disk0 == built['disk_after'], 'Disk changed since the build')
    need(receipt['desert_param_count'] == MW_PARAM_COUNT, 'DesertExample does not expose 99 MW parameters')
    need(not receipt['pathb_mi_exists'] and disk0['pathb_mi'] is None, 'MI_GeoCityGround_MW exists (must stay absent)')
    need(receipt['landscape']['components'] == EXPECTED_COMPONENTS, 'Landscape component count differs from 64')
    d1 = dirty(u)
    receipt['dirty_after'] = d1
    need(d1 == d0, 'Inspection changed dirty packages: %s -> %s' % (d0, d1))
    return 'INSPECTED_READ_ONLY'


def do_apply(u, lib, h, root, args, receipt):
    g, world, land = guard(u, root, args, 'apply')
    out = root / OUT_REL
    prior = sorted(out.glob('HYBRID_ASSIGN_APPLY_*_PID%s.json' % os.getpid())) if out.is_dir() else []
    need(len(prior) < MAX_APPLY, 'Apply iteration limit (%d) reached in this PID' % MAX_APPLY)
    receipt['apply_iteration'] = len(prior) + 1
    built = build_receipt(root, args)
    profile = read_profile(root, args)
    disk0 = disk(root)
    need(disk0['map'] == args['expected_map_sha256'], 'Saved map differs from the reviewed baseline')
    need(disk0['vendor_pins'] == args['vendor_sha256'], 'MW vendor DesertExample/master files differ from the pins')
    need(disk0 == built['disk_after'], 'Disk changed since the build')
    vendor0 = vendor_snapshot(root)
    need(vendor0 == built['vendor_snapshot'], 'MW vendor snapshot changed since the build')
    d0 = dirty(u)
    need(not any(p.startswith('/Game/MWLandscapeAutoMaterial') for p in d0[0]), 'MW vendor packages are dirty; refuse')
    need(COPY_PKG in d0[0] and set(d0[0]) <= {COPY_PKG, MI_PKG} and set(d0[1]) <= {MAP},
         'Unreviewed dirty packages before apply: %s' % (d0,))
    need(not u.EditorAssetLibrary.does_asset_exist(PATHB_MI_PKG), 'MI_GeoCityGround_MW exists (must stay absent)')
    master, live = check_master(u, lib, h, built)
    desert = u.load_asset(DESERT)
    need(desert is not None and chain_of(u, desert) == [DESERT, VENDOR_OBJ], 'DesertExample chain differs')
    dvals = mi_values(u, lib, desert)
    need(sum(len(v) for v in dvals.values()) == MW_PARAM_COUNT, 'DesertExample does not expose 99 MW parameters')
    scale = land.get_actor_scale3d()
    grid = float(scale.x)
    need(math.isfinite(grid) and grid > 0 and abs(float(scale.x) - float(scale.y)) < 1e-3,
         'Landscape scale X/Y must be equal and positive for one Urban_GridCm: %s' % [scale.x, scale.y])
    receipt.update(guard=g, profile=profile, disk_before=disk0, dirty_before=d0, master=live,
                   build_receipt=args['build_receipt'], build_receipt_sha256=args['build_receipt_sha256'],
                   landscape_before=landscape_state(u, land), purpose=args['purpose'],
                   log={'file': str(log_file(u)), 'offset': log_file(u).stat().st_size})
    if u.EditorAssetLibrary.does_asset_exist(MI_PKG):
        mi = u.load_asset(MI_PATH)
        need(isinstance(mi, u.MaterialInstanceConstant) and str(u.EditorAssetLibrary.get_metadata_tag(mi, OWNER_TAG)) == OWNER_VALUE,
             'Existing MI_GeoCityGround_Auto is not a Hybrid-owned MaterialInstanceConstant')
        need(prior, 'MI_GeoCityGround_Auto exists before the first apply of this PID')
        receipt['mi_created'] = False
    else:
        mi = u.AssetToolsHelpers.get_asset_tools().create_asset(MI_NAME, AREA_ROOT + '/Materials',
                                                                  u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        need(mi is not None and _p(mi) == MI_PATH, 'MaterialInstanceConstant creation failed')
        u.EditorAssetLibrary.set_metadata_tag(mi, OWNER_TAG, OWNER_VALUE)
        receipt['mi_created'] = True
    receipt['mi_before'] = mi_state(u, lib, mi)
    lib.set_material_instance_parent(mi, master)
    setters = {}
    # Installed 5.8 setters can return False while applying (M: PathB PID34928, LW:375-377): readback is the proof.
    for name, value in SET_SWITCHES.items():
        setters['switch:' + name] = bool(lib.set_material_instance_static_switch_parameter_value(mi, name, value))
    for name, value in DESERT_SCALARS.items():
        setters['scalar:' + name] = bool(lib.set_material_instance_scalar_parameter_value(mi, name, value))
    for name, path in DESERT_TEXTURES.items():
        texture = u.load_asset(path)
        need(isinstance(texture, u.Texture), 'MW texture missing: ' + path)
        setters['texture:' + name] = bool(lib.set_material_instance_texture_parameter_value(mi, name, texture))
    for name in TINT_PARAMS:
        r, gg, b = args['tints'][name]
        setters['tint:' + name] = bool(lib.set_material_instance_vector_parameter_value(mi, name, u.LinearColor(r, gg, b, 1.0)))
    urban = dict(args['urban'], Urban_GridCm=grid)
    for name in URBAN_NAMES['scalars']:
        setters['urban:' + name] = bool(lib.set_material_instance_scalar_parameter_value(mi, name, float(urban[name])))
    r, gg, b = urban['Urban_Tint']
    setters['urban:Urban_Tint'] = bool(lib.set_material_instance_vector_parameter_value(mi, 'Urban_Tint', u.LinearColor(r, gg, b, 1.0)))
    urban_textures = built['parameters']['textures']
    need(sorted(urban_textures) == sorted(URBAN_NAMES['textures']), 'Build receipt Urban textures')
    for name, path in urban_textures.items():
        texture = u.load_asset(path)
        need(isinstance(texture, u.Texture2D), 'Urban texture missing: ' + path)
        setters['urban:' + name] = bool(lib.set_material_instance_texture_parameter_value(mi, name, texture))
    lib.update_material_instance(mi)
    state = mi_state(u, lib, mi)
    vals = state['values']
    receipt.update(setter_returns=setters, mi_after=state, urban_applied=urban, urban_textures=urban_textures)
    need(state['class'] == 'MaterialInstanceConstant' and state['owner_tag'] == OWNER_VALUE, 'MI class/owner readback')
    need(state['parent_chain'] == [COPY_OBJ], 'MI parent chain readback differs: ' + str(state['parent_chain']))
    for kind in ('scalars', 'vectors', 'textures', 'switches'):
        need(set(vals[kind]) == set(dvals[kind]) | set(URBAN_NAMES[kind]),
             'MI %s names differ from DesertExample + Urban: %s' % (kind, sorted(set(vals[kind]) ^ (set(dvals[kind]) | set(URBAN_NAMES[kind])))))
    need(all(vals['switches'][n] == v for n, v in SET_SWITCHES.items()), 'MI static switch readback differs')
    for name in TINT_PARAMS:
        need(close(vals['vectors'][name][:3], args['tints'][name]), 'Tint readback differs: ' + name)
    for name, value in DESERT_SCALARS.items():
        need(close(lib.get_material_instance_scalar_parameter_value(mi, name), value), 'Scalar readback: ' + name)
    for name, path in DESERT_TEXTURES.items():
        need(vals['textures'][name] == path, 'Texture readback: ' + name)
    for name in URBAN_NAMES['scalars']:
        need(close(vals['scalars'][name], urban[name]), 'Urban readback: ' + name)
    need(close(vals['vectors']['Urban_Tint'][:3], urban['Urban_Tint']), 'Urban_Tint readback')
    for name, path in urban_textures.items():
        need(vals['textures'][name] == path, 'Urban texture readback: ' + name)
    rows, diff, expected = parity(dvals, vals, args['tints'])
    receipt['parity'] = {'compared': len(rows), 'differing': diff, 'expected_differing': expected, 'rows': rows}
    need(len(rows) == MW_PARAM_COUNT and diff == expected,
         'Parity gate: differing %s != expected %s' % (diff, expected))
    land.set_editor_property('landscape_material', mi)
    after = landscape_state(u, land)
    receipt['landscape_after'] = after
    need(after['landscape_material'] == MI_PATH, 'Landscape material readback differs')
    need(after['components'] == EXPECTED_COMPONENTS and after['components_bound_to_auto_mi'] == EXPECTED_COMPONENTS
         and after['components_bound_to_old_mi'] == 0 and after['components_bound_to_pathb_mi'] == 0,
         'Not all 64 Landscape components bound to MI_GeoCityGround_Auto: %s' % after)
    d1 = dirty(u)
    receipt['dirty_after'] = d1
    need(set(d1[0]) <= {COPY_PKG, MI_PKG} and set(d1[1]) <= {MAP} and COPY_PKG in d1[0] and MI_PKG in d1[0],
         'Apply dirtied other packages (refuse save; exit without saving): %s' % (d1,))
    need(vendor_snapshot(root) == vendor0 and disk(root) == disk0, 'Disk changed during apply')
    receipt['log_scan_advisory'] = log_scan(u, receipt['log']['offset'])
    receipt['vendor_snapshot'] = vendor0
    return 'APPLIED_VERIFIED_NO_SAVE'


def do_save(u, lib, h, root, args, receipt):
    g, world, land = guard(u, root, args, 'save')
    pid = os.getpid()
    apply_path, applied = bound_json(root, args['apply_receipt'], args['apply_receipt_sha256'], OUT_REL)
    need(applied.get('schema') == SCHEMA and applied.get('mode') == 'apply' and applied.get('status') == 'APPLIED_VERIFIED_NO_SAVE'
         and applied.get('pid') == pid, 'Apply receipt is not a verified apply of this PID')
    latest = sorted((root / OUT_REL).glob('HYBRID_ASSIGN_APPLY_*_PID%s.json' % pid), key=lambda p: p.stat().st_mtime_ns)[-1]
    need(latest.resolve() == apply_path, 'Only the latest apply of this PID may be saved')
    need(applied['purpose'] == 'look', 'A mask-proof apply is never saved; re-apply with purpose look first')
    need(applied['build_receipt'] == args['build_receipt'] and applied['build_receipt_sha256'] == args['build_receipt_sha256'],
         'Apply and save name different build receipts')
    built = build_receipt(root, args)
    approval_path, approval = bound_json(root, args['approval_receipt'], args['approval_receipt_sha256'], STAGE_REL)
    need(approval.get('schema') == APPROVAL_SCHEMA and approval.get('save_approved') is True and approval.get('pid') == pid
         and approval.get('approved_by') == 'Aviv' and approval.get('apply_receipt_sha256') == args['apply_receipt_sha256'],
         'Approval receipt does not approve saving this apply in this PID')
    need(read_profile(root, args)['sha256'] == applied['profile']['sha256'], 'Profile changed since apply')
    need(disk(root) == applied['disk_before'] and vendor_snapshot(root) == applied['vendor_snapshot'], 'Disk changed since apply')
    master, live = check_master(u, lib, h, built)
    mi = u.load_asset(MI_PATH)
    state = mi_state(u, lib, mi)
    need(state['class'] == applied['mi_after']['class'] and state['parent_chain'] == applied['mi_after']['parent_chain']
         and state['owner_tag'] == OWNER_VALUE and values_equal(state['values'], applied['mi_after']['values']),
         'MI drifted since apply')
    land_now = landscape_state(u, land)
    need(land_now['landscape_material'] == MI_PATH and land_now['components_bound_to_auto_mi'] == EXPECTED_COMPONENTS,
         'Landscape is not bound to MI_GeoCityGround_Auto')
    need(not u.EditorAssetLibrary.does_asset_exist(PATHB_MI_PKG), 'MI_GeoCityGround_MW exists (must stay absent)')
    content, maps = dirty(u)
    need(content == sorted([COPY_PKG, MI_PKG]) and maps == [MAP], 'Dirty set is not exactly {master, MI} + map: %s' % ((content, maps),))
    scan = log_scan(u, built['log']['offset'])
    receipt.update(guard=g, apply_receipt=str(apply_path), apply_receipt_sha256=args['apply_receipt_sha256'],
                   approval_receipt=str(approval_path), approval_receipt_sha256=args['approval_receipt_sha256'],
                   build_receipt=args['build_receipt'], build_receipt_sha256=args['build_receipt_sha256'],
                   scope=args['scope'], dirty_before=[content, maps], master=live, mi=state, landscape=land_now,
                   disk_before=applied['disk_before'], log_scan_since_build=scan)
    need(scan['clean'], 'Material compile failure lines in the editor log since the build (STOP; exit without saving)')
    saved = []
    ok = u.EditorLoadingAndSavingUtils.save_packages([master.get_outermost()], False)     # named only (LW:382 pattern)
    need(ok and COPY_PKG not in dirty(u)[0] and sha_file(root / COPY_FILE), 'Named M_GeoCityAuto save failed')
    saved.append(COPY_PKG)
    ok = u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)
    need(ok and MI_PKG not in dirty(u)[0] and sha_file(root / MI_FILE), 'Named MI save failed')
    saved.append(MI_PKG)
    need(u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'Named map save failed')            # BW:901 pattern
    need(MAP not in dirty(u)[1], 'Map remains dirty after the named save')
    saved.append(MAP)
    after = disk(root)
    d_after = dirty(u)
    receipt.update(saved_packages=saved, disk_after=after, dirty_after=d_after, vendor_snapshot=applied['vendor_snapshot'],
                   vendor_unchanged=vendor_snapshot(root) == applied['vendor_snapshot'],
                   protected_unchanged=after['protected'] == applied['disk_before']['protected'],
                   explicit_save_scope=['save_packages(M_GeoCityAuto)', 'save_packages(MI_GeoCityGround_Auto)', 'save_map(Shujaiya)'])
    need(after['copy'] and after['mi'] and after['map'], 'A saved package file is missing')
    need(after['pathb_mi'] is None, 'MI_GeoCityGround_MW appeared on disk')
    need(d_after == ([], []), 'Packages remain dirty after the named save: %s' % (d_after,))
    need(receipt['vendor_unchanged'] and receipt['protected_unchanged'], 'Vendor or protected files changed during save')
    need(after['vendor_pins'] == applied['disk_before']['vendor_pins'] == args['vendor_sha256'], 'MW vendor pins changed')
    return 'SAVED_NAMED_ONLY'


def run(args):
    if not isinstance(args, dict) or not args.get('mode'):
        return {'ok': False, 'idle': True, 'reason': 'No ARGS.mode; nothing was done.'}
    mode = validate(args)
    script = verify_identity(args)
    import unreal as u
    lib = u.MaterialEditingLibrary
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    need(not receipt_path(root, mode, args['label'], os.getpid()).exists(), 'Receipt label already used in this PID; pick a new label')
    receipt = {'schema': SCHEMA, 'mode': mode, 'label': args['label'], 'pid': os.getpid(), 'utc_start': utc(),
               'executed_script': script, 'script_sha256': args['script_sha256'], 'args': args,
               'engine': u.SystemLibrary.get_engine_version(), 'status': 'STARTED'}
    try:
        h = load_helper(root)
        receipt['status'] = {'inspect': do_inspect, 'apply': do_apply, 'save': do_save}[mode](u, lib, h, root, args, receipt)
    except Exception as exc:
        receipt.update(status='FAILED_' + mode.upper(), error=repr(exc), utc_end=utc())
        receipt['receipt_file'] = write_receipt(root, receipt)
        raise
    receipt['utc_end'] = utc()
    receipt['receipt_file'] = write_receipt(root, receipt)
    return {'ok': True, 'status': receipt['status'], 'receipt': receipt['receipt_file'],
            'receipt_sha256': sha_file(receipt['receipt_file']),
            'landscape': receipt.get('landscape_after') or receipt.get('landscape'),
            'parity_differing': (receipt.get('parity') or {}).get('differing'), 'dirty_after': receipt.get('dirty_after')}


RESULT = run(globals().get('ARGS'))
