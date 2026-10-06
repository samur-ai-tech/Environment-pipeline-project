// Copyright WorldBLD LLC. All rights reserved.

#include "Resources/SWorldBLDResourcesDialog.h"

#include "AssetLibrary/WorldBLDAssetLibraryWindow.h"
#include "ContextMenu/WorldBLDContextMenuFont.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"
#include "WorldBLDEditorToolkit.h"

#include "Brushes/SlateColorBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "InputCoreTypes.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "Styling/AppStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SWindow.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WorldBLDResourcesDialog"

namespace WorldBLDResourcesDialogLocal
{
	static const TCHAR* DocsUrl = TEXT("https://worldbld.notion.site/WorldBLD-Documentation-Home-29a1ba824a30813ab7f2ce4399672dc4");
	static const TCHAR* YouTubeUrl = TEXT("https://www.youtube.com/@WorldBLD");

	static constexpr float DialogWidth = 520.0f;
	static constexpr float RowIconExtent = 20.0f;
	static constexpr float HeaderIconExtent = 28.0f;
	static constexpr float TrailingIconExtent = 14.0f;
	static constexpr float CloseIconExtent = 14.0f;
	static constexpr float AccentBarWidth = 3.0f;

	static TWeakPtr<SWindow> ActiveWindow;

	static const FLinearColor& GetPanelColor()
	{
		static const FLinearColor Color(0.045f, 0.045f, 0.045f, 1.0f);
		return Color;
	}

	static const FLinearColor& GetFooterColor()
	{
		static const FLinearColor Color(0.030f, 0.030f, 0.030f, 1.0f);
		return Color;
	}

	static const FLinearColor& GetRowColor()
	{
		static const FLinearColor Color(0.085f, 0.085f, 0.085f, 1.0f);
		return Color;
	}

	static const FLinearColor& GetRowHoveredColor()
	{
		static const FLinearColor Color(0.115f, 0.115f, 0.115f, 1.0f);
		return Color;
	}

	static const FLinearColor& GetIconWellColor()
	{
		static const FLinearColor Color(0.055f, 0.055f, 0.055f, 1.0f);
		return Color;
	}

	static const FLinearColor& GetSubtitleColor()
	{
		static const FLinearColor Color(0.55f, 0.55f, 0.55f, 1.0f);
		return Color;
	}

	static const FLinearColor& GetFooterTextColor()
	{
		static const FLinearColor Color(0.45f, 0.45f, 0.45f, 1.0f);
		return Color;
	}

	static TSharedPtr<FSlateDynamicImageBrush> MakeResourceIconBrush(const TCHAR* RelativeResourcePath, const FVector2D& Size)
	{
		const TSharedPtr<IPlugin> WorldBLDPlugin = IPluginManager::Get().FindPlugin(TEXT("WorldBLD"));
		if (!WorldBLDPlugin.IsValid())
		{
			return nullptr;
		}

		const FString FullPath = FPaths::ConvertRelativePathToFull(WorldBLDPlugin->GetBaseDir() / RelativeResourcePath);
		if (!IFileManager::Get().FileExists(*FullPath))
		{
			return nullptr;
		}

		return MakeShared<FSlateDynamicImageBrush>(FName(*FullPath), Size);
	}

	static const FSlateBrush* GetAppIcon(const TCHAR* BrushName)
	{
		return FAppStyle::Get().GetBrush(BrushName);
	}
}

