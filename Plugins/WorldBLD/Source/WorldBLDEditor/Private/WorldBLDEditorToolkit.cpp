// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDEditorToolkit.h"
#include "WorldBLDEditController.h"
#include "WorldBLDDefaultEditController.h"
#include "WorldBLDToolPaletteWidget.h"

#include "WorldBLDEditorModule.h"
#include "WorldBLDToolUpdateSettings.h"
#include "WorldBLDContextMenuRegistry.h"

#include "ContextMenu/SWorldBLDContextMenu.h"
#include "ContextMenu/SWorldBLDContextMenuViewportOverlay.h"
#include "ContextMenu/SWorldBLDWarningTooltipOverlay.h"
#include "IWorldBLDContextMenuFactory.h"
#include "IWorldBLDContextMenuProvider.h"

#include "ViewportToolbar/WorldBLDToolbarProvider.h"
#include "SLevelViewport.h"
#include "Editor.h"
#include "TimerManager.h"

#include "EditorModeManager.h"
#include "EditorUtilityWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/Text/STextBlock.h"
#include "LevelEditor.h"
#include "LevelEditorSubsystem.h"
#include "LevelEditorViewport.h"
#include "Engine/Selection.h"
#include "Editor/Transbuffer.h"

#include "ActorFactories/ActorFactory.h"
#include "Builders/CubeBuilder.h"
#include "Engine/PostProcessVolume.h"
#include "EngineUtils.h"
#include "HttpModule.h"
#include "Misc/App.h"
#include "Misc/EngineVersion.h"
#include "Misc/PackageName.h"
#include "ScopedTransaction.h"
#include "Dialogs/Dialogs.h"
#include "UObject/SoftObjectPath.h"
#include "Styling/AppStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Notifications/SProgressBar.h"
#include "Widgets/SWindow.h"
#include "Downloader/CurlDownloaderLibrary.h"

#include "Toolkits/AssetEditorModeUILayer.h"
#include "Input/HittestGrid.h"
#include "PrimitiveDrawWrapper.h"

#include "Framework/Docking/SDockingTabStack.h" // Tab stack APIs used for sidebar/tab-well behavior
#include "Framework/Docking/SDockingArea.h"
#include "Authorization/WorldBLDAuthSubsystem.h"
#include "Framework/Notifications/NotificationManager.h"
#include "Interfaces/IPluginManager.h"
#include "Interfaces/IHttpResponse.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "Framework/Application/SlateApplication.h"
#include "LevelEditor.h"
#include "SLevelViewport.h"
#include "Utilities/UtilitiesLibrary.h"
#include "FileHelpers.h"
#include "Containers/Ticker.h"
///////////////////////////////////////////////////////////////////////////////////////////////////

#define LOCTEXT_NAMESPACE "WorldBLDEditorToolkit"

///////////////////////////////////////////////////////////////////////////////////////////////////

namespace WorldBLDEditorContextMenu
{
	static bool IsResolvableClassPackage(const FString& PackageName)
	{
		return PackageName.IsEmpty() || FPackageName::IsScriptPackage(PackageName) || FPackageName::DoesPackageExist(PackageName);
	}

	static const UWorldBLDEditorUISettings* GetUISettings()
	{
		return GetDefault<UWorldBLDEditorUISettings>();
	}

	static FString GetWorldBLDEditorPluginVersionString()
	{
		if (const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().GetModuleOwnerPlugin(*FWorldBLDEditorModule::GetModuleName()))
		{
			return Plugin->GetDescriptor().VersionName;
		}
		return TEXT("0.0.0");
	}

	// Parses a "Major.Minor.Patch" version string into its integer components.
	static bool TryParseVersionTriplet(const FString& VersionString, int32& OutMajor, int32& OutMinor, int32& OutPatch)
	{
		TArray<FString> Parts;
		VersionString.ParseIntoArray(Parts, TEXT("."));
		if (Parts.Num() < 3 || !Parts[0].IsNumeric() || !Parts[1].IsNumeric() || !Parts[2].IsNumeric())
		{
			return false;
		}
		OutMajor = FCString::Atoi(*Parts[0]);
		OutMinor = FCString::Atoi(*Parts[1]);
		OutPatch = FCString::Atoi(*Parts[2]);
		return true;
	}

	// Returns true when the LHS version is strictly less than the given threshold.
	static bool IsVersionBelow(int32 LhsMajor, int32 LhsMinor, int32 LhsPatch, int32 ThreshMajor, int32 ThreshMinor, int32 ThreshPatch)
	{
		if (LhsMajor != ThreshMajor) { return LhsMajor < ThreshMajor; }
		if (LhsMinor != ThreshMinor) { return LhsMinor < ThreshMinor; }
		return LhsPatch < ThreshPatch;
	}

	static UClass* ResolveDefaultToolClass(const UWorldBLDEdMode* EdMode)
	{
		if (EdMode == nullptr)
		{
			return UWorldBLDDefaultEditController::StaticClass();
		}

		// Prefer the already-loaded class (fast path).
		if (UClass* Loaded = EdMode->DefaultToolClass.Get())
		{
			return Loaded;
		}

		// If configured but not loaded yet, load synchronously (editor-only).
		if (!EdMode->DefaultToolClass.IsNull())
		{
			const FSoftObjectPath ToolClassPath = EdMode->DefaultToolClass.ToSoftObjectPath();
			const FString ToolClassPackageName = ToolClassPath.GetLongPackageName();
			if (!IsResolvableClassPackage(ToolClassPackageName))
			{
				return UWorldBLDDefaultEditController::StaticClass();
			}

			if (UClass* Loaded = EdMode->DefaultToolClass.LoadSynchronous())
			{
				return Loaded;
			}
		}

		return UWorldBLDDefaultEditController::StaticClass();
	}

	static bool IsControllerAllowedToShowContextMenu(const UWorldBLDEdMode* EdMode, const UWorldBLDEditController* Controller)
	{
		// If we don't have an active controller, allow context menus (selection-driven behavior).
		if ((EdMode == nullptr) || !IsValid(Controller))
		{
			return true;
		}

		// Always allow the configured default controller (including BP subclasses).
		if (Controller->IsA(ResolveDefaultToolClass(EdMode)))
		{
			return true;
		}

		// Legacy palette-driven exemptions were removed as part of the toolbar migration.
		// Keep the setting for one release cycle, but route to controller-based exemptions.
		return EdMode->IsContextMenuControllerExempt(Controller);
	}

	static bool IsControllerAllowedToShowViewportToolbar(const UWorldBLDEdMode* EdMode, const UWorldBLDEditController* Controller)
	{
		// Keep the toolbar visible when no controller is active.
		if ((EdMode == nullptr) || !IsValid(Controller))
		{
			return true;
		}

		// Only the configured default controller keeps the toolbar visible.
		return Controller->IsA(ResolveDefaultToolClass(EdMode));
	}
}

class FWorldBLDSelectModeWidgetHelper;
const FEditorModeID UWorldBLDEdMode::EditorModeID(TEXT("WorldBLDEditorMode"));

DEFINE_LOG_CATEGORY(LogWorldBLDEditor);

///////////////////////////////////////////////////////////////////////////////////////////////////

// SEE: DefaultEdMode.cpp
class FWorldBLDSelectModeWidgetHelper : public FLegacyEdModeWidgetHelper
{
	using Super = FLegacyEdModeWidgetHelper;
public:
	virtual bool AllowWidgetMove() override;
	virtual bool CanCycleWidgetMode() const override;
	virtual bool ShowModeWidgets() const override;
	virtual bool ShouldDrawWidget() const override;
	virtual bool UsesTransformWidget() const override;
	virtual bool UsesPropertyWidgets() const override;
    virtual EAxisList::Type GetWidgetAxisToDraw(UE::Widget::EWidgetMode CheckMode) const override;
    virtual FVector GetWidgetLocation() const override;

	virtual void ActorSelectionChangeNotify() override; // testing only

	UWorldBLDEditController* GetActiveController() const;
};

///////////////////////////////////////////////////////////////////////////////////////////////////

UWorldBLDEdMode::UWorldBLDEdMode()
{
	// Only the native C++ class is the real registered editor mode. Any Blueprint subclass (skeleton
	// or generated) is treated as a dummy/invisible template so a stray legacy BP_*_EdMode asset can
	// never register a second mode under the shared EditorModeID and clobber the native one.
	const bool bIsBlueprintTemplate = !GetClass()->IsNative();
    Info = FEditorModeInfo(
        bIsBlueprintTemplate ? FEditorModeID(TEXT("WorldBLDEditorMode_Dummy")) : EditorModeID,
		NSLOCTEXT("WorldBLDEditorToolkit", "DisplayName", "WorldBLD"),
		FSlateIcon("WorldBLD", "WorldBLD.ToolIcon"),
		/* Visibility */ !bIsBlueprintTemplate,
		/* PriorityOrder */ 5001 // Picked semi-randomly
    );

	DefaultToolClass = UWorldBLDDefaultEditController::StaticClass();
}

bool UWorldBLDEdMode::IsThisEdModeActive() const
{
	if (IsRunningCommandlet())
	{
		return false;
	}
	return GLevelEditorModeTools().IsModeActive(FName("WorldBLDEditorMode"));
}

UWorldBLDEdMode* UWorldBLDEdMode::GetWorldBLDEdMode()
{
	// GLevelEditorModeTools() asserts in commandlets; interactive editor modes do not exist there.
	if (IsRunningCommandlet())
	{
		return nullptr;
	}
	return Cast<UWorldBLDEdMode>(GLevelEditorModeTools().GetActiveScriptableMode(UWorldBLDEdMode::EditorModeID));
}

FString UWorldBLDEdMode::GetRecordedInstalledToolSha1(const FString& ToolId) const
{
	return GetDefault<UWorldBLDToolUpdateSettings>()->GetInstalledSha1(ToolId);
}

namespace WorldBLDEdModeToolUpdateInternal
{
	static FString GetInstalledPluginVersionString(const TSharedPtr<IPlugin>& Plugin)
	{
		if (!Plugin.IsValid())
		{
			return FString();
		}

		const FPluginDescriptor& Descriptor = Plugin->GetDescriptor();
		if (!Descriptor.VersionName.IsEmpty())
		{
			return Descriptor.VersionName.TrimStartAndEnd();
		}

		// Fall back to numeric version if a version name is not provided.
		return FString::FromInt(Descriptor.Version);
	}

	static bool ParseNumericVersionParts(const FString& InVersion, TArray<int32>& OutParts)
	{
		OutParts.Reset();

		const FString Trimmed = InVersion.TrimStartAndEnd();
		if (Trimmed.IsEmpty())
		{
			return false;
		}

		// Parse leading numeric dot-separated parts (so like "1.2.3" in "1.2.3-beta").
		int32 Current = 0;
		bool bHasDigits = false;

		for (int32 Index = 0; Index < Trimmed.Len(); ++Index)
		{
			const TCHAR C = Trimmed[Index];

			if (FChar::IsDigit(C))
			{
				bHasDigits = true;
				Current = (Current * 10) + (C - TEXT('0'));
				continue;
			}

			if (C == TEXT('.'))
			{
				if (!bHasDigits)
				{
					return false;
				}
				OutParts.Add(Current);
				Current = 0;
				bHasDigits = false;
				continue;
			}

			// Stop at first non digit/dot.
			break;
		}

		if (bHasDigits)
		{
			OutParts.Add(Current);
		}

		return OutParts.Num() > 0;
	}

	static int32 CompareNumericVersionParts(const TArray<int32>& A, const TArray<int32>& B)
	{
		const int32 MaxParts = FMath::Max(A.Num(), B.Num());
		for (int32 Index = 0; Index < MaxParts; ++Index)
		{
			const int32 AV = (Index < A.Num()) ? A[Index] : 0;
			const int32 BV = (Index < B.Num()) ? B[Index] : 0;
			if (AV != BV)
			{
				return (AV < BV) ? -1 : 1;
			}
		}
		return 0;
	}
}

EWorldBLDToolUpdateState UWorldBLDEdMode::GetToolUpdateState(const FString& ToolId, const FString& ServerVersion, const FString& ServerSHA1) const
{
	if (ToolId.IsEmpty())
	{
		return EWorldBLDToolUpdateState::NotInstalled;
	}

	const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(ToolId);
	if (!Plugin.IsValid())
	{
		return EWorldBLDToolUpdateState::NotInstalled;
	}

	const FString InstalledVersion = WorldBLDEdModeToolUpdateInternal::GetInstalledPluginVersionString(Plugin);
	const FString ServerVersionTrimmed = ServerVersion.TrimStartAndEnd();
	if (InstalledVersion.IsEmpty() || ServerVersionTrimmed.IsEmpty())
	{
		return EWorldBLDToolUpdateState::InstalledUnknownSha1;
	}

	// Fast path: exact match (case-insensitive) => up-to-date.
	if (InstalledVersion.Equals(ServerVersionTrimmed, ESearchCase::IgnoreCase))
	{
		return EWorldBLDToolUpdateState::UpToDate;
	}

	// Staged updates are applied very early at startup, but plugin descriptor metadata can remain stale
	// for the current session in some packaging layouts. If we have a recorded installed SHA1 that matches
	// the server SHA1, trust that as up-to-date for UI/update gating.
	const FString ServerSha1Trimmed = ServerSHA1.TrimStartAndEnd();
	if (!ServerSha1Trimmed.IsEmpty())
	{
		const FString RecordedInstalledSha1 = GetRecordedInstalledToolSha1(ToolId).TrimStartAndEnd();
		if (!RecordedInstalledSha1.IsEmpty() && RecordedInstalledSha1.Equals(ServerSha1Trimmed, ESearchCase::IgnoreCase))
		{
			UE_LOG(
				LogWorldBLDEditor,
				Verbose,
				TEXT("[ToolUpdates] '%s' version mismatch (installed='%s', server='%s') but SHA1 matches server; treating as up-to-date."),
				*ToolId,
				*InstalledVersion,
				*ServerVersionTrimmed);
			return EWorldBLDToolUpdateState::UpToDate;
		}
	}

	// Prefer semantic-ish numeric compare if both sides have numeric parts.
	TArray<int32> InstalledParts;
	TArray<int32> ServerParts;
	const bool bInstalledParsed = WorldBLDEdModeToolUpdateInternal::ParseNumericVersionParts(InstalledVersion, InstalledParts);
	const bool bServerParsed = WorldBLDEdModeToolUpdateInternal::ParseNumericVersionParts(ServerVersionTrimmed, ServerParts);
	if (bInstalledParsed && bServerParsed)
	{
		const int32 Cmp = WorldBLDEdModeToolUpdateInternal::CompareNumericVersionParts(InstalledParts, ServerParts);
		return (Cmp < 0) ? EWorldBLDToolUpdateState::UpdateAvailable : EWorldBLDToolUpdateState::UpToDate;
	}

	// Fallback: if strings differ and we can't order reliably, treat as an available update.
	return EWorldBLDToolUpdateState::UpdateAvailable;
}

void UWorldBLDEdMode::RefreshAvailableToolsFromServer()
{
	FetchAvailableTools();
}

