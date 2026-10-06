// Copyright WorldBLD LLC. All rights reserved.

#include "Common/RoadBLDToolsetUtils.h"

#include "Authorization/RoadBLDAuthGate.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Components/SplineComponent.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "DynamicRoad/EdgeCurve.h"
#include "Editor.h"
#include "Engine/Blueprint.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "EngineUtils.h"
#include "Interfaces/IPluginManager.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/App.h"
#include "CoreGlobals.h"
#include "Misc/CoreMisc.h"
#include "Containers/Ticker.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "RoadControlSplineComponent.h"
#include "RoadEditorUtilityLibrary.h"
#include "RoadGeo.h"
#include "UObject/SoftObjectPath.h"
#include "UObject/UObjectHash.h"

namespace RoadBLDToolset
{
	const TCHAR* GeneratedContentRoot = TEXT("/Game/RoadBLD_Generated");

	namespace
	{
		bool IsExcludedPresetPackage(const FString& PackageName)
		{
			static const TCHAR* ExcludedPackages[] =
			{
				TEXT("/RoadBLD/RoadBLD/Blueprints/Data/RoadKits_System/RP_DefaultRoadPreset"),
				TEXT("/RoadBLD/Blueprints/Data/RoadKits_System/RP_DefaultRoadPreset"),
				TEXT("/TwinBLD/SampleContent/RoadPresets/RP_TwinBLD_Sample_LargeRoad"),
				TEXT("/TwinBLD/SampleContent/RoadPresets/RP_TwinBLD_Sample_SmallRoad"),
			};

			for (const TCHAR* Excluded : ExcludedPackages)
			{
				if (PackageName.Equals(Excluded))
				{
					return true;
				}
			}

			// The asset library button is a UI placeholder, not a drawable road.
			return PackageName.Contains(TEXT("RP_AssetLibraryButton"));
		}

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

		bool ContainsCaseSensitive(const FString& Haystack, const TCHAR* Token)
		{
			return !Haystack.IsEmpty() && Haystack.Contains(Token, ESearchCase::CaseSensitive);
		}
	}

	void RaiseError(const FString& Message)
	{
		UKismetSystemLibrary::RaiseScriptError(FString::Printf(TEXT("RoadBLDToolset: %s"), *Message));
	}

	namespace
	{
		bool bUnattendedSetByToolset = false;
		FDelegateHandle UnattendedSlateResetHandle;

		void ResetUnattended()
		{
			// Leave the flag alone when someone else owns it (commandlets, -unattended, other scripts).
			if (bUnattendedSetByToolset)
			{
				GIsRunningUnattendedScript = false;
				bUnattendedSetByToolset = false;
			}

			if (UnattendedSlateResetHandle.IsValid() && FSlateApplication::IsInitialized())
			{
				FSlateApplication::Get().OnPreTick().Remove(UnattendedSlateResetHandle);
			}
			UnattendedSlateResetHandle.Reset();
		}
	}

	void MarkCurrentCallUnattended()
	{
		if (GIsRunningUnattendedScript)
		{
			return;
		}

		GIsRunningUnattendedScript = true;
		bUnattendedSetByToolset = true;

		// Clear the flag before Slate handles the next frame's input, so user-triggered dialogs are never suppressed,
		// with the core ticker as a fallback when Slate is not running.
		if (FSlateApplication::IsInitialized())
		{
			UnattendedSlateResetHandle = FSlateApplication::Get().OnPreTick().AddLambda([](float)
			{
				ResetUnattended();
			});
		}
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float)
		{
			ResetUnattended();
			return false;
		}), 0.0f);
	}

	UWorld* GetEditorWorld()
	{
		MarkCurrentCallUnattended();
		return GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	}

#if WITH_DEV_AUTOMATION_TESTS
	namespace
	{
		int32 TestAuthorizationDepth = 0;
	}

	FScopedTestAuthorization::FScopedTestAuthorization()
	{
		check(IsInGameThread());
		++TestAuthorizationDepth;
	}

	FScopedTestAuthorization::~FScopedTestAuthorization()
	{
		check(IsInGameThread());
		--TestAuthorizationDepth;
	}