void SWorldBLDResourcesDialog::Construct(const FArguments& InArgs)
{
	using namespace WorldBLDResourcesDialogLocal;

	YouTubeIconBrush = MakeResourceIconBrush(TEXT("Resources/Icon_youtube-app-white-icon.png"), FVector2D(RowIconExtent, RowIconExtent));
	CloseIconBrush = MakeResourceIconBrush(TEXT("Resources/Icon_x_exit.PNG"), FVector2D(CloseIconExtent, CloseIconExtent));

	const FVector4 CornerRadii(8.0f, 8.0f, 8.0f, 8.0f);
	const FVector4 IconWellRadii(4.0f, 4.0f, 4.0f, 4.0f);

	PanelBrush = MakeShared<FSlateRoundedBoxBrush>(GetPanelColor(), CornerRadii);
	FooterBrush = MakeShared<FSlateRoundedBoxBrush>(GetFooterColor(), FVector4(0.0f, 0.0f, 8.0f, 8.0f));
	IconWellBrush = MakeShared<FSlateRoundedBoxBrush>(GetIconWellColor(), IconWellRadii);
	RowAccentBrush = MakeShared<FSlateColorBrush>(WorldBLDContextMenuStyle::GetHighlightRedColor());

	{
		const FVector4 OutlineRadii(6.0f, 6.0f, 6.0f, 6.0f);
		FSlateBrushOutlineSettings RowOutline;
		RowOutline.CornerRadii = OutlineRadii;
		RowOutline.Color = FSlateColor(FLinearColor(0.12f, 0.12f, 0.12f, 1.0f));
		RowOutline.Width = 1.0f;
		RowOutline.RoundingType = ESlateBrushRoundingType::FixedRadius;
		RowOutline.bUseBrushTransparency = false;

		auto MakeRowBrush = [&RowOutline, &OutlineRadii](const FLinearColor& Color) -> FSlateRoundedBoxBrush
		{
			FSlateRoundedBoxBrush Brush(Color, OutlineRadii);
			Brush.OutlineSettings = RowOutline;
			return Brush;
		};

		RowButtonStyle = MakeShared<FButtonStyle>();
		RowButtonStyle->SetNormal(MakeRowBrush(GetRowColor()))
			.SetHovered(MakeRowBrush(GetRowHoveredColor()))
			.SetPressed(MakeRowBrush(GetRowHoveredColor()))
			.SetDisabled(MakeRowBrush(GetRowColor()))
			.SetNormalPadding(FMargin(0.0f))
			.SetPressedPadding(FMargin(0.0f));
	}

	{
		const FVector4 OutlineRadii(4.0f, 4.0f, 4.0f, 4.0f);
		FSlateBrushOutlineSettings Outline;
		Outline.CornerRadii = OutlineRadii;
		Outline.Color = FSlateColor(FLinearColor(0.55f, 0.55f, 0.55f, 1.0f));
		Outline.Width = 1.0f;
		Outline.RoundingType = ESlateBrushRoundingType::FixedRadius;
		Outline.bUseBrushTransparency = false;

		auto MakeOutlineBrush = [&Outline, &OutlineRadii](const FLinearColor& Fill) -> FSlateRoundedBoxBrush
		{
			FSlateRoundedBoxBrush Brush(Fill, OutlineRadii);
			Brush.OutlineSettings = Outline;
			return Brush;
		};

		CheckUpdatesButtonStyle = MakeShared<FButtonStyle>();
		CheckUpdatesButtonStyle->SetNormal(MakeOutlineBrush(FLinearColor(0.06f, 0.06f, 0.06f, 1.0f)))
			.SetHovered(MakeOutlineBrush(FLinearColor(0.10f, 0.10f, 0.10f, 1.0f)))
			.SetPressed(MakeOutlineBrush(FLinearColor(0.08f, 0.08f, 0.08f, 1.0f)))
			.SetDisabled(MakeOutlineBrush(FLinearColor(0.06f, 0.06f, 0.06f, 1.0f)))
			.SetNormalPadding(FMargin(10.0f, 6.0f))
			.SetPressedPadding(FMargin(10.0f, 6.0f));
	}

	const FSlateBrush* DocsIcon = GetAppIcon(TEXT("Icons.Documentation"));
	const FSlateBrush* DemoIcon = GetAppIcon(TEXT("Icons.Level"));
	const FSlateBrush* PresetsIcon = GetAppIcon(TEXT("Icons.PlaceActors"));
	const FSlateBrush* ExternalIcon = GetAppIcon(TEXT("Icons.OpenInBrowser"));
	const FSlateBrush* ChevronIcon = GetAppIcon(TEXT("Icons.ChevronRight"));
	const FSlateBrush* InfoIcon = GetAppIcon(TEXT("Icons.Info"));
	const FSlateBrush* GlobeIcon = GetAppIcon(TEXT("Icons.World"));
	const FSlateBrush* HeaderBookIcon = DocsIcon != nullptr ? DocsIcon : GetAppIcon(TEXT("Icons.Help"));

	ChildSlot
	[
		SNew(SBox)
		.WidthOverride(DialogWidth)
		[
			SNew(SBorder)
			.BorderImage(PanelBrush.Get())
			.Padding(0.0f)
			[
				SNew(SVerticalBox)

				// Header
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(20.0f, 18.0f, 16.0f, 8.0f))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.VAlign(VAlign_Top)
					.Padding(FMargin(0.0f, 2.0f, 14.0f, 0.0f))
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot()
						.AutoHeight()
						[
							SNew(SBox)
							.WidthOverride(HeaderIconExtent)
							.HeightOverride(HeaderIconExtent)
							[
								SNew(SImage)
								.Image(HeaderBookIcon)
								.ColorAndOpacity(WorldBLDContextMenuStyle::GetHighlightRedColor())
							]
						]
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(FMargin(0.0f, 6.0f, 0.0f, 0.0f))
						[
							SNew(SBox)
							.HeightOverride(2.0f)
							.WidthOverride(HeaderIconExtent)
							[
								SNew(SBorder)
								.BorderImage(RowAccentBrush.Get())
								.BorderBackgroundColor(WorldBLDContextMenuStyle::GetHighlightRedColor())
							]
						]
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.VAlign(VAlign_Center)
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot()
						.AutoHeight()
						[
							SNew(STextBlock)
							.Text(LOCTEXT("Title", "WorldBLD Resources"))
							.Font(WorldBLDContextMenuFont::GetMedium(16.0f, 0))
							.ColorAndOpacity(FLinearColor::White)
						]
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(FMargin(0.0f, 4.0f, 0.0f, 0.0f))
						[
							SNew(STextBlock)
							.Text(LOCTEXT("Subtitle", "Learn, explore, and get the most out of WorldBLD"))
							.Font(WorldBLDContextMenuFont::GetMedium(10.0f, 0))
							.ColorAndOpacity(GetSubtitleColor())
							.AutoWrapText(true)
						]
					]
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.VAlign(VAlign_Top)
					[
						SNew(SButton)
						.ButtonStyle(FAppStyle::Get(), "SimpleButton")
						.ContentPadding(FMargin(4.0f))
						.OnClicked(this, &SWorldBLDResourcesDialog::HandleCloseClicked)
						.ToolTipText(LOCTEXT("CloseTooltip", "Close"))
						[
							SNew(SBox)
							.WidthOverride(CloseIconExtent)
							.HeightOverride(CloseIconExtent)
							[
								SNew(SImage)
								.Image(CloseIconBrush.IsValid() ? CloseIconBrush.Get() : GetAppIcon(TEXT("Icons.X")))
								.ColorAndOpacity(FLinearColor(0.75f, 0.75f, 0.75f, 1.0f))
							]
						]
					]
				]

				// Rows
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(16.0f, 8.0f, 16.0f, 4.0f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 0.0f, 0.0f, 8.0f))
					[
						BuildResourceRow(
							LOCTEXT("DocsTitle", "Online Documentation"),
							LOCTEXT("DocsSubtitle", "Open the WorldBLD documentation website"),
							DocsIcon,
							ExternalIcon,
							FLinearColor::White,
							FSimpleDelegate::CreateLambda([this]() { HandleDocsClicked(); }))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 0.0f, 0.0f, 8.0f))
					[
						BuildResourceRow(
							LOCTEXT("YouTubeTitle", "WorldBLD YouTube Channel"),
							LOCTEXT("YouTubeSubtitle", "Tutorials, tips, and feature showcases"),
							YouTubeIconBrush.IsValid() ? YouTubeIconBrush.Get() : GetAppIcon(TEXT("Icons.Video")),
							ExternalIcon,
							FLinearColor::White,
							FSimpleDelegate::CreateLambda([this]() { HandleYouTubeClicked(); }))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 0.0f, 0.0f, 8.0f))
					[
						BuildResourceRow(
							LOCTEXT("DemoTitle", "Open Demo Map"),
							LOCTEXT("DemoSubtitle", "Open the WorldBLD demo map in a new level"),
							DemoIcon,
							ChevronIcon,
							FLinearColor::White,
							FSimpleDelegate::CreateLambda([this]() { HandleDemoMapClicked(); }))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						BuildResourceRow(
							LOCTEXT("PresetsTitle", "Browse Example Presets"),
							LOCTEXT("PresetsSubtitle", "Explore and apply example presets"),
							PresetsIcon,
							ChevronIcon,
							FLinearColor::White,
							FSimpleDelegate::CreateLambda([this]() { HandleBrowsePresetsClicked(); }))
					]
				]

				// Footer
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 12.0f, 0.0f, 0.0f))
				[
					SNew(SBorder)
					.BorderImage(FooterBrush.Get())
					.Padding(FMargin(16.0f, 12.0f))
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot()
						.FillWidth(1.0f)
						.VAlign(VAlign_Center)
						[
							SNew(SHorizontalBox)
							+ SHorizontalBox::Slot()
							.AutoWidth()
							.VAlign(VAlign_Center)
							.Padding(FMargin(0.0f, 0.0f, 8.0f, 0.0f))
							[
								SNew(SBox)
								.WidthOverride(14.0f)
								.HeightOverride(14.0f)
								[
									SNew(SImage)
									.Image(InfoIcon)
									.ColorAndOpacity(GetFooterTextColor())
								]
							]
							+ SHorizontalBox::Slot()
							.FillWidth(1.0f)
							.VAlign(VAlign_Center)
							[
								SNew(STextBlock)
								.Text(LOCTEXT("FooterHint", "Stay up to date with the latest resources and updates."))
								.Font(WorldBLDContextMenuFont::GetMedium(9.0f, 0))
								.ColorAndOpacity(GetFooterTextColor())
								.AutoWrapText(true)
							]
						]
						+ SHorizontalBox::Slot()
						.AutoWidth()
						.VAlign(VAlign_Center)
						.Padding(FMargin(12.0f, 0.0f, 0.0f, 0.0f))
						[
							SNew(SButton)
							.ButtonStyle(CheckUpdatesButtonStyle.Get())
							.OnClicked(this, &SWorldBLDResourcesDialog::HandleCheckForUpdatesClicked)
							.ToolTipText(LOCTEXT("CheckUpdatesTooltip", "Refresh tools from the server and notify if an update is available"))
							[
								SNew(SHorizontalBox)
								+ SHorizontalBox::Slot()
								.AutoWidth()
								.VAlign(VAlign_Center)
								.Padding(FMargin(0.0f, 0.0f, 6.0f, 0.0f))
								[
									SNew(SBox)
									.WidthOverride(14.0f)
									.HeightOverride(14.0f)
									[
										SNew(SImage)
										.Image(GlobeIcon)
										.ColorAndOpacity(FLinearColor::White)
									]
								]
								+ SHorizontalBox::Slot()
								.AutoWidth()
								.VAlign(VAlign_Center)
								[
									SNew(STextBlock)
									.Text(LOCTEXT("CheckUpdates", "Check for Updates"))
									.Font(WorldBLDContextMenuFont::GetMedium(10.0f, 0))
									.ColorAndOpacity(FLinearColor::White)
								]
							]
						]
					]
				]
			]
		]
	];
}

