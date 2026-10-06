// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/SWorldBLDConfirmPurchaseModal.h"

#include "ContextMenu/WorldBLDContextMenuFont.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"
#include "Framework/Application/SlateApplication.h"
#include "Styling/AppStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	static FText BuildPriceText(const bool bInIsFree, const int32 InCredits)
	{
		if (bInIsFree || InCredits <= 0)
		{
			return FText::FromString(TEXT("Free"));
		}

		return FText::FromString(FString::Printf(TEXT("%d Credits"), InCredits));
	}

static FSlateFontInfo GetConfirmPurchaseModalCreditsValueFont()
	{
		FSlateFontInfo Font = FAppStyle::Get().GetFontStyle(TEXT("BoldFont"));
		Font.Size = 14.0f;
		return Font;
	}
}

void SWorldBLDConfirmPurchaseModal::Construct(const FArguments& InArgs)
{
	ItemName = InArgs._ItemName;
	PriceCredits = InArgs._PriceCredits;
	bIsFree = InArgs._bIsFree;
	UserCredits = InArgs._UserCredits;
	PreviewBrush = InArgs._PreviewBrush;
	OnConfirm = InArgs._OnConfirm;
	OnCancel = InArgs._OnCancel;

	const FText PriceText = BuildPriceText(bIsFree, PriceCredits);
	const FString CreditsLabel = FString::Printf(TEXT("%d"), UserCredits);

	// "Purchase {Name} for" wraps naturally; the price + "?" are kept together on the next line in red.
	const FString PurchasePrefix = FString::Printf(TEXT("Purchase %s for"), *ItemName);

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FAppStyle::Get().GetBrush("ToolPanel.GroupBorder"))
		.Padding(0.0f)
		[
			SNew(SBox)
			.MinDesiredWidth(500.0f)
			[
				SNew(SVerticalBox)

				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(20.0f, 20.0f, 20.0f, 16.0f))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.Padding(FMargin(0.0f, 0.0f, 18.0f, 0.0f))
					[
						SNew(SBox)
						.WidthOverride(150.0f)
						.HeightOverride(150.0f)
						[
							SNew(SBorder)
							.BorderImage(FAppStyle::Get().GetBrush("Brushes.Panel"))
							.Padding(1.0f)
							.Clipping(EWidgetClipping::ClipToBounds)
							[
								SNew(SScaleBox)
								.Stretch(EStretch::ScaleToFill)
								.StretchDirection(EStretchDirection::Both)
								[
									SNew(SImage)
									.Image(PreviewBrush)
								]
							]
						]
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.VAlign(VAlign_Center)
					[
						SNew(SVerticalBox)

						// "Purchase {Name} for" — wraps naturally at word boundaries.
						+ SVerticalBox::Slot()
						.AutoHeight()
						[
							SNew(STextBlock)
							.Text(FText::FromString(PurchasePrefix))
							.Font(WorldBLDContextMenuFont::GetMedium(16.0f, -10))
							.ColorAndOpacity(FLinearColor(0.86f, 0.86f, 0.86f, 1.0f))
							.AutoWrapText(true)
						]

						// "{N Credits}?" on its own line so the price is always together and stays red.
						+ SVerticalBox::Slot()
						.AutoHeight()
						[
							SNew(SHorizontalBox)
							+ SHorizontalBox::Slot()
							.AutoWidth()
							.VAlign(VAlign_Center)
							[
								SNew(STextBlock)
								.Text(PriceText)
								.Font(WorldBLDContextMenuFont::GetMedium(16.0f, -10))
								.ColorAndOpacity(WorldBLDContextMenuStyle::GetHighlightRedColor())
							]
							+ SHorizontalBox::Slot()
							.AutoWidth()
							.VAlign(VAlign_Center)
							[
								SNew(STextBlock)
								.Text(FText::FromString(TEXT("?")))
								.Font(WorldBLDContextMenuFont::GetMedium(16.0f, -10))
								.ColorAndOpacity(FLinearColor(0.86f, 0.86f, 0.86f, 1.0f))
							]
						]

						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(FMargin(0.0f, 16.0f, 0.0f, 0.0f))
						[
							SNew(SHorizontalBox)
							+ SHorizontalBox::Slot()
							.AutoWidth()
							.VAlign(VAlign_Center)
							[
								SNew(STextBlock)
								.Text(FText::FromString(TEXT("Your Credits: ")))
								.Font(WorldBLDContextMenuFont::GetThin(15.0f, 0))
								.ColorAndOpacity(FLinearColor(0.78f, 0.78f, 0.78f, 1.0f))
							]
							+ SHorizontalBox::Slot()
							.AutoWidth()
							.VAlign(VAlign_Center)
							[
								SNew(STextBlock)
								.Text(FText::FromString(CreditsLabel))
								.Font(GetConfirmPurchaseModalCreditsValueFont())
								.ColorAndOpacity(FLinearColor::White)
							]
						]
					]
				]

				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(20.0f, 0.0f, 20.0f, 20.0f))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.Padding(FMargin(0.0f, 0.0f, 8.0f, 0.0f))
					[
						SNew(SBox)
						.MinDesiredHeight(42.0f)
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
							.OnClicked(this, &SWorldBLDConfirmPurchaseModal::HandleCancel)
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.ContentPadding(FMargin(18.0f, 6.0f))
							[
								SNew(STextBlock)
								.Text(FText::FromString(TEXT("CANCEL")))
								.Font(WorldBLDContextMenuFont::GetMedium(16.0f, -10))
								.ColorAndOpacity(FLinearColor(0.88f, 0.88f, 0.88f, 1.0f))
							]
						]
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.Padding(FMargin(8.0f, 0.0f, 0.0f, 0.0f))
					[
						SNew(SBox)
						.MinDesiredHeight(42.0f)
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
							.OnClicked(this, &SWorldBLDConfirmPurchaseModal::HandleConfirm)
							.IsEnabled(this, &SWorldBLDConfirmPurchaseModal::CanConfirm)
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.ContentPadding(FMargin(18.0f, 6.0f))
							[
								SNew(STextBlock)
								.Text(FText::FromString(TEXT("CONFIRM")))
								.Font(WorldBLDContextMenuFont::GetMedium(16.0f, -10))
								.ColorAndOpacity(FLinearColor::White)
							]
						]
					]
				]
			]
		]
	];
}

FReply SWorldBLDConfirmPurchaseModal::HandleCancel()
{
	OnCancel.ExecuteIfBound();

	if (const TSharedPtr<SWindow> ParentWindow = FSlateApplication::Get().FindWidgetWindow(AsShared()))
	{
		ParentWindow->RequestDestroyWindow();
	}

	return FReply::Handled();
}

FReply SWorldBLDConfirmPurchaseModal::HandleConfirm()
{
	OnConfirm.ExecuteIfBound();

	if (const TSharedPtr<SWindow> ParentWindow = FSlateApplication::Get().FindWidgetWindow(AsShared()))
	{
		ParentWindow->RequestDestroyWindow();
	}

	return FReply::Handled();
}

bool SWorldBLDConfirmPurchaseModal::CanConfirm() const
{
	return bIsFree || UserCredits >= PriceCredits;
}
