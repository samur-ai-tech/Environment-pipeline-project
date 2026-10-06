// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/WBVToolset.h"

#include "BLDCapture.h"
#include "BLDToolsetUtils.h"
#include "BLDValidation.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "ToolsetRegistry/ToolCallAsyncResultString.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(WBVToolset)

namespace WorldBLDValidationPrivate
{
	constexpr TCHAR ToolsetName[] = TEXT("WorldBLDToolset");

	bool PluginEnabled(const TCHAR* PluginName)
	{
		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(PluginName);
		return Plugin.IsValid() && Plugin->IsEnabled();
	}

	bool ToolsetRegistered(const FString& ToolsetNameValue)
	{
		return UToolsetRegistry::IsToolsetRegistered(ToolsetNameValue);
	}

	TSharedPtr<FJsonValue> ExecuteSyncTool(const FString& Toolset, const FString& Tool, const FString& ArgumentsJson, FString& OutError)
	{
		const UToolCallAsyncResultString* Async = UToolsetRegistry::ExecuteTool(Toolset, Tool, ArgumentsJson);
		if (!Async)
		{
			OutError = TEXT("ExecuteTool returned null.");
			return nullptr;
		}
		if (!Async->bIsComplete)
		{
			OutError = TEXT("Tool did not complete synchronously.");
			return nullptr;
		}
		if (!Async->Error.IsEmpty())
		{
			OutError = Async->Error;
			return nullptr;
		}

		TSharedPtr<FJsonObject> Envelope;
		if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Async->Value), Envelope) || !Envelope.IsValid())
		{
			OutError = FString::Printf(TEXT("Unparseable tool result: %s"), *Async->Value);
			return nullptr;
		}
		return Envelope->TryGetField(TEXT("returnValue"));
	}

	EBLDIssueSeverity ParseSeverity(const FString& Text)
	{
		if (Text.Equals(TEXT("Error"), ESearchCase::IgnoreCase) || Text.Equals(TEXT("ECityBLDIssueSeverity::Error")))
		{
			return EBLDIssueSeverity::Error;
		}
		if (Text.Equals(TEXT("Info"), ESearchCase::IgnoreCase) || Text.Equals(TEXT("ECityBLDIssueSeverity::Info")))
		{
			return EBLDIssueSeverity::Info;
		}
		return EBLDIssueSeverity::Warning;
	}

	FBLDActorRef ActorFromJson(const TSharedPtr<FJsonObject>& Obj)
	{
		FBLDActorRef Ref;
		if (!Obj.IsValid())
		{
			return Ref;
		}
		Obj->TryGetStringField(TEXT("name"), Ref.Name);
		Obj->TryGetStringField(TEXT("Name"), Ref.Name);
		Obj->TryGetStringField(TEXT("label"), Ref.Label);
		Obj->TryGetStringField(TEXT("Label"), Ref.Label);
		Obj->TryGetStringField(TEXT("refPath"), Ref.RefPath);
		Obj->TryGetStringField(TEXT("RefPath"), Ref.RefPath);
		Obj->TryGetStringField(TEXT("class"), Ref.Class);
		Obj->TryGetStringField(TEXT("Class"), Ref.Class);
		return Ref;
	}

	FVector VectorFromJson(const TSharedPtr<FJsonObject>& Obj)
	{
		if (!Obj.IsValid())
		{
			return FVector::ZeroVector;
		}
		double X = 0, Y = 0, Z = 0;
		Obj->TryGetNumberField(TEXT("x"), X);
		Obj->TryGetNumberField(TEXT("X"), X);
		Obj->TryGetNumberField(TEXT("y"), Y);
		Obj->TryGetNumberField(TEXT("Y"), Y);
		Obj->TryGetNumberField(TEXT("z"), Z);
		Obj->TryGetNumberField(TEXT("Z"), Z);
		return FVector(X, Y, Z);
	}

	void AppendFromIssueReport(FBLDIssueReport& Report, const TSharedPtr<FJsonValue>& ReturnValue, const int32 MaxIssues, const FString& DefaultSource)
	{
		const TSharedPtr<FJsonObject>* RootObj = nullptr;
		if (!ReturnValue.IsValid() || !ReturnValue->TryGetObject(RootObj) || !RootObj || !RootObj->IsValid())
		{
			return;
		}

		const TArray<TSharedPtr<FJsonValue>>* IssuesArray = nullptr;
		if (!(*RootObj)->TryGetArrayField(TEXT("issues"), IssuesArray) && !(*RootObj)->TryGetArrayField(TEXT("Issues"), IssuesArray))
		{
			return;
		}

		const TArray<TSharedPtr<FJsonValue>>* NotesArray = nullptr;
		if ((*RootObj)->TryGetArrayField(TEXT("notes"), NotesArray) || (*RootObj)->TryGetArrayField(TEXT("Notes"), NotesArray))
		{
			for (const TSharedPtr<FJsonValue>& Note : *NotesArray)
			{
				if (Note.IsValid() && Note->Type == EJson::String)
				{
					Report.Notes.Add(Note->AsString());
				}
			}
		}

		int32 Added = 0;
		for (const TSharedPtr<FJsonValue>& Entry : *IssuesArray)
		{
			if (Added >= MaxIssues)
			{
				break;
			}
			const TSharedPtr<FJsonObject>* IssueObj = nullptr;
			if (!Entry.IsValid() || !Entry->TryGetObject(IssueObj) || !IssueObj || !IssueObj->IsValid())
			{
				continue;
			}

			FString SeverityText, Code, Message, Fix, Source;
			(*IssueObj)->TryGetStringField(TEXT("severity"), SeverityText);
			(*IssueObj)->TryGetStringField(TEXT("Severity"), SeverityText);
			(*IssueObj)->TryGetStringField(TEXT("code"), Code);
			(*IssueObj)->TryGetStringField(TEXT("Code"), Code);
			(*IssueObj)->TryGetStringField(TEXT("message"), Message);
			(*IssueObj)->TryGetStringField(TEXT("Message"), Message);
			(*IssueObj)->TryGetStringField(TEXT("fix"), Fix);
			(*IssueObj)->TryGetStringField(TEXT("Fix"), Fix);
			(*IssueObj)->TryGetStringField(TEXT("source"), Source);
			(*IssueObj)->TryGetStringField(TEXT("Source"), Source);
			if (Source.IsEmpty())
			{
				Source = DefaultSource;
			}

			const TSharedPtr<FJsonObject>* SubjectObj = nullptr;
			FBLDActorRef Subject;
			if ((*IssueObj)->TryGetObjectField(TEXT("subject"), SubjectObj) || (*IssueObj)->TryGetObjectField(TEXT("Subject"), SubjectObj)
				|| (*IssueObj)->TryGetObjectField(TEXT("actor"), SubjectObj) || (*IssueObj)->TryGetObjectField(TEXT("Actor"), SubjectObj))
			{
				Subject = ActorFromJson(*SubjectObj);
			}
			const TSharedPtr<FJsonObject>* OtherObj = nullptr;
			FBLDActorRef Other;
			if ((*IssueObj)->TryGetObjectField(TEXT("other"), OtherObj) || (*IssueObj)->TryGetObjectField(TEXT("Other"), OtherObj)
				|| (*IssueObj)->TryGetObjectField(TEXT("otherActor"), OtherObj) || (*IssueObj)->TryGetObjectField(TEXT("OtherActor"), OtherObj))
			{
				Other = ActorFromJson(*OtherObj);
			}
			const TSharedPtr<FJsonObject>* LocObj = nullptr;
			FVector Location = FVector::ZeroVector;
			if ((*IssueObj)->TryGetObjectField(TEXT("location"), LocObj) || (*IssueObj)->TryGetObjectField(TEXT("Location"), LocObj))
			{
				Location = VectorFromJson(*LocObj);
			}
			double Radius = 0.0;
			(*IssueObj)->TryGetNumberField(TEXT("radius"), Radius);
			(*IssueObj)->TryGetNumberField(TEXT("Radius"), Radius);

			Report.Issues.Add(BLDValidation::MakeIssue(
				ParseSeverity(SeverityText),
				Source,
				Code.IsEmpty() ? TEXT("Issue") : Code,
				Message,
				Subject,
				Other,
				Location,
				Radius,
				Fix));
			++Added;
		}
	}

	void AppendRoadJunctionIssues(FBLDIssueReport& Report, const TSharedPtr<FJsonValue>& ReturnValue, const int32 MaxIssues)
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		if (!ReturnValue.IsValid() || !ReturnValue->TryGetArray(Arr) || !Arr)
		{
			return;
		}

		int32 Added = 0;
		for (const TSharedPtr<FJsonValue>& Entry : *Arr)
		{
			if (Added >= MaxIssues)
			{
				break;
			}
			const TSharedPtr<FJsonObject>* IssueObj = nullptr;
			if (!Entry.IsValid() || !Entry->TryGetObject(IssueObj) || !IssueObj || !IssueObj->IsValid())
			{
				continue;
			}

			FString Kind, Suggestion;
			(*IssueObj)->TryGetStringField(TEXT("kind"), Kind);
			(*IssueObj)->TryGetStringField(TEXT("Kind"), Kind);
			(*IssueObj)->TryGetStringField(TEXT("suggestion"), Suggestion);
			(*IssueObj)->TryGetStringField(TEXT("Suggestion"), Suggestion);

			FBLDActorRef Subject;
			const TSharedPtr<FJsonObject>* RoadObj = nullptr;
			if ((*IssueObj)->TryGetObjectField(TEXT("road"), RoadObj) || (*IssueObj)->TryGetObjectField(TEXT("Road"), RoadObj))
			{
				Subject = ActorFromJson(*RoadObj);
			}
			FBLDActorRef Other;
			const TSharedPtr<FJsonObject>* OtherRoadObj = nullptr;
			if ((*IssueObj)->TryGetObjectField(TEXT("otherRoad"), OtherRoadObj) || (*IssueObj)->TryGetObjectField(TEXT("OtherRoad"), OtherRoadObj))
			{
				Other = ActorFromJson(*OtherRoadObj);
			}
			FVector Location = FVector::ZeroVector;
			const TSharedPtr<FJsonObject>* LocObj = nullptr;
			if ((*IssueObj)->TryGetObjectField(TEXT("location"), LocObj) || (*IssueObj)->TryGetObjectField(TEXT("Location"), LocObj))
			{
				Location = VectorFromJson(*LocObj);
			}

			const FString Message = Suggestion.IsEmpty()
				? FString::Printf(TEXT("Road junction issue: %s"), *Kind)
				: Suggestion;

			Report.Issues.Add(BLDValidation::MakeIssue(
				EBLDIssueSeverity::Warning,
				TEXT("RoadBLD"),
				Kind.IsEmpty() ? TEXT("JunctionIssue") : Kind,
				Message,
				Subject,
				Other,
				Location,
				1500.0,
				TEXT("Use RoadBLDAuthoringToolset (SetControlPoints / CloseCorner) then Rebuild.")));
			++Added;
		}
	}

	void AppendRoadGeometryIssues(FBLDIssueReport& Report, const TSharedPtr<FJsonValue>& ReturnValue, const int32 MaxIssues)
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		if (!ReturnValue.IsValid() || !ReturnValue->TryGetArray(Arr) || !Arr)
		{
			return;
		}

		int32 Added = 0;
		for (const TSharedPtr<FJsonValue>& Entry : *Arr)
		{
			if (Added >= MaxIssues)
			{
				break;
			}
			const TSharedPtr<FJsonObject>* IssueObj = nullptr;
			if (!Entry.IsValid() || !Entry->TryGetObject(IssueObj) || !IssueObj || !IssueObj->IsValid())
			{
				continue;
			}

			FString Kind, GeometryActor;
			(*IssueObj)->TryGetStringField(TEXT("kind"), Kind);
			(*IssueObj)->TryGetStringField(TEXT("Kind"), Kind);
			(*IssueObj)->TryGetStringField(TEXT("geometryActor"), GeometryActor);
			(*IssueObj)->TryGetStringField(TEXT("GeometryActor"), GeometryActor);
			double Radius = 0.0;
			(*IssueObj)->TryGetNumberField(TEXT("radius"), Radius);
			(*IssueObj)->TryGetNumberField(TEXT("Radius"), Radius);

			FVector Location = FVector::ZeroVector;
			const TSharedPtr<FJsonObject>* LocObj = nullptr;
			if ((*IssueObj)->TryGetObjectField(TEXT("location"), LocObj) || (*IssueObj)->TryGetObjectField(TEXT("Location"), LocObj))
			{
				Location = VectorFromJson(*LocObj);
			}

			FBLDActorRef Subject;
			Subject.RefPath = GeometryActor;
			Subject.Name = FPaths::GetBaseFilename(GeometryActor);

			Report.Issues.Add(BLDValidation::MakeIssue(
				EBLDIssueSeverity::Error,
				TEXT("RoadBLD"),
				Kind.IsEmpty() ? TEXT("GeometryIssue") : Kind,
				FString::Printf(TEXT("Generated road mesh has %s artifacts."), *Kind),
				Subject,
				FBLDActorRef(),
				Location,
				Radius > 0.0 ? Radius : 3000.0,
				TEXT("Inspect with CaptureArea, fix nearby ends (FindJunctionIssues / CloseCorner), then Rebuild.")));
			++Added;
		}
	}

	void AppendRebuildBusy(FBLDPostOpReadiness& Readiness, const TSharedPtr<FJsonValue>& ReturnValue)
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		if (!ReturnValue.IsValid() || !ReturnValue->TryGetArray(Arr) || !Arr)
		{
			return;
		}
		for (const TSharedPtr<FJsonValue>& Entry : *Arr)
		{
			const TSharedPtr<FJsonObject>* NetObj = nullptr;
			if (!Entry.IsValid() || !Entry->TryGetObject(NetObj) || !NetObj || !NetObj->IsValid())
			{
				continue;
			}
			bool bRebuildInProgress = false;
			(*NetObj)->TryGetBoolField(TEXT("bRebuildInProgress"), bRebuildInProgress);
			(*NetObj)->TryGetBoolField(TEXT("BRebuildInProgress"), bRebuildInProgress);
			if (bRebuildInProgress)
			{
				Readiness.bRebuildInProgress = true;
				Readiness.bReady = false;
				FString Label;
				(*NetObj)->TryGetStringField(TEXT("label"), Label);
				(*NetObj)->TryGetStringField(TEXT("Label"), Label);
				Readiness.BlockingReasons.Add(FString::Printf(
					TEXT("Road network%s is still rebuilding."),
					Label.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(" '%s'"), *Label)));
			}
		}
	}
}