#endif

	bool CheckAuthorized(FString& OutError)
	{
		MarkCurrentCallUnattended();
		OutError.Reset();

#if WITH_DEV_AUTOMATION_TESTS
		// Only the toolset's own specs may bypass the gate; a test run started by anyone else does not.
		if (GIsAutomationTesting && TestAuthorizationDepth > 0 && IsInGameThread())
		{
			return true;
		}
#endif

		FText AccessError;
		if (RoadBLDAuthGate::AllowEdits(AccessError))
		{
			return true;
		}

		OutError = AccessError.IsEmpty() ? FString(TEXT("RoadBLD edits are blocked.")) : AccessError.ToString();
		return false;
	}

	bool EnsureAuthorized()
	{
		FString Error;
		if (CheckAuthorized(Error))
		{
			return true;
		}

		RaiseError(Error);
		return false;
	}

	FRoadBLDActorRef MakeActorRef(const AActor* Actor)
	{
		FRoadBLDActorRef Ref;
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

	FString GetObjectPath(const UObject* Object)
	{
		return IsValid(Object) ? Object->GetPathName() : FString();
	}

	TArray<FString> SplitCommaList(const FString& List)
	{
		TArray<FString> Parts;
		List.ParseIntoArray(Parts, TEXT(","), true);
		for (FString& Part : Parts)
		{
			Part.TrimStartAndEndInline();
		}
		Parts.RemoveAll([](const FString& Part) { return Part.IsEmpty(); });
		return Parts;
	}

	FString GetOptionalString(const FString& Value, const TCHAR* UnsetWord)
	{
		FString Trimmed = Value.TrimStartAndEnd();
		return Trimmed.Equals(UnsetWord, ESearchCase::IgnoreCase) ? FString() : Trimmed;
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

	ERoadSide ToRoadSide(const ERoadBLDSide Side)
	{
		return Side == ERoadBLDSide::Left ? ERoadSide::Left : ERoadSide::Right;
	}

	TArray<ADynamicRoadNetwork*> GetNetworks()
	{
		TArray<ADynamicRoadNetwork*> Networks = URoadEditorFunctionLibrary::GetAllRoadNetworksInLevel();
		Networks.RemoveAll([](const ADynamicRoadNetwork* Network) { return !IsValid(Network); });
		return Networks;
	}

	ADynamicRoadNetwork* GetOwningNetwork(ADynamicRoad* Road)
	{
		return IsValid(Road) ? URoadEditorFunctionLibrary::FindRoadNetworkForRoad(Road) : nullptr;
	}

	ADynamicRoadNetwork* SpawnNetwork(const FString& Label, FString& OutError)
	{
		UWorld* World = GetEditorWorld();
		if (!World)
		{
			OutError = TEXT("No editor world is available.");
			return nullptr;
		}

		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ADynamicRoadNetwork* Network = World->SpawnActor<ADynamicRoadNetwork>(
			ADynamicRoadNetwork::StaticClass(), FTransform::Identity, SpawnParams);
		if (!IsValid(Network))
		{
			OutError = TEXT("Failed to spawn a road network actor.");
			return nullptr;
		}

		Network->SetActorLabel(Label.IsEmpty() ? TEXT("RoadNetwork") : Label);
		return Network;
	}

	ADynamicRoadNetwork* ResolveNetwork(
		ADynamicRoadNetwork* Requested,
		const bool bCreateIfMissing,
		bool& bOutCreated,
		FString& OutError)
	{
		bOutCreated = false;
		if (IsValid(Requested))
		{
			return Requested;
		}

		const TArray<ADynamicRoadNetwork*> Networks = GetNetworks();
		if (Networks.Num() == 1)
		{
			return Networks[0];
		}

		if (Networks.Num() > 1)
		{
			OutError = FString::Printf(
				TEXT("The level has %d road networks; pass Network explicitly (see DescribeNetwork)."),
				Networks.Num());
			return nullptr;
		}

		if (!bCreateIfMissing)
		{
			OutError = TEXT("The level has no road network. Create one with CreateNetwork or CreateRoad.");
			return nullptr;
		}

		ADynamicRoadNetwork* Network = SpawnNetwork(TEXT("RoadNetwork"), OutError);
		bOutCreated = IsValid(Network);
		return Network;
	}

	UObject* LoadObjectFromPath(const FString& InPath, UClass* ExpectedClass, FString& OutError)
	{
		FString Path = InPath.TrimStartAndEnd();

		// Accept export text such as Material'/Game/Foo.Foo'.
		int32 QuoteIndex = INDEX_NONE;
		if (Path.FindChar(TEXT('\''), QuoteIndex) && Path.EndsWith(TEXT("'")))
		{
			Path = Path.Mid(QuoteIndex + 1, Path.Len() - QuoteIndex - 2);
		}

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
		FString Path = InPath.TrimStartAndEnd();
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

		const TArray<FName> Roots = GetContentRoots();

		TSet<FTopLevelAssetPath> DerivedClassPaths;
		AssetRegistry.GetDerivedClassNames({ BaseClass->GetClassPathName() }, {}, DerivedClassPaths);
		TSet<FName> DerivedClassNames;
		for (const FTopLevelAssetPath& ClassPath : DerivedClassPaths)
		{
			DerivedClassNames.Add(ClassPath.GetAssetName());
		}

		FARFilter Filter;
		Filter.PackagePaths = Roots;
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

	TArray<TSubclassOf<UDynamicRoadDrawPreset>> DiscoverPresetClasses()
	{
		TArray<TSubclassOf<UDynamicRoadDrawPreset>> Presets;
		for (UClass* Class : DiscoverClasses(UDynamicRoadDrawPreset::StaticClass()))
		{
			if (!IsExcludedPresetPackage(Class->GetOutermost()->GetName()))
			{
				Presets.Add(Class);
			}
		}

		Presets.Sort([](const TSubclassOf<UDynamicRoadDrawPreset>& A, const TSubclassOf<UDynamicRoadDrawPreset>& B)
		{
			return A->GetName() < B->GetName();
		});
		return Presets;
	}

	FString ResolvePresetRegion(const UClass* PresetClass)
	{
		const UDynamicRoadDrawPreset* Preset = IsValid(PresetClass)
			? PresetClass->GetDefaultObject<UDynamicRoadDrawPreset>()
			: nullptr;
		if (!Preset)
		{
			return TEXT("Unspecified");
		}

		if (!Preset->Region.IsNone())
		{
			return Preset->Region.ToString();
		}

		// Mirrors the RoadBLD toolbar fallback for presets authored before the Region field existed.
		const FString PresetName = Preset->PresetName.ToString();
		const FString ClassName = PresetClass->GetName();
		const FString PackageName = PresetClass->GetOutermost()->GetName();
		for (const TCHAR* Token : { TEXT("USA"), TEXT("UK") })
		{
			if (ContainsCaseSensitive(PresetName, Token)
				|| ContainsCaseSensitive(ClassName, Token)
				|| ContainsCaseSensitive(PackageName, Token))
			{
				return Token;
			}
		}

		return TEXT("Unspecified");
	}

	FRoadBLDPresetTraits ComputePresetTraits(const UDynamicRoadDrawPreset* Preset)
	{
		FRoadBLDPresetTraits Traits;
		if (!Preset)
		{
			return Traits;
		}

		auto AccumulateLanes = [&Traits](const TArray<FDynamicRoadLaneProfile>& Lanes, int32& DrivingLanes)
		{
			for (const FDynamicRoadLaneProfile& Lane : Lanes)
			{
				Traits.TotalLaneWidth += Lane.Width;
				switch (Lane.Type)
				{
				case ELaneType::Normal:
					++DrivingLanes;
					break;
				case ELaneType::Parking:
					Traits.bHasParking = true;
					break;
				case ELaneType::Restricted:
					Traits.bHasRestrictedLane = true;
					break;
				case ELaneType::Shoulder:
					Traits.bHasShoulder = true;
					break;
				case ELaneType::CenterTurn:
					Traits.bHasCenterTurnLane = true;
					break;
				case ELaneType::Median:
					Traits.bHasMedian = true;
					break;
				default:
					break;
				}
			}
		};

		AccumulateLanes(Preset->LeftLanes, Traits.LeftDrivingLanes);
		AccumulateLanes(Preset->RightLanes, Traits.RightDrivingLanes);
		Traits.bOneWay = (Traits.LeftDrivingLanes == 0) != (Traits.RightDrivingLanes == 0);
		Traits.bHasLeftSidewalk = Preset->LeftSidewalkPresetClass != nullptr;
		Traits.bHasRightSidewalk = Preset->RightSidewalkPresetClass != nullptr;
		return Traits;
	}

	TArray<FString> ComputeDerivedPresetTags(const UDynamicRoadDrawPreset* Preset, const FRoadBLDPresetTraits& Traits)
	{
		TArray<FString> Tags;
		if (!Preset)
		{
			return Tags;
		}

		Tags.Add(EnumToString(Preset->Category).ToLower());
		Tags.Add(Traits.bOneWay ? TEXT("one-way") : TEXT("two-way"));
		Tags.Add(FString::Printf(TEXT("%d-lane"), Traits.LeftDrivingLanes + Traits.RightDrivingLanes));
		if (Traits.bHasMedian)
		{
			Tags.Add(TEXT("median"));
		}
		if (Traits.bHasCenterTurnLane)
		{
			Tags.Add(TEXT("center-turn"));
		}
		if (Traits.bHasParking)
		{
			Tags.Add(TEXT("parking"));
		}
		if (Traits.bHasShoulder)
		{
			Tags.Add(TEXT("shoulder"));
		}
		if (Traits.bHasRestrictedLane)
		{
			Tags.Add(TEXT("restricted-lane"));
		}
		Tags.Add((Traits.bHasLeftSidewalk || Traits.bHasRightSidewalk) ? TEXT("sidewalks") : TEXT("no-sidewalks"));
		return Tags;
	}

	FRoadBLDPresetSummary MakePresetSummary(const UClass* PresetClass)
	{
		FRoadBLDPresetSummary Summary;
		const UDynamicRoadDrawPreset* Preset = IsValid(PresetClass)
			? PresetClass->GetDefaultObject<UDynamicRoadDrawPreset>()
			: nullptr;
		if (!Preset)
		{
			return Summary;
		}

		Summary.Id = PresetClass->GetPathName();
		Summary.AssetPath = PresetClass->GetOutermost()->GetName();
		Summary.Name = Preset->PresetName.IsNone() ? PresetClass->GetName() : Preset->PresetName.ToString();
		Summary.Region = ResolvePresetRegion(PresetClass);
		Summary.Category = EnumToString(Preset->Category);
		Summary.Tags = Preset->Tags;
		Summary.Description = Preset->Description;
		Summary.Traits = ComputePresetTraits(Preset);
		Summary.DerivedTags = ComputeDerivedPresetTags(Preset, Summary.Traits);
		Summary.bIsGenerated = IsGeneratedAsset(PresetClass);
		return Summary;
	}

	bool IsGeneratedAsset(const UObject* Object)
	{
		return IsValid(Object)
			&& Object->GetOutermost()->GetName().StartsWith(FString(GeneratedContentRoot) + TEXT("/"));
	}

	const TArray<FReferenceKitAsset>& GetReferenceKitAssets()
	{
		// Keep in sync with the URoadBLDPresetToolset class description; the schema test checks both.
		static const TArray<FReferenceKitAsset> Assets =
		{
			// Road presets
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Street_2Lane"), TEXT("Sample preset: two-lane city street. General starting point for urban styles.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Street_3Lane_1Way"), TEXT("Sample preset: three-lane one-way city street.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Boulevard_4Lane_CenterTurns"), TEXT("Sample preset: four-lane boulevard with center turn lanes.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Freeway_2Lane"), TEXT("Sample preset: two-lane freeway.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Freeway_3Lane"), TEXT("Sample preset: three-lane freeway.") },

			// Sidewalks, crossings and lanes
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/Sidewalks/RSP_USA_StandardSidewalk"), TEXT("Sample sidewalk preset (USA kit).") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/RSP_Sample_ConcreteSidewalk"), TEXT("Sample concrete sidewalk preset.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/Crossings/CP_USA_ParallelCrosswalk"), TEXT("Sample crossing style: parallel-line crosswalk.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/CP_SampleCrossing"), TEXT("Sample crossing style.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/Lanes/Lane_NormalDriving"), TEXT("Sample lane preset: normal driving lane.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/Lanes/Lane_BikeLane"), TEXT("Sample lane preset: bike lane.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/Lanes/Lane_Restricted"), TEXT("Sample lane preset: restricted lane.") },

			// Road modules
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_USA_Curb"), TEXT("Sample road module: curb. Use as a sidewalk CurbClass.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_USA_Gutter"), TEXT("Sample road module: gutter.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_USA_Guardrail"), TEXT("Sample road module: guardrail.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_HighwaySupport"), TEXT("Sample road module: highway support.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_HighwaySupport_Wide"), TEXT("Sample road module: wide highway support.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_Photoreal_ProceduralBridgeBarrier"), TEXT("Sample road module: procedural bridge barrier.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/RM_Sample_Curb"), TEXT("Sample road module: curb.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/RM_Sample_StreetLights"), TEXT("Sample road module: street lights.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/RM_Sample_Bridge"), TEXT("Sample road module: bridge.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/RM_Sample_ProceduralBridge"), TEXT("Sample road module: procedural bridge.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/RoadBLDSampleKit/Roads/RoadPresets/RM_Sample_HighwaySupport"), TEXT("Sample road module: highway support.") },

			// PCG graphs
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/PCG/PCG_USA_CityStreet"), TEXT("Sample PCG graph for city streets (spec field RoadPCGGraph).") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/PCG/PCG_USA_Freeway"), TEXT("Sample PCG graph for freeways (spec field RoadPCGGraph).") },

			// Master materials
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Asphalt_Master"), TEXT("Master material for road and intersection surfaces. Create variants for RoadMaterial/IntersectionMaterial.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Sidewalk_Master"), TEXT("Master material for sidewalks. Create variants for sidewalk Material/CornerMaterial.") },
			{ TEXT("/RoadBLD/RoadBLD/Materials/M_LaneDecal_Master"), TEXT("Master material for lane markings and decals.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_EdgeDetail_Master"), TEXT("Master material for road edge-detail strips.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Abutment_Master"), TEXT("Master material for bridge abutments.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_TireWear_Master"), TEXT("Master material for tire wear overlays.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Materials/Kit_Freeway_A_Master"), TEXT("USA kit freeway master material.") },

			// Sample material instances
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/Materials/MI_RoadBLD_Asphalt_Road"), TEXT("Sample road surface material instance: asphalt.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/Materials/MI_RoadBLD_Asphalt_Road_Worn"), TEXT("Sample road surface material instance: worn asphalt.") },
			{ TEXT("/RoadBLD/RoadBLD/DefaultRoadKit/Materials/MI_RoadBLD_Default_Abutment"), TEXT("Sample abutment material instance.") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_USA_Sidewalk"), TEXT("Sample sidewalk material instance (USA kit).") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_USA_Sidewalk_WS"), TEXT("Sample world-space sidewalk material instance (USA kit).") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_USA_Concrete_WS"), TEXT("Sample world-space concrete material instance (USA kit).") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_USA_Curb"), TEXT("Sample curb material instance (USA kit).") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_USA_Gutter"), TEXT("Sample gutter material instance (USA kit).") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_HardnedTar"), TEXT("Sample hardened tar material instance (USA kit).") },
			{ TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_RuralRoad_EdgeDetail"), TEXT("Sample rural road edge-detail material instance (USA kit).") },
		};
		return Assets;
	}

	const FReferenceKitAsset* FindReferenceKitAsset(const FString& PackagePath)
	{
		return GetReferenceKitAssets().FindByPredicate([&PackagePath](const FReferenceKitAsset& Asset)
		{
			return PackagePath.Equals(Asset.PackagePath);
		});
	}

	bool GetEndpointLocation(const ADynamicRoad* Road, const bool bStart, FVector& OutLocation)
	{
		if (!IsValid(Road) || !IsValid(Road->ControlSpline))
		{
			return false;
		}

		const int32 NumPoints = Road->ControlSpline->GetNumberOfSplinePoints();
		if (NumPoints < 1)
		{
			return false;
		}

		OutLocation = Road->ControlSpline->GetLocationAtSplinePoint(bStart ? 0 : NumPoints - 1, ESplineCoordinateSpace::World);
		return true;
	}

	bool GetEndpointOutwardDirection(const ADynamicRoad* Road, const bool bStart, FVector& OutDirection)
	{
		if (!IsValid(Road) || !IsValid(Road->ControlSpline))
		{
			return false;
		}

		const int32 NumPoints = Road->ControlSpline->GetNumberOfSplinePoints();
		if (NumPoints < 2)
		{
			return false;
		}

		const int32 EndIndex = bStart ? 0 : NumPoints - 1;
		const int32 NeighborIndex = bStart ? 1 : NumPoints - 2;
		const FVector EndLocation = Road->ControlSpline->GetLocationAtSplinePoint(EndIndex, ESplineCoordinateSpace::World);
		const FVector NeighborLocation = Road->ControlSpline->GetLocationAtSplinePoint(NeighborIndex, ESplineCoordinateSpace::World);

		OutDirection = (EndLocation - NeighborLocation).GetSafeNormal2D();
		return !OutDirection.IsNearlyZero();
	}

	int32 CountEndpointLinks(const ADynamicRoad* Road, const bool bStart)
	{
		if (!IsValid(Road))
		{
			return 0;
		}

		const TArray<FRoadEndpointLink>* Links = Road->GetEndpointLinks(bStart);
		return Links ? Links->Num() : 0;
	}

	FRoadBLDEndpointInfo MakeEndpointInfo(ADynamicRoad* Road, const bool bStart)
	{
		FRoadBLDEndpointInfo Info;
		Info.Road = MakeActorRef(Road);
		Info.bStart = bStart;
		GetEndpointLocation(Road, bStart, Info.Location);
		GetEndpointOutwardDirection(Road, bStart, Info.OutwardDirection);

		if (const TArray<FRoadEndpointLink>* Links = IsValid(Road) ? Road->GetEndpointLinks(bStart) : nullptr)
		{
			for (const FRoadEndpointLink& Link : *Links)
			{
				FRoadBLDLinkInfo& LinkInfo = Info.Links.AddDefaulted_GetRef();
				LinkInfo.Road = MakeActorRef(Link.LinkedRoad.Get());
				LinkInfo.bLinkedToStart = Link.bLinkedToFirstPoint;
				LinkInfo.RightAxisOffset = Link.RightAxisOffset;
			}
		}

		return Info;
	}

	bool CanLinkEndpoints(ADynamicRoad* RoadA, const bool bAStart, ADynamicRoad* RoadB, const bool bBStart, FString& OutReason)
	{
		if (!IsValid(RoadA) || !IsValid(RoadB))
		{
			OutReason = TEXT("Both endpoints must reference valid roads.");
			return false;
		}

		if (RoadA == RoadB)
		{
			OutReason = TEXT("Endpoint links require two different roads.");
			return false;
		}

		if (GetOwningNetwork(RoadA) != GetOwningNetwork(RoadB))
		{
			OutReason = TEXT("Both roads must belong to the same road network.");
			return false;
		}

		if (CountEndpointLinks(RoadA, bAStart) > 0 || CountEndpointLinks(RoadB, bBStart) > 0)
		{
			OutReason = TEXT("Endpoint links are one-to-one and one of the endpoints is already linked.");
			return false;
		}

		return true;
	}

	bool CreateReciprocalLink(ADynamicRoad* RoadA, const bool bAStart, ADynamicRoad* RoadB, const bool bBStart)
	{
		FString Reason;
		FVector LocationA;
		if (!CanLinkEndpoints(RoadA, bAStart, RoadB, bBStart, Reason) || !GetEndpointLocation(RoadA, bAStart, LocationA))
		{
			return false;
		}

		const double RightAxisOffset = ADynamicRoad::CalculateRightAxisOffset(RoadB, bBStart, LocationA);

		FRoadEndpointLink LinkToB;
		LinkToB.LinkedRoad = RoadB;
		LinkToB.bLinkedToFirstPoint = bBStart;
		LinkToB.RightAxisOffset = RightAxisOffset;
		RoadA->AddEndpointLink(bAStart, LinkToB);

		FRoadEndpointLink LinkToA;
		LinkToA.LinkedRoad = RoadA;
		LinkToA.bLinkedToFirstPoint = bAStart;
		LinkToA.RightAxisOffset = -RightAxisOffset;
		RoadB->AddEndpointLink(bBStart, LinkToA);

		return CountEndpointLinks(RoadA, bAStart) == 1 && CountEndpointLinks(RoadB, bBStart) == 1;
	}

	EEndpointMeeting ClassifyEndpointDirections(const FVector& OutwardA, const FVector& OutwardB, double& OutTurnAngle)
	{
		// Driving out of A continues along -OutwardB on the other road.
		const double Cosine = FMath::Clamp(FVector::DotProduct(OutwardA.GetSafeNormal2D(), -OutwardB.GetSafeNormal2D()), -1.0, 1.0);
		OutTurnAngle = FMath::RadiansToDegrees(FMath::Acos(Cosine));
		return OutTurnAngle <= ContinuationMaxAngle ? EEndpointMeeting::Continuation : EEndpointMeeting::Corner;
	}

	bool ClassifyEndpointMeeting(
		const ADynamicRoad* RoadA,
		const bool bStartA,
		const ADynamicRoad* RoadB,
		const bool bStartB,
		EEndpointMeeting& OutMeeting,
		double& OutTurnAngle)
	{
		FVector OutwardA;
		FVector OutwardB;
		if (!GetEndpointOutwardDirection(RoadA, bStartA, OutwardA) || !GetEndpointOutwardDirection(RoadB, bStartB, OutwardB))
		{
			return false;
		}

		OutMeeting = ClassifyEndpointDirections(OutwardA, OutwardB, OutTurnAngle);
		return true;
	}

	bool AreEndpointsLinked(const ADynamicRoad* Road, const bool bStart, const ADynamicRoad* OtherRoad, const bool bOtherStart)
	{
		const TArray<FRoadEndpointLink>* Links = IsValid(Road) ? Road->GetEndpointLinks(bStart) : nullptr;
		return Links && Links->ContainsByPredicate([OtherRoad, bOtherStart](const FRoadEndpointLink& Link)
		{
			return Link.LinkedRoad.Get() == OtherRoad && Link.bLinkedToFirstPoint == bOtherStart;
		});
	}

	TArray<FEndpointCorner> FindCornersAtEnd(ADynamicRoadNetwork* Network, ADynamicRoad* Road, const bool bStart)
	{
		TArray<FEndpointCorner> Corners;
		FVector EndLocation;
		if (!IsValid(Network) || !GetEndpointLocation(Road, bStart, EndLocation))
		{
			return Corners;
		}

		for (const TObjectPtr<ADynamicRoad>& Other : Network->RoadsInNetwork)
		{
			if (!IsValid(Other) || Other.Get() == Road)
			{
				continue;
			}

			for (const bool bOtherStart : { true, false })
			{
				FVector OtherEnd;
				if (!GetEndpointLocation(Other, bOtherStart, OtherEnd) || FVector::Dist2D(OtherEnd, EndLocation) > EndpointMeetTolerance)
				{
					continue;
				}

				EEndpointMeeting Meeting = EEndpointMeeting::Continuation;
				double TurnAngle = 0.0;
				if (ClassifyEndpointMeeting(Road, bStart, Other, bOtherStart, Meeting, TurnAngle) && Meeting == EEndpointMeeting::Corner)
				{
					FEndpointCorner& Corner = Corners.AddDefaulted_GetRef();
					Corner.OtherRoad = Other.Get();
					Corner.bOtherStart = bOtherStart;
					Corner.bLinked = AreEndpointsLinked(Road, bStart, Other, bOtherStart);
					Corner.TurnAngle = TurnAngle;
				}
			}
		}

		return Corners;
	}

	bool FindUnlinkedEndpointNear(
		ADynamicRoadNetwork* Network,
		const FVector& Location,
		const double Tolerance,
		const ADynamicRoad* RoadToIgnore,
		ADynamicRoad*& OutRoad,
		bool& bOutStart)
	{
		OutRoad = nullptr;
		if (!IsValid(Network))
		{
			return false;
		}

		double BestDistanceSquared = FMath::Square(Tolerance);
		for (const TObjectPtr<ADynamicRoad>& Road : Network->RoadsInNetwork)
		{
			if (!IsValid(Road) || Road.Get() == RoadToIgnore)
			{
				continue;
			}

			for (const bool bStart : { true, false })
			{
				FVector EndpointLocation;
				if (CountEndpointLinks(Road, bStart) > 0 || !GetEndpointLocation(Road, bStart, EndpointLocation))
				{
					continue;
				}

				const double DistanceSquared = FVector::DistSquared2D(EndpointLocation, Location);
				if (DistanceSquared <= BestDistanceSquared)
				{
					BestDistanceSquared = DistanceSquared;
					OutRoad = Road.Get();
					bOutStart = bStart;
				}
			}
		}

		return OutRoad != nullptr;
	}

	TArray<UEdgeCurve*> GetSortedSideEdges(const ADynamicRoad* Road, const ERoadSide Side)
	{
		TArray<UEdgeCurve*> Edges;
		if (!IsValid(Road))
		{
			return Edges;
		}

		for (const TObjectPtr<UEdgeCurve>& Edge : Road->EdgeCurves)
		{
			if (IsValid(Edge) && Edge->Side == Side && Edge.Get() != Road->LaneMidpoint.Get())
			{
				Edges.Add(Edge.Get());
			}
		}

		Edges.Sort([](const UEdgeCurve& A, const UEdgeCurve& B)
		{
			return A.BaseOffset < B.BaseOffset;
		});
		return Edges;
	}

	double EvaluateEdgeOffset(const UEdgeCurve* Edge, const double Distance)
	{
		if (!IsValid(Edge))
		{
			return 0.0;
		}

		const TArray<FOffsetPoint>& Points = Edge->OffsetPoints;
		if (Points.Num() == 0)
		{
			return Edge->BaseOffset;
		}

		if (Points.Num() == 1 || Distance <= Points[0].Distance)
		{
			return Points[0].Offset;
		}

		if (Distance >= Points.Last().Distance)
		{
			return Points.Last().Offset;
		}

		int32 UpperIndex = 1;
		while (UpperIndex < Points.Num() && Points[UpperIndex].Distance < Distance)
		{
			++UpperIndex;
		}

		const FOffsetPoint& Start = Points[UpperIndex - 1];
		const FOffsetPoint& End = Points[UpperIndex];
		const double SegmentLength = End.Distance - Start.Distance;
		if (SegmentLength <= UE_SMALL_NUMBER)
		{
			return End.Offset;
		}

		const double Alpha = FMath::Clamp((Distance - Start.Distance) / SegmentLength, 0.0, 1.0);
		const double SmoothAlpha = Alpha * Alpha * (3.0 - 2.0 * Alpha);
		return FMath::Lerp(Start.Offset, End.Offset, SmoothAlpha);
	}

	double GetRoadSideWidth(const ADynamicRoad* Road, const ERoadSide Side, const double Distance)
	{
		double Width = 0.0;
		for (const UEdgeCurve* Edge : GetSortedSideEdges(Road, Side))
		{
			Width = FMath::Max(Width, FMath::Abs(EvaluateEdgeOffset(Edge, Distance)));
		}
		return Width;
	}

	double FindClosestDistanceAlongRoad(const ADynamicRoad* Road, const FVector& Location)
	{
		const double Length = IsValid(Road) ? Road->GetLength() : 0.0;
		if (Length <= 0.0)
		{
			return 0.0;
		}

		auto DistanceSquaredAt = [Road, &Location](const double Distance)
		{
			return FVector::DistSquared2D(Road->GetWorldLocationAtDistanceAlongRoad(Distance), Location);
		};

		const int32 SampleCount = FMath::Clamp(FMath::CeilToInt32(Length / 200.0), 2, 2000);
		const double Step = Length / SampleCount;
		double BestDistance = 0.0;
		double BestDistanceSquared = TNumericLimits<double>::Max();
		for (int32 Index = 0; Index <= SampleCount; ++Index)
		{
			const double Distance = Index * Step;
			const double DistanceSquared = DistanceSquaredAt(Distance);
			if (DistanceSquared < BestDistanceSquared)
			{
				BestDistanceSquared = DistanceSquared;
				BestDistance = Distance;
			}
		}

		double Low = FMath::Max(0.0, BestDistance - Step);
		double High = FMath::Min(Length, BestDistance + Step);
		for (int32 Iteration = 0; Iteration < 24; ++Iteration)
		{
			const double Third = (High - Low) / 3.0;
			if (DistanceSquaredAt(Low + Third) < DistanceSquaredAt(High - Third))
			{
				High -= Third;
			}
			else
			{
				Low += Third;
			}
		}
		return (Low + High) * 0.5;
	}

	bool FindJunctionStub(
		ADynamicRoadNetwork* Network,
		const ADynamicRoad* RoadToIgnore,
		const FVector& EndLocation,
		const FVector& NeighborLocation,
		const double IncomingRoadWidth,
		FJunctionStub& OutStub)
	{
		const FVector Direction = (EndLocation - NeighborLocation).GetSafeNormal2D();
		const double SegmentLength = FVector::Dist2D(EndLocation, NeighborLocation);
		if (!IsValid(Network) || Direction.IsNearlyZero())
		{
			return false;
		}

		for (const TObjectPtr<ADynamicRoad>& Other : Network->RoadsInNetwork)
		{
			if (!IsValid(Other) || Other.Get() == RoadToIgnore)
			{
				continue;
			}

			for (const bool bStart : { true, false })
			{
				FVector OtherEnd;
				if (GetEndpointLocation(Other, bStart, OtherEnd) && FVector::Dist2D(OtherEnd, EndLocation) <= EndpointMeetTolerance)
				{
					// Ends that meet are continuations or corners, not junction arms.
					return false;
				}
			}
		}

		const double MinCrossArm = FMath::Max(JunctionMinCrossArm, IncomingRoadWidth);
		bool bFound = false;
		double BestMove = TNumericLimits<double>::Max();
		for (const TObjectPtr<ADynamicRoad>& Other : Network->RoadsInNetwork)
		{
			if (!IsValid(Other) || Other.Get() == RoadToIgnore || Other->GetLength() <= 0.0)
			{
				continue;
			}

			const FBox Bounds = GetRoadBounds(Other.Get(), false);
			if (!Bounds.IsValid || !Bounds.ExpandBy(MinCrossArm).IsInsideXY(EndLocation))
			{
				continue;
			}

			const double Length = Other->GetLength();
			const double Distance = FindClosestDistanceAlongRoad(Other, EndLocation);
			if (Distance <= 1.0 || Distance >= Length - 1.0)
			{
				// Beyond the other road's own ends: not a T or crossing.
				continue;
			}

			const FVector Center = Other->GetWorldLocationAtDistanceAlongRoad(Distance);
			const FVector Right = Other->GetRightVectorAtDistanceAlongRoad(Distance).GetSafeNormal2D();
			const double Crossing = FVector::DotProduct(Direction, Right);
			if (FMath::Abs(Crossing) < 0.5)
			{
				// Shallow angles merge alongside the other road rather than cross it.
				continue;
			}

			// Distance travelled past the centerline along the incoming direction; widths are measured the same way.
			const double PastCenterline = FVector::DotProduct(EndLocation - Center, Right) / Crossing;
			const double FarWidth = GetRoadSideWidth(Other, Crossing > 0.0 ? ERoadSide::Right : ERoadSide::Left, Distance) / FMath::Abs(Crossing);
			const double NearWidth = GetRoadSideWidth(Other, Crossing > 0.0 ? ERoadSide::Left : ERoadSide::Right, Distance) / FMath::Abs(Crossing);

			const bool bStubPast = PastCenterline >= 0.0 && PastCenterline < FarWidth + MinCrossArm;
			const bool bShort = PastCenterline < 0.0 && PastCenterline >= -(NearWidth + JunctionShortGap);
			const double Move = FMath::Abs(PastCenterline);
			if ((!bStubPast && !bShort) || Move >= BestMove)
			{
				continue;
			}

			if (PastCenterline > 0.0 && Move >= SegmentLength - 100.0)
			{
				// Pulling the end back that far would fold the road over its neighbouring control point.
				continue;
			}

			bFound = true;
			BestMove = Move;
			OutStub.OtherRoad = Other.Get();
			OutStub.SnappedLocation = EndLocation - Direction * PastCenterline;
			OutStub.MoveDistance = Move;
			OutStub.bPastCenterline = PastCenterline > 0.0;
			OutStub.EdgeDistance = bStubPast ? PastCenterline - FarWidth : Move - NearWidth;
		}

		return bFound;
	}

	bool DoesGeoReferenceRoad(const ARoadGeo* Geo, const ADynamicRoad* Road)
	{
		if (!IsValid(Geo) || !IsValid(Road))
		{
			return false;
		}

		return Geo->SourceRoads.ContainsByPredicate([Road](const TSoftObjectPtr<ADynamicRoad>& SourceRoad)
		{
			return SourceRoad.Get() == Road;
		});
	}

	FBox GetRoadBounds(ADynamicRoad* Road, const bool bIncludeGeneratedGeometry)
	{
		FBox Bounds(ForceInit);
		if (!IsValid(Road) || !IsValid(Road->ControlSpline))
		{
			return Bounds;
		}

		for (int32 Index = 0; Index < Road->ControlSpline->GetNumberOfSplinePoints(); ++Index)
		{
			Bounds += Road->ControlSpline->GetLocationAtSplinePoint(Index, ESplineCoordinateSpace::World);
		}

		double MaxOffset = 0.0;
		for (const TObjectPtr<UEdgeCurve>& Edge : Road->EdgeCurves)
		{
			if (IsValid(Edge))
			{
				MaxOffset = FMath::Max(MaxOffset, Edge->BaseOffset);
			}
		}

		if (Bounds.IsValid)
		{
			// Curves between control points bulge outward; pad generously so framing never clips the road.
			Bounds = Bounds.ExpandBy(FVector(MaxOffset + 1500.0, MaxOffset + 1500.0, 300.0));
		}

		if (bIncludeGeneratedGeometry)
		{
			if (UWorld* World = Road->GetWorld())
			{
				for (TActorIterator<ARoadGeo> It(World); It; ++It)
				{
					if (DoesGeoReferenceRoad(*It, Road))
					{
						const FBox GeoBounds = It->GetComponentsBoundingBox(true);
						if (GeoBounds.IsValid)
						{
							Bounds += GeoBounds;
						}
					}
				}
			}
		}

		return Bounds;
	}

	FBox GetNetworkBounds(ADynamicRoadNetwork* Network, const bool bIncludeGeneratedGeometry)
	{
		FBox Bounds(ForceInit);
		if (!IsValid(Network))
		{
			return Bounds;
		}

		for (const TObjectPtr<ADynamicRoad>& Road : Network->RoadsInNetwork)
		{
			const FBox RoadBounds = GetRoadBounds(Road.Get(), bIncludeGeneratedGeometry);
			if (RoadBounds.IsValid)
			{
				Bounds += RoadBounds;
			}
		}
		return Bounds;
	}

	TArray<ARoadGeo*> GetJunctionGeos(const ADynamicRoadNetwork* Network)
	{
		return GetNetworkGeos(Network, 2);
	}

	TArray<ARoadGeo*> GetNetworkGeos(const ADynamicRoadNetwork* Network, const int32 MinSourceRoads)
	{
		TArray<ARoadGeo*> Geos;
		UWorld* World = IsValid(Network) ? Network->GetWorld() : nullptr;
		if (!World)
		{
			return Geos;
		}

		TSet<const ADynamicRoad*> NetworkRoads;
		for (const TObjectPtr<ADynamicRoad>& Road : Network->RoadsInNetwork)
		{
			if (IsValid(Road))
			{
				NetworkRoads.Add(Road.Get());
			}
		}

		for (TActorIterator<ARoadGeo> It(World); It; ++It)
		{
			ARoadGeo* Geo = *It;
			if (!IsValid(Geo) || Geo->SourceRoads.Num() < MinSourceRoads)
			{
				continue;
			}

			const bool bBelongsToNetwork = Geo->SourceRoads.ContainsByPredicate(
				[&NetworkRoads](const TSoftObjectPtr<ADynamicRoad>& SourceRoad)
				{
					return NetworkRoads.Contains(SourceRoad.Get());
				});
			if (bBelongsToNetwork)
			{
				Geos.Add(Geo);
			}
		}

		return Geos;
	}
}
