using UnrealBuildTool;

public class WorldBLDToolset : ModuleRules
{
	public WorldBLDToolset(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"CoreUObject",
			"Engine",
			"Json",
			"JsonUtilities",
			"Kismet",
			"Landscape",
			"PCG",
			"Projects",
			"DeveloperToolSettings",
			"ToolsetRegistry",
			"UnrealEd",
			"BLDToolsetCommon",
			"WorldBLDEditor",
			"WorldBLDRuntime"
		});
	}
}
