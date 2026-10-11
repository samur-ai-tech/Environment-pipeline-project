"""In-editor, read-only on Content (Karmei Yosef operator, 2026-10-10; Aviv approved "Real materials per plot").
Exports candidate ground textures from installed packs to PNG files outside Content (ARGS.out_dir) so they can be compared
and their mean colours measured offline. Vendor packages are only read. ARGS: expected_pid, out_dir, textures [paths].
"""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
out = ARGS['out_dir']; os.makedirs(out, exist_ok=True)
info = {}
for path in ARGS['textures']:
    t = u.load_asset(path)
    if not isinstance(t, u.Texture2D):
        info[path] = {'missing': True}
        continue
    dst = os.path.join(out, path.rsplit('/', 1)[1] + '.png')
    task = u.AssetExportTask()
    for k, v in dict(object=t, filename=dst, automated=True, prompt=False, replace_identical=True,
                     exporter=u.TextureExporterPNG()).items():
        task.set_editor_property(k, v)
    ok = u.Exporter.run_asset_export_task(task)
    info[path] = {'png': dst if ok else None, 'w': t.blueprint_get_size_x(), 'h': t.blueprint_get_size_y(),
                  'srgb': bool(t.get_editor_property('srgb')), 'compression': str(t.get_editor_property('compression_settings')),
                  'lod_group': str(t.get_editor_property('lod_group'))}
dirty = sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
RESULT = {'ok': True, 'textures': info, 'dirty_content': dirty[:20]}
