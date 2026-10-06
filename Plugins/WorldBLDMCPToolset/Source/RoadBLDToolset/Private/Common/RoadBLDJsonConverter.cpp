// Copyright WorldBLD LLC. All rights reserved.

#include "Common/RoadBLDJsonConverter.h"

#include "Common/RoadBLDToolsetUtils.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"
#include "JsonObjectConverter.h"
#include "Presets/RoadBLDPresetSpec.h"
#include "ToolsetRegistry/ToolsetRegistrySubsystem.h"
#include "UObject/EnumProperty.h"
#include "UObject/PropertyOptional.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

TSharedPtr<FRoadBLDJsonConverter> FRoadBLDJsonConverter::Instance;

namespace RoadBLDJsonConverterPrivate
{
	/** Structs that tools take as parameters. Nested structs inside them are imported by the same converter. */
	const TArray<const UScriptStruct*>& GetClaimedStructs()
	{
		static const TArray<const UScriptStruct*> Structs =
		{
			FRoadBLDPresetSpec::StaticStruct(),
			FRoadBLDMaterialVariantSpec::StaticStruct(),
			FRoadBLDPoint::StaticStruct(),
			FRoadBLDGridSpec::StaticStruct(),
			FRoadBLDRange::StaticStruct(),
			FRoadBLDEndpointRef::StaticStruct(),
		};
		return Structs;
	}

	const UScriptStruct* GetClaimedStruct(const FProperty* Property)
	{
		const FStructProperty* StructProperty = CastField<FStructProperty>(Property);
		return StructProperty && GetClaimedStructs().Contains(StructProperty->Struct.Get()) ? StructProperty->Struct.Get() : nullptr;
	}

	/** Matches the registry schema: only fields an agent can see are importable. */
	bool IsVisibleField(const FProperty* Property)
	{
		EPropertyFlags VisibleFlags = CPF_BlueprintVisible | CPF_BlueprintAssignable;
		if (GEditor)
		{
			VisibleFlags |= CPF_Edit;
		}
		return Property->HasAnyPropertyFlags(VisibleFlags) && !Property->HasAnyPropertyFlags(CPF_Deprecated);
	}

	FString ToJsonKey(const FProperty* Property)
	{
		return FJsonObjectConverter::StandardizeCase(Property->GetAuthoredName());
	}

	FProperty* FindField(const UScriptStruct* Struct, const FString& Key)
	{
		for (TFieldIterator<FProperty> It(Struct); It; ++It)
		{
			if (IsVisibleField(*It) && (Key.Equals(It->GetAuthoredName(), ESearchCase::IgnoreCase) || Key.Equals(ToJsonKey(*It), ESearchCase::IgnoreCase)))
			{
				return *It;
			}
		}
		return nullptr;
	}

	FString ListFields(const UScriptStruct* Struct)
	{
		TArray<FString> Names;
		for (TFieldIterator<FProperty> It(Struct); It; ++It)
		{
			if (IsVisibleField(*It))
			{
				Names.Add(ToJsonKey(*It));
			}
		}
		return FString::Join(Names, TEXT(", "));
	}

	FString DescribeJson(const TSharedPtr<FJsonValue>& JsonValue)
	{
		switch (JsonValue.IsValid() ? JsonValue->Type : EJson::None)
		{
		case EJson::String:
			return FString::Printf(TEXT("'%s'"), *JsonValue->AsString());
		case EJson::Number:
		case EJson::Boolean:
		{
			FString Text;
			JsonValue->TryGetString(Text);
			return Text;
		}
		case EJson::Array:
			return TEXT("an array");
		case EJson::Object:
			return TEXT("an object");
		case EJson::Null:
			return TEXT("null");
		default:
			return TEXT("nothing");
		}
	}

