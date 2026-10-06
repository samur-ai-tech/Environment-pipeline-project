// Copyright WorldBLD LLC. All rights reserved.

#include "Misc/AutomationTest.h"

#include "Common/RoadBLDToolsetUtils.h"
#include "Containers/Ticker.h"
#include "Dom/JsonObject.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "Engine/Blueprint.h"
#include "Engine/World.h"
#include "ObjectTools.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Toolsets/RoadBLDAuthoringToolset.h"
#include "Toolsets/RoadBLDBuildToolset.h"
#include "Toolsets/RoadBLDDiscoveryToolset.h"
#include "Toolsets/RoadBLDFeedbackToolset.h"
#include "Toolsets/RoadBLDPresetToolset.h"
#include "ToolsetRegistry/ToolCallAsyncResultString.h"
#include "ToolsetRegistry/UToolsetRegistry.h"
#include "UObject/StrongObjectPtr.h"

#if WITH_DEV_AUTOMATION_TESTS

/**
 * Drives tools through the toolset registry with JSON arguments, the same path the MCP server uses, so schema
 * defaults, optional parameters and struct conversion are covered.
 */
namespace RoadBLDToolsetRegistryTestPrivate
{
	const TCHAR* StreetPresetPath = TEXT("/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Street_2Lane.RP_Default_USA_Street_2Lane_C");
	const TCHAR* UpdateTestPresetName = TEXT("AITest_RegistryUpdate");

	/** Errors produced by the registry's argument handling rather than by the tool itself. */
	const TCHAR* ParameterErrorMarkers[] =
	{
		TEXT("required by the function input schema"),
		TEXT("needs a default value"),
		TEXT("could not convert incoming function input params"),
		TEXT("Parameter error"),
	};

	struct FToolResult
	{
		bool bComplete = false;
		FString Error;
		TSharedPtr<FJsonValue> Value;

		bool Succeeded() const
		{
			return bComplete && Error.IsEmpty() && Value.IsValid();
		}

		bool IsParameterError() const
		{
			for (const TCHAR* Marker : ParameterErrorMarkers)
			{
				if (Error.Contains(Marker))
				{
					return true;
				}
			}
			return false;
		}

		TSharedPtr<FJsonObject> Object() const
		{
			const TSharedPtr<FJsonObject>* Result = nullptr;
			return Value.IsValid() && Value->TryGetObject(Result) ? *Result : nullptr;
		}

		TArray<TSharedPtr<FJsonValue>> Array() const
		{
			const TArray<TSharedPtr<FJsonValue>>* Result = nullptr;
			return Value.IsValid() && Value->TryGetArray(Result) ? *Result : TArray<TSharedPtr<FJsonValue>>();
		}
	};

	FString GetToolsetName(const UClass* ToolsetClass)
	{
		// Matches the registry's naming: "<module>.<class name>".
		return FString::Printf(TEXT("%s.%s"),
			*FPackageName::GetShortName(ToolsetClass->GetOutermost()->GetName()),
			*ToolsetClass->GetName());
	}

