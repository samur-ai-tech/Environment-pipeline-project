// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/CityBLDDiscoveryToolset.h"
#include "BLDValidation.h"

#include "BLDJobRegistry.h"
#include "BLDToolsetUtils.h"
#include "CityBlock.h"
#include "CityBLDPrefab.h"
#include "CityBLDTypes.h"
#include "CityBLDUtils.h"
#include "Common/CityBLDToolsetUtils.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "ModularBuildingActor.h"
#include "Safety/CityBLDSafetyChecks.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(CityBLDDiscoveryToolset)

namespace CityBLDDiscoveryPrivate
{
	using namespace CityBLDToolsetUtils;

	const TCHAR* ToolsetName = TEXT("CityBLDDiscoveryToolset");

	/** Building pairs are only checked for overlap below this count, to keep FindCityIssues fast. */
	constexpr int32 MaxBuildingsForOverlapCheck = 4000;

	void RaiseError(const FString& Message)
	{
		BLDToolset::RaiseError(ToolsetName, Message);
	}

	int32 ClampMaxResults(const int32 MaxResults)
	{
		return FMath::Clamp(MaxResults, 1, 1000);
	}

	bool MatchesQuery(const FString& Query, std::initializer_list<const FString*> Fields)
	{
		const FString Trimmed = Query.TrimStartAndEnd();
		if (Trimmed.IsEmpty())
		{
			return true;
		}

		for (const FString* Field : Fields)
		{
			if (Field && Field->Contains(Trimmed, ESearchCase::IgnoreCase))
			{
				return true;
			}
		}
		return false;
	}

	FString FormatMeters(const double Centimeters)
	{
		return FString::Printf(TEXT("%.1f m"), Centimeters / 100.0);
	}

