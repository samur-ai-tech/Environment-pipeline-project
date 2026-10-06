// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/TwinBLDToolsetTypes.h"
#include "Templates/Function.h"

/**
 * Nominatim geocoding client (OpenStreetMap). Follows the public usage policy: one request per second, an identifying
 * User-Agent, and cached answers. The endpoint can be changed with [TwinBLDToolset] NominatimEndpoint in the editor
 * config, for example to point at a self-hosted server.
 */
namespace TwinBLDNominatim
{
	/** Answers are reused for 30 days. */
	constexpr double CacheTtlSeconds = 30.0 * 24.0 * 3600.0;

	inline const TCHAR* Attribution = TEXT("Data (c) OpenStreetMap contributors, ODbL 1.0. Geocoding by Nominatim.");

	using FOnPlaces = TFunction<void(bool bSucceeded, const FTwinBLDGeocodeResult& Result, const FString& Error)>;

	FString GetEndpoint();

	void Search(const FString& Query, int32 MaxResults, const FString& CountryCodes, FOnPlaces OnDone);

	void Reverse(const FTwinBLDGeoPoint& Point, int32 Zoom, FOnPlaces OnDone);

	/** Parses a jsonv2 search response (an array) or reverse response (an object). */
	bool ParsePlaces(const FString& Json, TArray<FTwinBLDPlace>& OutPlaces, FString& OutError);
}
