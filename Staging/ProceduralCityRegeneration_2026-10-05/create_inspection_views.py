import unreal,json,pathlib,math,collections
ROOT=pathlib.Path(__file__).parent
def run():
    data=json.loads((ROOT/'NEW_FAMILY_USAGE_AFTER.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_path_name()==data['map']
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    existing={a.get_actor_label():a for a in actors.get_all_level_actors() if a.get_actor_label().startswith('INSPECT_MODULAR_')}
    assert {p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()}.issubset({data['map']})
    byfamily=collections.defaultdict(list)
    for b in data['buildings']:byfamily[b['family_id']].append(b)
    records=[]
    for index,(family,buildings) in enumerate(sorted(byfamily.items()),1):
        # Prefer a clearly varied example, then a location nearer the area center.
        b=min(buildings,key=lambda x:(-(x['horizontal_repeats']*x['floor_repeats']),math.hypot(*x['center_cm'][:2])))
        ident=family.split('.')[1];ring=b['envelope_xz_m'];width=max(x[0] for x in ring)-min(x[0] for x in ring);depth=max(x[1] for x in ring)-min(x[1] for x in ring)
        x,y,z=b['center_cm'];distance=max(width,depth,b['height_m'],12)*130
        target=unreal.Vector(x,y,z+b['height_m']*45);position=unreal.Vector(x-distance,y-distance,z+b['height_m']*100+distance*.75)
        rotation=unreal.MathLibrary.find_look_at_rotation(position,target)
        label='INSPECT_MODULAR_%02d_%s_OSM_%s'%(index,ident,b['osm_id'])
        camera=existing.get(label) or actors.spawn_actor_from_class(unreal.CameraActor,position,rotation);assert camera
        camera.set_actor_label(label);camera.set_folder_path('Inspection/New Modular Buildings')
        camera.get_editor_property('camera_component').set_field_of_view(55.0)
        camera.tags=[unreal.Name('GeoCity_Modular_Inspection'),unreal.Name(ident),unreal.Name('OSM_'+b['osm_id'])]
        records.append({'family_id':family,'family':ident,'building_count':len(buildings),'camera_label':label,'camera_actor':camera.get_path_name(),'osm_id':b['osm_id'],'center_cm':b['center_cm'],'horizontal_repeats':b['horizontal_repeats'],'floor_repeats':b['floor_repeats'],'camera_location_cm':[position.x,position.y,position.z],'camera_rotation':rotation.export_text()})
    actors.set_selected_level_actors([])
    assert level.save_current_level() and not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    (ROOT/'INSPECTION_VIEWS.json').write_text(json.dumps({'map':data['map'],'folder':'Inspection/New Modular Buildings','cameras':records},indent=2))
    return {'saved_cameras':len(records),'map_saved':True,'labels':[r['camera_label'] for r in records]}
