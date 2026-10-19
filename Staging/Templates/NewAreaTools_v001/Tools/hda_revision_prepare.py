"""In-editor on the MAIN area map. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat hda_v002_prepare.py
(itself a fork of the Karmei Yosef one). Prepares an instantiate run for a NEW generator revision of this area
(area_constants.py HDA_VERSION, replacing HDA_PREVIOUS_VERSION that the profile names now).
A menu run REUSES an existing HoudiniAssetActor (regenerate mode never reads profile['hda'], geocity_bank_workflow.py:1019-1038),
so the new revision is used only in instantiate mode: the previous actor must be gone and the map saved. A freshly
instantiated actor has no bake state, so the old Landscape must be gone too (else the bake renames it '<name>_old_0' ->
'Duplicate Landscapes after bake'), and so must any split Bldg_ actors outside the ledger (holding bank meshes ->
'Overlapping native bank copies'). The road StaticMeshActor and the bank_instances actors are KEPT: the sealed run retires
them by LAST_SUCCESSFUL_WORKFLOW_STATE.json baked_actor_paths (ledger). All generator constants come from hda_edits.py (E),
loaded from its file at each call.
'import' first asserts TRACK_MI (MaterialInstanceConstant, parent E.TRACK_MI_PARENT) and ends with nothing dirty;
'remove_actor' asserts identity by the actor label + package_file == profile source (houdini_asset is unreadable since the
Cookable move; kept for information only) and records typed parameter values and the transform; an unknown step refuses.
steps
  import                 import E.DEST as E.UNREAL_HDA (HoudiniAssetFactory, replace_existing False, no cook), named save of
                         that package only, uasset sha recorded
  remove_actor           record the single HoudiniAssetActor (label, path, transform, all parameter values readable through the
                         official API) to receipts/HDA_PREVIOUS_ACTOR_BEFORE_<VERSION>.json, destroy it, named save of the map
  clear_for_instantiate  record the Landscape '<AREA>_landscape' and the ARGS.bldg_labels actors (transform, components,
                         meshes, instance counts, override materials) plus a dry run of the sealed retirement/overlap logic
                         (geocity_bank_workflow.py:875, :883-890) to receipts/CLEAR_BEFORE_<VERSION>.json, destroy exactly
                         those, assert the kept actors (ARGS.expected_kept_classes: bank_instances + road at their ledger
                         paths + sky), named save of the map only
ARGS: expected_pid, script_file (client), step, authority (Aviv's words); clear_for_instantiate also ledger_actor_count
(baked_actor_count of the archived ledger), bank_instances (number of bank_instances_<i> actors), bldg_labels (list, may be
empty), expected_kept_classes ({class: count} after the destroy, e.g. {"Actor": <bank_instances>, "BP_EnvironmentSky_C": 1,
"StaticMeshActor": 1}).
"""
import collections, datetime, hashlib, importlib.util, json, os, sys
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('hda_edits', TOOLS.parent / 'hda_edits.py')
E = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(E)  # generator constants as on disk now (loads area_constants)
TASK = E.A.task_dir(TOOLS, ROOT)
AREA = E.A.AREA_ROOT
MAP = E.A.MAIN_MAP
PFX = MAP + '.' + MAP.rsplit('/', 1)[1] + ':PersistentLevel.'
MAPFILE = ROOT / ('Content' + MAP[5:] + '.umap')
V2 = E.UNREAL_HDA
assert E.UNREAL_HDA_PREVIOUS, 'area_constants.py HDA_PREVIOUS_VERSION is None: no previous revision to replace'
V1_LABEL = E.UNREAL_HDA_PREVIOUS.rsplit('/', 1)[1]
SRC = E.DEST
PROFILE = ROOT / E.A.PROFILE_REL
REC = json.loads((TASK / E.RECORD).read_text(encoding='utf-8-sig'))
VTAG = E.VERSION.upper()
ACTOR_REC, CLEAR_REC = 'HDA_PREVIOUS_ACTOR_BEFORE_%s.json' % VTAG, 'CLEAR_BEFORE_%s.json' % VTAG
AUTH = ARGS['authority']
assert isinstance(AUTH, str) and AUTH.strip(), 'ARGS.authority (Aviv\'s words) is required'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
P = lambda o: o.get_path_name() if o else None
utc = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
hist = lambda xs: dict(sorted(collections.Counter(a.get_class().get_name() for a in xs).items()))
wr = lambda name, obj: (TASK / 'receipts' / name).write_text(json.dumps(obj, indent=2, default=str), encoding='utf-8')
pid = os.getpid(); assert pid == ARGS['expected_pid'], (pid, ARGS['expected_pid'])
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAP, world.get_outermost().get_path_name()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
step = ARGS['step']
assert V2.startswith(AREA + '/HDA/') and E.UNREAL_HDA_PREVIOUS.startswith(AREA + '/HDA/'), (V2, E.UNREAL_HDA_PREVIOUS)
assert V1_LABEL != V2.rsplit('/', 1)[1], V1_LABEL
assert (Path(REC['path']) == SRC and REC['unreal_asset'] == V2 and REC['type'] == E.TYPE and REC['track_material'] == E.TRACK_MI
        and REC.get('verified_by_separate_script') is True), '%s does not match hda_edits.py' % E.RECORD
