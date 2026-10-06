import json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
cases=[('clear_noon','PresetClear',{'TimeOfDay':12.0,'CloudSpeed':0.0,'HighQuality':False}),('partly_noon_balanced','PresetPartlyCloudy',{'HighQuality':False}),('partly_noon_high',None,{'HighQuality':True}),('overcast_noon','PresetOvercast',{'HighQuality':False}),('hazy_noon','PresetHazy',{}),('partly_morning','PresetPartlyCloudy',{'TimeOfDay':6.0}),('partly_evening',None,{'TimeOfDay':18.0}),('motion_start',None,{'TimeOfDay':12.0,'CloudSpeed':20.0,'CloudDirection':90.0}),('motion_after_10s',None,{})]
for name,preset,values in cases:
 (root/'REQUEST.json').write_text(json.dumps({'name':name,'preset':preset,'values':values}))
 for cmd in [[sys.executable,str(root/'sky_client.py'),str(root/'controls.py')]]:
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
  if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 time.sleep(10)
 r=subprocess.run([sys.executable,str(root/'capture.py'),name],capture_output=True,text=True,timeout=180)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 print(name,flush=True)
