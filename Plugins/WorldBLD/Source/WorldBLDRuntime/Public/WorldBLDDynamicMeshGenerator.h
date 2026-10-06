// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "MeshDescription.h"
#include "StaticMeshAttributes.h"
#include "MeshDescriptionBuilder.h"
#include "IndexTypes.h"
#include "WorldBLDDynamicMeshGenerator.generated.h"

class AWorldBLDGeo;
class UMaterialInterface;
class UStaticMesh;

/**
 * Base class for WorldBLD dynamic mesh generators.
 * Provides a common foundation for mesh generation functionality
 * used across different WorldBLD plugins, including Delaunay triangulation
 * and mesh description building.
 */
UCLASS()
class WORLDBLDRUNTIME_API UWorldBLDDynamicMeshGenerator : public UObject
{
	GENERATED_BODY()
	
public:
	UWorldBLDDynamicMeshGenerator();

	/**
	 * Recenters the accumulated vertex positions so the owning actor sits at the XY bounds center of the generated geometry.
	 *
	 * This is primarily used to make geometry-only actors stream correctly in World Partition:
	 * - The actor's XY location becomes the geometry center (Z is preserved)
	 * - Vertex positions are shifted so the generated geometry stays in the same world-space location
	 * - Attached spline-mesh start/end params and instanced-static-mesh instance transforms are
	 *   rebased the same way, so they do not inherit the pivot delta as a world-space offset
	 *
	 * Important: call this AFTER all triangles are added, and BEFORE CreateMesh()/BuildFromMeshDescriptions().
	 * If vertices were authored in world space, the actor transform must be identity first; otherwise
	 * the world-space positions are treated as local and the mesh is double-translated.
	 *
	 * @param TargetActor Actor whose transform should be moved to the generated bounds center (XY only).
	 * @param OutWorldCenter Optional output of the computed world-space center (XY center; Z = actor Z).
	 * @return True if a recenter was applied.
	 */
	bool CenterGeneratedMeshOnActorXY(AActor* TargetActor, FVector* OutWorldCenter = nullptr);

	// ==================== Core Mesh Building ====================

	/**
	 * Gets or creates a polygon group ID for the specified material.
	 * @param Material The material to get/create a group for (can be nullptr)
	 * @return The polygon group ID for this material
	 */
	FPolygonGroupID GetGroupID(UMaterialInterface* Material);

	/**
	 * Creates the final static mesh from the accumulated mesh description.
	 * @param Outer The outer object for the new mesh
	 * @param Name Optional name for the mesh
	 * @param Flags Object flags for the new mesh
	 * @return The created static mesh, or nullptr if no geometry was added
	 */
	UStaticMesh* CreateMesh(UObject* Outer, FName Name = NAME_None, EObjectFlags Flags = RF_Transactional);

	/** Returns the accumulated mesh description without building a UStaticMesh. */
	const FMeshDescription* GetMeshDescription() const { return MeshDescription.Get(); }

	/** Returns materials ordered by polygon group ID so dynamic preview output matches static mesh slots. */
	void GetOrderedPolygonGroupMaterials(TArray<UMaterialInterface*>& OutMaterials) const;

	// ==================== Triangle Addition ====================

	/**
	 * Adds triangles to the mesh with the specified material.
	 * @param Material The material to apply
	 * @param Triangles Array of triangle indices
	 * @param Vertices Array of vertex positions
	 */
	void AddTriangles(UMaterialInterface* Material, const TArray<UE::Geometry::FIndex3i>& Triangles, const TArray<FVector>& Vertices);

	/**
	 * Adds triangles to the mesh with the specified material and UVs.
	 * @param Material The material to apply
	 * @param Triangles Array of triangle indices
	 * @param Vertices Array of vertex positions
	 * @param UVs Array of UV coordinates
	 */
	void AddTriangles(UMaterialInterface* Material, const TArray<UE::Geometry::FIndex3i>& Triangles, const TArray<FVector>& Vertices, const TArray<FVector2D>& UVs);

	/**
	 * Adds triangles to the mesh with the specified material, UVs, and per-vertex colors.
	 * If VertexColors is empty or mismatched, defaults to black for all vertex instances.
	 * @param Material The material to apply
	 * @param Triangles Array of triangle indices
	 * @param Vertices Array of vertex positions
	 * @param UVs Array of UV coordinates
	 * @param VertexColors Array of vertex colors (must match Vertices.Num())
	 */
	void AddTriangles(UMaterialInterface* Material, const TArray<UE::Geometry::FIndex3i>& Triangles, const TArray<FVector>& Vertices, const TArray<FVector2D>& UVs, const TArray<FColor>& VertexColors);

