// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDBootstrapModule.h"

#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "HAL/PlatformProcess.h"
#include "Misc/App.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Policies/PrettyJsonPrintPolicy.h"

DEFINE_LOG_CATEGORY_STATIC(LogWorldBLDBootstrap, Log, All);

// Journal phase identifiers.
namespace JournalPhase
{
	const TCHAR* BackupOld = TEXT("BackupOld");
	const TCHAR* CopyNew   = TEXT("CopyNew");
	const TCHAR* Cleanup   = TEXT("Cleanup");
}

// ───────────────────────────────────────────────────────────────────────────
// JSON helpers (local)
// ───────────────────────────────────────────────────────────────────────────

namespace
{
	/** Serialize a JSON object to a pretty-printed string and save to disk. */
	bool SaveJsonToFile(const TSharedRef<FJsonObject>& JsonObj, const FString& FilePath)
	{
		IFileManager::Get().MakeDirectory(*FPaths::GetPath(FilePath), true);
		FString OutJson;
		const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
			TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&OutJson);
		if (!FJsonSerializer::Serialize(JsonObj, Writer))
		{
			return false;
		}
		return FFileHelper::SaveStringToFile(OutJson, *FilePath);
	}

	/** Load a JSON object from a file. */
	TSharedPtr<FJsonObject> LoadJsonFromFile(const FString& FilePath)
	{
		FString JsonText;
		if (!FFileHelper::LoadFileToString(JsonText, *FilePath))
		{
			return nullptr;
		}
		TSharedPtr<FJsonObject> Root;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
		if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
		{
			return nullptr;
		}
		return Root;
	}

	/** Convert a TArray<FString> to a TArray<TSharedPtr<FJsonValue>> of string values. */
	TArray<TSharedPtr<FJsonValue>> StringArrayToJsonArray(const TArray<FString>& Strings)
	{
		TArray<TSharedPtr<FJsonValue>> Result;
		Result.Reserve(Strings.Num());
		for (const FString& S : Strings)
		{
			Result.Add(MakeShared<FJsonValueString>(S));
		}
		return Result;
	}

	/** Read a string array from a JSON object field. */
	TArray<FString> JsonArrayToStringArray(const TSharedPtr<FJsonObject>& Obj, const FString& FieldName)
	{
		TArray<FString> Result;
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		if (Obj.IsValid() && Obj->TryGetArrayField(FieldName, Arr) && Arr)
		{
			for (const TSharedPtr<FJsonValue>& Val : *Arr)
			{
				FString S;
				if (Val.IsValid() && Val->TryGetString(S))
				{
					Result.Add(S);
				}
			}
		}
		return Result;
	}
}

// ───────────────────────────────────────────────────────────────────────────
// Module lifecycle
// ───────────────────────────────────────────────────────────────────────────

IMPLEMENT_MODULE(FWorldBLDBootstrapModule, WorldBLDBootstrap)

void FWorldBLDBootstrapModule::StartupModule()
{
	// Always attempt to clear the pending-delete queue first, even in protected
	// dev projects, since stale entries should never block an install retry.
	ProcessPendingDeletes();

	if (IsProtectedDevProject())
	{
		UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Protected dev project detected -- skipping staged update processing."));
		return;
	}

	CleanUpLeftoverOldDirectories();
	RecoverFromAnyJournals();
	ScanAndCleanPartialInstalls();
	ProcessStagedUpdates();
}

void FWorldBLDBootstrapModule::ShutdownModule()
{
}

// ───────────────────────────────────────────────────────────────────────────
// Path helpers
// ───────────────────────────────────────────────────────────────────────────

FString FWorldBLDBootstrapModule::GetStagedUpdatesManifestPath()
{
	return FPaths::ConvertRelativePathToFull(
		FPaths::ProjectSavedDir() / TEXT("WorldBLD/StagedPluginUpdates.json"));
}

FString FWorldBLDBootstrapModule::GetPendingDeletesManifestPath()
{
	return FPaths::ConvertRelativePathToFull(
		FPaths::ProjectSavedDir() / TEXT("WorldBLD/PendingPluginDeletes.json"));
}

bool FWorldBLDBootstrapModule::IsProtectedDevProject()
{
	const FString ProjectDir = FPaths::ProjectDir();
	return FPaths::FileExists(ProjectDir / TEXT("WORLDBLD_API_DOCUMENTATION.md"))
		|| FPaths::FileExists(ProjectDir / TEXT("GenerateAndBuildProject.bat"));
}

FString FWorldBLDBootstrapModule::GetJournalPath(const FString& PluginName)
{
	return FPaths::ConvertRelativePathToFull(
		FPaths::ProjectSavedDir() / TEXT("WorldBLD") / (TEXT("UpdateJournal_") + PluginName + TEXT(".json")));
}

FString FWorldBLDBootstrapModule::GetBackupsBaseDir()
{
	return FPaths::ConvertRelativePathToFull(
		FPaths::ProjectSavedDir() / TEXT("WorldBLD/Backups"));
}

// ───────────────────────────────────────────────────────────────────────────
// Pending delete queue
// ───────────────────────────────────────────────────────────────────────────

bool FWorldBLDBootstrapModule::IsSafePathToDelete(const FString& NormalizedAbsPath)
{
	if (NormalizedAbsPath.IsEmpty())
	{
		return false;
	}

	if (FPaths::IsRelative(NormalizedAbsPath))
	{
		UE_LOG(LogWorldBLDBootstrap, Warning,
			TEXT("IsSafePathToDelete: rejecting relative path '%s'"), *NormalizedAbsPath);
		return false;
	}

	// Reject drive/filesystem roots and anything suspiciously short (e.g. "C:/", "/").
	if (NormalizedAbsPath.Len() <= 4)
	{
		return false;
	}

	// Helper: true when Path is a strict subdirectory of Root (not Root itself).
	auto IsStrictSubdir = [](const FString& Path, const FString& Root) -> bool
	{
		if (Root.IsEmpty())
		{
			return false;
		}
		FString NormRoot = FPaths::ConvertRelativePathToFull(Root);
		FPaths::NormalizeDirectoryName(NormRoot);
		FString NormPath = Path;
		FPaths::NormalizeDirectoryName(NormPath);
		if (!NormRoot.EndsWith(TEXT("/")))
		{
			NormRoot += TEXT("/");
		}
		return NormPath.StartsWith(NormRoot, ESearchCase::IgnoreCase) && NormPath.Len() > NormRoot.Len();
	};

	// Known safe parent directories.
	if (IsStrictSubdir(NormalizedAbsPath, FPaths::ProjectPersistentDownloadDir()))
	{
		return true;
	}
	if (IsStrictSubdir(NormalizedAbsPath, FPaths::ProjectSavedDir() / TEXT("WorldBLD")))
	{
		return true;
	}
	if (IsStrictSubdir(NormalizedAbsPath, FPaths::ProjectPluginsDir()))
	{
		return true;
	}

	return false;
}

