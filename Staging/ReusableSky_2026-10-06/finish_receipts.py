import json,hashlib,datetime
from pathlib import Path
root=Path(__file__).resolve().parent;project=root.parent.parent
status=root/'STATUS.txt'
if status.exists() and not (root/'STATUS_BEFORE_PARALLEL_AUTHORIZATION.txt').exists():
 (root/'STATUS_BEFORE_PARALLEL_AUTHORIZATION.txt').write_bytes(status.read_bytes())
status.write_text('STAGE 1 IMPLEMENTED, SAVED AND FRESH-PROCESS REOPENED — 2026-10-06\n\nAsset: /Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky\nOriginal map: /Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration\nNative controls and editor behavior verified; morning/noon/evening images captured. Fresh PID28148 loaded the saved asset/map with no dirty packages. Both sky processes exited cleanly. The Asset Bank session was left untouched.\n\nRead RESULT.txt and QUICK_START.txt. Native receipts: CONTROL_VERIFICATION.json, NORTH_ARROW_VERIFIED.json, REOPEN_VERIFIED.json, EXIT_28148.json. Evidence is under Evidence/. Runtime PIE/packaged execution, second-map use, migration and user visual acceptance remain unverified. Clouds/haze/moon/stars are later stages.\n',encoding='utf-8')
a=json.loads((root/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
a.update(status='COMPLETE_SAVED_REOPEN_VERIFIED_EDITOR_RELEASED',editor_live=False,released_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plugin_activation='SunPosition enabled in project descriptor; fresh restart without launch flag verified',reopen_receipt='REOPEN_VERIFIED.json',exit_receipt='EXIT_28148.json')
(root/'ASSIGNMENT.json').write_text(json.dumps(a,indent=2),encoding='utf-8')
paths=['Content/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky.uasset','Content/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.umap','Environmentpipeline.uproject','AGENTS.md']
files=[]
for p in paths:
 f=project/p;assert f.is_file();files.append({'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
vendor=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/SunPosition/Content/SunSky.uasset')
files.append({'path':str(vendor),'sha256':hashlib.sha256(vendor.read_bytes()).hexdigest(),'saved_by_sky_task':False})
(root/'DELIVERY_FILES.json').write_text(json.dumps(files,indent=2))
print(json.dumps(files[:2],indent=2))
