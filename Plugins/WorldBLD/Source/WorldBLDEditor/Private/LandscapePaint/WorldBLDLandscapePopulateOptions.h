// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "WorldBLDLandscapePopulateOptions.generated.h"

class ALandscape;
class UWorldBLDLandscapePreset;

UCLASS(Transient)
class UWorldBLDLandscapePopulateOptions : public UObject
{
	GENERATED_BODY()

public:
	bool CanContinue() const;

	UPROPERTY(EditAnywhere, NonTransactional, Category = "Setup", meta = (DisplayName = "Target Landscape"))
	TObjectPtr<ALandscape> TargetLandscape = nullptr;

	UPROPERTY(EditAnywhere, NonTransactional, Category = "Setup", meta = (DisplayName = "Landscape Preset"))
	TObjectPtr<UWorldBLDLandscapePreset> Preset = nullptr;
};
