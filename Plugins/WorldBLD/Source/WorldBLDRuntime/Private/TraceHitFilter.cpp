// Copyright WorldBLD LLC. All rights reserved.

#include "TraceHitFilter.h"
#include "WorldBLDKitElementUtils.h"

#include "Components/PrimitiveComponent.h"
#include "Components/ShapeComponent.h"
#include "GameFramework/Actor.h"
#include "PCGVolume.h"

bool WorldBLDPlacementTrace::ShouldIgnoreActorForPlacementTrace(const AActor* Actor)
{
	if (!IsValid(Actor))
	{
		return true;
	}

	// Hidden actors retain collision but are not intended placement surfaces.
	if (Actor->IsHidden())
	{
		return true;
	}

#if WITH_EDITOR
	if (Actor->IsHiddenEd() || Actor->IsTemporarilyHiddenInEditor(/*bIncludeParent*/ true))
	{
		return true;
	}
#endif

	// PCG volumes are generation bounds sized to landscapes; they block mouse placement
	// even when volume visualization is off or the actor is editor-hidden.
	if (Actor->IsA(APCGVolume::StaticClass()))
	{
		return true;
	}

	return false;
}

bool WorldBLDPlacementTrace::ShouldIgnoreComponentForPlacementTrace(const UPrimitiveComponent* Component)
{
	if (!IsValid(Component))
	{
		return false;
	}

	// Box/Sphere/Capsule Collision volumes (typically a UBoxComponent named "Box")
	// draw as editor wireframes and block ECC_Visibility, but they are not meshes.
	if (Component->IsA(UShapeComponent::StaticClass()))
	{
		return true;
	}

	return false;
}

bool WorldBLDPlacementTrace::IsValidPlacementTraceHit(const FHitResult& Hit)
{
	return !ShouldIgnoreActorForPlacementTrace(Hit.GetActor())
		&& !ShouldIgnoreComponentForPlacementTrace(Hit.GetComponent());
}

bool WorldBLDPlacementTrace::FindFirstValidPlacementHit(const TArray<FHitResult>& Hits, FHitResult& OutHit)
{
	for (const FHitResult& Hit : Hits)
	{
		if (IsValidPlacementTraceHit(Hit))
		{
			OutHit = Hit;
			return true;
		}
	}
	return false;
}

void UTraceHitFilterBase::FilterHits_Implementation(TArray<FHitResult>& Hits) 
{
	for (int32 Idx = 0; Idx < Hits.Num(); Idx += 1)
	{
		if (!FilterAcceptHit(Hits[Idx]))
		{
			Hits.RemoveAtSwap(Idx);
			Idx -= 1;
		}
	}
}

bool UTraceHitFilterBase::FilterAcceptHit_Implementation(const FHitResult& Hit) const 
{
	return true;
}

void UTraceSequentialFilter::FilterHits_Implementation(TArray<FHitResult>& Hits)
{
	for (UTraceHitFilterBase* Filter : Filters)
	{
		if (IsValid(Filter))
		{
			Filter->FilterHits(Hits);
		}
	}
}

bool UTraceActorClassFilter::FilterAcceptHit_Implementation(const FHitResult& Hit) const 
{
	if (!IsValid(Hit.GetActor())) 
	{
		return RequiredActorTypes.Num() == 0;
	}
	TSubclassOf<AActor> ActorClass = Hit.GetActor()->GetClass();
	for (TSoftClassPtr<AActor> RequiredClass : RequiredActorTypes)
	{
		if (!ActorClass->IsChildOf(RequiredClass.LoadSynchronous()))
		{
			return false;
		}
	}
	for (TSoftClassPtr<AActor> RejectedClass : RejectedActorTypes)
	{
		if (ActorClass->IsChildOf(RejectedClass.LoadSynchronous()))
		{
			return false;
		}
	}
	return true;
}

bool UTraceCityKitElementFilter::FilterAcceptHit_Implementation(const FHitResult& Hit) const
{
	return !bRejectElements == (UWorldBLDKitElementUtils::FindWorldBLDKitElementImplementor(Hit.GetActor()) != nullptr);
}

bool UTracePlacementSurfaceFilter::FilterAcceptHit_Implementation(const FHitResult& Hit) const
{
	return WorldBLDPlacementTrace::IsValidPlacementTraceHit(Hit);
}
