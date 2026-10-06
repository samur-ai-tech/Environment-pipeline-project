// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/SWorldBLDAssetTile.h"

#include "AssetLibrary/WorldBLDAssetDownloadManager.h"
#include "AssetLibrary/WorldBLDAssetLibraryImageLoader.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"

#include "Editor.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Styling/AppStyle.h"
#include "Styling/SlateTypes.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace WorldBLDAssetTile_Constants
{
	constexpr float TileSize = 200.0f;
	constexpr float TileCornerRadius = 10.0f;
	constexpr float StatusCheckSize = 16.0f;
}

void SWorldBLDAssetTile::Construct(const FArguments& InArgs)
{
	constexpr float LabelMinHeight = 56.0f;

	AssetInfo = InArgs._AssetInfo;
	KitInfo = InArgs._KitInfo;
	bIsKit = InArgs._bIsKit;
	TileSize = InArgs._TileSize;
	OnClicked = InArgs._OnClicked;

	DownloadManager = GEditor ? GEditor->GetEditorSubsystem<UWorldBLDAssetDownloadManager>() : nullptr;

	const FString ThumbnailURL = bIsKit ? (KitInfo.PreviewImages.Num() > 0 ? KitInfo.PreviewImages[0] : FString()) : AssetInfo.ThumbnailURL;
	ThumbnailBrush = FWorldBLDAssetLibraryImageLoader::Get().GetPlaceholderBrush();

	FWorldBLDAssetLibraryImageLoader::Get().LoadImageFromURL(ThumbnailURL, [WeakThis = TWeakPtr<SWorldBLDAssetTile>(SharedThis(this))](TSharedPtr<FSlateDynamicImageBrush> LoadedBrush)
	{
		if (TSharedPtr<SWorldBLDAssetTile> Pinned = WeakThis.Pin())
		{
			Pinned->ThumbnailBrush = LoadedBrush;
			Pinned->Invalidate(EInvalidateWidgetReason::Paint);
		}
	});

	// Prefetch preview images for this tile while the user is browsing the grid, so detail-panel preview
	// images display instantly on selection. This naturally only runs for tiles that are actually constructed
	// (i.e., items currently visible in the grid).
	const TArray<FString>& PreviewUrls = bIsKit ? KitInfo.PreviewImages : AssetInfo.PreviewImages;
	FWorldBLDAssetLibraryImageLoader::Get().PrefetchImagesFromURLs(PreviewUrls);

	static const FSlateRoundedBoxBrush TileBackgroundBrush(
		FLinearColor(0.025f, 0.025f, 0.025f, 1.0f),
		WorldBLDAssetTile_Constants::TileCornerRadius);

	ChildSlot
	[
		SNew(SBox)
		.WidthOverride(this, &SWorldBLDAssetTile::GetTileSizeOverride)
		[
			SNew(SBorder)
			.Padding(0.0f)
			.BorderImage(&TileBackgroundBrush)
			.Cursor(EMouseCursor::Hand)
			.Clipping(EWidgetClipping::ClipToBounds)
			[
				SNew(SOverlay)
				+ SOverlay::Slot()
				.HAlign(HAlign_Fill)
				.VAlign(VAlign_Fill)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(SBox)
						.WidthOverride(this, &SWorldBLDAssetTile::GetTileSizeOverride)
						.HeightOverride(this, &SWorldBLDAssetTile::GetTileSizeOverride)
						[
							SNew(SOverlay)
							+ SOverlay::Slot()
							[
								SNew(SImage)
								.Image(this, &SWorldBLDAssetTile::GetThumbnailBrush)
							]
							+ SOverlay::Slot()
							.HAlign(HAlign_Right)
							.VAlign(VAlign_Top)
							.Padding(FMargin(8.0f))
							[
								SNew(SBox)
								.WidthOverride(WorldBLDAssetTile_Constants::StatusCheckSize)
								.HeightOverride(WorldBLDAssetTile_Constants::StatusCheckSize)
								.Visibility(this, &SWorldBLDAssetTile::GetStatusCheckVisibility)
								[
									SNew(SImage)
									.Image(FAppStyle::Get().GetBrush("Icons.Check"))
									.ColorAndOpacity(this, &SWorldBLDAssetTile::GetStatusCheckColor)
								]
							]
						]
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(SBox)
						.MinDesiredHeight(LabelMinHeight)
						[
						SNew(SBorder)
						.Padding(FMargin(8.0f, 10.0f))
						.BorderImage(FStyleDefaults::GetNoBrush())
						[
						SNew(STextBlock)
						.Text(this, &SWorldBLDAssetTile::GetDisplayName)
						.ColorAndOpacity(FLinearColor(0.92f, 0.92f, 0.92f, 1.0f))
						.WrapTextAt(this, &SWorldBLDAssetTile::GetTextWrapAt)
						.Justification(ETextJustify::Center)
						.Font(FCoreStyle::GetDefaultFontStyle("Bold", 11))
						]
						]
					]
				]
				+ SOverlay::Slot()
				.HAlign(HAlign_Fill)
				.VAlign(VAlign_Fill)
				[
					SNew(SBorder)
					.Visibility(this, &SWorldBLDAssetTile::GetHoverOutlineVisibility)
					.Padding(0.0f)
					.BorderImage(this, &SWorldBLDAssetTile::GetHoverOutlineBrush)
					[
						SNew(SSpacer)
					]
				]
			]
		]
	];
}

