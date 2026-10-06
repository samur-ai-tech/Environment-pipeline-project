// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolCallAsyncResult.h"
#include "ToolsetRegistry/ToolsetImage.h"

#include "BLDToolsetTypes.generated.h"

/** Reference to an actor returned by BLD toolsets. */
USTRUCT(BlueprintType)
struct BLDTOOLSETCOMMON_API FBLDActorRef
{
	GENERATED_BODY()

	/** Canonical actor name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Name;

	/** Human-readable actor label shown in the World Outliner. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Label;

	/** Object path. Pass it back as {"refPath": RefPath} for actor parameters of other tools. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString RefPath;

	/** Short class name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Class;
};

UENUM(BlueprintType)
enum class EBLDJobState : uint8
{
	Running,
	Succeeded,
	Aborted,
	Failed
};

/** State of a long-running toolset job (downloads, generation, imagery imports). */
USTRUCT(BlueprintType)
struct BLDTOOLSETCOMMON_API FBLDJobStatus
{
	GENERATED_BODY()

	/** Pass to the owning toolset's GetJob, WaitForJob or CancelJob. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString JobId;

	/** What the job does, such as TwinBLD.FetchOsm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Kind;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	EBLDJobState State = EBLDJobState::Running;

	/** True when a wait returned because its timeout elapsed. The job keeps running; wait again or poll. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	bool bTimedOut = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	double ElapsedMs = 0.0;

	/** Current stage name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Stage;

	/** Rough completion from 0 to 1, when the job can estimate it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	double Progress = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Message;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FString> Warnings;

	/** Most recent log lines, oldest first. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FString> Log;

	/** Job-specific result as a JSON object string, once the job has produced one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString ResultJson;
};

/** A validation problem tied to a spec field path such as BuildingRules[2].StyleClass. */
USTRUCT(BlueprintType)
struct BLDTOOLSETCOMMON_API FBLDValidationIssue
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Field;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Message;
};


UENUM(BlueprintType)
enum class EBLDIssueSeverity : uint8
{
	/** Blocks correct generation or leaves the scene unusable. */
	Error,
	/** Scene works but is likely wrong, incomplete, or fragile. */
	Warning,
	/** Worth knowing; often intentional. */
	Info
};

/**
 * Shared validation issue for WorldBLD agent validation loops (City / Road / Twin).
 * Prefer this shape over product-specific issue structs when aggregating or testing.
 */
USTRUCT(BlueprintType)
struct BLDTOOLSETCOMMON_API FBLDIssue
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	EBLDIssueSeverity Severity = EBLDIssueSeverity::Warning;

	/** Product or subsystem that produced the issue (CityBLD, RoadBLD, TwinBLD, WorldBLD). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Source;

	/** Stable machine code such as BlockMissingDistrict or UnjoinedCorner. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Code;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Message;

	/** Primary actor or asset the issue is about. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FBLDActorRef Subject;

	/** Secondary actor when the issue is a relationship (overlap, corner pair). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FBLDActorRef Other;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FVector Location = FVector::ZeroVector;

	/** Suggested capture / inspect radius in cm. 0 when not spatial. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	double Radius = 0.0;

	/** Suggested next tool or fix. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString Fix;
};

/** Aggregated validation report with a shared Issues array. */
USTRUCT(BlueprintType)
struct BLDTOOLSETCOMMON_API FBLDIssueReport
{
	GENERATED_BODY()

	/** Most severe first, then by Source and Code. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FBLDIssue> Issues;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	int32 ErrorCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	int32 WarningCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	int32 InfoCount = 0;

	/** True when ErrorCount is 0 and no source reported itself not-ready. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	bool bReady = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FString> Notes;
};

/** Post-op readiness before capture / further edits. */
USTRUCT(BlueprintType)
struct BLDTOOLSETCOMMON_API FBLDPostOpReadiness
{
	GENERATED_BODY()

	/** True when it is safe to capture or continue mutating. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	bool bReady = true;

	/** True when a RoadBLD (or similar) rebuild is still running. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	bool bRebuildInProgress = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FString> BlockingReasons;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FString> Notes;
};

/** Result of one validation loop pass across enabled WorldBLD toolsets. */
USTRUCT(BlueprintType)
struct BLDTOOLSETCOMMON_API FBLDValidationLoopResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FBLDIssueReport Report;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FBLDPostOpReadiness Readiness;

	/** Tool names that contributed issues (e.g. CityBLD.ValidateCity). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FString> SourcesChecked;

	/** Tool names skipped because the plugin/toolset was unavailable. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FString> SourcesSkipped;

	/** Optional evidence capture when bCaptureEvidence was requested and a spatial issue existed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FString EvidenceNote;
};

UENUM(BlueprintType)
enum class EBLDCaptureView : uint8
{
	/** Bird's-eye view at 50 degrees framing the target. */
	Oblique,
	/** Straight-down view framing the target. */
	TopDown,
	/** Keep the current editor camera. */
	Current,
	/** Use an explicit camera location and rotation. */
	Pose
};

USTRUCT(BlueprintType)
struct BLDTOOLSETCOMMON_API FBLDCaptureResult
{
	GENERATED_BODY()

	/** PNG image, base64 encoded. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FToolsetImage Image;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FVector CameraLocation = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FRotator CameraRotation = FRotator::ZeroRotator;

	/** World bounds that were framed, when a target was framed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FVector BoundsMin = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	FVector BoundsMax = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BLDToolset")
	TArray<FString> Warnings;
};

/** Async tool result that completes with a job status. */
UCLASS()
class BLDTOOLSETCOMMON_API UBLDJobAsyncResult : public UToolCallAsyncResult
{
	GENERATED_BODY()

public:
	bool SetValue(const FBLDJobStatus& InValue)
	{
		FBLDJobStatus ValueCopy = InValue;
		return MaybeBroadcastSuccessfulCompletion(MoveTemp(ValueCopy), Value);
	}

	UPROPERTY()
	FBLDJobStatus Value;
};

/** Async tool result that completes with a viewport capture. */
UCLASS()
class BLDTOOLSETCOMMON_API UBLDCaptureAsyncResult : public UToolCallAsyncResult
{
	GENERATED_BODY()

public:
	bool SetValue(const FBLDCaptureResult& InValue)
	{
		FBLDCaptureResult ValueCopy = InValue;
		return MaybeBroadcastSuccessfulCompletion(MoveTemp(ValueCopy), Value);
	}

	UPROPERTY()
	FBLDCaptureResult Value;
};
