// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "BLDToolsetTypes.h"
#include "CityBLDTypes.h"
#include "ModularBuildingActor.h"

#include "CityBLDToolsetTypes.generated.h"

/** Kinds of CityBLD preset classes. */
UENUM(BlueprintType)
enum class ECityBLDPresetKind : uint8
{
	/** How a block is subdivided into parcels and which land uses the parcels get. Assigned to blocks. */
	District,
	/** What spawns on a parcel: modular buildings, static prefabs or nothing. Referenced by districts. */
	LandUse,
	/** Modular building meshes, height range and roof. Assigned to buildings and referenced by land uses. */
	BuildingStyle,
	/** Roof shape and materials. Referenced by building styles. */
	RoofStyle,
	/** Sidewalk width, materials and PCG. Referenced by districts and blocks. */
	SidewalkPreset,
	/** Ground floor mesh override. Assigned to buildings. */
	GroundFloorType,
	/** Static building prefab fitted to parcels. Referenced by land uses. */
	Prefab
};

UENUM(BlueprintType)
enum class ECityBLDIssueSeverity : uint8
{
	/** Generation will fail or produce nothing. */
	Error,
	/** Generation works but the result is probably wrong or slow. */
	Warning,
	/** Worth knowing, often intentional. */
	Info
};

/** Axis-aligned world area in cm. Only X and Y are used; Z is ignored. */
USTRUCT(BlueprintType)
struct FCityBLDBounds
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FVector Min = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FVector Max = FVector::ZeroVector;
};

/** Reference to a CityBLD class such as a District or BuildingStyle. */
USTRUCT(BlueprintType)
struct FCityBLDClassRef
{
	GENERATED_BODY()

	/** Class path. Pass it to class parameters of other tools. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString ClassPath;

	/** Name from the preset (DistrictName, LandUseName, StyleName...) or the asset name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString DisplayName;
};

/** A class reference with a weight, such as a land use in a district. */
USTRUCT(BlueprintType)
struct FCityBLDWeightedClass
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef Class;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double Weight = 0.0;

	/** Weight divided by the total weight, from 0 to 1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double Share = 0.0;
};

USTRUCT(BlueprintType)
struct FCityBLDClassUsage
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef Class;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 Count = 0;
};

USTRUCT(BlueprintType)
struct FCityBLDPresetInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	ECityBLDPresetKind Kind = ECityBLDPresetKind::District;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef Class;

	/** Blueprint asset path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString AssetPath;

	/** One-line description of the preset's key settings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString Summary;

	/** True for CityBLD sample content under /CityBLD. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bIsSampleContent = false;
};

USTRUCT(BlueprintType)
struct FCityBLDPresetList
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDPresetInfo> Presets;

	/** Matches before the MaxResults cap. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 TotalCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ReturnedCount = 0;
};

USTRUCT(BlueprintType)
struct FCityBLDPresetCount
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	ECityBLDPresetKind Kind = ECityBLDPresetKind::District;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 Count = 0;
};

USTRUCT(BlueprintType)
struct FCityBLDDistrictDescription
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDPresetInfo Preset;

	/** Subdivision method and its parameters in cm. Only the fields for SubdivisionMethod apply. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FParcelSubdivisionSettingsStruct SubdivisionRules;

	/** True when the method is Skeleton, which is slow on blocks with more than 6 simplified outline points. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bUsesSkeletonSubdivision = false;

	/** Land uses for street-facing parcels. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDWeightedClass> LandUses;

	/** Land uses for interior courtyard parcels (OffsetWithCourtyard only). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDWeightedClass> CourtyardLandUses;

	/** Sidewalk preset. When set, it overrides the block's own sidewalk preset. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef SidewalkPreset;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double DefaultSidewalkWidthMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString PCGGraphPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString MaterialPath;

	/** Z offset in cm applied to parcel geometry. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	float ParcelZOffset = 0.0f;

	/** Blocks in the current level using this district. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 BlocksInLevel = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FString> Notes;
};

USTRUCT(BlueprintType)
struct FCityBLDLandUseDescription
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDPresetInfo Preset;

	/** What spawns on parcels with this land use. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	EBuildingSpawn BuildingSpawnRule = EBuildingSpawn::ModularBuilding;

	/** Styles picked at random for modular buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDClassRef> ModularBuildingStyles;

	/** Prefabs for static buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDClassRef> StaticPrefabs;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bUsePrefabFitting = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	EStaticBuildingSpawn StaticSpawnPositioning = EStaticBuildingSpawn::StreetAligned;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double ParcelEdgeClearance = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bGenerateMesh = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString ParcelMaterialPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double DisplacementAmount = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 SeedOffset = 0;

	/** Districts that reference this land use. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDClassRef> UsedByDistricts;

	/** Parcels in the current level using this land use. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ParcelsInLevel = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FString> Notes;
};

/** Floors a style produces for a target height. */
USTRUCT(BlueprintType)
struct FCityBLDFloorSample
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double HeightMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 Floors = 0;
};

