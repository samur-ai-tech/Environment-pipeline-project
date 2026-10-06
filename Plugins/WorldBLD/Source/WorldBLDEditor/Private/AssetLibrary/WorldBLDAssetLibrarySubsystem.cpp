// Copyright WorldBLD LLC. All Rights Reserved.

#include "AssetLibrary/WorldBLDAssetLibrarySubsystem.h"
#include "Authorization/WorldBLDAuthSubsystem.h"
#include "AssetLibrary/WorldBLDAssetDownloadManager.h"
#include "AssetLibrary/WorldBLDAssetEngineVersionUtils.h"

#include "Editor.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "Misc/MessageDialog.h"

DEFINE_LOG_CATEGORY(LogWorldBLDAssetLibrary);

namespace
{
	FString ConvertRelativeURLToAbsolute_Local(const FString& RelativeURL)
	{
		if (RelativeURL.StartsWith(TEXT("http://")) || RelativeURL.StartsWith(TEXT("https://")))
		{
			return RelativeURL;
		}

		const FString BaseDomain = TEXT("https://worldbld.com");
		if (RelativeURL.StartsWith(TEXT("/")))
		{
			return BaseDomain + RelativeURL;
		}

		return BaseDomain + TEXT("/") + RelativeURL;
	}

	FString ReadStringFieldAny_Local(const TSharedPtr<FJsonObject>& Obj, std::initializer_list<const TCHAR*> Keys)
	{
		if (!Obj.IsValid())
		{
			return TEXT("");
		}

		for (const TCHAR* Key : Keys)
		{
			FString Out;
			if (Obj->TryGetStringField(Key, Out))
			{
				return Out;
			}
		}

		return TEXT("");
	}

	void ParseStringArrayField_Local(const TSharedPtr<FJsonObject>& Obj, std::initializer_list<const TCHAR*> Keys, TArray<FString>& OutValues)
	{
		OutValues.Reset();

		if (!Obj.IsValid())
		{
			return;
		}

		const TArray<TSharedPtr<FJsonValue>>* ArrayPtr = nullptr;
		for (const TCHAR* Key : Keys)
		{
			if (Obj->TryGetArrayField(Key, ArrayPtr) && ArrayPtr != nullptr)
			{
				break;
			}

			ArrayPtr = nullptr;
		}

		if (ArrayPtr == nullptr)
		{
			return;
		}

		for (const TSharedPtr<FJsonValue>& Value : *ArrayPtr)
		{
			if (!Value.IsValid())
			{
				continue;
			}

			FString TextValue;
			switch (Value->Type)
			{
			case EJson::String:
				TextValue = Value->AsString();
				break;
			case EJson::Number:
				TextValue = FString::SanitizeFloat(Value->AsNumber());
				break;
			case EJson::Boolean:
				TextValue = Value->AsBool() ? TEXT("true") : TEXT("false");
				break;
			default:
				break;
			}

			TextValue = TextValue.TrimStartAndEnd();
			if (!TextValue.IsEmpty())
			{
				OutValues.Add(TextValue);
			}
		}
	}

	void ParseMirrorDownloadFiles_Local(const TSharedPtr<FJsonObject>& Obj, TArray<FWorldBLDMirrorDownloadFile>& OutFiles)
	{
		OutFiles.Reset();

		if (!Obj.IsValid())
		{
			return;
		}

		const TArray<TSharedPtr<FJsonValue>>* FilesArrayPtr = nullptr;
		if (!Obj->TryGetArrayField(TEXT("files"), FilesArrayPtr) || FilesArrayPtr == nullptr)
		{
			return;
		}

		for (const TSharedPtr<FJsonValue>& FileValue : *FilesArrayPtr)
		{
			if (!FileValue.IsValid() || FileValue->Type != EJson::Object)
			{
				continue;
			}

			const TSharedPtr<FJsonObject> FileObj = FileValue->AsObject();
			if (!FileObj.IsValid())
			{
				continue;
			}

			FWorldBLDMirrorDownloadFile FileEntry;
			FileEntry.Path = ReadStringFieldAny_Local(FileObj, { TEXT("path") });
			FileEntry.StorageKey = ReadStringFieldAny_Local(FileObj, { TEXT("storage_key"), TEXT("storageKey") });
			FileEntry.SignedURL = ReadStringFieldAny_Local(FileObj, { TEXT("signed_url"), TEXT("signedUrl"), TEXT("url") });
			FileEntry.SHA256 = ReadStringFieldAny_Local(FileObj, { TEXT("sha256"), TEXT("sha") });

			double SizeNumber = 0.0;
			if (FileObj->TryGetNumberField(TEXT("size"), SizeNumber) || FileObj->TryGetNumberField(TEXT("file_size"), SizeNumber))
			{
				FileEntry.Size = static_cast<int64>(SizeNumber);
			}

			if (!FileEntry.Path.IsEmpty() && !FileEntry.SignedURL.IsEmpty())
			{
				OutFiles.Add(MoveTemp(FileEntry));
			}
		}
	}

	FString ParseProductImageUrl_Local(const TSharedPtr<FJsonObject>& Obj)
	{
		if (!Obj.IsValid())
		{
			return TEXT("");
		}

		const TSharedPtr<FJsonObject>* ProductImageObj = nullptr;
		if (Obj->TryGetObjectField(TEXT("productImage"), ProductImageObj) && ProductImageObj != nullptr && ProductImageObj->IsValid())
		{
			FString Url;
			if ((*ProductImageObj)->TryGetStringField(TEXT("url"), Url) && !Url.TrimStartAndEnd().IsEmpty())
			{
				return ConvertRelativeURLToAbsolute_Local(Url);
			}
		}

		FString Thumbnail;
		if (Obj->TryGetStringField(TEXT("thumbnail"), Thumbnail) && !Thumbnail.TrimStartAndEnd().IsEmpty())
		{
			return ConvertRelativeURLToAbsolute_Local(Thumbnail);
		}

		return TEXT("");
	}

	void ParseEngineVersions_Local(const TSharedPtr<FJsonObject>& Obj, TArray<FString>& OutVersions)
	{
		OutVersions.Reset();
		if (!Obj.IsValid())
		{
			return;
		}

		const TArray<TSharedPtr<FJsonValue>>* EngineVersionsArrayPtr = nullptr;
		if (!Obj->TryGetArrayField(TEXT("engineVersions"), EngineVersionsArrayPtr) || EngineVersionsArrayPtr == nullptr)
		{
			return;
		}

		for (const TSharedPtr<FJsonValue>& VersionValue : *EngineVersionsArrayPtr)
		{
			if (!VersionValue.IsValid() || VersionValue->Type != EJson::String)
			{
				continue;
			}

			const FString Trimmed = VersionValue->AsString().TrimStartAndEnd();
			if (!Trimmed.IsEmpty())
			{
				OutVersions.Add(Trimmed);
			}
		}
	}

	void ParsePreviewImageUrls_Local(const TSharedPtr<FJsonObject>& Obj, TArray<FString>& OutUrls)
	{
		OutUrls.Reset();
		if (!Obj.IsValid())
		{
			return;
		}

		const TArray<TSharedPtr<FJsonValue>>* PreviewArrayPtr = nullptr;
		if (!Obj->TryGetArrayField(TEXT("previewImages"), PreviewArrayPtr) || PreviewArrayPtr == nullptr)
		{
			(void)Obj->TryGetArrayField(TEXT("preview_images"), PreviewArrayPtr);
		}

		if (PreviewArrayPtr == nullptr)
		{
			return;
		}

		for (const TSharedPtr<FJsonValue>& PreviewValue : *PreviewArrayPtr)
		{
			if (!PreviewValue.IsValid() || PreviewValue->Type != EJson::String)
			{
				continue;
			}

			const FString Url = PreviewValue->AsString().TrimStartAndEnd();
			if (!Url.IsEmpty())
			{
				OutUrls.Add(ConvertRelativeURLToAbsolute_Local(Url));
			}
		}
	}

