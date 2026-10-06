// Copyright WorldBLD LLC. All rights reserved.

#include "Presets/RoadBLDPresetSpecIO.h"

#include "Common/RoadBLDToolsetUtils.h"
#include "CrossingStyle.h"
#include "Curves/CurveFloat.h"
#include "DynamicRoad/DynamicRoadData.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInterface.h"
#include "RoadModuleObject.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"

namespace RoadBLDPresetSpecIOPrivate
{
	using namespace RoadBLDToolset;

	struct FApplyContext
	{
		FApplyContext(FRoadBLDValidationReport& InReport, TArray<FString>& InWrittenAssets)
			: Report(InReport)
			, WrittenAssets(InWrittenAssets)
		{
		}

		/** When true nothing is written; material variants resolve to their parent and inline sidewalks are only checked. */
		bool bDryRun = true;
		bool bOverwrite = false;
		FString AssetBaseName;
		FRoadBLDValidationReport& Report;
		TArray<FString>& WrittenAssets;

		void Error(const FString& Field, const FString& Message)
		{
			FRoadBLDValidationIssue& Issue = Report.Errors.AddDefaulted_GetRef();
			Issue.Field = Field;
			Issue.Message = Message;
		}

		void Warning(const FString& Field, const FString& Message)
		{
			FRoadBLDValidationIssue& Issue = Report.Warnings.AddDefaulted_GetRef();
			Issue.Field = Field;
			Issue.Message = Message;
		}

		void PlanWrite(const FString& Field, const FString& PackageName)
		{
			if (!bOverwrite && RoadBLDPresetAssetFactory::DoesPackageExist(PackageName))
			{
				Error(Field, FString::Printf(
					TEXT("Asset %s already exists. Set bOverwrite=true to replace it or choose another name."),
					*PackageName));
				return;
			}
			Report.AssetsToWrite.AddUnique(PackageName);
		}
	};

	void CopyPresetProperties(UDynamicRoadDrawPreset* Destination, const UDynamicRoadDrawPreset* Source)
	{
		for (TFieldIterator<FProperty> It(UDynamicRoadDrawPreset::StaticClass()); It; ++It)
		{
			It->CopyCompleteValue_InContainer(Destination, Source);
		}
	}

	void ValidateClampedProperties(UObject* Object, const FString& FieldPrefix, FApplyContext& Context)
	{
		for (TFieldIterator<FProperty> It(Object->GetClass()); It; ++It)
		{
			const FNumericProperty* Numeric = CastField<FNumericProperty>(*It);
			if (!Numeric || !Numeric->IsFloatingPoint())
			{
				continue;
			}

			const FString& MinText = Numeric->GetMetaData(TEXT("ClampMin"));
			const FString& MaxText = Numeric->GetMetaData(TEXT("ClampMax"));
			if (MinText.IsEmpty() && MaxText.IsEmpty())
			{
				continue;
			}

			const double Value = Numeric->GetFloatingPointPropertyValue(Numeric->ContainerPtrToValuePtr<void>(Object));
			const FString Field = FieldPrefix.IsEmpty() ? Numeric->GetName() : FieldPrefix + TEXT(".") + Numeric->GetName();
			if (!MinText.IsEmpty() && Value < FCString::Atod(*MinText))
			{
				Context.Error(Field, FString::Printf(TEXT("%g is below the minimum %s."), Value, *MinText));
			}
			if (!MaxText.IsEmpty() && Value > FCString::Atod(*MaxText))
			{
				Context.Error(Field, FString::Printf(TEXT("%g is above the maximum %s."), Value, *MaxText));
			}
		}
	}

	UClass* ResolveClass(const FString& Path, UClass* BaseClass, const FString& Field, FApplyContext& Context)
	{
		if (Path.TrimStartAndEnd().IsEmpty() || Path.TrimStartAndEnd().Equals(TEXT("None"), ESearchCase::IgnoreCase))
		{
			return nullptr;
		}

		FString Error;
		UClass* Class = LoadClassFromPath(Path, BaseClass, Error);
		if (!Class)
		{
			Context.Error(Field, Error);
		}
		return Class;
	}

	UMaterialInterface* ResolveMaterial(
		const FRoadBLDMaterialRef& Ref,
		const FString& Field,
		const FString& DefaultVariantName,
		FApplyContext& Context)
	{
		if (Ref.Variant.IsSet())
		{
			FRoadBLDMaterialVariantSpec Variant = Ref.Variant.GetValue();
			if (Variant.Name.TrimStartAndEnd().IsEmpty())
			{
				Variant.Name = DefaultVariantName;
			}

			TArray<FString> Errors;
			UMaterialInterface* Parent = RoadBLDPresetAssetFactory::ValidateMaterialVariant(Variant, Errors);
			for (const FString& VariantError : Errors)
			{
				Context.Error(Field + TEXT(".Variant"), VariantError);
			}
			if (!Parent || Errors.Num() > 0)
			{
				return nullptr;
			}

			const FString PackageName = RoadBLDPresetAssetFactory::GetMaterialPackageName(
				Context.AssetBaseName, SanitizeAssetName(Variant.Name));
			if (Context.bDryRun)
			{
				Context.PlanWrite(Field + TEXT(".Variant.Name"), PackageName);
				return Parent;
			}

			FString Error;
			UMaterialInstanceConstant* Instance = RoadBLDPresetAssetFactory::WriteMaterialVariant(Variant, PackageName, Error);
			if (!Instance)
			{
				Context.Error(Field + TEXT(".Variant"), Error);
				return nullptr;
			}

			Context.WrittenAssets.AddUnique(PackageName);
			return Instance;
		}

		const FString Path = Ref.Path.TrimStartAndEnd();
		if (Path.IsEmpty() || Path.Equals(TEXT("None"), ESearchCase::IgnoreCase))
		{
			return nullptr;
		}

		FString Error;
		UMaterialInterface* Material = Cast<UMaterialInterface>(LoadObjectFromPath(Path, UMaterialInterface::StaticClass(), Error));
		if (!Material)
		{
			Context.Error(Field + TEXT(".Path"), Error);
		}
		return Material;
	}