bool FWorldBLDBootstrapModule::RobustDeleteDirectoryTree(const FString& Dir, int32 MaxRetries)
{
	if (!FPaths::DirectoryExists(Dir))
	{
		return true;
	}

	// Fast path -- works most of the time.
	if (IFileManager::Get().DeleteDirectory(*Dir, false, true))
	{
		return true;
	}

	// Clear read-only attribute on every file so Windows will permit deletion.
	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
	PlatformFile.IterateDirectoryRecursively(*Dir,
		[&PlatformFile](const TCHAR* FilenameOrDir, bool bIsDirectory) -> bool
		{
			if (!bIsDirectory)
			{
				PlatformFile.SetReadOnly(FilenameOrDir, false);
			}
			return true;
		});

	static const float RetryDelaysSeconds[] = { 0.2f, 0.5f, 1.0f, 2.0f };
	const int32 ClampedRetries = FMath::Clamp(MaxRetries, 0, static_cast<int32>(UE_ARRAY_COUNT(RetryDelaysSeconds)));

	for (int32 Attempt = 0; Attempt < ClampedRetries; ++Attempt)
	{
		const float Delay = RetryDelaysSeconds[Attempt];
		UE_LOG(LogWorldBLDBootstrap, Log,
			TEXT("RobustDeleteDirectoryTree: retry %d/%d for '%s' after %.1fs ..."),
			Attempt + 1, ClampedRetries, *Dir, Delay);
		FPlatformProcess::Sleep(Delay);

		if (IFileManager::Get().DeleteDirectory(*Dir, false, true))
		{
			UE_LOG(LogWorldBLDBootstrap, Log,
				TEXT("RobustDeleteDirectoryTree: deleted '%s' on retry %d."), *Dir, Attempt + 1);
			return true;
		}
	}

	UE_LOG(LogWorldBLDBootstrap, Warning,
		TEXT("RobustDeleteDirectoryTree: could not delete '%s' after %d retries. "
		     "Files may be held open by another process or an AV/cloud-sync tool."),
		*Dir, ClampedRetries);
	return false;
}

void FWorldBLDBootstrapModule::ProcessPendingDeletes()
{
	const FString ManifestPath = GetPendingDeletesManifestPath();
	if (!FPaths::FileExists(ManifestPath))
	{
		return;
	}

	const TSharedPtr<FJsonObject> Root = LoadJsonFromFile(ManifestPath);
	if (!Root.IsValid())
	{
		UE_LOG(LogWorldBLDBootstrap, Warning,
			TEXT("ProcessPendingDeletes: manifest '%s' could not be parsed -- deleting corrupt file."),
			*ManifestPath);
		IFileManager::Get().Delete(*ManifestPath);
		return;
	}

	const TArray<FString> PendingDirs = JsonArrayToStringArray(Root, TEXT("PendingDeletes"));
	if (PendingDirs.IsEmpty())
	{
		IFileManager::Get().Delete(*ManifestPath);
		return;
	}

	UE_LOG(LogWorldBLDBootstrap, Log,
		TEXT("ProcessPendingDeletes: processing %d pending deletion(s) from manifest."),
		PendingDirs.Num());

	TArray<FString> RemainingDirs;
	for (const FString& Dir : PendingDirs)
	{
		const FString NormalizedDir = FPaths::ConvertRelativePathToFull(Dir);

		if (NormalizedDir.IsEmpty())
		{
			continue;
		}

		if (!FPaths::DirectoryExists(NormalizedDir))
		{
			UE_LOG(LogWorldBLDBootstrap, Log,
				TEXT("ProcessPendingDeletes: '%s' no longer exists -- removing from queue."),
				*NormalizedDir);
			continue;
		}

		if (!IsSafePathToDelete(NormalizedDir))
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("ProcessPendingDeletes: '%s' is not in a recognized safe location -- "
				     "removing from queue without deleting. Inspect the manifest if this is unexpected."),
				*NormalizedDir);
			continue;
		}

		if (RobustDeleteDirectoryTree(NormalizedDir))
		{
			UE_LOG(LogWorldBLDBootstrap, Log,
				TEXT("ProcessPendingDeletes: successfully deleted '%s'."), *NormalizedDir);
		}
		else
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("ProcessPendingDeletes: '%s' still could not be deleted -- "
				     "keeping in queue for later retry."),
				*NormalizedDir);
			RemainingDirs.Add(Dir);
		}
	}

	if (RemainingDirs.IsEmpty())
	{
		UE_LOG(LogWorldBLDBootstrap, Log,
			TEXT("ProcessPendingDeletes: all entries resolved -- deleting manifest."));
		IFileManager::Get().Delete(*ManifestPath);
	}
	else
	{
		UE_LOG(LogWorldBLDBootstrap, Log,
			TEXT("ProcessPendingDeletes: %d entry(s) remain after early-startup pass; "
			     "CurlDownloaderLibrary will retry during editor init."),
			RemainingDirs.Num());
		TSharedRef<FJsonObject> NewRoot = MakeShared<FJsonObject>();
		NewRoot->SetArrayField(TEXT("PendingDeletes"), StringArrayToJsonArray(RemainingDirs));
		SaveJsonToFile(NewRoot, ManifestPath);
	}
}

// ───────────────────────────────────────────────────────────────────────────
// Manifest processing
// ───────────────────────────────────────────────────────────────────────────