	bool ParseAssetIsActive_Local(const TSharedPtr<FJsonObject>& Obj)
	{
		if (!Obj.IsValid())
		{
			return true;
		}

		bool bExplicitActive = true;
		if (Obj->TryGetBoolField(TEXT("isActive"), bExplicitActive)
			|| Obj->TryGetBoolField(TEXT("is_active"), bExplicitActive))
		{
			return bExplicitActive;
		}

		const FString Status = ReadStringFieldAny_Local(Obj, { TEXT("status") });
		if (!Status.IsEmpty())
		{
			return Status.Equals(TEXT("active"), ESearchCase::IgnoreCase);
		}

		// Legacy collection payloads omit status because the endpoint already filtered to active assets.
		return true;
	}

	FWorldBLDCollectionAsset ParseCollectionAssetFromJson_Local(const TSharedPtr<FJsonObject>& AssetObject)
	{
		FWorldBLDCollectionAsset Asset;
		if (!AssetObject.IsValid())
		{
			return Asset;
		}

		Asset.ID = ReadStringFieldAny_Local(AssetObject, { TEXT("id"), TEXT("_id") });
		Asset.Name = ReadStringFieldAny_Local(AssetObject, { TEXT("name") });
		Asset.Description = ReadStringFieldAny_Local(AssetObject, { TEXT("description") });
		Asset.ThumbnailURL = ParseProductImageUrl_Local(AssetObject);
		Asset.CreditsPrice = AssetObject->HasTypedField<EJson::Number>(TEXT("creditsPrice")) ? AssetObject->GetIntegerField(TEXT("creditsPrice")) : 0;
		Asset.bIsFree = AssetObject->HasField(TEXT("isFree")) ? AssetObject->GetBoolField(TEXT("isFree")) : false;
		Asset.bIsActive = ParseAssetIsActive_Local(AssetObject);
		ParseStringArrayField_Local(AssetObject, { TEXT("tags") }, Asset.Tags);
		ParseEngineVersions_Local(AssetObject, Asset.EngineVersions);
		return Asset;
	}

	FWorldBLDCollectionInfo ParseCollectionInfoFromJson_Local(const TSharedPtr<FJsonObject>& CollectionObject)
	{
		FWorldBLDCollectionInfo Collection;
		if (!CollectionObject.IsValid())
		{
			return Collection;
		}

		Collection.ID = ReadStringFieldAny_Local(CollectionObject, { TEXT("id"), TEXT("_id") });
		Collection.CollectionName = ReadStringFieldAny_Local(CollectionObject, { TEXT("collectionName") });
		Collection.DisplayName = ReadStringFieldAny_Local(CollectionObject, { TEXT("displayName") });
		if (Collection.DisplayName.TrimStartAndEnd().IsEmpty())
		{
			Collection.DisplayName = Collection.CollectionName;
		}
		Collection.Description = ReadStringFieldAny_Local(CollectionObject, { TEXT("description") });
		Collection.Version = ReadStringFieldAny_Local(CollectionObject, { TEXT("version") });
		Collection.ProductImageURL = ParseProductImageUrl_Local(CollectionObject);
		Collection.bIsFeatured = CollectionObject->HasField(TEXT("isFeatured")) ? CollectionObject->GetBoolField(TEXT("isFeatured")) : false;
		Collection.bIsManaged = CollectionObject->HasField(TEXT("isManaged")) ? CollectionObject->GetBoolField(TEXT("isManaged")) : false;
		Collection.AssetCount = CollectionObject->HasTypedField<EJson::Number>(TEXT("assetCount")) ? CollectionObject->GetIntegerField(TEXT("assetCount")) : 0;
		ParseStringArrayField_Local(CollectionObject, { TEXT("features") }, Collection.Features);
		ParseStringArrayField_Local(CollectionObject, { TEXT("tags") }, Collection.Tags);
		ParsePreviewImageUrls_Local(CollectionObject, Collection.PreviewImages);
		return Collection;
	}

	bool ParseHttpJsonObject_Local(FHttpResponsePtr Response, bool bConnectedSuccessfully, TSharedPtr<FJsonObject>& OutJsonObject, FString& OutErrorMessage)
	{
		OutJsonObject.Reset();
		OutErrorMessage.Reset();

		if (!bConnectedSuccessfully || !Response.IsValid())
		{
			OutErrorMessage = TEXT("Connection failed");
			return false;
		}

		const FString ResponseContent = Response->GetContentAsString();
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
		if (!FJsonSerializer::Deserialize(Reader, OutJsonObject) || !OutJsonObject.IsValid())
		{
			OutErrorMessage = TEXT("Failed to parse response");
			return false;
		}

		const int32 ResponseCode = Response->GetResponseCode();
		if (ResponseCode != 200)
		{
			FString Message = OutJsonObject->HasField(TEXT("message")) ? OutJsonObject->GetStringField(TEXT("message")) : TEXT("Unknown error");
			if (Message.IsEmpty() && OutJsonObject->HasField(TEXT("error")))
			{
				Message = OutJsonObject->GetStringField(TEXT("error"));
			}
			OutErrorMessage = Message.IsEmpty() ? TEXT("Request failed") : Message;
			return false;
		}

		return true;
	}

