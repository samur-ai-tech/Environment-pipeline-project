// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

class UCurlDownloaderLibrary;
class UWorldBLDEdMode;
struct FSlateBrush;

/**
 * Persistent in-viewport tool switcher.
 * Displays discovered tools as compact icon tabs with anchored hover labels,
 * and adapts between a horizontal strip and vertical rail.
 */
class SWorldBLDToolSwitchMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDToolSwitchMenu)
		: _EdMode(nullptr)
		, _Downloader(nullptr)
		, _Orientation(Orient_Horizontal)
		, _bIsLoggedIn(false)
	{}
		SLATE_ARGUMENT(TWeakObjectPtr<UWorldBLDEdMode>, EdMode)
		SLATE_ARGUMENT(TWeakObjectPtr<UCurlDownloaderLibrary>, Downloader)
		SLATE_ARGUMENT(EOrientation, Orientation)
		SLATE_ARGUMENT(bool, bIsLoggedIn)
		SLATE_EVENT(FSimpleDelegate, OnLoginClicked)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	void SetOrientation(EOrientation InOrientation);

private:
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;

	TWeakObjectPtr<UWorldBLDEdMode> EdMode;
	TWeakObjectPtr<UCurlDownloaderLibrary> Downloader;
	EOrientation Orientation = Orient_Horizontal;
	bool bIsLoggedIn = false;
	FSimpleDelegate OnLoginClicked;

	TSharedRef<SWidget> BuildMenuContent();
	TSharedRef<SWidget> BuildToolTab(
		const FString& ToolId,
		const FText& DisplayName,
		const FString& ServerVersion,
		const FString& ServerSHA1,
		bool bIsWorldBLD);
	TSharedRef<SWidget> BuildMoreToolsTab();
	TSharedRef<SWidget> BuildCustomToolsTab();
	TSharedRef<SWidget> BuildMiniToolsTab();
	TSharedRef<SWidget> BuildLoginTab();
	TSharedRef<SWidget> CreateMiniToolsMenuContent();
	TSharedRef<SWidget> WrapTabStripInPanel(const TSharedRef<SWidget>& TabStrip) const;
	TSharedRef<SWidget> BuildTabStripWidget(const TArray<TSharedRef<SWidget>>& Tabs) const;
	void RebuildMenuEntries();
	uint32 ComputeAvailableToolsHash() const;
	const FSlateBrush* GetToolIcon(const FString& ToolId);

	TSharedPtr<class SBox> MenuContainer;
	TSharedPtr<class SMenuAnchor> CustomToolsMenuAnchor;
	TSharedPtr<class SMenuAnchor> MiniToolsMenuAnchor;
	TMap<FString, TSharedPtr<FSlateBrush>> ToolIconBrushes;
	uint32 CachedAvailableToolsHash = 0;
	bool bShowMoreToolsPanel = false;

	// Tool helpers
	static FString NormalizeToolId(const FString& ToolName);
	bool IsToolInstalled(const FString& ToolId) const;
	bool IsToolInstalling(const FString& ToolId) const;

	// UI actions
	FReply HandleToolClicked(FString ToolId) const;
	FReply HandleSwitchToWorldBLDClicked() const;
	FReply HandleLoginClicked() const;
	FReply HandleMoreToolsClicked();
};