USTRUCT(BlueprintType)
struct FCityBLDBuildingStyleDescription
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDPresetInfo Preset;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString StyleDescription;

	/** Height range in meters used when a building has no explicit height. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double MinHeightMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double MaxHeightMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	EBuildingLayeringType LayeringType = EBuildingLayeringType::Simple;

	/** Floor counts at the minimum, middle and maximum of the height range. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDFloorSample> FloorSamples;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef RoofStyle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	ERoofType RoofType = ERoofType::Flat;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double RoofRidgeHeightMeters = 0.0;

	/** Floor definitions in each mesh set. 0 means the mesh set is unused. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 FacadeFloorDefinitions = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 SideFloorDefinitions = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 RearFloorDefinitions = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bUseSideMeshSetForRearFaces = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bAddTrim = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bOverrideTopFloor = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 RandomizedMaterialSlots = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bHasHLODMaterial = false;

	/** Land uses that spawn this style. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDClassRef> UsedByLandUses;

	/** Modular buildings in the current level using this style. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 BuildingsInLevel = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FString> Notes;
};

USTRUCT(BlueprintType)
struct FCityBLDBlockSummary
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FBLDActorRef Actor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef District;

	/** Points on the outer loop (road edge). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 OutlineVertexCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double AreaSquareMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FVector Centroid = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDBounds Bounds;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double SidewalkWidthMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ParcelCount = 0;

	/** Loaded modular buildings registered to this block's parcels. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 BuildingCount = 0;

	/** True when the block has parcels or block geometry. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bGenerated = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bHasBlockGeometry = false;

	/** Skeleton subdivision on a block this complex can take a long time. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bSkeletonRisk = false;
};

USTRUCT(BlueprintType)
struct FCityBLDBlockList
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDBlockSummary> Blocks;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 TotalCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ReturnedCount = 0;
};

USTRUCT(BlueprintType)
struct FCityBLDParcelInfo
{
	GENERATED_BODY()

	/** Index in the block's parcel list. Pass it to parcel tools. Indices change when the block regenerates. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 Index = INDEX_NONE;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef LandUse;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bIsCourtyard = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double AreaSquareMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FVector Centroid = FVector::ZeroVector;

	/** World-space outline in cm. Empty when shapes were not requested. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FVector> ShapePoints;

	/** Parcel edges on the street side. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 StreetEdgeCount = 0;

	/** Loaded actors spawned on the parcel. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FBLDActorRef> ChildActors;

	/** Registered actors, including ones streamed out by World Partition. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 RegisteredChildCount = 0;
};

USTRUCT(BlueprintType)
struct FCityBLDParcelList
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FBLDActorRef Block;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDParcelInfo> Parcels;

	/** Parcels on the block, before the land use filter. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 TotalCount = 0;
};

USTRUCT(BlueprintType)
struct FCityBLDBlockDescription
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDBlockSummary Summary;

	/** The block's own sidewalk preset. Ignored when the district sets one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef BlockSidewalkPreset;

	/** The sidewalk preset generation actually uses. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef EffectiveSidewalkPreset;

	/** Minimum segment length in cm when simplifying the outline for parcels. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	float MinSegmentLength = 0.0f;

	/** Maximum deviation in cm allowed when simplifying the outline for parcels. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	float MaxParcelSplineDeviation = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	float CityBlockGeoZOffset = 0.0f;

	/** World-space outer loop in cm, counter-clockwise from above. Empty when not requested. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FVector> Outline;

	/** Points on the sidewalk-inset loop. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 InnerLoopVertexCount = 0;

	/** Points on the simplified loop used for subdivision. Skeleton subdivision is slow above 6. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ParcelSplineVertexCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDClassUsage> LandUseCounts;

	/** Empty when not requested. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDParcelInfo> Parcels;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FString> Notes;
};

USTRUCT(BlueprintType)
struct FCityBLDBuildingSummary
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FBLDActorRef Actor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef Style;

	/** Target height in meters. 0 means a random height from the style's range at generation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double HeightMeters = 0.0;

	/** Generated floors. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 FloorCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 FootprintVertexCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double FootprintAreaSquareMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FVector Location = FVector::ZeroVector;

	/** Block whose parcel spawned this building. Empty for hand-placed buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FBLDActorRef OwningBlock;

	/** Parcel index on OwningBlock, or -1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ParcelIndex = INDEX_NONE;

	/** False when the building has no valid style or footprint. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bValid = false;
};

USTRUCT(BlueprintType)
struct FCityBLDBuildingList
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDBuildingSummary> Buildings;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 TotalCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ReturnedCount = 0;
};

/** One tier of a building with authored floor plates. */
USTRUCT(BlueprintType)
struct FCityBLDFloorPlateInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	double StartHeightMeters = 0.0;

	/** Point count of each shell outline on this plate. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<int32> ShellVertexCounts;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bHasRoofOverride = false;
};

USTRUCT(BlueprintType)
struct FCityBLDBuildingDescription
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDBuildingSummary Summary;

	/** World-space footprint in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FVector> FootprintWorld;

	/** Generated floor heights in cm, bottom first. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<float> FloorHeights;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDClassRef GroundFloorOverride;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString SignText;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	EBuildingGenerationCollision Collision = EBuildingGenerationCollision::EBC_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	EBuildingMeshGenerationType MeshGenerationType = EBuildingMeshGenerationType::EBM_InstancedStaticMeshComponent;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bGenerateFoundations = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bGenerateRooftops = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bAllFloorsFacade = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bPreciseHeight = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bTwinBLDUpperFloorsPreferFacade = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 NumBasementFloors = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 Seed = 0;

	/** Footprint segment indices that face a street. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<int32> StreetFacingFaces;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bHasRoofOverride = false;

	/** Roof settings that override the style's roof. Only fields with their bOverride flag set apply. Heights in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FBuildingRoofOverride RoofOverride;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bUseAuthoredFloorPlates = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDFloorPlateInfo> FloorPlates;

	/** Floors the style would produce for HeightMeters. 0 when there is no style or height. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 StyleFloorsForHeight = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FString> Notes;
};

USTRUCT(BlueprintType)
struct FCityBLDIssue
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	ECityBLDIssueSeverity Severity = ECityBLDIssueSeverity::Warning;

	/** Stable issue code such as BlockMissingDistrict. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString Code;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString Message;

	/** Actor the issue is about. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FBLDActorRef Actor;

	/** Other actor involved, such as the second of two overlapping buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FBLDActorRef OtherActor;

	/** Parcel index on Actor for parcel issues, otherwise -1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ParcelIndex = INDEX_NONE;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FVector Location = FVector::ZeroVector;

	/** Suggested fix. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString Fix;
};

USTRUCT(BlueprintType)
struct FCityBLDIssueReport
{
	GENERATED_BODY()

	/** Most severe first. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDIssue> Issues;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ErrorCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 WarningCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 InfoCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 BlocksChecked = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 BuildingsChecked = 0;

	/** Issues found before the MaxResults cap. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 TotalCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FString> Warnings;
};

USTRUCT(BlueprintType)
struct FCityBLDCityContext
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString LevelName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 BlockCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 GeneratedBlockCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 BlocksWithoutDistrict = 0;

	/** Blocks where skeleton subdivision may be slow. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 SkeletonRiskBlockCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ParcelCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 ModularBuildingCount = 0;

	/** Modular buildings not registered to any parcel (hand-placed, TwinBLD imports or orphans). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	int32 UnparentedBuildingCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bHasCityBounds = false;

	/** Area covered by blocks and buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FCityBLDBounds CityBounds;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDClassUsage> DistrictsInUse;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDClassUsage> StylesInUse;

	/** Preset classes available in the project, by kind. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FCityBLDPresetCount> PresetCounts;

	/** Licensed, Trial, Unlicensed, Checking, Unknown, Error, NotLoggedIn or Unavailable. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString LicenseState;

	/** True when editing tools are allowed to change the level. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	bool bCanEdit = false;

	/** Why editing is blocked, when bCanEdit is false. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	FString LicenseMessage;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FBLDJobStatus> RunningJobs;

	/** Suggested next steps. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CityBLDToolset")
	TArray<FString> Notes;
};
