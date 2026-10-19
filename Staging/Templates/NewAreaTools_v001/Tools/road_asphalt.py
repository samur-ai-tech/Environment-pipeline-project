"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69) (playbook 10c; tracks keep this area's TRACK_MI).
Map-level material override on this area's road-surface actor only (component override materials); the baked road mesh asset
and the material assets are never changed or saved here. Reports dirty packages afterwards so a vendor material touched by
usage flags is caught before any save. Generator constants from hda_edits.py (E, loaded from its file at each call):
  - the actor is the ONE StaticMeshActor whose component mesh is <root>/Bake/<area>_road_surfaces (not found by label:
    labels get '_1' after a regeneration);
  - the mesh has 1 slot (E.ROAD_GENERATED_MATERIAL) or 2 slots ({E.ROAD_GENERATED_MATERIAL, E.TRACK_MI}, in an
    order the bake does not control); any other slot set refuses before anything is touched (a track MI that fails to load
    makes the Houdini Engine bake fall back silently to its default material);
  - 'set' clears all overrides, then overrides ONLY the slot whose mesh material is E.ROAD_GENERATED_MATERIAL with
    ARGS.material; the track slot is touched only when ARGS.track_material is given;
  - every slot (index, slot name, mesh material, component material) is recorded and checked after the change.
steps (ARGS.step): set (ARGS.material, optional ARGS.track_material) | clear (remove all overrides). No save (save_main_map.py).
ARGS: expected_pid, script_file (client), step, material (set), track_material (optional), expected_slots (optional: 1 or 2)."""
import importlib.util, os, sys
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('hda_edits', TOOLS.parent / 'hda_edits.py')
E = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(E)  # generator constants, read from the file at each call
TASK = E.A.task_dir(TOOLS, ROOT)
assert Path(E.__file__).resolve().parent == TASK, ('generator constants loaded from elsewhere', E.__file__)
MAIN = E.A.MAIN_MAP
MESH = E.A.ROAD_MESH
ROAD, TRACK = E.ROAD_GENERATED_MATERIAL, E.TRACK_MI
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAIN
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']
assert step in ('set', 'clear'), step
P = lambda m: m.get_path_name() if m else None


def mesh_of(a):
    m = a.static_mesh_component.get_editor_property('static_mesh') if a.static_mesh_component else None
    return m.get_path_name().split('.')[0] if m else None


# every check and load happens before modify(), so a refused call leaves the map untouched
roads = [a for a in eas.get_all_level_actors() if isinstance(a, u.StaticMeshActor) and mesh_of(a) == MESH]
assert len(roads) == 1, ('road actors by mesh', MESH, [a.get_actor_label() for a in roads])
actor = roads[0]
c = actor.static_mesh_component
mesh = c.get_editor_property('static_mesh')
asset = [(i, str(s.get_editor_property('material_slot_name')), P(s.get_editor_property('material_interface')))
         for i, s in enumerate(mesh.get_editor_property('static_materials'))]
assert sorted(p or '' for _, _, p in asset) in ([ROAD], sorted([ROAD, TRACK])), \
    ('road mesh slots are neither run-1 [road] nor v002 {road, track}; a track MI that failed to load falls back silently to '
     'the Houdini default material', asset)
if ARGS.get('expected_slots') is not None:
    assert len(asset) == ARGS['expected_slots'], ('slot count', len(asset), ARGS['expected_slots'], asset)
ai = next(i for i, _, p in asset if p == ROAD)
ti = next((i for i, _, p in asset if p == TRACK), None)
mat = tmat = None
if step == 'set':
    mat = u.load_asset(ARGS['material'])
    assert mat and isinstance(mat, u.MaterialInterface), ARGS['material']
    if ARGS.get('track_material'):
        assert ti is not None, ('track_material given but the mesh has no track slot', asset)
        tmat = u.load_asset(ARGS['track_material'])
        assert tmat and isinstance(tmat, u.MaterialInterface), ARGS['track_material']
overrides_before = [P(x) for x in c.get_editor_property('override_materials')]
actor.modify(); c.modify()
c.set_editor_property('override_materials', [])          # both steps: drop any stale (run-1 slot-0) override first
if step == 'set':
    c.set_material(ai, mat)
    if tmat:
        c.set_material(ti, tmat)
want = {i: p for i, _, p in asset}
if mat:
    want[ai] = mat.get_path_name()
if tmat:
    want[ti] = tmat.get_path_name()
slots = [{'index': i, 'slot_name': n, 'asset_material': p, 'component_material': P(c.get_material(i))} for i, n, p in asset]
assert all(s['component_material'] == want[s['index']] for s in slots), ('component materials after ' + step, slots, want)
RESULT = {'ok': True, 'step': step, 'actor_label': actor.get_actor_label(), 'actor_path': actor.get_path_name(), 'mesh': MESH,
          'slot_count': len(asset), 'asphalt_slot': ai, 'track_slot': ti, 'slots': slots,
          'track_slot_touched': bool(tmat), 'overrides_before': overrides_before,
          'mesh_nanite': mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),
          'override_materials': [P(x) for x in c.get_editor_property('override_materials')],
          'dirty_maps': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
