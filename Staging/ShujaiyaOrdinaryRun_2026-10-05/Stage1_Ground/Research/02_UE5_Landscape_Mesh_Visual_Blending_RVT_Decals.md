# Comprehensive Technical Report: Methodologies for Visual Integration and Blending Between Landscape Surfaces and Models in Unreal Engine 5

> Provenance: research text pasted by Aviv into Claude Code on 2026-10-05 (origin: external report, author unknown). Saved verbatim as REFERENCE material. Claims are DOCUMENTED-BY-REPORT only; verify against official Epic docs before relying on any setting, node or CVar. Takeaways applied to the plan are in `../STAGE1_GROUND_PLAN.md` ("Research intake").

## 1. Introduction to the Environmental Blending System

The pursuit of absolute realism in virtual environments requires tackling a complex challenge well known to graphics engineers: eliminating the geometric and visual "seam" created at the intersection between static 3D models (such as rocks, ruins, or tree trunks) and the landscape surfaces on which they are placed. Unreal Engine 5 offers a multi-layered architecture to resolve this issue, based on a structured workflow that must be implemented in stages. The optimal strategy begins with creating a complete and continuous landscape material, continues with applying a systemic visual connection using Runtime Virtual Texturing (RVT), moves to adding local details via DBuffer Decals to break uniformity, and concludes with separate geometric fixes to deal with height differences and elevated surfaces.

This report details exactly how to implement each of these techniques in the workspace, while analyzing the technical implications on the Deferred Rendering Pipeline, GPU memory management (VRAM), and performance optimization.

## 2. Implementing Runtime Virtual Texturing (RVT)

The RVT system is designed to solve the problem of visual mismatch by allowing the static model to "inherit" the color, roughness, and normal attributes of the specific landscape it rests upon. Instead of loading massive textures into video memory, the system generates and stores texel data on demand, dividing it into tiles managed in a Page Table. To implement this in practice, preparation is required at the project level, the level environment, and the Material Graphs.

### 2.1 Project Settings and Virtualization Space Deployment

The first step in the solution architecture requires enabling systemic support. Through the Project Settings menu, under the Rendering category (Engine > Rendering > Virtual Textures), you must enable "Enable Virtual Texture Support" and restart the engine. After restarting, the workflow begins by creating a new data asset. In the Content Browser, under the Materials & Textures category, create a "Runtime Virtual Texture" resource. It is common to create two separate resources: one for photometric display data (Base Color, Normal, Roughness, Specular) and another to store only height data (World Height), in order to streamline data streaming and prevent bandwidth congestion.

After creating the RVT asset, a "Runtime Virtual Texture Volume" object must be placed in the workspace. This object serves as a bounding box defining the physical space where texture capture and projection occur. To map the space accurately, select the Volume object, navigate to the Details Panel under the "Transform from Bounds" category, select the Landscape in the "Source Actor" field, and click the "Set Bounds" button. This action will stretch and align the virtualization volume so that it precisely encompasses the entire landscape topology. Finally, assign the previously created RVT asset into the Virtual Texture slot located in the Volume's details.

### 2.2 Writing Data from the Landscape Material

For the landscape to transmit its data to the RVT palette, its applied material must be updated. Within the landscape's material editor, a Runtime Virtual Texture Output node is added. All complex layer calculations of the landscape, which previously flowed directly to the main material output, must now also be routed to the matching pins of this output node (such as Base Color, Roughness, Normal).

It is important to integrate a safety mechanism for weaker hardware platforms or end devices that do not support virtualization. For this, developers use the Virtual Texture Feature Switch node. The original material logic is fed into the "No" input of this node, while the "Yes" input is fed by a Runtime Virtual Texture Sample node that reads the data back from the RVT. This ensures that the landscape surface will always display properly.

A crucial geometric issue at this stage concerns the vector space of the normals. Texture normals are traditionally represented in Tangent Space, which is relative to the polygon's angle. Since the RVT captures the landscape from a fixed top-down projection, saving normals in Tangent Space will lead to severe lighting distortions when a model with a different angle samples them. Therefore, the developer must use a TransformVector node to convert the landscape normals from Tangent Space to World Space before feeding them into the RVT Output node. Storing normals in the RVT as absolute World Space is key to a seamless blending of lighting and reflections.

### 2.3 Sampling Data and Integrating It into Static Models

The complementary phase of the architecture takes place inside the materials of the objects intended to blend into the landscape (such as rocks or grass sheets). In the object's material editor, place a Runtime Virtual Texture Sample Parameter node. Using the parameter version is essential as it will later allow control over the resource via Material Instances without needing to recompile the shader code.

