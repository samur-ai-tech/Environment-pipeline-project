// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDToolset.h"

#include "BLDToolsetUtils.h"
#include "Editor.h"
#include "EditorModeManager.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Interfaces/IProjectManager.h"
#include "Kismet/KismetSystemLibrary.h"
#include "LandscapeProxy.h"
#include "Misc/App.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "ModuleDescriptor.h"
#include "PCGVolume.h"
#include "PluginDescriptor.h"
#include "PluginReferenceDescriptor.h"
#include "ProjectDescriptor.h"
#include "Settings/ProjectPackagingSettings.h"
#include "WorldBLDEditorToolkit.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(WorldBLDToolset)

namespace WorldBLDToolsetPrivate
{
	constexpr int32 MaxListedActors = 100;

	void RaiseError(const FString& Message)
	{
		UKismetSystemLibrary::RaiseScriptError(FString::Printf(TEXT("WorldBLDToolset: %s"), *Message));
	}

	UWorld* GetEditorWorld()
	{
		BLDToolset::MarkCurrentCallUnattended();
		if (!GEditor)
		{
			RaiseError(TEXT("Editor is not available."));
			return nullptr;
		}

		UWorld* World = GEditor->GetEditorWorldContext().World();
		if (!IsValid(World))
		{
			RaiseError(TEXT("No editor world is loaded."));
			return nullptr;
		}

		return World;
	}

	FWorldBLDActorRef MakeActorRef(const AActor* Actor)
	{
		FWorldBLDActorRef Ref;
		if (!IsValid(Actor))
		{
			return Ref;
		}

		Ref.Name = Actor->GetName();
		Ref.Label = Actor->GetActorLabel();
		Ref.RefPath = Actor->GetPathName();
		Ref.Class = Actor->GetClass()->GetName();
		return Ref;
	}

	FWorldBLDPluginCapability DescribePlugin(const TCHAR* PluginName)
	{
		FWorldBLDPluginCapability Info;
		Info.Name = PluginName;

		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(PluginName);
		if (!Plugin.IsValid())
		{
			return Info;
		}

		Info.bAvailable = true;
		Info.bEnabled = Plugin->IsEnabled();
		Info.VersionName = Plugin->GetDescriptor().VersionName;
		return Info;
	}

	FWorldBLDPluginPackagingInfo DescribePluginPackaging(const TCHAR* PluginName)
	{
		FWorldBLDPluginPackagingInfo Info;
		Info.Name = PluginName;

		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(PluginName);
		if (!Plugin.IsValid())
		{
			return Info;
		}

		Info.bAvailable = true;
		Info.bEnabled = Plugin->IsEnabled();
		Info.VersionName = Plugin->GetDescriptor().VersionName;
		Info.BaseDir = FPaths::ConvertRelativePathToFull(Plugin->GetBaseDir());
		Info.LoadedFrom = (Plugin->GetLoadedFrom() == EPluginLoadedFrom::Engine) ? TEXT("Engine") : TEXT("Project");
		Info.bHasSource = IFileManager::Get().DirectoryExists(*FPaths::Combine(Info.BaseDir, TEXT("Source")));

		for (const FPluginReferenceDescriptor& Ref : Plugin->GetDescriptor().Plugins)
		{
			if (!Ref.bEnabled)
			{
				continue;
			}

			const TSharedPtr<IPlugin> Dependency = IPluginManager::Get().FindPlugin(Ref.Name);
			if (!Dependency.IsValid() || !Dependency->IsEnabled())
			{
				Info.MissingDependencies.Add(Ref.Name);
			}
		}

		return Info;
	}

	FWorldBLDPackagingCheck MakeCheck(
		const TCHAR* Id,
		const TCHAR* Title,
		const FString& Status,
		const bool bLooksOk,
		const FString& Recommendation)
	{
		FWorldBLDPackagingCheck Check;
		Check.Id = Id;
		Check.Title = Title;
		Check.Status = Status;
		Check.bLooksOk = bLooksOk;
		Check.Recommendation = Recommendation;
		return Check;
	}

