"""Offline captured-array replay. Never imports or calls an active Unreal editor."""
import gzip
import hashlib
import json
import math
import sys
import time
from types import SimpleNamespace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT/'Content/Python'))
sys.dont_write_bytecode = True
import geocity_roadbld_grounding as g
import geocity_roadbld_seams as s

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load():
    review = json.loads((HERE/'ALL40_OFFLINE_REVIEW_20261003T213901084762Z.json').read_text())
    plan = json.loads((HERE/'EXTERIOR_INTERVAL_EVIDENCE_20261003T213208608026Z.json').read_text())['plan']
    package = review['review_geometry_packages']['retained_preclip']
    assert sha(package['path']) == package['sha256']
    with gzip.open(package['path'], 'rt') as stream:
        data = json.load(stream)
    surfaces = [{**ref, **data['geometry_blobs'][ref['geometry_blob_sha256']]} for ref in data['surface_references']]
    changes = []
    for surface in surfaces:
        assert surface['frame']['scale3d'] == [1.,1.,1.]
        assert surface['frame']['rotation_xyzw'] == [0.,0.,0.,1.]
        flags=[]
        for number,(triangle,material,old) in enumerate(zip(surface['triangles'],surface['material_ids'],surface['upward'])):
            points=[surface['points_cm'][i] for i in triangle]
            try:
                normal_z=-s._unit_normal(points)[2]
            except AssertionError:
                normal_z=0.
            flag=material==0 and normal_z>.25
            flags.append(flag)
            if flag != old:
                changes.append({'component':surface['component_path'],'triangle':number,'old':old,'new':flag,'actual_native_normal_z':normal_z})
        surface['upward']=flags
    rows=[row for row in review['source_rows'] if row['piece_id'] in review['affected_piece_ids']]
    return review,plan,surfaces,rows,changes

