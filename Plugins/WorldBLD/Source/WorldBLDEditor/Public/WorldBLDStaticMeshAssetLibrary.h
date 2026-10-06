// Copyright WorldBLD LLC. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "WorldBLDStaticMeshAssetLibrary.generated.h"

class AStaticMeshActor;
class UStaticMesh;
class UWorld;

USTRUCT(BlueprintType)
struct FWorldBLDStaticMeshSaveResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLD")
	TObjectPtr<UStaticMesh> SavedMesh = nullptr;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLD")
	FString PackagePath;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLD")
	bool bSuccess = false;
};

/**
 * Editor-only helpers for saving generated UStaticMesh assets and optionally spawning AStaticMeshActor.
 * Owns the generic bake/save path shared by RoadBLD bake-to-mesh and other editor mesh importers.
 */
UCLASS()
class WORLDBLDEDITOR_API UWorldBLDStaticMeshAssetLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Saves (or replaces) a generated static mesh into the given package path.
	 * Accepts either a package path (/Game/Folder/Asset) or object path (/Game/Folder/Asset.Asset).
	 * Notifies the Asset Registry and writes the package to disk.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|StaticMesh")
	static bool SaveStaticMeshAsset(
		UStaticMesh* SourceMesh,
		const FString& PackagePath,
		UStaticMesh*& OutSavedMesh);

	/** Convenience wrapper returning a result struct. */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|StaticMesh")
	static FWorldBLDStaticMeshSaveResult SaveStaticMeshAssetResult(
		UStaticMesh* SourceMesh,
		const FString& PackagePath);

	/**
	 * Spawns an AStaticMeshActor at the given transform and assigns the mesh.
	 * Returns nullptr on failure.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|StaticMesh", meta = (WorldContext = "WorldContextObject"))
	static AStaticMeshActor* SpawnStaticMeshActor(
		UObject* WorldContextObject,
		UStaticMesh* Mesh,
		const FVector& Location,
		const FRotator& Rotation,
		const FString& ActorLabel);
};
