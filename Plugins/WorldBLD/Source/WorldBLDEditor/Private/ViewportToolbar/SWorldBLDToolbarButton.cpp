// Copyright WorldBLD LLC. All rights reserved.

#include "ViewportToolbar/SWorldBLDToolbarButton.h"

#include "Styling/AppStyle.h"
#include "Styling/SlateTypes.h"
#include "Styling/ToolBarStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SMenuAnchor.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace WorldBLDToolbarButtonConstants
{
	static const FName PaletteToolBarStyle(TEXT("PaletteToolBar"));
	static constexpr float IconExtent = 30.0f;
}

void SWorldBLDToolbarButton::Construct(const FArguments& InArgs)
{
	Def = InArgs._ButtonDef;
	EnabledAttr = InArgs._ButtonEnabled;

	const FToolBarStyle& ToolBarStyle = FAppStyle::Get().GetWidgetStyle<FToolBarStyle>(WorldBLDToolbarButtonConstants::PaletteToolBarStyle);
	const FSlateBrush* IconBrush = nullptr;
	if (Def.IconBrush.IsValid())
	{
		IconBrush = Def.IconBrush.Get();
	}
	else if (Def.IconName != NAME_None)
	{
		IconBrush = FAppStyle::Get().GetBrush(Def.IconName);
	}

	const TSharedRef<SWidget> ButtonContent =
		SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.HAlign(HAlign_Center)
		.Padding(FMargin(0.0f, 2.0f, 0.0f, 0.0f))
		[
			SNew(SBox)
			.WidthOverride(WorldBLDToolbarButtonConstants::IconExtent)
			.HeightOverride(WorldBLDToolbarButtonConstants::IconExtent)
			[
				SNew(SImage)
				.Image(IconBrush)
				.ColorAndOpacity(this, &SWorldBLDToolbarButton::GetIconColorAndOpacity)
			]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		.HAlign(HAlign_Center)
		.Padding(FMargin(
			ToolBarStyle.LabelPadding.Left,
			ToolBarStyle.LabelPadding.Top + 5.0f,
			ToolBarStyle.LabelPadding.Right,
			ToolBarStyle.LabelPadding.Bottom))
		[
			SNew(STextBlock)
			.TextStyle(&ToolBarStyle.LabelStyle)
			.Text(Def.Label)
			.Justification(ETextJustify::Center)
		];

	const TSharedRef<SButton> Button =
		SNew(SButton)
		.ButtonStyle(&ToolBarStyle.ButtonStyle)
		.ContentPadding(FMargin(4.0f, 2.0f))
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		.IsEnabled(this, &SWorldBLDToolbarButton::IsButtonEnabled)
		.ToolTipText(this, &SWorldBLDToolbarButton::GetTooltipText)
		.OnClicked(this, &SWorldBLDToolbarButton::HandleClicked)
		[
			ButtonContent
		];

	if (Def.IsAnchor())
	{
		ChildSlot
		[
			SAssignNew(MenuAnchor, SMenuAnchor)
			.Placement(MenuPlacement_BelowAnchor)
			.OnGetMenuContent(Def.OnGetMenuContent)
			[
				Button
			]
		];
	}
	else
	{
		ChildSlot
		[
			Button
		];
	}
}

FReply SWorldBLDToolbarButton::HandleClicked()
{
	if (Def.IsAnchor() && MenuAnchor.IsValid())
	{
		MenuAnchor->SetIsOpen(!MenuAnchor->IsOpen());
		return FReply::Handled();
	}

	Def.OnClicked.ExecuteIfBound();
	return FReply::Handled();
}

bool SWorldBLDToolbarButton::IsButtonEnabled() const
{
	return !EnabledAttr.IsBound() || EnabledAttr.Get();
}

FText SWorldBLDToolbarButton::GetTooltipText() const
{
	return Def.Tooltip.IsEmpty() ? Def.Label : Def.Tooltip;
}

FSlateColor SWorldBLDToolbarButton::GetIconColorAndOpacity() const
{
	// Dim the icon when disabled so the grayed-out state reads clearly.
	if (IsButtonEnabled())
	{
		return Def.IconColorAndOpacity;
	}

	FLinearColor DisabledColor = Def.IconColorAndOpacity.GetSpecifiedColor();
	DisabledColor.A *= 0.35f;
	return FSlateColor(DisabledColor);
}
