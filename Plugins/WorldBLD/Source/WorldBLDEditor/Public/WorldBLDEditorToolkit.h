// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "Tools/LegacyEdModeWidgetHelpers.h"
#include "Toolkits/BaseToolkit.h"

#include "Blueprint/UserWidget.h"
#include "UnrealEdMisc.h"
#include "WorldBLDEditorToolkit.generated.h"

WORLDBLDEDITOR_API DECLARE_LOG_CATEGORY_EXTERN(LogWorldBLDEditor, Log, All);

class AActor;
class SLevelViewport;
class SDockTab;
class SWidget;
class UWorldBLDMainWidget;
class UWorldBLDToolPaletteWidget;

USTRUCT(BlueprintType)
struct FPluginToolData
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Available Tool")
    FString ToolName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Available Tool")
    FString Description;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Available Tool")
    FString DownloadLink;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Available Tool")
    FString Version;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Available Tool")
    FString SHA1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Available Tool")
    FString ServerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,Category="Available Tool")
    TArray<FString> RequiredToolIds;
};

UENUM(BlueprintType)
enum class EWorldBLDToolUpdateState : uint8
{
	/** Tool/plugin is not currently installed in this project. */
	NotInstalled UMETA(DisplayName="Not Installed"),

	/** Tool/plugin is installed, but we don't have a reliable version string to compare against the server. */
	InstalledUnknownSha1 UMETA(DisplayName="Installed (Unknown Version)"),

	/** Tool/plugin is installed and the installed version matches (or exceeds) the server version. */
	UpToDate UMETA(DisplayName="Up To Date"),

	/** Tool/plugin is installed and the server version is newer than the installed version. */
	UpdateAvailable UMETA(DisplayName="Update Available")
};
///////////////////////////////////////////////////////////////////////////////////////////////////

// The root of the Edit Mode for the WorldBLDEditorToolkit. The native C++ class is now the real,
// registered Editor Mode (see UWorldBLDEdModeSettings::EditModeClass pointing at /Script/...).
// It stays Blueprintable for backwards compatibility with legacy BP_*_EdMode assets, but only the
// native class registers/shows in the mode dropdown (see the constructor's IsNative() guard) so any
// lingering Blueprint subclass cannot conflict on the shared editor mode id.
UCLASS(BlueprintType, Blueprintable)
class WORLDBLDEDITOR_API UWorldBLDEdMode : public UBaseLegacyWidgetEdMode
{
	GENERATED_BODY()

/* friends: */
    friend class FWorldBLDEdModeToolkit;
    friend class UWorldBLDMainWidget;
    friend class UWorldBLDKitEditorUtils;
    friend class FWorldBLDSelectModeWidgetHelper;

public:
    static const FEditorModeID EditorModeID;

	UWorldBLDEdMode();

    ///////////////////////////////////////////////////////////////////////////////////////////////

    UFUNCTION(BlueprintPure, Category="WorldBLDEditor")
    bool IsThisEdModeActive() const;

    UFUNCTION(BlueprintPure, Category="WorldBLDEditor")
    static UWorldBLDEdMode* GetWorldBLDEdMode();

	///////////////////////////////////////////////////////////////////////////////////////////////
	// Tool update helpers (version-based)

	/** Returns the SHA1 that was last recorded as installed for ToolId (empty if unknown). */
	UFUNCTION(BlueprintPure, Category="WorldBLD|ToolUpdates")
	FString GetRecordedInstalledToolSha1(const FString& ToolId) const;

	/** Returns update state for ToolId using installed plugin version and (optionally) server SHA1 metadata. */
	UFUNCTION(BlueprintPure, Category="WorldBLD|ToolUpdates")
	EWorldBLDToolUpdateState GetToolUpdateState(const FString& ToolId, const FString& ServerVersion, const FString& ServerSHA1) const;

