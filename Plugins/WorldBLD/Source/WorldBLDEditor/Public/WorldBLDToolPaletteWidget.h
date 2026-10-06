// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "EditorUtilityWidget.h"
#include "Engine/DataAsset.h"
#include "WorldBLDToolPaletteWidget.generated.h"

class UWorldBLDEditController;
class UWorldBLDEdMode;
class UWorldBLDAuthSubsystem;

/**
 * Legacy compatibility shim for pre-1.4.1 tool palette widgets.
 * The toolbar-first flow no longer depends on this class, but old binaries/assets still reference it.
 */
UCLASS(BlueprintType, Blueprintable, Abstract)
class WORLDBLDEDITOR_API UWorldBLDToolPaletteWidget : public UEditorUtilityWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="Tool")
	FName ToolId {NAME_None};

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="Tool")
	FText ToolDisplayName;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="Tool")
	TSoftObjectPtr<UTexture2D> ToolTabIcon;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="Tool")
	bool bIsAlwaysEnabled {false};

	UFUNCTION(BlueprintPure, Category="License")
	bool IsLicensed(UWorldBLDAuthSubsystem* Subsystem);

	UFUNCTION(BlueprintNativeEvent, Category="Tool")
	void ToolPaletteActivate();

	UFUNCTION(BlueprintNativeEvent, Category="Tool")
	void ToolPaletteActorSelectionChanged(
		UWorldBLDEditController* ActiveTool,
		const TArray<AActor*>& NewlySelected,
		const TArray<AActor*>& Deselected,
		const TArray<AActor*>& CurrentSelectionSet);

	UFUNCTION(BlueprintNativeEvent, Category="Tool")
	void ToolPaletteDeactivate();

	UFUNCTION(BlueprintCallable, Category="Tool")
	void ToolMakeForemostPalette(bool bForceFocused = false);

	UPROPERTY(Transient, BlueprintReadOnly, VisibleAnywhere, Category="Tool")
	TObjectPtr<UWorldBLDEdMode> EdMode;

protected:
	virtual void ToolPaletteActivate_Implementation() {}
	virtual void ToolPaletteDeactivate_Implementation() {}
	virtual void ToolPaletteActorSelectionChanged_Implementation(
		UWorldBLDEditController* ActiveTool,
		const TArray<AActor*>& NewlySelected,
		const TArray<AActor*>& Deselected,
		const TArray<AActor*>& CurrentSelectionSet)
	{
		(void)ActiveTool;
		(void)NewlySelected;
		(void)Deselected;
		(void)CurrentSelectionSet;
	}
};

UCLASS(BlueprintType, Blueprintable)
class WORLDBLDEDITOR_API UWorldBLDToolPaletteWidgetExtended : public UWorldBLDToolPaletteWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category="Tool")
	TSubclassOf<UWorldBLDEditController> MainSubtoolClass;

protected:
	UPROPERTY(BlueprintReadOnly, Category="Tool")
	TObjectPtr<UWorldBLDEditController> MainSubtool {nullptr};

	virtual void ToolPaletteActivate_Implementation() override;
	virtual void ToolPaletteDeactivate_Implementation() override;
};

UCLASS(BlueprintType)
class WORLDBLDEDITOR_API UWorldBLDToolBundle : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="WorldBLD", Meta=(Untracked))
	TObjectPtr<UTexture2D> ToolIcon;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="WorldBLD", Meta=(Untracked))
	TArray<TObjectPtr<UWorldBLDToolPaletteWidget>> ToolWidgets;
};
