// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/RoadBLDDiscoveryToolset.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Common/RoadBLDRebuildJobs.h"
#include "Common/RoadBLDToolsetUtils.h"
#include "Components/SplineComponent.h"
#include "CrossingStyle.h"
#include "Curves/CurveFloat.h"
#include "DynamicMesh/DynamicMesh3.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadLane.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "DynamicRoad/EdgeCurve.h"
#include "DynamicRoad/Sidewalk.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialParameters.h"
#include "Misc/PackageName.h"
#include "Presets/RoadBLDPresetSpecIO.h"
#include "RoadControlSplineComponent.h"
#include "RoadGeo.h"
#include "RoadModuleObject.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(RoadBLDDiscoveryToolset)

namespace RoadBLDDiscoveryPrivate
{
	using namespace RoadBLDToolset;

	FRoadBLDLaneInfo MakeLaneInfo(const ADynamicRoad* Road, const UDynamicRoadLane* Lane, const ERoadBLDSide Side, const int32 Index)
	{
		FRoadBLDLaneInfo Info;
		Info.Side = Side;
		Info.Index = Index;
		Info.Type = Lane->LaneSections.Num() > 0 ? EnumToString(Lane->LaneSections[0].LaneType) : TEXT("Normal");

		const UEdgeCurve* OuterEdge = Side == ERoadBLDSide::Left ? Lane->LeftEdgeCurve.Get() : Lane->RightEdgeCurve.Get();
		const UEdgeCurve* InnerEdge = Side == ERoadBLDSide::Left ? Lane->RightEdgeCurve.Get() : Lane->LeftEdgeCurve.Get();
		const double Length = Road->GetLength();

		TArray<double> SampleDistances = { 0.0, Length };
		for (const UEdgeCurve* Edge : { OuterEdge, InnerEdge })
		{
			if (IsValid(Edge))
			{
				for (const FOffsetPoint& Point : Edge->OffsetPoints)
				{
					SampleDistances.Add(FMath::Clamp(Point.Distance, 0.0, Length));
				}
			}
		}

		auto WidthAt = [OuterEdge, InnerEdge](const double Distance)
		{
			return FMath::Abs(EvaluateEdgeOffset(OuterEdge, Distance) - EvaluateEdgeOffset(InnerEdge, Distance));
		};

		Info.WidthAtStart = WidthAt(0.0);
		Info.WidthAtEnd = WidthAt(Length);
		Info.MinWidth = TNumericLimits<double>::Max();
		Info.MaxWidth = 0.0;
		for (const double Distance : SampleDistances)
		{
			const double Width = WidthAt(Distance);
			Info.MinWidth = FMath::Min(Info.MinWidth, Width);
			Info.MaxWidth = FMath::Max(Info.MaxWidth, Width);
		}

		if (IsValid(OuterEdge) && OuterEdge->Segments.Num() > 0)
		{
			Info.OuterMarkingMaterial = GetObjectPath(OuterEdge->Segments[0].LaneMarking.MarkingMaterial);
			Info.OuterMarkingWidth = OuterEdge->Segments[0].LaneMarking.MarkingWidth;
		}

		return Info;
	}

	TArray<FRoadBLDLaneInfo> MakeLaneInfos(const ADynamicRoad* Road, const ERoadBLDSide Side)
	{
		TArray<FRoadBLDLaneInfo> Infos;
		const TArray<TObjectPtr<UDynamicRoadLane>>& Lanes = Side == ERoadBLDSide::Left ? Road->LeftLanes : Road->RightLanes;
		for (int32 Index = 0; Index < Lanes.Num(); ++Index)
		{
			if (IsValid(Lanes[Index]))
			{
				Infos.Add(MakeLaneInfo(Road, Lanes[Index], Side, Index));
			}
		}
		return Infos;
	}

	FRoadBLDSidewalkInfo MakeSidewalkInfo(const ADynamicRoad* Road, const ERoadBLDSide Side)
	{
		FRoadBLDSidewalkInfo Info;
		Info.Side = Side;

		TSubclassOf<URoadBLDSidewalkPreset> PresetClass = Side == ERoadBLDSide::Left ? Road->LeftSidewalkPreset : Road->RightSidewalkPreset;
		if (!PresetClass && Road->SourceDrawPreset)
		{
			PresetClass = Side == ERoadBLDSide::Left
				? Road->SourceDrawPreset->LeftSidewalkPresetClass
				: Road->SourceDrawPreset->RightSidewalkPresetClass;
		}

		const USidewalk* Sidewalk = Road->GetSidewalkOnSide(ToRoadSide(Side));
		if (!IsValid(Sidewalk))
		{
			return Info;
		}

		Info.bPresent = true;
		Info.PresetId = GetObjectPath(PresetClass.Get());
		Info.Width = FMath::Abs(EvaluateEdgeOffset(Sidewalk->LeftEdgeCurve, 0.0) - EvaluateEdgeOffset(Sidewalk->RightEdgeCurve, 0.0));
		Info.ZOffset = Sidewalk->ZOffset;
		Info.PartitionCount = Sidewalk->Partitions.Num();
		Info.Material = GetObjectPath(Sidewalk->Material);
		return Info;
	}

