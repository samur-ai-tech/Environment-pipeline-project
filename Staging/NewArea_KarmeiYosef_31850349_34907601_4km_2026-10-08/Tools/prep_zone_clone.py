"""In-editor (Karmei Yosef operator), no map loaded: import the six zone masks into the 4 km PCG trial folder and
duplicate the saved 4 km map there (named save of the copy only; the copy is NOT loaded in this process).
ARGS: expected_pid."""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
SRC = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/L_KarmeiYosef_31850349_34907601_4km'
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
DST = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial'
SRC_SHA = 'c7c858c50ca986d8f9791d394134bc6532c02e50f1971e0a0e302dfee96fca24'
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
    for k, v in dict(filename=info['file'], destination_path=TRIAL + '/Masks', destination_name='T_KY4_Mask_' + name,
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
