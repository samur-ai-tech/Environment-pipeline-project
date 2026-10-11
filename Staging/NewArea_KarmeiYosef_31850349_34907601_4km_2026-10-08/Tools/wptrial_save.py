"""In-editor (Karmei Yosef operator, WP/per-building trial 2026-10-10): named saves for the trial only - dirty content under the
trial folder and its World Partition mirrors (__ExternalActors__/__ExternalObjects__ for the trial), then the loaded trial map.
Refuses anything else dirty. Writes receipts/WPTRIAL_SAVE_<label>.json. ARGS: expected_pid, label."""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
AREA = '/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/'
OK = ('/Game' + AREA, '/Game/__ExternalActors__' + AREA, '/Game/__ExternalObjects__' + AREA)
# ARGS.extra_ok: extra owned prefixes for one save (e.g. the clone's Vegetation copies after lowest_lod.py)
OK = OK + tuple(p for p in ARGS.get('extra_ok', []) if p.startswith('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/Vegetation/'))
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
wmap = world.get_outermost().get_path_name()
assert wmap.startswith(OK[0]), wmap
maps = [x for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
content = [x for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
bad = [x.get_path_name() for x in maps + content if not x.get_path_name().startswith(OK)]
assert not bad, 'dirty outside the trial: %s' % bad[:20]
t0 = datetime.datetime.now()
if content:
    assert u.EditorLoadingAndSavingUtils.save_packages(content, False)
assert u.EditorLoadingAndSavingUtils.save_map(world, wmap)
secs = (datetime.datetime.now() - t0).total_seconds()
f = ROOT / ('Content' + wmap[5:] + '.umap')
ext = ROOT / ('Content/__ExternalActors__' + AREA)
rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'label': ARGS['label'], 'map': wmap,
       'saved_content': len(content), 'saved_maps': [x.get_path_name() for x in maps], 'save_seconds': round(secs, 1),
       'map_sha256': hashlib.sha256(f.read_bytes()).hexdigest(), 'map_bytes': f.stat().st_size,
       'external_actor_files': sum(1 for _ in ext.rglob('*.uasset')) if ext.exists() else 0,
       'dirty_after': [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()] +
                      [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
(TASK / 'receipts' / ('WPTRIAL_SAVE_%s.json' % ARGS['label'])).write_text(json.dumps(rec, indent=2), encoding='utf-8')
RESULT = {'ok': True, **rec}
