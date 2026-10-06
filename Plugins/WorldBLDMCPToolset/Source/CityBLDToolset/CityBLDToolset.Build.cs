using UnrealBuildTool;

public class CityBLDToolset : ModuleRules
{
	public CityBLDToolset(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"AssetRegistry",
			"BLDToolsetCommon",
			"CityBLDEditor",
			"CityBLDRuntime",
			"CoreUObject",
			"EditorSubsystem",
			"Engine",
			"Kismet",
			"Projects",
			"ToolsetRegistry",
			"UnrealEd",
			"WorldBLDRuntime"
		});
	}
}
