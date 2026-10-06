// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/RoadBLDToolsetTypes.h"
#include "CrossingStyle.h"
#include "DynamicRoad/DynamicRoadData.h"
#include "PropSpawner.h"
#include "RoadBLDTypes.h"

#include "RoadBLDPresetSpec.generated.h"

/**
 * A new material instance created from an existing parent material.
 * RoadBLD masters worth starting from: /RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Asphalt_Master (road and
 * intersection surfaces), /RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Sidewalk_Master (sidewalks) and
 * /RoadBLD/RoadBLD/Materials/M_LaneDecal_Master (markings). Call ListMaterialParameters on the parent first:
 * every parameter name used here must exist on it.
 */
USTRUCT(BlueprintType)
struct FRoadBLDMaterialVariantSpec
{
	GENERATED_BODY()

	/** Parent material or material instance path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Parent;

	/** Asset name suffix. The asset is saved as MI_<Name>. Defaults to a name derived from the preset and slot. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Name;

	/** Scalar parameter overrides, by parameter name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TMap<FString, float> Scalars;

	/** Vector/color parameter overrides, by parameter name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TMap<FString, FLinearColor> Vectors;

	/** Texture parameter overrides: parameter name -> texture asset path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TMap<FString, FString> Textures;

	/** Static switch overrides, by parameter name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TMap<FString, bool> StaticSwitches;
};

/** A material slot: either an existing material Path, or a new Variant. Leave both empty for no material. */
USTRUCT(BlueprintType)
struct FRoadBLDMaterialRef
{
	GENERATED_BODY()

	/** Existing material asset path. Ignored when Variant is set. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Path;

	/** Creates a new material instance for this slot. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDMaterialVariantSpec> Variant;
};

/** A painted line on a lane edge or the centerline. */
USTRUCT(BlueprintType)
struct FRoadBLDMarkingSpec
{
	GENERATED_BODY()

	/** Line width in cm (typically 10-20). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Width = 15.0;

	/** Marking material. Empty Path and no Variant means no marking. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDMaterialRef Material;

	/** Lateral offset from the edge in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double EdgeOffset = 0.0;

	/** Texture tiling along the road (dash length control for dashed-line materials). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double TextureVScale = 1.0;
};

/** One lane, ordered from the centerline outwards on its side. */
USTRUCT(BlueprintType)
struct FRoadBLDLaneSpec
{
	GENERATED_BODY()

	/** Lane width in cm. Typical: driving 330-370, parking 250, bike 150-200, shoulder 100-300, median 100-600. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Width = 350.0;

	/** Normal, Parking, Border, Restricted, Shoulder, CenterTurn or Median. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Type = TEXT("Normal");

	/** Marking on this lane's outer edge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDMarkingSpec OuterMarking;

	/** Optional surface overlay for this lane only (bike lane paint, bus lane tint, median grass). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDMaterialRef OverlayMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double TextureUScale = 1000.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double TextureVScale = 1000.0;

	/** How this lane's marking is masked at junctions. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	ESegmentBehavior SegmentBehavior = ESegmentBehavior::UseFullMask;
};

USTRUCT(BlueprintType)
struct FRoadBLDModuleSpec
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	ERoadModulePosition Position = ERoadModulePosition::Center;

	/** Road module class path (see ListStyleAssets with Kind=RoadModule). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString ModuleClass;
};

/** Scatters meshes along the road (lamp posts, trees, bollards). X/Y pairs are random min/max ranges. */
USTRUCT(BlueprintType)
struct FRoadBLDPropSpawnerSpec
{
	GENERATED_BODY()

	/** Static mesh asset paths chosen at random. Repeat an entry to weight it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> Meshes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	EEdgeSnap Edge = EEdgeSnap::RightEdge;

	/** Sideways offset range from the edge, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector2D EdgeOffset = FVector2D::ZeroVector;

	/** Spacing range between props along the road, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector2D DistanceBetweenProps = FVector2D(2000.0, 2000.0);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector2D MinAndMaxScale = FVector2D(1.0, 1.0);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector2D ZOffset = FVector2D::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRotator RotationOffset = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bRandomZRotation = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bAlignToWorldZ = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	ESpawnArea SpawnArea = ESpawnArea::RoadOnly;
};

USTRUCT(BlueprintType)
struct FRoadBLDSidewalkPartitionSpec
{
	GENERATED_BODY()

	/** Partition width in cm, measured from the curb outwards. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Width = 100.0;

	/** False for planting strips and furniture zones. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bWalkable = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDMaterialRef Material;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double TextureUScale = 1000.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double TextureVScale = 1000.0;
};

/** A sidewalk preset created alongside the road preset. */
USTRUCT(BlueprintType)
struct FRoadBLDSidewalkSpec
{
	GENERATED_BODY()

	/** Asset name suffix; saved as RSP_<Name>. Defaults to <PresetName>_Left/Right. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Name;

	/** Total sidewalk width in cm (typical 150-500). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Width = 250.0;

	/** Curb height above the road surface in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double ZOffset = 15.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDMaterialRef Material;

	/** Material for sidewalk corners at junctions. Empty uses Material. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDMaterialRef CornerMaterial;

	/** Curb road module class path, for example /RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_USA_Curb. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString CurbClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double CurbCutLowerAmount = 10.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDMaterialRef CurbCutMaterial;

	/** Optional material strips from curb to outer edge. Widths should add up to Width. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDSidewalkPartitionSpec> Partitions;
};

/** Sidewalk for one side of a preset. Set exactly one of bNone, Preset or Inline. */
USTRUCT(BlueprintType)
struct FRoadBLDSidewalkChoice
{
	GENERATED_BODY()

