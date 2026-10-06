// Copyright WorldBLD LLC. All rights reserved.

#include "UtilityBundleItemButtonWidget.h"
#include "WorldBLDEditController.h"
#include "Components/Button.h"
#include "Engine/Texture2D.h"

void UUtilityBundleItemButtonWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (ItemButton && !ItemButton->OnClicked.IsAlreadyBound(this, &UUtilityBundleItemButtonWidget::OnUtilityBundleButtonClicked))
	{
		ItemButton->OnClicked.AddDynamic(this, &UUtilityBundleItemButtonWidget::OnUtilityBundleButtonClicked);
		UE_LOG(LogTemp, Log, TEXT("UUtilityBundleItemButtonWidget::NativeConstruct - Bound OnClicked for widget '%s'"), *GetPathName());
	}
	else if (!ItemButton)
	{
		UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleItemButtonWidget::NativeConstruct - ItemButton is null for widget '%s'"), *GetPathName());
	}
}

void UUtilityBundleItemButtonWidget::SetUtilityBundle(UWorldBLDUtilityBundle* InBundleAsset)
{
	// Store the asset instance
	UtilityBundleAsset = InBundleAsset;
	
	// Set the item using the asset's class (for compatibility with base widget system)
	if (UtilityBundleAsset)
	{
		SetItem(UtilityBundleAsset->GetClass());
	}
}

UTexture2D* UUtilityBundleItemButtonWidget::GetThumbnailFromClass_Implementation(UClass* InClass)
{
	// Use the stored asset instance directly instead of trying to get CDO
	if (UtilityBundleAsset)
	{
		return UtilityBundleAsset->ToolImage;
	}
	return nullptr;
}

FText UUtilityBundleItemButtonWidget::GetTooltipTextFromClass_Implementation(UClass* InClass)
{
	// Use the stored asset instance directly instead of trying to get CDO
	if (UtilityBundleAsset && !UtilityBundleAsset->UtilityName.IsEmpty())
	{
		return UtilityBundleAsset->UtilityName;
	}
	return FText::GetEmpty();
}

void UUtilityBundleItemButtonWidget::OnUtilityBundleButtonClicked()
{
	UE_LOG(LogTemp, Log, TEXT("UUtilityBundleItemButtonWidget::OnUtilityBundleButtonClicked - Clicked widget '%s' (Bundle=%s, DelegateBound=%s)"),
		*GetPathName(),
		UtilityBundleAsset ? *UtilityBundleAsset->GetPathName() : TEXT("<null>"),
		OnUtilityBundleItemClicked.IsBound() ? TEXT("true") : TEXT("false"));

	if (OnUtilityBundleItemClicked.IsBound() && UtilityBundleAsset)
	{
		OnUtilityBundleItemClicked.Execute(UtilityBundleAsset);
		return;
	}

	UE_LOG(LogTemp, Warning, TEXT("UUtilityBundleItemButtonWidget::OnUtilityBundleButtonClicked - Did not execute delegate (Bundle=%s, DelegateBound=%s)"),
		UtilityBundleAsset ? TEXT("true") : TEXT("false"),
		OnUtilityBundleItemClicked.IsBound() ? TEXT("true") : TEXT("false"));
}

