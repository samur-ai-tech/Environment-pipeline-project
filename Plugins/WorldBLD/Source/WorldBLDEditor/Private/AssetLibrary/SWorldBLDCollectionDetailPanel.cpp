// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/SWorldBLDCollectionDetailPanel.h"

#include "AssetLibrary/SWorldBLDAssetLibraryDetailHeader.h"
#include "AssetLibrary/SWorldBLDConfirmPurchaseModal.h"
#include "AssetLibrary/WorldBLDAssetDownloadManager.h"
#include "AssetLibrary/WorldBLDAssetEngineVersionUtils.h"
#include "AssetLibrary/WorldBLDAssetLibraryCategoryTypes.h"
#include "AssetLibrary/WorldBLDAssetLibraryImageLoader.h"
#include "AssetLibrary/WorldBLDAssetLibrarySubsystem.h"
#include "Authorization/WorldBLDAuthSubsystem.h"
#include "Authorization/WorldBLDLoginWindow.h"
#include "ContextMenu/WorldBLDContextMenuFont.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"

#include "ContentBrowserModule.h"
#include "IContentBrowserSingleton.h"
#include "Modules/ModuleManager.h"

#include "Editor.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/PlatformProcess.h"
#include "Misc/MessageDialog.h"

#include "Styling/AppStyle.h"
#include "Styling/SlateBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Notifications/SProgressBar.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace WorldBLDCollectionDetailPanel_Private
{
	static FSlateFontInfo MakeAppFont(const FName& FontStyleName, int32 Size)
	{
		FSlateFontInfo Font = FAppStyle::Get().GetFontStyle(FontStyleName);
		Font.Size = Size;
		return Font;
	}

	static FSlateFontInfo GetCreditsLabelFont()
	{
		return WorldBLDContextMenuFont::GetThin(12.0f, 0);
	}

	static FSlateFontInfo GetCreditsValueFont()
	{
		return MakeAppFont(TEXT("BoldFont"), 12);
	}

	static const FSlateBrush* GetPanelBackgroundBrush()
	{
		static const FVector4 CornerRadii(6.0f, 6.0f, 6.0f, 6.0f);
		static const FSlateRoundedBoxBrush Brush(FLinearColor(0.07f, 0.07f, 0.08f, 1.0f), CornerRadii);
		return &Brush;
	}

	static const FSlateBrush* GetInfoBannerBrush()
	{
		static const FVector4 CornerRadii(4.0f, 4.0f, 4.0f, 4.0f);
		static const FSlateRoundedBoxBrush Brush(FLinearColor(0.09f, 0.09f, 0.10f, 1.0f), CornerRadii);
		return &Brush;
	}

	static TSharedRef<SWidget> MakeSpecRow(const FString& Label, const FString& Value)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text(FText::FromString(Label))
				.ColorAndOpacity(FLinearColor(0.72f, 0.72f, 0.72f, 1.0f))
			]
			+ SHorizontalBox::Slot()
			.FillWidth(1.0f)
			.VAlign(VAlign_Center)
			.Padding(FMargin(8.0f, 0.0f))
			[
				SNew(SBox)
				.HeightOverride(1.0f)
				[
					SNew(SBorder)
					.BorderImage(FAppStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(FLinearColor(0.28f, 0.28f, 0.28f, 0.55f))
					.Padding(0.0f)
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			.HAlign(HAlign_Right)
			[
				SNew(STextBlock)
				.Text(FText::FromString(Value))
				.ColorAndOpacity(FLinearColor(0.94f, 0.94f, 0.94f, 1.0f))
			];
	}
}

SWorldBLDCollectionDetailPanel::~SWorldBLDCollectionDetailPanel()
{
	if (ApplicationReactivatedHandle.IsValid())
	{
		FCoreDelegates::ApplicationHasReactivatedDelegate.Remove(ApplicationReactivatedHandle);
		ApplicationReactivatedHandle.Reset();
	}
}

void SWorldBLDCollectionDetailPanel::Construct(const FArguments& InArgs)
{
	OnBackRequested = InArgs._OnBackRequested;
	OnViewAllAssets = InArgs._OnViewAllAssets;

	AssetLibrarySubsystem = GEditor ? GEditor->GetEditorSubsystem<UWorldBLDAssetLibrarySubsystem>() : nullptr;
	DownloadManager = GEditor ? GEditor->GetEditorSubsystem<UWorldBLDAssetDownloadManager>() : nullptr;
	AuthSubsystem = GEditor ? GEditor->GetEditorSubsystem<UWorldBLDAuthSubsystem>() : nullptr;

	if (AuthSubsystem.IsValid() && !AuthSubsystem->GetSessionToken().IsEmpty())
	{
		AuthSubsystem->ValidateSession();
	}

	if (!CreditsRefreshTimerHandle.IsValid())
	{
		CreditsRefreshTimerHandle = RegisterActiveTimer(1.0f, FWidgetActiveTimerDelegate::CreateSP(this, &SWorldBLDCollectionDetailPanel::HandleCreditsRefreshTick));
	}
	if (!ApplicationReactivatedHandle.IsValid())
	{
		ApplicationReactivatedHandle = FCoreDelegates::ApplicationHasReactivatedDelegate.AddSP(this, &SWorldBLDCollectionDetailPanel::HandleApplicationHasReactivated);
	}

	ChildSlot
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.HAlign(HAlign_Left)
		.Padding(FMargin(0.0f, 0.0f, 0.0f, 10.0f))
		[
			SNew(SButton)
			.ButtonStyle(FAppStyle::Get(), "NoBorder")
			.ContentPadding(FMargin(0.0f))
			.Cursor(EMouseCursor::Hand)
			.OnClicked_Lambda([this]()
			{
				HandleBackClicked();
				return FReply::Handled();
			})
			[
				SNew(STextBlock)
				.Text(FText::FromString(TEXT("← Back to Kits")))
				.ColorAndOpacity(FLinearColor(0.75f, 0.75f, 0.75f, 1.0f))
			]
		]
		+ SVerticalBox::Slot()
		.FillHeight(0.58f)
		.Padding(FMargin(0.0f, 0.0f, 0.0f, 10.0f))
		[
			SAssignNew(DetailHeader, SWorldBLDAssetLibraryDetailHeader)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.FillHeight(1.0f)
				[
					SNew(SScrollBox)
					+ SScrollBox::Slot()
					[
						SNew(STextBlock)
						.Text(this, &SWorldBLDCollectionDetailPanel::GetTitleText)
						.Font_Lambda([]()
						{
							FSlateFontInfo TitleFont = FAppStyle::Get().GetFontStyle("BoldFont");
							TitleFont.Size = 32;
							return TitleFont;
						})
						.ColorAndOpacity(FLinearColor(0.95f, 0.95f, 0.95f, 1.0f))
						.AutoWrapText(true)
					]
					+ SScrollBox::Slot()
					.Padding(FMargin(0.0f, 12.0f, 0.0f, 0.0f))
					[
						SNew(STextBlock)
						.Text(this, &SWorldBLDCollectionDetailPanel::GetDescriptionText)
						.AutoWrapText(true)
					]
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 0.0f, 0.0f, 6.0f))
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.VAlign(VAlign_Center)
						[
							SNew(STextBlock)
							.Text(this, &SWorldBLDCollectionDetailPanel::GetStatusText)
							.Visibility(this, &SWorldBLDCollectionDetailPanel::GetStatusTextVisibility)
							.Font_Lambda([]()
							{
								return WorldBLDContextMenuFont::GetMedium(16.0f, -10);
							})
						]
						+ SHorizontalBox::Slot()
						.FillWidth(1.0f)
						[
							SNew(SSpacer)
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.VAlign(VAlign_Center)
						[
							SNew(STextBlock)
							.Text_Lambda([this]()
							{
								return FText::FromString(GetPriceText().ToString().ToUpper());
							})
							.Visibility(this, &SWorldBLDCollectionDetailPanel::GetPriceVisibility)
							.Font_Lambda([]()
							{
								return WorldBLDContextMenuFont::GetMedium(16.0f, -10);
							})
						]
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.HAlign(HAlign_Fill)
					.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
					[
						SNew(SButton)
						.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
						.Visibility(this, &SWorldBLDCollectionDetailPanel::GetPurchaseButtonVisibility)
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						.ContentPadding(FMargin(3.0f))
						.IsEnabled_Lambda([this]()
						{
							return !IsAnyActionQueueRunning()
								&& (!UWorldBLDAuthSubsystem::IsLoggedIn() || (AuthSubsystem.IsValid() && bDetailsLoaded));
						})
						.OnClicked(this, &SWorldBLDCollectionDetailPanel::HandlePurchaseClicked)
						[
							SNew(STextBlock)
							.Text(this, &SWorldBLDCollectionDetailPanel::GetPurchaseButtonText)
							.Font(WorldBLDContextMenuFont::GetMedium(16.0f, -10))
							.Justification(ETextJustify::Center)
						]
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.HAlign(HAlign_Fill)
					.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
					[
						SNew(SButton)
						.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
						.Visibility(this, &SWorldBLDCollectionDetailPanel::GetDownloadButtonVisibility)
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						.ContentPadding(FMargin(3.0f))
						.IsEnabled_Lambda([this]()
						{
							if (bDownloadInProgress || bPurchaseInProgress || bImportInProgress || !bDetailsLoaded)
							{
								return false;
							}

							TArray<FString> DownloadableIds;
							CollectDownloadableAssetIds(DownloadableIds);
							return DownloadManager.IsValid() && DownloadableIds.Num() > 0;
						})
						.OnClicked(this, &SWorldBLDCollectionDetailPanel::HandleDownloadClicked)
						[
							SNew(STextBlock)
							.Text(this, &SWorldBLDCollectionDetailPanel::GetDownloadButtonText)
							.Font(WorldBLDContextMenuFont::GetMedium(16.0f, -10))
							.Justification(ETextJustify::Center)
						]
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 6.0f, 0.0f, 0.0f))
					[
						SNew(SProgressBar)
						.Visibility(this, &SWorldBLDCollectionDetailPanel::GetDownloadProgressVisibility)
						.Percent(this, &SWorldBLDCollectionDetailPanel::GetDownloadProgressValue)
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.HAlign(HAlign_Fill)
					.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
					[
						SNew(SButton)
						.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
						.Visibility(this, &SWorldBLDCollectionDetailPanel::GetImportButtonVisibility)
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						.ContentPadding(FMargin(3.0f))
						.IsEnabled_Lambda([this]()
						{
							if (IsAnyActionQueueRunning() || !bDetailsLoaded || !DownloadManager.IsValid())
							{
								return false;
							}

							TArray<FString> ImportableIds;
							CollectImportableAssetIds(ImportableIds);
							return ImportableIds.Num() > 0;
						})
						.OnClicked(this, &SWorldBLDCollectionDetailPanel::HandleImportClicked)
						[
							SNew(STextBlock)
							.Text(this, &SWorldBLDCollectionDetailPanel::GetImportButtonText)
							.Font(WorldBLDContextMenuFont::GetMedium(16.0f, -10))
							.Justification(ETextJustify::Center)
						]
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot()
						.FillWidth(1.0f)
						[
							SNew(SSpacer)
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.VAlign(VAlign_Center)
						[
							SNew(STextBlock)
							.Text(FText::FromString(TEXT("Your Credits: ")))
							.Font(WorldBLDCollectionDetailPanel_Private::GetCreditsLabelFont())
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.VAlign(VAlign_Center)
						[
							SNew(STextBlock)
							.Text_Lambda([this]()
							{
								return FText::AsNumber(AuthSubsystem.IsValid() ? AuthSubsystem->GetUserCredits() : 0);
							})
							.Font(WorldBLDCollectionDetailPanel_Private::GetCreditsValueFont())
						]
					]
				]
			]
		]
		+ SVerticalBox::Slot()
		.FillHeight(0.42f)
		[
			SNew(SScrollBox)
			+ SScrollBox::Slot()
			.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
			[
			SNew(SBorder)
			.BorderImage(WorldBLDCollectionDetailPanel_Private::GetInfoBannerBrush())
			.Padding(0.0f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SBox)
					.WidthOverride(4.0f)
					[
						SNew(SBorder)
						.BorderImage(FAppStyle::Get().GetBrush("WhiteBrush"))
						.BorderBackgroundColor(WorldBLDContextMenuStyle::GetHighlightRedColor())
						.Padding(0.0f)
					]
				]
				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.VAlign(VAlign_Center)
				.Padding(FMargin(12.0f, 10.0f))
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("This kit is a collection of other assets on the store. The price is calculated based on what you don't already own, so you only pay for what's new to your library.")))
					.ColorAndOpacity(FLinearColor(0.82f, 0.82f, 0.82f, 1.0f))
					.AutoWrapText(true)
				]
			]
		]
		+ SScrollBox::Slot()
		.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
		[
			SNew(SBorder)
			.BorderImage(WorldBLDCollectionDetailPanel_Private::GetInfoBannerBrush())
			.Padding(0.0f)
			.Visibility(this, &SWorldBLDCollectionDetailPanel::GetEngineCompatibilityWarningVisibility)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SBox)
					.WidthOverride(4.0f)
					[
						SNew(SBorder)
						.BorderImage(FAppStyle::Get().GetBrush("WhiteBrush"))
						.BorderBackgroundColor(FLinearColor(0.92f, 0.62f, 0.12f, 1.0f))
						.Padding(0.0f)
					]
				]
				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.VAlign(VAlign_Center)
				.Padding(FMargin(12.0f, 10.0f))
				[
					SNew(STextBlock)
					.Text(this, &SWorldBLDCollectionDetailPanel::GetEngineCompatibilityWarningText)
					.ColorAndOpacity(FLinearColor(0.92f, 0.82f, 0.55f, 1.0f))
					.AutoWrapText(true)
				]
			]
		]
		+ SScrollBox::Slot()
		.Padding(FMargin(0.0f, 18.0f, 0.0f, 0.0f))
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.FillWidth(0.5f)
			.Padding(FMargin(0.0f, 0.0f, 10.0f, 0.0f))
			[
				SNew(SBorder)
				.BorderImage(WorldBLDCollectionDetailPanel_Private::GetPanelBackgroundBrush())
				.Padding(FMargin(16.0f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 0.0f, 0.0f, 12.0f))
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT("KIT SPECIFICATIONS")))
						.Font(WorldBLDContextMenuFont::GetMedium(13.0f, 80))
						.ColorAndOpacity(FLinearColor(0.95f, 0.95f, 0.95f, 1.0f))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SAssignNew(SpecsList, SVerticalBox)
					]
				]
			]
			+ SHorizontalBox::Slot()
			.FillWidth(0.5f)
			.Padding(FMargin(10.0f, 0.0f, 0.0f, 0.0f))
			[
				SNew(SBorder)
				.BorderImage(WorldBLDCollectionDetailPanel_Private::GetPanelBackgroundBrush())
				.Padding(FMargin(16.0f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT("INCLUDED IN THIS KIT")))
						.Font(WorldBLDContextMenuFont::GetMedium(13.0f, 80))
						.ColorAndOpacity(FLinearColor(0.95f, 0.95f, 0.95f, 1.0f))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 8.0f, 0.0f, 12.0f))
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT("This kit includes the following assets and collections.")))
						.ColorAndOpacity(FLinearColor(0.7f, 0.7f, 0.7f, 1.0f))
						.AutoWrapText(true)
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(SButton)
						.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						.ContentPadding(FMargin(8.0f, 8.0f))
						.OnClicked(this, &SWorldBLDCollectionDetailPanel::HandleViewAllAssetsClicked)
						[
							SNew(STextBlock)
							.Text(this, &SWorldBLDCollectionDetailPanel::GetViewAllAssetsText)
							.Justification(ETextJustify::Center)
						]
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 12.0f, 0.0f, 0.0f))
					[
						SAssignNew(IncludedBreakdown, SVerticalBox)
					]
				]
			]
		]
		]
	];
}