	void AddCommonSolutions(TArray<FString>& OutSolutions, const FString& GameModuleName)
	{
		const FString ModuleName = GameModuleName.IsEmpty() ? TEXT("YourGameModule") : GameModuleName;

		OutSolutions.Add(TEXT(
			"1. Custom source engine vs Epic launcher: Are you running a custom source build of Unreal, or a standard build from the Epic Games Launcher? You need the source version (not the binary/Fab version) of every installed WorldBLD tool to compile against a custom engine build."));
		OutSolutions.Add(TEXT(
			"2. Engine vs project install: Is WorldBLD (and CityBLD / RoadBLD / TwinBLD) installed to your project or your engine? You can only build when the plugins are in your project's Plugins folder. Fab/Marketplace installs them to the engine by default — copy or reinstall the source plugins into <Project>/Plugins."));
		OutSolutions.Add(TEXT(
			"3. Blueprint-only project: Are you in a Blueprint project? Convert it to a C++ project (File > New C++ Class — adding a single C++ class is enough; Unreal converts the project automatically), then compile before packaging."));
		OutSolutions.Add(TEXT(
			"4. Locked files: Restart the PC. This can resolve file-lock / sharing-violation errors left behind by a previous editor, build, or antivirus scan."));
		OutSolutions.Add(TEXT(
			"5. Full Rebuild: Ensure Full Rebuild is DISABLED in Project Settings > Packaging. A full rebuild often fails or loops with these plugins."));
		OutSolutions.Add(TEXT(
			"6. Build settings (source-engine users): In the *.Build.cs of every WorldBLD product plugin, try setting DefaultBuildSettings = BuildSettingsVersion.V4; or BuildSettingsVersion.V5; then regenerate project files and rebuild."));
		OutSolutions.Add(TEXT(
			"7. Cook path too long: If you see a content-missing cook error such as \"Build Failed: LogCook: Error: Content is missing from cook... /ModernEssentials/WorldBLD_Content\", the output path is likely too long. Move the packaged-game folder up to a shorter path, for example H:/Pack."));
		OutSolutions.Add(FString::Printf(
			TEXT("8. Packaged executable will not launch / plugin failed to load: Check the logs. You may see:\n")
			TEXT("LogPluginManager: Error: Unable to load plugin 'CityBLD'. It was requested by .uplugin files that are enabled by default, but it has a dependency that is missing on disk.\n")
			TEXT("The missing dependency is GeometryScripting (ReferenceChain: CityBLD -> GeometryScripting).\n")
			TEXT("Aborting.\n")
			TEXT("Enable GeometryScripting in Edit > Plugins, and add the missing module to your game's Build.cs under PublicDependencyModuleNames (GeometryScriptingCore is the usual missing module). Example for module %s:\n\n")
			TEXT("// Copyright Epic Games, Inc. All Rights Reserved.\n\n")
			TEXT("using UnrealBuildTool;\n\n")
			TEXT("public class %s : ModuleRules\n")
			TEXT("{\n")
			TEXT("\tpublic %s(ReadOnlyTargetRules Target) : base(Target)\n")
			TEXT("\t{\n")
			TEXT("\t\tPCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;\n\n")
			TEXT("\t\tPublicDependencyModuleNames.AddRange(new string[] { \"Core\", \"CoreUObject\", \"Engine\", \"InputCore\", \"EnhancedInput\", \"GeometryScriptingCore\" });\n")
			TEXT("\t}\n")
			TEXT("}"),
			*ModuleName, *ModuleName, *ModuleName));
	}

	bool ErrorMentionsAny(const FString& ErrorText, const TCHAR* const* Keywords, const int32 Count)
	{
		for (int32 Index = 0; Index < Count; ++Index)
		{
			if (ErrorText.Contains(Keywords[Index], ESearchCase::IgnoreCase))
			{
				return true;
			}
		}
		return false;
	}

