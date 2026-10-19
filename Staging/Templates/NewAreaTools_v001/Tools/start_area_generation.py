"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat fork of the Karmei Yosef operator's
tool, itself a fork of the manager's start_area_generation.py: start the ordinary GeoCity generation of the loaded area map
through the sealed menu action geocity_editor_action.generate_current_area(). Fork of the bank owner's
start_regeneration.py, generalized to any area profile (ARGS.profile_path) and allowing 0 (instantiate) or 1
(regenerate) HoudiniAssetActor. Checks BEFORE the call: world == profile map; exactly one persistent profile matches
the world; nothing dirty; runtime guard verify(); no active GeoCity run; table == AnyArea; optional expected_digest;
RoadBLD phase disabled in the profile; timeout in [600, 43200]; autosave off; Houdini cooking paused; last lease line
OWNER=NONE; this is the only Unreal editor process. The menu action appends its own GEOCITY_MENU lease line; this script
never writes EDITOR_OWNER.txt and never reads the live WORKFLOW_STATE.json / BUILD_STATE.json.
Expectations (El Wahat change, kept): for EVERY instantiate run all four are mandatory (template fix; before, only the El
Wahat map required them). Each one given is asserted after the checks above and before any receipt, ASSIGNMENT_RUN status or menu call,
and is recorded in the preflight receipt under 'expectations':
  expected_action ('instantiate'|'regenerate'): must equal the action the sealed menu takes (regenerate whenever a
    HoudiniAssetActor exists, else instantiate). For instantiate also: 0 Landscape (streaming proxies included), 0 actors
    labelled 'Bldg_*', and every live owner of a run-1 bank mesh (LAST_SUCCESSFUL_WORKFLOW_STATE.json baked_mesh_counts) is
    a run-1 ledger actor (its baked_actor_paths), i.e. a dry run of the sealed scoped replacement + overlap check before the
    bake. LAST_SUCCESSFUL_* is the archived copy of the last verified run, not a live ledger. The area's FIRST generation has
    neither that archive nor a WORKFLOW_STATE.json: then the ledger is empty and every live actor counts as outside it;
  expected_hda: profile['hda'] must equal it; in regenerate mode the one HoudiniAssetActor's label must also equal its asset
    name (regenerate reuses that actor and never reads profile['hda']);
  expected_track_mi: must equal TRACK_MI of hda_edits.py (the module default track material of this area's generator)
    and must load as a MaterialInstanceConstant whose parent is the spec's TRACK_MI_PARENT (Houdini Engine falls back to
    its default material silently). The spec is loaded from its file, without touching sys.path.
  Nothing may become dirty during these checks. Existing checks and the sealed call are unchanged.