void SWorldBLDCollectionDetailPanel::ShowCollection(const FWorldBLDCollectionInfo& Collection)
{
	CurrentCollection = Collection;
	CollectionAssets.Reset();
	bDetailsLoaded = false;
	ResetActionQueues();

	RebuildGalleryUrls();
	RefreshPreviewImages();
	RefreshSpecsList();
	RefreshIncludedBreakdown();
	Invalidate(EInvalidateWidgetReason::Paint);
}

void SWorldBLDCollectionDetailPanel::ResetActionQueues()
{
	PendingPurchaseAssetIds.Reset();
	PurchaseQueueTotal = 0;
	PurchaseQueueCompleted = 0;
	bPurchaseInProgress = false;

	PendingDownloadAssetIds.Reset();
	CurrentDownloadAssetId.Reset();
	DownloadQueueTotal = 0;
	DownloadQueueCompleted = 0;
	DownloadQueueSucceeded = 0;
	DownloadQueueFailed = 0;
	bDownloadInProgress = false;
	bCurrentDownloadStarted = false;

	PendingImportAssetIds.Reset();
	LastSuccessfulImportAssetId.Reset();
	ImportQueueTotal = 0;
	ImportQueueCompleted = 0;
	ImportQueueSucceeded = 0;
	ImportQueueFailed = 0;
	ImportQueueSkipped = 0;
	bImportInProgress = false;
}

