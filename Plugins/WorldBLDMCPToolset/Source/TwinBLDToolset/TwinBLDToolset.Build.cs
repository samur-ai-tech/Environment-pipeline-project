using UnrealBuildTool;

public class TwinBLDToolset : ModuleRules
{
	public TwinBLDToolset(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"BLDToolsetCommon",
			"CityBLDRuntime",
			"CoreUObject",
			"EditorSubsystem",
			"Engine",
			"HTTP",
			"Json",
			"JsonUtilities",
			"Kismet",
			"Landscape",
			"Projects",
			"RoadBLDRuntime",
			"ToolsetRegistry",
			"TwinBLDEditor",
			"UnrealEd"
		});
	}
}
