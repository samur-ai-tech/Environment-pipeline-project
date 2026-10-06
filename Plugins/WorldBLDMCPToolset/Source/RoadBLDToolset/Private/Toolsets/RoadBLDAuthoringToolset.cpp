// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/RoadBLDAuthoringToolset.h"

#include "Algo/Reverse.h"
#include "Common/RoadBLDRebuildJobs.h"
#include "Common/RoadBLDToolsetUtils.h"
#include "Components/SplineComponent.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadLane.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "DynamicRoad/EdgeCurve.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "RoadControlSplineComponent.h"
#include "RoadEdit/RoadEditActionScope.h"
#include "RoadEditorUtilityLibrary.h"
#include "ToolsetRegistry/ToolsetLibrary.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(RoadBLDAuthoringToolset)

namespace RoadBLDAuthoringPrivate
{
	using namespace RoadBLDToolset;

	constexpr int32 MaxRoadsPerCall = 400;

	/** New roads sit this far above the given ground height, matching RoadBLD's draw tool, so displaced ground stays below the surface. */
	constexpr double GroundClearance = 5.0;

	/** Corners sharper than this cannot be rounded into a usable road. */
	constexpr double MaxCornerTurnAngle = 150.0;

	/** Turn radius used when authoring tools close corners automatically (CloseCorner's default). */
	constexpr double DefaultCornerTurnRadius = 3000.0;

	TArray<FRoadBLDPoint> LiftAboveGround(TArray<FRoadBLDPoint> Points)
	{
		for (FRoadBLDPoint& Point : Points)
		{
			Point.Location.Z += GroundClearance;
		}
		return Points;
	}

	UDynamicRoadDrawPreset* GetPresetObject(const TSubclassOf<UDynamicRoadDrawPreset>& Preset)
	{
		return Preset ? Preset.GetDefaultObject() : nullptr;
	}

	FString GetRoadName(const ADynamicRoad* Road)
	{
		return Road->GetActorLabel().IsEmpty() ? Road->GetName() : Road->GetActorLabel();
	}

	const TCHAR* EndName(const bool bStart)
	{
		return bStart ? TEXT("start") : TEXT("end");
	}

	FVector2D GetTurnRadiusLimit()
	{
		return FVector2D(GetDefault<URoadControlSplineComponent>()->TurnRadiusLimit);
	}

	bool SetRoadPoints(ADynamicRoad* Road, const TArray<FRoadBLDPoint>& Points, FString& OutError)
	{
		TArray<FRoadSplineAuthoringPoint> AuthoringPoints;
		AuthoringPoints.Reserve(Points.Num());
		for (const FRoadBLDPoint& Point : Points)
		{
			FRoadSplineAuthoringPoint& AuthoringPoint = AuthoringPoints.AddDefaulted_GetRef();
			AuthoringPoint.WorldPosition = Point.Location;
			AuthoringPoint.MaxRadius = Point.TurnRadius;
		}
		return Road->ReplaceControlSplineFromAuthoringPoints(AuthoringPoints, OutError);
	}

	/** The road's control points as SetRoadPoints takes them (Z is the road surface). */
	TArray<FRoadBLDPoint> GetRoadPoints(const ADynamicRoad* Road)
	{
		TArray<FRoadBLDPoint> Points;
		if (!IsValid(Road) || !IsValid(Road->ControlSpline))
		{
			return Points;
		}

		for (int32 Index = 0; Index < Road->ControlSpline->GetNumberOfSplinePoints(); ++Index)
		{
			FRoadBLDPoint& Point = Points.AddDefaulted_GetRef();
			Point.Location = Road->ControlSpline->GetLocationAtSplinePoint(Index, ESplineCoordinateSpace::World);
			Road->GetPointTurnRadius(Index, Point.TurnRadius);
		}
		return Points;
	}

	/** Replaces a road's points while keeping the links of the given ends (their positions must not change). */
	bool ReshapeKeepingLinks(ADynamicRoad* Road, const TArray<FRoadBLDPoint>& Points, const TArray<bool>& EndsToKeep, FString& OutError)
	{
		TArray<TPair<bool, FRoadEndpointLink>> Saved;
		for (const bool bStart : EndsToKeep)
		{
			if (const TArray<FRoadEndpointLink>* Links = Road->GetEndpointLinks(bStart))
			{
				for (const FRoadEndpointLink& Link : *Links)
				{
					Saved.Emplace(bStart, Link);
				}
			}
		}

		Road->ClearEndpointLinks(true);
		Road->ClearEndpointLinks(false);
		const bool bSucceeded = SetRoadPoints(Road, Points, OutError);
		for (const TPair<bool, FRoadEndpointLink>& Link : Saved)
		{
			Road->AddEndpointLink(Link.Key, Link.Value);
		}
		return bSucceeded;
	}

	void ApplyPresetToRoad(ADynamicRoad* Road, UDynamicRoadDrawPreset* Preset, const bool bKeepSidewalkOverrides)
	{
		if (!bKeepSidewalkOverrides)
		{
			Road->LeftSidewalkPreset = nullptr;
			Road->RightSidewalkPreset = nullptr;
		}

		// Same mapping ADynamicRoadNetwork::AddRoadToRoadNetwork applies to new roads.
		switch (Preset->Category)
		{
		case ERoadPresetCategory::Walkway:
			Road->RoadType = ERoadType::Walkway;
			break;
		case ERoadPresetCategory::Railway:
			Road->RoadType = ERoadType::Railway;
			break;
		case ERoadPresetCategory::Other:
			Road->RoadType = ERoadType::Other;
			break;
		default:
			Road->RoadType = ERoadType::Normal;
			break;
		}

		Road->InitializeRoad(Preset, Preset->ElementEdgeZOffset);
		Road->CalculateRefLine();
	}

	/**
	 * One undoable authoring action on top of RoadBLD's edit scope. Failing removes spawned roads again and, when
	 * existing roads were already changed, undoes the transaction so they are restored too.
	 */
	class FAuthoringAction
	{
	public:
		explicit FAuthoringAction(const TCHAR* Name)
			: Scope(FText::FromString(FString::Printf(TEXT("RoadBLD Toolset: %s"), Name)))
			, UndoCountBefore(UToolsetLibrary::GetActiveUndoCount())
		{
		}

		TArray<FString> Warnings;

		bool Failed() const
		{
			return bDenied || Scope.WasCancelled();
		}

		/** Register networks before Begin so pending rebuilds on them are aborted first. */
		void AddNetwork(ADynamicRoadNetwork* Network)
		{
			if (IsValid(Network))
			{
				Scope.AddAffectedNetwork(Network);
				Networks.AddUnique(Network);
			}
		}

		/** Checks access and opens the transaction. On false an error was raised; return without editing. */
		bool Begin()
		{
			if (!EnsureAuthorized())
			{
				bDenied = true;
				return false;
			}

			Scope.Begin();
			if (Scope.WasCancelled())
			{
				bDenied = true;
				RaiseError(Scope.GetCancelReason().IsEmpty()
					? FString(TEXT("RoadBLD edits are blocked."))
					: Scope.GetCancelReason().ToString());
				return false;
			}

			if (UWorld* World = GetEditorWorld())
			{
				if (ULevel* Level = World->GetCurrentLevel())
				{
					Scope.ModifyObject(Level);
				}
			}
			return true;
		}

		/** Resolves the target network, registers it and begins. Spawns a network when the level has none. */
		ADynamicRoadNetwork* BeginOnNetwork(ADynamicRoadNetwork* Requested, FString& OutError)
		{
			const bool bSpawnNetwork = !IsValid(Requested) && GetNetworks().Num() == 0;
			ADynamicRoadNetwork* Network = nullptr;
			if (!bSpawnNetwork)
			{
				bool bCreated = false;
				Network = ResolveNetwork(Requested, false, bCreated, OutError);
				if (!Network)
				{
					return nullptr;
				}
				AddNetwork(Network);
			}

			if (!Begin())
			{
				return nullptr;
			}

			if (bSpawnNetwork)
			{
				Network = SpawnNetwork(TEXT("RoadNetwork"), OutError);
				if (!Network)
				{
					return nullptr;
				}
				Scope.TrackSpawnedActor(Network);
				AddNetwork(Network);
			}

			return Network;
		}

		void ModifyRoad(ADynamicRoad* Road)
		{
			if (!IsValid(Road))
			{
				return;
			}

			if (!SpawnedRoads.Contains(Road))
			{
				bModifiedExisting = true;
			}

			Scope.AddAffectedRoad(Road);
			Scope.ModifyObject(Road);
			if (IsValid(Road->ControlSpline))
			{
				Scope.ModifyObject(Road->ControlSpline);
				if (UObject* Metadata = Road->ControlSpline->GetSplinePointsMetadata())
				{
					Scope.ModifyObject(Metadata);
				}
			}

			TouchedRoads.AddUnique(Road);
			AddNetwork(GetOwningNetwork(Road));
		}

		void ModifyObject(UObject* Object)
		{
			bModifiedExisting = true;
			Scope.ModifyObject(Object);
		}

		void TrackSpawnedRoad(ADynamicRoad* Road)
		{
			SpawnedRoads.Add(Road);
			Scope.TrackSpawnedActor(Road);
			ModifyRoad(Road);
		}

		/** Removes a road from its network and destroys it. Call ModifyRoad on it and its linked roads first. */
		void DeleteRoad(ADynamicRoad* Road)
		{
			Road->RemoveReciprocalLinksFromLinkedRoads();
			if (ADynamicRoadNetwork* Network = GetOwningNetwork(Road))
			{
				Network->RoadsInNetwork.Remove(Road);
				Scope.TrackDeletedRoadID(Network, Road->RoadID);
			}
			TouchedRoads.Remove(Road);
			bModifiedExisting = true;
			bDeletedRoads = true;
			Road->GetWorld()->EditorDestroyActor(Road, true);
		}