	const UEnum* GetEnum(const FProperty* Property)
	{
		if (const FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property))
		{
			return EnumProperty->GetEnum();
		}
		if (const FByteProperty* ByteProperty = CastField<FByteProperty>(Property))
		{
			return ByteProperty->Enum;
		}
		return nullptr;
	}

	FString ListEnumValues(const UEnum* Enum)
	{
		TArray<FString> Names;
		for (int32 Index = 0; Index < Enum->NumEnums() - 1; ++Index)
		{
			if (!Enum->HasMetaData(TEXT("Hidden"), Index))
			{
				Names.Add(Enum->GetAuthoredNameStringByIndex(Index));
			}
		}
		return FString::Join(Names, TEXT(", "));
	}

	FString DescribeLeafFailure(const TSharedPtr<FJsonValue>& JsonValue, const FProperty* Property)
	{
		if (const UEnum* Enum = GetEnum(Property))
		{
			return FString::Printf(TEXT("%s is not a valid value. Use one of: %s."), *DescribeJson(JsonValue), *ListEnumValues(Enum));
		}
		if (Property->IsA<FNumericProperty>())
		{
			return FString::Printf(TEXT("expected a number, got %s."), *DescribeJson(JsonValue));
		}
		if (Property->IsA<FBoolProperty>())
		{
			return FString::Printf(TEXT("expected true or false, got %s."), *DescribeJson(JsonValue));
		}
		if (const FStructProperty* StructProperty = CastField<FStructProperty>(Property))
		{
			return FString::Printf(TEXT("expected a %s object, got %s."), *StructProperty->Struct->GetName(), *DescribeJson(JsonValue));
		}
		if (Property->IsA<FMapProperty>())
		{
			return FString::Printf(TEXT("expected an object of name/value pairs, got %s."), *DescribeJson(JsonValue));
		}
		return FString::Printf(TEXT("could not convert %s to %s."), *DescribeJson(JsonValue), *Property->GetCPPType());
	}

	bool HasOtherConverter(const FProperty* Property)
	{
		const TValueOrError<TObjectPtr<UToolsetRegistrySubsystem>, FString> Subsystem = UToolsetRegistrySubsystem::Get();
		if (!Subsystem.HasValue() || !Subsystem.GetValue())
		{
			return false;
		}

		const TSharedPtr<UE::ToolsetRegistry::FToolsetJsonConverter> Converter =
			Subsystem.GetValue()->ToolsetRegistry.GetConverterForProperty(Property);
		return Converter.IsValid() && Converter->GetName() != FString(TEXT("RoadBLDToolsetStructConverter"));
	}

	/** Struct fields are imported leniently (omitted fields keep defaults), so the schema must not require them. */
	void RemoveRequiredFromOwnStructs(const TSharedPtr<FJsonObject>& Schema)
	{
		if (!Schema.IsValid())
		{
			return;
		}

		FString Title;
		if (Schema->TryGetStringField(TEXT("title"), Title) && Title.StartsWith(TEXT("RoadBLD")))
		{
			Schema->RemoveField(TEXT("required"));
		}

		for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : Schema->Values)
		{
			if (Pair.Value->Type == EJson::Object)
			{
				RemoveRequiredFromOwnStructs(Pair.Value->AsObject());
			}
			else if (Pair.Value->Type == EJson::Array)
			{
				for (const TSharedPtr<FJsonValue>& Item : Pair.Value->AsArray())
				{
					if (Item->Type == EJson::Object)
					{
						RemoveRequiredFromOwnStructs(Item->AsObject());
					}
				}
			}
		}
	}
}

FString FRoadBLDJsonConverter::GetName() const
{
	return TEXT("RoadBLDToolsetStructConverter");
}

bool FRoadBLDJsonConverter::CanConvertProperty(TNotNull<const FProperty*> Property)
{
	return RoadBLDJsonConverterPrivate::GetClaimedStruct(Property) != nullptr;
}

