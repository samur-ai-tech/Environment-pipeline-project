// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"

#include "RoadBLDToolsetTypes.generated.h"

class ADynamicRoad;

/** Side of a road relative to its drawing direction (first control point -> last control point). */
UENUM(BlueprintType)
enum class ERoadBLDSide : uint8
{
	Left,
	Right,
	/** Both sides. Only accepted by tools that document it. */
	Both
};

/** How ConnectEndpoints joins two road ends. */
UENUM(BlueprintType)
enum class ERoadBLDConnectMode : uint8
{
	/** Link when the endpoints already touch (within LinkTolerance), otherwise build a bridging road. */
	Auto,
	/** Only link endpoints that already touch. Fails otherwise. */
	Link,
	/** Always create a new road between the two endpoints and link both of its ends. */
	Bridge
};

UENUM(BlueprintType)
enum class ERoadBLDRebuildState : uint8
{
	Running,
	Succeeded,
	Aborted,
	Failed
};

UENUM(BlueprintType)
enum class ERoadBLDStyleAssetKind : uint8
{
	/** Blueprint subclasses of URoadBLDSidewalkPreset. Use with SetSidewalk and preset specs. */
	SidewalkPreset,
	/** Blueprint subclasses of UCrossingStyle (crosswalk styles for automatic crossings). */
	CrossingStyle,
	/** Blueprint subclasses of URoadModuleObject (curbs, gutters, guardrails, barriers, lights, bridge supports). */
	RoadModule,
	/** Blueprint subclasses of ULanePreset. */
	LanePreset,
	/** Materials and material instances (road surfaces, sidewalks, lane markings). */
	Material,
	/** Static meshes usable by prop spawners. */
	StaticMesh,
	/** Float curves usable as road edge-detail profiles. */
	Curve
};

UENUM(BlueprintType)
enum class ERoadBLDCaptureView : uint8
{
	/** Bird's-eye view at 50 degrees framing the target. */
	Oblique,
	/** Straight-down view framing the target. */
	TopDown,
	/** Keep the current editor camera. */
	Current
};

USTRUCT(BlueprintType)
struct FRoadBLDActorRef
{
	GENERATED_BODY()

	/** Canonical actor name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Name;

	/** Human-readable actor label shown in the World Outliner. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Label;

	/** Object path. Pass it back as {"refPath": RefPath} for actor parameters of other tools. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString RefPath;

	/** Short class name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Class;
};

/** A road control point. All units are Unreal centimeters. */
USTRUCT(BlueprintType)
struct FRoadBLDPoint
{
	GENERATED_BODY()

	/** World-space location. Z sets the road elevation at this point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Location = FVector::ZeroVector;

	/** Maximum turn radius used to round the corner at this point, in cm. Valid range is 1000-100000. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double TurnRadius = 2000.0;
};

/** Identifies one end of a road. */
USTRUCT(BlueprintType)
struct FRoadBLDEndpointRef
{
	GENERATED_BODY()

