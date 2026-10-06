import unreal,json,pathlib,hashlib
ROOT=pathlib.Path(__file__).parent
def capture(name):
    roads=[];landscapes=[];new=[]
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        cls=a.get_class().get_name()
        if cls in ('DynamicRoadNetwork','DynamicRoad','RoadGeo'):
            parts=[]
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                m=c.get_editor_property('static_mesh')
                parts.append({'path':c.get_path_name(),'mesh':m.get_path_name() if m else None,'transform':c.get_world_transform().export_text(),'materials':[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]})
            roads.append({'path':a.get_path_name(),'transform':a.get_actor_transform().export_text(),'components':parts})
        if cls=='Landscape':
            origin,extent=a.get_actor_bounds(False)
            landscapes.append({'path':a.get_path_name(),'transform':a.get_actor_transform().export_text(),'origin':str(origin),'extent':str(extent),'material':a.get_editor_property('landscape_material').get_path_name(),'components':len(a.get_components_by_class(unreal.LandscapeComponent))})
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m=c.get_editor_property('static_mesh')
            if m and '/Procedural_v002/' in m.get_path_name():
                new.append({'actor':a.get_path_name(),'label':a.get_actor_label(),'component':c.get_path_name(),'mesh':m.get_path_name(),'instances':c.get_instance_count() if isinstance(c,unreal.InstancedStaticMeshComponent) else 1})
    roads.sort(key=lambda r:r['path'])
    result={'roads':roads,'roads_signature':hashlib.sha256(json.dumps(roads,sort_keys=True).encode()).hexdigest(),'landscapes':landscapes,'new_family_components':new,'new_module_instances':sum(c['instances'] for c in new)}
    (ROOT/(name+'.json')).write_text(json.dumps(result,indent=2));return {'road_actors':len(roads),'landscapes':len(landscapes),'new_module_instances':result['new_module_instances'],'roads_signature':result['roads_signature']}
