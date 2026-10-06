// Copyright WorldBLD LLC. All Rights Reserved.

#include "WorldBLDEditorModule.h"
#include "WorldBLDContextMenuRegistry.h"

#include "ContextMenu/SWorldBLDContextMenu.h"
#include "ContextMenu/SWorldBLDContextMenuViewportOverlay.h"
#include "IWorldBLDContextMenuFactory.h"

#include "Interfaces/IPluginManager.h"

#include "WorldBLDEditorToolkit.h"
#include "CallInEditorAssetActions.h"
#include "AssetLibrary/WorldBLDAssetLibraryWindow.h"
#include "LandscapePaint/WorldBLDLandscapePaintLayerCustomization.h"

#include "LevelTemplate/SWorldBLDLightingPresetDialog.h"
#include "LevelTemplate/WorldBLDLevelTemplateWindow.h"

#include "WorldBLDLevelTemplateBlueprintLibrary.h"
#include "WorldBLDLevelTemplateBundle.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/IConsoleManager.h"
#include "LevelEditor.h"
#include "LevelEditorSubsystem.h"
#include "SLevelViewport.h"

#include "Editor.h"
#include "Engine/Selection.h"
#include "FileHelpers.h"
#include "ScopedTransaction.h"
#include "Engine/Level.h"
#include "Engine/LevelScriptActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "ContentBrowserModule.h"
#include "IContentBrowserSingleton.h"
#include "Framework/Notifications/NotificationManager.h"
#include "GameFramework/Actor.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/MessageDialog.h"
#include "PropertyEditorModule.h"
#include "Widgets/Notifications/SNotificationList.h"

DEFINE_LOG_CATEGORY(LogWorldBuild)
FOnOpenBuildingMeshCreatorRequested FWorldBLDEditorModule::OpenBuildingMeshCreatorDelegate;
FOnOpenBuildingStyleCreatorRequested FWorldBLDEditorModule::OpenBuildingStyleCreatorDelegate;
FOnOpenGroundFloorCreatorRequested FWorldBLDEditorModule::OpenGroundFloorCreatorDelegate;
FOnPopulateWorldBLDMenuExtensions FWorldBLDEditorModule::WorldBLDMenuExtensions;

#define LOCTEXT_NAMESPACE "WorldBLDEditorModule"