	/** Triggers a refresh of the server tool list and re-evaluates update state. */
	UFUNCTION(BlueprintCallable, Category="WorldBLD|ToolUpdates")
	void RefreshAvailableToolsFromServer();

	/**
	 * Refreshes tools from the server and evaluates plugin version mismatch afterward.
	 * When bForceNotify is true, a mismatch modal is shown even if already notified this session.
	 */
	UFUNCTION(BlueprintCallable, Category="WorldBLD|ToolUpdates")
	void CheckForPluginUpdates(bool bForceNotify = true);

	/** Loads the WorldBLD demo map (same map used by the former first-time welcome prompt). */
	UFUNCTION(BlueprintCallable, Category="WorldBLD|Resources")
	static void OpenDemoMap();

	/**
	 * Returns true if the locally installed WorldBLD plugin is at least as new as the latest server version.
	 * Returns false when the server/local version is unknown so companion-tool updates stay blocked.
	 */
	UFUNCTION(BlueprintPure, Category="WorldBLD|ToolUpdates")
	bool IsWorldBLDPluginUpToDate() const;

	/** Returns the WorldBLD tool id as reported by the server tools endpoint (empty if unknown). */
	const FString& GetServerWorldBLDToolId() const { return ServerWorldBLDToolId; }

    // Legacy palette compatibility API (kept for binary/plugin upgrade safety).
    UFUNCTION(BlueprintPure, Category="WorldBLDEditor")
    UWorldBLDToolPaletteWidget* GetToolPaletteByClass(TSubclassOf<UWorldBLDToolPaletteWidget> ToolClass) const;

    UFUNCTION(BlueprintPure, Category="WorldBLDEditor")
    UWorldBLDToolPaletteWidget* GetActiveToolPalette() const;

    UFUNCTION(BlueprintPure, Category="WorldBLDEditor")
    TArray<UWorldBLDToolPaletteWidget*> GetAvailableToolPalettes() const;

    UFUNCTION(BlueprintCallable, Category="WorldBLDEditor")
    void SwitchToToolPaletteByClass(TSubclassOf<UWorldBLDToolPaletteWidget> ToolClass);

    UFUNCTION(BlueprintCallable, Category="WorldBLDEditor")
    void SwitchToToolPalette(UWorldBLDToolPaletteWidget* Palette, bool bForceFocused = false) const;

    // Legacy inline/sidebar config fields retained for serialized-asset compatibility.
    UPROPERTY(EditDefaultsOnly, BlueprintReadonly, Category="Config", Meta=(Untracked))
    TSoftClassPtr<UWorldBLDMainWidget> UserInterfaceClass;

    UPROPERTY(EditDefaultsOnly, BlueprintReadonly, Category="Config", Meta=(Untracked))
    TArray<TSoftClassPtr<UWorldBLDToolPaletteWidget>> CustomToolClasses;

    UPROPERTY(EditDefaultsOnly, BlueprintReadonly, Category="Config", Meta=(Untracked))
    bool bCreateToolkit {false};

    UPROPERTY(EditDefaultsOnly, BlueprintReadonly, Category="Config", Meta=(Untracked))
    TSoftClassPtr<class UWorldBLDEditController> DefaultToolClass;

    UPROPERTY(BlueprintReadOnly, Category="WorldBLDEditor", Meta=(Untracked))
    TArray<FPluginToolData> AvailableTools;
    ///////////////////////////////////////////////////////////////////////////////////////////////

    void InstallDefaultRecompileHandler();

    UFUNCTION(BlueprintCallable, Category="WorldBLDEditor")
    void MovePrimaryTabToSidebar() const;

    UFUNCTION(BlueprintCallable, Category="WorldBLDEditor")
    void RestorePrimaryTabFromSidebar() const;

    UFUNCTION(BlueprintPure, Category="WorldBLDEditor")
    bool IsPrimaryTabInSidebar() const;

    UFUNCTION(BlueprintCallable, Category="WorldBLDEditor")
    void TryOpenPrimaryTabSidebarDrawer() const;

