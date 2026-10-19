"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef clone_v2.py (playbook 7.1: the clone
rebuilt after a regeneration). Old and new clone are explicit inputs: ARGS.old_clone_suffix and ARGS.new_clone_suffix
(area_constants.clone_map: '' = first clone, '_v2' = rebuilt clone; both required, they must differ). The old clone stays
untouched as the fallback. No level streaming of the old clone (both maps
hold copies of the same landscape); actors travel as data instead.
steps
  export      (OLD clone loaded, read-only) all actor labels/classes -> receipts/CLONE_V1_ACTORS.json; ARGS.labels -> exact
              data (actor transform, folder, every (H)ISM component: mesh, material overrides, mobility, world instance
              transforms; StaticMeshActor: mesh, overrides, transform) -> receipts/CLONE_V1_EXPORT.json. Nothing saved.
  duplicate   (any map loaded) drop the loaded map without saving, duplicate the SAVED regenerated main map to
              <clone folder>/L_<AreaId>_PCGTrial<new_clone_suffix>, named save (ARGS.main_sha256 must match; ARGS.authority
              is recorded).
              Quit afterwards (a duplicated world held in Python crashed load_level before).
  save        (NEW clone loaded) named save of the new clone map only; no dirty content allowed
  import      (NEW clone loaded) recreate the exported actors: Static chains, same meshes/overrides/transforms/folders.
              Heights are kept; ARGS.retrace true re-drops instances onto the landscape (landscape-only hits) and reports dz.
