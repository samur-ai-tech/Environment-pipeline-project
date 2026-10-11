"""In-editor (Karmei Yosef operator, session 4a6a1d0c), 2026-10-08. Fork of the manager's start_area_generation.py: start the ordinary GeoCity generation of the loaded area map
through the sealed menu action geocity_editor_action.generate_current_area(). Fork of the bank owner's
start_regeneration.py, generalized to any area profile (ARGS.profile_path) and allowing 0 (instantiate) or 1
(regenerate) HoudiniAssetActor. Checks BEFORE the call: world == profile map; exactly one persistent profile matches
the world; nothing dirty; runtime guard verify(); no active GeoCity run; table == AnyArea; optional expected_digest;
RoadBLD phase disabled in the profile; timeout in [600, 43200]; autosave off; Houdini cooking paused; last lease line
OWNER=NONE; this is the only Unreal editor process. The menu action appends its own GEOCITY_MENU lease line; this script
never writes EDITOR_OWNER.txt and never reads the live WORKFLOW_STATE.json / BUILD_STATE.json.
ARGS: label, profile_path (project-relative), expected_digest (optional 64 hex), expected_pid (client).
"""
import datetime, hashlib, json, os, re, subprocess
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
TABLE = '/Game/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea'
LEASE = ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt'
STATE_KEYS = ('phase', 'pid', 'utc', 'operation_timeout_seconds', 'operation_started_epoch', 'lease_at_start',
              'profile_sha256_at_start', 'reviewed_dirty_packages', 'official_engine_connected', 'error')


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def p(obj):
    return obj.get_path_name() if hasattr(obj, 'get_path_name') else str(obj)


def lease_tail():
    lines = [line for line in LEASE.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    return lines[-1] if lines else ''


def lease_fields(line):
    return dict(part.split('=', 1) for part in line.split() if '=' in part)


def unreal_processes():
    out = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                          "Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue | ForEach-Object { $_.ProcessName + ' ' + $_.Id }"],
                         capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    editors, cmds = [], []
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].isdigit():
            (cmds if parts[0].lower().endswith('-cmd') else editors).append(int(parts[1]))
    return {'editor': sorted(editors), 'cmd': sorted(cmds)}


def busy_runs(bank, roads):
    busy = [r for r in getattr(bank, 'ACTIVE', []) if not str(r.state.get('phase', '')).startswith(('baked_saved', 'failed', 'released'))]
    busy += [r for r in getattr(roads, 'ACTIVE', []) if not str(getattr(r, 'state', {}).get('phase', '')).startswith(('failed', 'released', 'completed'))]
    return [str(getattr(r, 'state', {}).get('phase')) for r in busy]


assert isinstance(ARGS, dict) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', str(ARGS.get('label', ''))), 'ARGS.label required'
pid = os.getpid()
assert pid == ARGS['expected_pid'], (pid, ARGS['expected_pid'])
a = json.loads((TASK / 'ASSIGNMENT_RUN.json').read_text(encoding='utf-8-sig'))
assert a.get('assigned_editor_PID') == pid and a.get('editor_live') is True and a.get('released_utc') is None, a
assert a.get('generation_authorized') is True, a.get('generation_authorized')
PROFILE = ROOT / ARGS['profile_path']
profile_bytes = PROFILE.read_bytes()
profile = json.loads(profile_bytes.decode('utf-8-sig'))
release = profile.get('release') or {}
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == profile['map'], world.get_path_name()
matching = [str(f) for f in sorted((ROOT / 'Staging/ModelBank').glob('*/AREA_PROFILE.json'))
            if json.loads(f.read_text(encoding='utf-8-sig')).get('map') == profile['map']]
