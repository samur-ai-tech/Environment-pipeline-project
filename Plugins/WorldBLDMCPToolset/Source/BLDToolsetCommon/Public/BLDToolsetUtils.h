// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "BLDToolsetTypes.h"

class AActor;
class UClass;
class UObject;
class UWorld;

/** Helpers shared by the WorldBLD, CityBLD and TwinBLD toolsets. */
namespace BLDToolset
{
	/** Raises a script error that the ToolsetRegistry reports to the agent, prefixed with the toolset name. */
	BLDTOOLSETCOMMON_API void RaiseError(const TCHAR* ToolsetName, const FString& Message);

	/** The editor world, or null when no editor world is loaded. Marks the calling tool as unattended so product UI skips modal dialogs. */
	BLDTOOLSETCOMMON_API UWorld* GetEditorWorld();

	/** Sets GIsRunningUnattendedScript until the next tick so product code takes the unattended path. */
	BLDTOOLSETCOMMON_API void MarkCurrentCallUnattended();

	BLDTOOLSETCOMMON_API FBLDActorRef MakeActorRef(const AActor* Actor);

	/** Keeps letters, digits and underscores (spaces and dashes become underscores), capped at 64 characters. */
	BLDTOOLSETCOMMON_API FString SanitizeAssetName(const FString& Name);

	/** Loads an asset from /Game/Folder/Asset, /Game/Folder/Asset.Asset or Type'/Game/Folder/Asset.Asset'. */
	BLDTOOLSETCOMMON_API UObject* LoadObjectFromPath(const FString& Path, UClass* ExpectedClass, FString& OutError);

	/** Loads a class from a native class path, a Blueprint asset path, or a generated class path (with or without _C). */
	BLDTOOLSETCOMMON_API UClass* LoadClassFromPath(const FString& Path, UClass* BaseClass, FString& OutError);

	/** /Game plus the content roots of enabled project plugins. */
	BLDTOOLSETCOMMON_API TArray<FName> GetContentRoots();

	/** Native and Blueprint subclasses of BaseClass, skipping abstract, deprecated and skeleton classes. */
	BLDTOOLSETCOMMON_API TArray<UClass*> DiscoverClasses(UClass* BaseClass);

	BLDTOOLSETCOMMON_API bool ParseJobId(const FString& Text, FGuid& OutJobId);

	/** Finds the first actor tag starting with Prefix (case-insensitive) and returns the remainder, e.g. "TwinBLD.OSM=" -> "way/123". */
	BLDTOOLSETCOMMON_API bool FindTagValue(const AActor* Actor, const FString& Prefix, FString& OutValue);

	/** True when any actor tag starts with Prefix (case-insensitive). */
	BLDTOOLSETCOMMON_API bool HasTagWithPrefix(const AActor* Actor, const FString& Prefix);
}
