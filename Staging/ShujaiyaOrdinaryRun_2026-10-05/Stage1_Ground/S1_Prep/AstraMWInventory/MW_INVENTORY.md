# MW material inventory — 2026-10-05

For Claude Code manager cc37d4d2-3d62-4f53-b689-28432b5527ae under Aviv’s read-only instruction. Inspected UE 5.8 PID 10460, original Shujaiya. This is an inventory and proposal, not an implemented or accepted repair.

## Inspection side effect — preserved unsaved

**No save was issued; all 107 monitored disk files are unchanged. However, 15 MW material-function packages became newly dirty in memory during inspection.** The map stayed clean; the pre-existing dirty generated Cook mesh remains. The newly dirty set matches the 15 functions queried by the advertised get_material_info read tool. Earlier Python inspection passes ended with unchanged dirty state. The precise engine-side mutation has not been established. Editor calls stopped on discovery; no save, discard, dirty-flag reset or close was attempted. This is not an entirely unchanged editor state.

Exact packages and timestamps are in MW_INVENTORY.json → inspection_side_effect and final_readonly_check.json. No lease/owner write, asset setter, Cook/Bake, Save All or map load was issued. Files authored by this task are restricted to this inventory directory.

## Findings

- 100 pack assets: 4 actual master Materials, 14 MaterialInstanceConstants, 15 functions, 32 Texture2Ds, 3 render targets, plus supporting assets. MTL_MWAM_Plant_Megascan_MASTER is actually an instance.
- Landscape master exposes 99 unique parameters including function parameters. Automatic slope/elevation masks; only painted layer sample is RemoveFoliage. No LandscapeLayerBlend nodes.
- Near/far sampling, macro color/normal variation, slope, water and snow are present. No MW triplanar, texture bombing, texture-height blend or RVT system found.
- Seven ground color/normal pairs are 4096×4096. No ground ORM/roughness/AO/metallic/height texture sets supplied.
- SandA/SandC are warm brown dry-ground candidates; Stones is conditional gray gravel. Dirt is dark olive-brown; Rock dark gray. Pale-soil suitability needs native visual assessment.
- Master statistics: 2 sampler states, 48 pixel texture samples, 524 pixel instructions. DesertExample: 2, 32, 479. These are material statistics, not frame-time profiling or complete Landscape-component budgets.

## Retained paths and routing

| Geographic role | Actual material layer |
|---|---|
| Ground | Sand_01 |
| Steep | Sand_02 |
| RoadBed | Dirt_Path |
| BuildingPad | Sand_Path |

Preserve all four role names and this routing. Do not rename actual layer entries to literal role names or MW biome names. Retain all additional bank-palette entries.

Master: /Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.M_SurfaceBank_Natural

Base MI: /Game/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural.MI_SurfaceBank_Natural

Gaza child: /Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround.MI_GeoCityGround

Gaza child: /Game/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround.MI_GeoCityGround

Live Shujaiya Landscape binds its child; both Gaza children parent the shared base MI. Iran profile uses the base directly; no Iran/Rimal map was opened. Current master has 1,015 expressions and ratified GeoCity_GroundStochastic_20261005 nodes. Older simple-graph assumptions are not current.

Current connections: MaterialExpressionLandscapeLayerBlend_6 → BaseColor; _7 → Normal; _8 → Roughness; _0 → AmbientOcclusion. Preserve these exact existing paths as fallback, including current AO.

| Expression | Owned description | Parameter/input |
|---|---|---|
| MaterialExpressionLandscapeLayerSample_1 | GeoCity_LandscapeGrass:Ground | Sand_01 |
| MaterialExpressionScalarParameter_1 | GeoCity_LandscapeGrass:Density | GeoCity_GrassCoverage |
| MaterialExpressionMultiply_3 | GeoCity_LandscapeGrass:GroundDensity | MaterialExpressionLandscapeLayerSample_1, MaterialExpressionScalarParameter_1 |
| MaterialExpressionLandscapeGrassOutput_0 | GeoCity_LandscapeGrass:Output | MaterialExpressionMultiply_3 |

These are the exactly four owned Grass nodes. GrassCoverage master default=0; Shujaiya effective=0.15; Rimal effective=0. Preserve them. Output GeoCityGroundGrass references /Game/Project/Shared/SurfacePainting/Appearance_20261003/LG_GeoCity_PermittedGroundGrass.LG_GeoCity_PermittedGroundGrass. Never add another Grass output or use the GeoCity_LandscapeGrass: description prefix for appearance nodes.

Contract source: Content/Python/geocity_landscape_workflow.py constants 12–19, parent check 222–224, owned-node checks 321–344, child parenting 355–369 and validation 416 onward. That module was not executed.

## Materials and expected layers

| Exact path | Native class | Parent | Parameter count |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER | Material | None | 25 |
| /Game/MWLandscapeAutoMaterial/Materials/Plants/MTL_MWAM_PlantsGrass.MTL_MWAM_PlantsGrass | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER | 25 |
| /Game/MWLandscapeAutoMaterial/Materials/Cover/MTL_MWAM_CoverSnow.MTL_MWAM_CoverSnow | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER | 25 |
| /Game/MWLandscapeAutoMaterial/Materials/Cover/MTL_MWAM_CoverRocks.MTL_MWAM_CoverRocks | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER | 25 |
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER | Material | None | 99 |
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MW_VolumeClouds_MASTER.MTL_MW_VolumeClouds_MASTER | Material | None | 25 |
| /Game/MWLandscapeAutoMaterial/Materials/FX/MTL_MWAM_VolumeCloudsA.MTL_MWAM_VolumeCloudsA | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MW_VolumeClouds_MASTER.MTL_MW_VolumeClouds_MASTER | 25 |
| /Game/MWLandscapeAutoMaterial/Materials/FX/MTL_MWAM_VolumeCloudsB.MTL_MWAM_VolumeCloudsB | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MW_VolumeClouds_MASTER.MTL_MW_VolumeClouds_MASTER | 25 |
| /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.MTL_MWAM_Landscape_DesertExample | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER | 99 |
| /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_IslandExample.MTL_MWAM_Landscape_IslandExample | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER | 99 |
| /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_MountainRangeExample.MTL_MWAM_Landscape_MountainRangeExample | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER | 99 |
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER | Material | None | 6 |
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_Black.MTL_MW_Basic_Black | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER | 6 |
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_Chrome.MTL_MW_Basic_Chrome | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER | 6 |
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_ColorChecker.MTL_MW_Basic_ColorChecker | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER | 6 |
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_Gray.MTL_MW_Basic_Gray | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER | 6 |
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_White.MTL_MW_Basic_White | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER | 6 |
| /Game/MWLandscapeAutoMaterial/Materials/Plants/MTL_MWAM_Plant_Megascan_MASTER.MTL_MWAM_Plant_Megascan_MASTER | MaterialInstanceConstant | /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER | 25 |

Only the AutoMaterial family expects RemoveFoliage. Other masters have no named LandscapeLayerBlend/LayerSample dependency. The landscape master also has LandscapeVisibilityMask, Grass outputs Rock/Stones/Grass/Dirt/Snow and physical-material outputs PM_MW_Rocks/Stones/Grass/Dirt/Snow/Water. These output labels are not painted layers. Exact GrassType and physical-material paths are in the JSON catalog.

Master biome textures default to temporary 256px color/normal assets. DesertExample binds Dirt/Grass/Snow to SandA, Stones to SandC, Rock to Stones. Do not use placeholder master textures as the real palette.

## All 15 material functions

No function expects named MW landscape weight layers or RVT. LandscapeUVs contains LandscapeLayerCoords. Pixel-normal and vertex constraints are noted below. Callability is a graph assessment, not an integration compile test. JSON retains pin defaults and connected Preview nodes; connected Preview inputs take precedence over numeric preview_value.

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_CombineNormal.MF_MWAM_CombineNormal

Lerps each normal from flat (0,0,1) with intensity, adds XY and multiplies Z. Normalize node exists but is not on the output connection.

Reuse: Yes with explicit intensities and compatible tangent-space normals. Normalize in the new enabled branch as appropriate.

Inputs: BaseNormal (vector3); AddNormal (vector3); BaseNormalIntensity (scalar); AddNormalIntensity (scalar).
Outputs: Normal.
Dependencies: /Engine/Functions/Engine_MaterialFunctions02/SplitComponents.SplitComponents.

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_CombineNormalSimple.MF_MWAM_CombineNormalSimple

Adds normal XY and multiplies Z. No texture fetches.

Reuse: Yes for compatible tangent-space normals. Combine is not a distance fade.

Inputs: NormalA (vector3); NormalB (vector3).
Outputs: Result.
Dependencies: /Engine/Functions/Engine_MaterialFunctions02/SplitComponents.SplitComponents.

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_DepthFade.MF_MWAM_DepthFade

Engine CameraDepthFade, For Vertex Shader=true. Parameters MW_DistanceBlendFadeLength=4096 and MW_DistanceBlendFadeOffset=512. This is camera distance, not scene intersection DepthFade.

Reuse: Yes; shared MW parameter names will appear on the caller. Wrap/remap for independent per-role control.

Inputs: none.
Outputs: DepthFadeMask.
Dependencies: /Engine/Functions/Engine_MaterialFunctions01/Opacity/CameraDepthFade.CameraDepthFade.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_DistanceBlendFadeLength | ScalarParameter | 4096 | UVs |
| MW_DistanceBlendFadeOffset | ScalarParameter | 512 | UVs |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_LandscapeUVs.MF_MWAM_LandscapeUVs

Selects LandscapeLayerCoords or world XY, with MW_LandscapeWorldUVSize=384; MW_UseWorldPositionUVs=true. Also returns raw world XY. Planar, not triplanar.

Reuse: Yes on our Landscape. Contains LandscapeLayerCoords but no painted-layer names. Prefer feeding retained world XY UVs directly to DefaultLayer to retain existing scale control.

Inputs: none.
Outputs: LandscapeCoords, LandscapeUvs, WorldCoords, WorldCoordsRAW.
Dependencies: none.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_LandscapeWorldUVSize | ScalarParameter | 384 | UVs |
| MW_UseWorldPositionUVs | StaticSwitchParameter | true | UVs |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_LayerBlend.MF_MWAM_LayerBlend

Sequential Rock/Stones/Grass/Dirt color and normal blends with optional Snow normals, supplied masks and distance alpha. Uses MW_UseSnow. Not LandscapeLayerBlend and not texture-height blending.

Reuse: Technically callable, but not a direct replacement for our named-weight blends. Its slots/order encode MW biomes; prefer reusable per-role sampling functions.