void FWorldBLDEditorModule::StartupModule()
{
	RegisterCustomizations();

	ExtendLevelEditorMenu();
	ExtendFileMenu();

	LevelTemplateSelectedHandle = FWorldBLDLevelTemplateWindow::OnLevelTemplateSelected().AddRaw(this, &FWorldBLDEditorModule::HandleLevelTemplateSelected);

	FCallInEditorAssetActions::InstallHooks();

	ContextManagerPtr = MakeWeakObjectPtr(const_cast<UUtilsEditorContext_Manager*>(GetDefault<UUtilsEditorContext_Manager>()));
	ContextMenuRegistryPtr = UWorldBLDContextMenuRegistry::Get();
	// Context menu window manager is stateless, no initialization needed
	UE_LOG(LogWorldBuild, Log, TEXT("Context menu registry initialized"));
	IConsoleManager::Get().RegisterConsoleCommand(
		TEXT("WorldBLD.TestContextMenu"),
		TEXT("Spawn a WorldBLD context menu for the currently selected actor."),
		FConsoleCommandDelegate::CreateRaw(this, &FWorldBLDEditorModule::HandleTestContextMenuCommand),
		ECVF_Default);

	{
		FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
		IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();
		if (!AssetRegistry.IsLoadingAssets())
		{
			ScanContentForLevelTemplateBundles();
		}
		else
		{
			AssetRegistryLevelTemplatesFilesLoadedHandle = AssetRegistry.OnFilesLoaded().AddRaw(this, &FWorldBLDEditorModule::ScanContentForLevelTemplateBundles);
		}
	}

	//@TODO: This code is looking for the WorldBLD plugin to find the edmode class, we need to set up the WorldBLD plugin's content folder
	if (UWorldBLDEdModeSettings* Settings = GetMutableDefault<UWorldBLDEdModeSettings>())
	{
		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("WorldBLD"));
		const FString BasePluginDir = FPaths::GetPath(Plugin->GetContentDir());
		const FString ConfigFilePath = FConfigCacheIni::NormalizeConfigIniPath(BasePluginDir / "Config" / "DefaultWorldBLD.ini");
		Settings->LoadConfig(nullptr, *ConfigFilePath);

		TSubclassOf<UWorldBLDEdMode> ResolvedEdModeClass;
		if (!Settings->EditModeClass.IsNull())
		{
			ResolvedEdModeClass = Settings->EditModeClass.LoadSynchronous();
		}

		// Compatibility fallback: projects may still reference old BP_*_EdMode classes from older plugin packs.
		// If that class is missing or non-native, force the native mode class for this session.
		if ((ResolvedEdModeClass == nullptr) || !ResolvedEdModeClass->IsNative())
		{
			static bool bLoggedEditModeFallback = false;
			if (!bLoggedEditModeFallback)
			{
				UE_LOG(
					LogWorldBuild,
					Warning,
					TEXT("WorldBLD EditModeClass is stale/invalid ('%s'). Falling back to native /Script/WorldBLDEditor.WorldBLDEdMode."),
					*Settings->EditModeClass.ToString());
				bLoggedEditModeFallback = true;
			}

			Settings->EditModeClass = UWorldBLDEdMode::StaticClass();
			ResolvedEdModeClass = UWorldBLDEdMode::StaticClass();
		}

		if (ResolvedEdModeClass != nullptr)
		{
			if (UWorldBLDEdMode* CDO = Cast<UWorldBLDEdMode>(ResolvedEdModeClass->GetDefaultObject()))
			{
				// Make sure we handle gracefully recompiling this blueprint so we don't crash the editor.
				CDO->InstallDefaultRecompileHandler();
			}
		}
	}
}

void FWorldBLDEditorModule::ShutdownModule()
{
	UnregisterCustomizations();

	FCallInEditorAssetActions::RemoveHooks();

	IConsoleManager::Get().UnregisterConsoleObject(TEXT("WorldBLD.TestContextMenu"), false);

	if (LevelTemplateSelectedHandle.IsValid())
	{
		FWorldBLDLevelTemplateWindow::OnLevelTemplateSelected().Remove(LevelTemplateSelectedHandle);
		LevelTemplateSelectedHandle.Reset();
	}

	if (AssetLibraryMenuExtender.IsValid() && FModuleManager::Get().IsModuleLoaded(TEXT("LevelEditor")))
	{
		FLevelEditorModule& LevelEditorModule = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
		LevelEditorModule.GetMenuExtensibilityManager()->RemoveExtender(AssetLibraryMenuExtender);
		AssetLibraryMenuExtender.Reset();
	}

	if (FileMenuExtender.IsValid() && FModuleManager::Get().IsModuleLoaded(TEXT("LevelEditor")))
	{
		FLevelEditorModule& LevelEditorModule = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
		LevelEditorModule.GetMenuExtensibilityManager()->RemoveExtender(FileMenuExtender);
		FileMenuExtender.Reset();
	}

	if (FModuleManager::Get().IsModuleLoaded(TEXT("AssetRegistry")))
	{
		FAssetRegistryModule& AssetRegistryModule = FModuleManager::GetModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
		AssetRegistryModule.Get().OnFilesLoaded().Remove(AssetRegistryLevelTemplatesFilesLoadedHandle);
	}

	ContextMenuRegistryPtr = nullptr;
	ContextManagerPtr = nullptr;
}

UWorldBLDContextMenuRegistry* FWorldBLDEditorModule::GetContextMenuRegistry()
{
	if (!ContextMenuRegistryPtr.IsValid())
	{
		ContextMenuRegistryPtr = UWorldBLDContextMenuRegistry::Get();
	}

	return ContextMenuRegistryPtr.Get();
}

