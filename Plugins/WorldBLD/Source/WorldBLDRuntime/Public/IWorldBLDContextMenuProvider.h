// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "UObject/ObjectMacros.h"

class AActor;

#include "IWorldBLDContextMenuProvider.generated.h"

UINTERFACE(MinimalAPI, BlueprintType)
class UWorldBLDContextMenuProvider : public UInterface
{
	GENERATED_BODY()
};

class WORLDBLDRUNTIME_API IWorldBLDContextMenuProvider
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "WorldBLD|ContextMenu")
	AActor* GetContextMenuTargetActor() const;

protected:
	virtual AActor* GetContextMenuTargetActor_Implementation() const { return nullptr; }
};