ARGS: label, profile_path (project-relative), expected_digest (optional 64 hex), expected_pid (client), expected_action,
expected_hda, expected_track_mi, expected_outside_ledger_classes (all four mandatory for an instantiate), script_file (client).
"""
import datetime, hashlib, importlib.util, json, os, re, subprocess
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
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

# Expectations (see the docstring), asserted before any receipt, ASSIGNMENT_RUN status or menu call. The menu's own rule
# (geocity_editor_action.py): regenerate if any HoudiniAssetActor exists, else instantiate.
action = 'regenerate' if hdas else 'instantiate'
if action == 'instantiate':                                # template: every expectation is mandatory for every instantiate
    missing = [k for k in ('expected_action', 'expected_hda', 'expected_track_mi', 'expected_outside_ledger_classes') if ARGS.get(k) is None]
    assert not missing, 'An instantiate run requires ARGS %s' % missing
expect = {}
if ARGS.get('expected_action') is not None:
    assert ARGS['expected_action'] in ('instantiate', 'regenerate'), 'ARGS.expected_action must be instantiate or regenerate: %r' % (ARGS['expected_action'],)
    assert action == ARGS['expected_action'], 'The menu would %s (HoudiniAssetActors %s); expected_action is %s' % (action, hdas, ARGS['expected_action'])
    expect['action'] = {'expected': ARGS['expected_action'], 'derived': action, 'hda_actors': hdas}
    if action == 'instantiate':
        lands = sorted(p(x) for x in actors if isinstance(x, u.Landscape) or x.get_class().get_name() == 'LandscapeStreamingProxy')
        bldgs = sorted(p(x) + ' | ' + x.get_actor_label() for x in actors if x.get_actor_label().startswith('Bldg_'))
        assert not lands, 'Instantiate needs 0 Landscape (the bake would rename an existing one to _old_0): %s' % lands
        assert not bldgs, 'Instantiate needs 0 Bldg_* actors (outside the ledger they fail the overlap check after the bake): %s' % bldgs
        ledger_path = Path(profile['workflow_receipt']).with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json')
        # the area's first generation: no archived ledger and no workflow receipt yet (existence only; never read live)
        first_generation = not ledger_path.is_file() and not Path(profile['workflow_receipt']).exists()
        assert first_generation or ledger_path.is_file(), 'Instantiate over a previous run needs its archived ledger: %s' % ledger_path
        ledger, ledger_sha, owners, strays = (set() if first_generation else None), None, [], []
        if ledger_path.is_file():
            ledger_bytes = ledger_path.read_bytes()
            ledger_sha = hashlib.sha256(ledger_bytes).hexdigest()
            prior = json.loads(ledger_bytes.decode('utf-8-sig'))
            assert Path(prior.get('profile', '')).resolve() == PROFILE.resolve(), 'LAST_SUCCESSFUL ledger belongs to another profile: %s' % prior.get('profile')
            ledger, bank_meshes = set(prior['baked_actor_paths']), set(prior.get('baked_mesh_counts') or {})
            owners = sorted({p(x) for x in actors for c in x.get_components_by_class(u.StaticMeshComponent) if p(c.static_mesh) in bank_meshes})
            strays = [o for o in owners if o not in ledger]
        assert not strays, 'Live owners of run-1 bank meshes outside the run-1 ledger (the scoped replacement keeps them and the overlap check fails after the bake): %s' % strays
        outside_classes = sorted(x.get_class().get_name() for x in actors if p(x) not in ledger)
        if ARGS.get('expected_outside_ledger_classes') is not None:
            assert outside_classes == sorted(ARGS['expected_outside_ledger_classes']), 'Live actors outside the run-1 ledger would survive the scoped replacement: %s' % outside_classes
        expect['instantiate'] = {'landscapes': lands, 'bldg_actors': bldgs, 'first_generation': first_generation,
                                 'ledger': None if first_generation else str(ledger_path),
                                 'outside_ledger_classes': outside_classes,
                                 'ledger_sha256': ledger_sha, 'ledger_actor_count': len(ledger) if ledger is not None else None,
                                 'bank_mesh_owner_count': len(owners), 'bank_mesh_owners_outside_ledger': strays,
                                 'live_actors_outside_ledger': sorted(p(x) + ' | ' + x.get_class().get_name() for x in actors if ledger is not None and p(x) not in ledger)}
if ARGS.get('expected_hda') is not None:
    assert profile['hda'] == ARGS['expected_hda'], 'profile hda %s != expected_hda %s' % (profile['hda'], ARGS['expected_hda'])
    assert u.EditorAssetLibrary.does_asset_exist(ARGS['expected_hda']), 'HDA asset missing: ' + ARGS['expected_hda']
    hda_asset = u.load_asset(ARGS['expected_hda'])
    assert hda_asset and hda_asset.get_class().get_name() == 'HoudiniAsset', ARGS['expected_hda']
    expect['hda'] = {'expected': ARGS['expected_hda'], 'profile': profile['hda']}
    if action == 'regenerate':
        hda_labels = [x.get_actor_label() for x in actors if x.get_class().get_name() == 'HoudiniAssetActor']
        assert hda_labels == [ARGS['expected_hda'].rsplit('/', 1)[-1]], 'Regenerate reuses the existing actor and never reads profile hda; its label must be %s: %s' % (ARGS['expected_hda'].rsplit('/', 1)[-1], hda_labels)
        expect['hda']['regenerate_actor_labels'] = hda_labels
if ARGS.get('expected_track_mi') is not None:
    import importlib.util
    spec_path = TASK / 'hda_edits.py'
    spec = importlib.util.spec_from_file_location('hda_edits', spec_path)
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    assert ARGS['expected_track_mi'] == E.TRACK_MI, 'expected_track_mi must be TRACK_MI of hda_edits.py %s: %s' % (E.TRACK_MI, ARGS['expected_track_mi'])
    assert u.EditorAssetLibrary.does_asset_exist(E.TRACK_MI), 'Track MI is missing: ' + E.TRACK_MI
    mi = u.load_asset(E.TRACK_MI)
    assert isinstance(mi, u.MaterialInstanceConstant), 'Track MI is not a MaterialInstanceConstant: %s' % (mi.get_class().get_name() if mi else None)
    parent = mi.get_editor_property('parent')
    assert parent is not None and p(parent).split('.')[0] == E.TRACK_MI_PARENT, 'Track MI parent %s != %s' % (p(parent), E.TRACK_MI_PARENT)
    bc = u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, 'BaseColorTex')
    ao = u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, 'AOTex')
    assert bc and p(bc).split('.')[0] != '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_basecolor' and ao and \
        p(ao).split('.')[0] != '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_AO', ('track MI still inherits the asphalt textures', p(bc), p(ao))
    expect['track_mi'] = {'expected': ARGS['expected_track_mi'], 'path': p(mi), 'class': mi.get_class().get_name(), 'parent': p(parent),
                          'spec': str(spec_path), 'spec_sha256': hashlib.sha256(spec_path.read_bytes()).hexdigest()}
if expect:
    dirty_after = (sorted(p(x) for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                   sorted(p(x) for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
    assert dirty_after == dirty, 'The expectation checks dirtied packages: %s' % (dirty_after,)

receipts = TASK / 'receipts'
receipts.mkdir(exist_ok=True)
pre = {'schema': 'environmentpipeline.manager_generation.v1', 'stage': 'preflight', 'pid': pid, 'utc': utc(),
       'label': ARGS['label'], 'map': profile['map'], 'profile': str(PROFILE), 'profile_sha256': hashlib.sha256(profile_bytes).hexdigest(),
       'dirty_before': dirty, 'auto_save': False, 'cooking_paused': True, 'editor_processes': procs, 'lease_tail_before': tail,
       'road_provider': profile.get('road_provider'), 'roadbld_workflow_enabled': False, 'table': profile['table'],
       'release_id': release.get('id'), 'catalog_sha256': profile.get('catalog_sha256'), 'effective_operation_timeout_seconds': timeout,
       'hda_actors': hdas, 'action': action, 'runtime_guard': 'verify() passed', 'expectations': expect}
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
if not started:                                            # template fix: a failed start does not leave REGEN_ACTIVE behind
    a['status'] = 'GENERATION_START_FAILED'
    (TASK / 'ASSIGNMENT_RUN.json').write_text(json.dumps(a, indent=2), encoding='utf-8')
RESULT = {'ok': started, 'status': start['status'], 'run_state': start['run_state'], 'lease_tail_after': start['lease_tail_after'],
          'action': action, 'expectations': expect}
assert started, 'Generation did not start; see receipts/GENERATION_START_*.json'
