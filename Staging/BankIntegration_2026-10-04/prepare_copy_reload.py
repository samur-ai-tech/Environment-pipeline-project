"""Freeze exact saved recovery package readback request; no editor operation."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;OUT=HERE/'DirtyOriginals_Transfer'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare():
    target=OUT/'COPY_RELOAD_REQUEST.json';assert not target.exists()
    q=read(OUT/'PRESERVE_REQUEST.json');resume=read(OUT/'PRESERVE_RESUME_REQUEST_v2.json');saved=read(OUT/'PRESERVE_RESUME_RESULT.json')
    assert saved['passed'] and len(saved['saved'])==3
    assert saved['after']['dirty_content']==sorted(q['source_packages']) and not saved['after']['dirty_maps']
    script=HERE/'reload_preserved_copies.py';ast.parse(script.read_text(encoding='utf-8-sig'))
    pins=dict(resume['file_pins']);pins[str(script)]=sha(script)
    for p in (OUT/'PRESERVE_RESUME_REQUEST_v2.json',OUT/'PRESERVE_RESUME_RESULT.json'):pins[str(p)]=sha(p)
    for row in saved['saved']:
        p=HERE.parents[1]/'Content'/(row['path'][6:]+'.uasset');assert sha(p)==row['sha256'];pins[str(p)]=row['sha256']
    result={'schema':'environmentpipeline.recovery_copy_reload_request.v1','status':'PREPARED_NOT_EXECUTED',
        'manager_thread_id':q['manager_thread_id'],'operator_thread_id':q['operator_thread_id'],'pid':q['pid'],'world':q['world'],
        'script_path':str(script.resolve()),'script_sha256':sha(script),'file_pins':pins,
        'preserve_helper_path':q['script_path'],'normalization_helper_path':resume['script_path'],
        'destinations':q['destinations'],'identity_guid_deltas':resume['identity_guid_deltas'],
        'activation_path':str(HERE.parents[1]/'Staging/ManagedSystemsAstra_2026-10-04/DirtyOriginals_COPY_RELOAD_ACTIVATION.json'),
        'required_scope_and_lease_activation':'RELOAD_RECOVERY_COPIES_ONLY',
        'operations':'Reload ONLY three saved CLEAN recovery packages with installed ASSUME_NEGATIVE API. Verify distinct native object AND package pointers at each exact path, full property/raw geometry/corner-attribute equality and each exact LightingGuid; check sole OS PID/command before and after.',
        'forbidden':'No original save/reload/discard/close/shutdown, no Content saves, no catalog or area operation.',
        'originals_remain_dirty':q['source_packages'],'native_execution':False}
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'request':str(target),'request_sha256':sha(target),'script_sha256':sha(script),'pins':len(pins),'saved_receipt_sha256':sha(OUT/'PRESERVE_RESUME_RESULT.json')}))

if __name__=='__main__':prepare()
