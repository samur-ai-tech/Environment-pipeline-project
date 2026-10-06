"""Two explicit source-session phases: read closure, then native migrate to target.
Never launches an editor. Root must grant the exact temporary target namespace;
all source originals remain read-only. Target remapping is in migration_remap.py.
"""
from pathlib import Path
import json
import os
import subprocess
from . import intake as I
from . import authority as A
from . import integrity as V


def _preflight(action,activation_path):
    import unreal
    act=I.read(activation_path);m,mp,fields=A.lease(action,act)
    assert fields.get('OWNER')=='CODEX_BANK_INTEGRATION'
    assert fields.get('scope')=='native_source_migration','source_session_scope_required'
    raw=subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id) | ConvertTo-Json -Compress"],text=True).strip()
    pids=json.loads(raw) if raw else []
    if isinstance(pids,int):pids=[pids]
    assert pids==[os.getpid()],'not_sole_editor'
    dirty=list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())+list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    assert not dirty,'source_session_dirty'
    return act,m,mp


def capture(source_id,job_ids,activation_path):
    import unreal
    act,m,mp=_preflight('capture_native_source_closure',activation_path)
    assert act['source_id']==source_id and sorted(act['job_ids'])==sorted(job_ids)
    assert job_ids and len(job_ids)==len(set(job_ids))
    jobs={j['job_id']:j for j in I.read(I.HERE/'READY_JOBS.json')['jobs']}
    selected=[jobs[j] for j in job_ids]
    assert all(j['source_id']==source_id and j['operation']=='native_migrate_with_dependency_remap' and j['status']!='blocked_identity_ambiguity' for j in selected)
    project=Path(selected[0]['source_project']).resolve()
    assert project!=I.ROOT and Path(unreal.Paths.project_dir()).resolve()==project
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    assert not registry.is_loading_assets(),'source_registry_not_ready'
    opts=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_game_package_references=True,include_editor_only_package_references=True)
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
        assert len(data)==1,'non_single_asset_package_requires_review:'+p
        a=data[0];cls=str(a.asset_class_path.asset_name)
        assert cls in {'StaticMesh','Material','MaterialInstanceConstant','Texture2D','TextureCube','Texture2DArray','TextureRenderTarget2D','MaterialFunction','MaterialFunctionInstance','MaterialParameterCollection','RuntimeVirtualTexture','SubsurfaceProfile','CurveLinearColorAtlas','CurveLinearColor'},'unreviewed_dependency_class:'+cls+':'+p
        assert str(a.asset_name)==p.rsplit('/',1)[-1],'noncanonical_primary_object_name'
        f=(project/'Content'/(p[6:]+'.uasset')) if p.startswith('/Game/') else Path(unreal.Paths.engine_content_dir()).resolve()/(p[8:]+'.uasset')
        assert f.is_file(),'missing_source_file:'+str(f)
        files=[{'file':str(f.with_suffix(e)),'sha256':I.sha(f.with_suffix(e)),'bytes':f.with_suffix(e).stat().st_size} for e in ['.uasset','.uexp','.ubulk','.uptnl'] if f.with_suffix(e).is_file()]
        dependencies=sorted(str(x) for x in (registry.get_dependencies(p,opts) or []))
        packages.append({'package':p,'class':cls,'object_path':p+'.'+str(a.asset_name),'files':files,'dependencies':dependencies})
        todo.extend(dependencies)
    assert not list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()) and not list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    receipt={'schema':'environmentpipeline.native_source_closure.v2','source_id':source_id,'pid':os.getpid(),
        'source_project':str(project),'job_ids':job_ids,'packages':sorted(packages,key=lambda x:x['package']),
        'script_dependencies':sorted(scripts),'engine_version':unreal.SystemLibrary.get_engine_version(),
        'authority':m['authority'],'command_manifest_sha256':I.sha(mp),'queue_sha256':m['queue_sha256'],
        'native_measured':True,'source_dirty_unchanged':True,'target_project_imported':False}
    p=I.HERE/'Migration'/source_id/('SOURCE_CLOSURE_'+V.digest(receipt)+'.json');A.immutable_json(p,receipt)
    I.write('Migration/'+source_id+'/LATEST_CLOSURE.json',{'path':str(p),'sha256':I.sha(p)})
    return {'path':str(p),'sha256':I.sha(p)}


def export(plan_path,activation_path):
    import unreal
    from . import migration_remap as R
    act,m,mp=_preflight('migrate_native_source_to_target',activation_path)
    plan=R.validate_plan(plan_path)
    assert act['plan_sha256']==I.sha(plan_path)
    assert act['allow_exact_intermediate_namespace'] is True
    assert sorted(act['intermediate_packages'])==sorted(p['original_package'] for p in plan['mapping'])
    assert Path(unreal.Paths.project_dir()).resolve()==Path(plan['source_project']).resolve()
    assert act['target_editor_closed'] is True # Sole-editor process check above independently verifies it.
    out=Path(plan_path).parent/'MIGRATED.json'
    if out.exists():
        result=I.read(out)
        for f in result['target_files']:assert I.sha(f['file'])==f['sha256']
        return result
    R.assert_unoccupied(plan)
    assert not (Path(plan_path).parent/'MIGRATION_STARTED.json').exists(),'partial_migration_requires_reconciliation'
    A.immutable_json(Path(plan_path).parent/'MIGRATION_STARTED.json',{'pid':os.getpid(),'plan_sha256':I.sha(plan_path)})
    options=unreal.MigrationOptions(prompt=False,ignore_dependencies=False,asset_conflict=unreal.AssetMigrationConflict.SKIP)
    unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(plan['root_packages'],str(I.ROOT/'Content'),options)
    files=[]
    for item in plan['mapping']:
        base=I.ROOT/'Content'/(item['original_package'][6:]+'.uasset')
        assert base.is_file(),'native_migration_missing_output'
        for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
            p=base.with_suffix(ext)
            if p.exists():files.append({'file':str(p),'sha256':I.sha(p),'bytes':p.stat().st_size})
    R.verify_source_files(plan)
    assert not list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()) and not list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    result={'plan_sha256':I.sha(plan_path),'pid':os.getpid(),'native_migrate_completed':True,'source_originals_unchanged':True,
        'target_files':files,'namespace_remap_completed':False,'selected_or_registered':False}
    A.immutable_json(out,result)
    return result
