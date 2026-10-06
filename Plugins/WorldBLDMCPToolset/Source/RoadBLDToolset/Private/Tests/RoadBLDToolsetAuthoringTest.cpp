// Copyright WorldBLD LLC. All rights reserved.

#include "Misc/AutomationTest.h"

#include "Common/RoadBLDRebuildJobs.h"
#include "Common/RoadBLDToolsetUtils.h"

#include "Components/SplineComponent.h"
#include "DynamicMesh/DynamicMesh3.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadLane.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "Editor.h"
#include "Engine/World.h"
#include "RoadGeo.h"
#include "Toolsets/RoadBLDAuthoringToolset.h"
#include "Toolsets/RoadBLDDiscoveryToolset.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace RoadBLDToolsetAuthoringTestPrivate
{
	const TCHAR* StreetPresetPath = TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Street_2Lane.RP_Default_USA_Street_2Lane_C");
	const TCHAR* BoulevardPresetPath = TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Boulevard_4Lane_CenterTurns.RP_Default_USA_Boulevard_4Lane_CenterTurns_C");

	TArray<FRoadBLDPoint> MakeStraightPoints(const FVector& Start, const FVector& End)
	{
		TArray<FRoadBLDPoint> Points;
		Points.AddDefaulted(2);
		Points[0].Location = Start;
		Points[1].Location = End;
		return Points;
	}

	ADynamicRoad* FindRoad(const FRoadBLDActorRef& Ref)
	{
		return FindObject<ADynamicRoad>(nullptr, *Ref.RefPath);
	}

	ADynamicRoad* FindRoadByLabel(const FRoadBLDEditResult& Result, const FString& Label)
	{
		const FRoadBLDActorRef* Ref = Result.Roads.FindByPredicate([&Label](const FRoadBLDActorRef& Candidate) { return Candidate.Label == Label; });
		return Ref ? FindRoad(*Ref) : nullptr;
	}

	FRoadBLDEndpointRef MakeEnd(ADynamicRoad* Road, const bool bStart)
	{
		FRoadBLDEndpointRef End;
		End.Road = Road;
		End.bStart = bStart;
		return End;
	}

	int32 CountIssuesOfKind(ADynamicRoadNetwork* Network, const FString& Kind)
	{
		return URoadBLDDiscoveryToolset::FindJunctionIssues(Network).FilterByPredicate([&Kind](const FRoadBLDJunctionIssue& Issue)
		{
			return Issue.Kind == Kind;
		}).Num();
	}

	int32 CountPoints(const ADynamicRoad* Road)
	{
		return IsValid(Road) && Road->ControlSpline ? Road->ControlSpline->GetNumberOfSplinePoints() : 0;
	}

	/** Centers of generated triangles with a horizontal edge longer than MinEdge, found without the toolset's filters. */
	TArray<FVector> FindLongTriangles(const ADynamicRoadNetwork* Network, const double MinEdge)
	{
		TArray<FVector> Centers;
		for (const ARoadGeo* Geo : RoadBLDToolset::GetNetworkGeos(Network))
		{
			UE::Geometry::FDynamicMesh3 Mesh;
			if (!Geo->GetSurfaceMeshView().CopyToDynamicMesh(Mesh, true))
			{
				continue;
			}

			for (const int32 TriangleId : Mesh.TriangleIndicesItr())
			{
				FVector3d A, B, C;
				Mesh.GetTriVertices(TriangleId, A, B, C);
				if (FMath::Max3(FVector::Dist2D(A, B), FVector::Dist2D(B, C), FVector::Dist2D(C, A)) > MinEdge)
				{
					Centers.Add((A + B + C) / 3.0);
				}
			}
		}
		return Centers;
	}

	/** Rebuilds the whole network and calls OnDone when the rebuild finishes. */
	void RebuildThen(ADynamicRoadNetwork* Network, TFunction<void(const FRoadBLDRebuildStatus&)> OnDone)
	{
		for (const TObjectPtr<ADynamicRoad>& Road : Network->RoadsInNetwork)
		{
			Road->CalculateRefLine();
		}
		const FGuid JobId = FRoadBLDRebuildJobs::Get().Start({ Network }, {}, true, false);
		FRoadBLDRebuildJobs::Get().Wait(JobId, 120.0, MoveTemp(OnDone));
	}
}

