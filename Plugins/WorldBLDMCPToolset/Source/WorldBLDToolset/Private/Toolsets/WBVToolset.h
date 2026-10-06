// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "BLDToolsetTypes.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "WBVToolset.generated.h"

/**
 * Cross-product validation loop for WorldBLD agent workflows.
 * Aggregates City / Road / Twin issue finders into a shared FBLDIssueReport,
 * checks post-op readiness (rebuild in flight), and optionally frames evidence.
 *
 * Typical flow after a mutating tool batch:
 * 1. CheckPostOpReadiness (wait / rebuild if not ready)
 * 2. RunValidationLoop
 * 3. CaptureValidationEvidence on the top spatial issue if needed
 * 4. Fix via product toolsets, then repeat
 */
UCLASS(BlueprintType, MinimalAPI)
class UWorldBLDValidationToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Reports whether it is safe to capture or continue editing after a mutating batch.
	 * Today this checks RoadBLD rebuild job state through the registry when RoadBLDToolset is loaded.
	 */
	UFUNCTION(meta = (AICallable), Category = "WorldBLDToolset")
	static FBLDPostOpReadiness CheckPostOpReadiness();

	/**
	 * Runs one validation pass across enabled WorldBLD product toolsets and returns a shared Issues array.
	 * Skips sources whose plugins or toolsets are not registered. Does not mutate the level.
	 * @param bIncludeCity Call CityBLD ValidateCity / FindCityIssues when available.
	 * @param bIncludeRoad Call RoadBLD junction + geometry finders when available.
	 * @param bIncludeTwin Call TwinBLD ValidateTwinScene when available.
	 * @param MaxIssuesPerSource Cap per source (1-200).
	 */
	UFUNCTION(meta = (AICallable), Category = "WorldBLDToolset")
	static FBLDValidationLoopResult RunValidationLoop(
		bool bIncludeCity = true,
		bool bIncludeRoad = true,
		bool bIncludeTwin = true,
		int32 MaxIssuesPerSource = 50);

	/**
	 * Captures a viewport framed on a world location as visual evidence for a validation issue.
	 * Prefer Location/Radius from an FBLDIssue. Requires the editor UI (async).
	 */
	UFUNCTION(meta = (AICallable), Category = "WorldBLDToolset")
	static UBLDCaptureAsyncResult* CaptureValidationEvidence(
		FVector Location,
		double Radius = 5000.0,
		EBLDCaptureView View = EBLDCaptureView::Oblique,
		int32 Width = 768,
		int32 Height = 432);
};