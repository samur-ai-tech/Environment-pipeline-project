"""Bounded read-only selected material values/settings; no material editor required."""
import datetime,hashlib,json,os,time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_clip as clip
import geocity_roadbld_junctions as junctions
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline');HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
p=bank.ACTIVE[-1];r=native.ACTIVE[-1];p.guard();r.guard()
assert os.getpid()==32752 and r.state['phase']=='failed_validating'
assert p.watch_tick is None and p.save_tick is None and r.tick_handle is None and not r._tick_running
assert p.api.is_asset_cooking_paused() and p.api.is_session_valid()
began=time.monotonic();lib=unreal.MaterialEditingLibrary
def val(x):
    if x is None or isinstance(x,(str,int,float,bool)):return x
    if isinstance(x,unreal.Object):return x.get_path_name()
    if isinstance(x,unreal.LinearColor):return [float(x.r),float(x.g),float(x.b),float(x.a)]
    if isinstance(x,(list,tuple,unreal.Array)):return [val(t) for t in x]
    return str(x)
def prop(x,k):
    try:return {'supported':True,'value':val(x.get_editor_property(k))}
    except Exception:return {'supported':False}
def ledger():
    return [{'component':c.get_path_name(),'mesh':native._path(c.static_mesh),'materials':clip._materials(c),'transform':clip._transform(c.get_world_transform())}
      for a in r.native_geos() for c in a.get_components_by_class(unreal.StaticMeshComponent)]
def dirty():return {'maps':sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),'content':sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
before=ledger();owned=junctions._owned_state(r);dirty_before=dirty();checkpoint=junctions._sha(r.junction_repair)
row_index=next(i for i,row in enumerate(r.plan['roads']) if row['piece_id']=='41254867:0')
road=r.roads[row_index]
geos=[a for a in r.native_geos() if road in list(native._get(a,'SourceRoads'))]
bindings=[];selected={}
for a in geos:
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.static_mesh is None:continue
        entry={'geo':a.get_path_name(),'component':c.get_path_name(),'mesh':native._path(c.static_mesh),'source_refs':[native._path(x) for x in native._get(a,'SourceRoads')],'slots':[]}
        for index in [0,1]:
            if index>=c.get_num_materials():continue
            material=c.get_material(index);entry['slots'].append({'index':index,'material':material.get_path_name()});selected[material.get_path_name()]=material
        bindings.append(entry)
profile=json.loads((ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json').read_text(encoding='utf-8-sig'))
natural=unreal.load_object(None,profile['landscape_material']);assert natural
selected[natural.get_path_name()]=natural
landscape=unreal.load_object(None,r.landscape_sampler.path)
textures={};materials=[]
for path,material in selected.items():
    p.guard();r.guard();assert time.monotonic()-began<90
    chain=[];current=material
    while current:
        item={'path':current.get_path_name(),'class':current.get_class().get_name(),'effective_parameters':{}}
        inst=isinstance(current,unreal.MaterialInstanceConstant)
        for kind in ['scalar','vector','texture','static_switch']:
            names=getattr(lib,'get_'+kind+'_parameter_names')(current)
            getter=getattr(lib,('get_material_instance_' if inst else 'get_material_default_')+kind+'_parameter_value')
            values={}
            for name in names:
                value=getter(current,name);values[str(name)]=val(value)
                if kind=='texture' and value:textures[value.get_path_name()]=value
            item['effective_parameters'][kind]=values
        if inst:
            item['local_override_arrays']={k:prop(current,k) for k in ['scalar_parameter_values','vector_parameter_values','texture_parameter_values','base_property_overrides']}
            parent=current.get_editor_property('parent');item['parent']=val(parent)
        else:
            parent=None;item['settings']={k:prop(current,k) for k in ['blend_mode','two_sided','shading_model','use_material_attributes']}
            # Expression readback only; no active material editor, update, compile or edits.
            nodes=[]
            for e in lib.get_material_expressions(current):
                kind=e.get_class().get_name()
                properties={}
                for name in ['parameter_name','texture','sampler_type','coordinate_index','u_tiling','v_tiling','r','g','b','a','const_a','const_b','default_value','material_function','desc']:
                    v=prop(e,name)
                    if v['supported']:properties[name]=v['value']
                inputs={}
                for name in ['coordinates','input','a','b','alpha','x','y','z','value','min','max']:
                    try:
                        iv=e.get_editor_property(name)
                        source=iv.get_editor_property('expression')
                        inputs[name]={'expression':val(source),'output_index':val(iv.get_editor_property('output_index'))}
                    except Exception:pass
                if properties or inputs:nodes.append({'path':e.get_path_name(),'class':kind,'properties':properties,'inputs':inputs})
            item['root_expression_readback']=nodes
        chain.append(item);current=parent
        assert len(chain)<8
    used=lib.get_material_used_textures(material)
    for tex in used:textures[tex.get_path_name()]=tex
    materials.append({'selected_material':path,'chain':chain,'used_textures':[val(t) for t in used]})
texture_rows=[]
for path,tex in textures.items():
    item={'path':path,'class':tex.get_class().get_name(),'settings':{k:prop(tex,k) for k in ['srgb','compression_settings','compression_no_alpha','lod_group','filter','address_x','address_y','virtual_texture_streaming','flip_green_channel','mip_gen_settings']}}
    if isinstance(tex,unreal.Texture2D):item['size_xy']=[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()]
    texture_rows.append(item)
assert before==ledger() and owned==junctions._owned_state(r) and checkpoint==junctions._sha(r.junction_repair) and dirty()==dirty_before
assert p.watch_tick is None and p.save_tick is None and r.tick_handle is None
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_SELECTED_STREET_MATERIAL_READBACK_'+stamp+'.json')
data={'status':'READ_ONLY_SELECTED_MATERIAL_MEASUREMENT_COMPLETE','utc':stamp,'pid':os.getpid(),'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),
 'label':'UNSAVED_CURRENT_CANDIDATE','source_piece_id':'41254867:0','source_road_actor':road.get_path_name(),'actual_street_bindings':bindings,
 'exact_current_export_landscape':r.landscape_sampler.path,'landscape_material_readback':prop(landscape,'landscape_material'),'selected_natural_profile_material':natural.get_path_name(),
 'materials':materials,'textures':texture_rows,'elapsed_seconds':time.monotonic()-began,'callbacks':0,'bound_ledger_sha256':junctions._sha(before),'participants_sha256':junctions._sha(owned),
 'checkpoint_sha256':checkpoint,'bound_participants_checkpoint_dirty_packages_unchanged':True,'official_engine_paused':True,'official_engine_valid':True,
 'no_material_edit_shader_compilation_helper_reload_cook_rebuild_or_save':True}
receipt.write_text(json.dumps(data,indent=2)+'\n')
(HERE/'TASK2_SELECTED_MATERIAL_STATUS.json').write_text(json.dumps({'status':data['status'],'receipt':str(receipt),'sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'bytes':receipt.stat().st_size,'selected_material_count':len(materials),'used_or_parameter_texture_count':len(texture_rows),'elapsed_seconds':data['elapsed_seconds']},indent=2)+'\n')
print(json.dumps({'receipt':str(receipt),'materials':len(materials),'textures':len(texture_rows),'elapsed_seconds':data['elapsed_seconds']}))
