"""In-editor (diagnosis, Karmei Yosef operator): set Nanite enabled on area-owned copies only; report LOD count/tris.
ARGS: expected_pid, meshes [paths under the clone], enabled (bool)."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
out = {}
for p in ARGS['meshes']:
    assert p.startswith('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/'), p
    m = u.load_asset(p); s = m.get_editor_property('nanite_settings')
    s.set_editor_property('enabled', bool(ARGS['enabled'])); sms.set_nanite_settings(m, s, True)
    out[p.rsplit('/', 1)[1]] = {'nanite': bool(m.get_editor_property('nanite_settings').enabled), 'lods': sms.get_lod_count(m), 'tris0': m.get_num_triangles(0)}
RESULT = {'ok': True, 'meshes': out}