	FString SummarizePreset(const ECityBLDPresetKind Kind, const UClass* Class)
	{
		switch (Kind)
		{
		case ECityBLDPresetKind::District:
		{
			const UDistrict* District = Class->GetDefaultObject<UDistrict>();
			return FString::Printf(TEXT("%s subdivision, %d land uses%s, sidewalk %s"),
				*EnumToString(District->ParcelSubdivisionRules.SubdivisionMethod),
				District->LandUseClasses.Num(),
				District->CourtyardLandUseClasses.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(" + %d courtyard"), District->CourtyardLandUseClasses.Num()),
				District->SidewalkPresetClass ? *GetClassDisplayName(District->SidewalkPresetClass.Get()) : TEXT("none"));
		}

		case ECityBLDPresetKind::LandUse:
		{
			const ULandUse* LandUse = Class->GetDefaultObject<ULandUse>();
			switch (LandUse->BuildingSpawnRules)
			{
			case EBuildingSpawn::ModularBuilding:
				return FString::Printf(TEXT("Modular buildings from %d styles"), LandUse->ModularBuildingStyles.Num());
			case EBuildingSpawn::StaticBuilding:
				return FString::Printf(TEXT("Static prefabs from %d choices"), LandUse->StaticBuildingStyles.PrefabsToUse.Num());
			default:
				return TEXT("No building");
			}
		}

		case ECityBLDPresetKind::BuildingStyle:
		{
			const UBuildingStyle* Style = Class->GetDefaultObject<UBuildingStyle>();
			FString Summary = FString::Printf(TEXT("%s-%s tall"),
				*FormatMeters(Style->SpawnRules.MinHeight), *FormatMeters(Style->SpawnRules.MaxHeight));
			if (Style->RoofStyle)
			{
				Summary += FString::Printf(TEXT(", %s roof"), *EnumToString(Style->RoofStyle.GetDefaultObject()->Type));
			}
			const FString Description = Style->StyleDescription.TrimStartAndEnd();
			if (!Description.IsEmpty())
			{
				Summary += TEXT(". ") + Description.Left(160);
			}
			return Summary;
		}

		case ECityBLDPresetKind::RoofStyle:
		{
			const URoofStyle* Roof = Class->GetDefaultObject<URoofStyle>();
			return Roof->Type == ERoofType::Flat
				? FString(TEXT("Flat roof"))
				: FString::Printf(TEXT("%s roof, ridge %s"), *EnumToString(Roof->Type), *FormatMeters(Roof->RidgeHeight));
		}

		case ECityBLDPresetKind::SidewalkPreset:
		{
			const USidewalkPreset* Sidewalk = Class->GetDefaultObject<USidewalkPreset>();
			return FString::Printf(TEXT("Default width %s%s"),
				*FormatMeters(Sidewalk->DefaultSidewalkWidth), Sidewalk->SidewalkPCG ? TEXT(", PCG details") : TEXT(""));
		}

		case ECityBLDPresetKind::GroundFloorType:
			return Class->GetDefaultObject<UGroundFloorType>()->Description.TrimStartAndEnd().Left(160);

		case ECityBLDPresetKind::Prefab:
		{
			const ACityBLDPrefab* Prefab = Class->GetDefaultObject<ACityBLDPrefab>();
			if (IsValid(Prefab->BoundingBox))
			{
				const FVector Size = Prefab->BoundingBox->GetUnscaledBoxExtent() * 2.0;
				return FString::Printf(TEXT("Footprint %.1f x %.1f m (depth x width)"), Size.X / 100.0, Size.Y / 100.0);
			}
			return TEXT("No bounding box; cannot be fitted to parcels");
		}

		default:
			return FString();
		}
	}

	FCityBLDPresetInfo MakePresetInfo(const ECityBLDPresetKind Kind, const UClass* Class)
	{
		FCityBLDPresetInfo Info;
		Info.Kind = Kind;
		Info.Class = MakeClassRef(Class);
		Info.AssetPath = GetAssetPath(Class);
		Info.Summary = SummarizePreset(Kind, Class);
		Info.bIsSampleContent = Info.Class.ClassPath.StartsWith(TEXT("/CityBLD/"));
		return Info;
	}

	TArray<FCityBLDWeightedClass> MakeWeightedClasses(const TMap<TSubclassOf<ULandUse>, double>& Weights, int32& OutNullEntries)
	{
		double TotalWeight = 0.0;
		for (const TPair<TSubclassOf<ULandUse>, double>& Pair : Weights)
		{
			if (Pair.Key)
			{
				TotalWeight += FMath::Max(Pair.Value, 0.0);
			}
		}

		TArray<FCityBLDWeightedClass> Result;
		for (const TPair<TSubclassOf<ULandUse>, double>& Pair : Weights)
		{
			if (!Pair.Key)
			{
				++OutNullEntries;
				continue;
			}

			FCityBLDWeightedClass& Entry = Result.AddDefaulted_GetRef();
			Entry.Class = MakeClassRef(Pair.Key.Get());
			Entry.Weight = Pair.Value;
			Entry.Share = TotalWeight > 0.0 ? FMath::Max(Pair.Value, 0.0) / TotalWeight : 0.0;
		}

		Result.Sort([](const FCityBLDWeightedClass& A, const FCityBLDWeightedClass& B)
		{
			return A.Weight > B.Weight;
		});
		return Result;
	}

	bool IsSkeletonRisk(const ACityBlock* Block)
	{
		return Block->DistrictClass
			&& CityBLDSafetyChecks::DoesDistrictUseSkeletonSubdivision(Block->DistrictClass.Get())
			&& CityBLDSafetyChecks::IsCityBlockOverSkeletonSegmentThreshold(Block);
	}

	TArray<AActor*> GetLoadedParcelChildren(const UCityParcel* Parcel, UWorld* World)
	{
		TArray<AActor*> Children;
		for (const FParcelActorEntry& Entry : Parcel->ChildActors)
		{
			if (AActor* Child = Entry.TryGetActor(World))
			{
				Children.Add(Child);
			}
		}
		return Children;
	}

	FCityBLDBlockSummary MakeBlockSummary(ACityBlock* Block)
	{
		FCityBLDBlockSummary Summary;
		UWorld* World = Block->GetWorld();

		const TArray<FVector> Outline = GetBlockOutline(Block);
		Summary.Actor = BLDToolset::MakeActorRef(Block);
		Summary.District = MakeClassRef(Block->DistrictClass.Get());
		Summary.OutlineVertexCount = Outline.Num();
		Summary.AreaSquareMeters = PolygonArea2D(Outline) / 10000.0;
		Summary.Centroid = Outline.IsEmpty() ? Block->GetActorLocation() : PolygonCentroid(Outline);
		Summary.Bounds = MakeBounds(GetBlockBounds(Block));
		Summary.SidewalkWidthMeters = Block->SidewalkWidth / 100.0;
		Summary.ParcelCount = Block->Parcels.Num();
		Summary.bHasBlockGeometry = Block->HasCityBlockGeo();
		Summary.bGenerated = Summary.ParcelCount > 0 || Summary.bHasBlockGeometry;
		Summary.bSkeletonRisk = IsSkeletonRisk(Block);

		for (const UCityParcel* Parcel : Block->Parcels)
		{
			if (!IsValid(Parcel))
			{
				continue;
			}

			for (const AActor* Child : GetLoadedParcelChildren(Parcel, World))
			{
				if (Child->IsA<AModularBuildingActor>())
				{
					++Summary.BuildingCount;
				}
			}
		}
		return Summary;
	}

	FCityBLDParcelInfo MakeParcelInfo(const UCityParcel* Parcel, const int32 Index, UWorld* World, const bool bIncludeShape)
	{
		FCityBLDParcelInfo Info;
		Info.Index = Index;
		if (!IsValid(Parcel))
		{
			return Info;
		}

		Info.LandUse = MakeClassRef(Parcel->LandUseClass.Get());
		Info.bIsCourtyard = Parcel->bIsCourtyard;
		Info.AreaSquareMeters = PolygonArea2D(Parcel->ShapePoints) / 10000.0;
		Info.Centroid = PolygonCentroid(Parcel->ShapePoints);
		Info.StreetEdgeCount = Parcel->FindStreetEdges().Num();
		Info.RegisteredChildCount = Parcel->ChildActors.Num();
		if (bIncludeShape)
		{
			Info.ShapePoints = Parcel->ShapePoints;
		}

		for (const AActor* Child : GetLoadedParcelChildren(Parcel, World))
		{
			Info.ChildActors.Add(BLDToolset::MakeActorRef(Child));
		}
		return Info;
	}

	FCityBLDBuildingSummary MakeBuildingSummary(const AModularBuildingActor* Building, const TMap<const AActor*, FParcelOwner>& Owners)
	{
		FCityBLDBuildingSummary Summary;
		const TArray<FVector> Footprint = GetBuildingFootprintWorld(Building);

		Summary.Actor = BLDToolset::MakeActorRef(Building);
		Summary.Style = MakeClassRef(Building->Style.Get());
		Summary.HeightMeters = Building->BuildingHeight / 100.0;
		Summary.FloorCount = Building->FloorHeights.Num();
		Summary.FootprintVertexCount = Footprint.Num();
		Summary.FootprintAreaSquareMeters = PolygonArea2D(Footprint) / 10000.0;
		Summary.Location = Building->GetActorLocation();
		Summary.bValid = Building->Style && Footprint.Num() >= 3 && Building->IsValidBuilding();

		if (const FParcelOwner* Owner = Owners.Find(Building))
		{
			Summary.OwningBlock = BLDToolset::MakeActorRef(Owner->Block);
			Summary.ParcelIndex = Owner->ParcelIndex;
		}
		return Summary;
	}

	FCityBLDIssue& AddIssue(
		TArray<FCityBLDIssue>& Issues,
		const ECityBLDIssueSeverity Severity,
		const TCHAR* Code,
		const FString& Message,
		const AActor* Actor,
		const FVector& Location,
		const FString& Fix)
	{
		FCityBLDIssue& Issue = Issues.AddDefaulted_GetRef();
		Issue.Severity = Severity;
		Issue.Code = Code;
		Issue.Message = Message;
		Issue.Actor = BLDToolset::MakeActorRef(Actor);
		Issue.Location = Location;
		Issue.Fix = Fix;
		return Issue;
	}
}

