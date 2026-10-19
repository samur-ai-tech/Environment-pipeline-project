"""In-editor on a PCG clone. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef tool (Aviv approved "Real
materials per plot"; playbook 7.5 and 8.3: the farm branch is reusable for any field blend). Real tiling ground materials
blended by a weight mask (made offline per site: R tilled soil, G grass/weedy margin, B compacted dirt, A coverage).
The site is an argument: ARGS.site (folder and name prefix, e.g. the hero-site name); nothing shared is edited.
NEW clone-owned packages in <clone>/<site>/RealGround/:
   T_<site>_GroundMask_v2, M_GeoCityAuto_<AREA_SHORT>_RealFarm_v2 (copy of the area master + the farm branch below),
   MI_GeoCityGround_<site>Real_v2 (copy of the area MI, reparented; FarmR_Blend 1, a painted Farm_Blend stays 0).
Only the clone map's landscape material changes (saved later with the map). Undo: landscape material back to the
previous MI (ARGS.painted_mi when a painted site MI exists, else the area MI); the new folder can be deleted.
Precondition of find_sat() (graph chain, RG3 #1): the area master copy must reach MakeMaterialAttributes.BaseColor through
a painted-farm Lerp (input A) whose input A is the satellite Lerp of build_ground_satellite.py (sat x detail on input B,
a 'SatelliteColor' TextureSampleParameter2D as its first input); 'build' refuses (assert) on any other chain.
Farm branch (pixel attributes, world-aligned tiling textures from installed packs, read only):
   soil   Modular_Rural_Cabin Mud            tilled  FC_Coastal T_SoilGround_02 (+ Mud normal)
   grass  ForestLandscape fl2_ground_VII     dirt    Modular_Rural_Cabin Ground_Dirt
   colour = texture x FarmR_Tint_<layer> (tints match the surrounding Sentinel-2 colours; MI-tunable, no recompile)
   two texture scales per colour layer against tiling; farm attributes = soil -> lerp tilled(R) -> grass(G) -> dirt(B)
   output = BlendMaterialAttributes(original, farm, mask.A * FarmR_Blend)
steps: build | tune (ARGS.vectors {name: [r,g,b]}, ARGS.scalars {name: v} on the new MI) | assign | status
ARGS: expected_pid, script_file (client), clone_suffix (required: '' first clone, '_v2' rebuilt clone), site (required),
painted_mi (optional), step, mask_png + origin_x/origin_y/size_cm (build; UE cm of the mask's north-west corner and side).
v2 (Karmei Yosef): mask = road-to-road parcels, FarmR_Origin*/FarmR_SizeCm, satellite colour mix.
"""
import datetime, hashlib, importlib.util, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
TRIAL = A.TRIAL_ROOT
CLONE = A.clone_map(ARGS['clone_suffix'])                               # required: '' first clone, '_v2' rebuilt clone
AREA = A.AREA_MATERIALS
SRC_MAT, SRC_MI = A.GROUND_MASTER_COPY, A.GROUND_MI
SITE = ARGS['site']                                                    # site name: clone folder and name prefix
assert isinstance(SITE, str) and SITE.isidentifier(), ('ARGS.site must be one plain name', SITE)
RG = TRIAL + '/' + SITE + '/RealGround'
MASK, MAT, MI = (RG + '/T_%s_GroundMask_v2' % SITE, RG + '/M_GeoCityAuto_%s_RealFarm_v2' % A.AREA_SHORT,
                 RG + '/MI_GeoCityGround_%sReal_v2' % SITE)
