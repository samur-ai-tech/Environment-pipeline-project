// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"

#include "WorldBLDAuthBlueprintLibrary.generated.h"

UCLASS()
class WORLDBLDEDITOR_API UWorldBLDAuthBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Opens the WorldBLD Login dialog window (editor-only). */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Auth")
	static void OpenLoginDialog();
};

