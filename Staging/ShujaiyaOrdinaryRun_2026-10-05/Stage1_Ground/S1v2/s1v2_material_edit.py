"""Stage 1 v2 (S1v2) ground edit of the retained M_SurfaceBank_Natural: Gaza-only branch.

IN-EDITOR ONLY (imports unreal). Arguments: a JSON file whose absolute path is in
os.environ['GEOCITY_S1_ARGS']; it must resolve under
Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground. Unset -> idle, nothing done.
The variable is set/cleared by S1_Prep/s1_set_args.py, sent by S1v2/run_s1v2.py (inline exec, no
__file__; args must name executed_script_file = S1v2/s1v2_material_edit.py).

Design: S1v2/S1V2_DESIGN.md + S1v2/S1V2_SPEC.json. Derived from S1_Prep/s1_material_edit.py (v1,
sha 5c48daaf); guard/lease/backup/snapshot/diff/compile/tune/save/verify machinery is reused, the
builder is new. v2 is applied to the UNTOUCHED baseline graph (1015 nodes, 605c55d0...), never on
top of v1 (v1 was discarded unsaved: Operator/EXIT_PID23156.json).

Graph (all new nodes carry the desc prefix MARK; nothing existing is edited):
  * Three StaticSwitchParameter 'GeoCity_S1_Enable' (default False) at BaseColor/Normal/Roughness;
    False <- the untouched LandscapeLayerBlend_6/_7/_8, True <- the v2 branch. AO root untouched.
    Iran/base MI compile only the False permutation; base MI is never written.
  * MF_GeoCityV2_CellSample (8 Shared:Wrap COLOR fetches): every routed albedo (GroundB = MW SandA,
    GroundC = MW SandC, Steep = Sand_02_Albedo, RoadBed = Dirt_Path_Albedo, Pad = Sand_Path_Albedo)
    is sampled through the EXISTING Sand_01 hash lattice (Custom_0-7 hashes, ComponentMask_17-20
    quintic weights, Saturate_1 distance alpha): 4 near + 4 far taps at UV + hash_i.
    cell_sample_mip_mode (args): 'derivative' (default) = TMVM_DERIVATIVE with DDX/DDY of the
    untranslated UV on the 'DDX(UVs)'/'DDY(UVs)' pins (MEASURED reachable from Python on master
    samples: GP native_graph_stochastic.py:595-598, GRAPH_BEFORE TextureSample_37); 'gradient_free'
    = TMVM_NONE fetches (no derivative pins; 1-px mip seams at the 2 m / 4 m cell borders are
    possible). The mode is chosen in args before inspect, bound by the inspect receipt, asserted per
    fetch and recorded; it is never switched silently at run time.
  * MF_GeoCityV2_MacroField (3 Shared:Wrap MASKS fetches, TMVM_NONE): octaves 127/463/1531 m rotated
    0/37/71 deg, z_i = (n_i - NoiseMean) * NoiseInvStd, linear outputs Value/HueT/VariantB/VariantC/Fine
    (no thresholds).
  * MF_GeoCityV2_MacroColor (new body: symmetric hue lerp, value +-, optional far desaturation),
    MF_GeoCityV2_SlopeBlend and MF_GeoCityV2_HeightBlend (v1 bodies unchanged).
  * Ground base = the full existing Gaza ground: LinearInterpolate_42 (colour, incl. the macro
    Multiply_8 and soil chain) and Normalize_9 (normal) - the exact sources of LLB_6/_7 'Layer
    Sand_01'. Switch True with every S1 amount 0 therefore reproduces B0 on Ground-only pixels
    (closes v1 caveat 15). Steep/RoadBed/Pad albedos are resampled through CellSample on purpose.
  * Three new 4-layer LB_HEIGHT_BLEND LandscapeLayerBlend nodes; 4 LandscapeLayerSample 'Weight<Layer>'.
  * Five new parameter-free packages /Game/Project/Shared/SurfacePainting/Appearance_20261003/
    Functions/MF_GeoCityV2_* (v1 MF_GeoCity_* names are never reused; both sets must be absent).
  * 40 new parameter names (SPEC params table); the MW pack is used only as child-bound textures.

Lease: identity never comes from args alone. args['root_activation'] (+ '_sha256') names a ROOT-written
JSON under Stage1_Ground, NOT under S1_Prep or S1v2, whose file name starts with S1V2_ROOT_ACTIVATION;
schema ACTIVATION_SCHEMA (same document schema as v1) with scope == S1_SCOPE (v2 scope), OWNER,
manager_thread_id, operator_thread_id, assigned_editor_PID (actual PID), map, areas, modes,
script_sha256 (this file), authoring_activations, readonly_pairs [[activation, scope], ...] (read-only
modes only), expected_hda_count (int), max_tune_iterations (int), optional expected_consumers. The last
EDITOR_OWNER.txt line must carry OWNER, manager_thread_id, operator_thread_id, assigned_editor_PID and
map equal to that document, and (for apply/tune/save/child_save) activation in authoring_activations AND
scope=S1_SCOPE. Template: S1v2/S1V2_ROOT_ACTIVATION_GazaShujaiya.json (root copies it to
Stage1_Ground/Activation/S1V2_ROOT_ACTIVATION_GazaShujaiya_PID<pid>.json).

Scope: one area per editor session = the open map's area (args['areas'] == [area]).

Modes (args['mode']); receipts and latches live in S1v2/receipts (never overwritten):
  inspect  read-only: guard, baseline gates (1015 nodes, graph_sha256 605c55d0..., 631/241, 207 root
           Layer pins), anchors (desc + active-set parameter names), root-layer drift guard, Grass
           contract, derivative-pin probe on existing master samples, instance/switch state, consumers,
           child texture compatibility, v1+v2 MF absence. Writes GRAPH_BEFORE_<pid>.json and
           S1V2_INSPECT_<label>_PID<pid>.json.
  apply    same PID as inspect, inspect receipt SHA-bound and re-matched. Static-switch probe -> 5 MF
           packages -> branch -> in-memory diff (zero old-row changes, only 3 root bindings moved) ->
           compile gate (switch defaults forced True then False, RecompileMaterial == [] both) -> child
           overrides (open area only) -> G2 replay of LW:366-367 -> GRAPH_AFTER_<pid>.json +
           S1V2_APPLY receipt (latch S1V2_APPLY_ONCE.json). NO SAVE.
  tune     child-only value iterations (phase a before the master save, phase b after it); latch
           S1V2_TUNE_ONCE_<label>.json; budget activation max_tune_iterations per area.
  save     same PID as apply, after capture/review: saves ONLY the 5 MF_GeoCityV2_* packages, the master
           and CHILDREN[open area] via save_packages(named, False); latch S1V2_SAVE_ONCE.json.
  child_save  phase-b tune receipt of this PID -> saves ONLY CHILDREN[open area].
  verify   fresh process, read-only identity of the saved state.
Never: prepare(), verify_landscape(), Save All, save_assets([]), base MI / Grass type / map / vendor
saves, edits/deletes of existing nodes or edges, MW material functions, cleanup or rollback. Any failure
after mutation writes a failure receipt and raises; close the editor with "Don't Save"; root reviews.

Backup manifest: S1_Prep/Before/S1B_20261005T202836Z/BACKUP_MANIFEST.json (c32afcdb...) is reused. Its
new_asset_paths lists the five v1 MF_GeoCity_* names; v2 accepts exactly that list (or the v2 list),
asserts that NEITHER the v1 nor the v2 function packages exist, and records the v2 packages it creates
in the apply receipt (rollback list). Every other pin check is unchanged.
Offline companion: s1v2_material_edit_offline.py (mock selftest in both mip modes, AST scan,
expectations -> S1V2_EDIT_EXPECTATIONS_*.json). Note: S1_Prep/s1_verify.py post_s1 reads only the v1
.v1 receipt schemas and cannot verify v2 receipts; use mode=verify here.
"""
import datetime
import hashlib
import json
import math
import os
import re
import struct
import sys
import types
from pathlib import Path

# `unreal` is imported lazily in bind_unreal() (only when GEOCITY_S1_ARGS is set), so an
# offline import of this file is idle and the graph-building logic can be exercised with
# a mock (s1v2_material_edit_offline.py). These globals are bound at run time.
unreal = LIB = ROOT = STAGE = PREP = V2DIR = RECEIPTS = SCRIPT = HELPER = WRAP = None
SAMPLER, FIN, ROOT_PROPS, MIP = {}, {}, {}, {}
CELL_MIP = {'mode': None}  # 'derivative' | 'gradient_free'; set from args before any function is built
REL_STAGE = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground'
# Lease scope token root must write as scope=<S1_SCOPE> in the S1v2 EDITOR_OWNER.txt line (no spaces).
S1_SCOPE = 'GeoCity_GroundS1v2_20261006_material_edit'
ACTIVATION_SCHEMA = 'environmentpipeline.s1_root_activation.v1'  # same document schema as v1; scope differs
ACTIVATION_PREFIX = 'S1V2_ROOT_ACTIVATION'
# Known non-S1 lease owners (M: EDITOR_OWNER.txt); an S1 activation may never name them.
FOREIGN_OWNERS = ('NONE', 'GEOCITY_MENU', 'CODEX_MANAGED_SYSTEMS_TASK4', 'CODEX_MANAGED_SYSTEMS_STARTUP',
                  'CODEX_BANK_INTEGRATION', 'CODEX_BANK_UNIFIED', 'ASTRA_BANK', 'CODEX_SYSTEM_COMPLETION')
MUTATING = ('apply', 'tune', 'save', 'child_save')
INSPECT_SCHEMA = 'environmentpipeline.s1_material_edit.inspect.v2'
APPLY_SCHEMA = 'environmentpipeline.s1_material_edit.apply.v2'
TUNE_SCHEMA = 'environmentpipeline.s1_material_edit.tune.v2'
SAVE_SCHEMA = 'environmentpipeline.s1_material_edit.save.v2'
CHILD_SAVE_SCHEMA = 'environmentpipeline.s1_material_edit.child_save.v2'
VERIFY_SCHEMA = 'environmentpipeline.s1_material_edit.verify.v2'
GRAPH_SCHEMA = 'environmentpipeline.s1_graph_dump.v2'
# Latches and receipt prefixes (S1v2/receipts); v1 S1_Prep/receipts latches are never read or written.
APPLY_ONCE = 'S1V2_APPLY_ONCE.json'
SAVE_ONCE = 'S1V2_SAVE_ONCE.json'
TUNE_ONCE = 'S1V2_TUNE_ONCE_'
CHILD_SAVE_ONCE = 'S1V2_CHILD_SAVE_ONCE_'
PREFIX = 'S1V2_'
# FMaterialStatistics fields (M: UE_5.8 MaterialEditingLibrary.h:27-55; snake_case Python names INFERRED).
STAT_FIELDS = ('num_vertex_shader_instructions', 'num_pixel_shader_instructions', 'num_samplers',
               'num_vertex_texture_samples', 'num_pixel_texture_samples', 'num_virtual_texture_samples',
               'num_uv_scalars', 'num_interpolator_scalars')
# Anchored material-failure markers (UE log format), replacing the loose 'error'/'failed' substrings.
LOG_FAILURE_MARKERS = ('Failed to compile Material', 'Default Material will be used', ': Error:')
# Frozen describe/digest helper; reproduces the r030/r031 graph_sha256 (M).
REL_HELPER = 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py'
HELPER_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
SURFACE = '/Game/Project/Shared/SurfacePainting/Appearance_20261003'
MASTER = SURFACE + '/M_SurfaceBank_Natural'           # LW:16
BASE = SURFACE + '/MI_SurfaceBank_Natural'            # LW:15
GRASS = SURFACE + '/LG_GeoCity_PermittedGroundGrass'  # LW:17
FUNCTION_DIR = SURFACE + '/Functions'
# v1 packages (never saved, M: EXIT_PID23156.json); listed in the reused backup manifest; must stay absent.
V1_FUNCTIONS = ('MF_GeoCity_MacroNoise', 'MF_GeoCity_DistanceBlend', 'MF_GeoCity_MacroColor',
                'MF_GeoCity_SlopeBlend', 'MF_GeoCity_HeightBlend')
MAPS = {'GazaShujaiya': '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration',
        'GazaRimal': '/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration'}
CHILDREN = {a: '/Game/Project/Areas/' + a + '/BankIntegration_v015/Materials/MI_GeoCityGround' for a in MAPS}
MARK = 'GeoCity_GroundS1v2_20261006:'
OWNER_TAG = 'GeoCity_GroundS1v2_20261006'
GRASS_OWNER = 'GeoCity_LandscapeGrass'                # LW:12, :278, :323
LAYERS = ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')  # Ground/Steep/RoadBed/BuildingPad, LW:18-19
SWITCH = 'GeoCity_S1_Enable'
BASELINE = {'node_count': 1015,
            'graph_sha256': '605c55d04955ec410d51f42f7e7bb66d949cf5fbefcb42df5e31034473e40a1b',
            'reachable_any_root_plus_grass': 631, 'reachable_active4_plus_grass': 241,
            'root_layer_pins_connected': 207}
SETTINGS = ('tangent_space_normal', 'enable_tessellation', 'blend_mode', 'shading_model',
            'material_domain', 'two_sided', 'use_material_attributes')
SAMPLER_NAMES = {'COLOR': 'SAMPLERTYPE_COLOR', 'NORMAL': 'SAMPLERTYPE_NORMAL', 'MASKS': 'SAMPLERTYPE_MASKS'}
FIN_NAMES = {'S': 'FUNCTION_INPUT_SCALAR', 'V2': 'FUNCTION_INPUT_VECTOR2',
             'V3': 'FUNCTION_INPUT_VECTOR3', 'T2D': 'FUNCTION_INPUT_TEXTURE2D'}
ROOT_PROP_NAMES = {'color': 'MP_BASE_COLOR', 'normal': 'MP_NORMAL', 'roughness': 'MP_ROUGHNESS'}
MIP_NAMES = {'derivative': 'TMVM_DERIVATIVE', 'gradient_free': 'TMVM_NONE', 'none': 'TMVM_NONE'}
DERIVATIVE_PINS = ('DDX(UVs)', 'DDY(UVs)')  # M: GRAPH_BEFORE_23156 TextureSample_37 input_names
GRAVEL_D = '/Game/StarterContent/Textures/T_Ground_Gravel_D.T_Ground_Gravel_D'
SAND_MASK = SURFACE + '/Textures/T_Sand_01_Mask_GeoCity.T_Sand_01_Mask_GeoCity'
MW_TEXTURES = '/Game/MWLandscapeAutoMaterial/Textures/'
# Epic-owned fallback for the macro noise if the MW licence fails (M r027: sRGB false, TC_MASKS).
# Child-texture swap only (no graph change); allowed only with args['epic_noise_fallback'] is True.
PERLIN = '/Game/StarterContent/Textures/T_Perlin_Noise_M.T_Perlin_Noise_M'
NOISE_FALLBACK = {'GeoCity_S1_MacroNoise': (PERLIN,)}
COS15, COS35 = math.cos(math.radians(15.0)), math.cos(math.radians(35.0))  # MOD:5133-5137 range
LUMA = (0.2126, 0.7152, 0.0722)
# MacroField octaves (SPEC functions.MF_GeoCity_MacroField): output channel, rotation deg, UV offset.
OCTAVES = (('1', 'R', 0.0, (0.13, 0.71)), ('2', 'G', 37.0, (0.37, 0.61)), ('3', 'B', 71.0, (0.83, 0.29)))

# Existing anchors by desc (M: GRAPH_BEFORE_23156 / SPEC anchors_by_desc): key -> (desc, class, suffix, output).
ANCHORS = {
    'ground_full': ('GeoCity_GroundRefinement_20261005:GroundSoilcolor', 'LinearInterpolate', 'LinearInterpolate_42', ''),
    'ground_full_normal': ('GeoCity_GroundRefinement_20261005:GroundSoilUnitNormal', 'Normalize', 'Normalize_9', ''),
    'ground_near': ('GeoCity_GroundStochastic_20261005:NearcolorCellBlend', 'LinearInterpolate', 'LinearInterpolate_48', ''),
    'ground_far': ('GeoCity_GroundStochastic_20261005:FarcolorCellBlend', 'LinearInterpolate', 'LinearInterpolate_57', ''),
    'near_hash0': ('GeoCity_GroundStochastic_20261005:NearHash0', 'Custom', 'Custom_0', ''),
    'near_hash1': ('GeoCity_GroundStochastic_20261005:NearHash1', 'Custom', 'Custom_1', ''),
    'near_hash2': ('GeoCity_GroundStochastic_20261005:NearHash2', 'Custom', 'Custom_2', ''),
    'near_hash3': ('GeoCity_GroundStochastic_20261005:NearHash3', 'Custom', 'Custom_3', ''),
    'far_hash0': ('GeoCity_GroundStochastic_20261005:FarHash0', 'Custom', 'Custom_4', ''),
    'far_hash1': ('GeoCity_GroundStochastic_20261005:FarHash1', 'Custom', 'Custom_5', ''),
    'far_hash2': ('GeoCity_GroundStochastic_20261005:FarHash2', 'Custom', 'Custom_6', ''),
    'far_hash3': ('GeoCity_GroundStochastic_20261005:FarHash3', 'Custom', 'Custom_7', ''),
    'near_wx': ('GeoCity_GroundStochastic_20261005:NearSmoothX', 'ComponentMask', 'ComponentMask_17', ''),
    'near_wy': ('GeoCity_GroundStochastic_20261005:NearSmoothY', 'ComponentMask', 'ComponentMask_18', ''),
    'far_wx': ('GeoCity_GroundStochastic_20261005:FarSmoothX', 'ComponentMask', 'ComponentMask_19', ''),
    'far_wy': ('GeoCity_GroundStochastic_20261005:FarSmoothY', 'ComponentMask', 'ComponentMask_20', ''),
    'road_uv': ('GeoCity_GroundRefinement_20261005:Dirt_PathNearPatternUV', 'Multiply', 'Multiply_17', ''),
    'pad_uv': ('GeoCity_GroundRefinement_20261005:Sand_PathNearPatternUV', 'Multiply', 'Multiply_19', ''),
    'steep_far_scale': ('GeoCity_GroundRevision_20261005:Sand_02FarScaleBound', 'Clamp', 'Clamp_9', ''),
    'road_far_scale': ('GeoCity_GroundRevision_20261005:Dirt_PathFarScaleBound', 'Clamp', 'Clamp_12', ''),
    'pad_far_scale': ('GeoCity_GroundRevision_20261005:Sand_PathFarScaleBound', 'Clamp', 'Clamp_16', ''),
    'steep_normal': ('GeoCity_GroundRevision_20261005:Sand_02UnitNormal', 'Normalize', 'Normalize_3', ''),
    'road_normal': ('GeoCity_GroundRevision_20261005:Dirt_PathUnitNormal', 'Normalize', 'Normalize_4', ''),
    'pad_normal': ('GeoCity_GroundRevision_20261005:Sand_PathUnitNormal', 'Normalize', 'Normalize_5', ''),
    'distance_alpha': ('GeoCity_GroundRevision_20261005:SharedDistanceAlpha', 'Saturate', 'Saturate_1', ''),
    'layer_coords': ('GeoCity_GroundRevision_20261005:LandscapeXY', 'LandscapeLayerCoords', 'LandscapeLayerCoords_0', ''),
    'grid_cm': ('GeoCity_GroundRevision_20261005:LandscapeGridCm100', 'Constant', 'Constant_0', ''),
}
# Existing parameters found by name in the active (color/normal/roughness-reachable) set
# (M: SPEC anchors_by_parameter_name_active_set; VectorParameter_69 'Dirt_Path_Tint' and _73
# 'Sand_02_TileCm' are unreachable duplicates): key -> (parameter name, class, suffix, output).
PARAM_ANCHORS = {
    'steep_albedo': ('Sand_02_Albedo', 'TextureObjectParameter', 'TextureObjectParameter_157', ''),
    'road_albedo': ('Dirt_Path_Albedo', 'TextureObjectParameter', 'TextureObjectParameter_150', ''),
    'pad_albedo': ('Sand_Path_Albedo', 'TextureObjectParameter', 'TextureObjectParameter_161', ''),
    'steep_tint': ('Sand_02_Tint', 'VectorParameter', 'VectorParameter_179', 'RGB'),
    'road_tint': ('Dirt_Path_Tint', 'VectorParameter', 'VectorParameter_174', 'RGB'),
    'pad_tint': ('Sand_Path_Tint', 'VectorParameter', 'VectorParameter_183', 'RGB'),
    'steep_tile': ('Sand_02_TileCm', 'VectorParameter', 'VectorParameter_178', 'R'),
    'pattern_scale': ('GeoCity_PatternScale', 'ScalarParameter', 'ScalarParameter_8', ''),
}
ROUGHNESS = {'Sand_01': 'ScalarParameter_105', 'Sand_02': 'ScalarParameter_106',
             'Dirt_Path': 'ScalarParameter_103', 'Sand_Path': 'ScalarParameter_108'}
