// Copyright WorldBLD LLC. All rights reserved.

#include "ToolsMenu/SWorldBLDToolSwitchMenu.h"

#include "WorldBLDEditorToolkit.h"
#include "WorldBLDEditorUtilityLibrary.h"

#include "Authorization/WorldBLDAuthSubsystem.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"
#include "Downloader/CurlDownloaderLibrary.h"
#include "PluginManager/SWorldBLDPluginManager.h"
#include "ViewportToolbar/WorldBLDToolbarProvider.h"

#include "Brushes/SlateColorBrush.h"
#include "Brushes/SlateDynamicImageBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/FileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Math/Vector4.h"
#include "Misc/Paths.h"
#include "Styling/AppStyle.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateBrush.h"
#include "Styling/StyleColors.h"
#include "Styling/StyleDefaults.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SMenuAnchor.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WorldBLDToolSwitchMenu"

namespace WorldBLDToolSwitchMenuInternal
{
	static constexpr float ToolIconExtent = 22.0f;
	static constexpr float TabHeight = 34.0f;
	static constexpr float ActiveIndicatorThickness = 2.0f;
	static constexpr float MiniToolsMenuWidth = 340.0f;
	static constexpr float MiniToolsMenuMaxHeight = 280.0f;
	static constexpr float MiniToolIconWellExtent = 48.0f;
	static constexpr float MiniToolIconExtent = 24.0f;
	static constexpr float MiniToolAccentWidth = 3.0f;
	static const FLinearColor PanelColor(0.025f, 0.025f, 0.025f, 0.97f);
	static const FLinearColor DisabledIconColor(1.0f, 1.0f, 1.0f, 0.30f);
	static constexpr float MoreToolsPanelGap = 4.0f;
	static constexpr float PanelContentPadding = 3.0f;
	static constexpr float TabGap = 2.0f;

	static const FSlateBrush* GetPanelBorderBrush()
	{
		// Corner order: TopLeft, TopRight, BottomRight, BottomLeft.
		static const FVector4 CornerRadii(4.0f, 4.0f, 4.0f, 4.0f);
		static const FSlateRoundedBoxBrush Brush(PanelColor, CornerRadii);
		return &Brush;
	}

	static FSlateFontInfo GetToolNameFont()
	{
		FSlateFontInfo Font = FAppStyle::GetFontStyle(TEXT("NormalFont"));
		Font.Size = 12;
		return Font;
	}

	/** Hardcoded built-in mini tool entry used by the Mini Tools popup. */
	struct FMiniToolDescriptor
	{
		FText Title;
		FText Description;
		FName IconBrushName = NAME_None;
		FSimpleDelegate OnClicked;
	};

	static TArray<FMiniToolDescriptor> GetMiniToolDescriptors()
	{
		TArray<FMiniToolDescriptor> Tools;

		{
			FMiniToolDescriptor LandBLD;
			LandBLD.Title = LOCTEXT("LandBLDMiniToolTitle", "LandBLD");
			LandBLD.Description = LOCTEXT(
				"LandBLDMiniToolDescription",
				"Populate any landscape with a complete PCG setup: grass, forest, fields, and more, ready to go.");
			LandBLD.IconBrushName = TEXT("LandscapeEditor.ErosionTool");
			LandBLD.OnClicked = FSimpleDelegate::CreateLambda([]()
			{
				UWorldBLDEditorUtilityLibrary::PopulateTargetLandscape();
			});
			Tools.Add(MoveTemp(LandBLD));
		}

		return Tools;
	}

	static const FSlateBrush* ResolveMiniToolIcon(const FName& IconBrushName)
	{
		if (!IconBrushName.IsNone())
		{
			const FSlateBrush* Brush = FAppStyle::GetOptionalBrush(IconBrushName);
			if (Brush != nullptr && Brush != FStyleDefaults::GetNoBrush())
			{
				return Brush;
			}
		}
		return FAppStyle::GetBrush(TEXT("ClassThumbnail.Default"));
	}

