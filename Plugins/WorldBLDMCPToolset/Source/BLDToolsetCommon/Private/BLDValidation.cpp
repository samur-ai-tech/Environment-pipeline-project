// Copyright WorldBLD LLC. All rights reserved.

#include "BLDValidation.h"

namespace BLDValidation
{
	FBLDIssue MakeIssue(
		const EBLDIssueSeverity Severity,
		const FString& Source,
		const FString& Code,
		const FString& Message,
		const FBLDActorRef& Subject,
		const FBLDActorRef& Other,
		const FVector& Location,
		const double Radius,
		const FString& Fix)
	{
		FBLDIssue Issue;
		Issue.Severity = Severity;
		Issue.Source = Source;
		Issue.Code = Code;
		Issue.Message = Message;
		Issue.Subject = Subject;
		Issue.Other = Other;
		Issue.Location = Location;
		Issue.Radius = Radius;
		Issue.Fix = Fix;
		return Issue;
	}

	static int32 SeverityRank(const EBLDIssueSeverity Severity)
	{
		switch (Severity)
		{
		case EBLDIssueSeverity::Error: return 0;
		case EBLDIssueSeverity::Warning: return 1;
		default: return 2;
		}
	}

	void FinalizeReport(FBLDIssueReport& Report)
	{
		Report.ErrorCount = 0;
		Report.WarningCount = 0;
		Report.InfoCount = 0;
		for (const FBLDIssue& Issue : Report.Issues)
		{
			switch (Issue.Severity)
			{
			case EBLDIssueSeverity::Error: ++Report.ErrorCount; break;
			case EBLDIssueSeverity::Warning: ++Report.WarningCount; break;
			case EBLDIssueSeverity::Info: ++Report.InfoCount; break;
			}
		}

		Report.Issues.Sort([](const FBLDIssue& A, const FBLDIssue& B)
		{
			const int32 RankA = SeverityRank(A.Severity);
			const int32 RankB = SeverityRank(B.Severity);
			if (RankA != RankB)
			{
				return RankA < RankB;
			}
			const int32 SourceCmp = A.Source.Compare(B.Source, ESearchCase::IgnoreCase);
			if (SourceCmp != 0)
			{
				return SourceCmp < 0;
			}
			return A.Code.Compare(B.Code, ESearchCase::IgnoreCase) < 0;
		});

		Report.bReady = Report.ErrorCount == 0;
	}

	void AppendIssues(FBLDIssueReport& Report, TArray<FBLDIssue>&& Issues)
	{
		Report.Issues.Append(MoveTemp(Issues));
		FinalizeReport(Report);
	}

	void MergeReports(FBLDIssueReport& Dest, const FBLDIssueReport& Src)
	{
		Dest.Issues.Append(Src.Issues);
		Dest.Notes.Append(Src.Notes);
		FinalizeReport(Dest);
	}
}