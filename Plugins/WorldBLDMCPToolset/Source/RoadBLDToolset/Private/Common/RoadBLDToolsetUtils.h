// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/RoadBLDToolsetTypes.h"
#include "DynamicRoad/DynamicRoadData.h"
#include "Templates/SubclassOf.h"

class AActor;
class ADynamicRoad;
class ADynamicRoadNetwork;
class ARoadGeo;
class UEdgeCurve;
class UWorld;

namespace RoadBLDToolset
{
	/** Root folder for assets created by the toolset. */
	extern const TCHAR* GeneratedContentRoot;

	void RaiseError(const FString& Message);
	UWorld* GetEditorWorld();
	/** Sets GIsRunningUnattendedScript until the next tick so product UI skips modal dialogs. */
	void MarkCurrentCallUnattended();
	/** Dialog-free RoadBLD access check. Returns false with the reason when edits are blocked. Raises nothing. */
	bool CheckAuthorized(FString& OutError);
	/** CheckAuthorized that raises the reason as a script error when edits are blocked. */
	bool EnsureAuthorized();

#if WITH_DEV_AUTOMATION_TESTS
	/**
	 * Lets the toolset's own automation specs make licensed calls while the scope is alive. Only honored while
	 * GIsAutomationTesting is set. Keep scopes inside a single test step so tool calls from other clients that run
	 * between ticks are never covered.
	 */
	struct FScopedTestAuthorization
	{
		FScopedTestAuthorization();
		~FScopedTestAuthorization();
		UE_NONCOPYABLE(FScopedTestAuthorization);
	};
#endif

	FRoadBLDActorRef MakeActorRef(const AActor* Actor);
	FString GetObjectPath(const UObject* Object);
	TArray<FString> SplitCommaList(const FString& List);

	/**
	 * The registry treats a string parameter with an empty C++ default as required, so optional string parameters
	 * default to a word instead (Any, Auto or None). Returns the trimmed value, or "" when it is empty or that word.
	 */
	FString GetOptionalString(const FString& Value, const TCHAR* UnsetWord);
	FString SanitizeAssetName(const FString& Name);

	template <typename TEnum>
	FString EnumToString(const TEnum Value)
	{
		return StaticEnum<TEnum>()->GetNameStringByValue(static_cast<int64>(Value));
	}

	template <typename TEnum>
	bool EnumFromString(const FString& Name, TEnum& OutValue)
	{
		const int64 RawValue = StaticEnum<TEnum>()->GetValueByNameString(Name.TrimStartAndEnd());
		if (RawValue == INDEX_NONE)
		{
			return false;
		}
		OutValue = static_cast<TEnum>(RawValue);
		return true;
	}

	template <typename TEnum>
	FString ListEnumNames()
	{
		const UEnum* Enum = StaticEnum<TEnum>();
		TArray<FString> Names;
		for (int32 Index = 0; Index < Enum->NumEnums() - 1; ++Index)
		{
			if (!Enum->HasMetaData(TEXT("Hidden"), Index))
			{
				Names.Add(Enum->GetNameStringByIndex(Index));
			}
		}
		return FString::Join(Names, TEXT(", "));
	}

	ERoadSide ToRoadSide(ERoadBLDSide Side);

	// Networks
	TArray<ADynamicRoadNetwork*> GetNetworks();
	ADynamicRoadNetwork* GetOwningNetwork(ADynamicRoad* Road);
	ADynamicRoadNetwork* SpawnNetwork(const FString& Label, FString& OutError);
	/** Returns Requested, the only network in the level, or (when allowed) a newly spawned one. */
	ADynamicRoadNetwork* ResolveNetwork(ADynamicRoadNetwork* Requested, bool bCreateIfMissing, bool& bOutCreated, FString& OutError);

	// Asset and class lookup
	UClass* LoadClassFromPath(const FString& Path, UClass* BaseClass, FString& OutError);
	UObject* LoadObjectFromPath(const FString& Path, UClass* ExpectedClass, FString& OutError);
	TArray<FName> GetContentRoots();
	/** Native and Blueprint subclasses of BaseClass in /Game and project plugin content. */
	TArray<UClass*> DiscoverClasses(UClass* BaseClass);

	// Presets
	TArray<TSubclassOf<UDynamicRoadDrawPreset>> DiscoverPresetClasses();
	FString ResolvePresetRegion(const UClass* PresetClass);
	FRoadBLDPresetTraits ComputePresetTraits(const UDynamicRoadDrawPreset* Preset);
	TArray<FString> ComputeDerivedPresetTags(const UDynamicRoadDrawPreset* Preset, const FRoadBLDPresetTraits& Traits);
	FRoadBLDPresetSummary MakePresetSummary(const UClass* PresetClass);
	bool IsGeneratedAsset(const UObject* Object);

	struct FReferenceKitAsset
	{
		/** Package path, as named in the toolset descriptions. */
		const TCHAR* PackagePath;
		const TCHAR* Note;
	};

	/** RoadBLD sample presets and assets that agents should study and reuse when authoring new styles. */
	const TArray<FReferenceKitAsset>& GetReferenceKitAssets();
	const FReferenceKitAsset* FindReferenceKitAsset(const FString& PackagePath);