	FWorldBLDAssetInfo ParseAssetInfoFromJson_Local(const TSharedPtr<FJsonObject>& AssetObject)
	{
		FWorldBLDAssetInfo Asset;
		if (!AssetObject.IsValid())
		{
			return Asset;
		}

		auto TryGetObjectFieldShared = [](const TSharedPtr<FJsonObject>& Obj, const TCHAR* FieldName, TSharedPtr<FJsonObject>& OutObject) -> bool
		{
			OutObject.Reset();
			if (!Obj.IsValid())
			{
				return false;
			}

			const TSharedPtr<FJsonObject>* OutPtr = nullptr;
			if (!Obj->TryGetObjectField(FStringView(FieldName), OutPtr) || OutPtr == nullptr || !OutPtr->IsValid())
			{
				return false;
			}

			OutObject = *OutPtr;
			return OutObject.IsValid();
		};

		Asset.ID = ReadStringFieldAny_Local(AssetObject, { TEXT("id"), TEXT("_id") });
		Asset.Name = ReadStringFieldAny_Local(AssetObject, { TEXT("name") });
		Asset.Author = ReadStringFieldAny_Local(AssetObject, { TEXT("author") });
		Asset.Description = ReadStringFieldAny_Local(AssetObject, { TEXT("description") });
		Asset.CreditsPrice = AssetObject->HasField(TEXT("creditsPrice")) ? AssetObject->GetIntegerField(TEXT("creditsPrice")) : 0;
		Asset.bIsFree = AssetObject->HasField(TEXT("isFree")) ? AssetObject->GetBoolField(TEXT("isFree")) : false;
		Asset.Category = ReadStringFieldAny_Local(AssetObject, { TEXT("category") });
		Asset.RootAssetID = ReadStringFieldAny_Local(AssetObject, { TEXT("rootAssetID"), TEXT("rootAssetId") });
		Asset.DownloadURL = ReadStringFieldAny_Local(AssetObject, { TEXT("downloadUrl") });
		Asset.DeliveryMode = ReadStringFieldAny_Local(AssetObject, { TEXT("deliveryMode"), TEXT("delivery_mode") });
		Asset.PackageId = ReadStringFieldAny_Local(AssetObject, { TEXT("packageId"), TEXT("package_id") });
		Asset.PrimaryAssetPath = ReadStringFieldAny_Local(AssetObject, { TEXT("primaryAssetPath"), TEXT("primary_asset_path") });

		if (AssetObject->HasField(TEXT("productImage")))
		{
			const TSharedPtr<FJsonObject> ProductImageObj = AssetObject->GetObjectField(TEXT("productImage"));
			if (ProductImageObj.IsValid() && ProductImageObj->HasField(TEXT("url")))
			{
				Asset.ThumbnailURL = ConvertRelativeURLToAbsolute_Local(ProductImageObj->GetStringField(TEXT("url")));
			}
		}
		else if (AssetObject->HasField(TEXT("thumbnail")))
		{
			Asset.ThumbnailURL = ConvertRelativeURLToAbsolute_Local(AssetObject->GetStringField(TEXT("thumbnail")));
		}

		ParseStringArrayField_Local(AssetObject, { TEXT("tags") }, Asset.Tags);
		ParseStringArrayField_Local(AssetObject, { TEXT("features") }, Asset.Features);
		ParseStringArrayField_Local(AssetObject, { TEXT("mirroredFilePaths"), TEXT("mirrored_file_paths") }, Asset.MirroredFilePaths);
		ParseStringArrayField_Local(AssetObject, { TEXT("ownedFilePaths"), TEXT("owned_file_paths") }, Asset.OwnedFilePaths);
		ParseStringArrayField_Local(AssetObject, { TEXT("sharedFilePaths"), TEXT("shared_file_paths") }, Asset.SharedFilePaths);
		ParseStringArrayField_Local(AssetObject, { TEXT("externalDependencyPackageIds"), TEXT("external_dependency_package_ids") }, Asset.ExternalDependencyPackageIds);
		ParseStringArrayField_Local(AssetObject, { TEXT("thirdPartyWarnings"), TEXT("third_party_warnings") }, Asset.ThirdPartyWarnings);

		{
			auto AddCollectionName = [&Asset](const FString& InName)
			{
				const FString Trimmed = InName.TrimStartAndEnd();
				if (!Trimmed.IsEmpty())
				{
					Asset.CollectionNames.AddUnique(Trimmed);
				}
			};

			const TArray<TSharedPtr<FJsonValue>>* CollectionsArrayPtr = nullptr;
			if (AssetObject->TryGetArrayField(TEXT("collectionNames"), CollectionsArrayPtr) && CollectionsArrayPtr != nullptr)
			{
				for (const TSharedPtr<FJsonValue>& CollectionValue : *CollectionsArrayPtr)
				{
					if (CollectionValue.IsValid() && CollectionValue->Type == EJson::String)
					{
						AddCollectionName(CollectionValue->AsString());
					}
				}
			}
			else if (AssetObject->HasField(TEXT("collectionName")))
			{
				AddCollectionName(AssetObject->GetStringField(TEXT("collectionName")));
			}
		}

		{
			const TArray<TSharedPtr<FJsonValue>>* PreviewArrayPtr = nullptr;
			if (!AssetObject->TryGetArrayField(TEXT("preview_images"), PreviewArrayPtr) || PreviewArrayPtr == nullptr)
			{
				(void)AssetObject->TryGetArrayField(TEXT("previewImages"), PreviewArrayPtr);
			}

			if (PreviewArrayPtr != nullptr)
			{
				for (const TSharedPtr<FJsonValue>& PreviewValue : *PreviewArrayPtr)
				{
					if (PreviewValue.IsValid() && PreviewValue->Type == EJson::String)
					{
						Asset.PreviewImages.Add(ConvertRelativeURLToAbsolute_Local(PreviewValue->AsString()));
					}
				}
			}
		}

		TSharedPtr<FJsonObject> ManifestObject;
		if (TryGetObjectFieldShared(AssetObject, TEXT("manifest"), ManifestObject))
		{
			Asset.Manifest.RootAssetID = ReadStringFieldAny_Local(ManifestObject, { TEXT("rootAssetID"), TEXT("rootAssetId") });
			Asset.Manifest.AssetName = ReadStringFieldAny_Local(ManifestObject, { TEXT("assetName"), TEXT("name") });
			Asset.Manifest.CollectionName = ReadStringFieldAny_Local(ManifestObject, { TEXT("collectionName"), TEXT("collection_name") });

			if (ManifestObject->HasField(TEXT("dependencies")))
			{
				const TArray<TSharedPtr<FJsonValue>>& DepsArray = ManifestObject->GetArrayField(TEXT("dependencies"));
				for (const TSharedPtr<FJsonValue>& DepValue : DepsArray)
				{
					if (DepValue.IsValid() && DepValue->Type == EJson::Object)
					{
						const TSharedPtr<FJsonObject> DepObject = DepValue->AsObject();
						if (!DepObject.IsValid())
						{
							continue;
						}

						FWorldBLDAssetDependency Dependency;
						Dependency.UniqueID = ReadStringFieldAny_Local(DepObject, { TEXT("uniqueID"), TEXT("uniqueId"), TEXT("id") });
						Dependency.AssetName = ReadStringFieldAny_Local(DepObject, { TEXT("assetName"), TEXT("name") });
						Dependency.AssetType = ReadStringFieldAny_Local(DepObject, { TEXT("assetType"), TEXT("type") });
						Dependency.PackagePath = ReadStringFieldAny_Local(DepObject, { TEXT("packagePath"), TEXT("package_path") });
						Dependency.SHA1Hash = ReadStringFieldAny_Local(DepObject, { TEXT("sha1Hash"), TEXT("sha1_hash"), TEXT("sha1") });
						Dependency.FileSize = DepObject->HasField(TEXT("fileSize")) ? static_cast<int64>(DepObject->GetNumberField(TEXT("fileSize"))) : 0;
						Asset.Manifest.Dependencies.Add(MoveTemp(Dependency));
					}
				}
			}
		}

		if (Asset.Manifest.CollectionName.IsEmpty())
		{
			Asset.Manifest.CollectionName = ReadStringFieldAny_Local(AssetObject, { TEXT("collectionName"), TEXT("collection_name") });
		}

		if (Asset.CollectionNames.IsEmpty() && !Asset.Manifest.CollectionName.IsEmpty())
		{
			Asset.CollectionNames.AddUnique(Asset.Manifest.CollectionName.TrimStartAndEnd());
		}

		{
			const TArray<TSharedPtr<FJsonValue>>* RequiredToolsArrayPtr = nullptr;
			if (AssetObject->TryGetArrayField(TEXT("requiredTools"), RequiredToolsArrayPtr) && RequiredToolsArrayPtr != nullptr)
			{
				for (const TSharedPtr<FJsonValue>& ToolValue : *RequiredToolsArrayPtr)
				{
					if (!ToolValue.IsValid() || ToolValue->Type != EJson::Object)
					{
						continue;
					}

					const TSharedPtr<FJsonObject> ToolObj = ToolValue->AsObject();
					if (!ToolObj.IsValid())
					{
						continue;
					}

					FWorldBLDRequiredTool Req;
					if (!ToolObj->TryGetStringField(TEXT("tool"), Req.ToolId))
					{
						ToolObj->TryGetStringField(TEXT("toolId"), Req.ToolId);
					}

					ToolObj->TryGetStringField(TEXT("minVersion"), Req.MinVersion);
					Req.ToolId = Req.ToolId.TrimStartAndEnd();
					Req.MinVersion = Req.MinVersion.TrimStartAndEnd();

					if (!Req.ToolId.IsEmpty())
					{
						Asset.RequiredTools.Add(MoveTemp(Req));
					}
				}
			}
		}

		{
			ParseEngineVersions_Local(AssetObject, Asset.EngineVersions);
		}

		{
			const TArray<TSharedPtr<FJsonValue>>* PrimaryAssetsArrayPtr = nullptr;
			if (!AssetObject->TryGetArrayField(TEXT("primaryAssets"), PrimaryAssetsArrayPtr) || PrimaryAssetsArrayPtr == nullptr)
			{
				(void)AssetObject->TryGetArrayField(TEXT("primary_assets"), PrimaryAssetsArrayPtr);
			}

			if (PrimaryAssetsArrayPtr != nullptr)
			{
				for (const TSharedPtr<FJsonValue>& Value : *PrimaryAssetsArrayPtr)
				{
					if (Value.IsValid() && Value->Type == EJson::String)
					{
						const FString Trimmed = Value->AsString().TrimStartAndEnd();
						if (!Trimmed.IsEmpty())
						{
							Asset.PrimaryAssets.Add(Trimmed);
						}
					}
				}
			}
		}

		ParseMirrorDownloadFiles_Local(AssetObject, Asset.MirrorDownloadFiles);
		return Asset;
	}
}

void UWorldBLDAssetLibrarySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (GEditor)
	{
		AuthSubsystem = GEditor->GetEditorSubsystem<UWorldBLDAuthSubsystem>();
	}

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("AssetLibrary subsystem initialized"));
}

void UWorldBLDAssetLibrarySubsystem::Deinitialize()
{
	AuthSubsystem = nullptr;
	Super::Deinitialize();
}

void UWorldBLDAssetLibrarySubsystem::FetchAssets(int32 Page, int32 PerPage, const FString& Category)
{
	if (GEditor)
	{
		if (UWorldBLDAssetDownloadManager* DownloadManager = GEditor->GetEditorSubsystem<UWorldBLDAssetDownloadManager>())
		{
			DownloadManager->RefreshOwnershipStatus();
		}
	}

	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	FString Url = FString::Printf(TEXT("%s/assets?page=%d&per_page=%d"), BaseURL, Page, PerPage);
	if (!Category.IsEmpty())
	{
		Url += FString::Printf(TEXT("&category=%s"), *Category);
	}

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(Url);
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH ASSETS REQUEST ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("URL: %s"), *Request->GetURL());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Method: %s"), *Request->GetVerb());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Content-Type: application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchAssetsResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::FetchKits(int32 Page, int32 PerPage)
{
	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	FString Url = FString::Printf(TEXT("%s/kits?page=%d&per_page=%d"), BaseURL, Page, PerPage);

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(Url);
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH KITS REQUEST ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("URL: %s"), *Request->GetURL());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Method: %s"), *Request->GetVerb());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Content-Type: application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchKitsResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::FetchAssetDetails(const FString& AssetID)
{
	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	FString Url = FString::Printf(TEXT("%s/assets/%s"), BaseURL, *AssetID);

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(Url);
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH ASSET DETAILS REQUEST ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("URL: %s"), *Request->GetURL());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Method: %s"), *Request->GetVerb());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Content-Type: application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchAssetDetailsResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::FetchKitDetails(const FString& KitID)
{
	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	FString Url = FString::Printf(TEXT("%s/kits/%s"), BaseURL, *KitID);

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(Url);
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH KIT DETAILS REQUEST ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("URL: %s"), *Request->GetURL());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Method: %s"), *Request->GetVerb());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Content-Type: application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchKitDetailsResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::PurchaseAsset(const FString& AssetId)
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[PurchaseAsset] Starting purchase for asset: %s"), *AssetId);
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[PurchaseAsset] AuthSubsystem pointer: %p"), AuthSubsystem.Get());

	FString Token = GetAuthToken();
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[PurchaseAsset] Token retrieved: %s"), Token.IsEmpty() ? TEXT("EMPTY") : *Token.Left(20));

	if (Token.IsEmpty())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[PurchaseAsset] Token is empty - not authenticated"));
		OnAPIError.Broadcast(TEXT("Looks like you're not logged in. Please log in to purchase this asset."));
		return;
	}

	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/assets/purchase"), BaseURL));
	Request->SetVerb(TEXT("POST"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	// Use standard Authorization header for Sanctum
	Request->SetHeader(TEXT("Authorization"), FString::Printf(TEXT("Bearer %s"), *Token));

	TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
	JsonObject->SetStringField(TEXT("asset_id"), AssetId);

	FString Content;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Content);
	FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
	Request->SetContentAsString(Content);

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== PURCHASE REQUEST ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("URL: %s"), *Request->GetURL());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Method: %s"), *Request->GetVerb());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Content-Type: application/json"));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Authorization: Bearer %s..."), *Token.Left(20));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Body: %s"), *Content);

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnPurchaseResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::FetchFreeAssets()
{
	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/assets/free"), BaseURL));
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH FREE ASSETS REQUEST ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("URL: %s"), *Request->GetURL());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Method: %s"), *Request->GetVerb());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Content-Type: application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchAssetsResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::FetchFreeKits()
{
	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/kits/free"), BaseURL));
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH FREE KITS REQUEST ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("URL: %s"), *Request->GetURL());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Method: %s"), *Request->GetVerb());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Content-Type: application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchKitsResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::RequestDownloadURL(const FString& AssetId, bool bIsKit)
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[RequestDownloadURL] Requesting download URL for asset: %s (IsKit: %s)"), *AssetId, bIsKit ? TEXT("true") : TEXT("false"));

	FString Token = GetAuthToken();
	if (Token.IsEmpty())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[RequestDownloadURL] Not authenticated"));
		OnAPIError.Broadcast(TEXT("Looks like you're not logged in. Please log in to download this asset."));
		return;
	}

	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	// Call backend endpoint: /api/downloads/asset/{id} or /api/downloads/kit/{id}
	// NOTE: Backend route requires POST request, not GET
	FString Endpoint = bIsKit ? TEXT("kit") : TEXT("asset");
	FString Url = FString::Printf(TEXT("%s/downloads/%s/%s"), BaseURL, *Endpoint, *AssetId);

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(Url);
	Request->SetVerb(TEXT("POST"));  // Backend route requires POST
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	Request->SetHeader(TEXT("Authorization"), FString::Printf(TEXT("Bearer %s"), *Token));

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== REQUEST DOWNLOAD URL ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("URL: %s"), *Request->GetURL());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Method: %s"), *Request->GetVerb());
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Header Authorization: Bearer %s..."), *Token.Left(20));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnRequestDownloadURLResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::FetchAssetCollectionNames()
{
	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/assets/collection-names"), BaseURL));
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchAssetCollectionNamesResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::FetchCollections()
{
	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/collections?managed_only=1"), BaseURL));
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchCollectionsResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::FetchCollectionDetails(const FString& CollectionName)
{
	const FString TrimmedName = CollectionName.TrimStartAndEnd();
	if (TrimmedName.IsEmpty())
	{
		OnAPIError.Broadcast(TEXT("Collection name is empty"));
		return;
	}

	FHttpModule* Http = &FHttpModule::Get();
	if (!Http)
	{
		OnAPIError.Broadcast(TEXT("HTTP Module unavailable"));
		return;
	}

	const FString EncodedName = FGenericPlatformHttp::UrlEncode(TrimmedName);
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = Http->CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/collections/%s"), BaseURL, *EncodedName));
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	Request->OnProcessRequestComplete().BindUObject(this, &UWorldBLDAssetLibrarySubsystem::OnFetchCollectionDetailsResponse);
	Request->ProcessRequest();
}

void UWorldBLDAssetLibrarySubsystem::OnFetchAssetsResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH ASSETS RESPONSE ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Connected: %s"), bConnectedSuccessfully ? TEXT("YES") : TEXT("NO"));

	if (!bConnectedSuccessfully || !Response.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Connection failed or invalid response"));
		OnAPIError.Broadcast(TEXT("Unstable connection, attempting to reconnect..."));
		return;
	}

	int32 ResponseCode = Response->GetResponseCode();
	FString ResponseContent = Response->GetContentAsString();

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Response Code: %d"), ResponseCode);

	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Failed to parse response"));
		OnAPIError.Broadcast(TEXT("Failed to parse response"));
		return;
	}

	if (ResponseCode != 200)
	{
		FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("Unknown error");
		if (Message.IsEmpty() && JsonObject->HasField(TEXT("error")))
		{
			Message = JsonObject->GetStringField(TEXT("error"));
		}
		OnAPIError.Broadcast(Message.IsEmpty() ? TEXT("Request failed") : Message);
		return;
	}

	if (!JsonObject->HasField(TEXT("data")))
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Response missing 'data' field"));
		OnAPIError.Broadcast(TEXT("Invalid response format"));
		return;
	}

	FWorldBLDAssetListResponse Parsed;

	const TArray<TSharedPtr<FJsonValue>>& DataArray = JsonObject->GetArrayField(TEXT("data"));
	for (const TSharedPtr<FJsonValue>& Value : DataArray)
	{
		if (!Value.IsValid() || Value->Type != EJson::Object)
		{
			continue;
		}

		TSharedPtr<FJsonObject> AssetObject = Value->AsObject();
		if (!AssetObject.IsValid())
		{
			continue;
		}

		Parsed.Data.Add(ParseAssetInfoFromJson_Local(AssetObject));
	}

	if (JsonObject->HasField(TEXT("meta")))
	{
		TSharedPtr<FJsonObject> MetaObject = JsonObject->GetObjectField(TEXT("meta"));
		if (MetaObject.IsValid())
		{
			Parsed.CurrentPage = MetaObject->HasField(TEXT("current_page")) ? MetaObject->GetIntegerField(TEXT("current_page")) : 0;
			Parsed.LastPage = MetaObject->HasField(TEXT("last_page")) ? MetaObject->GetIntegerField(TEXT("last_page")) : 0;
			Parsed.PerPage = MetaObject->HasField(TEXT("per_page")) ? MetaObject->GetIntegerField(TEXT("per_page")) : 0;
			Parsed.Total = MetaObject->HasField(TEXT("total")) ? MetaObject->GetIntegerField(TEXT("total")) : 0;
		}
	}

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Parsed %d assets"), Parsed.Data.Num());
	OnAssetsFetched.Broadcast(Parsed);
}