Inputs: DepthFade (scalar); StonesNormalMask (scalar); GrassNormalMask (scalar); DirtNormalMask (scalar); SnowVertexMask (scalar); RockFarNormal (vector3); RockNearNormal (vector3); StonesFarNormal (vector3); StonesNearNormal (vector3); RockBaseColor (vector3); StonesBaseColor (vector3); GrassBaseColor (vector3); DirtBaseColor (vector3); StonesMask (scalar); GrassMask (scalar); DirtMask (scalar); --------------------------------- (static_bool); GrassFarNormal (vector3); GrassNearNormal (vector3); DirtFarNormal (vector3); DirtNearNormal (vector3); SnowFarNormal (vector3); SnowNearNormal (vector3).
Outputs: BaseColor, NormalNear, NormalFar.
Dependencies: none.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_UseSnow | StaticSwitchParameter | true | 0_Snow |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_Roughness.MF_MWAM_Roughness

pow((MW_UseInvertedRoughness ? 1-input : input) * MW_RoughnessMultiplier, MW_RoughnessPower), defaults true/1/0.5. No texture unpacking. The master supplies color-derived modulation times weighted per-role scalars.

Reuse: Yes, but default behavior is not identity. Gate and clamp separately. Do not describe color-derived roughness as a measured roughness map.

Inputs: Roughness (scalar).
Outputs: Roughness.
Dependencies: none.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_UseInvertedRoughness | StaticSwitchParameter | true | Lighting |
| MW_RoughnessMultiplier | ScalarParameter | 1 | Lighting |
| MW_RoughnessPower | ScalarParameter | 0.5 | Lighting |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_Snow.MF_MWAM_Snow

Blends BaseColor toward SnowBaseColor with SnowPixelMask, gated by MW_UseSnow.

Reuse: Callable; omit for dry Gaza.

Inputs: BaseColor (vector3); SnowBaseColor (vector3); SnowPixelMask (scalar).
Outputs: BaseColor.
Dependencies: none.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_UseSnow | StaticSwitchParameter | true | 0_Snow |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_DefaultLayer.MF_MWAM_DefaultLayer

Samples color and normal at near/far UVs. Color alpha = DepthFadeMask * 0.75. Static options apply color correction, normal XY intensity and UV multipliers. Four Shared:Wrap sample nodes. No bombing, stochastic rotation, triplanar or height blend.

Reuse: Yes with explicit inputs. Set WaterRefractionUV=(0,0), white ColorCorrection, NormalIntensity=1 and deliberate static booleans. ColorCorrection preview is black. NormalNear/NormalFar are separate outputs, not a final distance-normal blend.

Inputs: TextureBaseColor (texture2d); TextureNormal (texture2d); DepthFadeMask (scalar); UVNear (vector2); UVFar (vector2); ColorCorrection (vector3); UVFarMultiplier (scalar); UVNearMultiplier (scalar); WaterRefractionUV (vector2); NormalIntensity (scalar); AdvInstructions (static_bool); AdvInstructionsUVs (static_bool).
Outputs: BaseColor, NormalNear, NormalFar.
Dependencies: none.

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_SlopeMask.MF_MWAM_SlopeMask

Engine SlopeMask calls combine pixel-normal and base-slope responses with world-elevation gating; separate color/normal mask outputs.

Reuse: Conditional: do not connect the PixelNormalWS-dependent SlopeMask output back into Normal. SlopeNormalMask is the separate route. Do not replace geographic paint weights with its absolute elevation thresholds.

Inputs: SlopePower (scalar); MaxWorldPosition (scalar); MaxWorldPositionPower (scalar).
Outputs: SlopeMask, SlopeNormalMask.
Dependencies: /Engine/Functions/Engine_MaterialFunctions01/Texturing/SlopeMask.SlopeMask.

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_SnowMask.MF_MWAM_SnowMask

World elevation, input noise and slope, with pixel/vertex normals, produce separate snow masks.

Reuse: Callable but unnecessary for Gaza dry ground. Pixel-normal result must not drive a normal feedback loop.

Inputs: Mask (scalar).
Outputs: SnowVertexMask, SnowPixelMask.
Dependencies: /Engine/Functions/Engine_MaterialFunctions01/Texturing/SlopeMask.SlopeMask.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_SnowWorldPositionPower | ScalarParameter | 9.9999997e-05 | 0_Snow |
| MW_SnowMaskMultiplier | ScalarParameter | 1.4 | 0_Snow |
| MW_SnowMaskPower | ScalarParameter | 10 | 0_Snow |
| MW_SnowWorldPosition | ScalarParameter | -1500 | 0_Snow |
| MW_SnowSlopePower | ScalarParameter | 3 | 0_Snow |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_WaterMask.MF_MWAM_WaterMask

Slope/elevation/noise mask, snow exclusion and MW_UseWater switch.

Reuse: Callable; omit for dry Gaza. Not an object-contact detector.

Inputs: Mask (scalar); SnowVertexMask (scalar).
Outputs: WaterMask.
Dependencies: /Engine/Functions/Engine_MaterialFunctions01/Texturing/SlopeMask.SlopeMask.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_WaterSlopePower | ScalarParameter | 1536 | 1_Water |
| MW_WaterEdgeContrast | ScalarParameter | 4 | 1_Water |
| MW_WaterWorldPositionPower | ScalarParameter | 9.9999997e-05 | 1_Water |
| MW_WaterMaxWorldPosition | ScalarParameter | 0 | 1_Water |
| MW_UseWater | StaticSwitchParameter | true | 1_Water |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MW_MWAM_Water.MW_MWAM_Water

Two panned water-normal samples, normal combine, mask-driven color/specular/roughness/metallic and WaterRefractionUV; MW_UseWater switch.

Reuse: Callable with inputs; omit for dry ground. Wetness/puddles are not RVT or road/building contact.

Inputs: BaseColor (vector3); WaterMask (scalar); Specular (scalar); Roughness (scalar); Normal (vector3); WorldCoords (vector2).
Outputs: BaseColor, Metallic, Specular, Roughness, Normal, WaterRefractionUV.
Dependencies: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_CombineNormalSimple.MF_MWAM_CombineNormalSimple.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_UseWater | StaticSwitchParameter | true | 1_Water |
| MW_WaterUVSize | ScalarParameter | 12 | 1_Water |
| MW_WaterNormalIntensity | VectorParameter | r=0.050000001, g=0.050000001, b=1, a=1 | 1_Water |
| MW_WaterColor | VectorParameter | r=0.039999999, g=0.047499999, b=0.050000001, a=1 | 1_Water |
| MW_WaterRefractionIntensity | ScalarParameter | 0.30000001 | 1_Water |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_PivotMask.MF_MWAM_PivotMask

World position relative to engine ObjectPivotPoint makes an object-height mask for cover/foliage.

Reuse: Technically callable, but Landscape pivot does not identify building footprints. Not a contact solution.

Inputs: none.
Outputs: PivotMask.
Dependencies: /Engine/Functions/Engine_MaterialFunctions02/WorldPositionOffset/ObjectPivotPoint.ObjectPivotPoint.

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_SubSurface.MF_MWAM_SubSurface

Optional subsurface texture/base-color path with color and intensity controls for foliage.

Reuse: Callable but not useful for opaque DefaultLit ground without a shading change outside this proposal.

Inputs: BaseColor (vector3).
Outputs: SubSurfaceColor.
Dependencies: none.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_SubSurfaceColor | VectorParameter | r=1, g=1, b=1, a=0 | Lighting |
| MW_UseSubSurfaceColor | StaticSwitchParameter | false | Lighting |
| MW_UseSeparateSubSurfaceTexture | StaticSwitchParameter | false | Textures |
| MW_TextureSubSurfaceColor | TextureSampleParameter2D | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | Textures |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_Opacity.MF_MWAM_Opacity

Foliage opacity, camera-distance fade and DitherTemporalAA controls.

Reuse: Not appropriate for the retained opaque ground contact problem; do not import its opacity/dither behavior.

Inputs: Opacity (scalar).
Outputs: Opacity.
Dependencies: /Engine/Functions/Engine_MaterialFunctions01/Opacity/CameraDepthFade.CameraDepthFade; /Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA.

| Parameter | Type | Default | Group |
|---|---|---|---|
| MW_CameraFadeRange | ScalarParameter | 5000 | DistanceCulling |
| MW_UseDepthFade | StaticSwitchParameter | false | DistanceCulling |
| MW_CameraFadeOffset | ScalarParameter | 0 | DistanceCulling |
| MW_UseSolidOpacity | StaticSwitchParameter | false | DistanceCulling |

## Textures

Settled native dimensions agree with Asset Registry Dimensions. First-load reads returned transient 32px placeholders for some textures; native_inventory_complete.json supersedes those first-pass sizes. Compression columns are editor enums, not a cooked GPU format claim.

### SandA

Recommended dry-sand candidate. Fine warm brown thumbnail; not inherently pale Gaza soil.

| Exact path | Resolution | Compression | sRGB |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_col.TEX_MWAM_SandA_col | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_nrm.TEX_MWAM_SandA_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |

ORM/separate PBR/height textures: none supplied for this ground type.

### SandC

Recommended compact dry-soil/sand variation candidate. Brown with coarser clumps than SandA.

| Exact path | Resolution | Compression | sRGB |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandC_col.TEX_MWAM_SandC_col | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandC_nrm.TEX_MWAM_SandC_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |

ORM/separate PBR/height textures: none supplied for this ground type.

### Stones

Conditional gray gravel/stone candidate; value/scale-match. DesertExample uses this in its Rock slot.

| Exact path | Resolution | Compression | sRGB |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Stones_col.TEX_MWAM_Stones_col | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Stones_nrm.TEX_MWAM_Stones_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |

ORM/separate PBR/height textures: none supplied for this ground type.

### Dirt

Conditional, not first pale-soil choice. Thumbnail is dark olive-brown/organic.

| Exact path | Resolution | Compression | sRGB |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Dirt_col.TEX_MWAM_Dirt_col | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Dirt_nrm.TEX_MWAM_Dirt_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |

ORM/separate PBR/height textures: none supplied for this ground type.

### Rock

Conditional dark rock. Thumbnail is dark gray; pale limestone suitability is unverified.

| Exact path | Resolution | Compression | sRGB |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Rock_col.TEX_MWAM_Rock_col | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Rock_nrm.TEX_MWAM_Rock_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |

ORM/separate PBR/height textures: none supplied for this ground type.

### Grass

Exclude from dry soil palette; grass role.

| Exact path | Resolution | Compression | sRGB |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Grass_col.TEX_MWAM_Grass_col | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Grass_nrm.TEX_MWAM_Grass_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |

ORM/separate PBR/height textures: none supplied for this ground type.

### Snow

Exclude from dry Gaza.

| Exact path | Resolution | Compression | sRGB |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Snow_col.TEX_MWAM_Snow_col | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Snow_nrm.TEX_MWAM_Snow_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |

ORM/separate PBR/height textures: none supplied for this ground type.

### Other textures / render targets

