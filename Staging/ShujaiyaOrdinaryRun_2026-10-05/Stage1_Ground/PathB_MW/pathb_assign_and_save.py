"""Path B (GazaShujaiya): MW auto-landscape ground MI, Landscape assignment and NAMED save. In-editor only.

Run through the manager's UnrealCopilot client (Operator/copilot_client.py -> run_unreal_skill inline exec:
ARGS global in, RESULT global out; runner.py:221-236). No __file__/__name__/main() (runner.py:207-212).
A failed run writes its receipt first and then RAISES, so the client exits 1. Import without ARGS is idle.

Modes (one PID, one lease):
  inspect  read-only preconditions (lease STARTUP_INSPECTION_ONLY or GROUND_PATHB_AUTHORING).
  apply    create/update /Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW,
           parent DesertExample (recommended) or the MW master, 12 static switches (5 MW Grass/scatter
           procedurals OFF, 5 layer Advanced ON so ColorCorrection applies, Water OFF, Snow-slot ON),
           5 ColorCorrection tints from ARGS; optionally assign it to the single Landscape. NO save.
           Re-running apply in the same PID re-tints (max MAX_APPLY applies per PID).
  save     NAMED save only: scope 'mi_and_map' (MI package + map) or 'mi_only' (MI package; for the
           regeneration-proof option). Refuses if any other package is dirty or anything drifted since apply.
Never: Save All, save_assets([]), Cook/Bake/recook, prepare()/verify_landscape(), vendor (MW) or Natural
asset edits, the MCP get_material_info tool, profile/ledger/lease writes. Writes only PathB_MW/receipts/.

ARGS (all modes): mode, label [A-Za-z0-9_], expected_pid (int), lease_owner, manager_thread_id,
  operator_thread_id, script_file (absolute path of THIS reviewed file), script_sha256.
apply: profile_sha256, expected_map_sha256, parent ('desert'|'master'), tints {param: [r, g, b]} for the five
  TINT_PARAMS (each in [0.25, 3.0]; see TINT_PRESETS.json), assign_landscape (bool, default true),
  vendor_sha256 {desert, master} (pinned .uasset hashes).
save: profile_sha256, apply_receipt, apply_receipt_sha256, scope ('mi_and_map'|'mi_only').
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

_EXECUTED_CODE = sys._getframe(0).f_code   # pattern: S1_Prep/s1_verify.py:84,238-241,611

SCHEMA = 'environmentpipeline.pathb_mw_assign.v1'
MAP = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
AREA_ROOT = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015'
MI_PKG = AREA_ROOT + '/Materials/MI_GeoCityGround_MW'
MI_PATH = MI_PKG + '.MI_GeoCityGround_MW'
OLD_MI_PATH = AREA_ROOT + '/Materials/MI_GeoCityGround.MI_GeoCityGround'
DESERT = '/Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.MTL_MWAM_Landscape_DesertExample'
MASTER = '/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER'
CHAINS = {'desert': [DESERT, MASTER], 'master': [MASTER]}
OWNER_TAG, OWNER_VALUE = 'GeoCityOwner', 'GeoCity_GroundPathB_MW'   # not the GeoCity_LandscapeGrass owner
PROFILE_REL = 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
OUT_REL = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/PathB_MW/receipts'
VENDOR_REL = 'Content/MWLandscapeAutoMaterial'
VENDOR_FILES = {'desert': 'Content/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.uasset',
                'master': 'Content/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.uasset'}
PROTECTED_FILES = ('Content/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.uasset',
                   'Content/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural.uasset',
                   'Content/Project/Shared/SurfacePainting/Appearance_20261003/LG_GeoCity_PermittedGroundGrass.uasset',
                   'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround.uasset',
                   'Content/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround.uasset')
MI_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW.uasset'
MAP_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
PROCEDURALS = ('MW_[x]_UseRockProcedurals', 'MW_[x]_UseStonesProcedurals', 'MW_[x]_UseGrassProcedurals',
               'MW_[x]_UseDirtProcedurals', 'MW_[x]_UseSnowProcedurals')       # only feed LandscapeGrassOutput_0
ADVANCED = ('MW_[x]_UseSnowAdvanced', 'MW_[x]_UseStonesAdvanced', 'MW_[x]_UseRockAdvanced',
            'MW_[x]_UseDirtAdvanced', 'MW_[x]_UseGrassAdvanced')                # gate ColorCorrection (MF_MWAM_DefaultLayer)
SET_SWITCHES = dict([(n, False) for n in PROCEDURALS] + [(n, True) for n in ADVANCED] +
                    [('MW_UseWater', False), ('MW_UseSnow', True)])
EXPECTED_SWITCHES = dict(SET_SWITCHES, **{'MW_DebugBake': False, 'MW_DebugSnowWater': False,
                                          'MW_[x]_UseLandscapeVariation': True, 'MW_UseWorldPositionUVs': True})
TINT_PARAMS = ('MW_SnowColorCorrection', 'MW_GrassColorCorrection', 'MW_DirtColorCorrection',
               'MW_StonesColorCorrection', 'MW_RockColorCorrection')
# Master parent only: DesertExample's measured overrides (MW_INVENTORY.json, 2026-10-05). Dirt 1.25 is in the tints.
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
AUTHORING, READONLY = 'GROUND_PATHB_AUTHORING', ('STARTUP_INSPECTION_ONLY',)
MAX_APPLY, TOL = 4, 1e-4
COMMON = {'mode', 'label', 'expected_pid', 'lease_owner', 'manager_thread_id', 'operator_thread_id', 'script_file', 'script_sha256'}
KEYS = {'inspect': COMMON | {'profile_sha256', 'vendor_sha256'},
        'apply': COMMON | {'profile_sha256', 'expected_map_sha256', 'parent', 'tints', 'assign_landscape', 'vendor_sha256'},
        'save': COMMON | {'profile_sha256', 'apply_receipt', 'apply_receipt_sha256', 'scope'}}


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


def validate(args):
    mode = args.get('mode')
    need(mode in KEYS, 'mode must be inspect|apply|save')
    unknown = set(args) - KEYS[mode]
    need(not unknown, 'Unknown ARGS keys: %s' % sorted(unknown))
    need(token(args.get('label')), 'label: ascii [A-Za-z0-9_-]')
    need(isinstance(args.get('expected_pid'), int) and not isinstance(args.get('expected_pid'), bool), 'expected_pid int')
    for key in ('lease_owner', 'manager_thread_id', 'operator_thread_id'):
        need(token(args.get(key), 64) and args[key] != 'NONE', key + ' required')
    need(isinstance(args.get('script_sha256'), str) and len(args['script_sha256']) == 64, 'script_sha256 required')
    if mode in ('apply', 'save'):
        need(isinstance(args.get('profile_sha256'), str) and len(args['profile_sha256']) == 64, 'profile_sha256 required')
    if mode == 'apply':
        need(args.get('parent') in CHAINS, "parent must be 'desert' or 'master'")
        need(isinstance(args.get('expected_map_sha256'), str) and len(args['expected_map_sha256']) == 64, 'expected_map_sha256')
        tints = args.get('tints')
        need(isinstance(tints, dict) and set(tints) == set(TINT_PARAMS), 'tints must give exactly ' + str(TINT_PARAMS))
        for name, rgb in tints.items():
            need(isinstance(rgb, list) and len(rgb) == 3 and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                                                                 and 0.25 <= v <= 3.0 for v in rgb), 'tint out of [0.25, 3.0]: ' + name)
        need(isinstance(args.get('assign_landscape', True), bool), 'assign_landscape bool')
        need(isinstance(args.get('vendor_sha256'), dict) and set(args['vendor_sha256']) == set(VENDOR_FILES), 'vendor_sha256 {desert, master}')
    if mode == 'save':
        need(args.get('scope') in ('mi_and_map', 'mi_only'), "scope must be 'mi_and_map' or 'mi_only'")
        need(isinstance(args.get('apply_receipt'), str) and isinstance(args.get('apply_receipt_sha256'), str), 'apply receipt pin')
    return mode


def verify_identity(args):
    """The executed code must be exactly the pinned file (same compile flags: compile() inherits them)."""
    script = Path(args['script_file'])
    need(script.is_absolute() and script.is_file() and script.parent.name == 'PathB_MW', 'script_file must be the PathB_MW copy')
    source = script.read_bytes()
    need(sha_bytes(source) == args['script_sha256'], 'Unreviewed script bytes (sha256 differs)')
    need(code_signature(_EXECUTED_CODE) == code_signature(compile(source, str(script), 'exec')),
         'Executed code differs from script_file')
    return str(script)


def vendor_snapshot(root):
    """size/mtime for every MW file; sha256 for the small material/function/grass-type packages."""
    rows = {}
    base = root / VENDOR_REL
    for path in sorted(base.rglob('*')):
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
    allowed = (AUTHORING,) if mode in ('apply', 'save') else (AUTHORING,) + READONLY
    need(f.get('activation') in allowed, 'Lease activation %s does not permit %s' % (f.get('activation'), mode))
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
    return {'pid': pid, 'lease': lease, 'world': MAP, 'hda_actors': 1, 'cooking_paused': True, 'autosave': False,
            'editor_pids': pids, 'landscape': _p(lands[0])}, world, lands[0]


def landscape_state(u, land):
    comps = list(land.get_components_by_class(u.LandscapeComponent))
    chains = [chain_of(u, c.get_material(0)) for c in comps]
    grass = [c for c in land.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent)]
    return {'landscape_material': _p(land.get_editor_property('landscape_material')),
            'components': len(comps), 'components_bound_to_mw_mi': sum(MI_PATH in c for c in chains),
            'components_bound_to_old_mi': sum(OLD_MI_PATH in c for c in chains),
            'sample_component_chain': chains[0] if chains else [],
            'landscape_hism_components': len(grass),
            'landscape_hism_instances': sum(c.get_instance_count() for c in grass),
            'hism_note': 'grass/scatter cache is viewer-dependent; MW procedural switches OFF are the real no-grass control'}


def mi_state(u, lib, mi):
    if mi is None:
        return None
    names = {str(n) for n in lib.get_static_switch_parameter_names(mi)}
    tints = {}
    for name in TINT_PARAMS:
        c = lib.get_material_instance_vector_parameter_value(mi, name)
        tints[name] = [round(float(c.r), 6), round(float(c.g), 6), round(float(c.b), 6)]
    return {'path': _p(mi), 'class': mi.get_class().get_name(), 'parent_chain': chain_of(u, mi.get_editor_property('parent')),
            'owner_tag': str(u.EditorAssetLibrary.get_metadata_tag(mi, OWNER_TAG)),
            'switches': {n: (bool(lib.get_material_instance_static_switch_parameter_value(mi, n)) if n in names else 'MISSING')
                         for n in sorted(EXPECTED_SWITCHES)}, 'tints': tints}


def receipt_path(root, mode, label, pid):
    return root / OUT_REL / ('PATHB_%s_%s_PID%s.json' % (mode.upper(), label, pid))


def write_receipt(root, receipt):
    path = receipt_path(root, receipt['mode'], receipt['label'], receipt['pid'])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'x', encoding='utf-8') as stream:      # exclusive: never overwrite a receipt
        json.dump(receipt, stream, indent=2, default=str)
    return str(path)


def read_profile(root, args, require_patched):
    raw = (root / PROFILE_REL).read_bytes()
    profile = json.loads(raw.decode('utf-8'))
    row = {'sha256': sha_bytes(raw), 'landscape_material': profile.get('landscape_material'),
           'landscape_grass_enabled': profile.get('landscape_grass', {}).get('enabled'),
           'external_block': 'external_landscape_material' in profile}
    if require_patched:
        need(row['sha256'] == args['profile_sha256'], 'Profile sha256 differs from the reviewed patched profile')
        need(row['landscape_material'] == MI_PATH and row['landscape_grass_enabled'] is False,
             'Profile is not patched for Path B (landscape_material / landscape_grass.enabled)')
    return row


def disk(root):
    return {'map': sha_file(root / MAP_FILE), 'mi': sha_file(root / MI_FILE),
            'protected': {rel: sha_file(root / rel) for rel in PROTECTED_FILES},
            'vendor_pins': {k: sha_file(root / rel) for k, rel in VENDOR_FILES.items()}}


# ------------------------------------------------------------------ modes
def do_inspect(u, lib, root, args, receipt):
    g, world, land = guard(u, root, args, 'inspect')
    d0 = dirty(u)
    desert, master = u.load_asset(DESERT), u.load_asset(MASTER)
    switch_names = {str(n) for n in lib.get_static_switch_parameter_names(desert)} if desert else set()
    vector_names = {str(n) for n in lib.get_vector_parameter_names(desert)} if desert else set()
    receipt.update(guard=g, dirty_before=d0, profile=read_profile(root, args, False), disk=disk(root),
                   landscape=landscape_state(u, land),
                   mi_exists=bool(u.EditorAssetLibrary.does_asset_exist(MI_PKG)),
                   desert={'class': desert.get_class().get_name() if desert else None, 'chain': chain_of(u, desert),
                           'switches': {n: bool(lib.get_material_instance_static_switch_parameter_value(desert, n))
                                        for n in sorted(EXPECTED_SWITCHES) if n in switch_names},
                           'missing_switch_names': sorted(set(EXPECTED_SWITCHES) - switch_names),
                           'missing_tint_names': sorted(set(TINT_PARAMS) - vector_names)},
                   master_class=master.get_class().get_name() if master else None)
    if args.get('vendor_sha256'):
        receipt['vendor_pins_match'] = receipt['disk']['vendor_pins'] == args['vendor_sha256']
    d1 = dirty(u)
    receipt['dirty_after'] = d1
    need(d1 == d0, 'Inspection changed dirty packages: %s -> %s' % (d0, d1))
    need(not receipt['desert']['missing_switch_names'] and not receipt['desert']['missing_tint_names'],
         'MW parameter names missing on DesertExample')
    return 'INSPECTED_READ_ONLY'


def do_apply(u, lib, root, args, receipt):
    g, world, land = guard(u, root, args, 'apply')
    out = root / OUT_REL
    prior = sorted(out.glob('PATHB_APPLY_*_PID%s.json' % os.getpid())) if out.is_dir() else []
    need(len(prior) < MAX_APPLY, 'Apply iteration limit (%d) reached in this PID' % MAX_APPLY)
    receipt['apply_iteration'] = len(prior) + 1
    profile = read_profile(root, args, True)
    disk0 = disk(root)
    need(disk0['map'] == args['expected_map_sha256'], 'Saved map differs from the reviewed baseline')
    need(disk0['vendor_pins'] == args['vendor_sha256'], 'MW vendor DesertExample/master files differ from the pins')
    vendor0 = vendor_snapshot(root)
    d0 = dirty(u)
    need(not any(p.startswith('/Game/MWLandscapeAutoMaterial') for p in d0[0]), 'MW vendor packages are dirty; refuse')
    allowed0 = ({MI_PKG}, {MAP}) if prior else (set(), set())
    need(set(d0[0]) <= allowed0[0] and set(d0[1]) <= allowed0[1], 'Unreviewed dirty packages before apply: %s' % (d0,))
    receipt.update(guard=g, profile=profile, disk_before=disk0, dirty_before=d0, landscape_before=landscape_state(u, land))
    parent = u.load_asset(CHAINS[args['parent']][0])
    need(parent is not None and chain_of(u, parent) == CHAINS[args['parent']], 'MW parent chain differs: ' + str(chain_of(u, parent)))
    setters = {}
    if u.EditorAssetLibrary.does_asset_exist(MI_PKG):
        mi = u.load_asset(MI_PATH)
        need(isinstance(mi, u.MaterialInstanceConstant) and str(u.EditorAssetLibrary.get_metadata_tag(mi, OWNER_TAG)) == OWNER_VALUE,
             'Existing MI_GeoCityGround_MW is not a Path B-owned MaterialInstanceConstant')
        receipt['mi_created'] = False
    else:
        # Measured creation pattern LW:358-366: plain factory, then set_material_instance_parent below.
        mi = u.AssetToolsHelpers.get_asset_tools().create_asset('MI_GeoCityGround_MW', AREA_ROOT + '/Materials',
                                                                  u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        need(mi is not None and _p(mi) == MI_PATH, 'MaterialInstanceConstant creation failed')
        u.EditorAssetLibrary.set_metadata_tag(mi, OWNER_TAG, OWNER_VALUE)
        receipt['mi_created'] = True
    receipt['mi_before'] = mi_state(u, lib, mi)
    lib.set_material_instance_parent(mi, parent)
    # Installed 5.8 setters can return False while applying (LW:375-377): readback is the proof.
    for name, value in SET_SWITCHES.items():
        setters['switch:' + name] = bool(lib.set_material_instance_static_switch_parameter_value(mi, name, value))
    if args['parent'] == 'master':
        for name, value in DESERT_SCALARS.items():
            setters['scalar:' + name] = bool(lib.set_material_instance_scalar_parameter_value(mi, name, value))
        for name, path in DESERT_TEXTURES.items():
            texture = u.load_asset(path)
            need(isinstance(texture, u.Texture), 'MW texture missing: ' + path)
            setters['texture:' + name] = bool(lib.set_material_instance_texture_parameter_value(mi, name, texture))
    for name in TINT_PARAMS:
        r, gg, b = args['tints'][name]
        setters['tint:' + name] = bool(lib.set_material_instance_vector_parameter_value(mi, name, u.LinearColor(r, gg, b, 1.0)))
    lib.update_material_instance(mi)
    state = mi_state(u, lib, mi)
    receipt.update(setter_returns=setters, mi_after=state)
    need(state['class'] == 'MaterialInstanceConstant' and state['owner_tag'] == OWNER_VALUE, 'MI class/owner readback')
    need(state['parent_chain'] == CHAINS[args['parent']], 'MI parent chain readback differs: ' + str(state['parent_chain']))
    need(state['switches'] == EXPECTED_SWITCHES, 'MI static switch readback differs: ' + json.dumps(state['switches']))
    for name in TINT_PARAMS:
        need(all(abs(a - b) < TOL for a, b in zip(state['tints'][name], args['tints'][name])), 'Tint readback differs: ' + name)
    if args['parent'] == 'master':
        for name, value in DESERT_SCALARS.items():
            need(abs(lib.get_material_instance_scalar_parameter_value(mi, name) - value) < TOL, 'Scalar readback: ' + name)
        for name, path in DESERT_TEXTURES.items():
            need(_p(lib.get_material_instance_texture_parameter_value(mi, name)) == path, 'Texture readback: ' + name)
    if args.get('assign_landscape', True):
        land.set_editor_property('landscape_material', mi)
    after = landscape_state(u, land)
    receipt['landscape_after'] = after
    if args.get('assign_landscape', True):
        need(after['landscape_material'] == MI_PATH, 'Landscape material readback differs')
        need(after['components_bound_to_old_mi'] == 0 and after['components_bound_to_mw_mi'] >= 1,
             'Landscape component material instances did not rebind to the MW MI')
    else:
        need(after['landscape_material'] == receipt['landscape_before']['landscape_material'], 'Landscape changed without assign')
    d1 = dirty(u)
    receipt['dirty_after'] = d1
    need(set(d1[0]) <= {MI_PKG} and set(d1[1]) <= {MAP}, 'Apply dirtied other packages (refuse save; exit without saving): %s' % (d1,))
    need(vendor_snapshot(root) == vendor0 and disk(root) == disk0, 'Disk changed during apply')
    receipt['vendor_snapshot'] = vendor0
    receipt['parent'] = args['parent']
    receipt['assign_landscape'] = bool(args.get('assign_landscape', True))
    return 'APPLIED_VERIFIED_NO_SAVE'


def do_save(u, lib, root, args, receipt):
    g, world, land = guard(u, root, args, 'save')
    apply_path = Path(args['apply_receipt'])
    raw = apply_path.read_bytes()
    need(sha_bytes(raw) == args['apply_receipt_sha256'], 'Apply receipt sha256 differs')
    applied = json.loads(raw.decode('utf-8'))
    need(applied.get('schema') == SCHEMA and applied.get('status') == 'APPLIED_VERIFIED_NO_SAVE'
         and applied.get('pid') == os.getpid(), 'Apply receipt is not a verified apply of this PID')
    latest = sorted((root / OUT_REL).glob('PATHB_APPLY_*_PID%s.json' % os.getpid()), key=lambda p: p.stat().st_mtime_ns)[-1]
    need(latest.resolve() == apply_path.resolve(), 'Only the latest apply of this PID may be saved')
    need(read_profile(root, args, True)['sha256'] == applied['profile']['sha256'], 'Profile changed since apply')
    need(disk(root) == applied['disk_before'] and vendor_snapshot(root) == applied['vendor_snapshot'], 'Disk changed since apply')
    mi = u.load_asset(MI_PATH)
    state = mi_state(u, lib, mi)
    need(state == applied['mi_after'], 'MI drifted since apply')
    land_now = landscape_state(u, land)
    scope = args['scope']
    content, maps = dirty(u)
    need(not any(p.startswith('/Game/MWLandscapeAutoMaterial') for p in content), 'MW vendor packages are dirty; refuse')
    if scope == 'mi_and_map':
        need(applied['assign_landscape'] and land_now['landscape_material'] == MI_PATH, 'Landscape is not bound to the MW MI')
        need(set(content) <= {MI_PKG} and set(maps) <= {MAP}, 'Other packages are dirty; refuse: %s' % ((content, maps),))
    else:
        need(not applied['assign_landscape'] and land_now['landscape_material'] == applied['landscape_before']['landscape_material'],
             'mi_only requires an apply with assign_landscape=false')
        need(set(content) <= {MI_PKG} and not maps, 'Other packages are dirty; refuse: %s' % ((content, maps),))
    receipt.update(guard=g, apply_receipt=str(apply_path), apply_receipt_sha256=args['apply_receipt_sha256'], scope=scope,
                   dirty_before=[content, maps], mi=state, landscape=land_now, disk_before=applied['disk_before'])
    saved = []
    if MI_PKG in content or applied['disk_before']['mi'] is None:
        ok = u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)     # LW:382 pattern, named only
        need(ok and MI_PKG not in dirty(u)[0], 'Named MI save failed')
        saved.append(MI_PKG)
    if scope == 'mi_and_map':
        need(u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'Named map save failed')      # BW:901 pattern
        need(MAP not in dirty(u)[1], 'Map remains dirty after the named save')
        saved.append(MAP)
    after = disk(root)
    d_after = dirty(u)
    receipt.update(saved_packages=saved, disk_after=after, dirty_after=d_after,
                   vendor_unchanged=vendor_snapshot(root) == applied['vendor_snapshot'],
                   protected_unchanged=after['protected'] == applied['disk_before']['protected'])
    need(after['mi'] is not None, 'MI package file missing after save')
    need(d_after == ([], []), 'Packages remain dirty after the named save: %s' % (d_after,))
    need(receipt['vendor_unchanged'] and receipt['protected_unchanged'], 'Vendor or protected files changed during save')
    need(after['vendor_pins'] == applied['disk_before']['vendor_pins'], 'MW vendor pins changed')
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
        receipt['status'] = {'inspect': do_inspect, 'apply': do_apply, 'save': do_save}[mode](u, lib, root, args, receipt)
    except Exception as exc:
        receipt.update(status='FAILED_' + mode.upper(), error=repr(exc), utc_end=utc())
        receipt['receipt_file'] = write_receipt(root, receipt)
        raise
    receipt['utc_end'] = utc()
    receipt['receipt_file'] = write_receipt(root, receipt)
    return {'ok': True, 'status': receipt['status'], 'receipt': receipt['receipt_file'],
            'receipt_sha256': sha_file(receipt['receipt_file']),
            'landscape': receipt.get('landscape_after') or receipt.get('landscape'), 'dirty_after': receipt.get('dirty_after')}


RESULT = run(globals().get('ARGS'))