void UWorldBLDEdMode::CheckForPluginUpdates(bool bForceNotify)
{
	bCheckWorldBLDPluginVersionOnNextToolsFetch = true;
	bForceWorldBLDPluginVersionNotifyOnNextToolsFetch = bForceNotify;
	FetchAvailableTools();
}

void UWorldBLDEdMode::OpenDemoMap()
{
	FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float) -> bool
	{
		const FString FileToOpen = FPackageName::LongPackageNameToFilename(
			TEXT("/WorldBLD/Maps/Demo_WorldBLD"),
			FPackageName::GetMapPackageExtension()
		);
		FEditorFileUtils::LoadMap(FileToOpen, /*bLoadAsTemplate=*/false, /*bShowProgress=*/true);
		return false;
	}));
}

bool UWorldBLDEdMode::IsWorldBLDPluginUpToDate() const
{
	const FString ServerVersion = ServerWorldBLDPluginVersion.TrimStartAndEnd();
	if (ServerVersion.IsEmpty())
	{
		// Fail closed: tool updates must not proceed until we know the latest WorldBLD version.
		return false;
	}

	const FString LocalVersion = WorldBLDEditorContextMenu::GetWorldBLDEditorPluginVersionString().TrimStartAndEnd();
	if (LocalVersion.IsEmpty())
	{
		// Fail closed: cannot confirm currency without a local version.
		return false;
	}

	if (ServerVersion.Equals(LocalVersion, ESearchCase::IgnoreCase))
	{
		return true;
	}

	// Match GetToolUpdateState(): installed >= server counts as up to date (dev / ahead builds).
	TArray<int32> LocalParts;
	TArray<int32> ServerParts;
	if (WorldBLDEdModeToolUpdateInternal::ParseNumericVersionParts(LocalVersion, LocalParts)
		&& WorldBLDEdModeToolUpdateInternal::ParseNumericVersionParts(ServerVersion, ServerParts))
	{
		return WorldBLDEdModeToolUpdateInternal::CompareNumericVersionParts(LocalParts, ServerParts) >= 0;
	}

	// Unparseable mismatch: treat as outdated so companion-tool updates stay gated.
	return false;
}

void UWorldBLDEdMode::BuildLegacyPaletteCompatibilityCache()
{
	if (bLegacyToolPalettesInitialized)
	{
		return;
	}

	bLegacyToolPalettesInitialized = true;
	LegacyToolPalettes.Reset();
	ActiveLegacyToolPalette = nullptr;

	if ((GEditor == nullptr) || CustomToolClasses.IsEmpty())
	{
		return;
	}

	UWorld* World = GEditor->GetEditorWorldContext().World();
	if (World == nullptr)
	{
		return;
	}

	for (const TSoftClassPtr<UWorldBLDToolPaletteWidget>& ToolClass : CustomToolClasses)
	{
		if (ToolClass.IsNull())
		{
			continue;
		}

		const FSoftObjectPath ToolClassPath = ToolClass.ToSoftObjectPath();
		const FString ToolClassPackageName = ToolClassPath.GetLongPackageName();
		if (!WorldBLDEditorContextMenu::IsResolvableClassPackage(ToolClassPackageName))
		{
			continue;
		}

		UClass* LoadedToolClass = ToolClass.Get();
		if (LoadedToolClass == nullptr)
		{
			LoadedToolClass = ToolClass.LoadSynchronous();
		}

		if ((LoadedToolClass == nullptr) || !LoadedToolClass->IsChildOf(UWorldBLDToolPaletteWidget::StaticClass()))
		{
			continue;
		}

		UWorldBLDToolPaletteWidget* NewTool = CreateWidget<UWorldBLDToolPaletteWidget>(World, LoadedToolClass);
		if (NewTool == nullptr)
		{
			continue;
		}

		NewTool->SetFlags(RF_Transient);
		NewTool->EdMode = this;
		LegacyToolPalettes.Add(NewTool);
	}
}

UWorldBLDToolPaletteWidget* UWorldBLDEdMode::GetToolPaletteByClass(TSubclassOf<UWorldBLDToolPaletteWidget> ToolClass) const
{
	if (!IsValid(ToolClass))
	{
		return nullptr;
	}

	UWorldBLDEdMode* MutableThis = const_cast<UWorldBLDEdMode*>(this);
	MutableThis->BuildLegacyPaletteCompatibilityCache();
	for (UWorldBLDToolPaletteWidget* Palette : MutableThis->LegacyToolPalettes)
	{
		if (IsValid(Palette) && Palette->IsA(ToolClass))
		{
			return Palette;
		}
	}

	return nullptr;
}

UWorldBLDToolPaletteWidget* UWorldBLDEdMode::GetActiveToolPalette() const
{
	UWorldBLDEdMode* MutableThis = const_cast<UWorldBLDEdMode*>(this);
	MutableThis->BuildLegacyPaletteCompatibilityCache();
	return MutableThis->ActiveLegacyToolPalette.Get();
}

TArray<UWorldBLDToolPaletteWidget*> UWorldBLDEdMode::GetAvailableToolPalettes() const
{
	UWorldBLDEdMode* MutableThis = const_cast<UWorldBLDEdMode*>(this);
	MutableThis->BuildLegacyPaletteCompatibilityCache();

	TArray<UWorldBLDToolPaletteWidget*> Result;
	Result.Reserve(MutableThis->LegacyToolPalettes.Num());
	for (UWorldBLDToolPaletteWidget* Palette : MutableThis->LegacyToolPalettes)
	{
		if (IsValid(Palette))
		{
			Result.Add(Palette);
		}
	}
	return Result;
}

void UWorldBLDEdMode::SwitchToToolPaletteByClass(TSubclassOf<UWorldBLDToolPaletteWidget> ToolClass)
{
	SwitchToToolPalette(GetToolPaletteByClass(ToolClass), false);
}

void UWorldBLDEdMode::SwitchToToolPalette(UWorldBLDToolPaletteWidget* Palette, bool bForceFocused) const
{
	UWorldBLDEdMode* MutableThis = const_cast<UWorldBLDEdMode*>(this);
	MutableThis->BuildLegacyPaletteCompatibilityCache();

	if (!IsValid(Palette))
	{
		return;
	}

	if (IsValid(MutableThis->ActiveLegacyToolPalette) && (MutableThis->ActiveLegacyToolPalette != Palette))
	{
		MutableThis->ActiveLegacyToolPalette->ToolPaletteDeactivate();
	}

	MutableThis->ActiveLegacyToolPalette = Palette;
	Palette->ToolPaletteActivate();

	if (bForceFocused)
	{
		TryOpenPrimaryTabSidebarDrawer();
	}
}

void UWorldBLDEdMode::EvaluateWorldBLDPluginVersionAndNotify(bool bForce) const
{
	// Keep dialogs editor-only and non-intrusive.
	if (IsRunningCommandlet() || FApp::IsUnattended() || (GEditor == nullptr))
	{
		return;
	}

	// Don't show modals during PIE/SIE.
	if (GEditor->PlayWorld != nullptr)
	{
		return;
	}

	const FString ServerVersion = ServerWorldBLDPluginVersion.TrimStartAndEnd();
	if (ServerVersion.IsEmpty())
	{
		return;
	}

	const FString LocalVersion = WorldBLDEditorContextMenu::GetWorldBLDEditorPluginVersionString().TrimStartAndEnd();
	if (LocalVersion.IsEmpty())
	{
		return;
	}

	if (ServerVersion.Equals(LocalVersion, ESearchCase::IgnoreCase))
	{
		return;
	}

	// Avoid spamming: only show once per (server, local) pair per editor session,
	// unless the caller explicitly forces a notification (e.g. Resources "Check for Updates").
	static FString LastNotifiedServerVersion;
	static FString LastNotifiedLocalVersion;
	if (!bForce
		&& ServerVersion.Equals(LastNotifiedServerVersion, ESearchCase::IgnoreCase)
		&& LocalVersion.Equals(LastNotifiedLocalVersion, ESearchCase::IgnoreCase))
	{
		return;
	}
	LastNotifiedServerVersion = ServerVersion;
	LastNotifiedLocalVersion = LocalVersion;

	// Fab migration prompt: installed build is still pre-2.0, and the server is
	// advertising a 2.0.x release (2.0.0 inclusive, 2.1.0 exclusive).
	{
		int32 LocalMajor = 0, LocalMinor = 0, LocalPatch = 0;
		int32 ServerMajor = 0, ServerMinor = 0, ServerPatch = 0;
		const bool bLocalParsed  = WorldBLDEditorContextMenu::TryParseVersionTriplet(LocalVersion,  LocalMajor,  LocalMinor,  LocalPatch);
		const bool bServerParsed = WorldBLDEditorContextMenu::TryParseVersionTriplet(ServerVersion, ServerMajor, ServerMinor, ServerPatch);
		const bool bLocalPredatesFab = WorldBLDEditorContextMenu::IsVersionBelow(LocalMajor, LocalMinor, LocalPatch, 2, 0, 0);
		const bool bServerInFabWindow =
			!WorldBLDEditorContextMenu::IsVersionBelow(ServerMajor, ServerMinor, ServerPatch, 2, 0, 0)
			&& WorldBLDEditorContextMenu::IsVersionBelow(ServerMajor, ServerMinor, ServerPatch, 2, 1, 0);

		if (bLocalParsed && bServerParsed && bLocalPredatesFab && bServerInFabWindow)
		{
			const FText FabMessage = LOCTEXT(
				"WorldBLD_FabAvailable_Message",
				"The WorldBLD plugin is now available on Fab! Installing from Fab offers easy automatic updates and improved stability.\n\n"
				"You'll need to remove your current WorldBLD installation from the /Plugins folder you installed it first.");
			const FText FabTitle = LOCTEXT("WorldBLD_FabAvailable_Title", "WorldBLD Now on Fab");

			FSuppressableWarningDialog::FSetupInfo FabDialogSetup(FabMessage, FabTitle, TEXT("WorldBLD_FabPromotionNotice"));
			FabDialogSetup.ConfirmText = LOCTEXT("WorldBLD_FabAvailable_GetFromFab", "Get From Fab");
			FabDialogSetup.CancelText = LOCTEXT("WorldBLD_FabAvailable_NotYet", "Not Yet");
			// Hide the suppress checkbox so this prompt always remains actionable.
			FabDialogSetup.CheckBoxText = FText::GetEmpty();

			const FSuppressableWarningDialog FabDialog(FabDialogSetup);
			if (FabDialog.ShowModal() == FSuppressableWarningDialog::Confirm)
			{
				FPlatformProcess::LaunchURL(TEXT("https://worldbld.com/downloads"), nullptr, nullptr);
			}
			return;
		}
	}

	const FText Message = LOCTEXT(
		"WorldBLD_PluginVersionMismatch_Message",
		"A new version of the WorldBLD plugin is available. Please download the latest version from our website for the best experience.");
	const FText Title = LOCTEXT("WorldBLD_PluginVersionMismatch_Title", "WorldBLD Update Available");
	UUtilitiesLibrary::ShowOkModalDialog(Message, Title);
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Dependency-version enforcement (toolbar update)

namespace WorldBLDDependencyVersions
{
	// Minimum versions required by this WorldBLD release.
	// Only tools that are already installed are checked; uninstalled tools are skipped.
	struct FEntry
	{
		const TCHAR* ToolId;
		int32 Major;
		int32 Minor;
		int32 Patch;
	};

	static const FEntry Required[] =
	{
		{ TEXT("RoadBLD"), 1, 5, 6 },
		{ TEXT("CityBLD"), 1, 3, 3 },
		{ TEXT("TwinBLD"), 0, 4, 5 },
	};
}

///////////////////////////////////////////////////////////////////////////////////////////////////

/** Runtime state for one tool's staged download inside the dependency update dialog. */
struct FDependencyToolDownloadState
{
	FString ToolId;
	FString InstalledVersion;
	FString RequiredVersion;
	FString DownloadUrl;
	FString Sha1;

	// Written only on the game thread (download callbacks + Construct).
	float Progress = 0.0f;
	bool bComplete = false;
	bool bFailed = false;
};

///////////////////////////////////////////////////////////////////////////////////////////////////

/**
 * Blocking modal that stages downloads for one or more out-of-date dependency plugins.
 * Downloads begin immediately on construction. The user can restart the editor once all
 * downloads are staged, or skip for now (updates will apply on the next manual restart).
 */
class SWorldBLDDependencyUpdateDialog final : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDDependencyUpdateDialog)
		: _Downloader(nullptr)
	{}
		SLATE_ARGUMENT(TArray<FDependencyToolDownloadState>, ToolStates)
		SLATE_ARGUMENT(UCurlDownloaderLibrary*, Downloader)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		ToolStates = InArgs._ToolStates;
		Downloader = InArgs._Downloader;

		// Build the per-tool rows first so we can reference indices in lambdas.
		TSharedRef<SVerticalBox> ToolRowsBox = SNew(SVerticalBox);

		for (int32 i = 0; i < ToolStates.Num(); ++i)
		{
			const FDependencyToolDownloadState& State = ToolStates[i];
			const int32 ToolIndex = i;

			const FText VersionLabel = FText::Format(
				LOCTEXT("DepUpdate_VersionLabel", "{0}  {1}  \u2192  {2}"),
				FText::FromString(State.ToolId),
				FText::FromString(State.InstalledVersion),
				FText::FromString(State.RequiredVersion));

			ToolRowsBox->AddSlot()
			.AutoHeight()
			.Padding(FMargin(0.0f, i == 0 ? 0.0f : 12.0f, 0.0f, 0.0f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(STextBlock)
					.Text(VersionLabel)
					.Font(FAppStyle::GetFontStyle(TEXT("NormalFont")))
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 4.0f, 0.0f, 2.0f))
				[
					SNew(SProgressBar)
					.Percent(TAttribute<TOptional<float>>::CreateLambda(
						[this, ToolIndex]() -> TOptional<float>
						{
							if (ToolStates[ToolIndex].bComplete || ToolStates[ToolIndex].bFailed)
							{
								return TOptional<float>(1.0f);
							}
							return TOptional<float>(ToolStates[ToolIndex].Progress);
						}))
					.FillColorAndOpacity(TAttribute<FSlateColor>::CreateLambda(
						[this, ToolIndex]() -> FSlateColor
						{
							if (ToolStates[ToolIndex].bFailed)
							{
								return FLinearColor(0.8f, 0.2f, 0.2f, 1.0f);
							}
							if (ToolStates[ToolIndex].bComplete)
							{
								return FLinearColor(0.2f, 0.7f, 0.3f, 1.0f);
							}
							return FSlateColor::UseForeground();
						}))
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(STextBlock)
					.Text(TAttribute<FText>::CreateLambda(
						[this, ToolIndex]() -> FText
						{
							return GetToolStatusText(ToolIndex);
						}))
					.ColorAndOpacity(TAttribute<FSlateColor>::CreateLambda(
						[this, ToolIndex]() -> FSlateColor
						{
							if (ToolStates[ToolIndex].bFailed)
							{
								return FLinearColor(0.8f, 0.3f, 0.3f, 1.0f);
							}
							if (ToolStates[ToolIndex].bComplete)
							{
								return FLinearColor(0.3f, 0.8f, 0.4f, 1.0f);
							}
							return FSlateColor::UseSubduedForeground();
						}))
				]
			];
		}

		ChildSlot
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::Get().GetBrush("ToolPanel.GroupBorder"))
			.Padding(20.0f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(STextBlock)
					.Text(LOCTEXT("DepUpdate_Title", "Hang on, we're downloading some important updates"))
					.Font(FAppStyle::GetFontStyle(TEXT("NormalFontBold")))
					.AutoWrapText(true)
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
				[
					SNew(STextBlock)
					.Text(LOCTEXT("DepUpdate_Subtitle",
						"The WorldBLD toolbar requires updated versions of the following tools. "
						"They will be staged automatically and applied on the next editor restart."))
					.AutoWrapText(true)
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 16.0f, 0.0f, 0.0f))
				[
					ToolRowsBox
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 20.0f, 0.0f, 0.0f))
				.HAlign(HAlign_Right)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.Padding(FMargin(0.0f, 0.0f, 8.0f, 0.0f))
					[
						SNew(SButton)
						.Text(LOCTEXT("DepUpdate_SkipForNow", "Skip for Now"))
						.OnClicked(this, &SWorldBLDDependencyUpdateDialog::HandleSkipClicked)
					]
					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						SNew(SButton)
						.Text(LOCTEXT("DepUpdate_RestartEditor", "Restart Editor"))
						.IsEnabled(TAttribute<bool>::CreateLambda(
							[this]() -> bool { return AreAllDownloadsFinished(); }))
						.OnClicked(this, &SWorldBLDDependencyUpdateDialog::HandleRestartClicked)
					]
				]
			]
		];

		StartDownloads();
	}

	void SetHostWindow(TSharedRef<SWindow> InWindow)
	{
		HostWindow = InWindow;
	}

