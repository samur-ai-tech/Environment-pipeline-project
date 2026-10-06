// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Misc/EngineVersion.h"

/**
 * Helpers for asset-library engineVersions gating.
 * Asset engineVersions is a minimum floor: compatible when CurrentMajor.Minor >= min(list).
 * Empty / all-unparseable lists are treated as unrestricted (legacy assets).
 */
namespace WorldBLDAssetEngineVersionUtils
{
	inline int32 ParseSemVerToSortableInt(const FString& InVersion)
	{
		int32 Major = 0;
		int32 Minor = 0;
		int32 Patch = 0;

		const FString Clean = InVersion.TrimStartAndEnd();
		if (Clean.IsEmpty())
		{
			return 0;
		}

		TArray<FString> Parts;
		Clean.ParseIntoArray(Parts, TEXT("."), /*bCullEmpty=*/true);
		if (Parts.Num() > 0)
		{
			Major = FCString::Atoi(*Parts[0]);
		}
		if (Parts.Num() > 1)
		{
			Minor = FCString::Atoi(*Parts[1]);
		}
		if (Parts.Num() > 2)
		{
			FString PatchToken = Parts[2];
			int32 DigitCount = 0;
			while (DigitCount < PatchToken.Len() && FChar::IsDigit(PatchToken[DigitCount]))
			{
				++DigitCount;
			}
			if (DigitCount > 0)
			{
				PatchToken = PatchToken.Left(DigitCount);
				Patch = FCString::Atoi(*PatchToken);
			}
		}

		return (Major * 10000) + (Minor * 100) + Patch;
	}

	inline FString GetCurrentEngineMajorMinorString()
	{
		const FEngineVersion Current = FEngineVersion::Current();
		return FString::Printf(TEXT("%u.%u"), Current.GetMajor(), Current.GetMinor());
	}

	/** Lowest parseable engineVersions entry as "Major.Minor"; empty if none parse. */
	inline FString GetAssetMinimumEngineVersionString(const TArray<FString>& EngineVersions)
	{
		int32 MinSortable = TNumericLimits<int32>::Max();
		FString MinString;

		for (const FString& Raw : EngineVersions)
		{
			const FString Trimmed = Raw.TrimStartAndEnd();
			if (Trimmed.IsEmpty())
			{
				continue;
			}

			const int32 Sortable = ParseSemVerToSortableInt(Trimmed);
			if (Sortable <= 0)
			{
				continue;
			}

			if (Sortable < MinSortable)
			{
				MinSortable = Sortable;
				// Normalize to major.minor for dialogs.
				TArray<FString> Parts;
				Trimmed.ParseIntoArray(Parts, TEXT("."), /*bCullEmpty=*/true);
				if (Parts.Num() >= 2)
				{
					MinString = FString::Printf(TEXT("%d.%d"), FCString::Atoi(*Parts[0]), FCString::Atoi(*Parts[1]));
				}
				else
				{
					MinString = Trimmed;
				}
			}
		}

		return MinString;
	}

	inline bool IsEngineVersionCompatible(const TArray<FString>& EngineVersions)
	{
		const FString MinVersion = GetAssetMinimumEngineVersionString(EngineVersions);
		if (MinVersion.IsEmpty())
		{
			return true;
		}

		const int32 RequiredInt = ParseSemVerToSortableInt(MinVersion);
		if (RequiredInt <= 0)
		{
			return true;
		}

		const int32 CurrentInt = ParseSemVerToSortableInt(GetCurrentEngineMajorMinorString());
		return CurrentInt >= RequiredInt;
	}

	inline FString MakeIncompatibleEngineMessage(const TArray<FString>& EngineVersions)
	{
		const FString Required = GetAssetMinimumEngineVersionString(EngineVersions);
		const FString Current = GetCurrentEngineMajorMinorString();
		return FString::Printf(
			TEXT("This asset requires Unreal Engine %s or newer. You are running %s."),
			Required.IsEmpty() ? TEXT("a newer version") : *Required,
			*Current);
	}
}
