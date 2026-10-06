import json,pathlib,collections,re
P=pathlib.Path(__file__).resolve().parent
D=json.loads((P/'native_inventory_complete.json').read_text())
I=json.loads((P/'native_inventory_raw.json').read_text())
F=json.loads((P/'final_readonly_check.json').read_text())
A={a['path']:a for a in D['assets']}
mw=[a for a in A.values() if a['path'].startswith('/Game/MWLandscapeAutoMaterial/')]
def closure(a,seen=None):
    seen=set() if seen is None else seen
    if a['path'] in seen:return []
    seen.add(a['path']);out=[a]
    for n in a.get('nodes',[]):
        f=n['properties'].get('material_function')
        if f in A:out+=closure(A[f],seen)
    return out
def root(a):
    while a.get('parent') in A:a=A[a['parent']]
    return a
def definitions(a):
    d={}
    for a in closure(root(a)):
        for n in a.get('nodes',[]):
            p=n['properties']
            if 'Parameter' in n['class'] and 'parameter_name' in p:
                d.setdefault(p['parameter_name'],{'group':p.get('group','None'),'default':p.get('default_value',p.get('texture')),'declaration_class':n['class'],'source_asset':a['path'],'source_node':n['name']})
    return d
materials=[]
for a in mw:
    if a['class'] not in ['Material','MaterialInstanceConstant']:continue
    defs=definitions(a);par=[]
    pv={p['name']:p['effective_value'] for p in A.get(a.get('parent'),{}).get('parameters',[])}
    for p in a['parameters']:
        z=dict(p);z.update(defs.get(p['name'],{}));z['differs_from_parent']=a['class']=='MaterialInstanceConstant' and p['effective_value']!=pv.get(p['name']);par.append(z)
    materials.append({'path':a['path'],'class':a['class'],'parent':a.get('parent'),'parameters':par,'statistics':a.get('statistics'),'scalar_overrides':a.get('scalar_parameter_values'),'vector_overrides':a.get('vector_parameter_values'),'texture_overrides':a.get('texture_parameter_values')})
