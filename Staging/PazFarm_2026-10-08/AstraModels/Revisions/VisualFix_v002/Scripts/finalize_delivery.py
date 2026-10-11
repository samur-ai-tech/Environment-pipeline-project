"""Assemble the offline revision; writes only below this revision directory."""
import hashlib, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FARM = ROOT.parents[2]
def read(rel): return json.loads((ROOT / rel).read_text(encoding='utf-8-sig'))
def write(rel, data):
    target = ROOT / rel
    assert target.resolve().is_relative_to(ROOT.resolve())
    target.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

qa = read('Reports/VALIDATION.json')
ground_qa = read('Reports/GROUND_QA.json')
placement_qa = read('Reports/placement_qa.json')
assert qa['passed'] and len(qa['assets']) == 9 and len(qa['families']) == 5
assert ground_qa['status'] == 'PASS' and placement_qa['passed']
assets = sum([read('Reports/' + name)['assets'] for name in
              ['trees_v002.json', 'barn_v002.json', 'strawberries_v002.json']], [])
textures = sorted({t.replace('\\', '/') for a in assets for m in a['materials'] for t in m['textures']})
for asset in assets:
    for key in ['fbx', 'blend', 'preview']:
        assert (ROOT / asset[key]).is_file(), (asset['name'], key)
for tex in textures: assert (ROOT / tex).is_file(), tex

originals = read('Reports/ORIGINAL_INPUTS_SHA256.json')
changes = []
for record in originals:
    p = FARM / record['path']
    if not p.is_file() or sha(p) != record['sha256']:
        changes.append(record['path'])
preservation = {'passed': not changes, 'files_checked': len(originals),
                'changed_or_missing': changes,
                'method': 'SHA256 against the before-work baseline of original farm staging inputs and delivery. Revision directory excluded.'}
write('Reports/ORIGINALS_UNCHANGED.json', preservation)
assert preservation['passed'], changes

clone = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
actions = {
    'status': 'PROPOSED_NATIVE_HANDOFF_NOT_EXECUTED',
    'offline_revision': str(ROOT),
    'documented_map': clone + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial',
    'documented_model_folder': clone + '/PazFarm/',
    'scope_note': 'Receiving operator must verify current ownership, actual asset bindings and named writable packages. This file is data, not an editor script or lease.',
    'ranked_actions': [
        {'rank': 1, 'action': 'Inspect distant canopy loss at fixed exposure; check Nanite Preserve Area and two-sided leaf material bindings; replace seven tree assets and leaf textures with this revision.', 'assets': [a['name'] for a in assets if any(s in a['name'] for s in ['Avocado','Lemon','Orange'])], 'keep_plant_transforms': True},
        {'rank': 2, 'action': 'Replace the existing farm ground overlay through its current clone Farm_Blend route; preserve mapping and coverage alpha.', 'texture': 'Georef/T_PazFarm_Ground.png', 'settings': 'Georef/GROUND_SETTINGS.json'},
        {'rank': 3, 'action': 'Reimport fuller strawberry mesh and revised material maps; retain 763 current instances.', 'asset': 'SM_PazFarm_StrawberryBed_4m'},
        {'rank': 4, 'action': 'Reimport barn; add and explicitly bind roof-only material slot 4; retain existing barn instance transform.', 'asset': 'SM_PazFarm_Barn', 'new_material': 'M_PazFarm_Barn_RoofCharcoal_v002'},
        {'rank': 5, 'action': 'Move and rotate existing PazFarm_Gate using the gate-only patch; sample terrain Z with the existing placement convention.', 'patch': 'Georef/PLACEMENT_PATCH.json'},
        {'rank': 6, 'action': 'Inspect ground contact, road overlay conflicts and missing boundary/north-field vegetation using current native assets; resolve under explicit package ownership.', 'offline_geometry_supplied_for_this_action': False}
    ],
    'native_verification_required': ['Same overhead and close cameras at consistent exposure', 'No distant crown loss', 'No floating beds/fence/gate or wrong row orientation', 'No duplicated placement instances', 'Named clone-only saves and fresh reopen'],
    'native_actions_performed': False
}
write('NATIVE_ACTIONS.json', actions)

