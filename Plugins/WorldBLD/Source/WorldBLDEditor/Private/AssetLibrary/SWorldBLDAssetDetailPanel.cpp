// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/SWorldBLDAssetDetailPanel.h"
#include "AssetLibrary/SWorldBLDAssetLibraryDetailHeader.h"
#include "AssetLibrary/SWorldBLDConfirmPurchaseModal.h"
#include "AssetLibrary/SWorldBLDDependencyRequiredModal.h"

#include "AssetLibrary/WorldBLDAssetDownloadManager.h"
#include "AssetLibrary/WorldBLDAssetEngineVersionUtils.h"
#include "AssetLibrary/WorldBLDAssetLibraryImageLoader.h"
#include "AssetLibrary/WorldBLDAssetLibrarySubsystem.h"
#include "Authorization/WorldBLDAuthSubsystem.h"
#include "Authorization/WorldBLDLoginWindow.h"
#include "ContextMenu/WorldBLDContextMenuFont.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"

#include "ContentBrowserModule.h"
#include "IContentBrowserSingleton.h"
#include "Modules/ModuleManager.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"

#include "Editor.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/PlatformProcess.h"
#include "Misc/MessageDialog.h"
#include "Interfaces/IPluginManager.h"
#include "WorldBLDEditorToolkit.h"
#include "Brushes/SlateDynamicImageBrush.h"
#include "Styling/AppStyle.h"
#include "Styling/SlateBrush.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SHyperlink.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Notifications/SProgressBar.h"

namespace
{
	static FSlateFontInfo MakeAppFont(const FName& FontStyleName, int32 Size)
	{
		FSlateFontInfo Font = FAppStyle::Get().GetFontStyle(FontStyleName);
		Font.Size = Size;
		return Font;
	}

	static FString ExtractAssetTypeLabelFromFeatures(const TArray<FString>& Features)
	{
		if (Features.Num() <= 0)
		{
			return FString();
		}

		const FString First = Features[0].TrimStartAndEnd();
		if (First.IsEmpty())
		{
			return FString();
		}

		static const FString Prefix = TEXT("Asset Type:");
		if (!First.StartsWith(Prefix, ESearchCase::IgnoreCase))
		{
			return FString();
		}

		FString TypeLabel = First.Mid(Prefix.Len()).TrimStartAndEnd();
		return TypeLabel;
	}

	static FString GetTypeBlurbForAssetTypeLabel(const FString& TypeLabel)
	{
		const FString Trimmed = TypeLabel.TrimStartAndEnd();
		if (Trimmed.IsEmpty())
		{
			return FString();
		}

		if (Trimmed.Equals(TEXT("Static Mesh"), ESearchCase::IgnoreCase))
		{
			return TEXT("A professionally crafted, game-ready static mesh asset, built to AAA optimization standards.");
		}

		if (Trimmed.Equals(TEXT("Static Mesh Collection"), ESearchCase::IgnoreCase))
		{
			return TEXT("A set of professionally crafted, game-ready static meshes designed to be assembled together.");
		}

		if (Trimmed.Equals(TEXT("WorldBLD Assembly"), ESearchCase::IgnoreCase))
		{
			return TEXT("A complete drag-and-drop assembly, saved as a WorldBLD Prefab Actor to maximize performance.");
		}

		if (Trimmed.Equals(TEXT("CityBLD Prefab"), ESearchCase::IgnoreCase))
		{
			return TEXT("A complete assembly for use with CityBLD tools, built to maximize performance.");
		}

		if (Trimmed.Equals(TEXT("CityBLD Building Style"), ESearchCase::IgnoreCase))
		{
			return TEXT("A fully configured Building Style for use with CityBLD. Just select this Style in any building's context menu to use it!");
		}

		if (Trimmed.Equals(TEXT("CityBLD District"), ESearchCase::IgnoreCase))
		{
			return TEXT("A fully configured District for use with CityBLD. Just select this District when you create a new City Block to use it!");
		}

		if (Trimmed.Equals(TEXT("RoadBLD Road Preset"), ESearchCase::IgnoreCase))
		{
			return TEXT("A fully configured Road Preset for use with RoadBLD.");
		}

		if (Trimmed.Equals(TEXT("RoadBLD Road Marking"), ESearchCase::IgnoreCase))
		{
			return TEXT("A Road Marking asset for RoadBLD. Use the Markings tool to select any slot on your road and assign this marking.");
		}

		if (Trimmed.Equals(TEXT("CityBLD Ground Floor"), ESearchCase::IgnoreCase))
		{
			return TEXT("A Ground Floor preset for use with CityBLD. Select any building in your level to assign this Ground Floor without affecting the upper floors. Sign text can be set per-building.");
		}

		if (Trimmed.Equals(TEXT("TwinBLD Customizer Script"), ESearchCase::IgnoreCase))
		{
			return TEXT("A Customizer Script for use with TwinBLD. This automatically assigns realistic styles to buildings and roads based on the map data. Select this Customizer when importing buildings, roads, or parcels.");
		}

		return FString();
	}

	static FSlateFontInfo GetCreditsLabelFont()
	{
		return WorldBLDContextMenuFont::GetThin(12.0f, 0);
	}

	static FSlateFontInfo GetCreditsValueFont()
	{
		return MakeAppFont(TEXT("BoldFont"), 12);
	}

	static FText CreditsToText(int32 Credits)
	{
		return FText::FromString(FString::Printf(TEXT("%d Credits"), Credits));
	}

	static FText StatusToText(EWorldBLDAssetStatus Status)
	{
		switch (Status)
		{
		case EWorldBLDAssetStatus::NotOwned:
			return FText::FromString(TEXT("Not Owned"));
		case EWorldBLDAssetStatus::Owned:
			return FText::FromString(TEXT("Owned"));
		case EWorldBLDAssetStatus::Downloading:
			return FText::FromString(TEXT("Downloading"));
		case EWorldBLDAssetStatus::Downloaded:
			return FText::FromString(TEXT("Downloaded"));
		case EWorldBLDAssetStatus::Imported:
			return FText::FromString(TEXT("Imported"));
		default:
			return FText::FromString(TEXT("Unknown"));
		}
	}

	static EWorldBLDAssetStatus GetStatusForSelection(TWeakObjectPtr<UWorldBLDAssetDownloadManager> DownloadManager, const FString& AssetId)
	{
		if (!DownloadManager.IsValid() || AssetId.IsEmpty())
		{
			return EWorldBLDAssetStatus::NotOwned;
		}
		return DownloadManager->GetAssetStatus(AssetId);
	}

	static bool ShowConfirmationModal(const FText& Title, const FText& Message, const FText& ConfirmText, const FText& CancelText)
	{
		bool bConfirmed = false;

		TSharedRef<SWindow> Dialog = SNew(SWindow)
			.Title(Title)
			.SizingRule(ESizingRule::Autosized)
			.SupportsMaximize(false)
			.SupportsMinimize(false);

		Dialog->SetContent(
			SNew(SBorder)
			.BorderImage(FAppStyle::Get().GetBrush("Brushes.Panel"))
			.Padding(FMargin(14.0f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(STextBlock)
					.Text(Message)
					.AutoWrapText(true)
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 14.0f, 0.0f, 0.0f))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					[
						SNew(SButton)
						.Text(CancelText)
						.OnClicked_Lambda([Dialog]()
						{
							Dialog->RequestDestroyWindow();
							return FReply::Handled();
						})
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.Padding(FMargin(10.0f, 0.0f, 0.0f, 0.0f))
					[
						SNew(SButton)
						.ButtonStyle(FAppStyle::Get(), "PrimaryButton")
						.Text(ConfirmText)
						.OnClicked_Lambda([Dialog, &bConfirmed]()
						{
							bConfirmed = true;
							Dialog->RequestDestroyWindow();
							return FReply::Handled();
						})
					]
				]
			]
		);