The data sampled from the RVT (color, roughness, world normal) is combined with the local data of the rock using a Linear Interpolation (Lerp) node. The Alpha value (which determines the blending influence area) is typically calculated based on vertical distance from the ground, or via mathematical subtraction between the pixel's Absolute World Position and the virtual ground height sampled simultaneously.

To complete the normal space correction that started in the landscape material, the world normal output sampled from the RVT must be taken into the rock's material, converted back to the rock's Tangent Space using a TransformVector node (this time from World Space to Tangent Space), and then blended with the rock's normal map. Alternatively, the "Tangent Space Normal" option in the rock's material settings can be completely disabled, allowing direct work with world normal output.

To finalize the process, select the rock itself in the game world, and in the details panel under the Virtual Texture category, add the RVT resource to the "Render to Virtual Textures" array.

### 2.4 Memory Management and Performance Optimization in RVT

Using the RVT system requires continuous video memory allocation from the GPU and necessitates strict load regulation. Tile streaming management is done via dedicated console variables (CVARs).

| Console Variable | Functional Meaning and Performance Implications |
|---|---|
| r.VT.MaxUploadsPerFrame | Defines the maximum amount of virtual memory page uploads per single frame. Lowering the value (e.g., to 4 or 8) reduces bandwidth loads and prevents stuttering, but comes at the cost of slower visual updates for fast movements. |
| r.VT.MaxContinuousUpdatesPerFrame | Controls the number of updates for existing tiles already mapped in memory. Especially relevant for RVT assets set to update continuously (e.g., for dynamic tracks or impacts). |
| r.VT.PoolSizeScale | A multiplier factor that changes the physical size of the virtual memory pools. Lowering the value below 1 will reduce essential VRAM consumption on constrained platforms, but may lead to cyclical memory thrashing that significantly lowers performance. |
| r.VT.RVT.TileCountBias | Adjusts the final output resolution of the RVT. Entering a value of -1 will halve the resolution, while 1 will double it. |

Additionally, the Landscape component contains a Virtual Texture Num LODs setting. Setting this value to 0 is most optimal for the GPU, as it instructs the system to render each landscape section into the RVT as a single, flat quad. Higher values are only required if the landscape material includes particularly high-frequency data interpolation across vertices, which generates considerable processing load.

## 3. Breaking Uniformity and Creating Local Details Using Epic Decals

While the RVT system solves overall blending uniformity, real-world landscape surfaces are characterized by local micro-disturbances: cracks, dust accumulations, puddles, tire tracks, and weathering. Injecting these details without increasing the polygon count or adding heavy material layers to the landscape is efficiently done using Deferred Decals.

### 3.1 DBuffer Decals Architecture vs. GBuffer

In previous engine iterations, decals were integrated late in the rendering pipeline, right before lighting calculations (GBuffer Decals). This method was flawed, as decals did not react correctly to baked lighting (Lightmaps) or static ambient lighting (Sky Lighting).

Unreal Engine 5 solves this by enabling DBuffer (Decal Buffer) technology as a default in project settings. The DBuffer system pre-collects the base colors, normals, and roughness of all decals in the scene into a dedicated buffer before or during the Base Pass. When objects are drawn on screen, their materials sample the DBuffer and integrate the decals at an early stage, ensuring all global illumination and shading calculations affect the decal and object as one consistent physical unit.

### 3.2 Creating Decals and Applying Them to the Environment

To create a material functioning as a valid decal, the developer must set its Material Domain attribute to Deferred Decal. The Blend Mode attribute must be set to Translucent or Alpha Composite. It is important to note that the Modulate blend mode is not supported with DBuffer technology; setting it will cause the engine to silently fall back to Translucent mode, resulting in undesirable visual outcomes.

The central control mechanism for decal efficiency and impact is the Decal Response (DBuffer) attribute found in the details of the material receiving the decal (e.g., the landscape material). This attribute defines which channels will be affected:

| Decal Response Attribute | Real-World Application and Performance Meaning |
|---|---|
| None | The object completely ignores the decal system projected onto it. Used for optimization and saving sampling resources for dynamic models, or when the material uses the ApplyDBuffer node allowing full internal logical control. |
| Color Normal Roughness | The default state, accepting the full dataset of the decal. This is the most demanding state in terms of memory bandwidth. |
| Normal or Roughness | Allows creating dedicated decals that alter reflection properties only (like wet puddle roughness) or visual bumps (scratches) without changing the original model color, saving heavy DBuffer memory calls. |

After material creation, practical application is done by dragging a Decal Actor object into the level. This object displays as a wireframe box with an arrow indicating the projection direction. Any polygonal surface falling within the box volume will absorb the decal. To manage situations with overlapping decals, the system provides a Sort Order parameter in the Actor's details window. Decals with higher numerical values will render on top of those with lower values.

