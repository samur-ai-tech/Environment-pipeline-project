import json,hashlib,datetime,html
from pathlib import Path
root=Path(__file__).resolve().parent;project=root.parents[2]
paths=[project/'Content/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky.uasset',project/'Content/Project/Shared/Atmosphere/ReusableSky/MI_EnvironmentCloudDefaults.uasset',project/'Content/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.umap']
def row(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
files=[row(p) for p in paths]
previous=json.loads((root.parent/'DELIVERY_FILES.json').read_text())
preserved=[]
for x in previous:
 if x['path'].endswith('Environmentpipeline.uproject') or x['path'].endswith('SunSky.uasset'):
  r=row(Path(x['path']));assert r['sha256']==x['sha256'];preserved.append(r)
(root/'DELIVERY_FILES.json').write_text(json.dumps({'delivered':files,'stage1_dependency_files_unchanged':preserved},indent=2))
perf=json.loads((root/'PERFORMANCE_RESULTS.json').read_text())
lines=[]
for x in perf:
 m=x['metrics'];gpu=m.get('GPU/VolumetricCloud',{}).get('median_ms');shadow=m.get('GPU/VolumetricCloudShadow',{}).get('median_ms')
 lines.append(f"{x['case']:12s} frame median {m['FrameTime']['median_ms']:.3f} ms; frame p90 {m['FrameTime']['p90_ms']:.3f} ms; cloud pass {'absent' if gpu is None else format(gpu,'.3f')+' ms'}; cloud shadow {'absent' if shadow is None else format(shadow,'.3f')+' ms'}")
report='''REUSABLE SKY — STAGE 2 DELIVERY RECEIPT
2026-10-06

IMPLEMENTED
Retained native BP_EnvironmentSky extended with one owned VolumetricCloudComponent and per-construction transient MaterialInstanceDynamic. No additional lighting manager, Tick-driven construction, global material collection or vendor derivative was introduced. Presets and weather controls use the same UpdateSky path as Stage 1. Saved MI_EnvironmentCloudDefaults derives from the Engine's m_SimpleVolumetricCloud material.

Entry: /Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky
Support: /Game/Project/Shared/Atmosphere/ReusableSky/MI_EnvironmentCloudDefaults
Map: /Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration
Actor: EnvironmentSky / BP_EnvironmentSky_C_0

AUTHORITY AND OWNERSHIP
Stage 1 delivery, on-disk hashes, public controls and the same operator's explicit handoff were checked before authoring. Initial manager-assignment wait was superseded by Aviv's direct instruction to perform the work in this operator's own window; DIRECT_AUTHORIZATION.txt records that transition. This was direct user activation, not a Claude-manager-issued lease. No manager identity or ModelBank/EDITOR_OWNER.txt change. Parallel editor policy was already saved in AGENTS.md during Stage 1 and was not broadened for Stage 2.
Authoring PID5288; first independent reopen PID9416; final active-realtime appearance reopen recorded in REOPEN_VERIFIED.json. All used dedicated ports19841/18081/8001 on original Rimal. PID29900 was never mutated, saved or closed by this task. No GeoCity generation was run or its single-editor guard bypassed.

CONTROLS AND COORDINATION
Cloud Amount0..1, Haze0..1, Cloud Speed0..20 multiplier, Cloud Direction degrees plus North Offset. High Quality false=Balanced, true=High. Preset buttons apply Clear(0,.05), Partly Cloudy(.55,.15), Overcast(1,.25), Hazy(.2,.8). Weather Preset is a descriptive last-applied label, not a selector.
Cloud coverage=-1+2.5*amount^2; density=.006+.012*amount. Haze changes owned Mie scale=.002+.022*haze. Base sun intensity is attenuated by 1-.88*amount^3, sky intensity by1-.15*amount, and source angle becomes .5357+4*amount^3 degrees. Below-horizon direct sun remains off. Base light inputs, geographic/manual controls and exposure are preserved. No automatic exposure adaptation changes were made.
Balanced view/reflection/shadow-view/shadow-reflection sample scales=1/.5/.5/.25; High=2/1/1/.5. Global scalability untouched. Balanced remains default because High costs more in the measured cloud pass and gave only a subtle visual improvement at this camera.

NATIVE VERIFICATION
Preset preservation checks used distinct clock/date/north/manual values. All four presets preserved the Stage 1 inputs. Switching time/manual modes returned the expected manual direction without changing stored clock or manual buffers. Morning06:00/noon12:00/evening18:00 visibly changed lighting in original Rimal.
50 repeated UpdateSky calls retained10 owned components: one each sun, skylight, atmosphere, cloud, scene root, compass mesh, exposure component and north arrow, plus2 editor billboards. Regular updates reused the same MID. Construction created a new MID. Shared material defaults stayed unchanged. Component class counts stayed stable.
Native comparisons cover clear and full overcast, Hazy, Balanced/High, morning/noon/evening and10-second wind motion at speed20/direction90. Camera(-8268,-6591,11552), pitch-15/yaw52/FOV90, captures1044x574. Most comparison captures used speed0 to isolate weather/quality; final saved actor uses speed1.

SAVED
Only MI_EnvironmentCloudDefaults, BP_EnvironmentSky and original Rimal were explicitly saved. NAMED_SAVE.json records successful calls and zero dirty maps/content afterward. No Save All. SHA256 and sizes are in DELIVERY_FILES.json. Asset defaults remain inactive; retained Rimal actor is active at12:00, Jun21 2026, latitude31.52/longitude34.44, UTC+2, DSToff, north0, manualoff, PartlyCloudy .55, haze.15, speed1, direction45, Balanced, exposure overrideoff.

REOPENED
The same original map and assets were opened in fresh editor processes. Without invoking UpdateSky or changing actor properties, native readback verified reconstructed MID, correct material/coverage/density/wind, cloud visibility, sun attenuation, haze, ten owned components, saved clock/preset/quality, preserved disabled originals and zero dirty packages. See REOPEN_VERIFIED.json and Evidence/reopened_realtime.png. Editor shutdown receipts record no shutdown saves; final OS process receipt identifies remaining editor29900 only.

PRESERVATION AND EXACT CONFLICTS
Stage 2 deliberately disabled only the visible component of original actor VolumetricCloud_0 after reporting it, retaining that actor/material. Exact component:
/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.L_GazaRimal_BankIntegration:PersistentLevel.VolumetricCloud_0.VolumetricCloudComponent
CLOUD_RESTORATION.json records its previous state. Stage 1's retained disabled DirectionalLight_0, SkyLight_0, SkyAtmosphere_0 and StaticMeshActor_0 (SM_SkySphere) remain unchanged. Original ExponentialHeightFog_0 stays active at its original density. Existing light intensities were read back against the Stage 1 inventory. Actor count remains122. No ground/building/road/Houdini/profile/catalog/bank/vendor authoring occurred. SunSky vendor asset and project plugin descriptor hashes match Stage 1. No PWL/MW dependencies were needed or modified.

PERFORMANCE OBSERVATIONS
UE5.8.2, D3D12, RTX5070 12GB, Ryzen7 7800X3D. Same retained camera and noon, frozen base wind, existing scalability3, cloud render target mode0. Six completed180-frame native CSV captures; first30 discarded,150 analyzed each. Finalized CSV trailing headers were used (early incomplete copies were rejected and measurements repeated).
'''+ '\n'.join(lines)+'''
The other project editor remained open, and editor scheduling/background behavior produced approximately100–103ms p90 spikes. These data support relative cloud-pass cost only, not gameplay FPS or isolated whole-frame performance. No GPU total was available in these captures. Cloud shadow cost barely changed between profiles at this camera. The existing scene also logs a VSM non-Nanite marking queue overflow; no scene geometry or shadow-global tuning was attempted.

LIMITATIONS / NOT VERIFIED
- Smooth wind retiming is not implemented: changing speed/direction/north can jump the Engine material's absolute-time cloud phase. Continuous motion at fixed settings was checked, but seamless animated transitions are not claimed. The plan's stronger no-discontinuity goal remains open.
- Native transient MID references emit one missing /Engine/Transient.EnvironmentCloudMID load warning before Construction Script rebuilds them. Reconstructed references and correct values were verified after fresh load. Warning suppression remains unresolved.
- Cloud reconstruction can look stippled in an unfocused, CPU-throttled viewport; active Realtime accumulation is required. Final reopen imagery explicitly checks active rendering. The original scene showed intermittent cyan ground gaps in some long-session screenshots, absent immediately after fresh load but recurring during active rendering. Their root cause was not diagnosed and no terrain repair was made.
- Haze is atmospheric Mie control, not modification of existing fog; the Hazy preset has a restrained effect in this near-city camera.
- A second retained scene/two simultaneously edited sky instances, PIE, packaged runtime, other hardware, seamless wind edits and user visual acceptance remain unverified. Per-instance isolation is implemented and checked by MID replacement/reuse and unchanged shared defaults; a second-scene native exercise was not authorized/performed.
- Moon, stars, night polish and automatic time animation remain later stages.

DEPENDENCIES / MIGRATION
Required: enabled Sun Position Calculator (already saved by Stage1), native Engine volumetric cloud resources, project-owned MI_EnvironmentCloudDefaults. Registry dependencies are recorded in NAMED_SAVE.json. BP also uses SunPosition's editor compass mesh and Engine editor resources. Use Unreal's dependency-aware Migrate for the Blueprint and support asset into a compatible UE project, then enable SunPosition. No guarantee for other engine versions/renderers/platforms; no PWL/MW content dependency.

EVIDENCE
EVIDENCE.html: direct native images grouped by weather, time, quality, motion and reopen.
CONTROL_VERIFICATION.json: input preservation, manual/time round trip, repeated update counts.
CHECK_*.json: individual controls and material/component readback.
Performance/*.csv and PERFORMANCE_RESULTS.json: finalized samples and statistics.
NAMED_SAVE.json, REOPEN_VERIFIED.json, EXIT_*.json, DELIVERY_FILES.json: persistence and close receipts.
QUICK_START.txt: ordinary usage and known limitations.
'''
(root/'RESULT.txt').write_text(report,encoding='utf-8')
groups=[('Fresh reopen',[('reopened_realtime','Saved Partly Cloudy, active Realtime, fresh process')]),('Weather at noon',[('clear_noon','Clear'),('partly_noon_balanced','Partly Cloudy'),('overcast_noon','Overcast'),('hazy_noon','Hazy')]),('Time of day',[('partly_morning','06:00'),('partly_noon_balanced','12:00'),('partly_evening','18:00')]),('Quality comparison',[('partly_noon_balanced','Balanced'),('partly_noon_high','High')]),('Cloud motion',[('motion_start','Speed20, direction90 — start'),('motion_after_10s','Same controls — 10 seconds later')])]
s='<!doctype html><html lang="en"><meta charset="utf-8"><title>Reusable Sky Stage 2 — native evidence</title><style>body{background:#17212b;color:#e8edf3;font:16px system-ui;margin:30px auto;max-width:1400px;padding:0 24px}h1{font-size:28px}h2{margin-top:36px}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:20px}figure{margin:0}img{width:100%;border-radius:6px}figcaption{padding:8px 0}a{color:#b8d8ff}p{max-width:1000px;line-height:1.6}</style><h1>Reusable Sky — Stage 2</h1><p>Actual Unreal viewport captures from retained GazaRimal, same camera. Click an image for full size. No generated or retouched imagery. The saved actor uses Partly Cloudy and Balanced. Weather and quality comparisons freeze base wind. Scene geometry was not part of this task; some long-session captures show transient cyan ground gaps which were absent just after loading but recurred during active rendering.</p><p><a href="QUICK_START.txt">Usage</a> · <a href="RESULT.txt">Delivery and limitations</a> · <a href="PERFORMANCE_RESULTS.json">Measured performance</a></p>'
for title,ims in groups:
 s+='<h2>'+html.escape(title)+'</h2><section>'
 for name,label in ims:s+=f'<figure><a href="Evidence/{name}.png"><img src="Evidence/{name}.png" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>'
 s+='</section>'
s+='<p>Implemented and saved; fresh-process reconstruction verified. Smooth wind retiming, packaged runtime, a second scene and user visual acceptance remain open. Moon/stars are Stage 3.</p></html>'
(root/'EVIDENCE.html').write_text(s,encoding='utf-8')
print(json.dumps(files,indent=2))
