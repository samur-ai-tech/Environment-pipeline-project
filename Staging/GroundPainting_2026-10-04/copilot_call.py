"""Use the installed UnrealCopilot MCP endpoint for a reviewed local script."""
import hashlib,json,sys,urllib.request
from pathlib import Path
URL='http://127.0.0.1:19840/mcp'
session=None
def send(payload):
    global session
    headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
    if session:headers['Mcp-Session-Id']=session
    req=urllib.request.Request(URL,json.dumps(payload).encode(),headers)
    with urllib.request.urlopen(req,timeout=60) as r:
        session=r.headers.get('Mcp-Session-Id',session)
        raw=r.read().decode()
    if not raw:return {}
    if raw.lstrip().startswith('{'):return json.loads(raw)
    events=[json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ')]
    return events[-1] if events else {'raw':raw}
send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Environmentpipeline new area operator','version':'1.0'}}})
send({'jsonrpc':'2.0','method':'notifications/initialized'})
script=Path(sys.argv[1]).resolve()
assert script.parent==Path(__file__).resolve().parent, 'Script must resolve to exact ground task directory'
pins=json.loads((Path(__file__).parent/'SCRIPT_PINS.json').read_text(encoding='utf-8'))
assert hashlib.sha256(script.read_bytes()).hexdigest()==pins[script.name], 'Unreviewed script bytes'
code=script.read_text(encoding='utf-8')
args=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig')) if len(sys.argv)>2 else {}
result=send({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'run_unreal_skill','arguments':{'python':code,'args':args}}})
body=result.get('result',{})
payload=body.get('structuredContent')
if payload is None:
    texts=[x['text'] for x in body.get('content',[]) if x.get('type')=='text']
    payload=json.loads(texts[0]) if texts else body
print(json.dumps(payload,ensure_ascii=False))
if body.get('isError') or payload.get('ok') is False or 'error' in result:sys.exit(1)
