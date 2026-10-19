"""In-editor (own editor on the PCG clone). Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef tool.
Aviv: trees and plants must NEVER disappear
(not leaves, not trunks), only degrade to a lower LOD. The audit (receipts/VISIBILITY_AUDIT.json) found no cull distances;
the remaining risk is Nanite masked-leaf foliage without shape preservation (the Paz Farm crowns vanished that way). Vendor
originals stay untouched: area-owned copies go to <clone>/Vegetation/Meshes with Nanite Preserve Area, and the zone PCG graph
points at the copies. Reversible: 'revert_pines' points the graph back to the vendor meshes.
The clone (ARGS.clone_suffix) and the graph version (ARGS.graph_version: '' = the build_zone_pcg.py graph, 'v002'... = a
trees_pcg.py graph) are REQUIRED, so the script never edits an unused graph. The 'own_mis' vendor reload is limited to
ARGS.vendor_prefixes (default ['/Game/STF/'], the pack the Karmei Yosef copies came from).
steps (ARGS.step):
  cams          write ../cameras_forest.json (overhead 460 m + oblique) at ARGS.xy with a traced ground height. Read-only.
  pines         copy the 4 Modular_Rural_Cabin pines (Preserve Area), swap graph entries, flush the PCG cache, regenerate.
  revert_pines  swap graph entries back to the vendor meshes, flush, regenerate.
  copy_swap     ARGS.sources [vendor mesh paths]: area-owned copies with Nanite ON + Preserve Area (e.g. STF trees whose last
                LOD is a dead-tree billboard card that reads as a pale stick), swap graph entries, regenerate.
  revert_swap   ARGS.sources: point the graph back to those vendor meshes, regenerate.
  alpha_fix     ARGS.sources [vendor mesh paths; copies in <clone>/Vegetation/Meshes]: masked slots get area-owned MI copies whose texture
                copies preserve alpha coverage across mips (threshold = the material's clip value), so leaves keep their
                cut-out size far away. Receipt receipts/NEVER_VANISH_ALPHA.json holds the original slot MIs.
  alpha_revert  restore the original slot MIs on those mesh copies.
  own_mis       ARGS.sources: every remaining vendor MI on those copies gets an area-owned copy too (enabling Nanite on a copy
                makes Unreal set the Nanite usage flag on whatever MI it uses; vendor MIs must not change), stray unsaved
                texture copies (ARGS.delete) are deleted, and vendor packages dirtied only by that flag are reloaded from disk.
  status        PCG generation state + per-mesh instance counts. Read-only.
  save          named saves: dirty content under <clone>/ only (graph, copies), then the clone map (PCG output lives in it).
ARGS: expected_pid, script_file (client), step, clone_suffix, graph_version [, xy, vendor_prefixes].
"""
import datetime, hashlib, importlib.util, json, os
from collections import Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
TRIAL = A.TRIAL_ROOT
CLONE = A.clone_map(ARGS['clone_suffix'])                               # required, explicit
GRAPH = A.zones_graph(ARGS['graph_version'])                            # required: the graph the clone's volume uses
MR = '/Game/Modular_Rural_Cabin/Meshes/Foliage/'
COPY = TRIAL + '/Vegetation/Meshes/'
PINES = ['SM_Pine_Tree_01', 'SM_Pine_Tree_02', 'SM_Pine_Tree_03', 'SM_Pine_Tree_05']
EAL = u.EditorAssetLibrary
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
vol = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)][0]
comp = vol.get_component_by_class(u.PCGComponent)


def spawners(g):
    out = []
    for node in g.get_editor_property('nodes'):
        try:
            s = node.get_settings()
        except Exception:
            s = node.get_editor_property('settings_interface')
        if isinstance(s, u.PCGStaticMeshSpawnerSettings):
            out.append(s)
    return out