	void AddSuggestedFromError(TArray<FString>& OutSuggested, const TArray<FString>& CommonSolutions, const FString& ErrorText)
	{
		if (ErrorText.IsEmpty() || CommonSolutions.Num() < 8)
		{
			return;
		}

		auto Add = [&OutSuggested, &CommonSolutions](const int32 Index)
		{
			if (CommonSolutions.IsValidIndex(Index))
			{
				OutSuggested.AddUnique(CommonSolutions[Index]);
			}
		};

		const TCHAR* SourceKeywords[] = {TEXT("source build"), TEXT("custom engine"), TEXT("binary"), TEXT("cannot compile"), TEXT("does not compile")};
		const TCHAR* InstallKeywords[] = {TEXT("engine plugin"), TEXT("installed to the engine"), TEXT("Plugins folder")};
		const TCHAR* BlueprintKeywords[] = {TEXT("blueprint"), TEXT("bp project"), TEXT("pure blueprint")};
		const TCHAR* LockKeywords[] = {TEXT("locked"), TEXT("sharing violation"), TEXT("being used by another"), TEXT("cannot open")};
		const TCHAR* RebuildKeywords[] = {TEXT("full rebuild")};
		const TCHAR* BuildCsKeywords[] = {TEXT("build.cs"), TEXT("buildsettings"), TEXT("include order")};
		const TCHAR* CookKeywords[] = {TEXT("content is missing from cook"), TEXT("worldbld_content"), TEXT("modernessentials"), TEXT("filename or extension is too long"), TEXT("path too long")};
		const TCHAR* LoadKeywords[] = {TEXT("unable to load plugin"), TEXT("geometryscripting"), TEXT("missing on disk"), TEXT("referencechain"), TEXT("aborting"), TEXT("executable")};

		if (ErrorMentionsAny(ErrorText, SourceKeywords, UE_ARRAY_COUNT(SourceKeywords))) { Add(0); }
		if (ErrorMentionsAny(ErrorText, InstallKeywords, UE_ARRAY_COUNT(InstallKeywords))) { Add(1); }
		if (ErrorMentionsAny(ErrorText, BlueprintKeywords, UE_ARRAY_COUNT(BlueprintKeywords))) { Add(2); }
		if (ErrorMentionsAny(ErrorText, LockKeywords, UE_ARRAY_COUNT(LockKeywords))) { Add(3); }
		if (ErrorMentionsAny(ErrorText, RebuildKeywords, UE_ARRAY_COUNT(RebuildKeywords))) { Add(4); }
		if (ErrorMentionsAny(ErrorText, BuildCsKeywords, UE_ARRAY_COUNT(BuildCsKeywords))) { Add(5); }
		if (ErrorMentionsAny(ErrorText, CookKeywords, UE_ARRAY_COUNT(CookKeywords))) { Add(6); }
		if (ErrorMentionsAny(ErrorText, LoadKeywords, UE_ARRAY_COUNT(LoadKeywords))) { Add(7); }
	}
}

TArray<FWorldBLDPluginCapability> UWorldBLDToolset::GetCapabilities()
{
	TArray<FWorldBLDPluginCapability> Capabilities;
	Capabilities.Add(WorldBLDToolsetPrivate::DescribePlugin(TEXT("WorldBLD")));
	Capabilities.Add(WorldBLDToolsetPrivate::DescribePlugin(TEXT("CityBLD")));
	Capabilities.Add(WorldBLDToolsetPrivate::DescribePlugin(TEXT("RoadBLD")));
	Capabilities.Add(WorldBLDToolsetPrivate::DescribePlugin(TEXT("TwinBLD")));
	return Capabilities;
}

