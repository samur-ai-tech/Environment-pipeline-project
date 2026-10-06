// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Framework/SlateDelegates.h"

class SWidget;
struct FWorldBLDToolbarButtonDef;

/**
 * Factory helpers that build fully-configured, viewport-ready plugin toolbars
 * (an SWorldBLDViewportToolbarHost independently positioning the tool tabs and
 * an SWorldBLDPluginToolbar).
 *
 * Each plugin (WorldBLD, RoadBLD, CityBLD, TwinBLD, CrowdBLD) gets its own toolbar.
 * Plugins register a factory keyed by their tool id; the persistent WorldBLD tool
 * tab strip then swaps the displayed toolbar by tool id. The tool tabs, trailing
 * Manage Installation button, and three-dots overflow come from the shared
 * SWorldBLDPluginToolbar for free.
 */
namespace WorldBLDToolbar
{
	/** Factory signature for a plugin toolbar widget (an SWorldBLDViewportToolbarHost). */
	using FToolbarFactory = FOnGetContent;

	/** Registers (or replaces) the toolbar factory for a tool id (e.g. "RoadBLD"). */
	WORLDBLDEDITOR_API void RegisterToolbarFactory(FName ToolId, FToolbarFactory Factory);

	/** Removes a previously registered toolbar factory. */
	WORLDBLDEDITOR_API void UnregisterToolbarFactory(FName ToolId);

	/** Returns true if a toolbar factory is registered for the tool id. */
	WORLDBLDEDITOR_API bool HasToolbarFactory(FName ToolId);

	/**
	 * Builds the toolbar for a given tool id:
	 *  - "WorldBLD" -> the fully wired WorldBLD toolbar
	 *  - a registered tool id -> that plugin's registered factory
	 *  - anything else -> a placeholder toolbar
	 */
	WORLDBLDEDITOR_API TSharedRef<SWidget> CreateToolbarForTool(FName ToolId);

	/** Builds the fully wired WorldBLD viewport toolbar. */
	WORLDBLDEDITOR_API TSharedRef<SWidget> CreateWorldBLDToolbar();

	/** Builds the WorldBLD utility-bundle tile picker used by the Custom Tools tab. */
	WORLDBLDEDITOR_API TSharedRef<SWidget> CreateUtilitiesMenuContent();

	/**
	 * Builds a placeholder toolbar for a plugin whose tools are not yet ported.
	 * Contains disabled placeholder buttons plus the shared persistent elements.
	 */
	WORLDBLDEDITOR_API TSharedRef<SWidget> CreatePlaceholderToolbar(const FText& PluginDisplayName);

	/**
	 * Wraps a plugin's own buttons and the persistent tool tabs in independent
	 * draggable-host canvas slots. This is the entry point other plugin modules
	 * use to build their toolbar with consistent layout/styling.
	 *
	 * Automatically shows a far-right Manage button for non-WorldBLD tool toolbars
	 * (with live "Update Available" styling). Keep FWorldBLDToolbarButtonDef ABI
	 * stable — packaged plugins copy these arrays into WorldBLD.
	 */
	WORLDBLDEDITOR_API TSharedRef<SWidget> CreatePluginToolbarWidget(
		const TArray<FWorldBLDToolbarButtonDef>& MainButtons,
		const TArray<FWorldBLDToolbarButtonDef>& OverflowButtons);
}
