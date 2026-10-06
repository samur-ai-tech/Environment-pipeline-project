// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

class SWindow;

enum class ELinePlacementExitSaveChoice : uint8
{
	StaticMeshActors,
	InstancedActor,
	Cancel
};

class SLinePlacementExitSaveDialog : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SLinePlacementExitSaveDialog) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	static ELinePlacementExitSaveChoice ShowModal();

private:
	void SetHostWindow(TSharedRef<SWindow> InHostWindow);
	FReply HandleSaveAsStaticMeshActorsClicked();
	FReply HandleSaveAsInstancedActorClicked();
	FReply HandleCancelClicked();

private:
	ELinePlacementExitSaveChoice Choice = ELinePlacementExitSaveChoice::Cancel;
	TWeakPtr<SWindow> HostWindow;
};
