// Copyright WorldBLD LLC. All rights reserved.

#include "Services/TwinBLDNominatim.h"

#include "BLDHttp.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "Misc/ConfigCacheIni.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace TwinBLDNominatim
{
	namespace
	{
		constexpr double MinSecondsBetweenRequests = 1.1;

		FString GetStringField(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field)
		{
			FString Value;
			if (Object.IsValid() && !Object->TryGetStringField(Field, Value))
			{
				double Number = 0.0;
				if (Object->TryGetNumberField(Field, Number))
				{
					Value = FString::Printf(TEXT("%.17g"), Number);
				}
			}
			return Value;
		}

		double GetDoubleField(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field)
		{
			double Number = 0.0;
			if (Object.IsValid() && !Object->TryGetNumberField(Field, Number))
			{
				FString Text;
				if (Object->TryGetStringField(Field, Text))
				{
					Number = FCString::Atod(*Text);
				}
			}
			return Number;
		}

		TArray<FTwinBLDKeyValue> ReadKeyValues(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field)
		{
			TArray<FTwinBLDKeyValue> Result;
			const TSharedPtr<FJsonObject>* Child = nullptr;
			if (!Object.IsValid() || !Object->TryGetObjectField(Field, Child) || !Child || !Child->IsValid())
			{
				return Result;
			}

			for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*Child)->Values)
			{
				FString Value;
				if (Pair.Value.IsValid() && Pair.Value->TryGetString(Value))
				{
					FTwinBLDKeyValue& Entry = Result.AddDefaulted_GetRef();
					Entry.Key = Pair.Key;
					Entry.Value = Value;
				}
			}
			return Result;
		}

		bool ParsePlace(const TSharedPtr<FJsonObject>& Object, FTwinBLDPlace& OutPlace)
		{
			if (!Object.IsValid() || !Object->HasField(TEXT("lat")) || !Object->HasField(TEXT("lon")))
			{
				return false;
			}

			OutPlace.Name = GetStringField(Object, TEXT("name"));
			OutPlace.DisplayName = GetStringField(Object, TEXT("display_name"));
			OutPlace.Category = GetStringField(Object, TEXT("category"));
			if (OutPlace.Category.IsEmpty())
			{
				OutPlace.Category = GetStringField(Object, TEXT("class"));
			}
			OutPlace.Type = GetStringField(Object, TEXT("type"));
			OutPlace.OsmType = GetStringField(Object, TEXT("osm_type"));
			OutPlace.OsmId = static_cast<int64>(GetDoubleField(Object, TEXT("osm_id")));
			OutPlace.Location.Lat = GetDoubleField(Object, TEXT("lat"));
			OutPlace.Location.Lon = GetDoubleField(Object, TEXT("lon"));
			OutPlace.Importance = GetDoubleField(Object, TEXT("importance"));
			OutPlace.Address = ReadKeyValues(Object, TEXT("address"));
			OutPlace.ExtraTags = ReadKeyValues(Object, TEXT("extratags"));

			for (const FTwinBLDKeyValue& Tag : OutPlace.ExtraTags)
			{
				if (Tag.Key == TEXT("wikidata"))
				{
					OutPlace.WikidataId = Tag.Value;
				}
			}

			// boundingbox is [south, north, west, east] as strings.
			const TArray<TSharedPtr<FJsonValue>>* BoundingBox = nullptr;
			if (Object->TryGetArrayField(TEXT("boundingbox"), BoundingBox) && BoundingBox && BoundingBox->Num() == 4)
			{
				auto ReadCorner = [](const TSharedPtr<FJsonValue>& Value)
				{
					FString Text;
					return Value.IsValid() && Value->TryGetString(Text) ? FCString::Atod(*Text) : (Value.IsValid() ? Value->AsNumber() : 0.0);
				};
				OutPlace.Bounds.South = ReadCorner((*BoundingBox)[0]);
				OutPlace.Bounds.North = ReadCorner((*BoundingBox)[1]);
				OutPlace.Bounds.West = ReadCorner((*BoundingBox)[2]);
				OutPlace.Bounds.East = ReadCorner((*BoundingBox)[3]);
			}
			else
			{
				OutPlace.Bounds.South = OutPlace.Bounds.North = OutPlace.Location.Lat;
				OutPlace.Bounds.West = OutPlace.Bounds.East = OutPlace.Location.Lon;
			}

			return true;
		}

		void SendAndParse(const FString& Url, FOnPlaces OnDone)
		{
			FBLDHttp::SetMinIntervalForHost(FGenericPlatformHttp::GetUrlDomain(GetEndpoint()), MinSecondsBetweenRequests);

			FBLDHttpRequest Request;
			Request.Url = Url;
			Request.CacheNamespace = TEXT("nominatim");
			Request.CacheTtlSeconds = CacheTtlSeconds;
			Request.Headers.Add(TEXT("Accept-Language"), TEXT("en"));

			FBLDHttp::Send(Request, [OnDone = MoveTemp(OnDone)](const FBLDHttpResponse& Response)
			{
				FTwinBLDGeocodeResult Result;
				Result.Attribution = Attribution;
				Result.bFromCache = Response.bFromCache;

				if (!Response.bSucceeded)
				{
					OnDone(false, Result, Response.Error);
					return;
				}

				FString Error;
				if (!ParsePlaces(Response.Content, Result.Places, Error))
				{
					OnDone(false, Result, Error);
					return;
				}

				OnDone(true, Result, FString());
			});
		}
	}

	FString GetEndpoint()
	{
		FString Endpoint = TEXT("https://nominatim.openstreetmap.org");
		if (GConfig)
		{
			GConfig->GetString(TEXT("TwinBLDToolset"), TEXT("NominatimEndpoint"), Endpoint, GEditorIni);
		}
		Endpoint.RemoveFromEnd(TEXT("/"));
		return Endpoint;
	}

	void Search(const FString& Query, const int32 MaxResults, const FString& CountryCodes, FOnPlaces OnDone)
	{
		FString Url = FString::Printf(
			TEXT("%s/search?format=jsonv2&addressdetails=1&extratags=1&limit=%d&q=%s"),
			*GetEndpoint(),
			FMath::Clamp(MaxResults, 1, 40),
			*FGenericPlatformHttp::UrlEncode(Query.TrimStartAndEnd()));

		if (!CountryCodes.TrimStartAndEnd().IsEmpty())
		{
			Url += TEXT("&countrycodes=") + FGenericPlatformHttp::UrlEncode(CountryCodes.TrimStartAndEnd().ToLower());
		}

		SendAndParse(Url, MoveTemp(OnDone));
	}

	void Reverse(const FTwinBLDGeoPoint& Point, const int32 Zoom, FOnPlaces OnDone)
	{
		const FString Url = FString::Printf(
			TEXT("%s/reverse?format=jsonv2&addressdetails=1&extratags=1&zoom=%d&lat=%.8f&lon=%.8f"),
			*GetEndpoint(),
			FMath::Clamp(Zoom, 3, 18),
			Point.Lat,
			Point.Lon);

		SendAndParse(Url, MoveTemp(OnDone));
	}

	bool ParsePlaces(const FString& Json, TArray<FTwinBLDPlace>& OutPlaces, FString& OutError)
	{
		OutPlaces.Reset();

		TSharedPtr<FJsonValue> Root;
		if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Root) || !Root.IsValid())
		{
			OutError = TEXT("Nominatim returned a response that is not valid JSON.");
			return false;
		}

		const TArray<TSharedPtr<FJsonValue>>* Array = nullptr;
		if (Root->TryGetArray(Array) && Array)
		{
			for (const TSharedPtr<FJsonValue>& Value : *Array)
			{
				FTwinBLDPlace Place;
				if (Value.IsValid() && ParsePlace(Value->AsObject(), Place))
				{
					OutPlaces.Add(MoveTemp(Place));
				}
			}
			return true;
		}

		const TSharedPtr<FJsonObject>* Object = nullptr;
		if (Root->TryGetObject(Object) && Object && Object->IsValid())
		{
			FString ServerError;
			if ((*Object)->TryGetStringField(TEXT("error"), ServerError))
			{
				// Reverse geocoding over open water or unmapped land reports "Unable to geocode".
				return true;
			}

			FTwinBLDPlace Place;
			if (ParsePlace(*Object, Place))
			{
				OutPlaces.Add(MoveTemp(Place));
			}
			return true;
		}

		OutError = TEXT("Nominatim returned an unexpected JSON shape.");
		return false;
	}
}