void UWorldBLDAssetLibrarySubsystem::OnFetchAssetCollectionNamesResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	(void)Request;

	if (!bConnectedSuccessfully || !Response.IsValid())
	{
		OnAPIError.Broadcast(TEXT("Connection failed"));
		return;
	}

	const int32 ResponseCode = Response->GetResponseCode();
	const FString ResponseContent = Response->GetContentAsString();

	TSharedPtr<FJsonObject> JsonObject;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		OnAPIError.Broadcast(TEXT("Failed to parse response"));
		return;
	}

	if (ResponseCode != 200)
	{
		FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("Unknown error");
		if (Message.IsEmpty() && JsonObject->HasField(TEXT("error")))
		{
			Message = JsonObject->GetStringField(TEXT("error"));
		}
		OnAPIError.Broadcast(Message.IsEmpty() ? TEXT("Request failed") : Message);
		return;
	}

	FWorldBLDAssetCollectionNamesResponse Parsed;
	Parsed.bSuccess = JsonObject->HasField(TEXT("success")) ? JsonObject->GetBoolField(TEXT("success")) : true;

	const TArray<TSharedPtr<FJsonValue>>* CollectionsArrayPtr = nullptr;
	if (JsonObject->TryGetArrayField(TEXT("collectionNames"), CollectionsArrayPtr) && CollectionsArrayPtr != nullptr)
	{
		for (const TSharedPtr<FJsonValue>& CollectionValue : *CollectionsArrayPtr)
		{
			if (CollectionValue.IsValid() && CollectionValue->Type == EJson::String)
			{
				const FString Trimmed = CollectionValue->AsString().TrimStartAndEnd();
				if (!Trimmed.IsEmpty())
				{
					Parsed.CollectionNames.AddUnique(Trimmed);
				}
			}
		}
	}

	OnAssetCollectionNamesFetched.Broadcast(Parsed);
}

void UWorldBLDAssetLibrarySubsystem::OnFetchCollectionsResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	(void)Request;

	TSharedPtr<FJsonObject> JsonObject;
	FString ErrorMessage;
	if (!ParseHttpJsonObject_Local(Response, bConnectedSuccessfully, JsonObject, ErrorMessage))
	{
		OnAPIError.Broadcast(ErrorMessage);
		return;
	}

	FWorldBLDCollectionListResponse Parsed;
	Parsed.bSuccess = JsonObject->HasField(TEXT("success")) ? JsonObject->GetBoolField(TEXT("success")) : true;

	const TArray<TSharedPtr<FJsonValue>>* CollectionsArrayPtr = nullptr;
	if (JsonObject->TryGetArrayField(TEXT("collections"), CollectionsArrayPtr) && CollectionsArrayPtr != nullptr)
	{
		for (const TSharedPtr<FJsonValue>& CollectionValue : *CollectionsArrayPtr)
		{
			if (!CollectionValue.IsValid() || CollectionValue->Type != EJson::Object)
			{
				continue;
			}

			const TSharedPtr<FJsonObject> CollectionObject = CollectionValue->AsObject();
			if (!CollectionObject.IsValid())
			{
				continue;
			}

			Parsed.Collections.Add(ParseCollectionInfoFromJson_Local(CollectionObject));
		}
	}

	OnCollectionsFetched.Broadcast(Parsed);
}

void UWorldBLDAssetLibrarySubsystem::OnFetchCollectionDetailsResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	(void)Request;

	TSharedPtr<FJsonObject> JsonObject;
	FString ErrorMessage;
	if (!ParseHttpJsonObject_Local(Response, bConnectedSuccessfully, JsonObject, ErrorMessage))
	{
		OnAPIError.Broadcast(ErrorMessage);
		return;
	}

	FWorldBLDCollectionDetailResponse Parsed;
	Parsed.bSuccess = JsonObject->HasField(TEXT("success")) ? JsonObject->GetBoolField(TEXT("success")) : true;

	const TSharedPtr<FJsonObject>* CollectionObjectPtr = nullptr;
	if (JsonObject->TryGetObjectField(TEXT("collection"), CollectionObjectPtr) && CollectionObjectPtr != nullptr && CollectionObjectPtr->IsValid())
	{
		Parsed.Collection = ParseCollectionInfoFromJson_Local(*CollectionObjectPtr);

		const TArray<TSharedPtr<FJsonValue>>* AssetsArrayPtr = nullptr;
		if ((*CollectionObjectPtr)->TryGetArrayField(TEXT("assets"), AssetsArrayPtr) && AssetsArrayPtr != nullptr)
		{
			for (const TSharedPtr<FJsonValue>& AssetValue : *AssetsArrayPtr)
			{
				if (!AssetValue.IsValid() || AssetValue->Type != EJson::Object)
				{
					continue;
				}

				const TSharedPtr<FJsonObject> AssetObject = AssetValue->AsObject();
				if (!AssetObject.IsValid())
				{
					continue;
				}

				Parsed.Assets.Add(ParseCollectionAssetFromJson_Local(AssetObject));
			}
		}

		int32 ActiveAssetCount = 0;
		for (const FWorldBLDCollectionAsset& Asset : Parsed.Assets)
		{
			if (Asset.bIsActive)
			{
				++ActiveAssetCount;
			}
		}

		Parsed.Collection.AssetCount = ActiveAssetCount;
	}

	OnCollectionDetailsFetched.Broadcast(Parsed);
}

