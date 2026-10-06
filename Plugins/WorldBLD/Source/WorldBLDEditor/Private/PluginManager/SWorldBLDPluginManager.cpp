// Copyright WorldBLD LLC. All rights reserved.

#include "PluginManager/SWorldBLDPluginManager.h"

#include "ContextMenu/WorldBLDContextMenuStyle.h"
#include "Downloader/CurlDownloaderLibrary.h"
#include "WorldBLDEditorToolkit.h"

#include "Brushes/SlateColorBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Editor.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/MessageDialog.h"
#include "Misc/Paths.h"
#include "Styling/AppStyle.h"
#include "Styling/CoreStyle.h"
#include "Styling/StyleColors.h"
#include "Widgets/Images/SImage.h"
#include "UnrealEdMisc.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SGridPanel.h"
#include "Widgets/Notifications/SProgressBar.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SWindow.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WorldBLDPluginManager"

namespace WorldBLDPluginManagerInternal
{
	static constexpr float DialogWidth = 880.0f;
	static constexpr float DialogHeight = 570.0f;
	static constexpr float SidebarWidth = 232.0f;
	static constexpr float ToolIconExtent = 128.0f;

	static FString NormalizeToolId(const FString& ToolName)
	{
		const FString TrimmedName = ToolName.TrimStartAndEnd();
		static const TCHAR* KnownToolIds[] =
		{
			TEXT("WorldBLD"),
			TEXT("RoadBLD"),
			TEXT("CityBLD"),
			TEXT("TwinBLD"),
			TEXT("CrowdBLD")
		};

		for (const TCHAR* KnownToolId : KnownToolIds)
		{
			if (TrimmedName.Equals(KnownToolId, ESearchCase::IgnoreCase))
			{
				return KnownToolId;
			}
		}

		return TrimmedName;
	}
}

