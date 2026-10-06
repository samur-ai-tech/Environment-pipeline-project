"""Attach preserved FBX LOD parts to one permanent mesh using the native API."""
import re
import runpy
import types
import unreal
import bank_contracts as C
N=types.SimpleNamespace(**runpy.run_path(str(C.HERE/'native_bank_ops.py')))
B=runpy.run_path(str(C.HERE/'import_prepared.py'))
B['import_one'].__globals__['N']=N
E=unreal.EditorAssetLibrary
S=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

def run(aid):
    N.preflight()
    job=next(j for j in C.read(C.HERE/'EXTERNAL_IMPORT_QUEUE.json') if j['asset_id']==aid)
    source=C.read(job['original_source_receipt'])
    rec=next(r for r in C.read(C.HERE/'EXTERNAL_MATERIAL_RECIPES.json') if r['asset_id']==aid)
    dest=job['destination_package_proposed']
    assert not E.does_asset_exist(dest),'Existing target requires transaction reconciliation'
    raw_paths=E.list_assets(dest.rsplit('/',1)[0],recursive=True,include_folder=False)
    raw=[unreal.load_asset(p) for p in raw_paths]
    assert raw and all(isinstance(o,unreal.StaticMesh) and not C.package_file(o.get_path_name()).exists() for o in raw)
    expected=sorted([r for r in source['objects'] if re.fullmatch(r'render_lod\d+',r['geometry_role'])],key=lambda r:int(r['geometry_role'][10:]))
    assert len(raw)==len(expected)>1
    ordered=[]
    evidence=[]
    for row in expected:
        matches=[m for m in raw if B['norm'](m.get_name()).endswith(B['norm'](row['name']))]
        assert len(matches)==1,(aid,row['name'])
        mesh=matches[0]
        actual_triangles=mesh.get_static_mesh_description(0).get_triangle_count()
        equivalence=None
        if actual_triangles!=row['triangles']:
            proof=C.read(C.HERE/'IMPORT_GEOMETRY_EQUIVALENCE.json').get(aid,{})
            equivalence=next((r for r in proof.get('objects',[]) if r['source_object']==row['name']),None)
            assert equivalence and equivalence['passed'] and equivalence['native_path']==mesh.get_path_name(),('source_lod_triangle_mismatch',aid,row['name'],actual_triangles,row['triangles'])
            assert equivalence['native_triangles']==actual_triangles and equivalence['source_triangles']==row['triangles']
            assert row['triangles']-actual_triangles==equivalence['source_zero_area_triangles']-equivalence['native_zero_area_triangles']
        ordered.append(mesh)
        evidence.append({'source_object':row['name'],'source_triangles':row['triangles'],'native_triangles':actual_triangles,'zero_area_removal_proof':equivalence,'native_buffer':mesh.get_path_name()})
    assert len(set(m.get_path_name() for m in ordered))==len(raw)
    created={};used=[]
    materials=[B['material_for'](job,r,created,used) for r in rec['materials']]
    for mesh in ordered:
        for index,slot in enumerate(mesh.static_materials):
            name=B['norm'](str(slot.get_editor_property('imported_material_slot_name')))
            matches=[i for i,r in enumerate(rec['materials']) if name in {B['norm'](r['source_material']),B['norm'](r['prepared_material_name']),B['norm'](r['source_material']+'.001')}]
            assert len(matches)==1,('unresolved_lod_material',aid,name)
            mesh.set_material(index,materials[matches[0]])
    target=E.duplicate_asset(ordered[0].get_path_name(),dest)
    assert target
    for index,mesh in enumerate(ordered[1:],1):
        actual=S.set_lod_from_static_mesh(target,index,mesh,0,True)
        assert actual==index
        assert target.get_static_mesh_description(index).get_triangle_count()==evidence[index]['native_triangles']
    assert S.get_lod_count(target)==len(ordered)
    report=B['import_one'](aid)
    assert report['saved'] and C.package_file(dest).exists()
    # These exact buffers were created by this bank import in this PID and were
    # never saved. Their geometry now resides in the retained mesh's LODs.
    removed=[]
    for mesh in ordered:
        path=mesh.get_path_name()
        assert path.startswith(dest.rsplit('/',1)[0]+'/') and path.split('.')[0]!=dest
        assert not C.package_file(path).exists()
        assert not E.find_package_referencers_for_asset(path,False),('import_buffer_still_referenced',path)
        assert E.delete_asset(path)
        removed.append(path)
    report.update(native_lod_assembly={'source_lods':evidence,'lod_count':S.get_lod_count(target),'geometry_rebuilt':False,'native_api':'StaticMeshEditorSubsystem.set_lod_from_static_mesh','unsaved_import_buffers_removed':removed},native_sha256=C.sha(C.package_file(dest)))
    C.write(C.HERE/('IMPORTED_'+aid.replace('.','_')+'.json'),report)
    C.write(C.HERE/('LOD_ASSEMBLY_'+aid.replace('.','_')+'.json'),report['native_lod_assembly'])
    print({'asset_id':aid,'saved_lods':len(ordered),'removed_unsaved_own_buffers':len(removed)})
    return report
