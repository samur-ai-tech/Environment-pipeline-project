// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "BLDToolsetTypes.h"
#include "ToolsetRegistry/ToolCallAsyncResult.h"

#include "TwinBLDToolsetTypes.generated.h"

/** A WGS84 location in decimal degrees. */
USTRUCT(BlueprintType)
struct FTwinBLDGeoPoint
{
	GENERATED_BODY()

	/** Latitude in degrees, -90 (south) to 90 (north). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double Lat = 0.0;

	/** Longitude in degrees, -180 (west) to 180 (east). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double Lon = 0.0;
};

/** A WGS84 bounding box in decimal degrees. */
USTRUCT(BlueprintType)
struct FTwinBLDGeoBox
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double South = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double West = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double North = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double East = 0.0;
};

USTRUCT(BlueprintType)
struct FTwinBLDKeyValue
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Key;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Value;
};

/** A place found by geocoding. */
USTRUCT(BlueprintType)
struct FTwinBLDPlace
{
	GENERATED_BODY()

	/** Short name, such as "Flatiron Building". Empty for unnamed features. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Name;

	/** Full address line. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString DisplayName;

	/** OSM key of the main tag, such as building, tourism or place. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Category;

	/** OSM value of the main tag, such as yes, attraction or city. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Type;

	/** node, way or relation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString OsmType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int64 OsmId = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint Location;

	/** Extent of the feature. Pass to SuggestImportArea to import the whole feature. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoBox Bounds;

	/** Wikidata item such as Q220728, when the feature links one. Use with LookupLandmark. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString WikidataId;

	/** Search ranking from 0 to 1. Higher is more prominent. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double Importance = 0.0;

	/** Address parts such as road, city and country. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDKeyValue> Address;

	/** Extra OSM tags such as height, building:levels or wikipedia. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDKeyValue> ExtraTags;
};

USTRUCT(BlueprintType)
struct FTwinBLDGeocodeResult
{
	GENERATED_BODY()

	/** Best matches first. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDPlace> Places;

	/** True when the answer came from the local cache. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bFromCache = false;

	/** Data license attribution to keep with any use of the results. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Attribution;
};

/** Async tool result that completes with geocoding matches. */
UCLASS()
class UTwinBLDGeocodeAsyncResult : public UToolCallAsyncResult
{
	GENERATED_BODY()

public:
	bool SetValue(const FTwinBLDGeocodeResult& InValue)
	{
		FTwinBLDGeocodeResult ValueCopy = InValue;
		return MaybeBroadcastSuccessfulCompletion(MoveTemp(ValueCopy), Value);
	}

	UPROPERTY()
	FTwinBLDGeocodeResult Value;
};

/** One TwinBLD import tile. */
USTRUCT(BlueprintType)
struct FTwinBLDTileInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 X = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 Y = 0;

	/** World-space corner with the smallest X and Y, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FVector2D WorldMinCm = FVector2D::ZeroVector;

	/** World-space corner with the largest X and Y, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FVector2D WorldMaxCm = FVector2D::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoBox GeoBounds;
};

USTRUCT(BlueprintType)
struct FTwinBLDImportAreaSuggestion
{
	GENERATED_BODY()

	/** Area to fetch and import. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoBox Bounds;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint Center;

	/** East-west size in meters. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double WidthMeters = 0.0;

	/** North-south size in meters. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double HeightMeters = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double AreaSquareKm = 0.0;

	/** True when the level already has a geo origin. Tiles below use it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bLevelHasGeoOrigin = false;

	/** Origin the tiles were computed with: the level origin when set, otherwise SuggestedOrigin. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint TileOrigin;

	/** Area center. Pass to SetGeoOrigin when the level has no origin yet. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint SuggestedOrigin;

	/** Tile edge length in meters (X, Y). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FIntPoint TileSizeMeters = FIntPoint(1000, 1000);

	/** Tiles overlapping the area, capped at 100. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FTwinBLDTileInfo> Tiles;

	/** Uncapped number of overlapping tiles. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 TileCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Warnings;
};

USTRUCT(BlueprintType)
struct FTwinBLDGeoReference
{
	GENERATED_BODY()

	/** True when the level stores a geo origin. Without one, geo conversion tools fail. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bHasGeoOrigin = false;

	/** Geographic location of world (0, 0). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint Origin;

	/** Increments every time the origin changes; content generated with an older revision is misplaced. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 GeoTransformRevision = 0;

	/** Projection used for world coordinates. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Projection;

	/** Direction of geographic north in world XY (unit vector). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FVector2D WorldNorth = FVector2D::ZeroVector;

	/** Direction of geographic east in world XY (unit vector). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FVector2D WorldEast = FVector2D::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FIntPoint TileSizeMeters = FIntPoint(1000, 1000);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FIntPoint TileOffsetMeters = FIntPoint::ZeroValue;

	/** True when OSM data is loaded into the import session. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bOsmSourceLoaded = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString OsmSourcePath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 SelectedTileCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bGenerationInProgress = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bSatelliteImportInProgress = false;

	/** Import session status line. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Status;
};

USTRUCT(BlueprintType)
struct FTwinBLDSetGeoOriginResult
{
	GENERATED_BODY()

	/** True when the origin was changed. Always false for dry runs. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bApplied = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bDryRun = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bHadGeoOrigin = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint PreviousOrigin;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint NewOrigin;

	/** How far the new origin is from the previous one, in meters. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double ShiftMeters = 0.0;

	/** Tiles with generated content that would be left in the wrong place. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 GeneratedTileCount = 0;

	/** Loaded generated actors that would be tagged stale. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	int32 LoadedGeneratedActorCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bBlockedByActiveWork = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString Message;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Warnings;
};

USTRUCT(BlueprintType)
struct FTwinBLDGeoConversion
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint Geo;

	/** World location in cm. Z is the landscape height when bGroundHit is true, otherwise the input Z (or 0). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FVector World = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bGroundHit = false;

	/** Tile containing the point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FIntPoint Tile = FIntPoint::ZeroValue;
};

USTRUCT(BlueprintType)
struct FTwinBLDSunResult
{
	GENERATED_BODY()

	/** Compass bearing of the sun in degrees clockwise from north. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double AzimuthDeg = 0.0;

	/** Sun angle above the horizon in degrees. Negative means night. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	double ElevationDeg = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bSunAboveHorizon = false;

	/** UTC time the position was computed for, ISO 8601. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FString UtcTime;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FTwinBLDGeoPoint Location;

	/** Rotation for a directional light shining from the sun. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FRotator LightRotation = FRotator::ZeroRotator;

	/** Light that was rotated. Empty when bApply was false. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	FBLDActorRef Light;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	bool bSpawnedLight = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TwinBLDToolset")
	TArray<FString> Warnings;
};
