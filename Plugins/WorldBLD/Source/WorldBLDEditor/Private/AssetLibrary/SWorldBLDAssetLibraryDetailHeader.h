// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

struct FSlateDynamicImageBrush;
class SWorldBLDCoverImage;

/**
 * Shared Asset Library detail header: cover-image carousel (prev/next) on the left,
 * caller-provided sidebar on the right. Used by both the asset detail drawer and
 * the kit/collection detail page so preview browsing stays identical.
 */
class SWorldBLDAssetLibraryDetailHeader : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDAssetLibraryDetailHeader) {}
		SLATE_DEFAULT_SLOT(FArguments, Sidebar)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	void SetPreviewUrls(const TArray<FString>& Urls);
	const FSlateBrush* GetCurrentPreviewBrush() const;

private:
	FReply HandlePrevImage();
	FReply HandleNextImage();
	void BeginLoadPreviewImages(const TArray<FString>& Urls);
	void SetPreviewIndex(int32 NewIndex);

	EVisibility GetPreviewNavigationVisibility() const;
	const FSlateBrush* GetCurrentPreviewBrushInternal() const;
	TSharedRef<SWidget> MakePreviewNavButton(const TSharedPtr<FSlateDynamicImageBrush>& IconBrush, bool bNavigateNext);

private:
	TSharedPtr<SWorldBLDCoverImage> PreviewImageWidget;
	TSharedPtr<FSlateDynamicImageBrush> PrevChevronBrush;
	TSharedPtr<FSlateDynamicImageBrush> NextChevronBrush;

	TArray<TSharedPtr<FSlateDynamicImageBrush>> PreviewImageBrushes;
	int32 CurrentPreviewIndex = 0;
	int32 PreviewImagesLoadGeneration = 0;
	int32 PreviewUrlCount = 0;
	bool bPlaceholderStillPresent = false;
};
