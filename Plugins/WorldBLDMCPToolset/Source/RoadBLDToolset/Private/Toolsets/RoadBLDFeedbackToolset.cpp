// Copyright WorldBLD LLC. All rights reserved.

#include "Toolsets/RoadBLDFeedbackToolset.h"

#include "Common/RoadBLDRebuildJobs.h"
#include "Common/RoadBLDToolsetUtils.h"
#include "Containers/Ticker.h"
#include "DynamicRoad/DynamicRoad.h"
#include "DynamicRoad/DynamicRoadNetwork.h"
#include "Editor.h"
#include "ImageUtils.h"
#include "LevelEditorViewport.h"
#include "RenderingThread.h"
#include "RoadGeo.h"
#include "UnrealClient.h"
#include "UObject/StrongObjectPtr.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(RoadBLDFeedbackToolset)

namespace RoadBLDFeedbackPrivate
{
	using namespace RoadBLDToolset;

	/** Frames drawn after moving the camera so streaming and virtual textures can catch up. */
	constexpr int32 SettleFrames = 4;

	/** Longest a capture waits for rebuilds, kept well under typical MCP client request timeouts. */
	constexpr int32 MaxRebuildWaitMs = 30000;

	struct FCaptureRequest
	{
		TStrongObjectPtr<URoadBLDCaptureAsyncResult> Result;
		FBox Bounds = FBox(ForceInit);
		ERoadBLDCaptureView View = ERoadBLDCaptureView::Oblique;
		int32 Width = 768;
		int32 Height = 432;
		double Padding = 1.15;
		bool bRestoreCamera = false;
		TArray<FString> Warnings;
	};

	FLevelEditorViewportClient* FindPerspectiveViewport()
	{
		if (GCurrentLevelEditingViewportClient
			&& GCurrentLevelEditingViewportClient->IsPerspective()
			&& GCurrentLevelEditingViewportClient->Viewport)
		{
			return GCurrentLevelEditingViewportClient;
		}

		if (GEditor)
		{
			for (FLevelEditorViewportClient* Client : GEditor->GetLevelViewportClients())
			{
				if (Client && Client->IsPerspective() && Client->Viewport)
				{
					return Client;
				}
			}
		}

		return nullptr;
	}

	bool IsViewportClientAlive(const FLevelEditorViewportClient* Client)
	{
		return GEditor && Client && GEditor->GetLevelViewportClients().Contains(Client) && Client->Viewport;
	}

	void FrameBounds(FLevelEditorViewportClient* Client, const FBox& Bounds, const ERoadBLDCaptureView View, const double Padding)
	{
		const FVector Center = Bounds.GetCenter();
		const FVector Extent = Bounds.GetExtent();
		const FIntPoint ViewportSize = Client->Viewport->GetSizeXY();
		const double Aspect = ViewportSize.Y > 0 ? static_cast<double>(ViewportSize.X) / ViewportSize.Y : 16.0 / 9.0;
		const double HalfHorizontalFov = FMath::DegreesToRadians(FMath::Clamp<double>(Client->ViewFOV, 10.0, 170.0)) * 0.5;
		const double HalfVerticalFov = FMath::Atan(FMath::Tan(HalfHorizontalFov) / Aspect);
		const double SafePadding = FMath::Max(1.0, Padding);

		FRotator Rotation;
		double Distance = 0.0;
		if (View == ERoadBLDCaptureView::TopDown)
		{
			// Looking straight down with yaw 0, screen-right is world +Y and screen-up is world +X.
			Rotation = FRotator(-89.9, 0.0, 0.0);
			Distance = FMath::Max(Extent.Y / FMath::Tan(HalfHorizontalFov), Extent.X / FMath::Tan(HalfVerticalFov)) * SafePadding + Extent.Z;
		}
		else
		{
			Rotation = FRotator(-50.0, 45.0, 0.0);
			const double Radius = FMath::Max(FVector(Extent.X, Extent.Y, Extent.Z).Size(), 500.0);
			Distance = Radius / FMath::Sin(FMath::Min(HalfHorizontalFov, HalfVerticalFov)) * SafePadding;
		}

		Client->SetViewLocation(Center - Rotation.Vector() * FMath::Max(Distance, 1000.0));
		Client->SetViewRotation(Rotation);
		Client->Invalidate();
	}

