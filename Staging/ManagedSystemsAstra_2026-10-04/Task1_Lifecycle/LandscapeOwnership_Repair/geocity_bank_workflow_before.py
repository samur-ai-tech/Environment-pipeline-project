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
import geocity_landscape_workflow

ACTIVE = []
RUNTIME_PROFILE_FIELDS = ('landscape_material','road_provider','road_provider_contract','roadbld_workflow.status')


def _runtime_profile_merge(before,current,proposed):
    """Reject concurrent/configuration edits and merge only runtime delivery."""
    if current!=before:
        raise RuntimeError('Current profile differs from the operation baseline; refusing overwrite')
    stripped=json.loads(json.dumps(proposed))
    merged=json.loads(json.dumps(current))
    changes=[]
    for field in RUNTIME_PROFILE_FIELDS:
        parts=field.split('.')
        a=before;b=proposed;s=stripped;m=merged
        for part in parts[:-1]:
            if part not in a and part not in b:break
            if not isinstance(a.get(part),dict) or not isinstance(b.get(part),dict):
                raise RuntimeError('Runtime cannot create/remove profile configuration: '+part)
            a=a[part];b=b[part];s=s[part];m=m[part]
        else:
            key=parts[-1]
            if key in b:
                if key not in a or a[key]!=b[key]:
                    changes.append({'field':field,'before_present':key in a,'before':a.get(key),'after':b[key]})
                    m[key]=b[key]
            elif key in a:
                raise RuntimeError('Runtime cannot remove profile delivery field: '+field)
            if key in a:s[key]=a[key]
            else:s.pop(key,None)
    if stripped!=before:
        raise RuntimeError('Runtime attempted to alter manager/bank-owned profile configuration')
    if any(row['field']=='landscape_material' for row in changes):
        expected=before['root']+'/Materials/MI_GeoCityGround.MI_GeoCityGround'
        if not before.get('landscape_grass',{}).get('enabled') or proposed['landscape_material']!=expected:
            raise RuntimeError('Runtime landscape material is outside the permitted permanent area child')
    return merged,changes

def _path(obj):
    return obj.get_path_name() if obj else None

def _hda_json(value):
    """Houdini string evaluation consumes backslash escapes in Windows paths."""
    def portable(item):
        if isinstance(item,dict):return {key:portable(v) for key,v in item.items()}
        if isinstance(item,list):return [portable(v) for v in item]
        if isinstance(item,str) and len(item)>2 and item[1]==':' and item[2]=='\\':
            return item.replace('\\','/')
        return item
    return json.dumps(portable(value),sort_keys=True,separators=(',',':'))

