// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/TwinBLDSceneToolset.h"
#include "BLDValidation.h"

#include "BLDJobRegistry.h"
#include "BLDToolsetUtils.h"
#include "BlueprintLibraries/TwinBLDMapUtilsLibrary.h"
#include "Common/TwinBLDGeo.h"
#include "Common/TwinBLDToolsetSubsystem.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "Editor.h"
#include "Engine/Selection.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "ModularBuildingActor.h"
#include "RoadControlSplineComponent.h"
#include "RoadGeo.h"
#include "ScopedTransaction.h"
#include "StreetMap/StreetMap.h"
#include "Toolsets/TwinBLDLocationToolset.h"
#include "TwinBLDGenerationUtils.h"
#include "TwinBLDImportSession.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(TwinBLDSceneToolset)

#define LOCTEXT_NAMESPACE "TwinBLDSceneToolset"

namespace TwinBLDScenePrivate
{
	const TCHAR* ToolsetName = TEXT("TwinBLDToolset");
	const FString TypeTagPrefix = TEXT("TwinBLD.Type.");
	const FString TileTagPrefix = TEXT("TwinBLD.Tile=");
	const FString OsmTagPrefix = TEXT("TwinBLD.OSM=");
	const FName StaleTag(TEXT("TwinBLD.GeoTransform.Stale"));

	constexpr int32 MaxListedTiles = 100;
	constexpr int32 MaxListedUnchanged = 50;

	/** TwinBLD's importer uses 3 m per level when OSM has no height. */
	constexpr double MetersPerLevel = 3.0;

	void RaiseError(const FString& Message)
	{
		BLDToolset::RaiseError(ToolsetName, Message);
	}

	/** Most specific TwinBLD.Type.* value, such as LandscapePCG.Static. Empty when untagged. */
	FString GetGeneratedType(const AActor* Actor)
	{
		FString Best;
		if (!IsValid(Actor))
		{
			return Best;
		}

		for (const FName& Tag : Actor->Tags)
		{
			const FString TagString = Tag.ToString();
			if (TagString.StartsWith(TypeTagPrefix, ESearchCase::IgnoreCase) && TagString.Len() - TypeTagPrefix.Len() > Best.Len())
			{
				Best = TagString.RightChop(TypeTagPrefix.Len());
			}
		}
		return Best;
	}

	bool MatchesType(const FString& ActorType, const FString& Filter)
	{
		return Filter.IsEmpty()
			|| ActorType.Equals(Filter, ESearchCase::IgnoreCase)
			|| ActorType.StartsWith(Filter + TEXT("."), ESearchCase::IgnoreCase);
	}

	bool GetTile(const AActor* Actor, FIntPoint& OutTile)
	{
		FString Value;
		FString Left;
		FString Right;
		if (!BLDToolset::FindTagValue(Actor, TileTagPrefix, Value) || !Value.Split(TEXT(","), &Left, &Right))
		{
			return false;
		}

		OutTile = FIntPoint(FCString::Atoi(*Left), FCString::Atoi(*Right));
		return true;
	}

	bool IsStale(const AActor* Actor)
	{
		return IsValid(Actor) && Actor->Tags.Contains(StaleTag);
	}

	/** Parses "way/123" (also node/ and relation/) into an id. */
	bool ParseOsmRef(const FString& Ref, int64& OutId)
	{
		FString Kind;
		FString Id;
		if (!Ref.Split(TEXT("/"), &Kind, &Id) || Id.IsEmpty() || !Id.IsNumeric())
		{
			return false;
		}

		OutId = FCString::Atoi64(*Id);
		return true;
	}

	/** Looks up OSM elements of the loaded source map by id or by building footprint. */
	class FOsmIndex
	{
	public:
		explicit FOsmIndex(const UTwinBLDImportSession* Session)
		{
			Map = Session ? Session->GetSourceStreetMap() : nullptr;
			if (!Map)
			{
				return;
			}

			SourceToWorld = Session->GetSourceStreetMapTransform();
			for (int32 Index = 0; Index < Map->Buildings.Num(); ++Index)
			{
				const FStreetMapBuilding& Building = Map->Buildings[Index];
				BuildingsById.Add(Building.OSMId, Index);

				const FIntPoint MinCell = CellOf(Building.BoundsMin);
				const FIntPoint MaxCell = CellOf(Building.BoundsMax);
				for (int32 X = MinCell.X; X <= MaxCell.X; ++X)
				{
					for (int32 Y = MinCell.Y; Y <= MaxCell.Y; ++Y)
					{
						Grid.FindOrAdd(FIntPoint(X, Y)).Add(Index);
					}
				}
			}

			for (int32 Index = 0; Index < Map->Roads.Num(); ++Index)
			{
				RoadsById.Add(Map->Roads[Index].OSMId, Index);
			}
		}

		bool IsLoaded() const
		{
			return Map != nullptr;
		}

		const FStreetMapBuilding* FindBuildingById(const int64 Id) const
		{
			const int32* Index = BuildingsById.Find(Id);
			return Index ? &Map->Buildings[*Index] : nullptr;
		}

		const FStreetMapRoad* FindRoadById(const int64 Id) const
		{
			const int32* Index = RoadsById.Find(Id);
			return Index ? &Map->Roads[*Index] : nullptr;
		}