FCityBLDCityContext UCityBLDDiscoveryToolset::GetCityContext()
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDCityContext Context;
	Context.LicenseState = GetLicenseStateName();
	Context.bCanEdit = EnsureAuthorized(Context.LicenseMessage);
	Context.RunningJobs = FBLDJobRegistry::Get().ListJobs(TEXT("CityBLD."), true);

	for (int32 KindIndex = 0; KindIndex <= static_cast<int32>(ECityBLDPresetKind::Prefab); ++KindIndex)
	{
		const ECityBLDPresetKind Kind = static_cast<ECityBLDPresetKind>(KindIndex);
		FCityBLDPresetCount& Count = Context.PresetCounts.AddDefaulted_GetRef();
		Count.Kind = Kind;
		Count.Count = DiscoverPresetClasses(Kind).Num();
	}

	UWorld* World = BLDToolset::GetEditorWorld();
	if (!IsValid(World))
	{
		Context.Notes.Add(TEXT("No editor world is loaded. Open a level first."));
		return Context;
	}

	Context.LevelName = World->GetMapName();

	FBox CityBox(ForceInit);
	TMap<UClass*, int32> DistrictUsage;
	TMap<UClass*, int32> StyleUsage;

	for (ACityBlock* Block : GetBlocks(World))
	{
		++Context.BlockCount;
		Context.ParcelCount += Block->Parcels.Num();
		CityBox += GetBlockBounds(Block);

		if (Block->Parcels.Num() > 0 || Block->HasCityBlockGeo())
		{
			++Context.GeneratedBlockCount;
		}

		if (!Block->DistrictClass)
		{
			++Context.BlocksWithoutDistrict;
		}
		else
		{
			++DistrictUsage.FindOrAdd(Block->DistrictClass.Get());
		}

		if (IsSkeletonRisk(Block))
		{
			++Context.SkeletonRiskBlockCount;
		}
	}

	const TMap<const AActor*, FParcelOwner> Owners = BuildParcelOwnerMap(World);
	for (const AModularBuildingActor* Building : GetBuildings(World))
	{
		++Context.ModularBuildingCount;
		CityBox += Building->GetActorLocation();

		if (!Owners.Contains(Building))
		{
			++Context.UnparentedBuildingCount;
		}

		if (Building->Style)
		{
			++StyleUsage.FindOrAdd(Building->Style.Get());
		}
	}

	Context.bHasCityBounds = CityBox.IsValid != 0;
	Context.CityBounds = MakeBounds(CityBox);

	const auto AppendUsage = [](const TMap<UClass*, int32>& Usage, TArray<FCityBLDClassUsage>& Out)
	{
		for (const TPair<UClass*, int32>& Pair : Usage)
		{
			FCityBLDClassUsage& Entry = Out.AddDefaulted_GetRef();
			Entry.Class = MakeClassRef(Pair.Key);
			Entry.Count = Pair.Value;
		}
		Out.Sort([](const FCityBLDClassUsage& A, const FCityBLDClassUsage& B)
		{
			return A.Count > B.Count;
		});
	};
	AppendUsage(DistrictUsage, Context.DistrictsInUse);
	AppendUsage(StyleUsage, Context.StylesInUse);

	if (Context.BlockCount == 0 && Context.ModularBuildingCount == 0)
	{
		Context.Notes.Add(TEXT("The level has no CityBLD content. Pick a District with ListPresets(Kind=District) and DescribeDistrict before creating blocks."));
	}
	if (Context.BlocksWithoutDistrict > 0)
	{
		Context.Notes.Add(FString::Printf(TEXT("%d blocks have no District and cannot generate. Run FindCityIssues for the list."), Context.BlocksWithoutDistrict));
	}
	if (Context.BlockCount > Context.GeneratedBlockCount)
	{
		Context.Notes.Add(FString::Printf(TEXT("%d blocks are not generated yet."), Context.BlockCount - Context.GeneratedBlockCount));
	}
	if (Context.SkeletonRiskBlockCount > 0)
	{
		Context.Notes.Add(FString::Printf(TEXT("%d blocks use Skeleton subdivision on complex outlines; generating them can take a long time."), Context.SkeletonRiskBlockCount));
	}
	if (!Context.bCanEdit)
	{
		Context.Notes.Add(FString::Printf(TEXT("CityBLD edits are blocked: %s"), *Context.LicenseMessage));
	}
	return Context;
}

FCityBLDPresetList UCityBLDDiscoveryToolset::ListPresets(const ECityBLDPresetKind Kind, const FString& Query, const int32 MaxResults)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDPresetList Result;
	const int32 Limit = ClampMaxResults(MaxResults);

	for (const UClass* Class : DiscoverPresetClasses(Kind))
	{
		FCityBLDPresetInfo Info = MakePresetInfo(Kind, Class);
		if (!MatchesQuery(Query, { &Info.Class.DisplayName, &Info.Class.ClassPath, &Info.Summary }))
		{
			continue;
		}

		++Result.TotalCount;
		if (Result.Presets.Num() < Limit)
		{
			Result.Presets.Add(MoveTemp(Info));
		}
	}

	Result.ReturnedCount = Result.Presets.Num();
	return Result;
}

