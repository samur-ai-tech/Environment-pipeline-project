// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDToolPaletteWidget.h"

#include "Authorization/WorldBLDAuthSubsystem.h"
#include "WorldBLDEditController.h"
#include "WorldBLDEditorToolkit.h"

bool UWorldBLDToolPaletteWidget::IsLicensed(UWorldBLDAuthSubsystem* Subsystem)
{
	if (!IsValid(Subsystem))
	{
		return false;
	}

	return Subsystem->HasLicenseForTool(ToolId.ToString());
}

void UWorldBLDToolPaletteWidget::ToolMakeForemostPalette(bool bForceFocused)
{
	if (IsValid(EdMode))
	{
		EdMode->SwitchToToolPalette(this, bForceFocused);
	}
}

void UWorldBLDToolPaletteWidgetExtended::ToolPaletteActivate_Implementation()
{
	if (!IsValid(EdMode) || !IsValid(MainSubtoolClass))
	{
		return;
	}

	MainSubtool = CreateWidget<UWorldBLDEditController>(this, MainSubtoolClass.Get());
	if (IsValid(MainSubtool))
	{
		EdMode->PushEditController(MainSubtool);
	}
}

void UWorldBLDToolPaletteWidgetExtended::ToolPaletteDeactivate_Implementation()
{
	if (IsValid(MainSubtool) && IsValid(EdMode))
	{
		MainSubtool->TryExitTool(/* bForceEnd */ false);
	}
}
