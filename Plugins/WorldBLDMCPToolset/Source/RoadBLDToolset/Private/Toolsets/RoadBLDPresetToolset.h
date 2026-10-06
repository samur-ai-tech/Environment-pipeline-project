// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Presets/RoadBLDPresetSpec.h"
#include "Templates/SubclassOf.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "RoadBLDPresetToolset.generated.h"

class UDynamicRoadDrawPreset;

USTRUCT(BlueprintType)
struct FRoadBLDAssetResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bSucceeded = false;

	/** Object path of the asset. Use it as a material Path in preset specs. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString AssetPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> Errors;
};

/**
 * Create new road styles from JSON specs: road presets (lanes, markings, surfaces, modules, props, sidewalks) and
 * material variants of existing masters. Workflow: DescribePreset on the closest reference preset below to learn the
 * preset structure and the materials it uses, edit its Spec to match the prompt (set BasePreset, a new Name, and only
 * the fields that change), ValidatePreset, fix every error, then CreatePresetFromSpec and use the returned PresetId
 * with the authoring tools. For new looks, give material slots a Variant: {"Parent": master path,
 * "Scalars"/"Vectors"/"Textures": overrides} after checking parameter names with ListMaterialParameters.
 * Assets are written under /Game/RoadBLD_Generated.
 *
 * RoadBLD reference kit (study with DescribePreset / ListMaterialParameters; reuse paths directly in specs):
 * Road presets (Preset Ids):
 * - /RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Street_2Lane.RP_Default_USA_Street_2Lane_C (two-lane city street)
 * - /RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Street_3Lane_1Way.RP_Default_USA_Street_3Lane_1Way_C (three-lane one-way street)
 * - /RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Boulevard_4Lane_CenterTurns.RP_Default_USA_Boulevard_4Lane_CenterTurns_C (four-lane boulevard with center turn lanes)
 * - /RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Freeway_2Lane.RP_Default_USA_Freeway_2Lane_C (two-lane freeway)
 * - /RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Freeway_3Lane.RP_Default_USA_Freeway_3Lane_C (three-lane freeway)
 * Sidewalk presets: /RoadBLD/RoadBLD/RoadKit_USA/Presets/Sidewalks/RSP_USA_StandardSidewalk,
 *   /RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/RSP_Sample_ConcreteSidewalk
 * Crossing styles: /RoadBLD/RoadBLD/RoadKit_USA/Presets/Crossings/CP_USA_ParallelCrosswalk,
 *   /RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/CP_SampleCrossing
 * Lane presets: /RoadBLD/RoadBLD/RoadKit_USA/Presets/Lanes/Lane_NormalDriving, Lane_BikeLane, Lane_Restricted (same folder)
 * Road modules: /RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_USA_Curb, RM_USA_Gutter, RM_USA_Guardrail,
 *   RM_HighwaySupport, RM_HighwaySupport_Wide, RM_Photoreal_ProceduralBridgeBarrier (same folder);
 *   /RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/RM_Sample_Curb, RM_Sample_StreetLights,
 *   RM_Sample_Bridge, RM_Sample_ProceduralBridge, RM_Sample_HighwaySupport (same folder)
 * PCG graphs: /RoadBLD/RoadBLD/RoadKit_USA/PCG/PCG_USA_CityStreet, /RoadBLD/RoadBLD/RoadKit_USA/PCG/PCG_USA_Freeway
 * Master materials (Variant parents): /RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Asphalt_Master,
 *   /RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Sidewalk_Master, /RoadBLD/RoadBLD/Materials/M_LaneDecal_Master,
 *   /RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_EdgeDetail_Master, M_RoadBLD_Abutment_Master, M_RoadBLD_TireWear_Master
 *   (same folder), /RoadBLD/RoadBLD/RoadKit_USA/Materials/Kit_Freeway_A_Master
 * Sample material instances: /RoadBLD/RoadBLD/DefaultRoadKit/Materials/MI_RoadBLD_Asphalt_Road, MI_RoadBLD_Asphalt_Road_Worn,
 *   MI_RoadBLD_Default_Abutment (same folder); /RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_USA_Sidewalk, MI_USA_Sidewalk_WS,
 *   MI_USA_Concrete_WS, MI_USA_Curb, MI_USA_Gutter, MI_HardnedTar, MI_RuralRoad_EdgeDetail (same folder)
 * ListStyleAssets flags all of these with bIsRecommended=true.
 */
UCLASS(BlueprintType, MinimalAPI)
class URoadBLDPresetToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Dry run of CreatePresetFromSpec: checks enums, ranges, asset paths, material parameter names and name
	 * collisions without writing anything.
	 * @param Spec Preset spec.
	 * @return Errors to fix, warnings, the resolved lane layout and the assets that would be written.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDValidationReport ValidatePreset(const FRoadBLDPresetSpec& Spec);

	/**
	 * Creates a road preset from a spec, including its material variants and inline sidewalk presets.
	 * Nothing is written when validation fails; read Report.Errors and retry.
	 * @param Spec Preset spec.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDCreatePresetResult CreatePresetFromSpec(const FRoadBLDPresetSpec& Spec);

	/**
	 * Updates a preset previously created by this toolset. Unset spec fields keep their current values.
	 * @param Preset Generated preset Id (under /Game/RoadBLD_Generated).
	 * @param Spec Fields to change. Name is required. Omit BasePreset (or leave it as this preset's own Id); another base is an error.
	 * @param bReapplyToRoads Re-initialize every road using this preset (per-road lane edits are lost). Rebuild afterwards.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDCreatePresetResult UpdatePreset(
		TSubclassOf<UDynamicRoadDrawPreset> Preset,
		const FRoadBLDPresetSpec& Spec,
		bool bReapplyToRoads = false);

	/**
	 * Creates a standalone material instance under /Game/RoadBLD_Generated/Materials/Shared for reuse across presets.
	 * @param Spec Parent material, Name and parameter overrides.
	 * @param bOverwrite Update the instance if it already exists.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDAssetResult CreateMaterialVariant(const FRoadBLDMaterialVariantSpec& Spec, bool bOverwrite = false);
};
