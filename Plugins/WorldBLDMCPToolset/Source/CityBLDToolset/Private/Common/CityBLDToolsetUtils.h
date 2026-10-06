// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/CityBLDToolsetTypes.h"

class AActor;
class ACityBlock;
class AModularBuildingActor;
class UClass;
class USplineComponent;
class UWorld;

/** Helpers shared by the CityBLD toolsets. Game thread only. */
namespace CityBLDToolsetUtils
{
	/** Where a parcel child actor is registered. */
	struct FParcelOwner
	{
		ACityBlock* Block = nullptr;
		int32 ParcelIndex = INDEX_NONE;
	};

	/** The editor world. Raises an error prefixed with ToolsetName when none is loaded. */
	UWorld* GetEditorWorldOrRaise(const TCHAR* ToolsetName);

	/** Blocks in World, optionally only those whose outline bounds overlap Bounds in XY. */
	TArray<ACityBlock*> GetBlocks(UWorld* World, const TOptional<FCityBLDBounds>& Bounds = {});

	/** Modular buildings in World, optionally only those whose footprint bounds overlap Bounds in XY. */
	TArray<AModularBuildingActor*> GetBuildings(UWorld* World, const TOptional<FCityBLDBounds>& Bounds = {});

	/** Maps every loaded parcel child actor to its block and parcel index. */
	TMap<const AActor*, FParcelOwner> BuildParcelOwnerMap(UWorld* World);

	/** False with an error when Bounds is set but empty or inverted. */
	bool ValidateBounds(const TOptional<FCityBLDBounds>& Bounds, FString& OutError);

	/** True when Bounds is unset or Box overlaps it in XY. */
	bool OverlapsBounds(const FBox& Box, const TOptional<FCityBLDBounds>& Bounds);

	FCityBLDBounds MakeBounds(const FBox& Box);

	TArray<FVector> GetSplineWorldPoints(const USplineComponent* Spline);

	/** The block's outer loop in world space. */
	TArray<FVector> GetBlockOutline(const ACityBlock* Block);

	FBox GetBlockBounds(const ACityBlock* Block);

	/** The building's ShapePoints transformed to world space. */
	TArray<FVector> GetBuildingFootprintWorld(const AModularBuildingActor* Building);

	FBox GetPointsBounds(const TArray<FVector>& Points);

	/** Unsigned XY area in cm^2. */
	double PolygonArea2D(const TArray<FVector>& Points);

	/** XY area centroid, with the average Z. Falls back to the vertex average for degenerate polygons. */
	FVector PolygonCentroid(const TArray<FVector>& Points);

	/** True when two non-adjacent edges cross in XY. */
	bool IsPolygonSelfIntersecting2D(const TArray<FVector>& Points);

	/** True when the polygons' interiors overlap in XY by more than Tolerance cm. Shared or touching edges do not count. */
	bool DoPolygonsOverlap2D(const TArray<FVector>& A, const TArray<FVector>& B, double Tolerance = 5.0);

	FString GetClassPath(const UClass* Class);

	/** Blueprint package path for Blueprint classes, otherwise the class path. */
	FString GetAssetPath(const UClass* Class);

	/** The preset's own name field (DistrictName, StyleName...) when set, otherwise the asset name. */
	FString GetClassDisplayName(const UClass* Class);

	FCityBLDClassRef MakeClassRef(const UClass* Class);

	UClass* GetPresetBaseClass(ECityBLDPresetKind Kind);

	/** Every preset class of Kind in /Game and project plugin content, sorted by path. Loads the Blueprints. */
	TArray<UClass*> DiscoverPresetClasses(ECityBLDPresetKind Kind);

	/** Licensed, Trial, Unlicensed, Checking, Unknown, Error, NotLoggedIn or Unavailable. */
	FString GetLicenseStateName();

	/**
	 * Applies the same license and trial rules as CityBLD's EvaluateAccess, without dialogs. Tools that change the
	 * level must call this first. When a check is still running it starts a refresh and fails; retrying shortly after works.
	 */
	bool EnsureAuthorized(FString& OutError);

	/** EnsureAuthorized, raising the error prefixed with ToolsetName on failure. */
	bool EnsureAuthorizedOrRaise(const TCHAR* ToolsetName);

#if WITH_DEV_AUTOMATION_TESTS
	/**
	 * Lets the toolset's own automation specs make licensed calls while the scope is alive. Only honored while
	 * GIsAutomationTesting is set. Keep scopes inside a single test step so tool calls from other clients that run
	 * between ticks are never covered.
	 */
	struct FScopedTestAuthorization
	{
		FScopedTestAuthorization();
		~FScopedTestAuthorization();
		UE_NONCOPYABLE(FScopedTestAuthorization);
	};
#endif

	template <typename TEnum>
	FString EnumToString(TEnum Value)
	{
		return StaticEnum<TEnum>()->GetNameStringByValue(static_cast<int64>(Value));
	}
}