		/** Smallest OSM building whose outline contains the world location. */
		const FStreetMapBuilding* FindBuildingAt(const FVector& WorldLocation) const
		{
			if (!Map)
			{
				return nullptr;
			}

			const FVector2D Local(SourceToWorld.InverseTransformPosition(WorldLocation));
			const TArray<int32>* Candidates = Grid.Find(CellOf(Local));
			if (!Candidates)
			{
				return nullptr;
			}

			const FStreetMapBuilding* Best = nullptr;
			double BestArea = TNumericLimits<double>::Max();
			for (const int32 Index : *Candidates)
			{
				const FStreetMapBuilding& Building = Map->Buildings[Index];
				if (Local.X < Building.BoundsMin.X || Local.Y < Building.BoundsMin.Y || Local.X > Building.BoundsMax.X || Local.Y > Building.BoundsMax.Y)
				{
					continue;
				}

				if (!ContainsPoint(Building.BuildingPoints, Local))
				{
					continue;
				}

				const FVector2D Size = Building.BoundsMax - Building.BoundsMin;
				const double Area = Size.X * Size.Y;
				if (Area < BestArea)
				{
					BestArea = Area;
					Best = &Building;
				}
			}
			return Best;
		}

	private:
		static constexpr double CellSizeCm = 5000.0;

		static FIntPoint CellOf(const FVector2D& Local)
		{
			return FIntPoint(FMath::FloorToInt32(Local.X / CellSizeCm), FMath::FloorToInt32(Local.Y / CellSizeCm));
		}

		static bool ContainsPoint(const TArray<FVector2D>& Polygon, const FVector2D& Point)
		{
			bool bInside = false;
			for (int32 Index = 0, Previous = Polygon.Num() - 1; Index < Polygon.Num(); Previous = Index++)
			{
				const FVector2D& A = Polygon[Index];
				const FVector2D& B = Polygon[Previous];
				if ((A.Y > Point.Y) != (B.Y > Point.Y)
					&& Point.X < (B.X - A.X) * (Point.Y - A.Y) / (B.Y - A.Y) + A.X)
				{
					bInside = !bInside;
				}
			}
			return bInside;
		}

		const UStreetMap* Map = nullptr;
		FTransform SourceToWorld;
		TMap<int64, int32> BuildingsById;
		TMap<int64, int32> RoadsById;
		TMap<FIntPoint, TArray<int32>> Grid;
	};

	struct FOsmMatch
	{
		const TMap<FName, FString>* Tags = nullptr;
		FString Name;
		double HeightMeters = 0.0;
		int32 Levels = 0;
		FString Method;
	};

	FVector GetFootprintCenter(const AModularBuildingActor* Building)
	{
		if (Building->ShapePoints.Num() < 3)
		{
			return Building->GetActorLocation();
		}

		FVector Sum = FVector::ZeroVector;
		for (const FVector& Point : Building->ShapePoints)
		{
			Sum += Point;
		}
		return Building->GetActorTransform().TransformPosition(Sum / Building->ShapePoints.Num());
	}

	bool FindOsm(const AActor* Actor, const FOsmIndex& Index, FOsmMatch& OutMatch)
	{
		if (!IsValid(Actor) || !Index.IsLoaded())
		{
			return false;
		}

		FString OsmRef;
		int64 OsmId = 0;
		if (BLDToolset::FindTagValue(Actor, OsmTagPrefix, OsmRef) && ParseOsmRef(OsmRef, OsmId))
		{
			if (const FStreetMapBuilding* Building = Index.FindBuildingById(OsmId))
			{
				OutMatch = { &Building->Tags, Building->BuildingName, Building->Height, Building->BuildingLevels, TEXT("Tag") };
				return true;
			}
			if (const FStreetMapRoad* Road = Index.FindRoadById(OsmId))
			{
				OutMatch = { &Road->Tags, Road->RoadName, 0.0, 0, TEXT("Tag") };
				return true;
			}
		}

		if (const AModularBuildingActor* BuildingActor = Cast<AModularBuildingActor>(Actor))
		{
			if (const FStreetMapBuilding* Building = Index.FindBuildingAt(GetFootprintCenter(BuildingActor)))
			{
				OutMatch = { &Building->Tags, Building->BuildingName, Building->Height, Building->BuildingLevels, TEXT("Footprint") };
				return true;
			}
		}

		return false;
	}

	/** OSM tag filter: key, key=value, key!=value, key>number or key<number. */
	struct FTagFilter
	{
		FString Key;
		FString Operator;
		FString Value;

		bool Parse(const FString& Text, FString& OutError)
		{
			const FString Trimmed = Text.TrimStartAndEnd();
			for (const TCHAR* Candidate : { TEXT("!="), TEXT(">="), TEXT("<="), TEXT("="), TEXT(">"), TEXT("<") })
			{
				int32 Position = Trimmed.Find(Candidate);
				if (Position != INDEX_NONE)
				{
					Key = Trimmed.Left(Position).TrimStartAndEnd();
					Operator = Candidate;
					Value = Trimmed.Mid(Position + FCString::Strlen(Candidate)).TrimStartAndEnd();
					break;
				}
			}

			if (Operator.IsEmpty())
			{
				Key = Trimmed;
			}

			if (Key.IsEmpty())
			{
				OutError = FString::Printf(TEXT("OsmTagFilter '%s' has no key. Use key, key=value, key!=value, key>number or key<number."), *Text);
				return false;
			}

			if ((Operator.StartsWith(TEXT(">")) || Operator.StartsWith(TEXT("<"))) && !Value.IsNumeric())
			{
				OutError = FString::Printf(TEXT("OsmTagFilter '%s' compares with %s but '%s' is not a number."), *Text, *Operator, *Value);
				return false;
			}

			return true;
		}

		bool Matches(const TMap<FName, FString>& Tags) const
		{
			const FString* Found = Tags.Find(FName(*Key));
			if (Operator.IsEmpty())
			{
				return Found != nullptr;
			}
			if (Operator == TEXT("!="))
			{
				return !Found || !Found->Equals(Value, ESearchCase::IgnoreCase);
			}
			if (!Found)
			{
				return false;
			}
			if (Operator == TEXT("="))
			{
				return Found->Equals(Value, ESearchCase::IgnoreCase);
			}

			// OSM numbers may carry units ("87 m"); Atod reads the leading number.
			const double Number = FCString::Atod(**Found);
			const double Threshold = FCString::Atod(*Value);
			if (Operator == TEXT(">")) return Number > Threshold;
			if (Operator == TEXT("<")) return Number < Threshold;
			if (Operator == TEXT(">=")) return Number >= Threshold;
			return Number <= Threshold;
		}
	};