void SWorldBLDAssetTile::OnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	bIsHovered = true;
	SCompoundWidget::OnMouseEnter(MyGeometry, MouseEvent);
	Invalidate(EInvalidateWidgetReason::Paint);
}

void SWorldBLDAssetTile::OnMouseLeave(const FPointerEvent& MouseEvent)
{
	bIsHovered = false;
	SCompoundWidget::OnMouseLeave(MouseEvent);
	Invalidate(EInvalidateWidgetReason::Paint);
}

FReply SWorldBLDAssetTile::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		return HandleClicked();
	}

	return SCompoundWidget::OnMouseButtonDown(MyGeometry, MouseEvent);
}

FReply SWorldBLDAssetTile::HandleClicked()
{
	if (OnClicked.IsBound())
	{
		return OnClicked.Execute(bIsKit, AssetInfo, KitInfo);
	}

	return FReply::Handled();
}

EWorldBLDAssetStatus SWorldBLDAssetTile::GetAssetStatus() const
{
	if (!DownloadManager.IsValid())
	{
		return EWorldBLDAssetStatus::NotOwned;
	}

	const FString AssetId = bIsKit ? KitInfo.ID : AssetInfo.ID;
	return DownloadManager->GetAssetStatus(AssetId);
}

FSlateColor SWorldBLDAssetTile::GetStatusCheckColor() const
{
	switch (GetAssetStatus())
	{
	case EWorldBLDAssetStatus::Downloaded:
		return WorldBLDContextMenuStyle::GetHighlightRedColor();
	case EWorldBLDAssetStatus::Imported:
		return FLinearColor(0.2f, 0.8f, 0.3f, 1.0f);
	case EWorldBLDAssetStatus::Owned:
	case EWorldBLDAssetStatus::Downloading:
	default:
		return FLinearColor::White;
	}
}

EVisibility SWorldBLDAssetTile::GetStatusCheckVisibility() const
{
	switch (GetAssetStatus())
	{
	case EWorldBLDAssetStatus::Owned:
	case EWorldBLDAssetStatus::Downloading:
	case EWorldBLDAssetStatus::Downloaded:
	case EWorldBLDAssetStatus::Imported:
		return EVisibility::HitTestInvisible;
	default:
		return EVisibility::Collapsed;
	}
}

