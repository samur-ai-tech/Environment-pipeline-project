// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/RoadBLDToolsetTypes.h"
#include "ToolsetRegistry/ToolCallAsyncResult.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "RoadBLDBuildToolset.generated.h"

class ADynamicRoad;
class ADynamicRoadNetwork;

/** Async tool result that completes with a rebuild status. */
UCLASS()
class URoadBLDRebuildAsyncResult : public UToolCallAsyncResult
{
	GENERATED_BODY()

public:
	bool SetValue(const FRoadBLDRebuildStatus& InValue)
	{
		FRoadBLDRebuildStatus ValueCopy = InValue;
		return MaybeBroadcastSuccessfulCompletion(MoveTemp(ValueCopy), Value);
	}

	UPROPERTY()
	FRoadBLDRebuildStatus Value;
};

/**
 * Build RoadBLD road networks. Rebuilding generates road meshes, junctions, markings, sidewalks, props and landscape
 * edits from authored roads. Rebuilds start on the next editor tick and finish in the background; with bWait=false
 * the call returns State=Running and a JobId immediately, so the job can be polled or cancelled.
 * When the user reports visual artifacts (gaps or seams, missing, stretched or distorted meshes, floating or misplaced
 * pieces, stale junctions or markings), first call Rebuild with bForceRebuildAll=true and bOnlyStale=false on the
 * affected network, then CaptureViewport to check. Change road shapes only if the artifact survives a forced rebuild.
 * Small scopes: call Rebuild with bWait=true. Large networks: a wait that exceeds TimeoutMs returns State=Running with
 * bTimedOut=true and a JobId; keep polling with WaitForRebuild or RebuildStatus instead of starting another rebuild.
 */
UCLASS(BlueprintType, MinimalAPI)
class URoadBLDBuildToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Rebuilds road networks.
	 * @param Network Optional network. When omitted, every network in the level (or every stale one) is rebuilt.
	 * @param bOnlyStale With no Network, only rebuild networks that have unbuilt edits.
	 * @param bForceRebuildAll Regenerate all geometry instead of reusing unchanged pieces. Slower; always use it first when the user reports gaps, missing or distorted meshes, or floating pieces.
	 * @param bWait Wait for completion (or TimeoutMs) before returning.
	 * @param TimeoutMs Maximum wait in milliseconds.
	 * @param bLowQualityMesh Build low-detail preview meshes (faster iteration).
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static URoadBLDRebuildAsyncResult* Rebuild(
		ADynamicRoadNetwork* Network = nullptr,
		bool bOnlyStale = false,
		bool bForceRebuildAll = false,
		bool bWait = true,
		int32 TimeoutMs = 30000,
		bool bLowQualityMesh = false);

	/**
	 * Incrementally rebuilds only the given roads and the junctions around them.
	 * @param Roads Modified roads.
	 * @param bWait Wait for completion (or TimeoutMs) before returning.
	 * @param TimeoutMs Maximum wait in milliseconds.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static URoadBLDRebuildAsyncResult* RebuildRoads(const TArray<ADynamicRoad*>& Roads, bool bWait = true, int32 TimeoutMs = 30000);

	/**
	 * Returns the current state of a rebuild job without waiting.
	 * @param JobId Job id from Rebuild, RebuildRoads or an authoring tool.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDRebuildStatus RebuildStatus(const FString& JobId);

	/**
	 * Waits for a rebuild job to finish, up to TimeoutMs.
	 * @param JobId Job id.
	 * @param TimeoutMs Maximum wait in milliseconds.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static URoadBLDRebuildAsyncResult* WaitForRebuild(const FString& JobId, int32 TimeoutMs = 30000);

	/**
	 * Aborts a running rebuild job. Its networks stay stale until rebuilt again.
	 * @param JobId Job id.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDRebuildStatus CancelRebuild(const FString& JobId);
};