| Exact path | Resolution | Compression | sRGB |
|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | 4096×4096 | <TextureCompressionSettings.TC_MASKS: 2> | false |
| /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |
| /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_Noise_msk.TEX_MW_Noise_msk | 2048×2048 | <TextureCompressionSettings.TC_MASKS: 2> | false |
| /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | 256×256 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | 256×256 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |
| /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_WaterA_nrm.TEX_MW_WaterA_nrm | 1024×1024 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |
| /Game/MWLandscapeAutoMaterial/Textures/Plants/TEX_MWAM_Grass_col.TEX_MWAM_Grass_col | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Plants/TEX_MWAM_Grass_nrm.TEX_MWAM_Grass_nrm | 4096×4096 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |
| /Game/MWLandscapeAutoMaterial/Textures/Cover/TEX_MWAM_CoverRocks_col.TEX_MWAM_CoverRocks_col | 2048×2048 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Cover/TEX_MWAM_CoverRocks_nrm.TEX_MWAM_CoverRocks_nrm | 2048×2048 | <TextureCompressionSettings.TC_NORMALMAP: 1> | false |
| /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | 256×256 | <TextureCompressionSettings.TC_BC7: 11> | false |
| /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudGradientA.TEX_MW_CloudGradientA | 32×16 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudWeatherA.TEX_MW_CloudWeatherA | 512×512 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudGradientB.TEX_MW_CloudGradientB | 32×16 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | 1024×1024 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Bake/TRT_LandscapeLayerBake1k.TRT_LandscapeLayerBake1k | 1024×1024 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Bake/TRT_LandscapeLayerBake2k.TRT_LandscapeLayerBake2k | 2048×2048 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/Bake/TRT_LandscapeLayerBake4k.TRT_LandscapeLayerBake4k | 4096×4096 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudGradientC.TEX_MW_CloudGradientC | 32×16 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudWeatherB.TEX_MW_CloudWeatherB | 512×512 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |
| /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudWeatherC.TEX_MW_CloudWeatherC | 512×512 | <TextureCompressionSettings.TC_DEFAULT: 0> | true |

TEX_MWAM_Variation_msk RGB modulates color (*1.5 in the master); TEX_MW_Noise_msk drives water/snow masks at different scales. Neither is wired as ORM/height. Ground roughness derives from blended color, weighted role scalars and MF_MWAM_Roughness. No packed color/normal alpha semantics for roughness/height were established.

Five 256px asset thumbnails (not Lit Landscape evidence):

![SandA](TEX_MWAM_SandA_col_preview.png)

![SandC](TEX_MWAM_SandC_col_preview.png)

![Dirt](TEX_MWAM_Dirt_col_preview.png)

![Stones](TEX_MWAM_Stones_col_preview.png)

![Rock](TEX_MWAM_Rock_col_preview.png)

## Samplers and cost

| Material | Sampler states | Pixel samples | Vertex samples | Pixel instructions | Vertex instructions | Virtual samples |
|---|---|---|---|---|---|---|
| /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER | 2 | 48 | 3 | 524 | 153 | 0 |
| /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.MTL_MWAM_Landscape_DesertExample | 2 | 32 | 3 | 479 | 153 | 0 |
| /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_IslandExample.MTL_MWAM_Landscape_IslandExample | 2 | 46 | 3 | 557 | 153 | 0 |
| /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_MountainRangeExample.MTL_MWAM_Landscape_MountainRangeExample | 2 | 48 | 3 | 548 | 153 | 0 |

Five direct TextureSample nodes in the master are Shared:Wrap. Each of five DefaultLayer calls has four Shared:Wrap sample nodes, and Water has two. Graph sample-node count differs from compiled sample instructions due to stages, outputs and static permutations.

The 16 budget concerns sampler states, not 16 texture fetches. Shared:Wrap reduces unique sampler-state pressure, not texture memory, lookups or arithmetic. Reported 2 states are below 16 for these permutations; do not treat the difference as guaranteed free slots for every Landscape component/platform/pass. Weightmaps and actual component permutations need a later authorized native check. No recompile was requested. [Epic sampler-source API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialExpressionTextureSample?application_version=5.6).

Nominal four-role DefaultLayer use = 16 sample nodes before pruning; macro color adds one and macro normal another. Do not append this blindly to the retained 61 direct TextureSample expressions. Retained master preview stats prune Landscape branches and are not the live Shujaiya component cost.

## Five-defect mapping proposal

Add GeoCity_MW_Enable static switch, default false. False side preserves today’s entire BaseColor/Normal/Roughness/AO routes, existing stochastic graph, all bank-layer entries and the four Grass nodes. New amounts default 0; tint white; valid nonzero scales. Base MI unchanged. Enable only the two exact Gaza children during later manager-authorized implementation. Iran remains on its inherited disabled branch.

Prefer new GeoCity_MW texture-object parameters behind the switch, preserving existing profile-validated Sand_01_Normal/Sand_02_Normal bindings. Replacing those validated parameter values requires exact manager-owned profile reconciliation; an MI texture swap alone can break ordinary workflow checks.


### No color variety

MW assets: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_DefaultLayer.MF_MWAM_DefaultLayer, /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_col.TEX_MWAM_SandA_col, /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandC_col.TEX_MWAM_SandC_col, /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Stones_col.TEX_MWAM_Stones_col, /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk

Wiring: Keep the existing named-layer blends and wider bank palette. Add new GeoCity_MW texture-object parameters inside a default-off switch: SandA for Ground, SandC for soil partner/BuildingPad, conditional Stones for stony RoadBed/Steep. After LandscapeLayerBlend_6, apply coherent world-XY macro color with default amount 0.

Limit: MW macro color is inline mask RGB * blended color * 1.5, not a named macro function. A proposed MF_GeoCity_MW_MacroColor would be new project logic. Use white-to-variation interpolation so amount 0 is identity.

### Pale/uniform at distance

MW assets: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_DepthFade.MF_MWAM_DepthFade, /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_DefaultLayer.MF_MWAM_DefaultLayer, /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk

Wiring: Use retained world XY near/far UVs and camera-distance fade in DefaultLayer. Add a project far-color target with amount 0 by default. Separately gate a normal fade toward (0,0,1) after LandscapeLayerBlend_7.

Limit: MW blends the same texture at two scales with alpha=0.75*DepthFadeMask; this does not change its far mip mean reliably. A controlled far color is added project logic, not a discovered MW feature. Lighting/exposure was not diagnosed.

### Visible repetition

MW assets: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_DefaultLayer.MF_MWAM_DefaultLayer, /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_CombineNormal.MF_MWAM_CombineNormal, /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk, /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm

Wiring: Use distance sampling and coherent macro variation across the four roles. Preserve ratified GeoCity_GroundStochastic_20261005 and review its active routes before replacing sampling inputs. Avoid stacking a second expensive sampler system.

Limit: No MW UV bombing, stochastic rotation or triplanar function found. Stronger anti-tiling requires retained/custom logic; UV rotation must rotate normal XY consistently.

### Sharp joins

MW assets: /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk, /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_Noise_msk.TEX_MW_Noise_msk, /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_LayerBlend.MF_MWAM_LayerBlend

Wiring: Share macro variation across seams. Keep geographic weights/names and Grass input untouched. Future appearance-only noise modulation may refine existing fractional transition weights, with renormalization.

Limit: MF_MWAM_LayerBlend is not height blending. No MW height map found. A pointwise remap cannot widen a binary mask into a spatial feather. Wider masks remain manager-owned producer work.

### No contact with buildings/roads

MW assets: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_DepthFade.MF_MWAM_DepthFade, /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_PivotMask.MF_MWAM_PivotMask, /Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MW_MWAM_Water.MW_MWAM_Water

Wiring: Do not use these functions as contact detectors. Later provide a real road/pad edge-distance/contact mask, then separately gate a subtle darkening/roughness band without altering Grass exclusions.

Limit: CameraDepthFade is camera distance, PivotMask is object pivot and Water is wetness. Pack has no RVT/contact system or geometry grounding repair. These cannot close physical gaps; contact geometry/decal/RVT work is not delivered.

This proposal can improve color/distance/repetition and reduce visible seam contrast. It does not claim that MW alone supplies wider masks or physical ground contact. Height blending refines an existing transition with a height map. [Epic Landscape Materials](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine).

## License/readme

No license/readme/terms/EULA file found. Usage and redistribution terms not established.

Checked installed Content/MWLandscapeAutoMaterial and C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/MWLandsc0bb389159dceV3. Installed pack has 100 asset/map files; sole non-asset VaultCache file found was manifest. No readme/license/terms/EULA/copyright-named document found. Graph comments are not license terms. Usage/redistribution entitlement remains unverified; preserve or obtain the original acquisition/license receipt. No generic Marketplace/Fab license is assumed.

## Optional demo maps

- /Game/MWLandscapeAutoMaterial/Maps/LandscapeAutoMaterial_Desert_Example.LandscapeAutoMaterial_Desert_Example
- /Game/MWLandscapeAutoMaterial/Maps/LandscapeAutoMaterial_Island_Example.LandscapeAutoMaterial_Island_Example
- /Game/MWLandscapeAutoMaterial/Maps/LandscapeAutoMaterial_MountainRange_Example.LandscapeAutoMaterial_MountainRange_Example

No demo map loaded and no Lit demo screenshot captured: the existing Shujaiya world and dirty buffer were preserved. No new map or test Landscape was created.

## Complete parameter tables

Every exposed parameter is listed for every master/instance, including inherited function parameters. Default is the master declaration default; effective is the current value. Difference flag compares effective value to immediate parent, not override checkbox state. Native scalar/vector/texture override arrays are in JSON. Static override-checkbox metadata was not exposed. Markdown floats are rounded; JSON retains native precision.


### /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER

Class: Material. Parent: None.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_BaseColorContrast | scalar | ColorCorrection | 1 | 1 | false |
| MW_BaseColorCorrection | vector | ColorCorrection | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_ColorVariationContrast | scalar | ColorCorrection | 0.25 | 0.25 | false |
| MW_[x]_UseRandomizeBaseIntensity | static_switch | ColorCorrection | true | true | false |
| MW_CameraFadeOffset | scalar | DistanceCulling | 0 | 0 | false |
| MW_CameraFadeRange | scalar | DistanceCulling | 5000 | 5000 | false |
| MW_UseDepthFade | static_switch | DistanceCulling | false | false | false |
| MW_UseSolidOpacity | static_switch | DistanceCulling | false | false | false |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1 | false |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 0.5 | false |
| MW_SubSurfaceColor | vector | Lighting | r=1, g=1, b=1, a=0 | r=1, g=1, b=1, a=0 | false |
| MW_UseInvertedRoughness | static_switch | Lighting | true | true | false |
| MW_UseSubSurfaceColor | static_switch | Lighting | false | false | false |
| MW_Specular | scalar | None | 0.5 | 0.5 | false |
| MW_NormalIntensity | scalar | Normal | 1 | 1 | false |
| MW_[x]_UseWorldNormal | static_switch | Normal | false | false | false |
| MW_TextureBaseColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_TextureNormal | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | false |
| MW_TextureOpacity | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | false |
| MW_TextureSubSurfaceColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_UseSeparateSubSurfaceTexture | static_switch | Textures | false | false | false |
| MW_[x]_UseSeparateOpacityTexture | static_switch | Textures | false | false | false |
| MW_WindIntensity | scalar | Wind | 0.2 | 0.2 | false |
| MW_WindSpeed | scalar | Wind | 0.5 | 0.5 | false |
| MW_[x]_UseWind | static_switch | Wind | false | false | false |

