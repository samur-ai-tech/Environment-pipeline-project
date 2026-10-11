"""Karmei Yosef operator (session 4a6a1d0c) PID-verified UnrealCopilot client, 2026-10-08. Fork of the manager's mgr_client.py (port 19852).
Runs ONE in-editor script from this Tools folder through run_unreal_skill on this task's own endpoint (19852).
    python -B mgr_client.py <Tools/script.py> [--args '<json>'] [--args-file <file.json>]
Refuses unless ../ASSIGNMENT_RUN.json says editor_live true for an integer PID with released_utc null and the 19852
listener is owned by exactly that PID. Receipts: ../receipts/CLIENT_<stem>_<utc>.json. Never touches another editor;
never reads the live WORKFLOW_STATE.json / BUILD_STATE.json.
"""
import datetime, hashlib, json, socket, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
TASK = TOOLS.parent
PORT = 19852
URL = 'http://127.0.0.1:%d/mcp' % PORT
TIMEOUT_S = 900


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def refuse(message):
    print(json.dumps({'ok': False, 'refused': message}))
    sys.exit(1)


def port_owner(port):
    out = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
                          'Get-NetTCPConnection -LocalPort %d -State Listen -ErrorAction Stop | '
                          'Select-Object -ExpandProperty OwningProcess -Unique' % port],
                         capture_output=True, text=True, timeout=60)
    return sorted({int(v) for v in out.stdout.split() if v.strip().isdigit()})


class Session:
    def __init__(self, url):
        self.url, self.sid = url, None

    def send(self, payload, timeout):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
        if self.sid:
            headers['Mcp-Session-Id'] = self.sid
        req = urllib.request.Request(self.url, json.dumps(payload).encode(), headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            self.sid = response.headers.get('Mcp-Session-Id', self.sid)
            raw = response.read().decode('utf-8', 'replace')
        if not raw:
            return {}
        if raw.lstrip().startswith('{'):
            return json.loads(raw)
        events = [json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ')]
        return events[-1] if events else {'raw': raw}


def parse_argv(argv):
    if len(argv) < 2:
        refuse("usage: mgr_client.py <Tools/script.py> [--args '<json>'] [--args-file <file.json>]")
    script = Path(argv[1]).resolve()
    extra, rest = {}, argv[2:]
    while rest:
        flag = rest.pop(0)
        if flag not in ('--args', '--args-file') or not rest:
            refuse('unknown or incomplete option: ' + flag)
        value = rest.pop(0)
        obj = json.loads(Path(value).read_text(encoding='utf-8-sig') if flag == '--args-file' else value)
        if not isinstance(obj, dict):
            refuse(flag + ' must be a JSON object')
        extra.update(obj)
    return script, extra


def main(argv):
    script, extra = parse_argv(argv)
    if script.parent != TOOLS or not script.is_file() or script.suffix != '.py':
        refuse('script must be a .py file in ' + str(TOOLS))
    data = script.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    assignment = json.loads((TASK / 'ASSIGNMENT_RUN.json').read_text(encoding='utf-8-sig'))
    pid = assignment.get('assigned_editor_PID')
    if assignment.get('editor_live') is not True or not isinstance(pid, int) or pid <= 0 or assignment.get('released_utc'):
        refuse('ASSIGNMENT_RUN.json has no live editor PID')
    if (assignment.get('control_endpoints') or {}).get('copilot') != URL:
        refuse('ASSIGNMENT_RUN copilot endpoint is not ' + URL)
    owners = port_owner(PORT)
    if owners != [pid]:
        refuse('Port %d is owned by %s, not the assigned editor PID %s' % (PORT, owners, pid))
    args = dict(extra)
    args.update(expected_pid=pid, script_sha256=sha, script_file=str(script))
    receipts = TASK / 'receipts'
    receipts.mkdir(exist_ok=True)
    record = receipts / ('CLIENT_%s_%s.json' % (script.stem, stamp()))
    entry = {'utc_start': utc(), 'script': str(script), 'script_sha256': sha, 'args': args, 'editor_pid': pid, 'endpoint': URL}
    session, exit_code = Session(URL), 0
    try:
        session.send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'KarmeiYosef 4a6a1d0c', 'version': '1.0'}}}, 60)
        session.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, 60)
        body = session.send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {
            'name': 'run_unreal_skill', 'arguments': {'python': data.decode('utf-8'), 'args': args}}}, TIMEOUT_S)
        result = body.get('result', {})
        payload = result.get('structuredContent')
        if payload is None:
            texts = [x.get('text', '') for x in result.get('content', []) if x.get('type') == 'text']
            try:
                payload = json.loads(texts[0]) if texts else result
            except Exception:
                payload = {'text': texts}
        entry.update(payload=payload, is_error=bool(result.get('isError')), rpc_error=body.get('error'))
        inner = payload.get('result') if isinstance(payload, dict) else None
        if (result.get('isError') or body.get('error') or (isinstance(payload, dict) and payload.get('ok') is False)
                or (isinstance(inner, dict) and inner.get('ok') is False)):
            exit_code = 1
    except (socket.timeout, TimeoutError) as exc:
        entry.update(status='CLIENT_TIMEOUT', error=repr(exc))
        exit_code = 1
    except (urllib.error.URLError, OSError, ValueError) as exc:
        timed_out = isinstance(getattr(exc, 'reason', None), (socket.timeout, TimeoutError))
        entry.update(status='CLIENT_TIMEOUT' if timed_out else 'CLIENT_ERROR', error=repr(exc))
        exit_code = 1
    entry['utc_end'], entry['exit_code'] = utc(), exit_code
    with open(record, 'x', encoding='utf-8') as stream:
        json.dump(entry, stream, indent=2, ensure_ascii=False, default=str)
    print(json.dumps({k: entry.get(k) for k in ('payload', 'status', 'error', 'exit_code')}, ensure_ascii=False, default=str)[:5000])
    print('call record: ' + str(record))
    sys.exit(exit_code)


if __name__ == '__main__':
    main(sys.argv)
