// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/TwinBLDLocationToolset.h"

#include "BLDToolsetUtils.h"
#include "Common/TwinBLDGeo.h"
#include "Common/TwinBLDToolsetSubsystem.h"
#include "Components/LightComponent.h"
#include "Editor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "ScopedTransaction.h"
#include "Services/TwinBLDNominatim.h"
#include "StreetMap/StreetMap.h"
#include "TileManager.h"
#include "TwinBLDImportSession.h"
#include "UObject/StrongObjectPtr.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(TwinBLDLocationToolset)

#define LOCTEXT_NAMESPACE "TwinBLDLocationToolset"

namespace TwinBLDLocationPrivate
{
	const TCHAR* ToolsetName = TEXT("TwinBLDToolset");
	constexpr int32 MaxListedTiles = 100;
	constexpr int32 MaxConversions = 10000;

	/** Areas above this size are slow to fetch from Overpass and to generate. */
	constexpr double LargeAreaSquareKm = 4.0;

	void RaiseError(const FString& Message)
	{
		BLDToolset::RaiseError(ToolsetName, Message);
	}

	void CompleteGeocode(const TStrongObjectPtr<UTwinBLDGeocodeAsyncResult>& Result, const bool bSucceeded, const FTwinBLDGeocodeResult& Value, const FString& Error)
	{
		if (!bSucceeded)
		{
			Result->SetError(FString::Printf(TEXT("%s: Geocoding failed. %s"), ToolsetName, *Error));
			return;
		}
		Result->SetValue(Value);
	}

	FIntPoint GetTileSize(const UTwinBLDImportSession* Session)
	{
		const UTileManager* TileManager = Session ? Session->GetTileManager() : nullptr;
		return TileManager ? TileManager->TileSize : FIntPoint(1000, 1000);
	}

	FIntPoint GetTileOffset(const UTwinBLDImportSession* Session)
	{
		const UTileManager* TileManager = Session ? Session->GetTileManager() : nullptr;
		return TileManager ? TileManager->TilesOffset : FIntPoint::ZeroValue;
	}

	/** Tile containing a world XY position, computed the way TwinBLD lays out its grid (meters, with offset). */
	FIntPoint TileAt(const FVector2D& WorldCm, const FIntPoint& TileSizeMeters, const FIntPoint& TileOffsetMeters)
	{
		const double SizeX = FMath::Max(1, TileSizeMeters.X) * 100.0;
		const double SizeY = FMath::Max(1, TileSizeMeters.Y) * 100.0;
		return FIntPoint(
			FMath::FloorToInt32((WorldCm.X - TileOffsetMeters.X * 100.0) / SizeX),
			FMath::FloorToInt32((WorldCm.Y - TileOffsetMeters.Y * 100.0) / SizeY));
	}

	FTwinBLDTileInfo MakeTileInfo(const FIntPoint& Tile, const FIntPoint& TileSizeMeters, const FIntPoint& TileOffsetMeters, const TwinBLDGeo::FProjection& Projection)
	{
		FTwinBLDTileInfo Info;
		Info.X = Tile.X;
		Info.Y = Tile.Y;
		Info.WorldMinCm = FVector2D(
			(Tile.X * TileSizeMeters.X + TileOffsetMeters.X) * 100.0,
			(Tile.Y * TileSizeMeters.Y + TileOffsetMeters.Y) * 100.0);
		Info.WorldMaxCm = Info.WorldMinCm + FVector2D(TileSizeMeters.X * 100.0, TileSizeMeters.Y * 100.0);
		Info.GeoBounds = Projection.ToGeoBox(FBox2D(Info.WorldMinCm, Info.WorldMaxCm));
		return Info;
	}

	ADirectionalLight* FindOrSpawnSun(UWorld* World, bool& bOutSpawned)
	{
		bOutSpawned = false;
		for (TActorIterator<ADirectionalLight> It(World); It; ++It)
		{
			if (IsValid(*It))
			{
				return *It;
			}
		}

		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ADirectionalLight* Light = World->SpawnActor<ADirectionalLight>(ADirectionalLight::StaticClass(), FTransform::Identity, SpawnParams);
		if (Light)
		{
			Light->SetActorLabel(TEXT("TwinBLD_Sun"));
			bOutSpawned = true;
		}
		return Light;
	}

	bool ParseDateTime(const FString& Text, FDateTime& OutDateTime)
	{
		const FString Trimmed = Text.TrimStartAndEnd();
		return FDateTime::ParseIso8601(*Trimmed, OutDateTime) || FDateTime::Parse(Trimmed, OutDateTime);
	}
}