Special Technical Issue - Normal Reprojection: An inherent flaw in the DBuffer shader architecture stems from the inability to simultaneously read and write normals in the same frame without risking visual facetting artifacts where geometry triangles become visible. To prevent these flaws in normal-based decals applied to sharp-angled objects, the console variable r.Decal.NormalProjectionEnabled can be activated. This mechanism uses the Velocity Output vector from the previous frame's Depth Prepass to perform an accurate projection of the normal onto the surface.

## 4. Managing Pre-made Material Setup Using Material Instances

Workflows in surface blending require endless iterations of fine-tuning: adjusting surface roughness, altering displacement map scale, varying decal colors, and calibrating RVT masks. In Unreal Engine, every logical change in a material node requires Shader Compilation. In systems with highly complex materials, this process can take long minutes and paralyze environmental artists' workflow efficiency.

The systemic solution is the extensive use of Material Instances. A material instance is not a new shader; it is a lightweight memory allocation that stores an array of dynamic variables linked to predefined parameters inside the "Master Material". To enable this, the lead developer must pre-plan the master material and convert constant values to parameters.

Best Practices in Applying Parameters:

- Exposing Textures: Using the Texture Sample Parameter 2D node allows artists to swap color, normal, and roughness maps without touching the complex blending logic. Thus, the same master material can be used for a wide variety of rocks, paths, or decals.
- Exposing the RVT Source: Using the Runtime Virtual Texture Sample Parameter node instead of the standard sample node is critical. It allows the system to point a specific material instance toward a different RVT Volume (e.g., when transitioning from a snowy level to a desert level) while using the same unified rendering logic.
- Analytical Control over Blending: Converting multiplication variables into Scalar Parameter variables enables real-time control over texture scale (UV Tiling), height mask contrast intensity, and the dominance of the RVT color over the model.

Through this paradigm, the intricate RVT logic and normal space conversions are protected and locked inside the master material, while the design team gets a clean, immediate interface with real-time impact, significantly improving project uniformity (minimal Draw Calls transition due to shared shaders).

## 5. Advanced Handling of Height Differences and Elevated Surfaces (Separate Geometric Fixes)

While all previously described systems (RVT, Decals, Material Instances) flawlessly handle the pixel level, color data, and lighting - none of them actually alter the polygon structure. When a model like a rock is placed on a mild landscape slope, the RVT will cause the color to blend beautifully, but the physical intersection line will remain perfectly sharp and straight, betraying it as an external object penetrating another surface. To completely erase this cut, spatial manipulation strategies or geometric deformation must be employed.

### 5.1 Photometric Concealment via Pixel Depth Offset Combined with DitherTemporalAA

An elegant approach that creates a soft organic transition without altering the polygons themselves is writing manipulative values into the depth buffer (Z-Buffer). This is done by connecting numerical values into the Pixel Depth Offset (PDO) input in the model's material.

The applied offset virtually pushes the static model's pixels "backward" into the screen, making them appear as though they are behind the landscape that is actually in front of them. To create a gradual transition rather than another sharp cut, the developer injects the value through the DitherTemporalAA material function. This function generates a randomized stipple noise pattern based on depth distance. As the engine's Temporal Anti-Aliasing (TAA or TSR) process processes frames over time in real-time, it blurs this noise, creating a continuous, semi-transparent transition that completely hides the rock's borders.

Architectural and Performance Implications: Despite the high realism this method provides, it carries a very heavy performance penalty. Modern graphics cards use Early-Z Culling technology, exempting the card from calculating lighting and shadows on occluded pixels. Once Pixel Depth Offset is enabled in a material, the engine is prevented from performing this early optimization since the depth information becomes dynamic and is determined only after the material is calculated. In forest environments dense with rocks and vegetation intersecting one another, the loss of Early-Z leads to extreme Overdraw and crashing frame rates. Therefore, this effect must be limited and combined with a Camera Depth calculation, so the effect is disabled at large distances where the geometric seam is unnoticeable anyway. Furthermore, different overlapping models might cancel out each other's dither pattern; a solution is adding random data based on Object Position to create a unique noise shift for each model.

### 5.2 Dynamic Blending Gradient Using Distance Fields (DistanceToNearestSurface)

A superior alternative in terms of performance, based on world calculations, is using Mesh Distance Fields (MDF) technology. The developer must first ensure the "Generate Mesh Distance Fields" option is active in the Project Settings.

Inside the model's material editor, using the DistanceToNearestSurface node returns the exact distance from every pixel on the model's surface to the nearest spatial geometry (in this case, the landscape). This distance data acts as a foundation for creating a gradual enveloping gradient that climbs from the meeting point with the ground upward along the rock's sides. Using this gradient as a continuous mask allows a gentle Lerp operation to blend moss, mud, or pure RVT layer textures, embedding the rock into its surroundings.

