// Copyright WorldBLD LLC. All rights reserved.

#include "ViewportToolbar/SWorldBLDViewportToolbarHost.h"

#include "Misc/ConfigCacheIni.h"
#include "Styling/AppStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SConstraintCanvas.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WorldBLDViewportToolbarHost"

namespace WorldBLDToolbarHost
{
	DECLARE_DELEGATE_OneParam(FOnToolbarDragDelta, const FVector2D& /*LocalDelta*/);
	DECLARE_DELEGATE(FOnToolbarDragFinished);

	static const TCHAR* ToolbarLayoutConfigSection = TEXT("WorldBLD.ViewportToolbar");
	static const TCHAR* ToolbarPositionXConfigKey = TEXT("PositionX");
	static const TCHAR* ToolbarPositionYConfigKey = TEXT("PositionY");

	/**
	 * Small grip widget that captures the mouse and reports drag deltas in local
	 * (DPI-adjusted) space so the host can reposition the toolbar.
	 */
	class SToolbarDragHandle : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SToolbarDragHandle) {}
			SLATE_EVENT(FOnToolbarDragDelta, OnDragDelta)
			SLATE_EVENT(FOnToolbarDragFinished, OnDragFinished)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			OnDragDelta = InArgs._OnDragDelta;
			OnDragFinished = InArgs._OnDragFinished;

			SetCursor(EMouseCursor::CardinalCross);

			ChildSlot
			[
				SNew(SBorder)
				.BorderImage(FAppStyle::Get().GetBrush("Brushes.Recessed"))
				.Padding(FMargin(3.0f, 0.0f))
				.VAlign(VAlign_Center)
				.ToolTipText(LOCTEXT("DragTooltip", "Drag to move the toolbar"))
				[
					SNew(STextBlock)
					.Text(LOCTEXT("DragGlyph", "::"))
				]
			];
		}

		virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
		{
			if (MouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
			{
				bDragging = true;
				LastScreenPos = MouseEvent.GetScreenSpacePosition();
				return FReply::Handled().CaptureMouse(SharedThis(this));
			}
			return FReply::Unhandled();
		}

		virtual FReply OnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
		{
			if (bDragging && HasMouseCapture())
			{
				const FVector2D CurrentScreenPos = MouseEvent.GetScreenSpacePosition();
				const float Scale = (MyGeometry.Scale > 0.0f) ? MyGeometry.Scale : 1.0f;
				const FVector2D LocalDelta = (CurrentScreenPos - LastScreenPos) / Scale;
				LastScreenPos = CurrentScreenPos;
				OnDragDelta.ExecuteIfBound(LocalDelta);
				return FReply::Handled();
			}
			return FReply::Unhandled();
		}

		virtual FReply OnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
		{
			if (bDragging && MouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
			{
				bDragging = false;
				OnDragFinished.ExecuteIfBound();
				return FReply::Handled().ReleaseMouseCapture();
			}
			return FReply::Unhandled();
		}

	private:
		FOnToolbarDragDelta OnDragDelta;
		FOnToolbarDragFinished OnDragFinished;
		bool bDragging = false;
		FVector2D LastScreenPos = FVector2D::ZeroVector;
	};
}

