// Copyright WorldBLD LLC. All rights reserved.

#include "Common/TwinBLDGeo.h"

#include "Common/TwinBLDToolsetSubsystem.h"
#include "Engine/World.h"
#include "LandscapeProxy.h"
#include "ProjWrapper.h"
#include "TwinBLDImportSession.h"
#include "TwinBLDUtils.h"

namespace TwinBLDGeo
{
	namespace
	{
		constexpr double EarthRadiusMeters = 6371008.8;

		/** Small step used to measure the direction of north and east through the projection. */
		constexpr double DirectionProbeDegrees = 1.0e-4;

		double NormalizeDegrees(const double Degrees)
		{
			double Result = FMath::Fmod(Degrees, 360.0);
			return Result < 0.0 ? Result + 360.0 : Result;
		}
	}

	FProjection::FProjection(const FVector2D& OriginLatLon, const FIntPoint& AxisOrder)
		: Origin(OriginLatLon)
		, Proj(MakeUnique<FProjWrapper>(OriginLatLon, 100.0, AxisOrder))
	{
	}

	FProjection::~FProjection() = default;

	bool FProjection::IsValid() const
	{
		return Proj.IsValid() && Proj->IsValid();
	}

	FVector2D FProjection::ToWorld(const double Lat, const double Lon) const
	{
		return Proj->TransformCoord(Lat, Lon);
	}

	FTwinBLDGeoPoint FProjection::ToGeo(const FVector2D& WorldCm) const
	{
		const FVector2D LatLon = Proj->InverseTransformCoord(WorldCm);
		return MakePoint(LatLon.X, LatLon.Y);
	}

	FVector2D FProjection::WorldNorth() const
	{
		const FVector2D Delta = ToWorld(Origin.X + DirectionProbeDegrees, Origin.Y) - ToWorld(Origin.X, Origin.Y);
		return Delta.GetSafeNormal();
	}

	FVector2D FProjection::WorldEast() const
	{
		const FVector2D Delta = ToWorld(Origin.X, Origin.Y + DirectionProbeDegrees) - ToWorld(Origin.X, Origin.Y);
		return Delta.GetSafeNormal();
	}

	FBox2D FProjection::ToWorldBox(const FTwinBLDGeoBox& Box) const
	{
		FBox2D Result(ForceInit);
		Result += ToWorld(Box.South, Box.West);
		Result += ToWorld(Box.South, Box.East);
		Result += ToWorld(Box.North, Box.West);
		Result += ToWorld(Box.North, Box.East);
		return Result;
	}

	FTwinBLDGeoBox FProjection::ToGeoBox(const FBox2D& WorldBoxCm) const
	{
		const FTwinBLDGeoPoint Corners[] =
		{
			ToGeo(WorldBoxCm.Min),
			ToGeo(FVector2D(WorldBoxCm.Min.X, WorldBoxCm.Max.Y)),
			ToGeo(WorldBoxCm.Max),
			ToGeo(FVector2D(WorldBoxCm.Max.X, WorldBoxCm.Min.Y)),
		};

		FTwinBLDGeoBox Result;
		Result.South = Result.North = Corners[0].Lat;
		Result.West = Result.East = Corners[0].Lon;
		for (const FTwinBLDGeoPoint& Corner : Corners)
		{
			Result.South = FMath::Min(Result.South, Corner.Lat);
			Result.North = FMath::Max(Result.North, Corner.Lat);
			Result.West = FMath::Min(Result.West, Corner.Lon);
			Result.East = FMath::Max(Result.East, Corner.Lon);
		}
		return Result;
	}

	TUniquePtr<FProjection> MakeLevelProjection(FString& OutError)
	{
		UTwinBLDImportSession* Session = UTwinBLDToolsetSubsystem::GetSession();
		if (!Session)
		{
			OutError = TEXT("The TwinBLD import session is unavailable. Make sure an editor level is open.");
			return nullptr;
		}

		if (!Session->HasPersistedGeoOrigin())
		{
			OutError = TEXT("This level has no geo origin. Call TwinBLDLocationToolset.SetGeoOrigin with bDryRun=false "
				"(SuggestImportArea returns a SuggestedOrigin), or load OSM data, which sets one.");
			return nullptr;
		}

		TUniquePtr<FProjection> Projection = MakeUnique<FProjection>(Session->GeoOrigin, Session->AxisOrder);
		if (!Projection->IsValid())
		{
			OutError = TEXT("The PROJ projection failed to initialize. Check that the TwinBLD plugin content (proj.db) is installed.");
			return nullptr;
		}
		return Projection;
	}