void SWorldBLDCollectionDetailPanel::HandleCollectionDetailsFetched(const FWorldBLDCollectionDetailResponse& Response)
{
	if (!Response.bSuccess)
	{
		return;
	}

	const FString IncomingName = Response.Collection.CollectionName.TrimStartAndEnd();
	if (!IncomingName.IsEmpty() && IncomingName != CurrentCollection.CollectionName)
	{
		return;
	}

	if (!Response.Collection.CollectionName.IsEmpty())
	{
		CurrentCollection = Response.Collection;
	}

	CollectionAssets = Response.Assets;
	bDetailsLoaded = true;
	CurrentCollection.AssetCount = CountActiveCollectionAssets();

	RebuildGalleryUrls();
	RefreshPreviewImages();
	RefreshSpecsList();
	RefreshIncludedBreakdown();
	Invalidate(EInvalidateWidgetReason::Paint);
}

void SWorldBLDCollectionDetailPanel::HandleAssetStatusChanged(const FString& AssetId, EWorldBLDAssetStatus NewStatus)
{
	if (bDownloadInProgress && !AssetId.IsEmpty() && AssetId == CurrentDownloadAssetId)
	{
		if (NewStatus == EWorldBLDAssetStatus::Downloading)
		{
			bCurrentDownloadStarted = true;
		}
		else if (NewStatus == EWorldBLDAssetStatus::Downloaded || NewStatus == EWorldBLDAssetStatus::Imported)
		{
			AdvanceDownloadQueue(/*bCurrentSucceeded=*/true);
		}
		else if (NewStatus == EWorldBLDAssetStatus::Owned && bCurrentDownloadStarted)
		{
			AdvanceDownloadQueue(/*bCurrentSucceeded=*/false);
		}
	}

	Invalidate(EInvalidateWidgetReason::Paint);
}

EActiveTimerReturnType SWorldBLDCollectionDetailPanel::HandleCreditsRefreshTick(double CurrentTime, float DeltaTime)
{
	(void)DeltaTime;

	if (AuthSubsystem.IsValid() && !AuthSubsystem->GetSessionToken().IsEmpty())
	{
		const double Last = LastCreditsRefreshRequestTimeSeconds;
		const double Elapsed = (Last < 0.0) ? BIG_NUMBER : (CurrentTime - Last);
		if (Elapsed >= CreditsRefreshIntervalSeconds)
		{
			RequestCreditsRefreshFromServer(/*bForce=*/false);
		}
	}

	return EActiveTimerReturnType::Continue;
}

void SWorldBLDCollectionDetailPanel::RequestCreditsRefreshFromServer(bool bForce)
{
	if (!AuthSubsystem.IsValid() || AuthSubsystem->GetSessionToken().IsEmpty())
	{
		return;
	}

	const double Now = FPlatformTime::Seconds();
	if (!bForce && LastCreditsRefreshRequestTimeSeconds >= 0.0 && (Now - LastCreditsRefreshRequestTimeSeconds) < CreditsRefreshMinGapSeconds)
	{
		return;
	}

	LastCreditsRefreshRequestTimeSeconds = Now;
	AuthSubsystem->ValidateSession();
}

void SWorldBLDCollectionDetailPanel::HandleApplicationHasReactivated()
{
	if (!bPendingCreditsRefreshOnAppFocus)
	{
		return;
	}

	bPendingCreditsRefreshOnAppFocus = false;
	RequestCreditsRefreshFromServer(/*bForce=*/true);
}

void SWorldBLDCollectionDetailPanel::HandleBackClicked()
{
	if (OnBackRequested.IsBound())
	{
		OnBackRequested.Execute();
	}
}

FReply SWorldBLDCollectionDetailPanel::HandleViewAllAssetsClicked()
{
	if (OnViewAllAssets.IsBound())
	{
		OnViewAllAssets.Execute(CurrentCollection);
	}
	return FReply::Handled();
}

void SWorldBLDCollectionDetailPanel::RebuildGalleryUrls()
{
	GalleryUrls.Reset();
	for (const FString& Url : CurrentCollection.PreviewImages)
	{
		const FString Trimmed = Url.TrimStartAndEnd();
		if (!Trimmed.IsEmpty())
		{
			GalleryUrls.AddUnique(Trimmed);
		}
	}

	const FString ProductUrl = CurrentCollection.ProductImageURL.TrimStartAndEnd();
	if (GalleryUrls.Num() == 0 && !ProductUrl.IsEmpty())
	{
		GalleryUrls.Add(ProductUrl);
	}
}

