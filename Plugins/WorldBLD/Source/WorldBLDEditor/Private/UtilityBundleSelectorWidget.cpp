// Copyright WorldBLD LLC. All rights reserved.

#include "UtilityBundleSelectorWidget.h"
#include "UtilityBundleItemButtonWidget.h"
#include "WorldBLDEditController.h"
#include "WorldBLDEditorToolkit.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/WidgetBlueprintGeneratedClass.h"
#include "Components/TextBlock.h"
#include "Components/WrapBox.h"
#include "Components/WrapBoxSlot.h"
#include "Components/Widget.h"
#include "Editor.h"
#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"

void UUtilityBundleSelectorWidget::ForceRescanAssetRegistry()
{
	FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
	IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();
	
	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::ForceRescanAssetRegistry - Forcing Asset Registry to scan package paths..."));
	
	// AssetRegistry expects mount/package paths (e.g. /WorldBLD), not filesystem paths.
	TArray<FString> PathsToScan;
	PathsToScan.Add(TEXT("/WorldBLD"));
	PathsToScan.Add(TEXT("/WorldBLD/Utilities"));
	PathsToScan.Add(TEXT("/Game"));

	// Add all currently cached package paths under the WorldBLD mount.
	TArray<FString> CachedPaths;
	AssetRegistry.GetAllCachedPaths(CachedPaths);
	for (const FString& CachedPath : CachedPaths)
	{
		if (CachedPath.StartsWith(TEXT("/WorldBLD")))
		{
			PathsToScan.AddUnique(CachedPath);
		}
	}

	UE_LOG(LogTemp, Log, TEXT("  Scanning %d package path(s)"), PathsToScan.Num());
	AssetRegistry.ScanPathsSynchronous(PathsToScan, true);
	
	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::ForceRescanAssetRegistry - Scan complete!"));
}

