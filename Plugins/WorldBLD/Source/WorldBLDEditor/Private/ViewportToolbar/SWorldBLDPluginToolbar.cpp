// Copyright WorldBLD LLC. All rights reserved.

#include "ViewportToolbar/SWorldBLDPluginToolbar.h"

#include "ToolsMenu/SWorldBLDToolSwitchMenu.h"
#include "ViewportToolbar/SWorldBLDToolbarButton.h"
#include "Authorization/WorldBLDAuthSubsystem.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"
#include "Downloader/CurlDownloaderLibrary.h"
#include "PluginManager/SWorldBLDPluginManager.h"
#include "WorldBLDEditorToolkit.h"

#include "Brushes/SlateDynamicImageBrush.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "HAL/FileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
#include "Styling/AppStyle.h"
#include "Styling/ToolBarStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SMenuAnchor.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WorldBLDPluginToolbar"

namespace WorldBLDPluginToolbarConstants
{
	static const TCHAR* ToolbarLayoutConfigSection = TEXT("WorldBLD.ViewportToolbar");
	static const TCHAR* ToolbarOrientationConfigKey = TEXT("Orientation");
	static const TCHAR* OrientationHorizontalValue = TEXT("Horizontal");
	static const TCHAR* OrientationVerticalValue = TEXT("Vertical");

	static constexpr float AuthPollInterval = 0.5f;
	static constexpr float OverflowIconExtent = 15.0f;
	static constexpr float ManageIconExtent = 30.0f;
	static constexpr float SpacerThickness = 1.0f;
	static constexpr float SpacerLength = 52.0f;
	static const FLinearColor SpacerColor(0.18f, 0.18f, 0.18f, 1.0f);
	static const FName PaletteToolBarStyle(TEXT("PaletteToolBar"));
	static const FName OverflowIconName(TEXT("LandscapeEditor.RegionSelectTool"));
	static const TCHAR* WorldBLDPluginName = TEXT("WorldBLD");
	static const TCHAR* MoreIconRelativePath = TEXT("Resources/Icon_ThreeDots.png");
	static const TCHAR* ManageIconRelativePath = TEXT("Resources/Icon_Download_Icon.PNG");
}

void SWorldBLDPluginToolbar::Construct(const FArguments& InArgs)
{
	MainButtons = InArgs._MainButtons;
	EdMode = InArgs._EdMode;
	Downloader = InArgs._Downloader;
	LoginButton = InArgs._LoginButton;
	OverflowButtons = InArgs._OverflowButtons;
	ManageToolId = InArgs._ManageToolId;
	ManageToolDisplayName = FText::FromName(ManageToolId);
	LoadPersistedOrientation();

	if (const TSharedPtr<IPlugin> WorldBLDPlugin = IPluginManager::Get().FindPlugin(WorldBLDPluginToolbarConstants::WorldBLDPluginName))
	{
		const FString ThreeDotsIconPath = FPaths::ConvertRelativePathToFull(
			WorldBLDPlugin->GetBaseDir() / WorldBLDPluginToolbarConstants::MoreIconRelativePath);
		if (IFileManager::Get().FileExists(*ThreeDotsIconPath))
		{
			OverflowIconBrush = MakeShared<FSlateDynamicImageBrush>(
				FName(*ThreeDotsIconPath),
				FVector2D(WorldBLDPluginToolbarConstants::OverflowIconExtent, WorldBLDPluginToolbarConstants::OverflowIconExtent));
		}

		const FString ManageIconPath = FPaths::ConvertRelativePathToFull(
			WorldBLDPlugin->GetBaseDir() / WorldBLDPluginToolbarConstants::ManageIconRelativePath);
		if (IFileManager::Get().FileExists(*ManageIconPath))
		{
			ManageToolIconBrush = MakeShared<FSlateDynamicImageBrush>(
				FName(*ManageIconPath),
				FVector2D(WorldBLDPluginToolbarConstants::ManageIconExtent, WorldBLDPluginToolbarConstants::ManageIconExtent));
		}
	}

	if (const UWorldBLDEdMode* Mode = EdMode.Get())
	{
		for (const FPluginToolData& ToolData : Mode->AvailableTools)
		{
			if (ToolData.ToolName.Equals(ManageToolId.ToString(), ESearchCase::IgnoreCase))
			{
				ManageToolDisplayName = FText::FromString(ToolData.ToolName);
				break;
			}
		}
	}

	bCachedLoggedIn = UWorldBLDAuthSubsystem::IsLoggedIn();

	SAssignNew(ToolSwitchMenu, SWorldBLDToolSwitchMenu)
		.EdMode(EdMode)
		.Downloader(Downloader)
		.Orientation(Orientation)
		.bIsLoggedIn(bCachedLoggedIn)
		.OnLoginClicked(LoginButton.OnClicked);

	RebuildLayout();
}

