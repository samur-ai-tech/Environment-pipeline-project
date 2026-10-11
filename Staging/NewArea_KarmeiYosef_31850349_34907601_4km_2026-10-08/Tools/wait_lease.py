"""Outside the editor (Karmei Yosef operator, fork of the manager's wait_lease.py). Poll the EDITOR_OWNER.txt tail (never the live ledgers) until the sealed
run of --pid releases its lease, the editor exits, or --timeout-seconds pass. Prints one line per phase change seen in
the lease tail. Exit 0 = released baked_saved_verified; 2 = released in another phase (failed_*); 3 = editor exited
without release; 4 = timeout.
    python -B wait_lease.py --pid <pid> --label <label> [--timeout-seconds 21600]
"""
import argparse, datetime, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEASE = ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt'
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'


def tail():
    lines = [l for l in LEASE.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    return lines[-1] if lines else ''


def alive(pid):
    out = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', '(Get-Process -Id %d -ErrorAction SilentlyContinue) -ne $null' % pid],
                         capture_output=True, text=True, timeout=60)
    return out.stdout.strip().lower() == 'true'


ap = argparse.ArgumentParser()
ap.add_argument('--pid', type=int, required=True)
ap.add_argument('--label', required=True)
ap.add_argument('--timeout-seconds', type=int, default=21600)
a = ap.parse_args()
start = time.time()
last = None
outcome = {'kind': 'timeout'}
code = 4
while time.time() - start < a.timeout_seconds:
    t = tail()
    if t != last:
        print(datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%SZ'), t[:200], flush=True)
        last = t
    if ('OWNER=NONE' in t) and ('editor_PID=%d' % a.pid) in t:
        phase = next((part.split('=', 1)[1] for part in t.split() if part.startswith('released_phase=')), '')
        outcome = {'kind': 'released', 'released_phase': phase, 'lease_line': t}
        code = 0 if phase.startswith('baked_saved') else 2
        break
    if not alive(a.pid):
        outcome = {'kind': 'editor_exited', 'lease_line': t}
        code = 3
        break
    time.sleep(20)
outcome['elapsed_s'] = round(time.time() - start)
(TASK / 'receipts').mkdir(exist_ok=True)
(TASK / 'receipts' / ('WAIT_%s.json' % a.label)).write_text(json.dumps(outcome, indent=2), encoding='utf-8')
print(json.dumps(outcome))
sys.exit(code)
