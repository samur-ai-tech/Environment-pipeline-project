// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDEditorUtilityLibrary.h"

#include "AssetSelection.h"
#include "Containers/ArrayView.h"
#include "Editor.h"
#include "Elements/Framework/TypedElementRegistry.h"
#include "Elements/Interfaces/TypedElementObjectInterface.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Framework/Application/SlateApplication.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "Landscape.h"
#include "LandscapeEdit.h"
#include "LandscapeEditLayer.h"
#include "LandscapeImportHelper.h"
#include "LandscapeInfo.h"
#include "LandscapeLayerInfoObject.h"
#include "LandscapeProxy.h"
#include "LandscapeUtils.h"
#include "LandscapePaint/SWorldBLDLandscapePaintDialog.h"
#include "LandscapePaint/SWorldBLDLandscapePopulateDialog.h"
#include "LandscapePaint/WorldBLDLandscapePaintImportOptions.h"
#include "LandscapePaint/WorldBLDLandscapePopulateOptions.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "ObjectTools.h"
#include "ScopedTransaction.h"
#include "ISettingsModule.h"
#include "Modules/ModuleManager.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"
#include "Widgets/SWindow.h"

#include "ActorFactories/ActorFactory.h"
#include "Builders/CubeBuilder.h"
#include "PCGGraph.h"
#include "PCGComponent.h"
#include "PCGVolume.h"
#include "PCGWorldActor.h"
#include "Grid/PCGLandscapeCache.h"
#include "Helpers/PCGBlueprintHelpers.h"
#include "Subsystems/PCGSubsystem.h"

#include "WorldBLDLandscapePreset.h"
#include "WorldBLDRuntimeUtilsLibrary.h"
#include "WorldBLDRuntimeSettings.h"

namespace
{
	static void ApplyLandscapeMaterial(ALandscape* Landscape, UMaterialInterface* Material)
	{
		if (!IsValid(Landscape) || Material == nullptr)
		{
			return;
		}

		Landscape->LandscapeMaterial = Material;

		FProperty* Property = FindFProperty<FProperty>(ALandscapeProxy::StaticClass(), TEXT("LandscapeMaterial"));
		if (Property != nullptr)
		{
			FPropertyChangedEvent PropertyChangedEvent(Property);
			Landscape->PostEditChangeProperty(PropertyChangedEvent);
		}
		else
		{
			Landscape->PostEditChange();
		}
	}

	static void AssignLandscapePresetToPCGVolume(
		APCGVolume* PCGVolume,
		UWorldBLDLandscapePreset* Preset,
		const TCHAR* VolumeKindLabel)
	{
		if (!IsValid(PCGVolume) || !IsValid(Preset))
		{
			return;
		}

		UPCGComponent* PCGComponent = PCGVolume->GetComponentByClass<UPCGComponent>();
		UPCGGraphInstance* GraphInstance = IsValid(PCGComponent) ? PCGComponent->GetGraphInstance() : nullptr;
		if (GraphInstance == nullptr)
		{
			UE_LOG(LogWorldBLD, Warning,
				TEXT("[PopulateTargetLandscape] %s PCG volume '%s' has no graph instance; cannot set Preset parameter."),
				VolumeKindLabel,
				*GetNameSafe(PCGVolume));
			return;
		}

		// SetGraphParameter's UObject specialization requires an exact UObject* type deduction.
		UObject* PresetObject = Preset;
		const EPropertyBagResult SetPresetResult = GraphInstance->SetGraphParameter(
			FName(TEXT("Preset")),
			PresetObject);
		if (SetPresetResult != EPropertyBagResult::Success)
		{
			UE_LOG(LogWorldBLD, Warning,
				TEXT("[PopulateTargetLandscape] Failed to set %s PCG 'Preset' graph parameter on '%s' (result=%d)."),
				VolumeKindLabel,
				*GetNameSafe(PCGVolume),
				static_cast<int32>(SetPresetResult));
		}
	}

	static bool SaveLandscapeLayerInfoPackage(ULandscapeLayerInfoObject* LayerInfo)
	{
		if (!IsValid(LayerInfo))
		{
			return false;
		}

		UPackage* Package = LayerInfo->GetOutermost();
		if (Package == nullptr)
		{
			return false;
		}

		FString PackageFilename;
		if (!FPackageName::TryConvertLongPackageNameToFilename(
				Package->GetName(),
				PackageFilename,
				FPackageName::GetAssetPackageExtension()))
		{
			UE_LOG(LogWorldBLD, Warning,
				TEXT("[PaintTargetLandscape] Could not map LayerInfo package '%s' to a filename."),
				*Package->GetName());
			return false;
		}

		FSavePackageArgs SaveArgs;
		SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
		SaveArgs.SaveFlags = SAVE_NoError;
		if (!UPackage::SavePackage(Package, LayerInfo, *PackageFilename, SaveArgs))
		{
			UE_LOG(LogWorldBLD, Warning,
				TEXT("[PaintTargetLandscape] Failed to save LayerInfo package '%s'."),
				*Package->GetName());
			return false;
		}

		return true;
	}

	/** Commits target-layer registration so weightmaps / LayerInfo refs survive save + editor restart. */
	static void FinalizeLandscapeLayerRegistration(ALandscape* Landscape)
	{
		if (!IsValid(Landscape))
		{
			return;
		}

		ULandscapeInfo* LandscapeInfo = Landscape->GetLandscapeInfo();
		if (LandscapeInfo == nullptr)
		{
			return;
		}

		LandscapeInfo->UpdateLayerInfoMap();
		LandscapeInfo->ForceLayersFullUpdate();
		Landscape->RequestLayersContentUpdateForceAll();
		Landscape->PostEditChange();
		Landscape->MarkPackageDirty();

		LandscapeInfo->ForEachLandscapeProxy([](ALandscapeProxy* Proxy) -> bool
		{
			if (IsValid(Proxy))
			{
				Proxy->MarkPackageDirty();
			}
			return true;
		});

		if (GEditor != nullptr)
		{
			GEditor->RedrawLevelEditingViewports(true);
		}
	}

	// Keep in sync with Plugins/TwinBLD/Source/TwinBLDEditor/Private/LandscapeManager.cpp
	// and Plugins/RoadBLD/Source/RoadBLDRuntime/Private/DynamicRoad/Rebuild/RebuildCommitter_LandscapePaint.cpp.
	//
	// Resolution order: (a) layer info already registered on the landscape, if valid and not under /Temp
	//                   (b) WorldBLD shipped set: /WorldBLD/Maps/LandscapeLayerInfos/<Layer>_LayerInfo
	//                   (c) <persistent folder>/<Layer>_LayerInfo
	//                   (d) create in <persistent folder> (only if creation is allowed); caller saves it
	static constexpr const TCHAR* WorldBLDShippedLayerInfoFolder = TEXT("/WorldBLD/Maps/LandscapeLayerInfos");

