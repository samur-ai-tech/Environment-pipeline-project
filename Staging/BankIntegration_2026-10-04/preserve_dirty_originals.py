"""PRESERVE_ONLY: exact loaded Plant07 buffers to retained recovery assets.

Prepared for manager review. No operation occurs on import. Original assets are
never saved, reverted, closed or reloaded. Separate activation is mandatory.
"""
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path
import unreal

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'DirtyOriginals_Transfer'
REQUEST=OUT/'PRESERVE_REQUEST.json'
ACTIVATION=ROOT/'Staging/ManagedSystemsAstra_2026-10-04/DirtyOriginals_PRESERVE_ACTIVATION.json'


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data): Path(path).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def package_file(pkg):
    assert pkg.startswith('/Game/')
    return ROOT/'Content'/(pkg.split('.')[0][6:]+'.uasset')
def obj_path(pkg): return pkg+'.'+pkg.rsplit('/',1)[1]
def fields(line): return dict(p.split('=',1) for p in line.split() if '=' in p)


def value(v):
    if v is None or isinstance(v,(str,int,float,bool)): return v
    if isinstance(v,unreal.Object): return v.get_path_name()
    if hasattr(v,'export_text'): return v.export_text()
    try: return [value(x) for x in v]
    except TypeError: return str(v)