	/**
	 * Adds triangles with explicit per-vertex normals.
	 * If VertexNormals is empty or mismatched, falls back to internally computed smooth normals.
	 */
	void AddTriangles(UMaterialInterface* Material, const TArray<UE::Geometry::FIndex3i>& Triangles, const TArray<FVector>& Vertices, const TArray<FVector2D>& UVs, const TArray<FColor>& VertexColors, const TArray<FVector>& VertexNormals);

	/**
	 * Adds triangles to the mesh preserving both UV0 and UV1 from the source data.
	 * Requires SetNumUVLayers(>= 2) to have been called before any triangles are added.
	 * @param Material The material to apply
	 * @param Triangles Array of triangle indices
	 * @param Vertices Array of vertex positions
	 * @param UV0s Array of UV channel 0 coordinates
	 * @param UV1s Array of UV channel 1 coordinates (may be empty; zeros used for missing entries)
	 */
	void AddTriangles(UMaterialInterface* Material, const TArray<UE::Geometry::FIndex3i>& Triangles, const TArray<FVector>& Vertices, const TArray<FVector2D>& UV0s, const TArray<FVector2D>& UV1s);

	/**
	 * Backward-compatibility shim for call sites that provided UV0, UV1, and per-vertex colors.
	 * Uses UV0/UV1 where provided, while preserving the existing default-black behavior for missing colors.
	 */
	void AddTriangles(UMaterialInterface* Material, const TArray<UE::Geometry::FIndex3i>& Triangles, const TArray<FVector>& Vertices, const TArray<FVector2D>& UV0s, const TArray<FVector2D>& UV1s, const TArray<FColor>& VertexColors);

	/**
	 * Adds triangles using 2D vertices (Z=0).
	 * @param Material The material to apply
	 * @param Triangles Array of triangle indices
	 * @param Vertices Array of 2D vertex positions
	 */
	void AddTriangles(UMaterialInterface* Material, const TArray<UE::Geometry::FIndex3i>& Triangles, const TArray<FVector2D>& Vertices)
	{
		TArray<FVector> Positions;
		Positions.AddUninitialized(Vertices.Num());
		for (int32 i = 0; i < Vertices.Num(); i++)
		{
			Positions[i] = FVector(Vertices[i], 0);
		}
		AddTriangles(Material, Triangles, Positions);
	}

	// ==================== Polygon Triangulation ====================

