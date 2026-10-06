// Copyright WorldBLD LLC. All Rights Reserved.

#include "WorldBLDContextMenuRegistry.h"

#include "IWorldBLDContextMenuFactory.h"
#include "WorldBLDEditorModule.h"

#include "GameFramework/Actor.h"

TWeakObjectPtr<UWorldBLDContextMenuRegistry> UWorldBLDContextMenuRegistry::Instance = nullptr;

UWorldBLDContextMenuRegistry* UWorldBLDContextMenuRegistry::Get()
{
	if (UWorldBLDContextMenuRegistry* ExistingInstance = Instance.Get())
	{
		return ExistingInstance;
	}

	if (IsEngineExitRequested() || GExitPurge)
	{
		return nullptr;
	}

	UWorldBLDContextMenuRegistry* NewInstance = NewObject<UWorldBLDContextMenuRegistry>(GetTransientPackage());
	if (IsValid(NewInstance))
	{
		NewInstance->AddToRoot();
		Instance = NewInstance;
	}

	return NewInstance;
}

UWorldBLDContextMenuRegistry* UWorldBLDContextMenuRegistry::TryGet()
{
	if (IsEngineExitRequested() || GExitPurge)
	{
		return nullptr;
	}

	UWorldBLDContextMenuRegistry* ExistingInstance = Instance.Get();
	if (!IsValid(ExistingInstance))
	{
		Instance = nullptr;
		return nullptr;
	}

	if (ExistingInstance->HasAnyFlags(RF_BeginDestroyed | RF_FinishDestroyed))
	{
		Instance = nullptr;
		return nullptr;
	}

	return ExistingInstance;
}

void UWorldBLDContextMenuRegistry::RegisterFactory(UClass* ActorClass, TScriptInterface<IWorldBLDContextMenuFactory> Factory)
{
	if (IsEngineExitRequested() || GExitPurge || HasAnyFlags(RF_BeginDestroyed | RF_FinishDestroyed))
	{
		return;
	}

	if (!ActorClass)
	{
		UE_LOG(LogWorldBuild, Warning, TEXT("RegisterFactory called with null ActorClass"));
		return;
	}

	if (!Factory.GetObject())
	{
		UE_LOG(LogWorldBuild, Warning, TEXT("RegisterFactory called with null Factory for class %s"), *ActorClass->GetName());
		return;
	}

	FactoryMap.Add(ActorClass, Factory);
	UE_LOG(LogWorldBuild, Log, TEXT("Registered context menu factory for %s"), *ActorClass->GetName());
}

void UWorldBLDContextMenuRegistry::UnregisterFactory(UClass* ActorClass)
{
	if (IsEngineExitRequested() || GExitPurge || HasAnyFlags(RF_BeginDestroyed | RF_FinishDestroyed))
	{
		return;
	}

	if (!ActorClass)
	{
		UE_LOG(LogWorldBuild, Warning, TEXT("UnregisterFactory called with null ActorClass"));
		return;
	}

	FactoryMap.Remove(ActorClass);
	UE_LOG(LogWorldBuild, Log, TEXT("Unregistered context menu factory for %s"), *ActorClass->GetName());
}

TScriptInterface<IWorldBLDContextMenuFactory> UWorldBLDContextMenuRegistry::FindFactoryForActor(AActor* Actor) const
{
	if (!IsValid(Actor))
	{
		return TScriptInterface<IWorldBLDContextMenuFactory>();
	}

	return FindFactoryForClass(Actor->GetClass());
}

TScriptInterface<IWorldBLDContextMenuFactory> UWorldBLDContextMenuRegistry::FindFactoryForClass(UClass* ActorClass) const
{
	for (UClass* CurrentClass = ActorClass; CurrentClass; CurrentClass = CurrentClass->GetSuperClass())
	{
		if (const TScriptInterface<IWorldBLDContextMenuFactory>* FoundFactory = FactoryMap.Find(CurrentClass))
		{
			return *FoundFactory;
		}
	}

	return TScriptInterface<IWorldBLDContextMenuFactory>();
}
