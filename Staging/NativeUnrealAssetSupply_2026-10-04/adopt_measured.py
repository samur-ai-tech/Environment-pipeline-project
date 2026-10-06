"""Reuse exact bank-writer measurements instead of remeasuring owned work.

No native call and no Content write. Receipt origin is explicit. Hash current
mesh and all resolved dependency files; do not infer appearance or role approval.
"""
from pathlib import Path
from . import intake as I

def adopt():
    evidence_path=I.BANK/'R020_NATIVE_CONTENT_CONTRACTS.json'
    evidence=I.read(evidence_path)
    by_path={r['native_path']:r for r in evidence['jobs']}
    jobs=I.read(I.HERE/'READY_JOBS.json')['jobs']
    adopted=[]
    for job in jobs:
        row=by_path.get(job['native_object_path'])
        if not row or not row.get('measurement'):continue
        assert row['file_sha256']==job['source_sha256']==I.sha(job['source_file'])
        files=[]
        for package in row['original_dependencies']['packages']:
            if package.startswith('/Game/'):
                p=I.ROOT/'Content'/(package[6:]+'.uasset')
            elif package.startswith('/Engine/'):
                p=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Content')/(package[8:]+'.uasset')
            else:
                files.append({'package':package,'state':'plugin_mount_file_requires_resolved_owner_evidence'})
                continue
            parts=[{'file':str(p.with_suffix(ext)),'sha256':I.sha(p.with_suffix(ext)),'bytes':p.with_suffix(ext).stat().st_size}
                   for ext in ['.uasset','.uexp','.ubulk','.uptnl'] if p.with_suffix(ext).is_file()]
            files.append({'package':package,'files':parts,'state':'files_hashed' if parts else 'missing_package_file'})
        receipt={'job_id':job['job_id'],'asset_id':job['asset_id'],'native_object_path':row['native_path'],
            'resolved_object_path':row['native_path'],'source_sha256':row['file_sha256'],
            'native_class':row['native_class'],'pid':row['pid'],'measurement':row['measurement'],
            'dependencies':row['original_dependencies'],'dependency_files':files,
            'status':'native_measured','measurement_reused_from':str(evidence_path),'measurement_evidence_sha256':I.sha(evidence_path),
            'new_native_call_performed':False,'mesh_bytes_reverified':True,
            'dependency_hash_basis':'current_disk_hashes; source receipt supplies native closure; no claim of original dependency hashes',
            'materials_present':all(s['path'] for s in row['measurement']['material_slots']) and not row['original_dependencies']['missing'],
            'compatible_material_slots':row.get('compatible_material_slots'),
            'contact_reviewed':False,'facing_reviewed':False,'visual_reviewed':False,'selection_eligible':False,
            'named_save_performed_by_supplier':False,'area_generated':False,'role_review':row['role_review']}
        I.write('Receipts/'+job['job_id']+'.json',receipt)
        adopted.append(job['job_id'])
    I.write('ADOPTED_NATIVE_EVIDENCE.json',{'source_receipt':str(evidence_path),'source_sha256':I.sha(evidence_path),'job_ids':adopted,
        'native_writer':'01a1067c-5012-7550-b449-015b53c9d726','new_native_operations':0})
    return adopted

if __name__=='__main__':
    print(adopt())
