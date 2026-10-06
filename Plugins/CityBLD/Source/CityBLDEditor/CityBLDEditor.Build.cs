// Copyright WorldBLD LLC. All rights reserved.

using UnrealBuildTool;

public class CityBLDEditor : ModuleRules
{
	public CityBLDEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		bUsePrecompiled = true;

		// We intentionally consume the WorldBLD context menu widget framework from WorldBLDEditor's ContextMenu private headers.
		// This keeps CityBLD context menus lightweight and consistent with the WorldBLD editor UI.
		PrivateIncludePaths.AddRange(new string[]
		{
			System.IO.Path.Combine(GetModuleDirectory("WorldBLDEditor"), "Private"),
			System.IO.Path.Combine(GetModuleDirectory("WorldBLDEditor"), "Private", "ContextMenu"),
			System.IO.Path.Combine(GetModuleDirectory("WorldBLDEditor"), "Private", "ContextMenu", "Widgets"),
		});

		PublicDependencyModuleNames.AddRange(new string[]
		{
			// Core Engine Dependencies (keep Alphabetical please)
			"Core",
			"CoreUObject",
			"DynamicMesh",
			"Engine",			
			"GameplayTags",
			"GeometryCore",
			"GeometryFramework",
			"InputCore",
			"Slate",
			"SlateCore",
			"ToolMenus",
			"UnrealEd",
			
			// Internal Module Dependencies
			"CityBLDRuntime",
			"WorldBLDRuntime",
			"WorldBLDEditor",
            "HTTP",
            "Json",
            "JsonUtilities"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"AppFramework",
			"AssetRegistry",
			"AssetTools",
			"BlueprintGraph",
			"ComponentVisualizers",
			"ContentBrowser",
			"PropertyEditor",
			"Blutility",
			"EditorScriptingUtilities",
			"EditorSubsystem",
			"GeometryScriptingCore",
			"GeometryScriptingEditor",
			"MaterialBaking",
			"MaterialEditor",
			"MeshConversion",
			"MeshDescription",
			"MeshMergeUtilities",
			"ModelingComponents",
			"ModelingComponentsEditorOnly",
			"StaticMeshDescription",
			// Used by CityBLDTrialSubsystem for AES-GCM encrypted local trial activation record
			"OpenSSL",
			"PlatformCryptoContext",
			"Projects",
			"RenderCore",
			"Settings",
			"UMG",
			"UMGEditor"
		});

		AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL");
	}
}