assert sha(SRC) == REC['sha256'], 'new hdalc changed since ' + E.RECORD


def xf(a):
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    return {'location_cm': [l.x, l.y, l.z], 'rotation_pitch_yaw_roll': [r.pitch, r.yaw, r.roll], 'scale': [s.x, s.y, s.z]}


def safe(f, default=None):
    try:
        return f()
    except Exception as exc:
        return 'unreadable ' + repr(exc)[:120] if default is None else default


if step == 'import':
    assert dirty() == ([], []), dirty()
    assert u.EditorAssetLibrary.does_asset_exist(E.TRACK_MI), 'track MI missing (create it first): ' + E.TRACK_MI
    mi = u.load_asset(E.TRACK_MI)
    assert mi and mi.get_class().get_name() == 'MaterialInstanceConstant', ('track MI class', P(mi), mi and mi.get_class().get_name())
    assert P(mi) == E.TRACK_MI, (P(mi), E.TRACK_MI)
    parent = mi.get_editor_property('parent')
    assert parent and P(parent).split('.')[0] == E.TRACK_MI_PARENT, ('track MI parent', P(parent), E.TRACK_MI_PARENT)
    bc = u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, 'BaseColorTex')
    ao = u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, 'AOTex')
    assert bc and P(bc).split('.')[0] != '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_basecolor' and ao and \
        P(ao).split('.')[0] != '/Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_AO', ('track MI still inherits the asphalt textures', P(bc), P(ao))
    assert not u.EditorAssetLibrary.does_asset_exist(V2), 'new revision already imported: ' + V2
    assert dirty() == ([], []), ('loading the track MI dirtied packages', dirty())
    t = u.AssetImportTask()
    for k, v in dict(filename=str(SRC), destination_path=V2.rsplit('/', 1)[0], destination_name=V2.rsplit('/', 1)[1], automated=True,
                     replace_existing=False, save=False, factory=u.HoudiniAssetFactory()).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    hda = u.load_asset(V2); assert hda and hda.get_class().get_name() == 'HoudiniAsset', hda
    assert u.EditorLoadingAndSavingUtils.save_packages([hda.get_outermost()], False)
    f = ROOT / ('Content' + V2[5:] + '.uasset')
    d = dirty()
    assert d == ([], []), ('dirty after the named HDA save', d, sha(f))
    RESULT = {'ok': True, 'asset': V2, 'source': str(SRC), 'source_sha256': REC['sha256'], 'uasset_sha256': sha(f),
              'track_mi': P(mi), 'track_mi_parent': P(parent), 'authority': AUTH, 'dirty': d}