		ADynamicRoad* SpawnRoad(
			ADynamicRoadNetwork* Network,
			UDynamicRoadDrawPreset* Preset,
			const TArray<FRoadBLDPoint>& Points,
			const FString& Label,
			FString& OutError,
			const bool bSnapEndpoints = true)
		{
			if (SpawnedRoads.Num() >= MaxRoadsPerCall)
			{
				OutError = FString::Printf(TEXT("A single call can create at most %d roads."), MaxRoadsPerCall);
				return nullptr;
			}

			ADynamicRoad* Road = Network->AddRoadToRoadNetwork(Preset, 0.0);
			if (!IsValid(Road))
			{
				OutError = TEXT("RoadBLD failed to spawn a road.");
				return nullptr;
			}

			TrackSpawnedRoad(Road);
			if (!Label.IsEmpty())
			{
				Road->SetActorLabel(Label);
			}

			TArray<FRoadBLDPoint> FinalPoints = Points;
			if (bSnapEndpoints)
			{
				SnapEndpointsToJunctions(Network, Road, FinalPoints);
			}

			if (FinalPoints.Num() > 0 && !SetRoadPoints(Road, FinalPoints, OutError))
			{
				OutError = FString::Printf(TEXT("%s: %s"), Label.IsEmpty() ? TEXT("Road") : *Label, *OutError);
				return nullptr;
			}

			return Road;
		}

		/** Moves road ends that would form a too-short junction arm onto the centerline of the road they meet. */
		void SnapEndpointsToJunctions(ADynamicRoadNetwork* Network, const ADynamicRoad* Road, TArray<FRoadBLDPoint>& Points)
		{
			if (Points.Num() < 2)
			{
				return;
			}

			const double Width = GetRoadSideWidth(Road, ERoadSide::Left, 0.0) + GetRoadSideWidth(Road, ERoadSide::Right, 0.0);
			for (const bool bStart : { true, false })
			{
				const int32 EndIndex = bStart ? 0 : Points.Num() - 1;
				const int32 NeighborIndex = bStart ? 1 : Points.Num() - 2;
				FJunctionStub Stub;
				if (!FindJunctionStub(Network, Road, Points[EndIndex].Location, Points[NeighborIndex].Location, Width, Stub))
				{
					continue;
				}

				Points[EndIndex].Location = Stub.SnappedLocation;
				if (Stub.MoveDistance < 10.0)
				{
					continue;
				}

				const FString WasWhere = Stub.EdgeDistance < 0.0
					? FString(TEXT("inside the road"))
					: FString::Printf(TEXT("%.0f cm %s the road edge"), Stub.EdgeDistance, Stub.bPastCenterline ? TEXT("past") : TEXT("short of"));
				Warnings.Add(FString::Printf(
					TEXT("%s: %s moved %.0f cm onto the centerline of %s (it ended %s, which RoadBLD cannot build as a junction). For a crossing instead, end it at least %.0f cm past the far edge."),
					*GetRoadName(Road),
					EndName(bStart),
					Stub.MoveDistance,
					*Stub.OtherRoad->GetActorLabel(),
					*WasWhere,
					FMath::Max(JunctionMinCrossArm, Width)));
			}
		}

		void CheckShape(ADynamicRoad* Road)
		{
			FText FailureReason;
			if (IsValid(Road) && !URoadEditorFunctionLibrary::CheckRoadShapeValidity(Road, FailureReason))
			{
				Warnings.Add(FString::Printf(TEXT("%s: %s"), *Road->GetActorLabel(), *FailureReason.ToString()));
			}
		}

		void Fail()
		{
			if (bDenied)
			{
				Scope.Cancel();
				return;
			}

			for (const TWeakObjectPtr<ADynamicRoad>& WeakRoad : SpawnedRoads)
			{
				ADynamicRoad* Road = WeakRoad.Get();
				if (!IsValid(Road))
				{
					continue;
				}

				Road->RemoveReciprocalLinksFromLinkedRoads();
				for (const TWeakObjectPtr<ADynamicRoadNetwork>& WeakNetwork : Networks)
				{
					if (ADynamicRoadNetwork* Network = WeakNetwork.Get())
					{
						Network->RoadsInNetwork.Remove(Road);
					}
				}
			}

			if (!bModifiedExisting)
			{
				Scope.Cancel();
				return;
			}

			// Cancelling only discards the transaction record; changes to existing roads would stay. Close the
			// transaction and undo it instead, but only when it is the newest record, so nothing else is undone.
			Scope.Complete();
			if (UToolsetLibrary::GetActiveUndoCount() == UndoCountBefore + 1)
			{
				UToolsetLibrary::UndoTransaction(false);
			}
			else
			{
				Warnings.Add(TEXT("The failed edit could not be rolled back automatically; use Edit > Undo."));
			}
		}

		FRoadBLDEditResult Complete(ADynamicRoadNetwork* ResultNetwork, const TArray<ADynamicRoad*>& ResultRoads, const bool bRebuild, const bool bFullRebuild)
		{
			if (bDenied || Scope.WasCancelled())
			{
				return FRoadBLDEditResult();
			}

			Scope.Complete();

			FRoadBLDEditResult Result;
			Result.Network = MakeActorRef(ResultNetwork);
			for (ADynamicRoad* Road : ResultRoads)
			{
				if (IsValid(Road))
				{
					Result.Roads.Add(MakeActorRef(Road));
				}
			}
			Result.Warnings = MoveTemp(Warnings);

			TArray<ADynamicRoadNetwork*> AffectedNetworks;
			for (const TWeakObjectPtr<ADynamicRoadNetwork>& WeakNetwork : Networks)
			{
				if (ADynamicRoadNetwork* Network = WeakNetwork.Get())
				{
					Network->MarkRoadNetworkStale();
					AffectedNetworks.Add(Network);
				}
			}

			if (bRebuild && AffectedNetworks.Num() > 0)
			{
				TMap<ADynamicRoadNetwork*, TArray<ADynamicRoad*>> RoadsByNetwork;
				if (!bFullRebuild && !bDeletedRoads)
				{
					for (const TWeakObjectPtr<ADynamicRoad>& WeakRoad : TouchedRoads)
					{
						ADynamicRoad* Road = WeakRoad.Get();
						if (ADynamicRoadNetwork* Network = GetOwningNetwork(Road))
						{
							RoadsByNetwork.FindOrAdd(Network).AddUnique(Road);
						}
					}
				}

				const FGuid JobId = FRoadBLDRebuildJobs::Get().Start(AffectedNetworks, RoadsByNetwork, false, false);
				Result.RebuildJobId = JobId.ToString(EGuidFormats::DigitsWithHyphensLower);
				Result.bNeedsRebuild = false;
			}

			return Result;
		}

	private:
		FRoadEditActionScope Scope;
		int32 UndoCountBefore = 0;
		TArray<TWeakObjectPtr<ADynamicRoadNetwork>> Networks;
		TArray<TWeakObjectPtr<ADynamicRoad>> SpawnedRoads;
		TArray<TWeakObjectPtr<ADynamicRoad>> TouchedRoads;
		bool bDenied = false;
		bool bModifiedExisting = false;
		bool bDeletedRoads = false;
	};

	FRoadBLDEditResult FailWith(FAuthoringAction& Action, const FString& Error)
	{
		Action.Fail();
		if (!Error.IsEmpty())
		{
			RaiseError(Error);
		}
		return FRoadBLDEditResult();
	}

	/** Spawns a closed loop as two roads split at SplitA (on edge EdgeA) and SplitB (on edge EdgeB > EdgeA), linked end to end. */
	bool SpawnLoop(
		FAuthoringAction& Action,
		ADynamicRoadNetwork* Network,
		UDynamicRoadDrawPreset* Preset,
		const TArray<FVector>& Polygon,
		const double CornerRadius,
		const int32 EdgeA,
		const FVector& SplitA,
		const int32 EdgeB,
		const FVector& SplitB,
		const FString& Prefix,
		TArray<ADynamicRoad*>& OutRoads,
		FString& OutError)
	{
		const int32 VertexCount = Polygon.Num();
		auto MakePoint = [CornerRadius](const FVector& Location)
		{
			FRoadBLDPoint Point;
			Point.Location = Location;
			Point.TurnRadius = CornerRadius;
			return Point;
		};

		TArray<FRoadBLDPoint> PointsA;
		PointsA.Add(MakePoint(SplitA));
		for (int32 Index = EdgeA + 1; Index <= EdgeB; ++Index)
		{
			PointsA.Add(MakePoint(Polygon[Index]));
		}
		PointsA.Add(MakePoint(SplitB));

		TArray<FRoadBLDPoint> PointsB;
		PointsB.Add(MakePoint(SplitB));
		for (int32 Index = EdgeB + 1; Index < VertexCount + EdgeA + 1; ++Index)
		{
			PointsB.Add(MakePoint(Polygon[Index % VertexCount]));
		}
		PointsB.Add(MakePoint(SplitA));

		ADynamicRoad* RoadA = Action.SpawnRoad(Network, Preset, PointsA, Prefix + TEXT("_A"), OutError, false);
		ADynamicRoad* RoadB = RoadA ? Action.SpawnRoad(Network, Preset, PointsB, Prefix + TEXT("_B"), OutError, false) : nullptr;
		if (!RoadA || !RoadB)
		{
			return false;
		}

		if (!CreateReciprocalLink(RoadA, false, RoadB, true) || !CreateReciprocalLink(RoadB, false, RoadA, true))
		{
			OutError = FString::Printf(TEXT("Failed to link the two halves of %s."), *Prefix);
			return false;
		}

		Action.CheckShape(RoadA);
		Action.CheckShape(RoadB);
		OutRoads.Add(RoadA);
		OutRoads.Add(RoadB);
		return true;
	}