void SWorldBLDCollectionDetailPanel::RefreshPreviewImages()
{
	if (DetailHeader.IsValid())
	{
		DetailHeader->SetPreviewUrls(GalleryUrls);
	}
}

void SWorldBLDCollectionDetailPanel::RefreshSpecsList()
{
	if (!SpecsList.IsValid())
	{
		return;
	}

	SpecsList->ClearChildren();

	bool bHasAssetCountFeature = false;
	for (const FString& Feature : CurrentCollection.Features)
	{
		const FString Trimmed = Feature.TrimStartAndEnd();
		if (Trimmed.IsEmpty())
		{
			continue;
		}

		FString Label;
		FString Value;
		if (Trimmed.Split(TEXT(":"), &Label, &Value))
		{
			Label = Label.TrimStartAndEnd();
			Value = Value.TrimStartAndEnd();
			if (Label.Equals(TEXT("Asset Count"), ESearchCase::IgnoreCase))
			{
				bHasAssetCountFeature = true;
			}

			SpecsList->AddSlot()
			.AutoHeight()
			.Padding(FMargin(0.0f, 0.0f, 0.0f, 8.0f))
			[
				WorldBLDCollectionDetailPanel_Private::MakeSpecRow(Label, Value)
			];
		}
		else
		{
			SpecsList->AddSlot()
			.AutoHeight()
			.Padding(FMargin(0.0f, 0.0f, 0.0f, 8.0f))
			[
				SNew(STextBlock)
				.Text(FText::FromString(Trimmed))
				.ColorAndOpacity(FLinearColor(0.86f, 0.86f, 0.86f, 1.0f))
				.AutoWrapText(true)
			];
		}
	}

	if (!bHasAssetCountFeature && CurrentCollection.AssetCount > 0)
	{
		SpecsList->AddSlot()
		.AutoHeight()
		.Padding(FMargin(0.0f, 0.0f, 0.0f, 8.0f))
		[
			WorldBLDCollectionDetailPanel_Private::MakeSpecRow(
				TEXT("Asset Count"),
				FString::Printf(TEXT("%d Assets"), CurrentCollection.AssetCount))
		];
	}

	if (SpecsList->NumSlots() == 0)
	{
		SpecsList->AddSlot()
		.AutoHeight()
		[
			SNew(STextBlock)
			.Text(FText::FromString(TEXT("No specifications listed for this kit.")))
			.ColorAndOpacity(FLinearColor(0.65f, 0.65f, 0.65f, 1.0f))
			.AutoWrapText(true)
		];
	}
}

void SWorldBLDCollectionDetailPanel::RefreshIncludedBreakdown()
{
	if (!IncludedBreakdown.IsValid())
	{
		return;
	}

	IncludedBreakdown->ClearChildren();

	const TArray<FString> CategoryTags = FWorldBLDCategoryHierarchy::GetTopLevelAssetCategoryTags();
	TMap<FString, int32> Counts;
	int32 Uncategorized = 0;

	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!Asset.bIsActive)
		{
			continue;
		}

		bool bMatched = false;
		for (const FString& CategoryTag : CategoryTags)
		{
			if (Asset.Tags.Contains(CategoryTag))
			{
				Counts.FindOrAdd(CategoryTag) += 1;
				bMatched = true;
			}
		}

		if (!bMatched)
		{
			++Uncategorized;
		}
	}

	TArray<FString> OrderedTags = CategoryTags;
	OrderedTags.Sort();

	int32 RowsAdded = 0;
	for (const FString& CategoryName : OrderedTags)
	{
		if (const int32* Count = Counts.Find(CategoryName))
		{
			IncludedBreakdown->AddSlot()
			.AutoHeight()
			.Padding(FMargin(0.0f, 0.0f, 0.0f, 6.0f))
			[
				WorldBLDCollectionDetailPanel_Private::MakeSpecRow(CategoryName, FString::FromInt(*Count))
			];
			++RowsAdded;
		}
	}

	if (Uncategorized > 0)
	{
		IncludedBreakdown->AddSlot()
		.AutoHeight()
		.Padding(FMargin(0.0f, 0.0f, 0.0f, 6.0f))
		[
			WorldBLDCollectionDetailPanel_Private::MakeSpecRow(TEXT("Other"), FString::FromInt(Uncategorized))
		];
		++RowsAdded;
	}

	if (RowsAdded == 0)
	{
		const int32 Total = CountActiveCollectionAssets();
		IncludedBreakdown->AddSlot()
		.AutoHeight()
		[
			SNew(STextBlock)
			.Text(FText::FromString(Total > 0
				? FString::Printf(TEXT("%d assets included."), Total)
				: TEXT("Asset list will appear once kit details finish loading.")))
			.ColorAndOpacity(FLinearColor(0.7f, 0.7f, 0.7f, 1.0f))
			.AutoWrapText(true)
		];
	}
}

const FSlateBrush* SWorldBLDCollectionDetailPanel::GetCurrentPreviewBrush() const
{
	if (DetailHeader.IsValid())
	{
		return DetailHeader->GetCurrentPreviewBrush();
	}

	TSharedPtr<FSlateDynamicImageBrush> Placeholder = FWorldBLDAssetLibraryImageLoader::Get().GetPlaceholderBrush();
	return Placeholder.IsValid() ? Placeholder.Get() : nullptr;
}

FText SWorldBLDCollectionDetailPanel::GetTitleText() const
{
	const FString Name = CurrentCollection.DisplayName.TrimStartAndEnd().IsEmpty()
		? CurrentCollection.CollectionName
		: CurrentCollection.DisplayName;
	return FText::FromString(Name);
}

FText SWorldBLDCollectionDetailPanel::GetDescriptionText() const
{
	const FString Description = CurrentCollection.Description.TrimStartAndEnd();
	if (!Description.IsEmpty())
	{
		return FText::FromString(Description);
	}

	return FText::FromString(TEXT("Kit details are loading..."));
}

FText SWorldBLDCollectionDetailPanel::GetPriceText() const
{
	if (!bDetailsLoaded)
	{
		return FText::FromString(TEXT("Calculating Credits"));
	}

	const int32 PriceCredits = GetUnownedCreditCost();
	if (PriceCredits <= 0)
	{
		return FText::FromString(TEXT("Free"));
	}

	return FText::FromString(FString::Printf(TEXT("%d Credits"), PriceCredits));
}

FText SWorldBLDCollectionDetailPanel::GetPurchaseButtonText() const
{
	if (bPurchaseInProgress)
	{
		return FText::FromString(FString::Printf(TEXT("PURCHASING %d OF %d"), PurchaseQueueCompleted + 1, PurchaseQueueTotal));
	}

	if (!UWorldBLDAuthSubsystem::IsLoggedIn())
	{
		return FText::FromString(TEXT("LOG IN"));
	}

	TArray<FString> UnownedIds;
	CollectUnownedAssetIds(UnownedIds);
	if (bDetailsLoaded && UnownedIds.Num() == 0)
	{
		return FText::FromString(TEXT("OWNED"));
	}

	if (!HasSufficientCredits())
	{
		return HasActiveSubscription()
			? FText::FromString(TEXT("GET MORE CREDITS"))
			: FText::FromString(TEXT("GET PLAN"));
	}

	return FText::FromString(TEXT("PURCHASE KIT"));
}

