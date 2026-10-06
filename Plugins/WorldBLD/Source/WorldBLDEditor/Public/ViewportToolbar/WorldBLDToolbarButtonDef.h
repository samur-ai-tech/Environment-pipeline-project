// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Framework/SlateDelegates.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateColor.h"

/** Returns whether a toolbar button (or overflow entry) should currently be shown. */
DECLARE_DELEGATE_RetVal(bool, FWorldBLDToolbarVisibility);
/** Returns whether a toolbar button (or overflow entry) should currently be enabled. */
DECLARE_DELEGATE_RetVal(bool, FWorldBLDToolbarEnabled);

/**
 * Describes a single button in a WorldBLD viewport toolbar.
 *
 * A button is either:
 *  - a simple "image" button (binds OnClicked), or
 *  - an "anchor" button that opens a popup (binds OnGetMenuContent).
 *
 * This mirrors the previous UMG split between ViewportImageButton and
 * WorldBLDMenuAnchorButton, but in a plain, reusable data struct so every
 * plugin toolbar can share the same layout/styling code.
 *
 * IMPORTANT: Do not add members to this struct without coordinating a full
 * rebuild of every dependent plugin (CityBLD, RoadBLD, TwinBLD, etc.). Packaged
 * plugins compile against this layout; a size/order change causes crashes when
 * WorldBLD copies their toolbar button arrays.
 */
struct FWorldBLDToolbarButtonDef
{
	/** Text shown beneath the icon. */
	FText Label;

	/** Hover tooltip. Falls back to Label when empty. */
	FText Tooltip;

	/** FAppStyle/FSlateStyle brush name used for the 40x40 icon (resolved lazily). */
	FName IconName = NAME_None;

	/**
	 * Optional custom brush for the 40x40 icon (e.g. loaded from a plugin resource file).
	 * When set, takes priority over IconName.
	 */
	TSharedPtr<const FSlateBrush> IconBrush;

	/** Optional icon tint/color. Defaults to white. */
	FSlateColor IconColorAndOpacity = FSlateColor(FLinearColor::White);

	/** When true the button stays interactive while logged out (e.g. Settings, Log In). */
	bool bEnabledWhenLoggedOut = false;

	/** When true the button is placed under the far-right three-dots overflow menu instead of the main row. */
	bool bIsOverflow = false;

	/** When true this entry renders as a non-interactive toolbar divider/spacer. */
	bool bIsSpacer = false;

	/** Optional visibility predicate. When unbound the button is always visible. */
	FWorldBLDToolbarVisibility IsVisible;

	/** Optional enabled predicate. When unbound the button is always enabled. */
	FWorldBLDToolbarEnabled IsEnabled;

	/** Action for a simple image button. */
	FSimpleDelegate OnClicked;

	/** Popup content factory for an anchor button. */
	FOnGetContent OnGetMenuContent;

	/** True when this button opens a popup rather than firing a direct action. */
	bool IsAnchor() const { return OnGetMenuContent.IsBound(); }

	/** True when this button should currently be shown. */
	bool IsVisibleNow() const { return !IsVisible.IsBound() || IsVisible.Execute(); }

	/** True when this button should currently be interactive. */
	bool IsEnabledNow() const { return !IsEnabled.IsBound() || IsEnabled.Execute(); }

	/** True when a meaningful action/content has been configured. */
	bool IsValidDef() const { return bIsSpacer || OnClicked.IsBound() || OnGetMenuContent.IsBound() || !Label.IsEmpty(); }
};
