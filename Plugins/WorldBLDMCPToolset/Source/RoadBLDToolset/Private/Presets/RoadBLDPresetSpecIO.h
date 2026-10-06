// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Presets/RoadBLDPresetSpec.h"

class UDynamicRoadDrawPreset;
class UMaterialInstanceConstant;
class UMaterialInterface;
class URoadBLDSidewalkPreset;

/** Conversion between preset specs and RoadBLD preset classes. */
namespace RoadBLDPresetSpecIO
{
	/** Full spec describing an existing preset. Every optional field is set. */
	FRoadBLDPresetSpec ExportPresetSpec(const UDynamicRoadDrawPreset* Preset);

	FRoadBLDSidewalkSpec ExportSidewalkSpec(const URoadBLDSidewalkPreset* Preset);

	/** Dry run: resolves and checks everything a write would do without touching assets. */
	FRoadBLDValidationReport ValidatePresetSpec(const FRoadBLDPresetSpec& Spec, UClass* PresetClassToUpdate);

	/** Validates, then writes material variants, inline sidewalk presets and the road preset Blueprint. */
	FRoadBLDCreatePresetResult WritePreset(const FRoadBLDPresetSpec& Spec, UClass* PresetClassToUpdate);
}

/** Asset creation helpers for generated presets and materials under /Game/RoadBLD_Generated. */
namespace RoadBLDPresetAssetFactory
{
	FString GetPresetPackageName(const FString& AssetBaseName);
	FString GetSidewalkPackageName(const FString& AssetBaseName);
	FString GetMaterialPackageName(const FString& Folder, const FString& AssetBaseName);

	bool DoesPackageExist(const FString& PackageName);

	/** Loads the Blueprint class at PackageName, or creates a new Blueprint subclass of ParentClass there. */
	UClass* CreateOrLoadBlueprintClass(UClass* ParentClass, const FString& PackageName, bool& bOutCreated, FString& OutError);

	bool SaveAsset(UObject* Asset, FString& OutError);
	bool SaveClassAsset(UClass* Class, FString& OutError);

	/** Loads the parent and checks every parameter override. Returns the parent when it loaded. */
	UMaterialInterface* ValidateMaterialVariant(const FRoadBLDMaterialVariantSpec& Spec, TArray<FString>& OutErrors);

	/** Creates or updates the material instance at PackageName and saves it. */
	UMaterialInstanceConstant* WriteMaterialVariant(const FRoadBLDMaterialVariantSpec& Spec, const FString& PackageName, FString& OutError);
}