BEGIN_DEFINE_SPEC(
	FRoadBLDToolsetAuthoringSpec,
	TEXT("AI.Toolsets.WorldBLD.RoadBLDToolset.Authoring"),
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
	TWeakObjectPtr<ADynamicRoadNetwork> Network;
	UClass* StreetPreset = nullptr;

	void DefineCornerTests();
	void DefineGeometryTests();

	/** Draws an L: A runs +X into Corner, B leaves Corner towards +Y. Returns {A, B}. */
	TPair<ADynamicRoad*, ADynamicRoad*> CreateL(const FVector& Corner, UClass* PresetB, TArray<FString>* OutWarningsB = nullptr);
END_DEFINE_SPEC(FRoadBLDToolsetAuthoringSpec)

TPair<ADynamicRoad*, ADynamicRoad*> FRoadBLDToolsetAuthoringSpec::CreateL(const FVector& Corner, UClass* PresetB, TArray<FString>* OutWarningsB)
{
	using namespace RoadBLDToolsetAuthoringTestPrivate;

	RoadBLDToolset::FScopedTestAuthorization Authorization;
	const FRoadBLDEditResult ResultA = URoadBLDAuthoringToolset::CreateRoad(
		StreetPreset, MakeStraightPoints(Corner - FVector(12000, 0, 0), Corner), Network.Get(), TEXT("AITest_CornerA"));
	const FRoadBLDEditResult ResultB = URoadBLDAuthoringToolset::CreateRoad(
		PresetB, MakeStraightPoints(Corner, Corner + FVector(0, 12000, 0)), Network.Get(), TEXT("AITest_CornerB"));
	if (OutWarningsB)
	{
		*OutWarningsB = ResultB.Warnings;
	}

	ADynamicRoad* RoadA = ResultA.Roads.Num() > 0 ? FindRoad(ResultA.Roads[0]) : nullptr;
	ADynamicRoad* RoadB = ResultB.Roads.Num() > 0 ? FindRoad(ResultB.Roads[0]) : nullptr;
	for (ADynamicRoad* Road : { RoadA, RoadB })
	{
		if (Road)
		{
			Road->CalculateRefLine();
		}
	}
	return TPair<ADynamicRoad*, ADynamicRoad*>(RoadA, RoadB);
}

void FRoadBLDToolsetAuthoringSpec::Define()
{
	using namespace RoadBLDToolsetAuthoringTestPrivate;

	BeforeEach([this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		StreetPreset = LoadClass<UDynamicRoadDrawPreset>(nullptr, StreetPresetPath);
		TestNotNull(TEXT("USA street preset is available"), StreetPreset);

		const FRoadBLDActorRef NetworkRef = URoadBLDAuthoringToolset::CreateNetwork(TEXT("AITest_RoadNetwork"));
		Network = FindObject<ADynamicRoadNetwork>(nullptr, *NetworkRef.RefPath);
		TestTrue(TEXT("Network created"), Network.IsValid());
	});

	AfterEach([this]()
	{
		if (ADynamicRoadNetwork* TestNetwork = Network.Get())
		{
			UWorld* World = TestNetwork->GetWorld();
			TArray<TObjectPtr<ADynamicRoad>> Roads = TestNetwork->RoadsInNetwork;
			for (const TObjectPtr<ADynamicRoad>& Road : Roads)
			{
				if (IsValid(Road))
				{
					World->EditorDestroyActor(Road, true);
				}
			}
			World->EditorDestroyActor(TestNetwork, true);
		}
		Network.Reset();
	});

	It(TEXT("creates a road from points using a preset"), [this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		if (!StreetPreset || !Network.IsValid())
		{
			return;
		}

		const FRoadBLDEditResult Result = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(FVector(0, 0, 0), FVector(10000, 0, 0)), Network.Get(), TEXT("AITest_Street"));
		TestEqual(TEXT("One road created"), Result.Roads.Num(), 1);
		TestTrue(TEXT("Needs rebuild"), Result.bNeedsRebuild);

		const FRoadBLDRoadInfo Info = URoadBLDDiscoveryToolset::DescribeRoad(FindRoad(Result.Roads[0]));
		TestTrue(TEXT("Road has lanes"), Info.LeftLanes.Num() + Info.RightLanes.Num() > 0);
		TestTrue(TEXT("Road length matches"), FMath::IsNearlyEqual(Info.Length, 10000.0, 50.0));
		TestEqual(TEXT("Preset recorded"), Info.PresetId, FString(StreetPreset->GetPathName()));
	});

	It(TEXT("changes a lane width over a range"), [this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		if (!StreetPreset || !Network.IsValid())
		{
			return;
		}

		const FRoadBLDEditResult Created = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(FVector(0, 5000, 0), FVector(20000, 5000, 0)), Network.Get());
		ADynamicRoad* Road = FindRoad(Created.Roads[0]);
		const FRoadBLDRoadInfo Before = URoadBLDDiscoveryToolset::DescribeRoad(Road);
		if (!TestTrue(TEXT("Road has a right lane"), Before.RightLanes.Num() > 0))
		{
			return;
		}

		FRoadBLDRange Range;
		Range.StartDistance = 8000.0;
		Range.EndDistance = 12000.0;
		Range.Transition = 1000.0;
		const double OriginalWidth = Before.RightLanes[0].WidthAtStart;
		URoadBLDAuthoringToolset::SetLaneWidth(Road, ERoadBLDSide::Right, 0, OriginalWidth + 200.0, Range);

		const FRoadBLDRoadInfo After = URoadBLDDiscoveryToolset::DescribeRoad(Road);
		TestTrue(TEXT("Width at start unchanged"), FMath::IsNearlyEqual(After.RightLanes[0].WidthAtStart, OriginalWidth, 1.0));
		TestTrue(TEXT("Widened within the range"), FMath::IsNearlyEqual(After.RightLanes[0].MaxWidth, OriginalWidth + 200.0, 1.0));
	});

	It(TEXT("removes sidewalks"), [this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		if (!StreetPreset || !Network.IsValid())
		{
			return;
		}

		const FRoadBLDEditResult Created = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(FVector(0, 10000, 0), FVector(8000, 10000, 0)), Network.Get());
		ADynamicRoad* Road = FindRoad(Created.Roads[0]);
		URoadBLDAuthoringToolset::SetSidewalk(Road, ERoadBLDSide::Both, nullptr);

		const FRoadBLDRoadInfo Info = URoadBLDDiscoveryToolset::DescribeRoad(Road);
		TestFalse(TEXT("No left sidewalk"), Info.LeftSidewalk.bPresent);
		TestFalse(TEXT("No right sidewalk"), Info.RightSidewalk.bPresent);
	});

	It(TEXT("creates a linked two-piece roundabout with approaches"), [this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		if (!StreetPreset || !Network.IsValid())
		{
			return;
		}

		const FRoadBLDEditResult Result = URoadBLDAuthoringToolset::CreateRoundabout(
			StreetPreset, FVector(30000, 30000, 0), 3000.0, 3, 0.0, 6000.0, nullptr, Network.Get());
		TestEqual(TEXT("Two ring halves and three approaches"), Result.Roads.Num(), 5);

		const FRoadBLDRoadInfo RingA = URoadBLDDiscoveryToolset::DescribeRoad(FindRoad(Result.Roads[0]));
		TestEqual(TEXT("Ring start linked"), RingA.Start.Links.Num(), 1);
		TestEqual(TEXT("Ring end linked"), RingA.End.Links.Num(), 1);
	});

	It(TEXT("links touching endpoints and deletes roads with their links"), [this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		if (!StreetPreset || !Network.IsValid())
		{
			return;
		}

		const FRoadBLDEditResult First = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(FVector(0, 20000, 0), FVector(6000, 20000, 0)), Network.Get(), TEXT(""), false);
		const FRoadBLDEditResult Second = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(FVector(6000, 20000, 0), FVector(12000, 21000, 0)), Network.Get(), TEXT(""), false);
		ADynamicRoad* RoadA = FindRoad(First.Roads[0]);
		ADynamicRoad* RoadB = FindRoad(Second.Roads[0]);

		FRoadBLDEndpointRef EndA;
		EndA.Road = RoadA;
		EndA.bStart = false;
		FRoadBLDEndpointRef StartB;
		StartB.Road = RoadB;
		StartB.bStart = true;
		URoadBLDAuthoringToolset::ConnectEndpoints(EndA, StartB, ERoadBLDConnectMode::Link);
		TestEqual(TEXT("A end linked"), URoadBLDDiscoveryToolset::DescribeRoad(RoadA).End.Links.Num(), 1);

		URoadBLDAuthoringToolset::DeleteRoads({ RoadB });
		TestFalse(TEXT("B removed from network"), Network->RoadsInNetwork.Contains(RoadB));
		TestEqual(TEXT("A link removed"), URoadBLDDiscoveryToolset::DescribeRoad(RoadA).End.Links.Num(), 0);
	});

	Describe(TEXT("junction snapping"), [this]()
	{
		// Main road along Y at X=50000; side roads approach from -X along Y=40000.
		const double MainX = 50000.0;
		const double SideY = 40000.0;

		auto CreateMain = [this, MainX]()
		{
			const FRoadBLDEditResult Main = URoadBLDAuthoringToolset::CreateRoad(
				StreetPreset, MakeStraightPoints(FVector(MainX, 30000, 0), FVector(MainX, 50000, 0)), Network.Get(), TEXT("AITest_Main"));
			ADynamicRoad* Road = FindRoad(Main.Roads[0]);
			Road->CalculateRefLine();
			return Road;
		};

		auto EndX = [](const FRoadBLDEditResult& Result)
		{
			return URoadBLDDiscoveryToolset::DescribeRoad(FindRoad(Result.Roads[0])).End.Location.X;
		};

		It(TEXT("snaps an end just past the far edge to the centerline"), [this, CreateMain, EndX, MainX, SideY]()
		{
			RoadBLDToolset::FScopedTestAuthorization Authorization;

			if (!StreetPreset || !Network.IsValid())
			{
				return;
			}

			const double HalfWidth = RoadBLDToolset::GetRoadSideWidth(CreateMain(), ERoadSide::Left, 10000.0);
			const FRoadBLDEditResult Side = URoadBLDAuthoringToolset::CreateRoad(
				StreetPreset, MakeStraightPoints(FVector(MainX - 10000, SideY, 0), FVector(MainX + HalfWidth + 20, SideY, 0)), Network.Get());
			TestTrue(TEXT("End on the centerline"), FMath::IsNearlyEqual(EndX(Side), MainX, 5.0));
			TestEqual(TEXT("One warning"), Side.Warnings.Num(), 1);
		});

		It(TEXT("keeps a clean crossing"), [this, CreateMain, EndX, MainX, SideY]()
		{
			RoadBLDToolset::FScopedTestAuthorization Authorization;

			if (!StreetPreset || !Network.IsValid())
			{
				return;
			}

			const double HalfWidth = RoadBLDToolset::GetRoadSideWidth(CreateMain(), ERoadSide::Left, 10000.0);
			const double CrossEnd = MainX + HalfWidth + RoadBLDToolset::JunctionMinCrossArm + 3000.0;
			const FRoadBLDEditResult Side = URoadBLDAuthoringToolset::CreateRoad(
				StreetPreset, MakeStraightPoints(FVector(MainX - 10000, SideY, 0), FVector(CrossEnd, SideY, 0)), Network.Get());
			TestTrue(TEXT("End unchanged"), FMath::IsNearlyEqual(EndX(Side), CrossEnd, 1.0));
			TestEqual(TEXT("No warnings"), Side.Warnings.Num(), 0);
		});

		It(TEXT("pulls an end that stops just short onto the centerline"), [this, CreateMain, EndX, MainX, SideY]()
		{
			RoadBLDToolset::FScopedTestAuthorization Authorization;

			if (!StreetPreset || !Network.IsValid())
			{
				return;
			}

			const double HalfWidth = RoadBLDToolset::GetRoadSideWidth(CreateMain(), ERoadSide::Right, 10000.0);
			const FRoadBLDEditResult Side = URoadBLDAuthoringToolset::CreateRoad(
				StreetPreset, MakeStraightPoints(FVector(MainX - 10000, SideY, 0), FVector(MainX - HalfWidth - 100, SideY, 0)), Network.Get());
			TestTrue(TEXT("End on the centerline"), FMath::IsNearlyEqual(EndX(Side), MainX, 5.0));
		});

		It(TEXT("reports stubs made with snapping disabled"), [this, CreateMain, MainX, SideY]()
		{
			RoadBLDToolset::FScopedTestAuthorization Authorization;

			if (!StreetPreset || !Network.IsValid())
			{
				return;
			}

			const double HalfWidth = RoadBLDToolset::GetRoadSideWidth(CreateMain(), ERoadSide::Left, 10000.0);
			const FRoadBLDEditResult Side = URoadBLDAuthoringToolset::CreateRoad(
				StreetPreset, MakeStraightPoints(FVector(MainX - 10000, SideY, 0), FVector(MainX - 5000, SideY, 0)), Network.Get());
			ADynamicRoad* SideRoad = FindRoad(Side.Roads[0]);
			URoadBLDAuthoringToolset::SetControlPoints(
				SideRoad, MakeStraightPoints(FVector(MainX - 10000, SideY, 0), FVector(MainX + HalfWidth + 20, SideY, 0)), 100.0, false);
			SideRoad->CalculateRefLine();

			const TArray<FRoadBLDJunctionIssue> Issues = URoadBLDDiscoveryToolset::FindJunctionIssues(Network.Get());
			if (TestEqual(TEXT("One issue"), Issues.Num(), 1))
			{
				TestEqual(TEXT("Stub past the main road"), Issues[0].Kind, FString(TEXT("StubPastRoad")));
				TestTrue(TEXT("Suggested end on the centerline"), FMath::IsNearlyEqual(Issues[0].SuggestedLocation.X, MainX, 5.0));
			}
		});

		It(TEXT("drops a grid overhang too short to cross the perimeter"), [this]()
		{
			RoadBLDToolset::FScopedTestAuthorization Authorization;

			if (!StreetPreset || !Network.IsValid())
			{
				return;
			}

			FRoadBLDGridSpec Grid;
			Grid.Origin = FVector(-60000, -60000, 0);
			Grid.SizeX = 20000.0;
			Grid.SizeY = 20000.0;
			Grid.SpacingX = 10000.0;
			Grid.SpacingY = 10000.0;
			Grid.bIncludePerimeter = true;
			Grid.Overhang = 50.0;
			const FRoadBLDEditResult Result = URoadBLDAuthoringToolset::CreateGrid(StreetPreset, Grid, nullptr, Network.Get());
			TestEqual(FString::Printf(TEXT("One warning (%s)"), *FString::Join(Result.Warnings, TEXT(" | "))), Result.Warnings.Num(), 1);

			ADynamicRoad* RowRoad = FindRoadByLabel(Result, TEXT("GridRoad_Row00"));
			if (TestNotNull(TEXT("Interior row exists"), RowRoad))
			{
				const FRoadBLDRoadInfo Row = URoadBLDDiscoveryToolset::DescribeRoad(RowRoad);
				TestTrue(TEXT("Row ends flush at the perimeter"), FMath::IsNearlyEqual(Row.End.Location.X, -40000.0, 1.0));
			}
		});
	});

	Describe(TEXT("corners"), [this]()
	{
		DefineCornerTests();
	});

	Describe(TEXT("geometry issues"), [this]()
	{
		DefineGeometryTests();
	});

	It(TEXT("places new roads 5 cm above the ground and keeps reshaped points exact"), [this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		if (!StreetPreset || !Network.IsValid())
		{
			return;
		}

		const FRoadBLDEditResult Created = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(FVector(0, 70000, 100), FVector(8000, 70000, 100)), Network.Get());
		ADynamicRoad* Road = FindRoad(Created.Roads[0]);
		const FRoadBLDRoadInfo Info = URoadBLDDiscoveryToolset::DescribeRoad(Road);
		TestTrue(TEXT("Lifted on create"), FMath::IsNearlyEqual(Info.ControlPoints[0].Location.Z, 105.0, 0.1));

		URoadBLDAuthoringToolset::SetControlPoints(Road, Info.ControlPoints);
		const FRoadBLDRoadInfo Reshaped = URoadBLDDiscoveryToolset::DescribeRoad(Road);
		TestTrue(TEXT("Not lifted again on reshape"), FMath::IsNearlyEqual(Reshaped.ControlPoints[0].Location.Z, 105.0, 0.1));
	});
}

