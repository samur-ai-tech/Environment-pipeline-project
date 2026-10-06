// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDRuntime/Classes/WorldBLDStyleBase.h"

UE_DEFINE_GAMEPLAY_TAG(Tag_WorldBLD_Style, TEXT("WorldBLD.Style"));
UE_DEFINE_GAMEPLAY_TAG(Tag_WorldBLD_Style_Street, TEXT("WorldBLD.Style.Street"));
UE_DEFINE_GAMEPLAY_TAG(Tag_WorldBLD_Style_KitRoad, TEXT("WorldBLD.Style.KitRoad"));
UE_DEFINE_GAMEPLAY_TAG(Tag_WorldBLD_Style_KitRoadModule, TEXT("WorldBLD.Style.KitRoadModule"));
UE_DEFINE_GAMEPLAY_TAG(Tag_WorldBLD_Style_RoadPreset, TEXT("WorldBLD.Style.RoadPreset"));

UWorldBLDKitStyleBase::UWorldBLDKitStyleBase()
{
}

UWorldBLDKitPrimaryStyleBase::UWorldBLDKitPrimaryStyleBase()
{
}

UWorldBLDKitSubStyleBase::UWorldBLDKitSubStyleBase()
{
}

void UWorldBLDKitStyleBase::Serialize(FArchive& Ar)
{
	if (Ar.IsSaving() && UniqueId == FGuid())
	{
		MakeUnique(true);
	}

	Super::Serialize(Ar);

	if (Ar.IsLoading() && UniqueId == FGuid())
	{
		MakeUnique(true);
	}
}

FWorldBLDKitStyleReference UWorldBLDKitStyleBase::CreateReference() const
{
	FWorldBLDKitStyleReference Reference;
	Reference.Type = StyleType;
	Reference.Class = GetClass();
	Reference.Name = StyleName;
	Reference.Guid = UniqueId;
	Reference.bIsSubStyle = IsValid(GetOuter()) && GetOuter()->IsA(UWorldBLDKitStyleBase::StaticClass());
	return Reference;
}

UWorldBLDKitStyleBase* UWorldBLDKitStyleBase::Duplicate(UObject* NewOwner, bool bSharedUniqueId) const
{
	UWorldBLDKitStyleBase* Copy = DuplicateObject(this, NewOwner);
	if (Copy && bSharedUniqueId)
	{
		Copy->bIdIsShared = true;
		Copy->UniqueId = UniqueId;
	}
	return Copy;
}

void UWorldBLDKitStyleBase::MakeUnique(bool bForce)
{
	if (bForce || bIdIsShared)
	{
		UniqueId = FGuid::NewGuid();
		bIdIsShared = false;
	}
}