ARGS: expected_pid, script_file (client), step, old_clone_suffix, new_clone_suffix, ...
"""
import datetime, hashlib, importlib.util, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
MAIN = A.MAIN_MAP
OLD = A.clone_map(ARGS['old_clone_suffix'])                           # required, explicit (no default clone)
NEW = A.clone_map(ARGS['new_clone_suffix'])
assert OLD != NEW, ('old and new clone must differ', OLD)
EXPORT = TASK / 'receipts' / 'CLONE_V1_EXPORT.json'
f = lambda pkg: ROOT / ('Content' + pkg[5:] + '.umap')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pid = os.getpid(); assert pid == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
step = ARGS['step']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
P = lambda o: o.get_path_name().split('.')[0] if o else None


def xf(t):
    q = t.rotation
    return [round(t.translation.x, 3), round(t.translation.y, 3), round(t.translation.z, 3),
            q.x, q.y, q.z, q.w, round(t.scale3d.x, 5), round(t.scale3d.y, 5), round(t.scale3d.z, 5)]


def unxf(v):
    return u.Transform(location=u.Vector(v[0], v[1], v[2]), rotation=u.Quat(v[3], v[4], v[5], v[6]).rotator(), scale=u.Vector(v[7], v[8], v[9]))


if step == 'export':
    assert world.get_outermost().get_path_name() == OLD
    allact = [{'label': a.get_actor_label(), 'class': a.get_class().get_name(), 'folder': str(a.get_folder_path())} for a in eas.get_all_level_actors()]
    (TASK / 'receipts' / 'CLONE_V1_ACTORS.json').write_text(json.dumps(allact, indent=1), encoding='utf-8')
    out = {}
    for lab in ARGS['labels']:
        a = [x for x in eas.get_all_level_actors() if x.get_actor_label() == lab]
        assert len(a) == 1, (lab, len(a))
        a = a[0]
        rec = {'class': a.get_class().get_name(), 'folder': str(a.get_folder_path()), 'actor_xf': xf(a.get_actor_transform()), 'components': []}
        if isinstance(a, u.StaticMeshActor):
            c = a.static_mesh_component
            rec['static_mesh'] = {'mesh': P(c.get_editor_property('static_mesh')),
                                  'overrides': [P(m) for m in c.get_editor_property('override_materials')],
                                  'mobility': str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0]}
        for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
            n = c.get_instance_count()
            rec['components'].append({'name': c.get_name(), 'class': c.get_class().get_name(), 'mesh': P(c.get_editor_property('static_mesh')),
                                      'overrides': [P(m) for m in c.get_editor_property('override_materials')],
                                      'mobility': str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0],
                                      'instances': [xf(c.get_instance_transform(i, True)) for i in range(n)]})
        out[lab] = rec
    EXPORT.write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'map': OLD, 'map_sha256': sha(f(OLD)), 'actors': out}), encoding='utf-8')
    RESULT = {'ok': True, 'actors_total': len(allact), 'exported': {k: sum(len(c['instances']) for c in v['components']) for k, v in out.items()}, 'dirty': dirty()}

elif step == 'duplicate':
    assert sha(f(MAIN)) == ARGS['main_sha256'], 'main map changed'
    assert not f(NEW).exists() and not u.EditorAssetLibrary.does_asset_exist(NEW)
    assert dirty()[1] == [], dirty()
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    dup = u.EditorAssetLibrary.duplicate_asset(MAIN, NEW)
    assert dup, 'duplicate_asset failed'
    assert u.EditorLoadingAndSavingUtils.save_packages([dup.get_outermost()], False)
    del dup
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'source': MAIN, 'source_sha256': sha(f(MAIN)),
           'new_clone': NEW, 'new_sha256': sha(f(NEW)), 'old_clone_sha256': sha(f(OLD)),
           'authority': ARGS['authority']}
    (TASK / 'receipts' / 'CLONE_V2_COPY.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}

elif step == 'import':
    assert world.get_outermost().get_path_name() == NEW, world.get_outermost().get_path_name()
    D = json.loads(EXPORT.read_text())
    sds = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    retrace = bool(ARGS.get('retrace'))
    dzs = []

    def land_z(x, y):
        hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0), u.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                False, [], u.DrawDebugTrace.NONE, True)
        h = hit[1] if isinstance(hit, tuple) else hit
        t = h.to_tuple() if h is not None else None
        if not t or not t[0] or not isinstance(t[9], (u.Landscape, u.LandscapeProxy)):
            return None
        return t[4].z
    out = {}
    for lab, rec in D['actors'].items():
        assert not [x for x in eas.get_all_level_actors() if x.get_actor_label() == lab], lab + ' exists'
        at = unxf(rec['actor_xf'])
        if rec['class'] == 'StaticMeshActor':
            sm = rec['static_mesh']
            a = eas.spawn_actor_from_object(u.load_asset(sm['mesh']), at.translation, at.rotation.rotator())
            a.set_actor_scale3d(at.scale3d)
            c = a.static_mesh_component
            for i, m in enumerate(sm['overrides']):
                if m:
                    c.set_material(i, u.load_asset(m))
            c.set_mobility(u.ComponentMobility.STATIC)
        else:
            a = eas.spawn_actor_from_class(u.Actor, at.translation, at.rotation.rotator())
            top = sds.k2_gather_subobject_data_for_instance(a)[0]
            h, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=top, new_class=u.SceneComponent))
            for cr in rec['components']:
                hh, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=h, new_class=getattr(u, cr['class'])))
                c = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(hh))
                c.set_static_mesh(u.load_asset(cr['mesh']))
                for i, m in enumerate(cr['overrides']):
                    if m:
                        c.set_material(i, u.load_asset(m))
                ts = []
                for v in cr['instances']:
                    t = unxf(v)
                    if retrace:
                        z = land_z(t.translation.x, t.translation.y)
                        if z is not None:
                            dzs.append(z - t.translation.z); t = u.Transform(location=u.Vector(t.translation.x, t.translation.y, z), rotation=t.rotation.rotator(), scale=t.scale3d)
                    ts.append(t)
                c.add_instances(ts, False, True)
            rootc = a.root_component
            cs = [rootc] + [c for c in a.get_components_by_class(u.SceneComponent) if c != rootc]
            for c in cs:
                if not isinstance(c, u.BillboardComponent):
                    c.set_mobility(u.ComponentMobility.STATIC)
            for c in cs[1:]:
                if c.get_attach_parent() is None and not isinstance(c, u.BillboardComponent):
                    c.attach_to_component(rootc, '', u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, False)
        a.set_actor_label(lab); a.set_folder_path(rec['folder'])
        got = sum(c.get_instance_count() for c in a.get_components_by_class(u.InstancedStaticMeshComponent))
        want = sum(len(c['instances']) for c in rec['components'])
        assert got == want, (lab, got, want)
        out[lab] = got
    dz = sorted(abs(v) for v in dzs)
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'imported': out, 'retrace': retrace,
           'dz_cm': {'n': len(dz), 'median': dz[len(dz) // 2] if dz else None, 'max': dz[-1] if dz else None}, 'dirty': dirty()}
    (TASK / 'receipts' / 'CLONE_V2_IMPORT.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}

elif step == 'save':
    # staged named save of the NEW clone map only (crash rule: save after each stage); dirty content must be saved first
    assert world.get_outermost().get_path_name() == NEW, world.get_outermost().get_path_name()
    assert dirty()[1] == [], dirty()
    before = sha(f(NEW))
    assert u.EditorLoadingAndSavingUtils.save_map(world, NEW)
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'label': ARGS.get('label'),
           'map_sha256_before': before, 'map_sha256_after': sha(f(NEW)), 'dirty_after': dirty()}
    with open(TASK / 'receipts' / 'CLONE_V2_SAVES.jsonl', 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(rec) + '\n')
    RESULT = {'ok': True, **rec}
