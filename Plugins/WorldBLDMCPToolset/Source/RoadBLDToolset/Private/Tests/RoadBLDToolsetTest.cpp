// Copyright WorldBLD LLC. All rights reserved.

#include "Misc/AutomationTest.h"
#include "Common/RoadBLDToolsetUtils.h"
#include "Misc/PackageName.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Toolsets/RoadBLDAuthoringToolset.h"
#include "Toolsets/RoadBLDBuildToolset.h"
#include "Toolsets/RoadBLDDiscoveryToolset.h"
#include "Toolsets/RoadBLDFeedbackToolset.h"
#include "Toolsets/RoadBLDPresetToolset.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace RoadBLDToolsetTestPrivate
{
	struct FExpectedToolset
	{
		UClass* Class = nullptr;
		TArray<FString> Tools;
	};

	TArray<FExpectedToolset> GetExpectedToolsets()
	{
		return {
			{ URoadBLDDiscoveryToolset::StaticClass(), { TEXT("ListPresets"), TEXT("DescribePreset"), TEXT("ListStyleAssets"), TEXT("ListMaterialParameters"), TEXT("DescribeNetwork"), TEXT("DescribeRoad"), TEXT("ListJunctions"), TEXT("ListEndpoints"), TEXT("FindJunctionIssues"), TEXT("SampleRoad") } },
			{ URoadBLDAuthoringToolset::StaticClass(), { TEXT("CreateNetwork"), TEXT("CreateRoad"), TEXT("CreateGrid"), TEXT("CreateRing"), TEXT("CreateRoundabout"), TEXT("ConnectEndpoints"), TEXT("SetControlPoints"), TEXT("ChangePreset"), TEXT("SetLaneWidth"), TEXT("SetSidewalk"), TEXT("AddLane"), TEXT("DeleteRoads"), TEXT("DuplicateRoad") } },
			{ URoadBLDPresetToolset::StaticClass(), { TEXT("ValidatePreset"), TEXT("CreatePresetFromSpec"), TEXT("UpdatePreset"), TEXT("CreateMaterialVariant") } },
			{ URoadBLDBuildToolset::StaticClass(), { TEXT("Rebuild"), TEXT("RebuildRoads"), TEXT("RebuildStatus"), TEXT("WaitForRebuild"), TEXT("CancelRebuild") } },
			{ URoadBLDFeedbackToolset::StaticClass(), { TEXT("CaptureViewport"), TEXT("CaptureArea") } },
		};
	}

	FRoadBLDLaneSpec MakeLane(const double Width, const TCHAR* Type)
	{
		FRoadBLDLaneSpec Lane;
		Lane.Width = Width;
		Lane.Type = Type;
		return Lane;
	}
}