	void AutoLinkEndpoints(FAuthoringAction& Action, ADynamicRoad* Road, ADynamicRoadNetwork* Network, const double Tolerance)
	{
		for (const bool bStart : { true, false })
		{
			FVector Location;
			if (CountEndpointLinks(Road, bStart) > 0 || !GetEndpointLocation(Road, bStart, Location))
			{
				continue;
			}

			ADynamicRoad* OtherRoad = nullptr;
			bool bOtherStart = true;
			if (!FindUnlinkedEndpointNear(Network, Location, Tolerance, Road, OtherRoad, bOtherStart))
			{
				continue;
			}

			// Links only describe straight continuations; corners are reported separately.
			EEndpointMeeting Meeting = EEndpointMeeting::Corner;
			double TurnAngle = 0.0;
			if (!ClassifyEndpointMeeting(Road, bStart, OtherRoad, bOtherStart, Meeting, TurnAngle) || Meeting != EEndpointMeeting::Continuation)
			{
				continue;
			}

			Action.ModifyRoad(OtherRoad);
			if (!CreateReciprocalLink(Road, bStart, OtherRoad, bOtherStart))
			{
				Action.Warnings.Add(FString::Printf(TEXT("Could not link %s to %s."), *Road->GetActorLabel(), *OtherRoad->GetActorLabel()));
			}
		}
	}

	/** A validated corner between two road ends, ready for ApplyCorner. */
	struct FCornerPlan
	{
		ADynamicRoad* RoadA = nullptr;
		bool bAStart = true;
		ADynamicRoad* RoadB = nullptr;
		bool bBStart = true;
		ADynamicRoadNetwork* Network = nullptr;
		double TurnRadius = 3000.0;
		double TurnAngle = 0.0;
		bool bSamePreset = false;
		TArray<FRoadBLDPoint> PointsA;
		TArray<FRoadBLDPoint> PointsB;
	};

	/** Distance from a road end to its neighbouring control point along the XY plane. */
	double GetEndSegmentLength(const TArray<FRoadBLDPoint>& Points, const bool bStart)
	{
		const int32 End = bStart ? 0 : Points.Num() - 1;
		const int32 Neighbor = bStart ? 1 : Points.Num() - 2;
		return FVector::Dist2D(Points[End].Location, Points[Neighbor].Location);
	}

	/** Checks everything CloseCorner needs before any road is touched. */
	bool PlanCorner(
		ADynamicRoad* RoadA,
		const bool bAStart,
		ADynamicRoad* RoadB,
		const bool bBStart,
		const double TurnRadius,
		FCornerPlan& OutPlan,
		FString& OutError)
	{
		if (!IsValid(RoadA) || !IsValid(RoadB) || RoadA == RoadB)
		{
			OutError = TEXT("A and B must be two different valid roads.");
			return false;
		}

		OutPlan.Network = GetOwningNetwork(RoadA);
		if (!OutPlan.Network || OutPlan.Network != GetOwningNetwork(RoadB))
		{
			OutError = TEXT("Both roads must belong to the same road network.");
			return false;
		}

		const FVector2D RadiusLimit = GetTurnRadiusLimit();
		if (!FMath::IsFinite(TurnRadius) || TurnRadius < RadiusLimit.X || TurnRadius > RadiusLimit.Y)
		{
			OutError = FString::Printf(TEXT("TurnRadius must be between %.0f and %.0f cm."), RadiusLimit.X, RadiusLimit.Y);
			return false;
		}

		OutPlan.PointsA = GetRoadPoints(RoadA);
		OutPlan.PointsB = GetRoadPoints(RoadB);
		FVector LocationA;
		FVector LocationB;
		if (OutPlan.PointsA.Num() < 2 || OutPlan.PointsB.Num() < 2
			|| !GetEndpointLocation(RoadA, bAStart, LocationA) || !GetEndpointLocation(RoadB, bBStart, LocationB))
		{
			OutError = TEXT("Both roads need at least two control points.");
			return false;
		}

		const double Gap = FVector::Dist2D(LocationA, LocationB);
		if (Gap > EndpointMeetTolerance)
		{
			OutError = FString::Printf(
				TEXT("%s's %s and %s's %s are %.0f cm apart; CloseCorner needs ends within %.0f cm. Move one with SetControlPoints, or use ConnectEndpoints Mode=Bridge."),
				*GetRoadName(RoadA), EndName(bAStart), *GetRoadName(RoadB), EndName(bBStart), Gap, EndpointMeetTolerance);
			return false;
		}

		EEndpointMeeting Meeting = EEndpointMeeting::Continuation;
		if (!ClassifyEndpointMeeting(RoadA, bAStart, RoadB, bBStart, Meeting, OutPlan.TurnAngle))
		{
			OutError = TEXT("Could not determine the road directions at the corner.");
			return false;
		}
		if (Meeting == EEndpointMeeting::Continuation)
		{
			OutError = FString::Printf(
				TEXT("The ends continue straight (%.0f degree turn); link them with ConnectEndpoints Mode=Link instead."), OutPlan.TurnAngle);
			return false;
		}
		if (OutPlan.TurnAngle > MaxCornerTurnAngle)
		{
			OutError = FString::Printf(
				TEXT("The roads turn back on each other (%.0f degrees); a corner can turn at most %.0f degrees. Redraw them."),
				OutPlan.TurnAngle, MaxCornerTurnAngle);
			return false;
		}

		for (const TPair<ADynamicRoad*, bool>& End : { TPair<ADynamicRoad*, bool>(RoadA, bAStart), TPair<ADynamicRoad*, bool>(RoadB, bBStart) })
		{
			const ADynamicRoad* Partner = End.Key == RoadA ? RoadB : RoadA;
			const bool bPartnerStart = End.Key == RoadA ? bBStart : bAStart;
			if (const TArray<FRoadEndpointLink>* Links = End.Key->GetEndpointLinks(End.Value))
			{
				for (const FRoadEndpointLink& Link : *Links)
				{
					if (Link.LinkedRoad.Get() != Partner || Link.bLinkedToFirstPoint != bPartnerStart)
					{
						OutError = FString::Printf(TEXT("%s's %s is also linked to %s. Remove that road or link first."),
							*GetRoadName(End.Key), EndName(End.Value), Link.LinkedRoad.Get() ? *GetRoadName(Link.LinkedRoad.Get()) : TEXT("another road"));
						return false;
					}
				}
			}
		}

		const UDynamicRoadDrawPreset* PresetA = RoadA->SourceDrawPreset.Get();
		const UDynamicRoadDrawPreset* PresetB = RoadB->SourceDrawPreset.Get();
		OutPlan.bSamePreset = PresetA && PresetB && PresetA->GetClass() == PresetB->GetClass();
		if (!PresetA)
		{
			OutError = FString::Printf(TEXT("%s has no preset."), *GetRoadName(RoadA));
			return false;
		}

		if (!OutPlan.bSamePreset)
		{
			// The connector starts where the corner fillet would: TurnRadius * tan(turn / 2) back along each road.
			const double PullBack = TurnRadius * FMath::Tan(FMath::DegreesToRadians(OutPlan.TurnAngle) * 0.5);
			const double Shortest = FMath::Min(GetEndSegmentLength(OutPlan.PointsA, bAStart), GetEndSegmentLength(OutPlan.PointsB, bBStart));
			if (PullBack > Shortest - 100.0)
			{
				OutError = FString::Printf(
					TEXT("The last segment of each road must be longer than %.0f cm for a %.0f cm turn radius (shortest is %.0f cm). Use a smaller TurnRadius."),
					PullBack + 100.0, TurnRadius, Shortest);
				return false;
			}
		}

		OutPlan.RoadA = RoadA;
		OutPlan.bAStart = bAStart;
		OutPlan.RoadB = RoadB;
		OutPlan.bBStart = bBStart;
		OutPlan.TurnRadius = TurnRadius;
		return true;
	}

