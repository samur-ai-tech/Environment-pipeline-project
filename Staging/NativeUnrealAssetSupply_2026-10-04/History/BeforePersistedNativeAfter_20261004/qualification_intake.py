"""Generic immutable measurement intake. Shared writes belong to the bank integrator.

apply_prepared is a pure CAS callback: it returns the exact additive document;
it never writes PREPARED_BANK, configurations, canonical catalog or Content.
"""
import copy
import csv
import math
from pathlib import Path
from . import intake as I
from . import authority as A
from . import integrity as V
from . import native_supplier as N
from . import post_remap as P

ROLES={
    'whole_building':('Buildings/Whole','whole_building_footprint_height_terrain_fit'),
    'whole_warehouse':('Buildings/Whole','whole_building_footprint_height_terrain_fit'),
    'small_prop':('SmallProps','ground_prop_contact_clearance'),
    'street_prop':('StreetProps','roadside_ground_contact_clearance'),
    'street_pole':('StreetProps','roadside_pole_contact_clearance'),
    'tree':('Vegetation','vegetation_ground_fit'),
    'understory':('Vegetation','vegetation_ground_fit'),
    'vegetation':('Vegetation','vegetation_ground_fit'),
    'shrub':('Vegetation','vegetation_ground_fit'),
    'roof_hosted_utility':('Utility/RooftopProps','roof_host_attachment'),
    'wall_hosted_utility':('Utility/RooftopProps','wall_host_attachment'),
    'sign_hosted':('Signs','sign_host_attachment_or_measured_standalone_pole'),
    'linear_boundary':('StreetProps','linear_boundary_alignment'),
    'surface_material':('Materials/Ground','geographic_surface_material_layer'),
    'warehouse_loading_opening':('Buildings/Modules','modular_building_assembly'),
    **{r:('Buildings/Modules','modular_building_assembly') for r in
       ('modular_straight','modular_corner','modular_entrance','modular_glazing','modular_roof')},
}


def truth(value):
    return str(value).lower() in ('true','1')


def validate_prepared(doc):
    assert isinstance(doc,dict) and isinstance(doc['rows'],list)
    for key in ('asset_id','catalog_row_name','object_path'):
        values=[str(r.get(key,'')).casefold() for r in doc['rows'] if r.get(key)]
        assert len(values)==len(set(values)),'duplicate_prepared_'+key
    assert all(r.get('asset_id') for r in doc['rows'])


def check_measurement(job,receipt):
    path=job['native_object_path'];revision=job.get('native_sha256',job['source_sha256'])
    assert receipt['status']=='native_measured' and receipt['asset_id']==job['asset_id'] and receipt['job_id']==job['job_id']
    assert receipt['native_object_path']==receipt['resolved_object_path']==path,'measurement_native_path_mismatch'
    assert receipt['source_sha256']==job['source_sha256']
    assert receipt.get('native_sha256',receipt['source_sha256'])==revision,'measurement_native_revision_mismatch'
    assert receipt['pid']>0
    if receipt.get('measurement_reused_from'):
        assert receipt['new_native_call_performed'] is False and receipt['mesh_bytes_reverified'] is True
    else:assert receipt['dirty_unchanged'] is True
    assert not receipt['dependencies']['missing'] and receipt['materials_present'] is True
    deps=receipt['dependency_files']
    assert {d['package'] for d in deps}==set(receipt['dependencies']['packages'])
    assert all(d['state']=='files_hashed' and d['files'] for d in deps),'unresolved_dependency_files'
    assert len(deps)==len({d['package'].casefold() for d in deps})
    if receipt['native_class']=='StaticMesh':
        m=receipt['measurement'];bounds=m['bounds_cm'];dimensions=m['dimensions_cm']
        assert len(bounds['min'])==len(bounds['max'])==len(dimensions)==3
        for lo,hi,size in zip(bounds['min'],bounds['max'],dimensions):
            assert all(isinstance(v,(int,float)) and math.isfinite(v) for v in (lo,hi,size))
            assert hi>=lo and abs((hi-lo)-size)<=0.01,'invalid_measured_dimensions'
        assert m['source_vertices']>0 and m['triangles']>0 and m['lod_count']>0 and m['material_slots']
        assert all(slot.get('path') for slot in m['material_slots'])
    else:
        assert receipt['native_class'] in ('Material','MaterialInstanceConstant')
        assert job['requested_role_candidate']=='surface_material'
        assert isinstance(receipt['used_textures'],list)
    if job['operation']=='inspect_remapped_target':
        assert receipt['queue_sha256'] and receipt['queue_path'] and receipt['native_sha256']==revision
    return True