FText SWorldBLDAssetTile::GetPriceText() const
{
	const bool bFree = bIsKit ? KitInfo.bIsFree : AssetInfo.bIsFree;
	if (bFree)
	{
		return FText::FromString(TEXT("Free"));
	}

	const int32 Price = bIsKit ? KitInfo.Price : AssetInfo.CreditsPrice;
	return FText::FromString(FString::Printf(TEXT("%d Credits"), Price));
}

EVisibility SWorldBLDAssetTile::GetHoverOutlineVisibility() const
{
	return bIsHovered ? EVisibility::Visible : EVisibility::Collapsed;
}

const FSlateBrush* SWorldBLDAssetTile::GetHoverOutlineBrush() const
{
	// Simple hover outline: use the same red as the highlighted purchase/get-credits buttons.
	// Corner order: TopLeft, TopRight, BottomRight, BottomLeft.
	static const FVector4 CornerRadii(
		WorldBLDAssetTile_Constants::TileCornerRadius,
		WorldBLDAssetTile_Constants::TileCornerRadius,
		WorldBLDAssetTile_Constants::TileCornerRadius,
		WorldBLDAssetTile_Constants::TileCornerRadius);

	static const FSlateBrushOutlineSettings OutlineSettings = []()
	{
		FSlateBrushOutlineSettings Settings;
		Settings.CornerRadii = CornerRadii;
		Settings.Color = FSlateColor(WorldBLDContextMenuStyle::GetHighlightRedColor());
		Settings.Width = 2.0f;
		Settings.RoundingType = ESlateBrushRoundingType::FixedRadius;
		Settings.bUseBrushTransparency = false;
		return Settings;
	}();

	static const FSlateRoundedBoxBrush Brush = []()
	{
		FSlateRoundedBoxBrush RoundedBrush(FLinearColor(0.0f, 0.0f, 0.0f, 0.0f), CornerRadii);
		RoundedBrush.OutlineSettings = OutlineSettings;
		return RoundedBrush;
	}();

	return &Brush;
}

const FSlateBrush* SWorldBLDAssetTile::GetThumbnailBrush() const
{
	const FSlateBrush* SourceBrush = nullptr;
	if (ThumbnailBrush.IsValid())
	{
		SourceBrush = ThumbnailBrush.Get();
	}
	else
	{
		TSharedPtr<FSlateDynamicImageBrush> Placeholder = FWorldBLDAssetLibraryImageLoader::Get().GetPlaceholderBrush();
		SourceBrush = Placeholder.IsValid() ? Placeholder.Get() : nullptr;
	}

	if (!SourceBrush)
	{
		return nullptr;
	}

	// Draw the thumbnail as a rounded box so the top corners match the card radius.
	// Bottom radii stay square because they sit against the label, whose card rounding is
	// already handled by TileBackgroundBrush.
	RoundedThumbnailBrush = *SourceBrush;
	RoundedThumbnailBrush.DrawAs = ESlateBrushDrawType::RoundedBox;
	RoundedThumbnailBrush.OutlineSettings.CornerRadii = FVector4(
		WorldBLDAssetTile_Constants::TileCornerRadius,
		WorldBLDAssetTile_Constants::TileCornerRadius,
		0.0f,
		0.0f);
	RoundedThumbnailBrush.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
	RoundedThumbnailBrush.OutlineSettings.Width = 0.0f;
	return &RoundedThumbnailBrush;
}

FText SWorldBLDAssetTile::GetDisplayName() const
{
	return FText::FromString(bIsKit ? KitInfo.KitsName : AssetInfo.Name);
}

float SWorldBLDAssetTile::GetTileSize() const
{
	return TileSize.Get(WorldBLDAssetTile_Constants::TileSize);
}

FOptionalSize SWorldBLDAssetTile::GetTileSizeOverride() const
{
	return FOptionalSize(GetTileSize());
}

float SWorldBLDAssetTile::GetTextWrapAt() const
{
	return FMath::Max(0.0f, GetTileSize() - 20.0f);
}