private:

	void StartDownloads()
	{
		UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
		if (!IsValid(DownloaderPtr))
		{
			// Downloader unavailable; mark everything as failed so the restart button enables.
			for (FDependencyToolDownloadState& State : ToolStates)
			{
				State.bFailed = true;
			}
			return;
		}

		// Tools are downloaded/staged one at a time (rather than concurrently). Several of these
		// tools can depend on one another (e.g. TwinBLD requires RoadBLD and CityBLD), and each
		// staged extraction writes into the SAME shared staging root (Saved/WorldBLD/StagedUpdates/).
		// Running them concurrently was found to make the dependent tool's stage unreliable, so we
		// process ToolStates in order (RoadBLD/CityBLD before TwinBLD, matching the declared minimum
		// version list) and only start the next download once the current one has finished.
		StartDownloadAtIndex(0);
	}

	void StartDownloadAtIndex(int32 ToolIndex)
	{
		if (!ToolStates.IsValidIndex(ToolIndex))
		{
			return;
		}

		UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
		if (!IsValid(DownloaderPtr))
		{
			for (int32 i = ToolIndex; i < ToolStates.Num(); ++i)
			{
				ToolStates[i].bFailed = true;
			}
			return;
		}

		FDependencyToolDownloadState& State = ToolStates[ToolIndex];
		if (State.DownloadUrl.IsEmpty())
		{
			State.bFailed = true;
			StartDownloadAtIndex(ToolIndex + 1);
			return;
		}

		DownloaderPtr->RequestToolDownloadNative(
			State.ToolId,
			State.DownloadUrl,
			State.Sha1,
			FOnDownloadProgress::FDelegate::CreateSP(
				this, &SWorldBLDDependencyUpdateDialog::OnDownloadProgress, ToolIndex),
			FOnComplete::FDelegate::CreateSP(
				this, &SWorldBLDDependencyUpdateDialog::OnDownloadComplete, ToolIndex));
	}

	void OnDownloadProgress(float InProgress, int32 ToolIndex)
	{
		if (ToolStates.IsValidIndex(ToolIndex))
		{
			ToolStates[ToolIndex].Progress = FMath::Clamp(InProgress, 0.0f, 1.0f);
		}
	}

	void OnDownloadComplete(bool bSuccess, int32 ToolIndex)
	{
		if (!ToolStates.IsValidIndex(ToolIndex))
		{
			return;
		}

		FDependencyToolDownloadState& State = ToolStates[ToolIndex];
		State.Progress = 1.0f;
		State.bComplete = bSuccess;
		State.bFailed = !bSuccess;

		// Move on to the next tool regardless of success/failure so one bad download doesn't block
		// the rest of the queue from staging.
		StartDownloadAtIndex(ToolIndex + 1);
	}

	FText GetToolStatusText(int32 ToolIndex) const
	{
		if (!ToolStates.IsValidIndex(ToolIndex))
		{
			return FText::GetEmpty();
		}

		const FDependencyToolDownloadState& State = ToolStates[ToolIndex];

		if (State.bFailed)
		{
			if (State.DownloadUrl.IsEmpty())
			{
				return LOCTEXT("DepUpdate_Status_NoUrl", "Download URL unavailable \u2014 please update manually from worldbld.com");
			}
			return LOCTEXT("DepUpdate_Status_Failed", "Download failed \u2014 please update manually from worldbld.com");
		}

		if (State.bComplete)
		{
			return LOCTEXT("DepUpdate_Status_Complete", "Staged \u2014 will be applied on restart");
		}

		const int32 Percent = FMath::Min(99, FMath::RoundToInt(State.Progress * 100.0f));
		return FText::Format(LOCTEXT("DepUpdate_Status_Downloading", "Downloading\u2026 {0}%"), FText::AsNumber(Percent));
	}

	bool AreAllDownloadsFinished() const
	{
		for (const FDependencyToolDownloadState& State : ToolStates)
		{
			if (!State.bComplete && !State.bFailed)
			{
				return false;
			}
		}
		return true;
	}

	FReply HandleRestartClicked()
	{
		CloseDialog();
		FUnrealEdMisc::Get().RestartEditor(false);
		return FReply::Handled();
	}

	FReply HandleSkipClicked()
	{
		CloseDialog();
		return FReply::Handled();
	}

	void CloseDialog()
	{
		if (TSharedPtr<SWindow> Pinned = HostWindow.Pin())
		{
			Pinned->RequestDestroyWindow();
		}
	}

	TWeakPtr<SWindow> HostWindow;
	TWeakObjectPtr<UCurlDownloaderLibrary> Downloader;
	TArray<FDependencyToolDownloadState> ToolStates;
};

///////////////////////////////////////////////////////////////////////////////////////////////////

void UWorldBLDEdMode::EvaluateDependentToolVersions()
{
	if (IsRunningCommandlet() || FApp::IsUnattended() || !FSlateApplication::IsInitialized() || (GEditor == nullptr))
	{
		return;
	}

	if (GEditor->PlayWorld != nullptr)
	{
		return;
	}

	// Show at most once per editor session across mode exits/re-entries.
	static bool bShownThisSession = false;
	if (bShownThisSession)
	{
		return;
	}

	// Gather stale tools. Only tools already installed are checked; uninstalled tools are skipped.
	TArray<FDependencyToolDownloadState> StaleTools;
	for (const WorldBLDDependencyVersions::FEntry& Entry : WorldBLDDependencyVersions::Required)
	{
		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(Entry.ToolId);
		if (!Plugin.IsValid())
		{
			continue;
		}

		const FString InstalledVersion = WorldBLDEdModeToolUpdateInternal::GetInstalledPluginVersionString(Plugin);

		TArray<int32> InstalledParts;
		TArray<int32> RequiredParts;
		const FString RequiredVersionStr = FString::Printf(TEXT("%d.%d.%d"), Entry.Major, Entry.Minor, Entry.Patch);

		if (!WorldBLDEdModeToolUpdateInternal::ParseNumericVersionParts(InstalledVersion, InstalledParts) ||
			!WorldBLDEdModeToolUpdateInternal::ParseNumericVersionParts(RequiredVersionStr, RequiredParts))
		{
			continue;
		}

		if (WorldBLDEdModeToolUpdateInternal::CompareNumericVersionParts(InstalledParts, RequiredParts) >= 0)
		{
			continue;
		}

		// Look up the tool in the server-fetched list and verify the server version meets or
		// exceeds the required minimum. If the server doesn't have the required version yet,
		// skip this tool entirely — we never prompt the user to download something unavailable.
		FDependencyToolDownloadState ToolState;
		bool bServerHasRequiredVersion = false;
		for (const FPluginToolData& AvailableTool : AvailableTools)
		{
			if (!AvailableTool.ToolName.Equals(Entry.ToolId, ESearchCase::IgnoreCase))
			{
				continue;
			}

			TArray<int32> ServerParts;
			if (WorldBLDEdModeToolUpdateInternal::ParseNumericVersionParts(AvailableTool.Version, ServerParts) &&
				WorldBLDEdModeToolUpdateInternal::CompareNumericVersionParts(ServerParts, RequiredParts) >= 0)
			{
				ToolState.DownloadUrl = AvailableTool.DownloadLink;
				ToolState.Sha1 = AvailableTool.SHA1;
				bServerHasRequiredVersion = true;
			}
			break;
		}

		if (!bServerHasRequiredVersion)
		{
			continue;
		}

		ToolState.ToolId = Entry.ToolId;
		ToolState.InstalledVersion = InstalledVersion;
		ToolState.RequiredVersion = RequiredVersionStr;

		StaleTools.Add(MoveTemp(ToolState));
	}

	if (StaleTools.IsEmpty())
	{
		return;
	}

	bShownThisSession = true;

	UCurlDownloaderLibrary* DownloaderPtr = GEditor->GetEditorSubsystem<UCurlDownloaderLibrary>();

	TSharedPtr<SWorldBLDDependencyUpdateDialog> DialogWidget;
	TSharedRef<SWindow> Window = SNew(SWindow)
		.Title(LOCTEXT("DepUpdate_WindowTitle", "WorldBLD \u2014 Important Updates Required"))
		.SizingRule(ESizingRule::Autosized)
		.MinWidth(480.0f)
		.SupportsMaximize(false)
		.SupportsMinimize(false)
		.HasCloseButton(false);

	Window->SetContent(
		SAssignNew(DialogWidget, SWorldBLDDependencyUpdateDialog)
		.ToolStates(StaleTools)
		.Downloader(DownloaderPtr)
	);

	if (DialogWidget.IsValid())
	{
		DialogWidget->SetHostWindow(Window);
	}

	FSlateApplication::Get().AddModalWindow(Window, FSlateApplication::Get().GetActiveTopLevelWindow());
}

///////////////////////////////////////////////////////////////////////////////////////////////////

void UWorldBLDEdMode::RegisterContextMenuExemptControllerClass(TSubclassOf<UWorldBLDEditController> ControllerClass)
{
	if (!IsValid(ControllerClass))
	{
		return;
	}

	ContextMenuExemptControllerClasses.AddUnique(ControllerClass);
}

void UWorldBLDEdMode::UnregisterContextMenuExemptControllerClass(TSubclassOf<UWorldBLDEditController> ControllerClass)
{
	if (!IsValid(ControllerClass))
	{
		return;
	}

	ContextMenuExemptControllerClasses.Remove(ControllerClass);
}

bool UWorldBLDEdMode::IsContextMenuControllerExempt(const UWorldBLDEditController* Controller) const
{
	if (!IsValid(Controller))
	{
		return false;
	}

	for (const TSubclassOf<UWorldBLDEditController>& ExemptClass : ContextMenuExemptControllerClasses)
	{
		if (IsValid(ExemptClass) && Controller->IsA(ExemptClass))
		{
			return true;
		}
	}

	return false;
}

void UWorldBLDEdMode::MovePrimaryTabToSidebar() const
{
	// Legacy sidebar UI was removed in 1.4.1. Kept as a compatibility no-op.
}

void UWorldBLDEdMode::RestorePrimaryTabFromSidebar() const
{
	// Legacy sidebar UI was removed in 1.4.1. Kept as a compatibility no-op.
}

bool UWorldBLDEdMode::IsPrimaryTabInSidebar() const
{
	// Legacy sidebar UI was removed in 1.4.1.
	return false;
}

void UWorldBLDEdMode::TryOpenPrimaryTabSidebarDrawer() const
{
	// Legacy sidebar UI was removed in 1.4.1. Kept as a compatibility no-op.
}

bool UWorldBLDEdMode::TryHideTabWell(bool bHide) const
{
	(void)bHide;
	// Legacy tab well handling was removed in 1.4.1.
	return false;
}

bool UWorldBLDEdMode::UsesToolkits() const
{
	return false;
}

bool UWorldBLDEdMode::InputKey(FEditorViewportClient* ViewportClient, FViewport* Viewport, FKey Key, EInputEvent Event)
{
	if (UWorldBLDEditController* Controller = GetActiveEditController())
	{		
		if (Controller->PressingEscapeTriggersExit() && (Key == EKeys::Escape) && (Event == EInputEvent::IE_Pressed))
		{
			Controller->TryExitTool(/* Force? */ false);
			return true;
		}

		const FModifierKeysState ModifierState = FSlateApplication::Get().GetModifierKeys();
		
		if (((Key == EKeys::MouseScrollDown) || (Key == EKeys::MouseScrollUp)) && 
				(Event == EInputEvent::IE_Pressed) && Controller->ConsumesMouseScroll())
		{
			Controller->ToolMouseScroll((Key == EKeys::MouseScrollDown) ? -1.0f : 1.0f, ModifierState.IsControlDown(), ModifierState.IsAltDown(), ModifierState.IsShiftDown());
			return true;
		}

		if ((Key == EKeys::LeftMouseButton) || (Key == EKeys::MiddleMouseButton) || (Key == EKeys::RightMouseButton))
		{
			const int32 MouseIndex = (Key == EKeys::LeftMouseButton) ? 0 : ((Key == EKeys::MiddleMouseButton) ? 1 : 2);
			bool bPassivelyConsumes = false;
			if (Controller->ConsumesMouseClick(MouseIndex, bPassivelyConsumes) || bPassivelyConsumes)
			{
				Controller->ToolMouseClick(MouseIndex, Event == EInputEvent::IE_Pressed);
				return !bPassivelyConsumes;
			}
		}

		for (const FKeyHandlingSpec& KeySpec : Controller->InterceptedKeyEvents)
		{
			if ((Key == KeySpec.InterceptedKey) && (Event != EInputEvent::IE_Repeat))
			{
				Controller->ToolKeyEvent(Key, Event == EInputEvent::IE_Pressed,
						ModifierState.IsControlDown(), ModifierState.IsAltDown(), ModifierState.IsShiftDown());
				if (KeySpec.bConsumesKey)
				{
					return true;
				}
			}
		}
	}

	return ILegacyEdModeViewportInterface::InputKey(ViewportClient, Viewport, Key, Event);
}

TSharedRef<FLegacyEdModeWidgetHelper> UWorldBLDEdMode::CreateWidgetHelper()
{
	return MakeShared<FWorldBLDSelectModeWidgetHelper>();
}