### /Game/MWLandscapeAutoMaterial/Materials/Plants/MTL_MWAM_PlantsGrass.MTL_MWAM_PlantsGrass

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_BaseColorContrast | scalar | ColorCorrection | 1 | 0.5 | true |
| MW_BaseColorCorrection | vector | ColorCorrection | r=1, g=1, b=1, a=1 | r=0.11, g=0.15000001, b=0.029999999, a=1 | true |
| MW_ColorVariationContrast | scalar | ColorCorrection | 0.25 | 0.5 | true |
| MW_[x]_UseRandomizeBaseIntensity | static_switch | ColorCorrection | true | true | false |
| MW_CameraFadeOffset | scalar | DistanceCulling | 0 | 500 | true |
| MW_CameraFadeRange | scalar | DistanceCulling | 5000 | 9500 | true |
| MW_UseDepthFade | static_switch | DistanceCulling | false | true | true |
| MW_UseSolidOpacity | static_switch | DistanceCulling | false | false | false |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1 | false |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 4 | true |
| MW_SubSurfaceColor | vector | Lighting | r=1, g=1, b=1, a=0 | r=1, g=1, b=1, a=1 | true |
| MW_UseInvertedRoughness | static_switch | Lighting | true | true | false |
| MW_UseSubSurfaceColor | static_switch | Lighting | false | true | true |
| MW_Specular | scalar | None | 0.5 | 0.5 | false |
| MW_NormalIntensity | scalar | Normal | 1 | 10 | true |
| MW_[x]_UseWorldNormal | static_switch | Normal | false | false | false |
| MW_TextureBaseColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Plants/TEX_MWAM_Grass_col.TEX_MWAM_Grass_col | true |
| MW_TextureNormal | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Plants/TEX_MWAM_Grass_nrm.TEX_MWAM_Grass_nrm | true |
| MW_TextureOpacity | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | false |
| MW_TextureSubSurfaceColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_UseSeparateSubSurfaceTexture | static_switch | Textures | false | false | false |
| MW_[x]_UseSeparateOpacityTexture | static_switch | Textures | false | false | false |
| MW_WindIntensity | scalar | Wind | 0.2 | 0.2 | false |
| MW_WindSpeed | scalar | Wind | 0.5 | 0.5 | false |
| MW_[x]_UseWind | static_switch | Wind | false | true | true |

### /Game/MWLandscapeAutoMaterial/Materials/Cover/MTL_MWAM_CoverSnow.MTL_MWAM_CoverSnow

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_BaseColorContrast | scalar | ColorCorrection | 1 | 0.1 | true |
| MW_BaseColorCorrection | vector | ColorCorrection | r=1, g=1, b=1, a=1 | r=0.81, g=0.81, b=0.89999998, a=1 | true |
| MW_ColorVariationContrast | scalar | ColorCorrection | 0.25 | 0.25 | false |
| MW_[x]_UseRandomizeBaseIntensity | static_switch | ColorCorrection | true | false | true |
| MW_CameraFadeOffset | scalar | DistanceCulling | 0 | 1000 | true |
| MW_CameraFadeRange | scalar | DistanceCulling | 5000 | 9000 | true |
| MW_UseDepthFade | static_switch | DistanceCulling | false | true | true |
| MW_UseSolidOpacity | static_switch | DistanceCulling | false | true | true |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1 | false |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 0.1 | true |
| MW_SubSurfaceColor | vector | Lighting | r=1, g=1, b=1, a=0 | r=0.5, g=0.5, b=0.5, a=1 | true |
| MW_UseInvertedRoughness | static_switch | Lighting | true | false | true |
| MW_UseSubSurfaceColor | static_switch | Lighting | false | true | true |
| MW_Specular | scalar | None | 0.5 | 0.5 | false |
| MW_NormalIntensity | scalar | Normal | 1 | 0.5 | true |
| MW_[x]_UseWorldNormal | static_switch | Normal | false | false | false |
| MW_TextureBaseColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Cover/TEX_MWAM_CoverRocks_col.TEX_MWAM_CoverRocks_col | true |
| MW_TextureNormal | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Cover/TEX_MWAM_CoverRocks_nrm.TEX_MWAM_CoverRocks_nrm | true |
| MW_TextureOpacity | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | false |
| MW_TextureSubSurfaceColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_UseSeparateSubSurfaceTexture | static_switch | Textures | false | false | false |
| MW_[x]_UseSeparateOpacityTexture | static_switch | Textures | false | false | false |
| MW_WindIntensity | scalar | Wind | 0.2 | 0.2 | false |
| MW_WindSpeed | scalar | Wind | 0.5 | 0.5 | false |
| MW_[x]_UseWind | static_switch | Wind | false | false | false |

### /Game/MWLandscapeAutoMaterial/Materials/Cover/MTL_MWAM_CoverRocks.MTL_MWAM_CoverRocks

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_BaseColorContrast | scalar | ColorCorrection | 1 | 1 | false |
| MW_BaseColorCorrection | vector | ColorCorrection | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_ColorVariationContrast | scalar | ColorCorrection | 0.25 | 0.1 | true |
| MW_[x]_UseRandomizeBaseIntensity | static_switch | ColorCorrection | true | true | false |
| MW_CameraFadeOffset | scalar | DistanceCulling | 0 | 1000 | true |
| MW_CameraFadeRange | scalar | DistanceCulling | 5000 | 3000 | true |
| MW_UseDepthFade | static_switch | DistanceCulling | false | true | true |
| MW_UseSolidOpacity | static_switch | DistanceCulling | false | true | true |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1 | false |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 2 | true |
| MW_SubSurfaceColor | vector | Lighting | r=1, g=1, b=1, a=0 | r=1, g=1, b=1, a=0 | false |
| MW_UseInvertedRoughness | static_switch | Lighting | true | true | false |
| MW_UseSubSurfaceColor | static_switch | Lighting | false | false | false |
| MW_Specular | scalar | None | 0.5 | 0.5 | false |
| MW_NormalIntensity | scalar | Normal | 1 | 1.5 | true |
| MW_[x]_UseWorldNormal | static_switch | Normal | false | false | false |
| MW_TextureBaseColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Cover/TEX_MWAM_CoverRocks_col.TEX_MWAM_CoverRocks_col | true |
| MW_TextureNormal | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Cover/TEX_MWAM_CoverRocks_nrm.TEX_MWAM_CoverRocks_nrm | true |
| MW_TextureOpacity | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | false |
| MW_TextureSubSurfaceColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_UseSeparateSubSurfaceTexture | static_switch | Textures | false | false | false |
| MW_[x]_UseSeparateOpacityTexture | static_switch | Textures | false | false | false |
| MW_WindIntensity | scalar | Wind | 0.2 | 0.2 | false |
| MW_WindSpeed | scalar | Wind | 0.5 | 0.5 | false |
| MW_[x]_UseWind | static_switch | Wind | false | false | false |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER

Class: Material. Parent: None.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_DebugBake | static_switch | #Debug | false | false | false |
| MW_DebugMaskSnowWater | static_switch | #Debug | true | true | false |
| MW_DebugSnowWater | static_switch | #Debug | false | false | false |
| MW_NormalIntensity | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowColorCorrection | vector | 0_Snow | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_SnowEdgeMaskUVSize | scalar | 0_Snow | 256 | 256 | false |
| MW_SnowMaskMultiplier | scalar | 0_Snow | 1.4 | 1.4 | false |
| MW_SnowMaskPower | scalar | 0_Snow | 10 | 10 | false |
| MW_SnowNormalIntensity | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowProceduralMaskSize | scalar | 0_Snow | 32 | 32 | false |
| MW_SnowSlopePower | scalar | 0_Snow | 3 | 3 | false |
| MW_SnowUVNearMultiplier | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowWorldPosition | scalar | 0_Snow | -1500 | -1500 | false |
| MW_SnowWorldPositionPower | scalar | 0_Snow | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_TextureSnowBaseColor | texture | 0_Snow | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_TextureSnowNormal | texture | 0_Snow | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | false |
| MW_UseSnow | static_switch | 0_Snow | true | true | false |
| MW_[x]_UseSnowAdvanced | static_switch | 0_Snow | false | false | false |
| MW_[x]_UseSnowAdvancedUVs | static_switch | 0_Snow | false | false | false |
| MW_[x]_UseSnowProcedurals | static_switch | 0_Snow | true | true | false |
| MW_UseWater | static_switch | 1_Water | true | true | false |
| MW_WaterColor | vector | 1_Water | r=0.039999999, g=0.047499999, b=0.050000001, a=1 | r=0.039999999, g=0.047499999, b=0.050000001, a=1 | false |
| MW_WaterEdgeContrast | scalar | 1_Water | 4 | 4 | false |
| MW_WaterEdgeMaskUVSize | scalar | 1_Water | 16 | 16 | false |
| MW_WaterMaxWorldPosition | scalar | 1_Water | 0 | 0 | false |
| MW_WaterNormalIntensity | vector | 1_Water | r=0.050000001, g=0.050000001, b=1, a=1 | r=0.050000001, g=0.050000001, b=1, a=1 | false |
| MW_WaterRefractionIntensity | scalar | 1_Water | 0.30000001 | 0.30000001 | false |
| MW_WaterSlopePower | scalar | 1_Water | 1536 | 1536 | false |
| MW_WaterUVSize | scalar | 1_Water | 12 | 12 | false |
| MW_WaterWorldPositionPower | scalar | 1_Water | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_DirtColorCorrection | vector | 2_Dirt | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_DirtMaxWorldPosition | scalar | 2_Dirt | 1000000 | 1000000 | false |
| MW_DirtMaxWorldPositionPower | scalar | 2_Dirt | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_DirtNormalIntensity | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtRoughness | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtSlopePower | scalar | 2_Dirt | 128 | 128 | false |
| MW_DirtSpecular | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtUVFarMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtUVNearMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_SnowUVFarMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_TextureDirtBaseColor | texture | 2_Dirt | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_TextureDirtNormal | texture | 2_Dirt | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | false |
| MW_[x]_UseDirtAdvanced | static_switch | 2_Dirt | false | false | false |
| MW_[x]_UseDirtAdvancedUVs | static_switch | 2_Dirt | false | false | false |
| MW_[x]_UseDirtProcedurals | static_switch | 2_Dirt | true | true | false |
| MW_GrassColorCorrection | vector | 3_Grass | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_GrassMaxWorldPosition | scalar | 3_Grass | 1000000 | 1000000 | false |
| MW_GrassMaxWorldPositionPower | scalar | 3_Grass | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_GrassNormalIntensity | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassRoughness | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassSlopePower | scalar | 3_Grass | 8 | 8 | false |
| MW_GrassSpecular | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassUVFarMultiplier | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassUVNearMultiplier | scalar | 3_Grass | 1 | 1 | false |
| MW_TextureGrassBaseColor | texture | 3_Grass | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_TextureGrassNormal | texture | 3_Grass | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | false |
| MW_[x]_UseGrassAdvanced | static_switch | 3_Grass | false | false | false |
| MW_[x]_UseGrassAdvancedUVs | static_switch | 3_Grass | false | false | false |
| MW_[x]_UseGrassProcedurals | static_switch | 3_Grass | true | true | false |
| MW_StonesColorCorrection | vector | 4_Stones | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_StonesMaxWorldPosition | scalar | 4_Stones | 1000000 | 1000000 | false |
| MW_StonesMaxWorldPositionPower | scalar | 4_Stones | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_StonesNormalIntensity | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesRoughness | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesSlopePower | scalar | 4_Stones | 2 | 2 | false |
| MW_StonesSpecular | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesUVFarMultiplier | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesUVNearMultiplier | scalar | 4_Stones | 1 | 1 | false |
| MW_TextureStonesBaseColor | texture | 4_Stones | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_TextureStonesNormal | texture | 4_Stones | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | false |
| MW_[x]_UseStonesAdvanced | static_switch | 4_Stones | false | false | false |
| MW_[x]_UseStonesAdvancedUVs | static_switch | 4_Stones | false | false | false |
| MW_[x]_UseStonesProcedurals | static_switch | 4_Stones | true | true | false |
| MW_RockColorCorrection | vector | 5_Rock | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_RockNormalIntensity | scalar | 5_Rock | 1 | 1 | false |
| MW_RockRoughness | scalar | 5_Rock | 1 | 1 | false |
| MW_RockSpecular | scalar | 5_Rock | 1 | 1 | false |
| MW_RockUVFarMultiplier | scalar | 5_Rock | 1 | 1 | false |
| MW_RockUVNearMultiplier | scalar | 5_Rock | 1 | 1 | false |
| MW_TextureRockBaseColor | texture | 5_Rock | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_TextureRockNormal | texture | 5_Rock | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | false |
| MW_[x]_UseRockAdvanced | static_switch | 5_Rock | false | false | false |
| MW_[x]_UseRockAdvancedUVs | static_switch | 5_Rock | false | false | false |
| MW_[x]_UseRockProcedurals | static_switch | 5_Rock | true | true | false |
| MW_LandscapeSize | scalar | LandscapeVariation | 2017 | 2017 | false |
| MW_TextureLandscapeVariationMask | texture | LandscapeVariation | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | false |
| MW_TextureLandscapeVariationNormal | texture | LandscapeVariation | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | false |
| MW_VariationNormalIntensity | scalar | LandscapeVariation | 0.25 | 0.25 | false |
| MW_VariationWorldUVSize | scalar | LandscapeVariation | 32 | 32 | false |
| MW_[x]_UseLandscapeVariation | static_switch | LandscapeVariation | true | true | false |
| MW_[x]_UseVariationFitLandscape | static_switch | LandscapeVariation | false | false | false |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1 | false |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 0.5 | false |
| MW_UseInvertedRoughness | static_switch | Lighting | true | true | false |
| MW_DistanceBlendFadeLength | scalar | UVs | 4096 | 4096 | false |
| MW_DistanceBlendFadeOffset | scalar | UVs | 512 | 512 | false |
| MW_LandscapeWorldUVSize | scalar | UVs | 384 | 384 | false |
| MW_LandscapeWorldUVSizeFar | scalar | UVs | 8192 | 8192 | false |
| MW_UseWorldPositionUVs | static_switch | UVs | true | true | false |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MW_VolumeClouds_MASTER.MTL_MW_VolumeClouds_MASTER

