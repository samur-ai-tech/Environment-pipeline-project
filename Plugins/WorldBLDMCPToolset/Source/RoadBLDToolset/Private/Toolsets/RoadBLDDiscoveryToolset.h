// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/RoadBLDToolsetTypes.h"
#include "Presets/RoadBLDPresetSpec.h"
#include "Templates/SubclassOf.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "RoadBLDDiscoveryToolset.generated.h"

class ADynamicRoad;
class ADynamicRoadNetwork;
class UDynamicRoadDrawPreset;
class UMaterialInterface;

USTRUCT(BlueprintType)
struct FRoadBLDPresetDescription
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDPresetSummary Summary;

	/** Complete spec of the preset. Modify it and pass it to CreatePresetFromSpec to derive a new style. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDPresetSpec Spec;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasLeftSidewalk = false;

	/** Settings of the left sidewalk preset; copy into Spec.LeftSidewalk.Inline to customize it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDSidewalkSpec LeftSidewalk;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasRightSidewalk = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDSidewalkSpec RightSidewalk;
};

/**
 * Discover RoadBLD road presets, style assets and the current road network (roads, lanes, junctions, endpoints).
 * Typical workflow: ListPresets -> DescribePreset -> (RoadBLDPresetToolset for new styles) -> RoadBLDAuthoringToolset
 * to place roads -> FindJunctionIssues (fix stubs with SetControlPoints, corners with CloseCorner) ->
 * RoadBLDBuildToolset.Rebuild -> FindGeometryIssues -> RoadBLDFeedbackToolset.CaptureViewport to check the result.
 * Two roads may only end at the same point if they continue straight. For a turn, draw one road through the corner
 * with a TurnRadius, or call CloseCorner.
 * If the user reports artifacts in existing roads (gaps, missing or distorted meshes, floating pieces), start with
 * RoadBLDBuildToolset.Rebuild bForceRebuildAll=true on that network before inspecting or editing anything.
 * For RoadBLD / WorldBLD packaging, cook, compile, or plugin-load errors (missing WorldBLD_Content, Unable to load plugin,
 * GeometryScripting), call WorldBLDToolset.UWorldBLDToolset.GetPackagingGuide — do not treat those as road-content issues.
 * Distances are Unreal centimeters; +X forward, +Y right, +Z up. Actor parameters take {"refPath": "..."}.
 * For style work, start from the RoadBLD reference kit: the RoadKit_USA sample presets under
 * /RoadBLD/RoadBLD/RoadKit_USA/Presets (full list in RoadBLDPresetToolset's description) and ListStyleAssets entries
 * with bIsRecommended=true (sample sidewalks, crossings, lanes, modules, PCG graphs, master and sample materials).
 */
