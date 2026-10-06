// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/DataAsset.h"
#include "Templates/SubclassOf.h"

#include "WorldBLDTypes.generated.h"


class UStaticMesh;

UENUM(BlueprintType)
enum class EInteractionType : uint8
{
	// Used for allowing driveways to interact with RoadBLD sidewalks.
	FlattenSidewalks UMETA(DisplayName = "Flatten Sidewalks"),
};

// Generic interaction marker component for WorldBLD systems. Used to trigger interactions between different WorldBLD systems and actors.
UCLASS(BlueprintType, Blueprintable, ClassGroup = (WorldBLD), meta = (BlueprintSpawnableComponent))
class WORLDBLDRUNTIME_API UWorldBLDInteractionComponent : public USceneComponent
{
	GENERATED_BODY()

public:
	UWorldBLDInteractionComponent();

	// The type of interaction this component represents.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD")
	EInteractionType InteractionType {EInteractionType::FlattenSidewalks};

	// Volume used to define where the interaction applies.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WorldBLD|Interaction")
	TObjectPtr<UBoxComponent> InteractionVolume = nullptr;

	// Meshes to spawn while applying flatten-sidewalk interaction. Value is a local-space offset.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD|Flatten Sidewalks",
		meta = (EditCondition = "InteractionType == EInteractionType::FlattenSidewalks", EditConditionHides))
	TMap<UStaticMesh*, FVector> MeshesToSpawn;
};


UCLASS(Blueprintable, BlueprintType)
class WORLDBLDRUNTIME_API UWorldBLDMeshData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
    //The target mesh asset
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Meshes")
	TObjectPtr<UStaticMesh> StaticMesh{ nullptr };

    //A detailed text description of the mesh.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD")
	FString Description;

    //The name of the asset collection this mesh belongs to, if applicable. Case-sensitive.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD")
	FName AssetCollectionName;

    //The keywords used by AI agents to look up this mesh. Enter the keywords in lowercase and check spelling.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD")
	TArray<FString> Keywords;

    //The region of the world this mesh belongs to, if applicable. Enter only the capitalized English name of a city, country or continent, like "Berlin", "Germany" or "Europe".
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WorldBLD")
    FName RegionName;
};