		FSlateApplication::Get().AddModalWindow(Dialog, FSlateApplication::Get().GetActiveTopLevelWindow());
		return bConfirmed;
	}

	static void ShowInfoModal(const FText& Title, const FText& Message)
	{
		TSharedRef<SWindow> Dialog = SNew(SWindow)
			.Title(Title)
			.SizingRule(ESizingRule::Autosized)
			.SupportsMaximize(false)
			.SupportsMinimize(false);

		Dialog->SetContent(
			SNew(SBorder)
			.BorderImage(FAppStyle::Get().GetBrush("Brushes.Panel"))
			.Padding(FMargin(14.0f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(STextBlock)
					.Text(Message)
					.AutoWrapText(true)
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 14.0f, 0.0f, 0.0f))
				.HAlign(HAlign_Right)
				[
					SNew(SButton)
					.ButtonStyle(FAppStyle::Get(), "PrimaryButton")
					.Text(FText::FromString(TEXT("OK")))
					.OnClicked_Lambda([Dialog]()
					{
						Dialog->RequestDestroyWindow();
						return FReply::Handled();
					})
				]
			]
		);

		FSlateApplication::Get().AddModalWindow(Dialog, FSlateApplication::Get().GetActiveTopLevelWindow());
	}

	static FText BuildImportFailureModalBody(const FString& AssetDisplayName, const FString& ImportErrorMessage)
	{
		const FString SafeAssetDisplayName = AssetDisplayName.IsEmpty() ? TEXT("Selected asset") : AssetDisplayName;
		const FString SafeImportError = ImportErrorMessage.IsEmpty() ? TEXT("Import failed for an unknown reason.") : ImportErrorMessage;
		const FString RecoverySteps =
			TEXT("Recommended steps:\n")
			TEXT("1) Close any open Material or Static Mesh editors.\n")
			TEXT("2) Save everything (File -> Save All).\n")
			TEXT("3) Restart the editor.\n")
			TEXT("4) Switch to a blank level and retry the import.");

		return FText::FromString(FString::Printf(
			TEXT("%s\n\n%s\n\n%s"),
			*SafeAssetDisplayName,
			*SafeImportError,
			*RecoverySteps));
	}

	static FText BuildMissingCacheImportModalBody(const FString& AssetDisplayName)
	{
		const FString SafeAssetDisplayName = AssetDisplayName.IsEmpty() ? TEXT("Selected asset") : AssetDisplayName;
		return FText::FromString(FString::Printf(
			TEXT("%s\n\n")
			TEXT("The local download cache for this asset is missing, so it cannot be imported right now.\n\n")
			TEXT("Use the Re-download link under Your Credits to download the asset again, then import."),
			*SafeAssetDisplayName));
	}

	static bool IsMissingCacheImportError(const FString& ImportErrorMessage)
	{
		return ImportErrorMessage.Contains(TEXT("cannot be imported. Download it first."), ESearchCase::IgnoreCase)
			|| ImportErrorMessage.Contains(TEXT("Failed to load cached import artifact"), ESearchCase::IgnoreCase)
			|| ImportErrorMessage.Contains(TEXT("Could not prepare mirrored import payload"), ESearchCase::IgnoreCase)
			|| ImportErrorMessage.Contains(TEXT("No local asset state found. Download the asset first."), ESearchCase::IgnoreCase);
	}

	static int32 ParseSemVerToSortableInt(const FString& InVersion)
	{
		// Converts "Major.Minor.Patch" into an integer for easy comparison.
		// We intentionally clamp to 3 components; any additional suffixes are ignored (e.g. "1.2.3-preview" -> 1.2.3).
		int32 Major = 0;
		int32 Minor = 0;
		int32 Patch = 0;

		const FString Clean = InVersion.TrimStartAndEnd();
		if (Clean.IsEmpty())
		{
			return 0;
		}

		TArray<FString> Parts;
		Clean.ParseIntoArray(Parts, TEXT("."), /*bCullEmpty=*/true);
		if (Parts.Num() > 0)
		{
			Major = FCString::Atoi(*Parts[0]);
		}
		if (Parts.Num() > 1)
		{
			Minor = FCString::Atoi(*Parts[1]);
		}
		if (Parts.Num() > 2)
		{
			// Strip any non-digit suffix from patch (e.g. "3-alpha" -> "3")
			FString PatchToken = Parts[2];
			int32 DigitCount = 0;
			while (DigitCount < PatchToken.Len() && FChar::IsDigit(PatchToken[DigitCount]))
			{
				++DigitCount;
			}
			if (DigitCount > 0)
			{
				PatchToken = PatchToken.Left(DigitCount);
				Patch = FCString::Atoi(*PatchToken);
			}
		}

		// Sortable representation. (1.0.5 => 10005, 1.0.10 => 10010)
		return (Major * 10000) + (Minor * 100) + Patch;
	}

	static bool TryExtractToolIdFromDownloadLink(const FString& DownloadLink, FString& OutToolId)
	{
		OutToolId.Reset();

		// Expected shape (from logs): https://worldbld.com/api/tools/<toolId>/download
		static const FString Marker = TEXT("/api/tools/");
		const int32 MarkerIndex = DownloadLink.Find(Marker, ESearchCase::IgnoreCase, ESearchDir::FromStart);
		if (MarkerIndex == INDEX_NONE)
		{
			return false;
		}

		const int32 AfterMarker = MarkerIndex + Marker.Len();
		if (AfterMarker >= DownloadLink.Len())
		{
			return false;
		}

		const int32 NextSlashIndex = DownloadLink.Find(TEXT("/"), ESearchCase::IgnoreCase, ESearchDir::FromStart, AfterMarker);
		if (NextSlashIndex == INDEX_NONE || NextSlashIndex <= AfterMarker)
		{
			return false;
		}

		OutToolId = DownloadLink.Mid(AfterMarker, NextSlashIndex - AfterMarker).TrimStartAndEnd();
		return !OutToolId.IsEmpty();
	}

	static FString ResolveToolNameFromToolId(const FString& ToolId, const TArray<FString>* AuthorizedTools)
	{
		const FString TrimmedId = ToolId.TrimStartAndEnd();
		if (TrimmedId.IsEmpty())
		{
			return FString();
		}

		// If the user is logged in, the licenses endpoint returns strings like:
		// "696d3c5a283db15c8d0ac174 | CityBLD"
		// This also includes WorldBLD, which the tools list intentionally filters out in the UI.
		// Note: for the "please download X first" path the user typically does NOT have a license
		// for X, so this source often misses — AvailableTools / ToolIdMap must cover that case.
		if (AuthorizedTools != nullptr)
		{
			for (const FString& Entry : *AuthorizedTools)
			{
				FString Left;
				FString Right;
				if (Entry.Split(TEXT("|"), &Left, &Right))
				{
					const FString EntryId = Left.TrimStartAndEnd();
					const FString EntryName = Right.TrimStartAndEnd();
					if (!EntryId.IsEmpty() && EntryId.Equals(TrimmedId, ESearchCase::IgnoreCase) && !EntryName.IsEmpty())
					{
						return EntryName;
					}
				}
			}
		}

		// Local fallback: if this machine has installed a tool (including via trial), the installer persists a mapping
		// from the server tool id to the local plugin name. Prefer this over license-only sources.
		if (GConfig)
		{
			FString MappedPluginName;
			if (GConfig->GetString(TEXT("WorldBLD.ToolIdMap"), *TrimmedId, MappedPluginName, GEditorPerProjectIni))
			{
				MappedPluginName = MappedPluginName.TrimStartAndEnd();
				if (!MappedPluginName.IsEmpty())
				{
					return MappedPluginName;
				}
			}
		}

		// Prefer the server tool list (public endpoint) cached on the WorldBLD EdMode when available.
		if (UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
		{
			// WorldBLD itself is intentionally filtered out of AvailableTools (UI), but we still cache its tool id.
			// If this required tool matches that cached id, resolve it to "WorldBLD" so gating works as intended.
			const FString& WorldBLDToolId = EdMode->GetServerWorldBLDToolId();
			if (!WorldBLDToolId.IsEmpty() && WorldBLDToolId.Equals(TrimmedId, ESearchCase::IgnoreCase))
			{
				return TEXT("WorldBLD");
			}

			for (const FPluginToolData& ToolData : EdMode->AvailableTools)
			{
				// Prefer the explicit server id from the tools payload; download-link parsing is a fallback
				// for older payloads that only embed the id in the URL.
				if (!ToolData.ServerId.IsEmpty() && ToolData.ServerId.Equals(TrimmedId, ESearchCase::IgnoreCase))
				{
					return ToolData.ToolName;
				}

				FString ParsedId;
				if (TryExtractToolIdFromDownloadLink(ToolData.DownloadLink, ParsedId)
					&& ParsedId.Equals(TrimmedId, ESearchCase::IgnoreCase))
				{
					return ToolData.ToolName;
				}
			}
		}

		// If the backend ever sends plugin names directly (instead of ids), accept them.
		if (IPluginManager::Get().FindPlugin(TrimmedId).IsValid())
		{
			return TrimmedId;
		}

		// Fallback: return the raw id (not ideal, but better than an empty string).
		return TrimmedId;
	}

	static bool IsPluginMountedAndEnabled(const FString& PluginName)
	{
		const FString TrimmedName = PluginName.TrimStartAndEnd();
		if (TrimmedName.IsEmpty())
		{
			return false;
		}

		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TrimmedName);
		if (!Plugin.IsValid())
		{
			return false;
		}

		// If it's not enabled, its content won't be mounted.
		return Plugin->IsEnabled();
	}

	static FString GetPluginVersionString(const FString& PluginName)
	{
		const FString TrimmedName = PluginName.TrimStartAndEnd();
		if (TrimmedName.IsEmpty())
		{
			return FString();
		}

		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TrimmedName);
		if (!Plugin.IsValid())
		{
			return FString();
		}

		const FString VersionName = Plugin->GetDescriptor().VersionName.TrimStartAndEnd();
		if (!VersionName.IsEmpty())
		{
			return VersionName;
		}

		const int32 Version = Plugin->GetDescriptor().Version;
		return Version > 0 ? FString::FromInt(Version) : FString();
	}
}

SWorldBLDAssetDetailPanel::~SWorldBLDAssetDetailPanel()
{
	if (ApplicationReactivatedHandle.IsValid())
	{
		FCoreDelegates::ApplicationHasReactivatedDelegate.Remove(ApplicationReactivatedHandle);
		ApplicationReactivatedHandle.Reset();
	}
}