void UUtilityBundleSelectorWidget::LoadAndDisplayUtilityBundles(const FString& SearchPath, bool bTryCommonPaths)
{
	if (!ItemContainer)
	{
		UE_LOG(LogTemp, Error, TEXT("UUtilityBundleSelectorWidget::LoadAndDisplayUtilityBundles - ItemContainer is not bound!"));
		return;
	}

	// Clear existing widgets and bundles
	ItemContainer->ClearChildren();
	ItemWidgets.Empty();
	LoadedBundles.Empty();

	// Validate that we have an item widget class to instantiate
	if (!ItemWidgetClass || !IsValid(ItemWidgetClass))
	{
		UE_LOG(LogTemp, Error, TEXT("UUtilityBundleSelectorWidget::LoadAndDisplayUtilityBundles - ItemWidgetClass is not set!"));
		return;
	}

	// Ensure the ItemWidgetClass is a subclass of UUtilityBundleItemButtonWidget
	if (!ItemWidgetClass->IsChildOf(UUtilityBundleItemButtonWidget::StaticClass()))
	{
		UE_LOG(LogTemp, Error, TEXT("UUtilityBundleSelectorWidget::LoadAndDisplayUtilityBundles - ItemWidgetClass must be a subclass of UUtilityBundleItemButtonWidget!"));
		return;
	}

	// Get the Asset Registry
	FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
	IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();

	// Define the primary path to search in (package path format).
	// Default to /WorldBLD/Utilities, which matches current plugin content layout.
	const FString ActualSearchPath = SearchPath.IsEmpty() ? TEXT("/WorldBLD/Utilities") : SearchPath;

	auto UpdateNoBundlesFoundVisibility = [this](bool bHasDisplayedBundles)
	{
		const ESlateVisibility DesiredVisibility = bHasDisplayedBundles ? ESlateVisibility::Collapsed : ESlateVisibility::Visible;

		// Preferred path: explicit bind from UMG.
		if (NoBundlesFoundText)
		{
			NoBundlesFoundText->SetVisibility(DesiredVisibility);
		}

		// Defensive fallback: if the optional bind isn't wired in Blueprint, still try to
		// toggle any obvious "No utilities found" text blocks by name/text.
		if (WidgetTree)
		{
			TArray<UWidget*> AllWidgets;
			WidgetTree->GetAllWidgets(AllWidgets);
			for (UWidget* Widget : AllWidgets)
			{
				UTextBlock* CandidateText = Cast<UTextBlock>(Widget);
				if (!CandidateText)
				{
					continue;
				}

				const FString WidgetName = CandidateText->GetName();
				const FString WidgetText = CandidateText->GetText().ToString();
				const bool bLooksLikeNoResultsLabel =
					WidgetName.Contains(TEXT("NoBundlesFound"), ESearchCase::IgnoreCase) ||
					WidgetName.Contains(TEXT("NoUtilities"), ESearchCase::IgnoreCase) ||
					WidgetText.Contains(TEXT("No utilit"), ESearchCase::IgnoreCase) ||
					WidgetText.Contains(TEXT("No bundle"), ESearchCase::IgnoreCase);

				if (bLooksLikeNoResultsLabel)
				{
					CandidateText->SetVisibility(DesiredVisibility);
				}
			}
		}
	};

	auto QueryBundlesAtPath = [&AssetRegistry](const FString& InSearchPath, TArray<FAssetData>& OutAssets)
	{
		FARFilter Filter;
		Filter.PackagePaths.Add(FName(*InSearchPath));
		Filter.ClassPaths.Add(UWorldBLDUtilityBundle::StaticClass()->GetClassPathName());
		Filter.bRecursivePaths = true;     // Search recursively in subdirectories
		Filter.bRecursiveClasses = true;   // Include Blueprint subclasses of UWorldBLDUtilityBundle
		AssetRegistry.GetAssets(Filter, OutAssets);
	};

	TArray<FAssetData> AssetDataList;
	QueryBundlesAtPath(ActualSearchPath, AssetDataList);

	// Debug logging to help diagnose issues.
	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LoadAndDisplayUtilityBundles - Searching in path: %s"), *ActualSearchPath);
	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LoadAndDisplayUtilityBundles - Asset Registry returned %d asset(s)"), AssetDataList.Num());

	// Load and create widgets for each asset
	for (const FAssetData& AssetData : AssetDataList)
	{
		// Debug: Log each asset found
		UE_LOG(LogTemp, Log, TEXT("  - Found asset: %s (Class: %s, Path: %s)"), 
			*AssetData.AssetName.ToString(), 
			*AssetData.AssetClassPath.ToString(), 
			*AssetData.GetObjectPathString());

		// Load the asset instance
		UWorldBLDUtilityBundle* BundleAsset = Cast<UWorldBLDUtilityBundle>(AssetData.GetAsset());
		if (!BundleAsset)
		{
			UE_LOG(LogTemp, Warning, TEXT("  - Failed to cast asset %s to UWorldBLDUtilityBundle"), *AssetData.AssetName.ToString());
			continue;
		}

		// Store the loaded bundle
		LoadedBundles.Add(BundleAsset);

		// Create the item widget
		UUtilityBundleItemButtonWidget* ItemWidget = CreateWidget<UUtilityBundleItemButtonWidget>(this, ItemWidgetClass);
		
		if (ItemWidget)
		{
			// Configure the item with the bundle asset instance
			ItemWidget->SetUtilityBundle(BundleAsset);

			// Bind directly to the data asset. Utility bundles are DataAsset instances, so the
			// generic class-based selector path cannot distinguish one bundle from another.
			ItemWidget->OnUtilityBundleItemClicked.BindUObject(this, &UUtilityBundleSelectorWidget::HandleUtilityBundleItemClicked);

			// Add to the WrapBox
			UWrapBoxSlot* WrapBoxSlot = ItemContainer->AddChildToWrapBox(ItemWidget);
			
			if (WrapBoxSlot)
			{
				// Configure slot padding (hard-coded defaults matching base class)
				WrapBoxSlot->SetPadding(FMargin(4.0f));
				WrapBoxSlot->SetHorizontalAlignment(HAlign_Center);
				WrapBoxSlot->SetVerticalAlignment(VAlign_Center);
			}

			// Keep track of created widgets
			ItemWidgets.Add(ItemWidget);
		}
	}

	// Log the number of utility bundles found
	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LoadAndDisplayUtilityBundles - Found and displayed %d utility bundle(s) in %s"), 
		LoadedBundles.Num(), *ActualSearchPath);

	const bool bHasDisplayedBundles = ItemWidgets.Num() > 0;
	UpdateNoBundlesFoundVisibility(bHasDisplayedBundles);

	// If nothing was found, try common path variations or help debug
	if (!bHasDisplayedBundles)
	{
		UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LoadAndDisplayUtilityBundles - No utility bundles found in %s"), *ActualSearchPath);
		
		// If enabled, try common path variations automatically
		if (bTryCommonPaths && SearchPath.IsEmpty()) // Only try alternatives if user didn't specify a custom path
		{
			TArray<FString> CommonPaths = {
				TEXT("/WorldBLD/Utilities"),
				TEXT("/WorldBLD/Utilities/Data"),
				TEXT("/Game/WorldBLD/Utilities/Data"),
				TEXT("/Plugins/WorldBLD/Utilities/Data"),
				TEXT("/WorldBLD/Content/Utilities/Data"),
				TEXT("/Game/Plugins/WorldBLD/Utilities/Data"),
				TEXT("/Game/WorldBLD/Utilities")
			};
			
			UE_LOG(LogTemp, Log, TEXT("  Trying common path variations..."));
			
			for (const FString& AlternatePath : CommonPaths)
			{
				TArray<FAssetData> AltAssets;
				QueryBundlesAtPath(AlternatePath, AltAssets);
				
				if (AltAssets.Num() > 0)
				{
					UE_LOG(LogTemp, Log, TEXT("  SUCCESS! Found %d asset(s) in alternate path: %s"), AltAssets.Num(), *AlternatePath);
					UE_LOG(LogTemp, Log, TEXT("  Retrying with this path..."));
					
					// Recursively call with the found path, but disable auto-retry to avoid infinite loop
					LoadAndDisplayUtilityBundles(AlternatePath, false);
					return;
				}
			}
			
			UE_LOG(LogTemp, Warning, TEXT("  No assets found in any common path variation."));
		}
		
		UE_LOG(LogTemp, Warning, TEXT("  Possible reasons:"));
		UE_LOG(LogTemp, Warning, TEXT("  1. Assets might not be saved/loaded yet"));
		UE_LOG(LogTemp, Warning, TEXT("  2. Asset Registry might need to be rescanned - try calling ForceRescanAssetRegistry()"));
		UE_LOG(LogTemp, Warning, TEXT("  3. Assets might have a different base class"));
		
		// Try to find ANY UWorldBLDUtilityBundle assets in the entire project to help debug
		FARFilter DebugFilter;
		DebugFilter.ClassPaths.Add(UWorldBLDUtilityBundle::StaticClass()->GetClassPathName());
		DebugFilter.bRecursiveClasses = true;
		DebugFilter.bRecursivePaths = true;
		
		TArray<FAssetData> AllBundles;
		AssetRegistry.GetAssets(DebugFilter, AllBundles);
		
		if (AllBundles.Num() > 0)
		{
			UE_LOG(LogTemp, Warning, TEXT("  Found %d UWorldBLDUtilityBundle asset(s) elsewhere in project:"), AllBundles.Num());
			for (const FAssetData& Bundle : AllBundles)
			{
				UE_LOG(LogTemp, Warning, TEXT("    - %s"), *Bundle.GetObjectPathString());
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("  No UWorldBLDUtilityBundle assets found anywhere in the project!"));
			UE_LOG(LogTemp, Warning, TEXT("  Try:"));
			UE_LOG(LogTemp, Warning, TEXT("    1. Calling ForceRescanAssetRegistry() before LoadAndDisplayUtilityBundles()"));
			UE_LOG(LogTemp, Warning, TEXT("    2. Saving your utility bundle assets"));
			UE_LOG(LogTemp, Warning, TEXT("    3. Verifying they are actually UWorldBLDUtilityBundle data assets"));
		}
	}
}

