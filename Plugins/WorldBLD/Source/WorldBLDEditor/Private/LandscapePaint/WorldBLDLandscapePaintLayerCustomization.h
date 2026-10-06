#pragma once

#include "CoreMinimal.h"
#include "IPropertyTypeCustomization.h"

class FAssetThumbnail;
class IPropertyHandle;

class FWorldBLDLandscapePaintLayerCustomization : public IPropertyTypeCustomization
{
public:
	static TSharedRef<IPropertyTypeCustomization> MakeInstance();

	virtual void CustomizeHeader(
		TSharedRef<IPropertyHandle> StructPropertyHandle,
		class FDetailWidgetRow& HeaderRow,
		IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;

	virtual void CustomizeChildren(
		TSharedRef<IPropertyHandle> StructPropertyHandle,
		class IDetailChildrenBuilder& ChildBuilder,
		IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;

private:
	static void RefreshOuterOptions(TSharedRef<IPropertyHandle> StructPropertyHandle);
	static bool IsValidLayerInfo(TSharedRef<IPropertyHandle> LayerInfoHandle);
	static bool IsLayerSelected(TSharedRef<IPropertyHandle> SelectedHandle, TSharedRef<IPropertyHandle> LayerInfoHandle);
	static ECheckBoxState GetSelectedCheckState(TSharedRef<IPropertyHandle> SelectedHandle, TSharedRef<IPropertyHandle> LayerInfoHandle);
	static void OnSelectedChanged(ECheckBoxState NewState, TSharedRef<IPropertyHandle> SelectedHandle);
	static EVisibility GetErrorVisibility(TSharedRef<IPropertyHandle> ImportResultHandle);
	static FSlateColor GetErrorColor(TSharedRef<IPropertyHandle> ImportResultHandle);
	static FText GetErrorText(TSharedRef<IPropertyHandle> ErrorMessageHandle);
	static FReply OnBrowseLayerFileClicked(TSharedRef<IPropertyHandle> SourceFilePathHandle);

	TArray<TSharedPtr<FAssetThumbnail>> LayerThumbnails;
};
