r"""S1 pinned runner (Windows Python, run OUTSIDE the editor; never imports unreal).

Sends one pinned S1_Prep script to the single running editor through the UnrealCopilot MCP endpoint
(run_unreal_skill with inline python: ARGS global in, RESULT out). Same channel and response handling as
Staging/GroundPainting_2026-10-04/copilot_call.py (receipts LAUNCH_PID*.json + ARGS_capture_*.json -> CAPTURE_*.json)
and Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/copilot_client.py. The plugin execs the text on the game
thread through a FIFO queue, with no __file__ (Plugins/UnrealCopilot/Content/Python/unreal_copilot/
skills/runner.py:98-107, :221-236; execution.py:58-92).

Usage (paths may be relative to the current directory):
  python -B run_s1.py s1_material_edit.py <args.json> [--timeout SEC]
      three calls: s1_set_args.py set {path, sha256} -> the EDIT file text -> s1_set_args.py clear.
      The clear is always sent (also after a failure or timeout); the FIFO queue runs it after EDIT.
  python -B run_s1.py s1_verify.py <verify_args.json> [--timeout SEC]
  python -B run_s1.py s1_capture.py <begin_args.json>                       (mode=begin)
  python -B run_s1.py s1_capture.py <begin_args.json> --phase prepare|request|complete --index N
  python -B run_s1.py s1_capture.py <begin_args.json> --phase end [--cancel]
  python -B run_s1.py s1_capture.py <begin_args.json> --phase status
      phase ARGS are derived from the begin file: {mode, expected_pid, label[, index][, cancel]}.
  python -B run_s1.py --env-status | --clear-env

Refuses before sending anything (exit 2) when: this runner, s1_set_args.py or the target script differs from
S1_Prep/SCRIPT_PINS.json; the target is not one of the three in-editor S1 scripts; the args file is not a .json
under Stage1_Ground; EDIT args do not name executed_script_file = S1_Prep/s1_material_edit.py and
script_sha256 = its pin; s1_verify args do not name verifier_file = S1_Prep/s1_verify.py and its pin.
The pinned bytes are read once, hashed and decoded (universal newlines, as read_text in copilot_call.py).
Exit: 0 ok; 1 tool/script error or ok false; 2 refused before sending; 3 HTTP timeout. A timeout is NOT an
abort: the call keeps running in the editor; read S1_Prep/receipts/, the *_ONCE*.json latches and
CAPTURE_<label>.json before anything else.
"""
import argparse
import hashlib
import json
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = 'http://127.0.0.1:19840/mcp'  # GroundPainting_2026-10-04/copilot_call.py:4
HERE = Path(__file__).resolve().parent             # .../Stage1_Ground/S1_Prep
STAGE = HERE.parent                                # .../Stage1_Ground
PINS = HERE / 'SCRIPT_PINS.json'
SETTER = 's1_set_args.py'
EDIT, VERIFY, CAPTURE = 's1_material_edit.py', 's1_verify.py', 's1_capture.py'
IN_EDITOR = (EDIT, VERIFY, CAPTURE)
PHASES = ('prepare', 'request', 'complete', 'end', 'status')
session = None


class Refused(Exception):
    pass


