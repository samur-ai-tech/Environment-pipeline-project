# Reference review and rejected ground result

## Scope and method

The user rejected the 2026-10-04 ground result and supplied both Unreal Sensei videos. This review uses actual Chrome playback and decoded video frames, with media timestamps read from the video element. English automatic timed transcripts were exported through the supported browser transcript API to check the explanations. Selected relevant demonstrations were inspected; neither complete video is claimed to have been watched end to end.

## First reference: UE5 Landscape material

Source: https://www.youtube.com/watch?v=5ju7wyvZGBI

- **Observed at 12:54:** close cliff surface and its material panel. The distance-blend demonstration changes between two texture scales, preserving fine detail near the camera while breaking the repeated pattern farther away. The explanation at 12:12-13:45 identifies the two scales and transition offset/falloff.
- **Observed at 14:47 and 15:28:** grass-covered hills and texture/material options. Cell bombing is a separate mechanism from color stains: it varies texture placement/rotation and blends the samples. The transcript at 14:01-14:48 shows the before/after intent and notes a performance cost.
- **Observed at 28:11:** rocks protrude from the ground. The presenter moves a light to expose relief and self-shadowing. At 27:03-28:10 he identifies actual Nanite displacement, distinct from normal-map shading. This is not reproduced by a tint or roughness change.
- **Observed at 46:05:** a placed rock is integrated with grass through virtual texture material settings. The 45:01-46:10 explanation identifies runtime virtual texture blending and its setup; it is not an automatic property of every Landscape material.

The tutorial begins from the author's already-built master material and supplied textures. The short visible parameter edits rely on substantial material logic that already exists in that project.

## Second reference: Mesh Terrain

Source: https://www.youtube.com/watch?v=Lhj2LutYNjA

- **Observed at 0:48:** the finished scene combines detailed rock terrain, vegetation, water and lighting. It is a complete environment, not evidence that one color parameter produces the scene.
- **Observed at 21:00:** a cave/overhang is sculpted in an actual mesh, with its topology visible. This is a geometry tool demonstration.
- **Observed at 33:58:** textured rock relief and the cave mouth; displacement settings are visible. The following 34:01-34:34 explanation shows why projection/seams matter when displacement is used.
- **Observed at 37:08:** the ground repeats in visible rows while distance blending is disabled. **Observed at 37:20:** randomized sampling breaks up that pattern. The camera also moves, so these video frames are not a controlled same-camera test of our own scene.
- **Observed at 38:05:** the presenter proceeds to macro variation. The 38:05-39:11 explanation separates subtle macro stains from extra color/normal variation that fades near the camera.
- **Observed at 42:18:** a painted stone path meets grass beside the textured cave. The 41:25-41:54 explanation combines low-strength paint transitions with the rebuilt displacement result.

The material chapter explicitly says the anti-tiling mechanisms came from the earlier Landscape material (34:57-35:14). The video description identifies Sensei Terrain as Mesh Terrain-only and links the first video for the original Landscape system. The mesh sculpt/modifier workflow is not a drop-in material replacement for the current geographic Landscape route.

## Initial 704-node graph comparison: historical diagnosis

Native readback is retained in NATIVE_DIAGNOSIS_PID30632.json and INSTALLED_FUNCTIONS_PID30632.json.

- The active Natural graph has world-aligned color/normal sampling but no camera-distance sampling mechanism.
- Its active roughness tree is 69 per-layer scalar parameters plus the layer blend, without texture-derived roughness variation.
- The previous high-strength ground macro replaces sand color/normal with soil across broad cloudy regions. This is the dominant visible weakness in the rejected middle/wide views.
- Corrected sand normal copies are still referenced. Engine WorldAlignedNormal's default path converts its result from world to tangent space, consistent with the current tangent-space material setting. There is no proved normal-basis defect.
- The installed Iceland content already contains cell-bombing and distance-blend functions. Native inspection is required before reuse: generic color samplers and packed-channel interpretation must not be guessed, and vendor functions must remain unchanged.
- Existing lighting is measured and preserved. Screenshots alone do not prove a lighting fault.

## Consequence for the retained correction

The quality target is credible near surface detail, coherent color/normal/roughness coordinates, a smooth near/far transition, restrained irregular variation and plausible dry surface roles. Another broad tint adjustment is insufficient. The repair must preserve the original areas, geographic heights/weights, 69 layer names, corrected normal copies, Grass and non-ground assets. Real rock displacement, cave sculpting, foliage composition and object-ground blend setup are separate mechanisms; this ground task must not silently claim to have implemented them.