	static TSharedRef<SWidget> BuildMiniToolEntry(const FMiniToolDescriptor& Descriptor, const FSimpleDelegate& OnDismissMenu)
	{
		static const FVector4 CardRadii(5.0f, 5.0f, 5.0f, 5.0f);
		static const FVector4 IconWellRadii(4.0f, 4.0f, 4.0f, 4.0f);

		static const FSlateBrushOutlineSettings CardOutline = []()
		{
			FSlateBrushOutlineSettings Outline;
			Outline.CornerRadii = CardRadii;
			Outline.Color = FStyleColors::DropdownOutline;
			Outline.Width = 1.0f;
			Outline.RoundingType = ESlateBrushRoundingType::FixedRadius;
			Outline.bUseBrushTransparency = false;
			return Outline;
		}();

		static const FSlateRoundedBoxBrush NormalCardBrush = []()
		{
			FSlateRoundedBoxBrush Brush(FStyleColors::Recessed, CardRadii);
			Brush.OutlineSettings = CardOutline;
			return Brush;
		}();

		static const FSlateRoundedBoxBrush HoveredCardBrush = []()
		{
			FSlateRoundedBoxBrush Brush(FStyleColors::Header, CardRadii);
			Brush.OutlineSettings = CardOutline;
			return Brush;
		}();

		static const FButtonStyle CardButtonStyle = []()
		{
			return FButtonStyle()
				.SetNormal(NormalCardBrush)
				.SetHovered(HoveredCardBrush)
				.SetPressed(HoveredCardBrush)
				.SetDisabled(NormalCardBrush)
				.SetNormalPadding(FMargin(0.0f))
				.SetPressedPadding(FMargin(0.0f));
		}();

		static const FSlateRoundedBoxBrush IconWellBrush(FStyleColors::Header, IconWellRadii);
		static const FSlateColorBrush AccentBrush(WorldBLDContextMenuStyle::GetHighlightRedColor());

		const FSlateBrush* ToolIcon = ResolveMiniToolIcon(Descriptor.IconBrushName);
		const FText Title = Descriptor.Title;
		const FText Description = Descriptor.Description;
		const FSimpleDelegate OnClicked = Descriptor.OnClicked;

		return SNew(SButton)
			.ButtonStyle(&CardButtonStyle)
			.ContentPadding(FMargin(0.0f))
			.ToolTipText(Description)
			.OnClicked_Lambda([OnClicked, OnDismissMenu]()
			{
				OnDismissMenu.ExecuteIfBound();
				OnClicked.ExecuteIfBound();
				return FReply::Handled();
			})
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SBox)
					.WidthOverride(MiniToolAccentWidth)
					[
						SNew(SBorder)
						.BorderImage(&AccentBrush)
						.Padding(FMargin(0.0f))
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
						SNew(SBox)
						.WidthOverride(MiniToolIconWellExtent)
						.HeightOverride(MiniToolIconWellExtent)
						[
							SNew(SBorder)
							.BorderImage(&IconWellBrush)
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							[
								SNew(SImage)
								.Image(ToolIcon)
								.DesiredSizeOverride(FVector2D(MiniToolIconExtent, MiniToolIconExtent))
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
							.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 14))
							.ColorAndOpacity(FLinearColor::White)
						]
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(FMargin(0.0f, 4.0f, 0.0f, 0.0f))
						[
							SNew(STextBlock)
							.Text(Description)
							.AutoWrapText(true)
							.ColorAndOpacity(FSlateColor::UseSubduedForeground())
							.LineHeightPercentage(1.15f)
						]
					]
				]
			];
	}

	/** Icon wrapper that presents a non-interactive label above the tab without changing its layout. */
	class SHoverLabelAnchor final : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SHoverLabelAnchor)
		{}
			SLATE_ATTRIBUTE(FText, Label)
			SLATE_DEFAULT_SLOT(FArguments, Content)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			Label = InArgs._Label;

			ChildSlot
			[
				SAssignNew(MenuAnchor, SMenuAnchor)
				.Placement(MenuPlacement_AboveAnchor)
				.OnGetMenuContent(this, &SHoverLabelAnchor::BuildLabel)
				[
					InArgs._Content.Widget
				]
			];
		}

		void SetTabContent(const TSharedRef<SWidget>& InContent) const
		{
			if (MenuAnchor.IsValid())
			{
				MenuAnchor->SetContent(InContent);
			}
		}

	private:
		virtual void OnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
		{
			SCompoundWidget::OnMouseEnter(MyGeometry, MouseEvent);
			if (MenuAnchor.IsValid())
			{
				MenuAnchor->SetIsOpen(true, false);
			}
		}

		virtual void OnMouseLeave(const FPointerEvent& MouseEvent) override
		{
			if (MenuAnchor.IsValid())
			{
				MenuAnchor->SetIsOpen(false, false);
			}
			SCompoundWidget::OnMouseLeave(MouseEvent);
		}

		TSharedRef<SWidget> BuildLabel() const
		{
			return SNew(SBorder)
				.BorderImage(FAppStyle::GetBrush(TEXT("WhiteBrush")))
				.BorderBackgroundColor(PanelColor)
				.Padding(FMargin(8.0f, 4.0f))
				[
					SNew(STextBlock)
					.Text(Label)
					.Font(GetToolNameFont())
					.ColorAndOpacity(FLinearColor::White)
				];
		}

		TAttribute<FText> Label;
		TSharedPtr<SMenuAnchor> MenuAnchor;
	};
}

void SWorldBLDToolSwitchMenu::Construct(const FArguments& InArgs)
{
	EdMode = InArgs._EdMode;
	Downloader = InArgs._Downloader;
	Orientation = InArgs._Orientation;
	bIsLoggedIn = InArgs._bIsLoggedIn;
	OnLoginClicked = InArgs._OnLoginClicked;

	MenuContainer.Reset();
	ToolIconBrushes.Reset();
	CachedAvailableToolsHash = 0;
	bShowMoreToolsPanel = false;

	ChildSlot
	[
		BuildMenuContent()
	];
}

