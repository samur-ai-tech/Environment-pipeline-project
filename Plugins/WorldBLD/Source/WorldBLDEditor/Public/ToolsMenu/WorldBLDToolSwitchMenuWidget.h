// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/Widget.h"

#include "WorldBLDToolSwitchMenuWidget.generated.h"

class SWorldBLDToolSwitchMenu;

/**
 * UMG wrapper for the persistent SWorldBLDToolSwitchMenu tab strip.
 */
UCLASS()
class WORLDBLDEDITOR_API UWorldBLDToolSwitchMenuWidget : public UWidget
{
	GENERATED_BODY()

public:
	UWorldBLDToolSwitchMenuWidget(const FObjectInitializer& ObjectInitializer);

protected:
	//~ Begin UWidget interface
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void ReleaseSlateResources(bool bReleaseChildren) override;
	//~ End UWidget interface

private:
	TSharedPtr<SWorldBLDToolSwitchMenu> MyMenu;
};

