"""Reconcile retained evidence per catalog identity; never infer readiness."""
import collections
import datetime
import bank_contracts as C
source=C.read(C.SOURCE)
activation=C.read(C.ROOT/'Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json')
lease=[s for s in (C.ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
lease_fields=dict(v.split('=',1) for v in lease.split() if '=' in v)
native_active=activation.get('native_authorized_now') is True and lease_fields.get('activation')=='MANAGER_ACTIVATED'
configs={j['asset_id']:j for j in C.read(C.HERE/'NATIVE_CONFIGURATIONS.json')['rows']}
native=C.read(C.PREP/'NATIVE_MEASUREMENTS.json')
imports={r['asset_id']:r for p in C.HERE.glob('IMPORTED_external_*.json') for r in [C.read(p)]}
manifest={r['asset_id']:r for r in C.read(C.PREP/'EXTERNAL_IMPORT_MANIFEST.json')}
materials=C.read(C.HERE/'NATIVE_INSTANCE_MATERIALS.json')
host={r['asset_id']:r for r in C.read(C.HERE/'HOST_DEPENDENT_ASSETS.json')['assets']}
validation=C.read(C.HERE/'NATIVE_VALIDATION.json')
coverage=[];categories=collections.defaultdict(collections.Counter)
for record in source['rows']:
    aid=record['asset_id'];rt=record['runtime'];imp=imports.get(aid);cfg=configs.get(aid)
    held=C.yes(rt['ExplicitHold']);enabled=C.yes(rt['RunEligible']);blockers=[]
    if held:blockers.append({'kind':'explicit_hold','owner':'Existing recorded release/rights authority','reasons':record['hold_reasons']})
    unresolved_speedtree_materials=bool(imp and aid.startswith('external.ST_') and not imp.get('source_material_repair_completed'))
    if unresolved_speedtree_materials:blockers.append({'kind':'speedtree_import_returned_default_material_bindings','owner':'Vegetation category + bank','details':'Native geometry is saved; source material/texture/SpeedTree shader reconstruction remains pending. Import dependency closure does not establish material appearance.'})
    if aid in host:blockers.append({'kind':'unsupported_consumer','owner':'Manager / existing system owner','interface':host[aid]['consumer']})
    if cfg and not cfg.get('automatic_ground_activation_allowed',True):blockers.append({'kind':'host_or_context_contract','owner':'Bank + existing consumer owner','details':cfg.get('placement_context_note',cfg.get('activation_blocker','Specific placement contract required'))})
    if cfg and cfg['style_context']!='mediterranean_urban':blockers.append({'kind':'current_area_style_mismatch','owner':'Bank / area content policy','preserved_style':cfg['style_context'],'area_style':'mediterranean_urban'})
    if not rt['ObjectPath']:blockers.append({'kind':'native_connection_pending','owner':'Bank','prepared_source_available':aid in manifest})
    if not enabled and aid in configs and not validation.get(aid,{}).get('ready'):blockers.append({'kind':'individual_role_contact_facing_material_review_pending','owner':'Bank','existing_measurement':aid in native,'native_materials_saved':record['object_path'] in materials['mesh_slots']})
    if record['recorded_category']=='Buildings/Modules':blockers.append({'kind':'architectural_role_and_assembly_capability_not_validated_by_this_assignment','owner':'Bank + building consumer owner'})
    if not enabled and not blockers:blockers.append({'kind':'individual_configuration_or_dependency_role_pending','owner':'Bank'})
    row={'asset_id':aid,'category':record['recorded_category'],'native_path':rt['ObjectPath'],
        'source_identity':record['source_package'],'recorded_native_class':record['recorded_native_class'],
        'prepared_external_source':aid in manifest,'native_measurement_retained':aid in native,
        'imported_and_named_saved_by_this_assignment':bool(imp and imp['saved']),
        'catalog_connected':bool(rt['ObjectPath']),
        'native_material_contract_saved':bool((imp and not unresolved_speedtree_materials) or record['object_path'] in materials['mesh_slots']),
        'individually_enabled':enabled,'newly_enabled_by_this_assignment':enabled and rt['DecisionId']==C.DECISION,
        'selection_weight':rt['SelectionWeight'],'family_id':rt['FamilyId'],'style_preserved':record['environment_style_set'],
        'rights_preserved':record['recorded_rights_state'],'explicit_hold_preserved':held,
        'role':rt['RequestRole'],'placement_rule':rt['PlacementRule'],
        'consumer_configuration_connected':enabled and aid not in host,
        'actually_generated_by_this_assignment':False,'fresh_process_reopened_by_this_assignment':False,
        'ordinary_generation_owner':'Manager activation pending; bank/system native generation operator',
        'blockers':blockers,'import_receipt':str(C.HERE/('IMPORTED_'+aid.replace('.','_')+'.json')) if imp else None}
    coverage.append(row)
    cat=categories[row['category']];cat['identities']+=1
    for key in ('prepared_external_source','native_measurement_retained','imported_and_named_saved_by_this_assignment','catalog_connected','native_material_contract_saved','individually_enabled','newly_enabled_by_this_assignment','explicit_hold_preserved'):
        cat[key]+=bool(row[key])
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
report={'schema':'environmentpipeline.full_bank_coverage.v1','utc':stamp,'source_catalog_sha256':C.sha(C.SOURCE),
    'scope':f'All {len(coverage)} current catalog identities; current state, not a readiness certificate',
    'identity_count':len(coverage),'categories':dict(categories),'rows':coverage}
C.write(C.HERE/'FULL_BANK_COVERAGE.json',report)
saved=set(materials['saved_paths'])
for imp in imports.values():saved.update(imp['saved_paths'])
r020=C.read(C.HERE/'R020_NATIVE_CONTENT_CONTRACTS.json') if (C.HERE/'R020_NATIVE_CONTENT_CONTRACTS.json').exists() else {}
saved.update(r020.get('saved_material_paths',[]));saved.add('/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4')
recovery_path=C.HERE/'DirtyOriginals_Transfer/PRESERVE_RESUME_RESULT.json'
recovery=C.read(recovery_path) if recovery_path.exists() else {}
recovery_saved=[r['path'] for r in recovery.get('saved',[])] if recovery.get('passed') else []
saved.update(recovery_saved)
result=C.read(C.HERE/'RESULT.json')
result.update(recorded_utc=stamp,status='ACTIVE_NATIVE_FULL_BANK_INTEGRATION_INCOMPLETE' if native_active else 'CATEGORY_WORK_ACTIVE_NATIVE_CONTENT_PAUSED',native_imported=len(imports),
    catalog_native_connections_added=sum(bool(r.get('native_bank_integration',{}).get('imported_and_saved')) for r in source['rows']),
    newly_enabled=sum(r['newly_enabled_by_this_assignment'] for r in coverage),total_enabled_rows=sum(r['individually_enabled'] for r in coverage),
    newly_saved_unreal_packages=sorted(saved),editor_used_by_this_chat=True,editor_pid=int(lease_fields['assigned_editor_PID']),
    editor_pid_basis='Recorded current lease; this file-only report does not independently verify the live OS process',
    native_content_authorized=native_active,editor_lease=lease,system_manager=activation['manager_thread_id'],
    retained_recovery_packages=recovery_saved,recovery_packages_are_catalog_models=False,
    catalog_source_sha256=C.sha(C.SOURCE),catalog_csv_sha256=C.sha(C.CSV),catalog_source_unchanged=False,runtime_csv_unchanged=False,
    blocker='Remaining bank identities/individual qualifications/consumer contracts are active work; original-area generation requires separate manager activation and then native save/reopen/regeneration.',
    coverage_receipt=str(C.HERE/'FULL_BANK_COVERAGE.json'),r020_native_jobs=len(r020.get('jobs',[])),
    original_native_meshes_preserved=materials['originals_unchanged'],native_materials_configured_meshes=len(materials['mesh_slots']),
    source_building_normal_correction_native_status='Not applied: direct native graph inspection showed different normal bindings; source Blender repair does not imply native repair is required.')
C.write(C.HERE/'RESULT.json',result)
lines=['Environmentpipeline bank integration - actual rolling status, '+stamp,'',
    f"Imported and named saved: {result['native_imported']} external identities.",
    f"New external native bindings saved in shared catalog/DataTable: {result['catalog_native_connections_added']}.",
    f"New individually enabled native models: {result['newly_enabled']}; total enabled rows: {result['total_enabled_rows']} (includes two materials).",
    f"Instancing material contracts saved for {len(materials['mesh_slots'])} measured native candidates; {len(saved)} distinct named Unreal packages saved in this assignment.",
    f"Retained recovery copies included in package count: {len(recovery_saved)}; not catalog additions or model activations.",
    'Generated original areas by this assignment: 0. Fresh-process reopen of the latest additions: not yet performed.',
    'All explicit holds, rights, source identities and original native assets remain preserved.',
    'External imported held records remain disabled. Import/connection does not mean visual or use acceptance.',
    f"Recorded editor lease PID{result['editor_pid']}; activation={lease_fields.get('activation')}; normal bank content authorization={native_active}. Ordinary generation separately gated.",
    '', 'Full-bank work remains active. Initial153 configurations/84 jobs are not the complete scope.',
    f'FULL_BANK_COVERAGE.json accounts every {len(coverage)} current identity, category, current stage and remaining owner/blocker.',
    'Remaining external prepared identities, native qualification, modular/hosted contracts and actual area verification remain open.',
    'R020_NATIVE_CONTENT_CONTRACTS.json: seven native meshes and three materials measured, dependency/material copies saved; functional use qualification and generator consumer remain pending.',
    '', 'Category coverage (identity / catalog connected / newly imported / active rows):']
for category,counts in sorted(categories.items()):lines.append(f"{category}: {counts['identities']} / {counts['catalog_connected']} / {counts['imported_and_named_saved_by_this_assignment']} / {counts['individually_enabled']}")
(C.HERE/'RESULT.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print({'identities':len(coverage),'imported':len(imports),'enabled_rows':result['total_enabled_rows'],'saved_packages':len(saved)})