	FTwinBLDGeneratedActorInfo MakeInfo(const AActor* Actor, const TwinBLDGeo::FProjection* Projection)
	{
		FTwinBLDGeneratedActorInfo Info;
		Info.Actor = BLDToolset::MakeActorRef(Actor);
		Info.Type = GetGeneratedType(Actor);
		if (Info.Type.IsEmpty())
		{
			Info.Type = TEXT("Untagged");
		}
		Info.bHasTile = GetTile(Actor, Info.Tile);
		BLDToolset::FindTagValue(Actor, OsmTagPrefix, Info.OsmRef);
		Info.bStale = IsStale(Actor);

		if (const AModularBuildingActor* Building = Cast<AModularBuildingActor>(Actor))
		{
			Info.Location = GetFootprintCenter(Building);
			Info.HeightMeters = Building->BuildingHeight / 100.0;
			if (const UClass* Style = Building->Style.Get())
			{
				Info.StyleClassPath = Style->GetPathName();
			}
		}
		else
		{
			Info.Location = Actor->GetActorLocation();
		}

		if (Projection)
		{
			Info.Geo = Projection->ToGeo(FVector2D(Info.Location));
			Info.bHasGeo = true;
		}
		return Info;
	}

	FString DescribeRoof(const FBuildingRoofOverride& Roof)
	{
		if (!Roof.IsSet())
		{
			return FString();
		}

		TArray<FString> Parts;
		if (Roof.bOverrideType)
		{
			Parts.Add(StaticEnum<ERoofType>()->GetNameStringByValue(static_cast<int64>(Roof.Type)));
		}
		if (Roof.bOverrideRidgeHeight)
		{
			Parts.Add(FString::Printf(TEXT("ridge %.1f m"), Roof.RidgeHeight / 100.0));
		}
		if (Roof.bOverrideRidgeDirection)
		{
			Parts.Add(FString::Printf(TEXT("ridge direction %.0f deg (actor-local)"), Roof.RidgeDirectionDegrees));
		}
		if (Roof.bOverrideRidgeOrientation)
		{
			Parts.Add(Roof.bRidgeAcross ? TEXT("ridge across") : TEXT("ridge along"));
		}
		return FString::Join(Parts, TEXT(", "));
	}

	/** Selects Actors for the duration of the scope, then restores the user's selection. */
	class FScopedSelection
	{
	public:
		explicit FScopedSelection(const TArray<AActor*>& Actors)
		{
			if (!GEditor)
			{
				return;
			}

			if (USelection* Selection = GEditor->GetSelectedActors())
			{
				for (FSelectionIterator It(*Selection); It; ++It)
				{
					if (AActor* Actor = Cast<AActor>(*It))
					{
						Previous.Add(Actor);
					}
				}
			}

			GEditor->SelectNone(false, true, false);
			for (AActor* Actor : Actors)
			{
				if (IsValid(Actor))
				{
					GEditor->SelectActor(Actor, true, false, true);
				}
			}
		}

		~FScopedSelection()
		{
			if (!GEditor)
			{
				return;
			}

			GEditor->SelectNone(false, true, false);
			for (const TWeakObjectPtr<AActor>& Actor : Previous)
			{
				if (Actor.IsValid())
				{
					GEditor->SelectActor(Actor.Get(), true, false, true);
				}
			}
			GEditor->NoteSelectionChange();
		}

	private:
		TArray<TWeakObjectPtr<AActor>> Previous;
	};

	TArray<double> GetControlPointHeights(const ADynamicRoad* Road)
	{
		TArray<double> Heights;
		if (IsValid(Road) && IsValid(Road->ControlSpline))
		{
			for (int32 Index = 0; Index < Road->ControlSpline->GetNumberOfSplinePoints(); ++Index)
			{
				Heights.Add(Road->ControlSpline->GetLocationAtSplinePoint(Index, ESplineCoordinateSpace::World).Z);
			}
		}
		return Heights;
	}

	void AddUnchanged(TArray<FBLDActorRef>& List, int32& Count, const AActor* Actor)
	{
		++Count;
		if (List.Num() < MaxListedUnchanged)
		{
			List.Add(BLDToolset::MakeActorRef(Actor));
		}
	}

	TArray<AActor*> CollectGenerated(UWorld* World, const FString& Type, UClass* Class)
	{
		TArray<AActor*> Actors;
		for (TActorIterator<AActor> It(World, Class); It; ++It)
		{
			if (MatchesType(GetGeneratedType(*It), Type) && !GetGeneratedType(*It).IsEmpty())
			{
				Actors.Add(*It);
			}
		}
		return Actors;
	}
}