void SWorldBLDAssetDetailPanel::Construct(const FArguments& InArgs)
{
	bIsKit = InArgs._bIsKit;
	CurrentAsset = InArgs._AssetInfo;
	CurrentKit = InArgs._KitInfo;
	OnCloseRequested  = InArgs._OnCloseRequested;
	OnResolvePackageIds = InArgs._OnResolvePackageIds;
	OnNavigateToAsset   = InArgs._OnNavigateToAsset;

	AssetLibrarySubsystem = GEditor ? GEditor->GetEditorSubsystem<UWorldBLDAssetLibrarySubsystem>() : nullptr;
	DownloadManager = GEditor ? GEditor->GetEditorSubsystem<UWorldBLDAssetDownloadManager>() : nullptr;
	AuthSubsystem = GEditor ? GEditor->GetEditorSubsystem<UWorldBLDAuthSubsystem>() : nullptr;

	// We want credits-based purchase gating to work without forcing the user to manually refresh.
	// ValidateSession() populates CachedUserCredits on success.
	if (AuthSubsystem.IsValid() && !AuthSubsystem->GetSessionToken().IsEmpty())
	{
		AuthSubsystem->ValidateSession();
	}

	// Keep credits reasonably fresh while the panel exists, and refresh after returning from an external browser flow.
	if (!CreditsRefreshTimerHandle.IsValid())
	{
		CreditsRefreshTimerHandle = RegisterActiveTimer(1.0f, FWidgetActiveTimerDelegate::CreateSP(this, &SWorldBLDAssetDetailPanel::HandleCreditsRefreshTick));
	}
	if (!ApplicationReactivatedHandle.IsValid())
	{
		ApplicationReactivatedHandle = FCoreDelegates::ApplicationHasReactivatedDelegate.AddSP(this, &SWorldBLDAssetDetailPanel::HandleApplicationHasReactivated);
	}

	// 300ms cubic in/out animation to match a modern "drawer" feel.
	ExpandCollapseAnimation = FCurveSequence(0.0f, 0.3f);
	ExpandCurve = ExpandCollapseAnimation.AddCurve(0.0f, 0.3f, ECurveEaseFunction::CubicInOut);

	// The panel is always present, but HeightOverride drives visibility/space.
	// We keep an overlay so the panel can have its own background.
	ChildSlot
	[
		SNew(SBox)
		.HeightOverride(this, &SWorldBLDAssetDetailPanel::GetAnimatedHeight)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::Get().GetBrush("Brushes.Panel"))
			// Title bar removed; reduce top padding so content aligns to the top edge.
			.Padding(FMargin(12.0f, 0.0f, 12.0f, 10.0f))
			.Clipping(EWidgetClipping::ClipToBoundsAlways)
			[
				SNew(SOverlay)
				+ SOverlay::Slot()
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.FillHeight(1.0f)
					[
						SAssignNew(DetailHeader, SWorldBLDAssetLibraryDetailHeader)
						[
							SNew(SVerticalBox)
							+ SVerticalBox::Slot()
							.FillHeight(1.0f)
							[
								SNew(SScrollBox)
								// Title moved to sidebar (next to preview image).
								+ SScrollBox::Slot()
								[
									SNew(STextBlock)
									.Text_Lambda([this]()
									{
										return bShowingFeatured ? FText::FromString(CurrentFeaturedCollection.Title) : GetTitleText();
									})
									.Font_Lambda([]()
									{
										FSlateFontInfo TitleFont = FAppStyle::Get().GetFontStyle("BoldFont");
										TitleFont.Size = 32;
										return TitleFont;
									})
									.ColorAndOpacity(FLinearColor(0.95f, 0.95f, 0.95f, 1.0f))
									.AutoWrapText(true)
								]
								+ SScrollBox::Slot()
								.Padding(FMargin(0.0f, 4.0f, 0.0f, 0.0f))
								[
									SNew(SHorizontalBox)
									.Visibility_Lambda([this]()
									{
										return (!bIsKit && !bShowingFeatured) ? EVisibility::Visible : EVisibility::Collapsed;
									})
									+ SHorizontalBox::Slot()
									.AutoWidth()
									.VAlign(VAlign_Center)
									[
										SNew(STextBlock)
										.Text(FText::FromString(TEXT("Created By: ")))
										.Font(GetCreditsLabelFont())
										.AutoWrapText(true)
									]
									+ SHorizontalBox::Slot()
									.FillWidth(1.0f)
									.VAlign(VAlign_Center)
									[
										SNew(STextBlock)
										.Text_Lambda([this]()
										{
											const FString Trimmed = CurrentAsset.Author.TrimStartAndEnd();
											return FText::FromString(Trimmed.IsEmpty() ? TEXT("WorldBLD") : Trimmed);
										})
										.Font(GetCreditsValueFont())
										.AutoWrapText(true)
									]
								]
							+ SScrollBox::Slot()
							.Padding(FMargin(0.0f, 12.0f, 0.0f, 0.0f))
							[
								SNew(STextBlock)
								.Text(this, &SWorldBLDAssetDetailPanel::GetDescriptionText)
								.AutoWrapText(true)
							]
							+ SScrollBox::Slot()
							.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
							[
								SNew(SBorder)
								.Visibility(this, &SWorldBLDAssetDetailPanel::GetThirdPartyNoticeVisibility)
								.BorderImage([]() -> const FSlateBrush*
								{
									static const FVector4 CornerRadii(4.0f, 4.0f, 4.0f, 4.0f);
									static const FSlateRoundedBoxBrush Brush = []()
									{
										FSlateRoundedBoxBrush RoundedBrush(FLinearColor(0.09f, 0.10f, 0.12f, 1.0f), CornerRadii);
										FSlateBrushOutlineSettings OutlineSettings;
										OutlineSettings.CornerRadii = CornerRadii;
										OutlineSettings.Color = FSlateColor(FLinearColor(0.28f, 0.56f, 0.87f, 0.7f));
										OutlineSettings.Width = 1.0f;
										OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
										OutlineSettings.bUseBrushTransparency = false;
										RoundedBrush.OutlineSettings = OutlineSettings;
										return RoundedBrush;
									}();
									return &Brush;
								}())
								.Padding(FMargin(10.0f, 8.0f))
								[
									SNew(SHorizontalBox)
								+ SHorizontalBox::Slot()
								.AutoWidth()
								.VAlign(VAlign_Center)
								.Padding(FMargin(0.0f, 0.0f, 7.0f, 0.0f))
								[
								SNew(SBox)
								.WidthOverride(28.0f)
								.HeightOverride(28.0f)
								[
									SNew(SImage)
									.Image([]() -> const FSlateBrush*
									{
										static TSharedPtr<FSlateDynamicImageBrush> InfoIconBrush;
										if (!InfoIconBrush.IsValid())
										{
											if (UTexture2D* IconTex = LoadObject<UTexture2D>(nullptr, TEXT("/WorldBLD/Textures/UIcircle-question.UIcircle-question")))
											{
												InfoIconBrush = MakeShared<FSlateDynamicImageBrush>(FName(*IconTex->GetPathName()), FVector2D(28.0f, 28.0f));
												InfoIconBrush->SetResourceObject(IconTex);
											}
										}
										return InfoIconBrush.IsValid() ? InfoIconBrush.Get() : FAppStyle::Get().GetDefaultBrush();
									}())
										.ColorAndOpacity(FLinearColor(0.40f, 0.68f, 0.95f, 1.0f))
									]
								]
									+ SHorizontalBox::Slot()
									.FillWidth(1.0f)
									[
										SNew(STextBlock)
										.Text(FText::FromString(TEXT("This asset is sold by a third party. It may be priced higher or designed with a different workflow. WorldBLD has verified it meets quality standards and integrates with the tools.")))
									.AutoWrapText(true)
									.ColorAndOpacity(FLinearColor(0.70f, 0.72f, 0.75f, 1.0f))
										.Font(WorldBLDContextMenuFont::GetThin(11.0f, 0))
									]
								]
							]
							+ SScrollBox::Slot()
							.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
							[
								SNew(SVerticalBox)
								.Visibility(this, &SWorldBLDAssetDetailPanel::GetEpicLicensingNoteVisibility)
								+ SVerticalBox::Slot()
								.AutoHeight()
								[
									SNew(SBorder)
									.BorderImage([]() -> const FSlateBrush*
									{
										static const FVector4 CornerRadii(4.0f, 4.0f, 4.0f, 4.0f);
										static const FSlateRoundedBoxBrush Brush = []()
										{
											FSlateRoundedBoxBrush RoundedBrush(FLinearColor(0.09f, 0.10f, 0.12f, 1.0f), CornerRadii);
											FSlateBrushOutlineSettings OutlineSettings;
											OutlineSettings.CornerRadii = CornerRadii;
											OutlineSettings.Color = FSlateColor(FLinearColor(0.28f, 0.56f, 0.87f, 0.7f));
											OutlineSettings.Width = 1.0f;
											OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
											OutlineSettings.bUseBrushTransparency = false;
											RoundedBrush.OutlineSettings = OutlineSettings;
											return RoundedBrush;
										}();
										return &Brush;
									}())
									.Padding(FMargin(10.0f, 8.0f))
									[
										SNew(SHorizontalBox)
										+ SHorizontalBox::Slot()
										.AutoWidth()
										.VAlign(VAlign_Center)
										.Padding(FMargin(0.0f, 0.0f, 7.0f, 0.0f))
										[
											SNew(SBox)
											.WidthOverride(28.0f)
											.HeightOverride(28.0f)
											[
												SNew(SImage)
												.Image([]() -> const FSlateBrush*
												{
													static TSharedPtr<FSlateDynamicImageBrush> EpicInfoIconBrush;
													if (!EpicInfoIconBrush.IsValid())
													{
														if (UTexture2D* IconTex = LoadObject<UTexture2D>(nullptr, TEXT("/WorldBLD/Textures/UIcircle-question.UIcircle-question")))
														{
															EpicInfoIconBrush = MakeShared<FSlateDynamicImageBrush>(FName(*IconTex->GetPathName()), FVector2D(28.0f, 28.0f));
															EpicInfoIconBrush->SetResourceObject(IconTex);
														}
													}
													return EpicInfoIconBrush.IsValid() ? EpicInfoIconBrush.Get() : FAppStyle::Get().GetDefaultBrush();
												}())
												.ColorAndOpacity(FLinearColor(0.40f, 0.68f, 0.95f, 1.0f))
											]
										]
										+ SHorizontalBox::Slot()
										.FillWidth(1.0f)
										[
											SNew(STextBlock)
											.Text(FText::FromString(TEXT("Licensing Note: This asset depends on free sample content from Epic.")))
											.AutoWrapText(true)
											.ColorAndOpacity(FLinearColor(0.70f, 0.72f, 0.75f, 1.0f))
											.Font(WorldBLDContextMenuFont::GetThin(11.0f, 0))
										]
									]
								]
								+ SVerticalBox::Slot()
								.AutoHeight()
								.Padding(FMargin(0.0f, 4.0f, 0.0f, 0.0f))
								[
									SNew(SHyperlink)
									.Text(FText::FromString(TEXT("Click here to view Epic's content license terms.")))
									.ToolTipText(FText::FromString(TEXT("https://www.unrealengine.com/eula/content")))
									.OnNavigate(this, &SWorldBLDAssetDetailPanel::HandleEpicLicensingNoteNavigate)
								]
							]
								// Dependency information section
								+ SScrollBox::Slot()
								.Padding(FMargin(0.0f, 12.0f, 0.0f, 0.0f))
								[
									SNew(STextBlock)
									.Text(this, &SWorldBLDAssetDetailPanel::GetDependencyInfoText)
									.Visibility(this, &SWorldBLDAssetDetailPanel::GetDependencyInfoVisibility)
									.ColorAndOpacity_Lambda([this]()
									{
										// Show yellow/warning color if there are missing dependencies (use cached values)
										if (!bIsKit && CurrentAsset.Manifest.Dependencies.Num() > 0 && bDependencyCacheValid)
										{
											if (CachedMissingDepsCount > 0)
											{
												return FSlateColor(FLinearColor(0.95f, 0.75f, 0.25f, 1.0f)); // Orange/yellow warning
											}
										}
										return FSlateColor(FLinearColor(0.7f, 0.7f, 0.7f, 1.0f)); // Gray
									})
									.AutoWrapText(true)
								]
							]
							+ SVerticalBox::Slot()
							.AutoHeight()
							.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
							[
								SNew(SVerticalBox)
								+ SVerticalBox::Slot()
								.AutoHeight()
								.Padding(FMargin(0.0f, 0.0f, 0.0f, 6.0f))
								[
									SNew(SOverlay)
									+ SOverlay::Slot()
									[
										SNew(SHorizontalBox)
										+ SHorizontalBox::Slot()
										.AutoWidth()
										.VAlign(VAlign_Center)
										[
											SNew(STextBlock)
											.Text(this, &SWorldBLDAssetDetailPanel::GetStatusText)
											.Visibility(this, &SWorldBLDAssetDetailPanel::GetStatusTextVisibility)
											.ColorAndOpacity(this, &SWorldBLDAssetDetailPanel::GetStatusColor)
											.Font_Lambda([]()
											{
												return WorldBLDContextMenuFont::GetMedium(16.0f, -10);
											})
										]
										+ SHorizontalBox::Slot()
										.FillWidth(1.0f)
										[
											SNew(SSpacer)
										]
										+ SHorizontalBox::Slot()
										.AutoWidth()
										.VAlign(VAlign_Center)
										[
											SNew(STextBlock)
											.Text_Lambda([this]()
											{
												return FText::FromString(GetPriceText().ToString().ToUpper());
											})
											.Visibility_Lambda([this]()
											{
												if (bShowingFeatured)
												{
													return EVisibility::Collapsed;
												}

												const FString AppId = GetCurrentAssetId();
												const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
												return Status == EWorldBLDAssetStatus::NotOwned ? EVisibility::Visible : EVisibility::Collapsed;
											})
											.ColorAndOpacity(this, &SWorldBLDAssetDetailPanel::GetStatusColor)
											.Font_Lambda([]()
											{
												return WorldBLDContextMenuFont::GetMedium(16.0f, -10);
											})
										]
									]
									+ SOverlay::Slot()
									[
										SNew(SButton)
										.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
										.Visibility(this, &SWorldBLDAssetDetailPanel::GetViewAssetButtonVisibility)
										.OnClicked(this, &SWorldBLDAssetDetailPanel::HandleViewAssetClicked)
										.HAlign(HAlign_Center)
										.VAlign(VAlign_Center)
										.ContentPadding(FMargin(3.0f))
										[
											SNew(STextBlock)
											.Text(FText::FromString(TEXT("View Asset")).ToUpper())
											.Font_Lambda([]()
											{
												// Match the Asset Status text font.
												return WorldBLDContextMenuFont::GetMedium(16.0f, -10);
											})
											.Justification(ETextJustify::Center)
										]
									]
								]
								+ SVerticalBox::Slot()
								.AutoHeight()
								[
									SNew(SVerticalBox)
									+ SVerticalBox::Slot()
									.AutoHeight()
									.HAlign(HAlign_Fill)
									[
										SNew(SVerticalBox)
										// Purchase button (full width)
										+ SVerticalBox::Slot()
										.AutoHeight()
										.HAlign(HAlign_Fill)
										.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
										[
											SNew(SButton)
											.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
											.Visibility(this, &SWorldBLDAssetDetailPanel::GetPurchaseButtonVisibility)
											.OnClicked(this, &SWorldBLDAssetDetailPanel::HandlePurchaseClicked)
											.HAlign(HAlign_Center)
											.VAlign(VAlign_Center)
											.ContentPadding(FMargin(3.0f))
											.IsEnabled_Lambda([this]()
											{
												return AreToolRequirementsSatisfied()
													&& AreEngineRequirementsSatisfied()
													&& (!UWorldBLDAuthSubsystem::IsLoggedIn() || AuthSubsystem.IsValid());
											})
											[
												SNew(STextBlock)
												.Text(this, &SWorldBLDAssetDetailPanel::GetPurchaseButtonText)
												.Font_Lambda([]()
												{
													// Match the Asset Status text font.
													return WorldBLDContextMenuFont::GetMedium(16.0f, -10);
												})
												.Justification(ETextJustify::Center)
											]
										]
										// Download button (full width)
										+ SVerticalBox::Slot()
										.AutoHeight()
										.HAlign(HAlign_Fill)
										.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
										[
											SNew(SButton)
											.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
											.Visibility(this, &SWorldBLDAssetDetailPanel::GetDownloadButtonVisibility)
											.OnClicked(this, &SWorldBLDAssetDetailPanel::HandleDownloadClicked)
											.HAlign(HAlign_Center)
											.VAlign(VAlign_Center)
											.ContentPadding(FMargin(3.0f))
											.IsEnabled_Lambda([this]()
											{
												const FString AppId = GetCurrentAssetId();
												return AreToolRequirementsSatisfied()
													&& AreEngineRequirementsSatisfied()
													&& DownloadManager.IsValid()
													&& !AppId.IsEmpty()
													&& !DownloadManager->IsDownloadInProgress(AppId);
											})
											[
												SNew(STextBlock)
												.Text(FText::FromString(TEXT("Download")).ToUpper())
												.Font_Lambda([]()
												{
													// Match the Asset Status text font.
													return WorldBLDContextMenuFont::GetMedium(16.0f, -10);
												})
												.Justification(ETextJustify::Center)
											]
										]
										// Download progress (below button, full width)
										+ SVerticalBox::Slot()
										.AutoHeight()
										.Padding(FMargin(0.0f, 6.0f, 0.0f, 0.0f))
										[
											SNew(SProgressBar)
											.Visibility(this, &SWorldBLDAssetDetailPanel::GetDownloadProgressVisibility)
											.Percent(this, &SWorldBLDAssetDetailPanel::GetDownloadProgressValue)
										]
										// Import button (full width)
										+ SVerticalBox::Slot()
										.AutoHeight()
										.HAlign(HAlign_Fill)
										.Padding(FMargin(0.0f, 8.0f, 0.0f, 0.0f))
										[
											SNew(SButton)
											.ButtonStyle(&WorldBLDContextMenuStyle::GetHighlightedButtonStyleNoOutline())
											.Visibility(this, &SWorldBLDAssetDetailPanel::GetImportButtonVisibility)
											.OnClicked(this, &SWorldBLDAssetDetailPanel::HandleImportClicked)
											.HAlign(HAlign_Center)
											.VAlign(VAlign_Center)
											.ContentPadding(FMargin(3.0f))
											.IsEnabled_Lambda([this]()
											{
												return AreToolRequirementsSatisfied()
													&& AreEngineRequirementsSatisfied();
											})
											[
												SNew(STextBlock)
												.Text_Lambda([this]()
												{
													const FString AppId = GetCurrentAssetId();
													const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
													return (Status == EWorldBLDAssetStatus::Imported)
														? FText::FromString(TEXT("Re-Import")).ToUpper()
														: FText::FromString(TEXT("Import")).ToUpper();
												})
												.Font_Lambda([]()
												{
													// Match the Asset Status text font.
													return WorldBLDContextMenuFont::GetMedium(16.0f, -10);
												})
												.Justification(ETextJustify::Center)
											]
										]
									]
									// Credits row now sits beneath the action button.
									+ SVerticalBox::Slot()
									.AutoHeight()
									.Padding(FMargin(0.0f, 10.0f, 0.0f, 0.0f))
									[
										SNew(SHorizontalBox)
										+ SHorizontalBox::Slot()
										.FillWidth(1.0f)
										[
											SNew(SSpacer)
										]
										+ SHorizontalBox::Slot()
										.AutoWidth()
										.VAlign(VAlign_Center)
										[
											SNew(STextBlock)
											.Text(FText::FromString(TEXT("Your Credits: ")))
											.Font(GetCreditsLabelFont())
										]
										+ SHorizontalBox::Slot()
										.AutoWidth()
										.VAlign(VAlign_Center)
										[
											SNew(STextBlock)
											.Text_Lambda([this]()
											{
												return FText::AsNumber(AuthSubsystem.IsValid() ? AuthSubsystem->GetUserCredits() : 0);
											})
											.Font(GetCreditsValueFont())
										]
										+ SHorizontalBox::Slot()
										.AutoWidth()
										.VAlign(VAlign_Center)
										.Padding(FMargin(10.0f, 0.0f, 0.0f, 0.0f))
										[
										SNew(SHyperlink)
										.Text(this, &SWorldBLDAssetDetailPanel::GetCacheActionText)
										.ToolTipText(this, &SWorldBLDAssetDetailPanel::GetCacheActionToolTipText)
										.Visibility(this, &SWorldBLDAssetDetailPanel::GetDeleteCacheVisibility)
										.IsEnabled(this, &SWorldBLDAssetDetailPanel::CanUseCacheAction)
										.OnNavigate(this, &SWorldBLDAssetDetailPanel::HandleCacheActionClicked)
										]
									]
								]
						]
					]
				]
			]
		]
	]
	];

	if (DetailHeader.IsValid())
	{
		DetailHeader->SetPreviewUrls(bIsKit ? CurrentKit.PreviewImages : CurrentAsset.PreviewImages);
	}

	const FString InitialThumbnailURL = bIsKit
		? (CurrentKit.PreviewImages.Num() > 0 ? CurrentKit.PreviewImages[0] : FString())
		: CurrentAsset.ThumbnailURL;
	BeginLoadThumbnailBrush(InitialThumbnailURL);

	// By default, start collapsed.
	bIsExpanded = false;
}

