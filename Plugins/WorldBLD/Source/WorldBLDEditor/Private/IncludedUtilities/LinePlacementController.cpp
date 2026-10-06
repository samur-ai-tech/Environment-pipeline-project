// Copyright WorldBLD LLC. All rights reserved.

#include "IncludedUtilities/LinePlacementController.h"

#include "IncludedUtilities/SLinePlacementContextMenu.h"
#include "IncludedUtilities/SLinePlacementExitSaveDialog.h"

#include "PrimitiveDrawWrapper.h"
#include "LinePlacement/WorldBLDAssetPalette.h"

#include "Components/SplineComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"

#include "Editor.h"
#include "LevelEditorViewport.h"
#include "LevelEditor.h"
#include "SLevelViewport.h"
#include "Modules/ModuleManager.h"

#include "ContextMenu/SWorldBLDContextMenuViewportOverlay.h"
#include "ContextMenu/SMinimizableWorldBLDMenuPanel.h"

#include "GameFramework/Actor.h"
#include "CollisionQueryParams.h"
#include "ScopedTransaction.h"
#include "Engine/EngineTypes.h"
#include "TraceHitFilter.h"

namespace
{
	FVector ComputePlacementCenter(const TArray<FTransform>& WorldTransforms)
	{
		if (WorldTransforms.IsEmpty())
		{
			return FVector::ZeroVector;
		}

		FBox Bounds(EForceInit::ForceInit);
		for (const FTransform& Transform : WorldTransforms)
		{
			Bounds += Transform.GetLocation();
		}

		return Bounds.IsValid ? Bounds.GetCenter() : FVector::ZeroVector;
	}

	FVector ComputePlacementCenter(const TMap<UStaticMesh*, TArray<FTransform>>& MeshToWorldTransforms)
	{
		FBox Bounds(EForceInit::ForceInit);
		for (const TPair<UStaticMesh*, TArray<FTransform>>& Pair : MeshToWorldTransforms)
		{
			for (const FTransform& Transform : Pair.Value)
			{
				Bounds += Transform.GetLocation();
			}
		}

		return Bounds.IsValid ? Bounds.GetCenter() : FVector::ZeroVector;
	}
}

// ================================================================================================
// UWorldBLDEditController overrides
// ================================================================================================

void ULinePlacementController::ToolBegin_Implementation()
{
	Super::ToolBegin_Implementation();

	RandomStream.Initialize(FMath::Rand());
	InteractionMode = EWorldBLDViewportSplineMode::Draw;

	DisableGameViewInActiveViewports();
	TransientSplineEditor.EnsureSpawned(this, TEXT("LinePlacement_SplinePreview"));
	UpdateSplineFromPoints();
	ShowContextMenu();
}

void ULinePlacementController::ToolActivate_Implementation()
{
	Super::ToolActivate_Implementation();

	TransientSplineEditor.SelectInEditor(this);

	if (!ContextMenuOverlayWidget.IsValid())
	{
		ShowContextMenu();
	}
}

void ULinePlacementController::ToolResign_Implementation()
{
	Super::ToolResign_Implementation();

	HideContextMenu();
}

void ULinePlacementController::TryExitTool_Implementation(bool bForceEnd)
{
	// Force exits are used by map teardown and stack clearing, so do not prompt.
	if (bForceEnd)
	{
		Super::TryExitTool_Implementation(true);
		return;
	}

	// Preserve existing staged ESC behavior: Draw (with points) transitions to Edit first.
	if (InteractionMode == EWorldBLDViewportSplineMode::Draw && PlacedPoints.Num() > 0)
	{
		FinishDrawAndEnterEditMode();
		return;
	}

	if (HasPlacedAssetsForCommit())
	{
		const ELinePlacementExitSaveChoice Choice = SLinePlacementExitSaveDialog::ShowModal();
		if (Choice == ELinePlacementExitSaveChoice::Cancel)
		{
			return;
		}

		const FScopedTransaction Transaction(
			NSLOCTEXT("LinePlacementController", "ConvertPlacementOnExit", "Convert Line Placement Save Format"));
		switch (Choice)
		{
			case ELinePlacementExitSaveChoice::StaticMeshActors:
				ConvertPlacedAssetsToStaticActors();
				ForgetTrackedPlacedAssets();
				break;
			case ELinePlacementExitSaveChoice::InstancedActor:
				ConvertPlacedAssetsToInstancedActor();
				ForgetTrackedPlacedAssets();
				break;
			case ELinePlacementExitSaveChoice::Cancel:
			default:
				return;
		}
	}

	Super::TryExitTool_Implementation(false);
}