descs={
'MF_MWAM_DefaultLayer':[
'Samples color and normal at near/far UVs. Color alpha = DepthFadeMask * 0.75. Static options apply color correction, normal XY intensity and UV multipliers. Four Shared:Wrap sample nodes. No bombing, stochastic rotation, triplanar or height blend.',
'Yes with explicit inputs. Set WaterRefractionUV=(0,0), white ColorCorrection, NormalIntensity=1 and deliberate static booleans. ColorCorrection preview is black. NormalNear/NormalFar are separate outputs, not a final distance-normal blend.'],
'MF_MWAM_DepthFade':[
'Engine CameraDepthFade, For Vertex Shader=true. Parameters MW_DistanceBlendFadeLength=4096 and MW_DistanceBlendFadeOffset=512. This is camera distance, not scene intersection DepthFade.',
'Yes; shared MW parameter names will appear on the caller. Wrap/remap for independent per-role control.'],
'MF_MWAM_LandscapeUVs':[
'Selects LandscapeLayerCoords or world XY, with MW_LandscapeWorldUVSize=384; MW_UseWorldPositionUVs=true. Also returns raw world XY. Planar, not triplanar.',
'Yes on our Landscape. Contains LandscapeLayerCoords but no painted-layer names. Prefer feeding retained world XY UVs directly to DefaultLayer to retain existing scale control.'],
'MF_MWAM_LayerBlend':[
'Sequential Rock/Stones/Grass/Dirt color and normal blends with optional Snow normals, supplied masks and distance alpha. Uses MW_UseSnow. Not LandscapeLayerBlend and not texture-height blending.',
'Technically callable, but not a direct replacement for our named-weight blends. Its slots/order encode MW biomes; prefer reusable per-role sampling functions.'],
'MF_MWAM_Roughness':[
'pow((MW_UseInvertedRoughness ? 1-input : input) * MW_RoughnessMultiplier, MW_RoughnessPower), defaults true/1/0.5. No texture unpacking. The master supplies color-derived modulation times weighted per-role scalars.',
'Yes, but default behavior is not identity. Gate and clamp separately. Do not describe color-derived roughness as a measured roughness map.'],
'MF_MWAM_CombineNormal':[
'Lerps each normal from flat (0,0,1) with intensity, adds XY and multiplies Z. Normalize node exists but is not on the output connection.',
'Yes with explicit intensities and compatible tangent-space normals. Normalize in the new enabled branch as appropriate.'],
'MF_MWAM_CombineNormalSimple':[
'Adds normal XY and multiplies Z. No texture fetches.',
'Yes for compatible tangent-space normals. Combine is not a distance fade.'],
'MF_MWAM_SlopeMask':[
'Engine SlopeMask calls combine pixel-normal and base-slope responses with world-elevation gating; separate color/normal mask outputs.',
'Conditional: do not connect the PixelNormalWS-dependent SlopeMask output back into Normal. SlopeNormalMask is the separate route. Do not replace geographic paint weights with its absolute elevation thresholds.'],
'MF_MWAM_SnowMask':[
'World elevation, input noise and slope, with pixel/vertex normals, produce separate snow masks.',
'Callable but unnecessary for Gaza dry ground. Pixel-normal result must not drive a normal feedback loop.'],
'MF_MWAM_Snow':[
'Blends BaseColor toward SnowBaseColor with SnowPixelMask, gated by MW_UseSnow.',
'Callable; omit for dry Gaza.'],
'MF_MWAM_WaterMask':[
'Slope/elevation/noise mask, snow exclusion and MW_UseWater switch.',
'Callable; omit for dry Gaza. Not an object-contact detector.'],
'MW_MWAM_Water':[
'Two panned water-normal samples, normal combine, mask-driven color/specular/roughness/metallic and WaterRefractionUV; MW_UseWater switch.',
'Callable with inputs; omit for dry ground. Wetness/puddles are not RVT or road/building contact.'],
'MF_MWAM_PivotMask':[
'World position relative to engine ObjectPivotPoint makes an object-height mask for cover/foliage.',
'Technically callable, but Landscape pivot does not identify building footprints. Not a contact solution.'],
'MF_MWAM_SubSurface':[
'Optional subsurface texture/base-color path with color and intensity controls for foliage.',
'Callable but not useful for opaque DefaultLit ground without a shading change outside this proposal.'],
'MF_MWAM_Opacity':[
'Foliage opacity, camera-distance fade and DitherTemporalAA controls.',
'Not appropriate for the retained opaque ground contact problem; do not import its opacity/dither behavior.']}
functions=[]
for a in mw:
    if a['class']!='MaterialFunction':continue
    name=a['path'].split('.')[-1]
    pins=lambda c:[dict(n['properties'],node=n['name'],preview_connections=n.get('input_nodes',[])) for n in a['nodes'] if n['class']==c]
    ps={}
    for n in a['nodes']:
        p=n['properties']
        if 'Parameter' in n['class'] and 'parameter_name' in p:ps.setdefault(p['parameter_name'],{'name':p['parameter_name'],'type':n['class'],'default':p.get('default_value',p.get('texture')),'group':p.get('group')})
    functions.append({'path':a['path'],'purpose':descs[name][0],'call_as_is':descs[name][1],'inputs':pins('MaterialExpressionFunctionInput'),'outputs':pins('MaterialExpressionFunctionOutput'),'parameters':list(ps.values()),'dependencies':sorted(set(n['properties']['material_function'] for n in a['nodes'] if n['properties'].get('material_function'))),'MW_layer_names':[],'requires_RVT':False,'landscape_nodes':[n['class'] for n in a['nodes'] if 'Landscape' in n['class']],'sample_nodes':[{'node':n['name'],'sampler_source':n['properties'].get('sampler_source')} for n in a['nodes'] if 'TextureSample' in n['class']]})