	TArray<FColor> ResizeToFit(const TArray<FColor>& Source, const FIntPoint SourceSize, const int32 MaxWidth, const int32 MaxHeight, FIntPoint& OutSize)
	{
		const double Scale = FMath::Min3(
			static_cast<double>(FMath::Max(MaxWidth, 16)) / SourceSize.X,
			static_cast<double>(FMath::Max(MaxHeight, 16)) / SourceSize.Y,
			1.0);
		OutSize = FIntPoint(
			FMath::Max(1, FMath::RoundToInt32(SourceSize.X * Scale)),
			FMath::Max(1, FMath::RoundToInt32(SourceSize.Y * Scale)));
		if (OutSize == SourceSize)
		{
			return Source;
		}

		TArray64<FLinearColor> SourceLinear;
		SourceLinear.SetNum(Source.Num());
		for (int32 Index = 0; Index < Source.Num(); ++Index)
		{
			SourceLinear[Index] = FLinearColor::FromSRGBColor(Source[Index]);
		}

		TArray64<FLinearColor> TargetLinear;
		TargetLinear.SetNum(static_cast<int64>(OutSize.X) * OutSize.Y);
		FImageUtils::ImageResize(SourceSize.X, SourceSize.Y, SourceLinear, OutSize.X, OutSize.Y, TargetLinear);

		TArray<FColor> Target;
		Target.SetNum(OutSize.X * OutSize.Y);
		for (int32 Index = 0; Index < Target.Num(); ++Index)
		{
			Target[Index] = TargetLinear[Index].ToFColorSRGB();
		}
		return Target;
	}

