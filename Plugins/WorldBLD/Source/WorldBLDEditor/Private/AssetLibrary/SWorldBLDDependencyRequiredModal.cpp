// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/SWorldBLDDependencyRequiredModal.h"
#include "AssetLibrary/SWorldBLDAssetTile.h"

#include "Framework/Application/SlateApplication.h"
#include "Misc/MessageDialog.h"
#include "Styling/AppStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

void SWorldBLDDependencyRequiredModal::Construct(const FArguments& InArgs)
{
	MissingDependencies = InArgs._MissingDependencies;
	TotalCreditsCost    = InArgs._TotalCreditsCost;
	UserCredits         = InArgs._UserCredits;
	OnNavigateToDependency = InArgs._OnNavigateToDependency;
	OnGoBack      = InArgs._OnGoBack;
	OnPurchaseAll = InArgs._OnPurchaseAll;

	// Build the tile wrap box programmatically so we can iterate the dependency list.
	// Tiles are 200×200 px; PreferredSize(652) fits three per row inside the 680px dialog.
	TSharedRef<SWrapBox> TileWrapBox = SNew(SWrapBox)
		.PreferredSize(652.0f)
		.InnerSlotPadding(FVector2D(8.0f, 8.0f));

	for (const FWorldBLDAssetInfo& DepAsset : MissingDependencies)
	{
		TileWrapBox->AddSlot()
		[
			SNew(SWorldBLDAssetTile)
			.AssetInfo(DepAsset)
			.KitInfo(FWorldBLDKitInfo())
			.bIsKit(false)
			.OnClicked(FOnWorldBLDAssetTileClicked::CreateLambda(
				[this, DepAsset](bool /*bIsKit*/, const FWorldBLDAssetInfo& /*Info*/, const FWorldBLDKitInfo& /*Kit*/) -> FReply
				{
					// Notify the owner to navigate to this dependency, then close the window.
					OnNavigateToDependency.ExecuteIfBound(DepAsset.PackageId);

					TSharedPtr<SWindow> ParentWindow = FSlateApplication::Get().FindWidgetWindow(AsShared());
					if (ParentWindow.IsValid())
					{
						ParentWindow->RequestDestroyWindow();
					}
					return FReply::Handled();
				}))
		];
	}

	const FString PurchaseButtonLabel = TotalCreditsCost > 0
		? FString::Printf(TEXT("Get All Required Assets (%d Credits)"), TotalCreditsCost)
		: TEXT("Get All Required Assets (Free)");

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FAppStyle::Get().GetBrush("ToolPanel.GroupBorder"))
		.Padding(20.0f)
		[
			SNew(SBox)
			.MinDesiredWidth(680.0f)
			[
				SNew(SVerticalBox)

				// Title
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(0.0f, 0.0f, 0.0f, 8.0f)
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("Required Assets")))
					.Font(FAppStyle::Get().GetFontStyle("HeadingExtraSmall"))
				]

				// Subtitle
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(0.0f, 0.0f, 0.0f, 16.0f)
				[
					SNew(STextBlock)
					.Text(FText::FromString(
						TEXT("Heads up: this asset uses some other assets in the library. You must own these before you can purchase. Do you want to get them now?")
						TEXT("If you'd like to review them first, click any tile to open it in the asset library.")))
					.AutoWrapText(true)
					.ColorAndOpacity(FLinearColor(0.75f, 0.75f, 0.75f, 1.0f))
				]

				// Dependency tiles (scrollable in case there are many)
				+ SVerticalBox::Slot()
				.AutoHeight()
				.MaxHeight(500.0f)
				.Padding(0.0f, 0.0f, 0.0f, 20.0f)
				[
					SNew(SScrollBox)
					+ SScrollBox::Slot()
					[
						TileWrapBox
					]
				]

				// Button row: [Go Back] ---- [Get All Required Assets]
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(SHorizontalBox)

					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						SNew(SButton)
						.ButtonStyle(FAppStyle::Get(), "Button")
						.Text(FText::FromString(TEXT("Go Back")))
						.HAlign(HAlign_Center)
						.OnClicked(this, &SWorldBLDDependencyRequiredModal::HandleGoBack)
					]

					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					[
						SNew(SSpacer)
					]

					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						SNew(SButton)
						.ButtonStyle(FAppStyle::Get(), "PrimaryButton")
						.Text(FText::FromString(PurchaseButtonLabel))
						.HAlign(HAlign_Center)
						.IsEnabled(this, &SWorldBLDDependencyRequiredModal::CanPurchaseAll)
						.OnClicked(this, &SWorldBLDDependencyRequiredModal::HandlePurchaseAll)
					]
				]
			]
		]
	];
}

FReply SWorldBLDDependencyRequiredModal::HandleGoBack()
{
	OnGoBack.ExecuteIfBound();

	TSharedPtr<SWindow> ParentWindow = FSlateApplication::Get().FindWidgetWindow(AsShared());
	if (ParentWindow.IsValid())
	{
		ParentWindow->RequestDestroyWindow();
	}
	return FReply::Handled();
}

FReply SWorldBLDDependencyRequiredModal::HandlePurchaseAll()
{
	OnPurchaseAll.ExecuteIfBound();

	TSharedPtr<SWindow> ParentWindow = FSlateApplication::Get().FindWidgetWindow(AsShared());
	if (ParentWindow.IsValid())
	{
		ParentWindow->RequestDestroyWindow();
	}

	FMessageDialog::Open(
		EAppMsgType::Ok,
		FText::FromString(TEXT("Assets purchased successfully. You can now retry your previous purchase.")));

	return FReply::Handled();
}

bool SWorldBLDDependencyRequiredModal::CanPurchaseAll() const
{
	return UserCredits >= TotalCreditsCost;
}