	FRoadBLDRoadSummary MakeRoadSummary(ADynamicRoad* Road)
	{
		FRoadBLDRoadSummary Summary;
		Summary.Actor = MakeActorRef(Road);
		if (Road->SourceDrawPreset)
		{
			Summary.PresetId = Road->SourceDrawPreset->GetClass()->GetPathName();
			Summary.PresetName = Road->SourceDrawPreset->PresetName.ToString();
		}
		Summary.Length = Road->GetLength();
		Summary.LeftLaneCount = Road->LeftLanes.Num();
		Summary.RightLaneCount = Road->RightLanes.Num();
		return Summary;
	}

	FRoadBLDNetworkInfo MakeNetworkInfo(ADynamicRoadNetwork* Network, const int32 MaxRoads)
	{
		FRoadBLDNetworkInfo Info;
		Info.Actor = MakeActorRef(Network);
		Info.CumulativeLength = Network->GetCumulativeRoadLength();
		Info.bStale = Network->IsRoadNetworkStale();
		Info.bRebuildInProgress = FRoadBLDRebuildJobs::Get().IsNetworkRebuilding(Network);
		Info.JunctionCount = GetJunctionGeos(Network).Num();

		const FBox Bounds = GetNetworkBounds(Network, false);
		if (Bounds.IsValid)
		{
			Info.BoundsMin = Bounds.Min;
			Info.BoundsMax = Bounds.Max;
		}

		for (const TObjectPtr<ADynamicRoad>& Road : Network->RoadsInNetwork)
		{
			if (!IsValid(Road))
			{
				continue;
			}

			++Info.RoadCount;
			Info.UnlinkedEndpointCount += (CountEndpointLinks(Road, true) == 0 ? 1 : 0) + (CountEndpointLinks(Road, false) == 0 ? 1 : 0);
			if (Info.Roads.Num() < MaxRoads)
			{
				Info.Roads.Add(MakeRoadSummary(Road));
			}
		}

		return Info;
	}

	TArray<ADynamicRoadNetwork*> NetworksOrAll(ADynamicRoadNetwork* Network)
	{
		return IsValid(Network) ? TArray<ADynamicRoadNetwork*>{ Network } : GetNetworks();
	}

	bool MatchesQuery(const FString& Haystack, const FString& Query)
	{
		return Query.IsEmpty() || Haystack.Contains(Query, ESearchCase::IgnoreCase);
	}

	/** Road centerline samples used to tell stretched triangles from long strips that follow the road. */
	struct FRoadSamples
	{
		TArray<FVector> Locations;
		/** Total paved width. */
		double Width = 0.0;
		/** Widest side, measured from the centerline. */
		double SideWidth = 0.0;
	};

	FRoadSamples SampleCenterline(const ADynamicRoad* Road)
	{
		FRoadSamples Samples;
		const double Length = Road->GetLength();
		const double Left = GetRoadSideWidth(Road, ERoadSide::Left, 0.0);
		const double Right = GetRoadSideWidth(Road, ERoadSide::Right, 0.0);
		Samples.Width = Left + Right;
		Samples.SideWidth = FMath::Max(Left, Right);
		if (Length <= 0.0)
		{
			return Samples;
		}

		const int32 Count = FMath::Clamp(FMath::CeilToInt32(Length / 200.0), 1, 2000);
		for (int32 Index = 0; Index <= Count; ++Index)
		{
			const double Distance = Length * Index / Count;
			Samples.Locations.Add(Road->GetWorldLocationAtDistanceAlongRoad(Distance));
		}
		return Samples;
	}

	/**
	 * True when the segment stays on the surface of the roads along its whole length. Long strips of a straight road
	 * pass; triangles stretched across a gap or away from the road do not.
	 */
	bool IsSegmentOnRoads(const TArray<const FRoadSamples*>& Roads, const FVector& Start, const FVector& End)
	{
		// Samples are 200 cm apart, so allow for the gap between them.
		constexpr double SampleSlack = 300.0;
		const int32 Steps = FMath::Clamp(FMath::CeilToInt32(FVector::Dist2D(Start, End) / 500.0), 1, 64);
		for (int32 Step = 0; Step <= Steps; ++Step)
		{
			const FVector Point = FMath::Lerp(Start, End, static_cast<double>(Step) / Steps);
			const bool bOnRoad = Roads.ContainsByPredicate([&Point](const FRoadSamples* Road)
			{
				const double MaxDistanceSquared = FMath::Square(Road->SideWidth + SampleSlack);
				return Road->Locations.ContainsByPredicate([&Point, MaxDistanceSquared](const FVector& Location)
				{
					return FVector::DistSquared2D(Location, Point) <= MaxDistanceSquared;
				});
			});
			if (!bOnRoad)
			{
				return false;
			}
		}
		return true;
	}

