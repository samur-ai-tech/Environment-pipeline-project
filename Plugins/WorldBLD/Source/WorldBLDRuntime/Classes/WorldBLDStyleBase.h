// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "NativeGameplayTags.h"
#include "Templates/SubclassOf.h"
#include "UObject/Object.h"
#include "WorldBLDStyleBase.generated.h"

WORLDBLDRUNTIME_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Tag_WorldBLD_Style);
WORLDBLDRUNTIME_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Tag_WorldBLD_Style_Street);
WORLDBLDRUNTIME_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Tag_WorldBLD_Style_KitRoad);
WORLDBLDRUNTIME_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Tag_WorldBLD_Style_KitRoadModule);
WORLDBLDRUNTIME_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Tag_WorldBLD_Style_RoadPreset);

class UWorldBLDKitStyleBase;
struct FWorldBLDKitStyleReference;

// Compatibility shim for older prebuilt RoadBLD binaries.
UCLASS(BlueprintType, Blueprintable, Abstract, EditInlineNew, DefaultToInstanced)
class WORLDBLDRUNTIME_API UWorldBLDKitStyleBase : public UObject
{
	GENERATED_BODY()
public:
	UWorldBLDKitStyleBase();

	virtual void Serialize(FArchive& Ar) override;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Setup", meta = (Categories = "WorldBLD.Style"))
	FGameplayTag StyleType;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Setup")
	FText StyleText {FText::FromString(TEXT("New Style"))};

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Setup")
	FString StyleName {TEXT("New Style")};

	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, AdvancedDisplay, Category = "Setup")
	FGuid UniqueId;

	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, AdvancedDisplay, Category = "Setup")
	bool bIdIsShared {false};

	// Kept as plain C++ method to avoid UHT ordering constraints in compatibility builds.
	FWorldBLDKitStyleReference CreateReference() const;

	UFUNCTION(BlueprintPure, BlueprintNativeEvent, Category = "Style")
	TArray<UWorldBLDKitStyleBase*> SubStyles() const;

	UFUNCTION(BlueprintCallable, Category = "WorldBLD")
	UWorldBLDKitStyleBase* Duplicate(UObject* NewOwner, bool bSharedUniqueId = true) const;

	UFUNCTION(BlueprintCallable, Category = "Style")
	void MakeUnique(bool bForce = false);

protected:
	virtual TArray<UWorldBLDKitStyleBase*> SubStyles_Implementation() const { return {}; }
};

// Compatibility shim type retained for binary compatibility.
UCLASS(BlueprintType, Blueprintable, Abstract)
class WORLDBLDRUNTIME_API UWorldBLDKitPrimaryStyleBase : public UWorldBLDKitStyleBase
{
	GENERATED_BODY()
public:
	UWorldBLDKitPrimaryStyleBase();
};

// Compatibility shim type retained for binary compatibility.
UCLASS(BlueprintType, Blueprintable, Abstract)
class WORLDBLDRUNTIME_API UWorldBLDKitSubStyleBase : public UWorldBLDKitStyleBase
{
	GENERATED_BODY()
public:
	UWorldBLDKitSubStyleBase();
};

USTRUCT(BlueprintType)
struct FWorldBLDKitStyleReference
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Style", meta = (Categories = "WorldBLD.Style"))
	FGameplayTag Type;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Style")
	TSubclassOf<UWorldBLDKitStyleBase> Class;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Style")
	FString Name {TEXT("")};

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Style")
	bool bIsSubStyle {false};

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Style")
	FGuid Guid;
};
