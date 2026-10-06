// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "CityBLDTypes.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "CityBLDToolset.generated.h"

class ACityBlock;
class AModularBuildingActor;

USTRUCT(BlueprintType)
struct FCityBLDActorRef
{
	GENERATED_BODY()

	/** Canonical actor name. Use this when referring back to the actor. */
	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FString Name;

	/** Human-readable actor label shown in the World Outliner. */
	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FString Label;

	/** Soft object path / refPath for later tool calls. */
	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FString RefPath;

	/** Short class name. */
	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FString Class;
};

USTRUCT(BlueprintType)
struct FCityBLDBuildingInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FCityBLDActorRef Actor;

	/** BuildingStyle generated-class path, if assigned. */
	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FString StyleClassPath;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	float BuildingHeight = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	TArray<float> FloorHeights;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	int32 FootprintVertexCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	bool bAllFloorsFacade = false;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	bool bPreciseHeight = false;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	bool bTwinBLDUpperFloorsPreferFacade = false;
};

USTRUCT(BlueprintType)
struct FCityBLDBlockInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FCityBLDActorRef Actor;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	int32 ParcelCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	float SidewalkWidth = 0.0f;

	/** District class path, if assigned. */
	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FString DistrictClassPath;
};

USTRUCT(BlueprintType)
struct FCityBLDBuildingStyleInfo
{
	GENERATED_BODY()

	/** Soft class path of the BuildingStyle Blueprint generated class. */
	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FString ClassPath;

	/** Asset path of the Blueprint that defines the style. */
	UPROPERTY(BlueprintReadOnly, Category = "CityBLDToolset")
	FString AssetPath;
};

/**
 * Inspect CityBLD modular buildings and city blocks, list BuildingStyle assets,
 * assign a style, and regenerate a building. Does not open creator windows.
 * CityBLDDiscoveryToolset gives richer city context, preset descriptions, parcels and validation.
 * Mutating tools require a CityBLD license or active trial.
 *
 * When authoring a modular BuildingMesh externally, use Unreal local +X for width, +Z for up, and +Y for the facade/front
 * (Blender -Y with this project's export convention). Use a lower-left back-plane origin. Keep the entire X/Z perimeter
 * sharp and perfectly rectangular: no beveled outer corners and no sill, frame, trim, or other detail outside the intended
 * X/Z bounds. Details may protrude only in facade depth (+Y). AModularBuildingActor spaces modules from imported mesh
 * bounds rather than intended geometry, so any X/Z overhang creates gaps. Verify outward normals, exact bounds, and two
 * edge-to-edge copies in Unreal after import.
 */
UCLASS(BlueprintType, MinimalAPI)
class UCityBLDToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Lists every AModularBuildingActor in the current editor level.
	 * @return One summary record per modular building.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static TArray<FCityBLDBuildingInfo> ListModularBuildings();

	/**
	 * Describes a modular building: style, height, floors, footprint size, and generation flags.
	 * @param Building The AModularBuildingActor to inspect.
	 * @return Building summary.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDBuildingInfo DescribeBuilding(AModularBuildingActor* Building);

	/**
	 * Lists every ACityBlock in the current editor level.
	 * @return One summary record per city block.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static TArray<FCityBLDBlockInfo> ListCityBlocks();

	/**
	 * Lists BuildingStyle Blueprint classes discovered by the Asset Registry. Returns soft paths only.
	 * @return Style class and asset paths.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static TArray<FCityBLDBuildingStyleInfo> ListBuildingStyles();

	/**
	 * Assigns a BuildingStyle class on a modular building. This is a mutating, transactional edit.
	 * @param Building The AModularBuildingActor to update.
	 * @param StyleClass The BuildingStyle Blueprint class to assign.
	 * @return True if the style was assigned.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static bool SetBuildingStyle(AModularBuildingActor* Building, TSubclassOf<UBuildingStyle> StyleClass);

	/**
	 * Regenerates a modular building on the game thread. Can take several seconds for large buildings.
	 * @param Building The AModularBuildingActor to regenerate.
	 * @return True if generation was invoked.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static bool GenerateBuilding(AModularBuildingActor* Building);
};