TSharedRef<SWidget> SWorldBLDPluginToolbar::GetToolSwitchWidget() const
{
	return ToolSwitchMenu.IsValid()
		? StaticCastSharedRef<SWidget>(ToolSwitchMenu.ToSharedRef())
		: SNullWidget::NullWidget;
}

void SWorldBLDPluginToolbar::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

	// Poll login state cheaply; rebuild only when it changes so the disabled
	// tab treatment and inline Log In action stay current.
	AuthPollAccumulator += InDeltaTime;
	if (AuthPollAccumulator >= WorldBLDPluginToolbarConstants::AuthPollInterval)
	{
		AuthPollAccumulator = 0.0f;
		const bool bLoggedIn = UWorldBLDAuthSubsystem::IsLoggedIn();
		if (bLoggedIn != bCachedLoggedIn)
		{
			bCachedLoggedIn = bLoggedIn;
			RebuildLayout();
		}
	}
}

TSharedRef<SWidget> SWorldBLDPluginToolbar::MakeButtonWidget(const FWorldBLDToolbarButtonDef& InDef)
{
	const bool bEnabledWhenLoggedOut = InDef.bEnabledWhenLoggedOut;
	const FWorldBLDToolbarEnabled EnabledPredicate = InDef.IsEnabled;
	TAttribute<bool> EnabledAttr = TAttribute<bool>::Create(TAttribute<bool>::FGetter::CreateLambda(
		[this, bEnabledWhenLoggedOut, EnabledPredicate]()
		{
			const bool bAuthAllowsInteraction = bEnabledWhenLoggedOut || bCachedLoggedIn;
			const bool bPredicateAllowsInteraction = !EnabledPredicate.IsBound() || EnabledPredicate.Execute();
			return bAuthAllowsInteraction && bPredicateAllowsInteraction;
		}));

	return SNew(SWorldBLDToolbarButton)
		.ButtonDef(InDef)
		.ButtonEnabled(EnabledAttr);
}