UTwinBLDGeocodeAsyncResult* UTwinBLDLocationToolset::GeocodePlace(const FString& Query, const int32 MaxResults, const FString& CountryCodes)
{
	using namespace TwinBLDLocationPrivate;

	UTwinBLDGeocodeAsyncResult* Result = NewObject<UTwinBLDGeocodeAsyncResult>();
	if (Query.TrimStartAndEnd().Len() < 2)
	{
		Result->SetError(FString::Printf(TEXT("%s: Query is empty. Pass a place name or address."), ToolsetName));
		return Result;
	}

	TStrongObjectPtr<UTwinBLDGeocodeAsyncResult> StrongResult(Result);
	TwinBLDNominatim::Search(Query, MaxResults, CountryCodes, [StrongResult](const bool bSucceeded, const FTwinBLDGeocodeResult& Value, const FString& Error)
	{
		CompleteGeocode(StrongResult, bSucceeded, Value, Error);
	});
	return Result;
}

UTwinBLDGeocodeAsyncResult* UTwinBLDLocationToolset::ReverseGeocode(const FTwinBLDGeoPoint& Location, const int32 Zoom)
{
	using namespace TwinBLDLocationPrivate;

	UTwinBLDGeocodeAsyncResult* Result = NewObject<UTwinBLDGeocodeAsyncResult>();
	FString Error;
	if (!TwinBLDGeo::ValidatePoint(Location, TEXT("Location"), Error))
	{
		Result->SetError(FString::Printf(TEXT("%s: %s"), ToolsetName, *Error));
		return Result;
	}

	TStrongObjectPtr<UTwinBLDGeocodeAsyncResult> StrongResult(Result);
	TwinBLDNominatim::Reverse(Location, Zoom, [StrongResult](const bool bSucceeded, const FTwinBLDGeocodeResult& Value, const FString& ErrorMessage)
	{
		CompleteGeocode(StrongResult, bSucceeded, Value, ErrorMessage);
	});
	return Result;
}