	void CaptureNow(const TSharedRef<FCaptureRequest>& Request)
	{
		FLevelEditorViewportClient* Client = FindPerspectiveViewport();
		if (!Client)
		{
			Request->Result->SetError(TEXT("RoadBLDToolset: No perspective level viewport is available. Captures require the editor UI."));
			return;
		}

		const FVector SavedLocation = Client->GetViewLocation();
		const FRotator SavedRotation = Client->GetViewRotation();
		const bool bSavedSelection = Client->EngineShowFlags.Selection != 0;
		const bool bSavedSelectionOutline = Client->EngineShowFlags.SelectionOutline != 0;
		const bool bSavedModeWidgets = Client->EngineShowFlags.ModeWidgets != 0;

		if (Request->View != ERoadBLDCaptureView::Current && Request->Bounds.IsValid)
		{
			FrameBounds(Client, Request->Bounds, Request->View, Request->Padding);
		}

		Client->EngineShowFlags.SetSelection(false);
		Client->EngineShowFlags.SetSelectionOutline(false);
		Client->EngineShowFlags.SetModeWidgets(false);
		Client->Invalidate();

		TSharedRef<int32> FramesRemaining = MakeShared<int32>(SettleFrames);
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda(
			[Request, Client, FramesRemaining, SavedLocation, SavedRotation, bSavedSelection, bSavedSelectionOutline, bSavedModeWidgets](float)
			{
				if (!IsViewportClientAlive(Client))
				{
					Request->Result->SetError(TEXT("RoadBLDToolset: The level viewport closed during capture."));
					return false;
				}

				if (--(*FramesRemaining) > 0)
				{
					Client->Invalidate();
					return true;
				}

				Client->Viewport->Draw();
				FlushRenderingCommands();

				TArray<FColor> Bitmap;
				const FIntPoint SourceSize = Client->Viewport->GetSizeXY();
				const bool bCaptured = GetViewportScreenShot(Client->Viewport, Bitmap)
					&& Bitmap.Num() == SourceSize.X * SourceSize.Y;

				FRoadBLDCaptureResult Capture;
				Capture.CameraLocation = Client->GetViewLocation();
				Capture.CameraRotation = Client->GetViewRotation();
				if (Request->Bounds.IsValid)
				{
					Capture.BoundsMin = Request->Bounds.Min;
					Capture.BoundsMax = Request->Bounds.Max;
				}
				Capture.Warnings = Request->Warnings;

				Client->EngineShowFlags.SetSelection(bSavedSelection);
				Client->EngineShowFlags.SetSelectionOutline(bSavedSelectionOutline);
				Client->EngineShowFlags.SetModeWidgets(bSavedModeWidgets);
				if (Request->bRestoreCamera)
				{
					Client->SetViewLocation(SavedLocation);
					Client->SetViewRotation(SavedRotation);
				}
				Client->Invalidate();

				if (!bCaptured)
				{
					Request->Result->SetError(TEXT("RoadBLDToolset: Failed to read the viewport framebuffer."));
					return false;
				}

				for (FColor& Pixel : Bitmap)
				{
					Pixel.A = 255;
				}

				FIntPoint ImageSize;
				const TArray<FColor> Scaled = ResizeToFit(Bitmap, SourceSize, Request->Width, Request->Height, ImageSize);
				if (!Capture.Image.SetFromBitmap(Scaled, ImageSize))
				{
					Request->Result->SetError(TEXT("RoadBLDToolset: Failed to encode the capture."));
					return false;
				}

				Request->Result->SetValue(Capture);
				return false;
			}));
	}

	void AddStaleWarnings(FCaptureRequest& Request, const TArray<TWeakObjectPtr<ADynamicRoadNetwork>>& Networks)
	{
		for (const TWeakObjectPtr<ADynamicRoadNetwork>& WeakNetwork : Networks)
		{
			const ADynamicRoadNetwork* Network = WeakNetwork.Get();
			if (IsValid(Network) && Network->IsRoadNetworkStale())
			{
				Request.Warnings.Add(FString::Printf(
					TEXT("%s has unbuilt edits, so this capture shows its last build. Call RoadBLDBuildToolset.Rebuild, then capture again."),
					*Network->GetActorLabel()));
			}
		}
	}

	void StartCapture(const TSharedRef<FCaptureRequest>& Request, const TArray<ADynamicRoadNetwork*>& Networks, const bool bWaitForRebuild, const int32 TimeoutMs)
	{
		TArray<TWeakObjectPtr<ADynamicRoadNetwork>> WeakNetworks;
		for (ADynamicRoadNetwork* Network : Networks)
		{
			WeakNetworks.Add(Network);
		}

		// Only rebuilds that are queued or running are worth waiting for; a stale network with nothing queued never
		// becomes idle on its own.
		const FRoadBLDRebuildJobs& Jobs = FRoadBLDRebuildJobs::Get();
		const bool bAnyRebuilding = Networks.ContainsByPredicate([&Jobs](const ADynamicRoadNetwork* Network)
		{
			return Jobs.IsNetworkRebuilding(Network);
		});

		if (!bWaitForRebuild || !bAnyRebuilding)
		{
			AddStaleWarnings(*Request, WeakNetworks);
			CaptureNow(Request);
			return;
		}

		const int32 WaitMs = FMath::Clamp(TimeoutMs, 0, MaxRebuildWaitMs);
		FRoadBLDRebuildJobs::Get().WaitForNetworksIdle(Networks, WaitMs / 1000.0, [Request, WeakNetworks](const bool bIdle)
		{
			if (!bIdle)
			{
				Request->Warnings.Add(TEXT("Captured while a rebuild was still running; geometry may be incomplete. Wait with RoadBLDBuildToolset.WaitForRebuild, then capture again."));
			}
			AddStaleWarnings(*Request, WeakNetworks);
			CaptureNow(Request);
		});
	}

	TSharedRef<FCaptureRequest> MakeRequest(URoadBLDCaptureAsyncResult* Result, const ERoadBLDCaptureView View, const int32 Width, const int32 Height, const double Padding, const bool bRestoreCamera)
	{
		TSharedRef<FCaptureRequest> Request = MakeShared<FCaptureRequest>();
		Request->Result.Reset(Result);
		Request->View = View;
		Request->Width = FMath::Clamp(Width, 16, 4096);
		Request->Height = FMath::Clamp(Height, 16, 4096);
		Request->Padding = Padding;
		Request->bRestoreCamera = bRestoreCamera;
		return Request;
	}
}

