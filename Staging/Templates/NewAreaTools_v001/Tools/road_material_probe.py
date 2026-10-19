"""In-editor, read-only. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). The road-surface actor's material slots (asset
defaults and component overrides) and the asphalt / road material assets in the project (asset registry, no loading).
ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
roads = [a for a in eas.get_all_level_actors() if isinstance(a, u.StaticMeshActor) and a.get_actor_label().endswith('_road_surfaces')]
out = []
for a in roads:
    c = a.static_mesh_component; m = c.get_editor_property('static_mesh')
    slots = m.get_editor_property('static_materials')
    out.append({'label': a.get_actor_label(), 'mesh': m.get_path_name(), 'triangles': m.get_num_triangles(0),
                'slots': [[str(s.get_editor_property('material_slot_name')),
                           s.get_editor_property('material_interface').get_path_name() if s.get_editor_property('material_interface') else None,
                           c.get_material(i).get_path_name() if c.get_material(i) else None] for i, s in enumerate(slots)],
                'override_materials': [x.get_path_name() if x else None for x in c.get_editor_property('override_materials')]})
reg = u.AssetRegistryHelpers.get_asset_registry()
cands = []
for cls in ('MaterialInstanceConstant', 'Material'):
    for d in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', cls)):
        n = str(d.asset_name)
        if any(k in n.lower() for k in ('asphalt', 'road')):
            cands.append([cls, str(d.package_name)])
RESULT = {'ok': True, 'road_actors': out, 'candidates': sorted(cands)[:120], 'n_candidates': len(cands)}