def swap(mapping):
    g = u.load_asset(GRAPH)
    changed = 0
    for s in spawners(g):
        sel = s.get_editor_property('mesh_selector_parameters')
        entries = list(sel.get_editor_property('mesh_entries'))
        new = []
        for e in entries:
            d = e.get_editor_property('descriptor'); m = d.get_editor_property('static_mesh')
            p = m.get_path_name().split('.')[0] if m else None
            if p in mapping:
                d.set_editor_property('static_mesh', u.load_asset(mapping[p])); e.set_editor_property('descriptor', d); changed += 1
            new.append(e)
        s.modify(); sel.modify()
        sel.set_editor_property('mesh_entries', new)
    # read back
    used = Counter()
    for s in spawners(g):
        for e in s.get_editor_property('mesh_selector_parameters').get_editor_property('mesh_entries'):
            m = e.get_editor_property('descriptor').get_editor_property('static_mesh')
            used[m.get_path_name().split('.')[0] if m else None] += 1
    g.modify()
    u.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
    comp.cleanup_local(True)
    comp.generate_local(True)
    return changed, dict(used)


def status():
    per = Counter()
    for c in vol.get_components_by_class(u.InstancedStaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        per[m.get_path_name().split('.')[0] if m else None] += c.get_instance_count()
    return {'generated': comp.get_editor_property('generated'), 'in_progress': comp.get_editor_property('generation_in_progress'),
            'instances': sum(per.values()), 'pines': {k: v for k, v in per.items() if 'Pine_Tree' in str(k)}}


if step == 'cams':
    x, y = ARGS['xy']
    land = [a for a in eas.get_all_level_actors() if isinstance(a, u.Landscape)]
    ignore = [a for a in eas.get_all_level_actors() if not isinstance(a, (u.Landscape, u.LandscapeProxy))]
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 80000.0), u.Vector(x, y, -20000.0), u.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                            False, ignore, u.DrawDebugTrace.NONE, True)
    h = hit[1] if isinstance(hit, tuple) else hit
    z = h.to_tuple()[4].z
    cams = {'forest_overhead': {'eye': [x, y, z + 46000], 'target': [x, y - 1, z]},
            'forest_oblique': {'eye': [x - 30000, y - 30000, z + 15000], 'target': [x, y, z]},
            'forest_far': {'eye': [x - 80000, y - 60000, z + 25000], 'target': [x, y, z]}}
    (TASK / 'cameras_forest.json').write_text(json.dumps(cams, indent=1), encoding='utf-8')
    RESULT = {'ok': True, 'ground_z': z, 'cams': cams}

elif step == 'pines':
    sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    mapping, info = {}, {}
    for n in PINES:
        dst = COPY + n
        m = u.load_asset(dst) if EAL.does_asset_exist(dst) else EAL.duplicate_asset(MR + n, dst)
        s = m.get_editor_property('nanite_settings')
        info[n] = {'nanite_before': bool(s.enabled), 'shape_before': str(s.shape_preservation)}
        s.set_editor_property('enabled', True)
        s.set_editor_property('shape_preservation', u.NaniteShapePreservation.PRESERVE_AREA)
        sms.set_nanite_settings(m, s, True)
        info[n]['shape_after'] = str(m.get_editor_property('nanite_settings').shape_preservation)
        mapping[MR + n] = dst
    changed, used = swap(mapping)
    RESULT = {'ok': True, 'copies': info, 'entries_changed': changed, 'graph_meshes': used, 'dirty': dirty()}

elif step == 'copy_swap':
    sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    mapping, info = {}, {}
    for src in ARGS['sources']:
        n = src.rsplit('/', 1)[1]; dst = COPY + n
        m = u.load_asset(dst) if EAL.does_asset_exist(dst) else EAL.duplicate_asset(src, dst)
        s = m.get_editor_property('nanite_settings')
        info[n] = {'nanite_before': bool(s.enabled)}
        s.set_editor_property('enabled', True)
        s.set_editor_property('shape_preservation', u.NaniteShapePreservation.PRESERVE_AREA)
        sms.set_nanite_settings(m, s, True)
        a = m.get_editor_property('nanite_settings')
        info[n].update(nanite_after=bool(a.enabled), shape_after=str(a.shape_preservation))
        mapping[src] = dst
    changed, used = swap(mapping)
    RESULT = {'ok': True, 'copies': info, 'entries_changed': changed, 'dirty': dirty()}