TSharedRef<SWidget> SWorldBLDPluginToolbar::MakeManageToolButtonWidget()
{
	const FText Tooltip = FText::Format(
		LOCTEXT("ManageToolTooltip", "Install, update, or uninstall {0} for this project"),
		ManageToolDisplayName);
	const FToolBarStyle& ToolBarStyle = FAppStyle::Get().GetWidgetStyle<FToolBarStyle>(
		WorldBLDPluginToolbarConstants::PaletteToolBarStyle);

	const TSharedRef<SWidget> ButtonContent =
		SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.HAlign(HAlign_Center)
		.Padding(FMargin(0.0f, 2.0f, 0.0f, 0.0f))
		[
			SNew(SBox)
			.WidthOverride(WorldBLDPluginToolbarConstants::ManageIconExtent)
			.HeightOverride(WorldBLDPluginToolbarConstants::ManageIconExtent)
			[
				SNew(SImage)
				.Image(ManageToolIconBrush.Get())
				.ColorAndOpacity(this, &SWorldBLDPluginToolbar::GetManageToolIconColor)
			]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		.HAlign(HAlign_Center)
		.Padding(FMargin(
			ToolBarStyle.LabelPadding.Left,
			ToolBarStyle.LabelPadding.Top + 5.0f,
			ToolBarStyle.LabelPadding.Right,
			ToolBarStyle.LabelPadding.Bottom))
		[
			SNew(STextBlock)
			.TextStyle(&ToolBarStyle.LabelStyle)
			.Text(this, &SWorldBLDPluginToolbar::GetManageToolLabel)
			.Justification(ETextJustify::Center)
		];

	return SNew(SButton)
		.ButtonStyle(&ToolBarStyle.ButtonStyle)
		.ContentPadding(FMargin(4.0f, 2.0f))
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		.ToolTipText(Tooltip)
		.OnClicked_Lambda([this]()
		{
			HandleManageToolClicked();
			return FReply::Handled();
		})
		[
			ButtonContent
		];
}

TSharedRef<SWidget> SWorldBLDPluginToolbar::MakeSpacerWidget() const
{
	const bool bVerticalLayout = (Orientation == Orient_Vertical);
	const float SpacerWidth = bVerticalLayout
		? WorldBLDPluginToolbarConstants::SpacerLength
		: WorldBLDPluginToolbarConstants::SpacerThickness;
	const float SpacerHeight = bVerticalLayout
		? WorldBLDPluginToolbarConstants::SpacerThickness
		: WorldBLDPluginToolbarConstants::SpacerLength;

	return SNew(SBox)
		.WidthOverride(SpacerWidth)
		.HeightOverride(SpacerHeight)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::GetBrush("WhiteBrush"))
			.BorderBackgroundColor(WorldBLDPluginToolbarConstants::SpacerColor)
		];
}

void SWorldBLDPluginToolbar::LoadPersistedOrientation()
{
	if (GConfig == nullptr)
	{
		return;
	}

	FString OrientationValue;
	if (!GConfig->GetString(
		WorldBLDPluginToolbarConstants::ToolbarLayoutConfigSection,
		WorldBLDPluginToolbarConstants::ToolbarOrientationConfigKey,
		OrientationValue,
		GEditorPerProjectIni))
	{
		return;
	}

	if (OrientationValue.Equals(WorldBLDPluginToolbarConstants::OrientationVerticalValue, ESearchCase::IgnoreCase))
	{
		Orientation = Orient_Vertical;
	}
	else if (OrientationValue.Equals(WorldBLDPluginToolbarConstants::OrientationHorizontalValue, ESearchCase::IgnoreCase))
	{
		Orientation = Orient_Horizontal;
	}
}

void SWorldBLDPluginToolbar::SavePersistedOrientation() const
{
	if (GConfig == nullptr)
	{
		return;
	}

	const TCHAR* OrientationValue = (Orientation == Orient_Vertical)
		? WorldBLDPluginToolbarConstants::OrientationVerticalValue
		: WorldBLDPluginToolbarConstants::OrientationHorizontalValue;

	GConfig->SetString(
		WorldBLDPluginToolbarConstants::ToolbarLayoutConfigSection,
		WorldBLDPluginToolbarConstants::ToolbarOrientationConfigKey,
		OrientationValue,
		GEditorPerProjectIni);
	GConfig->Flush(false, GEditorPerProjectIni);
}

bool SWorldBLDPluginToolbar::HasAnyVisibleOverflow() const
{
	for (const FWorldBLDToolbarButtonDef& Def : OverflowButtons)
	{
		if (Def.IsVisibleNow())
		{
			return true;
		}
	}
	return false;
}

bool SWorldBLDPluginToolbar::IsManageToolUpdateAvailable() const
{
	const UWorldBLDEdMode* Mode = EdMode.Get();
	if (Mode == nullptr || ManageToolId.IsNone())
	{
		return false;
	}

	const FString ToolId = ManageToolId.ToString();
	FString ServerVersion;
	FString ServerSHA1;
	for (const FPluginToolData& ToolData : Mode->AvailableTools)
	{
		if (ToolData.ToolName.Equals(ToolId, ESearchCase::IgnoreCase))
		{
			ServerVersion = ToolData.Version;
			ServerSHA1 = ToolData.SHA1;
			break;
		}
	}

	return Mode->GetToolUpdateState(ToolId, ServerVersion, ServerSHA1)
		== EWorldBLDToolUpdateState::UpdateAvailable;
}

