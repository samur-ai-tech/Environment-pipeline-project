// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Common/CityBLDToolsetTypes.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "CityBLDDiscoveryToolset.generated.h"

class ACityBlock;
class AModularBuildingActor;

/**
 * Understand a CityBLD city and the presets available to build one. Read-only: nothing here changes the level.
 * CityBLD concepts: a City Block (ACityBlock) is a closed outline, usually traced along road edges. Its District decides
 * how it is subdivided into Parcels and which Land Use each parcel gets. A Land Use spawns a modular building with one of
 * its Building Styles, a static prefab, or nothing. Modular buildings (AModularBuildingActor) can also be placed by hand.
 * Workflow: start with GetCityContext. Browse presets with ListPresets and read one with DescribeDistrict, DescribeLandUse
 * or DescribeBuildingStyle. Inspect the level with ListCityBlocks, DescribeBlock, ListParcels, ListModularBuildings and
 * DescribeBuilding. Run FindCityIssues before and after edits.
 * For CityBLD / WorldBLD packaging, cook, compile, or plugin-load errors (missing WorldBLD_Content, Unable to load plugin,
 * GeometryScripting), call WorldBLDToolset.UWorldBLDToolset.GetPackagingGuide — do not treat those as city-content issues.
 * Actor parameters take {"refPath": "..."} from these results; class parameters take ClassPath. World positions are
 * Unreal centimeters; fields ending in Meters are meters.
 *
 * Modular-mesh authoring contract: in Unreal local space, +X is module width, +Z is up, and the facade/front faces +Y.
 * With the project's Blender-to-Unreal export convention, author the front toward Blender -Y. Put sills and other
 * front-only details on that side and verify the imported face normals point outward. Use a lower-left back-plane origin
 * (Min X = 0, Min Z = 0, back plane Y = 0). AModularBuildingActor advances modules from imported static-mesh bounds,
 * not from the intended wall geometry. Therefore the complete X/Z perimeter must remain a sharp, perfect rectangle:
 * never bevel/chamfer its outer corners or let a sill, frame, trim, or any other detail exceed the intended X/Z bounds.
 * Details may project only in depth toward +Y. After import, check the exact X/Z bounds and place two copies edge-to-edge;
 * they must tile with no gap.
 */
UCLASS(BlueprintType, MinimalAPI)
class UCityBLDDiscoveryToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/** Summarizes the city in the current level: block, parcel and building counts, districts and styles in use, available presets, license state, running CityBLD jobs and suggested next steps. */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDCityContext GetCityContext();

	/**
	 * Lists CityBLD preset classes in the project, including CityBLD sample content. Loads the preset Blueprints.
	 * @param Kind Preset kind to list.
	 * @param Query Optional case-insensitive text matched against the name, class path and summary.
	 * @param MaxResults Maximum presets to return (1-1000).
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDPresetList ListPresets(ECityBLDPresetKind Kind, const FString& Query = TEXT(""), int32 MaxResults = 200);

	/**
	 * Describes a District: subdivision rules, weighted land uses, sidewalk, PCG graph and how many blocks use it.
	 * @param District District class path from ListPresets.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDDistrictDescription DescribeDistrict(TSubclassOf<UDistrict> District);

	/**
	 * Describes a Land Use: what it spawns, its building styles or prefabs, and which districts use it.
	 * @param LandUse Land Use class path from ListPresets or DescribeDistrict.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDLandUseDescription DescribeLandUse(TSubclassOf<ULandUse> LandUse);

	/**
	 * Describes a Building Style: height range, floors per height, roof, mesh sets, and which land uses spawn it.
	 * Before authoring or replacing a modular mesh, follow the orientation and rectangular-bounds contract in this
	 * toolset's description; AModularBuildingActor uses imported mesh bounds to place adjacent modules.
	 * @param Style Building Style class path from ListPresets or DescribeLandUse.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDBuildingStyleDescription DescribeBuildingStyle(TSubclassOf<UBuildingStyle> Style);

	/**
	 * Lists city blocks with their district, size, generation state and skeleton-subdivision risk.
	 * @param Bounds Optional world area in cm. Blocks whose outline overlaps it in XY are listed.
	 * @param MaxResults Maximum blocks to return (1-1000).
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDBlockList ListCityBlocks(TOptional<FCityBLDBounds> Bounds, int32 MaxResults = 200);

	/**
	 * Describes a city block: settings, outline, effective sidewalk, land use mix and parcels.
	 * @param Block City block to describe.
	 * @param bIncludeOutline Include the outer loop points.
	 * @param bIncludeParcels Include per-parcel details. Large blocks can have many parcels.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDBlockDescription DescribeBlock(ACityBlock* Block, bool bIncludeOutline = true, bool bIncludeParcels = true);

	/**
	 * Lists the parcels of a city block with their land use, area, street edges and spawned actors.
	 * @param Block City block whose parcels to list.
	 * @param LandUseFilter Optional case-insensitive text matched against the land use name and class path.
	 * @param bIncludeShapes Include each parcel's outline points.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDParcelList ListParcels(ACityBlock* Block, const FString& LandUseFilter = TEXT(""), bool bIncludeShapes = false);

	/**
	 * Lists modular buildings with their style, height, footprint and the block and parcel that spawned them.
	 * @param Bounds Optional world area in cm. Buildings whose footprint overlaps it in XY are listed.
	 * @param StyleFilter Optional case-insensitive text matched against the style name and class path.
	 * @param MaxResults Maximum buildings to return (1-1000).
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDBuildingList ListModularBuildings(TOptional<FCityBLDBounds> Bounds, const FString& StyleFilter = TEXT(""), int32 MaxResults = 200);

	/**
	 * Describes a modular building: footprint, floors, generation settings, roof override and floor plates.
	 * @param Building Modular building to describe.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDBuildingDescription DescribeBuilding(AModularBuildingActor* Building);

	/**
	 * Checks the city for problems: blocks without a district or parcels, slow skeleton subdivision, bad outlines,
	 * overlapping blocks, parcels missing their buildings, buildings without a style or footprint, overlapping buildings
	 * and buildings not registered to a parcel. Each issue has a suggested fix.
	 * @param Bounds Optional world area in cm to check.
	 * @param MaxResults Maximum issues to return (1-1000).
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FCityBLDIssueReport FindCityIssues(TOptional<FCityBLDBounds> Bounds, int32 MaxResults = 200);

	/**
	 * Runs FindCityIssues and returns a shared FBLDIssueReport for validation loops.
	 * Prefer this from WorldBLDValidationToolset.RunValidationLoop or cross-product agents.
	 */
	UFUNCTION(meta = (AICallable), Category = "CityBLDToolset")
	static FBLDIssueReport ValidateCity(TOptional<FCityBLDBounds> Bounds, int32 MaxResults = 200);
};