FText SWorldBLDCollectionDetailPanel::GetDownloadButtonText() const
{
	if (bDownloadInProgress)
	{
		return FText::FromString(FString::Printf(TEXT("DOWNLOADING %d OF %d"), DownloadQueueCompleted + 1, DownloadQueueTotal));
	}

	return FText::FromString(TEXT("DOWNLOAD"));
}

FText SWorldBLDCollectionDetailPanel::GetImportButtonText() const
{
	if (bImportInProgress)
	{
		return FText::FromString(FString::Printf(TEXT("IMPORTING %d OF %d"), ImportQueueCompleted + 1, ImportQueueTotal));
	}

	bool bAllImported = false;
	if (bDetailsLoaded && IsFullyOwned() && !HasEligibleAssetsNeedingDownload())
	{
		bAllImported = true;
		for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
		{
			if (!IsCollectionAssetEligible(Asset))
			{
				continue;
			}

			if (GetCollectionAssetStatus(Asset) != EWorldBLDAssetStatus::Imported)
			{
				bAllImported = false;
				break;
			}
		}
	}

	return FText::FromString(bAllImported ? TEXT("RE-IMPORT") : TEXT("IMPORT"));
}

FText SWorldBLDCollectionDetailPanel::GetStatusText() const
{
	if (!bDetailsLoaded)
	{
		return FText::FromString(TEXT("LOADING"));
	}

	switch (GetCollectionAggregateStatus())
	{
	case EWorldBLDAssetStatus::Downloading:
		return FText::FromString(TEXT("DOWNLOADING"));
	case EWorldBLDAssetStatus::Downloaded:
		return FText::FromString(TEXT("DOWNLOADED"));
	case EWorldBLDAssetStatus::Imported:
		return FText::FromString(TEXT("IMPORTED"));
	case EWorldBLDAssetStatus::Owned:
		return FText::FromString(TEXT("OWNED"));
	case EWorldBLDAssetStatus::NotOwned:
	default:
		return FText::FromString(TEXT("NOT OWNED"));
	}
}

EVisibility SWorldBLDCollectionDetailPanel::GetPurchaseButtonVisibility() const
{
	if (bPurchaseInProgress)
	{
		return EVisibility::Visible;
	}

	return IsFullyOwned() ? EVisibility::Collapsed : EVisibility::Visible;
}

EVisibility SWorldBLDCollectionDetailPanel::GetDownloadButtonVisibility() const
{
	if (bDownloadInProgress)
	{
		return EVisibility::Visible;
	}

	if (!bDetailsLoaded || !IsFullyOwned() || bPurchaseInProgress || bImportInProgress)
	{
		return EVisibility::Collapsed;
	}

	return HasEligibleAssetsNeedingDownload() ? EVisibility::Visible : EVisibility::Collapsed;
}

EVisibility SWorldBLDCollectionDetailPanel::GetImportButtonVisibility() const
{
	if (bImportInProgress)
	{
		return EVisibility::Visible;
	}

	if (!bDetailsLoaded || !IsFullyOwned() || bPurchaseInProgress || bDownloadInProgress)
	{
		return EVisibility::Collapsed;
	}

	if (HasEligibleAssetsNeedingDownload())
	{
		return EVisibility::Collapsed;
	}

	return HasEligibleAssetsReadyToImport() ? EVisibility::Visible : EVisibility::Collapsed;
}

EVisibility SWorldBLDCollectionDetailPanel::GetDownloadProgressVisibility() const
{
	if (!bDownloadInProgress || !DownloadManager.IsValid() || CurrentDownloadAssetId.IsEmpty())
	{
		return EVisibility::Collapsed;
	}

	return DownloadManager->IsDownloadInProgress(CurrentDownloadAssetId)
		? EVisibility::Visible
		: EVisibility::Collapsed;
}

TOptional<float> SWorldBLDCollectionDetailPanel::GetDownloadProgressValue() const
{
	if (!DownloadManager.IsValid() || CurrentDownloadAssetId.IsEmpty())
	{
		return TOptional<float>();
	}

	const float Progress = DownloadManager->GetDownloadProgress(CurrentDownloadAssetId);
	if (Progress < 0.0f)
	{
		return TOptional<float>();
	}

	return FMath::Clamp(Progress, 0.0f, 1.0f);
}

EVisibility SWorldBLDCollectionDetailPanel::GetStatusTextVisibility() const
{
	return EVisibility::Visible;
}

EVisibility SWorldBLDCollectionDetailPanel::GetPriceVisibility() const
{
	if (!bDetailsLoaded)
	{
		return EVisibility::Visible;
	}

	return IsFullyOwned() ? EVisibility::Collapsed : EVisibility::Visible;
}

FText SWorldBLDCollectionDetailPanel::GetViewAllAssetsText() const
{
	const int32 Count = bDetailsLoaded
		? CountActiveCollectionAssets()
		: CurrentCollection.AssetCount;
	return FText::FromString(FString::Printf(TEXT("VIEW ALL %d ASSETS"), Count));
}

int32 SWorldBLDCollectionDetailPanel::CountActiveCollectionAssets() const
{
	int32 Count = 0;
	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (Asset.bIsActive)
		{
			++Count;
		}
	}

	return Count;
}

int32 SWorldBLDCollectionDetailPanel::CountIncompatibleEngineAssets() const
{
	int32 IncompatibleCount = 0;
	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!Asset.bIsActive)
		{
			continue;
		}

		if (!WorldBLDAssetEngineVersionUtils::IsEngineVersionCompatible(Asset.EngineVersions))
		{
			++IncompatibleCount;
		}
	}

	return IncompatibleCount;
}

EVisibility SWorldBLDCollectionDetailPanel::GetEngineCompatibilityWarningVisibility() const
{
	return CountIncompatibleEngineAssets() > 0 ? EVisibility::Visible : EVisibility::Collapsed;
}

FText SWorldBLDCollectionDetailPanel::GetEngineCompatibilityWarningText() const
{
	const int32 IncompatibleCount = CountIncompatibleEngineAssets();
	const int32 TotalCount = CountActiveCollectionAssets();
	const FString Current = WorldBLDAssetEngineVersionUtils::GetCurrentEngineMajorMinorString();

	if (TotalCount > 0 && IncompatibleCount >= TotalCount)
	{
		return FText::FromString(FString::Printf(
			TEXT("None of the assets in this kit support Unreal Engine %s."),
			*Current));
	}

	return FText::FromString(FString::Printf(
		TEXT("%d of %d assets in this kit do not support Unreal Engine %s and cannot be used in this editor."),
		IncompatibleCount,
		TotalCount,
		*Current));
}

bool SWorldBLDCollectionDetailPanel::HasSufficientCredits() const
{
	const int32 PriceCredits = GetUnownedCreditCost();
	if (PriceCredits <= 0)
	{
		return true;
	}

	if (!AuthSubsystem.IsValid())
	{
		return false;
	}

	return AuthSubsystem->GetUserCredits() >= PriceCredits;
}

