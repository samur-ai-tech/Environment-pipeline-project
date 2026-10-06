// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Widgets/Input/SComboBox.h"

class ULinePlacementController;
class UWorldBLDAssetPalette;
enum class EWorldBLDViewportSplineMode : uint8;
struct FAssetData;

/**
 * Viewport-overlay context menu panel for ULinePlacementController.
 * Provides controls for:
 *  - Asset palette picker (UWorldBLDAssetPalette BP subclass)
 *  - Spline type selector (Linear / Curve)
 *  - Instance Meshes toggle
 *  - Reset button
 */
class SLinePlacementContextMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SLinePlacementContextMenu)
	{}
		SLATE_ARGUMENT(TWeakObjectPtr<ULinePlacementController>, Controller)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:

	TWeakObjectPtr<ULinePlacementController> Controller;

	// -----------------------------------------------------------------------------------------
	// Spline type combo
	// -----------------------------------------------------------------------------------------

	TArray<TSharedPtr<FString>> SplineTypeOptions;
	TSharedPtr<SComboBox<TSharedPtr<FString>>> SplineTypeCombo;
	TSharedPtr<FString> CurrentSplineType;

	TSharedRef<SWidget> GenerateSplineTypeOptionWidget(TSharedPtr<FString> Item) const;
	void OnSplineTypeSelectionChanged(TSharedPtr<FString> NewSelection, ESelectInfo::Type SelectionType);
	FText GetSplineTypeLabel() const;

	// -----------------------------------------------------------------------------------------
	// Draw/Edit mode combo
	// -----------------------------------------------------------------------------------------

	TArray<TSharedPtr<FString>> InteractionModeOptions;
	TSharedPtr<SComboBox<TSharedPtr<FString>>> InteractionModeCombo;
	TSharedPtr<FString> CurrentInteractionMode;
	TSharedRef<SWidget> GenerateInteractionModeOptionWidget(TSharedPtr<FString> Item) const;
	void OnInteractionModeSelectionChanged(TSharedPtr<FString> NewSelection, ESelectInfo::Type SelectionType);
	FText GetInteractionModeLabel() const;

	// -----------------------------------------------------------------------------------------
	// Instance meshes checkbox
	// -----------------------------------------------------------------------------------------

	ECheckBoxState GetInstanceMeshesCheckState() const;
	void OnInstanceMeshesCheckStateChanged(ECheckBoxState NewState);

	// -----------------------------------------------------------------------------------------
	// Asset palette picker
	// -----------------------------------------------------------------------------------------

	TOptional<FAssetData> GetSelectedPaletteAsset() const;
	void OnPaletteAssetSelected(const FAssetData& AssetData);

	// -----------------------------------------------------------------------------------------
	// Offset variation slider
	// -----------------------------------------------------------------------------------------

	TOptional<float> GetOffsetVariationValue() const;
	void OnOffsetVariationValueChanged(float NewValue);

	// -----------------------------------------------------------------------------------------
	// Reset button
	// -----------------------------------------------------------------------------------------

	FReply OnSnapMeshesToGroundClicked();
	FReply OnResetClicked();
};
