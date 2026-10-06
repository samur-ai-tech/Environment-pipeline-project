// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Brushes/SlateDynamicImageBrush.h"
#include "Widgets/SCompoundWidget.h"

class IDetailsView;
class SWindow;
class UWorldBLDLandscapePaintImportOptions;
struct FSlateBrush;

class SWorldBLDLandscapePaintDialog : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWorldBLDLandscapePaintDialog) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs, TSharedRef<SWindow> InOwningWindow, UWorldBLDLandscapePaintImportOptions* InOptions);

	bool WasAccepted() const { return bAccepted; }

private:
	FReply OnImportClicked();
	FReply OnCancelClicked();
	bool CanImport() const;
	const FSlateBrush* GetToolIconBrush() const;

	TWeakPtr<SWindow> OwningWindow;
	TObjectPtr<UWorldBLDLandscapePaintImportOptions> Options = nullptr;
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
