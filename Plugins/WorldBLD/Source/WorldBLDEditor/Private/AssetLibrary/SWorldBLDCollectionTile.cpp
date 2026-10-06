// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/SWorldBLDCollectionTile.h"

#include "AssetLibrary/WorldBLDAssetLibraryImageLoader.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"

#include "Brushes/SlateRoundedBoxBrush.h"
#include "Styling/SlateTypes.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/SOverlay.h"

namespace WorldBLDCollectionTile_Constants
{
	constexpr float KitTileWidth = 580.0f / 3.0f;
	constexpr float KitTileHeight = 869.0f / 3.0f;
	constexpr float TileCornerRadius = 10.0f;
}

void SWorldBLDCollectionTile::Construct(const FArguments& InArgs)
{
	Collection = InArgs._Collection;
	OnClicked = InArgs._OnClicked;
	TileWidth = InArgs._TileWidth;
	TileHeight = InArgs._TileHeight;

	ThumbnailBrush = FWorldBLDAssetLibraryImageLoader::Get().GetPlaceholderBrush();

	FWorldBLDAssetLibraryImageLoader::Get().LoadImageFromURL(Collection.ProductImageURL, [WeakThis = TWeakPtr<SWorldBLDCollectionTile>(SharedThis(this))](TSharedPtr<FSlateDynamicImageBrush> LoadedBrush)
	{
		if (TSharedPtr<SWorldBLDCollectionTile> Pinned = WeakThis.Pin())
		{
			Pinned->ThumbnailBrush = LoadedBrush;
			Pinned->Invalidate(EInvalidateWidgetReason::Paint);
		}
	});

	// Preload the kit product image so it appears instantly if this tile is reconstructed.
	FWorldBLDAssetLibraryImageLoader::Get().PrefetchImagesFromURLs({ Collection.ProductImageURL });

	static const FSlateRoundedBoxBrush TileBackgroundBrush(
		FLinearColor(0.025f, 0.025f, 0.025f, 1.0f),
		WorldBLDCollectionTile_Constants::TileCornerRadius);

	ChildSlot
	[
		SNew(SBox)
		.WidthOverride(this, &SWorldBLDCollectionTile::GetTileWidthOverride)
		.HeightOverride(this, &SWorldBLDCollectionTile::GetTileHeightOverride)
		[
			SNew(SBorder)
			.Padding(0.0f)
			.BorderImage(&TileBackgroundBrush)
			.Cursor(EMouseCursor::Hand)
			.Clipping(EWidgetClipping::ClipToBounds)
			[
				SNew(SOverlay)
				+ SOverlay::Slot()
				[
					SNew(SScaleBox)
					.Stretch(EStretch::ScaleToFill)
					.StretchDirection(EStretchDirection::Both)
					[
						SNew(SImage)
						.Image(this, &SWorldBLDCollectionTile::GetThumbnailBrush)
					]
				]
				+ SOverlay::Slot()
				.HAlign(HAlign_Fill)
				.VAlign(VAlign_Fill)
				[
					SNew(SBorder)
					.Visibility(this, &SWorldBLDCollectionTile::GetHoverOutlineVisibility)
					.Padding(0.0f)
					.BorderImage(this, &SWorldBLDCollectionTile::GetHoverOutlineBrush)
					[
						SNew(SSpacer)
					]
				]
			]
		]
	];
}

void SWorldBLDCollectionTile::OnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	bIsHovered = true;
	SCompoundWidget::OnMouseEnter(MyGeometry, MouseEvent);
	Invalidate(EInvalidateWidgetReason::Paint);
}

void SWorldBLDCollectionTile::OnMouseLeave(const FPointerEvent& MouseEvent)
{
	bIsHovered = false;
	SCompoundWidget::OnMouseLeave(MouseEvent);
	Invalidate(EInvalidateWidgetReason::Paint);
}

FReply SWorldBLDCollectionTile::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		return HandleClicked();
	}

	return SCompoundWidget::OnMouseButtonDown(MyGeometry, MouseEvent);
}

FReply SWorldBLDCollectionTile::HandleClicked()
{
	if (OnClicked.IsBound())
	{
		return OnClicked.Execute(Collection);
	}

	return FReply::Handled();
}

EVisibility SWorldBLDCollectionTile::GetHoverOutlineVisibility() const
{
	return bIsHovered ? EVisibility::Visible : EVisibility::Collapsed;
}

const FSlateBrush* SWorldBLDCollectionTile::GetHoverOutlineBrush() const
{
	static const FVector4 CornerRadii(
		WorldBLDCollectionTile_Constants::TileCornerRadius,
		WorldBLDCollectionTile_Constants::TileCornerRadius,
		WorldBLDCollectionTile_Constants::TileCornerRadius,
		WorldBLDCollectionTile_Constants::TileCornerRadius);

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

const FSlateBrush* SWorldBLDCollectionTile::GetThumbnailBrush() const
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

	RoundedThumbnailBrush = *SourceBrush;
	RoundedThumbnailBrush.DrawAs = ESlateBrushDrawType::RoundedBox;
	RoundedThumbnailBrush.OutlineSettings.CornerRadii = FVector4(
		WorldBLDCollectionTile_Constants::TileCornerRadius,
		WorldBLDCollectionTile_Constants::TileCornerRadius,
		WorldBLDCollectionTile_Constants::TileCornerRadius,
		WorldBLDCollectionTile_Constants::TileCornerRadius);
	RoundedThumbnailBrush.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
	RoundedThumbnailBrush.OutlineSettings.Width = 0.0f;
	return &RoundedThumbnailBrush;
}

FOptionalSize SWorldBLDCollectionTile::GetTileWidthOverride() const
{
	return FOptionalSize(TileWidth.Get(WorldBLDCollectionTile_Constants::KitTileWidth));
}

FOptionalSize SWorldBLDCollectionTile::GetTileHeightOverride() const
{
	return FOptionalSize(TileHeight.Get(WorldBLDCollectionTile_Constants::KitTileHeight));
}