	FDynamicRoadDrawPresetMarking ToMarking(
		const FRoadBLDMarkingSpec& Spec,
		const FString& Field,
		const FString& DefaultVariantName,
		FApplyContext& Context)
	{
		FDynamicRoadDrawPresetMarking Marking;
		if (!FMath::IsFinite(Spec.Width) || Spec.Width < 0.0 || Spec.Width > 1000.0)
		{
			Context.Error(Field + TEXT(".Width"), TEXT("Marking width must be between 0 and 1000 cm."));
		}

		Marking.MarkingWidth = static_cast<float>(Spec.Width);
		Marking.MarkingMaterial = ResolveMaterial(Spec.Material, Field + TEXT(".Material"), DefaultVariantName, Context);
		Marking.EdgeOffset = static_cast<float>(Spec.EdgeOffset);
		Marking.TextureVScale = Spec.TextureVScale;
		return Marking;
	}

	TArray<FDynamicRoadLaneProfile> ToLaneProfiles(const TArray<FRoadBLDLaneSpec>& Lanes, const TCHAR* SideField, FApplyContext& Context)
	{
		TArray<FDynamicRoadLaneProfile> Profiles;
		for (int32 Index = 0; Index < Lanes.Num(); ++Index)
		{
			const FRoadBLDLaneSpec& Lane = Lanes[Index];
			const FString Field = FString::Printf(TEXT("%s[%d]"), SideField, Index);
			const FString VariantBaseName = FString::Printf(TEXT("%s%d"), SideField, Index);

			FDynamicRoadLaneProfile& Profile = Profiles.AddDefaulted_GetRef();
			if (!FMath::IsFinite(Lane.Width) || Lane.Width <= 0.0 || Lane.Width > 10000.0)
			{
				Context.Error(Field + TEXT(".Width"), TEXT("Lane width must be greater than 0 and at most 10000 cm."));
			}
			Profile.Width = static_cast<float>(Lane.Width);

			ELaneType LaneType = ELaneType::Normal;
			if (!EnumFromString(Lane.Type, LaneType) || LaneType == ELaneType::None)
			{
				Context.Error(Field + TEXT(".Type"), FString::Printf(
					TEXT("Unknown lane type '%s'. Use Normal, Parking, Border, Restricted, Shoulder, CenterTurn or Median."),
					*Lane.Type));
			}
			Profile.Type = LaneType;

			Profile.OuterLaneMarking = ToMarking(Lane.OuterMarking, Field + TEXT(".OuterMarking"), VariantBaseName + TEXT("_Marking"), Context);
			Profile.LaneOverlayMaterial = ResolveMaterial(Lane.OverlayMaterial, Field + TEXT(".OverlayMaterial"), VariantBaseName + TEXT("_Overlay"), Context);
			Profile.TextureUScale = Lane.TextureUScale;
			Profile.TextureVScale = Lane.TextureVScale;
			Profile.SegmentBehavior = Lane.SegmentBehavior;

			if (Profile.OuterLaneMarking.MarkingMaterial && Lane.OuterMarking.Width >= Lane.Width)
			{
				Context.Warning(Field + TEXT(".OuterMarking.Width"), TEXT("The marking is at least as wide as its lane."));
			}
		}
		return Profiles;
	}