FBLDPostOpReadiness UWorldBLDValidationToolset::CheckPostOpReadiness()
{
	using namespace WorldBLDValidationPrivate;
	BLDToolset::MarkCurrentCallUnattended();

	FBLDPostOpReadiness Readiness;
	Readiness.bReady = true;

	if (!PluginEnabled(TEXT("RoadBLD")) || !ToolsetRegistered(TEXT("RoadBLDToolset.URoadBLDDiscoveryToolset")))
	{
		Readiness.Notes.Add(TEXT("RoadBLD discovery toolset not available; rebuild readiness was not checked."));
		return Readiness;
	}

	FString Error;
	const TSharedPtr<FJsonValue> Value = ExecuteSyncTool(
		TEXT("RoadBLDToolset.URoadBLDDiscoveryToolset"),
		TEXT("DescribeNetwork"),
		TEXT("{}"),
		Error);
	if (!Error.IsEmpty())
	{
		Readiness.Notes.Add(FString::Printf(TEXT("DescribeNetwork skipped: %s"), *Error));
		return Readiness;
	}

	AppendRebuildBusy(Readiness, Value);
	if (Readiness.bReady)
	{
		Readiness.Notes.Add(TEXT("No RoadBLD rebuild in progress."));
	}
	return Readiness;
}

