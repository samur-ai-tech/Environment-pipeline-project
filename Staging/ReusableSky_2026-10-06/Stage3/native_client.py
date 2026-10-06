import json,sys,urllib.request,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parent
session=None
def send(payload):
 global session
 headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
 if session:headers['Mcp-Session-Id']=session
 req=urllib.request.Request('http://127.0.0.1:8001/mcp',json.dumps(payload).encode(),headers)
 with urllib.request.urlopen(req,timeout=120) as r:
  session=r.headers.get('Mcp-Session-Id',session);raw=r.read().decode()
 if not raw:return {}
 if raw.lstrip().startswith('{'):return json.loads(raw)
 return [json.loads(l[6:]) for l in raw.splitlines() if l.startswith('data: ')][-1]
send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Sky only native capture','version':'1'}}})
send({'jsonrpc':'2.0','method':'notifications/initialized'})
if len(sys.argv)==1:
 result=send({'jsonrpc':'2.0','id':2,'method':'tools/list'})
 filtered=[t for t in result.get('result',{}).get('tools',[]) if any(k in t['name'].lower() for k in ['captureviewport','setviewport','getviewport'])]
 (ROOT/'NATIVE_CAPTURE_SCHEMA.json').write_text(json.dumps(filtered,indent=2));print(json.dumps(filtered))
else:
 args=json.loads((ROOT/sys.argv[1]).read_text())
 result=send({'jsonrpc':'2.0','id':2,'method':'tools/call','params':args})
 (ROOT/'CAPTURE_RESPONSE.json').write_text(json.dumps(result))
 print(str(result)[:400])
