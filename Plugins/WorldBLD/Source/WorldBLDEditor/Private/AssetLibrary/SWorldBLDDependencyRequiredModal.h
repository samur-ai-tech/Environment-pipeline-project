// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "AssetLibrary/WorldBLDAssetLibraryTypes.h"

DECLARE_DELEGATE_OneParam(FOnWorldBLDNavigateToDependency, const FString& /*PackageId*/);

/**
 * Modal dialog shown when an asset has unowned external package dependencies.
 *
 * Shows each missing dependency as a clickable SWorldBLDAssetTile in a WrapBox so the user
 * can open any dependency directly in the asset library to view or purchase it.
 *
 * Two actions are offered:
 *   - "Go Back"                         : dismisses the dialog without taking action.
 *   - "Get All Required Assets (X Credits)" : purchases all missing dependencies at once.
 *     The button is disabled when the user does not have enough credits to cover the total cost.
 */
class SWorldBLDDependencyRequiredModal : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDDependencyRequiredModal) {}
		/** Full FWorldBLDAssetInfo for every dependency the user has not yet purchased. */
		SLATE_ARGUMENT(TArray<FWorldBLDAssetInfo>, MissingDependencies)
		/** Sum of CreditsPrice across all missing dependencies. */
		SLATE_ARGUMENT(int32, TotalCreditsCost)
		/** User's current credit balance (used to gate the purchase-all button). */
		SLATE_ARGUMENT(int32, UserCredits)
		/** Fired when the user clicks a dependency tile; caller should navigate to that PackageId. */
		SLATE_EVENT(FOnWorldBLDNavigateToDependency, OnNavigateToDependency)
		/** Fired when the user clicks "Go Back"; caller should close the modal window. */
		SLATE_EVENT(FSimpleDelegate, OnGoBack)
		/** Fired when the user clicks "Get All Required Assets"; caller should purchase all deps. */
		SLATE_EVENT(FSimpleDelegate, OnPurchaseAll)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	FReply HandleGoBack();
	FReply HandlePurchaseAll();
	bool CanPurchaseAll() const;

private:
	TArray<FWorldBLDAssetInfo> MissingDependencies;
	int32 TotalCreditsCost = 0;
	int32 UserCredits = 0;

	FOnWorldBLDNavigateToDependency OnNavigateToDependency;
	FSimpleDelegate OnGoBack;
	FSimpleDelegate OnPurchaseAll;
};