void FWorldBLDBootstrapModule::ProcessStagedUpdates()
{
	const FString ManifestPath = GetStagedUpdatesManifestPath();
	if (!FPaths::FileExists(ManifestPath))
	{
		return;
	}

	FString JsonText;
	if (!FFileHelper::LoadFileToString(JsonText, *ManifestPath))
	{
		UE_LOG(LogWorldBLDBootstrap, Warning, TEXT("Failed to read staged-updates manifest: %s"), *ManifestPath);
		return;
	}

	TSharedPtr<FJsonObject> Root;
	{
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
		if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
		{
			UE_LOG(LogWorldBLDBootstrap, Warning, TEXT("Failed to parse staged-updates manifest JSON."));
			return;
		}
	}

	const TArray<TSharedPtr<FJsonValue>>* StagedArray = nullptr;
	if (!Root->TryGetArrayField(TEXT("StagedUpdates"), StagedArray) || (StagedArray == nullptr))
	{
		return;
	}

	const FDateTime Now = FDateTime::UtcNow();
	constexpr int32 MaxStaleDays = 7;
	bool bManifestDirty = false;

	// Collect latest entry per plugin name (in case of duplicates).
	TMap<FString, int32> LatestEntryIndex; // PluginName -> index in StagedArray
	for (int32 Idx = 0; Idx < StagedArray->Num(); ++Idx)
	{
		const TSharedPtr<FJsonObject> Entry = (*StagedArray)[Idx].IsValid()
			? (*StagedArray)[Idx]->AsObject()
			: nullptr;
		if (!Entry.IsValid())
		{
			continue;
		}

		// Skip already-applied entries (will be finalized by CurlDownloaderLibrary later).
		bool bApplied = false;
		Entry->TryGetBoolField(TEXT("Applied"), bApplied);
		if (bApplied)
		{
			continue;
		}

		FString PluginName;
		if (!Entry->TryGetStringField(TEXT("PluginName"), PluginName) || PluginName.IsEmpty())
		{
			continue;
		}

		// Stale check.
		FString TimestampStr;
		if (Entry->TryGetStringField(TEXT("Timestamp"), TimestampStr))
		{
			FDateTime EntryTime;
			if (FDateTime::ParseIso8601(*TimestampStr, EntryTime))
			{
				const FTimespan Age = Now - EntryTime;
				if (Age.GetTotalDays() > MaxStaleDays)
				{
					UE_LOG(LogWorldBLDBootstrap, Warning,
						TEXT("Staged update for '%s' is stale (%.1f days old) -- skipping and cleaning up."),
						*PluginName, Age.GetTotalDays());

					FString StagingDir;
					if (Entry->TryGetStringField(TEXT("StagingDir"), StagingDir) && FPaths::DirectoryExists(StagingDir))
					{
						IFileManager::Get().DeleteDirectory(*StagingDir, false, true);
					}

					Entry->SetBoolField(TEXT("Applied"), true);
					bManifestDirty = true;
					continue;
				}
			}
		}

		// Keep only the latest entry per plugin (by index, which correlates with append order).
		if (const int32* Existing = LatestEntryIndex.Find(PluginName))
		{
			// Mark the older duplicate as applied so it gets cleaned up.
			if (const TSharedPtr<FJsonObject> OlderEntry = (*StagedArray)[*Existing]->AsObject())
			{
				FString OldStagingDir;
				if (OlderEntry->TryGetStringField(TEXT("StagingDir"), OldStagingDir) && FPaths::DirectoryExists(OldStagingDir))
				{
					IFileManager::Get().DeleteDirectory(*OldStagingDir, false, true);
				}
				OlderEntry->SetBoolField(TEXT("Applied"), true);
				bManifestDirty = true;
			}
		}
		LatestEntryIndex.Add(PluginName, Idx);
	}

	// Process the latest entry for each plugin.
	for (const TPair<FString, int32>& Pair : LatestEntryIndex)
	{
		const TSharedPtr<FJsonObject> Entry = (*StagedArray)[Pair.Value]->AsObject();
		if (!Entry.IsValid())
		{
			continue;
		}

		const FString& PluginName = Pair.Key;
		FString StagingDir;
		FString TargetPluginDir;
		if (!Entry->TryGetStringField(TEXT("StagingDir"), StagingDir) || StagingDir.IsEmpty()
			|| !Entry->TryGetStringField(TEXT("TargetPluginDir"), TargetPluginDir) || TargetPluginDir.IsEmpty())
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("Staged update for '%s' has missing StagingDir or TargetPluginDir -- skipping."), *PluginName);
			continue;
		}

		// Validate that the staging dir contains a .uplugin file.
		const FString ExpectedUpluginFile = StagingDir / (PluginName + TEXT(".uplugin"));
		if (!FPaths::FileExists(ExpectedUpluginFile))
		{
			UE_LOG(LogWorldBLDBootstrap, Error,
				TEXT("Staged update for '%s' is missing .uplugin file at '%s' -- skipping."),
				*PluginName, *ExpectedUpluginFile);
			continue;
		}

		// Before swapping, read module names from both old and new .uplugin for mismatch detection.
		TArray<FString> OldModuleNames;
		TArray<FString> NewModuleNames;
		{
			auto ExtractModuleNames = [](const FString& UpluginPath, TArray<FString>& OutNames)
			{
				FString DescJson;
				if (!FFileHelper::LoadFileToString(DescJson, *UpluginPath))
				{
					return;
				}
				TSharedPtr<FJsonObject> DescRoot;
				const TSharedRef<TJsonReader<>> DescReader = TJsonReaderFactory<>::Create(DescJson);
				if (!FJsonSerializer::Deserialize(DescReader, DescRoot) || !DescRoot.IsValid())
				{
					return;
				}
				const TArray<TSharedPtr<FJsonValue>>* ModulesArray = nullptr;
				if (DescRoot->TryGetArrayField(TEXT("Modules"), ModulesArray) && ModulesArray)
				{
					for (const TSharedPtr<FJsonValue>& ModVal : *ModulesArray)
					{
						const TSharedPtr<FJsonObject> ModObj = ModVal.IsValid() ? ModVal->AsObject() : nullptr;
						if (ModObj.IsValid())
						{
							FString ModName;
							if (ModObj->TryGetStringField(TEXT("Name"), ModName) && !ModName.IsEmpty())
							{
								OutNames.Add(ModName);
							}
						}
					}
				}
			};

			const FString OldUpluginPath = TargetPluginDir / (PluginName + TEXT(".uplugin"));
			if (FPaths::FileExists(OldUpluginPath))
			{
				ExtractModuleNames(OldUpluginPath, OldModuleNames);
			}
			ExtractModuleNames(ExpectedUpluginFile, NewModuleNames);
		}

		UE_LOG(LogWorldBLDBootstrap, Log,
			TEXT("Applying staged update for '%s': '%s' -> '%s'"), *PluginName, *StagingDir, *TargetPluginDir);

		if (SwapPluginDirectoryJournaled(PluginName, StagingDir, TargetPluginDir))
		{
			Entry->SetBoolField(TEXT("Applied"), true);
			bManifestDirty = true;

			UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Staged update for '%s' applied successfully."), *PluginName);

			// Module name mismatch detection: if the update adds or removes modules, the engine's
			// plugin descriptor cache (populated during discovery, before this module runs) references
			// the OLD module list.  New modules won't be loaded until a second restart.
			OldModuleNames.Sort();
			NewModuleNames.Sort();
			if (OldModuleNames != NewModuleNames)
			{
				UE_LOG(LogWorldBLDBootstrap, Warning,
					TEXT("Module list changed for '%s' (old: %d modules, new: %d modules). "
						 "A second restart may be needed to fully load the new module set."),
					*PluginName, OldModuleNames.Num(), NewModuleNames.Num());
			}
		}
		else
		{
			UE_LOG(LogWorldBLDBootstrap, Error, TEXT("Staged update for '%s' FAILED -- old version preserved."), *PluginName);
		}
	}

	// Rewrite manifest so CurlDownloaderLibrary can finalize applied entries.
	if (bManifestDirty)
	{
		SaveJsonToFile(Root.ToSharedRef(), ManifestPath);
	}
}

// ───────────────────────────────────────────────────────────────────────────
// File utilities
// ───────────────────────────────────────────────────────────────────────────