	FString ToJsonString(const TSharedRef<FJsonObject>& Object)
	{
		FString Json;
		const TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
			TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Json);
		FJsonSerializer::Serialize(Object, Writer);
		return Json;
	}

	void ReadResult(const UToolCallAsyncResultString* Async, FToolResult& OutResult)
	{
		OutResult.bComplete = Async->bIsComplete;
		OutResult.Error = Async->Error;
		if (!OutResult.bComplete || !OutResult.Error.IsEmpty())
		{
			return;
		}

		TSharedPtr<FJsonObject> Envelope;
		if (FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Async->Value), Envelope) && Envelope.IsValid())
		{
			OutResult.Value = Envelope->TryGetField(TEXT("returnValue"));
		}
		if (!OutResult.Value.IsValid())
		{
			OutResult.Error = FString::Printf(TEXT("Unparseable tool result: %s"), *Async->Value);
		}
	}

	/** Runs a synchronous tool; its result is complete when the registry returns. */
	FToolResult CallTool(const UClass* ToolsetClass, const FString& Tool, const TSharedRef<FJsonObject>& Arguments)
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;
		const UToolCallAsyncResultString* Async = UToolsetRegistry::ExecuteTool(GetToolsetName(ToolsetClass), Tool, ToJsonString(Arguments));
		FToolResult Result;
		ReadResult(Async, Result);
		if (!Result.bComplete)
		{
			Result.Error = TEXT("Tool did not complete synchronously.");
		}
		return Result;
	}

	FToolResult CallTool(const UClass* ToolsetClass, const FString& Tool, const FString& ArgumentsJson)
	{
		TSharedPtr<FJsonObject> Arguments;
		if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(ArgumentsJson), Arguments) || !Arguments.IsValid())
		{
			FToolResult Result;
			Result.bComplete = true;
			Result.Error = FString::Printf(TEXT("Test JSON does not parse: %s"), *ArgumentsJson);
			return Result;
		}
		return CallTool(ToolsetClass, Tool, Arguments.ToSharedRef());
	}

	/** Runs an async tool and calls OnDone once it completes (or after TimeoutSeconds). */
	void CallToolAsync(
		const UClass* ToolsetClass,
		const FString& Tool,
		const FString& ArgumentsJson,
		const double TimeoutSeconds,
		TFunction<void(const FToolResult&)> OnDone)
	{
		TStrongObjectPtr<UToolCallAsyncResultString> Async;
		{
			RoadBLDToolset::FScopedTestAuthorization Authorization;
			Async.Reset(UToolsetRegistry::ExecuteTool(GetToolsetName(ToolsetClass), Tool, ArgumentsJson));
		}

		const double Deadline = FPlatformTime::Seconds() + TimeoutSeconds;
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda(
			[Async, Deadline, OnDone = MoveTemp(OnDone)](float) mutable
			{
				FToolResult Result;
				ReadResult(Async.Get(), Result);
				if (!Result.bComplete && FPlatformTime::Seconds() < Deadline)
				{
					return true;
				}
				if (!Result.bComplete)
				{
					Result.Error = TEXT("Timed out waiting for the tool.");
				}
				OnDone(Result);
				return false;
			}));
	}

	FString RefJson(const FString& Path)
	{
		return FString::Printf(TEXT("{\"refPath\": \"%s\"}"), *Path);
	}

	FString GetRefPath(const TSharedPtr<FJsonObject>& ActorRef)
	{
		return ActorRef.IsValid() ? ActorRef->GetStringField(TEXT("refPath")) : FString();
	}

	FString GetStreetPresetId()
	{
		return StreetPresetPath;
	}

	double GetRightLaneWidth(const FToolResult& RoadInfo, const TCHAR* Field)
	{
		const TSharedPtr<FJsonObject> Info = RoadInfo.Object();
		const TArray<TSharedPtr<FJsonValue>>* Lanes = nullptr;
		if (!Info.IsValid() || !Info->TryGetArrayField(TEXT("rightLanes"), Lanes) || Lanes->Num() == 0)
		{
			return -1.0;
		}
		return (*Lanes)[0]->AsObject()->GetNumberField(Field);
	}
}

