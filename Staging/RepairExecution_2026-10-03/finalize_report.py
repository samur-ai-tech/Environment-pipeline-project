"""Reconcile the active English handoff with the two actual saved r017 areas."""
from pathlib import Path
from collections import Counter
import json, hashlib, datetime, shutil

PROJECT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=PROJECT/'Staging/RepairExecution_2026-10-03'
SOURCE=Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank')
utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
definition=json.loads((SOURCE/'definition_receipt.json').read_text())
assert definition['revision']=='r017_retained_native_environment'
assert hashlib.sha256((SOURCE/'geocity_city_module.py').read_bytes()).hexdigest()==definition['module_sha256']
assert hashlib.sha256((SOURCE/'GeoCity_city_v015_PermanentBank.hdalc').read_bytes()).hexdigest()==definition['hda_sha256']
handoff=json.loads((HERE/'FINAL_EDITOR_HANDOFF.json').read_text())
assert handoff['named_area_dependencies_clean'] and not handoff['dirty_maps']
areas={}
for area,sub in [('GazaRimal','PermanentIntegration_2026-10-02'),('GazaShujaiya','GazaShujaiyaIntegration_2026-10-02')]:
    folder=PROJECT/'Staging/ModelBank'/sub
    profile=json.loads((folder/'AREA_PROFILE.json').read_text())
    state=json.loads((folder/'WORKFLOW_STATE.json').read_text())
    catalog=json.loads((folder/'HDA_CATALOG_RECEIPT.json').read_text())
    actual=json.loads((HERE/('REOPEN_'+area+'.json')).read_text())
    collision=json.loads((HERE/('COLLISION_'+area+'.json')).read_text())
    assert state['phase']=='baked_saved_verified' and state['generator_revision']==definition['revision']
    assert actual['native_count']==state['instance_count']
    assert actual['native_material_slots_verified'] and actual['all_native_anchor_locations_match_recipe_within_1mm']
    assert actual['persistence']['all_saved_baked_actors_present'] and not actual['dirty_maps']
    assembly=state['building_assembly']
    assert assembly['unsupported_count']==0
    proxy={k:{f:p.get(f,0) for f in ('source_count','removed_count','omitted_generated_count','remaining_count','remaining_primitives')} for k,p in catalog['proxy_outputs'].items()}
    assert all(p['remaining_count']==0 and p['remaining_primitives']==0 for p in proxy.values())
    areas[area]={'map':profile['map'],'profile':str(folder/'AREA_PROFILE.json'),
        'native_instance_count':state['instance_count'],'roles':dict(Counter(p['role'] for p in catalog['nonbuilding_instances'])),
        'whole_buildings':assembly['whole_native_building_count'],'assembled_buildings':assembly['assembled_building_count'],
        'building_count':assembly['whole_native_building_count']+assembly['assembled_building_count'],'unsupported_buildings':0,
        'baked_actor_count':state['baked_actor_count'],'named_generated_dependency_paths':state['named_generated_dependency_paths'],
        'landscape_count':1,'cooked_mesh_components':0,'proxy_outputs':proxy,
        'all_native_transferred_anchors_verified_within_1mm':True,'native_material_slots_verified':True,
        'sampled_native_buildings_for_collision':collision['sampled_native_buildings'],
        'maximum_sampled_bbox_support_error_cm':collision['maximum_absolute_support_error_cm'],
        'landscape_readback':actual['landscape_readback'],
        'persistence':actual['persistence'],
        'map_sha256':hashlib.sha256((PROJECT/'Content'/Path(profile['map'].removeprefix('/Game/'))).with_suffix('.umap').read_bytes()).hexdigest()}
result={'schema':'environmentpipeline.retained_repair_result.v1','utc':utc,
    'status':'implemented_saved_reopened','generator_revision':definition['revision'],
    'external_hda_sha256':definition['hda_sha256'],'module_sha256':definition['module_sha256'],
    'catalog_rows':1223,'normal_enabled_rows':18,'catalog_sha256':'135fda14b5173ca919b1568b3faff20e1763cfb3dc90c0635983d1ce32b3ded1',
    'areas':areas,'appearance_accepted':False,'held_assets_released':False,'editor_handoff':handoff}
