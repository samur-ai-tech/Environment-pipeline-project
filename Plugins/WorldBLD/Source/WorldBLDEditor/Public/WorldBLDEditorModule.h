// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

#include "Utilities/UtilsEditorContext_Manager.h"
#include "Framework/MultiBox/MultiBoxExtender.h"
DECLARE_MULTICAST_DELEGATE(FOnWorldBLDLevelTemplateBundlesChanged);
DECLARE_DELEGATE(FOnOpenBuildingMeshCreatorRequested);
DECLARE_DELEGATE(FOnOpenBuildingStyleCreatorRequested);
DECLARE_DELEGATE(FOnOpenGroundFloorCreatorRequested);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnPopulateWorldBLDMenuExtensions, FMenuBuilder& /*MenuBuilder*/);

WORLDBLDEDITOR_API DECLARE_LOG_CATEGORY_EXTERN(LogWorldBuild, Log, All);

class FMenuBarBuilder;
class FMenuBuilder;
class UWorldBLDLevelTemplateBundle;
class UWorldBLDContextMenuRegistry;
class AActor;
class SLevelViewport;
class SWidget;

/**
 * This is the module definition for the editor mode. You can implement custom functionality
 * as your plugin module starts up and shuts down. See IModuleInterface for more extensibility options.
 */
class WORLDBLDEDITOR_API FWorldBLDEditorModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	static FString GetModuleName();
	static void SetOpenBuildingMeshCreatorDelegate(FOnOpenBuildingMeshCreatorRequested InDelegate);
	static void ClearOpenBuildingMeshCreatorDelegate();
	static bool CanOpenBuildingMeshCreator();
	static void OpenBuildingMeshCreator();
	static void SetOpenBuildingStyleCreatorDelegate(FOnOpenBuildingStyleCreatorRequested InDelegate);
	static void ClearOpenBuildingStyleCreatorDelegate();
	static bool CanOpenBuildingStyleCreator();
	static void OpenBuildingStyleCreator();
	static void SetOpenGroundFloorCreatorDelegate(FOnOpenGroundFloorCreatorRequested InDelegate);
	static void ClearOpenGroundFloorCreatorDelegate();
	static bool CanOpenGroundFloorCreator();
	static void OpenGroundFloorCreator();
	static FOnPopulateWorldBLDMenuExtensions& GetWorldBLDMenuExtensions();

	void ScanContentForLevelTemplateBundles();

	const TArray<TWeakObjectPtr<UWorldBLDLevelTemplateBundle>>& GetAvailableLevelTemplateBundles() const { return AvailableLevelTemplateBundles; }

	FOnWorldBLDLevelTemplateBundlesChanged OnAvailableLevelTemplateBundlesChanged;
	TArray<TWeakObjectPtr<UWorldBLDLevelTemplateBundle>> AvailableLevelTemplateBundles;

	virtual UUtilsEditorContext_Manager& GetContextManager() const { return *ContextManagerPtr;};
	UWorldBLDContextMenuRegistry* GetContextMenuRegistry();

	/** Debug/testing helper: shows a WorldBLD context menu in the active level viewport overlay. */
	void CreateAndShowContextMenu(AActor* Actor);

private:
	void RegisterCustomizations();
	void UnregisterCustomizations();

	void HandleTestContextMenuCommand();

	/** Debug-only: toggled by the WorldBLD.TestContextMenu console command. */
	TWeakPtr<SLevelViewport> TestContextMenuHostViewport;
	TSharedPtr<SWidget> TestContextMenuOverlayWidget;

	TWeakObjectPtr<class UUtilsEditorContext_Manager> ContextManagerPtr;
	TWeakObjectPtr<UWorldBLDContextMenuRegistry> ContextMenuRegistryPtr;
	static TSharedPtr<class FSlateStyleSet> InstalledStyle;
	void HandleLevelTemplateSelected(UWorldBLDLevelTemplateBundle* Bundle);

	void ExtendLevelEditorMenu();
	void ExtendFileMenu();
	void AddWorldBLDMenuBarExtension(FMenuBarBuilder& MenuBarBuilder);
	void PopulateWorldBLDMenu(FMenuBuilder& MenuBuilder);
	void AddLevelTemplateFileMenuItem(FMenuBuilder& MenuBuilder);

	TSharedPtr<FExtender> AssetLibraryMenuExtender;
	TSharedPtr<FExtender> FileMenuExtender;

	FDelegateHandle AssetRegistryLevelTemplatesFilesLoadedHandle;
	FDelegateHandle LevelTemplateSelectedHandle;

	static FOnOpenBuildingMeshCreatorRequested OpenBuildingMeshCreatorDelegate;
	static FOnOpenBuildingStyleCreatorRequested OpenBuildingStyleCreatorDelegate;
	static FOnOpenGroundFloorCreatorRequested OpenGroundFloorCreatorDelegate;
	static FOnPopulateWorldBLDMenuExtensions WorldBLDMenuExtensions;
};