void FWorldBLDEditorModule::CreateAndShowContextMenu(AActor* Actor)
{
	if (!GEditor)
	{
		return;
	}

	// Clear previous test overlay (if any).
	if (TestContextMenuOverlayWidget.IsValid())
	{
		if (TSharedPtr<SLevelViewport> PinnedHostViewport = TestContextMenuHostViewport.Pin())
		{
			PinnedHostViewport->RemoveOverlayWidget(TestContextMenuOverlayWidget.ToSharedRef());
		}
		TestContextMenuOverlayWidget.Reset();
		TestContextMenuHostViewport.Reset();
	}

	AActor* Target = Actor;
	if (!IsValid(Target))
	{
		USelection* SelectedActors = GEditor->GetSelectedActors();
		if (SelectedActors)
		{
			for (FSelectionIterator It(*SelectedActors); It; ++It)
			{
				Target = Cast<AActor>(*It);
				if (IsValid(Target))
				{
					break;
				}
			}
		}
	}

	if (!IsValid(Target))
	{
		return;
	}

	UWorldBLDContextMenuRegistry* Registry = GetContextMenuRegistry();
	if (!IsValid(Registry))
	{
		return;
	}

	const TScriptInterface<IWorldBLDContextMenuFactory> Factory = Registry->FindFactoryForActor(Target);
	if (!Factory)
	{
		return;
	}

	if (!Factory->CanCreateContextMenuForActor(Target))
	{
		return;
	}

	FLevelEditorModule& LevelEditorModule = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
	const TSharedPtr<ILevelEditor> PinnedEditor = LevelEditorModule.GetLevelEditorInstance().Pin();
	if (!PinnedEditor.IsValid())
	{
		return;
	}

	const TSharedPtr<SLevelViewport> ActiveViewport = PinnedEditor->GetActiveViewportInterface();
	if (!ActiveViewport.IsValid())
	{
		return;
	}

	const TSharedRef<SWidget> MenuContent = Factory->CreateContextMenuWidget(Target);
	const FText Title = FText::FromString(Target->GetActorLabel());

	const TSharedRef<SWorldBLDContextMenu> ContextMenu =
		SNew(SWorldBLDContextMenu)
		.Title(Title)
		.Content(MenuContent)
		.TargetActor(Target);

	const TSharedRef<SWorldBLDContextMenuViewportOverlay> Overlay =
		SNew(SWorldBLDContextMenuViewportOverlay)
		.Padding(FMargin(24.0f))
		.Panel(ContextMenu);

	ActiveViewport->AddOverlayWidget(Overlay);
	TestContextMenuHostViewport = ActiveViewport;
	TestContextMenuOverlayWidget = Overlay;
}

void FWorldBLDEditorModule::HandleTestContextMenuCommand()
{
	if (TestContextMenuOverlayWidget.IsValid())
	{
		if (TSharedPtr<SLevelViewport> PinnedHostViewport = TestContextMenuHostViewport.Pin())
		{
			PinnedHostViewport->RemoveOverlayWidget(TestContextMenuOverlayWidget.ToSharedRef());
		}
		TestContextMenuOverlayWidget.Reset();
		TestContextMenuHostViewport.Reset();
		return;
	}

	CreateAndShowContextMenu(nullptr);
}

