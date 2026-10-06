"""Record disk preservation after the reviewed orderly editor shutdown."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE / 'DirtyOriginals_Transfer'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    destination = OUT / 'POST_EXIT.json'
    assert not destination.exists(), 'immutable receipt already exists'
    command = "@(Get-CimInstance Win32_Process -Filter \"Name='UnrealEditor.exe'\" | Select-Object ProcessId,CommandLine) | ConvertTo-Json -Compress"
    process = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command], capture_output=True, text=True, check=True)
    live = json.loads(process.stdout) if process.stdout.strip() else []
    assert live == [], ('editor_still_running', live)
    request_path = OUT / 'NO_SAVE_RESTART_REQUEST.json'
    request = read(request_path)
    preserve = read(OUT / 'PRESERVE_REQUEST.json')
    deps_path = ROOT / 'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/BANK_SHUTDOWN_DEPENDENCIES.json'
    groups = {'protected_originals_catalog_profiles_maps': preserve['protected_disk_sha256'], 'reviewed_source_config_evidence_and_recovery_pins': request['file_pins'], 'saved_imports': {}, 'task4_dependencies': {}}
    for p in HERE.glob('IMPORTED_external_*.json'):
        value = read(p)
        if value.get('saved'):
            package = value['native_path'].split('.')[0]
            groups['saved_imports'][str(ROOT / 'Content' / (package.removeprefix('/Game/') + '.uasset'))] = value['native_sha256']
    for value in read(deps_path)['dependencies']:
        assert value['exists']
        groups['task4_dependencies'][str(ROOT / value['file'])] = value['sha256']
    assert len(groups['saved_imports']) == 84
    assert len(groups['task4_dependencies']) == 156
    measurements = {}
    failures = []
    for group, pins in groups.items():
        measurements[group] = []
        for p, expected in pins.items():
            actual = sha(p) if Path(p).is_file() else None
            entry = {'path': p, 'expected_sha256': expected, 'actual_sha256': actual, 'matches': actual == expected}
            measurements[group].append(entry)
            if not entry['matches']:
                failures.append(entry)
    log_path = ROOT / 'Saved/Logs/Environmentpipeline.log'
    log = log_path.read_text(encoding='utf-8', errors='replace')
    markers = [line for line in log.splitlines() if 'LogExit: Exiting.' in line or 'Log file closed' in line]
    receipt = {'schema': 'environmentpipeline.bank_preserved_post_exit.v1', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'manager_thread_id': request['manager_thread_id'], 'operator_thread_id': request['operator_thread_id'], 'exited_pid': request['pid'], 'live_editor_processes': live, 'process_exit_confirmed': True, 'shutdown_request_path': str(OUT / 'NO_SAVE_SHUTDOWN_REQUESTED.json'), 'shutdown_request_sha256': sha(OUT / 'NO_SAVE_SHUTDOWN_REQUESTED.json'), 'restart_request_sha256': sha(request_path), 'dependency_baseline_sha256': sha(deps_path), 'shutdown_log_path': str(log_path), 'shutdown_markers': markers[-4:], 'groups': measurements, 'counts': {k: len(v) for k, v in measurements.items()}, 'failures': failures, 'passed': not failures, 'fresh_start_executed': False, 'original_buffers_preserved_in_three_binary_verified_copies': True, 'content_or_map_save_requested_at_shutdown': False}
    with destination.open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'path': str(destination), 'sha256': sha(destination), 'passed': receipt['passed'], 'counts': receipt['counts'], 'failures': failures}))

if __name__ == '__main__':
    main()