def verify_measurement_files(job,receipt):
    assert I.sha(job['source_file'])==job['source_sha256'],'original_source_revision_changed'
    native=I.ROOT/'Content'/(job['native_object_path'].split('.')[0][6:]+'.uasset')
    assert I.sha(native)==job.get('native_sha256',job['source_sha256']),'native_target_revision_changed'
    for dep in receipt['dependency_files']:
        for f in dep['files']:assert I.sha(f['file'])==f['sha256'],'measurement_dependency_changed'
    if receipt.get('measurement_reused_from'):
        assert I.sha(receipt['measurement_reused_from'])==receipt['measurement_evidence_sha256'],'adopted_evidence_changed'


def project(job,receipt,canonical,evidence):
    """Project exact evidence; absent contact/facing/aperture stays unknown."""
    check_measurement(job,receipt)
    role=job['requested_role_candidate'];assert role in ROLES,'unsupported_role_requires_owner_contract'
    category,context=ROLES[role];rt=canonical['runtime'];path=job['native_object_path'];revision=job.get('native_sha256',job['source_sha256'])
    assert (canonical['asset_id'],canonical['catalog_row_name'],rt['ObjectPath'])==(job['asset_id'],job['catalog_row_name'],path)
    canonical_revision=rt['AssetRevision'].lower()
    assert canonical_revision==revision.lower() or (not canonical_revision and not truth(rt.get('RunEligible'))),'canonical_revision_mismatch'
    if job['canonical_existing']:
        assert V.digest(canonical)==job['queued_canonical_record_sha256'],'queued_canonical_record_changed'
    mesh=receipt['native_class']=='StaticMesh';m=receipt.get('measurement',{})
    native={'status':'measured','asset_id':job['asset_id'],'path':path,'pid':receipt['pid'],
        'package_sha256_at_queue':revision,'measurement_source':evidence['path'],'measurement_source_sha256':evidence['sha256'],
        'dependencies':{'packages':receipt['dependencies']['packages'],'unresolved_registry_packages':receipt['dependencies']['missing'],
            'method':'native_hard_soft_closure_and_exact_current_files'},'dependency_files':copy.deepcopy(receipt['dependency_files']),
        'source_scale':receipt.get('source_scale'),'native_up_axis':receipt.get('native_up_axis'),
        'pivot_local_cm':receipt.get('pivot_local_cm'),'pivot_contact_offset':receipt.get('pivot_contact_offset'),
        'targeted_measurement':copy.deepcopy(receipt.get('targeted_measurement')),
        'measurement_request_path':receipt.get('measurement_request_path'),'measurement_request_sha256':receipt.get('measurement_request_sha256'),
        'contact_status':'not_functionally_qualified','facing_status':'not_functionally_qualified'}
    if mesh:
        native.update(bounds_cm=m['bounds_cm'],vertex_bounds_cm=m['bounds_cm'],dimensions_cm=m['dimensions_cm'],
            vertex_scan='complete_compact_ids_native_writer',source_vertex_count=m['source_vertices'],triangles_LOD0=m['triangles'],
            uv_channels=m['uv_channels'],lod_count=m['lod_count'],material_slots=m['material_slots'],
            bottom_support_candidate=m.get('bottom_support'),simple_collision_count=m.get('simple_collision_count'),
            convex_collision_count=m.get('convex_collision_count'))
    else:native.update(used_textures=receipt['used_textures'],material_slots=[],dimensions_cm=None,bounds_cm=None)
    contract={'candidate_role':role,'role_evidence':job.get('role_basis'),'consumer_context':context,
        'canonical_request_role':canonical.get('request_role'),'canonical_placement_rule':canonical.get('placement_rule'),
        'canonical_contexts':copy.deepcopy(canonical.get('allowed_contexts',[])),
        'canonical_spacing_cm':canonical.get('min_spacing_cm'),'canonical_family_id':rt.get('FamilyId'),
        'bounds_cm':m.get('bounds_cm'),'dimensions_cm':m.get('dimensions_cm'),
        'native_up_axis':receipt.get('native_up_axis'),'authored_pivot_local_cm':receipt.get('pivot_local_cm'),
        'functional_contact':None,'functional_anchor':None,'functional_facing':None,'connector_frames':None,'aperture_dimensions_cm':None,
        'material_slots':m.get('material_slots',[]),'used_textures':receipt.get('used_textures'),
        'material_graph_contract':receipt.get('material_graph_contract') or receipt.get('targeted_measurement',{}).get('material_graph'),
        'support_candidate':m.get('bottom_support'),'functional_contract_verified':False,
        'readiness':'requires_category_owner_qualification','not_inferred_from_AABB_or_filename':True}
    row={'asset_id':canonical['asset_id'],'catalog_row_name':canonical['catalog_row_name'],'object_path':path,
        'name':rt['VariantId'],'category':canonical.get('recorded_category') or category,
        'candidate_category':category,'family_id':rt.get('FamilyId'),'source_package':canonical.get('source_package'),
        'source_path':str(I.ROOT/'Content'/(path.split('.')[0][6:]+'.uasset')),'record_kind':'asset_candidate',
        'native_class_recorded':receipt['native_class'],'current_package_sha256':revision,'package_exists':True,
        'package_revision_matches_runtime':canonical_revision==revision.lower(),'canonical_revision_binding_pending':not bool(canonical_revision),'runtime_enabled':truth(rt.get('RunEligible')),
        'runtime_hold_preserved':truth(rt.get('ExplicitHold')),'hold_reasons_preserved':copy.deepcopy(canonical.get('hold_reasons',[])),
        'named_holds_preserved':copy.deepcopy(canonical.get('named_holds_preserved',[])),
        'rights_state_preserved':canonical.get('recorded_rights_state'),'canonical_qualified':canonical.get('canonical_qualified',False),
        'request_role':canonical.get('request_role',''),'placement_rule':canonical.get('placement_rule',''),
        'allowed_zones_current':rt.get('AllowedZones',''),'style_source_recorded':canonical.get('environment_style_set'),
        'style_context_current':rt.get('StyleSet'),'normal_scope_current':canonical.get('allowed_area_policy'),
        'new_normal_scope_requested':[],'newly_imported':False,'newly_connected':False,'newly_enabled':False,'new_area_generation':False,
        'native_preview_sources':[],'prepared_source':None,'phase_status':'native_measured_qualification_pending',
        'required_consumer_context':context,'native_measurement':native,'placement_contract_candidate':contract,
        'blockers':(['canonical_revision_binding_pending'] if not canonical_revision else [])+['individual_functional_contract_review_pending','style_material_appearance_review_pending'],
        'native_supply_provenance':{'canonical_record_sha256':V.digest(canonical),'job_id':job['job_id'],'receipt':evidence,'source_original_file':job['source_file'],
            'source_original_sha256':job['source_sha256'],'source_style':job.get('source_style'),'source_rights':job.get('rights_state'),
            'native_sha256':revision,'post_remap_receipt_path':job.get('post_remap_receipt_path'),
            'post_remap_receipt_sha256':job.get('post_remap_receipt_sha256')}}
    if row['category']=='NativeSupply/PendingQualification':row['category']=category
    return row