void ULinePlacementController::ToolExit_Implementation(bool bForceEnd)
{
	// Keep ESC behavior intuitive by stepping through mode transitions before fully exiting:
	// Draw (with points) -> Edit; Edit -> exit.
	if (!bForceEnd)
	{
		if (InteractionMode == EWorldBLDViewportSplineMode::Draw && PlacedPoints.Num() > 0)
		{
			FinishDrawAndEnterEditMode();
			return;
		}
	}

	// On force exit, discard all placed assets; on normal ESC, keep them
	if (bForceEnd)
	{
		ClearPlacedAssets();
	}

	TransientSplineEditor.Destroy(this);
	HideContextMenu();

	Super::ToolExit_Implementation(bForceEnd);
}

bool ULinePlacementController::AllowStandardSelectionControls_Implementation() const
{
	// Edit mode intentionally hands interaction back to Unreal's native spline component
	// visualizer so point selection and transform handles behave like a normal selected spline.
	return InteractionMode == EWorldBLDViewportSplineMode::Edit;
}

bool ULinePlacementController::ConsumesMouseClick_Implementation(int32 Which, bool& bIsPassive) const
{
	if (Which != 0)
	{
		bIsPassive = false;
		return false;
	}

	if (InteractionMode == EWorldBLDViewportSplineMode::Edit)
	{
		bIsPassive = false;
		return false;
	}

	bIsPassive = false;
	return true;
}

void ULinePlacementController::ToolMouseClick_Implementation(int32 WhichButton, bool bPressed)
{
	if (WhichButton != 0 || !bPressed)
	{
		return;
	}

	if (!bHoverValid)
	{
		return;
	}

	if (InteractionMode == EWorldBLDViewportSplineMode::Draw)
	{
		PlacedPoints.Add(CurrentHoverPoint);
		UpdateSplineFromPoints();
		RefreshPlacedAssets();
	}
	else
	{
		TransientSplineEditor.SelectInEditor(this);
	}

	// Keep the spline actor selected
	TransientSplineEditor.SelectInEditor(this);
}

bool ULinePlacementController::ToolMouseMove_Implementation(int32 X, int32 Y)
{
	bHoverValid = TryGetMouseHitPoint(X, Y, CurrentHoverPoint);
	SharedDrawState.bHoverValid = bHoverValid;
	SharedDrawState.HoverPoint = CurrentHoverPoint;
	return false; // Don't consume move events
}

void ULinePlacementController::ToolRender_Implementation(FPrimitiveDrawWrapper Renderer)
{
	TransientSplineEditor.TickDragRelease([this]()
	{
		SyncPointsFromSpline();
		RefreshPlacedAssets();
	});

	SharedDrawState.Mode = InteractionMode;
	SharedDrawState.bHoverValid = bHoverValid;
	SharedDrawState.HoverPoint = CurrentHoverPoint;
	SharedDrawState.SelectedItemId = PlacedPoints.Num() > 0 ? 0 : INDEX_NONE;
	SharedDrawState.ActiveItemId = (InteractionMode == EWorldBLDViewportSplineMode::Draw && PlacedPoints.Num() > 0) ? 0 : INDEX_NONE;

	TArray<FWorldBLDViewportSplineItem> Items = BuildSplineItems();
	SharedSplineStyle.HoverCircleRadius = FMath::Max(10.0f, OffsetVariation > 0.0f ? OffsetVariation : 50.0f);
	FWorldBLDViewportSplineRenderer::DrawSplineItems(Renderer, Items, SharedDrawState, SharedSplineStyle, false);
	FWorldBLDViewportSplineRenderer::DrawHoverCircle(Renderer, SharedDrawState, SharedSplineStyle);

	const FWorldBLDViewportSplineItem* ActiveItem = Items.Num() > 0 ? &Items[0] : nullptr;
	FWorldBLDViewportSplineRenderer::DrawPendingPreview(Renderer, ActiveItem, SharedDrawState, SharedSplineStyle);
}