FTwinBLDSceneContext UTwinBLDSceneToolset::GetSceneContext()
{
	using namespace TwinBLDScenePrivate;

	FTwinBLDSceneContext Context;
	UWorld* World = BLDToolset::GetEditorWorld();
	if (!World)
	{
		RaiseError(TEXT("No editor world is loaded."));
		return Context;
	}

	Context.bHasLandscape = UTwinBLDGenerationUtils::HasLandscapeActorInLevel(World);
	Context.bHasRoadNetwork = UTwinBLDGenerationUtils::HasRoadNetworkActor(World);
	Context.bHasModularBuildings = UTwinBLDGenerationUtils::HasBuildingActors(World, AModularBuildingActor::StaticClass());

	TMap<FString, int32> TypeCounts;
	TMap<FIntPoint, TMap<FString, int32>> TileCounts;
	TMap<FIntPoint, int32> TileStale;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		const AActor* Actor = *It;
		const FString Type = GetGeneratedType(Actor);
		if (Type.IsEmpty())
		{
			if (Cast<AModularBuildingActor>(Actor))
			{
				++Context.UntaggedBuildingCount;
			}
			continue;
		}

		++TypeCounts.FindOrAdd(Type);
		const bool bStale = IsStale(Actor);
		Context.StaleActorCount += bStale ? 1 : 0;

		FIntPoint Tile;
		if (GetTile(Actor, Tile))
		{
			++TileCounts.FindOrAdd(Tile).FindOrAdd(Type);
			TileStale.FindOrAdd(Tile) += bStale ? 1 : 0;
		}
	}

	auto ToLayerCounts = [](const TMap<FString, int32>& Counts)
	{
		TArray<FTwinBLDLayerCount> Layers;
		for (const TPair<FString, int32>& Pair : Counts)
		{
			FTwinBLDLayerCount& Layer = Layers.AddDefaulted_GetRef();
			Layer.Type = Pair.Key;
			Layer.Count = Pair.Value;
		}
		Layers.Sort([](const FTwinBLDLayerCount& A, const FTwinBLDLayerCount& B) { return A.Count > B.Count; });
		return Layers;
	};

	Context.GeneratedCounts = ToLayerCounts(TypeCounts);
	Context.TileCount = TileCounts.Num();

	TArray<FIntPoint> SortedTiles;
	TileCounts.GetKeys(SortedTiles);
	SortedTiles.Sort([](const FIntPoint& A, const FIntPoint& B) { return A.X != B.X ? A.X < B.X : A.Y < B.Y; });
	for (const FIntPoint& Tile : SortedTiles)
	{
		if (Context.Tiles.Num() >= MaxListedTiles)
		{
			break;
		}

		FTwinBLDTileContent& Content = Context.Tiles.AddDefaulted_GetRef();
		Content.X = Tile.X;
		Content.Y = Tile.Y;
		Content.Layers = ToLayerCounts(TileCounts[Tile]);
		Content.StaleActorCount = TileStale.FindRef(Tile);
	}

	if (UTwinBLDToolsetSubsystem::GetSession())
	{
		Context.GeoReference = UTwinBLDLocationToolset::GetGeoReference();
	}
	Context.RunningJobs = FBLDJobRegistry::Get().ListJobs(TEXT("TwinBLD."), true);

	if (!Context.GeoReference.bHasGeoOrigin)
	{
		Context.Notes.Add(TEXT("The level has no geo origin. Start with TwinBLDLocationToolset.GeocodePlace, SuggestImportArea and SetGeoOrigin."));
	}
	if (Context.StaleActorCount > 0)
	{
		Context.Notes.Add(FString::Printf(TEXT("%d generated actors predate the current geo origin and are misplaced. Clear and regenerate their tiles."), Context.StaleActorCount));
	}
	if (Context.UntaggedBuildingCount > 0 && !TypeCounts.Contains(TEXT("Building")))
	{
		Context.Notes.Add(TEXT("The level has modular buildings that TwinBLD did not generate. FindGenerated skips them unless bIncludeUntagged is true."));
	}
	if (Context.bHasModularBuildings && !Context.bHasRoadNetwork)
	{
		Context.Notes.Add(TEXT("There are buildings but no road network, so DetectFacades cannot run. Generate roads, or set bAllFloorsFacade with EditBuildingFromReality."));
	}
	if (Context.bHasLandscape && TypeCounts.Contains(TEXT("Building")))
	{
		Context.Notes.Add(TEXT("If buildings float or sink into the terrain, run SnapToLandscape."));
	}

	return Context;
}

FTwinBLDFindResult UTwinBLDSceneToolset::FindGenerated(
	const FString& Type,
	TOptional<FTwinBLDGeoBox> Bounds,
	const TArray<FIntPoint>& Tiles,
	const FString& OsmTagFilter,
	const double MinHeightMeters,
	const double MaxHeightMeters,
	const bool bIncludeUntagged,
	const int32 MaxResults)
{
	using namespace TwinBLDScenePrivate;

	FTwinBLDFindResult Result;
	UWorld* World = BLDToolset::GetEditorWorld();
	if (!World)
	{
		RaiseError(TEXT("No editor world is loaded."));
		return Result;
	}

	const int32 Limit = FMath::Clamp(MaxResults, 1, 1000);
	FString Error;

	FBox2D WorldBounds(ForceInit);
	TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeLevelProjection(Error);
	if (Bounds.IsSet())
	{
		if (!TwinBLDGeo::ValidateBox(Bounds.GetValue(), TEXT("Bounds"), Error))
		{
			RaiseError(Error);
			return Result;
		}
		if (!Projection)
		{
			RaiseError(Error);
			return Result;
		}
		WorldBounds = Projection->ToWorldBox(Bounds.GetValue());
	}

	FTagFilter TagFilter;
	const bool bUseTagFilter = !OsmTagFilter.TrimStartAndEnd().IsEmpty();
	if (bUseTagFilter && !TagFilter.Parse(OsmTagFilter, Error))
	{
		RaiseError(Error);
		return Result;
	}

	const FOsmIndex OsmIndex(UTwinBLDToolsetSubsystem::GetSession());
	if (bUseTagFilter && !OsmIndex.IsLoaded())
	{
		RaiseError(TEXT("OsmTagFilter needs the source OSM data. Load it with TwinBLDImportToolset.LoadOsmFile (or FetchOsm) first."));
		return Result;
	}

	const TSet<FIntPoint> TileSet(Tiles);
	const bool bHeightFilter = MinHeightMeters >= 0.0 || MaxHeightMeters >= 0.0;

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		FString ActorType = GetGeneratedType(Actor);
		const AModularBuildingActor* Building = Cast<AModularBuildingActor>(Actor);

		if (ActorType.IsEmpty())
		{
			if (!bIncludeUntagged || !Building)
			{
				continue;
			}
			ActorType = TEXT("Untagged");
		}

		if (!Type.IsEmpty() && ActorType != TEXT("Untagged") && !MatchesType(ActorType, Type))
		{
			continue;
		}

		if (TileSet.Num() > 0)
		{
			FIntPoint Tile;
			if (!GetTile(Actor, Tile) || !TileSet.Contains(Tile))
			{
				continue;
			}
		}

		if (bHeightFilter)
		{
			if (!Building)
			{
				continue;
			}
			const double HeightMeters = Building->BuildingHeight / 100.0;
			if ((MinHeightMeters >= 0.0 && HeightMeters < MinHeightMeters) || (MaxHeightMeters >= 0.0 && HeightMeters > MaxHeightMeters))
			{
				continue;
			}
		}

		const FVector Location = Building ? GetFootprintCenter(Building) : Actor->GetActorLocation();
		if (WorldBounds.bIsValid && !WorldBounds.IsInside(FVector2D(Location)))
		{
			continue;
		}

		if (bUseTagFilter)
		{
			FOsmMatch Match;
			if (!FindOsm(Actor, OsmIndex, Match) || !TagFilter.Matches(*Match.Tags))
			{
				continue;
			}
		}

		++Result.TotalCount;
		if (Result.Actors.Num() < Limit)
		{
			Result.Actors.Add(MakeInfo(Actor, Projection.Get()));
		}
	}

	Result.ReturnedCount = Result.Actors.Num();
	if (Result.TotalCount > Result.ReturnedCount)
	{
		Result.Warnings.Add(FString::Printf(TEXT("Showing %d of %d matches. Narrow the search with Bounds, Tiles or filters."), Result.ReturnedCount, Result.TotalCount));
	}
	return Result;
}

