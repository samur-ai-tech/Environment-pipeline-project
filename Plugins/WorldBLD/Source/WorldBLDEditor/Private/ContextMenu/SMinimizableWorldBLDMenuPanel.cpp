// Copyright WorldBLD LLC. All rights reserved.

#include "ContextMenu/SMinimizableWorldBLDMenuPanel.h"

#include "ContextMenu/WorldBLDContextMenuFont.h"
#include "ContextMenu/WorldBLDContextMenuIcons.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"

#include "Brushes/SlateRoundedBoxBrush.h"
#include "Styling/AppStyle.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateTypes.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SNullWidget.h"

namespace
{
	const FButtonStyle& GetMinimizeButtonStyle()
	{
		static const FVector4 CornerRadii(4.0f, 4.0f, 4.0f, 4.0f);
		static const FSlateBrushOutlineSettings OutlineSettings = []()
		{
			FSlateBrushOutlineSettings Settings;
			Settings.CornerRadii = CornerRadii;
			Settings.Color = FSlateColor(FLinearColor::Transparent);
			Settings.Width = 0.0f;
			Settings.RoundingType = ESlateBrushRoundingType::FixedRadius;
			Settings.bUseBrushTransparency = true;
			return Settings;
		}();

		static const FLinearColor HoveredColor = WorldBLDContextMenuStyle::GetHighlightRedColor();
		static const FLinearColor PressedColor(0.833726f, 0.000000f, 0.040000f, 1.0f);

		static const FSlateRoundedBoxBrush NormalBrush = []()
		{
			FSlateRoundedBoxBrush Brush(FLinearColor::Transparent, CornerRadii);
			Brush.OutlineSettings = OutlineSettings;
			return Brush;
		}();

		static const FSlateRoundedBoxBrush HoveredBrush = []()
		{
			FSlateRoundedBoxBrush Brush(HoveredColor, CornerRadii);
			Brush.OutlineSettings = OutlineSettings;
			return Brush;
		}();

		static const FSlateRoundedBoxBrush PressedBrush = []()
		{
			FSlateRoundedBoxBrush Brush(PressedColor, CornerRadii);
			Brush.OutlineSettings = OutlineSettings;
			return Brush;
		}();

		static const FButtonStyle Style = FButtonStyle()
			.SetNormal(NormalBrush)
			.SetHovered(HoveredBrush)
			.SetPressed(PressedBrush)
			.SetDisabled(NormalBrush)
			.SetNormalForeground(FSlateColor(FLinearColor::White))
			.SetHoveredForeground(FSlateColor(FLinearColor::White))
			.SetPressedForeground(FSlateColor(FLinearColor::White))
			.SetDisabledForeground(FSlateColor(FLinearColor(1.0f, 1.0f, 1.0f, 0.40f)))
			.SetNormalPadding(FMargin(0.0f))
			.SetPressedPadding(FMargin(0.0f));
		return Style;
	}
}

void SMinimizableWorldBLDMenuPanel::Construct(const FArguments& InArgs)
{
	TitleText = InArgs._Title;
	ContentWidget = InArgs._Content;
	bMinimized = InArgs._bInitiallyMinimized;
	OnMinimizedChanged = InArgs._OnMinimizedChanged;

	if (!ContentWidget.IsValid())
	{
		ContentWidget = SNullWidget::NullWidget;
	}

	ChildSlot
	[
		SNew(SBox)
		.MinDesiredWidth(250.0f)
		.MaxDesiredWidth(500.0f)
		[
			// Rounded menu background to match WorldBLD context menu silhouette.
			SNew(SBorder)
			.BorderImage([]() -> const FSlateBrush*
			{
				static const FVector4 CornerRadii(4.0f, 4.0f, 4.0f, 4.0f);
				static const FSlateRoundedBoxBrush Brush(FLinearColor(0.011f, 0.011f, 0.011f, 0.95f), CornerRadii);
				return &Brush;
			}())
			.Padding(FMargin(1.0f))
			[
				// Outline border (visual framing only; background comes from the fill border above).
				SNew(SBorder)
				.BorderImage(FAppStyle::Get().GetBrush("ToolPanel.GroupBorder"))
				.BorderBackgroundColor(FLinearColor::Transparent)
				.Padding(FMargin(0.0f))
				[
					SNew(SVerticalBox)

					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(SBorder)
						.BorderImage(WorldBLDContextMenuStyle::GetTitleBarBackgroundBrush())
						.BorderBackgroundColor(FLinearColor::White)
						.Padding(FMargin(8.0f, 8.0f, 8.0f, 6.0f))
						[
							SNew(SHorizontalBox)

							+ SHorizontalBox::Slot()
							.FillWidth(1.0f)
							.VAlign(VAlign_Center)
							[
								SNew(STextBlock)
								.Text(TitleText)
								.Font(WorldBLDContextMenuFont::GetTitleBar())
								.ColorAndOpacity(FLinearColor::White)
								.AutoWrapText(true)
							]

							+ SHorizontalBox::Slot()
							.AutoWidth()
							.VAlign(VAlign_Center)
							.Padding(FMargin(8.0f, 0.0f, 0.0f, 0.0f))
							[
								SNew(SButton)
								.ButtonStyle(&GetMinimizeButtonStyle())
								.ContentPadding(FMargin(6.0f, 2.0f))
								.OnClicked(this, &SMinimizableWorldBLDMenuPanel::OnMinimizeClicked)
								[
									SNew(SImage)
									.Image(this, &SMinimizableWorldBLDMenuPanel::GetMinimizeIcon)
									.ColorAndOpacity(FLinearColor::White)
								]
							]
						]
					]

					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(8.0f, 8.0f))
					[
						SNew(SBorder)
						.BorderImage(FAppStyle::Get().GetBrush("NoBorder"))
						.Visibility(this, &SMinimizableWorldBLDMenuPanel::GetContentVisibility)
						[
							// Keep parity with WorldBLD menus: allow content to scroll if it grows.
							SNew(SScrollBox)
							+ SScrollBox::Slot()
							[
								ContentWidget.ToSharedRef()
							]
						]
					]
				]
			]
		]
	];
}

FReply SMinimizableWorldBLDMenuPanel::OnMinimizeClicked()
{
	bMinimized = !bMinimized;
	OnMinimizedChanged.ExecuteIfBound(bMinimized);
	Invalidate(EInvalidateWidgetReason::LayoutAndVolatility);
	return FReply::Handled();
}

const FSlateBrush* SMinimizableWorldBLDMenuPanel::GetMinimizeIcon() const
{
	return WorldBLDContextMenuIcons::GetActionIconBrush(
		bMinimized ? WorldBLDContextMenuIcons::EActionIcon::ArrowRight : WorldBLDContextMenuIcons::EActionIcon::ArrowDown);
}

EVisibility SMinimizableWorldBLDMenuPanel::GetContentVisibility() const
{
	return bMinimized ? EVisibility::Collapsed : EVisibility::Visible;
}

FReply SMinimizableWorldBLDMenuPanel::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	// Consume background clicks so they don't fall through to the viewport and change selection.
	return FReply::Handled();
}

FReply SMinimizableWorldBLDMenuPanel::OnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	return FReply::Handled();
}

FReply SMinimizableWorldBLDMenuPanel::OnMouseButtonDoubleClick(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	return FReply::Handled();
}

