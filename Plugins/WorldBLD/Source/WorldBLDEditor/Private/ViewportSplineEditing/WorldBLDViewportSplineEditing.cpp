#include "ViewportSplineEditing/WorldBLDViewportSplineEditing.h"

#include "WorldBLDEditController.h"
#include "WorldBLDKitElementUtils.h"

#include "CollisionQueryParams.h"
#include "Components/SplineComponent.h"
#include "Editor.h"
#include "GameFramework/Actor.h"

namespace
{
	constexpr int32 kPointHitProxyBase = 100000;
}

void FWorldBLDViewportSplineRenderer::DrawHoverCircle(
	FPrimitiveDrawWrapper Renderer,
	const FWorldBLDViewportSplineDrawState& DrawState,
	const FWorldBLDViewportSplineStyle& Style)
{
	if (!DrawState.bHoverValid)
	{
		return;
	}

	UPrimitiveDrawWrapperUtils::PDI_DrawCircle(
		Renderer,
		DrawState.HoverPoint,
		Style.HoverCircleRadius,
		Style.HoverColor,
		Style.HoverCircleThickness,
		Style.HoverCircleSegments);
}

void FWorldBLDViewportSplineRenderer::DrawSplineItems(
	FPrimitiveDrawWrapper Renderer,
	const TArray<FWorldBLDViewportSplineItem>& Items,
	const FWorldBLDViewportSplineDrawState& DrawState,
	const FWorldBLDViewportSplineStyle& Style,
	const bool bSetHitProxy)
{
	for (const FWorldBLDViewportSplineItem& Item : Items)
	{
		const bool bIsSelected = Item.bSelected || DrawState.SelectedItemId == Item.ItemId;
		const bool bIsActive = Item.bActive || DrawState.ActiveItemId == Item.ItemId;
		const FLinearColor Color = bIsSelected ? Style.SelectedColor : (bIsActive ? Style.ActiveDrawColor : Style.InactiveColor);
		DrawItemPolyline(Renderer, Item, Color, Style, bSetHitProxy);
	}
}

void FWorldBLDViewportSplineRenderer::DrawPendingPreview(
	FPrimitiveDrawWrapper Renderer,
	const FWorldBLDViewportSplineItem* ActiveItem,
	const FWorldBLDViewportSplineDrawState& DrawState,
	const FWorldBLDViewportSplineStyle& Style)
{
	if (!DrawState.bHoverValid || DrawState.Mode != EWorldBLDViewportSplineMode::Draw)
	{
		return;
	}

	const float Radius = FMath::Max(1.0f, Style.HoverCircleRadius);
	UPrimitiveDrawWrapperUtils::PDI_DrawCircle(
		Renderer,
		DrawState.HoverPoint,
		Radius,
		Style.ActiveDrawColor,
		Style.HoverCircleThickness,
		Style.HoverCircleSegments);

	if (ActiveItem == nullptr || ActiveItem->Points.Num() == 0)
	{
		return;
	}

	const FVector PreviewStart = ActiveItem->Points.Last() + FVector(0.0f, 0.0f, Style.ZOffset);
	const FVector PreviewEnd = DrawState.HoverPoint + FVector(0.0f, 0.0f, Style.ZOffset);
	const FPrimitiveDrawParams DrawParams(Style.ActiveDrawColor, Style.LineThickness);
	UPrimitiveDrawWrapperUtils::PDI_DrawLine(Renderer, DrawParams, PreviewStart, PreviewEnd);
}

int32 FWorldBLDViewportSplineRenderer::EncodePointHitProxyId(const int32 ItemId, const int32 PointIndex)
{
	return (ItemId * kPointHitProxyBase) + PointIndex;
}

void FWorldBLDViewportSplineRenderer::DrawItemPolyline(
	FPrimitiveDrawWrapper Renderer,
	const FWorldBLDViewportSplineItem& Item,
	const FLinearColor& Color,
	const FWorldBLDViewportSplineStyle& Style,
	const bool bSetHitProxy)
{
	if (Item.Points.Num() == 0)
	{
		return;
	}

	const FVector Lift(0.0f, 0.0f, Style.ZOffset);
	const FPrimitiveDrawParams LineParams(Color, Style.LineThickness);
	const FPrimitiveDrawParams PointParams(Color, Style.PointSize);

	if (bSetHitProxy)
	{
		FElementHitProxyContext ItemCtx;
		ItemCtx.Id = Item.ItemId;
		ItemCtx.Object = Item.OwnerObject;
		ItemCtx.String = Item.HitProxyLabel;
		UPrimitiveDrawWrapperUtils::PDI_SetHitProxy(Renderer, ItemCtx);
	}

	for (int32 PointIdx = 0; PointIdx + 1 < Item.Points.Num(); ++PointIdx)
	{
		UPrimitiveDrawWrapperUtils::PDI_DrawLine(
			Renderer,
			LineParams,
			Item.Points[PointIdx] + Lift,
			Item.Points[PointIdx + 1] + Lift);
	}

	if (bSetHitProxy)
	{
		UPrimitiveDrawWrapperUtils::PDI_ClearHitProxy(Renderer);
	}

	for (int32 PointIdx = 0; PointIdx < Item.Points.Num(); ++PointIdx)
	{
		if (bSetHitProxy)
		{
			FElementHitProxyContext PointCtx;
			PointCtx.Id = EncodePointHitProxyId(Item.ItemId, PointIdx);
			PointCtx.Object = Item.OwnerObject;
			PointCtx.String = Item.HitProxyLabel;
			UPrimitiveDrawWrapperUtils::PDI_SetHitProxy(Renderer, PointCtx);
		}

		UPrimitiveDrawWrapperUtils::PDI_DrawPoint(Renderer, PointParams, Item.Points[PointIdx] + Lift);

		if (bSetHitProxy)
		{
			UPrimitiveDrawWrapperUtils::PDI_ClearHitProxy(Renderer);
		}
	}
}