elif step == 'alpha_fix':
    # ARGS.sources = vendor mesh paths whose copies live in <clone>/Vegetation/Meshes (idempotent: originals are read from the
    # vendor meshes, never from the current copy slots)
    L = u.MaterialEditingLibrary
    REC = TASK / 'receipts' / 'NEVER_VANISH_ALPHA.json'
    rec = {'slots': {}, 'mis': {}, 'textures': {}}

    def unique(folder, src, used):
        dst = folder + src.rsplit('/', 1)[1]
        if dst in used.values() and used.get(src) != dst:
            dst += '_' + src.rsplit('/', 2)[1]
        return dst

    for src_mesh in ARGS['sources']:
        name = src_mesh.rsplit('/', 1)[1]
        v, m = u.load_asset(src_mesh), u.load_asset(COPY + name)
        assert v and m, name
        for i in range(len(v.get_editor_property('static_materials'))):
            vmi = v.get_material(i)
            if not isinstance(vmi, u.MaterialInstance):
                continue
            base = vmi.get_base_material()
            if base.get_editor_property('blend_mode') != u.BlendMode.BLEND_MASKED or 'lod3' in vmi.get_name().lower():
                continue
            src_mi = vmi.get_path_name().split('.')[0]
            rec['slots']['%s#%d' % (name, i)] = src_mi
            if src_mi not in rec['mis']:
                dst_mi = unique(TRIAL + '/Vegetation/Materials/', src_mi, rec['mis'])
                new_mi = u.load_asset(dst_mi) if EAL.does_asset_exist(dst_mi) else EAL.duplicate_asset(src_mi, dst_mi)
                clip = base.get_editor_property('opacity_mask_clip_value')
                for pn in L.get_texture_parameter_names(vmi):
                    t = L.get_material_instance_texture_parameter_value(vmi, pn)
                    if not t or t.get_editor_property('compression_settings') == u.TextureCompressionSettings.TC_NORMALMAP:
                        continue
                    if not t.get_path_name().startswith('/Game/') or any(k in t.get_name().lower() for k in ('wind', 'pivot', 'vector')):
                        L.set_material_instance_texture_parameter_value(new_mi, pn, t)     # data textures stay vendor
                        continue
                    src_t = t.get_path_name().split('.')[0]
                    tmap = {k: v_['dst'] for k, v_ in rec['textures'].items()}
                    if src_t in tmap:
                        dst_t = tmap[src_t]
                    else:
                        dst_t = unique(TRIAL + '/Vegetation/Textures/', src_t, tmap)
                        nt = u.load_asset(dst_t) if EAL.does_asset_exist(dst_t) else EAL.duplicate_asset(src_t, dst_t)
                        nt.set_editor_property('do_scale_mips_for_alpha_coverage', True)
                        nt.set_editor_property('alpha_coverage_thresholds', u.Vector4(0.0, 0.0, 0.0, float(clip)))
                        rec['textures'][src_t] = {'dst': dst_t, 'threshold': clip}
                    L.set_material_instance_texture_parameter_value(new_mi, pn, u.load_asset(dst_t))
                L.update_material_instance(new_mi)
                rec['mis'][src_mi] = dst_mi
            m.set_material(i, u.load_asset(rec['mis'][src_mi]))
    for stray in ARGS.get('delete_strays', []):                         # unsaved copies made by an earlier run
        if EAL.does_asset_exist(stray) and stray not in [v_['dst'] for v_ in rec['textures'].values()]:
            EAL.delete_asset(stray)
    REC.write_text(json.dumps(rec, indent=1), encoding='utf-8')
    RESULT = {'ok': True, 'slots': len(rec['slots']), 'mis': rec['mis'], 'textures': {k.rsplit('/', 1)[1]: v_['threshold'] for k, v_ in rec['textures'].items()}, 'dirty': dirty()}

