"""Project menu around official GeoCity generation, replacement and named saves."""
from pathlib import Path
import json
import datetime
import os
import subprocess
import re
import unreal
import geocity_bank_workflow


def persistent_profiles(project):
    # Canonical profiles are immediate children; archived copies are evidence.
    return sorted((project/'Staging/ModelBank').glob('*/AREA_PROFILE.json'))


def lease_fields(line):
    return dict(re.findall(r'(?:^|\s)([A-Za-z_]+)=([^\s]+)', line))


def managed_operation_lease(project, line, world_path):
    """Accept only task4's manager-issued actual-PID activation, not startup."""
    fields = lease_fields(line)
    if fields.get('OWNER') != 'CODEX_MANAGED_SYSTEMS_TASK4':
        return False
    assignment = json.loads((project/'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json').read_text(encoding='utf-8'))
    task = next(row for row in assignment['tasks'] if row['id'] == 'task4')
    return (bool(task['thread_id'])
            and fields.get('manager_thread_id') == assignment['manager_thread_id']
            and fields.get('operator_thread_id') == task['thread_id']
            and fields.get('assigned_editor_PID') == str(os.getpid())
            and fields.get('activation') == 'MANAGER_ACTIVATED'
            and fields.get('map') == world_path
            and world_path in assignment['native_area_maps'])


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
    acknowledged.update(_acknowledged_native_stages(project,dirty_paths,registry,options))
    return acknowledged


def _native_package(value):
    return str(value).split('.',1)[0]


