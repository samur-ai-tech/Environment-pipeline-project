// Copyright WorldBLD LLC. All rights reserved.

#include "BLDHttp.h"
#include "BLDJobRegistry.h"
#include "Modules/ModuleManager.h"

class FBLDToolsetCommonModule : public IModuleInterface
{
	virtual void ShutdownModule() override
	{
		FBLDJobRegistry::Get().Shutdown();
		FBLDHttp::Shutdown();
	}
};

IMPLEMENT_MODULE(FBLDToolsetCommonModule, BLDToolsetCommon)
