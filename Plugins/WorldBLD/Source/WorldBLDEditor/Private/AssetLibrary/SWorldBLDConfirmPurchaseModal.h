// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

class SWorldBLDConfirmPurchaseModal : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDConfirmPurchaseModal)
		: _PriceCredits(0)
		, _bIsFree(false)
		, _UserCredits(0)
		, _PreviewBrush(nullptr)
	{
	}
		SLATE_ARGUMENT(FString, ItemName)
		SLATE_ARGUMENT(int32, PriceCredits)
		SLATE_ARGUMENT(bool, bIsFree)
		SLATE_ARGUMENT(int32, UserCredits)
		SLATE_ARGUMENT(const FSlateBrush*, PreviewBrush)
		SLATE_EVENT(FSimpleDelegate, OnConfirm)
		SLATE_EVENT(FSimpleDelegate, OnCancel)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	FReply HandleCancel();
	FReply HandleConfirm();
	bool CanConfirm() const;

	FString ItemName;
	int32 PriceCredits = 0;
	bool bIsFree = false;
	int32 UserCredits = 0;
	const FSlateBrush* PreviewBrush = nullptr;

	FSimpleDelegate OnConfirm;
	FSimpleDelegate OnCancel;
};