EActiveTimerReturnType SWorldBLDAssetDetailPanel::HandleCreditsRefreshTick(double CurrentTime, float DeltaTime)
{
	(void)DeltaTime;

	// Only poll while the panel is visible/open to keep network usage minimal.
	if (bIsExpanded && AuthSubsystem.IsValid() && !AuthSubsystem->GetSessionToken().IsEmpty())
	{
		const double Last = LastCreditsRefreshRequestTimeSeconds;
		const double Elapsed = (Last < 0.0) ? BIG_NUMBER : (CurrentTime - Last);
		if (Elapsed >= CreditsRefreshIntervalSeconds)
		{
			RequestCreditsRefreshFromServer(/*bForce=*/false);
		}
	}

	return EActiveTimerReturnType::Continue;
}

void SWorldBLDAssetDetailPanel::RequestCreditsRefreshFromServer(bool bForce)
{
	if (!AuthSubsystem.IsValid() || AuthSubsystem->GetSessionToken().IsEmpty())
	{
		return;
	}

	const double Now = FPlatformTime::Seconds();
	if (!bForce && LastCreditsRefreshRequestTimeSeconds >= 0.0 && (Now - LastCreditsRefreshRequestTimeSeconds) < CreditsRefreshMinGapSeconds)
	{
		return;
	}

	LastCreditsRefreshRequestTimeSeconds = Now;
	AuthSubsystem->ValidateSession(); // Uses GET /api/auth/desktop/session (same endpoint as on widget construction).
}

void SWorldBLDAssetDetailPanel::HandleApplicationHasReactivated()
{
	if (!bPendingCreditsRefreshOnAppFocus)
	{
		return;
	}

	bPendingCreditsRefreshOnAppFocus = false;
	RequestCreditsRefreshFromServer(/*bForce=*/true);
}

void SWorldBLDAssetDetailPanel::SetHostHeight(float InHostHeight)
{
	CachedHostHeight = FMath::Max(0.0f, InHostHeight);
}

void SWorldBLDAssetDetailPanel::ShowAsset(const FWorldBLDAssetInfo& Asset)
{
	bShowingFeatured = false;
	bIsKit = false;
	CurrentAsset = Asset;
	CurrentKit = FWorldBLDKitInfo();

	// Invalidate dependency cache when switching assets
	bDependencyCacheValid = false;
	BeginLoadPreviewImages(CurrentAsset.PreviewImages);
	BeginLoadThumbnailBrush(CurrentAsset.ThumbnailURL);
	EvaluateToolRequirements(/*bShowDialogIfUnmet=*/true);
	EvaluateEngineRequirements(/*bShowDialogIfUnmet=*/true);

	// If the list item is missing richer fields, trigger a detail fetch.
	if (AssetLibrarySubsystem.IsValid() && !CurrentAsset.ID.IsEmpty())
	{
		AssetLibrarySubsystem->FetchAssetDetails(CurrentAsset.ID);
	}
}

void SWorldBLDAssetDetailPanel::ShowKit(const FWorldBLDKitInfo& Kit)
{
	bShowingFeatured = false;
	bIsKit = true;
	CurrentKit = Kit;
	CurrentAsset = FWorldBLDAssetInfo();
	BeginLoadPreviewImages(CurrentKit.PreviewImages);
	BeginLoadThumbnailBrush(CurrentKit.PreviewImages.Num() > 0 ? CurrentKit.PreviewImages[0] : FString());

	if (AssetLibrarySubsystem.IsValid() && !CurrentKit.ID.IsEmpty())
	{
		AssetLibrarySubsystem->FetchKitDetails(CurrentKit.ID);
	}
}

void SWorldBLDAssetDetailPanel::ShowFeaturedContent(const FWorldBLDFeaturedCollection& Collection)
{
	// The initial implementation just shows the collection header. Actual featured tiles will be wired later.
	bShowingFeatured = true;
	CurrentFeaturedCollection = Collection;

	BeginLoadPreviewImages({});
}

void SWorldBLDAssetDetailPanel::Expand()
{
	// Idempotent: switching the selected asset while the panel is already open should not replay the expansion.
	// Ensure we end up fully expanded, even if the animation was interrupted.
	if (bIsExpanded)
	{
		ExpandCollapseAnimation.JumpToEnd();
		return;
	}

	bIsExpanded = true;
	ExpandCollapseAnimation.Play(this->AsShared());
}

void SWorldBLDAssetDetailPanel::Collapse()
{
	// Idempotent collapse for safety (e.g., multiple collapse calls from different UX triggers).
	if (!bIsExpanded)
	{
		ExpandCollapseAnimation.JumpToStart();
		return;
	}

	bIsExpanded = false;
	ExpandCollapseAnimation.PlayReverse(this->AsShared());

	// We intentionally do not clear data immediately. This avoids flicker while the animation is still visible.
	// Data can be cleared lazily if needed, but keeping it enables re-open without re-fetching.
}

void SWorldBLDAssetDetailPanel::CheckScrollPosition(float ScrollOffset)
{
	// User experience rule: if the user starts exploring the grid, we get the detail panel out of the way.
	static constexpr float CollapseThreshold = 100.0f;
	if (bIsExpanded && ScrollOffset > CollapseThreshold)
	{
		Collapse();
	}
}