void SWorldBLDToolSwitchMenu::SetOrientation(EOrientation InOrientation)
{
	if (Orientation != InOrientation)
	{
		Orientation = InOrientation;
		RebuildMenuEntries();
	}
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::BuildMenuContent()
{
	SAssignNew(MenuContainer, SBox);
	RebuildMenuEntries();
	return MenuContainer.ToSharedRef();
}

void SWorldBLDToolSwitchMenu::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

	const bool bCurrentLoggedIn = UWorldBLDAuthSubsystem::IsLoggedIn();
	if (bCurrentLoggedIn != bIsLoggedIn)
	{
		bIsLoggedIn = bCurrentLoggedIn;
		RebuildMenuEntries();
		return;
	}

	// The server tool list is fetched asynchronously. Keep the persistent strip in
	// sync when discovery completes or tool metadata changes.
	const uint32 CurrentHash = ComputeAvailableToolsHash();
	if (CurrentHash != CachedAvailableToolsHash)
	{
		RebuildMenuEntries();
	}
}

uint32 SWorldBLDToolSwitchMenu::ComputeAvailableToolsHash() const
{
	const UWorldBLDEdMode* EdModePtr = EdMode.Get();
	if (EdModePtr == nullptr)
	{
		return 0;
	}

	// Only hash fields that affect tab strip contents / active indicator.
	// Description, DownloadLink, ServerId, and RequiredToolIds are filled/mutated
	// asynchronously after FetchAvailableTools and must not trigger full rebuilds.
	uint32 Hash = GetTypeHash(EdModePtr->GetActiveViewportToolbarId());
	for (const FPluginToolData& ToolData : EdModePtr->AvailableTools)
	{
		Hash = HashCombineFast(Hash, GetTypeHash(ToolData.ToolName));
		Hash = HashCombineFast(Hash, GetTypeHash(ToolData.Version));
		Hash = HashCombineFast(Hash, GetTypeHash(ToolData.SHA1));
	}
	return Hash;
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::BuildToolTab(
	const FString& ToolId,
	const FText& DisplayName,
	const FString& ServerVersion,
	const FString& ServerSHA1,
	bool bIsWorldBLD)
{
	const UWorldBLDEdMode* EdModePtr = EdMode.Get();
	const bool bIsActive = EdModePtr != nullptr
		&& EdModePtr->GetActiveViewportToolbarId().ToString().Equals(ToolId, ESearchCase::IgnoreCase);
	const bool bIsVertical = Orientation == Orient_Vertical;
	const FSlateBrush* ToolIcon = GetToolIcon(ToolId);

	TSharedPtr<WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor> HoverSurface;
	SAssignNew(HoverSurface, WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor)
		.Label(DisplayName);

	HoverSurface->SetTabContent(
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		[
			SNew(SButton)
			.ButtonStyle(&WorldBLDContextMenuStyle::GetToolSwitchTabButtonStyle())
			.ContentPadding(FMargin(6.0f, 4.0f))
			.IsEnabled_Lambda([this]()
			{
				return bIsLoggedIn;
			})
			.OnClicked_Lambda([this, ToolId, bIsWorldBLD]()
			{
				return bIsWorldBLD ? HandleSwitchToWorldBLDClicked() : HandleToolClicked(ToolId);
			})
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Center)
				[
					SNew(SBox)
					.WidthOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
					.HeightOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
					[
						SNew(SOverlay)
						+ SOverlay::Slot()
						[
							SNew(SImage)
							.Image(ToolIcon)
							.ColorAndOpacity_Lambda([this, bIsActive]()
							{
								if (!bIsLoggedIn)
								{
									return WorldBLDToolSwitchMenuInternal::DisabledIconColor;
								}
								return bIsActive
									? WorldBLDContextMenuStyle::GetHighlightRedColor()
									: FLinearColor::White;
							})
						]
						+ SOverlay::Slot()
						.HAlign(HAlign_Right)
						.VAlign(VAlign_Top)
						[
							SNew(SBox)
							.WidthOverride(6.0f)
							.HeightOverride(6.0f)
							.Visibility_Lambda([this, ToolId, ServerVersion, ServerSHA1, bIsWorldBLD]()
							{
								const UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
								const UWorldBLDEdMode* CurrentEdMode = EdMode.Get();
								const bool bPendingRestart = UCurlDownloaderLibrary::HasPendingStagedUpdate(ToolId)
									|| ((DownloaderPtr != nullptr) && DownloaderPtr->HasPendingInstallRestart(ToolId));
								const EWorldBLDToolUpdateState UpdateState = CurrentEdMode != nullptr
									? CurrentEdMode->GetToolUpdateState(ToolId, ServerVersion, ServerSHA1)
									: EWorldBLDToolUpdateState::InstalledUnknownSha1;
								const bool bNeedsAttention = !bIsWorldBLD
									&& bIsLoggedIn
									&& (IsToolInstalling(ToolId)
										|| bPendingRestart
										|| UpdateState == EWorldBLDToolUpdateState::NotInstalled
										|| UpdateState == EWorldBLDToolUpdateState::UpdateAvailable);
								return bNeedsAttention ? EVisibility::HitTestInvisible : EVisibility::Collapsed;
							})
							[
								SNew(SBorder)
								.BorderImage(FAppStyle::GetBrush(TEXT("WhiteBrush")))
								.BorderBackgroundColor(WorldBLDContextMenuStyle::GetHighlightRedColor())
								.Padding(FMargin(0.0f))
							]
						]
					]
				]
			]
		]
		);

	const TSharedRef<SBorder> ActiveIndicator =
		SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush(TEXT("WhiteBrush")))
		.BorderBackgroundColor(bIsActive
			? WorldBLDContextMenuStyle::GetHighlightRedColor()
			: FLinearColor::Transparent)
		.Padding(FMargin(0.0f));

	if (bIsVertical)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBox)
				.MinDesiredHeight(WorldBLDToolSwitchMenuInternal::TabHeight)
				[
					HoverSurface.ToSharedRef()
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBox)
				.WidthOverride(WorldBLDToolSwitchMenuInternal::ActiveIndicatorThickness)
				[
					ActiveIndicator
				]
			];
	}

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
				.MinDesiredHeight(WorldBLDToolSwitchMenuInternal::TabHeight)
				[
					HoverSurface.ToSharedRef()
				]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
				.HeightOverride(WorldBLDToolSwitchMenuInternal::ActiveIndicatorThickness)
				[
					ActiveIndicator
				]
		];
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::BuildMoreToolsTab()
{
	const bool bIsVertical = Orientation == Orient_Vertical;
	const bool bIsActive = bShowMoreToolsPanel;
	const FSlateBrush* ToolIcon = GetToolIcon(TEXT("MoreTools"));

	TSharedPtr<WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor> HoverSurface;
	SAssignNew(HoverSurface, WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor)
		.Label(LOCTEXT("MoreToolsTooltip", "More Tools"));

	HoverSurface->SetTabContent(
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		[
			SNew(SButton)
			.ButtonStyle(&WorldBLDContextMenuStyle::GetToolSwitchTabButtonStyle())
			.ContentPadding(FMargin(6.0f, 4.0f))
			.IsEnabled_Lambda([this]()
			{
				return bIsLoggedIn;
			})
			.OnClicked(this, &SWorldBLDToolSwitchMenu::HandleMoreToolsClicked)
			[
				SNew(SBox)
				.WidthOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
				.HeightOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
				[
					SNew(SImage)
					.Image(ToolIcon)
					.ColorAndOpacity_Lambda([this, bIsActive]()
					{
						if (!bIsLoggedIn)
						{
							return WorldBLDToolSwitchMenuInternal::DisabledIconColor;
						}
						return bIsActive
							? WorldBLDContextMenuStyle::GetHighlightRedColor()
							: FLinearColor::White;
					})
				]
			]
		]);

	const TSharedRef<SBorder> ActiveIndicator =
		SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush(TEXT("WhiteBrush")))
		.BorderBackgroundColor(bIsActive
			? WorldBLDContextMenuStyle::GetHighlightRedColor()
			: FLinearColor::Transparent)
		.Padding(FMargin(0.0f));

	if (bIsVertical)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBox)
				.MinDesiredHeight(WorldBLDToolSwitchMenuInternal::TabHeight)
				[
					HoverSurface.ToSharedRef()
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBox)
				.WidthOverride(WorldBLDToolSwitchMenuInternal::ActiveIndicatorThickness)
				[
					ActiveIndicator
				]
			];
	}

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
				.MinDesiredHeight(WorldBLDToolSwitchMenuInternal::TabHeight)
				[
					HoverSurface.ToSharedRef()
				]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
				.HeightOverride(WorldBLDToolSwitchMenuInternal::ActiveIndicatorThickness)
				[
					ActiveIndicator
				]
		];
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::BuildCustomToolsTab()
{
	const bool bIsVertical = Orientation == Orient_Vertical;
	const FSlateBrush* ToolIcon = GetToolIcon(TEXT("CustomTools"));

	TSharedPtr<WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor> HoverSurface;
	SAssignNew(HoverSurface, WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor)
		.Label(LOCTEXT("CustomToolsTooltip", "Custom Tools"));

	SAssignNew(CustomToolsMenuAnchor, SMenuAnchor)
		.Placement(MenuPlacement_AboveAnchor)
		.OnGetMenuContent_Static(&WorldBLDToolbar::CreateUtilitiesMenuContent)
		[
			SNew(SButton)
			.ButtonStyle(&WorldBLDContextMenuStyle::GetToolSwitchTabButtonStyle())
			.ContentPadding(FMargin(6.0f, 4.0f))
			.IsEnabled_Lambda([this]()
			{
				return bIsLoggedIn;
			})
			.OnClicked_Lambda([this]()
			{
				if (CustomToolsMenuAnchor.IsValid())
				{
					const bool bShouldOpen = !CustomToolsMenuAnchor->IsOpen();
					if (bShouldOpen && FSlateApplication::IsInitialized())
					{
						// Dismiss the hover label (and any other menus) so the utilities
						// popup is the only anchored menu above the tab.
						FSlateApplication::Get().DismissAllMenus();
					}
					CustomToolsMenuAnchor->SetIsOpen(bShouldOpen);
				}
				return FReply::Handled();
			})
			[
				SNew(SBox)
				.WidthOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
				.HeightOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
				[
					SNew(SImage)
					.Image(ToolIcon)
					.ColorAndOpacity_Lambda([this]()
					{
						return bIsLoggedIn
							? FLinearColor::White
							: WorldBLDToolSwitchMenuInternal::DisabledIconColor;
					})
				]
			]
		];

	HoverSurface->SetTabContent(
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		[
			CustomToolsMenuAnchor.ToSharedRef()
		]);

	const TSharedRef<SBorder> ActiveIndicator =
		SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush(TEXT("WhiteBrush")))
		.BorderBackgroundColor(FLinearColor::Transparent)
		.Padding(FMargin(0.0f));

	if (bIsVertical)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBox)
				.MinDesiredHeight(WorldBLDToolSwitchMenuInternal::TabHeight)
				[
					HoverSurface.ToSharedRef()
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBox)
				.WidthOverride(WorldBLDToolSwitchMenuInternal::ActiveIndicatorThickness)
				[
					ActiveIndicator
				]
			];
	}

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
				.MinDesiredHeight(WorldBLDToolSwitchMenuInternal::TabHeight)
				[
					HoverSurface.ToSharedRef()
				]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
				.HeightOverride(WorldBLDToolSwitchMenuInternal::ActiveIndicatorThickness)
				[
					ActiveIndicator
				]
		];
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::BuildMiniToolsTab()
{
	const bool bIsVertical = Orientation == Orient_Vertical;
	const FSlateBrush* ToolIcon = GetToolIcon(TEXT("MiniTools"));

	TSharedPtr<WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor> HoverSurface;
	SAssignNew(HoverSurface, WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor)
		.Label(LOCTEXT("MiniToolsTooltip", "Mini Tools"));

	SAssignNew(MiniToolsMenuAnchor, SMenuAnchor)
		.Placement(MenuPlacement_AboveAnchor)
		.OnGetMenuContent(this, &SWorldBLDToolSwitchMenu::CreateMiniToolsMenuContent)
		[
			SNew(SButton)
			.ButtonStyle(&WorldBLDContextMenuStyle::GetToolSwitchTabButtonStyle())
			.ContentPadding(FMargin(6.0f, 4.0f))
			.IsEnabled_Lambda([this]()
			{
				return bIsLoggedIn;
			})
			.OnClicked_Lambda([this]()
			{
				if (MiniToolsMenuAnchor.IsValid())
				{
					const bool bShouldOpen = !MiniToolsMenuAnchor->IsOpen();
					if (bShouldOpen && FSlateApplication::IsInitialized())
					{
						// Dismiss the hover label (and any other menus) so the mini-tools
						// popup is the only anchored menu above the tab.
						FSlateApplication::Get().DismissAllMenus();
					}
					MiniToolsMenuAnchor->SetIsOpen(bShouldOpen);
				}
				return FReply::Handled();
			})
			[
				SNew(SBox)
				.WidthOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
				.HeightOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
				[
					SNew(SImage)
					.Image(ToolIcon)
					.ColorAndOpacity_Lambda([this]()
					{
						return bIsLoggedIn
							? FLinearColor::White
							: WorldBLDToolSwitchMenuInternal::DisabledIconColor;
					})
				]
			]
		];

	HoverSurface->SetTabContent(
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		[
			MiniToolsMenuAnchor.ToSharedRef()
		]);

	const TSharedRef<SBorder> ActiveIndicator =
		SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush(TEXT("WhiteBrush")))
		.BorderBackgroundColor(FLinearColor::Transparent)
		.Padding(FMargin(0.0f));

	if (bIsVertical)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBox)
				.MinDesiredHeight(WorldBLDToolSwitchMenuInternal::TabHeight)
				[
					HoverSurface.ToSharedRef()
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBox)
				.WidthOverride(WorldBLDToolSwitchMenuInternal::ActiveIndicatorThickness)
				[
					ActiveIndicator
				]
			];
	}

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
				.MinDesiredHeight(WorldBLDToolSwitchMenuInternal::TabHeight)
				[
					HoverSurface.ToSharedRef()
				]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
				.HeightOverride(WorldBLDToolSwitchMenuInternal::ActiveIndicatorThickness)
				[
					ActiveIndicator
				]
		];
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::CreateMiniToolsMenuContent()
{
	using namespace WorldBLDToolSwitchMenuInternal;

	static const FVector4 PanelRadii(8.0f, 8.0f, 8.0f, 8.0f);
	static const FSlateRoundedBoxBrush PanelBrush(FStyleColors::Background, PanelRadii);

	const FSimpleDelegate DismissMenu = FSimpleDelegate::CreateLambda([this]()
	{
		if (MiniToolsMenuAnchor.IsValid())
		{
			MiniToolsMenuAnchor->SetIsOpen(false);
		}
		if (FSlateApplication::IsInitialized())
		{
			FSlateApplication::Get().DismissAllMenus();
		}
	});

	const TSharedRef<SVerticalBox> EntryList = SNew(SVerticalBox);
	const TArray<FMiniToolDescriptor> MiniTools = GetMiniToolDescriptors();
	for (int32 Index = 0; Index < MiniTools.Num(); ++Index)
	{
		EntryList->AddSlot()
			.AutoHeight()
			.Padding(FMargin(0.0f, 0.0f, 0.0f, Index + 1 < MiniTools.Num() ? 8.0f : 0.0f))
			[
				BuildMiniToolEntry(MiniTools[Index], DismissMenu)
			];
	}

	if (MiniTools.Num() == 0)
	{
		EntryList->AddSlot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("NoMiniToolsFound", "No mini tools available."))
				.ColorAndOpacity(FSlateColor::UseSubduedForeground())
			];
	}

	return SNew(SBox)
		.WidthOverride(MiniToolsMenuWidth)
		.MaxDesiredHeight(MiniToolsMenuMaxHeight)
		[
			SNew(SBorder)
			.BorderImage(&PanelBrush)
			.Padding(FMargin(12.0f))
			[
				SNew(SScrollBox)
				.Orientation(Orient_Vertical)
				+ SScrollBox::Slot()
				[
					EntryList
				]
			]
		];
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::BuildLoginTab()
{
	const FSlateBrush* LoginIcon = GetToolIcon(TEXT("Login"));

	return SNew(WorldBLDToolSwitchMenuInternal::SHoverLabelAnchor)
		.Label(LOCTEXT("LoginTabLabel", "Log In"))
		[
			SNew(SButton)
			.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
			.ContentPadding(FMargin(7.0f, 5.0f))
			.OnClicked(this, &SWorldBLDToolSwitchMenu::HandleLoginClicked)
			[
				SNew(SBox)
				.WidthOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
				.HeightOverride(WorldBLDToolSwitchMenuInternal::ToolIconExtent)
				[
					SNew(SImage)
					.Image(LoginIcon)
				]
			]
		];
}

