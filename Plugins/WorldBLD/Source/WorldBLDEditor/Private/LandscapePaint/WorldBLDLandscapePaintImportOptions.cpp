#include "LandscapePaint/WorldBLDLandscapePaintImportOptions.h"

#include "Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeUtils.h"
#include "Materials/MaterialInterface.h"

void UWorldBLDLandscapePaintImportOptions::Initialize(
	ALandscape* InLandscape,
	UMaterialInterface* InMaterial,
	const TArray<FName>& LayerNames,
	const TArray<TObjectPtr<ULandscapeLayerInfoObject>>& LayerInfos,
	bool bInFlipYAxis)
{
	TargetLandscape = InLandscape;
	LandscapeMaterial = InMaterial;
	bFlipYAxis = bInFlipYAxis;
	Layers.Reset();

	FMaterialUpdateContext MaterialUpdateContext(FMaterialUpdateContext::EOptions::Default & ~FMaterialUpdateContext::EOptions::RecreateRenderStates);

	for (int32 Index = 0; Index < LayerNames.Num(); ++Index)
	{
		const FName LayerName = LayerNames[Index];
		if (LayerName.IsNone())
		{
			continue;
		}

		FWorldBLDLandscapePaintLayer NewLayer;
		NewLayer.LayerName = LayerName;
		NewLayer.LayerInfo = LayerInfos.IsValidIndex(Index) ? LayerInfos[Index] : nullptr;
		NewLayer.ThumbnailMIC = UE::Landscape::CreateLandscapeLayerThumbnailMIC(MaterialUpdateContext, InMaterial, LayerName);
		Layers.Add(MoveTemp(NewLayer));
	}

	RefreshLayerImports();
}

FIntPoint UWorldBLDLandscapePaintImportOptions::GetTargetImportResolution() const
{
	if (!IsValid(TargetLandscape))
	{
		return FIntPoint::ZeroValue;
	}

	const ULandscapeInfo* LandscapeInfo = TargetLandscape->GetLandscapeInfo();
	if (!LandscapeInfo)
	{
		return FIntPoint::ZeroValue;
	}

	FIntRect ImportRegion;
	if (!LandscapeInfo->GetLandscapeExtent(ImportRegion))
	{
		return FIntPoint::ZeroValue;
	}

	ImportRegion.Max.X += 1;
	ImportRegion.Max.Y += 1;
	return FIntPoint(ImportRegion.Width(), ImportRegion.Height());
}

void UWorldBLDLandscapePaintImportOptions::RefreshLayerImport(FWorldBLDLandscapePaintLayer& ImportLayer)
{
	ImportLayer.ErrorMessage = FText();
	ImportLayer.ImportResult = ELandscapeImportResult::Success;
	ImportLayer.ImportDescriptor.Reset();

	if (ImportLayer.LayerName == ALandscapeProxy::VisibilityLayer->GetLayerName())
	{
		ImportLayer.LayerInfo = ALandscapeProxy::VisibilityLayer;
	}

	if (ImportLayer.SourceFilePath.IsEmpty())
	{
		return;
	}

	if (!ImportLayer.LayerInfo)
	{
		ImportLayer.ImportResult = ELandscapeImportResult::Error;
		ImportLayer.ErrorMessage = NSLOCTEXT("WorldBLD.PaintLandscape", "MissingLayerInfo", "Can't import a layer file without a layer info object.");
		return;
	}

	FText DescriptorMessage;
	ImportLayer.ImportResult = FLandscapeImportHelper::GetWeightmapImportDescriptor(
		ImportLayer.SourceFilePath,
		/*bSingleFile=*/true,
		bFlipYAxis,
		ImportLayer.LayerName,
		ImportLayer.ImportDescriptor,
		DescriptorMessage);
	ImportLayer.ErrorMessage = DescriptorMessage;

	if (ImportLayer.ImportResult != ELandscapeImportResult::Success)
	{
		return;
	}

	const FIntPoint ExpectedResolution = GetTargetImportResolution();
	if (ExpectedResolution.X <= 0 || ExpectedResolution.Y <= 0)
	{
		return;
	}

	if (ImportLayer.ImportDescriptor.FindDescriptorIndex(ExpectedResolution.X, ExpectedResolution.Y) == INDEX_NONE)
	{
		// Allow import anyway; PaintTargetLandscape resamples via TransformWeightmapImportData.
		ImportLayer.ImportResult = ELandscapeImportResult::Warning;
		ImportLayer.ErrorMessage = NSLOCTEXT("WorldBLD.PaintLandscape", "ResolutionMismatch", "Weightmap import resolution does not match target landscape resolution. The weightmap will be resampled on import.");
	}
}

void UWorldBLDLandscapePaintImportOptions::RefreshLayerImports()
{
	for (FWorldBLDLandscapePaintLayer& ImportLayer : Layers)
	{
		RefreshLayerImport(ImportLayer);
	}
}

bool UWorldBLDLandscapePaintImportOptions::HasAnySelectedLayers() const
{
	for (const FWorldBLDLandscapePaintLayer& Layer : Layers)
	{
		if (Layer.bSelected && !Layer.SourceFilePath.IsEmpty() && Layer.ImportResult != ELandscapeImportResult::Error)
		{
			return true;
		}
	}

	return false;
}
