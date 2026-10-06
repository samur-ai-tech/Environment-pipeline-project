"""Publish immutable review material with exact commands; does not activate native work."""
from pathlib import Path
import json
from . import intake as I
from . import authority as A
from . import integrity as V
from . import native_supplier as N

def build():
    m,mp=A.manifest();a=m['authority'];q=I.read(I.HERE/'READY_JOBS.json');tx=I.read(I.HERE/'REGISTRATION_TRANSACTION.json')
    N.validate_transaction(tx['transaction_path'])
    verify=I.read(I.HERE/'VERIFICATION_V2.json');assert verify['status']=='passed' and verify['command_manifest_sha256']==I.sha(mp)
    byid={j['job_id']:j for j in q['jobs']}
    kinds={'modular_glazing':0,'modular_entrance':1,'surface_material':2,'modular_corner':3}
    candidates=[j for j in q['jobs'] if j['status']=='ready_native_inspection' and j['requested_role_candidate'] in kinds]
    candidates.sort(key=lambda j:(kinds[j['requested_role_candidate']], 'ModularBuildingSet' not in j['source_relative_file'],j['source_relative_file']))
    # Explicit intact storefront families, not window-decor panels or shutters.
    first=['store_front_windows_intact_4x1_b','store_front_windows_intact_4x1_c',
           'store_front_door_4x1_a','store_front_door_4x1_b','store_front_door_5x1_a']
    chosen=[]
    for name in first:
        matches=[j for j in candidates if j['source_relative_file']=='ModularBuildingSet/Meshes/Store_fronts/'+name+'.uasset']
        assert len(matches)==1,'exact_writer_candidate_missing:'+name
        chosen.extend(matches)
    chosen += [j for j in candidates if j['native_object_path'] and any(j['native_object_path'].endswith('.'+x) for x in ['M_Ground_Grass','M_Ground_Gravel','M_Rock_Sandstone'])]
    chosen += [j for j in candidates if j['job_id']=='NU_2f0c1660f6cd3784b4d3']
    batch={'schema':'environmentpipeline.native_supply_writer_batch.v2','authority':a,'command_manifest_path':str(mp),
        'command_manifest_sha256':I.sha(mp),'queue_sha256':I.sha(I.HERE/'READY_JOBS.json'),
        'job_ids':[j['job_id'] for j in chosen],'jobs':[{'job_id':j['job_id'],'object_path':j['native_object_path'],'source_sha256':j['source_sha256'],'role_candidate':j['requested_role_candidate']} for j in chosen],
        'activation_action':'inspect_native_supply_batch','activation_required':True,
        'native_execution_status':'NOT_RUN_PAUSED_DIRTY_ORIGINAL_RECOVERY','native_saves':False,
        'purpose':'Measure two intact storefront glazing and three entrance variants, three generic ground materials and the exact missing roof corner. Existing seven detailed measurements are reused, not repeated.'}
    I.write('WRITER_BATCH.json',batch)
    adopted=I.read(I.HERE/'ADOPTED_NATIVE_EVIDENCE.json')
    contracts=[]
    for jid in adopted['job_ids']:
        j=byid[jid];r=I.read(I.HERE/'Receipts'/(jid+'.json'))
        contracts.append({'job_id':jid,'asset_id':j['asset_id'],'object_path':j['native_object_path'],'source_sha256':j['source_sha256'],
            'source_style':j['source_style'],'dimensions_cm':r['measurement']['dimensions_cm'],'material_slots':r['measurement']['material_slots'],
            'bottom_support_candidate':r['measurement']['bottom_support'],'measurement_receipt':str(I.HERE/'Receipts'/(jid+'.json')),
            'measurement_receipt_sha256':I.sha(I.HERE/'Receipts'/(jid+'.json')),'native_measurement_reused':True,
            'native_contact_or_opening_qualification':False,'aperture_dimensions':None,'connector_frames':None,'facing':None,
            'immediate_action':'Additive held registration plus Buildings/Modules prepared intake' if jid in ['NU_03d5b98d84743f46a66b','NU_eb007c34606172659e7e'] else 'Already canonical: reuse existing exact identity and source; category owner reviews functional contract; no duplicate registration.',
            'remaining':'Actual aperture/host connectors, source openings, style/appearance and consumer integration; overall bounds do not grant loading/station suitability.'})
    I.write('CURRENT_NATIVE_DELIVERY.json',{'manager':a['manager_thread_id'],'measured_candidates':contracts,
        'ready_registration_transaction':tx['transaction_path'],'qualification_intake':I.read(I.HERE/'QUALIFICATION_INTAKE.json'),
        'native_assets_to_copy':0,'newly_released_assets':0,'ordinary_generation_authorized':False})
    checkpoint=I.ROOT/'Staging/BankIntegration_2026-10-04/MANAGEMENT_TRANSFER_CHECKPOINT.json'
    blockers=[{'id':'native_recovery','owner':a['operator_thread_id'],'evidence':str(checkpoint),'sha256':I.sha(checkpoint),
        'state':'Native operator is paused on three dirty vendor originals; supplier batches do not authorize recovery or saves.'},
        {'id':'registration_sequence','owner':a['manager_thread_id'],'evidence':tx['transaction_path'],
        'state':'Bank owner is repairing fixed count. This transaction appends exactly two held Buildings/Modules identities; root updates row_count/digests after native apply and bank merges PREPARED_INTAKE.'},
        {'id':'external_closure','owner':a['operator_thread_id'],'state':'No source-session native closure exists for the99 external jobs. Capture exact selected closure first; source_migration.capture entrypoint is implemented but not run.'},
        {'id':'external_intermediate_scope','owner':a['manager_thread_id'],'state':'Supported procedure is native Migrate into verified-absent original namespace in CLOSED target project, then native RenameAssets plus RenameReferencingSoftObjectPaths in target to exact Prepared namespace. Requires root review of exact temporary packages and retained redirectors; neither permission nor plan is fabricated. No source originals change.'},
        {'id':'external_native_proof','owner':a['operator_thread_id'],'state':'Migration/remap native APIs are installed/documented; current implementation has not run. Target dependency closure, pixels, materials, native dimensions, persistence and rights qualification remain required.'},
        {'id':'functional_consumers','owner':a['manager_thread_id'],'state':'Existing source/consumer owners must consume measured module/host/linear/semantic contracts; no new eligibility follows from registration.'}]
    I.write('BLOCKERS.json',blockers)
    runner=str(I.HERE/'sealed_run.py')
    prefix="import runpy; run = runpy.run_path("+repr(runner)+")[\"run\"]"
    commands={'validate_registration_offline':prefix+'; run('+repr(str(mp))+', "validate_transaction", '+repr({'transaction_path':tx['transaction_path']})+')',
        'native_inspection_after_activation':prefix+'; run('+repr(str(mp))+', "inspect", '+repr({'job_ids':batch['job_ids'],'activation_path':str(I.HERE/'INSPECTION_ACTIVATION.json')})+')',
        'native_registration_after_activation':prefix+'; run('+repr(str(mp))+', "apply_registration", '+repr({'transaction_path':tx['transaction_path'],'activation_path':str(I.HERE/'REGISTRATION_ACTIVATION.json')})+')'}
    I.write('EXACT_COMMANDS.json',{'commands':commands,'authority':a,'command_manifest_path':str(mp),'command_manifest_sha256':I.sha(mp),
        'activation_common_required_fields':{'authority':a,'manager_thread_id':a['manager_thread_id'],'operator_thread_id':a['operator_thread_id'],
            'pid':'actual sole PID assigned by root after clean recovery','command_manifest_sha256':I.sha(mp),'ordinary_generation_authorized':False},
        'registration_additional_fields':{'action':'apply_held_native_supply_registration','transaction_sha256':I.sha(tx['transaction_path']),
            'decision_sha256':tx['decision_sha256'],'row_count_consumers_reviewed':'root sets true after bank repair review'},
        'inspection_additional_fields':{'action':'inspect_native_supply_batch','job_ids':batch['job_ids'],'batch_sha256':I.sha(I.HERE/'WRITER_BATCH.json')},
        'templates_are_not_activations':True})
    api=I.ROOT/'../..' # exact header locations below; no engine/source edits.
    installed=Path('C:/Program Files/Epic Games/UE_5.8/Engine')
    headers=[installed/'Source/Developer/AssetTools/Public/IAssetTools.h',installed/'Source/Editor/UnrealEd/Public/FileHelpers.h',installed/'Source/Developer/AssetTools/Public/PackageMigrationContext.h']
    I.write('MIGRATION_API_REVIEW.json',{'installed_headers':{str(p):I.sha(p) for p in headers},
        'supported_calls':['AssetTools.migrate_packages','AssetTools.rename_assets(Array[AssetRenameData])','AssetTools.rename_referencing_soft_object_paths','EditorLoadingAndSavingUtils.save_packages(exact_named_packages, only_dirty=False)'],
        'why_not_advanced_copy':'Python begin_advanced_copy_packages exposes an interactive target operation; exact flattened mapping overload is C++ only. Migrate+exact native RenameAssets gives explicit target mapping while source project originals remain read-only.',
        'selected_procedure':'Only new migrated target copies, never existing target/source originals, enter native RenameAssets. Native soft references are rewritten, only exact packages and created redirectors are saved, and final closure may reference only prepared targets and Engine.',
        'unperformed_native_validation':True,'temporary_namespace_and_redirectors_require_exact_manager_activation':True,
        'source_map_generator_imports':False,'raw_uasset_rename':False,'new_plugin_or_engine_rebuild':False,
        'official_sources':['https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetTools?application_version=5.7','https://dev.epicgames.com/documentation/en-us/unreal-engine/migrating-assets-in-unreal-engine']})
    artifacts=['COMMAND_MANIFEST.json','WRITER_BATCH.json','CURRENT_NATIVE_DELIVERY.json','QUALIFICATION_INTAKE.json','REGISTRATION_TRANSACTION.json','EXACT_COMMANDS.json','BLOCKERS.json','MIGRATION_API_REVIEW.json','SEMANTIC_MATERIAL_SUPPLY.json','VERIFICATION_V2.json','READY_JOBS.json']
    inputs={name:I.sha(I.HERE/name) for name in artifacts}
    release=V.digest({'artifacts':inputs,'command_manifest_sha256':I.sha(mp)})
    folder=I.HERE/'READY'/release
    for name in artifacts:
        dest=folder/name;dest.parent.mkdir(parents=True,exist_ok=True);payload=(I.HERE/name).read_bytes()
        if dest.exists():assert dest.read_bytes()==payload
        else:
            with dest.open('xb') as f:f.write(payload)
    handoff={'schema':'environmentpipeline.native_supply_READY.v2','status':'READY_FOR_REVIEW_NATIVE_EXECUTION_PAUSED',
        'manager_thread_id':a['manager_thread_id'],'supplier_thread_id':a['supplier_thread_id'],'native_operator_thread_id':a['operator_thread_id'],
        'authority':a,'release_id':release,'artifact_sha256':inputs,'command_manifest_path':str(mp),'command_manifest_sha256':I.sha(mp),
        'transaction_path':tx['transaction_path'],'transaction_sha256':I.sha(tx['transaction_path']),
        'before_rows':tx['before_rows'],'after_rows':tx['after_rows'],'existing_rows_exactly_preserved':True,
        'added_records_category':'Buildings/Modules','prepared_intake_ready':True,'qualified_or_enabled':0,
        'checks_passed':verify['count'],'checks':verify['checks'],'native_operations_performed':0,'new_native_saves':0,
        'external_api_procedure_implemented_native_unverified':True,'external_native_closures_available':0,
        'writer_batch_jobs':len(chosen),'source_candidates':q['summary'],'semantic_owner_reply_file':str(I.HERE/'SEMANTIC_MATERIAL_SUPPLY.json'),
        'remaining_external_inputs':['clean recovered native boundary and exact successor activation','bank dynamic row-count review','native source dependency closure','reviewed temporary target namespace/redirector list','fresh target writer/native remap proof','per-asset qualification and actual consumer integration'],
        'ordinary_generation_authorized':False,'shared_files_written':False}
    A.immutable_json(folder/'HANDOFF.json',handoff)
    I.write('HANDOFF.json',{'status':handoff['status'],'immutable_ready_handoff':str(folder/'HANDOFF.json'),'sha256':I.sha(folder/'HANDOFF.json'),
        'manager_thread_id':a['manager_thread_id'],'transaction_path':tx['transaction_path'],'summary':f"Successor-bound integrity repair and supported native remap procedure implemented;{verify['count']} focused checks pass;2 held modules plus concrete prepared intake ready; no native execution."})
    print(folder/'HANDOFF.json')
    return handoff

if __name__=='__main__':build()
