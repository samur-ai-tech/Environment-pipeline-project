"""PREPARED ONLY. Saved/reopen wrapper; import has no editor effects.

Requires separately reviewed inspector SHA after final source API freeze.
Refreshes only geocity_roadbld_grounding; never bank/native authoring modules.
"""
import datetime,hashlib,importlib,json,os,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
ACTIVE=[]
def schedule(expected_grounding_sha256,expected_workflow_sha256,independent_review_sha256,expected_inspector_sha256,manager_activation):
    assert manager_activation=='ROOT_ACTIVATED_SAVED_REOPEN_VERIFICATION'
    import unreal
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_grounding as grounding
    validator=runpy.run_path(str(HERE/'resume_existing_shuj_postbinding.py'))
    validator['frozen'](expected_grounding_sha256,expected_workflow_sha256,independent_review_sha256)
    inspector=ROOT/'Staging/AppearanceRepair_2026-10-03/inspect_native_road_delivery.py'
    assert hashlib.sha256(inspector.read_bytes()).hexdigest()==expected_inspector_sha256
    p=bank.ACTIVE[-1];r=native.ACTIVE[-1];p.guard();r.guard();p.guard_processes()
    assert os.getpid()==32752 and r.revision=='20261003T172549017159'
    assert r.state['phase']=='native_generated_saved_verified' and r.state.get('saved')
    assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
    assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
    assert p.api.is_asset_cooking_paused() and p.api.is_session_valid()
    assert not any(x['handle'] is not None for x in ACTIVE)
    profile=ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
    delivery=json.loads(profile.with_name('ROADBLD_DELIVERY.json').read_text())
    assert delivery['saved'] and delivery['revision']==r.revision
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_path_name()==delivery['named_map']
    dirty={x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()}|{x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
    assert delivery['named_map'] not in dirty
    assert not set(delivery['named_generated_dependency_paths']).intersection(dirty)
    # Final inspector must pass these exact retained proof objects to its proxy,
    # construct LandscapeSampler(saved=True), and preserve historical core keys.
    assert isinstance(delivery['clipping_report'],dict) and isinstance(delivery['grounding_report'],dict)
    grounding=importlib.reload(grounding)
    assert grounding.SCHEMA==delivery['grounding_report']['schema']==delivery['native_grounding_validation']['schema']
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_POSTBINDING_SAVED_REOPEN_'+stamp+'.json')
    state={'handle':None}
    report={'phase':'scheduled','area':'GazaShujaiya','pid':os.getpid(),'revision':r.revision,'source_sha256':expected_grounding_sha256,
      'inspector_sha256':expected_inspector_sha256,'review_sha256':independent_review_sha256,'no_recook':True,'fresh_editor_restart':False}
    def write():receipt.write_text(json.dumps(report,indent=2)+'\n')
    def compare_all_retained(proof):
        expected=delivery['native_grounding_validation']
        # Additional final partition/exclusion/continuity/ledger fields must
        # survive save/reopen exactly. Existing zero-exclusion contracts need
        # only their recorded fields; do not invent or rewrite old receipts.
        for key,value in expected.items():
            if key=='elapsed_seconds':continue
            assert key in proof and proof[key]==value,'Retained final grounding field changed: '+key
    def verify(dt):
        unreal.unregister_slate_post_tick_callback(state['handle']);state['handle']=None
        try:
            p.guard();r.guard()
            inspect=runpy.run_path(str(inspector))['inspect_delivery']
            report['phase']='inspecting_saved';write()
            first=inspect(str(profile),context='saved_readback',max_seconds=300)
            compare_all_retained(first['native_grounding_readback'])
            report['saved_native_receipt']=first;report['phase']='reopening_same_named_map';write()
            reopen=runpy.run_path(str(ROOT/'Staging/AppearanceRepair_2026-10-03/reopen_retained_area.py'))['reopen_area']
            report['bank_reopen_receipt']=reopen(str(profile))
            report['phase']='inspecting_reopened';write()
            second=inspect(str(profile),context='reopen_readback',max_seconds=300)
            compare_all_retained(second['native_grounding_readback'])
            report['reopened_native_receipt']=second;report['phase']='passed';write()
        except Exception as exc:
            import traceback
            report.update(phase='failed',error=repr(exc),traceback=traceback.format_exc());write()
    write();ACTIVE.append(state);state['handle']=unreal.register_slate_post_tick_callback(verify)
    return {'scheduled':True,'receipt':str(receipt)}