Class: Material. Parent: None.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| Albedo | vector | None | r=1, g=1, b=1, a=0 | r=1, g=1, b=1, a=0 | false |
| BaseNoiseExp | scalar | None | 15 | 15 | false |
| BaseNoiseScale | scalar | None | 0.050000001 | 0.050000001 | false |
| BeerPowder | scalar | None | 20 | 20 | false |
| BeerPowderPower | scalar | None | 0.5 | 0.5 | false |
| ErosionExp | scalar | None | 6 | 6 | false |
| ErosionMax | scalar | None | 1 | 1 | false |
| ErosionNewMin | scalar | None | 0 | 0 | false |
| ErosionNoiseScale | scalar | None | 9.9999997e-06 | 9.9999997e-06 | false |
| ErosionScale | scalar | None | 0.5 | 0.5 | false |
| ErosionStength | scalar | None | 0.2 | 0.2 | false |
| Extinction | vector | None | r=0.71875, g=0.85937494, b=1, a=0 | r=0.71875, g=0.85937494, b=1, a=0 | false |
| ExtinctionScale | scalar | None | 0.050000001 | 0.050000001 | false |
| MultiScatteringContribution | scalar | None | 1 | 1 | false |
| MultiScatteringEccentricity | scalar | None | 0.1 | 0.1 | false |
| MultiScatteringOcclusion | scalar | None | 0.1 | 0.1 | false |
| NoiseHeightExp | scalar | None | 3 | 3 | false |
| NoiseHeightRange | scalar | None | 2.5 | 2.5 | false |
| PhaseBlend | scalar | None | 0.2 | 0.2 | false |
| PhaseG | scalar | None | 0.5 | 0.5 | false |
| PhaseG2 | scalar | None | -0.5 | -0.5 | false |
| WeatherUVScale | scalar | None | 0.00050000002 | 0.00050000002 | false |
| WindVector | vector | None | r=1, g=1, b=0, a=0 | r=1, g=1, b=0, a=0 | false |
| MW_TextureCloudGradient | texture | Textures | /Engine/EngineSky/VolumetricClouds/CloudGradientTexture.CloudGradientTexture | /Engine/EngineSky/VolumetricClouds/CloudGradientTexture.CloudGradientTexture | false |
| MW_TextureCloudWeather | texture | Textures | /Engine/EngineSky/VolumetricClouds/CloudWeatherTexture.CloudWeatherTexture | /Engine/EngineSky/VolumetricClouds/CloudWeatherTexture.CloudWeatherTexture | false |

### /Game/MWLandscapeAutoMaterial/Materials/FX/MTL_MWAM_VolumeCloudsA.MTL_MWAM_VolumeCloudsA

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MW_VolumeClouds_MASTER.MTL_MW_VolumeClouds_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| Albedo | vector | None | r=1, g=1, b=1, a=0 | r=0.5, g=0.5, b=0.5, a=0 | true |
| BaseNoiseExp | scalar | None | 15 | 20 | true |
| BaseNoiseScale | scalar | None | 0.050000001 | 0.050000001 | false |
| BeerPowder | scalar | None | 20 | 20 | false |
| BeerPowderPower | scalar | None | 0.5 | 0.25 | true |
| ErosionExp | scalar | None | 6 | 9 | true |
| ErosionMax | scalar | None | 1 | 1 | false |
| ErosionNewMin | scalar | None | 0 | 0 | false |
| ErosionNoiseScale | scalar | None | 9.9999997e-06 | 9.9999997e-06 | false |
| ErosionScale | scalar | None | 0.5 | 0.75 | true |
| ErosionStength | scalar | None | 0.2 | 0.2 | false |
| Extinction | vector | None | r=0.71875, g=0.85937494, b=1, a=0 | r=0.71875, g=0.85937494, b=1, a=0 | false |
| ExtinctionScale | scalar | None | 0.050000001 | 0.050000001 | false |
| MultiScatteringContribution | scalar | None | 1 | 1 | false |
| MultiScatteringEccentricity | scalar | None | 0.1 | 0.1 | false |
| MultiScatteringOcclusion | scalar | None | 0.1 | 0.15000001 | true |
| NoiseHeightExp | scalar | None | 3 | 1 | true |
| NoiseHeightRange | scalar | None | 2.5 | 2.5 | false |
| PhaseBlend | scalar | None | 0.2 | 0.2 | false |
| PhaseG | scalar | None | 0.5 | 0.5 | false |
| PhaseG2 | scalar | None | -0.5 | -0.5 | false |
| WeatherUVScale | scalar | None | 0.00050000002 | 0.00025000001 | true |
| WindVector | vector | None | r=1, g=1, b=0, a=0 | r=0.25, g=0, b=0, a=0 | true |
| MW_TextureCloudGradient | texture | Textures | /Engine/EngineSky/VolumetricClouds/CloudGradientTexture.CloudGradientTexture | /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudGradientA.TEX_MW_CloudGradientA | true |
| MW_TextureCloudWeather | texture | Textures | /Engine/EngineSky/VolumetricClouds/CloudWeatherTexture.CloudWeatherTexture | /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudWeatherA.TEX_MW_CloudWeatherA | true |

### /Game/MWLandscapeAutoMaterial/Materials/FX/MTL_MWAM_VolumeCloudsB.MTL_MWAM_VolumeCloudsB

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MW_VolumeClouds_MASTER.MTL_MW_VolumeClouds_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| Albedo | vector | None | r=1, g=1, b=1, a=0 | r=0.5, g=0.5, b=0.5, a=0 | true |
| BaseNoiseExp | scalar | None | 15 | 30 | true |
| BaseNoiseScale | scalar | None | 0.050000001 | 0.025 | true |
| BeerPowder | scalar | None | 20 | 20 | false |
| BeerPowderPower | scalar | None | 0.5 | 0.25 | true |
| ErosionExp | scalar | None | 6 | 6 | false |
| ErosionMax | scalar | None | 1 | 1 | false |
| ErosionNewMin | scalar | None | 0 | 0 | false |
| ErosionNoiseScale | scalar | None | 9.9999997e-06 | 9.9999997e-06 | false |
| ErosionScale | scalar | None | 0.5 | 0.60000002 | true |
| ErosionStength | scalar | None | 0.2 | 0.15000001 | true |
| Extinction | vector | None | r=0.71875, g=0.85937494, b=1, a=0 | r=0.71875, g=0.85937494, b=1, a=0 | false |
| ExtinctionScale | scalar | None | 0.050000001 | 0.050000001 | false |
| MultiScatteringContribution | scalar | None | 1 | 1 | false |
| MultiScatteringEccentricity | scalar | None | 0.1 | 0.1 | false |
| MultiScatteringOcclusion | scalar | None | 0.1 | 0.1 | false |
| NoiseHeightExp | scalar | None | 3 | 3 | false |
| NoiseHeightRange | scalar | None | 2.5 | 2.5 | false |
| PhaseBlend | scalar | None | 0.2 | 0.2 | false |
| PhaseG | scalar | None | 0.5 | 0.5 | false |
| PhaseG2 | scalar | None | -0.5 | -0.5 | false |
| WeatherUVScale | scalar | None | 0.00050000002 | 0.00025000001 | true |
| WindVector | vector | None | r=1, g=1, b=0, a=0 | r=0.25, g=0, b=0, a=0 | true |
| MW_TextureCloudGradient | texture | Textures | /Engine/EngineSky/VolumetricClouds/CloudGradientTexture.CloudGradientTexture | /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudGradientB.TEX_MW_CloudGradientB | true |
| MW_TextureCloudWeather | texture | Textures | /Engine/EngineSky/VolumetricClouds/CloudWeatherTexture.CloudWeatherTexture | /Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_CloudWeatherA.TEX_MW_CloudWeatherA | true |