bool FWorldBLDBootstrapModule::CopyFileWithRetry(const FString& SrcPath, const FString& DstPath, int32 MaxRetries)
{
	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();

	// Ensure parent directory exists.
	IFileManager::Get().MakeDirectory(*FPaths::GetPath(DstPath), true);

	static const double RetryDelaysSeconds[] = { 0.2, 0.5, 1.0, 2.0 };

	for (int32 Attempt = 0; Attempt <= MaxRetries; ++Attempt)
	{
		if (PlatformFile.CopyFile(*DstPath, *SrcPath))
		{
			return true;
		}

		if (Attempt < MaxRetries)
		{
			const double Delay = (Attempt < UE_ARRAY_COUNT(RetryDelaysSeconds))
				? RetryDelaysSeconds[Attempt]
				: RetryDelaysSeconds[UE_ARRAY_COUNT(RetryDelaysSeconds) - 1];

			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("CopyFile failed (attempt %d/%d): '%s' -> '%s'. Retrying in %.1fs..."),
				Attempt + 1, MaxRetries + 1, *SrcPath, *DstPath, Delay);

			FPlatformProcess::Sleep(static_cast<float>(Delay));

			// On retry, try deleting the destination first in case it's read-only or partially written.
			if (FPaths::FileExists(DstPath))
			{
				PlatformFile.SetReadOnly(*DstPath, false);
				PlatformFile.DeleteFile(*DstPath);
			}
		}
	}

	UE_LOG(LogWorldBLDBootstrap, Error,
		TEXT("CopyFile failed after %d attempts: '%s' -> '%s'"), MaxRetries + 1, *SrcPath, *DstPath);
	return false;
}

bool FWorldBLDBootstrapModule::DeleteFileWithRetry(const FString& FilePath, int32 MaxRetries)
{
	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
	if (!FPaths::FileExists(FilePath))
	{
		return true;
	}

	static const double RetryDelaysSeconds[] = { 0.2, 0.5, 1.0, 2.0 };

	for (int32 Attempt = 0; Attempt <= MaxRetries; ++Attempt)
	{
		PlatformFile.SetReadOnly(*FilePath, false);
		if (PlatformFile.DeleteFile(*FilePath) || !FPaths::FileExists(FilePath))
		{
			return true;
		}

		if (Attempt < MaxRetries)
		{
			const double Delay = (Attempt < UE_ARRAY_COUNT(RetryDelaysSeconds))
				? RetryDelaysSeconds[Attempt]
				: RetryDelaysSeconds[UE_ARRAY_COUNT(RetryDelaysSeconds) - 1];

			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("DeleteFile failed (attempt %d/%d): '%s'. Retrying in %.1fs..."),
				Attempt + 1, MaxRetries + 1, *FilePath, Delay);

			FPlatformProcess::Sleep(static_cast<float>(Delay));
		}
	}

	return false;
}

bool FWorldBLDBootstrapModule::ClearTargetDirectoryForSwap(
	const FString& TargetPluginDir,
	const FString& PluginName,
	FString& OutRenamedAsideDir)
{
	OutRenamedAsideDir.Reset();
	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();

	if (!FPaths::DirectoryExists(TargetPluginDir))
	{
		return true;
	}

	// Preferred path: rename the whole tree aside.
	// On Windows, memory-mapped plugin DLLs can usually be renamed but not deleted.
	// This matches the immediate-install Move strategy in CurlDownloaderLibrary.
	auto MakeUniqueAsideDir = [&TargetPluginDir]() -> FString
	{
		FString Candidate = TargetPluginDir + TEXT("_wbld_swap_old");
		if (!FPaths::DirectoryExists(Candidate))
		{
			return Candidate;
		}

		for (int32 Attempt = 0; Attempt < 8; ++Attempt)
		{
			Candidate = FString::Printf(
				TEXT("%s_wbld_swap_old_%s_%d"),
				*TargetPluginDir,
				*FDateTime::UtcNow().ToString(TEXT("%Y%m%d%H%M%S")),
				Attempt);
			if (!FPaths::DirectoryExists(Candidate))
			{
				return Candidate;
			}
		}

		return TargetPluginDir + TEXT("_wbld_swap_old_") + FGuid::NewGuid().ToString(EGuidFormats::Digits);
	};

	// Clear a stale leftover aside dir from a previous crash when possible.
	{
		const FString StaleAside = TargetPluginDir + TEXT("_wbld_swap_old");
		if (FPaths::DirectoryExists(StaleAside))
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("ClearTargetDirectoryForSwap '%s': removing stale aside dir '%s' before rename."),
				*PluginName, *StaleAside);
			if (!RobustDeleteDirectoryTree(StaleAside))
			{
				DeferDirectoryDelete(StaleAside);
			}
		}
	}

	const FString AsideDir = MakeUniqueAsideDir();
	if (IFileManager::Get().Move(
		*AsideDir,
		*TargetPluginDir,
		/*Replace*/ false,
		/*EvenIfReadOnly*/ true,
		/*Attributes*/ false,
		/*bDoNotRetryOrError*/ true))
	{
		UE_LOG(LogWorldBLDBootstrap, Log,
			TEXT("ClearTargetDirectoryForSwap '%s': renamed target aside '%s' -> '%s'."),
			*PluginName, *TargetPluginDir, *AsideDir);
		OutRenamedAsideDir = AsideDir;
		return true;
	}

	UE_LOG(LogWorldBLDBootstrap, Warning,
		TEXT("ClearTargetDirectoryForSwap '%s': directory rename-aside failed for '%s'. Falling back to per-file clear."),
		*PluginName, *TargetPluginDir);

	// Fallback: per-file delete, then rename-aside for stubborn files.
	TArray<FString> FilesToClear;
	CollectRelativeFilePaths(TargetPluginDir, FilesToClear);
	TArray<FString> PendingDeleteFiles;

	for (const FString& RelPath : FilesToClear)
	{
		const FString FilePath = TargetPluginDir / RelPath;
		if (DeleteFileWithRetry(FilePath))
		{
			continue;
		}

		// Windows often allows renaming a mapped DLL even when DeleteFile fails.
		const FString AsideFilePath = FilePath + TEXT(".wbld_pending_delete");
		if (FPaths::FileExists(AsideFilePath))
		{
			DeleteFileWithRetry(AsideFilePath, /*MaxRetries*/ 1);
		}

		PlatformFile.SetReadOnly(*FilePath, false);
		if (IFileManager::Get().Move(
			*AsideFilePath,
			*FilePath,
			/*Replace*/ true,
			/*EvenIfReadOnly*/ true,
			/*Attributes*/ false,
			/*bDoNotRetryOrError*/ true))
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("ClearTargetDirectoryForSwap '%s': renamed locked file aside '%s'."),
				*PluginName, *FilePath);
			PendingDeleteFiles.Add(AsideFilePath);
			continue;
		}

		UE_LOG(LogWorldBLDBootstrap, Error,
			TEXT("ClearTargetDirectoryForSwap '%s': could not delete or rename '%s'."),
			*PluginName, *FilePath);
		return false;
	}

	// Best-effort cleanup of per-file rename-aside leftovers (may still be locked).
	for (const FString& PendingFile : PendingDeleteFiles)
	{
		if (!DeleteFileWithRetry(PendingFile, /*MaxRetries*/ 1))
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("ClearTargetDirectoryForSwap '%s': leaving pending-delete file '%s' for later cleanup."),
				*PluginName, *PendingFile);
		}
	}

	return true;
}