void SWorldBLDPluginManager::Construct(const FArguments& InArgs)
{
	using namespace WorldBLDPluginManagerInternal;

	ToolId = InArgs._ToolId.ToString();
	EdMode = InArgs._EdMode;
	Downloader = InArgs._Downloader;
	ProjectPluginsPath = FPaths::ConvertRelativePathToFull(FPaths::ProjectPluginsDir());
	FPaths::NormalizeDirectoryName(ProjectPluginsPath);
	RefreshToolMetadata();

	TArray<FString> IconCandidates;
	if (const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(ToolId))
	{
		IconCandidates.Add(Plugin->GetBaseDir() / TEXT("Resources/Icon128.png"));
	}
	IconCandidates.AddUnique(ProjectPluginsPath / ToolId / TEXT("Resources/Icon128.png"));
	for (FString IconPath : IconCandidates)
	{
		IconPath = FPaths::ConvertRelativePathToFull(IconPath);
		if (IFileManager::Get().FileExists(*IconPath))
		{
			ToolIconBrush = MakeShared<FSlateDynamicImageBrush>(
				FName(*IconPath),
				FVector2D(ToolIconExtent, ToolIconExtent));
			break;
		}
	}

	const FVector4 PanelRadii(8.0f, 8.0f, 8.0f, 8.0f);
	PanelBrush = MakeShared<FSlateRoundedBoxBrush>(FStyleColors::Background, PanelRadii);
	SidebarBrush = MakeShared<FSlateRoundedBoxBrush>(
		FStyleColors::Recessed,
		FVector4(8.0f, 0.0f, 0.0f, 0.0f));
	FooterBrush = MakeShared<FSlateRoundedBoxBrush>(
		FStyleColors::Background,
		FVector4(0.0f, 0.0f, 8.0f, 8.0f));
	IconWellBrush = MakeShared<FSlateRoundedBoxBrush>(
		FStyleColors::Header,
		FVector4(4.0f, 4.0f, 4.0f, 4.0f));
	AccentBrush = MakeShared<FSlateColorBrush>(WorldBLDContextMenuStyle::GetHighlightRedColor());

	{
		const FVector4 CardRadii(5.0f, 5.0f, 5.0f, 5.0f);
		FSlateBrushOutlineSettings CardOutline;
		CardOutline.CornerRadii = CardRadii;
		CardOutline.Color = FStyleColors::DropdownOutline;
		CardOutline.Width = 1.0f;
		CardOutline.RoundingType = ESlateBrushRoundingType::FixedRadius;
		CardOutline.bUseBrushTransparency = false;

		TSharedPtr<FSlateRoundedBoxBrush> RoundedCardBrush =
			MakeShared<FSlateRoundedBoxBrush>(FStyleColors::Recessed, CardRadii);
		RoundedCardBrush->OutlineSettings = CardOutline;
		CardBrush = RoundedCardBrush;
	}

	ProgressBarStyle = MakeShared<FProgressBarStyle>(
		FAppStyle::Get().GetWidgetStyle<FProgressBarStyle>(TEXT("ProgressBar")));
	ProgressBarStyle->SetFillImage(FSlateColorBrush(FLinearColor::White));

	ChildSlot
	[
		SNew(SBox)
		.WidthOverride(DialogWidth)
		.HeightOverride(DialogHeight)
		[
			SNew(SBorder)
			.BorderImage(PanelBrush.Get())
			.Padding(0.0f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.FillHeight(1.0f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						SNew(SBox)
						.WidthOverride(SidebarWidth)
						[
							SNew(SBorder)
							.BorderImage(SidebarBrush.Get())
							.Padding(FMargin(28.0f, 28.0f, 24.0f, 24.0f))
							[
								SNew(SVerticalBox)
								+ SVerticalBox::Slot()
								.AutoHeight()
								.HAlign(HAlign_Center)
								[
									SNew(SBox)
									.WidthOverride(ToolIconExtent)
									.HeightOverride(ToolIconExtent)
									.Visibility_Lambda([this]()
									{
										return ToolIconBrush.IsValid()
											? EVisibility::Visible
											: EVisibility::Collapsed;
									})
									[
										SNew(SImage)
										.Image(this, &SWorldBLDPluginManager::GetToolIconBrush)
									]
								]
								+ SVerticalBox::Slot()
								.AutoHeight()
								.Padding(FMargin(0.0f, 38.0f, 0.0f, 0.0f))
								[
									SNew(STextBlock)
									.Text(this, &SWorldBLDPluginManager::GetDisplayNameText)
									.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 22))
								]
								+ SVerticalBox::Slot()
								.AutoHeight()
								.Padding(FMargin(0.0f, 12.0f, 0.0f, 16.0f))
								[
									SNew(SBox)
									.HeightOverride(2.0f)
									[
										SNew(SBorder)
										.BorderImage(AccentBrush.Get())
									]
								]
								+ SVerticalBox::Slot()
								.AutoHeight()
								[
									SNew(STextBlock)
									.Text(this, &SWorldBLDPluginManager::GetManagerDescriptionText)
									.AutoWrapText(true)
									.ColorAndOpacity(FSlateColor::UseSubduedForeground())
									.LineHeightPercentage(1.15f)
								]
							]
						]
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					[
						SNew(SBorder)
						.BorderImage(FAppStyle::GetBrush(TEXT("NoBorder")))
						.Padding(FMargin(24.0f, 24.0f, 24.0f, 20.0f))
						[
							SNew(SVerticalBox)
							+ SVerticalBox::Slot()
							.AutoHeight()
							[
								SNew(SHorizontalBox)
								+ SHorizontalBox::Slot()
								.AutoWidth()
								[
									SNew(SBox)
									.WidthOverride(48.0f)
									.HeightOverride(48.0f)
									[
										SNew(SBorder)
										.BorderImage(IconWellBrush.Get())
										.HAlign(HAlign_Center)
										.VAlign(VAlign_Center)
										[
											SNew(SImage)
											.Image(FAppStyle::GetBrush(TEXT("Icons.Package")))
											.DesiredSizeOverride(FVector2D(24.0f, 24.0f))
										]
									]
								]
								+ SHorizontalBox::Slot()
								.AutoWidth()
								.VAlign(VAlign_Center)
								.Padding(FMargin(16.0f, 0.0f))
								[
									SNew(STextBlock)
									.Text(LOCTEXT("InstallationStatusHeading", "Installation Status"))
									.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 14))
								]
							]
							+ SVerticalBox::Slot()
							.AutoHeight()
							.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
							[
								SNew(SBorder)
								.BorderImage(CardBrush.Get())
								.Padding(FMargin(18.0f, 13.0f))
								[
									SNew(SGridPanel)
									.FillColumn(0, 1.0f)
									.FillColumn(1, 1.25f)
									.FillColumn(2, 1.0f)
									+ SGridPanel::Slot(0, 0)
									[
										SNew(SVerticalBox)
										+ SVerticalBox::Slot()
										.AutoHeight()
										[
											SNew(STextBlock)
											.Text(LOCTEXT("ToolNameLabel", "Tool name"))
											.ColorAndOpacity(FSlateColor::UseSubduedForeground())
										]
										+ SVerticalBox::Slot()
										.AutoHeight()
										.Padding(FMargin(0.0f, 6.0f, 0.0f, 0.0f))
										[
											SNew(STextBlock)
											.Text(this, &SWorldBLDPluginManager::GetDisplayNameText)
										]
									]
									+ SGridPanel::Slot(1, 0)
									[
										SNew(SVerticalBox)
										+ SVerticalBox::Slot()
										.AutoHeight()
										[
											SNew(STextBlock)
											.Text(LOCTEXT("LatestVersionLabel", "Latest available version"))
											.ColorAndOpacity(FSlateColor::UseSubduedForeground())
										]
										+ SVerticalBox::Slot()
										.AutoHeight()
										.Padding(FMargin(0.0f, 6.0f, 0.0f, 0.0f))
										[
											SNew(STextBlock)
											.Text(this, &SWorldBLDPluginManager::GetLatestVersionText)
										]
									]
									+ SGridPanel::Slot(2, 0)
									[
										SNew(SVerticalBox)
										+ SVerticalBox::Slot()
										.AutoHeight()
										[
											SNew(STextBlock)
											.Text(LOCTEXT("InstalledVersionLabel", "Installed version"))
											.ColorAndOpacity(FSlateColor::UseSubduedForeground())
										]
										+ SVerticalBox::Slot()
										.AutoHeight()
										.Padding(FMargin(0.0f, 6.0f, 0.0f, 0.0f))
										[
											SNew(STextBlock)
											.Text(this, &SWorldBLDPluginManager::GetInstalledVersionText)
											.ColorAndOpacity_Lambda([this]()
											{
												return IsToolInstalled()
													? FSlateColor::UseForeground()
													: FSlateColor(WorldBLDContextMenuStyle::GetHighlightRedColor());
											})
										]
									]
								]
							]
							+ SVerticalBox::Slot()
							.AutoHeight()
							.Padding(FMargin(0.0f, 22.0f, 0.0f, 0.0f))
							[
								SNew(SHorizontalBox)
								+ SHorizontalBox::Slot()
								.AutoWidth()
								[
									SNew(SBox)
									.WidthOverride(48.0f)
									.HeightOverride(48.0f)
									[
										SNew(SBorder)
										.BorderImage(IconWellBrush.Get())
										.HAlign(HAlign_Center)
										.VAlign(VAlign_Center)
										[
											SNew(SImage)
											.Image(FAppStyle::GetBrush(TEXT("Icons.FolderClosed")))
											.DesiredSizeOverride(FVector2D(24.0f, 24.0f))
										]
									]
								]
								+ SHorizontalBox::Slot()
								.AutoWidth()
								.VAlign(VAlign_Center)
								.Padding(FMargin(16.0f, 0.0f))
								[
									SNew(STextBlock)
									.Text(LOCTEXT("InstallationPathLabel", "Installation Path"))
									.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 14))
								]
							]
							+ SVerticalBox::Slot()
							.AutoHeight()
							.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
							[
								SNew(SBorder)
								.BorderImage(CardBrush.Get())
								.Padding(FMargin(18.0f, 10.0f))
								[
									SNew(SHorizontalBox)
									+ SHorizontalBox::Slot()
									.FillWidth(1.0f)
									.VAlign(VAlign_Center)
									[
										SNew(STextBlock)
										.Text(FText::FromString(ProjectPluginsPath))
										.OverflowPolicy(ETextOverflowPolicy::Ellipsis)
										.ColorAndOpacity(FSlateColor::UseSubduedForeground())
									]
									+ SHorizontalBox::Slot()
									.AutoWidth()
									.Padding(FMargin(12.0f, 0.0f, 0.0f, 0.0f))
									[
										SNew(SButton)
										.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
										.Text(LOCTEXT("OpenFolderButton", "Open in Explorer"))
										.ToolTipText(LOCTEXT("OpenFolderTooltip", "Open the current project's Plugins directory in Windows Explorer"))
										.OnClicked(this, &SWorldBLDPluginManager::HandleOpenPluginsFolderClicked)
									]
								]
							]
							+ SVerticalBox::Slot()
							.AutoHeight()
							.Padding(FMargin(0.0f, 16.0f, 0.0f, 0.0f))
							[
								SNew(SProgressBar)
								.Style(ProgressBarStyle.Get())
								.Percent(this, &SWorldBLDPluginManager::GetDownloadProgress)
								.Visibility(this, &SWorldBLDPluginManager::GetProgressVisibility)
								.FillColorAndOpacity(WorldBLDContextMenuStyle::GetHighlightRedColor())
							]
							+ SVerticalBox::Slot()
							.FillHeight(1.0f)
							.Padding(FMargin(0.0f, 16.0f, 0.0f, 0.0f))
							.VAlign(VAlign_Bottom)
							[
								SNew(SBorder)
								.BorderImage(CardBrush.Get())
								.Padding(FMargin(18.0f, 16.0f))
								[
									SNew(SHorizontalBox)
									+ SHorizontalBox::Slot()
									.AutoWidth()
									.VAlign(VAlign_Top)
									.Padding(FMargin(0.0f, 1.0f, 16.0f, 0.0f))
									[
										SNew(SImage)
										.Image(FAppStyle::GetBrush(TEXT("Icons.Info")))
										.DesiredSizeOverride(FVector2D(28.0f, 28.0f))
										.ColorAndOpacity(FLinearColor(0.38f, 0.55f, 0.82f, 1.0f))
									]
									+ SHorizontalBox::Slot()
									.FillWidth(1.0f)
									[
										SNew(SVerticalBox)
										+ SVerticalBox::Slot()
										.AutoHeight()
										[
											SNew(STextBlock)
											.Text(this, &SWorldBLDPluginManager::GetStatusText)
											.AutoWrapText(true)
											.Font(FAppStyle::GetFontStyle(TEXT("NormalFontBold")))
											.ColorAndOpacity_Lambda([this]()
											{
												return bOperationFailed
													? FSlateColor(FLinearColor(0.9f, 0.25f, 0.25f))
													: FSlateColor::UseForeground();
											})
										]
										+ SVerticalBox::Slot()
										.AutoHeight()
										.Padding(FMargin(0.0f, 5.0f, 0.0f, 0.0f))
										[
											SNew(STextBlock)
											.Text(this, &SWorldBLDPluginManager::GetStatusDetailText)
											.AutoWrapText(true)
											.ColorAndOpacity(FSlateColor::UseSubduedForeground())
										]
									]
								]
							]
						]
					]
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(SBorder)
					.BorderImage(FooterBrush.Get())
					.Padding(FMargin(24.0f, 14.0f))
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot()
						.AutoWidth()
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.Text(LOCTEXT("LearnMoreButton", "Learn More"))
							.ToolTipText(LOCTEXT("LearnMoreTooltip", "Open this tool's page on worldbld.com"))
							.OnClicked(this, &SWorldBLDPluginManager::HandleLearnMoreClicked)
						]
						+ SHorizontalBox::Slot()
						.FillWidth(1.0f)
						[
							SNew(SSpacer)
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.Text(LOCTEXT("CloseButton", "Close"))
							.OnClicked(this, &SWorldBLDPluginManager::HandleCloseClicked)
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.Padding(FMargin(10.0f, 0.0f, 0.0f, 0.0f))
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetToolSwitchMenuInstallButtonStyle())
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.Text(LOCTEXT("InstallButton", "Install"))
							.IsEnabled(this, &SWorldBLDPluginManager::CanRunLifecycleAction)
							.Visibility(this, &SWorldBLDPluginManager::GetInstallButtonVisibility)
							.OnClicked(this, &SWorldBLDPluginManager::HandleInstallClicked)
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.Padding(FMargin(10.0f, 0.0f, 0.0f, 0.0f))
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetToolSwitchMenuInstallButtonStyle())
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.Text(LOCTEXT("UpdateButton", "Update"))
							.IsEnabled(this, &SWorldBLDPluginManager::CanRunLifecycleAction)
							.Visibility(this, &SWorldBLDPluginManager::GetUpdateButtonVisibility)
							.OnClicked(this, &SWorldBLDPluginManager::HandleUpdateClicked)
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.Padding(FMargin(10.0f, 0.0f, 0.0f, 0.0f))
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.Text(LOCTEXT("UninstallButton", "Uninstall"))
							.IsEnabled(this, &SWorldBLDPluginManager::CanRunLifecycleAction)
							.Visibility(this, &SWorldBLDPluginManager::GetUninstallButtonVisibility)
							.OnClicked(this, &SWorldBLDPluginManager::HandleUninstallClicked)
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.Padding(FMargin(10.0f, 0.0f, 0.0f, 0.0f))
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetToolSwitchMenuInstallButtonStyle())
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.Text(LOCTEXT("RestartButton", "Restart Editor"))
							.Visibility(this, &SWorldBLDPluginManager::GetRestartButtonVisibility)
							.OnClicked(this, &SWorldBLDPluginManager::HandleRestartClicked)
						]
					]
				]
			]
		]
	];
}

