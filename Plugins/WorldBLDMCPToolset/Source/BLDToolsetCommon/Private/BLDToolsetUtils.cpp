// Copyright WorldBLD LLC. All rights reserved.

#include "BLDToolsetUtils.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Containers/Ticker.h"
#include "Editor.h"
#include "Engine/Blueprint.h"
#include "Engine/World.h"
#include "Misc/App.h"
#include "CoreGlobals.h"
#include "Misc/CoreMisc.h"
#include "GameFramework/Actor.h"
#include "Interfaces/IPluginManager.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "UObject/SoftObjectPath.h"
#include "UObject/UObjectHash.h"

namespace BLDToolset
{
	namespace
	{
		FString GetGeneratedClassPath(const FAssetData& AssetData)
		{
			FString ClassPath = AssetData.GetTagValueRef<FString>(FBlueprintTags::GeneratedClassPath);
			if (ClassPath.IsEmpty())
			{
				ClassPath = AssetData.GetTagValueRef<FString>(FName(TEXT("GeneratedClass")));
			}
			return ClassPath;
		}

		bool IsUsableClass(const UClass* Class, const UClass* BaseClass)
		{
			return IsValid(Class)
				&& Class != BaseClass
				&& Class->IsChildOf(BaseClass)
				&& !Class->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_NewerVersionExists)
				&& !Class->GetName().StartsWith(TEXT("SKEL_"))
				&& !Class->GetName().StartsWith(TEXT("REINST_"));
		}