void FWorldBLDBootstrapModule::CollectRelativeFilePaths(const FString& RootDir, TArray<FString>& OutRelativePaths)
{
	const FString NormalizedRoot = FPaths::ConvertRelativePathToFull(RootDir);

	IFileManager::Get().IterateDirectoryRecursively(*NormalizedRoot,
		[&NormalizedRoot, &OutRelativePaths](const TCHAR* FilenameOrDir, bool bIsDirectory) -> bool
	{
		if (!bIsDirectory)
		{
			FString FullPath(FilenameOrDir);
			FPaths::MakePathRelativeTo(FullPath, *(NormalizedRoot / TEXT("")));
			OutRelativePaths.Add(MoveTemp(FullPath));
		}
		return true; // continue iteration
	});
}

// ───────────────────────────────────────────────────────────────────────────
// Journal helpers
// ───────────────────────────────────────────────────────────────────────────

bool FWorldBLDBootstrapModule::WriteJournal(const TSharedRef<FJsonObject>& Journal, const FString& JournalPath)
{
	return SaveJsonToFile(Journal, JournalPath);
}

void FWorldBLDBootstrapModule::RecoverFromAnyJournals()
{
	const FString WorldBLDDir = FPaths::ConvertRelativePathToFull(
		FPaths::ProjectSavedDir() / TEXT("WorldBLD"));

	if (!FPaths::DirectoryExists(WorldBLDDir))
	{
		return;
	}

	TArray<FString> JournalFiles;
	IFileManager::Get().IterateDirectory(*WorldBLDDir,
		[&JournalFiles](const TCHAR* FilenameOrDir, bool bIsDirectory) -> bool
	{
		if (!bIsDirectory)
		{
			const FString FileName = FPaths::GetCleanFilename(FilenameOrDir);
			if (FileName.StartsWith(TEXT("UpdateJournal_")) && FileName.EndsWith(TEXT(".json")))
			{
				JournalFiles.Add(FilenameOrDir);
			}
		}
		return true;
	});

	for (const FString& JournalPath : JournalFiles)
	{
		UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Found incomplete update journal: %s"), *JournalPath);
		RecoverFromJournal(JournalPath);
	}
}

bool FWorldBLDBootstrapModule::RecoverFromJournal(const FString& JournalPath)
{
	const TSharedPtr<FJsonObject> Journal = LoadJsonFromFile(JournalPath);
	if (!Journal.IsValid())
	{
		UE_LOG(LogWorldBLDBootstrap, Warning, TEXT("Could not parse journal file '%s' -- deleting it."), *JournalPath);
		IFileManager::Get().Delete(*JournalPath);
		return true;
	}

	FString Phase;
	FString PluginName;
	FString BackupDir;
	FString TargetPluginDir;
	Journal->TryGetStringField(TEXT("Phase"), Phase);
	Journal->TryGetStringField(TEXT("PluginName"), PluginName);
	Journal->TryGetStringField(TEXT("BackupDir"), BackupDir);
	Journal->TryGetStringField(TEXT("TargetPluginDir"), TargetPluginDir);

	UE_LOG(LogWorldBLDBootstrap, Log,
		TEXT("Recovering journal for '%s' at phase '%s'"), *PluginName, *Phase);

	if (Phase == JournalPhase::BackupOld)
	{
		// Backup was incomplete.  Target plugin dir is still intact (we only copy FROM it, never
		// modify it during BackupOld).  Just delete the partial backup and the journal.
		if (!BackupDir.IsEmpty() && FPaths::DirectoryExists(BackupDir))
		{
			UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Deleting partial backup: %s"), *BackupDir);
			IFileManager::Get().DeleteDirectory(*BackupDir, false, true);
		}
		IFileManager::Get().Delete(*JournalPath);
		UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Recovery complete (BackupOld) for '%s'. Update will retry next restart."), *PluginName);
		return true;
	}

	if (Phase == JournalPhase::CopyNew)
	{
		// Partial clear/copy over target. Restore from backup.
		FString RenamedAsideDir;
		Journal->TryGetStringField(TEXT("RenamedAsideDir"), RenamedAsideDir);

		if (BackupDir.IsEmpty() || !FPaths::DirectoryExists(BackupDir))
		{
			// If the journaled file backup is missing but we renamed the live tree aside,
			// try to move it back as a last-resort restore.
			if (!RenamedAsideDir.IsEmpty()
				&& FPaths::DirectoryExists(RenamedAsideDir)
				&& !TargetPluginDir.IsEmpty()
				&& !FPaths::DirectoryExists(TargetPluginDir))
			{
				UE_LOG(LogWorldBLDBootstrap, Warning,
					TEXT("Backup missing for '%s'; attempting restore via rename-aside dir '%s'."),
					*PluginName, *RenamedAsideDir);
				if (IFileManager::Get().Move(
					*TargetPluginDir,
					*RenamedAsideDir,
					/*Replace*/ false,
					/*EvenIfReadOnly*/ true,
					/*Attributes*/ false,
					/*bDoNotRetryOrError*/ true))
				{
					IFileManager::Get().Delete(*JournalPath);
					UE_LOG(LogWorldBLDBootstrap, Log,
						TEXT("Rollback complete for '%s': restored target from rename-aside dir. Update will retry next restart."),
						*PluginName);
					return true;
				}
			}

			UE_LOG(LogWorldBLDBootstrap, Error,
				TEXT("Cannot rollback '%s': backup directory '%s' is missing. Manual intervention required."),
				*PluginName, *BackupDir);
			IFileManager::Get().Delete(*JournalPath);
			return false;
		}

		// Restore backed-up files.
		const TArray<FString> BackedUpFiles = JsonArrayToStringArray(Journal, TEXT("FilesBackedUp"));
		int32 RestoredCount = 0;
		bool bRestoreFailed = false;
		for (const FString& RelPath : BackedUpFiles)
		{
			const FString SrcFile = BackupDir / RelPath;
			const FString DstFile = TargetPluginDir / RelPath;
			if (FPaths::FileExists(SrcFile))
			{
				if (CopyFileWithRetry(SrcFile, DstFile))
				{
					++RestoredCount;
				}
				else
				{
					UE_LOG(LogWorldBLDBootstrap, Error, TEXT("Failed to restore file: %s"), *DstFile);
					bRestoreFailed = true;
				}
			}
		}

		// Remove any files that were copied from the NEW version but don't exist in the backup
		// (i.e., files that the new version added which shouldn't be in the rolled-back state).
		const TArray<FString> CopiedNewFiles = JsonArrayToStringArray(Journal, TEXT("FilesCopied"));
		TSet<FString> BackedUpFileSet(BackedUpFiles);
		for (const FString& RelPath : CopiedNewFiles)
		{
			if (!BackedUpFileSet.Contains(RelPath))
			{
				const FString OrphanFile = TargetPluginDir / RelPath;
				if (FPaths::FileExists(OrphanFile))
				{
					if (!DeleteFileWithRetry(OrphanFile))
					{
						UE_LOG(LogWorldBLDBootstrap, Error,
							TEXT("Failed to delete rollback orphan file '%s' for '%s'."), *OrphanFile, *PluginName);
						bRestoreFailed = true;
					}
				}
			}
		}

		if (bRestoreFailed)
		{
			UE_LOG(LogWorldBLDBootstrap, Error,
				TEXT("Rollback for '%s' was incomplete. Keeping backup '%s' and journal '%s' for retry/manual recovery."),
				*PluginName, *BackupDir, *JournalPath);
			return false;
		}

		UE_LOG(LogWorldBLDBootstrap, Log,
			TEXT("Rollback complete for '%s': restored %d files from backup. Update will retry next restart."),
			*PluginName, RestoredCount);

		// Clean up rename-aside tree (duplicate of the restored install) if present.
		if (!RenamedAsideDir.IsEmpty() && FPaths::DirectoryExists(RenamedAsideDir))
		{
			if (!IFileManager::Get().DeleteDirectory(*RenamedAsideDir, false, true))
			{
				DeferDirectoryDelete(RenamedAsideDir);
			}
		}

		// Clean up backup and journal.
		IFileManager::Get().DeleteDirectory(*BackupDir, false, true);
		IFileManager::Get().Delete(*JournalPath);
		return true;
	}

	if (Phase == JournalPhase::Cleanup)
	{
		// Copy succeeded but cleanup didn't finish. Just finish the cleanup.
		FString RenamedAsideDir;
		Journal->TryGetStringField(TEXT("RenamedAsideDir"), RenamedAsideDir);
		if (!RenamedAsideDir.IsEmpty() && FPaths::DirectoryExists(RenamedAsideDir))
		{
			if (!IFileManager::Get().DeleteDirectory(*RenamedAsideDir, false, true))
			{
				DeferDirectoryDelete(RenamedAsideDir);
			}
		}

		if (!BackupDir.IsEmpty() && FPaths::DirectoryExists(BackupDir))
		{
			IFileManager::Get().DeleteDirectory(*BackupDir, false, true);
		}

		FString StagingDir;
		if (Journal->TryGetStringField(TEXT("StagingDir"), StagingDir)
			&& !StagingDir.IsEmpty() && FPaths::DirectoryExists(StagingDir))
		{
			IFileManager::Get().DeleteDirectory(*StagingDir, false, true);
		}

		IFileManager::Get().Delete(*JournalPath);
		UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Recovery complete (Cleanup) for '%s'."), *PluginName);
		return true;
	}

	// Unknown phase -- delete the journal.
	UE_LOG(LogWorldBLDBootstrap, Warning, TEXT("Unknown journal phase '%s' for '%s' -- deleting journal."), *Phase, *PluginName);
	IFileManager::Get().Delete(*JournalPath);
	return true;
}