void UWorldBLDEdMode::CreateToolkit()
{
	if (WorldBLDEditorContextMenu::GetUISettings()->bEnableLegacySidebarUI)
	{
		UE_LOG(
			LogWorldBLDEditor,
			Warning,
			TEXT("bEnableLegacySidebarUI is enabled, but legacy sidebar UI has been removed. Running toolbar-only mode."));
	}

	if (UBlueprint* Blueprint = UBlueprint::GetBlueprintFromClass(GetClass()))
	{
		Blueprint->OnCompiled().AddUObject(this, &UWorldBLDEdMode::RegenerateContents);
	}

	InstallDefaultSelectionTool();
}


void UWorldBLDEdMode::OnBlueprintCompiled(UBlueprint* Blueprint)
{
	// If we recompile the editor mode's blueprint
	// it still sits in EditorModeManager::RecycledScriptableModes,
	// and will be re-used on Enter, which leads to the editor crash.
	if (Blueprint == UBlueprint::GetBlueprintFromClass(GetClass()))
	{
		GLevelEditorModeTools().DestroyMode(EditorModeID);
	}
}

void UWorldBLDEdMode::Enter()
{
    Super::Enter();

	EnsureLumenPostProcessVolumeExists();
		
	FLevelEditorModule& LevelEditor = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
	LevelEditor.OnMapChanged().AddUObject(this, &UWorldBLDEdMode::OnMapChanged);
	
	if (GEditor)
	{
		GEditor->OnBlueprintPreCompile().AddUObject(this, &UWorldBLDEdMode::OnBlueprintCompiled);

		if (UTransBuffer* TransBuffer = Cast<UTransBuffer>(GEditor->Trans))
		{
			TransBuffer->OnUndo().AddUObject(this, &UWorldBLDEdMode::PostEditorUndo);
			TransBuffer->OnRedo().AddUObject(this, &UWorldBLDEdMode::PostEditorRedo);
		}
	}

	bCheckWorldBLDPluginVersionOnNextToolsFetch = true;
	FetchAvailableTools();

	ShowWarningTooltipOverlay();

	if (!IsValid(GetActiveEditController()))
	{
		InstallDefaultSelectionTool();
	}

	RefreshViewportToolbarVisibility();
}

void UWorldBLDEdMode::ShowViewportToolbar()
{
	// Never create/show toolbars while this mode is inactive.
	if (!IsThisEdModeActive())
	{
		return;
	}

	if (ViewportToolbarOverlayWidget.IsValid())
	{
		return;
	}

	if (!WorldBLDEditorContextMenu::IsControllerAllowedToShowViewportToolbar(this, GetActiveEditController()))
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

	if (ActiveViewportToolbarId.IsNone())
	{
		ActiveViewportToolbarId = TEXT("WorldBLD");
	}

	const TSharedRef<SWidget> Toolbar = WorldBLDToolbar::CreateToolbarForTool(ActiveViewportToolbarId);
	ActiveViewport->AddOverlayWidget(Toolbar);

	ViewportToolbarHostViewport = ActiveViewport;
	ViewportToolbarOverlayWidget = Toolbar;
}

void UWorldBLDEdMode::HideViewportToolbar()
{
	TSharedPtr<SWidget> OverlayToRemove = ViewportToolbarOverlayWidget;
	TWeakPtr<SLevelViewport> HostViewport = ViewportToolbarHostViewport;
	ViewportToolbarOverlayWidget.Reset();
	ViewportToolbarHostViewport.Reset();

	if (!OverlayToRemove.IsValid())
	{
		return;
	}

	if (TSharedPtr<SLevelViewport> PinnedHostViewport = HostViewport.Pin())
	{
		PinnedHostViewport->RemoveOverlayWidget(OverlayToRemove.ToSharedRef());
		return;
	}

	// Fallback: attempt removal from the currently active viewport (in case focus changed).
	FLevelEditorModule& LevelEditor = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
	if (const TSharedPtr<ILevelEditor> PinnedEditor = LevelEditor.GetLevelEditorInstance().Pin())
	{
		if (const TSharedPtr<SLevelViewport> ActiveViewport = PinnedEditor->GetActiveViewportInterface())
		{
			ActiveViewport->RemoveOverlayWidget(OverlayToRemove.ToSharedRef());
		}
	}
}

void UWorldBLDEdMode::RefreshViewportToolbarVisibility()
{
	if (!IsThisEdModeActive())
	{
		HideViewportToolbar();
		return;
	}

	const bool bShouldShowToolbar =
		WorldBLDEditorContextMenu::IsControllerAllowedToShowViewportToolbar(this, GetActiveEditController());

	if (bShouldShowToolbar)
	{
		ShowViewportToolbar();
	}
	else
	{
		HideViewportToolbar();
	}
}

void UWorldBLDEdMode::SwitchViewportToolbar(FName ToolId)
{
	if (ToolId.IsNone())
	{
		ToolId = TEXT("WorldBLD");
	}

	// Already showing the requested toolbar.
	if ((ActiveViewportToolbarId == ToolId) && ViewportToolbarOverlayWidget.IsValid())
	{
		return;
	}

	ActiveViewportToolbarId = ToolId;

	// Close any open popups (e.g. the tool-switch menu this was invoked from).
	if (FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().DismissAllMenus();
	}

	// Defer the actual teardown/rebuild so we never destroy widgets while still
	// inside a click handler that originated from the toolbar/menu being replaced.
	if (GEditor != nullptr)
	{
		TWeakObjectPtr<UWorldBLDEdMode> WeakThis(this);
		GEditor->GetTimerManager()->SetTimerForNextTick([WeakThis]()
		{
			if (UWorldBLDEdMode* Mode = WeakThis.Get())
			{
				Mode->HideViewportToolbar();
				Mode->RefreshViewportToolbarVisibility();
			}
		});
	}
}

void UWorldBLDEdMode::EnsureLumenPostProcessVolumeExists()
{
	if (IsRunningCommandlet() || FApp::IsUnattended() || (GEditor == nullptr))
	{
		return;
	}

	// Don't modify maps during PIE/SIE.
	if (GEditor->PlayWorld != nullptr)
	{
		return;
	}

	UWorld* World = GEditor->GetEditorWorldContext().World();
	if (World == nullptr)
	{
		return;
	}

	APostProcessVolume* CandidateVolume = nullptr;
	for (TActorIterator<APostProcessVolume> It(World); It; ++It)
	{
		APostProcessVolume* Existing = *It;
		if (IsValid(Existing) && !Existing->IsTemplate())
		{
			// Prefer unbound volumes, but fall back to any valid PPV.
			if ((CandidateVolume == nullptr) || Existing->bUnbound)
			{
				CandidateVolume = Existing;
				if (Existing->bUnbound)
				{
					break;
				}
			}
		}
	}

	if (IsValid(CandidateVolume))
	{
		const bool bHasLumenGI =
			CandidateVolume->Settings.bOverride_DynamicGlobalIlluminationMethod &&
			(CandidateVolume->Settings.DynamicGlobalIlluminationMethod == EDynamicGlobalIlluminationMethod::Lumen);

		const bool bHasLumenReflections =
			CandidateVolume->Settings.bOverride_ReflectionMethod &&
			(CandidateVolume->Settings.ReflectionMethod == EReflectionMethod::Lumen);

		if (bHasLumenGI && bHasLumenReflections)
		{
			return;
		}

		const FText Title = LOCTEXT("WorldBLD_LumenRecommended_Title", "Enable Lumen (Recommended)");
		const FText Message = LOCTEXT(
			"WorldBLD_LumenRecommended_Message",
			"We found a PostProcessVolume, but it doesn't have Lumen Global Illumination and Reflections enabled.\n\n"
			"Would you like to enable Lumen on the existing Post Process Volume now? This is recommended for best results with WorldBLD assets."
		);

		static const TCHAR* SuppressSettingName = TEXT("SuppressWorldBLD_LumenPostProcessWarning");
		static const TCHAR* SuppressableDialogsSection = TEXT("SuppressableDialogs");

		// `FSuppressableWarningDialog` only persists its setting on some response paths.
		// This modal is commonly dismissed with "Not now", so we manage persistence ourselves to ensure
		// "Don't show this again" is respected regardless of which button is clicked.
		bool bSuppressed = false;
		if (GConfig != nullptr)
		{
			GConfig->GetBool(SuppressableDialogsSection, SuppressSettingName, bSuppressed, GEditorPerProjectIni);
		}
		if (bSuppressed)
		{
			return;
		}

		if (!FSlateApplication::IsInitialized())
		{
			return;
		}

		class SWorldBLDLumenPostProcessWarningDialog final : public SCompoundWidget
		{
		public:
			SLATE_BEGIN_ARGS(SWorldBLDLumenPostProcessWarningDialog) {}
				SLATE_ARGUMENT(FText, Message)
			SLATE_END_ARGS()

			void Construct(const FArguments& InArgs)
			{
				bEnableClicked = false;
				bDontShowAgain = false;

				ChildSlot
				[
					SNew(SBorder)
					.BorderImage(FAppStyle::Get().GetBrush("ToolPanel.GroupBorder"))
					.Padding(12.0f)
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot()
						.AutoHeight()
						[
							SNew(STextBlock)
							.Text(InArgs._Message)
							.AutoWrapText(true)
						]
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(FMargin(0.0f, 10.0f, 0.0f, 10.0f))
						[
							SNew(SCheckBox)
							.OnCheckStateChanged(this, &SWorldBLDLumenPostProcessWarningDialog::HandleDontShowAgainChanged)
							[
								SNew(STextBlock)
								.Text(LOCTEXT("WorldBLD_LumenRecommended_DontShowAgain", "Don't show this again"))
							]
						]
						+ SVerticalBox::Slot()
						.AutoHeight()
						.HAlign(HAlign_Right)
						[
							SNew(SUniformGridPanel)
							.SlotPadding(FMargin(4.0f, 0.0f))
							+ SUniformGridPanel::Slot(0, 0)
							[
								SNew(SButton)
								.Text(LOCTEXT("WorldBLD_LumenRecommended_Enable", "Enable"))
								.OnClicked(this, &SWorldBLDLumenPostProcessWarningDialog::HandleEnableClicked)
							]
							+ SUniformGridPanel::Slot(1, 0)
							[
								SNew(SButton)
								.Text(LOCTEXT("WorldBLD_LumenRecommended_NotNow", "Not now"))
								.OnClicked(this, &SWorldBLDLumenPostProcessWarningDialog::HandleNotNowClicked)
							]
						]
					]
				];
			}

			void SetHostWindow(TSharedRef<SWindow> InHostWindow)
			{
				HostWindow = InHostWindow;
			}

			bool WasEnableClicked() const
			{
				return bEnableClicked;
			}

			bool GetDontShowAgain() const
			{
				return bDontShowAgain;
			}

		private:
			FReply HandleEnableClicked()
			{
				bEnableClicked = true;
				CloseDialog();
				return FReply::Handled();
			}

			FReply HandleNotNowClicked()
			{
				bEnableClicked = false;
				CloseDialog();
				return FReply::Handled();
			}

			void HandleDontShowAgainChanged(ECheckBoxState NewState)
			{
				bDontShowAgain = (NewState == ECheckBoxState::Checked);
			}

			void CloseDialog()
			{
				if (TSharedPtr<SWindow> Pinned = HostWindow.Pin())
				{
					Pinned->RequestDestroyWindow();
				}
			}

			TWeakPtr<SWindow> HostWindow;
			bool bEnableClicked = false;
			bool bDontShowAgain = false;
		};

		bool bDontShowAgain = false;
		bool bEnableLumen = false;
		{
			TSharedPtr<SWorldBLDLumenPostProcessWarningDialog> DialogWidget;
			TSharedRef<SWindow> Window = SNew(SWindow)
				.Title(Title)
				.SizingRule(ESizingRule::Autosized)
				.SupportsMaximize(false)
				.SupportsMinimize(false)
				.HasCloseButton(false);

			Window->SetContent(
				SAssignNew(DialogWidget, SWorldBLDLumenPostProcessWarningDialog)
				.Message(Message)
			);

			DialogWidget->SetHostWindow(Window);

			FSlateApplication::Get().AddModalWindow(Window, FSlateApplication::Get().GetActiveTopLevelWindow());

			if (DialogWidget.IsValid())
			{
				bDontShowAgain = DialogWidget->GetDontShowAgain();
				bEnableLumen = DialogWidget->WasEnableClicked();
			}
		}

		if (bDontShowAgain && (GConfig != nullptr))
		{
			GConfig->SetBool(SuppressableDialogsSection, SuppressSettingName, true, GEditorPerProjectIni);
			GConfig->Flush(false, GEditorPerProjectIni);
		}

		if (bEnableLumen)
		{
			const FScopedTransaction Transaction(LOCTEXT("WorldBLD_EnableLumenOnExistingPPV", "WorldBLD: Enable Lumen on Post Process Volume"));
			if (ULevel* CandidateLevel = CandidateVolume->GetLevel())
			{
				CandidateLevel->Modify();
			}
			CandidateVolume->Modify();

			CandidateVolume->Settings.bOverride_DynamicGlobalIlluminationMethod = true;
			CandidateVolume->Settings.DynamicGlobalIlluminationMethod = EDynamicGlobalIlluminationMethod::Lumen;

			CandidateVolume->Settings.bOverride_ReflectionMethod = true;
			CandidateVolume->Settings.ReflectionMethod = EReflectionMethod::Lumen;
		}
		return;
	}

	ULevel* TargetLevel = nullptr;
	if (ULevelEditorSubsystem* LevelEditor = GEditor->GetEditorSubsystem<ULevelEditorSubsystem>())
	{
		TargetLevel = LevelEditor->GetCurrentLevel();
	}
	if (TargetLevel == nullptr)
	{
		TargetLevel = World->PersistentLevel;
	}
	if (TargetLevel == nullptr)
	{
		return;
	}

	const FScopedTransaction Transaction(LOCTEXT("WorldBLD_AddLumenPostProcessVolume", "WorldBLD: Add Lumen Post Process Volume"));
	TargetLevel->Modify();

	FActorSpawnParameters SpawnParams;
	SpawnParams.OverrideLevel = TargetLevel;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	SpawnParams.ObjectFlags |= RF_Transactional;

	APostProcessVolume* NewVolume = World->SpawnActor<APostProcessVolume>(APostProcessVolume::StaticClass(), FTransform::Identity, SpawnParams);
	if (!IsValid(NewVolume))
	{
		return;
	}

	NewVolume->Modify();

	// SpawnActor leaves ABrush::Brush nullptr, which yields zero bounds and breaks World Partition
	// streaming for the volume. Mirror SpawnLandscapePCGVolume / UActorFactoryBoxVolume: allocate
	// UModel + UPolys and build the default 200³ cube brush.
	UCubeBuilder* BrushBuilder = NewObject<UCubeBuilder>();
	BrushBuilder->X = 200.0f;
	BrushBuilder->Y = 200.0f;
	BrushBuilder->Z = 200.0f;
	UActorFactory::CreateBrushForVolumeActor(NewVolume, BrushBuilder);