TSharedRef<SWidget> SWorldBLDResourcesDialog::BuildResourceRow(
	const FText& Title,
	const FText& Subtitle,
	const FSlateBrush* LeadingIcon,
	const FSlateBrush* TrailingIcon,
	FLinearColor LeadingIconTint,
	const FSimpleDelegate& OnClicked)
{
	using namespace WorldBLDResourcesDialogLocal;

	return SNew(SButton)
		.ButtonStyle(RowButtonStyle.Get())
		.ContentPadding(FMargin(0.0f))
		.OnClicked_Lambda([OnClicked]()
		{
			OnClicked.ExecuteIfBound();
			return FReply::Handled();
		})
		[
			SNew(SOverlay)
			+ SOverlay::Slot()
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SBox)
					.WidthOverride(AccentBarWidth)
					[
						SNew(SBorder)
						.BorderImage(RowAccentBrush.Get())
						.BorderBackgroundColor(WorldBLDContextMenuStyle::GetHighlightRedColor())
					]
				]
				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.Padding(FMargin(12.0f, 12.0f, 14.0f, 12.0f))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.VAlign(VAlign_Center)
					.Padding(FMargin(0.0f, 0.0f, 12.0f, 0.0f))
					[
						SNew(SBorder)
						.BorderImage(IconWellBrush.Get())
						.Padding(FMargin(8.0f))
						[
							SNew(SBox)
							.WidthOverride(RowIconExtent)
							.HeightOverride(RowIconExtent)
							[
								SNew(SImage)
								.Image(LeadingIcon)
								.ColorAndOpacity(LeadingIconTint)
							]
						]
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.VAlign(VAlign_Center)
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot()
						.AutoHeight()
						[
							SNew(STextBlock)
							.Text(Title)
							.Font(WorldBLDContextMenuFont::GetMedium(12.0f, 0))
							.ColorAndOpacity(FLinearColor::White)
						]
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(FMargin(0.0f, 2.0f, 0.0f, 0.0f))
						[
							SNew(STextBlock)
							.Text(Subtitle)
							.Font(WorldBLDContextMenuFont::GetMedium(9.0f, 0))
							.ColorAndOpacity(GetSubtitleColor())
							.AutoWrapText(true)
						]
					]
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.VAlign(VAlign_Center)
					.Padding(FMargin(10.0f, 0.0f, 0.0f, 0.0f))
					[
						SNew(SBox)
						.WidthOverride(TrailingIconExtent)
						.HeightOverride(TrailingIconExtent)
						[
							SNew(SImage)
							.Image(TrailingIcon)
							.ColorAndOpacity(FLinearColor(0.65f, 0.65f, 0.65f, 1.0f))
						]
					]
				]
			]
		];
}