// ───────────────────────────────────────────────────────────────────────────
// Journaled directory swap
// ───────────────────────────────────────────────────────────────────────────

bool FWorldBLDBootstrapModule::SwapPluginDirectoryJournaled(
	const FString& PluginName,
	const FString& StagingDir,
	const FString& TargetPluginDir)
{
	const FString JournalPath = GetJournalPath(PluginName);

	// Build the backup directory path.
	const FString Timestamp = FDateTime::UtcNow().ToString(TEXT("%Y%m%d%H%M%S"));
	const FString BackupDir = GetBackupsBaseDir() / (PluginName + TEXT("_") + Timestamp);

	// Collect file lists.
	TArray<FString> StagedFiles;
	CollectRelativeFilePaths(StagingDir, StagedFiles);

	TArray<FString> OldFiles;
	const bool bTargetExists = FPaths::DirectoryExists(TargetPluginDir);
	if (bTargetExists)
	{
		CollectRelativeFilePaths(TargetPluginDir, OldFiles);
	}

	UE_LOG(LogWorldBLDBootstrap, Log,
		TEXT("SwapJournaled '%s': %d staged files, %d existing files."),
		*PluginName, StagedFiles.Num(), OldFiles.Num());

// ─── Phase 1 ───────────────────────────────────────────────────────────────

	TSharedRef<FJsonObject> Journal = MakeShared<FJsonObject>();
	Journal->SetStringField(TEXT("PluginName"), PluginName);
	Journal->SetStringField(TEXT("Phase"), JournalPhase::BackupOld);
	Journal->SetStringField(TEXT("StagingDir"), StagingDir);
	Journal->SetStringField(TEXT("TargetPluginDir"), TargetPluginDir);
	Journal->SetStringField(TEXT("BackupDir"), BackupDir);
	Journal->SetStringField(TEXT("Timestamp"), FDateTime::UtcNow().ToIso8601());
	Journal->SetArrayField(TEXT("FilesBackedUp"), TArray<TSharedPtr<FJsonValue>>());
	Journal->SetArrayField(TEXT("FilesCopied"), TArray<TSharedPtr<FJsonValue>>());

	if (!WriteJournal(Journal, JournalPath))
	{
		UE_LOG(LogWorldBLDBootstrap, Error, TEXT("Failed to create update journal for '%s'."), *PluginName);
		return false;
	}

	if (bTargetExists)
	{
		UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Phase 1/3: Backing up %d files from '%s'..."), OldFiles.Num(), *TargetPluginDir);

		TArray<FString> BackedUpFiles;
		BackedUpFiles.Reserve(OldFiles.Num());

		for (const FString& RelPath : OldFiles)
		{
			const FString SrcFile = TargetPluginDir / RelPath;
			const FString DstFile = BackupDir / RelPath;

			if (!CopyFileWithRetry(SrcFile, DstFile))
			{
				UE_LOG(LogWorldBLDBootstrap, Error,
					TEXT("Failed to backup file '%s'. Aborting swap for '%s'."), *SrcFile, *PluginName);

				// Abort: clean up partial backup and journal.
				IFileManager::Get().DeleteDirectory(*BackupDir, false, true);
				IFileManager::Get().Delete(*JournalPath);
				return false;
			}

			BackedUpFiles.Add(RelPath);
		}

		// Update journal with completed backup list.
		Journal->SetArrayField(TEXT("FilesBackedUp"), StringArrayToJsonArray(BackedUpFiles));
		WriteJournal(Journal, JournalPath);
	}

// ─── Phase 2 ───────────────────────────────────────────────────────────────
	// Strategy: clear the target path via Windows-safe rename-aside (preferred),
	// then copy staged files into the free path. Directory rename works even when
	// plugin DLLs are memory-mapped; DeleteFile does not. Any clear/copy failure
	// rolls back from the Phase 1 backup.

	Journal->SetStringField(TEXT("Phase"), JournalPhase::CopyNew);
	WriteJournal(Journal, JournalPath);

	FString RenamedAsideDir;
	if (bTargetExists && FPaths::DirectoryExists(TargetPluginDir))
	{
		UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Phase 2/3: Clearing existing target '%s' before copy..."), *TargetPluginDir);
		if (!ClearTargetDirectoryForSwap(TargetPluginDir, PluginName, RenamedAsideDir))
		{
			UE_LOG(LogWorldBLDBootstrap, Error,
				TEXT("Failed to clear existing target '%s' before copy. Aborting and rolling back '%s'."),
				*TargetPluginDir, *PluginName);
			if (!RenamedAsideDir.IsEmpty())
			{
				Journal->SetStringField(TEXT("RenamedAsideDir"), RenamedAsideDir);
			}
			WriteJournal(Journal, JournalPath);
			if (!RecoverFromJournal(JournalPath))
			{
				UE_LOG(LogWorldBLDBootstrap, Error,
					TEXT("Rollback after pre-copy clear failure did not complete for '%s'."), *PluginName);
			}
			return false;
		}

		if (!RenamedAsideDir.IsEmpty())
		{
			Journal->SetStringField(TEXT("RenamedAsideDir"), RenamedAsideDir);
			WriteJournal(Journal, JournalPath);
		}
	}

	UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Phase 2/3: Copying %d staged files to '%s'..."), StagedFiles.Num(), *TargetPluginDir);

	TArray<FString> CopiedFiles;
	CopiedFiles.Reserve(StagedFiles.Num());
	bool bCopyFailed = false;

	for (const FString& RelPath : StagedFiles)
	{
		const FString SrcFile = StagingDir / RelPath;
		const FString DstFile = TargetPluginDir / RelPath;

		if (!CopyFileWithRetry(SrcFile, DstFile))
		{
			UE_LOG(LogWorldBLDBootstrap, Error,
				TEXT("Failed to copy staged file '%s'. Rolling back '%s'."), *SrcFile, *PluginName);
			bCopyFailed = true;
			break;
		}

		CopiedFiles.Add(RelPath);

		// Periodically update journal with progress (every 50 files).
		if ((CopiedFiles.Num() % 50) == 0)
		{
			Journal->SetArrayField(TEXT("FilesCopied"), StringArrayToJsonArray(CopiedFiles));
			WriteJournal(Journal, JournalPath);
		}
	}

	// Final journal update for copied files.
	Journal->SetArrayField(TEXT("FilesCopied"), StringArrayToJsonArray(CopiedFiles));

	if (bCopyFailed)
	{
		// Rollback: restore from backup.
		WriteJournal(Journal, JournalPath);
		if (!RecoverFromJournal(JournalPath))
		{
			UE_LOG(LogWorldBLDBootstrap, Error,
				TEXT("Rollback after copy failure did not complete for '%s'."), *PluginName);
		}
		return false;
	}

// ─── Phase 3 ───────────────────────────────────────────────────────────────

	Journal->SetStringField(TEXT("Phase"), JournalPhase::Cleanup);
	WriteJournal(Journal, JournalPath);

	UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Phase 3/3: Cleaning up backup and staging directories..."));

	// Delete rename-aside directory left by ClearTargetDirectoryForSwap.
	if (!RenamedAsideDir.IsEmpty() && FPaths::DirectoryExists(RenamedAsideDir))
	{
		if (!IFileManager::Get().DeleteDirectory(*RenamedAsideDir, false, true))
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("Could not delete rename-aside directory '%s' -- deferring."), *RenamedAsideDir);
			DeferDirectoryDelete(RenamedAsideDir);
		}
	}

	// Delete backup directory.
	if (FPaths::DirectoryExists(BackupDir))
	{
		if (!IFileManager::Get().DeleteDirectory(*BackupDir, false, true))
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("Could not delete backup directory '%s' -- deferring."), *BackupDir);
			DeferDirectoryDelete(BackupDir);
		}
	}

	// Delete staging directory.
	if (FPaths::DirectoryExists(StagingDir))
	{
		if (!IFileManager::Get().DeleteDirectory(*StagingDir, false, true))
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("Could not delete staging directory '%s' -- deferring."), *StagingDir);
			DeferDirectoryDelete(StagingDir);
		}
	}

	// Delete the journal.
	IFileManager::Get().Delete(*JournalPath);

	UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Journaled swap complete for '%s'."), *PluginName);
	return true;
}