### /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.MTL_MWAM_Landscape_DesertExample

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_DebugBake | static_switch | #Debug | false | false | false |
| MW_DebugMaskSnowWater | static_switch | #Debug | true | true | false |
| MW_DebugSnowWater | static_switch | #Debug | false | false | false |
| MW_NormalIntensity | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowColorCorrection | vector | 0_Snow | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_SnowEdgeMaskUVSize | scalar | 0_Snow | 256 | 256 | false |
| MW_SnowMaskMultiplier | scalar | 0_Snow | 1.4 | 1.4 | false |
| MW_SnowMaskPower | scalar | 0_Snow | 10 | 10 | false |
| MW_SnowNormalIntensity | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowProceduralMaskSize | scalar | 0_Snow | 32 | 32 | false |
| MW_SnowSlopePower | scalar | 0_Snow | 3 | 3 | false |
| MW_SnowUVNearMultiplier | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowWorldPosition | scalar | 0_Snow | -1500 | 0 | true |
| MW_SnowWorldPositionPower | scalar | 0_Snow | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_TextureSnowBaseColor | texture | 0_Snow | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_col.TEX_MWAM_SandA_col | true |
| MW_TextureSnowNormal | texture | 0_Snow | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_nrm.TEX_MWAM_SandA_nrm | true |
| MW_UseSnow | static_switch | 0_Snow | true | true | false |
| MW_[x]_UseSnowAdvanced | static_switch | 0_Snow | false | false | false |
| MW_[x]_UseSnowAdvancedUVs | static_switch | 0_Snow | false | false | false |
| MW_[x]_UseSnowProcedurals | static_switch | 0_Snow | true | false | true |
| MW_UseWater | static_switch | 1_Water | true | false | true |
| MW_WaterColor | vector | 1_Water | r=0.039999999, g=0.047499999, b=0.050000001, a=1 | r=0.039999999, g=0.047499999, b=0.050000001, a=1 | false |
| MW_WaterEdgeContrast | scalar | 1_Water | 4 | 4 | false |
| MW_WaterEdgeMaskUVSize | scalar | 1_Water | 16 | 16 | false |
| MW_WaterMaxWorldPosition | scalar | 1_Water | 0 | 0 | false |
| MW_WaterNormalIntensity | vector | 1_Water | r=0.050000001, g=0.050000001, b=1, a=1 | r=0.050000001, g=0.050000001, b=1, a=1 | false |
| MW_WaterRefractionIntensity | scalar | 1_Water | 0.30000001 | 0.30000001 | false |
| MW_WaterSlopePower | scalar | 1_Water | 1536 | 1536 | false |
| MW_WaterUVSize | scalar | 1_Water | 12 | 12 | false |
| MW_WaterWorldPositionPower | scalar | 1_Water | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_DirtColorCorrection | vector | 2_Dirt | r=1, g=1, b=1, a=1 | r=1.25, g=1.25, b=1.25, a=1 | true |
| MW_DirtMaxWorldPosition | scalar | 2_Dirt | 1000000 | 1000000 | false |
| MW_DirtMaxWorldPositionPower | scalar | 2_Dirt | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_DirtNormalIntensity | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtRoughness | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtSlopePower | scalar | 2_Dirt | 128 | 512 | true |
| MW_DirtSpecular | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtUVFarMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtUVNearMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_SnowUVFarMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_TextureDirtBaseColor | texture | 2_Dirt | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_col.TEX_MWAM_SandA_col | true |
| MW_TextureDirtNormal | texture | 2_Dirt | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_nrm.TEX_MWAM_SandA_nrm | true |
| MW_[x]_UseDirtAdvanced | static_switch | 2_Dirt | false | true | true |
| MW_[x]_UseDirtAdvancedUVs | static_switch | 2_Dirt | false | false | false |
| MW_[x]_UseDirtProcedurals | static_switch | 2_Dirt | true | true | false |
| MW_GrassColorCorrection | vector | 3_Grass | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_GrassMaxWorldPosition | scalar | 3_Grass | 1000000 | 1000000 | false |
| MW_GrassMaxWorldPositionPower | scalar | 3_Grass | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_GrassNormalIntensity | scalar | 3_Grass | 1 | 0.75 | true |
| MW_GrassRoughness | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassSlopePower | scalar | 3_Grass | 8 | 4 | true |
| MW_GrassSpecular | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassUVFarMultiplier | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassUVNearMultiplier | scalar | 3_Grass | 1 | 1 | false |
| MW_TextureGrassBaseColor | texture | 3_Grass | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_col.TEX_MWAM_SandA_col | true |
| MW_TextureGrassNormal | texture | 3_Grass | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_nrm.TEX_MWAM_SandA_nrm | true |
| MW_[x]_UseGrassAdvanced | static_switch | 3_Grass | false | true | true |
| MW_[x]_UseGrassAdvancedUVs | static_switch | 3_Grass | false | false | false |
| MW_[x]_UseGrassProcedurals | static_switch | 3_Grass | true | false | true |
| MW_StonesColorCorrection | vector | 4_Stones | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_StonesMaxWorldPosition | scalar | 4_Stones | 1000000 | 1000000 | false |
| MW_StonesMaxWorldPositionPower | scalar | 4_Stones | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_StonesNormalIntensity | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesRoughness | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesSlopePower | scalar | 4_Stones | 2 | 0.69999999 | true |
| MW_StonesSpecular | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesUVFarMultiplier | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesUVNearMultiplier | scalar | 4_Stones | 1 | 1 | false |
| MW_TextureStonesBaseColor | texture | 4_Stones | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandC_col.TEX_MWAM_SandC_col | true |
| MW_TextureStonesNormal | texture | 4_Stones | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandC_nrm.TEX_MWAM_SandC_nrm | true |
| MW_[x]_UseStonesAdvanced | static_switch | 4_Stones | false | false | false |
| MW_[x]_UseStonesAdvancedUVs | static_switch | 4_Stones | false | false | false |
| MW_[x]_UseStonesProcedurals | static_switch | 4_Stones | true | true | false |
| MW_RockColorCorrection | vector | 5_Rock | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_RockNormalIntensity | scalar | 5_Rock | 1 | 1 | false |
| MW_RockRoughness | scalar | 5_Rock | 1 | 1 | false |
| MW_RockSpecular | scalar | 5_Rock | 1 | 1 | false |
| MW_RockUVFarMultiplier | scalar | 5_Rock | 1 | 1 | false |
| MW_RockUVNearMultiplier | scalar | 5_Rock | 1 | 1 | false |
| MW_TextureRockBaseColor | texture | 5_Rock | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Stones_col.TEX_MWAM_Stones_col | true |
| MW_TextureRockNormal | texture | 5_Rock | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Stones_nrm.TEX_MWAM_Stones_nrm | true |
| MW_[x]_UseRockAdvanced | static_switch | 5_Rock | false | false | false |
| MW_[x]_UseRockAdvancedUVs | static_switch | 5_Rock | false | false | false |
| MW_[x]_UseRockProcedurals | static_switch | 5_Rock | true | true | false |
| MW_LandscapeSize | scalar | LandscapeVariation | 2017 | 2017 | false |
| MW_TextureLandscapeVariationMask | texture | LandscapeVariation | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | false |
| MW_TextureLandscapeVariationNormal | texture | LandscapeVariation | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | false |
| MW_VariationNormalIntensity | scalar | LandscapeVariation | 0.25 | 0.25 | false |
| MW_VariationWorldUVSize | scalar | LandscapeVariation | 32 | 128 | true |
| MW_[x]_UseLandscapeVariation | static_switch | LandscapeVariation | true | true | false |
| MW_[x]_UseVariationFitLandscape | static_switch | LandscapeVariation | false | false | false |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1.3 | true |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 1.2 | true |
| MW_UseInvertedRoughness | static_switch | Lighting | true | true | false |
| MW_DistanceBlendFadeLength | scalar | UVs | 4096 | 4096 | false |
| MW_DistanceBlendFadeOffset | scalar | UVs | 512 | 512 | false |
| MW_LandscapeWorldUVSize | scalar | UVs | 384 | 512 | true |
| MW_LandscapeWorldUVSizeFar | scalar | UVs | 8192 | 6144 | true |
| MW_UseWorldPositionUVs | static_switch | UVs | true | true | false |

