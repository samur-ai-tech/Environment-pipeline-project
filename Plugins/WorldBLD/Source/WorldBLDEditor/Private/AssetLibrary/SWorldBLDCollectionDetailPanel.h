// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Misc/CoreDelegates.h"
#include "Widgets/SCompoundWidget.h"

#include "AssetLibrary/WorldBLDAssetLibraryTypes.h"

class SVerticalBox;
class SWorldBLDAssetLibraryDetailHeader;
class UWorldBLDAssetLibrarySubsystem;
class UWorldBLDAssetDownloadManager;
class UWorldBLDAuthSubsystem;

DECLARE_DELEGATE(FOnWorldBLDCollectionDetailBackRequested);
DECLARE_DELEGATE_OneParam(FOnWorldBLDCollectionViewAllAssets, const FWorldBLDCollectionInfo& /*Collection*/);

/**
 * Full-page kit/collection detail view for the WorldBLD Asset Library.
 * Shown in place of the kit grid when a kit tile is selected.
 */
class SWorldBLDCollectionDetailPanel : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDCollectionDetailPanel) {}
		SLATE_EVENT(FOnWorldBLDCollectionDetailBackRequested, OnBackRequested)
		SLATE_EVENT(FOnWorldBLDCollectionViewAllAssets, OnViewAllAssets)
	SLATE_END_ARGS()

	virtual ~SWorldBLDCollectionDetailPanel() override;

	void Construct(const FArguments& InArgs);

	void ShowCollection(const FWorldBLDCollectionInfo& Collection);
	void HandleCollectionDetailsFetched(const FWorldBLDCollectionDetailResponse& Response);
	void HandlePurchaseComplete(bool bSuccess, int32 RemainingCredits);
	void HandleAssetStatusChanged(const FString& AssetId, EWorldBLDAssetStatus NewStatus);
	void HandleImportComplete(const FString& AssetId, bool bSuccess);
	void HandleDownloadUrlFailed(const FString& ErrorMessage);

	bool IsPurchaseInProgress() const { return bPurchaseInProgress; }
	bool IsDownloadInProgress() const { return bDownloadInProgress; }
	bool IsImportInProgress() const { return bImportInProgress; }

private:
	EActiveTimerReturnType HandleCreditsRefreshTick(double CurrentTime, float DeltaTime);
	void RequestCreditsRefreshFromServer(bool bForce);
	void HandleApplicationHasReactivated();

	void HandleBackClicked();
	FReply HandlePurchaseClicked();
	FReply HandleDownloadClicked();
	FReply HandleImportClicked();
	FReply HandleViewAllAssetsClicked();

	void RefreshPreviewImages();
	void RefreshSpecsList();
	void RefreshIncludedBreakdown();
	void RebuildGalleryUrls();
	void ResetActionQueues();

	const FSlateBrush* GetCurrentPreviewBrush() const;

	FText GetTitleText() const;
	FText GetDescriptionText() const;
	FText GetPriceText() const;
	FText GetPurchaseButtonText() const;
	FText GetDownloadButtonText() const;
	FText GetImportButtonText() const;
	FText GetStatusText() const;
	FText GetViewAllAssetsText() const;

	int32 CountActiveCollectionAssets() const;
	int32 CountIncompatibleEngineAssets() const;
	EVisibility GetEngineCompatibilityWarningVisibility() const;
	FText GetEngineCompatibilityWarningText() const;

	EVisibility GetPurchaseButtonVisibility() const;
	EVisibility GetDownloadButtonVisibility() const;
	EVisibility GetImportButtonVisibility() const;
	EVisibility GetDownloadProgressVisibility() const;
	TOptional<float> GetDownloadProgressValue() const;
	EVisibility GetStatusTextVisibility() const;
	EVisibility GetPriceVisibility() const;

	bool HasSufficientCredits() const;
	bool HasActiveSubscription() const;
	bool IsAnyActionQueueRunning() const;
	bool IsCollectionAssetOwned(const FWorldBLDCollectionAsset& Asset) const;
	bool IsCollectionAssetEligible(const FWorldBLDCollectionAsset& Asset) const;
	bool IsFullyOwned() const;
	bool HasEligibleAssetsNeedingDownload() const;
	bool HasEligibleAssetsReadyToImport() const;
	EWorldBLDAssetStatus GetCollectionAssetStatus(const FWorldBLDCollectionAsset& Asset) const;
	EWorldBLDAssetStatus GetCollectionAggregateStatus() const;
	int32 GetUnownedCreditCost() const;
	void CollectUnownedAssetIds(TArray<FString>& OutAssetIds) const;
	void CollectDownloadableAssetIds(TArray<FString>& OutAssetIds) const;
	void CollectImportableAssetIds(TArray<FString>& OutAssetIds) const;

	void StartPurchaseQueue(const TArray<FString>& AssetIds);
	void PurchaseNextQueuedAsset();
	void FinishPurchaseQueue(bool bSuccess, const FString& ErrorMessage);

	void StartDownloadQueue(const TArray<FString>& AssetIds);
	void DownloadNextQueuedAsset();
	void AdvanceDownloadQueue(bool bCurrentSucceeded);
	void FinishDownloadQueue();

	void StartImportQueue(const TArray<FString>& AssetIds);
	void FinishImportQueue();
	void SyncContentBrowserToLastImportedAsset(const FString& AssetId);

	static void ShowInfoModal(const FText& Title, const FText& Message);