TSharedPtr<FJsonObject> FRoadBLDJsonConverter::PropertyToJsonSchema(TNotNull<const FProperty*> Property)
{
	const UScriptStruct* Struct = RoadBLDJsonConverterPrivate::GetClaimedStruct(Property);
	TSharedPtr<FJsonObject> Schema = Struct ? ToolsetStructToJsonSchema(Struct, true) : MakeShared<FJsonObject>();
	RoadBLDJsonConverterPrivate::RemoveRequiredFromOwnStructs(Schema);
	return Schema;
}

TSharedPtr<FJsonValue> FRoadBLDJsonConverter::PropertyToDefault(TNotNull<const FProperty*> Property, const FString& DefaultString)
{
	const UScriptStruct* Struct = RoadBLDJsonConverterPrivate::GetClaimedStruct(Property);
	if (!Struct)
	{
		return MakeShared<FJsonValueNull>();
	}

	// UHT writes "()" for a defaulted struct parameter; ImportText fills the fields it names and keeps the rest.
	FStructOnScope Scope(Struct);
	CastField<FStructProperty>(Property)->ImportText_Direct(*DefaultString, Scope.GetStructMemory(), nullptr, PPF_None);
	const TSharedPtr<FJsonObject> Object = ToolsetStructToJsonData(Struct, Scope.GetStructMemory(), false);
	return Object.IsValid() ? StaticCastSharedRef<FJsonValue>(MakeShared<FJsonValueObject>(Object)) : MakeShared<FJsonValueNull>();
}

TSharedPtr<FJsonValue> FRoadBLDJsonConverter::PropertyToJsonData(TNotNull<FProperty*> Property, const void* Value)
{
	const UScriptStruct* Struct = RoadBLDJsonConverterPrivate::GetClaimedStruct(Property);
	const TSharedPtr<FJsonObject> Object = Struct && Value ? ToolsetStructToJsonData(Struct, Value, false) : nullptr;
	if (!Object.IsValid())
	{
		return nullptr;
	}
	return MakeShared<FJsonValueObject>(Object);
}

bool FRoadBLDJsonConverter::JsonDataToProperty(
	const TSharedPtr<FJsonValue>& JsonValue,
	TNotNull<FProperty*> Property,
	void* OutValue,
	UObject* Outer)
{
	const UScriptStruct* Struct = RoadBLDJsonConverterPrivate::GetClaimedStruct(Property);
	if (!Struct || !OutValue)
	{
		RoadBLDToolset::RaiseError(FString::Printf(TEXT("%s could not be converted."), *Property->GetAuthoredName()));
		return false;
	}

	FString Error;
	if (ImportStruct(JsonValue, Struct, OutValue, Property->GetAuthoredName(), Error))
	{
		return true;
	}

	// An empty error means a nested converter already raised a specific one; raising again would repeat it.
	if (!Error.IsEmpty())
	{
		RoadBLDToolset::RaiseError(Error);
	}
	return false;
}

bool FRoadBLDJsonConverter::ImportStruct(
	const TSharedPtr<FJsonValue>& JsonValue,
	const UScriptStruct* Struct,
	void* OutStruct,
	const FString& RootPath,
	FString& OutError)
{
	using namespace RoadBLDJsonConverterPrivate;

	const TSharedPtr<FJsonObject>* Object = nullptr;
	if (!JsonValue.IsValid() || !JsonValue->TryGetObject(Object) || !Object->IsValid())
	{
		OutError = FString::Printf(TEXT("%s: expected a %s object, got %s."), *RootPath, *Struct->GetName(), *DescribeJson(JsonValue));
		return false;
	}

	for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*Object)->Values)
	{
		FProperty* Field = FindField(Struct, Pair.Key);
		if (!Field)
		{
			OutError = FString::Printf(TEXT("%s.%s is not a field of %s. Fields: %s."), *RootPath, *Pair.Key, *Struct->GetName(), *ListFields(Struct));
			return false;
		}

		const FString FieldPath = FString::Printf(TEXT("%s.%s"), *RootPath, *Field->GetAuthoredName());
		void* FieldValue = Field->ContainerPtrToValuePtr<void>(OutStruct);
		if (!Pair.Value.IsValid() || Pair.Value->IsNull())
		{
			// null clears an optional field and leaves any other field at its default.
			if (const FOptionalProperty* Optional = CastField<FOptionalProperty>(Field))
			{
				Optional->MarkUnset(FieldValue);
			}
			continue;
		}

		if (!ImportValue(Pair.Value, Field, FieldValue, FieldPath, OutError))
		{
			return false;
		}
	}

	return true;
}