### /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_IslandExample.MTL_MWAM_Landscape_IslandExample

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_DebugBake | static_switch | #Debug | false | false | false |
| MW_DebugMaskSnowWater | static_switch | #Debug | true | true | false |
| MW_DebugSnowWater | static_switch | #Debug | false | false | false |
| MW_NormalIntensity | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowColorCorrection | vector | 0_Snow | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_SnowEdgeMaskUVSize | scalar | 0_Snow | 256 | 128 | true |
| MW_SnowMaskMultiplier | scalar | 0_Snow | 1.4 | 1.1 | true |
| MW_SnowMaskPower | scalar | 0_Snow | 10 | 10 | false |
| MW_SnowNormalIntensity | scalar | 0_Snow | 1 | 0.5 | true |
| MW_SnowProceduralMaskSize | scalar | 0_Snow | 32 | 32 | false |
| MW_SnowSlopePower | scalar | 0_Snow | 3 | 3 | false |
| MW_SnowUVNearMultiplier | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowWorldPosition | scalar | 0_Snow | -1500 | 2000 | true |
| MW_SnowWorldPositionPower | scalar | 0_Snow | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_TextureSnowBaseColor | texture | 0_Snow | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Snow_col.TEX_MWAM_Snow_col | true |
| MW_TextureSnowNormal | texture | 0_Snow | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Snow_nrm.TEX_MWAM_Snow_nrm | true |
| MW_UseSnow | static_switch | 0_Snow | true | true | false |
| MW_[x]_UseSnowAdvanced | static_switch | 0_Snow | false | true | true |
| MW_[x]_UseSnowAdvancedUVs | static_switch | 0_Snow | false | false | false |
| MW_[x]_UseSnowProcedurals | static_switch | 0_Snow | true | true | false |
| MW_UseWater | static_switch | 1_Water | true | true | false |
| MW_WaterColor | vector | 1_Water | r=0.039999999, g=0.047499999, b=0.050000001, a=1 | r=0, g=0.1, b=0.1, a=1 | true |
| MW_WaterEdgeContrast | scalar | 1_Water | 4 | 4 | false |
| MW_WaterEdgeMaskUVSize | scalar | 1_Water | 16 | 16 | false |
| MW_WaterMaxWorldPosition | scalar | 1_Water | 0 | -5000 | true |
| MW_WaterNormalIntensity | vector | 1_Water | r=0.050000001, g=0.050000001, b=1, a=1 | r=0.050000001, g=0.050000001, b=1, a=1 | false |
| MW_WaterRefractionIntensity | scalar | 1_Water | 0.30000001 | 0.30000001 | false |
| MW_WaterSlopePower | scalar | 1_Water | 1536 | 1536 | false |
| MW_WaterUVSize | scalar | 1_Water | 12 | 24 | true |
| MW_WaterWorldPositionPower | scalar | 1_Water | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_DirtColorCorrection | vector | 2_Dirt | r=1, g=1, b=1, a=1 | r=2.5, g=2.5, b=2.5, a=1 | true |
| MW_DirtMaxWorldPosition | scalar | 2_Dirt | 1000000 | -4820 | true |
| MW_DirtMaxWorldPositionPower | scalar | 2_Dirt | 9.9999997e-05 | 0.001 | true |
| MW_DirtNormalIntensity | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtRoughness | scalar | 2_Dirt | 1 | 0.5 | true |
| MW_DirtSlopePower | scalar | 2_Dirt | 128 | 16 | true |
| MW_DirtSpecular | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtUVFarMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtUVNearMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_SnowUVFarMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_TextureDirtBaseColor | texture | 2_Dirt | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_col.TEX_MWAM_SandA_col | true |
| MW_TextureDirtNormal | texture | 2_Dirt | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandA_nrm.TEX_MWAM_SandA_nrm | true |
| MW_[x]_UseDirtAdvanced | static_switch | 2_Dirt | false | true | true |
| MW_[x]_UseDirtAdvancedUVs | static_switch | 2_Dirt | false | false | false |
| MW_[x]_UseDirtProcedurals | static_switch | 2_Dirt | true | true | false |
| MW_GrassColorCorrection | vector | 3_Grass | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_GrassMaxWorldPosition | scalar | 3_Grass | 1000000 | -820 | true |
| MW_GrassMaxWorldPositionPower | scalar | 3_Grass | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_GrassNormalIntensity | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassRoughness | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassSlopePower | scalar | 3_Grass | 8 | 4 | true |
| MW_GrassSpecular | scalar | 3_Grass | 1 | 0.2 | true |
| MW_GrassUVFarMultiplier | scalar | 3_Grass | 1 | 0.1 | true |
| MW_GrassUVNearMultiplier | scalar | 3_Grass | 1 | 1 | false |
| MW_TextureGrassBaseColor | texture | 3_Grass | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Grass_col.TEX_MWAM_Grass_col | true |
| MW_TextureGrassNormal | texture | 3_Grass | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Grass_nrm.TEX_MWAM_Grass_nrm | true |
| MW_[x]_UseGrassAdvanced | static_switch | 3_Grass | false | true | true |
| MW_[x]_UseGrassAdvancedUVs | static_switch | 3_Grass | false | true | true |
| MW_[x]_UseGrassProcedurals | static_switch | 3_Grass | true | true | false |
| MW_StonesColorCorrection | vector | 4_Stones | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_StonesMaxWorldPosition | scalar | 4_Stones | 1000000 | 1000000 | false |
| MW_StonesMaxWorldPositionPower | scalar | 4_Stones | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_StonesNormalIntensity | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesRoughness | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesSlopePower | scalar | 4_Stones | 2 | 1.5 | true |
| MW_StonesSpecular | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesUVFarMultiplier | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesUVNearMultiplier | scalar | 4_Stones | 1 | 1 | false |
| MW_TextureStonesBaseColor | texture | 4_Stones | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandC_col.TEX_MWAM_SandC_col | true |
| MW_TextureStonesNormal | texture | 4_Stones | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_SandC_nrm.TEX_MWAM_SandC_nrm | true |
| MW_[x]_UseStonesAdvanced | static_switch | 4_Stones | false | false | false |
| MW_[x]_UseStonesAdvancedUVs | static_switch | 4_Stones | false | false | false |
| MW_[x]_UseStonesProcedurals | static_switch | 4_Stones | true | true | false |
| MW_RockColorCorrection | vector | 5_Rock | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_RockNormalIntensity | scalar | 5_Rock | 1 | 1 | false |
| MW_RockRoughness | scalar | 5_Rock | 1 | 5 | true |
| MW_RockSpecular | scalar | 5_Rock | 1 | 1 | false |
| MW_RockUVFarMultiplier | scalar | 5_Rock | 1 | 1 | false |
| MW_RockUVNearMultiplier | scalar | 5_Rock | 1 | 1 | false |
| MW_TextureRockBaseColor | texture | 5_Rock | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Rock_col.TEX_MWAM_Rock_col | true |
| MW_TextureRockNormal | texture | 5_Rock | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Rock_nrm.TEX_MWAM_Rock_nrm | true |
| MW_[x]_UseRockAdvanced | static_switch | 5_Rock | false | false | false |
| MW_[x]_UseRockAdvancedUVs | static_switch | 5_Rock | false | false | false |
| MW_[x]_UseRockProcedurals | static_switch | 5_Rock | true | false | true |
| MW_LandscapeSize | scalar | LandscapeVariation | 2017 | 2017 | false |
| MW_TextureLandscapeVariationMask | texture | LandscapeVariation | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | false |
| MW_TextureLandscapeVariationNormal | texture | LandscapeVariation | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | false |
| MW_VariationNormalIntensity | scalar | LandscapeVariation | 0.25 | 0.25 | false |
| MW_VariationWorldUVSize | scalar | LandscapeVariation | 32 | 128 | true |
| MW_[x]_UseLandscapeVariation | static_switch | LandscapeVariation | true | true | false |
| MW_[x]_UseVariationFitLandscape | static_switch | LandscapeVariation | false | false | false |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1.3 | true |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 1.2 | true |
| MW_UseInvertedRoughness | static_switch | Lighting | true | true | false |
| MW_DistanceBlendFadeLength | scalar | UVs | 4096 | 4096 | false |
| MW_DistanceBlendFadeOffset | scalar | UVs | 512 | 512 | false |
| MW_LandscapeWorldUVSize | scalar | UVs | 384 | 512 | true |
| MW_LandscapeWorldUVSizeFar | scalar | UVs | 8192 | 6144 | true |
| MW_UseWorldPositionUVs | static_switch | UVs | true | true | false |

### /Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_MountainRangeExample.MTL_MWAM_Landscape_MountainRangeExample

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_DebugBake | static_switch | #Debug | false | false | false |
| MW_DebugMaskSnowWater | static_switch | #Debug | true | true | false |
| MW_DebugSnowWater | static_switch | #Debug | false | false | false |
| MW_NormalIntensity | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowColorCorrection | vector | 0_Snow | r=1, g=1, b=1, a=1 | r=0.89999998, g=0.94073403, b=1, a=1 | true |
| MW_SnowEdgeMaskUVSize | scalar | 0_Snow | 256 | 128 | true |
| MW_SnowMaskMultiplier | scalar | 0_Snow | 1.4 | 1.1 | true |
| MW_SnowMaskPower | scalar | 0_Snow | 10 | 10 | false |
| MW_SnowNormalIntensity | scalar | 0_Snow | 1 | 0.5 | true |
| MW_SnowProceduralMaskSize | scalar | 0_Snow | 32 | 32 | false |
| MW_SnowSlopePower | scalar | 0_Snow | 3 | 3 | false |
| MW_SnowUVNearMultiplier | scalar | 0_Snow | 1 | 1 | false |
| MW_SnowWorldPosition | scalar | 0_Snow | -1500 | -1500 | false |
| MW_SnowWorldPositionPower | scalar | 0_Snow | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_TextureSnowBaseColor | texture | 0_Snow | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Snow_col.TEX_MWAM_Snow_col | true |
| MW_TextureSnowNormal | texture | 0_Snow | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Snow_nrm.TEX_MWAM_Snow_nrm | true |
| MW_UseSnow | static_switch | 0_Snow | true | true | false |
| MW_[x]_UseSnowAdvanced | static_switch | 0_Snow | false | true | true |
| MW_[x]_UseSnowAdvancedUVs | static_switch | 0_Snow | false | false | false |
| MW_[x]_UseSnowProcedurals | static_switch | 0_Snow | true | true | false |
| MW_UseWater | static_switch | 1_Water | true | true | false |
| MW_WaterColor | vector | 1_Water | r=0.039999999, g=0.047499999, b=0.050000001, a=1 | r=0.039999999, g=0.047499999, b=0.050000001, a=1 | false |
| MW_WaterEdgeContrast | scalar | 1_Water | 4 | 4 | false |
| MW_WaterEdgeMaskUVSize | scalar | 1_Water | 16 | 16 | false |
| MW_WaterMaxWorldPosition | scalar | 1_Water | 0 | -3000 | true |
| MW_WaterNormalIntensity | vector | 1_Water | r=0.050000001, g=0.050000001, b=1, a=1 | r=0.050000001, g=0.050000001, b=1, a=1 | false |
| MW_WaterRefractionIntensity | scalar | 1_Water | 0.30000001 | 0.30000001 | false |
| MW_WaterSlopePower | scalar | 1_Water | 1536 | 1536 | false |
| MW_WaterUVSize | scalar | 1_Water | 12 | 12 | false |
| MW_WaterWorldPositionPower | scalar | 1_Water | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_DirtColorCorrection | vector | 2_Dirt | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_DirtMaxWorldPosition | scalar | 2_Dirt | 1000000 | 1000000 | false |
| MW_DirtMaxWorldPositionPower | scalar | 2_Dirt | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_DirtNormalIntensity | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtRoughness | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtSlopePower | scalar | 2_Dirt | 128 | 128 | false |
| MW_DirtSpecular | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtUVFarMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_DirtUVNearMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_SnowUVFarMultiplier | scalar | 2_Dirt | 1 | 1 | false |
| MW_TextureDirtBaseColor | texture | 2_Dirt | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Dirt_col.TEX_MWAM_Dirt_col | true |
| MW_TextureDirtNormal | texture | 2_Dirt | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Dirt_nrm.TEX_MWAM_Dirt_nrm | true |
| MW_[x]_UseDirtAdvanced | static_switch | 2_Dirt | false | false | false |
| MW_[x]_UseDirtAdvancedUVs | static_switch | 2_Dirt | false | false | false |
| MW_[x]_UseDirtProcedurals | static_switch | 2_Dirt | true | true | false |
| MW_GrassColorCorrection | vector | 3_Grass | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_GrassMaxWorldPosition | scalar | 3_Grass | 1000000 | 1000000 | false |
| MW_GrassMaxWorldPositionPower | scalar | 3_Grass | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_GrassNormalIntensity | scalar | 3_Grass | 1 | 0.5 | true |
| MW_GrassRoughness | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassSlopePower | scalar | 3_Grass | 8 | 8 | false |
| MW_GrassSpecular | scalar | 3_Grass | 1 | 0.050000001 | true |
| MW_GrassUVFarMultiplier | scalar | 3_Grass | 1 | 1 | false |
| MW_GrassUVNearMultiplier | scalar | 3_Grass | 1 | 1 | false |
| MW_TextureGrassBaseColor | texture | 3_Grass | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Grass_col.TEX_MWAM_Grass_col | true |
| MW_TextureGrassNormal | texture | 3_Grass | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Grass_nrm.TEX_MWAM_Grass_nrm | true |
| MW_[x]_UseGrassAdvanced | static_switch | 3_Grass | false | true | true |
| MW_[x]_UseGrassAdvancedUVs | static_switch | 3_Grass | false | false | false |
| MW_[x]_UseGrassProcedurals | static_switch | 3_Grass | true | true | false |
| MW_StonesColorCorrection | vector | 4_Stones | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_StonesMaxWorldPosition | scalar | 4_Stones | 1000000 | 1000000 | false |
| MW_StonesMaxWorldPositionPower | scalar | 4_Stones | 9.9999997e-05 | 9.9999997e-05 | false |
| MW_StonesNormalIntensity | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesRoughness | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesSlopePower | scalar | 4_Stones | 2 | 2 | false |
| MW_StonesSpecular | scalar | 4_Stones | 1 | 1 | false |
| MW_StonesUVFarMultiplier | scalar | 4_Stones | 1 | 2 | true |
| MW_StonesUVNearMultiplier | scalar | 4_Stones | 1 | 1 | false |
| MW_TextureStonesBaseColor | texture | 4_Stones | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Stones_col.TEX_MWAM_Stones_col | true |
| MW_TextureStonesNormal | texture | 4_Stones | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Stones_nrm.TEX_MWAM_Stones_nrm | true |
| MW_[x]_UseStonesAdvanced | static_switch | 4_Stones | false | false | false |
| MW_[x]_UseStonesAdvancedUVs | static_switch | 4_Stones | false | true | true |
| MW_[x]_UseStonesProcedurals | static_switch | 4_Stones | true | true | false |
| MW_RockColorCorrection | vector | 5_Rock | r=1, g=1, b=1, a=1 | r=1, g=1, b=1, a=1 | false |
| MW_RockNormalIntensity | scalar | 5_Rock | 1 | 0.5 | true |
| MW_RockRoughness | scalar | 5_Rock | 1 | 5 | true |
| MW_RockSpecular | scalar | 5_Rock | 1 | 1 | false |
| MW_RockUVFarMultiplier | scalar | 5_Rock | 1 | 1 | false |
| MW_RockUVNearMultiplier | scalar | 5_Rock | 1 | 1 | false |
| MW_TextureRockBaseColor | texture | 5_Rock | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Rock_col.TEX_MWAM_Rock_col | true |
| MW_TextureRockNormal | texture | 5_Rock | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/Ground/TEX_MWAM_Rock_nrm.TEX_MWAM_Rock_nrm | true |
| MW_[x]_UseRockAdvanced | static_switch | 5_Rock | false | false | false |
| MW_[x]_UseRockAdvancedUVs | static_switch | 5_Rock | false | false | false |
| MW_[x]_UseRockProcedurals | static_switch | 5_Rock | true | true | false |
| MW_LandscapeSize | scalar | LandscapeVariation | 2017 | 2017 | false |
| MW_TextureLandscapeVariationMask | texture | LandscapeVariation | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_msk.TEX_MWAM_Variation_msk | false |
| MW_TextureLandscapeVariationNormal | texture | LandscapeVariation | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | /Game/MWLandscapeAutoMaterial/Textures/Extra/TEX_MWAM_Variation_nrm.TEX_MWAM_Variation_nrm | false |
| MW_VariationNormalIntensity | scalar | LandscapeVariation | 0.25 | 0.25 | false |
| MW_VariationWorldUVSize | scalar | LandscapeVariation | 32 | 64 | true |
| MW_[x]_UseLandscapeVariation | static_switch | LandscapeVariation | true | true | false |
| MW_[x]_UseVariationFitLandscape | static_switch | LandscapeVariation | false | false | false |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1 | false |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 2 | true |
| MW_UseInvertedRoughness | static_switch | Lighting | true | true | false |
| MW_DistanceBlendFadeLength | scalar | UVs | 4096 | 4096 | false |
| MW_DistanceBlendFadeOffset | scalar | UVs | 512 | 512 | false |
| MW_LandscapeWorldUVSize | scalar | UVs | 384 | 512 | true |
| MW_LandscapeWorldUVSizeFar | scalar | UVs | 8192 | 8192 | false |
| MW_UseWorldPositionUVs | static_switch | UVs | true | true | false |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER

