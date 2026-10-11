"""Independent, read-only Blender source/FBX checks for StrawberryBeds v005.

Run from a fresh --background --factory-startup process. Only validation* reports
are written. Intentional open bed ends, film holes and skirt hems are distinguished
from accidentally open solid leaves; no producer validation result is trusted.
"""
import bpy
import numpy as np
import sys, json, math, hashlib, traceback
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict
from mathutils import Vector, Matrix
from mathutils.geometry import convex_hull_2d
from mathutils.kdtree import KDTree

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PROBE_MODE = 'evaluated_normals' if '--probe-evaluated-normals' in sys.argv else ('untriangulated' if '--probe-untriangulated' in sys.argv else None)
IS_DRAFT = '--draft' in sys.argv or '--only-a' in sys.argv or PROBE_MODE is not None
REPORT = ROOT / 'Reports' / ('validation_probe_'+PROBE_MODE+'.json' if PROBE_MODE else ('validation_v005_draft.json' if IS_DRAFT else 'validation_v005.json'))
TOL = 1e-4
WELD_TOL = 1e-6
AREA_EPS = 1e-12
UV_AREA_EPS = 1e-14
PREFIX = 'SM_PazFarm_StrawberryBed_4m_'
SOLID_ROLES = {'leaf', 'petiole', 'soil_clod', 'planting_hole_soil', 'drip_tape'}
OUT = {
    'phase': 'draft_diagnostic_not_acceptance' if IS_DRAFT else 'final_frozen_inputs',
    'method': 'Fresh Blender process: reopen source without scripts, measure actual mesh and material data, then clear scene and import each FBX independently. Imported triangles are mapped to source polygons by geometry and material; exact polygon coverage permits legal alternate diagonals while preserving per-corner attributes.',
    'blender': bpy.app.version_string,
    'generated_utc': datetime.now(timezone.utc).isoformat(),
    'tolerances': {'metres': TOL, 'geometric_weld_metres': WELD_TOL,
                   'zero_triangle_area_m2': AREA_EPS, 'zero_uv_triangle_area': UV_AREA_EPS},
    'source': {}, 'assets': [], 'joins': [], 'cross_lod_joins': [], 'endcap_joins': [],
    'slope_proof': {}, 'failures': [], 'warnings': [],
    'limits': ['Offline asset verification only; no Unreal or HLOD operation.',
               'Source/FBX congruence does not establish photographic realism or native appearance.',
               'Analytical planar-slope placements do not prove conformity to arbitrary terrain.'],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fbx_global_settings(path, name):
    from io_scene_fbx import parse_fbx
    from io_scene_fbx.fbx_utils import RIGHT_HAND_AXES
    tree,version=parse_fbx.parse(str(path))
    glob=next(e for e in tree.elems if e.id==b'GlobalSettings')
    props=next(e for e in glob.elems if e.id==b'Properties70')
    wanted={'UpAxis','UpAxisSign','FrontAxis','FrontAxisSign','CoordAxis','CoordAxisSign','UnitScaleFactor','OriginalUnitScaleFactor'}
    values={e.props[0].decode():e.props[4] for e in props.elems if e.id==b'P' and e.props[0].decode() in wanted}
    expected=RIGHT_HAND_AXES[('Z','-Y')]
    observed=tuple((values.get(a+'Axis'),values.get(a+'AxisSign')) for a in ['Up','Front','Coord'])
    if observed!=expected:fail(name,'FBX header does not encode -Y forward / Z up')
    if abs(values.get('UnitScaleFactor',0)-100)>1e-6:fail(name,'FBX header does not declare metre units (100 centimetres)')
    return {'version':version,**values,'expected_forward':'-Y','expected_up':'Z','axis_header_matches':observed==expected}


def fail(label, message):
    OUT['failures'].append(f'{label}: {message}')


def warn(label, message):
    OUT['warnings'].append(f'{label}: {message}')


def json_value(value, default):
    if value is None:
        return default
    if isinstance(value, str):
        return json.loads(value)
    if hasattr(value, 'to_list'):
        return value.to_list()
    return value


def segment_distance(point, a, b):
    point, a, b = np.asarray(point), np.asarray(a), np.asarray(b)
    d = b-a
    t = float(np.dot(point-a, d) / np.dot(d, d)) if np.dot(d, d) > 1e-20 else 0.
    return float(np.linalg.norm(point-(a+min(1., max(0., t))*d)))


def profile_gap(left, right):
    """Symmetric polyline distance, with midpoint probes to catch shape changes."""
    if not left or not right:
        return None
    def directed(a, b):
        return max(min(segment_distance(p, c, d) for c, d in b)
                   for v, w in a for p in (v, w, (np.array(v)+np.array(w))*.5))
    return max(directed(left, right), directed(right, left))


def edge_counts(triangles):
    edges = Counter()
    for tri in triangles:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges[tuple(sorted((int(a), int(b))))] += 1
    return edges


def oriented_boundary(faces):
    counts=Counter()
    for face in faces:
        for i,a in enumerate(face):
            b=face[(i+1)%len(face)];edge=tuple(sorted((int(a),int(b))))
            counts[edge]+=1 if int(a)<int(b) else -1
    return {edge:n for edge,n in counts.items() if n}


def component_stats(tri_ids, canonical_points):
    counts = edge_counts(tri_ids)
    return {'triangles': len(tri_ids), 'boundary_edges': sum(v == 1 for v in counts.values()),
            'nonmanifold_edges': sum(v > 2 for v in counts.values())}


def get_ranges(obj):
    ranges = json_value(obj.get('component_ranges'), [])
    if isinstance(ranges, dict):
        ranges = ranges.get('components', ranges.get('ranges', []))
    return list(ranges)


def canonical_vertices(verts):
    """Merge coincident geometry by distance, avoiding rounding-bin boundaries."""
    kd=KDTree(len(verts))
    for i,v in enumerate(verts):kd.insert(Vector(v),i)
    kd.balance()
    parent=list(range(len(verts)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,v in enumerate(verts):
        for _,j,dist in kd.find_range(Vector(v),WELD_TOL):
            if j>=i:continue
            a,b=root(i),root(j)
            if a!=b:parent[max(a,b)]=min(a,b)
    roots=[root(i) for i in range(len(verts))];unique=sorted(set(roots));lookup={v:i for i,v in enumerate(unique)}
    return verts[unique].copy(),np.array([lookup[i] for i in roots],dtype=np.int64),kd


def mesh_snapshot(obj, record, source=None):
    mesh = obj.data
    mesh.calc_loop_triangles()
    verts = np.array([tuple(obj.matrix_world @ v.co) for v in mesh.vertices], dtype=np.float64)
    tri_verts = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int64)
    tri_faces = np.array([t.polygon_index for t in mesh.loop_triangles], dtype=np.int64)
    materials = [m.name if m else None for m in mesh.materials]
    tri_materials = [materials[mesh.polygons[i].material_index] for i in tri_faces]
    uv_layer = mesh.uv_layers.get('UV0')
    tri_uv = np.array([[tuple(uv_layer.data[i].uv) for i in t.loops] for t in mesh.loop_triangles], dtype=np.float64) if uv_layer else None
    normals = np.array([tuple(t.normal) for t in mesh.loop_triangles], dtype=np.float64)
    corner_normals = np.array([[tuple(mesh.corner_normals[i].vector) for i in t.loops]
                               for t in mesh.loop_triangles], dtype=np.float64)
    name = record['name']
    if len(verts) == 0 or len(tri_verts) == 0:
        raise RuntimeError(name + ': empty mesh')
    if source is None:
        points, canonical, kd = canonical_vertices(verts)
        role_by_face = [None] * len(mesh.polygons)
        component_by_face = [-1] * len(mesh.polygons)
        ranges = get_ranges(obj)
        for ci, comp in enumerate(ranges):
            start, count = int(comp['start_face']), int(comp['face_count'])
            for fi in range(start, start+count):
                if fi >= len(role_by_face) or role_by_face[fi] is not None:
                    fail(name, 'component face ranges overlap or exceed mesh')
                    continue
                role_by_face[fi] = comp['role']
                component_by_face[fi] = ci
        if any(x is None for x in role_by_face):
            fail(name, 'component_ranges missing or do not cover every source face')
        roles = [role_by_face[i] or 'UNASSIGNED' for i in tri_faces]
        components = [component_by_face[i] for i in tri_faces]
        face_ids=[canonical[list(p.vertices)].tolist() for p in mesh.polygons]
        face_uv=[np.array([tuple(uv_layer.data[i].uv) for i in p.loop_indices]) for p in mesh.polygons] if uv_layer else None
        face_corner_normals=[np.array([tuple(mesh.corner_normals[i].vector) for i in p.loop_indices]) for p in mesh.polygons]
        face_normals=np.array([tuple(p.normal) for p in mesh.polygons])
        face_materials=[materials[p.material_index] for p in mesh.polygons]
        holes = json_value(obj.get('planting_holes'), record.get('planting_holes', []))
        plants = json_value(obj.get('plants'), record.get('plants', []))
        max_vertex_delta = 0.
    else:
        points = source['points']
        canonical = []
        distances = []
        for v in verts:
            _, index, distance = source['kd'].find(Vector(v))
            canonical.append(int(source['canonical'][index]))
            distances.append(distance)
        canonical = np.array(canonical, dtype=np.int64)
        max_vertex_delta = max(distances, default=0.)
        vertex_faces=defaultdict(set)
        for fi,ids in enumerate(source['face_ids']):
            for pid in ids:vertex_faces[(source['face_materials'][fi],int(pid))].add(fi)
        exact_triangles={tuple(sorted(map(int,t))) for t in source['tri_ids']}
        mapped_faces=defaultdict(list)
        roles, components = [], []
        unmapped, minimum_normal_dot, minimum_corner_normal_dot, uv_delta = 0, 1., 1., 0.
        alternate_triangles=0;normal_role_minimum={};normal_role_bad_corners=Counter();normal_samples=[]
        for ti, indices in enumerate(canonical[tri_verts]):
            candidates=set.intersection(*(vertex_faces.get((tri_materials[ti],int(pid)),set()) for pid in indices))
            candidates=[fi for fi in candidates if len(mapped_faces[fi])<len(source['face_ids'][fi])-2]
            if not candidates:
                roles.append('UNMAPPED'); components.append(-1); unmapped += 1
                continue
            fi=max(candidates,key=lambda f:float(np.dot(normals[ti],source['face_normals'][f])))
            mapped_faces[fi].append(indices)
            alternate_triangles+=int(tuple(sorted(map(int,indices))) not in exact_triangles)
            roles.append(source['role_by_face'][fi]); components.append(source['component_by_face'][fi])
            minimum_normal_dot = min(minimum_normal_dot, float(np.dot(normals[ti], source['face_normals'][fi])))
            for corner, point_id in enumerate(indices):
                sc = source['face_ids'][fi].index(point_id)
                dot=float(np.dot(corner_normals[ti,corner],source['face_corner_normals'][fi][sc]))
                minimum_corner_normal_dot = min(minimum_corner_normal_dot,dot)
                role=source['role_by_face'][fi]
                normal_role_minimum[role]=min(normal_role_minimum.get(role,1.),dot)
                if dot<.999:
                    normal_role_bad_corners[role]+=1
                    normal_samples.append({'source_face':fi,'imported_triangle':ti,'component':source['component_by_face'][fi],
                                           'role':role,'corner':corner,'dot':dot,
                                           'source_normal':source['face_corner_normals'][fi][sc].tolist(),
                                           'imported_normal':corner_normals[ti,corner].tolist()})
            if tri_uv is not None and source['face_uv'] is not None:
                for corner, point_id in enumerate(indices):
                    sc = source['face_ids'][fi].index(point_id)
                    uv_delta = max(uv_delta, float(np.max(np.abs(tri_uv[ti, corner]-source['face_uv'][fi][sc]))))
        unmatched_source=sum(max(0,len(ids)-2-len(mapped_faces[fi])) for fi,ids in enumerate(source['face_ids']))
        polygon_coverage_errors=[];polygon_winding_errors=[]
        for fi,ids in enumerate(source['face_ids']):
            expected_edges=Counter(tuple(sorted((ids[i],ids[(i+1)%len(ids)]))) for i in range(len(ids)))
            actual_edges=edge_counts(mapped_faces[fi])
            boundary=Counter({e:n for e,n in actual_edges.items() if n==1})
            if boundary!=expected_edges or any(n>2 for n in actual_edges.values()):
                polygon_coverage_errors.append(fi)
            if oriented_boundary(mapped_faces[fi])!=oriented_boundary([ids]):polygon_winding_errors.append(fi)
        if unmapped or unmatched_source or max_vertex_delta > TOL:
            fail(name, f'FBX geometry/material triangle mismatch: imported={unmapped}, source={unmatched_source}, vertex_delta={max_vertex_delta:g} m')
        if polygon_coverage_errors:
            fail(name,f'FBX triangulation does not cover {len(polygon_coverage_errors)} source polygons with their exact boundary')
        if polygon_winding_errors:
            fail(name,f'FBX triangulation changes winding on {len(polygon_winding_errors)} source polygons')
        if minimum_corner_normal_dot < .999:
            fail(name, f'FBX smooth corner normals differ from source (minimum dot={minimum_corner_normal_dot:g})')
        if uv_delta > 1e-4:
            fail(name, f'FBX UV coordinates differ from source ({uv_delta:g})')
        ranges, holes, plants = source['ranges'], source['holes'], source['plants']
        face_ids=face_uv=face_corner_normals=face_normals=face_materials=role_by_face=component_by_face=None
        kd = None
    ids = canonical[tri_verts]
    bounds = [verts.min(0).tolist(), verts.max(0).tolist()]
    areas = np.array([t.area for t in mesh.loop_triangles])
    uv_areas = np.abs(np.cross(tri_uv[:,1]-tri_uv[:,0], tri_uv[:,2]-tri_uv[:,0]))*.5 if tri_uv is not None else np.array([])
    result = {
        'name': name, 'triangles': len(ids), 'polygons':len(mesh.polygons),
        'polygon_size_histogram':dict(Counter(str(len(p.vertices)) for p in mesh.polygons)),
        'triangle_count_note':'Evaluated mesh loop-triangle count; FBX retains source polygons to preserve authored corner normals.',
        'vertices': len(verts), 'bounds_metres': bounds,
        'size_metres': (verts.max(0)-verts.min(0)).tolist(), 'pivot_metres': list(obj.matrix_world.translation),
        'finite_geometry': bool(np.isfinite(verts).all()), 'finite_normals': bool(np.isfinite(normals).all()),
        'finite_corner_normals': bool(np.isfinite(corner_normals).all()),
        'corner_normal_length_range': [float(np.linalg.norm(corner_normals,axis=2).min()),float(np.linalg.norm(corner_normals,axis=2).max())],
        'finite_uv0': bool(tri_uv is not None and np.isfinite(tri_uv).all()), 'UV0_present': uv_layer is not None,
        'zero_area_triangles': int(np.sum(areas <= AREA_EPS)), 'zero_uv_area_triangles': int(np.sum(uv_areas <= UV_AREA_EPS)),
        'zero_area_by_role': dict(Counter(roles[i] for i in np.where(areas<=AREA_EPS)[0])),
        'zero_uv_area_by_role': dict(Counter(roles[i] for i in np.where(uv_areas<=UV_AREA_EPS)[0])),
        'degenerate_triangle_samples': [{'triangle':int(i),'face':int(tri_faces[i]),'role':roles[i],'component':int(components[i]),
                                         'geometric_area_m2':float(areas[i]),'uv_area':float(uv_areas[i]) if len(uv_areas) else None}
                                        for i in np.where((areas<=AREA_EPS)|(uv_areas<=UV_AREA_EPS) if len(uv_areas) else areas<=AREA_EPS)[0][:24]],
        'materials': materials, 'scale': list(obj.scale), 'rotation_radians': list(obj.rotation_euler),
        'unapplied_modifiers': [m.name for m in obj.modifiers], 'animation': bool(obj.animation_data or mesh.shape_keys),
        'roles': dict(Counter(roles)), 'maximum_source_vertex_delta_m': max_vertex_delta,
    }
    if source is not None:
        result.update(source_triangle_mismatches=unmapped, unmatched_source_triangles=unmatched_source,
                      source_minimum_normal_dot=minimum_normal_dot, source_minimum_corner_normal_dot=minimum_corner_normal_dot,
                      source_maximum_uv_delta=uv_delta,alternate_legal_triangulation_count=alternate_triangles,
                      source_polygon_coverage_errors=polygon_coverage_errors,
                      source_polygon_winding_errors=polygon_winding_errors,
                      corner_normal_minimum_dot_by_role=normal_role_minimum,
                      corner_normal_mismatch_count_by_role=dict(normal_role_bad_corners),
                      corner_normal_worst_samples=sorted(normal_samples,key=lambda x:x['dot'])[:16],
                      surface_match_method='Each imported triangle must use vertices of one same-material source polygon; every polygon boundary is covered exactly once and internal edges exactly twice. All vertices, corner UVs and smooth normals are compared separately.')
    snap = dict(result=result, verts=verts, tri_verts=tri_verts, tri_ids=ids, points=points, canonical=canonical,
                tri_uv=tri_uv, normals=normals, corner_normals=corner_normals,
                tri_materials=tri_materials, roles=roles, components=components,
                ranges=ranges, holes=holes, plants=plants, kd=kd, record=record)
    snap.update(face_ids=face_ids,face_uv=face_uv,face_corner_normals=face_corner_normals,face_normals=face_normals,
                face_materials=face_materials,role_by_face=role_by_face,component_by_face=component_by_face)
    return snap


def geometry_checks(snap, imported=False):
    r, rec = snap['result'], snap['record']
    name = rec['name']; low = int(rec.get('lod_index', 3 if name.endswith('_LOD3') else 0)) == 3
    cap = 'StrawberryBedEnd' in name
    length = .4 if cap else 4.
    for key in ['finite_geometry','finite_normals','finite_corner_normals','finite_uv0','UV0_present']:
        if not r[key]: fail(name, key + ' failed')
    if r['corner_normal_length_range'][0] < .999 or r['corner_normal_length_range'][1] > 1.001:
        fail(name,'corner normals are not normalized')
    for key in ['zero_area_triangles','zero_uv_area_triangles','unapplied_modifiers','animation']:
        if r[key]: fail(name, key + ' is nonzero')
    if max(abs(v) for v in r['pivot_metres']) > TOL: fail(name, 'pivot is not ground/start-end origin')
    if max(abs(v-1) for v in r['scale']) > 1e-6: fail(name, 'nonidentity scale')
    if max(abs(v) for v in r['rotation_radians']) > 1e-5: fail(name, 'unapplied rotation')
    if not cap:
        limits = (100, 300) if low else (15000, 40000)
        if not limits[0] <= r['triangles'] <= limits[1]: fail(name, f'triangles outside {limits}')
    elif 'triangle_budget' in rec and r['triangles'] > rec['triangle_budget']:
        fail(name, 'optional endcap exceeds its declared triangle budget')
    if abs(r['bounds_metres'][0][2]+.15) > TOL: fail(name, 'skirt minimum is not -0.15 m')
    if not cap and (abs(r['bounds_metres'][0][1]) > TOL or abs(r['bounds_metres'][1][1]-4) > TOL):
        fail(name, 'exported geometry outside exact Y=0..4 tile envelope')
    roles = snap['roles']; points = snap['points']; tri_ids = snap['tri_ids']
    if not low and any('canopy' in str(role).lower() or 'hull' in str(role).lower() for role in roles):
        fail(name, 'LOD0 contains a declared canopy/hull role')
    endwalls, open_checks, closed_bad = {}, [], []
    profiles = {}; terminal_attributes={}
    role_sets = {'film': {role for role in roles if str(role).startswith('film')}, 'soil_body': {'soil_body'}}
    for group, members in role_sets.items():
        selected = np.array([t for t, role in zip(tri_ids, roles) if role in members], dtype=np.int64)
        if len(selected) == 0:
            if low and group=='soil_body':
                r['soil_body_omitted_for_lowest_LOD']=True
                continue
            fail(name, group+' surface not identified'); continue
        counts = edge_counts(selected)
        boundaries = [(points[a], points[b]) for (a,b), n in counts.items() if n == 1]
        excessive = [(a,b) for (a,b), n in counts.items() if n > 2]
        if excessive: fail(name, f'{group}: {len(excessive)} nonmanifold welded edges')
        expected = Counter(); unexpected = []; hole_lengths = Counter()
        for a, b in boundaries:
            end0 = max(abs(a[1]), abs(b[1])) <= TOL
            end1 = max(abs(a[1]-length), abs(b[1]-length)) <= TOL
            hem = max(abs(a[2]+.15), abs(b[2]+.15)) <= TOL
            hole = False
            if group == 'film':
                for hi, h in enumerate(snap['holes']):
                    rim = h.get('rim_xy', [])
                    if not rim: continue
                    if all(min(segment_distance(p[:2], rim[i], rim[(i+1)%len(rim)]) for i in range(len(rim))) <= TOL for p in (a,b,(a+b)*.5)):
                        hole = True; hole_lengths[hi] += float(np.linalg.norm(a[:2]-b[:2])); break
            if end0: expected['start_end'] += 1
            elif end1 and not cap: expected['finish_end'] += 1
            elif end1 and cap and max(a[2],b[2])<=TOL: expected['buried_cap_finish'] += 1
            elif group == 'film' and hem: expected['skirt_hem'] += 1
            elif hole: expected['planting_hole_rim'] += 1
            else: unexpected.append([a.tolist(), b.tolist()])
        for end, y in [('start',0.), ('finish',length)]:
            # Only exposed boundary edges define an uncapped terminal profile.
            profiles[(group,end)] = [(a[[0,2]].tolist(), b[[0,2]].tolist()) for a,b in boundaries if max(abs(a[1]-y),abs(b[1]-y)) <= TOL]
            end_tri_count = sum(np.max(np.abs(points[t,1]-y)) <= TOL for t in selected)
            endwalls[group+'_'+end] = int(end_tri_count)
            if (not cap or end == 'start') and end_tri_count:
                fail(name, group+' has forbidden '+end+' end-plane triangles')
            attrs=[]
            for ti,(triangle,role) in enumerate(zip(tri_ids,roles)):
                if role not in members:continue
                on_end=[corner for corner,pid in enumerate(triangle) if abs(points[pid,1]-y)<=TOL]
                if len(on_end)<2:continue
                for corner in on_end:
                    attrs.append({'xz':points[triangle[corner],[0,2]].tolist(),'material':snap['tri_materials'][ti],
                                  'uv':snap['tri_uv'][ti,corner].tolist() if snap['tri_uv'] is not None else None,
                                  'adjacent_triangle_normal':snap['normals'][ti].tolist(),
                                  'smooth_corner_normal':snap['corner_normals'][ti,corner].tolist()})
            terminal_attributes[(group,end)]=attrs
        if not profiles.get((group,'start')) or (not cap and not profiles.get((group,'finish'))):
            fail(name, group+' lacks an intentional open terminal profile')
        if unexpected: fail(name, f'{group}: {len(unexpected)} unexpected open boundary edges')
        rim_checks=[]
        if group=='film' and not low and not cap:
            for hi,h in enumerate(snap['holes']):
                rim=np.asarray(h.get('rim_xy',[]),dtype=np.float64)
                circumference=float(sum(np.linalg.norm(rim[(i+1)%len(rim)]-rim[i]) for i in range(len(rim)))) if len(rim) else 0.
                observed=hole_lengths[hi]
                rim_checks.append({'hole_index':hi,'declared_perimeter_m':circumference,'actual_boundary_length_m':observed})
                if circumference<=0 or abs(circumference-observed)>TOL:
                    fail(name,f'hole {hi}: actual film opening perimeter differs from rim metadata')
        open_checks.append({'group':group,'triangles':len(selected),'welded_boundary_edges':len(boundaries),
                            'allowed_boundary_categories':dict(expected),'nonmanifold_edges':len(excessive),
                            'unexpected_boundary_edges':unexpected[:24],'unexpected_boundary_count':len(unexpected),
                            'hole_rim_checks':rim_checks})
        if group == 'film':
            film = points[np.unique(selected)]
            r['film_bounds_metres'] = [film.min(0).tolist(), film.max(0).tolist()]
            if not cap and not .20-TOL <= film[:,2].max() <= .30+TOL: fail(name,'film top height outside 0.20-0.30 m')
            if not cap and not 1.-TOL <= np.ptp(film[:,0]) <= 1.1+TOL: fail(name,'film base width outside 1.0-1.1 m')
            top_ids=[t for t,role in zip(tri_ids,roles) if role=='film_top']
            if top_ids:
                r['film_top_width_m']=float(np.ptp(points[np.unique(top_ids),0]))
                if not cap and not .75-TOL<=r['film_top_width_m']<=.85+TOL:
                    warn(name,'film_top width is outside .75-.85 m; inspect the approximate .8 m top requirement')
    closed_count = 0
    for ci, comp in enumerate(snap['ranges']):
        if comp['role'] not in SOLID_ROLES: continue
        selected = np.array([tri_ids[i] for i, c in enumerate(snap['components']) if c == ci], dtype=np.int64)
        if not len(selected): continue
        stats = component_stats(selected, points); closed_count += 1
        pts = points[selected]
        volume = float(np.einsum('ij,ij->i', pts[:,0], np.cross(pts[:,1],pts[:,2])).sum()/6)
        if stats['boundary_edges'] or stats['nonmanifold_edges'] or volume <= 1e-14:
            closed_bad.append({'component':ci,'role':comp['role'],**stats,'signed_volume_m3':volume,
                               **{k:comp[k] for k in ['plant_index','compound_leaf_index','leaflet_index'] if k in comp}})
    if closed_bad: fail(name, f'{len(closed_bad)} solid components open/nonmanifold/inward or zero-volume')
    leaf_sel = np.array([t for t, role in zip(tri_ids,roles) if role == 'leaf'],dtype=np.int64)
    if len(leaf_sel):
        lp = points[np.unique(leaf_sel)]
        r['actual_leaf_bounds_metres'] = [lp.min(0).tolist(),lp.max(0).tolist()]
        r['actual_leaf_end_clearance_m'] = [float(lp[:,1].min()),float(length-lp[:,1].max())]
        if not cap and (lp[:,1].min() < -TOL or lp[:,1].max() > length+TOL): fail(name,'leaf geometry crosses tile end')
        r['leaf_end_plane_triangles']=int(sum(np.max(np.abs(points[t,1]))<=TOL or np.max(np.abs(points[t,1]-length))<=TOL for t in leaf_sel))
        if not cap and r['leaf_end_plane_triangles']:fail(name,'leaf end-plane faces suggest clipped plant geometry')
    r.update(intentional_open_surfaces=open_checks,end_plane_triangles=endwalls,
             closed_solid_components_checked=closed_count,invalid_solid_components=closed_bad,
             planting_holes_count=len(snap['holes']),declared_plants_count=len(snap['plants']))
    snap['profiles'] = profiles
    snap['terminal_attributes']=terminal_attributes


def plant_checks(snap):
    """Measure actual source component geometry; metadata only groups the parts."""
    name=snap['record']['name']
    if name.endswith('_LOD3') or 'StrawberryBedEnd' in name:return
    holes=snap['holes']; rows=defaultdict(list); byplant={}
    for i,h in enumerate(holes):
        centre=h.get('center_xy')
        if centre is None and h.get('rim_xy'):centre=np.mean(h['rim_xy'],axis=0).tolist()
        if centre is None:fail(name,f'hole {i} lacks centre/rim coordinates');continue
        index=h.get('plant_index',i);byplant[index]=h
        rows[h.get('row_index',int(centre[0]>0))].append((float(centre[1]),index,centre))
    result={'hole_count':len(holes),'row_count':len(rows),'rows':[],'actual_plants':[]}
    if len(rows)!=2:fail(name,'planting holes are not classified into two rows')
    mean_x=[]
    for row_id,values in sorted(rows.items()):
        values.sort();pitches=[values[i+1][0]-values[i][0] for i in range(len(values)-1)]
        mean_x.append(float(np.mean([v[2][0] for v in values])))
        result['rows'].append({'row_index':row_id,'hole_count':len(values),'centres_xy':[v[2] for v in values],
                               'within_tile_pitch_range_m':[min(pitches),max(pitches)] if pitches else None})
        if not pitches or min(pitches)<.25-TOL or max(pitches)>.30+TOL:fail(name,'within-row hole spacing outside 0.25-0.30 m')
    result['mean_row_separation_m']=abs(mean_x[1]-mean_x[0]) if len(mean_x)==2 else None
    if result['mean_row_separation_m'] is not None and not .30-TOL<=result['mean_row_separation_m']<=.35+TOL:
        fail(name,'planting row separation outside 0.30-0.35 m')
    if len(rows)==2:
        a,b=list(rows.values());stagger=[min(abs(x[0]-y[0]) for y in b) for x in a]
        result['nearest_cross_row_y_offset_range_m']=[min(stagger),max(stagger)]
        result['median_nearest_cross_row_y_offset_m']=float(np.median(stagger))
        if result['median_nearest_cross_row_y_offset_m']<.08:fail(name,'the two planting rows are not meaningfully staggered')
    geometry_plants=defaultdict(list)
    for ci,comp in enumerate(snap['ranges']):
        if comp['role'] in {'leaf','petiole'}:
            if 'plant_index' not in comp:fail(name,'plant component lacks plant_index grouping');continue
            geometry_plants[comp['plant_index']].append(ci)
    declared={p.get('plant_index',p.get('index',i)):p for i,p in enumerate(snap['plants'])}
    tiny_count=0
    for index,comps in sorted(geometry_plants.items()):
        select=[i for i,c in enumerate(snap['components']) if c in comps]
        points=snap['points'][np.unique(snap['tri_ids'][select])]
        h=byplant.get(index,{});p=declared.get(index,{})
        tiny=bool(p.get('tiny',False) or p.get('status')=='tiny' or p.get('state')=='tiny' or h.get('tiny',False) or h.get('status')=='tiny')
        tiny_count+=int(tiny)
        compound=defaultdict(set)
        for ci in comps:
            comp=snap['ranges'][ci]
            if comp['role']=='leaf':
                if 'compound_leaf_index' not in comp or 'leaflet_index' not in comp:
                    fail(name,f'plant {index}: missing trifoliate leaf grouping');continue
                compound[comp['compound_leaf_index']].add(comp['leaflet_index'])
        if any(len(leaves)!=3 for leaves in compound.values()):fail(name,f'plant {index}: compound leaf does not contain three leaflets')
        if not tiny and not 3<=len(compound)<=6:fail(name,f'plant {index}: normal young plant has {len(compound)} compound leaves')
        soil_z=h.get('soil_z')
        planar_hull=points[convex_hull_2d([Vector(p[:2]) for p in points]),:2]
        diameter=float(np.sqrt(((planar_hull[:,None,:]-planar_hull[None,:,:])**2).sum(2).max()))
        bbox_width=float(max(np.ptp(points[:,0]),np.ptp(points[:,1])))
        height=float(points[:,2].max()-soil_z) if soil_z is not None else None
        if soil_z is None:fail(name,f'plant {index}: no planting soil_z for height check')
        if not tiny and (not .10-TOL<=diameter<=.20+TOL or height is None or not .05-TOL<=height<=.12+TOL):
            fail(name,f'plant {index}: measured young plant diameter/height outside brief ({diameter}, {height})')
        result['actual_plants'].append({'plant_index':index,'tiny':tiny,'bounds_metres':[points.min(0).tolist(),points.max(0).tolist()],
                                        'diameter_m':diameter,'diameter_method':'Maximum distance between actual XY convex-hull vertices; independent of plant rotation.',
                                        'maximum_axis_aligned_xy_span_m':bbox_width,'height_above_soil_m':height,'compound_leaves':len(compound),
                                        'leaflets_per_compound':{str(k):len(v) for k,v in compound.items()}})
    empty_count=len(holes)-len(geometry_plants)
    result.update(actual_plants=len(geometry_plants),empty_holes=empty_count,tiny_plants=tiny_count,
                  tiny_or_empty_fraction=(empty_count+tiny_count)/len(holes) if holes else None,
                  plant_geometry=result.pop('actual_plants'))
    if result['tiny_or_empty_fraction'] is None or not .05-1e-6<=result['tiny_or_empty_fraction']<=.10+1e-6:
        fail(name,'tiny/empty fraction outside 5-10 percent')
    snap['result']['planting_measurements']=result
    snap['hole_rows']=rows


def inspect_materials(objects):
    mats = sorted({m for ob in objects for m in ob.data.materials if m},key=lambda m:m.name)
    images, material_records = {}, []
    for mat in mats:
        nodes = mat.node_tree.nodes if mat.use_nodes else []
        bs = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'),None)
        if bs is None: fail(mat.name,'missing Principled PBR node'); continue
        alpha = bs.inputs['Alpha']
        row = {'name':mat.name,'alpha':float(alpha.default_value),'alpha_linked':bool(alpha.is_linked),
               'backface_culling':mat.use_backface_culling,'specular':float(bs.inputs['Specular IOR Level'].default_value),
               'roughness_default':float(bs.inputs['Roughness'].default_value),'texture_images':[],
               'normal_convention':str(mat.get('normal_convention','')),
               'orm_channels':str(mat.get('orm_channels','')),'pbr_connections':{}}
        if alpha.is_linked or abs(alpha.default_value-1)>1e-6: fail(mat.name,'alpha must be constant1')
        if 'Leaf' in mat.name and mat.use_backface_culling: fail(mat.name,'foliage is not two-sided')
        if bs.inputs['Transmission Weight'].is_linked or bs.inputs['Transmission Weight'].default_value != 0:
            fail(mat.name,'opaque material has transmission')
        for socket_name in ['Base Color','Normal','Roughness','Metallic']:
            socket=bs.inputs[socket_name]
            link=socket.links[0] if socket.is_linked else None
            row['pbr_connections'][socket_name]={'node':link.from_node.type,'socket':link.from_socket.name} if link else None
            if link is None:fail(mat.name,socket_name+' lacks a PBR texture connection');continue
            node=link.from_node
            if socket_name=='Base Color':
                if node.type!='TEX_IMAGE' or not node.image or 'BaseColor' not in node.image.filepath:
                    fail(mat.name,'Base Color is not connected to its BaseColor image')
            elif socket_name=='Normal':
                if node.type!='NORMAL_MAP' or node.space!='TANGENT' or not node.inputs['Color'].is_linked:
                    fail(mat.name,'normal map is not a tangent-space normal texture')
                else:
                    tex=node.inputs['Color'].links[0].from_node
                    if tex.type!='TEX_IMAGE' or not tex.image or 'Normal' not in tex.image.filepath:
                        fail(mat.name,'normal input is not connected to its Normal image')
            else:
                expected='Green' if socket_name=='Roughness' else 'Blue'
                if node.type!='SEPARATE_COLOR' or link.from_socket.name!=expected or not node.inputs['Color'].is_linked:
                    fail(mat.name,socket_name+' is not connected to ORM '+expected)
                else:
                    tex=node.inputs['Color'].links[0].from_node
                    if tex.type!='TEX_IMAGE' or not tex.image or 'ORM' not in tex.image.filepath:
                        fail(mat.name,socket_name+' does not use its ORM image')
        for node in nodes:
            if node.type != 'TEX_IMAGE' or node.image is None: continue
            im = node.image; path = Path(bpy.path.abspath(im.filepath)).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file(): fail(mat.name,'texture missing/outside revision: '+str(path)); continue
            row['texture_images'].append(path.relative_to(ROOT).as_posix())
            key = (str(path),im.colorspace_settings.name)
            if key not in images:
                im.reload()
                pix = np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(pix); pix = pix.reshape((-1,4))
                suffix = 'BaseColor' if 'BaseColor' in path.name else ('Normal' if 'Normal' in path.name else ('ORM' if 'ORM' in path.name else 'unknown'))
                actual = {'file':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'size_px':list(im.size),
                          'colour_space':im.colorspace_settings.name,'relative_source_path':im.filepath.startswith('//'),
                          'alpha_min_max':[float(pix[:,3].min()),float(pix[:,3].max())],
                          'pixel_rgb_min':pix[:,:3].min(0).tolist(),'pixel_rgb_max':pix[:,:3].max(0).tolist(),
                          'role':suffix}
                if not actual['relative_source_path']:fail(mat.name,'nonrelative texture path')
                if suffix=='BaseColor' and actual['colour_space']!='sRGB':fail(mat.name,'BaseColor must be sRGB')
                if suffix in ['Normal','ORM'] and actual['colour_space']!='Non-Color':fail(mat.name,suffix+' must be Non-Color')
                if actual['alpha_min_max'][0] < .999999:fail(mat.name,'saved texture alpha is not solid')
                if not np.isfinite(pix).all():fail(mat.name,'saved texture contains nonfinite pixels')
                if suffix=='Normal':
                    normal_lengths=np.linalg.norm(pix[:,:3]*2-1,axis=1)
                    actual['decoded_normal_length_range']=[float(normal_lengths.min()),float(normal_lengths.max())]
                    if pix[:,2].min()<.5 or normal_lengths.min()<.97 or normal_lengths.max()>1.03:
                        fail(mat.name,'saved tangent normal image contains invalid vectors')
                if suffix=='ORM' and pix[:,2].max()>1/255:
                    fail(mat.name,'organic/film material unexpectedly metallic')
                if 'Mulch' in mat.name and suffix=='ORM' and float(pix[:,1].min()) < .85-1/255:
                    fail(mat.name,'mulch roughness texture falls below .85')
                images[key] = actual
        if not row['texture_images']: fail(mat.name,'missing saved PBR images')
        roles={kind for kind in ['BaseColor','Normal','ORM'] if any(kind in Path(p).name for p in row['texture_images'])}
        if roles!={'BaseColor','Normal','ORM'}:fail(mat.name,'incomplete BaseColor/Normal/ORM texture set')
        if 'Mulch' in mat.name and row['specular'] > .2:warn(mat.name,'specular exceeds low-specular review value .2; inspect grazing light')
        material_records.append(row)
    return material_records,list(images.values())


def join_check(a,b,kind):
    entry={'left':a['record']['name'],'right':b['record']['name'],'kind':kind,'placement_delta_local_m':[0,4,0],'profiles':{}}
    for group in ['film','soil_body']:
        if group=='soil_body' and (a['result'].get('soil_body_omitted_for_lowest_LOD') or b['result'].get('soil_body_omitted_for_lowest_LOD')):
            entry['profiles'][group]={'checked':False,'reason':'Lowest LOD is the film mound only; no internal soil body. Exterior film profile remains mandatory.'}
            continue
        gap=profile_gap(a['profiles'].get((group,'finish'),[]),b['profiles'].get((group,'start'),[]))
        entry['profiles'][group]={'maximum_polyline_gap_m':gap,'matched':gap is not None and gap<=TOL}
        left=a['terminal_attributes'].get((group,'finish'),[]);right=b['terminal_attributes'].get((group,'start'),[])
        uv_gaps=[];normal_angles=[];corner_angles=[]
        for attr in left:
            partners=[p for p in right if p['material']==attr['material'] and np.linalg.norm(np.array(p['xz'])-attr['xz'])<=TOL]
            if not partners:continue
            if attr['uv'] is not None:
                distances=[]
                for p in partners:
                    if p['uv'] is not None:
                        delta=np.array(attr['uv'])-p['uv'];distances.append(float(np.max(np.abs(delta-np.rint(delta)))))
                if distances:uv_gaps.append(min(distances))
            normal_angles.append(min(math.degrees(math.acos(max(-1.,min(1.,float(np.dot(attr['adjacent_triangle_normal'],p['adjacent_triangle_normal'])))))) for p in partners))
            corner_angles.append(min(math.degrees(math.acos(max(-1.,min(1.,float(np.dot(attr['smooth_corner_normal'],p['smooth_corner_normal'])))))) for p in partners))
        entry['profiles'][group]['maximum_periodic_uv_phase_difference']=max(uv_gaps) if uv_gaps else None
        entry['profiles'][group]['maximum_adjacent_triangle_normal_gap_degrees']=max(normal_angles) if normal_angles else None
        entry['profiles'][group]['maximum_smooth_corner_normal_gap_degrees']=max(corner_angles) if corner_angles else None
        entry['profiles'][group]['uv_normal_note']='Measured at matching terminal positions and material roles. Triangle and smooth corner normals are both checked; modulo1 UV comparison assumes repeating textures.'
        if kind!='cross_LOD' and uv_gaps and max(uv_gaps)>1e-3:
            warn(entry['left']+' / '+entry['right'],group+' terminal UV phase differs; inspect texture seam')
    entry['pass']=all(x.get('matched',True) for x in entry['profiles'].values())
    # With both complete meshes inside [0,4], translated tiles cannot overlap in
    # positive volume; profile checks above establish continuity on the join plane.
    amax=a['result']['bounds_metres'][1][1];bmin=b['result']['bounds_metres'][0][1]+4
    entry['whole_geometry_longitudinal_gap_m']=bmin-amax
    entry['positive_volume_longitudinal_overlap_m']=max(0.,amax-bmin)
    if a.get('hole_rows') and b.get('hole_rows'):
        pitches=[]
        for row_id,values in a['hole_rows'].items():
            other=b['hole_rows'].get(row_id,[])
            if values and other:
                pitch=4+min(v[0] for v in other)-max(v[0] for v in values)
                pitches.append({'row_index':row_id,'hole_pitch_across_joint_m':pitch})
                if not .25-TOL<=pitch<=.30+TOL:
                    fail(entry['left']+' / '+entry['right'],'hole pitch across joint outside 0.25-0.30 m')
        entry['planting_pitch_across_joint']=pitches
    if entry['positive_volume_longitudinal_overlap_m']>TOL:entry['pass']=False
    if not entry['pass']:
        if kind=='cross_LOD':warn(entry['left']+' / '+entry['right'],'cross-LOD terminal profiles differ; do not infer compatible independently mixed LOD joins')
        else:fail(entry['left']+' / '+entry['right'],'terminal seam fails')
    return entry


def analytical_slope(snapshots):
    theta=math.atan(.03);rx=Matrix.Rotation(theta,4,'X')
    cycle='AABACBBCC';placements=[];errors=[];pairs=set();skirt=[]
    for row in range(10):
        for tile in range(5):
            variant=cycle[(row+tile)%len(cycle)]
            origin=Vector(((row-4.5)*1.7,4*tile*math.cos(theta),4*tile*math.sin(theta)))
            placements.append({'row':row,'tile':tile,'variant':variant,'origin_metres':list(origin),'pitch_radians':theta})
            if tile<4:
                nxt=Vector(((row-4.5)*1.7,4*(tile+1)*math.cos(theta),4*(tile+1)*math.sin(theta)))
                errors.append((origin+rx@Vector((0,4,0))-nxt).length)
                pairs.add(variant+cycle[(row+tile+1)%len(cycle)])
    n=np.array((0,-math.sin(theta),math.cos(theta)))
    for lod in ['', '_LOD3']:
        for variant in 'ABC':
            s=snapshots[PREFIX+variant+lod]
            for sink in [0.,.03]:
                rotation=np.array(rx.to_3x3());v=(rotation@s['verts'].T).T-np.array((0,0,sink))
                signed=v@n
                skirt.append({'mesh':PREFIX+variant+lod,'vertical_sink_m':sink,'signed_ground_distance_range_m':[float(signed.min()),float(signed.max())]})
    return {'method':'Analytical validation arrangement from actual imported vertex data; this is not a rendered or native ground-contact proof.',
            'rows':10,'tiles_per_row':5,'row_centres_m':1.7,'slope_fraction':.03,'pitch_degrees':math.degrees(theta),
            'row_surface_length_m':20.,'row_horizontal_length_m':20*math.cos(theta),'row_rise_m':20*math.sin(theta),
            'instance_count':len(placements),'covered_directed_variant_pairs':sorted(pairs),
            'maximum_chained_endpoint_error_m':max(errors),'placements':placements,'signed_ground_checks':skirt,
            'pass':max(errors)<=TOL and len(pairs)==9 and all(x['signed_ground_distance_range_m'][0]<0<x['signed_ground_distance_range_m'][1] for x in skirt)}


def main():
    report_path=ROOT/'Reports'/'strawberries_v005.json'
    family=json.loads(report_path.read_text(encoding='utf-8-sig'))
    records=family['assets']
    if '--only-a' in sys.argv:records=[r for r in records if r['name'] in {PREFIX+'A',PREFIX+'A_LOD3'}]
    byname={r['name']:r for r in records}
    expected={PREFIX+v+suffix for v in 'ABC' for suffix in ['', '_LOD3']}
    optional={'SM_PazFarm_StrawberryBedEnd','SM_PazFarm_StrawberryBedEnd_LOD3'}
    if not expected.issubset(byname) or not set(byname).issubset(expected|optional):fail('delivery','required names missing or unexpected names')
    if bool(optional&set(byname)) and not optional.issubset(byname):fail('delivery','optional cap lacks its LOD pair')
    src_path=ROOT/'Blend'/'StrawberryBeds.blend'
    OUT['inputs']={'family_report':{'file':str(report_path.relative_to(ROOT)),'sha256':sha(report_path)},
                   'source':{'file':str(src_path.relative_to(ROOT)),'sha256':sha(src_path)},
                   'validator':{'file':str(Path(__file__).resolve().relative_to(ROOT)),'sha256':sha(__file__)}}
    bpy.ops.wm.open_mainfile(filepath=str(src_path),load_ui=False,use_scripts=False)
    OUT['source']['unit_scale']=bpy.context.scene.unit_settings.scale_length
    if abs(OUT['source']['unit_scale']-1)>1e-8:fail('source','unit scale is not metres')
    source_snapshots={};objects=[]
    for rec in records:
        ob=bpy.data.objects.get(rec.get('source_object',rec['name']))
        if ob is None or ob.type!='MESH':fail(rec['name'],'source mesh absent');continue
        objects.append(ob);s=mesh_snapshot(ob,rec);geometry_checks(s);plant_checks(s);source_snapshots[rec['name']]=s
    OUT['source']['meshes']=[s['result'] for s in source_snapshots.values()]
    OUT['source']['materials'],OUT['source']['images']=inspect_materials(objects)
    probe_paths={}
    if PROBE_MODE:
        OUT['transient_export_probe']=PROBE_MODE
        (ROOT/'Temp'/'QAProbes').mkdir(parents=True,exist_ok=True)
        for rec in records:
            ob=bpy.data.objects[rec['name']]
            if PROBE_MODE=='evaluated_normals':
                evaluated=[tuple(n.vector) for n in ob.data.corner_normals]
                ob.data=ob.data.copy();ob.data.normals_split_custom_set(evaluated)
            bpy.ops.object.select_all(action='DESELECT')
            ob.hide_set(False);ob.hide_viewport=False;ob.select_set(True);bpy.context.view_layer.objects.active=ob
            path=ROOT/'Temp'/'QAProbes'/('validation_probe_'+PROBE_MODE+'_'+rec['name']+'.fbx')
            bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},global_scale=1.,
                apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',
                use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=PROBE_MODE!='untriangulated',
                add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
            probe_paths[rec['name']]=path
    imported={}
    for rec in records:
        name=rec['name']
        if name not in source_snapshots:continue
        path=probe_paths.get(name,ROOT/rec['fbx'])
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1.
        bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False)
        obs=[ob for ob in bpy.data.objects if ob.type=='MESH']
        if len(obs)!=1:fail(name,f'FBX contains {len(obs)} mesh objects instead of1');continue
        bpy.context.view_layer.update()
        s=mesh_snapshot(obs[0],rec,source_snapshots[name]);geometry_checks(s,True)
        s['hole_rows']=source_snapshots[name].get('hole_rows',{})
        s['result'].update(file=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,imported_name=obs[0].name)
        s['result']['fbx_header']=fbx_global_settings(path,name)
        s['result']['imported_material_alpha']=[]
        for mat in obs[0].data.materials:
            bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if mat and mat.use_nodes else None
            if bs is None:fail(name,'imported material lacks Principled shader');continue
            alpha=bs.inputs['Alpha']
            s['result']['imported_material_alpha'].append({'name':mat.name,'alpha':float(alpha.default_value),'linked':bool(alpha.is_linked),
                                                         'backface_culling':mat.use_backface_culling})
            if abs(alpha.default_value-1)>1e-6:fail(name,'imported material alpha is not 1')
            if alpha.is_linked:
                node=alpha.links[0].from_node
                if node.type!='TEX_IMAGE' or not node.image:
                    fail(name,'imported alpha has an unexpected nontexture driver')
                else:
                    px=np.empty(len(node.image.pixels),np.float32);node.image.pixels.foreach_get(px)
                    if px.size==0 or float(px[3::4].min())<.999999:fail(name,'imported alpha texture is not solid')
            if 'Leaf' in mat.name and mat.use_backface_culling:fail(name,'imported foliage has backface culling enabled')
        if obs[0].name!=name:fail(name,'FBX mesh name differs from expected')
        if s['result']['materials']!=source_snapshots[name]['result']['materials']:fail(name,'FBX material slot names/order changed')
        if any(o.name.startswith(('UCX_','UBX_','USP_','UCP_')) for o in bpy.data.objects):fail(name,'collision object present')
        imported[name]=s;OUT['assets'].append(s['result'])
    for v in 'ABC':
        for w in 'ABC':
            for suffix in ['', '_LOD3']:
                if PREFIX+v+suffix in imported and PREFIX+w+suffix in imported:
                    OUT['joins'].append(join_check(imported[PREFIX+v+suffix],imported[PREFIX+w+suffix],'same_LOD'))
            for ls,rs in [('', '_LOD3'),('_LOD3','')]:
                if PREFIX+v+ls in imported and PREFIX+w+rs in imported:
                    OUT['cross_lod_joins'].append(join_check(imported[PREFIX+v+ls],imported[PREFIX+w+rs],'cross_LOD'))
        hi,lo=source_snapshots.get(PREFIX+v),source_snapshots.get(PREFIX+v+'_LOD3')
        if hi and lo and hi['result']['materials']!=lo['result']['materials']:fail(PREFIX+v,'high/low material slot names/order differ')
        for suffix in ['', '_LOD3']:
            capname='SM_PazFarm_StrawberryBedEnd'+suffix
            if capname in imported and PREFIX+v+suffix in imported:
                OUT['endcap_joins'].append(join_check(imported[PREFIX+v+suffix],imported[capname],'endcap'))
    if expected.issubset(imported):
        OUT['slope_proof']=analytical_slope(imported)
        if not OUT['slope_proof']['pass']:fail('slope','analytical placement/contact check failed')
    if len(OUT['assets'])!=len(records):fail('delivery','not all FBX assets inspected')
    OUT['inputs_unchanged']=sha(src_path)==OUT['inputs']['source']['sha256'] and sha(report_path)==OUT['inputs']['family_report']['sha256']
    OUT['inputs_unchanged'] = OUT['inputs_unchanged'] and all(sha(ROOT/a['file'])==a['sha256'] for a in OUT['assets']) and all(sha(ROOT/im['file'])==im['sha256'] for im in OUT['source']['images'])
    if not OUT['inputs_unchanged']:fail('delivery','source/report changed during validation; retry frozen inputs')
    OUT['comparison_evidence']=[]
    for file in ['Reports/strawberries_v005_fbx_normal_comparison_before_fix.json',
                 'Reports/strawberries_v005_fbx_normal_comparison.json',
                 'Reports/strawberries_v005_export_receipt.json']:
        path=ROOT/file
        if path.is_file():
            item={'file':file,'sha256':sha(path),
                'status':'Historical pre-fix diagnostic' if 'before_fix' in file else 'Author comparison/export receipt; independent mesh checks are recorded above'}
            evidence=json.loads(path.read_text(encoding='utf-8-sig'))
            if file.endswith('fbx_normal_comparison.json'):
                item['bound_current_inputs_match']=all((ROOT/p).is_file() and sha(ROOT/p)==digest for p,digest in evidence.get('input_hashes_after',{}).items())
                item['images']=[{'file':p,'sha256':digest,'matches_current_file':(ROOT/p).is_file() and sha(ROOT/p)==digest}
                                for p,digest in evidence.get('images',{}).items()]
                item['fraction_pixels_above_2_bytes']=evidence.get('fraction_pixels_above_2_bytes')
                item['mean_abs_RGB_byte_difference']=evidence.get('mean_abs_RGB_byte_difference')
                if not IS_DRAFT and (not item['bound_current_inputs_match'] or not item['images'] or not all(i['matches_current_file'] for i in item['images'])):
                    fail('evidence','current source/FBX comparison receipt is stale or incomplete')
            elif file.endswith('export_receipt.json'):
                bindings={**evidence.get('protected_hashes_after',{}),**evidence.get('current_fbx_hashes',{})}
                item['bound_current_inputs_match']=bool(bindings) and all((ROOT/p).is_file() and sha(ROOT/p)==digest for p,digest in bindings.items())
                if not IS_DRAFT and not item['bound_current_inputs_match']:fail('evidence','FBX export receipt is stale')
            OUT['comparison_evidence'].append(item)


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        fail('validator',repr(exc));OUT['exception_traceback']=traceback.format_exc()
    OUT['passed']=not OUT['failures']
    OUT['status']='PASS_OFFLINE_GEOMETRY' if OUT['passed'] else 'FAIL_OR_INCOMPLETE'
    REPORT.write_text(json.dumps(OUT,indent=2)+'\n',encoding='utf-8')
    print('V005_INDEPENDENT_VALIDATION',OUT['status'],'ASSETS',len(OUT['assets']),'FAILURES',OUT['failures'],flush=True)
    if not OUT['passed']:
        raise RuntimeError('Independent v005 checks failed; see '+str(REPORT))
