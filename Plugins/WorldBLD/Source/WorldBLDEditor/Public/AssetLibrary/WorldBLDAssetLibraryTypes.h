// Copyright WorldBLD LLC. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "WorldBLDAssetLibraryTypes.generated.h"

/**
 * Represents a single dependency in the asset manifest.
 * Each dependency has a unique ID, SHA1 hash, and metadata.
 */
USTRUCT(BlueprintType)
struct FWorldBLDAssetDependency
{
	GENERATED_BODY()

	/** Globally unique identifier for this dependency */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString UniqueID;

	/** Asset name (e.g., "M_MaterialRed") */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString AssetName;

	/** Asset type (e.g., "Materials", "Meshes", "Blueprints") */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString AssetType;

	/** Package path in Unreal (e.g., "/Game/WorldBLD/PreparedAssets/MyAsset/Materials/M_MaterialRed") */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString PackagePath;

	/** SHA1 hash of the asset file for integrity verification */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString SHA1Hash;

	/** File size in bytes */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int64 FileSize = 0;
};

/**
 * Asset manifest containing dependency information.
 * This is uploaded with the asset and used for dependency resolution.
 */
USTRUCT(BlueprintType)
struct FWorldBLDAssetManifest
{
	GENERATED_BODY()

	/** Unique ID of the root asset */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString RootAssetID;

	/** User-provided asset name */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString AssetName;

	/** Collection name this asset belongs to */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString CollectionName;

	/** All dependencies with their unique IDs and metadata */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDAssetDependency> Dependencies;
};

USTRUCT(BlueprintType)
struct FWorldBLDRequiredTool
{
	GENERATED_BODY()

	/** Backend tool id (string). In logs this is a Mongo ObjectId-like string. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ToolId;

	/** Minimum tool version required by the asset (semver-like string, e.g. "1.0.6"). */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString MinVersion;
};

USTRUCT(BlueprintType)
struct FWorldBLDMirrorDownloadFile
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Path;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString StorageKey;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString SignedURL;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString SHA256;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int64 Size = 0;
};

USTRUCT(BlueprintType)
struct FWorldBLDAssetInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ID;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Name;

	/** Asset author/publisher (API field: "author"). */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Author;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Description;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 CreditsPrice = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bIsFree = false;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Category;

	/** Collection names this asset belongs to (multi-collection). */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> CollectionNames;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> Tags;

	/** Human-readable feature list from the backend (API field: "features"). */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> Features;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ThumbnailURL;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> PreviewImages;

	/** Root asset ID from the manifest (for dependency tracking) */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString RootAssetID;

	/** Complete dependency manifest with unique IDs and SHA1 hashes */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FWorldBLDAssetManifest Manifest;

	/**
	 * Primary (core) assets for this library entry (backend field: primaryAssets[]).
	 * Typically object paths (e.g. "/Game/.../SM_Foo.SM_Foo") but may also be long package names.
	 */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> PrimaryAssets;

	/** File download URL from backend */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString DownloadURL;

	/** Delivery mode for this asset ("zip" legacy or "mirror"). */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString DeliveryMode;

	/** Stable mirror package slug. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString PackageId;

	/** Unreal object path for the primary mirrored asset. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString PrimaryAssetPath;

	/** All mirrored files this package references on the backend. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> MirroredFilePaths;

	/** Files owned directly by this package. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> OwnedFilePaths;

	/** Files shared with other packages. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> SharedFilePaths;

	/** Other mirrored package IDs that must be owned first. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> ExternalDependencyPackageIds;

	/** Referenced packages outside the mirrored library. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> ThirdPartyWarnings;

	/** Signed file list returned for mirror downloads. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDMirrorDownloadFile> MirrorDownloadFiles;

	/** Minimum tool requirements for this asset (API field: requiredTools). */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDRequiredTool> RequiredTools;

	/**
	 * Supported Unreal engine versions for this asset (API field: engineVersions), e.g. ["5.7","5.8"].
	 * Treated as a minimum floor: download/purchase is allowed when CurrentMajor.Minor >= min(list).
	 * Empty / missing means unrestricted (legacy assets).
	 */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> EngineVersions;

	bool IsMirrorAsset() const
	{
		return DeliveryMode.Equals(TEXT("mirror"), ESearchCase::IgnoreCase);
	}
};

