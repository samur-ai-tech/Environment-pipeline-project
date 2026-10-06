// Copyright WorldBLD LLC. All rights reserved.

#include "Modules/ModuleManager.h"
#include "ToolsetRegistry/UToolsetRegistry.h"
#include "CityBLDToolset.h"
#include "Toolsets/CityBLDDiscoveryToolset.h"

class FCityBLDToolsetModule : public IModuleInterface
{
	static TArray<UClass*> GetToolsetClasses()
	{
		return
		{
			UCityBLDToolset::StaticClass(),
			UCityBLDDiscoveryToolset::StaticClass(),
		};
	}

	virtual void StartupModule() override
	{
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
	}
};

IMPLEMENT_MODULE(FCityBLDToolsetModule, CityBLDToolset)