void SWorldBLDResourcesDialog::SetHostWindow(const TSharedRef<SWindow>& InWindow)
{
	HostWindow = InWindow;
}

void SWorldBLDResourcesDialog::Open()
{
	using namespace WorldBLDResourcesDialogLocal;

	if (!FSlateApplication::IsInitialized())
	{
		return;
	}

	if (ActiveWindow.IsValid())
	{
		if (const TSharedPtr<SWindow> Pinned = ActiveWindow.Pin())
		{
			Pinned->BringToFront();
			return;
		}
	}

	TSharedPtr<SWorldBLDResourcesDialog> DialogWidget;
	const TSharedRef<SWindow> Window = SNew(SWindow)
		.Title(LOCTEXT("WindowTitle", "WorldBLD Resources"))
		.CreateTitleBar(false)
		.SupportsMaximize(false)
		.SupportsMinimize(false)
		.HasCloseButton(false)
		.SizingRule(ESizingRule::Autosized)
		.AutoCenter(EAutoCenter::PreferredWorkArea)
		.IsTopmostWindow(false);

	Window->SetContent(
		SAssignNew(DialogWidget, SWorldBLDResourcesDialog)
	);
	DialogWidget->SetHostWindow(Window);

	Window->SetOnWindowClosed(FOnWindowClosed::CreateStatic([](const TSharedRef<SWindow>&)
	{
		WorldBLDResourcesDialogLocal::ActiveWindow.Reset();
	}));

	FSlateApplication::Get().AddWindow(Window);
	FSlateApplication::Get().SetKeyboardFocus(DialogWidget, EFocusCause::SetDirectly);
	ActiveWindow = Window;
}

