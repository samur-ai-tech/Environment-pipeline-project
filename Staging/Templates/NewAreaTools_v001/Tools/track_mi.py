"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat track_mi.py (tracks as dirt surfaces;
fork of road_mi.py). The area-owned track material instance E.TRACK_MI (area_constants.py TRACK_MI,
<root>/Materials/MI_RoadTrack_<AREA_SHORT>_v001; E = hda_edits.py loaded from its file), child of the area road master
E.TRACK_MI_PARENT (ROAD_MASTER, M_RoadAsphalt_<AREA_SHORT>_v001), created once
with MaterialInstanceConstantFactoryNew as road_mi.py does, then MI parameter values only (no graph edit). The generator
module's default 'track' route material is this exact path (hda_edits.py edit T); if it does not load, the Houdini Engine bake falls back silently to its
default material, so the MI must exist and be saved by name before the run.
Texture overrides (ARGS.textures may override any of these five; nothing else):
  BaseColorTex Namaqualand T_sandy_gravel_02_diff_4k, NormalTex T_sandy_gravel_02_nor_dx_4k, RoughnessTex and AOTex
  ScansMatter T_White, HeightTex Modular_Rural_Cabin Sand_height (the TextureObjectParameter that TextureVariation samples).
Checks BEFORE any change (also before the MI is created); any failure refuses with no MI change:
  - every texture exists, is a Texture, has virtual_texture_streaming False, and needs (sampler_for(), the same table as
    build_road_material.py) exactly the sampler type of the parent's parameter expression;
  - the parent's sampler types equal the build_road_material.py build (its CLIENT_ receipt): BaseColorTex COLOR,
    NormalTex NORMAL, RoughnessTex/AOTex/HeightTex LINEAR_GRAYSCALE;
  - every texture/scalar/vector name exists on the parent; an existing MI is a MaterialInstanceConstant of that parent.