	static bool IsTempOrMemoryPackageName(const FString& PackageName)
	{
		return FPackageName::IsTempPackage(PackageName) || FPackageName::IsMemoryPackage(PackageName);
	}

	static bool IsLayerInfoUnderTemp(const ULandscapeLayerInfoObject* LayerInfo)
	{
		const UPackage* Package = IsValid(LayerInfo) ? LayerInfo->GetOutermost() : nullptr;
		return Package != nullptr && FPackageName::IsTempPackage(Package->GetName());
	}

	static FString GetPersistentLayerInfoFolder(const ALandscape* Landscape, const TCHAR* Fallback)
	{
		const ULevel* Level = IsValid(Landscape) ? Landscape->GetLevel() : nullptr;
		const UPackage* LevelPackage = Level != nullptr ? Level->GetOutermost() : nullptr;
		if (LevelPackage != nullptr && !IsTempOrMemoryPackageName(LevelPackage->GetName()))
		{
			return FPackageName::GetLongPackagePath(LevelPackage->GetName()) / TEXT("LandscapeLayerInfos");
		}

		return Fallback != nullptr ? FString(Fallback) : FString();
	}

	static ULandscapeLayerInfoObject* FindLayerInfoByName(const FName LayerName, const FString& Folder)
	{
		if (LayerName.IsNone() || Folder.IsEmpty())
		{
			return nullptr;
		}

		const FString Sanitized = ObjectTools::SanitizeInvalidChars(LayerName.ToString(), INVALID_LONGPACKAGE_CHARACTERS);
		const FString AssetName = Sanitized + TEXT("_LayerInfo");
		const FString PackageName = Folder / AssetName;
		const FString ObjectPath = PackageName + TEXT(".") + AssetName;

		ULandscapeLayerInfoObject* LayerInfo = nullptr;
		if (UPackage* Package = FindPackage(nullptr, *PackageName))
		{
			LayerInfo = FindObject<ULandscapeLayerInfoObject>(Package, *AssetName);
		}
		if (!IsValid(LayerInfo))
		{
			LayerInfo = FindObject<ULandscapeLayerInfoObject>(nullptr, *ObjectPath);
		}
		if (!IsValid(LayerInfo) && FPackageName::DoesPackageExist(PackageName))
		{
			LayerInfo = LoadObject<ULandscapeLayerInfoObject>(nullptr, *ObjectPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
		}

		if (IsValid(LayerInfo) && LayerInfo->GetLayerName() == LayerName)
		{
			return LayerInfo;
		}
		return nullptr;
	}

	struct FResolvedLandscapeLayerInfo
	{
		ULandscapeLayerInfoObject* LayerInfo = nullptr;
		bool bCreated = false;
	};

	static FResolvedLandscapeLayerInfo ResolveLandscapeLayerInfo(
		ALandscape* Landscape,
		const FName LayerName,
		const TCHAR* FallbackFolder,
		const bool bAllowCreate)
	{
		FResolvedLandscapeLayerInfo Resolved;
		if (!IsValid(Landscape) || LayerName.IsNone())
		{
			return Resolved;
		}

		if (const FLandscapeTargetLayerSettings* Existing = Landscape->GetTargetLayers().Find(LayerName))
		{
			ULandscapeLayerInfoObject* ExistingInfo = Existing->LayerInfoObj.Get();
			if (IsValid(ExistingInfo) && !IsLayerInfoUnderTemp(ExistingInfo))
			{
				Resolved.LayerInfo = ExistingInfo;
				return Resolved;
			}
		}

		Resolved.LayerInfo = FindLayerInfoByName(LayerName, WorldBLDShippedLayerInfoFolder);
		if (IsValid(Resolved.LayerInfo))
		{
			return Resolved;
		}

		const FString PersistentFolder = GetPersistentLayerInfoFolder(Landscape, FallbackFolder);
		Resolved.LayerInfo = FindLayerInfoByName(LayerName, PersistentFolder);
		if (IsValid(Resolved.LayerInfo) || !bAllowCreate)
		{
			return Resolved;
		}

		Resolved.LayerInfo = UE::Landscape::CreateTargetLayerInfo(LayerName, PersistentFolder);
		Resolved.bCreated = IsValid(Resolved.LayerInfo);
		return Resolved;
	}

	static TArray<FName> GetMaterialLayerNamesExcludingVisibility(const ALandscape* Landscape)
	{
		TArray<FName> LayerNames;
		if (!IsValid(Landscape))
		{
			return LayerNames;
		}

		// No-argument call: the visibility bool exists only on UE 5.8. Filter it on both engines.
		LayerNames = Landscape->RetrieveTargetLayerNamesFromMaterials();
		LayerNames.Remove(NAME_None);
		if (const ULandscapeLayerInfoObject* VisibilityLayer = ALandscapeProxy::VisibilityLayer)
		{
			LayerNames.Remove(VisibilityLayer->GetLayerName());
		}
		return LayerNames;
	}

	static void AssignResolvedLayerInfo(ALandscape* Landscape, const FName LayerName, ULandscapeLayerInfoObject* LayerInfo)
	{
		if (!IsValid(Landscape) || !IsValid(LayerInfo) || LayerName.IsNone())
		{
			return;
		}

		const FLandscapeTargetLayerSettings* Existing = Landscape->GetTargetLayers().Find(LayerName);
		if (Existing != nullptr && Existing->LayerInfoObj.Get() == LayerInfo)
		{
			return;
		}

		if (Landscape->HasTargetLayer(LayerName))
		{
			Landscape->UpdateTargetLayer(LayerName, FLandscapeTargetLayerSettings(LayerInfo));
		}
		else
		{
			Landscape->AddTargetLayer(LayerName, FLandscapeTargetLayerSettings(LayerInfo));
		}
	}

	static bool BuildLandscapePaintLayersFromMaterial(
		ALandscape* Landscape,
		bool bFillEmptyLayers,
		TArray<FName>& OutLayerNames,
		TArray<TObjectPtr<ULandscapeLayerInfoObject>>& OutLayerInfos)
	{
		OutLayerNames.Reset();
		OutLayerInfos.Reset();

		if (!IsValid(Landscape))
		{
			return false;
		}

		ULandscapeInfo* LandscapeInfo = Landscape->GetLandscapeInfo();
		if (!LandscapeInfo)
		{
			return false;
		}

		const TArray<FName> MaterialLayerNames = GetMaterialLayerNamesExcludingVisibility(Landscape);
		if (MaterialLayerNames.IsEmpty())
		{
			return false;
		}

		ULandscapeLayerInfoObject* FirstLayerInfo = nullptr;
		TArray<UObject*> NewlyCreatedLayerInfos;
		for (const FName LayerName : MaterialLayerNames)
		{
			if (LayerName.IsNone())
			{
				continue;
			}

			const FResolvedLandscapeLayerInfo Resolved = ResolveLandscapeLayerInfo(
				Landscape,
				LayerName,
				TEXT("/Game/WorldBLD/LandscapeLayerInfos"),
				true);
			if (!IsValid(Resolved.LayerInfo))
			{
				UE_LOG(LogWorldBLD, Warning, TEXT("[PaintTargetLandscape] Failed to resolve LayerInfo for '%s'"), *LayerName.ToString());
				continue;
			}

			const ULandscapeLayerInfoObject* CurrentInfo = nullptr;
			if (const FLandscapeTargetLayerSettings* Existing = Landscape->GetTargetLayers().Find(LayerName))
			{
				CurrentInfo = Existing->LayerInfoObj.Get();
			}
			if (CurrentInfo != Resolved.LayerInfo)
			{
				// Epic parity: register on all proxies, then ensure the root landscape entry points at the asset.
				LandscapeInfo->CreateTargetLayerSettingsFor(Resolved.LayerInfo);
				AssignResolvedLayerInfo(Landscape, LayerName, Resolved.LayerInfo);
			}
			if (Resolved.bCreated)
			{
				NewlyCreatedLayerInfos.Add(Resolved.LayerInfo);
			}

			if (FirstLayerInfo == nullptr)
			{
				FirstLayerInfo = Resolved.LayerInfo;
			}

			OutLayerNames.Add(LayerName);
			OutLayerInfos.Add(Resolved.LayerInfo);
		}

		for (UObject* CreatedObject : NewlyCreatedLayerInfos)
		{
			SaveLandscapeLayerInfoPackage(Cast<ULandscapeLayerInfoObject>(CreatedObject));
		}

		if (NewlyCreatedLayerInfos.Num() > 0 && GEditor != nullptr)
		{
			GEditor->SyncBrowserToObjects(NewlyCreatedLayerInfos);
		}

		LandscapeInfo->UpdateLayerInfoMap();
		Landscape->Modify();
		Landscape->MarkPackageDirty();

		if (bFillEmptyLayers && FirstLayerInfo != nullptr)
		{
			const TArray<ULandscapeEditLayerBase*> EditLayers = Landscape->GetEditLayers();
			if (!EditLayers.IsEmpty() && EditLayers[0] != nullptr)
			{
				FScopedSetLandscapeEditingLayer Scope(Landscape, EditLayers[0]->GetGuid());
				FLandscapeEditDataInterface LandscapeEdit(LandscapeInfo);
				LandscapeEdit.FillEmptyLayers(FirstLayerInfo);
			}
			else
			{
				FLandscapeEditDataInterface LandscapeEdit(LandscapeInfo);
				LandscapeEdit.FillEmptyLayers(FirstLayerInfo);
			}
		}

		return OutLayerNames.Num() > 0;
	}

	static bool ShowLandscapePaintImportDialog(UWorldBLDLandscapePaintImportOptions* Options)
	{
		if (!IsValid(Options) || !FSlateApplication::IsInitialized())
		{
			return false;
		}

		const TSharedRef<SWindow> Window = SNew(SWindow)
			.Title(NSLOCTEXT("WorldBLD.PaintLandscape", "DialogTitle", "Import Landscape Layer Masks"))
			.SizingRule(ESizingRule::Autosized)
			.MinWidth(880.0f)
			.SupportsMaximize(false)
			.SupportsMinimize(false);

		TSharedPtr<SWorldBLDLandscapePaintDialog> DialogWidget;
		Window->SetContent(
			SAssignNew(DialogWidget, SWorldBLDLandscapePaintDialog, Window, Options));

		FSlateApplication::Get().AddModalWindow(Window, nullptr);
		return DialogWidget.IsValid() && DialogWidget->WasAccepted();
	}

	static bool ShowLandscapePopulateDialog(UWorldBLDLandscapePopulateOptions* Options)
	{
		if (!IsValid(Options) || !FSlateApplication::IsInitialized())
		{
			return false;
		}

		const TSharedRef<SWindow> Window = SNew(SWindow)
			.Title(NSLOCTEXT("WorldBLD.PopulateLandscape", "DialogTitle", "Populate Landscape"))
			.SizingRule(ESizingRule::Autosized)
			.MinWidth(880.0f)
			.SupportsMaximize(false)
			.SupportsMinimize(false);

		TSharedPtr<SWorldBLDLandscapePopulateDialog> DialogWidget;
		Window->SetContent(
			SAssignNew(DialogWidget, SWorldBLDLandscapePopulateDialog, Window, Options));

		FSlateApplication::Get().AddModalWindow(Window, nullptr);
		return DialogWidget.IsValid() && DialogWidget->WasAccepted();
	}

	static bool ImportSelectedLayerMasks(ALandscape* Landscape, UWorldBLDLandscapePaintImportOptions* Options)
	{
		if (!IsValid(Landscape) || !IsValid(Options))
		{
			return false;
		}

		ULandscapeInfo* LandscapeInfo = Landscape->GetLandscapeInfo();
		if (!LandscapeInfo)
		{
			UE_LOG(LogWorldBLD, Error, TEXT("[PaintTargetLandscape] Landscape has no LandscapeInfo."));
			return false;
		}

		FIntRect ImportRegion;
		if (!LandscapeInfo->GetLandscapeExtent(ImportRegion))
		{
			UE_LOG(LogWorldBLD, Error, TEXT("[PaintTargetLandscape] Failed to resolve landscape extent."));
			return false;
		}
		ImportRegion.Max.X += 1;
		ImportRegion.Max.Y += 1;

		const FLandscapeImportResolution RequiredResolution(ImportRegion.Width(), ImportRegion.Height());
		const TArray<ULandscapeEditLayerBase*> EditLayers = Landscape->GetEditLayers();
		const bool bUseEditLayerScope = !EditLayers.IsEmpty() && EditLayers[0] != nullptr;
		const FGuid CurrentLayerGuid = bUseEditLayerScope ? EditLayers[0]->GetGuid() : FGuid();

		FScopedTransaction Transaction(NSLOCTEXT("WorldBLD.PaintLandscape", "ImportLayersTxn", "Import Landscape Layer Masks"));
		Landscape->Modify();

		bool bImportedAnyLayer = false;
		bool bAttemptedMaskImport = false;
		for (FWorldBLDLandscapePaintLayer& Layer : Options->Layers)
		{
			if (!Layer.bSelected || Layer.SourceFilePath.IsEmpty() || !Layer.LayerInfo)
			{
				continue;
			}

			bAttemptedMaskImport = true;

			Options->RefreshLayerImport(Layer);
			if (Layer.ImportResult == ELandscapeImportResult::Error)
			{
				continue;
			}

			int32 DescriptorIndex = Layer.ImportDescriptor.FindDescriptorIndex(RequiredResolution.Width, RequiredResolution.Height);
			if (DescriptorIndex == INDEX_NONE && Layer.ImportDescriptor.ImportResolutions.IsEmpty())
			{
				Layer.ImportResult = ELandscapeImportResult::Error;
				Layer.ErrorMessage = NSLOCTEXT("WorldBLD.PaintLandscape", "NoImportDescriptor", "Unable to resolve import data for this layer file.");
				continue;
			}

			TArray<uint8> WeightData;
			FText ImportMessage;
			if (DescriptorIndex != INDEX_NONE)
			{
				const ELandscapeImportResult ImportResult = FLandscapeImportHelper::GetWeightmapImportData(
					Layer.ImportDescriptor,
					DescriptorIndex,
					Layer.LayerName,
					WeightData,
					ImportMessage);
				if (ImportResult == ELandscapeImportResult::Error)
				{
					Layer.ImportResult = ImportResult;
					Layer.ErrorMessage = ImportMessage;
					continue;
				}
			}
			else
			{
				DescriptorIndex = 0;
				const FLandscapeImportResolution SourceResolution = Layer.ImportDescriptor.ImportResolutions[DescriptorIndex];
				TArray<uint8> SourceData;
				const ELandscapeImportResult ImportResult = FLandscapeImportHelper::GetWeightmapImportData(
					Layer.ImportDescriptor,
					DescriptorIndex,
					Layer.LayerName,
					SourceData,
					ImportMessage);
				if (ImportResult == ELandscapeImportResult::Error)
				{
					Layer.ImportResult = ImportResult;
					Layer.ErrorMessage = ImportMessage;
					continue;
				}

				FLandscapeImportHelper::TransformWeightmapImportData(
					SourceData,
					WeightData,
					SourceResolution,
					RequiredResolution,
					ELandscapeImportTransformType::ExpandCentered);
			}

			if (WeightData.Num() != RequiredResolution.Width * RequiredResolution.Height)
			{
				Layer.ImportResult = ELandscapeImportResult::Error;
				Layer.ErrorMessage = NSLOCTEXT("WorldBLD.PaintLandscape", "ImportDataSizeMismatch", "Imported layer data size does not match landscape resolution.");
				continue;
			}

			if (bUseEditLayerScope)
			{
				FScopedSetLandscapeEditingLayer Scope(Landscape, CurrentLayerGuid);
				TAlphamapAccessor<false> AlphamapAccessor(LandscapeInfo, Layer.LayerInfo.Get());
				AlphamapAccessor.SetData(
					ImportRegion.Min.X,
					ImportRegion.Min.Y,
					ImportRegion.Max.X - 1,
					ImportRegion.Max.Y - 1,
					WeightData.GetData(),
					ELandscapeLayerPaintingRestriction::None);
			}
			else
			{
				TAlphamapAccessor<false> AlphamapAccessor(LandscapeInfo, Layer.LayerInfo.Get());
				AlphamapAccessor.SetData(
					ImportRegion.Min.X,
					ImportRegion.Min.Y,
					ImportRegion.Max.X - 1,
					ImportRegion.Max.Y - 1,
					WeightData.GetData(),
					ELandscapeLayerPaintingRestriction::None);
			}

			bImportedAnyLayer = true;
		}

		if (bAttemptedMaskImport && !bImportedAnyLayer)
		{
			return false;
		}

		FinalizeLandscapeLayerRegistration(Landscape);
		return true;
	}

	static AActor* GetPlacedActorFromHandle(const FTypedElementHandle& PlacedHandle)
	{
		UTypedElementRegistry* Registry = UTypedElementRegistry::GetInstance();
		if (Registry == nullptr)
		{
			return nullptr;
		}

		TTypedElement<ITypedElementObjectInterface> ObjectInterface = Registry->GetElement<ITypedElementObjectInterface>(PlacedHandle);
		return ObjectInterface ? ObjectInterface.GetObjectAs<AActor>() : nullptr;
	}

	static bool FitPCGVolumeToLandscapeExtent(APCGVolume* PCGVolume, const FVector& LandscapeExtentCm)
	{
		if (!IsValid(PCGVolume))
		{
			return false;
		}

		// Flat / near-flat landscapes report a tiny Z half-extent, which would produce a ~1.0 Z
		// actor scale on the default 200 cube. Clamp Z to at least 500 cm so sculpted terrain
		// still sits inside the volume without a manual rescale.
		constexpr double MinZExtentCm = 500.0;
		const FVector SafeExtentCm(
			FMath::Max(LandscapeExtentCm.X, 1.0),
			FMath::Max(LandscapeExtentCm.Y, 1.0),
			FMath::Max(LandscapeExtentCm.Z, MinZExtentCm));

		// Keep the default cube brush dimensions and fit bounds via actor scale.
		// Default UCubeBuilder size is 200, which corresponds to a half-extent of 100.
		const FVector VolumeScale = SafeExtentCm / 100.0;
		PCGVolume->SetActorScale3D(VolumeScale);
		return true;
	}

	static bool TryGetLandscapeBoundsForPCG(const ALandscape* TargetLandscape, FBox& OutBounds)
	{
		if (!IsValid(TargetLandscape))
		{
			return false;
		}

		// World Partition landscapes often have no components on the ALandscape actor itself
		// (they live on streaming proxies). GetComponentsBoundingBox is invalid in that case;
		// GetCompleteBounds covers loaded proxies and unloaded WP actor-desc extents.
		FBox LandscapeBounds = TargetLandscape->GetCompleteBounds();
		if (!LandscapeBounds.IsValid)
		{
			if (const ULandscapeInfo* LandscapeInfo = TargetLandscape->GetLandscapeInfo())
			{
				LandscapeBounds = LandscapeInfo->GetLoadedBounds();
			}
		}
		if (!LandscapeBounds.IsValid)
		{
			LandscapeBounds = TargetLandscape->GetComponentsBoundingBox(true);
		}
		if (!LandscapeBounds.IsValid)
		{
			return false;
		}

		OutBounds = LandscapeBounds;
		return true;
	}

	static APCGWorldActor* FindPCGWorldActor(UWorld* World)
	{
		if (!IsValid(World))
		{
			return nullptr;
		}

		for (TActorIterator<APCGWorldActor> It(World); It; ++It)
		{
			if (IsValid(*It))
			{
				return *It;
			}
		}

		return nullptr;
	}

	static APCGWorldActor* FindOrCreatePCGWorldActor(UWorld* World)
	{
		if (APCGWorldActor* ExistingWorldActor = FindPCGWorldActor(World))
		{
			return ExistingWorldActor;
		}

		// APCGWorldActor::CreatePCGWorldActor is not exported (MinimalAPI). UPCGSubsystem::GetPCGWorldActor
		// is the public entry point and creates a world actor in-editor when none is registered.
		if (UPCGSubsystem* PCGSubsystem = IsValid(World) ? World->GetSubsystem<UPCGSubsystem>() : nullptr)
		{
			return PCGSubsystem->GetPCGWorldActor();
		}

		return nullptr;
	}

	static void ConfigurePCGWorldActorForLandscapePCG(APCGWorldActor* PCGWorldActor, bool bTreatEditorViewportAsGenerationSource)
	{
		if (!IsValid(PCGWorldActor))
		{
			return;
		}

		PCGWorldActor->Modify();

		if (bTreatEditorViewportAsGenerationSource)
		{
			PCGWorldActor->bTreatEditorViewportAsGenerationSource = true;
		}

		UPCGLandscapeCache* LandscapeCache = PCGWorldActor->LandscapeCacheObject.Get();
		if (LandscapeCache == nullptr)
		{
			return;
		}

		if (LandscapeCache->SerializationMode != EPCGLandscapeCacheSerializationMode::AlwaysSerialize)
		{
			LandscapeCache->Modify();
			LandscapeCache->SerializationMode = EPCGLandscapeCacheSerializationMode::AlwaysSerialize;
		}
	}

	static void EnsurePCGVolumeAlwaysLoaded(APCGVolume* PCGVolume)
	{
		if (!IsValid(PCGVolume) || !PCGVolume->GetIsSpatiallyLoaded())
		{
			return;
		}

		PCGVolume->Modify();
		PCGVolume->SetIsSpatiallyLoaded(false);
	}

	static void EnsurePCGVolumePartitionedForWorldPartition(APCGVolume* PCGVolume, UWorld* World)
	{
		if (!IsValid(PCGVolume) || !IsValid(World) || !World->IsPartitionedWorld())
		{
			return;
		}

		UPCGComponent* PCGComponent = PCGVolume->GetComponentByClass<UPCGComponent>();
		if (PCGComponent == nullptr || PCGComponent->IsPartitioned())
		{
			return;
		}

		const bool bWasGenerated = PCGComponent->bGenerated;
		PCGComponent->SetIsPartitioned(true);

		// SetIsPartitioned cleans up prior non-partitioned output; regenerate static
		// volumes that had already completed generation. Runtime-managed components
		// are re-scheduled by the runtime gen system.
		if (bWasGenerated && PCGComponent->bActivated && !PCGComponent->IsManagedByRuntimeGenSystem())
		{
			PCGComponent->GenerateLocal(/*bForce=*/false);
		}
	}

	static void RefreshLandscapePCGVolumeGeneration(APCGVolume* PCGVolume)
	{
		if (!IsValid(PCGVolume))
		{
			return;
		}

		UPCGComponent* PCGComponent = PCGVolume->GetComponentByClass<UPCGComponent>();
		if (PCGComponent == nullptr || !PCGComponent->bActivated)
		{
			return;
		}

		if (PCGComponent->IsManagedByRuntimeGenSystem()
			|| PCGComponent->GenerationTrigger == EPCGComponentGenerationTrigger::GenerateAtRuntime)
		{
			UPCGBlueprintHelpers::RefreshPCGRuntimeComponent(PCGComponent, /*bFlushCache=*/true);
		}
		else
		{
			PCGComponent->GenerateLocal(/*bForce=*/true);
		}
	}

	static TArray<uint16> ReadHeightmapFromFile(const FString& HeightmapFilePath)
	{
		if (HeightmapFilePath.IsEmpty())
		{
			UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] HeightmapFilePath is empty"));
			return {};
		}

		if (!FPaths::FileExists(HeightmapFilePath))
		{
			UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] File does not exist: %s"), *HeightmapFilePath);
			return {};
		}

