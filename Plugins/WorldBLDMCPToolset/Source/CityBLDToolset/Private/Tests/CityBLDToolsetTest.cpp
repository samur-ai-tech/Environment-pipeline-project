// Copyright WorldBLD LLC. All rights reserved.

#include "Algo/Reverse.h"
#include "BLDToolsetUtils.h"
#include "CityBLDToolset.h"
#include "CityBLDTypes.h"
#include "Common/CityBLDToolsetUtils.h"
#include "Misc/AutomationTest.h"
#include "Toolsets/CityBLDDiscoveryToolset.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace CityBLDToolsetTestPrivate
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
			{ UCityBLDToolset::StaticClass(), { TEXT("ListModularBuildings"), TEXT("DescribeBuilding"), TEXT("ListCityBlocks"), TEXT("ListBuildingStyles"), TEXT("SetBuildingStyle"), TEXT("GenerateBuilding") } },
			{ UCityBLDDiscoveryToolset::StaticClass(), { TEXT("GetCityContext"), TEXT("ListPresets"), TEXT("DescribeDistrict"), TEXT("DescribeLandUse"), TEXT("DescribeBuildingStyle"), TEXT("ListCityBlocks"), TEXT("DescribeBlock"), TEXT("ListParcels"), TEXT("ListModularBuildings"), TEXT("DescribeBuilding"), TEXT("FindCityIssues") } },
		};
	}

	const TCHAR* SampleDistrictPath = TEXT("/CityBLD/CityBLDSampleContent/Styles/Districts/District_AmericanSample");

	TArray<FVector> MakeRectangle(double MinX, double MinY, double MaxX, double MaxY)
	{
		return { FVector(MinX, MinY, 0.0), FVector(MaxX, MinY, 0.0), FVector(MaxX, MaxY, 0.0), FVector(MinX, MaxY, 0.0) };
	}
}

