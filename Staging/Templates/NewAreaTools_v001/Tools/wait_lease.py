"""Outside the editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat fork of the manager's
wait_lease.py. Poll the EDITOR_OWNER.txt tail (never the live ledgers) until the sealed run of --pid releases its lease, the
editor exits, or --timeout-seconds pass. Prints one line per phase change seen in the lease tail.
El Wahat change kept in the template: optional --log <the editor's -abslog file, printed by
launch_area_editor.ps1>. The sealed run keeps OWNER=GEOCITY_MENU after a failure that leaves its wrapper or dirty packages
(geocity_bank_workflow.py finish_operation: recovery_required), so the lease alone cannot show such a failure until the
timeout. With --log the waiter also tails that log for the line the sealed fail() logs, 'GeoCity failed_<phase>: <error>',
and exits 5 at once. The log is opened read-only for each poll (binary, the default deny-none sharing, Unreal keeps writing)
and read from the end of the last complete line seen; the -abslog file is new for each launch, so it starts at offset 0 and
also catches a failure from before the waiter started. It never opens WORKFLOW_STATE.json or BUILD_STATE.json. Order per
poll: lease, then log, then process, so a failed run that released its lease keeps exit 2.
Exit 0 = released baked_saved_verified; 2 = released in another phase (failed_*); 3 = editor exited without release;
4 = timeout; 5 = a 'GeoCity failed_' line in --log while the lease is still held. A --log path that is not a file stops
the tool at once (assert, exit 1).
    python -B wait_lease.py --pid <pid> --label <label> [--log <abslog>] [--timeout-seconds 21600]
"""
import argparse, datetime, json, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEASE = ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt'
TASK = Path(__file__).resolve().parents[1]                               # template v001: this task folder (G1)
assert TASK.parent == ROOT / 'Staging', ('run from a task folder under <project>/Staging, never from the template', str(TASK))
MARK = b'GeoCity failed_'
LOG = {'path': None, 'offset': 0, 'read_errors': 0}


def tail():
    lines = [l for l in LEASE.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    return lines[-1] if lines else ''


def alive(pid):
    out = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', '(Get-Process -Id %d -ErrorAction SilentlyContinue) -ne $null' % pid],
                         capture_output=True, text=True, timeout=60)
    return out.stdout.strip().lower() == 'true'


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%SZ')


def log_failure_line():
    """First new complete log line holding MARK (decoded, stripped), or None. Only complete lines are consumed; a partial
    last line is read again on the next poll. An unreadable log is counted and retried, never fatal."""
    try:
        with open(LOG['path'], 'rb') as stream:
            size = stream.seek(0, 2)
            if size < LOG['offset']:
                LOG['offset'] = 0
            stream.seek(LOG['offset'])
            data = stream.read(size - LOG['offset'])
    except OSError as exc:
        LOG['read_errors'] += 1
        if LOG['read_errors'] == 1:
            print(stamp(), 'LOG read error (retrying):', repr(exc), flush=True)
        return None
    end = data.rfind(b'\n')
    if end < 0:
        return None
    hit = data.find(MARK, 0, end)
    if hit < 0:
        LOG['offset'] += end + 1
        return None
    stop = data.find(b'\n', hit)
    LOG['offset'] += stop + 1
    return data[data.rfind(b'\n', 0, hit) + 1:stop].decode('utf-8', 'replace').strip()


ap = argparse.ArgumentParser()
ap.add_argument('--pid', type=int, required=True)
ap.add_argument('--label', required=True)
ap.add_argument('--timeout-seconds', type=int, default=21600)
ap.add_argument('--log', default=None, help="the editor's -abslog file (launch_area_editor.ps1)")
a = ap.parse_args()
if a.log is not None:
    LOG['path'] = Path(a.log).resolve()
    assert LOG['path'].is_file(), '--log is not a file: %s' % LOG['path']
start = time.time()
last = None
outcome = {'kind': 'timeout'}
code = 4
while time.time() - start < a.timeout_seconds:
    t = tail()
    if t != last:
        print(stamp(), t[:200], flush=True)
        last = t
    if 'OWNER=NONE' in t and re.search(r'(?:^|\s)editor_PID=%d(?:\s|$)' % a.pid, t):   # whole PID only (review fix)
        phase = next((part.split('=', 1)[1] for part in t.split() if part.startswith('released_phase=')), '')
        outcome = {'kind': 'released', 'released_phase': phase, 'lease_line': t}
        code = 0 if phase.startswith('baked_saved') else 2
        if LOG['path'] is not None and code == 2:
            outcome['log_failure_line'] = (log_failure_line() or '')[:1000] or None
        break
    if LOG['path'] is not None:
        line = log_failure_line()
        if line is not None:
            print(stamp(), 'LOG', line[:300], flush=True)
            found = re.search(r'GeoCity (failed_[A-Za-z0-9_]+)', line)
            t2 = tail()                                                   # fail() releases before it logs (review fix: race)
            if 'OWNER=NONE' in t2 and re.search(r'(?:^|\s)editor_PID=%d(?:\s|$)' % a.pid, t2):
                phase = next((part.split('=', 1)[1] for part in t2.split() if part.startswith('released_phase=')), '')
                outcome = {'kind': 'released', 'released_phase': phase, 'lease_line': t2, 'log_failure_line': line[:1000]}
                code = 0 if phase.startswith('baked_saved') else 2
                break
            outcome = {'kind': 'failed_in_log', 'failed_phase': found.group(1) if found else None, 'log_line': line[:1000],
                       'lease_line': t, 'log_offset': LOG['offset']}
            code = 5
            break
    if not alive(a.pid):
        outcome = {'kind': 'editor_exited', 'lease_line': t}
        code = 3
        break
    time.sleep(20)
outcome['elapsed_s'] = round(time.time() - start)
if LOG['path'] is not None:
    outcome.update(log=str(LOG['path']), log_read_errors=LOG['read_errors'])
(TASK / 'receipts').mkdir(exist_ok=True)
(TASK / 'receipts' / ('WAIT_%s.json' % a.label)).write_text(json.dumps(outcome, indent=2), encoding='utf-8')
print(json.dumps(outcome))
sys.exit(code)
