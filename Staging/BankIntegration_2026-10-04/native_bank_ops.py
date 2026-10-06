"""Bank-only native operations. Every entry requires a current explicit editor lease."""
import hashlib
import json
import os
import time
from pathlib import Path
import unreal
import bank_contracts as C

MAT_ROOT='/Game/Project/Shared/ModelBank/Materials/BankIntegration_20261004'
E=unreal.EditorAssetLibrary
M=unreal.MaterialEditingLibrary

def dirty():
    return {'content':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
            'maps':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())}

def preflight():
    lease=[s for s in (C.ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if s.strip()][-1]
    import geocity_editor_action
    import geocity_runtime_guard
    fields=geocity_editor_action.lease_fields(lease)
    assignment=C.read(C.HERE/'ASSIGNMENT.json')
    assert fields.get('OWNER')=='CODEX_BANK_INTEGRATION' and fields.get('assigned_editor_PID')==str(os.getpid()),'bank_does_not_own_current_editor'
    assert fields.get('operator_thread_id')==assignment['thread'] and fields.get('manager_thread_id')==assignment['system_owner'],'bank_lease_identity_mismatch'
    activation=C.read(C.ROOT/'Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json')
    assert activation['manager_thread_id']==assignment['system_owner'] and activation['bank_thread_id']==assignment['thread'],'bank_activation_identity_mismatch'
    assert fields.get('activation')=='MANAGER_ACTIVATED' and fields.get('native_authorized_now')!='false','bank_lease_is_not_write_activation'
    assert activation.get('native_authorized_now') is True and activation.get('assigned_editor_PID')==os.getpid(),'bank_native_authoring_paused'
    geocity_runtime_guard.verify()
    assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused(),'official_engine_not_paused'
    state=dirty();handoff=C.read(C.HERE/'EDITOR_ACQUIRED.json')
    assert os.getpid()==handoff['pid']
    assert geocity_editor_action.lease_fields(handoff['lease']).get('manager_thread_id')==assignment['system_owner'],'bank_checkpoint_predates_manager_activation'
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
    assert world==handoff['world'],'world_changed_without_bank_checkpoint'
    assert set(state['maps']).issubset(set(handoff.get('allowed_dirty_maps',[]))),state
    allowed=set(handoff.get('allowed_dirty_content',[]))
    assert all(p in allowed or p.startswith(MAT_ROOT+'/') or p.startswith('/Game/Project/Shared/ModelBank/Prepared/') for p in state['content']),state
    return {'pid':os.getpid(),'world':world,'dirty':state}

def dependency_closure(pkg):
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    options=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_game_package_references=True,include_editor_only_package_references=False)
    seen=set();missing=[];todo=[pkg]
    while todo:
        p=todo.pop()
        if p in seen or p.startswith('/Script/'):continue
        seen.add(p)
        if not registry.get_assets_by_package_name(p):missing.append(p)
        todo.extend(str(v) for v in (registry.get_dependencies(p,options) or []))
    return {'packages':sorted(seen),'missing':sorted(missing)}

def measure(mesh):
    sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    desc=mesh.get_static_mesh_description(0);assert desc
    nv=desc.get_vertex_count();low=[float('inf')]*3;high=[-float('inf')]*3
    vertices=[]
    for n in range(nv):
        vid=unreal.VertexID(n);assert desc.is_vertex_valid(vid),'sparse_vertex_ids_not_certified'
        v=desc.get_vertex_position(vid);v=[v.x,v.y,v.z];vertices.append(v)
        low=[min(a,b) for a,b in zip(low,v)];high=[max(a,b) for a,b in zip(high,v)]
    bottom=[v for v in vertices if v[2]<=low[2]+1.0]
    support={'tolerance_cm':1.0,'vertex_count':len(bottom),'xy_min':[min(v[i] for v in bottom) for i in (0,1)],'xy_max':[max(v[i] for v in bottom) for i in (0,1)]}
    return {'bounds_cm':{'min':low,'max':high},'dimensions_cm':[b-a for a,b in zip(low,high)],'source_vertices':nv,
        'triangles':desc.get_triangle_count(),'bottom_support':support,'uv_channels':sub.get_num_uv_channels(mesh,0),
        'lod_count':sub.get_lod_count(mesh),'simple_collision_count':sub.get_simple_collision_count(mesh),'convex_collision_count':sub.get_convex_collision_count(mesh),
        'material_slots':[{'slot':i,'name':str(s.material_slot_name),'imported_name':str(s.get_editor_property('imported_material_slot_name')),'path':s.material_interface.get_path_name() if s.material_interface else None} for i,s in enumerate(mesh.static_materials)]}

def inspect_candidates(ids=None):
    before=preflight();path=C.HERE/'NATIVE_CONTACT_READBACK.json';results=C.read(path) if path.exists() else {}
    for job in C.read(C.HERE/'NATIVE_CONFIGURATIONS.json')['rows']:
        aid=job['asset_id']
        if ids and aid not in ids:continue
        assert C.sha(C.package_file(job['object_path']))==job['package_sha256'],aid
        mesh=unreal.load_asset(job['object_path']);assert isinstance(mesh,unreal.StaticMesh)
        data=measure(mesh);assert data['uv_channels']>0
        data.update(asset_id=aid,path=job['object_path'],source_sha256=job['package_sha256'],
            dependencies=dependency_closure(job['object_path'].split('.')[0]),pid=os.getpid(),
            ready=False,reason='native_measurement_complete_individual_contact_and_material_review_required')
        results[aid]=data;C.write(path,results)
    assert dirty()==before['dirty'],'inspection_unexpected_dirty_state'
    print(json.dumps({'native_contact_records':len(results),'dirty_unchanged':True}))
    return results

