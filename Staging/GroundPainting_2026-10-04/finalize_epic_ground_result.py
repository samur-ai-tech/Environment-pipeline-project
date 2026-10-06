"""Read existing receipts/files; write only the final bounded Staging report."""
import datetime, hashlib, json, struct, subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
rev = here / 'Revision_2026-10-05'
root = here.parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def checked(name, expected):
    p = rev / name
    assert sha(p) == expected, name
    return json.loads(p.read_text()), {'file':str(p), 'sha256':expected}

sh, sh_ref = checked('EPIC_RESIDENT_CONSUMER_verify_r030_fresh_reopen_PID18844.json', '18eacb5f538be6bfb53bd3749bfc0d39a268947896ecc8d42cb8a51339e6017b')
ri, ri_ref = checked('EPIC_RESIDENT_RIMAL_verify_r031_epic_fresh_reopen_PID35000.json', 'c6b74f0f9fe5dd64d9027ac9fca253c99d878925c167e077394912158f302d4b')
shv, shv_ref = checked('VISUAL_REVIEW_GazaShujaiya_epic_r030_fresh_PID18844.json', '2f26742079d35669980494156e4fc7d81b9421baef1f4aa1d5db824dbd69a962')
riv, riv_ref = checked('VISUAL_REVIEW_GazaRimal_epic_r031_fresh_PID35000.json', 'd197aa756051da71c36e5c28e8eb4bb3ce2a8b41b0a914a931f2f209302e5504')
ss, ss_ref = checked('EPIC_RESIDENT_CONSUMER_NAMED_SAVE_GazaShujaiya_r030_epic_complete_PID26820.json', '0939c4a2f543367c775ca780c4f40b10ddd602d1261094a06b2986bec8edce8e')
rs, rs_ref = checked('SAVE_GazaRimal_epic_r031_PID25008.json', 'ebd73bd476bee8550a64a973a717be04eb98ade2c8dab5a28b78916aa8d43ae3')
audit, audit_ref = checked('EPIC_RIMAL_NAMED_SAVE_FILE_REVIEW_R031.json', '6c8d0bddb6193647a5265ced5eace9c3278d3a9ac3b71a06ef03791a4f94a41a')
epic, epic_ref = checked('EPIC_STARTER_GROUND_NATIVE_READONLY_PID32464.json', '9b7785af647a3eaf5674cf45c8f1b56aa9d80da1f02d0848da46ebad391598b6')

for d, v in ((sh, shv), (ri, riv)):
    assert d['dirty'] == {'maps':[], 'content':[]}
    assert d['native_mutation'] is False and d['graph_count'] == 1015
    for k in ('preserved_1015_nodes','preserved_69_layer_names','preserved_grass','preserved_scene','preserved_cvars','preserved_original_files','preserved_epic_texture_properties','all_four_resources_strict_ready','copy_properties_match_except_policy_and_inactive_normal_gamma'):
        assert d[k] is True, k
    assert v['pid'] == d['pid'] and v['world'] == d['world']
    assert v['fresh_process_visual_persistence_approved'] is True
    assert len(v['images']) == 3
    for image, record in v['images'].items():
        p = Path(image)
        assert sha(p) == record['sha256']
        assert struct.unpack('>II', p.read_bytes()[16:24]) == (1600,1000)
        assert record['camera_matches'] and record['actual_lit_measured'] and record['viewmode'] == 3

ri_mi = '/Game/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround'
assert rs['named_packages'] == [ri_mi] and rs['after'] == {'content':[], 'maps':[]}
assert ri['preserved_resident_copy_files'] is True
# The earlier Shujaiya helper guards the saved copy files internally; its schema
# exposes the property comparison scope rather than the later Rimal boolean.
assert sh['copy_property_comparison_scope'] == 'ALL_FOUR'
assert len(ss['named_packages']) == 5
assert audit['tracked_files_checked'] == 117 and audit['tracked_files_unchanged'] == 116
assets = {
    'Shujaiya_child': ('Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround.uasset','0f1f68f1d0b7246fae38a8d76a834bd8e67bda511ee31e056b50eabd0896b3a3'),
    'Rimal_child': ('Content/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround.uasset','99ad6bb82076350867e8487927053def0acc74b54805b58aa1c55079eb86d33b'),
    'Natural_master': ('Content/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.uasset','bea25944f8aab25584cd01cfd7ec7556a301b8188f4ef2ac9bc91f7a569dc347'),
    'Shujaiya_original_map': ('Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap','17d5929a02b03d9e022c0043ec95bcd99ad030574959ecd6b6812a0b5d49fba3'),
    'Rimal_original_map': ('Content/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.umap','a6961c8e017901e61ccd3f64aa5d77dd881d83f5f17a410f45ff571103c2d8fd'),
}
files = {}
for name, (relative, expected) in assets.items():
    p = root / relative
    assert sha(p) == expected, name
    files[name] = {'file':str(p), 'sha256':expected}
