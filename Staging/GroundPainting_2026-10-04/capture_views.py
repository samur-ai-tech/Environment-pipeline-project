import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
area,stage=sys.argv[1:3]
shots=sys.argv[3:] or ['close','middle','wide']
for shot in shots:
 args=HERE/'capture_args.json';args.write_text(json.dumps({'stage':stage,'shot':shot}))
 r=subprocess.run([sys.executable,str(HERE/'copilot_call.py'),str(HERE/'native_capture.py'),str(args)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 request=json.loads(r.stdout)['result'];assert request['area']==area
 r=subprocess.run([sys.executable,str(HERE/'tool_capture.py'),'CaptureViewport','RoadBLDToolset.RoadBLDFeedbackToolset',f'{area}_{stage}_{shot}_native.png'],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 native=json.loads(r.stdout);assert 'image' in native,native
 eye=request['camera']['eye'];actual=native['cameraLocation'];assert all(abs(eye[i]-actual[k])<.01 for i,k in enumerate(('x','y','z')))
 image=Path(request['path'])
 deadline=time.monotonic()+12
 while not image.exists() and time.monotonic()<deadline:time.sleep(.25)
 assert image.exists(),request
 print(json.dumps({'area':area,'stage':stage,'shot':shot,'file':str(image),'bytes':image.stat().st_size,'camera_matched':True}),flush=True)