	TUniquePtr<FProjection> MakeProjection(const FTwinBLDGeoPoint& Origin, const FIntPoint& AxisOrder)
	{
		TUniquePtr<FProjection> Projection = MakeUnique<FProjection>(FVector2D(Origin.Lat, Origin.Lon), AxisOrder);
		return Projection->IsValid() ? MoveTemp(Projection) : nullptr;
	}

	bool ValidatePoint(const FTwinBLDGeoPoint& Point, const FString& Field, FString& OutError)
	{
		if (!FMath::IsFinite(Point.Lat) || Point.Lat < -90.0 || Point.Lat > 90.0)
		{
			OutError = FString::Printf(TEXT("%s.Lat must be between -90 and 90 degrees (got %f)."), *Field, Point.Lat);
			return false;
		}

		if (!FMath::IsFinite(Point.Lon) || Point.Lon < -180.0 || Point.Lon > 180.0)
		{
			OutError = FString::Printf(TEXT("%s.Lon must be between -180 and 180 degrees (got %f)."), *Field, Point.Lon);
			return false;
		}

		return true;
	}

	bool ValidateBox(const FTwinBLDGeoBox& Box, const FString& Field, FString& OutError)
	{
		if (!ValidatePoint(MakePoint(Box.South, Box.West), Field + TEXT(".South/West"), OutError)
			|| !ValidatePoint(MakePoint(Box.North, Box.East), Field + TEXT(".North/East"), OutError))
		{
			return false;
		}

		if (Box.North <= Box.South || Box.East <= Box.West)
		{
			OutError = FString::Printf(
				TEXT("%s is empty or inverted: North must be greater than South and East greater than West. Boxes crossing the antimeridian are not supported."),
				*Field);
			return false;
		}

		return true;
	}

	FTwinBLDGeoPoint MakePoint(const double Lat, const double Lon)
	{
		FTwinBLDGeoPoint Point;
		Point.Lat = Lat;
		Point.Lon = Lon;
		return Point;
	}

	FTwinBLDGeoBox BoxAround(const FTwinBLDGeoPoint& Center, const double RadiusMeters)
	{
		const double LatDelta = RadiusMeters / MetersPerDegreeLat;
		const double LonDelta = RadiusMeters / (MetersPerDegreeLat * FMath::Max(FMath::Cos(FMath::DegreesToRadians(Center.Lat)), 0.01));

		FTwinBLDGeoBox Box;
		Box.South = FMath::Max(-90.0, Center.Lat - LatDelta);
		Box.North = FMath::Min(90.0, Center.Lat + LatDelta);
		Box.West = FMath::Max(-180.0, Center.Lon - LonDelta);
		Box.East = FMath::Min(180.0, Center.Lon + LonDelta);
		return Box;
	}

	FTwinBLDGeoPoint BoxCenter(const FTwinBLDGeoBox& Box)
	{
		return MakePoint((Box.South + Box.North) * 0.5, (Box.West + Box.East) * 0.5);
	}

	double BoxWidthMeters(const FTwinBLDGeoBox& Box)
	{
		const double MidLat = (Box.South + Box.North) * 0.5;
		return DistanceMeters(MakePoint(MidLat, Box.West), MakePoint(MidLat, Box.East));
	}

	double BoxHeightMeters(const FTwinBLDGeoBox& Box)
	{
		return DistanceMeters(MakePoint(Box.South, Box.West), MakePoint(Box.North, Box.West));
	}