FTwinBLDImportAreaSuggestion UTwinBLDLocationToolset::SuggestImportArea(const FTwinBLDGeoPoint& Center, TOptional<FTwinBLDGeoBox> Bounds, const double RadiusMeters)
{
	using namespace TwinBLDLocationPrivate;

	FTwinBLDImportAreaSuggestion Suggestion;
	FString Error;

	if (Bounds.IsSet())
	{
		if (!TwinBLDGeo::ValidateBox(Bounds.GetValue(), TEXT("Bounds"), Error))
		{
			RaiseError(Error);
			return Suggestion;
		}
		Suggestion.Bounds = Bounds.GetValue();
	}
	else
	{
		if (!TwinBLDGeo::ValidatePoint(Center, TEXT("Center"), Error))
		{
			RaiseError(Error);
			return Suggestion;
		}
		if (RadiusMeters <= 0.0)
		{
			RaiseError(TEXT("RadiusMeters must be greater than 0."));
			return Suggestion;
		}
		Suggestion.Bounds = TwinBLDGeo::BoxAround(Center, RadiusMeters);
	}

	Suggestion.Center = TwinBLDGeo::BoxCenter(Suggestion.Bounds);
	Suggestion.SuggestedOrigin = Suggestion.Center;
	Suggestion.WidthMeters = TwinBLDGeo::BoxWidthMeters(Suggestion.Bounds);
	Suggestion.HeightMeters = TwinBLDGeo::BoxHeightMeters(Suggestion.Bounds);
	Suggestion.AreaSquareKm = Suggestion.WidthMeters * Suggestion.HeightMeters / 1.0e6;

	UTwinBLDImportSession* Session = UTwinBLDToolsetSubsystem::GetSession();
	Suggestion.bLevelHasGeoOrigin = Session && Session->HasPersistedGeoOrigin();
	Suggestion.TileOrigin = Suggestion.bLevelHasGeoOrigin
		? TwinBLDGeo::MakePoint(Session->GeoOrigin.X, Session->GeoOrigin.Y)
		: Suggestion.SuggestedOrigin;
	Suggestion.TileSizeMeters = GetTileSize(Session);
	const FIntPoint TileOffset = GetTileOffset(Session);

	if (Suggestion.AreaSquareKm > LargeAreaSquareKm)
	{
		Suggestion.Warnings.Add(FString::Printf(
			TEXT("The area is %.1f km². Areas above %.0f km² are slow to download and generate; start with the core of the place and extend later."),
			Suggestion.AreaSquareKm, LargeAreaSquareKm));
	}

	if (Suggestion.bLevelHasGeoOrigin)
	{
		const double OriginDistance = TwinBLDGeo::DistanceMeters(Suggestion.TileOrigin, Suggestion.Center);
		if (OriginDistance > 20000.0)
		{
			Suggestion.Warnings.Add(FString::Printf(
				TEXT("The area is %.0f km from the level's geo origin. Far from the origin, projection distortion and float precision degrade; consider a new level or a new origin."),
				OriginDistance / 1000.0));
		}
	}

	const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeProjection(Suggestion.TileOrigin, Session ? Session->AxisOrder : FIntPoint(1, 2));
	if (!Projection)
	{
		Suggestion.Warnings.Add(TEXT("The PROJ projection failed to initialize, so tiles could not be computed."));
		return Suggestion;
	}

	const FBox2D WorldBox = Projection->ToWorldBox(Suggestion.Bounds);
	const FIntPoint MinTile = TileAt(WorldBox.Min, Suggestion.TileSizeMeters, TileOffset);
	const FIntPoint MaxTile = TileAt(WorldBox.Max, Suggestion.TileSizeMeters, TileOffset);
	Suggestion.TileCount = (MaxTile.X - MinTile.X + 1) * (MaxTile.Y - MinTile.Y + 1);

	for (int32 X = MinTile.X; X <= MaxTile.X && Suggestion.Tiles.Num() < MaxListedTiles; ++X)
	{
		for (int32 Y = MinTile.Y; Y <= MaxTile.Y && Suggestion.Tiles.Num() < MaxListedTiles; ++Y)
		{
			Suggestion.Tiles.Add(MakeTileInfo(FIntPoint(X, Y), Suggestion.TileSizeMeters, TileOffset, *Projection));
		}
	}

	if (Session && Session->IsTrialModeActive())
	{
		if (Suggestion.TileCount > Session->GetMaxTrialSelectedTiles())
		{
			Suggestion.Warnings.Add(FString::Printf(
				TEXT("TwinBLD trial mode allows %d tiles per generation; this area needs %d. Shrink the area or use a full license."),
				Session->GetMaxTrialSelectedTiles(), Suggestion.TileCount));
		}
		if (FMath::Max(Suggestion.TileSizeMeters.X, Suggestion.TileSizeMeters.Y) > Session->GetMaxTrialTileSizeMeters())
		{
			Suggestion.Warnings.Add(FString::Printf(
				TEXT("TwinBLD trial mode allows tiles up to %d m; the tile size is %dx%d m."),
				Session->GetMaxTrialTileSizeMeters(), Suggestion.TileSizeMeters.X, Suggestion.TileSizeMeters.Y));
		}
	}

	return Suggestion;
}

FTwinBLDGeoReference UTwinBLDLocationToolset::GetGeoReference()
{
	using namespace TwinBLDLocationPrivate;

	FTwinBLDGeoReference Reference;
	UTwinBLDImportSession* Session = UTwinBLDToolsetSubsystem::GetSession();
	if (!Session)
	{
		RaiseError(TEXT("The TwinBLD import session is unavailable. Make sure an editor level is open."));
		return Reference;
	}

	Reference.bHasGeoOrigin = Session->HasPersistedGeoOrigin();
	Reference.Origin = TwinBLDGeo::MakePoint(Session->GeoOrigin.X, Session->GeoOrigin.Y);
	Reference.GeoTransformRevision = Session->GetGeoTransformRevision();
	Reference.Projection = TEXT("Transverse Mercator centered on the geo origin (WGS84), 1 m = 100 cm");
	Reference.TileSizeMeters = GetTileSize(Session);
	Reference.TileOffsetMeters = GetTileOffset(Session);
	Reference.bOsmSourceLoaded = Session->GetSourceStreetMap() != nullptr;
	Reference.OsmSourcePath = Session->SourcePath;
	Reference.SelectedTileCount = Session->GetSelectedTiles().Num();
	Reference.bGenerationInProgress = Session->bGenerationInProgress;
	Reference.bSatelliteImportInProgress = Session->IsSatelliteImportInProgress();
	Reference.Status = Session->GetStatusText().ToString();

	if (Reference.bHasGeoOrigin)
	{
		if (const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeProjection(Reference.Origin, Session->AxisOrder))
		{
			Reference.WorldNorth = Projection->WorldNorth();
			Reference.WorldEast = Projection->WorldEast();
		}
	}

	return Reference;
}