FTwinBLDActorDescription UTwinBLDSceneToolset::DescribeGeneratedActor(AActor* Actor)
{
	using namespace TwinBLDScenePrivate;

	FTwinBLDActorDescription Description;
	if (!IsValid(Actor))
	{
		RaiseError(TEXT("Actor is required. Pass {\"refPath\": ...} from FindGenerated."));
		return Description;
	}

	FString Error;
	const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeLevelProjection(Error);
	Description.Info = MakeInfo(Actor, Projection.Get());

	for (const FName& Tag : Actor->Tags)
	{
		Description.ActorTags.Add(Tag.ToString());
	}

	if (const AModularBuildingActor* Building = Cast<AModularBuildingActor>(Actor))
	{
		Description.FootprintVertexCount = Building->ShapePoints.Num();
		Description.FloorHeights = Building->FloorHeights;
		Description.FloorPlateCount = Building->bUseAuthoredFloorPlates ? Building->AuthoredFloorPlates.Num() : 0;
		Description.bAllFloorsFacade = Building->bAllFloorsFacade;
		Description.bPreciseHeight = Building->bPreciseHeight;
		Description.RoofOverride = DescribeRoof(Building->RoofOverride);
	}

	const FOsmIndex OsmIndex(UTwinBLDToolsetSubsystem::GetSession());
	if (!OsmIndex.IsLoaded())
	{
		Description.Notes.Add(TEXT("Load the source OSM data with TwinBLDImportToolset.LoadOsmFile to see the original OSM tags."));
		return Description;
	}

	FOsmMatch Match;
	if (!FindOsm(Actor, OsmIndex, Match))
	{
		Description.Notes.Add(TEXT("No element of the loaded OSM data matches this actor. It may come from a different OSM file or was placed by hand."));
		return Description;
	}

	Description.bOsmMatched = true;
	Description.OsmMatchMethod = Match.Method;
	Description.OsmName = Match.Name;
	Description.OsmHeightMeters = Match.HeightMeters;
	Description.OsmLevels = Match.Levels;
	for (const TPair<FName, FString>& Tag : *Match.Tags)
	{
		FTwinBLDKeyValue& Entry = Description.OsmTags.AddDefaulted_GetRef();
		Entry.Key = Tag.Key.ToString();
		Entry.Value = Tag.Value;
	}
	Description.OsmTags.Sort([](const FTwinBLDKeyValue& A, const FTwinBLDKeyValue& B) { return A.Key < B.Key; });

	if (const AModularBuildingActor* Building = Cast<AModularBuildingActor>(Actor))
	{
		if (Match.HeightMeters > 0.0 && FMath::Abs(Building->BuildingHeight / 100.0 - Match.HeightMeters) > 3.0)
		{
			Description.Notes.Add(FString::Printf(
				TEXT("The building is %.1f m tall but OSM says %.1f m. Fix with EditBuildingFromReality (HeightMeters, bPreciseHeight=true)."),
				Building->BuildingHeight / 100.0, Match.HeightMeters));
		}
	}

	return Description;
}