Class: Material. Parent: None.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_Metallic | scalar | Basic | 0 | 0 | false |
| MW_Roughness | scalar | Basic | 0.5 | 0.5 | false |
| MW_Specular | scalar | Basic | 0.5 | 0.5 | false |
| MW_Texture | texture | Basic | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | false |
| MW_UseTexture | static_switch | Basic | false | false | false |
| MW_BaseColor | vector | None | r=0.039999999, g=0.039999999, b=0.039999999, a=1 | r=0.039999999, g=0.039999999, b=0.039999999, a=1 | false |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_Black.MTL_MW_Basic_Black

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_Metallic | scalar | Basic | 0 | 0 | false |
| MW_Roughness | scalar | Basic | 0.5 | 0.5 | false |
| MW_Specular | scalar | Basic | 0.5 | 0.5 | false |
| MW_Texture | texture | Basic | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | false |
| MW_UseTexture | static_switch | Basic | false | false | false |
| MW_BaseColor | vector | None | r=0.039999999, g=0.039999999, b=0.039999999, a=1 | r=0.0040000002, g=0.0040000002, b=0.0040000002, a=1 | true |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_Chrome.MTL_MW_Basic_Chrome

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_Metallic | scalar | Basic | 0 | 1 | true |
| MW_Roughness | scalar | Basic | 0.5 | 0 | true |
| MW_Specular | scalar | Basic | 0.5 | 1 | true |
| MW_Texture | texture | Basic | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | false |
| MW_UseTexture | static_switch | Basic | false | false | false |
| MW_BaseColor | vector | None | r=0.039999999, g=0.039999999, b=0.039999999, a=1 | r=1, g=1, b=1, a=1 | true |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_ColorChecker.MTL_MW_Basic_ColorChecker

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_Metallic | scalar | Basic | 0 | 0 | false |
| MW_Roughness | scalar | Basic | 0.5 | 0.5 | false |
| MW_Specular | scalar | Basic | 0.5 | 0.5 | false |
| MW_Texture | texture | Basic | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | false |
| MW_UseTexture | static_switch | Basic | false | true | true |
| MW_BaseColor | vector | None | r=0.039999999, g=0.039999999, b=0.039999999, a=1 | r=0.039999999, g=0.039999999, b=0.039999999, a=1 | false |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_Gray.MTL_MW_Basic_Gray

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_Metallic | scalar | Basic | 0 | 0 | false |
| MW_Roughness | scalar | Basic | 0.5 | 0.5 | false |
| MW_Specular | scalar | Basic | 0.5 | 0.5 | false |
| MW_Texture | texture | Basic | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | false |
| MW_UseTexture | static_switch | Basic | false | false | false |
| MW_BaseColor | vector | None | r=0.039999999, g=0.039999999, b=0.039999999, a=1 | r=0.5, g=0.5, b=0.5, a=1 | true |

### /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_White.MTL_MW_Basic_White

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/Basic/MTL_MW_Basic_MASTER.MTL_MW_Basic_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_Metallic | scalar | Basic | 0 | 0 | false |
| MW_Roughness | scalar | Basic | 0.5 | 0.5 | false |
| MW_Specular | scalar | Basic | 0.5 | 0.5 | false |
| MW_Texture | texture | Basic | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_ColorChecker.TEX_MW_Temp_ColorChecker | false |
| MW_UseTexture | static_switch | Basic | false | false | false |
| MW_BaseColor | vector | None | r=0.039999999, g=0.039999999, b=0.039999999, a=1 | r=1, g=1, b=1, a=1 | true |

### /Game/MWLandscapeAutoMaterial/Materials/Plants/MTL_MWAM_Plant_Megascan_MASTER.MTL_MWAM_Plant_Megascan_MASTER

Class: MaterialInstanceConstant. Parent: /Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_CoverFoliage_MASTER.MTL_MWAM_CoverFoliage_MASTER.

| Name | Type | Group | Master default | Effective value | Differs from parent |
|---|---|---|---|---|---|
| MW_BaseColorContrast | scalar | ColorCorrection | 1 | 0.80000001 | true |
| MW_BaseColorCorrection | vector | ColorCorrection | r=1, g=1, b=1, a=1 | r=1.8, g=1.8, b=1.8, a=1 | true |
| MW_ColorVariationContrast | scalar | ColorCorrection | 0.25 | 0.25 | false |
| MW_[x]_UseRandomizeBaseIntensity | static_switch | ColorCorrection | true | true | false |
| MW_CameraFadeOffset | scalar | DistanceCulling | 0 | 1000 | true |
| MW_CameraFadeRange | scalar | DistanceCulling | 5000 | 4000 | true |
| MW_UseDepthFade | static_switch | DistanceCulling | false | true | true |
| MW_UseSolidOpacity | static_switch | DistanceCulling | false | false | false |
| MW_RoughnessMultiplier | scalar | Lighting | 1 | 1 | false |
| MW_RoughnessPower | scalar | Lighting | 0.5 | 1 | true |
| MW_SubSurfaceColor | vector | Lighting | r=1, g=1, b=1, a=0 | r=2, g=2, b=2, a=0 | true |
| MW_UseInvertedRoughness | static_switch | Lighting | true | true | false |
| MW_UseSubSurfaceColor | static_switch | Lighting | false | true | true |
| MW_Specular | scalar | None | 0.5 | 0.5 | false |
| MW_NormalIntensity | scalar | Normal | 1 | 1 | false |
| MW_[x]_UseWorldNormal | static_switch | Normal | false | false | false |
| MW_TextureBaseColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_TextureNormal | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_nrm.TEX_MW_Temp_nrm | false |
| MW_TextureOpacity | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_msk.TEX_MW_Temp_msk | false |
| MW_TextureSubSurfaceColor | texture | Textures | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | /Game/MWLandscapeAutoMaterial/Textures/TEX_MW_Temp_col.TEX_MW_Temp_col | false |
| MW_UseSeparateSubSurfaceTexture | static_switch | Textures | false | true | true |
| MW_[x]_UseSeparateOpacityTexture | static_switch | Textures | false | true | true |
| MW_WindIntensity | scalar | Wind | 0.2 | 0.2 | false |
| MW_WindSpeed | scalar | Wind | 0.5 | 0.5 | false |
| MW_[x]_UseWind | static_switch | Wind | false | true | true |

## Evidence and limitations

- MW_INVENTORY.json: structured inventory, proposal, exact paths, function input defaults and full side-effect record.
- native_inventory_complete.json: settled metadata and graph snapshot before later function dirtying; native_inventory_raw.json preserves first-pass baseline.
- mw_master_tool_readback.json and graphs/*.json: connection readbacks. Tool display IDs use parameter names/descriptions and can collide; native node names remain the authoritative identity.
- final_readonly_check.json: unchanged 107 disk files, clean map, exact new dirty-function set. Baseline hashes are in native inventory files.
- live_landscape_binding.json: one current Shujaiya Landscape with its area child.
- No integrated shader compile, frame profiling, save/reopen, regeneration, full-resolution texture review, rights approval or visual acceptance was performed.