BEGIN_DEFINE_SPEC(
	FRoadBLDToolsetRegistrySpec,
	TEXT("AI.Toolsets.WorldBLD.RoadBLDToolset.Registry"),
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
	TWeakObjectPtr<ADynamicRoadNetwork> Network;
	FString NetworkJson;

	/** Creates a straight road through the registry with only the required arguments. */
	FString CreateStraightRoad(double Y);
END_DEFINE_SPEC(FRoadBLDToolsetRegistrySpec)

FString FRoadBLDToolsetRegistrySpec::CreateStraightRoad(const double Y)
{
	using namespace RoadBLDToolsetRegistryTestPrivate;

	// Network may be omitted when the test network is the only one in the level.
	const FString NetworkArgument = RoadBLDToolset::GetNetworks().Num() > 1
		? FString::Printf(TEXT(", \"network\": %s"), *NetworkJson)
		: FString();
	const FToolResult Result = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("CreateRoad"), FString::Printf(
		TEXT("{\"preset\": %s, \"points\": [{\"location\": {\"x\": 0, \"y\": %f, \"z\": 0}}, {\"location\": {\"x\": 12000, \"y\": %f, \"z\": 0}}]%s}"),
		*RefJson(GetStreetPresetId()), Y, Y, *NetworkArgument));
	if (!TestTrue(FString::Printf(TEXT("CreateRoad with required arguments succeeds (%s)"), *Result.Error), Result.Succeeded()))
	{
		return FString();
	}

	const TArray<TSharedPtr<FJsonValue>>* Roads = nullptr;
	if (!TestTrue(TEXT("CreateRoad returns roads"), Result.Object()->TryGetArrayField(TEXT("roads"), Roads) && Roads->Num() == 1))
	{
		return FString();
	}
	return GetRefPath((*Roads)[0]->AsObject());
}

