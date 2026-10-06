// Copyright WorldBLD LLC. All Rights Reserved.

#include "WorldBLDStaticMeshAssetLibrary.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Misc/PackageName.h"
#include "UObject/SavePackage.h"

bool UWorldBLDStaticMeshAssetLibrary::SaveStaticMeshAsset(
	UStaticMesh* SourceMesh,
	const FString& PackagePath,
	UStaticMesh*& OutSavedMesh)
{
	OutSavedMesh = nullptr;

	if (!IsValid(SourceMesh) || PackagePath.IsEmpty())
	{
		return false;
	}

	const FString PackageName = FPackageName::IsValidObjectPath(PackagePath)
		? FPackageName::ObjectPathToPackageName(PackagePath)
		: PackagePath;
	const FString AssetName = FPackageName::GetLongPackageAssetName(PackageName);
	if (PackageName.IsEmpty() || AssetName.IsEmpty())
	{
		return false;
	}

	UPackage* Package = CreatePackage(*PackageName);
	if (!Package)
	{
		return false;
	}

	Package->FullyLoad();

	UStaticMesh* SavedMesh = DuplicateObject<UStaticMesh>(SourceMesh, Package, *AssetName);
	if (!IsValid(SavedMesh))
	{
		return false;
	}

	SavedMesh->SetFlags(RF_Public | RF_Standalone);
	SavedMesh->Build(false);
	SavedMesh->PostEditChange();
	SavedMesh->MarkPackageDirty();

	FAssetRegistryModule::AssetCreated(SavedMesh);

	FSavePackageArgs SaveArgs;
	SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
	SaveArgs.SaveFlags = SAVE_NoError;
	const FString Filename = FPackageName::LongPackageNameToFilename(
		PackageName,
		FPackageName::GetAssetPackageExtension());

	if (!UPackage::SavePackage(Package, SavedMesh, *Filename, SaveArgs))
	{
		return false;
	}

	OutSavedMesh = SavedMesh;
	return true;
}

FWorldBLDStaticMeshSaveResult UWorldBLDStaticMeshAssetLibrary::SaveStaticMeshAssetResult(
	UStaticMesh* SourceMesh,
	const FString& PackagePath)
{
	FWorldBLDStaticMeshSaveResult Result;
	Result.PackagePath = PackagePath;
	UStaticMesh* SavedMesh = nullptr;
	Result.bSuccess = SaveStaticMeshAsset(SourceMesh, PackagePath, SavedMesh);
	Result.SavedMesh = SavedMesh;
	if (Result.bSuccess && IsValid(SavedMesh))
	{
		Result.PackagePath = SavedMesh->GetOutermost()->GetName();
	}
	return Result;
}

AStaticMeshActor* UWorldBLDStaticMeshAssetLibrary::SpawnStaticMeshActor(
	UObject* WorldContextObject,
	UStaticMesh* Mesh,
	const FVector& Location,
	const FRotator& Rotation,
	const FString& ActorLabel)
{
	UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	if (!World || !IsValid(Mesh))
	{
		return nullptr;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AStaticMeshActor* StaticMeshActor = World->SpawnActor<AStaticMeshActor>(Location, Rotation, SpawnParams);
	if (!IsValid(StaticMeshActor))
	{
		return nullptr;
	}

	if (UStaticMeshComponent* MeshComponent = StaticMeshActor->GetStaticMeshComponent())
	{
		MeshComponent->SetStaticMesh(Mesh);
	}

	if (!ActorLabel.IsEmpty())
	{
		StaticMeshActor->SetActorLabel(ActorLabel);
	}

	return StaticMeshActor;
}
