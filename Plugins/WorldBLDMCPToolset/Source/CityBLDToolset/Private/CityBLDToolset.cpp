// Copyright WorldBLD LLC. All rights reserved.

#include "CityBLDToolset.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "BLDToolsetUtils.h"
#include "CityBlock.h"
#include "CityBLDTypes.h"
#include "Common/CityBLDToolsetUtils.h"
#include "Engine/Blueprint.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "ModularBuildingActor.h"
#include "ScopedTransaction.h"
#include "UObject/SoftObjectPath.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(CityBLDToolset)

namespace CityBLDToolsetPrivate
{
	const TCHAR* ToolsetName = TEXT("CityBLDToolset");

	void RaiseError(const FString& Message)
	{
		BLDToolset::RaiseError(ToolsetName, Message);
	}

	FCityBLDActorRef MakeActorRef(const AActor* Actor)
	{
		const FBLDActorRef Shared = BLDToolset::MakeActorRef(Actor);

		FCityBLDActorRef Ref;
		Ref.Name = Shared.Name;
		Ref.Label = Shared.Label;
		Ref.RefPath = Shared.RefPath;
		Ref.Class = Shared.Class;
		return Ref;
	}

	FCityBLDBuildingInfo MakeBuildingInfo(AModularBuildingActor* Building)
	{
		FCityBLDBuildingInfo Info;
		if (!IsValid(Building))
		{
			return Info;
		}

		Info.Actor = MakeActorRef(Building);
		if (UClass* StyleClass = Building->Style.Get())
		{
			Info.StyleClassPath = StyleClass->GetPathName();
		}
		Info.BuildingHeight = Building->BuildingHeight;
		Info.FloorHeights = Building->FloorHeights;
		Info.FootprintVertexCount = Building->ShapePoints.Num();
		Info.Location = Building->GetActorLocation();
		Info.bAllFloorsFacade = Building->bAllFloorsFacade;
		Info.bPreciseHeight = Building->bPreciseHeight;
		Info.bTwinBLDUpperFloorsPreferFacade = Building->bTwinBLDUpperFloorsPreferFacade;
		return Info;
	}

	FCityBLDBlockInfo MakeBlockInfo(ACityBlock* Block)
	{
		FCityBLDBlockInfo Info;
		if (!IsValid(Block))
		{
			return Info;
		}

		Info.Actor = MakeActorRef(Block);
		Info.ParcelCount = Block->Parcels.Num();
		Info.SidewalkWidth = Block->SidewalkWidth;
		if (UClass* DistrictClass = Block->DistrictClass.Get())
		{
			Info.DistrictClassPath = DistrictClass->GetPathName();
		}
		return Info;
	}
}

TArray<FCityBLDBuildingInfo> UCityBLDToolset::ListModularBuildings()
{
	TArray<FCityBLDBuildingInfo> Infos;
	UWorld* World = CityBLDToolsetUtils::GetEditorWorldOrRaise(CityBLDToolsetPrivate::ToolsetName);
	if (!World)
	{
		return Infos;
	}

	for (AModularBuildingActor* Building : CityBLDToolsetUtils::GetBuildings(World))
	{
		Infos.Add(CityBLDToolsetPrivate::MakeBuildingInfo(Building));
	}
	return Infos;
}

FCityBLDBuildingInfo UCityBLDToolset::DescribeBuilding(AModularBuildingActor* Building)
{
	if (!IsValid(Building))
	{
		CityBLDToolsetPrivate::RaiseError(TEXT("Building is required."));
		return FCityBLDBuildingInfo();
	}

	return CityBLDToolsetPrivate::MakeBuildingInfo(Building);
}

TArray<FCityBLDBlockInfo> UCityBLDToolset::ListCityBlocks()
{
	TArray<FCityBLDBlockInfo> Infos;
	UWorld* World = CityBLDToolsetUtils::GetEditorWorldOrRaise(CityBLDToolsetPrivate::ToolsetName);
	if (!World)
	{
		return Infos;
	}

	for (ACityBlock* Block : CityBLDToolsetUtils::GetBlocks(World))
	{
		Infos.Add(CityBLDToolsetPrivate::MakeBlockInfo(Block));
	}
	return Infos;
}

TArray<FCityBLDBuildingStyleInfo> UCityBLDToolset::ListBuildingStyles()
{
	TArray<FCityBLDBuildingStyleInfo> Infos;

	const IAssetRegistry& AssetRegistry =
		FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();

	FARFilter Filter;
	Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
	Filter.bRecursiveClasses = true;

	TArray<FAssetData> Assets;
	AssetRegistry.GetAssets(Filter, Assets);

	for (const FAssetData& AssetData : Assets)
	{
		FString NativeParentClassPath;
		if (!AssetData.GetTagValue(FBlueprintTags::NativeParentClassPath, NativeParentClassPath))
		{
			continue;
		}

		const UClass* NativeParentClass = FSoftClassPath(NativeParentClassPath).ResolveClass();
		if (!NativeParentClass || !NativeParentClass->IsChildOf(UBuildingStyle::StaticClass()))
		{
			continue;
		}

		FCityBLDBuildingStyleInfo Info;
		Info.AssetPath = AssetData.GetObjectPathString();

		FString GeneratedClassPath;
		if (AssetData.GetTagValue(FBlueprintTags::GeneratedClassPath, GeneratedClassPath) && !GeneratedClassPath.IsEmpty())
		{
			Info.ClassPath = FSoftClassPath(GeneratedClassPath).ToString();
		}
		else
		{
			Info.ClassPath = AssetData.GetObjectPathString() + TEXT("_C");
		}

		Infos.Add(MoveTemp(Info));
	}

	Infos.Sort([](const FCityBLDBuildingStyleInfo& A, const FCityBLDBuildingStyleInfo& B)
	{
		return A.AssetPath < B.AssetPath;
	});
	return Infos;
}

bool UCityBLDToolset::SetBuildingStyle(AModularBuildingActor* Building, TSubclassOf<UBuildingStyle> StyleClass)
{
	if (!IsValid(Building))
	{
		CityBLDToolsetPrivate::RaiseError(TEXT("Building is required."));
		return false;
	}

	if (!StyleClass)
	{
		CityBLDToolsetPrivate::RaiseError(TEXT("StyleClass is required."));
		return false;
	}

	if (!CityBLDToolsetUtils::EnsureAuthorizedOrRaise(CityBLDToolsetPrivate::ToolsetName))
	{
		return false;
	}

	FScopedTransaction Transaction(NSLOCTEXT("CityBLDToolset", "SetBuildingStyle", "Set Building Style"));
	Building->Modify();
	Building->Style = StyleClass;
	return true;
}

bool UCityBLDToolset::GenerateBuilding(AModularBuildingActor* Building)
{
	if (!IsValid(Building))
	{
		CityBLDToolsetPrivate::RaiseError(TEXT("Building is required."));
		return false;
	}

	if (!CityBLDToolsetUtils::EnsureAuthorizedOrRaise(CityBLDToolsetPrivate::ToolsetName))
	{
		return false;
	}

	FScopedTransaction Transaction(NSLOCTEXT("CityBLDToolset", "GenerateBuilding", "Generate Modular Building"));
	Building->Modify();
	Building->GenerateModularBuilding();
	return true;
}
