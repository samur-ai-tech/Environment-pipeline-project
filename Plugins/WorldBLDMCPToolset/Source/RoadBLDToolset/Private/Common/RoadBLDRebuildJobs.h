// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/RoadBLDToolsetTypes.h"
#include "Containers/Ticker.h"
#include "Templates/Function.h"
#include "UObject/WeakObjectPtrTemplates.h"

class ADynamicRoad;
class ADynamicRoadNetwork;

/**
 * Tracks road network rebuilds started by the toolset so agents can wait on them, poll them, or cancel them.
 *
 * Rebuilds run asynchronously and complete on the game thread. RoadBLD drops the completion callback when a
 * request is coalesced into an in-flight rebuild, so a ticker also watches each network's rebuild flags.
 */
class FRoadBLDRebuildJobs
{
public:
	static FRoadBLDRebuildJobs& Get();

	void Shutdown();

	/**
	 * Registers a rebuild for each network and dispatches it on the next ticker tick, so the calling tool returns
	 * before RoadBLD's synchronous rebuild setup runs. Networks without an entry in ModifiedRoads get a full rebuild.
	 * @return The job id, parseable with FGuid::Parse.
	 */
	FGuid Start(
		const TArray<ADynamicRoadNetwork*>& Networks,
		const TMap<ADynamicRoadNetwork*, TArray<ADynamicRoad*>>& ModifiedRoads,
		bool bForceRebuildAffectedRoads,
		bool bLowQualityMesh);

	bool GetStatus(const FGuid& JobId, FRoadBLDRebuildStatus& OutStatus) const;

	/** Calls OnDone when the job finishes or TimeoutSeconds elapse (status then has bTimedOut=true). */
	void Wait(const FGuid& JobId, double TimeoutSeconds, TFunction<void(const FRoadBLDRebuildStatus&)> OnDone);

	/**
	 * Calls OnDone(true) once no network has a rebuild queued or in flight, or OnDone(false) after TimeoutSeconds.
	 * Stale networks with nothing queued count as idle.
	 */
	void WaitForNetworksIdle(const TArray<ADynamicRoadNetwork*>& Networks, double TimeoutSeconds, TFunction<void(bool)> OnDone);

	bool Cancel(const FGuid& JobId, FRoadBLDRebuildStatus& OutStatus);

	/** True while the network has unbuilt edits or a rebuild in flight. */
	static bool IsNetworkBusy(const ADynamicRoadNetwork* Network);

	/** True while a rebuild is in flight on the network or a toolset job for it has not finished. */
	bool IsNetworkRebuilding(const ADynamicRoadNetwork* Network) const;

private:
	struct FJob
	{
		TArray<TWeakObjectPtr<ADynamicRoadNetwork>> Networks;
		TArray<FString> NetworkPaths;
		TArray<bool> NetworkDone;
		TArray<TArray<TWeakObjectPtr<ADynamicRoad>>> NetworkRoads;
		bool bForceRebuildAffectedRoads = false;
		bool bLowQualityMesh = false;
		bool bDispatched = false;
		double StartSeconds = 0.0;
		double DispatchSeconds = 0.0;
		double EndSeconds = 0.0;
		ERoadBLDRebuildState State = ERoadBLDRebuildState::Running;
		FString Message;
	};

	struct FWaiter
	{
		FGuid JobId;
		double DeadlineSeconds = 0.0;
		TFunction<void(const FRoadBLDRebuildStatus&)> OnDone;
	};

	struct FIdleWaiter
	{
		TArray<TWeakObjectPtr<ADynamicRoadNetwork>> Networks;
		double StartSeconds = 0.0;
		double DeadlineSeconds = 0.0;
		TFunction<void(bool)> OnDone;
	};

	void EnsureTicker();
	bool Tick(float DeltaTime);
	void Dispatch(const FGuid& JobId);
	void MarkNetworkDone(const FGuid& JobId, int32 NetworkIndex);
	void FinishJobIfComplete(const FGuid& JobId, FJob& Job, double NowSeconds);
	void FlushWaiters(const FGuid& JobId);
	FRoadBLDRebuildStatus MakeStatus(const FGuid& JobId, const FJob& Job) const;

	TMap<FGuid, FJob> Jobs;
	TArray<FWaiter> Waiters;
	TArray<FIdleWaiter> IdleWaiters;
	FTSTicker::FDelegateHandle TickerHandle;
};
