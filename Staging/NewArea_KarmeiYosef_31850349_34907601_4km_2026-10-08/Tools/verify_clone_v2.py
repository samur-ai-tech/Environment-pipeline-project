"""In-editor, read-only (Karmei Yosef operator, 2026-10-11): fresh-reopen check of the rebuilt clone
L_KarmeiYosef_31850349_34907601_4km_PCGTrial_v2. Per labelled actor: instance totals, component mobility, detached parts;
landscape material; PCG volume output; landscapes / HDA actors; dirty packages. Writes receipts/VERIFY_CLONE_V2.json.
ARGS: expected_pid, expect {label: instances}, pcg_instances, buildings {actors, parts, shells} (optional: one object per
building check - Bldg_ actors, their parts, shells, Static, none detached, merged buildings actor gone)."""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
NEW = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial_v2'
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == NEW, world.get_outermost().get_path_name()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
acts = eas.get_all_level_actors()
mob = lambda c: str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0]
out = {}
for lab, want in ARGS['expect'].items():
    a = [x for x in acts if x.get_actor_label() == lab]
    if len(a) != 1:
        out[lab] = {'found': len(a)}; continue
    a = a[0]
    comps = [c for c in a.get_components_by_class(u.SceneComponent) if not isinstance(c, u.BillboardComponent)]
    got = sum(c.get_instance_count() for c in a.get_components_by_class(u.InstancedStaticMeshComponent))
    out[lab] = {'instances': got, 'expected': want, 'match': got == want, 'mobility': sorted({mob(c) for c in comps}),
                'detached': sum(1 for c in comps if c != a.root_component and c.get_attach_parent() is None)}
vol = [x for x in acts if isinstance(x, u.PCGVolume)]
pcg = None
if len(vol) == 1:
    comp = vol[0].get_component_by_class(u.PCGComponent)
    pcg = {'graph': comp.get_editor_property('graph_instance').get_editor_property('graph').get_path_name() if comp.get_editor_property('graph_instance') else None,
           'generated': comp.get_editor_property('generated'),
           'instances': sum(c.get_instance_count() for c in vol[0].get_components_by_class(u.InstancedStaticMeshComponent))}
land = [x for x in acts if isinstance(x, u.Landscape)]
bl = [x for x in acts if x.get_actor_label().startswith('Bldg_')]
bstat = {'actors': len(bl), 'ism_instances': 0, 'single_meshes': 0, 'shells': 0, 'detached': 0, 'mobility': set(),
         'merged_buildings_actor': [x.get_actor_label() for x in acts if isinstance(x, u.StaticMeshActor) and x.get_actor_label().startswith('KarmeiYosef') and '_buildings' in x.get_actor_label()]}
for a in bl:
    for c in a.get_components_by_class(u.SceneComponent):
        if isinstance(c, u.BillboardComponent):
            continue
        bstat['mobility'].add(mob(c))
        if c != a.root_component and c.get_attach_parent() is None:
            bstat['detached'] += 1
        if isinstance(c, u.InstancedStaticMeshComponent):
            bstat['ism_instances'] += c.get_instance_count()
        elif isinstance(c, u.StaticMeshComponent):
            bstat['single_meshes'] += 1
            bstat['shells'] += c.get_name().startswith('Shell')
bstat['mobility'] = sorted(bstat['mobility'])
rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'map': NEW,
       'map_sha256': hashlib.sha256((ROOT / ('Content' + NEW[5:] + '.umap')).read_bytes()).hexdigest(),
       'actors': out, 'pcg': pcg, 'landscapes': [x.get_actor_label() for x in land],
       'landscape_material': land[0].get_editor_property('landscape_material').get_path_name() if land else None,
       'hda_actors': [x.get_actor_label() for x in acts if x.get_class().get_name() == 'HoudiniAssetActor'],
       'actor_count': len(acts), 'buildings': bstat,
       'dirty': (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))}
rec['all_match'] = all(v.get('match') for v in out.values()) and bool(pcg) and pcg['instances'] == ARGS.get('pcg_instances')
if ARGS.get('buildings'):
    want = ARGS['buildings']
    rec['buildings_match'] = (bstat['actors'] == want['actors'] and bstat['ism_instances'] + bstat['single_meshes'] - bstat['shells'] == want['parts']
                              and bstat['shells'] == want['shells'] and bstat['detached'] == 0 and bstat['mobility'] == ['STATIC']
                              and not bstat['merged_buildings_actor'])
    rec['all_match'] = rec['all_match'] and rec['buildings_match']
(TASK / 'receipts' / 'VERIFY_CLONE_V2.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
RESULT = {'ok': True, **rec}
