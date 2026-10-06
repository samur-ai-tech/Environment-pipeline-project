// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Styling/SlateBrush.h"
#include "Types/SlateStructs.h"
#include "Widgets/SCompoundWidget.h"

#include "AssetLibrary/WorldBLDAssetLibraryTypes.h"

DECLARE_DELEGATE_RetVal_OneParam(FReply, FOnWorldBLDCollectionTileClicked, const FWorldBLDCollectionInfo& /*Collection*/);

struct FSlateDynamicImageBrush;

class SWorldBLDCollectionTile : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDCollectionTile) {}
		SLATE_ARGUMENT(FWorldBLDCollectionInfo, Collection)
		SLATE_ATTRIBUTE(float, TileWidth)
		SLATE_ATTRIBUTE(float, TileHeight)
		SLATE_EVENT(FOnWorldBLDCollectionTileClicked, OnClicked)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual void OnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual void OnMouseLeave(const FPointerEvent& MouseEvent) override;
	virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;

private:
	FReply HandleClicked();
	EVisibility GetHoverOutlineVisibility() const;
	const FSlateBrush* GetHoverOutlineBrush() const;
	const FSlateBrush* GetThumbnailBrush() const;
	FOptionalSize GetTileWidthOverride() const;
	FOptionalSize GetTileHeightOverride() const;

private:
	FWorldBLDCollectionInfo Collection;
	FOnWorldBLDCollectionTileClicked OnClicked;
	TAttribute<float> TileWidth;
	TAttribute<float> TileHeight;

	TSharedPtr<FSlateDynamicImageBrush> ThumbnailBrush;
	mutable FSlateBrush RoundedThumbnailBrush;
	bool bIsHovered = false;
};
