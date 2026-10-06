// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "BLDToolsetTypes.h"
#include "CityBLDTypes.h"
#include "Common/TwinBLDToolsetTypes.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "TwinBLDSceneToolset.generated.h"

class AActor;
class AModularBuildingActor;

UENUM(BlueprintType)
enum class ETwinBLDSnapTarget : uint8
{
	Buildings,
	Roads,
	Both
};

USTRUCT(BlueprintType)
struct FTwinBLDLayerCount
{
	GENERATED_BODY()

	/** Generated content type: Building, Road, RoadNetwork, CustomRoadShape, Parcel, Landscape, LandscapePCG, Satellite or Detail.*. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Type;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 Count = 0;
};

USTRUCT(BlueprintType)
struct FTwinBLDTileContent
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 X = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 Y = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDLayerCount> Layers;

	/** Layers generated with an older geo origin. Clear and regenerate them. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 StaleActorCount = 0;
};

USTRUCT(BlueprintType)
struct FTwinBLDSceneContext
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bHasLandscape = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bHasRoadNetwork = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bHasModularBuildings = false;

	/** Actors TwinBLD generated, by type. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDLayerCount> GeneratedCounts;

	/** Generated content per tile, capped at 100 tiles. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDTileContent> Tiles;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 TileCount = 0;

	/** Generated actors tagged TwinBLD.GeoTransform.Stale because the geo origin changed after they were generated. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 StaleActorCount = 0;

	/** Modular buildings without TwinBLD tags (hand-placed or from other tools). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 UntaggedBuildingCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoReference GeoReference;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FBLDJobStatus> RunningJobs;

	/** Suggested next steps. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Notes;
};

USTRUCT(BlueprintType)
struct FTwinBLDGeneratedActorInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FBLDActorRef Actor;

	/** Generated content type from the TwinBLD.Type.* tag, or Untagged. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Type;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bHasTile = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FIntPoint Tile = FIntPoint::ZeroValue;

	/** Source OSM element such as way/123456, when known. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString OsmRef;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bHasGeo = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint Geo;

	/** Building height in meters. 0 for non-buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double HeightMeters = 0.0;

	/** BuildingStyle class path for buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString StyleClassPath;

	/** Generated with an older geo origin. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bStale = false;
};

USTRUCT(BlueprintType)
struct FTwinBLDFindResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDGeneratedActorInfo> Actors;

	/** Matches before the MaxResults cap. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 TotalCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 ReturnedCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Warnings;
};

USTRUCT(BlueprintType)
struct FTwinBLDActorDescription
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeneratedActorInfo Info;

	/** True when the actor was matched to an element of the loaded OSM data. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bOsmMatched = false;

	/** How the OSM element was found: Tag (TwinBLD.OSM tag) or Footprint (nearest building outline). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString OsmMatchMethod;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString OsmName;

	/** Original OSM tags, such as building=church, roof:shape=gabled, building:material=brick. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDKeyValue> OsmTags;

	/** Height from OSM in meters, 0 when OSM has none. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double OsmHeightMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 OsmLevels = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 FootprintVertexCount = 0;

	/** Floor heights in cm, bottom first. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<float> FloorHeights;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 FloorPlateCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bAllFloorsFacade = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bPreciseHeight = false;

	/** Roof override summary, such as "Hipped, ridge 3.5 m". Empty when the style's roof is used. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString RoofOverride;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> ActorTags;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Notes;
};

USTRUCT(BlueprintType)
struct FTwinBLDSnapResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 BuildingTargets = 0;

	/** Buildings moved to the landscape surface. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 BuildingsSnapped = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 RoadTargets = 0;

	/** Roads with at least one control point moved to the landscape surface. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 RoadsSnapped = 0;

	/** Targets with no landscape underneath or already on it, capped at 50. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FBLDActorRef> Unchanged;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 UnchangedCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Warnings;
};

USTRUCT(BlueprintType)
struct FTwinBLDFacadeResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 Targets = 0;

	/** Buildings whose street-facing faces changed and were regenerated. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 Updated = 0;

	/** Buildings with no road edge close enough, capped at 50. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FBLDActorRef> Unchanged;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 UnchangedCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Warnings;
};

/** One tier of a stepped building, such as a podium with a tower on top. */
USTRUCT(BlueprintType)
struct FTwinBLDFloorPlateSpec
{
	GENERATED_BODY()

	/** Height above the building base where this tier starts, in meters. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double StartHeightMeters = 0.0;

	/** Tier outline as world XY in cm (use TwinBLDLocationToolset.GeoToWorld for OSM building:part outlines). At least 3 points. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FVector2D> OutlineWorldCm;

	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<ERoofType> RoofType;

	/** Roof ridge height above the tier top, in meters. */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<double> RoofHeightMeters;
};

/** Real-world measurements to apply to a building. Unset fields are left unchanged. */
USTRUCT(BlueprintType)
struct FTwinBLDBuildingEdit
{
	GENERATED_BODY()

	/** Total height to the roof base in meters (OSM height minus roof:height). */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<double> HeightMeters;

	/** Above-ground floors (OSM building:levels). Sets the height at 3 m per floor when HeightMeters is not given. */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<int32> Levels;

