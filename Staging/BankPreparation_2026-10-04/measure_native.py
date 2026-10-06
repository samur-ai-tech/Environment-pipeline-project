"""Run under the sole leased Unreal editor. Read assets, never modify or save packages."""
import unreal,json,pathlib,os,time,traceback
OUT=pathlib.Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/BankPreparation_2026-10-04')
OWNER=OUT.parent/'ModelBank/EDITOR_OWNER.txt'
lease=[s for s in OWNER.read_text().splitlines() if s.strip()][-1]
assert 'OWNER=CODEX_BANK_PREPARATION' in lease and 'assigned_editor_PID='+str(os.getpid()) in lease,'editor_lease_changed'
def dirty():return sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
before=dirty();world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
queue=json.loads((OUT/'NATIVE_READBACK_QUEUE.json').read_text());dest=OUT/'NATIVE_MEASUREMENTS.json'
results=json.loads(dest.read_text()) if dest.exists() else {}
sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);registry=unreal.AssetRegistryHelpers.get_asset_registry()
options=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_game_package_references=True,include_editor_only_package_references=False)
cache={};known={}
def dependencies(pkg):
    todo=[pkg];seen=set();missing=[]
    while todo:
        p=todo.pop()
        if p in seen or p.startswith('/Script/'):continue
        seen.add(p)
        if p not in known:known[p]=bool(registry.get_assets_by_package_name(p))
        if not known[p]:missing.append(p)
        if p not in cache:cache[p]=[str(d) for d in (registry.get_dependencies(p,options) or [])]
        todo.extend(cache[p])
    return {'packages':sorted(seen),'unresolved_registry_packages':sorted(missing),'method':'on_disk_hard_and_soft_game_package_registry_closure_not_full_runtime_shader_validation'}
start=time.time();count=0
for job in queue:
    aid=job['asset_id']
    if aid in results:continue
    rec={'asset_id':aid,'path':job['path'],'package_sha256_at_queue':job['current_file_sha256'],'pid':os.getpid(),'status':'measuring'}
    try:
        asset=unreal.load_asset(job['path'])
        if not isinstance(asset,unreal.StaticMesh):raise ValueError('not_static_mesh')
        b=asset.get_bounds();lo=[getattr(b.origin,a)-getattr(b.box_extent,a) for a in ('x','y','z')];hi=[getattr(b.origin,a)+getattr(b.box_extent,a) for a in ('x','y','z')]
        rec.update(bounds_cm={'min':lo,'max':hi},dimensions_cm=[h-l for l,h in zip(lo,hi)],
            material_slots=[{'slot':n,'name':str(s.material_slot_name),'path':s.material_interface.get_path_name() if s.material_interface else None} for n,s in enumerate(asset.static_materials)],
            lod_count=sub.get_lod_count(asset),lod0_render_vertices=sub.get_number_verts(asset,0),uv_channels=sub.get_num_uv_channels(asset,0),
            simple_collision_count=sub.get_simple_collision_count(asset),convex_collision_count=sub.get_convex_collision_count(asset),collision_complexity=str(sub.get_collision_complexity(asset)))
        desc=asset.get_static_mesh_description(0)
        if desc:
            nv=desc.get_vertex_count();rec['source_vertex_count']=nv;rec['triangles_LOD0']=desc.get_triangle_count()
            if nv<=100000:
                low=[float('inf')]*3;high=[-float('inf')]*3;minimum=[];valid=0
                for n in range(nv):
                    vid=unreal.VertexID(n)
                    if not desc.is_vertex_valid(vid):continue
                    p=desc.get_vertex_position(vid);v=[p.x,p.y,p.z];valid+=1
                    low=[min(a,b) for a,b in zip(low,v)];high=[max(a,b) for a,b in zip(high,v)]
                # Sparse IDs cannot be assumed compact. Do not certify incomplete scans.
                if valid==nv:
                    rec['vertex_bounds_cm']={'min':low,'max':high};rec['vertex_scan']='complete_compact_ids'
                    rec['anchor_z_cm_candidate']=low[2]
                else:rec['vertex_scan']='sparse_ids_native_bounds_only'
            else:rec['vertex_scan']='large_mesh_native_bounds_recorded_exact_vertex_scan_deferred'
        rec['dependencies']=dependencies(job['path'].split('.')[0]);rec['status']='measured'
        rec['contact_status']='minimum_vertex_or_bounds_candidate_requires_role_contact_review';rec['facing_status']='not_inferred_from_bounds'
    except Exception:rec.update(status='measurement_error',error=traceback.format_exc())
    results[aid]=rec;count+=1
    if time.time()-start>30 or count>=80:break
after=dirty()
dest.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
state={'pid':os.getpid(),'world':world,'processed_this_call':count,'total':len(results),'queue_total':len(queue),'seconds':round(time.time()-start,3),'dirty_before':before,'dirty_after':after,'dirty_unchanged':before==after,'no_asset_or_map_save':True}
with (OUT/'NATIVE_PROGRESS.jsonl').open('a') as f:f.write(json.dumps(state)+'\n')
print(json.dumps(state))
assert before==after,'new_dirty_package_stop_and_preserve'