	struct FTriangleCluster
	{
		FBox Bounds = FBox(ForceInit);
		int32 TriangleCount = 0;
		double MinAngle = 180.0;
		double LongestEdge = 0.0;
		bool bSliver = false;
		const ARoadGeo* Geo = nullptr;
	};

	/** Thresholds for flagged triangles. Junction pieces legitimately contain long fan triangles, so they get more slack. */
	constexpr double SliverMaxAngle = 2.0;
	constexpr double SliverMinEdge = 500.0;
	constexpr double RoadStretchFactor = 3.0;
	constexpr double JunctionStretchFactor = 5.0;
	constexpr double ClusterRadius = 1000.0;
	constexpr int32 MaxFlaggedTrianglesPerGeo = 5000;

	void ScanGeo(
		const ARoadGeo* Geo,
		TMap<const ADynamicRoad*, FRoadSamples>& SampleCache,
		TArray<FTriangleCluster>& OutClusters)
	{
		const FRoadGeoSurfaceMeshView View = Geo->GetSurfaceMeshView();
		UE::Geometry::FDynamicMesh3 Mesh;
		if (!View.IsValid() || !View.CopyToDynamicMesh(Mesh, true))
		{
			return;
		}

		// Fill the cache first; adding to it can move the values that Roads points at.
		for (const TSoftObjectPtr<ADynamicRoad>& SourceRoad : Geo->SourceRoads)
		{
			const ADynamicRoad* Road = SourceRoad.Get();
			if (Road && !SampleCache.Contains(Road))
			{
				SampleCache.Add(Road, SampleCenterline(Road));
			}
		}

		TArray<const FRoadSamples*> Roads;
		double RoadWidth = 0.0;
		for (const TSoftObjectPtr<ADynamicRoad>& SourceRoad : Geo->SourceRoads)
		{
			if (const FRoadSamples* Samples = SampleCache.Find(SourceRoad.Get()))
			{
				Roads.Add(Samples);
				RoadWidth = FMath::Max(RoadWidth, Samples->Width);
			}
		}
		if (Roads.Num() == 0)
		{
			return;
		}

		RoadWidth = FMath::Max(RoadWidth, 300.0);
		const double StretchEdge = RoadWidth * (Roads.Num() > 1 ? JunctionStretchFactor : RoadStretchFactor);
		const double SliverEdge = FMath::Max(RoadWidth, SliverMinEdge) * (Roads.Num() > 1 ? 2.5 : 1.0);

		int32 Flagged = 0;
		for (const int32 TriangleId : Mesh.TriangleIndicesItr())
		{
			FVector3d Corners[3];
			Mesh.GetTriVertices(TriangleId, Corners[0], Corners[1], Corners[2]);

			int32 LongestIndex = 0;
			double Lengths[3];
			for (int32 Index = 0; Index < 3; ++Index)
			{
				Lengths[Index] = FVector::Dist(Corners[Index], Corners[(Index + 1) % 3]);
				if (Lengths[Index] > Lengths[LongestIndex])
				{
					LongestIndex = Index;
				}
			}

			double MinAngle = 180.0;
			for (int32 Index = 0; Index < 3; ++Index)
			{
				const FVector EdgeA = (Corners[(Index + 1) % 3] - Corners[Index]).GetSafeNormal();
				const FVector EdgeB = (Corners[(Index + 2) % 3] - Corners[Index]).GetSafeNormal();
				MinAngle = FMath::Min(MinAngle, FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(EdgeA, EdgeB), -1.0, 1.0))));
			}

			const double Longest = Lengths[LongestIndex];
			const bool bSliver = MinAngle < SliverMaxAngle && Longest > SliverEdge;
			const bool bStretched = Longest > StretchEdge;
			if (!bSliver && !bStretched)
			{
				continue;
			}

			// Vertical walls and long strips that stay on the road are fine; edges that leave it are not.
			const FVector EdgeStart = Corners[LongestIndex];
			const FVector EdgeEnd = Corners[(LongestIndex + 1) % 3];
			if (FVector::Dist2D(EdgeStart, EdgeEnd) < Longest * 0.5 || IsSegmentOnRoads(Roads, EdgeStart, EdgeEnd))
			{
				continue;
			}

			const FVector Centroid = (Corners[0] + Corners[1] + Corners[2]) / 3.0;

			FTriangleCluster* Cluster = OutClusters.FindByPredicate([Geo, &Centroid](const FTriangleCluster& Candidate)
			{
				return Candidate.Geo == Geo && Candidate.Bounds.ExpandBy(ClusterRadius).IsInsideXY(Centroid);
			});
			if (!Cluster)
			{
				Cluster = &OutClusters.AddDefaulted_GetRef();
				Cluster->Geo = Geo;
			}

			Cluster->Bounds += FVector(Corners[0]);
			Cluster->Bounds += FVector(Corners[1]);
			Cluster->Bounds += FVector(Corners[2]);
			++Cluster->TriangleCount;
			Cluster->MinAngle = FMath::Min(Cluster->MinAngle, MinAngle);
			Cluster->LongestEdge = FMath::Max(Cluster->LongestEdge, Longest);
			Cluster->bSliver |= bSliver;

			if (++Flagged >= MaxFlaggedTrianglesPerGeo)
			{
				break;
			}
		}
	}
}