void UWorldBLDAssetLibrarySubsystem::OnFetchKitsResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH KITS RESPONSE ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Connected: %s"), bConnectedSuccessfully ? TEXT("YES") : TEXT("NO"));

	if (!bConnectedSuccessfully || !Response.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Connection failed or invalid response"));
		OnAPIError.Broadcast(TEXT("Connection failed"));
		return;
	}

	int32 ResponseCode = Response->GetResponseCode();
	FString ResponseContent = Response->GetContentAsString();

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Response Code: %d"), ResponseCode);

	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Failed to parse response"));
		OnAPIError.Broadcast(TEXT("Failed to parse response"));
		return;
	}

	if (ResponseCode != 200)
	{
		FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("Unknown error");
		if (Message.IsEmpty() && JsonObject->HasField(TEXT("error")))
		{
			Message = JsonObject->GetStringField(TEXT("error"));
		}
		OnAPIError.Broadcast(Message.IsEmpty() ? TEXT("Request failed") : Message);
		return;
	}

	if (!JsonObject->HasField(TEXT("data")))
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Response missing 'data' field"));
		OnAPIError.Broadcast(TEXT("Invalid response format"));
		return;
	}

	FWorldBLDKitListResponse Parsed;

	const TArray<TSharedPtr<FJsonValue>>& DataArray = JsonObject->GetArrayField(TEXT("data"));
	for (const TSharedPtr<FJsonValue>& Value : DataArray)
	{
		if (!Value.IsValid() || Value->Type != EJson::Object)
		{
			continue;
		}

		TSharedPtr<FJsonObject> KitObject = Value->AsObject();
		if (!KitObject.IsValid())
		{
			continue;
		}

		FWorldBLDKitInfo Kit;
		Kit.ID = KitObject->HasField(TEXT("id")) ? KitObject->GetStringField(TEXT("id")) : TEXT("");
		Kit.KitsName = KitObject->HasField(TEXT("kitsName")) ? KitObject->GetStringField(TEXT("kitsName")) : TEXT("");
		Kit.Description = KitObject->HasField(TEXT("description")) ? KitObject->GetStringField(TEXT("description")) : TEXT("");
		Kit.Price = KitObject->HasField(TEXT("price")) ? KitObject->GetIntegerField(TEXT("price")) : 0;
		Kit.bIsFree = KitObject->HasField(TEXT("isFree")) ? KitObject->GetBoolField(TEXT("isFree")) : false;

		if (KitObject->HasField(TEXT("tags")))
		{
			const TArray<TSharedPtr<FJsonValue>>& TagsArray = KitObject->GetArrayField(TEXT("tags"));
			for (const TSharedPtr<FJsonValue>& TagValue : TagsArray)
			{
				if (TagValue.IsValid() && TagValue->Type == EJson::String)
				{
					Kit.Tags.Add(TagValue->AsString());
				}
			}
		}

		if (KitObject->HasField(TEXT("previewImages")))
		{
			const TArray<TSharedPtr<FJsonValue>>& PreviewArray = KitObject->GetArrayField(TEXT("previewImages"));
			for (const TSharedPtr<FJsonValue>& PreviewValue : PreviewArray)
			{
				if (PreviewValue.IsValid() && PreviewValue->Type == EJson::String)
				{
					Kit.PreviewImages.Add(PreviewValue->AsString());
				}
			}
		}

		Parsed.Data.Add(MoveTemp(Kit));
	}

	if (JsonObject->HasField(TEXT("meta")))
	{
		TSharedPtr<FJsonObject> MetaObject = JsonObject->GetObjectField(TEXT("meta"));
		if (MetaObject.IsValid())
		{
			Parsed.CurrentPage = MetaObject->HasField(TEXT("current_page")) ? MetaObject->GetIntegerField(TEXT("current_page")) : 0;
			Parsed.LastPage = MetaObject->HasField(TEXT("last_page")) ? MetaObject->GetIntegerField(TEXT("last_page")) : 0;
			Parsed.PerPage = MetaObject->HasField(TEXT("per_page")) ? MetaObject->GetIntegerField(TEXT("per_page")) : 0;
			Parsed.Total = MetaObject->HasField(TEXT("total")) ? MetaObject->GetIntegerField(TEXT("total")) : 0;
		}
	}

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Parsed %d kits"), Parsed.Data.Num());
	OnKitsFetched.Broadcast(Parsed);
}

void UWorldBLDAssetLibrarySubsystem::OnFetchAssetDetailsResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH ASSET DETAILS RESPONSE ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Connected: %s"), bConnectedSuccessfully ? TEXT("YES") : TEXT("NO"));

	if (!bConnectedSuccessfully || !Response.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Connection failed or invalid response"));
		OnAPIError.Broadcast(TEXT("Connection failed"));
		return;
	}

	int32 ResponseCode = Response->GetResponseCode();
	FString ResponseContent = Response->GetContentAsString();

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Response Code: %d"), ResponseCode);

	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Failed to parse response"));
		OnAPIError.Broadcast(TEXT("Failed to parse response"));
		return;
	}

	if (ResponseCode != 200)
	{
		FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("Unknown error");
		if (Message.IsEmpty() && JsonObject->HasField(TEXT("error")))
		{
			Message = JsonObject->GetStringField(TEXT("error"));
		}
		OnAPIError.Broadcast(Message.IsEmpty() ? TEXT("Request failed") : Message);
		return;
	}

	// Backend response has 'asset' field, not 'data'
	TSharedPtr<FJsonObject> AssetObject = JsonObject;
	if (JsonObject->HasField(TEXT("asset")))
	{
		TSharedPtr<FJsonObject> DataObject = JsonObject->GetObjectField(TEXT("asset"));
		if (DataObject.IsValid())
		{
			AssetObject = DataObject;
		}
	}
	else if (JsonObject->HasField(TEXT("data")))
	{
		TSharedPtr<FJsonObject> DataObject = JsonObject->GetObjectField(TEXT("data"));
		if (DataObject.IsValid())
		{
			AssetObject = DataObject;
		}
	}

	FWorldBLDAssetInfo Asset = ParseAssetInfoFromJson_Local(AssetObject);
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Asset download URL: %s"), *Asset.DownloadURL);
	if (!Asset.ThumbnailURL.IsEmpty())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Product image URL: %s"), *Asset.ThumbnailURL);
	}
	if (Asset.PreviewImages.Num() > 0)
	{
		UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Found %d preview images"), Asset.PreviewImages.Num());
		for (const FString& PreviewImage : Asset.PreviewImages)
		{
			UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Preview image: %s"), *PreviewImage);
		}
	}
	if (Asset.Manifest.Dependencies.Num() > 0)
	{
		UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Parsed %d dependencies total"), Asset.Manifest.Dependencies.Num());
	}

	OnAssetDetailsFetched.Broadcast(Asset);
}

void UWorldBLDAssetLibrarySubsystem::OnFetchKitDetailsResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== FETCH KIT DETAILS RESPONSE ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Connected: %s"), bConnectedSuccessfully ? TEXT("YES") : TEXT("NO"));

	if (!bConnectedSuccessfully || !Response.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Connection failed or invalid response"));
		OnAPIError.Broadcast(TEXT("Connection failed"));
		return;
	}

	int32 ResponseCode = Response->GetResponseCode();
	FString ResponseContent = Response->GetContentAsString();

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Response Code: %d"), ResponseCode);

	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Failed to parse response"));
		OnAPIError.Broadcast(TEXT("Failed to parse response"));
		return;
	}

	if (ResponseCode != 200)
	{
		FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("Unknown error");
		if (Message.IsEmpty() && JsonObject->HasField(TEXT("error")))
		{
			Message = JsonObject->GetStringField(TEXT("error"));
		}
		OnAPIError.Broadcast(Message.IsEmpty() ? TEXT("Request failed") : Message);
		return;
	}

	TSharedPtr<FJsonObject> KitObject = JsonObject;
	if (JsonObject->HasField(TEXT("data")))
	{
		TSharedPtr<FJsonObject> DataObject = JsonObject->GetObjectField(TEXT("data"));
		if (DataObject.IsValid())
		{
			KitObject = DataObject;
		}
	}

	FWorldBLDKitInfo Kit;
	Kit.ID = KitObject->HasField(TEXT("id")) ? KitObject->GetStringField(TEXT("id")) : TEXT("");
	Kit.KitsName = KitObject->HasField(TEXT("kitsName")) ? KitObject->GetStringField(TEXT("kitsName")) : TEXT("");
	Kit.Description = KitObject->HasField(TEXT("description")) ? KitObject->GetStringField(TEXT("description")) : TEXT("");
	Kit.Price = KitObject->HasField(TEXT("price")) ? KitObject->GetIntegerField(TEXT("price")) : 0;
	Kit.bIsFree = KitObject->HasField(TEXT("isFree")) ? KitObject->GetBoolField(TEXT("isFree")) : false;

	if (KitObject->HasField(TEXT("tags")))
	{
		const TArray<TSharedPtr<FJsonValue>>& TagsArray = KitObject->GetArrayField(TEXT("tags"));
		for (const TSharedPtr<FJsonValue>& TagValue : TagsArray)
		{
			if (TagValue.IsValid() && TagValue->Type == EJson::String)
			{
				Kit.Tags.Add(TagValue->AsString());
			}
		}
	}

	if (KitObject->HasField(TEXT("previewImages")))
	{
		const TArray<TSharedPtr<FJsonValue>>& PreviewArray = KitObject->GetArrayField(TEXT("previewImages"));
		for (const TSharedPtr<FJsonValue>& PreviewValue : PreviewArray)
		{
			if (PreviewValue.IsValid() && PreviewValue->Type == EJson::String)
			{
				Kit.PreviewImages.Add(PreviewValue->AsString());
			}
		}
	}

	OnKitDetailsFetched.Broadcast(Kit);
}

