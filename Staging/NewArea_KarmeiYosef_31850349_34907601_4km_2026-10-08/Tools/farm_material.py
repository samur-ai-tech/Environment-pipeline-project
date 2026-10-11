"""In-editor (Karmei Yosef operator), no map loaded, 2026-10-08. Reversible Paz Farm ground layer (Aviv: "rebuild each plot,
but make it reversible"). Imports T_PazFarm_Ground (RGBA, sRGB, clamp) into <area>/Materials/Zones and adds to this
area's own M_GeoCityAuto_KY4, after the satellite blend and before MakeMaterialAttributes.BaseColor:
   uv = (WorldPosition.xy - (Farm_OriginX, Farm_OriginY)) / Farm_SizeCm
   out = lerp(previous, FarmColor.rgb * detail, FarmColor.a * Farm_Blend)       (detail = the satellite branch's detail term)
Farm_Blend defaults to 0, so the main 4 km map looks exactly as before; the PCG clone switches it on in its own child MI.
Undo: Farm_Blend = 0 (or remove the clone's MI). Named saves: texture + material copy only. ARGS: expected_pid, origin_x, origin_y, size_cm, texture_png.
"""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
AREA = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015'
MAT = AREA + '/Materials/M_GeoCityAuto_KY4'
TEX = AREA + '/Materials/Zones/T_PazFarm_Ground'
L = u.MaterialEditingLibrary
pid = os.getpid(); assert pid == ARGS['expected_pid']
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
assert dirty() == ([], []), dirty()
assert not u.EditorAssetLibrary.does_asset_exist(TEX)
t = u.AssetImportTask()
for k, v in dict(filename=ARGS['texture_png'], destination_path=TEX.rsplit('/', 1)[0], destination_name='T_PazFarm_Ground', automated=True, replace_existing=False, save=False).items():
    t.set_editor_property(k, v)
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
tex = list(t.get_objects())[0]
tex.set_editor_property('srgb', True)
tex.set_editor_property('address_x', u.TextureAddress.TA_CLAMP); tex.set_editor_property('address_y', u.TextureAddress.TA_CLAMP)
assert u.EditorLoadingAndSavingUtils.save_packages([tex.get_outermost()], False)
mat = u.load_asset(MAT)
mma = L.get_material_property_input_node(mat, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
names = [str(x) for x in L.get_material_expression_input_names(mma)]
prev = L.get_inputs_for_material_expression(mat, mma)[names.index('BaseColor')]
assert prev.get_class().get_name() == 'MaterialExpressionLinearInterpolate', prev.get_class().get_name()
lerp_inputs = L.get_inputs_for_material_expression(mat, prev)           # A=orig, B=sat*detail, Alpha=Sat_Blend
mul = lerp_inputs[1]
assert mul.get_class().get_name() == 'MaterialExpressionMultiply', mul.get_class().get_name()
detail = L.get_inputs_for_material_expression(mat, mul)[1]
assert detail.get_class().get_name() == 'MaterialExpressionDivide', detail.get_class().get_name()
X0, Y0 = -12000, 3400
node = lambda cls, dx, dy: L.create_material_expression(mat, cls, X0 + dx, Y0 + dy)
def scalar(name, value, dx, dy):
    s = node(u.MaterialExpressionScalarParameter, dx, dy); s.set_editor_property('parameter_name', name); s.set_editor_property('default_value', value); return s
wp = node(u.MaterialExpressionWorldPosition, 0, 0)
mask = node(u.MaterialExpressionComponentMask, 250, 0)
for c, v in (('r', True), ('g', True), ('b', False), ('a', False)):
    mask.set_editor_property(c, v)
ox = scalar('Farm_OriginX', float(ARGS['origin_x']), 250, 150); oy = scalar('Farm_OriginY', float(ARGS['origin_y']), 250, 300)
app = node(u.MaterialExpressionAppendVector, 500, 200)
sub = node(u.MaterialExpressionSubtract, 750, 0)
size = scalar('Farm_SizeCm', float(ARGS['size_cm']), 750, 200)
div = node(u.MaterialExpressionDivide, 1000, 0)
farm = node(u.MaterialExpressionTextureSampleParameter2D, 1250, 0)
farm.set_editor_property('parameter_name', 'FarmColor'); farm.set_editor_property('texture', tex)
farm.set_editor_property('sampler_type', u.MaterialSamplerType.SAMPLERTYPE_COLOR)
fmul = node(u.MaterialExpressionMultiply, 1500, 0)
blend = scalar('Farm_Blend', 0.0, 1500, 250)
amul = node(u.MaterialExpressionMultiply, 1750, 200)
lerp = node(u.MaterialExpressionLinearInterpolate, 2000, 0)
C = L.connect_material_expressions
assert C(wp, '', mask, '') and C(ox, '', app, 'A') and C(oy, '', app, 'B')
assert C(mask, '', sub, 'A') and C(app, '', sub, 'B') and C(sub, '', div, 'A') and C(size, '', div, 'B')
assert C(div, '', farm, 'UVs') and C(farm, 'RGB', fmul, 'A') and C(detail, '', fmul, 'B')
assert C(farm, 'A', amul, 'A') and C(blend, '', amul, 'B')
assert C(prev, '', lerp, 'A') and C(fmul, '', lerp, 'B') and C(amul, '', lerp, 'Alpha')
assert C(lerp, '', mma, 'BaseColor')
assert L.get_inputs_for_material_expression(mat, mma)[names.index('BaseColor')] == lerp
L.recompile_material(mat)
assert u.EditorLoadingAndSavingUtils.save_packages([mat.get_outermost()], False)
sha = lambda pkg: hashlib.sha256((ROOT / ('Content/' + pkg[6:] + '.uasset')).read_bytes()).hexdigest()
receipt = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'saves': [TEX, MAT],
           'params': {'Farm_OriginX': ARGS['origin_x'], 'Farm_OriginY': ARGS['origin_y'], 'Farm_SizeCm': ARGS['size_cm'], 'Farm_Blend_default': 0.0},
           'undo': 'set Farm_Blend to 0 in the clone MI (the main area MI keeps the default 0)', 'dirty_after': dirty(),
           'files': {p: sha(p) for p in (TEX, MAT)}}
(TASK / 'receipts' / 'FARM_MATERIAL.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
RESULT = {'ok': True, **receipt}
