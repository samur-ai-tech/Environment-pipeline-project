// Copyright WorldBLD LLC. All rights reserved.

#include "LandscapePaint/WorldBLDLandscapePaintLayerCustomization.h"

#include "AssetThumbnail.h"
#include "DesktopPlatformModule.h"
#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "Framework/Application/SlateApplication.h"
#include "IDetailChildrenBuilder.h"
#include "IDesktopPlatform.h"
#include "IPropertyUtilities.h"
#include "LandscapeEditorModule.h"
#include "LandscapeEditorObject.h"
#include "LandscapePaint/WorldBLDLandscapePaintImportOptions.h"
#include "PropertyCustomizationHelpers.h"
#include "PropertyHandle.h"
#include "Widgets/Colors/SColorBlock.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Notifications/SErrorText.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WorldBLD.LandscapePaintLayerCustomization"

TSharedRef<IPropertyTypeCustomization> FWorldBLDLandscapePaintLayerCustomization::MakeInstance()
{
	return MakeShared<FWorldBLDLandscapePaintLayerCustomization>();
}

void FWorldBLDLandscapePaintLayerCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> StructPropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{
}

void FWorldBLDLandscapePaintLayerCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> StructPropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{
	const TSharedRef<IPropertyHandle> LayerNameHandle = StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FWorldBLDLandscapePaintLayer, LayerName)).ToSharedRef();
	const TSharedRef<IPropertyHandle> LayerInfoHandle = StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FWorldBLDLandscapePaintLayer, LayerInfo)).ToSharedRef();
	const TSharedRef<IPropertyHandle> SourceFilePathHandle = StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FWorldBLDLandscapePaintLayer, SourceFilePath)).ToSharedRef();
	const TSharedRef<IPropertyHandle> ThumbnailHandle = StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FWorldBLDLandscapePaintLayer, ThumbnailMIC)).ToSharedRef();
	const TSharedRef<IPropertyHandle> ImportResultHandle = StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FWorldBLDLandscapePaintLayer, ImportResult)).ToSharedRef();
	const TSharedRef<IPropertyHandle> ErrorMessageHandle = StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FWorldBLDLandscapePaintLayer, ErrorMessage)).ToSharedRef();
	const TSharedRef<IPropertyHandle> SelectedHandle = StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FWorldBLDLandscapePaintLayer, bSelected)).ToSharedRef();

	const TWeakPtr<IPropertyUtilities> PropertyUtilities = StructCustomizationUtils.GetPropertyUtilities();
	SourceFilePathHandle->SetOnPropertyValueChanged(FSimpleDelegate::CreateLambda([StructPropertyHandle, PropertyUtilities]()
	{
		RefreshOuterOptions(StructPropertyHandle);
		if (PropertyUtilities.IsValid())
		{
			PropertyUtilities.Pin()->ForceRefresh();
		}
	}));

	FName LayerName = NAME_None;
	LayerNameHandle->GetValue(LayerName);

	UObject* ThumbnailObject = nullptr;
	ThumbnailHandle->GetValue(ThumbnailObject);

	TSharedPtr<SWidget> ThumbnailWidget = SNew(SBox).WidthOverride(48.0f).HeightOverride(48.0f);
	if (StructCustomizationUtils.GetThumbnailPool().IsValid())
	{
		const TSharedPtr<FAssetThumbnail> LayerThumbnail = MakeShared<FAssetThumbnail>(
			ThumbnailObject != nullptr ? FAssetData(ThumbnailObject) : FAssetData(),
			48,
			48,
			StructCustomizationUtils.GetThumbnailPool().ToSharedRef());
		LayerThumbnails.Add(LayerThumbnail);

		FAssetThumbnailConfig ThumbnailConfig;
		ThumbnailConfig.bAllowRealTimeOnHovered = false;
		ThumbnailWidget = LayerThumbnail->MakeThumbnailWidget(ThumbnailConfig);
	}

	IDetailPropertyRow& LayerRow = ChildBuilder.AddProperty(SourceFilePathHandle);
	LayerRow.CustomWidget()
	.NameContent()
	[
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		.Padding(2.0f)
		[
			SNew(SCheckBox)
			.IsEnabled_Static(&FWorldBLDLandscapePaintLayerCustomization::IsValidLayerInfo, LayerInfoHandle)
			.IsChecked_Static(&FWorldBLDLandscapePaintLayerCustomization::GetSelectedCheckState, SelectedHandle, LayerInfoHandle)
			.OnCheckStateChanged_Static(&FWorldBLDLandscapePaintLayerCustomization::OnSelectedChanged, SelectedHandle)
		]
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		.Padding(2.0f)
		[
			SNew(SBox)
			.WidthOverride(48.0f)
			.HeightOverride(48.0f)
			[
				ThumbnailWidget.ToSharedRef()
			]
		]
		+ SHorizontalBox::Slot()
		.FillWidth(1.0f)
		.VAlign(VAlign_Center)
		.Padding(2.0f)
		[
			SNew(STextBlock)
			.Text(FText::FromName(LayerName))
		]
	]
	.ValueContent()
	.MinDesiredWidth(250.0f)
	.MaxDesiredWidth(0.0f)
	[
		SNew(SBox)
		.IsEnabled_Static(&FWorldBLDLandscapePaintLayerCustomization::IsLayerSelected, SelectedHandle, LayerInfoHandle)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(0.0f, 0.0f, 2.0f, 0.0f)
				[
					SNew(SErrorText)
					.Visibility_Static(&FWorldBLDLandscapePaintLayerCustomization::GetErrorVisibility, ImportResultHandle)
					.BackgroundColor_Static(&FWorldBLDLandscapePaintLayerCustomization::GetErrorColor, ImportResultHandle)
					.ErrorText(LOCTEXT("LayerErrorSymbol", "!"))
					.ToolTipText_Static(&FWorldBLDLandscapePaintLayerCustomization::GetErrorText, ErrorMessageHandle)
				]
				+ SHorizontalBox::Slot()
				[
					SourceFilePathHandle->CreatePropertyValueWidget()
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(1.0f, 0.0f, 0.0f, 0.0f)
				[
					SNew(SButton)
					.ContentPadding(FMargin(4.0f, 0.0f))
					.Text(LOCTEXT("BrowseButton", "..."))
					.OnClicked_Static(&FWorldBLDLandscapePaintLayerCustomization::OnBrowseLayerFileClicked, SourceFilePathHandle)
				]
			]
		]
	];
}