void UWorldBLDAssetLibrarySubsystem::OnPurchaseResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== PURCHASE RESPONSE ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Connected: %s"), bConnectedSuccessfully ? TEXT("YES") : TEXT("NO"));

	if (!bConnectedSuccessfully || !Response.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Connection failed or invalid response"));
		OnAPIError.Broadcast(TEXT("Connection failed"));
		return;
	}

	int32 ResponseCode = Response->GetResponseCode();
	FString ResponseContent = Response->GetContentAsString();

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Response Code: %d"), ResponseCode);

	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Failed to parse response"));
		OnAPIError.Broadcast(TEXT("Failed to parse response"));
		return;
	}

	if (ResponseCode == 200)
	{
		const bool bSuccess = JsonObject->HasField(TEXT("success")) ? JsonObject->GetBoolField(TEXT("success")) : true;

		// Refresh ownership state immediately so the UI updates without requiring the asset library window to be reopened.
		// (FetchAssets() already does this on open; purchasing previously did not.)
		if (bSuccess && GEditor)
		{
			if (UWorldBLDAssetDownloadManager* DownloadManager = GEditor->GetEditorSubsystem<UWorldBLDAssetDownloadManager>())
			{
				DownloadManager->RefreshOwnershipStatus();
			}
		}

		// IMPORTANT:
		// The details panel updates the displayed credits by calling AuthSubsystem->SetCachedUserCredits(RemainingCredits)
		// when a purchase succeeds. If we incorrectly parse RemainingCredits as 0 (e.g., wrong JSON field),
		// the UI will temporarily show 0 and block further purchases until ValidateSession runs again.
		auto TryParseCreditsFromObject = [](const TSharedPtr<FJsonObject>& Obj, int32& OutCredits) -> bool
		{
			if (!Obj.IsValid())
			{
				return false;
			}

			auto TryNum = [&OutCredits, &Obj](const TCHAR* Key) -> bool
			{
				if (Obj->HasTypedField<EJson::Number>(Key))
				{
					OutCredits = Obj->GetIntegerField(Key);
					return true;
				}
				return false;
			};

			// Common formats across endpoints (session uses user.credits; purchase may vary).
			return TryNum(TEXT("credits"))
				|| TryNum(TEXT("userCredits"))
				|| TryNum(TEXT("remainingCredits"))
				|| TryNum(TEXT("remaining_credits"));
		};

		// IMPORTANT:
		// RemainingCredits is forwarded to Slate and used to update the cached user credits displayed in the UI.
		// Some purchase responses don't include credits at all (or include them in an unexpected format). In those cases,
		// we must NOT forward 0, because the details panel will treat that as a real value and overwrite the cache,
		// causing the "Your Credits" display to reset to 0 until session validation completes.
		int32 Credits = INDEX_NONE; // sentinel = unknown/unprovided
		bool bHasCredits = TryParseCreditsFromObject(JsonObject, Credits);

		// Nested formats: { user: { credits: ... } } or { data: { credits: ... } } or { data: { user: { credits: ... } } }
		if (!bHasCredits && JsonObject->HasTypedField<EJson::Object>(TEXT("user")))
		{
			bHasCredits = TryParseCreditsFromObject(JsonObject->GetObjectField(TEXT("user")), Credits);
		}

		if (!bHasCredits && JsonObject->HasTypedField<EJson::Object>(TEXT("data")))
		{
			const TSharedPtr<FJsonObject> DataObject = JsonObject->GetObjectField(TEXT("data"));
			bHasCredits = TryParseCreditsFromObject(DataObject, Credits);
			if (!bHasCredits && DataObject.IsValid() && DataObject->HasTypedField<EJson::Object>(TEXT("user")))
			{
				bHasCredits = TryParseCreditsFromObject(DataObject->GetObjectField(TEXT("user")), Credits);
			}
		}

		// If the response doesn't include credits at all, don't clobber the cached value.
		// Opportunistically re-validate in the background and forward INDEX_NONE to indicate "unknown".
		if (!bHasCredits)
		{
			if (UWorldBLDAuthSubsystem* AuthSubsystemPtr = AuthSubsystem.Get())
			{
				AuthSubsystemPtr->ValidateSession();
			}
			Credits = INDEX_NONE;
		}
		else
		{
			Credits = FMath::Max(0, Credits);
		}

		OnPurchaseComplete.Broadcast(bSuccess, Credits);
		return;
	}

	if (ResponseCode == 401)
	{
		OnAPIError.Broadcast(TEXT("Unauthorized - please re-login"));
		return;
	}

	if (ResponseCode == 404)
	{
		OnAPIError.Broadcast(TEXT("Item not found"));
		return;
	}

	if (ResponseCode == 500)
	{
		OnAPIError.Broadcast(TEXT("Purchase failed"));
		return;
	}

	if (ResponseCode == 400)
	{
		FString Error = JsonObject->HasField(TEXT("error")) ? JsonObject->GetStringField(TEXT("error")) : TEXT("");
		FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("");

		// Special handling for "already-owned" - refresh ownership status
		if (Error == TEXT("already-owned"))
		{
			UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[OnPurchaseResponse] Asset already owned"));

			if (GEditor)
			{
				if (UWorldBLDAssetDownloadManager* DownloadManager = GEditor->GetEditorSubsystem<UWorldBLDAssetDownloadManager>())
				{
					DownloadManager->RefreshOwnershipStatus();
				}
			}

			// Broadcast error message to user
			OnAPIError.Broadcast(Message.IsEmpty() ? TEXT("You already own this asset") : Message);
			return;
		}

		FString Combined = !Error.IsEmpty() ? Error : Message;
		OnAPIError.Broadcast(Combined.IsEmpty() ? TEXT("Purchase request failed") : Combined);
		return;
	}

	FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("Purchase request failed");
	OnAPIError.Broadcast(Message.IsEmpty() ? TEXT("Purchase request failed") : Message);
}

FString UWorldBLDAssetLibrarySubsystem::GetAuthToken() const
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[GetAuthToken] AuthSubsystem pointer: %p"), AuthSubsystem.Get());

	// If AuthSubsystem is null, try to fetch it (this shouldn't happen, but let's be defensive)
	UWorldBLDAuthSubsystem* AuthSubsystemPtr = AuthSubsystem.Get();
	if (!AuthSubsystemPtr && GEditor)
	{
		UE_LOG(LogWorldBLDAssetLibrary, Warning, TEXT("[GetAuthToken] AuthSubsystem is null, attempting to fetch it..."));
		AuthSubsystemPtr = GEditor->GetEditorSubsystem<UWorldBLDAuthSubsystem>();
		if (AuthSubsystemPtr)
		{
			UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[GetAuthToken] Successfully fetched AuthSubsystem on-demand"));
		}
	}

	if (!AuthSubsystemPtr)
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[GetAuthToken] AuthSubsystem is null and couldn't be fetched!"));
		return TEXT("");
	}

	FString Token = AuthSubsystemPtr->GetSessionToken();
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[GetAuthToken] Token from AuthSubsystem: %s"), Token.IsEmpty() ? TEXT("EMPTY") : *Token.Left(20));
	return Token;
}