	// Endpoints
	bool GetEndpointLocation(const ADynamicRoad* Road, bool bStart, FVector& OutLocation);
	bool GetEndpointOutwardDirection(const ADynamicRoad* Road, bool bStart, FVector& OutDirection);
	int32 CountEndpointLinks(const ADynamicRoad* Road, bool bStart);
	FRoadBLDEndpointInfo MakeEndpointInfo(ADynamicRoad* Road, bool bStart);
	bool CanLinkEndpoints(ADynamicRoad* RoadA, bool bAStart, ADynamicRoad* RoadB, bool bBStart, FString& OutReason);
	bool CreateReciprocalLink(ADynamicRoad* RoadA, bool bAStart, ADynamicRoad* RoadB, bool bBStart);
	bool FindUnlinkedEndpointNear(
		ADynamicRoadNetwork* Network,
		const FVector& Location,
		double Tolerance,
		const ADynamicRoad* RoadToIgnore,
		ADynamicRoad*& OutRoad,
		bool& bOutStart);

	/** Road ends that meet another road's end: a straight continuation, or a corner at an angle. */
	enum class EEndpointMeeting : uint8
	{
		Continuation,
		Corner
	};

	/** Outward directions within this many degrees of opposite count as a straight continuation. */
	inline constexpr double ContinuationMaxAngle = 20.0;

	/** Ends within this distance (cm) meet. */
	inline constexpr double EndpointMeetTolerance = 100.0;

	/**
	 * Classifies how two road ends meet from their outward directions.
	 * @param OutTurnAngle Heading change in degrees when driving from one road into the other (0 = straight on).
	 * @return False when either end has no direction.
	 */
	bool ClassifyEndpointMeeting(
		const ADynamicRoad* RoadA,
		bool bStartA,
		const ADynamicRoad* RoadB,
		bool bStartB,
		EEndpointMeeting& OutMeeting,
		double& OutTurnAngle);

	/** Classifies from explicit outward directions (for ends that are not applied to a road yet). */
	EEndpointMeeting ClassifyEndpointDirections(const FVector& OutwardA, const FVector& OutwardB, double& OutTurnAngle);

	/** Another road end that meets a road end at an angle. */
	struct FEndpointCorner
	{
		ADynamicRoad* OtherRoad = nullptr;
		bool bOtherStart = true;
		/** True when the two ends are linked to each other. */
		bool bLinked = false;
		double TurnAngle = 0.0;
	};

	/** Road ends in the network that meet the given end (within EndpointMeetTolerance) at an angle. */
	TArray<FEndpointCorner> FindCornersAtEnd(ADynamicRoadNetwork* Network, ADynamicRoad* Road, bool bStart);

	/** True when Road's end is linked to OtherRoad's end. */
	bool AreEndpointsLinked(const ADynamicRoad* Road, bool bStart, const ADynamicRoad* OtherRoad, bool bOtherStart);

	// Cross-section
	/** Lane boundary curves on one side, ordered from the centerline outwards (sidewalk edges included). */
	TArray<UEdgeCurve*> GetSortedSideEdges(const ADynamicRoad* Road, ERoadSide Side);
	/** Cumulative offset of an edge at a distance along the road, matching ApplyCrossSectionEdgeProfiles interpolation. */
	double EvaluateEdgeOffset(const UEdgeCurve* Edge, double Distance);
	/** Width from the centerline to the outermost edge (sidewalk included) on one side. */
	double GetRoadSideWidth(const ADynamicRoad* Road, ERoadSide Side, double Distance);

	// Junction shape
	/** A crossing arm shorter than this past the other road's far edge is too short for RoadBLD to build cleanly. */
	inline constexpr double JunctionMinCrossArm = 1500.0;
	/** Endpoints that stop short of another road by at most this gap are pulled onto its centerline. */
	inline constexpr double JunctionShortGap = 300.0;

	/** An endpoint that forms a degenerate junction arm with another road. */
	struct FJunctionStub
	{
		ADynamicRoad* OtherRoad = nullptr;
		/** Endpoint moved along the incoming direction onto the other road's centerline (a clean T junction). */
		FVector SnappedLocation = FVector::ZeroVector;
		double MoveDistance = 0.0;
		/** True when the endpoint lies past the other road's centerline, false when it stops short of it. */
		bool bPastCenterline = false;
		/** Distance from the other road's outer edge to the endpoint: beyond the far edge, or short of the near edge. Negative when the endpoint is inside the road. */
		double EdgeDistance = 0.0;
	};

	/** Closest distance along a road's reference line to a location (XY). */
	double FindClosestDistanceAlongRoad(const ADynamicRoad* Road, const FVector& Location);

	/**
	 * Checks whether a road end forms a junction arm RoadBLD cannot build: it ends inside another road, just past its
	 * far edge, or just short of it. Ends that meet another road's end (continuations, corners) are ignored.
	 * @param EndLocation The road end.
	 * @param NeighborLocation The control point next to the end, giving the incoming direction.
	 * @param IncomingRoadWidth Total width of the road that owns the end.
	 */
	bool FindJunctionStub(
		ADynamicRoadNetwork* Network,
		const ADynamicRoad* RoadToIgnore,
		const FVector& EndLocation,
		const FVector& NeighborLocation,
		double IncomingRoadWidth,
		FJunctionStub& OutStub);

	// Geometry
	FBox GetRoadBounds(ADynamicRoad* Road, bool bIncludeGeneratedGeometry);
	FBox GetNetworkBounds(ADynamicRoadNetwork* Network, bool bIncludeGeneratedGeometry);
	/** Generated geometry actors built from at least MinSourceRoads roads of the network. */
	TArray<ARoadGeo*> GetNetworkGeos(const ADynamicRoadNetwork* Network, int32 MinSourceRoads = 1);
	/** Generated geometry actors shared by more than one road of the network (intersections and shared pieces). */
	TArray<ARoadGeo*> GetJunctionGeos(const ADynamicRoadNetwork* Network);
	bool DoesGeoReferenceRoad(const ARoadGeo* Geo, const ADynamicRoad* Road);
}
