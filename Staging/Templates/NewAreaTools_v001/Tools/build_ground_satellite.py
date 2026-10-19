"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat fork of the Karmei Yosef tool (Aviv: "real
satellite colours" on the ground). Names and size from area_constants.py (SAT_TEXTURE, ZONES_TEXTURE, GROUND_MASTER_COPY,
GROUND_MI, HALF_EXTENT_CM).
1. Import T_<AREA_SHORT>_Satellite (sRGB colour, clamp) and T_<AREA_SHORT>_Zones (linear grey, nearest, no mips,
   uncompressed, for PCG) into <area>/Materials/Zones/.
2. Duplicate the shared ground master M_GeoCityAuto into <area>/Materials/M_GeoCityAuto_<AREA_SHORT> (the shared master is
   not changed) and insert before MakeMaterialAttributes.BaseColor:
     uv      = (WorldPosition.xy - (-HALF_EXTENT_CM, -HALF_EXTENT_CM)) / (2 HALF_EXTENT_CM)   (X east, Y south, cm)
     sat     = TextureSampleParameter2D 'SatelliteColor' (uv)
     detail  = dot(orig, (0.3, 0.59, 0.11)) / Sat_DetailMid               (keeps the close-up texture variation)
     final   = lerp(orig, sat * detail, Sat_Blend)
3. Reparent this area's MI_GeoCityGround_Auto to the copy and set SatelliteColor; named saves of the two textures, the
   material copy and the MI only. ARGS: expected_pid, script_file (client).
