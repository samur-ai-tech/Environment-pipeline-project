// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/TwinBLDToolsetTypes.h"
#include "Templates/UniquePtr.h"

class FProjWrapper;
class UTwinBLDImportSession;
class UWorld;

/** Geographic helpers. Everything converts through the same projection the TwinBLD importer uses. */
namespace TwinBLDGeo
{
	/** Mean meters per degree of latitude. */
	constexpr double MetersPerDegreeLat = 111320.0;

	/** Projection between WGS84 and world centimeters for one geo origin. */
	class FProjection
	{
	public:
		FProjection(const FVector2D& OriginLatLon, const FIntPoint& AxisOrder);
		~FProjection();

		bool IsValid() const;

		/** World XY in cm for a latitude and longitude. */
		FVector2D ToWorld(double Lat, double Lon) const;

		/** Latitude and longitude for world XY in cm. */
		FTwinBLDGeoPoint ToGeo(const FVector2D& WorldCm) const;

		/** Unit vector pointing geographic north in world XY, measured at the origin. */
		FVector2D WorldNorth() const;

		/** Unit vector pointing geographic east in world XY, measured at the origin. */
		FVector2D WorldEast() const;

		/** World-space rectangle (cm) covering a geo box. */
		FBox2D ToWorldBox(const FTwinBLDGeoBox& Box) const;

		/** Geo box covering a world-space rectangle (cm). */
		FTwinBLDGeoBox ToGeoBox(const FBox2D& WorldBoxCm) const;

		const FVector2D& GetOrigin() const { return Origin; }

	private:
		FVector2D Origin;
		TUniquePtr<FProjWrapper> Proj;
	};

	/**
	 * Projection for the level's current geo origin. Fails with an agent-readable error when the level has no origin.
	 */
	TUniquePtr<FProjection> MakeLevelProjection(FString& OutError);

	/** Projection for an explicit origin, used before an origin is set. */
	TUniquePtr<FProjection> MakeProjection(const FTwinBLDGeoPoint& Origin, const FIntPoint& AxisOrder = FIntPoint(1, 2));

	bool ValidatePoint(const FTwinBLDGeoPoint& Point, const FString& Field, FString& OutError);
	bool ValidateBox(const FTwinBLDGeoBox& Box, const FString& Field, FString& OutError);

	FTwinBLDGeoPoint MakePoint(double Lat, double Lon);
	FTwinBLDGeoBox BoxAround(const FTwinBLDGeoPoint& Center, double RadiusMeters);
	FTwinBLDGeoPoint BoxCenter(const FTwinBLDGeoBox& Box);
	double BoxWidthMeters(const FTwinBLDGeoBox& Box);
	double BoxHeightMeters(const FTwinBLDGeoBox& Box);

	/** Great-circle distance in meters. */
	double DistanceMeters(const FTwinBLDGeoPoint& A, const FTwinBLDGeoPoint& B);

	/** Traces straight down for a landscape and returns its height. */
	bool SampleLandscapeZ(UWorld* World, const FVector2D& WorldXY, double& OutZ);

	/**
	 * Solar azimuth (degrees clockwise from north) and elevation (degrees above horizon) for a UTC time and location.
	 * NOAA low-precision algorithm, accurate to about 0.1 degree between 1950 and 2050.
	 */
	void ComputeSunPosition(const FDateTime& UtcTime, double Lat, double Lon, double& OutAzimuthDeg, double& OutElevationDeg);

	/** Rotation of a directional light shining from the given sun position, using the projection's north and east. */
	FRotator SunLightRotation(const FProjection& Projection, double AzimuthDeg, double ElevationDeg);
}
