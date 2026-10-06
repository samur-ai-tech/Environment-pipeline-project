"""Inspect and export exact loaded dirty originals without saving or changing them."""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
import unreal
import bank_contracts as C

PACKAGES = [
    '/Game/Palms_Pack_01/Add_Props/Plants/Materials/MI_Plant_07_6_Leaves_G',
    '/Game/Palms_Pack_01/Add_Props/Plants/Materials/MI_Plant_07_6_Stem_G',
    '/Game/Palms_Pack_01/Add_Props/Plants/Meshes/SM_Plant_07_6_G'
]


def inspect():
    import geocity_editor_action as action
    import geocity_runtime_guard as guard
    lease = [s for s in (C.ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
    fields = action.lease_fields(lease)
    transfer = C.read(C.ROOT/'Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/STATE.json')
    assignment = C.read(C.HERE/'ASSIGNMENT.json')
    assert fields['assigned_editor_PID'] == str(os.getpid())
    assert fields['activation'] == 'INSPECTION_ONLY'
    assert fields['manager_thread_id'] == transfer['successor_manager_thread_id'] == assignment['system_owner']
    assert fields['operator_thread_id'] == assignment['thread']
    source_seal = guard.verify()
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    wrappers = [(a, unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,a)) for a in actors if a.get_class().get_name() == 'HoudiniAssetActor']

    def snapshot():
        return {'pid': os.getpid(), 'world': unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name(),
            'dirty_content': sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
            'dirty_maps': sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
            'cooking_paused': api.is_asset_cooking_paused(), 'official_session_valid': api.is_session_valid(),
            'autosave': unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
            'hda_flags': [{'actor':a.get_path_name(),'auto_cook':w.is_auto_cooking_enabled(),'auto_bake':w.is_auto_bake_enabled()} for a,w in wrappers],
            'callbacks': {name: sum(getattr(run,k,None) is not None for run in getattr(sys.modules.get(name),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction')) for name in ('geocity_bank_workflow','geocity_roadbld_workflow')}}

    before = snapshot()
    assert before['dirty_content'] == sorted(PACKAGES) and not before['dirty_maps'], before
    dest = C.HERE/'DirtyOriginals_Transfer'
    dest.mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    result = {'schema':'environmentpipeline.exact_dirty_original_diagnostic.v1','utc':stamp,'lease':lease,'before':before,'source_seal':source_seal,'rows':[],
        'native_saved':False,'native_reverted':False,'editors_closed':False,'user_edits_status':'Unknown. Dirty flags and log timing do not establish who changed the mesh or whether any user edit is intentional.'}

    def serialize(value):
        if value is None or isinstance(value,(str,int,float,bool)): return value
        if isinstance(value,unreal.Object): return value.get_path_name()
        if hasattr(value,'export_text'):
            try:return value.export_text()
            except Exception:pass
        try:
            if not isinstance(value,str): return [serialize(v) for v in value]
        except TypeError:pass
        return str(value)

    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    options=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_game_package_references=True,include_editor_only_package_references=False)
    prior=C.read(C.HERE/'NATIVE_CONTACT_READBACK.json')
    for pkg in PACKAGES:
        obj_path=pkg+'.'+pkg.rsplit('/',1)[1]
        obj=unreal.find_object(None,obj_path)
        assert obj is not None,('exact_object_not_loaded',obj_path)
        disk=C.package_file(pkg); stat=disk.stat()
        row={'path':obj_path,'class':obj.get_class().get_name(),'disk_file':str(disk),'disk_sha256':C.sha(disk),'disk_bytes':stat.st_size,'disk_mtime_utc':datetime.datetime.fromtimestamp(stat.st_mtime,datetime.timezone.utc).isoformat(),
             'registry_referencers':sorted(str(x) for x in registry.get_referencers(pkg,options)),
             'registry_dependencies':sorted(str(x) for x in registry.get_dependencies(pkg,options)), 'properties':{},'unavailable_properties':{}}
        names=['nanite_settings','static_materials','min_lod','lod_group','light_map_resolution','light_map_coordinate_index','body_setup','asset_import_data'] if isinstance(obj,unreal.StaticMesh) else ['parent','base_property_overrides','scalar_parameter_values','vector_parameter_values','texture_parameter_values','static_parameters','used_with_nanite','automatically_set_usage_in_editor']
        for name in names:
            try:row['properties'][name]=serialize(obj.get_editor_property(name))
            except Exception as exc:row['unavailable_properties'][name]=str(exc)
        if isinstance(obj,unreal.StaticMesh):
            known=next(v for v in prior.values() if v['path']==obj_path)
            row['previous_measured_source_sha256']=known['source_sha256']
            row['disk_matches_previous_measurement']=row['disk_sha256']==known['source_sha256']
            desc=obj.get_static_mesh_description(0)
            row['loaded_geometry_counts']={'vertices':desc.get_vertex_count(),'triangles':desc.get_triangle_count()}
            row['prior_geometry_counts']={'vertices':known['source_vertices'],'triangles':known['triangles']}
        task=unreal.AssetExportTask()
        export=dest/(stamp+'_'+obj.get_name()+'.t3d')
        task.set_editor_property('object',obj)
        task.set_editor_property('filename',str(export))
        task.set_editor_property('automated',True)
        task.set_editor_property('prompt',False)
        task.set_editor_property('exporter',unreal.ObjectExporterT3D())
        row['text_export_success']=unreal.Exporter.run_asset_export_task(task)
        row['text_export_errors']=serialize(task.get_editor_property('errors'))
        if export.exists(): row['text_export']={'path':str(export),'sha256':C.sha(export),'bytes':export.stat().st_size}
        row['disk_unchanged_after_export']=C.sha(disk)==row['disk_sha256']
        result['rows'].append(row)
    result['protected_files']=[]
    for rel,expected in transfer['protected_file_hashes'].items():
        actual=C.sha(C.ROOT/rel)
        result['protected_files'].append({'path':str(C.ROOT/rel),'expected_sha256':expected,'actual_sha256':actual,'matches':actual==expected})
    result['saved_import_preservation']=[]
    for p in sorted(C.HERE.glob('IMPORTED_external_*.json')):
        receipt=C.read(p)
        actual=C.sha(C.package_file(receipt['native_path']))
        result['saved_import_preservation'].append({'asset_id':receipt['asset_id'],'path':receipt['native_path'],'matches_receipt':actual==receipt['native_sha256']})
    result['after']=snapshot()
    result['state_unchanged']=result['before']==result['after']
    result['all_disk_originals_unchanged']=all(r['disk_unchanged_after_export'] for r in result['rows'])
    result['all_protected_files_unchanged']=all(r['matches'] for r in result['protected_files'])
    result['all_saved_imports_unchanged']=all(r['matches_receipt'] for r in result['saved_import_preservation'])
    C.write(dest/'DIAGNOSTIC.json',result)
    print(json.dumps({'receipt':str(dest/'DIAGNOSTIC.json'),'state_unchanged':result['state_unchanged'],'rows':result['rows'],'all_protected_files_unchanged':result['all_protected_files_unchanged'],'all_saved_imports_unchanged':result['all_saved_imports_unchanged']},ensure_ascii=False))


if __name__=='__main__': inspect()
