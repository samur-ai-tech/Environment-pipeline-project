// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/SWorldBLDAssetGrid.h"

#include "AssetLibrary/SWorldBLDAssetTile.h"
#include "AssetLibrary/SWorldBLDCollectionTile.h"
#include "ContextMenu/WorldBLDContextMenuFont.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"

#include "Styling/AppStyle.h"
#include "Types/SlateEnums.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

void SWorldBLDAssetGrid::Construct(const FArguments& InArgs)
{
	Assets = InArgs._Assets;
	Kits = InArgs._Kits;
	Collections = InArgs._Collections;
	bShowKits = InArgs._bShowKits;
	bShowCollections = InArgs._bShowCollections;
	OnAssetClicked = InArgs._OnAssetClicked;
	OnCollectionClicked = InArgs._OnCollectionClicked;
	OnViewAllKitsRequested = InArgs._OnViewAllKitsRequested;
	OnUserScrolled = InArgs._OnUserScrolled;

	ChildSlot
	[
		SAssignNew(ScrollBox, SScrollBox)
		.OnUserScrolled(OnUserScrolled)
	];

	RefreshGrid();
}

void SWorldBLDAssetGrid::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

	float AvailableWidth = AllottedGeometry.GetLocalSize().X;
	if (ScrollBox.IsValid() && ScrollBox->GetScrollOffsetOfEnd() > 0.0f)
	{
		AvailableWidth = FMath::Max(0.0f, AvailableWidth - ScrollBarThickness);
	}

	if (AvailableWidth <= 1.0f || bShowCollections)
	{
		return;
	}

	const float NewTileWidth = ComputeFilledTileWidth(AvailableWidth, AssetTileMinSize);
	if (!FMath::IsNearlyEqual(NewTileWidth, CachedTileWidth, 0.5f))
	{
		CachedTileWidth = NewTileWidth;
		Invalidate(EInvalidateWidgetReason::Layout);
		if (WrapBox.IsValid())
		{
			WrapBox->Invalidate(EInvalidateWidgetReason::Layout);
		}
	}
}

void SWorldBLDAssetGrid::RefreshGrid()
{
	if (!ScrollBox.IsValid())
	{
		return;
	}

	const float PreviousScrollOffset = ScrollBox->GetScrollOffset();
	const float PreviousFeaturedOffset = FeaturedKitsScrollBox.IsValid()
		? FeaturedKitsScrollBox->GetScrollOffset()
		: 0.0f;

	ScrollBox->ClearChildren();

	if (CanShowFeaturedSection())
	{
		ScrollBox->AddSlot()
		.HAlign(HAlign_Fill)
		.Padding(FMargin(0.0f, 10.0f))
		[
			BuildFeaturedHeader()
		];

		ScrollBox->AddSlot()
		.HAlign(HAlign_Fill)
		[
			BuildFeaturedStrip()
		];

		ScrollBox->AddSlot()
		.HAlign(HAlign_Fill)
		.Padding(FMargin(0.0f, 14.0f, 0.0f, 0.0f))
		[
			BuildSectionDivider()
		];

		ScrollBox->AddSlot()
		.HAlign(HAlign_Fill)
		.Padding(FMargin(0.0f, 10.0f))
		[
			BuildLatestAssetsHeader()
		];
	}

	ScrollBox->AddSlot()
	.HAlign(HAlign_Fill)
	[
		SAssignNew(WrapBox, SWrapBox)
		.UseAllottedSize(true)
		.InnerSlotPadding(FVector2D(GridSlotPadding, GridSlotPadding))
		.HAlign(HAlign_Left)
	];

	if (!WrapBox.IsValid())
	{
		return;
	}

	WrapBox->ClearChildren();

	if (bShowCollections)
	{
		for (const FWorldBLDCollectionInfo& Collection : Collections)
		{
			WrapBox->AddSlot()
			[
				SNew(SWorldBLDCollectionTile)
				.Collection(Collection)
				.OnClicked(OnCollectionClicked)
			];
		}
	}
	else if (bShowKits)
	{
		for (const FWorldBLDKitInfo& Kit : Kits)
		{
			WrapBox->AddSlot()
			[
				SNew(SWorldBLDAssetTile)
				.KitInfo(Kit)
				.bIsKit(true)
				.TileSize(this, &SWorldBLDAssetGrid::GetAssetTileSize)
				.OnClicked(OnAssetClicked)
			];
		}
	}
	else
	{
		for (const FWorldBLDAssetInfo& Asset : Assets)
		{
			WrapBox->AddSlot()
			[
				SNew(SWorldBLDAssetTile)
				.AssetInfo(Asset)
				.bIsKit(false)
				.TileSize(this, &SWorldBLDAssetGrid::GetAssetTileSize)
				.OnClicked(OnAssetClicked)
			];
		}
	}

	RefreshFeaturedKitsStrip();

	if (FeaturedKitsScrollBox.IsValid())
	{
		FeaturedKitsScrollBox->SetScrollOffset(PreviousFeaturedOffset);
	}

	// Preserve scroll position when the grid is rebuilt (important for infinite-scroll growth).
	ScrollBox->SetScrollOffset(PreviousScrollOffset);
}