/** Response for GET /api/assets/collection-names */
USTRUCT(BlueprintType)
struct FWorldBLDAssetCollectionNamesResponse
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bSuccess = false;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> CollectionNames;
};

USTRUCT(BlueprintType)
struct FWorldBLDKitInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ID;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString KitsName;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Description;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 Price = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bIsFree = false;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> Tags;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> PreviewImages;
};

USTRUCT(BlueprintType)
struct FWorldBLDAssetListResponse
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDAssetInfo> Data;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 CurrentPage = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 LastPage = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 PerPage = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 Total = 0;
};

USTRUCT(BlueprintType)
struct FWorldBLDKitListResponse
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDKitInfo> Data;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 CurrentPage = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 LastPage = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 PerPage = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 Total = 0;
};

USTRUCT(BlueprintType)
struct FWorldBLDFeaturedCollection
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Title;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Description;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDAssetInfo> FeaturedAssets;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDKitInfo> FeaturedKits;
};

/** Public collection/kit payload from GET /api/collections and GET /api/collections/{name}. */
USTRUCT(BlueprintType)
struct FWorldBLDCollectionInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ID;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString CollectionName;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString DisplayName;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Description;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Version;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ProductImageURL;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> Features;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> Tags;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> PreviewImages;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 AssetCount = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bIsFeatured = false;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bIsManaged = false;
};

/** Nested asset summary from GET /api/collections/{name} -> collection.assets[]. */
USTRUCT(BlueprintType)
struct FWorldBLDCollectionAsset
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ID;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Name;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString Description;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ThumbnailURL;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> Tags;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	int32 CreditsPrice = 0;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bIsFree = false;

	/**
	 * Whether this nested collection asset is publicly active (API field: status / isActive).
	 * Inactive / deactivated assets are not purchasable and should be omitted from kit counts.
	 * Defaults to true when the payload omits the field (legacy collection responses).
	 */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bIsActive = true;

	/**
	 * Supported Unreal engine versions for this asset (API field: engineVersions).
	 * Same minimum-floor rules as FWorldBLDAssetInfo::EngineVersions.
	 */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> EngineVersions;
};

USTRUCT(BlueprintType)
struct FWorldBLDCollectionListResponse
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bSuccess = false;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDCollectionInfo> Collections;
};

USTRUCT(BlueprintType)
struct FWorldBLDCollectionDetailResponse
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bSuccess = false;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FWorldBLDCollectionInfo Collection;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FWorldBLDCollectionAsset> Assets;
};

UENUM(BlueprintType)
enum class EWorldBLDAssetStatus : uint8
{
	NotOwned UMETA(DisplayName = "Not Owned"),
	Owned UMETA(DisplayName = "Owned"),
	Downloading UMETA(DisplayName = "Downloading"),
	Downloaded UMETA(DisplayName = "Downloaded"),
	Imported UMETA(DisplayName = "Imported")
};

USTRUCT(BlueprintType)
struct FWorldBLDAssetDownloadState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString AssetId;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString AssetName;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	EWorldBLDAssetStatus Status = EWorldBLDAssetStatus::NotOwned;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString CachedPath;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ImportedPath;

	/** Content Browser path that this asset was imported into, e.g. "/Game/WorldBLD/Assets/MyAsset_123". */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString ImportedPackageRoot;

	/** Cached path to the downloaded manifest json on disk (if present). */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString CachedManifestPath;

	/** Exact authored destination package root provided by the manifest (must be imported exactly). */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString AuthoredPackageRoot;

	/** Delivery mode persisted with the cached asset state. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString DeliveryMode;

	/** Stable mirror package slug for ownership/import checks. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString PackageId;

	/** Persisted authored primary asset path for mirrored packages. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FString PrimaryAssetPath;

	/** Mirror files downloaded into cache for this asset. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> CachedMirrorFilePaths;

	/** Mirror-owned file list returned by the backend. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> OwnedFilePaths;

	/** Mirror-shared file list returned by the backend. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> SharedFilePaths;

	/** Mirror dependency package IDs required by this asset. */
	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TArray<FString> ExternalDependencyPackageIds;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	FDateTime LastModified;

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	bool bIsKit = false;
};

USTRUCT(BlueprintType)
struct FWorldBLDAssetCacheManifest
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "WorldBLD|AssetLibrary")
	TMap<FString, FWorldBLDAssetDownloadState> AssetStates;
};
