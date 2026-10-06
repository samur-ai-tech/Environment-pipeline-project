// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Brushes/SlateDynamicImageBrush.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateTypes.h"
#include "Widgets/SCompoundWidget.h"

class SWindow;

/**
 * Modeless WorldBLD learning/resources hub opened from the viewport Learn button.
 */
class SWorldBLDResourcesDialog final : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDResourcesDialog) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	void SetHostWindow(const TSharedRef<SWindow>& InWindow);

	/** Opens (or brings to front) the Resources dialog. */
	static void Open();

	virtual bool SupportsKeyboardFocus() const override { return true; }

private:
	TSharedRef<SWidget> BuildResourceRow(
		const FText& Title,
		const FText& Subtitle,
		const FSlateBrush* LeadingIcon,
		const FSlateBrush* TrailingIcon,
		FLinearColor LeadingIconTint,
		const FSimpleDelegate& OnClicked);

	FReply HandleCloseClicked();
	FReply HandleDocsClicked();
	FReply HandleYouTubeClicked();
	FReply HandleDemoMapClicked();
	FReply HandleBrowsePresetsClicked();
	FReply HandleCheckForUpdatesClicked();
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;
	void CloseDialog();

	TWeakPtr<SWindow> HostWindow;

	TSharedPtr<FSlateDynamicImageBrush> YouTubeIconBrush;
	TSharedPtr<FSlateDynamicImageBrush> CloseIconBrush;
	TSharedPtr<FButtonStyle> RowButtonStyle;
	TSharedPtr<FButtonStyle> CheckUpdatesButtonStyle;
	TSharedPtr<FSlateBrush> RowAccentBrush;
	TSharedPtr<FSlateBrush> IconWellBrush;
	TSharedPtr<FSlateBrush> PanelBrush;
	TSharedPtr<FSlateBrush> FooterBrush;
};
