"""Karmei Yosef capture via the editor's native MCP (port 8012) EditorAppToolset.CaptureViewport, read-only. Fork of the manager's mgr_capture.py.
owner's capture_lit.py. Refuses unless ../ASSIGNMENT_RUN.json is live and port 8012 is owned by that PID.
    python -B mgr_capture.py --label <label> --cameras <json file: {name: {eye:[x,y,z], target:[x,y,z]}}>
"""
import argparse, base64, json, math, re, subprocess, time, urllib.request
from pathlib import Path
TOOLS = Path(__file__).resolve().parent; TASK = TOOLS.parent
PORT = 8012; URL = 'http://127.0.0.1:%d/mcp' % PORT
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}

def port_owner(port):
    out = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
                          'Get-NetTCPConnection -LocalPort %d -State Listen -ErrorAction Stop | Select-Object -ExpandProperty OwningProcess -Unique' % port],
                         capture_output=True, text=True, timeout=60)
    return sorted({int(v) for v in out.stdout.split() if v.strip().isdigit()})

def call(method, params, sid=None, id_=1):
    headers = dict(HEADERS)
    if sid: headers['Mcp-Session-Id'] = sid
    req = urllib.request.Request(URL, data=json.dumps({'jsonrpc': '2.0', 'id': id_, 'method': method, 'params': params}).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode('utf-8', 'replace'); sid = r.headers.get('Mcp-Session-Id') or sid
    found = re.findall(r'^data: (.*)$', body, re.M)
    return json.loads(found[-1] if found else body), sid

def rot(eye, target):
    dx, dy, dz = (target[i] - eye[i] for i in range(3)); h = math.hypot(dx, dy)
    return {'pitch': math.degrees(math.atan2(dz, h)), 'yaw': math.degrees(math.atan2(dy, dx)), 'roll': 0.0}

def capture(sid, camera):
    transform = {'location': dict(zip('xyz', camera['eye'])), 'rotation': rot(camera['eye'], camera['target']), 'scale': {'x': 1, 'y': 1, 'z': 1}}
    args = {'captureTransform': transform, 'bShowUI': False,
            'annotations': {'gridSpacing': 0, 'gridExtent': 0, 'gridHeight': 0, 'maxLabelDistance': 0, 'classFilter': {'refPath': '/Script/Engine.Actor'}, 'maxLabels': 0}}
    res, _ = call('tools/call', {'name': 'call_tool', 'arguments': {'toolset_name': 'EditorToolset.EditorAppToolset', 'tool_name': 'CaptureViewport', 'arguments': args}}, sid, 2)
    content = res.get('result', {}).get('content', []); sc = res.get('result', {}).get('structuredContent'); data = None
    for part in content:
        if part.get('type') == 'image': data = part.get('data')
    if data is None and sc: data = ((sc.get('returnValue') or sc).get('image') or {}).get('data')
    if data is None:
        txt = ''.join(x.get('text', '') for x in content if x.get('type') == 'text'); found = re.search(r'"data":\s*"([A-Za-z0-9+/=]{100,})"', txt)
        if not found: return None, transform['rotation'], (txt or json.dumps(res))[:600]
        data = found.group(1)
    return base64.b64decode(data), transform['rotation'], None

ap = argparse.ArgumentParser(); ap.add_argument('--label', required=True); ap.add_argument('--cameras', required=True); a = ap.parse_args()
assignment = json.loads((TASK / 'ASSIGNMENT_RUN.json').read_text(encoding='utf-8-sig'))
pid = assignment.get('assigned_editor_PID')
assert assignment.get('editor_live') is True and not assignment.get('released_utc'), 'no live run editor'
assert port_owner(PORT) == [pid], 'port %d not owned by %s' % (PORT, pid)
cams = json.loads(Path(a.cameras).read_text(encoding='utf-8-sig'))
out_dir = TASK / 'receipts' / 'Captures'; out_dir.mkdir(parents=True, exist_ok=True)
_, sid = call('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'KarmeiYosef 4a6a1d0c', 'version': '1.0'}})
try: call('notifications/initialized', {}, sid)
except Exception: pass
receipt = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'pid': pid, 'label': a.label, 'shots': []}
for name, camera in cams.items():
    raw, rotation, error = capture(sid, camera); shot = {'shot': name, 'camera': camera, 'rotation': rotation, 'error': error}
    if raw:
        png = out_dir / ('%s_%s.png' % (a.label, name)); png.write_bytes(raw); shot.update(png=str(png), bytes=len(raw))
    receipt['shots'].append(shot); print(json.dumps({k: v for k, v in shot.items() if k != 'camera'}))
(out_dir / ('CAPTURE_%s.json' % a.label)).write_text(json.dumps(receipt, indent=1), encoding='utf-8')