Then scalars (ARGS.scalars over the defaults TileSizeM 2.75, DustAmount 0.35, Brightness 1.1, NormalStrength 0.8,
RoughnessMult 0.9) and vectors (ARGS.vectors over DustColor linear [0.571, 0.275, 0.091], set raw as road_mi.py does),
update_material_instance, and a readback of every value (textures as paths). Static switches are never read (reading them
dirties the MI). No save here (save_prefix on <root>/Materials/, the MI path only).
ARGS: expected_pid, script_file (client), textures (optional), scalars (optional), vectors (optional), dry (optional: checks
only, no MI change). The texture defaults below are the El Wahat 'Sandy gravel' set; pass ARGS.textures for another ground."""
import importlib.util, os, sys
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('hda_edits', TOOLS.parent / 'hda_edits.py')
E = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(E)  # generator constants, read from the file at each call
TASK = E.A.task_dir(TOOLS, ROOT)
assert Path(E.__file__).resolve().parent == TASK, ('generator constants loaded from elsewhere', E.__file__)
L, EA, ST = u.MaterialEditingLibrary, u.EditorAssetLibrary, u.MaterialSamplerType
MI, OBJ = E.TRACK_MI.split('.')
FOLDER, NAME = MI.rsplit('/', 1)
assert NAME == OBJ == E.A.TRACK_MI_NAME, E.TRACK_MI
TEXTURES = {'BaseColorTex': '/Game/Namaqualand/Textures/T_sandy_gravel_02_diff_4k',
            'NormalTex': '/Game/Namaqualand/Textures/T_sandy_gravel_02_nor_dx_4k',
            'RoughnessTex': '/Game/SM_Concrete_07/ScansMatter_Master/Textures/Defaults/T_White',
            'AOTex': '/Game/SM_Concrete_07/ScansMatter_Master/Textures/Defaults/T_White',
            'HeightTex': '/Game/Modular_Rural_Cabin/Textures/Tiling/Sand_height'}
# the parent's sampler per parameter as built; HeightTex is the TextureObjectParameter TextureVariation samples linear grayscale
PARENT_SAMPLERS = {'BaseColorTex': ST.SAMPLERTYPE_COLOR, 'NormalTex': ST.SAMPLERTYPE_NORMAL,
                   'RoughnessTex': ST.SAMPLERTYPE_LINEAR_GRAYSCALE, 'AOTex': ST.SAMPLERTYPE_LINEAR_GRAYSCALE,
                   'HeightTex': ST.SAMPLERTYPE_LINEAR_GRAYSCALE}
SCALARS = {'TileSizeM': 2.75, 'DustAmount': 0.35, 'Brightness': 1.1, 'NormalStrength': 0.8, 'RoughnessMult': 0.9}
VECTORS = {'DustColor': [0.571, 0.275, 0.091]}            # linear = sRGB(199, 143, 85)


def sampler_for(t):                                       # same table as build_road_material.py
    cs = t.get_editor_property('compression_settings')
    srgb = t.get_editor_property('srgb')
    if cs == u.TextureCompressionSettings.TC_NORMALMAP:
        return ST.SAMPLERTYPE_NORMAL
    if cs == u.TextureCompressionSettings.TC_GRAYSCALE:
        return ST.SAMPLERTYPE_GRAYSCALE if srgb else ST.SAMPLERTYPE_LINEAR_GRAYSCALE
    if cs == u.TextureCompressionSettings.TC_MASKS:
        return ST.SAMPLERTYPE_MASKS
    return ST.SAMPLERTYPE_COLOR if srgb else ST.SAMPLERTYPE_LINEAR_COLOR


unknown = sorted(set(ARGS.get('textures') or {}) - set(TEXTURES))
assert not unknown, ('ARGS.textures names outside the five track texture parameters', unknown)
tex_paths = dict(TEXTURES, **(ARGS.get('textures') or {}))
scalars = dict(SCALARS, **{n: float(v) for n, v in (ARGS.get('scalars') or {}).items()})
vectors = dict(VECTORS, **{n: [float(x) for x in v] for n, v in (ARGS.get('vectors') or {}).items()})
assert all(len(v) == 3 for v in vectors.values()), ('vectors are linear [r, g, b]', vectors)
dirty_before = sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
# ---- checks: nothing below changes anything until 'fail' is empty --------------------------------------------------------
fail = []
parent = u.load_asset(E.TRACK_MI_PARENT)
assert isinstance(parent, u.Material), ('parent master missing or not a Material', E.TRACK_MI_PARENT)
parent_samplers = {}
for e in L.get_material_expressions(parent):              # read-only (GroundFix/GroundPainting readers use the same call)
    if isinstance(e, (u.MaterialExpressionTextureSampleParameter2D, u.MaterialExpressionTextureObjectParameter)):
        parent_samplers.setdefault(str(e.get_editor_property('parameter_name')), []).append(e.get_editor_property('sampler_type'))
names_t = [str(n) for n in L.get_texture_parameter_names(parent)]
names_s = [str(n) for n in L.get_scalar_parameter_names(parent)]
names_v = [str(n) for n in L.get_vector_parameter_names(parent)]
textures, checks = {}, {}
for k in sorted(tex_paths):
    path, want = tex_paths[k], PARENT_SAMPLERS[k]
    ps = parent_samplers.get(k, [])
    row = {'path': path, 'parent_sampler': [str(s) for s in ps], 'expected_parent_sampler': str(want)}
    if k not in names_t:
        fail.append('%s: not a texture parameter of the parent' % k)
    if not ps or any(s != want for s in ps):
        fail.append('%s: parent sampler %s is not the built %s' % (k, row['parent_sampler'], want))
    t = u.load_asset(path) if EA.does_asset_exist(path) else None
    if not isinstance(t, u.Texture):
        fail.append('%s: texture missing or not a Texture: %s' % (k, path))
    else:
        textures[k] = t
        vt, need = t.get_editor_property('virtual_texture_streaming'), sampler_for(t)
        row.update(compression=str(t.get_editor_property('compression_settings')), srgb=bool(t.get_editor_property('srgb')),
                   virtual_texture_streaming=vt, sampler_needed=str(need))
        if vt is not False:
            fail.append('%s: virtual_texture_streaming is %r (the parent samplers are not virtual): %s' % (k, vt, path))
        if need != want:
            fail.append('%s: %s needs %s, the parent parameter samples %s' % (k, path, need, want))
    checks[k] = row
fail += ['scalar %s: not a parameter of the parent' % n for n in scalars if n not in names_s]
fail += ['vector %s: not a parameter of the parent' % n for n in vectors if n not in names_v]
existing = EA.does_asset_exist(MI)
mi = u.load_asset(MI) if existing else None
if existing and not isinstance(mi, u.MaterialInstanceConstant):
    fail.append('existing %s is not a MaterialInstanceConstant' % MI)
elif existing:
    was = mi.get_editor_property('parent')
    if was is None or was.get_path_name().split('.')[0] != E.TRACK_MI_PARENT:
        fail.append('existing %s has parent %s, not %s' % (MI, was.get_path_name() if was else None, E.TRACK_MI_PARENT))
if fail or ARGS.get('dry'):
    RESULT = {'ok': not fail, 'refused': fail or None, 'dry': bool(ARGS.get('dry')), 'mi': MI, 'mi_exists': existing,
              'parent': E.TRACK_MI_PARENT, 'checks': checks, 'scalars_requested': scalars, 'vectors_requested': vectors,
              'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
              'dirty_content_before': dirty_before}
else:
    # ---- change: create once, then parameter values only ----------------------------------------------------------------
    created = False
    if not existing:
        mi = u.AssetToolsHelpers.get_asset_tools().create_asset(NAME, FOLDER, u.MaterialInstanceConstant,
                                                                u.MaterialInstanceConstantFactoryNew())
        assert mi, 'create_asset MaterialInstanceConstant failed for ' + MI
        L.set_material_instance_parent(mi, parent)
        created = True
    assert mi.get_editor_property('parent').get_path_name().split('.')[0] == E.TRACK_MI_PARENT
    for k in sorted(textures):
        # the texture setter returns False in this build even when the value is set (measured 14:48Z: AOTex read back as
        # T_White after a False return); the readback below is the check
        L.set_material_instance_texture_parameter_value(mi, k, textures[k])
    for n, v in sorted(scalars.items()):
        L.set_material_instance_scalar_parameter_value(mi, n, v)            # return value unreliable here, as road_mi.py
    for n, v in sorted(vectors.items()):
        L.set_material_instance_vector_parameter_value(mi, n, u.LinearColor(v[0], v[1], v[2], 1.0))
    L.update_material_instance(mi)
    # ---- readback of every value ---------------------------------------------------------------------------------------
    tex_now = {}
    for k in sorted(tex_paths):
        t = L.get_material_instance_texture_parameter_value(mi, k)
        tex_now[k] = t.get_path_name() if t else None
    sc_now = {n: round(L.get_material_instance_scalar_parameter_value(mi, n), 4) for n in names_s}
    vec_now = {}
    for n in names_v:
        col = L.get_material_instance_vector_parameter_value(mi, n)
        vec_now[n] = [round(col.r, 4), round(col.g, 4), round(col.b, 4), round(col.a, 4)]
    mismatch = [['texture', k, tex_paths[k], tex_now[k]] for k in sorted(tex_paths)
                if (tex_now[k] or '').split('.')[0] != tex_paths[k].split('.')[0]]
    mismatch += [['scalar', n, v, sc_now.get(n)] for n, v in sorted(scalars.items()) if abs(sc_now.get(n, 1e9) - v) > 1e-4]
    mismatch += [['vector', n, v, vec_now.get(n)] for n, v in sorted(vectors.items())
                 if any(abs(a - b) > 1e-4 for a, b in zip(vec_now.get(n, [1e9] * 3), v))]
    RESULT = {'ok': not mismatch, 'mismatch': mismatch, 'mi': MI, 'object_path': E.TRACK_MI, 'created': created,
              'parent': mi.get_editor_property('parent').get_path_name(), 'checks': checks,
              'textures': tex_now, 'scalars': {n: sc_now[n] for n in sorted(scalars)}, 'vectors': {n: vec_now[n] for n in sorted(vectors)},
              'scalars_all': sc_now, 'vectors_all': vec_now,
              'dirty_maps': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
              'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
              'dirty_content_before': dirty_before, 'next': 'save_prefix on ' + FOLDER + '/ (this MI path only), then gc_probe'}
