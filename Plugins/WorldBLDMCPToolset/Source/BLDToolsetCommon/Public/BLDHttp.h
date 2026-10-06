// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Templates/Function.h"

struct BLDTOOLSETCOMMON_API FBLDHttpRequest
{
	FString Verb = TEXT("GET");
	FString Url;
	FString Body;
	TMap<FString, FString> Headers;

	/** Cache folder under Saved/BLDToolset/Cache. Empty uses "default". */
	FString CacheNamespace;

	/** Successful responses are reused for this many seconds. 0 disables the cache for this request. */
	double CacheTtlSeconds = 0.0;

	float TimeoutSeconds = 30.0f;
};

struct BLDTOOLSETCOMMON_API FBLDHttpResponse
{
	bool bSucceeded = false;
	int32 StatusCode = 0;
	FString Content;
	bool bFromCache = false;

	/** Human-readable failure reason when bSucceeded is false. */
	FString Error;
};

/**
 * HTTP for toolsets that call outside services. Adds a descriptive User-Agent, spaces out requests per host,
 * and caches successful responses on disk. Callbacks run on the game thread.
 */
class BLDTOOLSETCOMMON_API FBLDHttp
{
public:
	using FOnResponse = TFunction<void(const FBLDHttpResponse&)>;
	using FTransportOverride = TFunction<bool(const FBLDHttpRequest&, FBLDHttpResponse&)>;

	static void Send(const FBLDHttpRequest& Request, FOnResponse OnDone);

	/** Requests to Host (for example nominatim.openstreetmap.org) start at least Seconds apart. */
	static void SetMinIntervalForHost(const FString& Host, double Seconds);

	/**
	 * Routes requests through Override instead of the network. Return true after filling the response to handle a
	 * request. Used by automation tests. Pass nullptr to restore the network.
	 */
	static void SetTransportOverride(FTransportOverride Override);

	/** Deletes cached responses in Namespace, or all namespaces when Namespace is empty. */
	static void ClearCache(const FString& Namespace);

	static FString GetUserAgent();

	static void Shutdown();
};
