// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "BLDToolsetTypes.h"

/** Level viewport captures shared by BLD toolsets. Captures require the editor UI. */
namespace BLDCapture
{
	struct BLDTOOLSETCOMMON_API FRequest
	{
		/** World bounds to frame for Oblique and TopDown views. */
		FBox Bounds = FBox(ForceInit);

		EBLDCaptureView View = EBLDCaptureView::Oblique;

		/** Camera pose for EBLDCaptureView::Pose. */
		FVector PoseLocation = FVector::ZeroVector;
		FRotator PoseRotation = FRotator::ZeroRotator;

		int32 Width = 768;
		int32 Height = 432;

		/** Framing margin multiplier (1 = tight). */
		double Padding = 1.15;

		bool bRestoreCamera = false;

		TArray<FString> Warnings;

		/** Prefix for error messages, such as TwinBLDToolset. */
		FString ToolsetName = TEXT("BLDToolset");
	};

	/** Frames the request in the first perspective level viewport, waits a few frames, and completes Result with a PNG. */
	BLDTOOLSETCOMMON_API void Capture(UBLDCaptureAsyncResult* Result, FRequest Request);

	/** Scales Pixels down to fit MaxWidth x MaxHeight (never up) and encodes them as a PNG. */
	BLDTOOLSETCOMMON_API bool EncodeImage(const TArray<FColor>& Pixels, FIntPoint Size, int32 MaxWidth, int32 MaxHeight, FToolsetImage& OutImage);
}