		const FString Extension = FPaths::GetExtension(HeightmapFilePath).ToLower();
		if (Extension == TEXT("png"))
		{
			TArray<uint8> CompressedData;
			if (!FFileHelper::LoadFileToArray(CompressedData, *HeightmapFilePath))
			{
				UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] Failed to read PNG file: %s"), *HeightmapFilePath);
				return {};
			}

			IImageWrapperModule& ImageWrapperModule = FModuleManager::LoadModuleChecked<IImageWrapperModule>(TEXT("ImageWrapper"));
			TSharedPtr<IImageWrapper> ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::PNG);
			if (!ImageWrapper.IsValid())
			{
				UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] Failed to create PNG image wrapper"));
				return {};
			}

			if (!ImageWrapper->SetCompressed(CompressedData.GetData(), CompressedData.Num()))
			{
				UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] PNG decode failed (SetCompressed): %s"), *HeightmapFilePath);
				return {};
			}

			if (ImageWrapper->GetBitDepth() != 16)
			{
				UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] PNG is not 16-bit. BitDepth=%d. File=%s"), ImageWrapper->GetBitDepth(), *HeightmapFilePath);
				return {};
			}

			TArray64<uint8> RawGray16;
			if (!ImageWrapper->GetRaw(ERGBFormat::Gray, 16, RawGray16) || RawGray16.Num() == 0)
			{
				UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] Failed to extract raw grayscale16 data from PNG: %s"), *HeightmapFilePath);
				return {};
			}

			if ((RawGray16.Num() % 2) != 0)
			{
				UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] PNG raw data byte count is not even: %d. File=%s"), RawGray16.Num(), *HeightmapFilePath);
				return {};
			}

			TArray<uint16> Out;
			Out.SetNumUninitialized(RawGray16.Num() / 2);
			FMemory::Memcpy(Out.GetData(), RawGray16.GetData(), RawGray16.Num());

			#if !PLATFORM_LITTLE_ENDIAN
			for (uint16& Value : Out)
			{
				Value = BYTESWAP_ORDER16(Value);
			}
			#endif

			return Out;
		}
		else if (Extension == TEXT("raw") || Extension == TEXT("r16"))
		{
			TArray<uint8> Bytes;
			if (!FFileHelper::LoadFileToArray(Bytes, *HeightmapFilePath))
			{
				UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] Failed to read RAW/R16 file: %s"), *HeightmapFilePath);
				return {};
			}

			if ((Bytes.Num() % 2) != 0)
			{
				UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] RAW/R16 byte count is not even: %d. File=%s"), Bytes.Num(), *HeightmapFilePath);
				return {};
			}

			const int32 NumSamples = Bytes.Num() / 2;
			TArray<uint16> Out;
			Out.SetNumUninitialized(NumSamples);

			const uint8* Data = Bytes.GetData();
			for (int32 i = 0; i < NumSamples; ++i)
			{
				const uint16 Lo = Data[(i * 2) + 0];
				const uint16 Hi = Data[(i * 2) + 1];
				Out[i] = (Hi << 8) | Lo;
			}

			return Out;
		}

		UE_LOG(LogWorldBLD, Error, TEXT("[ReadHeightmapFromFile] Unsupported heightmap format: .%s (File=%s)"), *Extension, *HeightmapFilePath);
		return {};
	}
}