tex=[{k:a.get(k) for k in ['path','class','size_x','size_y','registry_dimensions','compression_settings','srgb','lod_group','max_texture_size','lod_bias','virtual_texture_streaming','compression_no_alpha']} for a in mw if a['class'] in ['Texture2D','TextureRenderTarget2D']]
fits={'SandA':'Recommended dry-sand candidate. Fine warm brown thumbnail; not inherently pale Gaza soil.','SandC':'Recommended compact dry-soil/sand variation candidate. Brown with coarser clumps than SandA.','Stones':'Conditional gray gravel/stone candidate; value/scale-match. DesertExample uses this in its Rock slot.','Dirt':'Conditional, not first pale-soil choice. Thumbnail is dark olive-brown/organic.','Rock':'Conditional dark rock. Thumbnail is dark gray; pale limestone suitability is unverified.','Grass':'Exclude from dry soil palette; grass role.','Snow':'Exclude from dry Gaza.'}
sets=[{'ground_type':k,'gaza_fit':v,'textures':[t for t in tex if '/Textures/Ground/TEX_MWAM_'+k+'_' in t['path']],'ORM_or_separate_PBR':[],'height_texture':None} for k,v in fits.items()]
B='/Game/Project/Shared/SurfacePainting/Appearance_20261003/'
master=A[B+'M_SurfaceBank_Natural.M_SurfaceBank_Natural']
children=[a['path'] for a in A.values() if a['path'].startswith('/Game/Project/Areas/Gaza')]
grass=[n for n in master['nodes'] if n['properties'].get('desc','').startswith('GeoCity_LandscapeGrass')]
def fp(n):return '/Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/'+n+'.'+n
def tp(n):return '/Game/MWLandscapeAutoMaterial/Textures/'+n+'.'+n.split('/')[-1]
mapping=[
{'defect':'No color variety','assets':[fp('MF_MWAM_DefaultLayer'),tp('Ground/TEX_MWAM_SandA_col'),tp('Ground/TEX_MWAM_SandC_col'),tp('Ground/TEX_MWAM_Stones_col'),tp('Extra/TEX_MWAM_Variation_msk')],'wiring':'Keep the existing named-layer blends and wider bank palette. Add new GeoCity_MW texture-object parameters inside a default-off switch: SandA for Ground, SandC for soil partner/BuildingPad, conditional Stones for stony RoadBed/Steep. After LandscapeLayerBlend_6, apply coherent world-XY macro color with default amount 0.','limit':'MW macro color is inline mask RGB * blended color * 1.5, not a named macro function. A proposed MF_GeoCity_MW_MacroColor would be new project logic. Use white-to-variation interpolation so amount 0 is identity.'},
{'defect':'Pale/uniform at distance','assets':[fp('MF_MWAM_DepthFade'),fp('MF_MWAM_DefaultLayer'),tp('Extra/TEX_MWAM_Variation_msk')],'wiring':'Use retained world XY near/far UVs and camera-distance fade in DefaultLayer. Add a project far-color target with amount 0 by default. Separately gate a normal fade toward (0,0,1) after LandscapeLayerBlend_7.','limit':'MW blends the same texture at two scales with alpha=0.75*DepthFadeMask; this does not change its far mip mean reliably. A controlled far color is added project logic, not a discovered MW feature. Lighting/exposure was not diagnosed.'},
{'defect':'Visible repetition','assets':[fp('MF_MWAM_DefaultLayer'),fp('MF_MWAM_CombineNormal'),tp('Extra/TEX_MWAM_Variation_msk'),tp('Extra/TEX_MWAM_Variation_nrm')],'wiring':'Use distance sampling and coherent macro variation across the four roles. Preserve ratified GeoCity_GroundStochastic_20261005 and review its active routes before replacing sampling inputs. Avoid stacking a second expensive sampler system.','limit':'No MW UV bombing, stochastic rotation or triplanar function found. Stronger anti-tiling requires retained/custom logic; UV rotation must rotate normal XY consistently.'},
{'defect':'Sharp joins','assets':[tp('Extra/TEX_MWAM_Variation_msk'),tp('FX/TEX_MW_Noise_msk'),fp('MF_MWAM_LayerBlend')],'wiring':'Share macro variation across seams. Keep geographic weights/names and Grass input untouched. Future appearance-only noise modulation may refine existing fractional transition weights, with renormalization.','limit':'MF_MWAM_LayerBlend is not height blending. No MW height map found. A pointwise remap cannot widen a binary mask into a spatial feather. Wider masks remain manager-owned producer work.'},
{'defect':'No contact with buildings/roads','assets':[fp('MF_MWAM_DepthFade'),fp('MF_MWAM_PivotMask'),fp('MW_MWAM_Water')],'wiring':'Do not use these functions as contact detectors. Later provide a real road/pad edge-distance/contact mask, then separately gate a subtle darkening/roughness band without altering Grass exclusions.','limit':'CameraDepthFade is camera distance, PivotMask is object pivot and Water is wetness. Pack has no RVT/contact system or geometry grounding repair. These cannot close physical gaps; contact geometry/decal/RVT work is not delivered.'}]
incident={'status':'UNEXPECTED_INSPECTION_SIDE_EFFECT_PRESERVED_UNSAVED','new_dirty_packages':sorted(set(F['dirty_content'])-set(I['before']['dirty_content'])),'explanation':'Both Python property/graph passes ended with only the pre-existing dirty Cook mesh. Later get_material_info queries covered 15 MW functions; final readback found the same 15 packages dirty. Tool-related dirtying is the leading inference; exact engine-side changes are unproved. No explicit asset setter, save, cook/bake, map switch, owner write or editor close was issued. Editor calls stopped on discovery; buffers untouched.','before':I['before'],'final':F}
license={'status':'No license/readme/terms/EULA file found. Usage and redistribution terms not established.','checked_roots':['C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/MWLandscapeAutoMaterial','C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/MWLandsc0bb389159dceV3'],'project_files':100,'vault_non_asset_files':['manifest'],'interpretation':'Local assets and Launcher manifest are not a license receipt. No generic Fab/Marketplace permission is inferred.'}
docs=[{'title':'Epic Landscape Materials','url':'https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine'},{'title':'Epic MaterialExpressionTextureSample API','url':'https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialExpressionTextureSample?application_version=5.6'}]
R={'schema':'MW_READONLY_MATERIAL_INVENTORY_v1','date':'2026-10-05','manager':'Claude Code cc37d4d2-3d62-4f53-b689-28432b5527ae','scope':'Inventory/proposal only; read inspection_side_effect first.','inspection_side_effect':incident,'catalog':D['catalog'],'materials_and_instances':materials,'functions':functions,'texture_sets':sets,'all_textures':tex,'features':{'painted_layers':['RemoveFoliage'],'LandscapeLayerBlend_count':0,'RVT_nodes':0,'RVT_assets':0,'triplanar_found':False,'UV_bombing_found':False,'height_blend_found':False,'macro_variation':'Inline in MW master','grass_outputs':['Rock','Stones','Grass','Dirt','Snow'],'physical_outputs':['PM_MW_Rocks','PM_MW_Stones','PM_MW_Grass','PM_MW_Dirt','PM_MW_Snow','PM_MW_Water']},'retained_contract':{'master':master['path'],'base_MI':B+'MI_SurfaceBank_Natural.MI_SurfaceBank_Natural','gaza_children':children,'roles_to_actual_layers':{'Ground':'Sand_01','Steep':'Sand_02','RoadBed':'Dirt_Path','BuildingPad':'Sand_Path'},'grass_nodes':grass,'outputs':master['material_outputs'],'expression_count':len(master['nodes']),'live_binding':json.loads((P/'live_landscape_binding.json').read_text()),'Iran':'Profile uses base MI directly; Iran world not loaded.'},'mapping_proposal':mapping,'neutral_enablement':{'static_switch':'GeoCity_MW_Enable','default':False,'base_MI':'Unchanged','gaza_children':'Enable only these two in later manager-authorized implementation','amount_defaults':0,'tint_defaults':'white','false_branch':'Exact current BaseColor/Normal/Roughness/AO output paths and existing stochastic graph','profile_safety':'Prefer new GeoCity_MW texture parameters. Preserve profile-validated Sand_01_Normal/Sand_02_Normal bindings; any replacement needs manager-owned profile reconciliation.'},'license':license,'demo_screenshots':{'captured':0,'maps':[c['path'] for c in D['catalog'] if c['class']=='World'],'reason':'No map switch: preserve current Shujaiya and dirty buffer. Five saved 256px texture thumbnails are supplemental, not Lit landscape evidence.'},'official_docs':docs}
(P/'MW_INVENTORY.json').write_text(json.dumps(R,indent=2),encoding='utf-8')
def v(x):
    if x is None:return 'None'
    if isinstance(x,bool):return str(x).lower()
    if isinstance(x,float):return f'{x:.8g}'
    if isinstance(x,dict):return ', '.join(k+'='+v(y) for k,y in x.items())
    return str(x).replace('|','\\|').replace('\n',' ')