TArray<FRoadBLDPresetSummary> URoadBLDDiscoveryToolset::ListPresets(
	const FString& Region,
	const FString& Category,
	const FString& Tags,
	const FString& Query)
{
	using namespace RoadBLDDiscoveryPrivate;

	const TArray<FString> RequiredTags = SplitCommaList(GetOptionalString(Tags, TEXT("Any")));
	const FString TrimmedRegion = GetOptionalString(Region, TEXT("Any"));
	const FString TrimmedCategory = GetOptionalString(Category, TEXT("Any"));
	const FString TrimmedQuery = GetOptionalString(Query, TEXT("Any"));

	TArray<FRoadBLDPresetSummary> Results;
	for (const TSubclassOf<UDynamicRoadDrawPreset>& PresetClass : DiscoverPresetClasses())
	{
		FRoadBLDPresetSummary Summary = MakePresetSummary(PresetClass.Get());
		if (!TrimmedRegion.IsEmpty() && !Summary.Region.Equals(TrimmedRegion, ESearchCase::IgnoreCase))
		{
			continue;
		}

		if (!TrimmedCategory.IsEmpty() && !Summary.Category.Equals(TrimmedCategory, ESearchCase::IgnoreCase))
		{
			continue;
		}

		const bool bTagsMatch = !RequiredTags.ContainsByPredicate([&Summary](const FString& RequiredTag)
		{
			auto Matches = [&RequiredTag](const FString& Tag) { return Tag.Equals(RequiredTag, ESearchCase::IgnoreCase); };
			return !Summary.Tags.ContainsByPredicate(Matches) && !Summary.DerivedTags.ContainsByPredicate(Matches);
		});
		if (!bTagsMatch)
		{
			continue;
		}

		const FString Haystack = FString::Join(TArray<FString>{
			Summary.Name, Summary.Description, Summary.Id, FString::Join(Summary.Tags, TEXT(" ")) }, TEXT(" "));
		if (!MatchesQuery(Haystack, TrimmedQuery))
		{
			continue;
		}

		Results.Add(MoveTemp(Summary));
	}

	return Results;
}

FRoadBLDPresetDescription URoadBLDDiscoveryToolset::DescribePreset(TSubclassOf<UDynamicRoadDrawPreset> Preset)
{
	using namespace RoadBLDDiscoveryPrivate;

	FRoadBLDPresetDescription Description;
	const UDynamicRoadDrawPreset* PresetObject = Preset ? Preset.GetDefaultObject() : nullptr;
	if (!PresetObject)
	{
		RaiseError(TEXT("Preset is required. Use an Id from ListPresets."));
		return Description;
	}

	Description.Summary = MakePresetSummary(Preset.Get());
	Description.Spec = RoadBLDPresetSpecIO::ExportPresetSpec(PresetObject);
	Description.Spec.BasePreset = Description.Summary.Id;

	if (PresetObject->LeftSidewalkPresetClass)
	{
		Description.bHasLeftSidewalk = true;
		Description.LeftSidewalk = RoadBLDPresetSpecIO::ExportSidewalkSpec(PresetObject->LeftSidewalkPresetClass.GetDefaultObject());
	}
	if (PresetObject->RightSidewalkPresetClass)
	{
		Description.bHasRightSidewalk = true;
		Description.RightSidewalk = RoadBLDPresetSpecIO::ExportSidewalkSpec(PresetObject->RightSidewalkPresetClass.GetDefaultObject());
	}

	return Description;
}