void FWorldBLDTransientSplineEditor::EnsureSpawned(UWorldBLDEditController* Controller, const TCHAR* BaseName)
{
	if (!IsValid(Controller))
	{
		return;
	}

	if (SplineActor.IsValid() && SplineComponent.IsValid())
	{
		return;
	}

	UWorld* World = Controller->GetWorld();
	if (!IsValid(World))
	{
		return;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.ObjectFlags |= RF_Transient;
	SpawnParams.Name = MakeUniqueObjectName(World, AActor::StaticClass(), BaseName);

	AActor* NewActor = World->SpawnActor<AActor>(SpawnParams);
	if (!IsValid(NewActor))
	{
		return;
	}

	USplineComponent* NewSpline = NewObject<USplineComponent>(NewActor, TEXT("Spline"));
	NewSpline->CreationMethod = EComponentCreationMethod::Instance;
	NewActor->SetRootComponent(NewSpline);
	NewActor->AddInstanceComponent(NewSpline);
	NewSpline->SetMobility(EComponentMobility::Movable);
	NewSpline->ClearSplinePoints(false);
	NewSpline->RegisterComponent();

	SplineActor = NewActor;
	SplineComponent = NewSpline;
	bWasDraggingGizmo = false;

	Controller->ActiveBrushActor = NewActor;
	Controller->bActiveBrushIsForceSelected = true;
}

void FWorldBLDTransientSplineEditor::Destroy(UWorldBLDEditController* Controller)
{
	if (AActor* ExistingActor = SplineActor.Get())
	{
		ExistingActor->Destroy();
	}

	SplineActor.Reset();
	SplineComponent.Reset();
	bWasDraggingGizmo = false;

	if (IsValid(Controller))
	{
		Controller->ActiveBrushActor = nullptr;
	}
}

bool FWorldBLDTransientSplineEditor::HasValidSpline() const
{
	return SplineActor.IsValid() && SplineComponent.IsValid();
}

USplineComponent* FWorldBLDTransientSplineEditor::GetSplineComponent() const
{
	return SplineComponent.Get();
}

AActor* FWorldBLDTransientSplineEditor::GetSplineActor() const
{
	return SplineActor.Get();
}

void FWorldBLDTransientSplineEditor::SyncFromPoints(const TArray<FVector>& Points, const bool bLinearSpline)
{
	USplineComponent* SC = SplineComponent.Get();
	if (!IsValid(SC))
	{
		return;
	}

	SC->ClearSplinePoints(false);
	for (const FVector& Point : Points)
	{
		SC->AddSplinePoint(Point, ESplineCoordinateSpace::World, false);
	}

	const ESplinePointType::Type PointType = bLinearSpline ? ESplinePointType::Linear : ESplinePointType::Curve;
	for (int32 PointIdx = 0; PointIdx < SC->GetNumberOfSplinePoints(); ++PointIdx)
	{
		SC->SetSplinePointType(PointIdx, PointType, false);
	}

	SC->UpdateSpline();
}

void FWorldBLDTransientSplineEditor::SyncToPoints(TArray<FVector>& OutPoints) const
{
	OutPoints.Reset();

	const USplineComponent* SC = SplineComponent.Get();
	if (!IsValid(SC))
	{
		return;
	}

	const int32 NumPoints = SC->GetNumberOfSplinePoints();
	OutPoints.Reserve(NumPoints);
	for (int32 PointIdx = 0; PointIdx < NumPoints; ++PointIdx)
	{
		OutPoints.Add(SC->GetLocationAtSplinePoint(PointIdx, ESplineCoordinateSpace::World));
	}
}

void FWorldBLDTransientSplineEditor::SelectInEditor(UWorldBLDEditController* Controller) const
{
	if (!IsValid(Controller))
	{
		return;
	}

	Controller->ForceEditorSelectionToActiveBrushActor();

	if (GEditor)
	{
		if (AActor* ExistingActor = SplineActor.Get())
		{
			GEditor->SelectNone(/* bNoteSelectionChange */ true, /* bDeselectBSPSurfs */ true);
			GEditor->SelectActor(ExistingActor, /* bInSelected */ true, /* bNotify */ true, /* bSelectEvenIfHidden */ true);
		}
	}
}

void FWorldBLDTransientSplineEditor::AddIgnoredActors(FCollisionQueryParams& TraceParams) const
{
	if (AActor* ExistingActor = SplineActor.Get())
	{
		TraceParams.AddIgnoredActor(ExistingActor);
	}
}

void FWorldBLDTransientSplineEditor::TickDragRelease(TFunctionRef<void()> OnDragReleased)
{
	const bool bIsDragging = UWorldBLDKitElementUtils::UserIsDraggingGizmoInViewport();
	if (bWasDraggingGizmo && !bIsDragging)
	{
		OnDragReleased();
	}
	bWasDraggingGizmo = bIsDragging;
}