def additive_merge(before,rows,packet_id):
    validate_prepared(before);validate_prepared({'rows':rows})
    out=copy.deepcopy(before);byid={r['asset_id']:r for r in out['rows']}
    for incoming in rows:
        aid=incoming['asset_id']
        if aid not in byid:
            added=copy.deepcopy(incoming);out['rows'].append(added);byid[aid]=added
        else:
            old=byid[aid]
            assert old['catalog_row_name']==incoming['catalog_row_name'] and old.get('object_path')==incoming['object_path'],'prepared_identity_binding_conflict'
            evidence=old.setdefault('native_supply_intakes',{})
            assert packet_id not in evidence or evidence[packet_id]==incoming,'prepared_intake_id_conflict'
            evidence[packet_id]=copy.deepcopy(incoming)
            # Preserve every prior field, including richer existing measurements and policy.
            if 'native_measurement' not in old:old['native_measurement']=copy.deepcopy(incoming['native_measurement'])
    validate_prepared(out)
    return out


def prepare(job_ids,queue_path=None,registration_transaction_path=None):
    m,mp=A.manifest();queue,qp=P.load_queue(queue_path);jobs={j['job_id']:j for j in queue['jobs']}
    assert job_ids and len(job_ids)==len(set(job_ids))
    tx=None
    if registration_transaction_path:
        tx,_,canonical=N.validate_transaction(registration_transaction_path)
        source_path=Path(tx['bundle_source_path']);csv_path=Path(tx['bundle_csv_path'])
    else:
        source_path=I.CATALOG;csv_path=N.CSV;canonical=I.read(source_path)
    V.validate_records(canonical['rows']);C=N._contracts(mp)
    with csv_path.open(encoding='utf-8-sig',newline='') as f:csv_rows=list(csv.DictReader(f))
    assert C.typed_rows(csv_rows)==C.typed_rows([r['runtime'] for r in canonical['rows']])
    byid={r['asset_id']:r for r in canonical['rows']};rows=[];evidences=[]
    source_hash=I.sha(source_path);csv_hash=I.sha(csv_path);prepared_hash=I.sha(I.PREP);before=I.read(I.PREP)
    for jid in job_ids:
        job=jobs[jid];assert job['status']!='blocked_identity_ambiguity'
        receipt=I.read(I.HERE/'Receipts'/(jid+'.json'));check_measurement(job,receipt);verify_measurement_files(job,receipt)
        if queue_path is not None:assert receipt['queue_sha256']==I.sha(qp)
        ep=I.HERE/'MeasurementEvidence'/V.digest(receipt)/'RECEIPT.json';A.immutable_json(ep,receipt)
        evidence={'path':str(ep),'sha256':I.sha(ep)};evidences.append(evidence)
        rows.append(project(job,receipt,byid[job['asset_id']],evidence))
    packet={'schema':'environmentpipeline.generic_prepared_intake.v2','authority':m['authority'],
        'command_manifest_path':str(mp),'command_manifest_sha256':I.sha(mp),'queue_path':str(qp),'queue_sha256':I.sha(qp),
        'job_ids':job_ids,'rows':rows,'measurement_evidence':evidences,'canonical_source_expected_sha256':source_hash,
        'canonical_csv_expected_sha256':csv_hash,'canonical_digest':C.digest(csv_rows),'canonical_rows':len(csv_rows),
        'registration_transaction_path':str(registration_transaction_path) if tx else None,
        'registration_transaction_sha256':I.sha(registration_transaction_path) if tx else None,
        'prepared_target':str(I.PREP),'prepared_before_sha256':prepared_hash,
        'selection_release_authorized':False,'ordinary_generation_authorized':False,'native_execution_performed_here':False}
    key=V.digest(packet);folder=I.HERE/'PreparedIntakes'/key
    after=additive_merge(before,rows,key)
    assert I.sha(I.PREP)==prepared_hash and I.sha(source_path)==source_hash and I.sha(csv_path)==csv_hash,'baseline_changed_during_preparation'
    A.immutable_json(folder/'PREPARED_INTAKE.json',packet);A.immutable_json(folder/'BEFORE.json',before);A.immutable_json(folder/'AFTER.json',after)
    transaction={'schema':'environmentpipeline.prepared_intake_CAS.v1','intake_path':str(folder/'PREPARED_INTAKE.json'),
        'intake_sha256':I.sha(folder/'PREPARED_INTAKE.json'),'before_path':str(folder/'BEFORE.json'),'before_sha256':I.sha(folder/'BEFORE.json'),
        'after_path':str(folder/'AFTER.json'),'after_sha256':I.sha(folder/'AFTER.json'),'packet_id':key,
        'before_rows':len(before['rows']),'after_rows':len(after['rows']),
        'callback':'qualification_intake.apply_prepared(transaction_path, native_rows, prepared_document)',
        'write_owner':m['authority']['operator_thread_id'],'callback_performs_shared_writes':False}
    dest=folder/'TRANSACTION.json';A.immutable_json(dest,transaction)
    I.write('QUALIFICATION_INTAKE.json',{'path':str(dest),'sha256':I.sha(dest),'intake_path':transaction['intake_path'],
        'intake_sha256':transaction['intake_sha256'],'rows':len(rows),'categories':sorted({r['category'] for r in rows}),'applied':False})
    return transaction