// ───────────────────────────────────────────────────────────────────────────
// Deferred deletion (mirrors the CurlDownloaderLibrary pattern)
// ───────────────────────────────────────────────────────────────────────────

bool FWorldBLDBootstrapModule::DeferDirectoryDelete(const FString& DirToDelete)
{
	const FString PendingPath = FPaths::ConvertRelativePathToFull(
		FPaths::ProjectSavedDir() / TEXT("WorldBLD/PendingPluginDeletes.json"));

	// Read existing pending list.
	TArray<FString> PendingDirs;
	if (FPaths::FileExists(PendingPath))
	{
		FString JsonText;
		if (FFileHelper::LoadFileToString(JsonText, *PendingPath))
		{
			TSharedPtr<FJsonObject> Root;
			const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
			if (FJsonSerializer::Deserialize(Reader, Root) && Root.IsValid())
			{
				const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
				if (Root->TryGetArrayField(TEXT("PendingDeletes"), Arr) && Arr)
				{
					for (const TSharedPtr<FJsonValue>& Val : *Arr)
					{
						FString Dir;
						if (Val.IsValid() && Val->TryGetString(Dir) && !Dir.IsEmpty())
						{
							PendingDirs.AddUnique(Dir);
						}
					}
				}
			}
		}
	}

	PendingDirs.AddUnique(DirToDelete);

	// Write back.
	TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetArrayField(TEXT("PendingDeletes"), StringArrayToJsonArray(PendingDirs));
	return SaveJsonToFile(Root, PendingPath);
}

// ───────────────────────────────────────────────────────────────────────────
// Partial-install cleanup
// ───────────────────────────────────────────────────────────────────────────

