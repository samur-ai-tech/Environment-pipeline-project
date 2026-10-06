"""Hybrid ground (GazaShujaiya): build the project-owned auto-landscape master M_GeoCityAuto. In-editor only.

Run through the manager's UnrealCopilot client (Operator/copilot_client.py -> run_unreal_skill inline exec:
ARGS global in, RESULT global out; runner.py:221-236). No file/name dunders and no top-level main().
A failed run writes its receipt first and then RAISES, so the client exits 1. Import without ARGS is idle.

Modes (one PID, one lease; plan PLAN_HYBRID.md "Scripts"):
  inspect  READ-ONLY. Lease GROUND_HYBRID_AUTHORING (scope exact) or STARTUP_INSPECTION_ONLY. Vendor pins +
           vendor snapshot; profile already patched (P'); saved map = expected; Urban texture rows for BOTH sets
           (sRGB / compression / LOD group / VT -> derived sampler type); MW master graph dump (190 rows,
           normalised); MakeMaterialAttributes_0 wiring read from a T3D export of the MW master (AssetExportTask +
           ObjectExporterT3D -> receipts/HYBRID_T3D_<label>_vendor_PID<pid>.t3d): each pin's (Expression,
           OutputIndex) resolved against MaterialFunctionCall_14's Outputs(N) names = mma_true_outputs; asserted
           BaseColor <- StaticSwitchParameter_16 MW_DebugBake output 0; Metallic/Specular/Roughness/Normal <-
           MW_MWAM_Water output named like the pin; AmbientOcclusion unconnected. (MEASURED PID23068: the legacy
           get_input_node_output_name_for_material_expression returns ONE name per (target, source) pair, 'Metallic'
           for all four MF_14 pins, so it is recorded as advisory only); M_GeoCityAuto, MI_GeoCityGround_Auto and
           MI_GeoCityGround_MW absent; dirty ([], []) before and after.
           Texture rule (Aviv 2026-10-06): Asphalt_cracked basecolor COLOR, normal NORMAL, roughness/AO LINEAR
           (sRGB off), VT off. If Asphalt fails and the documented fallback Concrete_plate passes, status
           STOP_TEXTURE_FALLBACK_REQUIRED (receipt written, then raise). Never edits a texture.
  build    Same PID as a bound inspect receipt; ONE build attempt per PID (HYBRID_BUILD_ONCE_PID<pid>.json latch).
           EditorAssetLibrary.duplicate_asset(MW master -> /Game/Project/Shared/SurfacePainting/Auto_20261006/
           M_GeoCityAuto); copied graph == vendor graph (rows keyed by expression name, vendor object path
           rewritten to the copy, expression GUIDs advisory); adds the Urban graph (desc prefix
           'GeoCity_GroundHybrid_20261006:', canvas x>=2500, y>=1400, every new sample Shared:Wrap) exactly as
           HYBRID_EDIT_EXPECTATIONS.json (sha-bound, generated offline from THIS script's bytes); re-points
           MakeMaterialAttributes_0 BaseColor/Normal/Roughness/Specular to Lerps and connects AmbientOcclusion; the
           Lerp A-inputs use the T3D-resolved true output names (copy T3D must equal the vendor's MMA_0 wiring);
           after the edit a second T3D export proves MMA_0 pins and every new node's (source, OutputIndex) set;
           gates: 190+N rows, the other 189 vendor rows byte-equal, MMA_0 exactly those 5 pins changed, all
           material roots unchanged, the 4 layer samples + RemoveFoliage present and reachable, every new node
           reachable from MMA_0, recompile_material == [], samplers <= 3, anchored log scan clean, dirty exactly
           ([M_GeoCityAuto], []), MW vendor files/pins unchanged. Status BUILT_VERIFIED_NO_SAVE. NO SAVE.
Never: Save All, save_assets([]), any save, Cook/Bake/recook, prepare()/verify_landscape(), vendor (MW) edits,
texture edits, the MCP get_material_info tool, profile/ledger/lease writes. Writes only Hybrid_Auto/receipts/.
A failed or stopped build leaves an UNSAVED copy in memory: close the editor WITHOUT saving; rebuild in a new PID.

ARGS (all modes): mode, label [A-Za-z0-9_-], expected_pid (int), lease_owner, manager_thread_id,
  operator_thread_id, script_file (absolute path of THIS reviewed file), script_sha256, profile_sha256 (P'),
  expected_map_sha256, vendor_sha256 {desert, master}.
build: + inspect_receipt, inspect_receipt_sha256, texture_set ('asphalt_cracked'|'concrete_plate'),
  expectations_file, expectations_sha256, fallback_acknowledged_by_manager (bool, only for concrete_plate).
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

_EXECUTED_CODE = sys._getframe(0).f_code   # pattern: S1_Prep/s1_verify.py, PathB_MW/pathb_assign_and_save.py

SCHEMA = 'environmentpipeline.ground_hybrid_master.v1'
MARK = 'GeoCity_GroundHybrid_20261006:'
OWNER_TAG, OWNER_VALUE = 'GeoCityOwner', 'GeoCity_GroundHybrid_20261006'
LEASE_OWNER, SCOPE = 'GEOCITY_GROUND_HYBRID', 'GeoCity_GroundHybrid_20261006_auto_material'
AUTHORING, READONLY = 'GROUND_HYBRID_AUTHORING', ('STARTUP_INSPECTION_ONLY',)
MAP = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
AREA_ROOT = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015'
MI_PKG = AREA_ROOT + '/Materials/MI_GeoCityGround_Auto'
MI_PATH = MI_PKG + '.MI_GeoCityGround_Auto'
PATHB_MI_PKG = AREA_ROOT + '/Materials/MI_GeoCityGround_MW'
PATHB_MI_PATH = PATHB_MI_PKG + '.MI_GeoCityGround_MW'
VENDOR_PKG = '/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER'
VENDOR_OBJ = VENDOR_PKG + '.MTL_MWAM_AutoMaterial_MASTER'
COPY_DIR = '/Game/Project/Shared/SurfacePainting/Auto_20261006'
COPY_PKG = COPY_DIR + '/M_GeoCityAuto'
COPY_OBJ = COPY_PKG + '.M_GeoCityAuto'
WATER_FUNCTION = '/Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MW_MWAM_Water.MW_MWAM_Water'
PROFILE_REL = 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
STAGE_REL = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/Hybrid_Auto'
OUT_REL = STAGE_REL + '/receipts'
HELPER_REL = 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py'
HELPER_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'     # frozen describe/digest (S1 pin)
VENDOR_REL = 'Content/MWLandscapeAutoMaterial'
VENDOR_FILES = {'desert': 'Content/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.uasset',
                'master': 'Content/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.uasset'}
COPY_FILE = 'Content/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto.uasset'
COPY_DIR_FILE = 'Content/Project/Shared/SurfacePainting/Auto_20261006'
MI_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_Auto.uasset'
PATHB_MI_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW.uasset'
MAP_FILE = 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
_ASPHALT = '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_'
_CONCRETE = '/Game/ModularCourtyard/Textures/Concrete_plate/T_Concrete_plate_'
# Urban texture sets: Aviv 2026-10-06 chose Asphalt_cracked (separate roughness/AO maps); Concrete_plate is the
# documented fallback (ORM: R=AO, G=Roughness by the usual ORM convention, I). Same parameter names either way.
TEXTURE_SETS = {
    'asphalt_cracked': {'textures': {'Urban_BaseColor': (_ASPHALT + 'basecolor.T_asphalt_cracked_basecolor', 'color'),
                                     'Urban_Normal': (_ASPHALT + 'normal.T_asphalt_cracked_normal', 'normal'),
                                     'Urban_Roughness': (_ASPHALT + 'roughness.T_asphalt_cracked_roughness', 'linear'),
                                     'Urban_AO': (_ASPHALT + 'AO.T_asphalt_cracked_AO', 'linear')},
                        'channels': {'roughness': 'R', 'ao': 'R'}},
    'concrete_plate': {'textures': {'Urban_BaseColor': (_CONCRETE + 'BaseColor.T_Concrete_plate_BaseColor', 'color'),
                                    'Urban_Normal': (_CONCRETE + 'Normal.T_Concrete_plate_Normal', 'normal'),
                                    'Urban_Roughness': (_CONCRETE + 'ORM.T_Concrete_plate_ORM', 'linear'),
                                    'Urban_AO': (_CONCRETE + 'ORM.T_Concrete_plate_ORM', 'linear')},
                       'channels': {'roughness': 'G', 'ao': 'R'}}}
PREFERRED_SET, FALLBACK_SET = 'asphalt_cracked', 'concrete_plate'
TEXTURE_FILES = sorted({'Content/' + p.split('.')[0][len('/Game/'):] + '.uasset'
                        for s in TEXTURE_SETS.values() for p, _ in s['textures'].values()})
PROTECTED_FILES = tuple(['Content/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.uasset',
                         'Content/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural.uasset',
                         'Content/Project/Shared/SurfacePainting/Appearance_20261003/LG_GeoCity_PermittedGroundGrass.uasset',
                         'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround.uasset',
                         'Content/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround.uasset']
                        + TEXTURE_FILES)
LAYERS = ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')     # Ground/Steep/RoadBed/BuildingPad (LW:18-19)
MW_LAYER = 'RemoveFoliage'                                    # M: the MW master's own LandscapeLayerSample_1
VENDOR_NODE_COUNT = 190                                       # M: native_inventory_complete.json
MMA = 'MaterialExpressionMakeMaterialAttributes_0'
SSP16 = 'MaterialExpressionStaticSwitchParameter_16'           # MW_DebugBake -> MMA_0.BaseColor (M)
MF14 = 'MaterialExpressionMaterialFunctionCall_14'             # MW_MWAM_Water -> MMA_0 Metallic/Specular/Roughness/Normal (M)
MMA_SOURCES = {'BaseColor': SSP16, 'Metallic': MF14, 'Specular': MF14, 'Roughness': MF14, 'Normal': MF14}
# T3D expression reference: Expression="<class>'<material>:<expression>'" followed (inside the same struct) by
# optional ,OutputIndex=N (omitted when 0), e.g. MMA_0 'Specular=(Expression="...MaterialFunctionCall_14'",OutputIndex=2)'
# (M: Operator/MWPreview_20261006/MTL_MWAM_AutoMaterial_MASTER.t3d, PID23068).
T3D_REF = re.compile(r'Expression="[^"\']*\'([^\']+)\'"([^()]*)')
T3D_PIN = re.compile(r'^(\w+)=\(Expression=')
T3D_OUTPUT = re.compile(r'^Outputs\((\d+)\)=\(OutputName="([^"]*)"')
MMA_TARGETS = {'BaseColor': 'OutBaseColor', 'Normal': 'OutUnitNormal', 'Roughness': 'OutRoughness',
               'Specular': 'OutSpecular', 'AmbientOcclusion': 'OutAmbientOcclusion'}
CANVAS = {'x0': 2500, 'y0': 1400, 'cols': 8, 'xstep': 240, 'ystep': 230}
GROUP = 'GeoCity_Urban'
URBAN_SCALARS = {'Urban_Amount': 0.0, 'Urban_PadAmount': 1.0, 'Urban_RoadAmount': 1.0, 'Urban_TileCm': 400.0,
                 'Urban_FarScale': 6.0, 'Urban_FarDistanceCm': 4000.0, 'Urban_GridCm': 100.0,
                 'Urban_RoughnessScale': 1.0, 'Urban_NormalStrength': 1.0, 'Urban_Specular': 0.5}
URBAN_VECTORS = {'Urban_Tint': (1.0, 1.0, 1.0, 1.0)}
URBAN_TEXTURES = ('Urban_BaseColor', 'Urban_Normal', 'Urban_Roughness', 'Urban_AO')
SAMPLER_ENUM = {'COLOR': 'SAMPLERTYPE_COLOR', 'GRAYSCALE': 'SAMPLERTYPE_GRAYSCALE', 'ALPHA': 'SAMPLERTYPE_ALPHA',
                'NORMAL': 'SAMPLERTYPE_NORMAL', 'MASKS': 'SAMPLERTYPE_MASKS', 'LINEAR_COLOR': 'SAMPLERTYPE_LINEAR_COLOR',
                'LINEAR_GRAYSCALE': 'SAMPLERTYPE_LINEAR_GRAYSCALE', 'DATA': 'SAMPLERTYPE_DATA'}
ROLE_ALLOWED = {'color': ('COLOR',), 'normal': ('NORMAL',),
                'linear': ('LINEAR_GRAYSCALE', 'LINEAR_COLOR', 'MASKS', 'ALPHA', 'DATA')}
# UMaterialExpressionTextureBase::GetSamplerTypeForTexture (D, UE5 source as recalled; the compile gate is the proof).
COMPRESSION_SAMPLER = {'TCNORMALMAP': 'NORMAL', 'TCALPHA': 'ALPHA', 'TCMASKS': 'MASKS'}
COLOR_COMPRESSIONS = ('TCDEFAULT', 'TCBC7', 'TCHDR', 'TCHDRCOMPRESSED', 'TCLQ', 'TCHALFFLOAT', 'TCSINGLEFLOAT',
                      'TCHDRF32', 'TCDISPLACEMENTMAP', 'TCVECTORDISPLACEMENTMAP')
DATA_GROUPS = ('TEXTUREGROUP8BITDATA', 'TEXTUREGROUP16BITDATA')
GUID_KEYS = ('expression_guid', 'material_expression_guid')
CANON_PROPS = ('parameter_name', 'default_value', 'const_a', 'const_b', 'constant', 'group')
SETTINGS = ('use_material_attributes', 'blend_mode', 'shading_model', 'material_domain', 'two_sided',
            'tangent_space_normal', 'enable_tessellation', 'used_with_nanite', 'used_with_static_lighting',
            'substrate_roughness_tracking', 'num_customized_u_vs')
STAT_FIELDS = ('num_vertex_shader_instructions', 'num_pixel_shader_instructions', 'num_samplers',
               'num_vertex_texture_samples', 'num_pixel_texture_samples', 'num_virtual_texture_samples',
               'num_uv_scalars', 'num_interpolator_scalars')
MAX_SAMPLERS = 3
LOG_FAILURE_MARKERS = ('Failed to compile Material', 'Default Material will be used', ': Error:')
LOG_NAMES = ('M_GeoCityAuto', 'MI_GeoCityGround_Auto', 'Auto_20261006')
SHA = re.compile(r'^[0-9a-f]{64}$')
COMMON = {'mode', 'label', 'expected_pid', 'lease_owner', 'manager_thread_id', 'operator_thread_id', 'script_file',
          'script_sha256', 'profile_sha256', 'expected_map_sha256', 'vendor_sha256'}
KEYS = {'inspect': (COMMON, set()),
        'build': (COMMON | {'inspect_receipt', 'inspect_receipt_sha256', 'texture_set', 'expectations_file',
                            'expectations_sha256'}, {'fallback_acknowledged_by_manager'})}


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


def norm(text):
    return re.sub(r'[^A-Z0-9]', '', str(text).upper())


def enum_name(value):
    text = getattr(value, 'name', None)
    if not isinstance(text, str):
        found = re.search(r'\.([A-Za-z0-9_]+)', str(value))
        text = found.group(1) if found else str(value)
    return text


def derive_sampler(srgb, compression, lod_group, virtual):
    """Sampler type UE assigns to a texture (GetSamplerTypeForTexture, non-VT); None + reason = STOP."""
    if virtual:
        return None, 'virtual_texture_streaming is on (VT samplers are not reviewed)'
    if norm(enum_name(lod_group)) in DATA_GROUPS:
        return 'DATA', None
    c = norm(enum_name(compression))
    if c in COMPRESSION_SAMPLER:
        return COMPRESSION_SAMPLER[c], None
    if c == 'TCGRAYSCALE':
        return ('GRAYSCALE' if srgb else 'LINEAR_GRAYSCALE'), None
    if c in COLOR_COMPRESSIONS:
        return ('COLOR' if srgb else 'LINEAR_COLOR'), None
    return None, 'compression %s outside the reviewed table' % compression


def texture_verdict(role, srgb, derived, virtual):
    if virtual is True:
        return False, 'VT on'
    if derived not in ROLE_ALLOWED[role]:
        return False, 'derived sampler %s not allowed for role %s' % (derived, role)
    if role == 'linear' and srgb:
        return False, 'roughness/AO texture is sRGB (must be linear)'
    return True, None


def select_texture_set(verdicts):
    """verdicts {set: bool} -> (selected or None, status)."""
    if verdicts.get(PREFERRED_SET):
        return PREFERRED_SET, 'INSPECTED_READ_ONLY'
    if verdicts.get(FALLBACK_SET):
        return FALLBACK_SET, 'STOP_TEXTURE_FALLBACK_REQUIRED'
    return None, 'STOP_NO_TEXTURE_SET'


def short(path):
    return path.rsplit(':', 1)[1] if isinstance(path, str) and ':' in path else path


def strip_guids(rows):
    return {k: dict(v, properties={p: x for p, x in v['properties'].items() if p not in GUID_KEYS})
            for k, v in rows.items()}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def close(a, b, tol=1e-5):
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return abs(float(a) - float(b)) <= tol
    return a == b


def compare_canon(actual, expected):
    """Mismatch list between realised canonical nodes and the offline expectations (same schema)."""
    out = []
    if set(actual) != set(expected):
        out.append({'labels_missing': sorted(set(expected) - set(actual)), 'labels_extra': sorted(set(actual) - set(expected))})
    for label in sorted(set(actual) & set(expected)):
        a, e = actual[label], expected[label]
        for key in ('class', 'edges', 'x', 'y'):
            if a.get(key) != e.get(key):
                out.append({'label': label, 'key': key, 'actual': a.get(key), 'expected': e.get(key)})
        for key, value in e['props'].items():
            if not close(a['props'].get(key), value):
                out.append({'label': label, 'prop': key, 'actual': a['props'].get(key), 'expected': value})
    return out


def validate(args):
    mode = args.get('mode')
    need(mode in KEYS, 'mode must be inspect|build')
    required, optional = KEYS[mode]
    need(not (required - set(args)), 'Missing ARGS keys: %s' % sorted(required - set(args)))
    need(not (set(args) - required - optional), 'Unknown ARGS keys: %s' % sorted(set(args) - required - optional))
    need(token(args.get('label')), 'label: ascii [A-Za-z0-9_-]')
    need(isinstance(args.get('expected_pid'), int) and not isinstance(args.get('expected_pid'), bool), 'expected_pid int')
    for key in ('lease_owner', 'manager_thread_id', 'operator_thread_id'):
        need(token(args.get(key), 64) and args[key] != 'NONE', key + ' required')
    for key in ('script_sha256', 'profile_sha256', 'expected_map_sha256'):
        need(isinstance(args.get(key), str) and SHA.match(args[key]), key + ' must be a sha256')
    v = args.get('vendor_sha256')
    need(isinstance(v, dict) and set(v) == set(VENDOR_FILES) and all(isinstance(x, str) and SHA.match(x) for x in v.values()),
         'vendor_sha256 {desert, master}')
    if mode == 'build':
        need(args.get('lease_owner') == LEASE_OWNER, 'build requires lease_owner ' + LEASE_OWNER)
        need(args.get('texture_set') in TEXTURE_SETS, 'texture_set must be one of %s' % sorted(TEXTURE_SETS))
        for key in ('inspect_receipt_sha256', 'expectations_sha256'):
            need(isinstance(args.get(key), str) and SHA.match(args[key]), key + ' must be a sha256')
        for key in ('inspect_receipt', 'expectations_file'):
            need(isinstance(args.get(key), str) and args[key].endswith('.json'), key + ' must be a .json path')
        if 'fallback_acknowledged_by_manager' in args:
            need(isinstance(args['fallback_acknowledged_by_manager'], bool), 'fallback_acknowledged_by_manager bool')
    return mode


def verify_identity(args):
    """The executed code must be exactly the pinned file (same compile flags: compile() inherits them)."""
    script = Path(args['script_file'])
    need(script.is_absolute() and script.is_file() and script.parent.name == 'Hybrid_Auto'
         and script.name == 'hybrid_build_master.py', 'script_file must be the Hybrid_Auto/hybrid_build_master.py copy')
    source = script.read_bytes()
    need(sha_bytes(source) == args['script_sha256'], 'Unreviewed script bytes (sha256 differs)')
    need(code_signature(_EXECUTED_CODE) == code_signature(compile(source, str(script), 'exec')),
         'Executed code differs from script_file')
    return str(script)


def vendor_snapshot(root):
    """size/mtime for every MW file; sha256 for the material/function/grass-type packages (PathB pattern)."""
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


def read_profile(root, args):
    raw = (root / PROFILE_REL).read_bytes()
    profile = json.loads(raw.decode('utf-8'))
    ext = profile.get('external_landscape_material') or {}
    row = {'sha256': sha_bytes(raw), 'landscape_material': profile.get('landscape_material'),
           'landscape_grass_enabled': profile.get('landscape_grass', {}).get('enabled'),
           'parent_chain': ext.get('parent_chain'), 'painted_layer_names': profile.get('painted_layer_names')}
    need(row['sha256'] == args['profile_sha256'], 'Profile sha256 differs from the reviewed patched profile (P\')')
    need(row['landscape_material'] == MI_PATH and row['landscape_grass_enabled'] is False
         and row['parent_chain'] == [COPY_OBJ], 'Profile is not patched for the Hybrid (run hybrid_profile_patch.py first)')
    need(sorted(row['painted_layer_names'] or []) == sorted(LAYERS), 'Profile painted_layer_names differ from the four layers')
    return row


# ------------------------------------------------------------------ graph builder (fork of S1 Builder, s1_material_edit.py:771-912)
class Builder:
    """Node creation/link helpers with the engine module and library injected (offline mock or unreal)."""

    def __init__(self, u, lib, owner, mark, canvas, sampler_source):
        self.u, self.lib, self.owner, self.mark = u, lib, owner, mark
        self.x0, self.y0, self.cols = canvas['x0'], canvas['y0'], canvas['cols']
        self.xstep, self.ystep = canvas['xstep'], canvas['ystep']
        self.wrap = sampler_source
        self.added, self.labels, self.notes = [], {}, {}

    def node(self, cls, label, **properties):
        need(label not in self.labels, 'Duplicate node label ' + label)
        i = len(self.added)
        x, y = self.x0 + (i % self.cols) * self.xstep, self.y0 + (i // self.cols) * self.ystep
        e = self.lib.create_material_expression(self.owner, cls, x, y)
        need(e is not None, 'create_material_expression failed: ' + label)
        self.added.append(e)
        self.labels[label] = e
        e.set_editor_property('desc', self.mark + label)
        for key, value in properties.items():
            e.set_editor_property(key, value)
        return e

    def link(self, source, target, pin):
        expr, output = source if isinstance(source, tuple) else (source, '')
        names = list(self.lib.get_material_expression_input_names(target))
        need(pin in names, 'Input pin %s not in %s' % (pin, names))
        outputs = list(self.lib.get_material_expression_output_names(expr))
        # '' only where an output is literally named '' (M: Constant3Vector ['', 'R', 'G', 'B']) or the node has one
        # output; on a named multi-output node (function call, texture sample) '' would silently connect output 0
        # (e.g. MW_MWAM_Water:BaseColor), so it is refused.
        need(output in outputs or (output == '' and len(outputs) == 1), 'Output %r not in %s' % (output, outputs))
        need(self.lib.connect_material_expressions(expr, output, target, pin), 'connect failed -> ' + pin)

    def op(self, cls, label, a=None, b=None, **properties):
        e = self.node(cls, label, **properties)
        if a is not None:
            self.link(a, e, 'A')
        if b is not None:
            self.link(b, e, 'B')
        return e

    def mul(self, label, a, b):
        return self.op(self.u.MaterialExpressionMultiply, label, a, b)

    def mul_c(self, label, a, c):
        return self.op(self.u.MaterialExpressionMultiply, label, a, const_b=float(c))

    def add(self, label, a, b):
        return self.op(self.u.MaterialExpressionAdd, label, a, b)

    def div(self, label, a, b):
        return self.op(self.u.MaterialExpressionDivide, label, a, b)

    def max_c(self, label, a, c):
        return self.op(self.u.MaterialExpressionMax, label, a, const_b=float(c))

    def single(self, cls, label, x, pin):
        e = self.node(cls, label)
        self.link(x, e, pin)
        return e

    def sat(self, label, x):
        return self.single(self.u.MaterialExpressionSaturate, label, x, 'None')

    def normalize(self, label, x):
        return self.single(self.u.MaterialExpressionNormalize, label, x, 'VectorInput')

    def lerp(self, label, a, b, alpha):
        properties = {'const_a': float(a)} if isinstance(a, (int, float)) else {}
        e = self.node(self.u.MaterialExpressionLinearInterpolate, label, **properties)
        if not properties:
            self.link(a, e, 'A')
        self.link(b, e, 'B')
        self.link(alpha, e, 'Alpha')
        return e

    def c3(self, label, x, y, z):
        return self.node(self.u.MaterialExpressionConstant3Vector, label,
                         constant=self.u.LinearColor(float(x), float(y), float(z), 0.0))

    def sample(self, label, texture, uv, sampler_type, output):
        # Every new sample is Shared:Wrap (precedent native_graph_stochastic.py:593-595, S1 Builder.sample).
        e = self.node(self.u.MaterialExpressionTextureSample, label, sampler_type=sampler_type,
                      sampler_source=self.wrap, mip_value_mode=self.u.TextureMipValueMode.TMVM_NONE)
        self.link(uv, e, 'UVs')
        self.link(texture, e, 'Tex')
        return (e, output)

    def texture_param(self, name, texture, sampler_type):
        e = self.node(self.u.MaterialExpressionTextureObjectParameter, name, parameter_name=self.u.Name(name),
                      texture=texture)
        # Setting Texture runs AutoSetSampleType (PostEditChangeProperty, D); record it, then set the derived type.
        self.notes[name] = {'auto_sampler_type_after_texture': str(e.get_editor_property('sampler_type'))}
        e.set_editor_property('sampler_type', sampler_type)
        e.set_editor_property('sampler_source', self.wrap)
        e.set_editor_property('group', self.u.Name(GROUP))
        return (e, '')


def make_params(g, textures, samplers):
    """15 Urban parameters with neutral master defaults (Urban_Amount 0 => pure MW)."""
    u, P = g.u, {}
    for name, value in URBAN_SCALARS.items():
        P[name] = (g.node(u.MaterialExpressionScalarParameter, name, parameter_name=u.Name(name),
                          default_value=float(value), group=u.Name(GROUP)), '')
    for name, value in URBAN_VECTORS.items():
        P[name] = (g.node(u.MaterialExpressionVectorParameter, name, parameter_name=u.Name(name),
                          default_value=u.LinearColor(*value), group=u.Name(GROUP)), 'RGB')
    for name in URBAN_TEXTURES:
        P[name] = g.texture_param(name, textures[name], samplers[name])
    return P


def build_urban(g, anchors, P, samplers, channels):
    """Urban graph per PLAN_HYBRID.md "Urban graph"; anchors: base_color/normal/roughness/specular -> (expr, output).
    Returns the five MMA_0 sources keyed by MMA pin name."""
    u = g.u
    W = {l: g.node(u.MaterialExpressionLandscapeLayerSample, 'Weight' + l, parameter_name=u.Name(l)) for l in LAYERS}
    pad = g.mul('PadWeight', W['Sand_Path'], P['Urban_PadAmount'])
    road = g.mul('RoadWeight', W['Dirt_Path'], P['Urban_RoadAmount'])
    pad_road = g.add('PadPlusRoad', pad, road)
    presence = g.mul_c('LayerPresenceZero', g.add('GroundLayerSum', W['Sand_01'], W['Sand_02']), 0.0)
    coverage = g.sat('UrbanCoverage', g.add('UrbanMaskRaw', pad_road, presence))
    mask = g.sat('UrbanMask', g.mul('UrbanMaskAmount', coverage, P['Urban_Amount']))
    coords = g.node(u.MaterialExpressionLandscapeLayerCoords, 'LandscapeCoords')
    cm_to_uv = g.div('CmToUV', P['Urban_GridCm'], g.max_c('TileCmPositive', P['Urban_TileCm'], 1.0))
    near_uv = g.mul('NearUV', coords, cm_to_uv)
    far_uv = g.div('FarUV', near_uv, g.max_c('FarScaleMin1', P['Urban_FarScale'], 1.0))
    depth = g.node(u.MaterialExpressionPixelDepth, 'PixelDepth')
    distance = g.sat('DistanceAlpha', g.div('DistanceRaw', depth, g.max_c('FarDistancePositive', P['Urban_FarDistanceCm'], 1.0)))
    near = g.sample('NearColorSample', P['Urban_BaseColor'], near_uv, samplers['Urban_BaseColor'], 'RGB')
    far = g.sample('FarColorSample', P['Urban_BaseColor'], far_uv, samplers['Urban_BaseColor'], 'RGB')
    color = g.mul('UrbanColor', g.lerp('NearFarColor', near, far, distance), P['Urban_Tint'])
    normal_sample = g.sample('NormalSample', P['Urban_Normal'], near_uv, samplers['Urban_Normal'], 'RGB')
    unit_normal = g.normalize('UrbanUnitNormal', g.lerp('UrbanNormalStrength', g.c3('FlatNormal', 0.0, 0.0, 1.0),
                                                        normal_sample, P['Urban_NormalStrength']))
    rough = g.sample('RoughnessSample', P['Urban_Roughness'], near_uv, samplers['Urban_Roughness'], channels['roughness'])
    urban_rough = g.sat('UrbanRoughness', g.mul('RoughnessScaled', rough, P['Urban_RoughnessScale']))
    ao = g.sample('AOSample', P['Urban_AO'], near_uv, samplers['Urban_AO'], channels['ao'])
    return {'BaseColor': g.lerp('OutBaseColor', anchors['base_color'], color, mask),
            'Normal': g.normalize('OutUnitNormal', g.lerp('OutNormalBlend', anchors['normal'], unit_normal, mask)),
            'Roughness': g.lerp('OutRoughness', anchors['roughness'], urban_rough, mask),
            'Specular': g.lerp('OutSpecular', anchors['specular'], P['Urban_Specular'], mask),
            'AmbientOcclusion': g.lerp('OutAmbientOcclusion', 1.0, ao, mask)}


def canonical(rows, labels, refs):
    """Engine describe rows of the new nodes -> expectation schema {label: {class, edges, x, y, props}}."""
    out = {}
    for key, label in labels.items():
        row = rows[key]
        edges = {pin: [refs.get(e['source'], 'vendor:' + str(e['source'])), e['output']]
                 for pin, e in row['edges'].items() if e.get('source')}
        props = row['properties']
        out[label] = {'class': row['class'], 'edges': edges, 'x': props.get('material_expression_editor_x'),
                      'y': props.get('material_expression_editor_y'),
                      'props': {k: props[k] for k in CANON_PROPS if k in props}}
    return out


def t3d_text(data):
    if data[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return data.decode('utf-16')
    return data.decode('utf-8-sig', 'replace')


def t3d_blocks(text):
    """{expression name: [stripped property lines]} for objects nested one level inside the exported material;
    the declaration and definition blocks of one name are merged."""
    blocks, stack = {}, []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('Begin Object'):
            found = re.search(r'\bName="([^"]+)"', s)
            stack.append(found.group(1) if found else None)
            if len(stack) == 2:
                blocks.setdefault(stack[-1], [])
        elif s.startswith('End Object'):
            need(stack, 'Unbalanced T3D End Object')
            stack.pop()
        elif len(stack) == 2 and s:
            blocks[stack[-1]].append(s)
    need(not stack, 'Unbalanced T3D Begin Object')
    return blocks


def t3d_refs(lines):
    """(pins {property: [source, OutputIndex]} for simple 'Pin=(Expression=...)' lines, sorted list of every
    [source, OutputIndex] reference in the block)."""
    pins, refs = {}, []
    for line in lines:
        found_all = []
        for found in T3D_REF.finditer(line):
            index = re.search(r'OutputIndex=(\d+)', found.group(2))
            found_all.append([short(found.group(1)), int(index.group(1)) if index else 0])
        refs.extend(found_all)
        pin = T3D_PIN.match(line)
        if pin and found_all:
            pins[pin.group(1)] = found_all[0]
    return pins, sorted(refs)


def t3d_outputs(lines):
    rows = {}
    for line in lines:
        found = T3D_OUTPUT.match(line)
        if found:
            rows[int(found.group(1))] = found.group(2)
    return [rows[i] for i in sorted(rows)]


def mma_true_outputs(blocks, water_outputs_live):
    """True MMA_0 wiring from T3D: OutputIndex resolved to MW_MWAM_Water output names (T3D Outputs(N), which must
    equal the live output-name list); gated to the pin-matched plan wiring."""
    need(MMA in blocks and MF14 in blocks, 'T3D lacks the MMA_0 / MF_14 blocks')
    pins, _ = t3d_refs(blocks[MMA])
    water = t3d_outputs(blocks[MF14])
    need(water == list(water_outputs_live), 'MF_14 T3D Outputs %s differ from the live names %s' % (water, water_outputs_live))
    need(set(pins) == set(MMA_SOURCES), 'MMA_0 T3D connected pins %s differ from %s' % (sorted(pins), sorted(MMA_SOURCES)))
    true = {}
    for pin, source in MMA_SOURCES.items():
        ref = pins[pin]
        need(ref[0] == source, 'MMA_0.%s T3D source %s != %s' % (pin, ref[0], source))
        if source == SSP16:
            need(ref[1] == 0, 'MMA_0.BaseColor OutputIndex %s != 0' % ref[1])
            true[pin] = {'source': source, 'output_index': 0, 'output': ''}
        else:
            need(ref[1] < len(water), 'MMA_0.%s OutputIndex %s out of range' % (pin, ref[1]))
            true[pin] = {'source': source, 'output_index': ref[1], 'output': water[ref[1]]}
            need(water[ref[1]] == pin, 'MMA_0.%s <- MW_MWAM_Water:%s (index %d): not the pin-matched plan wiring (STOP)'
                 % (pin, water[ref[1]], ref[1]))
    return true, water


def expected_refs(expected_nodes, short_of, output_names):
    """Expectation edges -> {new node name: sorted [[source name, OutputIndex], ...]}; also proves no new node takes
    two inputs from one source (so the legacy per-(target, source) output-name reader is unambiguous for them)."""
    result = {}
    for label, node in expected_nodes.items():
        refs = []
        for pin, (ref, output) in node['edges'].items():
            source = short_of[ref]
            outs = list(output_names[source])
            need(output in outs or (output == '' and len(outs) == 1), '%s.%s: output %r not in %s' % (label, pin, output, outs))
            refs.append([source, outs.index(output) if output in outs else 0])
        need(len({r[0] for r in refs}) == len(refs), 'Node %s takes two inputs from one source' % label)
        result[short_of['new:' + label]] = sorted(refs)
    return result


def t3d_check(blocks, mma_expected, refs_expected):
    """Mismatches of a post-edit T3D against the expected MMA_0 pins and every new node's reference set."""
    out = []
    pins, _ = t3d_refs(blocks.get(MMA, []))
    if pins != mma_expected:
        out.append({'node': MMA, 'actual': pins, 'expected': mma_expected})
    for key, want in refs_expected.items():
        got = t3d_refs(blocks.get(key, []))[1]
        if got != want:
            out.append({'node': key, 'actual': got, 'expected': want})
    return out