void SWorldBLDToolSwitchMenu::RebuildMenuEntries()
{
	if (!MenuContainer.IsValid())
	{
		return;
	}

	TArray<TSharedRef<SWidget>> ToolTabs;
	ToolTabs.Add(BuildToolTab(
		TEXT("WorldBLD"),
		LOCTEXT("WorldBLDEntry", "WorldBLD"),
		FString(),
		FString(),
		true));

	TSet<FString> AddedToolIds;
	AddedToolIds.Add(TEXT("worldbld"));

	if (const UWorldBLDEdMode* EdModePtr = EdMode.Get())
	{
		for (const FPluginToolData& ToolData : EdModePtr->AvailableTools)
		{
			const FString ToolId = NormalizeToolId(ToolData.ToolName);
			const FString ToolKey = ToolId.ToLower();
			if (ToolId.IsEmpty() || AddedToolIds.Contains(ToolKey))
			{
				continue;
			}

			AddedToolIds.Add(ToolKey);
			ToolTabs.Add(BuildToolTab(
				ToolId,
				FText::FromString(ToolData.ToolName),
				ToolData.Version,
				ToolData.SHA1,
				false));
		}
	}

	if (!bIsLoggedIn)
	{
		ToolTabs.Add(BuildLoginTab());
	}

	ToolTabs.Add(BuildMoreToolsTab());
	const TSharedRef<SWidget> MoreToolsTab = ToolTabs.Last();

	const TSharedRef<SWidget> MainPanel = WrapTabStripInPanel(BuildTabStripWidget(ToolTabs));

	if (bShowMoreToolsPanel)
	{
		TArray<TSharedRef<SWidget>> MoreToolsTabs;
		MoreToolsTabs.Add(BuildMiniToolsTab());
		MoreToolsTabs.Add(BuildCustomToolsTab());
		const TSharedRef<SWidget> MoreToolsPanel = WrapTabStripInPanel(BuildTabStripWidget(MoreToolsTabs));

		// Measure desired sizes so the overflow strip can be centered on the More Tools tab
		// (right-aligning alone leaves the wider overflow flush with the panel edge).
		constexpr float LayoutScale = 1.0f;
		MainPanel->SlatePrepass(LayoutScale);
		MoreToolsPanel->SlatePrepass(LayoutScale);
		MoreToolsTab->SlatePrepass(LayoutScale);

		const FVector2D MainSize = MainPanel->GetDesiredSize();
		const FVector2D OverflowSize = MoreToolsPanel->GetDesiredSize();
		const FVector2D AnchorSize = MoreToolsTab->GetDesiredSize();

		if (Orientation == Orient_Vertical)
		{
			const float TopOffset = FMath::Max(
				0.0f,
				MainSize.Y
					- WorldBLDToolSwitchMenuInternal::PanelContentPadding
					- (AnchorSize.Y * 0.5f)
					- (OverflowSize.Y * 0.5f));

			MenuContainer->SetContent(
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(FMargin(0.0f, 0.0f, WorldBLDToolSwitchMenuInternal::MoreToolsPanelGap, 0.0f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(SBox)
						.HeightOverride(TopOffset)
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						MoreToolsPanel
					]
					+ SVerticalBox::Slot()
					.FillHeight(1.0f)
					[
						SNullWidget::NullWidget
					]
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Top)
				[
					MainPanel
				]);
		}
		else
		{
			const float LeftOffset = FMath::Max(
				0.0f,
				MainSize.X
					- WorldBLDToolSwitchMenuInternal::PanelContentPadding
					- (AnchorSize.X * 0.5f)
					- (OverflowSize.X * 0.5f));

			MenuContainer->SetContent(
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 0.0f, 0.0f, WorldBLDToolSwitchMenuInternal::MoreToolsPanelGap))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						SNew(SBox)
						.WidthOverride(LeftOffset)
					]
					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						MoreToolsPanel
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					[
						SNullWidget::NullWidget
					]
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.HAlign(HAlign_Left)
				[
					MainPanel
				]);
		}
	}
	else
	{
		MenuContainer->SetContent(MainPanel);
	}

	CachedAvailableToolsHash = ComputeAvailableToolsHash();
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::BuildTabStripWidget(const TArray<TSharedRef<SWidget>>& Tabs) const
{
	if (Orientation == Orient_Vertical)
	{
		const TSharedRef<SVerticalBox> TabRail = SNew(SVerticalBox);
		for (int32 Index = 0; Index < Tabs.Num(); ++Index)
		{
			TabRail->AddSlot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 0.0f, 0.0f, Index + 1 < Tabs.Num() ? WorldBLDToolSwitchMenuInternal::TabGap : 0.0f))
				[
					Tabs[Index]
				];
		}
		return TabRail;
	}

	const TSharedRef<SHorizontalBox> TabStrip = SNew(SHorizontalBox);
	for (int32 Index = 0; Index < Tabs.Num(); ++Index)
	{
		TabStrip->AddSlot()
			.AutoWidth()
			.Padding(FMargin(0.0f, 0.0f, Index + 1 < Tabs.Num() ? WorldBLDToolSwitchMenuInternal::TabGap : 0.0f, 0.0f))
			[
				Tabs[Index]
			];
	}
	return TabStrip;
}