FCityBLDDistrictDescription UCityBLDDiscoveryToolset::DescribeDistrict(TSubclassOf<UDistrict> District)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDDistrictDescription Result;
	if (!District)
	{
		RaiseError(TEXT("District is required. Pass a ClassPath from ListPresets(Kind=District)."));
		return Result;
	}

	const UDistrict* CDO = District->GetDefaultObject<UDistrict>();
	Result.Preset = MakePresetInfo(ECityBLDPresetKind::District, District.Get());
	Result.SubdivisionRules = CDO->ParcelSubdivisionRules;
	Result.bUsesSkeletonSubdivision = CityBLDSafetyChecks::DoesDistrictUseSkeletonSubdivision(District.Get());

	int32 NullLandUses = 0;
	Result.LandUses = MakeWeightedClasses(CDO->LandUseClasses, NullLandUses);
	Result.CourtyardLandUses = MakeWeightedClasses(CDO->CourtyardLandUseClasses, NullLandUses);

	if (CDO->SidewalkPresetClass)
	{
		Result.SidewalkPreset = MakeClassRef(CDO->SidewalkPresetClass.Get());
		Result.DefaultSidewalkWidthMeters = CDO->SidewalkPresetClass.GetDefaultObject()->DefaultSidewalkWidth / 100.0;
	}

	// Read through reflection so this module does not need the PCG plugin's headers.
	if (const FObjectPropertyBase* GraphProperty = FindFProperty<FObjectPropertyBase>(UDistrict::StaticClass(), GET_MEMBER_NAME_CHECKED(UDistrict, DistrictPCGGraph)))
	{
		Result.PCGGraphPath = GetPathNameSafe(GraphProperty->GetObjectPropertyValue_InContainer(CDO));
	}
	Result.MaterialPath = GetPathNameSafe(CDO->DistrictMaterial.Get());
	Result.ParcelZOffset = CDO->ParcelZOffset;

	if (UWorld* World = BLDToolset::GetEditorWorld())
	{
		for (const ACityBlock* Block : GetBlocks(World))
		{
			if (Block->DistrictClass.Get() == District.Get())
			{
				++Result.BlocksInLevel;
			}
		}
	}

	if (Result.LandUses.IsEmpty())
	{
		Result.Notes.Add(TEXT("No land uses: parcels will be created but nothing will spawn on them."));
	}
	if (NullLandUses > 0)
	{
		Result.Notes.Add(FString::Printf(TEXT("%d land use entries are empty and are skipped."), NullLandUses));
	}
	if (CDO->ParcelSubdivisionRules.SubdivisionMethod == ESubdivisionMethods::OffsetWithCourtyard && Result.CourtyardLandUses.IsEmpty())
	{
		Result.Notes.Add(TEXT("OffsetWithCourtyard subdivision but no courtyard land uses: courtyard parcels stay empty."));
	}
	if (Result.bUsesSkeletonSubdivision)
	{
		Result.Notes.Add(TEXT("Skeleton subdivision is slow on blocks with more than 6 simplified outline points. Prefer simple outlines or raise the block's MinSegmentLength."));
	}
	if (!CDO->SidewalkPresetClass)
	{
		Result.Notes.Add(TEXT("No sidewalk preset: blocks get no sidewalk inset and use their own sidewalk preset, if any."));
	}
	return Result;
}

FCityBLDLandUseDescription UCityBLDDiscoveryToolset::DescribeLandUse(TSubclassOf<ULandUse> LandUse)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDLandUseDescription Result;
	if (!LandUse)
	{
		RaiseError(TEXT("LandUse is required. Pass a ClassPath from ListPresets(Kind=LandUse) or DescribeDistrict."));
		return Result;
	}

	const ULandUse* CDO = LandUse->GetDefaultObject<ULandUse>();
	Result.Preset = MakePresetInfo(ECityBLDPresetKind::LandUse, LandUse.Get());
	Result.BuildingSpawnRule = CDO->BuildingSpawnRules;
	Result.bGenerateMesh = CDO->bGenerateMesh;
	Result.ParcelMaterialPath = GetPathNameSafe(CDO->ParcelMaterial.Get());
	Result.DisplacementAmount = CDO->DisplacementAmount;
	Result.SeedOffset = CDO->SeedOffset;

	for (const TSubclassOf<UBuildingStyle>& Style : CDO->ModularBuildingStyles)
	{
		if (Style)
		{
			Result.ModularBuildingStyles.Add(MakeClassRef(Style.Get()));
		}
	}

	const FStaticBuildingSpawnRules& StaticRules = CDO->StaticBuildingStyles;
	for (const TSubclassOf<AActor>& Prefab : StaticRules.PrefabsToUse)
	{
		if (Prefab)
		{
			Result.StaticPrefabs.Add(MakeClassRef(Prefab.Get()));
		}
	}
	Result.bUsePrefabFitting = StaticRules.bUsePrefabFitting;
	Result.StaticSpawnPositioning = StaticRules.SpawnPositioning;
	Result.ParcelEdgeClearance = StaticRules.ParcelEdgeClearance;

	for (const UClass* DistrictClass : DiscoverPresetClasses(ECityBLDPresetKind::District))
	{
		const UDistrict* District = DistrictClass->GetDefaultObject<UDistrict>();
		if (District->LandUseClasses.Contains(LandUse) || District->CourtyardLandUseClasses.Contains(LandUse))
		{
			Result.UsedByDistricts.Add(MakeClassRef(DistrictClass));
		}
	}

	if (UWorld* World = BLDToolset::GetEditorWorld())
	{
		for (const ACityBlock* Block : GetBlocks(World))
		{
			for (const UCityParcel* Parcel : Block->Parcels)
			{
				if (IsValid(Parcel) && Parcel->LandUseClass.Get() == LandUse.Get())
				{
					++Result.ParcelsInLevel;
				}
			}
		}
	}

	if (CDO->BuildingSpawnRules == EBuildingSpawn::ModularBuilding && Result.ModularBuildingStyles.IsEmpty())
	{
		Result.Notes.Add(TEXT("Spawns modular buildings but lists no building styles, so parcels stay empty."));
	}
	if (CDO->BuildingSpawnRules == EBuildingSpawn::StaticBuilding && Result.StaticPrefabs.IsEmpty())
	{
		Result.Notes.Add(TEXT("Spawns static buildings but lists no prefabs, so parcels stay empty."));
	}
	if (CDO->BuildingSpawnRules == EBuildingSpawn::ModularBuilding && Result.ModularBuildingStyles.Num() > 1)
	{
		Result.Notes.Add(TEXT("The style for each parcel is picked with an unseeded random number, so regenerating changes which style each parcel gets."));
	}
	if (Result.UsedByDistricts.IsEmpty())
	{
		Result.Notes.Add(TEXT("No district references this land use; it is only applied by assigning it to parcels directly."));
	}
	return Result;
}

