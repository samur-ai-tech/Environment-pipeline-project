"""In-editor on the 4 km PCG clone (Karmei Yosef operator, 2026-10-10). Aviv: "every field from the screenshot" + "Yes, build it".
Places the field vegetation/structures from Staging/PazFarm_2026-10-08/Fields_2026-10-10/FIELD_PLANTS_V1.json and builds road 44
as an asphalt strip from ROAD44.json (OSM trunk). New actors/packages only; nothing shared is edited.
steps
  probe          read-only: greenhouse tunnel bounds/pivot, AsphaltMat material instances, farm meshes in PazFarm_Detail
  remove_old     destroy PazFarm_Extension (the scrapped road-to-road parcel crops)
  place          actors (Static chains, landscape-only heights): KY4_Fields_Orchards (orchard + young rows: same Astra meshes as
                 PazFarm_Detail), KY4_Fields_Crops (low crop stand-ins), KY4_Fields_Weeds (weed tufts + margin shrubs),
                 KY4_Fields_Greenhouses (Astra greenhouse tunnels, oriented along the field rows)
  road44         mesh <clone>/Roads/SM_KY4_Road44 (quads every 4 m, both edges draped on the landscape + 12 cm, UV in 4 m tiles)
                 + actor KY4_Road44 with ARGS.material (default MI_AsphaltMat_Inst1)
Undo: delete the KY4_Fields_* / KY4_Road44 actors (and <clone>/Roads). Map saved by pcg_finish.py. ARGS: expected_pid, step [, material].
"""
import datetime, json, math, os
from collections import Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
GEO = ROOT / 'Staging/PazFarm_2026-10-08/Georef'
FLD = ROOT / 'Staging/PazFarm_2026-10-08/Fields_2026-10-10'
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
CLONE = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial' + ARGS.get('clone_suffix', '')     # '_v2' = rebuilt clone
PN = '/Game/ProceduralNtr_vol2/pnp_v2_assets/Assets/'
STF = '/Game/STF/Pack03-LandscapePro/Environment/Foliage/'
PP = '/Game/Palms_Pack_01/Add_Props/'
GREEN = [PN + 'grass/Static_Meshes/green_grass_patch_tall_01', PN + 'grass/Static_Meshes/grass_patch_01']
WEED = [STF + 'GrassBush/SM_grass_bush0%d_lod00' % i for i in (1, 2, 3, 4)]
SHRUB = [PP + 'Thicket/Meshes/SM_Thicket_01_G', PP + 'Thicket/Meshes/SM_Thicket_02_G', PN + 'eldeberry_bushes/Static_Meshes/Elderberry_Living_Medium', STF + 'Bush/SM_bush01']
TUNNEL = TRIAL + '/PazFarm/Meshes/SM_PazFarm_Greenhouse_Tunnel_9x4'
ROADS = TRIAL + '/Roads'
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
XY = lambda e, n: ((pe + e) * 100.0, -(pn + n) * 100.0)
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
labelled = lambda lab: [a for a in eas.get_all_level_actors() if a.get_actor_label() == lab]
misses = Counter()


def ground(x, y):
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0),
                                            u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], u.DrawDebugTrace.NONE, True)
    h = hit[1] if isinstance(hit, tuple) else hit
    t = h.to_tuple() if h is not None else None
    if not t or not t[0]:
        misses['no_hit'] += 1; return None
    act = t[9] if len(t) > 9 else None
    if act is None or not isinstance(act, (u.Landscape, u.LandscapeProxy)):
        misses['not_landscape:' + (act.get_class().get_name() if act else 'None')] += 1; return None
    return t[4].z


def static_actor(label, folder, at):
    assert not labelled(label), label + ' exists'
    actor = eas.spawn_actor_from_class(u.Actor, at)
    actor.set_actor_label(label); actor.set_folder_path(folder)
    sds = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    top = sds.k2_gather_subobject_data_for_instance(actor)[0]
    h, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=top, new_class=u.SceneComponent))
    root = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(h))
    comps = {}

    def comp_for(mesh):
        key = mesh.get_path_name()
        if key not in comps:
            hh, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=h, new_class=u.HierarchicalInstancedStaticMeshComponent))
            c = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(hh))
            c.set_static_mesh(mesh)
            comps[key] = c
        return comps[key]
    return actor, comp_for, comps


def make_static(actor):
    actor.modify()
    rootc = actor.root_component
    cs = [rootc] + [c for c in actor.get_components_by_class(u.SceneComponent) if c != rootc]
    for c in cs:
        if c is not None and not isinstance(c, u.BillboardComponent):
            c.modify(); c.set_mobility(u.ComponentMobility.STATIC)
    for c in cs[1:]:
        if c.get_attach_parent() is None and not isinstance(c, u.BillboardComponent):
            c.attach_to_component(rootc, '', u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, False)
    return sum(1 for c in cs[1:] if c.get_attach_parent() is None and not isinstance(c, u.BillboardComponent))


