"""Use installed native toolset capture; save pixels without dumping base64."""
import base64,json,sys,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
session=None
def send(payload):
 global session
 headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
 if session:headers['Mcp-Session-Id']=session
 req=urllib.request.Request('http://127.0.0.1:8000/mcp',json.dumps(payload).encode(),headers)
 with urllib.request.urlopen(req,timeout=50) as r:session=r.headers.get('Mcp-Session-Id',session);raw=r.read().decode()
 if not raw:return {}
 if raw.lstrip().startswith('{'):return json.loads(raw)
 events=[json.loads(l[6:]) for l in raw.splitlines() if l.startswith('data: ')];return events[-1] if events else {}
send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Ground-only native capture','version':'1'}}})
send({'jsonrpc':'2.0','method':'notifications/initialized'})
name=sys.argv[1] if len(sys.argv)>1 else 'CaptureEditorImage'
toolset=sys.argv[2] if len(sys.argv)>2 else 'EditorToolset.EditorAppToolset'
args={'view':'Current','width':1600,'height':1000,'bWaitForRebuild':False,'bRestoreCamera':False} if toolset.startswith('RoadBLD') else {}
response=send({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'call_tool','arguments':{'toolset_name':toolset,'tool_name':name,'arguments':args}}})
content=response.get('result',{}).get('content',[])
for b in content:
 if b.get('type')=='text':
  try:d=json.loads(b['text'])
  except Exception:print(b['text'][:1200]);continue
  d=d.get('returnValue',d)
  im=d.get('image',d);data=im.pop('data','')
  if data:
   out=HERE/'Images'/(sys.argv[3] if len(sys.argv)>3 else f'{name}.png');out.write_bytes(base64.b64decode(data));im['file']=str(out)
   (HERE/('NATIVE_'+out.stem+'.json')).write_text(json.dumps(d,indent=2),encoding='utf-8')
  print(json.dumps(d))
 elif b.get('type')=='image':
  out=HERE/'Images'/(sys.argv[3] if len(sys.argv)>3 else f'{name}.png');out.write_bytes(base64.b64decode(b['data']));print(json.dumps({'file':str(out)}))