class Timeout(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def pins():
    try:
        table = json.loads(PINS.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as error:
        raise Refused('SCRIPT_PINS.json unreadable: %r' % (error,))
    me = Path(__file__).resolve()
    if table.get(me.name) != sha(me.read_bytes()):
        raise Refused('run_s1.py bytes differ from SCRIPT_PINS.json (re-pin after review)')
    return table


def pinned_code(table, name):
    """Read once, hash those bytes, decode them (universal newlines, like Path.read_text)."""
    file = (HERE / name).resolve()
    if file.parent != HERE or name not in table or not file.is_file():
        raise Refused('script is not a pinned S1_Prep file: ' + name)
    data = file.read_bytes()
    if sha(data) != table[name]:
        raise Refused('Unreviewed script bytes (SCRIPT_PINS.json): ' + name)
    return data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n'), table[name]


def args_file(value):
    try:
        file = Path(value).resolve(strict=True)
        if not (file.is_relative_to(STAGE) and file.suffix == '.json'):
            raise Refused('args must be a .json file under Stage1_Ground: ' + str(file))
        data = file.read_bytes()
        return file, sha(data), json.loads(data.decode('utf-8-sig'))
    except (OSError, ValueError) as error:
        raise Refused('args file unreadable: %r' % (error,))


def send(payload, timeout):
    global session
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if session:
        headers['Mcp-Session-Id'] = session
    request = urllib.request.Request(URL, json.dumps(payload).encode(), headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            session = response.headers.get('Mcp-Session-Id', session)
            raw = response.read().decode()
    except (socket.timeout, TimeoutError) as error:
        raise Timeout(repr(error))
    except urllib.error.URLError as error:
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            raise Timeout(repr(error))
        raise
    if not raw:
        return {}
    if raw.lstrip().startswith('{'):
        return json.loads(raw)
    events = [json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ')]
    return events[-1] if events else {'raw': raw}


def connect(timeout):
    send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
          'params': {'protocolVersion': '2024-11-05', 'capabilities': {},
                     'clientInfo': {'name': 'Environmentpipeline S1 runner', 'version': '1.0'}}}, timeout)
    send({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, timeout)


def call(step, code, args, timeout):
    """One run_unreal_skill call. Returns a step row; ok is False on any tool, runner or script failure."""
    row = {'step': step, 'utc': utc()}
    try:
        result = send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                       'params': {'name': 'run_unreal_skill', 'arguments': {'python': code, 'args': args}}}, timeout)
    except Timeout as error:
        row.update(ok=False, timeout=True, error=str(error),
                   note='HTTP timeout is NOT an abort: the call keeps running in the editor; read receipts first')
        return row
    except Exception as error:  # transport failure (no editor/endpoint, reset): outcome unknown, read receipts
        row.update(ok=False, timeout=False, transport_error=repr(error))
        return row
    body = result.get('result', {}) if isinstance(result, dict) else {}
    payload = body.get('structuredContent')
    if payload is None:
        texts = [x['text'] for x in body.get('content', []) if x.get('type') == 'text']
        try:
            payload = json.loads(texts[0]) if texts else body
        except Exception:
            payload = {'text': texts}
    if isinstance(payload, dict) and 'ok' not in payload and isinstance(payload.get('result'), dict) \
            and 'ok' in payload['result']:
        payload = payload['result']  # FastMCP wrapper, if any
    inner = payload.get('result') if isinstance(payload, dict) else None
    ok = not (body.get('isError') or 'error' in result or not isinstance(payload, dict) or payload.get('ok') is False
              or (isinstance(inner, dict) and inner.get('ok') is False))
    row.update(ok=bool(ok), timeout=False, payload=payload)
    if 'error' in result:
        row['rpc_error'] = result['error']
    return row


def finish(summary, rows, code):
    summary.update(steps=rows, exit=code, finished_utc=utc())
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    return code


def main(argv=None):
    ap = argparse.ArgumentParser(description='S1 pinned runner (see module docstring)')
    ap.add_argument('script', nargs='?')
    ap.add_argument('args', nargs='?')
    ap.add_argument('--timeout', type=float, default=1800.0, help='HTTP wait per call, seconds (default 1800)')
    ap.add_argument('--phase', choices=PHASES)
    ap.add_argument('--index', type=int)
    ap.add_argument('--cancel', action='store_true')
    ap.add_argument('--env-status', action='store_true')
    ap.add_argument('--clear-env', action='store_true')
    a = ap.parse_args(argv)
    summary = {'runner': 'run_s1.py', 'started_utc': utc(), 'url': URL}
    rows = []
    try:
        table = pins()
        setter_code, setter_sha = pinned_code(table, SETTER)
        summary['runner_sha256'] = table['run_s1.py']
        if a.env_status or a.clear_env:
            if a.script or a.args:
                raise Refused('--env-status/--clear-env take no script or args')
            connect(60.0)
            rows.append(call('env_clear' if a.clear_env else 'env_status', setter_code,
                             {'action': 'clear' if a.clear_env else 'status', 'expected_path': None}, 60.0))
            return finish(summary, rows, 0 if rows[-1]['ok'] else (3 if rows[-1]['timeout'] else 1))
        if not a.script or not a.args:
            raise Refused('usage: run_s1.py <s1_material_edit.py|s1_verify.py|s1_capture.py> <args.json> [...]')
        name = Path(a.script).name
        if name not in IN_EDITOR or Path(a.script).resolve() != (HERE / name).resolve():
            raise Refused('only S1_Prep/{%s} may be sent to the editor' % ', '.join(IN_EDITOR))
        code, script_sha = pinned_code(table, name)
        file, file_sha, args = args_file(a.args)
        summary.update(script=str(HERE / name), script_sha256=script_sha, args_file=str(file), args_sha256=file_sha,
                       setter_sha256=setter_sha)
        if name != CAPTURE and (a.phase or a.index is not None or a.cancel):
            raise Refused('--phase/--index/--cancel apply to s1_capture.py only')
        if name == EDIT:
            if Path(str(args.get('executed_script_file') or '')).resolve() != (HERE / EDIT).resolve():
                raise Refused('EDIT args executed_script_file must be ' + str(HERE / EDIT))
            if args.get('script_sha256') != script_sha:
                raise Refused('EDIT args script_sha256 differs from the SCRIPT_PINS.json pin')
            summary['mode'] = args.get('mode')
            connect(60.0)
            rows.append(call('env_set', setter_code, {'action': 'set', 'path': str(file), 'sha256': file_sha}, a.timeout))
            if rows[-1]['ok']:
                rows.append(call('edit', code, {}, a.timeout))
            clear = call('env_clear', setter_code, {'action': 'clear', 'expected_path': str(file)},
                         60.0 if any(r['timeout'] for r in rows) else a.timeout)
            rows.append(clear)
            main_row = rows[1] if len(rows) == 3 else rows[0]
            if main_row['timeout']:
                return finish(summary, rows, 3)
            return finish(summary, rows, 0 if all(r['ok'] for r in rows) else 1)
        if name == VERIFY:
            if Path(str(args.get('verifier_file') or '')).resolve() != (HERE / VERIFY).resolve() \
                    or args.get('verifier_sha256') != script_sha:
                raise Refused('s1_verify args must name verifier_file=%s and verifier_sha256=its pin' % (HERE / VERIFY))
            send_args = args
        else:
            if a.phase is None:
                if args.get('mode') != 'begin' or a.index is not None or a.cancel:
                    raise Refused('a capture args file is a begin file (mode=begin); phases use --phase')
                send_args = args
            else:
                if args.get('mode') != 'begin':
                    raise Refused('--phase derives its ARGS from the begin file (mode=begin)')
                send_args = {'mode': a.phase, 'expected_pid': args.get('expected_pid'), 'label': args.get('label')}
                if a.phase in ('prepare', 'request', 'complete'):
                    if a.index is None:
                        raise Refused('--index is required for ' + a.phase)
                    send_args['index'] = a.index
                elif a.index is not None:
                    raise Refused('--index applies to prepare/request/complete only')
                if a.cancel:
                    if a.phase != 'end':
                        raise Refused('--cancel applies to --phase end only')
                    send_args['cancel'] = True
            summary['capture_args_sent'] = send_args
        connect(60.0)
        rows.append(call(name, code, send_args, a.timeout))
        return finish(summary, rows, 0 if rows[-1]['ok'] else (3 if rows[-1]['timeout'] else 1))
    except Refused as error:
        summary['refused'] = str(error)
        return finish(summary, rows, 2)
    except Timeout as error:  # during connect: nothing was sent to run
        summary['connect_timeout'] = str(error)
        return finish(summary, rows, 3)
    except (urllib.error.URLError, OSError) as error:  # during connect: no editor endpoint
        summary['connect_error'] = repr(error)
        return finish(summary, rows, 1)


if __name__ == '__main__':
    sys.exit(main())
