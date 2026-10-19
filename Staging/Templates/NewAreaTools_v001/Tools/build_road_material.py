"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69) (playbook 10c: road tiling, stochastic texturing). Builds ONE
new area-owned master area_constants.py ROAD_MASTER (<root>/Materials/M_RoadAsphalt_<AREA_SHORT>_v001) for the baked road mesh, whose
UV0 is world metres (1 UV = 1 m):
  UV = TexCoord0 / TileSizeM  ->  Epic's TextureVariation (stochastic offsets driven by a grayscale heightmap; random rotation
  left off so normals stay valid)  ->  'Shifted UVs' sample the 4K ModularCourtyard Asphalt_cracked set (basecolor, normal,
  roughness, AO); BaseColor x large-scale macro variation (engine T_Default_MacroVariation at MacroSizeM) then lerp towards a
  desert DustColor by DustAmount; Roughness x RoughnessMult; Normal strength by NormalStrength.
Everything tunable is a parameter, so later tuning uses a material instance (no further graph edits).
Method (proven in the Karmei Yosef task; MaterialFactoryNew crashed an editor): duplicate StarterContent M_Basic_Wall into the new path
and rebuild its graph. Vendor textures and the engine function are only referenced. Validates every texture's sampler needs
and every connection BEFORE saving; on any failure the new asset is left unsaved and the step reports it.
Crash rule: quit the editor right after this step (no other step, no other save).
ARGS: expected_pid, script_file (client), dry (bool, optional)."""
import os
import importlib.util
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
EA, L = u.EditorAssetLibrary, u.MaterialEditingLibrary
P = u.MaterialProperty
ROOTP = A.AREA_ROOT
DST = A.ROAD_MASTER
TV = '/Engine/Functions/Engine_MaterialFunctions03/Texturing/TextureVariation'
TEX = {'BaseColorTex': '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_basecolor',
       'NormalTex': '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_normal',
       'RoughnessTex': '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_roughness',
       'AOTex': '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_AO',
       'HeightTex': '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_height',
       'MacroTex': '/Engine/EngineMaterials/T_Default_MacroVariation'}
ST = u.MaterialSamplerType


def sampler_for(t):
    cs = t.get_editor_property('compression_settings')
    srgb = t.get_editor_property('srgb')
    if cs == u.TextureCompressionSettings.TC_NORMALMAP:
        return ST.SAMPLERTYPE_NORMAL
    if cs == u.TextureCompressionSettings.TC_GRAYSCALE:
        return ST.SAMPLERTYPE_GRAYSCALE if srgb else ST.SAMPLERTYPE_LINEAR_GRAYSCALE
    if cs == u.TextureCompressionSettings.TC_MASKS:
        return ST.SAMPLERTYPE_MASKS
    return ST.SAMPLERTYPE_COLOR if srgb else ST.SAMPLERTYPE_LINEAR_COLOR


tex = {k: u.load_asset(v) for k, v in TEX.items()}
assert all(tex.values()), {k: bool(v) for k, v in tex.items()}
samplers = {k: sampler_for(t) for k, t in tex.items()}
info = {k: [str(t.get_editor_property('compression_settings')), bool(t.get_editor_property('srgb')), str(samplers[k])] for k, t in tex.items()}
# TextureVariation samples its heightmap as linear grayscale
assert samplers['HeightTex'] == ST.SAMPLERTYPE_LINEAR_GRAYSCALE, ('heightmap must be linear grayscale', info['HeightTex'])
func = u.load_asset(TV)
assert func, TV
assert not EA.does_asset_exist(DST), 'exists: ' + DST
if ARGS.get('dry'):
    RESULT = {'ok': True, 'dry': True, 'textures': info}
else:
    mat = EA.duplicate_asset('/Game/StarterContent/Materials/M_Basic_Wall', DST)
    assert mat, 'duplicate failed'
    L.delete_all_material_expressions(mat)
    X0, Y0 = -1400, -400
    node = lambda cls, dx, dy: L.create_material_expression(mat, cls, X0 + dx, Y0 + dy)
    conn = []

    def C(a, ao, b, bi):
        ok = L.connect_material_expressions(a, ao, b, bi)
        conn.append([ao, bi, bool(ok)])
        assert ok, ('connect failed', ao, bi)

    def scalar(name, value, dx, dy):
        e = node(u.MaterialExpressionScalarParameter, dx, dy)
        e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', float(value))
        return e

    def vector(name, rgb, dx, dy):
        e = node(u.MaterialExpressionVectorParameter, dx, dy)
        e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', u.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        return e

    tc = node(u.MaterialExpressionTextureCoordinate, 0, 0)
    tile = scalar('TileSizeM', 3.0, 0, 120)
    uv = node(u.MaterialExpressionDivide, 200, 40); C(tc, '', uv, 'A'); C(tile, '', uv, 'B')
    hobj = node(u.MaterialExpressionTextureObjectParameter, 200, -200)
    hobj.set_editor_property('parameter_name', 'HeightTex'); hobj.set_editor_property('texture', tex['HeightTex'])
    hobj.set_editor_property('sampler_type', samplers['HeightTex'])
    fc = node(u.MaterialExpressionMaterialFunctionCall, 450, -40)
    if hasattr(fc, 'set_material_function'):
        fc.set_material_function(func)
    else:
        fc.set_editor_property('material_function', func)
    ins = [str(x) for x in L.get_material_expression_input_names(fc)]
    outs = [str(x) for x in L.get_material_expression_output_names(fc)] if hasattr(L, 'get_material_expression_output_names') else []
    assert 'Heightmap' in ins and 'UVs' in ins, ins
    C(hobj, '', fc, 'Heightmap'); C(uv, '', fc, 'UVs')
    shifted = 'Shifted UVs'
    samples = {}
    for i, k in enumerate(('BaseColorTex', 'NormalTex', 'RoughnessTex', 'AOTex')):
        e = node(u.MaterialExpressionTextureSampleParameter2D, 800, -260 + 260 * i)
        e.set_editor_property('parameter_name', k); e.set_editor_property('texture', tex[k]); e.set_editor_property('sampler_type', samplers[k])
        C(fc, shifted, e, 'UVs')
        samples[k] = e
    # macro variation (large scale brightness), dust, brightness
    msize = scalar('MacroSizeM', 40.0, 200, 400)
    muv = node(u.MaterialExpressionDivide, 400, 360); C(tc, '', muv, 'A'); C(msize, '', muv, 'B')
    mtex = node(u.MaterialExpressionTextureSampleParameter2D, 600, 360)
    mtex.set_editor_property('parameter_name', 'MacroTex'); mtex.set_editor_property('texture', tex['MacroTex']); mtex.set_editor_property('sampler_type', samplers['MacroTex'])
    C(muv, '', mtex, 'UVs')
    mlo, mhi = scalar('MacroDark', 0.82, 600, 560), scalar('MacroBright', 1.08, 600, 640)
    mlerp = node(u.MaterialExpressionLinearInterpolate, 850, 560); C(mlo, '', mlerp, 'A'); C(mhi, '', mlerp, 'B'); C(mtex, 'R', mlerp, 'Alpha')
    bc1 = node(u.MaterialExpressionMultiply, 1100, -260); C(samples['BaseColorTex'], 'RGB', bc1, 'A'); C(mlerp, '', bc1, 'B')
    dust = vector('DustColor', (0.50, 0.43, 0.34), 1100, -120)
    damt = scalar('DustAmount', 0.12, 1100, -40)
    bc2 = node(u.MaterialExpressionLinearInterpolate, 1300, -220); C(bc1, '', bc2, 'A'); C(dust, '', bc2, 'B'); C(damt, '', bc2, 'Alpha')
    bright = scalar('Brightness', 1.0, 1300, -60)
    bc3 = node(u.MaterialExpressionMultiply, 1500, -220); C(bc2, '', bc3, 'A'); C(bright, '', bc3, 'B')
    # normal strength: lerp(flat, sampled, NormalStrength)
    flat = node(u.MaterialExpressionConstant3Vector, 1100, 60); flat.set_editor_property('constant', u.LinearColor(0.0, 0.0, 1.0, 1.0))
    nstr = scalar('NormalStrength', 1.0, 1100, 140)
    nl = node(u.MaterialExpressionLinearInterpolate, 1300, 40); C(flat, '', nl, 'A'); C(samples['NormalTex'], 'RGB', nl, 'B'); C(nstr, '', nl, 'Alpha')
    rmul = scalar('RoughnessMult', 1.0, 1100, 260)
    rm = node(u.MaterialExpressionMultiply, 1300, 240); C(samples['RoughnessTex'], 'R', rm, 'A'); C(rmul, '', rm, 'B')
    rc = node(u.MaterialExpressionClamp, 1500, 240); C(rm, '', rc, '')
    props = [[bc3, '', P.MP_BASE_COLOR], [nl, '', P.MP_NORMAL], [rc, '', P.MP_ROUGHNESS], [samples['AOTex'], 'R', P.MP_AMBIENT_OCCLUSION]]
    for e, o, p in props:
        assert L.connect_material_property(e, o, p), ('property connect failed', str(p))
    L.recompile_material(mat)
    assert u.EditorLoadingAndSavingUtils.save_packages([mat.get_outermost()], False)
    RESULT = {'ok': True, 'material': DST, 'function_inputs': ins, 'function_outputs': outs, 'connections': len(conn),
              'textures': info, 'expressions': L.get_num_material_expressions(mat),
              'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
              'next': 'QUIT the editor now (material-graph crash rule)'}