void SWorldBLDPluginManager::SetHostWindow(const TSharedRef<SWindow>& InWindow)
{
	HostWindow = InWindow;
}

void SWorldBLDPluginManager::ShowModalForTool(
	FName InToolId,
	TWeakObjectPtr<UWorldBLDEdMode> InEdMode,
	TWeakObjectPtr<UCurlDownloaderLibrary> InDownloader)
{
	if (InToolId.IsNone() || InToolId.ToString().Equals(TEXT("WorldBLD"), ESearchCase::IgnoreCase)
		|| !FSlateApplication::IsInitialized())
	{
		return;
	}

	if (!InEdMode.IsValid())
	{
		InEdMode = UWorldBLDEdMode::GetWorldBLDEdMode();
	}
	if (!InDownloader.IsValid() && GEditor != nullptr)
	{
		InDownloader = GEditor->GetEditorSubsystem<UCurlDownloaderLibrary>();
	}

	FSlateApplication::Get().DismissAllMenus();

	TSharedPtr<SWorldBLDPluginManager> ManagerWidget;
	const TSharedRef<SWindow> Window = SNew(SWindow)
		.Title(FText::Format(
			LOCTEXT("WindowTitle", "WorldBLD - Manage {0} Installation"),
			FText::FromName(InToolId)))
		.SizingRule(ESizingRule::Autosized)
		.MinWidth(WorldBLDPluginManagerInternal::DialogWidth)
		.SupportsMaximize(false)
		.SupportsMinimize(false);

	Window->SetContent(
		SAssignNew(ManagerWidget, SWorldBLDPluginManager)
		.ToolId(InToolId)
		.EdMode(InEdMode)
		.Downloader(InDownloader));

	if (ManagerWidget.IsValid())
	{
		ManagerWidget->SetHostWindow(Window);
	}

	FSlateApplication::Get().AddModalWindow(Window, FSlateApplication::Get().GetActiveTopLevelWindow());
}

