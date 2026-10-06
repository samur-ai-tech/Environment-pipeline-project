// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

#include "AssetLibrary/WorldBLDAssetLibraryTypes.h"
#include "AssetLibrary/SWorldBLDAssetTile.h"
#include "AssetLibrary/SWorldBLDCollectionTile.h"

#include "Widgets/Layout/SScrollBox.h"

class SWrapBox;

DECLARE_DELEGATE(FOnWorldBLDViewAllKitsRequested);

class SWorldBLDAssetGrid : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDAssetGrid) {}
		SLATE_ARGUMENT(TArray<FWorldBLDAssetInfo>, Assets)
		SLATE_ARGUMENT(TArray<FWorldBLDKitInfo>, Kits)
		SLATE_ARGUMENT(TArray<FWorldBLDCollectionInfo>, Collections)
		SLATE_ARGUMENT(bool, bShowKits)
		SLATE_ARGUMENT(bool, bShowCollections)
		SLATE_EVENT(FOnWorldBLDAssetTileClicked, OnAssetClicked)
		SLATE_EVENT(FOnWorldBLDCollectionTileClicked, OnCollectionClicked)
		SLATE_EVENT(FOnWorldBLDViewAllKitsRequested, OnViewAllKitsRequested)
		SLATE_EVENT(FOnUserScrolled, OnUserScrolled)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;

	void RefreshGrid();
	void ScrollToTop();

	void SetAssets(const TArray<FWorldBLDAssetInfo>& InAssets);
	void SetKits(const TArray<FWorldBLDKitInfo>& InKits);
	void SetCollections(const TArray<FWorldBLDCollectionInfo>& InCollections);
	void SetHomeView(const TArray<FWorldBLDCollectionInfo>& InFeaturedKits, const TArray<FWorldBLDAssetInfo>& InAssets);

	/** Returns true if the user is close to the bottom of the scrollable content. */
	bool IsNearEnd(float CurrentScrollOffset, float RemainingThreshold = 300.0f) const;

private:
	void RefreshFeaturedKitsStrip();

	FReply HandleViewAllKitsClicked();
	FReply HandleFeaturedPrevClicked();
	FReply HandleFeaturedNextClicked();
	void ScrollFeaturedBy(float Delta);

	EVisibility GetFeaturedPrevVisibility() const;
	EVisibility GetFeaturedNextVisibility() const;

	bool CanShowFeaturedSection() const;
	float ComputeFilledTileWidth(float AvailableWidth, float MinTileWidth) const;
	float GetAssetTileSize() const;

	TSharedRef<SWidget> BuildFeaturedHeader();
	TSharedRef<SWidget> BuildFeaturedStrip();
	TSharedRef<SWidget> BuildSectionDivider();
	TSharedRef<SWidget> BuildLatestAssetsHeader();

private:
	TArray<FWorldBLDAssetInfo> Assets;
	TArray<FWorldBLDKitInfo> Kits;
	TArray<FWorldBLDCollectionInfo> Collections;
	TArray<FWorldBLDCollectionInfo> FeaturedKits;
	bool bShowKits = false;
	bool bShowCollections = false;
	bool bShowHome = false;

	FOnWorldBLDAssetTileClicked OnAssetClicked;
	FOnWorldBLDCollectionTileClicked OnCollectionClicked;
	FOnWorldBLDViewAllKitsRequested OnViewAllKitsRequested;
	FOnUserScrolled OnUserScrolled;

	TSharedPtr<SScrollBox> ScrollBox;
	TSharedPtr<SWrapBox> WrapBox;
	TSharedPtr<SScrollBox> FeaturedKitsScrollBox;

	static constexpr float AssetTileMinSize = 200.0f;
	static constexpr float GridSlotPadding = 10.0f;
	static constexpr float ScrollBarThickness = 14.0f;
	static constexpr float FeaturedKitTileWidth = 580.0f / 3.0f;
	static constexpr float FeaturedKitTileHeight = 869.0f / 3.0f;
	static constexpr float FeaturedKitTilePadding = 10.0f;

	float CachedTileWidth = AssetTileMinSize;
};