void ULinePlacementController::ToolKeyEvent_Implementation(FKey Key, bool bPressed, bool bControl, bool bAlt, bool bShift)
{
	if (!bPressed)
	{
		return;
	}

	if (Key == EKeys::Enter)
	{
		FinishDrawAndEnterEditMode();
		return;
	}
}

void ULinePlacementController::AddIgnoredActorsForMouseTrace(FCollisionQueryParams& TraceParams) const
{
	Super::AddIgnoredActorsForMouseTrace(TraceParams);
	TransientSplineEditor.AddIgnoredActors(TraceParams);

	if (AActor* ISMA = InstancedMeshActor.Get())
	{
		TraceParams.AddIgnoredActor(ISMA);
	}

	for (const TWeakObjectPtr<AActor>& WeakActor : PlacedStaticActors)
	{
		if (AActor* A = WeakActor.Get())
		{
			TraceParams.AddIgnoredActor(A);
		}
	}
}

// ================================================================================================
// Public API
// ================================================================================================

void ULinePlacementController::ResetPlacement()
{
	PlacedPoints.Empty();
	ClearPlacedAssets();
	UpdateSplineFromPoints();
}

void ULinePlacementController::OnSplineTypeChanged(bool bLinear)
{
	bLinearSpline = bLinear;
	UpdateSplineFromPoints();
	RefreshPlacedAssets();
}

void ULinePlacementController::OnInstanceMeshesChanged(bool bInstance)
{
	if (bInstanceMeshes != bInstance)
	{
		bInstanceMeshes = bInstance;
		ClearPlacedAssets();
		RefreshPlacedAssets();
	}
}

void ULinePlacementController::OnPaletteClassChanged(TSubclassOf<UWorldBLDAssetPalette> NewClass)
{
	PaletteClass = NewClass;
	PaletteAsset = nullptr;
	ClearPlacedAssets();
	RefreshPlacedAssets();
}

void ULinePlacementController::OnPaletteAssetChanged(UWorldBLDAssetPalette* NewPaletteAsset)
{
	PaletteAsset = NewPaletteAsset;
	if (IsValid(NewPaletteAsset))
	{
		PaletteClass = NewPaletteAsset->GetClass();
	}
	else
	{
		PaletteClass = nullptr;
	}
	ClearPlacedAssets();
	RefreshPlacedAssets();
}

void ULinePlacementController::OnOffsetVariationChanged(float NewValue)
{
	OffsetVariation = FMath::Max(0.0f, NewValue);
	RefreshPlacedAssets();
}

