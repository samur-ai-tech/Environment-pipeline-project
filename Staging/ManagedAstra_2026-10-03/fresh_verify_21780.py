"""Saved delivery inspection and reopen, staged on fresh GameThread objects."""
import importlib.util,json,runpy,sys
import fresh_delivery_21780 as d

def execute(s,area,stage):
    import unreal as u
    d.idle(s);profile=d.PROFILES[area];p=d.read(profile)
    saved=d.read(profile.with_name('WORKFLOW_STATE.json'))
    assert saved['phase']=='baked_saved_verified'
    contract=p['road_provider_contract'];assert contract['saved'] and contract['adapter_settings']['road_material']==d.CHILD
    s['report'].update(area=area,stage=stage,revision=contract['revision'])
    d.write(s['receipt'],s['report'])
    if stage=='material':
        d.material_readback(s)
        child=s['report']['child'];original=s['report']['original']
        assert child['parent']==original['path']
        assert child['scalar_values']['MV_PatchMult']==1.0
        assert child['scalar_values']['MV_PatchScale']==original['scalar_values']['MV_PatchScale']
        assert child['local_scalars']==[{'name':'MV_PatchMult','value':1.0,'association':'<MaterialParameterAssociation.GLOBAL_PARAMETER: 2>','index':-1}]
        s['report']['effective_shared_child_override_verified']=True
        return
    if stage=='reopen':
        namespace=runpy.run_path(str(d.ROOT/'Staging/AppearanceRepair_2026-10-03/reopen_retained_area.py'))
        s['report']['bank_reopen_receipt']=d.call(s,'load_same_named_map_and_inspect_HDA_native_anchors',lambda:namespace['reopen_area'](str(profile)))
        return
    target=d.ROOT/'Staging/AppearanceRepair_2026-10-03/inspect_native_road_delivery.py'
    assert d.hashlib.sha256(target.read_bytes()).hexdigest()=='bfbf0451515d783d34100998319ee18b653843b7351dbc32abc03049cddd2255'
    spec=importlib.util.spec_from_file_location('fresh_native_inspector_21780',target)
    inspector=importlib.util.module_from_spec(spec);sys.modules[spec.name]=inspector;spec.loader.exec_module(inspector)
    for name in ['_component_snapshot','_inspect_grounding','_measure_all','_discover']:
        original=getattr(inspector,name)
        def instrument(*args,_name=name,_original=original,**kwargs):
            return d.call(s,'inspector.'+_name,lambda:_original(*args,**kwargs))
        setattr(inspector,name,instrument)
    context='saved_readback' if stage=='saved' else 'reopen_readback'
    result=d.call(s,'full_native_'+context,lambda:inspector.inspect_delivery(str(profile),context=context,max_seconds=300))
    s['report']['native_receipt']=result
    assert result['status']=='passed'
    actual=result['native_grounding_readback'];expected=contract['native_grounding_validation']
    for key,value in expected.items():
        if key!='elapsed_seconds':assert actual[key]==value,'Retained grounding field differs: '+key
    s['report']['all_recorded_grounding_fields_match_except_elapsed_seconds']=True

def schedule(area,stage):
    assert area in d.PROFILES and stage in ('saved','reopen','reopened','material')
    name=area+'_'+stage
    setattr(d,name,lambda s:execute(s,area,stage))
    return d.schedule(name)

def switch_rimal(s):
    import unreal as u
    from geocity_editor_action import acknowledged_cook_leftovers
    d.idle(s);values=d.dirty(s);assert not values['maps']
    assert set(values['content']).issubset(d.call(s,'acknowledge_exact_leftovers',lambda:acknowledged_cook_leftovers(d.ROOT,values['content'])))
    p=d.read(d.PROFILES['GazaRimal'])
    s['report']['named_target']=p['map']
    assert d.call(s,'load_existing_Rimal_named_map',lambda:u.EditorLoadingAndSavingUtils.load_map(p['map']))
    d.idle(s);s['report']['dirty_after']=d.dirty(s);assert not s['report']['dirty_after']['maps']

def schedule_switch():
    d.switch_rimal=switch_rimal
    return d.schedule('switch_rimal')