	void ApplySidewalkSpec(
		const FRoadBLDSidewalkSpec& Spec,
		URoadBLDSidewalkPreset* Target,
		const FString& Field,
		const FString& VariantBaseName,
		FApplyContext& Context)
	{
		if (!FMath::IsFinite(Spec.Width) || Spec.Width < 0.0)
		{
			Context.Error(Field + TEXT(".Width"), TEXT("Sidewalk width must be zero or positive."));
		}

		Target->Width = Spec.Width;
		Target->ZOffset = Spec.ZOffset;
		Target->CurbCutLowerAmount = Spec.CurbCutLowerAmount;
		Target->Material = ResolveMaterial(Spec.Material, Field + TEXT(".Material"), VariantBaseName + TEXT("_Surface"), Context);
		Target->CornerMaterial = ResolveMaterial(Spec.CornerMaterial, Field + TEXT(".CornerMaterial"), VariantBaseName + TEXT("_Corner"), Context);
		Target->CurbCutMaterial = ResolveMaterial(Spec.CurbCutMaterial, Field + TEXT(".CurbCutMaterial"), VariantBaseName + TEXT("_CurbCut"), Context);
		Target->CurbClass = ResolveClass(Spec.CurbClass, URoadModuleObject::StaticClass(), Field + TEXT(".CurbClass"), Context);

		Target->SidewalkPartitions.Reset();
		double PartitionWidthSum = 0.0;
		for (int32 Index = 0; Index < Spec.Partitions.Num(); ++Index)
		{
			const FRoadBLDSidewalkPartitionSpec& PartitionSpec = Spec.Partitions[Index];
			const FString PartitionField = FString::Printf(TEXT("%s.Partitions[%d]"), *Field, Index);
			if (!FMath::IsFinite(PartitionSpec.Width) || PartitionSpec.Width < 0.0)
			{
				Context.Error(PartitionField + TEXT(".Width"), TEXT("Partition width must be zero or positive."));
			}

			FSidewalkPartitionDescriptor& Partition = Target->SidewalkPartitions.AddDefaulted_GetRef();
			Partition.Width = PartitionSpec.Width;
			Partition.bWalkable = PartitionSpec.bWalkable;
			Partition.Material = ResolveMaterial(
				PartitionSpec.Material,
				PartitionField + TEXT(".Material"),
				FString::Printf(TEXT("%s_Partition%d"), *VariantBaseName, Index),
				Context);
			Partition.TextureUScale = PartitionSpec.TextureUScale;
			Partition.TextureVScale = PartitionSpec.TextureVScale;
			PartitionWidthSum += PartitionSpec.Width;
		}

		if (Spec.Partitions.Num() > 0 && !FMath::IsNearlyEqual(PartitionWidthSum, Spec.Width, 1.0))
		{
			Context.Warning(Field + TEXT(".Partitions"), FString::Printf(
				TEXT("Partition widths add up to %.0f cm but the sidewalk is %.0f cm wide."), PartitionWidthSum, Spec.Width));
		}
	}

	TSubclassOf<URoadBLDSidewalkPreset> ResolveSidewalkChoice(
		const FRoadBLDSidewalkChoice& Choice,
		const FString& Field,
		const FString& DefaultName,
		FApplyContext& Context)
	{
		const bool bHasPreset = !Choice.Preset.TrimStartAndEnd().IsEmpty();
		const int32 ChoiceCount = (Choice.bNone ? 1 : 0) + (bHasPreset ? 1 : 0) + (Choice.Inline.IsSet() ? 1 : 0);
		if (ChoiceCount != 1)
		{
			Context.Error(Field, TEXT("Set exactly one of bNone, Preset or Inline."));
			return nullptr;
		}

		if (Choice.bNone)
		{
			return nullptr;
		}

		if (bHasPreset)
		{
			return ResolveClass(Choice.Preset, URoadBLDSidewalkPreset::StaticClass(), Field + TEXT(".Preset"), Context);
		}

		const FRoadBLDSidewalkSpec& Spec = Choice.Inline.GetValue();
		const FString BaseName = SanitizeAssetName(Spec.Name.TrimStartAndEnd().IsEmpty() ? DefaultName : Spec.Name);
		const FString PackageName = RoadBLDPresetAssetFactory::GetSidewalkPackageName(BaseName);
		const FString InlineField = Field + TEXT(".Inline");

		if (Context.bDryRun)
		{
			URoadBLDSidewalkPreset* Scratch = NewObject<URoadBLDSidewalkPreset>(GetTransientPackage(), NAME_None, RF_Transient);
			ApplySidewalkSpec(Spec, Scratch, InlineField, BaseName, Context);
			ValidateClampedProperties(Scratch, InlineField, Context);
			Context.PlanWrite(InlineField + TEXT(".Name"), PackageName);
			return nullptr;
		}

		bool bCreated = false;
		FString Error;
		UClass* SidewalkClass = RoadBLDPresetAssetFactory::CreateOrLoadBlueprintClass(
			URoadBLDSidewalkPreset::StaticClass(), PackageName, bCreated, Error);
		if (!SidewalkClass)
		{
			Context.Error(InlineField, Error);
			return nullptr;
		}

		URoadBLDSidewalkPreset* SidewalkPreset = SidewalkClass->GetDefaultObject<URoadBLDSidewalkPreset>();
		SidewalkPreset->Modify();
		ApplySidewalkSpec(Spec, SidewalkPreset, InlineField, BaseName, Context);
		if (!RoadBLDPresetAssetFactory::SaveClassAsset(SidewalkClass, Error))
		{
			Context.Error(InlineField, Error);
			return nullptr;
		}

		Context.WrittenAssets.AddUnique(PackageName);
		return SidewalkClass;
	}

	void InitializeTarget(
		const FRoadBLDPresetSpec& Spec,
		UClass* PresetClassToUpdate,
		UDynamicRoadDrawPreset* Target,
		FApplyContext& Context)
	{
		UClass* BaseClass = nullptr;
		if (!Spec.BasePreset.TrimStartAndEnd().IsEmpty())
		{
			FString Error;
			BaseClass = LoadClassFromPath(Spec.BasePreset, UDynamicRoadDrawPreset::StaticClass(), Error);
			if (!BaseClass)
			{
				Context.Error(TEXT("BasePreset"), Error);
			}
		}

		const UDynamicRoadDrawPreset* Source = nullptr;
		if (PresetClassToUpdate)
		{
			// Updates start from the preset's current values so fields left unset are kept. DescribePreset sets
			// BasePreset to the preset itself, so that value is accepted.
			if (BaseClass && BaseClass != PresetClassToUpdate)
			{
				Context.Error(TEXT("BasePreset"), TEXT(
					"UpdatePreset keeps this preset's current values and cannot re-base it on another preset. "
					"Omit BasePreset, or create a new preset from that base with CreatePresetFromSpec."));
			}
			Source = PresetClassToUpdate->GetDefaultObject<UDynamicRoadDrawPreset>();
		}
		else if (BaseClass)
		{
			Source = BaseClass->GetDefaultObject<UDynamicRoadDrawPreset>();
		}

		if (Source && Source != Target)
		{
			CopyPresetProperties(Target, Source);
		}
	}

