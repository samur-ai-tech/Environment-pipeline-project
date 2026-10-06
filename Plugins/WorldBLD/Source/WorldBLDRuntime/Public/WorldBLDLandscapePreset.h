// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "WorldBLDLandscapePreset.generated.h"

class UMaterialInterface;
class UPrimaryDataAsset;
class UTextureRenderTarget2D;

/**
 * Data asset describing landscape material defaults and LandBLD scattering parameters.
 */
UCLASS(BlueprintType, Blueprintable)
class WORLDBLDRUNTIME_API UWorldBLDLandscapePreset : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape",
		meta = (DisplayName = "Landscape Material"))
	TObjectPtr<UMaterialInterface> LandscapeMaterial = nullptr;

	// ---- Shrubs (Static Scatter Base) ----

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Shrubs(Static Scatter Base)",
		meta = (DisplayName = "Shrubs A", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> ShrubsA = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Shrubs(Static Scatter Base)",
		meta = (DisplayName = "Shrubs A Density", ClampMin = "0.0"))
	float ShrubsADensity = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Shrubs(Static Scatter Base)",
		meta = (DisplayName = "Shrubs A Self Collision"))
	bool bShrubsASelfCollision = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Shrubs(Static Scatter Base)",
		meta = (DisplayName = "Shrubs A Bounds Scale"))
	float ShrubsABoundsScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Shrubs(Static Scatter Base)",
		meta = (DisplayName = "Shrubs B", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> ShrubsB = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Shrubs(Static Scatter Base)",
		meta = (DisplayName = "Shrubs B Density", ClampMin = "0.0"))
	float ShrubsBDensity = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Shrubs(Static Scatter Base)",
		meta = (DisplayName = "Shrubs B Self Collision"))
	bool bShrubsBSelfCollision = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Shrubs(Static Scatter Base)",
		meta = (DisplayName = "Shrubs B Bounds Scale"))
	float ShrubsBBoundsScale = 1.0f;

	// ---- Grass (Runtime Scatter Base) ----

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 1", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> GrassLayer1 = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 2", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> GrassLayer2 = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 3", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> GrassLayer3 = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 1 Density", ClampMin = "0.0"))
	float GrassLayer1Density = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 2 Density", ClampMin = "0.0"))
	float GrassLayer2Density = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 3 Density", ClampMin = "0.0"))
	float GrassLayer3Density = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 1 Bound Scale"))
	float GrassLayer1BoundScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 2 Bound Scale"))
	float GrassLayer2BoundScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 3 Bound Scale"))
	float GrassLayer3BoundScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 1 Self Collision"))
	bool bGrassLayer1SelfCollision = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 2 Self Collision"))
	bool bGrassLayer2SelfCollision = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Grass(Runtime Scatter Base)",
		meta = (DisplayName = "Grass Layer 3 Self Collision"))
	bool bGrassLayer3SelfCollision = true;

	// ---- Forest ----

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Mature Forest Trees", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> MatureForestTrees = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Young Forest Trees", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> YoungForestTrees = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Bushes", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> ForestBushes = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Groundcover", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> ForestGroundcover = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Rocks", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> ForestRocks = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Pebbles", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> ForestPebbles = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Flowmap Texture"))
	TObjectPtr<UTextureRenderTarget2D> ForestFlowmapTexture = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Trees Density", ClampMin = "0.0"))
	float ForestTreesDensity = 0.005f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Bushes Density", ClampMin = "0.0"))
	float ForestBushesDensity = 0.001f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Groundcover Density", ClampMin = "0.0"))
	float ForestGroundcoverDensity = 6.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Young Trees Ratio", ClampMin = "0.0"))
	float YoungTreesRatio = 5.0f;


	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Rocks Density", ClampMin = "0.0"))
	float ForestRocksDensity = 0.0002f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Forest",
		meta = (DisplayName = "Forest Pebbles Density", ClampMin = "0.0"))
	float ForestPebblesDensity = 6.0f;

	// ---- Fields ----

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Fields",
		meta = (DisplayName = "Field Type 1", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> FieldType1 = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Fields",
		meta = (DisplayName = "Field Type 2", AllowedClasses = "/WorldBLD/MiniTools/LandBLD/PCG/DataAssets/DataAssetStructure/LandBLDMeshData.LandBLDMeshData_C"))
	TObjectPtr<UPrimaryDataAsset> FieldType2 = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Fields",
		meta = (DisplayName = "Field Grid Size"))
	FVector FieldGridSize = FVector(250.0f, 150.0f, 100.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Landscape|Fields",
		meta = (DisplayName = "Field Output Bound Scale"))
	float FieldOutputBoundScale = 2.5f;
};
