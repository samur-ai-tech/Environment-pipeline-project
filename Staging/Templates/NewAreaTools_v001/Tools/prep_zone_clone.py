"""In-editor, no map loaded. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef tool (first clone, playbook 7.1).
Import the six zone masks (MASK_PREFIX) into the PCG clone folder (TRIAL_ROOT) and duplicate the saved main map there as the
FIRST clone L_<AreaId>_PCGTrial (area_constants.clone_map(''), playbook 1.2; named save of the copy only; the copy is NOT
loaded in this process). The main map's expected sha256 is an input.
ARGS: expected_pid, script_file (client), expected_sha (64 hex, the saved main map)."""
import datetime, hashlib, importlib.util, json, os, re
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
SRC = A.MAIN_MAP
TRIAL = A.TRIAL_ROOT
DST = A.clone_map('')                                                  # the first clone (explicit, playbook 1.2)
SRC_SHA = ARGS['expected_sha']
assert isinstance(SRC_SHA, str) and re.fullmatch(r'[0-9a-f]{64}', SRC_SHA), 'ARGS.expected_sha (64 hex) is required'
umap = lambda pkg: ROOT / ('Content' + pkg[5:] + '.umap')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert not world.get_outermost().get_path_name().startswith('/Game/Project/Areas/'), world.get_path_name()
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
assert dirty() == ([], []), dirty()
assert sha(umap(SRC)) == SRC_SHA and not umap(DST).exists()
masks = json.loads((TASK / 'Zones/MASKS.json').read_text(encoding='utf-8'))
saved = []
for name, info in masks.items():
    t = u.AssetImportTask()
    for k, v in dict(filename=info['file'], destination_path=TRIAL + '/Masks', destination_name=A.MASK_PREFIX + name,
                     automated=True, replace_existing=False, save=False).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = list(t.get_objects())[0]
    tex.set_editor_property('srgb', False)
    tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_GRAYSCALE)
    tex.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('filter', u.TextureFilter.TF_NEAREST)
    tex.set_editor_property('never_stream', True)
    tex.set_editor_property('address_x', u.TextureAddress.TA_CLAMP); tex.set_editor_property('address_y', u.TextureAddress.TA_CLAMP)
    assert u.EditorLoadingAndSavingUtils.save_packages([tex.get_outermost()], False)
    saved.append(tex.get_outermost().get_name())
    del tex
dup = u.EditorAssetLibrary.duplicate_asset(SRC, DST)
assert dup
pkg = dup.get_outermost()
del dup
if u.EditorLoadingAndSavingUtils.get_dirty_content_packages() or u.EditorLoadingAndSavingUtils.get_dirty_map_packages():
    assert u.EditorLoadingAndSavingUtils.save_packages([pkg], False)
del pkg
assert umap(DST).exists() and sha(umap(SRC)) == SRC_SHA
saved.append(DST)
receipt = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'saved': saved, 'clone_sha256': sha(umap(DST)),
           'source_unchanged': True, 'dirty_after': dirty(), 'note': 'clone references the 4 km area Bake/ meshes and ground MI'}
(TASK / 'receipts' / 'ZONE_CLONE_PREP.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
RESULT = {'ok': True, **receipt}
