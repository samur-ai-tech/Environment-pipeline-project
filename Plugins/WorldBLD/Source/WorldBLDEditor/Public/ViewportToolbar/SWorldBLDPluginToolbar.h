// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "ViewportToolbar/WorldBLDToolbarButtonDef.h"

class SBox;
struct FSlateBrush;
class SMenuAnchor;
class SWidget;
class SWorldBLDToolSwitchMenu;
class SWrapBox;
class UCurlDownloaderLibrary;
class UWorldBLDEdMode;

/**
 * Reusable body shared by every plugin's viewport toolbar.
 *
 * This widget renders only the main toolbar panel. It owns, but does not parent,
 * the persistent tool-tab widget exposed through GetToolSwitchWidget(); the
 * viewport host places both widgets in independent canvas slots.
 *
 * Buttons (except those flagged bEnabledWhenLoggedOut) are grayed out while the
 * user is logged out. Login state is polled cheaply and the toolbar rebuilds when
 * it changes.
 */
class WORLDBLDEDITOR_API SWorldBLDPluginToolbar : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDPluginToolbar) {}
		/** Plugin-specific buttons laid out in the wrap box. */
		SLATE_ARGUMENT(TArray<FWorldBLDToolbarButtonDef>, MainButtons)

		/** Editor mode that owns the discovered tools and active toolbar state. */
		SLATE_ARGUMENT(TWeakObjectPtr<UWorldBLDEdMode>, EdMode)

		/** Downloader used by inline install/update actions on tool tabs. */
		SLATE_ARGUMENT(TWeakObjectPtr<UCurlDownloaderLibrary>, Downloader)

		/** Login action surfaced by the tool strip while logged out. */
		SLATE_ARGUMENT(FWorldBLDToolbarButtonDef, LoginButton)

		/** Entries shown under the persistent far-right three-dots overflow menu. */
		SLATE_ARGUMENT(TArray<FWorldBLDToolbarButtonDef>, OverflowButtons)

		/**
		 * When set (non-WorldBLD tool toolbars), shows a far-right Manage button
		 * that opens the plugin manager for this tool id.
		 */
		SLATE_ARGUMENT(FName, ManageToolId)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	TSharedRef<SWidget> GetToolSwitchWidget() const;
	EOrientation GetOrientation() const { return Orientation; }

	//~ Begin SWidget interface
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;
	//~ End SWidget interface

private:
	/** Rebuilds the entire toolbar layout (used on construct and whenever orientation / collapse / login state changes). */
	void RebuildLayout();

	/** Builds the popup content for the three-dots overflow menu. */
	TSharedRef<SWidget> BuildOverflowMenuContent();

	/** Creates a configured button widget whose enabled state tracks login status. */
	TSharedRef<SWidget> MakeButtonWidget(const FWorldBLDToolbarButtonDef& InDef);

	/** Creates the far-right Manage / Update Available trailing button. */
	TSharedRef<SWidget> MakeManageToolButtonWidget();

	/** Creates a dark divider/spacer widget for grouping toolbar buttons. */
	TSharedRef<SWidget> MakeSpacerWidget() const;

	bool IsManageToolUpdateAvailable() const;
	FText GetManageToolLabel() const;
	FSlateColor GetManageToolIconColor() const;
	void HandleManageToolClicked();

	void LoadPersistedOrientation();
	void SavePersistedOrientation() const;

	FReply HandleToggleOrientation();

	bool HasAnyVisibleOverflow() const;

	TArray<FWorldBLDToolbarButtonDef> MainButtons;
	TWeakObjectPtr<UWorldBLDEdMode> EdMode;
	TWeakObjectPtr<UCurlDownloaderLibrary> Downloader;
	FWorldBLDToolbarButtonDef LoginButton;
	TArray<FWorldBLDToolbarButtonDef> OverflowButtons;
	FName ManageToolId = NAME_None;
	FText ManageToolDisplayName;
	TSharedPtr<FSlateBrush> ManageToolIconBrush;

	/** Optional custom brush for the persistent More button icon. */
	TSharedPtr<FSlateBrush> OverflowIconBrush;

	TSharedPtr<SMenuAnchor> OverflowAnchor;
	TSharedPtr<SWorldBLDToolSwitchMenu> ToolSwitchMenu;

	EOrientation Orientation = Orient_Horizontal;
	bool bCachedLoggedIn = false;

	/** Throttle accumulator for the cheap login-state poll. */
	float AuthPollAccumulator = 0.0f;
};