elif step == 'own_mis':
    REC = TASK / 'receipts' / 'NEVER_VANISH_ALPHA.json'
    rec = json.loads(REC.read_text())
    used = dict(rec['mis'])
    for src_mesh in ARGS['sources']:
        name = src_mesh.rsplit('/', 1)[1]
        v, m = u.load_asset(src_mesh), u.load_asset(COPY + name)
        for i in range(len(v.get_editor_property('static_materials'))):
            cur = m.get_material(i)
            if not cur or cur.get_path_name().startswith(TRIAL + '/'):
                continue
            src_mi = cur.get_path_name().split('.')[0]
            rec['slots'].setdefault('%s#%d' % (name, i), src_mi)
            if src_mi not in used:
                dst = TRIAL + '/Vegetation/Materials/' + src_mi.rsplit('/', 1)[1]
                if dst in used.values():
                    dst += '_' + src_mi.rsplit('/', 2)[1]
                if not EAL.does_asset_exist(dst):
                    EAL.duplicate_asset(src_mi, dst)
                used[src_mi] = dst
            m.set_material(i, u.load_asset(used[src_mi]))
    rec['mis'] = used
    deleted = []
    for d_ in ARGS.get('delete', []):
        if EAL.does_asset_exist(d_):
            EAL.delete_asset(d_); deleted.append(d_)
    REC.write_text(json.dumps(rec, indent=1), encoding='utf-8')
    outside = [x for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages() if not x.get_path_name().startswith(TRIAL + '/')]
    names = [x.get_path_name() for x in outside]
    assert all(n.startswith(tuple(ARGS.get('vendor_prefixes', ['/Game/STF/']))) for n in names), names
    reload = None
    if outside:
        reload = str(u.EditorLoadingAndSavingUtils.reload_packages(outside, u.ReloadPackagesInteractionMode.ASSUME_POSITIVE))
    RESULT = {'ok': True, 'mis': len(used), 'deleted': deleted, 'reloaded': names, 'reload_result': reload, 'dirty': dirty()}

elif step == 'alpha_revert':
    REC = TASK / 'receipts' / 'NEVER_VANISH_ALPHA.json'
    rec = json.loads(REC.read_text())
    for key, src_mi in rec['slots'].items():
        name, i = key.split('#')
        u.load_asset(COPY + name).set_material(int(i), u.load_asset(src_mi))     # the vendor MI = the copy's original slot
    RESULT = {'ok': True, 'restored': rec['slots'], 'dirty': dirty()}

elif step == 'revert_swap':
    changed, used = swap({COPY + src.rsplit('/', 1)[1]: src for src in ARGS['sources']})
    RESULT = {'ok': True, 'entries_changed': changed, 'dirty': dirty()}

elif step == 'revert_pines':
    changed, used = swap({COPY + n: MR + n for n in PINES})
    RESULT = {'ok': True, 'entries_changed': changed, 'graph_meshes': used, 'dirty': dirty()}

elif step == 'status':
    RESULT = {'ok': True, **status(), 'dirty': dirty()}

elif step == 'save':
    st = status()
    assert st['generated'] and not st['in_progress'] and st['instances'] > 0, st
    d = dirty()
    assert d[0] in ([CLONE], []), d
    other = [p for p in d[1] if not p.startswith(TRIAL + '/')]
    assert not other, 'dirty outside the clone: %s' % other
    pk = list(u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    if pk:
        assert u.EditorLoadingAndSavingUtils.save_packages(pk, False)
    assert u.EditorLoadingAndSavingUtils.save_map(world, CLONE)
    f = ROOT / ('Content' + CLONE[5:] + '.umap')
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'saved_content': d[1], 'status': st,
           'map_sha256': hashlib.sha256(f.read_bytes()).hexdigest(), 'map_bytes': f.stat().st_size, 'dirty_after': dirty()}
    (TASK / 'receipts' / 'NEVER_VANISH_SAVE.json').write_text(json.dumps(rec, indent=1), encoding='utf-8')
    RESULT = {'ok': True, **rec}
