// Copyright WorldBLD LLC. All rights reserved.

#include "Common/RoadBLDRebuildJobs.h"

#include "Common/RoadBLDToolsetUtils.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "HAL/PlatformTime.h"

namespace RoadBLDRebuildJobsPrivate
{
	constexpr float TickIntervalSeconds = 0.1f;

	// A network counts as finished once it has been idle for this long after dispatch. Covers rebuilds
	// that were coalesced into an in-flight rebuild, where RoadBLD drops the completion callback.
	constexpr double IdleGraceSeconds = 0.5;

	constexpr double FinishedJobLifetimeSeconds = 600.0;
}

FRoadBLDRebuildJobs& FRoadBLDRebuildJobs::Get()
{
	static FRoadBLDRebuildJobs Instance;
	return Instance;
}

void FRoadBLDRebuildJobs::Shutdown()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}

	Jobs.Reset();
	Waiters.Reset();
	IdleWaiters.Reset();
}

bool FRoadBLDRebuildJobs::IsNetworkBusy(const ADynamicRoadNetwork* Network)
{
	return IsValid(Network) && (Network->bRebuildInProgress || Network->bRebuildDirty || Network->bNeedsRebuild);
}

bool FRoadBLDRebuildJobs::IsNetworkRebuilding(const ADynamicRoadNetwork* Network) const
{
	if (!IsValid(Network))
	{
		return false;
	}

	if (Network->bRebuildInProgress || Network->bRebuildDirty)
	{
		return true;
	}

	for (const TPair<FGuid, FJob>& Pair : Jobs)
	{
		const FJob& Job = Pair.Value;
		if (Job.State != ERoadBLDRebuildState::Running)
		{
			continue;
		}

		for (int32 Index = 0; Index < Job.Networks.Num(); ++Index)
		{
			if (!Job.NetworkDone[Index] && Job.Networks[Index].Get() == Network)
			{
				return true;
			}
		}
	}

	return false;
}

void FRoadBLDRebuildJobs::EnsureTicker()
{
	if (!TickerHandle.IsValid())
	{
		TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateRaw(this, &FRoadBLDRebuildJobs::Tick),
			RoadBLDRebuildJobsPrivate::TickIntervalSeconds);
	}
}

FGuid FRoadBLDRebuildJobs::Start(
	const TArray<ADynamicRoadNetwork*>& Networks,
	const TMap<ADynamicRoadNetwork*, TArray<ADynamicRoad*>>& ModifiedRoads,
	const bool bForceRebuildAffectedRoads,
	const bool bLowQualityMesh)
{
	EnsureTicker();

	const FGuid JobId = FGuid::NewGuid();
	FJob& Job = Jobs.Add(JobId);
	Job.StartSeconds = FPlatformTime::Seconds();
	Job.bForceRebuildAffectedRoads = bForceRebuildAffectedRoads;
	Job.bLowQualityMesh = bLowQualityMesh;
	for (ADynamicRoadNetwork* Network : Networks)
	{
		if (!IsValid(Network) || Job.Networks.Contains(Network))
		{
			continue;
		}

		Job.Networks.Add(Network);
		Job.NetworkPaths.Add(Network->GetPathName());
		TArray<TWeakObjectPtr<ADynamicRoad>>& Roads = Job.NetworkRoads.AddDefaulted_GetRef();
		if (const TArray<ADynamicRoad*>* FoundRoads = ModifiedRoads.Find(Network))
		{
			for (ADynamicRoad* Road : *FoundRoads)
			{
				Roads.Add(Road);
			}
		}
	}
	Job.NetworkDone.Init(false, Job.Networks.Num());

	if (Job.Networks.Num() == 0)
	{
		Job.bDispatched = true;
		Job.State = ERoadBLDRebuildState::Succeeded;
		Job.DispatchSeconds = Job.StartSeconds;
		Job.EndSeconds = Job.StartSeconds;
		Job.Message = TEXT("There were no road networks to rebuild.");
	}

	return JobId;
}

