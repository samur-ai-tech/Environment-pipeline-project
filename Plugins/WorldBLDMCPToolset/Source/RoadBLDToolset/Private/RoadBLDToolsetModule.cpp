// Copyright WorldBLD LLC. All rights reserved.

#include "Common/RoadBLDJsonConverter.h"
#include "Common/RoadBLDRebuildJobs.h"
#include "Modules/ModuleManager.h"
#include "Toolsets/RoadBLDAuthoringToolset.h"
#include "Toolsets/RoadBLDBuildToolset.h"
#include "Toolsets/RoadBLDDiscoveryToolset.h"
#include "Toolsets/RoadBLDFeedbackToolset.h"
#include "Toolsets/RoadBLDPresetToolset.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

class FRoadBLDToolsetModule : public IModuleInterface
{
	static TArray<UClass*> GetToolsetClasses()
	{
		return {
			URoadBLDDiscoveryToolset::StaticClass(),
			URoadBLDAuthoringToolset::StaticClass(),
			URoadBLDPresetToolset::StaticClass(),
			URoadBLDBuildToolset::StaticClass(),
			URoadBLDFeedbackToolset::StaticClass(),
		};
	}

	virtual void StartupModule() override
	{
		// Tool schemas are built at registration, so the converter must be in place first.
		FRoadBLDJsonConverter::Register();
		for (UClass* ToolsetClass : GetToolsetClasses())
		{
			UToolsetRegistry::RegisterToolsetClass(ToolsetClass);
		}
	}

	virtual void ShutdownModule() override
	{
		for (UClass* ToolsetClass : GetToolsetClasses())
		{
			UToolsetRegistry::UnregisterToolsetClass(ToolsetClass);
		}
		FRoadBLDJsonConverter::Unregister();
		FRoadBLDRebuildJobs::Get().Shutdown();
	}
};

IMPLEMENT_MODULE(FRoadBLDToolsetModule, RoadBLDToolset)