FReply SWorldBLDResourcesDialog::HandleCloseClicked()
{
	CloseDialog();
	return FReply::Handled();
}

FReply SWorldBLDResourcesDialog::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape)
	{
		CloseDialog();
		return FReply::Handled();
	}

	return SCompoundWidget::OnKeyDown(MyGeometry, InKeyEvent);
}

FReply SWorldBLDResourcesDialog::HandleDocsClicked()
{
	FPlatformProcess::LaunchURL(WorldBLDResourcesDialogLocal::DocsUrl, nullptr, nullptr);
	return FReply::Handled();
}

FReply SWorldBLDResourcesDialog::HandleYouTubeClicked()
{
	FPlatformProcess::LaunchURL(WorldBLDResourcesDialogLocal::YouTubeUrl, nullptr, nullptr);
	return FReply::Handled();
}

FReply SWorldBLDResourcesDialog::HandleDemoMapClicked()
{
	UWorldBLDEdMode::OpenDemoMap();
	CloseDialog();
	return FReply::Handled();
}

FReply SWorldBLDResourcesDialog::HandleBrowsePresetsClicked()
{
	FWorldBLDAssetLibraryWindow::OpenAssetLibrary();
	CloseDialog();
	return FReply::Handled();
}

FReply SWorldBLDResourcesDialog::HandleCheckForUpdatesClicked()
{
	if (UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
	{
		EdMode->CheckForPluginUpdates(/*bForceNotify=*/true);
	}
	return FReply::Handled();
}

void SWorldBLDResourcesDialog::CloseDialog()
{
	if (const TSharedPtr<SWindow> Pinned = HostWindow.Pin())
	{
		Pinned->RequestDestroyWindow();
	}
}

#undef LOCTEXT_NAMESPACE