(HERE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
table='| Area | Buildings | Whole native | Native assemblies | Native trees | Native poles | Native street props | Native part/asset instances |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n'
for area,a in areas.items():
    table+=f"| {area} | {a['building_count']} | {a['whole_buildings']} | {a['assembled_buildings']} | {a['roles']['tree']} | {a['roles']['street_pole']} | {a['roles']['street_prop']} | {a['native_instance_count']:,} |\n"
common=f'''Both real areas were regenerated, baked with scoped replacement, explicitly saved and opened again in the same editor with cooking paused and no recook. Every recorded native mesh/material reference and all transferred anchors were checked; maximum allowed anchor error is 1 mm. Both saved areas have one Landscape, 23 baked actors, zero cooked mesh components, zero proxy primitives and seven clean named generated dependencies plus their map. This is saved-map persistence in one editor, not a fresh-process restart claim.

{table}
The 34,025 native instances include 33,377 facade/filler/door module instances. They are not 34,025 distinct assets or buildings. There are 667 actual geographic building pads: 101 whole native buildings plus 566 retained native assemblies, zero unsupported pads. Floor/roof slabs and corner closures are generated closed geometry with existing native materials. Geographic source packages and native originals remain intact.
'''
repairs='''- Preserved height provenance: only actual source height/floor data imposes a hard height gate; seeded heights are preferences. Native whole-building scale remains 1:1.
- Closed the medium-building size gap with measured facade bays, bounded widths/story heights, 1 m/2 m filler panels, real steel-door openings, true footprint floors/roofs and clipped corner solids. Simple concave footprints are supported. The shared generated solids now use outward Houdini winding and aligned normals, fixing the visibly open/black roofs.
- Corrected terrain support on the authoritative grid: complete pad interpolation-cell support, coherent touching-pad datums and bounded graded collars. The generator checks full whole-building support. Live Landscape-only collision samples at four whole buildings per area measured maximum bbox support-plane errors of 1.047 cm in Rimal and 1.214 cm in Shujaiya; these are sampled bbox planes, not every foundation vertex.
- Derived roadside positions from native asset dimensions and bounded candidate searches; configured the supported non-held native utility pole for both areas. Street furniture and poles now survive the full footprint/clearance checks and appear as native baked instances.
- Applied bounded generated-tree fitting within the original vegetation seed cell. Final failed generated decorations are explicitly omitted rather than rendered as box/cylinder proxies. Rimal omitted 15 of 60 generated trees and 9 of 36 generated poles; Shujaiya omitted 35 of 114 trees and 4 of 57 poles. These 63 omissions are not native substitutions or deletion of surveyed source features.
- Retained previous successful baked-actor/package ledgers across failed runs. Optional empty outputs can disappear without leaving old baked copies; ordinary regeneration can still recognize exact unreferenced Cook leftovers after a failed attempt.
'''
limits='''Native assets and their materials are really referenced and retained. The selected variety remains narrow: repeated Courtyard facades, four whole-building models, one tree family, one utility-pole model and one street-prop model. Missing geographic height/storey/entrance data still uses explicit generator rules. Shrub/small-prop/understory requests that cannot fit remain rejected. Signs, roof utilities and vehicles are outside the assigned active asset lanes. Final artistic suitability and Aviv's visual acceptance remain open; counts and successful cooking do not imply that approval.

The current Landscape uses MI_SurfaceBank_AllLayers with Dirt_Path, Sand_01, Sand_02 and Sand_Path. Live readback verified all four area-local LayerInfo bindings and all eight native MOUT albedo/normal parameter values. Actual views show the textured route. The shared base MI's used-textures query returns an empty array and Python does not expose the component MaterialInstances property; this query is recorded as inconclusive about component shader sampling. No material compile error was found. Existing ray-tracing resident-memory viewport warning remains.

The same 1,223 catalog identities, qualification, rights and explicit holds remain. Eighteen scoped runtime rows are enabled (16 meshes and two materials); measured assembly dependencies use the separate normal-area contract without clearing unrelated prop-role projection holds. H0013, H0907, H0051, H0958 and declined palms remain held. No general bank release or new rights approval occurred.
'''
links='''- [Rimal actual viewport](RIMAL_R017_CAPTURE.png)
- [Shujaiya actual viewport](SHUJ_R017_CAPTURE.png)
- [Machine-readable result](RESULT.json)
- [Rimal saved-map readback](REOPEN_GazaRimal.json)
- [Shujaiya saved-map readback](REOPEN_GazaShujaiya.json)
- [Focused original diagnosis](../Diagnostics_2026-10-03/ROOT_CAUSE.txt)
- [Lifecycle audit](LIFECYCLE_AUDIT.txt)
- [Appearance limits](APPEARANCE_LIMITATIONS_DRAFT.txt)
'''
report=f'''# Retained environment repair result

Updated 2026-10-03, Asia/Jerusalem. Measured result: the requested generation, native coverage, support and roof defects are repaired in the shared r017 generator and both existing saved areas. Final artistic acceptance remains separate.

## Actual retained result

{common}
## Changes and verification

{repairs}
Official Engine completed the real replacements: Shujaiya r014 -> repaired r015/r016 -> r017 and Rimal r014 -> r017. Failed intermediate contract/API attempts are preserved; the final generator uses supported float4 orient attributes and forward-slash contract paths. Actual viewport inspection confirmed closed, lit roofs; an independent image read agreed for the Shujaiya elevated view.

## Exact retained paths

Shared HDA: `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank`.
External source: `C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank`.
Revision: `{definition['revision']}`.
HDA SHA256: `{definition['hda_sha256']}`.
PythonModule SHA256: `{definition['module_sha256']}`.
Native table: `/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4`.
Typed catalog digest: `{result['catalog_sha256']}`.

Rimal: `{areas['GazaRimal']['map']}`.
Shujaiya: `{areas['GazaShujaiya']['map']}`.
Ordinary project action: `Tools > GeoCity: Generate / Regenerate Current Area`. Its existing official lifecycle performs input rebinding, configured rebuild/cook, scoped previous-bake replacement, cooked-output removal and named dependency/map saves. No separate disposable demonstration or alternate generator was introduced.

## Limits and preservation

{limits}
## Editor handoff

OWNER=NONE; sole editor PID15568 left on GazaRimal. Official cooking paused, auto-cooking disabled, zero lifecycle callbacks, no dirty maps and no dirty named retained dependencies. {len(handoff['unsaved_content_packages'])} exact previously recorded unreferenced Cook packages remain unsaved; no broad save or deletion was used. Refresh ownership, processes, world and dirty state before later editor operations. Old heartbeat remains paused; no Linear work.

## Receipts

{links}'''
(HERE/'RESULT.md').write_text(report,encoding='utf-8')
archive=PROJECT/'Staging/Archive/RepairCompletion_2026-10-03'
archive.mkdir(parents=True,exist_ok=False)
paths=['AGENTS.md','Staging/CURRENT_STATE.md','Staging/WORK_PLAN.md','Staging/ManagedExecution_2026-10-02/MANAGER_STATUS.txt']
manifest=[]
for relative in paths:
    original=PROJECT/relative
    destination=archive/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(original,destination)
    manifest.append({'original':relative,'archive':str(destination.relative_to(PROJECT)),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()})
(archive/'MANIFEST.json').write_text(json.dumps({'utc':utc,'reason':'Superseded r014/repair-active instruction and status snapshots preserved before reconciling actual r017 saved/reopened outcome','files':manifest},indent=2)+'\n')
current=f'''# Environmentpipeline current state

Updated 2026-10-03, Asia/Jerusalem. Retained repair completed; this supersedes the r014 170/277-instance snapshots.

## Actual outcome

[measured: official Engine, live native readback, viewport inspection and saved-map reopen] The shared r017 generator repaired the selection/support/building-coverage/roadside/roof defects in both real areas. [Full result and receipts](RepairExecution_2026-10-03/RESULT.md).

{common}
Maps:
- `{areas['GazaRimal']['map']}`
- `{areas['GazaShujaiya']['map']}`

## Reusable generator and normal action

Shared HDA: `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank`. External source: `C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank`. Revision `{definition['revision']}`, external HDA SHA256 `{definition['hda_sha256']}`. Prior revisions/source and native originals are preserved.

`Tools > GeoCity: Generate / Regenerate Current Area` uses the current-map profile and official Houdini Engine input/rebuild/cook, scoped previous-bake replacement, cooked-output removal and named dependency/map saves. Successful actor/package ledgers persist across failures. This is the existing project route, not an added generator bridge.

Rimal profile: `Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json`; Shujaiya: `Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json`. Native table: `/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4`, 1,223 retained identities, 18 scoped enabled runtime rows, digest `{result['catalog_sha256']}`. Assembly uses the separate measured normal-area contract.

## Implemented repair

{repairs}
## Remaining appearance scope and preservation

{limits}
## Handoff

[measured: FINAL_EDITOR_HANDOFF.json] OWNER=NONE; one editor PID15568 on GazaRimal, cooking paused, auto-cooking disabled, zero callbacks, no dirty maps or named retained dependencies. {len(handoff['unsaved_content_packages'])} exact unreferenced Cook leftovers remain unsaved. Ordinary action acknowledges them only after exact-ledger/reference checks. No Save All, broad deletion, extra editor, held release or Linear work. Old heartbeat remains paused.

The [single plan](WORK_PLAN.md) and [repair assignment/result](RepairExecution_2026-10-03/ASSIGNMENT.json) govern this outcome. The five 2026-10-02 execution chats and their task receipts remain historical. Superseded active documents are preserved in [RepairCompletion archive](Archive/RepairCompletion_2026-10-03/MANIFEST.json); earlier dated archives remain intact. No fresh editor-process restart or final user appearance approval is claimed.
'''
(PROJECT/'Staging/CURRENT_STATE.md').write_text(current,encoding='utf-8')
plan=f'''# Environmentpipeline work plan

Updated 2026-10-03, Asia/Jerusalem. This remains the single active plan. [Current actual state](CURRENT_STATE.md); [retained repair result](RepairExecution_2026-10-03/RESULT.md). The repair assignment is complete and no editor assignment is active.

## Intended result

Real geographic source -> reusable Houdini HDA -> official Houdini Engine -> native Unreal environment. Houdini retains authoritative terrain, masks, roads, sidewalks and fitting placement/assembly rules; native models/materials transfer through `unreal_instance`. The ordinary action replaces scoped baked output and saves named dependencies. Existing native originals, geographic packages, catalog rights/holds and prior revisions are preserved.

## Delivered work

The five 2026-10-02 task chats delivered the r014 pipeline core and are historical. Aviv's 2026-10-03 instruction authorized retained repair until the actual result works. Root was the single editor writer, with independent source/audit collaborators. Their changes now remain in the shared r017 source and both existing maps.

{common}
{repairs}
Both areas use the same HDA and official lifecycle. No separate tests, disposable maps, alternative bridge, PCG migration or WorldBLD work order was introduced. The real saved areas were opened again without recooking to verify retained counts/materials/anchors and baked actors.

## Retained configuration

- Rimal map: `{areas['GazaRimal']['map']}`.
- Shujaiya map: `{areas['GazaShujaiya']['map']}`.
- Shared HDA: `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank`, `{definition['revision']}`.
- Shared native table: `/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4`, 1,223 identities; digest `{result['catalog_sha256']}`.
- Existing separate profiles: `Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json` and `Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json`.
- Geographic packages: `C:/Users/USER/Documents/Pipeline Environment/SourceData/{{GazaRimal|GazaShujaiya}}/city_source_v1.json`.
- Source: `C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank`.
- Ordinary action: `Tools > GeoCity: Generate / Regenerate Current Area`, using `Content/Python/geocity_bank_workflow.py` and `geocity_editor_action.py`.

## Current limits

{limits}
The diagnosed technical repair is delivered. No overall completion percentage or invented aesthetic approval is assigned. Future appearance work can use the current actual maps and shared generator; earlier worker queues do not restart automatically.

## Management and preservation

OWNER=NONE, sole editor PID15568 on GazaRimal; official cooking paused, auto-cooking disabled, callbacks0, named retained dependencies/maps clean. Refresh lease/live processes/world/dirty packages before later editor operations. A historical released PID is not a current lease. Exact unreferenced Cook leftovers remain recorded, unsaved and reference-checked; never Save All or delete broad assets to make a clean-looking editor.

Normal scopes cover only the two named areas. Preserve source packages, HDA revisions, catalog identities, native originals/materials and primary receipts. No new editor/license/plugin rebuild, held release or Linear work. The old heartbeat remains paused. Prior active documents were archived in [RepairCompletion manifest](Archive/RepairCompletion_2026-10-03/MANIFEST.json).
'''
(PROJECT/'Staging/WORK_PLAN.md').write_text(plan,encoding='utf-8')
status=f'''ENVIRONMENTPIPELINE — CURRENT RETAINED DELIVERY STATUS
2026-10-03, Asia/Jerusalem

The actual r017 repair supersedes this folder's historical r014 170/277-instance figures. Both existing areas were regenerated through official Houdini Engine, baked with scoped replacement, explicitly saved and reopened without recooking.

GazaRimal: 269 buildings (60 whole native +209 native assemblies), 45 native trees, 27 native poles, 23 native street props, 16,009 native part/asset instances.
GazaShujaiya: 398 buildings (41 whole native +357 native assemblies), 79 native trees, 53 native poles, 41 native street props, 18,016 native part/asset instances.
Both: 1 Landscape, 23 baked actors, 7 clean named generated dependencies plus map, zero unsupported building pads, zero cooked copies, zero remaining proxy primitives. Generated roof/floor/corner geometry uses native materials; native module counts are not distinct building counts.

Height provenance, medium-building native assembly, full terrain support, asset-aware roadside placement, generated-tree fitting, outward roof winding/normals and failure-safe previous-bake/package ledgers are retained shared fixes.
50 generated tree and 13 generated pole requests were deliberately omitted after failing safe fit; these are not native substitutions. Limited model variety, source-unknown seeded building details, partial minor-decoration coverage and final Aviv appearance approval remain explicit. Named holds/rights preserved.

Shared HDA: /Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank
External HDA SHA256: {definition['hda_sha256']}
Catalog digest: {result['catalog_sha256']}; same1223 identities,18 scoped enabled runtime rows plus separate measured native assembly dependencies.
Ordinary action: Tools > GeoCity: Generate / Regenerate Current Area.
Handoff: OWNER=NONE; editorPID15568 left on GazaRimal, cookingpaused/autooff, callbacks0, dirtymaps0, named retained dependenciesclean. Exact unreferenced Cook leftovers remain unsaved. No Save All, broad deletion or Linear work; old heartbeatpaused.

Authoritative result: Staging/RepairExecution_2026-10-03/RESULT.md and RESULT.json.
Saved-map readback: REOPEN_GazaRimal.json and REOPEN_GazaShujaiya.json in that folder.
Original five-task receipts remain history; superseded active-status documents were archived in Staging/Archive/RepairCompletion_2026-10-03/MANIFEST.json.
'''
(PROJECT/'Staging/ManagedExecution_2026-10-02/MANAGER_STATUS.txt').write_text(status,encoding='utf-8')
agents=(PROJECT/'AGENTS.md').read_text(encoding='utf-8')
new='[reported: manager, 2026-10-03] Retained r017 repair is implemented, saved and reopened in both actual areas: GazaRimal 269 buildings/16,009 native part instances; GazaShujaiya 398 buildings/18,016 native part instances. All667 source pads are covered by101 whole native buildings and566 native assemblies; native trees124, poles80 and street props64. Zero unsupported pads, proxy primitives or cooked mesh copies. Height provenance, graded support, measured assembly, roadside fitting, closed outward roofs and failure-safe regeneration ledgers are retained. Failed generated decorations were explicitly omitted (50 trees/13 poles); style variety and Aviv\'s visual acceptance remain separate. No editor assignment is active; OWNER=NONE, PID15568 on GazaRimal, cooking paused/autooff, callbacks0, named maps/dependencies clean. Current result: [RESULT.md](Staging/RepairExecution_2026-10-03/RESULT.md). Earlier queue paragraphs are historical and do not restart automatically.\n\n'
position=agents.index('[decided: Aviv, 2026-10-03')
agents=agents[:position]+new+agents[position:]
agents=agents.replace('[decided: Aviv, 2026-10-02, latest instruction]', '[historical decided: Aviv, 2026-10-02]')
agents=agents.replace('[reported: manager, 2026-10-02]', '[historical reported: manager, 2026-10-02; superseded by r017 repair]')
(PROJECT/'AGENTS.md').write_text(agents,encoding='utf-8')
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text())
assignment.update(status='implemented_saved_reopened',completed_utc=utc,result='Staging/RepairExecution_2026-10-03/RESULT.md',editor_assignment_active=False,appearance_accepted=False)
(HERE/'ASSIGNMENT.json').write_text(json.dumps(assignment,indent=2)+'\n')
definition.update(status='implemented_saved_reopened',integrated_utc=utc,
    validation='Actual official Engine r017 replacement/Bake/named saves completed in both existing areas; all667 pads covered, native material/anchor counts checked, closed roofs visually inspected, both saved maps unloaded/reopened without recook. Same-editor persistence; no fresh process restart or final appearance acceptance.',
    actual_area_results={area:{k:a[k] for k in ('building_count','whole_buildings','assembled_buildings','native_instance_count','map')} for area,a in areas.items()})
(SOURCE/'definition_receipt.json').write_text(json.dumps(definition,indent=2)+'\n')
print(json.dumps({'result':str(HERE/'RESULT.md'),'native_instances':sum(a['native_instance_count'] for a in areas.values()),'buildings':sum(a['building_count'] for a in areas.values()),'status':assignment['status'],'active_documents_reconciled':True}))