void FRoadBLDRebuildJobs::Dispatch(const FGuid& JobId)
{
	FJob* Job = Jobs.Find(JobId);
	if (!Job || Job->State != ERoadBLDRebuildState::Running || Job->bDispatched)
	{
		return;
	}

	Job->bDispatched = true;

	// Dispatch is part of the tool call that queued the job; keep RoadBLD's rebuild setup dialog-free too.
	RoadBLDToolset::MarkCurrentCallUnattended();

	// Completion callbacks can fire synchronously and touch Jobs, so work from copies.
	const TArray<TWeakObjectPtr<ADynamicRoadNetwork>> Networks = Job->Networks;
	const TArray<TArray<TWeakObjectPtr<ADynamicRoad>>> NetworkRoads = Job->NetworkRoads;
	const bool bForceRebuildAffectedRoads = Job->bForceRebuildAffectedRoads;
	const bool bLowQualityMesh = Job->bLowQualityMesh;

	for (int32 Index = 0; Index < Networks.Num(); ++Index)
	{
		ADynamicRoadNetwork* Network = Networks[Index].Get();
		if (!IsValid(Network))
		{
			MarkNetworkDone(JobId, Index);
			continue;
		}

		TArray<ADynamicRoad*> Roads;
		for (const TWeakObjectPtr<ADynamicRoad>& WeakRoad : NetworkRoads[Index])
		{
			if (ADynamicRoad* Road = WeakRoad.Get())
			{
				Roads.Add(Road);
			}
		}

		// The callback may fire synchronously (empty networks, PIE) or from a later commit tick.
		Network->RebuildRoadNetworkIncremental(
			MoveTemp(Roads),
			TArray<ADynamicRoad*>{},
			bForceRebuildAffectedRoads,
			[this, JobId, Index]()
			{
				MarkNetworkDone(JobId, Index);
			},
			bLowQualityMesh);
	}

	// Idle detection starts after RoadBLD has taken the request, not when the job was queued.
	if (FJob* DispatchedJob = Jobs.Find(JobId))
	{
		DispatchedJob->DispatchSeconds = FPlatformTime::Seconds();
	}
}

void FRoadBLDRebuildJobs::MarkNetworkDone(const FGuid& JobId, const int32 NetworkIndex)
{
	FJob* Job = Jobs.Find(JobId);
	if (!Job || Job->State != ERoadBLDRebuildState::Running || !Job->NetworkDone.IsValidIndex(NetworkIndex))
	{
		return;
	}

	Job->NetworkDone[NetworkIndex] = true;
	FinishJobIfComplete(JobId, *Job, FPlatformTime::Seconds());
}

void FRoadBLDRebuildJobs::FinishJobIfComplete(const FGuid& JobId, FJob& Job, const double NowSeconds)
{
	if (Job.State != ERoadBLDRebuildState::Running || Job.NetworkDone.Contains(false))
	{
		return;
	}

	Job.State = ERoadBLDRebuildState::Succeeded;
	Job.EndSeconds = NowSeconds;
	FlushWaiters(JobId);
}

void FRoadBLDRebuildJobs::FlushWaiters(const FGuid& JobId)
{
	TArray<FWaiter> ReadyWaiters;
	for (int32 Index = Waiters.Num() - 1; Index >= 0; --Index)
	{
		if (Waiters[Index].JobId == JobId)
		{
			ReadyWaiters.Add(MoveTemp(Waiters[Index]));
			Waiters.RemoveAtSwap(Index);
		}
	}

	const FJob* Job = Jobs.Find(JobId);
	if (!Job)
	{
		return;
	}

	const FRoadBLDRebuildStatus Status = MakeStatus(JobId, *Job);
	for (FWaiter& Waiter : ReadyWaiters)
	{
		Waiter.OnDone(Status);
	}
}

