// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Volume.h"

#include "WorldBLDPropRemovalVolume.generated.h"

/**
 * Non-blocking editor volume used to suppress prop placement within its bounds.
 * Nothing fancy happening, just toggles for individual tools and functionality to get if we're in the volume or not(hardcoded for now, maybe later well addd toggles in the plugins themselves)
 */
UCLASS(BlueprintType)
class WORLDBLDRUNTIME_API AWorldBLDPropRemovalVolume : public AVolume
{
	GENERATED_BODY()

public:
	AWorldBLDPropRemovalVolume(const FObjectInitializer& ObjectInitializer);

	/** Master toggle for RoadBLD prop suppression in this volume. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prop Removal|RoadBLD")
	bool bAffectRoadBLDProps = true;

	/** Initial integration target: Static Meshes RoadModuleObjects generated during ADynamicRoad::BuildMesh(). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prop Removal|RoadBLD")
	bool bAffectRoadBLDStaticMeshRoadModules = true;

	/** Reserved for CityBLD prop suppression integration. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Prop Removal|CityBLD")
	bool bAffectCityBLDProps = true;

	/** Returns true when the location is inside any volume configured to remove RoadBLD static-mesh module props. */
	static bool ShouldRemoveRoadBLDStaticMeshModuleAtLocation(const UWorld* World, const FVector& WorldLocation);

private:
	bool ShouldSuppressRoadBLDStaticMeshModules() const;
};