    UFUNCTION(BlueprintCallable, Category="WorldBLDEditor")
    bool TryHideTabWell(bool bHide) const;

protected:
    UPROPERTY(Transient, BlueprintReadOnly, Category="WorldBLD|Tool")
    TArray<TObjectPtr<UWorldBLDEditController>> ToolModeStack;

    void ClearToolModeStack();
    void InstallDefaultSelectionTool();

public:

    UFUNCTION(BlueprintPure, Category="WorldBLD|Tool")
    UWorldBLDEditController* GetActiveEditController() const;

    //BP callable version of the function to revert to the default tool
    UFUNCTION(BlueprintCallable, Category="WorldBLD|Tool")
    void SwitchToMainWorldBLDWidget();

    UFUNCTION(BlueprintCallable, Category="WorldBLD|Tool")
    void PushEditController(UWorldBLDEditController* Controller);

    UFUNCTION(BlueprintCallable, Category="WorldBLD|Tool")
    void PopEditController(UWorldBLDEditController* OptionalController = nullptr);

    /**
     * Registers a controller class that should still allow WorldBLD selection context menus while active.
     * This replaces the legacy tool-palette MainSubtoolClass exemption path.
     */
    UFUNCTION(BlueprintCallable, Category="WorldBLD|ContextMenu")
    void RegisterContextMenuExemptControllerClass(TSubclassOf<UWorldBLDEditController> ControllerClass);

    /** Removes a previously registered context-menu exempt controller class. */
    UFUNCTION(BlueprintCallable, Category="WorldBLD|ContextMenu")
    void UnregisterContextMenuExemptControllerClass(TSubclassOf<UWorldBLDEditController> ControllerClass);

    /** Returns true if the controller is allowed to keep WorldBLD selection context menus visible. */
    UFUNCTION(BlueprintPure, Category="WorldBLD|ContextMenu")
    bool IsContextMenuControllerExempt(const UWorldBLDEditController* Controller) const;

    UFUNCTION(BlueprintCallable, Category="WorldBLD|Tool")
    bool IsLicensed(const FString& Credentials, const FString& ToolName) const;
    
    ///////////////////////////////////////////////////////////////////////////////////////////////
	// Context Menu (floating window)

	/** Create and display the context menu for the given actor selection (expects same-class selection). */
	void ShowContextMenuForActors(const TArray<AActor*>& Actors);

	/** Close the context menu window (if any) and clear tracking state. */
	void HideContextMenu();

	/** Returns true if a context menu window is currently active. */
	bool HasActiveContextMenu() const;

	/** Returns true if the given selection should show a context menu (provider + factory + can-create). */
	bool IsContextMenuRelevantForSelection(const TArray<AActor*>& SelectedActors) const;

    virtual bool InputKey(FEditorViewportClient* ViewportClient, FViewport* Viewport, FKey Key, EInputEvent Event) override;
    virtual bool IsSelectionAllowed(AActor* InActor, bool bInSelection) const override;    
    virtual bool MouseMove(FEditorViewportClient* ViewportClient, FViewport* Viewport, int32 x, int32 y) override;

public:
    /**
     * Broadcast at the end of Exit(), after the tool stack has been torn down.
     *
     * A static delegate rather than a hook into GLevelEditorModeTools(): dependent plugins need to
     * subscribe from StartupModule, and touching the level editor mode manager that early forces it
     * to initialise before UnrealEd is ready.
     */
    static FSimpleMulticastDelegate& OnWorldBLDEdModeExited();

    // >> UEdMode
    virtual void Enter() override;
    virtual void Exit() override;
    virtual void Tick(FEditorViewportClient* ViewportClient, float DeltaTime) override;
    virtual void Render(const FSceneView* View, FViewport* Viewport, FPrimitiveDrawInterface* PDI) override;
protected:
	virtual void CreateToolkit() override;
    // << UEdMode