TArray<FRoadBLDStyleAssetInfo> URoadBLDDiscoveryToolset::ListStyleAssets(
	const ERoadBLDStyleAssetKind Kind,
	const FString& Query,
	int32 MaxResults)
{
	using namespace RoadBLDDiscoveryPrivate;

	MaxResults = FMath::Clamp(MaxResults, 1, 1000);
	const FString TrimmedQuery = GetOptionalString(Query, TEXT("Any"));
	TArray<FRoadBLDStyleAssetInfo> Results;

	UClass* BlueprintBaseClass = nullptr;
	UClass* AssetClass = nullptr;
	switch (Kind)
	{
	case ERoadBLDStyleAssetKind::SidewalkPreset:
		BlueprintBaseClass = URoadBLDSidewalkPreset::StaticClass();
		break;
	case ERoadBLDStyleAssetKind::CrossingStyle:
		BlueprintBaseClass = UCrossingStyle::StaticClass();
		break;
	case ERoadBLDStyleAssetKind::RoadModule:
		BlueprintBaseClass = URoadModuleObject::StaticClass();
		break;
	case ERoadBLDStyleAssetKind::LanePreset:
		BlueprintBaseClass = ULanePreset::StaticClass();
		break;
	case ERoadBLDStyleAssetKind::Material:
		AssetClass = UMaterialInterface::StaticClass();
		break;
	case ERoadBLDStyleAssetKind::StaticMesh:
		AssetClass = UStaticMesh::StaticClass();
		break;
	case ERoadBLDStyleAssetKind::Curve:
		AssetClass = UCurveFloat::StaticClass();
		break;
	}

	if (BlueprintBaseClass)
	{
		for (UClass* Class : DiscoverClasses(BlueprintBaseClass))
		{
			FRoadBLDStyleAssetInfo Info;
			Info.Id = Class->GetPathName();
			Info.Name = Class->GetName();
			Info.Name.RemoveFromEnd(TEXT("_C"));
			Info.Class = Class->GetSuperClass() ? Class->GetSuperClass()->GetName() : BlueprintBaseClass->GetName();
			if (MatchesQuery(Info.Name + TEXT(" ") + Info.Id, TrimmedQuery))
			{
				Results.Add(MoveTemp(Info));
			}
		}
	}
	else if (AssetClass)
	{
		IAssetRegistry& AssetRegistry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
		FARFilter Filter;
		Filter.PackagePaths = GetContentRoots();
		Filter.bRecursivePaths = true;
		Filter.ClassPaths.Add(AssetClass->GetClassPathName());
		Filter.bRecursiveClasses = true;

		TArray<FAssetData> Assets;
		AssetRegistry.GetAssets(Filter, Assets);

		for (const FAssetData& AssetData : Assets)
		{
			FRoadBLDStyleAssetInfo Info;
			Info.Id = AssetData.GetObjectPathString();
			Info.Name = AssetData.AssetName.ToString();
			Info.Class = AssetData.AssetClassPath.GetAssetName().ToString();
			if (MatchesQuery(Info.Name + TEXT(" ") + Info.Id, TrimmedQuery))
			{
				Results.Add(MoveTemp(Info));
			}
		}
	}

	for (FRoadBLDStyleAssetInfo& Info : Results)
	{
		if (const FReferenceKitAsset* Reference = FindReferenceKitAsset(FPackageName::ObjectPathToPackageName(Info.Id)))
		{
			Info.bIsRecommended = true;
			Info.Note = Reference->Note;
		}
	}

	Results.Sort([](const FRoadBLDStyleAssetInfo& A, const FRoadBLDStyleAssetInfo& B)
	{
		if (A.bIsRecommended != B.bIsRecommended)
		{
			return A.bIsRecommended;
		}
		return A.Id < B.Id;
	});

	if (Results.Num() > MaxResults)
	{
		Results.SetNum(MaxResults);
	}
	return Results;
}

TArray<FRoadBLDMaterialParameterInfo> URoadBLDDiscoveryToolset::ListMaterialParameters(UMaterialInterface* Material)
{
	using namespace RoadBLDDiscoveryPrivate;

	TArray<FRoadBLDMaterialParameterInfo> Results;
	if (!IsValid(Material))
	{
		RaiseError(TEXT("Material is required."));
		return Results;
	}

	const TPair<EMaterialParameterType, const TCHAR*> ParameterTypes[] =
	{
		{ EMaterialParameterType::Scalar, TEXT("Scalar") },
		{ EMaterialParameterType::Vector, TEXT("Vector") },
		{ EMaterialParameterType::Texture, TEXT("Texture") },
		{ EMaterialParameterType::StaticSwitch, TEXT("StaticSwitch") },
	};

	for (const TPair<EMaterialParameterType, const TCHAR*>& ParameterType : ParameterTypes)
	{
		TMap<FMaterialParameterInfo, FMaterialParameterMetadata> Parameters;
		Material->GetAllParametersOfType(ParameterType.Key, Parameters);
		for (const TPair<FMaterialParameterInfo, FMaterialParameterMetadata>& Pair : Parameters)
		{
			if (Pair.Key.Association != EMaterialParameterAssociation::GlobalParameter)
			{
				continue;
			}

			FRoadBLDMaterialParameterInfo& Info = Results.AddDefaulted_GetRef();
			Info.Name = Pair.Key.Name.ToString();
			Info.Type = ParameterType.Value;
#if WITH_EDITORONLY_DATA
			Info.Group = Pair.Value.Group.ToString();
#endif
			switch (ParameterType.Key)
			{
			case EMaterialParameterType::Scalar:
				Info.ScalarDefault = Pair.Value.Value.AsScalar();
				break;
			case EMaterialParameterType::Vector:
				Info.VectorDefault = Pair.Value.Value.AsLinearColor();
				break;
			case EMaterialParameterType::Texture:
				Info.TextureDefault = GetObjectPath(Pair.Value.Value.Texture);
				break;
			case EMaterialParameterType::StaticSwitch:
				Info.bSwitchDefault = Pair.Value.Value.AsStaticSwitch();
				break;
			default:
				break;
			}
		}
	}

	Results.Sort([](const FRoadBLDMaterialParameterInfo& A, const FRoadBLDMaterialParameterInfo& B)
	{
		return A.Group != B.Group ? A.Group < B.Group : A.Name < B.Name;
	});
	return Results;
}