FBLDValidationLoopResult UWorldBLDValidationToolset::RunValidationLoop(
	const bool bIncludeCity,
	const bool bIncludeRoad,
	const bool bIncludeTwin,
	const int32 MaxIssuesPerSource)
{
	using namespace WorldBLDValidationPrivate;
	BLDToolset::MarkCurrentCallUnattended();

	FBLDValidationLoopResult Result;
	Result.Readiness = CheckPostOpReadiness();
	const int32 Cap = FMath::Clamp(MaxIssuesPerSource, 1, 200);

	if (bIncludeCity)
	{
		const FString CityToolset = TEXT("CityBLDToolset.UCityBLDDiscoveryToolset");
		if (PluginEnabled(TEXT("CityBLD")) && ToolsetRegistered(CityToolset))
		{
			FString Error;
			// Prefer ValidateCity when present; fall back to FindCityIssues.
			TSharedPtr<FJsonValue> Value = ExecuteSyncTool(CityToolset, TEXT("ValidateCity"), TEXT("{}"), Error);
			if (!Error.IsEmpty())
			{
				Error.Reset();
				Value = ExecuteSyncTool(
					CityToolset,
					TEXT("FindCityIssues"),
					FString::Printf(TEXT("{\"MaxResults\":%d}"), Cap),
					Error);
			}
			if (Error.IsEmpty())
			{
				AppendFromIssueReport(Result.Report, Value, Cap, TEXT("CityBLD"));
				Result.SourcesChecked.Add(TEXT("CityBLD.ValidateCity"));
			}
			else
			{
				Result.SourcesSkipped.Add(FString::Printf(TEXT("CityBLD (%s)"), *Error));
			}
		}
		else
		{
			Result.SourcesSkipped.Add(TEXT("CityBLD (plugin or toolset unavailable)"));
		}
	}

	if (bIncludeRoad)
	{
		const FString RoadDiscovery = TEXT("RoadBLDToolset.URoadBLDDiscoveryToolset");
		if (PluginEnabled(TEXT("RoadBLD")) && ToolsetRegistered(RoadDiscovery))
		{
			FString Error;
			TSharedPtr<FJsonValue> Junctions = ExecuteSyncTool(RoadDiscovery, TEXT("FindJunctionIssues"), TEXT("{}"), Error);
			if (Error.IsEmpty())
			{
				AppendRoadJunctionIssues(Result.Report, Junctions, Cap);
				Result.SourcesChecked.Add(TEXT("RoadBLD.FindJunctionIssues"));
			}
			else
			{
				Result.SourcesSkipped.Add(FString::Printf(TEXT("RoadBLD.FindJunctionIssues (%s)"), *Error));
			}

			Error.Reset();
			const FString GeomArgs = FString::Printf(TEXT("{\"MaxIssues\":%d}"), Cap);
			TSharedPtr<FJsonValue> Geometry = ExecuteSyncTool(RoadDiscovery, TEXT("FindGeometryIssues"), GeomArgs, Error);
			if (Error.IsEmpty())
			{
				AppendRoadGeometryIssues(Result.Report, Geometry, Cap);
				Result.SourcesChecked.Add(TEXT("RoadBLD.FindGeometryIssues"));
			}
			else
			{
				Result.SourcesSkipped.Add(FString::Printf(TEXT("RoadBLD.FindGeometryIssues (%s)"), *Error));
			}
		}
		else
		{
			Result.SourcesSkipped.Add(TEXT("RoadBLD (plugin or toolset unavailable)"));
		}
	}

	if (bIncludeTwin)
	{
		const FString TwinToolset = TEXT("TwinBLDToolset.UTwinBLDSceneToolset");
		if (PluginEnabled(TEXT("TwinBLD")) && ToolsetRegistered(TwinToolset))
		{
			FString Error;
			TSharedPtr<FJsonValue> Value = ExecuteSyncTool(TwinToolset, TEXT("ValidateTwinScene"), TEXT("{}"), Error);
			if (Error.IsEmpty())
			{
				AppendFromIssueReport(Result.Report, Value, Cap, TEXT("TwinBLD"));
				Result.SourcesChecked.Add(TEXT("TwinBLD.ValidateTwinScene"));
			}
			else
			{
				Result.SourcesSkipped.Add(FString::Printf(TEXT("TwinBLD.ValidateTwinScene (%s)"), *Error));
			}
		}
		else
		{
			Result.SourcesSkipped.Add(TEXT("TwinBLD (plugin or toolset unavailable)"));
		}
	}

	BLDValidation::FinalizeReport(Result.Report);
	if (!Result.Readiness.bReady)
	{
		Result.Report.bReady = false;
		Result.Report.Notes.Add(TEXT("Post-op readiness is false; finish rebuilds before trusting capture or further edits."));
	}

	if (Result.SourcesChecked.Num() == 0)
	{
		Result.Report.Notes.Add(TEXT("No validation sources ran. Enable CityBLD / RoadBLD / TwinBLD toolsets."));
	}

	Result.EvidenceNote = TEXT("Call CaptureValidationEvidence with an issue Location/Radius for visual proof.");
	return Result;
}

UBLDCaptureAsyncResult* UWorldBLDValidationToolset::CaptureValidationEvidence(
	const FVector Location,
	const double Radius,
	const EBLDCaptureView View,
	const int32 Width,
	const int32 Height)
{
	UBLDCaptureAsyncResult* Result = NewObject<UBLDCaptureAsyncResult>();
	BLDCapture::FRequest Request;
	const double R = FMath::Max(Radius, 100.0);
	Request.Bounds = FBox(Location - FVector(R, R, R), Location + FVector(R, R, R));
	Request.View = View;
	Request.Width = FMath::Clamp(Width, 64, 2048);
	Request.Height = FMath::Clamp(Height, 64, 2048);
	Request.ToolsetName = TEXT("WorldBLDToolset");
	Request.bRestoreCamera = true;
	BLDCapture::Capture(Result, MoveTemp(Request));
	return Result;
}