FTwinBLDSnapResult UTwinBLDSceneToolset::SnapToLandscape(const TArray<AActor*>& Actors, const ETwinBLDSnapTarget Target)
{
	using namespace TwinBLDScenePrivate;

	FTwinBLDSnapResult Result;
	if (!UTwinBLDToolsetSubsystem::EnsureAuthorizedOrRaise())
	{
		return Result;
	}
	UWorld* World = BLDToolset::GetEditorWorld();
	if (!World)
	{
		RaiseError(TEXT("No editor world is loaded."));
		return Result;
	}

	if (!UTwinBLDGenerationUtils::HasLandscapeActorInLevel(World))
	{
		RaiseError(TEXT("The level has no landscape to snap to. Generate one with TwinBLDImportToolset.GenerateTiles (bGenerateLandscape)."));
		return Result;
	}

	TArray<AModularBuildingActor*> Buildings;
	TArray<ADynamicRoad*> Roads;
	if (Actors.Num() > 0)
	{
		for (AActor* Actor : Actors)
		{
			if (AModularBuildingActor* Building = Cast<AModularBuildingActor>(Actor))
			{
				Buildings.AddUnique(Building);
			}
			else if (ADynamicRoad* Road = Cast<ADynamicRoad>(Actor))
			{
				Roads.AddUnique(Road);
			}
			else if (ARoadGeo* Geo = Cast<ARoadGeo>(Actor))
			{
				if (ADynamicRoad* SourceRoad = Geo->GetSingleSourceRoad())
				{
					Roads.AddUnique(SourceRoad);
				}
			}
			else if (IsValid(Actor))
			{
				Result.Warnings.Add(FString::Printf(TEXT("%s is not a building or road and was skipped."), *Actor->GetActorLabel()));
			}
		}
	}
	else
	{
		if (Target != ETwinBLDSnapTarget::Roads)
		{
			for (AActor* Actor : CollectGenerated(World, TEXT("Building"), AModularBuildingActor::StaticClass()))
			{
				Buildings.Add(CastChecked<AModularBuildingActor>(Actor));
			}
		}
		if (Target != ETwinBLDSnapTarget::Buildings)
		{
			for (AActor* Actor : CollectGenerated(World, TEXT("Road"), ADynamicRoad::StaticClass()))
			{
				Roads.Add(CastChecked<ADynamicRoad>(Actor));
			}
		}
	}

	if (Buildings.IsEmpty() && Roads.IsEmpty())
	{
		RaiseError(TEXT("Nothing to snap. There are no generated buildings or roads of that type; pass Actors explicitly to snap hand-placed ones."));
		return Result;
	}

	TMap<AModularBuildingActor*, double> BuildingZBefore;
	for (AModularBuildingActor* Building : Buildings)
	{
		BuildingZBefore.Add(Building, Building->GetActorLocation().Z);
	}

	TMap<ADynamicRoad*, TArray<double>> RoadZBefore;
	for (ADynamicRoad* Road : Roads)
	{
		RoadZBefore.Add(Road, GetControlPointHeights(Road));
	}

	{
		TArray<AActor*> Targets;
		Targets.Append(Buildings);
		Targets.Append(Roads);
		const FScopedSelection Selection(Targets);

		if (!Buildings.IsEmpty())
		{
			UTwinBLDMapUtilsLibrary::SnapBuildingsToLandscape(World);
		}
		if (!Roads.IsEmpty())
		{
			UTwinBLDMapUtilsLibrary::SnapRoadsToLandscape(World);
		}
	}

	Result.BuildingTargets = Buildings.Num();
	for (AModularBuildingActor* Building : Buildings)
	{
		if (IsValid(Building) && !FMath::IsNearlyEqual(Building->GetActorLocation().Z, BuildingZBefore[Building], 0.5))
		{
			++Result.BuildingsSnapped;
		}
		else
		{
			AddUnchanged(Result.Unchanged, Result.UnchangedCount, Building);
		}
	}

	Result.RoadTargets = Roads.Num();
	for (ADynamicRoad* Road : Roads)
	{
		const TArray<double> After = GetControlPointHeights(Road);
		const TArray<double>& Before = RoadZBefore[Road];
		bool bMoved = false;
		for (int32 Index = 0; Index < FMath::Min(Before.Num(), After.Num()) && !bMoved; ++Index)
		{
			bMoved = !FMath::IsNearlyEqual(Before[Index], After[Index], 0.5);
		}

		if (bMoved)
		{
			++Result.RoadsSnapped;
		}
		else
		{
			AddUnchanged(Result.Unchanged, Result.UnchangedCount, Road);
		}
	}

	if (Result.UnchangedCount > 0)
	{
		Result.Warnings.Add(FString::Printf(
			TEXT("%d targets did not move: they already sit on the landscape or have no landscape underneath."),
			Result.UnchangedCount));
	}
	if (Result.RoadsSnapped > 0)
	{
		Result.Warnings.Add(TEXT("Snapped roads are rebuilding in the background. Capture after RoadBLDBuildToolset.WaitForRebuild or RoadBLDFeedbackToolset.CaptureViewport (which waits)."));
	}

	return Result;
}

FTwinBLDFacadeResult UTwinBLDSceneToolset::DetectFacades(const TArray<AModularBuildingActor*>& Buildings)
{
	using namespace TwinBLDScenePrivate;

	FTwinBLDFacadeResult Result;
	if (!UTwinBLDToolsetSubsystem::EnsureAuthorizedOrRaise())
	{
		return Result;
	}
	UWorld* World = BLDToolset::GetEditorWorld();
	if (!World)
	{
		RaiseError(TEXT("No editor world is loaded."));
		return Result;
	}

	if (!UTwinBLDGenerationUtils::HasRoadNetworkActor(World))
	{
		RaiseError(TEXT("DetectFacades needs a road network. Generate roads first, or set bAllFloorsFacade=true with EditBuildingFromReality for buildings without streets."));
		return Result;
	}

	TArray<AModularBuildingActor*> Targets;
	for (AModularBuildingActor* Building : Buildings)
	{
		if (IsValid(Building))
		{
			Targets.AddUnique(Building);
		}
	}

	if (Targets.IsEmpty())
	{
		for (AActor* Actor : CollectGenerated(World, TEXT("Building"), AModularBuildingActor::StaticClass()))
		{
			Targets.Add(CastChecked<AModularBuildingActor>(Actor));
		}
	}

	if (Targets.IsEmpty())
	{
		RaiseError(TEXT("There are no generated buildings. Pass Buildings explicitly to process hand-placed ones."));
		return Result;
	}

	TMap<AModularBuildingActor*, TArray<int32>> FacesBefore;
	for (AModularBuildingActor* Building : Targets)
	{
		FacesBefore.Add(Building, Building->StreetFacingFaces);
	}

	{
		const FScopedSelection Selection{ TArray<AActor*>(Targets) };
		UTwinBLDMapUtilsLibrary::DetectBuildingFacadesSmart(World);
	}

	Result.Targets = Targets.Num();
	for (AModularBuildingActor* Building : Targets)
	{
		if (IsValid(Building) && Building->StreetFacingFaces != FacesBefore[Building])
		{
			++Result.Updated;
		}
		else
		{
			AddUnchanged(Result.Unchanged, Result.UnchangedCount, Building);
		}
	}

	if (Result.UnchangedCount > 0)
	{
		Result.Warnings.Add(FString::Printf(
			TEXT("%d buildings kept their street-facing faces: no road edge was close enough, or detection found the same faces as before."),
			Result.UnchangedCount));
	}

	return Result;
}

