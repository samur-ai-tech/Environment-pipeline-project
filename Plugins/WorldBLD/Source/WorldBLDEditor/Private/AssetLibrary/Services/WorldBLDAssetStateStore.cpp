// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/Services/WorldBLDAssetStateStore.h"

#include "AssetLibrary/WorldBLDAssetLibraryTypes.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "JsonObjectConverter.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"

namespace
{
	constexpr const TCHAR* ProjectImportedMapFieldName = TEXT("ImportedPackageRootsByAssetId");
}

FString FWorldBLDAssetStateStore::GetCacheDirectory()
{
	return FPaths::Combine(FPlatformProcess::UserSettingsDir(), TEXT("WorldBLD"), TEXT("AssetLibrary"), TEXT("Cache"));
}

FString FWorldBLDAssetStateStore::GetManifestPath()
{
	return FPaths::Combine(FPlatformProcess::UserSettingsDir(), TEXT("WorldBLD"), TEXT("AssetLibrary"), TEXT("manifest.json"));
}

FString FWorldBLDAssetStateStore::GetProjectImportedManifestPath()
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("WorldBLD"), TEXT("AssetLibrary"), TEXT("project_imported_assets.json"));
}

bool FWorldBLDAssetStateStore::LoadStates(TMap<FString, FWorldBLDAssetDownloadState>& OutStates)
{
	OutStates.Reset();

	FString Content;
	if (!FFileHelper::LoadFileToString(Content, *GetManifestPath()))
	{
		return false;
	}

	FWorldBLDAssetCacheManifest Manifest;
	if (!FJsonObjectConverter::JsonObjectStringToUStruct(Content, &Manifest, 0, 0))
	{
		return false;
	}

	OutStates = MoveTemp(Manifest.AssetStates);
	return true;
}

bool FWorldBLDAssetStateStore::SaveStates(const TMap<FString, FWorldBLDAssetDownloadState>& States)
{
	FWorldBLDAssetCacheManifest Manifest;
	Manifest.AssetStates = States;

	FString Content;
	if (!FJsonObjectConverter::UStructToJsonObjectString(Manifest, Content, 0, 0))
	{
		return false;
	}

	IFileManager::Get().MakeDirectory(*FPaths::GetPath(GetManifestPath()), true);
	return FFileHelper::SaveStringToFile(Content, *GetManifestPath());
}

bool FWorldBLDAssetStateStore::LoadProjectImportedPackageRoots(TMap<FString, FString>& OutImportedPackageRootsByAssetId)
{
	OutImportedPackageRootsByAssetId.Reset();

	FString Content;
	if (!FFileHelper::LoadFileToString(Content, *GetProjectImportedManifestPath()))
	{
		return false;
	}

	TSharedPtr<FJsonObject> RootObject;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Content);
	if (!FJsonSerializer::Deserialize(Reader, RootObject) || !RootObject.IsValid())
	{
		return false;
	}

	const TSharedPtr<FJsonObject>* ImportedMapObject = nullptr;
	if (!RootObject->TryGetObjectField(ProjectImportedMapFieldName, ImportedMapObject) || ImportedMapObject == nullptr || !ImportedMapObject->IsValid())
	{
		return false;
	}

	for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*ImportedMapObject)->Values)
	{
		if (Pair.Key.IsEmpty() || !Pair.Value.IsValid())
		{
			continue;
		}

		FString ImportedPackageRoot;
		if (!Pair.Value->TryGetString(ImportedPackageRoot) || ImportedPackageRoot.IsEmpty())
		{
			continue;
		}

		OutImportedPackageRootsByAssetId.Add(Pair.Key, MoveTemp(ImportedPackageRoot));
	}

	return true;
}

bool FWorldBLDAssetStateStore::SaveProjectImportedPackageRoots(const TMap<FString, FString>& ImportedPackageRootsByAssetId)
{
	TSharedRef<FJsonObject> RootObject = MakeShared<FJsonObject>();
	TSharedRef<FJsonObject> ImportedMapObject = MakeShared<FJsonObject>();

	for (const TPair<FString, FString>& Pair : ImportedPackageRootsByAssetId)
	{
		if (Pair.Key.IsEmpty() || Pair.Value.IsEmpty())
		{
			continue;
		}

		ImportedMapObject->SetStringField(Pair.Key, Pair.Value);
	}

	RootObject->SetObjectField(ProjectImportedMapFieldName, ImportedMapObject);

	FString Content;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Content);
	if (!FJsonSerializer::Serialize(RootObject, Writer))
	{
		return false;
	}

	IFileManager::Get().MakeDirectory(*FPaths::GetPath(GetProjectImportedManifestPath()), true);
	return FFileHelper::SaveStringToFile(Content, *GetProjectImportedManifestPath());
}