bool FRoadBLDJsonConverter::ImportValue(
	const TSharedPtr<FJsonValue>& JsonValue,
	FProperty* Property,
	void* OutValue,
	const FString& Path,
	FString& OutError)
{
	using namespace RoadBLDJsonConverterPrivate;

	if (const FOptionalProperty* Optional = CastField<FOptionalProperty>(Property))
	{
		if (JsonValue->IsNull())
		{
			Optional->MarkUnset(OutValue);
			return true;
		}
		return ImportValue(JsonValue, Optional->GetValueProperty(), Optional->MarkSetAndGetInitializedValuePointerToReplace(OutValue), Path, OutError);
	}

	if (!HasOtherConverter(Property))
	{
		if (const FArrayProperty* Array = CastField<FArrayProperty>(Property))
		{
			const TArray<TSharedPtr<FJsonValue>>* Items = nullptr;
			if (!JsonValue->TryGetArray(Items))
			{
				OutError = FString::Printf(TEXT("%s: expected an array, got %s."), *Path, *DescribeJson(JsonValue));
				return false;
			}

			FScriptArrayHelper Helper(Array, OutValue);
			Helper.EmptyValues();
			for (int32 Index = 0; Index < Items->Num(); ++Index)
			{
				const int32 ItemIndex = Helper.AddValue();
				if (!ImportValue((*Items)[Index], Array->Inner, Helper.GetRawPtr(ItemIndex), FString::Printf(TEXT("%s[%d]"), *Path, Index), OutError))
				{
					return false;
				}
			}
			return true;
		}

		if (const FStructProperty* StructProperty = CastField<FStructProperty>(Property))
		{
			return ImportStruct(JsonValue, StructProperty->Struct, OutValue, Path, OutError);
		}
	}

	if (JsonValue->IsNull())
	{
		OutError = FString::Printf(TEXT("%s: null is not allowed here."), *Path);
		return false;
	}

	if (!ToolsetJsonDataToProperty(JsonValue, Property, OutValue))
	{
		// Registry converters (object references) raise their own specific error before failing.
		OutError = HasOtherConverter(Property)
			? FString()
			: FString::Printf(TEXT("%s: %s"), *Path, *DescribeLeafFailure(JsonValue, Property));
		return false;
	}
	return true;
}

void FRoadBLDJsonConverter::Register()
{
	const TValueOrError<TObjectPtr<UToolsetRegistrySubsystem>, FString> Subsystem = UToolsetRegistrySubsystem::Get(TEXT("RoadBLDToolset"));
	if (Subsystem.HasValue() && Subsystem.GetValue())
	{
		Instance = MakeShared<FRoadBLDJsonConverter>();
		Subsystem.GetValue()->ToolsetRegistry.RegisterConverter(Instance);
	}
}

void FRoadBLDJsonConverter::Unregister()
{
	if (!Instance.IsValid())
	{
		return;
	}

	const TValueOrError<TObjectPtr<UToolsetRegistrySubsystem>, FString> Subsystem = UToolsetRegistrySubsystem::Get();
	if (Subsystem.HasValue() && Subsystem.GetValue())
	{
		Subsystem.GetValue()->ToolsetRegistry.UnregisterConverter(Instance);
	}
	Instance.Reset();
}
