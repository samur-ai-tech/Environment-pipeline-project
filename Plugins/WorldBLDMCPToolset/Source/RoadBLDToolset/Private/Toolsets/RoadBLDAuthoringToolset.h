// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/RoadBLDToolsetTypes.h"
#include "Templates/SubclassOf.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "RoadBLDAuthoringToolset.generated.h"

class ADynamicRoad;
class ADynamicRoadNetwork;
class UDynamicRoadDrawPreset;
class UMaterialInterface;
class URoadBLDSidewalkPreset;

/**
 * Create and edit RoadBLD roads. Every call is one undoable editor transaction and fails atomically.
 * Junctions are not authored: they form automatically wherever roads overlap once the network is rebuilt. End a side
 * street exactly on the centerline of the road it joins (T junction), or carry it at least 15 m past that road's far
 * edge (crossing). Ends left inside, just beyond or just short of another road are snapped to its centerline and
 * reported in Warnings.
 * Two roads may only end at the same point if they continue straight; those ends are linked automatically. For a turn,
 * draw one road through the corner with a TurnRadius, or call CloseCorner. After Rebuild, run
 * RoadBLDDiscoveryToolset.FindJunctionIssues and FindGeometryIssues.
 * Edits are not visible until the network is rebuilt. Batch many edits with bRebuild=false, then call
 * RoadBLDBuildToolset.Rebuild once. Distances are cm; Z is elevation.
 */
