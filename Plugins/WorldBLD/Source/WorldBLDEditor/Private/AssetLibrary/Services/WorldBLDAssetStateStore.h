// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"

struct FWorldBLDAssetCacheManifest;
struct FWorldBLDAssetDownloadState;

class FWorldBLDAssetStateStore
{
public:
	static FString GetCacheDirectory();
	static FString GetManifestPath();
	static FString GetProjectImportedManifestPath();

	static bool LoadStates(TMap<FString, FWorldBLDAssetDownloadState>& OutStates);
	static bool SaveStates(const TMap<FString, FWorldBLDAssetDownloadState>& States);
	static bool LoadProjectImportedPackageRoots(TMap<FString, FString>& OutImportedPackageRootsByAssetId);
	static bool SaveProjectImportedPackageRoots(const TMap<FString, FString>& ImportedPackageRootsByAssetId);
};