TSharedRef<SWidget> SWorldBLDToolSwitchMenu::WrapTabStripInPanel(const TSharedRef<SWidget>& TabStrip) const
{
	return SNew(SBorder)
		.Padding(FMargin(WorldBLDToolSwitchMenuInternal::PanelContentPadding))
		.BorderImage(WorldBLDToolSwitchMenuInternal::GetPanelBorderBrush())
		.BorderBackgroundColor(FLinearColor::White)
		[
			TabStrip
		];
}

const FSlateBrush* SWorldBLDToolSwitchMenu::GetToolIcon(const FString& ToolId)
{
	const FString ToolKey = ToolId.ToLower();
	if (const TSharedPtr<FSlateBrush>* ExistingBrush = ToolIconBrushes.Find(ToolKey))
	{
		return ExistingBrush->Get();
	}

	TArray<FString> CandidateRelativePaths;
	if (ToolId.Equals(TEXT("MoreTools"), ESearchCase::IgnoreCase))
	{
		CandidateRelativePaths.Add(TEXT("Resources/Icon_plus-large.PNG"));
	}
	else if (ToolId.Equals(TEXT("CustomTools"), ESearchCase::IgnoreCase))
	{
		CandidateRelativePaths.Add(TEXT("Resources/Icon_Freehand-Draw-Tool.png"));
	}
	else if (ToolId.Equals(TEXT("MiniTools"), ESearchCase::IgnoreCase))
	{
		CandidateRelativePaths.Add(TEXT("Resources/Icon_Wrench.png"));
	}
	else if (ToolId.Equals(TEXT("WorldBLD"), ESearchCase::IgnoreCase))
	{
		CandidateRelativePaths.Add(TEXT("Resources/Icon_UI_HomeIcon.png"));
	}
	else if (ToolId.Equals(TEXT("RoadBLD"), ESearchCase::IgnoreCase))
	{
		CandidateRelativePaths.Add(TEXT("Resources/Icon_Road-Editor-Mode.png"));
	}
	else if (ToolId.Equals(TEXT("CityBLD"), ESearchCase::IgnoreCase))
	{
		CandidateRelativePaths.Add(TEXT("Resources/Icon_City-Editor-Mode.png"));
	}
	else if (ToolId.Equals(TEXT("TwinBLD"), ESearchCase::IgnoreCase))
	{
		CandidateRelativePaths.Add(TEXT("Resources/Icon_District-tool.png"));
	}
	else if (ToolId.Equals(TEXT("Login"), ESearchCase::IgnoreCase))
	{
		CandidateRelativePaths.Add(TEXT("Resources/Icon_Login.png"));
	}
	else
	{
		const FString SafeToolId = FPaths::GetCleanFilename(ToolId);
		if (!SafeToolId.IsEmpty() && SafeToolId.Equals(ToolId, ESearchCase::CaseSensitive))
		{
			CandidateRelativePaths.Add(FString::Printf(TEXT("Resources/Icon_Tool_%s.png"), *SafeToolId));
		}
	}
	CandidateRelativePaths.AddUnique(TEXT("Resources/Icon_UISettings.PNG"));

	if (const TSharedPtr<IPlugin> WorldBLDPlugin = IPluginManager::Get().FindPlugin(TEXT("WorldBLD")))
	{
		for (const FString& RelativePath : CandidateRelativePaths)
		{
			const FString FullPath = FPaths::ConvertRelativePathToFull(WorldBLDPlugin->GetBaseDir() / RelativePath);
			if (IFileManager::Get().FileExists(*FullPath))
			{
				TSharedPtr<FSlateBrush> NewBrush = MakeShared<FSlateDynamicImageBrush>(
					FName(*FullPath),
					FVector2D(
						WorldBLDToolSwitchMenuInternal::ToolIconExtent,
						WorldBLDToolSwitchMenuInternal::ToolIconExtent));
				ToolIconBrushes.Add(ToolKey, NewBrush);
				return NewBrush.Get();
			}
		}
	}

	return FAppStyle::GetBrush(TEXT("ClassThumbnail.Default"));
}

