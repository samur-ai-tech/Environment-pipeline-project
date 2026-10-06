// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "WorldBLDEditorUtilityLibrary.generated.h"

 class ALandscape;
class APCGVolume;
 class UMaterialInterface;
class UPCGGraphInterface;

UCLASS()
class WORLDBLDEDITOR_API UWorldBLDEditorUtilityLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:

	/**
	 * Spawns a landscape at world origin with specified resolution and applies a heightmap from file
	 * Compatible with UE 5.7 and 5.8 landscape APIs
	 * 
	 * @param HeightmapFilePath - Absolute path to heightmap file (PNG or RAW format)
	 * @param Resolution - Overall resolution of the landscape (e.g., 1009, 2017, 4033, 8129)
	 * @param NumComponents - Number of components per axis (e.g., 1x1, 2x2, 4x4, 8x8)
	 * @param Material - Optional landscape material to apply (can be nullptr)
	 * @return The spawned landscape actor, or nullptr if creation failed
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Landscape")
	static ALandscape* SpawnLandscapeWithHeightmap(
		const FString& HeightmapFilePath,
		int32 Resolution,
		int32 NumComponents,
		UMaterialInterface* Material = nullptr);

	/**
	 * Assigns a material to an existing landscape, creates and saves missing target LayerInfo assets
	 * from the material, fills empty weightmaps, then opens a modal dialog to optionally import
	 * weight masks per layer. Skipping the import dialog still finalizes layer registration.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Landscape")
	static bool PaintTargetLandscape(
		ALandscape* TargetLandscape,
		UMaterialInterface* Material,
		bool bFillEmptyLayers = true,
		bool bFlipYAxis = false);

	/**
	 * Opens a setup dialog to choose a landscape and LandBLD preset, then runs PaintTargetLandscape
	 * with the preset material, spawns the default LandBLD Static/Runtime PCG volumes, and wires the
	 * selected preset into each volume's "Preset" graph parameter.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Landscape")
	static bool PopulateTargetLandscape(
		bool bFillEmptyLayers = true,
		bool bFlipYAxis = false);

	/**
	 * Spawns a PCG volume for the target landscape using the same placement factory path as
	 * manually dragging a PCG graph into the level, then fits the volume bounds to the landscape.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Landscape")
	static APCGVolume* SpawnLandscapePCGVolume(
		ALandscape* TargetLandscape,
		UPCGGraphInterface* PCGGraph,
		const FString& OptionalActorLabel = TEXT(""),
		bool bRuntimeGeneration = false);

	/**
	 * Fits an existing PCG volume to the target landscape's complete bounds.
	 * When bExpandExistingBounds is true, the result is the union of the volume's current
	 * world bounds and the landscape bounds so later tiles grow the volume instead of shrinking it.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Landscape")
	static bool FitLandscapePCGVolume(
		APCGVolume* PCGVolume,
		ALandscape* TargetLandscape,
		bool bExpandExistingBounds = true);

	/** Opens Project Settings focused on the WorldBLD settings section (UWorldBLDRuntimeSettings). */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Settings")
	static void OpenWorldBLDProjectSettings();

};