bool SWorldBLDCollectionDetailPanel::HasActiveSubscription() const
{
	return AuthSubsystem.IsValid()
		&& (AuthSubsystem->HasLicenseForTool(TEXT("RoadBLD")) || AuthSubsystem->HasLicenseForTool(TEXT("CityBLD")));
}

bool SWorldBLDCollectionDetailPanel::IsCollectionAssetOwned(const FWorldBLDCollectionAsset& Asset) const
{
	if (Asset.ID.IsEmpty() || !DownloadManager.IsValid())
	{
		return false;
	}

	return DownloadManager->GetAssetStatus(Asset.ID) != EWorldBLDAssetStatus::NotOwned;
}

bool SWorldBLDCollectionDetailPanel::IsFullyOwned() const
{
	if (!bDetailsLoaded)
	{
		return false;
	}

	TArray<FString> UnownedIds;
	CollectUnownedAssetIds(UnownedIds);
	return UnownedIds.Num() == 0;
}

int32 SWorldBLDCollectionDetailPanel::GetUnownedCreditCost() const
{
	int32 Total = 0;
	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!Asset.bIsActive || Asset.bIsFree || IsCollectionAssetOwned(Asset))
		{
			continue;
		}

		Total += FMath::Max(0, Asset.CreditsPrice);
	}

	return Total;
}

void SWorldBLDCollectionDetailPanel::CollectUnownedAssetIds(TArray<FString>& OutAssetIds) const
{
	OutAssetIds.Reset();
	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!Asset.bIsActive || Asset.ID.IsEmpty() || IsCollectionAssetOwned(Asset))
		{
			continue;
		}

		OutAssetIds.Add(Asset.ID);
	}
}

bool SWorldBLDCollectionDetailPanel::IsAnyActionQueueRunning() const
{
	return bPurchaseInProgress || bDownloadInProgress || bImportInProgress;
}

bool SWorldBLDCollectionDetailPanel::IsCollectionAssetEligible(const FWorldBLDCollectionAsset& Asset) const
{
	return Asset.bIsActive
		&& !Asset.ID.IsEmpty()
		&& WorldBLDAssetEngineVersionUtils::IsEngineVersionCompatible(Asset.EngineVersions);
}

EWorldBLDAssetStatus SWorldBLDCollectionDetailPanel::GetCollectionAssetStatus(const FWorldBLDCollectionAsset& Asset) const
{
	if (Asset.ID.IsEmpty() || !DownloadManager.IsValid())
	{
		return EWorldBLDAssetStatus::NotOwned;
	}

	return DownloadManager->GetAssetStatus(Asset.ID);
}

EWorldBLDAssetStatus SWorldBLDCollectionDetailPanel::GetCollectionAggregateStatus() const
{
	if (bDownloadInProgress)
	{
		return EWorldBLDAssetStatus::Downloading;
	}

	bool bAnyEligible = false;
	bool bAnyNotOwned = false;
	bool bAnyOwned = false;
	bool bAnyDownloading = false;
	bool bAnyDownloaded = false;
	bool bAnyImported = false;

	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!IsCollectionAssetEligible(Asset))
		{
			continue;
		}

		bAnyEligible = true;
		switch (GetCollectionAssetStatus(Asset))
		{
		case EWorldBLDAssetStatus::NotOwned:
			bAnyNotOwned = true;
			break;
		case EWorldBLDAssetStatus::Owned:
			bAnyOwned = true;
			break;
		case EWorldBLDAssetStatus::Downloading:
			bAnyDownloading = true;
			break;
		case EWorldBLDAssetStatus::Downloaded:
			bAnyDownloaded = true;
			break;
		case EWorldBLDAssetStatus::Imported:
			bAnyImported = true;
			break;
		default:
			break;
		}
	}

	if (!bAnyEligible)
	{
		return IsFullyOwned() ? EWorldBLDAssetStatus::Owned : EWorldBLDAssetStatus::NotOwned;
	}

	if (bAnyNotOwned)
	{
		return EWorldBLDAssetStatus::NotOwned;
	}
	if (bAnyDownloading)
	{
		return EWorldBLDAssetStatus::Downloading;
	}
	if (bAnyOwned)
	{
		return EWorldBLDAssetStatus::Owned;
	}
	if (bAnyDownloaded)
	{
		return EWorldBLDAssetStatus::Downloaded;
	}
	if (bAnyImported)
	{
		return EWorldBLDAssetStatus::Imported;
	}

	return EWorldBLDAssetStatus::NotOwned;
}

bool SWorldBLDCollectionDetailPanel::HasEligibleAssetsNeedingDownload() const
{
	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!IsCollectionAssetEligible(Asset))
		{
			continue;
		}

		const EWorldBLDAssetStatus Status = GetCollectionAssetStatus(Asset);
		if (Status == EWorldBLDAssetStatus::Owned || Status == EWorldBLDAssetStatus::Downloading)
		{
			return true;
		}
	}

	return false;
}

bool SWorldBLDCollectionDetailPanel::HasEligibleAssetsReadyToImport() const
{
	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!IsCollectionAssetEligible(Asset))
		{
			continue;
		}

		const EWorldBLDAssetStatus Status = GetCollectionAssetStatus(Asset);
		if (Status == EWorldBLDAssetStatus::Downloaded || Status == EWorldBLDAssetStatus::Imported)
		{
			return true;
		}
	}

	return false;
}

void SWorldBLDCollectionDetailPanel::CollectDownloadableAssetIds(TArray<FString>& OutAssetIds) const
{
	OutAssetIds.Reset();
	if (!DownloadManager.IsValid())
	{
		return;
	}

	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!IsCollectionAssetEligible(Asset))
		{
			continue;
		}

		if (GetCollectionAssetStatus(Asset) != EWorldBLDAssetStatus::Owned)
		{
			continue;
		}

		if (DownloadManager->IsDownloadInProgress(Asset.ID))
		{
			continue;
		}

		OutAssetIds.Add(Asset.ID);
	}
}

void SWorldBLDCollectionDetailPanel::CollectImportableAssetIds(TArray<FString>& OutAssetIds) const
{
	OutAssetIds.Reset();

	TArray<FString> DownloadedIds;
	TArray<FString> ImportedIds;
	for (const FWorldBLDCollectionAsset& Asset : CollectionAssets)
	{
		if (!IsCollectionAssetEligible(Asset))
		{
			continue;
		}

		const EWorldBLDAssetStatus Status = GetCollectionAssetStatus(Asset);
		if (Status == EWorldBLDAssetStatus::Downloaded)
		{
			DownloadedIds.Add(Asset.ID);
		}
		else if (Status == EWorldBLDAssetStatus::Imported)
		{
			ImportedIds.Add(Asset.ID);
		}
	}

	OutAssetIds = DownloadedIds.Num() > 0 ? MoveTemp(DownloadedIds) : MoveTemp(ImportedIds);
}

