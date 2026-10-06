// Copyright WorldBLD LLC. All rights reserved.

#include "BLDJobRegistry.h"

#include "HAL/PlatformTime.h"
#include "UObject/StrongObjectPtr.h"

namespace BLDJobRegistryPrivate
{
	constexpr float TickIntervalSeconds = 0.1f;
	constexpr double FinishedJobLifetimeSeconds = 600.0;
	constexpr int32 MaxLogLines = 40;
}

void FBLDJobProgress::AddLog(const FString& Line)
{
	Log.Add(Line);
	if (Log.Num() > BLDJobRegistryPrivate::MaxLogLines)
	{
		Log.RemoveAt(0, Log.Num() - BLDJobRegistryPrivate::MaxLogLines);
	}
}

FBLDJobRegistry& FBLDJobRegistry::Get()
{
	static FBLDJobRegistry Instance;
	return Instance;
}

void FBLDJobRegistry::Shutdown()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}

	Jobs.Reset();
	Waiters.Reset();
}

void FBLDJobRegistry::EnsureTicker()
{
	if (!TickerHandle.IsValid())
	{
		TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateRaw(this, &FBLDJobRegistry::Tick),
			BLDJobRegistryPrivate::TickIntervalSeconds);
	}
}

FGuid FBLDJobRegistry::Start(FBLDJobDefinition Definition)
{
	EnsureTicker();

	const FGuid JobId = FGuid::NewGuid();
	FJob& Job = Jobs.Add(JobId);
	Job.Definition = MoveTemp(Definition);
	Job.StartSeconds = FPlatformTime::Seconds();
	return JobId;
}

void FBLDJobRegistry::Update(const FGuid& JobId, TFunctionRef<void(FBLDJobProgress&)> Mutator)
{
	if (FJob* Job = Jobs.Find(JobId))
	{
		if (Job->State == EBLDJobState::Running)
		{
			Mutator(Job->Progress);
		}
	}
}

void FBLDJobRegistry::Finish(const FGuid& JobId, const EBLDJobState State, const FString& Message)
{
	FinishInternal(JobId, State, Message);
}

void FBLDJobRegistry::FinishInternal(const FGuid& JobId, const EBLDJobState State, const FString& Message)
{
	FJob* Job = Jobs.Find(JobId);
	if (!Job || Job->State != EBLDJobState::Running)
	{
		return;
	}

	Job->State = State == EBLDJobState::Running ? EBLDJobState::Succeeded : State;
	Job->EndSeconds = FPlatformTime::Seconds();
	if (!Message.IsEmpty())
	{
		Job->Progress.Message = Message;
	}
	if (Job->State == EBLDJobState::Succeeded)
	{
		Job->Progress.Progress = 1.0;
	}

	FlushWaiters(JobId);
}

void FBLDJobRegistry::FlushWaiters(const FGuid& JobId)
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

	const FBLDJobStatus Status = MakeStatus(JobId, *Job);
	for (FWaiter& Waiter : ReadyWaiters)
	{
		Waiter.OnDone(Status);
	}
}

bool FBLDJobRegistry::Tick(float DeltaTime)
{
	const double NowSeconds = FPlatformTime::Seconds();

	TArray<FGuid> RunningJobIds;
	for (const TPair<FGuid, FJob>& Pair : Jobs)
	{
		if (Pair.Value.State == EBLDJobState::Running)
		{
			RunningJobIds.Add(Pair.Key);
		}
	}

	for (const FGuid& JobId : RunningJobIds)
	{
		FJob* Job = Jobs.Find(JobId);
		if (!Job || Job->State != EBLDJobState::Running)
		{
			continue;
		}

		const double MaxRuntime = Job->Definition.MaxRuntimeSeconds;
		if (MaxRuntime > 0.0 && NowSeconds - Job->StartSeconds > MaxRuntime)
		{
			if (Job->Definition.OnCancel)
			{
				TFunction<void()> OnCancel = Job->Definition.OnCancel;
				OnCancel();
			}
			FinishInternal(JobId, EBLDJobState::Failed, FString::Printf(TEXT("The job exceeded its time limit of %.0f seconds."), MaxRuntime));
			continue;
		}

		if (!Job->Definition.Poll)
		{
			continue;
		}

		// Poll functions may start other jobs, which can reallocate the map, so work on copies.
		TFunction<EBLDJobState(FBLDJobProgress&)> Poll = Job->Definition.Poll;
		FBLDJobProgress Progress = Job->Progress;
		const EBLDJobState NewState = Poll(Progress);

		Job = Jobs.Find(JobId);
		if (!Job || Job->State != EBLDJobState::Running)
		{
			continue;
		}

		Job->Progress = MoveTemp(Progress);
		if (NewState != EBLDJobState::Running)
		{
			FinishInternal(JobId, NewState, FString());
		}
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
		FBLDJobStatus Status;
		if (const FJob* Job = Jobs.Find(Waiter.JobId))
		{
			Status = MakeStatus(Waiter.JobId, *Job);
		}
		Status.bTimedOut = true;
		Status.Message = FString::Printf(TEXT("Timed out while waiting; the job continues. %s"), *Status.Message);
		Waiter.OnDone(Status);
	}

	for (auto It = Jobs.CreateIterator(); It; ++It)
	{
		if (It.Value().State != EBLDJobState::Running
			&& NowSeconds - It.Value().EndSeconds > BLDJobRegistryPrivate::FinishedJobLifetimeSeconds)
		{
			It.RemoveCurrent();
		}
	}

	return true;
}