void ULinePlacementController::SnapPlacedMeshesToGround()
{
	UWorld* World = GetWorld();
	if (!IsValid(World))
	{
		return;
	}

	constexpr float TraceHeight = 100000.0f;
	bool bAnySnapped = false;

	FCollisionQueryParams TraceParams(SCENE_QUERY_STAT(LinePlacementSnapToGround), true);
	AddIgnoredActorsForMouseTrace(TraceParams);

	FScopedTransaction Transaction(
		NSLOCTEXT("LinePlacementController", "SnapMeshesToGround", "Snap Line Placement Meshes To Ground"));

	for (TWeakObjectPtr<AActor>& WeakActor : PlacedStaticActors)
	{
		AActor* Actor = WeakActor.Get();
		if (!IsValid(Actor))
		{
			continue;
		}

		const FVector CurrentLocation = Actor->GetActorLocation();
		FHitResult Hit;
		const FVector TraceStart = CurrentLocation + FVector(0.0f, 0.0f, TraceHeight);
		const FVector TraceEnd = CurrentLocation - FVector(0.0f, 0.0f, TraceHeight);
		TArray<FHitResult> Hits;
		World->LineTraceMultiByChannel(Hits, TraceStart, TraceEnd, ECC_Visibility, TraceParams);
		if (!WorldBLDPlacementTrace::FindFirstValidPlacementHit(Hits, Hit))
		{
			continue;
		}

		FVector NewLocation = CurrentLocation;
		NewLocation.Z = Hit.Location.Z;
		if (!NewLocation.Equals(CurrentLocation, KINDA_SMALL_NUMBER))
		{
			Actor->Modify();
			Actor->SetActorLocation(NewLocation);
			bAnySnapped = true;
		}
	}

	if (AActor* ISMActor = InstancedMeshActor.Get())
	{
		TArray<UInstancedStaticMeshComponent*> ISMCs;
		ISMActor->GetComponents<UInstancedStaticMeshComponent>(ISMCs);
		for (UInstancedStaticMeshComponent* ISMC : ISMCs)
		{
			if (!IsValid(ISMC))
			{
				continue;
			}

			const int32 InstanceCount = ISMC->GetInstanceCount();
			if (InstanceCount == 0)
			{
				continue;
			}

			bool bComponentModified = false;
			for (int32 InstanceIdx = 0; InstanceIdx < InstanceCount; ++InstanceIdx)
			{
				FTransform InstanceWorldTransform;
				if (!ISMC->GetInstanceTransform(InstanceIdx, InstanceWorldTransform, true))
				{
					continue;
				}

				const FVector CurrentLocation = InstanceWorldTransform.GetLocation();
				FHitResult Hit;
				const FVector TraceStart = CurrentLocation + FVector(0.0f, 0.0f, TraceHeight);
				const FVector TraceEnd = CurrentLocation - FVector(0.0f, 0.0f, TraceHeight);
				TArray<FHitResult> Hits;
				World->LineTraceMultiByChannel(Hits, TraceStart, TraceEnd, ECC_Visibility, TraceParams);
				if (!WorldBLDPlacementTrace::FindFirstValidPlacementHit(Hits, Hit))
				{
					continue;
				}

				FVector NewLocation = CurrentLocation;
				NewLocation.Z = Hit.Location.Z;
				if (NewLocation.Equals(CurrentLocation, KINDA_SMALL_NUMBER))
				{
					continue;
				}

				if (!bComponentModified)
				{
					ISMC->Modify();
					bComponentModified = true;
				}

				InstanceWorldTransform.SetLocation(NewLocation);
				ISMC->UpdateInstanceTransform(InstanceIdx, InstanceWorldTransform, true, false, true);
				bAnySnapped = true;
			}

			if (bComponentModified)
			{
				ISMC->MarkRenderStateDirty();
			}
		}
	}

	if (!bAnySnapped)
	{
		Transaction.Cancel();
	}
}

void ULinePlacementController::UpdateSplineFromPoints()
{
	TransientSplineEditor.SyncFromPoints(PlacedPoints, bLinearSpline);
}

void ULinePlacementController::SyncPointsFromSpline()
{
	TransientSplineEditor.SyncToPoints(PlacedPoints);
}

void ULinePlacementController::FinishDrawAndEnterEditMode()
{
	if (PlacedPoints.Num() < 2)
	{
		return;
	}

	SetInteractionMode(EWorldBLDViewportSplineMode::Edit);
}

TArray<FWorldBLDViewportSplineItem> ULinePlacementController::BuildSplineItems() const
{
	TArray<FWorldBLDViewportSplineItem> Items;
	if (PlacedPoints.Num() == 0)
	{
		return Items;
	}

	FWorldBLDViewportSplineItem MainLine;
	MainLine.ItemId = 0;
	MainLine.OwnerObject = const_cast<ULinePlacementController*>(this);
	MainLine.HitProxyLabel = TEXT("LinePlacementSpline");
	MainLine.Width = 100.0f;
	MainLine.Points = PlacedPoints;
	MainLine.bSelected = (InteractionMode == EWorldBLDViewportSplineMode::Edit);
	MainLine.bActive = (InteractionMode == EWorldBLDViewportSplineMode::Draw);
	Items.Add(MoveTemp(MainLine));
	return Items;
}

void ULinePlacementController::SetInteractionMode(const EWorldBLDViewportSplineMode NewMode)
{
	if (InteractionMode == NewMode)
	{
		return;
	}

	InteractionMode = NewMode;

	if (InteractionMode == EWorldBLDViewportSplineMode::Edit)
	{
		UpdateSplineFromPoints();
		TransientSplineEditor.SelectInEditor(this);
	}
}

// ================================================================================================
// Asset placement
// ================================================================================================

void ULinePlacementController::RefreshPlacedAssets()
{
	ClearPlacedAssets();
	PlaceAssetsAlongSpline();
}

bool ULinePlacementController::HasPlacedAssetsForCommit() const
{
	for (const TWeakObjectPtr<AActor>& WeakActor : PlacedStaticActors)
	{
		if (IsValid(WeakActor.Get()))
		{
			return true;
		}
	}

	if (AActor* ISMActor = InstancedMeshActor.Get())
	{
		TArray<UInstancedStaticMeshComponent*> ISMCs;
		ISMActor->GetComponents<UInstancedStaticMeshComponent>(ISMCs);
		for (const UInstancedStaticMeshComponent* ISMC : ISMCs)
		{
			if (IsValid(ISMC) && ISMC->GetInstanceCount() > 0)
			{
				return true;
			}
		}
	}

	return false;
}

