"""Scoped GeoCity v015 lifecycle through the official Houdini Engine Public API.

Use run(profile_path, action='regenerate'|'instantiate') for named area delivery;
explicit 'recook'/'rebuild' actions retain cook-only engineering use. The profile
contains the area source, native bank table, saved HDA, mode and scoped paths.
No server, alternate geometry loader, plugin patch or editor manager is used.
"""
import datetime
import hashlib
import json
import os
import subprocess
import time
from collections import Counter
from pathlib import Path
import unreal

ACTIVE = []

def _path(obj):
    return obj.get_path_name() if obj else None

class GeoCityRun:
    def __init__(self, profile_path,reviewed_dirty_packages=(),release_menu_lease=False):
        self.profile_path=Path(profile_path)
        self.p=json.loads(self.profile_path.read_text(encoding='utf-8'))
        self.project=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
        self.lease_line=(self.project/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
        self.receipt=Path(self.p['catalog_receipt'])
        self.state_path=Path(self.p['workflow_receipt'])
        self.wrapper=None
        self.api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
        self.started_epoch=time.time()
        self.watch_tick=None
        self.was_paused=None
        self.save_tick=None
        self.previous_baked_paths=[]
        self.last_successful_path=self.state_path.with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json')
        if self.state_path.is_file():
            prior=json.loads(self.state_path.read_text(encoding='utf-8'))
            if prior.get('phase')=='baked_saved_verified':
                self.last_successful_path.write_text(json.dumps(prior,indent=2),encoding='utf-8')
        if self.last_successful_path.is_file():
            prior=json.loads(self.last_successful_path.read_text(encoding='utf-8'))
            assert prior.get('profile')==str(self.profile_path),'Previous saved-area ledger belongs to another profile'
            self.previous_baked_paths=list(prior['baked_actor_paths'])
        self.reviewed_dirty_packages=set(reviewed_dirty_packages)
        self.release_menu_lease=release_menu_lease
        self.state={'schema':'environmentpipeline.geocity_official_lifecycle.v1','pid':os.getpid(),
                    'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'profile':str(self.profile_path),'mode':self.p['mode'],'phase':'preflight'}

    def guard(self):
        lease=(self.project/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
        assert 'OWNER=NONE' not in lease and f'assigned_editor_PID={os.getpid()}' in lease,lease
        assert lease==self.lease_line,'Editor ownership changed during this operation'
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        assert world.get_outermost().get_path_name()==self.p['map'],'Wrong area map'
        assert self.p['map'].startswith('/Game/Project/Areas/')

    def finish_operation(self):
        if self.wrapper:
            self.wrapper.set_auto_cooking_enabled(False)
            self.wrapper.on_post_instantiation_delegate.remove_callable(self.after_instantiation)
            self.wrapper.on_post_cook_delegate.remove_callable(self.after_cook)
            self.wrapper.on_post_processing_delegate.remove_callable(self.after_processing)
            self.wrapper.on_post_bake_delegate.remove_callable(self.after_bake)
        if self.save_tick is not None:
            unreal.unregister_slate_post_tick_callback(self.save_tick)
            self.save_tick=None
        if self.was_paused and not self.api.is_asset_cooking_paused():
            self.api.pause_asset_cooking()
        if self.watch_tick is not None:
            unreal.unregister_slate_post_tick_callback(self.watch_tick)
            self.watch_tick=None
        if self.release_menu_lease:
            lease_path=self.project/'Staging/ModelBank/EDITOR_OWNER.txt'
            latest=lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
            if 'OWNER=GEOCITY_MENU' in latest and f'assigned_editor_PID={os.getpid()}' in latest:
                with lease_path.open('a',encoding='utf-8') as stream:
                    stream.write('\n'+datetime.datetime.now(datetime.timezone.utc).isoformat()+f' OWNER=NONE task=GEOCITY_MENU editor_PID={os.getpid()} released_phase={self.state["phase"]}\n')
            self.release_menu_lease=False

    def fail(self,phase,exc):
        self.state.update(phase=phase,error=repr(exc),api_error=self.wrapper.get_last_error_message() if self.wrapper else None)
        self.write()
        self.finish_operation()
        unreal.log_error('GeoCity '+phase+': '+repr(exc))

    def watch(self,delta_time):
        try:
            self.guard()
            assert time.time()-self.started_epoch<600,'GeoCity operation timed out; see workflow receipt'
        except Exception as exc:
            self.fail('failed_operation',exc)

    def guard_processes(self):
        process_read=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
        assert [int(p) for p in process_read.stdout.split()]==[os.getpid()],'Exactly one Unreal editor is required'

    def after_cook(self,w,success):
        if self.state['phase']=='cooking' and not success:
            self.fail('failed_engine_cook',RuntimeError('Official Houdini Engine cook failed'))

    def validate_outputs(self,w,receipt):
        area=json.loads(Path(self.p['source']).read_text(encoding='utf-8'))['area_id']
        expected_meshes={area+'_'+role for role in ('road_surfaces','sidewalks','buildings','vegetation','street_details')}
        # A successfully evaluated proxy filter can legitimately have no mesh.
        for role,suffix in (('tree','vegetation'),('street_pole','street_details')):
            proxy=receipt.get('proxy_outputs',{}).get(role)
            assert proxy is not None,'Missing completed proxy output ledger: '+role
            assert proxy['source_count']==proxy['removed_count']+proxy.get('omitted_generated_count',0)+proxy['remaining_count']
            if proxy['remaining_primitives']==0:
                expected_meshes.discard(area+'_'+suffix)
        actual_meshes=set()
        landscape_count=instancer_count=0
        for index in range(w.get_num_outputs()):
            kind=w.get_output_type_at(index)
            identifiers=w.get_output_identifiers_at(index)
            assert identifiers,'Output has no native identities'
            if kind==unreal.HoudiniOutputType.MESH:
                actual_meshes.update(i.part_name for i in identifiers)
                assert all(w.get_output_component_at(index,i) for i in identifiers),'Missing mesh output component'
            elif kind==unreal.HoudiniOutputType.LANDSCAPE:
                landscape_count+=1
            elif kind==unreal.HoudiniOutputType.INSTANCER:
                instancer_count+=1
                assert all(i.part_name=='bank_instances' and w.get_output_component_at(index,i) for i in identifiers),'Missing native bank output'
        assert actual_meshes==expected_meshes,'Procedural output identities differ: '+str(actual_meshes)
        assert landscape_count==1 and instancer_count==1,'Landscape or native bank output is incomplete'
        assert w.get_num_outputs()==len(expected_meshes)+2,'Unexpected or incomplete native outputs'
        required={'output_landscape','output_roads','output_sidewalks','output_buildings','output_vegetation','output_street_details','output_controls','output_bank_instances'}
        assert set(receipt['output_wiring'])==required and all(receipt['output_wiring'].values()),'HDA output wiring is incomplete'
        self.state['output_identities_verified']=True
        self.state['controls_output']='point-only Houdini controls; no separate Unreal mesh expected'

    def write(self):
        payload=json.dumps(self.state,indent=2,default=str)
        self.state_path.write_text(payload,encoding='utf-8')
        if self.p.get('build_state_alias'):
            Path(self.p['build_state_alias']).write_text(payload,encoding='utf-8')

    def configure_and_bind(self,w):
        self.guard()
        self.guard_processes()
        w.set_auto_cooking_enabled(False)
        assert not w.is_auto_cooking_enabled()
        table=unreal.load_asset(self.p['table'])
        assert isinstance(table,unreal.DataTable)
        assert len(unreal.DataTableFunctionLibrary.get_data_table_row_names(table))==self.p['row_count']
        # A retained object list can hide stale HAPI input fields after rebuild.
        # Empty then refill using the supported API to recreate input objects.
        geo=unreal.new_object(unreal.HoudiniPublicAPIGeoInput)
        geo.set_input_objects([])
        assert w.set_input_parameter('bank_catalog',geo)
        # Distinct input object prevents the cleared object from retaining cached rows.
        bound=unreal.new_object(unreal.HoudiniPublicAPIGeoInput)
        bound.set_input_objects([table])
        assert w.set_input_parameter('bank_catalog',bound)
        self.state['bound_table_objects']=[_path(x) for x in w.get_input_parameter('bank_catalog').get_input_objects()]
        mode=self.p['mode']
        assert mode in ('disabled','technical_preview','released')
        release=self.p.get('release',{})
        if mode=='released':
            assert release.get('decision_receipt') and release.get('id') and release.get('style_set') and release.get('catalog_sha256')
            decision=Path(release['decision_receipt'])
            assert decision.is_file() and hashlib.sha256(decision.read_bytes()).hexdigest()==release['decision_sha256']
        else:
            assert not release,'Non-release modes cannot carry a release decision'
        strings={'package_file':self.p['source'],'catalog_file':'','bank_receipt_file':str(self.receipt).replace('\\','/'),
                 'mesh_preview_material':self.p['procedural_material'],
                 'bank_instance_materials':json.dumps(self.p.get('instance_materials',{}),sort_keys=True,separators=(',',':')),
                 'environment_style_set':self.p['environment_style_set'],'landscape_layerinfo_bake_root':self.p['root'],
                 'catalog_release_id':release.get('id',''),'bank_style_set':release.get('style_set',''),
                 'catalog_expected_sha256':release.get('catalog_sha256',self.p['catalog_sha256'])}
        if 'building_assembly_contract' in self.p:
            strings['building_assembly_contract_json']=json.dumps(self.p['building_assembly_contract'],sort_keys=True,separators=(',',':'))
        bools={'bank_inspection_only':False,'bank_pilot_enabled':False,'module_test_enabled':False,
               'modular_pilot_enabled':False,'nonbuilding_enabled':True,
               'technical_preview_enabled':mode=='technical_preview','bank_release_enabled':mode=='released'}
        for name,value in strings.items():
            assert w.set_string_parameter_value(name,value),name
            assert w.get_string_parameter_value(name)==value,name
        for name,value in bools.items():
            assert w.set_bool_parameter_value(name,value),name
            assert w.get_bool_parameter_value(name)==value,name
        for name,value in self.p['surface_choices'].items():
            assert w.set_int_parameter_value(name,value),name
        for key,setter in (('cook_folder',w.set_temporary_cook_folder),('bake_folder',w.set_bake_folder)):
            directory=unreal.DirectoryPath();directory.path=self.p[key]
            assert setter(directory)
        assert w.set_replace_previous_bake(True)
        assert w.set_remove_output_after_bake(True)
        assert w.set_auto_bake_enabled(False)
        self.state['parameters']={**strings,**bools,**self.p['surface_choices']}
        if self.receipt.exists():
            archive=self.receipt.with_name(self.receipt.stem+'_'+str(time.time_ns())+'.json')
            self.receipt.rename(archive)
            self.state['previous_catalog_receipt']=str(archive)
        error_path=Path(str(self.receipt)+'.errors.json')
        if error_path.exists():
            error_path.rename(error_path.with_name(error_path.name+'.'+str(time.time_ns())))
        self.state['cook_started_epoch']=time.time()
        self.state['phase']='cooking';self.write()
        assert w.recook()

    def after_instantiation(self,w):
        try:
            self.configure_and_bind(w)
        except Exception as exc:
            self.fail('failed_binding',exc)

    def after_processing(self,w):
        if self.state['phase']!='cooking':return
        try:
            self.guard()
            assert self.receipt.stat().st_mtime>=self.state['cook_started_epoch'],'Stale catalog receipt'
            receipt=json.loads(self.receipt.read_text())
            assert len(receipt['rows'])==self.p['row_count']
            assert receipt['catalog_sha256']==self.p['catalog_sha256']
            assert receipt['technical_preview_enabled']==(self.p['mode']=='technical_preview')
            assert receipt['release_enabled']==(self.p['mode']=='released')
            assert receipt['schema_version']==3 and receipt['native_table_schema_version']==3,'Stale translated table schema'
            assert receipt['native_v3_catalog_sha256']==self.p['catalog_sha256']
            assert receipt.get('request_scope')=='complete_augmented_selector_input','Incomplete request report'
            assert receipt['request_count']==sum(receipt['request_roles'].values())==len(receipt['requests'])
            outputs=[]
            for index in range(w.get_num_outputs()):
                identifiers=w.get_output_identifiers_at(index)
                outputs.append({'index':index,'type':str(w.get_output_type_at(index)),
                    'objects':[{'part_name':i.part_name,'split_identifier':i.split_identifier,
                                'object':_path(w.get_output_object_at(index,i)),
                                'component':_path(w.get_output_component_at(index,i))} for i in identifiers]})
            self.state['outputs']=outputs
            self.state['request_roles']=receipt['request_roles']
            self.state['placement_diagnostics']=receipt['placement_diagnostics']
            self.state['generator_revision']=receipt.get('generator_revision')
            self.state['proxy_outputs']=receipt.get('proxy_outputs',{})
            self.state['building_assembly']=receipt.get('building_assembly',{})
            self.state['terrain_support']=receipt.get('terrain_support',{})
            if self.p.get('building_assembly_contract',{}).get('enabled'):
                assembly=receipt.get('building_assembly',{})
                support=receipt.get('terrain_support',{})
                assert assembly and support,'Retained assembly or final terrain report is missing'
                assert support['conflicting_support_cells']==0,'Contradictory building ground support'
                total=assembly['whole_native_building_count']+assembly['assembled_building_count']+assembly['unsupported_count']
                assert total==support['source_pad_count'],'Geographic buildings disappeared from the complete coverage ledger'
                assert assembly['native_module_point_count']>0,'Enabled assembly emitted no native facade modules'
                self.state['geographic_building_coverage']={'total':total,'whole_native':assembly['whole_native_building_count'],
                    'native_assembly':assembly['assembled_building_count'],'explicitly_unsupported':assembly['unsupported_count']}
            self.write()
            instances=receipt.get('nonbuilding_instances',[])
            if self.p['mode']!='disabled':
                assert instances,'No catalog assets were emitted'
                self.validate_outputs(w,receipt)
            actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
            meshes=[]
            expected_meshes=Counter(x['path'] for x in instances)
            for actor in [w.get_houdini_asset_actor()]:
                for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
                    if _path(comp.static_mesh) in expected_meshes:
                        meshes.append({'mesh':_path(comp.static_mesh),'instances':comp.get_instance_count() if isinstance(comp,unreal.InstancedStaticMeshComponent) else 1,
                                       'component':_path(comp),'materials':[_path(comp.get_material(i)) for i in range(comp.get_num_materials())]})
            actual=sum(x['instances'] for x in meshes)
            self.state['native_components']=meshes
            self.state['expected_mesh_counts']=dict(expected_meshes)
            self.state['actual_instance_count']=actual
            self.write()
            assert actual==len(instances),'Translated native instance count differs from HDA receipt'
            actual_meshes=Counter()
            for rec in meshes:actual_meshes[rec['mesh']]+=rec['instances']
            assert actual_meshes==expected_meshes,'Per-model native counts differ from HDA receipt'
            for rec in meshes:
                expected_materials=self.p.get('instance_materials',{}).get(rec['mesh'])
                if expected_materials:
                    assert rec['materials']==expected_materials,'Native material-slot override differs: '+rec['mesh']
            baked_paths={_path(a) for a in w.get_baked_output_actors()}
            landscapes=[a for a in actors if isinstance(a,unreal.Landscape) and _path(a) not in baked_paths]
            assert len(landscapes)==1 and _path(landscapes[0].landscape_material)==self.p['landscape_material']
            self.state.update(phase='cooked_verified',row_count=len(receipt['rows']),
                              catalog_sha256=receipt['catalog_sha256'],output_count=w.get_num_outputs(),
                              instance_count=actual,roles=dict(Counter(x['role'] for x in instances)),native_components=meshes)
            self.state.pop('error',None);self.write()
            if self.action in ('regenerate','instantiate'):
                self.bake_and_save()
            else:
                self.finish_operation()
        except Exception as exc:
            self.state['output_count']=w.get_num_outputs()
            error_path=Path(str(self.receipt)+'.errors.json')
            if error_path.exists():self.state['stage_errors']=json.loads(error_path.read_text())
            self.fail('failed_cook_verification',exc)

    def bake_and_save(self):
        self.guard()
        assert self.state['phase']=='cooked_verified'
        assert self.receipt.stat().st_mtime>=self.state['cook_started_epoch']
        # Keep the complete prior saved actor set when optional outputs disappear.
        self.previous_baked_paths=sorted(set(self.previous_baked_paths).union(_path(a) for a in self.wrapper.get_baked_output_actors()))
        self.state['previous_baked_actor_paths']=self.previous_baked_paths
        self.state['phase']='baking';self.write()
        self.wrapper.on_post_bake_delegate.add_callable(self.after_bake)
        assert self.wrapper.bake_all_outputs()

    def after_bake(self,w,success):
        self.guard()
        self.state.update(phase='baked_waiting_for_output_removal' if success else 'failed_bake',bake_success=bool(success))
        self.write()
        if success:
            self.bake_completed_epoch=time.time()
            self.save_tick=unreal.register_slate_post_tick_callback(self.finish_save)
        else:
            self.finish_operation()

    def finish_save(self,delta_time):
        try:
            self.guard()
            components=self.wrapper.get_houdini_asset_actor().get_components_by_class(unreal.MeshComponent)
            if components:
                assert time.time()-self.bake_completed_epoch<120,'Cooked output was not removed'
                return
            # Saving pumps Slate. Detach first to avoid a recursive save callback.
            if self.save_tick is not None:
                unreal.unregister_slate_post_tick_callback(self.save_tick)
                self.save_tick=None
            baked=self.wrapper.get_baked_output_actors()
            receipt=json.loads(self.receipt.read_text())
            expected=Counter(x['path'] for x in receipt.get('nonbuilding_instances',[]))
            actual=Counter()
            for actor in baked:
                for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                    mesh=_path(component.static_mesh)
                    if mesh in expected:
                        actual[mesh]+=component.get_instance_count() if isinstance(component,unreal.InstancedStaticMeshComponent) else 1
                        slots=self.p.get('instance_materials',{}).get(mesh)
                        if slots:
                            assert [_path(component.get_material(i)) for i in range(component.get_num_materials())]==slots,'Baked native material slots differ: '+mesh
            assert actual==expected,'Baked bank counts differ from cooked bank counts'
            actor_system=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            worlds=actor_system.get_all_level_actors()
            baked_paths={_path(a) for a in baked}
            obsolete=[a for a in worlds if _path(a) in self.previous_baked_paths and _path(a) not in baked_paths]
            self.state['removed_obsolete_baked_actor_paths']=[_path(a) for a in obsolete]
            for actor in obsolete:
                assert actor_system.destroy_actor(actor),'Failed scoped obsolete baked actor removal'
            for actor in baked:
                actor.set_is_temporarily_hidden_in_editor(False)
            worlds=actor_system.get_all_level_actors()
            assert sum(isinstance(a,unreal.Landscape) for a in worlds)==1,'Duplicate Landscapes after bake'
            all_native=Counter()
            for actor in worlds:
                for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
                    mesh=_path(comp.static_mesh)
                    if mesh in expected:
                        all_native[mesh]+=comp.get_instance_count() if isinstance(comp,unreal.InstancedStaticMeshComponent) else 1
            assert all_native==expected,'Overlapping native bank copies remain in the area'
            self.save_generated_dependencies(baked)
            world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
            assert unreal.EditorLoadingAndSavingUtils.save_map(world,self.p['map'])
            self.save_generated_dependencies(baked,include_saved_map=True)
            self.state.pop('error',None)
            self.state.update(phase='baked_saved_verified',baked_actor_paths=[_path(a) for a in baked],
                              baked_actor_count=len(baked),baked_mesh_counts=dict(actual),
                              cooked_mesh_component_count=0,landscape_count=1,
                              baked_native_material_slots_verified=True,
                              dirty_maps=[_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
                              unsaved_content_packages=[_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()])
            saved_dependencies=set(self.state['named_generated_dependency_paths'])
            self.state['unreferenced_cook_packages']=[p for p in self.state['unsaved_content_packages']
                if p.startswith(self.p['cook_folder']+'/') and p not in saved_dependencies]
            self.write()
            self.last_successful_path.write_text(json.dumps(self.state,indent=2,default=str),encoding='utf-8')
            self.finish_operation()
        except Exception as exc:
            self.state.update(phase='failed_bake_save_verification',error=repr(exc));self.write()
            self.finish_operation()

    def save_generated_dependencies(self,baked,include_saved_map=False):
        """Save the explicit dependency closure of retained actors, never dirty-all."""
        self.guard()
        packages={}
        seen=set()
        def visit(obj):
            if not isinstance(obj,unreal.Object) or _path(obj) in seen:return
            seen.add(_path(obj))
            package=obj.get_outermost()
            path=_path(package)
            if path.startswith(self.p['root']+'/') and path!=self.p['map']:
                packages[path]=package
            # Live references include unsaved Landscape textures/layer info.
            for prop in ('static_mesh','landscape_material','heightmap_texture','weightmap_textures',
                         'override_materials','editor_layer_settings','layer_info_obj','layer_info',
                         'layer_info_object','parent','texture_parameter_values','parameter_value'):
                try:value=obj.get_editor_property(prop)
                except Exception:continue
                values=list(value) if isinstance(value,(list,tuple,unreal.Array)) else [value]
                for item in values:
                    if isinstance(item,unreal.Object):visit(item)
                    else:
                        for field in ('layer_info_obj','layer_info_object','parameter_value'):
                            try:visit(item.get_editor_property(field))
                            except Exception:pass
        for actor in baked:
            visit(actor)
            for comp in actor.get_components_by_class(unreal.ActorComponent):visit(comp)
        # Saved generated assets can hold further generated dependencies.
        registry=unreal.AssetRegistryHelpers.get_asset_registry()
        options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True)
        pending=list(packages)+([self.p['map']] if include_saved_map else [])
        expanded=set()
        while pending:
            path=pending.pop()
            if path in expanded:continue
            expanded.add(path)
            for dependency in registry.get_dependencies(path,options) or []:
                dep=str(dependency)
                if not dep.startswith(self.p['root']+'/') or dep==self.p['map'] or dep in packages:continue
                asset=unreal.load_asset(dep)
                assert asset,'Missing generated dependency: '+dep
                packages[dep]=asset.get_outermost();pending.append(dep)
        self.state['named_generated_dependency_paths']=sorted(packages)
        self.write()
        if packages:
            assert unreal.EditorLoadingAndSavingUtils.save_packages([packages[p] for p in sorted(packages)],True),'Named generated dependency save failed'
        dirty={_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
        assert not dirty.intersection(packages),'Referenced generated packages remain dirty'

    def start(self,action):
        self.guard()
        self.guard_processes()
        assert action in ('instantiate','recook','rebuild','regenerate')
        assert not any(x is not self and x.watch_tick is not None for x in ACTIVE),'Another GeoCity operation is active'
        dirty=[_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]+[_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
        assert set(dirty)==self.reviewed_dirty_packages,'Resolve or explicitly review current unsaved packages before generation: '+str(dirty)
        foreign={p for p in self.reviewed_dirty_packages if p!=self.p['map'] and not p.startswith(self.p['cook_folder']+'/')}
        if foreign:
            from geocity_editor_action import acknowledged_cook_leftovers
            assert foreign.issubset(acknowledged_cook_leftovers(self.project,foreign)),'Foreign dirty packages are not exact acknowledged unreferenced area cook leftovers'
        self.state['reviewed_dirty_packages']=sorted(self.reviewed_dirty_packages)
        assert self.api.is_session_valid(),'Open the official Houdini Engine session'
        self.was_paused=self.api.is_asset_cooking_paused()
        self.action=action
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        hd=[a for a in actors if a.get_class().get_name()=='HoudiniAssetActor']
        if action=='instantiate':
            assert not hd,'Area already contains an HDA'
            api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
            assert api.is_session_valid(),'Open the official Houdini Engine session'
            self.wrapper=api.instantiate_asset(unreal.load_asset(self.p['hda']),unreal.Transform(),enable_auto_cook=False)
        else:
            assert len(hd)==1,'Area must contain exactly one HDA'
            self.wrapper=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0])
        self.wrapper.set_auto_cooking_enabled(False)
        assert self.wrapper.set_auto_bake_enabled(False)
        self.wrapper.on_post_cook_delegate.add_callable(self.after_cook)
        self.wrapper.on_post_processing_delegate.add_callable(self.after_processing)
        self.watch_tick=unreal.register_slate_post_tick_callback(self.watch)
        if self.api.is_asset_cooking_paused():self.api.resume_asset_cooking()
        if action in ('instantiate','rebuild','regenerate'):
            self.wrapper.on_post_instantiation_delegate.add_callable(self.after_instantiation)
            self.state['phase']='waiting_for_instantiation';self.write()
            if action in ('rebuild','regenerate'):assert self.wrapper.rebuild()
        else:self.configure_and_bind(self.wrapper)
        return self

def run(profile_path,action='regenerate',reviewed_dirty_packages=(),release_menu_lease=False):
    run=GeoCityRun(profile_path,reviewed_dirty_packages,release_menu_lease)
    ACTIVE.append(run)
    try:
        return run.start(action)
    except Exception as exc:
        run.fail('failed_start',exc)
        raise

