"""In-editor (Karmei Yosef operator, WP/per-building trial 2026-10-10). Splits the merged generated-shell mesh (floor and roof
slabs, corner closures, door lintels, infills; 598,089 triangles) into one mesh per building, so each Bldg_<osm> actor owns its
whole building. Trial map only; the source mesh in the main area's Bake folder is read, never changed.
Each triangle goes to the building whose footprint (WPTrial/FOOTPRINTS.json, UE cm) contains its centroid, else to the nearest
footprint within 3 m, else to 'unassigned'. Exact positions, UVs and material slots are copied; every triangle gets its own
vertices so the flat slabs and closures keep flat normals after the rebuild.
steps (ARGS.step):
  analyze  read-only: assignment per triangle -> receipts/WPTRIAL_SHELL_ASSIGN.json + per-building counts.
  build    ARGS.start, ARGS.count: create <trial>/Buildings/Shells/SM_Shell_<key> for that slice and attach a 'Shell'
           StaticMeshComponent to the matching Bldg_ actor (a new Bldg_<osm> actor for the unsupported shell / unassigned).
  remove   delete the merged buildings actor from the trial map (the shared asset is untouched).
  verify   triangle totals across shells == source triangles; every Bldg_ has a Shell where triangles were assigned.
ARGS: expected_pid, step, target ('wptrial' | 'clone_v2').
"""
import datetime, json, math, os
from collections import Counter, defaultdict
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
SRC = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/Bake/KarmeiYosef_31850349_34907601_4km_buildings'
# ARGS.target: 'wptrial' (2026-10-10 trial, default) | 'clone_v2' (Aviv 2026-10-11 "Split on the clone now")
TARGET = ARGS.get('target', 'wptrial')
if TARGET == 'wptrial':
    TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial'
    MAP = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_WPTrial'
    OUT, DATA, ASSIGN = TRIAL + '/Buildings/Shells/', TASK / 'WPTrial', TASK / 'receipts' / 'WPTRIAL_SHELL_ASSIGN.json'
    UNSUPPORTED = '1042209923'
else:
    TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
    MAP = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial_v2'
    OUT, DATA, ASSIGN = TRIAL + '/Buildings_v2/Shells/', TASK / 'Buildings_v2', TASK / 'receipts' / 'CLONE_V2_SHELL_ASSIGN.json'
    _uns = json.loads((DATA / 'BUILDINGS_COMPACT.json').read_text(encoding='utf-8'))['unsupported']
    assert len(_uns) == 1, _uns
    UNSUPPORTED = str(_uns[0]['source_osm_id'])
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAP
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']
src = u.load_asset(SRC)
d = src.get_static_mesh_description(0)
NT = d.get_polygon_count()          # every polygon is one triangle here; the polygon getters return clean ids
assert NT == d.get_triangle_count()
V, VI, TR, PG = u.VertexID, u.VertexInstanceID, u.PolygonID, u.PolygonGroupID   # TR = polygon id (get_triangle_vertices returns 3 junk ids first in this build)


def inside(px, py, poly):
    c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i - 1]; x2, y2 = poly[i]
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def seg_dist(px, py, poly):
    best = 1e18
    for i in range(len(poly)):
        x1, y1 = poly[i - 1]; x2, y2 = poly[i]
        dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L))
        best = min(best, math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)))
    return best