FWorldBLDEditorContext UWorldBLDToolset::GetEditorContext()
{
	FWorldBLDEditorContext Context;

	if (GEditor)
	{
		if (UWorld* World = GEditor->GetEditorWorldContext().World())
		{
			Context.MapName = World->GetMapName();
			Context.WorldPath = World->GetPathName();
		}
	}

	if (const UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
	{
		Context.bWorldBLDEditorModeActive = EdMode->IsThisEdModeActive();
	}

	return Context;
}

FWorldBLDLevelActorList UWorldBLDToolset::ListLevelActors()
{
	FWorldBLDLevelActorList List;
	UWorld* World = WorldBLDToolsetPrivate::GetEditorWorld();
	if (!World)
	{
		return List;
	}

	auto AppendActors = [&List](AActor* Actor)
	{
		if (!IsValid(Actor))
		{
			return;
		}

		++List.TotalCount;
		if (List.Actors.Num() < WorldBLDToolsetPrivate::MaxListedActors)
		{
			List.Actors.Add(WorldBLDToolsetPrivate::MakeActorRef(Actor));
		}
	};

	for (TActorIterator<ALandscapeProxy> It(World); It; ++It)
	{
		AppendActors(*It);
	}

	for (TActorIterator<APCGVolume> It(World); It; ++It)
	{
		AppendActors(*It);
	}

	List.ReturnedCount = List.Actors.Num();
	return List;
}

bool UWorldBLDToolset::SetWorldBLDEditorModeActive(const bool bActive)
{
	if (!GEditor)
	{
		WorldBLDToolsetPrivate::RaiseError(TEXT("Editor is not available."));
		return false;
	}

	if (bActive)
	{
		GLevelEditorModeTools().ActivateMode(UWorldBLDEdMode::EditorModeID);
	}
	else
	{
		GLevelEditorModeTools().DeactivateMode(UWorldBLDEdMode::EditorModeID);
	}

	if (const UWorldBLDEdMode* EdMode = UWorldBLDEdMode::GetWorldBLDEdMode())
	{
		return EdMode->IsThisEdModeActive();
	}

	return false;
}

FWorldBLDPackagingGuide UWorldBLDToolset::GetPackagingGuide(FString ErrorText)
{
	using namespace WorldBLDToolsetPrivate;

	FWorldBLDPackagingGuide Guide;
	Guide.IntegrationOverview = TEXT(
		"WorldBLD is the hub plugin (Runtime + Editor). CityBLD and RoadBLD are Runtime+Editor product plugins that "
		"depend on WorldBLD and on engine plugins such as GeometryScripting and PCG. TwinBLD is Editor-only and depends "
		"on WorldBLD, CityBLD, and RoadBLD. Fab/Marketplace installs these into the Engine/Plugins folder by default; "
		"packaging and compiling require the product plugins in the project's Plugins folder. On a custom source engine "
		"you also need the source (not binary) plugin drop. The WorldBLDMCPToolset plugin (WorldBLDToolset, CityBLDToolset, "
		"RoadBLDToolset and TwinBLDToolset modules) is an Editor-only MCP wrapper and is not required in a packaged game.\n\n"
		"Tell the user the live Checks first, then the matching CommonSolutions. Do not skip GetPackagingGuide when the "
		"question is a WorldBLD / CityBLD / TwinBLD / RoadBLD packaging, cook, compile, or plugin-load error.");

	Guide.bIsInstalledEngine = FApp::IsEngineInstalled();
	Guide.EngineKind = Guide.bIsInstalledEngine
		? TEXT("Installed (Epic Games Launcher)")
		: TEXT("Source / custom engine build");
	Guide.EngineVersion = FEngineVersion::Current().ToString();
	Guide.EngineDir = FPaths::ConvertRelativePathToFull(FPaths::EngineDir());
	Guide.ProjectDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());

	if (const FProjectDescriptor* Project = IProjectManager::Get().GetCurrentProject())
	{
		Guide.bIsCppProject = Project->Modules.Num() > 0;
		for (const FModuleDescriptor& Module : Project->Modules)
		{
			if (Module.Type == EHostType::Runtime)
			{
				Guide.GameModuleName = Module.Name.ToString();
				break;
			}
		}
		if (Guide.GameModuleName.IsEmpty() && Project->Modules.Num() > 0)
		{
			Guide.GameModuleName = Project->Modules[0].Name.ToString();
		}
	}

	if (!Guide.GameModuleName.IsEmpty())
	{
		Guide.GameModuleBuildCsPath = FPaths::ConvertRelativePathToFull(
			FPaths::Combine(FPaths::GameSourceDir(), Guide.GameModuleName, Guide.GameModuleName + TEXT(".Build.cs")));
		FString BuildCs;
		if (FPaths::FileExists(Guide.GameModuleBuildCsPath) && FFileHelper::LoadFileToString(BuildCs, *Guide.GameModuleBuildCsPath))
		{
			Guide.bGameModuleListsGeometryScriptingCore = BuildCs.Contains(TEXT("GeometryScriptingCore"));
		}
	}

	if (const UProjectPackagingSettings* PackagingSettings = GetDefault<UProjectPackagingSettings>())
	{
		Guide.bFullRebuildEnabled = PackagingSettings->FullRebuild;
	}

	if (const TSharedPtr<IPlugin> GeometryScripting = IPluginManager::Get().FindPlugin(TEXT("GeometryScripting")))
	{
		Guide.bGeometryScriptingEnabled = GeometryScripting->IsEnabled();
	}

	const TCHAR* ProductPlugins[] = {TEXT("WorldBLD"), TEXT("CityBLD"), TEXT("RoadBLD"), TEXT("TwinBLD")};
	TArray<FString> EngineInstalled;
	TArray<FString> MissingSourceOnCustomEngine;
	TArray<FString> MissingPlugins;
	TArray<FString> MissingDeps;
	for (const TCHAR* PluginName : ProductPlugins)
	{
		const FWorldBLDPluginPackagingInfo Info = DescribePluginPackaging(PluginName);
		if (!Info.bAvailable)
		{
			MissingPlugins.Add(PluginName);
		}
		else if (Info.LoadedFrom == TEXT("Engine"))
		{
			EngineInstalled.Add(PluginName);
		}
		if (Info.bAvailable && !Guide.bIsInstalledEngine && !Info.bHasSource)
		{
			MissingSourceOnCustomEngine.Add(PluginName);
		}
		for (const FString& Dep : Info.MissingDependencies)
		{
			MissingDeps.AddUnique(FString::Printf(TEXT("%s -> %s"), *Info.Name, *Dep));
		}
		Guide.Plugins.Add(Info);
	}

	AddCommonSolutions(Guide.CommonSolutions, Guide.GameModuleName);

	const bool bEngineInstallOk = EngineInstalled.Num() == 0;
	Guide.Checks.Add(MakeCheck(
		TEXT("InstallLocation"),
		TEXT("Plugin install location"),
		bEngineInstallOk
			? TEXT("WorldBLD product plugins that are present are loaded from the project.")
			: FString::Printf(TEXT("Loaded from Engine (not the project): %s"), *FString::Join(EngineInstalled, TEXT(", "))),
		bEngineInstallOk,
		TEXT("Copy or reinstall the source versions of WorldBLD, CityBLD, RoadBLD and TwinBLD into this project's Plugins folder. Engine/Fab installs cannot be used to package or to compile against a custom engine.")));

	const bool bSourceOk = MissingSourceOnCustomEngine.Num() == 0;
	Guide.Checks.Add(MakeCheck(
		TEXT("SourcePlugins"),
		TEXT("Source vs binary plugins"),
		Guide.bIsInstalledEngine
			? TEXT("Using an installed Epic launcher engine. Binary plugins can run in the editor; packaging still needs a project install.")
			: (bSourceOk
				? TEXT("Custom source engine, and installed WorldBLD plugins include Source.")
				: FString::Printf(TEXT("Custom source engine, but these plugins have no Source folder: %s"), *FString::Join(MissingSourceOnCustomEngine, TEXT(", ")))),
		Guide.bIsInstalledEngine || bSourceOk,
		TEXT("On a custom source engine you must use the source version of every WorldBLD product plugin, not the binary/Fab build, and they must live in the project's Plugins folder.")));

	Guide.Checks.Add(MakeCheck(
		TEXT("CppProject"),
		TEXT("Blueprint vs C++ project"),
		Guide.bIsCppProject
			? FString::Printf(TEXT("C++ project (game module %s)."), *Guide.GameModuleName)
			: TEXT("Blueprint-only project (no runtime modules in the .uproject)."),
		Guide.bIsCppProject,
		TEXT("Add a single C++ class (File > New C++ Class). Unreal converts the Blueprint project to C++, then compile before packaging.")));

	Guide.Checks.Add(MakeCheck(
		TEXT("FullRebuild"),
		TEXT("Full Rebuild"),
		Guide.bFullRebuildEnabled ? TEXT("Full Rebuild is ENABLED.") : TEXT("Full Rebuild is disabled."),
		!Guide.bFullRebuildEnabled,
		TEXT("Open Project Settings > Packaging and disable Full Rebuild.")));

	Guide.Checks.Add(MakeCheck(
		TEXT("GeometryScriptingPlugin"),
		TEXT("GeometryScripting plugin"),
		Guide.bGeometryScriptingEnabled ? TEXT("GeometryScripting is enabled.") : TEXT("GeometryScripting is missing or disabled."),
		Guide.bGeometryScriptingEnabled,
		TEXT("Enable GeometryScripting under Edit > Plugins, then restart the editor. CityBLD, RoadBLD, TwinBLD and WorldBLD all depend on it.")));

	const bool bModuleDepOk = !Guide.bIsCppProject || Guide.bGameModuleListsGeometryScriptingCore;
	Guide.Checks.Add(MakeCheck(
		TEXT("GeometryScriptingModule"),
		TEXT("Game module GeometryScriptingCore"),
		!Guide.bIsCppProject
			? TEXT("No game Build.cs yet (Blueprint project).")
			: (Guide.bGameModuleListsGeometryScriptingCore
				? FString::Printf(TEXT("%s.Build.cs lists GeometryScriptingCore."), *Guide.GameModuleName)
				: FString::Printf(TEXT("%s.Build.cs does not list GeometryScriptingCore."), *Guide.GameModuleName)),
		bModuleDepOk,
		FString::Printf(
			TEXT("Add \"GeometryScriptingCore\" to PublicDependencyModuleNames in %s so the packaged game can load CityBLD / RoadBLD / WorldBLD."),
			Guide.GameModuleBuildCsPath.IsEmpty() ? TEXT("your game module Build.cs") : *Guide.GameModuleBuildCsPath)));

	Guide.Checks.Add(MakeCheck(
		TEXT("LockedFiles"),
		TEXT("Locked files"),
		TEXT("Cannot detect from the editor. If the log shows sharing violation / file in use, restart the PC."),
		true,
		TEXT("Close Unreal, Visual Studio and any packaged-game process, then restart the PC and retry the package.")));

	Guide.Checks.Add(MakeCheck(
		TEXT("CookPathLength"),
		TEXT("Cook output path length"),
		FString::Printf(TEXT("Project path is %d characters (%s). Long package-output paths often fail cook with missing /ModernEssentials/WorldBLD_Content."), Guide.ProjectDir.Len(), *Guide.ProjectDir),
		Guide.ProjectDir.Len() < 80,
		TEXT("Package to a short path such as H:/Pack instead of a nested folder under the project.")));

	if (MissingPlugins.Num() > 0)
	{
		Guide.Checks.Add(MakeCheck(
			TEXT("MissingProducts"),
			TEXT("Missing product plugins"),
			FString::Printf(TEXT("Not discovered: %s"), *FString::Join(MissingPlugins, TEXT(", "))),
			false,
			TEXT("Install the missing product through WorldBLD's plugin manager (WorldBLD editor mode) or your WorldBLD account download, into this project's Plugins folder.")));
	}

	if (MissingDeps.Num() > 0)
	{
		Guide.Checks.Add(MakeCheck(
			TEXT("MissingDependencies"),
			TEXT("Missing plugin dependencies"),
			FString::Join(MissingDeps, TEXT("; ")),
			false,
			TEXT("Enable the missing plugins under Edit > Plugins. GeometryScripting is the usual gap; after enabling, add GeometryScriptingCore to the game module Build.cs.")));
	}

	for (const FWorldBLDPackagingCheck& Check : Guide.Checks)
	{
		if (!Check.bLooksOk)
		{
			Guide.SuggestedFirst.Add(FString::Printf(TEXT("%s: %s — %s"), *Check.Title, *Check.Status, *Check.Recommendation));
		}
	}
	AddSuggestedFromError(Guide.SuggestedFirst, Guide.CommonSolutions, ErrorText);

	return Guide;
}
