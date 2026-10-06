// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

class SConstraintCanvas;
class SBorder;
class SWidget;

/**
 * Full-viewport, click-through host that positions the grouped toolbar widgets
 * at a draggable offset. Visual panel backgrounds belong to the hosted widgets,
 * allowing the tool-tab strip and main toolbar to size independently.
 *
 * The host itself is SelfHitTestInvisible (mirrors SWorldBLDContextMenuViewportOverlay)
 * so only the toolbar panel consumes input; the rest of the viewport stays interactive.
 * Because it lives in the level viewport overlay it is always rendered on top, and it
 * provides only a drag grip (no close affordance) so the user can move/collapse it but
 * never dismiss it.
 */
class WORLDBLDEDITOR_API SWorldBLDViewportToolbarHost : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDViewportToolbarHost)
		: _InitialPosition(FVector2D::ZeroVector)
	{}
		/** The plugin toolbar body to host. */
		SLATE_ARGUMENT(TSharedPtr<SWidget>, ToolbarContent)

		/** Independently positioned persistent tool-tab strip/rail. */
		SLATE_ARGUMENT(TSharedPtr<SWidget>, ToolSwitchContent)

		/** Current toolbar orientation, used to place the tabs above or to the left. */
		SLATE_ATTRIBUTE(EOrientation, ToolbarOrientation)

		/**
		 * Fallback top-left offset used only until the first layout pass can apply the
		 * bottom-centered default (or a persisted position is loaded). Prefer leaving
		 * this at zero; new users get a bottom-centered placement automatically.
		 */
		SLATE_ARGUMENT(FVector2D, InitialPosition)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	//~ Begin SWidget interface
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;
	//~ End SWidget interface

private:
	void HandleDragDelta(const FVector2D& LocalDelta);
	void HandleDragFinished();
	FMargin GetPanelOffset() const;
	FMargin GetToolSwitchOffset() const;
	void ApplyDefaultPositionIfNeeded();
	void ClampPositionToBounds();
	void LoadPersistedPosition();
	void SavePersistedPosition() const;

	/** Gap between the toolbar bottom edge and the viewport bottom for the default layout. */
	static constexpr float DefaultBottomGap = 100.0f;

	FVector2D Position = FVector2D::ZeroVector;
	FVector2D LastAllottedSize = FVector2D::ZeroVector;
	/** True once a user-dragged or previously saved position is in effect. */
	bool bHasPersistedPosition = false;
	TSharedPtr<SConstraintCanvas> Canvas;
	TSharedPtr<SBorder> PanelWidget;
	TSharedPtr<SWidget> ToolSwitchWidget;
	TAttribute<EOrientation> ToolbarOrientation;
};