#if WITH_EDITOR
	NewVolume->SetActorLabel(TEXT("WorldBLD PostProcess (Lumen)"));
	// Keep the unbound Lumen volume always loaded in World Partition levels.
	NewVolume->SetIsSpatiallyLoaded(false);
#endif

	NewVolume->bUnbound = true;
	NewVolume->bEnabled = true;

	NewVolume->Settings.bOverride_DynamicGlobalIlluminationMethod = true;
	NewVolume->Settings.DynamicGlobalIlluminationMethod = EDynamicGlobalIlluminationMethod::Lumen;

	NewVolume->Settings.bOverride_ReflectionMethod = true;
	NewVolume->Settings.ReflectionMethod = EReflectionMethod::Lumen;
}

void UWorldBLDEdMode::FetchAvailableTools()
{
	// Get UE version (e.g., "5.6" from "5.6.0")
	const FString FullVersion = FEngineVersion::Current().ToString();
	FString UEVersion;
	int32 DotCount = 0;
	for (int32 i = 0; i < FullVersion.Len(); i++)
	{
		if (FullVersion[i] == '.')
		{
			DotCount++;
			if (DotCount >= 2) break;
		}
		UEVersion.AppendChar(FullVersion[i]);
	}

	const FString URL = FString::Printf(TEXT("https://worldbld.com/api/tools?ue_version=%s"), *UEVersion);

	// Capture the session token once so we can (safely) retry without auth if needed.
	FString SessionToken;
	if (GEditor != nullptr)
	{
		if (const UWorldBLDAuthSubsystem* AuthSubsystem = GEditor->GetEditorSubsystem<UWorldBLDAuthSubsystem>())
		{
			SessionToken = AuthSubsystem->GetSessionToken();
		}
	}

	UE_LOG(
		LogWorldBLDEditor,
		Log,
		TEXT("[FetchAvailableTools] Requesting server tool list. ue_version='%s' url='%s' useAuth=%s"),
		*UEVersion,
		*URL,
		SessionToken.IsEmpty() ? TEXT("false") : TEXT("true"));

	struct FFetchAvailableToolsRequestContext : public TSharedFromThis<FFetchAvailableToolsRequestContext>
	{
		enum class EAuthHeaderMode : uint8
		{
			None,
			XAuthorization,
			BearerAuthorization
		};

		TWeakObjectPtr<UWorldBLDEdMode> WeakMode;
		FString URL;
		FString SessionToken;
		int32 AttemptCounter = 0;

		void PopulateFallbackFromInstalledPlugins() const
		{
			UWorldBLDEdMode* Mode = WeakMode.Get();
			if (Mode == nullptr)
			{
				return;
			}

			TArray<FPluginToolData> FallbackTools;
			FallbackTools.Reserve(3);

			const auto AddIfInstalled = [&FallbackTools](const FString& ToolId, const FString& Description)
			{
				if (ToolId.IsEmpty())
				{
					return;
				}

				if (!IPluginManager::Get().FindPlugin(ToolId).IsValid())
				{
					return;
				}

				FPluginToolData ToolData;
				ToolData.ToolName = ToolId;
				ToolData.Description = Description;
				FallbackTools.Add(MoveTemp(ToolData));
			};

			AddIfInstalled(TEXT("CityBLD"), TEXT("Installed (server list unavailable)"));
			AddIfInstalled(TEXT("RoadBLD"), TEXT("Installed (server list unavailable)"));
			AddIfInstalled(TEXT("TwinBLD"), TEXT("Installed (server list unavailable)"));

			if (FallbackTools.Num() > 0)
			{
				Mode->AvailableTools = MoveTemp(FallbackTools);
			}
		}

		void StartRequest(EAuthHeaderMode AuthHeaderMode, bool bAllowRetryWithAlternateAuth, bool bAllowRetryWithoutAuth)
		{
			const int32 AttemptNumber = ++AttemptCounter;

			FHttpModule& HttpModule = FHttpModule::Get();
			TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = HttpModule.CreateRequest();

			Request->SetURL(URL);
			Request->SetVerb(TEXT("GET"));
			Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
			Request->SetHeader(TEXT("Accept"), TEXT("application/json"));

			// If the user is logged in, include the session token so the backend can return license-gated tools.
			// If the backend returns an empty tool list when auth is present (eg token expired), we'll retry once without auth.
			if (AuthHeaderMode == EAuthHeaderMode::XAuthorization && !SessionToken.IsEmpty())
			{
				Request->SetHeader(TEXT("X-Authorization"), SessionToken);
			}
			else if (AuthHeaderMode == EAuthHeaderMode::BearerAuthorization && !SessionToken.IsEmpty())
			{
				Request->SetHeader(TEXT("Authorization"), FString::Printf(TEXT("Bearer %s"), *SessionToken));
			}

			Request->OnProcessRequestComplete().BindLambda(
				[Self = AsShared(), AuthHeaderMode, bAllowRetryWithAlternateAuth, bAllowRetryWithoutAuth, AttemptNumber](FHttpRequestPtr /*InRequest*/, FHttpResponsePtr Response, bool bWasSuccessful)
				{
					UWorldBLDEdMode* Mode = Self->WeakMode.Get();
					if (Mode == nullptr)
					{
						// The editor mode was destroyed/deactivated before the HTTP callback returned.
						return;
					}

					const auto TryRetryAlternateAuth = [&](const TCHAR* Reason) -> bool
					{
						if (bAllowRetryWithAlternateAuth && AuthHeaderMode == EAuthHeaderMode::XAuthorization && !Self->SessionToken.IsEmpty())
						{
							UE_LOG(LogWorldBLDEditor, Warning, TEXT("[FetchAvailableTools] Retrying with Authorization: Bearer. Reason='%s'"), Reason);
							Self->StartRequest(EAuthHeaderMode::BearerAuthorization, false, true);
							return true;
						}
						return false;
					};

					const auto TryRetryWithoutAuth = [&](const TCHAR* Reason) -> bool
					{
						if (bAllowRetryWithoutAuth && AuthHeaderMode != EAuthHeaderMode::None && !Self->SessionToken.IsEmpty())
						{
							UE_LOG(LogWorldBLDEditor, Warning, TEXT("[FetchAvailableTools] Retrying without auth. Reason='%s'"), Reason);
							Self->StartRequest(EAuthHeaderMode::None, false, false);
							return true;
						}
						return false;
					};

					if (!bWasSuccessful || !Response.IsValid())
					{
						UE_LOG(LogWorldBLDEditor, Warning, TEXT("[FetchAvailableTools] HTTP request failed. bWasSuccessful=%s responseValid=%s"), bWasSuccessful ? TEXT("true") : TEXT("false"), Response.IsValid() ? TEXT("true") : TEXT("false"));

						// If we attempted an authenticated request and it failed (eg expired token / proxy / captive portal),
						// retry once without auth so we still show public tools.
						if (TryRetryAlternateAuth(TEXT("RequestFailedOrNoResponse")))
						{
							return;
						}
						if (TryRetryWithoutAuth(TEXT("RequestFailedOrNoResponse")))
						{
							return;
						}

						// Don't clear the current list on request failure; keep last-known tools, and fall back if we have none.
						if (Mode->AvailableTools.Num() == 0)
						{
							Self->PopulateFallbackFromInstalledPlugins();
						}
						return;
					}

					const int32 ResponseCode = Response->GetResponseCode();
					const FString ResponseContentType = Response->GetHeader(TEXT("Content-Type"));
					const FString ResponseRequestId = Response->GetHeader(TEXT("X-Request-Id"));
					const FString ResponseCorrelationId = Response->GetHeader(TEXT("X-Correlation-Id"));
					const FString ResponseCFRay = Response->GetHeader(TEXT("CF-Ray"));
					const FString ResponseServer = Response->GetHeader(TEXT("Server"));

					const FString ContentAsString = Response->GetContentAsString();
					if (ContentAsString.IsEmpty())
					{
						UE_LOG(LogWorldBLDEditor, Warning, TEXT("[FetchAvailableTools] Empty response body. code=%d"), ResponseCode);
						if (TryRetryWithoutAuth(TEXT("EmptyBody")))
						{
							return;
						}

						if (Mode->AvailableTools.Num() == 0)
						{
							Self->PopulateFallbackFromInstalledPlugins();
						}
						return;
					}

					if (ResponseCode < 200 || ResponseCode >= 300)
					{
						UE_LOG(
							LogWorldBLDEditor,
							Warning,
							TEXT("[FetchAvailableTools] Non-2xx HTTP response. code=%d contentType='%s' server='%s' x-request-id='%s' x-correlation-id='%s' cf-ray='%s'"),
							ResponseCode,
							*ResponseContentType,
							*ResponseServer,
							*ResponseRequestId,
							*ResponseCorrelationId,
							*ResponseCFRay);

						if (TryRetryAlternateAuth(TEXT("Non2xxHttpResponse")))
						{
							return;
						}
					}

					const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ContentAsString);

					TSharedPtr<FJsonObject> JsonObject;
					if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
					{
						UE_LOG(LogWorldBLDEditor, Warning, TEXT("[FetchAvailableTools] Failed to deserialize JSON. code=%d contentType='%s'"), ResponseCode, *ResponseContentType);

						if (TryRetryAlternateAuth(TEXT("JsonDeserializeFailed")))
						{
							return;
						}
						if (TryRetryWithoutAuth(TEXT("JsonDeserializeFailed")))
						{
							return;
						}

						if (Mode->AvailableTools.Num() == 0)
						{
							Self->PopulateFallbackFromInstalledPlugins();
						}
						return;
					}

					if (!JsonObject->HasTypedField(TEXT("success"), EJson::Boolean) || !JsonObject->GetBoolField(TEXT("success")))
					{
						FString Message;
						JsonObject->TryGetStringField(TEXT("message"), Message);
						UE_LOG(LogWorldBLDEditor, Warning, TEXT("[FetchAvailableTools] Server returned failure JSON. code=%d message='%s'"), ResponseCode, *Message);

						if (TryRetryAlternateAuth(TEXT("JsonSuccessFalseOrMissing")))
						{
							return;
						}
						if (TryRetryWithoutAuth(TEXT("JsonSuccessFalseOrMissing")))
						{
							return;
						}

						if (Mode->AvailableTools.Num() == 0)
						{
							Self->PopulateFallbackFromInstalledPlugins();
						}
						return;
					}

					if (!JsonObject->HasTypedField(TEXT("tools"), EJson::Array))
					{
						UE_LOG(LogWorldBLDEditor, Warning, TEXT("[FetchAvailableTools] JSON missing expected field 'tools'. code=%d"), ResponseCode);

						if (TryRetryAlternateAuth(TEXT("JsonMissingToolsArray")))
						{
							return;
						}
						if (TryRetryWithoutAuth(TEXT("JsonMissingToolsArray")))
						{
							return;
						}

						if (Mode->AvailableTools.Num() == 0)
						{
							Self->PopulateFallbackFromInstalledPlugins();
						}
						return;
					}

					const TArray<TSharedPtr<FJsonValue>>& ToolsArray = JsonObject->GetArrayField(TEXT("tools"));

					TArray<FPluginToolData> NewTools;
					NewTools.Reserve(ToolsArray.Num());
					FString NewServerWorldBLDPluginVersion;
					FString NewServerWorldBLDToolId;
					bool bTwinBLDPresentInPayload = false;
					bool bTwinBLDAddedToNewTools = false;

					for (const TSharedPtr<FJsonValue>& ToolObj : ToolsArray)
					{
						if (!ToolObj.IsValid())
						{
							continue;
						}

						FPluginToolData ToolData;
						const TSharedPtr<FJsonObject> ToolJsonObject = ToolObj->AsObject();
						if (!ToolJsonObject.IsValid())
						{
							// Some payloads may return tools as simple strings (eg ["CityBLD","RoadBLD"]).
							if (ToolObj->Type == EJson::String)
							{
								ToolData.ToolName = ToolObj->AsString().TrimStartAndEnd();
								if (ToolData.ToolName.Equals(TEXT("TwinBLD"), ESearchCase::IgnoreCase))
								{
									bTwinBLDPresentInPayload = true;
								}
								if (!ToolData.ToolName.IsEmpty() && !ToolData.ToolName.Equals(TEXT("WorldBLD"), ESearchCase::IgnoreCase))
								{
									if (ToolData.ToolName.Equals(TEXT("TwinBLD"), ESearchCase::IgnoreCase))
									{
										bTwinBLDAddedToNewTools = true;
									}
									NewTools.Add(MoveTemp(ToolData));
								}
							}
							continue;
						}

						// Tool identifier can come under different keys depending on backend payload version.
						// Prefer "name" (historical), but fall back to "toolId"/"tool"/"id".
						{
							FString NameOrId;
							if (!ToolJsonObject->TryGetStringField(TEXT("name"), NameOrId) || NameOrId.TrimStartAndEnd().IsEmpty())
							{
								ToolJsonObject->TryGetStringField(TEXT("toolId"), NameOrId);
								if (NameOrId.TrimStartAndEnd().IsEmpty())
								{
									ToolJsonObject->TryGetStringField(TEXT("tool"), NameOrId);
								}
								if (NameOrId.TrimStartAndEnd().IsEmpty())
								{
									ToolJsonObject->TryGetStringField(TEXT("id"), NameOrId);
								}
							}

							ToolData.ToolName = NameOrId.TrimStartAndEnd();
							if (ToolData.ToolName.IsEmpty())
							{
								continue;
							}

							if (ToolData.ToolName.Equals(TEXT("TwinBLD"), ESearchCase::IgnoreCase))
							{
								bTwinBLDPresentInPayload = true;
							}

							if (ToolData.ToolName.Equals(TEXT("WorldBLD"), ESearchCase::IgnoreCase))
							{
								// Keep this out of AvailableTools (UI), but cache the version + tool id for:
								// - mismatch warning (version)
								// - requiredTools gating (tool id -> "WorldBLD" resolution)
								ToolJsonObject->TryGetStringField(TEXT("version"), NewServerWorldBLDPluginVersion);
								if (!ToolJsonObject->TryGetStringField(TEXT("toolId"), NewServerWorldBLDToolId) || NewServerWorldBLDToolId.TrimStartAndEnd().IsEmpty())
								{
									ToolJsonObject->TryGetStringField(TEXT("id"), NewServerWorldBLDToolId);
								}
								NewServerWorldBLDToolId = NewServerWorldBLDToolId.TrimStartAndEnd();
								continue;
							}
						}

						ToolJsonObject->TryGetStringField(TEXT("id"), ToolData.ServerId);
						ToolData.ServerId = ToolData.ServerId.TrimStartAndEnd();

						ToolJsonObject->TryGetStringField(TEXT("description"), ToolData.Description);
						ToolJsonObject->TryGetStringField(TEXT("downloadLink"), ToolData.DownloadLink);
						ToolJsonObject->TryGetStringField(TEXT("version"), ToolData.Version);
						ToolJsonObject->TryGetStringField(TEXT("sha1"), ToolData.SHA1);

						// Persist a server-tool-id -> plugin-name mapping so other systems can resolve requiredTools even
						// when license-based lists are incomplete (e.g., missing-tool download prompts, trial installs).
						{
							auto TryExtractServerToolIdFromUrl = [](const FString& Url, FString& OutServerToolId) -> bool
							{
								OutServerToolId.Reset();
								static const FString Marker = TEXT("/api/tools/");
								const int32 MarkerIndex = Url.Find(Marker, ESearchCase::IgnoreCase, ESearchDir::FromStart);
								if (MarkerIndex == INDEX_NONE)
								{
									return false;
								}

								const int32 AfterMarker = MarkerIndex + Marker.Len();
								if (AfterMarker >= Url.Len())
								{
									return false;
								}

								const int32 NextSlashIndex = Url.Find(TEXT("/"), ESearchCase::IgnoreCase, ESearchDir::FromStart, AfterMarker);
								if (NextSlashIndex == INDEX_NONE || NextSlashIndex <= AfterMarker)
								{
									return false;
								}

								OutServerToolId = Url.Mid(AfterMarker, NextSlashIndex - AfterMarker).TrimStartAndEnd();
								return !OutServerToolId.IsEmpty();
							};

							FString ServerToolIdFromUrl;
							const bool bParsedIdFromUrl = TryExtractServerToolIdFromUrl(ToolData.DownloadLink, ServerToolIdFromUrl);
							if (ToolData.ServerId.IsEmpty() && bParsedIdFromUrl)
							{
								ToolData.ServerId = ServerToolIdFromUrl;
							}

							// Always map from the explicit server id when present. Previously we only wrote
							// ToolIdMap when the download URL contained /api/tools/<id>/, so assets whose
							// requiredTools referenced an id (while downloadLink was empty/marketplace/etc.)
							// fell through to showing the raw ObjectId in the UI.
							if (GConfig && !ToolData.ToolName.IsEmpty() && !ToolData.ServerId.IsEmpty())
							{
								GConfig->SetString(TEXT("WorldBLD.ToolIdMap"), *ToolData.ServerId, *ToolData.ToolName, GEditorPerProjectIni);
							}
							else if (GConfig && !ToolData.ToolName.IsEmpty() && bParsedIdFromUrl)
							{
								GConfig->SetString(TEXT("WorldBLD.ToolIdMap"), *ServerToolIdFromUrl, *ToolData.ToolName, GEditorPerProjectIni);
							}
						}

						if (ToolData.ToolName.Equals(TEXT("TwinBLD"), ESearchCase::IgnoreCase))
						{
							bTwinBLDAddedToNewTools = true;
						}

						NewTools.Add(MoveTemp(ToolData));
					}

					if (GConfig)
					{
						GConfig->Flush(false, GEditorPerProjectIni);
					}

					{
						TArray<FString> ToolNames;
						ToolNames.Reserve(NewTools.Num());
						for (const FPluginToolData& Tool : NewTools)
						{
							ToolNames.Add(Tool.ToolName);
						}

						UE_LOG(
							LogWorldBLDEditor,
							Log,
							TEXT("[FetchAvailableTools] Tool list updated. count=%d names='%s' twinInPayload=%s"),
							NewTools.Num(),
							*FString::Join(ToolNames, TEXT(", ")),
							bTwinBLDPresentInPayload ? TEXT("true") : TEXT("false"));
					}

					// WorldBLD is stripped from NewTools above. Always cache its version/id when present so
					// update gating does not lose a previously known server version (or drop a WorldBLD-only payload).
					auto CommitWorldBLDServerMetadata = [Mode, &NewServerWorldBLDPluginVersion, &NewServerWorldBLDToolId]()
					{
						const FString TrimmedVersion = NewServerWorldBLDPluginVersion.TrimStartAndEnd();
						if (!TrimmedVersion.IsEmpty())
						{
							Mode->ServerWorldBLDPluginVersion = TrimmedVersion;
						}

						const FString TrimmedToolId = NewServerWorldBLDToolId.TrimStartAndEnd();
						if (!TrimmedToolId.IsEmpty())
						{
							Mode->ServerWorldBLDToolId = TrimmedToolId;

							// Persist so requiredTools resolution can map this id even before EdMode state is ready
							// (WorldBLD is filtered out of AvailableTools, so it never hits the NewTools ToolIdMap write).
							if (GConfig)
							{
								GConfig->SetString(TEXT("WorldBLD.ToolIdMap"), *TrimmedToolId, TEXT("WorldBLD"), GEditorPerProjectIni);
							}
						}
					};

					// If we requested with auth and got no tools back, retry once without auth so we at least show public tools.
					if (NewTools.Num() == 0)
					{
						CommitWorldBLDServerMetadata();

						if (TryRetryWithoutAuth(TEXT("EmptyToolsArrayAfterParse")))
						{
							return;
						}

						// Keep current list if any; otherwise fall back to installed plugins so the menu is never empty.
						if (Mode->AvailableTools.Num() == 0)
						{
							Self->PopulateFallbackFromInstalledPlugins();
						}
						return;
					}

					Mode->AvailableTools = MoveTemp(NewTools);
					// Only overwrite WorldBLD metadata when this payload included it. License-filtered
					// responses may omit WorldBLD while still listing companion tools; clearing the
					// cached version would fail-open (previously) / permanently block (fail-closed) updates.
					CommitWorldBLDServerMetadata();

					const TWeakObjectPtr<UWorldBLDEdMode> WeakMode = Mode;
					for (const FPluginToolData& ToolData : Mode->AvailableTools)
					{
						const FString ServerToolId = ToolData.ServerId.TrimStartAndEnd();
						if (ServerToolId.IsEmpty())
						{
							continue;
						}

						const FString RequiredToolsUrl = FString::Printf(TEXT("https://worldbld.com/api/tools/%s/required-tools"), *ServerToolId);
						TSharedRef<IHttpRequest, ESPMode::ThreadSafe> RequiredToolsRequest = FHttpModule::Get().CreateRequest();
						RequiredToolsRequest->SetURL(RequiredToolsUrl);
						RequiredToolsRequest->SetVerb(TEXT("GET"));
						RequiredToolsRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
						RequiredToolsRequest->SetHeader(TEXT("Accept"), TEXT("application/json"));

						RequiredToolsRequest->OnProcessRequestComplete().BindLambda(
							[WeakMode, ServerToolId](FHttpRequestPtr /*InRequest*/, FHttpResponsePtr InResponse, bool bInWasSuccessful)
							{
								UWorldBLDEdMode* PinnedMode = WeakMode.Get();
								if (PinnedMode == nullptr || !bInWasSuccessful || !InResponse.IsValid())
								{
									return;
								}

								if (InResponse->GetResponseCode() < 200 || InResponse->GetResponseCode() >= 300)
								{
									return;
								}

								const TSharedRef<TJsonReader<>> RequiredReader = TJsonReaderFactory<>::Create(InResponse->GetContentAsString());
								TSharedPtr<FJsonObject> RequiredJson;
								if (!FJsonSerializer::Deserialize(RequiredReader, RequiredJson) || !RequiredJson.IsValid())
								{
									return;
								}

								bool bSuccess = false;
								if (!RequiredJson->TryGetBoolField(TEXT("success"), bSuccess) || !bSuccess)
								{
									return;
								}

								const TArray<TSharedPtr<FJsonValue>>* RequiredToolsArray = nullptr;
								if (!RequiredJson->TryGetArrayField(TEXT("required_tools"), RequiredToolsArray) || RequiredToolsArray == nullptr)
								{
									return;
								}

								TArray<FString> RequiredToolNames;
								RequiredToolNames.Reserve(RequiredToolsArray->Num());
								for (const TSharedPtr<FJsonValue>& RequiredValue : *RequiredToolsArray)
								{
									if (!RequiredValue.IsValid())
									{
										continue;
									}

									const TSharedPtr<FJsonObject> RequiredObj = RequiredValue->AsObject();
									if (!RequiredObj.IsValid())
									{
										continue;
									}

									FString RequiredName;
									RequiredObj->TryGetStringField(TEXT("name"), RequiredName);
									RequiredName = RequiredName.TrimStartAndEnd();
									if (!RequiredName.IsEmpty())
									{
										RequiredToolNames.AddUnique(RequiredName);
									}
								}

								for (FPluginToolData& AvailableTool : PinnedMode->AvailableTools)
								{
									if (AvailableTool.ServerId.TrimStartAndEnd().Equals(ServerToolId, ESearchCase::IgnoreCase))
									{
										AvailableTool.RequiredToolIds = MoveTemp(RequiredToolNames);
										break;
									}
								}
							});

						RequiredToolsRequest->ProcessRequest();
					}

					if (Mode->bCheckWorldBLDPluginVersionOnNextToolsFetch)
					{
						const bool bForceNotify = Mode->bForceWorldBLDPluginVersionNotifyOnNextToolsFetch;
						Mode->bCheckWorldBLDPluginVersionOnNextToolsFetch = false;
						Mode->bForceWorldBLDPluginVersionNotifyOnNextToolsFetch = false;
						Mode->EvaluateWorldBLDPluginVersionAndNotify(bForceNotify);
						Mode->EvaluateDependentToolVersions();
					}
				});

			if (!Request->ProcessRequest())
			{
				UE_LOG(LogWorldBLDEditor, Warning, TEXT("[FetchAvailableTools] ProcessRequest() failed synchronously."));
				if (UWorldBLDEdMode* Mode = WeakMode.Get())
				{
					if (Mode->AvailableTools.Num() == 0)
					{
						PopulateFallbackFromInstalledPlugins();
					}
				}
			}
		}
	};

	const TSharedRef<FFetchAvailableToolsRequestContext> Context = MakeShared<FFetchAvailableToolsRequestContext>();
	Context->WeakMode = this;
	Context->URL = URL;
	Context->SessionToken = SessionToken;

	// First attempt: use auth if we have a session token.
	Context->StartRequest(SessionToken.IsEmpty() ? FFetchAvailableToolsRequestContext::EAuthHeaderMode::None : FFetchAvailableToolsRequestContext::EAuthHeaderMode::XAuthorization, true, true);
}

