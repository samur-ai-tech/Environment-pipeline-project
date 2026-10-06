// Copyright WorldBLD LLC. All rights reserved.

#include "ViewportToolbar/WorldBLDToolbarProvider.h"

#include "ViewportToolbar/SWorldBLDPluginToolbar.h"
#include "ViewportToolbar/SWorldBLDViewportToolbarHost.h"
#include "ViewportToolbar/WorldBLDToolbarButtonDef.h"

#include "AssetLibrary/WorldBLDAssetLibraryWindow.h"
#include "Authorization/WorldBLDAuthSubsystem.h"
#include "Authorization/WorldBLDLoginWindow.h"
#include "Downloader/CurlDownloaderLibrary.h"
#include "Resources/SWorldBLDResourcesDialog.h"
#include "WorldBLDEditController.h"
#include "WorldBLDEditorToolkit.h"
#include "WorldBLDEditorUtilityLibrary.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Blueprint/WidgetBlueprintGeneratedClass.h"
#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateDynamicImageBrush.h"
#include "Components/Widget.h"
#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"
#include "Editor.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "UObject/StrongObjectPtr.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WorldBLDToolbarProvider"

namespace WorldBLDToolbarProviderLocal
{
	static const FName WorldBLDToolId(TEXT("WorldBLD"));

	static constexpr float ToolbarIconExtent = 30.0f;
	static constexpr float UtilityTileImageSize = 96.0f;
	static constexpr float UtilityTileWidth = 132.0f;
	static constexpr float UtilityMenuWidth = 600.0f;
	static constexpr float UtilityMenuHeight = 480.0f;

	/**
	 * Loads a PNG from the WorldBLD plugin Resources folder and returns a brush sized for the
	 * toolbar icon slot (30x30). Returns an empty pointer if the file cannot be found.
	 */
	static TSharedPtr<FSlateDynamicImageBrush> MakeResourceIconBrush(const TCHAR* RelativeResourcePath)
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