void FRoadBLDToolsetAuthoringSpec::DefineCornerTests()
{
	using namespace RoadBLDToolsetAuthoringTestPrivate;

	const FVector Corner(20000.0, 100000.0, 0.0);

	It(TEXT("reports an unjoined L corner and warns when it is drawn"), [this, Corner]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		TArray<FString> Warnings;
		const TPair<ADynamicRoad*, ADynamicRoad*> Roads = CreateL(Corner, StreetPreset, &Warnings);
		TestTrue(TEXT("Drawing the corner warns"), Warnings.ContainsByPredicate([](const FString& Warning) { return Warning.Contains(TEXT("CloseCorner")); }));
		TestEqual(TEXT("The corner ends are not linked"), RoadBLDToolset::CountEndpointLinks(Roads.Key, false), 0);

		const TArray<FRoadBLDJunctionIssue> Issues = URoadBLDDiscoveryToolset::FindJunctionIssues(Network.Get());
		if (TestEqual(TEXT("One issue"), Issues.Num(), 1))
		{
			TestEqual(TEXT("Kind"), Issues[0].Kind, FString(TEXT("UnjoinedCorner")));
			TestNearlyEqual(TEXT("Turn angle"), Issues[0].TurnAngle, 90.0, 1.0);
			TestTrue(TEXT("Suggestion names CloseCorner"), Issues[0].Suggestion.Contains(TEXT("CloseCorner")));
		}
	});

	It(TEXT("reports a sharp linked corner"), [this, Corner]()
	{
		const TPair<ADynamicRoad*, ADynamicRoad*> Roads = CreateL(Corner, StreetPreset);
		TestTrue(TEXT("Linked for the test"), RoadBLDToolset::CreateReciprocalLink(Roads.Key, false, Roads.Value, true));
		TestEqual(TEXT("One sharp linked corner"), CountIssuesOfKind(Network.Get(), TEXT("SharpLinkedCorner")), 1);
	});

	It(TEXT("links a straight continuation and reports nothing"), [this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		const FRoadBLDEditResult First = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(FVector(0, 110000, 0), FVector(10000, 110000, 0)), Network.Get());
		const FRoadBLDEditResult Second = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(FVector(10000, 110000, 0), FVector(20000, 111000, 0)), Network.Get());
		TestEqual(TEXT("Continuation auto-linked"), RoadBLDToolset::CountEndpointLinks(FindRoad(First.Roads[0]), false), 1);
		TestEqual(TEXT("No warnings"), Second.Warnings.Num(), 0);
		TestEqual(TEXT("No issues"), URoadBLDDiscoveryToolset::FindJunctionIssues(Network.Get()).Num(), 0);
	});

	It(TEXT("refuses to link ends that meet at an angle"), [this, Corner]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		const TPair<ADynamicRoad*, ADynamicRoad*> Roads = CreateL(Corner, StreetPreset);
		const FRoadBLDEditResult Result = URoadBLDAuthoringToolset::ConnectEndpoints(MakeEnd(Roads.Key, false), MakeEnd(Roads.Value, true), ERoadBLDConnectMode::Link);
		TestEqual(TEXT("No roads returned"), Result.Roads.Num(), 0);
		TestEqual(TEXT("Not linked"), RoadBLDToolset::CountEndpointLinks(Roads.Key, false), 0);
	});

	It(TEXT("merges a same-preset L into one road"), [this, Corner]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		const TPair<ADynamicRoad*, ADynamicRoad*> Roads = CreateL(Corner, StreetPreset);
		FVector FarEndB;
		RoadBLDToolset::GetEndpointLocation(Roads.Value, false, FarEndB);

		const FRoadBLDEditResult Result = URoadBLDAuthoringToolset::CloseCorner(MakeEnd(Roads.Key, false), MakeEnd(Roads.Value, true), 3000.0);
		TestEqual(TEXT("One road returned"), Result.Roads.Num(), 1);
		TestFalse(TEXT("B removed from the network"), Network->RoadsInNetwork.Contains(Roads.Value));
		TestEqual(TEXT("A runs through the corner"), CountPoints(Roads.Key), 3);

		FVector EndA;
		RoadBLDToolset::GetEndpointLocation(Roads.Key, false, EndA);
		TestTrue(TEXT("A ends where B ended"), EndA.Equals(FarEndB, 1.0));
		TestEqual(TEXT("No issues"), URoadBLDDiscoveryToolset::FindJunctionIssues(Network.Get()).Num(), 0);
	});

	It(TEXT("moves the far-end link of the merged road"), [this, Corner]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		const TPair<ADynamicRoad*, ADynamicRoad*> Roads = CreateL(Corner, StreetPreset);
		const FRoadBLDEditResult Next = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(Corner + FVector(0, 12000, 0), Corner + FVector(0, 24000, 0)), Network.Get());
		ADynamicRoad* NextRoad = FindRoad(Next.Roads[0]);
		TestEqual(TEXT("B continues into the next road"), RoadBLDToolset::CountEndpointLinks(Roads.Value, false), 1);

		URoadBLDAuthoringToolset::CloseCorner(MakeEnd(Roads.Key, false), MakeEnd(Roads.Value, true), 3000.0);
		TestTrue(TEXT("A's end now links to the next road"), RoadBLDToolset::AreEndpointsLinked(Roads.Key, false, NextRoad, true));
		TestTrue(TEXT("The next road links back to A"), RoadBLDToolset::AreEndpointsLinked(NextRoad, true, Roads.Key, false));
	});

	It(TEXT("joins a mixed-preset L with a linked connector"), [this, Corner]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		UClass* Boulevard = LoadClass<UDynamicRoadDrawPreset>(nullptr, BoulevardPresetPath);
		if (!TestNotNull(TEXT("Boulevard preset is available"), Boulevard))
		{
			return;
		}

		const TPair<ADynamicRoad*, ADynamicRoad*> Roads = CreateL(Corner, Boulevard);
		const FRoadBLDEditResult Result = URoadBLDAuthoringToolset::CloseCorner(MakeEnd(Roads.Key, false), MakeEnd(Roads.Value, true), 3000.0);
		if (!TestEqual(TEXT("A, connector and B returned"), Result.Roads.Num(), 3))
		{
			return;
		}

		ADynamicRoad* Connector = FindRoad(Result.Roads[1]);
		TestTrue(TEXT("B is kept"), Network->RoadsInNetwork.Contains(Roads.Value));
		TestTrue(TEXT("Connector starts at A"), RoadBLDToolset::AreEndpointsLinked(Connector, true, Roads.Key, false));
		TestTrue(TEXT("Connector ends at B"), RoadBLDToolset::AreEndpointsLinked(Connector, false, Roads.Value, true));
		TestTrue(TEXT("Lane change is reported"), Result.Warnings.ContainsByPredicate([](const FString& Warning) { return Warning.Contains(TEXT("different presets")); }));
		TestEqual(TEXT("No unjoined corners"), CountIssuesOfKind(Network.Get(), TEXT("UnjoinedCorner")), 0);
		TestEqual(TEXT("No sharp linked corners"), CountIssuesOfKind(Network.Get(), TEXT("SharpLinkedCorner")), 0);
	});

	It(TEXT("undoes a merge"), [this, Corner]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		const TPair<ADynamicRoad*, ADynamicRoad*> Roads = CreateL(Corner, StreetPreset);
		const FString PathB = Roads.Value->GetPathName();
		URoadBLDAuthoringToolset::CloseCorner(MakeEnd(Roads.Key, false), MakeEnd(Roads.Value, true), 3000.0);
		if (!TestEqual(TEXT("Merged"), CountPoints(Roads.Key), 3) || !TestNotNull(TEXT("Editor"), GEditor))
		{
			return;
		}

		TestTrue(TEXT("Undo succeeds"), GEditor->UndoTransaction(false));
		ADynamicRoad* RestoredB = FindObject<ADynamicRoad>(nullptr, *PathB);
		TestTrue(TEXT("B restored"), IsValid(RestoredB) && Network->RoadsInNetwork.Contains(RestoredB));
		TestEqual(TEXT("A restored"), CountPoints(Roads.Key), 2);
	});

	It(TEXT("closes corners while drawing when asked"), [this, Corner]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		const FRoadBLDEditResult ResultA = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(Corner - FVector(12000, 0, 0), Corner), Network.Get());
		ADynamicRoad* RoadA = FindRoad(ResultA.Roads[0]);
		const FRoadBLDEditResult ResultB = URoadBLDAuthoringToolset::CreateRoad(
			StreetPreset, MakeStraightPoints(Corner, Corner + FVector(0, 12000, 0)), Network.Get(), TEXT("Auto"), true, 100.0, false, true, true);
		if (!TestEqual(TEXT("One road returned"), ResultB.Roads.Num(), 1))
		{
			return;
		}

		ADynamicRoad* RoadB = FindRoad(ResultB.Roads[0]);
		TestFalse(TEXT("The existing road was merged away"), Network->RoadsInNetwork.Contains(RoadA));
		TestEqual(TEXT("The new road runs through the corner"), CountPoints(RoadB), 3);
		TestEqual(TEXT("No issues"), URoadBLDDiscoveryToolset::FindJunctionIssues(Network.Get()).Num(), 0);
	});

	It(TEXT("builds the grid perimeter as one closed loop"), [this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;

		FRoadBLDGridSpec Grid;
		Grid.Origin = FVector(-60000, 120000, 0);
		Grid.SizeX = 30000.0;
		Grid.SizeY = 20000.0;
		const FRoadBLDEditResult Result = URoadBLDAuthoringToolset::CreateGrid(StreetPreset, Grid, nullptr, Network.Get());
		TestEqual(TEXT("One row, two columns and two perimeter halves"), Result.Roads.Num(), 5);
		TestEqual(FString::Printf(TEXT("No warnings (%s)"), *FString::Join(Result.Warnings, TEXT(" | "))), Result.Warnings.Num(), 0);

		ADynamicRoad* PerimeterA = FindRoadByLabel(Result, TEXT("GridRoad_Perimeter_A"));
		ADynamicRoad* PerimeterB = FindRoadByLabel(Result, TEXT("GridRoad_Perimeter_B"));
		if (TestNotNull(TEXT("Perimeter A"), PerimeterA) && TestNotNull(TEXT("Perimeter B"), PerimeterB))
		{
			TestTrue(TEXT("Loop closed at A's end"), RoadBLDToolset::AreEndpointsLinked(PerimeterA, false, PerimeterB, true));
			TestTrue(TEXT("Loop closed at B's end"), RoadBLDToolset::AreEndpointsLinked(PerimeterB, false, PerimeterA, true));
		}

		for (const TObjectPtr<ADynamicRoad>& Road : Network->RoadsInNetwork)
		{
			Road->CalculateRefLine();
		}
		for (const FRoadBLDJunctionIssue& Issue : URoadBLDDiscoveryToolset::FindJunctionIssues(Network.Get()))
		{
			AddError(FString::Printf(TEXT("%s at %s: %s"), *Issue.Kind, *Issue.Road.Label, *Issue.Suggestion));
		}
	});
}