FSimpleMulticastDelegate& UWorldBLDEdMode::OnWorldBLDEdModeExited()
{
	static FSimpleMulticastDelegate Delegate;
	return Delegate;
}

void UWorldBLDEdMode::Exit()
{
	HideViewportToolbar();
	HideWarningTooltipOverlay();
	HideContextMenu();

	if (GEditor)
	{
		if (UTransBuffer* TransBuffer = Cast<UTransBuffer>(GEditor->Trans))
		{
			TransBuffer->OnUndo().RemoveAll(this);
			TransBuffer->OnRedo().RemoveAll(this);
		}
	}

	ClearToolModeStack();

    Super::Exit();

	OnWorldBLDEdModeExited().Broadcast();
}

void UWorldBLDEdMode::Tick(FEditorViewportClient* ViewportClient, float DeltaTime)
{
	RefreshViewportToolbarVisibility();

	if (HasActiveContextMenu() && !ValidateContextMenuTargets())
	{
		HideContextMenu();
	}
}

void UWorldBLDEdMode::Render(const FSceneView* View, FViewport* Viewport, FPrimitiveDrawInterface* PDI)
{
	Super::Render(View, Viewport, PDI);

	if (ToolModeStack.Num() > 0)
	{
		ToolModeStack.Last()->RenderInView(View, Viewport, PDI);
	}
}

bool UWorldBLDEdMode::HandleClick(FEditorViewportClient* InViewportClient, HHitProxy* HitProxy, const FViewportClick& Click)
{
	bool bHandled = false;

    // Route hit proxy clicks for WorldBLD runtime selectable elements
    if (const HCityKitSelectableObjectHitProxy* SelectedItemProxy = HitProxyCast<HCityKitSelectableObjectHitProxy>(HitProxy))
    {
        if (ToolModeStack.Num() > 0 && IsValid(ToolModeStack.Last()))
        {
            ToolModeStack.Last()->ToolHitProxyClick(SelectedItemProxy->Context, Click.GetKey());
            bHandled = true;
        }
    }

	if (!bHandled)
	{
		bHandled = Super::HandleClick(InViewportClient, HitProxy, Click);
	}
	return bHandled;
}

bool UWorldBLDEdMode::MouseMove(FEditorViewportClient* ViewportClient, FViewport* Viewport, int32 x, int32 y)
{
	bool bHandled = false;
	if (UWorldBLDEditController* Controller = GetActiveEditController())
	{
		Controller->ToolMouseMove(x, y);
		bHandled = true;
	}

	if (!bHandled)
	{
		Super::MouseMove(ViewportClient, Viewport, x, y);
	}
	return bHandled;
}

void UWorldBLDEdMode::InstallDefaultRecompileHandler()
{
	UBlueprint* MyBlueprint = UBlueprint::GetBlueprintFromClass(GetClass());
	if (IsValid(MyBlueprint))
	{
		MyBlueprint->OnCompiled().AddUObject(this, &UWorldBLDEdMode::RegenerateContents);
	}
}

void UWorldBLDEdMode::RegenerateContents(UBlueprint* RecompiledBlueprint)
{
	// Regenerating contents is expensive, so if the ed mode is not presented then ignore this.
	if (!IsThisEdModeActive())
	{
		return;
	}

	// If we are recompiling ourselves, we need to entirely delete this mode so it can be re-registered by the new class.
	if (RecompiledBlueprint == UBlueprint::GetBlueprintFromClass(GetClass()))
	{
		GLevelEditorModeTools().DestroyMode(EditorModeID);
	}
#if 1
	else
	{
		// NOTE: Regenerating contents is just too expensive. Deactivate the EdMode and let it regenerate its contents later.
		GLevelEditorModeTools().DeactivateMode(EditorModeID);
	}
#else
	else
	{	
		TryConstructInlineContent(/* Force? */ true);
	}

	InstallDefaultSelectionTool();
#endif
}

void UWorldBLDEdMode::OnMapChanged(UWorld* World, EMapChangeType MapChangeType)
{
	if (MapChangeType == EMapChangeType::TearDownWorld)
	{
		// Force tool teardown first so tool-owned async work (for example road rebuilds)
		// is asked to abort before we begin broader world cleanup.
		if (UWorldBLDEditController* ActiveController = GetActiveEditController())
		{
			ActiveController->TryExitTool(/* bForceEnd */ true);
		}

		// Tear down any active viewport context menu before world GC. The overlay widget can outlive
		// actor teardown if it remains attached to the viewport.
		HideContextMenu();

		// Ensure actors from the tearing-down world are not left in the editor selection set.
		// Keeping stale selected actors can pin world-owned objects/packages and trigger leak checks.
		if ((GEditor != nullptr) && IsValid(World))
		{
			if (USelection* SelectedActors = GEditor->GetSelectedActors())
			{
				TArray<AActor*> ActorsToDeselect;
				for (FSelectionIterator It(*SelectedActors); It; ++It)
				{
					if (AActor* SelectedActor = Cast<AActor>(*It))
					{
						if (SelectedActor->GetWorld() == World)
						{
							ActorsToDeselect.Add(SelectedActor);
						}
					}
				}

				for (AActor* ActorToDeselect : ActorsToDeselect)
				{
					SelectedActors->Deselect(ActorToDeselect);
				}

				if (!ActorsToDeselect.IsEmpty())
				{
					GEditor->NoteSelectionChange();
				}
			}
		}

		ClearToolModeStack();
	}
}

