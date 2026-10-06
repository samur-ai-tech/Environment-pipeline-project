import json,subprocess,time,shutil,sys,csv,statistics
from pathlib import Path
root=Path(__file__).resolve().parent;project=root.parent.parent.parent
out=root/'Performance';out.mkdir(exist_ok=True)
csvdir=project/'Saved/Profiling/CSV'
def run(script):
 r=subprocess.run([sys.executable,str(root/'sky_client.py'),str(root/script)],capture_output=True,text=True,timeout=180)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
def quantile(vals,q):
 s=sorted(vals);return s[round((len(s)-1)*q)]
results=[]
cases=[('clear_B','PresetClear',False),('clear_H','PresetClear',True),('partly_H','PresetPartlyCloudy',True),('partly_B','PresetPartlyCloudy',False),('overcast_B','PresetOvercast',False),('overcast_H','PresetOvercast',True)]
for name,preset,high in cases:
 (root/'REQUEST.json').write_text(json.dumps({'name':name,'preset':preset,'values':{'HighQuality':high,'CloudSpeed':0.0,'TimeOfDay':12.0}}))
 run('controls.py');time.sleep(8)
 before=set(csvdir.glob('*.csv'));run('performance_start.py')
 deadline=time.monotonic()+40;new=[]
 while time.monotonic()<deadline:
  new=list(set(csvdir.glob('*.csv'))-before)
  try:
   if new and b'[HasHeaderRowAtEnd]' in new[0].read_bytes():break
  except PermissionError:pass
  time.sleep(1)
 assert len(new)==1,(name,new)
 time.sleep(2)
 dest=out/(name+'.csv');shutil.copy2(new[0],dest)
 with dest.open() as f:rows=list(csv.reader(f))
 assert rows[-1][0]=='[HasHeaderRowAtEnd]', 'Capture not finalized'
 header=rows[-2];data=[row+['0']*(len(header)-len(row)) for row in rows[:-2] if row and row[0]!='EVENTS']
 assert len(data)==180, len(data)
 metrics={}
 for col in ['FrameTime','GPU/FrameTime','GPU/Total','GPU/VolumetricCloud','GPU/VolumetricCloudShadow','GPU/VolCloudReconstruction','GPU/VolCloudComposeOverScene']:
  if col not in header:continue
  i=header.index(col);v=[]
  for row in data[30:]:
   try:v.append(float(row[i]))
   except ValueError:pass
  if v:metrics[col]={'n':len(v),'median_ms':statistics.median(v),'p10_ms':quantile(v,.1),'p90_ms':quantile(v,.9)}
 result={'case':name,'preset':preset,'high':high,'metrics':metrics,'gpu_columns':[c for c in header if c.startswith('GPU/') and ('Cloud' in c or 'Frame' in c or 'Total' in c)],'raw_csv':str(dest)}
 results.append(result);(root/'PERFORMANCE_RESULTS.json').write_text(json.dumps(results,indent=2));print(json.dumps(result),flush=True)
