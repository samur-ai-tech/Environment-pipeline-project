"""In-editor, read-only: how StaticMeshDescription element ids and getters behave in this build. ARGS: expected_pid."""
import os, time
import unreal as u
assert os.getpid() == ARGS['expected_pid']
m = u.load_asset('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/Bake/KarmeiYosef_31850349_34907601_4km_buildings')
d = m.get_static_mesh_description(0)
out = {}
for cls in ('VertexID', 'VertexInstanceID', 'TriangleID', 'PolygonID', 'PolygonGroupID'):
    c = getattr(u, cls, None)
    out[cls] = [n for n in dir(c) if not n.startswith('_')][:12] if c else None
try:
    v = u.VertexID(0); out['vid_ctor'] = str(v)
except Exception as e:
    out['vid_ctor_err'] = repr(e)[:200]
try:
    t0 = time.time()
    p = d.get_vertex_position(u.VertexID(0)); out['pos0'] = [p.x, p.y, p.z]
    pid0 = u.PolygonID(0)
    out['poly0_verts'] = [str(x) for x in d.get_polygon_vertices(pid0)]
    out['poly0_vis'] = [str(x) for x in d.get_polygon_vertex_instances(pid0)]
    out['poly0_group'] = str(d.get_polygon_polygon_group(pid0))
    vi = d.get_polygon_vertex_instances(pid0)[0]
    out['uv'] = str(d.get_vertex_instance_uv(vi, 0))
    out['vi_vertex'] = str(d.get_vertex_instance_vertex(vi))
    out['counts'] = [d.get_vertex_count(), d.get_vertex_instance_count(), d.get_polygon_count(), d.get_triangle_count(), d.get_polygon_group_count()]
    # timing: 2000 polygon reads
    t1 = time.time()
    for k in range(2000):
        vs = d.get_polygon_vertices(u.PolygonID(k))
    out['t_2000_polys_s'] = round(time.time() - t1, 3)
    t1 = time.time()
    for k in range(2000):
        d.get_vertex_position(u.VertexID(k))
    out['t_2000_pos_s'] = round(time.time() - t1, 3)
    g = [str(s.get_editor_property('material_slot_name')) for s in m.get_editor_property('static_materials')]
    out['slots'] = g
    out['group_slot_names'] = [str(d.get_polygon_group_material_slot_name(u.PolygonGroupID(i))) if hasattr(d, 'get_polygon_group_material_slot_name') else 'n/a' for i in range(d.get_polygon_group_count())]
except Exception as e:
    out['err'] = repr(e)[:400]
RESULT = {'ok': True, **out}