	void ApplySpecToPreset(const FRoadBLDPresetSpec& Spec, UDynamicRoadDrawPreset* Target, FApplyContext& Context)
	{
		const FString Name = Spec.Name.TrimStartAndEnd();
		if (Name.IsEmpty())
		{
			Context.Error(TEXT("Name"), TEXT("Name is required."));
		}
		else
		{
			Target->PresetName = FName(*Name);
		}

		if (Spec.Description.IsSet())
		{
			Target->Description = Spec.Description.GetValue();
		}
		if (Spec.Tags.IsSet())
		{
			Target->Tags = Spec.Tags.GetValue();
		}
		if (Spec.Region.IsSet())
		{
			const FString Region = Spec.Region.GetValue().TrimStartAndEnd();
			Target->Region = (Region.IsEmpty() || Region.Equals(TEXT("Unspecified"), ESearchCase::IgnoreCase)) ? NAME_None : FName(*Region);
		}
		if (Spec.Category.IsSet())
		{
			Target->Category = Spec.Category.GetValue();
		}

		if (Spec.LeftLanes.IsSet())
		{
			Target->LeftLanes = ToLaneProfiles(Spec.LeftLanes.GetValue(), TEXT("LeftLanes"), Context);
		}
		if (Spec.RightLanes.IsSet())
		{
			Target->RightLanes = ToLaneProfiles(Spec.RightLanes.GetValue(), TEXT("RightLanes"), Context);
		}
		if (Target->LeftLanes.Num() + Target->RightLanes.Num() == 0)
		{
			Context.Error(TEXT("RightLanes"), TEXT("A preset needs at least one lane."));
		}

		if (Spec.CenterlineMarking.IsSet())
		{
			Target->CenterlineMarking = ToMarking(Spec.CenterlineMarking.GetValue(), TEXT("CenterlineMarking"), TEXT("Centerline"), Context);
		}
		if (Spec.CenterlineSegmentBehavior.IsSet())
		{
			Target->CenterlineSegmentBehavior = Spec.CenterlineSegmentBehavior.GetValue();
		}
		if (Spec.LaneMarkingIntersectionOffset.IsSet())
		{
			Target->LaneMarkingIntersectionOffset = static_cast<float>(Spec.LaneMarkingIntersectionOffset.GetValue());
		}

		if (Spec.RoadMaterial.IsSet())
		{
			Target->RoadMaterial = ResolveMaterial(Spec.RoadMaterial.GetValue(), TEXT("RoadMaterial"), TEXT("Road"), Context);
		}
		if (Spec.IntersectionMaterial.IsSet())
		{
			Target->IntersectionMaterial = ResolveMaterial(Spec.IntersectionMaterial.GetValue(), TEXT("IntersectionMaterial"), TEXT("Intersection"), Context);
		}
		if (Spec.AbutmentMaterial.IsSet())
		{
			Target->AbutmentMaterial = ResolveMaterial(Spec.AbutmentMaterial.GetValue(), TEXT("AbutmentMaterial"), TEXT("Abutment"), Context);
		}
		if (Spec.IntersectionBlendDistance.IsSet())
		{
			Target->IntersectionBlendDistance = static_cast<float>(Spec.IntersectionBlendDistance.GetValue());
		}
		if (Spec.RoadCrownHeight.IsSet())
		{
			Target->RoadCrownHeight = static_cast<float>(Spec.RoadCrownHeight.GetValue());
		}
		if (Spec.bDisableRoadThickness.IsSet())
		{
			Target->bDisableRoadThickness = Spec.bDisableRoadThickness.GetValue();
		}

		if (Spec.bEnableRoadEdgeDetail.IsSet())
		{
			Target->bEnableRoadEdgeDetail = Spec.bEnableRoadEdgeDetail.GetValue();
		}
		if (Spec.RoadEdgeDetailMaterial.IsSet())
		{
			Target->RoadEdgeDetailMaterial = ResolveMaterial(Spec.RoadEdgeDetailMaterial.GetValue(), TEXT("RoadEdgeDetailMaterial"), TEXT("EdgeDetail"), Context);
		}
		if (Spec.RoadEdgeDetailProfile.IsSet())
		{
			const FString ProfilePath = Spec.RoadEdgeDetailProfile.GetValue().TrimStartAndEnd();
			if (ProfilePath.IsEmpty())
			{
				Target->RoadEdgeDetailProfile.Reset();
			}
			else
			{
				FString Error;
				if (UObject* Curve = LoadObjectFromPath(ProfilePath, UCurveFloat::StaticClass(), Error))
				{
					Target->RoadEdgeDetailProfile = TSoftObjectPtr<UCurveFloat>(Cast<UCurveFloat>(Curve));
				}
				else
				{
					Context.Error(TEXT("RoadEdgeDetailProfile"), Error);
				}
			}
		}
		if (Spec.RoadEdgeDetailProfileScale.IsSet())
		{
			Target->RoadEdgeDetailProfileScale = static_cast<float>(Spec.RoadEdgeDetailProfileScale.GetValue());
		}
		if (Spec.RoadEdgeDetailUScale.IsSet())
		{
			Target->RoadEdgeDetailUScale = static_cast<float>(Spec.RoadEdgeDetailUScale.GetValue());
		}
		if (Spec.RoadEdgeDetailVScale.IsSet())
		{
			Target->RoadEdgeDetailVScale = static_cast<float>(Spec.RoadEdgeDetailVScale.GetValue());
		}

		if (Spec.bGenerateAbutments.IsSet())
		{
			Target->bGenerateAbutments = Spec.bGenerateAbutments.GetValue();
		}
		if (Spec.AbutmentThreshold.IsSet())
		{
			Target->AbutmentThreshold = static_cast<float>(Spec.AbutmentThreshold.GetValue());
		}
		if (Spec.BridgeRangeGrowth.IsSet())
		{
			Target->BridgeRangeGrowth = static_cast<float>(Spec.BridgeRangeGrowth.GetValue());
		}

		if (Spec.bEnableLandscapePaint.IsSet())
		{
			Target->bEnableLandscapePaint = Spec.bEnableLandscapePaint.GetValue();
		}
		if (Spec.LandscapePaintLayerName.IsSet())
		{
			Target->LandscapePaintLayerName = FName(*Spec.LandscapePaintLayerName.GetValue().TrimStartAndEnd());
		}
		if (Spec.LandscapePaintWidthExtension.IsSet())
		{
			Target->LandscapePaintWidthExtension = static_cast<float>(Spec.LandscapePaintWidthExtension.GetValue());
		}
		if (Spec.LandscapePaintFalloff.IsSet())
		{
			Target->LandscapePaintFalloff = static_cast<float>(Spec.LandscapePaintFalloff.GetValue());
		}

		if (Spec.RoadModules.IsSet())
		{
			Target->RoadModules.Reset();
			const TArray<FRoadBLDModuleSpec>& Modules = Spec.RoadModules.GetValue();
			for (int32 Index = 0; Index < Modules.Num(); ++Index)
			{
				const FString Field = FString::Printf(TEXT("RoadModules[%d].ModuleClass"), Index);
				UClass* ModuleClass = ResolveClass(Modules[Index].ModuleClass, URoadModuleObject::StaticClass(), Field, Context);
				if (!ModuleClass)
				{
					if (Modules[Index].ModuleClass.TrimStartAndEnd().IsEmpty())
					{
						Context.Error(Field, TEXT("ModuleClass is required."));
					}
					continue;
				}

				FDynamicRoadDrawPresetModule& Module = Target->RoadModules.AddDefaulted_GetRef();
				Module.ModulePosition = Modules[Index].Position;
				Module.ModuleClass = ModuleClass;
			}
		}

		if (Spec.PropSpawners.IsSet())
		{
			Target->PropSpawners.Reset();
			const TArray<FRoadBLDPropSpawnerSpec>& Spawners = Spec.PropSpawners.GetValue();
			for (int32 Index = 0; Index < Spawners.Num(); ++Index)
			{
				const FRoadBLDPropSpawnerSpec& SpawnerSpec = Spawners[Index];
				const FString Field = FString::Printf(TEXT("PropSpawners[%d]"), Index);

				FPropSpawnerSettings& Settings = Target->PropSpawners.AddDefaulted_GetRef();
				for (int32 MeshIndex = 0; MeshIndex < SpawnerSpec.Meshes.Num(); ++MeshIndex)
				{
					FString Error;
					if (UStaticMesh* Mesh = Cast<UStaticMesh>(LoadObjectFromPath(SpawnerSpec.Meshes[MeshIndex], UStaticMesh::StaticClass(), Error)))
					{
						Settings.MeshesToUse.Add(Mesh);
					}
					else
					{
						Context.Error(FString::Printf(TEXT("%s.Meshes[%d]"), *Field, MeshIndex), Error);
					}
				}
				if (SpawnerSpec.Meshes.Num() == 0)
				{
					Context.Error(Field + TEXT(".Meshes"), TEXT("A prop spawner needs at least one mesh."));
				}
				if (SpawnerSpec.DistanceBetweenProps.X <= 0.0 || SpawnerSpec.DistanceBetweenProps.Y <= 0.0)
				{
					Context.Error(Field + TEXT(".DistanceBetweenProps"), TEXT("Prop spacing must be positive."));
				}

				Settings.Edge = SpawnerSpec.Edge;
				Settings.EdgeOffset = SpawnerSpec.EdgeOffset;
				Settings.DistanceBetweenProps = SpawnerSpec.DistanceBetweenProps;
				Settings.MinAndMaxScale = SpawnerSpec.MinAndMaxScale;
				Settings.ZOffset = SpawnerSpec.ZOffset;
				Settings.RotationOffset = SpawnerSpec.RotationOffset;
				Settings.bRandomZRotation = SpawnerSpec.bRandomZRotation;
				Settings.bAlignToWorldZ = SpawnerSpec.bAlignToWorldZ;
				Settings.SpawnArea = SpawnerSpec.SpawnArea;
			}
		}

		if (Spec.bAutomaticCrossings.IsSet())
		{
			Target->DefaultAutomations.AutomaticCrossings.bEnabled = Spec.bAutomaticCrossings.GetValue();
		}
		if (Spec.CrossingStyle.IsSet())
		{
			Target->DefaultAutomations.AutomaticCrossings.CrossingStyleClass =
				ResolveClass(Spec.CrossingStyle.GetValue(), UCrossingStyle::StaticClass(), TEXT("CrossingStyle"), Context);
		}

		if (Spec.LeftSidewalk.IsSet())
		{
			Target->LeftSidewalkPresetClass = ResolveSidewalkChoice(
				Spec.LeftSidewalk.GetValue(), TEXT("LeftSidewalk"), Context.AssetBaseName + TEXT("_Left"), Context);
		}
		if (Spec.RightSidewalk.IsSet())
		{
			Target->RightSidewalkPresetClass = ResolveSidewalkChoice(
				Spec.RightSidewalk.GetValue(), TEXT("RightSidewalk"), Context.AssetBaseName + TEXT("_Right"), Context);
		}

		if (Spec.ActorTags.IsSet())
		{
			Target->ActorTags.Reset();
			for (const FString& Tag : Spec.ActorTags.GetValue())
			{
				Target->ActorTags.Add(FName(*Tag));
			}
		}

		if (Spec.RoadPCGGraph.IsSet())
		{
			// Set through reflection so the toolset does not depend on the PCG module.
			const FObjectPropertyBase* GraphProperty = FindFProperty<FObjectPropertyBase>(UDynamicRoadDrawPreset::StaticClass(), TEXT("RoadPCGGraph"));
			const FString GraphPath = Spec.RoadPCGGraph.GetValue().TrimStartAndEnd();
			if (GraphProperty)
			{
				UObject* Graph = nullptr;
				if (!GraphPath.IsEmpty())
				{
					FString Error;
					Graph = LoadObjectFromPath(GraphPath, GraphProperty->PropertyClass, Error);
					if (!Graph)
					{
						Context.Error(TEXT("RoadPCGGraph"), Error);
					}
				}
				GraphProperty->SetObjectPropertyValue_InContainer(Target, Graph);
			}
		}

		if (Spec.ElementEdgeZOffset.IsSet())
		{
			Target->ElementEdgeZOffset = Spec.ElementEdgeZOffset.GetValue();
		}
	}