def table(h,rows):
    return '\n'.join(['| '+' | '.join(h)+' |','|'+'|'.join('---' for x in h)+'|']+['| '+' | '.join(v(x) for x in r)+' |' for r in rows])
L=['# MW material inventory — 2026-10-05','',
'For Claude Code manager cc37d4d2-3d62-4f53-b689-28432b5527ae under Aviv’s read-only instruction. Inspected UE 5.8 PID 10460, original Shujaiya. This is an inventory and proposal, not an implemented or accepted repair.','',
'## Inspection side effect — preserved unsaved','',
'**No save was issued; all 107 monitored disk files are unchanged. However, 15 MW material-function packages became newly dirty in memory during inspection.** The map stayed clean; the pre-existing dirty generated Cook mesh remains. The newly dirty set matches the 15 functions queried by the advertised get_material_info read tool. Earlier Python inspection passes ended with unchanged dirty state. The precise engine-side mutation has not been established. Editor calls stopped on discovery; no save, discard, dirty-flag reset or close was attempted. This is not an entirely unchanged editor state.','',
'Exact packages and timestamps are in MW_INVENTORY.json → inspection_side_effect and final_readonly_check.json. No lease/owner write, asset setter, Cook/Bake, Save All or map load was issued. Files authored by this task are restricted to this inventory directory.','',
'## Findings','',
'- 100 pack assets: 4 actual master Materials, 14 MaterialInstanceConstants, 15 functions, 32 Texture2Ds, 3 render targets, plus supporting assets. MTL_MWAM_Plant_Megascan_MASTER is actually an instance.',
'- Landscape master exposes 99 unique parameters including function parameters. Automatic slope/elevation masks; only painted layer sample is RemoveFoliage. No LandscapeLayerBlend nodes.',
'- Near/far sampling, macro color/normal variation, slope, water and snow are present. No MW triplanar, texture bombing, texture-height blend or RVT system found.',
'- Seven ground color/normal pairs are 4096×4096. No ground ORM/roughness/AO/metallic/height texture sets supplied.',
'- SandA/SandC are warm brown dry-ground candidates; Stones is conditional gray gravel. Dirt is dark olive-brown; Rock dark gray. Pale-soil suitability needs native visual assessment.',
'- Master statistics: 2 sampler states, 48 pixel texture samples, 524 pixel instructions. DesertExample: 2, 32, 479. These are material statistics, not frame-time profiling or complete Landscape-component budgets.','',
'## Retained paths and routing','',
table(['Geographic role','Actual material layer'],R['retained_contract']['roles_to_actual_layers'].items()),'',
'Preserve all four role names and this routing. Do not rename actual layer entries to literal role names or MW biome names. Retain all additional bank-palette entries.','',
'Master: '+master['path'],'','Base MI: '+R['retained_contract']['base_MI'],'']
L+=['Gaza child: '+c+'\n' for c in children]
L+=['Live Shujaiya Landscape binds its child; both Gaza children parent the shared base MI. Iran profile uses the base directly; no Iran/Rimal map was opened. Current master has 1,015 expressions and ratified GeoCity_GroundStochastic_20261005 nodes. Older simple-graph assumptions are not current.','',
'Current connections: MaterialExpressionLandscapeLayerBlend_6 → BaseColor; _7 → Normal; _8 → Roughness; _0 → AmbientOcclusion. Preserve these exact existing paths as fallback, including current AO.','',
table(['Expression','Owned description','Parameter/input'],[(n['name'],n['properties']['desc'],n['properties'].get('parameter_name') or ', '.join(x or 'None' for x in n.get('input_nodes',[]))) for n in grass]),'',
'These are the exactly four owned Grass nodes. GrassCoverage master default=0; Shujaiya effective=0.15; Rimal effective=0. Preserve them. Output GeoCityGroundGrass references '+B+'LG_GeoCity_PermittedGroundGrass.LG_GeoCity_PermittedGroundGrass. Never add another Grass output or use the GeoCity_LandscapeGrass: description prefix for appearance nodes.','',
'Contract source: Content/Python/geocity_landscape_workflow.py constants 12–19, parent check 222–224, owned-node checks 321–344, child parenting 355–369 and validation 416 onward. That module was not executed.','',
'## Materials and expected layers','',
table(['Exact path','Native class','Parent','Parameter count'],[(m['path'],m['class'],m['parent'],len(m['parameters'])) for m in materials]),'',
'Only the AutoMaterial family expects RemoveFoliage. Other masters have no named LandscapeLayerBlend/LayerSample dependency. The landscape master also has LandscapeVisibilityMask, Grass outputs Rock/Stones/Grass/Dirt/Snow and physical-material outputs PM_MW_Rocks/Stones/Grass/Dirt/Snow/Water. These output labels are not painted layers. Exact GrassType and physical-material paths are in the JSON catalog.','',
'Master biome textures default to temporary 256px color/normal assets. DesertExample binds Dirt/Grass/Snow to SandA, Stones to SandC, Rock to Stones. Do not use placeholder master textures as the real palette.','',
'## All 15 material functions','',
'No function expects named MW landscape weight layers or RVT. LandscapeUVs contains LandscapeLayerCoords. Pixel-normal and vertex constraints are noted below. Callability is a graph assessment, not an integration compile test. JSON retains pin defaults and connected Preview nodes; connected Preview inputs take precedence over numeric preview_value.']
for f in functions:
    L+=['','### '+f['path'],'',f['purpose'],'','Reuse: '+f['call_as_is'],'',
        'Inputs: '+('; '.join(x['input_name']+' ('+x['input_type'].split('FUNCTION_INPUT_')[-1].split(':')[0].lower()+')' for x in f['inputs']) or 'none')+'.',
        'Outputs: '+', '.join(x['output_name'] for x in sorted(f['outputs'],key=lambda x:x.get('sort_priority',0)))+'.',
        'Dependencies: '+('; '.join(f['dependencies']) or 'none')+'.']
    if f['parameters']:L+=['',table(['Parameter','Type','Default','Group'],[(x['name'],x['type'].replace('MaterialExpression',''),x['default'],x['group']) for x in f['parameters']])]