def _acknowledged_native_stages(project,dirty_paths,registry,options):
    """Acknowledge exact unused clipping stages; never save/delete/load maps.

    Only a completed saved native delivery can supply the candidate ledger.
    Live StaticMeshComponent bindings are checked across every loaded world
    and template through ObjectIterator; saved hard/soft referencers are checked
    globally. This is the bounded ClippedGeometry route, not general asset
    cleanup or an acknowledgment of arbitrary dirty content.
    """
    profiles=[]
    retained_dependencies=set()
    scoped=[]
    dirty=set(dirty_paths)
    for path in persistent_profiles(project):
        profile=json.loads(path.read_text(encoding='utf-8'))
        profiles.append((path,profile))
        retained_dependencies.add(profile['map'])
        receipt=Path(profile['workflow_receipt'])
        for ledger_path in (receipt,receipt.with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json')):
            if not ledger_path.exists():continue
            saved=json.loads(ledger_path.read_text(encoding='utf-8'))
            if saved.get('phase')=='baked_saved_verified':
                if Path(saved['profile']).resolve()!=path.resolve():
                    raise RuntimeError('A retained dependency ledger belongs to another profile.')
                retained_dependencies.update(map(_native_package,saved.get('named_generated_dependency_paths',[])))
        delivery=profile.get('road_provider_contract')
        if not isinstance(delivery,dict):continue
        if delivery.get('provider')!='RoadBLD' or delivery.get('saved') is not True or delivery.get('phase')!='native_generated_saved_verified':continue
        retained_dependencies.update(map(_native_package,delivery.get('named_generated_dependency_paths',[])))
        retained_dependencies.update(_native_package(row['mesh']) for row in delivery.get('native_component_bindings',[]))
        ledger=delivery.get('unreferenced_native_staged_packages',[])
        if not isinstance(ledger,list) or any(not isinstance(value,str) for value in ledger):
            raise RuntimeError('Native unused-stage ledger must contain exact package paths.')
        candidates=set(ledger).intersection(dirty)
        if not candidates:continue
        area=delivery.get('area_id')
        if area not in ('GazaRimal','GazaShujaiya') or profile.get('road_provider')!='RoadBLD':
            raise RuntimeError('Unused native stages lack the scoped active provider.')
        area_root='/Game/Project/Areas/'+area+'/'
        if (delivery.get('schema')!='environmentpipeline.roadbld_delivery.v1'
                or delivery.get('named_map')!=profile['map']
                or not profile['map'].startswith(area_root)
                or not profile['root'].startswith(area_root)
                or delivery.get('hda_vehicle_surfaces_suppressed') is not True):
            raise RuntimeError('Unused native stages do not belong to a completed named area delivery.')
        source=json.loads(Path(profile['source']).read_text(encoding='utf-8'))
        if source.get('area_id')!=area:
            raise RuntimeError('Unused native-stage area differs from its geographic source.')
        pattern=re.compile(re.escape(area_root+'RoadBLD/ClippedGeometry/')+
            r'[A-Za-z0-9_]{1,80}/SM_Clipped_[0-9a-f]{16}')
        if len(ledger)!=len(set(ledger)) or any(not pattern.fullmatch(value) for value in ledger):
            raise RuntimeError('Native stage ledger contains an unscoped or non-package path.')
        scoped.append((area,candidates))
    candidates={value for area,values in scoped for value in values}
    if not candidates:return set()
    if registry.is_loading_assets():
        raise RuntimeError('Native stage acknowledgment requires completed saved-asset discovery.')
    if candidates.intersection(retained_dependencies):
        raise RuntimeError('An unused native stage remains in a retained dependency/binding ledger.')
    # Referencers are global, so any saved map/content reference rejects the
    # candidate. Do not exempt other stage packages or another named area.
    for candidate in candidates:
        if registry.get_referencers(candidate,options):
            raise RuntimeError('A native stage has a saved hard/soft package referencer: '+candidate)
    # Walk every retained map dependency graph, including links through shared
    # content. Restricting traversal to an area root could miss cross-map refs.
    pending=[profile['map'] for path,profile in profiles]
    expanded=set()
    while pending:
        package=pending.pop()
        if package in expanded:continue
        expanded.add(package)
        dependencies={str(value) for value in registry.get_dependencies(package,options) or []}
        if dependencies.intersection(candidates):
            raise RuntimeError('A retained map dependency graph references an unused native stage.')
        pending.extend(value for value in dependencies if value.startswith('/Game/') and value not in expanded)
    iterator=getattr(unreal,'ObjectIterator',None)
    if iterator is None:
        raise RuntimeError('Native stage acknowledgment requires loaded-object binding inspection.')
    meshes={}
    for mesh in iterator(unreal.StaticMesh):
        package=mesh.get_outermost().get_path_name()
        if package in candidates:
            if package in meshes:
                raise RuntimeError('An unused native stage package has ambiguous mesh identity.')
            meshes[package]=mesh
    if set(meshes)!=candidates:
        raise RuntimeError('An unused native stage is not an exact loaded StaticMesh package.')
    for component in iterator(unreal.StaticMeshComponent):
        mesh=component.get_editor_property('static_mesh')
        if mesh is not None and mesh.get_outermost().get_path_name() in candidates:
            raise RuntimeError('A native stage remains bound to a loaded component: '+component.get_path_name())
    for area,values in scoped:
        for candidate in values:
            mesh=meshes[candidate]
            if mesh.get_path_name()!=candidate+'.'+candidate.rsplit('/',1)[-1]:
                raise RuntimeError('An unused native stage has an unexpected asset identity.')
            if (str(unreal.EditorAssetLibrary.get_metadata_tag(mesh,'GeoCityOwner'))!='GeoCity_RoadBLD'
                    or str(unreal.EditorAssetLibrary.get_metadata_tag(mesh,'GeoCityArea'))!=area):
                raise RuntimeError('An unused native stage lacks its exact owner/area metadata.')
    return candidates


def generate_current_area():
    menu_lease = None
    try:
        import geocity_runtime_guard
        geocity_runtime_guard.verify()
        project=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        world_path=world.get_outermost().get_path_name()
        profiles=persistent_profiles(project)
        matching=[p for p in profiles if json.loads(p.read_text(encoding='utf-8'))['map']==world_path]
        if len(matching)!=1:
            raise RuntimeError('The current area requires exactly one persistent AREA_PROFILE.json')
        lease_path=project/'Staging/ModelBank/EDITOR_OWNER.txt'
        lease=lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
        managed = managed_operation_lease(project,lease,world_path)
        if lease_fields(lease).get('OWNER') != 'NONE' and not managed:
            raise RuntimeError('The editor is assigned to an active task. Wait until that task releases it.')
        if any(getattr(r,key,None) is not None for r in geocity_bank_workflow.ACTIVE
               for key in ('watch_tick','save_tick')):
            raise RuntimeError('An ordinary GeoCity operation is already active.')
        dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()+unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
        profile=json.loads(matching[0].read_text(encoding='utf-8'))
        if profile.get('roadbld_workflow',{}).get('enabled'):
            import geocity_roadbld_workflow
            geocity_roadbld_workflow.require_geographic_landscape_authority()
        dirty_paths=[p.get_path_name() for p in dirty]
        if dirty_paths:
            acknowledged=acknowledged_cook_leftovers(project,dirty_paths)
            if not set(dirty_paths).issubset(acknowledged):
                raise RuntimeError('Resolve unsaved changes before generating the current area.')
        process_read=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
        process_read.check_returncode()
        pids=[int(p) for p in process_read.stdout.split()]
        if pids!=[os.getpid()]:
            raise RuntimeError('GeoCity requires this to be the only open Unreal editor.')
        if lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]!=lease:
            raise RuntimeError('Editor ownership changed. Try again after the task finishes.')
        if not managed:
            with lease_path.open('a',encoding='utf-8') as stream:
                menu_lease = datetime.datetime.now(datetime.timezone.utc).isoformat()+f' OWNER=GEOCITY_MENU task=GENERATE_CURRENT_AREA assigned_editor_PID={os.getpid()} scope={world_path}_configured_generation_scoped_replace_Bake_named_dependencies_map_save'
                stream.write('\n'+menu_lease+'\n')
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        action='regenerate' if any(a.get_class().get_name()=='HoudiniAssetActor' for a in actors) else 'instantiate'
        return geocity_bank_workflow.run(str(matching[0]),action,reviewed_dirty_packages=dirty_paths,release_menu_lease=not managed)
    except Exception as exc:
        # Constructor/preflight errors can occur before GeoCityRun owns a
        # callback. Release only this exact menu acquisition, never another run.
        if menu_lease is not None and lease_path.read_text(encoding='utf-8-sig').splitlines()[-1] == menu_lease:
            import sys
            active = list(getattr(sys.modules.get('geocity_bank_workflow'),'ACTIVE',[])) + list(getattr(sys.modules.get('geocity_roadbld_workflow'),'ACTIVE',[]))
            dirty_now=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()+unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
            if (not dirty_now and not any(getattr(r,key,None) is not None for r in active for key in ('watch_tick','save_tick','tick_handle','_pending_correction'))
                    and not any(getattr(r,'state',{}).get('recovery_required') for r in active)):
                with lease_path.open('a',encoding='utf-8') as stream:
                    stream.write('\n'+datetime.datetime.now(datetime.timezone.utc).isoformat()+f' OWNER=NONE task=GEOCITY_MENU editor_PID={os.getpid()} released_phase=failed_preflight\n')
        error = str(exc) or repr(exc)
        unreal.log_error('GeoCity Generate/Regenerate: '+error)
        unreal.EditorDialog.show_message('GeoCity',error,unreal.AppMsgType.OK)


def register_menu():
    menus=unreal.ToolMenus.get()
    menu=menus.extend_menu('LevelEditor.MainMenu.Tools')
    entry=unreal.ToolMenuEntry(name='GeoCity.GenerateCurrentArea',type=unreal.MultiBlockType.MENU_ENTRY)
    entry.set_label('GeoCity: Generate / Regenerate Current Area')
    entry.set_tool_tip('Generate the current area through Houdini Engine, replace its previous baked output and save its named dependencies and map.')
    entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON,'','import geocity_editor_action; geocity_editor_action.generate_current_area()')
    menu.add_menu_entry('GeoCity',entry)
    menus.refresh_all_widgets()
