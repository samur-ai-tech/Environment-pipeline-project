// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "BLDToolsetTypes.h"
#include "Containers/Ticker.h"
#include "Templates/Function.h"

/** Mutable progress of a job. Written by poll functions and completion callbacks. */
struct BLDTOOLSETCOMMON_API FBLDJobProgress
{
	FString Stage;
	double Progress = 0.0;
	FString Message;
	TArray<FString> Warnings;
	TArray<FString> Log;
	FString ResultJson;

	/** Appends a log line, keeping only the most recent lines. */
	void AddLog(const FString& Line);
};

struct BLDTOOLSETCOMMON_API FBLDJobDefinition
{
	/** Short job kind such as TwinBLD.GenerateTiles. */
	FString Kind;

	/**
	 * Called on the game thread every tick while the job runs. Return Running to keep polling, or a final state to finish.
	 * Optional: callback-driven jobs call FBLDJobRegistry::Update and Finish instead. A poll function must not call
	 * Update for its own job; write to the progress it is given.
	 */
	TFunction<EBLDJobState(FBLDJobProgress&)> Poll;

	/** Called once when the job is cancelled. Stop the underlying work here. */
	TFunction<void()> OnCancel;

	/** The job fails once it has run this long. 0 means no limit. */
	double MaxRuntimeSeconds = 0.0;
};

/**
 * Tracks long-running toolset work so agents can wait on it, poll it or cancel it. Shared by every BLD toolset.
 * All calls must happen on the game thread. Finished jobs are forgotten 10 minutes after they end.
 */
class BLDTOOLSETCOMMON_API FBLDJobRegistry
{
public:
	static FBLDJobRegistry& Get();

	void Shutdown();

	/** Starts tracking a job. The job is Running until its poll function or Finish ends it. */
	FGuid Start(FBLDJobDefinition Definition);

	/** Edits the progress of a running job. Does nothing for unknown or finished jobs. */
	void Update(const FGuid& JobId, TFunctionRef<void(FBLDJobProgress&)> Mutator);

	/** Ends a running job. Message replaces the progress message when it is not empty. */
	void Finish(const FGuid& JobId, EBLDJobState State, const FString& Message = FString());

	bool GetStatus(const FGuid& JobId, FBLDJobStatus& OutStatus) const;

	bool IsRunning(const FGuid& JobId) const;

	/** Statuses of jobs whose kind starts with KindPrefix, newest first. */
	TArray<FBLDJobStatus> ListJobs(const FString& KindPrefix, bool bRunningOnly) const;

	/** Calls OnDone when the job finishes, or after TimeoutSeconds with bTimedOut=true. Unknown jobs report Failed. */
	void Wait(const FGuid& JobId, double TimeoutSeconds, TFunction<void(const FBLDJobStatus&)> OnDone);

	/** Cancels a running job and calls its OnCancel. Returns false for unknown jobs. */
	bool Cancel(const FGuid& JobId, FBLDJobStatus& OutStatus);

	/**
	 * Completes Result with the job status: immediately when bWait is false, otherwise when the job finishes or
	 * TimeoutMs elapses. ToolsetName prefixes the error for unknown jobs.
	 */
	void CompleteAsyncResult(UBLDJobAsyncResult* Result, const FGuid& JobId, bool bWait, int32 TimeoutMs, const TCHAR* ToolsetName);

private:
	struct FJob
	{
		FBLDJobDefinition Definition;
		FBLDJobProgress Progress;
		EBLDJobState State = EBLDJobState::Running;
		double StartSeconds = 0.0;
		double EndSeconds = 0.0;
	};

	struct FWaiter
	{
		FGuid JobId;
		double DeadlineSeconds = 0.0;
		TFunction<void(const FBLDJobStatus&)> OnDone;
	};

	void EnsureTicker();
	bool Tick(float DeltaTime);
	void FinishInternal(const FGuid& JobId, EBLDJobState State, const FString& Message);
	void FlushWaiters(const FGuid& JobId);
	FBLDJobStatus MakeStatus(const FGuid& JobId, const FJob& Job) const;

	TMap<FGuid, FJob> Jobs;
	TArray<FWaiter> Waiters;
	FTSTicker::FDelegateHandle TickerHandle;
};
