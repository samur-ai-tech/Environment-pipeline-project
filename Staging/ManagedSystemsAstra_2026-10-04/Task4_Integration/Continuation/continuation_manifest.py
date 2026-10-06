"""Offline evidence capture/check only; never imports Unreal or modifies shared files."""
import argparse
import csv
import datetime
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MANAGER = '01a10789-2e6a-7321-ad85-0a2964f8a937'
OPERATOR = '01a106e8-f85a-7a72-a010-e1cb28356e2b'
SEAL = ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
ASSIGNMENTS = ROOT/'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json'
TRANSFER = ROOT/'Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/STATE.json'
BANK = ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02'
INTS = {'SchemaVersion','RunEligible','BoundsValid','AnchorValid','OrientationValid','TechnicalPreviewEligible','ExplicitHold'}
BANK_OPERATOR = '01a1067c-5012-7550-b449-015b53c9d726'

def editor_pids():
    """Fresh OS enumeration; fixed read-only command, no native Unreal calls."""
    executable=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    result=subprocess.run([str(executable),'-NoProfile','-NonInteractive','-Command',
        '$ErrorActionPreference="Stop"; ConvertTo-Json -Compress -InputObject @(Get-Process -Name UnrealEditor -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })'],
        check=True,capture_output=True,text=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
    values=json.loads(result.stdout)
    assert isinstance(values,list) and all(type(p) is int and p>0 for p in values)
    return sorted(values)

def require_sole_editor(pids, pid):
    assert pids==[pid], 'Inspection requires the actual sole UnrealEditor PID'

def lease_fields(line):
    fields={}
    for token in line.split():
        if '=' in token:
            key,value=token.split('=',1)
            assert key not in fields, 'Duplicate lease field'
            fields[key]=value
    return fields

def checked_receipt(name, expected):
    path=Path(name).resolve(strict=True)
    assert path.is_relative_to(ROOT/'Staging'), 'Receipt must be an exact project staging file'
    assert sha(path)==expected, 'Receipt hash differs: '+str(path)
    return path,read(path)

def validate_landscapes(expected, area, actual_paths, official_paths, baked_paths, hda_path):
    assert expected['map']==area['map'] and expected['map_sha256']==area['map_sha256']
    assert expected['source_sha256']==area['source_sha256']
    assert expected['hda_actor_path']==hda_path
    groups=[expected[k] for k in ('actor_paths','official_actor_paths','baked_actor_paths')]
    for paths in groups:
        assert isinstance(paths,list) and len(paths)==len(set(paths))
        assert all(p.startswith(area['map']+'.'+area['map'].rsplit('/',1)[-1]+':PersistentLevel.') for p in paths)
    all_expected,official_expected,baked_expected=map(set,groups)
    assert all_expected and official_expected, 'Nonempty exact official Landscape ownership required'
    assert all_expected==official_expected|baked_expected, 'Incomplete reviewed ownership partition'
    assert set(actual_paths)==all_expected, 'Missing or unexpected saved Landscape'
    assert set(official_paths)==official_expected, 'Empty or different official Landscape result'
    assert set(baked_paths)&all_expected==baked_expected, 'Prior baked ownership differs'

def validate_release_data(receipt, approval, record, last_lease):
    assert receipt['schema']=='environmentpipeline.clean_editor_release.v1'
    assert receipt['manager_thread_id']==approval['manager_thread_id']==MANAGER
    assert receipt['operator_thread_id']==approval['release_operator_thread_id']
    assert receipt['operator_thread_id'] in (BANK_OPERATOR,OPERATOR)
    assert type(receipt['released_editor_pid']) is int and receipt['released_editor_pid']>0
    assert receipt['released_editor_pid']==approval['released_editor_pid']
    assert receipt['map']==approval['released_map']
    assert receipt['map'] in {a['map'] for a in record['areas']}
    for flag in ('process_exited','clean_handoff','cooking_paused_before_exit','no_shutdown_saves'):
        assert receipt[flag] is True, 'Unproven release boundary: '+flag
    assert receipt['auto_cook_before_exit'] is False and receipt['auto_bake_before_exit'] is False
    assert receipt['callbacks_before_exit']==0 and type(receipt['callbacks_before_exit']) is int
    assert receipt['dirty_maps_before_exit']==[] and receipt['dirty_content_before_exit']==[]
    fields=lease_fields(last_lease)
    assert fields['OWNER']=='NONE'
    assert fields['manager_thread_id']==MANAGER
    assert fields['operator_thread_id']==receipt['operator_thread_id']
    assert fields['released_editor_PID']==str(receipt['released_editor_pid']) and fields['map']==receipt['map']
    assert fields['clean_handoff']=='true' and fields['process_exited']=='true'
    assert fields['release_receipt']==Path(approval['bank_clean_handoff_receipt']).resolve().relative_to(ROOT).as_posix()
    assert fields['release_receipt_sha256']==approval['bank_clean_handoff_sha256']
    assert receipt['catalog_digest']==record['catalog']['typed_source_digest']
    assert receipt['preserved_original_maps']=={a['map']:a['map_sha256'] for a in record['areas']}
    # Exact file closures, not just aggregate counts or a preservation boolean.
    baseline=read(HERE.parent/'DISK_RECONCILIATION.json')
    candidates={r['file']:r['sha256'] for a in baseline['areas'] for r in a['preserved_candidate_disk_checks']}
    assert len(candidates)==87 and receipt['preserved_candidates']==candidates
    vendor=receipt['preserved_vendor_originals']
    required={'Content/Palms_Pack_01/Add_Props/Plants/Materials/MI_Plant_07_6_Leaves_G.uasset',
        'Content/Palms_Pack_01/Add_Props/Plants/Materials/MI_Plant_07_6_Stem_G.uasset',
        'Content/Palms_Pack_01/Add_Props/Plants/Meshes/SM_Plant_07_6_G.uasset'}
    assert required.issubset(vendor), 'Missing exact Plant07 original preservation'
    saved=receipt['named_saved_packages']
    assert isinstance(saved,dict), 'Exact named saved package file/hash closure required'
    for name in saved:
        assert name.startswith('Content/Project/') and name.endswith(('.uasset','.umap')), 'Saved vendor or unscoped package'
    for group in (candidates,vendor,saved):
        for name,expected in group.items():
            path=(ROOT/name).resolve(strict=True)
            assert path.is_relative_to(ROOT/'Content') and sha(path)==expected, 'Release file boundary changed: '+name

def verify_launch():
    record=verify();approval=read(HERE/'STARTUP_ACTIVATION.json')
    assert approval['startup_inspection_authorized'] is True and approval['ordinary_generation_authorized'] is False
    assert approval['manager_thread_id']==MANAGER and approval['operator_thread_id']==OPERATOR
    assert approval['continuation_manifest_sha256']==sha(HERE/'CONTINUATION_MANIFEST.json')
    assert approval['native_table_selection_sha256']==record['native_table_selection_sha256']
    _,ownership=checked_receipt(approval['landscape_ownership_receipt'],approval['landscape_ownership_sha256'])
    area=next(a for a in record['areas'] if a['map']==approval['map'])
    validate_landscapes(ownership,area,ownership['actor_paths'],ownership['official_actor_paths'],
        read(area['last_success_receipt'])['baked_actor_paths'],ownership['hda_actor_path'])
    _,receipt=checked_receipt(approval['bank_clean_handoff_receipt'],approval['bank_clean_handoff_sha256'])
    last=(ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').strip().splitlines()[-1]
    validate_release_data(receipt,approval,record,last)
    assert editor_pids()==[], 'An UnrealEditor process is still open'
    return record

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def digest(rows):
    # Same typed canonicalization as bank_contracts.digest; hash-bound in manifest.
    result = []
    for raw in rows:
        row = {}
        for key, value in raw.items():
            if key in INTS:
                row[key] = int(value) if key == 'SchemaVersion' else int(str(value).lower() in ('true','1'))
            elif key.endswith('Cm') or key in ('SelectionWeight','PreviewWeight'):
                row[key] = float(value)
                assert math.isfinite(row[key]), key
            else:
                row[key] = value
        result.append(row)
    assert len({r['Name'] for r in result}) == len(result), 'Duplicate catalog identity'
    return hashlib.sha256(json.dumps(sorted(result,key=lambda r:r['Name']),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def package_file(name, extension='.uasset'):
    assert name.startswith('/Game/')
    return ROOT/'Content'/(name.split('.')[0][6:]+extension)

def current_authority():
    assignment = read(ASSIGNMENTS)
    transfer = read(TRANSFER)
    assert assignment['manager_thread_id'] == transfer['successor_manager_thread_id'] == MANAGER
    assert transfer['status'] == 'TRANSFERRED_TO_SUCCESSOR'
    assert next(t for t in assignment['tasks'] if t['id']=='task4')['thread_id'] == OPERATOR
    return {'manager_thread_id':assignment['manager_thread_id'],'operator_thread_id':OPERATOR,
        'transfer_status':transfer['status'],'successor_manager_thread_id':transfer['successor_manager_thread_id'],
        'original_maps':sorted(assignment['native_area_maps'])}

def collect(selection_path):
    authority=current_authority();assignment=read(ASSIGNMENTS)
    seal = read(SEAL)
    paths = [SEAL, ROOT/'Content/Python'/seal['startup']['file']]
    assert sha(paths[-1]) == seal['startup']['sha256']
    assert len(seal['modules']) == 12
    for name, entry in seal['modules'].items():
        assert entry['file'] == name+'.py'
        path = ROOT/'Content/Python'/entry['file']
        assert sha(path) == entry['sha256'], str(path)
        paths.append(path)
    for name, expected in seal['support_files'].items():
        path = ROOT/name
        assert sha(path) == expected, str(path)
        paths.append(path)
    source_path = BANK/'catalog_v4_source.json'
    csv_path = BANK/'catalog_v4_full.csv'
    source = read(source_path)
    with csv_path.open(encoding='utf-8-sig',newline='') as stream:
        rows = list(csv.DictReader(stream))
    expected = digest([r['runtime'] for r in source['rows']])
    assert expected == digest(rows) == source['catalog_sha256']
    paths += [source_path,csv_path,ROOT/'Staging/BankIntegration_2026-10-04/bank_contracts.py']
    selection_path=Path(selection_path).resolve(strict=True)
    assert selection_path.is_relative_to(HERE), 'Receipt selection must be in Task4 continuation scope'
    selection=read(selection_path)
    assert selection['manager_thread_id']==MANAGER
    assert selection['source_sha256']==sha(source_path) and selection['csv_sha256']==sha(csv_path)
    native_receipt,native=checked_receipt(selection['receipt'],selection['receipt_sha256'])
    readback_path,readback=checked_receipt(selection['native_readback'],selection['native_readback_sha256'])
    assert native['saved'] is True and native['digest'] == expected and native['rows'] == len(rows)
    assert native['table']=='/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4'
    assert len(readback)==len(rows) and digest(readback)==expected
    paths += [selection_path,native_receipt,readback_path]
    areas = []
    for map_name in assignment['native_area_maps']:
        profiles = [p for p in (ROOT/'Staging/ModelBank').glob('*/AREA_PROFILE.json') if read(p)['map']==map_name]
        assert len(profiles)==1
        path = profiles[0]; p = read(path)
        assert p['catalog_sha256'] == p['release']['catalog_sha256'] == expected
        decision = Path(p['release']['decision_receipt'])
        assert sha(decision)==p['release']['decision_sha256']
        prior = Path(p['workflow_receipt']).with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json')
        assert Path(read(prior)['profile']).resolve()==path.resolve()
        selected = [path,package_file(map_name,'.umap'),Path(p['source']),decision,prior,package_file(p['hda']),package_file(p['table'])]
        paths += selected
        areas.append({'map':map_name,'profile':str(path),'profile_sha256':sha(path),'map_sha256':sha(selected[1]),
            'source':p['source'],'source_sha256':sha(selected[2]),'table':p['table'],'hda':p['hda'],
            'last_success_receipt':str(prior),'catalog_sha256':expected})
    baseline_path = HERE.parent/'DISK_RECONCILIATION.json'
    baseline = read(baseline_path)
    candidates = [r for a in baseline['areas'] for r in a['preserved_candidate_disk_checks']]
    assert len(candidates)==87 and len({r['file'] for r in candidates})==87
    for r in candidates:
        assert r['approved'] is False and sha(ROOT/r['file'])==r['sha256'], r['file']
        paths.append(ROOT/r['file'])
    paths.append(baseline_path)
    paths += [HERE/n for n in ('continuation_manifest.py','inspect_task4_startup.py','launch_reviewed.ps1','CONTINUATION.txt',
        'STARTUP_ACTIVATION.template.json','CLEAN_RELEASE_CONTRACT.txt','check_review_gates.py')]
    files = {str(p.resolve()):sha(p) for p in paths}
    # A second read catches concurrent writes during the snapshot.
    for name, expected_sha in files.items():
        assert sha(name)==expected_sha, 'Changed during capture: '+name
    return {'schema':'environmentpipeline.task4.continuation.v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'PREPARATION_ONLY_NOT_NATIVE_ACTIVATION','manager_thread_id':MANAGER,'operator_thread_id':OPERATOR,
        'manifest_sha256':sha(SEAL),'files':files,'areas':areas,'catalog':{'typed_source_digest':expected,'typed_csv_digest':expected,
        'native_saved_receipt_digest':native['digest'],'native_live_checked_this_turn':False,'rows':len(rows)},
        'authority':authority,'authority_files_observed':{str(ASSIGNMENTS):sha(ASSIGNMENTS),str(TRANSFER):sha(TRANSFER)},
        'native_table_selection':str(selection_path),'native_table_selection_sha256':sha(selection_path),
        'preserved_candidates':87,'candidate_approval':False,'native_execution':'NOT_RUN',
        'lease_observed':(ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').strip().splitlines()[-1]}

def verify(path=None):
    record = read(path or HERE/'CONTINUATION_MANIFEST.json')
    assert record['manager_thread_id']==read(ASSIGNMENTS)['manager_thread_id']==MANAGER
    assert record['operator_thread_id']==OPERATOR
    assert current_authority()==record['authority'], 'Current transfer/task4 authority differs from reviewed identities'
    for name, expected in record['files'].items():
        assert sha(name)==expected, 'Reviewed snapshot changed: '+name
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group()
    group.add_argument('--capture',action='store_true');group.add_argument('--verify-launch',action='store_true')
    parser.add_argument('--native-table-selection');args=parser.parse_args()
    if args.capture:
        assert args.native_table_selection, 'Capture requires an explicitly designated receipt selection; no fallback'
        record=collect(args.native_table_selection)
        (HERE/'CONTINUATION_MANIFEST.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    else:
        record=verify_launch() if args.verify_launch else verify()
    print(json.dumps({'passed':True,'mode':'captured' if args.capture else 'verified','files':len(record['files']),
        'catalog':record['catalog'],'manifest_sha256':record['manifest_sha256'],'native_calls':0,'activation_granted':False}))
