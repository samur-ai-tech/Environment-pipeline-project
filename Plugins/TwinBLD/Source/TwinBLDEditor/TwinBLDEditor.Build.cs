using System.IO;

namespace UnrealBuildTool.Rules
{
    public class TwinBLDEditor : ModuleRules
    {
        public TwinBLDEditor(ReadOnlyTargetRules Target)
			: base(Target)
        {
            PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
            bUsePrecompiled = true;
            PrecompileForTargets = PrecompileTargetsType.Any;
            bUseUnity = false;
            bEnableExceptions = true;
            OptimizeCode = CodeOptimization.InShippingBuildsOnly;
            
            PublicDefinitions.Add("OSMIUM_WITH_XML=1");
            PublicDefinitions.Add("XML_STATIC");
            PublicDefinitions.Add("PROJ_DLL=");

            AddEngineThirdPartyPrivateStaticDependencies(Target, new string[]
            {
                "nghttp2",
                "OpenSSL",
                "zlib",
                "libcurl",
                "LibJpegTurbo",
            });

            // Third-party libraries
            string ThirdPartyPath = Path.Combine(ModuleDirectory, "ThirdParty");
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "tiff", "include"));
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "sqlite", "include"));
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "proj", "include"));
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "expat", "include"));
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "gdal", "include"));
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "protozero", "include"));
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "libosmium", "include"));
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "lz4"));
            PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "gdal", "include"));

            string LibtiffLibPath = Path.Combine(ThirdPartyPath, "tiff", "lib", "tiff.lib");
            string Sqlite3LibPath = Path.Combine(ThirdPartyPath, "sqlite", "lib", "sqlite3.lib");
            string ProjLibPath = Path.Combine(ThirdPartyPath, "proj", "lib", "proj.lib");
            string ExpatLibPath = Path.Combine(ThirdPartyPath, "expat", "lib", "libexpatMD.lib");
            string GdalLibPath = Path.Combine(ThirdPartyPath, "gdal", "lib", "gdal.lib");
            
            if (File.Exists(ProjLibPath)) PublicAdditionalLibraries.Add(ProjLibPath);
            if (File.Exists(LibtiffLibPath)) PublicAdditionalLibraries.Add(LibtiffLibPath);
            if (File.Exists(Sqlite3LibPath)) PublicAdditionalLibraries.Add(Sqlite3LibPath);
            if (File.Exists(ExpatLibPath)) PublicAdditionalLibraries.Add(ExpatLibPath);
            if (File.Exists(GdalLibPath)) PublicAdditionalLibraries.Add(GdalLibPath);

            PublicDependencyModuleNames.AddRange(
                new string[]
                {
					// NOTE: This module exposes UCLASS types and the public Slate importer header that reference these modules.
					// They must be Public deps so UHT/UBT and dependent editor plugins can resolve types when packaging via BuildPlugin.
					"CityBLDRuntime",
                    "Core",
                    "CoreUObject",
                    "DeveloperSettings",
                    "Engine",
                    "InputCore",
                    "RoadBLDRuntime",
                    "Slate",
                    "SlateCore",
					"WorldBLDEditor",
                }
            );
            PrivateDependencyModuleNames.AddRange(
                new string[] {
                    "AssetTools",
                    "AssetRegistry",
                    "Blutility",
                    "DesktopPlatform",
                    "DynamicMesh",
                    "EditorStyle",
                    "EditorSubsystem",
                    "Foliage",
                    "GeometryAlgorithms",
                    "GeometryCore",
                    "GeometryFramework",
                    "GeometryScriptingCore",
                    "HTTP",
                    "ImageWrapper",
                    "Json",
                    "JsonUtilities",
                    "LevelEditor",
                    "Landscape",
                    "LandscapeEditor",
                    // Used by TwinBLD's auth/trial subsystems for AES-GCM encrypted local trial activation records.
                    "OpenSSL",
                    "PCG",
                    "PlatformCryptoContext",
                    "ProceduralMeshComponent",
                    "Projects",
                    "PropertyEditor",
                    "RenderCore",
                    "RHI",
                    "RawMesh",
                    "Settings",
                    "ToolMenus",
                    "UMG",
                    "UMGEditor",
                    "UnrealEd",
                    "WorldBLDRuntime",
                    "XmlParser"
                }
            );

            AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL");
        }
    }
}