void SWorldBLDViewportToolbarHost::Construct(const FArguments& InArgs)
{
	Position = InArgs._InitialPosition;
	ToolbarOrientation = InArgs._ToolbarOrientation;
	LoadPersistedPosition();

	TSharedRef<SWidget> ToolbarContent = InArgs._ToolbarContent.IsValid()
		? InArgs._ToolbarContent.ToSharedRef()
		: SNullWidget::NullWidget;
	ToolSwitchWidget = InArgs._ToolSwitchContent;
	if (!ToolSwitchWidget.IsValid())
	{
		ToolSwitchWidget = SNullWidget::NullWidget;
	}

	// Host ignores hit-testing itself so the rest of the viewport stays interactive;
	// only the toolbar panel and its drag grip consume input.
	SetVisibility(EVisibility::SelfHitTestInvisible);

	ChildSlot
	[
		SAssignNew(Canvas, SConstraintCanvas)

		+ SConstraintCanvas::Slot()
		.Anchors(FAnchors(0.0f, 0.0f, 0.0f, 0.0f))
		.AutoSize(true)
		.Alignment(FVector2D(0.0f, 0.0f))
		.Offset(TAttribute<FMargin>::Create(TAttribute<FMargin>::FGetter::CreateSP(this, &SWorldBLDViewportToolbarHost::GetToolSwitchOffset)))
		[
			ToolSwitchWidget.ToSharedRef()
		]

		+ SConstraintCanvas::Slot()
		.Anchors(FAnchors(0.0f, 0.0f, 0.0f, 0.0f))
		.AutoSize(true)
		.Alignment(FVector2D(0.0f, 0.0f))
		.Offset(TAttribute<FMargin>::Create(TAttribute<FMargin>::FGetter::CreateSP(this, &SWorldBLDViewportToolbarHost::GetPanelOffset)))
		[
			SAssignNew(PanelWidget, SBorder)
			.BorderImage(FAppStyle::Get().GetBrush(TEXT("Brushes.Panel")))
			.Padding(FMargin(2.0f))
			[
				SNew(SHorizontalBox)

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Fill)
				[
					SNew(WorldBLDToolbarHost::SToolbarDragHandle)
					.OnDragDelta(WorldBLDToolbarHost::FOnToolbarDragDelta::CreateSP(this, &SWorldBLDViewportToolbarHost::HandleDragDelta))
					.OnDragFinished(WorldBLDToolbarHost::FOnToolbarDragFinished::CreateSP(this, &SWorldBLDViewportToolbarHost::HandleDragFinished))
				]

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Center)
				.Padding(2.0f, 0.0f)
				[
					ToolbarContent
				]
			]
		]
	];
}

void SWorldBLDViewportToolbarHost::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

	LastAllottedSize = AllottedGeometry.GetLocalSize();
	ApplyDefaultPositionIfNeeded();
	ClampPositionToBounds();
}

FMargin SWorldBLDViewportToolbarHost::GetPanelOffset() const
{
	return FMargin(Position.X, Position.Y, 0.0f, 0.0f);
}

FMargin SWorldBLDViewportToolbarHost::GetToolSwitchOffset() const
{
	if (!ToolSwitchWidget.IsValid())
	{
		return GetPanelOffset();
	}

	static constexpr float PanelGap = 5.0f;

	const FVector2D ToolSwitchSize = ToolSwitchWidget->GetDesiredSize();
	const FVector2D MainPanelSize = PanelWidget.IsValid() ? PanelWidget->GetDesiredSize() : FVector2D::ZeroVector;
	const EOrientation Orientation = ToolbarOrientation.IsSet()
		? ToolbarOrientation.Get()
		: Orient_Horizontal;

	FVector2D ToolSwitchPosition = Position;
	if (Orientation == Orient_Vertical)
	{
		ToolSwitchPosition.X = Position.X >= ToolSwitchSize.X + PanelGap
			? Position.X - ToolSwitchSize.X - PanelGap
			: Position.X + MainPanelSize.X + PanelGap;
	}
	else
	{
		// Keep X at Position.X so the tab strip left edge aligns with the drag handle.
		ToolSwitchPosition.Y = Position.Y >= ToolSwitchSize.Y + PanelGap
			? Position.Y - ToolSwitchSize.Y - PanelGap
			: Position.Y + MainPanelSize.Y + PanelGap;
	}

	if (!LastAllottedSize.IsNearlyZero())
	{
		const FVector2D MaxToolSwitchPosition(
			FMath::Max(0.0f, LastAllottedSize.X - ToolSwitchSize.X),
			FMath::Max(0.0f, LastAllottedSize.Y - ToolSwitchSize.Y));
		ToolSwitchPosition.X = FMath::Clamp(ToolSwitchPosition.X, 0.0f, MaxToolSwitchPosition.X);
		ToolSwitchPosition.Y = FMath::Clamp(ToolSwitchPosition.Y, 0.0f, MaxToolSwitchPosition.Y);
	}

	return FMargin(ToolSwitchPosition.X, ToolSwitchPosition.Y, 0.0f, 0.0f);
}