void FWorldBLDEditorModule::HandleLevelTemplateSelected(UWorldBLDLevelTemplateBundle* Bundle)
{
	if (!IsValid(Bundle))
	{
		return;
	}

	auto Notify = [](const FText& Message, SNotificationItem::ECompletionState State)
	{
		FNotificationInfo Info(Message);
		Info.ExpireDuration = 5.0f;
		Info.bFireAndForget = true;
		TSharedPtr<SNotificationItem> Item = FSlateNotificationManager::Get().AddNotification(Info);
		if (Item.IsValid())
		{
			Item->SetCompletionState(State);
		}
	};

	TArray<FString> PresetNames;
	Bundle->CompatibleLightingPresets.GetKeys(PresetNames);
	PresetNames.Sort();

	TOptional<FString> SelectedPresetName;
	if (PresetNames.Num() > 0)
	{
		SelectedPresetName = SWorldBLDLightingPresetDialog::ShowModal(PresetNames, Bundle->DefaultLightingTemplate);
		if (!SelectedPresetName.IsSet())
		{
			return;
		}
	}

	if (Bundle->TemplateLevel.IsNull())
	{
		Notify(LOCTEXT("LevelTemplate_MissingTemplate", "Template level is not set."), SNotificationItem::CS_Fail);
		return;
	}

	const FSoftObjectPath TemplateWorldPath = Bundle->TemplateLevel.ToSoftObjectPath();
	if (!TemplateWorldPath.IsValid())
	{
		Notify(LOCTEXT("LevelTemplate_InvalidTemplatePath", "Template level path is invalid."), SNotificationItem::CS_Fail);
		return;
	}

	TSoftObjectPtr<UWorld> PresetWorld;
	if (SelectedPresetName.IsSet())
	{
		const TSoftObjectPtr<UWorld>* PresetWorldPtr = Bundle->CompatibleLightingPresets.Find(*SelectedPresetName);
		if (!PresetWorldPtr)
		{
			Notify(LOCTEXT("LevelTemplate_PresetMissing", "Selected lighting preset is missing."), SNotificationItem::CS_Fail);
			return;
		}

		PresetWorld = *PresetWorldPtr;
		if (PresetWorld.IsNull() || !PresetWorld.ToSoftObjectPath().IsValid())
		{
			Notify(LOCTEXT("LevelTemplate_InvalidPresetPath", "Lighting preset level path is invalid."), SNotificationItem::CS_Fail);
			return;
		}
	}

	if (!GEditor)
	{
		Notify(LOCTEXT("LevelTemplate_NoEditor", "Editor is not available."), SNotificationItem::CS_Fail);
		return;
	}

	FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>(TEXT("ContentBrowser"));
	FSaveAssetDialogConfig SaveAssetDialogConfig;
	SaveAssetDialogConfig.DialogTitleOverride = LOCTEXT("LevelTemplate_SaveNewLevel", "Create Level from Template");
	SaveAssetDialogConfig.DefaultPath = TEXT("/Game");
	SaveAssetDialogConfig.DefaultAssetName = Bundle->TemplateName.IsEmpty() ? TEXT("NewLevel") : Bundle->TemplateName;
	SaveAssetDialogConfig.AssetClassNames.Add(UWorld::StaticClass()->GetClassPathName());

	const FString NewLevelObjectPath = ContentBrowserModule.Get().CreateModalSaveAssetDialog(SaveAssetDialogConfig);
	if (NewLevelObjectPath.IsEmpty())
	{
		return;
	}

	const FString NewLevelPackagePath = FPackageName::ObjectPathToPackageName(NewLevelObjectPath);
	const FString TemplateLevelPackagePath = TemplateWorldPath.GetLongPackageName();
	if (TemplateLevelPackagePath.IsEmpty())
	{
		Notify(LOCTEXT("LevelTemplate_InvalidTemplatePath", "Template level path is invalid."), SNotificationItem::CS_Fail);
		return;
	}

	bool bCreatedNewLevel = false;
	if (ULevelEditorSubsystem* LevelEditorSubsystem = GEditor->GetEditorSubsystem<ULevelEditorSubsystem>())
	{
		bCreatedNewLevel = LevelEditorSubsystem->NewLevelFromTemplate(NewLevelPackagePath, TemplateLevelPackagePath);
	}

	if (!bCreatedNewLevel)
	{
		Notify(LOCTEXT("LevelTemplate_NewLevelFailed", "Failed to create new level from template."), SNotificationItem::CS_Fail);
		return;
	}

	UWorld* NewWorld = GEditor->GetEditorWorldContext().World();
	if (!IsValid(NewWorld))
	{
		Notify(LOCTEXT("LevelTemplate_NewWorldInvalid", "New level was created but could not be loaded."), SNotificationItem::CS_Fail);
		return;
	}

	if (!PresetWorld.IsNull())
	{
		UWorldBLDLevelTemplateBlueprintLibrary::LoadLightingPresetFromSoftWorld(NewWorld, PresetWorld);
		NewWorld->MarkPackageDirty();
	}

	Notify(LOCTEXT("LevelTemplate_Success", "Created level from template."), SNotificationItem::CS_Success);
	FWorldBLDLevelTemplateWindow::CloseLevelTemplateWindow();
}