	/** Roof shape. OSM roof:shape flat, gabled, hipped, pyramidal, dome and skillion map to Flat, AdvancedGable, Hipped, Pyramidal, Dome and Skillion. */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<ERoofType> RoofType;

	/** Roof ridge height above the roof base, in meters (OSM roof:height). */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<double> RoofHeightMeters;

	/** Ridge compass bearing in degrees clockwise from north (OSM roof:direction). Converted to the actor's local frame. */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<double> RoofDirectionDegrees;

	/** Ridge runs across the short axis (OSM roof:orientation=across). */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<bool> bRoofAcross;

	/** Stretch floors so the building reaches HeightMeters exactly instead of snapping to whole modules. */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<bool> bPreciseHeight;

	/** Use facade meshes on every face (for buildings with no nearby roads). */
	UPROPERTY(EditAnywhere, Category = "TwinBLDToolset")
	TOptional<bool> bAllFloorsFacade;

	/** Replace the building's tiers. Pass an empty list with bClearFloorPlates=true to go back to a single extrusion. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDFloorPlateSpec> FloorPlates;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bClearFloorPlates = false;
};

USTRUCT(BlueprintType)
struct FTwinBLDBuildingEditResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FBLDActorRef Building;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double HeightMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 FloorPlateCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bRegenerated = false;

	/** What changed, one line per field. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Changes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Warnings;
};

/**
 * Inspect and fix content TwinBLD generated, with its real-world metadata.
 * TwinBLD tags generated actors TwinBLD.Type.<Type>, TwinBLD.Tile=<X>,<Y> and, for imports run through
 * TwinBLDImportToolset, TwinBLD.OSM=<way|relation|node>/<id>. Start with GetSceneContext, narrow down with
 * FindGenerated, read original OSM tags with DescribeGeneratedActor, then fix with SnapToLandscape, DetectFacades and
 * EditBuildingFromReality. Every edit is one undoable transaction. Actor parameters take {"refPath": "..."}.
 * Heights are meters in these tools; world positions are Unreal centimeters.
 * For TwinBLD packaging, cook, compile, or plugin-load errors, call WorldBLDToolset.UWorldBLDToolset.GetPackagingGuide.
 */
UCLASS(BlueprintType, MinimalAPI)
class UTwinBLDSceneToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/** Summarizes the level: landscape, roads and buildings present, generated content by type and tile, stale content, geo origin and running jobs. */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDSceneContext GetSceneContext();

	/**
	 * Finds generated actors.
	 * @param Type Content type such as Building or Road. Empty matches every type.
	 * @param Bounds Optional geographic area. Needs a geo origin.
	 * @param Tiles Optional tiles to search.
	 * @param OsmTagFilter Optional OSM tag filter such as "building=church", "amenity" (any value) or "height>50". Needs the source OSM data loaded (TwinBLDImportToolset.LoadOsmFile).
	 * @param MinHeightMeters Only buildings at least this tall. Negative disables the filter.
	 * @param MaxHeightMeters Only buildings at most this tall. Negative disables the filter.
	 * @param bIncludeUntagged Also include modular buildings without TwinBLD tags.
	 * @param MaxResults Maximum actors to return (1-1000).
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDFindResult FindGenerated(
		const FString& Type,
		TOptional<FTwinBLDGeoBox> Bounds,
		const TArray<FIntPoint>& Tiles,
		const FString& OsmTagFilter = TEXT(""),
		double MinHeightMeters = -1.0,
		double MaxHeightMeters = -1.0,
		bool bIncludeUntagged = false,
		int32 MaxResults = 100);

	/**
	 * Describes a generated actor, including the original OSM tags when the source OSM data is loaded.
	 * @param Actor Actor to describe.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDActorDescription DescribeGeneratedActor(AActor* Actor);

	/**
	 * Moves buildings and road control points onto the landscape surface. Roads are rebuilt afterwards. Mutating.
	 * The user's editor selection is left unchanged.
	 * @param Actors Buildings, roads or road geometry to snap. When empty, every generated actor of Target is snapped.
	 * @param Target Which kind of actor to snap when Actors is empty.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDSnapResult SnapToLandscape(const TArray<AActor*>& Actors, ETwinBLDSnapTarget Target = ETwinBLDSnapTarget::Both);

	/**
	 * Detects which faces of each building face a street, using nearby road edges, and regenerates the buildings. Requires a
	 * road network. Mutating. The user's editor selection is left unchanged.
	 * @param Buildings Buildings to process. When empty, every generated building is processed.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDFacadeResult DetectFacades(const TArray<AModularBuildingActor*>& Buildings);

	/**
	 * Applies real-world measurements to a building: height, levels, roof shape and direction, and stepped tiers. Mutating.
	 * @param Building Building to edit.
	 * @param Edit Fields to change. Unset fields are left as they are.
	 * @param bRegenerate Regenerate the building meshes after editing.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDBuildingEditResult EditBuildingFromReality(AModularBuildingActor* Building, const FTwinBLDBuildingEdit& Edit, bool bRegenerate = true);

	/**
	 * Builds a shared FBLDIssueReport from the current TwinBLD scene (stale geo, missing landscape/roads, untagged buildings).
	 * Read-only. Use after import or geo-origin changes, and from WorldBLDValidationToolset.RunValidationLoop.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FBLDIssueReport ValidateTwinScene();
};