void SWorldBLDAssetDetailPanel::HandleAssetDetailsFetched(const FWorldBLDAssetInfo& Asset)
{
	if (bIsKit)
	{
		return;
	}
	if (!CurrentAsset.ID.IsEmpty() && Asset.ID == CurrentAsset.ID)
	{
		CurrentAsset = Asset;
		bDependencyCacheValid = false; // Invalidate cache when asset details are fetched
		BeginLoadPreviewImages(CurrentAsset.PreviewImages);
		BeginLoadThumbnailBrush(CurrentAsset.ThumbnailURL);
		EvaluateToolRequirements(/*bShowDialogIfUnmet=*/true);
		EvaluateEngineRequirements(/*bShowDialogIfUnmet=*/true);
	}
}

void SWorldBLDAssetDetailPanel::HandleKitDetailsFetched(const FWorldBLDKitInfo& Kit)
{
	if (!bIsKit)
	{
		return;
	}
	if (!CurrentKit.ID.IsEmpty() && Kit.ID == CurrentKit.ID)
	{
		CurrentKit = Kit;
		BeginLoadPreviewImages(CurrentKit.PreviewImages);
		BeginLoadThumbnailBrush(CurrentKit.PreviewImages.Num() > 0 ? CurrentKit.PreviewImages[0] : FString());
	}
}

void SWorldBLDAssetDetailPanel::HandlePurchaseComplete(bool bSuccess, int32 RemainingCredits)
{
	(void)RemainingCredits;

	// Always refresh credits from the server after a successful purchase, using the same session endpoint
	// used when constructing the widget (do not rely on "remaining credits" responses).
	if (bSuccess)
	{
		RequestCreditsRefreshFromServer(/*bForce=*/true);
	}
}

void SWorldBLDAssetDetailPanel::HandleImportComplete(const FString& AssetId, bool bSuccess)
{
	// Only react if the import corresponds to the item currently shown in this panel.
	if (AssetId.IsEmpty() || AssetId != GetCurrentAssetId())
	{
		return;
	}

	if (!bSuccess)
	{
		FString ErrorMessage = TEXT("Import failed for an unknown reason.");
		FString ManagerError;
		if (DownloadManager.IsValid() && DownloadManager->GetLastImportError(AssetId, ManagerError) && !ManagerError.IsEmpty())
		{
			ErrorMessage = ManagerError;
		}

		const bool bMissingCache =
			(DownloadManager.IsValid() && !DownloadManager->HasLocalCache(AssetId))
			|| IsMissingCacheImportError(ErrorMessage);

		if (bMissingCache)
		{
			const FText Title = FText::FromString(TEXT("Cache Missing"));
			const FText Body = BuildMissingCacheImportModalBody(GetTitleText().ToString());
			ShowInfoModal(Title, Body);
			return;
		}

		const FText Title = FText::FromString(TEXT("Import Failed"));
		const FText Body = BuildImportFailureModalBody(GetTitleText().ToString(), ErrorMessage);
		ShowInfoModal(Title, Body);
		return;
	}

	// Invalidate dependency cache after import completes
	bDependencyCacheValid = false;

	// Sync the Content Browser to the imported content so the user can immediately find it.
	// Note: the download manager imports into a sanitized folder like "<SanitizedAssetName>_<AssetId>",
	// so we must query the actual imported package root from the manager (not assume it's just <AssetId>).
	FString ImportedPackageRoot;
	if (!DownloadManager.IsValid() || !DownloadManager->GetImportedPackageRoot(AssetId, ImportedPackageRoot))
	{
		return;
	}

	FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>(TEXT("ContentBrowser"));
	IContentBrowserSingleton& ContentBrowser = ContentBrowserModule.Get();

	// Prefer selecting an actual asset (high-signal UX). Fallback to opening the folder if no assets are found yet.
	IAssetRegistry& AssetRegistry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
	TArray<FAssetData> ImportedAssets;
	AssetRegistry.GetAssetsByPath(FName(*ImportedPackageRoot), ImportedAssets, /*bRecursive=*/false);

	if (ImportedAssets.Num() > 0)
	{
		TArray<FAssetData> ToSync;
		ToSync.Add(ImportedAssets[0]);
		ContentBrowser.SyncBrowserToAssets(ToSync);
	}
	else
	{
		ContentBrowser.SyncBrowserToFolders({ ImportedPackageRoot }, /*bAllowLockedBrowsers=*/true, /*bFocusContentBrowser=*/true);
	}
}

FReply SWorldBLDAssetDetailPanel::HandlePurchaseClicked()
{

	if (!AssetLibrarySubsystem.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[HandlePurchaseClicked] AssetLibrarySubsystem is invalid"));
		return FReply::Handled();
	}

	if (!UWorldBLDAuthSubsystem::IsLoggedIn())
	{
		FWorldBLDLoginWindow::OpenLoginDialog();
		return FReply::Handled();
	}

	// Tool gating: keep actions disabled when required tools/versions are missing.
	EvaluateToolRequirements(/*bShowDialogIfUnmet=*/true);
	if (!AreToolRequirementsSatisfied())
	{
		return FReply::Handled();
	}

	EvaluateEngineRequirements(/*bShowDialogIfUnmet=*/true);
	if (!AreEngineRequirementsSatisfied())
	{
		return FReply::Handled();
	}

	if (!bIsKit)
	{
		TArray<FString> MissingIds;
		GetMissingExternalPackageDependencies(MissingIds);
		if (MissingIds.Num() > 0)
		{
			ShowDependencyRequiredModal(MissingIds);
			return FReply::Handled();
		}
	}

	// If the user doesn't have enough credits:
	// - If they have an active subscription, route them to buy credits.
	// - Otherwise (including trial / no subscription), route them to choose a plan to avoid confusion.
	if (!HasSufficientCredits())
	{
		static const TCHAR* PurchaseCreditsUrl = TEXT("https://worldbld.com/purchase-credits");
		static const TCHAR* PlansUrl = TEXT("https://www.worldbld.com/plans");

		bPendingCreditsRefreshOnAppFocus = true;
		FPlatformProcess::LaunchURL(HasActiveSubscription() ? PurchaseCreditsUrl : PlansUrl, nullptr, nullptr);
		return FReply::Handled();
	}

	// Get the asset/kit ID for purchase
	FString AssetIdForPurchase = bIsKit ? CurrentKit.ID : CurrentAsset.ID;
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[HandlePurchaseClicked] bIsKit: %s"), bIsKit ? TEXT("true") : TEXT("false"));
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[HandlePurchaseClicked] Asset/Kit ID: '%s'"), *AssetIdForPurchase);

	if (AssetIdForPurchase.IsEmpty())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[HandlePurchaseClicked] Asset ID is empty, cannot purchase"));
		return FReply::Handled();
	}

	TSharedRef<SWindow> Dialog = SNew(SWindow)
		.Title(FText::FromString(TEXT("Confirm Purchase")))
		.SizingRule(ESizingRule::Autosized)
		.SupportsMaximize(false)
		.SupportsMinimize(false);

	const FString ItemName = GetTitleText().ToString();
	const int32 UserCredits = AuthSubsystem.IsValid() ? AuthSubsystem->GetUserCredits() : 0;
	const int32 PriceCredits = GetCurrentPriceCredits();
	const bool bCurrentSelectionIsFree = bIsKit ? CurrentKit.bIsFree : CurrentAsset.bIsFree;

	const FSlateBrush* PurchaseModalBrush = ThumbnailBrush.IsValid() ? ThumbnailBrush.Get() : GetCurrentPreviewBrush();

	Dialog->SetContent(
		SNew(SWorldBLDConfirmPurchaseModal)
		.ItemName(ItemName)
		.PriceCredits(PriceCredits)
		.bIsFree(bCurrentSelectionIsFree)
		.UserCredits(UserCredits)
		.PreviewBrush(PurchaseModalBrush)
		.OnCancel(FSimpleDelegate::CreateLambda([Dialog]()
		{
			Dialog->RequestDestroyWindow();
		}))
		.OnConfirm(FSimpleDelegate::CreateLambda([this, Dialog, AssetIdForPurchase]()
		{
			Dialog->RequestDestroyWindow();
			if (AssetLibrarySubsystem.IsValid())
			{
				// Use asset/kit ID for purchase - Backend expects the MongoDB _id in the asset_id field
				UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[HandlePurchaseClicked] Calling PurchaseAsset with ID: '%s'"), *AssetIdForPurchase);
				AssetLibrarySubsystem->PurchaseAsset(AssetIdForPurchase);
			}
		}))
	);

	FSlateApplication::Get().AddModalWindow(Dialog, FSlateApplication::Get().GetActiveTopLevelWindow());
	return FReply::Handled();
}

FReply SWorldBLDAssetDetailPanel::HandleDownloadClicked()
{
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[HandleDownloadClicked] Download button clicked"));

	if (!DownloadManager.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[HandleDownloadClicked] DownloadManager is invalid"));
		return FReply::Handled();
	}

	if (!AssetLibrarySubsystem.IsValid())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[HandleDownloadClicked] AssetLibrarySubsystem is invalid"));
		return FReply::Handled();
	}

	// Tool gating
	EvaluateToolRequirements(/*bShowDialogIfUnmet=*/true);
	if (!AreToolRequirementsSatisfied())
	{
		return FReply::Handled();
	}

	EvaluateEngineRequirements(/*bShowDialogIfUnmet=*/true);
	if (!AreEngineRequirementsSatisfied())
	{
		return FReply::Handled();
	}

	const FString AssetId = GetCurrentAssetId();
	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[HandleDownloadClicked] Asset ID: '%s'"), *AssetId);

	if (AssetId.IsEmpty())
	{
		UE_LOG(LogWorldBLDAssetLibrary, Error, TEXT("[HandleDownloadClicked] Asset ID is empty"));
		return FReply::Handled();
	}

	// Dependency checking can be expensive on large assets. Keep it lazy so browsing stays smooth,
	// and only compute when the user explicitly initiates an action.
	RefreshDependencyCache();

	if (!bIsKit && CurrentAsset.IsMirrorAsset() && !AreExternalPackageDependenciesOwned(/*bShowDialogIfMissing=*/true))
	{
		return FReply::Handled();
	}

	if (!bIsKit && !CurrentAsset.IsMirrorAsset())
	{
		const bool bContinue = ShowConfirmationModal(
			FText::FromString(TEXT("Legacy Asset Format")),
			FText::FromString(TEXT("This asset uses an older format. The download size may be larger than expected.")),
			FText::FromString(TEXT("Continue")),
			FText::FromString(TEXT("Cancel")));
		if (!bContinue)
		{
			return FReply::Handled();
		}
	}

	// Request signed download URL from backend
	// The backend will verify ownership and return a temporary download URL
	AssetLibrarySubsystem->RequestDownloadURL(AssetId, bIsKit);

	UE_LOG(LogWorldBLDAssetLibrary, Log, TEXT("[HandleDownloadClicked] Requested download URL from backend"));
	return FReply::Handled();
}

