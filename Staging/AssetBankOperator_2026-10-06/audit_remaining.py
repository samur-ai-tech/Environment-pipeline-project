"""Read-only native registry audit; never loads, edits or saves an asset."""
import unreal,os,json,collections,time
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve();HERE=ROOT/'Staging/AssetBankOperator_2026-10-06'
assert os.getpid()==29900
line=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if x.strip()][-1]
assert 'OWNER=ASSET_BANK_OPERATOR ' in line and 'authority=AVIV_DIRECT_USER' in line
def dirty():return sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()+unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
before=dirty();reg=unreal.AssetRegistryHelpers.get_asset_registry()
q=json.loads((HERE/'EXPANDED_SUPPLY_QUEUE.json').read_text())['rows'];done=set()
for p in (HERE/'Receipts').glob('*.json'):done.update(a['asset_id'] for a in json.loads(p.read_text()).get('assets',[]))
groups=collections.defaultdict(list)
for r in q:
    if r['asset_id'] not in done:groups[r['source_pack']].append(r)
opts=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_game_package_references=True,include_editor_only_package_references=False)
results=[]
for pack,rows in groups.items():
    source_path=rows[0]['source_file']
    if source_path.startswith('\\\\?\\'):source_path=source_path[4:]
    sourcefile=Path(source_path);parts=list(sourcefile.parts);content=Path(*parts[:parts.index('Content')+1])
    roots={r['source_object_path'].split('/')[2] for r in rows}
    if pack=='CitySample':roots.update(['Material','Megascans','Textures','MSPresets'])
    mounts=[];collisions=[]
    try:
        for name in sorted(roots):
            source=content/name;target=ROOT/'Content'/name
            if not source.is_dir():continue
            if target.exists():
                if source.resolve()==target.resolve():continue
                # Registry-only source inspection: temporarily resolve the external
                # namespace, never load an object, and restore/rescan in finally.
            mount='/Game/'+name+'/'
            old=Path(unreal.Paths.convert_relative_path_to_full(unreal.PackageTools.package_name_to_filename(mount+'marker'))).parent
            if old.exists():unreal.SystemLibrary.execute_console_command(None,'PackageName.UnregisterMountPoint '+mount+' "'+old.as_posix()+'/"')
            unreal.SystemLibrary.execute_console_command(None,'PackageName.RegisterMountPoint '+mount+' "'+source.as_posix()+'/"')
            mounts.append((mount,source,old if old.exists() else None))
            actual=Path(unreal.Paths.convert_relative_path_to_full(unreal.PackageTools.package_name_to_filename(mount+'marker'))).parent.resolve()
            assert actual==source.resolve(), 'Mount did not resolve requested source directory'
            reg.scan_paths_synchronous([mount],True)
        if pack=='greasewood':
            source=Path(unreal.Paths.engine_plugins_dir()).resolve()/'Experimental/ProceduralVegetationEditor/Content'
            mount='/ProceduralVegetationEditor/'
            assert source.is_dir()
            old_filename=unreal.PackageTools.package_name_to_filename(mount+'marker')
            old=Path(unreal.Paths.convert_relative_path_to_full(old_filename)).parent if old_filename else None
            prior=old if old and old.exists() else None
            unreal.SystemLibrary.execute_console_command(None,'PackageName.RegisterMountPoint '+mount+' "'+source.as_posix()+'/"')
            mounts.append((mount,source,prior));reg.scan_paths_synchronous([mount],True)
        cache={}
        def dep(p):
            if p not in cache:
                data=reg.get_assets_by_package_name(p)
                cache[p]=([str(a.asset_class_path.asset_name) for a in data],[str(x) for x in (reg.get_dependencies(p,opts) or [])])
            return cache[p]
        for r in rows:
            pkg=r['source_object_path'].split('.')[0];name=pkg.split('/')[2]
            result={'asset_id':r['asset_id'],'source_pack':pack,'source_package':pkg,'source_file':r['source_file'],'category_proposed':r['category'],'proposed_role':r['proposed_role'],'state':'registry_audit','missing_dependencies':[],'native_imported':False}
            if name in collisions:
                result['state']='source_namespace_collision_requires_isolated_inspection';results.append(result);continue
            todo=[pkg];seen=set();packages=[]
            while todo:
                p=todo.pop()
                if p in seen or p.startswith('/Script/'):continue
                seen.add(p);classes,deps=dep(p)
                if not classes:result['missing_dependencies'].append(p)
                packages.append({'package':p,'classes':classes,'dependencies':deps});todo.extend(deps)
            result['classes']=dep(pkg)[0];result['closure_package_count']=len(packages)
            result['state']='registry_static_mesh_dependencies_complete' if 'StaticMesh' in result['classes'] and not result['missing_dependencies'] else 'registry_repair_or_class_review_required'
            result['source_closure']=packages;results.append(result)
        assert dirty()==before,'Unexpected dirty state during registry-only audit'
        (HERE/'Native/REMAINING_REGISTRY_AUDIT.json').write_text(json.dumps({'complete':False,'read_only':True,'results':results,'dirty_unchanged':True},indent=2))
        print(json.dumps({'source_pack':pack,'audited':len(rows),'colliding_roots':collisions}),flush=True)
    finally:
        for mount,source,old in reversed(mounts):
            unreal.SystemLibrary.execute_console_command(None,'PackageName.UnregisterMountPoint '+mount+' "'+source.as_posix()+'/"')
            if old:
                unreal.SystemLibrary.execute_console_command(None,'PackageName.RegisterMountPoint '+mount+' "'+old.as_posix()+'/"');reg.scan_paths_synchronous([mount],True)
assert dirty()==before
summary=dict(collections.Counter(r['state'] for r in results))
(HERE/'Native/REMAINING_REGISTRY_AUDIT.json').write_text(json.dumps({'complete':True,'read_only':True,'results':results,'summary':summary,'dirty_unchanged':True,'new_asset_loads':0,'native_saves':0},indent=2))
print(json.dumps({'audited':len(results),'summary':summary,'dirty_unchanged':True}))
