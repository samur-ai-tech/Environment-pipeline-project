// Copyright WorldBLD LLC. All rights reserved.

#include "Modules/ModuleManager.h"
#include "ToolsetRegistry/UToolsetRegistry.h"
#include "Toolsets/WBVToolset.h"
#include "WorldBLDToolset.h"

class FWorldBLDToolsetModule : public IModuleInterface
{
	static TArray<UClass*> GetToolsetClasses()
	{
		return
		{
			UWorldBLDToolset::StaticClass(),
			UWorldBLDValidationToolset::StaticClass(),
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

IMPLEMENT_MODULE(FWorldBLDToolsetModule, WorldBLDToolset)