def validate(transaction_path):
    p=Path(transaction_path).resolve();assert p.is_relative_to(I.HERE/'PreparedIntakes')
    tx=I.read(p)
    for k in ('intake','before','after'):
        assert Path(tx[k+'_path']).resolve().parent==p.parent and I.sha(tx[k+'_path'])==tx[k+'_sha256']
    packet=I.read(tx['intake_path']);assert V.digest(packet)==tx['packet_id']==p.parent.name
    assert packet['authority']==A.authority() and packet['selection_release_authorized'] is False
    assert I.sha(packet['command_manifest_path'])==packet['command_manifest_sha256'];A.manifest(packet['command_manifest_path'])
    queue,qp=P.load_queue(packet['queue_path']);assert I.sha(qp)==packet['queue_sha256']
    jobs={j['job_id']:j for j in queue['jobs']}
    assert len(packet['job_ids'])==len(packet['rows'])==len(packet['measurement_evidence'])
    for jid,row,evidence in zip(packet['job_ids'],packet['rows'],packet['measurement_evidence']):
        assert I.sha(evidence['path'])==evidence['sha256'];receipt=I.read(evidence['path'])
        check_measurement(jobs[jid],receipt);verify_measurement_files(jobs[jid],receipt)
        assert row['asset_id']==jobs[jid]['asset_id']
    before=I.read(tx['before_path']);after=I.read(tx['after_path'])
    assert after==additive_merge(before,packet['rows'],tx['packet_id'])
    return tx,packet,after


