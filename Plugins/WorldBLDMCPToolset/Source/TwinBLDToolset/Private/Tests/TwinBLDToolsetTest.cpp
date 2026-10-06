// Copyright WorldBLD LLC. All rights reserved.

#include "Common/TwinBLDGeo.h"
#include "Misc/AutomationTest.h"
#include "Services/TwinBLDNominatim.h"
#include "Toolsets/TwinBLDLocationToolset.h"
#include "Toolsets/TwinBLDSceneToolset.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace TwinBLDToolsetTestPrivate
{
	struct FExpectedToolset
	{
		UClass* Class = nullptr;
		TArray<FString> Tools;
	};

	TArray<FExpectedToolset> GetExpectedToolsets()
	{
		return
		{
			{ UTwinBLDLocationToolset::StaticClass(), { TEXT("GeocodePlace"), TEXT("ReverseGeocode"), TEXT("SuggestImportArea"), TEXT("GetGeoReference"), TEXT("SetGeoOrigin"), TEXT("GeoToWorld"), TEXT("WorldToGeo"), TEXT("SetSunForLocation") } },
			{ UTwinBLDSceneToolset::StaticClass(), { TEXT("GetSceneContext"), TEXT("FindGenerated"), TEXT("DescribeGeneratedActor"), TEXT("SnapToLandscape"), TEXT("DetectFacades"), TEXT("EditBuildingFromReality") } },
		};
	}

	/** Trimmed Nominatim jsonv2 search response. */
	const TCHAR* NominatimSearchFixture = TEXT(R"json([
	{
		"place_id": 1,
		"osm_type": "way",
		"osm_id": 264768896,
		"lat": "40.7410861",
		"lon": "-73.9896530",
		"category": "building",
		"type": "yes",
		"importance": 0.62,
		"name": "Flatiron Building",
		"display_name": "Flatiron Building, 175, 5th Avenue, Manhattan, New York, 10010, United States",
		"address": { "house_number": "175", "road": "5th Avenue", "city": "New York", "country_code": "us" },
		"extratags": { "wikidata": "Q220728", "height": "87", "building:levels": "22" },
		"boundingbox": ["40.7407926", "40.7414230", "-73.9900020", "-73.9893020"]
	}
])json");
}