	/**
	 * Triangulates a polygon and adds it to the mesh (no material).
	 * @param Transform Transform to apply to the polygon
	 * @param PolygonPoints The polygon vertices
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddTriangulatedPolygon(FTransform Transform, TArray<FVector> PolygonPoints, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon and adds it to the mesh with a material.
	 * @param Material The material to apply
	 * @param Transform Transform to apply to the polygon
	 * @param PolygonPoints The polygon vertices
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddTriangulatedPolygon(UMaterialInterface* Material, FTransform Transform, TArray<FVector> PolygonPoints, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon using Delaunay algorithm and adds interior points for mesh density.
	 * @param Material The material to apply
	 * @param InVertices The polygon boundary vertices
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygon(UMaterialInterface* Material, const TArray<FVector>& InVertices,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with interior holes using constrained Delaunay and adds it to the mesh.
	 * @param Material The material to apply
	 * @param OuterRing The outer boundary vertices
	 * @param HoleRings Interior hole boundary rings
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithHoles(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with interior holes using constrained Delaunay and adds it to the mesh,
	 * using custom UV generation.
	 * @param Material The material to apply
	 * @param OuterRing The outer boundary vertices
	 * @param HoleRings Interior hole boundary rings
	 * @param UVGenerator Callback that maps generated vertex world positions to UVs
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithHoles(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, const TFunction<FVector2D(const FVector&)>& UVGenerator,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with interior holes using constrained Delaunay and adds it to the mesh,
	 * using custom UV generation and per-vertex displacement callback.
	 * @param Material The material to apply
	 * @param OuterRing The outer boundary vertices
	 * @param HoleRings Interior hole boundary rings
	 * @param UVGenerator Callback that maps generated vertex world positions to UVs
	 * @param VertexDisplacementFunc Callback that returns a Z offset for a generated vertex world position
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithHoles(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, const TFunction<FVector2D(const FVector&)>& UVGenerator,
		const TFunction<float(const FVector&)>& VertexDisplacementFunc,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with interior holes using constrained Delaunay and adds it to the mesh,
	 * assigning per-vertex colors via callback.
	 * @param Material The material to apply
	 * @param OuterRing The outer boundary vertices
	 * @param HoleRings Interior hole boundary rings
	 * @param VertexColorFunc Callback that maps a generated vertex world position to a color
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithHolesColored(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, TFunctionRef<FColor(const FVector&)> VertexColorFunc,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with interior holes using constrained Delaunay and adds it to the mesh,
	 * using custom UV generation and assigning per-vertex colors via callback.
	 * @param Material The material to apply
	 * @param OuterRing The outer boundary vertices
	 * @param HoleRings Interior hole boundary rings
	 * @param UVGenerator Callback that maps generated vertex world positions to UVs
	 * @param VertexColorFunc Callback that maps a generated vertex world position to a color
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithHolesColored(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, const TFunction<FVector2D(const FVector&)>& UVGenerator,
		TFunctionRef<FColor(const FVector&)> VertexColorFunc, float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with interior holes using constrained Delaunay and adds it to the mesh,
	 * using custom UV generation, per-vertex displacement, and per-vertex colors.
	 * @param Material The material to apply
	 * @param OuterRing The outer boundary vertices
	 * @param HoleRings Interior hole boundary rings
	 * @param UVGenerator Callback that maps generated vertex world positions to UVs
	 * @param VertexDisplacementFunc Callback that returns a Z offset for a generated vertex world position
	 * @param VertexColorFunc Callback that maps a generated vertex world position to a color
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithHolesColored(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, const TFunction<FVector2D(const FVector&)>& UVGenerator,
		const TFunction<float(const FVector&)>& VertexDisplacementFunc,
		TFunctionRef<FColor(const FVector&)> VertexColorFunc, float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with interior holes using constrained Delaunay and assigns absolute
	 * vertex heights via callback after triangulation. This is useful when the boundary topology
	 * should remain boolean-driven, but the final surface Z must come from an analytic evaluator.
	 * @param Material The material to apply
	 * @param OuterRing The outer boundary vertices
	 * @param HoleRings Interior hole boundary rings
	 * @param UVGenerator Callback that maps generated vertex world positions to UVs
	 * @param VertexHeightFunc Callback that returns the final absolute Z for a generated vertex
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithHolesEvaluated(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, const TFunction<FVector2D(const FVector&)>& UVGenerator,
		const TFunction<float(const FVector&)>& VertexHeightFunc,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Same as AddDelaunayTriangulatedPolygonWithHolesEvaluated(), but also assigns per-vertex colors.
	 */
	void AddDelaunayTriangulatedPolygonWithHolesEvaluatedColored(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, const TFunction<FVector2D(const FVector&)>& UVGenerator,
		const TFunction<float(const FVector&)>& VertexHeightFunc,
		TFunctionRef<FColor(const FVector&)> VertexColorFunc,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with holes, solves interior heights via Laplacian relaxation, and then
	 * re-evaluates only boundary vertices with the supplied absolute-height callback.
	 * This preserves seam correctness while avoiding per-interior evaluator bumps.
	 */
	void AddDelaunayTriangulatedPolygonWithHolesBoundaryLockedColored(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, const TFunction<FVector2D(const FVector&)>& UVGenerator,
		const TFunction<float(const FVector&)>& BoundaryHeightFunc,
		TFunctionRef<FColor(const FVector&)> VertexColorFunc,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon with holes, solves interior heights via Laplacian relaxation, and applies an
	 * optional soft interior target term (z_target, lambda) to preserve near-seam slope continuity.
	 */
	void AddDelaunayTriangulatedPolygonWithHolesGuidedColored(UMaterialInterface* Material, const TArray<FVector>& OuterRing,
		const TArray<TArray<FVector>>& HoleRings, const TFunction<FVector2D(const FVector&)>& UVGenerator,
		const TFunction<bool(const FVector&, float&, float&)>& InteriorHeightGuidanceFunc,
		TFunctionRef<FColor(const FVector&)> VertexColorFunc,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon using Delaunay algorithm and adds interior points for mesh density,
	 * then applies an upward-only Perlin-style displacement to interior (non-boundary) vertices.
	 * Boundary vertices are left unchanged.
	 *
	 * @param Material The material to apply
	 * @param InVertices The polygon boundary vertices
	 * @param DisplacementAmount Upward displacement amount in cm (0 disables displacement)
	 * @param DisplacementScale Noise scale in cm (larger = smoother/broader noise)
	 * @param Seed Stable seed for per-polygon variation
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonDisplaced(UMaterialInterface* Material, const TArray<FVector>& InVertices,
		double DisplacementAmount, double DisplacementScale, int32 Seed, float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon using Delaunay algorithm and adds interior points for mesh density,
	 * applying a custom displacement callback to interior (non-boundary) vertices only.
	 * Boundary vertices are left unchanged to maintain continuity with adjacent geometry.
	 *
	 * @param Material The material to apply
	 * @param InVertices The polygon boundary vertices
	 * @param InteriorDisplacementFunc Callback that returns a Z offset for a given vertex world position (interior vertices only)
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithCallback(UMaterialInterface* Material, const TArray<FVector>& InVertices,
		TFunctionRef<float(const FVector&)> InteriorDisplacementFunc, float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon using Delaunay algorithm and adds interior points for mesh density,
	 * applying a custom displacement callback to interior vertices and assigning per-vertex colors via callback.
	 * Boundary vertices are left undisplaced to maintain continuity with adjacent geometry.
	 *
	 * @param Material The material to apply
	 * @param InVertices The polygon boundary vertices
	 * @param InteriorDisplacementFunc Callback that returns a Z offset for a given vertex world position (interior vertices only)
	 * @param VertexColorFunc Callback that maps generated vertex position to a color
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonWithCallbackColored(UMaterialInterface* Material, const TArray<FVector>& InVertices,
		TFunctionRef<float(const FVector&)> InteriorDisplacementFunc, TFunctionRef<FColor(const FVector&)> VertexColorFunc,
		float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon using Delaunay algorithm and adds interior points for mesh density,
	 * assigning per-vertex colors via callback.
	 * @param Material The material to apply
	 * @param InVertices The polygon boundary vertices
	 * @param VertexColorFunc Callback that maps generated vertex position to a color
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddDelaunayTriangulatedPolygonColored(UMaterialInterface* Material, const TArray<FVector>& InVertices,
		TFunctionRef<FColor(const FVector&)> VertexColorFunc, float DuplicatePointEpsilon = 0.5f, bool bReverseWindingOrder = false);

	/**
	 * Triangulates a polygon using robust ear clipping with cleanup.
	 * @param Material The material to apply
	 * @param InVertices The polygon boundary vertices
	 * @param DuplicatePointEpsilon Tolerance for duplicate point detection
	 * @param MinEdgeLength Minimum edge length (smaller edges are removed)
	 * @param MinSpikeAngleDeg Minimum angle for spike removal
	 * @param bReverseWindingOrder Whether to reverse the winding order
	 */
	void AddRobustTriangulatedPolygon(UMaterialInterface* Material, const TArray<FVector>& InVertices,
		float DuplicatePointEpsilon = 0.5f, float MinEdgeLength = 1.0f, float MinSpikeAngleDeg = 5.0f, bool bReverseWindingOrder = false);

	// ==================== UV Layer Configuration ====================

	/**
	 * Sets the number of UV layers in the underlying mesh description.
	 * Must be called BEFORE any AddTriangles calls. Defaults to 1 (UV0 only).
	 * Use 2 to also store UV1, 3 to store UV0+UV1+UV2 (e.g. for lightmaps in UV2).
	 */
	void SetNumUVLayers(int32 NumLayers);

	/**
	 * Backward-compatibility helper for older call paths that directly configured lightmap UV generation.
	 */
	void SetLightmapUVGeneration(bool bInGenerateLightmapUVs, int32 InDestinationChannel = 1);

	// ==================== Configuration ====================

	/** When true, the resulting UStaticMesh will have Nanite enabled. Must be set before CreateMesh() is called. */
	bool bEnableNanite = false;

	/** When true, generates a non-overlapping lightmap UV channel during CreateMesh(). */
	bool bGenerateLightmapUVs = false;

	/**
	 * Destination UV channel index for the generated lightmap UVs (used when bGenerateLightmapUVs is true).
	 * Defaults to 1. Set to 2 when UV1 is already used by materials so lightmaps do not overwrite it.
	 */
	int32 LightmapUVDestinationChannel = 1;

	/** Grid spacing for interior point generation in Delaunay triangulation */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mesh Generation")
	double DelaunayGridSpacing = 300.0;

	/** Texture scale for UV generation */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mesh Generation")
	double TextureScale = 200.0;

	/** UV scale multiplier for triangulated polygons */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mesh Generation")
	double PolygonUVScaleMultiplier = 3.0;

protected:
	// Mesh building infrastructure
	TSharedPtr<FMeshDescription> MeshDescription;
	TSharedPtr<FStaticMeshAttributes> MeshAttributes;
	TSharedPtr<FMeshDescriptionBuilder> Builder;
	TMap<UMaterialInterface*, FPolygonGroupID> PolygonGroups;
};
