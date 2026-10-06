"""Match normal Houdini family choices to saved native city instances."""
import unreal,json,pathlib,collections,math,runpy,hashlib
ROOT=pathlib.Path(__file__).parent;PROJECT=ROOT.parents[1]
PROFILE=PROJECT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def run(suffix='AFTER'):
    p=read(PROFILE);state=read(p['workflow_receipt']);assert state['phase']=='baked_saved_verified',state['phase']
    receipt=read(p['catalog_receipt']);records=receipt['native_building_assembly_records']
    wanted=[r for r in records if r.get('source_family',{}).get('mode')=='facade_floor_grid']
    assert wanted,'Normal selection did not instantiate any new procedural families'
    assert len({r['source_feature']['osm_id'] for r in records})==len(records)
    native=collections.defaultdict(list)
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m=c.get_editor_property('static_mesh')
            if not m or '/Procedural_v002/' not in m.get_path_name():continue
            count=c.get_instance_count() if isinstance(c,unreal.InstancedStaticMeshComponent) else 1
            for index in range(count):
                t=c.get_instance_transform(index,world_space=True) if isinstance(c,unreal.InstancedStaticMeshComponent) else c.get_world_transform()
                q=t.translation;native[m.get_path_name()].append({'position':[q.x,q.y,q.z],'actor':a.get_path_name(),'label':a.get_actor_label(),'component':c.get_path_name(),'instance':index,'scale':[t.scale3d.x,t.scale3d.y,t.scale3d.z],'materials':[c.get_material(k).get_path_name() if c.get_material(k) else None for k in range(c.get_num_materials())]})
    claimed=set();buildings=[];maximum_error=0.
    for record in wanted:
        instances=[]
        for item in record['wall_placements']:
            expected=[100*item['P'][0],100*item['P'][2],100*item['P'][1]];options=native[item['path']]
            nearest=min(enumerate(options),key=lambda it:math.dist(expected,it[1]['position']));index,actual=nearest
            error=math.dist(expected,actual['position']);assert error<.1,(item['placement_id'],error)
            key=(item['path'],index);assert key not in claimed;claimed.add(key)
            assert max(abs(v-1) for v in actual['scale'])<1e-4
            assert actual['materials']==item['material_slots']
            maximum_error=max(maximum_error,error);instances.append(dict(actual,mesh=item['path'],placement_id=item['placement_id'],position_error_cm=error))
        ring=record['native_family_envelope_xz_m'];x=sum(v[0] for v in ring)/len(ring)*100;y=sum(v[1] for v in ring)/len(ring)*100
        buildings.append({'family_id':record['style_family_id'],'osm_id':record['source_feature']['osm_id'],'center_cm':[x,y,record['base_m']*100],'height_m':record['height_m'],'envelope_xz_m':ring,'horizontal_repeats':record['source_family']['horizontal_repeats'],'floor_repeats':record['source_family']['floor_repeats'],'modules':len(instances),'native_instances':instances})
    total=sum(len(v) for v in native.values());assert total==len(claimed),(total,len(claimed))
    snapshot=runpy.run_path(str(ROOT/'city_snapshot.py'))['capture']('CITY_'+suffix);before=read(ROOT/'CITY_BEFORE.json');after=read(ROOT/('CITY_'+suffix+'.json'))
    assert before['roads_signature']==after['roads_signature'],'Existing road actors changed'
    assert len(after['landscapes'])==1
    oldland=before['landscapes'][0];newland=after['landscapes'][0]
    for k in ('transform','material','components'):assert oldland[k]==newland[k],('Landscape changed',k,oldland[k],newland[k])
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    counts=dict(collections.Counter(r['family_id'] for r in buildings))
    result={'map':p['map'],'profile':str(PROFILE),'workflow_phase':state['phase'],'total_assembled_buildings':len(records),'new_procedural_buildings':len(buildings),'new_module_instances':total,'families_used':counts,'maximum_position_error_cm':maximum_error,'roads_unchanged':True,'one_landscape_same_transform_material_components':True,'map_clean':True,'buildings':buildings,'catalog_receipt_sha256':hashlib.sha256(pathlib.Path(p['catalog_receipt']).read_bytes()).hexdigest()}
    (ROOT/('NEW_FAMILY_USAGE_'+suffix+'.json')).write_text(json.dumps(result,indent=2));return {k:v for k,v in result.items() if k!='buildings'}