void FRoadBLDToolsetRegistrySpec::Define()
{
	using namespace RoadBLDToolsetRegistryTestPrivate;

	BeforeEach([this]()
	{
		RoadBLDToolset::FScopedTestAuthorization Authorization;
		const FRoadBLDActorRef NetworkRef = URoadBLDAuthoringToolset::CreateNetwork(TEXT("AITest_RegistryNetwork"));
		Network = FindObject<ADynamicRoadNetwork>(nullptr, *NetworkRef.RefPath);
		NetworkJson = RefJson(NetworkRef.RefPath);
		TestTrue(TEXT("Network created"), Network.IsValid());
	});

	AfterEach([this]()
	{
		if (ADynamicRoadNetwork* TestNetwork = Network.Get())
		{
			TestNetwork->AbortAndWaitForPendingRebuild();
			UWorld* World = TestNetwork->GetWorld();
			const TArray<TObjectPtr<ADynamicRoad>> Roads = TestNetwork->RoadsInNetwork;
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

	Describe(TEXT("optional parameters"), [this]()
	{
		It(TEXT("ListPresets with no arguments matches the unfiltered C++ call"), [this]()
		{
			const FToolResult Result = CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("ListPresets"), TEXT("{}"));
			if (TestTrue(FString::Printf(TEXT("ListPresets {} succeeds (%s)"), *Result.Error), Result.Succeeded()))
			{
				const int32 Expected = URoadBLDDiscoveryToolset::ListPresets().Num();
				TestTrue(TEXT("Presets exist"), Expected > 0);
				TestEqual(TEXT("Same count as the C++ call"), Result.Array().Num(), Expected);
			}
		});

		It(TEXT("ListPresets with only a category filters by it"), [this]()
		{
			const FToolResult Result = CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("ListPresets"), TEXT("{\"category\": \"Street\"}"));
			if (TestTrue(FString::Printf(TEXT("ListPresets {category} succeeds (%s)"), *Result.Error), Result.Succeeded()))
			{
				const TArray<TSharedPtr<FJsonValue>> Presets = Result.Array();
				TestTrue(TEXT("Street presets exist"), Presets.Num() > 0);
				TestEqual(TEXT("Same count as the C++ call"), Presets.Num(), URoadBLDDiscoveryToolset::ListPresets(TEXT(""), TEXT("Street")).Num());
				for (const TSharedPtr<FJsonValue>& Preset : Presets)
				{
					TestEqual(TEXT("Category"), Preset->AsObject()->GetStringField(TEXT("category")), FString(TEXT("Street")));
				}
			}
		});

		It(TEXT("ListStyleAssets needs only a kind"), [this]()
		{
			const FToolResult Result = CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("ListStyleAssets"), TEXT("{\"kind\": \"SidewalkPreset\"}"));
			TestTrue(FString::Printf(TEXT("ListStyleAssets {kind} succeeds (%s)"), *Result.Error), Result.Succeeded() && Result.Array().Num() > 0);
		});

		It(TEXT("CreateRoad needs only a preset and points"), [this]()
		{
			if (Network.IsValid())
			{
				TestFalse(TEXT("Road created"), CreateStraightRoad(0.0).IsEmpty());
			}
		});

		It(TEXT("CreateRing needs only a preset and a polygon"), [this]()
		{
			if (!Network.IsValid())
			{
				return;
			}

			const FToolResult Result = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("CreateRing"), FString::Printf(
				TEXT("{\"preset\": %s, \"polygon\": [{\"x\": 0, \"y\": 0, \"z\": 0}, {\"x\": 20000, \"y\": 0, \"z\": 0}, {\"x\": 20000, \"y\": 20000, \"z\": 0}, {\"x\": 0, \"y\": 20000, \"z\": 0}]}"),
				*RefJson(GetStreetPresetId())));
			TestTrue(FString::Printf(TEXT("CreateRing succeeds (%s)"), *Result.Error), Result.Succeeded());
		});

		It(TEXT("SetLaneWidth without a range changes the whole road"), [this]()
		{
			if (!Network.IsValid())
			{
				return;
			}

			const FString RoadPath = CreateStraightRoad(10000.0);
			if (RoadPath.IsEmpty())
			{
				return;
			}

			const FString RoadArgs = FString::Printf(TEXT("{\"road\": %s}"), *RefJson(RoadPath));
			const FToolResult Before = CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("DescribeRoad"), RoadArgs);
			const double OriginalWidth = GetRightLaneWidth(Before, TEXT("widthAtStart"));
			if (!TestTrue(TEXT("Road has a right lane"), OriginalWidth > 0.0))
			{
				return;
			}

			const double NewWidth = OriginalWidth + 150.0;
			const FToolResult Edit = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("SetLaneWidth"), FString::Printf(
				TEXT("{\"road\": %s, \"side\": \"Right\", \"laneIndex\": 0, \"width\": %f}"), *RefJson(RoadPath), NewWidth));
			if (!TestTrue(FString::Printf(TEXT("SetLaneWidth without range succeeds (%s)"), *Edit.Error), Edit.Succeeded()))
			{
				return;
			}

			const FToolResult After = CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("DescribeRoad"), RoadArgs);
			TestNearlyEqual(TEXT("Width at start"), GetRightLaneWidth(After, TEXT("widthAtStart")), NewWidth, 1.0);
			TestNearlyEqual(TEXT("Width at end"), GetRightLaneWidth(After, TEXT("widthAtEnd")), NewWidth, 1.0);
			TestNearlyEqual(TEXT("Minimum width"), GetRightLaneWidth(After, TEXT("minWidth")), NewWidth, 1.0);
		});

		It(TEXT("SetLaneWidth with a range changes only that range"), [this]()
		{
			if (!Network.IsValid())
			{
				return;
			}

			const FString RoadPath = CreateStraightRoad(15000.0);
			if (RoadPath.IsEmpty())
			{
				return;
			}

			const FString RoadArgs = FString::Printf(TEXT("{\"road\": %s}"), *RefJson(RoadPath));
			const double OriginalWidth = GetRightLaneWidth(CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("DescribeRoad"), RoadArgs), TEXT("widthAtStart"));
			const FToolResult Edit = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("SetLaneWidth"), FString::Printf(
				TEXT("{\"road\": %s, \"side\": \"Right\", \"laneIndex\": 0, \"width\": %f, \"range\": {\"startDistance\": 5000, \"endDistance\": 7000}}"),
				*RefJson(RoadPath), OriginalWidth + 150.0));
			if (!TestTrue(FString::Printf(TEXT("SetLaneWidth with range succeeds (%s)"), *Edit.Error), Edit.Succeeded()))
			{
				return;
			}

			const FToolResult After = CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("DescribeRoad"), RoadArgs);
			TestNearlyEqual(TEXT("Start unchanged"), GetRightLaneWidth(After, TEXT("widthAtStart")), OriginalWidth, 1.0);
			TestNearlyEqual(TEXT("Widened inside the range"), GetRightLaneWidth(After, TEXT("maxWidth")), OriginalWidth + 150.0, 1.0);
		});

		It(TEXT("FindJunctionIssues, DescribeNetwork and ListJunctions need no arguments"), [this]()
		{
			for (const TCHAR* Tool : { TEXT("FindJunctionIssues"), TEXT("FindGeometryIssues"), TEXT("DescribeNetwork"), TEXT("ListJunctions"), TEXT("ListEndpoints") })
			{
				const FToolResult Result = CallTool(URoadBLDDiscoveryToolset::StaticClass(), Tool, TEXT("{}"));
				TestTrue(FString::Printf(TEXT("%s {} succeeds (%s)"), Tool, *Result.Error), Result.Succeeded());
			}
		});

		LatentIt(TEXT("CaptureViewport accepts no arguments"), FTimespan::FromSeconds(60), [this](const FDoneDelegate& Done)
		{
			CallToolAsync(URoadBLDFeedbackToolset::StaticClass(), TEXT("CaptureViewport"), TEXT("{}"), 45.0, [this, Done](const FToolResult& Result)
			{
				// Headless runs have no viewport; that error is fine, an argument error is not.
				TestFalse(FString::Printf(TEXT("CaptureViewport {} has no parameter error (%s)"), *Result.Error), Result.IsParameterError());
				TestTrue(TEXT("CaptureViewport completed"), Result.bComplete);
				Done.Execute();
			});
		});

		LatentIt(TEXT("CaptureArea needs only a center"), FTimespan::FromSeconds(60), [this](const FDoneDelegate& Done)
		{
			CallToolAsync(URoadBLDFeedbackToolset::StaticClass(), TEXT("CaptureArea"), TEXT("{\"center\": {\"x\": 0, \"y\": 0, \"z\": 0}}"), 45.0,
				[this, Done](const FToolResult& Result)
				{
					TestFalse(FString::Printf(TEXT("CaptureArea {center} has no parameter error (%s)"), *Result.Error), Result.IsParameterError());
					TestTrue(TEXT("CaptureArea completed"), Result.bComplete);
					Done.Execute();
				});
		});
	});

	Describe(TEXT("endpoint references"), [this]()
	{
		It(TEXT("CloseCorner accepts endpoint refs"), [this]()
		{
			if (!Network.IsValid())
			{
				return;
			}

			const FString NetworkArgument = FString::Printf(TEXT("\"network\": %s"), *NetworkJson);
			const FToolResult First = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("CreateRoad"), FString::Printf(
				TEXT("{\"preset\": %s, %s, \"points\": [{\"location\": {\"x\": 0, \"y\": 40000, \"z\": 0}}, {\"location\": {\"x\": 12000, \"y\": 40000, \"z\": 0}}]}"),
				*RefJson(GetStreetPresetId()), *NetworkArgument));
			const FToolResult Second = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("CreateRoad"), FString::Printf(
				TEXT("{\"preset\": %s, %s, \"points\": [{\"location\": {\"x\": 12000, \"y\": 40000, \"z\": 0}}, {\"location\": {\"x\": 12000, \"y\": 52000, \"z\": 0}}]}"),
				*RefJson(GetStreetPresetId()), *NetworkArgument));
			if (!TestTrue(TEXT("Roads created"), First.Succeeded() && Second.Succeeded()))
			{
				return;
			}

			const FString PathA = GetRefPath(First.Object()->GetArrayField(TEXT("roads"))[0]->AsObject());
			const FString PathB = GetRefPath(Second.Object()->GetArrayField(TEXT("roads"))[0]->AsObject());
			const FToolResult Closed = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("CloseCorner"), FString::Printf(
				TEXT("{\"a\": {\"road\": %s, \"bStart\": false}, \"b\": {\"road\": %s, \"bStart\": true}}"), *RefJson(PathA), *RefJson(PathB)));
			if (TestTrue(FString::Printf(TEXT("CloseCorner succeeds (%s)"), *Closed.Error), Closed.Succeeded()))
			{
				TestEqual(TEXT("One road left"), Closed.Object()->GetArrayField(TEXT("roads")).Num(), 1);
			}
		});

		It(TEXT("reports a bad road reference once"), [this]()
		{
			const FToolResult Result = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("ConnectEndpoints"),
				TEXT("{\"a\": {\"road\": {\"refPath\": \"/Game/Missing.Missing:PersistentLevel.NoRoad\"}, \"bStart\": true}, \"b\": {\"road\": null, \"bStart\": false}}"));
			TestFalse(TEXT("Rejected"), Result.Succeeded());
			TestFalse(FString::Printf(TEXT("Not the generic conversion error (%s)"), *Result.Error), Result.Error.Contains(TEXT("could not convert incoming")));
			TestFalse(FString::Printf(TEXT("Not reported twice (%s)"), *Result.Error), Result.Error.Contains(TEXT("RoadBLDToolset: A")));
		});

		It(TEXT("rejects unknown struct fields by name"), [this]()
		{
			const FToolResult Result = CallTool(URoadBLDAuthoringToolset::StaticClass(), TEXT("CreateRoad"), FString::Printf(
				TEXT("{\"preset\": %s, \"points\": [{\"location\": {\"x\": 0, \"y\": 0, \"z\": 0}, \"turnRadious\": 2000}, {\"location\": {\"x\": 100, \"y\": 0, \"z\": 0}}]}"),
				*RefJson(GetStreetPresetId())));
			TestFalse(TEXT("Rejected"), Result.Succeeded());
			TestTrue(FString::Printf(TEXT("Names the field (%s)"), *Result.Error), Result.Error.Contains(TEXT("turnRadious is not a field of RoadBLDPoint")));
		});
	});

	Describe(TEXT("rebuild jobs"), [this]()
	{
		It(TEXT("Rebuild with bWait=false returns a job that can be cancelled"), [this]()
		{
			if (!Network.IsValid() || CreateStraightRoad(20000.0).IsEmpty())
			{
				return;
			}

			// With bWait=false the result is complete when the call returns, so the job cannot have started yet.
			const FToolResult Started = CallTool(URoadBLDBuildToolset::StaticClass(), TEXT("Rebuild"), FString::Printf(TEXT("{\"network\": %s, \"bWait\": false}"), *NetworkJson));
			if (!TestTrue(FString::Printf(TEXT("Rebuild bWait=false succeeds (%s)"), *Started.Error), Started.Succeeded()))
			{
				return;
			}

			TestEqual(TEXT("Job is running"), Started.Object()->GetStringField(TEXT("state")), FString(TEXT("Running")));
			const FString JobId = Started.Object()->GetStringField(TEXT("jobId"));
			const FToolResult Cancelled = CallTool(URoadBLDBuildToolset::StaticClass(), TEXT("CancelRebuild"), FString::Printf(TEXT("{\"jobId\": \"%s\"}"), *JobId));
			if (TestTrue(FString::Printf(TEXT("CancelRebuild succeeds (%s)"), *Cancelled.Error), Cancelled.Succeeded()))
			{
				TestEqual(TEXT("Job aborted"), Cancelled.Object()->GetStringField(TEXT("state")), FString(TEXT("Aborted")));
			}

			const TArray<FRoadBLDNetworkInfo> Infos = URoadBLDDiscoveryToolset::DescribeNetwork(Network.Get());
			if (TestEqual(TEXT("One network described"), Infos.Num(), 1))
			{
				TestTrue(TEXT("Cancelled network stays stale"), Infos[0].bStale);
				TestFalse(TEXT("Stale network is not reported as rebuilding"), Infos[0].bRebuildInProgress);
			}
		});

		LatentIt(TEXT("CaptureViewport of a stale, idle network returns without waiting"), FTimespan::FromSeconds(30), [this](const FDoneDelegate& Done)
		{
			if (!Network.IsValid() || CreateStraightRoad(25000.0).IsEmpty())
			{
				Done.Execute();
				return;
			}

			const double StartSeconds = FPlatformTime::Seconds();
			CallToolAsync(URoadBLDFeedbackToolset::StaticClass(), TEXT("CaptureViewport"), FString::Printf(TEXT("{\"network\": %s}"), *NetworkJson), 20.0,
				[this, Done, StartSeconds](const FToolResult& Result)
				{
					TestTrue(TEXT("Capture completed"), Result.bComplete);
					TestFalse(FString::Printf(TEXT("No parameter error (%s)"), *Result.Error), Result.IsParameterError());
					TestTrue(TEXT("Capture did not wait for a rebuild"), FPlatformTime::Seconds() - StartSeconds < 10.0);
					if (Result.Succeeded())
					{
						const TArray<TSharedPtr<FJsonValue>>* Warnings = nullptr;
						TestTrue(TEXT("Stale warning"), Result.Object()->TryGetArrayField(TEXT("warnings"), Warnings) && Warnings->Num() > 0);
					}
					Done.Execute();
				});
		});
	});

	Describe(TEXT("preset specs"), [this]()
	{
		It(TEXT("DescribePreset spec round-trips through ValidatePreset"), [this]()
		{
			const FToolResult Described = CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("DescribePreset"),
				FString::Printf(TEXT("{\"preset\": %s}"), *RefJson(GetStreetPresetId())));
			if (!TestTrue(FString::Printf(TEXT("DescribePreset succeeds (%s)"), *Described.Error), Described.Succeeded()))
			{
				return;
			}

			const TSharedPtr<FJsonObject> Spec = Described.Object()->GetObjectField(TEXT("spec"));
			const TSharedRef<FJsonObject> Arguments = MakeShared<FJsonObject>();
			Arguments->SetObjectField(TEXT("spec"), Spec);
			const FToolResult Validated = CallTool(URoadBLDPresetToolset::StaticClass(), TEXT("ValidatePreset"), Arguments);
			if (!TestTrue(FString::Printf(TEXT("ValidatePreset accepts the described spec (%s)"), *Validated.Error), Validated.Succeeded()))
			{
				return;
			}

			const TArray<TSharedPtr<FJsonValue>>* Errors = nullptr;
			if (Validated.Object()->TryGetArrayField(TEXT("errors"), Errors))
			{
				for (const TSharedPtr<FJsonValue>& Error : *Errors)
				{
					AddError(FString::Printf(TEXT("%s: %s"),
						*Error->AsObject()->GetStringField(TEXT("field")),
						*Error->AsObject()->GetStringField(TEXT("message"))));
				}
			}
			TestTrue(TEXT("Described spec is valid"), Validated.Object()->GetBoolField(TEXT("bValid")));
		});

		It(TEXT("reports the offending field for a spec that does not convert"), [this]()
		{
			const FToolResult Result = CallTool(URoadBLDPresetToolset::StaticClass(), TEXT("ValidatePreset"),
				TEXT("{\"spec\": {\"name\": \"AITest_BadCategory\", \"category\": \"Spaceway\"}}"));
			TestFalse(TEXT("Rejected"), Result.Succeeded());
			TestTrue(FString::Printf(TEXT("Error names the field (%s)"), *Result.Error), Result.Error.Contains(TEXT("Spec.Category")));
			TestFalse(TEXT("Error is not the generic conversion failure"), Result.Error.Contains(TEXT("could not convert incoming function input params")));
		});

		It(TEXT("converts the README example spec"), [this]()
		{
			// Material parameter names in the example are placeholders, so only conversion is checked.
			const FToolResult Result = CallTool(URoadBLDPresetToolset::StaticClass(), TEXT("ValidatePreset"), TEXT(R"json({
				"spec": {
					"name": "EU_Cobble_Boulevard",
					"basePreset": "/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Boulevard_4Lane_CenterTurns.RP_Default_USA_Boulevard_4Lane_CenterTurns_C",
					"region": "Germany",
					"tags": ["boulevard", "cobblestone", "european"],
					"description": "Four-lane cobblestone boulevard with a planted median and wide sidewalks.",
					"leftLanes":  [ { "width": 300, "type": "Median" }, { "width": 330, "type": "Normal" }, { "width": 330, "type": "Normal" } ],
					"rightLanes": [ { "width": 330, "type": "Normal" }, { "width": 330, "type": "Normal" } ],
					"roadMaterial": {
						"variant": {
							"parent": "/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Asphalt_Master",
							"name": "Cobble",
							"scalars": { "Roughness": 0.85 },
							"vectors": { "BaseColorTint": { "r": 0.55, "g": 0.5, "b": 0.45, "a": 1 } }
						}
					},
					"rightSidewalk": {
						"inline": {
							"width": 400,
							"material": { "variant": { "parent": "/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Sidewalk_Master", "name": "Granite" } },
							"curbClass": "/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_USA_Curb"
						}
					},
					"crossingStyle": null
				}
			})json"));
			if (TestTrue(FString::Printf(TEXT("Example converts (%s)"), *Result.Error), Result.Succeeded()))
			{
				const TSharedPtr<FJsonObject> Report = Result.Object();
				TestTrue(TEXT("Median lane read"), Report->GetObjectField(TEXT("traits"))->GetBoolField(TEXT("bHasMedian")));
				TestTrue(TEXT("Inline sidewalk read"), Report->GetObjectField(TEXT("traits"))->GetBoolField(TEXT("bHasRightSidewalk")));
			}
		});

		It(TEXT("UpdatePreset keeps fields the spec omits"), [this]()
		{
			const FString CreateJson = FString::Printf(
				TEXT("{\"spec\": {\"name\": \"%s\", \"basePreset\": \"%s\", \"bOverwrite\": true, \"description\": \"Original description\", \"tags\": [\"aitest\"]}}"),
				UpdateTestPresetName, *GetStreetPresetId());
			const FToolResult Created = CallTool(URoadBLDPresetToolset::StaticClass(), TEXT("CreatePresetFromSpec"), CreateJson);
			if (!TestTrue(FString::Printf(TEXT("CreatePresetFromSpec succeeds (%s)"), *Created.Error), Created.Succeeded() && Created.Object()->GetBoolField(TEXT("bSucceeded"))))
			{
				return;
			}

			const FString PresetId = Created.Object()->GetStringField(TEXT("presetId"));
			const FToolResult Updated = CallTool(URoadBLDPresetToolset::StaticClass(), TEXT("UpdatePreset"), FString::Printf(
				TEXT("{\"preset\": %s, \"spec\": {\"name\": \"%s\", \"tags\": [\"aitest\", \"updated\"]}}"), *RefJson(PresetId), UpdateTestPresetName));
			TestTrue(FString::Printf(TEXT("UpdatePreset succeeds (%s)"), *Updated.Error), Updated.Succeeded() && Updated.Object()->GetBoolField(TEXT("bSucceeded")));

			const FToolResult Described = CallTool(URoadBLDDiscoveryToolset::StaticClass(), TEXT("DescribePreset"), FString::Printf(TEXT("{\"preset\": %s}"), *RefJson(PresetId)));
			if (TestTrue(FString::Printf(TEXT("DescribePreset succeeds (%s)"), *Described.Error), Described.Succeeded()))
			{
				const TSharedPtr<FJsonObject> Spec = Described.Object()->GetObjectField(TEXT("spec"));
				TestEqual(TEXT("Omitted description kept"), Spec->GetStringField(TEXT("description")), FString(TEXT("Original description")));
				TArray<FString> Tags;
				Spec->TryGetStringArrayField(TEXT("tags"), Tags);
				TestTrue(TEXT("Given tags applied"), Tags.Contains(TEXT("updated")));
				TestTrue(TEXT("Lanes kept from the base"), Spec->GetArrayField(TEXT("rightLanes")).Num() > 0);
			}

			if (UClass* PresetClass = FindObject<UClass>(nullptr, *PresetId))
			{
				if (UBlueprint* Blueprint = UBlueprint::GetBlueprintFromClass(PresetClass))
				{
					ObjectTools::ForceDeleteObjects({ Blueprint }, false);
				}
			}
		});
	});
}

#endif