bool FRoadBLDRebuildJobs::Tick(float DeltaTime)
{
	TArray<FGuid> RunningJobIds;
	for (const TPair<FGuid, FJob>& Pair : Jobs)
	{
		if (Pair.Value.State == ERoadBLDRebuildState::Running)
		{
			RunningJobIds.Add(Pair.Key);
		}
	}

	for (const FGuid& JobId : RunningJobIds)
	{
		Dispatch(JobId);
	}

	// Dispatching can take seconds, so sample the clock afterwards.
	const double NowSeconds = FPlatformTime::Seconds();

	for (const FGuid& JobId : RunningJobIds)
	{
		FJob* Job = Jobs.Find(JobId);
		if (!Job || Job->State != ERoadBLDRebuildState::Running || !Job->bDispatched)
		{
			continue;
		}

		const bool bGraceElapsed = NowSeconds - Job->DispatchSeconds >= RoadBLDRebuildJobsPrivate::IdleGraceSeconds;
		for (int32 Index = 0; Index < Job->Networks.Num(); ++Index)
		{
			if (Job->NetworkDone[Index])
			{
				continue;
			}

			const ADynamicRoadNetwork* Network = Job->Networks[Index].Get();
			if (!IsValid(Network) || (bGraceElapsed && !IsNetworkBusy(Network)))
			{
				Job->NetworkDone[Index] = true;
			}
		}

		FinishJobIfComplete(JobId, *Job, NowSeconds);
	}

	TArray<FWaiter> ExpiredWaiters;
	for (int32 Index = Waiters.Num() - 1; Index >= 0; --Index)
	{
		if (NowSeconds >= Waiters[Index].DeadlineSeconds)
		{
			ExpiredWaiters.Add(MoveTemp(Waiters[Index]));
			Waiters.RemoveAtSwap(Index);
		}
	}

	for (FWaiter& Waiter : ExpiredWaiters)
	{
		FRoadBLDRebuildStatus Status;
		if (const FJob* Job = Jobs.Find(Waiter.JobId))
		{
			Status = MakeStatus(Waiter.JobId, *Job);
		}
		Status.bTimedOut = true;
		Status.Message = TEXT("Timed out while waiting; the rebuild continues. Poll RebuildStatus or call WaitForRebuild again.");
		Waiter.OnDone(Status);
	}

	TArray<TPair<TFunction<void(bool)>, bool>> ReadyIdleWaiters;
	for (int32 Index = IdleWaiters.Num() - 1; Index >= 0; --Index)
	{
		FIdleWaiter& Waiter = IdleWaiters[Index];
		const bool bAnyRebuilding = Waiter.Networks.ContainsByPredicate([this](const TWeakObjectPtr<ADynamicRoadNetwork>& Network)
		{
			return IsNetworkRebuilding(Network.Get());
		});

		const bool bIdle = !bAnyRebuilding && NowSeconds - Waiter.StartSeconds >= RoadBLDRebuildJobsPrivate::IdleGraceSeconds;
		if (bIdle || NowSeconds >= Waiter.DeadlineSeconds)
		{
			ReadyIdleWaiters.Emplace(MoveTemp(Waiter.OnDone), bIdle);
			IdleWaiters.RemoveAtSwap(Index);
		}
	}

	for (TPair<TFunction<void(bool)>, bool>& Ready : ReadyIdleWaiters)
	{
		Ready.Key(Ready.Value);
	}

	for (auto It = Jobs.CreateIterator(); It; ++It)
	{
		if (It.Value().State != ERoadBLDRebuildState::Running
			&& NowSeconds - It.Value().EndSeconds > RoadBLDRebuildJobsPrivate::FinishedJobLifetimeSeconds)
		{
			It.RemoveCurrent();
		}
	}

	return true;
}

bool FRoadBLDRebuildJobs::GetStatus(const FGuid& JobId, FRoadBLDRebuildStatus& OutStatus) const
{
	const FJob* Job = Jobs.Find(JobId);
	if (!Job)
	{
		return false;
	}

	OutStatus = MakeStatus(JobId, *Job);
	return true;
}