## Additional playback and corrected native evidence on 2026-10-05

The second video was played through 37:08-39:20, with actual decoded frames inspected at 36:58, 38:02 and 39:20. The first video was played through 14:02-15:52, with decoded frames inspected at both ends. These are further selected-section reviews, not a claim of end-to-end viewing. The demonstrations distinguish cell bombing, distance scales and macro color variation; their finished rock/grass composition includes geometry and vegetation beyond this ground material task.

A material repair alone could not explain the previously flat native screenshots. A supported native readback exposed a capture error: the actual active viewport was Unlit (enum 2), at the exact matching wide camera. The former capture helper's 'Lit' field was only a console-command request. The correction is documented in CAPTURE_VIEWMODE_CORRECTION.json; earlier normal, roughness and missing-shadow visual conclusions are withdrawn. They must not be used as verified Lit evidence.

The corrected capture helper uses AutomationLibrary's active viewport setter/getter and records actual Lit (enum 3), its viewport key, and matching camera metadata for every new image. Actual Lit r010-r012 now show the existing directional light's cast shadows and dry surface response without changing any lighting actor. The shared retained 915-node graph preserves all layer roles and Grass, couples color/normal/packed-mask coordinates, decodes linear roughness and AO, and retains fixed translated phases. Those fixed translations are not a complete stochastic cell-bombing implementation. The measured ground/soil far-scale controls are tuned to avoid the visible enlarged texture pattern; the video's displacement, mesh sculpting and RVT contact setup have not been implemented by this task.

## Closer review and unresolved fresh-process detail

Further second-video playback covered 39:20-42:58. Playback was changed from automatic 480p to actual decoded 1920x1080 before examining frames at 41:27 and 42:48. The path demonstrates textured stone/soil against grass, paint controls and material transitions beside displaced rock. The first video was also changed to actual decoded 1920x1080; its automatic cliff/ground layering was examined at 16:54, followed by the Nanite chapter from 27:01. These are selected visual inspections, not full-video claims.

Independent reachability review of the retained 915-node graph found that all nine historical MF_DistanceCellBlend calls are now disconnected from the active surface roots. The active flat layers use two fixed UV translations, not per-cell random placement. GeoCity_CellScale is consequently inactive. Sand_01 and Dirt_Path far scales are both 1, so the near/far scale distinction is disabled on the main bare-ground layers, although the 12-72 metre distance alpha remains connected. Height-aware layer transitions, actual displacement and RVT contact integration remain absent.

Shujaiya's r014 graph, parameters and named packages were saved and exactly recovered in fresh PID14776. Its matched actual-Lit close image is nevertheless substantially softer than the presave image, including a second settled capture. The verified same camera and sharp road silhouettes do not explain the ground-detail loss. A loading-completion diagnostic returned without changing persistent texture properties or CVars, but its subsequent close capture remained blurred. Technical persistence has passed; visual-detail persistence remains unresolved. Neither the reference quality nor final user acceptance is claimed.

## Deeper transition review on 2026-10-05

The first reference was replayed at full decoded1920x1080 around27:01-28:39, then its36:44-37:55 height-blend/paint demonstration was played and inspected. The rocky close surface visibly protrudes and casts small self-shadows. During weak paint application, isolated rocks appear before the whole rocky surface replaces grass. The narrated36:04-38:21 section distinguishes material height-aware transitions from displacement. Exact durable automatic English transcripts are REFERENCE_TRANSCRIPT_5ju7wyvZGBI.txt and REFERENCE_TRANSCRIPT_Lhj2LutYNjA.txt; they are primary-source narration with automatic-caption errors possible. Selected sections remain the scope of visual viewing.

This adds a specific quality requirement: detailed transitions should reveal the plausible components of the next surface, not only crossfade flat colors or add broad cloudy stains. The current Ground material's plain weighted layer roots do not implement that height-aware transition. Geometry/displacement remains distinct from normal detail, and the geographic masks cannot be silently repainted by this ground assignment.

