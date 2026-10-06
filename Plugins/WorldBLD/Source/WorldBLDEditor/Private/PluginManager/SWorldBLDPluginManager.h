// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Brushes/SlateDynamicImageBrush.h"
#include "Widgets/SCompoundWidget.h"

class UCurlDownloaderLibrary;
class UWorldBLDEdMode;
class SWindow;
struct FProgressBarStyle;
struct FSlateBrush;
struct FPluginToolData;

/** Modal management surface for one companion WorldBLD tool plugin. */
class SWorldBLDPluginManager final : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDPluginManager)
		: _ToolId(NAME_None)
	{}
		SLATE_ARGUMENT(FName, ToolId)
		SLATE_ARGUMENT(TWeakObjectPtr<UWorldBLDEdMode>, EdMode)
		SLATE_ARGUMENT(TWeakObjectPtr<UCurlDownloaderLibrary>, Downloader)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	void SetHostWindow(const TSharedRef<SWindow>& InWindow);

	/** Opens the manager as an editor modal. WorldBLD core is intentionally excluded. */
	static void ShowModalForTool(
		FName ToolId,
		TWeakObjectPtr<UWorldBLDEdMode> EdMode,
		TWeakObjectPtr<UCurlDownloaderLibrary> Downloader);

private:
	void RefreshToolMetadata();
	bool IsToolInstalled() const;
	bool IsOperationInProgress() const;
	bool HasPendingRestart() const;
	bool AreDependenciesInstalled(TArray<FString>& OutMissingDependencies) const;
	bool AreDependenciesUpToDate(TArray<FString>& OutOutdatedDependencies) const;

	FText GetDisplayNameText() const;
	FText GetManagerDescriptionText() const;
	FText GetLatestVersionText() const;
	FText GetInstalledVersionText() const;
	FText GetStatusText() const;
	FText GetStatusDetailText() const;
	const FSlateBrush* GetToolIconBrush() const;
	float GetLiveDownloadProgress() const;
	TOptional<float> GetDownloadProgress() const;
	EVisibility GetProgressVisibility() const;
	EVisibility GetInstallButtonVisibility() const;
	EVisibility GetUpdateButtonVisibility() const;
	EVisibility GetUninstallButtonVisibility() const;
	EVisibility GetRestartButtonVisibility() const;
	bool CanRunLifecycleAction() const;

	FReply HandleInstallClicked();
	FReply HandleUpdateClicked();
	FReply HandleUninstallClicked();
	FReply HandleOpenPluginsFolderClicked() const;
	FReply HandleLearnMoreClicked() const;
	FReply HandleRestartClicked();
	FReply HandleCloseClicked();
	void StartInstallOrUpdate(bool bIsUpdate);
	void HandleDownloadProgress(float InProgress);
	void HandleDownloadComplete(bool bSuccess);
	void CloseDialog();

	FString ToolId;
	FString DisplayName;
	FString ToolDescription;
	FString ServerVersion;
	FString DownloadUrl;
	FString ServerSHA1;
	TArray<FString> RequiredToolIds;
	FString ProjectPluginsPath;
	FText OperationStatus;
	TWeakObjectPtr<UWorldBLDEdMode> EdMode;
	TWeakObjectPtr<UCurlDownloaderLibrary> Downloader;
	TWeakPtr<SWindow> HostWindow;
	TSharedPtr<FSlateDynamicImageBrush> ToolIconBrush;
	TSharedPtr<FSlateBrush> PanelBrush;
	TSharedPtr<FSlateBrush> SidebarBrush;
	TSharedPtr<FSlateBrush> FooterBrush;
	TSharedPtr<FSlateBrush> CardBrush;
	TSharedPtr<FSlateBrush> IconWellBrush;
	TSharedPtr<FSlateBrush> AccentBrush;
	TSharedPtr<FProgressBarStyle> ProgressBarStyle;
	float DownloadProgress = 0.0f;
	bool bHasServerMetadata = false;
	bool bOperationFailed = false;
	bool bUninstallRequested = false;
	bool bRestartRequired = false;
};