void UWorldBLDEdMode::PostEditorUndo(const struct FTransactionContext& TransactionContext, bool bSucceeded) const
{
	if (IsThisEdModeActive())
	{
		if (UWorldBLDEditController* Tool = GetActiveEditController())
		{
			Tool->ToolPostUndoRedo(/* is undo? */ true);
		}
	}
}

void UWorldBLDEdMode::PostEditorRedo(const struct FTransactionContext& TransactionContext, bool bSucceeded) const
{
	if (IsThisEdModeActive())
	{
		if (UWorldBLDEditController* Tool = GetActiveEditController())
		{
			Tool->ToolPostUndoRedo(/* is undo? */ false);
		}
	}
}

void UWorldBLDEdMode::TryConstructUserWidget(TObjectPtr<UUserWidget>& WidgetRef, TSoftClassPtr<UUserWidget> WidgetClass, bool bForce)
{
	if ((!IsValid(WidgetRef) || bForce) && !WidgetClass.IsNull() && GEditor)
    {
        /// NOTE: see UEditorUtilityWidgetBlueprint::CreateUtilityWidget() as a reference
        UWorld* World = GEditor->GetEditorWorldContext().World();
        if (World)
        {
			DestructWidget(WidgetRef);

			// Avoid noisy LoadPackage warnings and CreateWidget(null class) errors when a configured widget class
			// points at a package that doesn't exist (eg optional companion plugins not installed).
			const FSoftObjectPath WidgetClassPath = WidgetClass.ToSoftObjectPath();
			if (!WidgetClassPath.IsValid())
			{
				return;
			}

			const FString WidgetClassPackageName = WidgetClassPath.GetLongPackageName();
			if (!WorldBLDEditorContextMenu::IsResolvableClassPackage(WidgetClassPackageName))
			{
				return;
			}

			// Prefer already-loaded class when possible; otherwise load synchronously (editor-only).
			UClass* LoadedWidgetClass = WidgetClass.Get();
			if (LoadedWidgetClass == nullptr)
			{
				LoadedWidgetClass = WidgetClass.LoadSynchronous();
			}
			if (LoadedWidgetClass == nullptr)
			{
				return;
			}

            WidgetRef = CreateWidget<UUserWidget>(World, LoadedWidgetClass);
		    if (WidgetRef)
		    {
			    // Editor Utility is flagged as transient to prevent from dirty the World it's created in when a property added to the Utility Widget is changed
			    WidgetRef->SetFlags(RF_Transient);

			    // Also mark nested utility widgets as transient to prevent them from dirtying the world (since they'll be created via CreateWidget and not CreateUtilityWidget)
			    TArray<UWidget*> AllWidgets;
			    WidgetRef->WidgetTree->GetAllWidgets(AllWidgets);

			    for (UWidget* Widget : AllWidgets)
			    {
				    if (Widget->IsA(UEditorUtilityWidget::StaticClass()))
				    {
					    Widget->SetFlags(RF_Transient);
					    Widget->Slot->SetFlags(RF_Transient);
				    }
			    }
		    }
        }
    }
}

void UWorldBLDEdMode::DestructWidget(TObjectPtr<UUserWidget>& WidgetRef)
{
	if (WidgetRef)
	{
		WidgetRef->Rename(nullptr, GetTransientPackage(), REN_DoNotDirty);
		WidgetRef = nullptr;
	}
}

UWorldBLDEditController* UWorldBLDEdMode::GetActiveEditController() const
{
	return ToolModeStack.IsEmpty() ? nullptr : ToolModeStack.Last();
}

bool UWorldBLDEdMode::AreSameActorSelection(const TArray<AActor*>& Actors, const TArray<TWeakObjectPtr<AActor>>& WeakActors)
{
	if (Actors.Num() != WeakActors.Num())
	{
		return false;
	}

	TSet<const AActor*> ActorSet;
	ActorSet.Reserve(Actors.Num());
	for (AActor* Actor : Actors)
	{
		if (!IsValid(Actor))
		{
			return false;
		}
		ActorSet.Add(Actor);
	}

	// If there were duplicates, sets will collapse them.
	if (ActorSet.Num() != Actors.Num())
	{
		return false;
	}

	for (const TWeakObjectPtr<AActor>& WeakActor : WeakActors)
	{
		if (!WeakActor.IsValid() || !ActorSet.Contains(WeakActor.Get()))
		{
			return false;
		}
	}

	return true;
}

bool UWorldBLDEdMode::HasActiveContextMenu() const
{
	return ActiveContextMenuOverlayWidget.IsValid();
}

void UWorldBLDEdMode::HideContextMenu()
{
	TSharedPtr<SWidget> OverlayToRemove = ActiveContextMenuOverlayWidget;
	TWeakPtr<SLevelViewport> HostViewport = ActiveContextMenuHostViewport;

	ActiveContextMenuOverlayWidget.Reset();
	ActiveContextMenuHostViewport.Reset();
	ContextMenuTargetActor.Reset();
	ContextMenuTargetActors.Reset();
	bContextMenuHiddenByTool = false;

	if (OverlayToRemove.IsValid())
	{
		if (TSharedPtr<SLevelViewport> PinnedHostViewport = HostViewport.Pin())
		{
			PinnedHostViewport->RemoveOverlayWidget(OverlayToRemove.ToSharedRef());
		}
		else
		{
			// Fallback: attempt removal from the currently active viewport (in case focus changed).
			FLevelEditorModule& LevelEditor = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
			if (const TSharedPtr<ILevelEditor> PinnedEditor = LevelEditor.GetLevelEditorInstance().Pin())
			{
				if (const TSharedPtr<SLevelViewport> ActiveViewport = PinnedEditor->GetActiveViewportInterface())
				{
					ActiveViewport->RemoveOverlayWidget(OverlayToRemove.ToSharedRef());
				}
			}
		}
	}
}

void UWorldBLDEdMode::ShowWarningTooltipOverlay()
{
	if (WarningTooltipOverlayWidget.IsValid())
	{
		return;
	}

	FLevelEditorModule& LevelEditor = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
	const TSharedPtr<ILevelEditor> LevelEditorInstance = LevelEditor.GetLevelEditorInstance().Pin();
	if (!LevelEditorInstance.IsValid())
	{
		return;
	}

	const TSharedPtr<SLevelViewport> ActiveViewport = LevelEditorInstance->GetActiveViewportInterface();
	if (!ActiveViewport.IsValid())
	{
		return;
	}

	const TWeakObjectPtr<UWorldBLDEdMode> WeakThis(this);

	const TSharedRef<SWorldBLDWarningTooltipOverlay> Overlay =
		SNew(SWorldBLDWarningTooltipOverlay)
		.WarningText_Lambda([WeakThis]() -> FText
		{
			if (WeakThis.IsValid())
			{
				if (const UWorldBLDEditController* Controller = WeakThis->GetActiveEditController())
				{
					return Controller->UserWarning;
				}
			}
			return FText::GetEmpty();
		});

	WarningTooltipOverlayWidget = Overlay;
	WarningTooltipHostViewport = ActiveViewport;

	ActiveViewport->AddOverlayWidget(Overlay);
}

void UWorldBLDEdMode::HideWarningTooltipOverlay()
{
	TSharedPtr<SWidget> OverlayToRemove = WarningTooltipOverlayWidget;
	TWeakPtr<SLevelViewport> HostViewport = WarningTooltipHostViewport;

	WarningTooltipOverlayWidget.Reset();
	WarningTooltipHostViewport.Reset();

	if (OverlayToRemove.IsValid())
	{
		if (TSharedPtr<SLevelViewport> PinnedHostViewport = HostViewport.Pin())
		{
			PinnedHostViewport->RemoveOverlayWidget(OverlayToRemove.ToSharedRef());
			return;
		}

		// Fallback: attempt removal from the currently active viewport (in case focus changed).
		FLevelEditorModule& LevelEditor = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
		if (const TSharedPtr<ILevelEditor> PinnedEditor = LevelEditor.GetLevelEditorInstance().Pin())
		{
			if (const TSharedPtr<SLevelViewport> ActiveViewport = PinnedEditor->GetActiveViewportInterface())
			{
				ActiveViewport->RemoveOverlayWidget(OverlayToRemove.ToSharedRef());
			}
		}
	}
}

bool UWorldBLDEdMode::IsContextMenuRelevantForSelection(const TArray<AActor*>& SelectedActors) const
{
	// Only allow context menus when the active controller is an exempt controller (default controller or
	// the MainSubtoolClass of one of our available tool palettes).
	if (!WorldBLDEditorContextMenu::IsControllerAllowedToShowContextMenu(this, GetActiveEditController()))
	{
		return false;
	}

	if (SelectedActors.IsEmpty())
	{
		return false;
	}

	UWorldBLDContextMenuRegistry* Registry = UWorldBLDContextMenuRegistry::Get();
	if (!IsValid(Registry))
	{
		return false;
	}

	auto ResolveTarget = [](AActor* Actor) -> AActor*
	{
		if (!IsValid(Actor))
		{
			return nullptr;
		}

		if (Actor->GetClass()->ImplementsInterface(UWorldBLDContextMenuProvider::StaticClass()))
		{
			return IWorldBLDContextMenuProvider::Execute_GetContextMenuTargetActor(Actor);
		}

		return Actor;
	};

	AActor* FirstTarget = ResolveTarget(SelectedActors[0]);
	if (!IsValid(FirstTarget))
	{
		return false;
	}

	// A selection is "context-menu relevant" if every selected actor resolves to a valid target actor that has a factory.
	// We allow mixed selection types here (handled as an error state in the menu UI).
	const TScriptInterface<IWorldBLDContextMenuFactory> FirstFactory = Registry->FindFactoryForActor(FirstTarget);
	const IWorldBLDContextMenuFactory* FirstFactoryInterface = FirstFactory.GetInterface();
	if ((FirstFactoryInterface == nullptr) || !FirstFactoryInterface->CanCreateContextMenuForActor(FirstTarget))
	{
		return false;
	}

	for (AActor* Actor : SelectedActors)
	{
		AActor* TargetActor = ResolveTarget(Actor);
		if (!IsValid(TargetActor))
		{
			return false;
		}

		const TScriptInterface<IWorldBLDContextMenuFactory> Factory = Registry->FindFactoryForActor(TargetActor);
		const IWorldBLDContextMenuFactory* FactoryInterface = Factory.GetInterface();
		if ((FactoryInterface == nullptr) || !FactoryInterface->CanCreateContextMenuForActor(TargetActor))
		{
			return false;
		}
	}

	return true;
}

void UWorldBLDEdMode::ShowContextMenuForActors(const TArray<AActor*>& Actors)
{
	if (Actors.IsEmpty())
	{
		HideContextMenu();
		return;
	}

	// Context menus should only show for exempt controller classes (default controller or
	// main controller of one of our tool palettes).
	if (!WorldBLDEditorContextMenu::IsControllerAllowedToShowContextMenu(this, GetActiveEditController()))
	{
		HideContextMenu();
		return;
	}

	auto ResolveTarget = [](AActor* Actor) -> AActor*
	{
		if (!IsValid(Actor))
		{
			return nullptr;
		}

		if (Actor->GetClass()->ImplementsInterface(UWorldBLDContextMenuProvider::StaticClass()))
		{
			return IWorldBLDContextMenuProvider::Execute_GetContextMenuTargetActor(Actor);
		}

		return Actor;
	};

	auto MakeErrorContent = [](const FText& Message) -> TSharedRef<SWidget>
	{
		return SNew(SBorder)
			.Padding(FMargin(8.0f))
			[
				SNew(STextBlock)
				.AutoWrapText(true)
				.Text(Message)
			];
	};

	TArray<AActor*> TargetActors;
	TargetActors.Reserve(Actors.Num());

	for (AActor* Actor : Actors)
	{
		if (AActor* Target = ResolveTarget(Actor); IsValid(Target))
		{
			TargetActors.AddUnique(Target);
		}
	}

	if (TargetActors.IsEmpty())
	{
		HideContextMenu();
		return;
	}

	// If we already have an active menu for this exact selection, keep it.
	if (HasActiveContextMenu() && AreSameActorSelection(Actors, ContextMenuTargetActors))
	{
		return;
	}

	// If we have a menu but for a different selection, close it first.
	if (HasActiveContextMenu())
	{
		HideContextMenu();
	}

	UWorldBLDContextMenuRegistry* Registry = UWorldBLDContextMenuRegistry::Get();
	if (!IsValid(Registry))
	{
		return;
	}

	// Determine whether the selection resolves to a single supported target type (factory), or is mixed.
	AActor* FirstTargetActor = TargetActors[0];
	const TScriptInterface<IWorldBLDContextMenuFactory> FirstFactory = Registry->FindFactoryForActor(FirstTargetActor);
	const IWorldBLDContextMenuFactory* FirstFactoryInterface = FirstFactory.GetInterface();

	bool bMixedTargetTypes = false;

	if ((FirstFactoryInterface == nullptr) || !FirstFactoryInterface->CanCreateContextMenuForActor(FirstTargetActor))
	{
		HideContextMenu();
		return;
	}

	UClass* CommonTargetClass = FirstTargetActor->GetClass();

	for (AActor* TargetActor : TargetActors)
	{
		if (!IsValid(TargetActor))
		{
			bMixedTargetTypes = true;
			break;
		}

		const TScriptInterface<IWorldBLDContextMenuFactory> Factory = Registry->FindFactoryForActor(TargetActor);
		const IWorldBLDContextMenuFactory* FactoryInterface = Factory.GetInterface();
		if ((FactoryInterface == nullptr) || !FactoryInterface->CanCreateContextMenuForActor(TargetActor))
		{
			bMixedTargetTypes = true;
			break;
		}

		// Mixed actor type selection is detected at the *target* actor level (after provider indirection).
		if (TargetActor->GetClass() != CommonTargetClass)
		{
			bMixedTargetTypes = true;
			break;
		}
	}

	TSharedRef<SWidget> ContentWidget = SNullWidget::NullWidget;
	FText Title = FText::GetEmpty();
	AActor* MenuPositionActor = FirstTargetActor;

	if (bMixedTargetTypes)
	{
		Title = LOCTEXT("MixedSelectionTitle", "Selection");
		ContentWidget = MakeErrorContent(LOCTEXT("MixedSelectionError", "Mixed actor types selected.\nPlease select actors that resolve to a single supported target type."));
	}
	else
	{
		// Use display name (adds spaces like "CityBlock" -> "City Block" and respects DisplayName metadata).
		Title = CommonTargetClass->GetDisplayNameText();
		ContentWidget = FirstFactoryInterface->CreateContextMenuWidget(TargetActors);
		MenuPositionActor = FirstTargetActor;
	}

	TSharedRef<SWorldBLDContextMenu> ContextMenuWidget =
		SNew(SWorldBLDContextMenu)
		.Title(Title)
		.Content(ContentWidget)
		.TargetActor(MenuPositionActor)
		.TargetActors(TargetActors)
		.OnRequestClose(FSimpleDelegate::CreateUObject(this, &UWorldBLDEdMode::HideContextMenu))
		;

	FLevelEditorModule& LevelEditor = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
	const TSharedPtr<ILevelEditor> PinnedEditor = LevelEditor.GetLevelEditorInstance().Pin();
	if (!PinnedEditor.IsValid())
	{
		return;
	}

	const TSharedPtr<SLevelViewport> ActiveViewport = PinnedEditor->GetActiveViewportInterface();
	if (!ActiveViewport.IsValid())
	{
		return;
	}

	const TSharedRef<SWorldBLDContextMenuViewportOverlay> Overlay =
		SNew(SWorldBLDContextMenuViewportOverlay)
		.Padding(FMargin(24.0f))
		.Panel(ContextMenuWidget);

	ActiveViewport->AddOverlayWidget(Overlay);
	ActiveContextMenuHostViewport = ActiveViewport;
	ActiveContextMenuOverlayWidget = Overlay;

	ContextMenuTargetActor = MenuPositionActor;
	ContextMenuTargetActors.Reset();
	for (AActor* Actor : Actors)
	{
		ContextMenuTargetActors.Add(Actor);
	}
}