	/** No sidewalk on this side. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bNone = false;

	/** Existing sidewalk preset class path (see ListStyleAssets with Kind=SidewalkPreset). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Preset;

	/** Creates a new sidewalk preset. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDSidewalkSpec> Inline;
};

/**
 * Road preset specification. Every optional field left unset is inherited from BasePreset (or RoadBLD defaults).
 * Start from DescribePreset(...).Spec of a similar preset, change what the prompt asks for, and set BasePreset to
 * that preset's Id so unmentioned settings (modules, props, bridge, landscape) carry over. All lengths are cm.
 */
USTRUCT(BlueprintType)
struct FRoadBLDPresetSpec
{
	GENERATED_BODY()

	/** Display name. Also names the asset: /Game/RoadBLD_Generated/Presets/RP_<Name>. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Name;

	/** Preset Id to inherit unset fields from. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString BasePreset;

	/** Replace an existing generated preset (and generated materials/sidewalks) with the same name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bOverwrite = false;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FString> Description;

	/** Searchable tags, for example ["boulevard", "tree-lined", "european"]. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<TArray<FString>> Tags;

	/** Capitalized English region name such as USA, UK, Germany, Japan. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FString> Region;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<ERoadPresetCategory> Category;

	/** Lanes left of the centerline (opposing traffic in right-hand-traffic regions), centerline outwards. [] for none. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<TArray<FRoadBLDLaneSpec>> LeftLanes;

	/** Lanes right of the centerline, centerline outwards. [] for none. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<TArray<FRoadBLDLaneSpec>> RightLanes;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDMarkingSpec> CenterlineMarking;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<ESegmentBehavior> CenterlineSegmentBehavior;

	/** Positive values stop markings earlier before junctions (cm). */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> LaneMarkingIntersectionOffset;

	/** Road surface material. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDMaterialRef> RoadMaterial;

	/** Junction surface material. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDMaterialRef> IntersectionMaterial;

	/** Bridge abutment wall material. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDMaterialRef> AbutmentMaterial;

	/** Blend distance from road to junction surface, cm (0-5000). */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> IntersectionBlendDistance;

	/** Crown height from edge to center, cm (0-100). 0 is flat. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> RoadCrownHeight;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<bool> bDisableRoadThickness;

	/** Adds a swept profile strip along both outer asphalt edges (rolled edges, gravel verges). */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<bool> bEnableRoadEdgeDetail;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDMaterialRef> RoadEdgeDetailMaterial;

	/** Float curve asset path describing the edge-detail cross-section. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FString> RoadEdgeDetailProfile;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> RoadEdgeDetailProfileScale;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> RoadEdgeDetailUScale;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> RoadEdgeDetailVScale;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<bool> bGenerateAbutments;

	/** Height above ground (cm) where a road counts as a bridge. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> AbutmentThreshold;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> BridgeRangeGrowth;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<bool> bEnableLandscapePaint;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FString> LandscapePaintLayerName;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> LandscapePaintWidthExtension;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> LandscapePaintFalloff;

	/** Road modules (curbs, gutters, guardrails, barriers, supports). Replaces the base list when set. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<TArray<FRoadBLDModuleSpec>> RoadModules;

	/** Prop spawners. Replaces the base list when set. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<TArray<FRoadBLDPropSpawnerSpec>> PropSpawners;

	/** Generate crosswalks automatically at junctions. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<bool> bAutomaticCrossings;

	/** Crossing style class path used for automatic crossings. Empty for the default style. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FString> CrossingStyle;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDSidewalkChoice> LeftSidewalk;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FRoadBLDSidewalkChoice> RightSidewalk;

	/** Actor tags stamped on generated single-road geometry. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<TArray<FString>> ActorTags;

	/** PCG graph asset path executed on generated road geometry. */
	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<FString> RoadPCGGraph;

	UPROPERTY(EditAnywhere, Category = "RoadBLDToolset")
	TOptional<double> ElementEdgeZOffset;
};

USTRUCT(BlueprintType)
struct FRoadBLDValidationIssue
{
	GENERATED_BODY()

	/** Spec field the issue refers to, for example RightLanes[1].Width. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Field;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Message;
};

USTRUCT(BlueprintType)
struct FRoadBLDValidationReport
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bValid = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDValidationIssue> Errors;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDValidationIssue> Warnings;

	/** Lane layout of the resolved preset (base preset merged with the spec). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDPresetTraits Traits;

	/** Package paths that CreatePresetFromSpec would create or overwrite. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> AssetsToWrite;
};

USTRUCT(BlueprintType)
struct FRoadBLDCreatePresetResult
{
	GENERATED_BODY()

	/** True when the preset asset was written. When false, read Report.Errors, fix the spec and retry. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bSucceeded = false;

	/** Preset Id to pass to CreateRoad, ChangePreset and other authoring tools. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString PresetId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> WrittenAssets;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDValidationReport Report;

	/** Roads re-initialized from the updated preset (UpdatePreset with bReapplyToRoads). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDActorRef> ReappliedRoads;
};