ROOT_LLB = {'color': 'LandscapeLayerBlend_6', 'normal': 'LandscapeLayerBlend_7',
            'roughness': 'LandscapeLayerBlend_8', 'ao': 'LandscapeLayerBlend_0'}
# Root Layer edges that must hold before editing (M: GRAPH_BEFORE_23156). Anchored keys prove that the
# v2 Ground base is exactly B0's Sand_01 colour/normal source; suffix rows are a drift guard only.
ROOT_LAYER_EXPECT = {('color', 'Sand_01'): 'ground_full', ('normal', 'Sand_01'): 'ground_full_normal',
                     ('normal', 'Sand_02'): 'steep_normal', ('normal', 'Dirt_Path'): 'road_normal',
                     ('normal', 'Sand_Path'): 'pad_normal'}
ROOT_LAYER_SUFFIX = {('color', 'Sand_02'): 'Multiply_10', ('color', 'Dirt_Path'): 'Multiply_12',
                     ('color', 'Sand_Path'): 'Multiply_14'}

# New master parameters (SPEC params, 40 names): name -> (kind, master default, sampler kind). Defaults
# are neutral (amounts 0, tints 1, Steep 0..0.001, HeightAmount 0, NormalFade 0, RoughVar 0, FarAmount 0);
# texture defaults only reuse textures the master already references (M: GRAPH_BEFORE textures).
PARAMS = {
    SWITCH: ('switch', False, None),
    'GeoCity_S1_MacroNoise': ('texture', SAND_MASK, 'MASKS'),
    'GeoCity_S1_GroundB_Albedo': ('texture', GRAVEL_D, 'COLOR'),
    'GeoCity_S1_GroundC_Albedo': ('texture', GRAVEL_D, 'COLOR'),
    'GeoCity_S1_HueA': ('vector', (1.0, 1.0, 1.0, 1.0), None),
    'GeoCity_S1_HueB': ('vector', (1.0, 1.0, 1.0, 1.0), None),
    'GeoCity_S1_GroundB_Tint': ('vector', (1.0, 1.0, 1.0, 1.0), None),
    'GeoCity_S1_GroundC_Tint': ('vector', (1.0, 1.0, 1.0, 1.0), None),
    'GeoCity_S1_MacroTile1Cm': ('scalar', 12700.0, None),
    'GeoCity_S1_MacroTile2Cm': ('scalar', 46300.0, None),
    'GeoCity_S1_MacroTile3Cm': ('scalar', 153100.0, None),
    'GeoCity_S1_NoiseMean': ('scalar', 0.35, None),
    'GeoCity_S1_NoiseInvStd': ('scalar', 4.0, None),
    'GeoCity_S1_HueGain': ('scalar', 0.35, None),
    'GeoCity_S1_VariantGain': ('scalar', 0.35, None),
    'GeoCity_S1_HueAmount': ('scalar', 0.0, None),
    'GeoCity_S1_ValueAmount': ('scalar', 0.0, None),
    'GeoCity_S1_FarSaturation': ('scalar', 1.0, None),
    'GeoCity_S1_FarValue': ('scalar', 1.0, None),
    'GeoCity_S1_FarAmount': ('scalar', 0.0, None),
    'GeoCity_S1_GroundB_TileCm': ('scalar', 512.0, None),
    'GeoCity_S1_GroundB_FarScale': ('scalar', 4.0, None),
    'GeoCity_S1_GroundB_Amount': ('scalar', 0.0, None),
    'GeoCity_S1_GroundC_TileCm': ('scalar', 470.0, None),
    'GeoCity_S1_GroundC_FarScale': ('scalar', 4.0, None),
    'GeoCity_S1_GroundC_Amount': ('scalar', 0.0, None),
    'GeoCity_S1_SteepLo': ('scalar', 0.0, None),
    'GeoCity_S1_SteepHi': ('scalar', 0.001, None),
    'GeoCity_S1_SteepJitter': ('scalar', 0.0, None),
    'GeoCity_S1_SteepSlopeMix': ('scalar', 0.0, None),
    'GeoCity_S1_HeightBias': ('scalar', 0.85, None),
    'GeoCity_S1_HeightContrast': ('scalar', 0.0, None),
    'GeoCity_S1_HeightAmount': ('scalar', 0.0, None),
    'GeoCity_S1_ContactRoad': ('scalar', 0.0, None),
    'GeoCity_S1_ContactPad': ('scalar', 0.0, None),
    'GeoCity_S1_ContactDarken': ('scalar', 0.0, None),
    'GeoCity_S1_ContactSoil': ('scalar', 0.0, None),
    'GeoCity_S1_ContactRough': ('scalar', 0.0, None),
    'GeoCity_S1_NormalFade': ('scalar', 0.0, None),
    'GeoCity_S1_RoughVar': ('scalar', 0.0, None),
}
# Existing parameters a Gaza child may override in S1 (D2 existing_param_child_overrides).
# Sand_01_Normal/Sand_02_Normal stay pinned (LW:110-121); GeoCity_GrassCoverage only via grass_coverage.
EXISTING_CHILD = {'Dirt_Path_Albedo': 'texture', 'Dirt_Path_Normal': 'texture', 'Dirt_Path_Tint': 'vector',
                  'Dirt_Path_TileCm': 'vector', 'Sand_Path_Albedo': 'texture', 'Sand_Path_Normal': 'texture',
                  'Sand_Path_Tint': 'vector', 'Sand_Path_TileCm': 'vector'}
CONTACT = ('GeoCity_S1_ContactRoad', 'GeoCity_S1_ContactPad', 'GeoCity_S1_ContactDarken',
           'GeoCity_S1_ContactSoil', 'GeoCity_S1_ContactRough')
LOG_NAMES = ('M_SurfaceBank_Natural', 'MI_GeoCityGround', 'MF_GeoCityV2_', 'MF_GeoCity_', 'MI_SurfaceBank_Natural',
             'LandscapeMaterialInstanceConstant', 'L_GazaShujaiya_BankIntegration', 'L_GazaRimal_BankIntegration')


# ----------------------------------------------------------------- basics
def bind_unreal():
    """Bind the editor module and the enum/path globals; called only for a real run."""
    global unreal, LIB, ROOT, STAGE, PREP, V2DIR, RECEIPTS, SCRIPT, HELPER, WRAP
    import unreal as engine
    unreal, LIB = engine, engine.MaterialEditingLibrary
    ROOT = Path(engine.Paths.convert_relative_path_to_full(engine.Paths.project_dir())).resolve()
    STAGE = ROOT / REL_STAGE
    PREP = STAGE / 'S1_Prep'
    V2DIR = STAGE / 'S1v2'
    RECEIPTS = V2DIR / 'receipts'
    SCRIPT = V2DIR / 's1v2_material_edit.py'
    HELPER = ROOT / REL_HELPER
    WRAP = engine.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS
    SAMPLER.update({k: getattr(engine.MaterialSamplerType, v) for k, v in SAMPLER_NAMES.items()})
    FIN.update({k: getattr(engine.FunctionInputType, v) for k, v in FIN_NAMES.items()})
    ROOT_PROPS.update({k: getattr(engine.MaterialProperty, v) for k, v in ROOT_PROP_NAMES.items()})
    MIP.update({k: getattr(engine.TextureMipValueMode, v) for k, v in MIP_NAMES.items()})


def cell_mip_mode(args):
    """Fetch mode of the CellSample function, chosen by root in args (never switched at run time)."""
    mode = args.get('cell_sample_mip_mode', 'derivative')
    assert mode in ('derivative', 'gradient_free'), ('cell_sample_mip_mode must be derivative|gradient_free', mode)
    return mode


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def pkg(path):
    return path.split('.')[0]


def obj_path(path):
    path = pkg(path)
    return path + '.' + path.rsplit('/', 1)[1]


def package_file(package, suffix='.uasset'):
    package = pkg(package)
    assert package.startswith('/Game/'), package
    return ROOT / 'Content' / (package[6:] + suffix)


def disk_state(file):
    file = Path(file)
    row = {'file': str(file), 'exists': file.exists()}
    if row['exists']:
        row['sha256'] = sha(file)
    return row


def one(candidates, label):
    candidates = list(candidates)
    assert len(candidates) == 1, (label, len(candidates))
    return candidates[0]


def write_new(file, value):
    file = Path(file)
    assert file.parent == RECEIPTS and not file.exists(), 'Receipts are never overwritten: ' + str(file)
    file.write_text(json.dumps(value, indent=1), encoding='utf-8')
    return {'file': str(file), 'sha256': sha(file)}


def load_helper():
    data = HELPER.read_bytes()
    assert hashlib.sha256(data).hexdigest() == HELPER_SHA, 'Frozen ground helper changed'
    module = types.ModuleType('s1_frozen_graph_helper')
    module.__file__ = str(HELPER)
    exec(compile(data, str(HELPER), 'exec'), module.__dict__)
    assert 'ARGS' not in module.__dict__ and 'RESULT' not in module.__dict__
    return module


def load_doc(file, expected_sha):
    file = Path(file).resolve(strict=True)
    assert file.is_relative_to(STAGE) and file.suffix == '.json', str(file)
    assert sha(file) == expected_sha, 'SHA-bound document changed: ' + str(file)
    return file, json.loads(file.read_text(encoding='utf-8-sig'))


def dirty(h):
    return {'maps': sorted(h.path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
            'content': sorted(h.path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}


def log_file():
    folder = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_log_dir()))
    return folder / (Path(unreal.Paths.get_project_file_path()).stem + '.log')


def log_scan(offset):
    """Anchored scan (review r2): named = lines naming S1 assets with a whole-word error/failure
    (not 'errors=0'-style counters); unattributed = anchored material-compile failures elsewhere.
    Per-error MI-permutation lines are LogMaterial Warnings; their 'Failed to compile Material ...
    Default Material will be used' header is what is anchored (INFERRED UE log format)."""
    file = log_file()
    data = file.read_bytes()
    assert len(data) >= offset, 'Editor log shrank/rotated since the recorded offset'
    lines = data[offset:].decode('utf-8', 'replace').splitlines()
    benign = re.compile(r'\berrors?\s*[=:]\s*0\b', re.I)
    word = re.compile(r'\b(error|errors|failed|failure)\b', re.I)
    named = [s for s in lines if any(n in s for n in LOG_NAMES) and not benign.search(s)
             and (word.search(s) or any(m in s for m in LOG_FAILURE_MARKERS))]
    unattributed = [s for s in lines if s not in named and (
        any(m in s for m in LOG_FAILURE_MARKERS[:2]) or
        (('LogMaterial' in s or 'LogShaderCompilers' in s) and LOG_FAILURE_MARKERS[2] in s))]
    return {'file': str(file), 'offset': offset, 'end': len(data), 'named_hits': named[:200],
            'unattributed_material_errors': unattributed[:200],
            'clean': not named and not unattributed}


# ----------------------------------------------------------------- guard
def load_activation(args, mode):
    """Root activation document (review r2): lease identity is never taken from args alone."""
    assert 'lease' not in args, 'Lease identity comes from the root activation document, not args'
    file, act = load_doc(args['root_activation'], args['root_activation_sha256'])
    assert not file.is_relative_to(PREP) and not file.is_relative_to(V2DIR), ('Activation must be root-written '
                                                                            'outside S1_Prep/S1v2', str(file))
    assert file.name.startswith(ACTIVATION_PREFIX), ('Activation file name prefix', file.name)
    assert act.get('schema') == ACTIVATION_SCHEMA and act.get('scope') == S1_SCOPE, 'Not an S1v2 root activation'
    assert mode in act['modes'], ('Mode not activated by root', mode)
    for key in ('OWNER', 'manager_thread_id', 'operator_thread_id'):
        assert isinstance(act.get(key), str) and act[key] and ' ' not in act[key] and '<' not in act[key], key
    assert act['OWNER'] not in FOREIGN_OWNERS, ('Activation names a non-S1 owner', act['OWNER'])
    assert int(act['assigned_editor_PID']) == os.getpid() == int(args['expected_pid']), 'Activation is for another PID'
    assert act['areas'] and set(act['areas']) <= set(MAPS) and act['map'] in MAPS.values(), 'Activation areas/map'
    assert type(act['expected_hda_count']) is int and type(act['max_tune_iterations']) is int, 'Activation counts'
    assert list(act['authoring_activations']) and all(isinstance(a, str) and a for a in act['authoring_activations'])
    return file, act