void SWorldBLDPluginManager::RefreshToolMetadata()
{
	bHasServerMetadata = false;
	DisplayName = ToolId;
	ToolDescription.Reset();
	ServerVersion.Reset();
	DownloadUrl.Reset();
	ServerSHA1.Reset();
	RequiredToolIds.Reset();

	if (const UWorldBLDEdMode* EdModePtr = EdMode.Get())
	{
		for (const FPluginToolData& ToolData : EdModePtr->AvailableTools)
		{
			const FString AvailableToolId = WorldBLDPluginManagerInternal::NormalizeToolId(ToolData.ToolName);
			if (!AvailableToolId.Equals(ToolId, ESearchCase::IgnoreCase))
			{
				continue;
			}

			bHasServerMetadata = true;
			DisplayName = ToolData.ToolName.IsEmpty() ? ToolId : ToolData.ToolName;
			ToolDescription = ToolData.Description;
			ServerVersion = ToolData.Version;
			DownloadUrl = ToolData.DownloadLink;
			ServerSHA1 = ToolData.SHA1;
			RequiredToolIds = ToolData.RequiredToolIds;
			break;
		}
	}

	if (DisplayName.Equals(ToolId, ESearchCase::CaseSensitive))
	{
		if (const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(ToolId))
		{
			const FString& FriendlyName = Plugin->GetDescriptor().FriendlyName;
			if (!FriendlyName.IsEmpty())
			{
				DisplayName = FriendlyName;
			}
		}
	}
}