L+=['','## Textures','',
'Settled native dimensions agree with Asset Registry Dimensions. First-load reads returned transient 32px placeholders for some textures; native_inventory_complete.json supersedes those first-pass sizes. Compression columns are editor enums, not a cooked GPU format claim.']
for s in sets:
    L+=['','### '+s['ground_type'],'',s['gaza_fit'],'',table(['Exact path','Resolution','Compression','sRGB'],[(t['path'],str(t['size_x'])+'×'+str(t['size_y']),t['compression_settings'],t['srgb']) for t in s['textures']]),'','ORM/separate PBR/height textures: none supplied for this ground type.']
L+=['','### Other textures / render targets','',table(['Exact path','Resolution','Compression','sRGB'],[(t['path'],str(t['size_x'])+'×'+str(t['size_y']),t['compression_settings'],t['srgb']) for t in tex if '/Textures/Ground/' not in t['path']]),'',
'TEX_MWAM_Variation_msk RGB modulates color (*1.5 in the master); TEX_MW_Noise_msk drives water/snow masks at different scales. Neither is wired as ORM/height. Ground roughness derives from blended color, weighted role scalars and MF_MWAM_Roughness. No packed color/normal alpha semantics for roughness/height were established.','',
'Five 256px asset thumbnails (not Lit Landscape evidence):']
for k in ['SandA','SandC','Dirt','Stones','Rock']:L+=['','!['+k+'](TEX_MWAM_'+k+'_col_preview.png)']
L+=['','## Samplers and cost','',table(['Material','Sampler states','Pixel samples','Vertex samples','Pixel instructions','Vertex instructions','Virtual samples'],[(m['path'],m['statistics']['num_samplers'],m['statistics']['num_pixel_texture_samples'],m['statistics']['num_vertex_texture_samples'],m['statistics']['num_pixel_shader_instructions'],m['statistics']['num_vertex_shader_instructions'],m['statistics']['num_virtual_texture_samples']) for m in materials if m['path'].endswith('.MTL_MWAM_AutoMaterial_MASTER') or '/Landscape/' in m['path']]),'',
'Five direct TextureSample nodes in the master are Shared:Wrap. Each of five DefaultLayer calls has four Shared:Wrap sample nodes, and Water has two. Graph sample-node count differs from compiled sample instructions due to stages, outputs and static permutations.','',
'The 16 budget concerns sampler states, not 16 texture fetches. Shared:Wrap reduces unique sampler-state pressure, not texture memory, lookups or arithmetic. Reported 2 states are below 16 for these permutations; do not treat the difference as guaranteed free slots for every Landscape component/platform/pass. Weightmaps and actual component permutations need a later authorized native check. No recompile was requested. [Epic sampler-source API]('+docs[1]['url']+').','',
'Nominal four-role DefaultLayer use = 16 sample nodes before pruning; macro color adds one and macro normal another. Do not append this blindly to the retained 61 direct TextureSample expressions. Retained master preview stats prune Landscape branches and are not the live Shujaiya component cost.','',
'## Five-defect mapping proposal','',
'Add GeoCity_MW_Enable static switch, default false. False side preserves today’s entire BaseColor/Normal/Roughness/AO routes, existing stochastic graph, all bank-layer entries and the four Grass nodes. New amounts default 0; tint white; valid nonzero scales. Base MI unchanged. Enable only the two exact Gaza children during later manager-authorized implementation. Iran remains on its inherited disabled branch.','',
'Prefer new GeoCity_MW texture-object parameters behind the switch, preserving existing profile-validated Sand_01_Normal/Sand_02_Normal bindings. Replacing those validated parameter values requires exact manager-owned profile reconciliation; an MI texture swap alone can break ordinary workflow checks.','']
for z in mapping:L+=['','### '+z['defect'],'','MW assets: '+', '.join(z['assets']),'','Wiring: '+z['wiring'],'','Limit: '+z['limit']]
L+=['','This proposal can improve color/distance/repetition and reduce visible seam contrast. It does not claim that MW alone supplies wider masks or physical ground contact. Height blending refines an existing transition with a height map. [Epic Landscape Materials]('+docs[0]['url']+').','',
'## License/readme','',license['status'],'',
'Checked installed Content/MWLandscapeAutoMaterial and C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/MWLandsc0bb389159dceV3. Installed pack has 100 asset/map files; sole non-asset VaultCache file found was manifest. No readme/license/terms/EULA/copyright-named document found. Graph comments are not license terms. Usage/redistribution entitlement remains unverified; preserve or obtain the original acquisition/license receipt. No generic Marketplace/Fab license is assumed.','',
'## Optional demo maps','']
L+=['- '+p for p in R['demo_screenshots']['maps']]
L+=['','No demo map loaded and no Lit demo screenshot captured: the existing Shujaiya world and dirty buffer were preserved. No new map or test Landscape was created.','',
'## Complete parameter tables','',
'Every exposed parameter is listed for every master/instance, including inherited function parameters. Default is the master declaration default; effective is the current value. Difference flag compares effective value to immediate parent, not override checkbox state. Native scalar/vector/texture override arrays are in JSON. Static override-checkbox metadata was not exposed. Markdown floats are rounded; JSON retains native precision.','']
for m in materials:
    L+=['','### '+m['path'],'','Class: '+m['class']+'. Parent: '+str(m['parent'])+'.','',table(['Name','Type','Group','Master default','Effective value','Differs from parent'],[(p['name'],p['type'],p.get('group','UNRESOLVED'),p.get('default'),p['effective_value'],p['differs_from_parent']) for p in sorted(m['parameters'],key=lambda p:(p.get('group',''),p['name']))])]