URoadBLDCaptureAsyncResult* URoadBLDFeedbackToolset::CaptureViewport(
	ADynamicRoad* Road,
	const FString& JunctionId,
	ADynamicRoadNetwork* Network,
	const ERoadBLDCaptureView View,
	const int32 Width,
	const int32 Height,
	const double Padding,
	const bool bWaitForRebuild,
	const int32 TimeoutMs,
	const bool bRestoreCamera)
{
	using namespace RoadBLDFeedbackPrivate;

	URoadBLDCaptureAsyncResult* Result = NewObject<URoadBLDCaptureAsyncResult>();
	TSharedRef<FCaptureRequest> Request = MakeRequest(Result, View, Width, Height, Padding, bRestoreCamera);
	TArray<ADynamicRoadNetwork*> Networks;

	const FString Junction = GetOptionalString(JunctionId, TEXT("None"));
	if (!Junction.IsEmpty())
	{
		const ARoadGeo* Geo = FindObject<ARoadGeo>(nullptr, *Junction);
		if (!IsValid(Geo))
		{
			Result->SetError(TEXT("RoadBLDToolset: Junction not found. Junction ids change after rebuilds; call ListJunctions again."));
			return Result;
		}

		Request->Bounds += Geo->GetComponentsBoundingBox(true);
		for (const TSoftObjectPtr<ADynamicRoad>& SourceRoad : Geo->SourceRoads)
		{
			if (ADynamicRoadNetwork* SourceNetwork = GetOwningNetwork(SourceRoad.Get()))
			{
				Networks.AddUnique(SourceNetwork);
			}
		}
	}

	if (IsValid(Road))
	{
		Request->Bounds += GetRoadBounds(Road, true);
		Networks.AddUnique(GetOwningNetwork(Road));
	}

	if (IsValid(Network))
	{
		Request->Bounds += GetNetworkBounds(Network, false);
		Networks.AddUnique(Network);
	}

	const bool bHasTarget = !Junction.IsEmpty() || IsValid(Road) || IsValid(Network);
	if (!bHasTarget)
	{
		for (ADynamicRoadNetwork* Candidate : GetNetworks())
		{
			Request->Bounds += GetNetworkBounds(Candidate, false);
			Networks.AddUnique(Candidate);
		}
	}

	Networks.Remove(nullptr);
	if (!Request->Bounds.IsValid && View != ERoadBLDCaptureView::Current)
	{
		Result->SetError(TEXT("RoadBLDToolset: Nothing to frame. Pass a Road, JunctionId or Network, or create roads first."));
		return Result;
	}

	StartCapture(Request, Networks, bWaitForRebuild, TimeoutMs);
	return Result;
}

URoadBLDCaptureAsyncResult* URoadBLDFeedbackToolset::CaptureArea(
	const FVector Center,
	const double Radius,
	const ERoadBLDCaptureView View,
	const int32 Width,
	const int32 Height,
	const bool bWaitForRebuild,
	const int32 TimeoutMs,
	const bool bRestoreCamera)
{
	using namespace RoadBLDFeedbackPrivate;

	URoadBLDCaptureAsyncResult* Result = NewObject<URoadBLDCaptureAsyncResult>();
	TSharedRef<FCaptureRequest> Request = MakeRequest(Result, View, Width, Height, 1.0, bRestoreCamera);
	const double SafeRadius = FMath::Max(Radius, 100.0);
	Request->Bounds = FBox(Center - FVector(SafeRadius, SafeRadius, 100.0), Center + FVector(SafeRadius, SafeRadius, 100.0));

	StartCapture(Request, GetNetworks(), bWaitForRebuild, TimeoutMs);
	return Result;
}
