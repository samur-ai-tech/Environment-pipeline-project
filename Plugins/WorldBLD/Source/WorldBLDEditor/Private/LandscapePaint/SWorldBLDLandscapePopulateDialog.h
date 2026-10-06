// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Brushes/SlateDynamicImageBrush.h"
#include "Widgets/SCompoundWidget.h"

class IDetailsView;
class SWindow;
class UWorldBLDLandscapePopulateOptions;
struct FSlateBrush;

class SWorldBLDLandscapePopulateDialog : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDLandscapePopulateDialog) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs, TSharedRef<SWindow> InOwningWindow, UWorldBLDLandscapePopulateOptions* InOptions);

	bool WasAccepted() const { return bAccepted; }

private:
	FReply OnContinueClicked();
	FReply OnCancelClicked();
	bool CanContinue() const;
	const FSlateBrush* GetToolIconBrush() const;

	TWeakPtr<SWindow> OwningWindow;
	TObjectPtr<UWorldBLDLandscapePopulateOptions> Options = nullptr;
	TSharedPtr<IDetailsView> DetailsView;
	TSharedPtr<FSlateDynamicImageBrush> ToolIconBrush;
	TSharedPtr<FSlateBrush> PanelBrush;
	TSharedPtr<FSlateBrush> SidebarBrush;
	TSharedPtr<FSlateBrush> FooterBrush;
	TSharedPtr<FSlateBrush> CardBrush;
	TSharedPtr<FSlateBrush> IconWellBrush;
	TSharedPtr<FSlateBrush> AccentBrush;
	bool bAccepted = false;
};
