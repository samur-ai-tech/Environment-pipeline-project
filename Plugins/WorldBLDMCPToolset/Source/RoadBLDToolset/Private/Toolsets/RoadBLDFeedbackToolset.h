// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/RoadBLDToolsetTypes.h"
#include "ToolsetRegistry/ToolCallAsyncResult.h"
#include "ToolsetRegistry/ToolsetDefinition.h"
#include "ToolsetRegistry/ToolsetImage.h"

#include "RoadBLDFeedbackToolset.generated.h"

class ADynamicRoad;
class ADynamicRoadNetwork;

USTRUCT(BlueprintType)
struct FRoadBLDCaptureResult
{
	GENERATED_BODY()

	/** PNG image, base64 encoded. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FToolsetImage Image;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector CameraLocation = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRotator CameraRotation = FRotator::ZeroRotator;

	/** World bounds that were framed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector BoundsMin = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector BoundsMax = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> Warnings;
};

/** Async tool result that completes with a viewport capture. */
UCLASS()
class URoadBLDCaptureAsyncResult : public UToolCallAsyncResult
{
	GENERATED_BODY()

public:
	bool SetValue(const FRoadBLDCaptureResult& InValue)
	{
		FRoadBLDCaptureResult ValueCopy = InValue;
		return MaybeBroadcastSuccessfulCompletion(MoveTemp(ValueCopy), Value);
	}

	UPROPERTY()
	FRoadBLDCaptureResult Value;
};

/**
 * Look at road networks. Captures frame a road, junction, network or area in the active level viewport, wait for
 * pending rebuilds, and return a PNG image so you can check lane layouts, markings, materials and junction shapes.
 * Captures require the editor UI. Keep images small (the defaults are fine) to save context.
 * When investigating reported artifacts (gaps, missing or distorted meshes, floating pieces), run
 * RoadBLDBuildToolset.Rebuild with bForceRebuildAll=true first; captures of a stale build are misleading.
 */
UCLASS(BlueprintType, MinimalAPI)
class URoadBLDFeedbackToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Frames and captures a road, junction or network. With no target, frames every road network in the level.
	 * @param Road Optional road to frame.
	 * @param JunctionId Junction Id from ListJunctions. None frames no junction.
	 * @param Network Optional network to frame.
	 * @param View Oblique for a 3D overview, TopDown for layout checks, Current to keep the camera.
	 * @param Width Maximum image width in pixels.
	 * @param Height Maximum image height in pixels.
	 * @param Padding Framing margin multiplier (1 = tight).
	 * @param bWaitForRebuild Wait for queued or running rebuilds of the affected networks before capturing. Captures never start a rebuild; networks with unbuilt edits are captured as last built, with a warning.
	 * @param TimeoutMs Maximum rebuild wait in milliseconds (at most 30000).
	 * @param bRestoreCamera Put the editor camera back after capturing.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static URoadBLDCaptureAsyncResult* CaptureViewport(
		ADynamicRoad* Road = nullptr,
		const FString& JunctionId = TEXT("None"),
		ADynamicRoadNetwork* Network = nullptr,
		ERoadBLDCaptureView View = ERoadBLDCaptureView::Oblique,
		int32 Width = 768,
		int32 Height = 432,
		double Padding = 1.15,
		bool bWaitForRebuild = true,
		int32 TimeoutMs = 30000,
		bool bRestoreCamera = false);

	/**
	 * Frames and captures a circular area.
	 * @param Center Area center in world space.
	 * @param Radius Area radius in cm.
	 * @param View Oblique or TopDown.
	 * @param Width Maximum image width in pixels.
	 * @param Height Maximum image height in pixels.
	 * @param bWaitForRebuild Wait for queued or running rebuilds before capturing. Captures never start a rebuild.
	 * @param TimeoutMs Maximum rebuild wait in milliseconds (at most 30000).
	 * @param bRestoreCamera Put the editor camera back after capturing.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static URoadBLDCaptureAsyncResult* CaptureArea(
		FVector Center,
		double Radius = 5000.0,
		ERoadBLDCaptureView View = ERoadBLDCaptureView::TopDown,
		int32 Width = 768,
		int32 Height = 432,
		bool bWaitForRebuild = true,
		int32 TimeoutMs = 30000,
		bool bRestoreCamera = false);
};
