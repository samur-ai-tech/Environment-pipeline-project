// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDTypes.h"

UWorldBLDInteractionComponent::UWorldBLDInteractionComponent()
{
	PrimaryComponentTick.bCanEverTick = false;

	InteractionVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionVolume"));
	if (InteractionVolume)
	{
		InteractionVolume->SetupAttachment(this);
		InteractionVolume->SetBoxExtent(FVector(250.0f, 250.0f, 100.0f));
		InteractionVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		InteractionVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
		InteractionVolume->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Overlap);
	}
}

