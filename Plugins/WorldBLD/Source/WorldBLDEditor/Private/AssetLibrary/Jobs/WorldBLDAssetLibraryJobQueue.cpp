// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/Jobs/WorldBLDAssetLibraryJobQueue.h"

#include "UObject/GarbageCollection.h"
#include "UObject/UObjectGlobals.h"

FWorldBLDAssetLibraryJobQueue::FWorldBLDAssetLibraryJobQueue(TWeakObjectPtr<UWorldBLDAssetDownloadManager> InManager)
	: Manager(InManager)
{
}

void FWorldBLDAssetLibraryJobQueue::Enqueue(TSharedPtr<IWorldBLDAssetJob> Job)
{
	if (!Job.IsValid())
	{
		return;
	}

	FScopeLock Lock(&QueueMutex);
	Queue.Enqueue(MoveTemp(Job));
}

bool FWorldBLDAssetLibraryJobQueue::IsBusy() const
{
	FScopeLock Lock(&QueueMutex);
	return ActiveJob.IsValid() || !Queue.IsEmpty();
}

bool FWorldBLDAssetLibraryJobQueue::CanExecuteNow() const
{
	return !IsGarbageCollecting() && !UE::IsSavingPackage();
}

void FWorldBLDAssetLibraryJobQueue::Tick(float DeltaTime)
{
	if (!CanExecuteNow())
	{
		return;
	}

	{
		FScopeLock Lock(&QueueMutex);
		if (!ActiveJob.IsValid())
		{
			Queue.Dequeue(ActiveJob);
		}
	}

	if (!ActiveJob.IsValid())
	{
		return;
	}

	const bool bFinished = ActiveJob->TickJob(DeltaTime);
	if (bFinished)
	{
		FScopeLock Lock(&QueueMutex);
		ActiveJob.Reset();
	}
}

TStatId FWorldBLDAssetLibraryJobQueue::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(WorldBLDAssetLibraryJobQueue, STATGROUP_Tickables);
}