def cas_state(packet,source_sha,csv_sha,prepared_sha,native_digest,native_count,prepared_document,before):
    assert source_sha==packet['canonical_source_expected_sha256'],'stale_current_canonical_source'
    assert csv_sha==packet['canonical_csv_expected_sha256'],'stale_current_canonical_csv'
    assert prepared_sha==packet['prepared_before_sha256'],'stale_current_prepared_registry'
    assert prepared_document==before,'prepared_document_mismatch'
    assert native_count==packet['canonical_rows'] and native_digest==packet['canonical_digest'],'native_catalog_differs'
    return True


def apply_prepared(transaction_path,native_rows,prepared_document):
    """Bank-owned integration calls this before its own atomic write, under its lease.

    Exact disk CAS + actual DataTable rows + complete deterministic projection.
    Returns a document only. Bank must keep its one-writer lease and recheck
    expected hashes immediately before commit, then publish its applied receipt.
    """
    tx,packet,after=validate(transaction_path)
    C=N._contracts(packet['command_manifest_path'])
    cas_state(packet,I.sha(I.CATALOG),I.sha(N.CSV),I.sha(I.PREP),C.digest(native_rows),len(native_rows),prepared_document,I.read(tx['before_path']))
    assert prepared_document==I.read(I.PREP),'prepared_document_mismatch'
    source=I.read(I.CATALOG);V.validate_records(source['rows']);C=N._contracts(packet['command_manifest_path'])
    assert C.typed_rows(native_rows)==C.typed_rows([r['runtime'] for r in source['rows']]),'native_catalog_differs'
    assert len(native_rows)==packet['canonical_rows'] and C.digest(native_rows)==packet['canonical_digest']
    if packet['registration_transaction_path']:
        reg=I.read(packet['registration_transaction_path'])
        assert I.sha(packet['registration_transaction_path'])==packet['registration_transaction_sha256']
        applied=I.read(Path(packet['registration_transaction_path']).parent/'APPLIED.json')
        V.applied_receipt(applied,reg,packet['registration_transaction_sha256'],N.TABLE)
    queue,_=P.load_queue(packet['queue_path']);jobs={j['job_id']:j for j in queue['jobs']};canonical={r['asset_id']:r for r in source['rows']}
    for jid,row,e in zip(packet['job_ids'],packet['rows'],packet['measurement_evidence']):
        assert row==project(jobs[jid],I.read(e['path']),canonical[row['asset_id']],e),'projection_changed'
    return {'prepared_document':after,'expected_source_sha256':packet['canonical_source_expected_sha256'],
        'expected_csv_sha256':packet['canonical_csv_expected_sha256'],'expected_prepared_sha256':packet['prepared_before_sha256'],
        'after_file_path':tx['after_path'],'after_file_sha256':tx['after_sha256'],'transaction_sha256':I.sha(transaction_path),
        'shared_writes_performed':False,'newly_enabled':[],'newly_qualified':[],'ordinary_generation_authorized':False}


def build():
    adopted=I.read(I.HERE/'ADOPTED_NATIVE_EVIDENCE.json')
    tx=I.read(I.HERE/'REGISTRATION_TRANSACTION.json')
    queue,_=P.load_queue();jobs={j['job_id']:j for j in queue['jobs']};ready=[];blocked=[]
    for jid in adopted['job_ids']:
        try:
            receipt=I.read(I.HERE/'Receipts'/(jid+'.json'))
            check_measurement(jobs[jid],receipt);verify_measurement_files(jobs[jid],receipt);ready.append(jid)
        except (AssertionError,KeyError) as exc:
            blocked.append({'job_id':jid,'reason':str(exc),'qualification_or_selection_changed':False})
    I.write('GENERIC_INTAKE_OUTCOMES.json',{'checked_ids':adopted['job_ids'],'ready_ids':ready,'blocked':blocked})
    return prepare(ready,registration_transaction_path=tx['transaction_path'])