    void OnBlueprintCompiled(UBlueprint* Blueprint);

public:
    // >> UBaseLegacyWidgetEdMode
    virtual bool UsesToolkits() const override;
    virtual bool HandleClick(FEditorViewportClient* InViewportClient, HHitProxy* HitProxy, const FViewportClick& Click) override;    
protected:
    virtual TSharedRef<FLegacyEdModeWidgetHelper> CreateWidgetHelper() override;
    // << UBaseLegacyWidgetEdMode

protected:
    void TryConstructUserWidget(TObjectPtr<UUserWidget>& WidgetRef, TSoftClassPtr<UUserWidget> WidgetClass, bool bForce = false);
    void DestructWidget(TObjectPtr<UUserWidget>& WidgetRef);
    void DestroyAllWidgets();

    void RegenerateContents(UBlueprint* RecompiledBlueprint);
    void OnMapChanged(UWorld* World, EMapChangeType MapChangeType);

    void PostEditorUndo(const struct FTransactionContext& TransactionContext, bool bSucceeded) const;
    void PostEditorRedo(const struct FTransactionContext& TransactionContext, bool bSucceeded) const;

private:
    void BuildLegacyPaletteCompatibilityCache();

	void EnsureLumenPostProcessVolumeExists();
    void FetchAvailableTools();
	void EvaluateWorldBLDPluginVersionAndNotify(bool bForce = false) const;

	/**
	 * Checks whether any installed dependent tools (RoadBLD, CityBLD, TwinBLD) fall below the
	 * minimum versions required by this WorldBLD release. When stale tools are found, a blocking
	 * modal dialog is shown that immediately stages downloads for each outdated tool and prompts
	 * the user to restart once all downloads are ready. Called once per session after the server
	 * tool list is fetched (so download URLs are available).
	 */
	void EvaluateDependentToolVersions();

	// Context menu helpers
	bool ValidateContextMenuTargets() const;
	static bool AreSameActorSelection(const TArray<AActor*>& Actors, const TArray<TWeakObjectPtr<AActor>>& WeakActors);

	// Viewport toolbar (Slate overlay, shown only while this mode is active)
	void ShowViewportToolbar();
	void HideViewportToolbar();
	void RefreshViewportToolbarVisibility();
	TWeakPtr<SLevelViewport> ViewportToolbarHostViewport;
	TSharedPtr<SWidget> ViewportToolbarOverlayWidget;

	/** Tool id whose toolbar is currently displayed in the viewport (defaults to "WorldBLD"). */
	FName ActiveViewportToolbarId;

public:
	/** Returns the tool id whose viewport toolbar is currently displayed. */
	FName GetActiveViewportToolbarId() const
	{
		return ActiveViewportToolbarId.IsNone() ? FName(TEXT("WorldBLD")) : ActiveViewportToolbarId;
	}

	/**
	 * Swaps the displayed viewport toolbar to the one registered for ToolId (e.g. "RoadBLD").
	 * "WorldBLD" (or NAME_None) returns to the WorldBLD toolbar. The swap is deferred to the
	 * next tick so it is safe to call from within a toolbar/menu button click handler.
	 */
	void SwitchViewportToolbar(FName ToolId);

private:

	// Context menu state
	TWeakPtr<SLevelViewport> ActiveContextMenuHostViewport;
	TSharedPtr<SWidget> ActiveContextMenuOverlayWidget;
	TWeakObjectPtr<AActor> ContextMenuTargetActor;
	TArray<TWeakObjectPtr<AActor>> ContextMenuTargetActors;
	bool bContextMenuHiddenByTool = false;

	// Warning tooltip overlay (follows mouse cursor, shows active controller's UserWarning)
	void ShowWarningTooltipOverlay();
	void HideWarningTooltipOverlay();
	TSharedPtr<SWidget> WarningTooltipOverlayWidget;
	TWeakPtr<SLevelViewport> WarningTooltipHostViewport;