def compatible_copy(source,created,copies):
    key=source.get_path_name()
    if key in copies:return copies[key]
    # Previously retained compatible materials can be reused without modifying their packages.
    if key.startswith('/Game/Project/Shared/ModelBank/Materials/Instancing/') and M.has_material_usage(source,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES):
        copies[key]=source;return source
    is_base=isinstance(source,unreal.Material)
    assert is_base or isinstance(source,unreal.MaterialInstanceConstant),key
    target=MAT_ROOT+'/'+('M_' if is_base else 'MI_')+hashlib.sha256(key.encode()).hexdigest()[:16]
    exists=E.does_asset_exist(target)
    copied=unreal.load_asset(target) if exists else E.duplicate_asset(key,target)
    assert copied and copied.get_path_name().startswith(MAT_ROOT+'/')
    copies[key]=copied
    if not exists:
        if is_base:
            copied.set_editor_property('used_with_instanced_static_meshes',True)
            copied.set_editor_property('automatically_set_usage_in_editor',False)
            M.recompile_material(copied)
        else:
            copied.set_editor_property('parent',compatible_copy(source.get_editor_property('parent'),created,copies))
            M.update_material_instance(copied)
        created[target]=copied
    assert M.has_material_usage(copied,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES),target
    return copied

def prepare_native_materials(ids=None):
    before=preflight();created={};copies={}
    dest=C.HERE/'NATIVE_INSTANCE_MATERIALS.json';results=C.read(dest) if dest.exists() else {'mesh_slots':{},'saved_paths':[],'copies':{}}
    for job in C.read(C.HERE/'NATIVE_CONFIGURATIONS.json')['rows']:
        if ids and job['asset_id'] not in ids:continue
        mesh=unreal.load_asset(job['object_path']);assert isinstance(mesh,unreal.StaticMesh)
        source_slots=job['existing_instance_materials'] or [s.material_interface.get_path_name() for s in mesh.static_materials]
        assert len(source_slots)==len(mesh.static_materials) and all(source_slots)
        result=[compatible_copy(unreal.load_asset(p),created,copies).get_path_name() for p in source_slots]
        results['mesh_slots'][job['object_path']]=result
    for path in sorted(created):assert E.save_asset(path,only_if_is_dirty=True),path
    results['saved_paths']=sorted(set(results['saved_paths'])|set(created))
    results['copies'].update({a:b.get_path_name() for a,b in copies.items()})
    results['originals_unchanged']=all(C.sha(C.package_file(j['object_path']))==j['package_sha256'] for j in C.read(C.HERE/'NATIVE_CONFIGURATIONS.json')['rows'])
    C.write(dest,results)
    unexpected=set(dirty()['content'])-set(before['dirty']['content'])
    assert not unexpected and dirty()['maps']==before['dirty']['maps'],dirty()
    print(json.dumps({'saved_materials':len(created),'configured_meshes':len(results['mesh_slots']),'native_original_meshes_unchanged':results['originals_unchanged']}))
    return results

def apply_building_normal_corrections():
    before=preflight()
    slots=C.read(C.HERE/'NATIVE_INSTANCE_MATERIALS.json')
    jobs={j['asset_id']:j for j in C.read(C.HERE/'NATIVE_CONFIGURATIONS.json')['rows']}
    receipts=[]
    for correction in C.read(C.HERE/'BUILDING_MATERIAL_CORRECTIONS.json'):
        job=jobs[correction['native_catalog_asset_id']]
        changes=[]
        for original,copy_path in zip(job['material_slots'],slots['mesh_slots'][job['object_path']]):
            # Match the exact source slot/material names; no broad material replacement.
            normalize=lambda s:''.join(c.lower() for c in s if c.isalnum())
            matching=[c for c in correction['material_changes'] if normalize(c['material'])==normalize(original['name'])]
            if not matching:continue
            assert copy_path.startswith(MAT_ROOT+'/'),'only_this_task_material_derivatives_can_be_corrected'
            mat=unreal.load_asset(copy_path);assert isinstance(mat,unreal.Material)
            used=[t.get_path_name() for t in M.get_used_textures(mat)]
            assert any('T_CracksStreet_normal_076f5fec4437' in t for t in used),'unexpected_normal_source'
            old=M.get_material_property_input_node(mat,unreal.MaterialProperty.MP_NORMAL)
            assert old is not None,'normal_already_disconnected_requires_receipt_reconciliation'
            neutral=M.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector)
            neutral.set_editor_property('constant',unreal.LinearColor(0,0,1,1))
            assert M.connect_material_property(neutral,'',unreal.MaterialProperty.MP_NORMAL)
            M.recompile_material(mat)
            assert M.get_material_property_input_node(mat,unreal.MaterialProperty.MP_NORMAL)==neutral
            E.set_metadata_tag(mat,'BankNormalCorrection','Neutral tangent normal replaces unrelated T_CracksStreet normal; original material preserved')
            assert E.save_asset(copy_path,only_if_is_dirty=True)
            changes.append({'native_copy':copy_path,'original_material':original['path'],'prior_normal_node':old.get_name(),'new_normal':[0,0,1]})
        assert len(changes)==len(correction['material_changes']),job['asset_id']
        receipts.append({'asset_id':job['asset_id'],'saved_material_corrections':changes,'source_receipt':correction,'native_mesh_unchanged':C.sha(C.package_file(job['object_path']))==job['package_sha256']})
    C.write(C.HERE/'NATIVE_BUILDING_MATERIAL_CORRECTIONS.json',receipts)
    assert dirty()==before['dirty'],dirty()
    return receipts
