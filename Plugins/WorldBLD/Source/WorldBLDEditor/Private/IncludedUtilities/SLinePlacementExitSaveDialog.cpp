// Copyright WorldBLD LLC. All rights reserved.

#include "IncludedUtilities/SLinePlacementExitSaveDialog.h"

#include "Editor.h"
#include "Styling/AppStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/SWindow.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "LinePlacementExitSaveDialog"

void SLinePlacementExitSaveDialog::Construct(const FArguments& InArgs)
{
	(void)InArgs;

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FAppStyle::Get().GetBrush("ToolPanel.GroupBorder"))
		.Padding(12.0f)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("Header", "Save Line Placement"))
				.Font(FAppStyle::GetFontStyle("NormalFontBold"))
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(FMargin(0.0f, 8.0f, 0.0f, 12.0f))
			[
				SNew(STextBlock)
				.Text(LOCTEXT("Body", "Choose how to save the placed meshes before exiting the tool."))
				.AutoWrapText(true)
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Right)
			[
				SNew(SUniformGridPanel)
				.SlotPadding(FMargin(4.0f, 0.0f))
				+ SUniformGridPanel::Slot(0, 0)
				[
					SNew(SButton)
					.Text(LOCTEXT("SaveAsStaticMeshActors", "Each mesh is a separate Actor(full control)"))
					.OnClicked(this, &SLinePlacementExitSaveDialog::HandleSaveAsStaticMeshActorsClicked)
				]
				+ SUniformGridPanel::Slot(1, 0)
				[
					SNew(SButton)
					.Text(LOCTEXT("SaveAsInstancedActor", "Batch into a single Actor(best performance)"))
					.OnClicked(this, &SLinePlacementExitSaveDialog::HandleSaveAsInstancedActorClicked)
				]
				+ SUniformGridPanel::Slot(2, 0)
				[
					SNew(SButton)
					.Text(LOCTEXT("Cancel", "Cancel"))
					.OnClicked(this, &SLinePlacementExitSaveDialog::HandleCancelClicked)
				]
			]
		]
	];
}

ELinePlacementExitSaveChoice SLinePlacementExitSaveDialog::ShowModal()
{
	TSharedPtr<SLinePlacementExitSaveDialog> DialogWidget;
	TSharedRef<SWindow> Window = SNew(SWindow)
		.Title(LOCTEXT("Title", "Save Line Placement"))
		.SizingRule(ESizingRule::Autosized)
		.SupportsMaximize(false)
		.SupportsMinimize(false);

	Window->SetContent(SAssignNew(DialogWidget, SLinePlacementExitSaveDialog));

	DialogWidget->SetHostWindow(Window);

	if (GEditor != nullptr)
	{
		GEditor->EditorAddModalWindow(Window);
	}

	return DialogWidget.IsValid() ? DialogWidget->Choice : ELinePlacementExitSaveChoice::Cancel;
}

void SLinePlacementExitSaveDialog::SetHostWindow(TSharedRef<SWindow> InHostWindow)
{
	HostWindow = InHostWindow;
}

FReply SLinePlacementExitSaveDialog::HandleSaveAsStaticMeshActorsClicked()
{
	Choice = ELinePlacementExitSaveChoice::StaticMeshActors;

	if (TSharedPtr<SWindow> Pinned = HostWindow.Pin())
	{
		Pinned->RequestDestroyWindow();
	}

	return FReply::Handled();
}

FReply SLinePlacementExitSaveDialog::HandleSaveAsInstancedActorClicked()
{
	Choice = ELinePlacementExitSaveChoice::InstancedActor;

	if (TSharedPtr<SWindow> Pinned = HostWindow.Pin())
	{
		Pinned->RequestDestroyWindow();
	}

	return FReply::Handled();
}

FReply SLinePlacementExitSaveDialog::HandleCancelClicked()
{
	Choice = ELinePlacementExitSaveChoice::Cancel;

	if (TSharedPtr<SWindow> Pinned = HostWindow.Pin())
	{
		Pinned->RequestDestroyWindow();
	}

	return FReply::Handled();
}

#undef LOCTEXT_NAMESPACE