		return MakeShared<FSlateDynamicImageBrush>(
			FName(*FullPath),
			FVector2D(ToolbarIconExtent, ToolbarIconExtent));
	}

	/** Tool id -> toolbar factory registered by each plugin module. */
	static TMap<FName, WorldBLDToolbar::FToolbarFactory>& GetToolbarFactories()
	{
		static TMap<FName, WorldBLDToolbar::FToolbarFactory> Factories;
		return Factories;
	}

	static void LaunchUtilityBundle(UWorldBLDUtilityBundle* ClickedBundle)
	{
		if (!ClickedBundle)
		{
			return;
		}

		if (!IsValid(ClickedBundle->WidgetClass))
		{
			UE_LOG(LogTemp, Warning, TEXT("WorldBLDToolbarProvider::LaunchUtilityBundle - Invalid WidgetClass for '%s'."), *ClickedBundle->GetPathName());
			return;
		}

		if (!ClickedBundle->PushWidgetToViewport)
		{
			if (!GEditor)
			{
				return;
			}

			UEditorUtilitySubsystem* UtilitySubsystem = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();
			if (!UtilitySubsystem)
			{
				return;
			}

			UClass* WidgetClass = ClickedBundle->WidgetClass.Get();
			if (!WidgetClass)
			{
				return;
			}

			if (UWidgetBlueprintGeneratedClass* GeneratedWidgetClass = Cast<UWidgetBlueprintGeneratedClass>(WidgetClass))
			{
				if (UEditorUtilityWidget* SpawnedWidget = UtilitySubsystem->SpawnAndRegisterTabGeneratedClass(GeneratedWidgetClass))
				{
					return;
				}
			}

			UEditorUtilityWidgetBlueprint* WidgetBlueprint = Cast<UEditorUtilityWidgetBlueprint>(WidgetClass->ClassGeneratedBy);
			if (!WidgetBlueprint)
			{
				const FString ClassObjectPath = WidgetClass->GetPathName();
				const FString BlueprintObjectPath = ClassObjectPath.EndsWith(TEXT("_C"))
					? ClassObjectPath.LeftChop(2)
					: FString();
				if (!BlueprintObjectPath.IsEmpty())
				{
					WidgetBlueprint = LoadObject<UEditorUtilityWidgetBlueprint>(nullptr, *BlueprintObjectPath);
				}
			}

			if (WidgetBlueprint)
			{
				UtilitySubsystem->SpawnAndRegisterTab(WidgetBlueprint);
			}

			return;
		}

		UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!World)
		{
			return;
		}

		UEditorUtilityWidget* UtilityWidget = CreateWidget<UEditorUtilityWidget>(World, ClickedBundle->WidgetClass);
		if (!IsValid(UtilityWidget))
		{
			return;
		}

		UtilityWidget->SetFlags(RF_Transient);

		if (UtilityWidget->WidgetTree)
		{
			TArray<UWidget*> AllWidgets;
			UtilityWidget->WidgetTree->GetAllWidgets(AllWidgets);
			for (UWidget* Widget : AllWidgets)
			{
				if (Widget && Widget->IsA(UEditorUtilityWidget::StaticClass()))
				{
					Widget->SetFlags(RF_Transient);
					if (Widget->Slot)
					{
						Widget->Slot->SetFlags(RF_Transient);
					}
				}
			}
		}

		if (UWorldBLDEditController* ToolController = Cast<UWorldBLDEditController>(UtilityWidget))
		{
			if (UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
			{
				EdMode->PushEditController(ToolController);
			}
			else
			{
				ToolController->AddToEditorLevelViewport();
				ToolController->ToolBegin();
			}
		}
	}

	static void QueryUtilityBundlesAtPath(IAssetRegistry& AssetRegistry, const FString& SearchPath, TArray<FAssetData>& OutAssets)
	{
		FARFilter Filter;
		Filter.PackagePaths.Add(FName(*SearchPath));
		Filter.ClassPaths.Add(UWorldBLDUtilityBundle::StaticClass()->GetClassPathName());
		Filter.bRecursivePaths = true;
		Filter.bRecursiveClasses = true;
		AssetRegistry.GetAssets(Filter, OutAssets);
	}

	class SUtilityBundleSelectorMenu : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SUtilityBundleSelectorMenu) {}
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			LoadBundles();
			RebuildTiles();
		}

	private:
		struct FUtilityBundleEntry
		{
			TStrongObjectPtr<UWorldBLDUtilityBundle> Bundle;
			TSharedPtr<FSlateBrush> ThumbnailBrush;
		};

		TArray<FUtilityBundleEntry> BundleEntries;
		TSharedPtr<SWrapBox> WrapBox;

		void LoadBundles()
		{
			BundleEntries.Reset();

			FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();
			TArray<FString> PathsToScan = { TEXT("/WorldBLD"), TEXT("/WorldBLD/Utilities"), TEXT("/Game") };
			AssetRegistry.ScanPathsSynchronous(PathsToScan, false);

			TArray<FAssetData> AssetDataList;
			QueryUtilityBundlesAtPath(AssetRegistry, TEXT("/WorldBLD/Utilities"), AssetDataList);

			if (AssetDataList.Num() == 0)
			{
				static const TCHAR* FallbackPaths[] =
				{
					TEXT("/WorldBLD/Utilities/Data"),
					TEXT("/Game/WorldBLD/Utilities"),
					TEXT("/Game/WorldBLD/Utilities/Data")
				};

				for (const TCHAR* FallbackPath : FallbackPaths)
				{
					QueryUtilityBundlesAtPath(AssetRegistry, FallbackPath, AssetDataList);
					if (AssetDataList.Num() > 0)
					{
						break;
					}
				}
			}

			for (const FAssetData& AssetData : AssetDataList)
			{
				UWorldBLDUtilityBundle* BundleAsset = Cast<UWorldBLDUtilityBundle>(AssetData.GetAsset());
				if (!BundleAsset)
				{
					continue;
				}

				FUtilityBundleEntry& NewEntry = BundleEntries.AddDefaulted_GetRef();
				NewEntry.Bundle.Reset(BundleAsset);
				NewEntry.ThumbnailBrush = MakeShared<FSlateBrush>();
				NewEntry.ThumbnailBrush->DrawAs = ESlateBrushDrawType::Image;
				NewEntry.ThumbnailBrush->ImageSize = FVector2D(UtilityTileImageSize, UtilityTileImageSize);
				NewEntry.ThumbnailBrush->SetResourceObject(BundleAsset->ToolImage);
			}
		}

		FReply HandleBundleClicked(UWorldBLDUtilityBundle* ClickedBundle) const
		{
			LaunchUtilityBundle(ClickedBundle);
			return FReply::Handled();
		}

		void RebuildTiles()
		{
			ChildSlot
			[
				SNew(SBox)
				.WidthOverride(UtilityMenuWidth)
				.HeightOverride(UtilityMenuHeight)
				[
					SNew(SBorder)
					.Padding(8.0f)
					[
						SNew(SScrollBox)
						+ SScrollBox::Slot()
						[
							SAssignNew(WrapBox, SWrapBox)
							.PreferredSize(UtilityMenuWidth - 20.0f)
							.UseAllottedSize(true)
						]
					]
				]
			];

			if (!WrapBox.IsValid())
			{
				return;
			}

			WrapBox->ClearChildren();
			if (BundleEntries.Num() == 0)
			{
				WrapBox->AddSlot()
				.Padding(FMargin(8.0f))
				[
					SNew(STextBlock)
					.Text(LOCTEXT("NoUtilityBundlesFound", "No utility bundles found."))
				];
				return;
			}

			for (const FUtilityBundleEntry& Entry : BundleEntries)
			{
				const UWorldBLDUtilityBundle* Bundle = Entry.Bundle.Get();
				if (!Bundle)
				{
					continue;
				}

				const FText UtilityLabel = Bundle->UtilityName.IsEmpty()
					? FText::FromString(Bundle->GetName())
					: Bundle->UtilityName;
				const FText UtilityTooltip = Bundle->UtilityDescription.IsEmpty()
					? UtilityLabel
					: Bundle->UtilityDescription;

				WrapBox->AddSlot()
				.Padding(FMargin(4.0f))
				[
					SNew(SBox)
					.WidthOverride(UtilityTileWidth)
					[
						SNew(SButton)
						.OnClicked(this, &SUtilityBundleSelectorMenu::HandleBundleClicked, const_cast<UWorldBLDUtilityBundle*>(Bundle))
						.ToolTipText(UtilityTooltip)
						.ContentPadding(FMargin(6.0f))
						[
							SNew(SVerticalBox)
							+ SVerticalBox::Slot()
							.AutoHeight()
							.HAlign(HAlign_Center)
							[
								SNew(SBox)
								.WidthOverride(UtilityTileImageSize)
								.HeightOverride(UtilityTileImageSize)
								[
									SNew(SImage)
									.Image(Entry.ThumbnailBrush.Get())
								]
							]
							+ SVerticalBox::Slot()
							.AutoHeight()
							.Padding(FMargin(0.0f, 6.0f, 0.0f, 0.0f))
							.HAlign(HAlign_Center)
							[
								SNew(STextBlock)
								.Text(UtilityLabel)
								.Justification(ETextJustify::Center)
								.AutoWrapText(true)
							]
						]
					]
				];
			}
		}
	};

	static EVisibility GetToolbarVisibility()
	{
		// Collapse every plugin toolbar while a PIE session is active so the
		// floating panels never obstruct the in-game viewport or HUD.
		return (GEditor && GEditor->PlayWorld != nullptr)
			? EVisibility::Collapsed
			: EVisibility::SelfHitTestInvisible;
	}

	static void LogOutCurrentSession()
	{
		if (GEditor != nullptr)
		{
			if (UWorldBLDAuthSubsystem* Auth = GEditor->GetEditorSubsystem<UWorldBLDAuthSubsystem>())
			{
				Auth->Logout();
			}
		}
	}

	static FWorldBLDToolbarButtonDef MakeLoginButtonDef()
	{
		FWorldBLDToolbarButtonDef Def;
		Def.Label = LOCTEXT("LoginLabel", "Log In");
		Def.Tooltip = LOCTEXT("LoginTooltip", "Log in to your WorldBLD account");
		Def.IconBrush = MakeResourceIconBrush(TEXT("Resources/Icon_Login.png"));
		Def.bEnabledWhenLoggedOut = true;
		Def.OnClicked = FSimpleDelegate::CreateStatic(&FWorldBLDLoginWindow::OpenLoginDialog);
		return Def;
	}
}

