"""Project menu around the official GeoCity input/configure/cook lifecycle."""
from pathlib import Path
import json
import datetime
import os
import subprocess
import unreal
import geocity_bank_workflow


def generate_current_area():
    try:
        project=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        world_path=world.get_outermost().get_path_name()
        profiles=list((project/'Staging/ModelBank').rglob('AREA_PROFILE.json'))
        matching=[p for p in profiles if json.loads(p.read_text(encoding='utf-8'))['map']==world_path]
        if len(matching)!=1:
            raise RuntimeError('The current area requires exactly one persistent AREA_PROFILE.json')
        lease_path=project/'Staging/ModelBank/EDITOR_OWNER.txt'
        lease=lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
        if 'OWNER=NONE' not in lease:
            raise RuntimeError('The editor is assigned to an active task. Wait until that task releases it.')
        dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()+unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
        if dirty:
            raise RuntimeError('Resolve unsaved changes before generating the current area.')
        process_read=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
        pids=[int(p) for p in process_read.stdout.split()]
        if pids!=[os.getpid()]:
            raise RuntimeError('GeoCity requires this to be the only open Unreal editor.')
        if lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]!=lease:
            raise RuntimeError('Editor ownership changed. Try again after the task finishes.')
        with lease_path.open('a',encoding='utf-8') as stream:
            stream.write('\n'+datetime.datetime.now(datetime.timezone.utc).isoformat()+f' OWNER=GEOCITY_MENU task=GENERATE_CURRENT_AREA assigned_editor_PID={os.getpid()} scope={world_path}_cook_only_no_Bake_no_map_save\n')
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        action='regenerate' if any(a.get_class().get_name()=='HoudiniAssetActor' for a in actors) else 'instantiate'
        return geocity_bank_workflow.run(str(matching[0]),action,release_menu_lease=True)
    except Exception as exc:
        unreal.log_error('GeoCity Generate/Regenerate: '+str(exc))
        unreal.EditorDialog.show_message('GeoCity',str(exc),unreal.AppMsgType.OK)


def register_menu():
    menus=unreal.ToolMenus.get()
    menu=menus.extend_menu('LevelEditor.MainMenu.Tools')
    entry=unreal.ToolMenuEntry(name='GeoCity.GenerateCurrentArea',type=unreal.MultiBlockType.MENU_ENTRY)
    entry.set_label('GeoCity: Generate / Regenerate Current Area')
    entry.set_tool_tip('Configure the current area profile and native catalog, then cook through Houdini Engine. Bake remains a separate action.')
    entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON,'','import geocity_editor_action; geocity_editor_action.generate_current_area()')
    menu.add_menu_entry('GeoCity',entry)
    menus.refresh_all_widgets()