FTwinBLDBuildingEditResult UTwinBLDSceneToolset::EditBuildingFromReality(AModularBuildingActor* Building, const FTwinBLDBuildingEdit& Edit, const bool bRegenerate)
{
	using namespace TwinBLDScenePrivate;

	FTwinBLDBuildingEditResult Result;
	if (!UTwinBLDToolsetSubsystem::EnsureAuthorizedOrRaise())
	{
		return Result;
	}
	if (!IsValid(Building))
	{
		RaiseError(TEXT("Building is required. Pass {\"refPath\": ...} from FindGenerated."));
		return Result;
	}

	if (Edit.HeightMeters.IsSet() && (Edit.HeightMeters.GetValue() <= 0.0 || Edit.HeightMeters.GetValue() > 1000.0))
	{
		RaiseError(TEXT("Edit.HeightMeters must be between 0 and 1000."));
		return Result;
	}
	if (Edit.Levels.IsSet() && (Edit.Levels.GetValue() < 1 || Edit.Levels.GetValue() > 250))
	{
		RaiseError(TEXT("Edit.Levels must be between 1 and 250."));
		return Result;
	}
	if (Edit.RoofHeightMeters.IsSet() && (Edit.RoofHeightMeters.GetValue() < 0.0 || Edit.RoofHeightMeters.GetValue() > 200.0))
	{
		RaiseError(TEXT("Edit.RoofHeightMeters must be between 0 and 200."));
		return Result;
	}
	for (int32 Index = 0; Index < Edit.FloorPlates.Num(); ++Index)
	{
		const FTwinBLDFloorPlateSpec& Plate = Edit.FloorPlates[Index];
		if (Plate.OutlineWorldCm.Num() < 3)
		{
			RaiseError(FString::Printf(TEXT("Edit.FloorPlates[%d].OutlineWorldCm needs at least 3 points."), Index));
			return Result;
		}
		if (Plate.StartHeightMeters < 0.0)
		{
			RaiseError(FString::Printf(TEXT("Edit.FloorPlates[%d].StartHeightMeters must not be negative."), Index));
			return Result;
		}
	}

	const FScopedTransaction Transaction(LOCTEXT("EditBuildingFromReality", "Edit Building From Reality"));
	Building->Modify();

	const double OldHeightMeters = Building->BuildingHeight / 100.0;
	if (Edit.HeightMeters.IsSet())
	{
		Building->BuildingHeight = Edit.HeightMeters.GetValue() * 100.0;
	}
	else if (Edit.Levels.IsSet())
	{
		Building->BuildingHeight = Edit.Levels.GetValue() * MetersPerLevel * 100.0;
	}
	if (!FMath::IsNearlyEqual(OldHeightMeters, Building->BuildingHeight / 100.0, 0.01))
	{
		Result.Changes.Add(FString::Printf(TEXT("Height %.1f m -> %.1f m"), OldHeightMeters, Building->BuildingHeight / 100.0));
	}

	FBuildingRoofOverride& Roof = Building->RoofOverride;
	if (Edit.RoofType.IsSet())
	{
		Roof.bOverrideType = true;
		Roof.Type = Edit.RoofType.GetValue();
		Result.Changes.Add(FString::Printf(TEXT("Roof type %s"), *StaticEnum<ERoofType>()->GetNameStringByValue(static_cast<int64>(Roof.Type))));
	}
	if (Edit.RoofHeightMeters.IsSet())
	{
		Roof.bOverrideRidgeHeight = true;
		Roof.RidgeHeight = Edit.RoofHeightMeters.GetValue() * 100.0;
		Result.Changes.Add(FString::Printf(TEXT("Roof ridge height %.1f m"), Edit.RoofHeightMeters.GetValue()));
	}
	if (Edit.RoofDirectionDegrees.IsSet())
	{
		FString Error;
		if (const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeLevelProjection(Error))
		{
			const double Bearing = FMath::DegreesToRadians(Edit.RoofDirectionDegrees.GetValue());
			const FVector2D WorldDirection = Projection->WorldNorth() * FMath::Cos(Bearing) + Projection->WorldEast() * FMath::Sin(Bearing);
			const FVector LocalDirection = Building->GetActorTransform().InverseTransformVectorNoScale(FVector(WorldDirection, 0.0));
			Roof.bOverrideRidgeDirection = true;
			Roof.RidgeDirectionDegrees = FMath::RadiansToDegrees(FMath::Atan2(LocalDirection.Y, LocalDirection.X));
			Result.Changes.Add(FString::Printf(TEXT("Roof ridge bearing %.0f deg (%.0f deg actor-local)"), Edit.RoofDirectionDegrees.GetValue(), Roof.RidgeDirectionDegrees));
		}
		else
		{
			Result.Warnings.Add(FString::Printf(TEXT("RoofDirectionDegrees was ignored: %s"), *Error));
		}
	}
	if (Edit.bRoofAcross.IsSet())
	{
		Roof.bOverrideRidgeOrientation = true;
		Roof.bRidgeAcross = Edit.bRoofAcross.GetValue();
		Result.Changes.Add(Roof.bRidgeAcross ? TEXT("Roof ridge across") : TEXT("Roof ridge along"));
	}
	if (Edit.bPreciseHeight.IsSet() && Building->bPreciseHeight != Edit.bPreciseHeight.GetValue())
	{
		Building->bPreciseHeight = Edit.bPreciseHeight.GetValue();
		Result.Changes.Add(FString::Printf(TEXT("bPreciseHeight %s"), Building->bPreciseHeight ? TEXT("true") : TEXT("false")));
	}
	if (Edit.bAllFloorsFacade.IsSet() && Building->bAllFloorsFacade != Edit.bAllFloorsFacade.GetValue())
	{
		Building->bAllFloorsFacade = Edit.bAllFloorsFacade.GetValue();
		Result.Changes.Add(FString::Printf(TEXT("bAllFloorsFacade %s"), Building->bAllFloorsFacade ? TEXT("true") : TEXT("false")));
	}

	if (Edit.bClearFloorPlates || Edit.FloorPlates.Num() > 0)
	{
		Building->ClearAuthoredFloorPlates();
		const FTransform ActorTransform = Building->GetActorTransform();
		for (const FTwinBLDFloorPlateSpec& Plate : Edit.FloorPlates)
		{
			const int32 PlateIndex = Building->AddAuthoredFloorPlate(Plate.StartHeightMeters * 100.0);

			TArray<FVector2D> LocalOutline;
			LocalOutline.Reserve(Plate.OutlineWorldCm.Num());
			for (const FVector2D& Point : Plate.OutlineWorldCm)
			{
				LocalOutline.Add(FVector2D(ActorTransform.InverseTransformPosition(FVector(Point, ActorTransform.GetLocation().Z))));
			}
			Building->AddAuthoredShellToPlate(PlateIndex, LocalOutline);

			if (Plate.RoofType.IsSet() || Plate.RoofHeightMeters.IsSet())
			{
				FBuildingRoofOverride PlateRoof;
				if (Plate.RoofType.IsSet())
				{
					PlateRoof.bOverrideType = true;
					PlateRoof.Type = Plate.RoofType.GetValue();
				}
				if (Plate.RoofHeightMeters.IsSet())
				{
					PlateRoof.bOverrideRidgeHeight = true;
					PlateRoof.RidgeHeight = Plate.RoofHeightMeters.GetValue() * 100.0;
				}
				Building->SetAuthoredFloorPlateRoofOverride(PlateIndex, PlateRoof);
			}
		}
		Building->SetUseAuthoredFloorPlates(Edit.FloorPlates.Num() > 0);
		Result.Changes.Add(Edit.FloorPlates.Num() > 0
			? FString::Printf(TEXT("%d floor plates"), Edit.FloorPlates.Num())
			: FString(TEXT("Floor plates cleared")));
	}

	Result.Building = BLDToolset::MakeActorRef(Building);
	Result.HeightMeters = Building->BuildingHeight / 100.0;
	Result.FloorPlateCount = Building->bUseAuthoredFloorPlates ? Building->AuthoredFloorPlates.Num() : 0;

	if (Result.Changes.IsEmpty())
	{
		Result.Warnings.Add(TEXT("Edit had no fields set, so nothing changed."));
		return Result;
	}

	if (bRegenerate)
	{
		Building->GenerateModularBuilding();
		Result.bRegenerated = true;
	}
	Building->MarkPackageDirty();
	return Result;
}