After an exact owned child-material asset viewer was opened and closed via native APIs, all maps/Content remained clean, but texture streamer's View0 reported the now-closed preview's origin and48-pixel screen size. A subsequent active-level close capture stayed crisp from already-loaded4096 mips; it does not prove fresh default residency or correct camera tracking. This observation strengthens the requirement to validate default fresh-process views without finite texture residency forcing or relying on material-preview cache.

## Additional height-patch and contact review

First-video playback continued from37:55 to42:19 at decoded1920x1080. Actual frames inspected at39:26 and40:52 show the complete castle landscape and the height-patch management workflow; the paused42:19 frame shows a height texture patch with world-unit encoding controls. The complete composition contains authored landforms, vegetation, atmospheric depth and built assets. Height patches manipulate Landscape shape; this ground-only material task does not authorize modifying the preserved geographic heights.

The45:01 Virtual Texture Blending chapter was opened for further playback. Its narrated setup and actual contacts are being compared with the current abrupt curb/building contacts. Ground color, texture-scale changes and normal shading alone do not establish object-ground contact blending.

The new Sand01 stochastic graph compiled70/70 native shader jobs at03:24:02.590. Initial close/middle captures can precede this completion and are superseded for shader readiness by the separate settled stage. Independent review of all three settled views still finds insufficient visible gain to approve saving that revision. This negative result is preserved; graph implementation is not treated as appearance success. A subsequent single existing child-instance cell-scale override(.1 to1) remains unsaved pending its own comparison and exact instance review.


## Completed selected contact/paint review and current checkpoint

Further first-video playback covered45:01-54:16 at decoded1920x1080. Inspected frames47:49,48:40 and51:28 show the virtual-texture asset, volume setup and MF_VTGroundBlend in the object material;53:06 shows the finished creek/cabin/ground composition. This contact mechanism needs both material sides and the virtual-texture setup. Second-video selected playback was reopened at34:57, with a36:12 decoded full-HD material frame reviewed. Its39:12 paint chapter was subsequently replayed and inspected at43:02, with playback paused45:22. A51:56 spline frame was also inspected; the elapsed background playback between previously inspected sections is not claimed as a fully watched passage. Neither video is claimed viewed end-to-end.

The matched Shujaiya comparisons isolate a second limitation: increasing SoilStrength from0.10 to0.35 returns conspicuous dark gouge chains even when Dirt normal intensity is reduced from0.85 to0.20. Exported Dirt albedo already contains directional bright/dark relief-like features; albedo contributes, but normal/roughness/AO attribution is not fully isolated. Keep the modest0.10 mixture rather than increase it to create visual activity. SandFarScale2 makes middle-distance grain slightly clearer; it does not create physical relief or wide-view variety. The r022 current candidate is the r020 total recipe restored after rejecting r021: CellScale1, Soil0.10, SandFarScale2, DirtNormal0.20. These four instance overrides and the1015-node graph remain unsaved.

The two original Landscape streaming multipliers read1.0. Both primary and keyed active cameras are exactly the close camera; the primary viewport reads364x1148. The streamer nevertheless reports the preceding wide origin and Screen364 after86seconds of idle, with exact Sand color/normal/mask Wanted64 and cachedCurrent4096. The pool is23.75/1000MB. This is a measured camera-registration mismatch, not proved pool exhaustion or a shader texture-density defect. High-resolution capture1600x1000 does not establish ordinary streaming at that screen size. No further forced residency, multiplier edit, global CVar change, broad streaming-data build or window-focus workaround was made. Installed purpose-built native tool headers expose no existing viewport/window focus action. The remaining check needs an actual foreground level-viewport interaction and fresh readback before a final save/reopen claim.


## 2026-10-05 r024 retained checkpoint
The actual foreground viewport measured1182x820 and native Wanted/Current4096 without a new residency override. Programmatic subsequent captures still showed a different registered StreamView0, so capture tracking was not declared solved. Experimental Sand_01_Tint(.78,.84,.94) changed image pixels only slightly and showed no perceptible useful visual improvement; it was restored to(1.02,1.02,1) and the exact r022 recipe fully verified. Named-save checkpoint retained only the Natural master and Shujaiya child. Fresh PID9160 reopened the original map clean; complete1015-node/Custom-code/mip/MI/Grass/scene identity verified. Three fresh matched1600x1000 actualLit3 images are stage revision_r024_fresh_actual_lit. No forced residency was used in this fresh process. This is a limited material improvement, not reference-quality completion. Rimal still pending.