	/** The road, as {"refPath": "..."}. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TObjectPtr<ADynamicRoad> Road = nullptr;

	/** True for the first control point, false for the last control point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bStart = true;
};

USTRUCT(BlueprintType)
struct FRoadBLDLinkInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Road;

	/** True when the link targets the linked road's start point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bLinkedToStart = true;

	/** Lateral offset (cm) from the linked road's endpoint along its right axis. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double RightAxisOffset = 0.0;
};

USTRUCT(BlueprintType)
struct FRoadBLDEndpointInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Road;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bStart = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Location = FVector::ZeroVector;

	/** Unit direction pointing away from the road at this end. Continue a road along this direction. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector OutwardDirection = FVector::ZeroVector;

	/** Endpoint links. Linked endpoints join smoothly without forming an intersection. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDLinkInfo> Links;
};

USTRUCT(BlueprintType)
struct FRoadBLDLaneInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	ERoadBLDSide Side = ERoadBLDSide::Left;

	/** Lane index on its side. 0 is next to the lane midpoint (centerline); higher indices are further out. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 Index = 0;

	/** Normal, Parking, Border, Restricted, Shoulder, CenterTurn or Median. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Type;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double WidthAtStart = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double WidthAtEnd = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double MinWidth = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double MaxWidth = 0.0;

	/** Material of the marking on this lane's outer edge, empty when unmarked. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString OuterMarkingMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double OuterMarkingWidth = 0.0;
};

USTRUCT(BlueprintType)
struct FRoadBLDSidewalkInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	ERoadBLDSide Side = ERoadBLDSide::Left;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bPresent = false;

	/** Sidewalk preset class path, when known. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString PresetId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Width = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double ZOffset = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 PartitionCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Material;
};

USTRUCT(BlueprintType)
struct FRoadBLDRoadSummary
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Actor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString PresetId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString PresetName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Length = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 LeftLaneCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 RightLaneCount = 0;
};

USTRUCT(BlueprintType)
struct FRoadBLDRoadInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Actor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Network;

	/** Class path of the preset the road was initialized from. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString PresetId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString PresetName;

	/** Centerline length in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Length = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector BoundsMin = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector BoundsMax = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDPoint> ControlPoints;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDLaneInfo> LeftLanes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDLaneInfo> RightLanes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDSidewalkInfo LeftSidewalk;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDSidewalkInfo RightSidewalk;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDEndpointInfo Start;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDEndpointInfo End;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bConformToLandscape = false;

	/** Ids of junctions (from ListJunctions) that include this road. Requires a completed rebuild. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> JunctionIds;
};

USTRUCT(BlueprintType)
struct FRoadBLDNetworkInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Actor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 RoadCount = 0;

	/** Sum of road lengths in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double CumulativeLength = 0.0;

	/** True when the network has edits that are not built yet. Call Rebuild. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bStale = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bRebuildInProgress = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector BoundsMin = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector BoundsMax = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 JunctionCount = 0;

	/** Road ends without an endpoint link. Candidates for ConnectEndpoints. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 UnlinkedEndpointCount = 0;

	/** Road summaries, capped by MaxRoads. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDRoadSummary> Roads;
};

USTRUCT(BlueprintType)
struct FRoadBLDJunctionInfo
{
	GENERATED_BODY()

	/** Stable id for this junction; pass to CaptureViewport. It is the generated geometry actor's path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector BoundsMin = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector BoundsMax = FVector::ZeroVector;

	/** Roads that meet in this junction. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDActorRef> Roads;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 CornerCount = 0;

	/** Curb corner radii in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<double> CornerRadii;
};

USTRUCT(BlueprintType)
struct FRoadBLDJunctionList
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Network;

	/** Junctions only reflect the last completed rebuild. When true, rebuild first. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bStale = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bRebuildInProgress = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDJunctionInfo> Junctions;
};

USTRUCT(BlueprintType)
struct FRoadBLDRoadSample
{
	GENERATED_BODY()

	/** Distance along the centerline in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Distance = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Location = FVector::ZeroVector;

	/** Unit travel direction at this distance. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Direction = FVector::ZeroVector;

	/** Unit vector pointing to the road's right side. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Right = FVector::ZeroVector;

	/** Paved width left of the centerline, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double LeftWidth = 0.0;

	/** Paved width right of the centerline, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double RightWidth = 0.0;
};

USTRUCT(BlueprintType)
struct FRoadBLDPresetTraits
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 LeftDrivingLanes = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 RightDrivingLanes = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bOneWay = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasMedian = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasCenterTurnLane = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasParking = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasShoulder = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasRestrictedLane = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasLeftSidewalk = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bHasRightSidewalk = false;

	/** Sum of all lane widths in cm, excluding sidewalks. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double TotalLaneWidth = 0.0;
};

USTRUCT(BlueprintType)
struct FRoadBLDPresetSummary
{
	GENERATED_BODY()

	/** Preset class path. Pass it as the Preset parameter of authoring tools. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString AssetPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Name;

	/** Region such as USA or UK; Unspecified when unknown. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Region;

	/** Other, Street, Freeway, Railway or Walkway. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Category;

	/** Authored tags. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> Tags;

	/** Tags derived from the lane layout, such as two-way, 4-lane, median, parking, sidewalks. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> DerivedTags;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDPresetTraits Traits;

	/** True for presets created by this toolset under /Game/RoadBLD_Generated. Only these can be updated. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bIsGenerated = false;
};

USTRUCT(BlueprintType)
struct FRoadBLDStyleAssetInfo
{
	GENERATED_BODY()

	/** Asset or class path to reference in preset specs. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Class;

	/** True for RoadBLD reference kit assets (sample presets, sidewalks, crossings, modules, masters and sample materials) worth studying or reusing. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bIsRecommended = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Note;
};

USTRUCT(BlueprintType)
struct FRoadBLDMaterialParameterInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Name;

	/** Scalar, Vector, Texture or StaticSwitch. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Type;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Group;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double ScalarDefault = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FLinearColor VectorDefault = FLinearColor::Black;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString TextureDefault;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bSwitchDefault = false;
};

USTRUCT(BlueprintType)
struct FRoadBLDEditResult
{
	GENERATED_BODY()

	/** Roads created or modified by the call. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDActorRef> Roads;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Network;

	/** True when geometry, junctions and markings are not built yet. Call Rebuild when your batch of edits is done. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bNeedsRebuild = true;

	/** Rebuild job started by this call (bRebuild=true). Poll with RebuildStatus or WaitForRebuild. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString RebuildJobId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FString> Warnings;
};

/** A road end that RoadBLD cannot build cleanly: a broken junction arm or a corner between two road ends. */
USTRUCT(BlueprintType)
struct FRoadBLDJunctionIssue
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef Road;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bStart = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Location = FVector::ZeroVector;

