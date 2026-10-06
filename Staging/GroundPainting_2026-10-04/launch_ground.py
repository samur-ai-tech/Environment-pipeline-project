"""Narrow original-area paused launch. Does not activate old workers or generation."""
import datetime, hashlib, json, os, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
THREAD='01a10883-481f-7723-bdaa-fed004f15ef1'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def processes():
    command="Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'UnrealEditor|Houdini|HARS' } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    raw=subprocess.check_output(['powershell','-NoProfile','-Command',command],text=True).strip()
    return json.loads(raw) if raw else []
def launch(area):
    assignment=read(HERE/'ASSIGNMENT.json')
    assert assignment['execution_thread_id']==THREAD
    assert assignment['coordinating_thread_id']=='01a10864-8261-76a1-a118-0cb0c1894739'
    assert area in ('GazaShujaiya','GazaRimal')
    assert assignment['authority']['ordinary_generation_authorized'] is False
    target=assignment['original_maps'][area]
    assert not processes(), 'Existing native process requires preservation, not takeover'
    manifest_path=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
    manifest=read(manifest_path)
    pins=read(HERE/'STARTUP_REVIEWED_PINS.json')
    assert sha(manifest_path)==pins['manifest_sha256']
    assert sha(HERE/'ASSIGNMENT.json')==pins['assignment_sha256']
    for filename,expected in pins['task_scripts'].items():assert sha(HERE/filename)==expected,filename
    for relative,expected in pins['sealed_files'].items():
        assert (ROOT/relative).resolve(strict=True)==(ROOT/relative)
        assert sha(ROOT/relative)==expected,relative
    assert manifest['schema']=='environmentpipeline.geocity_runtime_sources.v2'
    assert len(manifest['modules'])==12
    mapfile=ROOT/('Content/'+target[6:]+'.umap')
    baselines=read(HERE/'LAUNCH_BASELINES.json')
    assert sha(mapfile)==baselines[area]['map_sha256']
    profiles=[p for p in (ROOT/'Staging/ModelBank').glob('*/AREA_PROFILE.json') if read(p).get('map')==target]
    assert len(profiles)==1
    assert str(profiles[0].resolve())==baselines[area]['profile']
    assert sha(profiles[0])==baselines[area]['profile_sha256']
    restore=ROOT/'Saved/Autosaves/PackageRestoreData.json'
    if restore.exists():
        recovery=json.loads(restore.read_text(encoding='utf-16-le').lstrip('\ufeff'))
        assert recovery.get('Packages')==[] and recovery.get('RestoreEnabled') is False, 'Pending package recovery'
    lease_path=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
    last=[x for x in lease_path.read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
    fields=dict(t.split('=',1) for t in last.split() if '=' in t)
    assert fields.get('OWNER')=='NONE',last
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    env=os.environ.copy(); env['UE_PYTHONPATH']=str(ROOT/'Content/Python')
    args=[r'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe',str(ROOT/'Environmentpipeline.uproject'),target,
          '-NoAutoSave','-NoRestoreOpenAssetTabs',
          '-ini:Engine:[/Script/HoudiniEngineRuntime.HoudiniRuntimeSettings]:bPauseCookingOnStart=True',
          '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:bAutoSaveEnable=False,[/Script/UnrealEd.EditorLoadingSavingSettings]:RestoreOpenAssetTabsOnRestart=NeverRestore']
    assert not processes()
    assert [x for x in lease_path.read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]==last
    # The user explicitly needs to see the interactive editor and Lit pixels.
    si=subprocess.STARTUPINFO(); si.dwFlags|=subprocess.STARTF_USESHOWWINDOW; si.wShowWindow=1
    p=subprocess.Popen(args,cwd=ROOT,env=env,startupinfo=si)
    lease=f'{stamp} OWNER=CODEX_GROUND_PAINTING operator_thread_id={THREAD} task=ground assigned_editor_PID={p.pid} map={target} activation=STARTUP_INSPECTION_ONLY ordinary_generation_authorized=false'
    with lease_path.open('a',encoding='utf-8') as f:f.write('\n'+lease+'\n')
    result={'pid':p.pid,'area':area,'map':target,'map_sha256':sha(mapfile),'manifest_sha256':sha(manifest_path),'source_checks_passed':True,'args':args,'lease':lease}
    (HERE/f'LAUNCH_PID{p.pid}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__':launch(sys.argv[1])
