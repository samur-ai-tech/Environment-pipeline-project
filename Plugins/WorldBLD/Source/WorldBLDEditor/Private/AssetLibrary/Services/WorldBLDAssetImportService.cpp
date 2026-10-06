// Copyright WorldBLD LLC. All rights reserved.

#include "AssetLibrary/Services/WorldBLDAssetImportService.h"

#include "AssetLibrary/Services/WorldBLDAssetImportArtifact.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformProcess.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "RenderingThread.h"
#include "UObject/LinkerLoad.h"
#include "UObject/UObjectGlobals.h"

DEFINE_LOG_CATEGORY_STATIC(LogWorldBLDAssetImportService, Log, All);

namespace
{
	static FString GetCurrentSystemErrorText()
	{
		TCHAR SystemError[1024] = { 0 };
		FPlatformMisc::GetSystemErrorMessage(SystemError, UE_ARRAY_COUNT(SystemError), 0);
		return FString(SystemError).TrimStartAndEnd();
	}

	static void DetachLoadedPackageForFilename(const FString& Filename)
	{
		FString LongPackageName;
		if (!FPackageName::TryConvertFilenameToLongPackageName(Filename, LongPackageName))
		{
			return;
		}

		if (UPackage* Package = FindPackage(nullptr, *LongPackageName))
		{
			ResetLoaders(Package);
		}
	}

	static void DetachLoadedDestinationPackages(const FWorldBLDDownloadedArtifact& Artifact, const FString& DestRootOnDisk, IPlatformFile& PlatformFile)
	{
		TArray<FString> DestPackageFiles;
		DestPackageFiles.Reserve(Artifact.Files.Num());

		for (const FWorldBLDAssetImportFileEntry& FileEntry : Artifact.Files)
		{
			if (FileEntry.RelativePathFromPackageRoot.IsEmpty())
			{
				continue;
			}

			const FString DestPath = FPaths::Combine(DestRootOnDisk, FileEntry.RelativePathFromPackageRoot);
			const FString Ext = FPaths::GetExtension(DestPath).ToLower();
			if (Ext != TEXT("uasset") && Ext != TEXT("umap"))
			{
				continue;
			}

			if (!PlatformFile.FileExists(*DestPath))
			{
				continue;
			}

			DestPackageFiles.Add(DestPath);
		}

		if (DestPackageFiles.Num() == 0)
		{
			return;
		}

		FlushRenderingCommands();
		for (const FString& DestPackageFile : DestPackageFiles)
		{
			DetachLoadedPackageForFilename(DestPackageFile);
		}
	}

	static bool DeleteFileWithRetries(IPlatformFile& PlatformFile, const FString& DestPath, int32 MaxAttempts, FString& OutSystemError)
	{
		OutSystemError.Reset();

		for (int32 Attempt = 1; Attempt <= MaxAttempts; ++Attempt)
		{
			PlatformFile.SetReadOnly(*DestPath, false);
			DetachLoadedPackageForFilename(DestPath);

			if (PlatformFile.DeleteFile(*DestPath))
			{
				return true;
			}

			OutSystemError = GetCurrentSystemErrorText();
			if (Attempt < MaxAttempts)
			{
				FPlatformProcess::Sleep(0.05f * static_cast<float>(Attempt));
			}
		}

		return false;
	}

	static bool CopyFileWithRetries(IPlatformFile& PlatformFile, const FString& DestPath, const FString& SourcePath, int32 MaxAttempts, FString& OutSystemError)
	{
		OutSystemError.Reset();

		for (int32 Attempt = 1; Attempt <= MaxAttempts; ++Attempt)
		{
			PlatformFile.SetReadOnly(*DestPath, false);
			DetachLoadedPackageForFilename(DestPath);

			if (PlatformFile.CopyFile(*DestPath, *SourcePath))
			{
				return true;
			}

			OutSystemError = GetCurrentSystemErrorText();
			if (Attempt < MaxAttempts)
			{
				FPlatformProcess::Sleep(0.05f * static_cast<float>(Attempt));
			}
		}

		return false;
	}
}