bool SWorldBLDPluginManager::IsToolInstalled() const
{
	return !bUninstallRequested && IPluginManager::Get().FindPlugin(ToolId).IsValid();
}

bool SWorldBLDPluginManager::IsOperationInProgress() const
{
	const UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
	return DownloaderPtr != nullptr && DownloaderPtr->IsDownloadInProgress(ToolId);
}

bool SWorldBLDPluginManager::HasPendingRestart() const
{
	const UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
	return bRestartRequired
		|| UCurlDownloaderLibrary::HasPendingStagedUpdate(ToolId)
		|| (DownloaderPtr != nullptr && DownloaderPtr->HasPendingInstallRestart(ToolId));
}

bool SWorldBLDPluginManager::AreDependenciesInstalled(TArray<FString>& OutMissingDependencies) const
{
	OutMissingDependencies.Reset();
	for (const FString& RequiredToolIdRaw : RequiredToolIds)
	{
		const FString RequiredToolId = WorldBLDPluginManagerInternal::NormalizeToolId(RequiredToolIdRaw);
		if (!RequiredToolId.IsEmpty() && !IPluginManager::Get().FindPlugin(RequiredToolId).IsValid())
		{
			OutMissingDependencies.AddUnique(RequiredToolId);
		}
	}
	return OutMissingDependencies.IsEmpty();
}

bool SWorldBLDPluginManager::AreDependenciesUpToDate(TArray<FString>& OutOutdatedDependencies) const
{
	OutOutdatedDependencies.Reset();

	const UWorldBLDEdMode* EdModePtr = EdMode.Get();
	if (EdModePtr == nullptr || RequiredToolIds.IsEmpty())
	{
		return true;
	}

	for (const FString& RequiredToolIdRaw : RequiredToolIds)
	{
		const FString RequiredToolId = WorldBLDPluginManagerInternal::NormalizeToolId(RequiredToolIdRaw);
		if (RequiredToolId.IsEmpty())
		{
			continue;
		}

		// WorldBLD is gated separately via IsWorldBLDPluginUpToDate() (fail-closed when unknown).
		if (RequiredToolId.Equals(TEXT("WorldBLD"), ESearchCase::IgnoreCase))
		{
			continue;
		}

		FString DependencyServerVersion;
		FString DependencyServerSHA1;
		bool bFoundServerMetadata = false;
		for (const FPluginToolData& ToolData : EdModePtr->AvailableTools)
		{
			const FString AvailableToolId = WorldBLDPluginManagerInternal::NormalizeToolId(ToolData.ToolName);
			if (!AvailableToolId.Equals(RequiredToolId, ESearchCase::IgnoreCase))
			{
				continue;
			}

			DependencyServerVersion = ToolData.Version;
			DependencyServerSHA1 = ToolData.SHA1;
			bFoundServerMetadata = true;
			break;
		}

		// Soft dependency check: if this tool's server metadata is unavailable, skip rather than block.
		if (!bFoundServerMetadata || DependencyServerVersion.TrimStartAndEnd().IsEmpty())
		{
			continue;
		}

		const EWorldBLDToolUpdateState UpdateState = EdModePtr->GetToolUpdateState(
			RequiredToolId,
			DependencyServerVersion,
			DependencyServerSHA1);
		if (UpdateState == EWorldBLDToolUpdateState::UpdateAvailable)
		{
			OutOutdatedDependencies.AddUnique(RequiredToolId);
		}
	}

	return OutOutdatedDependencies.IsEmpty();
}