handoff = '''# Paz Farm v002 — handoff to Claude / native operator

**Offline revision complete and verified. Unreal has not been opened or changed.** All new work is under `Staging/PazFarm_2026-10-08/AstraModels/Revisions/VisualFix_v002/`. Start with `INDEX.html`; `MANIFEST.json` lists nine FBX assets, five editable Blender sources, material maps, ground and gate data. Original delivery and original georeference files are preserved.

The existing result is documented in `Staging/PazFarm_2026-10-08/RESULT_PLACEMENT.md`. Its clone map is `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial`; model packages are documented under that area's `PazFarm/` folder. These paths are a handoff target, not a fresh editor-state check. Obtain the current writer scope and verify package bindings before applying. Preserve other sessions and save only named owned packages. No shared-bank, Houdini, main-area or project-wide rendering changes are included.

## Apply in visual-impact order

1. **Restore visible crowns first.** Seven tree FBXs retain names, crown sizes, trunk-base pivots and material slots. Leaf silhouettes now come from six-vertex geometry, with solid white texture alpha and slightly rougher leaves. Reimport their mesh and leaf maps, preserve two-sided foliage, and inspect Nanite **Preserve Area** on these local meshes. The overhead loss is still an unverified native cause. Epic documents Preserve Area for disconnected foliage geometry; Nanite meshes are not controlled by ordinary foliage cull-distance/fade settings. Check those settings only on a non-Nanite/fallback path. See [Nanite foliage guidance](https://dev.epicgames.com/documentation/unreal-engine/working-with-naniteenabled-content) and [foliage culling behaviour](https://dev.epicgames.com/documentation/unreal-engine/foliage-mode-in-unreal-engine). Do not change density or global exposure to hide a missing-crown defect.
2. **Replace the ground overlay.** Use `Georef/T_PazFarm_Ground.png`, keeping the existing `MI_GeoCityGround_PazFarm` / `Farm_Blend` route. The texture remains north-up, 2048² RGBA over 512 m, west −219.843 m / north +230.463 m from the farm pin. Preserve sRGB, coverage alpha and Clamp addressing. Do not rotate the texture again by the screenshot angle. Finer NE/SW furrows, western green/brown split, muted bare fields, strawberry soil shoulders, yard/apron and pink-tan tracks are included. `Reports/GROUND_HANDOFF.md` has per-plot colours and settings. The comparison is ground only; orchard soil intentionally contains no painted tree crowns. If the existing texture is shared, isolate its replacement to the clone's authorized material scope after checking references.
3. **Replace the strawberry bed.** Reimport `SM_PazFarm_StrawberryBed_4m` and revised material maps. Keep all **449 west + 314 triangle** instances and their rotations. The 0.8 × 4 m tile and ground/start-end pivot remain; total height is 0.424107 m. Geometric leaf coverage increased from 24.55% to 54.53% with 32 plants, while staying at 19,624 triangles. The soil overlay's 2 m shoulder bands align to the existing tile positions. They are not a reason to stretch the mesh. Inspect seams, clipped ends and terrain contact. See `Reports/strawberries_v002.md`.
4. **Replace the barn roof appearance.** Reimport `SM_PazFarm_Barn`; preserve its current placement transform, including the documented 25.8 × 20.5 m footprint. Source wall footprint is still 20 × 12 m, eave 6 m and ridge 8 m. Bind new material **slot 4: `M_PazFarm_Barn_RoofCharcoal_v002`**, with BaseColor PNG median **sRGB (70,62,68)**, roughness 0.94 and metallic 0. Corrugation relief is reduced from 45 mm to 6 mm. **Keep slot 1 `M_PazFarm_Barn_RoofPaintedGrey` unchanged**: it also serves doors and trim. All non-roof geometry and three UCX boxes are preserved. See `Reports/barn_v002_notes.md` for all five slots; FBX alone does not reconstruct packed material wiring.
5. **Centre the existing gate in its gap.** Apply only `Georef/PLACEMENT_PATCH.json`: east **24.266047 m**, north **52.460000 m**, direction **90.075493°** counter-clockwise from east. Use the existing EN-to-Unreal conversion and terrain-height rule; this is not an Unreal yaw or Z value. The gate is centre-pivoted, unlike end-pivoted fence panels. Its 6 m envelope aligns to the adjacent panel interval. `Georef/PLACEMENTS.json` is a complete corrected copy for reference, not an instruction to respawn everything. All **1,955 plants, 225 fence panels, 9 posts and the barn transform** are identical to the original data.

## Material and scale contract

Reconstruct materials from manifest texture paths: BaseColor sRGB on; Normal/ORM sRGB off; ORM channels R=AO, G=roughness, B=metallic. Normals use OpenGL +Y, so retain the established Unreal green-channel conversion. Leaf meshes need two-sided shading; their new alpha is 1. Strawberry mulch normal reduction is already baked in, so use normal strength 1. Set mulch roughness from its ORM (0.79 nominal) and retain the documented reduced specular response. Barn roof has a flat normal map; its Blender specular setting still needs native matching. Preserve existing material bindings by name, not FBX defaults.

Source units are metres; exports use FBX Units Scale, −Y forward / Z up. Reuse the established import conversion and instance transforms. Fresh independent FBX imports matched source dimensions within 0.0001 m. Do not apply another ×100 scale. Leaves have no wind or collision. Barn retains UCX; other revised plants retain no collision.

## Still requires native work or a species decision

- Crown retention, lighting/exposure, floating/clipping and final likeness are unverified until the revised assets are seen in the actual farm cameras. No native import, save, reopen or visual acceptance is claimed here.
- Keep 247 south-orchard trees and their current scale initially. Optional avocado XY factor 0.8 is disabled in `Georef/DEFERRED_VISUAL_OPTIONS.json`; evaluate only after distant visibility works. Keep height unchanged if later selected.
- The eastern crop remains the existing 861 young-citrus placeholders. Species is unresolved; no new crop identity is invented. The NE orchard remains 84 trees.
- Boundary scrub and isolated trees in the north field still need identified native mesh bindings and placements. This revision supplies no new instances for them. Fence base heights and gate swing clearance need ground-level inspection.
- Painted roads now have three explicit junction connectors, but existing GeoCity track geometry can overlap them. Reconcile those local surfaces under the receiving operator's scope. Original traced road vertices and nominal 4/5 m widths remain unchanged.
- Georeference uncertainty remains 8.96 m RMS. NE furrow spacing 1.8 m is an editable visual estimate. Screenshot RGB values are sRGB appearance anchors, not guaranteed framebuffer values under arbitrary lighting.

## Acceptance and evidence

Compare the same overhead, oblique, orchard, barn and strawberry views used for `Review/VISUAL_REVIEW.md`, with consistent exposure. Verify visible crowns, row direction, soil colours, barn roof, ground contact, gate alignment and no duplicate instances. Save only the authorized clone packages and reopen them before reporting native completion.

Offline evidence: `Reports/VALIDATION.json` passes nine fresh FBX imports and five source reopens, triangle budgets, UV0, finite geometry, relative texture paths, solid leaf alpha and dimensions. `Reports/GROUND_QA.json` verifies the unchanged mapping, exact PNG byte round-trip and all 763 strawberry tiles within 7.64 mm cross-axis phase error. `Reports/placement_qa.json` verifies the gate-only data change. `Reports/ORIGINALS_UNCHANGED.json` checks the original inputs/delivery against pre-work SHA256 hashes. Scripts and `Georef/GROUND_SETTINGS.json` retain editable defaults; run only revision scripts, not the original ground script that writes outside staging.
'''
(ROOT / 'HANDOFF_CLAUDE.md').write_text(handoff, encoding='utf-8')