PAINTED_MI = ARGS.get('painted_mi')                                    # information only (undo target)
GROUP = SITE + ' Real Ground'
MRC = '/Game/Modular_Rural_Cabin/Textures/Tiling/'
LAYERS = {   # name: (basecolor, normal, tile cm, roughness, default tint (linear multiplier))
    'Soil': (MRC + 'Mud_Basecolor', MRC + 'Mud_Normal', 350.0, 0.92, (2.12, 1.51, 1.17)),
    'Tilled': ('/Game/FC_Coastal_Landscape/Landscape/LandscapeTextures/T_SoilGround_02_BC', MRC + 'Mud_Normal', 450.0, 0.95, (1.70, 1.17, 0.93)),
    'Grass': ('/Game/ForestLandscape/Textures/4k/fl2_ground_VII_albedo', '/Game/ForestLandscape/Textures/4k/fl2_ground_VII_normal', 300.0, 0.9, (0.75, 0.88, 0.85)),
    'Dirt': (MRC + 'Ground_Dirt_Basecolor', MRC + 'Ground_Dirt_Normal', 400.0, 0.85, (2.23, 1.91, 1.22)),
}
ML = u.MaterialEditingLibrary
MEANS = {'Soil': (0.1442, 0.107, 0.0727), 'Tilled': (0.1062, 0.0796, 0.0535), 'Grass': (0.4042, 0.2285, 0.0904), 'Dirt': (0.1998, 0.1689, 0.1543)}
REL = {'Soil': (1.0, 1.0, 1.0), 'Tilled': (0.72, 0.7, 0.68), 'Grass': (1.05, 1.05, 0.9), 'Dirt': (1.3, 1.25, 1.2)}


def find_sat(mat, mma):
    """the Sentinel-2 colour sample of the area master: MMA.BaseColor <- painted-farm lerp.A <- satellite lerp.B (sat x detail).A"""
    names = [str(x) for x in ML.get_material_expression_input_names(mma)]
    farm_lerp = ML.get_inputs_for_material_expression(mat, mma)[names.index('BaseColor')]
    sat_lerp = ML.get_inputs_for_material_expression(mat, farm_lerp)[0]
    mul = ML.get_inputs_for_material_expression(mat, sat_lerp)[1]
    sat = ML.get_inputs_for_material_expression(mat, mul)[0]
    assert str(sat.get_editor_property('parameter_name')) == 'SatelliteColor', sat.get_name()
    return sat


def reachable(mat, roots):
    seen, stack = set(), list(roots)
    out = []
    while stack:
        e = stack.pop()
        if e is None or e.get_name() in seen:
            continue
        seen.add(e.get_name()); out.append(e)
        stack.extend(x for x in ML.get_inputs_for_material_expression(mat, e) if x is not None)
    return out