void FWorldBLDLandscapePaintLayerCustomization::RefreshOuterOptions(TSharedRef<IPropertyHandle> StructPropertyHandle)
{
	TArray<UObject*> OuterObjects;
	StructPropertyHandle->GetOuterObjects(OuterObjects);
	for (UObject* OuterObject : OuterObjects)
	{
		if (UWorldBLDLandscapePaintImportOptions* Options = Cast<UWorldBLDLandscapePaintImportOptions>(OuterObject))
		{
			Options->RefreshLayerImports();
		}
	}
}

bool FWorldBLDLandscapePaintLayerCustomization::IsValidLayerInfo(TSharedRef<IPropertyHandle> LayerInfoHandle)
{
	UObject* LayerInfo = nullptr;
	return LayerInfoHandle->GetValue(LayerInfo) != FPropertyAccess::Fail && LayerInfo != nullptr;
}

bool FWorldBLDLandscapePaintLayerCustomization::IsLayerSelected(TSharedRef<IPropertyHandle> SelectedHandle, TSharedRef<IPropertyHandle> LayerInfoHandle)
{
	if (!IsValidLayerInfo(LayerInfoHandle))
	{
		return false;
	}

	bool bSelected = false;
	return SelectedHandle->GetValue(bSelected) == FPropertyAccess::Success ? bSelected : false;
}

ECheckBoxState FWorldBLDLandscapePaintLayerCustomization::GetSelectedCheckState(TSharedRef<IPropertyHandle> SelectedHandle, TSharedRef<IPropertyHandle> LayerInfoHandle)
{
	return IsLayerSelected(SelectedHandle, LayerInfoHandle) ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
}

