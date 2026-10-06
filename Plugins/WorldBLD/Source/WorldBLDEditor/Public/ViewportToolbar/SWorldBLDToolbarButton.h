// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Styling/SlateColor.h"
#include "ViewportToolbar/WorldBLDToolbarButtonDef.h"

class SMenuAnchor;

/**
 * A single viewport toolbar button matching Unreal's editor-mode tool palette
 * convention: a 40x40 icon stacked above a small centered text label.
 *
 * Styling is pulled from the engine "PaletteToolBar" style so the button reads
 * as native. When the supplied definition is an anchor it wraps the button in an
 * SMenuAnchor and toggles the popup on click; otherwise it fires OnClicked.
 */
class WORLDBLDEDITOR_API SWorldBLDToolbarButton : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDToolbarButton) {}
		/** The button this widget represents. */
		SLATE_ARGUMENT(FWorldBLDToolbarButtonDef, ButtonDef)

		/** Whether the button is interactive. Bound so the gray-out state updates live. */
		SLATE_ATTRIBUTE(bool, ButtonEnabled)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	FReply HandleClicked();
	FText GetTooltipText() const;
	FSlateColor GetIconColorAndOpacity() const;
	bool IsButtonEnabled() const;

	FWorldBLDToolbarButtonDef Def;
	TAttribute<bool> EnabledAttr;
	TSharedPtr<SMenuAnchor> MenuAnchor;
};