FReply SWorldBLDAssetDetailPanel::HandleImportClicked()
{
	if (!DownloadManager.IsValid())
	{
		return FReply::Handled();
	}

	// Tool gating
	EvaluateToolRequirements(/*bShowDialogIfUnmet=*/true);
	if (!AreToolRequirementsSatisfied())
	{
		return FReply::Handled();
	}

	EvaluateEngineRequirements(/*bShowDialogIfUnmet=*/true);
	if (!AreEngineRequirementsSatisfied())
	{
		return FReply::Handled();
	}

	const FString AppId = GetCurrentAssetId();
	if (AppId.IsEmpty())
	{
		return FReply::Handled();
	}

	// Dependency checking can be expensive on large assets. Keep it lazy so browsing stays smooth,
	// and only compute when the user explicitly initiates an action.
	RefreshDependencyCache();

	if (!bIsKit && CurrentAsset.IsMirrorAsset() && !AreExternalPackageDependenciesOwned(/*bShowDialogIfMissing=*/true))
	{
		return FReply::Handled();
	}

	if (DownloadManager.IsValid() && !DownloadManager->HasLocalCache(AppId))
	{
		const FText Title = FText::FromString(TEXT("Cache Missing"));
		const FText Body = BuildMissingCacheImportModalBody(GetTitleText().ToString());
		ShowInfoModal(Title, Body);
		return FReply::Handled();
	}

	if (!DownloadManager->ImportAsset(AppId))
	{
		FString ErrorMessage = TEXT("Import could not be started.");
		FString ManagerError;
		if (DownloadManager->GetLastImportError(AppId, ManagerError) && !ManagerError.IsEmpty())
		{
			ErrorMessage = ManagerError;
		}

		if (IsMissingCacheImportError(ErrorMessage) || !DownloadManager->HasLocalCache(AppId))
		{
			const FText Title = FText::FromString(TEXT("Cache Missing"));
			const FText Body = BuildMissingCacheImportModalBody(GetTitleText().ToString());
			ShowInfoModal(Title, Body);
		}
		else
		{
			const FText Title = FText::FromString(TEXT("Import Failed"));
			const FText Body = BuildImportFailureModalBody(GetTitleText().ToString(), ErrorMessage);
			ShowInfoModal(Title, Body);
		}
	}
	return FReply::Handled();
}

FReply SWorldBLDAssetDetailPanel::HandleViewAssetClicked()
{
	if (bShowingFeatured || bIsKit)
	{
		return FReply::Handled();
	}

	const FString AppId = GetCurrentAssetId();
	if (AppId.IsEmpty())
	{
		return FReply::Handled();
	}

	FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>(TEXT("ContentBrowser"));
	IContentBrowserSingleton& ContentBrowser = ContentBrowserModule.Get();
	IAssetRegistry& AssetRegistry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();

	auto TrySyncToPrimaryAssetPath = [&ContentBrowser, &AssetRegistry](const FString& InPath) -> bool
	{
		const FString Trimmed = InPath.TrimStartAndEnd();
		if (Trimmed.IsEmpty())
		{
			return false;
		}

		// Try to resolve a full object-path string to an asset and sync the content browser to it.
		auto TrySyncToObjectPath = [&ContentBrowser, &AssetRegistry](const FString& ObjectPath) -> bool
		{
			const FSoftObjectPath SoftPath(ObjectPath);
			if (!SoftPath.IsValid())
			{
				return false;
			}
			FAssetData AssetData = AssetRegistry.GetAssetByObjectPath(SoftPath);
			if (!AssetData.IsValid())
			{
				UObject* Loaded = SoftPath.TryLoad();
				if (IsValid(Loaded))
				{
					AssetData = FAssetData(Loaded);
				}
			}
			if (AssetData.IsValid())
			{
				ContentBrowser.SyncBrowserToAssets({ AssetData });
				return true;
			}
			return false;
		};

		// Try 1: path as supplied (handles the canonical "/Game/A/B/Asset.Asset" form).
		if (TrySyncToObjectPath(Trimmed))
		{
			return true;
		}

		int32 DotIndex = INDEX_NONE;
		const bool bHasDot = Trimmed.FindChar(TEXT('.'), DotIndex) && DotIndex > 0;

		if (bHasDot)
		{
			// The backend sometimes encodes the path as "ContainerFolder.AssetName" instead of the
			// canonical "ContainerFolder/AssetName.AssetName". Reconstruct the correct form and retry.
			// e.g. "/Game/A/WorldBLD.BS_Foo" → "/Game/A/WorldBLD/BS_Foo.BS_Foo"
			const FString PackagePart   = Trimmed.Left(DotIndex);
			const FString AssetNamePart = Trimmed.Mid(DotIndex + 1);
			if (!AssetNamePart.IsEmpty() && !AssetNamePart.Contains(TEXT("/")))
			{
				if (TrySyncToObjectPath(FString::Printf(TEXT("%s/%s.%s"), *PackagePart, *AssetNamePart, *AssetNamePart)))
				{
					return true;
				}
			}
		}
		else
		{
			// Try 2: bare package path with no dot (e.g. "/Game/A/B/Asset").
			// Retry with the canonical "Package.AssetName" dot form (last component repeated).
			const FString LastComp = FPaths::GetBaseFilename(Trimmed);
			if (!LastComp.IsEmpty())
			{
				if (TrySyncToObjectPath(FString::Printf(TEXT("%s.%s"), *Trimmed, *LastComp)))
				{
					return true;
				}
			}
		}

		// All asset lookups failed: fall back to folder navigation so the user at least lands in the
		// right area of the content browser.
		//
		// Path format guide for the folder fallback:
		//   "/Game/A/B/Asset.Asset"         → strip dot → "/Game/A/B/Asset"   → GetLongPackagePath → "/Game/A/B"
		//   "/Game/A/WorldBLD.BS_Foo"        → strip dot → "/Game/A/WorldBLD"  → use directly (it IS the containing folder)
		//   "/Game/A/B"   (bare folder path) → no dot    → use directly        → "/Game/A/B"
		//   "/Game/A/B/Asset" (bare package) → no dot    → GetLongPackagePath  → "/Game/A/B"
		//
		// The critical distinction: when a dot is present, PackagePart ("/Game/A/WorldBLD" or "/Game/A/B/Asset")
		// may itself be the folder containing the asset, so prefer it over stripping another level.
		// When no dot, use GetLongPackagePath to strip the final component (which is the asset/package name).
		FString FolderPath;
		if (bHasDot)
		{
			FolderPath = Trimmed.Left(DotIndex); // PackagePart — the folder that contains the asset
		}
		else
		{
			// No dot: path is either a folder or a bare package name; GetLongPackagePath gives the parent.
			FolderPath = FPackageName::GetLongPackagePath(Trimmed);
		}

		if (!FolderPath.IsEmpty() && FPackageName::IsValidLongPackageName(FolderPath))
		{
			ContentBrowser.SyncBrowserToFolders({ FolderPath }, /*bAllowLockedBrowsers=*/true, /*bFocusContentBrowser=*/true);
			return true;
		}

		return false;
	};

	// Primary behavior: use the first PrimaryAssets entry from the API.
	if (CurrentAsset.PrimaryAssets.Num() > 0 && TrySyncToPrimaryAssetPath(CurrentAsset.PrimaryAssets[0]))
	{
		return FReply::Handled();
	}

	// Fallback: if we can resolve the imported root, open that folder.
	FString ImportedPackageRoot;
	if (DownloadManager.IsValid() && DownloadManager->GetImportedPackageRoot(AppId, ImportedPackageRoot) && !ImportedPackageRoot.IsEmpty())
	{
		ContentBrowser.SyncBrowserToFolders({ ImportedPackageRoot }, /*bAllowLockedBrowsers=*/true, /*bFocusContentBrowser=*/true);
		return FReply::Handled();
	}

	// Final fallback: try the first manifest dependency package path if present.
	if (CurrentAsset.Manifest.Dependencies.Num() > 0 && TrySyncToPrimaryAssetPath(CurrentAsset.Manifest.Dependencies[0].PackagePath))
	{
		return FReply::Handled();
	}

	return FReply::Handled();
}

EVisibility SWorldBLDAssetDetailPanel::GetPurchaseButtonVisibility() const
{
	if (bShowingFeatured)
	{
		return EVisibility::Collapsed;
	}

	const FString AppId = GetCurrentAssetId();
	const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
	return Status == EWorldBLDAssetStatus::NotOwned ? EVisibility::Visible : EVisibility::Collapsed;
}

EVisibility SWorldBLDAssetDetailPanel::GetDownloadButtonVisibility() const
{
	if (bShowingFeatured)
	{
		return EVisibility::Collapsed;
	}
	const FString AppId = GetCurrentAssetId();
	const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
	return Status == EWorldBLDAssetStatus::Owned || Status == EWorldBLDAssetStatus::Downloading ? EVisibility::Visible : EVisibility::Collapsed;
}

EVisibility SWorldBLDAssetDetailPanel::GetImportButtonVisibility() const
{
	if (bShowingFeatured)
	{
		return EVisibility::Collapsed;
	}
	const FString AppId = GetCurrentAssetId();
	const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
	return (Status == EWorldBLDAssetStatus::Downloaded || Status == EWorldBLDAssetStatus::Imported)
		? EVisibility::Visible
		: EVisibility::Collapsed;
}

EVisibility SWorldBLDAssetDetailPanel::GetDeleteCacheVisibility() const
{
	if (bShowingFeatured || bIsKit)
	{
		return EVisibility::Collapsed;
	}

	const FString AppId = GetCurrentAssetId();
	const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);

	return (Status == EWorldBLDAssetStatus::Downloaded || Status == EWorldBLDAssetStatus::Imported)
		? EVisibility::Visible
		: EVisibility::Collapsed;
}

bool SWorldBLDAssetDetailPanel::CanDeleteCache() const
{
	if (bShowingFeatured || bIsKit)
	{
		return false;
	}

	const FString AppId = GetCurrentAssetId();
	if (AppId.IsEmpty() || !DownloadManager.IsValid())
	{
		return false;
	}

	const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
	if (Status != EWorldBLDAssetStatus::Downloaded && Status != EWorldBLDAssetStatus::Imported)
	{
		return false;
	}

	return DownloadManager->HasLocalCache(AppId);
}

bool SWorldBLDAssetDetailPanel::ShouldShowRedownloadAction() const
{
	if (bShowingFeatured || bIsKit || !DownloadManager.IsValid())
	{
		return false;
	}

	const FString AppId = GetCurrentAssetId();
	if (AppId.IsEmpty())
	{
		return false;
	}

	const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
	if (Status != EWorldBLDAssetStatus::Imported && Status != EWorldBLDAssetStatus::Downloaded)
	{
		return false;
	}

	return !DownloadManager->HasLocalCache(AppId);
}

FText SWorldBLDAssetDetailPanel::GetCacheActionText() const
{
	return ShouldShowRedownloadAction()
		? FText::FromString(TEXT("Re-download"))
		: FText::FromString(TEXT("Delete Cache"));
}

FText SWorldBLDAssetDetailPanel::GetCacheActionToolTipText() const
{
	if (ShouldShowRedownloadAction())
	{
		return FText::FromString(TEXT("Local cache is missing. Re-download this asset so you can import it again. Imported content in your project is not affected."));
	}

	return FText::FromString(TEXT("Delete cached download files for this asset. Imported content in your project is not affected."));
}

bool SWorldBLDAssetDetailPanel::CanUseCacheAction() const
{
	if (ShouldShowRedownloadAction())
	{
		const FString AppId = GetCurrentAssetId();
		// Tool/engine gating is enforced in HandleDownloadClicked when the action runs.
		return DownloadManager.IsValid()
			&& !AppId.IsEmpty()
			&& !DownloadManager->IsDownloadInProgress(AppId);
	}

	return CanDeleteCache();
}