	/** Merges B into A through the corner and deletes B. */
	bool MergeCorner(FAuthoringAction& Action, const FCornerPlan& Plan, FString& OutError)
	{
		ADynamicRoad* RoadA = Plan.RoadA;
		ADynamicRoad* RoadB = Plan.RoadB;

		// Orient A to end at the corner and B to start there, then restore A's own direction.
		TArray<FRoadBLDPoint> PointsA = Plan.PointsA;
		TArray<FRoadBLDPoint> PointsB = Plan.PointsB;
		if (Plan.bAStart)
		{
			Algo::Reverse(PointsA);
		}
		if (!Plan.bBStart)
		{
			Algo::Reverse(PointsB);
		}

		FRoadBLDPoint Corner;
		Corner.Location = (PointsA.Last().Location + PointsB[0].Location) * 0.5;
		Corner.TurnRadius = Plan.TurnRadius;

		TArray<FRoadBLDPoint> Merged(PointsA.GetData(), PointsA.Num() - 1);
		Merged.Add(Corner);
		Merged.Append(PointsB.GetData() + 1, PointsB.Num() - 1);
		if (Plan.bAStart)
		{
			Algo::Reverse(Merged);
		}

		// B's far end becomes the end of A that used to be at the corner.
		const bool bBFarStart = !Plan.bBStart;
		const bool bNewEndIsStart = Plan.bAStart;
		TArray<FRoadEndpointLink> FarLinks;
		if (const TArray<FRoadEndpointLink>* Links = RoadB->GetEndpointLinks(bBFarStart))
		{
			FarLinks = *Links;
		}
		for (const FRoadEndpointLink& Link : FarLinks)
		{
			if (ADynamicRoad* Partner = Link.LinkedRoad.Get())
			{
				Action.ModifyRoad(Partner);
				Partner->RemoveEndpointLink(Link.bLinkedToFirstPoint, RoadB, bBFarStart);
			}
		}
		RoadB->ClearEndpointLinks(true);
		RoadB->ClearEndpointLinks(false);

		// Only A's far end keeps its links; the corner end is gone after the merge.
		if (!ReshapeKeepingLinks(RoadA, Merged, { !Plan.bAStart }, OutError))
		{
			OutError = FString::Printf(TEXT("%s: %s"), *GetRoadName(RoadA), *OutError);
			return false;
		}

		for (const FRoadEndpointLink& Link : FarLinks)
		{
			ADynamicRoad* Partner = Link.LinkedRoad.Get();
			if (IsValid(Partner) && !CreateReciprocalLink(RoadA, bNewEndIsStart, Partner, Link.bLinkedToFirstPoint))
			{
				Action.Warnings.Add(FString::Printf(TEXT("Could not move %s's link to %s onto %s."), *GetRoadName(RoadB), *GetRoadName(Partner), *GetRoadName(RoadA)));
			}
		}

		Action.Warnings.Add(FString::Printf(
			TEXT("Merged %s into %s through a %.0f cm corner; %s was deleted (its per-road lane and sidewalk edits are not carried over)."),
			*GetRoadName(RoadB), *GetRoadName(RoadA), Plan.TurnRadius, *GetRoadName(RoadB)));
		Action.DeleteRoad(RoadB);
		Action.CheckShape(RoadA);
		return true;
	}

	/** Pulls both ends back from the corner and joins them with a curved, linked connector road. */
	ADynamicRoad* BridgeCorner(FAuthoringAction& Action, const FCornerPlan& Plan, FString& OutError)
	{
		const double PullBack = Plan.TurnRadius * FMath::Tan(FMath::DegreesToRadians(Plan.TurnAngle) * 0.5);
		auto PullEnd = [PullBack](TArray<FRoadBLDPoint>& Points, const bool bStart)
		{
			FRoadBLDPoint& End = Points[bStart ? 0 : Points.Num() - 1];
			const FVector& Neighbor = Points[bStart ? 1 : Points.Num() - 2].Location;
			const FVector Toward = Neighbor - End.Location;
			End.Location += Toward * (PullBack / FMath::Max(Toward.Size2D(), UE_SMALL_NUMBER));
			return End.Location;
		};

		TArray<FRoadBLDPoint> PointsA = Plan.PointsA;
		TArray<FRoadBLDPoint> PointsB = Plan.PointsB;
		FRoadBLDPoint Corner;
		Corner.Location = (PointsA[Plan.bAStart ? 0 : PointsA.Num() - 1].Location + PointsB[Plan.bBStart ? 0 : PointsB.Num() - 1].Location) * 0.5;
		Corner.TurnRadius = Plan.TurnRadius;

		FRoadBLDPoint ConnectorStart;
		ConnectorStart.Location = PullEnd(PointsA, Plan.bAStart);
		FRoadBLDPoint ConnectorEnd;
		ConnectorEnd.Location = PullEnd(PointsB, Plan.bBStart);

		// Reshaping keeps only the far-end links, which drops any link between the two corner ends.
		if (!ReshapeKeepingLinks(Plan.RoadA, PointsA, { !Plan.bAStart }, OutError)
			|| !ReshapeKeepingLinks(Plan.RoadB, PointsB, { !Plan.bBStart }, OutError))
		{
			return nullptr;
		}

		ADynamicRoad* Connector = Action.SpawnRoad(
			Plan.Network, Plan.RoadA->SourceDrawPreset.Get(), { ConnectorStart, Corner, ConnectorEnd },
			FString::Printf(TEXT("%s_Corner"), *GetRoadName(Plan.RoadA)), OutError, false);
		if (!Connector)
		{
			return nullptr;
		}

		if (!CreateReciprocalLink(Connector, true, Plan.RoadA, Plan.bAStart) || !CreateReciprocalLink(Connector, false, Plan.RoadB, Plan.bBStart))
		{
			OutError = TEXT("RoadBLD rejected the corner connector links.");
			return nullptr;
		}

		Action.Warnings.Add(FString::Printf(
			TEXT("%s and %s use different presets, so they were pulled back %.0f cm and joined by %s (preset of %s). The lane layout changes where it links to %s."),
			*GetRoadName(Plan.RoadA), *GetRoadName(Plan.RoadB), PullBack, *GetRoadName(Connector), *GetRoadName(Plan.RoadA), *GetRoadName(Plan.RoadB)));
		Action.CheckShape(Plan.RoadA);
		Action.CheckShape(Plan.RoadB);
		Action.CheckShape(Connector);
		return Connector;
	}

	/** Applies a planned corner. Adds any connector road to OutRoads. */
	bool ApplyCorner(FAuthoringAction& Action, const FCornerPlan& Plan, TArray<ADynamicRoad*>& OutRoads, FString& OutError)
	{
		Action.ModifyRoad(Plan.RoadA);
		Action.ModifyRoad(Plan.RoadB);
		if (Plan.bSamePreset)
		{
			return MergeCorner(Action, Plan, OutError);
		}

		ADynamicRoad* Connector = BridgeCorner(Action, Plan, OutError);
		if (Connector)
		{
			OutRoads.AddUnique(Connector);
		}
		return Connector != nullptr;
	}

	/**
	 * Handles ends of Road that meet another unlinked road end at an angle: closes them when bCloseCorners is set
	 * (Road is kept) and reports them otherwise. Returns false only when closing failed after roads were changed.
	 */
	bool HandleCorners(FAuthoringAction& Action, ADynamicRoad* Road, const bool bCloseCorners, TArray<ADynamicRoad*>& OutRoads, FString& OutError)
	{
		for (const bool bStart : { true, false })
		{
			// Closing the first corner can reshape Road, so look up each end's corners afresh.
			const TArray<FEndpointCorner> Corners = FindCornersAtEnd(GetOwningNetwork(Road), Road, bStart);
			const FEndpointCorner* Corner = Corners.FindByPredicate([](const FEndpointCorner& Candidate) { return !Candidate.bLinked; });
			if (!Corner)
			{
				continue;
			}

			const FString Description = FString::Printf(TEXT("%s's %s meets %s's %s at a %.0f degree turn"),
				*GetRoadName(Road), EndName(bStart), *GetRoadName(Corner->OtherRoad), EndName(Corner->bOtherStart), Corner->TurnAngle);
			if (!bCloseCorners)
			{
				Action.Warnings.Add(FString::Printf(
					TEXT("%s. Unjoined corners build stretched triangles: call CloseCorner, set bCloseCorners=true, or draw one road through the corner."),
					*Description));
				continue;
			}

			FCornerPlan Plan;
			FString PlanError;
			if (!PlanCorner(Road, bStart, Corner->OtherRoad, Corner->bOtherStart, DefaultCornerTurnRadius, Plan, PlanError))
			{
				Action.Warnings.Add(FString::Printf(TEXT("%s and was not closed: %s"), *Description, *PlanError));
				continue;
			}

			if (!ApplyCorner(Action, Plan, OutRoads, OutError))
			{
				return false;
			}
		}
		return true;
	}
}