FCityBLDBuildingStyleDescription UCityBLDDiscoveryToolset::DescribeBuildingStyle(TSubclassOf<UBuildingStyle> Style)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDBuildingStyleDescription Result;
	if (!Style)
	{
		RaiseError(TEXT("Style is required. Pass a ClassPath from ListPresets(Kind=BuildingStyle) or DescribeLandUse."));
		return Result;
	}

	const UBuildingStyle* CDO = Style->GetDefaultObject<UBuildingStyle>();
	Result.Preset = MakePresetInfo(ECityBLDPresetKind::BuildingStyle, Style.Get());
	Result.StyleDescription = CDO->StyleDescription;
	Result.MinHeightMeters = CDO->SpawnRules.MinHeight / 100.0;
	Result.MaxHeightMeters = CDO->SpawnRules.MaxHeight / 100.0;
	Result.LayeringType = CDO->SpawnRules.LayeringType;
	Result.FacadeFloorDefinitions = CDO->FacadeMeshSet.Floors.Num();
	Result.SideFloorDefinitions = CDO->SideMeshSet.Floors.Num();
	Result.RearFloorDefinitions = CDO->RearMeshSet.Floors.Num();
	Result.bUseSideMeshSetForRearFaces = CDO->UseSideMeshSetForRearFaces;
	Result.bAddTrim = CDO->AddTrim;
	Result.bOverrideTopFloor = CDO->OverrideTopFloor;
	Result.RandomizedMaterialSlots = CDO->RandomizedMaterials.Num();
	Result.bHasHLODMaterial = CDO->HLODMaterial != nullptr;

	if (CDO->RoofStyle)
	{
		const URoofStyle* Roof = CDO->RoofStyle.GetDefaultObject();
		Result.RoofStyle = MakeClassRef(CDO->RoofStyle.Get());
		Result.RoofType = Roof->Type;
		Result.RoofRidgeHeightMeters = Roof->RidgeHeight / 100.0;
	}

	const double MinHeight = CDO->SpawnRules.MinHeight;
	const double MaxHeight = FMath::Max(CDO->SpawnRules.MaxHeight, MinHeight);
	for (const double Height : { MinHeight, (MinHeight + MaxHeight) * 0.5, MaxHeight })
	{
		if (Height <= 0.0 || Result.FloorSamples.ContainsByPredicate([Height](const FCityBLDFloorSample& Sample) { return FMath::IsNearlyEqual(Sample.HeightMeters, Height / 100.0); }))
		{
			continue;
		}

		FCityBLDFloorSample& Sample = Result.FloorSamples.AddDefaulted_GetRef();
		Sample.HeightMeters = Height / 100.0;
		Sample.Floors = UCityBLDUtils::GetBestNumFloorsForHeight(Style, static_cast<float>(Height));
	}

	for (const UClass* LandUseClass : DiscoverPresetClasses(ECityBLDPresetKind::LandUse))
	{
		const ULandUse* LandUse = LandUseClass->GetDefaultObject<ULandUse>();
		const bool bUsesStyle = LandUse->ModularBuildingStyles.ContainsByPredicate([&Style](const TSubclassOf<UBuildingStyle>& Candidate)
		{
			return Candidate.Get() == Style.Get();
		});
		if (bUsesStyle)
		{
			Result.UsedByLandUses.Add(MakeClassRef(LandUseClass));
		}
	}

	if (UWorld* World = BLDToolset::GetEditorWorld())
	{
		for (const AModularBuildingActor* Building : GetBuildings(World))
		{
			if (Building->Style.Get() == Style.Get())
			{
				++Result.BuildingsInLevel;
			}
		}
	}

	if (Result.FacadeFloorDefinitions == 0)
	{
		Result.Notes.Add(TEXT("The facade mesh set has no floors, so buildings with this style generate no walls."));
	}
	if (!CDO->RoofStyle)
	{
		Result.Notes.Add(TEXT("No roof style: buildings get no roof unless they have a roof override."));
	}
	if (CDO->SpawnRules.MaxHeight < CDO->SpawnRules.MinHeight)
	{
		Result.Notes.Add(TEXT("MaxHeight is below MinHeight in the style's spawn rules."));
	}
	return Result;
}

FCityBLDBlockList UCityBLDDiscoveryToolset::ListCityBlocks(TOptional<FCityBLDBounds> Bounds, const int32 MaxResults)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDBlockList Result;
	FString Error;
	if (!ValidateBounds(Bounds, Error))
	{
		RaiseError(Error);
		return Result;
	}

	UWorld* World = GetEditorWorldOrRaise(ToolsetName);
	if (!World)
	{
		return Result;
	}

	const int32 Limit = ClampMaxResults(MaxResults);
	for (ACityBlock* Block : GetBlocks(World, Bounds))
	{
		++Result.TotalCount;
		if (Result.Blocks.Num() < Limit)
		{
			Result.Blocks.Add(MakeBlockSummary(Block));
		}
	}

	Result.ReturnedCount = Result.Blocks.Num();
	return Result;
}

FCityBLDBlockDescription UCityBLDDiscoveryToolset::DescribeBlock(ACityBlock* Block, const bool bIncludeOutline, const bool bIncludeParcels)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDBlockDescription Result;
	if (!IsValid(Block))
	{
		RaiseError(TEXT("Block is required. Pass {\"refPath\": ...} from ListCityBlocks."));
		return Result;
	}

	UWorld* World = Block->GetWorld();
	Result.Summary = MakeBlockSummary(Block);
	Result.BlockSidewalkPreset = MakeClassRef(Block->SidewalkPresetClass.Get());
	Result.EffectiveSidewalkPreset = Block->DistrictClass
		? MakeClassRef(Block->DistrictClass.GetDefaultObject()->SidewalkPresetClass.Get())
		: Result.BlockSidewalkPreset;
	Result.MinSegmentLength = Block->MinSegmentLength;
	Result.MaxParcelSplineDeviation = Block->MaxParcelSplineDeviation;
	Result.CityBlockGeoZOffset = Block->CityBlockGeoZOffset;
	Result.InnerLoopVertexCount = IsValid(Block->InnerLoop) ? Block->InnerLoop->GetNumberOfSplinePoints() : 0;
	Result.ParcelSplineVertexCount = IsValid(Block->ParcelGenerationSpline) ? Block->ParcelGenerationSpline->GetNumberOfSplinePoints() : 0;

	if (bIncludeOutline)
	{
		Result.Outline = GetBlockOutline(Block);
	}

	TMap<UClass*, int32> LandUseCounts;
	int32 MissingLandUse = 0;
	for (int32 Index = 0; Index < Block->Parcels.Num(); ++Index)
	{
		const UCityParcel* Parcel = Block->Parcels[Index];
		if (!IsValid(Parcel))
		{
			continue;
		}

		if (Parcel->LandUseClass)
		{
			++LandUseCounts.FindOrAdd(Parcel->LandUseClass.Get());
		}
		else
		{
			++MissingLandUse;
		}

		if (bIncludeParcels)
		{
			Result.Parcels.Add(MakeParcelInfo(Parcel, Index, World, false));
		}
	}

	for (const TPair<UClass*, int32>& Pair : LandUseCounts)
	{
		FCityBLDClassUsage& Usage = Result.LandUseCounts.AddDefaulted_GetRef();
		Usage.Class = MakeClassRef(Pair.Key);
		Usage.Count = Pair.Value;
	}
	Result.LandUseCounts.Sort([](const FCityBLDClassUsage& A, const FCityBLDClassUsage& B)
	{
		return A.Count > B.Count;
	});

	if (!Block->DistrictClass)
	{
		Result.Notes.Add(TEXT("No District: the block cannot generate."));
	}
	if (!Result.Summary.bGenerated)
	{
		Result.Notes.Add(TEXT("Not generated yet."));
	}
	if (Result.Summary.bSkeletonRisk)
	{
		Result.Notes.Add(FString::Printf(TEXT("Skeleton subdivision with %d simplified outline points may be slow."), Result.ParcelSplineVertexCount));
	}
	if (MissingLandUse > 0)
	{
		Result.Notes.Add(FString::Printf(TEXT("%d parcels have no land use."), MissingLandUse));
	}
	if (Block->DistrictClass && Block->SidewalkPresetClass && Block->SidewalkPresetClass.Get() != Block->DistrictClass.GetDefaultObject()->SidewalkPresetClass.Get())
	{
		Result.Notes.Add(TEXT("The block's own sidewalk preset is ignored because the District decides the sidewalk."));
	}
	return Result;
}

