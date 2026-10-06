from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve();out=root/'Staging/AssetBankOperator_2026-10-06'
p=out/'native_operator.py';ns={'__file__':str(p)};exec(p.read_text(),ns);ns['preflight']()
mounts=[]
for name in ['Prop','Material','Megascans','Textures']:
    source=out/'NativeIntake/CitySample'/name
    if not source.exists():continue
    mount='/Game/'+name+'/'
    unreal.SystemLibrary.execute_console_command(None,'PackageName.RegisterMountPoint '+mount+' "'+source.as_posix()+'/"')
    unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous([mount],True)
    mounts.append(mount)
ns['import_mounted']('BANK_USE_CITY_001',mounts)
ns['validate_batch']('BANK_USE_CITY_001')