FText SWorldBLDPluginManager::GetDisplayNameText() const
{
	return FText::FromString(DisplayName.IsEmpty() ? ToolId : DisplayName);
}

FText SWorldBLDPluginManager::GetManagerDescriptionText() const
{
	const FText InstallOrUpdateSentence = FText::Format(
		LOCTEXT("ManagerInstallOrUpdateSentence", "You can install or update {0} here."),
		GetDisplayNameText());

	const FString TrimmedDescription = ToolDescription.TrimStartAndEnd();
	if (TrimmedDescription.IsEmpty())
	{
		return InstallOrUpdateSentence;
	}

	return FText::Format(
		LOCTEXT("ManagerDescriptionWithServerText", "{0}\n\n{1}"),
		FText::FromString(TrimmedDescription),
		InstallOrUpdateSentence);
}

FText SWorldBLDPluginManager::GetLatestVersionText() const
{
	if (!bHasServerMetadata || ServerVersion.IsEmpty())
	{
		return LOCTEXT("VersionUnavailable", "Unavailable");
	}
	return FText::FromString(ServerVersion);
}

FText SWorldBLDPluginManager::GetInstalledVersionText() const
{
	if (!IsToolInstalled())
	{
		return LOCTEXT("NotInstalledVersion", "Not installed");
	}

	const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(ToolId);
	if (!Plugin.IsValid() || Plugin->GetDescriptor().VersionName.IsEmpty())
	{
		return LOCTEXT("UnknownInstalledVersion", "Installed (version unknown)");
	}
	return FText::FromString(Plugin->GetDescriptor().VersionName);
}

FText SWorldBLDPluginManager::GetStatusText() const
{
	if (!OperationStatus.IsEmpty())
	{
		return OperationStatus;
	}

	if (IsOperationInProgress())
	{
		const int32 Percent = FMath::Min(99, FMath::RoundToInt(GetLiveDownloadProgress() * 100.0f));
		return FText::Format(LOCTEXT("DownloadingStatus", "Downloading and installing... {0}%"), FText::AsNumber(Percent));
	}
	if (UCurlDownloaderLibrary::HasPendingStagedUpdate(ToolId))
	{
		return FText::Format(
			LOCTEXT("StagedRestartPendingStatus", "{0} update downloaded successfully. Restart Unreal to complete installation."),
			GetDisplayNameText());
	}
	if (HasPendingRestart())
	{
		return FText::Format(
			LOCTEXT("InstallRestartPendingStatus", "{0} installed successfully. Restart Unreal to complete installation."),
			GetDisplayNameText());
	}
	if (!IsToolInstalled())
	{
		return bHasServerMetadata
			? LOCTEXT("AvailableStatus", "This tool is available to install.")
			: LOCTEXT("MetadataUnavailableStatus", "Latest release information is unavailable. Refresh the WorldBLD tool list and try again.");
	}

	if (const UWorldBLDEdMode* EdModePtr = EdMode.Get())
	{
		switch (EdModePtr->GetToolUpdateState(ToolId, ServerVersion, ServerSHA1))
		{
		case EWorldBLDToolUpdateState::UpdateAvailable:
			if (!EdModePtr->IsWorldBLDPluginUpToDate())
			{
				return LOCTEXT(
					"UpdateBlockedByWorldBLDStatus",
					"A newer version is available, but WorldBLD must be updated first.");
			}
			return LOCTEXT("UpdateAvailableStatus", "A newer version is available.");
		case EWorldBLDToolUpdateState::InstalledUnknownSha1:
			return LOCTEXT("InstalledUnknownStatus", "Installed. The server could not confirm whether this version is current.");
		default:
			break;
		}
	}

	return LOCTEXT("UpToDateStatus", "Installed and up to date.");
}