TSharedRef<SWidget> SWorldBLDAssetGrid::BuildFeaturedHeader()
{
	return SNew(SBox)
		.MaxDesiredWidth(1.0f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.FillWidth(1.0f)
			.VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text(FText::FromString(TEXT("FEATURED KITS")))
				.Font(WorldBLDContextMenuFont::GetMedium(13.0f, 80))
				.ColorAndOpacity(FLinearColor(0.95f, 0.95f, 0.95f, 1.0f))
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			.HAlign(HAlign_Right)
			[
				SNew(SButton)
				.ButtonStyle(FAppStyle::Get(), "NoBorder")
				.ContentPadding(FMargin(0.0f))
				.Cursor(EMouseCursor::Hand)
				.OnClicked(this, &SWorldBLDAssetGrid::HandleViewAllKitsClicked)
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("View All Kits   ")))
					.Font(WorldBLDContextMenuFont::GetMedium(12.0f, 40))
					.ColorAndOpacity(WorldBLDContextMenuStyle::GetHighlightRedColor())
				]
			]
		];
}

TSharedRef<SWidget> SWorldBLDAssetGrid::BuildFeaturedStrip()
{
	// MaxDesiredWidth(1) keeps this strip from reporting N×tile width, which would
	// stretch the vertical scroll box and leave a gap beside the asset wrap grid.
	return SNew(SBox)
		.MaxDesiredWidth(1.0f)
		.HeightOverride(FeaturedKitTileHeight)
		[
			SNew(SOverlay)
			+ SOverlay::Slot()
			[
				SAssignNew(FeaturedKitsScrollBox, SScrollBox)
				.Orientation(Orient_Horizontal)
				.ScrollBarVisibility(EVisibility::Collapsed)
				.ConsumeMouseWheel(EConsumeMouseWheel::Never)
				.OnUserScrolled_Lambda([this](float)
				{
					Invalidate(EInvalidateWidgetReason::Paint);
				})
			]
			+ SOverlay::Slot()
			.HAlign(HAlign_Left)
			.VAlign(VAlign_Center)
			.Padding(FMargin(4.0f, 0.0f))
			[
				SNew(SBox)
				.WidthOverride(34.0f)
				.HeightOverride(34.0f)
				[
					SNew(SButton)
					.ButtonStyle(FAppStyle::Get(), "Button")
					.ContentPadding(0.0f)
					.HAlign(HAlign_Center)
					.VAlign(VAlign_Center)
					.Visibility(this, &SWorldBLDAssetGrid::GetFeaturedPrevVisibility)
					.OnClicked(this, &SWorldBLDAssetGrid::HandleFeaturedPrevClicked)
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT("<")))
					]
				]
			]
			+ SOverlay::Slot()
			.HAlign(HAlign_Right)
			.VAlign(VAlign_Center)
			.Padding(FMargin(4.0f, 0.0f))
			[
				SNew(SBox)
				.WidthOverride(34.0f)
				.HeightOverride(34.0f)
				[
					SNew(SButton)
					.ButtonStyle(FAppStyle::Get(), "Button")
					.ContentPadding(0.0f)
					.HAlign(HAlign_Center)
					.VAlign(VAlign_Center)
					.Visibility(this, &SWorldBLDAssetGrid::GetFeaturedNextVisibility)
					.OnClicked(this, &SWorldBLDAssetGrid::HandleFeaturedNextClicked)
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT(">")))
					]
				]
			]
		];
}

TSharedRef<SWidget> SWorldBLDAssetGrid::BuildSectionDivider()
{
	return SNew(SBox)
		.MaxDesiredWidth(1.0f)
		.HeightOverride(1.0f)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.16f, 0.16f, 0.16f, 1.0f))
			.Padding(0.0f)
		];
}

TSharedRef<SWidget> SWorldBLDAssetGrid::BuildLatestAssetsHeader()
{
	return SNew(SBox)
		.MaxDesiredWidth(1.0f)
		[
			SNew(STextBlock)
			.Text(FText::FromString(TEXT("LATEST ASSETS")))
			.Font(WorldBLDContextMenuFont::GetMedium(13.0f, 80))
			.ColorAndOpacity(FLinearColor(0.95f, 0.95f, 0.95f, 1.0f))
		];
}

void SWorldBLDAssetGrid::RefreshFeaturedKitsStrip()
{
	if (!FeaturedKitsScrollBox.IsValid())
	{
		return;
	}

	FeaturedKitsScrollBox->ClearChildren();

	if (!CanShowFeaturedSection())
	{
		return;
	}

	for (const FWorldBLDCollectionInfo& Collection : FeaturedKits)
	{
		FeaturedKitsScrollBox->AddSlot()
		.Padding(FMargin(0.0f, 0.0f, FeaturedKitTilePadding, 0.0f))
		[
			SNew(SWorldBLDCollectionTile)
			.Collection(Collection)
			.OnClicked(OnCollectionClicked)
		];
	}
}

