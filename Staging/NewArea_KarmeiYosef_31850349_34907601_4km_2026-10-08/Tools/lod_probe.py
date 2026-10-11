"""In-editor, read-only (Karmei Yosef operator), 2026-10-09: per-LOD sections/materials and screen sizes of vegetation meshes,
to see whether any LOD drops leaves. ARGS: expected_pid, meshes [paths]."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
out = {}
for p in ARGS['meshes']:
    m = u.load_asset(p)
    if not m:
        out[p] = None; continue
    slots = [str(s.get_editor_property('material_slot_name')) for s in m.get_editor_property('static_materials')]
    lods = []
    for l in range(sms.get_lod_count(m)):
        secs = m.get_num_sections(l)
        mats = []
        for s in range(secs):
            try:
                idx = m.get_section_info(l, s).get_editor_property('material_index') if hasattr(m, 'get_section_info') else None
            except Exception:
                idx = None
            mats.append(idx)
        lods.append({'lod': l, 'tris': m.get_num_triangles(l), 'sections': secs})
    try:
        ss = [round(x, 3) for x in sms.get_lod_screen_sizes(m)]
    except Exception as exc:
        ss = repr(exc)[:60]
    s = m.get_editor_property('nanite_settings')
    out[p.rsplit('/', 1)[1]] = {'nanite': bool(s.enabled), 'slots': slots, 'lods': lods, 'screen_sizes': ss,
                                'materials': [ (m.get_material(i).get_path_name().rsplit('/', 1)[1] if m.get_material(i) else None) for i in range(len(slots))]}
RESULT = {'ok': True, 'meshes': out}