void ULinePlacementController::ClearPlacedAssets()
{
	if (bInstanceMeshes)
	{
		if (AActor* ISMA = InstancedMeshActor.Get())
		{
			// Remove all ISMC instances on all components
			TArray<UInstancedStaticMeshComponent*> ISMCs;
			ISMA->GetComponents<UInstancedStaticMeshComponent>(ISMCs);
			for (UInstancedStaticMeshComponent* ISMC : ISMCs)
			{
				ISMC->ClearInstances();
			}
		}
	}
	else
	{
		for (TWeakObjectPtr<AActor>& WeakActor : PlacedStaticActors)
		{
			if (AActor* A = WeakActor.Get())
			{
				A->Destroy();
			}
		}
		PlacedStaticActors.Empty();
	}
}

void ULinePlacementController::ForgetTrackedPlacedAssets()
{
	InstancedMeshActor.Reset();
	PlacedStaticActors.Empty();
}

void ULinePlacementController::ConvertPlacedAssetsToStaticActors()
{
	UWorld* World = GetWorld();
	if (!IsValid(World))
	{
		return;
	}

	PlacedStaticActors.RemoveAll([](const TWeakObjectPtr<AActor>& WeakActor)
	{
		return !IsValid(WeakActor.Get());
	});

	if (AActor* ISMActor = InstancedMeshActor.Get())
	{
		ISMActor->Modify();
		TArray<UInstancedStaticMeshComponent*> ISMCs;
		ISMActor->GetComponents<UInstancedStaticMeshComponent>(ISMCs);
		for (UInstancedStaticMeshComponent* ISMC : ISMCs)
		{
			if (!IsValid(ISMC))
			{
				continue;
			}

			ISMC->Modify();
			UStaticMesh* Mesh = ISMC->GetStaticMesh();
			if (!IsValid(Mesh))
			{
				continue;
			}

			const int32 InstanceCount = ISMC->GetInstanceCount();
			for (int32 InstanceIdx = 0; InstanceIdx < InstanceCount; ++InstanceIdx)
			{
				FTransform WorldTransform;
				if (!ISMC->GetInstanceTransform(InstanceIdx, WorldTransform, true))
				{
					continue;
				}

				FActorSpawnParameters SMAParams;
				SMAParams.ObjectFlags |= RF_Transactional;
				AStaticMeshActor* SMA = World->SpawnActor<AStaticMeshActor>(
					AStaticMeshActor::StaticClass(), WorldTransform, SMAParams);
				if (!IsValid(SMA))
				{
					continue;
				}

				SMA->Modify();
				UStaticMeshComponent* MeshComponent = SMA->GetStaticMeshComponent();
				if (IsValid(MeshComponent))
				{
					MeshComponent->Modify();
					MeshComponent->SetStaticMesh(Mesh);
				}
				PlacedStaticActors.Add(SMA);
			}
		}

		ISMActor->Destroy();
		InstancedMeshActor.Reset();
	}

	bInstanceMeshes = false;
}