UCLASS(BlueprintType, MinimalAPI)
class URoadBLDDiscoveryToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	// No Category specifier on ListPresets: the registry reads a parameter's default from function metadata with the
	// same name first, so Category = "..." would become the default of the Category parameter.
	/**
	 * Lists road presets in the project and RoadBLD content. Every filter is optional; Any matches everything.
	 * @param Region Region filter such as USA or UK (case-insensitive).
	 * @param Category Category filter: Street, Freeway, Walkway, Railway or Other.
	 * @param Tags Comma-separated tags that must all match authored or derived tags (e.g. "two-way, parking").
	 * @param Query Text matched against name, description, tags and id.
	 * @return Matching presets. Use Id as the Preset parameter of other tools.
	 */
	UFUNCTION(meta = (AICallable))
	static TArray<FRoadBLDPresetSummary> ListPresets(
		const FString& Region = TEXT("Any"),
		const FString& Category = TEXT("Any"),
		const FString& Tags = TEXT("Any"),
		const FString& Query = TEXT("Any"));

	/**
	 * Describes a preset in full: lane layout, markings, materials, modules, props and sidewalks, as an editable spec.
	 * @param Preset Preset Id from ListPresets.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDPresetDescription DescribePreset(TSubclassOf<UDynamicRoadDrawPreset> Preset);

	/**
	 * Lists assets that preset specs can reference: sidewalk presets, crossing styles, road modules, lane presets,
	 * materials (masters flagged bIsRecommended), static meshes and curves.
	 * @param Kind Asset kind to list.
	 * @param Query Case-insensitive text filter on name and path. Any matches everything.
	 * @param MaxResults Maximum entries returned (1-1000).
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static TArray<FRoadBLDStyleAssetInfo> ListStyleAssets(ERoadBLDStyleAssetKind Kind, const FString& Query = TEXT("Any"), int32 MaxResults = 200);

	/**
	 * Lists the parameters of a material so material variants can override them.
	 * @param Material Material or material instance, as {"refPath": "/RoadBLD/.../M_RoadBLD_Asphalt_Master.M_RoadBLD_Asphalt_Master"}.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static TArray<FRoadBLDMaterialParameterInfo> ListMaterialParameters(UMaterialInterface* Material);

	/**
	 * Describes road networks: road count, length, bounds, build state, junction count and road summaries.
	 * @param Network Optional network. When omitted, every network in the level is described.
	 * @param MaxRoads Maximum road summaries per network.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static TArray<FRoadBLDNetworkInfo> DescribeNetwork(ADynamicRoadNetwork* Network = nullptr, int32 MaxRoads = 200);

	/**
	 * Describes a road: preset, control points, per-lane widths and types, sidewalks, endpoint links and junctions.
	 * @param Road The road actor.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static FRoadBLDRoadInfo DescribeRoad(ADynamicRoad* Road);

	/**
	 * Lists junctions (intersections) produced by the last rebuild, with their roads and curb corner radii.
	 * Junctions form automatically wherever roads overlap; they are not authored directly.
	 * @param Network Optional network. When omitted, every network is listed.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static TArray<FRoadBLDJunctionList> ListJunctions(ADynamicRoadNetwork* Network = nullptr);

	/**
	 * Lists road endpoints with their location, outward direction and links.
	 * @param Network Optional network. When omitted, every network is listed.
	 * @param bUnlinkedOnly Only return endpoints without links (dead ends and connection candidates).
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static TArray<FRoadBLDEndpointInfo> ListEndpoints(ADynamicRoadNetwork* Network = nullptr, bool bUnlinkedOnly = true);

	/**
	 * Finds road ends that would build broken geometry. StubPastRoad / ShortOfRoad: an end inside, just past or just
	 * short of another road; fix with SetControlPoints, moving the end to SuggestedLocation or well past the other
	 * road. UnjoinedCorner / SharpLinkedCorner: two road ends meet at an angle, which builds stretched triangles; fix
	 * with CloseCorner. Works on authored roads; no rebuild needed.
	 * @param Network Optional network. When omitted, every network is checked.
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static TArray<FRoadBLDJunctionIssue> FindJunctionIssues(ADynamicRoadNetwork* Network = nullptr);

	/**
	 * Scans the generated road meshes of the last rebuild for stretched and sliver triangles, the visible symptom of
	 * unjoined corners and broken junction arms. Look at each issue with RoadBLDFeedbackToolset.CaptureArea
	 * (Center=Location), then fix the nearby road ends (FindJunctionIssues, CloseCorner) and rebuild.
	 * @param Network Optional network. When omitted, every network is checked.
	 * @param MaxIssues Maximum issues returned (1-200).
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static TArray<FRoadBLDGeometryIssue> FindGeometryIssues(ADynamicRoadNetwork* Network = nullptr, int32 MaxIssues = 50);

	/**
	 * Samples a road's centerline: locations, directions and paved widths at regular intervals.
	 * Useful to place side roads, driveways or props relative to an existing road.
	 * @param Road The road actor.
	 * @param Interval Distance between samples in cm (minimum 100; at most 1000 samples are returned).
	 */
	UFUNCTION(meta = (AICallable), Category = "RoadBLDToolset")
	static TArray<FRoadBLDRoadSample> SampleRoad(ADynamicRoad* Road, double Interval = 1000.0);
};
