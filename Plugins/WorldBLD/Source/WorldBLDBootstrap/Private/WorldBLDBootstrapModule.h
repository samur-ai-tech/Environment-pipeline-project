// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleInterface.h"

class FJsonObject;

/**
 * Tiny early-loading module (PostConfigInit) whose sole purpose is to apply
 * staged plugin updates BEFORE tool-plugin DLLs are loaded (Default phase).
 *
 * It reads Saved/WorldBLD/StagedPluginUpdates.json, swaps the old plugin
 * directory with the staged one, and marks the manifest entry as applied so
 * CurlDownloaderLibrary::ProcessAppliedStagedUpdates() can finalize later.
 *
 * Uses a journaled, file-by-file copy approach for reliability:
 *   Phase BackupOld -> CopyNew (rename-aside clear + copy) -> Cleanup -> (journal deleted)
 * If the editor crashes mid-swap, the journal enables full recovery on next startup.
 */
class FWorldBLDBootstrapModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
// ─── Path helpers ──────────────────────────────────────────────────────────

	/** Path to the staged-updates manifest. */
	static FString GetStagedUpdatesManifestPath();

	/** Path to the deferred-deletion manifest (shared with CurlDownloaderLibrary). */
	static FString GetPendingDeletesManifestPath();

	/** Returns true if this project is a protected development workspace. */
	static bool IsProtectedDevProject();

	/** Path to the journal file for a given plugin swap operation. */
	static FString GetJournalPath(const FString& PluginName);

	/** Base directory for plugin backups (Saved/WorldBLD/Backups/). */
	static FString GetBackupsBaseDir();

// ─── Manifest processing ───────────────────────────────────────────────────

	/** Process all pending staged updates from the manifest. */
	void ProcessStagedUpdates();

// ─── Pending delete queue ──────────────────────────────────────────────────

	/**
	 * Process PendingPluginDeletes.json early, before any tool plugin DLLs are
	 * loaded, so cache and staging directories are more likely to be deletable.
	 * Entries that are already gone are silently removed; entries that still
	 * cannot be deleted are kept for a later retry by CurlDownloaderLibrary.
	 * Deletes the manifest file entirely when the queue becomes empty.
	 * Always runs, even in protected dev projects.
	 */
	static void ProcessPendingDeletes();

	/**
	 * Returns true only for paths that are safe to remove from the pending-delete
	 * queue. Rejects empty strings, drive/filesystem roots, project root, engine
	 * root, and the top-level Plugins/ and Saved/ directories. Allows any strict
	 * subdirectory of known safe roots: the project persistent-download dir,
	 * Saved/WorldBLD/, and the project Plugins/ folder.
	 */
	static bool IsSafePathToDelete(const FString& NormalizedAbsPath);

	/**
	 * Delete a directory tree robustly:
	 *   1. Fast path: single DeleteDirectory call.
	 *   2. On failure: clear read-only attribute on all contained files, then
	 *      retry up to MaxRetries times with short exponential backoff.
	 * Returns true if the directory was deleted or was already absent.
	 */
	static bool RobustDeleteDirectoryTree(const FString& Dir, int32 MaxRetries = 3);

// ─── Journaled swap ────────────────────────────────────────────────────────

	/**
	 * Replace the target plugin directory with the staged one using a
	 * journaled, file-by-file copy that is resilient to transient file locks,
	 * cross-volume paths, and crashes.
	 *
	 * Phases:
	 *   1. BackupOld  -- copy target plugin files to Saved/WorldBLD/Backups/
	 *   2. CopyNew    -- clear target via Windows-safe rename-aside (fallback: per-file
	 *                   delete/rename), then copy staged files (rollback on any clear/copy failure)
	 *   3. Cleanup    -- delete backup + staging + rename-aside dirs, delete journal
	 */
	static bool SwapPluginDirectoryJournaled(
		const FString& PluginName,
		const FString& StagingDir,
		const FString& TargetPluginDir);

	/**
	 * Clear TargetPluginDir so staged files can be copied into its path.
	 * Prefers renaming the whole directory to <Target>_wbld_swap_old (works on Windows
	 * even when plugin DLLs are memory-mapped). Falls back to per-file delete with retry,
	 * then per-file rename-aside for files that still cannot be deleted.
	 * On success, OutRenamedAsideDir is set when the whole-tree rename path was used.
	 */
	static bool ClearTargetDirectoryForSwap(
		const FString& TargetPluginDir,
		const FString& PluginName,
		FString& OutRenamedAsideDir);

	/**
	 * Delete a single file with short retry/backoff. Clears the read-only attribute first.
	 * Returns true if the file is gone (or was already absent).
	 */
	static bool DeleteFileWithRetry(const FString& FilePath, int32 MaxRetries = 3);

// ─── Journal helpers ───────────────────────────────────────────────────────

	/** Scan for leftover journal files and recover from any incomplete swaps. */
	static void RecoverFromAnyJournals();

	/** Recover from a single journal file. Returns true if handled successfully. */
	static bool RecoverFromJournal(const FString& JournalPath);

	/** Write (or overwrite) the journal JSON to disk. */
	static bool WriteJournal(const TSharedRef<FJsonObject>& Journal, const FString& JournalPath);

// ─── File utilities ────────────────────────────────────────────────────────

	/**
	 * Copy a single file with retry + backoff. Handles AV transient locks.
	 * Retries up to MaxRetries times with increasing delays (200ms, 500ms, 1000ms).
	 */
	static bool CopyFileWithRetry(
		const FString& SrcPath,
		const FString& DstPath,
		int32 MaxRetries = 3);

	/**
	 * Recursively collect all file paths under RootDir, returned as paths
	 * relative to RootDir (using forward slashes).
	 */
	static void CollectRelativeFilePaths(
		const FString& RootDir,
		TArray<FString>& OutRelativePaths);

// ─── Legacy cleanup ────────────────────────────────────────────────────────

	/** Schedule a directory for deferred deletion via PendingPluginDeletes.json. */
	static bool DeferDirectoryDelete(const FString& DirToDelete);

	/**
	 * Scan Plugins/ for leftover _old_ directories from a previous (legacy) swap
	 * that crashed before cleanup could finish, and remove them.
	 * Kept for one release cycle for backwards compatibility.
	 */
	static void CleanUpLeftoverOldDirectories();

	/**
	 * Scan Plugins/ for leftover partial-install temp directories (_wbld_temp suffix)
	 * and old-version backup directories (_wbld_old suffix) left by an interrupted
	 * immediate install.
	 *
	 * _wbld_temp directories are always removed.
	 * _wbld_old backups are removed only when the canonical plugin directory exists
	 * and has a valid matching .uplugin descriptor; otherwise backups are preserved.
	 * Called before ProcessStagedUpdates() so no DLLs are loaded.
	 */
	static void ScanAndCleanPartialInstalls();
};