def object_state(obj):
    if isinstance(obj,unreal.StaticMesh):
        names=['nanite_settings','static_materials','lod_group','light_map_resolution','light_map_coordinate_index']
        data={n:value(obj.get_editor_property(n)) for n in names}
        sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        data['lod_count']=sub.get_lod_count(obj)
        data['simple_collision_count']=sub.get_simple_collision_count(obj)
        data['convex_collision_count']=sub.get_convex_collision_count(obj)
        body=obj.get_editor_property('body_setup')
        data['collision_properties']={n:value(body.get_editor_property(n)) for n in ('agg_geom','collision_trace_flag','physics_type','default_instance')}
        data['lod_geometry']=[]
        for lod in range(data['lod_count']):
            desc=obj.get_static_mesh_description(lod)
            assert desc,('missing_source_description',obj.get_path_name(),lod)
            vertices=[];triangles=[];uvs=[]
            for i in range(desc.get_vertex_count()):
                vid=unreal.VertexID(i)
                assert desc.is_vertex_valid(vid),'sparse_vertex_ids'
                p=desc.get_vertex_position(vid);vertices.append([p.x,p.y,p.z])
            tid_value=0
            while len(triangles)<desc.get_triangle_count():
                tid=unreal.TriangleID(tid_value);tid_value+=1
                assert tid_value<desc.get_triangle_count()*4+1024,'unexpected_sparse_triangles'
                if not desc.is_triangle_valid(tid): continue
                corners=[]
                for k in range(3):
                    vi=desc.get_triangle_vertex_instance(tid,k)
                    corners.append(desc.get_vertex_instance_vertex(vi).get_editor_property('id_value'))
                    corner_uv=[]
                    for channel in range(sub.get_num_uv_channels(obj,lod)):
                        uv=desc.get_vertex_instance_uv(vi,channel);corner_uv.append([uv.x,uv.y])
                    uvs.append(corner_uv)
                triangles.append([corners,desc.get_triangle_polygon_group(tid).get_editor_property('id_value')])
            geometry={'vertices':vertices,'triangles':triangles,'corner_uv':uvs}
            data['lod_geometry'].append({'lod':lod,'vertices':len(vertices),'triangles':len(triangles),'uv_channels':sub.get_num_uv_channels(obj,lod),'geometry_sha256':hashlib.sha256(json.dumps(geometry,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()})
        return data
    assert isinstance(obj,unreal.MaterialInstanceConstant)
    return {n:value(obj.get_editor_property(n)) for n in ('parent','base_property_overrides','scalar_parameter_values','vector_parameter_values','texture_parameter_values')}


def normalized(data,replacements):
    text=json.dumps(data,sort_keys=True,allow_nan=False)
    for src,dst in replacements.items(): text=text.replace(src,dst)
    return text


def snapshot():
    api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
    wrappers=[unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,a) for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_class().get_name()=='HoudiniAssetActor']
    return {'pid':os.getpid(),'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name(),
        'dirty_content':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
        'dirty_maps':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
        'paused':api.is_asset_cooking_paused(),'auto_flags':[(w.is_auto_cooking_enabled(),w.is_auto_bake_enabled()) for w in wrappers],
        'autosave':unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
        'callbacks':{n:sum(getattr(r,k,None) is not None for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction')) for n in ('geocity_bank_workflow','geocity_roadbld_workflow')}}


def export_text(obj,dest):
    task=unreal.AssetExportTask()
    for name,v in {'object':obj,'filename':str(dest),'automated':True,'prompt':False,'exporter':unreal.ObjectExporterT3D()}.items(): task.set_editor_property(name,v)
    assert unreal.Exporter.run_asset_export_task(task),(obj.get_path_name(),list(task.errors))
    return {'path':str(dest),'sha256':sha(dest)}


def export_corner_attributes(obj,dest):
    """Compare all exported LOD corner attributes plus separate raw topology/UVs.

    FBX may omit zero-area triangles; object_state retains their raw geometry.
    Missing vertex-color layers are explicitly recorded, never called measured.
    """
    options=unreal.FbxExportOption()
    for name,v in {'ascii':True,'level_of_detail':True,'collision':True,'export_source_mesh':True,'vertex_color':True}.items(): options.set_editor_property(name,v)
    task=unreal.AssetExportTask()
    for name,v in {'object':obj,'filename':str(dest),'automated':True,'prompt':False,'exporter':unreal.StaticMeshExporterFBX(),'options':options}.items(): task.set_editor_property(name,v)
    assert unreal.Exporter.run_asset_export_task(task)
    lines=dest.read_text(encoding='utf-8-sig').splitlines()
    blocks=[];current=None;depth=0
    for line in lines:
        if current is None:
            if re.match(r'^\s*Geometry:\s*\d+,.*"Mesh"\s*\{\s*$',line): current=[];depth=1
        else:
            # FBX geometry property strings contain no braces in this exact asset.
            depth+=line.count('{')-line.count('}')
            if depth==0:
                blocks.append('\n'.join(current));current=None
            else: current.append(line.rstrip())
    assert current is None and len(blocks)==unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_lod_count(obj),'incomplete_exported_lods'
    assert all(all(n in b for n in ('LayerElementNormal:','LayerElementTangent:','LayerElementBinormal:','LayerElementUV:')) for b in blocks),'missing_exported_corner_attributes'
    return {'geometry_blocks_sha256':[hashlib.sha256(b.encode()).hexdigest() for b in blocks],
        'vertex_color_layers_present':['LayerElementColor:' in b for b in blocks],
        'lod_count':len(blocks),'exported_normals_tangents_binormals_uvs_compared':True}


def preserve():
    import geocity_runtime_guard as guard
    request=read(REQUEST);activation=read(ACTIVATION)
    assignment=read(HERE/'ASSIGNMENT.json')
    lease=[s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
    f=fields(lease)
    assert f['OWNER']=='CODEX_BANK_INTEGRATION' and f['activation']=='PRESERVE_ONLY'
    assert f['manager_thread_id']==activation['manager_thread_id']==assignment['system_owner']
    assert f['operator_thread_id']==activation['operator_thread_id']==assignment['thread']
    assert f['assigned_editor_PID']==str(os.getpid())==str(activation['pid'])==str(request['pid'])
    assert activation['approved'] is True and activation['scope']=='PRESERVE_ONLY'
    assert Path(__file__).resolve(strict=True)==Path(request['script_path']).resolve(strict=True),'unexpected_command_origin'
    assert activation['request_sha256']==sha(REQUEST) and activation['script_sha256']==sha(__file__)==request['script_sha256']
    assert activation['destinations']==request['destinations']
    assert activation.get('ordinary_generation_authorized') is False
    assert f.get('ordinary_generation_authorized')=='false'
    for path,expected in request['command_closure'].items(): assert sha(path)==expected,('command_source_changed',path)
    sources=guard.verify()
    before=snapshot()
    assert before['world']==request['world']==activation['world']==f['map']
    assert before['dirty_content']==sorted(request['source_packages']) and not before['dirty_maps']
    assert before['paused'] and not before['autosave'] and not any(before['callbacks'].values())
    assert all(not a and not b for a,b in before['auto_flags'])
    for path,expected in request['protected_disk_sha256'].items(): assert sha(path)==expected,('protected_file_changed',path)
    originals={p:unreal.find_object(None,obj_path(p)) for p in request['source_packages']}
    assert all(originals.values()),'source_buffer_missing'
    for dst in request['destinations']:
        assert not package_file(dst).exists() and not unreal.EditorAssetLibrary.does_asset_exist(dst) and unreal.find_object(None,obj_path(dst)) is None,('destination_already_exists',dst)
    # Complete read-only extraction occurs before any duplicate or setter.
    source_states={p:object_state(o) for p,o in originals.items()}
    for pkg,state in source_states.items():
        digest=hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        assert digest==request['source_state_sha256'][pkg],('source_buffer_changed_since_review',pkg)
    result={'schema':'environmentpipeline.dirty_original_preservation.v1','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'request_sha256':sha(REQUEST),'activation_sha256':sha(ACTIVATION),'lease':lease,'source_seal':sources,'before':before,'source_states':source_states,'created':[],'saved':[],'source_exports':{},'recovery_exports':{},'catalog_changed':False,'originals_reloaded':False,'qualified_for_selection':False,'fresh_process_reopen':False}
    receipt=OUT/'PRESERVE_RESULT.json'
    assert not receipt.exists(),'preservation_receipt_already_exists_no_blind_retry'
    write(receipt,result)
    copies={};mapping=dict(zip(request['source_packages'],request['destinations']))
    try:
        for src,obj in originals.items(): result['source_exports'][src]=export_text(obj,OUT/('PRESERVE_BEFORE_'+obj.get_name()+'.t3d'))
        source_texts={src:Path(item['path']).read_text(encoding='utf-8-sig') for src,item in result['source_exports'].items()}
        mesh_src=next(p for p,o in originals.items() if isinstance(o,unreal.StaticMesh))
        source_corner_attributes=export_corner_attributes(originals[mesh_src],OUT/'PRESERVE_SOURCE_ATTRIBUTES.fbx')
        result['source_corner_attributes']=source_corner_attributes
        def mutation_boundary(label):
            current=snapshot()
            assert set(request['source_packages']).issubset(set(current['dirty_content'])),'original_dirty_flag_cleared'
            assert set(current['dirty_content']).issubset(set(request['source_packages']+result['created'])),('unexpected_dirty_package',label)
            assert {k:v for k,v in current.items() if k!='dirty_content'}=={k:v for k,v in before.items() if k!='dirty_content'},('native_state_changed',label)
            for src,obj in originals.items():
                assert object_state(obj)==source_states[src],('original_buffer_changed',label,src)
                current_export=export_text(obj,OUT/('PRESERVE_CHECK_'+obj.get_name()+'.t3d'))
                assert Path(current_export['path']).read_text(encoding='utf-8-sig')==source_texts[src],('original_export_changed',label,src)
            assert export_corner_attributes(originals[mesh_src],OUT/'PRESERVE_CHECK_ATTRIBUTES.fbx')==source_corner_attributes,('original_corner_attributes_changed',label)
            for path,expected in request['protected_disk_sha256'].items(): assert sha(path)==expected,('protected_file_changed',label,path)
            for path,expected in request['command_closure'].items(): assert sha(path)==expected,('command_source_changed',label,path)
            guard.verify()
        mutation_boundary('before_first_duplicate')
        for src,dst in mapping.items():
            copies[src]=unreal.EditorAssetLibrary.duplicate_loaded_asset(originals[src],dst)
            assert copies[src] and copies[src].get_path_name()==obj_path(dst)
            result['created'].append(dst);write(receipt,result)
            mutation_boundary('after_duplicate_'+dst)
        for i,slot in enumerate(originals[mesh_src].static_materials):
            material_src=slot.material_interface.get_path_name().split('.')[0]
            assert material_src in copies,'unaccounted_mesh_material'
            copies[mesh_src].set_material(i,copies[material_src])
            mutation_boundary('after_material_setter_'+str(i))
        replacements={src:dst for src,dst in mapping.items()}
        for src,obj in copies.items():
            assert normalized(source_states[src],replacements)==normalized(object_state(obj),{}),('copy_properties_or_geometry_differ',src)
            result['recovery_exports'][mapping[src]]=export_text(obj,OUT/('RECOVERY_'+obj.get_name()+'.t3d'))
            expected_text=source_texts[src]
            for old,new in replacements.items(): expected_text=expected_text.replace(old,new)
            actual_text=Path(result['recovery_exports'][mapping[src]]['path']).read_text(encoding='utf-8-sig')
            assert expected_text==actual_text,('complete_t3d_property_or_subobject_export_differs',src)
        result['recovery_corner_attributes']=export_corner_attributes(copies[mesh_src],OUT/'RECOVERY_ATTRIBUTES.fbx')
        assert result['recovery_corner_attributes']==source_corner_attributes,'recovery_corner_attributes_differ'
        mutation_boundary('before_first_recovery_save')
        # Only exact retained recovery packages are saved. Originals remain dirty.
        for src,dst in mapping.items():
            assert unreal.EditorAssetLibrary.save_asset(dst,only_if_is_dirty=True),('recovery_save_failed',dst)
            assert package_file(dst).is_file()
            result['saved'].append({'path':dst,'sha256':sha(package_file(dst))});write(receipt,result)
            mutation_boundary('after_recovery_save_'+dst)
        result['saved_loaded_readback']={mapping[src]:object_state(unreal.load_asset(obj_path(mapping[src]))) for src in copies}
        for src in copies:
            assert normalized(source_states[src],replacements)==normalized(result['saved_loaded_readback'][mapping[src]],{})
        for src,obj in originals.items(): assert object_state(obj)==source_states[src],('original_buffer_changed',src)
        for path,expected in request['protected_disk_sha256'].items(): assert sha(path)==expected,('protected_file_changed',path)
        result['after']=snapshot()
        assert result['after']==before,'native_state_changed_outside_exact_recovery_copies'
        result['passed']=True
        result['binary_disk_reload_proven']=False
        result['complete_t3d_subobject_property_comparison']=True
        result['readback_limit']='Named native saves returned success, files exist and have hashes, and loaded properties/LOD geometry/UV/collision/material states agree. A later separately authorized reload or fresh-process reopen must prove disk deserialization before any original buffer discard.'
    except Exception as exc:
        result['passed']=False;result['error']=repr(exc);result['after']=snapshot()
        raise
    finally: write(receipt,result)
    return result


if __name__=='__main__': print(json.dumps(preserve()))