	FRoadBLDMaterialRef ExportMaterial(const UObject* Material)
	{
		FRoadBLDMaterialRef Ref;
		Ref.Path = GetObjectPath(Material);
		return Ref;
	}

	FRoadBLDMarkingSpec ExportMarking(const FDynamicRoadDrawPresetMarking& Marking)
	{
		FRoadBLDMarkingSpec Spec;
		Spec.Width = Marking.MarkingWidth;
		Spec.Material = ExportMaterial(Marking.MarkingMaterial);
		Spec.EdgeOffset = Marking.EdgeOffset;
		Spec.TextureVScale = Marking.TextureVScale;
		return Spec;
	}

	TArray<FRoadBLDLaneSpec> ExportLanes(const TArray<FDynamicRoadLaneProfile>& Lanes)
	{
		TArray<FRoadBLDLaneSpec> Specs;
		for (const FDynamicRoadLaneProfile& Lane : Lanes)
		{
			FRoadBLDLaneSpec& Spec = Specs.AddDefaulted_GetRef();
			Spec.Width = Lane.Width;
			Spec.Type = EnumToString(Lane.Type);
			Spec.OuterMarking = ExportMarking(Lane.OuterLaneMarking);
			Spec.OverlayMaterial = ExportMaterial(Lane.LaneOverlayMaterial);
			Spec.TextureUScale = Lane.TextureUScale;
			Spec.TextureVScale = Lane.TextureVScale;
			Spec.SegmentBehavior = Lane.SegmentBehavior;
		}
		return Specs;
	}

