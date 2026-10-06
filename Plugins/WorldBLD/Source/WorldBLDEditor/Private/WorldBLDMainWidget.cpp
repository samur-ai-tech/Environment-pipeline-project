// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDMainWidget.h"

#include "Components/PanelWidget.h"
#include "Components/WidgetSwitcher.h"
#include "Editor.h"
#include "WorldBLDEditorToolkit.h"
#include "WorldBLDToolButtonWidget.h"
#include "WorldBLDToolPaletteWidget.h"

void UWorldBLDMainWidget::SetTools(TArray<UWorldBLDToolPaletteWidget*> Tools)
{
	if (TabButtonContainer != nullptr)
	{
		TabButtonContainer->ClearChildren();
	}
	if (MainWidgetSwitcher != nullptr)
	{
		MainWidgetSwitcher->ClearChildren();
	}

	AssignedWidgets.Reset();

	UWorld* World = (GEditor != nullptr) ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (World == nullptr)
	{
		OnToolsSet();
		return;
	}

	for (UWorldBLDToolPaletteWidget* Tool : Tools)
	{
		if (!IsValid(Tool))
		{
			continue;
		}

		FLocalWidgetSet& WidgetSet = AssignedWidgets.AddDefaulted_GetRef();
		WidgetSet.UniqueId = Tool->ToolId;
		WidgetSet.BodyContent = Tool;

		if ((ButtonWidgetClass != nullptr) && (TabButtonContainer != nullptr))
		{
			UWorldBLDToolButtonWidget* NewButton = CreateWidget<UWorldBLDToolButtonWidget>(World, ButtonWidgetClass);
			if (IsValid(NewButton))
			{
				NewButton->OptionalId = Tool->ToolId;
				NewButton->SetIcon(Tool->ToolTabIcon.LoadSynchronous());
				NewButton->SetCustomTooltip(Tool->ToolDisplayName);
				NewButton->OnClicked.AddUniqueDynamic(this, &UWorldBLDMainWidget::OnButtonClicked);
				TabButtonContainer->AddChild(NewButton);
				WidgetSet.ButtonContent = NewButton;
			}
		}

		if (MainWidgetSwitcher != nullptr)
		{
			MainWidgetSwitcher->AddChild(Tool);
		}
	}

	OnToolsSet();
	SetActiveTool(ActiveTool);
}

void UWorldBLDMainWidget::SetActiveTool(const FName& NewActiveTool)
{
	for (const FLocalWidgetSet& WidgetSet : AssignedWidgets)
	{
		UWorldBLDToolPaletteWidget* Tool = WidgetSet.BodyContent.Get();
		if (IsValid(Tool) && (ActiveTool == WidgetSet.UniqueId))
		{
			Tool->ToolPaletteDeactivate();
		}

		const bool bIsSelected = (WidgetSet.UniqueId == NewActiveTool);
		if (WidgetSet.ButtonContent.IsValid())
		{
			WidgetSet.ButtonContent->SetHighlighted(bIsSelected);
		}

		if (bIsSelected)
		{
			if ((MainWidgetSwitcher != nullptr) && IsValid(Tool))
			{
				MainWidgetSwitcher->SetActiveWidget(Tool);
			}
			NewToolTabSelected(Tool);
			if (IsValid(Tool))
			{
				Tool->ToolPaletteActivate();
			}
		}
	}

	ActiveTool = NewActiveTool;
}

UWorldBLDToolPaletteWidget* UWorldBLDMainWidget::GetActiveTool() const
{
	for (const FLocalWidgetSet& WidgetSet : AssignedWidgets)
	{
		UWorldBLDToolPaletteWidget* Tool = WidgetSet.BodyContent.Get();
		if (IsValid(Tool) && (ActiveTool == WidgetSet.UniqueId))
		{
			return Tool;
		}
	}

	return nullptr;
}

FName UWorldBLDMainWidget::GetFirstToolName() const
{
	return AssignedWidgets.IsEmpty() ? NAME_None : AssignedWidgets[0].UniqueId;
}

void UWorldBLDMainWidget::ResetContent()
{
	AssignedWidgets.Reset();
	if (TabButtonContainer != nullptr)
	{
		TabButtonContainer->ClearChildren();
	}
	if (MainWidgetSwitcher != nullptr)
	{
		MainWidgetSwitcher->ClearChildren();
	}
}

void UWorldBLDMainWidget::MakeFirstEnabledPaletteActive()
{
	for (const FLocalWidgetSet& WidgetSet : AssignedWidgets)
	{
		if (WidgetSet.BodyContent.IsValid() && WidgetSet.ButtonContent.IsValid() && WidgetSet.ButtonContent->bButtonIsEnabled)
		{
			SetActiveTool(WidgetSet.UniqueId);
			return;
		}
	}
}

void UWorldBLDMainWidget::OnButtonClicked(UWidget* Widget)
{
	if (const UWorldBLDToolButtonWidget* ToolButton = Cast<UWorldBLDToolButtonWidget>(Widget))
	{
		SetActiveTool(ToolButton->OptionalId);
	}
}

void UWorldBLDMainWidget::ResetToDefaultController()
{
	if (IsValid(EdMode))
	{
		EdMode->ClearToolModeStack();
		EdMode->InstallDefaultSelectionTool();
	}
}