# ------------------------------------------------------------------ editor helpers (lazy unreal)
def _p(obj):
    return obj.get_path_name() if obj else None


def dirty(u):
    return (sorted(_p(p) for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
            sorted(_p(p) for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()))


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
    return {'pid': pid, 'lease': lease, 'lease_kind': 'authoring' if authoring else 'readonly', 'world': MAP,
            'hda_actors': 1, 'cooking_paused': True, 'autosave': False, 'editor_pids': pids, 'landscape': _p(lands[0])}


def load_helper(root):
    """Frozen describe/digest/reachable helper (S1 pattern: sha-pinned, executed in its own module namespace)."""
    data = (root / HELPER_REL).read_bytes()
    need(sha_bytes(data) == HELPER_SHA, 'Frozen graph helper changed')
    module = types.ModuleType('hybrid_frozen_graph_helper')
    exec(compile(data, str(root / HELPER_REL), 'exec'), module.__dict__)
    need('ARGS' not in module.__dict__ and 'RESULT' not in module.__dict__, 'Helper executed a mode')
    return module


def graph(u, lib, h, material):
    """Rows keyed by expression object name; the material's own object path is rewritten away so a copy and its
    source compare row-for-row. Returns (rows, {name: expression})."""
    obj = h.path(material)
    exprs = {}
    for e in lib.get_material_expressions(material):
        p = h.path(e)
        need(p.startswith(obj + ':'), 'Expression outside the material: ' + p)
        need(short(p) not in exprs, 'Duplicate expression name ' + p)
        exprs[short(p)] = e
    rows = {k: h.describe(material, e) for k, e in exprs.items()}
    text = json.dumps(rows, sort_keys=True).replace(obj + ':', '').replace(obj, '<SELF>')
    return json.loads(text), exprs


def roots_of(u, lib, h, material):
    props = dict(h.PROPERTIES)
    props['material_attributes'] = u.MaterialProperty.MP_MATERIAL_ATTRIBUTES
    return {k: short(h.path(lib.get_material_property_input_node(material, p))) for k, p in sorted(props.items())}


def settings_of(h, material):
    return {k: h.plain(h.safe(material, k)) for k in SETTINGS}


def reach(rows, starts):
    seen, stack = set(), [s for s in starts if s]
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in rows:
            continue
        seen.add(cur)
        stack.extend(e['source'] for e in rows[cur]['edges'].values() if e.get('source'))
    return seen


def output_nodes(rows):
    return sorted(k for k, r in rows.items() if r['class'] in ('MaterialExpressionLandscapeGrassOutput',
                                                              'MaterialExpressionLandscapePhysicalMaterialOutput'))


def layer_samples(rows):
    return {k: r['properties'].get('parameter_name') for k, r in rows.items()
            if r['class'] == 'MaterialExpressionLandscapeLayerSample'}


def anchors_check(rows, roots, blocks):
    """MW master wiring the Hybrid edits. Sources/classes from the describe rows (M: native_inventory_complete.json);
    output names from the T3D export (the legacy reader is advisory: one name per (target, source) pair)."""
    mma = rows.get(MMA)
    need(mma is not None and mma['class'] == 'MaterialExpressionMakeMaterialAttributes', 'MakeMaterialAttributes_0 missing')
    need(roots.get('material_attributes') == MMA, 'Material attributes root is not MakeMaterialAttributes_0: %s' % roots)
    ssp = rows.get(SSP16)
    need(ssp and ssp['class'] == 'MaterialExpressionStaticSwitchParameter'
         and ssp['properties'].get('parameter_name') == 'MW_DebugBake', 'StaticSwitchParameter_16 is not MW_DebugBake')
    mf = rows.get(MF14)
    need(mf and mf['class'] == 'MaterialExpressionMaterialFunctionCall'
         and mf['properties'].get('material_function') == WATER_FUNCTION, 'MaterialFunctionCall_14 is not MW_MWAM_Water')
    edges = mma['edges']
    need(all(p in edges for p in list(MMA_SOURCES) + ['AmbientOcclusion']), 'MMA_0 pin names differ: %s' % sorted(edges))
    for pin, source in MMA_SOURCES.items():
        need(edges[pin].get('source') == source, 'MMA_0.%s source %s != %s' % (pin, edges[pin].get('source'), source))
    others = {p: e for p, e in edges.items() if p not in MMA_SOURCES and e.get('source')}
    need(not others, 'MMA_0 has other connected pins: %s' % others)
    true, water = mma_true_outputs(blocks, mf.get('output_names') or [])
    samples = layer_samples(rows)
    need(sorted(samples.values()) == [MW_LAYER], 'MW master layer samples differ: %s' % samples)
    need(not any(str(r['properties'].get('desc') or '').startswith(MARK) for r in rows.values()), 'Hybrid nodes already present')
    busy = [k for k, r in rows.items() if r['properties'].get('material_expression_editor_x', 0) >= CANVAS['x0'] - 260
            and r['properties'].get('material_expression_editor_y', 0) >= CANVAS['y0'] - 260]
    need(not busy, 'Canvas x>=2500,y>=1400 is not free: %s' % busy)
    return {'mma_true_outputs': true, 'water_outputs': water,
            'mma_legacy_reader_outputs_advisory': {p: [edges[p]['source'], edges[p].get('output')] for p in MMA_SOURCES},
            'mma_input_names': mma.get('input_names'), 'layer_samples': samples}


def export_t3d(u, obj, dest):
    """Read-only T3D export (pattern: Staging/BankIntegration_2026-10-04/preserve_dirty_originals.py:98-102)."""
    need(not dest.exists(), 'T3D file already exists: ' + str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    task = u.AssetExportTask()
    for name, value in {'object': obj, 'filename': str(dest), 'automated': True, 'prompt': False,
                        'exporter': u.ObjectExporterT3D()}.items():
        task.set_editor_property(name, value)
    need(u.Exporter.run_asset_export_task(task), 'T3D export failed: %s' % str(task.get_editor_property('errors')))
    need(dest.is_file(), 'T3D file missing after export: ' + str(dest))
    return {'file': str(dest), 'sha256': sha_file(dest)}, t3d_blocks(t3d_text(dest.read_bytes()))


def t3d_path(root, label, kind, pid):
    return root / OUT_REL / ('HYBRID_T3D_%s_%s_PID%s.t3d' % (label, kind, pid))


def log_file(u):
    folder = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_log_dir()))
    return folder / (Path(u.Paths.get_project_file_path()).stem + '.log')