void UUtilityBundleSelectorWidget::OnItemClicked_Implementation(UClass* ClickedItemClass)
{
	// Find the utility bundle asset associated with the clicked item
	// We need to iterate through the item widgets to find which one was clicked
	for (UWorldBLDItemButtonWidget* Widget : ItemWidgets)
	{
		if (Widget && Widget->ItemClass == ClickedItemClass)
		{
			// Cast to our specialized widget type to get the bundle asset
			UUtilityBundleItemButtonWidget* BundleWidget = Cast<UUtilityBundleItemButtonWidget>(Widget);
			if (BundleWidget && BundleWidget->UtilityBundleAsset)
			{
				LaunchUtilityBundle(BundleWidget->UtilityBundleAsset);
				return;
			}
		}
	}
	
	UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::OnItemClicked - Could not find utility bundle asset for clicked item"));
}

void UUtilityBundleSelectorWidget::HandleUtilityBundleItemClicked(UWorldBLDUtilityBundle* ClickedBundle)
{
	if (!ClickedBundle)
	{
		UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::HandleUtilityBundleItemClicked - ClickedBundle is null"));
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::HandleUtilityBundleItemClicked - Clicked bundle '%s' (PushWidgetToViewport=%s, WidgetClass=%s)"),
		*ClickedBundle->GetPathName(),
		ClickedBundle->PushWidgetToViewport ? TEXT("true") : TEXT("false"),
		ClickedBundle->WidgetClass ? *ClickedBundle->WidgetClass->GetPathName() : TEXT("<null>"));

	LaunchUtilityBundle(ClickedBundle);
}