bool FWorldBLDAssetImportService::CopyPreparedTreeToProjectContent(const FString& InPreparedRootOnDisk, const FString& InDestinationOnDisk) const
{
	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
	PlatformFile.CreateDirectoryTree(*InDestinationOnDisk);
	if (!PlatformFile.CopyDirectoryTree(*InDestinationOnDisk, *InPreparedRootOnDisk, true))
	{
		UE_LOG(LogWorldBLDAssetImportService, Warning,
			TEXT("[ImportService] CopyDirectoryTree failed. Source='%s' Dest='%s'"),
			*InPreparedRootOnDisk,
			*InDestinationOnDisk);
		return false;
	}

	// Ensure copied files are writable.
	TArray<FString> CopiedFiles;
	IFileManager::Get().FindFilesRecursive(CopiedFiles, *InDestinationOnDisk, TEXT("*.*"), true, false, false);
	for (const FString& FilePath : CopiedFiles)
	{
		PlatformFile.SetReadOnly(*FilePath, false);
	}

	return true;
}

bool FWorldBLDAssetImportService::ImportDownloadedArtifact(const FWorldBLDDownloadedArtifact& Artifact, FString& OutImportedPackageRoot, FString& OutImportedDiskRoot, bool bSkipExistingFiles, FString* OutErrorMessage) const
{
	OutImportedPackageRoot.Reset();
	OutImportedDiskRoot.Reset();
	if (OutErrorMessage != nullptr)
	{
		OutErrorMessage->Reset();
	}

	const auto FailImport = [&](const FString& ErrorMessage) -> bool
	{
		if (OutErrorMessage != nullptr)
		{
			*OutErrorMessage = ErrorMessage;
		}

		return false;
	};

	if (Artifact.PreparedRootOnDisk.IsEmpty() || Artifact.AuthoredPackageRoot.IsEmpty() || Artifact.Files.Num() == 0)
	{
		UE_LOG(LogWorldBLDAssetImportService, Warning,
			TEXT("[ImportService] Invalid artifact input. PreparedRoot='%s' AuthoredRoot='%s' FileCount=%d"),
			*Artifact.PreparedRootOnDisk,
			*Artifact.AuthoredPackageRoot,
			Artifact.Files.Num());
		return FailImport(FString::Printf(
			TEXT("Invalid import payload. PreparedRoot='%s' AuthoredRoot='%s' FileCount=%d."),
			*Artifact.PreparedRootOnDisk,
			*Artifact.AuthoredPackageRoot,
			Artifact.Files.Num()));
	}

	if (!FPackageName::IsValidLongPackageName(Artifact.AuthoredPackageRoot))
	{
		UE_LOG(LogWorldBLDAssetImportService, Warning,
			TEXT("[ImportService] Invalid authored package root: '%s'"),
			*Artifact.AuthoredPackageRoot);
		return FailImport(FString::Printf(TEXT("Invalid authored package root '%s'."), *Artifact.AuthoredPackageRoot));
	}

	FString RelativeContentPath = Artifact.AuthoredPackageRoot;
	RelativeContentPath.RemoveFromStart(TEXT("/Game/"));
	if (RelativeContentPath.IsEmpty())
	{
		UE_LOG(LogWorldBLDAssetImportService, Warning,
			TEXT("[ImportService] Relative content path resolved empty. AuthoredRoot='%s'"),
			*Artifact.AuthoredPackageRoot);
		return FailImport(FString::Printf(TEXT("Could not resolve destination path from authored root '%s'."), *Artifact.AuthoredPackageRoot));
	}

	const FString DestRootOnDisk = FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectContentDir(), RelativeContentPath));
	UE_LOG(LogWorldBLDAssetImportService, Log,
		TEXT("[ImportService] Import artifact begin. AuthoredRoot='%s' PreparedRoot='%s' DestRoot='%s' Files=%d SkipExisting=%s"),
		*Artifact.AuthoredPackageRoot,
		*Artifact.PreparedRootOnDisk,
		*DestRootOnDisk,
		Artifact.Files.Num(),
		bSkipExistingFiles ? TEXT("true") : TEXT("false"));

	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
	PlatformFile.CreateDirectoryTree(*DestRootOnDisk);
	DetachLoadedDestinationPackages(Artifact, DestRootOnDisk, PlatformFile);

	TArray<FString> NewUassetFiles;
	NewUassetFiles.Reserve(Artifact.Files.Num());
	int32 CopiedFilesCount = 0;
	int32 SkippedExistingCount = 0;
	static constexpr int32 MaxFileOperationAttempts = 5;

	for (const FWorldBLDAssetImportFileEntry& FileEntry : Artifact.Files)
	{
		if (FileEntry.RelativePathFromPackageRoot.IsEmpty())
		{
			continue;
		}

		const FString SourcePath = FPaths::Combine(Artifact.PreparedRootOnDisk, FileEntry.RelativePathFromPackageRoot);
		const FString DestPath = FPaths::Combine(DestRootOnDisk, FileEntry.RelativePathFromPackageRoot);
		if (!PlatformFile.FileExists(*SourcePath))
		{
			UE_LOG(LogWorldBLDAssetImportService, Warning,
				TEXT("[ImportService] Source file missing. Rel='%s' Source='%s'"),
				*FileEntry.RelativePathFromPackageRoot,
				*SourcePath);
			return FailImport(FString::Printf(
				TEXT("Missing source file for '%s'. Source='%s'."),
				*FileEntry.RelativePathFromPackageRoot,
				*SourcePath));
		}

		PlatformFile.CreateDirectoryTree(*FPaths::GetPath(DestPath));
		if (bSkipExistingFiles && PlatformFile.FileExists(*DestPath))
		{
			SkippedExistingCount++;
			continue;
		}

		if (!bSkipExistingFiles && PlatformFile.FileExists(*DestPath))
		{
			FString DeleteSystemError;
			if (!DeleteFileWithRetries(PlatformFile, DestPath, MaxFileOperationAttempts, DeleteSystemError))
			{
				const bool bDestReadOnly = PlatformFile.IsReadOnly(*DestPath);
				UE_LOG(LogWorldBLDAssetImportService, Warning,
					TEXT("[ImportService] Failed to delete existing destination before overwrite after %d attempts. Rel='%s' Dest='%s' ReadOnly=%s SystemError='%s'"),
					MaxFileOperationAttempts,
					*FileEntry.RelativePathFromPackageRoot,
					*DestPath,
					bDestReadOnly ? TEXT("true") : TEXT("false"),
					DeleteSystemError.IsEmpty() ? TEXT("<none>") : *DeleteSystemError);
				return FailImport(FString::Printf(
					TEXT("Failed to overwrite existing file '%s' after %d attempts. Destination='%s' (read-only=%s). SystemError='%s'."),
					*FileEntry.RelativePathFromPackageRoot,
					MaxFileOperationAttempts,
					*DestPath,
					bDestReadOnly ? TEXT("true") : TEXT("false"),
					DeleteSystemError.IsEmpty() ? TEXT("<none>") : *DeleteSystemError));
			}
		}

		FString CopySystemError;
		if (!CopyFileWithRetries(PlatformFile, DestPath, SourcePath, MaxFileOperationAttempts, CopySystemError))
		{
			const bool bSourceExists = PlatformFile.FileExists(*SourcePath);
			const bool bDestExists = PlatformFile.FileExists(*DestPath);
			const bool bDestReadOnly = bDestExists ? PlatformFile.IsReadOnly(*DestPath) : false;
			const int64 SourceSize = bSourceExists ? PlatformFile.FileSize(*SourcePath) : -1;
			const int64 DestSize = bDestExists ? PlatformFile.FileSize(*DestPath) : -1;

			UE_LOG(LogWorldBLDAssetImportService, Warning,
				TEXT("[ImportService] CopyFile failed after %d attempts. Rel='%s' Source='%s' Dest='%s' SourceExists=%s DestExists=%s DestReadOnly=%s SourceSize=%lld DestSize=%lld SystemError='%s'"),
				MaxFileOperationAttempts,
				*FileEntry.RelativePathFromPackageRoot,
				*SourcePath,
				*DestPath,
				bSourceExists ? TEXT("true") : TEXT("false"),
				bDestExists ? TEXT("true") : TEXT("false"),
				bDestReadOnly ? TEXT("true") : TEXT("false"),
				SourceSize,
				DestSize,
				CopySystemError.IsEmpty() ? TEXT("<none>") : *CopySystemError);
			return FailImport(FString::Printf(
				TEXT("Failed to copy '%s' after %d attempts. Source='%s' Dest='%s' SourceExists=%s DestExists=%s DestReadOnly=%s SourceSize=%lld DestSize=%lld SystemError='%s'."),
				*FileEntry.RelativePathFromPackageRoot,
				MaxFileOperationAttempts,
				*SourcePath,
				*DestPath,
				bSourceExists ? TEXT("true") : TEXT("false"),
				bDestExists ? TEXT("true") : TEXT("false"),
				bDestReadOnly ? TEXT("true") : TEXT("false"),
				SourceSize,
				DestSize,
				CopySystemError.IsEmpty() ? TEXT("<none>") : *CopySystemError));
		}
		CopiedFilesCount++;

		PlatformFile.SetReadOnly(*DestPath, false);

		const FString Ext = FPaths::GetExtension(DestPath).ToLower();
		if (Ext == TEXT("uasset") || Ext == TEXT("umap"))
		{
			NewUassetFiles.Add(DestPath);
		}
	}

	if (NewUassetFiles.Num() == 0)
	{
		if (bSkipExistingFiles)
		{
			UE_LOG(LogWorldBLDAssetImportService, Warning,
				TEXT("[ImportService] No new uasset/umap files copied (skip-existing mode). Copied=%d SkippedExisting=%d AuthoredRoot='%s'"),
				CopiedFilesCount,
				SkippedExistingCount,
				*Artifact.AuthoredPackageRoot);
			OutImportedPackageRoot = Artifact.AuthoredPackageRoot;
			OutImportedDiskRoot = DestRootOnDisk;
			return true;
		}

		UE_LOG(LogWorldBLDAssetImportService, Warning,
			TEXT("[ImportService] No uasset/umap files available for registry scan. Copied=%d SkippedExisting=%d AuthoredRoot='%s'"),
			CopiedFilesCount,
			SkippedExistingCount,
			*Artifact.AuthoredPackageRoot);
		return FailImport(FString::Printf(
			TEXT("Import produced no scanable assets (.uasset/.umap). Copied=%d SkippedExisting=%d AuthoredRoot='%s'."),
			CopiedFilesCount,
			SkippedExistingCount,
			*Artifact.AuthoredPackageRoot));
	}

	FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
	AssetRegistryModule.Get().ScanFilesSynchronous(NewUassetFiles, /*bForceRescan=*/true);
	UE_LOG(LogWorldBLDAssetImportService, Log,
		TEXT("[ImportService] Import artifact success. Copied=%d SkippedExisting=%d ScannedAssets=%d AuthoredRoot='%s'"),
		CopiedFilesCount,
		SkippedExistingCount,
		NewUassetFiles.Num(),
		*Artifact.AuthoredPackageRoot);

	OutImportedPackageRoot = Artifact.AuthoredPackageRoot;
	OutImportedDiskRoot = DestRootOnDisk;
	return true;
}