def log_scan(u, offset):
    """Anchored scan (S1 log_scan pattern): named = lines naming Hybrid assets with error/failure words;
    unattributed = anchored material-compile failures elsewhere."""
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


def statistics(lib, material):
    try:
        stats = lib.get_statistics(material)
        return {k: int(stats.get_editor_property(k)) for k in STAT_FIELDS}
    except Exception as error:
        return {'error': repr(error)}


def texture_row(u, h, path, role):
    texture = u.load_asset(path)
    row = {'path': path, 'role': role, 'class': texture.get_class().get_name() if texture else None}
    if not isinstance(texture, u.Texture2D):
        row.update(ok=False, reason='missing or not a Texture2D')
        return row
    vt = h.safe(texture, 'virtual_texture_streaming')
    row.update(srgb=bool(texture.get_editor_property('srgb')),
               compression=enum_name(texture.get_editor_property('compression_settings')),
               lod_group=enum_name(texture.get_editor_property('lod_group')),
               virtual_texture_streaming=vt if isinstance(vt, bool) else 'UNREADABLE (compile gate decides)',
               size=[int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())])
    derived, reason = derive_sampler(row['srgb'], row['compression'], row['lod_group'], vt is True)
    row['derived_sampler'] = derived
    ok, why = texture_verdict(role, row['srgb'], derived, vt) if derived else (False, reason)
    row.update(ok=ok, reason=why)
    return row