	/** The road the end runs into. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FRoadBLDActorRef OtherRoad;

	/** Corner kinds only: true when OtherRoad meets at its start. Pass Road/bStart and OtherRoad/bOtherStart to CloseCorner. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bOtherStart = true;

	/**
	 * StubPastRoad (ends inside or just beyond the other road), ShortOfRoad (stops just before it), UnjoinedCorner
	 * (two unlinked road ends meet at an angle) or SharpLinkedCorner (two linked road ends meet at an angle).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Kind;

	/** Corner kinds only: heading change in degrees when driving from Road into OtherRoad. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double TurnAngle = 0.0;

	/** Distance in cm from the other road's outer edge to the end. Negative when the end is inside the road. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double EdgeDistance = 0.0;

	/** End location on the other road's centerline (T junction). Apply with SetControlPoints. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector SuggestedLocation = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Suggestion;
};

/** Straight road grid, laid out in a local frame rotated by RotationYaw around Origin. */
USTRUCT(BlueprintType)
struct FRoadBLDGridSpec
{
	GENERATED_BODY()

	/** Grid corner (local X=0, Y=0) in world space. Z is ground level; roads are placed 5 cm above it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Origin = FVector::ZeroVector;

	/** Grid extent along local X, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double SizeX = 40000.0;

	/** Grid extent along local Y, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double SizeY = 40000.0;

	/** Distance between roads that run along local Y, in cm (block length). Typical city blocks: 8000-15000. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double SpacingX = 10000.0;

	/** Distance between roads that run along local X, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double SpacingY = 10000.0;

	/** Rotation of the grid around Origin, in degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double RotationYaw = 0.0;

	/** Include the boundary, built as one closed loop with rounded corners. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bIncludePerimeter = true;

	/**
	 * Turn radius of the perimeter corners in cm (1000-100000). Reduced when a grid line would end inside a rounded
	 * corner.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double PerimeterCornerRadius = 3000.0;

	/** When > 0, every Nth grid line (counting from the origin) uses the arterial preset. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 ArterialEvery = 0;

	/**
	 * Extends every road past the grid boundary by this distance in cm (0 ends roads flush at the perimeter). With the
	 * perimeter included, use 0 or a real crossing arm (at least ~20 m); shorter values are reset to 0.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Overhang = 0.0;
};

/** Distance range along a road. StartDistance and EndDistance both 0 means the whole road. */
USTRUCT(BlueprintType)
struct FRoadBLDRange
{
	GENERATED_BODY()

	/** Start distance along the road in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double StartDistance = 0.0;

	/** End distance along the road in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double EndDistance = 0.0;

	/** Taper length before StartDistance and after EndDistance, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Transition = 1500.0;
};

/** A suspicious triangle cluster in generated road geometry (stretched or sliver triangles). */
USTRUCT(BlueprintType)
struct FRoadBLDGeometryIssue
{
	GENERATED_BODY()

	/** Center of the flagged triangles. Pass it to CaptureArea to look at the problem. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FVector Location = FVector::ZeroVector;

	/** Radius in cm that covers the flagged triangles. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double Radius = 0.0;

	/** Sliver (a needle-thin triangle) or StretchedTriangle (an edge far longer than the road is wide). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Kind;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 TriangleCount = 0;

	/** Smallest triangle angle in degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double MinAngle = 0.0;

	/** Longest triangle edge in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double LongestEdge = 0.0;

	/** Generated geometry actor that holds the triangles. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString GeometryActor;

	/** Roads the geometry was built from. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDActorRef> Roads;

	/** Road ends near the problem, the usual cause (see FindJunctionIssues and CloseCorner). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDEndpointInfo> NearbyEnds;
};

USTRUCT(BlueprintType)
struct FRoadBLDRebuildStatus
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString JobId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	ERoadBLDRebuildState State = ERoadBLDRebuildState::Running;

	/** True when a wait returned because its timeout elapsed. The job keeps running; poll RebuildStatus. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	bool bTimedOut = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	double ElapsedMs = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	TArray<FRoadBLDActorRef> Networks;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	int32 RemainingNetworks = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RoadBLDToolset")
	FString Message;
};