elif step == 'remove_actor':
    assert dirty() == ([], []), dirty()
    prof = json.loads(PROFILE.read_text(encoding='utf-8-sig'))
    assert prof['map'] == MAP and prof['hda'] == E.UNREAL_HDA_PREVIOUS, ('profile must still name the previous revision here', prof['map'], prof['hda'])
    hd = [a for a in eas.get_all_level_actors() if a.get_class().get_name() == 'HoudiniAssetActor']
    assert len(hd) == 1, ('expected exactly 1 HoudiniAssetActor', [a.get_path_name() for a in hd])
    a = hd[0]
    assert a.get_actor_label() == V1_LABEL, ('not the previous-revision HDA actor', a.get_actor_label(), V1_LABEL)
    assert a.get_path_name() == PFX + 'HoudiniAssetActor_0', ('not the approved HoudiniAssetActor_0', a.get_path_name())
    try:                                                                  # information only (HoudiniAsset_DEPRECATED since the Cookable)
        comp = a.get_component_by_class(u.HoudiniAssetComponent)
        asset = comp.get_editor_property('houdini_asset').get_path_name()
    except Exception as exc:
        asset = 'unreadable ' + repr(exc)[:120]
    w = u.HoudiniPublicAPIAssetWrapper.create_wrapper(None, a)            # same call as geocity_bank_workflow.py:1026
    assert w, 'no official API wrapper for ' + a.get_path_name()
    package_file = w.get_string_parameter_value('package_file')         # same identity read as geocity_bank_workflow.py:420
    assert Path(package_file).resolve() == Path(prof['source']).resolve(), ('previous actor source differs from the profile', package_file, prof['source'])
    params = {}
    for name, val in w.get_parameter_tuples().items():
        typed = {}
        for k in ('bool_values', 'int32_values', 'float_values', 'string_values'):
            v = safe(lambda: list(val.get_editor_property(k)))
            if v:
                typed[k] = v
        params[str(name)] = typed or {'repr': safe(lambda: str(val)[:400])}
    before = {'utc': utc(), 'pid': pid, 'map': MAP, 'map_sha256_before': sha(MAPFILE), 'actor_label': a.get_actor_label(),
              'actor_path': a.get_path_name(), 'transform': xf(a), 'houdini_asset': asset, 'package_file': package_file,
              'package_file_equals_profile_source': True, 'parameters': params, 'authority': AUTH,
              'reason': 'regenerate mode reuses the previous-revision actor; the new revision needs instantiate mode'}
    _old = TASK / 'receipts' / ACTOR_REC
    if _old.exists():                                                     # keep earlier evidence (review fix)
        _old.rename(_old.with_name(ACTOR_REC[:-5] + '_superseded_%s.json' % datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')))
    wr(ACTOR_REC, before)
    assert eas.destroy_actor(a)
    assert not [x for x in eas.get_all_level_actors() if x.get_class().get_name() == 'HoudiniAssetActor']
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP)
    d = dirty()
    before.update(map_sha256_after=sha(MAPFILE), dirty_after=d, hda_actors_after=0)
    wr(ACTOR_REC, before)
    assert not [x for x in eas.get_all_level_actors() if x.get_class().get_name() == 'HoudiniAssetActor']
    assert d == ([], []), ('dirty after the named map save', d)
    RESULT = {'ok': True, 'removed': before['actor_path'], 'label': before['actor_label'], 'asset_was': asset,
              'map_sha256_after': before['map_sha256_after'], 'parameters_recorded': len(params), 'dirty': d}

elif step == 'clear_for_instantiate':
    assert dirty() == ([], []), dirty()
    acts = eas.get_all_level_actors()
    assert not [P(a) for a in acts if a.get_class().get_name() == 'HoudiniAssetActor'], 'run remove_actor first'
    LEDGER = TASK / 'LAST_SUCCESSFUL_WORKFLOW_STATE.json'                  # finished run-1 ledger; never the live WORKFLOW_STATE.json
    led = json.loads(LEDGER.read_text(encoding='utf-8-sig'))
    KP, KM = 'baked_actor_paths', 'baked_mesh_counts'
    assert led.get('phase') == 'baked_saved_verified' and Path(led.get('profile', '')).resolve() == PROFILE.resolve(), (led.get('phase'), led.get('profile'))
    assert isinstance(led.get(KP), list) and len(led[KP]) == len(set(led[KP])) == led.get('baked_actor_count') == ARGS['ledger_actor_count'], ('ledger ' + KP, len(led.get(KP) or []))
    assert isinstance(led.get(KM), dict) and led[KM], 'ledger ' + KM
    assert all(x.startswith(PFX) for x in led[KP]), 'ledger actor paths outside the named map'
    baked, bank_meshes = set(led[KP]), set(led[KM])
    LAND, ROAD = PFX + E.AREA + '_landscape', PFX + E.AREA + '_road_surfaces'
    NBANK = int(ARGS['bank_instances'])                                  # this run's bank_instances_0..N-1 (template: an input)
    BANK = {PFX + 'bank_instances_%d' % i for i in range(NBANK)}
    BLDG = list(ARGS['bldg_labels'])                                      # split Bldg_ actors outside the ledger (may be empty)
    TARGET = dict(ARGS['expected_kept_classes'])                           # kept actors by class after the destroy
    NKEEP = sum(TARGET.values())
    assert LAND in baked and ROAD in baked and BANK <= baked, 'ledger lacks the landscape / road / bank_instances paths'
    live = {P(a): a for a in acts}
    assert len(live) == len(acts), 'duplicate actor identities'
    lands = [a for a in acts if isinstance(a, u.LandscapeProxy)]
    assert [(P(a), a.get_class().get_name()) for a in lands] == [(LAND, 'Landscape')], \
        ('expected exactly the Landscape ' + LAND, [(P(a), a.get_class().get_name()) for a in lands])
    bldg = sorted((a for a in acts if a.get_actor_label().startswith('Bldg_')), key=lambda a: a.get_actor_label())
    assert [a.get_actor_label() for a in bldg] == sorted(BLDG) and all(a.get_class().get_name() == 'Actor' for a in bldg), \
        ('expected exactly the Actors ' + ', '.join(BLDG), [(P(a), a.get_actor_label(), a.get_class().get_name()) for a in bldg])
    assert ROAD in live and live[ROAD].get_class().get_name() == 'StaticMeshActor', ('road actor', ROAD, ROAD in live and live[ROAD].get_class().get_name())
    assert BANK <= set(live) and all(live[x].get_class().get_name() == 'Actor' and live[x].get_actor_label().startswith('bank_instances') for x in BANK), \
        'bank_instances are not live at their ledger paths'

    def owners(actors):                                                   # dry run of geocity_bank_workflow.py:883-890 (full object paths)
        out = set()
        for a in actors:
            for c in a.get_components_by_class(u.StaticMeshComponent):
                if P(c.static_mesh) in bank_meshes:
                    out.add(P(a)); break
        return out

    def comp_rec(c):
        return {'name': c.get_name(), 'class': c.get_class().get_name(), 'mesh': safe(lambda: P(c.static_mesh)),
                'instances': safe(lambda: c.get_instance_count() if isinstance(c, u.InstancedStaticMeshComponent) else 1),
                'override_materials': safe(lambda: [P(m) for m in (c.get_editor_property('override_materials') or [])]),
                'materials': safe(lambda: [P(c.get_material(i)) for i in range(c.get_num_materials())])}

    def actor_rec(a):
        r = {'path': P(a), 'class': a.get_class().get_name(), 'label': a.get_actor_label(), 'in_ledger': P(a) in baked,
             'folder': safe(lambda: str(a.get_folder_path())), 'transform': xf(a),
             'component_classes': dict(sorted(collections.Counter(c.get_class().get_name() for c in a.get_components_by_class(u.ActorComponent)).items())),
             'mesh_components': [comp_rec(c) for c in a.get_components_by_class(u.StaticMeshComponent)]}
        if isinstance(a, u.LandscapeProxy):
            r['landscape_material'] = safe(lambda: P(a.get_editor_property('landscape_material')))
        return r

    kill = lands + bldg
    kill_paths = [P(a) for a in kill]
    owners_before = owners(acts)
    assert owners_before - set(kill_paths) <= baked, ('live bank-mesh owners outside the ledger would survive the run',
                                                       sorted(owners_before - set(kill_paths) - baked))
    keep = [a for a in acts if P(a) not in kill_paths]
    assert len(keep) == NKEEP and hist(keep) == TARGET, ('predicted kept actors', len(keep), hist(keep))
    assert {P(a) for a in keep if a.get_class().get_name() == 'Actor'} == BANK, 'kept plain Actors are not exactly the bank_instances'
    assert [P(a) for a in keep if a.get_class().get_name() == 'StaticMeshActor'] == [ROAD], 'kept StaticMeshActor is not the ledger road'
    rec = {'schema': 'newarea.clear_for_instantiate.v1', 'version': E.VERSION, 'status': 'RECORDED_BEFORE_DESTROY', 'utc': utc(), 'pid': pid, 'map': MAP,
           'authority': AUTH, 'map_sha256_before': sha(MAPFILE), 'ledger': str(LEDGER), 'ledger_sha256': sha(LEDGER),
           'ledger_keys_used': {'actor_paths': KP, 'mesh_counts': KM}, 'ledger_baked_actor_count': len(baked),
           'ledger_bank_mesh_count': len(bank_meshes), 'actor_count_before': len(acts), 'classes_before': hist(acts),
           'to_destroy': [actor_rec(a) for a in kill],
           'dry_run': {'bank_mesh_owners_before': sorted(owners_before), 'bank_mesh_owners_not_in_ledger': sorted(owners_before - baked),
                       'owners_minus_destroyed_subset_of_ledger': True, 'landscape_path': LAND, 'road_path': ROAD,
                       'landscape_road_and_bank_instances_in_ledger': True, 'predicted_kept_count': len(keep),
                       'predicted_kept_classes': hist(keep)},
           'kept_retired_by_sealed_run_ledger': sorted(BANK | {ROAD})}
    _old = TASK / 'receipts' / CLEAR_REC
    if _old.exists():                                                     # keep earlier evidence (review fix)
        _old.rename(_old.with_name(CLEAR_REC[:-5] + '_superseded_%s.json' % datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')))
    wr(CLEAR_REC, rec)
    try:
        for a, path in zip(kill, kill_paths):
            assert eas.destroy_actor(a), 'destroy failed: ' + path
        now = eas.get_all_level_actors()
        assert len(now) == NKEEP and hist(now) == TARGET, ('after destroy', len(now), hist(now))
        assert {P(a) for a in now if a.get_class().get_name() == 'Actor'} == BANK and all(
            a.get_actor_label().startswith('bank_instances') for a in now if a.get_class().get_name() == 'Actor'), 'plain Actors after destroy'
        assert [P(a) for a in now if a.get_class().get_name() == 'StaticMeshActor'] == [ROAD], 'road after destroy'
        assert not [P(a) for a in now if isinstance(a, u.LandscapeProxy) or a.get_class().get_name() == 'HoudiniAssetActor'
                    or a.get_actor_label().startswith('Bldg_')], 'Landscape / HDA / Bldg_ left after destroy'
        assert owners(now) <= baked, ('bank-mesh owners outside the ledger after destroy', sorted(owners(now) - baked))
        assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'named map save failed'
    except Exception as exc:
        rec.update(status='FAILED_AFTER_RECORD', error=repr(exc)[:2000], utc_failed=utc(),
                   classes_now=hist(eas.get_all_level_actors()), dirty_now=dirty(), map_sha256_now=sha(MAPFILE))
        wr(CLEAR_REC, rec)
        raise
    now = eas.get_all_level_actors()
    d = dirty()
    rec.update(status='CLEARED_SAVED', utc_after=utc(), destroyed=kill_paths, map_sha256_after=sha(MAPFILE),
               actor_count_after=len(now), classes_after=hist(now), bank_mesh_owners_after=sorted(owners(now)), dirty_after=d)
    wr(CLEAR_REC, rec)
    assert d == ([], []), ('dirty after the named map save', d)
    assert len(now) == NKEEP and hist(now) == TARGET and owners(now) <= baked, ('after save', len(now), hist(now))
    RESULT = {'ok': True, 'destroyed': kill_paths, 'actor_count_after': len(now), 'classes_after': hist(now),
              'map_sha256_before': rec['map_sha256_before'], 'map_sha256_after': rec['map_sha256_after'], 'dirty': d,
              'receipt': str(TASK / 'receipts' / CLEAR_REC)}

else:
    raise AssertionError('unknown step %r (import | remove_actor | clear_for_instantiate)' % step)