def texture_rows(u, h):
    rows, verdicts = {}, {}
    for name, spec in TEXTURE_SETS.items():
        rows[name] = {p: texture_row(u, h, path, role) for p, (path, role) in spec['textures'].items()}
        verdicts[name] = all(r['ok'] for r in rows[name].values())
    return rows, verdicts


def receipt_path(root, mode, label, pid):
    return root / OUT_REL / ('HYBRID_MASTER_%s_%s_PID%s.json' % (mode.upper(), label, pid))


def write_receipt(root, receipt):
    path = receipt_path(root, receipt['mode'], receipt['label'], receipt['pid'])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'x', encoding='utf-8') as stream:      # exclusive: never overwrite a receipt
        json.dump(receipt, stream, indent=2, default=str)
    return str(path)


def bound_json(root, file, expected_sha, under):
    path = Path(file).resolve()
    need(path.is_file() and path.is_relative_to((root / under).resolve()), 'Bound file outside %s: %s' % (under, path))
    raw = path.read_bytes()
    need(sha_bytes(raw) == expected_sha, 'Bound file sha256 differs: ' + str(path))
    return path, json.loads(raw.decode('utf-8'))


# ------------------------------------------------------------------ modes
def do_inspect(u, lib, h, root, args, receipt):
    receipt['guard'] = guard(u, root, args, 'inspect')
    d0 = dirty(u)
    receipt['dirty_before'] = d0
    need(d0 == ([], []), 'Packages are dirty before inspection: %s' % (d0,))
    receipt['profile'] = read_profile(root, args)
    disk0 = disk(root)
    receipt['disk'] = disk0
    need(disk0['map'] == args['expected_map_sha256'], 'Saved map differs from the reviewed baseline')
    need(disk0['vendor_pins'] == args['vendor_sha256'], 'MW vendor DesertExample/master files differ from the pins')
    need(disk0['copy'] is None and disk0['mi'] is None and disk0['pathb_mi'] is None,
         'M_GeoCityAuto / MI_GeoCityGround_Auto / MI_GeoCityGround_MW already exist on disk')
    folder = root / COPY_DIR_FILE
    need(not folder.exists() or not any(folder.rglob('*.uasset')), 'Auto_20261006 already holds packages on disk')
    need(all(disk0['protected'][rel] for rel in TEXTURE_FILES), 'An Urban texture package is missing on disk')
    for pkg in (COPY_PKG, MI_PKG, PATHB_MI_PKG):
        need(not u.EditorAssetLibrary.does_asset_exist(pkg), 'Asset already exists: ' + pkg)
    receipt['vendor_snapshot'] = vendor_snapshot(root)
    vendor = u.load_asset(VENDOR_OBJ)
    need(isinstance(vendor, u.Material), 'MW master is not a Material')
    rows, _ = graph(u, lib, h, vendor)
    roots = roots_of(u, lib, h, vendor)
    receipt['vendor_graph'] = {'rows': len(rows), 'digest': digest(rows), 'digest_noguid': digest(strip_guids(rows)),
                               'roots': roots, 'settings': settings_of(h, vendor), 'output_nodes': output_nodes(rows),
                               'nodes': rows}
    trows, verdicts = texture_rows(u, h)
    receipt['textures'] = trows
    t3d, blocks = export_t3d(u, vendor, t3d_path(root, args['label'], 'vendor', os.getpid()))
    receipt['vendor_t3d'] = t3d
    need(len(rows) == VENDOR_NODE_COUNT, 'MW master has %d rows, expected %d' % (len(rows), VENDOR_NODE_COUNT))
    anchors = anchors_check(rows, roots, blocks)
    receipt['vendor_graph']['anchors'] = anchors
    receipt['mma_true_outputs'] = anchors['mma_true_outputs']
    reachable = reach(rows, list(roots.values()) + output_nodes(rows))
    receipt['vendor_graph']['remove_foliage_reachable'] = any(k in reachable for k in anchors['layer_samples'])
    need(receipt['vendor_graph']['remove_foliage_reachable'], 'MW RemoveFoliage layer sample is not reachable from any output')
    selected, status = select_texture_set(verdicts)
    receipt['texture_selection'] = {'verdicts': verdicts, 'selected': selected, 'preferred': PREFERRED_SET,
                                    'fallback': FALLBACK_SET, 'rule': 'Aviv 2026-10-06: Asphalt_cracked; roughness/AO '
                                    'must be linear, VT off; else the documented Concrete_plate fallback; never edit textures'}
    if selected:
        receipt['texture_selection']['samplers'] = {p: trows[selected][p]['derived_sampler'] for p in URBAN_TEXTURES}
        receipt['texture_selection']['channels'] = TEXTURE_SETS[selected]['channels']
    d1 = dirty(u)
    receipt['dirty_after'] = d1
    need(d1 == d0, 'Inspection changed dirty packages: %s -> %s' % (d0, d1))
    need(disk(root) == disk0, 'Disk changed during inspection')
    return status


