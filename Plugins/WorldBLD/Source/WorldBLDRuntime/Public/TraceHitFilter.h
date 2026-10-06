// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "Engine/HitResult.h"
#include "UObject/SoftObjectPtr.h"
#include "TraceHitFilter.generated.h"

///////////////////////////////////////////////////////////////////////////////////////////////////

class AActor;
class UPrimitiveComponent;

namespace WorldBLDPlacementTrace
{
	/**
	 * Actors that should not be used as placement surfaces for editor mouse traces.
	 * Includes editor/game-hidden actors and APCGVolume generation bounds (which retain
	 * collision even when volume visualization is off / the actor is hidden).
	 */
	WORLDBLDRUNTIME_API bool ShouldIgnoreActorForPlacementTrace(const AActor* Actor);

	/**
	 * Primitive components that should not be used as placement surfaces.
	 * Includes collision volumes such as Box/Sphere/Capsule Collision (UShapeComponent),
	 * which remain editor-visible as wireframes and still block traces despite having
	 * no rendered geometry.
	 */
	WORLDBLDRUNTIME_API bool ShouldIgnoreComponentForPlacementTrace(const UPrimitiveComponent* Component);

	/** True if this hit is usable as a placement surface. */
	WORLDBLDRUNTIME_API bool IsValidPlacementTraceHit(const FHitResult& Hit);

	/**
	 * Returns the first hit in Hits that passes IsValidPlacementTraceHit.
	 * @return True if a usable hit was found.
	 */
	WORLDBLDRUNTIME_API bool FindFirstValidPlacementHit(const TArray<FHitResult>& Hits, FHitResult& OutHit);
}

// Base trace hit filter.
UCLASS(Blueprintable, BlueprintType, Abstract)
class WORLDBLDRUNTIME_API UTraceHitFilterBase : public UObject
{
	GENERATED_BODY()
public:
	// Operates on the Hits, called FilterAcceptHit on each.
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category=Filter)
	void FilterHits(UPARAM(ref) TArray<FHitResult>& Hits);

	// Returns whether or not the Hit results is accepted (kept in the array).
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category=Filter)
	bool FilterAcceptHit(const FHitResult& Hit) const;
protected:
	virtual void FilterHits_Implementation(TArray<FHitResult>& Hits);
	virtual bool FilterAcceptHit_Implementation(const FHitResult& Hit) const;
};

// Runs a series of filters in sequence
UCLASS(Blueprintable, BlueprintType, EditInlineNew)
class WORLDBLDRUNTIME_API UTraceSequentialFilter : public UTraceHitFilterBase
{
	GENERATED_BODY()
public:
	// The filters to run sequentially.
	UPROPERTY(Instanced, EditAnywhere, BlueprintReadOnly, Category=Filter)
	TArray<TObjectPtr<UTraceHitFilterBase>> Filters;

protected:
	virtual void FilterHits_Implementation(TArray<FHitResult>& Hits) override;
};

// Used to require and/or reject actors by class (includes subclasses)
UCLASS(Blueprintable, BlueprintType, EditInlineNew)
class WORLDBLDRUNTIME_API UTraceActorClassFilter : public UTraceHitFilterBase
{
	GENERATED_BODY()
public:
	// Only actors of these types can get through the filter.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category=Filter)
	TArray<TSoftClassPtr<AActor>> RequiredActorTypes;

	// These actor classes are removed.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category=Filter)
	TArray<TSoftClassPtr<AActor>> RejectedActorTypes;

protected:
	virtual bool FilterAcceptHit_Implementation(const FHitResult& Hit) const override;
};

// Simple filter for CityKitElements - either reject or only accept them.
UCLASS(Blueprintable, BlueprintType, EditInlineNew)
class WORLDBLDRUNTIME_API UTraceCityKitElementFilter : public UTraceHitFilterBase
{
	GENERATED_BODY()
public:
	// Wether we reject city kit elements (true) or only accept them (false).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category=Filter)
	bool bRejectElements {true};
protected:
	virtual bool FilterAcceptHit_Implementation(const FHitResult& Hit) const override;
};

/**
 * Rejects hidden actors, APCGVolume bounds, and collision volumes (Box/Sphere/Capsule)
 * so editor placement traces fall through to landscape / meshes underneath.
 */
UCLASS(Blueprintable, BlueprintType, EditInlineNew)
class WORLDBLDRUNTIME_API UTracePlacementSurfaceFilter : public UTraceHitFilterBase
{
	GENERATED_BODY()
protected:
	virtual bool FilterAcceptHit_Implementation(const FHitResult& Hit) const override;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
