"""Concrete, held PREPARED_BANK projection for the existing bank/category owners."""
from pathlib import Path
from . import intake as I
from . import native_supplier as N
from . import authority as A

def build():
    tx=I.read(I.HERE/'REGISTRATION_TRANSACTION.json');tx,before,after=N.validate_transaction(tx['transaction_path'])
    byid={r['asset_id']:r for r in after['rows']};rows=[]
    for aid in tx['added_ids']:
        r=byid[aid];n=I.read(r['native_supply']['measurement_receipt']);m=n['measurement'];rt=r['runtime']
        rows.append({'asset_id':aid,'catalog_row_name':r['catalog_row_name'],'name':rt['VariantId'],
            'category':r['recorded_category'],'family_id':rt['FamilyId'],'source_package':r['source_package'],
            'source_path':str(I.ROOT/'Content'/(r['object_path'].split('.')[0][6:]+'.uasset')),
            'record_kind':'asset_candidate','object_path':r['object_path'],'native_class_recorded':'StaticMesh',
            'runtime_enabled':False,'runtime_hold_preserved':True,'hold_reasons_preserved':r['hold_reasons'],
            'named_holds_preserved':[],'palm_hold_not_released':False,'rights_state_preserved':r['recorded_rights_state'],
            'canonical_qualified':False,'request_role':'','placement_rule':'','allowed_zones_current':'',
            'style_source_recorded':r['environment_style_set'],'style_context_current':rt['StyleSet'],
            'normal_scope_current':'none_pending_individual_review','new_normal_scope_requested':[],
            'newly_imported':False,'newly_connected':False,'newly_enabled':False,'new_area_generation':False,
            'native_preview_sources':[],'prepared_source':None,'current_package_sha256':r['asset_revision_sha256'],
            'package_exists':True,'package_revision_matches_runtime':True,'phase_status':'modular_native_measured_qualification_pending',
            'required_consumer_context':'modular_building_assembly',
            'native_measurement':{'status':'measured','asset_id':aid,'path':r['object_path'],'pid':n['pid'],
                'measurement_reused_from':n['measurement_reused_from'],'measurement_source_sha256':n['measurement_evidence_sha256'],
                'bounds_cm':m['bounds_cm'],'vertex_bounds_cm':m['bounds_cm'],'dimensions_cm':m['dimensions_cm'],
                'vertex_scan':'complete_compact_ids_from_existing_native_writer_receipt','source_vertex_count':m['source_vertices'],
                'triangles_LOD0':m['triangles'],'uv_channels':m['uv_channels'],'lod_count':m['lod_count'],
                'material_slots':m['material_slots'],'bottom_support_candidate':m['bottom_support'],
                'dependencies':{'packages':n['dependencies']['packages'],'unresolved_registry_packages':n['dependencies']['missing'],
                    'method':'existing_native_writer_hard_soft_closure_plus_current_dependency_file_hashes'},
                'contact_status':'functional_base_not_qualified','facing_status':'not_reviewed'},
            'blockers':['native_supply_qualification_pending','loading_aperture_not_measured','functional_facing_not_reviewed','source_style_stylized_town_not_area_qualified','source_openings_survey_not_available'],
            'native_supply_provenance':r['native_supply']})
    contract={'schema':'environmentpipeline.prepared_bank_additive_intake.v1','owner':tx['authority']['operator_thread_id'],
        'manager':tx['authority']['manager_thread_id'],'target_registry':str(I.PREP),'target_registry_before_sha256':I.sha(I.PREP),
        'source_transaction':tx['transaction_path'],'source_transaction_sha256':I.sha(tx['transaction_path']),
        'require_native_registration_applied_digest':tx['after_digest'],'merge_key':'asset_id','merge_rule':'append these exact two records only after registration APPLIED receipt; preserve every existing record; reject duplicate identity/name/casefold path; no eligibility or family release.',
        'rows':rows,'category_consumer':'Buildings/Modules','native_execution_performed_here':False,
        'qualification_next_steps':['bank/category owner consumes these exact provenance and measurement records','measure actual loading aperture, connector planes, support and exterior normal','Lit review source style and material appearance','resolve exact source-opening/assembly consumer contract with root','individual authorization required to change current qualification hold']}
    dest=Path(tx['transaction_path']).parent/'PREPARED_INTAKE.json';A.immutable_json(dest,contract)
    I.write('QUALIFICATION_INTAKE.json',{'path':str(dest),'sha256':I.sha(dest),'rows':len(rows),'category':'Buildings/Modules','applied':False})
    return contract

if __name__=='__main__':build()