	FRoadBLDSidewalkChoice ExportSidewalkChoice(const TSubclassOf<URoadBLDSidewalkPreset>& SidewalkClass)
	{
		FRoadBLDSidewalkChoice Choice;
		if (SidewalkClass)
		{
			Choice.Preset = SidewalkClass->GetPathName();
		}
		else
		{
			Choice.bNone = true;
		}
		return Choice;
	}
}

FRoadBLDPresetSpec RoadBLDPresetSpecIO::ExportPresetSpec(const UDynamicRoadDrawPreset* Preset)
{
	using namespace RoadBLDPresetSpecIOPrivate;

	FRoadBLDPresetSpec Spec;
	if (!Preset)
	{
		return Spec;
	}

	Spec.Name = Preset->PresetName.IsNone() ? Preset->GetClass()->GetName() : Preset->PresetName.ToString();
	Spec.Description = Preset->Description;
	Spec.Tags = Preset->Tags;
	Spec.Region = ResolvePresetRegion(Preset->GetClass());
	Spec.Category = Preset->Category;

	Spec.LeftLanes = ExportLanes(Preset->LeftLanes);
	Spec.RightLanes = ExportLanes(Preset->RightLanes);
	Spec.CenterlineMarking = ExportMarking(Preset->CenterlineMarking);
	Spec.CenterlineSegmentBehavior = Preset->CenterlineSegmentBehavior;
	Spec.LaneMarkingIntersectionOffset = Preset->LaneMarkingIntersectionOffset;

	Spec.RoadMaterial = ExportMaterial(Preset->RoadMaterial);
	Spec.IntersectionMaterial = ExportMaterial(Preset->IntersectionMaterial);
	Spec.AbutmentMaterial = ExportMaterial(Preset->AbutmentMaterial);
	Spec.IntersectionBlendDistance = Preset->IntersectionBlendDistance;
	Spec.RoadCrownHeight = Preset->RoadCrownHeight;
	Spec.bDisableRoadThickness = Preset->bDisableRoadThickness;

	Spec.bEnableRoadEdgeDetail = Preset->bEnableRoadEdgeDetail;
	Spec.RoadEdgeDetailMaterial = ExportMaterial(Preset->RoadEdgeDetailMaterial);
	Spec.RoadEdgeDetailProfile = Preset->RoadEdgeDetailProfile.ToSoftObjectPath().ToString();
	Spec.RoadEdgeDetailProfileScale = Preset->RoadEdgeDetailProfileScale;
	Spec.RoadEdgeDetailUScale = Preset->RoadEdgeDetailUScale;
	Spec.RoadEdgeDetailVScale = Preset->RoadEdgeDetailVScale;

	Spec.bGenerateAbutments = Preset->bGenerateAbutments;
	Spec.AbutmentThreshold = Preset->AbutmentThreshold;
	Spec.BridgeRangeGrowth = Preset->BridgeRangeGrowth;

	Spec.bEnableLandscapePaint = Preset->bEnableLandscapePaint;
	Spec.LandscapePaintLayerName = Preset->LandscapePaintLayerName.ToString();
	Spec.LandscapePaintWidthExtension = Preset->LandscapePaintWidthExtension;
	Spec.LandscapePaintFalloff = Preset->LandscapePaintFalloff;

	TArray<FRoadBLDModuleSpec> Modules;
	for (const FDynamicRoadDrawPresetModule& Module : Preset->RoadModules)
	{
		FRoadBLDModuleSpec& ModuleSpec = Modules.AddDefaulted_GetRef();
		ModuleSpec.Position = Module.ModulePosition;
		ModuleSpec.ModuleClass = GetObjectPath(Module.ModuleClass.Get());
	}
	Spec.RoadModules = Modules;

	TArray<FRoadBLDPropSpawnerSpec> Spawners;
	for (const FPropSpawnerSettings& Settings : Preset->PropSpawners)
	{
		FRoadBLDPropSpawnerSpec& SpawnerSpec = Spawners.AddDefaulted_GetRef();
		for (const TObjectPtr<UStaticMesh>& Mesh : Settings.MeshesToUse)
		{
			SpawnerSpec.Meshes.Add(GetObjectPath(Mesh));
		}
		SpawnerSpec.Edge = Settings.Edge;
		SpawnerSpec.EdgeOffset = Settings.EdgeOffset;
		SpawnerSpec.DistanceBetweenProps = Settings.DistanceBetweenProps;
		SpawnerSpec.MinAndMaxScale = Settings.MinAndMaxScale;
		SpawnerSpec.ZOffset = Settings.ZOffset;
		SpawnerSpec.RotationOffset = Settings.RotationOffset;
		SpawnerSpec.bRandomZRotation = Settings.bRandomZRotation;
		SpawnerSpec.bAlignToWorldZ = Settings.bAlignToWorldZ;
		SpawnerSpec.SpawnArea = Settings.SpawnArea;
	}
	Spec.PropSpawners = Spawners;

	Spec.bAutomaticCrossings = Preset->DefaultAutomations.AutomaticCrossings.bEnabled;
	Spec.CrossingStyle = GetObjectPath(Preset->DefaultAutomations.AutomaticCrossings.CrossingStyleClass.Get());
	Spec.LeftSidewalk = ExportSidewalkChoice(Preset->LeftSidewalkPresetClass);
	Spec.RightSidewalk = ExportSidewalkChoice(Preset->RightSidewalkPresetClass);

	TArray<FString> ActorTags;
	for (const FName& Tag : Preset->ActorTags)
	{
		ActorTags.Add(Tag.ToString());
	}
	Spec.ActorTags = ActorTags;

	if (const FObjectPropertyBase* GraphProperty = FindFProperty<FObjectPropertyBase>(UDynamicRoadDrawPreset::StaticClass(), TEXT("RoadPCGGraph")))
	{
		Spec.RoadPCGGraph = GetObjectPath(GraphProperty->GetObjectPropertyValue_InContainer(Preset));
	}

	Spec.ElementEdgeZOffset = Preset->ElementEdgeZOffset;
	return Spec;
}