def do_build(u, lib, h, root, args, receipt):
    pid = os.getpid()
    receipt['guard'] = guard(u, root, args, 'build')
    _, insp = bound_json(root, args['inspect_receipt'], args['inspect_receipt_sha256'], OUT_REL)
    need(insp.get('schema') == SCHEMA and insp.get('mode') == 'inspect' and insp.get('pid') == pid,
         'Inspect receipt is not an inspection of this PID')
    sel = insp['texture_selection']
    need(insp.get('status') in ('INSPECTED_READ_ONLY', 'STOP_TEXTURE_FALLBACK_REQUIRED'), 'Inspect status does not permit a build')
    need(args['texture_set'] == sel['selected'], 'texture_set differs from the inspected selection %s' % sel['selected'])
    if insp['status'] == 'STOP_TEXTURE_FALLBACK_REQUIRED':
        need(args.get('fallback_acknowledged_by_manager') is True, 'Fallback texture set needs the manager acknowledgement')
    exp_path, exp = bound_json(root, args['expectations_file'], args['expectations_sha256'], STAGE_REL)
    need(exp.get('schema') == 'environmentpipeline.ground_hybrid_expectations.v1' and exp_path.name == 'HYBRID_EDIT_EXPECTATIONS.json',
         'Not the Hybrid expectations file')
    need(exp['generated_from']['target_sha256'] == args['script_sha256'], 'Expectations were generated from other script bytes')
    expected_nodes = exp['texture_sets'][args['texture_set']]['nodes']
    out = root / OUT_REL
    latch = out / ('HYBRID_BUILD_ONCE_PID%d.json' % pid)
    need(not latch.exists(), 'One build per PID: a build was already attempted in this PID (close without saving)')
    d0 = dirty(u)
    need(d0 == ([], []), 'Packages are dirty before the build: %s' % (d0,))
    need(read_profile(root, args)['sha256'] == insp['profile']['sha256'], 'Profile changed since inspect')
    disk0 = disk(root)
    need(disk0 == insp['disk'], 'Disk (map/vendor/protected/new packages) changed since inspect')
    vendor0 = vendor_snapshot(root)
    need(vendor0 == insp['vendor_snapshot'], 'MW vendor snapshot changed since inspect')
    for pkg in (COPY_PKG, MI_PKG, PATHB_MI_PKG):
        need(not u.EditorAssetLibrary.does_asset_exist(pkg), 'Asset already exists: ' + pkg)
    vendor = u.load_asset(VENDOR_OBJ)
    vrows, _ = graph(u, lib, h, vendor)
    need(digest(vrows) == insp['vendor_graph']['digest'], 'MW master graph changed since inspect')
    vroots = roots_of(u, lib, h, vendor)
    vsettings = settings_of(h, vendor)
    trows, verdicts = texture_rows(u, h)
    need(trows == insp['textures'], 'Urban texture settings changed since inspect')
    samplers_kind = sel['samplers']
    channels = TEXTURE_SETS[args['texture_set']]['channels']
    sampler_enum = {}
    for p in URBAN_TEXTURES:
        sampler_enum[p] = getattr(u.MaterialSamplerType, SAMPLER_ENUM[samplers_kind[p]], None)
        need(sampler_enum[p] is not None, 'MaterialSamplerType.%s missing' % SAMPLER_ENUM[samplers_kind[p]])
    wrap = u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS
    log0 = log_file(u).stat().st_size
    receipt.update(inspect_receipt=args['inspect_receipt'], inspect_receipt_sha256=args['inspect_receipt_sha256'],
                   expectations={'file': str(exp_path), 'sha256': args['expectations_sha256']},
                   texture_set=args['texture_set'], samplers=samplers_kind, channels=channels,
                   disk_before=disk0, dirty_before=d0, log={'file': str(log_file(u)), 'offset': log0},
                   explicit_save_called=False)
    out.mkdir(parents=True, exist_ok=True)
    with open(latch, 'x', encoding='utf-8') as stream:
        json.dump({'pid': pid, 'utc': utc(), 'status': 'build_started', 'label': args['label']}, stream, indent=2)
    # ---- duplicate (vendor untouched)
    copy = u.EditorAssetLibrary.duplicate_asset(VENDOR_PKG, COPY_PKG)
    need(isinstance(copy, u.Material) and _p(copy) == COPY_OBJ, 'duplicate_asset did not return the M_GeoCityAuto Material')
    d1 = dirty(u)
    receipt['dirty_after_duplicate'] = d1
    need(set(d1[0]) <= {COPY_PKG} and not d1[1], 'duplicate_asset dirtied other packages: %s' % (d1,))
    need(sha_file(root / COPY_FILE) is None, 'duplicate_asset wrote M_GeoCityAuto to disk (unexpected save)')
    crows, cexprs = graph(u, lib, h, copy)
    need(set(crows) == set(vrows), 'Copied expression names differ from the vendor names (STOP; no heuristic mapping)')
    need(VENDOR_PKG not in json.dumps(crows), 'Copied graph still references vendor master expressions')
    guid_equal = crows == vrows
    need(strip_guids(crows) == strip_guids(vrows), 'Copied graph != vendor graph (STOP)')
    croots = roots_of(u, lib, h, copy)
    need(croots == vroots, 'Copied material roots differ: %s vs %s' % (croots, vroots))
    need(settings_of(h, copy) == vsettings, 'Copied material settings differ')
    receipt['copy_equals_vendor'] = {'rows': len(crows), 'noguid_equal': True, 'guid_equal_advisory': guid_equal,
                                     'roots_equal': True, 'settings_equal': True, 'settings': vsettings}
    u.EditorAssetLibrary.set_metadata_tag(copy, OWNER_TAG, OWNER_VALUE)
    # ---- Urban graph + MMA_0 rewire
    textures = {p: u.load_asset(path) for p, (path, role) in TEXTURE_SETS[args['texture_set']]['textures'].items()}
    need(all(isinstance(t, u.Texture2D) for t in textures.values()), 'Urban texture load failed')
    # True MMA_0 wiring of the COPY from its own T3D export (must equal the inspected vendor wiring).
    t3d_pre, blocks_pre = export_t3d(u, copy, t3d_path(root, args['label'], 'copy_pre', pid))
    true, water = mma_true_outputs(blocks_pre, crows[MF14].get('output_names') or [])
    receipt.update(copy_t3d_pre=t3d_pre, mma_true_outputs=true)
    need(true == insp['mma_true_outputs'], 'Copy MMA_0 wiring (T3D) differs from the inspected vendor wiring')
    live_water = list(lib.get_material_expression_output_names(cexprs[MF14]))
    need(live_water == water, 'MF_14 live output names differ from its T3D Outputs')
    anchors = {'base_color': (cexprs[SSP16], true['BaseColor']['output']), 'normal': (cexprs[MF14], true['Normal']['output']),
               'roughness': (cexprs[MF14], true['Roughness']['output']), 'specular': (cexprs[MF14], true['Specular']['output'])}
    g = Builder(u, lib, copy, MARK, CANVAS, wrap)
    P = make_params(g, textures, sampler_enum)
    finals = build_urban(g, anchors, P, sampler_enum, channels)
    for pin, source in finals.items():
        g.link(source, cexprs[MMA], pin)
    receipt['texture_param_notes'] = g.notes
    arows, aexprs = graph(u, lib, h, copy)
    labels = {short(h.path(e)): label for label, e in g.labels.items()}
    receipt['added_nodes'] = labels
    # ---- in-memory gates (before compile)
    need(len(arows) == VENDOR_NODE_COUNT + exp['added_node_count'] == VENDOR_NODE_COUNT + len(labels),
         'Row count %d != 190 + %d' % (len(arows), exp['added_node_count']))
    need(set(arows) - set(crows) == set(labels), 'New rows differ from the created nodes')
    changed = sorted(k for k in crows if k != MMA and arows[k] != crows[k])
    need(not changed, 'Vendor rows changed by the edit: %s' % changed[:20])
    ma, mb = arows[MMA], crows[MMA]
    pins = sorted(p for p in ma['edges'] if ma['edges'][p] != mb['edges'].get(p))
    need(pins == sorted(MMA_TARGETS), 'MMA_0 changed pins %s != %s' % (pins, sorted(MMA_TARGETS)))
    need(mb['edges']['AmbientOcclusion'].get('source') is None, 'MMA_0.AmbientOcclusion was connected before')
    need({k: v for k, v in ma.items() if k != 'edges'} == {k: v for k, v in mb.items() if k != 'edges'}, 'MMA_0 properties changed')
    by_label = {v: k for k, v in labels.items()}
    for pin, label in MMA_TARGETS.items():
        need(ma['edges'][pin] == {'source': by_label[label], 'output': ''}, 'MMA_0.%s is not %s' % (pin, label))
    roots_after = roots_of(u, lib, h, copy)
    # Gate: the attributes root stays MakeMaterialAttributes_0 and every other root is untouched. The five legacy
    # property inputs (stored but unused while use_material_attributes is on) are recorded, not gated.
    legacy = ('color', 'normal', 'roughness', 'specular', 'ao')
    need(roots_after['material_attributes'] == MMA and
         {k: v for k, v in roots_after.items() if k not in legacy} == {k: v for k, v in croots.items() if k not in legacy},
         'Material roots changed (root must stay MakeMaterialAttributes_0): %s' % roots_after)
    receipt['legacy_property_roots'] = {'before': {k: croots[k] for k in legacy}, 'after': {k: roots_after[k] for k in legacy}}
    refs = {k: 'new:' + v for k, v in labels.items()}
    refs.update({SSP16: 'anchor:debug_bake', MF14: 'anchor:water'})
    mismatch = compare_canon(canonical(arows, labels, refs), expected_nodes)
    receipt['expectation_mismatches'] = mismatch
    need(not mismatch, 'Realised graph differs from HYBRID_EDIT_EXPECTATIONS.json: %s' % mismatch[:5])
    # Output indices proven from T3D (independent of the legacy output-name reader).
    short_of = {'new:' + v: k for k, v in labels.items()}
    short_of.update({'anchor:debug_bake': SSP16, 'anchor:water': MF14})
    refs_expected = expected_refs(expected_nodes, short_of, {k: r.get('output_names') or [] for k, r in arows.items()})
    mma_expected = {pin: [short_of['new:' + label], 0] for pin, label in MMA_TARGETS.items()}
    mma_expected['Metallic'] = [MF14, true['Metallic']['output_index']]
    t3d_post, blocks_post = export_t3d(u, copy, t3d_path(root, args['label'], 'copy_post', pid))
    receipt['copy_t3d_post'] = t3d_post
    receipt['t3d_mismatches'] = t3d_check(blocks_post, mma_expected, refs_expected)
    need(not receipt['t3d_mismatches'], 'Post-edit T3D wiring differs (STOP): %s' % receipt['t3d_mismatches'][:5])
    sampler_rows = {}
    for key, label in labels.items():
        row = arows[key]['properties']
        need(row.get('desc') == MARK + label, 'desc marker missing: ' + label)
        need(row['material_expression_editor_x'] >= CANVAS['x0'] and row['material_expression_editor_y'] >= CANVAS['y0'],
             'Node outside the canvas: ' + label)
        if arows[key]['class'] in ('MaterialExpressionTextureSample', 'MaterialExpressionTextureObjectParameter'):
            tex_param = label if label in URBAN_TEXTURES else exp['sample_textures'][label]
            want = SAMPLER_ENUM[samplers_kind[tex_param]]
            sampler_rows[label] = {'sampler_type': enum_name(row.get('sampler_type')), 'expected': want,
                                   'sampler_source': enum_name(row.get('sampler_source')), 'texture': row.get('texture')}
            need(norm(sampler_rows[label]['sampler_type']) == norm(want), 'Sampler type mismatch on ' + label)
            need(norm(sampler_rows[label]['sampler_source']) == norm('SSM_WRAP_WORLD_GROUP_SETTINGS'), 'Not Shared:Wrap: ' + label)
            if label in URBAN_TEXTURES:
                need(row.get('texture') == TEXTURE_SETS[args['texture_set']]['textures'][label][0], 'Texture default ' + label)
    receipt['sampler_rows'] = sampler_rows
    samples = layer_samples(arows)
    need(sorted(samples.values()) == sorted(LAYERS + (MW_LAYER,)), 'Layer samples differ: %s' % samples)
    from_mma = reach(arows, [MMA])
    from_all = reach(arows, list(croots.values()) + output_nodes(arows))
    need(set(labels) <= from_mma, 'New nodes not reachable from MMA_0: %s' % sorted(set(labels) - from_mma))
    need(all(k in from_all for k in samples), 'A layer sample is unreachable: %s' % samples)
    receipt['layers'] = {'samples': samples, 'new_reachable_from_mma': True, 'all_reachable': True}
    d2 = dirty(u)
    need(d2 == ([COPY_PKG], []), 'Edit dirtied other packages: %s' % (d2,))
    # ---- compile gate
    errors = lib.recompile_material(copy)
    receipt['compile_errors'] = [str(e) for e in (errors or [])]
    need(not receipt['compile_errors'], 'Compile errors: %s' % receipt['compile_errors'][:5])
    rows_compiled, _ = graph(u, lib, h, copy)
    need(rows_compiled == arows, 'Compile changed graph rows')
    stats = statistics(lib, copy)
    receipt['statistics'] = stats
    need('error' not in stats and stats['num_samplers'] <= MAX_SAMPLERS, 'Sampler gate: %s' % stats)
    receipt['log_scan'] = log_scan(u, log0)
    need(receipt['log_scan']['clean'], 'Material compile failure lines in the editor log (STOP)')
    d3 = dirty(u)
    receipt['dirty_after'] = d3
    need(d3 == ([COPY_PKG], []), 'Dirty set after compile differs: %s' % (d3,))
    disk1 = disk(root)
    need(disk1 == disk0 and vendor_snapshot(root) == vendor0, 'Disk/MW vendor files changed during the build')
    need(str(u.EditorAssetLibrary.get_metadata_tag(copy, OWNER_TAG)) == OWNER_VALUE, 'Owner tag readback')
    receipt.update(graph={'rows': len(arows), 'digest': digest(arows), 'digest_noguid': digest(strip_guids(arows)),
                          'roots': croots, 'nodes': arows},
                   vendor_graph_digest_noguid=insp['vendor_graph']['digest_noguid'],
                   parameters={'scalars': URBAN_SCALARS, 'vectors': {k: list(v) for k, v in URBAN_VECTORS.items()},
                               'textures': {p: TEXTURE_SETS[args['texture_set']]['textures'][p][0] for p in URBAN_TEXTURES}},
                   vendor_snapshot=vendor0, disk_after=disk1)
    return 'BUILT_VERIFIED_NO_SAVE'