void SWorldBLDAssetDetailPanel::HandleCacheActionClicked()
{
	if (ShouldShowRedownloadAction())
	{
		HandleDownloadClicked();
		return;
	}

	HandleDeleteCacheClicked();
}

void SWorldBLDAssetDetailPanel::HandleDeleteCacheClicked()
{
	if (!CanDeleteCache() || !DownloadManager.IsValid())
	{
		return;
	}

	const FString AppId = GetCurrentAssetId();
	const FText Title = GetTitleText();

	const FText Prompt = FText::Format(
		FText::FromString(TEXT("Delete cached files for \"{0}\"?\n\nThis removes the downloaded cache only. Imported content in your project is not affected.\n\nUse Re-download afterward if you need to import again.")),
		Title);

	const EAppReturnType::Type Result = FMessageDialog::Open(EAppMsgType::YesNo, Prompt);
	if (Result != EAppReturnType::Yes)
	{
		return;
	}

	DownloadManager->UninstallAsset(AppId, /*bDeleteCache=*/true, /*bDeleteImportedContent=*/false);
}

FText SWorldBLDAssetDetailPanel::GetTitleText() const
{
	if (bIsKit)
	{
		return FText::FromString(CurrentKit.KitsName);
	}
	return FText::FromString(CurrentAsset.Name);
}

FText SWorldBLDAssetDetailPanel::GetDescriptionText() const
{
	if (bShowingFeatured)
	{
		return FText::FromString(CurrentFeaturedCollection.Description);
	}
	if (bIsKit)
	{
		return FText::FromString(CurrentKit.Description);
	}

	
	if (CurrentAsset.Features.Num() > 0)
	{
		FString BulletList;
		for (const FString& Feature : CurrentAsset.Features)
		{
			const FString Trimmed = Feature.TrimStartAndEnd();
			if (Trimmed.IsEmpty())
			{
				continue;
			}

			if (!BulletList.IsEmpty())
			{
				BulletList += TEXT("\n");
			}
			BulletList += TEXT("- ");
			BulletList += Trimmed;
		}

		if (!BulletList.IsEmpty())
		{
			const FString TypeLabel = ExtractAssetTypeLabelFromFeatures(CurrentAsset.Features);
			const FString Blurb = GetTypeBlurbForAssetTypeLabel(TypeLabel);
			if (!Blurb.IsEmpty())
			{
				return FText::FromString(Blurb + TEXT("\n\n") + BulletList);
			}

			return FText::FromString(BulletList);
		}
	}

	return FText::FromString(CurrentAsset.Description);
}

EVisibility SWorldBLDAssetDetailPanel::GetEpicLicensingNoteVisibility() const
{
	return ShouldShowEpicLicensingNote() ? EVisibility::Visible : EVisibility::Collapsed;
}

void SWorldBLDAssetDetailPanel::HandleEpicLicensingNoteNavigate()
{
	static const TCHAR* EpicContentLicenseUrl = TEXT("https://www.unrealengine.com/eula/content");
	FPlatformProcess::LaunchURL(EpicContentLicenseUrl, nullptr, nullptr);
}

FText SWorldBLDAssetDetailPanel::GetPriceText() const
{
	if (bShowingFeatured)
	{
		return FText::GetEmpty();
	}

	const int32 PriceCredits = GetCurrentPriceCredits();
	const bool bFree = bIsKit ? CurrentKit.bIsFree : CurrentAsset.bIsFree;
	if (bFree || PriceCredits <= 0)
	{
		return FText::FromString(TEXT("Free"));
	}
	return CreditsToText(PriceCredits);
}

FText SWorldBLDAssetDetailPanel::GetPurchaseButtonText() const
{
	if (!UWorldBLDAuthSubsystem::IsLoggedIn())
	{
		return FText::FromString(TEXT("Log In")).ToUpper();
	}

	if (!HasSufficientCredits())
	{
		return HasActiveSubscription()
			? FText::FromString(TEXT("Get More Credits")).ToUpper()
			: FText::FromString(TEXT("Get Plan")).ToUpper();
	}

	return FText::FromString(TEXT("Purchase")).ToUpper();
}

bool SWorldBLDAssetDetailPanel::HasActiveSubscription() const
{
	// Subscription endpoint is currently inactive; treat "has an active plan" as "has a tool license".
	// If the user has no paid tool license (or only a trial), we show "Get Plan".
	return AuthSubsystem.IsValid()
		&& (AuthSubsystem->HasLicenseForTool(TEXT("RoadBLD")) || AuthSubsystem->HasLicenseForTool(TEXT("CityBLD")));
}

FText SWorldBLDAssetDetailPanel::GetUserCreditsText() const
{
	if (!AuthSubsystem.IsValid())
	{
		return FText::FromString(TEXT("Your Credits: 0"));
	}
	return FText::FromString(FString::Printf(TEXT("Your Credits: %d"), AuthSubsystem->GetUserCredits()));
}

FSlateColor SWorldBLDAssetDetailPanel::GetStatusColor() const
{
	// Match the description text color (instead of status-specific colors).
	return FSlateColor::UseForeground();
}

FText SWorldBLDAssetDetailPanel::GetStatusText() const
{
	if (!bShowingFeatured && !bIsKit && CurrentAsset.IsMirrorAsset())
	{
		TArray<FString> MissingPackageIds;
		GetMissingExternalPackageDependencies(MissingPackageIds);
		if (MissingPackageIds.Num() > 0)
		{
			return FText::FromString(TEXT("NOT OWNED"));
		}
	}

	const FText RawStatus = bShowingFeatured
		? FText::FromString(TEXT("Featured"))
		: StatusToText(GetStatusForSelection(DownloadManager, GetCurrentAssetId()));

	return FText::FromString(RawStatus.ToString().ToUpper());
}

EVisibility SWorldBLDAssetDetailPanel::GetStatusTextVisibility() const
{
	if (bShowingFeatured)
	{
		return EVisibility::Visible;
	}

	// Replace "IMPORTED" label with a "View Asset" action button.
	if (!bIsKit)
	{
		const FString AppId = GetCurrentAssetId();
		const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
		if (Status == EWorldBLDAssetStatus::Imported)
		{
			return EVisibility::Collapsed;
		}
	}

	return EVisibility::Visible;
}

EVisibility SWorldBLDAssetDetailPanel::GetViewAssetButtonVisibility() const
{
	if (bShowingFeatured || bIsKit)
	{
		return EVisibility::Collapsed;
	}

	const FString AppId = GetCurrentAssetId();
	const EWorldBLDAssetStatus Status = GetStatusForSelection(DownloadManager, AppId);
	return Status == EWorldBLDAssetStatus::Imported ? EVisibility::Visible : EVisibility::Collapsed;
}

const FSlateBrush* SWorldBLDAssetDetailPanel::GetCurrentPreviewBrush() const
{
	if (DetailHeader.IsValid())
	{
		return DetailHeader->GetCurrentPreviewBrush();
	}

	TSharedPtr<FSlateDynamicImageBrush> Placeholder = FWorldBLDAssetLibraryImageLoader::Get().GetPlaceholderBrush();
	return Placeholder.IsValid() ? Placeholder.Get() : nullptr;
}

FOptionalSize SWorldBLDAssetDetailPanel::GetAnimatedHeight() const
{
	// We animate a fraction of the *host* height, not the whole window, so the panel behaves properly inside splitters.
	const float Lerp = ExpandCurve.GetLerp();
	const float Target = CachedHostHeight * TargetHeightFraction;
	return FOptionalSize(Lerp * Target);
}

bool SWorldBLDAssetDetailPanel::HasSufficientCredits() const
{
	const int32 PriceCredits = GetCurrentPriceCredits();
	const bool bFree = bIsKit ? CurrentKit.bIsFree : CurrentAsset.bIsFree;
	if (bFree || PriceCredits <= 0)
	{
		return true;
	}

	if (!AuthSubsystem.IsValid())
	{
		return false;
	}

	return AuthSubsystem->GetUserCredits() >= PriceCredits;
}

EVisibility SWorldBLDAssetDetailPanel::GetDownloadProgressVisibility() const
{
	const FString AppId = GetCurrentAssetId();
	if (!DownloadManager.IsValid() || AppId.IsEmpty())
	{
		return EVisibility::Collapsed;
	}
	return DownloadManager->IsDownloadInProgress(AppId) ? EVisibility::Visible : EVisibility::Collapsed;
}

TOptional<float> SWorldBLDAssetDetailPanel::GetDownloadProgressValue() const
{
	const FString AppId = GetCurrentAssetId();
	if (!DownloadManager.IsValid() || AppId.IsEmpty())
	{
		return TOptional<float>();
	}

	const float Progress = DownloadManager->GetDownloadProgress(AppId);
	if (Progress < 0.0f)
	{
		return TOptional<float>();
	}
	return FMath::Clamp(Progress, 0.0f, 1.0f);
}

int32 SWorldBLDAssetDetailPanel::GetCurrentPriceCredits() const
{
	return bIsKit ? CurrentKit.Price : CurrentAsset.CreditsPrice;
}

FString SWorldBLDAssetDetailPanel::GetCurrentAssetId() const
{
	return bIsKit ? CurrentKit.ID : CurrentAsset.ID;
}

bool SWorldBLDAssetDetailPanel::ShouldShowEpicLicensingNote() const
{
	if (bIsKit || bShowingFeatured)
	{
		return false;
	}

	return CurrentAsset.Author.Contains(TEXT("Epic"), ESearchCase::IgnoreCase);
}

bool SWorldBLDAssetDetailPanel::ShouldShowThirdPartyNotice() const
{
	if (bIsKit || bShowingFeatured)
	{
		return false;
	}

	const FString Author = CurrentAsset.Author.TrimStartAndEnd();
	if (Author.IsEmpty())
	{
		return false;
	}

	return !Author.Contains(TEXT("WorldBLD"), ESearchCase::IgnoreCase)
		&& !Author.Contains(TEXT("Epic"), ESearchCase::IgnoreCase);
}

EVisibility SWorldBLDAssetDetailPanel::GetThirdPartyNoticeVisibility() const
{
	return ShouldShowThirdPartyNotice() ? EVisibility::Visible : EVisibility::Collapsed;
}

void SWorldBLDAssetDetailPanel::GetMissingExternalPackageDependencies(TArray<FString>& OutMissingPackageIds) const
{
	OutMissingPackageIds.Reset();

	if (bIsKit || bShowingFeatured || !CurrentAsset.IsMirrorAsset() || !DownloadManager.IsValid())
	{
		return;
	}

	DownloadManager->GetMissingExternalDependencyPackageIds(CurrentAsset, OutMissingPackageIds);
}

bool SWorldBLDAssetDetailPanel::AreExternalPackageDependenciesOwned(bool bShowDialogIfMissing)
{
	TArray<FString> MissingPackageIds;
	GetMissingExternalPackageDependencies(MissingPackageIds);
	if (MissingPackageIds.Num() == 0)
	{
		return true;
	}

	if (bShowDialogIfMissing)
	{
		ShowDependencyRequiredModal(MissingPackageIds);
	}

	return false;
}