void FWorldBLDBootstrapModule::ScanAndCleanPartialInstalls()
{
	// Directories to scan: the project Plugins/ folder AND the ImmediateTemp staging area.
	const FString PluginsDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectPluginsDir());
	const FString ImmediateTempDir = FPaths::ConvertRelativePathToFull(
		FPaths::ProjectSavedDir() / TEXT("WorldBLD/ImmediateTemp"));

	auto DeleteOrDeferDirectory = [](const FString& Dir, const TCHAR* Reason)
	{
		UE_LOG(LogWorldBLDBootstrap, Warning,
			TEXT("ScanAndCleanPartialInstalls: removing %s '%s'"), Reason, *Dir);
		if (!IFileManager::Get().DeleteDirectory(*Dir, false, true))
		{
			UE_LOG(LogWorldBLDBootstrap, Warning,
				TEXT("ScanAndCleanPartialInstalls: could not immediately delete '%s' -- deferring."), *Dir);
			FWorldBLDBootstrapModule::DeferDirectoryDelete(Dir);
		}
	};

	auto IsCanonicalPluginDirValid = [](const FString& CanonicalPluginDir, const FString& PluginName) -> bool
	{
		if (!FPaths::DirectoryExists(CanonicalPluginDir))
		{
			return false;
		}

		const FString DescriptorPath = CanonicalPluginDir / (PluginName + TEXT(".uplugin"));
		if (!FPaths::FileExists(DescriptorPath))
		{
			return false;
		}

		FString DescriptorJson;
		if (!FFileHelper::LoadFileToString(DescriptorJson, *DescriptorPath))
		{
			return false;
		}

		TSharedPtr<FJsonObject> DescriptorRoot;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(DescriptorJson);
		return FJsonSerializer::Deserialize(Reader, DescriptorRoot) && DescriptorRoot.IsValid();
	};

	if (FPaths::DirectoryExists(PluginsDir))
	{
		TArray<FString> TempDirsToDelete;
		TArray<FString> BackupDirsToEvaluate;
		TArray<FString> SwapAsideDirsToEvaluate;
		IFileManager::Get().IterateDirectory(*PluginsDir,
			[&TempDirsToDelete, &BackupDirsToEvaluate, &SwapAsideDirsToEvaluate](const TCHAR* FilenameOrDir, bool bIsDirectory) -> bool
		{
			if (!bIsDirectory)
			{
				return true;
			}

			const FString DirName = FPaths::GetCleanFilename(FilenameOrDir);
			if (DirName.EndsWith(TEXT("_wbld_temp")))
			{
				TempDirsToDelete.Add(FilenameOrDir);
			}
			else if (DirName.EndsWith(TEXT("_wbld_old")))
			{
				BackupDirsToEvaluate.Add(FilenameOrDir);
			}
			else if (DirName.Contains(TEXT("_wbld_swap_old")))
			{
				SwapAsideDirsToEvaluate.Add(FilenameOrDir);
			}
			return true;
		});

		for (const FString& TempDir : TempDirsToDelete)
		{
			DeleteOrDeferDirectory(TempDir, TEXT("leftover immediate temp directory"));
		}

		for (const FString& BackupDir : BackupDirsToEvaluate)
		{
			const FString BackupName = FPaths::GetCleanFilename(BackupDir);
			const FString PluginName = BackupName.LeftChop(FCString::Strlen(TEXT("_wbld_old")));
			const FString CanonicalPluginDir = PluginsDir / PluginName;
			if (IsCanonicalPluginDirValid(CanonicalPluginDir, PluginName))
			{
				DeleteOrDeferDirectory(BackupDir, TEXT("recoverable old backup (canonical plugin is valid)"));
			}
			else
			{
				UE_LOG(LogWorldBLDBootstrap, Warning,
					TEXT("ScanAndCleanPartialInstalls: preserving backup '%s' because canonical plugin '%s' is missing or invalid."),
					*BackupDir, *CanonicalPluginDir);
			}
		}

		// Rename-aside leftovers from staged swaps. Safe to remove only when the live
		// target path (suffix stripped) exists again — otherwise this may be the only copy.
		const FString SwapAsideMarker(TEXT("_wbld_swap_old"));
		for (const FString& AsideDir : SwapAsideDirsToEvaluate)
		{
			const FString AsideName = FPaths::GetCleanFilename(AsideDir);
			const int32 MarkerPos = AsideName.Find(SwapAsideMarker, ESearchCase::CaseSensitive);
			if (MarkerPos == INDEX_NONE)
			{
				continue;
			}

			const FString BaseName = AsideName.Left(MarkerPos);
			const FString LiveTargetDir = PluginsDir / BaseName;
			if (FPaths::DirectoryExists(LiveTargetDir))
			{
				DeleteOrDeferDirectory(AsideDir, TEXT("leftover staged-swap rename-aside directory"));
			}
			else
			{
				UE_LOG(LogWorldBLDBootstrap, Warning,
					TEXT("ScanAndCleanPartialInstalls: preserving rename-aside '%s' because live target '%s' is missing."),
					*AsideDir, *LiveTargetDir);
			}
		}
	}

	// Also wipe every subdirectory under ImmediateTemp -- anything left there is a
	// failed extraction that never made it to the final Plugins/ location.
	if (FPaths::DirectoryExists(ImmediateTempDir))
	{
		TArray<FString> StaleTempDirs;
		IFileManager::Get().IterateDirectory(*ImmediateTempDir,
			[&StaleTempDirs](const TCHAR* FilenameOrDir, bool bIsDirectory) -> bool
		{
			if (bIsDirectory)
			{
				StaleTempDirs.Add(FilenameOrDir);
			}
			return true;
		});

		for (const FString& Dir : StaleTempDirs)
		{
			DeleteOrDeferDirectory(Dir, TEXT("stale ImmediateTemp extraction"));
		}
	}
}

// ───────────────────────────────────────────────────────────────────────────
// Leftover _old directory cleanup (legacy, kept for backwards compatibility)
// ───────────────────────────────────────────────────────────────────────────

void FWorldBLDBootstrapModule::CleanUpLeftoverOldDirectories()
{
	const FString PluginsDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectPluginsDir());

	// Pattern: <PluginsDir>/<Name>_old_<timestamp>
	// We look for directories matching *_old_* at the top level of the Plugins folder.
	TArray<FString> FoundDirs;
	IFileManager::Get().IterateDirectory(*PluginsDir, [&FoundDirs](const TCHAR* FilenameOrDir, bool bIsDirectory) -> bool
	{
		if (bIsDirectory)
		{
			const FString DirName = FPaths::GetCleanFilename(FilenameOrDir);
			if (DirName.Contains(TEXT("_old_")))
			{
				FoundDirs.Add(FilenameOrDir);
			}
		}
		return true; // continue iteration
	});

	for (const FString& OldDir : FoundDirs)
	{
		// Only delete if the corresponding "real" plugin directory also exists
		// (meaning the swap completed but cleanup didn't).
		const FString DirName = FPaths::GetCleanFilename(OldDir);
		int32 OldMarkerIdx = INDEX_NONE;
		if (DirName.FindChar(TEXT('_'), OldMarkerIdx))
		{
			// Find the _old_ marker position.
			const int32 OldPos = DirName.Find(TEXT("_old_"), ESearchCase::CaseSensitive);
			if (OldPos != INDEX_NONE)
			{
				const FString BaseName = DirName.Left(OldPos);
				const FString RealDir = PluginsDir / BaseName;
				if (FPaths::DirectoryExists(RealDir))
				{
					UE_LOG(LogWorldBLDBootstrap, Log, TEXT("Cleaning up leftover old directory: %s"), *OldDir);
					if (!IFileManager::Get().DeleteDirectory(*OldDir, false, true))
					{
						DeferDirectoryDelete(OldDir);
					}
				}
				// If the real dir doesn't exist, the swap may not have completed -- leave the _old dir alone.
			}
		}
	}
}
