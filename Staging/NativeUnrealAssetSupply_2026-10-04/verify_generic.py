"""Focused generic intake checks, entirely offline; no bank/native writes."""
import copy
from pathlib import Path
from unittest.mock import patch
from . import intake as I
from . import authority as A
from . import integrity as V
from . import qualification_intake as Q
from . import post_remap as P
from . import native_supplier as N


def rejects(fn):
    try:fn()
    except (AssertionError,KeyError):return
    raise AssertionError('expected_rejection')


def verify():
    checks=[];protected={str(p):I.sha(p) for p in [I.CATALOG,N.CSV,I.PREP]}
    tx=Q.build();ptr=I.read(I.HERE/'QUALIFICATION_INTAKE.json');t,packet,after=Q.validate(ptr['path'])
    assert Q.build()==tx and I.sha(ptr['path'])==ptr['sha256'];checks.append('six_real_measurements_immutable_deterministic_intake')
    assert len(packet['rows'])==6
    before=I.read(tx['before_path']);assert len(after['rows'])==len(before['rows'])+2
    prior={r['asset_id']:r for r in before['rows']};new={r['asset_id']:r for r in after['rows']}
    for aid,r in prior.items():
        assert all(new[aid][key]==value for key,value in r.items()),'existing_prepared_field_changed'
    checks.append('all_existing_prepared_fields_preserved_two_append_four_evidence_augment')
    realq,_=P.load_queue();jobs={j['job_id']:j for j in realq['jobs']};job=jobs[packet['job_ids'][0]]
    rec=I.read(packet['measurement_evidence'][0]['path']);reg=I.read(packet['registration_transaction_path']);canonical=I.read(reg['bundle_source_path'])
    row=next(r for r in canonical['rows'] if r['asset_id']==job['asset_id'])
    for role in Q.ROLES:
        j=copy.deepcopy(job);r=copy.deepcopy(rec);c=copy.deepcopy(row);j['requested_role_candidate']=role
        # Synthetic roles exercise dispatch only, never assert actual source suitability.
        if role=='surface_material':
            r['native_class']='Material';r['used_textures']=[];r.pop('measurement')
        result=Q.project(j,r,c,packet['measurement_evidence'][0])
        assert result['required_consumer_context']==Q.ROLES[role][1]
        assert result['placement_contract_candidate']['functional_contact'] is None
        assert result['placement_contract_candidate']['functional_contract_verified'] is False
        assert result['newly_enabled'] is False
    checks.append('all_twenty_role_projections_including_material_have_explicit_unknown_functional_fields')
    for field,value in [('asset_id','wrong'),('native_object_path','/Game/Wrong.Wrong'),('native_sha256','0'*64),('pid',0)]:
        changed=copy.deepcopy(rec);changed[field]=value;rejects(lambda:Q.check_measurement(job,changed));checks.append('reject_measurement_'+field)
    changed=copy.deepcopy(rec);changed['measurement']['dimensions_cm'][0]+=5
    rejects(lambda:Q.check_measurement(job,changed));checks.append('reject_inconsistent_geometry')
    changed=copy.deepcopy(rec);changed['dependencies']['packages'].append('/Game/Missing')
    rejects(lambda:Q.check_measurement(job,changed));checks.append('reject_unhashed_dependency_package')
    for field in ('asset_id','catalog_row_name','object_path'):
        bad=copy.deepcopy(before);bad['rows'][1][field]=bad['rows'][0][field]
        rejects(lambda:Q.validate_prepared(bad));checks.append('reject_prepared_duplicate_'+field)
    bad=copy.deepcopy(packet['rows']);bad[0]['object_path']='/Game/Wrong.Wrong'
    # Bind a preexisting record exactly, then attempt to overwrite its native path.
    existing=copy.deepcopy(packet['rows'][0]);base={'schema':'fixture','rows':[existing]}
    rejects(lambda:Q.additive_merge(base,bad[:1],'fixture'));checks.append('reject_prepared_rebinding')
    rich=copy.deepcopy(packet['rows'][0]);rich['native_measurement']={'owner':'preserve','extra':123};rich['hold_reasons_preserved']=['H0013','H0094']
    merged=Q.additive_merge({'schema':'fixture','rows':[rich]},packet['rows'][:1],'fixture')
    assert merged['rows'][0]['native_measurement']==rich['native_measurement'] and merged['rows'][0]['hold_reasons_preserved']==rich['hold_reasons_preserved']
    checks.append('preserve_richer_measurements_and_named_holds')
    args=[packet,packet['canonical_source_expected_sha256'],packet['canonical_csv_expected_sha256'],packet['prepared_before_sha256'],packet['canonical_digest'],packet['canonical_rows'],before,before]
    assert Q.cas_state(*args)
    for pos in (1,2,3,4,5,6):
        bad=list(args);bad[pos]='stale' if pos!=6 else {'rows':[]}
        rejects(lambda:Q.cas_state(*bad));checks.append('reject_CAS_component_'+str(pos))
    checks.append('CAS_exact_before_state_passes_no_shared_write')
    # Final-target/source revision separation, using an in-memory receipt only.
    finaljob=copy.deepcopy(job);finalrec=copy.deepcopy(rec)
    finaljob.update(operation='inspect_remapped_target',native_sha256='a'*64)
    finalrec.update(native_sha256='a'*64,queue_sha256='b'*64,queue_path='fixture_final_queue')
    assert Q.check_measurement(finaljob,finalrec)
    finalrec.pop('native_sha256');rejects(lambda:Q.check_measurement(finaljob,finalrec));checks.append('source_receipt_cannot_stand_in_for_post_remap_native_revision')
    changed=copy.deepcopy(row);changed['runtime']['AssetRevision']='c'*64
    rejects(lambda:Q.project(job,rec,changed,packet['measurement_evidence'][0]));checks.append('reject_stale_canonical_revision')
    # Missing canonical revision remains visible and unselected for four existing rows.
    unbound=[r for r in packet['rows'] if r['canonical_revision_binding_pending']]
    assert len(unbound)==4 and all(not r['runtime_enabled'] and not r['package_revision_matches_runtime'] for r in unbound)
    checks.append('missing_canonical_revision_explicitly_pending_never_fabricated')
    # Exercise complete source->final-target queue projection in memory only.
    external=copy.deepcopy(next(j for j in realq['jobs'] if j['source_id']=='CitySample'))
    original=external['source_object_path'].split('.')[0]
    target='/Game/Project/Shared/ModelBank/Prepared/NativeUnreal/CitySample/'+original[6:]
    obj=target+'.'+external['source_object_path'].rsplit('.',1)[-1]
    plan_path=I.HERE/'MigrationPlans'/'offline_fixture'/'PLAN.json';remap_path=plan_path.parent/'REMAPPED.json'
    plan={'source_id':'CitySample','job_ids':[external['job_id']],'mapping':[{'original_object':external['source_object_path'],'target_object':obj,'target_package':target}]}
    native_file=I.ROOT/'Content'/(target[6:]+'.uasset')
    remap={'plan_sha256':'plan_hash','namespace_remap_completed':True,'source_originals_unchanged':True,'no_source_project_writes':True,'pid':123,
        'saved_files':[{'file':str(native_file),'sha256':'n'*64}], 'prepared_targets':[target],
        'dependency_closures':{obj:{'packages':[target],'missing':[]}}}
    original_read=I.read;original_sha=I.sha;captured={}
    def fixture_read(path):
        return remap if Path(path).resolve()==remap_path.resolve() else original_read(path)
    def fixture_sha(path):
        resolved=Path(path).resolve()
        if resolved==plan_path.resolve():return 'plan_hash'
        if resolved==native_file.resolve():return 'n'*64
        if resolved==remap_path.resolve():return 'remap_hash'
        if resolved.is_relative_to(I.HERE/'TargetQueues'):return V.digest(captured[str(resolved)])
        return original_sha(path)
    def capture_document(path,doc):captured[str(Path(path).resolve())]=copy.deepcopy(doc)
    with patch.object(P.M,'validate_plan',return_value=plan),patch.object(P.M,'verify_source_files'),patch.object(I,'read',side_effect=fixture_read),patch.object(I,'sha',side_effect=fixture_sha),patch.object(A,'immutable_json',side_effect=capture_document):
        result=P.prepare_jobs(plan_path,remap_path);projected=captured[str(Path(result['queue_path']).resolve())]['jobs'][0]
        assert projected['source_sha256']==external['source_sha256'] and projected['native_sha256']=='n'*64
        assert projected['native_object_path']==obj and projected['existing_measurement'] is None
        checks.append('post_remap_full_projection_preserves_source_and_requires_target_measurement_offline_fixture')
        remap['dependency_closures'][obj]['packages'].append('/Game/Unremapped')
        rejects(lambda:P.prepare_jobs(plan_path,remap_path));checks.append('post_remap_rejects_unremapped_dependency')
        remap['dependency_closures'][obj]['packages'].pop()
        remap['saved_files'][0]['sha256']='bad'
        rejects(lambda:P.prepare_jobs(plan_path,remap_path));checks.append('post_remap_rejects_changed_target_file')
        remap['saved_files'][0]['sha256']='n'*64
        remap['source_originals_unchanged']=False
        rejects(lambda:P.prepare_jobs(plan_path,remap_path));checks.append('post_remap_rejects_original_change')
    assert protected=={str(p):I.sha(p) for p in [I.CATALOG,N.CSV,I.PREP]}
    report={'schema':'environmentpipeline.generic_intake_checks.v1','status':'passed','checks':checks,'count':len(checks),
        'real_projected_records':len(packet['rows']),'prepared_additions':2,'existing_evidence_augmentations':4,
        'role_dispatch_cases':len(Q.ROLES),'tests_are_offline':True,'native_or_shared_apply_tested':False,
        'protected_files_unchanged':protected,'transaction_path':ptr['path'],'transaction_sha256':ptr['sha256'],
        'command_manifest_sha256':I.sha(A.manifest()[1]),'verification_source_sha256':I.sha(__file__)}
    I.write('GENERIC_INTAKE_VERIFICATION.json',report);print(report)
    return report