FText SWorldBLDPluginManager::GetStatusDetailText() const
{
	if (bOperationFailed)
	{
		return LOCTEXT("OperationFailedDetail", "Review the message above, then try the action again.");
	}
	if (IsOperationInProgress())
	{
		return LOCTEXT(
			"OperationInProgressDetail",
			"You can close this window and track progress in the Plugins Browser.");
	}
	if (HasPendingRestart())
	{
		return LOCTEXT("RestartRequiredDetail", "Restart the editor to finish applying the plugin changes.");
	}
	if (!IsToolInstalled())
	{
		return bHasServerMetadata
			? LOCTEXT(
				"AvailableDetail",
				"Click Install to begin. You can close this window and track progress in the Plugins Browser.")
			: LOCTEXT("MetadataUnavailableDetail", "Refresh the WorldBLD tool list before trying again.");
	}

	const UWorldBLDEdMode* EdModePtr = EdMode.Get();
	const bool bUpdateAvailable = EdModePtr != nullptr
		&& EdModePtr->GetToolUpdateState(ToolId, ServerVersion, ServerSHA1)
			== EWorldBLDToolUpdateState::UpdateAvailable;
	if (bUpdateAvailable && EdModePtr != nullptr && !EdModePtr->IsWorldBLDPluginUpToDate())
	{
		return LOCTEXT(
			"UpdateBlockedByWorldBLDDetail",
			"Install the latest WorldBLD from worldbld.com or Fab, then return here to update this tool.");
	}
	return bUpdateAvailable
		? LOCTEXT("UpdateAvailableDetail", "Click Update to download and install the latest available version.")
		: LOCTEXT("InstalledDetail", "No action is required. You can uninstall the tool from this window.");
}

const FSlateBrush* SWorldBLDPluginManager::GetToolIconBrush() const
{
	return ToolIconBrush.Get();
}

float SWorldBLDPluginManager::GetLiveDownloadProgress() const
{
	if (const UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get())
	{
		const float LiveProgress = DownloaderPtr->GetDownloadProgress(ToolId);
		if (LiveProgress >= 0.0f)
		{
			return FMath::Clamp(LiveProgress, 0.0f, 1.0f);
		}
	}
	return FMath::Clamp(DownloadProgress, 0.0f, 1.0f);
}

TOptional<float> SWorldBLDPluginManager::GetDownloadProgress() const
{
	return TOptional<float>(GetLiveDownloadProgress());
}

EVisibility SWorldBLDPluginManager::GetProgressVisibility() const
{
	return IsOperationInProgress() ? EVisibility::Visible : EVisibility::Collapsed;
}

EVisibility SWorldBLDPluginManager::GetInstallButtonVisibility() const
{
	return !IsToolInstalled() && bHasServerMetadata && !HasPendingRestart()
		? EVisibility::Visible
		: EVisibility::Collapsed;
}

EVisibility SWorldBLDPluginManager::GetUpdateButtonVisibility() const
{
	const UWorldBLDEdMode* EdModePtr = EdMode.Get();
	const bool bUpdateAvailable = IsToolInstalled() && EdModePtr != nullptr
		&& EdModePtr->GetToolUpdateState(ToolId, ServerVersion, ServerSHA1) == EWorldBLDToolUpdateState::UpdateAvailable;
	return bUpdateAvailable && !HasPendingRestart() ? EVisibility::Visible : EVisibility::Collapsed;
}

EVisibility SWorldBLDPluginManager::GetUninstallButtonVisibility() const
{
	return IsToolInstalled() ? EVisibility::Visible : EVisibility::Collapsed;
}

EVisibility SWorldBLDPluginManager::GetRestartButtonVisibility() const
{
	return HasPendingRestart() ? EVisibility::Visible : EVisibility::Collapsed;
}

bool SWorldBLDPluginManager::CanRunLifecycleAction() const
{
	return Downloader.IsValid() && !IsOperationInProgress() && !HasPendingRestart();
}

FReply SWorldBLDPluginManager::HandleInstallClicked()
{
	StartInstallOrUpdate(false);
	return FReply::Handled();
}

FReply SWorldBLDPluginManager::HandleUpdateClicked()
{
	StartInstallOrUpdate(true);
	return FReply::Handled();
}

FReply SWorldBLDPluginManager::HandleUninstallClicked()
{
	UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
	if (!IsValid(DownloaderPtr) || !IsToolInstalled() || IsOperationInProgress())
	{
		return FReply::Handled();
	}

	const FText Prompt = FText::Format(
		LOCTEXT(
			"ConfirmUninstall",
			"Uninstall {0} from this project?\n\n"
			"The plugin will be disabled and its files will be removed from the project Plugins directory."),
		GetDisplayNameText());
	if (FMessageDialog::Open(EAppMsgType::YesNo, Prompt) != EAppReturnType::Yes)
	{
		return FReply::Handled();
	}

	const FWorldBLDPluginUninstallResult Result = DownloaderPtr->UninstallPlugin(ToolId, true);
	bOperationFailed = !Result.bSuccess;
	OperationStatus = FText::FromString(Result.Message);
	if (Result.bSuccess)
	{
		bUninstallRequested = true;
		bRestartRequired = Result.bRestartRequired;
	}
	return FReply::Handled();
}

FReply SWorldBLDPluginManager::HandleOpenPluginsFolderClicked() const
{
	FPlatformProcess::ExploreFolder(*ProjectPluginsPath);
	return FReply::Handled();
}