void ULinePlacementController::ConvertPlacedAssetsToInstancedActor()
{
	UWorld* World = GetWorld();
	if (!IsValid(World))
	{
		return;
	}

	TMap<UStaticMesh*, TArray<FTransform>> MeshToWorldTransforms;

	if (AActor* ExistingISMActor = InstancedMeshActor.Get())
	{
		TArray<UInstancedStaticMeshComponent*> ExistingISMCs;
		ExistingISMActor->GetComponents<UInstancedStaticMeshComponent>(ExistingISMCs);
		for (UInstancedStaticMeshComponent* ISMC : ExistingISMCs)
		{
			if (!IsValid(ISMC))
			{
				continue;
			}

			UStaticMesh* Mesh = ISMC->GetStaticMesh();
			if (!IsValid(Mesh))
			{
				continue;
			}

			TArray<FTransform>& Transforms = MeshToWorldTransforms.FindOrAdd(Mesh);
			const int32 InstanceCount = ISMC->GetInstanceCount();
			for (int32 InstanceIdx = 0; InstanceIdx < InstanceCount; ++InstanceIdx)
			{
				FTransform WorldTransform;
				if (ISMC->GetInstanceTransform(InstanceIdx, WorldTransform, true))
				{
					Transforms.Add(WorldTransform);
				}
			}
		}
	}

	for (int32 ActorIdx = PlacedStaticActors.Num() - 1; ActorIdx >= 0; --ActorIdx)
	{
		AStaticMeshActor* SMA = Cast<AStaticMeshActor>(PlacedStaticActors[ActorIdx].Get());
		if (!IsValid(SMA))
		{
			PlacedStaticActors.RemoveAtSwap(ActorIdx);
			continue;
		}

		UStaticMeshComponent* MeshComponent = SMA->GetStaticMeshComponent();
		UStaticMesh* Mesh = IsValid(MeshComponent) ? MeshComponent->GetStaticMesh() : nullptr;
		if (IsValid(Mesh))
		{
			MeshToWorldTransforms.FindOrAdd(Mesh).Add(SMA->GetActorTransform());
		}
	}

	AActor* ISMActor = InstancedMeshActor.Get();
	if (!IsValid(ISMActor))
	{
		FActorSpawnParameters Params;
		Params.ObjectFlags |= RF_Transactional;
		Params.Name = MakeUniqueObjectName(World, AActor::StaticClass(), TEXT("LinePlacement_Instanced"));
		ISMActor = World->SpawnActor<AActor>(Params);
		if (IsValid(ISMActor))
		{
			ISMActor->Modify();
			USceneComponent* Root = NewObject<USceneComponent>(ISMActor, TEXT("Root"), RF_Transactional);
			ISMActor->SetRootComponent(Root);
			Root->RegisterComponent();
			InstancedMeshActor = ISMActor;
		}
	}

	if (!IsValid(ISMActor))
	{
		return;
	}

	ISMActor->Modify();
	TArray<UInstancedStaticMeshComponent*> OldISMCs;
	ISMActor->GetComponents<UInstancedStaticMeshComponent>(OldISMCs);
	for (UInstancedStaticMeshComponent* OldISMC : OldISMCs)
	{
		if (IsValid(OldISMC))
		{
			OldISMC->Modify();
			OldISMC->DestroyComponent();
		}
	}

	const FVector PlacementCenter = ComputePlacementCenter(MeshToWorldTransforms);
	ISMActor->SetActorTransform(FTransform(PlacementCenter));
	const FTransform ISMActorTransform = ISMActor->GetActorTransform();

	for (const TPair<UStaticMesh*, TArray<FTransform>>& Pair : MeshToWorldTransforms)
	{
		UStaticMesh* Mesh = Pair.Key;
		if (!IsValid(Mesh))
		{
			continue;
		}

		UInstancedStaticMeshComponent* NewISMC = NewObject<UInstancedStaticMeshComponent>(
			ISMActor, NAME_None, RF_Transactional);
		if (!IsValid(NewISMC))
		{
			continue;
		}

		NewISMC->Modify();
		NewISMC->SetStaticMesh(Mesh);
		NewISMC->SetupAttachment(ISMActor->GetRootComponent());
		NewISMC->RegisterComponent();

		for (const FTransform& WorldTransform : Pair.Value)
		{
			const FTransform LocalTransform = WorldTransform.GetRelativeTransform(ISMActorTransform);
			NewISMC->AddInstance(LocalTransform, false);
		}
	}

	for (TWeakObjectPtr<AActor>& WeakActor : PlacedStaticActors)
	{
		if (AActor* Actor = WeakActor.Get())
		{
			Actor->Modify();
			Actor->Destroy();
		}
	}
	PlacedStaticActors.Empty();
	bInstanceMeshes = true;
}

