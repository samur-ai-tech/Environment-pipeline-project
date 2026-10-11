"""In-editor, read-only: vertex bbox of the merged shell mesh description vs render bounds; sample triangles per group."""
import os, json
import unreal as u
assert os.getpid() == ARGS['expected_pid']
m = u.load_asset('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/Bake/KarmeiYosef_31850349_34907601_4km_buildings')
d = m.get_static_mesh_description(0)
xs = []; ys = []; zs = []
for i in range(0, d.get_vertex_count(), 7):
    p = d.get_vertex_position(u.VertexID(i)); xs.append(p.x); ys.append(p.y); zs.append(p.z)
b = m.get_bounding_box()
samp = {}
for t in range(0, d.get_triangle_count(), 50000):
    g = d.get_triangle_polygon_group(u.TriangleID(t)).id_value
    vs = [d.get_vertex_position(v) for v in d.get_triangle_vertices(u.TriangleID(t))]
    samp[t] = [g, [[round(p.x), round(p.y), round(p.z)] for p in vs]]
bs = m.get_editor_property('build_settings') if hasattr(m, 'build_settings') else None
src = m.get_source_models() if hasattr(m, 'get_source_models') else None
RESULT = {'ok': True, 'desc_bbox': [[round(min(xs)), round(min(ys)), round(min(zs))], [round(max(xs)), round(max(ys)), round(max(zs))]],
          'render_bbox': [[round(b.min.x), round(b.min.y), round(b.min.z)], [round(b.max.x), round(b.max.y), round(b.max.z)]],
          'samples': samp}
try:
    sm = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    RESULT['lod_build'] = str(sm.get_lod_build_settings(m, 0))[:600]
except Exception as e:
    RESULT['lod_build_err'] = repr(e)[:200]
