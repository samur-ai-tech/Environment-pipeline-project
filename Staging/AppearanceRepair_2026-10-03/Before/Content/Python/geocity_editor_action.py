"""Project menu around official GeoCity generation, replacement and named saves."""
from pathlib import Path
import json
import datetime
import os
import subprocess
import unreal
import geocity_bank_workflow


def persistent_profiles(project):
    return list((project/'Staging/ModelBank').rglob('AREA_PROFILE.json'))


def acknowledged_cook_leftovers(project, dirty_paths):
    """Only exact unreferenced leftovers from successful named area deliveries."""
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True)
    acknowledged=set()
    for path in persistent_profiles(project):
        profile=json.loads(path.read_text(encoding='utf-8'))
        receipt=Path(profile['workflow_receipt'])
        prior=json.loads(receipt.read_text(encoding='utf-8')) if receipt.exists() else {}
        if prior.get('phase')!='baked_saved_verified':
            # Failed attempts must not erase the last complete saved-area
            # ledger used to recognize exact, still-unreferenced leftovers.
            successful=receipt.with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json')
            if not successful.exists():continue
            prior=json.loads(successful.read_text(encoding='utf-8'))
            if prior.get('phase')!='baked_saved_verified':continue
        if Path(prior['profile']).resolve()!=path.resolve():
            raise RuntimeError('A saved-area ledger belongs to another profile.')
        candidates=set(prior.get('unreferenced_cook_packages',[])).intersection(dirty_paths)
        if not candidates:continue
        if any(not p.startswith(profile['cook_folder']+'/') for p in candidates):
            raise RuntimeError('An acknowledged leftover is outside its recorded cook root.')
        pending=[profile['map']];dependencies=set()
        while pending:
            for dependency in registry.get_dependencies(pending.pop(),options) or []:
                dependency=str(dependency)
                if dependency not in dependencies:
                    dependencies.add(dependency)
                    if dependency.startswith(profile['root']+'/'):pending.append(dependency)
        if dependencies.intersection(candidates):
            raise RuntimeError('A saved area still references an unsaved cook package.')
        for candidate in candidates:
            referencers=[str(p) for p in registry.get_referencers(candidate,options) or []]
            if any(not p.startswith(profile['cook_folder']+'/') for p in referencers):
                raise RuntimeError('An obsolete cook package has a retained external reference: '+candidate)
        acknowledged.update(candidates)
    return acknowledged


def generate_current_area():
    try:
        project=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        world_path=world.get_outermost().get_path_name()
        profiles=persistent_profiles(project)
        matching=[p for p in profiles if json.loads(p.read_text(encoding='utf-8'))['map']==world_path]
        if len(matching)!=1:
            raise RuntimeError('The current area requires exactly one persistent AREA_PROFILE.json')
        lease_path=project/'Staging/ModelBank/EDITOR_OWNER.txt'
        lease=lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
        if 'OWNER=NONE' not in lease:
            raise RuntimeError('The editor is assigned to an active task. Wait until that task releases it.')
        dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()+unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
        profile=json.loads(matching[0].read_text(encoding='utf-8'))
        dirty_paths=[p.get_path_name() for p in dirty]
        if dirty_paths:
            acknowledged=acknowledged_cook_leftovers(project,dirty_paths)
            if not set(dirty_paths).issubset(acknowledged):
                raise RuntimeError('Resolve unsaved changes before generating the current area.')
        process_read=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
        pids=[int(p) for p in process_read.stdout.split()]
        if pids!=[os.getpid()]:
            raise RuntimeError('GeoCity requires this to be the only open Unreal editor.')
        if lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]!=lease:
            raise RuntimeError('Editor ownership changed. Try again after the task finishes.')
        with lease_path.open('a',encoding='utf-8') as stream:
            stream.write('\n'+datetime.datetime.now(datetime.timezone.utc).isoformat()+f' OWNER=GEOCITY_MENU task=GENERATE_CURRENT_AREA assigned_editor_PID={os.getpid()} scope={world_path}_configured_generation_scoped_replace_Bake_named_dependencies_map_save\n')
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        action='regenerate' if any(a.get_class().get_name()=='HoudiniAssetActor' for a in actors) else 'instantiate'
        return geocity_bank_workflow.run(str(matching[0]),action,reviewed_dirty_packages=dirty_paths,release_menu_lease=True)
    except Exception as exc:
        unreal.log_error('GeoCity Generate/Regenerate: '+str(exc))
        unreal.EditorDialog.show_message('GeoCity',str(exc),unreal.AppMsgType.OK)


def register_menu():
    menus=unreal.ToolMenus.get()
    menu=menus.extend_menu('LevelEditor.MainMenu.Tools')
    entry=unreal.ToolMenuEntry(name='GeoCity.GenerateCurrentArea',type=unreal.MultiBlockType.MENU_ENTRY)
    entry.set_label('GeoCity: Generate / Regenerate Current Area')
    entry.set_tool_tip('Generate the current area through Houdini Engine, replace its previous baked output and save its named dependencies and map.')
    entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON,'','import geocity_editor_action; geocity_editor_action.generate_current_area()')
    menu.add_menu_entry('GeoCity',entry)
    menus.refresh_all_widgets()
