#pragma once

#include "CoreMinimal.h"
#include "PrimitiveDrawWrapper.h"

class AActor;
class UWorldBLDEditController;
class USplineComponent;
struct FCollisionQueryParams;

enum class EWorldBLDViewportSplineMode : uint8
{
	Draw,
	Edit
};

struct FWorldBLDViewportSplineItem
{
	int32 ItemId = INDEX_NONE;
	TArray<FVector> Points;
	float Width = 50.0f;
	bool bSelected = false;
	bool bActive = false;
	UObject* OwnerObject = nullptr;
	FString HitProxyLabel;
};

struct FWorldBLDViewportSplineStyle
{
	FLinearColor InactiveColor = FLinearColor(0.6f, 0.4f, 0.8f, 1.0f);
	FLinearColor ActiveDrawColor = FLinearColor::Green;
	FLinearColor SelectedColor = FLinearColor::Yellow;
	FLinearColor HoverColor = FLinearColor(1.0f, 1.0f, 0.6f, 1.0f);
	float LineThickness = 4.0f;
	float PointSize = 12.0f;
	float HoverCircleRadius = 50.0f;
	float HoverCircleThickness = 4.0f;
	int32 HoverCircleSegments = 24;
	float ZOffset = 3.0f;
};

struct FWorldBLDViewportSplineDrawState
{
	EWorldBLDViewportSplineMode Mode = EWorldBLDViewportSplineMode::Draw;
	bool bHoverValid = false;
	FVector HoverPoint = FVector::ZeroVector;
	bool bHasPendingPoint = false;
	FVector PendingPoint = FVector::ZeroVector;
	int32 ActiveItemId = INDEX_NONE;
	int32 SelectedItemId = INDEX_NONE;
};

class WORLDBLDEDITOR_API FWorldBLDViewportSplineRenderer
{
public:
	static void DrawHoverCircle(
		FPrimitiveDrawWrapper Renderer,
		const FWorldBLDViewportSplineDrawState& DrawState,
		const FWorldBLDViewportSplineStyle& Style);

	static void DrawSplineItems(
		FPrimitiveDrawWrapper Renderer,
		const TArray<FWorldBLDViewportSplineItem>& Items,
		const FWorldBLDViewportSplineDrawState& DrawState,
		const FWorldBLDViewportSplineStyle& Style,
		bool bSetHitProxy);

	static void DrawPendingPreview(
		FPrimitiveDrawWrapper Renderer,
		const FWorldBLDViewportSplineItem* ActiveItem,
		const FWorldBLDViewportSplineDrawState& DrawState,
		const FWorldBLDViewportSplineStyle& Style);

	static int32 EncodePointHitProxyId(int32 ItemId, int32 PointIndex);

private:
	static void DrawItemPolyline(
		FPrimitiveDrawWrapper Renderer,
		const FWorldBLDViewportSplineItem& Item,
		const FLinearColor& Color,
		const FWorldBLDViewportSplineStyle& Style,
		bool bSetHitProxy);
};

class WORLDBLDEDITOR_API FWorldBLDTransientSplineEditor
{
public:
	void EnsureSpawned(UWorldBLDEditController* Controller, const TCHAR* BaseName = TEXT("WorldBLD_SplineEdit"));
	void Destroy(UWorldBLDEditController* Controller);

	bool HasValidSpline() const;
	USplineComponent* GetSplineComponent() const;
	AActor* GetSplineActor() const;

	void SyncFromPoints(const TArray<FVector>& Points, bool bLinearSpline);
	void SyncToPoints(TArray<FVector>& OutPoints) const;

	void SelectInEditor(UWorldBLDEditController* Controller) const;
	void AddIgnoredActors(FCollisionQueryParams& TraceParams) const;

	void TickDragRelease(TFunctionRef<void()> OnDragReleased);

private:
	TWeakObjectPtr<AActor> SplineActor;
	TWeakObjectPtr<USplineComponent> SplineComponent;
	bool bWasDraggingGizmo = false;
};