FTwinBLDSetGeoOriginResult UTwinBLDLocationToolset::SetGeoOrigin(const FTwinBLDGeoPoint& Origin, const bool bDryRun)
{
	using namespace TwinBLDLocationPrivate;

	FTwinBLDSetGeoOriginResult Result;
	Result.bDryRun = bDryRun;
	Result.NewOrigin = Origin;

	FString Error;
	if (!TwinBLDGeo::ValidatePoint(Origin, TEXT("Origin"), Error))
	{
		RaiseError(Error);
		return Result;
	}

	UTwinBLDImportSession* Session = UTwinBLDToolsetSubsystem::GetSession();
	if (!Session)
	{
		RaiseError(TEXT("The TwinBLD import session is unavailable. Make sure an editor level is open."));
		return Result;
	}

	Result.bHadGeoOrigin = Session->HasPersistedGeoOrigin();
	Result.PreviousOrigin = TwinBLDGeo::MakePoint(Session->GeoOrigin.X, Session->GeoOrigin.Y);
	Result.ShiftMeters = Result.bHadGeoOrigin ? TwinBLDGeo::DistanceMeters(Result.PreviousOrigin, Origin) : 0.0;

	const FTwinBLDGeoOriginChangeImpact Impact = Session->AnalyzeGeoOriginChangeImpact();
	Result.GeneratedTileCount = Impact.GeneratedTileCount;
	Result.LoadedGeneratedActorCount = Impact.LoadedGeneratedActorCount;
	Result.bBlockedByActiveWork = Impact.HasActiveWorkBlockers();

	if (Impact.HasGeneratedContent())
	{
		Result.Warnings.Add(FString::Printf(
			TEXT("%d generated tiles and %d loaded generated actors use the current origin. After the change they are tagged TwinBLD.GeoTransform.Stale and should be cleared and regenerated."),
			Impact.GeneratedTileCount, Impact.LoadedGeneratedActorCount));
	}
	if (Impact.bHasLoadedShapefile)
	{
		Result.Warnings.Add(TEXT("The loaded shapefile is reprojected to the new origin."));
	}

	if (Result.bHadGeoOrigin && Result.ShiftMeters < 0.001)
	{
		Result.Message = TEXT("The level already uses this origin. Nothing to change.");
		return Result;
	}

	if (Result.bBlockedByActiveWork)
	{
		Result.Message = TEXT("Generation or an imagery import is running. Wait for it (TwinBLDImportToolset.WaitForJob) or cancel it first.");
		return Result;
	}

	if (bDryRun)
	{
		Result.Message = TEXT("Dry run: nothing changed. Call again with bDryRun=false to apply.");
		return Result;
	}

	if (!UTwinBLDToolsetSubsystem::EnsureAuthorizedOrRaise())
	{
		return Result;
	}

	FText ApplyError;
	if (!Session->ApplyGeoOriginChange(FVector2D(Origin.Lat, Origin.Lon), ApplyError))
	{
		RaiseError(FString::Printf(TEXT("Could not set the geo origin: %s"), *ApplyError.ToString()));
		return Result;
	}

	Result.bApplied = true;
	Result.Message = FString::Printf(TEXT("Geo origin set. Geo revision is now %d; the tile selection was cleared."), Session->GetGeoTransformRevision());
	return Result;
}

TArray<FTwinBLDGeoConversion> UTwinBLDLocationToolset::GeoToWorld(const TArray<FTwinBLDGeoPoint>& Points, const bool bSampleGroundZ)
{
	using namespace TwinBLDLocationPrivate;

	TArray<FTwinBLDGeoConversion> Conversions;
	if (Points.Num() > MaxConversions)
	{
		RaiseError(FString::Printf(TEXT("Pass at most %d points per call (got %d)."), MaxConversions, Points.Num()));
		return Conversions;
	}

	FString Error;
	const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeLevelProjection(Error);
	if (!Projection)
	{
		RaiseError(Error);
		return Conversions;
	}

	UTwinBLDImportSession* Session = UTwinBLDToolsetSubsystem::GetSession();
	const FIntPoint TileSize = GetTileSize(Session);
	const FIntPoint TileOffset = GetTileOffset(Session);
	UWorld* World = BLDToolset::GetEditorWorld();

	Conversions.Reserve(Points.Num());
	for (int32 Index = 0; Index < Points.Num(); ++Index)
	{
		const FTwinBLDGeoPoint& Point = Points[Index];
		if (!TwinBLDGeo::ValidatePoint(Point, FString::Printf(TEXT("Points[%d]"), Index), Error))
		{
			RaiseError(Error);
			return TArray<FTwinBLDGeoConversion>();
		}

		FTwinBLDGeoConversion& Conversion = Conversions.AddDefaulted_GetRef();
		Conversion.Geo = Point;
		const FVector2D WorldXY = Projection->ToWorld(Point.Lat, Point.Lon);
		Conversion.World = FVector(WorldXY, 0.0);
		Conversion.Tile = TileAt(WorldXY, TileSize, TileOffset);

		double GroundZ = 0.0;
		if (bSampleGroundZ && TwinBLDGeo::SampleLandscapeZ(World, WorldXY, GroundZ))
		{
			Conversion.World.Z = GroundZ;
			Conversion.bGroundHit = true;
		}
	}

	return Conversions;
}

