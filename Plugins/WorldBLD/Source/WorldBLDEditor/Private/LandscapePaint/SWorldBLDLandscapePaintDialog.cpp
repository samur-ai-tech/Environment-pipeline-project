// Copyright WorldBLD LLC. All rights reserved.

#include "LandscapePaint/SWorldBLDLandscapePaintDialog.h"

#include "ContextMenu/WorldBLDContextMenuStyle.h"
#include "LandscapePaint/WorldBLDLandscapePaintImportOptions.h"

#include "Brushes/SlateColorBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "HAL/FileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "PropertyEditorModule.h"
#include "Styling/AppStyle.h"
#include "Styling/CoreStyle.h"
#include "Styling/StyleColors.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SWindow.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WorldBLD.LandscapePaintDialog"

namespace WorldBLDLandscapePaintDialogInternal
{
	static constexpr float DialogWidth = 880.0f;
	static constexpr float DialogHeight = 620.0f;
	static constexpr float SidebarWidth = 232.0f;
	static constexpr float ToolIconExtent = 128.0f;
}

void SWorldBLDLandscapePaintDialog::Construct(
	const FArguments& InArgs,
	TSharedRef<SWindow> InOwningWindow,
	UWorldBLDLandscapePaintImportOptions* InOptions)
{
	using namespace WorldBLDLandscapePaintDialogInternal;

	OwningWindow = InOwningWindow;
	Options = InOptions;

	FPropertyEditorModule& PropertyEditorModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>(TEXT("PropertyEditor"));

	FDetailsViewArgs DetailsViewArgs;
	DetailsViewArgs.bAllowSearch = false;
	DetailsViewArgs.bHideSelectionTip = true;
	DetailsViewArgs.bLockable = false;
	DetailsViewArgs.bShowObjectLabel = false;
	DetailsViewArgs.bUpdatesFromSelection = false;
	DetailsViewArgs.NameAreaSettings = FDetailsViewArgs::HideNameArea;

	DetailsView = PropertyEditorModule.CreateDetailView(DetailsViewArgs);
	DetailsView->SetObject(Options.Get());

	if (const TSharedPtr<IPlugin> WorldBLDPlugin = IPluginManager::Get().FindPlugin(TEXT("WorldBLD")))
	{
		FString IconPath = FPaths::ConvertRelativePathToFull(
			WorldBLDPlugin->GetBaseDir() / TEXT("Resources/LandBLD128x128.JPG"));
		if (IFileManager::Get().FileExists(*IconPath))
		{
			ToolIconBrush = MakeShared<FSlateDynamicImageBrush>(
				FName(*IconPath),
				FVector2D(ToolIconExtent, ToolIconExtent));
		}
	}

	const FVector4 PanelRadii(8.0f, 8.0f, 8.0f, 8.0f);
	PanelBrush = MakeShared<FSlateRoundedBoxBrush>(FStyleColors::Background, PanelRadii);
	SidebarBrush = MakeShared<FSlateRoundedBoxBrush>(
		FStyleColors::Recessed,
		FVector4(8.0f, 0.0f, 0.0f, 0.0f));
	FooterBrush = MakeShared<FSlateRoundedBoxBrush>(
		FStyleColors::Background,
		FVector4(0.0f, 0.0f, 8.0f, 8.0f));
	IconWellBrush = MakeShared<FSlateRoundedBoxBrush>(
		FStyleColors::Header,
		FVector4(4.0f, 4.0f, 4.0f, 4.0f));
	AccentBrush = MakeShared<FSlateColorBrush>(WorldBLDContextMenuStyle::GetHighlightRedColor());

	{
		const FVector4 CardRadii(5.0f, 5.0f, 5.0f, 5.0f);
		FSlateBrushOutlineSettings CardOutline;
		CardOutline.CornerRadii = CardRadii;
		CardOutline.Color = FStyleColors::DropdownOutline;
		CardOutline.Width = 1.0f;
		CardOutline.RoundingType = ESlateBrushRoundingType::FixedRadius;
		CardOutline.bUseBrushTransparency = false;

		TSharedPtr<FSlateRoundedBoxBrush> RoundedCardBrush =
			MakeShared<FSlateRoundedBoxBrush>(FStyleColors::Recessed, CardRadii);
		RoundedCardBrush->OutlineSettings = CardOutline;
		CardBrush = RoundedCardBrush;
	}

	ChildSlot
	[
		SNew(SBox)
		.WidthOverride(DialogWidth)
		.HeightOverride(DialogHeight)
		[
			SNew(SBorder)
			.BorderImage(PanelBrush.Get())
			.Padding(0.0f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.FillHeight(1.0f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						SNew(SBox)
						.WidthOverride(SidebarWidth)
						[
							SNew(SBorder)
							.BorderImage(SidebarBrush.Get())
							.Padding(FMargin(28.0f, 28.0f, 24.0f, 24.0f))
							[
								SNew(SVerticalBox)
								+ SVerticalBox::Slot()
								.AutoHeight()
								.HAlign(HAlign_Center)
								[
									SNew(SBox)
									.WidthOverride(ToolIconExtent)
									.HeightOverride(ToolIconExtent)
									.Visibility_Lambda([this]()
									{
										return ToolIconBrush.IsValid()
											? EVisibility::Visible
											: EVisibility::Collapsed;
									})
									[
										SNew(SImage)
										.Image(this, &SWorldBLDLandscapePaintDialog::GetToolIconBrush)
									]
								]
								+ SVerticalBox::Slot()
								.AutoHeight()
								.Padding(FMargin(0.0f, 38.0f, 0.0f, 0.0f))
								[
									SNew(STextBlock)
									.Text(LOCTEXT("SidebarTitle", "LandBLD"))
									.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 22))
								]
								+ SVerticalBox::Slot()
								.AutoHeight()
								.Padding(FMargin(0.0f, 12.0f, 0.0f, 16.0f))
								[
									SNew(SBox)
									.HeightOverride(2.0f)
									[
										SNew(SBorder)
										.BorderImage(AccentBrush.Get())
									]
								]
								+ SVerticalBox::Slot()
								.AutoHeight()
								[
									SNew(STextBlock)
									.Text(LOCTEXT(
										"SidebarDescription",
										"Select which landscape paint layers to import from mask files, then choose Import to apply them."))
									.AutoWrapText(true)
									.ColorAndOpacity(FSlateColor::UseSubduedForeground())
									.LineHeightPercentage(1.15f)
								]
							]
						]
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					[
						SNew(SBorder)
						.BorderImage(FAppStyle::GetBrush(TEXT("NoBorder")))
						.Padding(FMargin(24.0f, 24.0f, 24.0f, 20.0f))
						[
							SNew(SVerticalBox)
							+ SVerticalBox::Slot()
							.AutoHeight()
							[
								SNew(SHorizontalBox)
								+ SHorizontalBox::Slot()
								.AutoWidth()
								[
									SNew(SBox)
									.WidthOverride(48.0f)
									.HeightOverride(48.0f)
									[
										SNew(SBorder)
										.BorderImage(IconWellBrush.Get())
										.HAlign(HAlign_Center)
										.VAlign(VAlign_Center)
										[
											SNew(SImage)
											.Image(FAppStyle::GetBrush(TEXT("Icons.Import")))
											.DesiredSizeOverride(FVector2D(24.0f, 24.0f))
										]
									]
								]
								+ SHorizontalBox::Slot()
								.AutoWidth()
								.VAlign(VAlign_Center)
								.Padding(FMargin(16.0f, 0.0f))
								[
									SNew(STextBlock)
									.Text(LOCTEXT("ImportSettingsHeading", "Import Settings"))
									.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 14))
								]
							]
							+ SVerticalBox::Slot()
							.FillHeight(1.0f)
							.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
							[
								SNew(SBorder)
								.BorderImage(CardBrush.Get())
								.Padding(FMargin(18.0f, 13.0f))
								[
									DetailsView.ToSharedRef()
								]
							]
						]
					]
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(SBorder)
					.BorderImage(FooterBrush.Get())
					.Padding(FMargin(24.0f, 14.0f))
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot()
						.AutoWidth()
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.Text(LOCTEXT("SkipButton", "Skip Layer Import"))
							.OnClicked(this, &SWorldBLDLandscapePaintDialog::OnCancelClicked)
						]
						+ SHorizontalBox::Slot()
						.FillWidth(1.0f)
						[
							SNew(SSpacer)
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						[
							SNew(SButton)
							.ButtonStyle(&WorldBLDContextMenuStyle::GetToolSwitchMenuInstallButtonStyle())
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							.Text(LOCTEXT("ImportButton", "Import"))
							.IsEnabled(this, &SWorldBLDLandscapePaintDialog::CanImport)
							.OnClicked(this, &SWorldBLDLandscapePaintDialog::OnImportClicked)
						]
					]
				]
			]
		]
	];
}

FReply SWorldBLDLandscapePaintDialog::OnImportClicked()
{
	bAccepted = true;
	if (OwningWindow.IsValid())
	{
		OwningWindow.Pin()->RequestDestroyWindow();
	}
	return FReply::Handled();
}

FReply SWorldBLDLandscapePaintDialog::OnCancelClicked()
{
	bAccepted = false;
	if (OwningWindow.IsValid())
	{
		OwningWindow.Pin()->RequestDestroyWindow();
	}
	return FReply::Handled();
}

bool SWorldBLDLandscapePaintDialog::CanImport() const
{
	return IsValid(Options.Get()) && Options->HasAnySelectedLayers();
}

const FSlateBrush* SWorldBLDLandscapePaintDialog::GetToolIconBrush() const
{
	return ToolIconBrush.Get();
}

#undef LOCTEXT_NAMESPACE
