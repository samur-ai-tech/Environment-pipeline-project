"""Open the real saved area and read its retained native references without a cook."""
import unreal, json, os, subprocess, runpy, datetime
from pathlib import Path
import geocity_bank_workflow
from geocity_editor_action import acknowledged_cook_leftovers

PROJECT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=PROJECT/'Staging/RepairExecution_2026-10-03'

def reopen_area(profile_path):
    lease=(PROJECT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
    assert 'OWNER=CODEX_REPAIR_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
    processes=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
    assert [int(p) for p in processes.stdout.split()]==[os.getpid()]
    assert all(not w.watch_tick and not w.save_tick for w in geocity_bank_workflow.ACTIVE)
    api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
    assert api.is_asset_cooking_paused()
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    dirty=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    assert set(dirty).issubset(acknowledged_cook_leftovers(PROJECT,dirty))
    profile=json.loads(Path(profile_path).read_text())
    saved=json.loads(Path(profile['workflow_receipt']).read_text())
    assert saved['phase']=='baked_saved_verified' and saved['generator_revision']=='r017_retained_native_environment'
    assert unreal.EditorLoadingAndSavingUtils.load_map(profile['map'])
    assert api.is_asset_cooking_paused()
    runpy.run_path(str(HERE/'inspect_retained_area.py'))
    area=json.loads(Path(profile['source']).read_text())['area_id']
    actual=json.loads((HERE/('ACTUAL_'+area+'.json')).read_text())
    assert actual['native_count']==saved['instance_count']
    assert actual['landscape_count']==1 and not actual['dirty_maps']
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    names={a.get_path_name() for a in actors}
    assert set(saved['baked_actor_paths']).issubset(names)
    hdas=[a for a in actors if a.get_class().get_name()=='HoudiniAssetActor']
    assert len(hdas)==1 and not hdas[0].get_components_by_class(unreal.MeshComponent)
    wrapper=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hdas[0])
    assert not wrapper.is_auto_cooking_enabled()
    actual['persistence']={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'method':'Saved map unloaded and opened again in the same owned editor; Engine paused, no recook or new bake',
        'all_saved_baked_actors_present':True,'cooked_mesh_components':0,'hda_actor_count':1,'auto_cooking_enabled':False,
        'fresh_editor_process_restart_performed':False}
    (HERE/('REOPEN_'+area+'.json')).write_text(json.dumps(actual,indent=2),encoding='utf-8')
    print(json.dumps({'reopened':area,'native_count':actual['native_count'],'baked_actors':len(saved['baked_actor_paths']),'dirty_maps':actual['dirty_maps'],'no_recook':True}))
