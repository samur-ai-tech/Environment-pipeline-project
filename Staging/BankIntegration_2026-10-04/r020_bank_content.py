"""Bank-owned content evidence for the existing r020 building consumer.

No source surveys, area profiles, HDA revisions or ordinary-export guards are
modified here. Native work requires the bank's actual-PID lease.
"""
import json
from pathlib import Path
import bank_contracts as C

HANDOFF=C.ROOT/'Staging/IranBuildingAdaptation_2026-10-04/HANDOFF.json'
MESHES={
    '/Game/AssetsvilleTown/Meshes/BuildingTilset/SM_wallGarageDoor_01.SM_wallGarageDoor_01':'warehouse_loading_opening_candidate',
    '/Game/AssetsvilleTown/Meshes/BuildingTilset/SM_wallGarageDoor_01_double.SM_wallGarageDoor_01_double':'warehouse_loading_opening_candidate',
    '/Game/ProceduralBuildingGenerator/Meshes/Entrance_Door/B08_Entrance_Var1.B08_Entrance_Var1':'station_entrance_candidate',
    '/Game/ProceduralBuildingGenerator/Meshes/Entrance_Door/B08_Sliding_Door_Var1.B08_Sliding_Door_Var1':'station_entrance_leaf_candidate',
    '/Game/ProceduralBuildingGenerator/Meshes/Entrance_Door/B94_Entrance_Var3.B94_Entrance_Var3':'station_entrance_candidate',
    '/Game/ModularBuildingSet/Meshes/Store_fronts/store_front_windows_intact_4x1_a.store_front_windows_intact_4x1_a':'station_glazing_candidate',
    '/Game/Warehouse_Building/StaticMeshes/SM_Warehouse_Building.SM_Warehouse_Building':'whole_warehouse_candidate',
}
MATERIALS={
    '/Game/AssetsvilleTown/Materials/MI_wallMetal_01_white.MI_wallMetal_01_white':'industrial_facade_candidate',
    '/Game/AssetsvilleTown/Materials/MI_GlassBasic.MI_GlassBasic':'station_glazing_material_candidate',
    '/Game/ModularCourtyard/Mats/MI_Glass_2.MI_Glass_2':'station_glazing_material_candidate',
}


def prepare():
    handoff=C.read(HANDOFF)
    records={r.get('object_path'):r for r in C.read(C.SOURCE)['rows'] if r.get('object_path')}
    jobs=[]
    for path,role in list(MESHES.items())+list(MATERIALS.items()):
        file=C.package_file(path);assert file.is_file(),file
        record=records.get(path)
        jobs.append({'native_path':path,'file_sha256':C.sha(file),'requested_role':role,
            'catalog_asset_id':record['asset_id'] if record else None,
            'catalog_explicit_hold':record['runtime']['ExplicitHold'] if record else None,
            'catalog_hold_reasons':record['hold_reasons'] if record else [],
            'source_style':record.get('environment_style_set') if record else None,
            'rights_state':record.get('recorded_rights_state') if record else 'not_inferred_from_installed_package',
            'native_evidence_complete':False,'use_qualified':False,
            'automatic_selection_eligible':False,'hold_clearance':False})
    C.write(C.HERE/'R020_CONTENT_REQUEST.json',{
        'schema':'environmentpipeline.bank_r020_content_request.v1','handoff':str(HANDOFF),'handoff_sha256':C.sha(HANDOFF),
        'source_revision_preserved':handoff['revision'],'jobs':jobs,
        'specific_missing_roles':handoff['specific_missing_roles'],
        'whole_use_contract_fields':['uses','native_evidence','storeys','actual_hold','floor_layout','facade','openings','roof','facing'],
        'source_blockers_unchanged':{
            'unknown_use':['122770773','122770780','122770783','122770790','905869523'],
            'station_source_openings':['905869511'],
            'warehouse_source_openings':['122770767','122770768','122770771','122770774','122770778'],
            'retained_source_height_and_storeys':'absent; model dimensions do not establish surveyed source heights',
            'excluded_warehouse':'122770784 remains excluded'},
        'consumer_interface_limit':{
            'whole_building_consumer':'building_rules_json.whole_use_contracts[exact ObjectPath]',
            'assembly_content_consumer':'r020 assembly_layout currently emits the warehouse/station unresolved_dependencies unconditionally by use; no material/module qualification registry is consumed there yet.',
            'required_owner_work':'The r020 building owner must consume measured bank evidence and source-opening provenance in a later reviewed revision; importing or copying assets cannot clear the current export guards.',
            'ordinary_export':'blocked; no HDA promotion, guard bypass or partial Bake'},
        'status':'candidate_paths_saved_native_contracts_pending'})
    print(json.dumps({'r020_candidate_paths':len(jobs),'native_work':False}))


def native_contracts():
    import os
    import unreal
    import runpy
    import types
    N=types.SimpleNamespace(**runpy.run_path(str(C.HERE/'native_bank_ops.py')))
    before=N.preflight();request=C.read(C.HERE/'R020_CONTENT_REQUEST.json')
    created={};copies={};evidence=[]
    for job in request['jobs']:
        path=job['native_path'];assert C.sha(C.package_file(path))==job['file_sha256'],path
        asset=unreal.load_asset(path);assert asset,path
        row=dict(job,pid=os.getpid(),native_class=asset.get_class().get_name())
        row['original_dependencies']=N.dependency_closure(path.split('.')[0])
        if path in MESHES:
            row['measurement']=N.measure(asset)
            sources=[s.material_interface for s in asset.static_materials]
            assert sources and all(sources),('empty_material_slots',path)
            row['compatible_material_slots']=[N.compatible_copy(m,created,copies).get_path_name() for m in sources]
            row['role_review']={'actual_opening_clear_width_height':None,'exterior_facing':None,
                'architectural_floor_count':None,'visual_evidence':None,
                'reason':'Full dimensions are measured; functional opening, facing, floors and intended-use appearance are not inferred from the asset name or AABB.'}
        else:
            copy=N.compatible_copy(asset,created,copies)
            row['compatible_material_path']=copy.get_path_name()
            row['role_review']={'material_appearance_checked':False,'uv_scale_and_tiling_verified':False,
                'reason':'Native material/dependency connection alone does not establish industrial or station use.'}
        evidence.append(row)
    for path in sorted(created):assert N.E.save_asset(path,only_if_is_dirty=True),path
    for row in evidence:
        targets=row.get('compatible_material_slots') or [row['compatible_material_path']]
        row['compatible_material_dependencies']={path:N.dependency_closure(path.split('.')[0]) for path in targets}
        row['compatible_dependency_closure_complete']=all(not c['missing'] for c in row['compatible_material_dependencies'].values())
        assert C.sha(C.package_file(row['native_path']))==row['file_sha256'],row['native_path']
    C.write(C.HERE/'R020_NATIVE_CONTENT_CONTRACTS.json',{'schema':'environmentpipeline.bank_r020_native_content_evidence.v1',
        'request_sha256':C.sha(C.HERE/'R020_CONTENT_REQUEST.json'),'jobs':evidence,
        'saved_material_paths':sorted(created),'native_originals_unchanged':True,
        'source_survey_blockers_unchanged':request['source_blockers_unchanged'],
        'whole_use_contracts':{},'ordinary_export_complete':False,'native_area_generated':False})
    assert N.dirty()==before['dirty'],N.dirty()
    return {'native_jobs':len(evidence),'saved_material_paths':sorted(created),'qualified_for_automatic_selection':0}


if __name__=='__main__': prepare()
