// Copyright WorldBLD LLC. All rights reserved.

#include "LandscapePaint/WorldBLDLandscapePopulateOptions.h"

#include "Landscape.h"
#include "WorldBLDLandscapePreset.h"

bool UWorldBLDLandscapePopulateOptions::CanContinue() const
{
	return IsValid(TargetLandscape) && IsValid(Preset);
}
