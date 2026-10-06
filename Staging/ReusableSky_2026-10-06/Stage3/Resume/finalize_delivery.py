from pathlib import Path
import json, hashlib, shutil, datetime, subprocess, html
import struct

root = Path(__file__).resolve().parents[4]
stage = root/'Staging/ReusableSky_2026-10-06/Stage3'
resume = stage/'Resume'
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x): p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
saved = read(resume/'FINAL_SAVE_RECEIPT.json')
proc = subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process UnrealEditor -ErrorAction SilentlyContinue).Id | ConvertTo-Json -Compress'],capture_output=True,text=True)
assert not proc.stdout.strip(), proc.stdout
hashes = {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in saved['hashes']}
assert hashes == saved['hashes']
log = (stage/'SkyEditor.log').read_text(encoding='utf-8',errors='replace')
assert '17.40.19:191][376]LogExit: Exiting.' in log
shutil.copy2(stage/'SkyEditor.log',resume/'SkyEditor_PID39400.log')
write(resume/'EXIT_PID39400.json', {'pid':39400,'checked_utc':now,'live_unreal_editor_pids':[], 'clean_exit_log_utc':'2026-10-06T17:40:19.191Z','shutdown_saves':0,'dirty_before_exit':[], 'temporary_preferences_restored':True,'saved_hashes_match_after_exit':True,'hashes':hashes})
if not (resume/'PRIOR_BLOCKED_RESULT.txt').exists(): shutil.copy2(stage/'RESULT.txt',resume/'PRIOR_BLOCKED_RESULT.txt')
controls = read(stage/'CONTROL_INTERFACE.json')
controls['status']='SAVED_FRESH_REOPEN_VERIFIED'
controls['verification_receipts']=['Resume/REGRESSION_VERIFICATION.json','Resume/REOPEN_VERIFIED.json','Resume/RUNTIME_paused.json']
write(stage/'CONTROL_INTERFACE.json',controls)
write(stage/'DEPENDENCIES.json', {'engine':'Unreal Engine 5.8.2','required_plugin':'SunPosition (already enabled by Stage 1)','native_dependencies':saved['dependencies_after_reload'],'area_asset_dependencies':[], 'third_party_cloud_material_dependencies':[], 'portability_migration_test':'NOT_PERFORMED_STAGE4'})
result='''REUSABLE SKY STAGE 3 — IMPLEMENTED, SAVED, FRESH-PROCESS REOPEN VERIFIED
2026-10-06. Operator 01a1118e-256a-7d83-8a2b-ad3293e53281.

RETAINED DELIVERY
/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky
/Game/Project/Shared/Atmosphere/ReusableSky/M_EnvironmentCelestial (new)
/Game/Project/Shared/Atmosphere/ReusableSky/MI_EnvironmentCloudDefaults (Stage 2 unchanged)
The shared Blueprint and celestial material are saved native assets, verified after a clean exit and fresh editor launch. Stage 4 portability and final integration are NOT complete.

IMPLEMENTED
One integrated actor reuses the existing sun, atmosphere, sky light, clouds and UpdateSky path. Added one aligned movable moon directional light and one opaque IsSky celestial dome. Moon enable, light/disk brightness, artistic phase and angular diameter; stars enable and brightness; continuous elevation-based twilight/night fades; optional runtime time progression, pause and adjustable day length, OFF by default. Grouped controls and callable setters are documented in CONTROL_INTERFACE.json. No custom control window.
UpdateSky -> ApplyWeather -> UpdateNight -> ApplyNightMaterial coordinates lighting. Native index1 moon disk is suppressed so the material supplies one visible moon. Moon illumination aligns with its disk. Per-instance transient cloud/celestial material instances are reconstructed on load and reused. Native volumetric clouds obscure the moon and stars. Existing exposure remains authoritative, with OverrideExposure=false.
Final defaults: MoonBrightness0.006 lux; MoonDiskBrightness0.04; MoonPhase0.5; MoonAngularDiameter1.2 degrees; StarBrightness0.02; NightSkyFill0.12; AnimateTime=false; DayLengthMinutes20. These are calibrated to this scene's existing exposure and Stage 1 sun level.

MEASURED VERIFICATION
Stage 1/2 saved receipts, hashes and native public controls were checked before authoring. Manager cc37d4d2 assigned this bounded turn in RESUME_MANAGER_RESPONSE.json. Commandlet34880 compiled/saved exactly M_EnvironmentCelestial with zero compile errors. Interactive authoring PID38224 saved the Blueprint and original Rimal map by exact names, with no dirty packages remaining. It exited cleanly. Fresh PID39400 read the saved controls, material and hashes before any mutation: Resume/REOPEN_VERIFIED.json.
Regression: Clear, PartlyCloudy, Overcast and Hazy preserve time/manual/moon/star/progression choices; independent time/manual buffers preserved; enabling stars at noon leaves noon and zero star visibility; moon toggle/phase and star toggle verified; 50 UpdateSky calls retain 13 editor components and reuse material instances. Runtime has 10 components because editor-only billboards are absent. Actual Simulate on the assigned original map exercised a one-minute day, midnight wrapping and pause; paused Tick is disabled and editor time does not inherit simulation changes. Final clock solver passes seconds to SunPosition; HH:MM remains readable.
Matching-camera native screenshots cover sunrise05:00, noon12:00, sunset18:30, twilight19:12, clear/partly/overcast night, half moon, moon off, stars off, and23:59/00:00 wrap. Fresh-process noon/night screenshots verify visible persistence. Smooth fade formulas and sampled transitions passed; no exhaustive frame-by-frame cinematographic sweep is claimed.
All121 unrelated scene actors' measured transforms, component visibility and recorded lighting/fog settings match the before snapshot (122 actors total). No bank, terrain, building, road, Houdini, profile or vendor authoring occurred. Scene exposure was not changed. No Save All, disposable map, self-issued lease or manager identity change.

SAVED VS REOPENED
The first named Stage 3 Rimal map save (sha2566332f42f0a260163ac4b4c51882d5e6114be0ab0d11a41a42ffb521e6741d923) and the final Blueprint/material were reopened in PID39400 and verified. After that process's night verification, the original noon/PartlyCloudy/wind1 state was restored and the map alone saved again. That final map restoration was read back clean and hash-verified after exit, but was NOT reopened a third time. Blueprint/material hashes were unchanged by the restoration. Exact final hashes follow below and in Resume/FINAL_SAVE_RECEIPT.json.
Both interactive editors exited cleanly; final PID39400 LogExit was2026-10-06T17:40:19.191Z. No shutdown saves. Resume/EXIT_PID39400.json records zero live editors and post-exit hashes.

DEPENDENCIES AND REMAINING LIMITATIONS
Engine native sky/cloud assets and installed SunPosition only; no PWL/MW dependency, no area/Rimal dependency. DEPENDENCIES.json records actual post-reload package references. Migration to another project, packaged-build/cook validation, broad platform testing and integration into retained GazaShujaiya are deferred to Stage 4. Manager reports Rimal will be retired by consolidation after release; its verification instance is not the retained shared deliverable. Shujaiya was NOT edited.
Moon position/phase are artistic, not astronomical: moon is opposite the actual sun. Phase is user-selected; clock wrap retains the selected date. Automatic progression is Play/Simulate/runtime only; static editor changes update immediately. Manual Sun keeps its direction while the time buffer advances.
Material compiler reports156 vertex/337 pixel instructions,2 samplers and3 pixel texture fetches. Static/paused actor Tick is disabled. These are measured implementation costs, not a GPU-frame-time benchmark; a controlled Balanced/High comparative performance sweep for the new dome remains unverified. Realtime viewport rendering and temporal settling are required for stable clouds/exposure. Existing scene ray-tracing memory-budget warnings were observed during some captures and were not repaired by this sky task. Other scenes may need appearance calibration to their exposure.

EVIDENCE AND USE
Open EVIDENCE.html for unretouched native viewport comparisons. QUICK_START.txt explains dragging one actor, conflict review before Rig Enabled, time/manual controls, moon/stars and runtime progression. Existing conflicting lighting actors are never automatically removed or disabled.
Prior material-compile hangs and blocked status are preserved under Resume/PRIOR_BLOCKED_RESULT.txt and original incident receipts. The approved commandlet route resolved that implementation blocker; the old blocked receipt does not describe the current saved delivery.

FINAL SHA256
'''
result += '\n'.join(f'{v}  {k}' for k,v in hashes.items())+'\n'
(stage/'RESULT.txt').write_text(result,encoding='utf-8')
groups=[('Day and night — same camera',[('sunrise','Sunrise · 05:00'),('noon','Noon · 12:00'),('sunset','Sunset · 18:30'),('twilight','Twilight · 19:12'),('night_clear','Night · clear sky'),('night_overcast','Night · overcast')]),('Independent appearance controls',[('night_partly','Partly cloudy · native cloud occlusion'),('moon_half','Half moon · artistic phase'),('moon_disabled','Moon disabled · stars remain'),('stars_disabled','Stars disabled · moon remains')]),('Midnight and fresh-process persistence',[('wrap_before','Before midnight · 23:59'),('wrap_after','After midnight · 00:00'),('reopened_noon','Fresh editor · saved noon'),('reopened_night','Fresh editor · night verification')])]
sections=[]; manifest=[]
for title, items in groups:
    cards=[]
    for name,label in items:
        p=stage/'Evidence'/f'{name}.png'
        dims=list(struct.unpack('>II',p.read_bytes()[16:24]))
        manifest.append({'file':str(p.relative_to(stage)),'label':label,'dimensions':dims,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        cards.append(f'<figure><a href="Evidence/{name}.png"><img loading="lazy" src="Evidence/{name}.png" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>')
    sections.append(f'<section><h2>{title}</h2><div class="grid">'+''.join(cards)+'</div></section>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reusable Sky · Stage 3</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b101a;color:#e8edf6;font:16px/1.6 system-ui,sans-serif}main{max-width:1380px;margin:auto;padding:42px 28px}h1{font-size:42px;line-height:1.12;margin:12px 0}h2{font-size:23px;margin-top:44px}p{max-width:950px;color:#bdc9dc}a{color:#a8d1ff}.badge{display:inline-block;background:#153b35;color:#b7f2d9;padding:5px 12px;border-radius:16px;font-size:13px}code{overflow-wrap:anywhere;color:#d3e6ff}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}figure{margin:0;border:1px solid #293349;border-radius:12px;overflow:hidden;background:#111a28}img{display:block;width:100%;height:auto}figcaption{padding:13px 17px}.note{border-left:3px solid #89b3eb;padding:10px 20px;background:#111b2b}footer{margin-top:40px;color:#99aac2;font-size:14px}@media(max-width:700px){.grid{grid-template-columns:1fr}main{padding:24px 16px}h1{font-size:33px}}</style><main>
<span class="badge">Stage 3 · saved native assets · fresh-process reopen verified</span><h1>Moon, stars &amp; the changing sky</h1>
<p>Unretouched Unreal viewport captures from the assigned original GazaRimal scene. One existing sky actor coordinates sunlight, moonlight, sky fill and weather. The scene's exposure and unrelated actors were preserved.</p>
<p><code>/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky</code></p>
<p><a href="QUICK_START.txt">Simple usage instructions</a> · <a href="RESULT.txt">Delivery and verification receipt</a> · <a href="CONTROL_INTERFACE.json">Future panel control interface</a></p>
<div class="note">Stage 4 portability and GazaShujaiya integration remain open. Moon placement and phase are artistic. Automatic time progression is disabled by default. Editor changes are immediate; automatic progression runs in Play/Simulate.</div>
'''+''.join(sections)+'''<footer>Primary comparison camera: location (20000, 0, 11552), pitch8°, yaw184.5°, FOV90°. Click any image for its native resolution. Fresh reopen views may have a different viewport size. Final shared assets were reopened; the final map-only noon restoration was saved and read back clean, without a third reopen. The dedicated editor has exited cleanly. The manager-assigned Rimal verification scene is released for consolidation; the shared package has no Rimal asset dependency.</footer></main></html>'''
(stage/'EVIDENCE.html').write_text(page,encoding='utf-8')
write(stage/'EVIDENCE_MANIFEST.json',manifest)
assignment = read(stage/'ASSIGNMENT.json')
assignment.update(status='SAVED_REOPEN_VERIFIED_RELEASED',editor_live=False,released_utc=now,clean_exit_receipt='Resume/EXIT_PID39400.json')
write(stage/'ASSIGNMENT.json',assignment)
handoff=f'''STAGE 3 DELIVERY AND CLEAN RELEASE — {now}
Manager cc37d4d2-3d62-4f53-b689-28432b5527ae; operator01a1118e-256a-7d83-8a2b-ad3293e53281.
Dedicated authoring PID38224 and fresh-reopen PID39400 both exited cleanly. No live UnrealEditor at final check; no dirty/shutdown saves. No legacy owner/lease edits.
Retained BP_EnvironmentSky and new M_EnvironmentCelestial are implemented, named-saved and fresh-process reopened; Stage2 cloud MI unchanged. RESULT.txt, EVIDENCE.html, QUICK_START.txt, DEPENDENCIES.json and Resume/FINAL_SAVE_RECEIPT.json are final delivery receipts.
Rimal is released to the already authorized consolidation operation. No shared sky asset depends on Rimal or any /Areas/ asset. We do not authorize deletion ourselves; the existing consolidation authorization controls it. Shujaiya has not been edited; Stage4 migration, performance sweep and integration remain pending. All121 measured unrelated scene actors unchanged. No bank/Houdini/roads/ground modifications.
The final map-only noon restoration was saved clean after successful fresh reopen/night check; it was not reopened a third time. Shared BP/material remained hash-identical throughout fresh-process verification.
Consolidation may now remove its temporary Git excludes and include the retained sky delivery under its own assignment; this task did not modify Git excludes.
Final hashes:\n'''+ '\n'.join(f'{v}  {k}' for k,v in hashes.items())+'\n'
(stage/'DELIVERY_HANDOFF.txt').write_text(handoff,encoding='utf-8')
(stage/'STATUS.txt').write_text(f'RELEASED {now}: Stage3 shared native BP/material SAVED and FRESH-PROCESS REOPEN VERIFIED. PID38224 and PID39400 exited cleanly; zero live UnrealEditor processes at release. Original Rimal verification map released to manager/consolidation; no Rimal dependencies in shared package. No Shujaiya changes. Stage4 portability/integration remains open. See RESULT.txt, DELIVERY_HANDOFF.txt and EVIDENCE.html.\n',encoding='utf-8')
print(json.dumps({'delivery':'SAVED_REOPEN_VERIFIED_RELEASED','evidence_images':len(manifest),'hashes_verified':True,'live_editors':[],'utc':now}))