FRoadBLDSidewalkSpec RoadBLDPresetSpecIO::ExportSidewalkSpec(const URoadBLDSidewalkPreset* Preset)
{
	using namespace RoadBLDPresetSpecIOPrivate;

	FRoadBLDSidewalkSpec Spec;
	if (!Preset)
	{
		return Spec;
	}

	Spec.Name = Preset->GetClass()->GetName();
	Spec.Name.RemoveFromEnd(TEXT("_C"));
	Spec.Width = Preset->Width;
	Spec.ZOffset = Preset->ZOffset;
	Spec.Material = ExportMaterial(Preset->Material);
	Spec.CornerMaterial = ExportMaterial(Preset->CornerMaterial);
	Spec.CurbClass = GetObjectPath(Preset->CurbClass.Get());
	Spec.CurbCutLowerAmount = Preset->CurbCutLowerAmount;
	Spec.CurbCutMaterial = ExportMaterial(Preset->CurbCutMaterial);
	for (const FSidewalkPartitionDescriptor& Partition : Preset->SidewalkPartitions)
	{
		FRoadBLDSidewalkPartitionSpec& PartitionSpec = Spec.Partitions.AddDefaulted_GetRef();
		PartitionSpec.Width = Partition.Width;
		PartitionSpec.bWalkable = Partition.bWalkable;
		PartitionSpec.Material = ExportMaterial(Partition.Material);
		PartitionSpec.TextureUScale = Partition.TextureUScale;
		PartitionSpec.TextureVScale = Partition.TextureVScale;
	}
	return Spec;
}