for path, record in ri['copies'].items():
    disk = record['disk']
    assert sha(disk['file']) == disk['sha256'], path
    files[path] = disk

command = "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'UnrealEditor|Houdini|HARS' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"
assert not subprocess.check_output(['powershell','-NoProfile','-Command',command], text=True).strip()
lease_path = root / 'Staging/ModelBank/EDITOR_OWNER.txt'
last = [s for s in lease_path.read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
assert 'OWNER=NONE' in last and 'previous_editor_PID=35000' in last
exits = []
for pid in (18844,25008,35000):
    p = here / f'EXIT_PID{pid}.json'
    d = json.loads(p.read_text())
    assert d['clean'] and d['paused'] and d['shutdown_saves'] == 0 and d['forced_termination'] is False
    exits.append({'file':str(p),'sha256':sha(p),'pid':pid,'shutdown_saves':0})

result = {
    'schema':'environmentpipeline.epic_ground_result.v1',
    'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'execution_thread_id':'01a10883-481f-7723-bdaa-fed004f15ef1',
    'task_status':'EPIC_GROUND_SOURCE_CHECKPOINT_SAVED_FRESH_REOPENED_WITH_VISUAL_LIMITS',
    'source_policy':'Installed original Unreal/Epic StarterContent gravel/sandstone D/N and original Epic macro; neutral tint. Retained Natural material adapts these sources, not a clone of the complete Epic master graphs.',
    'source_native_evidence':epic_ref,
    'ground_roles':{'Ground/Sand_01':'Epic gravel','Steep/Sand_02':'Epic sandstone','RoadBed/Dirt_Path':'Epic gravel','BuildingPad/Sand_Path':'Epic gravel','Ground_MacroSoilAlbedo/Normal':'Epic sandstone','Ground_MacroMask':'Original Epic T_MacroVariation'},
    'copy_policy':{'shared_copies':4,'size':2048,'never_stream':True,'max_texture_size':2048,'source_upscale':False,'global_residency_force':False,'global_cvar_changes':False,'original_assets_modified':False},
    'material_adaptation':{'master_revision':'Earlier r027:8existing Roughness/AO root edges and3macro default/sampler properties; no nodes added. Subsequent resident phases:zero master edits.','graph_nodes':1015,'layer_names':69,'other_layer_contracts_preserved':65,'roughness':0.8,'ao':1,'target_tints':[1,1,1,1],'normal_exception':'Captured normal-copy use_legacy_gamma=False versus source=True. Both are sRGB=False/TC_NORMALMAP; installed gamma-space implementation is Linear. Final helper has no gamma setter. Property comparison covers30records/28readable/2unavailable, not every SDK field.'},
    'areas':{
        'GazaShujaiya':{'world':sh['world'],'save_pid':26820,'fresh_pid':18844,'named_save':ss_ref,'fresh_native':sh_ref,'fresh_visual':shv_ref,'consumer_binding_count':10,'actors':316,'landscapes':2,'images':shv['images']},
        'GazaRimal':{'world':ri['world'],'save_pid':25008,'fresh_pid':35000,'named_save':rs_ref,'fresh_native':ri_ref,'fresh_visual':riv_ref,'independent_saved_file_review':audit_ref,'texture_bindings':11,'changed_controls':27,'actors':121,'landscapes':1,'images':riv['images']},
    },
    'preserved':{'original_maps_this_epic_phase':True,'geographic_heights_weights_scene':True,'grass_graph_settings_coverage_zero':True,'sealed_sources_profiles_catalogue_holds_native_originals':True,'cooked_mesh_or_actor_edits':False},
    'saved_files':files,
    'acceptance':{'technical_saved_reopened':True,'matched_lit_visual_persistence':True,'ordinary_regeneration':'NOT_RUN','cooked_runtime_platform_validation':'NOT_RUN','reference_quality':False,'whole_environment_accepted':False,'user_visual_acceptance':'PENDING'},
    'remaining_visual_work':['Ground remains pale and uniform at middle/wide distances.','Faint directional repetition and broad angular shading remain; their cause is not established.','Rimal smooth raised strips, sharp surface edges, road joins/patches and building contact remain.','Reference demonstrations also involve height blending, RVT/contact and geometric detail; Epic palette substitution alone does not establish that result.'],
    'handoff':{'owner':'NONE','live_native_processes':0,'last_lease':last,'clean_exits':exits,'ordinary_generation_authorized':False},
}
out = rev / 'RESULT.json'
txt = rev / 'RESULT.txt'
assert not out.exists() and not txt.exists()
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
text = f'''EPIC GROUND SOURCE CHECKPOINT — 2026-10-05

Both original areas now use installed Unreal/Epic StarterContent ground sources. Named saves and fresh-process native and actual-Lit persistence passed for Shujaiya and Rimal. This fulfills the bounded Epic-source ground change. Overall scene/reference quality and user acceptance remain open.

WHAT CHANGED
Gravel D/N supplies Ground, RoadBed and BuildingPad; sandstone D/N supplies Steep and both active macro-soil consumers. Original Epic T_MacroVariation supplies the macro mask. All four target tints are neutral1. The former active custom-bank macro-soil fallback has been replaced. Other65 layer contracts and their inactive native assets remain preserved.

Four owned2K copies under /Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/EpicResident2K keep source detail ready in fresh close captures. They use NeverStream=True and MaxTextureSize=2048. The sources were already2K; no upscale, global mip force, pool/CVar or original-asset changes occurred. Original streamed textures previously read Current/Wanted128 while the close programmatic viewport capture retained a wide registered streaming view. This proves the measured capture-demand mismatch, not a general Unreal streaming defect.

Epic textures are adapted to the retained Natural material. Earlier r027 rewired8existing Roughness/AO root edges and3macro default/sampler properties; no new nodes were added. The copy/consumer phases made zero master edits. Constant roughness.8 and AO1 are the retained shader adaptation, not an exact clone of Epic's texture/macro-driven PBR graph. The complete1015-node graph,69names, other65contracts and Grass are preserved.

The normal copies carry use_legacy_gamma=False while originals carryTrue. Both use sRGB=False/TC_NORMALMAP. Installed Texture.h/TextureCompressorModule.h return Linear when sRGB is disabled; the final helper never sets this flag. This is an explicit inactive normal-only difference.30captured property records comprise28readable/two unavailable fields; unknown SDK fields and GPU bitwise equality are not claimed. Official API context: https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UTexture?lang=en-US

MEASURED SAVES AND PERSISTENCE
Shujaiya PID26820 saved exactly its childMI plus four resident copies. Fresh PID18844 verified saved hashes,10consumer bindings, strict2048 readiness, graph/source/scene/Grass/CVar preservation and all-clean state. All three matched actual1600x1000 Lit views retain close pebble/grain detail.

Rimal PID25008 saved exactly its existing childMI after full27-control readback:11texture bindings,8scalars and8neutral-tint/tile vectors. Fresh PID35000 verified the same values, saved childSHA99ad6bb82076350867e8487927053def0acc74b54805b58aa1c55079eb86d33b, strict2K copies and all-clean state. All three matched actual1600x1000 Lit views preserve the improved ground without fresh blur or return of brown cloudy pit chains. Independent disk review found only Rimal child changed among117trackedfiles; other116were unchanged.

Original map files, source/vendor originals, native scene/geographic heights/weights, sealed sources/profiles, catalog/holds and Grass graph/settings/coverage0 remain preserved. Scenes retain316actors/twoLandscapes in Shujaiya and121actors/oneLandscape in Rimal. No HDA, Cook/Bake, generation, terrain geometry, lighting, road/building or catalogue edits were performed in this material phase.

VISIBLE LIMITS
The close ground is clearer, especially Shujaiya. Middle/wide ground remains pale and uniform, with faint repetition and angular shading whose cause is unproven. Rimal smooth raised strips, sharp joins, road patches and building contact remain. The selected references use additional height blending/RVT/contact/geometric detail; palette replacement alone does not achieve their quality. Overall appearance/user acceptance is PENDING; ordinary regeneration and cooked/runtime-platform validation are NOT_RUN.

CLEAN RELEASE
Fresh PID35000 exited normally with clean packages, cooking paused, callbacks0 and shutdown saves0. No Unreal/Houdini/HARS process remains. OWNER=NONE; ordinary_generation_authorized=false. Earlier RESULT documents, backups and failed native creation receipts remain intact.

READING SET
Structured final evidence: {out}
Shujaiya named save: {ss_ref['file']}
Shujaiya fresh native: {sh_ref['file']}
Shujaiya fresh visual: {shv_ref['file']}
Rimal named save: {rs_ref['file']}
Rimal fresh native: {ri_ref['file']}
Rimal fresh visual: {riv_ref['file']}
Rimal independent file audit: {audit_ref['file']}
Native Epic source study: {epic_ref['file']}
Actual images: {here / 'Images'}
'''
txt.write_text(text, encoding='utf-8')
print(json.dumps({'result':str(out),'result_sha256':sha(out),'report':str(txt),'report_sha256':sha(txt),'both_saved_reopened':True,'owner':'NONE','live_native_processes':0}))