FText SWorldBLDPluginToolbar::GetManageToolLabel() const
{
	return IsManageToolUpdateAvailable()
		? LOCTEXT("UpdateAvailableLabel", "Update Available")
		: LOCTEXT("ManageToolLabelLive", "Manage");
}

FSlateColor SWorldBLDPluginToolbar::GetManageToolIconColor() const
{
	return IsManageToolUpdateAvailable()
		? FSlateColor(WorldBLDContextMenuStyle::GetHighlightRedColor())
		: FSlateColor(FLinearColor::White);
}

void SWorldBLDPluginToolbar::HandleManageToolClicked()
{
	SWorldBLDPluginManager::ShowModalForTool(ManageToolId, EdMode, Downloader);
}

void SWorldBLDPluginToolbar::RebuildLayout()
{
	// Wrap box of plugin-specific buttons (collapsible).
	const TSharedRef<SWrapBox> WrapBox =
		SNew(SWrapBox)
		.Orientation(Orientation)
		.UseAllottedSize(false)
		.PreferredSize(4096.0f);

	for (const FWorldBLDToolbarButtonDef& Def : MainButtons)
	{
		if (Def.bIsOverflow || !Def.IsVisibleNow())
		{
			continue;
		}

		WrapBox->AddSlot()
		.Padding(Def.bIsSpacer ? FMargin(8.0f, 2.0f) : FMargin(2.0f))
		[
			Def.bIsSpacer ? MakeSpacerWidget() : MakeButtonWidget(Def)
		];
	}

	const TSharedRef<SWidget> TrailingWidget = !ManageToolId.IsNone()
		? MakeManageToolButtonWidget()
		: SNullWidget::NullWidget;

	// Persistent three-dots overflow menu.
	const FSlateBrush* OverflowIcon = OverflowIconBrush.IsValid()
		? OverflowIconBrush.Get()
		: FAppStyle::Get().GetBrush(WorldBLDPluginToolbarConstants::OverflowIconName);
	const TSharedRef<SWidget> OverflowWidget =
		SAssignNew(OverflowAnchor, SMenuAnchor)
		.Placement(MenuPlacement_BelowAnchor)
		.OnGetMenuContent(this, &SWorldBLDPluginToolbar::BuildOverflowMenuContent)
		[
			SNew(SButton)
			.ButtonStyle(FAppStyle::Get(), "SimpleButton")
			.ContentPadding(FMargin(4.0f))
			.ToolTipText(LOCTEXT("MoreTooltip", "More"))
			.OnClicked_Lambda([this]()
			{
				if (OverflowAnchor.IsValid())
				{
					OverflowAnchor->SetIsOpen(!OverflowAnchor->IsOpen());
				}
				return FReply::Handled();
			})
			[
				SNew(SBox)
				.WidthOverride(WorldBLDPluginToolbarConstants::OverflowIconExtent)
				.HeightOverride(WorldBLDPluginToolbarConstants::OverflowIconExtent)
				[
					SNew(SImage)
					.Image(OverflowIcon)
				]
			]
		];

	// Collapse + orientation controls.
	const TSharedRef<SWidget> Controls =
		SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SButton)
			.ButtonStyle(FAppStyle::Get(), "SimpleButton")
			.ContentPadding(FMargin(2.0f))
			.ToolTipText(LOCTEXT("OrientationTooltip", "Toggle horizontal / vertical layout"))
			.OnClicked(this, &SWorldBLDPluginToolbar::HandleToggleOrientation)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("OrientationGlyph", "<"))
			]
		];

	const EVisibility BodyVisibility = EVisibility::Visible;

	if (Orientation == Orient_Vertical)
	{
		ChildSlot
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[ Controls ]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.0f, 2.0f)[ SNew(SBox).Visibility(BodyVisibility)[ WrapBox ] ]
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0.0f, 2.0f, 0.0f, 0.0f)[ TrailingWidget ]
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[ OverflowWidget ]
		];
		return;
	}

	ChildSlot
	[
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[ Controls ]
		+ SHorizontalBox::Slot().AutoWidth().Padding(2.0f, 0.0f)[ SNew(SBox).Visibility(BodyVisibility)[ WrapBox ] ]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(2.0f, 0.0f)[ TrailingWidget ]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[ OverflowWidget ]
	];
}