void SWorldBLDAssetDetailPanel::ShowDependencyRequiredModal(const TArray<FString>& MissingPackageIds)
{
	// Close any previously open dependency modal before opening a new one.
	if (DependencyModalWindow.IsValid())
	{
		if (TSharedPtr<SWindow> Existing = DependencyModalWindow.Pin())
		{
			Existing->RequestDestroyWindow();
		}
		DependencyModalWindow.Reset();
	}

	// Resolve PackageIds to full asset info objects via the owning library window.
	TArray<FWorldBLDAssetInfo> DepAssets;
	if (OnResolvePackageIds.IsBound())
	{
		DepAssets = OnResolvePackageIds.Execute(MissingPackageIds, /*bMissingOnly=*/true);
	}

	// Compute total credits cost across all missing deps.
	int32 TotalCreditsCost = 0;
	for (const FWorldBLDAssetInfo& Dep : DepAssets)
	{
		if (!Dep.bIsFree)
		{
			TotalCreditsCost += Dep.CreditsPrice;
		}
	}

	const int32 UserCredits = AuthSubsystem.IsValid() ? AuthSubsystem->GetUserCredits() : 0;

	// Capture the assets list and subsystem ref for the purchase-all callback.
	TArray<FWorldBLDAssetInfo> DepAssetsCopy = DepAssets;
	TWeakObjectPtr<UWorldBLDAssetLibrarySubsystem> WeakSubsystem = AssetLibrarySubsystem;

	TSharedRef<SWindow> ModalWindow = SNew(SWindow)
		.Title(FText::FromString(TEXT("Required Assets")))
		.SizingRule(ESizingRule::Autosized)
		.SupportsMaximize(false)
		.SupportsMinimize(false);

	ModalWindow->SetContent(
		SNew(SWorldBLDDependencyRequiredModal)
		.MissingDependencies(DepAssets)
		.TotalCreditsCost(TotalCreditsCost)
		.UserCredits(UserCredits)
		.OnNavigateToDependency(FOnWorldBLDNavigateToDependency::CreateLambda(
			[this](const FString& PackageId)
			{
				OnNavigateToAsset.ExecuteIfBound(PackageId);
			}))
		.OnGoBack(FSimpleDelegate::CreateLambda([]() {}))
		.OnPurchaseAll(FSimpleDelegate::CreateLambda(
			[DepAssetsCopy, WeakSubsystem]()
			{
				if (UWorldBLDAssetLibrarySubsystem* Subsystem = WeakSubsystem.Get())
				{
					for (const FWorldBLDAssetInfo& Dep : DepAssetsCopy)
					{
						if (!Dep.ID.IsEmpty())
						{
							Subsystem->PurchaseAsset(Dep.ID);
						}
					}
				}
			}))
	);

	DependencyModalWindow = ModalWindow;
	FSlateApplication::Get().AddModalWindow(ModalWindow, FSlateApplication::Get().GetActiveTopLevelWindow());
}

void SWorldBLDAssetDetailPanel::BeginLoadPreviewImages(const TArray<FString>& Urls)
{
	if (DetailHeader.IsValid())
	{
		DetailHeader->SetPreviewUrls(Urls);
	}
}

void SWorldBLDAssetDetailPanel::BeginLoadThumbnailBrush(const FString& URL)
{
	ThumbnailBrush = FWorldBLDAssetLibraryImageLoader::Get().GetPlaceholderBrush();

	if (URL.IsEmpty())
	{
		return;
	}

	const TWeakPtr<SWorldBLDAssetDetailPanel> WeakPanel = StaticCastSharedRef<SWorldBLDAssetDetailPanel>(AsShared());
	FWorldBLDAssetLibraryImageLoader::Get().LoadImageFromURL(URL, [WeakPanel](TSharedPtr<FSlateDynamicImageBrush> LoadedBrush)
	{
		if (TSharedPtr<SWorldBLDAssetDetailPanel> Pinned = WeakPanel.Pin())
		{
			Pinned->ThumbnailBrush = LoadedBrush;
		}
	});
}

FText SWorldBLDAssetDetailPanel::GetDependencyInfoText() const
{
	if (!bIsKit && CurrentAsset.IsMirrorAsset())
	{
		TArray<FString> MissingPackageIds;
		GetMissingExternalPackageDependencies(MissingPackageIds);
		if (MissingPackageIds.Num() > 0)
		{
			return FText::FromString(FString::Printf(TEXT("Requires %d other assets before purchase. Click Purchase to review them."),
				MissingPackageIds.Num()));
		}
	}

	if (bIsKit || CurrentAsset.Manifest.Dependencies.Num() == 0)
	{
		return FText::GetEmpty();
	}

	const int32 TotalDeps = CurrentAsset.Manifest.Dependencies.Num();

	if (!DownloadManager.IsValid() || !bDependencyCacheValid)
	{
		return FText::FromString(FString::Printf(TEXT("Dependencies: %d (not checked)"), TotalDeps));
	}

	// Use cached values instead of calling CheckLocalDependencies every frame
	if (CachedMissingDepsCount == 0)
	{
		return FText::FromString(FString::Printf(TEXT("Dependencies: %d (all available locally)"), TotalDeps));
	}
	else if (CachedExistingDepsCount == 0)
	{
		return FText::FromString(FString::Printf(TEXT("Dependencies: %d (none available locally)"), TotalDeps));
	}
	else
	{
		return FText::FromString(FString::Printf(TEXT("Dependencies: %d (%d available, %d missing)"),
			TotalDeps, CachedExistingDepsCount, CachedMissingDepsCount));
	}
}

EVisibility SWorldBLDAssetDetailPanel::GetDependencyInfoVisibility() const
{
	if (!bIsKit && CurrentAsset.IsMirrorAsset() && CurrentAsset.ExternalDependencyPackageIds.Num() > 0)
	{
		return EVisibility::Visible;
	}

	return EVisibility::Collapsed;
}

void SWorldBLDAssetDetailPanel::RefreshDependencyCache()
{
	// Avoid repeated work if we've already computed the cache for the current selection.
	if (bDependencyCacheValid)
	{
		return;
	}

	// Skip if this is a kit or no dependencies
	if (bIsKit || CurrentAsset.Manifest.Dependencies.Num() == 0 || !DownloadManager.IsValid())
	{
		bDependencyCacheValid = false;
		CachedMissingDepsCount = 0;
		CachedExistingDepsCount = 0;
		return;
	}

	// Perform the actual check and cache the results
	TArray<FWorldBLDAssetDependency> MissingDeps;
	TArray<FWorldBLDAssetDependency> ExistingDeps;
	DownloadManager->CheckLocalDependencies(CurrentAsset, MissingDeps, ExistingDeps);

	CachedMissingDepsCount = MissingDeps.Num();
	CachedExistingDepsCount = ExistingDeps.Num();
	bDependencyCacheValid = true;
}

bool SWorldBLDAssetDetailPanel::AreToolRequirementsSatisfied()
{
	// Kits currently have no requiredTools data in the asset schema. Only gate assets.
	if (bIsKit || bShowingFeatured)
	{
		return true;
	}

	// Keep this lazy so if the tool-name mapping becomes available after the panel is shown
	// (e.g., licenses/tools list arrives), the buttons will re-enable without requiring a re-select.
	EvaluateToolRequirements(/*bShowDialogIfUnmet=*/false);
	return bToolRequirementsSatisfied;
}

void SWorldBLDAssetDetailPanel::EvaluateToolRequirements(bool bShowDialogIfUnmet)
{
	// Default: allow actions.
	bToolRequirementsSatisfied = true;

	if (bIsKit || bShowingFeatured)
	{
		return;
	}

	if (CurrentAsset.RequiredTools.Num() <= 0)
	{
		return;
	}

	const FString AssetId = GetCurrentAssetId();

	// Find the first failing requirement (we keep UX simple and focused).
	const TArray<FString> AuthorizedTools = AuthSubsystem.IsValid() ? AuthSubsystem->GetAuthorizedTools() : TArray<FString>();
	for (const FWorldBLDRequiredTool& Req : CurrentAsset.RequiredTools)
	{
		const FString ToolId = Req.ToolId.TrimStartAndEnd();
		if (ToolId.IsEmpty())
		{
			continue;
		}

		const FString ToolName = ResolveToolNameFromToolId(ToolId, AuthorizedTools.Num() > 0 ? &AuthorizedTools : nullptr);
		const FString MinVersion = Req.MinVersion.TrimStartAndEnd();

		// 1) Plugin must be mounted/enabled
		// WorldBLD is the host tool for this UI; treat it as always present and only enforce version.
		if (!ToolName.Equals(TEXT("WorldBLD"), ESearchCase::IgnoreCase) && !IsPluginMountedAndEnabled(ToolName))
		{
			bToolRequirementsSatisfied = false;

			if (bShowDialogIfUnmet && (AssetId != LastToolRequirementDialogAssetId || LastToolRequirementDialogReason != TEXT("missing")))
			{
				LastToolRequirementDialogAssetId = AssetId;
				LastToolRequirementDialogReason = TEXT("missing");

				const FString Message = FString::Printf(
					TEXT("This asset requires the %s tool. Please download %s first."),
					*ToolName, *ToolName);
				FMessageDialog::Open(EAppMsgType::Ok, FText::FromString(Message));
			}
			return;
		}

		// 2) Version must be >= required minVersion
		if (!MinVersion.IsEmpty())
		{
			const FString InstalledVersion = GetPluginVersionString(ToolName);
			const int32 InstalledInt = ParseSemVerToSortableInt(InstalledVersion);
			const int32 RequiredInt = ParseSemVerToSortableInt(MinVersion);

			// If we can parse required version, enforce it. If parsing fails (0), skip enforcing.
			if (RequiredInt > 0 && InstalledInt < RequiredInt)
			{
				bToolRequirementsSatisfied = false;

				if (bShowDialogIfUnmet && (AssetId != LastToolRequirementDialogAssetId || LastToolRequirementDialogReason != TEXT("outdated")))
				{
					LastToolRequirementDialogAssetId = AssetId;
					LastToolRequirementDialogReason = TEXT("outdated");

					const FString Message = FString::Printf(
						TEXT("This asset requires a newer version of %s. Please update %s first."),
						*ToolName, *ToolName);
					FMessageDialog::Open(EAppMsgType::Ok, FText::FromString(Message));
				}
				return;
			}
		}
	}
}

bool SWorldBLDAssetDetailPanel::AreEngineRequirementsSatisfied()
{
	if (bIsKit || bShowingFeatured)
	{
		return true;
	}

	EvaluateEngineRequirements(/*bShowDialogIfUnmet=*/false);
	return bEngineRequirementsSatisfied;
}

void SWorldBLDAssetDetailPanel::EvaluateEngineRequirements(bool bShowDialogIfUnmet)
{
	bEngineRequirementsSatisfied = true;

	if (bIsKit || bShowingFeatured)
	{
		return;
	}

	if (WorldBLDAssetEngineVersionUtils::IsEngineVersionCompatible(CurrentAsset.EngineVersions))
	{
		return;
	}

	bEngineRequirementsSatisfied = false;

	if (bShowDialogIfUnmet)
	{
		const FString AssetId = GetCurrentAssetId();
		if (AssetId != LastEngineRequirementDialogAssetId)
		{
			LastEngineRequirementDialogAssetId = AssetId;
			FMessageDialog::Open(
				EAppMsgType::Ok,
				FText::FromString(WorldBLDAssetEngineVersionUtils::MakeIncompatibleEngineMessage(CurrentAsset.EngineVersions)));
		}
	}
}
