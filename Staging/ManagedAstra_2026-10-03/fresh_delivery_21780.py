"""Task2 PID21780 delivery steps; persistent one-shot GameThread callbacks."""
import datetime,hashlib,json,os,sys,time,traceback
from pathlib import Path
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
PROFILES={a:ROOT/'Staging/ModelBank'/d/'AREA_PROFILE.json' for a,d in [('GazaShujaiya','GazaShujaiyaIntegration_2026-10-02'),('GazaRimal','PermanentIntegration_2026-10-02')]}
CHILD='/Game/Project/Shared/RoadBLD/Materials/MI_RoadBLD_Asphalt_Road_Worn_GeoCity'
PARENT='/RoadBLD/RoadBLD/DefaultRoadKit/Materials/MI_RoadBLD_Asphalt_Road_Worn'
FROZEN={'geocity_roadbld_junctions.py':'dfb65168e6cdc6f5e75a98d63b2f862f0c1e5eca13bf8d93741be5accaf62802','geocity_roadbld_workflow.py':'a75d78d4eff44068109ab56fae46f34a074f4c0b141409ca2f764dfb26bc645a','geocity_roadbld_grounding.py':'62a8a28a03803fb845bafa2ce820b742a83cb35134b25cf192fcd532bbf6233d','geocity_roadbld_clip.py':'872f4814060a214cdf4238a8ae8c7b9a0a819364bc4f5ea486e573d396980211'}
ACTIVE=[]
_GUARD_JOURNAL={}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,data):
    with Path(p).open('w',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def journal(s,event,**kw):
    with s['journal'].open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),event=event,**kw))+'\n');f.flush();os.fsync(f.fileno())
def call(s,label,fn):
    state=None;emit=True
    if label in ('native.guard','parent.guard'):
        state=_GUARD_JOURNAL.setdefault((str(s['journal']),label),{'last':float('-inf'),'calls':0,'omitted':0})
        state['calls']+=1;now=time.monotonic();emit=now-state['last']>=1.0
        if emit:
            journal(s,'BEFORE_NATIVE',operation=label,guard_calls=state['calls'],omitted_log_pairs=state['omitted'])
            state.update(last=now,omitted=0)
        else:state['omitted']+=1
    else:journal(s,'BEFORE_NATIVE',operation=label)
    try:value=fn()  # Every original guard executes unconditionally, every call.
    except Exception:
        journal(s,'NATIVE_EXCEPTION',operation=label,error=traceback.format_exc(),guard_counters=state)
        raise
    if emit:journal(s,'AFTER_NATIVE',operation=label)
    return value
