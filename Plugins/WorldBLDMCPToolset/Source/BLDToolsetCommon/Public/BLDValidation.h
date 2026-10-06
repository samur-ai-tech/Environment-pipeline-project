// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "BLDToolsetTypes.h"

/** Helpers for building shared FBLDIssueReport validation loops. */
namespace BLDValidation
{
	BLDTOOLSETCOMMON_API FBLDIssue MakeIssue(
		EBLDIssueSeverity Severity,
		const FString& Source,
		const FString& Code,
		const FString& Message,
		const FBLDActorRef& Subject = FBLDActorRef(),
		const FBLDActorRef& Other = FBLDActorRef(),
		const FVector& Location = FVector::ZeroVector,
		double Radius = 0.0,
		const FString& Fix = FString());

	/** Recomputes counts, sorts Issues (Error > Warning > Info, then Source/Code), sets bReady from ErrorCount. */
	BLDTOOLSETCOMMON_API void FinalizeReport(FBLDIssueReport& Report);

	BLDTOOLSETCOMMON_API void AppendIssues(FBLDIssueReport& Report, TArray<FBLDIssue>&& Issues);

	BLDTOOLSETCOMMON_API void MergeReports(FBLDIssueReport& Dest, const FBLDIssueReport& Src);
}