FReply SWorldBLDPluginManager::HandleLearnMoreClicked() const
{
	FString ToolSlug = WorldBLDPluginManagerInternal::NormalizeToolId(ToolId).ToLower();
	ToolSlug.ReplaceInline(TEXT(" "), TEXT(""));
	const FString ToolUrl = FString::Printf(TEXT("https://worldbld.com/%s"), *ToolSlug);
	FPlatformProcess::LaunchURL(*ToolUrl, nullptr, nullptr);
	return FReply::Handled();
}

FReply SWorldBLDPluginManager::HandleRestartClicked()
{
	CloseDialog();
	FUnrealEdMisc::Get().RestartEditor(false);
	return FReply::Handled();
}

FReply SWorldBLDPluginManager::HandleCloseClicked()
{
	CloseDialog();
	return FReply::Handled();
}

void SWorldBLDPluginManager::StartInstallOrUpdate(bool bIsUpdate)
{
	UWorldBLDEdMode* EdModePtr = EdMode.Get();
	UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
	if (!IsValid(EdModePtr) || !IsValid(DownloaderPtr) || !bHasServerMetadata || IsOperationInProgress())
	{
		return;
	}

	TArray<FString> MissingDependencies;
	if (!AreDependenciesInstalled(MissingDependencies))
	{
		FMessageDialog::Open(
			EAppMsgType::Ok,
			FText::Format(
				LOCTEXT(
					"MissingDependencies",
					"{0} requires the following tools to be installed first:\n\n{1}"),
				GetDisplayNameText(),
				FText::FromString(FString::Join(MissingDependencies, TEXT(", ")))));
		return;
	}

	TArray<FString> OutdatedDependencies;
	if (!AreDependenciesUpToDate(OutdatedDependencies))
	{
		FMessageDialog::Open(
			EAppMsgType::Ok,
			FText::Format(
				LOCTEXT(
					"OutdatedDependencies",
					"{0} cannot be {1} until the latest versions of the following tools are installed:\n\n{2}"),
				GetDisplayNameText(),
				bIsUpdate
					? LOCTEXT("OutdatedDependenciesActionUpdate", "updated")
					: LOCTEXT("OutdatedDependenciesActionInstall", "installed"),
				FText::FromString(FString::Join(OutdatedDependencies, TEXT(", ")))));
		return;
	}

	if (bIsUpdate && !EdModePtr->IsWorldBLDPluginUpToDate())
	{
		FMessageDialog::Open(
			EAppMsgType::Ok,
			FText::Format(
				LOCTEXT(
					"WorldBLDUpdateRequired",
					"{0} cannot be updated until the latest version of WorldBLD is installed."),
				GetDisplayNameText()));
		return;
	}

	bOperationFailed = false;
	DownloadProgress = 0.0f;
	OperationStatus = bIsUpdate
		? LOCTEXT("StartingUpdateStatus", "Starting update...")
		: LOCTEXT("StartingInstallStatus", "Starting installation...");

	DownloaderPtr->RequestToolDownloadNative(
		ToolId,
		DownloadUrl,
		ServerSHA1,
		FOnDownloadProgress::FDelegate::CreateSP(this, &SWorldBLDPluginManager::HandleDownloadProgress),
		FOnComplete::FDelegate::CreateSP(this, &SWorldBLDPluginManager::HandleDownloadComplete));
}

void SWorldBLDPluginManager::HandleDownloadProgress(float InProgress)
{
	DownloadProgress = FMath::Clamp(InProgress, 0.0f, 1.0f);
	OperationStatus = FText::GetEmpty();
}

void SWorldBLDPluginManager::HandleDownloadComplete(bool bSuccess)
{
	DownloadProgress = 1.0f;
	bOperationFailed = !bSuccess;
	if (!bSuccess)
	{
		OperationStatus = LOCTEXT("InstallFailedStatus", "The download or installation failed. Check the Output Log for details and try again.");
		return;
	}

	UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
	const bool bWasStaged = UCurlDownloaderLibrary::HasPendingStagedUpdate(ToolId);
	if (!bWasStaged && IsValid(DownloaderPtr))
	{
		FString EnableError;
		if (!DownloaderPtr->SetPluginEnabledInProjectFileNative(ToolId, true, EnableError))
		{
			bOperationFailed = true;
			OperationStatus = FText::FromString(EnableError);
			return;
		}
		DownloaderPtr->MarkPendingInstallRestart(ToolId);
	}

	bUninstallRequested = false;
	bRestartRequired = true;
	RefreshToolMetadata();
	OperationStatus = bWasStaged
		? FText::Format(
			LOCTEXT("UpdateCompleteStatus", "{0} update downloaded successfully. Restart Unreal to complete installation."),
			GetDisplayNameText())
		: FText::Format(
			LOCTEXT("InstallCompleteStatus", "{0} installed successfully. Restart Unreal to complete installation."),
			GetDisplayNameText());
}

void SWorldBLDPluginManager::CloseDialog()
{
	if (const TSharedPtr<SWindow> Window = HostWindow.Pin())
	{
		Window->RequestDestroyWindow();
	}
}

#undef LOCTEXT_NAMESPACE