void WorldBLDToolbar::RegisterToolbarFactory(FName ToolId, FToolbarFactory Factory)
{
	if (!ToolId.IsNone())
	{
		WorldBLDToolbarProviderLocal::GetToolbarFactories().Add(ToolId, MoveTemp(Factory));
	}
}

void WorldBLDToolbar::UnregisterToolbarFactory(FName ToolId)
{
	WorldBLDToolbarProviderLocal::GetToolbarFactories().Remove(ToolId);
}

bool WorldBLDToolbar::HasToolbarFactory(FName ToolId)
{
	return WorldBLDToolbarProviderLocal::GetToolbarFactories().Contains(ToolId);
}

TSharedRef<SWidget> WorldBLDToolbar::CreateToolbarForTool(FName ToolId)
{
	if (ToolId.IsNone() || ToolId == WorldBLDToolbarProviderLocal::WorldBLDToolId)
	{
		return CreateWorldBLDToolbar();
	}

	if (const FToolbarFactory* Factory = WorldBLDToolbarProviderLocal::GetToolbarFactories().Find(ToolId))
	{
		if (Factory->IsBound())
		{
			return Factory->Execute();
		}
	}

	return CreatePlaceholderToolbar(FText::FromName(ToolId));
}

TSharedRef<SWidget> WorldBLDToolbar::CreatePluginToolbarWidget(
	const TArray<FWorldBLDToolbarButtonDef>& MainButtons,
	const TArray<FWorldBLDToolbarButtonDef>& OverflowButtons)
{
	using namespace WorldBLDToolbarProviderLocal;

	UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode();
	UCurlDownloaderLibrary* Downloader = GEditor ? GEditor->GetEditorSubsystem<UCurlDownloaderLibrary>() : nullptr;

	FName ManageToolId = NAME_None;
	const FName ActiveToolId = EdMode != nullptr ? EdMode->GetActiveViewportToolbarId() : NAME_None;
	if (!ActiveToolId.IsNone() && ActiveToolId != WorldBLDToolId)
	{
		ManageToolId = ActiveToolId;
	}

	const TSharedRef<SWorldBLDPluginToolbar> Frame =
		SNew(SWorldBLDPluginToolbar)
		.MainButtons(MainButtons)
		.EdMode(EdMode)
		.Downloader(Downloader)
		.LoginButton(MakeLoginButtonDef())
		.OverflowButtons(OverflowButtons)
		.ManageToolId(ManageToolId);

	const TSharedRef<SWorldBLDViewportToolbarHost> Host =
		SNew(SWorldBLDViewportToolbarHost)
		.ToolbarContent(Frame)
		.ToolSwitchContent(Frame->GetToolSwitchWidget())
		.ToolbarOrientation(TAttribute<EOrientation>::Create(
			TAttribute<EOrientation>::FGetter::CreateSP(Frame, &SWorldBLDPluginToolbar::GetOrientation)));

	// Keep every toolbar hidden during PIE so the panels never overlay the game viewport.
	Host->SetVisibility(TAttribute<EVisibility>::Create(
		TAttribute<EVisibility>::FGetter::CreateStatic(&GetToolbarVisibility)));

	return Host;
}

