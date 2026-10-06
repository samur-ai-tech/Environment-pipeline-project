// Copyright WorldBLD LLC. All rights reserved.

#include "LinePlacement/WorldBLDAssetPalette.h"
#include "Math/RandomStream.h"

bool UWorldBLDAssetPalette::SampleWeighted(FRandomStream& Rng, FPlacedAsset& OutAsset) const
{
	if (Assets.IsEmpty())
	{
		return false;
	}

	// Compute total weight
	float TotalWeight = 0.0f;
	for (const TPair<FPlacedAsset, float>& Pair : Assets)
	{
		TotalWeight += FMath::Max(0.0f, Pair.Value);
	}

	if (TotalWeight <= 0.0f)
	{
		// All weights are zero or negative — fall back to uniform selection
		int32 Idx = Rng.RandRange(0, Assets.Num() - 1);
		int32 Current = 0;
		for (const TPair<FPlacedAsset, float>& Pair : Assets)
		{
			if (Current == Idx)
			{
				OutAsset = Pair.Key;
				return true;
			}
			++Current;
		}
		return false;
	}

	float Roll = Rng.FRandRange(0.0f, TotalWeight);
	float Accumulated = 0.0f;

	for (const TPair<FPlacedAsset, float>& Pair : Assets)
	{
		const float W = FMath::Max(0.0f, Pair.Value);
		Accumulated += W;
		if (Roll <= Accumulated)
		{
			OutAsset = Pair.Key;
			return true;
		}
	}

	// Floating-point edge case — return last entry
	OutAsset = Assets.begin()->Key;
	return true;
}