BEGIN_DEFINE_SPEC(
	FTwinBLDToolsetSpec,
	TEXT("AI.Toolsets.WorldBLD.TwinBLDToolset"),
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
END_DEFINE_SPEC(FTwinBLDToolsetSpec)

void FTwinBLDToolsetSpec::Define()
{
	using namespace TwinBLDToolsetTestPrivate;

	Describe(TEXT("registration"), [this]()
	{
		It(TEXT("registers every toolset and exposes every tool"), [this]()
		{
			for (const FExpectedToolset& Expected : GetExpectedToolsets())
			{
				TestTrue(FString::Printf(TEXT("%s is registered"), *Expected.Class->GetName()),
					UToolsetRegistry::IsToolsetClassRegistered(Expected.Class));

				const FString Schema = UToolsetRegistry::GetToolsetJsonSchema(Expected.Class);
				for (const FString& Tool : Expected.Tools)
				{
					TestTrue(FString::Printf(TEXT("%s schema contains %s"), *Expected.Class->GetName(), *Tool), Schema.Contains(Tool));
				}
			}
		});

		It(TEXT("exposes optional building edit fields in the schema"), [this]()
		{
			const FString Schema = UToolsetRegistry::GetToolsetJsonSchema(UTwinBLDSceneToolset::StaticClass());
			TestTrue(TEXT("heightMeters"), Schema.Contains(TEXT("heightMeters")));
			TestTrue(TEXT("roofType"), Schema.Contains(TEXT("roofType")));
			TestTrue(TEXT("floorPlates"), Schema.Contains(TEXT("floorPlates")));
		});
	});

	Describe(TEXT("geo"), [this]()
	{
		It(TEXT("round-trips geographic points through the projection within 1 cm"), [this]()
		{
			const FTwinBLDGeoPoint Origin = TwinBLDGeo::MakePoint(40.7410861, -73.9896530);
			const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeProjection(Origin);
			if (!TestNotNull(TEXT("Projection"), Projection.Get()))
			{
				return;
			}

			TestTrue(TEXT("Origin maps to world (0, 0)"), Projection->ToWorld(Origin.Lat, Origin.Lon).Size() < 1.0);

			const FTwinBLDGeoPoint Nearby = TwinBLDGeo::MakePoint(Origin.Lat + 0.004, Origin.Lon - 0.006);
			const FVector2D World = Projection->ToWorld(Nearby.Lat, Nearby.Lon);
			const FTwinBLDGeoPoint Back = Projection->ToGeo(World);
			const FVector2D WorldAgain = Projection->ToWorld(Back.Lat, Back.Lon);
			TestTrue(TEXT("Round trip stays within 1 cm"), FVector2D::Distance(World, WorldAgain) < 1.0);

			const double ExpectedMeters = TwinBLDGeo::DistanceMeters(Origin, Nearby);
			TestTrue(TEXT("Projected distance matches the great-circle distance within 0.5%"),
				FMath::IsNearlyEqual(World.Size() / 100.0, ExpectedMeters, ExpectedMeters * 0.005));
		});

		It(TEXT("reports perpendicular north and east directions"), [this]()
		{
			const TUniquePtr<TwinBLDGeo::FProjection> Projection = TwinBLDGeo::MakeProjection(TwinBLDGeo::MakePoint(51.5007, -0.1246));
			if (!TestNotNull(TEXT("Projection"), Projection.Get()))
			{
				return;
			}

			TestTrue(TEXT("North and east are perpendicular"),
				FMath::Abs(FVector2D::DotProduct(Projection->WorldNorth(), Projection->WorldEast())) < 0.01);
		});

		It(TEXT("sizes boxes around a center"), [this]()
		{
			const FTwinBLDGeoBox Box = TwinBLDGeo::BoxAround(TwinBLDGeo::MakePoint(35.6595, 139.7005), 250.0);
			TestTrue(TEXT("Width is about 500 m"), FMath::IsNearlyEqual(TwinBLDGeo::BoxWidthMeters(Box), 500.0, 5.0));
			TestTrue(TEXT("Height is about 500 m"), FMath::IsNearlyEqual(TwinBLDGeo::BoxHeightMeters(Box), 500.0, 5.0));

			FString Error;
			TestTrue(TEXT("Box is valid"), TwinBLDGeo::ValidateBox(Box, TEXT("Box"), Error));

			FTwinBLDGeoBox Inverted = Box;
			Swap(Inverted.North, Inverted.South);
			TestFalse(TEXT("Inverted box is rejected"), TwinBLDGeo::ValidateBox(Inverted, TEXT("Box"), Error));
			TestTrue(TEXT("Error names the field"), Error.Contains(TEXT("Box")));
		});

		It(TEXT("computes the sun position"), [this]()
		{
			double Azimuth = 0.0;
			double Elevation = 0.0;

			// March equinox, solar noon on the prime meridian at the equator: sun nearly overhead.
			TwinBLDGeo::ComputeSunPosition(FDateTime(2026, 3, 20, 12, 7, 0), 0.0, 0.0, Azimuth, Elevation);
			TestTrue(TEXT("Equinox noon sun is nearly overhead"), Elevation > 85.0);

			// June solstice afternoon in New York (17:00 UTC is 13:00 EDT): high in the southern sky.
			TwinBLDGeo::ComputeSunPosition(FDateTime(2026, 6, 21, 17, 0, 0), 40.7411, -73.9897, Azimuth, Elevation);
			TestTrue(TEXT("New York summer noon elevation is about 72 degrees"), FMath::IsNearlyEqual(Elevation, 72.0, 3.0));
			TestTrue(TEXT("New York summer noon azimuth is southerly"), Azimuth > 150.0 && Azimuth < 230.0);

			// Midnight UTC in London: sun below the horizon.
			TwinBLDGeo::ComputeSunPosition(FDateTime(2026, 12, 21, 0, 0, 0), 51.5007, -0.1246, Azimuth, Elevation);
			TestTrue(TEXT("London midnight sun is below the horizon"), Elevation < 0.0);
		});
	});

	Describe(TEXT("nominatim"), [this]()
	{
		It(TEXT("parses search results"), [this]()
		{
			TArray<FTwinBLDPlace> Places;
			FString Error;
			if (!TestTrue(TEXT("Parses"), TwinBLDNominatim::ParsePlaces(NominatimSearchFixture, Places, Error)) || !TestEqual(TEXT("One place"), Places.Num(), 1))
			{
				return;
			}

			const FTwinBLDPlace& Place = Places[0];
			TestEqual(TEXT("Name"), Place.Name, FString(TEXT("Flatiron Building")));
			TestEqual(TEXT("OsmType"), Place.OsmType, FString(TEXT("way")));
			TestEqual(TEXT("OsmId"), Place.OsmId, static_cast<int64>(264768896));
			TestTrue(TEXT("Latitude"), FMath::IsNearlyEqual(Place.Location.Lat, 40.7410861, 1.0e-7));
			TestTrue(TEXT("Longitude"), FMath::IsNearlyEqual(Place.Location.Lon, -73.9896530, 1.0e-7));
			TestTrue(TEXT("Bounds south"), FMath::IsNearlyEqual(Place.Bounds.South, 40.7407926, 1.0e-7));
			TestTrue(TEXT("Bounds east"), FMath::IsNearlyEqual(Place.Bounds.East, -73.9893020, 1.0e-7));
			TestEqual(TEXT("Wikidata"), Place.WikidataId, FString(TEXT("Q220728")));
			TestTrue(TEXT("Extra tags include height"), Place.ExtraTags.ContainsByPredicate([](const FTwinBLDKeyValue& Tag)
			{
				return Tag.Key == TEXT("height") && Tag.Value == TEXT("87");
			}));
		});

		It(TEXT("treats a reverse-geocoding miss as no results"), [this]()
		{
			TArray<FTwinBLDPlace> Places;
			FString Error;
			TestTrue(TEXT("Parses"), TwinBLDNominatim::ParsePlaces(TEXT("{\"error\":\"Unable to geocode\"}"), Places, Error));
			TestEqual(TEXT("No places"), Places.Num(), 0);
		});

		It(TEXT("rejects invalid JSON"), [this]()
		{
			TArray<FTwinBLDPlace> Places;
			FString Error;
			TestFalse(TEXT("Rejects"), TwinBLDNominatim::ParsePlaces(TEXT("<html>rate limited</html>"), Places, Error));
			TestFalse(TEXT("Explains"), Error.IsEmpty());
		});
	});

	Describe(TEXT("scene"), [this]()
	{
		It(TEXT("rejects a missing building"), [this]()
		{
			AddExpectedError(TEXT("Building"), EAutomationExpectedErrorFlags::Contains, 1);
			const FTwinBLDBuildingEditResult Result = UTwinBLDSceneToolset::EditBuildingFromReality(nullptr, FTwinBLDBuildingEdit());
			TestTrue(TEXT("Nothing changed"), Result.Changes.IsEmpty());
		});
	});
}

#endif
