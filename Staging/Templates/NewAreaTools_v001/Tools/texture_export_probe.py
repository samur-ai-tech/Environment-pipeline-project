"""In-editor, read-only for assets. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Exports ARGS.textures (asset paths) as PNG
files into ARGS.out_dir (outside Content) so their look can be judged offline. The assets are not modified or saved.
ARGS: expected_pid, textures, out_dir."""
import os
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
out = Path(ARGS['out_dir']); out.mkdir(parents=True, exist_ok=True)
d0 = sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
rows = {}
for p in ARGS['textures']:
    t = u.load_asset(p)
    f = out / (p.rsplit('/', 1)[1] + '.png')
    task = u.AssetExportTask()
    for k, v in dict(object=t, filename=str(f), automated=True, prompt=False, replace_identical=True).items():
        task.set_editor_property(k, v)
    ok = u.Exporter.run_asset_export_task(task)
    rows[p] = {'ok': bool(ok), 'file': str(f), 'bytes': f.stat().st_size if f.exists() else None}
RESULT = {'ok': True, 'exports': rows,
          'dirty_changed': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()) != d0}