UCLASS(BlueprintType, MinimalAPI)
class URoadBLDAuthoringToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Creates an empty road network actor. Most levels need only one; authoring tools create one automatically when
	 * the level has none.
	 * @param Label World Outliner label.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDActorRef CreateNetwork(const FString& Label = TEXT("RoadNetwork"));

	/**
	 * Creates a road through the given control points. Corners are rounded with each point's TurnRadius.
	 * @param Preset Preset Id from ListPresets or CreatePresetFromSpec.
	 * @param Points At least two points. Consecutive points must not share the same XY position. Z is ground level; the road is placed 5 cm above it.
	 * @param Network Target network. Optional when the level has zero or one network.
	 * @param Label World Outliner label. Auto keeps RoadBLD's generated label.
	 * @param bAutoLinkEndpoints Link each end to an existing unlinked road end within LinkTolerance when the two continue straight. Ends that meet at an angle are reported in Warnings instead.
	 * @param LinkTolerance Distance in cm used by bAutoLinkEndpoints.
	 * @param bConformToLandscape Follow the landscape height instead of the point elevations.
	 * @param bSnapEndpointsToJunctions Move ends that stop inside, just past or just short of another road onto its centerline.
	 * @param bCloseCorners Apply CloseCorner (3000 cm turn radius) to every end that meets another unlinked road end at an angle. With the same preset the other road is merged into this one and deleted.
	 * @param bRebuild Start a rebuild of the affected roads after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult CreateRoad(
		TSubclassOf<UDynamicRoadDrawPreset> Preset,
		const TArray<FRoadBLDPoint>& Points,
		ADynamicRoadNetwork* Network = nullptr,
		const FString& Label = TEXT("Auto"),
		bool bAutoLinkEndpoints = true,
		double LinkTolerance = 100.0,
		bool bConformToLandscape = false,
		bool bSnapEndpointsToJunctions = true,
		bool bCloseCorners = false,
		bool bRebuild = false);

	/**
	 * Creates a grid of straight roads. Crossing roads become intersections on rebuild. The perimeter is one closed
	 * loop with rounded corners; interior roads end on its centerline (T junctions) unless Grid.Overhang carries them
	 * across it.
	 * @param Preset Preset for grid roads.
	 * @param Grid Grid layout.
	 * @param ArterialPreset Optional preset for every Grid.ArterialEvery-th line (wider avenues).
	 * @param Network Target network. Optional when the level has zero or one network.
	 * @param bRebuild Start a full rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult CreateGrid(
		TSubclassOf<UDynamicRoadDrawPreset> Preset,
		const FRoadBLDGridSpec& Grid,
		TSubclassOf<UDynamicRoadDrawPreset> ArterialPreset = nullptr,
		ADynamicRoadNetwork* Network = nullptr,
		bool bRebuild = false);

	/**
	 * Creates a closed loop road (ring road, block perimeter, racetrack) through the polygon vertices.
	 * The loop is built from two roads linked end-to-end.
	 * @param Preset Preset for the ring.
	 * @param Polygon At least three vertices in order (clockwise or counter-clockwise). Do not repeat the first vertex. Z is ground level; the road is placed 5 cm above it.
	 * @param CornerRadius Turn radius applied at every vertex, in cm (1000-100000).
	 * @param Network Target network. Optional when the level has zero or one network.
	 * @param Label Label prefix. Auto uses RingRoad.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult CreateRing(
		TSubclassOf<UDynamicRoadDrawPreset> Preset,
		const TArray<FVector>& Polygon,
		double CornerRadius = 3000.0,
		ADynamicRoadNetwork* Network = nullptr,
		const FString& Label = TEXT("Auto"),
		bool bRebuild = false);

	/**
	 * Creates a circular roundabout from two linked semicircle roads, with optional straight approach roads that
	 * end on the ring (they become junctions on rebuild).
	 * @param Preset Preset for the circulating road (one-way presets suit roundabouts).
	 * @param Center Center of the roundabout. Z is ground level; the roads are placed 5 cm above it.
	 * @param Radius Centerline radius in cm (1000-100000).
	 * @param ApproachCount Number of evenly spaced approach roads (0 for none).
	 * @param FirstApproachYaw Direction of the first approach in degrees (0 = +X, 90 = +Y).
	 * @param ApproachLength Length of each approach road in cm, measured outward from the ring centerline.
	 * @param ApproachPreset Preset for approach roads. Defaults to Preset.
	 * @param Network Target network. Optional when the level has zero or one network.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult CreateRoundabout(
		TSubclassOf<UDynamicRoadDrawPreset> Preset,
		FVector Center,
		double Radius = 3000.0,
		int32 ApproachCount = 4,
		double FirstApproachYaw = 0.0,
		double ApproachLength = 8000.0,
		TSubclassOf<UDynamicRoadDrawPreset> ApproachPreset = nullptr,
		ADynamicRoadNetwork* Network = nullptr,
		bool bRebuild = false);

	/**
	 * Joins two road ends. Link records a smooth continuation between ends that already touch and continue straight
	 * (ends that meet at an angle are rejected; use CloseCorner). Bridge creates a new road between the two ends
	 * (following their directions) and links both of its ends.
	 * @param A First endpoint.
	 * @param B Second endpoint.
	 * @param Mode Auto links when the ends are within LinkTolerance and bridges otherwise.
	 * @param Preset Preset for a bridging road. Defaults to A's preset.
	 * @param LinkTolerance Maximum distance in cm between ends for linking.
	 * @param TurnRadius Turn radius for the bridging road's inner points, in cm.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult ConnectEndpoints(
		const FRoadBLDEndpointRef& A,
		const FRoadBLDEndpointRef& B,
		ERoadBLDConnectMode Mode = ERoadBLDConnectMode::Auto,
		TSubclassOf<UDynamicRoadDrawPreset> Preset = nullptr,
		double LinkTolerance = 100.0,
		double TurnRadius = 3000.0,
		bool bRebuild = false);

	/**
	 * Replaces a road's control points (reshape, extend, change elevation). Endpoint links are kept when the linked
	 * end did not move further than LinkTolerance; otherwise they are removed and reported as warnings.
	 * @param Road The road to reshape.
	 * @param Points New control points (at least two), used exactly as given: Z is the road surface, as DescribeRoad reports it.
	 * @param LinkTolerance Distance in cm used to keep endpoint links.
	 * @param bSnapEndpointsToJunctions Move ends that stop inside, just past or just short of another road onto its centerline.
	 * @param bCloseCorners Apply CloseCorner (3000 cm turn radius) to every end that meets another unlinked road end at an angle. Otherwise those ends are reported in Warnings.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult SetControlPoints(
		ADynamicRoad* Road,
		const TArray<FRoadBLDPoint>& Points,
		double LinkTolerance = 100.0,
		bool bSnapEndpointsToJunctions = true,
		bool bCloseCorners = false,
		bool bRebuild = false);

	/**
	 * Re-initializes a road from another preset, keeping its control points. Replaces lanes, markings, materials,
	 * modules and props; per-lane width edits are lost.
	 * @param Road The road to change.
	 * @param Preset New preset Id.
	 * @param bKeepSidewalkOverrides Keep sidewalks set with SetSidewalk instead of the new preset's sidewalks.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult ChangePreset(
		ADynamicRoad* Road,
		TSubclassOf<UDynamicRoadDrawPreset> Preset,
		bool bKeepSidewalkOverrides = true,
		bool bRebuild = false);

	/**
	 * Sets a lane's width along the whole road, or over a distance range with tapered transitions (turn pockets,
	 * bus bays, narrowing). Lanes further out on the same side shift to make room.
	 * @param Road The road.
	 * @param Side Left or Right (not Both).
	 * @param LaneIndex Lane index on that side; 0 is next to the centerline (see DescribeRoad).
	 * @param Width New width in cm. 0 tapers the lane away.
	 * @param Range Distance range with tapered ends. Omit it (or leave both distances 0) to change the whole road.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult SetLaneWidth(
		ADynamicRoad* Road,
		ERoadBLDSide Side,
		int32 LaneIndex,
		double Width,
		const FRoadBLDRange& Range = FRoadBLDRange(),
		bool bRebuild = false);

	/**
	 * Adds, replaces or removes the sidewalk on one or both sides of a road.
	 * @param Road The road.
	 * @param Side Left, Right or Both.
	 * @param Preset Sidewalk preset class (ListStyleAssets Kind=SidewalkPreset). Omit or null to remove the sidewalk.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult SetSidewalk(
		ADynamicRoad* Road,
		ERoadBLDSide Side,
		TSubclassOf<URoadBLDSidewalkPreset> Preset = nullptr,
		bool bRebuild = false);

	/**
	 * Inserts a new lane on one side of a road. Outer lanes shift outward.
	 * @param Road The road.
	 * @param Side Left or Right (not Both).
	 * @param Index Insert position on that side; 0 is next to the centerline. Out-of-range values append outermost.
	 * @param Width Lane width in cm.
	 * @param MarkingMaterial Optional material for the new lane's outer marking.
	 * @param MarkingWidth Marking width in cm.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult AddLane(
		ADynamicRoad* Road,
		ERoadBLDSide Side,
		int32 Index,
		double Width = 350.0,
		UMaterialInterface* MarkingMaterial = nullptr,
		double MarkingWidth = 15.0,
		bool bRebuild = false);

	/**
	 * Deletes roads and removes their endpoint links from neighbouring roads.
	 * @param Roads Roads to delete.
	 * @param bRebuild Start a full rebuild of the affected networks after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult DeleteRoads(const TArray<ADynamicRoad*>& Roads, bool bRebuild = false);

	/**
	 * Duplicates a road with an XY offset (parallel carriageways, frontage roads).
	 * @param Road Road to copy.
	 * @param Offset XY offset in cm applied to every control point.
	 * @param bRebuild Start a rebuild after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult DuplicateRoad(ADynamicRoad* Road, FVector2D Offset, bool bRebuild = false);

	/**
	 * Turns two road ends that meet at an angle (FindJunctionIssues kinds UnjoinedCorner and SharpLinkedCorner) into a
	 * rounded corner. With the same preset on both roads, B is merged into A through the corner and deleted; links at
	 * B's far end move to A. With different presets, both ends are pulled back from the corner and joined by a curved
	 * connector road linked at both ends; the lane layout changes at those links.
	 * @param A One road end at the corner. With the same preset this road is kept.
	 * @param B The other road end at the corner.
	 * @param TurnRadius Corner turn radius in cm (1000-100000).
	 * @param bRebuild Start a full rebuild of the network after the edit.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDEditResult CloseCorner(
		const FRoadBLDEndpointRef& A,
		const FRoadBLDEndpointRef& B,
		double TurnRadius = 3000.0,
		bool bRebuild = false);
};