if __name__ == '__main__' and '--transaction' not in sys.argv:
    began=time.monotonic()
    review,plan,surfaces,rows,changes=load()
    print('captured surfaces',len(surfaces),'affected rows',len(rows),'normal changes',len(changes),flush=True)
    gaps,proof=s.continuous_gaps(plan,rows,surfaces,lambda:None)
    print('refreshed preclip gaps',len(gaps),'max',max(v['length_cm'] for v in gaps),flush=True)
    result={'source_scope':'all40 captured audit; replay geometry restricted to its 16 affected source rows and 58 captured components',
            'captured_all40_gap_count':review['gap_count'],'replayed_source_rows':len(rows),
            'refreshed_eligibility_changes':changes,'initial_refreshed_preclip_gaps':gaps,'initial_proof':proof,
            'editor_calls':0,'elapsed_seconds':time.monotonic()-began}
    diagnostic_name='TASK1_REPLACEMENT_V3_REPLAY_DIAGNOSTIC.json' if '--v3-xy' in sys.argv else 'TASK1_REPLACEMENT_REPLAY_DIAGNOSTIC.json'
    (HERE/diagnostic_name).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    # The replay executes the production planner/iteration with explicit array
    # sinks. It proves XY coverage and ownership, not native Boolean/UV/collision
    # execution or physical Landscape heights, which require the owned editor.
    replay_patches=[]
    def append_array(surface,points,triangles):
        offset=len(surface['points_cm'])
        surface['points_cm']=surface['points_cm']+points
        surface['triangles']=surface['triangles']+[[offset+i for i in tri] for tri in triangles]
        surface['material_ids']=surface['material_ids']+[0]*len(triangles)
        surface['upward']=surface['upward']+[True]*len(triangles)
    def apron(run,proposal,surfaces,fields,landscape_z,bounded):
        carrier=next(v for v in surfaces if v['component_path']==proposal['component_path'])
        ring=proposal['ring_world_xy_cm']
        tri=fields[carrier['component_path']].faces[proposal['parent_asphalt_triangle_index']]
        points=[[x,y,g._plane_z(g._barycentric([x,y],*tri),tri)] for x,y in ring]
        append_array(carrier,points,[[0,1,2],[0,2,3]])
        replay_patches.append({'kind':'join_plan_xy_projection','component':carrier['component_path'],'ring':ring})
        print('join strip',proposal['gap']['piece_id'],round(proposal['longitudinal_length_cm'],3),flush=True)
    def fan(surface,proposal,bounded):
        points=proposal['boundary_edge_world_cm']+[proposal['support_vertex_world_cm']]
        append_array(surface,points,[[0,1,2]])
        replay_patches.append({'kind':'fan_actual_plane','component':surface['component_path'],'proposal':proposal})
        print('fan',proposal['gap']['piece_id'],proposal['gap']['length_cm'],flush=True)
    def nearest_native_plane(x,y):
        # A geometric replay fixture, deliberately not called Landscape proof.
        candidates=[]
        for v in surfaces:
            f=g.AsphaltField(v['points_cm'],v['triangles'],v['material_ids'],v['upward'])
            hit=f.covered([x,y])
            if hit:
                candidates.append((0.,hit[0]))
            else:
                for t in f.faces.values():
                    dist,p=g._closest_xy([x,y],t)
                    candidates.append((dist,g._plane_z(g._barycentric([x,y],*t),t)))
        return min(candidates,key=lambda v:v[0])[1]-plan['settings']['surface_clearance_cm']
    # Small-fan support Z must use its selected native parent plane; the
    # production check still calls the real Landscape and enforces <=10cm.
    last_support={}
    original_plan=s.plan_boundary_fan
    def boundary_plan(*args,**kwargs):
        args=list(args);args[4]=lambda x,y:0.
        proposal=original_plan(*args,**kwargs)
        surface=next(v for v in surfaces if v['component_path']==proposal['component_path'])
        tri=args[3][surface['component_path']].faces[proposal['parent_asphalt_triangle_index']]
        p=proposal['support_vertex_world_cm'];z=g._plane_z(g._barycentric(p,*tri),tri)
        last_support['z']=z-plan['settings']['surface_clearance_cm']
        return proposal
    s._append_connector_apron=apron
    s._append_fan=fan
    s.refresh_surface=lambda surface:None
    s._clear_fan_obstructions=lambda *args:None
    s.plan_boundary_fan=boundary_plan
    try:
        proof=s.repair_continuous(SimpleNamespace(plan=plan),rows,surfaces,lambda x,y:last_support['z'],lambda:None)
        result['xy_planner_replay']=proof
        result['status']='XY_PLANNER_REPLAY_PASSED_NATIVE_OPERATIONS_NOT_RUN'
    except Exception as exc:
        result['status']='REPLAY_FAILED'
        result['error']=repr(exc)
        raise
    finally:
        result['executed_array_sinks']=replay_patches
        result['not_run']=['Unreal Boolean trimming','native UV/normal/material/collision mutation and rollback','Landscape height validation','static mesh conversion','editor binding/save/reopen','unaffected24 geometry replay']
        result['elapsed_seconds']=time.monotonic()-began
        replay_name='TASK1_REPLACEMENT_V3_CAPTURED_REPLAY.json' if '--v3-xy' in sys.argv else 'TASK1_REPLACEMENT_CAPTURED_REPLAY.json'
        (HERE/replay_name).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


