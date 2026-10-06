"""Refresh supplier handoff from retained queue, receipts and exact owner blockers."""
from pathlib import Path
from datetime import datetime,timezone
import collections
import intake as I

def finalize():
    q=I.read(I.HERE/'READY_JOBS.json');tx=I.read(I.HERE/'REGISTRATION_TRANSACTION.json')
    adopted=I.read(I.HERE/'ADOPTED_NATIVE_EVIDENCE.json')
    jobs=q['jobs'];byid={j['job_id']:j for j in jobs}
    contracts=[]
    for jid in adopted['job_ids']:
        j=byid[jid];r=I.read(I.HERE/'Receipts'/(jid+'.json'))
        contracts.append({'job_id':jid,'asset_id':j['asset_id'],'object_path':j['native_object_path'],
            'source_sha256':j['source_sha256'],'requested_role_candidate':j['requested_role_candidate'],
            'source_style':j['source_style'],'dimensions_cm':r['measurement']['dimensions_cm'],
            'bounds_cm':r['measurement']['bounds_cm'],'bottom_support_candidate':r['measurement']['bottom_support'],
            'material_slots':r['measurement']['material_slots'],'lod_count':r['measurement']['lod_count'],
            'measurement_receipt':str(I.HERE/'Receipts'/(jid+'.json')),
            'functional_opening_dimensions_cm':None,'functional_facing':None,'connectors':None,
            'automatic_use_qualified':False,'consumer_owner':'Root coordinates existing Iran building/source owner',
            'required_next_measurement':['clear aperture width/height (exclude jambs and wall)','exterior normal and local origin','left/right/base/top join planes',
                'separate door leaves and frame occupancy','closed roof/floor and complete facade coverage if whole building'],
            'important_limit':'AABB width is not clear loading aperture; source style is preserved; no survey dimensions or area suitability inferred.'})
    interfaces={
        'modular_building':{'owner':'root -> existing Iran building owner','fields':['asset_id','object_path','hash','family_id','role','native_scale','exterior_normal','base_plane_cm','story_height_cm','left_right_connector_frames','corner_inside_outside_role','opening_aperture_and_leaf_sweep','roof_closed_support_polygon','material_slots','allowed_use_and_style','source_opening_provenance','replacement_source_id'],
            'current_blocker':'r020 emits warehouse/station unresolved_dependencies unconditionally; content registry integration is not implemented there. Source surveys remain absent.',
            'dimensional_gap':'Measured compatible single-storey facade band needed for height strictly between 440 and 530 cm. Existing source policy forbids stretching arbitrary modules into this gap.',
            'existing_evidence':str(I.BANK/'R020_CONTENT_REQUEST.json')},
        'roof_wall_and_sign':{'owner':'root -> existing HDA building/attachment owner','fields':['source_area_id','source_osm_id','host_actor_and_component','host_surface_local_frame','outward_normal','support_polygon','mount_height_cm','contact_offset_cm','clearance_volume_cm','sign_readable_facing','owned_replacement_key'],
            'current_blocker':'mount_sign and roof_anchor reject unsupported_attachment_contract. Roof equipment cannot become generic ground props.'},
        'linear_boundary':{'owner':'root -> existing source/placement owner','fields':['source_polyline_id','source_polyline_points','segment_start_end_frames','segment_native_length_cm','post_corner_end_roles','slope_and_support_limits','gap_overlap_policy','entrance_exclusion_intervals','owned_replacement_key'],
            'current_blocker':'Fence/railing source-polyline consumer absent; generic roadside scatter does not satisfy it.'},
        'surface_material':{'owner':'root -> existing terrain/material owner; bank supplies native dependencies','fields':['material_object_path','slot_or_layer_role','texture_dependencies','native_uv_units','world_scale_cm','tiling','normal_encoding','runtime_virtual_texture_requirements','shader_compile_result','geographic_mask_layer','approved_style_context'],
            'current_blocker':'StarterContent standalone materials are candidates, not substitutions for the geographic multi-layer Landscape master; no profile/source mutation here.'},
        'vegetation':{'owner':'bank measurement and individual selection; root existing grass/tree consumer','fields':['root_or_stem_support_plane','native_bounds','card_or_geometry_LODs','season_species_style_evidence','material_wind_requirements','collision_clearance','family_weight_budget','geographic_vegetation_context'],
            'current_blocker':'GIS and CitySample candidates are not native migrated or climate/style qualified; named palms remain held.'}}
    I.write('ROLE_CONTRACTS.json',{'measured_candidates':contracts,'consumer_interfaces':interfaces,
        'not_a_new_content_request':'Existing candidates are unqualified or consumer-blocked; do not buy/download replacements based on these counts.',
        'true_missing_information':['source opening positions, sizes and orientation','architectural use/floor/roof survey for unknown source buildings','individual native style/appearance review'],
        'variety_policy':'Assess the 75 CitySample and 24 GIS candidates by truthful source family before declaring missing content; no automatic North American-to-Gaza/Iran relabel.'})
    next_ids=[j['job_id'] for j in jobs if j['status']=='ready_native_inspection' and j['source_id']=='Current' and j['requested_role_candidate'] in ('surface_material','modular_glazing','modular_corner')][:10]
    I.write('WRITER_BATCH.json',{'operator_thread_id':'01a1067c-5012-7550-b449-015b53c9d726','required_preflight':'native_bank_ops.preflight() under actual current PID lease',
        'call':'native_supplier.inspect(job_ids)','job_ids':next_ids,'queue_sha256':I.sha(I.HERE/'READY_JOBS.json'),
        'read_only_native':True,'no_save_cook_or_generation':True,'status':'prepared_not_dispatched_by_supplier',
        'coordinator':'root manager sequences this bounded batch when bank is at a safe boundary'})
    category=[]
    for role in sorted({j['requested_role_candidate'] for j in jobs}):
        cohort=[j for j in jobs if j['requested_role_candidate']==role]
        category.append({'role':role,'sourced_candidates':len(cohort),'native_present':sum(j['states']['native_present'] for j in cohort),
            'canonical_identity_present':sum(j['canonical_existing'] for j in cohort),
            'prior_native_measurements_adopted':sum(j['job_id'] in adopted['job_ids'] for j in cohort),
            'new_imports_by_supplier':0,'new_bank_registrations_applied':0,'new_selection_releases':0,
            'new_area_output':0,'new_named_persistence':0,'job_ids':[j['job_id'] for j in cohort]})
    I.write('CATEGORY_OUTCOMES.json',category)
    blockers=[
        {'id':'B001','owner':'root manager and existing bank writer','evidence':str(I.BANK/'apply_bank_configuration.py')+':18',
            'measured':'assert len(rows)==len(source[rows])==1223; current canonical count is 1223; additive prepared bundle is 1225.',
            'next_action':'Bank owner generalizes only fixed-count assumption under root sequencing, reviews actual source/CSV/table identities, then root activates exact held registration transaction and merges matching profile digest.',
            'blocking_jobs':tx['added_ids']},
        {'id':'B002','owner':'root manager sequences bank native inspection','evidence':str(I.ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'),
            'measured':'Last lease grants sole actual PID32508 to existing bank writer. Supplier has no editor lease; no native calls made.',
            'next_action':'Consume WRITER_BATCH.json through existing bank writer at a safe boundary. Write native per-job receipts in Receipts/. No new editor is required for existing assets.'},
        {'id':'B003','owner':'root and designated native migration writer','evidence':'Installed IAssetTools.h FMigrationOptions and MigratePackages signature; Epic migrating-assets documentation.',
            'measured':'MigratePackages accepts package names and a filesystem destination, without a per-package namespace-remap mapping. Source packages reference /Game/Prop, /Game/Building etc; required retained namespace is /Game/Project/Shared/ModelBank/Prepared/NativeUnreal/<SourceId>.',
            'next_action':'Review a supported native remap procedure preserving source originals and all dependency references. Do not rename/copy .uasset files into Prepared and assume references were rewritten. source_migration.export can capture closure and staged native packages only after reviewed sole-writer source activation.',
            'blocking_jobs':99,'native_source_closure_measured':False,'native_migration_executed':False,
            'additional_limit':'Staging export is not a live target project Content folder; migration API success there is unverified and fail-closed. No source project or startup hooks launched.'},
        {'id':'B004','owner':'root assigns existing consumer owners','evidence':str(I.HERE/'ROLE_CONTRACTS.json'),
            'measured':'Attachment/linear consumers and r020 industrial/station registry integration remain absent; full geometric measurements do not clear functional opening/style/survey gates.',
            'next_action':'Use exact existing source/consumer repair assignments and measured contracts; preserve holds and ordinary-generation gate.'}]
    I.write('BLOCKERS.json',blockers)
    header=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Source/Developer/AssetTools/Public/IAssetTools.h')
    log=I.ROOT.parent/'CitySample/Saved/Logs/CitySample.log'
    lines=log.read_text(encoding='utf-8',errors='replace').splitlines()
    engine_lines=[{'line':i+1,'text':line} for i,line in enumerate(lines) if 'LogInit: Engine Version:' in line or 'LogInit: Compatible Engine Version:' in line]
    I.write('API_AND_VERSION_EVIDENCE.json',{'installed_header':str(header),'header_sha256':I.sha(header),'migration_options_lines':[241,267],
        'native_api':'MigratePackages(PackageNamesToMigrate, DestinationPath, FMigrationOptions); dependencies not ignored; conflict SKIP',
        'engine_build':I.read(Path('C:/Program Files/Epic Games/UE_5.8/Engine/Build/Build.version')),
        'citysample_prior_session_log':str(log),'citysample_prior_session_version_lines':engine_lines,
        'interpretation':'CitySample previously opened in same 5.8.2 build; current exact mesh/dependency load compatibility remains unverified. Source GUID alone was not interpreted as engine version.',
        'official_sources':[
            {'url':'https://dev.epicgames.com/documentation/en-us/unreal-engine/migrating-assets-in-unreal-engine','finding':'Migrate includes referenced dependencies; normal destination is target project Content; missing dependencies can break assets.'},
            {'url':'https://dev.epicgames.com/documentation/unreal-engine/API/Developer/AssetTools/FMigrationOptions','finding':'Dependency and conflict behavior are explicit options.'},
            {'url':'https://dev.epicgames.com/documentation/en-us/unreal-engine/city-sample-project-unreal-engine-demonstration','finding':'CitySample is a complete sample with procedural systems; this supplier selects content only.'}]})
    handoff={'schema':'environmentpipeline.native_supply_handoff.v1','utc':datetime.now(timezone.utc).isoformat(),
        'status':'RETAINED_ADAPTER_AND_MEASURED_ADDITIVE_TRANSACTION_READY_NATIVE_OWNER_DEPENDENCIES_OPEN',
        'supplier_thread':'01a1075c-313d-7133-9bc5-580cb2681f9b','manager_thread':'01a106bc-2fde-7f23-9aa7-8ba413dc6245',
        'native_writer_thread':'01a1067c-5012-7550-b449-015b53c9d726','summary':q['summary'],
        'source_version_evidence':'CitySample prior log shows UE5.8.2 CL56702186; matches installed engine; current native compatibility unverified.',
        'first_concrete_supply':{'existing_measured_modules':7,'new_native_operations':0,'held_registration_ready_ids':tx['added_ids'],
            'new_assets_copied':0,'existing_bank_rows_preserved':tx['before_rows'],'prepared_rows':tx['after_rows'],
            'transaction_sha256':I.sha(I.HERE/'REGISTRATION_TRANSACTION.json'),'native_apply_done':False},
        'verification':I.read(I.HERE/'VERIFICATION.json'),
        'next_coordinator_actions':['Review two-row held transaction and fixed1223 consumer dependency B001.','Dispatch WRITER_BATCH.json via current bank writer.','Review source-session/migration namespace contract B003; never use a second editor.','Assign exact missing consumers from ROLE_CONTRACTS.json.'],
        'not_completed':['external dependency closure','external native migration and namespace remap','new native table registration','new selection qualification','consumer implementation','area generation/Lit review/named save/reopen/regeneration'],
        'ordinary_generation_authorized':False,'shared_files_modified':False,'native_originals_modified':False,
        'blockers_file':str(I.HERE/'BLOCKERS.json'),'artifacts':{p.name:I.sha(p) for p in sorted(I.HERE.glob('*')) if p.is_file() and p.name not in ('HANDOFF.json','RESULT.txt','ASSIGNMENT.json')}}
    I.write('HANDOFF.json',handoff)
    print(handoff['status'])

if __name__=='__main__':finalize()