		FString StripExportText(const FString& InPath)
		{
			FString Path = InPath.TrimStartAndEnd();

			// Accept export text such as Material'/Game/Foo.Foo'.
			int32 QuoteIndex = INDEX_NONE;
			if (Path.FindChar(TEXT('\''), QuoteIndex) && Path.EndsWith(TEXT("'")))
			{
				Path = Path.Mid(QuoteIndex + 1, Path.Len() - QuoteIndex - 2);
			}
			return Path;
		}
	}

	void RaiseError(const TCHAR* ToolsetName, const FString& Message)
	{
		UKismetSystemLibrary::RaiseScriptError(FString::Printf(TEXT("%s: %s"), ToolsetName, *Message));
	}

	void MarkCurrentCallUnattended()
	{
		if (GIsRunningUnattendedScript)
		{
			return;
		}

		GIsRunningUnattendedScript = true;
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float)
		{
			GIsRunningUnattendedScript = false;
			return false;
		}), 0.0f);
	}

	UWorld* GetEditorWorld()
	{
		MarkCurrentCallUnattended();
		return GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	}

	FBLDActorRef MakeActorRef(const AActor* Actor)
	{
		FBLDActorRef Ref;
		if (!IsValid(Actor))
		{
			return Ref;
		}

		Ref.Name = Actor->GetName();
		Ref.Label = Actor->GetActorLabel();
		Ref.RefPath = Actor->GetPathName();
		Ref.Class = Actor->GetClass()->GetName();
		return Ref;
	}

	FString SanitizeAssetName(const FString& Name)
	{
		FString Result;
		Result.Reserve(Name.Len());
		for (const TCHAR Character : Name.TrimStartAndEnd())
		{
			if (FChar::IsAlnum(Character))
			{
				Result.AppendChar(Character);
			}
			else if (Character == TEXT('_') || Character == TEXT(' ') || Character == TEXT('-'))
			{
				Result.AppendChar(TEXT('_'));
			}
		}
		return Result.Left(64);
	}

	UObject* LoadObjectFromPath(const FString& InPath, UClass* ExpectedClass, FString& OutError)
	{
		FString Path = StripExportText(InPath);
		if (Path.IsEmpty())
		{
			OutError = TEXT("Asset path is empty.");
			return nullptr;
		}

		if (!Path.StartsWith(TEXT("/")))
		{
			OutError = FString::Printf(TEXT("'%s' is not a content path. Use a path such as /Game/Folder/Asset."), *InPath);
			return nullptr;
		}

		if (!Path.Contains(TEXT(".")))
		{
			Path = Path + TEXT(".") + FPackageName::GetLongPackageAssetName(Path);
		}

		UObject* Object = FSoftObjectPath(Path).TryLoad();
		if (!Object)
		{
			OutError = FString::Printf(TEXT("Asset '%s' was not found."), *InPath);
			return nullptr;
		}

		if (ExpectedClass && !Object->IsA(ExpectedClass))
		{
			OutError = FString::Printf(
				TEXT("Asset '%s' is a %s, expected a %s."),
				*InPath,
				*Object->GetClass()->GetName(),
				*ExpectedClass->GetName());
			return nullptr;
		}

		return Object;
	}

	UClass* LoadClassFromPath(const FString& InPath, UClass* BaseClass, FString& OutError)
	{
		FString Path = StripExportText(InPath);
		if (Path.IsEmpty())
		{
			OutError = TEXT("Class path is empty.");
			return nullptr;
		}

		if (!Path.Contains(TEXT(".")))
		{
			Path = Path + TEXT(".") + FPackageName::GetLongPackageAssetName(Path);
		}

		UObject* Object = FSoftObjectPath(Path).TryLoad();
		if (!Object && !Path.EndsWith(TEXT("_C")))
		{
			Object = FSoftObjectPath(Path + TEXT("_C")).TryLoad();
		}

		UClass* Class = Cast<UClass>(Object);
		if (!Class)
		{
			if (const UBlueprint* Blueprint = Cast<UBlueprint>(Object))
			{
				Class = Blueprint->GeneratedClass;
			}
		}

		if (!Class)
		{
			OutError = FString::Printf(TEXT("Class '%s' was not found."), *InPath);
			return nullptr;
		}

		if (BaseClass && !Class->IsChildOf(BaseClass))
		{
			OutError = FString::Printf(TEXT("Class '%s' is not a %s."), *InPath, *BaseClass->GetName());
			return nullptr;
		}

		return Class;
	}

	TArray<FName> GetContentRoots()
	{
		TArray<FName> Roots;
		Roots.Add(TEXT("/Game"));

		const FString ProjectPluginsDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectPluginsDir());
		for (const TSharedRef<IPlugin>& Plugin : IPluginManager::Get().GetEnabledPlugins())
		{
			if (!Plugin->CanContainContent())
			{
				continue;
			}

			const FString PluginBaseDir = FPaths::ConvertRelativePathToFull(Plugin->GetBaseDir());
			if (!PluginBaseDir.StartsWith(ProjectPluginsDir))
			{
				continue;
			}

			FString MountedAssetPath = Plugin->GetMountedAssetPath();
			MountedAssetPath.RemoveFromEnd(TEXT("/"));
			if (MountedAssetPath.StartsWith(TEXT("/")) && MountedAssetPath.Len() > 1)
			{
				Roots.AddUnique(*MountedAssetPath);
			}
		}

		return Roots;
	}

	TArray<UClass*> DiscoverClasses(UClass* BaseClass)
	{
		TArray<UClass*> Classes;
		if (!BaseClass)
		{
			return Classes;
		}

		TArray<UClass*> DerivedClasses;
		GetDerivedClasses(BaseClass, DerivedClasses, true);
		for (UClass* DerivedClass : DerivedClasses)
		{
			if (IsUsableClass(DerivedClass, BaseClass) && DerivedClass->IsNative())
			{
				Classes.AddUnique(DerivedClass);
			}
		}

		IAssetRegistry& AssetRegistry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
		if (AssetRegistry.IsLoadingAssets())
		{
			AssetRegistry.WaitForCompletion();
		}

		TSet<FTopLevelAssetPath> DerivedClassPaths;
		AssetRegistry.GetDerivedClassNames({ BaseClass->GetClassPathName() }, {}, DerivedClassPaths);
		TSet<FName> DerivedClassNames;
		for (const FTopLevelAssetPath& ClassPath : DerivedClassPaths)
		{
			DerivedClassNames.Add(ClassPath.GetAssetName());
		}

		FARFilter Filter;
		Filter.PackagePaths = GetContentRoots();
		Filter.bRecursivePaths = true;
		Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
		Filter.bRecursiveClasses = true;

		TArray<FAssetData> BlueprintAssets;
		AssetRegistry.GetAssets(Filter, BlueprintAssets);

		for (const FAssetData& AssetData : BlueprintAssets)
		{
			const FString GeneratedClassPath = GetGeneratedClassPath(AssetData);
			if (GeneratedClassPath.IsEmpty())
			{
				continue;
			}

			const FName GeneratedClassName(*FSoftClassPath(GeneratedClassPath).GetAssetName());
			if (!DerivedClassNames.Contains(GeneratedClassName))
			{
				continue;
			}

			UClass* GeneratedClass = Cast<UClass>(FSoftObjectPath(GeneratedClassPath).TryLoad());
			if (IsUsableClass(GeneratedClass, BaseClass))
			{
				Classes.AddUnique(GeneratedClass);
			}
		}

		return Classes;
	}

	bool ParseJobId(const FString& Text, FGuid& OutJobId)
	{
		return FGuid::Parse(Text.TrimStartAndEnd(), OutJobId) && OutJobId.IsValid();
	}

	bool FindTagValue(const AActor* Actor, const FString& Prefix, FString& OutValue)
	{
		if (!IsValid(Actor))
		{
			return false;
		}

		for (const FName& Tag : Actor->Tags)
		{
			const FString TagString = Tag.ToString();
			if (TagString.StartsWith(Prefix, ESearchCase::IgnoreCase))
			{
				OutValue = TagString.RightChop(Prefix.Len());
				return true;
			}
		}
		return false;
	}

	bool HasTagWithPrefix(const AActor* Actor, const FString& Prefix)
	{
		FString Unused;
		return FindTagValue(Actor, Prefix, Unused);
	}
}