def transaction_replay():
    """Production transaction/control flow; explicit surrogate native IO only."""
    import ast, copy, os, tempfile, types
    import geocity_roadbld_workflow as w
    import geocity_roadbld_clip as c
    NS=SimpleNamespace
    class Mesh:
        def __init__(self,name):
            self.name=name
            self.payload={'positions':[[1.,2.,3.]],'triangles':[[0,0,0]],'uvs':[[.2,.7]],
                          'split_normals':[[0.,0.,1.]],'material_ids':[0]}
            self.slots=[NS(material_interface='material_native',material_slot_name='asphalt')]
            self.metadata={'GeoCityNativeSourceMesh':'original_native','collision_note':'original','empty_value':''}
        def get_editor_property(self,key):
            assert key=='static_materials';return self.slots
        def set_editor_property(self,key,value):
            assert key=='static_materials';self.slots=list(value)
    class Component:
        def __init__(self,mesh):self.static_mesh=mesh;self.path=mesh.name+'.component'
        def set_static_mesh(self,mesh):self.static_mesh=mesh;return True
        def get_world_transform(self):return 'unchanged_transform'
        def get_num_materials(self):return 1
        def get_material(self,i):return 'material_native'
    class Options:
        def set_editor_property(self,*args):pass
    class AssetLib:
        get_metadata_tag_values=staticmethod(lambda mesh:dict(mesh.metadata))
        remove_metadata_tag=staticmethod(lambda mesh,key:mesh.metadata.pop(key))
        set_metadata_tag=staticmethod(lambda mesh,key,value:mesh.metadata.__setitem__(key,value))
    def copy_mesh(source,target,*args):target.payload=copy.deepcopy(source);return source,True
    native_io=NS(EditorAssetLibrary=AssetLib,GeometryScriptCopyMeshToAssetOptions=Options,
                 GeometryScriptMeshWriteLOD=Options,GeometryScript_AssetUtils=NS(copy_mesh_to_static_mesh=copy_mesh))
    c.unreal=native_io
    c._success=lambda outcome: outcome is True or (_ for _ in ()).throw(AssertionError('copy failed'))
    c._read_geometry=lambda mesh,transform:(mesh['positions'],mesh['triangles'])
    c._copy_static=lambda mesh:copy.deepcopy(mesh.payload)
    c._mesh_payload_sha=lambda mesh,transform:g._sha(mesh)
    c._materials=lambda component:['material_native']
    c._collision=lambda component,mesh:{'complexity':'original','simple_shape_count':0}
    c._transform=lambda transform:transform
    c._path=lambda obj:obj if isinstance(obj,str) else obj.name
    w._path=lambda obj:obj.path
    w._get=lambda obj,key:getattr(obj,key)
    w._plain=lambda value:value
    sys.modules['geocity_roadbld_topology']=NS(classify_native_junction_issues=lambda run,issues:([],[]))
    original_verify_links=g._verify_links
    g._verify_links=lambda run,previous,result:{'passed':True,'source_coverage_accounted':True}
    g.verify_native_delivery=lambda *args,**kwargs:{'automatic_empty_geometry':[],'passed':True}
    parent_tree=ast.parse((ROOT/'Content/Python/geocity_bank_workflow.py').read_text())
    parent_node=next(n for node in parent_tree.body if isinstance(node,ast.ClassDef)
                     for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='after_native_roads')
    parent_namespace={'os':os,'hashlib':hashlib,'_path':w._path}
    exec(compile(ast.Module(body=[parent_node],type_ignores=[]),str(ROOT/'Content/Python/geocity_bank_workflow.py'),'exec'),parent_namespace)
    parent_method=parent_namespace['after_native_roads']
    event_log=[]
    with tempfile.TemporaryDirectory(prefix='geocity_transaction_replay_') as temp:
        folder=Path(temp);serial=0
        def fixture():
            nonlocal serial
            serial+=1
            run=object.__new__(w.RoadBLDRun)
            run.state={'phase':'failed_validating','original_marker':{'retained':True}}
            run.state_path=folder/('state_'+str(serial)+'.json');run.state_path.write_text(json.dumps(run.state))
            run.grounding_report={'original_ground':True};run.clipping_report={'original_clip':True}
            run.junction_repair=None;run.landscape_sampler=NS(path='landscape_original')
            run._grounding_transient_diagnostic=object();run.geo_actors=[]
            run.revision='fixture_revision';run.transaction_token='fixture_token';run.tick_handle=None;run._tick_running=False
            run.guard=lambda:None
            run.write=lambda:run.state_path.write_text(json.dumps(run.state))
            original_refs={k:getattr(run,k) for k in ('state','grounding_report','clipping_report','landscape_sampler','_grounding_transient_diagnostic','geo_actors')}
            original_values={k:copy.deepcopy(getattr(run,k)) for k in ('state','grounding_report','clipping_report')}
            snapshots=[]
            for i in range(3):
                mesh=Mesh('candidate_'+str(i));component=Component(mesh)
                snapshots.append({'source':mesh,'component':component,'rollback_mesh':copy.deepcopy(mesh.payload),
                    'rollback_slots':list(mesh.slots),'rollback_metadata':c._candidate_metadata(mesh),
                    'materials':['material_native'],'collision':c._collision(component,mesh),'transform':'unchanged_transform'})
            pending=g._PendingCorrection(run,snapshots,folder/('correction_'+str(serial)+'.json'))
            pending.wrote_candidates=True;pending.result={'receipt':'fixture'}
            for snap in snapshots:
                snap['source'].payload={'positions':[[9.,9.,9.]],'triangles':[[0,0,0]],'uvs':[[.8,.8]],'split_normals':[[1.,0.,0.]],'material_ids':[2]}
                snap['source'].metadata={'GeoCityNativeSourceMesh':'incorrect_self_reference','newly_added':'must_disappear'}
            run.grounding_report={'corrected_ground':True};run.clipping_report={'corrected_clip':True}
            run.landscape_sampler=NS(path='landscape_corrected');run.state['phase']='validating'
            samples=copy.copy(snapshots)
            def restored():
                assert run._pending_correction is None
                for key in original_refs:assert getattr(run,key) is original_refs[key],key
                for key,value in original_values.items():assert getattr(run,key)==value,key
                assert run.state_path.read_bytes()==pending.state_bytes
                for snap in samples:
                    assert snap['source'].payload==snap['rollback_mesh']
                    assert snap['source'].metadata==snap['rollback_metadata']
                    assert snap['source'].slots==snap['rollback_slots']
                    assert snap['component'].static_mesh is snap['source']
                assert not pending.snapshots
            named_map='/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
            prefix=named_map+'.'+named_map.rsplit('/',1)[-1]+':PersistentLevel.'
            tags=['GeoCity_RoadBLD','GeoCityArea_GazaShujaiya']
            def actor(name):return NS(path=prefix+name,get_editor_property=lambda key:tags)
            road=actor('ReplayRoad');geo=actor('ReplayGeo');network=actor('ReplayNetwork')
            network.is_road_network_stale=lambda:False
            geo.SourceRoads=[road];geo.bDisableIntersectionLandscapeAlignment=True
            geo.get_components_by_class=lambda cls:[samples[0]['component']]
            run.network=network;run.roads=[road];run.derived_junction_roads=[]
            run.plan={'source_piece_count':1,'roads':[{'points_m':[[0.,0.,0.],[1.,0.,0.]],'width_m':7.,'source_osm_id':'fixture','piece_id':'fixture:0'}],
                      'settings':{'max_geometry_issues':1,'surface_clearance_cm':5.,'centreline_fit_tolerance_cm':50.,'ground_profile_tolerance_cm':10.},
                      'drivable_piece_ids':['fixture:0'],'drivable_source_ids':['fixture']}
            run.p={'map':named_map};run.lease_line='fixture_lease'
            run.check_road=lambda *args:None;run.tag=lambda *args:None
            run.native_geos=lambda:[geo];run.owned_actors=lambda:[road,geo,network]
            def footprint(owned):run.state['native_mesh_footprint_validation']={'passed':True};return {'passed':True}
            run.validate_mesh_footprints=footprint
            run.capture_component_bindings=lambda actors:[{'fixture':True}]
            run.state.update(area_id='GazaShujaiya',named_map=named_map,mode='native',source_sha256='fixture',centreline_sha256='fixture',
                drivable_source_ids=['fixture'],source_road_count=1,source_piece_count=1,network_actor_path=network.path,protected_footprint_proof={})
            def tool(group,name,*args):
                if name=='DescribeNetwork':return [NS(RoadCount=1,Roads=[NS(Actor=NS(RefPath=road.path))])]
                if name in ('FindJunctionIssues','FindGeometryIssues'):return []
                if name=='SampleRoad':return [NS(Location=NS(x=0.,y=0.,z=5.),LeftWidth=350.,RightWidth=350.)]
                raise AssertionError(name)
            w._tool=tool
            actors=[road,geo,network]
            runtime=NS(MeshComponent=Component,PrimitiveComponent=Component,EditorActorSubsystem=object,log_error=lambda text:None,
                       get_editor_subsystem=lambda cls:NS(get_all_level_actors=lambda:actors))
            w.unreal=runtime;parent_namespace['unreal']=runtime
            parent=NS(guard=lambda:None,native_road_phase='authoring',p={'map':named_map},lease_line=run.lease_line,state={})
            parent.write=lambda:event_log.append('parent_write')
            parent.fail=lambda phase,exc:event_log.append('parent_failed')
            def resume():
                assert run._pending_correction is None and pending.status=='committed' and not pending.snapshots
                event_log.append('suppression_resume')
            parent.api=NS(is_asset_cooking_paused=lambda:True,resume_asset_cooking=resume)
            parent.wrapper=object();parent.configure_and_bind=lambda wrapper:event_log.append('configure')
            return run,pending,parent,restored
        def trace_at(code,line,action):
            def tracer(frame,event,arg):
                if frame.f_code is code and event=='line' and frame.f_lineno==line:
                    sys.settrace(None);raise RuntimeError('injected gate '+str(line))
                return tracer
            sys.settrace(tracer)
            try:return action()
            finally:sys.settrace(None)
        results=[]
        # Actual verify_links guard rolls back on internal lineage failure.
        run,pending,parent,restored=fixture()
        g._verify_links=lambda *args:(_ for _ in ()).throw(RuntimeError('injected lineage failure'))
        try:g.verify_links(run,{},pending.result)
        except RuntimeError:pass
        else:raise AssertionError('lineage failure escaped')
        restored();results.append('verify_links_failure_restored')
        g._verify_links=lambda *args:{'passed':True,'source_coverage_accounted':True}
        # Discover the executed lines of actual ordinary validation and parent.
        codes={w.RoadBLDRun._validate_native.__code__,w.RoadBLDRun._staged_contract_native.__code__,parent_method.__code__}
        lines={code:set() for code in codes}
        def record(frame,event,arg):
            if event=='line' and frame.f_code in lines:lines[frame.f_code].add(frame.f_lineno)
            return record
        run,pending,parent,restored=fixture();g.verify_links(run,{},pending.result)
        sys.settrace(record)
        try:
            run.validate();parent_method(parent,run,True)
        finally:sys.settrace(None)
        assert pending.status=='committed' and event_log[-2:]==['suppression_resume','configure']
        results.append('commit_before_suppression_success')
        # Parent lines at/after commit belong to the explicit point of no return.
        commit_line=next(n.lineno for n in ast.walk(parent_node) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
                         and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='commit_correction')
        injected=[]
        for code in codes:
            for line in sorted(lines[code]):
                if code is parent_method.__code__ and line>commit_line:continue
                if code is parent_method.__code__ and line in {n.lineno for n in ast.walk(parent_node) if isinstance(n,ast.Try)}:continue
                run,pending,parent,restored=fixture();g.verify_links(run,{},pending.result)
                before_resumes=event_log.count('suppression_resume')
                if code is w.RoadBLDRun._validate_native.__code__:
                    action=run.validate
                else:
                    run.validate()
                    action=(lambda:run.staged_contract()) if code is w.RoadBLDRun._staged_contract_native.__code__ else (lambda:parent_method(parent,run,True))
                try:trace_at(code,line,action)
                except RuntimeError:pass
                try:restored()
                except AssertionError as exc:raise AssertionError((code.co_name,line,'restoration failed')) from exc
                assert event_log.count('suppression_resume')==before_resumes
                injected.append({'function':code.co_name,'line':line})
        # A wrapper failure after successful verify_links still restores via
        # its required explicit rollback API, and premature commit fails closed.
        for kind in ('post_links_owner_failure','premature_commit'):
            run,pending,parent,restored=fixture();g.verify_links(run,{},pending.result)
            if kind=='post_links_owner_failure':g.rollback_correction(run,RuntimeError(kind))
            else:
                try:g.commit_correction(run)
                except AssertionError:pass
                else:raise AssertionError('early commit accepted')
            restored();results.append(kind+'_restored')
        run.on_complete=lambda owner,success:event_log.append(('failure_callback',success))
        run.fail(RuntimeError('owner cleanup after rollback'))
        restored();assert event_log[-1]==('failure_callback',False)
        results.append('ordinary_fail_after_rollback_preserves_prior_native_state')
        run,pending,parent,restored=fixture();g.verify_links(run,{},pending.result);run.validate()
        resolution=pending.resolution
        def fail_commit_receipt(status,*args):
            if status=='committed_before_suppression':raise OSError('injected commit receipt write failure')
            return resolution(status,*args)
        pending.resolution=fail_commit_receipt
        before_resumes=event_log.count('suppression_resume');parent_method(parent,run,True)
        restored();assert event_log.count('suppression_resume')==before_resumes
        results.append('commit_receipt_failure_restores_before_suppression')
        run,pending,parent,restored=fixture();restore=c._restore_candidate_asset
        c._restore_candidate_asset=lambda snap:(_ for _ in ()).throw(RuntimeError('injected native restore failure'))
        try:g.rollback_correction(run,RuntimeError('owner failed'))
        except RuntimeError:pass
        else:raise AssertionError('rollback failure hidden')
        assert run._pending_correction is pending and pending.status=='rollback_failed' and len(pending.snapshots)==3
        c._restore_candidate_asset=restore;g.rollback_correction(run,RuntimeError('retry restore'));restored()
        results.append('rollback_failure_retains_handles_then_retry_restores')
    g._verify_links=original_verify_links
    report={'status':'PASSED_OFFLINE_TRANSACTION_CONTROL_FLOW','checks':results,'injected_gate_count':len(injected),'injected_gates':injected,
            'production_code_executed':['_PendingCorrection','rollback_correction','commit_correction','verify_links exception guard',
                 'RoadBLDRun.validate','RoadBLDRun._validate_native','RoadBLDRun.staged_contract','RoadBLDRun._staged_contract_native',
                 'parent after_native_roads','clip._restore_candidate_asset'],
            'state_reference_identity_and_bytes_restored':True,'metadata_absence_empty_values_and_added_tags_restored':True,
            'native_IO':'Explicit in-memory surrogates for native mesh/asset/component calls. No Unreal imported or called.',
            'limits':['Real UObject lifetime/GC and GeometryScript conversion/restoration are NOT proven',
                      'UV/split normal/collision native fidelity remains an editor readback requirement',
                      'Physical geometry and Landscape checks substituted; this tests transaction control flow only'],
            'source_hashes':{n:sha(ROOT/'Content/Python'/n) for n in ('geocity_roadbld_grounding.py','geocity_roadbld_clip.py','geocity_roadbld_workflow.py','geocity_bank_workflow.py')}}
    (HERE/'TASK1_REPLACEMENT_V3_TRANSACTION_REPLAY.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'injected_gates':len(injected),'checks':results},indent=2))


if __name__ == '__main__' and '--transaction' in sys.argv:
    transaction_replay()