void SWorldBLDAssetGrid::ScrollToTop()
{
	if (ScrollBox.IsValid())
	{
		ScrollBox->SetScrollOffset(0.0f);
	}
}

void SWorldBLDAssetGrid::SetAssets(const TArray<FWorldBLDAssetInfo>& InAssets)
{
	Assets = InAssets;
	bShowKits = false;
	bShowCollections = false;
	bShowHome = false;
	RefreshGrid();
}

void SWorldBLDAssetGrid::SetKits(const TArray<FWorldBLDKitInfo>& InKits)
{
	Kits = InKits;
	bShowKits = true;
	bShowCollections = false;
	bShowHome = false;
	RefreshGrid();
}

void SWorldBLDAssetGrid::SetCollections(const TArray<FWorldBLDCollectionInfo>& InCollections)
{
	Collections = InCollections;
	bShowCollections = true;
	bShowKits = false;
	bShowHome = false;
	RefreshGrid();
}

void SWorldBLDAssetGrid::SetHomeView(const TArray<FWorldBLDCollectionInfo>& InFeaturedKits, const TArray<FWorldBLDAssetInfo>& InAssets)
{
	FeaturedKits = InFeaturedKits;
	Assets = InAssets;
	bShowHome = true;
	bShowKits = false;
	bShowCollections = false;
	RefreshGrid();
}

FReply SWorldBLDAssetGrid::HandleViewAllKitsClicked()
{
	OnViewAllKitsRequested.ExecuteIfBound();
	return FReply::Handled();
}

FReply SWorldBLDAssetGrid::HandleFeaturedPrevClicked()
{
	ScrollFeaturedBy(-(FeaturedKitTileWidth + FeaturedKitTilePadding));
	return FReply::Handled();
}

FReply SWorldBLDAssetGrid::HandleFeaturedNextClicked()
{
	ScrollFeaturedBy(FeaturedKitTileWidth + FeaturedKitTilePadding);
	return FReply::Handled();
}

void SWorldBLDAssetGrid::ScrollFeaturedBy(float Delta)
{
	if (!FeaturedKitsScrollBox.IsValid())
	{
		return;
	}

	const float NewOffset = FMath::Clamp(
		FeaturedKitsScrollBox->GetScrollOffset() + Delta,
		0.0f,
		FeaturedKitsScrollBox->GetScrollOffsetOfEnd());
	FeaturedKitsScrollBox->SetScrollOffset(NewOffset);
	Invalidate(EInvalidateWidgetReason::Paint);
}

EVisibility SWorldBLDAssetGrid::GetFeaturedPrevVisibility() const
{
	if (!CanShowFeaturedSection() || !FeaturedKitsScrollBox.IsValid() || FeaturedKits.Num() <= 1)
	{
		return EVisibility::Collapsed;
	}

	return FeaturedKitsScrollBox->GetScrollOffset() > 1.0f ? EVisibility::Visible : EVisibility::Collapsed;
}

EVisibility SWorldBLDAssetGrid::GetFeaturedNextVisibility() const
{
	if (!CanShowFeaturedSection() || !FeaturedKitsScrollBox.IsValid() || FeaturedKits.Num() <= 1)
	{
		return EVisibility::Collapsed;
	}

	const float EndOffset = FeaturedKitsScrollBox->GetScrollOffsetOfEnd();
	if (EndOffset <= 0.0f)
	{
		return EVisibility::Collapsed;
	}

	return (EndOffset - FeaturedKitsScrollBox->GetScrollOffset()) > 1.0f
		? EVisibility::Visible
		: EVisibility::Collapsed;
}

bool SWorldBLDAssetGrid::CanShowFeaturedSection() const
{
	return bShowHome && FeaturedKits.Num() > 0;
}

float SWorldBLDAssetGrid::ComputeFilledTileWidth(float AvailableWidth, float MinTileWidth) const
{
	if (AvailableWidth <= MinTileWidth)
	{
		return MinTileWidth;
	}

	const int32 NumColumns = FMath::Max(1, FMath::FloorToInt((AvailableWidth + GridSlotPadding) / (MinTileWidth + GridSlotPadding)));
	return (AvailableWidth - (NumColumns - 1) * GridSlotPadding) / static_cast<float>(NumColumns);
}

float SWorldBLDAssetGrid::GetAssetTileSize() const
{
	return CachedTileWidth;
}

bool SWorldBLDAssetGrid::IsNearEnd(float CurrentScrollOffset, float RemainingThreshold) const
{
	if (!ScrollBox.IsValid())
	{
		return false;
	}

	const float EndOffset = ScrollBox->GetScrollOffsetOfEnd();
	if (EndOffset <= 0.0f)
	{
		// Not scrollable; do not treat this as "near end" to avoid accidental eager loads.
		return false;
	}

	const float Remaining = EndOffset - CurrentScrollOffset;
	return Remaining <= RemainingThreshold;
}
