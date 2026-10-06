// Copyright WorldBLD LLC. All rights reserved.

#include "LandscapePaint/SWorldBLDLandscapePopulateDialog.h"

#include "ContextMenu/WorldBLDContextMenuStyle.h"
#include "LandscapePaint/WorldBLDLandscapePopulateOptions.h"

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

#define LOCTEXT_NAMESPACE "WorldBLD.LandscapePopulateDialog"

namespace WorldBLDLandscapePopulateDialogInternal
{
	static constexpr float DialogWidth = 880.0f;
	static constexpr float DialogHeight = 520.0f;
	static constexpr float SidebarWidth = 232.0f;
	static constexpr float ToolIconExtent = 128.0f;
}

void SWorldBLDLandscapePopulateDialog::Construct(
	const FArguments& InArgs,
	TSharedRef<SWindow> InOwningWindow,
	UWorldBLDLandscapePopulateOptions* InOptions)
{
	using namespace WorldBLDLandscapePopulateDialogInternal;

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
										.Image(this, &SWorldBLDLandscapePopulateDialog::GetToolIconBrush)
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
										"To use this mini-tool, choose a landscape actor and a LandBLD preset. The preset contains settings for paint layers and PCG content."))
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
											.Image(FAppStyle::GetBrush(TEXT("Icons.Settings")))
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
									.Text(LOCTEXT("SetupHeading", "Populate Setup"))
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
							.Text(LOCTEXT("CancelButton", "Cancel"))
							.OnClicked(this, &SWorldBLDLandscapePopulateDialog::OnCancelClicked)
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
							.Text(LOCTEXT("ContinueButton", "Continue"))
							.IsEnabled(this, &SWorldBLDLandscapePopulateDialog::CanContinue)
							.OnClicked(this, &SWorldBLDLandscapePopulateDialog::OnContinueClicked)
						]
					]
				]
			]
		]
	];
}

FReply SWorldBLDLandscapePopulateDialog::OnContinueClicked()
{
	bAccepted = true;
	if (OwningWindow.IsValid())
	{
		OwningWindow.Pin()->RequestDestroyWindow();
	}
	return FReply::Handled();
}

FReply SWorldBLDLandscapePopulateDialog::OnCancelClicked()
{
	bAccepted = false;
	if (OwningWindow.IsValid())
	{
		OwningWindow.Pin()->RequestDestroyWindow();
	}
	return FReply::Handled();
}

bool SWorldBLDLandscapePopulateDialog::CanContinue() const
{
	return IsValid(Options.Get()) && Options->CanContinue();
}

const FSlateBrush* SWorldBLDLandscapePopulateDialog::GetToolIconBrush() const
{
	return ToolIconBrush.Get();
}

#undef LOCTEXT_NAMESPACE
