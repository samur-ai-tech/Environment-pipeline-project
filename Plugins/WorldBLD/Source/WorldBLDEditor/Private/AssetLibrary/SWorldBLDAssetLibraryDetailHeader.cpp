// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/SWorldBLDAssetLibraryDetailHeader.h"

#include "AssetLibrary/WorldBLDAssetLibraryImageLoader.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"

#include "Brushes/SlateDynamicImageBrush.h"
#include "HAL/FileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "Styling/AppStyle.h"
#include "Styling/SlateTypes.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SWorldBLDCoverImage.h"

namespace WorldBLDAssetLibraryDetailHeader_Private
{
	static constexpr float ChevronIconExtent = 32.0f;

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

	static const FButtonStyle& GetPreviewNavChevronButtonStyle()
	{
		static const FButtonStyle Style = []()
		{
			FButtonStyle NewStyle = FAppStyle::Get().GetWidgetStyle<FButtonStyle>("NoBorder");
			NewStyle
				.SetNormalForeground(FLinearColor::White)
				.SetHoveredForeground(WorldBLDContextMenuStyle::GetHighlightRedColor())
				.SetPressedForeground(WorldBLDContextMenuStyle::GetHighlightRedColor())
				.SetDisabledForeground(FLinearColor(1.0f, 1.0f, 1.0f, 0.35f))
				.SetNormalPadding(FMargin(0.0f))
				.SetPressedPadding(FMargin(0.0f));
			return NewStyle;
		}();
		return Style;
	}
}

void SWorldBLDAssetLibraryDetailHeader::Construct(const FArguments& InArgs)
{
	using namespace WorldBLDAssetLibraryDetailHeader_Private;

	const FVector2D ChevronSize(ChevronIconExtent, ChevronIconExtent);
	PrevChevronBrush = MakeResourceIconBrush(TEXT("Resources/Icon_UI_arrow-left-small.PNG"), ChevronSize);
	NextChevronBrush = MakeResourceIconBrush(TEXT("Resources/Icon_UI_arrow-right-small.PNG"), ChevronSize);

	ChildSlot
	[
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.FillWidth(0.6f)
		.Padding(FMargin(0.0f, 0.0f, 12.0f, 0.0f))
		[
			SNew(SOverlay)
			+ SOverlay::Slot()
			[
				SNew(SBorder)
				.BorderImage(FAppStyle::Get().GetBrush("ToolPanel.GroupBorder"))
				.Padding(0.0f)
				.Clipping(EWidgetClipping::ClipToBounds)
				[
					SNew(SBox)
					.MaxDesiredWidth(1280.0f)
					.MaxDesiredHeight(720.0f)
					.HAlign(HAlign_Fill)
					.VAlign(VAlign_Fill)
					[
						SAssignNew(PreviewImageWidget, SWorldBLDCoverImage)
						.Image(this, &SWorldBLDAssetLibraryDetailHeader::GetCurrentPreviewBrushInternal)
					]
				]
			]
			+ SOverlay::Slot()
			.HAlign(HAlign_Left)
			.VAlign(VAlign_Center)
			.Padding(FMargin(8.0f, 0.0f))
			[
				MakePreviewNavButton(PrevChevronBrush, false)
			]
			+ SOverlay::Slot()
			.HAlign(HAlign_Right)
			.VAlign(VAlign_Center)
			.Padding(FMargin(8.0f, 0.0f))
			[
				MakePreviewNavButton(NextChevronBrush, true)
			]
		]
		+ SHorizontalBox::Slot()
		.FillWidth(0.4f)
		[
			InArgs._Sidebar.Widget
		]
	];

	SetPreviewUrls({});
}

TSharedRef<SWidget> SWorldBLDAssetLibraryDetailHeader::MakePreviewNavButton(
	const TSharedPtr<FSlateDynamicImageBrush>& IconBrush,
	const bool bNavigateNext)
{
	using namespace WorldBLDAssetLibraryDetailHeader_Private;

	return SNew(SButton)
		.ButtonStyle(&GetPreviewNavChevronButtonStyle())
		.ContentPadding(0.0f)
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		.Cursor(EMouseCursor::Hand)
		.Visibility(this, &SWorldBLDAssetLibraryDetailHeader::GetPreviewNavigationVisibility)
		.OnClicked(this, bNavigateNext
			? &SWorldBLDAssetLibraryDetailHeader::HandleNextImage
			: &SWorldBLDAssetLibraryDetailHeader::HandlePrevImage)
		.IsEnabled_Lambda([this]() { return PreviewUrlCount > 1; })
		[
			SNew(SBox)
			.WidthOverride(ChevronIconExtent)
			.HeightOverride(ChevronIconExtent)
			[
				SNew(SImage)
				.Image(IconBrush.IsValid() ? IconBrush.Get() : nullptr)
				.ColorAndOpacity(FSlateColor::UseForeground())
			]
		];
}

