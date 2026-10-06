import subprocess,json,sys,time
from pathlib import Path
r=Path(__file__).resolve().parent.parent
cases=[('sunrise',5.,'PresetPartlyCloudy',{}),('noon',12.,'PresetPartlyCloudy',{}),('sunset',18.5,'PresetPartlyCloudy',{}),('twilight',19.2,'PresetPartlyCloudy',{}),('night_clear',0.,'PresetClear',{}),('night_overcast',0.,'PresetOvercast',{}),('night_partly',0.,'PresetPartlyCloudy',{}),('moon_half',0.,'PresetClear',{'MoonPhase':.25}),('moon_disabled',0.,'PresetClear',{'MoonEnabled':False}),('stars_disabled',0.,'PresetClear',{'StarsEnabled':False}),('wrap_before',23.99,'PresetClear',{}),('wrap_after',.01,'PresetClear',{})]
results=[]
for name,hour,preset,extra in cases:
 vals={'TimeOfDay':hour,'CloudSpeed':0.,'MoonEnabled':True,'StarsEnabled':True,'MoonPhase':.5,'MoonBrightness':.006,'MoonDiskBrightness':.04,'StarBrightness':.02,'NightSkyFill':.12};vals.update(extra)
 (r/'REQUEST.json').write_text(json.dumps({'name':name,'preset':preset,'values':vals}))
 t=time.monotonic()
 p=subprocess.run([sys.executable,str(r/'sky_client.py'),str(r/'controls.py')],capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
 time.sleep(6)
 # One warm capture lets the renderer consume this case before retaining its view.
 p=subprocess.run([sys.executable,str(r/'capture.py'),'warm'],capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
 p=subprocess.run([sys.executable,str(r/'capture.py'),name],capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
 results.append({'case':name,'hour':hour,'preset':preset,'control_and_two_capture_wall_seconds':time.monotonic()-t})
 (r/'Resume/CAPTURE_CASES.json').write_text(json.dumps(results,indent=2))
 print(name,flush=True)