def run(args):
    if not isinstance(args, dict) or not args.get('mode'):
        return {'ok': False, 'idle': True, 'reason': 'No ARGS.mode; nothing was done.'}
    mode = validate(args)
    script = verify_identity(args)
    import unreal as u
    lib = u.MaterialEditingLibrary
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    need(not receipt_path(root, mode, args['label'], os.getpid()).exists(), 'Receipt label already used in this PID')
    receipt = {'schema': SCHEMA, 'mode': mode, 'label': args['label'], 'pid': os.getpid(), 'utc_start': utc(),
               'executed_script': script, 'script_sha256': args['script_sha256'], 'args': args,
               'engine': u.SystemLibrary.get_engine_version(), 'status': 'STARTED'}
    try:
        h = load_helper(root)
        receipt['helper_sha256'] = HELPER_SHA
        receipt['status'] = {'inspect': do_inspect, 'build': do_build}[mode](u, lib, h, root, args, receipt)
    except Exception as exc:
        receipt.update(status='FAILED_' + mode.upper(), error=repr(exc), utc_end=utc())
        receipt['receipt_file'] = write_receipt(root, receipt)
        raise
    receipt['utc_end'] = utc()
    receipt['receipt_file'] = write_receipt(root, receipt)
    need(not receipt['status'].startswith('STOP_'), '%s; see %s' % (receipt['status'], receipt['receipt_file']))
    return {'ok': True, 'status': receipt['status'], 'receipt': receipt['receipt_file'],
            'receipt_sha256': sha_file(receipt['receipt_file']), 'texture_selection': receipt.get('texture_selection'),
            'statistics': receipt.get('statistics'), 'dirty_after': receipt.get('dirty_after')}


RESULT = run(globals().get('ARGS'))