ALandscape* UWorldBLDEditorUtilityLibrary::SpawnLandscapeWithHeightmap(
	const FString& HeightmapFilePath,
	int32 Resolution,
	int32 NumComponents,
	UMaterialInterface* Material)
{
	if (HeightmapFilePath.IsEmpty())
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] HeightmapFilePath is empty"));
		return nullptr;
	}

	if (!FPaths::FileExists(HeightmapFilePath))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] Heightmap file not found: %s"), *HeightmapFilePath);
		return nullptr;
	}

	if (Resolution <= 0)
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] Resolution must be > 0. Got=%d"), Resolution);
		return nullptr;
	}

	if (NumComponents <= 0)
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] NumComponents must be > 0. Got=%d"), NumComponents);
		return nullptr;
	}

	TArray<uint16> HeightData = ReadHeightmapFromFile(HeightmapFilePath);
	if (HeightData.Num() == 0)
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] Failed to read heightmap data from: %s"), *HeightmapFilePath);
		return nullptr;
	}

	const int32 NumSubsections = 2;
	const int32 ComponentSizeQuads = (Resolution + 1) / NumComponents - 1;
	if (ComponentSizeQuads <= 0)
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] Computed invalid ComponentSizeQuads=%d (Resolution=%d, NumComponents=%d)"), ComponentSizeQuads, Resolution, NumComponents);
		return nullptr;
	}

	const int32 SubsectionSizeQuads = ComponentSizeQuads / NumSubsections;
	if (SubsectionSizeQuads <= 0)
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] Computed invalid SubsectionSizeQuads=%d (ComponentSizeQuads=%d, NumSubsections=%d)"), SubsectionSizeQuads, ComponentSizeQuads, NumSubsections);
		return nullptr;
	}

	if (!FMath::IsPowerOfTwo(SubsectionSizeQuads + 1))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] Landscape requirement failed: (SubsectionSizeQuads+1) must be power of two. SubsectionSizeQuads=%d"), SubsectionSizeQuads);
		return nullptr;
	}

	const int32 MinX = 0;
	const int32 MinY = 0;
	const int32 MaxX = NumComponents * ComponentSizeQuads;
	const int32 MaxY = NumComponents * ComponentSizeQuads;
	const int32 ExpectedSamples = (MaxX - MinX + 1) * (MaxY - MinY + 1);

	if (HeightData.Num() != ExpectedSamples)
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] Heightmap sample count mismatch. Expected=%d, Actual=%d. ImportBounds=[%d,%d]-[%d,%d]"), ExpectedSamples, HeightData.Num(), MinX, MinY, MaxX, MaxY);
		return nullptr;
	}

	UWorld* World = (GEditor != nullptr) ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] No editor world context available"));
		return nullptr;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ALandscape* Landscape = World->SpawnActor<ALandscape>(ALandscape::StaticClass(), FTransform::Identity, SpawnParams);
	if (!IsValid(Landscape))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapeWithHeightmap] Failed to spawn ALandscape actor"));
		return nullptr;
	}

	const FGuid LandscapeGuid = FGuid::NewGuid();
	TMap<FGuid, TArray<uint16>> HeightmapData;
	HeightmapData.Add(LandscapeGuid, MoveTemp(HeightData));

	TMap<FGuid, TArray<FLandscapeImportLayerInfo>> MaterialLayerData;
	TArray<FLandscapeLayer> ImportLayers;

	Landscape->Import(
		LandscapeGuid,
		MinX,
		MinY,
		MaxX,
		MaxY,
		NumSubsections,
		SubsectionSizeQuads,
		HeightmapData,
		*HeightmapFilePath,
		MaterialLayerData,
		ELandscapeImportAlphamapType::Additive,
		MakeArrayView(static_cast<const TArray<FLandscapeLayer>&>(ImportLayers)));

	if (Material != nullptr)
	{
		Landscape->LandscapeMaterial = Material;

		FProperty* Property = FindFProperty<FProperty>(ALandscapeProxy::StaticClass(), TEXT("LandscapeMaterial"));
		if (Property != nullptr)
		{
			FPropertyChangedEvent PropertyChangedEvent(Property);
			Landscape->PostEditChangeProperty(PropertyChangedEvent);
		}
		else
		{
			Landscape->PostEditChange();
		}
	}

	Landscape->RegisterAllComponents();
	Landscape->RecreateCollisionComponents();
	Landscape->MarkPackageDirty();

	return Landscape;
}