FString UWorldBLDAssetLibrarySubsystem::ConvertRelativeURLToAbsolute(const FString& RelativeURL) const
{
	// If URL is already absolute (starts with http:// or https://), return as-is
	if (RelativeURL.StartsWith(TEXT("http://")) || RelativeURL.StartsWith(TEXT("https://")))
	{
		return RelativeURL;
	}

	// Convert relative URL to absolute by prepending base domain
	// BaseURL is "https://worldbld.com/api", we need just "https://worldbld.com"
	FString BaseDomain = TEXT("https://worldbld.com");

	// Remove leading slash if present (e.g., "/storage/..." -> "storage/...")
	FString CleanRelativeURL = RelativeURL;
	if (CleanRelativeURL.StartsWith(TEXT("/")))
	{
		// Keep the leading slash for absolute paths
		return BaseDomain + CleanRelativeURL;
	}

	return BaseDomain + TEXT("/") + CleanRelativeURL;
}

void UWorldBLDAssetLibrarySubsystem::OnRequestDownloadURLResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("=== REQUEST DOWNLOAD URL RESPONSE ==="));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Connected: %s"), bConnectedSuccessfully ? TEXT("YES") : TEXT("NO"));

	if (!bConnectedSuccessfully || !Response.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Connection failed or invalid response"));
		OnAPIError.Broadcast(TEXT("Connection failed"));
		return;
	}

	int32 ResponseCode = Response->GetResponseCode();
	FString ResponseContent = Response->GetContentAsString();

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("Response Code: %d"), ResponseCode);

	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Failed to parse response"));
		OnAPIError.Broadcast(TEXT("Failed to parse response"));
		return;
	}

	if (ResponseCode != 200)
	{
		FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("Unknown error");
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Request failed: %s"), *Message);
		OnAPIError.Broadcast(Message);
		return;
	}

	// Check if response is successful
	bool bSuccess = JsonObject->HasField(TEXT("success")) ? JsonObject->GetBoolField(TEXT("success")) : false;
	if (!bSuccess)
	{
		FString Message = JsonObject->HasField(TEXT("message")) ? JsonObject->GetStringField(TEXT("message")) : TEXT("Download URL request failed");
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Download URL request failed: %s"), *Message);
		OnAPIError.Broadcast(Message);
		return;
	}

	// Extract asset/kit ID from the request URL
	FString RequestURL = Request->GetURL();
	FString AssetId;

	// Parse asset ID from URL: https://worldbld.com/api/downloads/asset/{id}
	int32 LastSlashIndex;
	if (RequestURL.FindLastChar('/', LastSlashIndex))
	{
		AssetId = RequestURL.RightChop(LastSlashIndex + 1);
	}

	bool bIsKit = RequestURL.Contains(TEXT("/kit/"));

	const FString DeliveryMode = ReadStringFieldAny_Local(JsonObject, { TEXT("deliveryMode"), TEXT("delivery_mode") });
	if (DeliveryMode.Equals(TEXT("mirror"), ESearchCase::IgnoreCase))
	{
		FWorldBLDAssetInfo MirrorAsset = ParseAssetInfoFromJson_Local(JsonObject);
		if (MirrorAsset.ID.IsEmpty())
		{
			MirrorAsset.ID = AssetId;
		}

		if (MirrorAsset.Name.IsEmpty())
		{
			MirrorAsset.Name = ReadStringFieldAny_Local(JsonObject, { TEXT("asset_name"), TEXT("name") });
		}

		if (MirrorAsset.MirrorDownloadFiles.Num() == 0)
		{
			UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Mirror response missing downloadable file list"));
			OnAPIError.Broadcast(TEXT("Mirror download payload was incomplete"));
			return;
		}

		if (!WorldBLDAssetEngineVersionUtils::IsEngineVersionCompatible(MirrorAsset.EngineVersions))
		{
			const FString Message = WorldBLDAssetEngineVersionUtils::MakeIncompatibleEngineMessage(MirrorAsset.EngineVersions);
			UE_LOG(LogWorldBLDAssetLibrary, Warning, TEXT("[OnRequestDownloadURLResponse] Engine version guard blocked mirror download for asset %s: %s"), *MirrorAsset.ID, *Message);
			FMessageDialog::Open(EAppMsgType::Ok, FText::FromString(Message));
			OnAPIError.Broadcast(Message);
			return;
		}

		if (GEditor)
		{
			if (UWorldBLDAssetDownloadManager* DownloadManager = GEditor->GetEditorSubsystem<UWorldBLDAssetDownloadManager>())
			{
				FDOnDownloadProgress Progress;
				FDOnComplete Complete;
				DownloadManager->DownloadMirroredAsset(MirrorAsset, Progress, Complete);
				UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[OnRequestDownloadURLResponse] Mirror download started for asset: %s"), *MirrorAsset.ID);
				return;
			}
		}

		OnAPIError.Broadcast(TEXT("Failed to start mirror download"));
		return;
	}

	// Extract download URL from response
	FString DownloadURL = JsonObject->HasField(TEXT("download_url")) ? JsonObject->GetStringField(TEXT("download_url")) : TEXT("");
	if (DownloadURL.IsEmpty())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("Download URL is empty in response"));
		OnAPIError.Broadcast(TEXT("Download URL not provided"));
		return;
	}

	// Defense-in-depth: zip responses may include engineVersions; when present, enforce the floor.
	{
		TArray<FString> EngineVersions;
		const TArray<TSharedPtr<FJsonValue>>* EngineVersionsArrayPtr = nullptr;
		if (JsonObject->TryGetArrayField(TEXT("engineVersions"), EngineVersionsArrayPtr) && EngineVersionsArrayPtr != nullptr)
		{
			for (const TSharedPtr<FJsonValue>& VersionValue : *EngineVersionsArrayPtr)
			{
				if (VersionValue.IsValid() && VersionValue->Type == EJson::String)
				{
					const FString Trimmed = VersionValue->AsString().TrimStartAndEnd();
					if (!Trimmed.IsEmpty())
					{
						EngineVersions.Add(Trimmed);
					}
				}
			}
		}

		if (!WorldBLDAssetEngineVersionUtils::IsEngineVersionCompatible(EngineVersions))
		{
			const FString Message = WorldBLDAssetEngineVersionUtils::MakeIncompatibleEngineMessage(EngineVersions);
			UE_LOG(LogWorldBLDAssetLibrary, Warning, TEXT("[OnRequestDownloadURLResponse] Engine version guard blocked zip download for asset %s: %s"), *AssetId, *Message);
			FMessageDialog::Open(EAppMsgType::Ok, FText::FromString(Message));
			OnAPIError.Broadcast(Message);
			return;
		}
	}

	// Extract asset name from response
	FString AssetName = JsonObject->HasField(TEXT("asset_name")) ? JsonObject->GetStringField(TEXT("asset_name")) : TEXT("");

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[OnRequestDownloadURLResponse] Received download URL for asset: %s (Name: %s)"), *AssetId, *AssetName);
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[OnRequestDownloadURLResponse] Download URL: %s"), *DownloadURL);

	// Start the download using the download manager
	if (GEditor)
	{
		if (UWorldBLDAssetDownloadManager* DownloadManager = GEditor->GetEditorSubsystem<UWorldBLDAssetDownloadManager>())
		{
			FDOnDownloadProgress Progress;
			FDOnComplete Complete;

			DownloadManager->DownloadAsset(AssetId, AssetName, DownloadURL, bIsKit, Progress, Complete);
			UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[OnRequestDownloadURLResponse] Download started for asset: %s"), *AssetId);
		}
		else
		{
			UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[OnRequestDownloadURLResponse] Failed to get DownloadManager"));
			OnAPIError.Broadcast(TEXT("Failed to start download"));
		}
	}
}
