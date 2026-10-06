// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/RoadBLDPresetToolset.h"

#include "Common/RoadBLDToolsetUtils.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Presets/RoadBLDPresetSpecIO.h"
#include "Toolsets/RoadBLDAuthoringToolset.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(RoadBLDPresetToolset)

FRoadBLDValidationReport URoadBLDPresetToolset::ValidatePreset(const FRoadBLDPresetSpec& Spec)
{
	return RoadBLDPresetSpecIO::ValidatePresetSpec(Spec, nullptr);
}

FRoadBLDCreatePresetResult URoadBLDPresetToolset::CreatePresetFromSpec(const FRoadBLDPresetSpec& Spec)
{
	if (!RoadBLDToolset::EnsureAuthorized())
	{
		return FRoadBLDCreatePresetResult();
	}

	return RoadBLDPresetSpecIO::WritePreset(Spec, nullptr);
}

FRoadBLDCreatePresetResult URoadBLDPresetToolset::UpdatePreset(
	TSubclassOf<UDynamicRoadDrawPreset> Preset,
	const FRoadBLDPresetSpec& Spec,
	const bool bReapplyToRoads)
{
	if (!RoadBLDToolset::EnsureAuthorized())
	{
		return FRoadBLDCreatePresetResult();
	}
	if (!Preset)
	{
		RoadBLDToolset::RaiseError(TEXT("Preset is required."));
		return FRoadBLDCreatePresetResult();
	}

	if (!RoadBLDToolset::IsGeneratedAsset(Preset.Get()))
	{
		RoadBLDToolset::RaiseError(TEXT(
			"Only presets created by this toolset (under /Game/RoadBLD_Generated) can be updated. "
			"Create a new preset with BasePreset set to this preset instead."));
		return FRoadBLDCreatePresetResult();
	}

	FRoadBLDCreatePresetResult Result = RoadBLDPresetSpecIO::WritePreset(Spec, Preset.Get());
	if (!Result.bSucceeded || !bReapplyToRoads)
	{
		return Result;
	}

	for (ADynamicRoadNetwork* Network : RoadBLDToolset::GetNetworks())
	{
		TArray<ADynamicRoad*> RoadsUsingPreset;
		for (const TObjectPtr<ADynamicRoad>& Road : Network->RoadsInNetwork)
		{
			if (IsValid(Road) && Road->SourceDrawPreset && Road->SourceDrawPreset->GetClass() == Preset.Get())
			{
				RoadsUsingPreset.Add(Road.Get());
			}
		}

		for (ADynamicRoad* Road : RoadsUsingPreset)
		{
			URoadBLDAuthoringToolset::ChangePreset(Road, Preset, true, false);
			Result.ReappliedRoads.Add(RoadBLDToolset::MakeActorRef(Road));
		}
	}

	return Result;
}

FRoadBLDAssetResult URoadBLDPresetToolset::CreateMaterialVariant(const FRoadBLDMaterialVariantSpec& Spec, const bool bOverwrite)
{
	FRoadBLDAssetResult Result;
	if (!RoadBLDToolset::EnsureAuthorized())
	{
		return Result;
	}

	const FString AssetBaseName = RoadBLDToolset::SanitizeAssetName(Spec.Name);
	if (AssetBaseName.IsEmpty())
	{
		Result.Errors.Add(TEXT("Name is required and must contain letters or digits."));
		return Result;
	}

	const FString PackageName = RoadBLDPresetAssetFactory::GetMaterialPackageName(TEXT("Shared"), AssetBaseName);
	if (!bOverwrite && RoadBLDPresetAssetFactory::DoesPackageExist(PackageName))
	{
		Result.Errors.Add(FString::Printf(TEXT("%s already exists. Set bOverwrite=true to update it."), *PackageName));
		return Result;
	}

	FString Error;
	const UMaterialInstanceConstant* Instance = RoadBLDPresetAssetFactory::WriteMaterialVariant(Spec, PackageName, Error);
	if (!Instance)
	{
		Result.Errors.Add(Error);
		return Result;
	}

	Result.bSucceeded = true;
	Result.AssetPath = Instance->GetPathName();
	return Result;
}