void UUtilityBundleSelectorWidget::OnUtilityBundleClicked_Implementation(UWorldBLDUtilityBundle* ClickedBundle)
{
	LaunchUtilityBundle(ClickedBundle);
}

void UUtilityBundleSelectorWidget::LaunchUtilityBundle(UWorldBLDUtilityBundle* ClickedBundle)
{
	if (!ClickedBundle)
	{
		UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Received null ClickedBundle"));
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Begin for bundle '%s' (PushWidgetToViewport=%s)"),
		*ClickedBundle->GetPathName(),
		ClickedBundle->PushWidgetToViewport ? TEXT("true") : TEXT("false"));

	if (!IsValid(ClickedBundle->WidgetClass))
	{
		UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Invalid WidgetClass for bundle '%s'"),
			*ClickedBundle->GetPathName());
		return;
	}

	if (!ClickedBundle->PushWidgetToViewport)
	{
		// Non-viewport utilities are expected to open as standard editor utility tabs/windows.
		if (!GEditor)
		{
			UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - GEditor is null while opening non-viewport utility '%s'"),
				*ClickedBundle->GetPathName());
			return;
		}

		UEditorUtilitySubsystem* UtilitySubsystem = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();
		if (!UtilitySubsystem)
		{
			UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Missing UEditorUtilitySubsystem for %s"),
				*ClickedBundle->GetName());
			return;
		}

		UClass* WidgetClass = ClickedBundle->WidgetClass.Get();
		if (!WidgetClass)
		{
			UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - WidgetClass is null for %s"),
				*ClickedBundle->GetName());
			return;
		}

		UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Non-viewport launch class='%s' ClassGeneratedBy='%s'"),
			*WidgetClass->GetPathName(),
			WidgetClass->ClassGeneratedBy ? *WidgetClass->ClassGeneratedBy->GetPathName() : TEXT("<null>"));

		if (UWidgetBlueprintGeneratedClass* GeneratedWidgetClass = Cast<UWidgetBlueprintGeneratedClass>(WidgetClass))
		{
			UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Trying SpawnAndRegisterTabGeneratedClass with '%s'"),
				*GeneratedWidgetClass->GetPathName());

			if (UEditorUtilityWidget* SpawnedWidget = UtilitySubsystem->SpawnAndRegisterTabGeneratedClass(GeneratedWidgetClass))
			{
				UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - SpawnAndRegisterTabGeneratedClass succeeded for '%s'"),
					*GeneratedWidgetClass->GetPathName());
				return;
			}

			UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - SpawnAndRegisterTabGeneratedClass failed for %s"),
				*GeneratedWidgetClass->GetName());
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - WidgetClass '%s' is not a UWidgetBlueprintGeneratedClass"),
				*WidgetClass->GetPathName());
		}

		UEditorUtilityWidgetBlueprint* WidgetBlueprint = Cast<UEditorUtilityWidgetBlueprint>(WidgetClass->ClassGeneratedBy);
		if (WidgetBlueprint)
		{
			UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Resolved WidgetBlueprint from ClassGeneratedBy: '%s'"),
				*WidgetBlueprint->GetPathName());
		}

		// Fallback: resolve the blueprint asset from the generated class object path.
		// Some class references can lose a direct ClassGeneratedBy link, while the package path is still valid.
		if (!WidgetBlueprint)
		{
			const FString ClassObjectPath = WidgetClass->GetPathName();
			const FString BlueprintObjectPath = ClassObjectPath.EndsWith(TEXT("_C"))
				? ClassObjectPath.LeftChop(2)
				: FString();

			UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Fallback blueprint resolution from class path '%s' -> '%s'"),
				*ClassObjectPath,
				BlueprintObjectPath.IsEmpty() ? TEXT("<empty>") : *BlueprintObjectPath);

			if (!BlueprintObjectPath.IsEmpty())
			{
				WidgetBlueprint = LoadObject<UEditorUtilityWidgetBlueprint>(nullptr, *BlueprintObjectPath);
				UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - LoadObject fallback %s for '%s'"),
					WidgetBlueprint ? TEXT("succeeded") : TEXT("failed"),
					*BlueprintObjectPath);
			}
		}

		if (WidgetBlueprint)
		{
			UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Trying SpawnAndRegisterTab with blueprint '%s'"),
				*WidgetBlueprint->GetPathName());

			if (UEditorUtilityWidget* SpawnedWidget = UtilitySubsystem->SpawnAndRegisterTab(WidgetBlueprint))
			{
				UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - SpawnAndRegisterTab succeeded for '%s'"),
					*WidgetBlueprint->GetPathName());
				return;
			}

			UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - SpawnAndRegisterTab failed for %s"),
				*WidgetBlueprint->GetName());
			return;
		}

		UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Could not resolve an editor utility blueprint from WidgetClass %s"),
			*WidgetClass->GetPathName());
		return;
	}

	// Create the widget in the editor world (mirrors UWorldBLDEdMode::TryConstructUserWidget).
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Editor world is null for viewport utility '%s'"),
			*ClickedBundle->GetPathName());
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - Viewport launch path for class '%s'"),
		*ClickedBundle->WidgetClass->GetPathName());

	UEditorUtilityWidget* UtilityWidget = CreateWidget<UEditorUtilityWidget>(World, ClickedBundle->WidgetClass);
	if (!IsValid(UtilityWidget))
	{
		UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleSelectorWidget::LaunchUtilityBundle - CreateWidget failed for class '%s'"),
			*ClickedBundle->WidgetClass->GetPathName());
		return;
	}

	// Mark transient to prevent dirtying the editor world.
	UtilityWidget->SetFlags(RF_Transient);

	// Also mark nested utility widgets as transient (see UWorldBLDEdMode::TryConstructUserWidget).
	if (UtilityWidget->WidgetTree)
	{
		TArray<UWidget*> AllWidgets;
		UtilityWidget->WidgetTree->GetAllWidgets(AllWidgets);
		for (UWidget* Widget : AllWidgets)
		{
			if (Widget && Widget->IsA(UEditorUtilityWidget::StaticClass()))
			{
				Widget->SetFlags(RF_Transient);
				if (Widget->Slot)
				{
					Widget->Slot->SetFlags(RF_Transient);
				}
			}
		}
	}

	// Utilities that are also WorldBLD tools should be pushed via the EdMode tool stack.
	if (UWorldBLDEditController* ToolController = Cast<UWorldBLDEditController>(UtilityWidget))
	{
		if (UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
		{
			EdMode->PushEditController(ToolController);
		}
		else
		{
			// Fallback for cases where the EdMode isn't active, but we still want to display the tool in-viewport.
			ToolController->AddToEditorLevelViewport();
			ToolController->ToolBegin();
		}
	}
}

