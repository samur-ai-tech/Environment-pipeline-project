// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "WorldBLDToolset.generated.h"

USTRUCT(BlueprintType)
struct FWorldBLDActorRef
{
	GENERATED_BODY()

	/** Canonical actor name. Use this when referring back to the actor. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Name;

	/** Human-readable actor label shown in the World Outliner. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Label;

	/** Soft object path / refPath for later tool calls. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString RefPath;

	/** Short class name. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Class;
};

USTRUCT(BlueprintType)
struct FWorldBLDPluginCapability
{
	GENERATED_BODY()

	/** Plugin descriptor name (WorldBLD, CityBLD, RoadBLD, TwinBLD). */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Name;

	/** VersionName from the plugin descriptor. Empty if the plugin is not discovered. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString VersionName;

	/** True when the plugin is discovered in this project. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bAvailable = false;

	/** True when the plugin is currently enabled. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bEnabled = false;
};

USTRUCT(BlueprintType)
struct FWorldBLDEditorContext
{
	GENERATED_BODY()

	/** Current editor map package name, or empty if no world is loaded. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString MapName;

	/** Full path of the current editor world. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString WorldPath;

	/** True when the WorldBLD editor mode is the active mode. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bWorldBLDEditorModeActive = false;
};

USTRUCT(BlueprintType)
struct FWorldBLDLevelActorList
{
	GENERATED_BODY()

	/** Landscapes and PCG volumes in the current editor world, capped at ReturnedCount. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	TArray<FWorldBLDActorRef> Actors;

	/** Total matching actors in the level. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	int32 TotalCount = 0;

	/** Number of actors included in Actors. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	int32 ReturnedCount = 0;
};

USTRUCT(BlueprintType)
struct FWorldBLDPluginPackagingInfo
{
	GENERATED_BODY()

	/** Plugin descriptor name (WorldBLD, CityBLD, RoadBLD, TwinBLD). */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Name;

	/** VersionName from the plugin descriptor. Empty if the plugin is not discovered. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString VersionName;

	/** True when the plugin is discovered in this project. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bAvailable = false;

	/** True when the plugin is currently enabled. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bEnabled = false;

	/** "Engine" or "Project". Packaging and compiling require a Project install. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString LoadedFrom;

	/** True when the plugin folder contains Source (needed to compile against a custom engine). */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bHasSource = false;

	/** Absolute plugin root on disk. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString BaseDir;

	/** Enabled .uplugin dependencies that are missing or disabled, such as GeometryScripting. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	TArray<FString> MissingDependencies;
};

USTRUCT(BlueprintType)
struct FWorldBLDPackagingCheck
{
	GENERATED_BODY()

	/** Stable id such as InstallLocation, CppProject, FullRebuild, GeometryScripting. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Id;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Title;

	/** What this project currently looks like. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Status;

	/** True when this check does not look like a packaging blocker. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bLooksOk = true;

	/** What to tell the user if bLooksOk is false. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString Recommendation;
};

USTRUCT(BlueprintType)
struct FWorldBLDPackagingGuide
{
	GENERATED_BODY()

	/** How WorldBLD, CityBLD, RoadBLD, TwinBLD and the editor toolsets depend on each other. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString IntegrationOverview;

	/** Numbered fixes for the usual packaging / cook / plugin-load failures. Present these to the user. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	TArray<FString> CommonSolutions;

	/** Live failing checks plus solutions that match ErrorText. Lead with these. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	TArray<FString> SuggestedFirst;

	/** "Installed (Epic Games Launcher)" or "Source / custom engine build". */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString EngineKind;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bIsInstalledEngine = true;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString EngineVersion;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString EngineDir;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString ProjectDir;

	/** False for Blueprint-only projects; those must add a C++ class before these plugins will package. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bIsCppProject = false;

	/** Runtime game module name from the .uproject, if this is a C++ project. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString GameModuleName;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	FString GameModuleBuildCsPath;

	/** Project Settings > Packaging > Full Rebuild. Must be disabled. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bFullRebuildEnabled = false;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bGeometryScriptingEnabled = false;

	/** True when the game module Build.cs already lists GeometryScriptingCore. */
	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	bool bGameModuleListsGeometryScriptingCore = false;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	TArray<FWorldBLDPluginPackagingInfo> Plugins;

	UPROPERTY(BlueprintReadOnly, Category = "WorldBLDToolset")
	TArray<FWorldBLDPackagingCheck> Checks;
};

/**
 * Inspect WorldBLD editor session context: which product plugins are enabled,
 * whether WorldBLD edit mode is active, and landscapes / PCG volumes in the level.
 * Use EditorToolset.UEditorAppToolset for viewport capture and actor selection.
 * For WorldBLD / CityBLD / TwinBLD / RoadBLD packaging, cook, compile, or plugin-load errors,
 * call GetPackagingGuide before guessing.
 */
UCLASS(BlueprintType, MinimalAPI)
class UWorldBLDToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Reports whether WorldBLD, CityBLD, RoadBLD, and TwinBLD are discovered and enabled, with version names.
	 * @return Capability records for the four WorldBLD product plugins.
	 */
	UFUNCTION(meta = (AICallable), Category = "WorldBLDToolset")
	static TArray<FWorldBLDPluginCapability> GetCapabilities();

	/**
	 * Returns the current editor map and whether WorldBLD editor mode is active.
	 * @return Map name, world path, and WorldBLD editor-mode flag.
	 */
	UFUNCTION(meta = (AICallable), Category = "WorldBLDToolset")
	static FWorldBLDEditorContext GetEditorContext();

	/**
	 * Lists landscape proxies and PCG volumes in the current editor level.
	 * Results are capped so the response stays small; TotalCount is the uncapped match count.
	 * @return Bounded actor summary for landscapes and PCG volumes.
	 */
	UFUNCTION(meta = (AICallable), Category = "WorldBLDToolset")
	static FWorldBLDLevelActorList ListLevelActors();

	/**
	 * Activates or deactivates WorldBLD editor mode. This is a mutating editor-mode change.
	 * @param bActive True to enter WorldBLD editor mode, false to leave it.
	 * @return True if WorldBLD editor mode is active after the call.
	 */
	UFUNCTION(meta = (AICallable), Category = "WorldBLDToolset")
	static bool SetWorldBLDEditorModeActive(bool bActive);

	/**
	 * First-call tool for WorldBLD, CityBLD, TwinBLD, or RoadBLD packaging, cook, compile, or plugin-load failures.
	 * Returns how the product plugins integrate, live diagnostics for this project (launcher vs source engine,
	 * Engine vs Project install, Blueprint vs C++ project, Full Rebuild, GeometryScripting), and the usual fixes.
	 * Call this before guessing whenever a user reports packaging errors, cook failures, missing WorldBLD_Content,
	 * Unable to load plugin, or a packaged executable that will not launch.
	 * @param ErrorText Optional log excerpt or error message. When set, SuggestedFirst is ordered toward that error.
	 * @return Integration overview, common solutions, live checks, and plugin install details.
	 */
	UFUNCTION(meta = (AICallable), Category = "WorldBLDToolset")
	static FWorldBLDPackagingGuide GetPackagingGuide(FString ErrorText = TEXT(""));
};