void ULinePlacementController::PlaceAssetsAlongSpline()
{
	if (PlacedPoints.Num() < 2)
	{
		return;
	}

	USplineComponent* SC = TransientSplineEditor.GetSplineComponent();
	if (!IsValid(SC))
	{
		return;
	}

	const UWorldBLDAssetPalette* Palette = GetPaletteInstance();
	if (!IsValid(Palette) || Palette->Assets.IsEmpty())
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!IsValid(World))
	{
		return;
	}

	const float SplineLength = SC->GetSplineLength();
	if (SplineLength < 1.0f)
	{
		return;
	}

	const float Spacing = FMath::Max(1.0f, Palette->DefaultSpacing);

	struct FPendingPlacement
	{
		UStaticMesh* Mesh = nullptr;
		FTransform WorldTransform;
	};
	TArray<FPendingPlacement> PendingPlacements;
	PendingPlacements.Reserve(FMath::CeilToInt(SplineLength / Spacing) + 1);

	// Walk along spline
	for (float Distance = 0.0f; Distance <= SplineLength; Distance += Spacing)
	{
		FPlacedAsset Asset;
		if (!Palette->SampleWeighted(RandomStream, Asset))
		{
			continue;
		}

		UStaticMesh* Mesh = Asset.Mesh.LoadSynchronous();
		if (!IsValid(Mesh))
		{
			continue;
		}

		const FVector SplinePos   = SC->GetLocationAtDistanceAlongSpline(Distance, ESplineCoordinateSpace::World);
		const FVector RightVec    = SC->GetRightVectorAtDistanceAlongSpline(Distance, ESplineCoordinateSpace::World);
		const float   SideOffset  = OffsetVariation > 0.0f ? RandomStream.FRandRange(-OffsetVariation, OffsetVariation) : 0.0f;
		const float   Scale       = RandomStream.FRandRange(Asset.MinScale, Asset.MaxScale);
		const float   YawDegrees  = Asset.ZRotationRange > 0.0f ? RandomStream.FRandRange(0.0f, Asset.ZRotationRange) : 0.0f;
		const FVector PlacePos    = SplinePos + RightVec * SideOffset + FVector(0.0f, 0.0f, Asset.ZOffset);
		const FRotator PlaceRot   = FRotator(0.0f, YawDegrees, 0.0f);
		const FVector  PlaceScale = FVector(Scale);
		const FTransform PlaceXform(PlaceRot, PlacePos, PlaceScale);

		FPendingPlacement& NewPlacement = PendingPlacements.AddDefaulted_GetRef();
		NewPlacement.Mesh = Mesh;
		NewPlacement.WorldTransform = PlaceXform;
	}

	if (bInstanceMeshes)
	{
		if (PendingPlacements.IsEmpty())
		{
			return;
		}

		AActor* ISMActor = nullptr;
		if (!InstancedMeshActor.IsValid())
		{
			FActorSpawnParameters Params;
			Params.ObjectFlags |= RF_Transactional;
			Params.Name = MakeUniqueObjectName(World, AActor::StaticClass(), TEXT("LinePlacement_Instanced"));
			ISMActor = World->SpawnActor<AActor>(Params);
			if (IsValid(ISMActor))
			{
				USceneComponent* Root = NewObject<USceneComponent>(ISMActor, TEXT("Root"));
				ISMActor->SetRootComponent(Root);
				Root->RegisterComponent();
				InstancedMeshActor = ISMActor;
			}
		}
		else
		{
			ISMActor = InstancedMeshActor.Get();
		}

		if (!IsValid(ISMActor))
		{
			return;
		}

		TArray<FTransform> WorldTransforms;
		WorldTransforms.Reserve(PendingPlacements.Num());
		for (const FPendingPlacement& Placement : PendingPlacements)
		{
			WorldTransforms.Add(Placement.WorldTransform);
		}

		const FVector PlacementCenter = ComputePlacementCenter(WorldTransforms);
		ISMActor->SetActorTransform(FTransform(PlacementCenter));
		const FTransform ISMActorTransform = ISMActor->GetActorTransform();

		for (const FPendingPlacement& Placement : PendingPlacements)
		{
			if (!IsValid(Placement.Mesh))
			{
				continue;
			}

			UInstancedStaticMeshComponent* ISMC = nullptr;
			TArray<UInstancedStaticMeshComponent*> ISMCs;
			ISMActor->GetComponents<UInstancedStaticMeshComponent>(ISMCs);
			for (UInstancedStaticMeshComponent* C : ISMCs)
			{
				if (IsValid(C) && C->GetStaticMesh() == Placement.Mesh)
				{
					ISMC = C;
					break;
				}
			}

			if (!IsValid(ISMC))
			{
				ISMC = NewObject<UInstancedStaticMeshComponent>(ISMActor, NAME_None, RF_Transactional);
				ISMC->SetStaticMesh(Placement.Mesh);
				ISMC->SetupAttachment(ISMActor->GetRootComponent());
				ISMC->RegisterComponent();
			}

			const FTransform LocalTransform = Placement.WorldTransform.GetRelativeTransform(ISMActorTransform);
			ISMC->AddInstance(LocalTransform, false);
		}
	}
	else
	{
		for (const FPendingPlacement& Placement : PendingPlacements)
		{
			if (!IsValid(Placement.Mesh))
			{
				continue;
			}

			FActorSpawnParameters SMAParams;
			SMAParams.ObjectFlags |= RF_Transactional;

			AStaticMeshActor* SMA = World->SpawnActor<AStaticMeshActor>(
				AStaticMeshActor::StaticClass(), Placement.WorldTransform, SMAParams);
			if (IsValid(SMA))
			{
				SMA->GetStaticMeshComponent()->SetStaticMesh(Placement.Mesh);
				PlacedStaticActors.Add(SMA);
			}
		}
	}
}

