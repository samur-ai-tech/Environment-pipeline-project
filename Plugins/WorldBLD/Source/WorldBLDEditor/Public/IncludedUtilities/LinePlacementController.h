// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "WorldBLDEditController.h"
#include "LinePlacement/WorldBLDAssetPalette.h"
#include "ViewportSplineEditing/WorldBLDViewportSplineEditing.h"
#include "Math/RandomStream.h"
#include "LinePlacementController.generated.h"

class USplineComponent;
class SLevelViewport;
class SWidget;

/**
 * Editor tool controller that scatters assets along a user-drawn line or curve.
 *
 * Usage:
 *  1. Push this controller onto the WorldBLD editor mode stack.
 *  2. Click in the viewport to place spline control points.
 *  3. Assets from the selected UWorldBLDAssetPalette are distributed along the spline.
 *  4. Press ESC to finish draw/edit flow and choose how to save placed assets on exit.
 *
 * The tool displays a yellow PDI circle at the cursor position and keeps the temporary
 * spline actor selected at all times to prevent accidental selection of other actors.
 */
UCLASS(BlueprintType, Blueprintable)
class WORLDBLDEDITOR_API ULinePlacementController : public UWorldBLDEditController
{
	GENERATED_BODY()

public:

	// -----------------------------------------------------------------------------------------
	// Settings — driven by the context menu panel
	// -----------------------------------------------------------------------------------------

	/**
	 * Asset palette instance that defines which meshes to scatter and their weights.
	 * Set via the context menu asset picker.
	 */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="LinePlacement")
	TObjectPtr<UWorldBLDAssetPalette> PaletteAsset = nullptr;

	/**
	 * Optional fallback for class-based palettes. If PaletteAsset is null, this class default
	 * object is used as the palette source.
	 */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="LinePlacement")
	TSubclassOf<UWorldBLDAssetPalette> PaletteClass;

	/** When true the spline uses linear (straight) segments; when false uses CurveAuto tangents */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="LinePlacement")
	bool bLinearSpline = true;

	/** When true assets are placed as instances in a single InstancedStaticMeshComponent actor;
	 *  when false each asset is a separate AStaticMeshActor */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="LinePlacement")
	bool bInstanceMeshes = false;

	/**
	 * Each asset is displaced laterally by a random amount in [-OffsetVariation, +OffsetVariation] cm
	 * along the spline's right vector at its placement distance. 0 = no offset (default).
	 */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="LinePlacement", meta=(ClampMin="0.0"))
	float OffsetVariation = 0.0f;

	// -----------------------------------------------------------------------------------------
	// Public API (called by the context menu)
	// -----------------------------------------------------------------------------------------

	/** Clears all placed points and assets so the user can start fresh */
	UFUNCTION(BlueprintCallable, Category="LinePlacement")
	void ResetPlacement();

	/** Called by context menu when the spline type combobox changes */
	void OnSplineTypeChanged(bool bLinear);

	/** Called by context menu when the Instance Meshes checkbox changes */
	void OnInstanceMeshesChanged(bool bInstance);

	/** Called by context menu when a new palette class is selected */
	void OnPaletteClassChanged(TSubclassOf<UWorldBLDAssetPalette> NewClass);

	/** Called by context menu when a new palette asset is selected */
	void OnPaletteAssetChanged(UWorldBLDAssetPalette* NewPaletteAsset);

	/** Called by context menu when the Offset Variation slider changes */
	void OnOffsetVariationChanged(float NewValue);

	/** Called by context menu when Draw/Edit mode changes */
	void SetInteractionMode(EWorldBLDViewportSplineMode NewMode);
	EWorldBLDViewportSplineMode GetInteractionMode() const { return InteractionMode; }

	/** Repositions already placed meshes onto the first ground hit found by downward line traces */
	void SnapPlacedMeshesToGround();

protected:

	// -----------------------------------------------------------------------------------------
	// UWorldBLDEditController overrides
	// -----------------------------------------------------------------------------------------

	virtual void ToolBegin_Implementation() override;
	virtual void ToolActivate_Implementation() override;
	virtual void ToolResign_Implementation() override;
	virtual void TryExitTool_Implementation(bool bForceEnd) override;
	virtual void ToolExit_Implementation(bool bForceEnd) override;

	virtual bool AllowStandardSelectionControls_Implementation() const override;
	virtual bool PressingEscapeTriggersExit_Implementation() const override { return true; }

	virtual bool ConsumesMouseClick_Implementation(int32 Which, bool& bIsPassive) const override;
	virtual void ToolMouseClick_Implementation(int32 WhichButton, bool bPressed) override;
	virtual bool ToolMouseMove_Implementation(int32 X, int32 Y) override;
	virtual void ToolRender_Implementation(FPrimitiveDrawWrapper Renderer) override;
	virtual void ToolKeyEvent_Implementation(FKey Key, bool bPressed, bool bControl, bool bAlt, bool bShift) override;
	virtual void AddIgnoredActorsForMouseTrace(FCollisionQueryParams& TraceParams) const override;

private:

	// -----------------------------------------------------------------------------------------
	// Input state
	// -----------------------------------------------------------------------------------------

	FVector CurrentHoverPoint { FVector::ZeroVector };
	bool    bHoverValid        { false };

	// -----------------------------------------------------------------------------------------
	// Placed control points
	// -----------------------------------------------------------------------------------------

	TArray<FVector> PlacedPoints;

	void UpdateSplineFromPoints();
	void SyncPointsFromSpline();
	void FinishDrawAndEnterEditMode();
	TArray<FWorldBLDViewportSplineItem> BuildSplineItems() const;

	// -----------------------------------------------------------------------------------------
	// Placed assets
	// -----------------------------------------------------------------------------------------

	/** Actor holding InstancedStaticMeshComponents when bInstanceMeshes = true */
	TWeakObjectPtr<AActor> InstancedMeshActor;

	/** Individual AStaticMeshActors when bInstanceMeshes = false */
	TArray<TWeakObjectPtr<AActor>> PlacedStaticActors;

	void RefreshPlacedAssets();
	void ClearPlacedAssets();
	void ForgetTrackedPlacedAssets();
	void PlaceAssetsAlongSpline();
	bool HasPlacedAssetsForCommit() const;
	void ConvertPlacedAssetsToStaticActors();
	void ConvertPlacedAssetsToInstancedActor();

	/** Returns a CDO-like instance of the selected palette, or nullptr */
	const UWorldBLDAssetPalette* GetPaletteInstance() const;

	FRandomStream RandomStream;

	// -----------------------------------------------------------------------------------------
	// Game view
	// -----------------------------------------------------------------------------------------

	void DisableGameViewInActiveViewports();

	// -----------------------------------------------------------------------------------------
	// Context menu overlay
	// -----------------------------------------------------------------------------------------

	TSharedPtr<SWidget>          ContextMenuOverlayWidget;
	TWeakPtr<SLevelViewport>     ContextMenuHostViewport;

	void ShowContextMenu();
	void HideContextMenu();

	EWorldBLDViewportSplineMode InteractionMode = EWorldBLDViewportSplineMode::Draw;
	FWorldBLDViewportSplineStyle SharedSplineStyle;
	FWorldBLDViewportSplineDrawState SharedDrawState;
	FWorldBLDTransientSplineEditor TransientSplineEditor;
};