TArray<FRoadBLDNetworkInfo> URoadBLDDiscoveryToolset::DescribeNetwork(ADynamicRoadNetwork* Network, const int32 MaxRoads)
{
	using namespace RoadBLDDiscoveryPrivate;

	TArray<FRoadBLDNetworkInfo> Infos;
	for (ADynamicRoadNetwork* Candidate : NetworksOrAll(Network))
	{
		Infos.Add(MakeNetworkInfo(Candidate, FMath::Max(0, MaxRoads)));
	}
	return Infos;
}

FRoadBLDRoadInfo URoadBLDDiscoveryToolset::DescribeRoad(ADynamicRoad* Road)
{
	using namespace RoadBLDDiscoveryPrivate;

	FRoadBLDRoadInfo Info;
	if (!IsValid(Road))
	{
		RaiseError(TEXT("Road is required."));
		return Info;
	}

	ADynamicRoadNetwork* Network = GetOwningNetwork(Road);
	Info.Actor = MakeActorRef(Road);
	Info.Network = MakeActorRef(Network);
	if (Road->SourceDrawPreset)
	{
		Info.PresetId = Road->SourceDrawPreset->GetClass()->GetPathName();
		Info.PresetName = Road->SourceDrawPreset->PresetName.ToString();
	}
	Info.Length = Road->GetLength();

	const FBox Bounds = GetRoadBounds(Road, true);
	if (Bounds.IsValid)
	{
		Info.BoundsMin = Bounds.Min;
		Info.BoundsMax = Bounds.Max;
	}

	if (IsValid(Road->ControlSpline))
	{
		for (int32 Index = 0; Index < Road->ControlSpline->GetNumberOfSplinePoints(); ++Index)
		{
			FRoadBLDPoint& Point = Info.ControlPoints.AddDefaulted_GetRef();
			Point.Location = Road->ControlSpline->GetLocationAtSplinePoint(Index, ESplineCoordinateSpace::World);
			Road->GetPointTurnRadius(Index, Point.TurnRadius);
		}
	}

	Info.LeftLanes = MakeLaneInfos(Road, ERoadBLDSide::Left);
	Info.RightLanes = MakeLaneInfos(Road, ERoadBLDSide::Right);
	Info.LeftSidewalk = MakeSidewalkInfo(Road, ERoadBLDSide::Left);
	Info.RightSidewalk = MakeSidewalkInfo(Road, ERoadBLDSide::Right);
	Info.Start = MakeEndpointInfo(Road, true);
	Info.End = MakeEndpointInfo(Road, false);
	Info.bConformToLandscape = Road->bConformToLandscape;

	for (const ARoadGeo* Geo : GetJunctionGeos(Network))
	{
		if (DoesGeoReferenceRoad(Geo, Road))
		{
			Info.JunctionIds.Add(Geo->GetPathName());
		}
	}

	return Info;
}

TArray<FRoadBLDJunctionList> URoadBLDDiscoveryToolset::ListJunctions(ADynamicRoadNetwork* Network)
{
	using namespace RoadBLDDiscoveryPrivate;

	TArray<FRoadBLDJunctionList> Lists;
	for (ADynamicRoadNetwork* Candidate : NetworksOrAll(Network))
	{
		FRoadBLDJunctionList& List = Lists.AddDefaulted_GetRef();
		List.Network = MakeActorRef(Candidate);
		List.bStale = Candidate->IsRoadNetworkStale();
		List.bRebuildInProgress = FRoadBLDRebuildJobs::Get().IsNetworkRebuilding(Candidate);

		const TArrayView<const FRoadNetworkCorner> Corners = Candidate->GetRoadNetworkCornersView();
		for (const ARoadGeo* Geo : GetJunctionGeos(Candidate))
		{
			FRoadBLDJunctionInfo& Junction = List.Junctions.AddDefaulted_GetRef();
			Junction.Id = Geo->GetPathName();

			const FBox Bounds = Geo->GetComponentsBoundingBox(true);
			if (Bounds.IsValid)
			{
				Junction.BoundsMin = Bounds.Min;
				Junction.BoundsMax = Bounds.Max;
				Junction.Location = Bounds.GetCenter();
			}

			TSet<const UEdgeCurve*> JunctionEdges;
			for (const TSoftObjectPtr<ADynamicRoad>& SourceRoad : Geo->SourceRoads)
			{
				if (ADynamicRoad* Road = SourceRoad.Get())
				{
					Junction.Roads.Add(MakeActorRef(Road));
					for (const TObjectPtr<UEdgeCurve>& Edge : Road->EdgeCurves)
					{
						JunctionEdges.Add(Edge.Get());
					}
				}
			}

			const FBox CornerBounds = Bounds.IsValid ? Bounds.ExpandBy(500.0) : FBox(ForceInit);
			for (const FRoadNetworkCorner& Corner : Corners)
			{
				if (CornerBounds.IsValid
					&& CornerBounds.IsInsideXY(Corner.IntersectionPoint)
					&& (JunctionEdges.Contains(Corner.StartEdge.Get()) || JunctionEdges.Contains(Corner.EndEdge.Get())))
				{
					++Junction.CornerCount;
					Junction.CornerRadii.Add(Corner.CornerRadius);
				}
			}
		}
	}

	return Lists;
}

