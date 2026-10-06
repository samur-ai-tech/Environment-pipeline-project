// Copyright WorldBLD LLC. All rights reserved.

#include "Misc/AutomationTest.h"
#include "ToolsetRegistry/UToolsetRegistry.h"
#include "Toolsets/WBVToolset.h"
#include "WorldBLDToolset.h"

#if WITH_DEV_AUTOMATION_TESTS

BEGIN_DEFINE_SPEC(
	FWorldBLDToolsetSpec,
	TEXT("AI.Toolsets.WorldBLD.WorldBLDToolset"),
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
END_DEFINE_SPEC(FWorldBLDToolsetSpec)

void FWorldBLDToolsetSpec::Define()
{
	It(TEXT("registers the toolset class"), [this]()
	{
		TestTrue(TEXT("WorldBLDToolset is registered"),
			UToolsetRegistry::IsToolsetClassRegistered(UWorldBLDToolset::StaticClass()));
		TestTrue(TEXT("WorldBLDValidationToolset is registered"),
			UToolsetRegistry::IsToolsetClassRegistered(UWorldBLDValidationToolset::StaticClass()));
	});

	It(TEXT("schema contains expected tools"), [this]()
	{
		const FString Schema = UToolsetRegistry::GetToolsetJsonSchema(UWorldBLDToolset::StaticClass());
		TestTrue(TEXT("GetCapabilities"), Schema.Contains(TEXT("GetCapabilities")));
		TestTrue(TEXT("GetEditorContext"), Schema.Contains(TEXT("GetEditorContext")));
		TestTrue(TEXT("ListLevelActors"), Schema.Contains(TEXT("ListLevelActors")));
		TestTrue(TEXT("SetWorldBLDEditorModeActive"), Schema.Contains(TEXT("SetWorldBLDEditorModeActive")));
		TestTrue(TEXT("GetPackagingGuide"), Schema.Contains(TEXT("GetPackagingGuide")));

		const FString ValidationSchema = UToolsetRegistry::GetToolsetJsonSchema(UWorldBLDValidationToolset::StaticClass());
		TestTrue(TEXT("CheckPostOpReadiness"), ValidationSchema.Contains(TEXT("CheckPostOpReadiness")));
		TestTrue(TEXT("RunValidationLoop"), ValidationSchema.Contains(TEXT("RunValidationLoop")));
		TestTrue(TEXT("CaptureValidationEvidence"), ValidationSchema.Contains(TEXT("CaptureValidationEvidence")));
	});

	It(TEXT("GetPackagingGuide returns integration context and common solutions"), [this]()
	{
		const FWorldBLDPackagingGuide Guide = UWorldBLDToolset::GetPackagingGuide(FString());
		TestTrue(TEXT("has integration overview"), Guide.IntegrationOverview.Contains(TEXT("WorldBLD")));
		TestTrue(TEXT("mentions CityBLD"), Guide.IntegrationOverview.Contains(TEXT("CityBLD")));
		TestEqual(TEXT("eight common solutions"), Guide.CommonSolutions.Num(), 8);
		TestTrue(TEXT("source vs launcher"), Guide.CommonSolutions[0].Contains(TEXT("source")));
		TestTrue(TEXT("project Plugins folder"), Guide.CommonSolutions[1].Contains(TEXT("Plugins")));
		TestTrue(TEXT("Blueprint project"), Guide.CommonSolutions[2].Contains(TEXT("C++")));
		TestTrue(TEXT("restart PC"), Guide.CommonSolutions[3].Contains(TEXT("Restart")));
		TestTrue(TEXT("Full Rebuild"), Guide.CommonSolutions[4].Contains(TEXT("Full Rebuild")));
		TestTrue(TEXT("Build.cs v4/v5"), Guide.CommonSolutions[5].Contains(TEXT("V4")));
		TestTrue(TEXT("cook path"), Guide.CommonSolutions[6].Contains(TEXT("WorldBLD_Content")));
		TestTrue(TEXT("GeometryScriptingCore"), Guide.CommonSolutions[7].Contains(TEXT("GeometryScriptingCore")));
		TestTrue(TEXT("reports four product plugins"), Guide.Plugins.Num() == 4);
		TestTrue(TEXT("has live checks"), Guide.Checks.Num() > 0);
	});

	It(TEXT("GetPackagingGuide matches cook missing-content errors"), [this]()
	{
		const FWorldBLDPackagingGuide Guide = UWorldBLDToolset::GetPackagingGuide(
			TEXT("Build Failed: LogCook: Error: Content is missing from cook... /ModernEssentials/WorldBLD_Content"));
		bool bMatchedCook = false;
		for (const FString& Suggested : Guide.SuggestedFirst)
		{
			if (Suggested.Contains(TEXT("WorldBLD_Content")) || Suggested.Contains(TEXT("H:/Pack")))
			{
				bMatchedCook = true;
				break;
			}
		}
		TestTrue(TEXT("suggested cook-path solution"), bMatchedCook);
	});
}

#endif