bool UWorldBLDEdMode::ValidateContextMenuTargets() const
{
	if (!HasActiveContextMenu() || ContextMenuTargetActors.IsEmpty() || (GEditor == nullptr))
	{
		return false;
	}

	for (const TWeakObjectPtr<AActor>& WeakActor : ContextMenuTargetActors)
	{
		if (!WeakActor.IsValid())
		{
			return false;
		}
	}

	USelection* Selected = GEditor->GetSelectedActors();
	if (Selected == nullptr)
	{
		return false;
	}

	TArray<AActor*> CurrentSelection;
	for (FSelectionIterator It(*Selected); It; ++It)
	{
		if (AActor* Actor = Cast<AActor>(*It))
		{
			CurrentSelection.Add(Actor);
		}
	}

	return !CurrentSelection.IsEmpty() && AreSameActorSelection(CurrentSelection, ContextMenuTargetActors);
}

void UWorldBLDEdMode::SwitchToMainWorldBLDWidget()
{
	InstallDefaultSelectionTool();
}

void UWorldBLDEdMode::PushEditController(UWorldBLDEditController* Controller)
{


	if (IsValid(Controller))
	{
		ToolModeStack.Remove(Controller);
		if (ToolModeStack.Num() > 0)
		{
			ToolModeStack.Last()->ToolResign();
		}
		ToolModeStack.Add(Controller);
		
		UBlueprint* ToolBlueprint = UBlueprint::GetBlueprintFromClass(Controller->GetClass());
		if (IsValid(ToolBlueprint))
		{
			ToolBlueprint->OnCompiled().AddUObject(this, &UWorldBLDEdMode::RegenerateContents);
		}
		
		Controller->AddToEditorLevelViewport();
		Controller->ToolBegin();

		// Hide any activee context menu while a non-exempt controller is active (to prevent interference).
		// Note: HideContextMenu() clears bContextMenuHiddenByTool, so preserve our "hidden by tool" intent after hiding.
		if (!WorldBLDEditorContextMenu::IsControllerAllowedToShowContextMenu(this, Controller))
		{
			const bool bHadMenu = HasActiveContextMenu();
			HideContextMenu();
			bContextMenuHiddenByTool = bHadMenu;
		}

		RefreshViewportToolbarVisibility();
	}
}

void UWorldBLDEdMode::PopEditController(UWorldBLDEditController* OptionalController)
{
	if (IsValid(OptionalController))
	{
		OptionalController->ToolResign();
		OptionalController->RemoveFromEditorLevelViewport();
		OptionalController->RemoveFromParent();
		ToolModeStack.Remove(OptionalController);
	}
	else if (ensure(!ToolModeStack.IsEmpty()))
	{
		if (IsValid(ToolModeStack.Last()))
		{
			ToolModeStack.Last()->ToolResign();
			ToolModeStack.Last()->RemoveFromEditorLevelViewport();
			ToolModeStack.Last()->RemoveFromParent();
		}
		ToolModeStack.Pop();
	}

	// New tool on top of stack get a notification
	if ((ToolModeStack.Num() > 0) && IsValid(ToolModeStack.Last()))
	{
		ToolModeStack.Last()->ToolActivate();
	}

	// If a tool previously hid the context menu, re-evaluate after popping.
	if (bContextMenuHiddenByTool)
	{
		bContextMenuHiddenByTool = false;

		const UWorldBLDEditController* NewTop = GetActiveEditController();
		if (WorldBLDEditorContextMenu::IsControllerAllowedToShowContextMenu(this, NewTop))
		{
			TArray<AActor*> SelectedActors;
			if (GEditor && GEditor->GetSelectedActors())
			{
				for (FSelectionIterator It(*GEditor->GetSelectedActors()); It; ++It)
				{
					if (AActor* Actor = Cast<AActor>(*It))
					{
						SelectedActors.Add(Actor);
					}
				}
			}

			if (IsContextMenuRelevantForSelection(SelectedActors))
			{
				ShowContextMenuForActors(SelectedActors);
			}
			else
			{
				HideContextMenu();
			}
		}
	}

	RefreshViewportToolbarVisibility();
}

void UWorldBLDEdMode::ClearToolModeStack()
{
	while (!ToolModeStack.IsEmpty())
	{
		UWorldBLDEditController* Controller = ToolModeStack.Last();
		if (IsValid(Controller))
		{
			Controller->ToolExit(/* Force? */ true);
			if (ToolModeStack.Contains(Controller))
			{
				PopEditController(Controller);
			}
		}
		else
		{
			PopEditController(Controller);
		}

		TObjectPtr<UUserWidget> WidgetVersion = Cast<UUserWidget>(Controller);
		DestructWidget(WidgetVersion);
	}
}

void UWorldBLDEdMode::InstallDefaultSelectionTool()
{
	ClearToolModeStack();

	TObjectPtr<UUserWidget> NewTool {nullptr};
	TSoftClassPtr<UUserWidget> LoadedToolClass = UWorldBLDDefaultEditController::StaticClass();

	// Default tool can be overridden in BP config, treat missing packages (eg optional plugins) as "not configured".
	if (!DefaultToolClass.IsNull())
	{
		const FSoftObjectPath DefaultToolPath = DefaultToolClass.ToSoftObjectPath();
		const FString DefaultToolPackageName = DefaultToolPath.GetLongPackageName();
		if (WorldBLDEditorContextMenu::IsResolvableClassPackage(DefaultToolPackageName))
		{
			if (const TSubclassOf<UWorldBLDEditController> SuppliedTool = DefaultToolClass.LoadSynchronous())
			{
				LoadedToolClass = SuppliedTool;
			}
		}
	}

	TryConstructUserWidget(NewTool, LoadedToolClass, /* Force */ true);

	if (IsValid(NewTool))
	{
		PushEditController(Cast<UWorldBLDEditController>(NewTool));
	}
	else
	{
		UE_LOG(
			LogWorldBLDEditor,
			Verbose,
			TEXT("Default edit controller widget was not constructed yet for class '%s'."),
			*LoadedToolClass.ToString());
	}
	
}

bool UWorldBLDEdMode::IsLicensed(const FString& Credentials, const FString& ToolName) const
{
	(void)Credentials;

	if (ToolName.IsEmpty() || (GEditor == nullptr))
	{
		return false;
	}

	if (const UWorldBLDAuthSubsystem* AuthSubsystem = GEditor->GetEditorSubsystem<UWorldBLDAuthSubsystem>())
	{
		return AuthSubsystem->HasLicenseForTool(ToolName);
	}

	return false;
}

///////////////////////////////////////////////////////////////////////////////////////////////////

FWorldBLDEdModeToolkit::FWorldBLDEdModeToolkit()
{
    // Empty
}

FName FWorldBLDEdModeToolkit::GetToolkitFName() const 
{ 
    return FName("WorldBLDEdMode"); 
}

FText FWorldBLDEdModeToolkit::GetBaseToolkitName() const 
{ 
    return NSLOCTEXT("WorldBLDEditorToolkit", "DisplayName", "City Builder"); 
}

TSharedPtr<class SWidget> FWorldBLDEdModeToolkit::GetInlineContent() const 
{
    return nullptr;
}

TSharedPtr<SDockTab> FWorldBLDEdModeToolkit::GetPrimaryTab() const
{
	return PrimaryTab.Pin();
}

void FWorldBLDEdModeToolkit::InvokeUI()
{
	Super::InvokeUI();
	if (EditModeRef.IsValid())
	{
		EditModeRef->InstallDefaultSelectionTool();
	}
}

///////////////////////////////////////////////////////////////////////////////////////////////////

bool UWorldBLDEdMode::IsSelectionAllowed(AActor* InActor, bool bInSelection) const
{
	if (const UWorldBLDEditController* Controller = GetActiveEditController())
	{
		return Controller->AllowStandardSelectionControls() || (Controller->ActiveBrushActor == InActor);
	}
	return true;
}

bool FWorldBLDSelectModeWidgetHelper::AllowWidgetMove()
{
	if (const UWorldBLDEditController* Controller = GetActiveController())
	{
		return Controller->AllowStandardSelectionControls();
	}
	return Super::AllowWidgetMove();
}

bool FWorldBLDSelectModeWidgetHelper::CanCycleWidgetMode() const
{
	if (const UWorldBLDEditController* Controller = GetActiveController())
	{
		return Controller->AllowStandardSelectionControls();
	}
	return Super::CanCycleWidgetMode();
}

bool FWorldBLDSelectModeWidgetHelper::ShowModeWidgets() const
{
	if (const UWorldBLDEditController* Controller = GetActiveController())
	{
		return Controller->AllowStandardSelectionControls();
	}
	return Super::ShowModeWidgets();
}

bool FWorldBLDSelectModeWidgetHelper::ShouldDrawWidget() const
{
	bool bDoDefaultBehavior = true;
	if (const UWorldBLDEditController* Controller = GetActiveController())
	{
		bDoDefaultBehavior = Controller->AllowStandardSelectionControls();
	}

	if (GCurrentLevelEditingViewportClient && bDoDefaultBehavior)
	{
		const FTypedElementListConstRef ElementsToManipulate = GCurrentLevelEditingViewportClient->GetElementsToManipulate();
		return ElementsToManipulate->Num() > 0;
	}
	return false;
}

bool FWorldBLDSelectModeWidgetHelper::UsesTransformWidget() const
{
	if (const UWorldBLDEditController* Controller = GetActiveController())
	{
        // If controller requests a custom widget, we always use transform widget
        if (Controller->WantsCustomTransformWidget())
        {
            return true;
        }
        return Controller->AllowStandardSelectionControls();
	}
	return Super::UsesTransformWidget();
}

// Note: FLegacyEdModeWidgetHelper does not have a mode-parameter overload in all engine versions,
// so we only override the parameterless UsesTransformWidget above.

bool FWorldBLDSelectModeWidgetHelper::UsesPropertyWidgets() const
{
	if (const UWorldBLDEditController* Controller = GetActiveController())
	{
		return Controller->AllowStandardSelectionControls();
	}
	return true;
}

EAxisList::Type FWorldBLDSelectModeWidgetHelper::GetWidgetAxisToDraw(UE::Widget::EWidgetMode CheckMode) const
{
    if (const UWorldBLDEditController* Controller = GetActiveController())
    {
        if (Controller->WantsCustomTransformWidget())
        {
            return Controller->GetWidgetAxisMask();
        }
    }
    return Super::GetWidgetAxisToDraw(CheckMode);
}

FVector FWorldBLDSelectModeWidgetHelper::GetWidgetLocation() const
{
    if (const UWorldBLDEditController* Controller = GetActiveController())
    {
        if (Controller->WantsCustomTransformWidget())
        {
            return Controller->GetDesiredWidgetLocation();
        }
    }
    return Super::GetWidgetLocation();
}

void FWorldBLDSelectModeWidgetHelper::ActorSelectionChangeNotify()
{
	if (UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
	{
		if (UWorldBLDEditController* Controller = GetActiveController())
		{
			int Index = EdMode->ToolModeStack.Find(Controller);
			while (Index >= 0)
			{
				Controller = EdMode->ToolModeStack[Index];				
				if (!Controller->ForceEditorSelectionToActiveBrushActor())
				{
					Controller->OnActorSelectionSetChanged();
				}				
				if (Controller->ConsumeSelectionControls())
				{
					break;
				}
				Index -= 1;
			}			
		}

		// Context menu integration: only show for exempt controller classes.
		const UWorldBLDEditController* ActiveController = GetActiveController();
		if (!WorldBLDEditorContextMenu::IsControllerAllowedToShowContextMenu(EdMode, ActiveController))
		{
			EdMode->HideContextMenu();
			return;
		}

		// If our existing targets are stale (deleted, deselected), close the window.
		if (EdMode->HasActiveContextMenu() && !EdMode->ValidateContextMenuTargets())
		{
			EdMode->HideContextMenu();
		}

		TArray<AActor*> SelectedActors;
		if (GEditor && GEditor->GetSelectedActors())
		{
			for (FSelectionIterator It(*GEditor->GetSelectedActors()); It; ++It)
			{
				if (AActor* Actor = Cast<AActor>(*It))
				{
					SelectedActors.Add(Actor);
				}
			}
		}

		if (SelectedActors.IsEmpty())
		{
			EdMode->HideContextMenu();
			return;
		}

		// Avoid re-creating if selection hasn't changed.
		bool bSelectionMatchesExisting = false;
		if (EdMode->HasActiveContextMenu())
		{
			bSelectionMatchesExisting = UWorldBLDEdMode::AreSameActorSelection(SelectedActors, EdMode->ContextMenuTargetActors);
		}

		if (!bSelectionMatchesExisting)
		{
			if (EdMode->IsContextMenuRelevantForSelection(SelectedActors))
			{
				EdMode->ShowContextMenuForActors(SelectedActors);
			}
			else
			{
				EdMode->HideContextMenu();
			}
		}
	}
}

UWorldBLDEditController* FWorldBLDSelectModeWidgetHelper::GetActiveController() const
{
	UWorldBLDEditController* Controller = nullptr;
	if (const UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
	{
		Controller = EdMode->GetActiveEditController();
	}
	return Controller;
}

///////////////////////////////////////////////////////////////////////////////////////////////////

void UWorldBLDEdModeLicenseSettings::PostEditChangeProperty(struct FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);
	OnLicenseChanged.Broadcast(this, LicenseFile);
}

void UWorldBLDEdModeLicenseSettings::ResetLicense()
{
	LicenseFile.FilePath = TEXT("");
	SaveConfig();
	OnLicenseChanged.Broadcast(this, LicenseFile);
}


#undef LOCTEXT_NAMESPACE

