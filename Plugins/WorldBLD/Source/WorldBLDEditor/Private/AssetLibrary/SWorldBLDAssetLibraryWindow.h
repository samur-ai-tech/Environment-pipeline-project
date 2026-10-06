// Copyright WorldBLD LLC. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Input/SCheckBox.h"

#include "AssetLibrary/WorldBLDAssetLibraryTypes.h"
#include "AssetLibrary/WorldBLDAssetLibraryCategoryTypes.h"

#include "AssetLibrary/SWorldBLDAssetGrid.h"
#include "AssetLibrary/WorldBLDAssetLibrarySlateBridge.h"

class UWorldBLDAssetLibrarySubsystem;
class UWorldBLDAssetDownloadManager;
class UWorldBLDAuthSubsystem;
class SWorldBLDAssetDetailPanel;
class SWorldBLDCollectionDetailPanel;
class SWorldBLDAssetLibrarySearchBar;
class SWorldBLDCategoryTree;

class STextBlock;
class SButton;

class SWorldBLDAssetLibraryWindow : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDAssetLibraryWindow) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual ~SWorldBLDAssetLibraryWindow() override;
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;
	virtual void OnFocusChanging(const FWeakWidgetPath& PreviousFocusPath, const FWidgetPath& NewWidgetPath, const FFocusEvent& InFocusEvent) override;

	void RefreshAssetGrid();
	void SelectCategoryByPath(const FString& CategoryPath);

	void OnAssetsFetched(const FWorldBLDAssetListResponse& Response);
	void OnAssetCollectionNamesFetched(const FWorldBLDAssetCollectionNamesResponse& Response);
	void OnCollectionsFetched(const FWorldBLDCollectionListResponse& Response);
	void OnCollectionDetailsFetched(const FWorldBLDCollectionDetailResponse& Response);
	void OnAPIError(const FString& ErrorMessage);
	void OnAssetDetailsFetched(const FWorldBLDAssetInfo& AssetInfo);
	void OnPurchaseComplete(bool bSuccess, int32 RemainingCredits);
	void OnImportComplete(const FString& AssetId, bool bSuccess);
	void OnAssetStatusChanged(const FString& AssetId, EWorldBLDAssetStatus NewStatus);
	void OnSubscriptionStatusChanged(bool bIsKnown, bool bHasActiveSubscription);

private:
	void CollapseDetailPanel();
	bool IsNewFocusInSearchBar(const FWidgetPath& NewWidgetPath) const;

	void HandleCategorySelected(TSharedPtr<FWorldBLDCategoryNode> InCategory);
	void HandleSearchTextChanged(const FText& InText);
	void HandleFreeFilterChanged(ECheckBoxState NewState);
	FReply HandleAssetTileClicked(bool bIsKit, const FWorldBLDAssetInfo& AssetInfo, const FWorldBLDKitInfo& KitInfo);
	FReply HandleCollectionTileClicked(const FWorldBLDCollectionInfo& Collection);
	void HandleCollectionDetailBackRequested();
	void HandleCollectionViewAllAssets(const FWorldBLDCollectionInfo& Collection);
	void HandleViewAllKitsRequested();
	void HandleGridUserScrolled(float ScrollOffset);

	/**
	 * Resolves a list of stable PackageIds to full FWorldBLDAssetInfo objects from AllAssets.
	 * When bMissingOnly is true, only assets the user does not currently own are returned.
	 */
	TArray<FWorldBLDAssetInfo> ResolvePackageIdsToAssets(const TArray<FString>& PackageIds, bool bMissingOnly);

	/** Opens the detail panel for the asset matching PackageId and expands it. */
	void HandleNavigateToAsset(const FString& PackageId);

	void RefreshAssetList();
	void RequestAssetsPage(int32 Page);
	void RequestNextAssetsPage();
	void ResetInfiniteScroll();
	bool GrowVisibleItemWindow();
	bool HasActiveFilter() const;

	TArray<FWorldBLDAssetInfo> BuildVisibleAssets() const;
	TArray<FWorldBLDCollectionInfo> BuildVisibleCollections() const;
	TArray<FWorldBLDCollectionInfo> BuildFeaturedCollections() const;
	void ApplyFilters();
	void RebuildRightPanel();
	void CloseCollectionDetail();
	bool IsShowingCollectionDetail() const;
	bool IsHomeCategory() const;
	EVisibility GetAssetGridVisibility() const;
	EVisibility GetCollectionDetailVisibility() const;
	EVisibility GetLoadingVisibility() const;
	EVisibility GetErrorTextVisibility() const;

	FText GetLoginButtonText() const;
	FReply HandleLoginLogoutClicked();
	EVisibility GetNoResultsVisibility() const;

	FText GetCreditsOrPlanButtonText() const;
	FReply HandleCreditsOrPlanClicked();

private:
	TWeakObjectPtr<UWorldBLDAssetLibrarySubsystem> AssetLibrarySubsystem;
	TWeakObjectPtr<UWorldBLDAssetDownloadManager> DownloadManager;
	TWeakObjectPtr<UWorldBLDAuthSubsystem> AuthSubsystem;

	TStrongObjectPtr<UWorldBLDAssetLibrarySlateBridge> Bridge;

	TSharedPtr<SWorldBLDAssetLibrarySearchBar> SearchBar;
	TSharedPtr<SWorldBLDCategoryTree> CategoryTree;

	TSharedPtr<SWorldBLDAssetDetailPanel> DetailPanel;
	TSharedPtr<SWorldBLDCollectionDetailPanel> CollectionDetailPanel;
	TSharedPtr<SWorldBLDAssetGrid> AssetGrid;
	TSharedPtr<STextBlock> ErrorText;
	TSharedPtr<SButton> LoginLogoutButton;
	TSharedPtr<SButton> CreditsOrPlanButton;

	float CachedRightPanelHeight = 0.0f;

	TSharedPtr<FWorldBLDCategoryNode> CurrentCategory;
	FString CurrentSearchQuery;

	TArray<FWorldBLDAssetInfo> AllAssets;
	TArray<FWorldBLDAssetInfo> FilteredAssets;
	TArray<FWorldBLDCollectionInfo> AllCollections;
	TArray<FWorldBLDCollectionInfo> FilteredCollections;
	TArray<FString> AllCollectionNames;

	int32 AssetsCurrentPage = 1;
	int32 AssetsLastPage = 1;
	int32 RequestedAssetsPage = 1;

	int32 VisibleAssetsCount = 0;
	int32 VisibleCollectionsCount = 0;
	int32 AutoFetchBudget = 0;

	bool bShowOnlyFree = false;

	bool bIsLoading = false;
	bool bIsInitialLoadInProgress = false;

	// One-shot: when we programmatically select a category (ex: kit "View All" selecting Assets),
	// do not clear the search box, even if the target is Assets/Kits.
	bool bPreserveSearchOnNextCategorySelection = false;

	bool bShowingCollectionDetail = false;
};