TArray<FRoadBLDEndpointInfo> URoadBLDDiscoveryToolset::ListEndpoints(ADynamicRoadNetwork* Network, const bool bUnlinkedOnly)
{
	using namespace RoadBLDDiscoveryPrivate;

	TArray<FRoadBLDEndpointInfo> Endpoints;
	for (ADynamicRoadNetwork* Candidate : NetworksOrAll(Network))
	{
		for (const TObjectPtr<ADynamicRoad>& Road : Candidate->RoadsInNetwork)
		{
			if (!IsValid(Road))
			{
				continue;
			}

			for (const bool bStart : { true, false })
			{
				if (!bUnlinkedOnly || CountEndpointLinks(Road, bStart) == 0)
				{
					Endpoints.Add(MakeEndpointInfo(Road, bStart));
				}
			}
		}
	}
	return Endpoints;
}

TArray<FRoadBLDJunctionIssue> URoadBLDDiscoveryToolset::FindJunctionIssues(ADynamicRoadNetwork* Network)
{
	using namespace RoadBLDDiscoveryPrivate;

	TArray<FRoadBLDJunctionIssue> Issues;
	for (ADynamicRoadNetwork* Candidate : NetworksOrAll(Network))
	{
		TSet<FString> ReportedCorners;
		for (const TObjectPtr<ADynamicRoad>& Road : Candidate->RoadsInNetwork)
		{
			if (!IsValid(Road) || !IsValid(Road->ControlSpline) || Road->ControlSpline->GetNumberOfSplinePoints() < 2)
			{
				continue;
			}

			const int32 NumPoints = Road->ControlSpline->GetNumberOfSplinePoints();
			const double Width = GetRoadSideWidth(Road, ERoadSide::Left, 0.0) + GetRoadSideWidth(Road, ERoadSide::Right, 0.0);
			for (const bool bStart : { true, false })
			{
				const FVector End = Road->ControlSpline->GetLocationAtSplinePoint(bStart ? 0 : NumPoints - 1, ESplineCoordinateSpace::World);
				const FVector Neighbor = Road->ControlSpline->GetLocationAtSplinePoint(bStart ? 1 : NumPoints - 2, ESplineCoordinateSpace::World);

				for (const FEndpointCorner& Corner : FindCornersAtEnd(Candidate, Road, bStart))
				{
					const FString EndKey = FString::Printf(TEXT("%s:%d"), *Road->GetPathName(), bStart ? 1 : 0);
					const FString OtherKey = FString::Printf(TEXT("%s:%d"), *Corner.OtherRoad->GetPathName(), Corner.bOtherStart ? 1 : 0);
					const FString PairKey = EndKey < OtherKey ? EndKey + TEXT("|") + OtherKey : OtherKey + TEXT("|") + EndKey;
					if (ReportedCorners.Contains(PairKey))
					{
						continue;
					}
					ReportedCorners.Add(PairKey);

					FRoadBLDJunctionIssue& Issue = Issues.AddDefaulted_GetRef();
					Issue.Road = MakeActorRef(Road);
					Issue.bStart = bStart;
					Issue.Location = End;
					Issue.OtherRoad = MakeActorRef(Corner.OtherRoad);
					Issue.bOtherStart = Corner.bOtherStart;
					Issue.Kind = Corner.bLinked ? TEXT("SharpLinkedCorner") : TEXT("UnjoinedCorner");
					Issue.TurnAngle = Corner.TurnAngle;
					Issue.SuggestedLocation = End;
					Issue.Suggestion = FString::Printf(
						TEXT("The %s meets %s's %s at a %.0f degree turn, which builds stretched triangles. Call CloseCorner with A={road, bStart=%s} and B={otherRoad, bStart=%s}, or redraw it as one road through the corner."),
						bStart ? TEXT("start") : TEXT("end"),
						*Corner.OtherRoad->GetActorLabel(),
						Corner.bOtherStart ? TEXT("start") : TEXT("end"),
						Corner.TurnAngle,
						bStart ? TEXT("true") : TEXT("false"),
						Corner.bOtherStart ? TEXT("true") : TEXT("false"));
				}

				FJunctionStub Stub;
				if (!FindJunctionStub(Candidate, Road, End, Neighbor, Width, Stub) || Stub.MoveDistance < 10.0)
				{
					continue;
				}

				FRoadBLDJunctionIssue& Issue = Issues.AddDefaulted_GetRef();
				Issue.Road = MakeActorRef(Road);
				Issue.bStart = bStart;
				Issue.Location = End;
				Issue.OtherRoad = MakeActorRef(Stub.OtherRoad);
				Issue.Kind = Stub.bPastCenterline ? TEXT("StubPastRoad") : TEXT("ShortOfRoad");
				Issue.EdgeDistance = Stub.EdgeDistance;
				Issue.SuggestedLocation = Stub.SnappedLocation;
				Issue.Suggestion = Stub.bPastCenterline
					? FString::Printf(TEXT("Move the %s to SuggestedLocation for a T junction, or extend it at least %.0f cm further for a crossing."),
						bStart ? TEXT("start") : TEXT("end"), FMath::Max(JunctionMinCrossArm, Width) - Stub.EdgeDistance)
					: FString::Printf(TEXT("Move the %s to SuggestedLocation to join %s, or pull it back clear of the road."),
						bStart ? TEXT("start") : TEXT("end"), *Stub.OtherRoad->GetActorLabel());
			}
		}
	}
	return Issues;
}