void FWorldBLDEditorModule::ScanContentForLevelTemplateBundles()
{
    for (int32 Index = AvailableLevelTemplateBundles.Num() - 1; Index >= 0; --Index)
    {
        if (!AvailableLevelTemplateBundles[Index].IsValid())
        {
            AvailableLevelTemplateBundles.RemoveAt(Index);
        }
    }

    const int32 PreviousCount = AvailableLevelTemplateBundles.Num();

    FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
    IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();
    if (AssetRegistry.IsLoadingAssets())
    {
        return;
    }

    FARFilter Filter;
    Filter.ClassPaths.Add(UWorldBLDLevelTemplateBundle::StaticClass()->GetClassPathName());
    Filter.bRecursiveClasses = true;
    Filter.bRecursivePaths = true;

    TArray<FAssetData> AssetDataList;
    AssetRegistry.GetAssets(Filter, AssetDataList);
    UE_LOG(LogWorldBuild, Verbose, TEXT("ScanContentForLevelTemplateBundles: FoundAssets=%d"), AssetDataList.Num());

    for (const FAssetData& AssetData : AssetDataList)
    {
        UWorldBLDLevelTemplateBundle* LevelTemplateBundle = Cast<UWorldBLDLevelTemplateBundle>(AssetData.GetAsset());
        if (IsValid(LevelTemplateBundle))
        {
            AvailableLevelTemplateBundles.AddUnique(LevelTemplateBundle);
        }
    }

    for (int32 Index = 0; Index < FMath::Min(AssetDataList.Num(), 10); ++Index)
    {
        UE_LOG(LogWorldBuild, Verbose, TEXT("ScanContentForLevelTemplateBundles: Asset[%d]=%s"), Index, *AssetDataList[Index].GetObjectPathString());
    }

    if (AvailableLevelTemplateBundles.Num() != PreviousCount)
    {
        OnAvailableLevelTemplateBundlesChanged.Broadcast();
    }
}

FString FWorldBLDEditorModule::GetModuleName()
{
    return TEXT("WorldBLDEditor");
}

FOnPopulateWorldBLDMenuExtensions& FWorldBLDEditorModule::GetWorldBLDMenuExtensions()
{
	return WorldBLDMenuExtensions;
}

void FWorldBLDEditorModule::SetOpenBuildingMeshCreatorDelegate(FOnOpenBuildingMeshCreatorRequested InDelegate)
{
	OpenBuildingMeshCreatorDelegate = MoveTemp(InDelegate);
}

void FWorldBLDEditorModule::ClearOpenBuildingMeshCreatorDelegate()
{
	OpenBuildingMeshCreatorDelegate.Unbind();
}

void FWorldBLDEditorModule::SetOpenBuildingStyleCreatorDelegate(FOnOpenBuildingStyleCreatorRequested InDelegate)
{
	OpenBuildingStyleCreatorDelegate = MoveTemp(InDelegate);
}

void FWorldBLDEditorModule::ClearOpenBuildingStyleCreatorDelegate()
{
	OpenBuildingStyleCreatorDelegate.Unbind();
}

void FWorldBLDEditorModule::SetOpenGroundFloorCreatorDelegate(FOnOpenGroundFloorCreatorRequested InDelegate)
{
	OpenGroundFloorCreatorDelegate = MoveTemp(InDelegate);
}

void FWorldBLDEditorModule::ClearOpenGroundFloorCreatorDelegate()
{
	OpenGroundFloorCreatorDelegate.Unbind();
}

bool FWorldBLDEditorModule::CanOpenBuildingMeshCreator()
{
	return OpenBuildingMeshCreatorDelegate.IsBound();
}