if step == 'analyze':
    FP = json.loads((DATA / 'FOOTPRINTS.json').read_text())['footprints_ue_cm']
    keys = sorted(FP); polys = [FP[k] for k in keys]
    CELL = 5000.0
    grid = defaultdict(list)
    for bi, poly in enumerate(polys):
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        for gx in range(int(math.floor((min(xs) - 300) / CELL)), int(math.floor((max(xs) + 300) / CELL)) + 1):
            for gy in range(int(math.floor((min(ys) - 300) / CELL)), int(math.floor((max(ys) + 300) / CELL)) + 1):
                grid[(gx, gy)].append(bi)
    pos = {}
    def P(vid):
        if vid not in pos:
            p = d.get_vertex_position(V(vid)); pos[vid] = (p.x, p.y, p.z)
        return pos[vid]
    assign = []
    how = Counter()
    for t in range(NT):
        vs = [x.id_value for x in d.get_polygon_vertices(TR(t))]
        assert len(vs) == 3, (t, len(vs))
        cx = sum(P(v)[0] for v in vs) / 3.0; cy = sum(P(v)[1] for v in vs) / 3.0
        cand = grid.get((int(math.floor(cx / CELL)), int(math.floor(cy / CELL))), [])
        hit = [bi for bi in cand if inside(cx, cy, polys[bi])]
        if len(hit) == 1:
            assign.append(hit[0]); how['inside'] += 1; continue
        if len(hit) > 1:
            hit.sort(key=lambda bi: seg_dist(cx, cy, polys[bi]), reverse=True)        # deepest inside wins
            assign.append(hit[0]); how['inside_overlap'] += 1; continue
        near = sorted((seg_dist(cx, cy, polys[bi]), bi) for bi in cand)
        if near and near[0][0] <= 300.0:
            assign.append(near[0][1]); how['near'] += 1
        else:
            assign.append(-1); how['unassigned'] += 1
    per = Counter(assign)
    un = [t for t, b in enumerate(assign) if b == -1]
    ub = None
    if un:
        xs = [sum(P(v.id_value)[0] for v in d.get_polygon_vertices(TR(t))) / 3 for t in un]
        ys = [sum(P(v.id_value)[1] for v in d.get_polygon_vertices(TR(t))) / 3 for t in un]
        ub = [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]
    groups = Counter(d.get_polygon_polygon_group(TR(t)).id_value for t in range(0, NT, 1))
    res = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'source': SRC, 'triangles': NT,
           'how': dict(how), 'buildings_with_triangles': len([k for k in per if k >= 0]), 'unassigned_bbox_cm': ub,
           'triangles_per_group': dict(groups), 'keys': keys, 'assign': assign}
    ASSIGN.write_text(json.dumps(res), encoding='utf-8')
    tri_counts = sorted(per[b] for b in per if b >= 0)
    RESULT = {'ok': True, **{k: v for k, v in res.items() if k not in ('assign', 'keys')},
              'tris_per_building_min_med_max': [tri_counts[0], tri_counts[len(tri_counts) // 2], tri_counts[-1]] if tri_counts else None}

elif step == 'build':
    A = json.loads(ASSIGN.read_text())
    keys = A['keys'] + ['unassigned']
    by_b = defaultdict(list)
    for t, b in enumerate(A['assign']):
        by_b[keys[b] if b >= 0 else 'unassigned'].append(t)
    names = sorted(by_b)[ARGS['start']:ARGS['start'] + ARGS['count']]
    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors() if a.get_actor_label().startswith('Bldg_')}
    merged = [a for a in eas.get_all_level_actors() if isinstance(a, u.StaticMeshActor) and a.static_mesh_component.get_editor_property('static_mesh')
              and a.static_mesh_component.get_editor_property('static_mesh').get_path_name().split('.')[0] == SRC]   # by mesh: labels get '_1' after a regeneration
    mats = [merged[0].static_mesh_component.get_material(i) for i in range(len(src.get_editor_property('static_materials')))] if merged else \
           [s.get_editor_property('material_interface') for s in src.get_editor_property('static_materials')]
    slot_names = [s.get_editor_property('material_slot_name') for s in src.get_editor_property('static_materials')]
    trace_flag = src.get_editor_property('body_setup').get_editor_property('collision_trace_flag') if src.get_editor_property('body_setup') else None
    sds = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    made = []
    for key in names:
        osm = UNSUPPORTED if key == 'unassigned' else key
        label = 'Bldg_' + osm
        a = actors.get(label)
        tris = by_b[key]
        pts = [d.get_vertex_position(V(v.id_value)) for t in tris for v in d.get_polygon_vertices(TR(t))]
        if a is None:                                                    # the unsupported shell gets its own building actor
            xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
            a = eas.spawn_actor_from_class(u.Actor, u.Vector((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
            a.set_actor_label(label); a.set_folder_path('Buildings')
            rh = sds.k2_gather_subobject_data_for_instance(a)[0]
            h, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=rh, new_class=u.SceneComponent))
            sds.rename_subobject(h, u.Text('BuildingRoot'))
            rc = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(h))
            rc.set_mobility(u.ComponentMobility.STATIC)
            a.set_actor_location(u.Vector((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)), False, False)
        if [c for c in a.get_components_by_class(u.StaticMeshComponent) if c.get_name().startswith('Shell')]:
            continue
        o = a.get_actor_location()
        path = OUT + 'SM_Shell_' + osm
        # a fresh, never-rendered mesh: rebuilding a duplicated engine Cube in place crashed the editor (render resource
        # deleted without release, 2026-10-09 23:45Z)
        if u.EditorAssetLibrary.does_asset_exist(path):
            continue
        mesh = u.AssetToolsHelpers.get_asset_tools().create_asset('SM_Shell_' + osm, OUT[:-1], u.StaticMesh, None)
        assert mesh, 'create_asset StaticMesh failed for ' + path
        desc = u.StaticMesh.create_static_mesh_description(mesh)
        gmap = {}
        for t in tris:
            g = d.get_polygon_polygon_group(TR(t)).id_value
            if g not in gmap:
                ng = desc.create_polygon_group()
                desc.set_polygon_group_material_slot_name(ng, slot_names[g])
                gmap[g] = ng
            vis = []
            for svi in d.get_polygon_vertex_instances(TR(t)):
                sp = d.get_vertex_position(d.get_vertex_instance_vertex(svi))
                nv = desc.create_vertex(); desc.set_vertex_position(nv, u.Vector(sp.x - o.x, sp.y - o.y, sp.z - o.z))
                nvi = desc.create_vertex_instance(nv)
                desc.set_vertex_instance_uv(nvi, d.get_vertex_instance_uv(svi, 0), 0)
                vis.append(nvi)
            desc.create_triangle(gmap[g], vis)
        used = sorted(gmap)
        mesh.set_editor_property('static_materials', [u.StaticMaterial(material_interface=mats[g], material_slot_name=slot_names[g]) for g in used])
        sm_sub = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        bs = sm_sub.get_lod_build_settings(mesh, 0)
        bs.set_editor_property('recompute_normals', True); bs.set_editor_property('recompute_tangents', True)
        bs.set_editor_property('generate_lightmap_u_vs', False)
        sm_sub.set_lod_build_settings(mesh, 0, bs)
        mesh.build_from_static_mesh_descriptions([desc], False, False)     # full build: fast build skips normal computation
        if trace_flag is not None and mesh.get_editor_property('body_setup'):
            mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', trace_flag)
        root_h = None
        for h in sds.k2_gather_subobject_data_for_instance(a):
            obj = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(h))
            if isinstance(obj, u.SceneComponent) and obj.get_name().startswith('BuildingRoot'):
                root_h = h
        h, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=root_h, new_class=u.StaticMeshComponent))
        sds.rename_subobject(h, u.Text('Shell'))
        c = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(h))
        c.set_mobility(u.ComponentMobility.STATIC)
        c.set_static_mesh(mesh)
        c.set_world_transform(u.Transform(location=o, rotation=u.Rotator(roll=0.0, pitch=0.0, yaw=0.0), scale=u.Vector(1, 1, 1)), False, False)
        made.append([osm, len(tris), mesh.get_num_triangles(0)])
    RESULT = {'ok': True, 'slice': [ARGS['start'], ARGS['count']], 'made': len(made), 'tri_mismatch': [m for m in made if m[1] != m[2]][:20],
              'tris': sum(m[1] for m in made)}