void FRoadBLDRebuildJobs::Wait(const FGuid& JobId, const double TimeoutSeconds, TFunction<void(const FRoadBLDRebuildStatus&)> OnDone)
{
	const FJob* Job = Jobs.Find(JobId);
	if (!Job)
	{
		FRoadBLDRebuildStatus Status;
		Status.JobId = JobId.ToString(EGuidFormats::DigitsWithHyphensLower);
		Status.State = ERoadBLDRebuildState::Failed;
		Status.Message = TEXT("Unknown rebuild job. Jobs are forgotten 10 minutes after they finish.");
		OnDone(Status);
		return;
	}

	if (Job->State != ERoadBLDRebuildState::Running)
	{
		OnDone(MakeStatus(JobId, *Job));
		return;
	}

	EnsureTicker();
	FWaiter& Waiter = Waiters.AddDefaulted_GetRef();
	Waiter.JobId = JobId;
	Waiter.DeadlineSeconds = FPlatformTime::Seconds() + FMath::Max(0.0, TimeoutSeconds);
	Waiter.OnDone = MoveTemp(OnDone);
}

void FRoadBLDRebuildJobs::WaitForNetworksIdle(
	const TArray<ADynamicRoadNetwork*>& Networks,
	const double TimeoutSeconds,
	TFunction<void(bool)> OnDone)
{
	EnsureTicker();
	FIdleWaiter& Waiter = IdleWaiters.AddDefaulted_GetRef();
	for (ADynamicRoadNetwork* Network : Networks)
	{
		if (IsValid(Network))
		{
			Waiter.Networks.Add(Network);
		}
	}
	Waiter.StartSeconds = FPlatformTime::Seconds();
	Waiter.DeadlineSeconds = Waiter.StartSeconds + FMath::Max(0.0, TimeoutSeconds);
	Waiter.OnDone = MoveTemp(OnDone);
}

bool FRoadBLDRebuildJobs::Cancel(const FGuid& JobId, FRoadBLDRebuildStatus& OutStatus)
{
	FJob* Job = Jobs.Find(JobId);
	if (!Job)
	{
		return false;
	}

	if (Job->State == ERoadBLDRebuildState::Running)
	{
		const bool bWasDispatched = Job->bDispatched;
		if (bWasDispatched)
		{
			const TArray<TWeakObjectPtr<ADynamicRoadNetwork>> Networks = Job->Networks;
			for (const TWeakObjectPtr<ADynamicRoadNetwork>& WeakNetwork : Networks)
			{
				if (ADynamicRoadNetwork* Network = WeakNetwork.Get())
				{
					Network->AbortAndWaitForPendingRebuild();
				}
			}

			// Aborting can complete callbacks that change Jobs.
			Job = Jobs.Find(JobId);
			if (!Job)
			{
				return false;
			}
		}

		if (Job->State == ERoadBLDRebuildState::Running)
		{
			Job->bDispatched = true;
			Job->State = ERoadBLDRebuildState::Aborted;
			Job->EndSeconds = FPlatformTime::Seconds();
			Job->Message = bWasDispatched
				? TEXT("Rebuild aborted. Affected networks stay stale until rebuilt.")
				: TEXT("Rebuild cancelled before it started. Affected networks stay stale until rebuilt.");
			FlushWaiters(JobId);
		}
	}

	if (const FJob* FinalJob = Jobs.Find(JobId))
	{
		OutStatus = MakeStatus(JobId, *FinalJob);
	}
	return true;
}

FRoadBLDRebuildStatus FRoadBLDRebuildJobs::MakeStatus(const FGuid& JobId, const FJob& Job) const
{
	FRoadBLDRebuildStatus Status;
	Status.JobId = JobId.ToString(EGuidFormats::DigitsWithHyphensLower);
	Status.State = Job.State;
	Status.Message = Job.Message;

	const double EndSeconds = Job.State == ERoadBLDRebuildState::Running ? FPlatformTime::Seconds() : Job.EndSeconds;
	Status.ElapsedMs = (EndSeconds - Job.StartSeconds) * 1000.0;

	for (int32 Index = 0; Index < Job.Networks.Num(); ++Index)
	{
		if (const ADynamicRoadNetwork* Network = Job.Networks[Index].Get())
		{
			Status.Networks.Add(RoadBLDToolset::MakeActorRef(Network));
		}
		else
		{
			FRoadBLDActorRef& Ref = Status.Networks.AddDefaulted_GetRef();
			Ref.RefPath = Job.NetworkPaths[Index];
		}

		if (!Job.NetworkDone[Index])
		{
			++Status.RemainingNetworks;
		}
	}

	return Status;
}