bool UWorldBLDEditorUtilityLibrary::PaintTargetLandscape(
	ALandscape* TargetLandscape,
	UMaterialInterface* Material,
	bool bFillEmptyLayers,
	bool bFlipYAxis)
{
	if (!IsValid(TargetLandscape))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[PaintTargetLandscape] TargetLandscape is null."));
		return false;
	}

	if (!IsValid(Material))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[PaintTargetLandscape] Material is null."));
		return false;
	}

	ApplyLandscapeMaterial(TargetLandscape, Material);

	TArray<FName> LayerNames;
	TArray<TObjectPtr<ULandscapeLayerInfoObject>> LayerInfos;
	if (!BuildLandscapePaintLayersFromMaterial(TargetLandscape, bFillEmptyLayers, LayerNames, LayerInfos))
	{
		UE_LOG(LogWorldBLD, Warning, TEXT("[PaintTargetLandscape] No paint layers found in material '%s'."), *GetNameSafe(Material));
		return false;
	}

	UWorldBLDLandscapePaintImportOptions* Options = NewObject<UWorldBLDLandscapePaintImportOptions>(GetTransientPackage());
	Options->Initialize(TargetLandscape, Material, LayerNames, LayerInfos, bFlipYAxis);

	if (!ShowLandscapePaintImportDialog(Options))
	{
		// Skip Layer Import: registration/fill already ran; finalize so LayerInfos + weights persist.
		FinalizeLandscapeLayerRegistration(TargetLandscape);
		return true;
	}

	return ImportSelectedLayerMasks(TargetLandscape, Options);
}

