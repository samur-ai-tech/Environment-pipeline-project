// Copyright WorldBLD LLC. All rights reserved.

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "Common/RoadBLDToolsetUtils.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Engine/Texture.h"
#include "Factories/MaterialInstanceConstantFactoryNew.h"
#include "IAssetTools.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "MaterialEditingLibrary.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialParameters.h"
#include "Misc/PackageName.h"
#include "Presets/RoadBLDPresetSpecIO.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace RoadBLDPresetAssetFactory
{
	FString GetPresetPackageName(const FString& AssetBaseName)
	{
		return FString::Printf(TEXT("%s/Presets/RP_%s"), RoadBLDToolset::GeneratedContentRoot, *AssetBaseName);
	}

	FString GetSidewalkPackageName(const FString& AssetBaseName)
	{
		return FString::Printf(TEXT("%s/Sidewalks/RSP_%s"), RoadBLDToolset::GeneratedContentRoot, *AssetBaseName);
	}

	FString GetMaterialPackageName(const FString& Folder, const FString& AssetBaseName)
	{
		return FString::Printf(TEXT("%s/Materials/%s/MI_%s"), RoadBLDToolset::GeneratedContentRoot, *Folder, *AssetBaseName);
	}

	bool DoesPackageExist(const FString& PackageName)
	{
		return FindPackage(nullptr, *PackageName) != nullptr || FPackageName::DoesPackageExist(PackageName);
	}

	UClass* CreateOrLoadBlueprintClass(UClass* ParentClass, const FString& PackageName, bool& bOutCreated, FString& OutError)
	{
		bOutCreated = false;
		const FString AssetName = FPackageName::GetLongPackageAssetName(PackageName);

		if (DoesPackageExist(PackageName))
		{
			const UBlueprint* Existing = LoadObject<UBlueprint>(nullptr, *(PackageName + TEXT(".") + AssetName));
			if (!Existing || !Existing->GeneratedClass || !Existing->GeneratedClass->IsChildOf(ParentClass))
			{
				OutError = FString::Printf(TEXT("%s exists but is not a %s Blueprint."), *PackageName, *ParentClass->GetName());
				return nullptr;
			}
			return Existing->GeneratedClass;
		}

		UPackage* Package = CreatePackage(*PackageName);
		if (!Package)
		{
			OutError = FString::Printf(TEXT("Failed to create package %s."), *PackageName);
			return nullptr;
		}
		Package->FullyLoad();

		UBlueprint* Blueprint = FKismetEditorUtilities::CreateBlueprint(
			ParentClass,
			Package,
			FName(*AssetName),
			BPTYPE_Normal,
			UBlueprint::StaticClass(),
			UBlueprintGeneratedClass::StaticClass());
		if (!Blueprint || !Blueprint->GeneratedClass)
		{
			OutError = FString::Printf(TEXT("Failed to create Blueprint %s."), *PackageName);
			return nullptr;
		}

		FKismetEditorUtilities::CompileBlueprint(Blueprint, EBlueprintCompileOptions::SkipGarbageCollection);
		FAssetRegistryModule::AssetCreated(Blueprint);
		bOutCreated = true;
		return Blueprint->GeneratedClass;
	}

	bool SaveAsset(UObject* Asset, FString& OutError)
	{
		UPackage* Package = Asset->GetOutermost();
		Package->MarkPackageDirty();

		const FString FileName = FPackageName::LongPackageNameToFilename(Package->GetName(), FPackageName::GetAssetPackageExtension());
		FSavePackageArgs SaveArgs;
		SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
		SaveArgs.SaveFlags = SAVE_NoError;
		if (!UPackage::SavePackage(Package, Asset, *FileName, SaveArgs))
		{
			OutError = FString::Printf(TEXT("Failed to save %s."), *Package->GetName());
			return false;
		}
		return true;
	}

	bool SaveClassAsset(UClass* Class, FString& OutError)
	{
		UBlueprint* Blueprint = UBlueprint::GetBlueprintFromClass(Class);
		if (!Blueprint)
		{
			OutError = FString::Printf(TEXT("%s is not a Blueprint class."), *Class->GetPathName());
			return false;
		}
		return SaveAsset(Blueprint, OutError);
	}

	UMaterialInterface* ValidateMaterialVariant(const FRoadBLDMaterialVariantSpec& Spec, TArray<FString>& OutErrors)
	{
		if (Spec.Parent.TrimStartAndEnd().IsEmpty())
		{
			OutErrors.Add(TEXT("Parent is required."));
			return nullptr;
		}

		FString Error;
		UMaterialInterface* Parent = Cast<UMaterialInterface>(
			RoadBLDToolset::LoadObjectFromPath(Spec.Parent, UMaterialInterface::StaticClass(), Error));
		if (!Parent)
		{
			OutErrors.Add(Error);
			return nullptr;
		}

		auto CheckParameters = [Parent, &OutErrors](const EMaterialParameterType Type, const TArray<FString>& Names, const TCHAR* TypeName)
		{
			if (Names.Num() == 0)
			{
				return;
			}

			TMap<FMaterialParameterInfo, FMaterialParameterMetadata> Parameters;
			Parent->GetAllParametersOfType(Type, Parameters);
			for (const FString& Name : Names)
			{
				const FName ParameterName(*Name);
				bool bFound = false;
				for (const TPair<FMaterialParameterInfo, FMaterialParameterMetadata>& Pair : Parameters)
				{
					if (Pair.Key.Name == ParameterName)
					{
						bFound = true;
						break;
					}
				}

				if (!bFound)
				{
					OutErrors.Add(FString::Printf(
						TEXT("%s parameter '%s' does not exist on %s. Call ListMaterialParameters to see valid names."),
						TypeName, *Name, *Parent->GetName()));
				}
			}
		};

		TArray<FString> ScalarNames;
		Spec.Scalars.GetKeys(ScalarNames);
		CheckParameters(EMaterialParameterType::Scalar, ScalarNames, TEXT("Scalar"));

		TArray<FString> VectorNames;
		Spec.Vectors.GetKeys(VectorNames);
		CheckParameters(EMaterialParameterType::Vector, VectorNames, TEXT("Vector"));

		TArray<FString> TextureNames;
		Spec.Textures.GetKeys(TextureNames);
		CheckParameters(EMaterialParameterType::Texture, TextureNames, TEXT("Texture"));

		TArray<FString> SwitchNames;
		Spec.StaticSwitches.GetKeys(SwitchNames);
		CheckParameters(EMaterialParameterType::StaticSwitch, SwitchNames, TEXT("StaticSwitch"));

		for (const TPair<FString, float>& Scalar : Spec.Scalars)
		{
			if (!FMath::IsFinite(Scalar.Value))
			{
				OutErrors.Add(FString::Printf(TEXT("Scalar parameter '%s' is not a finite number."), *Scalar.Key));
			}
		}

		for (const TPair<FString, FString>& Texture : Spec.Textures)
		{
			FString TextureError;
			if (!RoadBLDToolset::LoadObjectFromPath(Texture.Value, UTexture::StaticClass(), TextureError))
			{
				OutErrors.Add(FString::Printf(TEXT("Texture parameter '%s': %s"), *Texture.Key, *TextureError));
			}
		}

		return Parent;
	}

	UMaterialInstanceConstant* WriteMaterialVariant(const FRoadBLDMaterialVariantSpec& Spec, const FString& PackageName, FString& OutError)
	{
		TArray<FString> Errors;
		UMaterialInterface* Parent = ValidateMaterialVariant(Spec, Errors);
		if (!Parent || Errors.Num() > 0)
		{
			OutError = FString::Join(Errors, TEXT(" "));
			return nullptr;
		}

		const FString AssetName = FPackageName::GetLongPackageAssetName(PackageName);
		UMaterialInstanceConstant* Instance = nullptr;
		if (DoesPackageExist(PackageName))
		{
			Instance = LoadObject<UMaterialInstanceConstant>(nullptr, *(PackageName + TEXT(".") + AssetName));
			if (!Instance)
			{
				OutError = FString::Printf(TEXT("%s exists but is not a material instance."), *PackageName);
				return nullptr;
			}
			Instance->Modify();
			UMaterialEditingLibrary::SetMaterialInstanceParent(Instance, Parent);
		}
		else
		{
			IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get();
			UMaterialInstanceConstantFactoryNew* Factory = NewObject<UMaterialInstanceConstantFactoryNew>();
			Factory->InitialParent = Parent;
			Instance = Cast<UMaterialInstanceConstant>(AssetTools.CreateAsset(
				AssetName,
				FPackageName::GetLongPackagePath(PackageName),
				UMaterialInstanceConstant::StaticClass(),
				Factory));
			if (!Instance)
			{
				OutError = FString::Printf(TEXT("Failed to create material instance %s."), *PackageName);
				return nullptr;
			}
		}

		for (const TPair<FString, float>& Scalar : Spec.Scalars)
		{
			UMaterialEditingLibrary::SetMaterialInstanceScalarParameterValue(Instance, FName(*Scalar.Key), Scalar.Value);
		}

		for (const TPair<FString, FLinearColor>& Vector : Spec.Vectors)
		{
			UMaterialEditingLibrary::SetMaterialInstanceVectorParameterValue(Instance, FName(*Vector.Key), Vector.Value);
		}

		for (const TPair<FString, FString>& Texture : Spec.Textures)
		{
			FString TextureError;
			UTexture* TextureAsset = Cast<UTexture>(RoadBLDToolset::LoadObjectFromPath(Texture.Value, UTexture::StaticClass(), TextureError));
			UMaterialEditingLibrary::SetMaterialInstanceTextureParameterValue(Instance, FName(*Texture.Key), TextureAsset);
		}

		for (const TPair<FString, bool>& Switch : Spec.StaticSwitches)
		{
			UMaterialEditingLibrary::SetMaterialInstanceStaticSwitchParameterValue(
				Instance, FName(*Switch.Key), Switch.Value, EMaterialParameterAssociation::GlobalParameter, false);
		}

		UMaterialEditingLibrary::UpdateMaterialInstance(Instance);

		if (!SaveAsset(Instance, OutError))
		{
			return nullptr;
		}
		return Instance;
	}
}