void SWorldBLDAssetLibraryDetailHeader::SetPreviewUrls(const TArray<FString>& Urls)
{
	TArray<FString> CleanUrls;
	CleanUrls.Reserve(Urls.Num());
	for (const FString& Url : Urls)
	{
		const FString Trimmed = Url.TrimStartAndEnd();
		if (!Trimmed.IsEmpty())
		{
			CleanUrls.Add(Trimmed);
		}
	}

	PreviewUrlCount = CleanUrls.Num();
	BeginLoadPreviewImages(CleanUrls);
}

const FSlateBrush* SWorldBLDAssetLibraryDetailHeader::GetCurrentPreviewBrush() const
{
	return GetCurrentPreviewBrushInternal();
}

FReply SWorldBLDAssetLibraryDetailHeader::HandlePrevImage()
{
	if (PreviewImageBrushes.Num() <= 1)
	{
		return FReply::Handled();
	}

	SetPreviewIndex(CurrentPreviewIndex - 1);
	return FReply::Handled();
}

FReply SWorldBLDAssetLibraryDetailHeader::HandleNextImage()
{
	if (PreviewImageBrushes.Num() <= 1)
	{
		return FReply::Handled();
	}

	SetPreviewIndex(CurrentPreviewIndex + 1);
	return FReply::Handled();
}

void SWorldBLDAssetLibraryDetailHeader::BeginLoadPreviewImages(const TArray<FString>& Urls)
{
	++PreviewImagesLoadGeneration;
	const int32 ThisGeneration = PreviewImagesLoadGeneration;

	PreviewImageBrushes.Reset();
	PreviewImageBrushes.Add(FWorldBLDAssetLibraryImageLoader::Get().GetPlaceholderBrush());
	CurrentPreviewIndex = 0;
	bPlaceholderStillPresent = true;

	if (Urls.Num() <= 0)
	{
		Invalidate(EInvalidateWidgetReason::Paint);
		return;
	}

	FWorldBLDAssetLibraryImageLoader::Get().PrefetchImagesFromURLs(Urls);

	const TWeakPtr<SWorldBLDAssetLibraryDetailHeader> WeakHeader =
		StaticCastSharedRef<SWorldBLDAssetLibraryDetailHeader>(AsShared());
	for (const FString& Url : Urls)
	{
		FWorldBLDAssetLibraryImageLoader::Get().LoadImageFromURL(Url, [WeakHeader, ThisGeneration](TSharedPtr<FSlateDynamicImageBrush> Brush)
		{
			const TSharedPtr<SWorldBLDAssetLibraryDetailHeader> Pinned = WeakHeader.Pin();
			if (!Pinned.IsValid() || Pinned->PreviewImagesLoadGeneration != ThisGeneration)
			{
				return;
			}

			if (!Brush.IsValid())
			{
				return;
			}

			Pinned->PreviewImageBrushes.Add(Brush);

			if (Pinned->bPlaceholderStillPresent && Pinned->PreviewImageBrushes.Num() > 1)
			{
				Pinned->PreviewImageBrushes.RemoveAt(0);
				Pinned->CurrentPreviewIndex = 0;
				Pinned->bPlaceholderStillPresent = false;
			}

			Pinned->Invalidate(EInvalidateWidgetReason::Paint);
		});
	}

	Invalidate(EInvalidateWidgetReason::Paint);
}

void SWorldBLDAssetLibraryDetailHeader::SetPreviewIndex(int32 NewIndex)
{
	if (PreviewImageBrushes.Num() <= 0)
	{
		CurrentPreviewIndex = 0;
		return;
	}

	const int32 Count = PreviewImageBrushes.Num();
	int32 Wrapped = NewIndex % Count;
	if (Wrapped < 0)
	{
		Wrapped += Count;
	}
	CurrentPreviewIndex = Wrapped;
	Invalidate(EInvalidateWidgetReason::Paint);
}

EVisibility SWorldBLDAssetLibraryDetailHeader::GetPreviewNavigationVisibility() const
{
	return PreviewUrlCount > 1 ? EVisibility::Visible : EVisibility::Collapsed;
}

const FSlateBrush* SWorldBLDAssetLibraryDetailHeader::GetCurrentPreviewBrushInternal() const
{
	if (PreviewImageBrushes.IsValidIndex(CurrentPreviewIndex) && PreviewImageBrushes[CurrentPreviewIndex].IsValid())
	{
		return PreviewImageBrushes[CurrentPreviewIndex].Get();
	}

	TSharedPtr<FSlateDynamicImageBrush> Placeholder = FWorldBLDAssetLibraryImageLoader::Get().GetPlaceholderBrush();
	return Placeholder.IsValid() ? Placeholder.Get() : nullptr;
}