bool UWorldBLDEditorUtilityLibrary::PopulateTargetLandscape(
	bool bFillEmptyLayers,
	bool bFlipYAxis)
{
	UWorldBLDLandscapePopulateOptions* Options = NewObject<UWorldBLDLandscapePopulateOptions>(GetTransientPackage());
	if (!ShowLandscapePopulateDialog(Options))
	{
		return false;
	}

	ALandscape* TargetLandscape = Options->TargetLandscape;
	UWorldBLDLandscapePreset* Preset = Options->Preset;
	if (!IsValid(TargetLandscape) || !IsValid(Preset))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[PopulateTargetLandscape] Setup dialog accepted without a valid landscape and preset."));
		return false;
	}

	if (IsValid(Preset->LandscapeMaterial))
	{
		PaintTargetLandscape(TargetLandscape, Preset->LandscapeMaterial, bFillEmptyLayers, bFlipYAxis);
	}
	else
	{
		UE_LOG(LogWorldBLD, Warning, TEXT("[PopulateTargetLandscape] Preset '%s' has no Landscape Material; skipping paint step."), *GetNameSafe(Preset));
	}

	// Preset no longer stores PCG graphs; spawn the LandBLD default static/runtime graphs.
	UPCGGraph* StaticPCG = LoadObject<UPCGGraph>(
		nullptr,
		TEXT("/WorldBLD/MiniTools/LandBLD/PCG/PCG_LandBLDStatic.PCG_LandBLDStatic"));
	UPCGGraph* RuntimePCG = LoadObject<UPCGGraph>(
		nullptr,
		TEXT("/WorldBLD/MiniTools/LandBLD/PCG/PCG_LandBLDRuntime.PCG_LandBLDRuntime"));

	if (IsValid(StaticPCG))
	{
		APCGVolume* StaticPCGVolume = SpawnLandscapePCGVolume(TargetLandscape, StaticPCG, TEXT("LandBLD Static PCG"), false);
		AssignLandscapePresetToPCGVolume(StaticPCGVolume, Preset, TEXT("Static"));
	}
	else
	{
		UE_LOG(LogWorldBLD, Warning, TEXT("[PopulateTargetLandscape] Failed to load LandBLD Static PCG graph; skipping static volume spawn."));
	}

	if (IsValid(RuntimePCG))
	{
		APCGVolume* RuntimePCGVolume = SpawnLandscapePCGVolume(TargetLandscape, RuntimePCG, TEXT("LandBLD Runtime PCG"), true);
		AssignLandscapePresetToPCGVolume(RuntimePCGVolume, Preset, TEXT("Runtime"));
	}
	else
	{
		UE_LOG(LogWorldBLD, Warning, TEXT("[PopulateTargetLandscape] Failed to load LandBLD Runtime PCG graph; skipping runtime volume spawn."));
	}

	return true;
}

