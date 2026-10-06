// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/RoadBLDBuildToolset.h"

#include "Common/RoadBLDRebuildJobs.h"
#include "Common/RoadBLDToolsetUtils.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "UObject/StrongObjectPtr.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(RoadBLDBuildToolset)

namespace RoadBLDBuildPrivate
{
	void CompleteWithJob(URoadBLDRebuildAsyncResult* Result, const FGuid& JobId, const bool bWait, const int32 TimeoutMs)
	{
		if (!bWait)
		{
			FRoadBLDRebuildStatus Status;
			FRoadBLDRebuildJobs::Get().GetStatus(JobId, Status);
			Result->SetValue(Status);
			return;
		}

		TStrongObjectPtr<URoadBLDRebuildAsyncResult> StrongResult(Result);
		FRoadBLDRebuildJobs::Get().Wait(
			JobId,
			FMath::Max(0, TimeoutMs) / 1000.0,
			[StrongResult](const FRoadBLDRebuildStatus& Status) mutable
			{
				if (StrongResult.IsValid())
				{
					StrongResult->SetValue(Status);
					StrongResult.Reset();
				}
			});
	}

	/** Completes Result with the access error when edits are blocked. Async tools report errors only through the result. */
	bool CheckAuthorized(URoadBLDRebuildAsyncResult* Result)
	{
		FString Error;
		if (RoadBLDToolset::CheckAuthorized(Error))
		{
			return true;
		}

		Result->SetError(FString::Printf(TEXT("RoadBLDToolset: %s"), *Error));
		return false;
	}

	bool ParseJobId(const FString& JobId, FGuid& OutGuid)
	{
		if (FGuid::Parse(JobId.TrimStartAndEnd(), OutGuid))
		{
			return true;
		}

		RoadBLDToolset::RaiseError(FString::Printf(TEXT("'%s' is not a valid rebuild job id."), *JobId));
		return false;
	}
}

URoadBLDRebuildAsyncResult* URoadBLDBuildToolset::Rebuild(
	ADynamicRoadNetwork* Network,
	const bool bOnlyStale,
	const bool bForceRebuildAll,
	const bool bWait,
	const int32 TimeoutMs,
	const bool bLowQualityMesh)
{
	URoadBLDRebuildAsyncResult* Result = NewObject<URoadBLDRebuildAsyncResult>();
	if (!RoadBLDBuildPrivate::CheckAuthorized(Result))
	{
		return Result;
	}

	TArray<ADynamicRoadNetwork*> Networks;
	if (IsValid(Network))
	{
		Networks.Add(Network);
	}
	else
	{
		for (ADynamicRoadNetwork* Candidate : RoadBLDToolset::GetNetworks())
		{
			if (!bOnlyStale || Candidate->IsRoadNetworkStale())
			{
				Networks.Add(Candidate);
			}
		}
	}

	const FGuid JobId = FRoadBLDRebuildJobs::Get().Start(Networks, {}, bForceRebuildAll, bLowQualityMesh);
	RoadBLDBuildPrivate::CompleteWithJob(Result, JobId, bWait, TimeoutMs);
	return Result;
}

URoadBLDRebuildAsyncResult* URoadBLDBuildToolset::RebuildRoads(const TArray<ADynamicRoad*>& Roads, const bool bWait, const int32 TimeoutMs)
{
	URoadBLDRebuildAsyncResult* Result = NewObject<URoadBLDRebuildAsyncResult>();
	if (!RoadBLDBuildPrivate::CheckAuthorized(Result))
	{
		return Result;
	}

	TMap<ADynamicRoadNetwork*, TArray<ADynamicRoad*>> RoadsByNetwork;
	for (ADynamicRoad* Road : Roads)
	{
		if (ADynamicRoadNetwork* Network = RoadBLDToolset::GetOwningNetwork(Road))
		{
			RoadsByNetwork.FindOrAdd(Network).AddUnique(Road);
		}
	}

	if (RoadsByNetwork.Num() == 0)
	{
		Result->SetError(TEXT("RoadBLDToolset: Roads must contain at least one road that belongs to a network."));
		return Result;
	}

	TArray<ADynamicRoadNetwork*> Networks;
	RoadsByNetwork.GetKeys(Networks);
	const FGuid JobId = FRoadBLDRebuildJobs::Get().Start(Networks, RoadsByNetwork, false, false);
	RoadBLDBuildPrivate::CompleteWithJob(Result, JobId, bWait, TimeoutMs);
	return Result;
}

FRoadBLDRebuildStatus URoadBLDBuildToolset::RebuildStatus(const FString& JobId)
{
	FRoadBLDRebuildStatus Status;
	FGuid Guid;
	if (!RoadBLDBuildPrivate::ParseJobId(JobId, Guid))
	{
		return Status;
	}

	if (!FRoadBLDRebuildJobs::Get().GetStatus(Guid, Status))
	{
		RoadBLDToolset::RaiseError(TEXT("Unknown rebuild job. Jobs are forgotten 10 minutes after they finish."));
	}
	return Status;
}

URoadBLDRebuildAsyncResult* URoadBLDBuildToolset::WaitForRebuild(const FString& JobId, const int32 TimeoutMs)
{
	URoadBLDRebuildAsyncResult* Result = NewObject<URoadBLDRebuildAsyncResult>();
	FGuid Guid;
	if (!FGuid::Parse(JobId.TrimStartAndEnd(), Guid))
	{
		Result->SetError(FString::Printf(TEXT("RoadBLDToolset: '%s' is not a valid rebuild job id."), *JobId));
		return Result;
	}

	RoadBLDBuildPrivate::CompleteWithJob(Result, Guid, true, TimeoutMs);
	return Result;
}

FRoadBLDRebuildStatus URoadBLDBuildToolset::CancelRebuild(const FString& JobId)
{
	FRoadBLDRebuildStatus Status;
	FGuid Guid;
	if (!RoadBLDBuildPrivate::ParseJobId(JobId, Guid))
	{
		return Status;
	}

	if (!FRoadBLDRebuildJobs::Get().Cancel(Guid, Status))
	{
		RoadBLDToolset::RaiseError(TEXT("Unknown rebuild job."));
	}
	return Status;
}
