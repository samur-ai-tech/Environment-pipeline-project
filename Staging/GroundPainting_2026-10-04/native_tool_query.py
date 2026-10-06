"""Use installed toolset metadata and inspected native tools through their MCP API."""
import json,sys,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
request=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'));sid=None
def send(d):
 global sid
 headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
 if sid:headers['Mcp-Session-Id']=sid
 with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/mcp',json.dumps(d).encode(),headers),timeout=50) as r:
  sid=r.headers.get('Mcp-Session-Id',sid);raw=r.read().decode()
 if not raw:return {}
 if raw.lstrip().startswith('{'):return json.loads(raw)
 return [json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ')][-1]
send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'GroundViewportInspection','version':'1'}}})
send({'jsonrpc':'2.0','method':'notifications/initialized'})
r=send({'jsonrpc':'2.0','id':2,'method':'tools/call','params':request})
out=HERE/'Revision_2026-10-05'/Path(sys.argv[2]).name
assert not out.exists(),'Preserve prior native tool receipt'
out.write_text(json.dumps(r,indent=2),encoding='utf-8')
print(json.dumps(r,ensure_ascii=False)[:22000])