TArray<FTwinBLDGeoConversion> UTwinBLDLocationToolset::WorldToGeo(const TArray<FVector>& Locations)
{
	using namespace TwinBLDLocationPrivate;

	TArray<FTwinBLDGeoConversion> Conversions;
	if (Locations.Num() > MaxConversions)
	{
		RaiseError(FString::Printf(TEXT("Pass at most %d locations per call (got %d)."), MaxConversions, Locations.Num()));
		return Conversions;
	}

	FString Error;
	const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeLevelProjection(Error);
	if (!Projection)
	{
		RaiseError(Error);
		return Conversions;
	}

	UTwinBLDImportSession* Session = UTwinBLDToolsetSubsystem::GetSession();
	const FIntPoint TileSize = GetTileSize(Session);
	const FIntPoint TileOffset = GetTileOffset(Session);

	Conversions.Reserve(Locations.Num());
	for (const FVector& Location : Locations)
	{
		FTwinBLDGeoConversion& Conversion = Conversions.AddDefaulted_GetRef();
		Conversion.World = Location;
		Conversion.Geo = Projection->ToGeo(FVector2D(Location));
		Conversion.Tile = TileAt(FVector2D(Location), TileSize, TileOffset);
	}

	return Conversions;
}

FTwinBLDSunResult UTwinBLDLocationToolset::SetSunForLocation(const FString& DateTime, const double UtcOffsetHours, ADirectionalLight* Light, const bool bApply)
{
	using namespace TwinBLDLocationPrivate;

	FTwinBLDSunResult Result;

	FDateTime LocalTime;
	if (!ParseDateTime(DateTime, LocalTime))
	{
		RaiseError(FString::Printf(TEXT("DateTime '%s' is not a valid ISO 8601 date and time, such as 2026-06-21T17:30:00."), *DateTime));
		return Result;
	}

	if (FMath::Abs(UtcOffsetHours) > 14.0)
	{
		RaiseError(TEXT("UtcOffsetHours must be between -14 and 14."));
		return Result;
	}

	FString Error;
	const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeLevelProjection(Error);
	if (!Projection)
	{
		RaiseError(Error);
		return Result;
	}

	const FDateTime UtcTime = LocalTime - FTimespan::FromHours(UtcOffsetHours);
	Result.Location = TwinBLDGeo::MakePoint(Projection->GetOrigin().X, Projection->GetOrigin().Y);
	Result.UtcTime = UtcTime.ToIso8601();

	TwinBLDGeo::ComputeSunPosition(UtcTime, Result.Location.Lat, Result.Location.Lon, Result.AzimuthDeg, Result.ElevationDeg);
	Result.bSunAboveHorizon = Result.ElevationDeg > 0.0;
	Result.LightRotation = TwinBLDGeo::SunLightRotation(*Projection, Result.AzimuthDeg, Result.ElevationDeg);

	if (!Result.bSunAboveHorizon)
	{
		Result.Warnings.Add(TEXT("The sun is below the horizon at this time. For a night scene, lower the sun light intensity and rely on artificial lights and the sky."));
	}

	if (!bApply)
	{
		return Result;
	}

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

	const FScopedTransaction Transaction(LOCTEXT("SetSunForLocation", "Set Sun For Location"));
	if (!IsValid(Light))
	{
		Light = FindOrSpawnSun(World, Result.bSpawnedLight);
		if (!Light)
		{
			RaiseError(TEXT("Failed to spawn a directional light."));
			return Result;
		}
	}

	Light->Modify();
	Light->SetActorRotation(Result.LightRotation);
	if (ULightComponent* LightComponent = Light->GetLightComponent())
	{
		LightComponent->Modify();
		LightComponent->MarkRenderStateDirty();
	}

	Result.Light = BLDToolset::MakeActorRef(Light);
	return Result;
}

#undef LOCTEXT_NAMESPACE
