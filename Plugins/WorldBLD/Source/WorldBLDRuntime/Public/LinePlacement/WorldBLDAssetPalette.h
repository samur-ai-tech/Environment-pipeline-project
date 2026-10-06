// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Engine/StaticMesh.h"
#include "Math/RandomStream.h"
#include "WorldBLDAssetPalette.generated.h"

/**
 * Describes a single placeable asset entry within a UWorldBLDAssetPalette.
 * Defines the mesh to use and per-instance randomization parameters.
 */
USTRUCT(BlueprintType)
struct WORLDBLDRUNTIME_API FPlacedAsset
{
	GENERATED_BODY()

	/** The static mesh to place */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Placement")
	TSoftObjectPtr<UStaticMesh> Mesh;

	/** Minimum uniform scale applied to placed instances */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Placement", meta=(ClampMin="0.01"))
	float MinScale = 1.0f;

	/** Maximum uniform scale applied to placed instances */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Placement", meta=(ClampMin="0.01"))
	float MaxScale = 1.0f;

	/**
	 * Each placed instance receives a random yaw rotation in [0, ZRotationRange] degrees.
	 * Set to 0 to keep all instances facing the same direction.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Placement", meta=(ClampMin="0.0", ClampMax="360.0"))
	float ZRotationRange = 0.0f;

	/** Additional vertical offset (cm) added to the surface-traced placement position */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Placement")
	float ZOffset = 0.0f;

	/** Spacing between instances of this asset along the spline (cm). 0 = use palette default */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Placement", meta=(ClampMin="0.0"))
	float SpacingOverride = 0.0f;

	bool operator==(const FPlacedAsset& Other) const
	{
		return Mesh == Other.Mesh
			&& MinScale == Other.MinScale
			&& MaxScale == Other.MaxScale
			&& ZRotationRange == Other.ZRotationRange
			&& ZOffset == Other.ZOffset
			&& SpacingOverride == Other.SpacingOverride;
	}
};

FORCEINLINE uint32 GetTypeHash(const FPlacedAsset& Asset)
{
	return HashCombine(GetTypeHash(Asset.Mesh), GetTypeHash(Asset.MinScale));
}

/**
 * A DataAsset subclass that defines a weighted collection of FPlacedAsset entries
 * for use with line/scatter placement tools. Create Blueprint subclasses to configure
 * specific asset palettes (e.g., trees, lampposts, benches).
 */
UCLASS(BlueprintType, Blueprintable)
class WORLDBLDRUNTIME_API UWorldBLDAssetPalette : public UDataAsset
{
	GENERATED_BODY()

public:
	/**
	 * Map of asset entries to their relative spawn weights.
	 * Higher weight values result in more frequent placement.
	 * Weights do not need to sum to any particular value.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Palette")
	TMap<FPlacedAsset, float> Assets;

	/**
	 * Default spacing between placed instances along the spline (cm).
	 * Individual FPlacedAsset entries can override this via SpacingOverride.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Palette", meta=(ClampMin="1.0"))
	float DefaultSpacing = 200.0f;

	/**
	 * Selects a random entry from Assets using weighted sampling.
	 * @param Rng Random stream for deterministic or random results
	 * @param OutAsset Receives the sampled asset entry
	 * @return true if a valid entry was found and returned
	 */
	UFUNCTION(BlueprintCallable, Category="Palette")
	bool SampleWeighted(UPARAM(ref) FRandomStream& Rng, FPlacedAsset& OutAsset) const;
};