FRoadBLDValidationReport RoadBLDPresetSpecIO::ValidatePresetSpec(const FRoadBLDPresetSpec& Spec, UClass* PresetClassToUpdate)
{
	using namespace RoadBLDPresetSpecIOPrivate;

	FRoadBLDValidationReport Report;
	TArray<FString> UnusedWrites;
	FApplyContext Context(Report, UnusedWrites);
	Context.bDryRun = true;
	Context.bOverwrite = Spec.bOverwrite || PresetClassToUpdate != nullptr;
	Context.AssetBaseName = SanitizeAssetName(Spec.Name);

	if (Context.AssetBaseName.IsEmpty())
	{
		Context.Error(TEXT("Name"), TEXT("Name must contain letters or digits."));
	}
	else if (PresetClassToUpdate)
	{
		Report.AssetsToWrite.Add(PresetClassToUpdate->GetOutermost()->GetName());
	}
	else
	{
		Context.PlanWrite(TEXT("Name"), RoadBLDPresetAssetFactory::GetPresetPackageName(Context.AssetBaseName));
	}

	UDynamicRoadDrawPreset* Scratch = NewObject<UDynamicRoadDrawPreset>(GetTransientPackage(), NAME_None, RF_Transient);
	InitializeTarget(Spec, PresetClassToUpdate, Scratch, Context);
	ApplySpecToPreset(Spec, Scratch, Context);
	ValidateClampedProperties(Scratch, FString(), Context);

	Report.Traits = ComputePresetTraits(Scratch);
	if (Spec.LeftSidewalk.IsSet() && Spec.LeftSidewalk.GetValue().Inline.IsSet())
	{
		Report.Traits.bHasLeftSidewalk = true;
	}
	if (Spec.RightSidewalk.IsSet() && Spec.RightSidewalk.GetValue().Inline.IsSet())
	{
		Report.Traits.bHasRightSidewalk = true;
	}

	Report.bValid = Report.Errors.Num() == 0;
	return Report;
}

FRoadBLDCreatePresetResult RoadBLDPresetSpecIO::WritePreset(const FRoadBLDPresetSpec& Spec, UClass* PresetClassToUpdate)
{
	using namespace RoadBLDPresetSpecIOPrivate;

	FRoadBLDCreatePresetResult Result;
	Result.Report = ValidatePresetSpec(Spec, PresetClassToUpdate);
	if (!Result.Report.bValid)
	{
		return Result;
	}

	FRoadBLDValidationReport WriteReport;
	FApplyContext Context(WriteReport, Result.WrittenAssets);
	Context.bDryRun = false;
	Context.bOverwrite = true;
	Context.AssetBaseName = SanitizeAssetName(Spec.Name);

	UClass* PresetClass = PresetClassToUpdate;
	if (!PresetClass)
	{
		bool bCreated = false;
		FString Error;
		PresetClass = RoadBLDPresetAssetFactory::CreateOrLoadBlueprintClass(
			UDynamicRoadDrawPreset::StaticClass(),
			RoadBLDPresetAssetFactory::GetPresetPackageName(Context.AssetBaseName),
			bCreated,
			Error);
		if (!PresetClass)
		{
			Context.Error(TEXT("Name"), Error);
		}
	}

	if (PresetClass)
	{
		UDynamicRoadDrawPreset* Preset = PresetClass->GetDefaultObject<UDynamicRoadDrawPreset>();
		Preset->Modify();
		InitializeTarget(Spec, PresetClassToUpdate, Preset, Context);
		ApplySpecToPreset(Spec, Preset, Context);

		FString SaveError;
		if (WriteReport.Errors.Num() == 0 && !RoadBLDPresetAssetFactory::SaveClassAsset(PresetClass, SaveError))
		{
			Context.Error(TEXT("Name"), SaveError);
		}

		if (WriteReport.Errors.Num() == 0)
		{
			Result.bSucceeded = true;
			Result.PresetId = PresetClass->GetPathName();
			Result.WrittenAssets.AddUnique(PresetClass->GetOutermost()->GetName());
			Result.Report.Traits = ComputePresetTraits(Preset);
		}
	}

	Result.Report.Errors.Append(WriteReport.Errors);
	Result.Report.bValid = Result.Report.Errors.Num() == 0;
	return Result;
}
