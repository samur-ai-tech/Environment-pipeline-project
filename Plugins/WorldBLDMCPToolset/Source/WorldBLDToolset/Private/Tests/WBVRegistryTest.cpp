// Copyright WorldBLD LLC. All rights reserved.

#include "Misc/AutomationTest.h"

#include "Dom/JsonObject.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "ToolsetRegistry/ToolCallAsyncResultString.h"
#include "ToolsetRegistry/UToolsetRegistry.h"
#include "Toolsets/WBVToolset.h"
#include "WorldBLDToolset.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace WorldBLDValidationRegistryTestPrivate
{
	struct FToolResult
	{
		bool bComplete = false;
		FString Error;
		TSharedPtr<FJsonValue> Value;

		bool Succeeded() const
		{
			return bComplete && Error.IsEmpty() && Value.IsValid();
		}
	};

	FString GetToolsetName(const UClass* ToolsetClass)
	{
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

	FToolResult CallTool(const UClass* ToolsetClass, const FString& Tool, const TSharedRef<FJsonObject>& Arguments)
	{
		const UToolCallAsyncResultString* Async =
			UToolsetRegistry::ExecuteTool(GetToolsetName(ToolsetClass), Tool, ToJsonString(Arguments));
		FToolResult Result;
		ReadResult(Async, Result);
		if (!Result.bComplete)
		{
			Result.Error = TEXT("Tool did not complete synchronously.");
		}
		return Result;
	}
}

BEGIN_DEFINE_SPEC(
	FWorldBLDValidationRegistrySpec,
	TEXT("AI.Toolsets.WorldBLD.WorldBLDValidationToolset.Registry"),
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
END_DEFINE_SPEC(FWorldBLDValidationRegistrySpec)

void FWorldBLDValidationRegistrySpec::Define()
{
	It(TEXT("CheckPostOpReadiness via registry returns an object"), [this]()
	{
		using namespace WorldBLDValidationRegistryTestPrivate;
		const FToolResult Result = CallTool(
			UWorldBLDValidationToolset::StaticClass(),
			TEXT("CheckPostOpReadiness"),
			MakeShared<FJsonObject>());
		TestTrue(TEXT("succeeded"), Result.Succeeded());
		const TSharedPtr<FJsonObject>* Obj = nullptr;
		TestTrue(TEXT("object"), Result.Value.IsValid() && Result.Value->TryGetObject(Obj) && Obj && Obj->IsValid());
		if (Obj && Obj->IsValid())
		{
			TestTrue(TEXT("has bReady"), (*Obj)->HasField(TEXT("bReady")) || (*Obj)->HasField(TEXT("BReady")));
		}
	});

	It(TEXT("RunValidationLoop via registry returns Issues array shape"), [this]()
	{
		using namespace WorldBLDValidationRegistryTestPrivate;
		const TSharedRef<FJsonObject> Args = MakeShared<FJsonObject>();
		Args->SetBoolField(TEXT("bIncludeCity"), true);
		Args->SetBoolField(TEXT("bIncludeRoad"), true);
		Args->SetBoolField(TEXT("bIncludeTwin"), true);
		Args->SetNumberField(TEXT("MaxIssuesPerSource"), 25);

		const FToolResult Result = CallTool(
			UWorldBLDValidationToolset::StaticClass(),
			TEXT("RunValidationLoop"),
			Args);
		TestTrue(TEXT("succeeded"), Result.Succeeded());
		const TSharedPtr<FJsonObject>* Root = nullptr;
		TestTrue(TEXT("root object"), Result.Value.IsValid() && Result.Value->TryGetObject(Root) && Root && Root->IsValid());
		if (!(Root && Root->IsValid()))
		{
			return;
		}

		const TSharedPtr<FJsonObject>* Report = nullptr;
		const bool bHasReport = (*Root)->TryGetObjectField(TEXT("report"), Report) || (*Root)->TryGetObjectField(TEXT("Report"), Report);
		TestTrue(TEXT("has report"), bHasReport && Report && Report->IsValid());
		if (bHasReport && Report && Report->IsValid())
		{
			const TArray<TSharedPtr<FJsonValue>>* Issues = nullptr;
			TestTrue(TEXT("has issues array"),
				(*Report)->TryGetArrayField(TEXT("issues"), Issues) || (*Report)->TryGetArrayField(TEXT("Issues"), Issues));
		}

		const TArray<TSharedPtr<FJsonValue>>* Checked = nullptr;
		const TArray<TSharedPtr<FJsonValue>>* Skipped = nullptr;
		const bool bHasChecked = (*Root)->TryGetArrayField(TEXT("sourcesChecked"), Checked) || (*Root)->TryGetArrayField(TEXT("SourcesChecked"), Checked);
		const bool bHasSkipped = (*Root)->TryGetArrayField(TEXT("sourcesSkipped"), Skipped) || (*Root)->TryGetArrayField(TEXT("SourcesSkipped"), Skipped);
		TestTrue(TEXT("has sourcesChecked"), bHasChecked);
		TestTrue(TEXT("has sourcesSkipped"), bHasSkipped);
	});
}

#endif