#pragma once

#include "CoreMinimal.h"
#include "LandscapeImportHelper.h"
#include "LandscapeEditorObject.h"
#include "LandscapeProxy.h"
#include "UObject/Object.h"
#include "WorldBLDLandscapePaintImportOptions.generated.h"

class ALandscape;
class ULandscapeLayerInfoObject;
class ULandscapeMaterialInstanceConstant;
class UMaterialInterface;

USTRUCT()
struct FWorldBLDLandscapePaintLayer : public FLandscapeImportLayerInfo
{
	GENERATED_BODY()

	UPROPERTY(Category = "Import", VisibleAnywhere)
	TObjectPtr<ULandscapeMaterialInstanceConstant> ThumbnailMIC = nullptr;

	UPROPERTY(Category = "Import", VisibleAnywhere)
	ELandscapeImportResult ImportResult = ELandscapeImportResult::Success;

	UPROPERTY(Category = "Import", VisibleAnywhere)
	FText ErrorMessage;

	UPROPERTY(Category = "Import", EditAnywhere)
	bool bSelected = false;

	FLandscapeImportDescriptor ImportDescriptor;
};

UCLASS(Transient)
class UWorldBLDLandscapePaintImportOptions : public UObject
{
	GENERATED_BODY()

public:
	void Initialize(
		ALandscape* InLandscape,
		UMaterialInterface* InMaterial,
		const TArray<FName>& LayerNames,
		const TArray<TObjectPtr<ULandscapeLayerInfoObject>>& LayerInfos,
		bool bInFlipYAxis);

	void RefreshLayerImport(FWorldBLDLandscapePaintLayer& ImportLayer);
	void RefreshLayerImports();
	bool HasAnySelectedLayers() const;
	FIntPoint GetTargetImportResolution() const;

	UPROPERTY(Transient)
	TObjectPtr<ALandscape> TargetLandscape = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> LandscapeMaterial = nullptr;

	UPROPERTY(EditAnywhere, NonTransactional, Category = "Import", meta = (DisplayName = "Flip Y Axis"))
	bool bFlipYAxis = false;

	UPROPERTY(EditAnywhere, NonTransactional, EditFixedSize, Category = "Import", meta = (DisplayName = "Layers"))
	TArray<FWorldBLDLandscapePaintLayer> Layers;
};
