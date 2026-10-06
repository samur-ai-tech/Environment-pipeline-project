// Copyright WorldBLD LLC. All rights reserved. 

#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "WorldBLDKitEditorUtils.generated.h"

UCLASS()
class WORLDBLDEDITOR_API UWorldBLDKitEditorUtils : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:

	UFUNCTION(BlueprintCallable, Category="WorldBLDEditor|Utils")
	static FString GetPlatformUserUniqueId();

	UFUNCTION(BlueprintCallable, Category = "WorldBLDEditor|Utils")
	static const UObject* GetStyleObjectByName(const UObject* InObj, const FName& Name);

	UFUNCTION(BlueprintCallable, Category = "WorldBLDEditor|Utils")
	static void GetAllWidgetsWithInterface(UWidget* Parent, TSubclassOf<UInterface> Interface, TArray<UWidget*>& FoundWidgets);

	static FString Internal_GetPlatformUserUniqueId();	


};