manifest = {'revision': 'VisualFix_v002', 'status': 'OFFLINE_COMPLETE_NATIVE_NOT_APPLIED',
    'scope': str(ROOT), 'assets': assets, 'asset_count': len(assets),
    'blend_count': len({a['blend'] for a in assets}), 'material_texture_count': len(textures),
    'ground': read('Reports/GROUND_MANIFEST.json'), 'gate_patch': read('Georef/PLACEMENT_PATCH.json'),
    'verification': {'model_qa_pass': qa['passed'], 'ground_qa_pass': True, 'gate_qa_pass': True, 'originals': preservation},
    'handoff': 'HANDOFF_CLAUDE.md', 'native_actions': 'NATIVE_ACTIONS.json',
    'native_actions_performed': False,
    'unchanged_original_assets': '17 remaining meshes and their original sources remain in AstraModels; this revision does not replace those assets.',
    'editable_defaults': ['Georef/GROUND_SETTINGS.json', 'Georef/DEFERRED_VISUAL_OPTIONS.json', 'Scripts/build_trees_v002.py', 'Scripts/build_barn_v002.py', 'Scripts/build_strawberries_v002.py'],
    'files': []}
for folder in ['FBX','Blend','Textures','Georef']:
    for p in sorted((ROOT / folder).rglob('*')):
        if p.is_file() and p.suffix.lower() not in ['.blend1', '.pyc']:
            manifest['files'].append({'path':p.relative_to(ROOT).as_posix(), 'bytes':p.stat().st_size, 'sha256':sha(p)})