BEGIN_DEFINE_SPEC(
	FCityBLDToolsetSpec,
	TEXT("AI.Toolsets.WorldBLD.CityBLDToolset"),
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
END_DEFINE_SPEC(FCityBLDToolsetSpec)

void FCityBLDToolsetSpec::Define()
{
	using namespace CityBLDToolsetTestPrivate;

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

		It(TEXT("exposes optional bounds in the discovery schema"), [this]()
		{
			const FString Schema = UToolsetRegistry::GetToolsetJsonSchema(UCityBLDDiscoveryToolset::StaticClass());
			TestTrue(TEXT("bounds"), Schema.Contains(TEXT("bounds")));
			TestTrue(TEXT("maxResults"), Schema.Contains(TEXT("maxResults")));
		});

		It(TEXT("exposes the modular mesh authoring contract to agents"), [this]()
		{
			const FString DiscoverySchema = UToolsetRegistry::GetToolsetJsonSchema(UCityBLDDiscoveryToolset::StaticClass());
			TestTrue(TEXT("Unreal front axis"), DiscoverySchema.Contains(TEXT("facade/front faces +Y")));
			TestTrue(TEXT("Blender front axis"), DiscoverySchema.Contains(TEXT("Blender -Y")));
			TestTrue(TEXT("bounds drive placement"), DiscoverySchema.Contains(TEXT("imported static-mesh bounds")));
			TestTrue(TEXT("outer corners stay rectangular"), DiscoverySchema.Contains(TEXT("never bevel/chamfer its outer corners")));
			TestTrue(TEXT("details stay inside X/Z bounds"), DiscoverySchema.Contains(TEXT("detail exceed the intended X/Z bounds")));
		});
	});

	Describe(TEXT("geometry"), [this]()
	{
		It(TEXT("measures polygon area and centroid"), [this]()
		{
			const TArray<FVector> Square = MakeRectangle(0.0, 0.0, 1000.0, 1000.0);
			TestTrue(TEXT("10 m square is 100 m2"), FMath::IsNearlyEqual(CityBLDToolsetUtils::PolygonArea2D(Square), 1000000.0));
			TestTrue(TEXT("Centroid is the middle"), CityBLDToolsetUtils::PolygonCentroid(Square).Equals(FVector(500.0, 500.0, 0.0), 0.01));

			TArray<FVector> Reversed = Square;
			Algo::Reverse(Reversed);
			TestTrue(TEXT("Area ignores winding"), FMath::IsNearlyEqual(CityBLDToolsetUtils::PolygonArea2D(Reversed), 1000000.0));
		});

		It(TEXT("detects self-intersecting outlines"), [this]()
		{
			TestFalse(TEXT("Square"), CityBLDToolsetUtils::IsPolygonSelfIntersecting2D(MakeRectangle(0.0, 0.0, 1000.0, 1000.0)));

			const TArray<FVector> Bowtie = { FVector(0.0, 0.0, 0.0), FVector(1000.0, 1000.0, 0.0), FVector(1000.0, 0.0, 0.0), FVector(0.0, 1000.0, 0.0) };
			TestTrue(TEXT("Bowtie"), CityBLDToolsetUtils::IsPolygonSelfIntersecting2D(Bowtie));
		});

		It(TEXT("detects overlapping footprints but not shared edges"), [this]()
		{
			const TArray<FVector> Base = MakeRectangle(0.0, 0.0, 1000.0, 1000.0);
			TestFalse(TEXT("Shared edge"), CityBLDToolsetUtils::DoPolygonsOverlap2D(Base, MakeRectangle(1000.0, 0.0, 2000.0, 1000.0)));
			TestFalse(TEXT("Apart"), CityBLDToolsetUtils::DoPolygonsOverlap2D(Base, MakeRectangle(1500.0, 0.0, 2500.0, 1000.0)));
			TestTrue(TEXT("Crossing"), CityBLDToolsetUtils::DoPolygonsOverlap2D(Base, MakeRectangle(500.0, 500.0, 1500.0, 1500.0)));
			TestTrue(TEXT("Nested"), CityBLDToolsetUtils::DoPolygonsOverlap2D(Base, MakeRectangle(200.0, 200.0, 800.0, 800.0)));
			TestTrue(TEXT("Identical"), CityBLDToolsetUtils::DoPolygonsOverlap2D(Base, Base));
		});

		It(TEXT("filters by bounds in XY"), [this]()
		{
			FCityBLDBounds Bounds;
			Bounds.Min = FVector(0.0, 0.0, 0.0);
			Bounds.Max = FVector(1000.0, 1000.0, 0.0);

			TestTrue(TEXT("Unset bounds match"), CityBLDToolsetUtils::OverlapsBounds(FBox(FVector(5000.0), FVector(6000.0)), {}));
			TestTrue(TEXT("Overlap ignores Z"), CityBLDToolsetUtils::OverlapsBounds(FBox(FVector(500.0, 500.0, 900.0), FVector(1500.0, 1500.0, 1200.0)), Bounds));
			TestFalse(TEXT("Outside"), CityBLDToolsetUtils::OverlapsBounds(FBox(FVector(2000.0, 0.0, 0.0), FVector(3000.0, 1000.0, 0.0)), Bounds));

			FString Error;
			FCityBLDBounds Inverted = Bounds;
			Swap(Inverted.Min, Inverted.Max);
			TestFalse(TEXT("Inverted bounds are rejected"), CityBLDToolsetUtils::ValidateBounds(Inverted, Error));
		});
	});

	Describe(TEXT("discovery"), [this]()
	{
		// Called directly from C++ there is no script frame, so RaiseScriptError is silent; the registry reports it to agents.
		It(TEXT("returns empty results for missing inputs"), [this]()
		{
			TestTrue(TEXT("DescribeDistrict"), UCityBLDDiscoveryToolset::DescribeDistrict(TSubclassOf<UDistrict>()).Preset.Class.ClassPath.IsEmpty());
			TestTrue(TEXT("DescribeBlock"), UCityBLDDiscoveryToolset::DescribeBlock(nullptr).Summary.Actor.RefPath.IsEmpty());
			TestTrue(TEXT("ListParcels"), UCityBLDDiscoveryToolset::ListParcels(nullptr).Parcels.IsEmpty());
			TestTrue(TEXT("DescribeBuilding"), UCityBLDDiscoveryToolset::DescribeBuilding(nullptr).Summary.Actor.RefPath.IsEmpty());
		});

		It(TEXT("finds and describes the sample district"), [this]()
		{
			FString Error;
			UClass* DistrictClass = BLDToolset::LoadClassFromPath(SampleDistrictPath, UDistrict::StaticClass(), Error);
			if (!TestNotNull(FString::Printf(TEXT("Sample district loads (%s)"), *Error), DistrictClass))
			{
				return;
			}

			const FCityBLDPresetList Districts = UCityBLDDiscoveryToolset::ListPresets(ECityBLDPresetKind::District, TEXT("AmericanSample"));
			TestTrue(TEXT("ListPresets finds the sample district"), Districts.Presets.ContainsByPredicate([DistrictClass](const FCityBLDPresetInfo& Info)
			{
				return Info.Class.ClassPath == DistrictClass->GetPathName() && Info.bIsSampleContent;
			}));

			const FCityBLDDistrictDescription Description = UCityBLDDiscoveryToolset::DescribeDistrict(DistrictClass);
			TestFalse(TEXT("Has land uses"), Description.LandUses.IsEmpty());

			double TotalShare = 0.0;
			for (const FCityBLDWeightedClass& LandUse : Description.LandUses)
			{
				TotalShare += LandUse.Share;
				TestFalse(TEXT("Land use has a class path"), LandUse.Class.ClassPath.IsEmpty());
			}
			TestTrue(TEXT("Land use shares add up to 1"), FMath::IsNearlyEqual(TotalShare, 1.0, 0.001));
		});

		It(TEXT("summarizes the level without errors"), [this]()
		{
			const FCityBLDCityContext Context = UCityBLDDiscoveryToolset::GetCityContext();
			TestEqual(TEXT("A count for every preset kind"), Context.PresetCounts.Num(), static_cast<int32>(ECityBLDPresetKind::Prefab) + 1);
			TestFalse(TEXT("License state is reported"), Context.LicenseState.IsEmpty());

			const FCityBLDIssueReport Report = UCityBLDDiscoveryToolset::FindCityIssues({});
			TestEqual(TEXT("Issue counts add up"), Report.ErrorCount + Report.WarningCount + Report.InfoCount, Report.TotalCount);
		});
	});
}

#endif