bool FWorldBLDEditorModule::CanOpenBuildingStyleCreator()
{
	return OpenBuildingStyleCreatorDelegate.IsBound();
}

bool FWorldBLDEditorModule::CanOpenGroundFloorCreator()
{
	return OpenGroundFloorCreatorDelegate.IsBound();
}

void FWorldBLDEditorModule::OpenBuildingMeshCreator()
{
	if (OpenBuildingMeshCreatorDelegate.IsBound())
	{
		OpenBuildingMeshCreatorDelegate.Execute();
		return;
	}

	FMessageDialog::Open(
		EAppMsgType::Ok,
		LOCTEXT("BuildingMeshCreatorUnavailable", "The Building Mesh Creator is currently unavailable because the CityBLD editor module has not registered it yet."));
}

void FWorldBLDEditorModule::OpenBuildingStyleCreator()
{
	if (OpenBuildingStyleCreatorDelegate.IsBound())
	{
		OpenBuildingStyleCreatorDelegate.Execute();
		return;
	}

	FMessageDialog::Open(
		EAppMsgType::Ok,
		LOCTEXT("BuildingStyleCreatorUnavailable", "The Building Style Creator is currently unavailable because the CityBLD editor module has not registered it yet."));
}

void FWorldBLDEditorModule::OpenGroundFloorCreator()
{
	if (OpenGroundFloorCreatorDelegate.IsBound())
	{
		OpenGroundFloorCreatorDelegate.Execute();
		return;
	}

	FMessageDialog::Open(
		EAppMsgType::Ok,
		LOCTEXT("GroundFloorCreatorUnavailable", "The Ground Floor Creator is currently unavailable because the CityBLD editor module has not registered it yet."));
}

void FWorldBLDEditorModule::ExtendLevelEditorMenu()
{
    FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));

    AssetLibraryMenuExtender = MakeShared<FExtender>();
    AssetLibraryMenuExtender->AddMenuBarExtension(
        "Window",
        EExtensionHook::After,
        nullptr,
        FMenuBarExtensionDelegate::CreateRaw(this, &FWorldBLDEditorModule::AddWorldBLDMenuBarExtension));

    LevelEditorModule.GetMenuExtensibilityManager()->AddExtender(AssetLibraryMenuExtender);
}

void FWorldBLDEditorModule::AddWorldBLDMenuBarExtension(FMenuBarBuilder& MenuBarBuilder)
{
    MenuBarBuilder.AddPullDownMenu(
        LOCTEXT("WorldBLDMenu", "WorldBLD"),
        LOCTEXT("WorldBLDMenu_Tooltip", "WorldBLD tools"),
        FNewMenuDelegate::CreateRaw(this, &FWorldBLDEditorModule::PopulateWorldBLDMenu),
        "WorldBLD");
}

