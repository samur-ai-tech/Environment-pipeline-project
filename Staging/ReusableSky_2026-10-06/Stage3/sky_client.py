"""PID-bound client for the dedicated sky editor's existing UnrealCopilot MCP."""
import json, sys, urllib.request, textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parent
A=json.loads((ROOT/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
URL=A['copilot_endpoint']
assert URL=='http://127.0.0.1:19841/mcp'
session=None
def send(payload):
    global session
    headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
    if session: headers['Mcp-Session-Id']=session
    req=urllib.request.Request(URL,json.dumps(payload).encode(),headers)
    with urllib.request.urlopen(req,timeout=180) as res:
        session=res.headers.get('Mcp-Session-Id',session); raw=res.read().decode()
    if not raw:return {}
    if raw.lstrip().startswith('{'):return json.loads(raw)
    return [json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ')][-1]
send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'ReusableSky dedicated operator','version':'1.0'}}})
send({'jsonrpc':'2.0','method':'notifications/initialized'})
script=Path(sys.argv[1]).resolve()
assert script.is_relative_to(ROOT), 'Only reviewed sky staging scripts are dispatched'
guard='import os, unreal\nassert os.getpid()=='+str(A['assigned_editor_PID'])+', "WRONG EDITOR PID"\n'
guard+='sky_guard_sub=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)\nsky_guard_world=sky_guard_sub.get_editor_world() or sky_guard_sub.get_game_world()\nassert sky_guard_world and sky_guard_world.get_outermost().get_path_name().replace("/UEDPIE_0_","/")=='+repr(A['map'])+', "WRONG MAP"\n'
result=send({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'run_unreal_skill','arguments':{'python':guard+'import toolset_registry\nwith toolset_registry.tool_raising_exceptions():\n'+textwrap.indent(script.read_text(encoding='utf-8-sig'),'    ')}}})
body=result.get('result',{})
payload=body.get('structuredContent')
if payload is None:
    texts=[c['text'] for c in body.get('content',[]) if c.get('type')=='text']
    try:payload=json.loads(texts[0]) if texts else body
    except Exception:payload={'text':texts}
out=ROOT/'Calls';out.mkdir(exist_ok=True)
(out/(script.stem+'.json')).write_text(json.dumps(payload,indent=2),encoding='utf-8')
print(json.dumps(payload,ensure_ascii=False)[:18000])
if body.get('isError') or 'error' in result or payload.get('ok') is False:sys.exit(1)