write('MANIFEST.json', manifest)

cards = []
for a in assets:
    name=html.escape(a['name']); preview=html.escape(a['preview'])
    cards.append(f'<article><a href="{preview}"><img loading="lazy" src="{preview}" alt="{name}"></a><h3>{name.replace("SM_PazFarm_", "")}</h3><p>{a["triangles_LOD0"]:,} triangles · <a href="{a["fbx"]}">FBX</a> · <a href="{a["blend"]}">Blender source</a></p></article>')
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Paz Farm — visual revision 002</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#171e1b;color:#edf2e9;font:16px/1.6 system-ui}main{max-width:1400px;margin:auto;padding:42px 28px}h1{font-size:clamp(32px,5vw,54px);line-height:1.1;max-width:900px}h2{font-size:27px;margin-top:46px}h3{margin:12px 16px 0;font-size:18px}p{max-width:980px}a{color:#b8d4a7}nav{display:flex;gap:12px;flex-wrap:wrap;margin:25px 0}nav a,.badge{border:1px solid #566750;padding:8px 14px;border-radius:8px;text-decoration:none}.badge{font-size:13px;display:inline-block;color:#dbe9b9}img{display:block;width:100%;height:auto}article{background:#253028;border:1px solid #38453b;border-radius:10px;overflow:hidden}article p{margin:4px 16px 16px;font-size:14px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.note{border-left:3px solid #aabc87;padding-left:16px;color:#c6cfc3}li{margin:7px 0}@media(max-width:850px){.grid,.pair{grid-template-columns:1fr}main{padding:24px 16px}}
</style></head><body><main><span class="badge">OFFLINE REVISION · UNREAL NOT CHANGED</span><h1>Paz Farm — visual fixes ready to apply</h1><p>Nine revised models, corrected ground colours and field rows, and a gate placement patch. Original assets and placement data are preserved. The model exports and ground mapping pass offline checks; final farm appearance still needs review in Unreal.</p>
<nav><a href="HANDOFF_CLAUDE.md">Operator handoff</a><a href="MANIFEST.json">Delivery manifest</a><a href="DONE.md">Completion note</a><a href="../../../Review/VISUAL_REVIEW.md">Visual review</a></nav>
<h2>Ground and field rows</h2><p>Fine furrows replace broad bands. Western crop colours vary by side. Strawberry soil shoulders follow the existing bed positions. This preview contains only the ground layer; trees, plants, barn and fence are separate.</p><div class="pair"><article><a href="../../../References/Screenshot%202026-10-08%20175537.png"><img src="../../../References/Screenshot%202026-10-08%20175537.png" alt="Real farm aerial reference"></a><h3>Real farm reference</h3><p>The photograph used for comparison.</p></article><article><a href="Previews/ground_v002_reference_aligned.png"><img src="Previews/ground_v002_reference_aligned.png" alt="Revised ground aligned to reference"></a><h3>Revised ground only</h3><p>Reference alignment for comparison; import texture remains north up.</p></article></div><nav><a href="Previews/GROUND_COMPARE.html">Reference / original / revision</a><a href="Georef/GROUND_SETTINGS.json">Editable ground settings</a><a href="Reports/GROUND_HANDOFF.md">Ground details</a></nav>
<h2>Fuller strawberry plants</h2><p>Geometric leaf coverage increased from 24.55% to 54.53%, with the same 0.8 × 4 m bed. All 763 placement transforms remain unchanged.</p><a href="Previews/SM_PazFarm_StrawberryBed_4m_Comparison.png"><img src="Previews/SM_PazFarm_StrawberryBed_4m_Comparison.png" alt="Original strawberry bed left and fuller revised bed right"></a>
<h2>Revised models</h2><p>Tree leaves now have real outline geometry and solid alpha. The barn has a matte charcoal roof with shallower corrugation. The 1.8 m figure in each preview is a scale guide and is not part of the export.</p><div class="grid">''' + ''.join(cards) + '''</div>
<h2>Gate correction</h2><p>The gate centre moves to east 24.266047 m / north 52.460000 m, aligning its 6 m envelope with the adjacent fence panels. Only its position and angle change in the staged data. Terrain height is left to the native operator.</p><nav><a href="Georef/PLACEMENT_PATCH.json">Gate-only patch</a><a href="Reports/placement_qa.json">Alignment check</a></nav>
<h2>What remains in Unreal</h2><ul><li>Verify distant crown retention and two-sided leaf materials at the original cameras.</li><li>Apply the ground and material changes, including the barn's new roof-only slot.</li><li>Check terrain contact, road overlap and gate clearance; add missing boundary vegetation when its native assets are identified.</li><li>Resolve the unknown eastern crop separately; current species, counts and scales are retained.</li></ul><p class="note">This is a Blender and ground-texture delivery, not a new Unreal screenshot. Native import, saves, reopen and visual acceptance have not been performed.</p><nav><a href="Reports/VALIDATION.json">Model verification</a><a href="Reports/GROUND_QA.json">Ground verification</a><a href="Reports/ORIGINALS_UNCHANGED.json">Original-file verification</a></nav></main></body></html>'''
(ROOT / 'INDEX.html').write_text(page, encoding='utf-8')
done = f'''# Paz Farm visual revision v002 — DONE

**Offline work complete; native application and visual acceptance remain pending.**

- Delivered **9 revised FBX models, 5 editable Blender sources and {len(textures)} material PNG maps**: seven trees with geometric leaf outlines, a fuller strawberry bed, and a matte charcoal barn roof.
- Delivered the corrected 2048² ground overlay with the original mapping, finer NE/SW rows, revised plot/road colours, phased strawberry shoulders and joined road endpoints. Editable defaults are in `Georef/GROUND_SETTINGS.json`.
- Prepared a **gate-only** centre-pivot placement patch. All 1,955 plant placements, 225 fence panels, 9 posts and the barn transform remain identical to the source.
- Independent offline checks pass: nine FBX round-trips, five Blender source reopens, triangle budgets, UVs, texture links, dimensions, full-white leaf alpha, exact ground PNG/mapping and strawberry band alignment within 7.64 mm.
- **{len(originals)} original staging/delivery files** match their pre-work SHA256 hashes. All new files are inside this revision folder.

Open [INDEX.html](INDEX.html) for previews. Give [HANDOFF_CLAUDE.md](HANDOFF_CLAUDE.md) and [MANIFEST.json](MANIFEST.json) to the native operator. The handoff ranks application steps and identifies remaining visibility, ground-contact, road and vegetation work. No Unreal, Content, map, bank, Houdini or git action was performed.
'''
(ROOT / 'DONE.md').write_text(done, encoding='utf-8')
print(json.dumps({'status': manifest['status'], 'assets':len(assets), 'blends':manifest['blend_count'], 'textures':len(textures), 'originals_checked':len(originals), 'originals_unchanged':preservation['passed']}))