void FWorldBLDEditorModule::PopulateWorldBLDMenu(FMenuBuilder& MenuBuilder)
{
	MenuBuilder.AddMenuEntry(
		LOCTEXT("OpenAssetLibrary", "Open Asset Library"),
		LOCTEXT("OpenAssetLibrary_Tooltip", "Open the WorldBLD Asset Library window"),
		FSlateIcon(),
		FUIAction(FExecuteAction::CreateStatic(&FWorldBLDAssetLibraryWindow::OpenAssetLibrary)));

	MenuBuilder.AddMenuEntry(
		LOCTEXT("OpenBuildingStyleCreator", "Open Building Style Creator..."),
		LOCTEXT("OpenBuildingStyleCreator_Tooltip", "Open the CityBLD Building Style Creator window"),
		FSlateIcon(),
		FUIAction(
			FExecuteAction::CreateStatic(&FWorldBLDEditorModule::OpenBuildingStyleCreator),
			FCanExecuteAction::CreateStatic(&FWorldBLDEditorModule::CanOpenBuildingStyleCreator)));

	MenuBuilder.AddMenuEntry(
		LOCTEXT("OpenBuildingMeshCreator", "Open Building Mesh Creator..."),
		LOCTEXT("OpenBuildingMeshCreator_Tooltip", "Open the CityBLD Building Mesh Creator window"),
		FSlateIcon(),
		FUIAction(
			FExecuteAction::CreateStatic(&FWorldBLDEditorModule::OpenBuildingMeshCreator),
			FCanExecuteAction::CreateStatic(&FWorldBLDEditorModule::CanOpenBuildingMeshCreator)));

	MenuBuilder.AddMenuEntry(
		LOCTEXT("OpenGroundFloorCreator", "Open Ground Floor Creator..."),
		LOCTEXT("OpenGroundFloorCreator_Tooltip", "Open the CityBLD Ground Floor Creator window"),
		FSlateIcon(),
		FUIAction(
			FExecuteAction::CreateStatic(&FWorldBLDEditorModule::OpenGroundFloorCreator),
			FCanExecuteAction::CreateStatic(&FWorldBLDEditorModule::CanOpenGroundFloorCreator)));

	MenuBuilder.AddMenuEntry(
		LOCTEXT("OpenLevelTemplates", "Open Level Templates..."),
		LOCTEXT("OpenLevelTemplates_Tooltip", "Open the Level Template selection window"),
		FSlateIcon(),
		FUIAction(FExecuteAction::CreateStatic(&FWorldBLDLevelTemplateWindow::OpenLevelTemplateWindow)));

	MenuBuilder.AddMenuEntry(
		LOCTEXT("CheckForToolUpdates", "Check for Tool Updates"),
		LOCTEXT("CheckForToolUpdates_Tooltip", "Fetch the latest tool list from the server"),
		FSlateIcon(),
		FUIAction(FExecuteAction::CreateLambda([]()
		{
			if (UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
			{
				EdMode->RefreshAvailableToolsFromServer();
			}
		})));

	WorldBLDMenuExtensions.Broadcast(MenuBuilder);
}

void FWorldBLDEditorModule::ExtendFileMenu()
{
	FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));

	FileMenuExtender = MakeShared<FExtender>();
	FileMenuExtender->AddMenuExtension(
		"FileNew",
		EExtensionHook::After,
		nullptr,
		FMenuExtensionDelegate::CreateRaw(this, &FWorldBLDEditorModule::AddLevelTemplateFileMenuItem));

	LevelEditorModule.GetMenuExtensibilityManager()->AddExtender(FileMenuExtender);
}

void FWorldBLDEditorModule::AddLevelTemplateFileMenuItem(FMenuBuilder& MenuBuilder)
{
	MenuBuilder.AddMenuEntry(
		LOCTEXT("NewLevelFromTemplate", "New Level from Template..."),
		LOCTEXT("NewLevelFromTemplate_Tooltip", "Create a new level using a WorldBLD Level Template"),
		FSlateIcon(),
		FUIAction(FExecuteAction::CreateStatic(&FWorldBLDLevelTemplateWindow::OpenLevelTemplateWindow)));
}

void FWorldBLDEditorModule::RegisterCustomizations()
{
	FPropertyEditorModule& PropertyEditorModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>(TEXT("PropertyEditor"));
	PropertyEditorModule.RegisterCustomPropertyTypeLayout(
		TEXT("WorldBLDLandscapePaintLayer"),
		FOnGetPropertyTypeCustomizationInstance::CreateStatic(&FWorldBLDLandscapePaintLayerCustomization::MakeInstance));
	PropertyEditorModule.NotifyCustomizationModuleChanged();
}

void FWorldBLDEditorModule::UnregisterCustomizations()
{
	if (!FModuleManager::Get().IsModuleLoaded(TEXT("PropertyEditor")))
	{
		return;
	}

	FPropertyEditorModule& PropertyEditorModule = FModuleManager::GetModuleChecked<FPropertyEditorModule>(TEXT("PropertyEditor"));
	PropertyEditorModule.UnregisterCustomPropertyTypeLayout(TEXT("WorldBLDLandscapePaintLayer"));
	PropertyEditorModule.NotifyCustomizationModuleChanged();
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FWorldBLDEditorModule, WorldBLDEditor)