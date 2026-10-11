"""Host-side driver (Karmei Yosef operator, play-mode test 2026-10-10). Runs pie_test.py steps on the live editor through
ky_client.py: start PIE, for each camera move -> wait for streaming -> HighResShot -> 8 s CSV profile; collects the newest
screenshot / CSV into receipts/Captures/PIE_<label>_<cam>.png and receipts/PIE/<label>_<cam>.csv and summarises frame times.
    python pie_run.py <label> <cameras.json>
"""
import csv, glob, json, os, shutil, statistics, subprocess, sys, time
from pathlib import Path
TOOLS = Path(__file__).resolve().parent; TASK = TOOLS.parent
ROOT = TASK.parents[1]
PY = r'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
label, cams = sys.argv[1], json.loads(Path(sys.argv[2]).read_text())
SHOTS = ROOT / 'Saved' / 'Screenshots' / 'WindowsEditor'
CSVD = ROOT / 'Saved' / 'Profiling' / 'CSV'
OUTC = TASK / 'receipts' / 'Captures'; OUTP = TASK / 'receipts' / 'PIE'; OUTP.mkdir(exist_ok=True)


def call(args):
    r = subprocess.run([PY, '-B', str(TOOLS / 'ky_client.py'), str(TOOLS / 'pie_test.py'), '--args', json.dumps(args)], capture_output=True, text=True, timeout=600)
    line = r.stdout.splitlines()[0] if r.stdout else ''
    try:
        return json.loads(line).get('payload', {}).get('result')
    except Exception:
        return {'raw': r.stdout[:300], 'err': r.stderr[:300]}


def newest(d, pat, after):
    fs = [Path(f) for f in glob.glob(str(d / pat))]
    fs = [f for f in fs if f.stat().st_mtime > after]
    return max(fs, key=lambda f: f.stat().st_mtime) if fs else None


def summarise(path):
    with open(path, newline='', encoding='utf-8', errors='replace') as fh:
        rows = list(csv.reader(fh))
    head = rows[0]; data = [r for r in rows[1:] if len(r) == len(head)]
    out = {'frames': len(data)}
    for col in ('FrameTime', 'GameThreadTime', 'RenderThreadTime', 'GPUTime', 'RHIThreadTime', 'MemoryFreeMB', 'PhysicalUsedMB', 'DrawCalls', 'PrimitivesDrawn'):
        if col in head:
            vals = []
            for r in data:
                try:
                    vals.append(float(r[head.index(col)]))
                except ValueError:
                    pass
            if vals:
                out[col] = {'mean': round(statistics.mean(vals), 2), 'p95': round(sorted(vals)[int(0.95 * (len(vals) - 1))], 2)}
    out['columns_with'] = [c for c in head if any(k in c for k in ('DrawCall', 'Primitive', 'Memory', 'GPU'))][:20]
    return out


res = {'label': label, 'unthrottle': call({'step': 'unthrottle'}), 'start': call({'step': 'start'})}
time.sleep(20)
res['state0'] = call({'step': 'state'})
for name, cam in cams.items():
    r = {'move': call({'step': 'move', 'eye': cam['eye'], 'target': cam['target']})}
    time.sleep(10)
    r['state'] = call({'step': 'state'})
    t0 = time.time(); call({'step': 'shot'}); time.sleep(4)
    s = newest(SHOTS, '*.png', t0 - 1)
    if s:
        dst = OUTC / ('PIE_%s_%s.png' % (label, name)); shutil.copy2(s, dst); r['shot'] = str(dst)
    t1 = time.time(); call({'step': 'csv_start'}); time.sleep(8); call({'step': 'csv_stop'}); time.sleep(4)
    c = newest(CSVD, '*.csv', t1 - 1)
    if c:
        dst = OUTP / ('%s_%s.csv' % (label, name)); shutil.copy2(c, dst); r['csv'] = str(dst); r['frames'] = summarise(dst)
    res[name] = r
res['stop'] = call({'step': 'stop'})
(OUTP / ('PIE_%s.json' % label)).write_text(json.dumps(res, indent=1), encoding='utf-8')
for name in cams:
    f = res[name].get('frames', {})
    st = res[name].get('state') or {}
    print(name, 'frames', f.get('frames'), 'FrameTime', f.get('FrameTime'), 'GPU', f.get('GPUTime'), 'GT', f.get('GameThreadTime'), 'RT', f.get('RenderThreadTime'),
          '| actors', st.get('actors'), 'hlod vis/hid', st.get('hlod_visible'), st.get('hlod_hidden'), '| shot', bool(res[name].get('shot')))
print('state0', json.dumps(res['state0'])[:400])