BEGIN_DEFINE_SPEC(
	FRoadBLDToolsetSpec,
	TEXT("AI.Toolsets.WorldBLD.RoadBLDToolset"),
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
END_DEFINE_SPEC(FRoadBLDToolsetSpec)

void FRoadBLDToolsetSpec::Define()
{
	using namespace RoadBLDToolsetTestPrivate;

	It(TEXT("registers every toolset class"), [this]()
	{
		for (const FExpectedToolset& Toolset : GetExpectedToolsets())
		{
			TestTrue(Toolset.Class->GetName(), UToolsetRegistry::IsToolsetClassRegistered(Toolset.Class));
		}
	});

	It(TEXT("schemas contain the expected tools"), [this]()
	{
		for (const FExpectedToolset& Toolset : GetExpectedToolsets())
		{
			const FString Schema = UToolsetRegistry::GetToolsetJsonSchema(Toolset.Class);
			for (const FString& Tool : Toolset.Tools)
			{
				TestTrue(FString::Printf(TEXT("%s.%s"), *Toolset.Class->GetName(), *Tool), Schema.Contains(Tool));
			}
		}
	});

	It(TEXT("no tool parameter shares a name with function metadata"), [this]()
	{
		// The registry takes a parameter's default from function metadata of the same name before its C++ default.
		for (const FExpectedToolset& Toolset : GetExpectedToolsets())
		{
			for (TFieldIterator<UFunction> FunctionIt(Toolset.Class, EFieldIterationFlags::None); FunctionIt; ++FunctionIt)
			{
				for (TFieldIterator<FProperty> ParamIt(*FunctionIt); ParamIt && ParamIt->HasAnyPropertyFlags(CPF_Parm); ++ParamIt)
				{
					TestFalse(FString::Printf(TEXT("%s(%s) collides with metadata"), *FunctionIt->GetName(), *ParamIt->GetName()),
						FunctionIt->HasMetaData(*ParamIt->GetName()));
				}
			}
		}
	});

	It(TEXT("only truly required parameters are required in the schema"), [this]()
	{
		const TMap<FString, TArray<FString>> Expected =
		{
			{ TEXT("ListPresets"), {} },
			{ TEXT("ListStyleAssets"), { TEXT("kind") } },
			{ TEXT("CreateRoad"), { TEXT("preset"), TEXT("points") } },
			{ TEXT("CreateRing"), { TEXT("preset"), TEXT("polygon") } },
			{ TEXT("SetLaneWidth"), { TEXT("road"), TEXT("side"), TEXT("laneIndex"), TEXT("width") } },
			{ TEXT("CloseCorner"), { TEXT("a"), TEXT("b") } },
			{ TEXT("CaptureViewport"), {} },
			{ TEXT("CaptureArea"), { TEXT("center") } },
		};

		TSet<FString> Checked;
		for (const FExpectedToolset& Toolset : GetExpectedToolsets())
		{
			TSharedPtr<FJsonObject> Root;
			const FString Schema = UToolsetRegistry::GetToolsetJsonSchema(Toolset.Class);
			if (!TestTrue(TEXT("Schema parses"), FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Schema), Root) && Root.IsValid()))
			{
				continue;
			}

			for (const TSharedPtr<FJsonValue>& Tool : Root->GetArrayField(TEXT("tools")))
			{
				FString ToolName;
				Tool->AsObject()->GetStringField(TEXT("name")).Split(TEXT("."), nullptr, &ToolName, ESearchCase::IgnoreCase, ESearchDir::FromEnd);
				if (const TArray<FString>* ExpectedRequired = Expected.Find(ToolName))
				{
					TArray<FString> Required;
					Tool->AsObject()->GetObjectField(TEXT("inputSchema"))->TryGetStringArrayField(TEXT("required"), Required);
					TestEqual(FString::Printf(TEXT("%s required parameters"), *ToolName), FString::Join(Required, TEXT(",")), FString::Join(*ExpectedRequired, TEXT(",")));
					Checked.Add(ToolName);
				}
			}
		}
		TestEqual(TEXT("Every expected tool was checked"), Checked.Num(), Expected.Num());
	});

	It(TEXT("preset schema exposes spec fields"), [this]()
	{
		const FString Schema = UToolsetRegistry::GetToolsetJsonSchema(URoadBLDPresetToolset::StaticClass());
		for (const TCHAR* Field : { TEXT("leftLanes"), TEXT("rightLanes"), TEXT("roadMaterial"), TEXT("variant"), TEXT("scalars"), TEXT("leftSidewalk") })
		{
			TestTrue(Field, Schema.Contains(Field));
		}
	});

	It(TEXT("rejects a preset spec without lanes"), [this]()
	{
		FRoadBLDPresetSpec Spec;
		Spec.Name = TEXT("AITest_NoLanes");
		Spec.LeftLanes = TArray<FRoadBLDLaneSpec>();
		Spec.RightLanes = TArray<FRoadBLDLaneSpec>();

		const FRoadBLDValidationReport Report = URoadBLDPresetToolset::ValidatePreset(Spec);
		TestFalse(TEXT("Spec is invalid"), Report.bValid);
		TestTrue(TEXT("Reports the missing lanes"), Report.Errors.ContainsByPredicate([](const FRoadBLDValidationIssue& Issue)
		{
			return Issue.Field == TEXT("RightLanes");
		}));
	});

	It(TEXT("rejects unknown lane types, bad widths and missing assets"), [this]()
	{
		FRoadBLDPresetSpec Spec;
		Spec.Name = TEXT("AITest_BadValues");
		Spec.RightLanes = TArray<FRoadBLDLaneSpec>{ MakeLane(0.0, TEXT("Hovercraft")) };
		FRoadBLDMaterialRef MissingMaterial;
		MissingMaterial.Path = TEXT("/Game/DoesNotExist/M_Missing");
		Spec.RoadMaterial = MissingMaterial;

		const FRoadBLDValidationReport Report = URoadBLDPresetToolset::ValidatePreset(Spec);
		TestFalse(TEXT("Spec is invalid"), Report.bValid);
		auto HasError = [&Report](const FString& Field)
		{
			return Report.Errors.ContainsByPredicate([&Field](const FRoadBLDValidationIssue& Issue) { return Issue.Field == Field; });
		};
		TestTrue(TEXT("Width error"), HasError(TEXT("RightLanes[0].Width")));
		TestTrue(TEXT("Type error"), HasError(TEXT("RightLanes[0].Type")));
		TestTrue(TEXT("Material error"), HasError(TEXT("RoadMaterial.Path")));
	});

	It(TEXT("accepts a simple two-lane spec"), [this]()
	{
		FRoadBLDPresetSpec Spec;
		Spec.Name = TEXT("AITest_TwoLane_ValidationOnly");
		Spec.LeftLanes = TArray<FRoadBLDLaneSpec>{ MakeLane(350.0, TEXT("Normal")) };
		Spec.RightLanes = TArray<FRoadBLDLaneSpec>{ MakeLane(350.0, TEXT("Normal")), MakeLane(250.0, TEXT("Parking")) };

		const FRoadBLDValidationReport Report = URoadBLDPresetToolset::ValidatePreset(Spec);
		TestTrue(TEXT("Spec is valid"), Report.bValid);
		TestEqual(TEXT("Driving lanes"), Report.Traits.LeftDrivingLanes + Report.Traits.RightDrivingLanes, 2);
		TestTrue(TEXT("Parking detected"), Report.Traits.bHasParking);
		TestEqual(TEXT("Total width"), Report.Traits.TotalLaneWidth, 950.0);
	});

	It(TEXT("reference kit assets exist and are named in the preset toolset description"), [this]()
	{
		const FString Schema = UToolsetRegistry::GetToolsetJsonSchema(URoadBLDPresetToolset::StaticClass());
		for (const RoadBLDToolset::FReferenceKitAsset& Asset : RoadBLDToolset::GetReferenceKitAssets())
		{
			const FString PackagePath = Asset.PackagePath;
			FString Error;
			TestNotNull(FString::Printf(TEXT("%s loads"), *PackagePath), RoadBLDToolset::LoadObjectFromPath(PackagePath, nullptr, Error));

			// The description may name later assets in a folder by asset name only ("..., Lane_BikeLane (same folder)").
			const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
			const FString Folder = FPackageName::GetLongPackagePath(PackagePath);
			TestTrue(FString::Printf(TEXT("%s is described"), *PackagePath),
				Schema.Contains(PackagePath) || (Schema.Contains(Folder) && Schema.Contains(AssetName)));
		}
	});
}

#endif