FReply SWorldBLDCollectionDetailPanel::HandlePurchaseClicked()
{
	if (IsAnyActionQueueRunning())
	{
		return FReply::Handled();
	}

	if (!AssetLibrarySubsystem.IsValid())
	{
		return FReply::Handled();
	}

	if (!UWorldBLDAuthSubsystem::IsLoggedIn())
	{
		FWorldBLDLoginWindow::OpenLoginDialog();
		return FReply::Handled();
	}

	if (!bDetailsLoaded)
	{
		return FReply::Handled();
	}

	TArray<FString> UnownedIds;
	CollectUnownedAssetIds(UnownedIds);
	if (UnownedIds.Num() == 0)
	{
		return FReply::Handled();
	}

	if (!HasSufficientCredits())
	{
		static const TCHAR* PurchaseCreditsUrl = TEXT("https://worldbld.com/purchase-credits");
		static const TCHAR* PlansUrl = TEXT("https://www.worldbld.com/plans");

		bPendingCreditsRefreshOnAppFocus = true;
		FPlatformProcess::LaunchURL(HasActiveSubscription() ? PurchaseCreditsUrl : PlansUrl, nullptr, nullptr);
		return FReply::Handled();
	}

	TSharedRef<SWindow> Dialog = SNew(SWindow)
		.Title(FText::FromString(TEXT("Confirm Purchase")))
		.SizingRule(ESizingRule::Autosized)
		.SupportsMaximize(false)
		.SupportsMinimize(false);

	const FString ItemName = GetTitleText().ToString();
	const int32 UserCredits = AuthSubsystem.IsValid() ? AuthSubsystem->GetUserCredits() : 0;
	const int32 PriceCredits = GetUnownedCreditCost();
	const FSlateBrush* PurchaseModalBrush = GetCurrentPreviewBrush();

	Dialog->SetContent(
		SNew(SWorldBLDConfirmPurchaseModal)
		.ItemName(ItemName)
		.PriceCredits(PriceCredits)
		.bIsFree(PriceCredits <= 0)
		.UserCredits(UserCredits)
		.PreviewBrush(PurchaseModalBrush)
		.OnCancel(FSimpleDelegate::CreateLambda([Dialog]()
		{
			Dialog->RequestDestroyWindow();
		}))
		.OnConfirm(FSimpleDelegate::CreateLambda([this, Dialog, UnownedIds]()
		{
			Dialog->RequestDestroyWindow();
			StartPurchaseQueue(UnownedIds);
		}))
	);

	FSlateApplication::Get().AddModalWindow(Dialog, FSlateApplication::Get().GetActiveTopLevelWindow());
	return FReply::Handled();
}

void SWorldBLDCollectionDetailPanel::StartPurchaseQueue(const TArray<FString>& AssetIds)
{
	PendingPurchaseAssetIds = AssetIds;
	PurchaseQueueTotal = PendingPurchaseAssetIds.Num();
	PurchaseQueueCompleted = 0;
	bPurchaseInProgress = PurchaseQueueTotal > 0;
	Invalidate(EInvalidateWidgetReason::Paint);
	PurchaseNextQueuedAsset();
}

void SWorldBLDCollectionDetailPanel::PurchaseNextQueuedAsset()
{
	if (!bPurchaseInProgress)
	{
		return;
	}

	if (PendingPurchaseAssetIds.Num() == 0)
	{
		FinishPurchaseQueue(true, TEXT(""));
		return;
	}

	if (!AssetLibrarySubsystem.IsValid())
	{
		FinishPurchaseQueue(false, TEXT("Asset library is unavailable."));
		return;
	}

	AssetLibrarySubsystem->PurchaseAsset(PendingPurchaseAssetIds[0]);
}

void SWorldBLDCollectionDetailPanel::HandlePurchaseComplete(bool bSuccess, int32 RemainingCredits)
{
	(void)RemainingCredits;

	if (!bPurchaseInProgress)
	{
		return;
	}

	if (!bSuccess)
	{
		FinishPurchaseQueue(false, TEXT("One of the kit assets could not be purchased. Remaining items were not charged."));
		return;
	}

	if (PendingPurchaseAssetIds.Num() > 0)
	{
		PendingPurchaseAssetIds.RemoveAt(0);
	}
	++PurchaseQueueCompleted;
	Invalidate(EInvalidateWidgetReason::Paint);
	PurchaseNextQueuedAsset();
}

void SWorldBLDCollectionDetailPanel::FinishPurchaseQueue(bool bSuccess, const FString& ErrorMessage)
{
	bPurchaseInProgress = false;
	PendingPurchaseAssetIds.Reset();
	Invalidate(EInvalidateWidgetReason::Paint);

	if (DownloadManager.IsValid())
	{
		DownloadManager->RefreshOwnershipStatus();
	}

	RequestCreditsRefreshFromServer(/*bForce=*/true);

	if (!bSuccess)
	{
		ShowInfoModal(FText::FromString(TEXT("Kit Purchase Incomplete")), FText::FromString(ErrorMessage));
		return;
	}

	TArray<FString> RemainingUnowned;
	CollectUnownedAssetIds(RemainingUnowned);
	if (RemainingUnowned.Num() == 0)
	{
		ShowInfoModal(
			FText::FromString(TEXT("Kit Purchased")),
			FText::FromString(TEXT("You now own every asset in this kit.")));
	}
}

FReply SWorldBLDCollectionDetailPanel::HandleDownloadClicked()
{
	if (IsAnyActionQueueRunning() || !bDetailsLoaded || !AssetLibrarySubsystem.IsValid())
	{
		return FReply::Handled();
	}

	TArray<FString> DownloadableIds;
	CollectDownloadableAssetIds(DownloadableIds);
	if (DownloadableIds.Num() == 0)
	{
		return FReply::Handled();
	}

	StartDownloadQueue(DownloadableIds);
	return FReply::Handled();
}

void SWorldBLDCollectionDetailPanel::StartDownloadQueue(const TArray<FString>& AssetIds)
{
	PendingDownloadAssetIds = AssetIds;
	CurrentDownloadAssetId.Reset();
	DownloadQueueTotal = PendingDownloadAssetIds.Num();
	DownloadQueueCompleted = 0;
	DownloadQueueSucceeded = 0;
	DownloadQueueFailed = 0;
	bDownloadInProgress = DownloadQueueTotal > 0;
	bCurrentDownloadStarted = false;
	Invalidate(EInvalidateWidgetReason::Paint);
	DownloadNextQueuedAsset();
}

void SWorldBLDCollectionDetailPanel::DownloadNextQueuedAsset()
{
	if (!bDownloadInProgress)
	{
		return;
	}

	if (PendingDownloadAssetIds.Num() == 0)
	{
		FinishDownloadQueue();
		return;
	}

	if (!AssetLibrarySubsystem.IsValid())
	{
		DownloadQueueFailed += PendingDownloadAssetIds.Num();
		PendingDownloadAssetIds.Reset();
		FinishDownloadQueue();
		return;
	}

	CurrentDownloadAssetId = PendingDownloadAssetIds[0];
	bCurrentDownloadStarted = false;
	AssetLibrarySubsystem->RequestDownloadURL(CurrentDownloadAssetId, /*bIsKit=*/false);
}

void SWorldBLDCollectionDetailPanel::AdvanceDownloadQueue(bool bCurrentSucceeded)
{
	if (!bDownloadInProgress)
	{
		return;
	}

	if (bCurrentSucceeded)
	{
		++DownloadQueueSucceeded;
	}
	else
	{
		++DownloadQueueFailed;
	}

	if (PendingDownloadAssetIds.Num() > 0)
	{
		PendingDownloadAssetIds.RemoveAt(0);
	}

	++DownloadQueueCompleted;
	CurrentDownloadAssetId.Reset();
	bCurrentDownloadStarted = false;
	Invalidate(EInvalidateWidgetReason::Paint);
	DownloadNextQueuedAsset();
}