APCGVolume* UWorldBLDEditorUtilityLibrary::SpawnLandscapePCGVolume(
	ALandscape* TargetLandscape,
	UPCGGraphInterface* PCGGraph,
	const FString& OptionalActorLabel,
	bool bRuntimeGeneration)
{
#if WITH_EDITOR
	if (!IsValid(TargetLandscape))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapePCGVolume] TargetLandscape is null."));
		return nullptr;
	}

	if (!IsValid(PCGGraph))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapePCGVolume] PCGGraph is null or invalid."));
		return nullptr;
	}

	UWorld* World = TargetLandscape->GetWorld();
	if (!IsValid(World) || GEditor == nullptr)
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapePCGVolume] Missing valid editor world context."));
		return nullptr;
	}

	FBox LandscapeBounds;
	if (!TryGetLandscapeBoundsForPCG(TargetLandscape, LandscapeBounds))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapePCGVolume] Landscape bounds are invalid for '%s'."), *GetNameSafe(TargetLandscape));
		return nullptr;
	}

	const FVector LandscapeCenter = LandscapeBounds.GetCenter();

	APCGVolume* SpawnedPCGVolume = nullptr;

	if (bRuntimeGeneration)
	{
		// For runtime PCG we must NOT go through PlaceAssetInCurrentLevel.
		//
		// PlaceAssetInCurrentLevel → PostPlaceAsset → SetGraph → RefreshAfterGraphChanged →
		// Refresh() → ScheduleRefresh queues an OnRefresh lambda in the PCG executor. If we then
		// flip GenerationTrigger to GenerateAtRuntime after placement, the already-queued OnRefresh
		// fires with IsManagedByRuntimeGenSystem() == true and hits the PCGComponent assertion:
		//   !IsManagedByRuntimeGenSystem() [PCGComponent.cpp:3106]
		//
		// CancelGeneration() cannot fix this because it only cancels active generation tasks
		// (CurrentGenerationTask), not the pending refresh task (CurrentRefreshTask).
		//
		// The correct fix is to flip GenerationTrigger BEFORE SetGraph so that the Refresh() call
		// inside RefreshAfterGraphChanged sees IsManagedByRuntimeGenSystem() == true and routes to
		// RefreshRuntimeGenComponent instead of ScheduleRefresh. This requires spawning the volume
		// directly so we control the ordering of trigger flip and SetGraph.
		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		SpawnParams.ObjectFlags |= RF_Transactional;
		SpawnedPCGVolume = World->SpawnActor<APCGVolume>(APCGVolume::StaticClass(), FTransform(LandscapeCenter), SpawnParams);

		if (!IsValid(SpawnedPCGVolume))
		{
			UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapePCGVolume] Failed to spawn APCGVolume for runtime graph '%s'."), *GetNameSafe(PCGGraph));
			return nullptr;
		}

		// SpawnActor leaves ABrush::Brush nullptr. A bare UCubeBuilder::Build silently no-ops in
		// EndBrush when Brush is null, so FitPCGVolumeToLandscapeExtent would scale empty geometry
		// and leave zero bounds. Mirror UActorFactoryBoxVolume / UPCGVolumeTool: allocate UModel +
		// UPolys, build the default 200³ cube, then FBSPOps::csgPrepMovingBrush.
		UCubeBuilder* BrushBuilder = NewObject<UCubeBuilder>();
		BrushBuilder->X = 200.0f;
		BrushBuilder->Y = 200.0f;
		BrushBuilder->Z = 200.0f;
		UActorFactory::CreateBrushForVolumeActor(SpawnedPCGVolume, BrushBuilder);

		UPCGComponent* SpawnedPCGComponent = SpawnedPCGVolume->GetComponentByClass<UPCGComponent>();
		if (SpawnedPCGComponent != nullptr)
		{
			FProperty* TriggerProperty = FindFieldChecked<FProperty>(
				UPCGComponent::StaticClass(),
				GET_MEMBER_NAME_CHECKED(UPCGComponent, GenerationTrigger));

			// UPCGComponent hides PreEditChange/PostEditChangeProperty as private, but they remain
			// public on UActorComponent — call through the base pointer to run PCG's transition
			// logic (registers the component with the runtime gen system so that
			// IsManagedByRuntimeGenSystem() returns true before SetGraph is called below).
			UActorComponent* PCGActorComponent = SpawnedPCGComponent;
			PCGActorComponent->PreEditChange(TriggerProperty);
			SpawnedPCGComponent->GenerationTrigger = EPCGComponentGenerationTrigger::GenerateAtRuntime;
			FPropertyChangedEvent TriggerChangedEvent(TriggerProperty, EPropertyChangeType::ValueSet);
			PCGActorComponent->PostEditChangeProperty(TriggerChangedEvent);

			// Now safe: Refresh() inside SetGraph → RefreshAfterGraphChanged routes to the runtime
			// scheduler (RefreshRuntimeGenComponent) instead of ScheduleRefresh.
			SpawnedPCGComponent->SetGraph(PCGGraph);
		}
		else
		{
			UE_LOG(LogWorldBLD, Warning, TEXT("[SpawnLandscapePCGVolume] Spawned volume '%s' has no UPCGComponent."), *GetNameSafe(SpawnedPCGVolume));
		}
	}
	else
	{
		// Static PCG: use the standard placement factory path. SetGraph → ScheduleRefresh is safe
		// here because GenerationTrigger stays at its default (GenerateOnLoad), so OnRefresh never
		// sees IsManagedByRuntimeGenSystem() == true.
		GEditor->ClickLocation = LandscapeCenter;
		GEditor->ClickPlane = FPlane(LandscapeCenter, FVector::UpVector);

		UE::AssetPlacementUtil::FExtraPlaceAssetOptions PlacementOptions;
		PlacementOptions.bSelectOutput = true;
		PlacementOptions.ObjectFlags = RF_Transactional;

		const TArray<FTypedElementHandle> PlacedElements = UE::AssetPlacementUtil::PlaceAssetInCurrentLevel(PCGGraph, PlacementOptions);
		if (PlacedElements.IsEmpty())
		{
			UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapePCGVolume] Placement returned no elements for graph '%s'."), *GetNameSafe(PCGGraph));
			return nullptr;
		}

		for (const FTypedElementHandle& PlacedElement : PlacedElements)
		{
			if (AActor* PlacedActor = GetPlacedActorFromHandle(PlacedElement))
			{
				SpawnedPCGVolume = Cast<APCGVolume>(PlacedActor);
				if (SpawnedPCGVolume != nullptr)
				{
					break;
				}
			}
		}

		if (SpawnedPCGVolume == nullptr)
		{
			UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapePCGVolume] Placement did not produce an APCGVolume for graph '%s'."), *GetNameSafe(PCGGraph));
			return nullptr;
		}
	}

	SpawnedPCGVolume->SetActorLocation(LandscapeCenter);

	if (!OptionalActorLabel.IsEmpty())
	{
		SpawnedPCGVolume->SetActorLabel(OptionalActorLabel);
	}

	const FVector LandscapeExtent = LandscapeBounds.GetExtent();
	if (!FitPCGVolumeToLandscapeExtent(SpawnedPCGVolume, LandscapeExtent))
	{
		UE_LOG(LogWorldBLD, Warning, TEXT("[SpawnLandscapePCGVolume] Failed to fit brush bounds for '%s'."), *GetNameSafe(SpawnedPCGVolume));
	}

	EnsurePCGVolumeAlwaysLoaded(SpawnedPCGVolume);
	EnsurePCGVolumePartitionedForWorldPartition(SpawnedPCGVolume, World);

	if (APCGWorldActor* PCGWorldActor = FindOrCreatePCGWorldActor(World))
	{
		ConfigurePCGWorldActorForLandscapePCG(PCGWorldActor, bRuntimeGeneration);
	}
	else if (bRuntimeGeneration)
	{
		UE_LOG(LogWorldBLD, Warning, TEXT("[SpawnLandscapePCGVolume] Failed to find or create APCGWorldActor while enabling runtime generation for '%s'."), *GetNameSafe(SpawnedPCGVolume));
	}

	return SpawnedPCGVolume;