const UWorldBLDAssetPalette* ULinePlacementController::GetPaletteInstance() const
{
	if (IsValid(PaletteAsset))
	{
		return PaletteAsset;
	}

	if (!PaletteClass)
	{
		return nullptr;
	}
	return PaletteClass.GetDefaultObject();
}

// ================================================================================================
// Game view
// ================================================================================================

void ULinePlacementController::DisableGameViewInActiveViewports()
{
	if (!GEditor)
	{
		return;
	}

	for (FLevelEditorViewportClient* ViewportClient : GEditor->GetLevelViewportClients())
	{
		if (!ViewportClient || !ViewportClient->IsInGameView())
		{
			continue;
		}

		ViewportClient->SetGameView(false);
		if (ViewportClient->Viewport)
		{
			ViewportClient->Viewport->InvalidateDisplay();
		}
	}
}

// ================================================================================================
// Context menu overlay
// ================================================================================================

void ULinePlacementController::ShowContextMenu()
{
	if (ContextMenuOverlayWidget.IsValid())
	{
		return;
	}

	FLevelEditorModule& LevelEditor = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
	const TSharedPtr<ILevelEditor> LevelEditorInstance = LevelEditor.GetLevelEditorInstance().Pin();
	if (!LevelEditorInstance.IsValid())
	{
		return;
	}

	const TSharedPtr<SLevelViewport> ActiveViewport = LevelEditorInstance->GetActiveViewportInterface();
	if (!ActiveViewport.IsValid())
	{
		return;
	}

	const TWeakObjectPtr<ULinePlacementController> WeakThis(this);

	const TSharedRef<SWidget> MenuContent =
		SNew(SLinePlacementContextMenu)
		.Controller(WeakThis);

	const TSharedRef<SWidget> Panel =
		SNew(SMinimizableWorldBLDMenuPanel)
		.Title(NSLOCTEXT("LinePlacementController", "MenuTitle", "Line Placement"))
		.Content(MenuContent);

	const TSharedRef<SWorldBLDContextMenuViewportOverlay> Overlay =
		SNew(SWorldBLDContextMenuViewportOverlay)
		.Panel(Panel);

	ContextMenuOverlayWidget     = Overlay;
	ContextMenuHostViewport      = ActiveViewport;

	ActiveViewport->AddOverlayWidget(Overlay);
}

void ULinePlacementController::HideContextMenu()
{
	TSharedPtr<SWidget> OverlayToRemove = ContextMenuOverlayWidget;
	TWeakPtr<SLevelViewport> HostViewport = ContextMenuHostViewport;

	ContextMenuOverlayWidget.Reset();
	ContextMenuHostViewport.Reset();

	if (!OverlayToRemove.IsValid())
	{
		return;
	}

	if (TSharedPtr<SLevelViewport> PinnedViewport = HostViewport.Pin())
	{
		PinnedViewport->RemoveOverlayWidget(OverlayToRemove.ToSharedRef());
		return;
	}

	// Fallback: remove from currently active viewport
	FLevelEditorModule& LevelEditor = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
	if (const TSharedPtr<ILevelEditor> LEInstance = LevelEditor.GetLevelEditorInstance().Pin())
	{
		if (const TSharedPtr<SLevelViewport> ActiveViewport = LEInstance->GetActiveViewportInterface())
		{
			ActiveViewport->RemoveOverlayWidget(OverlayToRemove.ToSharedRef());
		}
	}
}