TSharedRef<SWidget> WorldBLDToolbar::CreateUtilitiesMenuContent()
{
	return SNew(WorldBLDToolbarProviderLocal::SUtilityBundleSelectorMenu);
}

TSharedRef<SWidget> WorldBLDToolbar::CreateWorldBLDToolbar()
{
	using namespace WorldBLDToolbarProviderLocal;

	TArray<FWorldBLDToolbarButtonDef> MainButtons;

	// 1. Asset Library
	{
		FWorldBLDToolbarButtonDef AssetLibrary;
		AssetLibrary.Label = LOCTEXT("AssetLibraryLabel", "Asset Library");
		AssetLibrary.Tooltip = LOCTEXT("AssetLibraryTooltip", "Browse the WorldBLD asset library");
		AssetLibrary.IconBrush = MakeResourceIconBrush(TEXT("Resources/Icon_Prefab-Tool.png"));
		AssetLibrary.OnClicked = FSimpleDelegate::CreateStatic(&FWorldBLDAssetLibraryWindow::OpenAssetLibrary);
		MainButtons.Add(MoveTemp(AssetLibrary));
	}

	// 2. Spacer
	{
		FWorldBLDToolbarButtonDef Spacer;
		Spacer.bIsSpacer = true;
		MainButtons.Add(MoveTemp(Spacer));
	}

	// 3. Learn
	{
		FWorldBLDToolbarButtonDef Learn;
		Learn.Label = LOCTEXT("LearnLabel", "Learn");
		Learn.Tooltip = LOCTEXT("LearnTooltip", "Open WorldBLD learning resources");
		Learn.IconBrush = MakeResourceIconBrush(TEXT("Resources/Icon_circle-question.PNG"));
		Learn.OnClicked = FSimpleDelegate::CreateStatic(&SWorldBLDResourcesDialog::Open);
		MainButtons.Add(MoveTemp(Learn));
	}

	// 4. Spacer
	{
		FWorldBLDToolbarButtonDef Spacer;
		Spacer.bIsSpacer = true;
		MainButtons.Add(MoveTemp(Spacer));
	}

	// 5. Settings
	{
		FWorldBLDToolbarButtonDef Settings;
		Settings.Label = LOCTEXT("SettingsLabel", "Settings");
		Settings.Tooltip = LOCTEXT("SettingsTooltip", "Open WorldBLD project settings");
		Settings.IconBrush = MakeResourceIconBrush(TEXT("Resources/Icon_UISettings.PNG"));
		Settings.bEnabledWhenLoggedOut = true;
		Settings.OnClicked = FSimpleDelegate::CreateStatic(&UWorldBLDEditorUtilityLibrary::OpenWorldBLDProjectSettings);
		MainButtons.Add(MoveTemp(Settings));
	}

	// 6. Spacer
	{
		FWorldBLDToolbarButtonDef Spacer;
		Spacer.bIsSpacer = true;
		MainButtons.Add(MoveTemp(Spacer));
	}

	TArray<FWorldBLDToolbarButtonDef> OverflowButtons;
	{
		FWorldBLDToolbarButtonDef LogOut;
		LogOut.Label = LOCTEXT("LogOutLabel", "Log Out");
		LogOut.Tooltip = LOCTEXT("LogOutTooltip", "Log out of your current WorldBLD session");
		LogOut.IconBrush = MakeResourceIconBrush(TEXT("Resources/Icon_UI_Backarrow.PNG"));
		LogOut.bIsOverflow = true;
		LogOut.IsVisible = FWorldBLDToolbarVisibility::CreateStatic(&UWorldBLDAuthSubsystem::IsLoggedIn);
		LogOut.OnClicked = FSimpleDelegate::CreateStatic(&LogOutCurrentSession);
		OverflowButtons.Add(MoveTemp(LogOut));
	}

	return CreatePluginToolbarWidget(MainButtons, OverflowButtons);
}

TSharedRef<SWidget> WorldBLDToolbar::CreatePlaceholderToolbar(const FText& PluginDisplayName)
{
	TArray<FWorldBLDToolbarButtonDef> MainButtons;
	static const FName PlaceholderIcons[] =
	{
		TEXT("ClassThumbnail.Default"),
		TEXT("ClassThumbnail.Blueprint"),
		TEXT("ClassThumbnail.World")
	};

	for (int32 Index = 0; Index < 3; ++Index)
	{
		FWorldBLDToolbarButtonDef Placeholder;
		Placeholder.Label = FText::Format(LOCTEXT("PlaceholderToolFmt", "Tool {0}"), FText::AsNumber(Index + 1));
		Placeholder.Tooltip = FText::Format(LOCTEXT("PlaceholderToolTooltipFmt", "{0} placeholder tool {1}"), PluginDisplayName, FText::AsNumber(Index + 1));
		Placeholder.IconName = PlaceholderIcons[Index];
		MainButtons.Add(MoveTemp(Placeholder));
	}

	return CreatePluginToolbarWidget(MainButtons, TArray<FWorldBLDToolbarButtonDef>());
}

#undef LOCTEXT_NAMESPACE
