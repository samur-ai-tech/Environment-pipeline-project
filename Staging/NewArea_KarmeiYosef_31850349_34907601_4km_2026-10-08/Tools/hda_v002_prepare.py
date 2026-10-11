"""In-editor on the MAIN 4 km map (Karmei Yosef operator, 2026-10-11). Aviv: road 44 by the generator ("Generator builds it",
"Yes, full generator route"). A menu run REUSES an existing HoudiniAssetActor (regenerate mode never reads profile['hda'],
geocity_bank_workflow.py:1019-1038), so v002 is used only in instantiate mode: the v001 actor must be gone and the map saved.
Old baked actors are still removed by the run through LAST_SUCCESSFUL_WORKFLOW_STATE.json baked_actor_paths (ledger).
steps
  import        import GeoCity_city_v015_CurrentBank_4km_KY_v002.hdalc as <root>/HDA/GeoCity_city_v015_CurrentBank_4km_KY_v002
                (HoudiniAssetFactory, no cook), named save
  remove_actor  record the single HoudiniAssetActor (label, path, asset, all parameter values readable through the official
                API) to receipts/HDA_V001_ACTOR_BEFORE_V002.json, destroy it, named save of the main map only
ARGS: expected_pid, step.
"""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
AREA = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015'
MAP = AREA + '/L_KarmeiYosef_31850349_34907601_4km'
V2 = AREA + '/HDA/GeoCity_city_v015_CurrentBank_4km_KY_v002'
SRC = Path(r'C:\Users\USER\Documents\Pipeline Environment\Houdini\GeoCity_city_v015_PermanentBank\revisions\20261008_KarmeiYosef_4km\GeoCity_city_v015_CurrentBank_4km_KY_v002.hdalc')
REC = json.loads((TASK / 'HDA_SOURCE_V002.json').read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAP, world.get_outermost().get_path_name()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
step = ARGS['step']
assert sha(SRC) == REC['sha256'], 'v002 hdalc changed since HDA_SOURCE_V002.json'

if step == 'import':
    assert dirty() == ([], []), dirty()
    assert not u.EditorAssetLibrary.does_asset_exist(V2)
    t = u.AssetImportTask()
    for k, v in dict(filename=str(SRC), destination_path=V2.rsplit('/', 1)[0], destination_name=V2.rsplit('/', 1)[1], automated=True,
                     replace_existing=False, save=False, factory=u.HoudiniAssetFactory()).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    hda = u.load_asset(V2); assert hda and hda.get_class().get_name() == 'HoudiniAsset', hda
    assert u.EditorLoadingAndSavingUtils.save_packages([hda.get_outermost()], False)
    f = ROOT / ('Content' + V2[5:] + '.uasset')
    RESULT = {'ok': True, 'asset': V2, 'uasset_sha256': sha(f), 'dirty': dirty()}

elif step == 'remove_actor':
    assert dirty() == ([], []), dirty()
    hd = [a for a in eas.get_all_level_actors() if a.get_class().get_name() == 'HoudiniAssetActor']
    assert len(hd) == 1, [a.get_path_name() for a in hd]
    a = hd[0]
    try:
        comp = a.get_component_by_class(u.HoudiniAssetComponent)
        asset = comp.get_editor_property('houdini_asset').get_path_name()
    except Exception as exc:
        asset = 'unreadable ' + repr(exc)[:120]
    params = {}
    try:
        w = u.HoudiniPublicAPIAssetWrapper.create_wrapper(None, a)          # same call as geocity_bank_workflow.py:1026
        for name, val in w.get_parameter_tuples().items():
            try:
                params[str(name)] = str(val)[:400]
            except Exception as exc:
                params[str(name)] = 'unreadable ' + repr(exc)[:80]
    except Exception as exc:
        params = {'error': repr(exc)[:300]}
    before = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'map': MAP,
              'map_sha256_before': sha(ROOT / ('Content' + MAP[5:] + '.umap')), 'actor_label': a.get_actor_label(),
              'actor_path': a.get_path_name(), 'houdini_asset': asset, 'parameters': params,
              'reason': 'regenerate mode reuses this v001 actor; v002 needs instantiate mode (Aviv 2026-10-11 full generator route)'}
    (TASK / 'receipts' / 'HDA_V001_ACTOR_BEFORE_V002.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    assert eas.destroy_actor(a)
    assert not [x for x in eas.get_all_level_actors() if x.get_class().get_name() == 'HoudiniAssetActor']
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP)
    RESULT = {'ok': True, 'removed': before['actor_path'], 'asset_was': asset, 'map_sha256_after': sha(ROOT / ('Content' + MAP[5:] + '.umap')),
              'parameters_recorded': len(params), 'dirty': dirty()}