void SWorldBLDViewportToolbarHost::HandleDragDelta(const FVector2D& LocalDelta)
{
	// First drag commits away from the auto bottom-center default.
	bHasPersistedPosition = true;

	Position += LocalDelta;

	// Keep the toolbar from being dragged fully off the top-left edge.
	Position.X = FMath::Max(Position.X, 0.0f);
	Position.Y = FMath::Max(Position.Y, 0.0f);

	ClampPositionToBounds();
}

void SWorldBLDViewportToolbarHost::HandleDragFinished()
{
	bHasPersistedPosition = true;
	SavePersistedPosition();
}

void SWorldBLDViewportToolbarHost::ApplyDefaultPositionIfNeeded()
{
	if (bHasPersistedPosition || !PanelWidget.IsValid() || LastAllottedSize.IsNearlyZero())
	{
		return;
	}

	const FVector2D PanelSize = PanelWidget->GetDesiredSize();
	if (PanelSize.IsNearlyZero())
	{
		return;
	}

	// Bottom-centered: horizontally centered, ~100px above the viewport bottom.
	Position.X = FMath::Max(0.0f, (LastAllottedSize.X - PanelSize.X) * 0.5f);
	Position.Y = FMath::Max(0.0f, LastAllottedSize.Y - PanelSize.Y - DefaultBottomGap);
}

void SWorldBLDViewportToolbarHost::ClampPositionToBounds()
{
	if (!PanelWidget.IsValid() || LastAllottedSize.IsNearlyZero())
	{
		return;
	}

	const FVector2D PanelSize = PanelWidget->GetDesiredSize();
	const FVector2D MaxPosition(
		FMath::Max(0.0f, LastAllottedSize.X - PanelSize.X),
		FMath::Max(0.0f, LastAllottedSize.Y - PanelSize.Y));

	Position.X = FMath::Clamp(Position.X, 0.0f, MaxPosition.X);
	Position.Y = FMath::Clamp(Position.Y, 0.0f, MaxPosition.Y);
}

void SWorldBLDViewportToolbarHost::LoadPersistedPosition()
{
	if (GConfig == nullptr)
	{
		return;
	}

	float PersistedX = Position.X;
	float PersistedY = Position.Y;
	if (GConfig->GetFloat(
			WorldBLDToolbarHost::ToolbarLayoutConfigSection,
			WorldBLDToolbarHost::ToolbarPositionXConfigKey,
			PersistedX,
			GEditorPerProjectIni)
		&& GConfig->GetFloat(
			WorldBLDToolbarHost::ToolbarLayoutConfigSection,
			WorldBLDToolbarHost::ToolbarPositionYConfigKey,
			PersistedY,
			GEditorPerProjectIni))
	{
		Position.X = FMath::Max(PersistedX, 0.0f);
		Position.Y = FMath::Max(PersistedY, 0.0f);
		bHasPersistedPosition = true;
	}
}

void SWorldBLDViewportToolbarHost::SavePersistedPosition() const
{
	if (GConfig == nullptr)
	{
		return;
	}

	GConfig->SetFloat(
		WorldBLDToolbarHost::ToolbarLayoutConfigSection,
		WorldBLDToolbarHost::ToolbarPositionXConfigKey,
		Position.X,
		GEditorPerProjectIni);
	GConfig->SetFloat(
		WorldBLDToolbarHost::ToolbarLayoutConfigSection,
		WorldBLDToolbarHost::ToolbarPositionYConfigKey,
		Position.Y,
		GEditorPerProjectIni);
	GConfig->Flush(false, GEditorPerProjectIni);
}

#undef LOCTEXT_NAMESPACE
