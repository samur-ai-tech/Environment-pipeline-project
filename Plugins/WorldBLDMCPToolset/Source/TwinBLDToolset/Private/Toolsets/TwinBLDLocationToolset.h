// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/TwinBLDToolsetTypes.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "TwinBLDLocationToolset.generated.h"

class ADirectionalLight;

/**
 * Where on Earth the level is. Start every real-world replica here.
 * Workflow: GeocodePlace("Flatiron Building, New York") -> SuggestImportArea(place Location or Bounds) ->
 * SetGeoOrigin(SuggestedOrigin, bDryRun=false) -> TwinBLDSurveyToolset / TwinBLDImportToolset.
 * Geographic values are WGS84 decimal degrees ({"lat": 40.7411, "lon": -73.9897}); boxes are
 * {"south", "west", "north", "east"}. World values are Unreal centimeters, Z up. The geo origin is the real-world
 * location of world (0, 0); changing it after importing leaves existing content misplaced, so dry-run first.
 * Geocoding uses OpenStreetMap Nominatim (rate limited to one request per second, answers cached for 30 days);
 * search for specific places, never bulk-geocode lists.
 * For TwinBLD / WorldBLD / CityBLD / RoadBLD packaging, cook, compile, or plugin-load errors (missing WorldBLD_Content,
 * Unable to load plugin, GeometryScripting), call WorldBLDToolset.UWorldBLDToolset.GetPackagingGuide.
 */
UCLASS(BlueprintType, MinimalAPI)
class UTwinBLDLocationToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Finds places by name or address with OpenStreetMap Nominatim.
	 * @param Query Free-form text such as "Shibuya Crossing, Tokyo" or "221B Baker Street, London".
	 * @param MaxResults Matches to return (1-40), best first.
	 * @param CountryCodes Optional comma-separated ISO 3166-1 alpha-2 codes that limit the search, such as "us,ca".
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static UTwinBLDGeocodeAsyncResult* GeocodePlace(const FString& Query, int32 MaxResults = 5, const FString& CountryCodes = TEXT(""));

	/**
	 * Describes what is at a location: the nearest named feature and its address.
	 * @param Location Point to look up.
	 * @param Zoom Detail level from 3 (country) to 18 (building).
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static UTwinBLDGeocodeAsyncResult* ReverseGeocode(const FTwinBLDGeoPoint& Location, int32 Zoom = 18);

	/**
	 * Sizes an import area and lists the TwinBLD tiles it covers. Read-only.
	 * @param Center Area center, used when Bounds is not given.
	 * @param Bounds Optional exact area, such as a place's Bounds from GeocodePlace. Overrides Center and RadiusMeters.
	 * @param RadiusMeters Half-width of a square area around Center.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDImportAreaSuggestion SuggestImportArea(const FTwinBLDGeoPoint& Center, TOptional<FTwinBLDGeoBox> Bounds, double RadiusMeters = 250.0);

	/** Reports the level's geo origin, projection, world north and east directions, tile grid and import session state. */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDGeoReference GetGeoReference();

	/**
	 * Sets the real-world location of world (0, 0) for this level. Applying bumps the geo revision, clears the tile
	 * selection and tags existing generated actors as stale. Fails while generation or imagery imports are running.
	 * @param Origin New origin. Use SuggestImportArea's SuggestedOrigin.
	 * @param bDryRun Report the impact without changing anything.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDSetGeoOriginResult SetGeoOrigin(const FTwinBLDGeoPoint& Origin, bool bDryRun = true);

	/**
	 * Converts geographic points to world locations (cm) using the level's geo origin.
	 * @param Points Points to convert, at most 10000.
	 * @param bSampleGroundZ Set Z to the landscape height under each point when a landscape exists.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static TArray<FTwinBLDGeoConversion> GeoToWorld(const TArray<FTwinBLDGeoPoint>& Points, bool bSampleGroundZ = false);

	/**
	 * Converts world locations (cm) to geographic points using the level's geo origin.
	 * @param Locations World locations, at most 10000.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static TArray<FTwinBLDGeoConversion> WorldToGeo(const TArray<FVector>& Locations);

	/**
	 * Aims a directional light where the real sun is at the geo origin for a date and time. Mutating unless bApply is false.
	 * @param DateTime ISO 8601 date and time, such as 2026-06-21T17:30:00. Interpreted as local time at UtcOffsetHours.
	 * @param UtcOffsetHours Offset of DateTime from UTC, such as -4 for New York in summer or 9 for Tokyo.
	 * @param Light Directional light to rotate. When omitted, the first directional light in the level is used, or one is spawned.
	 * @param bApply Rotate the light. False only computes the sun position.
	 */
	UFUNCTION(meta = (AICallable), Category = "TwinBLDToolset")
	static FTwinBLDSunResult SetSunForLocation(const FString& DateTime, double UtcOffsetHours = 0.0, ADirectionalLight* Light = nullptr, bool bApply = true);
};