def farm_meshes():
    det = labelled('PazFarm_Detail')[0]
    return {c.get_editor_property('static_mesh').get_name(): c.get_editor_property('static_mesh')
            for c in det.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent) if c.get_editor_property('static_mesh')}


if step == 'probe':
    t = u.load_asset(TUNNEL); b = t.get_bounding_box()
    RESULT = {'ok': True, 'tunnel_bounds_cm': [[round(b.min.x), round(b.min.y), round(b.min.z)], [round(b.max.x), round(b.max.y), round(b.max.z)]],
              'tunnel_materials': [m.get_editor_property('material_interface').get_path_name() if m.get_editor_property('material_interface') else None for m in t.get_editor_property('static_materials')],
              'asphalt_mis': sorted(a.split('.')[0] for a in u.EditorAssetLibrary.list_assets('/Game/AsphaltMat/Materials', False, False)),
              'farm_meshes': {k: v.get_path_name().split('.')[0] for k, v in farm_meshes().items()}}

elif step == 'remove_old':
    gone = []
    for a in labelled('PazFarm_Extension'):
        eas.destroy_actor(a); gone.append('PazFarm_Extension')
    RESULT = {'ok': True, 'removed': gone, 'dirty': dirty()}

elif step == 'place':
    P = json.loads((FLD / ARGS.get('plants', 'FIELD_PLANTS_V1.json')).read_text())
    V4 = TRIAL + '/PazFarm/FieldCrops_v004/Meshes/'
    fm = farm_meshes()
    pick = lambda base: [m for n, m in fm.items() if n == base or n.startswith(base)][0]
    tb = u.load_asset(TUNNEL).get_bounding_box()
    tunnel_yaw_offset = 90.0 if (tb.max.y - tb.min.y) > (tb.max.x - tb.min.x) else 0.0      # lay the 9 m side along the row
    groups = {'orchard': 'KY4_Fields_Orchards', 'rows': 'KY4_Fields_Orchards', 'olive': 'KY4_Fields_Orchards', 'vine': 'KY4_Fields_Vines',
              'crop': 'KY4_Fields_Crops', 'weed': 'KY4_Fields_Weeds', 'grass': 'KY4_Fields_Weeds', 'patch': 'KY4_Fields_Weeds',
              'margin': 'KY4_Fields_Weeds', 'greenhouse': 'KY4_Fields_Greenhouses'}
    batches = {}
    rnd = [0]
    def choose(lst):
        rnd[0] = (rnd[0] * 1103515245 + 12345) & 0x7fffffff
        return lst[rnd[0] % len(lst)]
    for kind, mesh, e, n, yaw, sc in P['items']:
        x, y = XY(e, n); z = ground(x, y)
        if z is None:
            continue
        if mesh.startswith('V4:'):
            m = u.load_asset(V4 + mesh[3:]); assert m, mesh
        elif kind in ('orchard', 'rows'):
            m = pick(mesh)
        elif kind == 'crop':
            m = u.load_asset(choose(GREEN))
        elif kind == 'weed':
            m = u.load_asset(choose(WEED))
        elif kind == 'margin':
            m = u.load_asset(choose(SHRUB))
        else:
            m = u.load_asset(TUNNEL); yaw = yaw + tunnel_yaw_offset
        batches.setdefault(groups[kind], {}).setdefault(m.get_path_name(), []).append(
            u.Transform(location=u.Vector(x, y, z), rotation=u.Rotator(roll=0.0, pitch=0.0, yaw=yaw), scale=u.Vector(sc, sc, sc)))
    out = {}
    for label, per_mesh in batches.items():
        actor, comp_for, comps = static_actor(label, 'Fields', u.Vector(*XY(0, 0), 0.0))
        for path, ts in per_mesh.items():
            comp_for(u.load_asset(path)).add_instances(ts, False, True)
        det = make_static(actor)
        out[label] = {'instances': {p.split('.')[0].rsplit('/', 1)[1]: len(t) for p, t in per_mesh.items()}, 'total': sum(len(t) for t in per_mesh.values()), 'detached': det}
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'actors': out, 'skipped': dict(misses),
           'tunnel_yaw_offset': tunnel_yaw_offset}
    (TASK / 'receipts' / 'FIELDS_PLACE_V1.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec, 'dirty': dirty()}

elif step == 'road44':
    R = json.loads((FLD / 'ROAD44.json').read_text())
    WID = {'trunk': 11.0, 'primary': 9.0, 'trunk_link': 6.0, 'primary_link': 6.0}
    mat = u.load_asset(ARGS.get('material', '/Game/AsphaltMat/Materials/MI_AsphaltMat_Inst1')); assert mat
    path = ROADS + '/SM_KY4_Road44'
    assert not u.EditorAssetLibrary.does_asset_exist(path), path
    others = [a for a in eas.get_all_level_actors() if not isinstance(a, (u.Landscape, u.LandscapeProxy))]

    def land_z(x, y):
        hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0),
                                                u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, others, u.DrawDebugTrace.NONE, True)
        h = hit[1] if isinstance(hit, tuple) else hit
        t = h.to_tuple() if h is not None else None
        return t[4].z if t and t[0] else None
    LIM = 200800.0                                                      # inside the +-201,600 cm landscape
    strips = []
    for w in R['ways']:
        pts = [XY(e, n) for e, n in w['pts']]
        half = WID.get(w['highway'], 9.0) * 50.0
        samp = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            Lg = math.hypot(x1 - x0, y1 - y0)
            k = max(1, int(Lg / 400.0))
            for j in range(k):
                samp.append((x0 + (x1 - x0) * j / k, y0 + (y1 - y0) * j / k))
        samp.append(pts[-1])
        cur = []
        for i, (x, y) in enumerate(samp):
            inside = abs(x) < LIM and abs(y) < LIM
            if not inside:
                if len(cur) > 1:
                    strips.append((cur, half))
                cur = []; continue
            a = samp[max(0, i - 1)]; b = samp[min(len(samp) - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]; Lg = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / Lg, dx / Lg
            l = (x + nx * half, y + ny * half); r = (x - nx * half, y - ny * half)
            zl, zr = land_z(*l), land_z(*r)
            if zl is None or zr is None:
                if len(cur) > 1:
                    strips.append((cur, half))
                cur = []; continue
            cur.append((l, r, zl + 12.0, zr + 12.0))
        if len(cur) > 1:
            strips.append((cur, half))
    assert strips, 'no road 44 samples inside the landscape'
    o = strips[0][0][0][0]; oz = strips[0][0][0][2]
    mesh = u.AssetToolsHelpers.get_asset_tools().create_asset('SM_KY4_Road44', ROADS, u.StaticMesh, None)
    desc = u.StaticMesh.create_static_mesh_description(mesh)
    g = desc.create_polygon_group(); desc.set_polygon_group_material_slot_name(g, 'Asphalt')
    nquads = 0
    for cur, half in strips:
        dist = 0.0
        prev = None
        vrow = []
        for (l, r, zl, zr) in cur:
            if prev is not None:
                cx0, cy0 = (prev[0][0] + prev[1][0]) / 2, (prev[0][1] + prev[1][1]) / 2
                cx1, cy1 = (l[0] + r[0]) / 2, (l[1] + r[1]) / 2
                dist += math.hypot(cx1 - cx0, cy1 - cy0)
            prev = (l, r)
            row = []
            for (p, z, uu) in ((l, zl, 0.0), (r, zr, 2 * half / 400.0)):
                v = desc.create_vertex(); desc.set_vertex_position(v, u.Vector(p[0] - o[0], p[1] - o[1], z - oz))
                vi = desc.create_vertex_instance(v); desc.set_vertex_instance_uv(vi, u.Vector2D(uu, dist / 400.0), 0)
                row.append(vi)
            vrow.append(row)
        for a, b in zip(vrow, vrow[1:]):
            desc.create_triangle(g, [a[0], b[0], a[1]]); desc.create_triangle(g, [a[1], b[0], b[1]]); nquads += 1
    mesh.set_editor_property('static_materials', [u.StaticMaterial(material_interface=mat, material_slot_name='Asphalt')])
    sm_sub = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    bs = sm_sub.get_lod_build_settings(mesh, 0)
    bs.set_editor_property('recompute_normals', True); bs.set_editor_property('recompute_tangents', True); bs.set_editor_property('generate_lightmap_u_vs', False)
    sm_sub.set_lod_build_settings(mesh, 0, bs)
    mesh.build_from_static_mesh_descriptions([desc], False, False)
    assert u.EditorLoadingAndSavingUtils.save_packages([mesh.get_outermost()], False)
    act = eas.spawn_actor_from_object(mesh, u.Vector(o[0], o[1], oz), u.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    act.set_actor_label('KY4_Road44'); act.set_folder_path('Fields')
    act.static_mesh_component.set_mobility(u.ComponentMobility.STATIC)
    RESULT = {'ok': True, 'mesh': path, 'strips': len(strips), 'quads': nquads, 'material': mat.get_path_name(), 'dirty': dirty()}

elif step == 'road44_material':
    mesh = u.load_asset(ROADS + '/SM_KY4_Road44'); mat = u.load_asset(ARGS['material']); assert mesh and mat
    mesh.set_material(0, mat)
    assert u.EditorLoadingAndSavingUtils.save_packages([mesh.get_outermost()], False)
    RESULT = {'ok': True, 'material': mat.get_path_name(), 'dirty': dirty()}