def add_farm(mat, mma, mask_tex, sat):
    """adds the farm branch after `mma` (the original attributes) and connects the blend to the material output"""
    X0, Y0 = -16000, 5200
    node = lambda cls, dx, dy: ML.create_material_expression(mat, cls, X0 + dx, Y0 + dy)
    C = ML.connect_material_expressions

    def scalar(name, value, dx, dy):
        s = node(u.MaterialExpressionScalarParameter, dx, dy); s.set_editor_property('parameter_name', name)
        s.set_editor_property('default_value', value); s.set_editor_property('group', GROUP); return s

    def vector(name, value, dx, dy):
        s = node(u.MaterialExpressionVectorParameter, dx, dy); s.set_editor_property('parameter_name', name)
        s.set_editor_property('default_value', u.LinearColor(value[0], value[1], value[2], 1.0)); s.set_editor_property('group', GROUP); return s
    wp = node(u.MaterialExpressionWorldPosition, 0, 0)
    xy = node(u.MaterialExpressionComponentMask, 220, 0)
    for c, v in (('r', True), ('g', True), ('b', False), ('a', False)):
        xy.set_editor_property(c, v)
    assert C(wp, '', xy, '')
    # mask frame UV: own parameters (the road-to-road parcels reach far past the painted layer's 512 m square)
    ox = scalar('FarmR_OriginX', FRAME[0], 220, 200); oy = scalar('FarmR_OriginY', FRAME[1], 220, 330)
    app = node(u.MaterialExpressionAppendVector, 450, 250); sub = node(u.MaterialExpressionSubtract, 650, 100)
    size = scalar('FarmR_SizeCm', FRAME[2], 650, 300); div = node(u.MaterialExpressionDivide, 850, 100)
    assert C(ox, '', app, 'A') and C(oy, '', app, 'B') and C(xy, '', sub, 'A') and C(app, '', sub, 'B') and C(sub, '', div, 'A') and C(size, '', div, 'B')
    msk = node(u.MaterialExpressionTextureSampleParameter2D, 1050, 100)
    msk.set_editor_property('parameter_name', 'FarmR_Mask'); msk.set_editor_property('texture', mask_tex)
    msk.set_editor_property('sampler_type', u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    msk.set_editor_property('sampler_source', u.SamplerSourceMode.SSM_CLAMP_WORLD_GROUP_SETTINGS)
    assert C(div, '', msk, 'UVs')
    satmix = scalar('FarmR_SatMix', 0.5, 1150, 500)
    layer_out = {}
    for i, (name, (bc, nm, tile, rough, tint)) in enumerate(LAYERS.items()):
        y = 700 + i * 900
        tl = scalar('FarmR_Tile_' + name, tile, 220, y)
        uv1 = node(u.MaterialExpressionDivide, 450, y); assert C(xy, '', uv1, 'A') and C(tl, '', uv1, 'B')
        k2 = scalar('FarmR_Scale2_' + name, 0.27, 450, y + 160)
        uv2 = node(u.MaterialExpressionMultiply, 650, y + 160); assert C(uv1, '', uv2, 'A') and C(k2, '', uv2, 'B')
        s1 = node(u.MaterialExpressionTextureSample, 900, y); s2 = node(u.MaterialExpressionTextureSample, 900, y + 250)
        sn = node(u.MaterialExpressionTextureSample, 900, y + 500)
        for s, tex, kind in ((s1, bc, u.MaterialSamplerType.SAMPLERTYPE_COLOR), (s2, bc, u.MaterialSamplerType.SAMPLERTYPE_COLOR),
                             (sn, nm, u.MaterialSamplerType.SAMPLERTYPE_NORMAL)):
            s.set_editor_property('texture', u.load_asset(tex)); s.set_editor_property('sampler_type', kind)
            s.set_editor_property('sampler_source', u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        assert C(uv1, '', s1, 'UVs') and C(uv2, '', s2, 'UVs') and C(uv1, '', sn, 'UVs')
        mixk = scalar('FarmR_Mix2_' + name, 0.4, 1150, y + 160)
        mix = node(u.MaterialExpressionLinearInterpolate, 1150, y)
        assert C(s1, 'RGB', mix, 'A') and C(s2, 'RGB', mix, 'B') and C(mixk, '', mix, 'Alpha')
        tv = vector('FarmR_Tint_' + name, tint, 1150, y + 320)
        absc = node(u.MaterialExpressionMultiply, 1400, y); assert C(mix, '', absc, 'A') and C(tv, '', absc, 'B')
        # satellite-driven colour: Sentinel-2 colour of this spot x the pack texture's own detail (texture / its mean) x a relative tint
        mv = vector('FarmR_Mean_' + name, MEANS[name], 1150, y + 450)
        det = node(u.MaterialExpressionDivide, 1400, y + 450); assert C(mix, '', det, 'A') and C(mv, '', det, 'B')
        rv = vector('FarmR_Rel_' + name, REL[name], 1400, y + 600)
        sd = node(u.MaterialExpressionMultiply, 1600, y + 450); assert C(sat, 'RGB', sd, 'A') and C(det, '', sd, 'B')
        satc = node(u.MaterialExpressionMultiply, 1600, y + 600); assert C(sd, '', satc, 'A') and C(rv, '', satc, 'B')
        col = node(u.MaterialExpressionLinearInterpolate, 1650, y); assert C(absc, '', col, 'A') and C(satc, '', col, 'B') and C(satmix, '', col, 'Alpha')
        rg = scalar('FarmR_Rough_' + name, rough, 1400, y + 250)
        layer_out[name] = (col, sn, rg)
    # blend chain soil -> tilled (R) -> grass (G) -> dirt (B)
    chan = {'Tilled': 'R', 'Grass': 'G', 'Dirt': 'B'}
    cur_c, cur_n, cur_r = layer_out['Soil'][0], layer_out['Soil'][1], layer_out['Soil'][2]
    cur_n_pin = 'RGB'
    for i, name in enumerate(('Tilled', 'Grass', 'Dirt')):
        y = 700 + i * 300
        col, sn, rg = layer_out[name]
        lc = node(u.MaterialExpressionLinearInterpolate, 1800, y); ln = node(u.MaterialExpressionLinearInterpolate, 2000, y)
        lr = node(u.MaterialExpressionLinearInterpolate, 2200, y)
        assert C(cur_c, '', lc, 'A') and C(col, '', lc, 'B') and C(msk, chan[name], lc, 'Alpha')
        assert C(cur_n, cur_n_pin, ln, 'A') and C(sn, 'RGB', ln, 'B') and C(msk, chan[name], ln, 'Alpha')
        assert C(cur_r, '', lr, 'A') and C(rg, '', lr, 'B') and C(msk, chan[name], lr, 'Alpha')
        cur_c, cur_n, cur_r, cur_n_pin = lc, ln, lr, ''
    nrm = node(u.MaterialExpressionNormalize, 2450, 1000); assert C(cur_n, '', nrm, '')
    spec = scalar('FarmR_Specular', 0.35, 2450, 1200)
    fmma = node(u.MaterialExpressionMakeMaterialAttributes, 2700, 800)
    assert C(cur_c, '', fmma, 'BaseColor') and C(nrm, '', fmma, 'Normal') and C(cur_r, '', fmma, 'Roughness') and C(spec, '', fmma, 'Specular')
    fb = scalar('FarmR_Blend', 0.0, 2700, 400)
    am = node(u.MaterialExpressionMultiply, 2900, 400); assert C(msk, 'A', am, 'A') and C(fb, '', am, 'B')
    blend = node(u.MaterialExpressionBlendMaterialAttributes, 3150, 600)
    assert C(mma, '', blend, 'A') and C(fmma, '', blend, 'B') and C(am, '', blend, 'Alpha')
    assert ML.connect_material_property(blend, '', u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    assert ML.get_material_property_input_node(mat, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES) == blend
    return blend


pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']
FRAME = (float(ARGS.get('origin_x', 0)), float(ARGS.get('origin_y', 0)), float(ARGS.get('size_cm', 1)))
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
sha = lambda pkg: hashlib.sha256((ROOT / ('Content/' + pkg[6:] + '.uasset')).read_bytes()).hexdigest()
land = [a for a in eas.get_all_level_actors() if isinstance(a, u.Landscape)]
assert len(land) == 1
land = land[0]

if step == 'build':
    for p in (MASK, MAT, MI):
        assert not u.EditorAssetLibrary.does_asset_exist(p), p + ' exists'
    assert FRAME[2] > 1000, FRAME
    for name, (bc, nm, _, _, _) in LAYERS.items():
        n = u.load_asset(nm)
        assert isinstance(u.load_asset(bc), u.Texture2D) and isinstance(n, u.Texture2D), name
        assert n.get_editor_property('compression_settings') == u.TextureCompressionSettings.TC_NORMALMAP, nm
    # 1) mask texture (linear, uncompressed RGBA8, clamped)
    t = u.AssetImportTask()
    for k, v in dict(filename=ARGS['mask_png'], destination_path=RG, destination_name=MASK.rsplit('/', 1)[1], automated=True,
                     replace_existing=False, save=False).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    mask_tex = u.load_asset(MASK)
    mask_tex.set_editor_property('srgb', False)
    mask_tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP)
    mask_tex.set_editor_property('address_x', u.TextureAddress.TA_CLAMP); mask_tex.set_editor_property('address_y', u.TextureAddress.TA_CLAMP)
    mask_tex.set_editor_property('never_stream', True)
    assert u.EditorLoadingAndSavingUtils.save_packages([mask_tex.get_outermost()], False)
    # 2) material copy (the area master is only read)
    mat = u.EditorAssetLibrary.duplicate_asset(SRC_MAT, MAT)
    assert mat is not None
    mma = ML.get_material_property_input_node(mat, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    assert mma.get_class().get_name() == 'MaterialExpressionMakeMaterialAttributes'
    sat = find_sat(mat, mma)
    add_farm(mat, mma, mask_tex, sat)
    ML.recompile_material(mat)
    assert u.EditorLoadingAndSavingUtils.save_packages([mat.get_outermost()], False)
    # 3) MI copy of the area MI (keeps its overrides), reparented to the copy
    mi = u.EditorAssetLibrary.duplicate_asset(SRC_MI, MI)
    ML.set_material_instance_parent(mi, mat)
    ML.set_material_instance_scalar_parameter_value(mi, 'FarmR_Blend', 1.0)
    ML.set_material_instance_scalar_parameter_value(mi, 'Farm_Blend', 0.0)
    ML.update_material_instance(mi)
    assert abs(ML.get_material_instance_scalar_parameter_value(mi, 'FarmR_Blend') - 1.0) < 1e-6
    assert u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)
    RESULT = {'ok': True, 'saved': [MASK, MAT, MI], 'num_expressions': ML.get_num_material_expressions(mat),
              'files': {p: sha(p) for p in (MASK, MAT, MI)}, 'dirty': dirty()}

elif step == 'macro':
    # adds (never deletes) a large-scale brightness variation from the Sentinel-2 luminance of each spot, so the farm ground
    # is not one flat colour from the air: farm BaseColor x lerp(1, lum(sat) / FarmR_SatLumMean, FarmR_MacroAmt)
    mat = u.load_asset(MAT)
    blend = ML.get_material_property_input_node(mat, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    assert blend.get_class().get_name() == 'MaterialExpressionBlendMaterialAttributes'
    ins = ML.get_inputs_for_material_expression(mat, blend)
    mma, fmma = ins[0], ins[1]
    fn = [str(x) for x in ML.get_material_expression_input_names(fmma)]
    cur_c = ML.get_inputs_for_material_expression(mat, fmma)[fn.index('BaseColor')]
    assert cur_c.get_class().get_name() == 'MaterialExpressionLinearInterpolate', cur_c.get_class().get_name()
    sat = find_sat(mat, mma)
    X0, Y0 = -16000 + 2500, 5200 - 900
    node = lambda cls, dx, dy: ML.create_material_expression(mat, cls, X0 + dx, Y0 + dy)
    C = ML.connect_material_expressions
    def scalar(name, value, dx, dy):
        s_ = node(u.MaterialExpressionScalarParameter, dx, dy); s_.set_editor_property('parameter_name', name)
        s_.set_editor_property('default_value', value); s_.set_editor_property('group', GROUP); return s_
    w = node(u.MaterialExpressionConstant3Vector, 0, 0); w.set_editor_property('constant', u.LinearColor(0.3, 0.59, 0.11, 1.0))
    dot = node(u.MaterialExpressionDotProduct, 200, 0); assert C(sat, 'RGB', dot, 'A') and C(w, '', dot, 'B')
    lm = scalar('FarmR_SatLumMean', 0.21, 200, 150)
    rel = node(u.MaterialExpressionDivide, 400, 0); assert C(dot, '', rel, 'A') and C(lm, '', rel, 'B')
    one = node(u.MaterialExpressionConstant, 400, 150); one.set_editor_property('r', 1.0)
    amt = scalar('FarmR_MacroAmt', 0.6, 400, 250)
    mac = node(u.MaterialExpressionLinearInterpolate, 600, 0); assert C(one, '', mac, 'A') and C(rel, '', mac, 'B') and C(amt, '', mac, 'Alpha')
    mul = node(u.MaterialExpressionMultiply, 800, 0); assert C(cur_c, '', mul, 'A') and C(mac, '', mul, 'B')
    assert C(mul, '', fmma, 'BaseColor')
    assert ML.get_inputs_for_material_expression(mat, fmma)[fn.index('BaseColor')] == mul
    ML.recompile_material(mat)
    assert u.EditorLoadingAndSavingUtils.save_packages([mat.get_outermost()], False)
    RESULT = {'ok': True, 'num_expressions': ML.get_num_material_expressions(mat), 'file': sha(MAT), 'dirty': dirty()}

elif step == 'macro_clamp':
    # limits the satellite brightness factor to [FarmR_MacroMin, FarmR_MacroMax] (bright plastic / bare spots made white blotches)
    mat = u.load_asset(MAT)
    blend = ML.get_material_property_input_node(mat, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    fmma = ML.get_inputs_for_material_expression(mat, blend)[1]
    fn = [str(x) for x in ML.get_material_expression_input_names(fmma)]
    mul = ML.get_inputs_for_material_expression(mat, fmma)[fn.index('BaseColor')]
    assert mul.get_class().get_name() == 'MaterialExpressionMultiply'
    mac = ML.get_inputs_for_material_expression(mat, mul)[1]
    assert mac.get_class().get_name() == 'MaterialExpressionLinearInterpolate'
    rel = ML.get_inputs_for_material_expression(mat, mac)[1]
    assert rel.get_class().get_name() == 'MaterialExpressionDivide'
    X0, Y0 = -16000 + 2500, 5200 - 1300
    node = lambda cls, dx, dy: ML.create_material_expression(mat, cls, X0 + dx, Y0 + dy)
    C = ML.connect_material_expressions
    def scalar(name, value, dx, dy):
        s_ = node(u.MaterialExpressionScalarParameter, dx, dy); s_.set_editor_property('parameter_name', name)
        s_.set_editor_property('default_value', value); s_.set_editor_property('group', GROUP); return s_
    lo, hi = scalar('FarmR_MacroMin', 0.75, 400, 0), scalar('FarmR_MacroMax', 1.25, 400, 120)
    cl = node(u.MaterialExpressionClamp, 600, 0)
    assert C(rel, '', cl, '') and C(lo, '', cl, 'Min') and C(hi, '', cl, 'Max') and C(cl, '', mac, 'B')
    assert ML.get_inputs_for_material_expression(mat, mac)[1] == cl
    ML.recompile_material(mat)
    assert u.EditorLoadingAndSavingUtils.save_packages([mat.get_outermost()], False)
    RESULT = {'ok': True, 'num_expressions': ML.get_num_material_expressions(mat), 'file': sha(MAT), 'dirty': dirty()}

elif step == 'reimport_mask':
    # same texture asset, new source PNG (parcels changed); settings kept
    t = u.AssetImportTask()
    for k, v in dict(filename=ARGS['mask_png'], destination_path=RG, destination_name=MASK.rsplit('/', 1)[1], automated=True,
                     replace_existing=True, replace_existing_settings=False, save=False).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = u.load_asset(MASK)
    assert not tex.get_editor_property('srgb') and tex.get_editor_property('compression_settings') == u.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP
    assert u.EditorLoadingAndSavingUtils.save_packages([tex.get_outermost()], False)
    RESULT = {'ok': True, 'file': sha(MASK), 'dirty': dirty()}

elif step == 'set_mask':
    # Karmei Yosef lesson ("every field from the screenshot"): new mask texture (fields, 4096 px, BC7) on the existing MI; no graph edit
    dst = RG + '/' + ARGS['name']
    assert not u.EditorAssetLibrary.does_asset_exist(dst), dst
    t = u.AssetImportTask()
    for k, v in dict(filename=ARGS['mask_png'], destination_path=RG, destination_name=ARGS['name'], automated=True, replace_existing=False, save=False).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = u.load_asset(dst)
    tex.set_editor_property('srgb', False)
    tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_BC7)
    tex.set_editor_property('address_x', u.TextureAddress.TA_CLAMP); tex.set_editor_property('address_y', u.TextureAddress.TA_CLAMP)
    assert u.EditorLoadingAndSavingUtils.save_packages([tex.get_outermost()], False)
    mi = u.load_asset(MI)
    ML.set_material_instance_texture_parameter_value(mi, 'FarmR_Mask', tex)
    for k_, v_ in (('FarmR_OriginX', ARGS['origin_x']), ('FarmR_OriginY', ARGS['origin_y']), ('FarmR_SizeCm', ARGS['size_cm'])):
        ML.set_material_instance_scalar_parameter_value(mi, k_, float(v_))
    ML.update_material_instance(mi)
    assert u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)
    RESULT = {'ok': True, 'mask': dst, 'file': sha(dst), 'dirty': dirty()}

elif step == 'reimport_named':
    # re-import a mask texture in place (same asset, new PNG), settings kept
    dst = RG + '/' + ARGS['name']; assert u.EditorAssetLibrary.does_asset_exist(dst), dst
    t = u.AssetImportTask()
    for k, v in dict(filename=ARGS['mask_png'], destination_path=RG, destination_name=ARGS['name'], automated=True,
                     replace_existing=True, replace_existing_settings=False, save=False).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    assert u.EditorLoadingAndSavingUtils.save_packages([u.load_asset(dst).get_outermost()], False)
    RESULT = {'ok': True, 'file': sha(dst), 'dirty': dirty()}

elif step == 'path_through':
    # Karmei Yosef lesson ("Yes, fix them"): the generator's dirt tracks are only landscape paint (RoadBed -> Dirt_Path, no mesh), so
    # the farm/field ground must step aside there: farm alpha x (1 - saturate(Dirt_Path weight x FarmR_PathKeep)).
    # Adds nodes only (no deletes); must be the FIRST material graph edit of a fresh editor session.
    mat = u.load_asset(MAT)
    blend = ML.get_material_property_input_node(mat, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    assert blend.get_class().get_name() == 'MaterialExpressionBlendMaterialAttributes'
    ins = ML.get_inputs_for_material_expression(mat, blend)
    am = ins[2]
    assert am.get_class().get_name() == 'MaterialExpressionMultiply', am.get_class().get_name()
    X0, Y0 = -16000 + 2900, 5200 - 1700
    node = lambda cls, dx, dy: ML.create_material_expression(mat, cls, X0 + dx, Y0 + dy)
    C = ML.connect_material_expressions
    lay = node(u.MaterialExpressionLandscapeLayerSample, 0, 0); lay.set_editor_property('parameter_name', ARGS.get('layer', 'Dirt_Path'))
    lay.set_editor_property('preview_weight', 0.0)
    keep = node(u.MaterialExpressionScalarParameter, 0, 150); keep.set_editor_property('parameter_name', 'FarmR_PathKeep')
    keep.set_editor_property('default_value', 1.0); keep.set_editor_property('group', GROUP)
    mul = node(u.MaterialExpressionMultiply, 220, 0); assert C(lay, '', mul, 'A') and C(keep, '', mul, 'B')
    sat = node(u.MaterialExpressionSaturate, 420, 0); assert C(mul, '', sat, '')
    inv = node(u.MaterialExpressionOneMinus, 600, 0); assert C(sat, '', inv, '')
    fin = node(u.MaterialExpressionMultiply, 800, 0); assert C(am, '', fin, 'A') and C(inv, '', fin, 'B')
    assert C(fin, '', blend, 'Alpha')
    assert ML.get_inputs_for_material_expression(mat, blend)[2] == fin
    ML.recompile_material(mat)
    assert u.EditorLoadingAndSavingUtils.save_packages([mat.get_outermost()], False)
    RESULT = {'ok': True, 'layer': ARGS.get('layer', 'Dirt_Path'), 'num_expressions': ML.get_num_material_expressions(mat), 'file': sha(MAT), 'dirty': dirty()}

elif step == 'assign':
    before = land.get_editor_property('landscape_material').get_path_name()
    target = u.load_asset(ARGS.get('material', MI))
    land.set_editor_property('landscape_material', target)
    for prx in [a for a in eas.get_all_level_actors() if isinstance(a, u.LandscapeProxy) and a != land]:
        prx.set_editor_property('landscape_material', target)
    RESULT = {'ok': True, 'before': before, 'after': land.get_editor_property('landscape_material').get_path_name(), 'dirty': dirty()}

elif step == 'tune':
    mi = u.load_asset(MI)
    for k, v in ARGS.get('vectors', {}).items():
        ML.set_material_instance_vector_parameter_value(mi, k, u.LinearColor(v[0], v[1], v[2], 1.0))
    for k, v in ARGS.get('scalars', {}).items():
        ML.set_material_instance_scalar_parameter_value(mi, k, float(v))
    ML.update_material_instance(mi)
    saved = False
    if ARGS.get('save'):
        saved = u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)
    RESULT = {'ok': True, 'saved': saved, 'dirty': dirty()}

elif step == 'status':
    mi = u.load_asset(MI) if u.EditorAssetLibrary.does_asset_exist(MI) else None
    out = {'landscape_material': land.get_editor_property('landscape_material').get_path_name(), 'dirty': dirty()}
    if mi:
        out['scalars'] = {str(p.parameter_info.name): p.parameter_value for p in mi.get_editor_property('scalar_parameter_values')}
        out['vectors'] = {str(p.parameter_info.name): [round(p.parameter_value.r, 3), round(p.parameter_value.g, 3), round(p.parameter_value.b, 3)]
                          for p in mi.get_editor_property('vector_parameter_values')}
    RESULT = {'ok': True, **out}