assert matching == [str(PROFILE)], 'Exactly this one persistent profile must match the world: %s' % matching
dirty = (sorted(p(x) for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
         sorted(p(x) for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
assert dirty == ([], []), 'Dirty packages before the generation: %s' % (dirty,)
import geocity_runtime_guard
geocity_runtime_guard.verify()
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as roads
assert not busy_runs(bank, roads), 'A GeoCity run is active: %s' % busy_runs(bank, roads)
assert profile['table'] == TABLE, profile['table']
if ARGS.get('expected_digest'):
    assert profile.get('catalog_sha256') == ARGS['expected_digest'] == release.get('catalog_sha256'), \
        (profile.get('catalog_sha256'), release.get('catalog_sha256'))
assert not (profile.get('roadbld_workflow') or {}).get('enabled'), 'This tool covers areas without the RoadBLD phase'
timeout = profile.get('operation_timeout_seconds', 600)
assert isinstance(timeout, int) and not isinstance(timeout, bool) and 600 <= timeout <= 43200, timeout
settings = u.get_default_object(u.load_class(None, '/Script/UnrealEd.EditorLoadingSavingSettings'))
assert not settings.get_editor_property('bAutoSaveEnable'), 'Editor autosave must be off (launch ini)'
api = u.HoudiniPublicAPIBlueprintLib.get_api()
assert api, 'Houdini public API is unavailable'
api.pause_asset_cooking()
assert api.is_asset_cooking_paused(), 'Houdini cooking did not pause'
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
hdas = [p(x) for x in actors if x.get_class().get_name() == 'HoudiniAssetActor']
assert len(hdas) <= 1, 'At most one HoudiniAssetActor is allowed: %s' % hdas
tail = lease_tail()
assert lease_fields(tail).get('OWNER') == 'NONE', 'Last EDITOR_OWNER.txt line is not OWNER=NONE: ' + tail
procs = unreal_processes()
assert procs == {'editor': [pid], 'cmd': []}, 'This must be the only Unreal editor process: %s' % procs

receipts = TASK / 'receipts'
receipts.mkdir(exist_ok=True)
pre = {'schema': 'environmentpipeline.manager_generation.v1', 'stage': 'preflight', 'pid': pid, 'utc': utc(),
       'label': ARGS['label'], 'map': profile['map'], 'profile': str(PROFILE), 'profile_sha256': hashlib.sha256(profile_bytes).hexdigest(),
       'dirty_before': dirty, 'auto_save': False, 'cooking_paused': True, 'editor_processes': procs, 'lease_tail_before': tail,
       'road_provider': profile.get('road_provider'), 'roadbld_workflow_enabled': False, 'table': profile['table'],
       'release_id': release.get('id'), 'catalog_sha256': profile.get('catalog_sha256'), 'effective_operation_timeout_seconds': timeout,
       'hda_actors': hdas, 'action': 'regenerate' if hdas else 'instantiate', 'runtime_guard': 'verify() passed'}
with open(receipts / ('GENERATION_PREFLIGHT_%s_%s.json' % (ARGS['label'], stamp())), 'x', encoding='utf-8') as stream:
    json.dump(pre, stream, indent=2, default=str)
a['status'] = 'REGEN_ACTIVE'
(TASK / 'ASSIGNMENT_RUN.json').write_text(json.dumps(a, indent=2), encoding='utf-8')

import geocity_editor_action
count_before = len(bank.ACTIVE)
started_utc = utc()
returned = geocity_editor_action.generate_current_area()
run = bank.ACTIVE[-1] if len(bank.ACTIVE) > count_before else None
started = (run is not None and run.watch_tick is not None and not str(run.state.get('phase', '')).startswith('failed'))
start = {'schema': pre['schema'], 'stage': 'start', 'pid': pid, 'label': ARGS['label'], 'utc_call': started_utc, 'utc_end': utc(),
         'status': 'GENERATION_STARTED' if started else 'GENERATION_START_FAILED', 'returned_run': returned is not None,
         'run_state': {k: run.state.get(k) for k in STATE_KEYS} if run is not None else None, 'lease_tail_after': lease_tail(),
         'note': None if started else 'generate_current_area returned without a running operation; its modal dialog and the editor log hold the reason'}
with open(receipts / ('GENERATION_START_%s_%s.json' % (ARGS['label'], stamp())), 'x', encoding='utf-8') as stream:
    json.dump(start, stream, indent=2, default=str)
RESULT = {'ok': started, 'status': start['status'], 'run_state': start['run_state'], 'lease_tail_after': start['lease_tail_after']}
assert started, 'Generation did not start; see receipts/GENERATION_START_*.json'