FRoadBLDActorRef URoadBLDAuthoringToolset::CreateNetwork(const FString& Label)
{
	using namespace RoadBLDAuthoringPrivate;

	FAuthoringAction Action(TEXT("Create Road Network"));
	if (!Action.Begin())
	{
		return FRoadBLDActorRef();
	}

	FString Error;
	ADynamicRoadNetwork* Network = SpawnNetwork(Label, Error);
	if (!Network)
	{
		FailWith(Action, Error);
		return FRoadBLDActorRef();
	}

	Action.Complete(Network, {}, false, false);
	return MakeActorRef(Network);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::CreateRoad(
	TSubclassOf<UDynamicRoadDrawPreset> Preset,
	const TArray<FRoadBLDPoint>& Points,
	ADynamicRoadNetwork* Network,
	const FString& Label,
	const bool bAutoLinkEndpoints,
	const double LinkTolerance,
	const bool bConformToLandscape,
	const bool bSnapEndpointsToJunctions,
	const bool bCloseCorners,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	UDynamicRoadDrawPreset* PresetObject = GetPresetObject(Preset);
	if (!PresetObject)
	{
		RaiseError(TEXT("Preset is required. Use an Id from ListPresets."));
		return FRoadBLDEditResult();
	}

	if (Points.Num() < 2)
	{
		RaiseError(TEXT("A road needs at least two points."));
		return FRoadBLDEditResult();
	}

	FAuthoringAction Action(TEXT("Create Road"));
	FString Error;
	ADynamicRoadNetwork* TargetNetwork = Action.BeginOnNetwork(Network, Error);
	if (!TargetNetwork)
	{
		return FailWith(Action, Error);
	}

	ADynamicRoad* Road = Action.SpawnRoad(TargetNetwork, PresetObject, LiftAboveGround(Points), GetOptionalString(Label, TEXT("Auto")), Error, bSnapEndpointsToJunctions);
	if (!Road)
	{
		return FailWith(Action, Error);
	}

	if (bConformToLandscape)
	{
		Road->bConformToLandscape = true;
		Road->CalculateRefLine();
	}

	Action.CheckShape(Road);
	if (bAutoLinkEndpoints)
	{
		AutoLinkEndpoints(Action, Road, TargetNetwork, LinkTolerance);
	}

	TArray<ADynamicRoad*> Roads = { Road };
	if (!HandleCorners(Action, Road, bCloseCorners, Roads, Error))
	{
		return FailWith(Action, Error);
	}

	return Action.Complete(TargetNetwork, Roads, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::CreateGrid(
	TSubclassOf<UDynamicRoadDrawPreset> Preset,
	const FRoadBLDGridSpec& Grid,
	TSubclassOf<UDynamicRoadDrawPreset> ArterialPreset,
	ADynamicRoadNetwork* Network,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	UDynamicRoadDrawPreset* PresetObject = GetPresetObject(Preset);
	UDynamicRoadDrawPreset* ArterialObject = GetPresetObject(ArterialPreset);
	if (!PresetObject)
	{
		RaiseError(TEXT("Preset is required. Use an Id from ListPresets."));
		return FRoadBLDEditResult();
	}

	if (Grid.SizeX <= 0.0 || Grid.SizeY <= 0.0 || Grid.SpacingX <= 0.0 || Grid.SpacingY <= 0.0)
	{
		RaiseError(TEXT("Grid sizes and spacings must be positive."));
		return FRoadBLDEditResult();
	}

	const FVector2D RadiusLimit = GetTurnRadiusLimit();
	if (Grid.bIncludePerimeter && (Grid.PerimeterCornerRadius < RadiusLimit.X || Grid.PerimeterCornerRadius > RadiusLimit.Y))
	{
		RaiseError(FString::Printf(TEXT("PerimeterCornerRadius must be between %.0f and %.0f cm."), RadiusLimit.X, RadiusLimit.Y));
		return FRoadBLDEditResult();
	}

	// Interior line positions; the perimeter is a separate loop.
	auto BuildLinePositions = [](const double Size, const double Spacing)
	{
		TArray<double> Positions;
		const int32 Count = FMath::FloorToInt32(Size / Spacing + KINDA_SMALL_NUMBER);
		for (int32 Index = 1; Index <= Count && Index <= MaxRoadsPerCall; ++Index)
		{
			const double Position = Index * Spacing;
			if (Position < Size - 1.0)
			{
				Positions.Add(Position);
			}
		}
		return Positions;
	};

	// Roads parallel to local Y sit at these X positions, and vice versa.
	const TArray<double> XPositions = BuildLinePositions(Grid.SizeX, Grid.SpacingX);
	const TArray<double> YPositions = BuildLinePositions(Grid.SizeY, Grid.SpacingY);
	const int32 RoadCount = XPositions.Num() + YPositions.Num() + (Grid.bIncludePerimeter ? 2 : 0);
	if (RoadCount > MaxRoadsPerCall)
	{
		RaiseError(FString::Printf(TEXT("The grid needs %d roads; the limit per call is %d. Increase spacing or split the grid."),
			RoadCount, MaxRoadsPerCall));
		return FRoadBLDEditResult();
	}

	if (RoadCount == 0)
	{
		RaiseError(TEXT("The grid has no roads: enable bIncludePerimeter or use spacings smaller than the grid size."));
		return FRoadBLDEditResult();
	}

	const FRotator Rotation(0.0, Grid.RotationYaw, 0.0);
	auto ToWorld = [&Grid, &Rotation](const double LocalX, const double LocalY)
	{
		return Grid.Origin + Rotation.RotateVector(FVector(LocalX, LocalY, GroundClearance));
	};

	auto PickPreset = [&](const double Position, const double Spacing)
	{
		const bool bArterial = ArterialObject && Grid.ArterialEvery > 0
			&& FMath::RoundToInt32(Position / Spacing) % Grid.ArterialEvery == 0;
		return bArterial ? ArterialObject : PresetObject;
	};

	FAuthoringAction Action(TEXT("Create Road Grid"));
	FString Error;
	ADynamicRoadNetwork* TargetNetwork = Action.BeginOnNetwork(Network, Error);
	if (!TargetNetwork)
	{
		return FailWith(Action, Error);
	}

	// Without a perimeter a short overhang only extends dead ends, so any value is fine.
	double Overhang = FMath::Max(0.0, Grid.Overhang);
	auto RowPoints = [&](const double Y)
	{
		TArray<FRoadBLDPoint> Points;
		Points.AddDefaulted(2);
		Points[0].Location = ToWorld(-Overhang, Y);
		Points[1].Location = ToWorld(Grid.SizeX + Overhang, Y);
		return Points;
	};
	auto ColumnPoints = [&](const double X)
	{
		TArray<FRoadBLDPoint> Points;
		Points.AddDefaulted(2);
		Points[0].Location = ToWorld(X, -Overhang);
		Points[1].Location = ToWorld(X, Grid.SizeY + Overhang);
		return Points;
	};

	// Grid lines are exactly placed, so per-road endpoint snapping is skipped; the overhang is checked below instead.
	TArray<ADynamicRoad*> Roads;
	for (int32 Index = 0; Index < YPositions.Num(); ++Index)
	{
		const double Y = YPositions[Index];
		ADynamicRoad* Road = Action.SpawnRoad(TargetNetwork, PickPreset(Y, Grid.SpacingY), RowPoints(Y), FString::Printf(TEXT("GridRoad_Row%02d"), Index), Error, false);
		if (!Road)
		{
			return FailWith(Action, Error);
		}
		Roads.Add(Road);
	}

	for (int32 Index = 0; Index < XPositions.Num(); ++Index)
	{
		const double X = XPositions[Index];
		ADynamicRoad* Road = Action.SpawnRoad(TargetNetwork, PickPreset(X, Grid.SpacingX), ColumnPoints(X), FString::Printf(TEXT("GridRoad_Col%02d"), Index), Error, false);
		if (!Road)
		{
			return FailWith(Action, Error);
		}
		Roads.Add(Road);
	}

	if (!Grid.bIncludePerimeter)
	{
		return Action.Complete(TargetNetwork, Roads, bRebuild, true);
	}

	UDynamicRoadDrawPreset* PerimeterPreset = ArterialObject && Grid.ArterialEvery > 0 ? ArterialObject : PresetObject;
	double MaxHalfWidth = 0.0;
	double MaxWidth = 0.0;
	for (const ADynamicRoad* Road : Roads)
	{
		const double Left = GetRoadSideWidth(Road, ERoadSide::Left, 0.0);
		const double Right = GetRoadSideWidth(Road, ERoadSide::Right, 0.0);
		MaxHalfWidth = FMath::Max3(MaxHalfWidth, Left, Right);
		MaxWidth = FMath::Max(MaxWidth, Left + Right);
	}

	// A short overhang leaves every road ending just past the perimeter: too short for a crossing arm.
	if (Overhang > 0.0 && Roads.Num() > 0)
	{
		const double MinOverhang = MaxHalfWidth + FMath::Max(JunctionMinCrossArm, MaxWidth);
		if (Overhang < MinOverhang)
		{
			Action.Warnings.Add(FString::Printf(
				TEXT("Overhang %.0f cm would leave road ends just past the perimeter, which RoadBLD cannot build as junctions, so it was set to 0. Use 0, or at least %.0f cm."),
				Overhang, MinOverhang));
			Overhang = 0.0;
			for (int32 Index = 0; Index < Roads.Num(); ++Index)
			{
				const bool bRow = Index < YPositions.Num();
				const TArray<FRoadBLDPoint> Points = bRow ? RowPoints(YPositions[Index]) : ColumnPoints(XPositions[Index - YPositions.Num()]);
				if (!SetRoadPoints(Roads[Index], Points, Error))
				{
					return FailWith(Action, Error);
				}
			}
		}
	}

	// Lines that end on the perimeter (T junctions) must meet a straight part of it, clear of the rounded corners.
	double CornerRadius = FMath::Min3(Grid.PerimeterCornerRadius, Grid.SizeX * 0.5, Grid.SizeY * 0.5);
	if (Overhang <= 0.0 && Roads.Num() > 0)
	{
		double Clearance = TNumericLimits<double>::Max();
		for (const TArray<double>* Positions : { &XPositions, &YPositions })
		{
			if (Positions->Num() > 0)
			{
				const double Size = Positions == &XPositions ? Grid.SizeX : Grid.SizeY;
				Clearance = FMath::Min3(Clearance, (*Positions)[0], Size - Positions->Last());
			}
		}

		// For a right-angle corner the fillet starts CornerRadius from the vertex.
		const double MaxRadius = Clearance - MaxHalfWidth - 100.0;
		if (CornerRadius > MaxRadius)
		{
			CornerRadius = FMath::Max(MaxRadius, RadiusLimit.X);
			Action.Warnings.Add(MaxRadius >= RadiusLimit.X
				? FString::Printf(TEXT("PerimeterCornerRadius was reduced to %.0f cm so the outer grid lines meet a straight part of the perimeter."), CornerRadius)
				: FString::Printf(TEXT("The outer grid lines are too close to the perimeter corners to round them (need %.0f cm clearance); they may not join cleanly. Increase the spacing or add an Overhang."),
					RadiusLimit.X + MaxHalfWidth + 100.0));
		}
	}
	CornerRadius = FMath::Clamp(CornerRadius, RadiusLimit.X, RadiusLimit.Y);

	// Split the loop on the two X edges, in the widest gap between the lines that cross them.
	TArray<double> Stops = { CornerRadius };
	Stops.Append(XPositions);
	Stops.Add(Grid.SizeX - CornerRadius);
	double SplitX = Grid.SizeX * 0.5;
	double WidestGap = -1.0;
	for (int32 Index = 1; Index < Stops.Num(); ++Index)
	{
		if (Stops[Index] - Stops[Index - 1] > WidestGap)
		{
			WidestGap = Stops[Index] - Stops[Index - 1];
			SplitX = (Stops[Index] + Stops[Index - 1]) * 0.5;
		}
	}

	const TArray<FVector> Polygon = { ToWorld(0.0, 0.0), ToWorld(Grid.SizeX, 0.0), ToWorld(Grid.SizeX, Grid.SizeY), ToWorld(0.0, Grid.SizeY) };
	if (!SpawnLoop(Action, TargetNetwork, PerimeterPreset, Polygon, CornerRadius,
		0, ToWorld(SplitX, 0.0), 2, ToWorld(SplitX, Grid.SizeY), TEXT("GridRoad_Perimeter"), Roads, Error))
	{
		return FailWith(Action, Error);
	}

	return Action.Complete(TargetNetwork, Roads, bRebuild, true);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::CreateRing(
	TSubclassOf<UDynamicRoadDrawPreset> Preset,
	const TArray<FVector>& Polygon,
	const double CornerRadius,
	ADynamicRoadNetwork* Network,
	const FString& Label,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	UDynamicRoadDrawPreset* PresetObject = GetPresetObject(Preset);
	if (!PresetObject)
	{
		RaiseError(TEXT("Preset is required. Use an Id from ListPresets."));
		return FRoadBLDEditResult();
	}

	const int32 VertexCount = Polygon.Num();
	if (VertexCount < 3)
	{
		RaiseError(TEXT("A ring needs at least three polygon vertices."));
		return FRoadBLDEditResult();
	}

	TArray<FVector> Lifted = Polygon;
	for (FVector& Vertex : Lifted)
	{
		Vertex.Z += GroundClearance;
	}

	// Split the loop at the midpoints of two opposite edges so both joints are straight and tangent-continuous.
	const int32 HalfIndex = VertexCount / 2;
	auto EdgeMidpoint = [&Lifted, VertexCount](const int32 EdgeStart)
	{
		return (Lifted[EdgeStart] + Lifted[(EdgeStart + 1) % VertexCount]) * 0.5;
	};

	FAuthoringAction Action(TEXT("Create Ring Road"));
	FString Error;
	ADynamicRoadNetwork* TargetNetwork = Action.BeginOnNetwork(Network, Error);
	if (!TargetNetwork)
	{
		return FailWith(Action, Error);
	}

	const FString Prefix = GetOptionalString(Label, TEXT("Auto"));
	TArray<ADynamicRoad*> Roads;
	if (!SpawnLoop(Action, TargetNetwork, PresetObject, Lifted, CornerRadius,
		0, EdgeMidpoint(0), HalfIndex, EdgeMidpoint(HalfIndex), Prefix.IsEmpty() ? TEXT("RingRoad") : Prefix, Roads, Error))
	{
		return FailWith(Action, Error);
	}

	return Action.Complete(TargetNetwork, Roads, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::CreateRoundabout(
	TSubclassOf<UDynamicRoadDrawPreset> Preset,
	const FVector Center,
	const double Radius,
	const int32 ApproachCount,
	const double FirstApproachYaw,
	const double ApproachLength,
	TSubclassOf<UDynamicRoadDrawPreset> ApproachPreset,
	ADynamicRoadNetwork* Network,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	UDynamicRoadDrawPreset* PresetObject = GetPresetObject(Preset);
	UDynamicRoadDrawPreset* ApproachObject = ApproachPreset ? GetPresetObject(ApproachPreset) : PresetObject;
	if (!PresetObject)
	{
		RaiseError(TEXT("Preset is required. Use an Id from ListPresets."));
		return FRoadBLDEditResult();
	}

	const FVector2D RadiusLimit = GetTurnRadiusLimit();
	if (Radius < RadiusLimit.X || Radius > RadiusLimit.Y)
	{
		RaiseError(FString::Printf(TEXT("Radius must be between %.0f and %.0f cm."), RadiusLimit.X, RadiusLimit.Y));
		return FRoadBLDEditResult();
	}

	if (ApproachCount < 0 || ApproachCount > 12 || (ApproachCount > 0 && ApproachLength <= 0.0))
	{
		RaiseError(TEXT("ApproachCount must be 0-12 and ApproachLength positive."));
		return FRoadBLDEditResult();
	}

	TArray<double> ApproachYaws;
	for (int32 Index = 0; Index < ApproachCount; ++Index)
	{
		ApproachYaws.Add(FirstApproachYaw + Index * 360.0 / ApproachCount);
	}

	// Place the two ring joints as far from the approaches as possible.
	double JointYaw = FirstApproachYaw + 90.0;
	double BestClearance = -1.0;
	for (double Candidate = 0.0; Candidate < 180.0; Candidate += 5.0)
	{
		double Clearance = 180.0;
		for (const double ApproachYaw : ApproachYaws)
		{
			for (const double Joint : { Candidate, Candidate + 180.0 })
			{
				Clearance = FMath::Min(Clearance, FMath::Abs(FMath::FindDeltaAngleDegrees(Joint, ApproachYaw)));
			}
		}
		if (Clearance > BestClearance)
		{
			BestClearance = Clearance;
			JointYaw = Candidate;
		}
	}

	FAuthoringAction Action(TEXT("Create Roundabout"));
	FString Error;
	ADynamicRoadNetwork* TargetNetwork = Action.BeginOnNetwork(Network, Error);
	if (!TargetNetwork)
	{
		return FailWith(Action, Error);
	}

	const FVector RingCenter = Center + FVector(0.0, 0.0, GroundClearance);
	TArray<ADynamicRoad*> Roads;
	for (int32 Half = 0; Half < 2; ++Half)
	{
		ADynamicRoad* RingRoad = Action.SpawnRoad(TargetNetwork, PresetObject, {}, FString::Printf(TEXT("Roundabout_%s"), Half == 0 ? TEXT("A") : TEXT("B")), Error);
		if (!RingRoad)
		{
			return FailWith(Action, Error);
		}

		const double StartYaw = JointYaw + Half * 180.0;
		RingRoad->CreateSemicircle(Radius, RingCenter, StartYaw, StartYaw + 180.0);
		RingRoad->CalculateRefLine();
		Roads.Add(RingRoad);
	}

	if (!CreateReciprocalLink(Roads[0], false, Roads[1], true) || !CreateReciprocalLink(Roads[1], false, Roads[0], true))
	{
		return FailWith(Action, TEXT("Failed to link the two halves of the roundabout."));
	}

	for (int32 Index = 0; Index < ApproachYaws.Num(); ++Index)
	{
		const FVector Direction = FRotator(0.0, ApproachYaws[Index], 0.0).Vector();
		TArray<FRoadBLDPoint> Points;
		Points.AddDefaulted(2);
		Points[0].Location = RingCenter + Direction * (Radius + ApproachLength);
		Points[1].Location = RingCenter + Direction * Radius;

		ADynamicRoad* Approach = Action.SpawnRoad(TargetNetwork, ApproachObject, Points, FString::Printf(TEXT("Roundabout_Approach%d"), Index), Error);
		if (!Approach)
		{
			return FailWith(Action, Error);
		}
		Roads.Add(Approach);
	}

	return Action.Complete(TargetNetwork, Roads, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::ConnectEndpoints(
	const FRoadBLDEndpointRef& A,
	const FRoadBLDEndpointRef& B,
	const ERoadBLDConnectMode Mode,
	TSubclassOf<UDynamicRoadDrawPreset> Preset,
	const double LinkTolerance,
	const double TurnRadius,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	ADynamicRoad* RoadA = A.Road.Get();
	ADynamicRoad* RoadB = B.Road.Get();
	FVector LocationA;
	FVector LocationB;
	if (!GetEndpointLocation(RoadA, A.bStart, LocationA) || !GetEndpointLocation(RoadB, B.bStart, LocationB))
	{
		RaiseError(TEXT("Both endpoints must reference valid roads with control points."));
		return FRoadBLDEditResult();
	}

	ADynamicRoadNetwork* Network = GetOwningNetwork(RoadA);
	if (Network != GetOwningNetwork(RoadB))
	{
		RaiseError(TEXT("Both roads must belong to the same road network."));
		return FRoadBLDEditResult();
	}

	const double Distance = FVector::Dist2D(LocationA, LocationB);
	const bool bLink = Mode == ERoadBLDConnectMode::Link || (Mode == ERoadBLDConnectMode::Auto && Distance <= LinkTolerance);

	if (bLink)
	{
		if (Distance > LinkTolerance)
		{
			RaiseError(FString::Printf(
				TEXT("The endpoints are %.0f cm apart (tolerance %.0f). Use Mode=Bridge, or move one end with SetControlPoints."),
				Distance, LinkTolerance));
			return FRoadBLDEditResult();
		}

		FString Reason;
		if (!CanLinkEndpoints(RoadA, A.bStart, RoadB, B.bStart, Reason))
		{
			RaiseError(Reason);
			return FRoadBLDEditResult();
		}

		EEndpointMeeting Meeting = EEndpointMeeting::Continuation;
		double TurnAngle = 0.0;
		if (ClassifyEndpointMeeting(RoadA, A.bStart, RoadB, B.bStart, Meeting, TurnAngle) && Meeting == EEndpointMeeting::Corner)
		{
			RaiseError(FString::Printf(
				TEXT("The ends meet at a %.0f degree turn. A link only joins roads that continue straight (within %.0f degrees); use CloseCorner to build a rounded corner."),
				TurnAngle, ContinuationMaxAngle));
			return FRoadBLDEditResult();
		}

		FAuthoringAction Action(TEXT("Link Road Endpoints"));
		Action.AddNetwork(Network);
		if (!Action.Begin())
		{
			return FRoadBLDEditResult();
		}

		Action.ModifyRoad(RoadA);
		Action.ModifyRoad(RoadB);
		if (!CreateReciprocalLink(RoadA, A.bStart, RoadB, B.bStart))
		{
			return FailWith(Action, TEXT("RoadBLD rejected the endpoint link."));
		}
		return Action.Complete(Network, { RoadA, RoadB }, bRebuild, false);
	}

	UDynamicRoadDrawPreset* PresetObject = Preset ? GetPresetObject(Preset) : RoadA->SourceDrawPreset.Get();
	if (!PresetObject)
	{
		RaiseError(TEXT("Road A has no preset; pass Preset for the bridging road."));
		return FRoadBLDEditResult();
	}

	FVector DirectionA;
	FVector DirectionB;
	GetEndpointOutwardDirection(RoadA, A.bStart, DirectionA);
	GetEndpointOutwardDirection(RoadB, B.bStart, DirectionB);

	const double Handle = FMath::Clamp(Distance * 0.25, 200.0, 3000.0);
	TArray<FRoadBLDPoint> Points;
	auto AddPoint = [&Points, TurnRadius](const FVector& Location)
	{
		FRoadBLDPoint& Point = Points.AddDefaulted_GetRef();
		Point.Location = Location;
		Point.TurnRadius = TurnRadius;
	};
	AddPoint(LocationA);
	if (Distance > Handle * 2.5 && !DirectionA.IsNearlyZero() && !DirectionB.IsNearlyZero())
	{
		AddPoint(LocationA + DirectionA * Handle);
		AddPoint(LocationB + DirectionB * Handle);
	}
	AddPoint(LocationB);

	FAuthoringAction Action(TEXT("Bridge Road Endpoints"));
	Action.AddNetwork(Network);
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	FString Error;
	ADynamicRoad* Bridge = Action.SpawnRoad(Network, PresetObject, Points, TEXT("ConnectorRoad"), Error);
	if (!Bridge)
	{
		return FailWith(Action, Error);
	}

	Action.ModifyRoad(RoadA);
	Action.ModifyRoad(RoadB);
	for (const TPair<const FRoadBLDEndpointRef*, bool>& End : { TPair<const FRoadBLDEndpointRef*, bool>(&A, true), TPair<const FRoadBLDEndpointRef*, bool>(&B, false) })
	{
		FString Reason;
		if (!CanLinkEndpoints(Bridge, End.Value, End.Key->Road.Get(), End.Key->bStart, Reason)
			|| !CreateReciprocalLink(Bridge, End.Value, End.Key->Road.Get(), End.Key->bStart))
		{
			Action.Warnings.Add(FString::Printf(TEXT("Connector road was not linked to %s: %s"), *End.Key->Road->GetActorLabel(), *Reason));
		}
	}

	Action.CheckShape(Bridge);
	return Action.Complete(Network, { Bridge }, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::SetControlPoints(
	ADynamicRoad* Road,
	const TArray<FRoadBLDPoint>& Points,
	const double LinkTolerance,
	const bool bSnapEndpointsToJunctions,
	const bool bCloseCorners,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	if (!IsValid(Road))
	{
		RaiseError(TEXT("Road is required."));
		return FRoadBLDEditResult();
	}

	if (Points.Num() < 2)
	{
		RaiseError(TEXT("A road needs at least two points."));
		return FRoadBLDEditResult();
	}

	TArray<FRoadBLDPoint> FinalPoints = Points;

	struct FSavedLink
	{
		bool bOwnStart = true;
		FRoadEndpointLink Link;
	};

	TArray<FSavedLink> SavedLinks;
	for (const bool bStart : { true, false })
	{
		if (const TArray<FRoadEndpointLink>* Links = Road->GetEndpointLinks(bStart))
		{
			for (const FRoadEndpointLink& Link : *Links)
			{
				SavedLinks.Add({ bStart, Link });
			}
		}
	}

	FAuthoringAction Action(TEXT("Set Road Control Points"));
	Action.AddNetwork(GetOwningNetwork(Road));
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	Action.ModifyRoad(Road);
	for (const FSavedLink& Saved : SavedLinks)
	{
		Action.ModifyRoad(Saved.Link.LinkedRoad.Get());
	}

	Road->ClearEndpointLinks(true);
	Road->ClearEndpointLinks(false);

	if (bSnapEndpointsToJunctions)
	{
		Action.SnapEndpointsToJunctions(GetOwningNetwork(Road), Road, FinalPoints);
	}

	FString Error;
	if (!SetRoadPoints(Road, FinalPoints, Error))
	{
		return FailWith(Action, Error);
	}

	for (const FSavedLink& Saved : SavedLinks)
	{
		ADynamicRoad* Partner = Saved.Link.LinkedRoad.Get();
		if (!IsValid(Partner))
		{
			continue;
		}

		FVector NewEnd;
		FVector PartnerEnd;
		const bool bStillTouching = GetEndpointLocation(Road, Saved.bOwnStart, NewEnd)
			&& GetEndpointLocation(Partner, Saved.Link.bLinkedToFirstPoint, PartnerEnd)
			&& FVector::Dist2D(NewEnd, PartnerEnd) <= LinkTolerance;
		if (bStillTouching)
		{
			Road->AddEndpointLink(Saved.bOwnStart, Saved.Link);
		}
		else
		{
			Partner->RemoveEndpointLink(Saved.Link.bLinkedToFirstPoint, Road, Saved.bOwnStart);
			Action.Warnings.Add(FString::Printf(TEXT("Removed the %s link to %s because that end moved away."),
				EndName(Saved.bOwnStart), *Partner->GetActorLabel()));
		}
	}

	Action.CheckShape(Road);
	TArray<ADynamicRoad*> Roads = { Road };
	if (!HandleCorners(Action, Road, bCloseCorners, Roads, Error))
	{
		return FailWith(Action, Error);
	}

	return Action.Complete(GetOwningNetwork(Road), Roads, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::ChangePreset(
	ADynamicRoad* Road,
	TSubclassOf<UDynamicRoadDrawPreset> Preset,
	const bool bKeepSidewalkOverrides,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	UDynamicRoadDrawPreset* PresetObject = GetPresetObject(Preset);
	if (!IsValid(Road) || !PresetObject)
	{
		RaiseError(TEXT("Road and Preset are required."));
		return FRoadBLDEditResult();
	}

	FAuthoringAction Action(TEXT("Change Road Preset"));
	Action.AddNetwork(GetOwningNetwork(Road));
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	Action.ModifyRoad(Road);
	ApplyPresetToRoad(Road, PresetObject, bKeepSidewalkOverrides);
	Action.CheckShape(Road);
	return Action.Complete(GetOwningNetwork(Road), { Road }, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::SetLaneWidth(
	ADynamicRoad* Road,
	const ERoadBLDSide Side,
	const int32 LaneIndex,
	const double Width,
	const FRoadBLDRange& Range,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	if (!IsValid(Road))
	{
		RaiseError(TEXT("Road is required."));
		return FRoadBLDEditResult();
	}

	if (Side == ERoadBLDSide::Both)
	{
		RaiseError(TEXT("Side must be Left or Right."));
		return FRoadBLDEditResult();
	}

	if (!FMath::IsFinite(Width) || Width < 0.0 || Width > 10000.0)
	{
		RaiseError(TEXT("Width must be between 0 and 10000 cm."));
		return FRoadBLDEditResult();
	}

	const bool bLeft = Side == ERoadBLDSide::Left;
	const TArray<TObjectPtr<UDynamicRoadLane>>& Lanes = bLeft ? Road->LeftLanes : Road->RightLanes;
	if (!Lanes.IsValidIndex(LaneIndex) || !IsValid(Lanes[LaneIndex]))
	{
		RaiseError(FString::Printf(TEXT("LaneIndex %d is out of range; the %s side has %d lanes."),
			LaneIndex, bLeft ? TEXT("left") : TEXT("right"), Lanes.Num()));
		return FRoadBLDEditResult();
	}

	const UDynamicRoadLane* Lane = Lanes[LaneIndex];
	UEdgeCurve* OuterEdge = bLeft ? Lane->LeftEdgeCurve.Get() : Lane->RightEdgeCurve.Get();
	const UEdgeCurve* InnerEdge = bLeft ? Lane->RightEdgeCurve.Get() : Lane->LeftEdgeCurve.Get();
	const double RoadLength = Road->GetLength();
	if (!IsValid(OuterEdge) || !IsValid(InnerEdge) || RoadLength <= 1.0)
	{
		RaiseError(TEXT("The lane has no valid boundaries or the road has no length yet."));
		return FRoadBLDEditResult();
	}

	const TArray<UEdgeCurve*> SideEdges = GetSortedSideEdges(Road, ToRoadSide(Side));
	const int32 OuterIndex = SideEdges.Find(OuterEdge);
	if (OuterIndex == INDEX_NONE)
	{
		RaiseError(TEXT("Could not locate the lane boundary on its side of the road."));
		return FRoadBLDEditResult();
	}
	const TArray<UEdgeCurve*> ShiftedEdges(SideEdges.GetData() + OuterIndex, SideEdges.Num() - OuterIndex);

	// A default (all-zero) range means the whole road.
	const bool bWholeRoad = Range.StartDistance == 0.0 && Range.EndDistance == 0.0;
	double RampInStart = 0.0;
	double RampInEnd = 0.0;
	double RampOutStart = RoadLength;
	double RampOutEnd = RoadLength;
	if (!bWholeRoad)
	{
		const double Start = FMath::Clamp(Range.StartDistance, 0.0, RoadLength);
		const double End = FMath::Clamp(Range.EndDistance, 0.0, RoadLength);
		if (End <= Start)
		{
			RaiseError(FString::Printf(TEXT("Range.EndDistance must be greater than StartDistance (road length is %.0f cm). Omit Range to change the whole road."), RoadLength));
			return FRoadBLDEditResult();
		}

		const double Transition = FMath::Max(0.0, Range.Transition);
		RampInStart = FMath::Max(0.0, Start - Transition);
		RampInEnd = Start;
		RampOutStart = End;
		RampOutEnd = FMath::Min(RoadLength, End + Transition);
	}

	auto Weight = [&](const double Distance)
	{
		if (bWholeRoad)
		{
			return 1.0;
		}
		if (Distance < RampInStart || Distance > RampOutEnd)
		{
			return 0.0;
		}
		if (Distance < RampInEnd)
		{
			return (Distance - RampInStart) / FMath::Max(RampInEnd - RampInStart, UE_SMALL_NUMBER);
		}
		if (Distance > RampOutStart)
		{
			return (RampOutEnd - Distance) / FMath::Max(RampOutEnd - RampOutStart, UE_SMALL_NUMBER);
		}
		return 1.0;
	};

	TArray<double> RawDistances = { 0.0, RoadLength, RampInStart, RampInEnd, RampOutStart, RampOutEnd };
	const double Step = FMath::Clamp(RoadLength / 64.0, 100.0, 1000.0);
	for (double Distance = Step; Distance < RoadLength; Distance += Step)
	{
		RawDistances.Add(Distance);
	}
	for (const UEdgeCurve* Edge : ShiftedEdges)
	{
		for (const FOffsetPoint& Point : Edge->OffsetPoints)
		{
			RawDistances.Add(Point.Distance);
		}
	}
	for (const FOffsetPoint& Point : InnerEdge->OffsetPoints)
	{
		RawDistances.Add(Point.Distance);
	}

	RawDistances.Sort();
	TArray<double> Distances;
	for (const double RawDistance : RawDistances)
	{
		const double Distance = FMath::Clamp(RawDistance, 0.0, RoadLength);
		if (Distances.Num() == 0 || Distance - Distances.Last() > 1.0)
		{
			Distances.Add(Distance);
		}
	}
	Distances[0] = 0.0;
	if (RoadLength - Distances.Last() > 1.0)
	{
		Distances.Add(RoadLength);
	}
	else
	{
		Distances.Last() = RoadLength;
	}

	TArray<FRoadCrossSectionEdgeProfile> Profiles;
	Profiles.SetNum(ShiftedEdges.Num());
	for (int32 EdgeIndex = 0; EdgeIndex < ShiftedEdges.Num(); ++EdgeIndex)
	{
		Profiles[EdgeIndex].EdgeCurve = ShiftedEdges[EdgeIndex];
	}

	for (const double Distance : Distances)
	{
		const double CurrentWidth = EvaluateEdgeOffset(OuterEdge, Distance) - EvaluateEdgeOffset(InnerEdge, Distance);
		const double Delta = Weight(Distance) * (Width - CurrentWidth);
		for (int32 EdgeIndex = 0; EdgeIndex < ShiftedEdges.Num(); ++EdgeIndex)
		{
			FOffsetPoint& Point = Profiles[EdgeIndex].OffsetPoints.AddDefaulted_GetRef();
			Point.Distance = Distance;
			Point.Offset = FMath::Max(0.0, EvaluateEdgeOffset(ShiftedEdges[EdgeIndex], Distance) + Delta);
		}
	}

	FAuthoringAction Action(TEXT("Set Lane Width"));
	Action.AddNetwork(GetOwningNetwork(Road));
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	Action.ModifyRoad(Road);
	for (UEdgeCurve* Edge : ShiftedEdges)
	{
		Action.ModifyObject(Edge);
	}

	FString Error;
	if (!Road->ApplyCrossSectionEdgeProfiles(Profiles, Error))
	{
		return FailWith(Action, Error);
	}

	return Action.Complete(GetOwningNetwork(Road), { Road }, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::SetSidewalk(
	ADynamicRoad* Road,
	const ERoadBLDSide Side,
	TSubclassOf<URoadBLDSidewalkPreset> Preset,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	if (!IsValid(Road))
	{
		RaiseError(TEXT("Road is required."));
		return FRoadBLDEditResult();
	}

	TArray<ERoadSide> Sides;
	if (Side != ERoadBLDSide::Right)
	{
		Sides.Add(ERoadSide::Left);
	}
	if (Side != ERoadBLDSide::Left)
	{
		Sides.Add(ERoadSide::Right);
	}

	FAuthoringAction Action(Preset ? TEXT("Set Sidewalk") : TEXT("Remove Sidewalk"));
	Action.AddNetwork(GetOwningNetwork(Road));
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	Action.ModifyRoad(Road);
	for (const ERoadSide RoadSide : Sides)
	{
		const bool bSucceeded = Preset
			? Road->ApplySidewalkPresetToSide(RoadSide, Preset)
			: (Road->GetSidewalkOnSide(RoadSide) == nullptr || Road->ClearSidewalkOnSide(RoadSide));
		if (!bSucceeded)
		{
			return FailWith(Action, FString::Printf(TEXT("RoadBLD could not update the %s sidewalk."),
				RoadSide == ERoadSide::Left ? TEXT("left") : TEXT("right")));
		}
	}

	return Action.Complete(GetOwningNetwork(Road), { Road }, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::AddLane(
	ADynamicRoad* Road,
	const ERoadBLDSide Side,
	const int32 Index,
	const double Width,
	UMaterialInterface* MarkingMaterial,
	const double MarkingWidth,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	if (!IsValid(Road) || Side == ERoadBLDSide::Both)
	{
		RaiseError(TEXT("Road is required and Side must be Left or Right."));
		return FRoadBLDEditResult();
	}

	if (!FMath::IsFinite(Width) || Width <= 0.0)
	{
		RaiseError(TEXT("Width must be positive."));
		return FRoadBLDEditResult();
	}

	FAuthoringAction Action(TEXT("Add Lane"));
	Action.AddNetwork(GetOwningNetwork(Road));
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	Action.ModifyRoad(Road);
	FDynamicRoadDrawPresetMarking Marking;
	Marking.MarkingMaterial = MarkingMaterial;
	Marking.MarkingWidth = static_cast<float>(MarkingWidth);
	if (!Road->AddLane(ToRoadSide(Side), Index, Width, Marking))
	{
		return FailWith(Action, TEXT("RoadBLD could not add the lane."));
	}

	Road->CalculateLaneShapes();
	return Action.Complete(GetOwningNetwork(Road), { Road }, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::DeleteRoads(const TArray<ADynamicRoad*>& Roads, const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	TArray<ADynamicRoad*> RoadsToDelete;
	for (ADynamicRoad* Road : Roads)
	{
		if (IsValid(Road))
		{
			RoadsToDelete.AddUnique(Road);
		}
	}

	if (RoadsToDelete.Num() == 0)
	{
		RaiseError(TEXT("Roads must contain at least one valid road."));
		return FRoadBLDEditResult();
	}

	ADynamicRoadNetwork* FirstNetwork = GetOwningNetwork(RoadsToDelete[0]);

	FAuthoringAction Action(TEXT("Delete Roads"));
	for (ADynamicRoad* Road : RoadsToDelete)
	{
		Action.AddNetwork(GetOwningNetwork(Road));
	}
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	for (ADynamicRoad* Road : RoadsToDelete)
	{
		Action.ModifyRoad(Road);
		for (const bool bStart : { true, false })
		{
			if (const TArray<FRoadEndpointLink>* Links = Road->GetEndpointLinks(bStart))
			{
				for (const FRoadEndpointLink& Link : *Links)
				{
					Action.ModifyRoad(Link.LinkedRoad.Get());
				}
			}
		}
	}

	for (ADynamicRoad* Road : RoadsToDelete)
	{
		Action.DeleteRoad(Road);
	}

	return Action.Complete(FirstNetwork, {}, bRebuild, true);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::DuplicateRoad(ADynamicRoad* Road, const FVector2D Offset, const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	if (!IsValid(Road))
	{
		RaiseError(TEXT("Road is required."));
		return FRoadBLDEditResult();
	}

	FAuthoringAction Action(TEXT("Duplicate Road"));
	Action.AddNetwork(GetOwningNetwork(Road));
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	ADynamicRoad* Copy = URoadEditorFunctionLibrary::DuplicateRoad(Road, Offset, true);
	if (!IsValid(Copy))
	{
		return FailWith(Action, TEXT("RoadBLD could not duplicate the road."));
	}

	Action.TrackSpawnedRoad(Copy);
	Action.CheckShape(Copy);
	return Action.Complete(GetOwningNetwork(Copy), { Copy }, bRebuild, false);
}

FRoadBLDEditResult URoadBLDAuthoringToolset::CloseCorner(
	const FRoadBLDEndpointRef& A,
	const FRoadBLDEndpointRef& B,
	const double TurnRadius,
	const bool bRebuild)
{
	using namespace RoadBLDAuthoringPrivate;

	FCornerPlan Plan;
	FString Error;
	if (!PlanCorner(A.Road.Get(), A.bStart, B.Road.Get(), B.bStart, TurnRadius, Plan, Error))
	{
		RaiseError(Error);
		return FRoadBLDEditResult();
	}

	FAuthoringAction Action(TEXT("Close Road Corner"));
	Action.AddNetwork(Plan.Network);
	if (!Action.Begin())
	{
		return FRoadBLDEditResult();
	}

	TArray<ADynamicRoad*> Roads = { Plan.RoadA };
	if (!ApplyCorner(Action, Plan, Roads, Error))
	{
		return FailWith(Action, Error);
	}

	if (!Plan.bSamePreset)
	{
		Roads.Add(Plan.RoadB);
	}
	return Action.Complete(Plan.Network, Roads, bRebuild, Plan.bSamePreset);
}