FBLDIssueReport UTwinBLDSceneToolset::ValidateTwinScene()
{
	const FTwinBLDSceneContext Context = GetSceneContext();
	FBLDIssueReport Report;

	if (!Context.bHasLandscape)
	{
		Report.Issues.Add(BLDValidation::MakeIssue(
			EBLDIssueSeverity::Warning,
			TEXT("TwinBLD"),
			TEXT("MissingLandscape"),
			TEXT("No TwinBLD landscape is present in the level."),
			FBLDActorRef(),
			FBLDActorRef(),
			FVector::ZeroVector,
			0.0,
			TEXT("Import map data or add a landscape before snapping buildings/roads.")));
	}
	if (!Context.bHasRoadNetwork)
	{
		Report.Issues.Add(BLDValidation::MakeIssue(
			EBLDIssueSeverity::Warning,
			TEXT("TwinBLD"),
			TEXT("MissingRoadNetwork"),
			TEXT("No TwinBLD/RoadBLD road network was found."),
			FBLDActorRef(),
			FBLDActorRef(),
			FVector::ZeroVector,
			0.0,
			TEXT("Import roads or author a RoadBLD network before DetectFacades.")));
	}
	if (Context.StaleActorCount > 0)
	{
		Report.Issues.Add(BLDValidation::MakeIssue(
			EBLDIssueSeverity::Error,
			TEXT("TwinBLD"),
			TEXT("StaleGeoActors"),
			FString::Printf(TEXT("%d generated actors predate the current geo origin and are misplaced."), Context.StaleActorCount),
			FBLDActorRef(),
			FBLDActorRef(),
			FVector::ZeroVector,
			0.0,
			TEXT("Clear and regenerate their tiles after SetGeoOrigin.")));
	}
	if (Context.UntaggedBuildingCount > 0)
	{
		Report.Issues.Add(BLDValidation::MakeIssue(
			EBLDIssueSeverity::Info,
			TEXT("TwinBLD"),
			TEXT("UntaggedBuildings"),
			FString::Printf(TEXT("%d modular buildings lack TwinBLD tags and are skipped by FindGenerated unless bIncludeUntagged is true."), Context.UntaggedBuildingCount),
			FBLDActorRef(),
			FBLDActorRef(),
			FVector::ZeroVector,
			0.0,
			TEXT("Use bIncludeUntagged or tag TwinBLD-generated content.")));
	}

	Report.Notes.Append(Context.Notes);
	BLDValidation::FinalizeReport(Report);
	return Report;
}
#undef LOCTEXT_NAMESPACE
