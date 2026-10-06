import sys,json,base64
label=sys.argv[1];sys.argv=sys.argv[:1]
import native_client as n
args={'captureTransform':{'location':{'x':-8268,'y':-6591,'z':11552},'rotation':{'pitch':-15,'yaw':52,'roll':0},'scale':{'x':1,'y':1,'z':1}},'annotations':{'gridSpacing':0,'gridExtent':0,'gridHeight':0,'maxLabelDistance':0,'maxLabels':0},'bShowUI':False}
if (n.ROOT/'CAMERA.json').exists():args['captureTransform']=json.loads((n.ROOT/'CAMERA.json').read_text(encoding='utf-8-sig'))
r=n.send({'jsonrpc':'2.0','id':8,'method':'tools/call','params':{'name':'call_tool','arguments':{'toolset_name':'EditorToolset.EditorAppToolset','tool_name':'CaptureViewport','arguments':args}}})
folder=n.ROOT/'Evidence';folder.mkdir(exist_ok=True)
for c in r.get('result',{}).get('content',[]):
 if c['type']=='image':
  p=folder/(label+'.png');p.write_bytes(base64.b64decode(c['data']));print(p)
 elif c['type']=='text':
  d=json.loads(c['text']);im=d.get('returnValue',{}).pop('image',{})
  if isinstance(im,dict):
   b=im.get('data') or im.get('base64Data') or im.get('base64')
   if b:
    p=folder/(label+'.png');p.write_bytes(base64.b64decode(b));print(p)
  (folder/(label+'.json')).write_text(json.dumps(d,indent=2));print(str(d)[:500]);print('imagekeys',list(im) if isinstance(im,dict) else str(im)[:100])