"""
import datetime, hashlib, importlib.util, json, os
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
AREA = A.AREA_ROOT
SHARED = '/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto'
COPY = A.GROUND_MASTER_COPY
MI = A.GROUND_MI
HALF_CM = float(A.HALF_EXTENT_CM)
TEX_DIR = AREA + '/Materials/Zones'
L = u.MaterialEditingLibrary
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
native = lambda pkg: ROOT / ('Content/' + pkg[6:] + '.uasset')
pid = os.getpid(); assert pid == ARGS['expected_pid']
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
first_dirty = dirty()
assert first_dirty[0] == [] and set(first_dirty[1]) <= {COPY}, first_dirty  # a stopped first attempt (13:46Z) left only the unsaved copy
shared_before = sha(native(SHARED))
tex = json.loads((TASK / 'Zones/TEXTURES.json').read_text(encoding='utf-8'))
saves = []

# 1. textures
def import_png(path, name):
    if u.EditorAssetLibrary.does_asset_exist(TEX_DIR + '/' + name):
        return u.load_asset(TEX_DIR + '/' + name)
    t = u.AssetImportTask()
    for k, v in dict(filename=path, destination_path=TEX_DIR, destination_name=name, automated=True, replace_existing=False, save=False).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    objs = list(t.get_objects()); assert len(objs) == 1, objs
    return objs[0]
sat_tex = import_png(tex['satellite'], A.SAT_TEXTURE)
sat_tex.set_editor_property('srgb', True)
sat_tex.set_editor_property('address_x', u.TextureAddress.TA_CLAMP); sat_tex.set_editor_property('address_y', u.TextureAddress.TA_CLAMP)
zone_tex = import_png(tex['zones'], A.ZONES_TEXTURE)
zone_tex.set_editor_property('srgb', False)
zone_tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_GRAYSCALE)
zone_tex.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
zone_tex.set_editor_property('filter', u.TextureFilter.TF_NEAREST)
zone_tex.set_editor_property('never_stream', True)
zone_tex.set_editor_property('address_x', u.TextureAddress.TA_CLAMP); zone_tex.set_editor_property('address_y', u.TextureAddress.TA_CLAMP)
for t in (sat_tex, zone_tex):
    assert u.EditorLoadingAndSavingUtils.save_packages([t.get_outermost()], False)
    saves.append(t.get_outermost().get_name())

# 2. material copy with the satellite blend
mat = u.load_asset(COPY) if u.EditorAssetLibrary.does_asset_exist(COPY) else u.EditorAssetLibrary.duplicate_asset(SHARED, COPY)
assert mat
mma = L.get_material_property_input_node(mat, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
assert mma and mma.get_class().get_name() == 'MaterialExpressionMakeMaterialAttributes'
names = [str(x) for x in L.get_material_expression_input_names(mma)]
orig = L.get_inputs_for_material_expression(mat, mma)[names.index('BaseColor')]
assert orig.get_name() == 'MaterialExpressionLinearInterpolate_2', 'copy already modified: ' + orig.get_name()
orig_out = L.get_input_node_output_name_for_material_expression(mma, orig) if hasattr(L, 'get_input_node_output_name_for_material_expression') else ''
X0, Y0 = -12000, 2600
def node(cls, dx, dy):
    return L.create_material_expression(mat, cls, X0 + dx, Y0 + dy)
wp = node(u.MaterialExpressionWorldPosition, 0, 0)
mask = node(u.MaterialExpressionComponentMask, 250, 0)
for c, v in (('r', True), ('g', True), ('b', False), ('a', False)):
    mask.set_editor_property(c, v)
origin = node(u.MaterialExpressionConstant2Vector, 250, 150)
origin.set_editor_property('r', -HALF_CM); origin.set_editor_property('g', -HALF_CM)
sub = node(u.MaterialExpressionSubtract, 500, 0)
size = node(u.MaterialExpressionScalarParameter, 500, 150)
size.set_editor_property('parameter_name', 'Sat_SizeCm'); size.set_editor_property('default_value', 2 * HALF_CM)
div = node(u.MaterialExpressionDivide, 750, 0)
sat = node(u.MaterialExpressionTextureSampleParameter2D, 1000, 0)
sat.set_editor_property('parameter_name', 'SatelliteColor'); sat.set_editor_property('texture', sat_tex)
sat.set_editor_property('sampler_type', u.MaterialSamplerType.SAMPLERTYPE_COLOR)
weights = node(u.MaterialExpressionConstant3Vector, 1000, 300)
weights.set_editor_property('constant', u.LinearColor(0.3, 0.59, 0.11, 0.0))
dot = node(u.MaterialExpressionDotProduct, 1250, 300)
mid = node(u.MaterialExpressionScalarParameter, 1250, 450)
mid.set_editor_property('parameter_name', 'Sat_DetailMid'); mid.set_editor_property('default_value', 0.35)
ddiv = node(u.MaterialExpressionDivide, 1500, 300)
mul = node(u.MaterialExpressionMultiply, 1750, 0)
blend = node(u.MaterialExpressionScalarParameter, 1750, 300)
blend.set_editor_property('parameter_name', 'Sat_Blend'); blend.set_editor_property('default_value', 0.8)
lerp = node(u.MaterialExpressionLinearInterpolate, 2000, 0)
C = L.connect_material_expressions
assert C(wp, '', mask, '')
assert C(mask, '', sub, 'A') and C(origin, '', sub, 'B')
assert C(sub, '', div, 'A') and C(size, '', div, 'B')
assert C(div, '', sat, 'UVs')
assert C(orig, orig_out, dot, 'A') and C(weights, '', dot, 'B')
assert C(dot, '', ddiv, 'A') and C(mid, '', ddiv, 'B')
assert C(sat, 'RGB', mul, 'A') and C(ddiv, '', mul, 'B')
assert C(orig, orig_out, lerp, 'A') and C(mul, '', lerp, 'B') and C(blend, '', lerp, 'Alpha')
assert C(lerp, '', mma, 'BaseColor')
check = L.get_inputs_for_material_expression(mat, mma)[names.index('BaseColor')]
assert check == lerp, check
L.recompile_material(mat)
assert u.EditorLoadingAndSavingUtils.save_packages([mat.get_outermost()], False)
saves.append(COPY)

# 3. area MI -> copy
mi = u.load_asset(MI)
old_parent = mi.get_editor_property('parent').get_path_name()
L.set_material_instance_parent(mi, mat)
L.set_material_instance_texture_parameter_value(mi, 'SatelliteColor', sat_tex)
L.update_material_instance(mi)
assert mi.get_editor_property('parent') == mat
assert u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)
saves.append(MI)
assert sha(native(SHARED)) == shared_before, 'Shared master changed'
d = dirty()
receipt = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'saves': saves,
           'mi_parent_before': old_parent, 'mi_parent_after': COPY, 'orig_basecolor_node': orig.get_name(), 'orig_output': orig_out,
           'parameters': {'Sat_Blend': 0.8, 'Sat_DetailMid': 0.35, 'Sat_SizeCm': 2 * HALF_CM, 'origin_cm': [-HALF_CM, -HALF_CM]},
           'shared_master_unchanged': True, 'dirty_after': d,
           'files': {p: sha(native(p)) for p in saves}}
(TASK / 'receipts').mkdir(exist_ok=True)
(TASK / 'receipts' / 'GROUND_SATELLITE.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
RESULT = {'ok': True, **receipt}