TSharedRef<SWidget> SWorldBLDPluginToolbar::BuildOverflowMenuContent()
{
	FMenuBuilder MenuBuilder(/*bShouldCloseWindowAfterMenuSelection=*/true, /*CommandList=*/nullptr);

	bool bAddedAny = false;
	for (const FWorldBLDToolbarButtonDef& Def : OverflowButtons)
	{
		if (!Def.IsVisibleNow())
		{
			continue;
		}

		const FText EntryTooltip = Def.Tooltip.IsEmpty() ? Def.Label : Def.Tooltip;

		const FSimpleDelegate Action = Def.OnClicked;
		const bool bEnabledWhenLoggedOut = Def.bEnabledWhenLoggedOut;
		const FWorldBLDToolbarEnabled EnabledPredicate = Def.IsEnabled;
		const FUIAction EntryAction(
			FExecuteAction::CreateLambda([Action]() { Action.ExecuteIfBound(); }),
			FCanExecuteAction::CreateLambda([this, bEnabledWhenLoggedOut, EnabledPredicate]()
			{
				const bool bAuthAllowsInteraction = bEnabledWhenLoggedOut || bCachedLoggedIn;
				const bool bPredicateAllowsInteraction = !EnabledPredicate.IsBound() || EnabledPredicate.Execute();
				return bAuthAllowsInteraction && bPredicateAllowsInteraction;
			}));

		if (Def.IconBrush.IsValid())
		{
			// FSlateIcon only references registered style-set brushes, so custom resource brushes
			// need a menu entry widget that renders the brush directly.
			const TSharedRef<SWidget> EntryContent =
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Center)
				[
					SNew(SImage)
					.Image(Def.IconBrush.Get())
					.ColorAndOpacity(Def.IconColorAndOpacity)
				]
				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.VAlign(VAlign_Center)
				.Padding(FMargin(8.0f, 0.0f, 0.0f, 0.0f))
				[
					SNew(STextBlock)
					.Text(Def.Label)
				];

			MenuBuilder.AddMenuEntry(EntryAction, EntryContent, NAME_None, EntryTooltip);
		}
		else
		{
			FSlateIcon EntryIcon;
			if (Def.IconName != NAME_None)
			{
				EntryIcon = FSlateIcon(FAppStyle::GetAppStyleSetName(), Def.IconName);
			}

			MenuBuilder.AddMenuEntry(Def.Label, EntryTooltip, EntryIcon, EntryAction);
		}
		bAddedAny = true;
	}

	if (!bAddedAny)
	{
		MenuBuilder.AddMenuEntry(
			LOCTEXT("NoOverflowActions", "No actions available"),
			FText::GetEmpty(),
			FSlateIcon(),
			FUIAction(FExecuteAction(), FCanExecuteAction::CreateLambda([]() { return false; })));
	}

	return MenuBuilder.MakeWidget();
}

FReply SWorldBLDPluginToolbar::HandleToggleOrientation()
{
	Orientation = (Orientation == Orient_Horizontal) ? Orient_Vertical : Orient_Horizontal;
	if (ToolSwitchMenu.IsValid())
	{
		ToolSwitchMenu->SetOrientation(Orientation);
	}
	SavePersistedOrientation();
	RebuildLayout();
	return FReply::Handled();
}

#undef LOCTEXT_NAMESPACE