TArray<FRoadBLDGeometryIssue> URoadBLDDiscoveryToolset::FindGeometryIssues(ADynamicRoadNetwork* Network, int32 MaxIssues)
{
	using namespace RoadBLDDiscoveryPrivate;

	MaxIssues = FMath::Clamp(MaxIssues, 1, 200);
	TArray<FRoadBLDGeometryIssue> Issues;
	for (ADynamicRoadNetwork* Candidate : NetworksOrAll(Network))
	{
		TMap<const ADynamicRoad*, FRoadSamples> SampleCache;
		TArray<FTriangleCluster> Clusters;
		for (const ARoadGeo* Geo : GetNetworkGeos(Candidate))
		{
			if (!Geo->IsPreviewProxy())
			{
				ScanGeo(Geo, SampleCache, Clusters);
			}
		}

		for (const FTriangleCluster& Cluster : Clusters)
		{
			FRoadBLDGeometryIssue& Issue = Issues.AddDefaulted_GetRef();
			Issue.Location = Cluster.Bounds.GetCenter();
			Issue.Radius = FMath::Max(Cluster.Bounds.GetExtent().Size2D(), 500.0);
			Issue.Kind = Cluster.bSliver ? TEXT("Sliver") : TEXT("StretchedTriangle");
			Issue.TriangleCount = Cluster.TriangleCount;
			Issue.MinAngle = Cluster.MinAngle;
			Issue.LongestEdge = Cluster.LongestEdge;
			Issue.GeometryActor = Cluster.Geo->GetPathName();
			for (const TSoftObjectPtr<ADynamicRoad>& SourceRoad : Cluster.Geo->SourceRoads)
			{
				if (const ADynamicRoad* Road = SourceRoad.Get())
				{
					Issue.Roads.Add(MakeActorRef(Road));
				}
			}

			const double NearbyRadius = Issue.Radius + 2000.0;
			for (const TObjectPtr<ADynamicRoad>& Road : Candidate->RoadsInNetwork)
			{
				for (const bool bStart : { true, false })
				{
					FVector EndLocation;
					if (IsValid(Road) && GetEndpointLocation(Road, bStart, EndLocation) && FVector::Dist2D(EndLocation, Issue.Location) <= NearbyRadius)
					{
						Issue.NearbyEnds.Add(MakeEndpointInfo(Road, bStart));
					}
				}
			}
		}
	}

	Issues.Sort([](const FRoadBLDGeometryIssue& A, const FRoadBLDGeometryIssue& B)
	{
		return A.TriangleCount > B.TriangleCount;
	});
	if (Issues.Num() > MaxIssues)
	{
		Issues.SetNum(MaxIssues);
	}
	return Issues;
}

TArray<FRoadBLDRoadSample> URoadBLDDiscoveryToolset::SampleRoad(ADynamicRoad* Road, const double Interval)
{
	using namespace RoadBLDDiscoveryPrivate;

	TArray<FRoadBLDRoadSample> Samples;
	if (!IsValid(Road))
	{
		RaiseError(TEXT("Road is required."));
		return Samples;
	}

	const double Length = Road->GetLength();
	if (Length <= 0.0)
	{
		RaiseError(TEXT("The road has no centerline yet."));
		return Samples;
	}

	const double Step = FMath::Max3(Interval, 100.0, Length / 1000.0);
	TArray<double> Distances;
	for (double Distance = 0.0; Distance < Length; Distance += Step)
	{
		Distances.Add(Distance);
	}
	Distances.Add(Length);

	for (const double Distance : Distances)
	{
		FRoadBLDRoadSample& Sample = Samples.AddDefaulted_GetRef();
		Sample.Distance = Distance;
		Sample.Location = Road->GetWorldLocationAtDistanceAlongRoad(Distance);
		Sample.Right = Road->GetRightVectorAtDistanceAlongRoad(Distance).GetSafeNormal();
		Sample.Direction = FVector::CrossProduct(Sample.Right, FVector::UpVector).GetSafeNormal();
		Sample.LeftWidth = Road->GetWidthAtDistanceAlongRoad(Distance, 0);
		Sample.RightWidth = Road->GetWidthAtDistanceAlongRoad(Distance, 1);
	}

	return Samples;
}
