using UnrealBuildTool;

public class BLDToolsetCommon : ModuleRules
{
	public BLDToolsetCommon(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"ToolsetRegistry"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"AssetRegistry",
			"HTTP",
			"ImageCore",
			"Kismet",
			"LevelEditor",
			"Projects",
			"RenderCore",
			"Slate",
			"SlateCore",
			"UnrealEd"
		});
	}
}
