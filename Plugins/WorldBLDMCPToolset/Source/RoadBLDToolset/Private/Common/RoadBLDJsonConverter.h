// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolsetJsonConverter.h"

/**
 * Registry JSON converter for the toolset's input structs (preset specs, points, grid specs, ranges, endpoint refs).
 *
 * The registry's default importer cannot read a JSON array into a TOptional<TArray<...>> and reports any conversion
 * failure as one generic error. This converter imports field by field instead: null means unset for optional fields,
 * unknown fields are rejected, and every failure names the field path (for example Spec.RightLanes[1].Type).
 * Schemas and exported JSON match the registry defaults, except that struct fields are never listed as required:
 * omitted fields keep their defaults.
 */
class FRoadBLDJsonConverter : public UE::ToolsetRegistry::FToolsetJsonConverter
{
public:
	virtual FString GetName() const override;
	virtual bool CanConvertProperty(TNotNull<const FProperty*> Property) override;
	virtual TSharedPtr<FJsonObject> PropertyToJsonSchema(TNotNull<const FProperty*> Property) override;
	virtual TSharedPtr<FJsonValue> PropertyToDefault(TNotNull<const FProperty*> Property, const FString& DefaultString) override;
	virtual TSharedPtr<FJsonValue> PropertyToJsonData(TNotNull<FProperty*> Property, const void* Value) override;
	virtual bool JsonDataToProperty(
		const TSharedPtr<FJsonValue>& JsonValue,
		TNotNull<FProperty*> Property,
		void* OutValue,
		UObject* Outer) override;

	/**
	 * Imports JSON into a struct field by field. On failure, OutError names the failing field below RootPath, or is
	 * empty when a nested registry converter (object references) already raised its own error.
	 */
	static bool ImportStruct(
		const TSharedPtr<FJsonValue>& JsonValue,
		const UScriptStruct* Struct,
		void* OutStruct,
		const FString& RootPath,
		FString& OutError);

	static void Register();
	static void Unregister();

private:
	static bool ImportValue(
		const TSharedPtr<FJsonValue>& JsonValue,
		FProperty* Property,
		void* OutValue,
		const FString& Path,
		FString& OutError);

	static TSharedPtr<FRoadBLDJsonConverter> Instance;
};