private:
	TWeakObjectPtr<UWorldBLDAssetLibrarySubsystem> AssetLibrarySubsystem;
	TWeakObjectPtr<UWorldBLDAssetDownloadManager> DownloadManager;
	TWeakObjectPtr<UWorldBLDAuthSubsystem> AuthSubsystem;

	FOnWorldBLDCollectionDetailBackRequested OnBackRequested;
	FOnWorldBLDCollectionViewAllAssets OnViewAllAssets;

	FWorldBLDCollectionInfo CurrentCollection;
	TArray<FWorldBLDCollectionAsset> CollectionAssets;
	bool bDetailsLoaded = false;

	TArray<FString> GalleryUrls;

	TSharedPtr<SWorldBLDAssetLibraryDetailHeader> DetailHeader;
	TSharedPtr<SVerticalBox> SpecsList;
	TSharedPtr<SVerticalBox> IncludedBreakdown;

	TArray<FString> PendingPurchaseAssetIds;
	int32 PurchaseQueueTotal = 0;
	int32 PurchaseQueueCompleted = 0;
	bool bPurchaseInProgress = false;

	TArray<FString> PendingDownloadAssetIds;
	FString CurrentDownloadAssetId;
	int32 DownloadQueueTotal = 0;
	int32 DownloadQueueCompleted = 0;
	int32 DownloadQueueSucceeded = 0;
	int32 DownloadQueueFailed = 0;
	bool bDownloadInProgress = false;
	bool bCurrentDownloadStarted = false;

	TArray<FString> PendingImportAssetIds;
	FString LastSuccessfulImportAssetId;
	int32 ImportQueueTotal = 0;
	int32 ImportQueueCompleted = 0;
	int32 ImportQueueSucceeded = 0;
	int32 ImportQueueFailed = 0;
	int32 ImportQueueSkipped = 0;
	bool bImportInProgress = false;

	TSharedPtr<FActiveTimerHandle> CreditsRefreshTimerHandle;
	FDelegateHandle ApplicationReactivatedHandle;
	double LastCreditsRefreshRequestTimeSeconds = -1.0;
	bool bPendingCreditsRefreshOnAppFocus = false;
	static constexpr float CreditsRefreshIntervalSeconds = 15.0f;
	static constexpr float CreditsRefreshMinGapSeconds = 2.0f;
};