FCityBLDParcelList UCityBLDDiscoveryToolset::ListParcels(ACityBlock* Block, const FString& LandUseFilter, const bool bIncludeShapes)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDParcelList Result;
	if (!IsValid(Block))
	{
		RaiseError(TEXT("Block is required. Pass {\"refPath\": ...} from ListCityBlocks."));
		return Result;
	}

	UWorld* World = Block->GetWorld();
	Result.Block = BLDToolset::MakeActorRef(Block);
	Result.TotalCount = Block->Parcels.Num();

	for (int32 Index = 0; Index < Block->Parcels.Num(); ++Index)
	{
		const UCityParcel* Parcel = Block->Parcels[Index];
		if (!IsValid(Parcel))
		{
			continue;
		}

		FCityBLDParcelInfo Info = MakeParcelInfo(Parcel, Index, World, bIncludeShapes);
		if (MatchesQuery(LandUseFilter, { &Info.LandUse.DisplayName, &Info.LandUse.ClassPath }))
		{
			Result.Parcels.Add(MoveTemp(Info));
		}
	}
	return Result;
}

FCityBLDBuildingList UCityBLDDiscoveryToolset::ListModularBuildings(TOptional<FCityBLDBounds> Bounds, const FString& StyleFilter, const int32 MaxResults)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDBuildingList Result;
	FString Error;
	if (!ValidateBounds(Bounds, Error))
	{
		RaiseError(Error);
		return Result;
	}

	UWorld* World = GetEditorWorldOrRaise(ToolsetName);
	if (!World)
	{
		return Result;
	}

	const int32 Limit = ClampMaxResults(MaxResults);
	const TMap<const AActor*, FParcelOwner> Owners = BuildParcelOwnerMap(World);

	for (const AModularBuildingActor* Building : GetBuildings(World, Bounds))
	{
		const FCityBLDClassRef Style = MakeClassRef(Building->Style.Get());
		if (!MatchesQuery(StyleFilter, { &Style.DisplayName, &Style.ClassPath }))
		{
			continue;
		}

		++Result.TotalCount;
		if (Result.Buildings.Num() < Limit)
		{
			Result.Buildings.Add(MakeBuildingSummary(Building, Owners));
		}
	}

	Result.ReturnedCount = Result.Buildings.Num();
	return Result;
}

FCityBLDBuildingDescription UCityBLDDiscoveryToolset::DescribeBuilding(AModularBuildingActor* Building)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDBuildingDescription Result;
	if (!IsValid(Building))
	{
		RaiseError(TEXT("Building is required. Pass {\"refPath\": ...} from ListModularBuildings."));
		return Result;
	}

	Result.Summary = MakeBuildingSummary(Building, BuildParcelOwnerMap(Building->GetWorld()));
	Result.FootprintWorld = GetBuildingFootprintWorld(Building);
	Result.FloorHeights = Building->FloorHeights;
	Result.GroundFloorOverride = MakeClassRef(Building->GroundFloorOverrideClass.Get());
	Result.SignText = Building->SignText;
	Result.Collision = Building->GenerationParameters.Collision;
	Result.MeshGenerationType = Building->GenerationParameters.MeshGenerationType;
	Result.bGenerateFoundations = Building->GenerationParameters.bGenerateFoundations;
	Result.bGenerateRooftops = Building->GenerationParameters.bGenerateRooftops;
	Result.bAllFloorsFacade = Building->bAllFloorsFacade;
	Result.bPreciseHeight = Building->bPreciseHeight;
	Result.bTwinBLDUpperFloorsPreferFacade = Building->bTwinBLDUpperFloorsPreferFacade;
	Result.NumBasementFloors = Building->NumBasementFloors;
	Result.Seed = Building->Seed.GetInitialSeed();
	Result.StreetFacingFaces = Building->StreetFacingFaces;
	Result.bHasRoofOverride = Building->RoofOverride.IsSet();
	Result.RoofOverride = Building->RoofOverride;
	Result.bUseAuthoredFloorPlates = Building->bUseAuthoredFloorPlates;

	for (const FAuthoredFloorPlate& Plate : Building->AuthoredFloorPlates)
	{
		FCityBLDFloorPlateInfo& Info = Result.FloorPlates.AddDefaulted_GetRef();
		Info.StartHeightMeters = Plate.StartHeight / 100.0;
		Info.bHasRoofOverride = Plate.RoofOverride.IsSet();
		for (const FAuthoredBuildingShell& Shell : Plate.Shells)
		{
			Info.ShellVertexCounts.Add(Shell.PerimeterVertices.Num());
		}
	}

	if (Building->Style && Building->BuildingHeight > 0.0f)
	{
		Result.StyleFloorsForHeight = UCityBLDUtils::GetBestNumFloorsForHeight(Building->Style, Building->BuildingHeight);
	}

	if (!Building->Style)
	{
		Result.Notes.Add(TEXT("No building style: the building cannot generate."));
	}
	if (Result.FootprintWorld.Num() < 3)
	{
		Result.Notes.Add(TEXT("The footprint has fewer than 3 points."));
	}
	if (Building->BuildingHeight <= 0.0f)
	{
		Result.Notes.Add(TEXT("No explicit height: a random height from the style's range is used on each generation."));
	}
	if (Result.Summary.ParcelIndex != INDEX_NONE)
	{
		Result.Notes.Add(TEXT("Spawned by a parcel: regenerating that block or parcel replaces this building and discards manual edits."));
	}
	if (!Building->bUseAuthoredFloorPlates && !Building->AuthoredFloorPlates.IsEmpty())
	{
		Result.Notes.Add(TEXT("Has authored floor plates, but bUseAuthoredFloorPlates is off so they are ignored."));
	}
	if (Building->StreetFacingFaces.IsEmpty() && !Building->bAllFloorsFacade)
	{
		Result.Notes.Add(TEXT("No street-facing faces recorded; facade meshes may only appear where street edges were detected at generation."));
	}
	return Result;
}

