"""Capture Lit viewport images through the in-editor unreal-mcp server (EditorAppToolset.CaptureViewport), read-only."""
import json, io, re, math, base64, struct, hashlib, sys, time, urllib.request
URL = 'http://127.0.0.1:8000/mcp'; H = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
label = sys.argv[1] if len(sys.argv) > 1 else 'r001'
def call(method, params, sid=None, id_=1):
    h = dict(H); h.update({'Mcp-Session-Id': sid} if sid else {})
    r = urllib.request.urlopen(urllib.request.Request(URL, data=json.dumps({'jsonrpc': '2.0', 'id': id_, 'method': method, 'params': params}).encode(), headers=h), timeout=180)
    body = r.read().decode('utf-8', 'replace'); sid = r.headers.get('Mcp-Session-Id') or sid
    m = re.findall(r'^data: (.*)$', body, re.M); return json.loads(m[-1] if m else body), sid
def rot(eye, tgt):
    dx, dy, dz = (tgt[i] - eye[i] for i in range(3)); h = math.hypot(dx, dy)
    return {'pitch': math.degrees(math.atan2(dz, h)), 'yaw': math.degrees(math.atan2(dy, dx)), 'roll': 0.0}
cams = json.load(io.open('CAMERAS_Iran_38196167_46086167_4km.json', encoding='utf-8'))
_, sid = call('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'claude-manager-capture', 'version': '1'}})
receipt = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'label': label, 'tool': 'EditorToolset.EditorAppToolset.CaptureViewport', 'shots': []}
for name, c in cams.items():
    if name.startswith('_'): continue
    tr = {'location': dict(zip('xyz', c['eye'])), 'rotation': rot(c['eye'], c['target']), 'scale': {'x': 1, 'y': 1, 'z': 1}}
    args = {'captureTransform': tr, 'bShowUI': False, 'annotations': {'gridSpacing': 0, 'gridExtent': 0, 'gridHeight': 0, 'maxLabelDistance': 0, 'classFilter': {'refPath': '/Script/Engine.Actor'}, 'maxLabels': 0}}  # server requires the field; zeros disable grid and labels
    res, _ = call('tools/call', {'name': 'call_tool', 'arguments': {'toolset_name': 'EditorToolset.EditorAppToolset', 'tool_name': 'CaptureViewport', 'arguments': args}}, sid, 2)
    out = {'shot': name, 'camera': c, 'rotation': tr['rotation']}
    content = res.get('result', {}).get('content', []); sc = res.get('result', {}).get('structuredContent')
    data = None; mime = None
    for part in content:
        if part.get('type') == 'image': data, mime = part.get('data'), part.get('mimeType')
    if data is None and sc:
        img = (sc.get('returnValue') or sc).get('image') or {}; data, mime = img.get('data'), img.get('mimeType')
    if data is None:
        txt = ''.join(p.get('text', '') for p in content if p.get('type') == 'text')
        m = re.search(r'"data":\s*"([A-Za-z0-9+/=]{100,})"', txt)
        if m: data = m.group(1); mime = 'image/png'
        else: out['error'] = (txt or json.dumps(res))[:600]
    if data:
        raw = base64.b64decode(data); w, h = struct.unpack('>II', raw[16:24]) if raw[:8] == b'\x89PNG\r\n\x1a\n' else (0, 0)
        p = f'Capture/IRAN_{name}_{label}.png'
        with open(p, 'xb') as f: f.write(raw)
        out.update({'png': p, 'width': w, 'height': h, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'landscape_orientation': w > h, 'mime': mime})
    receipt['shots'].append(out); print(json.dumps({k: v for k, v in out.items() if k != 'camera'}))
with open(f'CAPTURE_RECEIPT_{label}.json', 'x', encoding='utf-8') as f: json.dump(receipt, f, indent=1)