L+=['','## Evidence and limitations','',
'- MW_INVENTORY.json: structured inventory, proposal, exact paths, function input defaults and full side-effect record.',
'- native_inventory_complete.json: settled metadata and graph snapshot before later function dirtying; native_inventory_raw.json preserves first-pass baseline.',
'- mw_master_tool_readback.json and graphs/*.json: connection readbacks. Tool display IDs use parameter names/descriptions and can collide; native node names remain the authoritative identity.',
'- final_readonly_check.json: unchanged 107 disk files, clean map, exact new dirty-function set. Baseline hashes are in native inventory files.',
'- live_landscape_binding.json: one current Shujaiya Landscape with its area child.',
'- No integrated shader compile, frame profiling, save/reopen, regeneration, full-resolution texture review, rights approval or visual acceptance was performed.','']
(P/'MW_INVENTORY.md').write_text('\n'.join(L),encoding='utf-8')
print(json.dumps({'materials':len(materials),'parameters_including_inherited_per_instance':sum(len(m['parameters']) for m in materials),'functions':len(functions),'textures':len(tex),'new_dirty':len(incident['new_dirty_packages']),'unresolved_parameters':[(m['path'],p['name']) for m in materials for p in m['parameters'] if 'group' not in p],'md_bytes':(P/'MW_INVENTORY.md').stat().st_size,'json_bytes':(P/'MW_INVENTORY.json').stat().st_size},indent=2))