Systemic Challenge and Solution: A major logical limitation is that the distance node does not distinguish between objects. If the object samples the area, it will measure the distance to itself (always returning zero) or to concave parts of its own geometry. To bypass this, the developer must select the blending model in the game world and specifically disable the "Affect Distance Field Lighting" checkbox under its details. This prevents the object itself from being written into the global distance field. It is important to note that this reduction harms the model's ability to cast soft Distance Field Shadows, making this technique an artistic compromise between blending quality and shadow presence.

### 5.3 Real-Time Polygonal Conformity: World Position Offset (WPO)

For blending long meshes required to precisely adhere to the terrain contours (such as dirt paths, railway tracks, or roads via the Landscape Splines system), the definitive geometric solution is feeding vertex deformation commands into the World Position Offset (WPO) input of the model's material.

The mathematical logic for this connection is simple and elegant: The system uses the RVT to get the absolute World Position of the existing landscape surface. Inside the model's material (the road or path), the spatial absolute position of the current rendering point (Absolute World Position) is subtracted from this landscape position. The result is an exact directional vector. This vector is injected into the WPO input, forcing the GPU to physically "pull" the road's vertices up or down until they perfectly overlap the virtual geometry of the ground beneath them.

While earlier versions of Unreal Engine 5 had incompatibilities between Nanite and WPO, engine updates now allow full support. However, a sufficiently dense polygon mesh is required in the original object for the deformation to look natural and continuous. Furthermore, evaluating shadows and animating dynamic WPO-driven foliage leaves require optimization via WPO Disable Distance to prevent processing overload on Lumen global illumination calculations.

### 5.4 Virtual Heightfield Mesh (VHFM) as a Response to Micro-Geometry

Unreal's traditional Landscape system is based on a rigid-resolution 2D Heightmap that does not allow real-time dynamic shape changes. Since Tessellation technology was removed from the engine starting with version 5, creating depth changes like footprints in snow or tire ruts in mud required an architectural workaround. The solution comes in the form of an experimental plugin that integrates with the RVT system: Virtual Heightfield Mesh (VHFM).

When the landscape surface writes data to the RVT, it can also store height information (World Height) within the virtual tiles. The VHFM is a type of Actor deployed across space that generates an invisible mesh of triangles. This mesh adaptively subdivides based on camera distance (to save performance), reads the height and offset data from the RVT in real time, and pushes the polygons up or down accordingly to produce rich 3D geometric displacements.

Deep Operational Limitation: It is important to understand VHFM's limitations regarding the physics engine: The generated displacement occurs solely during the rendering stage (GPU Side) and does not affect the Collision Mesh located on the main processor (CPU Side) at all. This means this operation is excellent for minor, cosmetic depressions with minimal depth, but using it to create deep trenches or massive height differences will result in characters sinking into the visual ground or floating above it, as their collision is calculated against the original flat landscape surface from before the deformation.

## 6. Action Plan for Holistic Integration

A developer looking to coherently integrate all the above tools in a standard workflow ("Best Practices") in UE5 will need to implement the technology layers in the following order:

1. Base Ground Material Infrastructure: Create a full master material that manages logic, blends color and roughness layers via Layer Blend, incorporates spatial transformations from world vertex angle to tangent (Transform Vector), and transmits the processed output into the Runtime Virtual Texture Output node with a fallback Feature Switch.
2. Virtualization Deployment (RVT Setup): Place the RVT Volume object in the space, accurately fit it to the Landscape environment dimensions using Set Bounds, and allocate the virtual databases for saving photometric data.
3. Color and Texture Blending for Intersecting Geometry: Use Material Instances for objects like rocks or road axes. Sample the data from the RVT and apply Lerp operations using height masks to soften the visual integration (matching lighting and reflections by converting normals from RVT back to Tangent Space).
4. Deforming and Blurring the Geometric Seam: Implement Pixel Depth Offset code combined with DitherTemporalAA for heavy vertical models while disabling marginal Culling, or activate World Position Offset manipulation for continuous Spline objects required to stick like skin to the ground beneath them.
5. Diversifying and Breaking Spatial Patterns (Decals): Add local details at rock-dirt intersections using DBuffer Decals containing dirt, roots, and weathering effects, to break the patterned repetition of the virtual texture and grant the scene authenticity based on organic chaos.

This architecture severs the previously tight link between geometry and materials, creating a unified, dynamic workspace with the potential for immediate real-time changes, while maintaining tight control over the rendering loads of end systems.