def path(s,obj,label):return call(s,label+'.path',obj.get_path_name) if obj else None
def guards():
    assert os.getpid()==21780
    assignments=read(HERE/'ASSIGNMENTS.json');assert assignments['one_editor_pid']==21780 and assignments['tasks']['task2_delivery']['editor_calls_authorized']
    lease=(ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
    assert 'assigned_editor_PID=21780' in lease and 'worker_thread_id=01a102e1-25e6-7f13-b593-4988290a283b' in lease and 'ASTRA_FRESH_ORDINARY_APPEARANCE_DELIVERY' in lease
    for name,digest in FROZEN.items():assert hashlib.sha256((ROOT/'Content/Python'/name).read_bytes()).hexdigest()==digest,name
    assert (HERE/'MANAGER_FRESH_DELIVERY_ACTIVATION.json').is_file()
def dirty(s):
    import unreal as u
    return {kind:[path(s,x,kind) for x in call(s,'dirty_'+kind,fn)] for kind,fn in [('maps',u.EditorLoadingAndSavingUtils.get_dirty_map_packages),('content',u.EditorLoadingAndSavingUtils.get_dirty_content_packages)]}
def idle(s):
    import unreal as u
    for name in ['geocity_bank_workflow','geocity_roadbld_workflow']:
        for x in getattr(sys.modules.get(name),'ACTIVE',[]):
            assert all(getattr(x,k,None) is None for k in ['watch_tick','save_tick','tick_handle'])
    api=call(s,'official_API',u.HoudiniPublicAPIBlueprintLib.get_api)
    assert call(s,'cooking_paused',api.is_asset_cooking_paused)
    settings=call(s,'autosave_settings',lambda:u.load_object(None,'/Script/UnrealEd.Default__EditorLoadingSavingSettings'))
    assert not call(s,'autosave_disabled',lambda:settings.get_editor_property('bAutoSaveEnable'))
    return api
def readiness(s):
    import unreal as u
    api=idle(s);s['report']['dirty_before']=dirty(s)
    assert not any(s['report']['dirty_before'].values())
    valid=call(s,'official_session_before',api.is_session_valid)
    if not valid:call(s,'official_create_session',api.create_session)
    s['report']['official_session_valid']=call(s,'official_session_after',api.is_session_valid)
    s['report']['Engine_paused']=call(s,'cooking_paused_after_session',api.is_asset_cooking_paused)
    auth=call(s,'WorldBLD_auth_subsystem',lambda:u.get_editor_subsystem(u.WorldBLDAuthSubsystem))
    s['report']['RoadBLD_license']=call(s,'RoadBLD_has_license',lambda:auth.has_license_for_tool('RoadBLD'))
    s['report']['dirty_after']=dirty(s)
    assert s['report']['Engine_paused']
    assert s['report']['official_session_valid'],'Official Engine session initialization failed'
    assert s['report']['RoadBLD_license'],'RoadBLD needs native signed-in licensed session'
def baseline(s):
    import unreal as u
    import geocity_roadbld_clip as clip
    idle(s);p=read(PROFILES['GazaShujaiya']);c=p['road_provider_contract'];last=read(PROFILES['GazaShujaiya'].with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json'))
    world=call(s,'world',lambda:u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world())
    assert path(s,call(s,'world_package',world.get_outermost),'world_package')==p['map']
    actors=call(s,'all_level_actors',lambda:u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    bypath={path(s,a,'actor'):a for a in actors}
    assert len(c['owned_actor_paths'])==136 and len(c['native_component_bindings'])==89 and len(c['named_generated_dependency_paths'])==80
    assert len(last['baked_actor_paths'])==42
    for value in c['owned_actor_paths']+last['baked_actor_paths']:assert value in bypath,value
    bindings=[]
    for i,row in enumerate(c['native_component_bindings']):
        components=call(s,f'binding{i}.components',lambda a=bypath[row['actor']]:a.get_components_by_class(u.StaticMeshComponent))
        matches=[x for x in components if path(s,x,f'binding{i}.component')==row['component']];assert len(matches)==1
        component=matches[0];mesh=call(s,f'binding{i}.mesh',lambda:component.get_editor_property('static_mesh'))
        actual={'component':row['component'],'mesh':path(s,mesh,f'binding{i}.mesh'),'material_slots':call(s,f'binding{i}.materials',lambda:clip._materials(component)),'component_world_transform':call(s,f'binding{i}.transform',lambda:clip._transform(component.get_world_transform())),'collision':call(s,f'binding{i}.collision',lambda:clip._collision(component,mesh))}
        for key in ['mesh','material_slots','component_world_transform','collision']:assert actual[key]==row[key],str((i,key))
        bindings.append(actual)
    for dep in c['named_generated_dependency_paths']:assert call(s,'dependency_exists:'+dep,lambda dep=dep:u.EditorAssetLibrary.does_asset_exist(dep))
    s['report'].update(owned_actors=136,bindings=bindings,native_dependencies=80,HDA_baked_actors=42,dirty_after=dirty(s),geometry_recomputed=False)
    assert not any(s['report']['dirty_after'].values())
def material(s):
    import unreal as u
    idle(s);assert not any(dirty(s).values())
    assert not call(s,'child_exists',lambda:u.EditorAssetLibrary.does_asset_exist(CHILD)),'Child already exists; inspect before mutation'
    parent=call(s,'load_original_worn_parent',lambda:u.load_asset(PARENT));assert parent
    factory=call(s,'create_MI_factory',u.MaterialInstanceConstantFactoryNew)
    assettools=call(s,'asset_tools',u.AssetToolsHelpers.get_asset_tools)
    child=call(s,'create_named_shared_MI',lambda:assettools.create_asset(CHILD.rsplit('/',1)[1],CHILD.rsplit('/',1)[0],u.MaterialInstanceConstant,factory));assert child
    call(s,'set_direct_original_parent',lambda:u.MaterialEditingLibrary.set_material_instance_parent(child,parent))
    assert call(s,'set_MV_PatchMult_1',lambda:u.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(child,'MV_PatchMult',1.0))
    s['report']['parent']=path(s,call(s,'read_child_parent',lambda:child.get_editor_property('parent')),'child_parent')
    s['report']['effective_MV_PatchMult']=call(s,'read_effective_MV_PatchMult',lambda:u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(child,'MV_PatchMult'))
    scalars=call(s,'local_scalar_parameters',lambda:child.get_editor_property('scalar_parameter_values'))
    s['report']['local_scalar_overrides']=[{'name':str(x.parameter_info.name),'value':float(x.parameter_value)} for x in scalars]
    assert s['report']['parent']==PARENT+'.'+PARENT.rsplit('/',1)[1]
    assert s['report']['local_scalar_overrides']==[{'name':'MV_PatchMult','value':1.0}]
    for name in ['texture_parameter_values','vector_parameter_values']:assert not call(s,'read_'+name,lambda name=name:child.get_editor_property(name))
    assert s['report']['effective_MV_PatchMult']==1.0
    assert call(s,'named_shared_child_save',lambda:u.EditorAssetLibrary.save_loaded_asset(child,only_if_is_dirty=False))
    s['report'].update(asset=CHILD,dirty_after=dirty(s))
    assert not any(s['report']['dirty_after'].values())
def generate_shuj(s):generate(s,'GazaShujaiya')
def material_finish(s):
    import unreal as u
    idle(s);values=dirty(s);assert values=={'maps':[],'content':[CHILD]}
    child=call(s,'load_existing_new_child',lambda:u.load_asset(CHILD));parent=call(s,'load_original_parent',lambda:u.load_asset(PARENT))
    assert call(s,'read_parent',lambda:child.get_editor_property('parent'))==parent
    scalars=call(s,'read_local_scalars',lambda:child.get_editor_property('scalar_parameter_values'))
    assert len(scalars)==1 and str(scalars[0].parameter_info.name)=='MV_PatchMult' and scalars[0].parameter_value==1.0
    for name in ['texture_parameter_values','vector_parameter_values']:assert not call(s,'read_'+name,lambda name=name:child.get_editor_property(name))
    def normalize(value):
        if isinstance(value,u.Object):return value.get_path_name()
        if isinstance(value,u.LinearColor):return [value.r,value.g,value.b,value.a]
        return value
    effective={}
    for kind in ['scalar','vector','texture','static_switch']:
        names=call(s,kind+'.names',lambda kind=kind:getattr(u.MaterialEditingLibrary,'get_'+kind+'_parameter_names')(parent))
        row={}
        for name in names:
            getter=getattr(u.MaterialEditingLibrary,'get_material_instance_'+kind+'_parameter_value')
            before=call(s,kind+'.original.'+str(name),lambda name=name:getter(parent,name))
            after=call(s,kind+'.child.'+str(name),lambda name=name:getter(child,name))
            expected=1.0 if kind=='scalar' and str(name)=='MV_PatchMult' else normalize(before)
            assert normalize(after)==expected,kind+':'+str(name)
            row[str(name)]=normalize(after)
        effective[kind]=row
    s['report'].update(asset=CHILD,direct_parent=PARENT,local_scalar_overrides=[{'name':'MV_PatchMult','value':1.0}],effective_parameters=effective,other_effective_parameters_match_original=True,API_return_value_false_but_readback_proved_override_applied=True)
    write(s['receipt'],s['report'])
    assert call(s,'named_shared_child_save',lambda:u.EditorAssetLibrary.save_loaded_asset(child,only_if_is_dirty=False))
    s['report']['dirty_after']=dirty(s);assert not any(s['report']['dirty_after'].values())
def material_readback(s):
    import unreal as u
    idle(s)
    s['report']['dirty']=dirty(s)
    for label,value in [('child',CHILD),('original',PARENT)]:
        obj=call(s,'load_'+label,lambda value=value:u.load_asset(value));assert obj
        row={'path':path(s,obj,label),'parent':path(s,call(s,label+'.parent',lambda:obj.get_editor_property('parent')),label+'.parent')}
        row['scalar_names']=[str(x) for x in call(s,label+'.scalar_names',lambda:u.MaterialEditingLibrary.get_scalar_parameter_names(obj))]
        row['scalar_values']={name:call(s,label+'.effective.'+name,lambda name=name:u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(obj,name)) for name in row['scalar_names'] if 'patch' in name.lower()}
        row['local_scalars']=[{'name':str(x.parameter_info.name),'value':float(x.parameter_value),'association':str(x.parameter_info.association),'index':int(x.parameter_info.index)} for x in call(s,label+'.local_scalars',lambda:obj.get_editor_property('scalar_parameter_values'))]
        s['report'][label]=row
def generate_rimal(s):generate(s,'GazaRimal')
def generate(s,area):
    import unreal as u
    import geocity_bank_workflow as bank
    from geocity_editor_action import acknowledged_cook_leftovers
    api=idle(s);assert call(s,'session_valid',api.is_session_valid)
    p=read(PROFILES[area]);assert p['roadbld_workflow']['settings']['road_material']==CHILD
    world=call(s,'world',lambda:u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world())
    assert path(s,call(s,'world_package',world.get_outermost),'world_package')==p['map']
    values=dirty(s);assert not values['maps']
    acknowledged=call(s,'acknowledge_exact_unsaved_unreferenced_stages',lambda:acknowledged_cook_leftovers(ROOT,values['content'])) if values['content'] else set()
    assert set(values['content']).issubset(acknowledged)
    s['report'].update(area=area,profile=str(PROFILES[area]),reviewed_dirty=values['content'],source_freeze=FROZEN,phase='ordinary_run_starting')
    write(s['receipt'],s['report'])
    # Same lifecycle invoked by the normal menu; retain root-owned lease.
    run=call(s,'ordinary_geocity_bank_workflow.run_regenerate',lambda:bank.run(str(PROFILES[area]),'regenerate',reviewed_dirty_packages=values['content'],release_menu_lease=False))
    s['report'].update(phase=run.state['phase'],workflow_receipt=str(run.state_path),ordinary_operation_started=True)
def schedule(step):
    guards();assert not any(s['handle'] is not None for s in ACTIVE)
    import unreal as u
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'handle':None,'journal':HERE/('FRESH_'+step+'_'+stamp+'.jsonl'),'receipt':HERE/('FRESH_'+step+'_'+stamp+'.json'),'report':{'status':'scheduled','step':step,'pid':os.getpid()}}
    def tick(dt):
        call(s,'unregister_one_shot',lambda:u.unregister_slate_post_tick_callback(s['handle']));s['handle']=None
        try:guards();globals()[step](s);s['report']['status']='passed'
        except Exception:s['report'].update(status='stopped',error=traceback.format_exc())
        write(s['receipt'],s['report']);journal(s,'STEP_END',status=s['report']['status'])
    write(s['receipt'],s['report']);ACTIVE.append(s)
    s['handle']=call(s,'register_one_shot',lambda:u.register_slate_post_tick_callback(tick))
    return str(s['receipt'])