#else
	UE_LOG(LogWorldBLD, Error, TEXT("[SpawnLandscapePCGVolume] Editor-only API called in non-editor build."));
	return nullptr;
#endif
}

bool UWorldBLDEditorUtilityLibrary::FitLandscapePCGVolume(
	APCGVolume* PCGVolume,
	ALandscape* TargetLandscape,
	bool bExpandExistingBounds)
{
#if WITH_EDITOR
	if (!IsValid(PCGVolume))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[FitLandscapePCGVolume] PCGVolume is null."));
		return false;
	}

	if (!IsValid(TargetLandscape))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[FitLandscapePCGVolume] TargetLandscape is null."));
		return false;
	}

	UWorld* World = TargetLandscape->GetWorld();
	if (!IsValid(World))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[FitLandscapePCGVolume] Missing valid world context."));
		return false;
	}

	FBox LandscapeBounds;
	if (!TryGetLandscapeBoundsForPCG(TargetLandscape, LandscapeBounds))
	{
		UE_LOG(LogWorldBLD, Error, TEXT("[FitLandscapePCGVolume] Landscape bounds are invalid for '%s'."), *GetNameSafe(TargetLandscape));
		return false;
	}

	FBox TargetBounds = LandscapeBounds;
	if (bExpandExistingBounds)
	{
		const FBox ExistingVolumeBounds = PCGVolume->GetComponentsBoundingBox(true);
		if (ExistingVolumeBounds.IsValid)
		{
			TargetBounds += ExistingVolumeBounds;
		}
	}

	PCGVolume->Modify();
	PCGVolume->SetActorLocation(TargetBounds.GetCenter());
	if (!FitPCGVolumeToLandscapeExtent(PCGVolume, TargetBounds.GetExtent()))
	{
		UE_LOG(LogWorldBLD, Warning, TEXT("[FitLandscapePCGVolume] Failed to fit brush bounds for '%s'."), *GetNameSafe(PCGVolume));
		return false;
	}

	PCGVolume->PostEditChange();
	EnsurePCGVolumeAlwaysLoaded(PCGVolume);
	EnsurePCGVolumePartitionedForWorldPartition(PCGVolume, World);

	const UPCGComponent* PCGComponent = PCGVolume->GetComponentByClass<UPCGComponent>();
	const bool bRuntimeGeneration = IsValid(PCGComponent)
		&& (PCGComponent->IsManagedByRuntimeGenSystem()
			|| PCGComponent->GenerationTrigger == EPCGComponentGenerationTrigger::GenerateAtRuntime);
	if (APCGWorldActor* PCGWorldActor = FindOrCreatePCGWorldActor(World))
	{
		ConfigurePCGWorldActorForLandscapePCG(PCGWorldActor, bRuntimeGeneration);
	}

	RefreshLandscapePCGVolumeGeneration(PCGVolume);
	return true;
#else
	UE_LOG(LogWorldBLD, Error, TEXT("[FitLandscapePCGVolume] Editor-only API called in non-editor build."));
	return false;
#endif
}

void UWorldBLDEditorUtilityLibrary::OpenWorldBLDProjectSettings()
{
#if WITH_EDITOR
	const UWorldBLDRuntimeSettings* Settings = GetDefault<UWorldBLDRuntimeSettings>();
	if (Settings == nullptr)
	{
		return;
	}

	ISettingsModule* SettingsModule = FModuleManager::LoadModulePtr<ISettingsModule>(TEXT("Settings"));
	if (SettingsModule == nullptr)
	{
		return;
	}

	SettingsModule->ShowViewer(Settings->GetContainerName(), Settings->GetCategoryName(), Settings->GetSectionName());
#endif
}
