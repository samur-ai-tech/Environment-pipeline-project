"""Read the actual saved native references, transforms and materials."""
import unreal
import json
import os
import math
from collections import Counter
from pathlib import Path

PROJECT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world_path=world.get_outermost().get_path_name()
profiles=[p for p in (PROJECT/'Staging/ModelBank').rglob('AREA_PROFILE.json')
          if json.loads(p.read_text(encoding='utf-8'))['map']==world_path]
assert len(profiles)==1
profile=json.loads(profiles[0].read_text())
state=json.loads(Path(profile['workflow_receipt']).read_text())
assert state['phase']=='baked_saved_verified'
receipt=json.loads(Path(profile['catalog_receipt']).read_text())
records=receipt['nonbuilding_instances']
expected=Counter(p['path'] for p in records)
actual=Counter()
components=[]
native_positions={path:[] for path in expected}
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for actor in actors:
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh=component.static_mesh
        if not mesh or mesh.get_path_name() not in expected:continue
        path=mesh.get_path_name()
        count=component.get_instance_count() if isinstance(component,unreal.InstancedStaticMeshComponent) else 1
        actual[path]+=count
        transforms=[component.get_instance_transform(i,world_space=True) for i in range(count)] if isinstance(component,unreal.InstancedStaticMeshComponent) else [component.get_world_transform()]
        for t in transforms:
            p=t.translation
            native_positions[path].append((p.x,p.y,p.z))
        slots=[component.get_material(i).get_path_name() for i in range(component.get_num_materials())]
        desired=profile['instance_materials'].get(path)
        if desired:
            assert slots==desired,path
        else:
            assert slots==[s.material_interface.get_path_name() for s in mesh.get_editor_property('static_materials')],path
        components.append({'actor':actor.get_path_name(),'mesh':path,'instances':count,'materials':slots})
assert actual==expected
# Compare the complete unordered transferred anchor set, allowing 1 mm precision.
buckets={}
for path,positions in native_positions.items():
    table={}
    for p in positions:table.setdefault(tuple(math.floor(v) for v in p),[]).append(p)
    buckets[path]=table
maximum_error=0.0
for r in records:
    p=(r['P'][0]*100,r['P'][2]*100,r['P'][1]*100)
    cell=tuple(math.floor(v) for v in p)
    matches=[]
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for dz in (-1,0,1):
                key=(cell[0]+dx,cell[1]+dy,cell[2]+dz)
                matches.extend((math.dist(p,q),key,i) for i,q in enumerate(buckets[r['path']].get(key,[])))
    assert matches,'Missing transferred native point: '+r['placement_id']
    error,key,index=min(matches)
    assert error<=0.1,(r['placement_id'],error)
    maximum_error=max(maximum_error,error)
    buckets[r['path']][key].pop(index)
result={'world':world_path,'pid':os.getpid(),'generator_revision':receipt['generator_revision'],'native_count':sum(actual.values()),
        'native_mesh_counts':dict(actual),'all_native_anchor_locations_match_recipe_within_1mm':True,'maximum_anchor_transfer_error_cm':maximum_error,
        'native_material_slots_verified':True,'components':components,'building_assembly':receipt.get('building_assembly'),
        'terrain_support':receipt.get('terrain_support'),'proxy_outputs':receipt.get('proxy_outputs'),
        'dirty_maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
        'landscape_count':sum(isinstance(a,unreal.Landscape) for a in actors)}
area=json.loads(Path(profile['source']).read_text())['area_id']
result['landscape_readback']=[]
for landscape in [a for a in actors if isinstance(a,unreal.Landscape)]:
    material=landscape.get_editor_property('landscape_material')
    assert material.get_path_name()==profile['landscape_material']
    infos=[]
    for name, settings in landscape.get_editor_property('target_layers').items():
        info=settings.get_editor_property('layer_info_obj')
        if info:
            infos.append({'target':str(name),'layer':str(info.get_editor_property('layer_name')),'info':info.get_path_name()})
    assert {r['layer'] for r in infos}=={'Dirt_Path','Sand_01','Sand_02','Sand_Path'}
    resolved={}
    for name in [r['layer']+suffix for r in infos for suffix in ('_Albedo','_Normal')]:
        texture=unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material,name)
        assert texture is not None,'Missing selected Landscape texture: '+name
        resolved[name]=texture.get_path_name()
    result['landscape_readback'].append({'material':material.get_path_name(),
        'valid_target_layer_names':[str(name) for name in landscape.get_target_layer_names()],
        'assigned_layer_infos':infos,
        'resolved_selected_layer_texture_parameters':resolved,
        'texture_query_scope':'Shared base MI; no Landscape component static-weight permutation. Empty used-textures here is inconclusive.',
        'used_texture_paths':sorted(t.get_path_name() for t in unreal.MaterialEditingLibrary.get_material_used_textures(material))})
target=PROJECT/'Staging/RepairExecution_2026-10-03'/('ACTUAL_'+area+'.json')
target.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'area':area,'native_count':result['native_count'],'building_assembly':{k:v for k,v in result['building_assembly'].items() if not isinstance(v,(list,dict))},'receipt':str(target)}))