void SWorldBLDCollectionDetailPanel::HandleDownloadUrlFailed(const FString& ErrorMessage)
{
	(void)ErrorMessage;

	if (!bDownloadInProgress)
	{
		return;
	}

	AdvanceDownloadQueue(/*bCurrentSucceeded=*/false);
}

void SWorldBLDCollectionDetailPanel::FinishDownloadQueue()
{
	const int32 Succeeded = DownloadQueueSucceeded;
	const int32 Failed = DownloadQueueFailed;
	const int32 Total = DownloadQueueTotal;

	bDownloadInProgress = false;
	PendingDownloadAssetIds.Reset();
	CurrentDownloadAssetId.Reset();
	bCurrentDownloadStarted = false;
	Invalidate(EInvalidateWidgetReason::Paint);

	if (Failed <= 0)
	{
		ShowInfoModal(
			FText::FromString(TEXT("Kit Downloaded")),
			FText::FromString(TEXT("Downloaded every eligible asset in this kit.")));
		return;
	}

	ShowInfoModal(
		FText::FromString(TEXT("Kit Download Incomplete")),
		FText::FromString(FString::Printf(
			TEXT("Downloaded %d of %d eligible assets. %d could not be downloaded."),
			Succeeded,
			Total,
			Failed)));
}

FReply SWorldBLDCollectionDetailPanel::HandleImportClicked()
{
	if (IsAnyActionQueueRunning() || !bDetailsLoaded || !DownloadManager.IsValid())
	{
		return FReply::Handled();
	}

	TArray<FString> ImportableIds;
	CollectImportableAssetIds(ImportableIds);
	if (ImportableIds.Num() == 0)
	{
		return FReply::Handled();
	}

	StartImportQueue(ImportableIds);
	return FReply::Handled();
}

void SWorldBLDCollectionDetailPanel::StartImportQueue(const TArray<FString>& AssetIds)
{
	PendingImportAssetIds.Reset();
	LastSuccessfulImportAssetId.Reset();
	ImportQueueTotal = AssetIds.Num();
	ImportQueueCompleted = 0;
	ImportQueueSucceeded = 0;
	ImportQueueFailed = 0;
	ImportQueueSkipped = 0;
	bImportInProgress = ImportQueueTotal > 0;

	TArray<FString> AssetsToImport;
	for (const FString& AssetId : AssetIds)
	{
		if (!DownloadManager.IsValid() || !DownloadManager->HasLocalCache(AssetId))
		{
			++ImportQueueSkipped;
			++ImportQueueCompleted;
			continue;
		}

		AssetsToImport.Add(AssetId);
	}

	PendingImportAssetIds = AssetsToImport;
	Invalidate(EInvalidateWidgetReason::Paint);

	if (PendingImportAssetIds.Num() == 0 || !DownloadManager.IsValid())
	{
		if (!DownloadManager.IsValid())
		{
			ImportQueueFailed += PendingImportAssetIds.Num();
			PendingImportAssetIds.Reset();
		}
		FinishImportQueue();
		return;
	}

	const TArray<FString> AssetsToStart = PendingImportAssetIds;
	for (const FString& AssetId : AssetsToStart)
	{
		if (DownloadManager.IsValid())
		{
			DownloadManager->ImportAsset(AssetId);
		}
	}
}

void SWorldBLDCollectionDetailPanel::HandleImportComplete(const FString& AssetId, bool bSuccess)
{
	if (!bImportInProgress || AssetId.IsEmpty())
	{
		return;
	}

	const int32 PendingIndex = PendingImportAssetIds.IndexOfByKey(AssetId);
	if (PendingIndex == INDEX_NONE)
	{
		return;
	}

	PendingImportAssetIds.RemoveAt(PendingIndex);
	++ImportQueueCompleted;
	if (bSuccess)
	{
		++ImportQueueSucceeded;
		LastSuccessfulImportAssetId = AssetId;
	}
	else
	{
		++ImportQueueFailed;
	}

	Invalidate(EInvalidateWidgetReason::Paint);

	if (PendingImportAssetIds.Num() == 0)
	{
		FinishImportQueue();
	}
}

void SWorldBLDCollectionDetailPanel::FinishImportQueue()
{
	const int32 Succeeded = ImportQueueSucceeded;
	const int32 Failed = ImportQueueFailed;
	const int32 Skipped = ImportQueueSkipped;
	const int32 Total = ImportQueueTotal;
	const FString ImportedAssetId = LastSuccessfulImportAssetId;

	bImportInProgress = false;
	PendingImportAssetIds.Reset();
	LastSuccessfulImportAssetId.Reset();
	Invalidate(EInvalidateWidgetReason::Paint);

	SyncContentBrowserToLastImportedAsset(ImportedAssetId);

	if (Failed <= 0 && Skipped <= 0)
	{
		ShowInfoModal(
			FText::FromString(TEXT("Kit Imported")),
			FText::FromString(TEXT("Imported every eligible asset in this kit.")));
		return;
	}

	ShowInfoModal(
		FText::FromString(TEXT("Kit Import Incomplete")),
		FText::FromString(FString::Printf(
			TEXT("Imported %d of %d eligible assets. %d failed, %d skipped because local cache was missing."),
			Succeeded,
			Total,
			Failed,
			Skipped)));
}

void SWorldBLDCollectionDetailPanel::SyncContentBrowserToLastImportedAsset(const FString& AssetId)
{
	if (AssetId.IsEmpty() || !DownloadManager.IsValid())
	{
		return;
	}

	FString ImportedPackageRoot;
	if (!DownloadManager->GetImportedPackageRoot(AssetId, ImportedPackageRoot) || ImportedPackageRoot.IsEmpty())
	{
		return;
	}

	FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>(TEXT("ContentBrowser"));
	IContentBrowserSingleton& ContentBrowser = ContentBrowserModule.Get();
	ContentBrowser.SyncBrowserToFolders({ ImportedPackageRoot }, /*bAllowLockedBrowsers=*/true, /*bFocusContentBrowser=*/true);
}

void SWorldBLDCollectionDetailPanel::ShowInfoModal(const FText& Title, const FText& Message)
{
	TSharedRef<SWindow> Dialog = SNew(SWindow)
		.Title(Title)
		.SizingRule(ESizingRule::Autosized)
		.SupportsMaximize(false)
		.SupportsMinimize(false);

	Dialog->SetContent(
		SNew(SBorder)
		.BorderImage(FAppStyle::Get().GetBrush("Brushes.Panel"))
		.Padding(FMargin(14.0f))
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(Message)
				.AutoWrapText(true)
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Right)
			.Padding(FMargin(0.0f, 12.0f, 0.0f, 0.0f))
			[
				SNew(SButton)
				.Text(FText::FromString(TEXT("OK")))
				.OnClicked_Lambda([Dialog]()
				{
					Dialog->RequestDestroyWindow();
					return FReply::Handled();
				})
			]
		]
	);

	FSlateApplication::Get().AddModalWindow(Dialog, FSlateApplication::Get().GetActiveTopLevelWindow());
}
