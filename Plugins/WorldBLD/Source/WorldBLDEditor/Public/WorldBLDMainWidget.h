// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "Blueprint/UserWidget.h"
#include "WorldBLDMainWidget.generated.h"

class UPanelWidget;
class UWidgetSwitcher;
class UWorldBLDEditController;
class UWorldBLDEdMode;
class UWorldBLDToolButtonWidget;
class UWorldBLDToolPaletteWidget;

/**
 * Legacy compatibility shim for the old inline WorldBLD main widget.
 */
UCLASS(BlueprintType, Blueprintable, Abstract)
class UWorldBLDMainWidget : public UUserWidget
{
	GENERATED_BODY()

	/* friends: */
	friend class UWorldBLDEdMode;

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Meta=(BindWidget), Category="Tool")
	TObjectPtr<UPanelWidget> TabButtonContainer;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Meta=(BindWidget), Category="Tool")
	TObjectPtr<UWidgetSwitcher> MainWidgetSwitcher;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Tool|Design")
	TSubclassOf<UWorldBLDToolButtonWidget> ButtonWidgetClass;

	void SetTools(TArray<UWorldBLDToolPaletteWidget*> Tools);
	void SetActiveTool(const FName& NewActiveTool);
	UWorldBLDToolPaletteWidget* GetActiveTool() const;
	FName GetFirstToolName() const;

	UFUNCTION(BlueprintImplementableEvent, Category="Tool")
	void NewToolTabSelected(UWorldBLDToolPaletteWidget* NewTool);

	UFUNCTION(BlueprintImplementableEvent, Category="Tool")
	void OnToolsSet();

	UFUNCTION(BlueprintCallable, Category="Tool")
	void ResetToDefaultController();

	UPROPERTY(Transient, BlueprintReadOnly, VisibleAnywhere, Category="Tool")
	TObjectPtr<UWorldBLDEdMode> EdMode;

	void ResetContent();
	void MakeFirstEnabledPaletteActive();

protected:
	struct FLocalWidgetSet
	{
		FName UniqueId {NAME_None};
		TWeakObjectPtr<UWorldBLDToolPaletteWidget> BodyContent;
		TWeakObjectPtr<UWorldBLDToolButtonWidget> ButtonContent;
	};

	TArray<FLocalWidgetSet> AssignedWidgets;
	FName ActiveTool {NAME_None};

	UFUNCTION()
	void OnButtonClicked(UWidget* Widget);
};
