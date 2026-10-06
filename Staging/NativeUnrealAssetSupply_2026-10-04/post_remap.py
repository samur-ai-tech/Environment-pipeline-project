"""Offline handoff from a completed native remap to final-target inspection.

Source identity and remapped native revision are deliberately separate. This
module never treats a source-project measurement as a final-target measurement.
"""
import copy
from pathlib import Path
from . import intake as I
from . import authority as A
from . import integrity as V
from . import migration_remap as M


def verify_files(files):
    assert files and len(files)==len({str(Path(f['file']).resolve()).casefold() for f in files})
    for f in files:
        assert I.sha(f['file'])==f['sha256'],'post_remap_file_changed'


def prepare_jobs(plan_path, remap_receipt_path):
    p=M.validate_plan(plan_path);rp=Path(remap_receipt_path).resolve()
    assert rp==Path(plan_path).resolve().parent/'REMAPPED.json'
    r=I.read(rp)
    assert r['plan_sha256']==I.sha(plan_path) and r['namespace_remap_completed'] is True
    assert r['source_originals_unchanged'] is True and r['no_source_project_writes'] is True and r['pid']>0
    verify_files(r['saved_files']);M.verify_source_files(p)
    targets={x['target_package'] for x in p['mapping']}
    assert set(r['prepared_targets'])==targets
    source=I.read(I.HERE/'READY_JOBS.json');jobs={j['job_id']:j for j in source['jobs']}
    mapping={x['original_object']:x for x in p['mapping']};out=[]
    for jid in p['job_ids']:
        j=copy.deepcopy(jobs[jid]);x=mapping[j['source_object_path']]
        assert j['source_id']==p['source_id'] and I.sha(j['source_file'])==j['source_sha256']
        closure=r['dependency_closures'][x['target_object']]
        assert not closure['missing'] and all(d.startswith('/Engine/') or d in targets for d in closure['packages'])
        f=M.package_file(x['target_package']);expected=[v for v in r['saved_files'] if Path(v['file']).resolve()==f.resolve()]
        assert len(expected)==1 and I.sha(f)==expected[0]['sha256']
        j.update(native_object_path=x['target_object'],target_object_path=x['target_object'],native_file=str(f),
                 native_sha256=expected[0]['sha256'],operation='inspect_remapped_target',status='ready_native_inspection',
                 post_remap_dependency_closure=closure,post_remap_receipt_path=str(rp),post_remap_receipt_sha256=I.sha(rp),
                 materials_and_dimensions_require_final_target_measurement=True,existing_measurement=None)
        out.append(j)
    assert len(out)==len({j['job_id'] for j in out})==len({j['native_object_path'].casefold() for j in out})
    q={'schema':'environmentpipeline.final_native_target_queue.v1','authority':A.authority(),
       'origin_queue_path':str(I.HERE/'READY_JOBS.json'),'origin_queue_sha256':I.sha(I.HERE/'READY_JOBS.json'),
       'plan_path':str(Path(plan_path).resolve()),'plan_sha256':I.sha(plan_path),'remap_receipt_path':str(rp),
       'remap_receipt_sha256':I.sha(rp),'jobs':out,'native_measurement_performed':False}
    dest=I.HERE/'TargetQueues'/V.digest(q)/'QUEUE.json';A.immutable_json(dest,q)
    return {'queue_path':str(dest),'queue_sha256':I.sha(dest),'job_ids':[j['job_id'] for j in out]}


def load_queue(queue_path=None):
    p=Path(queue_path or I.HERE/'READY_JOBS.json').resolve();q=I.read(p)
    if p!=I.HERE/'READY_JOBS.json':
        assert p.is_relative_to(I.HERE/'TargetQueues') and V.digest(q)==p.parent.name
        assert q['authority']==A.authority() and q['origin_queue_sha256']==I.sha(I.HERE/'READY_JOBS.json')
        assert I.sha(q['plan_path'])==q['plan_sha256'] and I.sha(q['remap_receipt_path'])==q['remap_receipt_sha256']
        rebuilt=prepare_jobs(q['plan_path'],q['remap_receipt_path'])
        assert Path(rebuilt['queue_path']).resolve()==p and rebuilt['queue_sha256']==I.sha(p)
    assert len(q['jobs'])==len({j['job_id'] for j in q['jobs']})
    return q,p