FCityBLDIssueReport UCityBLDDiscoveryToolset::FindCityIssues(TOptional<FCityBLDBounds> Bounds, const int32 MaxResults)
{
	using namespace CityBLDDiscoveryPrivate;

	FCityBLDIssueReport Report;
	FString Error;
	if (!ValidateBounds(Bounds, Error))
	{
		RaiseError(Error);
		return Report;
	}

	UWorld* World = GetEditorWorldOrRaise(ToolsetName);
	if (!World)
	{
		return Report;
	}

	TArray<FCityBLDIssue> Issues;
	const TArray<ACityBlock*> Blocks = GetBlocks(World, Bounds);
	Report.BlocksChecked = Blocks.Num();

	TArray<TArray<FVector>> BlockOutlines;
	BlockOutlines.Reserve(Blocks.Num());

	for (ACityBlock* Block : Blocks)
	{
		const TArray<FVector>& Outline = BlockOutlines.Add_GetRef(GetBlockOutline(Block));
		const FVector Centroid = Outline.IsEmpty() ? Block->GetActorLocation() : PolygonCentroid(Outline);

		if (Outline.Num() < 3 || PolygonArea2D(Outline) < 10000.0)
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Error, TEXT("BlockOutlineDegenerate"),
				FString::Printf(TEXT("The block outline has %d points and %.2f m2 of area."), Outline.Num(), PolygonArea2D(Outline) / 10000.0),
				Block, Centroid, TEXT("Give the block a closed outline of at least 3 points, or delete it."));
			continue;
		}

		if (IsPolygonSelfIntersecting2D(Outline))
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Error, TEXT("BlockOutlineSelfIntersecting"),
				TEXT("The block outline crosses itself, so subdivision and sidewalk insets will be wrong."),
				Block, Centroid, TEXT("Reorder or move the outline points so the edges do not cross."));
		}

		if (!Block->DistrictClass)
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Error, TEXT("BlockMissingDistrict"),
				TEXT("The block has no District, so generating it does nothing."),
				Block, Centroid, TEXT("Assign a District (see ListPresets Kind=District), then generate the block."));
		}
		else if (Block->Parcels.IsEmpty())
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Warning, TEXT("BlockNotGenerated"),
				TEXT("The block has a District but no parcels yet."),
				Block, Centroid, TEXT("Generate the block."));
		}

		if (IsSkeletonRisk(Block))
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Warning, TEXT("BlockSkeletonRisk"),
				FString::Printf(TEXT("Skeleton subdivision on %d simplified outline points can take a long time."),
					IsValid(Block->ParcelGenerationSpline) ? Block->ParcelGenerationSpline->GetNumberOfSplinePoints() : 0),
				Block, Centroid, TEXT("Use a District with another subdivision method, simplify the outline, or raise MinSegmentLength."));
		}

		for (int32 ParcelIndex = 0; ParcelIndex < Block->Parcels.Num(); ++ParcelIndex)
		{
			const UCityParcel* Parcel = Block->Parcels[ParcelIndex];
			if (!IsValid(Parcel))
			{
				continue;
			}

			const FVector ParcelCentroid = PolygonCentroid(Parcel->ShapePoints);
			if (!Parcel->LandUseClass)
			{
				AddIssue(Issues, ECityBLDIssueSeverity::Warning, TEXT("ParcelMissingLandUse"),
					TEXT("The parcel has no land use, so nothing spawns on it."),
					Block, ParcelCentroid, TEXT("Assign a land use to the parcel or regenerate the block.")).ParcelIndex = ParcelIndex;
				continue;
			}

			const ULandUse* LandUse = Parcel->LandUseClass.GetDefaultObject();
			const bool bExpectsBuilding = LandUse->BuildingSpawnRules != EBuildingSpawn::NoBuilding;
			if (bExpectsBuilding && Parcel->ChildActors.IsEmpty())
			{
				const bool bHasChoices = LandUse->BuildingSpawnRules == EBuildingSpawn::ModularBuilding
					? !LandUse->ModularBuildingStyles.IsEmpty()
					: !LandUse->StaticBuildingStyles.PrefabsToUse.IsEmpty();

				AddIssue(Issues, ECityBLDIssueSeverity::Warning, TEXT("ParcelMissingBuilding"),
					bHasChoices
						? FString::Printf(TEXT("Land use %s should spawn a building here, but the parcel has none."), *GetClassDisplayName(Parcel->LandUseClass.Get()))
						: FString::Printf(TEXT("Land use %s spawns buildings but lists no styles or prefabs."), *GetClassDisplayName(Parcel->LandUseClass.Get())),
					Block, ParcelCentroid,
					bHasChoices
						? TEXT("Regenerate the parcel. If it stays empty, the parcel may be too small or oddly shaped for the style.")
						: TEXT("Add building styles or prefabs to the land use, or assign another land use.")).ParcelIndex = ParcelIndex;
			}
		}
	}

	for (int32 First = 0; First < Blocks.Num(); ++First)
	{
		for (int32 Second = First + 1; Second < Blocks.Num(); ++Second)
		{
			if (DoPolygonsOverlap2D(BlockOutlines[First], BlockOutlines[Second], 10.0))
			{
				AddIssue(Issues, ECityBLDIssueSeverity::Warning, TEXT("BlocksOverlap"),
					TEXT("Two block outlines overlap, so their buildings may intersect."),
					Blocks[First], PolygonCentroid(BlockOutlines[First]), TEXT("Delete one block or reshape their outlines.")).OtherActor = BLDToolset::MakeActorRef(Blocks[Second]);
			}
		}
	}

	const TArray<AModularBuildingActor*> Buildings = GetBuildings(World, Bounds);
	Report.BuildingsChecked = Buildings.Num();
	const TMap<const AActor*, FParcelOwner> Owners = BuildParcelOwnerMap(World);

	TArray<TArray<FVector>> Footprints;
	Footprints.Reserve(Buildings.Num());

	for (const AModularBuildingActor* Building : Buildings)
	{
		const TArray<FVector>& Footprint = Footprints.Add_GetRef(GetBuildingFootprintWorld(Building));
		const FVector Location = Footprint.IsEmpty() ? Building->GetActorLocation() : PolygonCentroid(Footprint);

		if (!Building->Style)
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Error, TEXT("BuildingMissingStyle"),
				TEXT("The building has no style, so it generates nothing."),
				Building, Location, TEXT("Assign a building style and regenerate the building."));
		}

		if (Footprint.Num() < 3)
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Error, TEXT("BuildingInvalidFootprint"),
				FString::Printf(TEXT("The footprint has %d points."), Footprint.Num()),
				Building, Location, TEXT("Give the building a footprint of at least 3 points, or delete it."));
		}
		else if (IsPolygonSelfIntersecting2D(Footprint))
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Error, TEXT("BuildingFootprintSelfIntersecting"),
				TEXT("The footprint crosses itself."),
				Building, Location, TEXT("Reorder or move the footprint points so the edges do not cross."));
		}
		else if (Building->Style && !Building->IsValidBuilding())
		{
			AddIssue(Issues, ECityBLDIssueSeverity::Warning, TEXT("BuildingInvalid"),
				TEXT("CityBLD reports the building as invalid (usually an incomplete style or footprint)."),
				Building, Location, TEXT("Check the style with DescribeBuildingStyle and regenerate the building."));
		}

		if (!Owners.Contains(Building) && Footprint.Num() >= 3)
		{
			for (int32 BlockIndex = 0; BlockIndex < Blocks.Num(); ++BlockIndex)
			{
				if (BlockOutlines[BlockIndex].Num() >= 3 && UCityBLDUtils::IsPointInPolygon2D(Location, BlockOutlines[BlockIndex]))
				{
					AddIssue(Issues, ECityBLDIssueSeverity::Info, TEXT("BuildingNotOnParcel"),
						TEXT("The building is inside a block but not registered to any of its parcels, so regenerating the block will not replace or remove it."),
						Building, Location, TEXT("Leave it if it was placed on purpose; otherwise delete it or regenerate the block.")).OtherActor = BLDToolset::MakeActorRef(Blocks[BlockIndex]);
					break;
				}
			}
		}
	}

	if (Buildings.Num() <= MaxBuildingsForOverlapCheck)
	{
		for (int32 First = 0; First < Buildings.Num(); ++First)
		{
			for (int32 Second = First + 1; Second < Buildings.Num(); ++Second)
			{
				if (DoPolygonsOverlap2D(Footprints[First], Footprints[Second]))
				{
					AddIssue(Issues, ECityBLDIssueSeverity::Warning, TEXT("BuildingsOverlap"),
						TEXT("Two building footprints overlap."),
						Buildings[First], PolygonCentroid(Footprints[First]), TEXT("Delete one building or change a footprint.")).OtherActor = BLDToolset::MakeActorRef(Buildings[Second]);
				}
			}
		}
	}
	else
	{
		Report.Warnings.Add(FString::Printf(TEXT("Skipped the building overlap check for %d buildings. Pass smaller Bounds to include it."), Buildings.Num()));
	}

	Issues.StableSort([](const FCityBLDIssue& A, const FCityBLDIssue& B)
	{
		return A.Severity < B.Severity;
	});

	for (const FCityBLDIssue& Issue : Issues)
	{
		switch (Issue.Severity)
		{
		case ECityBLDIssueSeverity::Error:
			++Report.ErrorCount;
			break;
		case ECityBLDIssueSeverity::Warning:
			++Report.WarningCount;
			break;
		default:
			++Report.InfoCount;
			break;
		}
	}

	Report.TotalCount = Issues.Num();
	const int32 Limit = ClampMaxResults(MaxResults);
	if (Issues.Num() > Limit)
	{
		Issues.SetNum(Limit);
	}
	Report.Issues = MoveTemp(Issues);
	return Report;
}

FBLDIssueReport UCityBLDDiscoveryToolset::ValidateCity(TOptional<FCityBLDBounds> Bounds, const int32 MaxResults)
{
	const FCityBLDIssueReport CityReport = FindCityIssues(Bounds, MaxResults);
	FBLDIssueReport Report;
	Report.Notes.Append(CityReport.Warnings);

	for (const FCityBLDIssue& CityIssue : CityReport.Issues)
	{
		EBLDIssueSeverity Severity = EBLDIssueSeverity::Warning;
		switch (CityIssue.Severity)
		{
		case ECityBLDIssueSeverity::Error: Severity = EBLDIssueSeverity::Error; break;
		case ECityBLDIssueSeverity::Info: Severity = EBLDIssueSeverity::Info; break;
		default: break;
		}

		Report.Issues.Add(BLDValidation::MakeIssue(
			Severity,
			TEXT("CityBLD"),
			CityIssue.Code.IsEmpty() ? TEXT("CityIssue") : CityIssue.Code,
			CityIssue.Message,
			CityIssue.Actor,
			CityIssue.OtherActor,
			CityIssue.Location,
			0.0,
			CityIssue.Fix));
	}

	BLDValidation::FinalizeReport(Report);
	return Report;
}