FString SWorldBLDToolSwitchMenu::NormalizeToolId(const FString& ToolName)
{
	const FString TrimmedName = ToolName.TrimStartAndEnd();
	static const TCHAR* KnownToolIds[] =
	{
		TEXT("WorldBLD"),
		TEXT("RoadBLD"),
		TEXT("CityBLD"),
		TEXT("TwinBLD"),
		TEXT("CrowdBLD")
	};

	for (const TCHAR* KnownToolId : KnownToolIds)
	{
		if (TrimmedName.Equals(KnownToolId, ESearchCase::IgnoreCase))
		{
			return KnownToolId;
		}
	}

	return TrimmedName;
}

bool SWorldBLDToolSwitchMenu::IsToolInstalled(const FString& ToolId) const
{
	return !ToolId.IsEmpty() && IPluginManager::Get().FindPlugin(ToolId).IsValid();
}

bool SWorldBLDToolSwitchMenu::IsToolInstalling(const FString& ToolId) const
{
	const UCurlDownloaderLibrary* DownloaderPtr = Downloader.Get();
	return (DownloaderPtr != nullptr) && !ToolId.IsEmpty() && DownloaderPtr->IsDownloadInProgress(ToolId);
}

FReply SWorldBLDToolSwitchMenu::HandleToolClicked(FString ToolId) const
{
	if (ToolId.IsEmpty())
	{
		return FReply::Handled();
	}

	UWorldBLDEdMode* EdModePtr = EdMode.Get();
	if (!IsValid(EdModePtr))
	{
		return FReply::Handled();
	}

	if (!IsToolInstalled(ToolId))
	{
		SWorldBLDPluginManager::ShowModalForTool(FName(*ToolId), EdMode, Downloader);
		return FReply::Handled();
	}

	// Swap the in-viewport toolbar to the selected plugin's toolbar (falls back to a
	// placeholder toolbar when the plugin hasn't registered one yet).
	EdModePtr->SwitchViewportToolbar(FName(*ToolId));

	return FReply::Handled();
}

FReply SWorldBLDToolSwitchMenu::HandleSwitchToWorldBLDClicked() const
{
	if (UWorldBLDEdMode* EdModePtr = EdMode.Get())
	{
		EdModePtr->SwitchViewportToolbar(TEXT("WorldBLD"));
		EdModePtr->SwitchToMainWorldBLDWidget();
	}
	return FReply::Handled();
}

FReply SWorldBLDToolSwitchMenu::HandleLoginClicked() const
{
	OnLoginClicked.ExecuteIfBound();
	return FReply::Handled();
}

FReply SWorldBLDToolSwitchMenu::HandleMoreToolsClicked()
{
	bShowMoreToolsPanel = !bShowMoreToolsPanel;
	RebuildMenuEntries();
	return FReply::Handled();
}

#undef LOCTEXT_NAMESPACE

