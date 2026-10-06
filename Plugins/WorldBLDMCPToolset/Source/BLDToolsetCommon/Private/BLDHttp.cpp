// Copyright WorldBLD LLC. All rights reserved.

#include "BLDHttp.h"

#include "Containers/Ticker.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"

namespace BLDHttpPrivate
{
	constexpr float TickIntervalSeconds = 0.05f;

	struct FPending
	{
		FBLDHttpRequest Request;
		FBLDHttp::FOnResponse OnDone;
	};

	struct FState
	{
		TMap<FString, double> MinIntervalSeconds;
		TMap<FString, double> LastDispatchSeconds;
		TMap<FString, TArray<FPending>> Queues;
		FTSTicker::FDelegateHandle TickerHandle;
		FBLDHttp::FTransportOverride TransportOverride;
	};

	FState& GetState()
	{
		static FState State;
		return State;
	}

	FString GetHost(const FString& Url)
	{
		FString Rest = Url;
		const int32 SchemeIndex = Rest.Find(TEXT("://"));
		if (SchemeIndex != INDEX_NONE)
		{
			Rest.RightChopInline(SchemeIndex + 3);
		}

		int32 EndIndex = INDEX_NONE;
		if (Rest.FindChar(TEXT('/'), EndIndex))
		{
			Rest.LeftInline(EndIndex);
		}
		return Rest.ToLower();
	}

	FString GetCacheDirectory(const FString& Namespace)
	{
		const FString Root = FPaths::ProjectSavedDir() / TEXT("BLDToolset") / TEXT("Cache");
		return Namespace.IsEmpty() ? Root : Root / FPaths::MakeValidFileName(Namespace);
	}

	FString GetCachePath(const FBLDHttpRequest& Request)
	{
		const FString Key = FMD5::HashAnsiString(*FString::Printf(TEXT("%s %s\n%s"), *Request.Verb, *Request.Url, *Request.Body));
		const FString Namespace = Request.CacheNamespace.IsEmpty() ? TEXT("default") : Request.CacheNamespace;
		return GetCacheDirectory(Namespace) / (Key + TEXT(".txt"));
	}

	bool TryReadCache(const FBLDHttpRequest& Request, FBLDHttpResponse& OutResponse)
	{
		if (Request.CacheTtlSeconds <= 0.0)
		{
			return false;
		}

		const FString Path = GetCachePath(Request);
		const FDateTime Stamp = IFileManager::Get().GetTimeStamp(*Path);
		if (Stamp == FDateTime::MinValue()
			|| (FDateTime::UtcNow() - Stamp).GetTotalSeconds() > Request.CacheTtlSeconds)
		{
			return false;
		}

		FString Content;
		if (!FFileHelper::LoadFileToString(Content, *Path))
		{
			return false;
		}

		OutResponse.bSucceeded = true;
		OutResponse.StatusCode = 200;
		OutResponse.Content = MoveTemp(Content);
		OutResponse.bFromCache = true;
		return true;
	}