	double DistanceMeters(const FTwinBLDGeoPoint& A, const FTwinBLDGeoPoint& B)
	{
		const double LatA = FMath::DegreesToRadians(A.Lat);
		const double LatB = FMath::DegreesToRadians(B.Lat);
		const double DeltaLat = LatB - LatA;
		const double DeltaLon = FMath::DegreesToRadians(B.Lon - A.Lon);

		const double H = FMath::Square(FMath::Sin(DeltaLat * 0.5))
			+ FMath::Cos(LatA) * FMath::Cos(LatB) * FMath::Square(FMath::Sin(DeltaLon * 0.5));
		return 2.0 * EarthRadiusMeters * FMath::Asin(FMath::Min(1.0, FMath::Sqrt(H)));
	}

	bool SampleLandscapeZ(UWorld* World, const FVector2D& WorldXY, double& OutZ)
	{
		if (!World)
		{
			return false;
		}

		const FVector Start(WorldXY.X, WorldXY.Y, 1.0e6);
		const FVector End(WorldXY.X, WorldXY.Y, -1.0e6);
		FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(TwinBLDToolset_SampleLandscapeZ), false);

		TArray<FHitResult> Hits;
		World->LineTraceMultiByChannel(Hits, Start, End, ECC_Visibility, QueryParams);
		for (const FHitResult& Hit : Hits)
		{
			if (Cast<ALandscapeProxy>(Hit.GetActor()))
			{
				OutZ = Hit.ImpactPoint.Z;
				return true;
			}
		}
		return false;
	}

	void ComputeSunPosition(const FDateTime& UtcTime, const double Lat, const double Lon, double& OutAzimuthDeg, double& OutElevationDeg)
	{
		// Days since J2000.0.
		const double Days = UtcTime.GetJulianDay() - 2451545.0;

		const double MeanLongitude = NormalizeDegrees(280.460 + 0.9856474 * Days);
		const double MeanAnomaly = FMath::DegreesToRadians(NormalizeDegrees(357.528 + 0.9856003 * Days));
		const double EclipticLongitude = FMath::DegreesToRadians(
			MeanLongitude + 1.915 * FMath::Sin(MeanAnomaly) + 0.020 * FMath::Sin(2.0 * MeanAnomaly));
		const double Obliquity = FMath::DegreesToRadians(23.439 - 0.0000004 * Days);

		const double RightAscension = FMath::Atan2(FMath::Cos(Obliquity) * FMath::Sin(EclipticLongitude), FMath::Cos(EclipticLongitude));
		const double Declination = FMath::Asin(FMath::Sin(Obliquity) * FMath::Sin(EclipticLongitude));

		const double SiderealDegrees = NormalizeDegrees(280.46061837 + 360.98564736629 * Days + Lon);
		const double HourAngle = FMath::DegreesToRadians(SiderealDegrees) - RightAscension;

		const double LatRad = FMath::DegreesToRadians(Lat);
		const double Elevation = FMath::Asin(
			FMath::Sin(LatRad) * FMath::Sin(Declination) + FMath::Cos(LatRad) * FMath::Cos(Declination) * FMath::Cos(HourAngle));
		const double Azimuth = FMath::Atan2(
			-FMath::Sin(HourAngle),
			FMath::Tan(Declination) * FMath::Cos(LatRad) - FMath::Sin(LatRad) * FMath::Cos(HourAngle));

		OutElevationDeg = FMath::RadiansToDegrees(Elevation);
		OutAzimuthDeg = NormalizeDegrees(FMath::RadiansToDegrees(Azimuth));
	}

	FRotator SunLightRotation(const FProjection& Projection, const double AzimuthDeg, const double ElevationDeg)
	{
		const FVector2D North = Projection.WorldNorth();
		const FVector2D East = Projection.WorldEast();
		const double Azimuth = FMath::DegreesToRadians(AzimuthDeg);
		const double Elevation = FMath::DegreesToRadians(ElevationDeg);

		const FVector2D Horizontal = North * FMath::Cos(Azimuth) + East * FMath::Sin(Azimuth);
		const FVector TowardSun = FVector(Horizontal * FMath::Cos(Elevation), FMath::Sin(Elevation)).GetSafeNormal();

		// Directional lights shine along their forward vector, away from the sun.
		return FRotationMatrix::MakeFromX(-TowardSun).Rotator();
	}
}
