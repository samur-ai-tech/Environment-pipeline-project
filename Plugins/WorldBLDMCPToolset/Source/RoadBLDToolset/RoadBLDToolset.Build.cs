using UnrealBuildTool;

public class RoadBLDToolset : ModuleRules
{
	public RoadBLDToolset(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"AssetRegistry",
			"AssetTools",
			"ClothoidsModule",
			"CoreUObject",
			"Engine",
			"GeometryCore",
			"ImageCore",
			"ImageWrapper",
			"Json",
			"JsonUtilities",
			"Kismet",
			"LevelEditor",
			"MaterialEditor",
			"Projects",
			"RenderCore",
			"RoadBLDEditorToolkit",
			"RoadBLDRuntime",
			"Slate",
			"SlateCore",
			"ToolsetRegistry",
			"UnrealEd"
		});
	}
}