void FRoadBLDToolsetAuthoringSpec::DefineGeometryTests()
{
	using namespace RoadBLDToolsetAuthoringTestPrivate;

	LatentIt(TEXT("finds no issues on a straight road and a clean T junction"), FTimespan::FromSeconds(150), [this](const FDoneDelegate& Done)
	{
		if (!StreetPreset || !Network.IsValid())
		{
			Done.Execute();
			return;
		}

		{
			RoadBLDToolset::FScopedTestAuthorization Authorization;
			URoadBLDAuthoringToolset::CreateRoad(StreetPreset, MakeStraightPoints(FVector(0, 150000, 0), FVector(20000, 150000, 0)), Network.Get());
			URoadBLDAuthoringToolset::CreateRoad(StreetPreset, MakeStraightPoints(FVector(10000, 160000, 0), FVector(10000, 150000, 0)), Network.Get());
			URoadBLDAuthoringToolset::CreateRoad(StreetPreset, MakeStraightPoints(FVector(0, 175000, 0), FVector(30000, 175000, 0)), Network.Get());
		}

		RebuildThen(Network.Get(), [this, Done](const FRoadBLDRebuildStatus& Status)
		{
			TestEqual(TEXT("Rebuild succeeded"), Status.State, ERoadBLDRebuildState::Succeeded);
			if (RoadBLDToolset::GetNetworkGeos(Network.Get()).Num() == 0)
			{
				AddWarning(TEXT("The rebuild produced no geometry in this environment; nothing to scan."));
			}

			for (const FRoadBLDGeometryIssue& Issue : URoadBLDDiscoveryToolset::FindGeometryIssues(Network.Get()))
			{
				AddError(FString::Printf(TEXT("Unexpected %s at %s (%d triangles, min angle %.2f, longest edge %.0f)"),
					*Issue.Kind, *Issue.Location.ToString(), Issue.TriangleCount, Issue.MinAngle, Issue.LongestEdge));
			}
			Done.Execute();
		});
	});

	LatentIt(TEXT("reports stretched triangles"), FTimespan::FromSeconds(150), [this](const FDoneDelegate& Done)
	{
		if (!StreetPreset || !Network.IsValid())
		{
			Done.Execute();
			return;
		}

		// Unjoined ends: an L corner and the pre-loop grid layout (separate perimeter roads meeting at the corners),
		// with the L's first road collinear with the grid's first row. This builds triangles that span the gap.
		CreateL(FVector(20000.0, 200000.0, 0.0), StreetPreset);
		{
			RoadBLDToolset::FScopedTestAuthorization Authorization;
			const FVector Origin(60000.0, 200000.0, 0.0);
			for (const double Line : { 0.0, 10000.0, 20000.0 })
			{
				URoadBLDAuthoringToolset::CreateRoad(StreetPreset, MakeStraightPoints(Origin + FVector(0, Line, 0), Origin + FVector(20000, Line, 0)), Network.Get(), TEXT("Auto"), false, 100.0, false, false);
				URoadBLDAuthoringToolset::CreateRoad(StreetPreset, MakeStraightPoints(Origin + FVector(Line, 0, 0), Origin + FVector(Line, 20000, 0)), Network.Get(), TEXT("Auto"), false, 100.0, false, false);
			}
		}

		TestTrue(TEXT("The layout has unjoined corners"), CountIssuesOfKind(Network.Get(), TEXT("UnjoinedCorner")) >= 5);
		RebuildThen(Network.Get(), [this, Done](const FRoadBLDRebuildStatus& Status)
		{
			const TArray<FVector> LongTriangles = FindLongTriangles(Network.Get(), 10000.0);
			const TArray<FRoadBLDGeometryIssue> Issues = URoadBLDDiscoveryToolset::FindGeometryIssues(Network.Get());
			AddInfo(FString::Printf(TEXT("%d triangles longer than 100 m, %d geometry issues"), LongTriangles.Num(), Issues.Num()));
			if (LongTriangles.Num() == 0)
			{
				AddWarning(TEXT("RoadBLD built no stretched triangles for this layout; only the absence of false positives was checked."));
				TestEqual(TEXT("No issues"), Issues.Num(), 0);
			}

			for (const FVector& Center : LongTriangles)
			{
				TestTrue(FString::Printf(TEXT("Stretched triangle at %s is reported"), *Center.ToString()),
					Issues.ContainsByPredicate([&Center](const FRoadBLDGeometryIssue& Issue)
					{
						return FVector::Dist2D(Issue.Location, Center) <= Issue.Radius + 1000.0;
					}));
			}

			for (const FRoadBLDGeometryIssue& Issue : Issues)
			{
				TestEqual(TEXT("Issue kind"), Issue.Kind == TEXT("Sliver") || Issue.Kind == TEXT("StretchedTriangle"), true);
				TestTrue(TEXT("Issue lists nearby road ends"), Issue.NearbyEnds.Num() > 0);
			}
			Done.Execute();
		});
	});
}

#endif
