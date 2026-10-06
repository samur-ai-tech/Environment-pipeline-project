"""Source-session native dependency export, only after root's one-writer activation.

This module never opens a project/editor. Native Migrate keeps source package
names; export goes to this supplier's staging Content folder. Relocation into
the required Prepared namespace is a separate unresolved writer operation.
"""
from pathlib import Path
import json
import os
import subprocess
import intake as I

def export(source_id, job_ids):
    import unreal
    act=I.read(I.HERE/'SOURCE_MIGRATION_ACTIVATION.json')
    assert act['manager_thread_id']=='01a106bc-2fde-7f23-9aa7-8ba413dc6245'
    assert act['source_id']==source_id and act['pid']==os.getpid()
    assert act['action']=='readonly_source_migrate_to_supplier_staging'
    assert act['queue_sha256']==I.sha(I.HERE/'READY_JOBS.json')
    assert sorted(act['job_ids'])==sorted(job_ids)
    fields=dict(part.split('=',1) for part in [x for x in (I.ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if x.strip()][-1].split() if '=' in part)
    assert fields.get('assigned_editor_PID')==str(os.getpid())
    assert fields.get('operator_thread_id')==act['operator_thread_id'] and fields.get('manager_thread_id')==act['manager_thread_id']
    assert fields.get('activation')=='MANAGER_ACTIVATED' and fields.get('scope')=='native_source_migration_to_staging'
    # Read-only process verification; does not spawn an Unreal process.
    raw=subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id) | ConvertTo-Json -Compress"],text=True).strip()
    pids=json.loads(raw) if raw else []
    if isinstance(pids,int):pids=[pids]
    assert pids==[os.getpid()],'not_the_sole_editor'
    jobs={j['job_id']:j for j in I.read(I.HERE/'READY_JOBS.json')['jobs']}
    selected=[jobs[j] for j in job_ids]
    assert selected and all(j['source_id']==source_id and j['operation']=='native_migrate_with_dependency_remap' for j in selected)
    project=Path(selected[0]['source_project']).resolve()
    assert Path(unreal.Paths.project_dir()).resolve()==project
    dirty=lambda: [p.get_path_name() for p in list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())+list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())]
    assert not dirty(),'source_session_must_be_clean'
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    opts=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_game_package_references=True,include_editor_only_package_references=False)
    todo=[j['source_object_path'].split('.')[0] for j in selected];seen=set();packages=[];scripts=[]
    for j in selected:assert I.sha(j['source_file'])==j['source_sha256']
    while todo:
        p=todo.pop()
        if p in seen:continue
        seen.add(p)
        if p.startswith('/Script/'):
            scripts.append(p);continue
        assert p.startswith(('/Game/','/Engine/')),'plugin_mount_requires_explicit_supported_migration:'+p
        data=registry.get_assets_by_package_name(p)
        assert data,'missing_registry_dependency:'+p
        classes=[str(a.asset_class_path.asset_name) for a in data]
        assert not any(c in ('World','Level','Blueprint','HoudiniAsset','DataTable') for c in classes),'excluded_world_generator_or_logic_dependency:'+p
        f=(project/'Content'/(p[6:]+'.uasset')) if p.startswith('/Game/') else Path(unreal.Paths.engine_content_dir()).resolve()/(p[8:]+'.uasset')
        assert f.is_file(),'missing_source_file:'+str(f)
        files=[{'file':str(f.with_suffix(e)),'sha256':I.sha(f.with_suffix(e)),'bytes':f.with_suffix(e).stat().st_size} for e in ['.uasset','.uexp','.ubulk','.uptnl'] if f.with_suffix(e).is_file()]
        packages.append({'package':p,'classes':classes,'files':files})
        todo.extend(str(x) for x in (registry.get_dependencies(p,opts) or []))
    receipt={'source_id':source_id,'pid':os.getpid(),'source_project':str(project),'job_ids':job_ids,'packages':packages,'script_dependencies':sorted(scripts),'engine_version':unreal.SystemLibrary.get_engine_version(),
        'namespace_remap_completed':False,'target_project_imported':False}
    I.write('Migration/'+source_id+'/SOURCE_CLOSURE.json',receipt)
    destination=I.HERE/'Migration'/source_id/'Content'
    destination.mkdir(parents=True,exist_ok=True)
    for r in packages:
        if not r['package'].startswith('/Game/'):continue
        for item in r['files']:
            target=destination/Path(item['file']).relative_to(project/'Content')
            assert not target.exists() or I.sha(target)==item['sha256'],'staged_migration_conflict:'+str(target)
    options=unreal.MigrationOptions(prompt=False,ignore_dependencies=False,asset_conflict=unreal.AssetMigrationConflict.SKIP)
    unreal.AssetToolsHelpers.get_asset_tools().migrate_packages([j['source_object_path'].split('.')[0] for j in selected],str(destination),options)
    for r in packages:
        for item in r['files']:
            assert I.sha(item['file'])==item['sha256'],'source_mutated'
            if r['package'].startswith('/Game/'):
                target=destination/Path(item['file']).relative_to(project/'Content')
                assert target.is_file() and I.sha(target)==item['sha256'],'migrated_file_missing_or_changed'
    assert not dirty(),'source_session_dirty_after_export'
    receipt.update(staged_native_packages=True,source_files_unchanged=True,source_dirty_unchanged=True,
                   target_path=str(destination),status='staged_native_export_requires_reviewed_namespace_remap')
    I.write('Migration/'+source_id+'/SOURCE_EXPORT.json',receipt)
    return receipt
