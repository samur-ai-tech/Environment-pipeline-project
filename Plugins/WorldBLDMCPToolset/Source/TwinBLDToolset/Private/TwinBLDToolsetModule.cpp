// Copyright WorldBLD LLC. All rights reserved.

#include "Modules/ModuleManager.h"
#include "Toolsets/TwinBLDLocationToolset.h"
#include "Toolsets/TwinBLDSceneToolset.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

namespace TwinBLDToolsetModulePrivate
{
	TArray<UClass*> GetToolsetClasses()
	{
		return
		{
			UTwinBLDLocationToolset::StaticClass(),
			UTwinBLDSceneToolset::StaticClass(),
		};
	}
}

class FTwinBLDToolsetModule : public IModuleInterface
{
	virtual void StartupModule() override
	{
		for (UClass* ToolsetClass : TwinBLDToolsetModulePrivate::GetToolsetClasses())
		{
			UToolsetRegistry::RegisterToolsetClass(ToolsetClass);
		}
	}

	virtual void ShutdownModule() override
	{
		for (UClass* ToolsetClass : TwinBLDToolsetModulePrivate::GetToolsetClasses())
		{
			UToolsetRegistry::UnregisterToolsetClass(ToolsetClass);
		}
	}
};

IMPLEMENT_MODULE(FTwinBLDToolsetModule, TwinBLDToolset)