def guard(h, args, mode):
    """Own lease/runtime guard (pattern GP native_graph_stochastic.py:192-217) bound to the root
    activation: OWNER/manager/operator/PID/map from the document, scope=S1_SCOPE for mutation."""
    mutate = mode in MUTATING
    act_file, act = load_activation(args, mode)
    line = [s for s in (ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(
        encoding='utf-8-sig').splitlines() if s.strip()][-1]
    fields = dict(token.split('=', 1) for token in line.split() if '=' in token)
    assert fields.get('OWNER') == act['OWNER'], ('Lease OWNER', fields.get('OWNER'))
    assert fields.get('manager_thread_id') == act['manager_thread_id'], 'Lease manager_thread_id'
    assert fields.get('operator_thread_id') == act['operator_thread_id'], 'Lease operator_thread_id'
    assert fields.get('assigned_editor_PID') == str(os.getpid()), 'Lease PID'
    pair = [fields.get('activation'), fields.get('scope')]
    authoring = fields.get('scope') == S1_SCOPE and fields.get('activation') in act['authoring_activations']
    readonly = (not mutate) and pair in [list(p) for p in act.get('readonly_pairs') or []]
    assert authoring or readonly, ('Lease line is not an S1 lease for this mode', mode, pair)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    assert fields.get('map') == named_map == act['map'], (fields.get('map'), named_map, act['map'])
    area = one((k for k, v in MAPS.items() if v == named_map), 'original Gaza map')
    assert area in act['areas'], ('Area not activated by root', area)
    import geocity_runtime_guard
    sources = geocity_runtime_guard.verify()
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    assert api and api.is_asset_cooking_paused(), 'Houdini cooking must stay paused'
    assert not unreal.get_default_object(unreal.load_class(
        None, '/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
    assert not any(getattr(run, key, None) is not None for name in
                   ('geocity_bank_workflow', 'geocity_roadbld_workflow') for run in
                   getattr(sys.modules.get(name), 'ACTIVE', []) for key in
                   ('watch_tick', 'save_tick', 'tick_handle', '_pending_correction'))
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    hdas = [a for a in actors if isinstance(a, unreal.HoudiniAssetActor)]
    assert len(hdas) == act['expected_hda_count'], ('HDA count', len(hdas))  # GP :213 exact count
    for actor in hdas:
        wrapper = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None, actor)
        assert not wrapper.is_auto_cooking_enabled() and not wrapper.is_auto_bake_enabled()
    landscapes = [a for a in actors if isinstance(a, unreal.LandscapeProxy)]
    assert landscapes, 'No Landscape in the original map'
    for actor in landscapes:
        assert h.path(actor.get_editor_property('landscape_material')) == obj_path(CHILDREN[area]), h.path(actor)
    return {'lease_line': line, 'sources': sources, 'world': named_map, 'area': area,
            'actors': actors, 'hda_count': len(hdas), 'landscapes': sorted(h.path(a) for a in landscapes),
            'activation': act, 'activation_file': {'file': str(act_file), 'sha256': sha(act_file)},
            'lease_kind': 'authoring' if authoring else 'readonly'}


def script_identity(args, act):
    """The executed file must be byte-identical to the reviewed S1v2 copy and to the SHA the
    root activation and args name (review r2). Hashing a file cannot prove which code object runs;
    the runner must exec exactly the named file's bytes (GP copilot_call.py:21-25 pattern)."""
    canonical = sha(SCRIPT)
    named = args.get('executed_script_file')
    if '__file__' in globals():
        executed = Path(globals()['__file__']).resolve(strict=True)
        assert named is None or Path(named).resolve(strict=True) == executed, 'executed_script_file differs from __file__'
    else:
        assert named, 'Runner must name the executed copy in args executed_script_file when __file__ is absent'
        executed = Path(named).resolve(strict=True)
    assert executed == SCRIPT or executed.is_relative_to(STAGE), ('Executed copy outside Stage1_Ground', str(executed))
    executed_sha = sha(executed)
    assert executed_sha == canonical == args.get('script_sha256') == act['script_sha256'], 'Unreviewed script bytes'
    return canonical, {'file': str(executed), 'sha256': executed_sha}


def operator_preconditions(args):
    """Not measurable from Python (AssetEditorSubsystem.h:160/:186 FindEditorForAsset/GetAllEditedAssets
    are not UFUNCTIONs, MEASURED); the operator attests, the receipt records it."""
    pre = dict(args.get('operator_preconditions') or {})
    assert pre.get('no_asset_editors_open_on_s1_assets') is True, \
        'Operator must attest that no Material/MI/MF editor is open on S1 assets'
    return pre


def consumers():
    """Direct child instances of master and base MI (GetChildInstances, MaterialEditingLibrary.h:494;
    asset-registry read)."""
    rows = {}
    for parent in (MASTER, BASE):
        found = LIB.get_child_instances(unreal.load_asset(parent)) or []
        rows[parent] = sorted(pkg(str(a.package_name)) for a in found)
    return rows


def check_consumers(act):
    rows = consumers()
    expected = act.get('expected_consumers') or {MASTER: [BASE], BASE: sorted(CHILDREN.values())}
    assert rows == {k: sorted(v) for k, v in expected.items()}, \
        ('Unpinned consumers of master/base MI: root pins them in activation expected_consumers', rows)
    return rows


# ----------------------------------------------------------------- read-only state
def facts(nodes, roots):
    """Mirror of S1_Prep/graph_dump_tools.py facts() reachability (offline-comparable)."""
    def reach(start):
        seen, stack = set(), [start]
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in nodes:
                continue
            seen.add(cur)
            stack.extend(e['source'] for e in nodes[cur]['edges'].values() if e['source'])
        return seen
    grass_out = [k for k, v in nodes.items() if v['class'] == 'MaterialExpressionLandscapeGrassOutput']
    grass = set().union(*(reach(g) for g in grass_out)) if grass_out else set()
    every, active = set(grass), set(grass)
    live = {k: v for k, v in roots.items() if v}
    for root in live.values():
        every |= reach(root)
        for layer in LAYERS:
            edge = nodes[root]['edges'].get('Layer ' + layer) or {}
            if edge.get('source'):
                active |= reach(edge['source'])
    pins = 0
    for key in ('color', 'normal', 'roughness'):
        root = live.get(key)
        if root and nodes[root]['class'] == 'MaterialExpressionLandscapeLayerBlend':
            pins += sum(1 for p, e in nodes[root]['edges'].items() if p.startswith('Layer ') and e['source'])
    return {'node_count': len(nodes), 'graph_sha256': digest(nodes),
            'reachable_any_root_plus_grass': len(every), 'reachable_active4_plus_grass': len(active),
            'root_layer_pins_connected': pins}


def grass_contract(h, material, nodes_list, grass_type):
    """Read-only re-implementation of LW:321-344 (never reconnects, unlike LW:346-349)."""
    desc = lambda n: str(h.safe(n, 'desc') or '')
    outputs = [n for n in nodes_list if isinstance(n, unreal.MaterialExpressionLandscapeGrassOutput)]
    owned = [n for n in nodes_list if desc(n).startswith(GRASS_OWNER)]
    assert len(outputs) == 1, 'LW:321 exactly one LandscapeGrassOutput'
    assert len(owned) == 4, 'LW:323 exactly four owned Grass nodes'
    by = {}
    for label, cls in (('Ground', unreal.MaterialExpressionLandscapeLayerSample),
                       ('Density', unreal.MaterialExpressionScalarParameter),
                       ('GroundDensity', unreal.MaterialExpressionMultiply),
                       ('Output', unreal.MaterialExpressionLandscapeGrassOutput)):
        match = [n for n in nodes_list if desc(n) == GRASS_OWNER + ':' + label]
        assert len(match) == 1 and isinstance(match[0], cls), 'LW:340 ' + label
        by[label] = match[0]
    assert h.path(by['Output']) == h.path(outputs[0])
    entries = list(by['Output'].get_editor_property('grass_types'))
    assert len(entries) == 1 and entries[0].get_editor_property('grass_type') == grass_type, 'LW:326'
    assert str(entries[0].get_editor_property('name')) == 'GeoCityGroundGrass', 'LW:326'
    assert str(by['Ground'].get_editor_property('parameter_name')) == 'Sand_01', 'LW:329'
    assert str(by['Density'].get_editor_property('parameter_name')) == 'GeoCity_GrassCoverage', 'LW:344'
    assert float(by['Density'].get_editor_property('default_value')) == 0.0, 'LW:344 coverage default 0.0'
    edges = dict((n, h.path(s)) for n, s in h.inputs(material, by['GroundDensity']))
    assert edges == {'A': h.path(by['Ground']), 'B': h.path(by['Density'])}, 'LW:346 edges'
    out_edges = dict((n, h.path(s)) for n, s in h.inputs(material, by['Output']))
    assert out_edges == {'GeoCityGroundGrass': h.path(by['GroundDensity'])}, 'LW:347 edge'
    return {'graph': {p: h.describe(material, e) for p, e in h.reachable(material, outputs).items()},
            'settings': h.grass_settings(grass_type), 'owned': {k: h.path(v) for k, v in by.items()}}


def switch_state(material, instances):
    names = sorted(str(n) for n in LIB.get_static_switch_parameter_names(material))
    return {'names': names,
            'defaults': {n: bool(LIB.get_material_default_static_switch_parameter_value(material, n)) for n in names},
            'instances': {p: {n: bool(LIB.get_material_instance_static_switch_parameter_value(mi, n)) for n in names}
                          for p, mi in instances.items()}}


def statistics(material_interface):
    try:
        stats = LIB.get_statistics(material_interface)
        return {k: int(stats.get_editor_property(k)) for k in STAT_FIELDS}
    except Exception as error:
        return {'error': repr(error)}


def statistics_gate(child, base):
    """INFERRED gate (review r2): the child's static permutation (switch True) has a resource with
    pixel instructions that differs from the base MI's False permutation; an uncompiled permutation or
    a default-material fallback is expected to fail this. Any read error fails closed. Run before the
    save latch, so a not-yet-finished compile can be retried later in the same PID."""
    c, b = statistics(child), statistics(base)
    assert 'error' not in c and 'error' not in b, ('get_statistics failed', c, b)
    assert c['num_pixel_shader_instructions'] > 0 and c != b, ('Child S1 permutation not compiled/distinct', c, b)
    return {'child': c, 'base': b}


def load_assets(h):
    material = unreal.load_asset(MASTER)
    base = unreal.load_asset(BASE)
    grass = unreal.load_asset(GRASS)
    children = {a: unreal.load_asset(p) for a, p in CHILDREN.items()}
    assert isinstance(material, unreal.Material) and isinstance(base, unreal.MaterialInstanceConstant)
    assert isinstance(grass, unreal.LandscapeGrassType)
    assert h.path(base.get_editor_property('parent')) == obj_path(MASTER), 'LW:222-224 parent chain'
    for area, child in children.items():
        assert isinstance(child, unreal.MaterialInstanceConstant), area
        assert child.get_editor_property('parent') == base, 'LW:368/416 child parent ' + area
    instances = {BASE: base, **{CHILDREN[a]: c for a, c in children.items()}}
    return material, base, grass, children, instances


def snapshot(h, ctx):
    material, base, grass, children, instances = load_assets(h)
    nodes_list = list(LIB.get_material_expressions(material))
    nodes = {h.path(e): h.describe(material, e) for e in nodes_list}
    roots = {k: h.path(LIB.get_material_property_input_node(material, prop)) for k, prop in h.PROPERTIES.items()}
    return {'nodes': nodes, 'roots': roots, 'facts': facts(nodes, roots),
            'material_settings': {k: h.plain(material.get_editor_property(k)) for k in SETTINGS},
            'instances': {p: h.material_state(material, mi) for p, mi in instances.items()},
            'switches': switch_state(material, instances),
            'grass': grass_contract(h, material, nodes_list, grass),
            'scene_sha256': digest(h.scene_state(ctx['actors'])),
            'dirty': dirty(h)}


def resolve_anchors(h, material, snap):
    """Existing anchors: unique desc rows (ANCHORS) and unique active-set parameters (PARAM_ANCHORS,
    ROUGHNESS); root Layer edges must still be the measured B0 sources (drift guard)."""
    nodes_list = list(LIB.get_material_expressions(material))
    by_desc = {}
    for e in nodes_list:
        by_desc.setdefault(str(h.safe(e, 'desc') or ''), []).append(e)
    found = {}
    for key, (desc, cls, suffix, output) in ANCHORS.items():
        e = one(by_desc.get(desc, []), 'anchor ' + key)
        assert e.get_class().get_name() == 'MaterialExpression' + cls, (key, e.get_class().get_name())
        assert h.path(e).endswith(':MaterialExpression' + suffix), (key, h.path(e))
        outs = list(LIB.get_material_expression_output_names(e))
        assert output in outs or (output == '' and outs), (key, outs)
        found[key] = (e, output)
    roots = {k: LIB.get_material_property_input_node(material, prop) for k, prop in h.PROPERTIES.items()}
    for key, suffix in ROOT_LLB.items():
        assert isinstance(roots[key], unreal.MaterialExpressionLandscapeLayerBlend), key
        assert h.path(roots[key]).endswith(':MaterialExpression' + suffix), (key, h.path(roots[key]))
        names = [str(x.get_editor_property('layer_name')) for x in roots[key].get_editor_property('layers')]
        assert len(names) == len(set(names)) == 69 and set(LAYERS) <= set(names), key
    assert all(roots[k] is None for k in ('specular', 'metallic', 'emissive', 'wpo', 'opacity', 'opacity_mask'))
    active = h.reachable(material, [roots[k] for k in ('color', 'normal', 'roughness')])
    for layer, suffix in ROUGHNESS.items():
        e = h.parameter(active, layer + '_Roughness', unreal.MaterialExpressionScalarParameter)
        assert h.path(e).endswith(':MaterialExpression' + suffix), (layer, h.path(e))
        found['rough_' + layer] = (e, '')
    for key, (name, cls, suffix, output) in PARAM_ANCHORS.items():
        e = h.parameter(active, name, getattr(unreal, 'MaterialExpression' + cls))
        assert h.path(e).endswith(':MaterialExpression' + suffix), (key, name, h.path(e))
        outs = list(LIB.get_material_expression_output_names(e))
        assert output in outs or (output == '' and outs), (key, outs)
        found[key] = (e, output)
    for (root, layer), key in ROOT_LAYER_EXPECT.items():
        edge = snap['nodes'][h.path(roots[root])]['edges']['Layer ' + layer]
        assert edge['source'] == h.path(found[key][0]) and edge['output'] in ('', None), ('root layer drift', root, layer, edge)
    for (root, layer), suffix in ROOT_LAYER_SUFFIX.items():
        edge = snap['nodes'][h.path(roots[root])]['edges']['Layer ' + layer]
        assert (edge['source'] or '').endswith(':MaterialExpression' + suffix), ('root layer drift', root, layer, edge)
    for layer in LAYERS:
        edge = snap['nodes'][h.path(roots['roughness'])]['edges']['Layer ' + layer]
        assert edge['source'] == h.path(found['rough_' + layer][0]), ('roughness drift', layer)
    texture_params = {}
    for name, kind in EXISTING_CHILD.items():
        if kind == 'texture':
            e = h.parameter(active, name, unreal.MaterialExpressionTextureObjectParameter)
            texture_params[name] = one((k for k, v in SAMPLER.items() if v == e.get_editor_property('sampler_type')), name)
        else:
            h.parameter(active, name, unreal.MaterialExpressionVectorParameter)
    for key in ('steep_albedo', 'road_albedo', 'pad_albedo'):  # CellSample fetches are COLOR
        assert found[key][0].get_editor_property('sampler_type') == SAMPLER['COLOR'], (key, 'sampler type')
    return found, roots, texture_params


def derivative_probe(h, snap):
    """Read-only evidence that TMVM_DERIVATIVE TextureSample nodes expose 'DDX(UVs)'/'DDY(UVs)' input pins
    and that they are connected from Python-authored nodes (existing GroundStochastic master samples)."""
    mode = h.plain(MIP['derivative'])
    rows = {p: r for p, r in snap['nodes'].items() if r['class'] == 'MaterialExpressionTextureSample'
            and r['properties'].get('mip_value_mode') == mode}
    connected = sorted(p for p, r in rows.items() if all(n in r['input_names'] and r['edges'][n]['source']
                                                         for n in DERIVATIVE_PINS))
    return {'derivative_samples': len(rows), 'pins_connected': len(connected), 'pin_names': list(DERIVATIVE_PINS),
            'example': connected[:1], 'label': 'MEASURED on master expressions; inside a MaterialFunction the same '
                                                'class is INFERRED to expose the same pins (asserted per fetch at apply)'}


# ----------------------------------------------------------------- plan validation
def plan_children(args, texture_params):
    areas = list(args['areas'])
    assert areas and set(areas) <= set(MAPS) and len(set(areas)) == len(areas), areas
    values = args['child_values']
    assert set(values) == set(areas), 'child_values must cover exactly the areas in scope'
    plans = {}
    for area in areas:
        row = values[area]
        assert set(row) <= {'textures', 'vectors', 'scalars'}, area
        plan = {'textures': {}, 'vectors': {}, 'scalars': {}}
        for name, value in row.get('textures', {}).items():
            spec = PARAMS.get(name)
            kind = spec[2] if spec and spec[0] == 'texture' else texture_params.get(name)
            assert kind, 'Texture parameter not allowed for S1 child override: ' + name
            path = obj_path(value)
            if path in NOISE_FALLBACK.get(name, ()):  # Epic-owned macro noise if the MW licence fails
                assert args.get('epic_noise_fallback') is True, 'Epic noise fallback needs args epic_noise_fallback=true'
            plan['textures'][name] = {'path': path, 'kind': kind}
        for name, value in row.get('vectors', {}).items():
            spec = PARAMS.get(name)
            assert (spec and spec[0] == 'vector') or EXISTING_CHILD.get(name) == 'vector', name
            assert len(value) == 4 and all(math.isfinite(float(v)) for v in value), name
            plan['vectors'][name] = [f32(v) for v in value]
        for name, value in row.get('scalars', {}).items():
            spec = PARAMS.get(name)
            assert spec and spec[0] == 'scalar', 'Scalar not allowed for S1 child override: ' + name
            assert math.isfinite(float(value)), name
            if name.endswith(('TileCm', 'FarScale', 'NoiseInvStd')):
                assert float(value) > 0, name
            plan['scalars'][name] = f32(value)
        for name in CONTACT:
            if not args.get('contact_band_acknowledged'):
                assert plan['scalars'].get(name, 0.0) == 0.0, 'Correction 9: contact band needs root acknowledgement'
        coverage = (args.get('grass_coverage') or {}).get(area)
        if coverage is not None:  # decision 3 'no grass now': S1 may only zero it (reverts at prepare(), LW:374-382)
            assert float(coverage) == 0.0, 'Decision 3: S1 may set GeoCity_GrassCoverage only to 0.0'
            plan['scalars']['GeoCity_GrassCoverage'] = f32(coverage)
        assert not ({'Sand_01_Normal', 'Sand_02_Normal'} & set(plan['textures'])), 'LW:110-121 pinned normals'
        plans[area] = plan
    return plans


def texture_fit(h, path, kind, allowed_defaults):
    assert path.startswith(MW_TEXTURES) or path in allowed_defaults, 'Texture source not allowed: ' + path
    texture = unreal.load_asset(path)
    assert isinstance(texture, unreal.Texture2D), path
    srgb = bool(texture.get_editor_property('srgb'))
    compression = texture.get_editor_property('compression_settings')
    vt = h.safe(texture, 'virtual_texture_streaming')
    tc = unreal.TextureCompressionSettings
    ok = {'COLOR': srgb and compression in (tc.TC_DEFAULT, tc.TC_BC7),
          'NORMAL': not srgb and compression == tc.TC_NORMALMAP,
          'MASKS': not srgb and compression == tc.TC_MASKS}[kind] and not vt
    row = {'path': path, 'kind': kind, 'srgb': srgb, 'compression': str(compression),
           'virtual_texture_streaming': h.plain(vt), 'size_x': int(texture.blueprint_get_size_x()),
           'size_y': int(texture.blueprint_get_size_y())}
    assert ok, ('Sampler/texture mismatch (compile error, not fallback)', row)
    return row


def master_textures(snap):
    return sorted({r['properties']['texture'] for r in snap['nodes'].values() if r['properties'].get('texture')})


def master_allowed_textures(snap):
    allowed = set(master_textures(snap))
    for name, (kind, default, sampler) in PARAMS.items():
        if kind == 'texture':
            assert default in allowed, 'Master default must reuse an existing master reference: ' + default
    return allowed


def fallback_textures(plans):
    """Fallback paths already gated by plan_children (args epic_noise_fallback)."""
    return {t['path'] for plan in plans.values() for n, t in plan['textures'].items()
            if t['path'] in NOISE_FALLBACK.get(n, ())}


def check_textures(h, plans, allowed):
    before = dirty(h)
    allowed = set(allowed) | fallback_textures(plans)
    rows = {area: {n: texture_fit(h, t['path'], t['kind'], allowed) for n, t in plan['textures'].items()}
            for area, plan in plans.items()}
    assert dirty(h) == before, 'Loading planned textures dirtied packages'
    return rows


def mw_files(plans):
    """Vendor texture files bound to children (MW pack, plus the Epic noise fallback when used)."""
    files = sorted({str(package_file(t['path'])) for plan in plans.values() for t in plan['textures'].values()
                    if t['path'].startswith(MW_TEXTURES)} | {str(package_file(p)) for p in fallback_textures(plans)})
    return {f: sha(f) for f in files}


def backup_pins(manifest):
    """{absolute file: sha256} from file_bindings + preserved_files + sealed_files.
    Accepts the REV schema and S1_Prep/s1_backup.py BACKUP_MANIFEST.json (there the Grass type
    and maps are copied: file_bindings rows plus equal preserved_files pins)."""
    pins = {}
    for key, row in manifest['file_bindings'].items():
        pins[str(Path(key).resolve(strict=True))] = row['sha256']
    for family in ('preserved_files', 'sealed_files'):
        for relative, expected in (manifest.get(family) or {}).items():
            file = (ROOT / relative).resolve(strict=True)
            assert file.is_relative_to(ROOT), relative
            assert pins.get(str(file), expected) == expected, ('Conflicting manifest pins', relative)
            pins[str(file)] = expected
    return pins


def function_packages(names=None):
    return [FUNCTION_DIR + '/' + n for n in (FUNCTIONS if names is None else names)]


def functions_absent():
    """Neither the v1 (never saved) nor the v2 function packages may exist before apply."""
    rows = {}
    for package in function_packages(V1_FUNCTIONS) + function_packages():
        rows[package] = {'registry': bool(unreal.EditorAssetLibrary.does_asset_exist(package)),
                         'disk': package_file(package).exists()}
        assert not rows[package]['registry'] and not rows[package]['disk'], ('Function package already exists', package)
    return rows


def check_backup(args):
    """Reused v1 backup (S1_Prep/s1_backup.py). Its new_asset_paths names the v1 packages; v2 accepts exactly
    that list or the v2 list and asserts both sets absent. The v2 rollback list is the apply receipt's
    created_functions."""
    file, manifest = load_doc(args['backup_manifest'], args['backup_manifest_sha256'])
    assert manifest['ready'] is True
    listed = sorted(manifest['new_asset_paths'])
    assert listed in (sorted(function_packages(V1_FUNCTIONS)), sorted(function_packages())), \
        ('Backup manifest new_asset_paths is neither the v1 nor the v2 function list', listed)
    bindings = {str(Path(k).resolve(strict=True)): v for k, v in manifest['file_bindings'].items()}
    copied = [package_file(MASTER), package_file(BASE), *(package_file(p) for p in CHILDREN.values())]
    missing = sorted(str(p.resolve()) for p in copied if str(p.resolve()) not in bindings)
    assert not missing, ('Backup manifest lacks copies of', missing)
    for source, row in bindings.items():
        backup = Path(row['backup']).resolve(strict=True)
        assert Path(source).is_relative_to(ROOT) and backup.is_relative_to(STAGE), source
        assert sha(source) == sha(backup) == row['sha256'], 'Backup/source differs: ' + source
    pins = backup_pins(manifest)
    pinned = [package_file(GRASS), *(package_file(p, '.umap') for p in MAPS.values())]
    missing = sorted(str(p.resolve()) for p in pinned if str(p.resolve()) not in pins)
    assert not missing, ('Backup manifest lacks pins for', missing)
    for source, expected in pins.items():
        assert sha(source) == expected, 'Pinned file changed since backup: ' + source
    functions_absent()
    return file, pins


# ----------------------------------------------------------------- graph builder
class Builder:
    """Node creation/link helpers; precedents GP native_graph_revision.py:333-379 and
    native_graph_stochastic.py:520-552 (create, desc, set_editor_property, validated link)."""

    def __init__(self, owner, in_function, x0, y0, cols, xstep=240, ystep=230):
        self.owner, self.in_function = owner, in_function
        self.x0, self.y0, self.cols, self.xstep, self.ystep = x0, y0, cols, xstep, ystep
        self.added = []

    def node(self, cls, label, adopt=None, **properties):
        i = len(self.added)
        x, y = self.x0 + (i % self.cols) * self.xstep, self.y0 + (i // self.cols) * self.ystep
        if adopt is not None:  # factory-created node of a brand-new MF package
            assert isinstance(adopt, cls), label
            e = adopt
        elif self.in_function:
            e = LIB.create_material_expression_in_function(self.owner, cls, x, y)
        else:
            e = LIB.create_material_expression(self.owner, cls, x, y)
        assert e is not None, label
        self.added.append(e)
        e.set_editor_property('desc', MARK + label)
        for key, value in properties.items():
            e.set_editor_property(key, value)
        return e

    @staticmethod
    def link(source, target, pin):
        expr, output = source if isinstance(source, tuple) else (source, '')
        names = list(LIB.get_material_expression_input_names(target))
        assert pin in names, (target.get_name(), pin, names)
        outputs = list(LIB.get_material_expression_output_names(expr))
        assert output in outputs or (output == '' and outputs), (expr.get_name(), output, outputs)
        assert LIB.connect_material_expressions(expr, output, target, pin), (target.get_name(), pin)

    def op(self, cls, label, a=None, b=None, **properties):
        e = self.node(cls, label, **properties)
        if a is not None:
            self.link(a, e, 'A')
        if b is not None:
            self.link(b, e, 'B')
        return e

    def mul(self, label, a, b):
        return self.op(unreal.MaterialExpressionMultiply, label, a, b)

    def mul_c(self, label, a, c):
        return self.op(unreal.MaterialExpressionMultiply, label, a, const_b=float(c))

    def add(self, label, a, b):
        return self.op(unreal.MaterialExpressionAdd, label, a, b)

    def add_c(self, label, a, c):
        return self.op(unreal.MaterialExpressionAdd, label, a, const_b=float(c))

    def sub(self, label, a, b):
        return self.op(unreal.MaterialExpressionSubtract, label, a, b)

    def div(self, label, a, b):
        return self.op(unreal.MaterialExpressionDivide, label, a, b)

    def max_c(self, label, a, c):
        return self.op(unreal.MaterialExpressionMax, label, a, const_b=float(c))

    def max(self, label, a, b):
        return self.op(unreal.MaterialExpressionMax, label, a, b)

    def dot(self, label, a, b):
        return self.op(unreal.MaterialExpressionDotProduct, label, a, b)

    def append(self, label, a, b):
        return self.op(unreal.MaterialExpressionAppendVector, label, a, b)

    def single(self, cls, label, x, pin='None', **properties):
        e = self.node(cls, label, **properties)
        self.link(x, e, pin)
        return e

    def sat(self, label, x):
        return self.single(unreal.MaterialExpressionSaturate, label, x)

    def one_minus(self, label, x):
        return self.single(unreal.MaterialExpressionOneMinus, label, x)

    def normalize(self, label, x):
        return self.single(unreal.MaterialExpressionNormalize, label, x, 'VectorInput')

    def clamp(self, label, x, low, high):
        return self.single(unreal.MaterialExpressionClamp, label, x, min_default=float(low), max_default=float(high))

    def mask(self, label, x, channel):
        flags = {c: c == channel for c in 'rgba'}
        return self.single(unreal.MaterialExpressionComponentMask, label, x, **flags)

    def ddx(self, label, x):  # pin 'Value' (M: GRAPH_BEFORE DDX_0/DDY_0 input_names)
        return self.single(unreal.MaterialExpressionDDX, label, x, 'Value')

    def ddy(self, label, x):
        return self.single(unreal.MaterialExpressionDDY, label, x, 'Value')

    def lerp(self, label, a, b, alpha):
        properties = {'const_a': float(a)} if isinstance(a, (int, float)) else {}
        e = self.node(unreal.MaterialExpressionLinearInterpolate, label, **properties)
        if not properties:
            self.link(a, e, 'A')
        self.link(b, e, 'B')
        self.link(alpha, e, 'Alpha')
        return e

    def smooth(self, label, low, high, value):
        properties = {}
        if isinstance(low, (int, float)):
            properties['const_min'] = float(low)
        if isinstance(high, (int, float)):
            properties['const_max'] = float(high)
        e = self.node(unreal.MaterialExpressionSmoothStep, label, **properties)
        if 'const_min' not in properties:
            self.link(low, e, 'Min')
        if 'const_max' not in properties:
            self.link(high, e, 'Max')
        self.link(value, e, 'Value')
        return e

    def c2(self, label, x, y):
        return self.node(unreal.MaterialExpressionConstant2Vector, label, r=float(x), g=float(y))

    def c3(self, label, x, y, z):
        return self.node(unreal.MaterialExpressionConstant3Vector, label,
                         constant=unreal.LinearColor(float(x), float(y), float(z), 0.0))

    def sample(self, label, texture, uv, kind, output='RGB'):
        # Continuous-UV fetch: Shared:Wrap, TMVM_NONE (precedent native_graph_stochastic.py:593-595).
        e = self.node(unreal.MaterialExpressionTextureSample, label, sampler_type=SAMPLER[kind],
                      sampler_source=WRAP, mip_value_mode=MIP['none'])
        self.link(uv, e, 'UVs')
        self.link(texture, e, 'Tex')
        return (e, output)

    def sample_cell(self, label, texture, uv, ddx, ddy, kind):
        """Translated-UV fetch of the CellSample function. 'derivative': TMVM_DERIVATIVE set FIRST, then the
        'DDX(UVs)'/'DDY(UVs)' pins (dynamic, present only in that mode) must exist and are linked to the
        derivatives of the UNTRANSLATED UV (no cell seams; GP native_graph_stochastic.py:593-598).
        'gradient_free': TMVM_NONE, hardware derivatives of the translated UV (ddx/ddy must be None)."""
        mode = CELL_MIP['mode']
        assert mode in ('derivative', 'gradient_free'), ('CELL_MIP mode unset', mode)
        e = self.node(unreal.MaterialExpressionTextureSample, label, sampler_type=SAMPLER[kind],
                      sampler_source=WRAP, mip_value_mode=MIP[mode])
        names = list(LIB.get_material_expression_input_names(e))
        if mode == 'derivative':
            assert all(p in names for p in DERIVATIVE_PINS), \
                ('STOP: derivative pins absent in this engine; root decides on cell_sample_mip_mode=gradient_free', label, names)
            assert ddx is not None and ddy is not None, label
        else:
            assert ddx is None and ddy is None, label
        self.link(uv, e, 'UVs')
        self.link(texture, e, 'Tex')
        if mode == 'derivative':
            self.link(ddx, e, DERIVATIVE_PINS[0])
            self.link(ddy, e, DERIVATIVE_PINS[1])
        return (e, 'RGB')

    def rotate2(self, label, uv, degrees):
        """(dot(uv, (cos, -sin)), dot(uv, (sin, cos))) with constant rows."""
        c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
        u = self.dot(label + 'U', uv, self.c2(label + 'RowU', c, -s))
        v = self.dot(label + 'V', uv, self.c2(label + 'RowV', s, c))
        return self.append(label + 'UV', u, v)

    def call(self, label, function, spec, connections):
        e = self.node(unreal.MaterialExpressionMaterialFunctionCall, label, material_function=function)
        names = list(LIB.get_material_expression_input_names(e))
        assert names == [n for n, _ in spec['inputs']], (label, names)
        outputs = list(LIB.get_material_expression_output_names(e))
        assert outputs == [n for n, _ in spec['outputs']], (label, outputs)
        assert set(connections) == set(names), (label, sorted(connections))
        for pin, source in connections.items():
            self.link(source, e, pin)
        return e


# ----------------------------------------------------------------- function bodies
def body_cell_sample(g, i):
    """SPEC MF_GeoCity_CellSample: 4 near + 4 far taps at UV + hash_i through the existing Sand_01 lattice."""
    derivative = CELL_MIP['mode'] == 'derivative'
    far_scale = g.max_c('FarScaleMin1', i['FarScale'], 1.0)
    far_uv = g.div('FarUV', i['NearUV'], far_scale)
    if derivative:
        dxn, dyn = g.ddx('NearUVDDX', i['NearUV']), g.ddy('NearUVDDY', i['NearUV'])
        dxf, dyf = g.div('FarUVDDX', dxn, far_scale), g.div('FarUVDDY', dyn, far_scale)
    else:
        dxn = dyn = dxf = dyf = None
    blends = {}
    for scale, uv, dx, dy in (('Near', i['NearUV'], dxn, dyn), ('Far', far_uv, dxf, dyf)):
        taps = [g.sample_cell(scale + 'Tap' + str(k), i['Tex'], g.add(scale + 'TapUV' + str(k), uv, i[scale + 'Hash' + str(k)]),
                              dx, dy, 'COLOR') for k in range(4)]
        bottom = g.lerp(scale + 'Bottom', taps[0], taps[1], i[scale + 'WX'])
        top = g.lerp(scale + 'Top', taps[2], taps[3], i[scale + 'WX'])
        blends[scale] = g.lerp(scale + 'CellBlend', bottom, top, i[scale + 'WY'])
    color = g.lerp('NearFarBlend', blends['Near'], blends['Far'], g.sat('DistanceAlphaSaturated', i['DistanceAlpha']))
    return {'Color': color, 'Near': blends['Near'], 'Far': blends['Far']}


def body_macro_field(g, i):
    """SPEC MF_GeoCity_MacroField: 3 octaves of one noise texture, linear outputs (no thresholds)."""
    z = {}
    for name, channel, degrees, offset in OCTAVES:
        uv = i['LandscapeUV'] if not degrees else g.rotate2('Octave' + name + 'Rot', i['LandscapeUV'], degrees)
        scale = g.div('Octave' + name + 'CmToUV', i['GridCm'], g.max_c('Octave' + name + 'TilePositive', i['Tile' + name + 'Cm'], 1.0))
        shifted = g.add('Octave' + name + 'UV', g.mul('Octave' + name + 'Scaled', uv, scale),
                        g.c2('Octave' + name + 'Offset', *offset))
        n = g.sample('Octave' + name + 'Sample', i['NoiseTex'], shifted, 'MASKS', channel)
        z[name] = g.mul('Octave' + name + 'Z', g.sub('Octave' + name + 'Centered', n, i['NoiseMean']), i['NoiseInvStd'])
    value = g.add('ValueSum', g.add('ValueSum12', g.mul_c('ValueW1', z['1'], 0.25), g.mul_c('ValueW2', z['2'], 0.35)),
                  g.mul_c('ValueW3', z['3'], 0.40))
    hue = g.add('HueMix', g.mul_c('HueW2', z['2'], 0.4), g.mul_c('HueW3', z['3'], 0.6))
    variant_b = g.add('VariantBMix', g.mul_c('VariantBW1', z['1'], 0.6), g.mul_c('VariantBW2', z['2'], 0.4))
    variant_c = g.add('VariantCMix', g.mul_c('VariantCW1', z['1'], 0.4), g.mul_c('VariantCW2', z['2'], -0.6))

    def unit(label, x, gain):
        return g.sat(label, g.add_c(label + 'Centered', g.mul(label + 'Gained', x, gain), 0.5))

    return {'Value': value, 'HueT': unit('HueT', hue, i['HueGain']),
            'VariantB': unit('VariantB', variant_b, i['VariantGain']),
            'VariantC': unit('VariantC', variant_c, i['VariantGain']), 'Fine': z['1']}


def body_macro_color(g, i):
    """SPEC MF_GeoCity_MacroColor (new body): symmetric hue pair, value +-, optional far desaturation."""
    tint = g.lerp('HueTint', 1.0, g.lerp('HueBA', i['HueB'], i['HueA'], i['HueT']), i['HueAmount'])
    value = g.add_c('ValueMultiplier', g.mul('ValueOffset', g.clamp('ValueClamped', i['Value'], -2.0, 2.0),
                                             i['ValueAmount']), 1.0)
    color = g.mul('ValueColor', g.mul('TintedBase', i['Base'], tint), value)
    luma = g.dot('Luminance', color, g.c3('LumaWeights', *LUMA))
    far = g.mul('FarValueColor', g.lerp('FarSaturationColor', luma, color, i['FarSaturation']), i['FarValue'])
    alpha = g.sat('FarAlpha', g.mul('FarAlphaRaw', i['DistanceAlpha'], i['FarAmount']))
    return {'Color': g.sat('ColorOut', g.lerp('FarBlend', color, far, alpha))}


def body_slope_blend(g, i):
    span = COS15 - COS35
    slope = g.sat('SlopeWeight', g.add_c('SlopeOffset', g.mul_c('SlopeScaled', i['NormalZ'], -1.0 / span), COS15 / span))
    mixed = g.lerp('PaintSlopeMix', i['SteepWeight'], slope, i['SlopeMix'])
    jitter = g.mul('JitterScaled', g.add_c('NoiseCentered', i['Noise'], -0.5), i['Jitter'])
    return {'Alpha': g.smooth('SteepAlpha', i['Lo'], i['Hi'], g.add('SteepDriver', mixed, jitter))}


def body_height_blend(g, i):
    luma = g.c3('LumaWeights', *LUMA)
    detail = g.sub('LumaDetail', g.dot('NearLuma', i['Near'], luma), g.dot('FarLuma', i['Far'], luma))
    height = g.sat('HeightRaw', g.add('HeightBiased', i['Bias'], g.mul('DetailContrast', detail, i['Contrast'])))
    # Correction 2: H = lerp(1-w, h, Amount); Amount 0 -> clamp(2w-1+1-w)=w, identity (INFERRED LLB math).
    return {'Height': g.lerp('HeightAmountBlend', g.one_minus('IdentityHeight', i['Weight']), height, i['Amount'])}


CELL_INPUTS = ([('Tex', 'T2D'), ('NearUV', 'V2'), ('FarScale', 'S')]
               + [('NearHash' + str(k), 'V2') for k in range(4)] + [('FarHash' + str(k), 'V2') for k in range(4)]
               + [('NearWX', 'S'), ('NearWY', 'S'), ('FarWX', 'S'), ('FarWY', 'S'), ('DistanceAlpha', 'S')])
FUNCTIONS = {
    'MF_GeoCityV2_CellSample': {'inputs': CELL_INPUTS, 'outputs': [('Color', 'V3'), ('Near', 'V3'), ('Far', 'V3')],
                                'body': body_cell_sample, 'samples': {'COLOR': 8}, 'cell_mip': True},
    'MF_GeoCityV2_MacroField': {'inputs': [('NoiseTex', 'T2D'), ('LandscapeUV', 'V2'), ('GridCm', 'S'), ('Tile1Cm', 'S'),
                                           ('Tile2Cm', 'S'), ('Tile3Cm', 'S'), ('NoiseMean', 'S'), ('NoiseInvStd', 'S'),
                                           ('HueGain', 'S'), ('VariantGain', 'S')],
                                'outputs': [('Value', 'S'), ('HueT', 'S'), ('VariantB', 'S'), ('VariantC', 'S'), ('Fine', 'S')],
                                'body': body_macro_field, 'samples': {'MASKS': 3}, 'cell_mip': False},
    'MF_GeoCityV2_MacroColor': {'inputs': [('Base', 'V3'), ('Value', 'S'), ('HueT', 'S'), ('HueA', 'V3'), ('HueB', 'V3'),
                                           ('HueAmount', 'S'), ('ValueAmount', 'S'), ('DistanceAlpha', 'S'),
                                           ('FarSaturation', 'S'), ('FarValue', 'S'), ('FarAmount', 'S')],
                                'outputs': [('Color', 'V3')], 'body': body_macro_color, 'samples': {}, 'cell_mip': False},
    'MF_GeoCityV2_SlopeBlend': {'inputs': [('SteepWeight', 'S'), ('NormalZ', 'S'), ('Noise', 'S'), ('Lo', 'S'),
                                           ('Hi', 'S'), ('Jitter', 'S'), ('SlopeMix', 'S')],
                                'outputs': [('Alpha', 'S')], 'body': body_slope_blend, 'samples': {}, 'cell_mip': False},
    'MF_GeoCityV2_HeightBlend': {'inputs': [('Near', 'V3'), ('Far', 'V3'), ('Weight', 'S'), ('Bias', 'S'),
                                            ('Contrast', 'S'), ('Amount', 'S')],
                                 'outputs': [('Height', 'S')], 'body': body_height_blend, 'samples': {}, 'cell_mip': False},
}
FN_KEYS = ('desc', 'input_name', 'input_type', 'sort_priority', 'output_name', 'use_preview_value_as_default',
           'sampler_type', 'sampler_source', 'mip_value_mode', 'const_a', 'const_b', 'const_alpha', 'const_min',
           'const_max', 'min_default', 'max_default', 'r', 'g', 'b', 'a', 'constant', 'parameter_name',
           'material_function', 'texture', 'material_expression_editor_x', 'material_expression_editor_y',
           'material_expression_guid')


def describe_function(h, function):
    rows = {}
    for e in LIB.get_material_function_expressions(function):
        names = list(LIB.get_material_expression_input_names(e))
        sources = list(LIB.get_inputs_for_material_function_expression(function, e))  # GP native_function_probe.py:17
        assert len(names) == len(sources), (h.path(e), names)
        row = {'class': e.get_class().get_name(), 'input_names': names, 'edges': {}, 'properties': {},
               'output_names': list(LIB.get_material_expression_output_names(e))}
        for name, source in zip(names, sources):
            row['edges'][name] = {'source': h.path(source), 'output': str(
                LIB.get_input_node_output_name_for_material_expression(e, source)) if source else None}
        for key in FN_KEYS:
            value = h.safe(e, key)
            if value is not None:
                row['properties'][key] = h.plain(value)
        rows[h.path(e)] = row
    return rows


def check_function(h, name, spec, rows):
    classes = [r['class'] for r in rows.values()]
    assert not [c for c in classes if 'Parameter' in c], (name, 'parameter nodes inside function')
    assert all((r['properties'].get('desc') or '').startswith(MARK) for r in rows.values()), name
    inputs = sorted((r for r in rows.values() if r['class'] == 'MaterialExpressionFunctionInput'),
                    key=lambda r: r['properties']['sort_priority'])
    assert [r['properties']['input_name'] for r in inputs] == [n for n, _ in spec['inputs']], name
    assert [r['properties']['input_type'] for r in inputs] == [h.plain(FIN[k]) for _, k in spec['inputs']], name
    outputs = sorted((r for r in rows.values() if r['class'] == 'MaterialExpressionFunctionOutput'),
                     key=lambda r: r['properties']['sort_priority'])
    assert [r['properties']['output_name'] for r in outputs] == [n for n, _ in spec['outputs']], name
    assert all(all(e['source'] for e in r['edges'].values()) for r in outputs), (name, 'unconnected output')
    samples = [r for r in rows.values() if r['class'] == 'MaterialExpressionTextureSample']
    assert len(samples) == sum(spec['samples'].values()), (name, len(samples))
    for kind, count in spec['samples'].items():
        assert sum(r['properties']['sampler_type'] == h.plain(SAMPLER[kind]) for r in samples) == count, (name, kind)
    for r in samples:
        assert r['properties']['sampler_source'] == h.plain(WRAP), (name, 'sampler source')
        assert r['edges']['UVs']['source'] and r['edges']['Tex']['source'], (name, 'unconnected sample')
    derivative = spec['cell_mip'] and CELL_MIP['mode'] == 'derivative'
    want_mode = h.plain(MIP['derivative' if derivative else 'none'])
    assert all(r['properties']['mip_value_mode'] == want_mode for r in samples), (name, 'mip_value_mode', want_mode)
    for r in samples:  # every CellSample fetch: derivative pins present AND connected (derivative mode)
        has = [p in r['edges'] and bool(r['edges'][p]['source']) for p in DERIVATIVE_PINS]
        assert has == [derivative, derivative], (name, 'derivative pins', has)
    assert classes.count('MaterialExpressionDDX') == classes.count('MaterialExpressionDDY') == (1 if derivative else 0), \
        (name, 'DDX/DDY census')
    assert not [c for c in classes if c in ('MaterialExpressionPixelNormalWS', 'MaterialExpressionMaterialFunctionCall')], name


def build_function_graph(g, name, spec, factory_nodes=()):
    """FunctionInput nodes (explicit sort_priority) -> body -> FunctionOutput nodes."""
    inputs = {}
    for index, (pin, kind) in enumerate(spec['inputs']):
        e = g.node(unreal.MaterialExpressionFunctionInput, 'In_' + pin, input_name=unreal.Name(pin),
                   input_type=FIN[kind], sort_priority=index)
        assert str(e.get_editor_property('input_name')) == pin, (name, pin)
        inputs[pin] = (e, '')
    results = spec['body'](g, inputs)
    assert set(results) == {n for n, _ in spec['outputs']}, name
    outputs = {}
    for index, (pin, _) in enumerate(spec['outputs']):
        out = g.node(unreal.MaterialExpressionFunctionOutput, 'Out_' + pin,
                     adopt=factory_nodes[0] if index == 0 and factory_nodes else None,
                     output_name=unreal.Name(pin), sort_priority=index)
        assert str(out.get_editor_property('output_name')) == pin, (name, pin)
        names = list(LIB.get_material_expression_input_names(out))
        assert len(names) == 1, (name, names)
        g.link(results[pin], out, names[0])
        outputs[pin] = out
    return inputs, outputs


def create_function(h, name, spec, receipt):
    package = FUNCTION_DIR + '/' + name
    assert not unreal.EditorAssetLibrary.does_asset_exist(package) and not package_file(package).exists(), package
    function = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FUNCTION_DIR, unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    assert isinstance(function, unreal.MaterialFunction) and h.path(function) == obj_path(package), package
    receipt['created_functions'][package] = {'disk_immediately_after_create': disk_state(package_file(package))}
    unreal.EditorAssetLibrary.set_metadata_tag(function, 'GeoCityOwner', OWNER_TAG)
    # INFERRED: the factory may pre-create one FunctionOutput; adopt it instead of deleting.
    factory_nodes = list(LIB.get_material_function_expressions(function))
    assert len(factory_nodes) <= 1 and all(isinstance(e, unreal.MaterialExpressionFunctionOutput)
                                           for e in factory_nodes), (name, [e.get_class().get_name() for e in factory_nodes])
    receipt['created_functions'][package]['factory_nodes'] = [e.get_class().get_name() for e in factory_nodes]
    g = Builder(function, True, -1600, 0, 8)
    build_function_graph(g, name, spec, factory_nodes)
    LIB.update_material_function(function)
    rows = describe_function(h, function)
    assert len(rows) == len(g.added), (name, len(rows), len(g.added))
    check_function(h, name, spec, rows)
    receipt['created_functions'][package].update(node_count=len(rows), rows_sha256=digest(rows))
    return function, rows


# ----------------------------------------------------------------- graph checks
def upstream_classes(h, material, starts, function_rows):
    """Classes upstream of start endpoints; descends into the new MF packages."""
    seen, stack, classes = set(), [h.path(s) for s in starts], set()
    nodes = {h.path(e): e for e in LIB.get_material_expressions(material)}
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in nodes:
            continue
        seen.add(cur)
        e = nodes[cur]
        classes.add(e.get_class().get_name())
        if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall):
            fn = h.path(e.get_editor_property('material_function'))
            if fn in function_rows:
                classes |= {r['class'] for r in function_rows[fn].values()}
        stack.extend(h.path(s) for _, s in h.inputs(material, e) if s)
    return classes


def verify_graph(h, material, before, after_nodes, added_paths, switches, finals, height_llbs,
                 function_rows, planned, roots_before, material_settings):
    """D1-D10: old rows identical, additions exact, roots, params, samplers, no PixelNormalWS."""
    old = before['nodes']
    assert set(old) <= set(after_nodes), 'Old node vanished'
    changed = [p for p, row in old.items() if after_nodes[p] != row]
    assert not changed, ('Old node rows changed', changed[:10])
    added = set(after_nodes) - set(old)
    assert added == set(added_paths), ('Unexpected additions', sorted(added ^ set(added_paths))[:10])
    for p in added:
        row = after_nodes[p]
        assert (row['properties'].get('desc') or '').startswith(MARK), p
        assert not (row['properties'].get('desc') or '').startswith(GRASS_OWNER), p
        assert row['class'] != 'MaterialExpressionLandscapeGrassOutput', p
    roots = {k: h.path(LIB.get_material_property_input_node(material, prop)) for k, prop in h.PROPERTIES.items()}
    for key in ROOT_PROPS:
        assert roots[key] == h.path(switches[key]), key
        row = after_nodes[roots[key]]
        assert row['properties']['parameter_name'] == SWITCH and row['properties']['default_value'] is False, key
        assert row['edges']['False']['source'] == roots_before[key], key
        assert row['edges']['True']['source'] == h.path(finals[key]), key
    assert all(roots[k] == roots_before[k] for k in roots if k not in ROOT_PROPS), 'Other roots moved'
    for key, node in height_llbs.items():
        row = after_nodes[h.path(node)]
        assert sorted(row['input_names']) == sorted(['Layer ' + l for l in LAYERS] + ['Height ' + l for l in LAYERS]), key
        assert all(e['source'] for e in row['edges'].values()), (key, 'unconnected LLB pin')
        assert [x['layer_name'] for x in row['layers']] == list(LAYERS), key
        assert all(x['blend_type'] == h.plain(unreal.LandscapeLayerBlendType.LB_HEIGHT_BLEND) for x in row['layers']), key
    height_sources = {k: {l: after_nodes[h.path(n)]['edges']['Height ' + l]['source'] for l in LAYERS}
                      for k, n in height_llbs.items()}
    assert len({json.dumps(v, sort_keys=True) for v in height_sources.values()}) == 1, 'Height sources differ'
    old_names = {r['properties'].get('parameter_name') for r in old.values() if r['properties'].get('parameter_name')}
    new_params = {}
    for p in added:
        row = after_nodes[p]
        name = row['properties'].get('parameter_name')
        if name and row['class'] != 'MaterialExpressionLandscapeLayerSample':
            new_params.setdefault(name, []).append(row)
    assert set(new_params) == set(PARAMS), ('Parameter set differs', sorted(set(new_params) ^ set(PARAMS)))
    assert not (set(new_params) & old_names), 'New parameter collides with an existing name'
    assert not [n for n in new_params if n.startswith('MW_')]
    allowed_textures = set(master_textures(before))
    for name, (kind, default, sampler) in PARAMS.items():
        rows = new_params[name]
        assert len(rows) == (3 if kind == 'switch' else 1), name
        for row in rows:
            value = row['properties'].get('default_value')
            if kind == 'scalar':
                assert value == f32(default), (name, value)
            elif kind == 'vector':
                assert value == [f32(x) for x in default], (name, value)
            elif kind == 'switch':
                assert value is False, name
            else:
                assert row['properties']['texture'] == default and default in allowed_textures, name
                assert row['properties']['sampler_type'] == h.plain(SAMPLER[sampler]), name
    samples = [after_nodes[p] for p in added if after_nodes[p]['class'] == 'MaterialExpressionTextureSample']
    assert len(samples) == len(planned['master_samples']), len(samples)
    assert sorted(r['properties']['sampler_type'] for r in samples) == sorted(h.plain(SAMPLER[k]) for k in planned['master_samples'])
    assert all(r['properties']['sampler_source'] == h.plain(WRAP) for r in samples), 'Non-wrap sampler source'
    calls = [after_nodes[p] for p in added if after_nodes[p]['class'] == 'MaterialExpressionMaterialFunctionCall']
    assert sorted(r['properties']['material_function'] for r in calls) == sorted(planned['calls']), 'Call census'
    assert not [r for r in calls if r['properties']['material_function'] not in function_rows]
    banned = upstream_classes(h, material, [finals['normal']] + [s for s in planned['height_sources']], function_rows)
    assert 'MaterialExpressionPixelNormalWS' not in banned, 'D8 PixelNormalWS upstream of Normal/Height'
    assert {k: h.plain(material.get_editor_property(k)) for k in SETTINGS} == material_settings, 'D9 settings'
    return {'roots_after': roots, 'added_count': len(added), 'new_parameters': sorted(new_params),
            'master_samples': len(samples), 'calls': len(calls), 'height_sources': height_sources,
            'upstream_classes_normal_height': sorted(banned)}


def expected_instances(before, plans, defaults):
    result = {}
    for path, state in before.items():
        area = next((a for a, p in CHILDREN.items() if obj_path(p) == state['path'] or p == path), None)
        plan = plans.get(area, {'textures': {}, 'vectors': {}, 'scalars': {}})
        updates = {'textures': {k: v['path'] for k, v in plan['textures'].items()},
                   'vectors': plan['vectors'], 'scalars': plan['scalars']}
        row = json.loads(json.dumps(state))
        for kind in ('scalars', 'vectors', 'textures'):
            for name, value in defaults[kind].items():
                assert name not in row[kind], name
                row[kind][name] = value
            row[kind].update(updates[kind])
        result[path] = {'state': row, 'updates': updates}
    return result


def check_instances(h, live, expected):
    association = h.plain(unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    for path, exp in expected.items():
        state, prior, updates = live[path], exp['state'], exp['updates']
        for key in ('path', 'parent', 'override_guid_capture', 'scalars', 'vectors', 'textures'):
            assert state[key] == prior[key], (path, key)
        for kind, overrides in (('scalars', 'scalar_overrides'), ('vectors', 'vector_overrides'),
                                ('textures', 'texture_overrides')):
            names = set(updates[kind])
            assert [r for r in state[overrides] if r['name'] not in names] == \
                   [r for r in prior[overrides] if r['name'] not in names], (path, overrides)
            selected = [r for r in state[overrides] if r['name'] in names]
            assert {r['name'] for r in selected} == names and len(selected) == len(names), (path, overrides)
            assert all(r['association'] == association and r['index'] == -1 and r['value'] == updates[kind][r['name']]
                       for r in selected), (path, overrides)


def new_defaults():
    result = {'scalars': {}, 'vectors': {}, 'textures': {}}
    for name, (kind, default, sampler) in PARAMS.items():
        if kind == 'scalar':
            result['scalars'][name] = f32(default)
        elif kind == 'vector':
            result['vectors'][name] = [f32(x) for x in default]
        elif kind == 'texture':
            result['textures'][name] = default
    return result


# ----------------------------------------------------------------- master branch
def make_params(g):
    """New master parameters with exact defaults (no switch; switches come from the probe)."""
    P = {}
    for name, (kind, default, sampler) in PARAMS.items():
        if kind == 'scalar':
            P[name] = (g.node(unreal.MaterialExpressionScalarParameter, name, parameter_name=unreal.Name(name),
                              default_value=float(default), group=unreal.Name('GeoCity_S1')), '')
        elif kind == 'vector':
            P[name] = (g.node(unreal.MaterialExpressionVectorParameter, name, parameter_name=unreal.Name(name),
                              default_value=unreal.LinearColor(*default), group=unreal.Name('GeoCity_S1')), 'RGB')
        elif kind == 'texture':
            texture = unreal.load_asset(default)
            assert isinstance(texture, unreal.Texture), default
            P[name] = (g.node(unreal.MaterialExpressionTextureObjectParameter, name, parameter_name=unreal.Name(name),
                              texture=texture, sampler_type=SAMPLER[sampler], sampler_source=WRAP,
                              group=unreal.Name('GeoCity_S1')), '')
    return P


def build_branch(g, anchors, P, functions):
    """Gaza-only True branch (SPEC branch); reads existing anchor outputs only (no old node is edited,
    no existing input pin is linked)."""
    p = lambda short: P['GeoCity_S1_' + short]
    A = dict(anchors)
    LC, GRID, DA = A['layer_coords'], A['grid_cm'], A['distance_alpha']
    call = lambda label, fn, conn: g.call(label, functions[fn], FUNCTIONS[fn], conn)
    field = call('MacroField', 'MF_GeoCityV2_MacroField', {
        'NoiseTex': p('MacroNoise'), 'LandscapeUV': LC, 'GridCm': GRID, 'Tile1Cm': p('MacroTile1Cm'),
        'Tile2Cm': p('MacroTile2Cm'), 'Tile3Cm': p('MacroTile3Cm'), 'NoiseMean': p('NoiseMean'),
        'NoiseInvStd': p('NoiseInvStd'), 'HueGain': p('HueGain'), 'VariantGain': p('VariantGain')})
    VALUE, HUE, VB, VC, FINE = ((field, o) for o in ('Value', 'HueT', 'VariantB', 'VariantC', 'Fine'))
    lattice = {'DistanceAlpha': DA, 'NearWX': A['near_wx'], 'NearWY': A['near_wy'],
               'FarWX': A['far_wx'], 'FarWY': A['far_wy']}
    for k in range(4):
        lattice['NearHash' + str(k)] = A['near_hash' + str(k)]
        lattice['FarHash' + str(k)] = A['far_hash' + str(k)]

    def cell(label, texture, near_uv, far_scale):
        return call(label + 'CellSample', 'MF_GeoCityV2_CellSample',
                    dict(lattice, Tex=texture, NearUV=near_uv, FarScale=far_scale))

    def pattern_uv(label, tile):
        scale = g.div(label + 'CmToUV', GRID, g.max_c(label + 'TilePositive', tile, 1.0))
        return g.mul(label + 'PatternUV', g.mul(label + 'UV', LC, scale), A['pattern_scale'])

    ground_b = cell('GroundB', p('GroundB_Albedo'), pattern_uv('GroundB', p('GroundB_TileCm')), p('GroundB_FarScale'))
    ground_c = cell('GroundC', p('GroundC_Albedo'), pattern_uv('GroundC', p('GroundC_TileCm')), p('GroundC_FarScale'))
    steep_cell = cell('Steep', A['steep_albedo'], pattern_uv('Steep', A['steep_tile']), A['steep_far_scale'])
    road_cell = cell('Road', A['road_albedo'], A['road_uv'], A['road_far_scale'])
    pad_cell = cell('Pad', A['pad_albedo'], A['pad_uv'], A['pad_far_scale'])
    # Ground: the full existing Gaza ground (LinearInterpolate_42 / Normalize_9) + two uncorrelated albedo variants.
    with_b = g.lerp('GroundWithB', A['ground_full'], g.mul('GroundBTintedColor', (ground_b, 'Color'), p('GroundB_Tint')),
                    g.mul('GroundBMask', VB, p('GroundB_Amount')))
    ground_color = g.lerp('GroundWithC', with_b, g.mul('GroundCTintedColor', (ground_c, 'Color'), p('GroundC_Tint')),
                          g.mul('GroundCMask', VC, p('GroundC_Amount')))
    ground_normal = A['ground_full_normal']
    ground_rough = A['rough_Sand_01']
    weight = {l: g.node(unreal.MaterialExpressionLandscapeLayerSample, 'Weight' + l, parameter_name=unreal.Name(l))
              for l in LAYERS}
    normal_z = g.mask('VertexNormalZ', g.node(unreal.MaterialExpressionVertexNormalWS, 'VertexNormal'), 'b')
    noise01 = g.sat('FineNoise01', g.add_c('FineNoiseCentered', g.mul_c('FineNoiseScaled', FINE, 0.25), 0.5))
    steep = (call('SteepSlopeBlend', 'MF_GeoCityV2_SlopeBlend', {
        'SteepWeight': weight['Sand_02'], 'NormalZ': normal_z, 'Noise': noise01, 'Lo': p('SteepLo'),
        'Hi': p('SteepHi'), 'Jitter': p('SteepJitter'), 'SlopeMix': p('SteepSlopeMix')}), 'Alpha')
    steep_color = g.lerp('SteepColor', ground_color,
                         g.mul('SteepTintedColor', (steep_cell, 'Color'), A['steep_tint']), steep)
    steep_normal = g.normalize('SteepUnitNormal', g.lerp('SteepNormal', ground_normal, A['steep_normal'], steep))
    steep_rough = g.lerp('SteepRoughness', ground_rough, A['rough_Sand_02'], steep)
    road_color = g.mul('RoadTintedColor', (road_cell, 'Color'), A['road_tint'])
    pad_color = g.mul('PadTintedColor', (pad_cell, 'Color'), A['pad_tint'])
    heights = {}
    for layer, near, far in (('Sand_01', A['ground_near'], A['ground_far']),
                             ('Sand_02', (steep_cell, 'Near'), (steep_cell, 'Far')),
                             ('Dirt_Path', (road_cell, 'Near'), (road_cell, 'Far')),
                             ('Sand_Path', (pad_cell, 'Near'), (pad_cell, 'Far'))):
        heights[layer] = (call('Height' + layer, 'MF_GeoCityV2_HeightBlend', {
            'Near': near, 'Far': far, 'Weight': weight[layer], 'Bias': p('HeightBias'),
            'Contrast': p('HeightContrast'), 'Amount': p('HeightAmount')}), 'Height')

    def height_llb(label, sources):
        entries = []
        for layer in LAYERS:  # fresh entries, precedent native_graph_revision.py:475-481
            entry = unreal.LayerBlendInput()
            entry.set_editor_property('layer_name', unreal.Name(layer))
            entry.set_editor_property('blend_type', unreal.LandscapeLayerBlendType.LB_HEIGHT_BLEND)
            entry.set_editor_property('preview_weight', 1.0 if layer == 'Sand_01' else 0.0)
            entries.append(entry)
        node = g.node(unreal.MaterialExpressionLandscapeLayerBlend, label, layers=entries)
        names = list(LIB.get_material_expression_input_names(node))
        expected = sorted(['Layer ' + l for l in LAYERS] + ['Height ' + l for l in LAYERS])
        assert sorted(names) == expected, ('Height-blend pin names', names)
        for layer in LAYERS:
            Builder.link(sources[layer], node, 'Layer ' + layer)
            Builder.link(heights[layer], node, 'Height ' + layer)
        return node

    llb_new = {'color': height_llb('HeightBlendColor', {'Sand_01': ground_color, 'Sand_02': steep_color,
                                                        'Dirt_Path': road_color, 'Sand_Path': pad_color}),
               'normal': height_llb('HeightBlendNormal', {'Sand_01': ground_normal, 'Sand_02': steep_normal,
                                                          'Dirt_Path': A['road_normal'], 'Sand_Path': A['pad_normal']}),
               'roughness': height_llb('HeightBlendRoughness', {'Sand_01': ground_rough, 'Sand_02': steep_rough,
                                                                'Dirt_Path': A['rough_Dirt_Path'],
                                                                'Sand_Path': A['rough_Sand_Path']})}
    macro = (call('MacroColor', 'MF_GeoCityV2_MacroColor', {
        'Base': llb_new['color'], 'Value': VALUE, 'HueT': HUE, 'HueA': p('HueA'), 'HueB': p('HueB'),
        'HueAmount': p('HueAmount'), 'ValueAmount': p('ValueAmount'), 'DistanceAlpha': DA,
        'FarSaturation': p('FarSaturation'), 'FarValue': p('FarValue'), 'FarAmount': p('FarAmount')}), 'Color')

    def contact(label, w, amount):
        peak = g.mul_c(label + 'BandPeak', g.mul(label + 'BandProduct', w, g.one_minus(label + 'BandInverse', w)), 4.0)
        return g.mul(label + 'BandAmount', peak, amount)

    # Contact band: unchanged v1 logic, gated at 0 (correction 9); jitter now from the Fine octave, target = road cell.
    band = g.sat('ContactBand', g.mul('ContactBandJittered', g.max(
        'ContactBandMax', contact('Road', weight['Dirt_Path'], p('ContactRoad')),
        contact('Pad', weight['Sand_Path'], p('ContactPad'))), g.add_c('ContactJitter', noise01, 0.5)))
    banded = g.mul('ContactDarkened', g.lerp('ContactSoilShift', macro, road_color, p('ContactSoil')),
                   g.one_minus('ContactKeep', p('ContactDarken')))
    final_color = g.sat('FinalColor', g.lerp('ContactColor', macro, banded, band))
    flat = g.c3('FlatNormal', 0.0, 0.0, 1.0)
    final_normal = g.normalize('FinalUnitNormal', g.lerp('NormalDistanceFade', llb_new['normal'], flat,
                                                         g.mul('NormalFadeAlpha', DA, p('NormalFade'))))
    rough_var = g.mul('RoughnessVariation', g.mul_c('RoughNoiseHalf', g.clamp('RoughNoiseClamped', FINE, -2.0, 2.0), 0.5),
                      p('RoughVar'))
    final_rough = g.clamp('FinalRoughness', g.add('ContactRoughness', g.add('VariedRoughness', llb_new['roughness'], rough_var),
                                                   g.mul('ContactRoughAmount', band, p('ContactRough'))), 0.0, 1.0)
    finals = {'color': final_color, 'normal': final_normal, 'roughness': final_rough}
    cells = {'GroundB': ground_b, 'GroundC': ground_c, 'Steep': steep_cell, 'Road': road_cell, 'Pad': pad_cell}
    return {'finals': finals, 'heights': heights, 'llbs': llb_new, 'weights': weight, 'cells': cells, 'field': field}


# ----------------------------------------------------------------- modes
def common_preflight(h, args, mode):
    ctx = guard(h, args, mode)
    assert list(args['areas']) == [ctx['area']], ('Scope is exactly the open map area (review r2)',
                                                  args['areas'], ctx['area'])
    script_sha, ctx['executed_script'] = script_identity(args, ctx['activation'])
    return ctx, script_sha


def run_identity(ctx):
    return {'activation': ctx['activation_file'], 'lease_kind': ctx['lease_kind'],
            'executed_script': ctx['executed_script']}


def baseline_gate(snap, args):
    expected = dict(BASELINE, **args.get('baseline_override', {}))
    assert snap['facts'] == expected, ('Baseline mismatch: stop and re-baseline', snap['facts'], expected)
    assert snap['dirty'] == {'maps': [], 'content': []}, ('Dirty packages before S1', snap['dirty'])
    return expected


def inspect(h, args, label):
    ctx, script_sha = common_preflight(h, args, 'inspect')
    mip_mode = cell_mip_mode(args)
    snap = snapshot(h, ctx)
    expected = baseline_gate(snap, args)
    material = unreal.load_asset(MASTER)
    anchors, roots, texture_params = resolve_anchors(h, material, snap)
    probe = derivative_probe(h, snap)
    if mip_mode == 'derivative':
        assert probe['pins_connected'] >= 1, ('No connected DDX(UVs)/DDY(UVs) pins on existing derivative samples', probe)
    plans = plan_children(args, texture_params)
    allowed = master_allowed_textures(snap)
    textures = check_textures(h, plans, allowed)
    backup = check_backup(args) if args.get('backup_manifest') else (None, None)
    absent = functions_absent()
    consumer_rows = check_consumers(ctx['activation'])
    base_stats = statistics(unreal.load_asset(BASE))  # read-only probe of the save-time statistics gate inputs
    assert 'error' not in base_stats and base_stats['num_pixel_shader_instructions'] > 0, \
        ('get_statistics unusable here: the save/child_save statistics gate could never pass; root decides', base_stats)
    assert dirty(h) == snap['dirty']  # all asserts before the first receipt write (retry stays possible)
    pid = os.getpid()
    graph = write_new(RECEIPTS / ('GRAPH_BEFORE_' + str(pid) + '.json'), {
        'schema': GRAPH_SCHEMA, 'pid': pid, 'world': ctx['world'], 'utc': now(),
        'master': obj_path(MASTER), 'graph_count': len(snap['nodes']), 'graph_sha256': snap['facts']['graph_sha256'],
        'nodes': snap['nodes'], 'roots': snap['roots'], 'material_settings': snap['material_settings'],
        'static_switches': snap['switches'], 'facts': snap['facts'], 'helper_sha256': HELPER_SHA})
    receipt = {'schema': INSPECT_SCHEMA, 'status': 'INSPECTED_READ_ONLY',
               'mode': 'inspect', 'label': label, 'pid': pid, 'world': ctx['world'], 'area': ctx['area'],
               'utc': now(), 'script_sha256': script_sha, 'helper_sha256': HELPER_SHA, 'lease_line': ctx['lease_line'],
               'sources': ctx['sources'], 'hda_count': ctx['hda_count'], 'landscapes': ctx['landscapes'],
               'graph_before': graph, 'facts': snap['facts'], 'baseline_expected': expected,
               'roots': snap['roots'], 'material_settings': snap['material_settings'],
               'instances': snap['instances'], 'switches': snap['switches'], 'grass': snap['grass'],
               'scene_sha256': snap['scene_sha256'], 'dirty': snap['dirty'],
               'anchors': {k: [h.path(e), o] for k, (e, o) in anchors.items()},
               'cell_sample_mip_mode': mip_mode, 'derivative_probe': probe,
               'epic_noise_fallback': bool(args.get('epic_noise_fallback')),
               'function_packages_absent': absent,
               'existing_texture_param_kinds': texture_params, 'plans': plans, 'plans_sha256': digest(plans),
               'planned_textures': textures, 'mw_file_sha256': mw_files(plans),
               'backup_manifest': {'file': str(backup[0]), 'sha256': sha(backup[0])} if backup[0] else None,
               'log': {'file': str(log_file()), 'offset': log_file().stat().st_size},
               'base_statistics': base_stats, 'consumers': consumer_rows,
               **run_identity(ctx), 'native_mutation': False, 'explicit_save_called': False,
               'labels': {'MEASURED': 'all readbacks in this receipt',
                          'INFERRED': 'LLB height math, switch propagation to Landscape MICs (gate G1), derivative '
                                      'pins inside a MaterialFunction (asserted per fetch at apply)'}}
    out = write_new(RECEIPTS / (PREFIX + 'INSPECT_' + label + '_PID' + str(pid) + '.json'), receipt)
    return {'ok': True, 'status': receipt['status'], 'receipt': out, 'graph_before': graph,
            'facts': snap['facts'], 'cell_sample_mip_mode': mip_mode, 'derivative_probe': probe, 'native_mutation': False}


def apply(h, args, label):
    ctx, script_sha = common_preflight(h, args, 'apply')
    preconditions = operator_preconditions(args)
    pid = os.getpid()
    mip_mode = cell_mip_mode(args)
    _, inspected = load_doc(args['inspect_receipt'], args['inspect_receipt_sha256'])
    assert inspected.get('schema') == INSPECT_SCHEMA, 'Not an S1v2 inspect receipt'
    assert inspected['status'] == 'INSPECTED_READ_ONLY' and inspected['pid'] == pid and inspected['world'] == ctx['world']
    assert inspected['script_sha256'] == script_sha
    assert inspected['cell_sample_mip_mode'] == mip_mode, ('cell_sample_mip_mode differs from the inspect receipt', mip_mode)
    assert inspected['epic_noise_fallback'] == bool(args.get('epic_noise_fallback')), 'epic_noise_fallback differs from inspect'
    backup_file, backup_shas = check_backup(args)
    snap = snapshot(h, ctx)
    baseline_gate(snap, args)
    for key in ('roots', 'material_settings', 'instances', 'switches', 'grass', 'scene_sha256', 'dirty'):
        assert snap[key] == inspected[key], ('State changed since inspect', key)
    assert snap['facts'] == inspected['facts']
    graph_before = json.loads(Path(inspected['graph_before']['file']).read_text(encoding='utf-8'))
    assert sha(inspected['graph_before']['file']) == inspected['graph_before']['sha256']
    assert graph_before['nodes'] == snap['nodes'] and graph_before['roots'] == snap['roots']
    material, base, grass, children, instances = load_assets(h)
    anchors, roots, texture_params = resolve_anchors(h, material, snap)
    assert {k: [h.path(e), o] for k, (e, o) in anchors.items()} == inspected['anchors']
    plans = plan_children(args, texture_params)
    assert digest(plans) == inspected['plans_sha256'], 'Planned child values differ from the inspected plan'
    assert sorted(plans) == [ctx['area']], 'Apply writes only the open map area child (review r2)'
    allowed = master_allowed_textures(snap)
    textures = check_textures(h, plans, allowed)
    mw_before = mw_files(plans)
    assert mw_before == inspected['mw_file_sha256']
    assert check_consumers(ctx['activation']) == inspected['consumers'], 'Consumers changed since inspect'
    once = RECEIPTS / APPLY_ONCE
    out = RECEIPTS / (PREFIX + 'APPLY_' + label + '_PID' + str(pid) + '.json')
    assert not once.exists() and not out.exists(), 'Attempt already recorded; root reviews before another'
    CELL_MIP['mode'] = mip_mode
    receipt = {'schema': APPLY_SCHEMA, 'status': 'attempt_started',
               'mode': 'apply', 'label': label, 'pid': pid, 'world': ctx['world'], 'area': ctx['area'],
               'utc': now(), 'script_sha256': script_sha, 'helper_sha256': HELPER_SHA,
               'inspect_receipt': {'file': str(Path(args['inspect_receipt']).resolve()), 'sha256': args['inspect_receipt_sha256']},
               'backup_manifest': {'file': str(backup_file), 'sha256': sha(backup_file)},
               'backup_new_asset_paths_note': ('The reused v1 manifest lists the v1 MF_GeoCity_* names (absent); the v2 '
                                               'rollback list is created_functions below (MF_GeoCityV2_*).'),
               'cell_sample_mip_mode': mip_mode, 'derivative_probe': inspected['derivative_probe'],
               'epic_noise_fallback': bool(args.get('epic_noise_fallback')),
               'log': {'file': str(log_file()), 'offset': log_file().stat().st_size},
               'graph_before_sha256': snap['facts']['graph_sha256'], 'plans': plans, 'planned_textures': textures,
               'existing_texture_param_kinds': texture_params, 'allowed_textures': sorted(allowed),
               'operator_preconditions': preconditions, **run_identity(ctx), 'consumers': inspected['consumers'],
               'created_functions': {}, 'added_nodes': [], 'probe': {}, 'compile_errors': {},
               'setter_returns': {}, 'explicit_save_called': False, 'rollback_executed': False}
    with once.open('x', encoding='utf-8') as stream:
        json.dump({'pid': pid, 'world': ctx['world'], 'status': 'attempt_started', 'receipt': str(out)}, stream, indent=1)
    switches, functions, function_rows = {}, {}, {}
    try:
        # Free canvas from live extents (old max y in the x band, M: 34070 in r031).
        band = [r['properties'].get('material_expression_editor_y', 0) for r in snap['nodes'].values()
                if -4400 <= r['properties'].get('material_expression_editor_x', 0) <= -1600]
        y0 = max(36000, int(math.ceil((max(band) + 460) / 10.0)) * 10)
        g = Builder(material, False, -4000, y0, 10)
        # ---- correction 1: static-switch probe; True == False == old root (identical output).
        llb = {k: roots[k] for k in ROOT_PROPS}
        for key, prop in ROOT_PROPS.items():
            switches[key] = g.node(unreal.MaterialExpressionStaticSwitchParameter, 'Enable' + key.title(),
                                   parameter_name=unreal.Name(SWITCH), default_value=False, group=unreal.Name('GeoCity_S1'))
            names = list(LIB.get_material_expression_input_names(switches[key]))
            assert sorted(names) == ['False', 'True'], ('Static switch pin names', names)
            Builder.link(llb[key], switches[key], 'True')
            Builder.link(llb[key], switches[key], 'False')
            assert LIB.connect_material_property(switches[key], '', prop), key
        errors = LIB.recompile_material(material)  # probe: True == False == old root; proves the probe wiring only
        receipt['compile_errors']['probe'] = [str(e) for e in (errors or [])]
        assert not receipt['compile_errors']['probe'], 'Compile errors after probe switches'
        probe_children = {a: children[a] for a in args['areas']}
        pre_probe = {CHILDREN[a]: h.material_state(material, c) for a, c in probe_children.items()}
        for area, child in probe_children.items():
            receipt['setter_returns']['probe_' + area] = bool(
                LIB.set_material_instance_static_switch_parameter_value(child, SWITCH, True))
            LIB.update_material_instance(child)
            assert LIB.get_material_instance_static_switch_parameter_value(child, SWITCH) is True, area
        receipt['probe']['dirty_after_switch'] = dirty(h)
        assert not receipt['probe']['dirty_after_switch']['maps'], 'STOP_MAP_DIRTY_AFTER_STATIC_SWITCH_PROBE'
        for area, child in probe_children.items():  # G2: exact LW:366-367 calls
            LIB.set_material_instance_parent(child, base)
            LIB.update_material_instance(child)
            assert child.get_editor_property('parent') == base, area
            assert LIB.get_material_instance_static_switch_parameter_value(child, SWITCH) is True, ('G2', area)
            assert h.material_state(material, child) == pre_probe[CHILDREN[area]], ('G2 state', area)
        receipt['probe'].update(status='PASSED', input_names=['True', 'False'],
                                dirty_after_replay=dirty(h), switch_nodes={k: h.path(v) for k, v in switches.items()})
        assert not receipt['probe']['dirty_after_replay']['maps'], 'STOP_MAP_DIRTY_AFTER_G2_REPLAY'
        # ---- five parameter-free material functions (saved before master in save mode).
        for name, spec in FUNCTIONS.items():
            functions[name], rows = create_function(h, name, spec, receipt)
            function_rows[h.path(functions[name])] = rows
        P = make_params(g)
        branch = build_branch(g, anchors, P, functions)
        finals, heights, llb_new = branch['finals'], branch['heights'], branch['llbs']
        for key in ROOT_PROPS:  # move the True pins from the probe source to the branch
            Builder.link(finals[key], switches[key], 'True')
        receipt['added_nodes'] = [h.path(e) for e in g.added]
        # ---- D1-D10 in memory, before compile
        after_nodes = {h.path(e): h.describe(material, e) for e in LIB.get_material_expressions(material)}
        planned = {'master_samples': [],  # every new fetch lives inside the MF packages
                   'calls': [h.path(functions['MF_GeoCityV2_CellSample'])] * 5
                   + [h.path(functions['MF_GeoCityV2_MacroField']), h.path(functions['MF_GeoCityV2_MacroColor']),
                      h.path(functions['MF_GeoCityV2_SlopeBlend'])]
                   + [h.path(functions['MF_GeoCityV2_HeightBlend'])] * 4,
                   'height_sources': [v[0] for v in heights.values()]}
        diff = verify_graph(h, material, snap, after_nodes, receipt['added_nodes'], switches, finals, llb_new,
                            function_rows, planned, snap['roots'], snap['material_settings'])
        assert all(-4000 <= after_nodes[p]['properties']['material_expression_editor_x'] <= -1840 and
                   after_nodes[p]['properties']['material_expression_editor_y'] >= y0 for p in receipt['added_nodes'])
        grass_now = grass_contract(h, material, list(LIB.get_material_expressions(material)), grass)
        assert grass_now == snap['grass'], 'D4 Grass graph/settings changed'
        # Compile gate (review r2). DOCUMENTED (MaterialEditingLibrary.h:262-267): RecompileMaterial returns the
        # compiler errors of this UMaterial. INFERRED: that is the permutation selected by the master's own
        # static-switch defaults, so with GeoCity_S1_Enable=False the branch and the 5 MFs are not translated.
        # In memory only (nothing saved): force all 3 switch defaults True -> recompile must return [] (Gaza
        # branch, MFs, height LLBs translated); restore all 3 to False -> recompile must return [] (Iran/base).
        for key in ROOT_PROPS:
            switches[key].set_editor_property('default_value', True)
        try:
            errors = LIB.recompile_material(material)
            receipt['compile_errors']['branch_forced_true'] = [str(e) for e in (errors or [])]
            receipt['master_statistics_forced_true'] = statistics(material)
        finally:
            for key in ROOT_PROPS:
                switches[key].set_editor_property('default_value', False)
        errors = LIB.recompile_material(material)
        receipt['compile_errors']['branch_default_false'] = [str(e) for e in (errors or [])]
        receipt['master_statistics_default_false'] = statistics(material)
        assert all(s.get_editor_property('default_value') is False for s in switches.values()), 'Switch default not restored'
        assert bool(LIB.get_material_default_static_switch_parameter_value(material, SWITCH)) is False
        assert not receipt['compile_errors']['branch_forced_true'], 'Compile errors in the True (Gaza) permutation'
        assert not receipt['compile_errors']['branch_default_false'], 'Compile errors in the default False permutation'
        compiled_nodes = {h.path(e): h.describe(material, e) for e in LIB.get_material_expressions(material)}
        assert compiled_nodes == after_nodes, 'Compile/switch round trip changed node rows'
        for name, fn in functions.items():
            assert describe_function(h, fn) == function_rows[h.path(fn)], ('Function changed by compile', name)
        # ---- child overrides (base MI never written)
        defaults = new_defaults()
        for area, plan in plans.items():
            child = children[area]
            for name, row in plan['textures'].items():
                texture = unreal.load_asset(row['path'])
                receipt['setter_returns'][area + ':' + name] = bool(
                    LIB.set_material_instance_texture_parameter_value(child, name, texture))
            for name, value in plan['vectors'].items():
                receipt['setter_returns'][area + ':' + name] = bool(
                    LIB.set_material_instance_vector_parameter_value(child, name, unreal.LinearColor(*value)))
            for name, value in plan['scalars'].items():
                receipt['setter_returns'][area + ':' + name] = bool(
                    LIB.set_material_instance_scalar_parameter_value(child, name, value))
            LIB.update_material_instance(child)
        receipt['dirty_after_children'] = dirty(h)
        assert not receipt['dirty_after_children']['maps'], 'STOP_MAP_DIRTY_AFTER_CHILD_OVERRIDES'
        expected = expected_instances(snap['instances'], plans, defaults)
        live = {p_: h.material_state(material, instances[p_]) for p_ in instances}
        check_instances(h, live, expected)  # readback is truth; setter returns are recorded only (LW:375-377)
        for area in plans:  # G2 again with the full override set: exact LW:366-367 calls
            child = children[area]
            LIB.set_material_instance_parent(child, base)
            LIB.update_material_instance(child)
            assert child.get_editor_property('parent') == base
        replayed = {p_: h.material_state(material, instances[p_]) for p_ in instances}
        assert replayed == live, 'G2 replay changed overrides'
        receipt['child_statistics_after'] = {a: statistics(children[a]) for a in plans}  # recorded; gated at save
        switches_after = switch_state(material, instances)
        assert switches_after['names'] == sorted(set(snap['switches']['names']) | {SWITCH}), 'D10 switch names'
        assert switches_after['defaults'][SWITCH] is False
        for p_, values in switches_after['instances'].items():
            area = next((a for a, c in CHILDREN.items() if c == p_), None)
            assert values[SWITCH] is (area in plans), (p_, values[SWITCH])
            assert {k: v for k, v in values.items() if k != SWITCH} == snap['switches']['instances'][p_], p_
        # ---- final state, dirty set, files
        ctx_after = guard(h, args, 'apply')
        assert digest(h.scene_state(ctx_after['actors'])) == snap['scene_sha256'], 'Scene changed'
        expected_dirty = sorted([FUNCTION_DIR + '/' + n for n in FUNCTIONS] + [MASTER] + [CHILDREN[a] for a in plans])
        final_dirty = dirty(h)
        assert final_dirty == {'maps': [], 'content': expected_dirty}, ('D13 dirty set', final_dirty)
        for source, expected_sha in backup_shas.items():
            assert sha(source) == expected_sha, 'Unexpected disk change: ' + source
        assert mw_files(plans) == mw_before, 'Vendor texture file changed'
        for name in FUNCTIONS:
            receipt['created_functions'][FUNCTION_DIR + '/' + name]['disk_before_save'] = disk_state(
                package_file(FUNCTION_DIR + '/' + name))
        assert grass_contract(h, material, list(LIB.get_material_expressions(material)), grass) == snap['grass']
        final_nodes = {h.path(e): h.describe(material, e) for e in LIB.get_material_expressions(material)}
        assert final_nodes == after_nodes
        graph_after = write_new(RECEIPTS / ('GRAPH_AFTER_' + str(pid) + '.json'), {
            'schema': GRAPH_SCHEMA, 'pid': pid, 'world': ctx['world'], 'utc': now(),
            'master': obj_path(MASTER), 'graph_count': len(final_nodes), 'graph_sha256': digest(final_nodes),
            'nodes': final_nodes, 'roots': diff['roots_after'], 'material_settings': snap['material_settings'],
            'functions': function_rows, 'static_switches': switches_after,
            'diff': {'base_graph_sha256': snap['facts']['graph_sha256'], 'added_nodes': receipt['added_nodes'],
                     'changed_old_rows': [], 'moved_roots': {k: [snap['roots'][k], diff['roots_after'][k]] for k in ROOT_PROPS}}})
        receipt.update(status='APPLIED_VERIFIED_NO_SAVE', graph_after=graph_after,
                       graph_after_sha256=digest(final_nodes), graph_count_after=len(final_nodes),
                       roots_after=diff['roots_after'], diff=diff, function_rows_sha256={k: digest(v) for k, v in function_rows.items()},
                       instances_before=snap['instances'], instances_after=live, switch_state_after=switches_after,
                       grass_after=snap['grass'], expected_dirty=expected_dirty, dirty_after=final_dirty,
                       base_statistics_after=statistics(base), mw_file_sha256=mw_before,
                       existing_package_files_unchanged=True, iran_base_mi_written=False,
                       contact_band_acknowledged=bool(args.get('contact_band_acknowledged')),
                       state_instances=live, state_instances_sha256=digest(live), state_switches=switches_after,
                       effective_plans=plans,
                       grass_coverage_note='Only 0.0 may be set (decision 3); it reverts at the next prepare() (LW:374-382).',
                       labels={'compile_gate': 'INFERRED scope: RecompileMaterial errors cover the permutation selected by '
                                               'the master switch defaults; both defaults (True forced in memory, False) '
                                               'were compiled. Child/Landscape-MIC permutations compile asynchronously.',
                               'g4_base_statistics': 'Recorded, not gated (deviation from D2 G4): base_statistics_after vs '
                                                     'inspect base_statistics equal=' + str(statistics(base) == inspected['base_statistics']),
                               'height_identity': 'INFERRED approximate: HeightAmount 0 gives H=1-w; LB_HEIGHT_BLEND '
                                                  'clamp(lerp(-1,1,w)+H,0.0001,1) then renormalizes, exact only when the 4 '
                                                  'weights sum to 1 (LW WEIGHT_TOLERANCE 4/255). Steep 0/0.001 is near-identity.',
                               'ground_identity': 'Ground base = LinearInterpolate_42 / Normalize_9, the measured B0 sources '
                                                  'of LLB_6/_7 Layer Sand_01 (macro Multiply_8 and soil chain kept; v1 '
                                                  'caveat 15 closed). Switch True at master defaults reproduces B0 on '
                                                  'Ground-only pixels up to the INFERRED height-LLB identity; Steep/RoadBed/'
                                                  'Pad albedos are resampled through MF_GeoCityV2_CellSample on purpose.',
                               'cell_sample_mip_mode': ('TMVM_DERIVATIVE with DDX/DDY of the untranslated UV on every '
                                                        'CellSample fetch' if mip_mode == 'derivative' else
                                                        'GRADIENT-FREE FALLBACK (TMVM_NONE): 1-px mip seams at the 2 m/4 m '
                                                        'cell borders are possible; root chose this in args')},
                       next_step='Operator I0 capture (B0 cameras, LIT+UNLIT) then mode=tune (t001 SPEC values) + A3 capture, '
                                 'review, then mode=save in this PID; on doubt exit editor with Do not Save.')
    except Exception as error:
        receipt.update(status='FAILED_NO_SAVE_REQUIRES_ROOT_REVIEW', error=repr(error),
                       instruction='No cleanup was attempted. Close the editor with "Don\'t Save"; restore from the backup manifest only if a disk hash changed.')
        try:
            receipt['dirty_at_failure'] = dirty(h)
            receipt['added_nodes_at_failure'] = sorted(set(h.path(e) for e in LIB.get_material_expressions(material)) - set(snap['nodes']))
            receipt['roots_at_failure'] = {k: h.path(LIB.get_material_property_input_node(material, prop)) for k, prop in h.PROPERTIES.items()}
            receipt['function_disk_at_failure'] = {n: disk_state(package_file(FUNCTION_DIR + '/' + n)) for n in FUNCTIONS}
            receipt['backup_files_unchanged'] = all(sha(s) == v for s, v in backup_shas.items())
        except Exception as snapshot_error:
            receipt['failure_snapshot_error'] = repr(snapshot_error)
        out.write_text(json.dumps(receipt, indent=1), encoding='utf-8')
        once.write_text(json.dumps({'pid': pid, 'world': ctx['world'], 'status': receipt['status'], 'receipt': str(out)}, indent=1), encoding='utf-8')
        raise
    out.write_text(json.dumps(receipt, indent=1), encoding='utf-8')
    once.write_text(json.dumps({'pid': pid, 'world': ctx['world'], 'status': receipt['status'], 'receipt': str(out)}, indent=1), encoding='utf-8')
    return {'ok': True, 'status': receipt['status'], 'receipt': {'file': str(out), 'sha256': sha(out)},
            'graph_after': graph_after, 'added_nodes': len(receipt['added_nodes']), 'expected_dirty': expected_dirty,
            'compile_errors': receipt['compile_errors'], 'cell_sample_mip_mode': mip_mode, 'explicit_save_called': False}


def dump_live(h, tag, label):
    """Evidence for root when the live graph no longer equals the apply receipt (offline diff
    with graph_dump_tools.py diff GRAPH_AFTER_<pid>.json <this file>)."""
    material = unreal.load_asset(MASTER)
    nodes = {h.path(e): h.describe(material, e) for e in LIB.get_material_expressions(material)}
    return write_new(RECEIPTS / (tag + '_' + label + '_PID' + str(os.getpid()) + '.json'),
                     {'utc': now(), 'graph_sha256': digest(nodes), 'nodes': nodes, 'roots': {
                         k: h.path(LIB.get_material_property_input_node(material, prop)) for k, prop in h.PROPERTIES.items()}})


def checked_live_state(h, applied, tag, label, state=None):
    try:
        return live_state_matches_apply(h, applied, state)
    except AssertionError:
        dump_live(h, tag, label)
        raise


def live_state_matches_apply(h, applied, state=None):
    """Master graph, MF rows, roots and Grass == the apply receipt; instances and static switches ==
    the state receipt (apply, tune, save or child_save; default: the apply receipt)."""
    state = state or applied
    material, base, grass, children, instances = load_assets(h)
    nodes = {h.path(e): h.describe(material, e) for e in LIB.get_material_expressions(material)}
    assert digest(nodes) == applied['graph_after_sha256'], 'Master graph differs from the apply receipt'
    roots = {k: h.path(LIB.get_material_property_input_node(material, prop)) for k, prop in h.PROPERTIES.items()}
    assert roots == applied['roots_after']
    for name in FUNCTIONS:
        fn = unreal.load_asset(FUNCTION_DIR + '/' + name)
        assert isinstance(fn, unreal.MaterialFunction), name
        assert digest(describe_function(h, fn)) == applied['function_rows_sha256'][h.path(fn)], name
    assert {p: h.material_state(material, mi) for p, mi in instances.items()} == state['state_instances'], \
        'Instance state differs from the state receipt'
    assert switch_state(material, instances) == state['state_switches'], 'Static switches differ from the state receipt'
    assert grass_contract(h, material, list(LIB.get_material_expressions(material)), grass) == applied['grass_after']
    return material, instances


STATE_STATUS = {APPLY_SCHEMA: 'APPLIED_VERIFIED_NO_SAVE', TUNE_SCHEMA: 'TUNED_VERIFIED_NO_SAVE',
                SAVE_SCHEMA: 'SAVED_NAMED_ONLY', CHILD_SAVE_SCHEMA: 'CHILD_SAVED_NAMED_ONLY'}
EMPTY_PLAN = {'textures': {}, 'vectors': {}, 'scalars': {}}


def load_state(args, apply_file):
    """The receipt whose state_instances/state_switches/effective_plans/s1_disk describe the current
    S1 state (args['state_receipt'], default the apply receipt). Safety comes from live == this receipt
    (checked by the caller) and review == this receipt's SHA, not from it being the latest file."""
    if args.get('state_receipt'):
        file, doc = load_doc(args['state_receipt'], args['state_receipt_sha256'])
    else:
        file = Path(apply_file)
        doc = json.loads(file.read_text(encoding='utf-8-sig'))
    assert STATE_STATUS.get(doc.get('schema')) == doc.get('status'), ('Not a completed S1 state receipt',
                                                                      doc.get('schema'), doc.get('status'))
    if doc['schema'] == APPLY_SCHEMA:
        assert sha(file) == sha(apply_file), 'A different apply receipt'
    else:
        assert doc['apply_receipt']['sha256'] == sha(apply_file), 'State receipt belongs to another apply'
    assert doc['state_instances_sha256'] == digest(doc['state_instances']), 'State receipt self-digest'
    return file, doc


def check_backup_saved_state(args, applied, copies=()):
    file, manifest = load_doc(args['backup_manifest'], args['backup_manifest_sha256'])
    assert str(file) == applied['backup_manifest']['file'] and sha(file) == applied['backup_manifest']['sha256']
    bindings = {str(Path(k).resolve(strict=True)): v for k, v in manifest['file_bindings'].items()}
    for package in copies:  # review r2: re-hash the copies right before anything can overwrite the originals
        row = bindings.get(str(package_file(package).resolve()))
        assert row, ('Backup manifest lacks a copy of', package)
        backup = Path(row['backup']).resolve(strict=True)
        assert backup.is_relative_to(STAGE) and sha(backup) == row['sha256'], ('Backup copy missing/changed', str(backup))
    return file, backup_pins(manifest)


def unsaved_pins_unchanged(pins):
    """Pinned files S1 never saves (base MI, Grass type, maps; any extra pins) are unchanged."""
    s1_files = {str(package_file(p).resolve()) for p in [MASTER, *CHILDREN.values()]}
    changed = sorted(s for s, v in pins.items() if s not in s1_files and sha(s) != v)
    assert not changed, ('Never-saved pinned file changed', changed)


def expected_child_disk(state, child_path, pins):
    row = (state.get('s1_disk') or {}).get(child_path)
    return row['sha256'] if row else pins[str(package_file(child_path).resolve())]


def saved_master_unchanged(saved):
    for package in [MASTER] + [FUNCTION_DIR + '/' + n for n in FUNCTIONS]:
        assert disk_state(package_file(package)) == saved['disk_after'][package], 'Saved master/MF changed on disk: ' + package


def review_gate(args, pid, areas, state_file, state):
    """Review r2: the approval must name exactly the saved areas and the exact state being saved."""
    state_sha = sha(state_file)
    if args.get('visual_review_receipt'):
        review_file, doc = load_doc(args['visual_review_receipt'], args['visual_review_receipt_sha256'])
        assert doc['pid'] == pid and doc['save_approved'] is True, 'Visual review must approve the save'
        assert sorted(doc['areas']) == sorted(areas), ('Review must list exactly the saved areas', doc['areas'], areas)
        assert doc['state_receipt_sha256'] == state_sha, 'Review approved another state receipt'
        assert doc['state_instances_sha256'] == state['state_instances_sha256'], 'Review approved another instance state'
        captures = doc.get('captures') or {}
        assert all(captures.get(a) for a in areas), 'Review lacks captures for a saved area'
        return {'file': str(review_file), 'sha256': sha(review_file), 'stage': doc.get('stage'), 'areas': sorted(areas)}
    waiver = args.get('visual_review_waiver') or {}
    assert waiver.get('by') and waiver.get('reason'), 'Save needs a visual review receipt or a root waiver'
    assert sorted(waiver.get('areas') or []) == sorted(areas) and waiver.get('state_receipt_sha256') == state_sha, \
        'Waiver must name the saved areas and the state receipt SHA'
    return {'waiver': waiver}


def save(h, args, label):
    ctx, script_sha = common_preflight(h, args, 'save')
    preconditions = operator_preconditions(args)
    pid, area = os.getpid(), ctx['area']
    apply_file, applied = load_doc(args['apply_receipt'], args['apply_receipt_sha256'])
    assert applied.get('schema') == APPLY_SCHEMA, 'Not an S1v2 apply receipt'
    assert applied['status'] == 'APPLIED_VERIFIED_NO_SAVE' and applied['pid'] == pid and applied['world'] == ctx['world']
    assert applied['script_sha256'] == script_sha and sorted(applied['plans']) == [area], 'Save scope is the open area'
    state_file, state = load_state(args, apply_file)
    if state['schema'] != APPLY_SCHEMA:
        assert state['schema'] == TUNE_SCHEMA and state['phase'] == 'a' and state['pid'] == pid and state['area'] == area, \
            'Save takes the apply receipt or a phase-a tune receipt of this PID'
    _, backup_shas = check_backup_saved_state(args, applied, [MASTER, CHILDREN[area]])
    checked_live_state(h, applied, PREFIX + 'SAVE_MISMATCH_GRAPH', label, state)
    before = dirty(h)
    assert before == {'maps': [], 'content': applied['expected_dirty']}, ('Dirty set changed since apply', before)
    scan = log_scan(applied['log']['offset'])
    assert scan['clean'], ('Editor log shows material compile errors since apply', scan)
    material, base, grass, children, instances = load_assets(h)
    stats = statistics_gate(children[area], base)
    review = review_gate(args, pid, [area], state_file, state)
    once = RECEIPTS / SAVE_ONCE
    out = RECEIPTS / (PREFIX + 'SAVE_' + label + '_PID' + str(pid) + '.json')
    assert not once.exists() and not out.exists(), 'Save attempt already recorded'
    groups = [('functions', [FUNCTION_DIR + '/' + n for n in FUNCTIONS]), ('master', [MASTER]),
              ('children', [CHILDREN[area]])]  # review r2: only the reviewed open-area child
    receipt = {'schema': SAVE_SCHEMA, 'status': 'attempt_started', 'mode': 'save', 'area': area,
               'label': label, 'pid': pid, 'world': ctx['world'], 'utc': now(), 'script_sha256': script_sha,
               'apply_receipt': {'file': str(apply_file), 'sha256': sha(apply_file)},
               'state_receipt': {'file': str(state_file), 'sha256': sha(state_file), 'schema': state['schema']},
               'visual_review': review, 'statistics_gate': stats, 'operator_preconditions': preconditions,
               **run_identity(ctx), 'log_scan': scan, 'dirty_before': before, 'saves': []}
    with once.open('x', encoding='utf-8') as stream:
        json.dump({'pid': pid, 'status': 'attempt_started', 'receipt': str(out)}, stream, indent=1)
    try:
        for group, packages in groups:
            objects = [unreal.load_asset(p).get_outermost() for p in packages]
            assert [h.path(o) for o in objects] == packages, group
            ok = unreal.EditorLoadingAndSavingUtils.save_packages(objects, False)  # GP native_revision_save.py:42
            receipt['saves'].append({'group': group, 'packages': packages, 'result': bool(ok),
                                     'disk_after': {p: disk_state(package_file(p)) for p in packages}})
            assert ok, 'Named save failed: ' + group
            assert not set(packages) & set(dirty(h)['content']), ('Still dirty after save', group)
        after = dirty(h)
        assert after == {'maps': [], 'content': []}, ('Dirty after named saves', after)
        saved = {p for _, packages in groups for p in packages}
        for source, expected_sha in backup_shas.items():
            if not any(Path(source) == package_file(p) for p in saved):
                assert sha(source) == expected_sha, 'Unsaved preserved file changed: ' + source
        assert mw_files(applied['plans']) == applied['mw_file_sha256'], 'Vendor texture file changed'
        if state['schema'] == TUNE_SCHEMA:
            assert mw_files({area: state['effective_plans'][area]}) == state['mw_file_sha256'], 'Vendor texture file changed'
        live_state_matches_apply(h, applied, state)
        disk_after = {p: disk_state(package_file(p)) for p in sorted(saved)}
        receipt.update(status='SAVED_NAMED_ONLY', dirty_after=after, disk_after=disk_after, s1_disk=disk_after,
                       state_instances=state['state_instances'], state_instances_sha256=state['state_instances_sha256'],
                       state_switches=state['state_switches'], effective_plans=state['effective_plans'],
                       never_saved=[BASE, GRASS, *MAPS.values(), *(CHILDREN[a] for a in MAPS if a != area),
                                    'vendor packages'],
                       note_s1_verify=('effective_plans differ from apply plans after a tune; s1_verify.py c_save_binding '
                                       'reads apply plans' if state['schema'] == TUNE_SCHEMA else 'untuned save'),
                       next_step='Fresh reopen of each Gaza map, then mode=verify and S1_fresh captures; the other Gaza '
                                 'area uses mode=tune (phase b) + child_save in its own map session.')
    except Exception as error:
        receipt.update(status='FAILED_DURING_SAVE_REQUIRES_ROOT_REVIEW', error=repr(error), dirty_at_failure=dirty(h))
        out.write_text(json.dumps(receipt, indent=1), encoding='utf-8')
        once.write_text(json.dumps({'pid': pid, 'status': receipt['status'], 'receipt': str(out)}, indent=1), encoding='utf-8')
        raise
    out.write_text(json.dumps(receipt, indent=1), encoding='utf-8')
    once.write_text(json.dumps({'pid': pid, 'status': receipt['status'], 'receipt': str(out)}, indent=1), encoding='utf-8')
    return {'ok': True, 'status': receipt['status'], 'receipt': {'file': str(out), 'sha256': sha(out)},
            'disk_after': receipt['disk_after']}


def tune_expected(before, child_path, plan):
    updates = {'textures': {k: v['path'] for k, v in plan['textures'].items()},
               'vectors': plan['vectors'], 'scalars': plan['scalars']}
    result = {}
    for path, state in before.items():
        row = json.loads(json.dumps(state))
        mine = updates if path == child_path else json.loads(json.dumps(EMPTY_PLAN))
        for kind in ('scalars', 'vectors', 'textures'):
            unknown = sorted(set(mine[kind]) - set(row[kind]))
            assert not unknown, ('Tune names parameters the master does not have', unknown)
            row[kind].update(mine[kind])
        result[path] = {'state': row, 'updates': mine}
    return result


def tune(h, args, label):
    """Child-only S1 value iteration for CHILDREN[open area] (review r2). Phase a: apply PID before the
    master save. Phase b: after the master save (save_receipt), any PID whose open map is a Gaza area;
    for an area never enabled it also sets the switch True. Never writes master/base/MFs/maps."""
    ctx, script_sha = common_preflight(h, args, 'tune')
    preconditions = operator_preconditions(args)
    pid, area = os.getpid(), ctx['area']
    child_path = CHILDREN[area]
    apply_file, applied = load_doc(args['apply_receipt'], args['apply_receipt_sha256'])
    assert applied.get('schema') == APPLY_SCHEMA and applied['status'] == 'APPLIED_VERIFIED_NO_SAVE'
    apply_sha = sha(apply_file)
    state_file, state = load_state(args, apply_file)
    save_ref = None
    if args.get('save_receipt'):
        save_file, saved = load_doc(args['save_receipt'], args['save_receipt_sha256'])
        assert saved.get('schema') == SAVE_SCHEMA and saved['status'] == 'SAVED_NAMED_ONLY'
        assert saved['apply_receipt']['sha256'] == apply_sha, 'Save receipt belongs to another apply'
        save_ref = {'file': str(save_file), 'sha256': sha(save_file)}
        saved_master_unchanged(saved)
        assert state['schema'] != APPLY_SCHEMA, 'Phase b state is the save, a tune or a child_save receipt'
        if state['schema'] == SAVE_SCHEMA:
            assert sha(state_file) == save_ref['sha256'], 'A different save receipt'
        else:
            assert (state.get('save_receipt') or {}).get('sha256') == save_ref['sha256'], 'State receipt predates this save'
        phase = 'b'
    else:
        assert pid == applied['pid'] and applied['world'] == ctx['world'] and applied['script_sha256'] == script_sha, \
            'Phase a runs in the apply PID/map with the apply script'
        assert not (RECEIPTS / SAVE_ONCE).exists(), 'Master save attempted: use phase b with its save receipt'
        assert state['schema'] in (APPLY_SCHEMA, TUNE_SCHEMA) and state['pid'] == pid, 'Phase a state is this PID'
        phase = 'a'
    if state['schema'] == TUNE_SCHEMA:
        assert state['phase'] == phase, 'State tune receipt is from the other phase'
    done = []
    for file in sorted(RECEIPTS.glob(PREFIX + 'TUNE_*.json')):
        if not file.name.startswith(TUNE_ONCE):
            if json.loads(file.read_text(encoding='utf-8')).get('area') == area:
                done.append(file.name)
    assert len(done) < ctx['activation']['max_tune_iterations'], ('Tune iteration budget used', done)
    _, pins = check_backup_saved_state(args, applied, [child_path])
    unsaved_pins_unchanged(pins)
    child_disk = disk_state(package_file(child_path))
    assert child_disk.get('sha256') == expected_child_disk(state, child_path, pins), 'Child file changed outside S1'
    checked_live_state(h, applied, PREFIX + 'TUNE_MISMATCH_GRAPH', label, state)
    if phase == 'a':
        dirty_expected = sorted(applied['expected_dirty'])
    elif state['schema'] == TUNE_SCHEMA and state['pid'] == pid:
        dirty_expected = [child_path]
    else:
        dirty_expected = []
    before = dirty(h)
    assert before == {'maps': [], 'content': dirty_expected}, ('Dirty set before tune', before)
    dirty_after_expected = sorted(set(dirty_expected) | {child_path})
    plans = plan_children(args, applied['existing_texture_param_kinds'])
    plan = plans[area]
    previous = (state.get('effective_plans') or {}).get(area) or EMPTY_PLAN
    for kind in ('textures', 'vectors', 'scalars'):
        dropped = sorted(set(previous[kind]) - set(plan[kind]))
        assert not dropped, ('A tune cannot drop an S1 override (no per-parameter clear in Python)', kind, dropped)
    effective_plans = dict(state.get('effective_plans') or {})
    effective_plans[area] = plan
    textures = check_textures(h, plans, set(applied['allowed_textures']))
    mw_before = mw_files(plans)
    material, base, grass, children, instances = load_assets(h)
    child = children[area]
    before_instances = {p: h.material_state(material, mi) for p, mi in instances.items()}
    before_switches = switch_state(material, instances)
    scene_before = digest(h.scene_state(ctx['actors']))
    once = RECEIPTS / (TUNE_ONCE + label + '.json')
    out = RECEIPTS / (PREFIX + 'TUNE_' + label + '_PID' + str(pid) + '.json')
    assert not once.exists() and not out.exists(), 'Tune label already used; root reviews before another'
    receipt = {'schema': TUNE_SCHEMA, 'status': 'attempt_started', 'mode': 'tune', 'phase': phase, 'label': label,
               'pid': pid, 'world': ctx['world'], 'area': area, 'utc': now(), 'script_sha256': script_sha,
               'apply_receipt': {'file': str(apply_file), 'sha256': apply_sha}, 'save_receipt': save_ref,
               'state_receipt': {'file': str(state_file), 'sha256': sha(state_file), 'schema': state['schema']},
               'operator_preconditions': preconditions, **run_identity(ctx), 'plan': plan, 'planned_textures': textures,
               'previous_plan': previous, 'child_disk_before': child_disk, 'dirty_before': before,
               'log': {'file': str(log_file()), 'offset': log_file().stat().st_size},
               'setter_returns': {}, 'explicit_save_called': False}
    with once.open('x', encoding='utf-8') as stream:
        json.dump({'pid': pid, 'area': area, 'status': 'attempt_started', 'receipt': str(out)}, stream, indent=1)
    try:
        receipt['setter_returns']['switch'] = bool(LIB.set_material_instance_static_switch_parameter_value(child, SWITCH, True))
        for name, row in plan['textures'].items():
            receipt['setter_returns'][name] = bool(LIB.set_material_instance_texture_parameter_value(
                child, name, unreal.load_asset(row['path'])))
        for name, value in plan['vectors'].items():
            receipt['setter_returns'][name] = bool(LIB.set_material_instance_vector_parameter_value(
                child, name, unreal.LinearColor(*value)))
        for name, value in plan['scalars'].items():
            receipt['setter_returns'][name] = bool(LIB.set_material_instance_scalar_parameter_value(child, name, value))
        LIB.update_material_instance(child)
        assert LIB.get_material_instance_static_switch_parameter_value(child, SWITCH) is True, 'Switch readback'
        receipt['dirty_after_setters'] = dirty(h)
        assert not receipt['dirty_after_setters']['maps'], 'STOP_MAP_DIRTY_AFTER_TUNE'
        live = {p: h.material_state(material, mi) for p, mi in instances.items()}
        check_instances(h, live, tune_expected(before_instances, child_path, plan))
        LIB.set_material_instance_parent(child, base)  # G2: exact LW:366-367 calls
        LIB.update_material_instance(child)
        assert child.get_editor_property('parent') == base
        assert {p: h.material_state(material, mi) for p, mi in instances.items()} == live, 'G2 replay changed overrides'
        switches_after = switch_state(material, instances)
        assert switches_after['names'] == before_switches['names'] and switches_after['defaults'] == before_switches['defaults']
        for p, values in switches_after['instances'].items():
            want = dict(before_switches['instances'][p])
            if p == child_path:
                want[SWITCH] = True
            assert values == want, ('Static switch state', p)
        ctx_after = guard(h, args, 'tune')
        assert digest(h.scene_state(ctx_after['actors'])) == scene_before, 'Scene changed'
        live_state_matches_apply(h, applied, {'state_instances': live, 'state_switches': switches_after})
        final_dirty = dirty(h)
        assert final_dirty == {'maps': [], 'content': dirty_after_expected}, ('Tune dirty set', final_dirty)
        unsaved_pins_unchanged(pins)
        assert disk_state(package_file(child_path)) == child_disk, 'Child file written by a tune'
        if save_ref:
            saved_master_unchanged(saved)
        assert mw_files(plans) == mw_before, 'Vendor texture file changed'
        receipt.update(status='TUNED_VERIFIED_NO_SAVE', state_instances=live, state_instances_sha256=digest(live),
                       state_switches=switches_after, effective_plans=effective_plans,
                       s1_disk=state.get('s1_disk') or {}, mw_file_sha256=mw_before, dirty_after=final_dirty,
                       child_statistics=statistics(child), base_statistics=statistics(base),
                       next_step=('mode=save in this PID with state_receipt=this receipt' if phase == 'a' else
                                  'mode=child_save in this PID with state_receipt=this receipt') +
                                 ' after capture/review, or another tune; on doubt exit with Do not Save.')
    except Exception as error:
        receipt.update(status='FAILED_NO_SAVE_REQUIRES_ROOT_REVIEW', error=repr(error),
                       instruction='No cleanup was attempted. Close the editor with "Don\'t Save".')
        try:
            receipt['dirty_at_failure'] = dirty(h)
        except Exception as snapshot_error:
            receipt['failure_snapshot_error'] = repr(snapshot_error)
        out.write_text(json.dumps(receipt, indent=1), encoding='utf-8')
        once.write_text(json.dumps({'pid': pid, 'area': area, 'status': receipt['status'], 'receipt': str(out)}, indent=1),
                        encoding='utf-8')
        raise
    out.write_text(json.dumps(receipt, indent=1), encoding='utf-8')
    once.write_text(json.dumps({'pid': pid, 'area': area, 'status': receipt['status'], 'receipt': str(out)}, indent=1),
                    encoding='utf-8')
    return {'ok': True, 'status': receipt['status'], 'phase': phase, 'receipt': {'file': str(out), 'sha256': sha(out)},
            'state_instances_sha256': receipt['state_instances_sha256'], 'explicit_save_called': False}


def child_save(h, args, label):
    """Saves ONLY CHILDREN[open area] from a reviewed phase-b tune receipt of this PID (review r2)."""
    ctx, script_sha = common_preflight(h, args, 'child_save')
    preconditions = operator_preconditions(args)
    pid, area = os.getpid(), ctx['area']
    child_path = CHILDREN[area]
    apply_file, applied = load_doc(args['apply_receipt'], args['apply_receipt_sha256'])
    assert applied.get('schema') == APPLY_SCHEMA and applied['status'] == 'APPLIED_VERIFIED_NO_SAVE'
    save_file, saved = load_doc(args['save_receipt'], args['save_receipt_sha256'])
    assert saved.get('schema') == SAVE_SCHEMA and saved['status'] == 'SAVED_NAMED_ONLY'
    assert saved['apply_receipt']['sha256'] == sha(apply_file), 'Save receipt belongs to another apply'
    state_file, state = load_state(args, apply_file)
    assert state['schema'] == TUNE_SCHEMA and state['phase'] == 'b' and state['pid'] == pid and state['area'] == area, \
        'child_save takes a phase-b tune receipt of this PID and area'
    assert state['save_receipt']['sha256'] == sha(save_file), 'Tune receipt belongs to another save'
    saved_master_unchanged(saved)
    _, pins = check_backup_saved_state(args, applied, [child_path])
    unsaved_pins_unchanged(pins)
    assert disk_state(package_file(child_path)) == state['child_disk_before'], 'Child file changed since the tune'
    checked_live_state(h, applied, PREFIX + 'CHILD_SAVE_MISMATCH_GRAPH', label, state)
    before = dirty(h)
    assert before == {'maps': [], 'content': [child_path]}, ('Dirty set before child_save', before)
    scan = log_scan(state['log']['offset'])
    assert scan['clean'], ('Editor log shows material compile errors since the tune', scan)
    material, base, grass, children, instances = load_assets(h)
    stats = statistics_gate(children[area], base)
    review = review_gate(args, pid, [area], state_file, state)
    once = RECEIPTS / (CHILD_SAVE_ONCE + label + '.json')
    out = RECEIPTS / (PREFIX + 'CHILD_SAVE_' + label + '_PID' + str(pid) + '.json')
    assert not once.exists() and not out.exists(), 'Child save label already used'
    receipt = {'schema': CHILD_SAVE_SCHEMA, 'status': 'attempt_started', 'mode': 'child_save', 'label': label,
               'pid': pid, 'world': ctx['world'], 'area': area, 'utc': now(), 'script_sha256': script_sha,
               'apply_receipt': {'file': str(apply_file), 'sha256': sha(apply_file)},
               'save_receipt': {'file': str(save_file), 'sha256': sha(save_file)},
               'state_receipt': {'file': str(state_file), 'sha256': sha(state_file), 'schema': state['schema']},
               'visual_review': review, 'statistics_gate': stats, 'operator_preconditions': preconditions,
               **run_identity(ctx), 'log_scan': scan, 'dirty_before': before, 'saves': []}
    with once.open('x', encoding='utf-8') as stream:
        json.dump({'pid': pid, 'area': area, 'status': 'attempt_started', 'receipt': str(out)}, stream, indent=1)
    try:
        package = unreal.load_asset(child_path).get_outermost()
        assert h.path(package) == child_path
        ok = unreal.EditorLoadingAndSavingUtils.save_packages([package], False)
        disk_after = {child_path: disk_state(package_file(child_path))}
        receipt['saves'].append({'group': 'child', 'packages': [child_path], 'result': bool(ok), 'disk_after': disk_after})
        assert ok, 'Named child save failed'
        after = dirty(h)
        assert after == {'maps': [], 'content': []}, ('Dirty after child save', after)
        unsaved_pins_unchanged(pins)
        saved_master_unchanged(saved)
        assert mw_files({area: state['effective_plans'][area]}) == state['mw_file_sha256'], 'Vendor texture file changed'
        live_state_matches_apply(h, applied, state)
        s1_disk = dict(state.get('s1_disk') or {})
        s1_disk.update(disk_after)
        receipt.update(status='CHILD_SAVED_NAMED_ONLY', dirty_after=after, disk_after=disk_after, s1_disk=s1_disk,
                       state_instances=state['state_instances'], state_instances_sha256=state['state_instances_sha256'],
                       state_switches=state['state_switches'], effective_plans=state['effective_plans'],
                       mw_file_sha256=state['mw_file_sha256'],
                       never_saved=[MASTER, BASE, GRASS, *MAPS.values(), 'MF packages', 'vendor packages'],
                       next_step='Fresh reopen, then mode=verify with child_save_receipts including this receipt.')
    except Exception as error:
        receipt.update(status='FAILED_DURING_SAVE_REQUIRES_ROOT_REVIEW', error=repr(error), dirty_at_failure=dirty(h))
        out.write_text(json.dumps(receipt, indent=1), encoding='utf-8')
        once.write_text(json.dumps({'pid': pid, 'area': area, 'status': receipt['status'], 'receipt': str(out)}, indent=1),
                        encoding='utf-8')
        raise
    out.write_text(json.dumps(receipt, indent=1), encoding='utf-8')
    once.write_text(json.dumps({'pid': pid, 'area': area, 'status': receipt['status'], 'receipt': str(out)}, indent=1),
                    encoding='utf-8')
    return {'ok': True, 'status': receipt['status'], 'receipt': {'file': str(out), 'sha256': sha(out)},
            'disk_after': receipt['disk_after']}


def verify(h, args, label):
    ctx, script_sha = common_preflight(h, args, 'verify')
    pid = os.getpid()
    apply_file, applied = load_doc(args['apply_receipt'], args['apply_receipt_sha256'])
    save_file, saved = load_doc(args['save_receipt'], args['save_receipt_sha256'])
    assert applied.get('schema') == APPLY_SCHEMA and saved.get('schema') == SAVE_SCHEMA, 'Not S1v2 receipts'
    assert applied['status'] == 'APPLIED_VERIFIED_NO_SAVE' and saved['status'] == 'SAVED_NAMED_ONLY'
    assert saved['apply_receipt']['sha256'] == sha(apply_file)
    child_saves = []
    for ref in args.get('child_save_receipts') or []:
        file, doc = load_doc(ref['file'], ref['sha256'])
        assert doc.get('schema') == CHILD_SAVE_SCHEMA and doc.get('status') == 'CHILD_SAVED_NAMED_ONLY', str(file)
        assert doc['apply_receipt']['sha256'] == sha(apply_file) and doc['save_receipt']['sha256'] == sha(save_file)
        child_saves.append((file, doc))
    child_saves.sort(key=lambda row: row[1]['utc'])
    earlier = sorted({applied['pid'], saved['pid'], *(doc['pid'] for _, doc in child_saves)})
    assert pid not in earlier, ('verify requires a fresh process', pid, earlier)  # review r2
    expected = {'state_instances': json.loads(json.dumps(saved['state_instances'])),
                'state_switches': json.loads(json.dumps(saved['state_switches']))}
    disk_rows = dict(saved['disk_after'])
    for _, doc in child_saves:  # later child-only saves replace that child's state and file
        child = CHILDREN[doc['area']]
        expected['state_instances'][child] = doc['state_instances'][child]
        expected['state_switches']['instances'][child] = doc['state_switches']['instances'][child]
        disk_rows.update(doc['disk_after'])
    current = dirty(h)
    assert current == {'maps': [], 'content': []}, ('Fresh reopen is dirty', current)
    material, instances = checked_live_state(h, applied, PREFIX + 'VERIFY_MISMATCH_GRAPH', label, expected)
    for package, row in disk_rows.items():
        assert disk_state(package_file(package)) == row, 'Saved package changed on disk: ' + package
    _, backup_shas = check_backup_saved_state(args, applied)
    saved_files = {str(package_file(p)) for p in disk_rows}
    for source, expected_sha in backup_shas.items():
        if source not in saved_files:
            assert sha(source) == expected_sha, 'Preserved file changed: ' + source
    assert mw_files(applied['plans']) == applied['mw_file_sha256']
    for _, doc in child_saves:
        assert mw_files({doc['area']: doc['effective_plans'][doc['area']]}) == doc['mw_file_sha256']
    scan = log_scan(0)  # whole fresh-session log
    assert not scan['named_hits'], ('Fresh-session log names S1 assets with errors', scan['named_hits'][:20])
    ack = args.get('unattributed_log_ack') or {}
    assert not scan['unattributed_material_errors'] or (ack.get('by') and ack.get('reason')), \
        ('Fresh-session log has unattributed material compile failures; root reviews (unattributed_log_ack)',
         scan['unattributed_material_errors'][:20])
    assert dirty(h) == current
    receipt = {'log_scan': scan, 'schema': VERIFY_SCHEMA, 'status': 'VERIFIED_READ_ONLY',
               'mode': 'verify', 'label': label, 'pid': pid, 'world': ctx['world'], 'area': ctx['area'], 'utc': now(),
               'script_sha256': script_sha, 'fresh_process': True, 'earlier_pids': earlier, **run_identity(ctx),
               'apply_receipt': {'file': str(apply_file), 'sha256': sha(apply_file)},
               'save_receipt': {'file': str(save_file), 'sha256': sha(save_file)},
               'child_save_receipts': [{'file': str(f), 'sha256': sha(f)} for f, _ in child_saves],
               'unattributed_log_ack': ack or None, 'disk_rows': disk_rows,
               'graph_sha256': applied['graph_after_sha256'], 'dirty': current, 'landscapes': ctx['landscapes'],
               'child_statistics': {a: statistics(unreal.load_asset(CHILDREN[a])) for a in MAPS},
               'base_statistics': statistics(unreal.load_asset(BASE)), 'native_mutation': False,
               'visual_acceptance': 'NOT_JUDGED_HERE; S1_fresh captures and Aviv review remain separate'}
    out = write_new(RECEIPTS / (PREFIX + 'VERIFY_' + label + '_PID' + str(pid) + '.json'), receipt)
    return {'ok': True, 'status': receipt['status'], 'receipt': out, 'fresh_process': True}


def main():
    raw = os.environ.get('GEOCITY_S1_ARGS')
    if not raw:
        return {'ok': False, 'idle': True, 'reason': 'GEOCITY_S1_ARGS is unset; nothing was done.'}
    bind_unreal()
    file = Path(raw).resolve(strict=True)
    assert file.is_relative_to(STAGE) and file.suffix == '.json', 'Args must be a JSON file under Stage1_Ground'
    args = json.loads(file.read_text(encoding='utf-8-sig'))
    label = args['label']
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label), label
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    h = load_helper()
    mode = args['mode']
    handler = {'inspect': inspect, 'apply': apply, 'tune': tune, 'save': save, 'child_save': child_save,
               'verify': verify}[mode]
    result = handler(h, args, label)
    result['args_file'] = {'file': str(file), 'sha256': sha(file)}
    return result


RESULT = main()