class GeoCityRun:
    def __init__(self, profile_path,reviewed_dirty_packages=(),release_menu_lease=False):
        self.profile_path=Path(profile_path).resolve(strict=True)
        self.profile_sha256=hashlib.sha256(self.profile_path.read_bytes()).hexdigest()
        self.p=json.loads(self.profile_path.read_text(encoding='utf-8'))
        self.profile_baseline=json.loads(json.dumps(self.p))
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
        self._finishing=False
        self.autosave_settings=None
        self.autosave_before=None
        self.previous_baked_paths=[]
        self.native_road_run=None
        self.native_road_contract=None
        self.native_road_phase='export' if self.p.get('roadbld_workflow',{}).get('enabled') else None
        self.last_successful_path=self.state_path.with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json')
        if self.state_path.is_file():
            prior=json.loads(self.state_path.read_text(encoding='utf-8'))
            assert Path(prior.get('profile','')).resolve()==self.profile_path,'Current workflow ledger belongs to another profile'
            history=self.state_path.parent/'WorkflowHistory'
            history.mkdir(exist_ok=True)
            (history/('WORKFLOW_STATE_'+str(time.time_ns())+'.json')).write_bytes(self.state_path.read_bytes())
            if prior.get('phase')=='baked_saved_verified':
                self.last_successful_path.write_text(json.dumps(prior,indent=2),encoding='utf-8')
        if self.last_successful_path.is_file():
            prior=json.loads(self.last_successful_path.read_text(encoding='utf-8'))
            assert Path(prior.get('profile','')).resolve()==self.profile_path,'Previous saved-area ledger belongs to another profile'
            self.previous_baked_paths=list(prior['baked_actor_paths'])
            prefix=self.p['map']+'.'+self.p['map'].rsplit('/',1)[-1]+':PersistentLevel.'
            assert all(path.startswith(prefix) for path in self.previous_baked_paths),'Previous output ledger contains actors outside the named map'
        self.reviewed_dirty_packages=set(reviewed_dirty_packages)
        self.release_menu_lease=release_menu_lease
        self.operation_timeout_seconds=self.p.get('operation_timeout_seconds',1800 if self.native_road_phase else 600)
        if (isinstance(self.operation_timeout_seconds,bool)
                or not isinstance(self.operation_timeout_seconds,int)
                or not 600<=self.operation_timeout_seconds<=3600):
            raise RuntimeError('Profile operation_timeout_seconds must be an integer within600..3600')
        self.state={'schema':'environmentpipeline.geocity_official_lifecycle.v1','pid':os.getpid(),
                    'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'profile':str(self.profile_path),'mode':self.p['mode'],'phase':'preflight',
                    'operation_timeout_seconds':self.operation_timeout_seconds,
                    'operation_started_epoch':self.started_epoch,
                    'previous_baked_actor_paths':list(self.previous_baked_paths),
                    'lease_at_start':self.lease_line,'profile_sha256_at_start':self.profile_sha256,
                    'native_execution_verified':False,'reopened':False,'user_accepted':False}

    def guard(self):
        assert not self.state['phase'].startswith('failed'),'Operation has failed; preserve its recovery state'
        from geocity_editor_action import lease_fields, managed_operation_lease
        lease=(self.project/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
        fields=lease_fields(lease)
        assert fields.get('OWNER') not in (None,'NONE','CODEX_MANAGED_SYSTEMS_STARTUP') and fields.get('assigned_editor_PID')==str(os.getpid()),lease
        if fields.get('OWNER')=='CODEX_MANAGED_SYSTEMS_TASK4':
            assert managed_operation_lease(self.project,lease,self.p['map']),'Missing actual-PID manager activation'
        assert lease==self.lease_line,'Editor ownership changed during this operation'
        assert hashlib.sha256(self.profile_path.read_bytes()).hexdigest()==self.profile_sha256,'Area profile changed during operation'
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        assert world.get_outermost().get_path_name()==self.p['map'],'Wrong area map'
        assert self.p['map'].startswith('/Game/Project/Areas/')

    def suspend_transaction_autosave(self):
        """Use only named saves during generation; restore the user's setting."""
        if getattr(self,'autosave_before',None) is not None:return
        settings=unreal.load_object(None,'/Script/UnrealEd.Default__EditorLoadingSavingSettings')
        assert settings,'Native editor autosave settings are unavailable'
        self.autosave_settings=settings
        self.autosave_before=bool(settings.get_editor_property('bAutoSaveEnable'))
        settings.set_editor_property('bAutoSaveEnable',False,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        self.state['transaction_autosave']={'previously_enabled':self.autosave_before,'temporarily_disabled':True,'config_saved':False}

    def finish_operation(self):
        if self._finishing:return
        self._finishing=True
        errors=[]
        def attempt(label,fn):
            try:fn()
            except Exception as exc:errors.append({'step':label,'error':repr(exc)})
        failed=self.state['phase'].startswith('failed')
        native=self.native_road_run
        if native and failed:
            import geocity_roadbld_grounding as grounding
            attempt('rollback_pending_road_correction',lambda:grounding.rollback_correction(native,RuntimeError(self.state.get('error',self.state['phase']))))
            attempt('stop_native_road_callbacks',native.finish)
            # A completed native save must remain recorded if a later parent
            # save fails; it is not a rollback or an unsaved transaction.
            native.state['parent_failure']=self.state['phase']
            attempt('record_native_parent_failure',native.write)
        if self.wrapper:
            attempt('disable_auto_cook',lambda:self.wrapper.set_auto_cooking_enabled(False))
            attempt('disable_auto_bake',lambda:self.wrapper.set_auto_bake_enabled(False))
            for name,callback in (('on_post_instantiation_delegate',self.after_instantiation),('on_post_cook_delegate',self.after_cook),
                                  ('on_post_processing_delegate',self.after_processing),('on_post_bake_delegate',self.after_bake)):
                attempt(name,lambda name=name,callback=callback:getattr(self.wrapper,name).remove_callable(callback))
            def verify_auto_disabled():
                assert not self.wrapper.is_auto_cooking_enabled() and not self.wrapper.is_auto_bake_enabled(),'Automatic HDA execution remains enabled'
            attempt('automatic_execution_readback',verify_auto_disabled)
        for key in ('save_tick','watch_tick'):
            if getattr(self,key) is not None:
                def detach(key=key):
                    unreal.unregister_slate_post_tick_callback(getattr(self,key));setattr(self,key,None)
                attempt('detach_'+key,detach)
        if failed or self.was_paused:
            attempt('pause_cooking',self.api.pause_asset_cooking)
            def verify_paused():
                assert self.api.is_asset_cooking_paused(),'Official cooking did not pause'
            attempt('pause_readback',verify_paused)
        elif self.was_paused is False:
            attempt('restore_cooking',self.api.resume_asset_cooking)
        dirty_maps=[];dirty_content=[]
        try:
            dirty_maps=[_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
            dirty_content=[_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
        except Exception as exc:errors.append({'step':'dirty_state_readback','error':repr(exc)})
        recovery=bool(errors or (failed and (self.wrapper is not None or dirty_maps or dirty_content)) or (native and getattr(native,'_pending_correction',None)))
        if getattr(self,'autosave_before',None) is not None:
            # Never let autosave persist a failed dirty generation after exit.
            restore=not failed and not recovery
            attempt('restore_autosave',lambda:self.autosave_settings.set_editor_property('bAutoSaveEnable',self.autosave_before if restore else False,
                                                       notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER))
            self.state['transaction_autosave'].update(restored=restore,held_disabled_for_recovery=not restore)
            self.autosave_before=None
        self.state.update(cleanup_errors=errors,dirty_maps_at_finish=dirty_maps,dirty_content_at_finish=dirty_content,
                          recovery_required=bool(recovery or errors),operation_elapsed_seconds=time.time()-self.started_epoch,
                          lease_released=False,failed_cook_cancellation_verified=False if failed else None)
        if self.release_menu_lease:
            lease_path=self.project/'Staging/ModelBank/EDITOR_OWNER.txt'
            latest=lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
            if latest==self.lease_line and not self.state['recovery_required']:
                with lease_path.open('a',encoding='utf-8') as stream:
                    stream.write('\n'+datetime.datetime.now(datetime.timezone.utc).isoformat()+f' OWNER=NONE task=GEOCITY_MENU editor_PID={os.getpid()} released_phase={self.state["phase"]}\n')
                self.state['lease_released']=True
            self.release_menu_lease=False
        try:self.write()
        finally:self._finishing=False

    def fail(self,phase,exc):
        try:api_error=self.wrapper.get_last_error_message() if self.wrapper else None
        except Exception as api_exc:api_error=repr(api_exc)
        self.state.update(phase=phase,error=repr(exc),api_error=api_error)
        try:self.write()
        except Exception as write_exc:self.state['failure_receipt_write_error']=repr(write_exc)
        finally:self.finish_operation()
        unreal.log_error('GeoCity '+phase+': '+repr(exc))

    def watch(self,delta_time):
        if self._finishing:return
        try:
            self.guard()
            assert time.time()-self.started_epoch<self.operation_timeout_seconds,'GeoCity operation timed out; see workflow receipt'
        except Exception as exc:
            self.fail('failed_operation',exc)

    def guard_processes(self):
        process_read=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
        process_read.check_returncode()
        assert [int(p) for p in process_read.stdout.split()]==[os.getpid()],'Exactly one Unreal editor is required'

    def after_cook(self,w,success):
        if self.state['phase']=='cooking' and not success:
            self.fail('failed_engine_cook',RuntimeError('Official Houdini Engine cook failed'))

    def validate_outputs(self,w,receipt):
        area=json.loads(Path(self.p['source']).read_text(encoding='utf-8'))['area_id']
        expected_meshes={area+'_'+role for role in ('road_surfaces','sidewalks','buildings','vegetation','street_details')}
        surface=receipt.get('surface_geometry',{})
        for name,suffix in (('catalog_road_material','road_surfaces'),('catalog_sidewalk_material','sidewalks')):
            report=surface.get('outputs',{}).get(name)
            if report is not None:
                assert surface.get('source_coverage_preserved') and report.get('source_coverage_preserved'),'Geographic surface coverage is incomplete'
                assert report['visible_face_count']>=0,'Invalid surface output count'
                if report['visible_face_count']==0:
                    expected_meshes.discard(area+'_'+suffix)
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
        if self.state.get('engine_output_configuration'):
            self.state['engine_output_configuration'][-1]['actual_outputs_verified_after_processing']=True
        self.state['controls_output']='point-only Houdini controls; no separate Unreal mesh expected'

    def official_landscapes(self,w):
        """Resolve exact public-wrapper output objects, never actor-name guesses.

        The installed plugin returns HoudiniLandscapeTargetLayerOutput objects;
        their reflected Landscape property is the parent actor (HoudiniOutput.h).
        An unavailable binding is a native integration failure, not permission
        to choose or remove another Landscape by class or naming convention.
        """
        result={}
        for index in range(w.get_num_outputs()):
            if w.get_output_type_at(index)!=unreal.HoudiniOutputType.LANDSCAPE:continue
            for identifier in w.get_output_identifiers_at(index):
                obj=w.get_output_object_at(index,identifier)
                assert obj and obj.get_class().get_name() in ('HoudiniLandscapeTargetLayerOutput','HoudiniLandscapeOutput'),'Unsupported official Landscape output object'
                landscape=obj.get_editor_property('landscape')
                assert isinstance(landscape,unreal.Landscape),'Official output has no native Landscape binding'
                assert landscape.get_outermost().get_path_name()==self.p['map'],'Official Landscape output belongs to another map'
                result[_path(landscape)]=landscape
        return result

    def account_previous_landscapes(self):
        """Record only source-bound official output and the successful ledger."""
        assert Path(self.wrapper.get_string_parameter_value('package_file')).resolve()==Path(self.p['source']).resolve(),'Existing HDA source differs from the current-map profile'
        bound=self.official_landscapes(self.wrapper)
        live={_path(a) for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a,unreal.Landscape)}
        known=set(self.previous_baked_paths)|set(bound)
        self.state['previous_landscape_accounting']={
            'live_actor_paths':sorted(live),'official_output_actor_paths':sorted(bound),
            'successful_ledger_actor_paths':sorted(live.intersection(self.previous_baked_paths)),
            'unaccounted_actor_paths':sorted(live-known),'hda_actor_path':_path(self.wrapper.get_houdini_asset_actor()),
            'source':self.p['source'],'source_sha256':hashlib.sha256(Path(self.p['source']).read_bytes()).hexdigest(),
            'saved_map_sha256':hashlib.sha256((self.project/('Content/'+self.p['map'][6:]+'.umap')).read_bytes()).hexdigest(),
            'retirement_policy':'Only these exact prior paths after complete replacement Bake verification'}
        self.write()
        assert not live-known,'A saved Landscape lacks successful-ledger or exact official HDA output ownership; manager reconciliation required'
        self.previous_baked_paths=sorted(known)
        self.state['previous_baked_actor_paths']=self.previous_baked_paths

    def write(self):
        payload=json.dumps(self.state,indent=2,default=str)
        paths=[self.state_path]
        if self.p.get('build_state_alias'):paths.append(Path(self.p['build_state_alias']))
        for path in paths:
            pending=path.with_name(path.name+'.'+str(os.getpid())+'.pending')
            pending.write_text(payload,encoding='utf-8')
            os.replace(pending,path)

    def expected_native_material_groups(self,instances):
        """Count every exact native mesh/material family, including facade variants."""
        groups=Counter()
        defaults={}
        for item in instances:
            mesh=item['path']
            slots=item.get('material_slots') or self.p.get('instance_materials',{}).get(mesh)
            if slots is None:
                if mesh not in defaults:
                    asset=unreal.load_asset(mesh)
                    assert isinstance(asset,unreal.StaticMesh),mesh
                    defaults[mesh]=[_path(s.material_interface) for s in asset.get_editor_property('static_materials')]
                slots=defaults[mesh]
            assert slots and all(slots),'Missing native material family: '+mesh
            groups[(mesh,tuple(slots))]+=1
        return groups

    def configure_engine_outputs(self,w):
        """Make native output translation explicit before rebuild and recook."""
        self.guard()
        if not w.get_houdini_asset_component():
            raise RuntimeError('The official HDA wrapper has no native component')
        if not w.get_houdini_cookable():
            raise RuntimeError('The official HDA wrapper has no cookable')
        before=bool(w.is_do_not_generate_outputs_enabled())
        # The setter returns false when already set correctly; use readback.
        w.set_do_not_generate_outputs(False)
        if w.is_do_not_generate_outputs_enabled():
            raise RuntimeError('Houdini Engine output generation remains disabled')
        # Protected OutputData and deprecated HAC copies are not accessed.
        # The existing complete-output gate verifies actual native translation.
        self.state.setdefault('engine_output_configuration',[]).append(
            {'output_generation_disabled_before':before,
             'output_generation_disabled_after':False,
             'actual_outputs_verified_after_processing':False})

    def configure_and_bind(self,w):
        self.guard()
        self.guard_processes()
        w.set_auto_cooking_enabled(False)
        assert not w.is_auto_cooking_enabled()
        self.configure_engine_outputs(w)
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
        assert self.state['bound_table_objects']==[_path(table)],'Official bank input does not reference the requested table'
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
                 'landscape_material':self.p['landscape_material'],
                 'mesh_preview_material':self.p['procedural_material'],
                 'bank_instance_materials':_hda_json(self.p.get('instance_materials',{})),
                 'environment_style_set':self.p['environment_style_set'],'landscape_layerinfo_bake_root':self.p['root'],
                 'catalog_release_id':release.get('id',''),'bank_style_set':release.get('style_set',''),
                 'catalog_expected_sha256':release.get('catalog_sha256',self.p['catalog_sha256'])}
        if 'building_assembly_contract' in self.p:
            strings['building_assembly_contract_json']=_hda_json(self.p['building_assembly_contract'])
        strings['road_provider']='houdini' if self.native_road_phase=='export' else ('RoadBLD' if self.native_road_contract else self.p.get('road_provider','houdini'))
        strings['road_provider_contract_json']=_hda_json(self.native_road_contract or ({} if self.native_road_phase=='export' else self.p.get('road_provider_contract',{})))
        strings['route_surface_materials_json']=_hda_json(self.p.get('route_surface_materials',{}))
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
            assert w.get_int_parameter_value(name)==value,name
        for key,setter in (('cook_folder',w.set_temporary_cook_folder),('bake_folder',w.set_bake_folder)):
            directory=unreal.DirectoryPath();directory.path=self.p[key]
            assert setter(directory)
        assert w.set_replace_previous_bake(True)
        assert w.get_replace_previous_bake()
        assert w.set_remove_output_after_bake(True)
        assert w.get_remove_output_after_bake()
        assert w.set_auto_bake_enabled(False)
        assert not w.is_auto_bake_enabled()
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
        if self.state['phase']!='waiting_for_instantiation':return
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
            error_path=Path(str(self.receipt)+'.errors.json')
            if error_path.exists():
                self.state['stage_errors']=json.loads(error_path.read_text())
                assert not self.state['stage_errors'],'HDA reported incomplete/error output'
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
                self.state['geographic_building_coverage']={'total':total,'whole_native':assembly['whole_native_building_count'],
                    'native_assembly':assembly['assembled_building_count'],'explicitly_unsupported':assembly['unsupported_count'],
                    'constructed':assembly['whole_native_building_count']+assembly['assembled_building_count'],
                    'complete_native_construction':assembly['unsupported_count']==0}
                self.write()
                assert all(isinstance(assembly[key],int) and not isinstance(assembly[key],bool) and assembly[key]>=0 for key in
                           ('whole_native_building_count','assembled_building_count','unsupported_count','native_module_point_count')),'Invalid native building ledger counts'
                assert assembly['unsupported_count']==len(assembly['unsupported'])==0,'Unsupported buildings remain; refusing complete-area Bake'
                ids=assembly['assembled_osm_ids']
                assert len(ids)==len(set(ids))==assembly['assembled_building_count'],'Native assembly identity ledger differs'
                assert assembly['native_module_point_count']==sum(x['role']=='building_module' for x in receipt.get('nonbuilding_instances',[])),'Native module receipt differs from assembly ledger'
                assert assembly['assembled_building_count']==0 or assembly['native_module_point_count']>0,'Enabled assembly emitted no native facade modules'
                if self.p['building_assembly_contract'].get('building_style_variants',{}).get('enabled'):
                    styles=receipt.get('building_style_variants',{})
                    assert styles,'Completed native building style ledger is missing'
                    assert sum(styles['family_building_counts'].values())==assembly['assembled_building_count']
                    assert sum(styles['palette_building_counts'].values())==assembly['assembled_building_count']
                    assert len(styles['family_building_counts'])>=2 and len(styles['palette_building_counts'])>=2,'Enabled native appearance variety was not generated'
                    self.state['building_style_variants']=styles
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
            expected_groups=self.expected_native_material_groups(instances)
            actual_groups=Counter()
            for rec in meshes:
                actual_groups[(rec['mesh'],tuple(rec['materials']))]+=rec['instances']
            assert actual_groups==expected_groups,'Native mesh/material family counts differ from complete instance receipt'
            self.state['native_material_family_count']=len(actual_groups)
            self.state['surface_geometry']=receipt.get('surface_geometry',{})
            landscapes=list(self.official_landscapes(w).values())
            assert len(landscapes)==1 and _path(landscapes[0].landscape_material)==self.p['landscape_material']
            if self.p.get('landscape_grass',{}).get('enabled'):
                self.state['geographic_ground_connection']=geocity_landscape_workflow.verify_landscape(self,landscapes[0],receipt)
            self.guard()
            self.state.update(phase='cooked_verified',row_count=len(receipt['rows']),
                              catalog_sha256=receipt['catalog_sha256'],output_count=w.get_num_outputs(),
                              instance_count=actual,roles=dict(Counter(x['role'] for x in instances)),native_components=meshes)
            self.state.pop('error',None);self.write()
            if (self.p.get('landscape_grass',{}).get('enabled')
                    and not self.state['geographic_ground_connection']['paint_ready']):
                self.cooked_landscape=landscapes[0]
                self.completed_receipt=receipt
                self.paint_wait_started=time.time()
                self.paint_last_probe=self.paint_wait_started
                self.state['phase']='cooked_waiting_for_paint';self.write()
                self.save_tick=unreal.register_slate_post_tick_callback(self.finish_cook_readiness)
            else:self.advance_cooked(receipt)
        except Exception as exc:
            self.state['output_count']=w.get_num_outputs()
            error_path=Path(str(self.receipt)+'.errors.json')
            if error_path.exists():self.state['stage_errors']=json.loads(error_path.read_text())
            self.fail('failed_cook_verification',exc)

    def finish_cook_readiness(self,delta_time):
        """CPU weight readback may lag official output callbacks; never recook."""
        try:
            self.guard()
            if time.time()-self.paint_last_probe<1:return
            self.paint_last_probe=time.time()
            result=geocity_landscape_workflow.verify_landscape(self,self.cooked_landscape,self.completed_receipt)
            self.state['geographic_ground_connection']=result
            self.state['paint_readiness_wait_seconds']=time.time()-self.paint_wait_started
            self.write()
            if not result['paint_ready']:
                assert time.time()-self.paint_wait_started<120,'Ground paint unavailable before native road authoring/Bake'
                return
            unreal.unregister_slate_post_tick_callback(self.save_tick);self.save_tick=None
            self.guard()
            self.state['phase']='cooked_verified';self.write()
            self.advance_cooked(self.completed_receipt)
        except Exception as exc:self.fail('failed_cook_paint_readiness',exc)

    def advance_cooked(self,receipt):
        if self.action in ('regenerate','instantiate'):
            if self.native_road_phase=='export':self.begin_native_roads(receipt)
            else:
                if self.native_road_phase=='suppression':
                    provider=receipt.get('surface_geometry',{}).get('road_provider',{})
                    assert provider.get('provider')=='RoadBLD' and provider.get('vehicle_surfaces_suppressed') is True,'Native provider suppression is incomplete before Bake'
                    contract=provider.get('contract') or provider.get('original_contract') or {}
                    assert contract.get('transaction',{}).get('token')==self.native_road_contract['transaction']['token'],'Suppression belongs to another native transaction'
                    for key in ('area_id','source_sha256','centreline_sha256','drivable_source_ids','source_road_count','generated_road_count','generated_piece_ids'):
                        assert provider.get(key)==self.native_road_contract[key],'Suppression/native contract differs before Bake: '+key
                    self.state['native_suppression_verified_before_bake']=True;self.write()
                self.bake_and_save()
        else:self.finish_operation()

    def begin_native_roads(self,receipt):
        """Stage native roads from this completed cook before saving either provider."""
        self.guard()
        assert self.native_road_phase=='export' and self.state['phase']=='cooked_verified'
        assert receipt.get('roadbld_centerlines'),'Completed final-ground road export is missing'
        if not self.api.is_asset_cooking_paused():self.api.pause_asset_cooking()
        self.native_road_phase='authoring'
        self.state['phase']='native_road_authoring';self.write()
        dirty=[_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]+[_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
        import geocity_roadbld_workflow
        self.native_road_run=geocity_roadbld_workflow.build(self.profile_path,export=receipt['roadbld_centerlines'],
            settings=self.p.get('roadbld_workflow',{}).get('settings'),reviewed_dirty_packages=dirty,on_complete=self.after_native_roads)

    def after_native_roads(self,native,success):
        self.native_road_run=native
        try:
            self.guard()
            assert self.native_road_phase=='authoring','Unexpected native completion callback'
            assert success,'Native road authoring failed: '+str(native.state.get('error'))
            contract=native.staged_contract()
            assert contract['named_map']==self.p['map'] and not contract['saved']
            assert contract['transaction']['pid']==os.getpid()
            assert contract['transaction']['lease_sha256']==hashlib.sha256(self.lease_line.encode('utf-8')).hexdigest()
            paths={_path(a) for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
            required=set(contract['road_actor_paths'])|set(contract['geometry_actor_paths'])|{contract['network_actor_path']}
            derived=contract.get('derived_junction_roads',[])
            derived_paths={row['road_actor_path'] for row in derived}
            owned=set(contract['owned_actor_paths'])
            assert len(derived_paths)==len(derived) and not derived_paths.intersection(contract['road_actor_paths'])
            assert contract['actual_native_road_actor_count']==len(contract['road_actor_paths'])+len(derived_paths)
            assert derived_paths.issubset(owned) and required.issubset(owned)
            required=owned
            assert required and required.issubset(paths),'Validated native candidate actors are absent from current world'
            prefix=self.p['map']+'.'+self.p['map'].rsplit('/',1)[-1]+':PersistentLevel.'
            actors={_path(a):a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
            for path in required:
                assert path.startswith(prefix),'Native candidate actor is outside the named area'
                tags={str(v) for v in actors[path].get_editor_property('tags')}
                assert {'GeoCity_RoadBLD','GeoCityArea_'+contract['area_id']}.issubset(tags),'Native candidate actor ownership differs'
            self.native_road_run=native
            self.native_road_contract=contract
            self.native_road_phase='suppression'
            self.state['native_road_staged_contract']=contract;self.write()
            # All native and parent ownership gates passed. This is the last
            # reversible correction boundary before official suppression Cook.
            import geocity_roadbld_grounding as grounding
            grounding.commit_correction(native)
            if self.api.is_asset_cooking_paused():self.api.resume_asset_cooking()
            self.configure_and_bind(self.wrapper)
        except Exception as exc:
            import geocity_roadbld_grounding as grounding
            try:grounding.rollback_correction(native,exc)
            except Exception as rollback_exc:self.state['correction_rollback_error']=repr(rollback_exc)
            self.fail('failed_native_road_transaction',exc)

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
        if self.state['phase']!='baking':return
        try:
            self.guard()
            self.state.update(phase='baked_waiting_for_output_removal' if success else 'failed_bake',bake_success=bool(success))
            self.write()
            if success:
                self.bake_completed_epoch=time.time()
                self.save_tick=unreal.register_slate_post_tick_callback(self.finish_save)
            else:self.fail('failed_bake',RuntimeError('Official Houdini Engine Bake failed'))
        except Exception as exc:self.fail('failed_bake_callback',exc)

    def finish_save(self,delta_time):
        try:
            self.guard()
            # Weight readback is expensive and may lag a native callback.
            # Keep Slate responsive while the bounded readiness gate waits.
            if time.time()-getattr(self,'last_save_probe',0)<1:return
            self.last_save_probe=time.time()
            components=self.wrapper.get_houdini_asset_actor().get_components_by_class(unreal.MeshComponent)
            if components:
                assert time.time()-self.bake_completed_epoch<120,'Cooked output was not removed'
                return
            if self.p.get('landscape_grass',{}).get('enabled'):
                # Inspect this completed Bake, before exact obsolete actors
                # are retired below. A prior saved Landscape can still exist.
                landscapes=[a for a in self.wrapper.get_baked_output_actors() if isinstance(a,unreal.Landscape)]
                assert len(landscapes)==1,'Completed Bake has no unique geographic Landscape'
                grass=geocity_landscape_workflow.verify_landscape(self,landscapes[0],json.loads(self.receipt.read_text()))
                self.state['geographic_ground_connection']=grass
                if not grass['paint_ready']:
                    # Native post-processing can precede CPU paint readback:
                    # the same generated component returned Ground=1 after
                    # the callback had reported zero. Wait within this normal
                    # save lifecycle; never save an unobserved paint binding.
                    self.write()
                    assert time.time()-self.bake_completed_epoch<120,'Geographic Ground paint readback is unavailable after Bake'
                    return
                # Native Landscape Grass is generated/cached around viewers.
                # Persist its verified graph, weights and profile bindings;
                # distant-view cache emptiness must not block an ordinary save.
                # Actual cache output remains explicitly observed/unobserved.
            # Saving pumps Slate. Detach first to avoid a recursive save callback.
            if self.save_tick is not None:
                unreal.unregister_slate_post_tick_callback(self.save_tick)
                self.save_tick=None
            baked=self.wrapper.get_baked_output_actors()
            receipt=json.loads(self.receipt.read_text())
            expected=Counter(x['path'] for x in receipt.get('nonbuilding_instances',[]))
            actual=Counter()
            material_groups=Counter()
            for actor in baked:
                for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                    if geocity_landscape_workflow.is_native_grass(actor,component,self.p):continue
                    mesh=_path(component.static_mesh)
                    if mesh in expected:
                        actual[mesh]+=component.get_instance_count() if isinstance(component,unreal.InstancedStaticMeshComponent) else 1
                        material_groups[(mesh,tuple(_path(component.get_material(i)) for i in range(component.get_num_materials())))]+=component.get_instance_count() if isinstance(component,unreal.InstancedStaticMeshComponent) else 1
            assert actual==expected,'Baked bank counts differ from cooked bank counts'
            assert material_groups==self.expected_native_material_groups(receipt.get('nonbuilding_instances',[])),'Baked native mesh/material family counts differ'
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
                    if geocity_landscape_workflow.is_native_grass(actor,comp,self.p):continue
                    mesh=_path(comp.static_mesh)
                    if mesh in expected:
                        all_native[mesh]+=comp.get_instance_count() if isinstance(comp,unreal.InstancedStaticMeshComponent) else 1
            assert all_native==expected,'Overlapping native bank copies remain in the area'
            if self.p.get('landscape_grass',{}).get('enabled'):
                landscape=next(a for a in worlds if isinstance(a,unreal.Landscape))
                self.state['geographic_ground_connection']=geocity_landscape_workflow.verify_landscape(self,landscape,receipt)
            self.save_generated_dependencies(baked)
            if self.native_road_run is not None:
                assert self.native_road_phase=='suppression'
                delivery=self.native_road_run.commit(hda_receipt=receipt)
                assert delivery['saved'] and delivery['named_map']==self.p['map']
                self.p['road_provider']='RoadBLD';self.p['road_provider_contract']=delivery
                self.p['roadbld_workflow']['status']='native_generated_saved_verified'
                assert self.wrapper.set_string_parameter_value('road_provider_contract_json',_hda_json(delivery))
                self.state['native_road_delivery']=delivery
            world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
            assert unreal.EditorLoadingAndSavingUtils.save_map(world,self.p['map'])
            self.save_generated_dependencies(baked,include_saved_map=True)
            assert self.p['map'] not in {_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()},'Named map remains dirty after final save'
            self.save_profile()
            self.state.pop('error',None)
            self.state.update(phase='baked_saved_verified',baked_actor_paths=[_path(a) for a in baked],
                              baked_actor_count=len(baked),baked_mesh_counts=dict(actual),
                              cooked_mesh_component_count=0,landscape_count=1,
                              baked_native_material_slots_verified=True,native_execution_verified=True,
                              dirty_maps=[_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
                              unsaved_content_packages=[_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()])
            saved_dependencies=set(self.state['named_generated_dependency_paths'])
            self.state['unreferenced_cook_packages']=[p for p in self.state['unsaved_content_packages']
                if p.startswith(self.p['cook_folder']+'/') and p not in saved_dependencies]
            self.write()
            self.last_successful_path.write_text(json.dumps(self.state,indent=2,default=str),encoding='utf-8')
            self.finish_operation()
        except Exception as exc:
            self.fail('failed_bake_save_verification',exc)

    def save_profile(self):
        """Final-save owner merges only runtime fields into the unchanged file."""
        self.guard()
        current=json.loads(self.profile_path.read_text(encoding='utf-8'))
        merged,changes=_runtime_profile_merge(self.profile_baseline,current,self.p)
        before_sha=self.profile_sha256
        if changes:
            pending=self.profile_path.with_name(self.profile_path.name+'.'+str(os.getpid())+'.pending')
            pending.write_text(json.dumps(merged,indent=2)+'\n',encoding='utf-8')
            self.guard()
            os.replace(pending,self.profile_path)
            self.profile_sha256=hashlib.sha256(self.profile_path.read_bytes()).hexdigest()
        self.profile_baseline=merged
        self.state['runtime_profile_update']={'allowed_fields':list(RUNTIME_PROFILE_FIELDS),'changes':changes,
            'sha256_before':before_sha,'sha256_after':self.profile_sha256,'immutable_configuration_preserved':True}
        self.write()

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
        if self.native_road_phase:
            import geocity_roadbld_workflow
            self.state['native_landscape_authority']=geocity_roadbld_workflow.require_geographic_landscape_authority()
            auth=unreal.get_editor_subsystem(unreal.WorldBLDAuthSubsystem)
            assert auth.has_license_for_tool('RoadBLD'),'RoadBLD is requested but the current WorldBLD session is not authorized; sign in inside Unreal before native road generation'
        dirty=[_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]+[_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
        assert set(dirty)==self.reviewed_dirty_packages,'Resolve or explicitly review current unsaved packages before generation: '+str(dirty)
        foreign={p for p in self.reviewed_dirty_packages if p!=self.p['map'] and not p.startswith(self.p['cook_folder']+'/')}
        if foreign:
            from geocity_editor_action import acknowledged_cook_leftovers
            assert foreign.issubset(acknowledged_cook_leftovers(self.project,foreign)),'Foreign dirty packages are not exact acknowledged unreferenced area cook leftovers'
        self.state['reviewed_dirty_packages']=sorted(self.reviewed_dirty_packages)
        if not self.api.is_session_valid():
            self.state['phase']='connecting_official_engine';self.write()
            self.api.create_session()
        assert self.api.is_session_valid(),'The official Houdini Engine session could not start through the installed native settings; check its connection/license error before retrying'
        self.state['official_engine_connected']=True
        self.suspend_transaction_autosave()
        self.state['landscape_grass_connection']=geocity_landscape_workflow.prepare(self)
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
            self.account_previous_landscapes()
        self.wrapper.set_auto_cooking_enabled(False)
        assert self.wrapper.set_auto_bake_enabled(False)
        self.configure_engine_outputs(self.wrapper)
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
    import geocity_runtime_guard
    geocity_runtime_guard.verify()
    run=GeoCityRun(profile_path,reviewed_dirty_packages,release_menu_lease)
    ACTIVE.append(run)
    try:
        return run.start(action)
    except Exception as exc:
        run.fail('failed_start',exc)
        raise