bool FBLDJobRegistry::GetStatus(const FGuid& JobId, FBLDJobStatus& OutStatus) const
{
	const FJob* Job = Jobs.Find(JobId);
	if (!Job)
	{
		return false;
	}

	OutStatus = MakeStatus(JobId, *Job);
	return true;
}

bool FBLDJobRegistry::IsRunning(const FGuid& JobId) const
{
	const FJob* Job = Jobs.Find(JobId);
	return Job && Job->State == EBLDJobState::Running;
}

TArray<FBLDJobStatus> FBLDJobRegistry::ListJobs(const FString& KindPrefix, const bool bRunningOnly) const
{
	TArray<TPair<double, FBLDJobStatus>> Sorted;
	for (const TPair<FGuid, FJob>& Pair : Jobs)
	{
		if (bRunningOnly && Pair.Value.State != EBLDJobState::Running)
		{
			continue;
		}

		if (!KindPrefix.IsEmpty() && !Pair.Value.Definition.Kind.StartsWith(KindPrefix))
		{
			continue;
		}

		Sorted.Emplace(Pair.Value.StartSeconds, MakeStatus(Pair.Key, Pair.Value));
	}

	Sorted.Sort([](const TPair<double, FBLDJobStatus>& A, const TPair<double, FBLDJobStatus>& B)
	{
		return A.Key > B.Key;
	});

	TArray<FBLDJobStatus> Statuses;
	for (TPair<double, FBLDJobStatus>& Entry : Sorted)
	{
		Statuses.Add(MoveTemp(Entry.Value));
	}
	return Statuses;
}

void FBLDJobRegistry::Wait(const FGuid& JobId, const double TimeoutSeconds, TFunction<void(const FBLDJobStatus&)> OnDone)
{
	const FJob* Job = Jobs.Find(JobId);
	if (!Job)
	{
		FBLDJobStatus Status;
		Status.JobId = JobId.ToString(EGuidFormats::DigitsWithHyphensLower);
		Status.State = EBLDJobState::Failed;
		Status.Message = TEXT("Unknown job. Jobs are forgotten 10 minutes after they finish.");
		OnDone(Status);
		return;
	}

	if (Job->State != EBLDJobState::Running)
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

bool FBLDJobRegistry::Cancel(const FGuid& JobId, FBLDJobStatus& OutStatus)
{
	FJob* Job = Jobs.Find(JobId);
	if (!Job)
	{
		return false;
	}

	if (Job->State == EBLDJobState::Running)
	{
		if (Job->Definition.OnCancel)
		{
			TFunction<void()> OnCancel = Job->Definition.OnCancel;
			OnCancel();
		}
		FinishInternal(JobId, EBLDJobState::Aborted, TEXT("Cancelled."));
	}

	if (const FJob* Cancelled = Jobs.Find(JobId))
	{
		OutStatus = MakeStatus(JobId, *Cancelled);
	}
	return true;
}

void FBLDJobRegistry::CompleteAsyncResult(
	UBLDJobAsyncResult* Result,
	const FGuid& JobId,
	const bool bWait,
	const int32 TimeoutMs,
	const TCHAR* ToolsetName)
{
	if (!Result)
	{
		return;
	}

	if (!bWait)
	{
		FBLDJobStatus Status;
		if (!GetStatus(JobId, Status))
		{
			Result->SetError(FString::Printf(TEXT("%s: Unknown job. Jobs are forgotten 10 minutes after they finish."), ToolsetName));
			return;
		}
		Result->SetValue(Status);
		return;
	}

	TStrongObjectPtr<UBLDJobAsyncResult> StrongResult(Result);
	Wait(JobId, FMath::Max(0, TimeoutMs) / 1000.0, [StrongResult](const FBLDJobStatus& Status)
	{
		StrongResult->SetValue(Status);
	});
}

FBLDJobStatus FBLDJobRegistry::MakeStatus(const FGuid& JobId, const FJob& Job) const
{
	FBLDJobStatus Status;
	Status.JobId = JobId.ToString(EGuidFormats::DigitsWithHyphensLower);
	Status.Kind = Job.Definition.Kind;
	Status.State = Job.State;
	Status.Stage = Job.Progress.Stage;
	Status.Progress = FMath::Clamp(Job.Progress.Progress, 0.0, 1.0);
	Status.Message = Job.Progress.Message;
	Status.Warnings = Job.Progress.Warnings;
	Status.Log = Job.Progress.Log;
	Status.ResultJson = Job.Progress.ResultJson;

	const double EndSeconds = Job.State == EBLDJobState::Running ? FPlatformTime::Seconds() : Job.EndSeconds;
	Status.ElapsedMs = (EndSeconds - Job.StartSeconds) * 1000.0;
	return Status;
}