    /** Runtime-selected controller classes that are allowed to keep selection context menus visible. */
    UPROPERTY(Transient)
    TArray<TSubclassOf<UWorldBLDEditController>> ContextMenuExemptControllerClasses;

    /** Legacy palette instances kept only for ABI/class-compatibility shims. */
    UPROPERTY(Transient)
    TArray<TObjectPtr<UWorldBLDToolPaletteWidget>> LegacyToolPalettes;

    UPROPERTY(Transient)
    TObjectPtr<UWorldBLDToolPaletteWidget> ActiveLegacyToolPalette {nullptr};

    bool bLegacyToolPalettesInitialized = false;

	// Cached server-side WorldBLD plugin version (from the tools API); used to warn when it differs from the local plugin version.
	FString ServerWorldBLDPluginVersion;
	// Cached server-side WorldBLD tool id (from the tools API); used to resolve requiredTools.toolId -> "WorldBLD" for asset gating.
	FString ServerWorldBLDToolId;
	bool bCheckWorldBLDPluginVersionOnNextToolsFetch = false;
	bool bForceWorldBLDPluginVersionNotifyOnNextToolsFetch = false;
};

///////////////////////////////////////////////////////////////////////////////////////////////////

// These settings are loaded directly from the Plugin's INI file.
UCLASS(Config=WorldBLD)
class UWorldBLDEdModeSettings : public UDeveloperSettings
{
    GENERATED_BODY()
public:

    // The Edit Mode class used. This shouldn't change.
    UPROPERTY(Config, Meta=(Untracked))
    TSoftClassPtr<UWorldBLDEdMode> EditModeClass;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWorldBLDLicChanged, class UWorldBLDEdModeLicenseSettings*, Settings, const FFilePath&, FilePath);

UCLASS(Config = EditorPerProjectUserSettings, BlueprintType)
class UWorldBLDEdModeLicenseSettings : public UDeveloperSettings
{
    GENERATED_BODY()
public:

    // Point this to your CityBLD License File (.lic) generated from worldbld.com
    UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "WorldBLD", Meta = (FilePathFilter = "WorldBLD License File (*.lic)|*.lic"))
    FFilePath LicenseFile;

    UFUNCTION(BlueprintCallable, Category = "WorldBLD")
    void ResetLicense();

    UPROPERTY(BlueprintAssignable)
    FOnWorldBLDLicChanged OnLicenseChanged;

    virtual void PostEditChangeProperty(struct FPropertyChangedEvent& PropertyChangedEvent) override;
};

///////////////////////////////////////////////////////////////////////////////////////////////////


class FWorldBLDEdModeToolkit: public FModeToolkit
{
    using Super = FModeToolkit;
public:

    FWorldBLDEdModeToolkit();

    // >> IToolkit
    virtual FName GetToolkitFName() const override;
    virtual FText GetBaseToolkitName() const override;
    virtual TSharedPtr<class SWidget> GetInlineContent() const override;
    virtual void InvokeUI() override;
    // << IToolkit

    TSharedPtr<SDockTab> GetPrimaryTab() const;

    TWeakObjectPtr<UWorldBLDEdMode> EditModeRef;
};

UCLASS(Config=WorldBLD, DefaultConfig)
class WORLDBLDEDITOR_API UWorldBLDEditorUISettings : public UDeveloperSettings
{
	GENERATED_BODY()
public:
	/** Temporary migration toggle. When false, legacy sidebar/palette UMG UI is disabled. */
	UPROPERTY(Config, EditAnywhere, Category="Migration")
	bool bEnableLegacySidebarUI = false;

	/**
	 * Temporary migration toggle. When true, keep the old palette-driven context-menu exemptions.
	 * Should remain false once all plugins use controller-based exemption registration.
	 */
	UPROPERTY(Config, EditAnywhere, Category="Migration")
	bool bUseLegacyPaletteContextMenuExemptions = false;
};

///////////////////////////////////////////////////////////////////////////////////////////////////