elif step == 'materials_check':
    # read-only: merged actor's per-slot materials vs the source mesh's own slot materials (build falls back to the latter)
    merged = [a for a in eas.get_all_level_actors() if isinstance(a, u.StaticMeshActor) and a.static_mesh_component.get_editor_property('static_mesh')
                  and a.static_mesh_component.get_editor_property('static_mesh').get_path_name().split('.')[0] == SRC]   # by mesh: labels get '_1' after a regeneration
    assert len(merged) == 1, [a.get_actor_label() for a in merged]
    sm = src.get_editor_property('static_materials')
    pairs = [[str(sm[i].get_editor_property('material_slot_name')), merged[0].static_mesh_component.get_material(i).get_path_name().split('.')[0],
              sm[i].get_editor_property('material_interface').get_path_name().split('.')[0]] for i in range(len(sm))]
    RESULT = {'ok': True, 'same': all(p[1] == p[2] for p in pairs), 'slots': pairs}

elif step == 'remove':
    merged = [a for a in eas.get_all_level_actors() if isinstance(a, u.StaticMeshActor) and a.static_mesh_component.get_editor_property('static_mesh')
              and a.static_mesh_component.get_editor_property('static_mesh').get_path_name().split('.')[0] == SRC]   # by mesh: labels get '_1' after a regeneration
    assert len(merged) == 1, [a.get_actor_label() for a in merged]
    lab = merged[0].get_actor_label()
    assert eas.destroy_actor(merged[0])
    RESULT = {'ok': True, 'removed_actor': lab, 'shared_asset_untouched': SRC}

elif step == 'verify':
    tot = 0; shells = 0; missing = []
    for a in eas.get_all_level_actors():
        if not a.get_actor_label().startswith('Bldg_'):
            continue
        sh = [c for c in a.get_components_by_class(u.StaticMeshComponent) if c.get_name().startswith('Shell')]
        if sh:
            shells += 1; tot += sh[0].get_editor_property('static_mesh').get_num_triangles(0)
    A = json.loads(ASSIGN.read_text())
    RESULT = {'ok': tot == NT, 'shell_triangles': tot, 'source_triangles': NT, 'buildings_with_shell': shells,
              'expected_shells': len({b for b in A['assign']})}