	void WriteCache(const FBLDHttpRequest& Request, const FBLDHttpResponse& Response)
	{
		if (Request.CacheTtlSeconds > 0.0 && Response.bSucceeded && !Response.bFromCache)
		{
			FFileHelper::SaveStringToFile(Response.Content, *GetCachePath(Request), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
		}
	}

	void Dispatch(FPending&& InPending)
	{
		const TSharedRef<FPending> Pending = MakeShared<FPending>(MoveTemp(InPending));

		FBLDHttpResponse OverrideResponse;
		if (GetState().TransportOverride && GetState().TransportOverride(Pending->Request, OverrideResponse))
		{
			WriteCache(Pending->Request, OverrideResponse);
			Pending->OnDone(OverrideResponse);
			return;
		}

		const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
		HttpRequest->SetURL(Pending->Request.Url);
		HttpRequest->SetVerb(Pending->Request.Verb);
		HttpRequest->SetHeader(TEXT("User-Agent"), FBLDHttp::GetUserAgent());
		HttpRequest->SetHeader(TEXT("Accept"), TEXT("application/json, text/xml, */*"));
		for (const TPair<FString, FString>& Header : Pending->Request.Headers)
		{
			HttpRequest->SetHeader(Header.Key, Header.Value);
		}
		if (!Pending->Request.Body.IsEmpty())
		{
			HttpRequest->SetContentAsString(Pending->Request.Body);
		}
		HttpRequest->SetTimeout(FMath::Max(1.0f, Pending->Request.TimeoutSeconds));

		HttpRequest->OnProcessRequestComplete().BindLambda(
			[Pending](FHttpRequestPtr, FHttpResponsePtr HttpResponse, const bool bConnected)
			{
				FBLDHttpResponse Response;
				Response.StatusCode = HttpResponse.IsValid() ? HttpResponse->GetResponseCode() : 0;
				Response.Content = HttpResponse.IsValid() ? HttpResponse->GetContentAsString() : FString();
				Response.bSucceeded = bConnected && HttpResponse.IsValid() && EHttpResponseCodes::IsOk(Response.StatusCode);

				const FString Host = GetHost(Pending->Request.Url);
				if (!bConnected || !HttpResponse.IsValid())
				{
					Response.Error = FString::Printf(TEXT("Could not reach %s. Check the network connection and try again."), *Host);
				}
				else if (!Response.bSucceeded)
				{
					Response.Error = FString::Printf(TEXT("%s returned HTTP %d."), *Host, Response.StatusCode);
				}

				WriteCache(Pending->Request, Response);
				Pending->OnDone(Response);
			});

		HttpRequest->ProcessRequest();
	}

	/** Returns true while any request is still queued. */
	bool Pump()
	{
		FState& State = GetState();
		const double NowSeconds = FPlatformTime::Seconds();

		TArray<FPending> Ready;
		bool bAnyQueued = false;
		for (TPair<FString, TArray<FPending>>& Queue : State.Queues)
		{
			if (Queue.Value.IsEmpty())
			{
				continue;
			}

			const double Interval = State.MinIntervalSeconds.FindRef(Queue.Key);
			if (Interval <= 0.0)
			{
				Ready.Append(MoveTemp(Queue.Value));
				Queue.Value.Reset();
				continue;
			}

			const double* LastDispatch = State.LastDispatchSeconds.Find(Queue.Key);
			if (!LastDispatch || NowSeconds - *LastDispatch >= Interval)
			{
				State.LastDispatchSeconds.Add(Queue.Key, NowSeconds);
				Ready.Add(MoveTemp(Queue.Value[0]));
				Queue.Value.RemoveAt(0);
			}

			bAnyQueued |= !Queue.Value.IsEmpty();
		}

		// Dispatch after iterating: overrides and cache hits can call back into Send synchronously.
		for (FPending& Pending : Ready)
		{
			Dispatch(MoveTemp(Pending));
		}

		for (const TPair<FString, TArray<FPending>>& Queue : GetState().Queues)
		{
			bAnyQueued |= !Queue.Value.IsEmpty();
		}
		return bAnyQueued;
	}

	void EnsureTicker()
	{
		FState& State = GetState();
		if (State.TickerHandle.IsValid())
		{
			return;
		}

		State.TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateLambda([](float)
			{
				const bool bKeepTicking = Pump();
				if (!bKeepTicking)
				{
					GetState().TickerHandle.Reset();
				}
				return bKeepTicking;
			}),
			TickIntervalSeconds);
	}
}

void FBLDHttp::Send(const FBLDHttpRequest& Request, FOnResponse OnDone)
{
	using namespace BLDHttpPrivate;

	FBLDHttpResponse Cached;
	if (TryReadCache(Request, Cached))
	{
		OnDone(Cached);
		return;
	}

	FPending& Pending = GetState().Queues.FindOrAdd(GetHost(Request.Url)).AddDefaulted_GetRef();
	Pending.Request = Request;
	Pending.OnDone = MoveTemp(OnDone);

	if (Pump())
	{
		EnsureTicker();
	}
}

void FBLDHttp::SetMinIntervalForHost(const FString& Host, const double Seconds)
{
	BLDHttpPrivate::GetState().MinIntervalSeconds.Add(Host.ToLower(), FMath::Max(0.0, Seconds));
}

void FBLDHttp::SetTransportOverride(FTransportOverride Override)
{
	BLDHttpPrivate::GetState().TransportOverride = MoveTemp(Override);
}

void FBLDHttp::ClearCache(const FString& Namespace)
{
	IFileManager::Get().DeleteDirectory(*BLDHttpPrivate::GetCacheDirectory(Namespace), false, true);
}

FString FBLDHttp::GetUserAgent()
{
	return TEXT("WorldBLD-BLDToolset/2.0 (Unreal Editor AI toolsets; +https://worldbld.com)");
}

void FBLDHttp::Shutdown()
{
	BLDHttpPrivate::FState& State = BLDHttpPrivate::GetState();
	if (State.TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(State.TickerHandle);
		State.TickerHandle.Reset();
	}
	State.Queues.Reset();
	State.TransportOverride = nullptr;
}
