"""Compare loaded dirty material functions with retained copies of their disk packages."""
import unreal,pathlib,json,shutil,hashlib,difflib
ROOT=pathlib.Path(__file__).parent
PROJECT=ROOT.parents[1]
PREFIX='/Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/'
SNAP='/Game/Project/Shared/Recovery/ProceduralCity_20261005/DiskFunctions/'
def export(asset,path):
    task=unreal.AssetExportTask();task.object=asset;task.filename=str(path);task.automated=True;task.prompt=False;task.exporter=unreal.ObjectExporterT3D()
    assert unreal.Exporter.run_asset_export_task(task),(asset.get_path_name(),list(task.errors))
def run():
    dirty=[p for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() if p.get_path_name().startswith(PREFIX)]
    assert len(dirty)==15 and not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    records=[];folder=ROOT/'Before';(folder/'DiskPackages').mkdir(parents=True,exist_ok=True)
    for package in dirty:
        path=package.get_path_name();name=path.rsplit('/',1)[-1];original=unreal.load_asset(path)
        source=PROJECT/'Content'/(path[6:]+'.uasset');backup=folder/'DiskPackages'/(name+'.uasset')
        assert source.exists() and not backup.exists();shutil.copy2(source,backup)
        snapshot_path=SNAP+name;snapshot_file=PROJECT/'Content'/(snapshot_path[6:]+'.uasset')
        assert not snapshot_file.exists();snapshot_file.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,snapshot_file)
        export(original,folder/(name+'_loaded.t3d'))
        snapshot=unreal.load_asset(snapshot_path);assert snapshot is not None
        export(snapshot,folder/(name+'_disk.t3d'))
        loaded=(folder/(name+'_loaded.t3d')).read_text();disk=(folder/(name+'_disk.t3d')).read_text().replace(SNAP,PREFIX)
        diff=list(difflib.unified_diff(disk.splitlines(),loaded.splitlines(),fromfile='disk',tofile='loaded'))
        (folder/(name+'.diff.txt')).write_text('\n'.join(diff))
        assert unreal.EditorAssetLibrary.save_loaded_asset(snapshot,only_if_is_dirty=False)
        records.append({'package':path,'disk_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'loaded_equals_disk':loaded==disk,'diff_line_count':len(diff),'diff_path':str(folder/(name+'.diff.txt')),'snapshot':snapshot_path})
    (ROOT/'DIRTY_MATERIAL_COMPARISON.json').write_text(json.dumps(records,indent=2))
    return [{'package':p['package'],'identical':p['loaded_equals_disk'],'diff_lines':p['diff_line_count']} for p in records]
