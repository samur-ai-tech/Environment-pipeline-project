// Copyright WorldBLD LLC. All rights reserved.

#include "Volumes/WorldBLDPropRemovalVolume.h"

#include "Components/BrushComponent.h"
#include "Engine/CollisionProfile.h"
#include "EngineUtils.h"

AWorldBLDPropRemovalVolume::AWorldBLDPropRemovalVolume(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	if (UBrushComponent* LocalBrushComponent = GetBrushComponent())
	{
		LocalBrushComponent->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
		LocalBrushComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		LocalBrushComponent->SetGenerateOverlapEvents(false);
	}

	SetActorEnableCollision(false);
}

bool AWorldBLDPropRemovalVolume::ShouldRemoveRoadBLDStaticMeshModuleAtLocation(
	const UWorld* World,
	const FVector& WorldLocation)
{
	if (!IsValid(World))
	{
		return false;
	}

	for (TActorIterator<AWorldBLDPropRemovalVolume> It(World); It; ++It)
	{
		const AWorldBLDPropRemovalVolume* Volume = *It;
		if (!IsValid(Volume) || !Volume->ShouldSuppressRoadBLDStaticMeshModules())
		{
			continue;
		}

		if (Volume->EncompassesPoint(WorldLocation))
		{
			return true;
		}
	}

	return false;
}

bool AWorldBLDPropRemovalVolume::ShouldSuppressRoadBLDStaticMeshModules() const
{
	return bAffectRoadBLDProps && bAffectRoadBLDStaticMeshRoadModules;
}