void FWorldBLDLandscapePaintLayerCustomization::OnSelectedChanged(ECheckBoxState NewState, TSharedRef<IPropertyHandle> SelectedHandle)
{
	SelectedHandle->SetValue(NewState == ECheckBoxState::Checked, EPropertyValueSetFlags::NotTransactable);
}

EVisibility FWorldBLDLandscapePaintLayerCustomization::GetErrorVisibility(TSharedRef<IPropertyHandle> ImportResultHandle)
{
	ELandscapeImportResult ImportResult = ELandscapeImportResult::Success;
	const FPropertyAccess::Result AccessResult = ImportResultHandle->GetValue((uint8&)ImportResult);
	if (AccessResult == FPropertyAccess::Fail || AccessResult == FPropertyAccess::MultipleValues)
	{
		return EVisibility::Visible;
	}

	return ImportResult == ELandscapeImportResult::Success ? EVisibility::Collapsed : EVisibility::Visible;
}

FSlateColor FWorldBLDLandscapePaintLayerCustomization::GetErrorColor(TSharedRef<IPropertyHandle> ImportResultHandle)
{
	ELandscapeImportResult ImportResult = ELandscapeImportResult::Success;
	const FPropertyAccess::Result AccessResult = ImportResultHandle->GetValue((uint8&)ImportResult);
	if (AccessResult == FPropertyAccess::Fail || AccessResult == FPropertyAccess::MultipleValues)
	{
		return FCoreStyle::Get().GetColor("ErrorReporting.BackgroundColor");
	}

	switch (ImportResult)
	{
	case ELandscapeImportResult::Warning:
		return FCoreStyle::Get().GetColor("ErrorReporting.WarningBackgroundColor");
	case ELandscapeImportResult::Error:
		return FCoreStyle::Get().GetColor("ErrorReporting.BackgroundColor");
	default:
		return FCoreStyle::Get().GetColor("InfoReporting.BackgroundColor");
	}
}

FText FWorldBLDLandscapePaintLayerCustomization::GetErrorText(TSharedRef<IPropertyHandle> ErrorMessageHandle)
{
	FText ErrorMessage;
	const FPropertyAccess::Result AccessResult = ErrorMessageHandle->GetValue(ErrorMessage);
	if (AccessResult == FPropertyAccess::Fail)
	{
		return LOCTEXT("UnknownError", "Unknown error");
	}
	if (AccessResult == FPropertyAccess::MultipleValues)
	{
		return NSLOCTEXT("PropertyEditor", "MultipleValues", "Multiple Values");
	}

	return ErrorMessage;
}

FReply FWorldBLDLandscapePaintLayerCustomization::OnBrowseLayerFileClicked(TSharedRef<IPropertyHandle> SourceFilePathHandle)
{
	ILandscapeEditorModule& LandscapeEditorModule = FModuleManager::LoadModuleChecked<ILandscapeEditorModule>(TEXT("LandscapeEditor"));
	const FString DialogTypeString = LandscapeEditorModule.GetWeightmapImportDialogTypeString();

	IDesktopPlatform* DesktopPlatform = FDesktopPlatformModule::Get();
	if (DesktopPlatform == nullptr)
	{
		return FReply::Handled();
	}

	TArray<FString> OpenedFiles;
	const void* ParentWindowHandle = FSlateApplication::Get().FindBestParentWindowHandleForDialogs(nullptr);
	const bool bPicked = DesktopPlatform->OpenFileDialog(
		ParentWindowHandle,
		LOCTEXT("ImportLayer", "Import Layer").ToString(),
		FString(),
		FString(),
		DialogTypeString,
		EFileDialogFlags::None,
		OpenedFiles);
	if (bPicked && OpenedFiles.Num() > 0 && !OpenedFiles[0].IsEmpty())
	{
		SourceFilePathHandle->SetValue(OpenedFiles[0]);
	}

	return FReply::Handled();
}

#undef LOCTEXT_NAMESPACE
